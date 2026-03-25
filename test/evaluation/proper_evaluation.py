"""
正确的算法评估测试

方法：
1. 实时测试 - 用户做动作后手动输入真实次数
2. 视频测试 - 录制视频后人工标注
"""

import argparse
import time
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config
from src.pose_detector import PoseDetector
from src.squat_counter import SquatCounter, PoseState


SKELETON_CONNECTIONS = [
    (11, 12),  # 肩膀
    (11, 13),
    (13, 15),  # 左臂
    (12, 14),
    (14, 16),  # 右臂
    (11, 23),
    (12, 24),  # 躯干
    (23, 24),  # 髋部
    (23, 25),
    (25, 27),  # 左腿
    (24, 26),
    (26, 28),  # 右腿
]


@dataclass
class FrameData:
    frame_id: int
    timestamp: float
    left_angle: float
    right_angle: float
    avg_angle: float
    smoothed_angle: float
    state: str
    rep_count: int


def draw_skeleton(frame, landmarks, color=(0, 255, 0)):
    if not landmarks:
        return frame

    h, w = frame.shape[:2]

    for connection in SKELETON_CONNECTIONS:
        idx1, idx2 = connection
        if idx1 < len(landmarks) and idx2 < len(landmarks):
            pt1 = landmarks[idx1]
            pt2 = landmarks[idx2]
            x1, y1 = int(pt1.x * w), int(pt1.y * h)
            x2, y2 = int(pt2.x * w), int(pt2.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), color, 3)

    for i, landmark in enumerate(landmarks):
        x, y = int(landmark.x * w), int(landmark.y * h)
        cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)

    return frame


def realtime_test(duration: int = 60, rotate: bool = True):
    print("\n" + "=" * 50)
    print("实时算法测试")
    print("=" * 50)
    print(f"测试时长: {duration}秒")
    print(f"画面旋转: {'开启' if rotate else '关闭'}")
    print("请对着摄像头做深蹲动作")
    print("测试结束后请输入实际深蹲次数")
    print("-" * 50)

    pose_detector = PoseDetector()
    squat_counter = SquatCounter()

    cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return

    width, height = Config.CAMERA_RESOLUTION
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    window_width = 800
    window_height = 600
    cv2.namedWindow("Squat Test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Squat Test", window_width, window_height)

    frame_data: List[FrameData] = []
    frame_count = 0
    fps = 30
    start_time = time.time()

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            continue

        if rotate:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        timestamp_ms = int(frame_count * 1000 / fps)

        pose_data = pose_detector.detect(rgb_frame, timestamp_ms)

        if pose_data:
            metrics = squat_counter.update(pose_data)

            landmarks = pose_data.get("normalized")
            if landmarks and len(landmarks) > 0:
                frame = draw_skeleton(frame, landmarks[0])

            frame_data.append(
                FrameData(
                    frame_id=frame_count,
                    timestamp=time.time() - start_time,
                    left_angle=metrics.left_knee_angle,
                    right_angle=metrics.right_knee_angle,
                    avg_angle=metrics.avg_knee_angle,
                    smoothed_angle=squat_counter._left_smoother.value or 0,
                    state=metrics.state.value,
                    rep_count=metrics.rep_count,
                )
            )

            cv2.putText(
                frame,
                f"Count: {metrics.rep_count}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Angle: {metrics.avg_knee_angle:.0f}",
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 0),
                2,
            )
            state_color = (
                (0, 255, 0) if metrics.state == PoseState.STANDING else (0, 165, 255)
            )
            cv2.putText(
                frame,
                f"State: {metrics.state.value}",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                state_color,
                2,
            )

        remaining = duration - (time.time() - start_time)
        cv2.putText(
            frame,
            f"Time: {remaining:.0f}s",
            (20, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (150, 150, 150),
            2,
        )

        cv2.imshow("Squat Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    pose_detector.close()

    predicted_count = squat_counter.count

    print("\n" + "=" * 50)
    print("测试结束!")
    print("=" * 50)
    print(f"算法检测次数: {predicted_count}")

    try:
        true_count = int(input("请输入实际深蹲次数: "))
    except ValueError:
        true_count = predicted_count

    if true_count > 0:
        accuracy = min(predicted_count, true_count) / true_count * 100
        if predicted_count > true_count:
            accuracy = true_count / predicted_count * 100

        over_count = max(0, predicted_count - true_count)
        under_count = max(0, true_count - predicted_count)

        print("\n--- 结果分析 ---")
        print(f"计数准确率: {accuracy:.1f}%")
        if over_count > 0:
            print(f"多计数: {over_count} 次")
        if under_count > 0:
            print(f"漏计数: {under_count} 次")
    else:
        print("未输入有效次数")

    if len(frame_data) > 10:
        angles = [f.avg_angle for f in frame_data]
        smoothed = [f.smoothed_angle for f in frame_data if f.smoothed_angle > 0]

        raw_jitter = np.std(angles)
        if smoothed:
            smooth_jitter = np.std(smoothed)
            print(f"\n角度抖动:")
            print(f"  原始: {raw_jitter:.2f}")
            print(f"  平滑后: {smooth_jitter:.2f}")
            print(f"  改善: {(1 - smooth_jitter / raw_jitter) * 100:.1f}%")

    return frame_data


def video_test(video_path: str, ground_truth: int = None):
    print(f"\n测试视频: {video_path}")

    pose_detector = PoseDetector()
    squat_counter = SquatCounter()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"错误: 无法打开视频 {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"视频帧数: {total_frames}, FPS: {fps:.1f}")

    cv2.namedWindow("Video Test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Video Test", 800, 600)

    frame_count = 0
    frame_data: List[FrameData] = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        timestamp_ms = int(frame_count * 1000 / fps)

        pose_data = pose_detector.detect(rgb_frame, timestamp_ms)

        if pose_data:
            metrics = squat_counter.update(pose_data)

            landmarks = pose_data.get("normalized")
            if landmarks and len(landmarks) > 0:
                frame = draw_skeleton(frame, landmarks[0])

            frame_data.append(
                FrameData(
                    frame_id=frame_count,
                    timestamp=frame_count / fps,
                    left_angle=metrics.left_knee_angle,
                    right_angle=metrics.right_knee_angle,
                    avg_angle=metrics.avg_knee_angle,
                    smoothed_angle=squat_counter._left_smoother.value or 0,
                    state=metrics.state.value,
                    rep_count=metrics.rep_count,
                )
            )

            cv2.putText(
                frame,
                f"Count: {metrics.rep_count}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                2,
            )

        if frame_count % 30 == 0:
            print(
                f"\r处理进度: {frame_count}/{total_frames} ({frame_count * 100 // total_frames}%)",
                end="",
            )

        cv2.imshow("Video Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    pose_detector.close()

    predicted_count = squat_counter.count

    print(f"\n\n--- 视频测试结果 ---")
    print(f"算法检测次数: {predicted_count}")

    if ground_truth:
        accuracy = min(predicted_count, ground_truth) / ground_truth * 100
        if predicted_count > ground_truth:
            accuracy = ground_truth / predicted_count * 100
        print(f"真实次数: {ground_truth}")
        print(f"准确率: {accuracy:.1f}%")
    else:
        true_count = int(input("请输入视频中的真实深蹲次数: "))
        accuracy = min(predicted_count, true_count) / true_count * 100
        print(f"准确率: {accuracy:.1f}%")

    return frame_data


def main():
    parser = argparse.ArgumentParser(description="算法精准度测试")
    parser.add_argument("--realtime", action="store_true", help="实时摄像头测试")
    parser.add_argument("--duration", type=int, default=60, help="测试时长(秒)")
    parser.add_argument(
        "--no-rotate", action="store_true", help="不旋转画面(横屏摄像头)"
    )
    parser.add_argument("--video", type=str, help="视频文件路径")
    parser.add_argument("--ground-truth", type=int, help="真实深蹲次数")

    args = parser.parse_args()

    rotate = not args.no_rotate

    if args.realtime:
        realtime_test(args.duration, rotate)
    elif args.video:
        video_test(args.video, args.ground_truth)
    else:
        print("请选择测试模式:")
        print("  --realtime         实时摄像头测试")
        print("  --no-rotate        不旋转画面(横屏摄像头)")
        print("  --video <path>     视频文件测试")
        print("\n示例:")
        print("  python test/proper_evaluation.py --realtime --duration 60")
        print("  python test/proper_evaluation.py --realtime --no-rotate")
        print("  python test/proper_evaluation.py --video squat.mp4 --ground-truth 10")


if __name__ == "__main__":
    main()

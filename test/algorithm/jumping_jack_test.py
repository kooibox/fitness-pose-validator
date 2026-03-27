#!/usr/bin/env python3
"""
开合跳算法测试脚本

支持多种测试模式:
1. 实时测试 - 使用摄像头实时检测
2. 视频测试 - 使用视频文件测试
3. 离线测试 - 使用CSV数据验证算法

使用方法:
    python test/algorithm/jumping_jack_test.py --realtime --duration 60
    python test/algorithm/jumping_jack_test.py --video jumping_jack.mp4 --ground-truth 20
    python test/algorithm/jumping_jack_test.py --csv jumping_jack_data.csv --actual-count 15
"""

import argparse
import csv
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config
from src.pose_detector import PoseDetector
from src.jumping_jack_counter import (
    JumpingJackCounter,
    JumpingJackState,
)


JUMPING_JACK_SKELETON = [
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (23, 25), (25, 27),
    (24, 26), (26, 28),
    (23, 24),
]


@dataclass
class JumpingJackFrameRecord:
    frame_id: int
    timestamp: float
    detected: bool
    left_hip_angle: float
    right_hip_angle: float
    avg_hip_angle: float
    left_shoulder_angle: float
    right_shoulder_angle: float
    avg_shoulder_angle: float
    combined_angle: float
    state: str
    rep_count: int
    confirm_count: int
    ankle_distance: float = 0.0
    wrist_height: float = 0.0
    open_ratio: float = 0.0


def draw_jumping_jack_skeleton(frame, landmarks, state: JumpingJackState):
    """绘制开合跳骨骼"""
    if not landmarks:
        return frame

    h, w = frame.shape[:2]

    color = (0, 255, 0) if state == JumpingJackState.OPEN else (0, 165, 255)

    for connection in JUMPING_JACK_SKELETON:
        idx1, idx2 = connection
        if idx1 < len(landmarks) and idx2 < len(landmarks):
            pt1, pt2 = landmarks[idx1], landmarks[idx2]
            x1, y1 = int(pt1.x * w), int(pt1.y * h)
            x2, y2 = int(pt2.x * w), int(pt2.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), color, 3)

    for landmark in landmarks:
        x, y = int(landmark.x * w), int(landmark.y * h)
        cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)

    return frame


def realtime_test(duration: int = 60, rotate: bool = True):
    """实时摄像头测试"""
    print("\n" + "=" * 60)
    print("开合跳实时测试")
    print("=" * 60)
    print(f"测试时长: {duration}秒")
    print(f"画面旋转: {'开启' if rotate else '关闭'}")
    print("-" * 60)
    print(f"阈值配置:")
    print(f"  并拢髋角阈值: {Config.CLOSED_HIP_THRESHOLD}°")
    print(f"  分开髋角阈值: {Config.OPEN_HIP_THRESHOLD}°")
    print(f"  下垂肩角阈值: {Config.CLOSED_SHOULDER_THRESHOLD}°")
    print(f"  上举肩角阈值: {Config.OPEN_SHOULDER_THRESHOLD}°")
    print("-" * 60)
    print("请对着摄像头做开合跳动作")
    print("测试结束后请输入实际次数")
    print("=" * 60)

    pose_detector = PoseDetector()
    counter = JumpingJackCounter()

    cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return None

    width, height = Config.CAMERA_RESOLUTION
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    cv2.namedWindow("Jumping Jack Test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Jumping Jack Test", 800, 600)

    records: List[JumpingJackFrameRecord] = []
    frame_count = 0
    fps = 30
    start_time = time.time()
    no_detection_count = 0

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            continue

        if rotate:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        timestamp_ms = int(frame_count * 1000 / fps)

        pose_data = pose_detector.detect(rgb_frame, timestamp_ms)

        detected = False
        metrics = None

        if pose_data:
            metrics = counter.update(pose_data)
            detected = True

            landmarks = pose_data.get("normalized")
            if landmarks and len(landmarks) > 0:
                frame = draw_jumping_jack_skeleton(frame, landmarks[0], metrics.state)

            records.append(
                JumpingJackFrameRecord(
                    frame_id=frame_count,
                    timestamp=time.time() - start_time,
                    detected=detected,
                    left_hip_angle=metrics.left_hip_angle,
                    right_hip_angle=metrics.right_hip_angle,
                    avg_hip_angle=metrics.avg_hip_angle,
                    left_shoulder_angle=metrics.left_shoulder_angle,
                    right_shoulder_angle=metrics.right_shoulder_angle,
                    avg_shoulder_angle=metrics.avg_shoulder_angle,
                    combined_angle=(metrics.avg_hip_angle + metrics.avg_shoulder_angle) / 2,
                    state=metrics.state.value,
                    rep_count=metrics.rep_count,
                    confirm_count=counter._confirm_count,
                )
            )
        else:
            no_detection_count += 1

        if metrics:
            cv2.putText(
                frame,
                f"Count: {metrics.rep_count}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.4,
                (0, 255, 0),
                2,
            )

            state_color = (0, 255, 0) if metrics.state == JumpingJackState.OPEN else (0, 165, 255)
            state_text = "OPEN" if metrics.state == JumpingJackState.OPEN else "CLOSED"
            cv2.putText(
                frame,
                f"State: {state_text}",
                (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                state_color,
                2,
            )

            cv2.putText(
                frame,
                f"Hip: {metrics.avg_hip_angle:.0f}",
                (20, 135),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Shoulder: {metrics.avg_shoulder_angle:.0f}",
                (20, 170),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 200, 0),
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

        cv2.imshow("Jumping Jack Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    pose_detector.close()

    predicted_count = counter.final_count

    print("\n" + "=" * 60)
    print("测试结束!")
    print("=" * 60)
    print(f"总帧数: {frame_count}")
    print(f"检测失败帧数: {no_detection_count}")
    print(f"检测成功率: {(frame_count - no_detection_count) / frame_count * 100:.1f}%")
    print(f"\n状态机计数: {counter.count}")
    print(f"峰值检测计数: {counter.peak_count}")
    print(f"最终计数: {predicted_count}")

    try:
        true_count = int(input("\n请输入实际开合跳次数: "))
    except ValueError:
        true_count = predicted_count

    if true_count > 0:
        accuracy = min(predicted_count, true_count) / true_count * 100
        if predicted_count > true_count:
            accuracy = true_count / predicted_count * 100

        print("\n--- 结果分析 ---")
        print(f"真实次数: {true_count}")
        print(f"检测次数: {predicted_count}")
        print(f"准确率: {accuracy:.1f}%")

        if predicted_count > true_count:
            print(f"多计数: {predicted_count - true_count} 次")
        elif predicted_count < true_count:
            print(f"漏计数: {true_count - predicted_count} 次")

    csv_path = save_records(records, "jumping_jack_realtime")
    print(f"\n数据已保存到: {csv_path}")

    return records


def video_test(video_path: str, ground_truth: int = None):
    """视频文件测试"""
    print(f"\n测试视频: {video_path}")

    pose_detector = PoseDetector()
    counter = JumpingJackCounter()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"错误: 无法打开视频 {video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"视频帧数: {total_frames}, FPS: {fps:.1f}")

    cv2.namedWindow("Video Test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Video Test", 800, 600)

    frame_count = 0
    records: List[JumpingJackFrameRecord] = []
    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        timestamp_ms = int(frame_count * 1000 / fps)

        pose_data = pose_detector.detect(rgb_frame, timestamp_ms)

        if pose_data:
            metrics = counter.update(pose_data)

            landmarks = pose_data.get("normalized")
            if landmarks and len(landmarks) > 0:
                frame = draw_jumping_jack_skeleton(frame, landmarks[0], metrics.state)

            records.append(
                JumpingJackFrameRecord(
                    frame_id=frame_count,
                    timestamp=frame_count / fps,
                    detected=True,
                    left_hip_angle=metrics.left_hip_angle,
                    right_hip_angle=metrics.right_hip_angle,
                    avg_hip_angle=metrics.avg_hip_angle,
                    left_shoulder_angle=metrics.left_shoulder_angle,
                    right_shoulder_angle=metrics.right_shoulder_angle,
                    avg_shoulder_angle=metrics.avg_shoulder_angle,
                    combined_angle=metrics.open_ratio * 100,
                    state=metrics.state.value,
                    rep_count=metrics.rep_count,
                    confirm_count=counter._confirm_count,
                    ankle_distance=metrics.ankle_distance,
                    wrist_height=metrics.wrist_height,
                    open_ratio=metrics.open_ratio,
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

            state_text = "OPEN" if metrics.state == JumpingJackState.OPEN else "CLOSED"
            cv2.putText(
                frame,
                f"State: {state_text}",
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 255),
                2,
            )
            
            cv2.putText(
                frame,
                f"Ankle: {metrics.ankle_distance:.2f}",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 200, 0),
                2,
            )
            
            cv2.putText(
                frame,
                f"Wrist: {metrics.wrist_height:.2f}",
                (20, 165),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 200, 0),
                2,
            )

        if frame_count % 30 == 0:
            progress = frame_count * 100 // total_frames
            print(f"\r处理进度: {frame_count}/{total_frames} ({progress}%)", end="")

        cv2.imshow("Video Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    pose_detector.close()

    predicted_count = counter.final_count

    print(f"\n\n--- 视频测试结果 ---")
    print(f"状态机计数: {counter.count}")
    print(f"峰值检测计数: {counter.peak_count}")
    print(f"最终计数: {predicted_count}")

    if ground_truth:
        accuracy = min(predicted_count, ground_truth) / ground_truth * 100
        if predicted_count > ground_truth:
            accuracy = ground_truth / predicted_count * 100
        print(f"真实次数: {ground_truth}")
        print(f"准确率: {accuracy:.1f}%")
    else:
        try:
            true_count = int(input("请输入视频中的真实开合跳次数: "))
            accuracy = min(predicted_count, true_count) / true_count * 100
            print(f"准确率: {accuracy:.1f}%")
        except ValueError:
            pass

    csv_path = save_records(records, "jumping_jack_video")
    print(f"数据已保存到: {csv_path}")

    return records


def offline_test(csv_path: str, actual_count: int):
    """离线CSV数据测试"""
    print("=" * 60)
    print("开合跳离线算法验证")
    print("=" * 60)

    records = load_csv_data(csv_path)
    if not records:
        print(f"错误: 无法加载数据 {csv_path}")
        return

    print(f"\n加载数据: {len(records)} 帧")
    print(f"用户实际开合跳次数: {actual_count}")

    original_count = records[-1].get("rep_count", 0)
    print(f"原始状态机计数: {original_count}")

    combined_angles = [r.get("combined_angle", 0) for r in records if r.get("combined_angle", 0) > 0]

    if combined_angles:
        detector = PeakDetector()
        for i, angle in enumerate(combined_angles):
            detector.add_sample(angle, i * 0.033)

        peak_count = detector.count
        print(f"峰值检测计数: {peak_count}")

        final_count = max(original_count, peak_count)
        accuracy = min(final_count, actual_count) / actual_count * 100

        print(f"\n--- 结果分析 ---")
        print(f"最终计数: {final_count}")
        print(f"准确率: {accuracy:.1f}%")

        print("\n角度统计:")
        print(f"  最小综合角度: {min(combined_angles):.1f}°")
        print(f"  最大综合角度: {max(combined_angles):.1f}°")
        print(f"  平均综合角度: {np.mean(combined_angles):.1f}°")

        print("\n" + "=" * 60)
        print("总结")
        print("=" * 60)
        print(f"| 算法       | 计数 | 准确率   |")
        print(f"|------------|------|----------|")
        print(f"| 状态机     | {original_count:4d} | {original_count / actual_count * 100:6.1f}%  |")
        print(f"| 峰值检测   | {peak_count:4d} | {peak_count / actual_count * 100:6.1f}%  |")
        print(f"| 最终结果   | {final_count:4d} | {accuracy:6.1f}%  |")
        print(f"| 用户实际   | {actual_count:4d} | 100.0%   |")


def load_csv_data(csv_path: str) -> List[dict]:
    """加载CSV数据"""
    rows = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "frame_id": int(row.get("frame_id", 0)),
                "timestamp": float(row.get("timestamp", 0)),
                "avg_hip_angle": float(row.get("avg_hip_angle", 0)),
                "avg_shoulder_angle": float(row.get("avg_shoulder_angle", 0)),
                "combined_angle": float(row.get("combined_angle", 0)),
                "state": row.get("state", "CLOSED"),
                "rep_count": int(row.get("rep_count", 0)),
            })
    return rows


def save_records(records: List[JumpingJackFrameRecord], prefix: str) -> Path:
    if not records:
        return None

    output_dir = PROJECT_ROOT / "test" / "data" / "samples" / "jumping_jack"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"{prefix}_{timestamp}.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))

    return csv_path


def analyze_thresholds():
    """分析阈值配置"""
    print("\n" + "=" * 60)
    print("阈值敏感性分析")
    print("=" * 60)

    configs = [
        {"closed_hip": 20, "open_hip": 50, "closed_shoulder": 30, "open_shoulder": 140},
        {"closed_hip": 30, "open_hip": 60, "closed_shoulder": 45, "open_shoulder": 150},
        {"closed_hip": 40, "open_hip": 70, "closed_shoulder": 60, "open_shoulder": 160},
    ]

    print("\n建议阈值配置:")
    print(f"| 配置 | 并拢髋角 | 分开髋角 | 下垂肩角 | 上举肩角 |")
    print(f"|------|----------|----------|----------|----------|")
    for i, cfg in enumerate(configs):
        print(f"| {i+1}    | {cfg['closed_hip']:8d}° | {cfg['open_hip']:8d}° | {cfg['closed_shoulder']:8d}° | {cfg['open_shoulder']:8d}° |")

    print("\n当前配置:")
    print(f"  CLOSED_HIP_THRESHOLD = {Config.CLOSED_HIP_THRESHOLD}°")
    print(f"  OPEN_HIP_THRESHOLD = {Config.OPEN_HIP_THRESHOLD}°")
    print(f"  CLOSED_SHOULDER_THRESHOLD = {Config.CLOSED_SHOULDER_THRESHOLD}°")
    print(f"  OPEN_SHOULDER_THRESHOLD = {Config.OPEN_SHOULDER_THRESHOLD}°")


def main():
    parser = argparse.ArgumentParser(
        description="开合跳算法测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  实时测试:
    python test/algorithm/jumping_jack_test.py --realtime --duration 60
    python test/algorithm/jumping_jack_test.py --realtime --no-rotate

  视频测试:
    python test/algorithm/jumping_jack_test.py --video jumping_jack.mp4 --ground-truth 20

  离线测试:
    python test/algorithm/jumping_jack_test.py --csv data.csv --actual-count 15

  阈值分析:
    python test/algorithm/jumping_jack_test.py --analyze
        """
    )

    parser.add_argument("--realtime", action="store_true", help="实时摄像头测试")
    parser.add_argument("--duration", type=int, default=60, help="测试时长(秒)")
    parser.add_argument("--no-rotate", action="store_true", help="不旋转画面(横屏摄像头)")
    parser.add_argument("--video", type=str, help="视频文件路径")
    parser.add_argument("--ground-truth", type=int, help="真实开合跳次数")
    parser.add_argument("--csv", type=str, help="CSV数据文件路径")
    parser.add_argument("--actual-count", type=int, help="CSV数据对应的真实次数")
    parser.add_argument("--analyze", action="store_true", help="分析阈值配置")

    args = parser.parse_args()
    rotate = not args.no_rotate

    if args.analyze:
        analyze_thresholds()
    elif args.realtime:
        realtime_test(args.duration, rotate)
    elif args.video:
        video_test(args.video, args.ground_truth)
    elif args.csv and args.actual_count:
        offline_test(args.csv, args.actual_count)
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("快速开始")
        print("=" * 60)
        print("1. 实时测试: python test/algorithm/jumping_jack_test.py --realtime")
        print("2. 视频测试: python test/algorithm/jumping_jack_test.py --video test/data/videos/your_video.mp4")
        print("3. 阈值分析: python test/algorithm/jumping_jack_test.py --analyze")


if __name__ == "__main__":
    main()
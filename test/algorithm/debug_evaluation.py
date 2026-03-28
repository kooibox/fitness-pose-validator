"""
调试版算法测试 - 记录详细数据用于分析
支持自适应阈值
"""

import argparse
import time
import sys
import csv
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config
from src.pose_detector import PoseDetector
from src.squat_counter import SquatCounter, PoseState
from src.adaptive_threshold import AdaptiveThresholdManager, run_calibration


SKELETON_CONNECTIONS = [
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (24, 26),
    (26, 28),
]


def draw_skeleton(frame, landmarks, color=(0, 255, 0)):
    if not landmarks:
        return frame
    h, w = frame.shape[:2]
    for connection in SKELETON_CONNECTIONS:
        idx1, idx2 = connection
        if idx1 < len(landmarks) and idx2 < len(landmarks):
            pt1, pt2 = landmarks[idx1], landmarks[idx2]
            x1, y1 = int(pt1.x * w), int(pt1.y * h)
            x2, y2 = int(pt2.x * w), int(pt2.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), color, 3)
    for i, landmark in enumerate(landmarks):
        x, y = int(landmark.x * w), int(landmark.y * h)
        cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)
    return frame


@dataclass
class FrameRecord:
    frame_id: int
    timestamp: float
    detected: bool
    left_angle: float
    right_angle: float
    avg_angle: float
    smoothed_angle: float
    state: str
    rep_count: int
    confirm_count: int
    left_hip_z: float
    left_knee_z: float
    left_ankle_z: float
    visibility_hip: float
    visibility_knee: float
    visibility_ankle: float


def debug_test(duration: int = 60, rotate: bool = True, adaptive: bool = False):
    print("\n" + "=" * 60)
    print("调试模式测试 - 记录详细数据")
    if adaptive:
        print("[自适应阈值模式]")
    print("=" * 60)
    print(f"测试时长: {duration}秒")
    print(f"画面旋转: {'开启' if rotate else '关闭'}")
    print("-" * 60)

    pose_detector = PoseDetector()
    squat_counter = SquatCounter()
    threshold_manager = AdaptiveThresholdManager() if adaptive else None

    standing_thresh = Config.STANDING_ANGLE_THRESHOLD
    squat_thresh = Config.SQUAT_ANGLE_THRESHOLD
    confirm_frames = squat_counter.CONFIRM_FRAMES

    print(f"初始阈值配置:")
    print(f"  站立阈值: {standing_thresh}")
    print(f"  下蹲阈值: {squat_thresh}")
    print(f"  确认帧数: {confirm_frames}")
    print("-" * 60)

    cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return

    width, height = Config.CAMERA_RESOLUTION
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    cv2.namedWindow("Debug Test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Debug Test", 800, 600)

    records: List[FrameRecord] = []
    frame_count = 0
    fps = 30
    start_time = time.time()
    no_detection_count = 0
    angle_samples = []

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
        left_angle = 0.0
        right_angle = 0.0
        avg_angle = 0.0
        smoothed = 0.0
        state = "UNKNOWN"
        rep_count = 0
        confirm_count = 0
        left_hip_z = 0.0
        left_knee_z = 0.0
        left_ankle_z = 0.0
        vis_hip = 0.0
        vis_knee = 0.0
        vis_ankle = 0.0

        if pose_data:
            normalized = pose_data.get("normalized")
            world = pose_data.get("world")

            if normalized and len(normalized) > 0:
                landmarks = normalized[0]
                frame = draw_skeleton(frame, landmarks)

                if len(landmarks) >= 29:
                    detected = True

                    if world and len(world) > 0:
                        wl = world[0]
                        left_hip_z = wl[23].z if hasattr(wl[23], "z") else 0
                        left_knee_z = wl[25].z if hasattr(wl[25], "z") else 0
                        left_ankle_z = wl[27].z if hasattr(wl[27], "z") else 0

                    vis_hip = (
                        landmarks[23].visibility
                        if hasattr(landmarks[23], "visibility")
                        else 1.0
                    )
                    vis_knee = (
                        landmarks[25].visibility
                        if hasattr(landmarks[25], "visibility")
                        else 1.0
                    )
                    vis_ankle = (
                        landmarks[27].visibility
                        if hasattr(landmarks[27], "visibility")
                        else 1.0
                    )

            metrics = squat_counter.update(pose_data)
            left_angle = metrics.left_knee_angle
            right_angle = metrics.right_knee_angle
            avg_angle = metrics.avg_knee_angle
            smoothed = squat_counter._left_smoother.value or avg_angle
            state = metrics.state.value
            rep_count = metrics.rep_count
            confirm_count = squat_counter._confirm_count

            if avg_angle > 0:
                angle_samples.append(avg_angle)

                if adaptive and threshold_manager:
                    threshold_manager.add_sample(avg_angle, metrics.state)

                    if frame_count > 0 and frame_count % 100 == 0:
                        result = threshold_manager.calibrate()
                        if result and result.confidence > 0.5:
                            squat_counter.standing_threshold = result.standing_threshold
                            squat_counter.squat_threshold = result.squat_threshold
                            standing_thresh = result.standing_threshold
                            squat_thresh = result.squat_threshold
        else:
            no_detection_count += 1

        records.append(
            FrameRecord(
                frame_id=frame_count,
                timestamp=time.time() - start_time,
                detected=detected,
                left_angle=left_angle,
                right_angle=right_angle,
                avg_angle=avg_angle,
                smoothed_angle=smoothed,
                state=state,
                rep_count=rep_count,
                confirm_count=confirm_count,
                left_hip_z=left_hip_z,
                left_knee_z=left_knee_z,
                left_ankle_z=left_ankle_z,
                visibility_hip=vis_hip,
                visibility_knee=vis_knee,
                visibility_ankle=vis_ankle,
            )
        )

        cv2.putText(
            frame,
            f"Count: {rep_count}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            f"Angle: {avg_angle:.0f} (raw)",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            f"Smooth: {smoothed:.0f}",
            (20, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"State: {state} [{confirm_count}/{confirm_frames}]",
            (20, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (200, 200, 200),
            2,
        )
        cv2.putText(
            frame,
            f"Thresh: {squat_thresh:.0f}/{standing_thresh:.0f}",
            (20, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (150, 150, 150),
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

        cv2.imshow("Debug Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    pose_detector.close()

    output_dir = PROJECT_ROOT / "test" / "data" / "samples" / "squat"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "debug_records.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))

    print("\n" + "=" * 60)
    print("测试结束!")
    print("=" * 60)

    print(f"\n--- 统计数据 ---")
    print(f"总帧数: {frame_count}")
    print(f"检测失败帧数: {no_detection_count}")
    print(f"检测成功率: {(frame_count - no_detection_count) / frame_count * 100:.1f}%")
    print(f"最终计数: {rep_count}")

    if angle_samples:
        print(f"\n--- 角度分析 ---")
        print(f"角度样本数: {len(angle_samples)}")
        print(f"最小角度: {min(angle_samples):.1f}")
        print(f"最大角度: {max(angle_samples):.1f}")
        print(f"平均角度: {np.mean(angle_samples):.1f}")
        print(f"角度范围: {max(angle_samples) - min(angle_samples):.1f}")

        actual_squat_thresh = squat_counter.squat_threshold
        actual_standing_thresh = squat_counter.standing_threshold

        below_squat = sum(1 for a in angle_samples if a < actual_squat_thresh)
        above_standing = sum(1 for a in angle_samples if a > actual_standing_thresh)
        in_transition = len(angle_samples) - below_squat - above_standing

        print(
            f"\n角度分布 (最终阈值: {actual_squat_thresh:.0f}/{actual_standing_thresh:.0f}):"
        )
        print(
            f"  < {actual_squat_thresh:.0f} (下蹲区): {below_squat} 帧 ({below_squat / len(angle_samples) * 100:.1f}%)"
        )
        print(
            f"  > {actual_standing_thresh:.0f} (站立区): {above_standing} 帧 ({above_standing / len(angle_samples) * 100:.1f}%)"
        )
        print(
            f"  过渡区: {in_transition} 帧 ({in_transition / len(angle_samples) * 100:.1f}%)"
        )

        if adaptive and threshold_manager:
            result = threshold_manager.calibrate()
            if result:
                print(f"\n--- 自适应校准结果 ---")
                print(f"推荐站立阈值: {result.standing_threshold:.1f}")
                print(f"推荐下蹲阈值: {result.squat_threshold:.1f}")
                print(f"置信度: {result.confidence * 100:.0f}%")

    print(f"\n数据已保存到: {csv_path}")

    true_count = int(input("\n请输入实际深蹲次数: "))

    if true_count > 0 and rep_count >= 0:
        accuracy = (
            min(rep_count, true_count) / true_count * 100
            if rep_count <= true_count
            else true_count / rep_count * 100
        )
        print(f"\n准确率: {accuracy:.1f}%")

        if rep_count < true_count:
            print(f"漏计数: {true_count - rep_count} 次")
        elif rep_count > true_count:
            print(f"多计数: {rep_count - true_count} 次")

    return records


def main():
    parser = argparse.ArgumentParser(description="调试模式测试")
    parser.add_argument("--duration", type=int, default=60, help="测试时长(秒)")
    parser.add_argument("--no-rotate", action="store_true", help="不旋转画面")
    parser.add_argument("--adaptive", action="store_true", help="启用自适应阈值")
    parser.add_argument("--calibrate", action="store_true", help="运行校准模式")

    args = parser.parse_args()
    rotate = not args.no_rotate

    if args.calibrate:
        run_calibration(args.duration)
    else:
        debug_test(args.duration, rotate, args.adaptive)


if __name__ == "__main__":
    main()

"""
视频转CSV工具
从视频文件中提取帧数据并保存到CSV
"""

import argparse
import sys
import csv
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config
from src.pose_detector import PoseDetector
from src.squat_counter import SquatCounter


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


def video_to_csv(video_path: str, output_filename: str = None):
    print("\n" + "=" * 60)
    print("视频数据提取工具")
    print("=" * 60)
    print(f"视频文件: {video_path}")
    print("-" * 60)

    pose_detector = PoseDetector()
    squat_counter = SquatCounter()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"错误: 无法打开视频 {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"视频帧数: {total_frames}, FPS: {fps:.1f}")
    print(f"预计时长: {total_frames / fps:.1f}秒")
    print("-" * 60)

    records: List[FrameRecord] = []
    frame_count = 0
    no_detection_count = 0
    angle_samples = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

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
        else:
            no_detection_count += 1

        records.append(
            FrameRecord(
                frame_id=frame_count,
                timestamp=frame_count / fps,
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

        if frame_count % 30 == 0:
            print(
                f"\r处理进度: {frame_count}/{total_frames} ({frame_count * 100 // total_frames}%)",
                end="",
            )

        frame_count += 1

    cap.release()
    pose_detector.close()

    output_dir = PROJECT_ROOT / "test" / "data" / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_filename is None:
        csv_path = output_dir / "debug_records.csv"
    else:
        csv_path = output_dir / output_filename

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))

    print(f"\n\n{'=' * 60}")
    print("数据提取完成!")
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
            f"\n角度分布 (阈值: {actual_squat_thresh:.0f}/{actual_standing_thresh:.0f}):"
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

    print(f"\n数据已保存到: {csv_path}")

    try:
        true_count = int(input("\n请输入视频中实际深蹲次数: "))
    except ValueError:
        true_count = 0

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


def main():
    parser = argparse.ArgumentParser(description="视频数据转CSV工具")
    parser.add_argument("--video", type=str, required=True, help="视频文件路径")
    parser.add_argument("--output", type=str, default=None, help="输出CSV文件名（默认：自动生成）")

    args = parser.parse_args()
    
    output_name = args.output
    if output_name is None:
        video_path = Path(args.video)
        output_name = f"{video_path.stem}_records.csv"
    
    video_to_csv(args.video, output_name)


if __name__ == "__main__":
    main()

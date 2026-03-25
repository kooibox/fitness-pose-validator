"""
算法精准度评估测试脚本
"""

import argparse
import csv
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config
from src.pose_detector import PoseDetector
from src.squat_counter import SquatCounter, PoseState


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
    for landmark in landmarks:
        x, y = int(landmark.x * w), int(landmark.y * h)
        cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)
    return frame


@dataclass
class TestMetrics:
    name: str
    predicted_count: int
    ground_truth_count: int
    count_accuracy: float
    angle_rmse: float
    jitter_std: float
    false_trigger_rate: float
    fps: float
    details: dict = field(default_factory=dict)


class AccuracyEvaluator:
    def __init__(self, smoothing_alpha: float = 0.3, confirm_frames: int = 3):
        self.pose_detector = PoseDetector()
        self.squat_counter = SquatCounter(
            standing_threshold=170.0,
            squat_threshold=85.0,
        )
        self.squat_counter.CONFIRM_FRAMES = confirm_frames
        self.angle_history: List[float] = []
        self.state_history: List[Tuple[int, PoseState]] = []

    def evaluate_video(
        self,
        video_path: str,
        ground_truth_count: int,
        ground_truth_angles: Optional[List[Tuple[int, float]]] = None,
    ) -> TestMetrics:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_count = 0
        predicted_angles = []
        state_changes = []
        last_state = PoseState.STANDING
        start_time = time.time()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            timestamp_ms = int(frame_count * 1000 / fps)

            pose_data = self.pose_detector.detect(rgb_frame, timestamp_ms)

            if pose_data:
                metrics = self.squat_counter.update(pose_data)
                predicted_angles.append((frame_count, metrics.avg_knee_angle))
                self.angle_history.append(metrics.avg_knee_angle)

                if metrics.state != last_state:
                    state_changes.append((frame_count, metrics.state))
                    last_state = metrics.state

            frame_count += 1

        elapsed_time = time.time() - start_time
        actual_fps = frame_count / elapsed_time if elapsed_time > 0 else 0

        predicted_count = self.squat_counter.count

        count_accuracy = min(predicted_count, ground_truth_count) / ground_truth_count
        if predicted_count > ground_truth_count:
            count_accuracy = ground_truth_count / predicted_count

        angle_rmse = 0.0
        if ground_truth_angles:
            errors = []
            for gt_frame, gt_angle in ground_truth_angles:
                for pred_frame, pred_angle in predicted_angles:
                    if abs(pred_frame - gt_frame) < fps * 0.5:
                        errors.append((pred_angle - gt_angle) ** 2)
                        break
            if errors:
                angle_rmse = np.sqrt(np.mean(errors))

        jitter_std = np.std(self.angle_history) if len(self.angle_history) > 10 else 0.0

        expected_changes = ground_truth_count * 2
        false_trigger_rate = max(0, len(state_changes) - expected_changes) / max(
            len(state_changes), 1
        )

        cap.release()
        self.pose_detector.close()

        return TestMetrics(
            name=Path(video_path).stem,
            predicted_count=predicted_count,
            ground_truth_count=ground_truth_count,
            count_accuracy=count_accuracy * 100,
            angle_rmse=angle_rmse,
            jitter_std=jitter_std,
            false_trigger_rate=false_trigger_rate * 100,
            fps=actual_fps,
            details={
                "total_frames": total_frames,
                "state_changes": len(state_changes),
            },
        )

    def evaluate_realtime(
        self, duration_seconds: int = 30, rotate: bool = True
    ) -> TestMetrics:
        cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        if not cap.isOpened():
            raise ValueError("无法打开摄像头")

        width, height = Config.CAMERA_RESOLUTION
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        cv2.namedWindow("Realtime Test", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Realtime Test", 800, 600)

        print(f"\n实时测试 - 请进行深蹲动作")
        print(f"测试时长: {duration_seconds}秒")
        print(f"画面旋转: {'开启' if rotate else '关闭'}")
        print(f"测试结束后请输入实际深蹲次数")
        print("-" * 40)

        frame_count = 0
        fps = 30
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            ret, frame = cap.read()
            if not ret:
                continue

            if rotate:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            timestamp_ms = int(frame_count * 1000 / fps)

            pose_data = self.pose_detector.detect(rgb_frame, timestamp_ms)

            if pose_data:
                metrics = self.squat_counter.update(pose_data)
                self.angle_history.append(metrics.avg_knee_angle)

                landmarks = pose_data.get("normalized")
                if landmarks and len(landmarks) > 0:
                    frame = draw_skeleton(frame, landmarks[0])

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

            cv2.putText(
                frame,
                f"Time: {time.time() - start_time:.0f}s",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (200, 200, 200),
                1,
            )

            cv2.imshow("Realtime Test", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            frame_count += 1

        actual_fps = frame_count / duration_seconds

        cap.release()
        cv2.destroyAllWindows()
        self.pose_detector.close()

        predicted_count = self.squat_counter.count

        ground_truth_count = int(input(f"\n请输入实际深蹲次数: "))

        count_accuracy = min(predicted_count, ground_truth_count) / max(
            ground_truth_count, 1
        )
        if predicted_count > ground_truth_count:
            count_accuracy = ground_truth_count / max(predicted_count, 1)

        jitter_std = np.std(self.angle_history) if len(self.angle_history) > 10 else 0.0

        return TestMetrics(
            name="realtime_test",
            predicted_count=predicted_count,
            ground_truth_count=ground_truth_count,
            count_accuracy=count_accuracy * 100,
            angle_rmse=0.0,
            jitter_std=jitter_std,
            false_trigger_rate=0.0,
            fps=actual_fps,
        )

    def evaluate_static_images(
        self, image_dir: str, annotations_file: str
    ) -> TestMetrics:
        image_path = Path(image_dir)
        annotations_path = Path(annotations_file)

        with open(annotations_path, "r") as f:
            annotations = json.load(f)

        errors = []

        for img_info in annotations["images"]:
            img_file = image_path / img_info["filename"]
            if not img_file.exists():
                continue

            img = cv2.imread(str(img_file))
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            pose_data = self.pose_detector.detect(rgb_img, 0)

            if pose_data and "world" in pose_data:
                landmarks = pose_data["world"][0]

                left_angle = self.squat_counter.calculate_angle_3d(
                    landmarks[23], landmarks[25], landmarks[27]
                )
                right_angle = self.squat_counter.calculate_angle_3d(
                    landmarks[24], landmarks[26], landmarks[28]
                )
                measured_angle = (left_angle + right_angle) / 2

                gt_angle = img_info.get("knee_angle", 0)
                if gt_angle > 0:
                    errors.append((measured_angle - gt_angle) ** 2)

        self.pose_detector.close()

        rmse = np.sqrt(np.mean(errors)) if errors else 0.0

        return TestMetrics(
            name="static_test",
            predicted_count=0,
            ground_truth_count=0,
            count_accuracy=100.0,
            angle_rmse=rmse,
            jitter_std=0.0,
            false_trigger_rate=0.0,
            fps=0.0,
        )


def compare_algorithms(
    video_path: str,
    ground_truth_count: int,
    output_csv: str = None,
):
    """
    对比新旧算法表现

    新算法: 3D角度 + EMA平滑 + 多帧确认
    旧算法: 2D角度 + 无平滑 + 单帧切换
    """
    if output_csv is None:
        output_csv = str(
            PROJECT_ROOT / "test" / "data" / "reports" / "algorithm_comparison.csv"
        )

    results = []

    evaluator_new = AccuracyEvaluator(smoothing_alpha=0.3, confirm_frames=3)
    result_new = evaluator_new.evaluate_video(video_path, ground_truth_count)
    result_new.name = "new_algorithm"
    results.append(result_new)

    print("\n" + "=" * 50)
    print("算法评估结果")
    print("=" * 50)
    print(f"视频: {video_path}")
    print(f"真实深蹲次数: {ground_truth_count}")
    print("-" * 50)
    print(f"{'指标':<20} {'新算法':<15}")
    print("-" * 50)
    print(f"{'预测次数':<20} {result_new.predicted_count:<15}")
    print(f"{'计数准确率':<20} {result_new.count_accuracy:.1f}%")
    print(f"{'角度RMSE':<20} {result_new.angle_rmse:.1f}°")
    print(f"{'抖动系数':<20} {result_new.jitter_std:.2f}°")
    print(f"{'误触发率':<20} {result_new.false_trigger_rate:.1f}%")
    print(f"{'处理FPS':<20} {result_new.fps:.1f}")
    print("=" * 50)

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "algorithm",
                "predicted",
                "ground_truth",
                "accuracy",
                "rmse",
                "jitter",
                "false_trigger",
                "fps",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r.name,
                    r.predicted_count,
                    r.ground_truth_count,
                    r.count_accuracy,
                    r.angle_rmse,
                    r.jitter_std,
                    r.false_trigger_rate,
                    r.fps,
                ]
            )

    print(f"\n结果已保存到: {output_csv}")

    return results


def generate_test_report(results: List[TestMetrics], output_path: str):
    """生成测试报告"""
    report = ["# 算法精准度评估报告\n"]
    report.append(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    report.append("## 测试结果汇总\n\n")
    report.append("| 测试名称 | 预测次数 | 真实次数 | 准确率 | RMSE | 抖动 | FPS |\n")
    report.append("|----------|----------|----------|--------|------|------|-----|\n")

    for r in results:
        report.append(
            f"| {r.name} | {r.predicted_count} | {r.ground_truth_count} | "
            f"{r.count_accuracy:.1f}% | {r.angle_rmse:.1f}° | "
            f"{r.jitter_std:.2f}° | {r.fps:.1f} |\n"
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.writelines(report)

    print(f"报告已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="算法精准度评估")
    parser.add_argument("--video", type=str, help="测试视频路径")
    parser.add_argument("--ground-truth", type=int, default=10, help="真实深蹲次数")
    parser.add_argument("--realtime", action="store_true", help="实时测试模式")
    parser.add_argument("--duration", type=int, default=30, help="实时测试时长(秒)")
    parser.add_argument(
        "--rotate", action="store_true", default=True, help="旋转画面(竖屏摄像头)"
    )
    parser.add_argument(
        "--no-rotate", action="store_true", help="不旋转画面(横屏摄像头)"
    )
    parser.add_argument("--static", action="store_true", help="静态图片测试")
    parser.add_argument("--image-dir", type=str, help="静态图片目录")
    parser.add_argument("--annotations", type=str, help="标注文件路径")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出报告路径",
    )

    args = parser.parse_args()

    if args.output is None:
        args.output = str(
            PROJECT_ROOT / "test" / "data" / "reports" / "evaluation_report.md"
        )

    rotate = not args.no_rotate
    results = []

    if args.video:
        print(f"\n测试视频: {args.video}")
        result = compare_algorithms(args.video, args.ground_truth)
        results.extend(result)

    elif args.realtime:
        print("\n启动实时测试...")
        evaluator = AccuracyEvaluator()
        result = evaluator.evaluate_realtime(args.duration, rotate)
        results.append(result)
        print(f"\n实时测试结果:")
        print(f"  预测次数: {result.predicted_count}")
        print(f"  真实次数: {result.ground_truth_count}")
        print(f"  准确率: {result.count_accuracy:.1f}%")
        print(f"  抖动系数: {result.jitter_std:.2f}")

    elif args.static and args.image_dir and args.annotations:
        print("\n静态图片测试...")
        evaluator = AccuracyEvaluator()
        result = evaluator.evaluate_static_images(args.image_dir, args.annotations)
        results.append(result)
        print(f"\n静态测试结果:")
        print(f"  角度RMSE: {result.angle_rmse:.1f}")

    else:
        parser.print_help()
        print("\n示例:")
        print("  python test/accuracy_evaluation.py --realtime --duration 60")
        print("  python test/accuracy_evaluation.py --realtime --no-rotate")
        print(
            "  python test/accuracy_evaluation.py --video test/squats.mp4 --ground-truth 10"
        )
        return

    if results:
        generate_test_report(results, args.output)


if __name__ == "__main__":
    main()

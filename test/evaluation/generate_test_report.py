#!/usr/bin/env python3
"""
量化测试报告生成器

运行完整的算法测试并生成量化报告
"""

import csv
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.squat_counter import SquatCounter, PeakDetector, PoseState
from src.form_analyzer import FormAnalyzer, StrictnessLevel
from src.adaptive_threshold import AdaptiveThresholdManager


@dataclass
class TestResult:
    test_name: str
    metric_name: str
    metric_value: float
    expected_value: Optional[float]
    passed: bool
    details: str


@dataclass
class AlgorithmMetrics:
    count_accuracy: float
    peak_detection_accuracy: float
    angle_rmse: float
    jitter_reduction: float
    false_positive_rate: float
    false_negative_rate: float


class TestReportGenerator:
    def __init__(self):
        self.results: List[TestResult] = []

    def test_peak_detector(self, csv_path: str, actual_count: int) -> AlgorithmMetrics:
        """测试峰值检测算法"""
        print("\n" + "=" * 60)
        print("测试 1: 峰值检测算法")
        print("=" * 60)

        rows = self._load_csv(csv_path)
        if not rows:
            print("错误: 无法加载数据")
            return None

        angles = [r["avg_angle"] for r in rows]
        timestamps = [r["timestamp"] for r in rows]

        detector = PeakDetector()
        for angle, ts in zip(angles, timestamps):
            detector.add_sample(angle, ts)

        predicted_count = detector.count

        accuracy = min(predicted_count, actual_count) / actual_count * 100
        if predicted_count > actual_count:
            accuracy = actual_count / predicted_count * 100

        over_count = max(0, predicted_count - actual_count)
        under_count = max(0, actual_count - predicted_count)

        print(f"真实次数: {actual_count}")
        print(f"检测次数: {predicted_count}")
        print(f"准确率: {accuracy:.1f}%")
        print(f"多计数: {over_count}, 漏计数: {under_count}")

        self.results.append(
            TestResult(
                test_name="peak_detection",
                metric_name="count_accuracy",
                metric_value=accuracy,
                expected_value=90.0,
                passed=accuracy >= 85.0,
                details=f"predicted={predicted_count}, actual={actual_count}",
            )
        )

        return AlgorithmMetrics(
            count_accuracy=accuracy,
            peak_detection_accuracy=accuracy,
            angle_rmse=0.0,
            jitter_reduction=0.0,
            false_positive_rate=over_count / actual_count * 100
            if actual_count > 0
            else 0,
            false_negative_rate=under_count / actual_count * 100
            if actual_count > 0
            else 0,
        )

    def test_angle_smoother(self, csv_path: str) -> float:
        """测试角度平滑效果"""
        print("\n" + "=" * 60)
        print("测试 2: EMA角度平滑")
        print("=" * 60)

        rows = self._load_csv(csv_path)
        if not rows:
            return 0.0

        from src.squat_counter import AngleSmoother

        smoother = AngleSmoother(alpha=0.3)
        raw_angles = [r["avg_angle"] for r in rows]
        smoothed_angles = []

        for angle in raw_angles:
            smoothed = smoother.update(angle)
            smoothed_angles.append(smoothed)

        raw_jitter = np.std(raw_angles)
        smooth_jitter = np.std(smoothed_angles)
        reduction = (1 - smooth_jitter / raw_jitter) * 100 if raw_jitter > 0 else 0

        print(f"原始角度抖动: {raw_jitter:.2f}°")
        print(f"平滑后抖动: {smooth_jitter:.2f}°")
        print(f"抖动减少: {reduction:.1f}%")

        self.results.append(
            TestResult(
                test_name="angle_smoother",
                metric_name="jitter_reduction",
                metric_value=reduction,
                expected_value=50.0,
                passed=reduction >= 40.0,
                details=f"raw={raw_jitter:.2f}, smooth={smooth_jitter:.2f}",
            )
        )

        return reduction

    def test_state_machine(self, csv_path: str, actual_count: int) -> float:
        """测试状态机计数"""
        print("\n" + "=" * 60)
        print("测试 3: 状态机计数")
        print("=" * 60)

        rows = self._load_csv(csv_path)
        if not rows:
            return 0.0

        angles = [r["avg_angle"] for r in rows]
        timestamps = [r["timestamp"] for r in rows]

        from src.squat_counter import AngleSmoother

        smoother = AngleSmoother(alpha=0.3)

        smoothed_angles = [smoother.update(a) for a in angles]

        from src.squat_counter import PoseState

        STANDING_THRESHOLD = 150.0
        SQUAT_THRESHOLD = 90.0
        CONFIRM_FRAMES = 2

        count = 0
        state = PoseState.STANDING
        confirm_count = 0

        for angle in smoothed_angles:
            if angle < SQUAT_THRESHOLD:
                target_state = PoseState.SQUATTING
            elif angle > STANDING_THRESHOLD:
                target_state = PoseState.STANDING
            else:
                confirm_count = 0
                continue

            if state == target_state:
                confirm_count = 0
                continue

            confirm_count += 1

            if confirm_count >= CONFIRM_FRAMES:
                if state == PoseState.SQUATTING and target_state == PoseState.STANDING:
                    count += 1
                state = target_state
                confirm_count = 0

        accuracy = (
            min(count, actual_count) / actual_count * 100 if actual_count > 0 else 0
        )
        if count > actual_count:
            accuracy = actual_count / count * 100

        print(f"状态机计数: {count}")
        print(f"准确率: {accuracy:.1f}%")

        self.results.append(
            TestResult(
                test_name="state_machine",
                metric_name="count_accuracy",
                metric_value=accuracy,
                expected_value=85.0,
                passed=accuracy >= 80.0,
                details=f"count={count}, actual={actual_count}",
            )
        )

        return accuracy

    def test_adaptive_threshold(self) -> float:
        """测试自适应阈值"""
        print("\n" + "=" * 60)
        print("测试 4: 自适应阈值")
        print("=" * 60)

        manager = AdaptiveThresholdManager()

        for _ in range(60):
            manager.add_sample(160.0, PoseState.STANDING)
            manager.add_sample(70.0, PoseState.SQUATTING)

        result = manager.calibrate()

        if result:
            print(f"校准成功")
            print(f"站立阈值: {result.standing_threshold:.1f}°")
            print(f"下蹲阈值: {result.squat_threshold:.1f}°")
            print(f"置信度: {result.confidence * 100:.0f}%")

            passed = (
                140 < result.standing_threshold < 175
                and 70 < result.squat_threshold < 110
            )

            self.results.append(
                TestResult(
                    test_name="adaptive_threshold",
                    metric_name="calibration_confidence",
                    metric_value=result.confidence * 100,
                    expected_value=70.0,
                    passed=passed,
                    details=f"standing={result.standing_threshold:.1f}, squat={result.squat_threshold:.1f}",
                )
            )

            return result.confidence * 100
        else:
            print("校准失败")
            self.results.append(
                TestResult(
                    test_name="adaptive_threshold",
                    metric_name="calibration_confidence",
                    metric_value=0.0,
                    expected_value=70.0,
                    passed=False,
                    details="calibration failed",
                )
            )
            return 0.0

    def _load_csv(self, csv_path: str) -> List[dict]:
        """加载CSV数据"""
        rows = []
        try:
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(
                        {
                            "frame_id": int(row.get("frame_id", 0)),
                            "timestamp": float(row.get("timestamp", 0)),
                            "avg_angle": float(row.get("avg_angle", 0)),
                            "state": row.get("state", "STANDING"),
                            "rep_count": int(row.get("rep_count", 0)),
                        }
                    )
        except Exception as e:
            print(f"加载CSV失败: {e}")
        return rows

    def generate_report(self, output_path: str = None):
        """生成测试报告"""
        if output_path is None:
            output_path = str(
                PROJECT_ROOT / "test" / "data" / "reports" / "test_report.md"
            )
        report = []
        report.append("# 算法测试量化报告\n")
        report.append(
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        report.append("## 测试结果汇总\n\n")
        report.append("| 测试名称 | 指标 | 实测值 | 期望值 | 通过 | 详情 |\n")
        report.append("|----------|------|--------|--------|------|------|\n")

        passed_count = 0
        for r in self.results:
            status = "✅" if r.passed else "❌"
            expected = f"{r.expected_value:.1f}" if r.expected_value else "-"
            report.append(
                f"| {r.test_name} | {r.metric_name} | {r.metric_value:.1f} | "
                f"{expected} | {status} | {r.details} |\n"
            )
            if r.passed:
                passed_count += 1

        report.append(
            f"\n**通过率**: {passed_count}/{len(self.results)} "
            f"({passed_count / len(self.results) * 100:.0f}%)\n"
        )

        report.append("\n## 测试详情\n\n")
        report.append("### 1. 峰值检测算法\n")
        report.append("- 谷值计数法，检测下蹲最低点\n")
        report.append("- 解决快速运动漏检问题\n\n")

        report.append("### 2. EMA角度平滑\n")
        report.append("- 指数移动平均滤波\n")
        report.append("- 减少关键点抖动\n\n")

        report.append("### 3. 状态机计数\n")
        report.append("- 多帧确认机制\n")
        report.append("- 结合峰值检测结果\n\n")

        report.append("### 4. 自适应阈值\n")
        report.append("- 自动学习用户角度范围\n")
        report.append("- 动态调整站立/下蹲阈值\n\n")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(report)

        print(f"\n报告已生成: {output_path}")

        json_path = output_path.replace(".md", ".json")

        # 自定义JSON编码器处理numpy类型
        class NumpyEncoder(json.JSONEncoder):
            def default(self, o):
                if hasattr(o, "item"):  # numpy scalar
                    return o.item()
                if hasattr(o, "tolist"):  # numpy array
                    return o.tolist()
                return super().default(o)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2,
                ensure_ascii=False,
                cls=NumpyEncoder,
            )

        print(f"JSON数据已保存: {json_path}")

        return passed_count == len(self.results)


def main():
    parser = argparse.ArgumentParser(description="生成量化测试报告")
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="测试数据CSV路径",
    )
    parser.add_argument(
        "--actual-count", type=int, default=None, help="真实深蹲次数（默认从CSV读取）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出报告路径",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent.parent
    csv_path = script_dir / "data" / "samples" / "debug_records.csv"

    if not csv_path.exists() and args.csv:
        csv_path = Path(args.csv)

    if not csv_path.exists():
        print(f"错误: CSV文件不存在: {csv_path}")
        print("请将CSV文件放到: test\\data\\samples\\debug_records.csv")
        print("或使用 --csv 参数指定路径")
        return 1

    actual_count = args.actual_count
    if actual_count is None:
        generator = TestReportGenerator()
        rows = generator._load_csv(str(csv_path))
        actual_count = rows[-1]["rep_count"] if rows else 0
        print(f"从CSV读取actual_count: {actual_count}")

    generator = TestReportGenerator()

    generator.test_peak_detector(str(csv_path), actual_count)
    generator.test_angle_smoother(str(csv_path))
    generator.test_state_machine(str(csv_path), actual_count)
    generator.test_adaptive_threshold()

    all_passed = generator.generate_report(args.output)

    return 0 if all_passed else 1


if __name__ == "__main__":
    import argparse

    sys.exit(main())

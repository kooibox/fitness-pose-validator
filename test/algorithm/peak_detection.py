#!/usr/bin/env python3
"""
峰值检测算法验证脚本

使用已有的CSV数据验证峰值检测算法的效果
"""

import csv
import sys
import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from src.squat_counter import PeakDetector


def load_csv_data(csv_path: str):
    """加载CSV数据"""
    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "frame_id": int(row["frame_id"]),
                    "timestamp": float(row["timestamp"]),
                    "avg_angle": float(row["avg_angle"]),
                    "state": row["state"],
                    "rep_count": int(row["rep_count"]),
                }
            )
    return rows


def test_peak_detection(csv_path: str, actual_count: int):
    """测试峰值检测算法"""
    print("=" * 60)
    print("峰值检测算法验证")
    print("=" * 60)

    rows = load_csv_data(csv_path)
    print(f"\n加载数据: {len(rows)} 帧")
    print(f"用户实际深蹲次数: {actual_count}")

    original_count = rows[-1]["rep_count"]
    print(f"原始算法计数: {original_count}")
    print(f"原始准确率: {original_count / actual_count * 100:.1f}%")

    detector = PeakDetector()

    for row in rows:
        detector.add_sample(row["avg_angle"], row["timestamp"])

    peak_count = detector.count
    print(f"\n峰值检测计数: {peak_count}")
    print(f"峰值检测准确率: {peak_count / actual_count * 100:.1f}%")

    improvement = (
        (peak_count - original_count) / original_count * 100
        if original_count > 0
        else 0
    )
    print(f"\n改进效果: +{peak_count - original_count} 次 ({improvement:.0f}% 提升)")

    print("\n" + "-" * 60)
    print("检测到的峰谷详情:")
    print("-" * 60)

    print(f"\n谷值(下蹲最低点): {len(detector.valleys)} 个")
    for i, v in enumerate(detector.valleys[:10]):
        print(f"  {i + 1}. 帧{v.frame_id}: {v.angle:.1f}°")
    if len(detector.valleys) > 10:
        print(f"  ... 还有 {len(detector.valleys) - 10} 个")

    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print(f"| 算法       | 计数 | 准确率   |")
    print(f"|------------|------|----------|")
    print(
        f"| 原始状态机 | {original_count:4d} | {original_count / actual_count * 100:6.1f}%  |"
    )
    print(
        f"| 峰值检测   | {peak_count:4d} | {peak_count / actual_count * 100:6.1f}%  |"
    )
    print(f"| 用户实际   | {actual_count:4d} | 100.0%   |")

    return peak_count


def analyze_params(csv_path: str, actual_count: int):
    """分析不同参数的效果"""
    print("\n" + "=" * 60)
    print("参数敏感性分析")
    print("=" * 60)

    rows = load_csv_data(csv_path)

    configs = [
        {"valley": 80, "rise": 105, "min_frames": 6},
        {"valley": 85, "rise": 110, "min_frames": 8},
        {"valley": 90, "rise": 115, "min_frames": 10},
        {"valley": 85, "rise": 110, "min_frames": 6},
    ]

    print(f"\n| Valley阈值 | Rise阈值 | 最小帧数 | 计数 | 准确率 |")
    print(f"|------------|----------|----------|------|--------|")

    for cfg in configs:
        detector = PeakDetector()
        detector.VALLEY_THRESHOLD = cfg["valley"]
        detector.RISE_THRESHOLD = cfg["rise"]
        detector.MIN_FRAMES_BETWEEN_VALLEYS = cfg["min_frames"]

        for row in rows:
            detector.add_sample(row["avg_angle"], row["timestamp"])

        accuracy = detector.count / actual_count * 100 if actual_count > 0 else 0
        print(
            f"| {cfg['valley']:10d}° | {cfg['rise']:8d}° | {cfg['min_frames']:8d} | {detector.count:4d} | {accuracy:5.1f}% |"
        )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="峰值检测算法验证")
    parser.add_argument("--csv", type=str, default=None, help="CSV文件路径")
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.csv:
        csv_path = args.csv
    else:
        csv_path = os.path.join(script_dir, "..", "data", "samples", "squat", "debug_records.csv")

    if not os.path.exists(csv_path):
        print(f"错误: CSV文件不存在: {csv_path}")
        print(f"请将CSV文件放到: test\\data\\samples\\debug_records.csv")
        sys.exit(1)

    rows = load_csv_data(csv_path)
    actual_count = max([r["rep_count"] for r in rows]) if rows else 0
    print(f"从CSV读取最大计数: {actual_count}")

    if actual_count == 0:
        print("警告: CSV中计数为0，请手动输入实际深蹲次数")
        try:
            actual_count = int(input("请输入实际深蹲次数: "))
        except ValueError:
            actual_count = 0

    test_peak_detection(csv_path, actual_count)
    analyze_params(csv_path, actual_count)

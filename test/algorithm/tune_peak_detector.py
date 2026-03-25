"""
峰值检测参数优化工具
自动寻找最优参数组合
"""

import csv
import itertools
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.squat_counter import PeakDetector


def load_csv_data(csv_path: str):
    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "frame_id": int(row["frame_id"]),
                "timestamp": float(row["timestamp"]),
                "avg_angle": float(row["avg_angle"]),
                "state": row["state"],
                "rep_count": int(row["rep_count"]),
            })
    return rows


def grid_search(rows, actual_count):
    print("=" * 70)
    print("峰值检测参数网格搜索")
    print("=" * 70)
    print(f"实际深蹲次数: {actual_count}")
    print(f"总帧数: {len(rows)}")
    print("-" * 70)

    valley_range = range(65, 100, 5)
    rise_range = range(100, 160, 10)
    min_frames_range = range(5, 50, 5)

    best_accuracy = 0
    best_params = None
    results = []

    total = len(list(valley_range)) * len(list(rise_range)) * len(list(min_frames_range))
    print(f"测试组合数: {total}")
    print("-" * 70)
    print(f"{'Valley':<8} {'Rise':<8} {'MinFrames':<10} {'计数':<6} {'准确率':<8}")
    print("-" * 70)

    for valley in valley_range:
        for rise in rise_range:
            for min_frames in min_frames_range:
                detector = PeakDetector()
                detector.VALLEY_THRESHOLD = valley
                detector.RISE_THRESHOLD = rise
                detector.MIN_FRAMES_BETWEEN_VALLEYS = min_frames

                for row in rows:
                    detector.add_sample(row["avg_angle"], row["timestamp"])

                count = detector.count
                accuracy = count / actual_count * 100 if actual_count > 0 else 0

                results.append({
                    "valley": valley,
                    "rise": rise,
                    "min_frames": min_frames,
                    "count": count,
                    "accuracy": accuracy,
                })

                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_params = (valley, rise, min_frames)

                if abs(accuracy - 100) < 5 or (count > 150 and count < 220):
                    print(f"{valley:<8}° {rise:<8}° {min_frames:<10} {count:<6} {accuracy:<7.1f}%")

    print("-" * 70)
    print(f"\n最优参数:")
    print(f"  Valley阈值: {best_params[0]}°")
    print(f"  Rise阈值: {best_params[1]}°")
    print(f"  最小帧数: {best_params[2]}")
    print(f"  准确率: {best_accuracy:.1f}%")

    top_results = sorted(results, key=lambda x: abs(x["accuracy"] - 100))[:10]
    print(f"\n--- Top 10 最优组合 ---")
    print(f"{'Valley':<8} {'Rise':<8} {'MinFrames':<10} {'计数':<6} {'准确率':<8}")
    for r in top_results:
        print(f"{r['valley']:<8}° {r['rise']:<8}° {r['min_frames']:<10} {r['count']:<6} {r['accuracy']:<7.1f}%")

    return best_params


def quick_tune(rows, actual_count):
    print("\n" + "=" * 70)
    print("快速调参（基于数据分析）")
    print("=" * 70)

    angles = [r["avg_angle"] for r in rows]
    min_angle = min(angles)
    max_angle = max(angles)

    print(f"角度范围: {min_angle:.1f}° ~ {max_angle:.1f}°")

    below_90_count = sum(1 for a in angles if a < 90)
    below_85_count = sum(1 for a in angles if a < 85)
    below_80_count = sum(1 for a in angles if a < 80)

    print(f"低于90°: {below_90_count} 帧")
    print(f"低于85°: {below_85_count} 帧")
    print(f"低于80°: {below_80_count} 帧")

    recommended_valley = 85
    if below_85_count > below_80_count * 2:
        recommended_valley = 80
    if below_90_count > len(angles) * 0.15:
        recommended_valley = 90

    print(f"\n推荐 Valley阈值: {recommended_valley}°")

    configs = [
        {"valley": recommended_valley, "rise": 110, "min_frames": 8},
        {"valley": recommended_valley, "rise": 120, "min_frames": 10},
        {"valley": recommended_valley, "rise": 130, "min_frames": 15},
        {"valley": recommended_valley - 5, "rise": 110, "min_frames": 8},
        {"valley": recommended_valley + 5, "rise": 110, "min_frames": 8},
    ]

    print(f"\n| Valley | Rise | MinFrames | 计数 | 准确率 |")
    print(f"|--------|------|-----------|------|--------|")

    best = None
    for cfg in configs:
        detector = PeakDetector()
        detector.VALLEY_THRESHOLD = cfg["valley"]
        detector.RISE_THRESHOLD = cfg["rise"]
        detector.MIN_FRAMES_BETWEEN_VALLEYS = cfg["min_frames"]

        for row in rows:
            detector.add_sample(row["avg_angle"], row["timestamp"])

        count = detector.count
        accuracy = count / actual_count * 100 if actual_count > 0 else 0

        print(f"| {cfg['valley']:6}° | {cfg['rise']:4}° | {cfg['min_frames']:10} | {count:4} | {accuracy:5.1f}% |")

        if best is None or abs(accuracy - 100) < abs(best["accuracy"] - 100):
            best = {**cfg, "count": count, "accuracy": accuracy}

    print(f"\n推荐配置: Valley={best['valley']}°, Rise={best['rise']}°, MinFrames={best['min_frames']}")
    return best


def main():
    script_dir = Path(__file__).parent.parent
    csv_path = script_dir / "data" / "samples" / "debug_records.csv"

    if not csv_path.exists():
        print(f"错误: CSV文件不存在: {csv_path}")
        return 1

    rows = load_csv_data(str(csv_path))

    print(f"\n请输入视频中实际深蹲次数: ", end="")
    try:
        actual_count = int(input())
    except ValueError:
        actual_count = 173
        print(f"使用默认值: {actual_count}")

    print("\n选择调参模式:")
    print("  1. 网格搜索（全面测试，找到最优）")
    print("  2. 快速调参（基于数据特征，推荐配置）")
    print("  3. 退出")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == "1":
        grid_search(rows, actual_count)
    elif choice == "2":
        quick_tune(rows, actual_count)
    else:
        print("退出")

    return 0


if __name__ == "__main__":
    sys.exit(main())
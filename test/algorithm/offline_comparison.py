"""
离线对比测试：使用历史数据对比新旧算法

从数据库读取历史角度数据，分别用新旧算法处理，对比结果
"""

import sqlite3
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum


class PoseState(Enum):
    STANDING = "STANDING"
    SQUATTING = "SQUATTING"


@dataclass
class TestResult:
    session_id: int
    true_count: int
    old_count: int
    new_count: int
    old_accuracy: float
    new_accuracy: float
    old_jitter: float
    new_jitter: float
    old_false_triggers: int
    new_false_triggers: int


class OldAlgorithm:
    """旧算法：2D角度 + 无平滑 + 单帧切换"""

    def __init__(self, standing_thresh: float = 155.0, squat_thresh: float = 90.0):
        self.standing_thresh = standing_thresh
        self.squat_thresh = squat_thresh
        self.count = 0
        self.state = PoseState.STANDING

    def update(self, avg_angle: float) -> Tuple[PoseState, int]:
        if self.state == PoseState.STANDING:
            if avg_angle < self.squat_thresh:
                self.state = PoseState.SQUATTING
        elif self.state == PoseState.SQUATTING:
            if avg_angle > self.standing_thresh:
                self.count += 1
                self.state = PoseState.STANDING
        return self.state, self.count

    def reset(self):
        self.count = 0
        self.state = PoseState.STANDING


class NewAlgorithm:
    """新算法：EMA平滑 + 多帧确认"""

    CONFIRM_FRAMES = 2
    ALPHA = 0.3

    def __init__(self, standing_thresh: float = 155.0, squat_thresh: float = 90.0):
        self.standing_thresh = standing_thresh
        self.squat_thresh = squat_thresh
        self.count = 0
        self.state = PoseState.STANDING
        self.confirm_count = 0
        self.smoothed_angle = None

    def update(self, raw_angle: float) -> Tuple[PoseState, int]:
        # EMA平滑
        if self.smoothed_angle is None:
            self.smoothed_angle = raw_angle
        else:
            self.smoothed_angle = (
                self.ALPHA * raw_angle + (1 - self.ALPHA) * self.smoothed_angle
            )

        # 判断目标状态
        if self.smoothed_angle < self.squat_thresh:
            target_state = PoseState.SQUATTING
        elif self.smoothed_angle > self.standing_thresh:
            target_state = PoseState.STANDING
        else:
            self.confirm_count = 0
            return self.state, self.count

        # 状态一致
        if self.state == target_state:
            self.confirm_count = 0
            return self.state, self.count

        # 累计确认
        self.confirm_count += 1

        # 达到确认帧数
        if self.confirm_count >= self.CONFIRM_FRAMES:
            if self.state == PoseState.SQUATTING and target_state == PoseState.STANDING:
                self.count += 1
            self.state = target_state
            self.confirm_count = 0

        return self.state, self.count

    def reset(self):
        self.count = 0
        self.state = PoseState.STANDING
        self.confirm_count = 0
        self.smoothed_angle = None


def run_comparison_test(db_path: str = None):
    """运行对比测试"""
    import os

    if db_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        db_path = os.path.join(project_root, "data", "fitness_data.db")

    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        print("请确保在项目根目录运行，或检查 data/fitness_data.db 是否存在")
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id, COUNT(*) as records, 
               MAX(rep_count) as true_count
        FROM squat_records 
        GROUP BY session_id
        HAVING true_count > 0
        ORDER BY session_id DESC
        LIMIT 20
    """)

    sessions = cursor.fetchall()
    print(f"找到 {len(sessions)} 个有效训练会话\n")

    old_algo = OldAlgorithm()
    new_algo = NewAlgorithm()

    results: List[TestResult] = []

    for session_id, record_count, true_count in sessions:
        cursor.execute(
            """
            SELECT avg_angle FROM squat_records 
            WHERE session_id = ? 
            ORDER BY timestamp
        """,
            (session_id,),
        )

        angles = [row[0] for row in cursor.fetchall()]

        if len(angles) < 10:
            continue

        old_algo.reset()
        new_algo.reset()

        old_angles = []
        new_angles = []
        old_state_changes = []
        new_state_changes = []

        last_old_state = PoseState.STANDING
        last_new_state = PoseState.STANDING

        for angle in angles:
            old_state, old_count = old_algo.update(angle)
            new_state, new_count = new_algo.update(angle)

            old_angles.append(angle)  # 旧算法不平滑
            new_angles.append(new_algo.smoothed_angle)

            if old_state != last_old_state:
                old_state_changes.append(old_state)
                last_old_state = old_state
            if new_state != last_new_state:
                new_state_changes.append(new_state)
                last_new_state = new_state

        old_count = old_algo.count
        new_count = new_algo.count

        old_accuracy = min(old_count, true_count) / max(true_count, 1)
        new_accuracy = min(new_count, true_count) / max(true_count, 1)

        if old_count > true_count:
            old_accuracy = true_count / max(old_count, 1)
        if new_count > true_count:
            new_accuracy = true_count / max(new_count, 1)

        old_jitter = np.std(old_angles) if len(old_angles) > 10 else 0
        new_jitter = (
            np.std([a for a in new_angles if a is not None])
            if len(new_angles) > 10
            else 0
        )

        expected_changes = true_count * 2
        old_false = max(0, len(old_state_changes) - expected_changes)
        new_false = max(0, len(new_state_changes) - expected_changes)

        results.append(
            TestResult(
                session_id=session_id,
                true_count=true_count,
                old_count=old_count,
                new_count=new_count,
                old_accuracy=old_accuracy * 100,
                new_accuracy=new_accuracy * 100,
                old_jitter=old_jitter,
                new_jitter=new_jitter,
                old_false_triggers=old_false,
                new_false_triggers=new_false,
            )
        )

    conn.close()

    print("=" * 70)
    print("算法对比测试结果")
    print("=" * 70)
    print(
        f"{'Session':<10} {'真实':<6} {'旧算法':<8} {'新算法':<8} {'旧准确率':<10} {'新准确率':<10}"
    )
    print("-" * 70)

    total_old_acc = 0
    total_new_acc = 0
    total_old_jitter = 0
    total_new_jitter = 0
    total_old_false = 0
    total_new_false = 0

    for r in results:
        print(
            f"{r.session_id:<10} {r.true_count:<6} {r.old_count:<8} {r.new_count:<8} "
            f"{r.old_accuracy:.1f}%{'':<5} {r.new_accuracy:.1f}%"
        )
        total_old_acc += r.old_accuracy
        total_new_acc += r.new_accuracy
        total_old_jitter += r.old_jitter
        total_new_jitter += r.new_jitter
        total_old_false += r.old_false_triggers
        total_new_false += r.new_false_triggers

    n = len(results)
    print("-" * 70)
    print(
        f"{'平均':<10} {'':<6} {'':<8} {'':<8} "
        f"{total_old_acc / n:.1f}%{'':<5} {total_new_acc / n:.1f}%"
    )
    print("=" * 70)

    print("\n抖动系数对比 (越小越稳定):")
    print(f"  旧算法: {total_old_jitter / n:.2f}°")
    print(f"  新算法: {total_new_jitter / n:.2f}°")
    print(f"  改善: {(1 - total_new_jitter / total_old_jitter) * 100:.1f}%")

    print("\n误触发次数对比:")
    print(f"  旧算法: {total_old_false} 次")
    print(f"  新算法: {total_new_false} 次")

    improvement = total_new_acc / n - total_old_acc / n
    print("\n" + "=" * 70)
    print("总结:")
    print(f"  计数准确率提升: {improvement:.1f}%")
    print(f"  抖动减少: {(1 - total_new_jitter / total_old_jitter) * 100:.1f}%")
    print(f"  误触发减少: {total_old_false - total_new_false} 次")
    print("=" * 70)

    return results


if __name__ == "__main__":
    import sys
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    run_comparison_test()

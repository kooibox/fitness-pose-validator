"""
深蹲计数模块

实现基于膝角角度的深蹲动作计数逻辑。
优化版: 3D角度计算 + EMA平滑 + 多帧状态确认 + 峰值检测
"""

import math
import time
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Protocol
from collections import deque

from src.config import Config
from src.database import Database


class Landmark(Protocol):
    """关键点协议，定义 x, y, z 属性"""

    x: float
    y: float
    z: float


class PoseState(Enum):
    """姿态状态枚举"""

    STANDING = "STANDING"
    SQUATTING = "SQUATTING"


@dataclass
class SquatMetrics:
    """深蹲指标数据类"""

    rep_count: int
    state: PoseState
    left_knee_angle: float
    right_knee_angle: float
    avg_knee_angle: float
    peak_count: int = 0  # 峰值检测计数


@dataclass
class AngleSample:
    """角度样本，用于峰值检测"""

    angle: float
    timestamp: float
    frame_id: int


@dataclass
class PeakValley:
    """峰谷数据结构"""

    frame_id: int
    angle: float
    timestamp: float
    is_peak: bool  # True=峰值(站立), False=谷值(下蹲)


class AngleSmoother:
    """
    指数移动平均角度平滑器

    计算复杂度: O(1)
    内存开销: 仅存储上一帧值
    """

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.value: Optional[float] = None

    def update(self, new_value: float) -> float:
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

    def reset(self) -> None:
        self.value = None


class PeakDetector:
    """
    峰值检测器 - 解决快速运动漏检问题

    核心算法：谷值计数法 + 状态验证
    - 检测谷值（下蹲最低点）来计数
    - 验证角度从上一个谷值回升后才能计数下一个谷值
    - 解决连续深蹲不完全站立的问题
    """

    BUFFER_SIZE = 50
    VALLEY_THRESHOLD = 95.0
    RISE_THRESHOLD = 120.0
    MIN_FRAMES_BETWEEN_VALLEYS = 30

    def __init__(self):
        self._buffer: deque = deque(maxlen=self.BUFFER_SIZE)
        self._valleys: List[PeakValley] = []
        self._peak_count = 0
        self._last_valley_frame = -100
        self._last_valley_angle = 180.0
        self._has_risen = True
        self._frame_id = 0
        self._last_processed_frame = -1

    def add_sample(self, angle: float, timestamp: float) -> int:
        self._buffer.append(AngleSample(angle, timestamp, self._frame_id))

        if len(self._buffer) >= 3:
            self._detect_and_count()

        self._frame_id += 1
        return self._peak_count

    def _detect_and_count(self) -> None:
        samples = list(self._buffer)
        n = len(samples)

        i = n - 2
        if i < 1:
            return

        prev_angle = samples[i - 1].angle
        curr_angle = samples[i].angle
        next_angle = samples[i + 1].angle
        frame = samples[i].frame_id
        ts = samples[i].timestamp

        if frame <= self._last_processed_frame:
            return

        self._last_processed_frame = frame

        if curr_angle > self.RISE_THRESHOLD:
            self._has_risen = True

        is_valley = (
            curr_angle < prev_angle
            and curr_angle < next_angle
            and curr_angle < self.VALLEY_THRESHOLD
            and curr_angle > 10.0
        )

        if is_valley:
            if (
                frame - self._last_valley_frame >= self.MIN_FRAMES_BETWEEN_VALLEYS
                and self._has_risen
            ):
                valley = PeakValley(frame, curr_angle, ts, is_peak=False)
                self._valleys.append(valley)
                self._peak_count += 1
                self._last_valley_frame = frame
                self._last_valley_angle = curr_angle
                self._has_risen = False

    @property
    def count(self) -> int:
        return self._peak_count

    @property
    def valleys(self) -> List[PeakValley]:
        return self._valleys

    def reset(self) -> None:
        self._buffer.clear()
        self._valleys.clear()
        self._peak_count = 0
        self._last_valley_frame = -100
        self._last_valley_angle = 180.0
        self._has_risen = True
        self._last_processed_frame = -1
        self._frame_id = 0


class SquatCounter:
    """
    深蹲计数器类

    通过检测膝关节角度变化来计数深蹲动作。
    使用状态机模式：STANDING <-> SQUATTING

    优化特性:
    - 3D世界坐标角度计算
    - EMA时序平滑
    - 多帧状态确认
    """

    CONFIRM_FRAMES = 2

    def __init__(
        self,
        database: Optional[Database] = None,
        session_id: Optional[int] = None,
        standing_threshold: float = Config.STANDING_ANGLE_THRESHOLD,
        squat_threshold: float = Config.SQUAT_ANGLE_THRESHOLD,
        buffer_size: int = Config.RECORD_BUFFER_SIZE,
        smoothing_alpha: float = 0.3,
    ):
        self.standing_threshold = standing_threshold
        self.squat_threshold = squat_threshold
        self.buffer_size = buffer_size

        self._count = 0
        self._state = PoseState.STANDING
        self._confirm_count = 0
        self._left_knee_angle = 0.0
        self._right_knee_angle = 0.0
        self._avg_knee_angle = 0.0
        self._left_smoother = AngleSmoother(alpha=smoothing_alpha)
        self._right_smoother = AngleSmoother(alpha=smoothing_alpha)
        self._peak_detector = PeakDetector()
        self._database = database
        self._session_id = session_id
        self._record_buffer: List[tuple] = []
        self._timestamp = 0.0

    @staticmethod
    def calculate_angle_2d(a: Landmark, b: Landmark, c: Landmark) -> float:
        """
        使用2D坐标计算角度（备用方法）

        Args:
            a, b, c: 三个关键点，b为顶点

        Returns:
            float: 角度值（0-180度）
        """
        radians = math.atan2(c.y - b.y, c.x - b.x) - math.atan2(a.y - b.y, a.x - b.x)
        angle = abs(radians * 180.0 / math.pi)
        if angle > 180.0:
            angle = 360.0 - angle
        return angle

    @staticmethod
    def calculate_angle_3d(a: Landmark, b: Landmark, c: Landmark) -> float:
        """
        使用3D世界坐标计算角度

        比2D方法更精确，不受视角影响。

        Args:
            a, b, c: 三个关键点（需有x, y, z属性），b为顶点

        Returns:
            float: 角度值（0-180度）
        """
        ba = np.array([a.x, a.y, a.z]) - np.array([b.x, b.y, b.z])
        bc = np.array([c.x, c.y, c.z]) - np.array([b.x, b.y, b.z])

        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)

        if norm_ba < 1e-8 or norm_bc < 1e-8:
            return 0.0

        cosine = np.dot(ba, bc) / (norm_ba * norm_bc)
        cosine = np.clip(cosine, -1.0, 1.0)

        return np.degrees(np.arccos(cosine))

    def update(self, pose_data: Optional[Dict]) -> SquatMetrics:
        """
        根据姿态关键点更新计数状态。

        Args:
            pose_data: 检测结果字典，包含:
                - 'normalized': 归一化坐标的关键点列表
                - 'world': 3D世界坐标的关键点列表

        Returns:
            SquatMetrics: 当前深蹲指标
        """
        if not pose_data:
            return self._get_metrics()

        world_landmarks = pose_data.get("world")
        normalized_landmarks = pose_data.get("normalized")

        if world_landmarks and len(world_landmarks) > 0:
            landmarks = world_landmarks[0]
            use_3d = True
        elif normalized_landmarks and len(normalized_landmarks) > 0:
            landmarks = normalized_landmarks[0]
            use_3d = False
        else:
            return self._get_metrics()

        if len(landmarks) < 29:
            return self._get_metrics()

        cfg = Config
        left_hip = landmarks[cfg.LEFT_HIP]
        left_knee = landmarks[cfg.LEFT_KNEE]
        left_ankle = landmarks[cfg.LEFT_ANKLE]
        right_hip = landmarks[cfg.RIGHT_HIP]
        right_knee = landmarks[cfg.RIGHT_KNEE]
        right_ankle = landmarks[cfg.RIGHT_ANKLE]

        # 计算原始角度
        if use_3d:
            raw_left = self.calculate_angle_3d(left_hip, left_knee, left_ankle)
            raw_right = self.calculate_angle_3d(right_hip, right_knee, right_ankle)
        else:
            raw_left = self.calculate_angle_2d(left_hip, left_knee, left_ankle)
            raw_right = self.calculate_angle_2d(right_hip, right_knee, right_ankle)

        self._left_knee_angle = self._left_smoother.update(raw_left)
        self._right_knee_angle = self._right_smoother.update(raw_right)
        self._avg_knee_angle = (self._left_knee_angle + self._right_knee_angle) / 2

        self._timestamp = time.time()
        self._peak_detector.add_sample(self._avg_knee_angle, self._timestamp)

        self._update_state_with_confirm()
        self._record_frame()

        return self._get_metrics()

    def _update_state_with_confirm(self) -> None:
        """多帧确认的状态转换，消除抖动误触发"""
        if self._avg_knee_angle < self.squat_threshold:
            target_state = PoseState.SQUATTING
        elif self._avg_knee_angle > self.standing_threshold:
            target_state = PoseState.STANDING
        else:
            self._confirm_count = 0
            return

        if self._state == target_state:
            self._confirm_count = 0
            return

        self._confirm_count += 1

        if self._confirm_count >= self.CONFIRM_FRAMES:
            if (
                self._state == PoseState.SQUATTING
                and target_state == PoseState.STANDING
            ):
                self._count += 1
            self._state = target_state
            self._confirm_count = 0

    def _record_frame(self) -> None:
        """记录当前帧数据到缓冲区"""
        if self._database is None or self._session_id is None:
            return

        self._record_buffer.append(
            (
                self._session_id,
                datetime.now().isoformat(),
                self._left_knee_angle,
                self._right_knee_angle,
                self._avg_knee_angle,
                self._state.value,
                self._count,
            )
        )

        if len(self._record_buffer) >= self.buffer_size:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """将缓冲区数据写入数据库"""
        if not self._record_buffer or self._database is None:
            return

        self._database.insert_records(self._record_buffer)
        self._record_buffer.clear()

    def _get_metrics(self) -> SquatMetrics:
        """获取当前指标"""
        final_count = max(self._count, self._peak_detector.count)
        return SquatMetrics(
            rep_count=final_count,
            state=self._state,
            left_knee_angle=self._left_knee_angle,
            right_knee_angle=self._right_knee_angle,
            avg_knee_angle=self._avg_knee_angle,
            peak_count=self._peak_detector.count,
        )

    @property
    def count(self) -> int:
        """当前深蹲计数（状态机）"""
        return self._count

    @property
    def peak_count(self) -> int:
        """峰值检测计数"""
        return self._peak_detector.count

    @property
    def final_count(self) -> int:
        """最终计数（取两种方法的较大值）"""
        return max(self._count, self._peak_detector.count)

    @property
    def state(self) -> PoseState:
        """当前姿态状态"""
        return self._state

    def reset(self) -> None:
        """重置计数器状态"""
        self._count = 0
        self._state = PoseState.STANDING
        self._confirm_count = 0
        self._record_buffer.clear()
        self._left_smoother.reset()
        self._right_smoother.reset()
        self._peak_detector.reset()

    def close(self) -> None:
        """关闭计数器，刷新缓冲区"""
        self._flush_buffer()

"""
开合跳计数模块 v2.0

实现基于关键点距离的开合跳动作计数逻辑。
使用状态机模式: CLOSED <-> OPEN

检测原理:
- 3D 欧氏距离: 统一使用 world 坐标计算
- 自适应阈值: 基于百分位数法动态校准
- 时序一致性: 状态持续时间约束 + 连续帧确认
- 峰值检测: 基于时间的动态间隔

版本历史:
- v1.0: 初始版本
- v2.0: 修复阈值硬编码、open_ratio 计算、统一 3D 坐标
"""

import math
import time
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Protocol
from collections import deque

from src.config import Config
from src.database import Database


class Landmark(Protocol):
    x: float
    y: float
    z: float


class JumpingJackState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"


@dataclass
class JumpingJackMetrics:
    rep_count: int
    state: JumpingJackState
    left_hip_angle: float
    right_hip_angle: float
    avg_hip_angle: float
    left_shoulder_angle: float
    right_shoulder_angle: float
    avg_shoulder_angle: float
    peak_count: int = 0
    ankle_distance: float = 0.0
    wrist_height: float = 0.0
    open_ratio: float = 0.0
    is_calibrated: bool = False


@dataclass
class DistanceSample:
    value: float
    timestamp: float
    frame_id: int


@dataclass
class PeakValley:
    frame_id: int
    value: float
    timestamp: float
    is_peak: bool


class DistanceSmoother:
    """距离平滑器 (EMA)"""
    
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


class AdaptiveJumpingJackThreshold:
    """
    开合跳自适应阈值
    
    基于百分位数法动态校准阈值，适应不同用户体型和拍摄距离
    """
    
    def __init__(self, sample_size: int = 300):
        self.sample_size = sample_size
        self._ankle_samples: deque = deque(maxlen=sample_size)
        self._wrist_samples: deque = deque(maxlen=sample_size)
        
        # 默认阈值（会在校准后更新）
        self.ankle_open_threshold = 0.30
        self.ankle_close_threshold = 0.20
        self.wrist_open_threshold = 0.50
        self.wrist_close_threshold = 0.10
        
        self._is_calibrated = False
        self._calibration_progress = 0.0
    
    def add_sample(self, ankle_ratio: float, wrist_ratio: float) -> None:
        """添加样本用于校准"""
        self._ankle_samples.append(ankle_ratio)
        self._wrist_samples.append(wrist_ratio)
        
        self._calibration_progress = len(self._ankle_samples) / self.sample_size
        
        if len(self._ankle_samples) >= self.sample_size and not self._is_calibrated:
            self._calibrate()
    
    def _calibrate(self) -> None:
        """基于百分位数法校准阈值"""
        ankle_arr = np.array(self._ankle_samples)
        wrist_arr = np.array(self._wrist_samples)
        
        # OPEN 阈值：取第 75 百分位数
        self.ankle_open_threshold = float(np.percentile(ankle_arr, 75))
        self.wrist_open_threshold = float(np.percentile(wrist_arr, 75))
        
        # CLOSE 阈值：取第 25 百分位数
        self.ankle_close_threshold = float(np.percentile(ankle_arr, 25))
        self.wrist_close_threshold = float(np.percentile(wrist_arr, 25))
        
        # 确保阈值有一定间隔
        min_gap = 0.02
        if self.ankle_open_threshold - self.ankle_close_threshold < min_gap:
            mid = (self.ankle_open_threshold + self.ankle_close_threshold) / 2
            self.ankle_open_threshold = mid + min_gap / 2
            self.ankle_close_threshold = mid - min_gap / 2
        
        self._is_calibrated = True
        print(f"[自适应阈值] 校准完成:")
        print(f"  - 踝距: OPEN={self.ankle_open_threshold:.3f}, CLOSE={self.ankle_close_threshold:.3f}")
        print(f"  - 腕高: OPEN={self.wrist_open_threshold:.3f}, CLOSE={self.wrist_close_threshold:.3f}")
    
    @property
    def is_calibrated(self) -> bool:
        return self._is_calibrated
    
    @property
    def calibration_progress(self) -> float:
        return self._calibration_progress
    
    def reset(self) -> None:
        self._ankle_samples.clear()
        self._wrist_samples.clear()
        self._is_calibrated = False
        self._calibration_progress = 0.0


class DistancePeakDetector:
    """
    基于距离的峰值检测器 v2.0
    
    检测开合跳的"开"状态峰值，用于计数
    改进：基于时间的动态间隔
    """
    BUFFER_SIZE = 45
    MIN_TIME_BETWEEN_PEAKS = 0.4  # 0.4 秒（快速动作约 0.5 秒一个）

    def __init__(self):
        self._buffer: deque = deque(maxlen=self.BUFFER_SIZE)
        self._peaks: List[PeakValley] = []
        self._peak_count = 0
        self._last_peak_time = 0.0
        self._has_dropped = False
        self._frame_id = 0
        self._last_processed_frame = -1
        
        # 自适应阈值
        self._peak_threshold = 0.6
        self._valley_threshold = 0.3
        self._value_history: deque = deque(maxlen=100)

    def add_sample(self, value: float, timestamp: float) -> int:
        self._buffer.append(DistanceSample(value, timestamp, self._frame_id))
        self._value_history.append(value)

        # 动态更新阈值
        if len(self._value_history) >= 50:
            self._update_thresholds()

        if len(self._buffer) >= 3:
            self._detect_and_count(timestamp)

        self._frame_id += 1
        return self._peak_count
    
    def _update_thresholds(self) -> None:
        """基于历史数据更新峰值/谷值阈值"""
        arr = np.array(self._value_history)
        self._peak_threshold = float(np.percentile(arr, 70))
        self._valley_threshold = float(np.percentile(arr, 30))

    def _detect_and_count(self, current_time: float) -> None:
        samples = list(self._buffer)
        n = len(samples)

        i = n - 2
        if i < 1:
            return

        prev_val = samples[i - 1].value
        curr_val = samples[i].value
        next_val = samples[i + 1].value
        frame = samples[i].frame_id
        ts = samples[i].timestamp

        if frame <= self._last_processed_frame:
            return

        self._last_processed_frame = frame

        if curr_val < self._valley_threshold:
            self._has_dropped = True

        is_peak = (
            curr_val > prev_val
            and curr_val > next_val
            and curr_val > self._peak_threshold
        )

        if is_peak and self._has_dropped:
            time_since_last = current_time - self._last_peak_time
            if time_since_last >= self.MIN_TIME_BETWEEN_PEAKS:
                peak = PeakValley(frame, curr_val, ts, is_peak=True)
                self._peaks.append(peak)
                self._peak_count += 1
                self._last_peak_time = current_time
                self._has_dropped = False

    @property
    def count(self) -> int:
        return self._peak_count

    @property
    def peaks(self) -> List[PeakValley]:
        return self._peaks

    def reset(self) -> None:
        self._buffer.clear()
        self._peaks.clear()
        self._peak_count = 0
        self._last_peak_time = 0.0
        self._has_dropped = False
        self._last_processed_frame = -1
        self._frame_id = 0
        self._value_history.clear()
        self._peak_threshold = 0.6
        self._valley_threshold = 0.3


class JumpingJackCounter:
    """
    开合跳计数器 v2.0

    改进:
    - 统一使用 3D World 坐标
    - 自适应阈值系统
    - 时序一致性校验
    - 持续方向检测 + 置信度累积

    检测原理:
    - 脚踝 3D 欧氏距离: 检测双腿开合程度
    - 手腕高度: 检测双臂上下位置
    - 躯干长度归一化: 适应不同拍摄距离
    """

    CONFIRM_FRAMES = 2  # 连续 2 帧确认状态
    MIN_STATE_DURATION = 0.15  # 状态最少持续 0.15 秒
    DIRECTION_CONFIRM_THRESHOLD = 10  # 方向检测确认阈值
    
    # MediaPipe 关键点索引
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    NOSE = 0
    LEFT_EAR = 7
    RIGHT_EAR = 8

    def __init__(
        self,
        database: Optional[Database] = None,
        session_id: Optional[int] = None,
        buffer_size: int = Config.RECORD_BUFFER_SIZE,
        smoothing_alpha: float = 0.3,
    ):
        self.buffer_size = buffer_size

        # 计数相关
        self._count = 0
        self._state = JumpingJackState.CLOSED
        self._confirm_count = 0
        
        # 距离指标
        self._ankle_distance = 0.0
        self._wrist_height = 0.0
        self._open_ratio = 0.0
        self._shoulder_width = 0.0
        self._torso_length = 0.0
        
        # 方向检测（持续检测 + 置信度）
        self._is_front_facing = True
        self._direction_detected = False
        self._front_facing_confidence = 0
        
        # 自适应阈值
        self._adaptive_threshold = AdaptiveJumpingJackThreshold(sample_size=300)
        
        # 历史极值（用于 open_ratio 计算）
        self._ankle_min = float('inf')
        self._ankle_max = float('-inf')
        self._wrist_min = float('inf')
        self._wrist_max = float('-inf')
        self._history_window = deque(maxlen=300)  # 5秒历史
        
        # 平滑器
        self._ankle_smoother = DistanceSmoother(alpha=smoothing_alpha)
        self._wrist_smoother = DistanceSmoother(alpha=smoothing_alpha)
        self._open_ratio_smoother = DistanceSmoother(alpha=smoothing_alpha)

        # 峰值检测器
        self._peak_detector = DistancePeakDetector()
        
        # 数据库相关
        self._database = database
        self._session_id = session_id
        self._record_buffer: List[tuple] = []
        self._timestamp = 0.0
        
        # 角度（预留）
        self._left_hip_angle = 0.0
        self._right_hip_angle = 0.0
        self._avg_hip_angle = 0.0
        self._left_shoulder_angle = 0.0
        self._right_shoulder_angle = 0.0
        self._avg_shoulder_angle = 0.0
        
        # 时序一致性
        self._state_history = deque(maxlen=5)
        self._last_state_change_time = 0.0

    @staticmethod
    def _calculate_3d_distance(p1: Landmark, p2: Landmark) -> float:
        """计算 3D 欧氏距离"""
        return math.sqrt(
            (p1.x - p2.x) ** 2 +
            (p1.y - p2.y) ** 2 +
            (p1.z - p2.z) ** 2
        )

    def _detect_facing_direction(self, landmarks) -> Optional[bool]:
        """
        持续方向检测（带置信度累积）
        
        Returns:
            True: 正面, False: 背身, None: 未确认
        """
        left_shoulder = landmarks[self.LEFT_SHOULDER]
        right_shoulder = landmarks[self.RIGHT_SHOULDER]
        left_hip = landmarks[self.LEFT_HIP]
        right_hip = landmarks[self.RIGHT_HIP]
        
        # 方法1：肩宽比髋宽（更稳定）
        shoulder_width = self._calculate_3d_distance(left_shoulder, right_shoulder)
        hip_width = self._calculate_3d_distance(left_hip, right_hip)
        
        # 正面时肩宽/髋宽比接近 1.3-1.5
        # 背身时肩宽/髋宽比更大（因透视）
        shoulder_hip_ratio = shoulder_width / (hip_width + 0.001)
        
        is_front_ratio = shoulder_hip_ratio < 1.8
        
        # 方法2：肩部 Z 深度差（正面时左右肩 Z 接近）
        shoulder_z_diff = abs(left_shoulder.z - right_shoulder.z)
        is_front_z = shoulder_z_diff < 0.15
        
        # 方法3：耳朵可见性（正面时耳朵更可见）
        try:
            left_ear = landmarks[self.LEFT_EAR]
            right_ear = landmarks[self.RIGHT_EAR]
            ear_visible = (left_ear.visibility > 0.5 and right_ear.visibility > 0.5)
            is_front_ear = ear_visible
        except (IndexError, AttributeError):
            is_front_ear = True  # 无法判断时默认
        
        # 综合判断（加权投票）
        votes = [is_front_ratio, is_front_z, is_front_ear]
        current_detected = sum(votes) >= 2
        
        # 置信度累积
        if current_detected == self._is_front_facing:
            self._front_facing_confidence += 1
        else:
            self._front_facing_confidence -= 2
        
        self._front_facing_confidence = max(0, min(20, self._front_facing_confidence))
        
        # 达到阈值才更新方向
        if self._front_facing_confidence >= self.DIRECTION_CONFIRM_THRESHOLD:
            self._direction_detected = True
            return self._is_front_facing
        
        # 尝试更新内部判断（但不确认）
        if self._front_facing_confidence >= 5:
            self._is_front_facing = current_detected
        
        return None  # 未确认

    def _calculate_distances(self, landmarks) -> tuple:
        """
        计算关键点距离（使用 3D 欧氏距离）
        
        使用躯干长度作为主要归一化基准，更稳定
        """
        left_ankle = landmarks[self.LEFT_ANKLE]
        right_ankle = landmarks[self.RIGHT_ANKLE]
        left_wrist = landmarks[self.LEFT_WRIST]
        right_wrist = landmarks[self.RIGHT_WRIST]
        left_shoulder = landmarks[self.LEFT_SHOULDER]
        right_shoulder = landmarks[self.RIGHT_SHOULDER]
        left_hip = landmarks[self.LEFT_HIP]
        right_hip = landmarks[self.RIGHT_HIP]

        # 肩宽（3D）
        self._shoulder_width = self._calculate_3d_distance(left_shoulder, right_shoulder)
        
        # 躯干长度（3D 欧氏距离）
        torso_left = self._calculate_3d_distance(left_shoulder, left_hip)
        torso_right = self._calculate_3d_distance(right_shoulder, right_hip)
        self._torso_length = (torso_left + torso_right) / 2
        
        if self._torso_length < 0.01:
            self._torso_length = 0.1

        # 踝距（3D 欧氏距离，不再只用 X 轴）
        ankle_distance_3d = self._calculate_3d_distance(left_ankle, right_ankle)
        ankle_ratio = ankle_distance_3d / self._torso_length

        # 腕高（相对于髋部的 Y 高度）
        left_wrist_height = left_hip.y - left_wrist.y
        right_wrist_height = right_hip.y - right_wrist.y
        avg_wrist_height = (left_wrist_height + right_wrist_height) / 2
        wrist_ratio = avg_wrist_height / self._torso_length

        return ankle_ratio, wrist_ratio

    def _calculate_open_ratio(self, ankle_ratio: float, wrist_ratio: float) -> float:
        """
        计算综合开合比例（基于历史极值归一化）
        
        使用动态范围进行归一化，不依赖绝对阈值
        """
        # 更新历史极值
        self._ankle_min = min(self._ankle_min, ankle_ratio)
        self._ankle_max = max(self._ankle_max, ankle_ratio)
        self._wrist_min = min(self._wrist_min, wrist_ratio)
        self._wrist_max = max(self._wrist_max, wrist_ratio)
        
        # 基于历史极值归一化
        ankle_range = self._ankle_max - self._ankle_min
        wrist_range = self._wrist_max - self._wrist_min
        
        if ankle_range > 0.01:
            leg_score = (ankle_ratio - self._ankle_min) / ankle_range
        else:
            leg_score = 0.5
        
        if wrist_range > 0.01:
            arm_score = (wrist_ratio - self._wrist_min) / wrist_range
        else:
            arm_score = 0.5
        
        leg_score = max(0, min(1, leg_score))
        arm_score = max(0, min(1, arm_score))
        
        return (leg_score + arm_score) / 2

    def update(self, pose_data: Optional[Dict]) -> JumpingJackMetrics:
        if not pose_data:
            return self._get_metrics()

        # 统一使用 world 坐标
        world_landmarks = pose_data.get("world")
        
        if not world_landmarks or len(world_landmarks) == 0:
            return self._get_metrics()
        
        landmarks = world_landmarks[0]

        if len(landmarks) < 29:
            return self._get_metrics()

        # 持续方向检测
        self._detect_facing_direction(landmarks)

        # 计算距离
        raw_ankle, raw_wrist = self._calculate_distances(landmarks)
        
        # 添加到自适应阈值样本
        self._adaptive_threshold.add_sample(raw_ankle, raw_wrist)
        
        # 平滑处理
        self._ankle_distance = self._ankle_smoother.update(raw_ankle)
        self._wrist_height = self._wrist_smoother.update(raw_wrist)
        
        # 计算开合比例
        raw_open_ratio = self._calculate_open_ratio(self._ankle_distance, self._wrist_height)
        self._open_ratio = self._open_ratio_smoother.update(raw_open_ratio)

        self._timestamp = time.time()
        self._peak_detector.add_sample(self._open_ratio, self._timestamp)

        # 更新状态（带时序一致性）
        self._update_state_with_consistency()

        return self._get_metrics()

    def _update_state_with_consistency(self) -> None:
        """
        带时序一致性的状态更新
        
        使用自适应阈值 + 时序约束
        """
        current_time = time.time()
        
        # 物理约束：状态切换间隔
        time_since_change = current_time - self._last_state_change_time
        if time_since_change < self.MIN_STATE_DURATION:
            return  # 防止过快切换
        
        # 确定目标状态
        target_state = self._determine_target_state()
        
        if target_state is None:
            self._confirm_count = 0
            return
        
        if self._state == target_state:
            self._confirm_count = 0
            return
        
        # 时序一致性：连续帧确认
        self._state_history.append(target_state)
        
        if len(self._state_history) >= 2:
            # 最近 2 帧都是目标状态
            if all(s == target_state for s in list(self._state_history)[-2:]):
                # 状态切换
                if (self._state == JumpingJackState.OPEN and 
                    target_state == JumpingJackState.CLOSED):
                    self._count += 1
                    print(f"[计数] 开合跳 #{self._count}")
                
                self._state = target_state
                self._last_state_change_time = current_time
                self._confirm_count = 0

    def _determine_target_state(self) -> Optional[JumpingJackState]:
        """确定目标状态（使用自适应阈值）"""
        if self._adaptive_threshold.is_calibrated:
            # 校准后使用自适应阈值
            ankle_open = self._adaptive_threshold.ankle_open_threshold
            ankle_close = self._adaptive_threshold.ankle_close_threshold
            wrist_open = self._adaptive_threshold.wrist_open_threshold
            wrist_close = self._adaptive_threshold.wrist_close_threshold
            
            # 使用 open_ratio 作为主要判断依据（更可靠）
            if self._open_ratio > 0.55:
                return JumpingJackState.OPEN
            elif self._open_ratio < 0.45:
                return JumpingJackState.CLOSED
            
            # 备用：使用踝距判断（开合跳腿部动作更明显）
            if self._ankle_distance >= ankle_open:
                return JumpingJackState.OPEN
            elif self._ankle_distance <= ankle_close:
                return JumpingJackState.CLOSED
            
            return None
        else:
            # 校准前使用 open_ratio 相对判断
            if self._open_ratio > 0.6:
                return JumpingJackState.OPEN
            elif self._open_ratio < 0.4:
                return JumpingJackState.CLOSED
            return None

    def _get_metrics(self) -> JumpingJackMetrics:
        final_count = max(self._count, self._peak_detector.count)
        return JumpingJackMetrics(
            rep_count=final_count,
            state=self._state,
            left_hip_angle=self._left_hip_angle,
            right_hip_angle=self._right_hip_angle,
            avg_hip_angle=self._avg_hip_angle,
            left_shoulder_angle=self._left_shoulder_angle,
            right_shoulder_angle=self._right_shoulder_angle,
            avg_shoulder_angle=self._avg_shoulder_angle,
            peak_count=self._peak_detector.count,
            ankle_distance=self._ankle_distance,
            wrist_height=self._wrist_height,
            open_ratio=self._open_ratio,
            is_calibrated=self._adaptive_threshold.is_calibrated,
        )

    @property
    def count(self) -> int:
        return self._count

    @property
    def peak_count(self) -> int:
        return self._peak_detector.count

    @property
    def final_count(self) -> int:
        return max(self._count, self._peak_detector.count)

    @property
    def state(self) -> JumpingJackState:
        return self._state
    
    @property
    def is_calibrated(self) -> bool:
        return self._adaptive_threshold.is_calibrated
    
    @property
    def calibration_progress(self) -> float:
        return self._adaptive_threshold.calibration_progress

    def reset(self) -> None:
        self._count = 0
        self._state = JumpingJackState.CLOSED
        self._confirm_count = 0
        self._record_buffer.clear()
        self._ankle_smoother.reset()
        self._wrist_smoother.reset()
        self._open_ratio_smoother.reset()
        self._peak_detector.reset()
        self._adaptive_threshold.reset()
        self._ankle_distance = 0.0
        self._wrist_height = 0.0
        self._open_ratio = 0.0
        self._ankle_min = float('inf')
        self._ankle_max = float('-inf')
        self._wrist_min = float('inf')
        self._wrist_max = float('-inf')
        self._history_window.clear()
        self._state_history.clear()
        self._last_state_change_time = 0.0
        self._front_facing_confidence = 0
        self._direction_detected = False

    def close(self) -> None:
        pass

"""
动作姿态分析模块

实时分析深蹲动作姿态，检测常见错误并提供反馈。
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import deque

from src.config import Config
from src.squat_counter import PoseState


class FeedbackType(Enum):
    """反馈类型枚举"""
    DEPTH_INSUFFICIENT = "depth_insufficient"  # 下蹲不够深
    DEEP_ENOUGH = "deep_enough"                # 下蹲深度足够
    KNEE_VALGUS = "knee_valgus"                # 膝盖内扣
    BACK_BENT = "back_bent"                    # 背部弯曲
    TORSO_LEAN = "torso_lean"                  # 身体过度前倾
    TOO_FAST = "too_fast"                      # 动作过快
    GOOD_FORM = "good_form"                    # 动作标准


class Severity(Enum):
    """严重程度枚举"""
    OK = 0       # 正常
    INFO = 1     # 提示
    WARNING = 2  # 警告
    ERROR = 3    # 错误（可能导致受伤）


class StrictnessLevel(Enum):
    """严格程度档位"""
    RELAXED = "relaxed"    # 宽松
    NORMAL = "normal"      # 标准
    STRICT = "strict"      # 严格


# 各档位的阈值配置
STRICTNESS_CONFIG = {
    StrictnessLevel.RELAXED: {
        # 深度阈值
        "depth_error_angle": 130.0,      # 角度 > 130° 才算错误
        "depth_warning_angle": 115.0,
        # 膝盖内扣阈值
        "knee_valgus_error": 0.5,        # 更宽松
        "knee_valgus_warning": 0.35,
        # 背部弯曲阈值
        "back_error_angle": 35.0,        # 更宽松
        "back_warning_angle": 25.0,
        # 容忍度（错误帧占比超过此值才算无效）
        "error_tolerance": 0.5,          # 50%以上的帧有错误才无效
    },
    StrictnessLevel.NORMAL: {
        "depth_error_angle": 115.0,
        "depth_warning_angle": 100.0,
        "knee_valgus_error": 0.4,
        "knee_valgus_warning": 0.25,
        "back_error_angle": 25.0,
        "back_warning_angle": 15.0,
        "error_tolerance": 0.3,          # 30%以上的帧有错误才无效
    },
    StrictnessLevel.STRICT: {
        "depth_error_angle": 100.0,      # 更严格
        "depth_warning_angle": 90.0,
        "knee_valgus_error": 0.3,        # 更严格
        "knee_valgus_warning": 0.2,
        "back_error_angle": 20.0,        # 更严格
        "back_warning_angle": 12.0,
        "error_tolerance": 0.15,         # 15%以上的帧有错误就无效
    },
}


@dataclass
class FormFeedback:
    """姿态反馈数据类"""
    type: FeedbackType
    severity: Severity
    message: str
    value: float = 0.0
    target: float = 0.0
    joints_to_highlight: Tuple[int, ...] = ()  # 需要高亮的关键点索引


@dataclass
class FormAnalysis:
    """姿态分析结果"""
    feedbacks: List[FormFeedback]
    overall_severity: Severity
    knee_valgus_score: float      # 0-1, 0=正常, 1=严重内扣
    back_angle: float             # 背部角度（偏离垂直的角度）
    depth_percentage: float       # 下蹲深度百分比
    velocity: float               # 角度变化速度
    
    @property
    def has_errors(self) -> bool:
        return any(fb.severity == Severity.ERROR for fb in self.feedbacks)
    
    @property
    def has_warnings(self) -> bool:
        return any(fb.severity == Severity.WARNING for fb in self.feedbacks)


class FormAnalyzer:
    """
    动作姿态分析器
    
    实时分析深蹲动作姿态，检测以下问题：
    1. 下蹲深度不足
    2. 膝盖内扣
    3. 背部弯曲
    4. 动作速度过快
    
    支持三档严格程度：宽松、标准、严格
    """
    
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    
    DEPTH_GOOD_ANGLE = 90.0
    VELOCITY_WARNING = 80.0
    VELOCITY_ERROR = 120.0
    
    TRIGGER_FRAMES = {
        FeedbackType.KNEE_VALGUS: 5,
        FeedbackType.BACK_BENT: 5,
        FeedbackType.DEPTH_INSUFFICIENT: 3,
        FeedbackType.TOO_FAST: 2,
    }
    
    def __init__(self, history_size: int = 30, strictness: StrictnessLevel = StrictnessLevel.NORMAL):
        self._history_size = history_size
        self._strictness = strictness
        self._config = STRICTNESS_CONFIG[strictness]
        
        self._angle_history: deque = deque(maxlen=history_size)
        self._time_history: deque = deque(maxlen=history_size)
        self._frame_counters: Dict[FeedbackType, int] = {}
        self._last_analysis: Optional[FormAnalysis] = None
        
        self._squat_frame_count = 0
        self._error_frame_count = 0
    
    def set_strictness(self, level: StrictnessLevel):
        self._strictness = level
        self._config = STRICTNESS_CONFIG[level]
    
    def get_strictness(self) -> StrictnessLevel:
        return self._strictness
    
    def start_new_rep(self):
        self._squat_frame_count = 0
        self._error_frame_count = 0
    
    def is_rep_valid(self) -> bool:
        if self._squat_frame_count == 0:
            return True
        tolerance = self._config["error_tolerance"]
        error_ratio = self._error_frame_count / self._squat_frame_count
        return error_ratio < tolerance
    
    def analyze(
        self, 
        landmarks: List, 
        knee_angle: float,
        state: PoseState,
        timestamp: float
    ) -> FormAnalysis:
        if not landmarks or len(landmarks[0]) < 29:
            return self._empty_analysis()
        
        person = landmarks[0]
        feedbacks: List[FormFeedback] = []
        
        knee_valgus_score = self._check_knee_valgus(person)
        back_angle = self._calculate_back_angle(person)
        velocity = self._calculate_velocity(knee_angle, timestamp)
        
        if state == PoseState.SQUATTING:
            self._squat_frame_count += 1
        
        if state == PoseState.SQUATTING:
            depth_feedback = self._check_depth(knee_angle)
            if depth_feedback:
                feedbacks.append(depth_feedback)
        
        valgus_feedback = self._check_valgus(knee_valgus_score)
        if valgus_feedback:
            feedbacks.append(valgus_feedback)
        
        back_feedback = self._check_back(posture_angle=back_angle)
        if back_feedback:
            feedbacks.append(back_feedback)
        
        speed_feedback = self._check_speed(velocity)
        if speed_feedback:
            feedbacks.append(speed_feedback)
        
        if not feedbacks and state == PoseState.SQUATTING:
            feedbacks.append(FormFeedback(
                type=FeedbackType.GOOD_FORM,
                severity=Severity.OK,
                message="动作标准",
            ))
        
        if state == PoseState.SQUATTING and any(fb.severity == Severity.ERROR for fb in feedbacks):
            self._error_frame_count += 1
        
        overall = self._get_overall_severity(feedbacks)
        depth_pct = self._calculate_depth_percentage(knee_angle)
        
        self._update_history(knee_angle, timestamp)
        
        self._last_analysis = FormAnalysis(
            feedbacks=feedbacks,
            overall_severity=overall,
            knee_valgus_score=knee_valgus_score,
            back_angle=back_angle,
            depth_percentage=depth_pct,
            velocity=velocity,
        )
        
        return self._last_analysis
    
    def _check_knee_valgus(self, landmarks) -> float:
        """
        检测膝盖内扣程度
        
        算法：膝盖横向距离与髋宽的比例
        - 正常：膝盖距离 >= 髋宽
        - 内扣：膝盖距离 < 髋宽
        
        Returns:
            float: 内扣程度 (0=正常, 1=严重内扣)
        """
        left_hip = landmarks[self.LEFT_HIP]
        right_hip = landmarks[self.RIGHT_HIP]
        left_knee = landmarks[self.LEFT_KNEE]
        right_knee = landmarks[self.RIGHT_KNEE]
        
        # 计算髋宽
        hip_width = abs(right_hip.x - left_hip.x)
        if hip_width < 0.01:  # 避免除零
            return 0.0
        
        # 计算膝盖距离
        knee_distance = abs(right_knee.x - left_knee.x)
        
        # 正常情况下，膝盖距离应该 >= 髋宽
        # 归一化：knee_distance / hip_width >= 1 为正常
        ratio = knee_distance / hip_width
        
        # 内扣程度：ratio < 1 时有内扣，越小越严重
        if ratio >= 1.0:
            return 0.0
        else:
            # 归一化到 0-1
            return min(1.0, (1.0 - ratio) * 2)
    
    def _calculate_back_angle(self, landmarks) -> float:
        """
        计算躯干倾斜角
        
        算法：肩膀中点到髋部中点的连线与垂直方向的夹角
        
        Returns:
            float: 倾斜角度 (0=直立, 90=水平)
        """
        left_shoulder = landmarks[self.LEFT_SHOULDER]
        right_shoulder = landmarks[self.RIGHT_SHOULDER]
        left_hip = landmarks[self.LEFT_HIP]
        right_hip = landmarks[self.RIGHT_HIP]
        
        # 计算中点
        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_mid_x = (left_hip.x + right_hip.x) / 2
        hip_mid_y = (left_hip.y + right_hip.y) / 2
        
        # 计算与垂直方向的夹角
        dx = shoulder_mid_x - hip_mid_x
        dy = shoulder_mid_y - hip_mid_y  # 注意：y轴向下
        
        if abs(dy) < 0.001:
            return 90.0  # 水平
        
        angle = abs(math.atan2(dx, -dy) * 180 / math.pi)
        return angle
    
    def _calculate_velocity(self, angle: float, timestamp: float) -> float:
        """
        计算角度变化速度
        
        Returns:
            float: 角度变化速度 (度/秒)
        """
        if len(self._angle_history) < 2:
            return 0.0
        
        prev_angle = self._angle_history[-1]
        prev_time = self._time_history[-1]
        
        dt = timestamp - prev_time
        if dt < 0.001:
            return 0.0
        
        velocity = abs(angle - prev_angle) / dt
        return velocity
    
    def _calculate_depth_percentage(self, knee_angle: float) -> float:
        """
        计算下蹲深度百分比
        
        标准深蹲：膝盖角度 90°
        站立：膝盖角度 170°
        
        Returns:
            float: 深度百分比 (0-100)
        """
        # 170° (站立) -> 0%
        # 90° (标准深蹲) -> 100%
        # 70° (更深) -> 100%+
        
        standing = 170.0
        target = self.DEPTH_GOOD_ANGLE
        
        if knee_angle >= standing:
            return 0.0
        if knee_angle <= target:
            return 100.0 + (target - knee_angle) * 2
        
        return (standing - knee_angle) / (standing - target) * 100
    
    def _check_depth(self, knee_angle: float) -> Optional[FormFeedback]:
        depth_error = self._config["depth_error_angle"]
        depth_warning = self._config["depth_warning_angle"]
        
        if knee_angle > depth_error:
            return FormFeedback(
                type=FeedbackType.DEPTH_INSUFFICIENT,
                severity=Severity.ERROR,
                message="蹲得太浅",
                value=knee_angle,
                target=self.DEPTH_GOOD_ANGLE,
            )
        elif knee_angle > depth_warning:
            return FormFeedback(
                type=FeedbackType.DEPTH_INSUFFICIENT,
                severity=Severity.WARNING,
                message="可以蹲得更深",
                value=knee_angle,
                target=self.DEPTH_GOOD_ANGLE,
            )
        elif knee_angle <= self.DEPTH_GOOD_ANGLE:
            return FormFeedback(
                type=FeedbackType.DEEP_ENOUGH,
                severity=Severity.OK,
                message="深度足够",
                value=knee_angle,
                target=self.DEPTH_GOOD_ANGLE,
            )
        return None
    
    def _check_valgus(self, score: float) -> Optional[FormFeedback]:
        valgus_error = self._config["knee_valgus_error"]
        valgus_warning = self._config["knee_valgus_warning"]
        
        if score > valgus_error:
            return FormFeedback(
                type=FeedbackType.KNEE_VALGUS,
                severity=Severity.ERROR,
                message="膝盖严重内扣！",
                value=score,
                joints_to_highlight=(self.LEFT_KNEE, self.RIGHT_KNEE),
            )
        elif score > valgus_warning:
            return FormFeedback(
                type=FeedbackType.KNEE_VALGUS,
                severity=Severity.WARNING,
                message="注意膝盖不要内扣",
                value=score,
                joints_to_highlight=(self.LEFT_KNEE, self.RIGHT_KNEE),
            )
        return None
    
    def _check_back(self, posture_angle: float) -> Optional[FormFeedback]:
        back_error = self._config["back_error_angle"]
        back_warning = self._config["back_warning_angle"]
        
        if posture_angle > back_error:
            return FormFeedback(
                type=FeedbackType.BACK_BENT,
                severity=Severity.ERROR,
                message="背部过度弯曲",
                value=posture_angle,
                joints_to_highlight=(self.LEFT_SHOULDER, self.RIGHT_SHOULDER, 
                                     self.LEFT_HIP, self.RIGHT_HIP),
            )
        elif posture_angle > back_warning:
            return FormFeedback(
                type=FeedbackType.BACK_BENT,
                severity=Severity.WARNING,
                message="保持背部挺直",
                value=posture_angle,
                joints_to_highlight=(self.LEFT_SHOULDER, self.RIGHT_SHOULDER),
            )
        return None
    
    def _check_speed(self, velocity: float) -> Optional[FormFeedback]:
        """检查动作速度"""
        if velocity > self.VELOCITY_ERROR:
            return FormFeedback(
                type=FeedbackType.TOO_FAST,
                severity=Severity.WARNING,
                message="动作太快，控制节奏",
                value=velocity,
            )
        elif velocity > self.VELOCITY_WARNING:
            return FormFeedback(
                type=FeedbackType.TOO_FAST,
                severity=Severity.INFO,
                message="稍微慢一点",
                value=velocity,
            )
        return None
    
    def _update_history(self, angle: float, timestamp: float):
        """更新历史数据"""
        self._angle_history.append(angle)
        self._time_history.append(timestamp)
    
    def _get_overall_severity(self, feedbacks: List[FormFeedback]) -> Severity:
        """获取总体严重程度"""
        if not feedbacks:
            return Severity.OK
        
        max_severity = max(fb.severity.value for fb in feedbacks)
        return Severity(max_severity)
    
    def _empty_analysis(self) -> FormAnalysis:
        """返回空分析结果"""
        return FormAnalysis(
            feedbacks=[],
            overall_severity=Severity.OK,
            knee_valgus_score=0.0,
            back_angle=0.0,
            depth_percentage=0.0,
            velocity=0.0,
        )
    
    @property
    def last_analysis(self) -> Optional[FormAnalysis]:
        """获取最近一次分析结果"""
        return self._last_analysis
    
    def reset(self):
        """重置分析器状态"""
        self._angle_history.clear()
        self._time_history.clear()
        self._frame_counters.clear()
        self._last_analysis = None
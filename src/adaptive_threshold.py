"""
自适应阈值校准模块

自动学习用户的角度范围，动态调整站立和下蹲阈值。
"""

import time
from dataclasses import dataclass
from typing import List, Optional, Tuple
from collections import deque

import numpy as np

from src.config import Config
from src.squat_counter import PoseState


@dataclass
class CalibrationResult:
    standing_threshold: float
    squat_threshold: float
    max_standing_angle: float
    min_squat_angle: float
    confidence: float
    samples_used: int


@dataclass
class AngleSample:
    angle: float
    timestamp: float


class AdaptiveThresholdManager:
    MIN_SAMPLES = 100
    BUFFER_SIZE = 500
    MIN_STANDING_THRESHOLD = 140.0
    MAX_STANDING_THRESHOLD = 175.0
    MIN_SQUAT_THRESHOLD = 70.0
    MAX_SQUAT_THRESHOLD = 110.0
    
    def __init__(self):
        self.angle_history: deque = deque(maxlen=self.BUFFER_SIZE)
        self.standing_angles: List[float] = []
        self.squat_angles: List[float] = []
        self._calibrated = False
        self._calibration_result: Optional[CalibrationResult] = None
    
    def add_sample(self, angle: float, state: PoseState) -> None:
        self.angle_history.append(AngleSample(angle, time.time()))
        
        if state == PoseState.STANDING:
            self.standing_angles.append(angle)
        elif state == PoseState.SQUATTING:
            self.squat_angles.append(angle)
    
    def calibrate(self) -> Optional[CalibrationResult]:
        if len(self.angle_history) < self.MIN_SAMPLES:
            return None
        
        angles = [s.angle for s in self.angle_history]
        
        all_max = max(angles)
        all_min = min(angles)
        angle_range = all_max - all_min
        
        if angle_range < 30:
            return None
        
        typical_standing = np.percentile(angles, 85)
        typical_squat = np.percentile(angles, 15)
        
        if self.standing_angles and self.squat_angles:
            max_standing = max(self.standing_angles)
            min_squat = min(self.squat_angles)
            standing_thresh = max_standing - (max_standing - min_squat) * 0.10
            squat_thresh = min_squat + (max_standing - min_squat) * 0.10
        else:
            standing_thresh = typical_standing - 5
            squat_thresh = typical_squat + 5
        
        standing_thresh = max(self.MIN_STANDING_THRESHOLD, 
                            min(self.MAX_STANDING_THRESHOLD, standing_thresh))
        squat_thresh = max(self.MIN_SQUAT_THRESHOLD, 
                          min(self.MAX_SQUAT_THRESHOLD, squat_thresh))
        
        confidence = min(1.0, len(angles) / 300) * min(1.0, angle_range / 100)
        
        self._calibrated = True
        self._calibration_result = CalibrationResult(
            standing_threshold=standing_thresh,
            squat_threshold=squat_thresh,
            max_standing_angle=all_max,
            min_squat_angle=all_min,
            confidence=confidence,
            samples_used=len(angles),
        )
        
        return self._calibration_result
    
    def get_thresholds(self) -> Tuple[float, float]:
        if self._calibrated and self._calibration_result:
            return (
                self._calibration_result.standing_threshold,
                self._calibration_result.squat_threshold
            )
        return Config.STANDING_ANGLE_THRESHOLD, Config.SQUAT_ANGLE_THRESHOLD
    
    def reset(self) -> None:
        self.angle_history.clear()
        self.standing_angles.clear()
        self.squat_angles.clear()
        self._calibrated = False
        self._calibration_result = None
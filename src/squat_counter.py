"""
深蹲计数模块

实现基于膝角角度的深蹲动作计数逻辑。
"""

import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Tuple, Protocol

from src.config import Config
from src.database import Database


class Landmark(Protocol):
    """关键点协议，定义 x 和 y 属性"""
    x: float
    y: float


class PoseState(Enum):
    """姿态状态枚举"""
    STANDING = "STANDING"      # 站立状态
    SQUATTING = "SQUATTING"    # 下蹲状态


@dataclass
class SquatMetrics:
    """深蹲指标数据类"""
    rep_count: int
    state: PoseState
    left_knee_angle: float
    right_knee_angle: float
    avg_knee_angle: float


class SquatCounter:
    """
    深蹲计数器类
    
    通过检测膝关节角度变化来计数深蹲动作。
    使用状态机模式：STANDING <-> SQUATTING
    
    Attributes:
        standing_threshold: 站立状态角度阈值
        squat_threshold: 下蹲状态角度阈值
    """
    
    def __init__(
        self,
        database: Optional[Database] = None,
        session_id: Optional[int] = None,
        standing_threshold: float = Config.STANDING_ANGLE_THRESHOLD,
        squat_threshold: float = Config.SQUAT_ANGLE_THRESHOLD,
        buffer_size: int = Config.RECORD_BUFFER_SIZE,
    ):
        """
        初始化深蹲计数器。
        
        Args:
            database: 数据库实例，用于持久化记录
            session_id: 训练会话ID
            standing_threshold: 站立状态膝角阈值
            squat_threshold: 下蹲状态膝角阈值
            buffer_size: 记录缓冲区大小
        """
        self.standing_threshold = standing_threshold
        self.squat_threshold = squat_threshold
        self.buffer_size = buffer_size
        
        # 计数状态
        self._count = 0
        self._state = PoseState.STANDING
        self._left_knee_angle = 0.0
        self._right_knee_angle = 0.0
        self._avg_knee_angle = 0.0
        
        # 数据库相关
        self._database = database
        self._session_id = session_id
        self._record_buffer: List[tuple] = []
    
    @staticmethod
    def calculate_angle(a: Landmark, b: Landmark, c: Landmark) -> float:
        """
        计算三点形成的角度。
        
        使用向量叉积计算角度，b为顶点。
        
        Args:
            a: 第一个点，需有x和y属性
            b: 顶点，需有x和y属性
            c: 第三个点，需有x和y属性
            
        Returns:
            float: 角度值（0-180度）
        """
        radians = math.atan2(c.y - b.y, c.x - b.x) - math.atan2(
            a.y - b.y, a.x - b.x
        )
        angle = abs(radians * 180.0 / math.pi)
        if angle > 180.0:
            angle = 360.0 - angle
        return angle
    
    def update(self, pose_landmarks: List) -> SquatMetrics:
        """
        根据姿态关键点更新计数状态。
        
        Args:
            pose_landmarks: MediaPipe检测到的姿态关键点列表
                           pose_landmarks[0] 是单人的关键点列表
                           
        Returns:
            SquatMetrics: 当前深蹲指标
        """
        if not pose_landmarks:
            return self._get_metrics()
        
        landmarks = pose_landmarks[0]
        
        # 验证关键点数量
        if len(landmarks) < 29:
            return self._get_metrics()
        
        # 获取关键点
        cfg = Config
        left_hip = landmarks[cfg.LEFT_HIP]
        left_knee = landmarks[cfg.LEFT_KNEE]
        left_ankle = landmarks[cfg.LEFT_ANKLE]
        right_hip = landmarks[cfg.RIGHT_HIP]
        right_knee = landmarks[cfg.RIGHT_KNEE]
        right_ankle = landmarks[cfg.RIGHT_ANKLE]
        
        # 计算膝角
        self._left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        self._right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)
        self._avg_knee_angle = (self._left_knee_angle + self._right_knee_angle) / 2
        
        # 状态机更新
        self._update_state()
        
        # 记录数据
        self._record_frame()
        
        return self._get_metrics()
    
    def _update_state(self) -> None:
        """更新状态机"""
        if self._state == PoseState.STANDING:
            if self._avg_knee_angle < self.squat_threshold:
                self._state = PoseState.SQUATTING
                
        elif self._state == PoseState.SQUATTING:
            if self._avg_knee_angle > self.standing_threshold:
                self._count += 1
                self._state = PoseState.STANDING
    
    def _record_frame(self) -> None:
        """记录当前帧数据到缓冲区"""
        if self._database is None or self._session_id is None:
            return
        
        self._record_buffer.append((
            self._session_id,
            datetime.now().isoformat(),
            self._left_knee_angle,
            self._right_knee_angle,
            self._avg_knee_angle,
            self._state.value,
            self._count,
        ))
        
        # 缓冲区满时批量写入
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
        return SquatMetrics(
            rep_count=self._count,
            state=self._state,
            left_knee_angle=self._left_knee_angle,
            right_knee_angle=self._right_knee_angle,
            avg_knee_angle=self._avg_knee_angle,
        )
    
    @property
    def count(self) -> int:
        """当前深蹲计数"""
        return self._count
    
    @property
    def state(self) -> PoseState:
        """当前姿态状态"""
        return self._state
    
    def reset(self) -> None:
        """重置计数器状态"""
        self._count = 0
        self._state = PoseState.STANDING
        self._record_buffer.clear()
    
    def close(self) -> None:
        """关闭计数器，刷新缓冲区"""
        self._flush_buffer()
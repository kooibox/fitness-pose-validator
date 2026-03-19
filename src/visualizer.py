"""
可视化模块

提供姿态检测结果的图形化渲染功能。
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np

from src.config import Config
from src.squat_counter import PoseState, SquatMetrics


class Visualizer:
    """
    可视化渲染器类
    
    负责在视频帧上渲染姿态关键点、骨骼连线和统计信息。
    
    Attributes:
        frame_width: 帧宽度
        frame_height: 帧高度
    """
    
    # 颜色定义 (BGR格式)
    COLOR_GREEN = (0, 255, 0)
    COLOR_BLUE = (255, 0, 0)
    COLOR_RED = (0, 0, 255)
    COLOR_YELLOW = (0, 255, 255)
    COLOR_CYAN = (255, 255, 0)
    COLOR_GRAY = (200, 200, 200)
    COLOR_WHITE = (255, 255, 255)
    
    def __init__(self, frame_width: int, frame_height: int):
        """
        初始化可视化渲染器。
        
        Args:
            frame_width: 视频帧宽度
            frame_height: 视频帧高度
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
    
    def render_frame(
        self,
        frame: np.ndarray,
        pose_landmarks: Optional[List],
        metrics: Optional[SquatMetrics],
        frame_count: int,
        pose_count: int,
    ) -> np.ndarray:
        """
        渲染单帧图像。
        
        Args:
            frame: 原始视频帧
            pose_landmarks: MediaPipe 姿态检测结果 (List[List[Landmark]])
            metrics: 深蹲指标
            frame_count: 总帧数
            pose_count: 检测到姿态的帧数
            
        Returns:
            np.ndarray: 渲染后的视频帧
        """
        # 提取第一个人的关键点
        landmarks = pose_landmarks[0] if pose_landmarks else None
        
        if landmarks is None:
            self._draw_no_pose_warning(frame)
        else:
            self._draw_landmarks(frame, landmarks)
            self._draw_skeleton(frame, landmarks)
            
            if metrics:
                self._draw_metrics(frame, metrics)
                self._draw_knee_angles(frame, landmarks, metrics)
        
        self._draw_stats(frame, frame_count, pose_count, metrics)
        
        return frame
    
    def _draw_no_pose_warning(self, frame: np.ndarray) -> None:
        """绘制未检测到姿态的警告"""
        cv2.putText(
            frame,
            "No pose detected",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            self.COLOR_RED,
            2,
        )
    
    def _draw_landmarks(self, frame: np.ndarray, landmarks: List) -> None:
        """
        绘制姿态关键点。
        
        Args:
            frame: 视频帧
            landmarks: 关键点列表
        """
        h, w = frame.shape[:2]
        for landmark in landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 4, self.COLOR_GREEN, -1)
    
    def _draw_skeleton(self, frame: np.ndarray, landmarks: List) -> None:
        """
        绘制骨骼连线。
        
        Args:
            frame: 视频帧
            landmarks: 关键点列表
        """
        h, w = frame.shape[:2]
        
        for connection in Config.SQUAT_CONNECTIONS:
            idx1, idx2 = connection
            
            if idx1 < len(landmarks) and idx2 < len(landmarks):
                pt1 = landmarks[idx1]
                pt2 = landmarks[idx2]
                x1, y1 = int(pt1.x * w), int(pt1.y * h)
                x2, y2 = int(pt2.x * w), int(pt2.y * h)
                cv2.line(frame, (x1, y1), (x2, y2), self.COLOR_BLUE, 2)
    
    def _draw_metrics(self, frame: np.ndarray, metrics: SquatMetrics) -> None:
        """
        绘制深蹲指标。
        
        Args:
            frame: 视频帧
            metrics: 深蹲指标
        """
        # 深蹲计数
        cv2.putText(
            frame,
            f"REPS: {metrics.rep_count}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            self.COLOR_GREEN,
            2,
        )
        
        # 当前状态
        state_color = self.COLOR_GREEN if metrics.state == PoseState.STANDING else self.COLOR_RED
        cv2.putText(
            frame,
            f"State: {metrics.state.value}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            state_color,
            1,
        )
        
        # 平均角度和阈值提示
        cv2.putText(
            frame,
            f"Avg: {metrics.avg_knee_angle:.0f}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.COLOR_CYAN,
            1,
        )
    
    def _draw_knee_angles(
        self,
        frame: np.ndarray,
        landmarks: List,
        metrics: SquatMetrics,
    ) -> None:
        """
        在膝盖位置绘制角度值。
        
        Args:
            frame: 视频帧
            landmarks: 关键点列表
            metrics: 深蹲指标
        """
        h, w = frame.shape[:2]
        
        # 左膝角度
        left_knee = landmarks[Config.LEFT_KNEE]
        cv2.putText(
            frame,
            f"{int(metrics.left_knee_angle)}",
            (int(left_knee.x * w) - 15, int(left_knee.y * h) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.COLOR_YELLOW,
            1,
        )
        
        # 右膝角度
        right_knee = landmarks[Config.RIGHT_KNEE]
        cv2.putText(
            frame,
            f"{int(metrics.right_knee_angle)}",
            (int(right_knee.x * w) - 15, int(right_knee.y * h) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.COLOR_YELLOW,
            1,
        )
    
    def _draw_stats(
        self,
        frame: np.ndarray,
        frame_count: int,
        pose_count: int,
        metrics: Optional[SquatMetrics],
    ) -> None:
        """
        绘制统计信息。
        
        Args:
            frame: 视频帧
            frame_count: 总帧数
            pose_count: 姿态帧数
            metrics: 深蹲指标
        """
        squat_count = metrics.rep_count if metrics else 0
        cv2.putText(
            frame,
            f"Frames: {frame_count} | Poses: {pose_count} | Squats: {squat_count}",
            (20, self.frame_height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.COLOR_GRAY,
            1,
        )
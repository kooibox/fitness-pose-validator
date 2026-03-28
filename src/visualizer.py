"""
可视化模块

提供姿态检测结果的图形化渲染功能，支持深色霓虹主题。
"""

from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from src.config import Config
from src.squat_counter import PoseState, SquatMetrics


class Visualizer:
    """
    可视化渲染器类

    负责在视频帧上渲染姿态关键点、骨骼连线和统计信息。
    支持深色霓虹主题。
    """

    # 霓虹颜色定义 (BGR for OpenCV)
    NEON_GREEN = (34, 197, 94)
    NEON_BLUE = (59, 130, 246)
    NEON_ORANGE = (249, 115, 22)
    NEON_RED = (239, 68, 68)
    NEON_PURPLE = (139, 92, 246)
    NEON_PINK = (236, 72, 153)
    NEON_CYAN = (34, 211, 238)

    # 传统颜色
    COLOR_GREEN = (0, 255, 0)
    COLOR_BLUE = (255, 0, 0)
    COLOR_RED = (0, 0, 255)
    COLOR_YELLOW = (0, 255, 255)
    COLOR_CYAN = (255, 255, 0)
    COLOR_GRAY = (200, 200, 200)
    COLOR_WHITE = (255, 255, 255)

    def __init__(self, frame_width: int, frame_height: int, dark_mode: bool = True):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.dark_mode = dark_mode

        # 深色模式下的霓虹颜色
        self.joint_color = self.NEON_GREEN
        self.bone_color = self.NEON_GREEN
        self.text_color = (255, 255, 255)

    def set_exercise_mode(self, mode: str):
        """设置运动模式颜色"""
        if mode == "jumping_jack":
            self.joint_color = self.NEON_BLUE
            self.bone_color = self.NEON_BLUE
        else:
            self.joint_color = self.NEON_GREEN
            self.bone_color = self.NEON_GREEN

    def _add_glow(self, frame: np.ndarray, x: int, y: int, radius: int, color: Tuple[int, int, int], glow_radius: int = 15) -> np.ndarray:
        """添加发光效果的辅助函数"""
        overlay = frame.copy()
        # 外发光
        cv2.circle(overlay, (x, y), glow_radius, color, -1)
        # 内核
        cv2.circle(overlay, (x, y), radius, color, -1)
        # 混合
        return cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

    def _draw_glow_line(self, frame: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int], color: Tuple[int, int, int], thickness: int = 3, glow: bool = True) -> np.ndarray:
        """绘制带发光效果的线条"""
        if glow and self.dark_mode:
            # 先画发光层
            overlay = frame.copy()
            cv2.line(overlay, pt1, pt2, color, thickness + 4)
            frame = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
            # 再画主线
            cv2.line(frame, pt1, pt2, color, thickness)
        else:
            cv2.line(frame, pt1, pt2, color, thickness)
        return frame

    def _draw_glow_circle(self, frame: np.ndarray, center: Tuple[int, int], radius: int, color: Tuple[int, int, int], fill: bool = True, glow: bool = True) -> np.ndarray:
        """绘制带发光效果的圆点"""
        if glow and self.dark_mode:
            overlay = frame.copy()
            # 外发光
            cv2.circle(overlay, center, radius + 6, color, -1)
            # 内核
            cv2.circle(overlay, center, radius, color, -1)
            # 混合
            frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
        else:
            cv2.circle(frame, center, radius, color, -1 if fill else 2)
        return frame

    def render_frame(
        self,
        frame: np.ndarray,
        pose_data: Optional[Dict],
        metrics: Optional[SquatMetrics],
        frame_count: int,
        pose_count: int,
    ) -> np.ndarray:
        """
        渲染单帧图像。
        
        Args:
            frame: 原始视频帧
            pose_data: 检测结果字典 {'normalized': ..., 'world': ...}
            metrics: 深蹲指标
            frame_count: 总帧数
            pose_count: 检测到姿态的帧数
            
        Returns:
            np.ndarray: 渲染后的视频帧
        """
        landmarks = None
        if pose_data and pose_data.get('normalized'):
            landmarks = pose_data['normalized'][0]
        
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
        """绘制未检测到姿态的警告（霓虹风格）"""
        cv2.putText(
            frame,
            "No pose detected",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            self.NEON_RED,
            2,
        )
    
    def _draw_landmarks(self, frame: np.ndarray, landmarks: List) -> None:
        """
        绘制姿态关键点（带霓虹发光效果）。

        Args:
            frame: 视频帧
            landmarks: 关键点列表
        """
        h, w = frame.shape[:2]
        for landmark in landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            # 使用发光效果绘制关节
            frame = self._draw_glow_circle(frame, (x, y), 4, self.joint_color, fill=True)

    def _draw_skeleton(self, frame: np.ndarray, landmarks: List) -> None:
        """
        绘制骨骼连线（带霓虹发光效果）。

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
                # 使用发光线条
                frame = self._draw_glow_line(frame, (x1, y1), (x2, y2), self.bone_color, thickness=3)
    
    def _draw_metrics(self, frame: np.ndarray, metrics: SquatMetrics) -> None:
        """
        绘制深蹲指标（深色霓虹风格）。

        Args:
            frame: 视频帧
            metrics: 深蹲指标
        """
        # 深蹲计数 - 使用霓虹绿
        cv2.putText(
            frame,
            f"REPS: {metrics.rep_count}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            self.NEON_GREEN,
            2,
        )

        # 当前状态 - 霓虹绿/橙
        state_color = self.NEON_GREEN if metrics.state == PoseState.STANDING else self.NEON_ORANGE
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
        在膝盖位置绘制角度值（霓虹风格）。

        Args:
            frame: 视频帧
            landmarks: 关键点列表
            metrics: 深蹲指标
        """
        h, w = frame.shape[:2]

        # 左膝角度 - 使用霓虹青色
        left_knee = landmarks[Config.LEFT_KNEE]
        cv2.putText(
            frame,
            f"{int(metrics.left_knee_angle)}",
            (int(left_knee.x * w) - 15, int(left_knee.y * h) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.NEON_CYAN,
            2,
        )

        # 右膝角度
        right_knee = landmarks[Config.RIGHT_KNEE]
        cv2.putText(
            frame,
            f"{int(metrics.right_knee_angle)}",
            (int(right_knee.x * w) - 15, int(right_knee.y * h) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.NEON_CYAN,
            2,
        )
    
    def _draw_stats(
        self,
        frame: np.ndarray,
        frame_count: int,
        pose_count: int,
        metrics: Optional[SquatMetrics],
    ) -> None:
        """
        绘制统计信息（深色霓虹风格）。

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
            (160, 160, 160),  # 浅灰色，适合深色背景
            1,
        )
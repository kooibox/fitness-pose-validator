"""
姿态检测模块

封装 MediaPipe Pose Landmarker，提供实时姿态检测功能。
"""

import os
from pathlib import Path
from typing import List, Optional

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from src.config import Config


class PoseDetector:
    """
    姿态检测器类
    
    封装 MediaPipe Pose Landmarker，提供视频帧级别的姿态检测。
    
    Attributes:
        landmarker: MediaPipe PoseLandmarker 实例
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        初始化姿态检测器。
        
        Args:
            model_path: 模型文件路径，默认使用配置中的路径
            
        Raises:
            FileNotFoundError: 模型文件不存在
        """
        # 设置环境变量以优化性能
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["OMP_NUM_THREADS"] = "1"
        
        self._model_path = model_path or Config.MODEL_PATH
        self._validate_model()
        self._landmarker = self._create_landmarker()
    
    def _validate_model(self) -> None:
        """验证模型文件是否存在"""
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"模型文件不存在: {self._model_path}\n"
                f"请确保模型文件已放置在正确位置。"
            )
    
    def _create_landmarker(self) -> vision.PoseLandmarker:
        """创建 PoseLandmarker 实例"""
        base_options = python.BaseOptions(model_asset_path=str(self._model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=Config.MAX_NUM_POSES,
            min_pose_detection_confidence=Config.POSE_DETECTION_CONFIDENCE,
            min_pose_presence_confidence=Config.POSE_PRESENCE_CONFIDENCE,
            min_tracking_confidence=Config.POSE_TRACKING_CONFIDENCE,
        )
        return vision.PoseLandmarker.create_from_options(options)
    
    def detect(self, frame, timestamp_ms: int) -> Optional[List]:
        """
        检测单帧图像中的姿态。
        
        Args:
            frame: BGR格式的图像帧（OpenCV格式）
            timestamp_ms: 帧时间戳（毫秒）
            
        Returns:
            Optional[List]: 检测到的姿态关键点列表，无检测结果返回None
                           每个元素是一个人的关键点列表
        """
        # 创建 MediaPipe 图像对象
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame,
        )
        
        # 执行检测
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        
        if result.pose_landmarks:
            return result.pose_landmarks
        return None
    
    def close(self) -> None:
        """关闭检测器，释放资源"""
        self._landmarker.close()
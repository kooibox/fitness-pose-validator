"""
配置模块

定义应用程序的所有配置常量和参数。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass(frozen=True)
class Config:
    """应用程序配置类（不可变）"""
    
    # ========== 路径配置 ==========
    # 项目根目录
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    
    # 模型文件路径
    MODEL_PATH: Path = PROJECT_ROOT / "models" / "pose_landmarker.task"
    
    # 数据库文件路径
    DATABASE_PATH: Path = PROJECT_ROOT / "data" / "fitness_data.db"
    
    # ========== 深蹲计数配置 ==========
    # 站立状态膝角阈值（角度大于此值判定为站立）
    STANDING_ANGLE_THRESHOLD: float = 165.0
    
    # 下蹲状态膝角阈值（角度小于此值判定为下蹲）
    SQUAT_ANGLE_THRESHOLD: float = 90.0
    
    # ========== MediaPipe 配置 ==========
    # 姿态检测置信度阈值
    POSE_DETECTION_CONFIDENCE: float = 0.5
    
    # 姿态存在置信度阈值
    POSE_PRESENCE_CONFIDENCE: float = 0.5
    
    # 姿态跟踪置信度阈值
    POSE_TRACKING_CONFIDENCE: float = 0.5
    
    # 最大检测人数
    MAX_NUM_POSES: int = 1
    
    # ========== 摄像头配置 ==========
    # 摄像头索引
    CAMERA_INDEX: int = 0
    
    # 摄像头分辨率
    CAMERA_RESOLUTION: Tuple[int, int] = (1280, 720)
    
    # 摄像头帧率
    CAMERA_FPS: int = 30
    
    # 摄像头初始化等待时间（秒）
    CAMERA_INIT_WAIT: float = 2.0
    
    # ========== 窗口配置 ==========
    # 窗口标题
    WINDOW_TITLE: str = "Fitness Pose Validator"
    
    # 窗口初始大小
    WINDOW_SIZE: Tuple[int, int] = (900, 700)
    
    # ========== 数据库配置 ==========
    # 记录缓冲区大小（每N帧批量写入数据库）
    RECORD_BUFFER_SIZE: int = 100
    
    # ========== MediaPipe 关键点索引 ==========
    # 参考文档: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
    LEFT_HIP: int = 23
    LEFT_KNEE: int = 25
    LEFT_ANKLE: int = 27
    RIGHT_HIP: int = 24
    RIGHT_KNEE: int = 26
    RIGHT_ANKLE: int = 28
    
    # 深蹲相关骨骼连接（用于可视化）
    SQUAT_CONNECTIONS: Tuple[Tuple[int, int], ...] = (
        (LEFT_HIP, LEFT_KNEE),
        (LEFT_KNEE, LEFT_ANKLE),
        (RIGHT_HIP, RIGHT_KNEE),
        (RIGHT_KNEE, RIGHT_ANKLE),
        (LEFT_HIP, RIGHT_HIP),
    )


# 全局配置实例
config = Config()
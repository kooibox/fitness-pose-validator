"""
配置模块

定义应用程序的所有配置常量和参数。
"""

from pathlib import Path
from typing import Dict, Tuple


class Config:
    """应用程序配置类"""
    
    # ========== 路径配置 ==========
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    MODEL_PATH: Path = PROJECT_ROOT / "models" / "pose_landmarker.task"
    DATABASE_PATH: Path = PROJECT_ROOT / "data" / "fitness_data.db"
    
    # ========== 深蹲计数配置 ==========
    STANDING_ANGLE_THRESHOLD: float = 165.0
    SQUAT_ANGLE_THRESHOLD: float = 90.0
    
    # ========== MediaPipe 配置 ==========
    POSE_DETECTION_CONFIDENCE: float = 0.5
    POSE_PRESENCE_CONFIDENCE: float = 0.5
    POSE_TRACKING_CONFIDENCE: float = 0.5
    MAX_NUM_POSES: int = 1
    
    # ========== 摄像头配置 ==========
    CAMERA_INDEX: int = 0
    CAMERA_RESOLUTION: Tuple[int, int] = (1280, 720)
    CAMERA_FPS: int = 30
    CAMERA_INIT_WAIT: float = 2.0
    
    # ========== 窗口配置 ==========
    WINDOW_TITLE: str = "Fitness Pose Validator"
    WINDOW_SIZE: Tuple[int, int] = (900, 700)
    
    # ========== 数据库配置 ==========
    RECORD_BUFFER_SIZE: int = 100
    
    # ========== 服务器配置 ==========
    SERVER_HOST: str = "117.72.185.244"
    SERVER_PORT: int = 80
    SERVER_API_BASE: str = "/api/v1"
    
    @classmethod
    @property
    def SERVER_URL(cls) -> str:
        if cls.SERVER_PORT == 80:
            return f"http://{cls.SERVER_HOST}"
        return f"http://{cls.SERVER_HOST}:{cls.SERVER_PORT}"
    
    API_ENDPOINTS: Dict[str, str] = {
        "login": "/auth/login",
        "me": "/auth/me",
        "upload": "/sessions/upload",
        "sessions": "/sessions",
        "session_detail": "/sessions/{}",
        "overview": "/dashboard/overview",
        "trend": "/dashboard/trend",
        "distribution": "/dashboard/distribution",
        "heatmap": "/dashboard/heatmap",
        "radar": "/dashboard/radar",
        "best_records": "/dashboard/best-records",
        "recent_sessions": "/dashboard/recent-sessions",
        "llm_analyze": "/llm/analyze",
        "llm_status": "/llm/status/{}",
        "llm_types": "/llm/types",
    }
    
    # ========== 认证配置 ==========
    TOKEN_EXPIRE_HOURS: int = 24
    DEFAULT_USERNAME: str = "demo"
    DEFAULT_PASSWORD: str = "demo123"
    
    # ========== 运动类型 ==========
    EXERCISE_TYPES: Tuple[str, ...] = ("squat", "pushup", "lunge")
    DEFAULT_EXERCISE_TYPE: str = "squat"
    
    # ========== MediaPipe 关键点索引 ==========
    LEFT_SHOULDER: int = 11
    RIGHT_SHOULDER: int = 12
    LEFT_ELBOW: int = 13
    RIGHT_ELBOW: int = 14
    LEFT_WRIST: int = 15
    RIGHT_WRIST: int = 16
    
    LEFT_HIP: int = 23
    LEFT_KNEE: int = 25
    LEFT_ANKLE: int = 27
    RIGHT_HIP: int = 24
    RIGHT_KNEE: int = 26
    RIGHT_ANKLE: int = 28
    
    SQUAT_CONNECTIONS: Tuple[Tuple[int, int], ...] = (
        (23, 25),
        (25, 27),
        (24, 26),
        (26, 28),
        (23, 24),
    )
    
    FULL_BODY_CONNECTIONS: Tuple[Tuple[int, int], ...] = (
        (11, 12),
        (11, 13),
        (13, 15),
        (12, 14),
        (14, 16),
        (11, 23),
        (12, 24),
        (23, 24),
        (23, 25),
        (25, 27),
        (24, 26),
        (26, 28),
    )


config = Config()
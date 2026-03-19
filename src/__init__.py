"""
Fitness Pose Validator - 健身姿态验证器

基于 MediaPipe 的实时健身动作检测与计数系统。
"""

__version__ = "1.0.0"
__author__ = "Fitness Pose Validator Team"

from src.config import Config
from src.database import Database
from src.squat_counter import SquatCounter
from src.pose_detector import PoseDetector
from src.visualizer import Visualizer
from src.analyzer import TrainingAnalyzer

__all__ = [
    "Config",
    "Database", 
    "SquatCounter",
    "PoseDetector",
    "Visualizer",
    "TrainingAnalyzer",
]
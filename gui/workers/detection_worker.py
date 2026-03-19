"""
检测工作线程

在后台线程中处理视频捕获和姿态检测，避免阻塞 UI。
"""

import time
from typing import List, Optional

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from src.config import Config
from src.database import Database
from src.pose_detector import PoseDetector
from src.squat_counter import SquatCounter, SquatMetrics


class DetectionWorker(QThread):
    """
    检测工作线程
    
    在后台执行视频捕获、姿态检测和深蹲计数。
    通过 Qt 信号与主线程通信。
    """
    
    # 信号定义
    frame_ready = pyqtSignal(np.ndarray)           # 新帧可用
    metrics_updated = pyqtSignal(object)            # 指标更新 (SquatMetrics)
    session_created = pyqtSignal(int)               # 会话已创建
    error_occurred = pyqtSignal(str)                # 错误发生
    camera_info = pyqtSignal(str, int, int, int)    # 摄像头信息 (状态, 宽, 高, FPS)
    
    def __init__(self, parent=None):
        """初始化检测工作线程"""
        super().__init__(parent)
        
        # 组件
        self._pose_detector: Optional[PoseDetector] = None
        self._squat_counter: Optional[SquatCounter] = None
        self._database: Optional[Database] = None
        self._cap: Optional[cv2.VideoCapture] = None
        
        # 状态
        self._running = False
        self._paused = False
        self._session_id: Optional[int] = None
        
        # 统计
        self._frame_count = 0
        self._pose_count = 0
        self._start_time: Optional[float] = None
        
        # 配置
        self._rotate_frame = True  # 是否旋转帧（摄像头竖屏模式）
        self._camera_index = Config.CAMERA_INDEX
    
    @property
    def session_id(self) -> Optional[int]:
        """当前会话 ID"""
        return self._session_id
    
    @property
    def frame_count(self) -> int:
        """总帧数"""
        return self._frame_count
    
    @property
    def pose_count(self) -> int:
        """检测到姿态的帧数"""
        return self._pose_count
    
    @property
    def elapsed_time(self) -> float:
        """已运行时间（秒）"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
    
    def set_camera_index(self, index: int):
        """设置摄像头索引"""
        self._camera_index = index
    
    def set_rotate_frame(self, rotate: bool):
        """设置是否旋转帧"""
        self._rotate_frame = rotate
    
    def run(self):
        """主循环：捕获 -> 检测 -> 发射信号"""
        try:
            self._init_components()
            self._init_camera()
            self._running = True
            self._start_time = time.time()
            
            while self._running and self._cap and self._cap.isOpened():
                if self._paused:
                    self.msleep(100)
                    continue
                
                # 捕获帧
                ret, frame = self._cap.read()
                if not ret:
                    self.error_occurred.emit("无法读取视频帧")
                    break
                
                # 旋转帧（摄像头竖屏模式）
                if self._rotate_frame:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                
                # 转换颜色空间
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 姿态检测
                timestamp_ms = int((self._frame_count + 1) * 1000 / Config.CAMERA_FPS)
                landmarks = self._pose_detector.detect(rgb_frame, timestamp_ms)
                
                self._frame_count += 1
                
                # 更新计数器
                metrics = None
                if landmarks:
                    self._pose_count += 1
                    metrics = self._squat_counter.update(landmarks)
                    
                    # 渲染骨骼
                    frame = self._render_landmarks(frame, landmarks, metrics)
                
                # 发射信号
                self.frame_ready.emit(frame)
                if metrics:
                    self.metrics_updated.emit(metrics)
                
                # 控制帧率
                self.msleep(1)
        
        except Exception as e:
            self.error_occurred.emit(str(e))
        
        finally:
            self._cleanup()
    
    def _init_components(self):
        """初始化检测组件"""
        # 初始化数据库
        self._database = Database()
        
        # 初始化姿态检测器
        try:
            self._pose_detector = PoseDetector()
        except FileNotFoundError as e:
            self.error_occurred.emit(f"模型文件错误: {e}")
            raise
        
        # 创建会话
        self._session_id = self._database.create_session()
        self.session_created.emit(self._session_id)
        
        # 初始化计数器
        self._squat_counter = SquatCounter(
            database=self._database,
            session_id=self._session_id,
        )
    
    def _init_camera(self):
        """初始化摄像头"""
        # 尝试打开摄像头
        self._cap = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self._camera_index)
        
        if not self._cap.isOpened():
            self.error_occurred.emit("无法打开摄像头，请检查摄像头连接")
            raise RuntimeError("无法打开摄像头")
        
        # 配置摄像头参数
        width, height = Config.CAMERA_RESOLUTION
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
        
        # 等待摄像头初始化
        time.sleep(Config.CAMERA_INIT_WAIT)
        
        # 预读取几帧以稳定摄像头
        for _ in range(5):
            self._cap.read()
            time.sleep(0.1)
        
        # 获取实际参数
        frame_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self._cap.get(cv2.CAP_PROP_FPS)) or Config.CAMERA_FPS
        
        self.camera_info.emit("已连接", frame_width, frame_height, fps)
    
    def _render_landmarks(
        self, 
        frame: np.ndarray, 
        landmarks: List,
        metrics: SquatMetrics
    ) -> np.ndarray:
        """
        渲染姿态关键点和骨骼
        
        Args:
            frame: 视频帧
            landmarks: 关键点列表
            metrics: 深蹲指标
            
        Returns:
            渲染后的视频帧
        """
        if not landmarks:
            return frame
        
        h, w = frame.shape[:2]
        person_landmarks = landmarks[0]
        
        # 绘制关键点
        for landmark in person_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
        
        # 绘制骨骼连线
        for connection in Config.SQUAT_CONNECTIONS:
            idx1, idx2 = connection
            if idx1 < len(person_landmarks) and idx2 < len(person_landmarks):
                pt1 = person_landmarks[idx1]
                pt2 = person_landmarks[idx2]
                x1, y1 = int(pt1.x * w), int(pt1.y * h)
                x2, y2 = int(pt2.x * w), int(pt2.y * h)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        # 绘制计数
        cv2.putText(
            frame,
            f"REPS: {metrics.rep_count}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
        )
        
        # 绘制状态
        state_color = (0, 255, 0) if metrics.state.value == "STANDING" else (0, 165, 255)
        cv2.putText(
            frame,
            f"State: {metrics.state.value}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            state_color,
            1,
        )
        
        return frame
    
    def pause(self):
        """暂停检测"""
        self._paused = True
    
    def resume(self):
        """恢复检测"""
        self._paused = False
    
    def stop(self):
        """停止检测"""
        self._running = False
    
    def reset_count(self):
        """重置计数"""
        if self._squat_counter:
            self._squat_counter.reset()
            self._frame_count = 0
            self._pose_count = 0
    
    def _cleanup(self):
        """清理资源"""
        # 释放摄像头
        if self._cap:
            self._cap.release()
            self._cap = None
        
        # 保存数据
        if self._squat_counter:
            self._squat_counter.close()
        
        if self._database and self._session_id:
            self._database.update_session(
                self._session_id,
                self._frame_count,
                self._squat_counter.count if self._squat_counter else 0
            )
        
        # 关闭姿态检测器
        if self._pose_detector:
            self._pose_detector.close()
            self._pose_detector = None
        
        # 打印统计信息
        print(f"\n检测线程已停止")
        print(f"总帧数: {self._frame_count}, 检测到姿态: {self._pose_count}")
        if self._squat_counter:
            print(f"深蹲计数: {self._squat_counter.count}")

"""
检测工作线程

在后台线程中处理视频捕获和姿态检测，避免阻塞 UI。
"""

import time
from typing import List, Optional

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image, ImageDraw, ImageFont

from src.config import Config
from src.database import Database
from src.pose_detector import PoseDetector
from src.squat_counter import SquatCounter, SquatMetrics
from src.form_analyzer import FormAnalyzer, FormAnalysis, Severity, StrictnessLevel


def put_chinese_text(
    img: np.ndarray, 
    text: str, 
    pos: tuple, 
    font_size: int = 20,
    color: tuple = (255, 255, 255),
    font_path: str = None
) -> np.ndarray:
    """
    在OpenCV图像上绘制中文文字
    
    Args:
        img: OpenCV图像
        text: 要绘制的文字
        pos: 文字位置
        font_size: 字体大小
        color: 文字颜色 (BGR格式)
        font_path: 字体文件路径
    
    Returns:
        绘制后的图像
    """
    # 转换为PIL图像
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # 尝试加载字体
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            font = ImageFont.load_default()
    else:
        # 尝试常见的中文字体
        font_names = [
            "C:/Windows/Fonts/msyh.ttc",      # Windows 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # Windows 黑体
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux Noto
        ]
        font = None
        for fn in font_names:
            try:
                font = ImageFont.truetype(fn, font_size)
                break
            except Exception as e:
                continue
        if font is None:
            font = ImageFont.load_default()
    
    # RGB颜色
    color_rgb = (color[2], color[1], color[0])
    
    # 绘制文字
    draw.text(pos, text, font=font, fill=color_rgb)
    
    # 转回OpenCV格式
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


class DetectionWorker(QThread):
    """
    检测工作线程
    
    在后台执行视频捕获、姿态检测和深蹲计数。
    通过 Qt 信号与主线程通信。
    """
    
    # 信号定义
    frame_ready = pyqtSignal(np.ndarray)           # 新帧可用
    metrics_updated = pyqtSignal(object)            # 指标更新 (SquatMetrics)
    valid_count_updated = pyqtSignal(int, int)      # 有效计数更新 (valid_count, total_count)
    feedback_updated = pyqtSignal(str, str)         # 反馈更新 (message, severity)
    session_created = pyqtSignal(int)               # 会话已创建
    error_occurred = pyqtSignal(str)                # 错误发生
    camera_info = pyqtSignal(str, int, int, int)    # 摄像头信息 (状态, 宽, 高, FPS)
    
    def __init__(self, parent=None):
        """初始化检测工作线程"""
        super().__init__(parent)
        
        # 组件
        self._pose_detector: Optional[PoseDetector] = None
        self._squat_counter: Optional[SquatCounter] = None
        self._form_analyzer: Optional[FormAnalyzer] = None
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
        
        # 有效计数（动作标准的深蹲次数）
        self._valid_rep_count: int = 0
        self._last_rep_count: int = 0
        
        # 反馈显示控制
        self._current_feedback_text: str = ""
        self._current_feedback_color: tuple = (0, 255, 0)
        self._feedback_show_start: float = 0
        self._feedback_min_duration: float = 2.5  # 每条反馈至少显示2.5秒
        
        # 配置
        self._rotate_frame = True
        self._camera_index = Config.CAMERA_INDEX
    
    @property
    def session_id(self) -> Optional[int]:
        return self._session_id
    
    @property
    def frame_count(self) -> int:
        return self._frame_count
    
    @property
    def pose_count(self) -> int:
        return self._pose_count
    
    @property
    def elapsed_time(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
    
    def set_camera_index(self, index: int):
        self._camera_index = index
    
    def set_rotate_frame(self, rotate: bool):
        self._rotate_frame = rotate
    
    def run(self):
        """主循环：捕获 -> 检测 -> 发射信号"""
        try:
            self._init_components()
            self._init_camera()
            self._running = True
            self._start_time = time.time()
            
            while self._running and self._cap and self._cap.isOpened():
                # 捕获帧
                ret, frame = self._cap.read()
                if not ret:
                    self.error_occurred.emit("无法读取视频帧")
                    break
                
                # 旋转帧
                if self._rotate_frame:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                
                # 暂停时只发送帧，不进行检测
                if self._paused:
                    self.frame_ready.emit(frame)
                    self.msleep(50)
                    continue
                
                # 转换颜色空间
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 姿态检测
                timestamp_ms = int((self._frame_count + 1) * 1000 / Config.CAMERA_FPS)
                landmarks = self._pose_detector.detect(rgb_frame, timestamp_ms)
                
                self._frame_count += 1
                
                # 更新计数器
                metrics = None
                form_analysis = None
                if landmarks:
                    self._pose_count += 1
                    metrics = self._squat_counter.update(landmarks)
                    
                    # 动作姿态分析
                    current_time = time.time()
                    form_analysis = self._form_analyzer.analyze(
                        landmarks,
                        metrics.avg_knee_angle,
                        metrics.state,
                        current_time
                    )
                    
                    # 更新有效计数
                    self._update_valid_count(metrics, form_analysis)
                    
                    # 发射反馈信号
                    self._emit_feedback(form_analysis)
                    
                    # 渲染骨骼
                    frame = self._render_landmarks(frame, landmarks, metrics, form_analysis)
                
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
        self._database = Database()
        
        try:
            self._pose_detector = PoseDetector()
        except FileNotFoundError as e:
            self.error_occurred.emit(f"模型文件错误: {e}")
            raise
        
        self._session_id = self._database.create_session()
        self.session_created.emit(self._session_id)
        
        self._squat_counter = SquatCounter(
            database=self._database,
            session_id=self._session_id,
        )
        
        self._form_analyzer = FormAnalyzer()
    
    def _init_camera(self):
        """初始化摄像头"""
        self._cap = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self._camera_index)
        
        if not self._cap.isOpened():
            self.error_occurred.emit("无法打开摄像头，请检查摄像头连接")
            raise RuntimeError("无法打开摄像头")
        
        width, height = Config.CAMERA_RESOLUTION
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
        
        time.sleep(Config.CAMERA_INIT_WAIT)
        
        for _ in range(5):
            self._cap.read()
            time.sleep(0.1)
        
        frame_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self._cap.get(cv2.CAP_PROP_FPS)) or Config.CAMERA_FPS
        
        self.camera_info.emit("已连接", frame_width, frame_height, fps)
    
    def _update_valid_count(self, metrics: SquatMetrics, form_analysis: Optional[FormAnalysis]):
        from src.squat_counter import PoseState
        
        if metrics.rep_count > self._last_rep_count:
            if self._form_analyzer.is_rep_valid():
                self._valid_rep_count += 1
            self._form_analyzer.start_new_rep()
            self._last_rep_count = metrics.rep_count
            self.valid_count_updated.emit(self._valid_rep_count, metrics.rep_count)
    
    def _emit_feedback(self, form_analysis: Optional[FormAnalysis]):
        current_time = time.time()
        
        if not form_analysis or not form_analysis.feedbacks:
            if current_time - self._feedback_show_start >= self._feedback_min_duration:
                self.feedback_updated.emit("动作标准", "ok")
                self._current_feedback_text = ""
            return
        
        feedback_to_show = max(form_analysis.feedbacks, key=lambda f: f.severity.value)
        new_text = feedback_to_show.message
        new_severity = feedback_to_show.severity.value
        
        severity_map = {
            Severity.ERROR.value: "error",
            Severity.WARNING.value: "warning",
            Severity.INFO.value: "info",
            Severity.OK.value: "ok",
        }
        
        should_update = False
        if not self._current_feedback_text:
            should_update = True
        elif self._get_severity_from_color(self._current_feedback_color) < new_severity:
            should_update = True
        elif current_time - self._feedback_show_start >= self._feedback_min_duration:
            if new_text != self._current_feedback_text:
                should_update = True
        
        if should_update:
            fb_color = (0, 255, 0)
            if feedback_to_show.severity == Severity.ERROR:
                fb_color = (0, 0, 255)
            elif feedback_to_show.severity == Severity.WARNING:
                fb_color = (0, 165, 255)
            elif feedback_to_show.severity == Severity.INFO:
                fb_color = (0, 255, 255)
            
            self._current_feedback_text = new_text
            self._current_feedback_color = fb_color
            self._feedback_show_start = current_time
            
            severity_str = severity_map.get(new_severity, "ok")
            self.feedback_updated.emit(new_text, severity_str)
    
    def set_strictness(self, level: StrictnessLevel):
        if self._form_analyzer:
            self._form_analyzer.set_strictness(level)
    
    def get_strictness(self) -> StrictnessLevel:
        if self._form_analyzer:
            return self._form_analyzer.get_strictness()
        return StrictnessLevel.NORMAL
    
    def _get_severity_from_color(self, color: tuple) -> int:
        """根据颜色获取严重程度数值"""
        if color == (0, 0, 255):      # 红色 - ERROR
            return 3
        elif color == (0, 165, 255):  # 橙色 - WARNING
            return 2
        elif color == (0, 255, 255):  # 黄色 - INFO
            return 1
        else:                          # 绿色 - OK
            return 0
    
    def _render_landmarks(
        self, 
        frame: np.ndarray, 
        landmarks: List,
        metrics: SquatMetrics,
        form_analysis: Optional[FormAnalysis] = None
    ) -> np.ndarray:
        """渲染姿态关键点和骨骼，包含实时动作反馈"""
        if not landmarks:
            return frame
        
        h, w = frame.shape[:2]
        person_landmarks = landmarks[0]
        
        # 根据分析结果确定骨骼颜色
        skeleton_color = (0, 255, 0)  # 默认绿色
        if form_analysis:
            severity = form_analysis.overall_severity
            if severity == Severity.ERROR:
                skeleton_color = (0, 0, 255)      # 红色 - 错误
            elif severity == Severity.WARNING:
                skeleton_color = (0, 165, 255)    # 橙色 - 警告
            elif severity == Severity.INFO:
                skeleton_color = (0, 255, 255)    # 黄色 - 提示
        
        # 绘制骨骼连线
        for connection in Config.SQUAT_CONNECTIONS:
            idx1, idx2 = connection
            if idx1 < len(person_landmarks) and idx2 < len(person_landmarks):
                pt1 = person_landmarks[idx1]
                pt2 = person_landmarks[idx2]
                x1, y1 = int(pt1.x * w), int(pt1.y * h)
                x2, y2 = int(pt2.x * w), int(pt2.y * h)
                cv2.line(frame, (x1, y1), (x2, y2), skeleton_color, 2)
        
        # 绘制关键点
        for landmark in person_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 4, skeleton_color, -1)
        
        # 高亮问题关节
        if form_analysis:
            for fb in form_analysis.feedbacks:
                if fb.joints_to_highlight and fb.severity in (Severity.WARNING, Severity.ERROR):
                    highlight_color = (0, 0, 255) if fb.severity == Severity.ERROR else (0, 165, 255)
                    for joint_idx in fb.joints_to_highlight:
                        if joint_idx < len(person_landmarks):
                            jx = int(person_landmarks[joint_idx].x * w)
                            jy = int(person_landmarks[joint_idx].y * h)
                            # 绘制高亮圆圈
                            cv2.circle(frame, (jx, jy), 12, highlight_color, 2)
                            cv2.circle(frame, (jx, jy), 16, highlight_color, 1)
        
        # 绘制计数
        frame = put_chinese_text(
            frame,
            f"深蹲: {metrics.rep_count}",
            (20, 50),
            font_size=32,
            color=(0, 255, 0)
        )
        
        # 绘制状态
        state_color = (0, 255, 0) if metrics.state.value == "STANDING" else (0, 165, 255)
        state_text = "站立" if metrics.state.value == "STANDING" else "下蹲"
        frame = put_chinese_text(
            frame,
            f"状态: {state_text}",
            (20, 90),
            font_size=24,
            color=state_color
        )
        
        # 绘制角度信息
        frame = put_chinese_text(
            frame,
            f"膝角: {metrics.avg_knee_angle:.0f}°",
            (20, 130),
            font_size=20,
            color=(200, 200, 200)
        )
        
        return frame
    
    def pause(self):
        self._paused = True
    
    def resume(self):
        self._paused = False
    
    def stop(self):
        self._running = False
    
    def reset_count(self):
        if self._squat_counter:
            self._squat_counter.reset()
        if self._form_analyzer:
            self._form_analyzer.reset()
        self._frame_count = 0
        self._pose_count = 0
        # 重置有效计数
        self._valid_rep_count = 0
        self._last_rep_count = 0
        # 重置反馈状态
        self._current_feedback_text = ""
        self._current_feedback_color = (0, 255, 0)
        self._feedback_show_start = 0
    
    def _cleanup(self):
        """清理资源"""
        if self._cap:
            self._cap.release()
            self._cap = None
        
        if self._squat_counter:
            self._squat_counter.close()
        
        if self._database and self._session_id:
            self._database.update_session(
                self._session_id,
                self._frame_count,
                self._squat_counter.count if self._squat_counter else 0
            )
        
        if self._pose_detector:
            self._pose_detector.close()
            self._pose_detector = None
        
        print(f"\n检测线程已停止")
        print(f"总帧数: {self._frame_count}, 检测到姿态: {self._pose_count}")
        if self._squat_counter:
            print(f"深蹲计数: {self._squat_counter.count}")

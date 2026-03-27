"""
检测工作线程

在后台线程中处理视频捕获和姿态检测，避免阻塞 UI。
"""

import time
from typing import Dict, List, Optional

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image, ImageDraw, ImageFont

from src.config import Config
from src.database import Database
from src.pose_detector import PoseDetector
from src.squat_counter import SquatCounter, SquatMetrics, PoseState
from src.jumping_jack_counter import JumpingJackCounter, JumpingJackMetrics, JumpingJackState
from src.form_analyzer import FormAnalyzer, FormAnalysis, Severity, StrictnessLevel
from src.adaptive_threshold import AdaptiveThresholdManager


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
    frame_ready = pyqtSignal(np.ndarray)
    metrics_updated = pyqtSignal(object)
    valid_count_updated = pyqtSignal(int, int)
    feedback_updated = pyqtSignal(str, str)
    session_created = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    camera_info = pyqtSignal(str, int, int, int)
    exercise_type_changed = pyqtSignal(str)
    
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
        self._exercise_type = Config.DEFAULT_EXERCISE_TYPE
        self._threshold_manager = AdaptiveThresholdManager()
        self._threshold_calibration_interval = 300
        self._last_threshold_calibration_frame = 0
    
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

    def set_exercise_type(self, exercise_type: str):
        self._exercise_type = exercise_type
    
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
                
                timestamp_ms = int((self._frame_count + 1) * 1000 / Config.CAMERA_FPS)
                pose_data = self._pose_detector.detect(rgb_frame, timestamp_ms)
                
                self._frame_count += 1
                
                metrics = None
                form_analysis = None
                if pose_data:
                    self._pose_count += 1

                    if self._exercise_type == "jumping_jack" and self._jumping_jack_counter:
                        metrics = self._jumping_jack_counter.update(pose_data)
                    elif self._squat_counter:
                        metrics = self._squat_counter.update(pose_data)

                    if metrics:
                        if self._squat_counter:
                            current_time = time.time()
                            form_analysis = self._form_analyzer.analyze(
                                pose_data,
                                metrics.avg_knee_angle,
                                metrics.state,
                                current_time
                            )
                            self._update_valid_count(metrics, form_analysis)
                            self._emit_feedback(form_analysis)
                            self._update_adaptive_threshold(metrics)

                    frame = self._render_landmarks(frame, pose_data, metrics, form_analysis)
                
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
        self._database = Database()

        try:
            self._pose_detector = PoseDetector()
        except FileNotFoundError as e:
            self.error_occurred.emit(f"模型文件错误: {e}")
            raise

        self._session_id = self._database.create_session()
        self.session_created.emit(self._session_id)

        if self._exercise_type == "jumping_jack":
            self._squat_counter = None
            self._jumping_jack_counter = JumpingJackCounter(
                database=self._database,
                session_id=self._session_id,
            )
        else:
            self._squat_counter = SquatCounter(
                database=self._database,
                session_id=self._session_id,
            )
            self._jumping_jack_counter = None

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
            rep_score = self._form_analyzer.get_rep_score()
            if rep_score.is_valid:
                self._valid_rep_count += 1
            print(f"深蹲 #{metrics.rep_count}: 错误比例={rep_score.error_ratio:.1%}, "
                  f"有效阈值={rep_score.valid_threshold:.1%}, 质量={rep_score.quality_score:.0f}分, "
                  f"有效={'✓' if rep_score.is_valid else '✗'}")
            self._form_analyzer.start_new_rep()
            self._last_rep_count = metrics.rep_count
            self.valid_count_updated.emit(self._valid_rep_count, metrics.rep_count)
    
    def _update_adaptive_threshold(self, metrics: SquatMetrics):
        from src.squat_counter import PoseState
        self._threshold_manager.add_sample(metrics.avg_knee_angle, metrics.state)
        
        if (self._frame_count - self._last_threshold_calibration_frame 
            >= self._threshold_calibration_interval):
            result = self._threshold_manager.calibrate()
            if result and result.confidence > 0.7:
                self._squat_counter.standing_threshold = result.standing_threshold
                self._squat_counter.squat_threshold = result.squat_threshold
                self._last_threshold_calibration_frame = self._frame_count
    
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
        if color == (0, 0, 255):
            return 3
        elif color == (0, 165, 255):
            return 2
        elif color == (0, 255, 255):
            return 1
        else:
            return 0

    def _render_landmarks(
        self,
        frame: np.ndarray,
        pose_data: Optional[Dict],
        metrics,
        form_analysis: Optional[FormAnalysis] = None
    ) -> np.ndarray:
        if not pose_data:
            return frame

        normalized_landmarks = pose_data.get('normalized')
        if not normalized_landmarks:
            return frame

        h, w = frame.shape[:2]
        person_landmarks = normalized_landmarks[0]

        if self._exercise_type == "jumping_jack":
            return self._render_jumping_jack(frame, person_landmarks, metrics, h, w)

        skeleton_color = (0, 255, 0)
        if form_analysis:
            severity = form_analysis.overall_severity
            if severity == Severity.ERROR:
                skeleton_color = (0, 0, 255)
            elif severity == Severity.WARNING:
                skeleton_color = (0, 165, 255)
            elif severity == Severity.INFO:
                skeleton_color = (0, 255, 255)

        for connection in Config.SQUAT_CONNECTIONS:
            idx1, idx2 = connection
            if idx1 < len(person_landmarks) and idx2 < len(person_landmarks):
                pt1 = person_landmarks[idx1]
                pt2 = person_landmarks[idx2]
                x1, y1 = int(pt1.x * w), int(pt1.y * h)
                x2, y2 = int(pt2.x * w), int(pt2.y * h)
                cv2.line(frame, (x1, y1), (x2, y2), skeleton_color, 2)

        for landmark in person_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 4, skeleton_color, -1)

        if form_analysis:
            for fb in form_analysis.feedbacks:
                if fb.joints_to_highlight and fb.severity in (Severity.WARNING, Severity.ERROR):
                    highlight_color = (0, 0, 255) if fb.severity == Severity.ERROR else (0, 165, 255)
                    for joint_idx in fb.joints_to_highlight:
                        if joint_idx < len(person_landmarks):
                            jx = int(person_landmarks[joint_idx].x * w)
                            jy = int(person_landmarks[joint_idx].y * h)
                            cv2.circle(frame, (jx, jy), 12, highlight_color, 2)
                            cv2.circle(frame, (jx, jy), 16, highlight_color, 1)

        frame = put_chinese_text(
            frame,
            f"深蹲: {metrics.rep_count}",
            (20, 50),
            font_size=32,
            color=(0, 255, 0)
        )

        if hasattr(metrics, 'peak_count') and metrics.peak_count > 0:
            frame = put_chinese_text(
                frame,
                f"谷值检测: {metrics.peak_count}",
                (20, 90),
                font_size=20,
                color=(0, 200, 255)
            )

        state_y = 130 if hasattr(metrics, 'peak_count') and metrics.peak_count > 0 else 90
        state_color = (0, 255, 0) if metrics.state.value == "STANDING" else (0, 165, 255)
        state_text = "站立" if metrics.state.value == "STANDING" else "下蹲"
        frame = put_chinese_text(
            frame,
            f"状态: {state_text}",
            (20, state_y),
            font_size=24,
            color=state_color
        )

        angle_y = state_y + 40
        frame = put_chinese_text(
            frame,
            f"膝角: {metrics.avg_knee_angle:.0f}°",
            (20, angle_y),
            font_size=20,
            color=(200, 200, 200)
        )

        return frame

    def _render_jumping_jack(
        self,
        frame: np.ndarray,
        person_landmarks,
        metrics: JumpingJackMetrics,
        h: int,
        w: int
    ) -> np.ndarray:
        skeleton_color = (0, 255, 0)

        for connection in Config.JUMPING_JACK_CONNECTIONS:
            idx1, idx2 = connection
            if idx1 < len(person_landmarks) and idx2 < len(person_landmarks):
                pt1 = person_landmarks[idx1]
                pt2 = person_landmarks[idx2]
                x1, y1 = int(pt1.x * w), int(pt1.y * h)
                x2, y2 = int(pt2.x * w), int(pt2.y * h)
                cv2.line(frame, (x1, y1), (x2, y2), skeleton_color, 2)

        for landmark in person_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 4, skeleton_color, -1)

        frame = put_chinese_text(
            frame,
            f"开合跳: {metrics.rep_count}",
            (20, 50),
            font_size=32,
            color=(0, 255, 0)
        )

        # 显示校准状态
        if hasattr(metrics, 'is_calibrated') and not metrics.is_calibrated:
            progress = self._jumping_jack_counter.calibration_progress if self._jumping_jack_counter else 0
            frame = put_chinese_text(
                frame,
                f"校准中: {progress*100:.0f}%",
                (20, 90),
                font_size=20,
                color=(0, 255, 255)
            )
            state_y = 130
        else:
            state_y = 90
        
        state_color = (0, 255, 0) if metrics.state.value == "OPEN" else (0, 165, 255)
        state_text = "开合" if metrics.state.value == "OPEN" else "并拢"
        frame = put_chinese_text(
            frame,
            f"状态: {state_text}",
            (20, state_y),
            font_size=24,
            color=state_color
        )

        # 显示踝距和腕高（调试信息）
        frame = put_chinese_text(
            frame,
            f"踝距: {metrics.ankle_distance:.2f}",
            (20, state_y + 40),
            font_size=18,
            color=(180, 180, 180)
        )

        frame = put_chinese_text(
            frame,
            f"腕高: {metrics.wrist_height:.2f}",
            (20, state_y + 65),
            font_size=18,
            color=(180, 180, 180)
        )

        frame = put_chinese_text(
            frame,
            f"开合比: {metrics.open_ratio:.2f}",
            (20, state_y + 90),
            font_size=18,
            color=(180, 180, 180)
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
        if self._jumping_jack_counter:
            self._jumping_jack_counter.reset()
        if self._form_analyzer:
            self._form_analyzer.reset()
        self._threshold_manager.reset()
        self._last_threshold_calibration_frame = 0
        self._frame_count = 0
        self._pose_count = 0
        self._valid_rep_count = 0
        self._last_rep_count = 0
        self._current_feedback_text = ""
        self._current_feedback_color = (0, 255, 0)
        self._feedback_show_start = 0
    
    def _cleanup(self):
        if self._cap:
            self._cap.release()
            self._cap = None

        if self._squat_counter:
            self._squat_counter.close()

        if self._jumping_jack_counter:
            self._jumping_jack_counter.close()

        count = 0
        if self._squat_counter:
            count = self._squat_counter.count
        elif self._jumping_jack_counter:
            count = self._jumping_jack_counter.count

        if self._database and self._session_id:
            self._database.update_session(
                self._session_id,
                self._frame_count,
                count
            )

        if self._pose_detector:
            self._pose_detector.close()
            self._pose_detector = None

        print(f"\n检测线程已停止")
        print(f"总帧数: {self._frame_count}, 检测到姿态: {self._pose_count}")
        if self._squat_counter:
            print(f"深蹲计数: {self._squat_counter.count}")
        elif self._jumping_jack_counter:
            print(f"开合跳计数: {self._jumping_jack_counter.count}")

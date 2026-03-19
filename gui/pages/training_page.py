"""
训练页面

实时训练界面，包含视频显示、统计面板和控制按钮。
"""

import time
from datetime import timedelta

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QVBoxLayout, QWidget
)

from gui.widgets.video_widget import VideoWidget
from gui.widgets.stats_panel import StatsPanel
from gui.widgets.angle_chart import AngleChart
from gui.workers.detection_worker import DetectionWorker
from src.squat_counter import SquatMetrics
from src.form_analyzer import StrictnessLevel


class TrainingPage(QWidget):
    """训练页面"""
    
    class State:
        IDLE = "idle"
        RUNNING = "running"
        PAUSED = "paused"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._state = self.State.IDLE
        self._worker: DetectionWorker = None
        self._session_id: int = None
        self._start_time: float = 0
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed_time)
        
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        video_container = QFrame()
        video_container.setProperty("cssClass", "card")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(12, 12, 12, 12)
        
        self._video_widget = VideoWidget()
        video_layout.addWidget(self._video_widget)
        
        content_layout.addWidget(video_container, stretch=7)
        
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        
        self._stats_panel = StatsPanel()
        self._stats_panel.setMaximumHeight(350)
        right_panel.addWidget(self._stats_panel)
        
        chart_container = QFrame()
        chart_container.setProperty("cssClass", "card")
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        
        chart_title = QLabel("角度变化曲线")
        chart_title.setProperty("cssClass", "subtitle")
        chart_layout.addWidget(chart_title)
        
        self._angle_chart = AngleChart()
        chart_layout.addWidget(self._angle_chart, stretch=1)
        
        right_panel.addWidget(chart_container, stretch=2)
        
        content_layout.addLayout(right_panel, stretch=3)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
    
    def _create_control_bar(self) -> QFrame:
        control_bar = QFrame()
        control_bar.setProperty("cssClass", "card")
        control_bar.setFixedHeight(70)
        
        layout = QHBoxLayout(control_bar)
        layout.setContentsMargins(16, 12, 16, 12)
        
        self._start_btn = QPushButton("▶ 开始训练")
        self._start_btn.setProperty("cssClass", "primary")
        self._start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self._start_btn)
        
        self._pause_btn = QPushButton("⏸ 暂停")
        self._pause_btn.setProperty("cssClass", "secondary")
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        self._pause_btn.setEnabled(False)
        layout.addWidget(self._pause_btn)
        
        self._stop_btn = QPushButton("⏹ 停止")
        self._stop_btn.setProperty("cssClass", "danger")
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        self._stop_btn.setEnabled(False)
        layout.addWidget(self._stop_btn)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #E2E8F0;")
        layout.addWidget(separator)
        
        self._reset_btn = QPushButton("🔄 重置计数")
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        self._reset_btn.setEnabled(False)
        layout.addWidget(self._reset_btn)
        
        self._screenshot_btn = QPushButton("📷 截图")
        self._screenshot_btn.clicked.connect(self._on_screenshot_clicked)
        self._screenshot_btn.setEnabled(False)
        layout.addWidget(self._screenshot_btn)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setStyleSheet("background-color: #E2E8F0;")
        layout.addWidget(separator2)
        
        strictness_label = QLabel("判定标准:")
        strictness_label.setStyleSheet("color: #64748B; font-size: 13px;")
        layout.addWidget(strictness_label)
        
        self._strictness_group = QButtonGroup(self)
        self._strictness_btns = {}
        for i, (level, name) in enumerate([
            (StrictnessLevel.RELAXED, "宽松"),
            (StrictnessLevel.NORMAL, "标准"),
            (StrictnessLevel.STRICT, "严格"),
        ]):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedWidth(50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E2E8F0;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #10B981;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, l=level: self._on_strictness_changed(l))
            layout.addWidget(btn)
            self._strictness_group.addButton(btn, i)
            self._strictness_btns[level] = btn
        
        self._strictness_btns[StrictnessLevel.NORMAL].setChecked(True)
        self._current_strictness = StrictnessLevel.NORMAL
        
        layout.addStretch()
        
        self._time_label = QLabel("00:00:00")
        self._time_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #64748B;
            font-family: 'Consolas', monospace;
        """)
        layout.addWidget(self._time_label)
        
        self._fps_label = QLabel("FPS: --")
        self._fps_label.setStyleSheet("""
            font-size: 14px;
            color: #94A3B8;
        """)
        layout.addWidget(self._fps_label)
        
        return control_bar
    
    def _update_button_states(self):
        if self._state == self.State.IDLE:
            self._start_btn.setEnabled(True)
            self._start_btn.setText("▶ 开始训练")
            self._pause_btn.setEnabled(False)
            self._pause_btn.setText("⏸ 暂停")
            self._stop_btn.setEnabled(False)
            self._reset_btn.setEnabled(False)
            self._screenshot_btn.setEnabled(False)
        
        elif self._state == self.State.RUNNING:
            self._start_btn.setEnabled(False)
            self._pause_btn.setEnabled(True)
            self._pause_btn.setText("⏸ 暂停")
            self._stop_btn.setEnabled(True)
            self._reset_btn.setEnabled(True)
            self._screenshot_btn.setEnabled(True)
        
        elif self._state == self.State.PAUSED:
            self._start_btn.setEnabled(True)
            self._start_btn.setText("▶ 继续")
            self._pause_btn.setEnabled(False)
            self._stop_btn.setEnabled(True)
            self._reset_btn.setEnabled(True)
            self._screenshot_btn.setEnabled(True)
    
    def _on_start_clicked(self):
        if self._state == self.State.IDLE:
            self._start_detection()
        elif self._state == self.State.PAUSED:
            self._resume_detection()
    
    def _on_pause_clicked(self):
        if self._state == self.State.RUNNING:
            self._pause_detection()
    
    def _on_stop_clicked(self):
        if self._state in (self.State.RUNNING, self.State.PAUSED):
            self._stop_detection()
    
    def _on_reset_clicked(self):
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置计数吗？当前数据将丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._reset_detection()
    
    def _on_screenshot_clicked(self):
        QMessageBox.information(self, "截图", "截图功能开发中...")
    
    def _on_strictness_changed(self, level: StrictnessLevel):
        self._current_strictness = level
        if self._worker:
            self._worker.set_strictness(level)
    
    def _start_detection(self):
        self._state = self.State.RUNNING
        self._start_time = time.time()
        self._update_button_states()
        
        self._worker = DetectionWorker()
        self._worker.frame_ready.connect(self._on_frame_ready)
        self._worker.metrics_updated.connect(self._on_metrics_updated)
        self._worker.session_created.connect(self._on_session_created)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.camera_info.connect(self._on_camera_info)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.valid_count_updated.connect(self._on_valid_count_updated)
        self._worker.feedback_updated.connect(self._on_feedback_updated)
        
        self._worker.set_strictness(self._current_strictness)
        self._worker.start()
        
        self._timer.start(1000)
    
    def _pause_detection(self):
        self._state = self.State.PAUSED
        self._update_button_states()
        
        if self._worker:
            self._worker.pause()
        
        self._timer.stop()
    
    def _resume_detection(self):
        self._state = self.State.RUNNING
        self._update_button_states()
        
        if self._worker:
            self._worker.resume()
        
        self._timer.start(1000)
    
    def _stop_detection(self):
        self._state = self.State.IDLE
        self._update_button_states()
        
        if self._worker:
            self._worker.stop()
            self._worker.wait()
        
        self._timer.stop()
        self._time_label.setText("00:00:00")
        self._fps_label.setText("FPS: --")
    
    def _reset_detection(self):
        if self._worker:
            self._worker.reset_count()
        
        self._stats_panel.reset()
        self._angle_chart.clear()
    
    def _on_frame_ready(self, frame):
        self._video_widget.update_frame(frame)
    
    def _on_metrics_updated(self, metrics: SquatMetrics):
        self._stats_panel.update_metrics(metrics)
        self._angle_chart.update_data(
            metrics.left_knee_angle,
            metrics.right_knee_angle,
            metrics.avg_knee_angle
        )
    
    def _on_session_created(self, session_id: int):
        self._session_id = session_id
        print(f"训练会话已创建: Session ID = {session_id}")
    
    def _on_valid_count_updated(self, valid_count: int, total_count: int):
        self._stats_panel.update_valid_count(valid_count, total_count)
    
    def _on_feedback_updated(self, message: str, severity: str):
        self._stats_panel.update_feedback(message, severity)
    
    def _on_camera_info(self, status: str, width: int, height: int, fps: int):
        self._fps_label.setText(f"FPS: {fps}")
        print(f"摄像头 {status}: {width}x{height} @ {fps}fps")
    
    def _on_error(self, error_msg: str):
        QMessageBox.critical(self, "错误", error_msg)
        self._stop_detection()
    
    def _on_worker_finished(self):
        print("检测线程已结束")
    
    def _update_elapsed_time(self):
        if self._start_time > 0:
            elapsed = time.time() - self._start_time
            td = timedelta(seconds=int(elapsed))
            self._time_label.setText(str(td).zfill(8))
    
    def closeEvent(self, event):
        if self._state != self.State.IDLE:
            self._stop_detection()
        event.accept()

"""
训练页面

实时训练界面，包含视频显示、统计面板和控制按钮。
"""

import time
from datetime import timedelta

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget
)

from gui.widgets.video_widget import VideoWidget
from gui.widgets.stats_panel import StatsPanel
from gui.widgets.angle_chart import AngleChart
from gui.workers.detection_worker import DetectionWorker
from src.squat_counter import SquatMetrics


class TrainingPage(QWidget):
    """
    训练页面
    
    包含视频显示区域、统计面板和控制按钮。
    """
    
    # 状态枚举
    class State:
        IDLE = "idle"           # 空闲
        RUNNING = "running"     # 运行中
        PAUSED = "paused"       # 暂停
    
    def __init__(self, parent=None):
        """初始化训练页面"""
        super().__init__(parent)
        
        # 状态
        self._state = self.State.IDLE
        self._worker: DetectionWorker = None
        self._session_id: int = None
        self._start_time: float = 0
        
        # 定时器（更新运行时间）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed_time)
        
        # 初始化 UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # ===== 上部分：视频 + 统计 =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # 左侧：视频显示
        video_container = QFrame()
        video_container.setProperty("cssClass", "card")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(12, 12, 12, 12)
        
        self._video_widget = VideoWidget()
        video_layout.addWidget(self._video_widget)
        
        content_layout.addWidget(video_container, stretch=7)
        
        # 右侧：统计面板 + 图表
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        
        # 统计面板 - 限制最大高度
        self._stats_panel = StatsPanel()
        self._stats_panel.setMaximumHeight(280)
        right_panel.addWidget(self._stats_panel)
        
        # 角度图表 - 给予更多空间
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
        
        # ===== 下部分：控制按钮栏 =====
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
    
    def _create_control_bar(self) -> QFrame:
        """创建控制按钮栏"""
        control_bar = QFrame()
        control_bar.setProperty("cssClass", "card")
        control_bar.setFixedHeight(70)
        
        layout = QHBoxLayout(control_bar)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # 开始/继续按钮
        self._start_btn = QPushButton("▶ 开始训练")
        self._start_btn.setProperty("cssClass", "primary")
        self._start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self._start_btn)
        
        # 暂停按钮
        self._pause_btn = QPushButton("⏸ 暂停")
        self._pause_btn.setProperty("cssClass", "secondary")
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        self._pause_btn.setEnabled(False)
        layout.addWidget(self._pause_btn)
        
        # 停止按钮
        self._stop_btn = QPushButton("⏹ 停止")
        self._stop_btn.setProperty("cssClass", "danger")
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        self._stop_btn.setEnabled(False)
        layout.addWidget(self._stop_btn)
        
        # 分隔符
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #E2E8F0;")
        layout.addWidget(separator)
        
        # 重置按钮
        self._reset_btn = QPushButton("🔄 重置计数")
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        self._reset_btn.setEnabled(False)
        layout.addWidget(self._reset_btn)
        
        # 保存截图按钮
        self._screenshot_btn = QPushButton("📷 截图")
        self._screenshot_btn.clicked.connect(self._on_screenshot_clicked)
        self._screenshot_btn.setEnabled(False)
        layout.addWidget(self._screenshot_btn)
        
        # 弹性空间
        layout.addStretch()
        
        # 运行时间
        self._time_label = QLabel("00:00:00")
        self._time_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #64748B;
            font-family: 'Consolas', monospace;
        """)
        layout.addWidget(self._time_label)
        
        # FPS
        self._fps_label = QLabel("FPS: --")
        self._fps_label.setStyleSheet("""
            font-size: 14px;
            color: #94A3B8;
        """)
        layout.addWidget(self._fps_label)
        
        return control_bar
    
    def _update_button_states(self):
        """更新按钮状态"""
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
        """开始/继续按钮点击"""
        if self._state == self.State.IDLE:
            self._start_detection()
        elif self._state == self.State.PAUSED:
            self._resume_detection()
    
    def _on_pause_clicked(self):
        """暂停按钮点击"""
        if self._state == self.State.RUNNING:
            self._pause_detection()
    
    def _on_stop_clicked(self):
        """停止按钮点击"""
        if self._state in (self.State.RUNNING, self.State.PAUSED):
            self._stop_detection()
    
    def _on_reset_clicked(self):
        """重置按钮点击"""
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
        """截图按钮点击"""
        # TODO: 实现截图功能
        QMessageBox.information(self, "截图", "截图功能开发中...")
    
    def _start_detection(self):
        """开始检测"""
        self._state = self.State.RUNNING
        self._start_time = time.time()
        self._update_button_states()
        
        # 创建工作线程
        self._worker = DetectionWorker()
        self._worker.frame_ready.connect(self._on_frame_ready)
        self._worker.metrics_updated.connect(self._on_metrics_updated)
        self._worker.session_created.connect(self._on_session_created)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.camera_info.connect(self._on_camera_info)
        self._worker.finished.connect(self._on_worker_finished)
        
        # 启动线程
        self._worker.start()
        
        # 启动定时器
        self._timer.start(1000)
    
    def _pause_detection(self):
        """暂停检测"""
        self._state = self.State.PAUSED
        self._update_button_states()
        
        if self._worker:
            self._worker.pause()
        
        self._timer.stop()
    
    def _resume_detection(self):
        """恢复检测"""
        self._state = self.State.RUNNING
        self._update_button_states()
        
        if self._worker:
            self._worker.resume()
        
        self._timer.start(1000)
    
    def _stop_detection(self):
        """停止检测"""
        self._state = self.State.IDLE
        self._update_button_states()
        
        if self._worker:
            self._worker.stop()
            self._worker.wait()
        
        self._timer.stop()
        self._time_label.setText("00:00:00")
        self._fps_label.setText("FPS: --")
    
    def _reset_detection(self):
        """重置检测"""
        if self._worker:
            self._worker.reset_count()
        
        self._stats_panel.reset()
        self._angle_chart.clear()
    
    def _on_frame_ready(self, frame):
        """收到新帧"""
        self._video_widget.update_frame(frame)
    
    def _on_metrics_updated(self, metrics: SquatMetrics):
        """指标更新"""
        self._stats_panel.update_metrics(metrics)
        self._angle_chart.update_data(
            metrics.left_knee_angle,
            metrics.right_knee_angle,
            metrics.avg_knee_angle
        )
        
        if self._worker:
            self._stats_panel.update_frame_stats(
                self._worker.frame_count,
                self._worker.pose_count
            )
    
    def _on_session_created(self, session_id: int):
        """会话创建"""
        self._session_id = session_id
        print(f"训练会话已创建: Session ID = {session_id}")
    
    def _on_camera_info(self, status: str, width: int, height: int, fps: int):
        """收到摄像头信息"""
        self._fps_label.setText(f"FPS: {fps}")
        print(f"摄像头 {status}: {width}x{height} @ {fps}fps")
    
    def _on_error(self, error_msg: str):
        """发生错误"""
        QMessageBox.critical(self, "错误", error_msg)
        self._stop_detection()
    
    def _on_worker_finished(self):
        """工作线程结束"""
        print("检测线程已结束")
    
    def _update_elapsed_time(self):
        """更新运行时间显示"""
        if self._start_time > 0:
            elapsed = time.time() - self._start_time
            td = timedelta(seconds=int(elapsed))
            self._time_label.setText(str(td).zfill(8))
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self._state != self.State.IDLE:
            self._stop_detection()
        event.accept()

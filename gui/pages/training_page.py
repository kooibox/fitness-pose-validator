"""
训练页面 v2

深色霓虹风格的实时训练界面。
"""

import time
from datetime import timedelta

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QVBoxLayout, QWidget, QSizePolicy
)

from gui.widgets.video_widget import VideoWidget
from gui.widgets.stats_panel import StatsPanelV2 as StatsPanel
from gui.widgets.angle_chart import AngleChart
from gui.widgets.neon_button import NeonButton, IconNeonButton
from gui.widgets.glow_card import GlowCard
from gui.workers.detection_worker import DetectionWorker
from src.squat_counter import SquatMetrics
from src.jumping_jack_counter import JumpingJackMetrics
from src.form_analyzer import StrictnessLevel


class TrainingPage(QWidget):
    """训练页面 V2 - 深色霓虹风格"""

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
        self._current_exercise_type = "squat"

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed_time)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # === 顶部状态栏 ===
        header = self._create_header()
        main_layout.addWidget(header)

        # === 主内容区 ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # 左侧：视频区域
        video_container = self._create_video_container()
        content_layout.addWidget(video_container, stretch=5)

        # 右侧：统计面板
        self._stats_panel = StatsPanel()
        content_layout.addWidget(self._stats_panel, stretch=4)

        main_layout.addLayout(content_layout, stretch=1)

        # === 底部控制栏 ===
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)

    def _create_header(self) -> QFrame:
        """创建顶部状态栏"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)

        # 左侧：状态指示灯 + 运动类型
        status_layout = QHBoxLayout()
        status_layout.setSpacing(12)

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet("color: #71717A; font-size: 14px; background: transparent; border: none;")
        status_layout.addWidget(self._status_dot)

        self._exercise_type_label = QLabel("深蹲")
        self._exercise_type_label.setStyleSheet("color: #22C55E; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        status_layout.addWidget(self._exercise_type_label)

        layout.addLayout(status_layout)

        layout.addStretch()

        # 右侧：时间 + 分辨率
        info_layout = QHBoxLayout()
        info_layout.setSpacing(24)

        time_container = QHBoxLayout()
        time_container.setSpacing(8)

        time_icon = QLabel("⏱")
        time_icon.setStyleSheet("font-size: 16px; color: #71717A; background: transparent; border: none;")
        time_container.addWidget(time_icon)

        self._time_label = QLabel("00:00:00")
        self._time_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 20px;
            font-weight: 600;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            background: transparent;
            border: none;
        """)
        time_container.addWidget(self._time_label)
        info_layout.addLayout(time_container)

        self._fps_label = QLabel("30fps")
        self._fps_label.setStyleSheet("color: #71717A; font-size: 13px; background: transparent; border: none;")
        info_layout.addWidget(self._fps_label)

        layout.addLayout(info_layout)

        return header

    def _create_video_container(self) -> QFrame:
        """创建视频容器"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #0D0D0F;
                border-radius: 16px;
                border: 2px solid #27272A;
            }
            QFrame:hover {
                border-color: #3F3F46;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # 视频组件
        self._video_widget = VideoWidget()
        self._video_widget.setMaximumHeight(400)
        self._video_widget.setStyleSheet("""
            QLabel {
                background-color: #0D0D0F;
                border-radius: 14px;
                border: none;
            }
        """)
        layout.addWidget(self._video_widget)

        # 角度图表
        chart_container = QFrame()
        chart_container.setMinimumHeight(200)
        chart_container.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 12px;
                border: 1px solid #27272A;
                margin: 8px;
            }
        """)
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(12, 8, 12, 8)

        chart_title = QLabel("角度变化曲线")
        chart_title.setStyleSheet("color: #A1A1AA; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        chart_layout.addWidget(chart_title)

        self._angle_chart = AngleChart()
        self._angle_chart.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 8px;
            }
        """)
        chart_layout.addWidget(self._angle_chart)

        layout.addWidget(chart_container)

        return container

    def _create_control_bar(self) -> QFrame:
        """创建控制栏"""
        control_bar = QFrame()
        control_bar.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        control_bar.setFixedHeight(72)

        layout = QHBoxLayout(control_bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # 左侧：主控制按钮
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self._start_btn = QPushButton("▶ 开始训练")
        self._start_btn.setToolTip("开始新的训练会话")
        self._start_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
                min-width: 110px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #16A34A 0%, #15803D 100%);
                border: 1px solid #22C55E;
            }
            QPushButton:disabled {
                background: #27272A;
                color: #71717A;
            }
        """)
        self._start_btn.clicked.connect(self._on_start_clicked)
        controls_layout.addWidget(self._start_btn)

        self._pause_btn = QPushButton("⏸ 暂停")
        self._pause_btn.setToolTip("暂停当前训练")
        self._pause_btn.setEnabled(False)
        self._pause_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
                min-width: 110px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
                border: 1px solid #3B82F6;
            }
            QPushButton:disabled {
                background: #27272A;
                color: #71717A;
            }
        """)
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        controls_layout.addWidget(self._pause_btn)

        self._stop_btn = QPushButton("⏹ 停止")
        self._stop_btn.setToolTip("停止训练并保存数据")
        self._stop_btn.setEnabled(False)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
                min-width: 110px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
                border: 1px solid #EF4444;
            }
            QPushButton:disabled {
                background: #27272A;
                color: #71717A;
            }
        """)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        controls_layout.addWidget(self._stop_btn)

        layout.addLayout(controls_layout)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #27272A;")
        separator.setFixedWidth(1)
        layout.addWidget(separator)

        # 辅助按钮
        aux_layout = QHBoxLayout()
        aux_layout.setSpacing(6)

        self._reset_btn = QPushButton("🔄 重置")
        self._reset_btn.setToolTip("重置计数（当前数据将丢失）")
        self._reset_btn.setEnabled(False)
        self._reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E22;
                color: #A1A1AA;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #252529;
                color: #FFFFFF;
                border-color: #52525B;
            }
            QPushButton:disabled {
                background-color: #161619;
                color: #52525B;
                border-color: #27272A;
            }
        """)
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        aux_layout.addWidget(self._reset_btn)

        self._screenshot_btn = QPushButton("📷 截图")
        self._screenshot_btn.setToolTip("保存当前画面截图")
        self._screenshot_btn.setEnabled(False)
        self._screenshot_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E22;
                color: #A1A1AA;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #252529;
                color: #FFFFFF;
                border-color: #52525B;
            }
            QPushButton:disabled {
                background-color: #161619;
                color: #52525B;
                border-color: #27272A;
            }
        """)
        self._screenshot_btn.clicked.connect(self._on_screenshot_clicked)
        aux_layout.addWidget(self._screenshot_btn)

        layout.addLayout(aux_layout)

        # 分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setStyleSheet("background-color: #27272A;")
        separator2.setFixedWidth(1)
        layout.addWidget(separator2)

        # 判定标准
        strictness_layout = QHBoxLayout()
        strictness_layout.setSpacing(6)

        self._strictness_group = QButtonGroup(self)
        self._strictness_btns = {}

        strictness_styles = """
            QPushButton {
                background-color: #1E1E22;
                color: #A1A1AA;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: rgba(34, 197, 94, 0.2);
                color: #22C55E;
                border-color: #22C55E;
            }
            QPushButton:hover:!checked {
                background-color: #252529;
                color: #FFFFFF;
            }
        """

        for i, (level, name) in enumerate([
            (StrictnessLevel.RELAXED, "宽松"),
            (StrictnessLevel.NORMAL, "标准"),
            (StrictnessLevel.STRICT, "严格"),
        ]):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setStyleSheet(strictness_styles)
            btn.clicked.connect(lambda checked, l=level: self._on_strictness_changed(l))
            strictness_layout.addWidget(btn)
            self._strictness_group.addButton(btn, i)
            self._strictness_btns[level] = btn

        self._strictness_btns[StrictnessLevel.NORMAL].setChecked(True)
        self._current_strictness = StrictnessLevel.NORMAL

        layout.addLayout(strictness_layout)

        # 分隔线
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.VLine)
        separator3.setStyleSheet("background-color: #27272A;")
        separator3.setFixedWidth(1)
        layout.addWidget(separator3)

        # 运动类型选择
        exercise_layout = QHBoxLayout()
        exercise_layout.setSpacing(6)

        self._exercise_combo = QComboBox()
        self._exercise_combo.setToolTip("选择运动类型")
        self._exercise_combo.addItems(["深蹲", "开合跳"])
        self._exercise_combo.setFixedWidth(100)
        self._exercise_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E1E22;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 6px 12px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #52525B;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #1E1E22;
                border: 1px solid #3F3F46;
                selection-background-color: rgba(34, 197, 94, 0.2);
                selection-color: #22C55E;
                color: #FFFFFF;
            }
        """)
        self._exercise_combo.currentIndexChanged.connect(self._on_exercise_changed)
        exercise_layout.addWidget(self._exercise_combo)

        layout.addLayout(exercise_layout)

        layout.addStretch()

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
            self._exercise_combo.setEnabled(True)

            self._status_dot.setText("●")
            self._status_dot.setStyleSheet("color: #71717A; font-size: 14px;")

        elif self._state == self.State.RUNNING:
            self._start_btn.setEnabled(False)
            self._pause_btn.setEnabled(True)
            self._pause_btn.setText("⏸ 暂停")
            self._stop_btn.setEnabled(True)
            self._reset_btn.setEnabled(True)
            self._screenshot_btn.setEnabled(True)
            self._exercise_combo.setEnabled(False)

            self._status_dot.setText("●")
            self._status_dot.setStyleSheet("color: #22C55E; font-size: 14px;")

        elif self._state == self.State.PAUSED:
            self._start_btn.setEnabled(True)
            self._start_btn.setText("▶ 继续")
            self._pause_btn.setEnabled(False)
            self._stop_btn.setEnabled(True)
            self._reset_btn.setEnabled(True)
            self._screenshot_btn.setEnabled(True)
            self._exercise_combo.setEnabled(False)

            self._status_dot.setText("●")
            self._status_dot.setStyleSheet("color: #F97316; font-size: 14px;")

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
        """截图当前训练画面"""
        import os
        from datetime import datetime
        from pathlib import Path

        current_frame = self._video_widget.current_frame
        if current_frame is None:
            QMessageBox.warning(self, "截图失败", "没有可截图的画面")
            return

        screenshot_dir = Path(__file__).parent.parent.parent / "data" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = screenshot_dir / filename

        import cv2
        success = cv2.imwrite(str(filepath), current_frame)

        if success:
            QMessageBox.information(
                self,
                "截图成功",
                f"截图已保存到:\n{filepath}"
            )
        else:
            QMessageBox.critical(self, "截图失败", "无法保存截图文件")

    def _on_strictness_changed(self, level: StrictnessLevel):
        self._current_strictness = level
        if self._worker:
            self._worker.set_strictness(level)

    def _on_exercise_changed(self, index: int):
        self._current_exercise_type = "jumping_jack" if index == 1 else "squat"

        # 更新状态标签
        if index == 1:
            self._exercise_type_label.setText("开合跳")
            self._exercise_type_label.setStyleSheet("color: #3B82F6; font-size: 16px; font-weight: 600;")
        else:
            self._exercise_type_label.setText("深蹲")
            self._exercise_type_label.setStyleSheet("color: #22C55E; font-size: 16px; font-weight: 600;")

        # 切换统计面板显示
        self._stats_panel.set_exercise_mode(self._current_exercise_type)

        if self._worker:
            self._worker.set_exercise_type(self._current_exercise_type)

    def _start_detection(self):
        self._state = self.State.RUNNING
        self._start_time = time.time()
        
        self._start_btn.setEnabled(False)
        self._start_btn.setText("⏳ 启动中...")
        
        self._worker = DetectionWorker()
        self._worker.frame_ready.connect(self._on_frame_ready)
        self._worker.metrics_updated.connect(self._on_metrics_updated)
        self._worker.session_created.connect(self._on_session_created)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.camera_info.connect(self._on_camera_info)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.valid_count_updated.connect(self._on_valid_count_updated)
        self._worker.feedback_updated.connect(self._on_feedback_updated)

        # 应用待处理的设置
        self._apply_pending_settings()

        self._worker.set_strictness(self._current_strictness)
        self._worker.set_exercise_type(self._current_exercise_type)
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
        self._fps_label.setText("30fps")
        self._video_widget.show_placeholder("🎥 训练已结束")

    def _reset_detection(self):
        if self._worker:
            self._worker.reset_count()

        self._stats_panel.reset()
        self._angle_chart.clear()

    def _on_frame_ready(self, frame):
        self._video_widget.update_frame(frame)

    def _on_metrics_updated(self, metrics):
        if isinstance(metrics, JumpingJackMetrics):
            self._stats_panel.update_jumping_jack_metrics(metrics)
            self._angle_chart.update_data(
                metrics.left_hip_angle,
                metrics.right_hip_angle,
                metrics.avg_hip_angle
            )
        else:
            self._stats_panel.update_squat_metrics(metrics)
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
        self._fps_label.setText(f"{fps}fps")
        print(f"摄像头 {status}: {width}x{height} @ {fps}fps")
        
        if status == "已连接":
            self._update_button_states()

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

    def apply_settings(self, settings: dict):
        """应用设置到训练页面"""
        if self._state != self.State.IDLE:
            QMessageBox.information(
                self,
                "设置已保存",
                "设置已保存，将在下次开始训练时生效。"
            )
            return

        self._pending_settings = settings

    def _apply_pending_settings(self):
        """应用待处理的设置到检测线程"""
        if not hasattr(self, '_pending_settings') or not self._pending_settings:
            return

        settings = self._pending_settings

        if self._worker:
            if "camera_index" in settings:
                self._worker.set_camera_index(settings["camera_index"])
            if "rotate_frame" in settings:
                self._worker.set_rotate_frame(settings["rotate_frame"])

        self._pending_settings = {}

    def closeEvent(self, event):
        if self._state != self.State.IDLE:
            self._stop_detection()
        event.accept()

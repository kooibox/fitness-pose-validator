"""
统计面板控件 v2

支持深蹲/开合跳两种运动模式的独立UI设计。
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QProgressBar, QVBoxLayout, QWidget, QSizePolicy
)

from src.squat_counter import PoseState, SquatMetrics
from src.jumping_jack_counter import JumpingJackMetrics, JumpingJackState
from gui.widgets.circular_progress import CircularProgress, StateIndicator


class StatsPanelV2(QWidget):
    """
    统计面板 V2 - 深色霓虹风格

    支持深蹲和开合跳两种运动模式，每种模式有独立的数据展示。
    """

    # 信号：请求切换运动类型显示
    exercise_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_exercise = "squat"  # "squat" 或 "jumping_jack"
        self._current_metrics = None

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(20)

        # === 深蹲模式面板 ===
        self._squat_panel = self._create_squat_panel()
        main_layout.addWidget(self._squat_panel)

        # === 开合跳模式面板 ===
        self._jj_panel = self._create_jumping_jack_panel()
        self._jj_panel.setVisible(False)  # 默认隐藏

        main_layout.addWidget(self._jj_panel)

        main_layout.addStretch()

    def _create_squat_panel(self) -> QWidget:
        """创建深蹲模式面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # 标题
        title = QLabel("深蹲训练")
        title.setStyleSheet("""
            color: #22C55E;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title)

        # 主统计卡片行
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        # 计数卡片
        self._squat_count_card = self._create_count_card("次数", "0", "#22C55E")
        stats_row.addWidget(self._squat_count_card)

        # 有效计数卡片
        self._squat_valid_card = self._create_count_card("有效", "0", "#3B82F6")
        stats_row.addWidget(self._squat_valid_card)

        layout.addLayout(stats_row)

        # 膝关节角度卡片
        angles_title = QLabel("膝关节角度")
        angles_title.setStyleSheet("""
            color: #A1A1AA;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            border: none;
            margin-top: 8px;
        """)
        layout.addWidget(angles_title)

        self._squat_left_angle = self._create_angle_row("左膝", "#22C55E")
        self._squat_right_angle = self._create_angle_row("右膝", "#3B82F6")
        self._squat_avg_angle = self._create_angle_row("平均", "#F97316")

        layout.addWidget(self._squat_left_angle)
        layout.addWidget(self._squat_right_angle)
        layout.addWidget(self._squat_avg_angle)

        # 动作反馈
        feedback_card = QFrame()
        feedback_card.setStyleSheet("""
            QFrame {
                background-color: #1E1E22;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        feedback_layout = QVBoxLayout(feedback_card)
        feedback_layout.setContentsMargins(16, 14, 16, 14)
        feedback_layout.setSpacing(6)

        feedback_title = QLabel("动作提示")
        feedback_title.setStyleSheet("color: #71717A; font-size: 12px; background: transparent; border: none;")
        feedback_layout.addWidget(feedback_title)

        self._squat_feedback_label = QLabel("准备开始")
        self._squat_feedback_label.setStyleSheet("""
            color: #22C55E;
            font-size: 15px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 10px;
        """)
        self._squat_feedback_label.setWordWrap(True)
        feedback_layout.addWidget(self._squat_feedback_label)

        layout.addWidget(feedback_card)

        return panel

    def _create_jumping_jack_panel(self) -> QWidget:
        """创建开合跳模式面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # 标题
        title = QLabel("开合跳训练")
        title.setStyleSheet("""
            color: #3B82F6;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title)

        # 主统计卡片行
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        # 计数卡片
        self._jj_count_card = self._create_count_card("次数", "0", "#3B82F6")
        stats_row.addWidget(self._jj_count_card)

        # 有效计数卡片
        self._jj_valid_card = self._create_count_card("有效", "0", "#22C55E")
        stats_row.addWidget(self._jj_valid_card)

        layout.addLayout(stats_row)

        # 髋关节角度卡片
        hip_title = QLabel("髋关节角度")
        hip_title.setStyleSheet("""
            color: #A1A1AA;
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
            margin-top: 8px;
        """)
        layout.addWidget(hip_title)

        self._jj_left_hip = self._create_angle_row("左髋", "#3B82F6")
        self._jj_right_hip = self._create_angle_row("右髋", "#22C55E")
        self._jj_avg_hip = self._create_angle_row("平均", "#F97316")

        layout.addWidget(self._jj_left_hip)
        layout.addWidget(self._jj_right_hip)
        layout.addWidget(self._jj_avg_hip)

        # 肩关节角度卡片
        shoulder_title = QLabel("肩关节角度")
        shoulder_title.setStyleSheet("""
            color: #A1A1AA;
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
            margin-top: 8px;
        """)
        layout.addWidget(shoulder_title)

        self._jj_left_shoulder = self._create_angle_row("左肩", "#8B5CF6")
        self._jj_right_shoulder = self._create_angle_row("右肩", "#EC4899")
        self._jj_avg_shoulder = self._create_angle_row("平均", "#F97316")

        layout.addWidget(self._jj_left_shoulder)
        layout.addWidget(self._jj_right_shoulder)
        layout.addWidget(self._jj_avg_shoulder)

        # 动作反馈
        feedback_card = QFrame()
        feedback_card.setStyleSheet("""
            QFrame {
                background-color: #1E1E22;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        feedback_layout = QVBoxLayout(feedback_card)
        feedback_layout.setContentsMargins(16, 14, 16, 14)
        feedback_layout.setSpacing(6)

        feedback_title = QLabel("动作提示")
        feedback_title.setStyleSheet("color: #71717A; font-size: 12px; background: transparent; border: none;")
        feedback_layout.addWidget(feedback_title)

        self._jj_feedback_label = QLabel("准备开始")
        self._jj_feedback_label.setStyleSheet("""
            color: #3B82F6;
            font-size: 15px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 10px;
        """)
        self._jj_feedback_label.setWordWrap(True)
        feedback_layout.addWidget(self._jj_feedback_label)

        layout.addWidget(feedback_card)

        return panel

    def _create_count_card(self, title: str, value: str, color: str) -> QFrame:
        """创建计数卡片"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1E1E22;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #71717A; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {color};
            font-size: 24px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setMinimumHeight(36)
        layout.addWidget(value_label)

        return card

    def _create_angle_row(self, title: str, color: str) -> QFrame:
        """创建角度显示行"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1E1E22;
                border-radius: 8px;
                border: 1px solid #27272A;
            }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setFixedWidth(35)
        title_label.setStyleSheet(f"""
            color: #A1A1AA;
            font-size: 13px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title_label)

        progress = QProgressBar()
        progress.setRange(0, 180)
        progress.setValue(0)
        progress.setTextVisible(False)
        progress.setFixedHeight(6)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #27272A;
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(progress, stretch=1)

        value_label = QLabel("0°")
        value_label.setFixedWidth(40)
        value_label.setStyleSheet(f"""
            color: {color};
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(value_label)

        # 存储引用以便更新
        frame._progress = progress
        frame._value_label = value_label
        frame._color = color

        return frame

    def set_exercise_mode(self, exercise: str):
        """切换运动模式显示"""
        self._current_exercise = exercise

        if exercise == "jumping_jack":
            self._squat_panel.setVisible(False)
            self._jj_panel.setVisible(True)
        else:
            self._squat_panel.setVisible(True)
            self._jj_panel.setVisible(False)

    def update_squat_metrics(self, metrics: SquatMetrics):
        """更新深蹲指标"""
        # 计数
        self._squat_count_card.findChildren(QLabel)[1].setText(str(metrics.rep_count))

        # 角度
        self._update_angle_row(self._squat_left_angle, metrics.left_knee_angle)
        self._update_angle_row(self._squat_right_angle, metrics.right_knee_angle)
        self._update_angle_row(self._squat_avg_angle, metrics.avg_knee_angle)

    def update_jumping_jack_metrics(self, metrics: JumpingJackMetrics):
        """更新开合跳指标"""
        # 计数
        self._jj_count_card.findChildren(QLabel)[1].setText(str(metrics.rep_count))

        # 髋关节角度
        self._update_angle_row(self._jj_left_hip, metrics.left_hip_angle)
        self._update_angle_row(self._jj_right_hip, metrics.right_hip_angle)
        self._update_angle_row(self._jj_avg_hip, metrics.avg_hip_angle)

        # 肩关节角度
        self._update_angle_row(self._jj_left_shoulder, metrics.left_shoulder_angle)
        self._update_angle_row(self._jj_right_shoulder, metrics.right_shoulder_angle)
        self._update_angle_row(self._jj_avg_shoulder, metrics.avg_shoulder_angle)

    def _update_angle_row(self, row: QFrame, angle: float):
        """更新角度行"""
        row._progress.setValue(int(angle))
        row._value_label.setText(f"{angle:.0f}°")

        # 根据角度变色
        if angle < 90:
            color = "#F97316"
        elif angle < 165:
            color = "#3B82F6"
        else:
            color = "#22C55E"

        row._value_label.setStyleSheet(f"""
            color: {color};
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        row._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #27272A;
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)

    def update_valid_count(self, valid_count: int, total_count: int):
        """更新有效计数"""
        if self._current_exercise == "jumping_jack":
            self._jj_valid_card.findChildren(QLabel)[1].setText(str(valid_count))
        else:
            self._squat_valid_card.findChildren(QLabel)[1].setText(str(valid_count))

    def update_feedback(self, message: str, severity: str = "ok"):
        """更新动作反馈"""
        colors = {
            "error": ("#EF4444", "#FEF2F2"),
            "warning": ("#F97316", "#FFFBEB"),
            "info": ("#3B82F6", "#EFF6FF"),
            "ok": ("#22C55E", "#F0FDF4"),
        }

        text_color, bg_color = colors.get(severity, colors["ok"])

        if self._current_exercise == "jumping_jack":
            self._jj_feedback_label.setStyleSheet(f"""
                color: {text_color};
                font-size: 15px;
                font-weight: 600;
                background: {bg_color};
                border: none;
                padding: 8px;
                border-radius: 6px;
            """)
            self._jj_feedback_label.setText(message)
        else:
            self._squat_feedback_label.setStyleSheet(f"""
                color: {text_color};
                font-size: 15px;
                font-weight: 600;
                background: {bg_color};
                border: none;
                padding: 8px;
                border-radius: 6px;
            """)
            self._squat_feedback_label.setText(message)

    def reset(self):
        """重置面板"""
        if self._current_exercise == "jumping_jack":
            self._jj_count_card.findChildren(QLabel)[1].setText("0")
            self._jj_valid_card.findChildren(QLabel)[1].setText("0")
            self._jj_feedback_label.setText("准备开始")
        else:
            self._squat_count_card.findChildren(QLabel)[1].setText("0")
            self._squat_valid_card.findChildren(QLabel)[1].setText("0")
            self._squat_feedback_label.setText("准备开始")


# 保留旧版 StatsPanel 以兼容
class StatsPanel(StatsPanelV2):
    """向后兼容的 StatsPanel"""
    pass

"""
统计面板控件

显示实时训练统计数据。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, 
    QProgressBar, QVBoxLayout, QWidget
)

from src.squat_counter import PoseState, SquatMetrics


class AngleCard(QFrame):
    """角度卡片"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-size: 12px; color: #64748B;")
        self._title_label.setFixedWidth(30)
        layout.addWidget(self._title_label)
        
        self._progress = QProgressBar()
        self._progress.setRange(0, 180)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(12)
        layout.addWidget(self._progress, stretch=1)
        
        self._value_label = QLabel("0°")
        self._value_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #10B981;")
        self._value_label.setFixedWidth(35)
        layout.addWidget(self._value_label)
    
    def set_angle(self, angle: float):
        self._value_label.setText(f"{angle:.0f}°")
        self._progress.setValue(int(angle))
        
        if angle < 90:
            color = "#F59E0B"
        elif angle < 165:
            color = "#3B82F6"
        else:
            color = "#10B981"
        
        self._value_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {color};")
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #E2E8F0;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)


class StatsPanel(QWidget):
    """统计面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # ===== 深蹲计数 + 有效计数 + 状态 =====
        top_card = QFrame()
        top_card.setProperty("cssClass", "card")
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(16)
        
        # 深蹲次数
        count_layout = QVBoxLayout()
        count_layout.setSpacing(4)
        count_title = QLabel("深蹲次数")
        count_title.setStyleSheet("font-size: 13px; color: #64748B;")
        count_layout.addWidget(count_title)
        
        self._rep_label = QLabel("0")
        self._rep_label.setStyleSheet("font-size: 40px; font-weight: 700; color: #10B981;")
        self._rep_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_layout.addWidget(self._rep_label)
        top_layout.addLayout(count_layout)
        
        # 有效次数
        valid_layout = QVBoxLayout()
        valid_layout.setSpacing(4)
        valid_title = QLabel("有效次数")
        valid_title.setStyleSheet("font-size: 13px; color: #64748B;")
        valid_layout.addWidget(valid_title)
        
        self._valid_label = QLabel("0")
        self._valid_label.setStyleSheet("font-size: 40px; font-weight: 700; color: #3B82F6;")
        self._valid_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        valid_layout.addWidget(self._valid_label)
        top_layout.addLayout(valid_layout)
        
        # 当前状态
        state_layout = QVBoxLayout()
        state_layout.setSpacing(4)
        state_title = QLabel("当前状态")
        state_title.setStyleSheet("font-size: 13px; color: #64748B;")
        state_layout.addWidget(state_title)
        
        self._state_label = QLabel("站立")
        self._state_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #10B981;")
        self._state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        state_layout.addWidget(self._state_label)
        top_layout.addLayout(state_layout)
        
        layout.addWidget(top_card)
        
        # ===== 动作提示 =====
        feedback_card = QFrame()
        feedback_card.setProperty("cssClass", "card")
        feedback_layout = QVBoxLayout(feedback_card)
        feedback_layout.setContentsMargins(16, 12, 16, 12)
        feedback_layout.setSpacing(6)
        
        feedback_title = QLabel("动作提示")
        feedback_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        feedback_layout.addWidget(feedback_title)
        
        self._feedback_label = QLabel("准备开始")
        self._feedback_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: 600; 
            color: #10B981;
            padding: 8px;
            background-color: #F0FDF4;
            border-radius: 6px;
        """)
        self._feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feedback_label.setWordWrap(True)
        self._feedback_label.setMinimumHeight(40)
        feedback_layout.addWidget(self._feedback_label)
        
        layout.addWidget(feedback_card)
        
        # ===== 膝关节角度 =====
        angles_card = QFrame()
        angles_card.setProperty("cssClass", "card")
        angles_layout = QVBoxLayout(angles_card)
        angles_layout.setContentsMargins(12, 8, 12, 8)
        angles_layout.setSpacing(6)
        
        angles_title = QLabel("膝关节角度")
        angles_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        angles_layout.addWidget(angles_title)
        
        self._left_angle_card = AngleCard("左膝")
        angles_layout.addWidget(self._left_angle_card)
        
        self._right_angle_card = AngleCard("右膝")
        angles_layout.addWidget(self._right_angle_card)
        
        self._avg_angle_card = AngleCard("平均")
        angles_layout.addWidget(self._avg_angle_card)
        
        layout.addWidget(angles_card)
        
        layout.addStretch()
    
    def update_metrics(self, metrics: SquatMetrics):
        self._rep_label.setText(str(metrics.rep_count))
        
        if metrics.state == PoseState.STANDING:
            self._state_label.setText("站立")
            self._state_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #10B981;")
        else:
            self._state_label.setText("下蹲")
            self._state_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #F59E0B;")
        
        self._left_angle_card.set_angle(metrics.left_knee_angle)
        self._right_angle_card.set_angle(metrics.right_knee_angle)
        self._avg_angle_card.set_angle(metrics.avg_knee_angle)
    
    def update_valid_count(self, valid_count: int, total_count: int):
        self._valid_label.setText(str(valid_count))
        
        if valid_count == total_count and total_count > 0:
            color = "#10B981"
        elif valid_count > 0:
            color = "#3B82F6"
        else:
            color = "#F59E0B"
        
        self._valid_label.setStyleSheet(f"font-size: 40px; font-weight: 700; color: {color};")
    
    def update_feedback(self, message: str, severity: str = "ok"):
        colors = {
            "error": ("#EF4444", "#FEF2F2"),
            "warning": ("#F59E0B", "#FFFBEB"),
            "info": ("#3B82F6", "#EFF6FF"),
            "ok": ("#10B981", "#F0FDF4"),
        }
        
        text_color, bg_color = colors.get(severity, colors["ok"])
        
        self._feedback_label.setText(message)
        self._feedback_label.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: 600; 
            color: {text_color};
            padding: 8px;
            background-color: {bg_color};
            border-radius: 6px;
        """)
    
    def reset(self):
        self._rep_label.setText("0")
        self._valid_label.setText("0")
        self._valid_label.setStyleSheet("font-size: 40px; font-weight: 700; color: #3B82F6;")
        self._state_label.setText("站立")
        self._state_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #10B981;")
        self._left_angle_card.set_angle(0)
        self._right_angle_card.set_angle(0)
        self._avg_angle_card.set_angle(0)
        self._feedback_label.setText("准备开始")
        self._feedback_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: 600; 
            color: #10B981;
            padding: 8px;
            background-color: #F0FDF4;
            border-radius: 6px;
        """)
"""
统计面板控件

显示实时训练统计数据。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, 
    QProgressBar, QVBoxLayout, QWidget, QScrollArea
)

from src.squat_counter import PoseState, SquatMetrics


class AngleCard(QFrame):
    """
    角度卡片
    
    带有进度条的角度显示卡片（紧凑版）。
    """
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        
        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # 标题
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-size: 12px; color: #64748B;")
        self._title_label.setFixedWidth(30)
        layout.addWidget(self._title_label)
        
        # 进度条
        self._progress = QProgressBar()
        self._progress.setRange(0, 180)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(12)
        layout.addWidget(self._progress, stretch=1)
        
        # 数值
        self._value_label = QLabel("0°")
        self._value_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #10B981;")
        self._value_label.setFixedWidth(35)
        layout.addWidget(self._value_label)
    
    def set_angle(self, angle: float):
        """更新角度"""
        self._value_label.setText(f"{angle:.0f}°")
        self._progress.setValue(int(angle))
        
        # 根据角度改变颜色
        if angle < 90:
            color = "#F59E0B"  # 下蹲状态 - 橙色
        elif angle < 165:
            color = "#3B82F6"  # 过渡状态 - 蓝色
        else:
            color = "#10B981"  # 站立状态 - 绿色
        
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
    """
    统计面板
    
    包含所有训练统计数据的面板（紧凑版）。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # ===== 深蹲计数 + 状态（一行）=====
        top_card = QFrame()
        top_card.setProperty("cssClass", "card")
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(16, 12, 16, 12)
        
        # 计数
        count_layout = QVBoxLayout()
        count_layout.setSpacing(2)
        count_title = QLabel("深蹲次数")
        count_title.setStyleSheet("font-size: 12px; color: #64748B;")
        count_layout.addWidget(count_title)
        
        self._rep_label = QLabel("0")
        self._rep_label.setStyleSheet("""
            font-size: 36px; 
            font-weight: 700; 
            color: #10B981;
        """)
        count_layout.addWidget(self._rep_label)
        top_layout.addLayout(count_layout)
        
        top_layout.addStretch()
        
        # 状态
        state_layout = QVBoxLayout()
        state_layout.setSpacing(2)
        state_title = QLabel("当前状态")
        state_title.setStyleSheet("font-size: 12px; color: #64748B;")
        state_layout.addWidget(state_title)
        
        self._state_label = QLabel("站立")
        self._state_label.setStyleSheet("font-size: 20px; font-weight: 600; color: #10B981;")
        state_layout.addWidget(self._state_label)
        top_layout.addLayout(state_layout)
        
        layout.addWidget(top_card)
        
        # ===== 角度卡片组（紧凑）=====
        angles_card = QFrame()
        angles_card.setProperty("cssClass", "card")
        angles_layout = QVBoxLayout(angles_card)
        angles_layout.setContentsMargins(12, 8, 12, 8)
        angles_layout.setSpacing(6)
        
        angles_title = QLabel("膝关节角度")
        angles_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #334155;")
        angles_layout.addWidget(angles_title)
        
        self._left_angle_card = AngleCard("左膝")
        angles_layout.addWidget(self._left_angle_card)
        
        self._right_angle_card = AngleCard("右膝")
        angles_layout.addWidget(self._right_angle_card)
        
        self._avg_angle_card = AngleCard("平均")
        angles_layout.addWidget(self._avg_angle_card)
        
        layout.addWidget(angles_card)
        
        # ===== 帧统计（一行）=====
        frames_card = QFrame()
        frames_card.setProperty("cssClass", "card")
        frames_layout = QHBoxLayout(frames_card)
        frames_layout.setContentsMargins(16, 8, 16, 8)
        
        # 总帧数
        frames_left = QVBoxLayout()
        frames_left.setSpacing(2)
        frames_title1 = QLabel("总帧数")
        frames_title1.setStyleSheet("font-size: 11px; color: #64748B;")
        frames_left.addWidget(frames_title1)
        self._frames_label = QLabel("0")
        self._frames_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #334155;")
        frames_left.addWidget(self._frames_label)
        frames_layout.addLayout(frames_left)
        
        frames_layout.addStretch()
        
        # 检测帧数
        frames_right = QVBoxLayout()
        frames_right.setSpacing(2)
        frames_title2 = QLabel("检测帧数")
        frames_title2.setStyleSheet("font-size: 11px; color: #64748B;")
        frames_right.addWidget(frames_title2)
        self._pose_label = QLabel("0")
        self._pose_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #334155;")
        frames_right.addWidget(self._pose_label)
        frames_layout.addLayout(frames_right)
        
        layout.addWidget(frames_card)
    
    def update_metrics(self, metrics: SquatMetrics):
        """
        更新指标显示
        
        Args:
            metrics: 深蹲指标
        """
        # 更新计数
        self._rep_label.setText(str(metrics.rep_count))
        
        # 更新状态
        if metrics.state == PoseState.STANDING:
            self._state_label.setText("站立")
            self._state_label.setStyleSheet("font-size: 20px; font-weight: 600; color: #10B981;")
        else:
            self._state_label.setText("下蹲")
            self._state_label.setStyleSheet("font-size: 20px; font-weight: 600; color: #F59E0B;")
        
        # 更新角度
        self._left_angle_card.set_angle(metrics.left_knee_angle)
        self._right_angle_card.set_angle(metrics.right_knee_angle)
        self._avg_angle_card.set_angle(metrics.avg_knee_angle)
    
    def update_frame_stats(self, frame_count: int, pose_count: int):
        """更新帧统计"""
        self._frames_label.setText(str(frame_count))
        self._pose_label.setText(str(pose_count))
    
    def reset(self):
        """重置所有显示"""
        self._rep_label.setText("0")
        self._state_label.setText("站立")
        self._state_label.setStyleSheet("font-size: 20px; font-weight: 600; color: #10B981;")
        self._left_angle_card.set_angle(0)
        self._right_angle_card.set_angle(0)
        self._avg_angle_card.set_angle(0)
        self._frames_label.setText("0")
        self._pose_label.setText("0")
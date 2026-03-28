"""
发光卡片组件

带霓虹发光效果的卡片容器组件。
"""

from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QGradient, QLinearGradient
from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect


class GlowCard(QFrame):
    """
    发光卡片组件

    特性:
    - 顶部边框霓虹发光
    - 支持绿色/蓝色/橙色变色
    - 悬浮时增强发光效果
    """

    def __init__(
        self,
        color: str = "#22C55E",
        glow_position: str = "top",
        parent=None
    ):
        super().__init__(parent)

        self._glow_color = QColor(color)
        self._glow_position = glow_position
        self._glow_intensity = 0.8
        self._hovered = False

        self._setup_style()
        self._setup_shadow()

    def _setup_style(self):
        """设置基础样式"""
        self.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 16px;
                border: 1px solid #27272A;
            }
            QFrame:hover {
                border-color: #3F3F46;
            }
        """)

    def _setup_shadow(self):
        """设置阴影效果"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(self._glow_color)
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def setColor(self, color: str):
        """设置发光颜色"""
        self._glow_color = QColor(color)
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setColor(self._glow_color)
        self.update()

    def setGlowIntensity(self, intensity: float):
        """设置发光强度"""
        self._glow_intensity = max(0, min(1, intensity))
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setBlurRadius(int(20 * intensity))
        self.update()

    def enterEvent(self, event):
        """鼠标进入"""
        self._hovered = True
        self.setGlowIntensity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._hovered = False
        self.setGlowIntensity(0.8)
        super().leaveEvent(event)

    def paintEvent(self, event):
        """绘制发光边框"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制顶部发光边框
        if self._glow_intensity > 0:
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, self._glow_color.lighter(100))
            gradient.setColorAt(0.5, self._glow_color)
            gradient.setColorAt(1, self._glow_color.lighter(100))

            pen = QPen()
            pen.setWidth(2)
            pen.setColor(self._glow_color)
            pen.setColor(gradient)
            painter.setPen(pen)

            # 绘制顶部圆弧
            path = QPainterPath()
            path.moveTo(16, 0)
            path.lineTo(self.width() - 16, 0)
            path.arcTo(self.width() - 16, 0, 32, 32, -90, 90)
            path.lineTo(16, 0)

            painter.fillPath(path, self._glow_color)
            painter.fillRect(16, 0, self.width() - 32, 2, self._glow_color)


class StatCard(QFrame):
    """
    统计数据发光卡片

    用于显示计数、统计数据的大号卡片。
    """

    def __init__(
        self,
        title: str = "",
        value: str = "0",
        unit: str = "",
        color: str = "#22C55E",
        parent=None
    ):
        super().__init__(parent)

        self._title = title
        self._value = value
        self._unit = unit
        self._glow_color = QColor(color)

        self._setup_ui()
        self._setup_shadow()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 16px;
                border: 1px solid #27272A;
            }
        """)

        # 顶部发光条
        self._top_bar = QFrame(self)
        self._top_bar.setFixedHeight(3)
        self._top_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.3 {self._glow_color.name()},
                    stop:0.7 {self._glow_color.name()}, stop:1 transparent);
                border-radius: 2px;
            }}
        """)

        from PyQt6.QtWidgets import QVBoxLayout, QLabel
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 20)
        layout.setSpacing(4)

        # 标题
        title_label = QLabel(self._title)
        title_label.setStyleSheet("color: #A1A1AA; font-size: 13px; font-weight: 500; background: transparent; border: none;")
        layout.addWidget(title_label)

        # 值
        self._value_label = QLabel(self._value)
        self._value_label.setStyleSheet(f"""
            color: {self._glow_color.name()};
            font-size: 48px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._value_label)

        # 单位
        if self._unit:
            unit_label = QLabel(self._unit)
            unit_label.setStyleSheet("color: #71717A; font-size: 14px; background: transparent; border: none;")
            layout.addWidget(unit_label)

        layout.addStretch()

    def _setup_shadow(self):
        """设置阴影"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(self._glow_color)
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def setValue(self, value: str):
        """设置显示值"""
        self._value = value
        self._value_label.setText(value)

    def setColor(self, color: str):
        """设置颜色"""
        self._glow_color = QColor(color)
        self._value_label.setStyleSheet(f"""
            color: {self._glow_color.name()};
            font-size: 48px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setColor(self._glow_color)


class AngleCardGlow(QFrame):
    """
    角度显示发光卡片

    用于实时显示关节角度，带进度条和颜色变化。
    """

    def __init__(
        self,
        title: str = "角度",
        color: str = "#22C55E",
        parent=None
    ):
        super().__init__(parent)

        self._title = title
        self._glow_color = QColor(color)
        self._current_angle = 0

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet("""
            QFrame {
                background-color: #1E1E22;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)

        from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QProgressBar

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # 左侧：标题和数值
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)

        title_label = QLabel(self._title)
        title_label.setStyleSheet("color: #71717A; font-size: 12px; background: transparent; border: none;")
        left_layout.addWidget(title_label)

        self._angle_label = QLabel("0°")
        self._angle_label.setStyleSheet(f"""
            color: {self._glow_color.name()};
            font-size: 24px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        left_layout.addWidget(self._angle_label)

        main_layout.addLayout(left_layout)

        # 右侧：进度条
        self._progress = QProgressBar()
        self._progress.setRange(0, 180)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #27272A;
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {self._glow_color.name()};
                border-radius: 4px;
            }}
        """)
        main_layout.addWidget(self._progress, stretch=1)

    def setAngle(self, angle: float):
        """设置角度值并更新颜色"""
        self._current_angle = angle
        self._angle_label.setText(f"{angle:.0f}°")
        self._progress.setValue(int(angle))

        # 根据角度更新颜色
        if angle < 90:
            color = "#F97316"  # 橙色 - 过低
        elif angle < 165:
            color = "#3B82F6"  # 蓝色 - 正常范围
        else:
            color = "#22C55E"  # 绿色 - 伸展

        self._glow_color = QColor(color)
        self._angle_label.setStyleSheet(f"""
            color: {color};
            font-size: 24px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #27272A;
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 4px;
            }}
        """)

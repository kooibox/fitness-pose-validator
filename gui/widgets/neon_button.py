"""
霓虹按钮组件

带发光效果的按钮组件，支持多种颜色变体。
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtProperty, QPoint
from PyQt6.QtGui import QPainter, QColor, QGradient, QLinearGradient, QRadialGradient
from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect


class NeonButton(QPushButton):
    """
    霓虹发光按钮

    支持的颜色变体:
    - green: 深蹲模式
    - blue: 开合跳模式
    - orange: 警告
    - red: 危险
    """

    def __init__(self, text: str = "", color: str = "green", parent=None):
        super().__init__(parent)

        self._neon_color = color
        self._glow_intensity = 0.5
        self._is_animating = False

        self.setText(text)
        self._setup_style()
        self._setup_animation()

    def _setup_style(self):
        """设置基础样式"""
        colors = {
            "green": ("#22C55E", "#16A34A", "rgba(34, 197, 94, 0.5)"),
            "blue": ("#3B82F6", "#2563EB", "rgba(59, 130, 246, 0.5)"),
            "orange": ("#F97316", "#EA580C", "rgba(249, 115, 22, 0.5)"),
            "red": ("#EF4444", "#DC2626", "rgba(239, 68, 68, 0.5)"),
        }

        primary, secondary, glow = colors.get(self._neon_color, colors["green"])

        self.setStyleSheet(f"""
            QPushButton {{
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                border: 1px solid {primary};
                border-radius: 12px;
                padding: 14px 28px;
                font-weight: 600;
                font-size: 15px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: linear-gradient(135deg, {secondary} 0%, {primary} 100%);
                border: 2px solid {primary};
            }}
            QPushButton:pressed {{
                background: linear-gradient(135deg, {secondary} 0%, #15803D 100%);
            }}
            QPushButton:disabled {{
                background: #27272A;
                color: #71717A;
                border-color: #3F3F46;
            }}
        """)

        # 设置发光阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(primary))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def _setup_animation(self):
        """设置动画"""
        self._glow_animation = QPropertyAnimation(self, "glowIntensity")
        self._glow_animation.setDuration(200)
        self._glow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def setColor(self, color: str):
        """动态更改颜色"""
        self._neon_color = color
        self._setup_style()

    def getGlowIntensity(self) -> float:
        return self._glow_intensity

    def setGlowIntensity(self, intensity: float):
        self._glow_intensity = max(0, min(1, intensity))
        self.update()

    glowIntensity = pyqtProperty(float, getGlowIntensity, setGlowIntensity)

    def enterEvent(self, event):
        """鼠标进入动画"""
        self._glow_animation.stop()
        self._glow_animation.setStartValue(self._glow_intensity)
        self._glow_animation.setEndValue(1.0)
        self._glow_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开动画"""
        self._glow_animation.stop()
        self._glow_animation.setStartValue(self._glow_intensity)
        self._glow_animation.setEndValue(0.5)
        self._glow_animation.start()
        super().leaveEvent(event)


class IconNeonButton(QPushButton):
    """
    图标霓虹按钮 (圆形)

    用于控制栏的图标按钮，带悬浮发光效果。
    """

    def __init__(self, icon: str = "", color: str = "green", parent=None):
        super().__init__(parent)

        self._neon_color = color
        self._icon = icon

        self.setText(icon)
        self._setup_style()

    def _setup_style(self):
        """设置样式"""
        colors = {
            "green": ("#22C55E", "rgba(34, 197, 94, 0.3)"),
            "blue": ("#3B82F6", "rgba(59, 130, 246, 0.3)"),
            "orange": ("#F97316", "rgba(249, 115, 22, 0.3)"),
            "red": ("#EF4444", "rgba(239, 68, 68, 0.3)"),
        }

        primary, glow = colors.get(self._neon_color, colors["green"])

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #A1A1AA;
                border: 1px solid #3F3F46;
                border-radius: 22px;
                padding: 10px;
                min-width: 44px;
                max-width: 44px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #252529;
                color: {primary};
                border-color: {primary};
            }}
            QPushButton:pressed {{
                background-color: #1E1E22;
            }}
            QPushButton:disabled {{
                color: #52525B;
                border-color: #27272A;
            }}
        """)

    def setColor(self, color: str):
        """动态更改颜色"""
        self._neon_color = color
        self._setup_style()

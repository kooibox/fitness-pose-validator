"""
动画效果模块

提供微交互动画效果。
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtProperty, QParallelAnimationGroup, QSequentialAnimationGroup
from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtGui import QFont, QPalette, QColor


class CountAnimation:
    """数字跳动动画"""

    @staticmethod
    def animate_count_change(label: QLabel, start_val: int, end_val: int, duration: int = 300):
        """
        数字变化时的跳动动画

        Args:
            label: 要动画的标签
            start_val: 起始值
            end_val: 结束值
            duration: 动画时长(ms)
        """
        anim = QPropertyAnimation(label, "countValue")
        anim.setDuration(duration)
        anim.setStartValue(start_val)
        anim.setEndValue(end_val)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        return anim


class PulseAnimation:
    """脉冲闪烁动画"""

    def __init__(self, widget: QWidget, color: str = "#22C55E"):
        self.widget = widget
        self.color = QColor(color)
        self._opacity = 1.0

        self._anim = QPropertyAnimation(self, "pulseOpacity")
        self._anim.setDuration(800)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.4)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)  # 无限循环

    def start(self):
        """开始脉冲动画"""
        self._anim.start()

    def stop(self):
        """停止脉冲动画"""
        self._anim.stop()
        self.widget.setStyleSheet(f"opacity: 1.0;")

    def getPulseOpacity(self) -> float:
        return self._opacity

    def setPulseOpacity(self, val: float):
        self._opacity = val
        # 通过透明度实现脉冲效果
        self.widget.setStyleSheet(f"color: {self.color.name()}; opacity: {val};")

    pulseOpacity = pyqtProperty(float, getPulseOpacity, setPulseOpacity)


class BounceAnimation:
    """弹跳动画"""

    @staticmethod
    def bounce(widget: QWidget, scale: float = 1.1, duration: int = 200):
        """
        弹跳缩放动画

        Args:
            widget: 要动画的控件
            scale: 缩放比例
            duration: 动画时长(ms)
        """
        # 放大
        up_anim = QPropertyAnimation(widget, "scale")
        up_anim.setDuration(duration // 2)
        up_anim.setStartValue(1.0)
        up_anim.setEndValue(scale)
        up_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        # 缩小回原
        down_anim = QPropertyAnimation(widget, "scale")
        down_anim.setDuration(duration // 2)
        down_anim.setStartValue(scale)
        down_anim.setEndValue(1.0)
        down_anim.setEasingCurve(QEasingCurve.Type.InQuad)

        # 顺序播放
        group = QSequentialAnimationGroup()
        group.addAnimation(up_anim)
        group.addAnimation(down_anim)
        group.start()

        return group


class SlideInAnimation:
    """滑入动画"""

    @staticmethod
    def slide_in(widget: QWidget, direction: str = "left", duration: int = 300):
        """
        滑入动画

        Args:
            widget: 要动画的控件
            direction: 方向 ("left", "right", "top", "bottom")
            duration: 动画时长(ms)
        """
        anim = QPropertyAnimation(widget, "geometry")

        start_rect = widget.geometry()
        end_rect = widget.geometry()

        if direction == "left":
            start_rect.moveLeft(-start_rect.width())
        elif direction == "right":
            start_rect.moveLeft(widget.parent().width())
        elif direction == "top":
            start_rect.moveTop(-start_rect.height())
        elif direction == "bottom":
            start_rect.moveTop(widget.parent().height())

        anim.setDuration(duration)
        anim.setStartValue(start_rect)
        anim.setEndValue(end_rect)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

        return anim


class GlowPulseAnimation:
    """发光脉冲动画（用于霓虹效果）"""

    def __init__(self, widget: QWidget, base_color: str = "#22C55E"):
        self.widget = widget
        self.base_color = QColor(base_color)
        self._glow_radius = 20

        self._anim = QPropertyAnimation(self, "glowRadius")
        self._anim.setDuration(1000)
        self._anim.setStartValue(15)
        self._anim.setEndValue(30)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)

    def start(self):
        self._anim.start()

    def stop(self):
        self._anim.stop()

    def getGlowRadius(self) -> int:
        return self._glow_radius

    def setGlowRadius(self, val: int):
        self._glow_radius = val
        # 这里可以通过更新样式表或使用 QGraphicsEffect 实现发光
        # 简化实现：使用阴影效果
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(val)
        shadow.setColor(self.base_color)
        shadow.setOffset(0, 0)
        self.widget.setGraphicsEffect(shadow)

    glowRadius = pyqtProperty(int, getGlowRadius, setGlowRadius)


class ShakeAnimation:
    """摇晃动画（用于错误提示）"""

    @staticmethod
    def shake(widget: QWidget, intensity: int = 10, duration: int = 300):
        """
        摇晃动画

        Args:
            widget: 要动画的控件
            intensity: 摇晃强度
            duration: 动画时长(ms)
        """
        anim = QPropertyAnimation(widget, "pos")

        start_pos = widget.pos()
        anim.setDuration(duration)
        anim.setKeyValueAt(0.0, start_pos)
        anim.setKeyValueAt(0.25, start_pos + (intensity, 0))
        anim.setKeyValueAt(0.5, start_pos + (0, -intensity // 2))
        anim.setKeyValueAt(0.75, start_pos + (-intensity, 0))
        anim.setKeyValueAt(1.0, start_pos)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.start()

        return anim


class FadeAnimation:
    """淡入淡出动画"""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300):
        """淡入动画"""
        anim = QPropertyAnimation(widget, "windowOpacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        return anim

    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300):
        """淡出动画"""
        anim = QPropertyAnimation(widget, "windowOpacity")
        anim.setDuration(duration)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.start()
        return anim

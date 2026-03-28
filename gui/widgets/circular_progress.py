"""
环形进度组件:

用于显示状态的环形进度指示器，带霓虹发光效果。
"""

import math
from PyQt6.QtCore import Qt, QRectF, QTimer, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QLinearGradient
from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect


class CircularProgress(QWidget):
    """
    环形进度指示器

    特性:
    - 霓虹发光效果
    - 支持百分比显示
    - 可配置颜色和大小
    - 动画过渡效果
    """

    def __init__(
        self,
        value: float = 0,
        max_value: float = 100,
        size: int = 120,
        line_width: int = 8,
        color: str = "#22C55E",
        parent=None
    ):
        super().__init__(parent)

        self._value = value
        self._max_value = max_value
        self._size = size
        self._line_width = line_width
        self._color = QColor(color)
        self._background_color = QColor("#27272A")
        self._glow_intensity = 0.6
        self._animated_value = value

        self._target_value = value

        # 设置最小尺寸
        self.setMinimumSize(size, size)
        self.setMaximumSize(size, size)

        # 动画定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_step)

    def _animate_step(self):
        """动画步骤"""
        diff = self._target_value - self._animated_value
        if abs(diff) < 0.5:
            self._animated_value = self._target_value
            self._timer.stop()
        else:
            self._animated_value += diff * 0.15
        self.update()

    def setValue(self, value: float, animate: bool = True):
        """设置进度值"""
        self._target_value = max(0, min(self._max_value, value))

        if animate:
            if not self._timer.isActive():
                self._timer.start(16)  # ~60fps
        else:
            self._animated_value = self._target_value
            self.update()

    def getValue(self) -> float:
        """获取当前值"""
        return self._value

    @pyqtProperty(float)
    def animatedValue(self) -> float:
        return self._animated_value

    @animatedValue.setter
    def animatedValue(self, val: float):
        self._animated_value = val
        self.update()

    def setColor(self, color: str):
        """设置进度条颜色"""
        self._color = QColor(color)
        self.update()

    def setGlowIntensity(self, intensity: float):
        """设置发光强度 (0-1)"""
        self._glow_intensity = max(0, min(1, intensity))
        self.update()

    def paintEvent(self, event):
        """绘制环形进度"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        # 获取绘制区域
        rect = QRectF(self.rect())
        rect.adjust(self._line_width / 2, self._line_width / 2, -self._line_width / 2, -self._line_width / 2)

        # 计算进度
        percentage = self._animated_value / self._max_value if self._max_value > 0 else 0
        span_angle = int(-percentage * 360 * 16)  # 转换为 Qt 的 1/16 度

        # 绘制背景圆环
        bg_pen = QPen()
        bg_pen.setColor(self._background_color)
        bg_pen.setWidth(self._line_width)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)

        painter.drawArc(rect, 0, -360 * 16)  # 完整圆

        # 绘制发光效果
        if self._glow_intensity > 0 and percentage > 0:
            glow_pen = QPen()
            glow_color = self._color
            glow_color.setAlphaF(self._glow_intensity * 0.3)
            glow_pen.setColor(glow_color)
            glow_pen.setWidth(self._line_width + 8)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(rect, 90 * 16, span_angle)

        # 绘制进度圆弧
        progress_pen = QPen()
        progress_pen.setColor(self._color)
        progress_pen.setWidth(self._line_width)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)

        painter.drawArc(rect, 90 * 16, span_angle)  # 从顶部开始

        # 绘制中心文字
        painter.setPen(QPen(self._color))

        # 百分比文字
        font = QFont("Inter", int(self._size / 4), QFont.Weight.Bold)
        painter.setFont(font)
        percent_text = f"{int(percentage * 100)}%"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, percent_text)


class StateIndicator(QWidget):
    """
    状态指示器组件

    显示当前运动状态的环形指示器（站立/下蹲 或 展开/合拢）
    """

    def __init__(
        self,
        state: str = "stand",
        label: str = "站立",
        size: int = 100,
        color: str = "#22C55E",
        parent=None
    ):
        super().__init__(parent)

        self._state = state
        self._label = label
        self._size = size
        self._color = QColor(color)
        self._pulse_opacity = 0.3
        self._pulse_direction = 1

        self.setMinimumSize(size, size)
        self.setMaximumSize(size, size)

        # 脉冲动画定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse_step)

    def _pulse_step(self):
        """脉冲动画步骤"""
        self._pulse_opacity += 0.03 * self._pulse_direction
        if self._pulse_opacity >= 1.0:
            self._pulse_opacity = 1.0
            self._pulse_direction = -1
        elif self._pulse_opacity <= 0.3:
            self._pulse_opacity = 0.3
            self._pulse_direction = 1
        self.update()

    def setState(self, state: str, label: str = None, color: str = None):
        """设置状态"""
        self._state = state
        if label is not None:
            self._label = label
        if color is not None:
            self._color = QColor(color)

        self.update()

    def startPulse(self):
        """开始脉冲动画"""
        if not self._timer.isActive():
            self._timer.start(30)  # ~33fps

    def stopPulse(self):
        """停止脉冲动画"""
        self._timer.stop()
        self._pulse_opacity = 0.3
        self.update()

    def paintEvent(self, event):
        """绘制状态指示器"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect())
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2 - 10

        # 绘制发光圆环
        glow_radius = radius + 5
        glow_color = QColor(self._color)
        glow_color.setAlphaF(self._pulse_opacity * 0.3)

        glow_pen = QPen()
        glow_pen.setColor(glow_color)
        glow_pen.setWidth(10)
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.drawEllipse(center, glow_radius, glow_radius)

        # 绘制主圆环
        main_pen = QPen()
        main_pen.setColor(self._color)
        main_pen.setWidth(4)
        painter.setPen(main_pen)
        painter.drawEllipse(center, radius, radius)

        # 绘制状态点
        dot_radius = 8
        dot_color = self._color
        painter.setBrush(dot_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, dot_radius, dot_radius)

        # 绘制标签文字
        painter.setPen(QPen(self._color))
        font = QFont("Inter", 12, QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(
            QRectF(center.x() - 40, center.y() + radius + 15, 80, 30),
            Qt.AlignmentFlag.AlignCenter,
            self._label
        )
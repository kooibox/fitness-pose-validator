"""
视频显示控件

自定义 QLabel 用于显示视频帧。
"""

import cv2
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy


class VideoWidget(QLabel):
    """
    视频显示控件
    
    将 OpenCV 帧转换为 QPixmap 并显示。
    支持等比缩放和全屏切换。
    """
    
    # 信号
    clicked = pyqtSignal()  # 点击信号（用于全屏切换）
    
    def __init__(self, parent=None):
        """初始化视频显示控件"""
        super().__init__(parent)
        
        # 基本设置
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(480, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 样式
        self.setStyleSheet("""
            QLabel {
                background-color: #1E293B;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        
        # 占位文本
        self.setText("🎥 点击开始训练")
        self.setStyleSheet(self.styleSheet() + """
            QLabel {
                color: #94A3B8;
                font-size: 18px;
            }
        """)
        
        # 状态
        self._current_pixmap: QPixmap = None
        self._is_fullscreen = False
    
    def update_frame(self, frame: np.ndarray):
        """
        更新视频帧显示
        
        Args:
            frame: BGR 格式的视频帧 (numpy array)
        """
        if frame is None:
            return
        
        # 转换颜色空间 BGR -> RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 获取帧尺寸
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # 创建 QImage
        q_img = QImage(
            rgb_frame.data, 
            w, h, 
            bytes_per_line, 
            QImage.Format.Format_RGB888
        )
        
        # 转换为 QPixmap 并缩放
        pixmap = QPixmap.fromImage(q_img)
        
        # 等比缩放到控件大小
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
        self._current_pixmap = pixmap
    
    def show_placeholder(self, message: str = "🎥 点击开始训练"):
        """显示占位文本"""
        self.clear()
        self.setText(message)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)
        self.clicked.emit()
    
    def resizeEvent(self, event):
        """窗口大小改变时重新缩放"""
        super().resizeEvent(event)
        if self._current_pixmap:
            scaled_pixmap = self._current_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)

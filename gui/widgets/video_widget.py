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
    """视频显示控件"""
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(480, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.setStyleSheet("""
            QLabel {
                background-color: #1E293B;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        
        self.setText("🎥  点击开始训练")
        self.setStyleSheet(self.styleSheet() + """
            QLabel {
                color: #94A3B8;
                font-size: 24px;
            }
        """)
        
        self._current_pixmap: QPixmap = None
        self._current_frame: np.ndarray = None
        self._is_fullscreen = False
    
    @property
    def current_frame(self) -> np.ndarray:
        """获取当前显示的帧"""
        return self._current_frame
    
    def update_frame(self, frame: np.ndarray):
        if frame is None:
            return
        
        self._current_frame = frame.copy()  # 保存当前帧
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        q_img = QImage(
            rgb_frame.data, 
            w, h, 
            bytes_per_line, 
            QImage.Format.Format_RGB888
        )
        
        pixmap = QPixmap.fromImage(q_img)
        
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
        self._current_pixmap = pixmap
    
    def show_placeholder(self, message: str = "🎥 点击开始训练"):
        self.clear()
        self.setText(message)
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_pixmap:
            scaled_pixmap = self._current_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)

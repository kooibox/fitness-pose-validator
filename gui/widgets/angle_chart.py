"""
角度图表控件

使用 Matplotlib 绘制实时角度变化曲线。
"""

from collections import deque
from typing import Optional

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import QWidget, QVBoxLayout


class AngleChart(QWidget):
    """
    角度图表
    
    实时显示膝关节角度变化曲线。
    """
    
    # 最大显示点数
    MAX_POINTS = 100
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据缓冲区
        self._left_angles = deque(maxlen=self.MAX_POINTS)
        self._right_angles = deque(maxlen=self.MAX_POINTS)
        self._avg_angles = deque(maxlen=self.MAX_POINTS)
        
        # 创建 Matplotlib 图形 - 调整尺寸适应容器
        self._figure = Figure(figsize=(5, 2.5), dpi=100, facecolor='#FFFFFF')
        self._canvas = FigureCanvas(self._figure)
        self._ax = self._figure.add_subplot(111)
        
        # 配置图表样式
        self._setup_chart_style()
        
        # 初始化线条 - 使用英文标签
        self._left_line, = self._ax.plot([], [], 'b-', label='Left', alpha=0.7, linewidth=1.5)
        self._right_line, = self._ax.plot([], [], 'g-', label='Right', alpha=0.7, linewidth=1.5)
        self._avg_line, = self._ax.plot([], [], 'r-', label='Avg', linewidth=2)
        
        # 添加阈值线 - 使用英文标签
        self._ax.axhline(y=90, color='#F59E0B', linestyle='--', alpha=0.5, label='Squat')
        self._ax.axhline(y=165, color='#10B981', linestyle='--', alpha=0.5, label='Stand')
        
        # 图例 - 放在图表下方
        self._ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), fontsize=7, framealpha=0.9, ncol=5)
        
        # 布局 - 为底部图例留出空间
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._canvas)
        
        # 调整图形布局
        self._figure.tight_layout(rect=[0, 0.1, 1, 1])
        
        # 样式
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
            }
        """)
    
    def _setup_chart_style(self):
        """配置图表样式"""
        # 背景色
        self._ax.set_facecolor('#F8FAFC')
        self._figure.patch.set_facecolor('#FFFFFF')
        
        # 网格
        self._ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # 坐标轴 - 使用英文
        self._ax.set_ylim(0, 180)
        self._ax.set_ylabel('Angle (deg)', fontsize=9, color='#475569')
        self._ax.set_xlabel('Frame', fontsize=9, color='#475569')
        
        # 刻度
        self._ax.tick_params(axis='both', labelsize=8, colors='#64748B')
        
        # 边框
        for spine in self._ax.spines.values():
            spine.set_color('#E2E8F0')
    
    def update_data(self, left_angle: float, right_angle: float, avg_angle: float):
        """
        更新角度数据
        
        Args:
            left_angle: 左膝角度
            right_angle: 右膝角度
            avg_angle: 平均角度
        """
        # 添加数据
        self._left_angles.append(left_angle)
        self._right_angles.append(right_angle)
        self._avg_angles.append(avg_angle)
        
        # 更新线条
        x = list(range(len(self._avg_angles)))
        self._left_line.set_data(x, list(self._left_angles))
        self._right_line.set_data(x, list(self._right_angles))
        self._avg_line.set_data(x, list(self._avg_angles))
        
        # 调整 x 轴范围
        if len(x) > 0:
            self._ax.set_xlim(max(0, x[0]), x[-1] + 1)
        
        # 重绘
        self._canvas.draw_idle()
    
    def clear(self):
        """清空数据"""
        self._left_angles.clear()
        self._right_angles.clear()
        self._avg_angles.clear()
        
        self._left_line.set_data([], [])
        self._right_line.set_data([], [])
        self._avg_line.set_data([], [])
        
        self._ax.set_xlim(0, 1)
        self._canvas.draw_idle()

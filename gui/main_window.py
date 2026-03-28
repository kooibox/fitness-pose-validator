"""
主窗口

Fitness Pose Validator 的主窗口，管理页面切换和全局状态。
"""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QStatusBar, 
    QTabWidget, QWidget
)

from gui.pages.training_page import TrainingPage
from gui.pages.history_page import HistoryPage
from gui.pages.settings_page import SettingsPage
from gui.resources.styles.dark_theme import apply_dark_theme


class MainWindow(QMainWindow):
    """
    主窗口
    
    包含导航栏和页面切换逻辑。
    """
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 窗口设置
        self.setWindowTitle("Fitness Pose Validator")
        self.setMinimumSize(QSize(1200, 800))
        self.resize(1400, 900)
        
        # 应用深色霓虹主题
        apply_dark_theme(self)
        
        # 初始化 UI
        self._init_ui()
        
        # 创建状态栏
        self._create_status_bar()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建标签页控件
        self._tab_widget = QTabWidget()
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 设置标签页样式
        self._tab_widget.setStyleSheet(self._tab_widget.styleSheet() + """
            QTabWidget::pane {
                border: none;
                background-color: #F8FAFC;
            }
        """)
        
        # 创建页面
        self._training_page = TrainingPage()
        self._history_page = HistoryPage()
        self._settings_page = SettingsPage()
        
        # 添加标签页
        self._tab_widget.addTab(self._training_page, "🏋️ 训练")
        self._tab_widget.addTab(self._history_page, "📊 历史记录")
        self._tab_widget.addTab(self._settings_page, "⚙️ 设置")
        
        main_layout.addWidget(self._tab_widget)
        
        # 连接设置改变信号
        self._settings_page.settings_changed.connect(self._on_settings_changed)
    
    def _create_status_bar(self):
        """创建状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 应用名称和版本
        app_info = QLabel("Fitness Pose Validator v2.0.0")
        app_info.setStyleSheet("color: #64748B; margin-left: 8px;")
        status_bar.addWidget(app_info)
        
        # 弹性空间
        status_bar.addWidget(QLabel(""), 1)
        
        # 版权信息
        copyright_label = QLabel("© 2026 OhMyOpenCode")
        copyright_label.setStyleSheet("color: #94A3B8; margin-right: 8px;")
        status_bar.addWidget(copyright_label)
    
    def _on_settings_changed(self, settings: dict):
        """设置改变回调"""
        # 应用设置到训练页面
        self._training_page.apply_settings(settings)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 检查训练页面是否正在运行
        if hasattr(self._training_page, '_state'):
            if self._training_page._state != self._training_page.State.IDLE:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "训练正在进行中，确定要退出吗？\n当前数据将被保存。",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
        
        event.accept()
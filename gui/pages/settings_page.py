"""
设置页面

应用程序配置界面。
"""

import json
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSlider, QSpinBox,
    QVBoxLayout, QWidget
)

from src.config import Config


class SettingsPage(QWidget):
    """
    设置页面
    
    包含摄像头、检测参数和界面配置。
    """
    
    # 配置改变信号
    settings_changed = pyqtSignal(dict)
    
    # 配置文件路径
    CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "gui_settings.json"
    
    def __init__(self, parent=None):
        """初始化设置页面"""
        super().__init__(parent)
        
        # 加载配置
        self._settings = self._load_settings()
        
        # 初始化 UI
        self._init_ui()
        
        # 应用配置到 UI
        self._apply_settings_to_ui()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # 标题
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("⚙️ 设置")
        title.setProperty("cssClass", "title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 重置按钮
        reset_btn = QPushButton("🔄 恢复默认")
        reset_btn.clicked.connect(self._reset_to_default)
        header_layout.addWidget(reset_btn)
        
        main_layout.addWidget(header)
        
        # 滚动区域内容
        content_layout = QVBoxLayout()
        content_layout.setSpacing(16)
        
        # 摄像头设置
        camera_group = self._create_camera_group()
        content_layout.addWidget(camera_group)
        
        # 检测参数
        detection_group = self._create_detection_group()
        content_layout.addWidget(detection_group)
        
        # 界面设置
        ui_group = self._create_ui_group()
        content_layout.addWidget(ui_group)
        
        # 数据设置
        data_group = self._create_data_group()
        content_layout.addWidget(data_group)
        
        # 服务器设置
        server_group = self._create_server_group()
        content_layout.addWidget(server_group)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
        
        # 保存按钮
        save_btn = QPushButton("💾 保存设置")
        save_btn.setProperty("cssClass", "primary")
        save_btn.clicked.connect(self._save_settings)
        main_layout.addWidget(save_btn)
    
    def _create_camera_group(self) -> QGroupBox:
        """创建摄像头设置组"""
        group = QGroupBox("摄像头设置")
        layout = QVBoxLayout(group)
        
        # 摄像头索引
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("摄像头索引:"))
        row1.addStretch()
        self._camera_index = QSpinBox()
        self._camera_index.setRange(0, 10)
        self._camera_index.setValue(Config.CAMERA_INDEX)
        row1.addWidget(self._camera_index)
        layout.addLayout(row1)
        
        # 分辨率
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("分辨率:"))
        row2.addStretch()
        self._resolution = QComboBox()
        self._resolution.addItems([
            "640x480",
            "1280x720",
            "1920x1080",
        ])
        self._resolution.setCurrentText(f"{Config.CAMERA_RESOLUTION[0]}x{Config.CAMERA_RESOLUTION[1]}")
        row2.addWidget(self._resolution)
        layout.addLayout(row2)
        
        # 帧率
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("目标帧率:"))
        row3.addStretch()
        self._fps = QSpinBox()
        self._fps.setRange(15, 60)
        self._fps.setValue(Config.CAMERA_FPS)
        row3.addWidget(self._fps)
        layout.addLayout(row3)
        
        # 旋转帧
        row4 = QHBoxLayout()
        self._rotate_frame = QCheckBox("旋转帧 90° (竖屏摄像头)")
        self._rotate_frame.setChecked(True)
        row4.addWidget(self._rotate_frame)
        layout.addLayout(row4)
        
        return group
    
    def _create_detection_group(self) -> QGroupBox:
        """创建检测参数组"""
        group = QGroupBox("检测参数")
        layout = QVBoxLayout(group)
        
        # 站立阈值
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("站立阈值:"))
        row1.addStretch()
        self._standing_threshold = QSlider(Qt.Orientation.Horizontal)
        self._standing_threshold.setRange(120, 180)
        self._standing_threshold.setValue(int(Config.STANDING_ANGLE_THRESHOLD))
        self._standing_threshold.setFixedWidth(200)
        row1.addWidget(self._standing_threshold)
        self._standing_threshold_label = QLabel(f"{int(Config.STANDING_ANGLE_THRESHOLD)}°")
        self._standing_threshold_label.setFixedWidth(40)
        row1.addWidget(self._standing_threshold_label)
        self._standing_threshold.valueChanged.connect(
            lambda v: self._standing_threshold_label.setText(f"{v}°")
        )
        layout.addLayout(row1)
        
        # 下蹲阈值
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("下蹲阈值:"))
        row2.addStretch()
        self._squat_threshold = QSlider(Qt.Orientation.Horizontal)
        self._squat_threshold.setRange(45, 120)
        self._squat_threshold.setValue(int(Config.SQUAT_ANGLE_THRESHOLD))
        self._squat_threshold.setFixedWidth(200)
        row2.addWidget(self._squat_threshold)
        self._squat_threshold_label = QLabel(f"{int(Config.SQUAT_ANGLE_THRESHOLD)}°")
        self._squat_threshold_label.setFixedWidth(40)
        row2.addWidget(self._squat_threshold_label)
        self._squat_threshold.valueChanged.connect(
            lambda v: self._squat_threshold_label.setText(f"{v}°")
        )
        layout.addLayout(row2)
        
        # 检测置信度
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("检测置信度:"))
        row3.addStretch()
        self._detection_confidence = QSlider(Qt.Orientation.Horizontal)
        self._detection_confidence.setRange(10, 100)
        self._detection_confidence.setValue(int(Config.POSE_DETECTION_CONFIDENCE * 100))
        self._detection_confidence.setFixedWidth(200)
        row3.addWidget(self._detection_confidence)
        self._detection_confidence_label = QLabel(f"{Config.POSE_DETECTION_CONFIDENCE:.1f}")
        self._detection_confidence_label.setFixedWidth(40)
        row3.addWidget(self._detection_confidence_label)
        self._detection_confidence.valueChanged.connect(
            lambda v: self._detection_confidence_label.setText(f"{v/100:.1f}")
        )
        layout.addLayout(row3)
        
        return group
    
    def _create_ui_group(self) -> QGroupBox:
        """创建界面设置组"""
        group = QGroupBox("界面设置")
        layout = QVBoxLayout(group)
        
        # 显示骨骼
        row1 = QHBoxLayout()
        self._show_skeleton = QCheckBox("显示骨骼连线")
        self._show_skeleton.setChecked(True)
        row1.addWidget(self._show_skeleton)
        layout.addLayout(row1)
        
        # 显示角度
        row2 = QHBoxLayout()
        self._show_angles = QCheckBox("显示角度数值")
        self._show_angles.setChecked(True)
        row2.addWidget(self._show_angles)
        layout.addLayout(row2)
        
        # 显示图表
        row3 = QHBoxLayout()
        self._show_chart = QCheckBox("显示角度曲线图")
        self._show_chart.setChecked(True)
        row3.addWidget(self._show_chart)
        layout.addLayout(row3)
        
        return group
    
    def _create_data_group(self) -> QGroupBox:
        """创建数据设置组"""
        group = QGroupBox("数据设置")
        layout = QVBoxLayout(group)
        
        # 数据库路径
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("数据库路径:"))
        row1.addStretch()
        self._db_path = QLineEdit(str(Config.DATABASE_PATH))
        self._db_path.setFixedWidth(300)
        row1.addWidget(self._db_path)
        layout.addLayout(row1)
        
        # 缓冲区大小
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("缓冲区大小:"))
        row2.addStretch()
        self._buffer_size = QSpinBox()
        self._buffer_size.setRange(10, 1000)
        self._buffer_size.setValue(Config.RECORD_BUFFER_SIZE)
        row2.addWidget(self._buffer_size)
        layout.addLayout(row2)
        
        return group
    
    def _create_server_group(self) -> QGroupBox:
        """创建服务器设置组"""
        group = QGroupBox("☁️ 服务器上传设置")
        layout = QVBoxLayout(group)
        
        # 服务器地址
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("服务器地址:"))
        row1.addStretch()
        self._server_url = QLineEdit()
        self._server_url.setPlaceholderText("http://192.168.1.100:8080/api/v1/sessions/upload")
        self._server_url.setFixedWidth(350)
        row1.addWidget(self._server_url)
        layout.addLayout(row1)
        
        # API密钥
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("API密钥:"))
        row2.addStretch()
        self._api_key = QLineEdit()
        self._api_key.setPlaceholderText("输入服务器API密钥")
        self._api_key.setFixedWidth(350)
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        row2.addWidget(self._api_key)
        layout.addLayout(row2)
        
        # 自动上传选项
        row3 = QHBoxLayout()
        self._auto_upload = QCheckBox("训练结束后自动上传")
        self._auto_upload.setChecked(False)
        row3.addWidget(self._auto_upload)
        layout.addLayout(row3)
        
        # 测试连接按钮
        row4 = QHBoxLayout()
        row4.addStretch()
        test_btn = QPushButton("🔗 测试连接")
        test_btn.clicked.connect(self._test_server_connection)
        row4.addWidget(test_btn)
        layout.addLayout(row4)
        
        return group
    
    def _test_server_connection(self):
        """测试服务器连接"""
        from PyQt6.QtWidgets import QMessageBox
        import urllib.request
        import urllib.error
        
        server_url = self._server_url.text().strip()
        api_key = self._api_key.text().strip()
        
        if not server_url:
            QMessageBox.warning(self, "测试失败", "请输入服务器地址")
            return
        
        try:
            # 发送一个简单的HEAD请求测试连接
            request = urllib.request.Request(
                server_url,
                method="HEAD"
            )
            
            if api_key:
                request.add_header("Authorization", f"Bearer {api_key}")
            
            with urllib.request.urlopen(request, timeout=5) as response:
                QMessageBox.information(self, "连接成功", f"服务器响应: {response.status}")
                
        except urllib.error.URLError as e:
            QMessageBox.warning(self, "连接失败", f"无法连接到服务器:\n{e}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"测试连接时出错:\n{e}")
    
    def _load_settings(self) -> dict:
        """加载设置"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载设置失败: {e}")
        return {}
    
    def _apply_settings_to_ui(self):
        """将设置应用到 UI"""
        if not self._settings:
            return
        
        # 摄像头设置
        if "camera_index" in self._settings:
            self._camera_index.setValue(self._settings["camera_index"])
        if "resolution" in self._settings:
            self._resolution.setCurrentText(self._settings["resolution"])
        if "fps" in self._settings:
            self._fps.setValue(self._settings["fps"])
        if "rotate_frame" in self._settings:
            self._rotate_frame.setChecked(self._settings["rotate_frame"])
        
        # 检测参数
        if "standing_threshold" in self._settings:
            self._standing_threshold.setValue(self._settings["standing_threshold"])
        if "squat_threshold" in self._settings:
            self._squat_threshold.setValue(self._settings["squat_threshold"])
        if "detection_confidence" in self._settings:
            self._detection_confidence.setValue(int(self._settings["detection_confidence"] * 100))
        
        # 界面设置
        if "show_skeleton" in self._settings:
            self._show_skeleton.setChecked(self._settings["show_skeleton"])
        if "show_angles" in self._settings:
            self._show_angles.setChecked(self._settings["show_angles"])
        if "show_chart" in self._settings:
            self._show_chart.setChecked(self._settings["show_chart"])
        
        # 数据设置
        if "db_path" in self._settings:
            self._db_path.setText(self._settings["db_path"])
        if "buffer_size" in self._settings:
            self._buffer_size.setValue(self._settings["buffer_size"])
        
        # 服务器设置
        if "server_url" in self._settings:
            self._server_url.setText(self._settings["server_url"])
        if "api_key" in self._settings:
            self._api_key.setText(self._settings["api_key"])
        if "auto_upload" in self._settings:
            self._auto_upload.setChecked(self._settings["auto_upload"])
    
    def _save_settings(self):
        """保存设置"""
        settings = {
            # 摄像头
            "camera_index": self._camera_index.value(),
            "resolution": self._resolution.currentText(),
            "fps": self._fps.value(),
            "rotate_frame": self._rotate_frame.isChecked(),
            
            # 检测参数
            "standing_threshold": self._standing_threshold.value(),
            "squat_threshold": self._squat_threshold.value(),
            "detection_confidence": self._detection_confidence.value() / 100,
            
            # 界面设置
            "show_skeleton": self._show_skeleton.isChecked(),
            "show_angles": self._show_angles.isChecked(),
            "show_chart": self._show_chart.isChecked(),
            
            # 数据设置
            "db_path": self._db_path.text(),
            "buffer_size": self._buffer_size.value(),
            
            # 服务器设置
            "server_url": self._server_url.text(),
            "api_key": self._api_key.text(),
            "auto_upload": self._auto_upload.isChecked(),
        }
        
        # 确保目录存在
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存到文件
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        self._settings = settings
        self.settings_changed.emit(settings)
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "保存成功", "设置已保存！")
    
    def _reset_to_default(self):
        """恢复默认设置"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要恢复默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 摄像头
            self._camera_index.setValue(Config.CAMERA_INDEX)
            self._resolution.setCurrentText(f"{Config.CAMERA_RESOLUTION[0]}x{Config.CAMERA_RESOLUTION[1]}")
            self._fps.setValue(Config.CAMERA_FPS)
            self._rotate_frame.setChecked(True)
            
            # 检测参数
            self._standing_threshold.setValue(int(Config.STANDING_ANGLE_THRESHOLD))
            self._squat_threshold.setValue(int(Config.SQUAT_ANGLE_THRESHOLD))
            self._detection_confidence.setValue(int(Config.POSE_DETECTION_CONFIDENCE * 100))
            
            # 界面设置
            self._show_skeleton.setChecked(True)
            self._show_angles.setChecked(True)
            self._show_chart.setChecked(True)
            
            # 数据设置
            self._db_path.setText(str(Config.DATABASE_PATH))
            self._buffer_size.setValue(Config.RECORD_BUFFER_SIZE)
    
    def get_settings(self) -> dict:
        """获取当前设置"""
        return self._settings

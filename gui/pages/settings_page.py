"""
设置页面

应用程序配置界面 - 现代化双栏布局设计。
"""

import json
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSlider, QSpinBox,
    QVBoxLayout, QWidget, QScrollArea, QStackedWidget,
    QSizePolicy, QSpacerItem
)

from src.config import Config


class SettingRow(QWidget):
    
    def __init__(self, label: str, widget: QWidget, description: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._init_ui(label, widget, description)
    
    def _init_ui(self, label: str, widget: QWidget, description: Optional[str]):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        row = QHBoxLayout()
        row.setSpacing(12)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #334155; font-weight: 500;")
        row.addWidget(label_widget)
        
        row.addStretch()
        
        widget.setMinimumHeight(36)
        row.addWidget(widget)
        
        layout.addLayout(row)
        
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
            layout.addWidget(desc_label)


class SliderWithLabel(QWidget):
    
    def __init__(self, min_val: int, max_val: int, default_val: int, 
                 suffix: str = "", format_str: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._suffix = suffix
        self._format_str = format_str
        self._init_ui(min_val, max_val, default_val)
    
    def _init_ui(self, min_val: int, max_val: int, default_val: int):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(min_val, max_val)
        self._slider.setValue(default_val)
        self._slider.setMinimumWidth(180)
        layout.addWidget(self._slider)
        
        self._label = QLabel()
        self._label.setMinimumWidth(50)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_label(default_val)
        layout.addWidget(self._label)
        
        self._slider.valueChanged.connect(self._update_label)
    
    def _update_label(self, value: int):
        if self._format_str:
            text = self._format_str.format(value / 100)
        else:
            text = f"{value}{self._suffix}"
        self._label.setText(text)
    
    def value(self) -> int:
        return self._slider.value()
    
    def setValue(self, value: int):
        self._slider.setValue(value)
    
    def valueChanged(self, callback):
        self._slider.valueChanged.connect(callback)


class CategoryButton(QPushButton):
    """侧边栏分类按钮"""
    
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._text = text
        self._active = False
        self._init_ui()
    
    def _init_ui(self):
        self.setText(f"{self._icon}  {self._text}")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #475569;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #1E293B;
            }
            QPushButton:checked {
                background-color: #D1FAE5;
                color: #059669;
                font-weight: 600;
            }
        """)
    
    def setActive(self, active: bool):
        self._active = active
        self.setChecked(active)


class SettingsPage(QWidget):
    """设置页面 - 现代化双栏布局"""
    
    settings_changed = pyqtSignal(dict)
    CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "gui_settings.json"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = self._load_settings()
        self._category_buttons = []
        self._init_ui()
        self._apply_settings_to_ui()
    
    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        content_area = self._create_content_area()
        main_layout.addWidget(content_area, stretch=1)
    
    def _create_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-right: 1px solid #E2E8F0;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)
        
        title = QLabel("设置")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 8px;
        """)
        layout.addWidget(title)
        
        layout.addSpacing(16)
        
        categories = [
            ("📷", "摄像头", 0),
            ("🎯", "检测参数", 1),
            ("🎨", "界面显示", 2),
            ("💾", "数据存储", 3),
            ("☁️", "服务器", 4),
        ]
        
        for icon, text, index in categories:
            btn = CategoryButton(icon, text)
            btn.clicked.connect(lambda checked, i=index: self._switch_category(i))
            self._category_buttons.append(btn)
            layout.addWidget(btn)
        
        self._category_buttons[0].setChecked(True)
        
        layout.addStretch()
        
        reset_btn = QPushButton("🔄 恢复默认")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FEF2F2;
                border-color: #FECACA;
                color: #DC2626;
            }
        """)
        reset_btn.clicked.connect(self._reset_to_default)
        layout.addWidget(reset_btn)
        
        return sidebar
    
    def _create_content_area(self) -> QWidget:
        content = QFrame()
        content.setStyleSheet("background-color: #F8FAFC;")
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #CBD5E1;
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        self._stack = QStackedWidget()
        
        self._stack.addWidget(self._create_camera_page())
        self._stack.addWidget(self._create_detection_page())
        self._stack.addWidget(self._create_ui_page())
        self._stack.addWidget(self._create_data_page())
        self._stack.addWidget(self._create_server_page())
        
        scroll.setWidget(self._stack)
        layout.addWidget(scroll)
        
        save_bar = self._create_save_bar()
        layout.addWidget(save_bar)
        
        return content
    
    def _create_camera_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        
        self._camera_index = QSpinBox()
        self._camera_index.setRange(0, 10)
        self._camera_index.setValue(Config.CAMERA_INDEX)
        self._camera_index.setFixedWidth(80)
        row1 = SettingRow("摄像头索引", self._camera_index, "选择要使用的摄像头设备")
        layout.addWidget(row1)
        
        self._resolution = QComboBox()
        self._resolution.addItems(["640x480", "1280x720", "1920x1080"])
        self._resolution.setCurrentText(f"{Config.CAMERA_RESOLUTION[0]}x{Config.CAMERA_RESOLUTION[1]}")
        self._resolution.setFixedWidth(120)
        row2 = SettingRow("分辨率", self._resolution, "摄像头采集分辨率")
        layout.addWidget(row2)
        
        self._fps = QSpinBox()
        self._fps.setRange(15, 60)
        self._fps.setValue(Config.CAMERA_FPS)
        self._fps.setFixedWidth(80)
        row3 = SettingRow("目标帧率", self._fps, "每秒采集帧数")
        layout.addWidget(row3)
        
        rotate_container = QWidget()
        rotate_layout = QHBoxLayout(rotate_container)
        rotate_layout.setContentsMargins(0, 0, 0, 0)
        self._rotate_frame = QCheckBox("启用")
        self._rotate_frame.setChecked(True)
        rotate_layout.addWidget(self._rotate_frame)
        row4 = SettingRow("旋转画面", rotate_container, "适用于竖屏摄像头")
        layout.addWidget(row4)
        
        layout.addStretch()
        
        return page
    
    def _create_detection_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        
        self._standing_threshold = SliderWithLabel(120, 180, int(Config.STANDING_ANGLE_THRESHOLD), "°")
        row1 = SettingRow("站立阈值", self._standing_threshold, "膝关节角度大于此值判定为站立")
        layout.addWidget(row1)
        
        self._squat_threshold = SliderWithLabel(45, 120, int(Config.SQUAT_ANGLE_THRESHOLD), "°")
        row2 = SettingRow("下蹲阈值", self._squat_threshold, "膝关节角度小于此值判定为下蹲")
        layout.addWidget(row2)
        
        self._detection_confidence = SliderWithLabel(10, 100, int(Config.POSE_DETECTION_CONFIDENCE * 100), 
                                                      format_str="{:.2f}")
        row3 = SettingRow("检测置信度", self._detection_confidence, "姿态检测的最小置信度阈值")
        layout.addWidget(row3)
        
        layout.addStretch()
        
        return page
    
    def _create_ui_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        
        self._show_skeleton = QCheckBox("显示骨骼连线")
        self._show_skeleton.setChecked(True)
        layout.addWidget(self._show_skeleton)
        
        self._show_angles = QCheckBox("显示角度数值")
        self._show_angles.setChecked(True)
        layout.addWidget(self._show_angles)
        
        self._show_chart = QCheckBox("显示角度曲线图")
        self._show_chart.setChecked(True)
        layout.addWidget(self._show_chart)
        
        layout.addStretch()
        
        return page
    
    def _create_data_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        
        self._db_path = QLineEdit(str(Config.DATABASE_PATH))
        self._db_path.setFixedWidth(280)
        row1 = SettingRow("数据库路径", self._db_path, "训练数据的存储位置")
        layout.addWidget(row1)
        
        self._buffer_size = QSpinBox()
        self._buffer_size.setRange(10, 1000)
        self._buffer_size.setValue(Config.RECORD_BUFFER_SIZE)
        self._buffer_size.setFixedWidth(100)
        row2 = SettingRow("缓冲区大小", self._buffer_size, "数据写入前的内存缓冲条目数")
        layout.addWidget(row2)
        
        layout.addStretch()
        
        return page
    
    def _create_server_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        
        self._server_url = QLineEdit()
        self._server_url.setPlaceholderText("http://117.72.185.244/api/v1/sessions/upload")
        self._server_url.setFixedWidth(320)
        row1 = SettingRow("服务器地址", self._server_url, "数据上传的目标服务器URL")
        layout.addWidget(row1)
        
        self._username = QLineEdit()
        self._username.setPlaceholderText("demo")
        self._username.setFixedWidth(160)
        row2 = SettingRow("用户名", self._username, "登录账号")
        layout.addWidget(row2)
        
        self._password = QLineEdit()
        self._password.setPlaceholderText("••••••")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setFixedWidth(160)
        row3 = SettingRow("密码", self._password, "登录密码")
        layout.addWidget(row3)
        
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self._login_status = QLabel("● 未登录")
        self._login_status.setStyleSheet("color: #EF4444; font-weight: 500;")
        status_layout.addWidget(self._login_status)
        status_layout.addStretch()
        
        row_status = SettingRow("登录状态", status_container)
        layout.addWidget(row_status)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self._login_btn = QPushButton("登录")
        self._login_btn.setMinimumHeight(36)
        self._login_btn.setMinimumWidth(100)
        self._login_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self._login_btn.clicked.connect(self._handle_login)
        btn_row.addWidget(self._login_btn)
        
        self._test_btn = QPushButton("测试连接")
        self._test_btn.setMinimumHeight(36)
        self._test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self._test_btn.clicked.connect(self._test_server_connection)
        btn_row.addWidget(self._test_btn)
        
        self._logout_btn = QPushButton("登出")
        self._logout_btn.setMinimumHeight(36)
        self._logout_btn.setMinimumWidth(100)
        self._logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        self._logout_btn.clicked.connect(self._handle_logout)
        self._logout_btn.setVisible(False)
        btn_row.addWidget(self._logout_btn)
        
        layout.addLayout(btn_row)
        
        self._auto_upload = QCheckBox("训练结束后自动上传数据")
        self._auto_upload.setChecked(False)
        layout.addWidget(self._auto_upload)
        
        layout.addStretch()
        
        return page
    
    def _create_save_bar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-top: 1px solid #E2E8F0;
            }
        """)
        bar.setFixedHeight(72)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(32, 16, 32, 16)
        
        layout.addStretch()
        
        save_btn = QPushButton("保存设置")
        save_btn.setMinimumSize(140, 44)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)
        
        return bar
    
    def _switch_category(self, index: int):
        for i, btn in enumerate(self._category_buttons):
            btn.setChecked(i == index)
        self._stack.setCurrentIndex(index)
    
    def _handle_login(self):
        from PyQt6.QtWidgets import QMessageBox
        import urllib.request
        import urllib.error
        import json
        from urllib.parse import urlparse
        
        username = self._username.text().strip()
        password = self._password.text().strip()
        server_url = self._server_url.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "登录失败", "请输入用户名和密码")
            return
        
        if not server_url:
            QMessageBox.warning(self, "登录失败", "请输入服务器地址")
            return
        
        try:
            parsed = urlparse(server_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            login_url = f"{base_url}/api/v1/auth/login"
            
            data = json.dumps({"username": username, "password": password}).encode('utf-8')
            
            request = urllib.request.Request(
                login_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if "access_token" in result:
                    self._settings["auth_token"] = result["access_token"]
                    self._settings["username"] = username
                    self._update_login_status(True, username)
                    self._save_token_to_file(result["access_token"], username)
                    QMessageBox.information(self, "登录成功", f"欢迎, {username}!")
                else:
                    QMessageBox.warning(self, "登录失败", "服务器未返回有效Token")
                    
        except urllib.error.HTTPError as e:
            if e.code == 401:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误")
            else:
                QMessageBox.warning(self, "登录失败", f"服务器错误: {e.code}")
        except urllib.error.URLError as e:
            QMessageBox.warning(self, "登录失败", f"无法连接到服务器:\n{e}")
        except Exception as e:
            QMessageBox.warning(self, "登录失败", f"登录时出错:\n{e}")
    
    def _handle_logout(self):
        from PyQt6.QtWidgets import QMessageBox
        
        self._settings["auth_token"] = None
        self._settings["username"] = None
        self._update_login_status(False)
        
        self._save_token_to_file(None, None)
        
        QMessageBox.information(self, "已登出", "您已成功登出")
    
    def _update_login_status(self, is_logged_in: bool, username: Optional[str] = None):
        if is_logged_in:
            self._login_status.setText(f"● 已登录 ({username})")
            self._login_status.setStyleSheet("color: #10B981; font-weight: 500;")
            self._login_btn.setVisible(False)
            self._logout_btn.setVisible(True)
        else:
            self._login_status.setText("● 未登录")
            self._login_status.setStyleSheet("color: #EF4444; font-weight: 500;")
            self._login_btn.setVisible(True)
            self._logout_btn.setVisible(False)
    
    def _save_token_to_file(self, token: Optional[str], username: Optional[str]):
        if token:
            self._settings["auth_token"] = token
            self._settings["username"] = username
        else:
            self._settings.pop("auth_token", None)
            self._settings.pop("username", None)
        
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=2, ensure_ascii=False)
    
    def _test_server_connection(self):
        from PyQt6.QtWidgets import QMessageBox
        import urllib.request
        import urllib.error
        from urllib.parse import urlparse
        
        server_url = self._server_url.text().strip()
        
        if not server_url:
            QMessageBox.warning(self, "测试失败", "请输入服务器地址")
            return
        
        try:
            parsed = urlparse(server_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            test_url = f"{base_url}/api/v1/dashboard/overview"
            
            request = urllib.request.Request(test_url, method="GET")
            
            with urllib.request.urlopen(request, timeout=10) as response:
                QMessageBox.information(self, "连接成功", f"服务器响应: {response.status}")
                
        except urllib.error.URLError as e:
            QMessageBox.warning(self, "连接失败", f"无法连接到服务器:\n{e}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"测试连接时出错:\n{e}")
    
    def _load_settings(self) -> dict:
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载设置失败: {e}")
        return {}
    
    def _apply_settings_to_ui(self):
        if not self._settings:
            return
        
        if "camera_index" in self._settings:
            self._camera_index.setValue(self._settings["camera_index"])
        if "resolution" in self._settings:
            self._resolution.setCurrentText(self._settings["resolution"])
        if "fps" in self._settings:
            self._fps.setValue(self._settings["fps"])
        if "rotate_frame" in self._settings:
            self._rotate_frame.setChecked(self._settings["rotate_frame"])
        
        if "standing_threshold" in self._settings:
            self._standing_threshold.setValue(self._settings["standing_threshold"])
        if "squat_threshold" in self._settings:
            self._squat_threshold.setValue(self._settings["squat_threshold"])
        if "detection_confidence" in self._settings:
            self._detection_confidence.setValue(int(self._settings["detection_confidence"] * 100))
        
        if "show_skeleton" in self._settings:
            self._show_skeleton.setChecked(self._settings["show_skeleton"])
        if "show_angles" in self._settings:
            self._show_angles.setChecked(self._settings["show_angles"])
        if "show_chart" in self._settings:
            self._show_chart.setChecked(self._settings["show_chart"])
        
        if "db_path" in self._settings:
            self._db_path.setText(self._settings["db_path"])
        if "buffer_size" in self._settings:
            self._buffer_size.setValue(self._settings["buffer_size"])
        
        if "server_url" in self._settings:
            self._server_url.setText(self._settings["server_url"])
        if "username" in self._settings:
            self._username.setText(self._settings["username"])
        if "auto_upload" in self._settings:
            self._auto_upload.setChecked(self._settings["auto_upload"])
        
        if "auth_token" in self._settings and self._settings["auth_token"]:
            self._update_login_status(True, self._settings.get("username", ""))
        else:
            self._update_login_status(False)
    
    def _save_settings(self):
        settings = {
            "camera_index": self._camera_index.value(),
            "resolution": self._resolution.currentText(),
            "fps": self._fps.value(),
            "rotate_frame": self._rotate_frame.isChecked(),
            
            "standing_threshold": self._standing_threshold.value(),
            "squat_threshold": self._squat_threshold.value(),
            "detection_confidence": self._detection_confidence.value() / 100,
            
            "show_skeleton": self._show_skeleton.isChecked(),
            "show_angles": self._show_angles.isChecked(),
            "show_chart": self._show_chart.isChecked(),
            
            "db_path": self._db_path.text(),
            "buffer_size": self._buffer_size.value(),
            
            "server_url": self._server_url.text(),
            "username": self._username.text(),
            "auto_upload": self._auto_upload.isChecked(),
            "auth_token": self._settings.get("auth_token"),
        }
        
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        self._settings = settings
        self.settings_changed.emit(settings)
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "保存成功", "设置已保存！")
    
    def _reset_to_default(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要恢复默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._camera_index.setValue(Config.CAMERA_INDEX)
            self._resolution.setCurrentText(f"{Config.CAMERA_RESOLUTION[0]}x{Config.CAMERA_RESOLUTION[1]}")
            self._fps.setValue(Config.CAMERA_FPS)
            self._rotate_frame.setChecked(True)
            
            self._standing_threshold.setValue(int(Config.STANDING_ANGLE_THRESHOLD))
            self._squat_threshold.setValue(int(Config.SQUAT_ANGLE_THRESHOLD))
            self._detection_confidence.setValue(int(Config.POSE_DETECTION_CONFIDENCE * 100))
            
            self._show_skeleton.setChecked(True)
            self._show_angles.setChecked(True)
            self._show_chart.setChecked(True)
            
            self._db_path.setText(str(Config.DATABASE_PATH))
            self._buffer_size.setValue(Config.RECORD_BUFFER_SIZE)
    
    def get_settings(self) -> dict:
        return self._settings
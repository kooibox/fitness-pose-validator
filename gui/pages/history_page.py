"""
历史记录页面

显示训练历史记录和分析图表 - 简洁扁平化设计。
"""

from datetime import datetime
from typing import List, Optional
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, 
    QMessageBox, QPushButton, QComboBox,
    QVBoxLayout, QWidget, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage

from src.database import Database, Session
from src.analyzer import TrainingAnalyzer
from gui.workers.upload_worker import UploadWorker


class HistoryPage(QWidget):
    """
    历史记录页面 - 简洁扁平化设计
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = Database()
        self._analyzer = TrainingAnalyzer()
        self._current_session_id = None
        self._sessions: List[Session] = []
        self._init_ui()
        self._load_sessions()
    
    def _init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)
        
        # === 顶部：标题 + 按钮 ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        title = QLabel("历史训练记录")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        header_layout.addWidget(title)
        
        # 统计标签
        self._stats_label = QLabel("共 0 条")
        self._stats_label.setStyleSheet("color: #94A3B8; font-size: 13px; margin-left: 8px;")
        header_layout.addWidget(self._stats_label)
        
        header_layout.addStretch()
        
        # 按钮组
        self._upload_btn = QPushButton("上传")
        self._upload_btn.clicked.connect(self._upload_current)
        self._upload_btn.setEnabled(False)
        self._upload_btn.setFixedHeight(32)
        self._upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; border: none;
                padding: 0 16px; border-radius: 6px; font-weight: 500;
            }
            QPushButton:hover { background-color: #059669; }
            QPushButton:disabled { background-color: #E2E8F0; color: #94A3B8; }
        """)
        header_layout.addWidget(self._upload_btn)
        
        self._delete_btn = QPushButton("删除")
        self._delete_btn.clicked.connect(self._delete_current)
        self._delete_btn.setEnabled(False)
        self._delete_btn.setFixedHeight(32)
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; color: white; border: none;
                padding: 0 16px; border-radius: 6px; font-weight: 500;
            }
            QPushButton:hover { background-color: #DC2626; }
            QPushButton:disabled { background-color: #E2E8F0; color: #94A3B8; }
        """)
        header_layout.addWidget(self._delete_btn)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_sessions)
        refresh_btn.setFixedHeight(32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6; color: white; border: none;
                padding: 0 16px; border-radius: 6px; font-weight: 500;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # === 分割线 ===
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        main_layout.addWidget(line1)
        
        # === 选择行：下拉框 ===
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(12)
        
        selector_label = QLabel("选择记录")
        selector_label.setStyleSheet("color: #475569; font-weight: 500;")
        selector_layout.addWidget(selector_label)
        
        self._combo = QComboBox()
        self._combo.setMinimumWidth(320)
        self._combo.setFixedHeight(36)
        self._combo.setStyleSheet("""
            QComboBox {
                background-color: white; border: 1px solid #D1D5DB; border-radius: 6px;
                padding: 0 12px; color: #1E293B; font-size: 13px;
            }
            QComboBox:focus { border-color: #10B981; }
            QComboBox::drop-down {
                subcontrol-position: center right; width: 24px; border: none;
                border-left: 1px solid #E2E8F0; border-radius: 0 6px 6px 0;
            }
            QComboBox::down-arrow {
                image: none; width: 10px; height: 10px;
                border-left: 4px solid transparent; border-right: 4px solid transparent;
                border-top: 5px solid #64748B;
            }
            QComboBox QAbstractItemView {
                background-color: white; border: 1px solid #E2E8F0; border-radius: 6px;
                selection-background-color: #D1FAE5; selection-color: #047857;
            }
        """)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        selector_layout.addWidget(self._combo)
        selector_layout.addStretch()
        
        main_layout.addLayout(selector_layout)
        
        # === 分割线 ===
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        main_layout.addWidget(line2)
        
        # === 详情区域 ===
        self._detail_container = QWidget()
        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(0, 8, 0, 0)
        self._detail_layout.setSpacing(16)
        
        # 占位提示
        self._placeholder = QLabel("请选择一条训练记录查看详情")
        self._placeholder.setStyleSheet("color: #94A3B8; font-size: 14px; padding: 32px 0;")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_layout.addWidget(self._placeholder)
        self._detail_layout.addStretch()
        
        main_layout.addWidget(self._detail_container, stretch=1)
    
    def _load_sessions(self):
        """加载训练会话"""
        self._sessions = self._db.get_recent_sessions(50)
        
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem("请选择...", None)
        
        for session in self._sessions:
            start_time = datetime.fromisoformat(session.start_time)
            time_str = start_time.strftime("%m-%d %H:%M")
            self._combo.addItem(f"#{session.id}  {time_str}  ·  {session.total_squats}次深蹲", session.id)
        
        self._combo.blockSignals(False)
        self._stats_label.setText(f"共 {len(self._sessions)} 条")
        
        self._current_session_id = None
        self._upload_btn.setEnabled(False)
        self._delete_btn.setEnabled(False)
        self._show_placeholder()
    
    def _on_selection_changed(self, index: int):
        """选择改变"""
        if index <= 0:
            self._current_session_id = None
            self._upload_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            self._show_placeholder()
            return
        
        self._current_session_id = self._combo.currentData()
        self._upload_btn.setEnabled(True)
        self._delete_btn.setEnabled(True)
        self._show_session_detail(self._current_session_id)
    
    def _clear_detail(self):
        """清除详情区域"""
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _show_placeholder(self):
        """显示占位提示"""
        self._clear_detail()
        placeholder = QLabel("请选择一条训练记录查看详情")
        placeholder.setStyleSheet("color: #94A3B8; font-size: 14px; padding: 32px 0;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_layout.addWidget(placeholder)
        self._detail_layout.addStretch()
    
    def _show_session_detail(self, session_id: int):
        """显示会话详情 - 卡片布局"""
        self._clear_detail()
        
        analysis = self._analyzer.analyze_session(session_id)
        if not analysis:
            error = QLabel("无法加载会话数据")
            error.setStyleSheet("color: #EF4444; padding: 20px;")
            self._detail_layout.addWidget(error)
            return
        
        # ===== 第一部分：两张卡片横向排列 =====
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        # --- 左侧卡片：核心数据 ---
        core_card = QFrame()
        core_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        core_layout = QVBoxLayout(core_card)
        core_layout.setContentsMargins(20, 16, 20, 16)
        core_layout.setSpacing(4)
        
        # 标题
        title_lbl = QLabel("核心数据")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 8px;")
        core_layout.addWidget(title_lbl)
        
        # 所有数据合并为一个文本
        core_text = f"""训练时长  {analysis.duration_seconds:.0f} 秒
总帧数    {analysis.total_records}
深蹲次数  {analysis.total_squats} 次
质量评分  {analysis.quality_score:.1f}"""
        
        core_lbl = QLabel(core_text)
        core_lbl.setStyleSheet("""
            font-size: 14px; 
            color: #334155; 
            line-height: 1.8;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        core_layout.addWidget(core_lbl)
        
        cards_layout.addWidget(core_card, stretch=1)
        
        # --- 右侧卡片：角度分析 ---
        angle_card = QFrame()
        angle_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        angle_layout = QVBoxLayout(angle_card)
        angle_layout.setContentsMargins(20, 16, 20, 16)
        angle_layout.setSpacing(4)
        
        # 标题
        angle_title_lbl = QLabel("角度分析")
        angle_title_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 8px;")
        angle_layout.addWidget(angle_title_lbl)
        
        # 所有数据合并为一个文本
        angle_text = f"""平均角度  {analysis.avg_angle:.1f}°
最小角度  {analysis.min_angle:.1f}°
最大角度  {analysis.max_angle:.1f}°"""
        
        angle_lbl = QLabel(angle_text)
        angle_lbl.setStyleSheet("""
            font-size: 14px; 
            color: #334155; 
            line-height: 1.8;
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        angle_layout.addWidget(angle_lbl)
        
        cards_layout.addWidget(angle_card, stretch=1)
        
        self._detail_layout.addLayout(cards_layout)
        
        # ===== 第二部分：图表区域 - 占满剩余空间 =====
        chart_label = self._generate_chart(session_id)
        if chart_label:
            chart_card = QFrame()
            chart_card.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 12px;
                }
            """)
            chart_outer = QVBoxLayout(chart_card)
            chart_outer.setContentsMargins(20, 16, 20, 16)
            chart_outer.setSpacing(12)
            
            chart_title = QLabel("训练曲线")
            chart_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #1E293B;")
            chart_outer.addWidget(chart_title)
            
            chart_outer.addWidget(chart_label, stretch=1)
            
            self._detail_layout.addWidget(chart_card, stretch=1)
    
    def _generate_chart(self, session_id: int) -> Optional[QWidget]:
        """生成训练分析图表 - 自适应大小"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from io import BytesIO
            
            fig = self._analyzer.plot_session_analysis(session_id)
            if not fig:
                return None
            
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            buf.seek(0)
            
            qimg = QImage.fromData(buf.read())
            self._chart_pixmap = QPixmap.fromImage(qimg)
            
            # 图表标签 - 可扩展
            self._chart_label = QLabel()
            self._chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._chart_label.setMinimumHeight(200)
            self._chart_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
            
            # 初始设置图表
            self._update_chart_size()
            
            return self._chart_label
            
        except Exception as e:
            print(f"生成图表失败: {e}")
            return None
    
    def _update_chart_size(self):
        """更新图表大小以保持宽高比"""
        if hasattr(self, '_chart_pixmap') and hasattr(self, '_chart_label'):
            if self._chart_pixmap.isNull():
                return
            
            # 获取标签的可用大小
            label_size = self._chart_label.size()
            available_width = max(label_size.width(), 400)
            available_height = max(label_size.height(), 250)
            
            # 按可用空间缩放，保持宽高比
            scaled = self._chart_pixmap.scaled(
                available_width, available_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._chart_label.setPixmap(scaled)
    
    def resizeEvent(self, event):
        """窗口大小改变时更新图表"""
        super().resizeEvent(event)
        self._update_chart_size()
    
    def _delete_current(self):
        """删除当前记录"""
        if not self._current_session_id:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除训练记录 #{self._current_session_id}？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._db.delete_sessions([self._current_session_id]) > 0:
                QMessageBox.information(self, "已删除", f"已删除训练记录 #{self._current_session_id}")
                self._load_sessions()
            else:
                QMessageBox.warning(self, "删除失败", "无法删除记录")
    
    def _upload_current(self):
        """上传当前记录"""
        if not self._current_session_id:
            return
        
        import json
        config_file = Path(__file__).parent.parent.parent / "data" / "gui_settings.json"
        if not config_file.exists():
            QMessageBox.warning(self, "配置错误", "请先配置服务器地址")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "配置错误", f"无法加载配置: {e}")
            return
        
        server_url = settings.get("server_url", "").strip()
        api_key = settings.get("api_key", "").strip()
        
        if not server_url:
            QMessageBox.warning(self, "配置错误", "请先配置服务器地址")
            return
        
        reply = QMessageBox.question(
            self, "确认上传",
            f"上传训练记录 #{self._current_session_id} 到服务器？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self._upload_btn.setEnabled(False)
        self._upload_btn.setText("上传中...")
        
        self._upload_worker = UploadWorker(
            session_ids=[self._current_session_id],
            server_url=server_url,
            api_key=api_key
        )
        
        self._upload_worker.progress.connect(lambda c, t: self._upload_btn.setText(f"上传中 {c}/{t}"))
        self._upload_worker.upload_failed.connect(lambda e: QMessageBox.warning(self, "上传失败", e))
        self._upload_worker.finished.connect(self._on_upload_finished)
        self._upload_worker.start()
    
    def _on_upload_finished(self):
        """上传完成"""
        self._upload_btn.setEnabled(True)
        self._upload_btn.setText("上传")
        QMessageBox.information(self, "上传完成", "数据已上传")
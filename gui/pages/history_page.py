"""
历史记录页面

显示训练历史记录和分析图表。
"""

from datetime import datetime
from typing import List, Optional
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, 
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget
)
from PyQt6.QtGui import QPixmap, QImage

from src.database import Database, Session
from src.analyzer import TrainingAnalyzer


class HistoryPage(QWidget):
    """
    历史记录页面
    
    显示训练会话列表和详细分析。
    """
    
    def __init__(self, parent=None):
        """初始化历史记录页面"""
        super().__init__(parent)
        
        # 数据库和分析器
        self._db = Database()
        self._analyzer = TrainingAnalyzer()
        
        # 初始化 UI
        self._init_ui()
        
        # 加载数据
        self._load_sessions()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # 标题栏
        header = self._create_header()
        main_layout.addWidget(header)
        
        # 内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # 左侧：会话列表
        list_container = QFrame()
        list_container.setProperty("cssClass", "card")
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(16, 16, 16, 16)
        
        list_title = QLabel("训练记录")
        list_title.setProperty("cssClass", "subtitle")
        list_layout.addWidget(list_title)
        
        self._table = self._create_table()
        list_layout.addWidget(self._table)
        
        content_layout.addWidget(list_container, stretch=2)
        
        # 右侧：详情面板
        detail_container = QFrame()
        detail_container.setProperty("cssClass", "card")
        self._detail_layout = QVBoxLayout(detail_container)
        self._detail_layout.setContentsMargins(16, 16, 16, 16)
        
        detail_title = QLabel("会话详情")
        detail_title.setProperty("cssClass", "subtitle")
        self._detail_layout.addWidget(detail_title)
        
        # 占位内容
        self._detail_placeholder = QLabel("选择一条记录查看详情")
        self._detail_placeholder.setStyleSheet("""
            color: #94A3B8;
            font-size: 14px;
        """)
        self._detail_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_layout.addWidget(self._detail_placeholder)
        
        content_layout.addWidget(detail_container, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
    
    def _create_header(self) -> QFrame:
        """创建标题栏"""
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title = QLabel("📊 历史训练记录")
        title.setProperty("cssClass", "title")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_sessions)
        layout.addWidget(refresh_btn)
        
        # 删除按钮
        self._delete_btn = QPushButton("🗑 删除选中")
        self._delete_btn.setProperty("cssClass", "danger")
        self._delete_btn.clicked.connect(self._delete_selected)
        self._delete_btn.setEnabled(False)
        layout.addWidget(self._delete_btn)
        
        return header
    
    def _create_table(self) -> QTableWidget:
        """创建表格"""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "开始时间", "时长", "深蹲次数"])
        
        # 表格设置
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # 列宽
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        return table
    
    def _load_sessions(self):
        """加载训练会话"""
        sessions = self._db.get_recent_sessions(50)
        
        self._table.setRowCount(len(sessions))
        
        for row, session in enumerate(sessions):
            # ID
            id_item = QTableWidgetItem(str(session.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, id_item)
            
            # 开始时间
            start_time = datetime.fromisoformat(session.start_time)
            time_item = QTableWidgetItem(start_time.strftime("%Y-%m-%d %H:%M"))
            self._table.setItem(row, 1, time_item)
            
            # 时长
            duration = "N/A"
            if session.end_time:
                end_time = datetime.fromisoformat(session.end_time)
                seconds = (end_time - start_time).total_seconds()
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                duration = f"{minutes}:{secs:02d}"
            
            duration_item = QTableWidgetItem(duration)
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 2, duration_item)
            
            # 深蹲次数
            count_item = QTableWidgetItem(str(session.total_squats))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, count_item)
    
    def _on_selection_changed(self):
        """选择改变"""
        selected_rows = self._table.selectionModel().selectedRows()
        self._delete_btn.setEnabled(len(selected_rows) > 0)
        
        if len(selected_rows) == 1:
            row = selected_rows[0].row()
            session_id = int(self._table.item(row, 0).text())
            self._show_session_detail(session_id)
    
    def _show_session_detail(self, session_id: int):
        """显示会话详情"""
        # 清除旧内容
        for i in reversed(range(self._detail_layout.count())):
            item = self._detail_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        # 分析会话
        analysis = self._analyzer.analyze_session(session_id)
        if not analysis:
            error_label = QLabel("无法加载会话数据")
            error_label.setStyleSheet("color: #EF4444;")
            self._detail_layout.addWidget(error_label)
            return
        
        # 标题
        title = QLabel(f"会话 #{session_id}")
        title.setProperty("cssClass", "subtitle")
        self._detail_layout.addWidget(title)
        
        # 基本信息
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            background-color: #F8FAFC;
            border-radius: 8px;
            padding: 12px;
        """)
        info_layout = QVBoxLayout(info_frame)
        
        info_items = [
            ("时长", f"{analysis.duration_seconds:.0f} 秒"),
            ("总帧数", str(analysis.total_records)),
            ("深蹲次数", str(analysis.total_squats)),
            ("质量评分", f"{analysis.quality_score:.1f} / 100"),
        ]
        
        for label, value in info_items:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addStretch()
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: 600; color: #10B981;")
            row.addWidget(value_label)
            info_layout.addLayout(row)
        
        self._detail_layout.addWidget(info_frame)
        
        # 角度统计
        angle_frame = QFrame()
        angle_frame.setStyleSheet("""
            background-color: #F8FAFC;
            border-radius: 8px;
            padding: 12px;
        """)
        angle_layout = QVBoxLayout(angle_frame)
        
        angle_title = QLabel("角度统计")
        angle_title.setStyleSheet("font-weight: 600;")
        angle_layout.addWidget(angle_title)
        
        angle_items = [
            ("平均角度", f"{analysis.avg_angle:.1f}°"),
            ("最小角度", f"{analysis.min_angle:.1f}°"),
            ("最大角度", f"{analysis.max_angle:.1f}°"),
        ]
        
        for label, value in angle_items:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addStretch()
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: 500;")
            row.addWidget(value_label)
            angle_layout.addLayout(row)
        
        self._detail_layout.addWidget(angle_frame)
        
        # 图表显示
        chart_title = QLabel("训练分析图表")
        chart_title.setStyleSheet("font-weight: 600; margin-top: 12px;")
        self._detail_layout.addWidget(chart_title)
        
        # 生成图表
        chart_label = self._generate_chart(session_id)
        if chart_label:
            self._detail_layout.addWidget(chart_label)
        
        # 弹性空间
        self._detail_layout.addStretch()
    
    def _generate_chart(self, session_id: int) -> Optional[QLabel]:
        """生成训练分析图表"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from io import BytesIO
            
            # 生成图表
            fig = self._analyzer.plot_session_analysis(session_id)
            if not fig:
                return None
            
            # 将图表转换为 QPixmap
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            
            # 创建 QImage
            img_data = buf.read()
            qimg = QImage.fromData(img_data)
            pixmap = QPixmap.fromImage(qimg)
            
            # 创建 QLabel 显示图表
            chart_label = QLabel()
            chart_label.setPixmap(pixmap)
            chart_label.setScaledContents(True)
            chart_label.setMaximumHeight(400)
            chart_label.setStyleSheet("""
                background-color: white;
                border-radius: 8px;
                padding: 8px;
            """)
            
            return chart_label
            
        except Exception as e:
            print(f"生成图表失败: {e}")
            return None
    
    def _clear_detail_panel(self):
        """清除详情面板内容"""
        for i in reversed(range(self._detail_layout.count())):
            item = self._detail_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        # 添加占位内容
        self._detail_placeholder = QLabel("选择一条记录查看详情")
        self._detail_placeholder.setStyleSheet("""
            color: #94A3B8;
            font-size: 14px;
        """)
        self._detail_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_layout.addWidget(self._detail_placeholder)
    
    def _delete_selected(self):
        """删除选中的记录"""
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {len(selected_rows)} 条记录吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 获取要删除的会话ID
            session_ids = []
            for index in selected_rows:
                row = index.row()
                session_id = int(self._table.item(row, 0).text())
                session_ids.append(session_id)
            
            # 批量删除
            deleted_count = self._db.delete_sessions(session_ids)
            
            if deleted_count > 0:
                QMessageBox.information(
                    self,
                    "删除成功",
                    f"已删除 {deleted_count} 条记录"
                )
                # 刷新列表
                self._load_sessions()
                # 清除详情面板
                self._clear_detail_panel()
            else:
                QMessageBox.warning(self, "删除失败", "无法删除记录")

"""
历史记录页面 v2

深色霓虹风格的历史训练记录展示页面。
"""

from datetime import datetime
from typing import List, Optional
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QComboBox,
    QVBoxLayout, QWidget, QSizePolicy, QProgressBar
)
from PyQt6.QtGui import QPixmap, QImage, QLinearGradient, QColor, QPainter, QPen

from src.database import Database, Session
from src.analyzer import TrainingAnalyzer
from gui.workers.upload_worker import UploadWorker


class QualityScoreWidget(QWidget):
    """质量评分环形组件"""

    def __init__(self, score: float = 0, parent=None):
        super().__init__(parent)
        self._score = score
        self.setMinimumSize(100, 100)
        self.setMaximumSize(120, 120)

    def setScore(self, score: float):
        self._score = score
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = int(min(rect.width(), rect.height()) / 2 - 10)

        # 背景圆环
        bg_pen = QPen()
        bg_pen.setColor(QColor("#27272A"))
        bg_pen.setWidth(8)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(center, radius, radius)

        # 进度圆环
        if self._score > 0:
            progress_pen = QPen()
            # 根据分数选择颜色
            if self._score >= 90:
                color = QColor("#22C55E")  # 绿色
            elif self._score >= 70:
                color = QColor("#3B82F6")  # 蓝色
            elif self._score >= 50:
                color = QColor("#F97316")  # 橙色
            else:
                color = QColor("#EF4444")  # 红色

            progress_pen.setColor(color)
            progress_pen.setWidth(8)
            progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(progress_pen)

            span_angle = int(-(self._score / 100) * 360 * 16)
            painter.drawArc(
                int(center.x() - radius),
                int(center.y() - radius),
                int(radius * 2),
                int(radius * 2),
                90 * 16,
                span_angle
            )

        # 中心文字
        painter.setPen(QPen(QColor("#FFFFFF")))
        font = painter.font()
        font.setPixelSize(int(radius * 0.5))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._score:.0f}")


class HistoryPage(QWidget):
    """历史记录页面 V2 - 深色霓虹风格"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = Database()
        self._analyzer = TrainingAnalyzer()
        self._current_session_id = None
        self._sessions: List[Session] = []
        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # === 顶部：标题 + 按钮 ===
        header = QFrame()
        header.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header)
        header_layout.setSpacing(16)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)

        title = QLabel("历史训练记录")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #FFFFFF; background: transparent; border: none;")
        title_layout.addWidget(title)

        self._stats_label = QLabel("共 0 条")
        self._stats_label.setStyleSheet("color: #71717A; font-size: 13px; background: transparent; border: none;")
        title_layout.addWidget(self._stats_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # 按钮组
        btn_style = """
            QPushButton {
                background-color: #1E1E22;
                color: #A1A1AA;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #252529;
                color: #FFFFFF;
                border-color: #52525B;
            }
            QPushButton:disabled {
                background-color: #161619;
                color: #52525B;
                border-color: #27272A;
            }
        """

        upload_btn = QPushButton("📤 上传")
        upload_btn.setToolTip("上传训练数据到服务器")
        upload_btn.setStyleSheet(btn_style.replace("#1E1E22", "#22C55E").replace("#A1A1AA", "#FFFFFF").replace("#3F3F46", "#22C55E").replace("#52525B", "#16A34A") + """
            QPushButton:disabled {
                background-color: #27272A;
                color: #71717A;
                border-color: #27272A;
            }
        """)
        upload_btn.clicked.connect(self._upload_current)
        upload_btn.setEnabled(False)
        upload_btn.setFixedHeight(36)
        self._upload_btn = upload_btn
        header_layout.addWidget(upload_btn)

        delete_btn = QPushButton("🗑 删除")
        delete_btn.setToolTip("删除选中的训练记录")
        delete_btn.setStyleSheet(btn_style.replace("#1E1E22", "#EF4444").replace("#A1A1AA", "#FFFFFF").replace("#3F3F46", "#EF4444").replace("#52525B", "#DC2626") + """
            QPushButton:disabled {
                background-color: #27272A;
                color: #71717A;
                border-color: #27272A;
            }
        """)
        delete_btn.clicked.connect(self._delete_current)
        delete_btn.setEnabled(False)
        delete_btn.setFixedHeight(36)
        self._delete_btn = delete_btn
        header_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setToolTip("刷新训练记录列表")
        refresh_btn.setStyleSheet(btn_style)
        refresh_btn.clicked.connect(self._load_sessions)
        refresh_btn.setFixedHeight(36)
        header_layout.addWidget(refresh_btn)

        main_layout.addWidget(header)

        # === 选择行 ===
        selector = QFrame()
        selector.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 12px;
                border: 1px solid #27272A;
                padding: 12px;
            }
        """)
        selector_layout = QHBoxLayout(selector)
        selector_layout.setSpacing(12)

        selector_label = QLabel("选择记录")
        selector_label.setStyleSheet("color: #A1A1AA; font-weight: 500; background: transparent; border: none;")
        selector_layout.addWidget(selector_label)

        self._combo = QComboBox()
        self._combo.setMinimumWidth(360)
        self._combo.setFixedHeight(40)
        self._combo.setStyleSheet("""
            QComboBox {
                background-color: #1E1E22;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 0 14px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #52525B;
            }
            QComboBox::drop-down {
                border: none;
                width: 32px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #71717A;
            }
            QComboBox QAbstractItemView {
                background-color: #1E1E22;
                border: 1px solid #3F3F46;
                selection-background-color: rgba(34, 197, 94, 0.2);
                selection-color: #22C55E;
                color: #FFFFFF;
            }
        """)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        selector_layout.addWidget(self._combo)
        selector_layout.addStretch()

        main_layout.addWidget(selector)

        # === 详情区域 ===
        self._detail_container = QWidget()
        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(0, 12, 0, 0)
        self._detail_layout.setSpacing(16)

        # 占位提示
        self._placeholder = QLabel("请选择一条训练记录查看详情")
        self._placeholder.setStyleSheet("color: #71717A; font-size: 14px; padding: 48px 0;")
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
            # 注意: Session 对象暂无 exercise_type 属性，暂不显示
            self._combo.addItem(
                f"#{session.id}  {time_str}  ·  {session.total_squats}次",
                session.id
            )

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
        placeholder.setStyleSheet("color: #71717A; font-size: 14px; padding: 48px 0;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_layout.addWidget(placeholder)
        self._detail_layout.addStretch()

    def _show_session_detail(self, session_id: int):
        """显示会话详情"""
        self._clear_detail()

        analysis = self._analyzer.analyze_session(session_id)
        if not analysis:
            error = QLabel("无法加载会话数据")
            error.setStyleSheet("color: #EF4444; padding: 20px;")
            self._detail_layout.addWidget(error)
            return

        # ===== 第一行：统计卡片 =====
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        # 训练时长卡片
        duration_card = self._create_info_card("⏱ 训练时长", f"{analysis.duration_seconds / 60:.1f} 分钟")
        stats_row.addWidget(duration_card)

        # 总次数卡片
        count_card = self._create_info_card("📋 总次数", f"{analysis.total_squats} 次")
        stats_row.addWidget(count_card)

        # 有效次数卡片
        valid_card = self._create_info_card("✅ 有效次数", f"{analysis.valid_count} 次")
        stats_row.addWidget(valid_card)

        # 质量评分卡片
        quality_card = self._create_quality_card(analysis.quality_score)
        stats_row.addWidget(quality_card)

        self._detail_layout.addLayout(stats_row)

        # ===== 第二行：角度分析 =====
        angles_row = QHBoxLayout()
        angles_row.setSpacing(16)

        angle_card = QFrame()
        angle_card.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        angle_layout = QVBoxLayout(angle_card)
        angle_layout.setContentsMargins(20, 16, 20, 16)
        angle_layout.setSpacing(12)

        angle_title = QLabel("📊 角度分析")
        angle_title.setStyleSheet("color: #E4E4E7; font-size: 15px; font-weight: 600; background: transparent; border: none;")
        angle_layout.addWidget(angle_title)

        angle_text = f"""
        <div style="color: #A1A1AA; font-size: 14px; line-height: 1.8;">
        <span style="color: #22C55E;">平均角度</span>  {analysis.avg_angle:.1f}°<br/>
        <span style="color: #3B82F6;">最小角度</span>  {analysis.min_angle:.1f}°<br/>
        <span style="color: #F97316;">最大角度</span>  {analysis.max_angle:.1f}°
        </div>
        """
        angle_lbl = QLabel(angle_text)
        angle_lbl.setStyleSheet("background: transparent; border: none;")
        angle_layout.addWidget(angle_lbl)

        angles_row.addWidget(angle_card, stretch=1)

        # 问题分布卡片
        issues_card = QFrame()
        issues_card.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        issues_layout = QVBoxLayout(issues_card)
        issues_layout.setContentsMargins(20, 16, 20, 16)
        issues_layout.setSpacing(12)

        issues_title = QLabel("⚠️ 动作问题分布")
        issues_title.setStyleSheet("color: #E4E4E7; font-size: 15px; font-weight: 600; background: transparent; border: none;")
        issues_layout.addWidget(issues_title)

        # 问题分布
        if hasattr(analysis, 'issue_stats') and analysis.issue_stats:
            for issue, percentage in analysis.issue_stats.items():
                issue_row = self._create_issue_bar(issue, percentage)
                issues_layout.addWidget(issue_row)
        else:
            no_issues = QLabel("无动作问题")
            no_issues.setStyleSheet("color: #22C55E; font-size: 13px; background: transparent; border: none;")
            issues_layout.addWidget(no_issues)

        issues_layout.addStretch()

        angles_row.addWidget(issues_card, stretch=1)

        self._detail_layout.addLayout(angles_row)

        # ===== 第三行：图表区域 =====
        chart_label = self._generate_chart(session_id)
        if chart_label:
            chart_card = QFrame()
            chart_card.setStyleSheet("""
                QFrame {
                    background-color: #161619;
                    border-radius: 12px;
                    border: 1px solid #27272A;
                }
            """)
            chart_outer = QVBoxLayout(chart_card)
            chart_outer.setContentsMargins(20, 16, 20, 16)
            chart_outer.setSpacing(12)

            chart_title = QLabel("📈 训练曲线")
            chart_title.setStyleSheet("color: #E4E4E7; font-size: 15px; font-weight: 600; background: transparent; border: none;")
            chart_outer.addWidget(chart_title)

            chart_outer.addWidget(chart_label, stretch=1)

            self._detail_layout.addWidget(chart_card, stretch=2)

    def _create_info_card(self, title: str, value: str) -> QFrame:
        """创建信息卡片"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #71717A; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("color: #FFFFFF; font-size: 24px; font-weight: 700; background: transparent; border: none;")
        layout.addWidget(value_label)

        return card

    def _create_quality_card(self, score: float) -> QFrame:
        """创建质量评分卡片"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #161619;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        quality_widget = QualityScoreWidget(score)
        layout.addWidget(quality_widget)

        title_label = QLabel("质量评分")
        title_label.setStyleSheet("color: #71717A; font-size: 12px; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        return card

    def _create_issue_bar(self, issue: str, percentage: float) -> QFrame:
        """创建问题分布条"""
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        label_layout = QHBoxLayout()
        label_layout.setSpacing(8)

        issue_label = QLabel(issue)
        issue_label.setStyleSheet("color: #A1A1AA; font-size: 12px; background: transparent; border: none;")
        label_layout.addWidget(issue_label)

        pct_label = QLabel(f"{percentage:.0f}%")
        pct_label.setStyleSheet("color: #F97316; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        label_layout.addWidget(pct_label)

        layout.addLayout(label_layout)

        # 进度条
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(percentage))
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setStyleSheet("""
            QProgressBar {
                background-color: #27272A;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: #F97316;
                border-radius: 3px;
            }
        """)
        layout.addWidget(bar)

        return frame

    def _generate_chart(self, session_id: int) -> Optional[QWidget]:
        """生成训练分析图表"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from io import BytesIO

            fig = self._analyzer.plot_session_analysis(session_id)
            if not fig:
                return None

            # 应用深色主题到图表
            fig.patch.set_facecolor('#161619')
            for ax in fig.axes:
                ax.set_facecolor('#1E1E22')
                ax.tick_params(colors='#A1A1AA', labelsize=9)
                ax.xaxis.label.set_color('#A1A1AA')
                ax.yaxis.label.set_color('#A1A1AA')
                for spine in ax.spines.values():
                    spine.set_color('#27272A')

            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                       facecolor='#161619', edgecolor='none')
            plt.close(fig)
            buf.seek(0)

            qimg = QImage.fromData(buf.read())
            self._chart_pixmap = QPixmap.fromImage(qimg)

            self._chart_label = QLabel()
            self._chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._chart_label.setMinimumHeight(200)
            self._chart_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )

            self._update_chart_size()

            return self._chart_label

        except Exception as e:
            print(f"生成图表失败: {e}")
            return None

    def _update_chart_size(self):
        """更新图表大小"""
        if hasattr(self, '_chart_pixmap') and hasattr(self, '_chart_label'):
            if self._chart_pixmap.isNull():
                return

            label_size = self._chart_label.size()
            available_width = max(label_size.width(), 400)
            available_height = max(label_size.height(), 200)

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
        self._upload_btn.setText("⏳ 上传中...")

        self._upload_worker = UploadWorker(
            session_ids=[self._current_session_id],
            server_url=server_url,
            api_key=api_key
        )

        self._upload_worker.progress.connect(lambda c, t: self._upload_btn.setText(f"上传 {c}/{t}"))
        self._upload_worker.upload_failed.connect(lambda e: QMessageBox.warning(self, "上传失败", e))
        self._upload_worker.finished.connect(self._on_upload_finished)
        self._upload_worker.start()

    def _on_upload_finished(self):
        """上传完成"""
        self._upload_btn.setEnabled(True)
        self._upload_btn.setText("📤 上传")
        QMessageBox.information(self, "上传完成", "数据已上传")

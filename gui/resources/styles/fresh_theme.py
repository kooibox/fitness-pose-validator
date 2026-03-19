"""
清新活力主题样式

设计原则:
- 主色调: 清新绿 (#10B981) + 活力蓝 (#3B82F6)
- 背景: 浅灰白 (#F8FAFC)
- 强调色: 活力橙 (#F59E0B) 用于计数
- 圆角设计，柔和阴影
"""

# 清新活力主题 QSS 样式表
FRESH_THEME = """
/* ========== 全局设置 ========== */
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #1E293B;
}

/* ========== 主窗口 ========== */
QMainWindow {
    background-color: #F8FAFC;
}

/* ========== 导航栏 ========== */
QTabWidget::pane {
    border: none;
    background-color: #FFFFFF;
    border-radius: 12px;
}

QTabBar::tab {
    background-color: #E2E8F0;
    color: #64748B;
    padding: 12px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #10B981;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #F1F5F9;
}

/* ========== 按钮样式 ========== */
QPushButton {
    background-color: #10B981;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 500;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #059669;
}

QPushButton:pressed {
    background-color: #047857;
}

QPushButton:disabled {
    background-color: #CBD5E1;
    color: #94A3B8;
}

/* 主要按钮 - 绿色 */
QPushButton[cssClass="primary"] {
    background-color: #10B981;
}

QPushButton[cssClass="primary"]:hover {
    background-color: #059669;
}

/* 次要按钮 - 蓝色 */
QPushButton[cssClass="secondary"] {
    background-color: #3B82F6;
}

QPushButton[cssClass="secondary"]:hover {
    background-color: #2563EB;
}

/* 警告按钮 - 橙色 */
QPushButton[cssClass="warning"] {
    background-color: #F59E0B;
}

QPushButton[cssClass="warning"]:hover {
    background-color: #D97706;
}

/* 危险按钮 - 红色 */
QPushButton[cssClass="danger"] {
    background-color: #EF4444;
}

QPushButton[cssClass="danger"]:hover {
    background-color: #DC2626;
}

/* 图标按钮 */
QPushButton[cssClass="icon"] {
    background-color: transparent;
    color: #64748B;
    padding: 8px;
    min-width: 40px;
    max-width: 40px;
    border-radius: 20px;
}

QPushButton[cssClass="icon"]:hover {
    background-color: #E2E8F0;
    color: #10B981;
}

/* ========== 卡片容器 ========== */
QFrame[cssClass="card"] {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

/* ========== 标签样式 ========== */
QLabel {
    color: #1E293B;
}

QLabel[cssClass="title"] {
    font-size: 24px;
    font-weight: 700;
    color: #0F172A;
}

QLabel[cssClass="subtitle"] {
    font-size: 16px;
    font-weight: 600;
    color: #334155;
}

QLabel[cssClass="caption"] {
    font-size: 12px;
    color: #64748B;
}

/* 统计数字 */
QLabel[cssClass="stat-value"] {
    font-size: 36px;
    font-weight: 700;
    color: #10B981;
}

QLabel[cssClass="stat-label"] {
    font-size: 14px;
    color: #64748B;
}

/* 状态标签 */
QLabel[cssClass="state-standing"] {
    color: #10B981;
    font-weight: 600;
}

QLabel[cssClass="state-squatting"] {
    color: #F59E0B;
    font-weight: 600;
}

/* ========== 进度条 ========== */
QProgressBar {
    background-color: #E2E8F0;
    border-radius: 6px;
    height: 12px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #10B981;
    border-radius: 6px;
}

/* ========== 输入框 ========== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #FFFFFF;
    border: 2px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 12px;
    color: #1E293B;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #10B981;
}

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border-color: #CBD5E1;
}

/* ========== 滑块 ========== */
QSlider::groove:horizontal {
    background-color: #E2E8F0;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background-color: #10B981;
    width: 20px;
    height: 20px;
    margin: -6px 0;
    border-radius: 10px;
}

QSlider::handle:horizontal:hover {
    background-color: #059669;
}

QSlider::sub-page:horizontal {
    background-color: #10B981;
    border-radius: 4px;
}

/* ========== 表格 ========== */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #D1FAE5;
    color: #047857;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: 600;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background-color: #F1F5F9;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #FFFFFF;
    color: #64748B;
    border-top: 1px solid #E2E8F0;
}

QStatusBar::item {
    border: none;
}

/* ========== 分组框 ========== */
QGroupBox {
    font-weight: 600;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 24px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #334155;
}

/* ========== 消息框 ========== */
QMessageBox {
    background-color: #FFFFFF;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""

# 颜色常量
class Colors:
    """清新活力主题颜色常量"""
    # 主色调
    PRIMARY = "#10B981"        # 清新绿
    PRIMARY_HOVER = "#059669"
    PRIMARY_PRESSED = "#047857"
    
    # 次要色
    SECONDARY = "#3B82F6"      # 活力蓝
    SECONDARY_HOVER = "#2563EB"
    
    # 强调色
    ACCENT = "#F59E0B"         # 活力橙
    ACCENT_HOVER = "#D97706"
    
    # 状态色
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"
    
    # 背景色
    BG_PRIMARY = "#F8FAFC"
    BG_SECONDARY = "#FFFFFF"
    BG_TERTIARY = "#F1F5F9"
    
    # 文字色
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#475569"
    TEXT_MUTED = "#64748B"
    TEXT_LIGHT = "#94A3B8"
    
    # 边框色
    BORDER = "#E2E8F0"
    BORDER_HOVER = "#CBD5E1"


def apply_theme(app):
    """
    应用清新活力主题到应用程序
    
    Args:
        app: QApplication 实例
    """
    app.setStyleSheet(FRESH_THEME)

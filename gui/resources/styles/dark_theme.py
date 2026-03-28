"""
深色霓虹主题样式 (Fitness Pro Dark)

设计方向:
- 深色背景 + 霓虹强调色
- 主色调: 霓虹绿 (#22C55E) - 深蹲
- 次色调: 霓虹蓝 (#3B82F6) - 开合跳
- 强调色: 霓虹橙 (#F97316) - 警告
"""

# 深色霓虹主题 QSS 样式表
DARK_THEME = """
/* ========== CSS 变量定义 (通过 QProxyStyle 实现) ========== */

QWidget {
    font-family: "Inter", "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #FFFFFF;
}

/* ========== 主窗口 ========== */
QMainWindow {
    background-color: #0D0D0F;
}

/* ========== 中央控件 ========== */
QTabWidget {
    background-color: #0D0D0F;
}

QTabWidget::pane {
    border: none;
    background-color: #0D0D0F;
}

/* ========== 标签栏 ========== */
QTabBar::tab {
    background-color: #161619;
    color: #A1A1AA;
    padding: 14px 28px;
    margin-right: 4px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-weight: 500;
    font-size: 14px;
}

QTabBar::tab:selected {
    background-color: #1E1E22;
    color: #22C55E;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #252529;
    color: #FFFFFF;
}

/* ========== 按钮样式 ========== */
QPushButton {
    background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 14px;
    min-width: 100px;
}

QPushButton:hover {
    background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
    border: 1px solid #22C55E;
}

QPushButton:pressed {
    background: linear-gradient(135deg, #16A34A 0%, #15803D 100%);
}

QPushButton:disabled {
    background: #27272A;
    color: #71717A;
}

/* 次要按钮 - 蓝色 */
QPushButton[cssClass="secondary"] {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
}

QPushButton[cssClass="secondary"]:hover {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
    border: 1px solid #3B82F6;
}

/* 警告按钮 - 橙色 */
QPushButton[cssClass="warning"] {
    background: linear-gradient(135deg, #F97316 0%, #EA580C 100%);
}

QPushButton[cssClass="warning"]:hover {
    background: linear-gradient(135deg, #F97316 0%, #EA580C 100%);
    border: 1px solid #F97316;
}

/* 危险按钮 - 红色 */
QPushButton[cssClass="danger"] {
    background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
}

QPushButton[cssClass="danger"]:hover {
    background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
    border: 1px solid #EF4444;
}

/* 图标按钮 */
QPushButton[cssClass="icon"] {
    background-color: transparent;
    color: #A1A1AA;
    padding: 10px;
    min-width: 44px;
    max-width: 44px;
    border-radius: 22px;
    border: 1px solid #3F3F46;
}

QPushButton[cssClass="icon"]:hover {
    background-color: #252529;
    color: #22C55E;
    border-color: #22C55E;
}

/* 霓虹按钮 */
QPushButton[cssClass="neon-green"] {
    background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
    border-radius: 12px;
    padding: 14px 28px;
    font-weight: 600;
    font-size: 15px;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

QPushButton[cssClass="neon-green"]:hover {
    background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
    border: 1px solid #22C55E;
}

QPushButton[cssClass="neon-blue"] {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
    border-radius: 12px;
    padding: 14px 28px;
    font-weight: 600;
    font-size: 15px;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

QPushButton[cssClass="neon-blue"]:hover {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
    border: 1px solid #3B82F6;
}

/* ========== 卡片容器 ========== */
QFrame[cssClass="card"] {
    background-color: #161619;
    border-radius: 16px;
    border: 1px solid #27272A;
}

QFrame[cssClass="card-glow"] {
    background-color: #161619;
    border-radius: 16px;
    border: 1px solid #27272A;
}

/* ========== 标签样式 ========== */
QLabel {
    color: #FFFFFF;
    background: transparent;
}

QLabel[cssClass="title"] {
    font-size: 24px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel[cssClass="subtitle"] {
    font-size: 16px;
    font-weight: 600;
    color: #E4E4E7;
}

QLabel[cssClass="caption"] {
    font-size: 12px;
    color: #71717A;
}

QLabel[cssClass="muted"] {
    font-size: 14px;
    color: #A1A1AA;
}

/* 统计数字 */
QLabel[cssClass="stat-value"] {
    font-size: 48px;
    font-weight: 700;
    color: #22C55E;
}

/* ========== 进度条 ========== */
QProgressBar {
    background-color: #27272A;
    border-radius: 8px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: linear-gradient(90deg, #22C55E, #16A34A);
    border-radius: 8px;
}

/* ========== 输入框 ========== */
QLineEdit {
    background-color: #1E1E22;
    border: 2px solid #3F3F46;
    border-radius: 8px;
    padding: 10px 14px;
    color: #FFFFFF;
    min-height: 28px;
}

QLineEdit:focus {
    border-color: #22C55E;
}

QLineEdit:hover {
    border-color: #52525B;
}

QLineEdit::placeholder {
    color: #71717A;
}

/* ========== 下拉框 ========== */
QComboBox {
    background-color: #1E1E22;
    border: 2px solid #3F3F46;
    border-radius: 8px;
    padding: 10px 14px;
    padding-right: 36px;
    color: #FFFFFF;
    min-height: 28px;
}

QComboBox:focus {
    border-color: #22C55E;
}

QComboBox:hover {
    border-color: #52525B;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border: none;
    border-left: 1px solid #3F3F46;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #252529;
}

QComboBox::drop-down:hover {
    background-color: #2E2E33;
}

QComboBox::down-arrow {
    image: none;
    width: 12px;
    height: 12px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #A1A1AA;
}

QComboBox QAbstractItemView {
    background-color: #1E1E22;
    border: 2px solid #3F3F46;
    border-radius: 8px;
    padding: 6px;
    selection-background-color: rgba(34, 197, 94, 0.2);
    selection-color: #22C55E;
    outline: none;
    color: #FFFFFF;
}

/* ========== 数字输入框 ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #1E1E22;
    border: 2px solid #3F3F46;
    border-radius: 8px;
    padding: 10px 14px;
    padding-right: 32px;
    color: #FFFFFF;
    min-height: 28px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #22C55E;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #52525B;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #252529;
    border: none;
    border-radius: 4px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #2E2E33;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 10px;
    height: 10px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #A1A1AA;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 10px;
    height: 10px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #A1A1AA;
}

/* ========== 滑块 ========== */
QSlider::groove:horizontal {
    background-color: #27272A;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background-color: #22C55E;
    width: 22px;
    height: 22px;
    margin: -7px 0;
    border-radius: 11px;
    border: 2px solid #FFFFFF;
}

QSlider::handle:horizontal:hover {
    background-color: #16A34A;
}

QSlider::sub-page:horizontal {
    background: linear-gradient(90deg, #22C55E, #16A34A);
    border-radius: 4px;
}

/* ========== 表格 ========== */
QTableWidget {
    background-color: #161619;
    border: 1px solid #27272A;
    border-radius: 12px;
    gridline-color: #27272A;
    color: #FFFFFF;
}

QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #27272A;
    background-color: #161619;
}

QTableWidget::item:selected {
    background-color: rgba(34, 197, 94, 0.2);
    color: #22C55E;
}

QHeaderView::section {
    background-color: #1E1E22;
    color: #E4E4E7;
    font-weight: 600;
    padding: 12px;
    border: none;
    border-bottom: 2px solid #27272A;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background-color: #1E1E22;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #3F3F46;
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #52525B;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #161619;
    color: #71717A;
    border-top: 1px solid #27272A;
}

QStatusBar::item {
    border: none;
}

/* ========== 分组框 ========== */
QGroupBox {
    font-weight: 600;
    color: #E4E4E7;
    border: 1px solid #27272A;
    border-radius: 12px;
    margin-top: 20px;
    padding-top: 24px;
    padding-left: 16px;
    padding-right: 16px;
    padding-bottom: 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    top: 2px;
    padding: 0 10px;
    color: #22C55E;
}

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 12px;
    color: #FFFFFF;
}

QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border: 2px solid #3F3F46;
    border-radius: 6px;
    background-color: #1E1E22;
}

QCheckBox::indicator:hover {
    border-color: #22C55E;
    background-color: rgba(34, 197, 94, 0.1);
}

QCheckBox::indicator:checked {
    background-color: #22C55E;
    border-color: #22C55E;
    image: none;
}

QCheckBox::indicator:checked:hover {
    background-color: #16A34A;
    border-color: #16A34A;
}

QCheckBox::indicator:disabled {
    background-color: #27272A;
    border-color: #3F3F46;
}

/* ========== 消息框 ========== */
QMessageBox {
    background-color: #161619;
}

QMessageBox QLabel {
    color: #FFFFFF;
}

QMessageBox QPushButton {
    min-width: 100px;
}

/* ========== 工具提示 ========== */
QToolTip {
    background-color: #252529;
    color: #FFFFFF;
    border: 1px solid #3F3F46;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

/* ========== 菜单 ========== */
QMenu {
    background-color: #1E1E22;
    border: 1px solid #27272A;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 10px 16px;
    border-radius: 4px;
    color: #FFFFFF;
}

QMenu::item:selected {
    background-color: rgba(34, 197, 94, 0.2);
    color: #22C55E;
}

QMenu::separator {
    height: 1px;
    background-color: #27272A;
    margin: 6px 0;
}
"""


# 颜色常量类
class NeonColors:
    """霓虹深色主题颜色常量"""

    # 主背景层
    BG_PRIMARY = "#0D0D0F"
    BG_SECONDARY = "#161619"
    BG_TERTIARY = "#1E1E22"
    BG_ELEVATED = "#252529"

    # 文字层
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#A1A1AA"
    TEXT_MUTED = "#71717A"

    # 深蹲霓虹色 (绿色)
    NEON_GREEN = "#22C55E"
    NEON_GREEN_GLOW = "rgba(34, 197, 94, 0.3)"
    NEON_GREEN_INTENSE = "#16A34A"

    # 开合跳霓虹色 (蓝色)
    NEON_BLUE = "#3B82F6"
    NEON_BLUE_GLOW = "rgba(59, 130, 246, 0.3)"
    NEON_BLUE_INTENSE = "#2563EB"

    # 警告/错误霓虹色
    NEON_ORANGE = "#F97316"
    NEON_RED = "#EF4444"

    # 边框
    BORDER_SUBTLE = "#27272A"
    BORDER_DEFAULT = "#3F3F46"
    BORDER_HOVER = "#52525B"


# 字体常量
class FontSizes:
    """字体大小常量"""

    XS = "12px"
    SM = "14px"
    BASE = "14px"
    LG = "18px"
    XL = "20px"
    XXL = "24px"
    XXXL = "36px"
    STAT = "48px"
    GIANT = "60px"


def apply_dark_theme(app):
    """
    应用深色霓虹主题到应用程序

    Args:
        app: QApplication 实例
    """
    app.setStyleSheet(DARK_THEME)

#!/usr/bin/env python3
"""
Fitness Pose Validator - GUI 启动脚本

基于 PyQt6 的现代化图形用户界面入口。

使用方法:
    python run_gui.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """检查依赖是否安装"""
    missing = []
    
    try:
        import PyQt6
    except ImportError:
        missing.append("PyQt6")
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    
    try:
        import mediapipe
    except ImportError:
        missing.append("mediapipe")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")
    
    if missing:
        print("=" * 60)
        print("错误: 缺少必要的依赖包")
        print("=" * 60)
        print("\n缺少以下依赖:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\n请运行以下命令安装依赖:")
        print(f"  pip install -r requirements.txt")
        print("\n或者单独安装:")
        print(f"  pip install {' '.join(missing)}")
        print("=" * 60)
        sys.exit(1)


def main():
    """程序入口"""
    print("=" * 60)
    print("Fitness Pose Validator v2.0.0 (PyQt6 GUI)")
    print("基于 MediaPipe 的实时健身动作检测系统")
    print("=" * 60)
    
    # 检查依赖
    check_dependencies()
    
    # 导入 PyQt6
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("Fitness Pose Validator")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("OhMyOpenCode")
    
    # 设置字体
    font = app.font()
    font.setFamily("Microsoft YaHei")
    app.setFont(font)
    
    # 导入主窗口
    from gui.main_window import MainWindow
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    print("\nGUI 窗口已启动")
    print("按 '开始训练' 按钮开始检测")
    
    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
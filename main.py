#!/usr/bin/env python3
"""
Fitness Pose Validator - 主入口

基于 MediaPipe 的实时健身动作检测与计数系统。
支持深蹲动作的实时检测、计数和数据持久化。

使用方法:
    python main.py
    
快捷键:
    q / ESC - 退出程序
"""

import sys
import time

import cv2
import numpy as np

from src.config import Config
from src.database import Database
from src.pose_detector import PoseDetector
from src.squat_counter import SquatCounter
from src.visualizer import Visualizer


class FitnessPoseValidator:
    """
    健身姿态验证器主类
    
    整合姿态检测、计数逻辑、数据存储和可视化渲染。
    """
    
    def __init__(self):
        """初始化各组件"""
        self._init_database()
        self._init_pose_detector()
        self._init_camera()
        self._init_session()
        self._init_visualizer()
    
    def _init_database(self) -> None:
        """初始化数据库"""
        self._database = Database()
        print(f"数据库已初始化: {Config.DATABASE_PATH}")
    
    def _init_pose_detector(self) -> None:
        """初始化姿态检测器"""
        try:
            self._pose_detector = PoseDetector()
            print("姿态检测模型加载成功")
        except FileNotFoundError as e:
            print(f"错误: {e}")
            sys.exit(1)
    
    def _init_camera(self) -> None:
        """初始化摄像头"""
        print("\n正在打开摄像头...")
        
        # 尝试打开摄像头
        self._cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        
        if not self._cap.isOpened():
            print("错误: 无法打开摄像头")
            print("请检查:")
            print("  1. 摄像头是否已连接")
            print("  2. 是否有其他程序占用摄像头")
            sys.exit(1)
        
        # 配置摄像头参数
        width, height = Config.CAMERA_RESOLUTION
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
        
        # 等待摄像头初始化
        print(f"等待摄像头初始化 ({Config.CAMERA_INIT_WAIT}秒)...")
        time.sleep(Config.CAMERA_INIT_WAIT)
        
        # 预读取几帧以稳定摄像头
        for _ in range(5):
            self._cap.read()
            time.sleep(0.1)
        
        # 获取实际参数
        self._frame_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._frame_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = int(self._cap.get(cv2.CAP_PROP_FPS)) or Config.CAMERA_FPS
        
        print(f"摄像头启动成功!")
        print(f"分辨率: {self._frame_width}x{self._frame_height}, FPS: {self._fps}")
    
    def _init_session(self) -> None:
        """初始化训练会话"""
        self._session_id = self._database.create_session()
        self._squat_counter = SquatCounter(
            database=self._database,
            session_id=self._session_id,
        )
        print(f"训练会话已创建: Session ID = {self._session_id}")
    
    def _init_visualizer(self) -> None:
        """初始化可视化渲染器"""
        self._visualizer = Visualizer(self._frame_width, self._frame_height)
        
        # 创建显示窗口
        cv2.namedWindow(Config.WINDOW_TITLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(Config.WINDOW_TITLE, *Config.WINDOW_SIZE)
        
        print(f"\n按 'q' 或 'ESC' 键退出程序")
    
    def run(self) -> None:
        """运行主循环"""
        frame_count = 0
        pose_count = 0
        
        try:
            while self._cap.isOpened():
                ret, frame = self._cap.read()
                if not ret:
                    print("警告：无法读取视频帧")
                    break
                
                # 旋转帧（摄像头竖屏模式）
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                
                # 转换颜色空间
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                timestamp_ms = int((frame_count + 1) * 1000 / self._fps)
                pose_data = self._pose_detector.detect(rgb_frame, timestamp_ms)
                
                frame_count += 1
                
                metrics = None
                if pose_data:
                    pose_count += 1
                    metrics = self._squat_counter.update(pose_data)
                
                frame = self._visualizer.render_frame(
                    frame, pose_data, metrics, frame_count, pose_count
                )
                
                # 显示帧
                cv2.imshow(Config.WINDOW_TITLE, frame)
                
                # 检查退出条件
                if self._should_exit():
                    break
                    
        except KeyboardInterrupt:
            print("\n收到中断信号")
        finally:
            self._cleanup(frame_count, pose_count)
    
    def _should_exit(self) -> bool:
        """检查是否应该退出程序"""
        key = cv2.waitKey(10) & 0xFF
        if key == ord('q') or key == 27:  # q 或 ESC
            return True
        
        # 检查窗口是否被关闭
        if cv2.getWindowProperty(Config.WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:
            return True
        
        return False
    
    def _cleanup(self, frame_count: int, pose_count: int) -> None:
        """清理资源"""
        # 释放摄像头
        self._cap.release()
        
        # 关闭窗口
        cv2.destroyAllWindows()
        
        # 保存数据
        self._squat_counter.close()
        self._database.update_session(
            self._session_id, 
            frame_count, 
            self._squat_counter.count
        )
        
        # 关闭姿态检测器
        self._pose_detector.close()
        
        # 打印统计信息
        print(f"\n程序已退出")
        print(f"总帧数: {frame_count}, 检测到姿态: {pose_count}")
        print(f"深蹲计数: {self._squat_counter.count}")
        print(f"数据已保存到: {Config.DATABASE_PATH} (Session ID: {self._session_id})")


def main():
    """程序入口"""
    print("=" * 50)
    print("Fitness Pose Validator v1.0.0")
    print("基于 MediaPipe 的实时健身动作检测系统")
    print("=" * 50)
    
    app = FitnessPoseValidator()
    app.run()


if __name__ == "__main__":
    main()
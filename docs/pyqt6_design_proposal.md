# PyQt6 界面设计方案

## 项目概述

为 Fitness Pose Validator 项目添加现代化的 PyQt6 图形用户界面，替代当前基于 OpenCV 窗口的交互方式，提供更好的用户体验和功能扩展性。

---

## 现有功能分析

### 核心模块
| 模块 | 功能 | UI 需求 |
|------|------|---------|
| `main.py` | 实时训练入口 | 视频显示、控制按钮、实时统计 |
| `analyze.py` | 历史数据分析 | 会话列表、图表展示、数据导出 |
| `src/pose_detector.py` | MediaPipe 姿态检测 | 后台运行，无需直接 UI |
| `src/squat_counter.py` | 深蹲计数逻辑 | 实时计数显示 |
| `src/visualizer.py` | OpenCV 渲染 | 迁移到 PyQt6 渲染 |
| `src/database.py` | 数据库操作 | 数据查询和展示 |
| `src/analyzer.py` | 统计分析 | 图表集成 (matplotlib) |

---

## 界面架构设计

### 整体结构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Fitness Pose Validator                       │
├─────────────────────────────────────────────────────────────────┤
│  [训练]  [历史记录]  [设置]                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────────────────────────┐  ┌─────────────────────────┐   │
│   │                             │  │      实时统计面板        │   │
│   │      实时视频显示区域        │  │  ┌───────────────────┐  │   │
│   │   (姿态骨骼 + 角度标注)      │  │  │ 深蹲次数: 0       │  │   │
│   │                             │  │  │ 当前状态: 站立    │  │   │
│   │                             │  │  │ 左膝角度: 175°   │  │   │
│   │                             │  │  │ 右膝角度: 172°   │  │   │
│   │                             │  │  │ 平均角度: 173°   │  │   │
│   │                             │  │  └───────────────────┘  │   │
│   │                             │  │                          │   │
│   │                             │  │  ┌───────────────────┐  │   │
│   │                             │  │  │    角度变化曲线    │  │   │
│   │                             │  │  │   (实时折线图)    │  │   │
│   │                             │  │  └───────────────────┘  │   │
│   └─────────────────────────────┘  └─────────────────────────┘   │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────────┐│
│   │  [开始训练]  [暂停]  [重置计数]  [保存截图]     FPS: 30      ││
│   └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│   状态栏: 摄像头已连接 | 会话ID: 5 | 运行时间: 00:02:35          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 页面详细设计

### 1. 训练页面 (主页面)

#### 视频显示区域
- **位置**: 左侧主区域 (约 70% 宽度)
- **功能**:
  - 实时显示摄像头画面
  - 叠加姿态骨骼渲染
  - 显示膝关节角度标注
  - 支持全屏切换

#### 实时统计面板
- **位置**: 右侧面板 (约 30% 宽度)
- **组件**:
  | 组件 | 类型 | 数据来源 |
  |------|------|----------|
  | 深蹲次数 | QLabel (大字体) | `SquatMetrics.rep_count` |
  | 当前状态 | QLabel (带颜色) | `SquatMetrics.state` |
  | 左膝角度 | QProgressBar + QLabel | `SquatMetrics.left_knee_angle` |
  | 右膝角度 | QProgressBar + QLabel | `SquatMetrics.right_knee_angle` |
  | 平均角度 | QProgressBar + QLabel | `SquatMetrics.avg_knee_angle` |
  | 角度曲线 | Matplotlib FigureCanvas | 实时角度数据 |

#### 控制按钮栏
| 按钮 | 图标 | 功能 | 状态依赖 |
|------|------|------|----------|
| 开始训练 | ▶️ | 启动摄像头和检测 | 初始/停止状态 |
| 暂停 | ⏸️ | 暂停检测（保持摄像头） | 运行状态 |
| 停止 | ⏹️ | 停止训练并保存数据 | 运行/暂停状态 |
| 重置计数 | 🔄 | 重置深蹲计数为 0 | 任意状态 |
| 保存截图 | 📷 | 保存当前帧为图片 | 运行状态 |
| 全屏 | ⛶ | 全屏显示视频 | 任意状态 |

#### 状态栏
- 摄像头状态 (已连接/未连接/错误)
- 当前会话 ID
- 运行时间 (格式: HH:MM:SS)
- 实时 FPS

---

### 2. 历史记录页面

#### 页面布局
```
┌─────────────────────────────────────────────────────────────────┐
│  历史训练记录                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │                      │  │                                   │ │
│  │   会话列表            │  │       会话详情                    │ │
│  │   (QTableWidget)     │  │                                   │ │
│  │                      │  │   基本信息:                       │ │
│  │  ID | 时间 | 深蹲数   │  │   - 时长: 5分32秒                │ │
│  │  ──────────────────  │  │   - 总帧数: 9960                 │ │
│  │   5  | 03-19 14:30 | 15 │  │   - 深蹲次数: 15              │ │
│  │   4  | 03-19 10:15 | 22 │  │   - 质量评分: 85/100          │ │
│  │   3  | 03-18 16:45 | 18 │  │                                   │ │
│  │   2  | 03-18 09:20 | 12 │  │   ┌───────────────────────┐   │ │
│  │   1  | 03-17 20:00 | 8  │  │   │                       │   │ │
│  │                      │  │   │   角度变化图表           │   │ │
│  │  [刷新] [删除选中]    │  │   │   (Matplotlib)          │   │ │
│  │                      │  │   │                       │   │ │
│  └──────────────────────┘  │   └───────────────────────┘   │ │
│                            │                                   │ │
│                            │   每次深蹲详情:                    │ │
│                            │   ┌───────────────────────────┐  │ │
│                            │   │ # | 时长 | 最小角度 | 范围 │  │ │
│                            │   │ 1 | 2.3s |   75°   | 95° │  │ │
│                            │   │ 2 | 2.1s |   78°   | 92° │  │ │
│                            │   └───────────────────────────┘  │ │
│                            └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 功能按钮
| 按钮 | 功能 |
|------|------|
| 刷新 | 重新加载会话列表 |
| 删除选中 | 删除选中的训练记录 (需确认) |
| 导出报告 | 导出选中会话的分析报告 (PDF/CSV) |
| 对比分析 | 多选会话进行对比 |

---

### 3. 设置页面

#### 配置分类

**摄像头设置**
| 配置项 | 控件类型 | 默认值 | 说明 |
|--------|----------|--------|------|
| 摄像头索引 | QSpinBox | 0 | 选择摄像头设备 |
| 分辨率 | QComboBox | 1280x720 | 预设分辨率选项 |
| 帧率 | QSpinBox | 30 | 目标 FPS |

**检测参数**
| 配置项 | 控件类型 | 默认值 | 范围 |
|--------|----------|--------|------|
| 站立阈值 | QSlider + QSpinBox | 165° | 120-180 |
| 下蹲阈值 | QSlider + QSpinBox | 90° | 45-120 |
| 检测置信度 | QSlider | 0.5 | 0.1-1.0 |
| 跟踪置信度 | QSlider | 0.5 | 0.1-1.0 |

**界面设置**
| 配置项 | 控件类型 | 默认值 |
|--------|----------|--------|
| 主题 | QComboBox | 浅色/深色 |
| 视频旋转 | QCheckBox | 勾选 (90° 顺时针) |
| 显示骨骼 | QCheckBox | 勾选 |
| 显示角度 | QCheckBox | 勾选 |

**数据设置**
| 配置项 | 控件类型 | 默认值 |
|--------|----------|--------|
| 数据库路径 | QLineEdit + 浏览按钮 | ./data/fitness_data.db |
| 缓冲区大小 | QSpinBox | 100 |
| 自动保存间隔 | QSpinBox | 0 (禁用) |

---

## 按钮状态机

```
                    ┌─────────────┐
                    │   初始状态   │
                    │  (未连接)    │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    [开始训练] ✅     [设置] ✅      [历史] ✅
            │
            ▼
    ┌───────────────┐      [暂停]      ┌───────────────┐
    │   运行状态     │ ──────────────▶ │   暂停状态     │
    │  (检测中)      │ ◀────────────── │  (摄像头保持)  │
    └───────┬───────┘     [继续]       └───────┬───────┘
            │                                  │
            │ [停止]                           │ [停止]
            ▼                                  ▼
    ┌───────────────┐                  ┌───────────────┐
    │   停止状态     │                  │   停止状态     │
    │  (数据已保存)  │                  │  (数据已保存)  │
    └───────────────┘                  └───────────────┘
```

### 按钮启用/禁用规则

| 按钮 | 初始 | 运行 | 暂停 | 停止 |
|------|------|------|------|------|
| 开始训练 | ✅ | ❌ | ❌ | ✅ |
| 暂停 | ❌ | ✅ | ❌ | ❌ |
| 继续 | ❌ | ❌ | ✅ | ❌ |
| 停止 | ❌ | ✅ | ✅ | ❌ |
| 重置计数 | ❌ | ✅ | ✅ | ❌ |
| 保存截图 | ❌ | ✅ | ✅ | ❌ |

---

## 技术实现方案

### 文件结构

```
fitness-pose-validator/
├── gui/                          # 新增 GUI 模块
│   ├── __init__.py
│   ├── main_window.py           # 主窗口
│   ├── pages/                   # 页面组件
│   │   ├── __init__.py
│   │   ├── training_page.py     # 训练页面
│   │   ├── history_page.py      # 历史记录页面
│   │   └── settings_page.py     # 设置页面
│   ├── widgets/                 # 自定义控件
│   │   ├── __init__.py
│   │   ├── video_widget.py      # 视频显示控件
│   │   ├── stats_panel.py       # 统计面板
│   │   └── angle_chart.py       # 角度图表
│   ├── workers/                 # 后台工作线程
│   │   ├── __init__.py
│   │   └── detection_worker.py  # 检测工作线程
│   └── resources/               # 资源文件
│       ├── icons/               # 图标
│       └── styles/              # 样式表
├── run_gui.py                   # GUI 启动脚本
└── requirements.txt             # 更新依赖
```

### 核心类设计

#### 1. MainWindow (主窗口)
```python
class MainWindow(QMainWindow):
    """主窗口，管理页面切换和全局状态"""
    
    def __init__(self):
        self.stacked_widget = QStackedWidget()
        self.training_page = TrainingPage()
        self.history_page = HistoryPage()
        self.settings_page = SettingsPage()
        
    def switch_page(self, page_name: str):
        """切换当前显示的页面"""
        pass
```

#### 2. TrainingPage (训练页面)
```python
class TrainingPage(QWidget):
    """训练页面，包含视频显示和控制面板"""
    
    # 信号定义
    start_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    
    def __init__(self):
        self.video_widget = VideoWidget()
        self.stats_panel = StatsPanel()
        self.control_bar = ControlBar()
        
    def update_frame(self, frame: np.ndarray):
        """更新视频帧显示"""
        pass
    
    def update_metrics(self, metrics: SquatMetrics):
        """更新统计数据"""
        pass
```

#### 3. DetectionWorker (检测工作线程)
```python
class DetectionWorker(QThread):
    """后台线程，处理视频捕获和姿态检测"""
    
    # 信号定义
    frame_ready = pyqtSignal(np.ndarray)      # 新帧可用
    metrics_updated = pyqtSignal(object)       # 指标更新
    error_occurred = pyqtSignal(str)           # 错误发生
    
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.squat_counter = SquatCounter()
        self.cap = None
        self.running = False
        
    def run(self):
        """主循环：捕获 -> 检测 -> 发射信号"""
        pass
    
    def stop(self):
        """停止检测"""
        pass
```

#### 4. VideoWidget (视频显示控件)
```python
class VideoWidget(QLabel):
    """自定义视频显示控件"""
    
    def __init__(self):
        super().__init__()
        self.setScaledContents(True)
        self.setMinimumSize(640, 480)
        
    def update_frame(self, frame: np.ndarray):
        """将 OpenCV 帧转换为 QPixmap 并显示"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(q_img))
```

### 依赖更新

```txt
# requirements.txt 新增
PyQt6>=6.5.0
PyQt6-Qt6>=6.5.0
matplotlib>=3.7.0  # 已有
```

---

## Git 管理策略

### 分支策略
```
main
  └── feature/pyqt6-gui
        ├── feature/pyqt6-training-page
        ├── feature/pyqt6-history-page
        └── feature/pyqt6-settings-page
```

### 提交计划

| 阶段 | 提交信息 | 内容 |
|------|----------|------|
| 1 | `feat(gui): 初始化 PyQt6 项目结构` | 创建 gui/ 目录、__init__.py、依赖更新 |
| 2 | `feat(gui): 实现主窗口框架` | MainWindow + 页面切换 |
| 3 | `feat(gui): 实现视频显示控件` | VideoWidget + DetectionWorker |
| 4 | `feat(gui): 实现训练页面` | 统计面板 + 控制按钮 |
| 5 | `feat(gui): 实现历史记录页面` | 会话列表 + 图表展示 |
| 6 | `feat(gui): 实现设置页面` | 配置界面 + 持久化 |
| 7 | `refactor: 迁移 OpenCV 渲染到 PyQt6` | 更新 visualizer.py |
| 8 | `docs: 更新 README` | 使用说明更新 |

### 版本标签
- `v1.0.0` - 当前 OpenCV 版本
- `v2.0.0` - PyQt6 GUI 版本 (计划)

---

## 开发优先级

### Phase 1 - MVP (最小可用版本)
- [x] 主窗口框架
- [ ] 训练页面 (视频 + 基础统计)
- [ ] 开始/停止控制
- [ ] 实时计数显示

### Phase 2 - 完整功能
- [ ] 历史记录页面
- [ ] 图表可视化
- [ ] 设置页面
- [ ] 配置持久化

### Phase 3 - 增强功能
- [ ] 深色主题
- [ ] 多语言支持
- [ ] 数据导出
- [ ] 训练对比分析

---

## 设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| GUI 框架 | PyQt6 | 成熟稳定、跨平台、与 matplotlib 集成好 |
| 视频渲染 | QImage + QLabel | 性能好、与 Qt 原生集成 |
| 后台检测 | QThread | 避免阻塞 UI 线程 |
| 图表库 | Matplotlib | 已有依赖，支持嵌入 Qt |
| 配置存储 | JSON 文件 | 简单、人类可读 |

---

## 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| PyQt6 安装问题 | 开发受阻 | 提供详细的安装指南 |
| 视频帧率下降 | 用户体验差 | 优化渲染管线，使用缓冲 |
| 线程同步问题 | 程序崩溃 | 使用 Qt 信号槽机制 |
| 内存泄漏 | 长时间运行问题 | 正确管理资源释放 |

---

## 下一步行动

等待用户审核通过后，按以下顺序开始开发：

1. 创建 `gui/` 目录结构
2. 更新 `requirements.txt`
3. 实现 `run_gui.py` 启动脚本
4. 实现 `MainWindow` 基础框架
5. 实现 `TrainingPage` MVP

---

**文档版本**: 1.0  
**创建时间**: 2026-03-19  
**状态**: ✅ 已完成实现

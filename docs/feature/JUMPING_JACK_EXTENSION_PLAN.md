# 开合跳动作检测功能扩展方案

## 1. 概述

本文档为在现有 fitness-pose-validator 项目中添加开合跳 (Jumping Jack) 动作检测功能提供客观公正的技术方案。方案基于对现有代码架构的全面分析，综合考虑代码改动量、服务端适配性和 GUI 设计兼容性。

### 1.1 开合跳动作特性

开合跳是一种全身运动，包含以下关键姿态：
- **站立状态**：双腿并拢，双臂下垂于身体两侧
- **开合状态**：双腿分开与肩同宽，双臂上举过头顶

### 1.2 检测原理

开合跳检测基于以下关键角度：
- **髋关节角度** (Hip Angle)：检测双腿开合程度
- **肩关节角度** (Shoulder Angle)：检测双臂上举程度
- **综合状态判断**：结合髋关节和肩关节角度判断动作完成度

---

## 2. 现有架构分析

### 2.1 核心模块结构

```
src/
├── config.py           # 配置常量 (关键点索引、阈值)
├── squat_counter.py    # 深蹲计数器 (状态机模式)
├── pose_detector.py    # MediaPipe 姿态检测
├── database.py         # 本地 SQLite 存储
├── analyzer.py         # 训练数据分析
└── form_analyzer.py    # 动作姿态分析
```

### 2.2 关键点映射 (MediaPipe Pose)

| 部位 | 左半侧 | 右半侧 |
|------|--------|--------|
| 肩部 | 11 | 12 |
| 肘部 | 13 | 14 |
| 腕部 | 15 | 16 |
| 髋部 | 23 | 24 |
| 膝部 | 25 | 26 |
| 踝部 | 27 | 28 |

### 2.3 现有深蹲检测算法

```python
# squat_counter.py 核心逻辑
- 使用 3D 世界坐标计算膝关节角度
- 状态机模式：STANDING <-> SQUATTING
- 峰值检测器：谷值计数法
- EMA 平滑：消除抖动
```

---

## 3. 代码改动量评估

### 3.1 客户端改动

| 模块 | 文件 | 改动类型 | 预估行数 |
|------|------|----------|----------|
| 配置 | `src/config.py` | 新增常量 | ~15 行 |
| 计数器 | `src/jumping_jack_counter.py` | 新建文件 | ~350 行 |
| 数据库 | `src/database.py` | 兼容扩展 | 0 行 (已支持) |
| 检测Worker | `gui/workers/detection_worker.py` | 条件分支 | ~20 行 |
| 训练页面 | `gui/pages/training_page.py` | UI适配 | ~30 行 |
| 配置页面 | `gui/pages/settings_page.py` | 新增选项 | ~20 行 |

**客户端总计：约 435 行新增/修改**

### 3.2 服务端改动

| 模块 | 文件 | 改动类型 | 预估行数 |
|------|------|----------|----------|
| 数据模型 | `server/models.py` | 字段扩展 | ~10 行 |
| 数据库 | `server/database.py` | 兼容扩展 | 0 行 (已支持) |
| 上传路由 | `server/routers/sessions.py` | 兼容扩展 | 0 行 (已支持) |
| Dashboard | `server/routers/dashboard.py` | 指标扩展 | ~30 行 |

**服务端总计：约 40 行新增/修改**

### 3.3 改动评估总结

| 层级 | 改动量 | 复杂度 | 风险 |
|------|--------|--------|------|
| 客户端核心 | 低 | 中 | 低 |
| 客户端GUI | 中 | 低 | 低 |
| 服务端 | 极低 | 低 | 低 |

**结论：代码改动量适中，主要集中在新增计数器模块，存量代码修改量极小。**

---

## 4. 服务端适配性分析

### 4.1 现有服务端架构

```python
# server/models.py - SessionUpload
class SessionUpload(BaseModel):
    version: str = "1.0"
    client: Optional[ClientInfo] = None
    session: Optional[SessionInfo] = None
    records: List[RecordData] = Field(default_factory=list)
    exercise_type: str = "squat"  # ← 兼容扩展
```

### 4.2 兼容性评估

| 现有字段 | 开合跳是否兼容 | 说明 |
|----------|----------------|------|
| `exercise_type` | ✅ 完全兼容 | 扩展为 "jumping_jack" |
| `records` | ✅ 完全兼容 | 复用现有角度记录结构 |
| `session.total_squats` | ⚠️ 需重命名 | 建议改为 `total_reps` |
| `avg_angle` | ⚠️ 需扩展 | 需同时记录髋角和肩角 |

### 4.3 服务端适配方案

**方案 A：最小改动（推荐）**
- `exercise_type` 字段支持 "jumping_jack"
- `records` 复用现有结构，增加 `hip_angle` 和 `shoulder_angle` 字段
- Dashboard 指标改为通用 "次数" 而非 "深蹲数"

**方案 B：完全重构**
- 新增 `exercise_reps` 字段，明确区分不同运动类型
- 缺点：改动量较大，不推荐

**服务端适配结论：方案 A 可行，改动量极小。**

---

## 5. GUI 设计适配性分析

### 5.1 现有 GUI 架构

```
gui/
├── main_window.py          # 标签页管理
├── pages/
│   ├── training_page.py    # 训练控制
│   ├── history_page.py     # 历史记录
│   └── settings_page.py    # 设置
└── widgets/
    ├── video_widget.py     # 视频显示
    ├── stats_panel.py      # 统计面板
    └── angle_chart.py      # 角度图表
```

### 5.2 GUI 改动需求

| 界面 | 改动内容 | 复杂度 |
|------|----------|--------|
| 训练页面 | 运动类型选择器 | 低 |
| 统计面板 | 显示髋关节+肩关节角度 | 中 |
| 角度图表 | 双曲线显示 | 中 |
| 设置页面 | 开合跳阈值配置 | 低 |

### 5.3 设计兼容性评估

| 现有设计元素 | 开合跳适配性 | 说明 |
|--------------|--------------|------|
| 视频骨架显示 | ✅ 完全兼容 | 复用 SQUAT_CONNECTIONS |
| 角度曲线图 | ✅ 完全兼容 | 支持双 Y 轴 |
| 状态指示 | ✅ 完全兼容 | 改为 "并拢/开合" |
| 反馈提示 | ✅ 完全兼容 | 复用现有框架 |

**GUI 适配结论：无需重大改动，可复用现有设计模式。**

---

## 6. 详细实现方案

### 6.1 配置层 (src/config.py)

```python
# 新增配置
class Config:
    # ... 现有配置 ...
    
    # ========== 开合跳配置 ==========
    JUMPING_JACK_CONNECTIONS: Tuple[Tuple[int, int], ...] = (
        (11, 13), (13, 15),  # 左臂
        (12, 14), (14, 16),  # 右臂
        (23, 25), (25, 27),  # 左腿
        (24, 26), (26, 28),  # 右腿
        (23, 24),            # 髋部连接
    )
    
    # 开合跳阈值
    CLOSED_HIP_THRESHOLD: float = 30.0    # 双腿并拢角度
    OPEN_HIP_THRESHOLD: float = 60.0      # 双腿分开角度
    CLOSED_SHOULDER_THRESHOLD: float = 45.0  # 双臂下垂
    OPEN_SHOULDER_THRESHOLD: float = 150.0   # 双臂上举
    
    # 运动类型元组
    EXERCISE_TYPES: Tuple[str, ...] = ("squat", "pushup", "lunge", "jumping_jack")
```

### 6.2 计数器模块 (src/jumping_jack_counter.py)

```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

class JumpingJackState(Enum):
    CLOSED = "CLOSED"    # 并拢状态
    OPEN = "OPEN"        # 开合状态

@dataclass
class JumpingJackMetrics:
    rep_count: int
    state: JumpingJackState
    left_hip_angle: float
    right_hip_angle: float
    left_shoulder_angle: float
    right_shoulder_angle: float
    avg_hip_angle: float
    avg_shoulder_angle: float

class JumpingJackCounter:
    """
    开合跳计数器
    
    检测原理：
    - 髋关节角度：检测双腿开合 (使用髋-膝-踝三点)
    - 肩关节角度：检测双臂上下 (使用肩-肘-腕三点)
    - 状态机：CLOSED <-> OPEN
    """
    
    def __init__(
        self,
        database: Optional[Database] = None,
        session_id: Optional[int] = None,
        closed_hip_threshold: float = Config.CLOSED_HIP_THRESHOLD,
        open_hip_threshold: float = Config.OPEN_HIP_THRESHOLD,
        closed_shoulder_threshold: float = Config.CLOSED_SHOULDER_THRESHOLD,
        open_shoulder_threshold: float = Config.OPEN_SHOULDER_THRESHOLD,
    ):
        # ... 初始化逻辑
    
    @staticmethod
    def calculate_hip_angle(a, b, c) -> float:
        """计算髋关节角度 (髋-膝-踝)"""
        # 使用 3D 坐标
        return calculate_angle_3d(a, b, c)
    
    @staticmethod
    def calculate_shoulder_angle(a, b, c) -> float:
        """计算肩关节角度 (肩-肘-腕)"""
        # 使用 3D 坐标
        return calculate_angle_3d(a, b, c)
    
    def update(self, pose_data: Dict) -> JumpingJackMetrics:
        """更新计数器状态"""
        # 1. 获取关键点
        # 2. 计算髋关节角度
        # 3. 计算肩关节角度
        # 4. 状态机转换判断
        # 5. 计数
        # 6. 记录数据
```

### 6.3 数据模型扩展 (server/models.py)

```python
# 扩展 RecordData
class RecordData(BaseModel):
    timestamp: Optional[str] = None
    left_angle: Optional[float] = None      # 深蹲: 膝角 / 开合跳: 髋角
    right_angle: Optional[float] = None     # 深蹲: 膝角 / 开合跳: 髋角
    avg_angle: Optional[float] = None       # 深蹲: 膝角 / 开合跳: 髋角
    hip_angle: Optional[float] = None       # 新增：髋关节角度
    shoulder_angle: Optional[float] = None  # 新增：肩关节角度
    state: Optional[str] = None
    rep_count: Optional[int] = None
```

### 6.4 GUI 适配

```python
# gui/workers/detection_worker.py - 运动类型路由
class DetectionWorker(QThread):
    def _init_components(self):
        exercise_type = self._get_exercise_type()
        
        if exercise_type == "squat":
            self._counter = SquatCounter(...)
        elif exercise_type == "jumping_jack":
            self._counter = JumpingJackCounter(...)
        # ... 其他类型
```

---

## 7. 实施计划

### 7.1 阶段划分

| 阶段 | 任务 | 预估工时 |
|------|------|----------|
| Phase 1 | 核心算法实现 | 2 小时 |
| Phase 2 | 配置集成 | 0.5 小时 |
| Phase 3 | GUI 适配 | 1 小时 |
| Phase 4 | 服务端兼容 | 0.5 小时 |
| Phase 5 | 测试验证 | 1 小时 |

**总计：约 5 小时**

### 7.2 优先级排序

1. **P0 - 核心功能**
   - `JumpingJackCounter` 类实现
   - 配置常量添加

2. **P1 - 集成**
   - DetectionWorker 路由
   - GUI 训练页面适配

3. **P2 - 增强**
   - 统计面板多角度显示
   - 角度图表优化

4. **P3 - 兼容**
   - 服务端字段扩展
   - 历史记录兼容

---

## 8. 风险评估与缓解

### 8.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 角度计算精度不足 | 中 | 中 | 使用 3D 坐标 + EMA 平滑 |
| 状态误判 | 中 | 中 | 多帧确认 + 峰值检测 |
| 服务端数据不兼容 | 低 | 高 | 字段兼容设计 |

### 8.2 架构风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 运动类型扩展困难 | 低 | 中 | 抽象计数器接口 |
| GUI 耦合度过高 | 中 | 中 | 通过配置驱动 UI |

---

## 9. 总结

### 9.1 方案优势

1. **代码改动量适中**：主要新增文件，存量修改极少
2. **服务端完全兼容**：利用现有 `exercise_type` 字段
3. **GUI 设计可复用**：现有组件可直接适配
4. **架构清晰**：遵循现有状态机模式

### 9.2 关键决策点

| 决策项 | 推荐方案 | 理由 |
|--------|----------|------|
| 计数算法 | 状态机 + 峰值检测 | 与深蹲一致，代码复用 |
| 数据存储 | 兼容现有结构 | 减少服务端改动 |
| GUI 显示 | 双角度曲线 | 直观展示动作 |
| 阈值配置 | 配置文件 | 灵活调整 |

### 9.3 下一步行动

1. 确认运动类型选择 UI 方案
2. 确定髋角/肩角阈值具体数值（需实测）
3. 评估是否需要自适应阈值功能

---

**文档版本**: v1.0  
**创建日期**: 2026-03-26  
**适用版本**: fitness-pose-validator v2.4.0+
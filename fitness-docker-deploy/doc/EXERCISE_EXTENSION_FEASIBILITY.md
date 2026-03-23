# 新健身动作扩展可行性分析报告

> **文档版本**: v1.0  
> **生成日期**: 2026-03-23  
> **适用项目**: Fitness Pose Server  
> **当前状态**: 仅支持深蹲（Squat）动作

---

## 一、现有系统架构分析

### 1.1 技术栈概览

```
┌─────────────────────────────────────────────────────────────┐
│                        系统架构                              │
├─────────────────────────────────────────────────────────────┤
│  客户端 (fitness-pose-validator)                             │
│  ├─ PyQt6 桌面应用                                          │
│  ├─ MediaPipe 姿态检测                                      │
│  ├─ 动作计数逻辑 (状态机)                                   │
│  └─ 数据上传到服务器                                        │
│                          │                                  │
│                          ▼                                  │
│  服务器 (Python HTTP)                                        │
│  ├─ 数据接收与存储 (SQLite)                                 │
│  ├─ Dashboard API (统计数据)                                │
│  ├─ LLM 分析 API                                           │
│  └─ Docker 部署                                             │
│                          │                                  │
│                          ▼                                  │
│  Dashboard (Web 前端)                                       │
│  ├─ ECharts 图表                                            │
│  ├─ 训练概览                                                │
│  ├─ 趋势分析                                                │
│  └─ 能力评估                                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 当前数据库结构

```sql
-- 训练会话表 (当前仅支持深蹲)
uploaded_sessions (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    client_session_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    total_frames INTEGER,
    total_squats INTEGER,      -- ❌ 硬编码为深蹲
    upload_time TEXT,
    raw_data TEXT
)

-- 训练记录表 (逐帧数据)
uploaded_records (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,
    timestamp TEXT,
    left_angle REAL,           -- 左膝角度
    right_angle REAL,          -- 右膝角度
    avg_angle REAL,            -- 平均角度
    state TEXT,                -- STANDING/SQUATTING
    rep_count INTEGER
)
```

### 1.3 代码模块分析

| 模块 | 文件 | 耦合度 | 需要修改 |
|------|------|--------|----------|
| **数据接收** | `server_receiver.py` | 高 | ✅ 表结构、验证逻辑 |
| **Dashboard 分析** | `dashboard_analyzer.py` | 高 | ✅ 查询字段、统计逻辑 |
| **LLM 数据预处理** | `data_preprocessor.py` | 中 | ✅ 数据格式化 |
| **LLM Prompt** | `prompt_templates.py` | 高 | ✅ 深蹲相关描述 |
| **Dashboard 前端** | `app.js`, `charts.js` | 中 | ✅ UI 标签、图表配置 |
| **API 路由** | `dashboard.py`, `llm.py` | 低 | ⚠️ 可能需要新增参数 |

---

## 二、动作分析与选择

### 2.1 候选动作对比

| 动作 | 主要关节 | 角度指标 | 检测难度 | 推荐度 |
|------|----------|----------|----------|--------|
| **俯卧撑 (Push-up)** | 肘关节、肩关节 | 肘部弯曲角度 | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ |
| **弓步蹲 (Lunge)** | 膝关节、髋关节 | 前后腿膝关节角度 | ⭐⭐⭐ 较难 | ⭐⭐⭐⭐ |
| **深蹲跳 (Squat Jump)** | 膝关节、髋关节 | 膝关节角度 + 高度 | ⭐⭐ 中等 | ⭐⭐⭐⭐ |
| **开合跳 (Jumping Jack)** | 肩关节、髋关节 | 四肢展开角度 | ⭐ 简单 | ⭐⭐⭐ |
| **平板支撑 (Plank)** | 肘关节、躯干 | 躯干角度、肘部角度 | ⭐⭐⭐ 较难 | ⭐⭐ |

### 2.2 推荐扩展动作

#### 动作 1: 俯卧撑 (Push-up)

**理由**:
- 与深蹲形成上下肢互补训练
- MediaPipe 检测点覆盖良好（肩、肘、手腕）
- 角度计算逻辑类似，复用性高

**关键检测指标**:
- 肘关节角度（180° 伸直 → 90° 弯曲）
- 躯干直线性（肩-髋-踝连线）
- 状态: UP (手臂伸直) / DOWN (手臂弯曲)

**难度评估**: ⭐⭐ 中等

#### 动作 2: 弓步蹲 (Lunge)

**理由**:
- 进阶下肢训练动作
- 利用现有的膝关节角度检测
- 可以评估单腿稳定性

**关键检测指标**:
- 前腿膝关节角度（90° 为标准）
- 后腿膝关节角度（接近地面为标准）
- 躯干垂直度

**难度评估**: ⭐⭐⭐ 较难（需要区分前后腿）

---

## 三、扩展方案详细设计

### 3.1 数据库扩展方案

#### 方案 A: 统一表结构（推荐）

```sql
-- 扩展会话表
ALTER TABLE uploaded_sessions RENAME TO training_sessions_old;

CREATE TABLE training_sessions (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    client_session_id INTEGER,
    exercise_type TEXT NOT NULL,     -- 'squat', 'pushup', 'lunge'
    start_time TEXT,
    end_time TEXT,
    total_frames INTEGER,
    total_reps INTEGER,              -- 通用的计数字段
    upload_time TEXT,
    raw_data TEXT
);

-- 扩展记录表
CREATE TABLE training_records (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,
    exercise_type TEXT NOT NULL,
    timestamp TEXT,
    
    -- 通用角度字段
    primary_angle REAL,              -- 主要关节角度
    secondary_angle REAL,            -- 次要关节角度（可选）
    symmetry_score REAL,             -- 对称性评分
    
    -- 动作特定字段 (JSON)
    extra_metrics TEXT,              -- {"plank_angle": 175, "depth_cm": 30}
    
    state TEXT,                      -- 动作状态
    rep_count INTEGER
);
```

#### 方案 B: 分表存储

```sql
-- 每种动作独立表
CREATE TABLE squat_sessions (...);
CREATE TABLE pushup_sessions (...);
CREATE TABLE lunge_sessions (...);

-- 联合视图
CREATE VIEW all_sessions AS
    SELECT *, 'squat' as exercise_type FROM squat_sessions
    UNION ALL
    SELECT *, 'pushup' as exercise_type FROM pushup_sessions;
```

**推荐方案 A**，因为：
1. 查询更简单，不需要联合多个表
2. Dashboard 分析器更容易实现跨动作统计
3. 扩展新动作时只需新增记录，不需要新建表

### 3.2 客户端修改点

```
客户端修改清单:
├─ 姿态检测模块
│  ├─ 新增俯卧撑检测逻辑
│  │  ├─ 计算肘关节角度
│  │  ├─ 检测躯干直线性
│  │  └─ 状态机: UP ↔ DOWN
│  │
│  └─ 新增弓步蹲检测逻辑
│     ├─ 区分前后腿
│     ├─ 计算双膝角度
│     └─ 状态机: STANDING ↔ LUNGING
│
├─ 数据上传模块
│  ├─ 添加 exercise_type 字段
│  ├─ 统一角度字段命名
│  └─ 扩展 extra_metrics
│
└─ UI 模块
   ├─ 动作选择界面
   ├─ 动作特定的指导提示
   └─ 实时反馈调整
```

### 3.3 服务器端修改点

#### 3.3.1 `server_receiver.py`

```python
# 需要修改的部分:

# 1. 数据验证
def _validate_data(self, data: Dict[str, Any]):
    required_fields = ["version", "session", "records", "exercise_type"]  # 新增
    exercise_type = data.get("exercise_type")
    if exercise_type not in ["squat", "pushup", "lunge"]:
        raise ValueError(f"不支持的动作类型: {exercise_type}")

# 2. 会话存储
def _save_session(self, client_id: int, data: Dict[str, Any]) -> int:
    # 修改 INSERT 语句，使用通用字段名
    cursor.execute("""
        INSERT INTO training_sessions 
        (..., exercise_type, total_reps, ...)
        VALUES (?, ?, ?, ...)
    """, (...))
```

#### 3.3.2 `dashboard_analyzer.py`

```python
# 需要修改的部分:

def get_overview_stats(self, exercise_type: str = None):
    """添加动作类型过滤"""
    where_clause = ""
    params = []
    
    if exercise_type:
        where_clause = "WHERE exercise_type = ?"
        params = [exercise_type]
    
    # 修改查询使用通用字段
    cursor.execute(f"SELECT SUM(total_reps) FROM training_sessions {where_clause}", params)

def get_trend_data(self, metric: str, period: str, exercise_type: str = None):
    """添加动作类型维度"""
    # 修改查询支持多动作对比

def get_radar_data(self, exercise_type: str = None):
    """雷达图支持按动作类型筛选"""
    # 修改评分维度
```

#### 3.3.3 `data_preprocessor.py`

```python
# 需要修改的部分:

def _prepare_session_data(self, session_ids: List[int]) -> str:
    # 通用化数据格式化
    session = self._get_session(sid)
    exercise_type = session['exercise_type']
    
    # 根据动作类型调整描述
    if exercise_type == 'squat':
        desc = "深蹲"
        metric_name = "下蹲角度"
    elif exercise_type == 'pushup':
        desc = "俯卧撑"
        metric_name = "肘部角度"
    # ...
```

#### 3.3.4 `prompt_templates.py`

```python
# 需要修改的部分:

TEMPLATES = {
    AnalysisType.SESSION: """
你是一位专业的健身教练，擅长分析多种训练动作。
当前分析的是: {exercise_type} 训练数据。

## 动作特定要求
{exercise_specific_instructions}

## 通用分析要求
...
""",
}

# 新增动作特定模板
EXERCISE_INSTRUCTIONS = {
    'squat': {
        'name': '深蹲',
        'key_metrics': ['下蹲深度', '左右对称性', '膝盖稳定性'],
        'standard_angle': '90°',
        'common_issues': ['膝盖内扣', '背部弯曲', '深度不足'],
    },
    'pushup': {
        'name': '俯卧撑',
        'key_metrics': ['肘部弯曲角度', '躯干直线性', '呼吸节奏'],
        'standard_angle': '90°',
        'common_issues': ['塌腰', '肘部外展过大', '颈部姿势'],
    },
    'lunge': {
        'name': '弓步蹲',
        'key_metrics': ['前腿膝关节角度', '后腿膝关节角度', '躯干垂直度'],
        'standard_angle': '90°',
        'common_issues': ['膝盖超过脚尖', '躯干前倾', '重心不稳'],
    },
}
```

---

## 四、前端 Dashboard 修改

### 4.1 需要修改的 UI 元素

| 元素 | 当前 | 修改后 |
|------|------|--------|
| KPI 卡片 - 总深蹲数 | `totalSquats` | `totalReps` + 动作类型选择器 |
| 趋势图标题 | "深蹲次数趋势" | "{动作名称}次数趋势" |
| 深度分布图 | "深度分布" | "{主要指标}分布" |
| 雷达图维度 | 深度、对称性、节奏、稳定性、频率 | 根据动作动态调整 |
| 训练详情 | "膝关节角度曲线" | "{关节}角度曲线" |

### 4.2 新增功能

```javascript
// app.js 新增功能

// 动作类型选择器
const state = {
    currentPage: 'overview',
    currentRange: 'today',
    currentExercise: 'all',  // 新增: 'all', 'squat', 'pushup', 'lunge'
    charts: {},
    sessions: [],
    selectedSession: null,
    isLoading: false
};

// 初始化动作选择器
function initExerciseSelector() {
    const selector = document.getElementById('exerciseSelector');
    selector.innerHTML = `
        <button class="exercise-btn active" data-exercise="all">全部</button>
        <button class="exercise-btn" data-exercise="squat">深蹲</button>
        <button class="exercise-btn" data-exercise="pushup">俯卧撑</button>
        <button class="exercise-btn" data-exercise="lunge">弓步蹲</button>
    `;
    
    selector.querySelectorAll('.exercise-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            state.currentExercise = btn.dataset.exercise;
            loadPage(state.currentPage);
        });
    });
}

// API 调用添加动作类型参数
async function loadOverview() {
    const [overview, trend, radar, sessions] = await Promise.all([
        api.getOverview(null, state.currentExercise),
        api.getTrend('reps', '7d', null, state.currentExercise),
        api.getRadar(null, state.currentExercise),
        api.getRecentSessions(5, null, state.currentExercise)
    ]);
    // ...
}
```

### 4.3 API.js 修改

```javascript
// api.js 修改

const API = {
    // 添加 exercise_type 参数
    async getOverview(clientId = null, exerciseType = null) {
        let url = `${API_BASE}/dashboard/overview`;
        if (clientId) url += `?client_id=${encodeURIComponent(clientId)}`;
        if (exerciseType && exerciseType !== 'all') {
            url += `${clientId ? '&' : '?'}exercise_type=${encodeURIComponent(exerciseType)}`;
        }
        // ...
    },
    
    async getTrend(metric = 'reps', period = '30d', clientId = null, exerciseType = null) {
        // 类似修改
    },
    
    // 新增: 获取动作类型列表
    async getExerciseTypes() {
        const response = await fetch(`${API_BASE}/dashboard/exercise-types`);
        const data = await response.json();
        return data.status === 'success' ? data.data : [];
    },
};
```

---

## 五、实施难度评估

### 5.1 各模块修改难度

| 模块 | 修改范围 | 难度 | 预计工时 | 风险点 |
|------|----------|------|----------|--------|
| **数据库迁移** | 新建表 + 数据迁移脚本 | ⭐⭐ | 4h | 数据丢失风险 |
| **客户端检测** | 新增动作检测逻辑 | ⭐⭐⭐ | 8h/动作 | 检测准确性 |
| **服务器接收** | 修改验证和存储逻辑 | ⭐⭐ | 4h | API 兼容性 |
| **Dashboard 分析** | 修改查询和统计逻辑 | ⭐⭐ | 6h | 统计准确性 |
| **LLM 模块** | 扩展 Prompt 和预处理 | ⭐⭐ | 4h | 分析质量 |
| **前端 Dashboard** | UI 修改和新功能 | ⭐⭐ | 6h | 用户体验 |

### 5.2 总体评估

| 维度 | 评估 |
|------|------|
| **整体难度** | ⭐⭐ 中等 |
| **工作量** | 30-40 小时（包含测试） |
| **风险等级** | 中等（主要是数据库迁移和检测准确性） |
| **可复用性** | 高（架构设计良好，扩展性强） |

---

## 六、实施建议

### 6.1 推荐实施顺序

```
Phase 1: 基础架构准备 (1-2天)
├─ 1.1 数据库 schema 扩展
├─ 1.2 数据迁移脚本
├─ 1.3 服务器端 API 适配
└─ 1.4 基础测试

Phase 2: 第一个新动作 - 俯卧撑 (3-4天)
├─ 2.1 客户端俯卧撑检测
├─ 2.2 服务器端适配
├─ 2.3 LLM Prompt 扩展
├─ 2.4 Dashboard 适配
└─ 2.5 集成测试

Phase 3: 第二个新动作 - 弓步蹲 (3-4天)
├─ 3.1 客户端弓步蹲检测
├─ 3.2 服务器端适配
├─ 3.3 LLM Prompt 扩展
├─ 3.4 Dashboard 适配
└─ 3.5 集成测试

Phase 4: 优化与完善 (2-3天)
├─ 4.1 跨动作统计功能
├─ 4.2 综合能力评估
├─ 4.3 性能优化
└─ 4.4 用户体验优化
```

### 6.2 关键风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| **数据库迁移失败** | 数据丢失 | 备份 + 灰度发布 + 回滚方案 |
| **动作检测不准确** | 用户体验差 | 充分测试 + 阈值调优 + 用户反馈 |
| **LLM 分析质量下降** | 报告不准确 | 动作特定 Prompt 优化 + 测试用例 |
| **前端兼容性** | 现有功能受影响 | 渐进式修改 + 回归测试 |

### 6.3 成功标准

- [ ] 支持 3 种动作（深蹲、俯卧撑、弓步蹲）
- [ ] 动作检测准确率 > 95%
- [ ] Dashboard 正确显示多动作数据
- [ ] LLM 分析报告针对不同动作提供专业建议
- [ ] 现有深蹲功能完全保留
- [ ] API 向后兼容

---

## 七、总结

### 7.1 可行性结论

**✅ 完全可行**

- 现有架构设计良好，具有良好的扩展性
- 数据库 schema 修改简单直接
- 代码模块化程度高，改动影响可控
- 前后端分离，可以并行开发

### 7.2 推荐方案

| 项目 | 推荐 |
|------|------|
| **扩展动作** | 俯卧撑 + 弓步蹲 |
| **数据库方案** | 统一表结构 + exercise_type 字段 |
| **实施方式** | 分阶段实施，先俯卧撑再弓步蹲 |
| **预计工期** | 10-12 天（包含测试） |

### 7.3 后续扩展

完成俯卧撑和弓步蹲后，可以考虑：
- 开合跳（简单）
- 深蹲跳（中等）
- 平板支撑（较难）
- 波比跳（高难度）

---

**报告生成完毕，请审阅。**

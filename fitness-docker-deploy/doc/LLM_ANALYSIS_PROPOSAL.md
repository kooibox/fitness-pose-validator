# LLM 训练分析功能技术方案报告

> **文档版本**: v1.0  
> **生成日期**: 2026-03-23  
> **适用项目**: Fitness Pose Server

---

## 一、项目现状分析

### 1.1 现有架构

```
技术栈：
├── 后端: Python 标准库 HTTP 服务器 (零依赖)
├── 数据库: SQLite
├── 前端: 原生 HTML/JS + ECharts
└── 部署: Docker Compose
```

### 1.2 已预留的 LLM 接口

项目已设计完整的 LLM 分析接口体系：

| 组件 | 文件 | 状态 |
|------|------|------|
| `LLMAnalyzerInterface` | `server/analysis/llm_analyzer.py` | ✅ 已定义 |
| `LLMAnalyzerStub` | `server/analysis/llm_analyzer.py` | ✅ 已实现 (桩) |
| `LLMAPIHandler` | `server/api/llm.py` | ✅ 已实现 |
| `LLMAnalysisRequest` | `server/analysis/llm_analyzer.py` | ✅ 已定义 |
| `LLMAnalysisResponse` | `server/analysis/llm_analyzer.py` | ✅ 已定义 |

### 1.3 数据结构

**数据库表结构：**

```sql
-- 训练会话表
uploaded_sessions (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    total_frames INTEGER,
    total_squats INTEGER,
    raw_data TEXT
)

-- 训练记录表 (逐帧数据)
uploaded_records (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,
    timestamp TEXT,
    left_angle REAL,
    right_angle REAL,
    avg_angle REAL,
    state TEXT,
    rep_count INTEGER
)
```

### 1.4 支持的分析类型

| 类型 | 枚举值 | 说明 |
|------|--------|------|
| 单次训练分析 | `session` | 分析单次训练表现 |
| 趋势分析 | `trend` | 分析训练进步趋势 |
| 对比分析 | `comparison` | 对比不同训练会话 |
| 个性化建议 | `advice` | 基于历史数据的改进建议 |
| 目标设定 | `goal` | 推荐合适的训练目标 |

---

## 二、LLM 服务商选型

### 2.1 候选方案对比

| 服务商 | 模型 | 输入价格 | 输出价格 | 中文能力 | JSON输出 | 推荐度 |
|--------|------|----------|----------|----------|----------|--------|
| **智谱 AI** | GLM-4.7-Flash | $0.04/1M | $0.20/1M | ⭐⭐⭐⭐⭐ | ✅ 原生支持 | ⭐⭐⭐⭐⭐ |
| DeepSeek | V3.2 | $0.28/1M | $0.42/1M | ⭐⭐⭐⭐⭐ | ✅ 支持 | ⭐⭐⭐⭐ |
| OpenAI | GPT-4o-mini | $0.15/1M | $0.60/1M | ⭐⭐⭐⭐ | ✅ 完整支持 | ⭐⭐⭐ |
| 通义千问 | qwen-plus | $0.40/1M | $1.20/1M | ⭐⭐⭐⭐⭐ | ❌ 不支持 | ⭐⭐ |

### 2.2 推荐方案

**主选：智谱 AI GLM-4.7-Flash**
- 最佳性价比
- 原生中文支持
- 原生 JSON Schema 输出
- Python SDK: `pip install zhipuai`

**备选：DeepSeek V3.2**
- OpenAI 兼容接口
- 最低价格梯队
- Python SDK: `pip install openai`

### 2.3 成本估算

| 使用场景 | 月请求量 | 智谱成本 | DeepSeek成本 |
|----------|----------|----------|--------------|
| 开发测试 | 100次 | ¥0.3 | ¥0.7 |
| 小型运营 | 1,000次 | ¥3 | ¥7 |
| 中型运营 | 10,000次 | ¥30 | ¥70 |
| 大型运营 | 100,000次 | ¥300 | ¥700 |

> 计算依据：平均输入 500 tokens，输出 1500 tokens

---

## 三、技术实现方案

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 Dashboard                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  用户点击「AI 分析」→ 选择分析类型 → 发起请求             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POST /api/v1/llm/analyze                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  LLMAPIHandler._handle_analyze()                          │  │
│  │  ├─ 解析请求体 → LLMAnalysisRequest                       │  │
│  │  └─ 调用 analyzer.analyze(request)                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LLMAnalyzerReal (新建)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ① DataPreprocessor                                       │  │
│  │  ├─ 查询数据库获取会话/记录数据                            │  │
│  │  ├─ 计算统计指标 (均值、方差、对称性)                      │  │
│  │  └─ 格式化为 JSON 文本                                    │  │
│  │                                                            │  │
│  │  ② PromptBuilder                                          │  │
│  │  ├─ 选择分析类型对应的 Prompt 模板                        │  │
│  │  └─ 注入训练数据                                          │  │
│  │                                                            │  │
│  │  ③ LLMClient                                              │  │
│  │  ├─ 调用智谱/DeepSeek API                                 │  │
│  │  └─ 解析 JSON 响应                                        │  │
│  │                                                            │  │
│  │  ④ ResponseParser                                         │  │
│  │  ├─ 验证响应格式                                          │  │
│  │  └─ 返回 LLMAnalysisResponse                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 代码结构

```
server/
├── analysis/
│   ├── __init__.py
│   ├── llm_analyzer.py          # 现有接口定义
│   ├── llm_analyzer_real.py     # 新增 - 真实实现
│   ├── data_preprocessor.py     # 新增 - 数据预处理
│   └── prompt_templates.py      # 新增 - Prompt 模板
├── api/
│   ├── __init__.py
│   ├── llm.py                   # 现有
│   └── dashboard.py             # 现有
└── requirements.txt             # 更新依赖
```

### 3.3 核心代码实现

#### 3.3.1 requirements.txt 更新

```txt
# LLM 分析功能依赖
openai>=1.0.0          # DeepSeek 兼容
zhipuai>=2.0.0         # 智谱 AI SDK
```

#### 3.3.2 llm_analyzer_real.py

```python
"""
LLM 分析器真实实现

接入智谱 AI / DeepSeek API 进行训练报告生成。
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .llm_analyzer import (
    LLMAnalyzerInterface,
    LLMAnalysisRequest,
    LLMAnalysisResponse,
    AnalysisType,
    AnalysisStatus,
)
from .data_preprocessor import DataPreprocessor
from .prompt_templates import PromptBuilder


class LLMAnalyzerReal(LLMAnalyzerInterface):
    """
    LLM 分析器真实实现
    
    支持:
    - 智谱 AI (GLM-4.7-Flash) - 主选
    - DeepSeek (V3.2) - 备选
    """
    
    def __init__(
        self,
        provider: str = "zhipuai",  # zhipuai 或 deepseek
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        db_path: Optional[Path] = None,
    ):
        """
        初始化分析器
        
        Args:
            provider: LLM 服务商 (zhipuai/deepseek)
            api_key: API 密钥，默认从环境变量读取
            model: 模型名称
            db_path: 数据库路径
        """
        self.provider = provider
        self.api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY")
        self.model = model or self._get_default_model()
        self.db_path = db_path
        
        # 初始化子模块
        self.preprocessor = DataPreprocessor(db_path)
        self.prompt_builder = PromptBuilder()
        
        # 初始化 LLM 客户端
        self.client = self._init_client()
        
        # 结果缓存
        self._results: Dict[str, LLMAnalysisResponse] = {}
    
    def _get_default_model(self) -> str:
        """获取默认模型名称"""
        models = {
            "zhipuai": "glm-4-flash",  # 智谱高性价比模型
            "deepseek": "deepseek-chat",
        }
        return models.get(self.provider, "glm-4-flash")
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        if self.provider == "zhipuai":
            from zhipuai import ZhipuAI
            return ZhipuAI(api_key=self.api_key)
        
        elif self.provider == "deepseek":
            from openai import OpenAI
            return OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        
        else:
            raise ValueError(f"不支持的服务商: {self.provider}")
    
    async def analyze(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """
        执行分析
        
        Args:
            request: 分析请求
            
        Returns:
            LLMAnalysisResponse: 分析响应
        """
        try:
            # 1. 数据预处理
            training_data = self.preprocessor.prepare(
                session_ids=request.session_ids,
                analysis_type=request.analysis_type,
            )
            
            # 2. 构建 Prompt
            prompt = self.prompt_builder.build(
                analysis_type=request.analysis_type,
                training_data=training_data,
                language=request.language,
            )
            
            # 3. 调用 LLM API
            llm_response = self._call_llm(prompt)
            
            # 4. 解析响应
            response = self._parse_response(
                request_id=request.request_id,
                llm_output=llm_response,
            )
            
            # 5. 缓存结果
            self._results[request.request_id] = response
            
            return response
            
        except Exception as e:
            return LLMAnalysisResponse(
                request_id=request.request_id,
                status=AnalysisStatus.FAILED,
                error=str(e),
                completed_at=datetime.now().isoformat(),
            )
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的健身教练，擅长分析训练数据并提供科学的训练建议。请以 JSON 格式返回分析结果。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        
        return response.choices[0].message.content
    
    def _parse_response(
        self,
        request_id: str,
        llm_output: str,
    ) -> LLMAnalysisResponse:
        """解析 LLM 响应"""
        try:
            data = json.loads(llm_output)
            
            return LLMAnalysisResponse(
                request_id=request_id,
                status=AnalysisStatus.COMPLETED,
                summary=data.get("summary", ""),
                insights=data.get("insights", []),
                suggestions=data.get("suggestions", []),
                score=data.get("score"),
                metadata=data.get("metadata"),
                completed_at=datetime.now().isoformat(),
            )
        
        except json.JSONDecodeError as e:
            return LLMAnalysisResponse(
                request_id=request_id,
                status=AnalysisStatus.FAILED,
                error=f"JSON 解析失败: {str(e)}",
                completed_at=datetime.now().isoformat(),
            )
    
    def get_status(self, request_id: str) -> Optional[LLMAnalysisResponse]:
        """获取分析状态"""
        return self._results.get(request_id)
```

#### 3.3.3 data_preprocessor.py

```python
"""
数据预处理模块

将数据库中的训练数据转换为 LLM 可理解的格式。
"""

import sqlite3
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .llm_analyzer import AnalysisType


class DataPreprocessor:
    """数据预处理器"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化预处理器
        
        Args:
            db_path: 数据库路径
        """
        import os
        if db_path:
            self.db_path = db_path
        else:
            env_path = os.environ.get("SERVER_DB_PATH")
            self.db_path = Path(env_path) if env_path else Path("server_data.db")
    
    def prepare(
        self,
        session_ids: List[int],
        analysis_type: AnalysisType,
    ) -> str:
        """
        准备训练数据
        
        Args:
            session_ids: 会话 ID 列表
            analysis_type: 分析类型
            
        Returns:
            str: 格式化后的训练数据文本
        """
        if analysis_type == AnalysisType.SESSION:
            return self._prepare_session_data(session_ids)
        elif analysis_type == AnalysisType.TREND:
            return self._prepare_trend_data(session_ids)
        elif analysis_type == AnalysisType.COMPARISON:
            return self._prepare_comparison_data(session_ids)
        elif analysis_type == AnalysisType.ADVICE:
            return self._prepare_advice_data(session_ids)
        elif analysis_type == AnalysisType.GOAL:
            return self._prepare_goal_data(session_ids)
        else:
            raise ValueError(f"未知的分析类型: {analysis_type}")
    
    def _prepare_session_data(self, session_ids: List[int]) -> str:
        """准备单次训练数据"""
        sessions_text = []
        
        for sid in session_ids:
            session = self._get_session(sid)
            records = self._get_records(sid)
            
            if not session or not records:
                continue
            
            # 计算统计指标
            stats = self._calculate_statistics(records)
            
            sessions_text.append(f"""
训练会话 #{sid}:
- 时间: {session['start_time']} 至 {session['end_time']}
- 总深蹲次数: {session['total_squats']}
- 总帧数: {session['total_frames']}
- 平均下蹲角度: {stats['avg_angle']:.1f}°
- 角度范围: {stats['min_angle']:.1f}° ~ {stats['max_angle']:.1f}°
- 角度标准差: {stats['angle_std']:.2f} (越低越稳定)
- 左右对称性评分: {stats['symmetry_score']:.1f}分
- 训练时长: {stats['duration_seconds']:.0f}秒
""")
        
        return "\n".join(sessions_text)
    
    def _prepare_trend_data(self, session_ids: List[int]) -> str:
        """准备趋势数据"""
        sessions_data = []
        
        for sid in sorted(session_ids):
            session = self._get_session(sid)
            records = self._get_records(sid)
            
            if session and records:
                stats = self._calculate_statistics(records)
                sessions_data.append({
                    "date": session['start_time'][:10],
                    "squats": session['total_squats'],
                    "avg_angle": stats['avg_angle'],
                    "symmetry": stats['symmetry_score'],
                })
        
        # 按日期排序
        sessions_data.sort(key=lambda x: x['date'])
        
        # 格式化为文本
        lines = ["训练趋势数据 (按时间顺序):"]
        for i, data in enumerate(sessions_data):
            lines.append(
                f"{i+1}. {data['date']}: "
                f"深蹲{data['squats']}次, "
                f"角度{data['avg_angle']:.1f}°, "
                f"对称性{data['symmetry']:.0f}分"
            )
        
        return "\n".join(lines)
    
    def _prepare_comparison_data(self, session_ids: List[int]) -> str:
        """准备对比数据"""
        if len(session_ids) < 2:
            return "对比分析需要至少2个训练会话"
        
        sessions_text = []
        for i, sid in enumerate(session_ids[:2]):  # 最多对比2个
            session = self._get_session(sid)
            records = self._get_records(sid)
            
            if session and records:
                stats = self._calculate_statistics(records)
                label = "本次训练" if i == 0 else "上次训练"
                sessions_text.append(f"""
{label} (会话 #{sid}):
- 时间: {session['start_time']}
- 深蹲次数: {session['total_squats']}
- 平均角度: {stats['avg_angle']:.1f}°
- 对称性: {stats['symmetry_score']:.1f}分
- 稳定性: {stats['angle_std']:.2f}
""")
        
        return "\n".join(sessions_text)
    
    def _prepare_advice_data(self, session_ids: List[int]) -> str:
        """准备个性化建议数据 (最近10个会话)"""
        recent_ids = sorted(session_ids)[-10:]  # 最近10个
        
        all_stats = []
        for sid in recent_ids:
            session = self._get_session(sid)
            records = self._get_records(sid)
            
            if session and records:
                stats = self._calculate_statistics(records)
                stats['date'] = session['start_time'][:10]
                stats['squats'] = session['total_squats']
                all_stats.append(stats)
        
        if not all_stats:
            return "暂无训练数据"
        
        # 计算整体统计
        avg_squats = statistics.mean([s['squats'] for s in all_stats])
        avg_angle = statistics.mean([s['avg_angle'] for s in all_stats])
        avg_symmetry = statistics.mean([s['symmetry_score'] for s in all_stats])
        
        return f"""
用户训练历史摘要 (最近{len(all_stats)}次训练):
- 平均每次深蹲: {avg_squats:.0f}次
- 平均下蹲角度: {avg_angle:.1f}° (标准值: 90°)
- 平均对称性: {avg_symmetry:.1f}分
- 训练频率: {len(all_stats)}次

详细记录:
{chr(10).join(f"- {s['date']}: {s['squats']}次, 角度{s['avg_angle']:.1f}°" for s in all_stats)}
"""
    
    def _prepare_goal_data(self, session_ids: List[int]) -> str:
        """准备目标设定数据"""
        # 复用 advice 数据准备逻辑
        return self._prepare_advice_data(session_ids)
    
    def _get_session(self, session_id: int) -> Optional[Dict]:
        """获取会话信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM uploaded_sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def _get_records(self, session_id: int) -> List[Dict]:
        """获取训练记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM uploaded_records WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def _calculate_statistics(self, records: List[Dict]) -> Dict[str, Any]:
        """计算统计指标"""
        angles = [r['avg_angle'] for r in records if r['avg_angle'] is not None]
        left_angles = [r['left_angle'] for r in records if r['left_angle'] is not None]
        right_angles = [r['right_angle'] for r in records if r['right_angle'] is not None]
        
        if not angles:
            return {
                "avg_angle": 0,
                "min_angle": 0,
                "max_angle": 0,
                "angle_std": 0,
                "symmetry_score": 0,
                "duration_seconds": 0,
            }
        
        # 计算左右对称性 (角度差的平均值)
        if left_angles and right_angles:
            angle_diffs = [abs(l - r) for l, r in zip(left_angles, right_angles)]
            avg_diff = statistics.mean(angle_diffs)
            symmetry_score = max(0, 100 - avg_diff * 2)  # 差异越小分数越高
        else:
            symmetry_score = 0
        
        # 计算时长
        if len(records) >= 2:
            try:
                start = datetime.fromisoformat(records[0]['timestamp'])
                end = datetime.fromisoformat(records[-1]['timestamp'])
                duration = (end - start).total_seconds()
            except:
                duration = 0
        else:
            duration = 0
        
        return {
            "avg_angle": statistics.mean(angles),
            "min_angle": min(angles),
            "max_angle": max(angles),
            "angle_std": statistics.stdev(angles) if len(angles) > 1 else 0,
            "symmetry_score": symmetry_score,
            "duration_seconds": duration,
        }
```

#### 3.3.4 prompt_templates.py

```python
"""
Prompt 模板管理模块
"""

from typing import Any, Dict
from .llm_analyzer import AnalysisType


class PromptBuilder:
    """Prompt 构建器"""
    
    TEMPLATES = {
        AnalysisType.SESSION: """
你是一位专业的健身教练，擅长分析深蹲训练数据。请根据以下训练数据，生成详细的训练报告。

## 训练数据
{training_data}

## 分析要求
请从以下维度进行分析：
1. **动作质量**: 下蹲深度是否标准（90°为佳）、左右对称性、动作稳定性
2. **训练强度**: 深蹲次数、训练时长、密度
3. **具体问题**: 发现的具体问题和风险点
4. **改进建议**: 针对性的、可操作的改进建议

## 输出格式
请以 JSON 格式返回，包含以下字段：
{{
    "summary": "一段话总结本次训练表现",
    "insights": ["洞察1", "洞察2", "洞察3"],
    "suggestions": ["具体建议1", "具体建议2", "具体建议3"],
    "score": 85.5,
    "metadata": {{
        "depth_assessment": "良好/一般/需改进",
        "symmetry_assessment": "良好/一般/需改进",
        "stability_assessment": "良好/一般/需改进"
    }}
}}
""",
        
        AnalysisType.TREND: """
你是一位专业的健身教练。请分析以下多日训练趋势数据，评估用户的进步情况。

## 趋势数据
{training_data}

## 分析要求
请关注：
1. 训练频率是否稳定
2. 训练质量是否提升
3. 是否存在平台期
4. 下一步的训练方向

## 输出格式
{{
    "summary": "趋势总结",
    "insights": ["趋势洞察1", "趋势洞察2", ...],
    "suggestions": ["改进建议1", "改进建议2", ...],
    "score": 88.0,
    "metadata": {{
        "trend_direction": "上升/平稳/下降",
        "improvement_rate": 0.15
    }}
}}
""",
        
        AnalysisType.COMPARISON: """
你是一位专业的健身教练。请对比分析以下两次训练数据，找出差异和进步。

## 对比数据
{training_data}

## 分析要求
请从以下维度对比：
1. 深蹲次数变化
2. 动作质量变化
3. 对称性和稳定性变化
4. 整体进步幅度

## 输出格式
{{
    "summary": "对比总结",
    "insights": ["对比洞察1", "对比洞察2", ...],
    "suggestions": ["针对性建议1", "针对性建议2", ...],
    "score": 86.0,
    "metadata": {{
        "improvements": ["进步项目"],
        "regressions": ["退步项目"]
    }}
}}
""",
        
        AnalysisType.ADVICE: """
你是一位专业的健身教练。请根据用户的训练历史，提供个性化的改进建议。

## 训练历史
{training_data}

## 分析要求
请提供：
1. 短期目标 (1-2周)
2. 中期目标 (1个月)
3. 具体训练建议
4. 注意事项和风险提示

## 输出格式
{{
    "summary": "个性化建议总结",
    "insights": ["优势分析", "待改进方面", ...],
    "suggestions": ["短期目标", "中期目标", "训练建议", ...],
    "score": 79.0,
    "metadata": {{
        "focus_areas": ["重点改进领域"],
        "strengths": ["现有优势"]
    }}
}}
""",
        
        AnalysisType.GOAL: """
你是一位专业的健身教练。请根据用户的训练水平，推荐合适的训练目标。

## 训练数据
{training_data}

## 分析要求
请设定：
1. 每周训练频率目标
2. 每次训练次数目标
3. 动作质量目标
4. 进阶目标

## 输出格式
{{
    "summary": "目标设定建议",
    "insights": ["当前水平评估", "潜力分析", ...],
    "suggestions": ["周目标", "月目标", "质量目标", "进阶目标"],
    "score": null,
    "metadata": {{
        "current_level": "初级/中级/高级",
        "recommended_goals": [
            {{"type": "weekly_sessions", "target": 4}},
            {{"type": "monthly_squats", "target": 1000}},
            {{"type": "quality_score", "target": 90}}
        ]
    }}
}}
""",
    }
    
    def build(
        self,
        analysis_type: AnalysisType,
        training_data: str,
        language: str = "zh",
    ) -> str:
        """
        构建 Prompt
        
        Args:
            analysis_type: 分析类型
            training_data: 训练数据文本
            language: 输出语言
            
        Returns:
            str: 完整的 Prompt
        """
        template = self.TEMPLATES.get(analysis_type)
        
        if not template:
            raise ValueError(f"未知的分析类型: {analysis_type}")
        
        return template.format(training_data=training_data)
```

---

## 四、部署配置

### 4.1 更新 docker-compose.yml

```yaml
version: '3.8'

services:
  server:
    build:
      context: .
      dockerfile: Dockerfile.server
    container_name: fitness-server
    restart: unless-stopped
    environment:
      - SERVER_DB_PATH=/data/server_data.db
      - PYTHONUNBUFFERED=1
      # LLM 配置
      - LLM_PROVIDER=zhipuai
      - ZHIPUAI_API_KEY=${ZHIPUAI_API_KEY}  # 从 .env 文件读取
    volumes:
      - server-data:/data
    ports:
      - "8080:8080"
    networks:
      - fitness-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/dashboard/overview')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # ... 其他服务保持不变

volumes:
  server-data:
    driver: local

networks:
  fitness-network:
    driver: bridge
```

### 4.2 创建 .env 文件

```bash
# LLM API 配置
LLM_PROVIDER=zhipuai
ZHIPUAI_API_KEY=your_api_key_here

# 备选配置
# DEEPSEEK_API_KEY=your_deepseek_key
```

### 4.3 更新 Dockerfile.server

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 复制依赖文件并安装
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY server/ ./

RUN mkdir -p /data

ENV SERVER_DB_PATH=/data/server_data.db

EXPOSE 8080

CMD ["python", "run_server.py", "--host", "0.0.0.0", "--port", "8080"]
```

### 4.4 修改 server_receiver.py

```python
# 在 FitnessHTTPHandler 类中修改初始化

from api.llm import LLMAPIHandler
from analysis.llm_analyzer_real import LLMAnalyzerReal

class FitnessHTTPHandler(BaseHTTPRequestHandler):
    receiver = FitnessDataReceiver()
    dashboard_handler = DashboardAPIHandler()
    
    # 使用真实 LLM 分析器
    llm_handler = LLMAPIHandler(
        analyzer=LLMAnalyzerReal(
            provider=os.environ.get("LLM_PROVIDER", "zhipuai"),
            api_key=os.environ.get("ZHIPUAI_API_KEY"),
        )
    )
    
    # ... 其他代码保持不变
```

---

## 五、实施计划

### 5.1 里程碑规划

| 阶段 | 任务 | 工期 | 交付物 |
|------|------|------|--------|
| **Phase 1** | 核心实现 | 3-5 天 | 可用的 LLM 分析功能 |
| **Phase 2** | 增强优化 | 2-3 天 | 异步处理、缓存、错误处理 |
| **Phase 3** | 前端集成 | 1-2 天 | 报告展示界面 |

### 5.2 Phase 1 详细任务

| # | 任务 | 负责 | 预计工时 |
|---|------|------|----------|
| 1 | 更新 requirements.txt | 后端 | 0.5h |
| 2 | 实现 data_preprocessor.py | 后端 | 2h |
| 3 | 实现 prompt_templates.py | 后端 | 1h |
| 4 | 实现 llm_analyzer_real.py | 后端 | 2h |
| 5 | 更新 docker-compose.yml | DevOps | 0.5h |
| 6 | 更新 Dockerfile.server | DevOps | 0.5h |
| 7 | 修改 server_receiver.py | 后端 | 1h |
| 8 | 单元测试 | 后端 | 2h |
| 9 | 集成测试 | 测试 | 2h |
| **总计** | | | **12h** |

### 5.3 Phase 2 优化任务

| # | 任务 | 说明 |
|---|------|------|
| 1 | 异步处理 | 使用线程池处理 LLM 请求 |
| 2 | 进度查询 | 实现 get_status 轮询 |
| 3 | 响应缓存 | 缓存相同请求的结果 |
| 4 | 错误重试 | 指数退避重试机制 |
| 5 | 限流处理 | 请求队列管理 |

---

## 六、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| **API 不稳定** | 请求失败 | 重试机制 + 备选服务商 |
| **响应延迟** | 用户等待 | 异步处理 + 进度提示 |
| **Token 超限** | 请求失败 | 限制输入数据量 |
| **JSON 解析失败** | 结果不可用 | 验证 + 重试 |
| **API Key 泄露** | 安全风险 | 环境变量 + Docker Secrets |

---

## 七、验收标准

### 7.1 功能验收

- [ ] 5 种分析类型均可正常调用
- [ ] 返回结构化的 JSON 响应
- [ ] 错误场景有明确的错误信息
- [ ] 分析结果符合预期格式

### 7.2 性能验收

- [ ] 单次分析响应时间 < 10 秒
- [ ] 并发 10 个请求不崩溃
- [ ] 错误率 < 5%

### 7.3 代码验收

- [ ] 代码符合现有项目风格
- [ ] 有完整的注释和文档
- [ ] 通过基础单元测试

---

## 八、总结

### 推荐方案

| 项目 | 推荐 |
|------|------|
| **LLM 服务商** | 智谱 AI GLM-4.7-Flash |
| **备选服务商** | DeepSeek V3.2 |
| **预计工期** | 5-7 天 (MVP) |
| **月度成本** | ¥30-70 (1000 次/月) |

### 实施建议

1. **第一周**: 完成 Phase 1 核心实现
2. **第二周**: 完成 Phase 2 优化和前端集成
3. **第三周**: 测试和调优

### 下一步行动

1. ✅ 获取智谱 AI API Key
2. ✅ 创建 `.env` 配置文件
3. ✅ 按照本方案实施代码
4. ✅ 部署测试

---

**报告生成完毕，请审阅。**

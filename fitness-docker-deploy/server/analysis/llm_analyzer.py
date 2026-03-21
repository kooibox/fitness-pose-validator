"""
LLM 分析接口模块

为后续接入大语言模型预留接口。
当前提供 stub 实现，便于开发和测试。
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisType(str, Enum):
    """分析类型枚举"""
    SESSION = "session"           # 单次训练分析
    TREND = "trend"               # 趋势分析
    COMPARISON = "comparison"     # 对比分析
    ADVICE = "advice"             # 个性化建议
    GOAL = "goal"                 # 目标设定


class AnalysisStatus(str, Enum):
    """分析状态枚举"""
    PENDING = "pending"           # 等待处理
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败


@dataclass
class LLMAnalysisRequest:
    """
    LLM 分析请求数据
    
    Attributes:
        request_id: 请求唯一ID
        session_ids: 要分析的会话ID列表
        analysis_type: 分析类型
        context: 额外上下文信息
        language: 输出语言 (zh/en)
        created_at: 请求创建时间
    """
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_ids: List[int] = field(default_factory=list)
    analysis_type: AnalysisType = AnalysisType.SESSION
    context: Optional[Dict[str, Any]] = None
    language: str = "zh"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "session_ids": self.session_ids,
            "analysis_type": self.analysis_type.value,
            "context": self.context,
            "language": self.language,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMAnalysisRequest":
        """从字典创建"""
        return cls(
            request_id=data.get("request_id", str(uuid.uuid4())),
            session_ids=data.get("session_ids", []),
            analysis_type=AnalysisType(data.get("analysis_type", "session")),
            context=data.get("context"),
            language=data.get("language", "zh"),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class LLMAnalysisResponse:
    """
    LLM 分析响应数据
    
    Attributes:
        request_id: 对应的请求ID
        status: 分析状态
        summary: 分析摘要
        insights: 洞察列表
        suggestions: 建议列表
        score: 综合评分 (0-100)
        metadata: 额外元数据
        error: 错误信息（如果失败）
        completed_at: 完成时间
    """
    request_id: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    summary: Optional[str] = None
    insights: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "summary": self.summary,
            "insights": self.insights,
            "suggestions": self.suggestions,
            "score": self.score,
            "metadata": self.metadata,
            "error": self.error,
            "completed_at": self.completed_at,
        }


class LLMAnalyzerInterface(ABC):
    """
    LLM 分析器接口（抽象基类）
    
    后续接入真实 LLM 时，实现此接口即可。
    """
    
    @abstractmethod
    async def analyze(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """
        执行分析
        
        Args:
            request: 分析请求
            
        Returns:
            LLMAnalysisResponse: 分析响应
        """
        pass
    
    @abstractmethod
    def get_status(self, request_id: str) -> Optional[LLMAnalysisResponse]:
        """
        获取分析状态
        
        Args:
            request_id: 请求ID
            
        Returns:
            LLMAnalysisResponse: 分析响应，不存在返回 None
        """
        pass


class LLMAnalyzerStub(LLMAnalyzerInterface):
    """
    LLM 分析器桩实现
    
    用于开发和测试阶段，返回模拟数据。
    后续替换为真实 LLM 实现即可。
    """
    
    def __init__(self):
        """初始化桩分析器"""
        self._results: Dict[str, LLMAnalysisResponse] = {}
    
    async def analyze(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """
        返回模拟分析结果
        """
        # 根据分析类型生成不同的模拟数据
        if request.analysis_type == AnalysisType.SESSION:
            response = self._mock_session_analysis(request)
        elif request.analysis_type == AnalysisType.TREND:
            response = self._mock_trend_analysis(request)
        elif request.analysis_type == AnalysisType.COMPARISON:
            response = self._mock_comparison_analysis(request)
        elif request.analysis_type == AnalysisType.ADVICE:
            response = self._mock_advice_analysis(request)
        elif request.analysis_type == AnalysisType.GOAL:
            response = self._mock_goal_analysis(request)
        else:
            response = LLMAnalysisResponse(
                request_id=request.request_id,
                status=AnalysisStatus.FAILED,
                error=f"Unknown analysis type: {request.analysis_type}",
            )
        
        # 存储结果
        self._results[request.request_id] = response
        return response
    
    def get_status(self, request_id: str) -> Optional[LLMAnalysisResponse]:
        """获取分析状态"""
        return self._results.get(request_id)
    
    def _mock_session_analysis(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """单次训练分析模拟"""
        return LLMAnalysisResponse(
            request_id=request.request_id,
            status=AnalysisStatus.COMPLETED,
            summary="本次训练整体表现良好，深蹲动作较为标准。",
            insights=[
                "您的下蹲深度逐渐改善，继续保持",
                "左右膝盖角度对称性良好",
                "建议适当放慢动作节奏，提高稳定性",
            ],
            suggestions=[
                "尝试将下蹲深度控制在90度左右",
                "注意保持背部挺直，避免过度前倾",
                "建议每组训练后休息30-60秒",
            ],
            score=82.5,
            metadata={
                "total_squats": 25,
                "avg_depth": 95.3,
                "symmetry_score": 88.0,
            },
            completed_at=datetime.now().isoformat(),
        )
    
    def _mock_trend_analysis(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """趋势分析模拟"""
        return LLMAnalysisResponse(
            request_id=request.request_id,
            status=AnalysisStatus.COMPLETED,
            summary="近30天训练趋势向好，训练频率和质量都有提升。",
            insights=[
                "训练频率从每周2次提升到每周4次",
                "平均深蹲次数从15次提升到25次",
                "动作质量评分从75分提升到85分",
                "周末训练频率较低，建议保持规律",
            ],
            suggestions=[
                "继续保持当前的训练频率",
                "可以尝试增加每组的深蹲次数",
                "建议设定每周至少训练5次的目标",
            ],
            score=88.0,
            metadata={
                "period": "30d",
                "sessions_count": 15,
                "improvement_rate": 0.15,
            },
            completed_at=datetime.now().isoformat(),
        )
    
    def _mock_comparison_analysis(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """对比分析模拟"""
        return LLMAnalysisResponse(
            request_id=request.request_id,
            status=AnalysisStatus.COMPLETED,
            summary="与上次训练相比，本次训练在多个维度有所提升。",
            insights=[
                "深蹲次数从20次提升到25次（+25%）",
                "平均下蹲深度从100度改善到92度",
                "动作稳定性评分从80分提升到85分",
                "训练时长基本保持一致",
            ],
            suggestions=[
                "继续保持当前的下蹲深度",
                "可以尝试增加训练强度",
                "注意训练后的拉伸放松",
            ],
            score=86.0,
            metadata={
                "comparison_type": "vs_last",
                "improvements": ["depth", "stability", "count"],
                "regressions": [],
            },
            completed_at=datetime.now().isoformat(),
        )
    
    def _mock_advice_analysis(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """个性化建议模拟"""
        return LLMAnalysisResponse(
            request_id=request.request_id,
            status=AnalysisStatus.COMPLETED,
            summary="基于您的训练历史，为您制定个性化改进建议。",
            insights=[
                "您的训练强度适中，但频率可以更高",
                "下蹲深度是您需要重点改进的方面",
                "您的动作节奏较为稳定，这是优势",
            ],
            suggestions=[
                "【短期目标】每周训练4次以上",
                "【深度改进】将下蹲角度控制在85-95度",
                "【强度提升】每组深蹲次数增加5次",
                "【休息调整】组间休息控制在45秒",
            ],
            score=79.0,
            metadata={
                "focus_areas": ["depth", "frequency"],
                "strengths": ["rhythm", "consistency"],
            },
            completed_at=datetime.now().isoformat(),
        )
    
    def _mock_goal_analysis(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """目标设定模拟"""
        return LLMAnalysisResponse(
            request_id=request.request_id,
            status=AnalysisStatus.COMPLETED,
            summary="根据您的训练水平，为您推荐以下训练目标。",
            insights=[
                "您当前的训练水平为中级",
                "每周训练频率建议4-5次",
                "每次训练建议30-45分钟",
            ],
            suggestions=[
                "【周目标】每周完成4次训练",
                "【月目标】月累计深蹲1000次",
                "【质量目标】动作评分达到90分以上",
                "【深度目标】下蹲角度稳定在90度",
            ],
            score=None,
            metadata={
                "current_level": "intermediate",
                "recommended_goals": [
                    {"type": "weekly_sessions", "target": 4},
                    {"type": "monthly_squats", "target": 1000},
                    {"type": "quality_score", "target": 90},
                ],
            },
            completed_at=datetime.now().isoformat(),
        )

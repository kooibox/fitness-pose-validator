# -*- coding: utf-8 -*-
"""Pydantic 数据模型 - 定义 API 请求和响应的数据结构"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============ 认证相关 ============

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """用户信息"""
    user_id: int
    username: str


# ============ 训练数据相关 ============

class RecordData(BaseModel):
    """单条训练记录"""
    timestamp: Optional[str] = None
    left_angle: Optional[float] = None
    right_angle: Optional[float] = None
    avg_angle: Optional[float] = None
    state: Optional[str] = None
    rep_count: Optional[int] = None


class ClientInfo(BaseModel):
    """客户端信息"""
    app_id: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[Dict[str, Any]] = None


class SessionInfo(BaseModel):
    """会话信息"""
    id: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_frames: Optional[int] = None
    total_squats: Optional[int] = None


class SessionUpload(BaseModel):
    """训练数据上传请求"""
    version: str = "1.0"
    client: Optional[ClientInfo] = None
    session: Optional[SessionInfo] = None
    records: List[RecordData] = Field(default_factory=list)
    exercise_type: str = "squat"  # 默认深蹲，兼容旧数据


class UploadResponse(BaseModel):
    """上传响应"""
    status: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    message: Optional[str] = None


# ============ Dashboard 相关 ============

class OverviewStats(BaseModel):
    """概览统计"""
    total_sessions: int
    total_squats: int
    total_frames: int
    avg_squats_per_session: float
    avg_duration_seconds: float
    weekly_sessions: int
    monthly_sessions: int
    last_training_time: Optional[str] = None


class TrendData(BaseModel):
    """趋势数据"""
    labels: List[str]
    values: List[float]
    metric: str
    period: str


class DistributionData(BaseModel):
    """分布数据"""
    labels: List[str]
    values: List[int]
    metric: str


class HeatmapData(BaseModel):
    """热力图数据"""
    data: List[Dict[str, Any]]
    period: str


class RadarData(BaseModel):
    """雷达图数据"""
    dimensions: List[str]
    values: List[float]


class BestRecord(BaseModel):
    """最佳记录"""
    session_id: int
    start_time: Optional[str]
    total_squats: int
    total_frames: int
    client_app_id: Optional[str]


class RecentSession(BaseModel):
    """最近会话"""
    server_session_id: int
    client_session_id: Optional[int]
    start_time: Optional[str]
    end_time: Optional[str]
    total_frames: int
    total_squats: int
    client_app_id: Optional[str]


# ============ LLM 分析相关 ============

class LLMAnalyzeRequest(BaseModel):
    """LLM 分析请求"""
    request_id: Optional[str] = None
    session_ids: List[int] = Field(default_factory=list)
    analysis_type: str = "session"
    context: Optional[Dict[str, Any]] = None
    language: str = "zh"


class LLMAnalyzeResponse(BaseModel):
    """LLM 分析响应"""
    request_id: str
    status: str
    summary: Optional[str] = None
    insights: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None


class AnalysisTypeInfo(BaseModel):
    """分析类型信息"""
    type: str
    name: str
    description: str


# ============ 通用响应 ============

class SuccessResponse(BaseModel):
    """成功响应"""
    status: str = "success"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    status: str = "error"
    error_code: Optional[str] = None
    message: str
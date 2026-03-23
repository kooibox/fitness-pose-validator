# -*- coding: utf-8 -*-
"""Dashboard 数据路由 - 提供数据大屏所需的各类 API 端点"""

from typing import Optional

from fastapi import APIRouter, Query

from analysis.dashboard_analyzer import DashboardAnalyzer
from auth import get_current_user_optional
from fastapi import Depends

router = APIRouter(tags=["Dashboard"])
analyzer = DashboardAnalyzer()


@router.get("/dashboard/overview")
async def get_overview(
    client_id: Optional[int] = Query(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    获取概览统计数据
    
    - **client_id**: 可选，指定客户端ID
    """
    # 如果用户已登录，使用 user_id 过滤
    effective_client_id = client_id
    if user and not client_id:
        # 已登录用户可以查看自己的数据
        pass  # 暂时保持原有逻辑，后续可根据 user_id 过滤
    
    stats = analyzer.get_overview_stats(effective_client_id)
    return {"status": "success", "data": stats}


@router.get("/dashboard/trend")
async def get_trend(
    metric: str = Query("squats", description="指标类型: squats/sessions/duration"),
    period: str = Query("30d", description="时间范围: 7d/30d/90d/all"),
    client_id: Optional[int] = Query(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    获取趋势数据
    
    - **metric**: 指标类型 (squats/sessions/duration)
    - **period**: 时间范围 (7d/30d/90d/all)
    - **client_id**: 可选，指定客户端ID
    """
    data = analyzer.get_trend_data(metric, period, client_id)
    return {"status": "success", "data": data}


@router.get("/dashboard/distribution")
async def get_distribution(
    metric: str = Query("depth", description="分布类型: depth/state/time_of_day"),
    session_id: Optional[int] = Query(None),
    client_id: Optional[int] = Query(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    获取分布数据
    
    - **metric**: 分布类型 (depth/state/time_of_day)
    - **session_id**: 可选，指定会话ID
    - **client_id**: 可选，指定客户端ID
    """
    data = analyzer.get_distribution_data(metric, session_id, client_id)
    return {"status": "success", "data": data}


@router.get("/dashboard/heatmap")
async def get_heatmap(
    period: str = Query("90d", description="时间范围: 30d/90d/180d/all"),
    client_id: Optional[int] = Query(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    获取热力图数据（每日训练强度）
    
    - **period**: 时间范围 (30d/90d/180d/all)
    - **client_id**: 可选，指定客户端ID
    """
    data = analyzer.get_heatmap_data(period, client_id)
    return {"status": "success", "data": data}


@router.get("/dashboard/radar")
async def get_radar(
    client_id: Optional[int] = Query(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    获取雷达图数据（多维度能力评估）
    
    - **client_id**: 可选，指定客户端ID
    """
    data = analyzer.get_radar_data(client_id)
    return {"status": "success", "data": data}


@router.get("/dashboard/best-records")
async def get_best_records(
    limit: int = Query(5, ge=1, le=20),
    client_id: Optional[int] = Query(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    获取最佳表现记录
    
    - **limit**: 返回数量限制
    - **client_id**: 可选，指定客户端ID
    """
    records = analyzer.get_best_records(limit, client_id)
    return {"status": "success", "data": records}


@router.get("/dashboard/recent-sessions")
async def get_recent_sessions(
    limit: int = Query(10, ge=1, le=50),
    client_id: Optional[int] = Query(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    获取最近的训练会话
    
    - **limit**: 返回数量限制
    - **client_id**: 可选，指定客户端ID
    """
    sessions = analyzer.get_recent_sessions(limit, client_id)
    return {"status": "success", "data": sessions}
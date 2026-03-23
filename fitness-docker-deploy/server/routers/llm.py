# -*- coding: utf-8 -*-
"""LLM 分析路由 - 提供 LLM 分析相关的 API 端点"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException

from analysis.llm_analyzer import (
    LLMAnalyzerStub,
    LLMAnalysisRequest,
    AnalysisType,
)
from analysis.llm_analyzer_real import LLMAnalyzerReal
from auth import get_current_user_optional
from fastapi import Depends
from models import LLMAnalyzeRequest as LLMAnalyzeRequestModel

router = APIRouter(tags=["LLM 分析"])


def get_llm_analyzer():
    """获取 LLM 分析器实例"""
    try:
        response_mode = os.environ.get("LLM_RESPONSE_MODE", "json")
        return LLMAnalyzerReal(response_mode=response_mode)
    except (ValueError, ImportError) as e:
        print(f"警告: 无法初始化真实 LLM 分析器: {e}")
        return LLMAnalyzerStub()


analyzer = get_llm_analyzer()


@router.post("/llm/analyze")
async def analyze(
    request: LLMAnalyzeRequestModel,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    提交分析请求
    
    - **session_ids**: 要分析的会话ID列表
    - **analysis_type**: 分析类型 (session/trend/comparison/advice/goal)
    - **context**: 额外上下文信息
    - **language**: 输出语言 (zh/en)
    """
    try:
        llm_request = LLMAnalysisRequest(
            request_id=request.request_id,
            session_ids=request.session_ids,
            analysis_type=AnalysisType(request.analysis_type),
            context=request.context,
            language=request.language,
        )
        
        response = await analyzer.analyze(llm_request)
        
        return {
            "status": "success",
            "data": response.to_dict()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/llm/status/{request_id}")
async def get_status(
    request_id: str,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    查询分析状态
    
    - **request_id**: 请求ID
    """
    response = analyzer.get_status(request_id)
    
    if response is None:
        raise HTTPException(status_code=404, detail=f"未找到请求: {request_id}")
    
    return {
        "status": "success",
        "data": response.to_dict()
    }


@router.get("/llm/types")
async def get_types(user: Optional[dict] = Depends(get_current_user_optional)):
    """获取支持的分析类型"""
    types = [
        {
            "type": AnalysisType.SESSION.value,
            "name": "单次训练分析",
            "description": "分析单次训练的表现，提供改进建议",
        },
        {
            "type": AnalysisType.TREND.value,
            "name": "趋势分析",
            "description": "分析一段时间内的训练趋势和进步情况",
        },
        {
            "type": AnalysisType.COMPARISON.value,
            "name": "对比分析",
            "description": "对比不同训练会话的表现差异",
        },
        {
            "type": AnalysisType.ADVICE.value,
            "name": "个性化建议",
            "description": "基于训练历史提供个性化改进建议",
        },
        {
            "type": AnalysisType.GOAL.value,
            "name": "目标设定",
            "description": "根据训练水平推荐合适的训练目标",
        },
    ]
    
    return {"status": "success", "data": types}
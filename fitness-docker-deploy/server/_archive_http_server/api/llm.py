"""
LLM 分析 API 处理器

提供 LLM 分析相关的 API 端点。
"""

import asyncio
import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.llm_analyzer import (
    LLMAnalyzerStub,
    LLMAnalysisRequest,
    AnalysisType,
)


class LLMAPIHandler:
    """
    LLM 分析 API 处理器
    
    提供以下端点：
    - POST /api/v1/llm/analyze - 提交分析请求
    - GET /api/v1/llm/status/{request_id} - 查询分析状态
    - GET /api/v1/llm/types - 获取支持的分析类型
    """
    
    def __init__(self, analyzer=None):
        """
        初始化处理器
        
        Args:
            analyzer: LLM 分析器实例，默认使用桩实现
        """
        self.analyzer = analyzer or LLMAnalyzerStub()
    
    def handle_request(
        self,
        handler: BaseHTTPRequestHandler,
        path: str,
        method: str,
        body: Optional[bytes] = None
    ) -> bool:
        """
        处理请求
        
        Args:
            handler: HTTP 请求处理器
            path: 请求路径
            method: 请求方法
            body: 请求体（POST 请求）
            
        Returns:
            bool: 是否处理了请求
        """
        parsed_path = urlparse(path)
        
        # 路由分发
        if parsed_path.path == "/api/v1/llm/analyze" and method == "POST":
            return self._handle_analyze(handler, body)
        elif parsed_path.path.startswith("/api/v1/llm/status/") and method == "GET":
            request_id = parsed_path.path.split("/")[-1]
            return self._handle_status(handler, request_id)
        elif parsed_path.path == "/api/v1/llm/types" and method == "GET":
            return self._handle_types(handler)
        
        return False
    
    def _send_json_response(self, handler: BaseHTTPRequestHandler, status_code: int, data: Dict[str, Any]):
        """发送 JSON 响应"""
        handler.send_response(status_code)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Access-Control-Allow-Origin", "*")  # CORS
        handler.end_headers()
        
        response = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        handler.wfile.write(response)
    
    def _send_error(self, handler: BaseHTTPRequestHandler, status_code: int, message: str):
        """发送错误响应"""
        self._send_json_response(handler, status_code, {
            "status": "error",
            "message": message,
        })
    
    def _handle_analyze(self, handler: BaseHTTPRequestHandler, body: Optional[bytes]) -> bool:
        """处理分析请求"""
        try:
            if not body:
                self._send_error(handler, 400, "请求体为空")
                return True
            
            # 解析请求体
            data = json.loads(body.decode('utf-8'))
            
            # 验证必需字段
            if "analysis_type" not in data:
                self._send_error(handler, 400, "缺少必需字段: analysis_type")
                return True
            
            # 创建请求对象
            request = LLMAnalysisRequest.from_dict(data)
            
            # 执行分析（使用 asyncio.run 替代手动创建事件循环，避免线程阻塞）
            response = asyncio.run(self.analyzer.analyze(request))
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": response.to_dict(),
            })
            return True
        
        except json.JSONDecodeError as e:
            self._send_error(handler, 400, f"JSON 解析失败: {str(e)}")
            return True
        except ValueError as e:
            self._send_error(handler, 400, f"参数错误: {str(e)}")
            return True
        except Exception as e:
            self._send_error(handler, 500, f"分析失败: {str(e)}")
            return True
    
    def _handle_status(self, handler: BaseHTTPRequestHandler, request_id: str) -> bool:
        """处理状态查询请求"""
        try:
            response = self.analyzer.get_status(request_id)
            
            if response is None:
                self._send_error(handler, 404, f"未找到请求: {request_id}")
                return True
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": response.to_dict(),
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"查询状态失败: {str(e)}")
            return True
    
    def _handle_types(self, handler: BaseHTTPRequestHandler) -> bool:
        """处理分析类型查询请求"""
        try:
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
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": types,
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"获取分析类型失败: {str(e)}")
            return True

"""
数据大屏 API 处理器

提供数据大屏所需的各类 API 端点。
"""

import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.dashboard_analyzer import DashboardAnalyzer


class DashboardAPIHandler:
    """
    数据大屏 API 处理器
    
    提供以下端点：
    - GET /api/v1/dashboard/overview - 概览统计
    - GET /api/v1/dashboard/trend - 趋势数据
    - GET /api/v1/dashboard/distribution - 分布数据
    - GET /api/v1/dashboard/heatmap - 热力图数据
    - GET /api/v1/dashboard/radar - 雷达图数据
    - GET /api/v1/dashboard/best-records - 最佳记录
    - GET /api/v1/dashboard/recent-sessions - 最近会话
    """
    
    def __init__(self):
        """初始化处理器"""
        self.analyzer = DashboardAnalyzer()
    
    def handle_request(
        self,
        handler: BaseHTTPRequestHandler,
        path: str,
        method: str
    ) -> bool:
        """
        处理请求
        
        Args:
            handler: HTTP 请求处理器
            path: 请求路径
            method: 请求方法
            
        Returns:
            bool: 是否处理了请求
        """
        if method != "GET":
            return False
        
        parsed_path = urlparse(path)
        query_params = parse_qs(parsed_path.query)
        
        # 路由分发
        if parsed_path.path == "/api/v1/dashboard/overview":
            return self._handle_overview(handler, query_params)
        elif parsed_path.path == "/api/v1/dashboard/trend":
            return self._handle_trend(handler, query_params)
        elif parsed_path.path == "/api/v1/dashboard/distribution":
            return self._handle_distribution(handler, query_params)
        elif parsed_path.path == "/api/v1/dashboard/heatmap":
            return self._handle_heatmap(handler, query_params)
        elif parsed_path.path == "/api/v1/dashboard/radar":
            return self._handle_radar(handler, query_params)
        elif parsed_path.path == "/api/v1/dashboard/best-records":
            return self._handle_best_records(handler, query_params)
        elif parsed_path.path == "/api/v1/dashboard/recent-sessions":
            return self._handle_recent_sessions(handler, query_params)
        
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
    
    def _get_param(self, params: Dict, key: str, default: Any = None) -> Any:
        """从查询参数中获取值"""
        values = params.get(key, [default])
        return values[0] if values else default
    
    def _handle_overview(self, handler: BaseHTTPRequestHandler, params: Dict) -> bool:
        """处理概览统计请求"""
        try:
            client_id = self._get_param(params, "client_id")
            if client_id:
                client_id = int(client_id)
            
            stats = self.analyzer.get_overview_stats(client_id)
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": stats,
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"获取概览统计失败: {str(e)}")
            return True
    
    def _handle_trend(self, handler: BaseHTTPRequestHandler, params: Dict) -> bool:
        """处理趋势数据请求"""
        try:
            metric = self._get_param(params, "metric", "squats")
            period = self._get_param(params, "period", "30d")
            client_id = self._get_param(params, "client_id")
            
            if client_id:
                client_id = int(client_id)
            
            data = self.analyzer.get_trend_data(metric, period, client_id)
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": data,
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"获取趋势数据失败: {str(e)}")
            return True
    
    def _handle_distribution(self, handler: BaseHTTPRequestHandler, params: Dict) -> bool:
        """处理分布数据请求"""
        try:
            metric = self._get_param(params, "metric", "depth")
            session_id = self._get_param(params, "session_id")
            client_id = self._get_param(params, "client_id")
            
            if session_id:
                session_id = int(session_id)
            if client_id:
                client_id = int(client_id)
            
            data = self.analyzer.get_distribution_data(metric, session_id, client_id)
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": data,
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"获取分布数据失败: {str(e)}")
            return True
    
    def _handle_heatmap(self, handler: BaseHTTPRequestHandler, params: Dict) -> bool:
        """处理热力图数据请求"""
        try:
            period = self._get_param(params, "period", "90d")
            client_id = self._get_param(params, "client_id")
            
            if client_id:
                client_id = int(client_id)
            
            data = self.analyzer.get_heatmap_data(period, client_id)
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": data,
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"获取热力图数据失败: {str(e)}")
            return True
    
    def _handle_radar(self, handler: BaseHTTPRequestHandler, params: Dict) -> bool:
        """处理雷达图数据请求"""
        try:
            client_id = self._get_param(params, "client_id")
            
            if client_id:
                client_id = int(client_id)
            
            data = self.analyzer.get_radar_data(client_id)
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": data,
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"获取雷达图数据失败: {str(e)}")
            return True
    
    def _handle_best_records(self, handler: BaseHTTPRequestHandler, params: Dict) -> bool:
        """处理最佳记录请求"""
        try:
            limit = int(self._get_param(params, "limit", "5"))
            client_id = self._get_param(params, "client_id")
            
            if client_id:
                client_id = int(client_id)
            
            records = self.analyzer.get_best_records(limit, client_id)
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": records,
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"获取最佳记录失败: {str(e)}")
            return True
    
    def _handle_recent_sessions(self, handler: BaseHTTPRequestHandler, params: Dict) -> bool:
        """处理最近会话请求"""
        try:
            limit = int(self._get_param(params, "limit", "10"))
            client_id = self._get_param(params, "client_id")
            
            if client_id:
                client_id = int(client_id)
            
            sessions = self.analyzer.get_recent_sessions(limit, client_id)
            
            self._send_json_response(handler, 200, {
                "status": "success",
                "data": sessions,
            })
            return True
        
        except Exception as e:
            self._send_error(handler, 500, f"获取最近会话失败: {str(e)}")
            return True

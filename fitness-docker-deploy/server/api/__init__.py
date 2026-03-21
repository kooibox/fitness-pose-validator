"""服务器端 API 模块"""

try:
    from .dashboard import DashboardAPIHandler
    from .llm import LLMAPIHandler
except ImportError:
    from dashboard import DashboardAPIHandler
    from llm import LLMAPIHandler

__all__ = ["DashboardAPIHandler", "LLMAPIHandler"]

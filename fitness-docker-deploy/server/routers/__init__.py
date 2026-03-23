# -*- coding: utf-8 -*-
"""路由模块"""

from .auth import router as auth_router
from .sessions import router as sessions_router
from .dashboard import router as dashboard_router
from .llm import router as llm_router

__all__ = [
    "auth_router",
    "sessions_router",
    "dashboard_router",
    "llm_router",
]
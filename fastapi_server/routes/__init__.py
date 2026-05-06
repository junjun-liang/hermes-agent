#!/usr/bin/env python3
"""
路由包初始化
"""

from .chat import router as chat_router
from .sessions import router as sessions_router
from .tools import router as tools_router
from .system import router as system_router

__all__ = [
    "chat_router",
    "sessions_router",
    "tools_router",
    "system_router",
]

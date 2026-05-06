#!/usr/bin/env python3
"""
FastAPI 服务包初始化

Hermes-Agent 生产级别 FastAPI 服务
"""

__version__ = "1.0.0"
__author__ = "Hermes-Agent Team"

from .config import settings, get_settings
from .main import app

__all__ = [
    "app",
    "settings",
    "get_settings",
]

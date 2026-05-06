#!/usr/bin/env python3
"""
服务包初始化
"""

from .agent_service import AgentService, get_agent_service

__all__ = [
    "AgentService",
    "get_agent_service",
]

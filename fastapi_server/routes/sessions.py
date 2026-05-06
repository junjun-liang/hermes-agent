#!/usr/bin/env python3
"""
会话管理 API 路由

提供会话列表、详情、删除等端点
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from ..models.response import SessionDetail, ListSessionsResponse, SessionInfo
from ..services.agent_service import get_agent_service, AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["会话管理"])


@router.get(
    "",
    response_model=ListSessionsResponse,
    summary="列出所有会话",
    description="获取用户的会话列表（分页）",
)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    agent_service: AgentService = Depends(get_agent_service),
) -> ListSessionsResponse:
    """
    列出所有会话
    
    支持分页查询，按最后更新时间倒序排列。
    
    **参数:**
    - `limit`: 每页数量（1-100）
    - `offset`: 偏移量
    
    **返回:**
    - 会话列表
    - 总会话数
    - 分页信息
    """
    
    sessions = agent_service.list_sessions(limit=limit, offset=offset)
    
    return ListSessionsResponse(
        sessions=sessions,
        total=len(sessions),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{session_id}",
    response_model=SessionDetail,
    summary="获取会话详情",
    description="获取指定会话的详细信息（包含消息历史）",
)
async def get_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service),
) -> SessionDetail:
    """
    获取会话详情
    
    包含完整的消息历史、使用情况等信息。
    
    **参数:**
    - `session_id`: 会话 ID
    
    **返回:**
    - 会话基本信息
    - 消息历史
    - Token 使用情况
    """
    
    detail = agent_service.get_session_detail(session_id)
    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"会话 {session_id} 不存在",
        )
    
    return detail


@router.delete(
    "/{session_id}",
    summary="删除会话",
    description="删除指定会话及其所有消息",
)
async def delete_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service),
) -> dict:
    """
    删除会话
    
    永久删除会话及其所有消息历史。
    
    **参数:**
    - `session_id`: 会话 ID
    
    **返回:**
    - 删除结果
    """
    
    try:
        await agent_service.cleanup_session(session_id)
        return {
            "success": True,
            "message": f"会话 {session_id} 已删除",
        }
    except Exception as e:
        logger.error("Delete session failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"删除失败：{str(e)}",
        )


@router.get(
    "/{session_id}/title",
    summary="获取会话标题",
    description="获取指定会话的标题",
)
async def get_session_title(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service),
) -> dict:
    """
    获取会话标题
    
    **参数:**
    - `session_id`: 会话 ID
    
    **返回:**
    - 会话标题
    """
    
    session = agent_service.get_session_info(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"会话 {session_id} 不存在",
        )
    
    return {
        "session_id": session_id,
        "title": session.title,
    }

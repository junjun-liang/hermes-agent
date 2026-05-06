#!/usr/bin/env python3
"""
工具管理 API 路由

提供工具列表、工具详情等端点
"""

import logging

from fastapi import APIRouter, Depends
from typing import List

from ..models.response import ToolInfo, ToolsListResponse
from ..services.agent_service import get_agent_service, AgentService
from model_tools import get_tool_definitions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["工具管理"])


@router.get(
    "/list",
    response_model=ToolsListResponse,
    summary="列出所有工具",
    description="获取当前可用的所有工具列表",
)
async def list_tools(
    agent_service: AgentService = Depends(get_agent_service),
) -> ToolsListResponse:
    """
    列出所有工具
    
    返回当前配置下所有可用的工具及其状态。
    
    **返回:**
    - 工具列表（名称、描述、所属工具集、可用性）
    - 工具集列表
    
    **示例:**
    ```json
    {
        "tools": [
            {
                "name": "web_search",
                "description": "搜索网络",
                "toolset": "web",
                "available": true
            },
            {
                "name": "read_file",
                "description": "读取文件",
                "toolset": "file",
                "available": true
            }
        ],
        "toolsets": ["web", "file", "code_execution"]
    }
    ```
    """
    
    try:
        # 获取工具定义
        tool_definitions = get_tool_definitions()
        
        tools: List[ToolInfo] = []
        toolsets = set()
        
        for tool_name, tool_def in tool_definitions.items():
            # 提取工具集
            toolset = tool_def.get("toolset", "unknown")
            toolsets.add(toolset)
            
            # 检查可用性
            available = True
            requires_env = tool_def.get("requires_env", [])
            
            # 检查环境变量
            if requires_env:
                import os
                for env_var in requires_env:
                    if not os.getenv(env_var):
                        available = False
                        break
            
            tools.append(
                ToolInfo(
                    name=tool_name,
                    description=tool_def.get("description", ""),
                    toolset=toolset,
                    available=available,
                    requires_env=requires_env if requires_env else None,
                )
            )
        
        return ToolsListResponse(
            tools=tools,
            toolsets=sorted(list(toolsets)),
        )
        
    except Exception as e:
        logger.error("List tools failed: %s", e, exc_info=True)
        return ToolsListResponse(tools=[], toolsets=[])


@router.get(
    "/info/{tool_name}",
    response_model=ToolInfo,
    summary="获取工具详情",
    description="获取指定工具的详细信息",
)
async def get_tool_info(
    tool_name: str,
    agent_service: AgentService = Depends(get_agent_service),
) -> ToolInfo:
    """
    获取工具详情
    
    **参数:**
    - `tool_name`: 工具名称
    
    **返回:**
    - 工具详细信息
    """
    
    try:
        tool_definitions = get_tool_definitions()
        
        if tool_name not in tool_definitions:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail=f"工具 {tool_name} 不存在",
            )
        
        tool_def = tool_definitions[tool_name]
        
        # 检查可用性
        available = True
        requires_env = tool_def.get("requires_env", [])
        if requires_env:
            import os
            for env_var in requires_env:
                if not os.getenv(env_var):
                    available = False
                    break
        
        return ToolInfo(
            name=tool_name,
            description=tool_def.get("description", ""),
            toolset=tool_def.get("toolset", "unknown"),
            available=available,
            requires_env=requires_env if requires_env else None,
        )
        
    except Exception as e:
        logger.error("Get tool info failed: %s", e, exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"获取工具信息失败：{str(e)}",
        )

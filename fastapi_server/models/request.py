#!/usr/bin/env python3
"""
请求数据模型

生产级别验证，包含详细的字段说明和验证规则
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Literal
import re


class ChatRequest(BaseModel):
    """聊天请求模型"""
    
    message: str = Field(
        ...,
        description="用户消息内容",
        min_length=1,
        max_length=50000,
        example="帮我创建一个 Python 快速排序算法",
    )
    
    session_id: Optional[str] = Field(
        None,
        description="会话 ID（不传则自动创建新会话）",
        pattern=r"^[a-zA-Z0-9_-]+$",
        example="session_abc123",
    )
    
    model: Optional[str] = Field(
        None,
        description="LLM 模型名称（不传则使用默认配置）",
        example="anthropic/claude-opus-4.6",
    )
    
    max_iterations: int = Field(
        50,
        ge=1,
        le=200,
        description="最大工具调用迭代次数",
        example=50,
    )
    
    max_cost_usd: Optional[float] = Field(
        None,
        ge=0.001,
        le=10.0,
        description="单次请求最大成本（USD）",
        example=0.10,
    )
    
    toolsets: Optional[List[str]] = Field(
        None,
        description="启用的工具集列表",
        example=["web", "file", "code_execution"],
    )
    
    disabled_tools: Optional[List[str]] = Field(
        None,
        description="禁用的具体工具列表",
        example=["terminal", "browser_navigate"],
    )
    
    stream: bool = Field(
        False,
        description="是否使用流式响应（SSE）",
    )
    
    system_message: Optional[str] = Field(
        None,
        description="自定义系统提示词",
        max_length=5000,
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="额外元数据",
    )
    
    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """验证消息内容"""
        if not v.strip():
            raise ValueError("消息不能为空")
        return v.strip()
    
    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        """验证会话 ID 格式"""
        if v and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("会话 ID 只能包含字母、数字、下划线和连字符")
        return v


class StreamChunk(BaseModel):
    """流式响应块"""
    
    type: Literal["text", "tool_start", "tool_complete", "thinking", "done", "error"] = Field(
        ...,
        description="块类型",
    )
    
    content: Optional[str] = Field(
        None,
        description="文本内容",
        max_length=10000,
    )
    
    tool_name: Optional[str] = Field(
        None,
        description="工具名称",
    )
    
    tool_args: Optional[Dict[str, Any]] = Field(
        None,
        description="工具参数",
    )
    
    tool_result: Optional[str] = Field(
        None,
        description="工具执行结果",
    )
    
    session_id: Optional[str] = Field(
        None,
        description="会话 ID",
    )
    
    error: Optional[str] = Field(
        None,
        description="错误信息",
    )
    
    timestamp: Optional[float] = Field(
        None,
        description="时间戳",
    )


class BatchChatRequest(BaseModel):
    """批量聊天请求（用于并发处理多个消息）"""
    
    messages: List[str] = Field(
        ...,
        description="消息列表",
        min_length=1,
        max_length=10,
    )
    
    session_id: Optional[str] = Field(
        None,
        description="共享会话 ID",
    )
    
    parallel: bool = Field(
        False,
        description="是否并行处理",
    )
    
    class Config:
        schema_extra = {
            "example": {
                "messages": ["问题 1", "问题 2"],
                "parallel": True,
            }
        }

#!/usr/bin/env python3
"""
响应数据模型

生产级别响应，包含完整的字段和验证
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class ToolCallInfo(BaseModel):
    """工具调用信息"""
    
    name: str = Field(..., description="工具名称")
    args: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    result: Optional[str] = Field(None, description="工具执行结果")
    success: bool = Field(True, description="是否执行成功")
    error: Optional[str] = Field(None, description="错误信息")
    duration: Optional[float] = Field(None, description="执行耗时（秒）")


class UsageInfo(BaseModel):
    """Token 使用量信息"""
    
    prompt_tokens: int = Field(0, description="输入 token 数")
    completion_tokens: int = Field(0, description="输出 token 数")
    total_tokens: int = Field(0, description="总 token 数")
    cache_read_tokens: Optional[int] = Field(0, description="缓存读取 token 数")
    cache_write_tokens: Optional[int] = Field(0, description="缓存写入 token 数")
    reasoning_tokens: Optional[int] = Field(0, description="推理 token 数")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    
    id: str = Field(
        default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}",
        description="响应唯一 ID",
    )
    
    object: str = Field("chat.completion", description="对象类型")
    
    created: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="创建时间戳",
    )
    
    session_id: str = Field(..., description="会话 ID")
    
    model: str = Field(..., description="使用的模型")
    
    response: str = Field(..., description="AI 响应内容")
    
    completed: bool = Field(True, description="是否完成（未被打断）")
    
    api_calls: int = Field(0, description="API 调用次数（LLM 调用次数）")
    
    iterations: int = Field(0, description="迭代次数（工具调用次数）")
    
    tool_calls: List[ToolCallInfo] = Field(
        default_factory=list,
        description="工具调用列表",
    )
    
    usage: Optional[UsageInfo] = Field(
        default_factory=UsageInfo,
        description="Token 使用量",
    )
    
    cost_usd: Optional[float] = Field(
        None,
        description="估算成本（USD）",
    )
    
    duration: float = Field(..., description="总处理耗时（秒）")
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="额外元数据",
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "chatcmpl_abc123",
                "session_id": "session_xyz789",
                "model": "anthropic/claude-opus-4.6",
                "response": "我已经为你创建了 Python 快速排序算法...",
                "completed": True,
                "api_calls": 2,
                "iterations": 1,
                "tool_calls": [
                    {
                        "name": "write_file",
                        "args": {"path": "quick_sort.py", "content": "..."},
                        "result": "文件已创建",
                        "success": True,
                        "duration": 0.5,
                    }
                ],
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 200,
                    "total_tokens": 350,
                },
                "cost_usd": 0.002,
                "duration": 3.5,
            }
        }


class StreamResponse(BaseModel):
    """流式响应"""
    
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    choices: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Optional[UsageInfo] = None


class SessionInfo(BaseModel):
    """会话信息"""
    
    session_id: str = Field(..., description="会话 ID")
    title: Optional[str] = Field(None, description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")
    message_count: int = Field(0, description="消息数量")
    model: str = Field(..., description="使用的模型")
    platform: str = Field("api", description="来源平台")
    status: str = Field("active", description="会话状态")
    cost_usd: Optional[float] = Field(None, description="累计成本")


class SessionDetail(SessionInfo):
    """会话详情（包含消息历史）"""
    
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="消息历史",
    )
    usage: Optional[UsageInfo] = Field(
        None,
        description="累计使用量",
    )


class ListSessionsResponse(BaseModel):
    """会话列表响应"""
    
    sessions: List[SessionInfo] = Field(default_factory=list)
    total: int = Field(0, description="总会话数")
    limit: int = Field(20, description="本次返回数量")
    offset: int = Field(0, description="偏移量")


class ToolInfo(BaseModel):
    """工具信息"""
    
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    toolset: str = Field(..., description="所属工具集")
    available: bool = Field(True, description="是否可用")
    requires_env: Optional[List[str]] = Field(None, description="所需环境变量")


class ToolsListResponse(BaseModel):
    """工具列表响应"""
    
    tools: List[ToolInfo] = Field(default_factory=list)
    toolsets: List[str] = Field(default_factory=list, description="所有工具集")


class HealthCheck(BaseModel):
    """健康检查响应"""
    
    status: str = Field("healthy", description="服务状态")
    version: str = Field(..., description="服务版本")
    uptime: float = Field(..., description="运行时间（秒）")
    agents_active: int = Field(0, description="活跃 Agent 数量")
    sessions_count: int = Field(0, description="总会话数")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="检查时间",
    )


class ReadinessCheck(HealthCheck):
    """就绪检查响应（包含依赖服务状态）"""
    
    database: str = Field("unknown", description="数据库状态")
    redis: Optional[str] = Field(None, description="Redis 状态")
    llm_provider: str = Field("unknown", description="LLM 提供商状态")


class ErrorResponse(BaseModel):
    """错误响应"""
    
    error: str = Field(..., description="错误类型")
    detail: str = Field("", description="错误详情")
    request_id: Optional[str] = Field(None, description="请求 ID（用于日志追踪）")
    timestamp: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="错误时间戳",
    )
    
    class Config:
        schema_extra = {
            "example": {
                "error": "RateLimitExceeded",
                "detail": "请求速率超限，请 1 分钟后重试",
                "request_id": "req_abc123",
                "timestamp": 1234567890,
            }
        }


class ConfigResponse(BaseModel):
    """配置响应（脱敏后的配置）"""
    
    model: str = Field(..., description="默认模型")
    max_iterations: int = Field(..., description="最大迭代次数")
    provider: str = Field(..., description="LLM 提供商")
    version: str = Field(..., description="服务版本")
    features: Dict[str, bool] = Field(
        default_factory=dict,
        description="功能开关",
    )

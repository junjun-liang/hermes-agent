#!/usr/bin/env python3
"""
聊天 API 路由

提供对话、流式响应等端点
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..config import settings
from ..models.request import ChatRequest, BatchChatRequest
from ..models.response import ChatResponse, StreamResponse
from ..services.agent_service import get_agent_service, AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post(
    "/completions",
    response_model=ChatResponse,
    summary="创建聊天补全",
    description="发送消息并获取 AI 响应（非流式）",
    response_description="AI 响应结果",
)
async def create_chat_completion(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    """
    创建聊天补全
    
    **功能:**
    - 发送单条消息
    - 支持会话延续（通过 session_id）
    - 自动工具调用
    - 成本估算
    
    **参数说明:**
    - `message`: 用户消息内容
    - `session_id`: 会话 ID（可选，不传则自动创建）
    - `model`: 模型名称（可选）
    - `max_iterations`: 最大迭代次数
    - `toolsets`: 启用的工具集
    
    **示例:**
    ```python
    POST /api/v1/chat/completions
    {
        "message": "帮我创建一个 Python 快速排序算法",
        "max_iterations": 50,
        "toolsets": ["file", "code_execution"]
    }
    ```
    """
    
    logger.info("Chat completion request: %s", request.message[:100])
    
    # 检查消息长度
    if len(request.message) > 50000:
        raise HTTPException(
            status_code=400,
            detail="消息过长，最大支持 50000 字符",
        )
    
    try:
        # 处理对话
        response = await agent_service.chat(request)
        
        logger.info(
            "Chat completion completed: session=%s, duration=%.2fs, cost=$%.6f",
            response.session_id,
            response.duration,
            response.cost_usd or 0,
        )
        
        return response
        
    except RuntimeError as e:
        logger.error("Chat failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Chat failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"处理失败：{str(e)}",
        )


@router.post(
    "/completions/stream",
    response_model=StreamResponse,
    summary="流式聊天补全",
    description="发送消息并获取流式 AI 响应（SSE）",
)
async def create_chat_completion_stream(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    """
    流式聊天补全
    
    使用 Server-Sent Events (SSE) 实时传输 AI 响应。
    
    **SSE 事件格式:**
    ```
    data: {"type": "text", "content": "你", "session_id": "..."}
    data: {"type": "text", "content": "好", "session_id": "..."}
    data: {"type": "tool_start", "tool_name": "web_search", ...}
    data: {"type": "tool_complete", "tool_name": "web_search", ...}
    data: {"type": "done", "content": "完整响应", ...}
    ```
    
    **客户端使用示例:**
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/completions/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'text') {
            console.log('收到文本:', data.content);
        } else if (data.type === 'done') {
            console.log('完成:', data.content);
            eventSource.close();
        }
    };
    ```
    """
    
    logger.info("Stream chat request: %s", request.message[:100])
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """生成流式响应"""
        try:
            async for chunk in agent_service.stream_chat(request):
                # 转换为 SSE 格式
                data = json.dumps(chunk.model_dump(exclude_none=True), ensure_ascii=False)
                yield f"data: {data}\n\n"
                
                # 如果是完成或错误，结束流
                if chunk.type in ["done", "error"]:
                    break
                    
        except Exception as e:
            logger.error("Stream failed: %s", e, exc_info=True)
            error_chunk = {
                "type": "error",
                "error": str(e),
                "timestamp": time.time(),
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 禁用缓冲
        },
    )


@router.post(
    "/batch",
    response_model=list[ChatResponse],
    summary="批量聊天",
    description="批量处理多个消息（可选并行）",
)
async def create_batch_chat(
    request: BatchChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> list[ChatResponse]:
    """
    批量聊天
    
    一次性处理多个消息，支持并行处理。
    
    **限制:**
    - 最多 10 条消息
    - 并行处理时共享 session_id
    
    **示例:**
    ```python
    POST /api/v1/chat/batch
    {
        "messages": ["问题 1", "问题 2", "问题 3"],
        "parallel": true
    }
    ```
    """
    
    if len(request.messages) > 10:
        raise HTTPException(
            status_code=400,
            detail="批量消息最多支持 10 条",
        )
    
    if request.parallel:
        # 并行处理
        tasks = [
            agent_service.chat(
                ChatRequest(
                    message=msg,
                    session_id=request.session_id,
                )
            )
            for msg in request.messages
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        results = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                logger.error("Batch message %d failed: %s", i, resp)
                results.append(
                    ChatResponse(
                        session_id=request.session_id or "unknown",
                        model="unknown",
                        response="",
                        completed=False,
                        duration=0,
                        metadata={"error": str(resp)},
                    )
                )
            else:
                results.append(resp)
        
        return results
    else:
        # 串行处理
        results = []
        for msg in request.messages:
            try:
                response = await agent_service.chat(
                    ChatRequest(
                        message=msg,
                        session_id=request.session_id,
                    )
                )
                results.append(response)
            except Exception as e:
                logger.error("Batch message failed: %s", e)
                results.append(
                    ChatResponse(
                        session_id=request.session_id or "unknown",
                        model="unknown",
                        response="",
                        completed=False,
                        duration=0,
                        metadata={"error": str(e)},
                    )
                )
        
        return results

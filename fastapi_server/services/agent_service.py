#!/usr/bin/env python3
"""
Agent 业务服务层

核心服务类，封装 AIAgent 实例管理、会话处理、工具调用等业务逻辑
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Callable
from pathlib import Path

from hermes_constants import get_hermes_home
from run_agent import AIAgent
from hermes_state import SessionDB
from ..config import settings
from ..models.request import ChatRequest, StreamChunk
from ..models.response import (
    ChatResponse,
    ToolCallInfo,
    UsageInfo,
    SessionInfo,
    SessionDetail,
)

logger = logging.getLogger(__name__)


class AgentService:
    """Agent 业务服务类
    
    功能:
    - Agent 实例池管理
    - 会话状态维护
    - 并发控制
    - 工具调用跟踪
    - 成本估算
    """
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}  # 会话信息缓存
        self.agents: Dict[str, AIAgent] = {}  # Agent 实例缓存
        self._lock = threading.Lock()
        self._active_count = 0
        self._max_concurrent = settings.max_concurrent_agents
        
        # 初始化会话数据库
        db_path = settings.session_db_path
        if not db_path:
            hermes_home = get_hermes_home()
            db_path = hermes_home / "state.db"
        elif isinstance(db_path, str):
            # 如果是字符串，转换为 Path 对象
            from pathlib import Path
            db_path = Path(db_path)
        
        try:
            self.session_db = SessionDB(db_path)
            logger.info("会话数据库已加载：%s", db_path)
        except Exception as e:
            logger.error("加载会话数据库失败：%s", e)
            self.session_db = None
        
        # 回调函数存储
        self._tool_calls: Dict[str, List[dict]] = {}  # session_id -> tool_calls
        
    async def create_agent(self, request: ChatRequest) -> AIAgent:
        """创建 Agent 实例
        
        Args:
            request: 聊天请求
            
        Returns:
            AIAgent 实例
        """
        
        # 检查并发限制
        with self._lock:
            if self._active_count >= self._max_concurrent:
                raise RuntimeError(
                    f"Max concurrent agents ({self._max_concurrent}) reached. "
                    "请稍后重试"
                )
            self._active_count += 1
        
        # 生成或使用现有会话 ID
        session_id = request.session_id or f"web_{uuid.uuid4().hex[:12]}"
        
        # 初始化工具调用跟踪
        self._tool_calls[session_id] = []
        
        def tool_start_callback(tool_name: str, args: dict):
            """工具开始回调"""
            tool_call = {
                "name": tool_name,
                "args": args,
                "start_time": time.time(),
                "result": None,
                "success": False,
                "error": None,
            }
            self._tool_calls[session_id].append(tool_call)
            logger.info("Tool started: %s", tool_name)
        
        def tool_complete_callback(tool_name: str, result: str, success: bool):
            """工具完成回调"""
            for tc in self._tool_calls.get(session_id, []):
                if tc["name"] == tool_name and tc["result"] is None:
                    tc["result"] = result
                    tc["success"] = success
                    tc["end_time"] = time.time()
                    tc["duration"] = tc["end_time"] - tc["start_time"]
                    if not success:
                        tc["error"] = result
                    break
            logger.info("Tool completed: %s, success=%s", tool_name, success)
        
        # 构建 Agent 参数
        agent_kwargs = {
            "session_id": session_id,
            "platform": "api",
            "quiet_mode": True,
            "save_trajectories": settings.save_trajectories,
            "max_iterations": request.max_iterations,
            "tool_start_callback": tool_start_callback,
            "tool_complete_callback": tool_complete_callback,
        }
        
        # 模型配置
        if request.model:
            agent_kwargs["model"] = request.model
        else:
            agent_kwargs["model"] = settings.default_model
        
        # 工具集配置
        if request.toolsets:
            agent_kwargs["enabled_toolsets"] = request.toolsets
        elif settings.enabled_toolsets:
            agent_kwargs["enabled_toolsets"] = settings.enabled_toolsets
        
        if request.disabled_tools:
            agent_kwargs["disabled_toolsets"] = request.disabled_tools
        elif settings.disabled_toolsets:
            agent_kwargs["disabled_toolsets"] = settings.disabled_toolsets
        
        # API 密钥配置（可选覆盖）
        api_key = self._get_api_key()
        if api_key:
            agent_kwargs["api_key"] = api_key
        
        # 创建 Agent 实例
        agent = AIAgent(**agent_kwargs)
        
        # 缓存会话信息
        with self._lock:
            self.sessions[session_id] = {
                "session_id": session_id,
                "created_at": datetime.now(),
                "last_updated": datetime.now(),
                "message_count": 0,
                "model": request.model or settings.default_model,
                "status": "active",
                "platform": "api",
            }
            self.agents[session_id] = agent
        
        logger.info("Agent created: session_id=%s, model=%s", session_id, agent.model)
        return agent
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """处理对话请求
        
        Args:
            request: 聊天请求
            
        Returns:
            聊天响应
        """
        
        start_time = time.time()
        
        # 创建 Agent
        agent = await self.create_agent(request)
        session_id = agent.session_id
        
        try:
            # 运行对话（在线程池中执行，避免阻塞）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: agent.run_conversation(
                    user_message=request.message,
                    system_message=request.system_message,
                )
            )
            
            # 收集工具调用信息
            tool_calls_info = self._build_tool_calls_info(session_id)
            
            # 提取使用情况
            usage = self._extract_usage(result)
            
            # 估算成本
            cost_usd = self._estimate_cost(usage, agent.model)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 更新会话
            self._update_session(session_id, result)
            
            return ChatResponse(
                session_id=session_id,
                model=agent.model,
                response=result.get("final_response", ""),
                completed=result.get("completed", True),
                api_calls=result.get("api_call_count", 0),
                iterations=len(tool_calls_info),
                tool_calls=tool_calls_info,
                usage=usage,
                cost_usd=cost_usd,
                duration=round(duration, 2),
                metadata=request.metadata,
            )
            
        except Exception as e:
            logger.error("Chat failed: %s", e, exc_info=True)
            raise
        finally:
            # 释放并发计数
            with self._lock:
                self._active_count -= 1
            # 清理临时数据
            self._tool_calls.pop(session_id, None)
    
    async def stream_chat(
        self, request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """流式对话
        
        Args:
            request: 聊天请求
            
        Yields:
            StreamChunk: 流式响应块
        """
        
        session_id = request.session_id or f"web_{uuid.uuid4().hex[:12]}"
        
        # 创建 Agent（带流式回调）
        agent = await self.create_agent(request)
        
        # 流式回调队列
        queue = asyncio.Queue()
        
        def stream_callback(text: str):
            """流式文本回调"""
            if text:
                asyncio.create_task(
                    queue.put(StreamChunk(
                        type="text",
                        content=text,
                        session_id=session_id,
                        timestamp=time.time(),
                    ))
                )
        
        try:
            # 在后台线程中运行对话
            def run_conversation():
                try:
                    result = agent.run_conversation(
                        user_message=request.message,
                        system_message=request.system_message,
                        stream_callback=stream_callback,
                    )
                    # 发送完成信号
                    asyncio.create_task(
                        queue.put(StreamChunk(
                            type="done",
                            content=result.get("final_response", ""),
                            session_id=session_id,
                            timestamp=time.time(),
                        ))
                    )
                except Exception as e:
                    asyncio.create_task(
                        queue.put(StreamChunk(
                            type="error",
                            error=str(e),
                            session_id=session_id,
                            timestamp=time.time(),
                        ))
                    )
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_conversation)
            
            # 流式输出
            while True:
                chunk = await queue.get()
                yield chunk
                if chunk.type == "done" or chunk.type == "error":
                    break
                    
        finally:
            with self._lock:
                self._active_count -= 1
            self._tool_calls.pop(session_id, None)
    
    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        with self._lock:
            session_data = self.sessions.get(session_id)
            if not session_data:
                return None
            return SessionInfo(**session_data)
    
    def get_session_detail(self, session_id: str) -> Optional[SessionDetail]:
        """获取会话详情（包含消息历史）"""
        if not self.session_db:
            return None
        
        try:
            session = self.session_db.get_session(session_id)
            if not session:
                return None
            
            # 构建详情
            messages = session.get("messages", [])
            usage_data = session.get("usage", {})
            
            usage = UsageInfo(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            
            return SessionDetail(
                session_id=session_id,
                title=session.get("title"),
                created_at=session.get("created_at", datetime.now()),
                updated_at=session.get("updated_at"),
                message_count=len(messages),
                model=session.get("model", "unknown"),
                platform=session.get("platform", "api"),
                status="active",
                messages=messages,
                usage=usage,
            )
        except Exception as e:
            logger.error("Get session detail failed: %s", e)
            return None
    
    def list_sessions(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SessionInfo]:
        """列出所有会话"""
        with self._lock:
            all_sessions = list(self.sessions.values())
        
        # 按时间倒序排序
        all_sessions.sort(
            key=lambda s: s.get("last_updated", s.get("created_at")),
            reverse=True,
        )
        
        # 分页
        paginated = all_sessions[offset:offset + limit]
        
        return [SessionInfo(**s) for s in paginated]
    
    async def cleanup_session(self, session_id: str):
        """清理会话"""
        with self._lock:
            if session_id in self.agents:
                agent = self.agents[session_id]
                # Agent 没有 close() 方法，直接删除引用
                del self.agents[session_id]
            if session_id in self.sessions:
                del self.sessions[session_id]
        
        logger.info("Session cleaned up: %s", session_id)
    
    def _build_tool_calls_info(self, session_id: str) -> List[ToolCallInfo]:
        """构建工具调用信息"""
        tool_calls = self._tool_calls.get(session_id, [])
        return [
            ToolCallInfo(
                name=tc["name"],
                args=tc["args"],
                result=tc.get("result"),
                success=tc.get("success", False),
                error=tc.get("error"),
                duration=round(tc.get("duration", 0), 2),
            )
            for tc in tool_calls
        ]
    
    def _extract_usage(self, result: dict) -> UsageInfo:
        """提取使用情况"""
        usage_data = result.get("usage", {})
        return UsageInfo(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            cache_read_tokens=usage_data.get("cache_read_tokens", 0),
            cache_write_tokens=usage_data.get("cache_write_tokens", 0),
            reasoning_tokens=usage_data.get("reasoning_tokens", 0),
        )
    
    def _estimate_cost(self, usage: UsageInfo, model: str) -> Optional[float]:
        """估算成本（USD）"""
        # 简化的成本估算（实际应根据具体模型定价）
        # Claude Opus: ~$15/1M input, ~$75/1M output
        if "opus" in model.lower():
            input_cost = usage.prompt_tokens * 15 / 1_000_000
            output_cost = usage.completion_tokens * 75 / 1_000_000
            return round(input_cost + output_cost, 6)
        elif "sonnet" in model.lower():
            # Claude Sonnet: ~$3/1M input, ~$15/1M output
            input_cost = usage.prompt_tokens * 3 / 1_000_000
            output_cost = usage.completion_tokens * 15 / 1_000_000
            return round(input_cost + output_cost, 6)
        else:
            # 默认不返回成本
            return None
    
    def _update_session(self, session_id: str, result: dict):
        """更新会话"""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]["last_updated"] = datetime.now()
                self.sessions[session_id]["message_count"] += 1
        
        # 保存到数据库
        if self.session_db:
            try:
                session = self.session_db.get_session(session_id)
                if session:
                    # 更新现有会话
                    session["updated_at"] = datetime.now().isoformat()
                    session["message_count"] = session.get("message_count", 0) + 1
                    
                    # 更新使用情况
                    usage_data = result.get("usage", {})
                    if "usage" not in session:
                        session["usage"] = {}
                    session["usage"].update(usage_data)
                    
                    self.session_db.save(session_id, session)
            except Exception as e:
                logger.error("Update session failed: %s", e)
    
    def _get_api_key(self) -> Optional[str]:
        """获取 API 密钥"""
        import os
        # 按优先级检查多个环境变量
        for key_name in ["DASHSCOPE_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY"]:
            api_key = os.getenv(key_name)
            if api_key:
                return api_key
        return None


# 全局服务实例（单例）
agent_service = AgentService()


def get_agent_service() -> AgentService:
    """获取 Agent 服务实例（依赖注入）"""
    return agent_service

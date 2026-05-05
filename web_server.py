#!/usr/bin/env python3
"""
Hermes Agent — FastAPI Web 服务

启动 FastAPI 网络服务，提供 RESTful API 给外部应用（如 Android App）调用 AI Agent。

功能：
- 聊天对话接口（同步/异步）
- 会话管理（创建、列表、删除、恢复）
- 会话历史查询
- 流式 SSE 响应
- 系统健康检查

启动方式：
    pip install "hermes-agent[web]"
    python web_server.py                          # 默认 8000 端口
    python web_server.py --host 0.0.0.0 --port 8080
    uvicorn web_server:app --host 0.0.0.0 --port 8000 --reload
"""

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator

# 加载 .env 环境变量
from hermes_constants import get_hermes_home
from hermes_cli.env_loader import load_hermes_dotenv

_hermes_home = get_hermes_home()
_project_env = Path(__file__).parent / '.env'
load_hermes_dotenv(hermes_home=_hermes_home, project_env=_project_env)

from fastapi import FastAPI, HTTPException, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import asyncio
from threading import Thread
import yaml

# 导入核心 Agent
sys.path.insert(0, str(Path(__file__).parent))
from run_agent import AIAgent
from hermes_state import SessionDB

# =============================================================================
# 日志配置
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_hermes_home / "logs" / "web_server.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("hermes-web")

# =============================================================================
# 全局状态
# =============================================================================
_session_db: Optional[SessionDB] = None
_active_agents: Dict[str, AIAgent] = {}  # session_id -> agent 实例映射

# =============================================================================
# 配置加载
# =============================================================================
def _load_web_config() -> dict:
    """从 config.yaml 加载 web 服务配置"""
    config_path = _hermes_home / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("web", {})
    except Exception:
        return {}

def _load_cli_config() -> dict:
    """加载 CLI 配置用于 AIAgent 初始化"""
    config_path = _hermes_home / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

# =============================================================================
# 生命周期
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期"""
    global _session_db
    
    # 启动
    logger.info("Hermes Agent Web 服务启动中...")
    _session_db = SessionDB(str(_hermes_home / "state.db"))
    logger.info("会话数据库已加载: %s/state.db", _hermes_home)
    
    yield
    
    # 关闭
    logger.info("Hermes Agent Web 服务关闭中...")
    if _session_db:
        _session_db.close()
    _active_agents.clear()
    logger.info("服务已关闭")

# =============================================================================
# FastAPI 应用
# =============================================================================
app = FastAPI(
    title="Hermes Agent API",
    description="AI Agent RESTful API — 供 Android App 等外部客户端调用",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 请求/响应模型
# =============================================================================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=50000)
    session_id: Optional[str] = Field(None, description="会话 ID（不传则自动创建新会话）")
    model: Optional[str] = Field(None, description="模型名称（不传则使用默认配置）")
    max_iterations: Optional[int] = Field(None, description="最大迭代次数", ge=1, le=200)
    toolsets: Optional[List[str]] = Field(None, description="启用的工具集列表")

class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str = Field(..., description="会话 ID")
    response: str = Field(..., description="Agent 回复内容")
    api_calls: int = Field(..., description="API 调用次数")
    duration: float = Field(..., description="处理时长（秒）")
    input_tokens: int = Field(0, description="输入 token 数")
    output_tokens: int = Field(0, description="输出 token 数")
    tools_used: List[str] = Field([], description="使用的工具列表")
    completed: bool = Field(True, description="是否完成")

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    title: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    message_count: int = 0
    cost_usd: Optional[float] = None

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    version: str = "1.0.0"
    uptime: float = 0
    active_sessions: int = 0

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: str = ""

# =============================================================================
# 启动时间戳
# =============================================================================
_START_TIME = time.time()

# =============================================================================
# 辅助函数
# =============================================================================

def _build_agent(session_id: str, request: ChatRequest, config: dict) -> AIAgent:
    """根据请求和配置构建 AIAgent 实例"""
    agent_kwargs = {
        "session_id": session_id,
        "platform": "web",
        "quiet_mode": True,
        "save_trajectories": config.get("save_trajectories", False),
    }
    
    # 模型配置
    if request.model:
        agent_kwargs["model"] = request.model
    elif config.get("model"):
        agent_kwargs["model"] = config["model"]
    
    # 迭代次数
    if request.max_iterations:
        agent_kwargs["max_iterations"] = request.max_iterations
    elif config.get("max_iterations"):
        agent_kwargs["max_iterations"] = config["max_iterations"]
    
    # 工具集配置
    if request.toolsets:
        agent_kwargs["enabled_toolsets"] = request.toolsets
    
    # API 密钥配置（可选覆盖）
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        agent_kwargs["api_key"] = api_key
    
    base_url = os.getenv("DASHSCOPE_BASE_URL") or os.getenv("OPENROUTER_BASE_URL")
    if base_url:
        agent_kwargs["base_url"] = base_url
    
    return AIAgent(**agent_kwargs)


def _parse_tools_used(messages: list) -> List[str]:
    """从消息历史中解析使用的工具"""
    tools = []
    for msg in messages:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                name = tc.get("function", {}).get("name", "")
                if name and name not in tools:
                    tools.append(name)
    return tools

# =============================================================================
# API 路由
# =============================================================================

@app.get("/", tags=["基础"])
async def root():
    """API 根路径"""
    return {
        "service": "Hermes Agent API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["基础"])
async def health_check():
    """健康检查接口"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=time.time() - _START_TIME,
        active_sessions=len(_active_agents),
    )


@app.post("/chat", response_model=ChatResponse, tags=["聊天"])
async def chat(request: ChatRequest):
    """
    聊天接口 — 发送用户消息，获取 Agent 回复
    
    Android App 调用示例：
    POST /chat
    {
        "message": "你好，帮我写一个 Python 排序算法",
        "session_id": "optional-session-id"
    }
    """
    start_time = time.time()
    
    try:
        # 确定 session_id
        session_id = request.session_id or f"web_{uuid.uuid4().hex[:12]}"
        
        # 加载配置
        config = _load_cli_config()
        
        # 构建 Agent
        agent = _build_agent(session_id, request, config)
        _active_agents[session_id] = agent
        
        # 执行对话
        result = agent.run_conversation(request.message)
        
        # 清理 agent 引用
        _active_agents.pop(session_id, None)
        
        # 提取工具使用情况
        tools_used = _parse_tools_used(result.get("messages", []))
        
        # 提取 token 使用情况
        usage = result.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        return ChatResponse(
            session_id=session_id,
            response=result.get("final_response", ""),
            api_calls=result.get("api_calls", 0),
            duration=round(time.time() - start_time, 2),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tools_used=tools_used,
            completed=result.get("completed", True),
        )
        
    except Exception as e:
        logger.exception("聊天请求失败: %s", e)
        raise HTTPException(status_code=500, detail=f"Agent 处理失败: {str(e)}")


@app.post("/chat/stream", tags=["聊天"])
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口 — SSE (Server-Sent Events)
    
    Android App 可以使用 OkHttp/SSE 库接收流式响应。
    """
    try:
        session_id = request.session_id or f"web_{uuid.uuid4().hex[:12]}"
        config = _load_cli_config()
        agent = _build_agent(session_id, request, config)
        _active_agents[session_id] = agent
        
        async def event_stream() -> AsyncGenerator[str, None]:
            try:
                # 使用 agent.chat() 获取最终响应
                # 注意：run_agent 的流式输出通过 callback 实现
                chunks = []
                
                def on_delta(delta: str):
                    """流式 delta 回调"""
                    if delta:
                        chunks.append(delta)
                
                # 覆盖 callback
                agent.stream_delta_callback = on_delta
                
                # 运行对话
                result = agent.run_conversation(request.message)
                final_response = result.get("final_response", "")
                
                # 发送完成事件
                yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'response': final_response}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.exception("流式请求失败: %s", e)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
            finally:
                _active_agents.pop(session_id, None)
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
        
    except Exception as e:
        logger.exception("流式请求初始化失败: %s", e)
        raise HTTPException(status_code=500, detail=f"流式请求失败: {str(e)}")


@app.get("/sessions", response_model=List[Dict[str, Any]], tags=["会话管理"])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    获取会话列表
    
    Android App 调用示例：GET /sessions?limit=10&offset=0
    """
    if not _session_db:
        raise HTTPException(status_code=500, detail="数据库未初始化")
    
    try:
        # 查询所有会话
        sessions = _session_db.search("")  # 空搜索返回全部
        # 按时间倒序排序
        sessions.sort(key=lambda s: s.get("updated_at", s.get("created_at", "")), reverse=True)
        
        # 分页
        paginated = sessions[offset:offset + limit]
        
        return [
            {
                "session_id": s.get("session_id", ""),
                "title": s.get("title"),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
                "message_count": len(s.get("messages", [])),
            }
            for s in paginated
        ]
    except Exception as e:
        logger.exception("获取会话列表失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", tags=["会话管理"])
async def get_session(session_id: str):
    """
    获取会话详情和历史消息
    
    Android App 调用示例：GET /sessions/{session_id}
    """
    if not _session_db:
        raise HTTPException(status_code=500, detail="数据库未初始化")
    
    try:
        session = _session_db.load(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        return {
            "session_id": session.get("session_id"),
            "title": session.get("title"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "messages": session.get("messages", []),
            "usage": session.get("usage", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取会话详情失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}", tags=["会话管理"])
async def delete_session(session_id: str):
    """
    删除会话
    
    Android App 调用示例：DELETE /sessions/{session_id}
    """
    if not _session_db:
        raise HTTPException(status_code=500, detail="数据库未初始化")
    
    try:
        if not _session_db.load(session_id):
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        _session_db.delete(session_id)
        return {"message": f"会话 {session_id} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("删除会话失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/title", tags=["会话管理"])
async def update_session_title(session_id: str, title: str = Query(..., description="新标题")):
    """
    更新会话标题
    
    Android App 调用示例：POST /sessions/{session_id}/title?title=我的对话
    """
    if not _session_db:
        raise HTTPException(status_code=500, detail="数据库未初始化")
    
    try:
        session = _session_db.load(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        session["title"] = title
        _session_db.save(session_id, session)
        return {"message": "标题已更新", "title": title}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("更新会话标题失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config", tags=["配置"])
async def get_config():
    """
    获取当前 Agent 配置（脱敏）
    
    用于 Android App 了解当前模型配置。
    """
    config = _load_cli_config()
    
    # 脱敏处理
    safe_config = {
        "model": config.get("model", ""),
        "max_iterations": config.get("max_iterations", 90),
        "provider": config.get("provider", ""),
        "version": "0.8.0",
    }
    
    return safe_config


# =============================================================================
# 运行入口
# =============================================================================
if __name__ == "__main__":
    import argparse
    import uvicorn
    
    parser = argparse.ArgumentParser(description="Hermes Agent FastAPI Web 服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    parser.add_argument("--reload", action="store_true", help="启用热重载（开发模式）")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("  Hermes Agent Web 服务")
    logger.info("  API 文档: http://%s:%d/docs", args.host, args.port)
    logger.info("  聊天接口: POST http://%s:%d/chat", args.host, args.port)
    logger.info("  会话管理: GET  http://%s:%d/sessions", args.host, args.port)
    logger.info("=" * 60)
    
    uvicorn.run(
        "web_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info",
    )

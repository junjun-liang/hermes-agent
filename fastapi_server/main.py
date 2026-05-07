#!/usr/bin/env python3
"""
Hermes-Agent FastAPI 服务主入口

生产级别 FastAPI 应用，包含完整的中间件、路由、错误处理
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge

from .config import settings, get_settings
from .routes import chat_router, sessions_router, tools_router, system_router
from .middleware import (
    APIKeyMiddleware,
    RateLimitMiddleware,
    LoggingMiddleware,
)

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Prometheus 指标（懒加载，避免模块重新加载时重复注册）
def _get_metrics():
    """获取指标（避免重复注册）"""
    from prometheus_client import REGISTRY, CollectorRegistry
    
    # 检查是否已注册
    try:
        collector = REGISTRY._names_to_collectors.get('hermes_requests_total')
        if collector is not None:
            # 已注册，返回现有指标
            return collector, REGISTRY._names_to_collectors.get('hermes_request_duration_seconds'), REGISTRY._names_to_collectors.get('hermes_agents_active')
    except (AttributeError, KeyError):
        pass
    
    # 未注册，创建新指标
    request_count = Counter(
        "hermes_requests_total",
        "Total number of requests",
        ["endpoint", "method", "status_code"],
    )
    
    request_duration = Histogram(
        "hermes_request_duration_seconds",
        "Request duration in seconds",
        ["endpoint"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    )
    
    agents_active = Gauge(
        "hermes_agents_active",
        "Number of active agents",
    )
    
    return request_count, request_duration, agents_active


# 初始化指标
REQUEST_COUNT, REQUEST_DURATION, AGENTS_ACTIVE = _get_metrics()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    
    # 启动时
    logger.info("=" * 60)
    logger.info("Hermes-Agent API 服务启动")
    logger.info("=" * 60)
    logger.info("版本：%s", settings.app_version)
    logger.info("调试模式：%s", settings.debug)
    logger.info("监听地址：%s:%d", settings.host, settings.port)
    logger.info("=" * 60)
    
    # 记录配置
    logger.info("默认模型：%s", settings.default_model)
    logger.info("最大迭代次数：%d", settings.max_iterations)
    logger.info("并发限制：%d", settings.max_concurrent_agents)
    logger.info("速率限制：%d 请求/分钟", settings.rate_limit_requests_per_minute)
    logger.info("=" * 60)
    
    yield
    
    # 关闭时
    logger.info("Hermes-Agent API 服务关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ========== 中间件配置 ==========

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# 日志中间件
app.add_middleware(LoggingMiddleware)

# 速率限制中间件
if settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)

# API Key 认证中间件
app.add_middleware(APIKeyMiddleware)


# ========== 全局错误处理 ==========

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    
    REQUEST_COUNT.labels(
        endpoint=request.url.path,
        method=request.method,
        status_code=exc.status_code,
    ).inc()
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    
    REQUEST_COUNT.labels(
        endpoint=request.url.path,
        method=request.method,
        status_code=500,
    ).inc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "服务器内部错误",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ========== 请求计时器 ==========

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """添加请求耗时头"""
    
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # 记录指标
    REQUEST_COUNT.labels(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
    ).inc()
    
    REQUEST_DURATION.labels(
        endpoint=request.url.path,
    ).observe(duration)
    
    # 添加耗时头
    response.headers["X-Process-Time"] = str(round(duration, 3))
    
    return response


# ========== 注册路由 ==========

app.include_router(chat_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")


# ========== 根路径 ==========

@app.get("/", tags=["根路径"])
async def root():
    """根路径欢迎信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# ========== 主程序 ==========

def main():
    """主程序入口"""
    
    uvicorn.run(
        "fastapi_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=not settings.debug,  # 生产环境关闭访问日志
        workers=1 if settings.debug else None,  # 开发模式单 worker
    )


if __name__ == "__main__":
    main()

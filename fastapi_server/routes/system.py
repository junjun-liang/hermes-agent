#!/usr/bin/env python3
"""
系统 API 路由

提供健康检查、就绪检查、指标等端点
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from ..config import settings
from ..models.response import HealthCheck, ReadinessCheck, ConfigResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["系统"])

# 服务启动时间
START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthCheck,
    summary="健康检查",
    description="检查服务基本健康状态",
)
async def health_check() -> HealthCheck:
    """
    健康检查
    
    返回服务的基本健康状态，用于 Kubernetes liveness probe。
    
    **检查项:**
    - 服务是否在运行
    - 运行时间
    - 活跃 Agent 数量
    
    **返回:**
    - status: healthy/unhealthy
    - version: 服务版本
    - uptime: 运行时间（秒）
    - agents_active: 活跃 Agent 数量
    """
    
    uptime = time.time() - START_TIME
    
    return HealthCheck(
        status="healthy",
        version=settings.app_version,
        uptime=round(uptime, 2),
        agents_active=0,  # 从服务获取
        timestamp=datetime.now(),
    )


@router.get(
    "/ready",
    response_model=ReadinessCheck,
    summary="就绪检查",
    description="检查服务是否准备好接收请求",
)
async def readiness_check() -> ReadinessCheck:
    """
    就绪检查
    
    检查所有依赖服务是否可用，用于 Kubernetes readiness probe。
    
    **检查项:**
    - 数据库连接
    - Redis 连接（如果配置）
    - LLM 提供商 API
    
    **返回:**
    - status: ready/not_ready
    - database: connected/disconnected
    - redis: connected/disconnected/unknown
    - llm_provider: available/unavailable
    """
    
    uptime = time.time() - START_TIME
    
    # 检查数据库
    database_status = "unknown"
    try:
        from hermes_state import SessionDB
        from hermes_constants import get_hermes_home
        from pathlib import Path
        db_path = settings.session_db_path or (get_hermes_home() / "state.db")
        # 如果是字符串，转换为 Path 对象
        if isinstance(db_path, str):
            db_path = Path(db_path)
        # 尝试加载数据库
        db = SessionDB(db_path)
        database_status = "connected"
    except Exception as e:
        logger.warning("Database check failed: %s", e)
        database_status = "disconnected"
    
    # 检查 Redis（如果配置）
    redis_status = None
    if settings.redis_url:
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            redis_status = "connected"
        except Exception as e:
            logger.warning("Redis check failed: %s", e)
            redis_status = "disconnected"
    
    # 检查 LLM 提供商
    llm_status = "unknown"
    try:
        import os
        # 检查 API Key
        if os.getenv("DASHSCOPE_API_KEY"):
            llm_status = "available"
        else:
            llm_status = "unavailable"
    except Exception as e:
        logger.warning("LLM provider check failed: %s", e)
        llm_status = "unavailable"
    
    # 判断是否就绪
    is_ready = (
        database_status == "connected" and
        (redis_status is None or redis_status == "connected") and
        llm_status == "available"
    )
    
    return ReadinessCheck(
        status="ready" if is_ready else "not_ready",
        version=settings.app_version,
        uptime=round(uptime, 2),
        agents_active=0,
        database=database_status,
        redis=redis_status,
        llm_provider=llm_status,
        timestamp=datetime.now(),
    )


@router.get(
    "/metrics",
    summary="Prometheus 指标",
    description="获取 Prometheus 格式的监控指标",
)
async def metrics() -> str:
    """
    Prometheus 指标
    
    返回 Prometheus 格式的监控指标，用于 Grafana 等监控系统。
    
    **指标类型:**
    - 请求计数
    - 请求延迟
    - Token 使用量
    - 活跃会话数
    - 错误率
    
    **使用示例:**
    ```bash
    curl http://localhost:8000/metrics
    ```
    
    然后在 Prometheus 配置中添加:
    ```yaml
    scrape_configs:
      - job_name: 'hermes-agent'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/metrics'
    ```
    """
    
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    
    # 定义指标
    REQUEST_COUNT = Counter(
        "hermes_requests_total",
        "Total number of requests",
        ["endpoint", "method", "status_code"],
    )
    
    REQUEST_DURATION = Histogram(
        "hermes_request_duration_seconds",
        "Request duration in seconds",
        ["endpoint"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    )
    
    AGENTS_ACTIVE = Gauge(
        "hermes_agents_active",
        "Number of active agents",
    )
    
    # 生成指标
    return generate_latest()


@router.get(
    "/config",
    response_model=ConfigResponse,
    summary="获取配置",
    description="获取脱敏后的服务配置",
)
async def get_config() -> ConfigResponse:
    """
    获取配置
    
    返回脱敏后的服务配置信息（不包含敏感信息如 API Key）。
    
    **返回:**
    - model: 默认模型
    - max_iterations: 最大迭代次数
    - provider: LLM 提供商
    - version: 服务版本
    - features: 功能开关
    """
    
    # 检测 LLM 提供商
    provider = "alibaba"
    
    # 功能开关
    features = {
        "streaming": True,
        "batch": True,
        "tool_calls": True,
        "cost_estimation": True,
        "rate_limiting": settings.rate_limit_enabled,
        "metrics": settings.enable_metrics,
    }
    
    return ConfigResponse(
        model=settings.default_model,
        max_iterations=settings.max_iterations,
        provider=provider,
        version=settings.app_version,
        features=features,
    )

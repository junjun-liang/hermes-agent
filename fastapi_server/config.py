#!/usr/bin/env python3
"""
FastAPI 服务配置管理

生产级别配置，支持环境变量、配置文件加载
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """服务配置类
    
    优先级:
    1. 环境变量
    2. .env 文件
    3. 默认值
    """
    
    # ========== 服务基础配置 ==========
    app_name: str = "Hermes-Agent API"
    app_version: str = "1.0.0"
    app_description: str = "Hermes AI Agent RESTful API - 供 Android App 等外部客户端调用"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # ========== Agent 核心配置 ==========
    default_model: str = "anthropic/claude-opus-4.6"
    max_iterations: int = 90
    tool_delay: float = 1.0
    save_trajectories: bool = False
    
    # 移动 API 安全工具集（排除 terminal、browser 等危险工具）
    enabled_toolsets: Optional[List[str]] = None  # None 表示使用默认
    disabled_toolsets: List[str] = ["messaging", "homeassistant", "cron"]
    
    # ========== 会话管理 ==========
    session_timeout: int = 3600  # 1 小时
    max_sessions_per_user: int = 10
    session_db_path: Optional[str] = None  # None 则使用默认 ~/.hermes/state.db
    
    # ========== 资源限制 ==========
    max_concurrent_agents: int = 10
    max_request_timeout: int = 300  # 5 分钟
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    
    # ========== 认证与安全 ==========
    api_keys: List[str] = []
    api_key_header: str = "X-API-Key"
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15
    
    # ========== CORS 配置 ==========
    cors_origins: List[str] = ["*"]  # 生产环境应设置具体域名
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # ========== 日志配置 ==========
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_format: str = "json"  # json 或 text
    
    # ========== 速率限制 ==========
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_redis_url: Optional[str] = None
    
    # ========== 监控与指标 ==========
    enable_metrics: bool = True
    prometheus_port: int = 9090
    sentry_dsn: Optional[str] = None
    
    # ========== 性能优化 ==========
    use_uvloop: bool = True
    use_httptools: bool = True
    worker_connections: int = 1000
    
    # ========== Redis 配置（分布式会话存储） ==========
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（使用 lru_cache 缓存）"""
    return Settings()


# 全局配置实例（便于导入）
settings = get_settings()


def reload_settings() -> Settings:
    """重新加载配置（用于热重载）"""
    get_settings.cache_clear()
    return get_settings()

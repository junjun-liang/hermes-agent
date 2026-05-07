#!/usr/bin/env python3
"""
认证中间件

支持 API Key 和 JWT 两种认证方式
"""

import logging
import time
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings

logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key 认证中间件
    
    支持两种认证方式:
    1. Header: X-API-Key
    2. Bearer Token (JWT)
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.http_bearer = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """处理请求认证"""
        
        # 跳过健康检查、文档和指标端点
        # 注意：健康检查在 /api/v1/health，不是 /health
        skip_paths = [
            "/",  # 根路径
            "/health", "/ready", "/metrics",  # 根路径
            "/api/v1/health", "/api/v1/ready", "/api/v1/metrics",  # API v1 路径
            "/docs", "/redoc", "/openapi.json",  # 文档
        ]
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # 尝试 API Key 认证
        api_key = request.headers.get(settings.api_key_header)
        if api_key:
            if self._validate_api_key(api_key):
                request.state.authenticated = True
                request.state.api_key = api_key
                return await call_next(request)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的 API Key",
                    headers={"WWW-Authenticate": "API-Key"},
                )
        
        # 尝试 JWT 认证
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            if self._validate_jwt(token):
                request.state.authenticated = True
                request.state.token = token
                return await call_next(request)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的 JWT Token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # 未认证
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "API-Key, Bearer"},
        )
    
    def _validate_api_key(self, api_key: str) -> bool:
        """验证 API Key"""
        if not settings.api_keys:
            # 未配置 API Key 时，允许任何 Key（开发模式）
            return True
        return api_key in settings.api_keys
    
    def _validate_jwt(self, token: str) -> bool:
        """验证 JWT Token"""
        if not settings.jwt_secret_key:
            # 未配置 JWT 密钥时，允许任何 Token（开发模式）
            return True
        
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            # 检查过期时间
            exp = payload.get("exp")
            if exp and exp < time.time():
                logger.warning("JWT Token 已过期")
                return False
            return True
        except JWTError as e:
            logger.warning("JWT 验证失败：%s", e)
            return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件
    
    使用滑动窗口算法限制请求频率
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.requests: dict = {}  # IP -> [timestamp, ...]
        self._lock = None  # asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next):
        """处理速率限制"""
        
        # 如果未启用速率限制，直接放行
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # 获取客户端 IP
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        window_start = current_time - 60  # 1 分钟窗口
        
        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip]
                if ts > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # 检查是否超限
        if len(self.requests[client_ip]) >= settings.rate_limit_requests_per_minute:
            logger.warning("Rate limit exceeded for IP: %s", client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求速率超限，请 1 分钟后重试",
                headers={"X-RateLimit-Reset": str(int(window_start + 60))},
            )
        
        # 记录请求
        self.requests[client_ip].append(current_time)
        
        # 添加速率限制头
        response = await call_next(request)
        remaining = settings.rate_limit_requests_per_minute - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(window_start + 60))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP（考虑代理）"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件
    
    记录所有请求的详细信息，用于审计和调试
    """
    
    async def dispatch(self, request: Request, call_next):
        """记录请求日志"""
        
        # 生成请求 ID
        request_id = f"req_{int(time.time() * 1000)}_{id(request)}"
        request.state.request_id = request_id
        
        # 记录请求开始
        start_time = time.time()
        logger.info(
            "Request started: %s %s (ID: %s)",
            request.method,
            request.url.path,
            request_id,
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 记录响应
            duration = time.time() - start_time
            logger.info(
                "Request completed: %s %s (ID: %s, Status: %s, Duration: %.3fs)",
                request.method,
                request.url.path,
                request_id,
                response.status_code,
                duration,
            )
            
            # 添加请求 ID 到响应头
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except HTTPException as e:
            # HTTP 异常
            duration = time.time() - start_time
            logger.warning(
                "HTTP error: %s %s (ID: %s, Status: %s, Duration: %.3fs)",
                request.method,
                request.url.path,
                request_id,
                e.status_code,
                duration,
            )
            raise
        except Exception as e:
            # 其他异常
            duration = time.time() - start_time
            logger.error(
                "Server error: %s %s (ID: %s, Error: %s, Duration: %.3fs)",
                request.method,
                request.url.path,
                request_id,
                e,
                duration,
                exc_info=True,
            )
            raise


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS 中间件
    
    处理跨域请求
    """
    
    async def dispatch(self, request: Request, call_next):
        """处理 CORS"""
        
        # 如果是 OPTIONS 预检请求，直接返回
        if request.method == "OPTIONS":
            from starlette.responses import PlainTextResponse
            response = PlainTextResponse("")
            self._add_cors_headers(response)
            return response
        
        # 处理正常请求
        response = await call_next(request)
        self._add_cors_headers(response)
        return response
    
    def _add_cors_headers(self, response):
        """添加 CORS 头"""
        if settings.cors_origins == ["*"]:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            # 具体域名
            response.headers["Access-Control-Allow-Origin"] = ", ".join(settings.cors_origins)
        
        if settings.cors_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        if settings.cors_methods == ["*"]:
            response.headers["Access-Control-Allow-Methods"] = "*"
        else:
            response.headers["Access-Control-Allow-Methods"] = ", ".join(settings.cors_methods)
        
        if settings.cors_headers == ["*"]:
            response.headers["Access-Control-Allow-Headers"] = "*"
        else:
            response.headers["Access-Control-Allow-Headers"] = ", ".join(settings.cors_headers)

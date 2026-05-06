# Hermes Agent - 生产环境部署规范

## 执行摘要

本文档提供了生产级别的规范，用于将 Hermes AI Agent 部署为 FastAPI 服务，供 Android 应用使用。该部署方案从 CLI/消息平台架构中提取核心 Agent 功能，并通过安全、可扩展的 REST API 进行暴露。

***

## 目录

1. [架构概览](#1-架构概览)
2. [组件提取](#2-组件提取)
3. [FastAPI 服务设计](#3-fastapi-服务设计)
4. [认证与安全](#4-认证与安全)
5. [部署架构](#5-部署架构)
6. [配置管理](#6-配置管理)
7. [数据库与状态管理](#7-数据库与状态管理)
8. [工具配置](#8-工具配置)
9. [监控与可观测性](#9-监控与可观测性)
10. [扩展策略](#10-扩展策略)
11. [实施路线图](#11-实施路线图)

***

## 1. 架构概览

### 1.1 当前架构

```
┌─────────────────────────────────────────────────────────┐
│                  Hermes Agent (当前)                     │
├─────────────────────────────────────────────────────────┤
│  CLI / 网关 (Telegram, Discord, Slack 等)               │
│  ├── cli.py (交互式终端)                                │
│  └── gateway/ (消息平台)                                │
│                        ↓                                │
│  run_agent.py (AIAgent 类 - 对话循环)                   │
│  ├── model_tools.py (工具编排)                          │
│  ├── tools/registry.py (工具注册)                       │
│  ├── toolsets.py (工具集定义)                           │
│  └── hermes_state.py (SQLite 会话存储)                  │
│                        ↓                                │
│  外部 API (LLM 提供商、web、终端等)                      │
└─────────────────────────────────────────────────────────┘
```

### 1.2 目标架构

```
┌─────────────────────────────────────────────────────────┐
│                  Android 应用                            │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│              负载均衡器 (nginx/ALB)                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│          FastAPI 服务集群 (Kubernetes)                   │
├─────────────────────────────────────────────────────────┤
│  /api/v1/chat/completions  (OpenAI 兼容 API)            │
│  /api/v1/chat/sessions     (会话管理)                   │
│  /api/v1/chat/history      (对话历史)                   │
│  /api/v1/tools/list        (可用工具)                   │
│  /health, /ready, /metrics (可观测性)                   │
│                                                         │
│  中间件栈：                                              │
│  ├── JWT 认证                                            │
│  ├── 速率限制 (Redis)                                    │
│  ├── 请求验证                                            │
│  ├── CORS 配置                                           │
│  └── 结构化日志                                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│               支撑服务                                    │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL (会话、用户、审计日志)                       │
│  Redis (速率限制、缓存、发布/订阅)                       │
│  S3/MinIO (文件存储、轨迹)                              │
│  Prometheus + Grafana (指标)                            │
│  ELK/Loki (日志)                                        │
└─────────────────────────────────────────────────────────┘
```

***

## 2. 组件提取

### 2.1 需要提取的核心组件

以下组件构成 API 部署的最小可行 Agent：

#### **核心必需组件** (必须包含)

```
run_agent.py          # AIAgent 类 - 主对话循环
model_tools.py        # 工具编排层
tools/registry.py     # 中央工具注册表
toolsets.py           # 工具集定义
hermes_state.py       # 会话持久化 (升级到 PostgreSQL)
hermes_constants.py   # 路径助手、常量
```

#### **Agent 包** (必须包含)

```
agent/
├── __init__.py
├── memory_manager.py      # 内存上下文构建
├── prompt_builder.py      # 系统提示组装
├── context_compressor.py  # 自动上下文压缩
├── error_classifier.py    # API 错误分类
├── model_metadata.py      # Token 估算、限制
├── prompt_caching.py      # Anthropic 缓存控制
├── retry_utils.py         # 抖动退避
├── usage_pricing.py       # 成本估算
└── display.py             # 工具预览格式化
```

#### **工具选择** (生产安全子集)

**移动 API 推荐工具集：**

```python
# 安全、只读工具（无终端访问）
SAFE_MOBILE_TOOLS = [
    # Web 研究
    "web_search", "web_extract",
    # 文件操作（沙箱）
    "read_file", "write_file", "patch", "search_files",
    # 视觉
    "vision_analyze",
    # 规划与内存
    "todo", "memory",
    # 会话历史
    "session_search",
    # 代码执行（仅限沙箱）
    "execute_code",  # 使用 modal/docker 后端
    # 委托
    "delegate_task",
]
```

**排除的工具** (移动设备安全风险)：

- `terminal` - 直接 shell 访问
- `process` - 进程管理
- `browser_*` - 重量级资源使用
- `ha_*` - Home Assistant（需要用户配置）
- `send_message` - 消息平台工具
- `cronjob` - 计划任务
- `text_to_speech` - 最好在客户端处理

### 2.2 依赖树

```
hermes-agent-api
├── 核心依赖
│   ├── openai>=2.21.0,<3
│   ├── anthropic>=0.39.0,<1
│   ├── httpx[socks]>=0.28.1,<1
│   ├── pydantic>=2.12.5,<3
│   └── pyyaml>=6.0.2,<7
│
├── Web 工具
│   ├── exa-py>=2.9.0,<3
│   ├── firecrawl-py>=4.16.0,<5
│   └── parallel-web>=0.4.2,<1
│
├── 代码执行
│   ├── modal>=1.0.0,<2  或  daytona>=0.148.0,<1
│   └── fal-client>=0.13.1,<1
│
├── FastAPI 栈
│   ├── fastapi>=0.104.0,<1
│   ├── uvicorn[standard]>=0.24.0,<1
│   ├── python-jose[cryptography]  # JWT
│   └── redis>=5.0.0,<6  # 速率限制
│
└── 可观测性
    ├── prometheus-client>=0.19.0,<1
    ├── structlog>=24.0.0,<25
    └── sentry-sdk>=2.0.0,<3
```

***

## 3. FastAPI 服务设计

### 3.1 API 端点

#### **3.1.1 聊天补全 (OpenAI 兼容)**

```python
# POST /api/v1/chat/completions
@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    auth: AuthData = Depends(require_auth),
) -> ChatCompletionResponse:
    """
    OpenAI 兼容的聊天补全端点。
    
    请求:
    {
        "model": "claude-opus-4.6",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": false,
        "max_tokens": 4096,
        "temperature": 0.7,
        "metadata": {
            "session_id": "uuid",
            "user_id": "uuid"
        }
    }
    
    响应:
    {
        "id": "chatcmpl-uuid",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "claude-opus-4.6",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "你好！我能帮你什么？"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        },
        "metadata": {
            "session_id": "uuid",
            "tool_calls": 0,
            "iterations": 1,
            "cost_usd": 0.0001
        }
    }
    """
```

#### **3.1.2 流式支持**

```python
# POST /api/v1/chat/completions (stream=true)
@router.post("/chat/completions")
async def create_chat_completion_stream(
    request: ChatCompletionRequest,
    auth: AuthData = Depends(require_auth),
) -> StreamingResponse:
    """
    使用 Server-Sent Events (SSE) 流式传输实时响应。
    
    产生:
    data: {"id":"chatcmpl-uuid","choices":[{"delta":{"content":"你"}}]}
    data: {"id":"chatcmpl-uuid","choices":[{"delta":{"content":"好"}}]}
    data: [DONE]
    """
```

#### **3.1.3 会话管理**

```python
# GET /api/v1/chat/sessions
@router.get("/sessions")
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    auth: AuthData = Depends(require_auth),
) -> ListSessionsResponse:
    """列出用户的对话会话。"""

# GET /api/v1/chat/sessions/{session_id}
@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    auth: AuthData = Depends(require_auth),
) -> SessionDetail:
    """获取会话详情及消息历史。"""

# DELETE /api/v1/chat/sessions/{session_id}
@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    auth: AuthData = Depends(require_auth),
) -> dict:
    """删除会话及其所有消息。"""

# POST /api/v1/chat/sessions/{session_id}/title
@router.post("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str,
    auth: AuthData = Depends(require_auth),
) -> dict:
    """更新会话标题。"""
```

#### **3.1.4 工具管理**

```python
# GET /api/v1/tools/list
@router.get("/tools/list")
async def list_available_tools(
    auth: AuthData = Depends(require_auth),
) -> ToolsListResponse:
    """
    列出认证用户的所有可用工具。
    
    响应:
    {
        "tools": [
            {
                "name": "web_search",
                "description": "搜索网络",
                "toolset": "web",
                "available": true
            },
            ...
        ]
    }
    """
```

#### **3.1.5 健康与指标**

```python
# GET /health
@router.get("/health")
async def health_check() -> dict:
    """基础健康检查。"""

# GET /ready
@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """Kubernetes 就绪探针 - 检查数据库、Redis、LLM 连接。"""

# GET /metrics
@router.get("/metrics")
async def metrics() -> str:
    """Prometheus 指标端点。"""
```

### 3.2 请求/响应模型

```python
# schemas/chat.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import uuid

class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[str] = None  # 用于具有推理能力的模型

class ChatCompletionRequest(BaseModel):
    model: str = "anthropic/claude-opus-4.6"
    messages: List[Message]
    stream: bool = False
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    
    # 会话管理
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # 工具配置
    enabled_toolsets: Optional[List[str]] = None
    disabled_tools: Optional[List[str]] = None
    
    # 预算控制
    max_iterations: int = 50
    max_cost_usd: Optional[float] = 0.10

class ChatChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cache_read_tokens: Optional[int] = 0
    cache_write_tokens: Optional[int] = 0
    reasoning_tokens: Optional[int] = 0

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    model: str
    choices: List[ChatChoice]
    usage: Usage
    metadata: Optional[Dict[str, Any]] = None

class SessionInfo(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    model: str
    cost_usd: float

class ListSessionsResponse(BaseModel):
    sessions: List[SessionInfo]
    total: int
    limit: int
    offset: int
```

### 3.3 服务层

```python
# services/agent_service.py
from typing import AsyncGenerator, Dict, Any, Optional
from run_agent import AIAgent
from model_tools import get_tool_definitions, handle_function_call
from hermes_state import SessionDB
from tools.registry import registry

class AgentService:
    """
    核心 Agent 服务，为 API 消费封装 AIAgent。
    
    处理:
    - 会话管理
    - 工具执行
    - Token 跟踪
    - 成本估算
    - 流式响应
    """
    
    def __init__(
        self,
        session_db: SessionDB,
        max_iterations: int = 50,
        enabled_toolsets: List[str] = None,
        disabled_toolsets: List[str] = None,
    ):
        self.session_db = session_db
        self.max_iterations = max_iterations
        self.enabled_toolsets = enabled_toolsets or ["hermes-api-server"]
        self.disabled_toolsets = disabled_toolsets or []
        
    async def chat(
        self,
        messages: List[Message],
        model: str,
        session_id: str,
        user_id: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> ChatCompletionResponse:
        """
        执行单个聊天轮次。
        
        1. 创建/加载会话
        2. 初始化工具定义的 AIAgent
        3. 运行对话循环
        4. 保存消息到会话
        5. 返回带使用统计的响应
        """
        
    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        session_id: str,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        使用 Server-Sent Events 流式传输聊天响应。
        
        在可用时产生 JSON 块。
        """
```

***

## 4. 认证与安全

### 4.1 认证策略

**基于 JWT 的认证**，带 API Key 后备：

```python
# middleware/auth.py
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

security = HTTPBearer()

class AuthData(BaseModel):
    user_id: str
    api_key_id: str
    permissions: List[str]
    rate_limit_tier: str  # "free", "pro", "enterprise"

async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> AuthData:
    """
    验证 Authorization header 中的 JWT token。
    
    Token 格式：Bearer <jwt_token>
    
    Claims:
    - sub: user_id
    - api_key_id: 使用的 API Key 标识符
    - permissions: 允许的操作列表
    - rate_limit_tier: 速率限制层级
    - exp: 过期时间戳
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return AuthData(
            user_id=payload["sub"],
            api_key_id=payload["api_key_id"],
            permissions=payload.get("permissions", ["chat:create"]),
            rate_limit_tier=payload.get("rate_limit_tier", "free"),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证凭据无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 4.2 API Key 管理

```python
# models/api_key.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import secrets

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: f"key_{secrets.token_urlsafe(24)}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # 用户提供的名称（如"Android 应用"）
    key_hash = Column(String, nullable=False)  # 哈希密钥 (bcrypt)
    key_prefix = Column(String, nullable=False)  # 前 8 个字符用于识别
    permissions = Column(JSON, default=["chat:create", "sessions:read"])
    rate_limit_tier = Column(String, default="free")
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    @classmethod
    def create(cls, user_id: str, name: str, permissions: List[str] = None) -> "APIKey":
        """生成新的 API Key。"""
        raw_key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()
        key_prefix = raw_key[:8]
        
        return cls(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions or ["chat:create", "sessions:read"],
        )
    
    def verify(self, raw_key: str) -> bool:
        """验证原始密钥与哈希。"""
        return bcrypt.checkpw(raw_key.encode(), self.key_hash.encode())
```

### 4.3 速率限制

```python
# middleware/rate_limiter.py
from fastapi import HTTPException, status
from redis.asyncio import Redis
from typing import Dict

RATE_LIMITS = {
    "free": {"requests_per_minute": 20, "tokens_per_day": 50000},
    "pro": {"requests_per_minute": 60, "tokens_per_day": 500000},
    "enterprise": {"requests_per_minute": 300, "tokens_per_day": 10000000},
}

async def rate_limit_middleware(
    request: Request,
    call_next,
    redis: Redis,
    auth: AuthData,
):
    """
    使用 Redis 滑动窗口进行速率限制。
    
    Keys:
    - rate_limit:{user_id}:requests  (有序集合，score=时间戳)
    - rate_limit:{user_id}:tokens    (计数器，每日重置)
    """
    limits = RATE_LIMITS.get(auth.rate_limit_tier, RATE_LIMITS["free"])
    
    # 检查每分钟请求数
    now = time.time()
    window_start = now - 60
    
    key = f"rate_limit:{auth.user_id}:requests"
    redis.zremrangebyscore(key, 0, window_start)
    count = await redis.zcard(key)
    
    if count >= limits["requests_per_minute"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="超过速率限制。请 1 分钟后重试。",
            headers={"X-RateLimit-Reset": str(int(window_start + 60))},
        )
    
    # 检查每日 token 数
    token_key = f"rate_limit:{auth.user_id}:tokens"
    tokens_used = await redis.get(token_key) or 0
    
    # 增加请求计数
    redis.zadd(key, {str(uuid.uuid4()): now})
    redis.expire(key, 120)  # 2 分钟 TTL
    
    response = await call_next(request)
    
    # 从响应更新 token 计数
    if hasattr(response, "body"):
        # 从响应体解析使用情况
        pass
    
    return response
```

### 4.4 安全检查清单

- [ ] **输入验证**: 所有用户输入使用 Pydantic 验证
- [ ] **SQL 注入防护**: SQLAlchemy ORM 带参数化查询
- [ ] **XSS 防护**: 所有文本输出进行 HTML 清理
- [ ] **CORS 配置**: Android 应用的严格来源白名单
- [ ] **仅 HTTPS**: 强制 TLS 1.3
- [ ] **API Key 哈希**: bcrypt 加盐
- [ ] **JWT 过期**: 短期 token（15 分钟）带刷新 token
- [ ] **请求大小限制**: 每个请求最大 10MB
- [ ] **超时强制**: 每个请求最大 120 秒
- [ ] **审计日志**: 所有 API 调用记录用户 ID、时间戳、操作

***

## 5. 部署架构

### 5.1 Kubernetes 部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hermes-agent-api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hermes-agent-api
  template:
    metadata:
      labels:
        app: hermes-agent-api
    spec:
      containers:
      - name: api
        image: registry.example.com/hermes-agent-api:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: hermes-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: hermes-secrets
              key: redis-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: hermes-secrets
              key: jwt-secret
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: hermes-secrets
              key: anthropic-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: hermes-secrets
              key: openai-api-key
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: hermes-agent-api
  namespace: production
spec:
  selector:
    app: hermes-agent-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hermes-agent-api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hermes-agent-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### 5.2 Docker 配置

```dockerfile
# Dockerfile
FROM python:3.12-slim

# 安全：非 root 用户
RUN useradd --create-home --shell /bin/bash hermes
USER hermes

WORKDIR /app

# 安装依赖
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# 复制应用
COPY --chown=hermes:hermes . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# 使用 uvicorn 运行
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

```yaml
# docker-compose.yml (用于本地开发)
version: '3.8'

services:
  api:
    build: .
    ports:
    - "8000:8000"
    environment:
    - DATABASE_URL=postgresql://hermes:password@db:5432/hermes
    - REDIS_URL=redis://redis:6379/0
    - JWT_SECRET_KEY=dev-secret-key-change-in-production
    volumes:
    - ./api:/app/api
    - ./run_agent.py:/app/run_agent.py
    - ./model_tools.py:/app/model_tools.py
    - ./tools:/app/tools
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:16-alpine
    environment:
    - POSTGRES_DB=hermes
    - POSTGRES_USER=hermes
    - POSTGRES_PASSWORD=password
    volumes:
    - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hermes"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
    - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 5.3 基础设施需求

**生产环境 (1 万日活目标):**

- **Kubernetes 集群**: 3-5 个节点（4 CPU, 16GB RAM 每个）
- **PostgreSQL**: 托管服务 (AWS RDS / GCP Cloud SQL) - 2 vCPU, 8GB RAM
- **Redis**: 托管服务 (ElastiCache / Memorystore) - 1GB 缓存
- **负载均衡器**: AWS ALB / GCP 负载均衡
- **对象存储**: S3 / GCS 用于文件存储
- **CDN**: CloudFlare / CloudFront 用于静态资源

**预估月度成本 (AWS):**

- EKS 集群：$73.50
- 3x m5.xlarge 节点：\~$150
- RDS PostgreSQL (db.t3.medium): \~$60
- ElastiCache Redis (cache.t3.small): \~$20
- ALB: \~$25
- **总计**: \~$330/月（不含 API 成本）

***

## 6. 配置管理

### 6.1 环境变量

```bash
# .env.example

# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/hermes

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT 配置
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_DAYS=30

# LLM 提供商
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...

# 工具配置
FIRECRAWL_API_KEY=fc-...
EXA_API_KEY=exa-...

# 安全
CORS_ORIGINS=https://your-android-app.com
ALLOWED_HOSTS=api.example.com

# 速率限制
RATE_LIMIT_REDIS_URL=redis://localhost:6379/1

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=https://...@sentry.io/...

# 功能开关
ENABLED_TOOLSETS=hermes-api-server
DISABLED_TOOLSETS=messaging,homeassistant
MAX_ITERATIONS_DEFAULT=50
MAX_COST_PER_REQUEST_USD=0.10

# 会话管理
SESSION_MAX_AGE_DAYS=90
SESSION_PRUNE_INTERVAL_HOURS=24
```

### 6.2 配置模块

```python
# api/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # 数据库
    database_url: str
    redis_url: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15
    
    # LLM 提供商
    anthropic_api_key: str
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # 工具
    firecrawl_api_key: Optional[str] = None
    exa_api_key: Optional[str] = None
    
    # 安全
    cors_origins: List[str] = ["*"]
    allowed_hosts: List[str] = ["*"]
    
    # 速率限制
    rate_limit_redis_url: Optional[str] = None
    
    # 日志
    log_level: str = "INFO"
    log_format: str = "json"
    sentry_dsn: Optional[str] = None
    
    # 功能开关
    enabled_toolsets: List[str] = ["hermes-api-server"]
    disabled_toolsets: List[str] = []
    max_iterations_default: int = 50
    max_cost_per_request_usd: float = 0.10
    
    # 会话管理
    session_max_age_days: int = 90
    session_prune_interval_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

***

## 7. 数据库与状态管理

### 7.1 PostgreSQL 模式

```sql
-- migrations/001_initial_schema.sql

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'
);

-- API Keys
CREATE TABLE api_keys (
    id VARCHAR(64) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(8) NOT NULL,
    permissions JSONB DEFAULT '["chat:create", "sessions:read"]',
    rate_limit_tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_prefix ON api_keys(key_prefix);

-- 会话表 (从 SQLite 升级)
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'api',
    model TEXT,
    model_config JSONB,
    system_prompt TEXT,
    parent_session_id TEXT REFERENCES sessions(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    billing_base_url TEXT,
    billing_mode TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    cost_status TEXT,
    cost_source TEXT,
    pricing_version TEXT,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_source ON sessions(source);
CREATE INDEX idx_sessions_parent ON sessions(parent_session_id);
CREATE INDEX idx_sessions_started ON sessions(started_at DESC);
CREATE UNIQUE INDEX idx_sessions_title_unique ON sessions(title) WHERE title IS NOT NULL;

-- 消息表
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls JSONB,
    tool_name TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,
    reasoning_details JSONB,
    codex_reasoning_items JSONB
);

CREATE INDEX idx_messages_session ON messages(session_id, timestamp);
CREATE INDEX idx_messages_role ON messages(role);

-- PostgreSQL 的 FTS5 等效
CREATE INDEX idx_messages_content_gin ON messages USING gin(to_tsvector('english', content));

-- 审计日志
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- 更新 updated_at 时间戳的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 7.2 SQLAlchemy 模型

```python
# models/session.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime
import uuid

class Session(Base):
    __tablename__ = "sessions"
    
    id: Mapped[str] = Column(String, primary_key=True)
    user_id: Mapped[uuid.UUID] = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = Column(String, default="api")
    model: Mapped[Optional[str]] = Column(String)
    title: Mapped[Optional[str]] = Column(String, index=True)
    started_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = Column(DateTime)
    message_count: Mapped[int] = Column(Integer, default=0)
    tool_call_count: Mapped[int] = Column(Integer, default=0)
    input_tokens: Mapped[int] = Column(Integer, default=0)
    output_tokens: Mapped[int] = Column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = Column(Float, default=0.0)
    
    messages: Mapped[List["Message"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    
    user: Mapped["User"] = relationship(back_populates="sessions")
```

### 7.3 从 SQLite 迁移

```python
# scripts/migrate_sqlite_to_postgres.py
"""
将现有 SQLite 会话迁移到 PostgreSQL。

用法:
    python -m scripts.migrate_sqlite_to_postgres \
        --sqlite-path ~/.hermes/state.db \
        --postgres-url postgresql://user:pass@localhost:5432/hermes
"""

import sqlite3
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def migrate(sqlite_path: str, postgres_url: str):
    # 连接到 SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    # 连接到 PostgreSQL
    engine = create_async_engine(postgres_url)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 迁移会话
        sqlite_cursor = sqlite_conn.execute(
            "SELECT * FROM sessions ORDER BY started_at"
        )
        for row in sqlite_cursor:
            session_dict = dict(row)
            # 转换并插入到 PostgreSQL
            # ... 迁移逻辑 ...
        
        await session.commit()
    
    sqlite_conn.close()
```

***

## 8. 工具配置

### 8.1 移动设备工具集配置

```python
# api/tool_config.py
from typing import Dict, List

# 移动 API 的安全工具配置
MOBILE_SAFE_TOOLSETS = {
    "web": {
        "description": "Web 研究工具",
        "tools": ["web_search", "web_extract"],
        "requires_env": ["FIRECRAWL_API_KEY", "EXA_API_KEY"],
    },
    "file": {
        "description": "文件操作（沙箱）",
        "tools": ["read_file", "write_file", "patch", "search_files"],
        "sandbox_only": True,
    },
    "vision": {
        "description": "图像分析",
        "tools": ["vision_analyze"],
        "requires_env": ["ANTHROPIC_API_KEY"],
    },
    "code_execution": {
        "description": "沙箱代码执行",
        "tools": ["execute_code"],
        "requires_backend": "modal",  # 或 "daytona"
    },
    "planning": {
        "description": "任务规划和内存",
        "tools": ["todo", "memory"],
    },
}

# API 用户的默认工具集
DEFAULT_API_TOOLSET = "hermes-api-server"

# 从 API 排除的工具（安全问题）
EXCLUDED_TOOLS = {
    "terminal",
    "process",
    "browser_navigate",
    "browser_snapshot",
    "browser_click",
    "browser_type",
    "browser_scroll",
    "browser_back",
    "browser_press",
    "browser_get_images",
    "browser_vision",
    "browser_console",
    "send_message",
    "cronjob",
    "ha_list_entities",
    "ha_get_state",
    "ha_list_services",
    "ha_call_service",
    "text_to_speech",
}
```

### 8.2 沙箱代码执行

```python
# api/code_execution_backend.py
"""
配置沙箱代码执行后端。

选项:
1. Modal（推荐用于生产）
2. Daytona（替代托管沙箱）
3. Docker（自托管，更复杂）
"""

from typing import Optional
from modal import Stub, Image, Volume

# Modal 配置
stub = Stub("hermes-code-execution")

sandbox_image = (
    Image.python("3.12")
    .pip_install(
        "requests",
        "httpx",
        "beautifulsoup4",
        "pandas",
        "numpy",
    )
)

@stub.function(
    image=sandbox_image,
    timeout=120,
    memory=1024,
)
def execute_code_modal(code: str, timeout: int = 60) -> dict:
    """在 Modal 沙箱中执行 Python 代码。"""
    import subprocess
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "script.py")
        with open(script_path, "w") as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"代码执行在 {timeout} 秒后超时",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
```

***

## 9. 监控与可观测性

### 9.1 指标 (Prometheus)

```python
# api/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from typing import Dict

# 请求指标
REQUEST_COUNT = Counter(
    "hermes_requests_total",
    "请求总数",
    ["endpoint", "method", "status_code"],
)

REQUEST_DURATION = Histogram(
    "hermes_request_duration_seconds",
    "请求持续时间（秒）",
    ["endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# Token 使用
TOKEN_USAGE = Counter(
    "hermes_tokens_total",
    "使用的 Token 总数",
    ["model", "type"],  # type: prompt, completion, cache_read, cache_write
)

# 成本跟踪
COST_USD = Counter(
    "hermes_cost_usd_total",
    "总成本（美元）",
    ["model", "user_tier"],
)

# 活跃会话
ACTIVE_SESSIONS = Gauge(
    "hermes_active_sessions",
    "活跃会话数",
)

# 工具调用
TOOL_CALLS = Counter(
    "hermes_tool_calls_total",
    "工具调用总数",
    ["tool_name", "success"],
)

# 速率限制命中
RATE_LIMIT_HITS = Counter(
    "hermes_rate_limit_hits_total",
    "速率限制命中总数",
    ["user_tier"],
)
```

### 9.2 结构化日志

```python
# api/logging_config.py
import structlog
from pythonjsonlogger import jsonlogger
import logging

def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """配置结构化日志。"""
    
    if log_format == "json":
        handler = logging.StreamHandler()
        handler.setFormatter(
            jsonlogger.JsonFormatter(
                fmt="%(timestamp)s %(level)s %(event)s %(logger)s %(user_id)s %(session_id)s %(request_id)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
        )
    else:
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s] %(message)s",
            level=log_level,
        )
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if log_format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### 9.3 分布式追踪

```python
# api/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing(service_name: str = "hermes-agent-api"):
    """配置 OpenTelemetry 追踪。"""
    
    provider = TracerProvider()
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint="otel-collector:4317")
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(service_name)
```

### 9.4 告警规则

```yaml
# k8s/alerts.yaml
groups:
- name: hermes-agent-alerts
  rules:
  - alert: 高错误率
    expr: |
      sum(rate(hermes_requests_total{status_code=~"5.."}[5m])) 
      / sum(rate(hermes_requests_total[5m])) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "检测到高错误率"
      description: "错误率为 {{ $value | humanizePercentage }}"
  
  - alert: 高延迟
    expr: |
      histogram_quantile(0.95, 
        sum(rate(hermes_request_duration_seconds_bucket[5m])) by (le)
      ) > 10
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "检测到高延迟"
      description: "P95 延迟为 {{ $value }} 秒"
  
  - alert: Token 使用峰值
    expr: |
      sum(rate(hermes_tokens_total[1h])) > 1000000
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "高 Token 使用量"
      description: "Token 使用量为 {{ $value }} tokens/小时"
  
  - alert: 数据库连接池耗尽
    expr: |
      pg_stat_activity_count / pg_settings_max_connections > 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "数据库连接池几乎耗尽"
```

***

## 10. 扩展策略

### 10.1 水平扩展

```
┌─────────────────────────────────────────────────────────┐
│              Kubernetes HPA 配置                         │
├─────────────────────────────────────────────────────────┤
│ 最小副本数：3                                           │
│ 最大副本数：20                                          │
│                                                         │
│ 扩容条件:                                               │
│ - CPU > 70% 平均                                        │
│ - 内存 > 80% 平均                                       │
│ - 请求队列 > 100                                        │
│                                                         │
│ 缩容条件:                                               │
│ - CPU < 30% 持续 5 分钟                                  │
│ - 内存 < 50% 持续 5 分钟                                 │
│                                                         │
│ 冷却时间:                                               │
│ - 扩容：立即                                            │
│ - 缩容：5 分钟                                          │
└─────────────────────────────────────────────────────────┘
```

### 10.2 缓存策略

```python
# api/caching.py
from redis.asyncio import Redis
from functools import wraps
import json
import hashlib

class CacheManager:
    """
    多层缓存策略。
    
    层:
    1. LRU 缓存 (内存) - 热数据 (< 100MB)
    2. Redis 缓存 - 会话数据、速率限制
    3. 数据库 - 持久存储
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self._local_cache = {}  # LRU 缓存
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """从缓存或数据库获取会话。"""
        # 首先尝试 L1 缓存
        if session_id in self._local_cache:
            return self._local_cache[session_id]
        
        # 尝试 Redis
        cached = await self.redis.get(f"session:{session_id}")
        if cached:
            session = json.loads(cached)
            self._local_cache[session_id] = session
            return session
        
        # 回退到数据库
        # ... 数据库查询 ...
    
    async def cache_tool_result(
        self,
        tool_name: str,
        args_hash: str,
        result: str,
        ttl_seconds: int = 3600,
    ):
        """缓存工具结果以避免重新计算。"""
        key = f"tool_result:{tool_name}:{args_hash}"
        await self.redis.setex(key, ttl_seconds, result)
```

### 10.3 数据库扩展

```
PostgreSQL 扩展策略:

1. 只读副本 (1 万 + 并发用户)
   - 1 个主库（写入）
   - 2-3 个副本（读取）
   - 连接池 (PgBouncer)

2. 分区 (1 亿 + 消息)
   - 按月份分区消息表
   - 自动创建分区

3. 归档 (90+ 天)
   - 将会话移至冷存储 (S3)
   - 热存储保留最后 90 天
```

***

## 11. 实施路线图

### 第 1 阶段：核心 API (第 1-2 周)

**目标:**

- 提取核心 Agent 组件
- 构建 FastAPI 骨架
- 实现认证
- 基础聊天端点

**交付物:**

```
api/
├── main.py              # FastAPI 应用
├── config.py            # 配置
├── auth.py              # JWT 认证
├── schemas/
│   └── chat.py          # 请求/响应模型
├── services/
│   └── agent_service.py # Agent 包装器
└── routers/
    └── chat.py          # 聊天端点
```

**任务:**

1. [ ] 提取 `run_agent.py`, `model_tools.py`, `tools/`, `agent/`
2. [ ] 创建 FastAPI 应用结构
3. [ ] 实现 JWT 认证
4. [ ] 构建 `/api/v1/chat/completions` 端点
5. [ ] 添加基础错误处理
6. [ ] 编写认证 + 聊天的单元测试

### 第 2 阶段：会话管理 (第 3 周)

**目标:**

- PostgreSQL 集成
- 会话 CRUD 操作
- 消息历史

**交付物:**

```
api/
├── models/
│   ├── user.py
│   ├── session.py
│   └── api_key.py
├── database.py          # SQLAlchemy 设置
└── routers/
    └── sessions.py      # 会话端点
```

**任务:**

1. [ ] 设置 PostgreSQL 模式
2. [ ] 实现 SQLAlchemy 模型
3. [ ] 构建会话管理端点
4. [ ] 添加消息历史检索
5. [ ] 实现会话修剪
6. [ ] 编写集成测试

### 第 3 阶段：工具配置 (第 4 周)

**目标:**

- 配置安全工具集
- 设置沙箱代码执行
- 实现工具过滤

**任务:**

1. [ ] 定义移动安全工具集
2. [ ] 配置 Modal/Daytona 后端
3. [ ] 实现工具可用性检查
4. [ ] 按用户层级添加工具过滤
5. [ ] 测试沙箱中的工具执行
6. [ ] 记录工具限制

### 第 4 阶段：速率限制与安全 (第 5 周)

**目标:**

- Redis 速率限制
- 输入验证
- 安全加固

**任务:**

1. [ ] 设置 Redis 用于速率限制
2. [ ] 实现滑动窗口速率限制器
3. [ ] 添加请求大小限制
4. [ ] 配置 CORS
5. [ ] 实现输入清理
6. [ ] 安全审计 + 渗透测试

### 第 5 阶段：可观测性 (第 6 周)

**目标:**

- 结构化日志
- Prometheus 指标
- 分布式追踪

**任务:**

1. [ ] 配置 structlog
2. [ ] 设置 Prometheus 指标
3. [ ] 添加 OpenTelemetry 追踪
4. [ ] 创建 Grafana 仪表板
5. [ ] 配置告警规则
6. [ ] 设置 Sentry 用于错误跟踪

### 第 6 阶段：部署与测试 (第 7-8 周)

**目标:**

- Kubernetes 部署
- 负载测试
- 性能优化

**任务:**

1. [ ] 编写 Dockerfile
2. [ ] 创建 Kubernetes 清单
3. [ ] 设置 CI/CD 管道
4. [ ] 负载测试 (locust)
5. [ ] 性能分析
6. [ ] 文档 + API 规范

### 第 7 阶段：Android 集成 (第 9-10 周)

**目标:**

- Android SDK
- 示例应用
- 文档

**任务:**

1. [ ] 创建 Android SDK (Kotlin)
2. [ ] 构建示例 Android 应用
3. [ ] 编写集成指南
4. [ ] API 文档 (OpenAPI/Swagger)
5. [ ] 与 Android 应用进行 Beta 测试
6. [ ] 根据反馈迭代

***

## 附录 A: API 参考

### OpenAPI 规范

```yaml
openapi: 3.0.0
info:
  title: Hermes Agent API
  version: 1.0.0
  description: 用于 Android 应用集成的生产 API

servers:
  - url: https://api.example.com/v1

paths:
  /chat/completions:
    post:
      summary: 创建聊天补全
      operationId: createChatCompletion
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatCompletionRequest'
      responses:
        '200':
          description: 成功响应
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatCompletionResponse'
        '401':
          description: 未授权
        '429':
          description: 超过速率限制
        '500':
          description: 服务器错误

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  
  schemas:
    ChatCompletionRequest:
      type: object
      properties:
        model:
          type: string
          example: "anthropic/claude-opus-4.6"
        messages:
          type: array
          items:
            $ref: '#/components/schemas/Message'
        stream:
          type: boolean
          default: false
        max_tokens:
          type: integer
          default: 4096
        temperature:
          type: number
          default: 0.7
    
    Message:
      type: object
      properties:
        role:
          type: string
          enum: [system, user, assistant, tool]
        content:
          type: string
        tool_call_id:
          type: string
        tool_calls:
          type: array
          items:
            type: object

security:
  - bearerAuth: []
```

***

## 附录 B: Android SDK 示例

```kotlin
// HermesAgent.kt
class HermesAgent(
    private val apiKey: String,
    private val baseUrl: String = "https://api.example.com/v1"
) {
    private val client = OkHttpClient()
    private val json = Json { ignoreUnknownKeys = true }
    
    suspend fun chat(
        message: String,
        sessionId: String? = null,
        model: String = "claude-opus-4.6"
    ): ChatResponse {
        val request = ChatRequest(
            model = model,
            messages = listOf(Message(role = "user", content = message)),
            sessionId = sessionId
        )
        
        val httpRequest = Request.Builder()
            .url("$baseUrl/chat/completions")
            .post(
                request.toString().toRequestBody(
                    "application/json".toMediaType()
                )
            )
            .addHeader("Authorization", "Bearer $apiKey")
            .build()
        
        return client.newCall(httpRequest).await()
            .use { response ->
                if (!response.isSuccessful) {
                    throw ApiException("请求失败：${response.code}")
                }
                json.decodeFromString(response.body!!.string())
            }
    }
}

// Android 应用中的使用
val agent = HermesAgent(apiKey = "your-api-key")

lifecycleScope.launch {
    try {
        val response = agent.chat("今天天气怎么样？")
        println(response.choices[0].message.content)
    } catch (e: ApiException) {
        // 处理错误
    }
}
```

***

## 附录 C: 成本估算

### 月度运营成本 (1 万日活)

**基础设施:**

- Kubernetes 集群：$330/月
- PostgreSQL (RDS): $60/月
- Redis (ElastiCache): $20/月
- 负载均衡器：$25/月
- **小计**: $435/月

**API 成本** (假设 10 请求/用户/天，500 tokens/请求):

- Anthropic Claude Opus: $15 per 1M tokens
- 每日 tokens: 1 万用户 × 10 请求 × 500 tokens = 5000 万 tokens/天
- 月度 tokens: 5000 万 × 30 = 15 亿 tokens
- **API 成本**: 15 亿 / 100 万 × $15 = $22,500/月

**总月度成本**: \~$23,000

**成本优化策略:**

1. 对简单查询使用更便宜的模型 (Claude Haiku: $0.80/1M)
2. 实现响应缓存
3. 使用提示缓存 (Anthropic)
4. 实现上下文压缩
5. 设置每用户 token 预算

***

## 附录 D: 测试策略

### 测试金字塔

```
        /\
       /  \      E2E 测试 (10%)
      /____\     - 完整对话流程
     /      \    - Android 应用集成
    /        \   
   /__________\  集成测试 (30%)
   |          |  - 数据库操作
   |          |  - 工具执行
   |__________|  - 认证
   
  /____________\ 单元测试 (60%)
  |            | - 模式验证
  |            | - 服务层逻辑
  |____________| - 工具函数
```

### 示例测试

```python
# tests/test_chat_endpoint.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture
def auth_token():
    # 生成测试 JWT token
    return generate_test_token()

def test_chat_completion(auth_token):
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "model": "claude-opus-4.6",
            "messages": [{"role": "user", "content": "你好"}],
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0

def test_rate_limiting():
    # 1 分钟内发送 21 个请求（免费层限制：20）
    for i in range(21):
        response = client.post(...)
    
    assert response.status_code == 429
```

***

## 结论

本规范为将 Hermes Agent 部署为生产 API 服务提供了全面的蓝图。该架构设计考虑了：

- **安全性**: JWT 认证、速率限制、沙箱工具
- **可扩展性**: Kubernetes HPA、只读副本、缓存
- **可观测性**: 指标、日志、追踪
- **成本控制**: Token 预算、模型路由、缓存

**后续步骤:**

1. 审查并批准规范
2. 开始第 1 阶段实施
3. 根据 Android 应用需求迭代
4. 部署到暂存环境
5. 与有限用户进行 Beta 测试
6. 生产发布


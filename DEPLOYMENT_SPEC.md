# Hermes Agent - Production Deployment Specification

## Executive Summary

This document provides a production-ready specification for deploying the Hermes AI Agent as a FastAPI service for Android app consumption. The deployment extracts the core agent functionality from the CLI/messaging platform architecture and exposes it via a secure, scalable REST API.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Extraction](#component-extraction)
3. [FastAPI Service Design](#fastapi-service-design)
4. [Authentication & Security](#authentication--security)
5. [Deployment Architecture](#deployment-architecture)
6. [Configuration Management](#configuration-management)
7. [Database & State Management](#database--state-management)
8. [Tool Configuration](#tool-configuration)
9. [Monitoring & Observability](#monitoring--observability)
10. [Scaling Strategy](#scaling-strategy)
11. [Implementation Roadmap](#implementation-roadmap)

---

## 1. Architecture Overview

### 1.1 Current Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Hermes Agent (Current)                 │
├─────────────────────────────────────────────────────────┤
│  CLI / Gateway (Telegram, Discord, Slack, etc.)        │
│  ├── cli.py (interactive terminal)                      │
│  └── gateway/ (messaging platforms)                     │
│                        ↓                                │
│  run_agent.py (AIAgent class - conversation loop)       │
│  ├── model_tools.py (tool orchestration)               │
│  ├── tools/registry.py (tool registration)             │
│  ├── toolsets.py (toolset definitions)                 │
│  └── hermes_state.py (SQLite session store)            │
│                        ↓                                │
│  External APIs (LLM providers, web, terminal, etc.)    │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Android App                            │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│              Load Balancer (nginx/ALB)                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│          FastAPI Service Cluster (Kubernetes)           │
├─────────────────────────────────────────────────────────┤
│  /api/v1/chat/completions  (OpenAI-compatible API)     │
│  /api/v1/chat/sessions     (Session management)         │
│  /api/v1/chat/history      (Conversation history)       │
│  /api/v1/tools/list        (Available tools)            │
│  /health, /ready, /metrics (Observability)              │
│                                                         │
│  Middleware Stack:                                      │
│  ├── JWT Authentication                                 │
│  ├── Rate Limiting (Redis)                              │
│  ├── Request Validation                                 │
│  ├── CORS Configuration                                 │
│  └── Structured Logging                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│               Supporting Services                       │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL (sessions, users, audit logs)              │
│  Redis (rate limiting, caching, pub/sub)               │
│  S3/MinIO (file storage, trajectories)                 │
│  Prometheus + Grafana (metrics)                        │
│  ELK/Loki (logging)                                     │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Component Extraction

### 2.1 Core Components to Extract

The following components form the minimal viable agent for API deployment:

#### **Essential Core** (MUST include)
```
run_agent.py          # AIAgent class - main conversation loop
model_tools.py        # Tool orchestration layer
tools/registry.py     # Central tool registry
toolsets.py           # Toolset definitions
hermes_state.py       # Session persistence (upgrade to PostgreSQL)
hermes_constants.py   # Path helpers, constants
```

#### **Agent Package** (MUST include)
```
agent/
├── __init__.py
├── memory_manager.py      # Memory context building
├── prompt_builder.py      # System prompt assembly
├── context_compressor.py  # Auto context compression
├── error_classifier.py    # API error classification
├── model_metadata.py      # Token estimation, limits
├── prompt_caching.py      # Anthropic cache control
├── retry_utils.py         # Jittered backoff
├── usage_pricing.py       # Cost estimation
└── display.py             # Tool preview formatting
```

#### **Tool Selection** (Production-safe subset)

**Recommended Toolset for Mobile API:**
```python
# Safe, read-only tools (no terminal access)
SAFE_MOBILE_TOOLS = [
    # Web research
    "web_search", "web_extract",
    # File operations (sandboxed)
    "read_file", "write_file", "patch", "search_files",
    # Vision
    "vision_analyze",
    # Planning & memory
    "todo", "memory",
    # Session history
    "session_search",
    # Code execution (sandboxed only)
    "execute_code",  # with modal/docker backend
    # Delegation
    "delegate_task",
]
```

**Excluded Tools** (Security risk for mobile):
- `terminal` - Direct shell access
- `process` - Process management
- `browser_*` - Heavy resource usage
- `ha_*` - Home Assistant (requires user config)
- `send_message` - Messaging platform tools
- `cronjob` - Scheduled tasks
- `text_to_speech` - Better handled client-side

### 2.2 Dependency Tree

```
hermes-agent-api
├── Core Dependencies
│   ├── openai>=2.21.0,<3
│   ├── anthropic>=0.39.0,<1
│   ├── httpx[socks]>=0.28.1,<1
│   ├── pydantic>=2.12.5,<3
│   └── pyyaml>=6.0.2,<7
│
├── Web Tools
│   ├── exa-py>=2.9.0,<3
│   ├── firecrawl-py>=4.16.0,<5
│   └── parallel-web>=0.4.2,<1
│
├── Code Execution
│   ├── modal>=1.0.0,<2  OR  daytona>=0.148.0,<1
│   └── fal-client>=0.13.1,<1
│
├── FastAPI Stack
│   ├── fastapi>=0.104.0,<1
│   ├── uvicorn[standard]>=0.24.0,<1
│   ├── python-jose[cryptography]  # JWT
│   └── redis>=5.0.0,<6  # Rate limiting
│
└── Observability
    ├── prometheus-client>=0.19.0,<1
    ├── structlog>=24.0.0,<25
    └── sentry-sdk>=2.0.0,<3
```

---

## 3. FastAPI Service Design

### 3.1 API Endpoints

#### **3.1.1 Chat Completions (OpenAI-compatible)**

```python
# POST /api/v1/chat/completions
@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    auth: AuthData = Depends(require_auth),
) -> ChatCompletionResponse:
    """
    OpenAI-compatible chat completions endpoint.
    
    Request:
    {
        "model": "claude-opus-4.6",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "stream": false,
        "max_tokens": 4096,
        "temperature": 0.7,
        "metadata": {
            "session_id": "uuid",
            "user_id": "uuid"
        }
    }
    
    Response:
    {
        "id": "chatcmpl-uuid",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "claude-opus-4.6",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help?"
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

#### **3.1.2 Streaming Support**

```python
# POST /api/v1/chat/completions (stream=true)
@router.post("/chat/completions")
async def create_chat_completion_stream(
    request: ChatCompletionRequest,
    auth: AuthData = Depends(require_auth),
) -> StreamingResponse:
    """
    Server-Sent Events (SSE) streaming for real-time responses.
    
    Yields:
    data: {"id":"chatcmpl-uuid","choices":[{"delta":{"content":"Hello"}}]}
    data: {"id":"chatcmpl-uuid","choices":[{"delta":{"content":"!"}}]}
    data: [DONE]
    """
```

#### **3.1.3 Session Management**

```python
# GET /api/v1/chat/sessions
@router.get("/sessions")
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    auth: AuthData = Depends(require_auth),
) -> ListSessionsResponse:
    """List user's conversation sessions."""

# GET /api/v1/chat/sessions/{session_id}
@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    auth: AuthData = Depends(require_auth),
) -> SessionDetail:
    """Get session details with message history."""

# DELETE /api/v1/chat/sessions/{session_id}
@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    auth: AuthData = Depends(require_auth),
) -> dict:
    """Delete a session and all its messages."""

# POST /api/v1/chat/sessions/{session_id}/title
@router.post("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str,
    auth: AuthData = Depends(require_auth),
) -> dict:
    """Update session title."""
```

#### **3.1.4 Tool Management**

```python
# GET /api/v1/tools/list
@router.get("/tools/list")
async def list_available_tools(
    auth: AuthData = Depends(require_auth),
) -> ToolsListResponse:
    """
    List all available tools for the authenticated user.
    
    Response:
    {
        "tools": [
            {
                "name": "web_search",
                "description": "Search the web",
                "toolset": "web",
                "available": true
            },
            ...
        ]
    }
    """
```

#### **3.1.5 Health & Metrics**

```python
# GET /health
@router.get("/health")
async def health_check() -> dict:
    """Basic health check."""

# GET /ready
@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """Kubernetes readiness probe - checks DB, Redis, LLM connectivity."""

# GET /metrics
@router.get("/metrics")
async def metrics() -> str:
    """Prometheus metrics endpoint."""
```

### 3.2 Request/Response Models

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
    reasoning: Optional[str] = None  # For models with reasoning

class ChatCompletionRequest(BaseModel):
    model: str = "anthropic/claude-opus-4.6"
    messages: List[Message]
    stream: bool = False
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    
    # Session management
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Tool configuration
    enabled_toolsets: Optional[List[str]] = None
    disabled_tools: Optional[List[str]] = None
    
    # Budget control
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

### 3.3 Service Layer

```python
# services/agent_service.py
from typing import AsyncGenerator, Dict, Any, Optional
from run_agent import AIAgent
from model_tools import get_tool_definitions, handle_function_call
from hermes_state import SessionDB
from tools.registry import registry

class AgentService:
    """
    Core agent service wrapping AIAgent for API consumption.
    
    Handles:
    - Session management
    - Tool execution
    - Token tracking
    - Cost estimation
    - Streaming responses
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
        Execute a single chat turn.
        
        1. Create/load session
        2. Initialize AIAgent with tool definitions
        3. Run conversation loop
        4. Save messages to session
        5. Return response with usage stats
        """
        
    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        session_id: str,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response using Server-Sent Events.
        
        Yields JSON chunks as they become available.
        """
```

---

## 4. Authentication & Security

### 4.1 Authentication Strategy

**JWT-based Authentication** with API Key fallback:

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
    Validate JWT token from Authorization header.
    
    Token format: Bearer <jwt_token>
    
    Claims:
    - sub: user_id
    - api_key_id: identifier of the API key used
    - permissions: list of allowed operations
    - rate_limit_tier: rate limiting tier
    - exp: expiration timestamp
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
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 4.2 API Key Management

```python
# models/api_key.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import secrets

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: f"key_{secrets.token_urlsafe(24)}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # User-provided name (e.g., "Android App")
    key_hash = Column(String, nullable=False)  # Hashed key (bcrypt)
    key_prefix = Column(String, nullable=False)  # First 8 chars for identification
    permissions = Column(JSON, default=["chat:create", "sessions:read"])
    rate_limit_tier = Column(String, default="free")
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    @classmethod
    def create(cls, user_id: str, name: str, permissions: List[str] = None) -> "APIKey":
        """Generate a new API key."""
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
        """Verify the raw key against the hash."""
        return bcrypt.checkpw(raw_key.encode(), self.key_hash.encode())
```

### 4.3 Rate Limiting

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
    Rate limiting using Redis sliding window.
    
    Keys:
    - rate_limit:{user_id}:requests  (sorted set, score=timestamp)
    - rate_limit:{user_id}:tokens    (counter, reset daily)
    """
    limits = RATE_LIMITS.get(auth.rate_limit_tier, RATE_LIMITS["free"])
    
    # Check requests per minute
    now = time.time()
    window_start = now - 60
    
    key = f"rate_limit:{auth.user_id}:requests"
    redis.zremrangebyscore(key, 0, window_start)
    count = await redis.zcard(key)
    
    if count >= limits["requests_per_minute"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again in 1 minute.",
            headers={"X-RateLimit-Reset": str(int(window_start + 60))},
        )
    
    # Check tokens per day
    token_key = f"rate_limit:{auth.user_id}:tokens"
    tokens_used = await redis.get(token_key) or 0
    
    # Increment request count
    redis.zadd(key, {str(uuid.uuid4()): now})
    redis.expire(key, 120)  # 2 minute TTL
    
    response = await call_next(request)
    
    # Update token count from response
    if hasattr(response, "body"):
        # Parse usage from response body
        pass
    
    return response
```

### 4.4 Security Checklist

- [ ] **Input Validation**: All user inputs validated with Pydantic
- [ ] **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- [ ] **XSS Prevention**: HTML sanitization on all text outputs
- [ ] **CORS Configuration**: Strict origin whitelist for Android app
- [ ] **HTTPS Only**: TLS 1.3 enforced
- [ ] **API Key Hashing**: bcrypt with salt
- [ ] **JWT Expiration**: Short-lived tokens (15 min) with refresh tokens
- [ ] **Request Size Limits**: Max 10MB per request
- [ ] **Timeout Enforcement**: Max 120s per request
- [ ] **Audit Logging**: All API calls logged with user ID, timestamp, action

---

## 5. Deployment Architecture

### 5.1 Kubernetes Deployment

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

### 5.2 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Security: non-root user
RUN useradd --create-home --shell /bin/bash hermes
USER hermes

WORKDIR /app

# Install dependencies
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application
COPY --chown=hermes:hermes . .

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run with uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

```yaml
# docker-compose.yml (for local development)
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

### 5.3 Infrastructure Requirements

**Production (10k DAU target):**
- **Kubernetes Cluster**: 3-5 nodes (4 CPU, 16GB RAM each)
- **PostgreSQL**: Managed (AWS RDS / GCP Cloud SQL) - 2 vCPU, 8GB RAM
- **Redis**: Managed (ElastiCache / Memorystore) - 1GB cache
- **Load Balancer**: AWS ALB / GCP Load Balancing
- **Object Storage**: S3 / GCS for file storage
- **CDN**: CloudFlare / CloudFront for static assets

**Estimated Monthly Cost (AWS):**
- EKS Cluster: $73.50
- 3x m5.xlarge nodes: ~$150
- RDS PostgreSQL (db.t3.medium): ~$60
- ElastiCache Redis (cache.t3.small): ~$20
- ALB: ~$25
- **Total**: ~$330/month (excluding API costs)

---

## 6. Configuration Management

### 6.1 Environment Variables

```bash
# .env.example

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/hermes

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_DAYS=30

# LLM Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...

# Tool Configuration
FIRECRAWL_API_KEY=fc-...
EXA_API_KEY=exa-...

# Security
CORS_ORIGINS=https://your-android-app.com
ALLOWED_HOSTS=api.example.com

# Rate Limiting
RATE_LIMIT_REDIS_URL=redis://localhost:6379/1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=https://...@sentry.io/...

# Feature Flags
ENABLED_TOOLSETS=hermes-api-server
DISABLED_TOOLSETS=messaging,homeassistant
MAX_ITERATIONS_DEFAULT=50
MAX_COST_PER_REQUEST_USD=0.10

# Session Management
SESSION_MAX_AGE_DAYS=90
SESSION_PRUNE_INTERVAL_HOURS=24
```

### 6.2 Settings Module

```python
# api/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # Database
    database_url: str
    redis_url: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15
    
    # LLM Providers
    anthropic_api_key: str
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # Tools
    firecrawl_api_key: Optional[str] = None
    exa_api_key: Optional[str] = None
    
    # Security
    cors_origins: List[str] = ["*"]
    allowed_hosts: List[str] = ["*"]
    
    # Rate Limiting
    rate_limit_redis_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    sentry_dsn: Optional[str] = None
    
    # Feature Flags
    enabled_toolsets: List[str] = ["hermes-api-server"]
    disabled_toolsets: List[str] = []
    max_iterations_default: int = 50
    max_cost_per_request_usd: float = 0.10
    
    # Session Management
    session_max_age_days: int = 90
    session_prune_interval_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 7. Database & State Management

### 7.1 PostgreSQL Schema

```sql
-- migrations/001_initial_schema.sql

-- Users table
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

-- Sessions (upgraded from SQLite)
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

-- Messages
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

-- FTS5 equivalent for PostgreSQL
CREATE INDEX idx_messages_content_gin ON messages USING gin(to_tsvector('english', content));

-- Audit Logs
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

-- Function to update updated_at timestamp
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

### 7.2 SQLAlchemy Models

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

### 7.3 Migration from SQLite

```python
# scripts/migrate_sqlite_to_postgres.py
"""
Migrate existing SQLite sessions to PostgreSQL.

Usage:
    python -m scripts.migrate_sqlite_to_postgres \
        --sqlite-path ~/.hermes/state.db \
        --postgres-url postgresql://user:pass@localhost:5432/hermes
"""

import sqlite3
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def migrate(sqlite_path: str, postgres_url: str):
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Connect to PostgreSQL
    engine = create_async_engine(postgres_url)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Migrate sessions
        sqlite_cursor = sqlite_conn.execute(
            "SELECT * FROM sessions ORDER BY started_at"
        )
        for row in sqlite_cursor:
            session_dict = dict(row)
            # Transform and insert into PostgreSQL
            # ... migration logic ...
        
        await session.commit()
    
    sqlite_conn.close()
```

---

## 8. Tool Configuration

### 8.1 Toolset Configuration for Mobile

```python
# api/tool_config.py
from typing import Dict, List

# Safe tool configuration for mobile API
MOBILE_SAFE_TOOLSETS = {
    "web": {
        "description": "Web research tools",
        "tools": ["web_search", "web_extract"],
        "requires_env": ["FIRECRAWL_API_KEY", "EXA_API_KEY"],
    },
    "file": {
        "description": "File operations (sandboxed)",
        "tools": ["read_file", "write_file", "patch", "search_files"],
        "sandbox_only": True,
    },
    "vision": {
        "description": "Image analysis",
        "tools": ["vision_analyze"],
        "requires_env": ["ANTHROPIC_API_KEY"],
    },
    "code_execution": {
        "description": "Sandboxed code execution",
        "tools": ["execute_code"],
        "requires_backend": "modal",  # or "daytona"
    },
    "planning": {
        "description": "Task planning and memory",
        "tools": ["todo", "memory"],
    },
}

# Default toolset for API users
DEFAULT_API_TOOLSET = "hermes-api-server"

# Tools excluded from API (security concerns)
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

### 8.2 Sandboxed Code Execution

```python
# api/code_execution_backend.py
"""
Configure sandboxed code execution backend.

Options:
1. Modal (recommended for production)
2. Daytona (alternative managed sandbox)
3. Docker (self-hosted, more complex)
"""

from typing import Optional
from modal import Stub, Image, Volume

# Modal configuration
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
    """Execute Python code in a Modal sandbox."""
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
                "error": f"Code execution timed out after {timeout}s",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
```

---

## 9. Monitoring & Observability

### 9.1 Metrics (Prometheus)

```python
# api/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from typing import Dict

# Request metrics
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

# Token usage
TOKEN_USAGE = Counter(
    "hermes_tokens_total",
    "Total tokens used",
    ["model", "type"],  # type: prompt, completion, cache_read, cache_write
)

# Cost tracking
COST_USD = Counter(
    "hermes_cost_usd_total",
    "Total cost in USD",
    ["model", "user_tier"],
)

# Active sessions
ACTIVE_SESSIONS = Gauge(
    "hermes_active_sessions",
    "Number of active sessions",
)

# Tool usage
TOOL_CALLS = Counter(
    "hermes_tool_calls_total",
    "Total tool calls",
    ["tool_name", "success"],
)

# Rate limiting
RATE_LIMIT_HITS = Counter(
    "hermes_rate_limit_hits_total",
    "Number of rate limit hits",
    ["user_tier"],
)
```

### 9.2 Structured Logging

```python
# api/logging_config.py
import structlog
from pythonjsonlogger import jsonlogger
import logging

def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """Configure structured logging."""
    
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

### 9.3 Distributed Tracing

```python
# api/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing(service_name: str = "hermes-agent-api"):
    """Configure OpenTelemetry tracing."""
    
    provider = TracerProvider()
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint="otel-collector:4317")
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(service_name)
```

### 9.4 Alerting Rules

```yaml
# k8s/alerts.yaml
groups:
- name: hermes-agent-alerts
  rules:
  - alert: HighErrorRate
    expr: |
      sum(rate(hermes_requests_total{status_code=~"5.."}[5m])) 
      / sum(rate(hermes_requests_total[5m])) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }}"
  
  - alert: HighLatency
    expr: |
      histogram_quantile(0.95, 
        sum(rate(hermes_request_duration_seconds_bucket[5m])) by (le)
      ) > 10
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High latency detected"
      description: "P95 latency is {{ $value }}s"
  
  - alert: TokenUsageSpike
    expr: |
      sum(rate(hermes_tokens_total[1h])) > 1000000
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "High token usage"
      description: "Token usage is {{ $value }} tokens/hour"
  
  - alert: DatabaseConnectionPoolExhausted
    expr: |
      pg_stat_activity_count / pg_settings_max_connections > 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Database connection pool nearly exhausted"
```

---

## 10. Scaling Strategy

### 10.1 Horizontal Scaling

```
┌─────────────────────────────────────────────────────────┐
│              Kubernetes HPA Configuration               │
├─────────────────────────────────────────────────────────┤
│ Min Replicas: 3                                         │
│ Max Replicas: 20                                        │
│                                                         │
│ Scale Up When:                                          │
│ - CPU > 70% average                                     │
│ - Memory > 80% average                                  │
│ - Request queue > 100                                   │
│                                                         │
│ Scale Down When:                                        │
│ - CPU < 30% for 5 minutes                               │
│ - Memory < 50% for 5 minutes                            │
│                                                         │
│ Cooldown:                                               │
│ - Scale up: immediate                                   │
│ - Scale down: 5 minutes                                 │
└─────────────────────────────────────────────────────────┘
```

### 10.2 Caching Strategy

```python
# api/caching.py
from redis.asyncio import Redis
from functools import wraps
import json
import hashlib

class CacheManager:
    """
    Multi-layer caching strategy.
    
    Layers:
    1. LRU Cache (in-memory) - Hot data (< 100MB)
    2. Redis Cache - Session data, rate limits
    3. Database - Persistent storage
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self._local_cache = {}  # LRU cache
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session from cache or database."""
        # Try L1 cache first
        if session_id in self._local_cache:
            return self._local_cache[session_id]
        
        # Try Redis
        cached = await self.redis.get(f"session:{session_id}")
        if cached:
            session = json.loads(cached)
            self._local_cache[session_id] = session
            return session
        
        # Fall back to database
        # ... database query ...
    
    async def cache_tool_result(
        self,
        tool_name: str,
        args_hash: str,
        result: str,
        ttl_seconds: int = 3600,
    ):
        """Cache tool result to avoid recomputation."""
        key = f"tool_result:{tool_name}:{args_hash}"
        await self.redis.setex(key, ttl_seconds, result)
```

### 10.3 Database Scaling

```
PostgreSQL Scaling Strategy:

1. Read Replicas (10k+ concurrent users)
   - 1 primary (writes)
   - 2-3 replicas (reads)
   - Connection pooling (PgBouncer)

2. Partitioning (100M+ messages)
   - Partition messages table by month
   - Automatic partition creation

3. Archival (90+ days)
   - Move old sessions to cold storage (S3)
   - Keep last 90 days in hot storage
```

---

## 11. Implementation Roadmap

### Phase 1: Core API (Week 1-2)

**Goals:**
- Extract core agent components
- Build FastAPI skeleton
- Implement authentication
- Basic chat endpoint

**Deliverables:**
```
api/
├── main.py              # FastAPI app
├── config.py            # Settings
├── auth.py              # JWT auth
├── schemas/
│   └── chat.py          # Request/response models
├── services/
│   └── agent_service.py # Agent wrapper
└── routers/
    └── chat.py          # Chat endpoints
```

**Tasks:**
1. [ ] Extract `run_agent.py`, `model_tools.py`, `tools/`, `agent/`
2. [ ] Create FastAPI app structure
3. [ ] Implement JWT authentication
4. [ ] Build `/api/v1/chat/completions` endpoint
5. [ ] Add basic error handling
6. [ ] Write unit tests for auth + chat

### Phase 2: Session Management (Week 3)

**Goals:**
- PostgreSQL integration
- Session CRUD operations
- Message history

**Deliverables:**
```
api/
├── models/
│   ├── user.py
│   ├── session.py
│   └── api_key.py
├── database.py          # SQLAlchemy setup
└── routers/
    └── sessions.py      # Session endpoints
```

**Tasks:**
1. [ ] Set up PostgreSQL schema
2. [ ] Implement SQLAlchemy models
3. [ ] Build session management endpoints
4. [ ] Add message history retrieval
5. [ ] Implement session pruning
6. [ ] Write integration tests

### Phase 3: Tool Configuration (Week 4)

**Goals:**
- Configure safe toolsets
- Set up sandboxed code execution
- Implement tool filtering

**Tasks:**
1. [ ] Define mobile-safe toolsets
2. [ ] Configure Modal/Daytona backend
3. [ ] Implement tool availability checks
4. [ ] Add tool filtering by user tier
5. [ ] Test tool execution in sandbox
6. [ ] Document tool limitations

### Phase 4: Rate Limiting & Security (Week 5)

**Goals:**
- Redis rate limiting
- Input validation
- Security hardening

**Tasks:**
1. [ ] Set up Redis for rate limiting
2. [ ] Implement sliding window rate limiter
3. [ ] Add request size limits
4. [ ] Configure CORS
5. [ ] Implement input sanitization
6. [ ] Security audit + penetration testing

### Phase 5: Observability (Week 6)

**Goals:**
- Structured logging
- Prometheus metrics
- Distributed tracing

**Tasks:**
1. [ ] Configure structlog
2. [ ] Set up Prometheus metrics
3. [ ] Add OpenTelemetry tracing
4. [ ] Create Grafana dashboards
5. [ ] Configure alerting rules
6. [ ] Set up Sentry for error tracking

### Phase 6: Deployment & Testing (Week 7-8)

**Goals:**
- Kubernetes deployment
- Load testing
- Performance optimization

**Tasks:**
1. [ ] Write Dockerfile
2. [ ] Create Kubernetes manifests
3. [ ] Set up CI/CD pipeline
4. [ ] Load testing (locust)
5. [ ] Performance profiling
6. [ ] Documentation + API specs

### Phase 7: Android Integration (Week 9-10)

**Goals:**
- Android SDK
- Sample app
- Documentation

**Tasks:**
1. [ ] Create Android SDK (Kotlin)
2. [ ] Build sample Android app
3. [ ] Write integration guide
4. [ ] API documentation (OpenAPI/Swagger)
5. [ ] Beta testing with Android app
6. [ ] Iterate based on feedback

---

## Appendix A: API Reference

### OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: Hermes Agent API
  version: 1.0.0
  description: Production API for Android app integration

servers:
  - url: https://api.example.com/v1

paths:
  /chat/completions:
    post:
      summary: Create chat completion
      operationId: createChatCompletion
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatCompletionRequest'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatCompletionResponse'
        '401':
          description: Unauthorized
        '429':
          description: Rate limit exceeded
        '500':
          description: Server error

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

---

## Appendix B: Android SDK Example

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
                    throw ApiException("Request failed: ${response.code}")
                }
                json.decodeFromString(response.body!!.string())
            }
    }
}

// Usage in Android App
val agent = HermesAgent(apiKey = "your-api-key")

lifecycleScope.launch {
    try {
        val response = agent.chat("What's the weather today?")
        println(response.choices[0].message.content)
    } catch (e: ApiException) {
        // Handle error
    }
}
```

---

## Appendix C: Cost Estimation

### Monthly Operating Costs (10k DAU)

**Infrastructure:**
- Kubernetes cluster: $330/month
- PostgreSQL (RDS): $60/month
- Redis (ElastiCache): $20/month
- Load balancer: $25/month
- **Subtotal**: $435/month

**API Costs** (assuming 10 requests/user/day, 500 tokens/request):
- Anthropic Claude Opus: $15 per 1M tokens
- Daily tokens: 10k users × 10 requests × 500 tokens = 50M tokens/day
- Monthly tokens: 50M × 30 = 1.5B tokens
- **API Cost**: 1.5B / 1M × $15 = $22,500/month

**Total Monthly Cost**: ~$23,000

**Cost Optimization Strategies:**
1. Use cheaper models for simple queries (Claude Haiku: $0.80/1M)
2. Implement response caching
3. Use prompt caching (Anthropic)
4. Implement context compression
5. Set per-user token budgets

---

## Appendix D: Testing Strategy

### Test Pyramid

```
        /\
       /  \      E2E Tests (10%)
      /____\     - Full conversation flows
     /      \    - Android app integration
    /        \   
   /__________\  Integration Tests (30%)
   |          |  - Database operations
   |          |  - Tool execution
   |__________|  - Authentication
   
  /____________\ Unit Tests (60%)
  |            | - Schema validation
  |            | - Service layer logic
  |____________| - Utility functions
```

### Example Tests

```python
# tests/test_chat_endpoint.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture
def auth_token():
    # Generate test JWT token
    return generate_test_token()

def test_chat_completion(auth_token):
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "model": "claude-opus-4.6",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0

def test_rate_limiting():
    # Send 21 requests in 1 minute (free tier limit: 20)
    for i in range(21):
        response = client.post(...)
    
    assert response.status_code == 429
```

---

## Conclusion

This specification provides a comprehensive blueprint for deploying Hermes Agent as a production API service. The architecture is designed for:

- **Security**: JWT auth, rate limiting, sandboxed tools
- **Scalability**: Kubernetes HPA, read replicas, caching
- **Observability**: Metrics, logging, tracing
- **Cost Control**: Token budgets, model routing, caching

**Next Steps:**
1. Review and approve specification
2. Begin Phase 1 implementation
3. Iterate based on Android app requirements
4. Deploy to staging environment
5. Beta test with limited users
6. Production rollout

# API 认证与安全配置指南

> **认证与安全** 是保护 API 服务的第一道防线，确保只有授权用户能够访问服务。

---

## 📋 目录

- [配置项详解](#配置项详解)
- [API Key 认证](#api-key-认证)
- [JWT Token 认证](#jwt-token-认证)
- [双重认证机制](#双重认证机制)
- [安全最佳实践](#安全最佳实践)
- [攻击防护](#攻击防护)
- [审计与监控](#审计与监控)
- [故障排查](#故障排查)

---

## 配置项详解

### 1. `api_keys: List[str] = []`

**作用：** 允许的 API Key 列表

```python
# 单个 API Key
api_keys = ["sk-xxxxxxxxxxxxxxxx"]

# 多个 API Key（多用户场景）
api_keys = [
    "sk-user1-xxxxxxxx",
    "sk-user2-xxxxxxxx",
    "sk-user3-xxxxxxxx",
]

# 空列表表示开发模式（不验证）
api_keys = []
```

**API Key 格式建议：**
```python
# 推荐格式：前缀 + 随机字符串
sk_xxxxxxxxxxxxxxxxxxxxxxxx  # sk = Service Key
pk_xxxxxxxxxxxxxxxxxxxxxxxx  # pk = Public Key
ak_xxxxxxxxxxxxxxxxxxxxxxxx  # ak = Access Key

# 生成示例
import secrets
api_key = f"sk_{secrets.token_urlsafe(32)}"
# 结果：sk_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890
```

---

### 2. `api_key_header: str = "X-API-Key"`

**作用：** API Key 在请求头中的字段名

```python
# 标准命名
api_key_header = "X-API-Key"

# 其他常见命名
api_key_header = "Authorization"  # 配合 Bearer 方案
api_key_header = "Api-Key"
api_key_header = "X-Api-Key"
```

**客户端使用示例：**
```bash
# curl 请求
curl -H "X-API-Key: sk-xxxxxxxx" http://localhost:8000/api/v1/health

# Python requests
import requests
headers = {"X-API-Key": "sk-xxxxxxxx"}
response = requests.get("http://localhost:8000/api/v1/health", headers=headers)
```

---

### 3. `jwt_secret_key: Optional[str] = None`

**作用：** JWT Token 的签名密钥

```python
# 开发环境（不推荐）
jwt_secret_key = "my-secret-key"

# 生产环境（推荐使用环境变量）
jwt_secret_key = os.getenv("JWT_SECRET_KEY")

# 生成强密钥
import secrets
jwt_secret_key = secrets.token_urlsafe(32)
# 结果：aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890-_aBcDeFgHiJk
```

**密钥强度要求：**
- ✅ 最少 32 个字符
- ✅ 包含大小写字母、数字、特殊字符
- ✅ 定期轮换（每 3-6 个月）
- ❌ 不要使用：`"secret"`, `"password"`, `"123456"`

---

### 4. `jwt_algorithm: str = "HS256"`

**作用：** JWT 签名算法

```python
# 推荐算法
jwt_algorithm = "HS256"  # HMAC-SHA256

# 其他算法
jwt_algorithm = "HS384"  # HMAC-SHA384（更安全）
jwt_algorithm = "HS512"  # HMAC-SHA512（最安全）
jwt_algorithm = "RS256"  # RSA-SHA256（非对称加密）
```

**算法对比：**

| 算法 | 类型 | 密钥 | 性能 | 安全性 | 适用场景 |
|------|------|------|------|--------|---------|
| HS256 | 对称 | 共享密钥 | 快 | 高 | 单服务 |
| HS512 | 对称 | 共享密钥 | 中 | 很高 | 高安全场景 |
| RS256 | 非对称 | 公钥/私钥 | 慢 | 最高 | 多服务/跨域 |

---

### 5. `jwt_expiration_minutes: int = 15`

**作用：** JWT Token 的过期时间（分钟）

```python
# 短期 Token（推荐）
jwt_expiration_minutes = 15  # 15 分钟

# 中期 Token
jwt_expiration_minutes = 60  # 1 小时

# 长期 Token（不推荐）
jwt_expiration_minutes = 1440  # 24 小时
```

**Token 生命周期：**

```
用户登录 → 获取 Access Token (15 分钟)
           ↓
       访问 API (携带 Token)
           ↓
   Token 即将过期 (< 5 分钟)
           ↓
   使用 Refresh Token 续期
           ↓
   获取新的 Access Token
```

---

## API Key 认证

### 工作原理

```
┌─────────┐              ┌──────────────┐              ┌─────────┐
│  客户端  │ ──请求 + Key──→│ API 网关/中间件 │ ──验证 Key──→│  服务   │
└─────────┘              └──────────────┘              └─────────┘
                              ↓
                        验证失败
                              ↓
                        401 Unauthorized
```

### 实现代码

```python
# middleware/auth.py

class APIKeyMiddleware:
    async def dispatch(self, request: Request, call_next):
        # 1. 提取 API Key
        api_key = request.headers.get("X-API-Key")
        
        # 2. 验证 API Key
        if not api_key or api_key not in settings.api_keys:
            raise HTTPException(
                status_code=401,
                detail="无效的 API Key",
            )
        
        # 3. 记录用户信息
        request.state.api_key = api_key
        
        # 4. 继续处理请求
        return await call_next(request)
```

### 使用示例

```bash
# 成功请求
$ curl -H "X-API-Key: sk-abc123" http://localhost:8000/api/v1/health
{
  "status": "healthy",
  "version": "1.0.0"
}

# 失败请求（无 Key）
$ curl http://localhost:8000/api/v1/health
{
  "error": "未提供认证凭据",
  "request_id": "req_abc123"
}

# 失败请求（错误 Key）
$ curl -H "X-API-Key: wrong-key" http://localhost:8000/api/v1/health
{
  "error": "无效的 API Key",
  "request_id": "req_def456"
}
```

---

## JWT Token 认证

### 工作原理

```
┌─────────┐
│  客户端  │
└────┬────┘
     │ 1. 登录（用户名 + 密码）
     ↓
┌─────────────┐
│ 认证服务     │ 2. 验证凭据
└─────┬───────┘ 3. 生成 JWT Token
      │         (Header.Payload.Signature)
      ↓
┌─────────┐
│  客户端  │ 4. 存储 Token
└────┬────┘
     │ 5. 访问 API（携带 Token）
     ↓
┌──────────────┐
│ API 中间件     │ 6. 验证签名和过期时间
└─────┬────────┘ 7. 提取用户信息
      │
      ↓
┌─────────┐
│  服务    │ 8. 处理请求
└─────────┘
```

### JWT 结构

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6MTYzNDU2Nzg5MH0.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

↑                        ↑                          ↑
Header (算法 + 类型)       Payload (数据)              Signature (签名)
```

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "user_123",           // 用户 ID
  "api_key_id": "key_abc",     // API Key ID
  "permissions": ["chat:create"],
  "rate_limit_tier": "pro",    // 速率限制等级
  "exp": 1634567890,           // 过期时间
  "iat": 1634566990            // 签发时间
}
```

**Signature:**
```python
# 签名算法
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  jwt_secret_key
)
```

### 实现代码

```python
# middleware/auth.py

from jose import jwt
from datetime import datetime, timedelta

class JWTMiddleware:
    async def dispatch(self, request: Request, call_next):
        # 1. 提取 Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(401, "缺少 Bearer Token")
        
        token = auth_header.split(" ")[1]
        
        # 2. 验证 Token
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            
            # 3. 检查过期时间
            exp = payload.get("exp")
            if exp and exp < datetime.now().timestamp():
                raise HTTPException(401, "Token 已过期")
            
            # 4. 提取用户信息
            request.state.user_id = payload["sub"]
            request.state.permissions = payload.get("permissions", [])
            
        except JWTError as e:
            raise HTTPException(401, f"Token 无效：{str(e)}")
        
        return await call_next(request)
```

### 生成 Token

```python
# auth.py

from jose import jwt
from datetime import datetime, timedelta

def create_access_token(
    user_id: str,
    permissions: list = None,
    expires_delta: timedelta = None
) -> str:
    """生成 Access Token"""
    
    now = datetime.now()
    expire = now + (expires_delta or timedelta(minutes=15))
    
    payload = {
        "sub": user_id,
        "exp": expire.timestamp(),
        "iat": now.timestamp(),
        "permissions": permissions or [],
        "rate_limit_tier": "free",
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    return token

# 使用示例
token = create_access_token(
    user_id="user_123",
    permissions=["chat:create", "sessions:read"],
    expires_delta=timedelta(minutes=15),
)
```

### 刷新 Token

```python
def create_refresh_token(user_id: str) -> str:
    """生成 Refresh Token（长期有效）"""
    
    now = datetime.now()
    expire = now + timedelta(days=30)  # 30 天
    
    payload = {
        "sub": user_id,
        "exp": expire.timestamp(),
        "iat": now.timestamp(),
        "type": "refresh",
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

# 刷新 Access Token
def refresh_access_token(refresh_token: str) -> str:
    """使用 Refresh Token 获取新的 Access Token"""
    
    # 1. 验证 Refresh Token
    payload = jwt.decode(
        refresh_token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    
    # 2. 检查类型
    if payload.get("type") != "refresh":
        raise ValueError("无效的 Refresh Token")
    
    # 3. 生成新的 Access Token
    return create_access_token(payload["sub"])
```

---

## 双重认证机制

### 为什么需要双重认证？

**单一认证的局限：**

| 认证方式 | 优点 | 缺点 | 适用场景 |
|---------|------|------|---------|
| **API Key** | 简单、持久 | 易泄露、难撤销 | 服务端对服务端 |
| **JWT** | 安全、可携带用户信息 | 需要定期刷新 | 客户端对服务端 |

**双重认证的优势：**
- ✅ API Key 标识应用/客户端
- ✅ JWT 标识具体用户
- ✅ 双重保护，更安全
- ✅ 灵活的权限控制

### 实现方案

```python
# middleware/auth.py

class DualAuthMiddleware:
    async def dispatch(self, request: Request, call_next):
        # 1. 验证 API Key（应用级认证）
        api_key = request.headers.get("X-API-Key")
        if api_key:
            app_info = await self.verify_api_key(api_key)
            request.state.app_id = app_info["app_id"]
            request.state.app_permissions = app_info["permissions"]
        
        # 2. 验证 JWT Token（用户级认证）
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user_info = await self.verify_jwt(token)
            request.state.user_id = user_info["user_id"]
            request.state.user_permissions = user_info["permissions"]
        
        # 3. 权限检查
        if not self.has_permission(request):
            raise HTTPException(403, "权限不足")
        
        return await call_next(request)
    
    def has_permission(self, request: Request) -> bool:
        """检查是否有权限访问当前端点"""
        required = get_required_permission(request)
        
        # 用户权限优先
        if hasattr(request.state, "user_permissions"):
            return required in request.state.user_permissions
        
        # 降级到应用权限
        if hasattr(request.state, "app_permissions"):
            return required in request.state.app_permissions
        
        return False
```

### 使用场景

```
场景 1: 企业内部系统
- API Key: 标识企业
- JWT: 标识企业员工
- 权限：企业权限 + 员工角色权限

场景 2: SaaS 平台
- API Key: 标识租户（公司）
- JWT: 标识租户的用户
- 权限：租户套餐权限 + 用户角色权限

场景 3: 开放平台
- API Key: 标识第三方应用
- JWT: 标识应用的用户
- 权限：应用权限 + 用户授权范围
```

---

## 安全最佳实践

### ✅ 1. API Key 管理

#### 生成安全的 Key

```python
import secrets
import hashlib

def generate_api_key(user_id: str) -> dict:
    """生成 API Key"""
    
    # 生成随机字符串
    raw_key = f"sk_{secrets.token_urlsafe(32)}"
    
    # 哈希存储（用于验证）
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    # Key 前缀（用于识别）
    key_prefix = raw_key[:8]
    
    return {
        "raw_key": raw_key,      # 只展示一次给用户
        "key_hash": key_hash,    # 存储到数据库
        "key_prefix": key_prefix, # 用于日志和识别
    }

# 使用示例
result = generate_api_key("user_123")
print(f"API Key: {result['raw_key']}")
# 输出：API Key: sk_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
```

#### 安全存储

```python
# ❌ 错误：明文存储
api_keys = ["sk-abc123", "sk-def456"]

# ✅ 正确：哈希存储
import bcrypt

def hash_api_key(raw_key: str) -> str:
    """哈希 API Key"""
    return bcrypt.hashpw(
        raw_key.encode(),
        bcrypt.gensalt(rounds=12)
    ).decode()

def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """验证 API Key"""
    return bcrypt.checkpw(
        raw_key.encode(),
        stored_hash.encode()
    )
```

#### 定期轮换

```python
# 数据库表结构
CREATE TABLE api_keys (
    id VARCHAR(64) PRIMARY KEY,
    user_id UUID NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- 过期时间
    last_used_at TIMESTAMP,
    rotated_from_id VARCHAR(64)  -- 轮换来源
);

# 轮换逻辑
def rotate_api_key(old_key_id: str) -> str:
    """轮换 API Key"""
    
    # 1. 生成新 Key
    new_key = generate_api_key(user_id)
    
    # 2. 标记旧 Key 为即将过期
    db.execute(
        "UPDATE api_keys SET expires_at = NOW() + INTERVAL '7 days' WHERE id = %s",
        (old_key_id,)
    )
    
    # 3. 记录轮换关系
    db.execute(
        "UPDATE api_keys SET rotated_from_id = %s WHERE id = %s",
        (old_key_id, new_key["id"])
    )
    
    return new_key
```

---

### ✅ 2. JWT 安全

#### 使用强密钥

```python
# ❌ 错误：弱密钥
jwt_secret_key = "secret"
jwt_secret_key = "123456"
jwt_secret_key = "my-secret-key"

# ✅ 正确：强密钥
import secrets
jwt_secret_key = secrets.token_urlsafe(32)
# 结果：aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890-_aBcDeFgHiJk

# 或者使用环境变量
jwt_secret_key = os.getenv("JWT_SECRET_KEY")
```

#### 设置合理的过期时间

```python
# ❌ 错误：永不过期
jwt_expiration_minutes = None

# ❌ 错误：过期时间太长
jwt_expiration_minutes = 525600  # 1 年

# ✅ 正确：短期 Token
jwt_expiration_minutes = 15  # 15 分钟

# ✅ 配合 Refresh Token
access_token_expires = timedelta(minutes=15)
refresh_token_expires = timedelta(days=30)
```

#### 验证所有声明

```python
from jose import jwt, JWTError, ExpiredSignatureError

def verify_jwt(token: str) -> dict:
    """完整验证 JWT"""
    
    try:
        # 1. 验证签名和过期时间
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
            },
            issuer="hermes-agent",  # 验证签发者
        )
        
        # 2. 验证必需字段
        if "sub" not in payload:
            raise JWTError("缺少用户 ID")
        
        if "exp" not in payload:
            raise JWTError("缺少过期时间")
        
        return payload
        
    except ExpiredSignatureError:
        raise HTTPException(401, "Token 已过期")
    except JWTError as e:
        raise HTTPException(401, f"Token 无效：{str(e)}")
```

---

### ✅ 3. 传输安全

#### 强制 HTTPS

```python
# FastAPI 配置
@app.middleware("http")
async def enforce_https(request: Request, call_next):
    # 检查是否使用 HTTPS
    if not request.url.scheme == "https" and not settings.debug:
        return JSONResponse(
            status_code=400,
            content={"error": "必须使用 HTTPS"},
        )
    
    return await call_next(request)

# Nginx 配置
server {
    listen 80;
    server_name api.example.com;
    
    # 强制跳转到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name api.example.com;
    
    ssl_certificate /etc/ssl/certs/api.example.com.crt;
    ssl_certificate_key /etc/ssl/private/api.example.com.key;
    
    # 使用强加密套件
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

#### 安全响应头

```python
from fastapi.middleware.cors import CORSMiddleware

# 添加安全头
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # 防止点击劫持
    response.headers["X-Frame-Options"] = "DENY"
    
    # 防止 MIME 类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # XSS 防护
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # 内容安全策略
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # 严格传输安全（HSTS）
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
```

---

### ✅ 4. 防止暴力破解

#### 登录限流

```python
from redis.asyncio import Redis

async def check_login_attempts(username: str) -> bool:
    """检查登录尝试次数"""
    
    key = f"login_attempts:{username}"
    attempts = await redis.get(key)
    
    if attempts and int(attempts) >= 5:
        # 锁定 15 分钟
        ttl = await redis.ttl(key)
        raise HTTPException(
            429,
            f"尝试次数过多，请{ttl}秒后重试",
        )
    
    return True

async def record_login_attempt(username: str, success: bool):
    """记录登录尝试"""
    
    if not success:
        key = f"login_attempts:{username}"
        await redis.incr(key)
        await redis.expire(key, 900)  # 15 分钟
    else:
        # 登录成功，清除记录
        key = f"login_attempts:{username}"
        await redis.delete(key)
```

#### 验证码机制

```python
# 连续失败 5 次后要求验证码
if failed_attempts >= 5:
    # 生成验证码
    captcha = generate_captcha()
    save_to_cache(username, captcha)
    
    # 要求用户提供验证码
    raise HTTPException(
        400,
        "需要验证码",
        headers={"X-Captcha-Required": "true"},
    )

# 验证验证码
def verify_captcha(username: str, user_input: str) -> bool:
    cached = get_from_cache(username)
    if cached != user_input:
        return False
    
    # 验证码只能用一次
    delete_from_cache(username)
    return True
```

---

## 攻击防护

### 攻击 1: API Key 泄露

**场景：**
```
攻击者获取了 API Key：sk-abc123
开始大量调用 API
```

**防护措施：**

```python
# 1. 速率限制
if request_count > 1000:  # 每小时
    block_ip(ip_address)

# 2. 异常检测
if request_pattern == "abnormal":  # 非正常访问模式
    alert_admin()

# 3. IP 白名单
if ip not in whitelist:
    reject_request()

# 4. 快速撤销
revoke_api_key("sk-abc123")
generate_new_key()
```

---

### 攻击 2: JWT 伪造

**场景：**
```
攻击者尝试修改 JWT Payload
{"user_id": "123"} → {"user_id": "admin"}
```

**防护措施：**

```python
# 1. 签名验证
payload = jwt.decode(token, secret_key, algorithms=["HS256"])
# 签名不匹配会抛出异常

# 2. 算法固定
# 明确指定算法，防止算法混淆攻击
jwt.decode(token, secret_key, algorithms=["HS256"])

# 3. 密钥轮换
# 定期更换密钥
rotate_jwt_secret()

# 4. Token 黑名单
# 撤销有问题的 Token
add_to_blacklist(token)
```

---

### 攻击 3: 重放攻击

**场景：**
```
攻击者截获合法请求
稍后重新发送相同的请求
```

**防护措施：**

```python
# 1. 时间戳验证
def verify_timestamp(timestamp: int) -> bool:
    now = time.time()
    # 只接受 5 分钟内的请求
    return abs(now - timestamp) < 300

# 2. Nonce 机制
def verify_nonce(nonce: str) -> bool:
    # 检查 Nonce 是否已使用
    if redis.exists(f"nonce:{nonce}"):
        return False
    
    # 记录 Nonce
    redis.setex(f"nonce:{nonce}", 300, "1")
    return True

# 3. 请求签名
signature = HMAC(secret_key, method + path + timestamp + nonce + body)
```

---

### 攻击 4: 中间人攻击

**场景：**
```
攻击者在客户端和服务器之间
窃听或篡改通信内容
```

**防护措施：**

```python
# 1. 强制 HTTPS
# 所有通信使用 TLS 加密

# 2. HSTS
# Strict-Transport-Security: max-age=31536000

# 3. 证书固定（移动端）
# 只信任特定的证书

# 4. 请求签名
# 防止内容被篡改
```

---

## 审计与监控

### 审计日志

```python
# 记录所有认证事件
async def log_auth_event(
    event_type: str,
    user_id: str,
    ip_address: str,
    user_agent: str,
    success: bool,
    details: dict = None,
):
    """记录认证事件"""
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,  # login, logout, token_refresh, api_key_used
        "user_id": user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "success": success,
        "details": details or {},
    }
    
    # 写入数据库或日志系统
    await db.auth_logs.insert_one(log_entry)

# 使用示例
await log_auth_event(
    event_type="login",
    user_id="user_123",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    success=True,
)
```

### 监控指标

```python
# Prometheus 指标
AUTH_ATTEMPTS = Counter(
    "hermes_auth_attempts_total",
    "认证尝试次数",
    ["type", "result"],  # type: login, api_key; result: success, failure
)

ACTIVE_TOKENS = Gauge(
    "hermes_active_tokens",
    "活跃 Token 数量",
)

REVOKED_KEYS = Gauge(
    "hermes_revoked_keys",
    "已撤销的 API Key 数量",
)

# 告警规则
- alert: HighAuthFailureRate
  expr: |
    sum(rate(hermes_auth_attempts_total{result="failure"}[5m])) 
    / sum(rate(hermes_auth_attempts_total[5m])) > 0.5
  for: 5m
  annotations:
    summary: "认证失败率超过 50%"
```

### 异常检测

```python
# 检测异常登录模式
async def detect_anomalies(user_id: str, ip_address: str) -> bool:
    """检测异常行为"""
    
    # 1. 地理位置异常
    last_ip = await get_last_login_ip(user_id)
    if last_ip and not same_region(last_ip, ip_address):
        return True
    
    # 2. 时间异常
    last_login = await get_last_login_time(user_id)
    if last_login and (now - last_login).seconds < 60:
        return True  # 1 分钟内重复登录
    
    # 3. 频率异常
    recent_logins = await get_recent_logins(user_id, minutes=60)
    if len(recent_logins) > 10:
        return True
    
    return False
```

---

## 故障排查

### 问题 1: Token 验证失败

**现象：**
```
客户端收到 401 Unauthorized
错误信息："Token 无效"
```

**排查步骤：**

```bash
# 1. 检查 Token 格式
echo $TOKEN | cut -d'.' -f1 | base64 -d
# 应该输出：{"alg":"HS256","typ":"JWT"}

# 2. 检查 Token 是否过期
echo $TOKEN | cut -d'.' -f2 | base64 -d
# 查看 exp 字段

# 3. 检查密钥是否匹配
cat .env | grep JWT_SECRET_KEY
```

**解决方案：**

```python
# 方案 1: 刷新 Token
new_token = refresh_access_token(refresh_token)

# 方案 2: 重新登录
login(username, password)

# 方案 3: 检查密钥一致性
# 确保所有服务实例使用相同的 JWT_SECRET_KEY
```

---

### 问题 2: API Key 不生效

**现象：**
```
请求携带了 API Key
仍然收到 401 Unauthorized
```

**排查步骤：**

```bash
# 1. 检查 Header 名称
curl -H "X-API-Key: sk-abc" ...
# 确认与配置一致：api_key_header = "X-API-Key"

# 2. 检查 Key 是否在白名单
cat .env | grep API_KEYS

# 3. 查看日志
grep "API Key" /var/log/hermes-agent/error.log
```

**解决方案：**

```python
# 方案 1: 添加 Key 到白名单
api_keys.append("sk-abc")

# 方案 2: 检查 Key 格式
# 确保没有多余的空格或换行
api_key = api_key.strip()

# 方案 3: 重启服务
# 确保配置生效
systemctl restart hermes-agent
```

---

### 问题 3: 双重认证冲突

**现象：**
```
同时使用 API Key 和 JWT
权限判断出现冲突
```

**排查步骤：**

```bash
# 1. 检查权限配置
curl -H "X-API-Key: sk-abc" -H "Authorization: Bearer $TOKEN" ...

# 2. 查看权限解析日志
grep "permission" /var/log/hermes-agent/access.log

# 3. 检查优先级配置
# 用户权限优先还是应用权限优先？
```

**解决方案：**

```python
# 明确权限优先级
def has_permission(request: Request, required: str) -> bool:
    # 1. 用户权限优先
    if hasattr(request.state, "user_permissions"):
        return required in request.state.user_permissions
    
    # 2. 降级到应用权限
    if hasattr(request.state, "app_permissions"):
        return required in request.state.app_permissions
    
    # 3. 默认拒绝
    return False
```

---

## 配置对比表

| 配置项 | 开发环境 | 测试环境 | 生产环境 | 说明 |
|--------|---------|---------|---------|------|
| `api_keys` | `[]` (不验证) | `["test-key"]` | `["sk-xxx", ...]` | 生产必须配置 |
| `jwt_secret_key` | `"dev-secret"` | `"test-secret"` | `强随机密钥` | 生产用强密钥 |
| `jwt_algorithm` | `HS256` | `HS256` | `HS256/HS512` | 推荐 HS256 |
| `jwt_expiration` | `60 分钟` | `30 分钟` | `15 分钟` | 生产更短 |
| `双重认证` | 禁用 | 启用 | 启用 | 生产推荐 |

---

## 总结

### 核心要点

1. **API Key**：简单、适合服务端认证
2. **JWT**：安全、可携带用户信息
3. **双重认证**：最安全、适合复杂场景
4. **HTTPS**：必须使用、防止窃听
5. **审计监控**：及时发现问题

### 安全原则

- 🔐 **最小权限**：只授予必要的权限
- ⏰ **短期有效**：Token 尽快过期
- 🔄 **定期轮换**：密钥定期更换
- 📊 **全面审计**：记录所有认证事件
- 🚨 **快速响应**：及时发现和处理异常

### 最佳实践

- ✅ 使用强密钥（32+ 字符）
- ✅ Token 过期时间 ≤ 15 分钟
- ✅ 配合 Refresh Token 机制
- ✅ 强制 HTTPS
- ✅ 添加安全响应头
- ✅ 实现速率限制
- ✅ 记录审计日志
- ✅ 监控异常行为

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**所属项目：** Hermes-Agent FastAPI 服务  
**作者：** Hermes-Agent Team

# CORS 中间件详解 - FastAPI 跨域资源共享指南

> CORS（Cross-Origin Resource Sharing）是现代 Web 应用中处理跨域请求的核心机制。本文档详细讲解 FastAPI 中的 CORS 中间件配置和使用。

---

## 📋 目录

- [什么是 CORS](#什么是 cors)
- [为什么需要 CORS](#为什么需要 cors)
- [同源策略](#同源策略)
- [CORS 工作原理](#cors 工作原理)
- [FastAPI CORS 中间件](#fastapi-cors-中间件)
- [配置参数详解](#配置参数详解)
- [实战示例](#实战示例)
- [安全问题](#安全问题)
- [调试技巧](#调试技巧)
- [常见问题](#常见问题)

---

## 什么是 CORS

### 定义

**CORS（Cross-Origin Resource Sharing，跨域资源共享）** 是一种基于 HTTP 头部的机制，允许浏览器验证服务器是否允许来自不同源（域名、协议、端口）的跨域请求。

### 通俗理解

```
前端应用（http://localhost:3000）
        ↓
    跨域请求
        ↓
后端 API（http://api.example.com:8000）
        ↓
    CORS 验证
        ↓
    允许/拒绝
```

### 为什么浏览器要限制跨域？

**安全原因：** 防止恶意网站窃取数据。

```
如果没有 CORS 限制：
恶意网站 (evil.com) → 请求 → 银行 API (bank.com)
                     → 获取用户数据 ❌

有了 CORS 限制：
恶意网站 (evil.com) → 请求 → 银行 API (bank.com)
                     → 浏览器拦截 ❌
                     → bank.com 未允许 evil.com 跨域
```

---

## 为什么需要 CORS

### 前后端分离场景

```
┌─────────────────┐         ┌─────────────────┐
│  前端应用        │         │  后端 API        │
│  localhost:3000 │ ──────→ │  localhost:8000 │
│  (React/Vue)    │  跨域    │  (FastAPI)      │
└─────────────────┘         └─────────────────┘
        ↓                           ↓
   不同端口                     不同端口
   = 不同源                     需要 CORS
```

### 微服务架构

```
┌─────────────────┐
│  Web 应用        │
│  app.com        │
└────────┬────────┘
         │
    ┌────┴────┬────────────┬────────────┐
    ↓         ↓            ↓            ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ API 1   │ │ API 2   │ │ API 3   │ │ CDN    │
│ a.com  │ │ b.com  │ │ c.com  │ │ cdn.com│
└────────┘ └────────┘ └────────┘ └────────┘
  跨域      跨域       跨域       跨域
```

### 第三方 API 集成

```
你的应用 (your-app.com)
        ↓
    跨域请求
        ↓
第三方 API (stripe.com, google.com, github.com)
        ↓
    CORS 响应头
        ↓
允许你的域名访问
```

---

## 同源策略

### 什么是同源？

**同源（Same Origin）** 是指两个 URL 的**协议**、**域名**、**端口**都完全相同。

```
URL: https://example.com:443/path?query=value
     └─┬─┘  └──┬───┘ └─┬─┘
      协议    域名    端口

同源 = 协议相同 + 域名相同 + 端口相同
```

### 同源判断示例

| URL 1 | URL 2 | 是否同源 | 原因 |
|-------|-------|---------|------|
| `http://example.com` | `http://example.com` | ✅ 是 | 完全相同 |
| `http://example.com` | `https://example.com` | ❌ 否 | 协议不同 |
| `http://example.com` | `http://api.example.com` | ❌ 否 | 域名不同 |
| `http://example.com:80` | `http://example.com:8000` | ❌ 否 | 端口不同 |
| `http://localhost:3000` | `http://localhost:8000` | ❌ 否 | 端口不同 |

### 同源策略限制的操作

浏览器同源策略限制以下操作：

1. **AJAX/Fetch 请求** - 跨域请求会被拦截
2. **DOM 访问** - 无法访问不同源页面的 DOM
3. **Cookie/Storage** - 无法读取不同源的 Cookie、LocalStorage

---

## CORS 工作原理

### 简单请求

某些请求不会触发预检（OPTIONS），称为**简单请求**。

**条件：**
1. 方法是 `GET`、`POST`、`HEAD` 之一
2. 头部只包含简单字段（如 `Accept`、`Content-Type` 等）
3. `Content-Type` 只限于：
   - `application/x-www-form-urlencoded`
   - `multipart/form-data`
   - `text/plain`

**流程：**
```
浏览器                    服务器
  ↓                        ↓
发送请求 (Origin 头)  ─────→
                        ↓
                    添加 CORS 头
                        ↓
返回响应 (Access-Control-*) ──→
  ↓                        ↓
检查 CORS 头
  ↓
允许/拒绝访问
```

### 预检请求（Preflight）

不满足简单请求条件的请求，会先发送一个 `OPTIONS` 预检请求。

**流程：**
```
浏览器                    服务器
  ↓                        ↓
发送 OPTIONS 请求      ─────→
(Check CORS)              ↓
                        检查允许
                        ↓
返回允许的方法/头部     ──→
  ↓                        ↓
检查通过
  ↓
发送实际请求          ─────→
  ↓                        ↓
接收响应               ──→
```

**示例：**
```javascript
// 前端代码
fetch('http://api.example.com/data', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token'  // 自定义头部
    },
    body: JSON.stringify({ data: 'test' })
})
```

**浏览器发送预检请求：**
```http
OPTIONS /data HTTP/1.1
Host: api.example.com
Origin: http://localhost:3000
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type, Authorization
```

**服务器响应：**
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

---

## FastAPI CORS 中间件

### 导入 CORSMiddleware

```python
from fastapi.middleware.cors import CORSMiddleware
```

### 基本配置

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### 执行流程

```
请求进入
    ↓
[CORS 中间件]
    ↓
检查 Origin 头
    ↓
验证是否在 allow_origins 中
    ↓
是 → 添加 CORS 响应头
否 → 拒绝请求
    ↓
继续处理请求
    ↓
返回响应（带 CORS 头）
```

---

## 配置参数详解

### 1. allow_origins（允许的源）

**类型：** `List[str]`  
**作用：** 指定允许跨域访问的域名列表

```python
# 允许特定域名
allow_origins=[
    "http://localhost:3000",
    "http://localhost:8080",
    "https://myapp.com",
    "https://www.myapp.com"
]

# 允许所有域名（不推荐生产环境）
allow_origins=["*"]

# 动态允许（见下方高级用法）
```

**注意事项：**
- ❌ 不能同时指定具体域名和使用 `["*"]`
- ❌ 不支持通配符（如 `*.example.com`）
- ✅ 必须包含协议和端口（如果有）

---

### 2. allow_credentials（允许凭证）

**类型：** `bool`  
**作用：** 是否允许发送 Cookie、认证头等凭证信息

```python
# 允许凭证
allow_credentials=True

# 不允许凭证（默认）
allow_credentials=False
```

**响应头：**
```http
Access-Control-Allow-Credentials: true
```

**前端使用：**
```javascript
// 允许发送 Cookie
fetch('http://api.example.com/data', {
    credentials: 'include'  // 或 'same-origin'
})

// Axios 配置
axios.create({
    baseURL: 'http://api.example.com',
    withCredentials: true  // 发送 Cookie
})
```

**注意事项：**
- ⚠️ 当 `allow_credentials=True` 时，`allow_origins` 不能为 `["*"]`
- ⚠️ 必须明确指定允许的域名

---

### 3. allow_methods（允许的方法）

**类型：** `List[str]`  
**作用：** 指定允许的 HTTP 方法

```python
# 允许所有方法
allow_methods=["*"]

# 允许特定方法
allow_methods=["GET", "POST", "PUT", "DELETE"]

# 只读权限
allow_methods=["GET", "HEAD", "OPTIONS"]
```

**响应头：**
```http
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
```

---

### 4. allow_headers（允许的头部）

**类型：** `List[str]`  
**作用：** 指定允许的请求头部

```python
# 允许所有头部
allow_headers=["*"]

# 允许特定头部
allow_headers=[
    "Content-Type",
    "Authorization",
    "X-Requested-With",
    "Accept"
]
```

**响应头：**
```http
Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With
```

**简单头部（不需要声明）：**
- `Accept`
- `Accept-Language`
- `Content-Language`
- `Content-Type`（部分限制）

---

### 5. allow_origin_regex（正则匹配源）

**类型：** `str`  
**作用：** 使用正则表达式匹配允许的源

```python
# 允许所有子域名
allow_origin_regex=r"https://.*\.example\.com"

# 允许 localhost 所有端口
allow_origin_regex=r"http://localhost:\d+"

# 组合使用
allow_origin_regex=r"https://(www\.)?example\.com"
```

**注意事项：**
- ⚠️ 不能与 `allow_origins=["*"]` 同时使用
- ⚠️ 正则表达式必须匹配完整的源（包含协议）

---

### 6. expose_headers（暴露的头部）

**类型：** `List[str]`  
**作用：** 指定浏览器可以访问的响应头部

```python
# 默认浏览器只能访问简单头部
# 自定义头部需要显式暴露
expose_headers=[
    "X-Custom-Header",
    "X-Request-ID",
    "X-Total-Count"
]
```

**响应头：**
```http
Access-Control-Expose-Headers: X-Custom-Header, X-Request-ID
```

**前端访问：**
```javascript
const response = await fetch(url)
// 默认可以访问
console.log(response.status)
console.log(response.headers.get('Content-Type'))

// 需要 expose_headers 才能访问
console.log(response.headers.get('X-Custom-Header'))
```

---

### 7. max_age（预检缓存时间）

**类型：** `int`（秒）  
**作用：** 预检请求结果的缓存时间

```python
# 缓存 24 小时
max_age=86400

# 缓存 1 小时
max_age=3600

# 不缓存
max_age=0
```

**响应头：**
```http
Access-Control-Max-Age: 86400
```

**作用：**
- 在缓存时间内，相同的预检请求不需要再次发送
- 减少网络请求，提高性能

---

## 实战示例

### 示例 1：开发环境配置

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 开发环境：允许所有跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**适用场景：**
- ✅ 本地开发
- ✅ 测试环境
- ❌ 不推荐生产环境

---

### 示例 2：生产环境配置

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 生产环境：明确指定允许的域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myapp.com",
        "https://www.myapp.com",
        "https://app.myapp.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    expose_headers=["X-Request-ID", "X-Total-Count"],
    max_age=86400,  # 缓存 24 小时
)
```

**适用场景：**
- ✅ 生产环境
- ✅ 明确的前端域名

---

### 示例 3：多环境配置

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

app = FastAPI()

# 根据环境配置不同的 CORS
if settings.debug:
    # 开发环境
    origins = ["*"]
else:
    # 生产环境
    origins = [
        "https://myapp.com",
        "https://www.myapp.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=not settings.debug,  # 生产环境允许凭证
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**配置文件：**
```python
# settings.py
class Settings:
    debug: bool = False
    environment: str = "production"
```

---

### 示例 4：动态允许源

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 允许的域名列表
ALLOWED_ORIGINS = [
    "https://myapp.com",
    "https://www.myapp.com",
]

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    
    origin = request.headers.get("origin")
    
    # 动态设置 CORS
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    
    return response
```

**适用场景：**
- ✅ 需要动态控制 CORS
- ✅ 多个前端项目

---

### 示例 5：子域名支持

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 使用正则匹配所有子域名
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.myapp\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**允许的域名：**
- ✅ `https://app.myapp.com`
- ✅ `https://api.myapp.com`
- ✅ `https://admin.myapp.com`
- ❌ `https://myapp.com`（没有子域名）

---

### 示例 6：Android App 跨域

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Android App 的 WebView 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # 本地开发
        "http://localhost:3000",
        "http://localhost:8080",
        # 生产环境
        "https://myapp.com",
        # Android WebView
        "file://",  # 本地文件
        "content://",  # Content Provider
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Android WebView 配置：**
```kotlin
val webView = findViewById<WebView>(R.id.webview)
webView.settings.apply {
    javaScriptEnabled = true
    allowFileAccess = true
    allowContentAccess = true
    domStorageEnabled = true
}

// 加载本地文件
webView.loadUrl("file:///android_asset/index.html")
```

---

### 示例 7：Hermes-Agent 实际配置

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

app = FastAPI()

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 从配置读取
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)
```

**配置文件：**
```python
# .env
# 开发环境
CORS_ORIGINS=["*"]
CORS_CREDENTIALS=True
CORS_METHODS=["*"]
CORS_HEADERS=["*"]

# 生产环境
CORS_ORIGINS=["https://hermes-agent.com", "https://app.hermes-agent.com"]
CORS_CREDENTIALS=True
CORS_METHODS=["GET", "POST", "PUT", "DELETE"]
CORS_HEADERS=["Content-Type", "Authorization", "X-API-Key"]
```

---

## 安全问题

### 1. 避免使用通配符（生产环境）

```python
# ❌ 错误：生产环境允许所有源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 危险！
    allow_credentials=True,  # 更危险！
)

# ✅ 正确：明确指定允许的源
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trusted-domain.com",
        "https://app.trusted-domain.com",
    ],
    allow_credentials=True,
)
```

**风险：**
- 恶意网站可以访问你的 API
- 可能泄露用户数据
- CSRF 攻击风险

---

### 2. 正确配置 allow_credentials

```python
# ❌ 错误：通配符 + 凭证
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ 不能与 credentials 一起用
    allow_credentials=True,
)

# ✅ 正确：明确域名 + 凭证
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted.com"],
    allow_credentials=True,
)
```

**浏览器错误：**
```
The 'Access-Control-Allow-Origin' header has the value '*' that is not 
included in the allowed list, but the 'Access-Control-Allow-Credentials' 
header is 'true'.
```

---

### 3. 限制 HTTP 方法

```python
# ❌ 错误：允许所有方法
allow_methods=["*"]

# ✅ 正确：只允许需要的方法
allow_methods=["GET", "POST", "PUT", "DELETE"]

# ✅ 更好：只读权限
allow_methods=["GET", "HEAD", "OPTIONS"]
```

**最小权限原则：**
- 只开放必要的 HTTP 方法
- 避免不必要的风险

---

### 4. 限制请求头部

```python
# ❌ 错误：允许所有头部
allow_headers=["*"]

# ✅ 正确：只允许需要的头部
allow_headers=[
    "Content-Type",
    "Authorization",
    "X-API-Key",
    "X-Requested-With",
]
```

**风险：**
- 恶意头部可能绕过安全检查
- 信息泄露风险

---

### 5. 验证 Origin 头

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

ALLOWED_ORIGINS = [
    "https://trusted.com",
    "https://app.trusted.com",
]

@app.middleware("http")
async def validate_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    
    # 验证 Origin
    if origin and origin not in ALLOWED_ORIGINS:
        return JSONResponse(
            status_code=403,
            content={"error": "Origin not allowed"}
        )
    
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 调试技巧

### 1. 浏览器开发者工具

**Network 面板查看 CORS 错误：**
```
Console 标签页：
Access to fetch at 'http://api.example.com/data' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present 
on the requested resource.
```

**Network 标签页查看请求：**
```
General:
  Request URL: http://api.example.com/data
  Request Method: OPTIONS  ← 预检请求
  Status Code: 200

Response Headers:
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Methods: GET, POST, OPTIONS
  Access-Control-Allow-Headers: Content-Type, Authorization
```

---

### 2. 使用 curl 测试

```bash
# 简单请求
curl -H "Origin: http://localhost:3000" \
     -v http://localhost:8000/api/v1/health

# 预检请求
curl -X OPTIONS \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type, Authorization" \
     -v http://localhost:8000/api/v1/chat
```

**查看响应头：**
```http
< Access-Control-Allow-Origin: http://localhost:3000
< Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
< Access-Control-Allow-Headers: Content-Type, Authorization
< Access-Control-Allow-Credentials: true
```

---

### 3. 添加 CORS 日志

```python
import logging
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_cors(request: Request, call_next):
    origin = request.headers.get("origin")
    method = request.method
    
    logger.info(f"CORS Request: {method} from {origin}")
    
    response = await call_next(request)
    
    cors_headers = {
        key: value for key, value in response.headers.items()
        if key.startswith("access-control")
    }
    
    if cors_headers:
        logger.info(f"CORS Response: {cors_headers}")
    
    return response
```

---

## 常见问题

### Q1: 什么是 CORS 错误？

**A:** CORS 错误是浏览器阻止跨域请求时的错误提示。

**常见错误：**
```
Access to fetch at 'http://api.example.com' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is 
present on the requested resource.
```

**原因：**
- 后端没有添加 CORS 中间件
- `allow_origins` 没有包含前端域名
- 其他 CORS 配置不正确

**解决：**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Q2: 为什么设置了 CORS 还是报错？

**A:** 检查以下几点：

1. **中间件顺序**
   ```python
   # ✅ 正确：CORS 中间件在其他中间件之前
   app.add_middleware(CORSMiddleware, ...)
   app.add_middleware(LoggingMiddleware)
   app.add_middleware(APIKeyMiddleware)
   
   # ❌ 错误：CORS 在其他中间件之后
   app.add_middleware(LoggingMiddleware)
   app.add_middleware(APIKeyMiddleware)
   app.add_middleware(CORSMiddleware, ...)  # 可能不生效
   ```

2. **OPTIONS 请求被拦截**
   ```python
   # 确保 OPTIONS 请求不被认证中间件拦截
   @app.middleware("http")
   async def auth_middleware(request: Request, call_next):
       if request.method == "OPTIONS":
           return await call_next(request)  # 跳过认证
       
       # ... 认证逻辑
   ```

3. **响应头被覆盖**
   ```python
   # 确保没有手动设置 CORS 头覆盖中间件
   @app.get("/api")
   async def api():
       response = Response()
       # ❌ 不要手动设置
       # response.headers["Access-Control-Allow-Origin"] = "*"
       return data
   ```

---

### Q3: 如何处理预检请求？

**A:** FastAPI 自动处理预检请求，无需手动处理。

```python
# FastAPI 自动处理 OPTIONS 请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 包含 OPTIONS
    allow_headers=["*"],
)

# 无需手动添加 OPTIONS 路由
# @app.options("/api")  # ❌ 不需要
```

---

### Q4: 开发环境和生产环境如何配置？

**A:** 使用环境变量区分配置。

```python
# .env.development
CORS_ORIGINS=["*"]
CORS_CREDENTIALS=True

# .env.production
CORS_ORIGINS=["https://myapp.com", "https://www.myapp.com"]
CORS_CREDENTIALS=True
```

```python
# config.py
class Settings:
    debug: bool = False
    cors_origins: List[str] = ["*"] if debug else ["https://myapp.com"]
    
settings = Settings()

# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Q5: 如何处理多个前端项目？

**A:** 使用列表或正则表达式。

```python
# 方式 1：明确列出所有域名
allow_origins=[
    "https://app1.com",
    "https://app2.com",
    "https://app3.com",
]

# 方式 2：使用正则
allow_origin_regex=r"https://app\d+\.com"

# 方式 3：动态验证
@app.middleware("http")
async def dynamic_cors(request: Request, call_next):
    origin = request.headers.get("origin")
    
    if origin and is_allowed(origin):  # 自定义验证逻辑
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        return response
    
    return await call_next(request)
```

---

### Q6: Android WebView 如何处理 CORS？

**A:** Android WebView 需要特殊配置。

**后端配置：**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "file://",      # 本地文件
        "content://",   # Content Provider
        "https://myapp.com",  # 线上域名
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Android 配置：**
```kotlin
webView.settings.apply {
    javaScriptEnabled = true
    allowFileAccess = true
    allowContentAccess = true
    domStorageEnabled = true
}

// Android 5.0+ 需要额外配置
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
    webView.settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
}
```

---

## Android 对比理解

### CORS vs Android 网络权限

```python
# FastAPI CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted.com"],
)
```

```kotlin
<!-- Android 网络权限 -->
<uses-permission android:name="android.permission.INTERNET" />

<!-- AndroidManifest.xml -->
<application android:usesCleartextTraffic="true">
    <!-- 允许 HTTP（Android 9+ 默认只允许 HTTPS） -->
</application>
```

### 跨域对比

| 场景 | Web (CORS) | Android |
|------|-----------|---------|
| **不同域名** | 需要 CORS | 不需要（网络请求） |
| **不同端口** | 需要 CORS | 不需要 |
| **WebView** | 需要 CORS | 需要配置 WebView |
| **Cookie** | 需要 `credentials` | CookieManager |

---

## 总结

### 核心知识点

1. **CORS 是什么**
   - 跨域资源共享机制
   - 基于 HTTP 头部
   - 浏览器实施的安全策略

2. **为什么需要 CORS**
   - 前后端分离架构
   - 微服务架构
   - 第三方 API 集成

3. **FastAPI CORS 配置**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://trusted.com"],  # 允许的源
       allow_credentials=True,                  # 允许凭证
       allow_methods=["*"],                     # 允许的方法
       allow_headers=["*"],                     # 允许的头部
   )
   ```

4. **安全最佳实践**
   - ✅ 生产环境明确指定域名
   - ✅ 避免使用通配符
   - ✅ 限制 HTTP 方法和头部
   - ✅ 正确配置 credentials

### 配置检查清单

- [ ] 开发环境使用 `["*"]`
- [ ] 生产环境明确指定域名
- [ ] 需要 Cookie 时设置 `credentials=True`
- [ ] 限制允许的 HTTP 方法
- [ ] 限制允许的请求头部
- [ ] 设置合理的 `max_age` 缓存时间
- [ ] 验证 Origin 头防止恶意请求

### 调试工具

- 🔍 浏览器开发者工具（Console、Network）
- 🔍 curl 命令测试
- 🔍 添加 CORS 日志
- 🔍 在线 CORS 测试工具

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**适用对象：** Web 开发者、Android 开发者、后端开发者  
**作者：** Hermes-Agent Team

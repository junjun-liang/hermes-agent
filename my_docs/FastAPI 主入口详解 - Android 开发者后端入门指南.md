# FastAPI 主入口详解 - Android 开发者后端入门指南

> 本文档专为 Android 开发者设计，通过对比 Android 开发概念，帮助您快速理解 FastAPI 后端服务的架构和业务逻辑。

---

## 📋 目录

- [文件概览](#文件概览)
- [核心概念对比](#核心概念对比)
- [代码逐行解析](#代码逐行解析)
- [技术栈详解](#技术栈详解)
- [业务逻辑流程](#业务逻辑流程)
- [Android 与后端对比](#android 与后端对比)
- [快速上手部署](#快速上手部署)
- [常见问题](#常见问题)

---

## 文件概览

### 文件作用

`fastapi_server/main.py` 是整个 FastAPI 服务的**主入口文件**，相当于 Android 开发中的：

```
Android              FastAPI
─────────────────────────────────
Application class → main.py (app 实例)
MainActivity      → routes/*.py (路由处理)
AndroidManifest   → @app装饰器 (路由配置)
```

### 核心功能

1. **创建应用实例** - 初始化 FastAPI 应用
2. **配置中间件** - 处理跨域、认证、限流等
3. **注册路由** - 绑定 API 端点
4. **异常处理** - 全局错误捕获
5. **监控指标** - Prometheus 集成
6. **启动服务** - Uvicorn 服务器运行

---

## 核心概念对比

### Android vs FastAPI 核心概念

| Android 概念 | FastAPI 对应 | 说明 |
|------------|-------------|------|
| `Application` | `FastAPI app` | 应用实例，全局上下文 |
| `Activity` | `Router` | 处理特定功能的模块 |
| `Intent` | `Request` | 请求载体 |
| `BroadcastReceiver` | `Middleware` | 拦截和处理请求 |
| `ContentProvider` | `Database` | 数据持久化 |
| `Service` | `Background Task` | 后台任务 |
| `Handler/Looper` | `async/await` | 异步处理 |

---

## 代码逐行解析

### 1. 导入依赖

```python
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
```

#### Android 对比理解

```kotlin
// Android 中的导入
import android.app.Application
import android.content.Context
import androidx.appcompat.app.AppCompatActivity

// FastAPI 中的导入（作用类似）
from fastapi import FastAPI, Request
from .routes import chat_router, sessions_router
```

#### 关键依赖说明

| 模块 | 作用 | Android 类比 |
|------|------|-------------|
| `uvicorn` | ASGI 服务器 | Tomcat/Jetty (Web 服务器) |
| `FastAPI` | Web 框架 | Spring Boot / Retrofit (服务端) |
| `CORSMiddleware` | 跨域中间件 | WebView 跨域设置 |
| `prometheus_client` | 监控指标 | Firebase Analytics / 自定义埋点 |

---

### 2. 日志配置

```python
# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)
```

#### Android 对比

```kotlin
// Android 日志
Log.d("TAG", "message")        // Debug
Log.i("TAG", "message")        // Info
Log.w("TAG", "message")        // Warning
Log.e("TAG", "message")        // Error

// Python 日志
logger.debug("message")
logger.info("message")
logger.warning("message")
logger.error("message")
```

#### 日志级别对应

| Python | Android | 使用场景 |
|--------|---------|---------|
| `DEBUG` | `Log.d` | 调试信息 |
| `INFO` | `Log.i` | 一般信息 |
| `WARNING` | `Log.w` | 警告信息 |
| `ERROR` | `Log.e` | 错误信息 |
| `CRITICAL` | `Log.wtf` | 严重错误 |

---

### 3. Prometheus 指标定义

```python
# Prometheus 指标
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
```

#### Android 对比理解

```kotlin
// Firebase Analytics 事件追踪
FirebaseAnalytics.getInstance(context).logEvent("api_call", bundle)

// 自定义性能监控
val startTime = System.currentTimeMillis()
// ... 执行操作
val duration = System.currentTimeMillis() - startTime
PerformanceMonitor.record("api_duration", duration)
```

#### 三种指标类型

| 类型 | 特点 | Android 类比 | 使用场景 |
|------|------|-------------|---------|
| **Counter** | 只增不减 | 计数器（下载进度） | 请求总数、错误总数 |
| **Histogram** | 统计分布 | 性能直方图 | 请求延迟分布 |
| **Gauge** | 可增可减 | 仪表盘（电量显示） | 活跃连接数、CPU 使用率 |

---

### 4. 应用生命周期管理

```python
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
```

#### Android 对比

```kotlin
// Application 类
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // 初始化全局配置
        // 类似 lifespan 的启动部分
    }
    
    override fun onTerminate() {
        super.onTerminate()
        // 清理资源（实际很少调用）
        // 类似 lifespan 的关闭部分
    }
}

// Activity 生命周期
class MainActivity : AppCompatActivity() {
    override fun onCreate() { /* 初始化 */ }
    override fun onStart() { /* 可见 */ }
    override fun onResume() { /* 前台 */ }
    override fun onPause() { /* 失去焦点 */ }
    override fun onStop() { /* 不可见 */ }
    override fun onDestroy() { /* 销毁 */ }
}
```

#### 生命周期对比

| FastAPI | Android | 触发时机 |
|---------|---------|---------|
| `lifespan` 启动 | `Application.onCreate()` | 应用启动 |
| `lifespan` yield | - | 应用运行中 |
| `lifespan` 关闭 | `Application.onTerminate()` | 应用关闭 |

---

### 5. 创建 FastAPI 应用

```python
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
```

#### Android 对比

```kotlin
// 创建 Application 实例
class MyApplication : Application() {
    // FastAPI 的 app 实例类似于 Application 对象
}

// 或者类似初始化配置
val config = AppConfig(
    appName = "Hermes-Agent API",
    version = "1.0.0",
    debug = true
)
```

#### 配置参数说明

| 参数 | 作用 | 默认值 | Android 类比 |
|------|------|--------|-------------|
| `title` | API 标题 | - | `app_name` (strings.xml) |
| `description` | API 描述 | - | 应用描述 |
| `version` | API 版本 | - | `versionName` (build.gradle) |
| `docs_url` | Swagger 文档路径 | `/docs` | 开发者文档 |
| `redoc_url` | ReDoc 文档路径 | `/redoc` | API 参考文档 |
| `lifespan` | 生命周期管理 | - | `Application` 类 |

---

### 6. 中间件配置

```python
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
```

#### Android 对比理解

```kotlin
// OkHttp 拦截器（类似中间件）
class AuthInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .build()
        return chain.proceed(request)
    }
}

val client = OkHttpClient.Builder()
    .addInterceptor(AuthInterceptor())      // 类似 APIKeyMiddleware
    .addInterceptor(LoggingInterceptor())   // 类似 LoggingMiddleware
    .addInterceptor(RateLimitInterceptor()) // 类似 RateLimitMiddleware
    .build()
```

#### 中间件执行顺序

```
请求 → [CORS] → [日志] → [限流] → [认证] → 路由处理 → 响应
       ↓        ↓        ↓        ↓
    跨域检查  记录日志  检查频率  验证 Key
```

#### 各中间件作用

| 中间件 | 作用 | Android 类比 |
|--------|------|-------------|
| `CORSMiddleware` | 允许跨域请求 | WebView 跨域设置 |
| `LoggingMiddleware` | 记录请求日志 | OkHttp LoggingInterceptor |
| `RateLimitMiddleware` | 限制请求频率 | 限流拦截器 |
| `APIKeyMiddleware` | 验证 API Key | Token 验证拦截器 |

---

### 7. 全局异常处理

```python
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
```

#### Android 对比

```kotlin
// Retrofit 异常处理
try {
    val response = api.getData()
    // 处理成功响应
} catch (e: HttpException) {
    // HTTP 异常（类似 HTTPException）
    when (e.code()) {
        400 -> showError("请求参数错误")
        401 -> showError("未授权")
        404 -> showError("资源不存在")
        500 -> showError("服务器错误")
    }
} catch (e: Exception) {
    // 通用异常
    Log.e("API", "Unknown error", e)
    showError("网络请求失败")
}

// 全局异常捕获（类似 @app.exception_handler）
Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
    // 记录崩溃日志
    // 上报 Crashlytics
}
```

#### 异常类型对比

| FastAPI | Android/Retrofit | HTTP 状态码 |
|---------|------------------|------------|
| `HTTPException(400)` | `HttpException(400)` | 请求错误 |
| `HTTPException(401)` | `HttpException(401)` | 未授权 |
| `HTTPException(404)` | `HttpException(404)` | 未找到 |
| `HTTPException(500)` | `HttpException(500)` | 服务器错误 |
| `Exception` | `IOException` / 其他 | - |

---

### 8. 请求计时器中间件

```python
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
```

#### Android 对比

```kotlin
// OkHttp 拦截器 - 添加请求耗时
class TimingInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val startTime = System.nanoTime()
        val response = chain.proceed(chain.request())
        val duration = (System.nanoTime() - startTime) / 1e9
        
        // 记录性能指标
        PerformanceMonitor.record("api_duration", duration)
        
        // 添加响应头
        return response.newBuilder()
            .addHeader("X-Process-Time", String.format("%.3f", duration))
            .build()
    }
}
```

#### 执行流程

```
请求进入
    ↓
记录开始时间 (start_time)
    ↓
调用下一个中间件/路由 (call_next)
    ↓
计算耗时 (duration = end - start)
    ↓
记录 Prometheus 指标
    ↓
添加响应头 (X-Process-Time)
    ↓
返回响应
```

---

### 9. 注册路由

```python
# ========== 注册路由 ==========

app.include_router(chat_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
```

#### Android 对比

```kotlin
// Activity 注册（类似路由注册）
// AndroidManifest.xml
<activity android:name=".ChatActivity" />
<activity android:name=".SessionsActivity" />
<activity android:name=".ToolsActivity" />
<activity android:name=".SystemActivity" />

// 或者 Fragment 注册
supportFragmentManager.beginTransaction()
    .add(R.id.container, ChatFragment(), "chat")
    .add(R.id.container, SessionsFragment(), "sessions")
    .commit()
```

#### 路由模块说明

| 路由 | 前缀 | 功能 | Android 类比 |
|------|------|------|-------------|
| `chat_router` | `/api/v1` | 聊天对话 | `ChatActivity` |
| `sessions_router` | `/api/v1` | 会话管理 | `SessionsActivity` |
| `tools_router` | `/api/v1` | 工具调用 | `ToolsActivity` |
| `system_router` | `/api/v1` | 系统接口 | `SystemActivity` |

#### 完整 API 端点

```
/api/v1/chat/completions    → chat_router
/api/v1/sessions            → sessions_router
/api/v1/tools               → tools_router
/api/v1/health              → system_router
```

---

### 10. 根路径路由

```python
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
```

#### Android 对比

```kotlin
// 类似应用的启动页/主页
@RestController
class HomeController {
    @GetMapping("/")
    fun home(): Map<String, Any> {
        return mapOf(
            "name" to "Hermes-Agent API",
            "version" to "1.0.0",
            "docs" to "/docs",
            "health" to "/api/v1/health"
        )
    }
}
```

#### 返回示例

访问 `http://localhost:8000/` 返回：

```json
{
    "name": "Hermes-Agent API",
    "version": "1.0.0",
    "docs": "/docs",
    "health": "/api/v1/health"
}
```

---

### 11. 主程序入口

```python
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
```

#### Android 对比

```kotlin
// Android 的 main 函数（简化理解）
fun main() {
    // 类似 Application 启动
    val application = MyApplication()
    application.onCreate()
    
    // 启动主 Activity
    val intent = Intent(application, MainActivity::class.java)
    startActivity(intent)
}

// 或者服务器启动（更接近）
val server = NettyServer()
server.bind(host = "0.0.0.0", port = 8000)
server.start()
```

#### uvicorn.run 参数详解

| 参数 | 作用 | Android 类比 |
|------|------|-------------|
| `"fastapi_server.main:app"` | 应用路径 | `MainActivity::class` |
| `host` | 监听地址 | 服务器 IP |
| `port` | 监听端口 | 服务器端口 |
| `reload` | 热重载 | Debug 模式热更新 |
| `log_level` | 日志级别 | `Log` 级别 |
| `access_log` | 访问日志 | OkHttp 日志拦截器 |
| `workers` | 工作进程数 | 线程池大小 |

---

## 技术栈详解

### 1. FastAPI 框架

#### 什么是 FastAPI？

FastAPI 是一个现代、高性能的 Python Web 框架，用于构建 API。

#### 核心特性

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
```

#### 对比其他框架

| 框架 | 性能 | 学习曲线 | 类型检查 | 自动文档 |
|------|------|---------|---------|---------|
| **FastAPI** | ⭐⭐⭐⭐⭐ | 简单 | ✅ | ✅ |
| Flask | ⭐⭐⭐ | 简单 | ❌ | ❌ |
| Django | ⭐⭐ | 复杂 | ❌ | ❌ |
| Spring Boot | ⭐⭐⭐⭐ | 复杂 | ✅ | ❌ |

---

### 2. Uvicorn 服务器

#### 什么是 Uvicorn？

Uvicorn 是一个 ASGI 服务器，用于运行 Python Web 应用。

```
┌─────────────────┐
│    FastAPI      │  ← Python 应用
├─────────────────┤
│    Uvicorn      │  ← ASGI 服务器
├─────────────────┤
│    Internet     │  ← 网络
└─────────────────┘
```

#### Android 对比

```
Android App
    ↓
Tomcat / Jetty (Web 服务器)
    ↓
Internet

FastAPI App
    ↓
Uvicorn (ASGI 服务器)
    ↓
Internet
```

---

### 3. 异步编程 (async/await)

#### 什么是异步？

异步允许程序在等待 I/O 时执行其他任务，提高并发性能。

```python
# 同步（阻塞）
def get_user():
    user = db.query()      # 等待数据库
    posts = api.get_posts() # 等待 API
    return {"user": user, "posts": posts}

# 异步（非阻塞）
async def get_user():
    user = await db.query()      # 不阻塞，可处理其他请求
    posts = await api.get_posts() # 不阻塞
    return {"user": user, "posts": posts}
```

#### Android 对比

```kotlin
// 同步（阻塞 - 主线程）
fun getUser(): User {
    val user = db.query()      // 阻塞主线程 ❌
    val posts = api.getPosts() // 阻塞主线程 ❌
    return User(user, posts)
}

// 异步（协程 - 推荐）
suspend fun getUser(): User {
    val user = withContext(Dispatchers.IO) {
        db.query()  // 不阻塞主线程 ✅
    }
    val posts = withContext(Dispatchers.IO) {
        api.getPosts() // 不阻塞主线程 ✅
    }
    return User(user, posts)
}

// 或者 RxJava
fun getUser(): Single<User> {
    return Single.zip(
        db.queryAsync(),
        api.getPostsAsync()
    ) { user, posts -> User(user, posts) }
}
```

#### 异步优势

| 场景 | 同步 | 异步 |
|------|------|------|
| 数据库查询 | 阻塞线程 | 释放线程 |
| API 调用 | 等待响应 | 处理其他请求 |
| 文件读写 | 阻塞 I/O | 非阻塞 I/O |
| 并发能力 | 低（1 请求/线程） | 高（多请求/线程） |

---

### 4. Pydantic 数据验证

#### 什么是 Pydantic？

Pydantic 是 Python 的数据验证库，使用类型注解自动验证数据。

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    age: int

# 自动验证
user = UserCreate(username="john", email="john@example.com", age=25)
# ✅ 验证通过

user = UserCreate(username="john", email="invalid", age="not a number")
# ❌ 验证失败，抛出异常
```

#### Android 对比

```kotlin
// data class + 手动验证
data class UserCreate(
    val username: String,
    val email: String,
    val age: Int
)

// 手动验证
fun validateUser(user: UserCreate): Boolean {
    if (user.username.isBlank()) throw IllegalArgumentException("用户名不能为空")
    if (!isValidEmail(user.email)) throw IllegalArgumentException("邮箱格式错误")
    if (user.age < 0) throw IllegalArgumentException("年龄必须为正数")
    return true
}

// 或使用 Kotlin 约束库
@Serializable
data class UserCreate(
    @NotBlank val username: String,
    @Email val email: String,
    @Min(0) val age: Int
)
```

---

### 5. 中间件系统

#### 什么是中间件？

中间件是在请求到达路由之前或响应返回客户端之前执行的代码。

```
请求 → [中间件 1] → [中间件 2] → [路由] → 响应
```

#### 执行流程

```python
@app.middleware("http")
async def middleware1(request: Request, call_next):
    print("中间件 1 - 请求前")
    response = await call_next(request)
    print("中间件 1 - 响应后")
    return response

@app.middleware("http")
async def middleware2(request: Request, call_next):
    print("中间件 2 - 请求前")
    response = await call_next(request)
    print("中间件 2 - 响应后")
    return response
```

输出顺序：
```
中间件 1 - 请求前
中间件 2 - 请求前
[路由处理]
中间件 2 - 响应后
中间件 1 - 响应后
```

#### Android 对比

```kotlin
// OkHttp 拦截器链
val client = OkHttpClient.Builder()
    .addInterceptor { chain ->
        println("拦截器 1 - 请求前")
        val response = chain.proceed(chain.request())
        println("拦截器 1 - 响应后")
        response
    }
    .addInterceptor { chain ->
        println("拦截器 2 - 请求前")
        val response = chain.proceed(chain.request())
        println("拦截器 2 - 响应后")
        response
    }
    .build()
```

---

## 业务逻辑流程

### 完整请求处理流程

```
1. 客户端发送请求
         ↓
2. Uvicorn 接收请求
         ↓
3. CORS 中间件（检查跨域）
         ↓
4. Logging 中间件（记录日志）
         ↓
5. RateLimit 中间件（检查限流）
         ↓
6. APIKey 中间件（验证认证）
         ↓
7. 路由匹配（/api/v1/chat → chat_router）
         ↓
8. 业务逻辑处理（调用 Agent）
         ↓
9. 返回响应
         ↓
10. 中间件处理响应（添加头、记录指标）
         ↓
11. 返回给客户端
```

### 代码示例：聊天请求

```python
# 1. 客户端请求
POST /api/v1/chat/completions
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json
Body:
{
  "message": "你好，请介绍一下自己"
}

# 2-6. 中间件处理（略）

# 7. 路由处理
@app.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    # 8. 业务逻辑
    agent = AIAgent(model="dashscope/deepseek-v4-flash")
    response = agent.chat(request.message)
    
    # 9. 返回响应
    return {
        "message": response,
        "model": agent.model,
        "timestamp": datetime.now()
    }

# 10-11. 返回响应
{
  "message": "你好！我是 Hermes-Agent...",
  "model": "dashscope/deepseek-v4-flash",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## Android 与后端对比

### 架构对比

```
┌─────────────────────────────────────────────────────────┐
│                    Android App                          │
├─────────────────────────────────────────────────────────┤
│  Activity/Fragment  →  ViewModel  →  Repository        │
│                          ↓                              │
│                    Retrofit/OkHttp                      │
│                          ↓                              │
│                    API Server                           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                       │
├─────────────────────────────────────────────────────────┤
│  Router  →  Service  →  Database/External API          │
│    ↓                                                      │
│  Middleware (认证、限流、日志)                           │
│    ↓                                                      │
│  Uvicorn Server                                          │
└─────────────────────────────────────────────────────────┘
```

### 组件映射表

| Android | FastAPI | 说明 |
|---------|---------|------|
| `Application` | `FastAPI app` | 应用实例 |
| `Activity` | `Router` | 功能模块 |
| `Intent` | `Request` | 请求载体 |
| `BroadcastReceiver` | `Middleware` | 拦截器 |
| `Service` | `Background Task` | 后台服务 |
| `ContentProvider` | `Database` | 数据源 |
| `ViewModel` | `Service` | 业务逻辑 |
| `Repository` | `Model` | 数据访问 |
| `Retrofit` | `HTTP Client` | 网络请求 |

---

## 快速上手部署

### 1. 环境准备

```bash
# 安装 Python 3.11+
python --version

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Mac/Linux
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

创建 `.env` 文件：

```bash
# 服务配置
APP_NAME=Hermes-Agent API
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Agent 配置
DEFAULT_MODEL=dashscope/deepseek-v4-flash
MAX_ITERATIONS=90

# 安全配置
API_KEYS=your-api-key-here

# 数据库配置
SESSION_DB_PATH=~/.hermes/state.db
```

### 3. 启动服务

```bash
# 开发模式（热重载）
python -m fastapi_server.main

# 或生产模式
uvicorn fastapi_server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问服务

```bash
# 浏览器访问
http://localhost:8000/

# API 文档
http://localhost:8000/docs

# 健康检查
curl http://localhost:8000/api/v1/health
```

### 5. Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "fastapi_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
# 构建镜像
docker build -t hermes-agent .

# 运行容器
docker run -p 8000:8000 hermes-agent
```

### 6. Android 客户端调用

```kotlin
// Retrofit 接口
interface HermesApi {
    @POST("api/v1/chat/completions")
    @Headers("X-API-Key: your-api-key")
    suspend fun chat(@Body request: ChatRequest): ChatResponse
}

// 数据类
data class ChatRequest(
    val message: String,
    val session_id: String? = null
)

data class ChatResponse(
    val message: String,
    val model: String,
    val timestamp: String
)

// 使用
val retrofit = Retrofit.Builder()
    .baseUrl("http://your-server:8000/")
    .addConverterFactory(GsonConverterFactory.create())
    .build()

val api = retrofit.create(HermesApi::class.java)

val response = api.chat(ChatRequest(message = "你好"))
println(response.message)
```

---

## 常见问题

### Q1: 什么是 ASGI？

**A:** ASGI (Asynchronous Server Gateway Interface) 是 Python Web 服务器的异步协议，类似 Java 的 Servlet 规范。

```
WSGI (同步) → Flask, Django
ASGI (异步) → FastAPI, Starlette
```

### Q2: 为什么要用 async/await？

**A:** 异步可以：
- 提高并发性能（1 线程处理多请求）
- 减少资源消耗（不需要为每个请求创建线程）
- 更好的 I/O 性能（数据库、API 调用）

### Q3: 中间件和装饰器有什么区别？

**A:**
- **中间件**：全局生效，所有请求都经过
- **装饰器**：局部生效，只作用于特定路由

```python
# 中间件（全局）
@app.middleware("http")
async def log_all(request, call_next):
    print("所有请求都记录")
    return await call_next(request)

# 装饰器（局部）
@app.get("/admin")
@require_admin  # 只验证这个路由
async def admin():
    return {"admin": True}
```

### Q4: 如何选择 workers 数量？

**A:** 公式：`workers = (CPU 核心数 * 2) + 1`

```bash
# 4 核 CPU
uvicorn main:app --workers 9

# 8 核 CPU
uvicorn main:app --workers 17
```

### Q5: 开发模式和生产模式有什么区别？

**A:**

| 配置 | 开发模式 | 生产模式 |
|------|---------|---------|
| `reload` | `true` | `false` |
| `workers` | `1` | `多进程` |
| `access_log` | `true` | `false` |
| `debug` | `true` | `false` |

---

## 总结

### 核心知识点

1. **FastAPI 应用结构**
   - 创建应用实例
   - 配置中间件
   - 注册路由
   - 异常处理

2. **异步编程**
   - `async/await` 语法
   - 非阻塞 I/O
   - 提高并发性能

3. **中间件系统**
   - CORS 跨域
   - 认证授权
   - 限流保护
   - 日志记录

4. **数据验证**
   - Pydantic 模型
   - 类型注解
   - 自动验证

5. **部署运维**
   - Uvicorn 服务器
   - Docker 容器化
   - 监控指标

### Android 开发者优势

作为 Android 开发者，您已经具备以下优势：

✅ **面向对象编程** - Python 和 Java/Kotlin 都是 OOP
✅ **异步处理经验** - Coroutine/RxJava → async/await
✅ **网络请求理解** - Retrofit → FastAPI 路由
✅ **架构模式** - MVVM → Router/Service/Model
✅ **调试技能** - Logcat → Python logging

### 下一步学习建议

1. **实践项目** - 用 FastAPI 构建一个简单的 API
2. **学习数据库** - SQLAlchemy（类似 Room）
3. **理解认证** - JWT、OAuth2
4. **学习测试** - pytest（类似 JUnit）
5. **容器化** - Docker、Kubernetes

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**适用对象：** Android 开发者转后端入门  
**作者：** Hermes-Agent Team

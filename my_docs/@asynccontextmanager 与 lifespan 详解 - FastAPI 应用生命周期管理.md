# @asynccontextmanager 与 lifespan 详解 - FastAPI 应用生命周期管理

> 本文档详细讲解 Python 的 `@asynccontextmanager` 装饰器和 FastAPI 的 `lifespan` 参数，帮助开发者理解应用生命周期管理。

---

## 📋 目录

- [基础概念](#基础概念)
- [什么是上下文管理器](#什么是上下文管理器)
- [从同步到异步](#从同步到异步)
- [@asynccontextmanager 详解](#asynccontextmanager-详解)
- [FastAPI lifespan 参数](#fastapi-lifespan-参数)
- [实战示例](#实战示例)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 基础概念

### 什么是应用生命周期？

应用生命周期指的是应用程序从**启动**到**运行**再到**关闭**的整个过程。

```
启动 (Startup) → 运行 (Running) → 关闭 (Shutdown)
   ↓                ↓                ↓
初始化资源        处理请求        清理资源
```

### 为什么需要生命周期管理？

在应用生命周期中，我们需要：

**启动时：**
- 初始化数据库连接
- 加载配置文件
- 创建连接池
- 启动后台任务
- 初始化缓存

**关闭时：**
- 关闭数据库连接
- 清理临时文件
- 保存状态
- 停止后台任务
- 释放资源

---

## 什么是上下文管理器

### 上下文管理器（Context Manager）

上下文管理器是 Python 中用于管理资源的机制，使用 `with` 语句。

#### 同步上下文管理器

```python
# 使用 with 语句管理文件
with open('file.txt', 'r') as f:
    content = f.read()
# 自动关闭文件，无需手动调用 f.close()

# 数据库连接管理
with database_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
# 自动关闭连接
```

#### 实现上下文管理器

```python
class ManagedFile:
    def __init__(self, filename):
        self.filename = filename
    
    def __enter__(self):
        """进入上下文时调用（初始化）"""
        self.file = open(self.filename, 'r')
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时调用（清理）"""
        self.file.close()
        # 返回 True 可以抑制异常，返回 False 或 None 会传播异常
        return False

# 使用
with ManagedFile('test.txt') as f:
    content = f.read()
```

#### 使用 contextlib.contextmanager

```python
from contextlib import contextmanager

@contextmanager
def managed_file(filename):
    """使用装饰器创建上下文管理器"""
    # 进入上下文（初始化）
    f = open(filename, 'r')
    try:
        yield f  # 返回资源
    finally:
        # 退出上下文（清理）
        f.close()

# 使用
with managed_file('test.txt') as f:
    content = f.read()
```

---

## 从同步到异步

### 异步上下文管理器

当资源管理涉及异步操作（如数据库连接、网络请求）时，需要使用异步上下文管理器。

```python
# 同步（阻塞）
with open('file.txt', 'r') as f:
    content = f.read()

# 异步（非阻塞）
async with aiofiles.open('file.txt', 'r') as f:
    content = await f.read()
```

### 实现异步上下文管理器

```python
class AsyncDatabaseConnection:
    async def __aenter__(self):
        """异步进入上下文"""
        self.conn = await create_connection()
        return self.conn
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步退出上下文"""
        await self.conn.close()
        return False

# 使用
async with AsyncDatabaseConnection() as conn:
    result = await conn.query("SELECT * FROM users")
```

---

## @asynccontextmanager 详解

### 什么是 @asynccontextmanager？

`@asynccontextmanager` 是 Python `contextlib` 模块提供的装饰器，用于简化异步上下文管理器的创建。

### 导入

```python
from contextlib import asynccontextmanager
```

### 基本语法

```python
@asynccontextmanager
async def my_async_context():
    # 进入上下文（初始化）
    resource = await create_resource()
    try:
        yield resource  # 返回资源
    finally:
        # 退出上下文（清理）
        await cleanup_resource(resource)
```

### 执行流程

```
调用 my_async_context()
    ↓
执行 yield 之前的代码（初始化）
    ↓
yield resource（返回资源）
    ↓
[使用资源的代码执行]
    ↓
执行 finally 块（清理）
    ↓
返回
```

### 完整示例

```python
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def async_database_connection():
    """异步数据库连接上下文管理器"""
    print("正在连接数据库...")
    conn = await asyncio.sleep(0.1)  # 模拟异步连接
    print("数据库连接成功")
    
    try:
        yield conn  # 返回连接对象
        print("使用连接完成")
    except Exception as e:
        print(f"发生错误：{e}")
        raise
    finally:
        print("正在关闭数据库连接...")
        await asyncio.sleep(0.1)  # 模拟异步关闭
        print("数据库连接已关闭")

# 使用
async def main():
    async with async_database_connection() as conn:
        # 使用连接
        print("正在使用数据库连接...")
        await asyncio.sleep(0.5)

asyncio.run(main())
```

输出：
```
正在连接数据库...
数据库连接成功
正在使用数据库连接...
使用连接完成
正在关闭数据库连接...
数据库连接已关闭
```

### 多个 yield（不推荐）

```python
@asynccontextmanager
async def bad_example():
    yield "first"   # ❌ 多个 yield
    yield "second"  # 会导致问题
```

### 异常处理

```python
@asynccontextmanager
async def safe_context():
    resource = await create_resource()
    try:
        yield resource
    except Exception as e:
        # 处理异常
        print(f"Error: {e}")
        raise  # 重新抛出异常
    finally:
        # 总是执行清理
        await cleanup_resource(resource)
```

---

## FastAPI lifespan 参数

### 什么是 lifespan？

`lifespan` 是 FastAPI 应用的一个参数，用于定义应用的生命周期事件（启动和关闭）。

### 基本用法

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行（初始化）
    print("应用启动")
    yield
    # 关闭时执行（清理）
    print("应用关闭")

app = FastAPI(lifespan=lifespan)
```

### 执行时机

```
启动 FastAPI 应用
    ↓
执行 lifespan 中 yield 之前的代码
    ↓
yield（应用开始处理请求）
    ↓
[应用运行中，处理请求]
    ↓
关闭 FastAPI 应用
    ↓
执行 lifespan 中 yield 之后的代码
    ↓
应用完全关闭
```

### 完整示例

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

# 模拟数据库连接池
class DatabasePool:
    async def connect(self):
        print("数据库连接池初始化")
    
    async def disconnect(self):
        print("数据库连接池关闭")

db_pool = DatabasePool()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    print("=" * 60)
    print("FastAPI 应用启动")
    print("=" * 60)
    
    # 初始化数据库
    await db_pool.connect()
    
    # 加载配置
    print("加载配置文件")
    
    # 启动后台任务
    print("启动后台任务")
    
    yield  # 应用开始运行
    
    # 关闭时
    print("=" * 60)
    print("FastAPI 应用关闭")
    print("=" * 60)
    
    # 关闭数据库连接
    await db_pool.disconnect()
    
    # 保存状态
    print("保存应用状态")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

---

## 实战示例

### 示例 1：数据库连接管理

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import databases

database = databases.Database("postgresql://localhost/mydb")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：连接数据库
    await database.connect()
    print("数据库连接成功")
    yield
    # 关闭：断开连接
    await database.disconnect()
    print("数据库连接已关闭")

app = FastAPI(lifespan=lifespan)

@app.get("/users")
async def get_users():
    query = "SELECT * FROM users"
    return await database.fetch_all(query)
```

### 示例 2：Redis 连接池

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as redis

redis_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：创建 Redis 连接池
    global redis_pool
    redis_pool = redis.RedisPool(
        host='localhost',
        port=6379,
        db=0,
        max_connections=10
    )
    await redis_pool.initialize()
    print("Redis 连接池初始化")
    
    yield
    
    # 关闭：关闭连接池
    await redis_pool.aclose()
    print("Redis 连接池已关闭")

app = FastAPI(lifespan=lifespan)

@app.get("/cache/{key}")
async def get_cache(key: str):
    return await redis_pool.get(key)
```

### 示例 3：后台任务管理

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

background_tasks = []

async def background_task(name: str, interval: int):
    """后台任务"""
    while True:
        print(f"执行后台任务：{name}")
        await asyncio.sleep(interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：创建并启动后台任务
    print("启动后台任务...")
    
    task1 = asyncio.create_task(background_task("clean_cache", 60))
    task2 = asyncio.create_task(background_task("save_state", 300))
    
    background_tasks.extend([task1, task2])
    
    yield
    
    # 关闭：取消后台任务
    print("停止后台任务...")
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    print("所有后台任务已停止")

app = FastAPI(lifespan=lifespan)
```

### 示例 4：多个 lifespan（不推荐）

```python
# ❌ 错误：多个 lifespan
@asynccontextmanager
async def db_lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

@asynccontextmanager
async def cache_lifespan(app: FastAPI):
    await cache.connect()
    yield
    await cache.disconnect()

app = FastAPI()
app.router.lifespan_context = db_lifespan  # ❌ 只能设置一个
app.router.lifespan_context = cache_lifespan  # ❌ 覆盖了上一个
```

### 示例 5：合并 lifespan（推荐）

```python
# ✅ 正确：合并到一个 lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化所有资源
    await db.connect()
    await cache.connect()
    await load_config()
    
    yield
    
    # 关闭：清理所有资源
    await db.disconnect()
    await cache.disconnect()

app = FastAPI(lifespan=lifespan)
```

### 示例 6：Hermes-Agent 实际应用

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Hermes-Agent 应用生命周期管理"""
    
    # ========== 启动时 ==========
    logger.info("=" * 60)
    logger.info("Hermes-Agent API 服务启动")
    logger.info("=" * 60)
    logger.info("版本：%s", app.version)
    logger.info("调试模式：%s", settings.debug)
    logger.info("监听地址：%s:%d", settings.host, settings.port)
    logger.info("=" * 60)
    
    # 初始化数据库
    logger.info("初始化数据库连接...")
    await init_database()
    logger.info("数据库连接成功")
    
    # 加载配置
    logger.info("加载配置文件...")
    await load_config()
    logger.info("配置加载完成")
    
    # 初始化连接池
    logger.info("初始化连接池...")
    await init_connection_pool()
    logger.info("连接池初始化完成")
    
    # 启动后台任务
    logger.info("启动后台任务...")
    start_background_tasks()
    logger.info("后台任务已启动")
    
    logger.info("=" * 60)
    logger.info("应用启动完成，准备接收请求")
    logger.info("=" * 60)
    
    yield  # 应用开始运行
    
    # ========== 关闭时 ==========
    logger.info("=" * 60)
    logger.info("Hermes-Agent API 服务关闭")
    logger.info("=" * 60)
    
    # 停止后台任务
    logger.info("停止后台任务...")
    stop_background_tasks()
    logger.info("后台任务已停止")
    
    # 关闭连接池
    logger.info("关闭连接池...")
    await close_connection_pool()
    logger.info("连接池已关闭")
    
    # 关闭数据库
    logger.info("关闭数据库连接...")
    await close_database()
    logger.info("数据库连接已关闭")
    
    # 保存状态
    logger.info("保存应用状态...")
    await save_state()
    logger.info("状态已保存")
    
    logger.info("=" * 60)
    logger.info("应用已完全关闭")
    logger.info("=" * 60)

app = FastAPI(lifespan=lifespan)
```

---

## 最佳实践

### 1. 异常处理

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # 初始化资源
        await init_resources()
        yield
    except Exception as e:
        # 记录错误
        logger.error(f"启动失败：{e}")
        raise  # 重新抛出，让应用启动失败
    finally:
        # 总是执行清理
        await cleanup_resources()
```

### 2. 资源顺序

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动顺序：先初始化依赖的资源
    await init_database()      # 1. 数据库
    await init_cache()         # 2. 缓存（依赖数据库）
    await init_connection_pool()  # 3. 连接池
    
    yield
    
    # 关闭顺序：与启动相反
    await close_connection_pool()  # 1. 先关闭连接池
    await close_cache()            # 2. 再关闭缓存
    await close_database()         # 3. 最后关闭数据库
```

### 3. 超时控制

```python
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # 设置超时
        await asyncio.wait_for(init_resources(), timeout=30.0)
        yield
    except asyncio.TimeoutError:
        logger.error("初始化超时")
        raise
    finally:
        # 清理时也设置超时
        await asyncio.wait_for(cleanup_resources(), timeout=10.0)
```

### 4. 状态检查

```python
from fastapi import FastAPI, HTTPException

app_state = {"ready": False}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_resources()
    app_state["ready"] = True  # 标记为就绪
    yield
    app_state["ready"] = False  # 标记为关闭
    await cleanup_resources()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    if not app_state["ready"]:
        raise HTTPException(status_code=503, detail="Service unavailable")
    return {"status": "healthy"}
```

### 5. 日志记录

```python
import time

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_time = time.time()
    logger.info("开始启动应用...")
    
    # 初始化
    await init_resources()
    
    duration = time.time() - start_time
    logger.info(f"应用启动完成，耗时：{duration:.2f}秒")
    
    yield
    
    logger.info("开始关闭应用...")
    await cleanup_resources()
    logger.info("应用已关闭")
```

### 6. 依赖注入

```python
from fastapi import Depends

class Database:
    async def connect(self): ...
    async def disconnect(self): ...

db = Database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(lifespan=lifespan)

# 依赖注入
async def get_db():
    try:
        yield db
    finally:
        pass  # 不在这里关闭，由 lifespan 管理

@app.get("/users")
async def get_users(database: Database = Depends(get_db)):
    return await database.query("SELECT * FROM users")
```

---

## 常见问题

### Q1: lifespan 和 @app.on_event("startup") 有什么区别？

**A:** `lifespan` 是新一代的生命周期管理方式，推荐使用。

```python
# 旧方式（不推荐）
@app.on_event("startup")
async def startup():
    await init_resources()

@app.on_event("shutdown")
async def shutdown():
    await cleanup_resources()

# 新方式（推荐）
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_resources()
    yield
    await cleanup_resources()

app = FastAPI(lifespan=lifespan)
```

**区别：**
- `lifespan` 使用单个函数管理启动和关闭
- `lifespan` 支持异步上下文管理器，更优雅
- `lifespan` 可以捕获启动异常
- `@app.on_event` 已被标记为过时

---

### Q2: 如何在 lifespan 中访问配置？

**A:** 通过 `app` 参数或全局配置对象。

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 方式 1：通过 app 访问
    config = app.state.config
    await init_with_config(config)
    
    # 方式 2：使用全局配置
    from .config import settings
    await init_with_config(settings)
    
    yield
    
    await cleanup()
```

---

### Q3: lifespan 中的异常如何处理？

**A:** 异常会传播，导致应用启动失败。

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_database()  # 如果失败，应用启动失败
    except Exception as e:
        logger.error(f"数据库初始化失败：{e}")
        raise  # 重新抛出，停止应用启动
    
    yield
```

---

### Q4: 如何在 lifespan 中启动多个后台任务？

**A:** 使用 `asyncio.create_task` 创建任务列表。

```python
background_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 创建多个后台任务
    task1 = asyncio.create_task(cleanup_job())
    task2 = asyncio.create_task(metrics_job())
    task3 = asyncio.create_task(backup_job())
    
    background_tasks.extend([task1, task2, task3])
    
    yield
    
    # 取消所有任务
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
```

---

### Q5: lifespan 和中间件有什么区别？

**A:** 执行时机不同。

```
请求流程：
    ↓
中间件（每个请求都执行）
    ↓
路由处理
    ↓
响应

应用生命周期：
启动 → lifespan(yield 之前) → 运行 → lifespan(yield 之后) → 关闭
```

**lifespan：** 应用启动/关闭时执行一次  
**中间件：** 每个请求都执行

---

### Q6: 如何在测试中使用 lifespan？

**A:** TestClient 会自动触发 lifespan。

```python
from fastapi.testclient import TestClient
from .main import app

# TestClient 会自动执行 lifespan
with TestClient(app) as client:
    response = client.get("/")
    assert response.status_code == 200
# 退出 with 时自动执行关闭清理
```

---

## Android 对比理解

### lifespan vs Application 生命周期

```python
# FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动（类似 Application.onCreate）
    init_resources()
    yield
    # 关闭（类似 Application.onTerminate）
    cleanup_resources()
```

```kotlin
// Android Application
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // 初始化资源（类似 lifespan yield 之前）
        initResources()
    }
    
    override fun onTerminate() {
        super.onTerminate()
        // 清理资源（类似 lifespan yield 之后）
        cleanupResources()
    }
}
```

### 生命周期对比表

| FastAPI | Android | 执行时机 |
|---------|---------|---------|
| `lifespan` (yield 前) | `Application.onCreate()` | 应用启动 |
| `lifespan` (yield) | - | 应用运行中 |
| `lifespan` (yield 后) | `Application.onTerminate()` | 应用关闭 |
| 中间件 | Interceptor | 每个请求 |
| 后台任务 | WorkManager/Service | 后台执行 |

---

## 总结

### 核心知识点

1. **@asynccontextmanager**
   - 简化异步上下文管理器创建
   - 使用 `yield` 分隔初始化和清理
   - 支持异常处理和 finally 块

2. **lifespan 参数**
   - 管理 FastAPI 应用生命周期
   - 启动时初始化资源
   - 关闭时清理资源

3. **最佳实践**
   - 异常处理（try-finally）
   - 资源顺序（启动正序，关闭逆序）
   - 超时控制（asyncio.wait_for）
   - 日志记录（记录启动/关闭时间）

### 使用场景

| 场景 | 示例 |
|------|------|
| 数据库连接 | 启动连接，关闭断开 |
| 连接池 | 启动创建，关闭销毁 |
| 后台任务 | 启动创建，关闭取消 |
| 配置加载 | 启动加载，关闭保存 |
| 缓存初始化 | 启动连接，关闭断开 |

### 代码模板

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理模板"""
    try:
        # ========== 启动：初始化资源 ==========
        logger.info("正在启动应用...")
        
        # 1. 初始化数据库
        await init_database()
        
        # 2. 初始化连接池
        await init_connection_pool()
        
        # 3. 加载配置
        await load_config()
        
        # 4. 启动后台任务
        start_background_tasks()
        
        logger.info("应用启动完成")
        
        yield  # 应用开始运行
        
    except Exception as e:
        logger.error(f"启动失败：{e}")
        raise
    finally:
        # ========== 关闭：清理资源 ==========
        logger.info("正在关闭应用...")
        
        # 1. 停止后台任务
        stop_background_tasks()
        
        # 2. 关闭连接池
        await close_connection_pool()
        
        # 3. 关闭数据库
        await close_database()
        
        logger.info("应用已关闭")

app = FastAPI(lifespan=lifespan)
```

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**适用对象：** Python 开发者、FastAPI 使用者  
**作者：** Hermes-Agent Team

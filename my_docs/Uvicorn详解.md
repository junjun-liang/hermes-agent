# Uvicorn 详解

## 概述

Uvicorn 是一个基于 Python 的**超快速 ASGI（Asynchronous Server Gateway Interface）服务器**，使用 uvloop 和 httptools 构建，专为异步 Python Web 框架（如 FastAPI、Starlette）设计。

**核心特点：**
- ⚡ **极速性能** — 基于 uvloop（Cython 实现的快速事件循环）和 httptools（C 语言 HTTP 解析器）
- 🔄 **异步原生** — 完全支持 Python 的 async/await 语法
- 🌐 **标准兼容** — 完整实现 ASGI 规范
- 🔧 **易于使用** — 简洁的命令行接口和编程接口
- 📦 **轻量级** — 依赖少，安装简单

---

## 为什么需要 Uvicorn

### Python Web 服务器演进

```
CGI (1993) → mod_python → WSGI (2003) → uWSGI/Gunicorn → ASGI (2016) → Uvicorn
```

| 服务器 | 协议 | 特点 | 适用场景 |
|--------|------|------|----------|
| **Gunicorn** | WSGI | 成熟稳定，多 worker | Django/Flask 等传统框架 |
| **uWSGI** | WSGI | 功能丰富，配置复杂 | 高性能 WSGI 应用 |
| **Uvicorn** | ASGI | 异步原生，极速 | FastAPI/Starlette 等异步框架 |
| **Daphne** | ASGI | Django 官方 ASGI 服务器 | Django Channels |
| **Hypercorn** | ASGI/HTTP2/WSGI | 支持 HTTP/2 和 Trio | 需要 HTTP/2 的场景 |

### WSGI vs ASGI

```python
# WSGI - 同步阻塞
def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [b'Hello World']

# ASGI - 异步非阻塞
async def application(scope, receive, send):
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', b'text/html')],
    })
    await send({
        'type': 'http.response.body',
        'body': b'Hello World',
    })
```

**关键区别：**
- WSGI 是同步的，每个请求占用一个线程/进程
- ASGI 是异步的，单个线程可以处理多个并发请求
- ASGI 支持 WebSocket、HTTP/2、SSE 等现代协议

---

## 安装

```bash
# 基础安装
pip install uvicorn

# 包含标准依赖（推荐）
pip install "uvicorn[standard]"

# 标准依赖包含：
# - uvloop: 高性能事件循环（替代 asyncio）
# - httptools: C 语言 HTTP 解析器
# - websockets: WebSocket 支持
# - python-dotenv: .env 文件支持
```

---

## 命令行使用

### 基本启动

```bash
# 基本启动
uvicorn main:app

# 指定主机和端口
uvicorn main:app --host 0.0.0.0 --port 8000

# 开发模式（热重载）
uvicorn main:app --reload

# 生产模式（多 worker）
uvicorn main:app --workers 4
```

### 完整参数列表

```bash
uvicorn main:app \
    --host 0.0.0.0 \              # 监听地址
    --port 8000 \                  # 监听端口
    --uds /tmp/uvicorn.sock \      # Unix Domain Socket
    --fd 0 \                       # 文件描述符
    --loop uvloop \                # 事件循环: auto|asyncio|uvloop
    --http httptools \             # HTTP 实现: auto|h11|httptools
    --ws websockets \              # WebSocket 实现: auto|none|websockets|wsproto
    --lifespan on \                # 生命周期: auto|on|off
    --interface auto \             # 接口: auto|asgi3|asgi2|wsgi
    --reload \                     # 启用热重载
    --reload-dir ./src \           # 指定重载监视目录
    --workers 4 \                  # worker 进程数
    --env-file .env \              # 环境变量文件
    --log-level info \             # 日志级别: debug|info|warning|error|critical
    --access-log \                 # 启用访问日志
    --no-access-log \              # 禁用访问日志
    --proxy-headers \              # 信任代理头
    --forwarded-allow-ips '*' \    # 允许的代理 IP
    --ssl-keyfile ./key.pem \      # SSL 私钥
    --ssl-certfile ./cert.pem \    # SSL 证书
    --ssl-version 17 \             # SSL 版本
    --ssl-cert-reqs 0 \            # SSL 证书要求
    --ssl-ca-certs ./ca.pem \      # CA 证书
    --ssl-ciphers TLSv1 \          # SSL 密码套件
    --header "Server: Uvicorn" \   # 自定义响应头
    --no-server-header \           # 不发送 Server 头
    --date-header \                # 发送 Date 头
    --no-date-header \             # 不发送 Date 头
    --limit-concurrency 1000 \     # 最大并发连接数
    --limit-max-requests 10000 \   # 每个 worker 最大请求数
    --timeout-keep-alive 5 \       # Keep-Alive 超时（秒）
    --timeout-graceful-shutdown 10 # 优雅关闭超时（秒）
```

### 在 Hermes Agent 中的使用

```bash
# 开发模式
uvicorn fastapi_server.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式（多 worker）
uvicorn fastapi_server.main:app --host 0.0.0.0 --port 8000 --workers 4

# 使用 Gunicorn + Uvicorn Worker（推荐生产部署）
gunicorn fastapi_server.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

---

## 编程接口

### 基础用法

```python
import uvicorn

# 最简单的启动方式
if __name__ == "__main__":
    uvicorn.run("main:app")

# 完整配置
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,
        log_level="info",
        access_log=True,
        loop="uvloop",
        http="httptools",
    )
```

### 高级配置

```python
from uvicorn import Config, Server

async def main():
    config = Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        # SSL 配置
        ssl_keyfile="./key.pem",
        ssl_certfile="./cert.pem",
        # 性能调优
        loop="uvloop",
        http="httptools",
        limit_concurrency=1000,
        timeout_keep_alive=5,
    )
    server = Server(config)
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 核心组件

### 1. uvloop — 高性能事件循环

```python
# uvloop 是 libuv 的 Python 绑定，比标准 asyncio 快 2-4 倍
import uvloop
import asyncio

# 替换默认事件循环
uvloop.install()

async def main():
    # 现在使用 uvloop
    await asyncio.sleep(1)

asyncio.run(main())
```

**性能对比：**

| 事件循环 | 请求/秒 (Hello World) | 延迟 (p99) |
|---------|---------------------|-----------|
| asyncio | 15,000 | 5ms |
| uvloop | 45,000 | 2ms |

### 2. httptools — C 语言 HTTP 解析器

```python
# httptools 使用 Node.js 的 http-parser 库
from httptools import HttpRequestParser

class Protocol:
    def on_url(self, url):
        print(f"URL: {url}")
    
    def on_header(self, name, value):
        print(f"Header: {name} = {value}")
    
    def on_body(self, body):
        print(f"Body: {body}")

parser = HttpRequestParser(Protocol())
parser.feed(b"GET /hello HTTP/1.1\r\nHost: example.com\r\n\r\n")
```

**解析速度：** 比纯 Python 解析器快 10 倍以上

### 3. 生命周期管理

```python
# ASGI 生命周期事件
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("🚀 服务启动中...")
    await init_database()
    await init_redis()
    yield
    # 关闭时执行
    print("🛑 服务关闭中...")
    await close_database()
    await close_redis()

app = FastAPI(lifespan=lifespan)
```

---

## 生产部署

### 1. 使用 systemd 管理

```ini
# /etc/systemd/system/hermes-agent.service
[Unit]
Description=Hermes-Agent API Service
After=network.target

[Service]
Type=simple
User=hermes
Group=hermes
WorkingDirectory=/opt/hermes-agent
Environment=PATH=/opt/hermes-agent/venv/bin
Environment=PYTHONPATH=/opt/hermes-agent
EnvironmentFile=/opt/hermes-agent/.env
ExecStart=/opt/hermes-agent/venv/bin/uvicorn fastapi_server.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --loop uvloop \
    --http httptools \
    --proxy-headers \
    --forwarded-allow-ips '*' \
    --access-log \
    --log-level info
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable hermes-agent
sudo systemctl start hermes-agent
sudo systemctl status hermes-agent
```

### 2. 使用 Gunicorn + Uvicorn Worker

```bash
# 推荐的生产部署方式
# Gunicorn 管理进程，Uvicorn 处理请求

gunicorn fastapi_server.main:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-connections 1000 \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance
```

**Worker 类型：**

| Worker Class | 特点 | 适用场景 |
|-------------|------|----------|
| `uvicorn.workers.UvicornWorker` | 标准 ASGI worker | 大多数场景 |
| `uvicorn.workers.UvicornH11Worker` | 使用 h11 解析器 | 需要 HTTP/1.1 严格兼容 |

### 3. Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 非 root 用户运行
RUN useradd -m -u 1000 hermes && chown -R hermes:hermes /app
USER hermes

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "fastapi_server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=info
    depends_on:
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api

volumes:
  redis_data:
```

### 4. Nginx 反向代理配置

```nginx
upstream hermes_api {
    least_conn;
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    keepalive 32;
}

server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://hermes_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        
        # 超时设置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 120s;
        
        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件缓存
    location /static {
        alias /app/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 性能调优

### 1. Worker 数量

```python
import multiprocessing

# 推荐公式：workers = CPU 核心数 * 2 + 1
workers = multiprocessing.cpu_count() * 2 + 1

# 例如：8 核 CPU → 17 个 worker
# uvicorn main:app --workers 17
```

**注意：**
- 开发环境：`--workers 1` + `--reload`
- 生产环境：`--workers $(($(nproc) * 2 + 1))`
- 容器环境：根据分配的 CPU 限制调整

### 2. 连接优化

```bash
# 调整系统限制
ulimit -n 65535  # 文件描述符限制

# Uvicorn 参数
uvicorn main:app \
    --limit-concurrency 1000 \      # 最大并发连接
    --limit-max-requests 10000 \    # 每个 worker 最大请求数（防内存泄漏）
    --timeout-keep-alive 5 \        # Keep-Alive 超时
    --timeout-graceful-shutdown 30  # 优雅关闭超时
```

### 3. 性能对比

| 服务器 | 并发连接 | 请求/秒 | 延迟 (p99) |
|--------|---------|--------|-----------|
| Flask + Gunicorn | 100 | 2,000 | 50ms |
| Django + Gunicorn | 100 | 1,500 | 80ms |
| FastAPI + Uvicorn | 100 | 15,000 | 5ms |
| FastAPI + Uvicorn (4 workers) | 1000 | 45,000 | 10ms |

---

## 监控与日志

### 结构化日志

```python
import logging
import sys
from uvicorn.config import LOGGING_CONFIG

# 自定义日志格式
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s - %(client_addr)s - %(request_line)s - %(status_code)s"

# JSON 格式日志（生产环境）
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        })

# 配置 Uvicorn 使用 JSON 日志
LOGGING_CONFIG["formatters"]["json"] = {
    "()": JSONFormatter,
}
LOGGING_CONFIG["handlers"]["default"]["formatter"] = "json"
LOGGING_CONFIG["handlers"]["access"]["formatter"] = "json"
```

### 性能指标

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import FastAPI, Response

app = FastAPI()

# 定义指标
requests_total = Counter(
    'hermes_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'hermes_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## 常见问题

### 1. 热重载不生效

```bash
# 确保指定正确的模块路径
uvicorn main:app --reload --reload-dir ./src

# 或者使用 Python 模块方式
uvicorn src.main:app --reload
```

### 2. 高并发下连接错误

```bash
# 增加文件描述符限制
ulimit -n 65535

# 调整 Uvicorn 并发限制
uvicorn main:app --limit-concurrency 1000 --limit-max-requests 10000
```

### 3. 内存泄漏

```bash
# 限制每个 worker 的请求数，自动重启
uvicorn main:app --workers 4 --limit-max-requests 10000

# 或使用 Gunicorn 的 max-requests
 gunicorn main:app -k uvicorn.workers.UvicornWorker --max-requests 10000 --max-requests-jitter 1000
```

### 4. SSE/WebSocket 连接断开

```bash
# 增加超时时间
uvicorn main:app --timeout-keep-alive 300

# Nginx 配置
proxy_read_timeout 300s;
proxy_send_timeout 300s;
```

---

## 总结

Uvicorn 是现代 Python 异步 Web 应用的首选服务器，它提供了：

1. **极致性能** — uvloop + httptools 带来接近 Node.js 的性能
2. **异步原生** — 完美支持 FastAPI、Starlette 等 ASGI 框架
3. **生产就绪** — 支持多 worker、SSL、代理头、优雅关闭
4. **易于部署** — 支持 systemd、Docker、Kubernetes 等多种部署方式

在 Hermes Agent 项目中，Uvicorn 作为 FastAPI 应用的运行服务器，提供高性能的 HTTP API 服务，支持 SSE 流式响应，是连接 Android 客户端和 AI Agent 的核心基础设施。

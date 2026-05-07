# FastAPI 服务启动与日志查看指南

> 本文档详细介绍如何启动 Hermes-Agent FastAPI 服务，并通过日志输出查看运行状态。

---

## 📋 目录

- [项目结构](#项目结构)
- [环境准备](#环境准备)
- [配置环境变量](#配置环境变量)
- [启动服务](#启动服务)
- [查看日志输出](#查看日志输出)
- [测试服务](#测试服务)
- [常见问题](#常见问题)

---

## 项目结构

```
fastapi_server/
├── main.py              # 主入口文件
├── config.py            # 配置管理
├── .env.example         # 环境变量示例
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 配置
├── middleware/          # 中间件
│   ├── __init__.py
│   └── auth.py
├── routes/              # 路由
│   ├── __init__.py
│   ├── chat.py
│   ├── sessions.py
│   ├── system.py
│   └── tools.py
├── models/              # 数据模型
│   ├── __init__.py
│   ├── request.py
│   └── response.py
└── services/            # 业务服务
    ├── __init__.py
    └── agent_service.py
```

---

## 环境准备

### 1. 检查 Python 版本

```bash
# 检查 Python 版本（需要 3.11+）
python --version
# 或
python3 --version
```

**要求：** Python 3.11 或更高版本

---

### 2. 创建虚拟环境

```bash
# 进入项目根目录
cd /home/meizu/Documents/my_agent_project/hermes-agent

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

**激活后提示符变化：**
```bash
# 激活前
(TraeAI-4) ~/Documents/my_agent_project/hermes-agent

# 激活后
(venv) (TraeAI-4) ~/Documents/my_agent_project/hermes-agent
```

---

### 3. 安装依赖

```bash
# 安装 FastAPI 服务依赖
pip install -r fastapi_server/requirements.txt

# 或者安装项目全部依赖
pip install -r requirements.txt
```

**主要依赖：**
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `pydantic-settings` - 配置管理
- `prometheus-client` - 监控指标
- `python-multipart` - 表单处理

---

## 配置环境变量

### 方式 1：复制并修改 .env 文件

```bash
# 复制示例文件
cp fastapi_server/.env.example fastapi_server/.env

# 编辑配置文件
vim fastapi_server/.env
# 或使用其他编辑器
```

### 最小化配置（开发环境）

```ini
# fastapi_server/.env

# ========== 服务基础配置 ==========
APP_NAME=Hermes-Agent API
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# ========== Agent 核心配置 ==========
DEFAULT_MODEL=dashscope/deepseek-v4-flash
MAX_ITERATIONS=90
TOOL_DELAY=1.0
SAVE_TRAJECTORIES=false

# 禁用的工具集
DISABLED_TOOLSETS=messaging,homeassistant,cron

# ========== 认证与安全 ==========
# 开发环境可以先不设置 API Key
API_KEYS=

# ========== CORS 配置 ==========
CORS_ORIGINS=*

# ========== 日志配置 ==========
LOG_LEVEL=INFO
LOG_FORMAT=text

# ========== 速率限制 ==========
RATE_LIMIT_ENABLED=false

# ========== 监控与指标 ==========
ENABLE_METRICS=true
PROMETHEUS_PORT=9090

# ========== LLM API Keys（必须配置至少一个） ==========
DASHSCOPE_API_KEY=sk-your-dashscope-api-key
# OPENROUTER_API_KEY=sk-or-your-openrouter-key
# OPENAI_API_KEY=sk-your-openai-key
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

---

### 方式 2：直接使用环境变量

```bash
# 设置环境变量（临时，当前终端有效）
export DASHSCOPE_API_KEY=sk-your-api-key
export DEBUG=true
export LOG_LEVEL=INFO

# 启动服务
python -m fastapi_server.main
```

---

### 方式 3：在命令中指定

```bash
# 在启动命令中直接设置环境变量
DASHSCOPE_API_KEY=sk-your-key DEBUG=true python -m fastapi_server.main
```

---

## 启动服务

### 方式 1：使用 main.py 启动（推荐）

```bash
# 确保在项目根目录
cd /home/meizu/Documents/my_agent_project/hermes-agent

# 启动服务
python -m fastapi_server.main
```

**启动日志输出：**
```
2024-01-01 12:00:00,000 [INFO] fastapi_server.main: ============================================================
2024-01-01 12:00:00,001 [INFO] fastapi_server.main: Hermes-Agent API 服务启动
2024-01-01 12:00:00,002 [INFO] fastapi_server.main: ============================================================
2024-01-01 12:00:00,003 [INFO] fastapi_server.main: 版本：1.0.0
2024-01-01 12:00:00,004 [INFO] fastapi_server.main: 调试模式：True
2024-01-01 12:00:00,005 [INFO] fastapi_server.main: 监听地址：0.0.0.0:8000
2024-01-01 12:00:00,006 [INFO] fastapi_server.main: ============================================================
2024-01-01 12:00:00,007 [INFO] fastapi_server.main: 默认模型：dashscope/deepseek-v4-flash
2024-01-01 12:00:00,008 [INFO] fastapi_server.main: 最大迭代次数：90
2024-01-01 12:00:00,009 [INFO] fastapi_server.main: 并发限制：10
2024-01-01 12:00:00,010 [INFO] fastapi_server.main: 速率限制：60 请求/分钟
2024-01-01 12:00:00,011 [INFO] fastapi_server.main: ============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### 方式 2：使用 uvicorn 直接启动

```bash
# 使用 uvicorn 命令启动
uvicorn fastapi_server.main:app --host 0.0.0.0 --port 8000 --reload
```

**参数说明：**
- `fastapi_server.main:app` - 应用路径（模块：变量）
- `--host 0.0.0.0` - 监听所有网络接口
- `--port 8000` - 端口号
- `--reload` - 开发模式，代码变更自动重启

---

### 方式 3：使用 web_server.py 启动

```bash
# 如果 web_server.py 是另一种启动方式
python fastapi_server/web_server.py
```

---

### 方式 4：后台运行（生产环境）

```bash
# 使用 nohup 后台运行
nohup python -m fastapi_server.main > api.log 2>&1 &

# 查看进程
ps aux | grep fastapi

# 查看日志
tail -f api.log

# 停止服务
kill <PID>
```

---

### 方式 5：使用 Docker 运行

```bash
# 构建镜像
cd fastapi_server
docker build -t hermes-agent .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -p 9090:9090 \
  -v $(pwd)/.env:/app/.env \
  --name hermes-agent \
  hermes-agent

# 查看日志
docker logs -f hermes-agent

# 停止容器
docker stop hermes-agent
```

---

## 查看日志输出

### 日志级别

FastAPI 使用 Python 标准日志模块，支持以下级别：

| 级别 | 说明 | 示例场景 |
|------|------|---------|
| `DEBUG` | 调试信息 | 详细的技术调试信息 |
| `INFO` | 一般信息 | 服务启动、请求处理 |
| `WARNING` | 警告信息 | 配置问题、性能警告 |
| `ERROR` | 错误信息 | 异常、失败 |
| `CRITICAL` | 严重错误 | 系统崩溃、无法恢复 |

---

### 日志格式配置

在 `.env` 文件中配置：

```ini
# 日志级别
LOG_LEVEL=INFO

# 日志格式（text 或 json）
LOG_FORMAT=text

# 日志文件（可选）
LOG_FILE=/var/log/hermes-agent/api.log
```

---

### 日志输出示例

#### 1. 服务启动日志

```
2024-01-01 12:00:00,000 [INFO] fastapi_server.main: ============================================================
2024-01-01 12:00:00,001 [INFO] fastapi_server.main: Hermes-Agent API 服务启动
2024-01-01 12:00:00,002 [INFO] fastapi_server.main: ============================================================
2024-01-01 12:00:00,003 [INFO] fastapi_server.main: 版本：1.0.0
2024-01-01 12:00:00,004 [INFO] fastapi_server.main: 调试模式：True
2024-01-01 12:00:00,005 [INFO] fastapi_server.main: 监听地址：0.0.0.0:8000
2024-01-01 12:00:00,006 [INFO] fastapi_server.main: ============================================================
2024-01-01 12:00:00,007 [INFO] fastapi_server.main: 默认模型：dashscope/deepseek-v4-flash
2024-01-01 12:00:00,008 [INFO] fastapi_server.main: 最大迭代次数：90
2024-01-01 12:00:00,009 [INFO] fastapi_server.main: 并发限制：10
2024-01-01 12:00:00,010 [INFO] fastapi_server.main: 速率限制：60 请求/分钟
2024-01-01 12:00:00,011 [INFO] fastapi_server.main: ============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**解读：**
- ✅ 服务版本：1.0.0
- ✅ 调试模式：开启（开发环境）
- ✅ 监听地址：0.0.0.0:8000（所有网卡）
- ✅ 默认模型：dashscope/deepseek-v4-flash
- ✅ 并发限制：10 个 Agent
- ✅ 速率限制：60 请求/分钟

---

#### 2. 请求处理日志

```
2024-01-01 12:05:30,123 [INFO] fastapi_server.middleware.logging: POST /api/v1/chat/completions - 200 OK - 1.234s
2024-01-01 12:05:31,456 [INFO] fastapi_server.middleware.logging: GET /api/v1/health - 200 OK - 0.005s
2024-01-01 12:05:32,789 [INFO] fastapi_server.middleware.logging: POST /api/v1/tools/execute - 201 Created - 0.567s
```

**解读：**
- 请求方法：POST/GET
- 请求路径：/api/v1/chat/completions
- 响应状态：200 OK
- 处理耗时：1.234 秒

---

#### 3. 错误日志

```
2024-01-01 12:10:15,123 [ERROR] fastapi_server.main: Unhandled exception: Connection timeout
Traceback (most recent call last):
  File "/path/to/fastapi_server/main.py", line 141, in general_exception_handler
    raise exc
  File "/path/to/fastapi_server/routes/chat.py", line 50, in chat_completions
    response = await agent.chat(message)
  File "/path/to/run_agent.py", line 100, in chat
    response = await call_llm_api(model, messages)
  File "/path/to/llm_client.py", line 75, in call_llm_api
    raise ConnectionTimeout("API server timeout")
ConnectionTimeout: Connection timeout
```

**解读：**
- 错误级别：ERROR
- 错误类型：Connection timeout
- 错误位置：chat.py 第 50 行
- 堆栈跟踪：完整的调用链

---

#### 4. 中间件日志

```
2024-01-01 12:15:20,123 [INFO] fastapi_server.middleware.auth: API Key 验证通过 - client: 192.168.1.100
2024-01-01 12:15:20,124 [INFO] fastapi_server.middleware.rate_limit: 速率限制检查通过 - 剩余：59/60
2024-01-01 12:15:20,125 [DEBUG] fastapi_server.middleware.logging: Request headers: Content-Type=application/json
```

**解读：**
- API Key 验证：通过
- 速率限制：剩余 59 次请求
- 请求头：Content-Type=application/json

---

#### 5. 服务关闭日志

```
2024-01-01 18:00:00,000 [INFO] fastapi_server.main: Hermes-Agent API 服务关闭
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [12345]
```

**解读：**
- 服务正常关闭
- 应用清理完成
- 服务器进程结束

---

### 实时查看日志

#### 方式 1：直接查看终端输出

启动服务后，日志会直接输出到终端。

---

#### 方式 2：重定向到文件

```bash
# 启动时重定向日志
python -m fastapi_server.main > api.log 2>&1

# 实时查看日志
tail -f api.log

# 查看最后 100 行
tail -n 100 api.log

# 查看特定时间段的日志
grep "2024-01-01 12:" api.log
```

---

#### 方式 3：使用 journalctl（systemd 管理）

如果使用 systemd 管理服务：

```bash
# 查看所有日志
journalctl -u hermes-agent

# 实时查看
journalctl -u hermes-agent -f

# 查看最近 100 行
journalctl -u hermes-agent -n 100

# 按时间过滤
journalctl -u hermes-agent --since "2024-01-01 12:00:00" --until "2024-01-01 13:00:00"
```

---

#### 方式 4：使用日志工具

```bash
# 使用 lnav（高级日志查看器）
lnav api.log

# 使用 multitail（多文件同时查看）
multitail api.log error.log
```

---

### 日志级别过滤

```bash
# 只查看 ERROR 级别
grep "\[ERROR\]" api.log

# 只查看 WARNING 及以上
grep -E "\[(ERROR|WARNING|CRITICAL)\]" api.log

# 排除 DEBUG 级别
grep -v "\[DEBUG\]" api.log
```

---

### 使用 Python 日志模块

在代码中添加自定义日志：

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    logger.info(f"收到聊天请求：{request.message}")
    
    try:
        response = await agent.chat(request.message)
        logger.info(f"处理成功，响应长度：{len(response)}")
        return {"message": response}
    except Exception as e:
        logger.error(f"处理失败：{e}", exc_info=True)
        raise
```

---

## 测试服务

### 1. 访问根路径

```bash
# 浏览器访问
http://localhost:8000/

# 或使用 curl
curl http://localhost:8000/
```

**预期响应：**
```json
{
  "name": "Hermes-Agent API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

**日志输出：**
```
2024-01-01 12:05:30,123 [INFO] fastapi_server.middleware.logging: GET / - 200 OK - 0.002s
```

---

### 2. 访问健康检查端点

```bash
curl http://localhost:8000/api/v1/health
```

**预期响应：**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:05:30"
}
```

**日志输出：**
```
2024-01-01 12:05:30,123 [INFO] fastapi_server.middleware.logging: GET /api/v1/health - 200 OK - 0.005s
```

---

### 3. 访问 API 文档

```bash
# Swagger UI
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc

# OpenAPI JSON
http://localhost:8000/openapi.json
```

---

### 4. 测试聊天接口

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，请介绍一下自己"
  }'
```

**预期响应：**
```json
{
  "message": "你好！我是 Hermes-Agent...",
  "model": "dashscope/deepseek-v4-flash",
  "timestamp": "2024-01-01T12:05:30"
}
```

**日志输出：**
```
2024-01-01 12:05:30,123 [INFO] fastapi_server.middleware.logging: POST /api/v1/chat/completions - 200 OK - 1.234s
2024-01-01 12:05:30,124 [INFO] fastapi_server.services.agent_service: Agent 响应生成完成，Token 使用：150
```

---

### 5. 查看 Prometheus 指标

```bash
# 访问指标端点
curl http://localhost:9090/metrics
```

**预期输出：**
```
# HELP hermes_requests_total Total number of requests
# TYPE hermes_requests_total counter
hermes_requests_total{endpoint="/api/v1/health",method="GET",status_code="200"} 5.0
hermes_requests_total{endpoint="/api/v1/chat/completions",method="POST",status_code="200"} 2.0

# HELP hermes_request_duration_seconds Request duration in seconds
# TYPE hermes_request_duration_seconds histogram
hermes_request_duration_seconds_bucket{endpoint="/api/v1/health",le="0.1"} 5.0
...
```

---

## 常见问题

### Q1: 启动失败 - 端口被占用

**错误信息：**
```
OSError: [Errno 98] error while attempting to bind on address ('0.0.0.0', 8000): address already in use
```

**解决方法：**

```bash
# 方法 1：查找并关闭占用端口的进程
lsof -i :8000
kill <PID>

# 方法 2：更换端口
export PORT=8001
python -m fastapi_server.main
```

---

### Q2: 启动失败 - 缺少 API Key

**错误信息：**
```
ValueError: No API key configured. Please set DASHSCOPE_API_KEY or other provider API keys.
```

**解决方法：**

```bash
# 设置 API Key（至少配置一个）
export DASHSCOPE_API_KEY=sk-your-api-key
# 或
export OPENAI_API_KEY=sk-your-api-key
# 或
export ANTHROPIC_API_KEY=sk-ant-your-api-key

# 重启服务
python -m fastapi_server.main
```

---

### Q3: 日志输出乱码

**问题：** 中文日志显示乱码

**解决方法：**

```bash
# 设置 Python 编码
export PYTHONIOENCODING=utf-8

# 或在启动命令中指定
PYTHONIOENCODING=utf-8 python -m fastapi_server.main
```

---

### Q4: 无法访问服务

**问题：** 浏览器无法访问 http://localhost:8000

**检查步骤：**

```bash
# 1. 检查服务是否运行
ps aux | grep fastapi

# 2. 检查端口监听
netstat -tlnp | grep 8000
# 或
ss -tlnp | grep 8000

# 3. 检查防火墙
sudo ufw status
sudo ufw allow 8000

# 4. 测试本地访问
curl http://localhost:8000/
```

---

### Q5: 日志文件过大

**问题：** 日志文件占用过多磁盘空间

**解决方法：**

```bash
# 方法 1：使用 logrotate 轮转
# /etc/logrotate.d/hermes-agent
/var/log/hermes-agent/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
}

# 方法 2：限制日志文件大小
# 在代码中配置
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler('api.log', maxBytes=10*1024*1024, backupCount=5)
```

---

### Q6: 生产环境如何配置日志？

**生产环境配置：**

```ini
# .env
DEBUG=false
LOG_LEVEL=WARNING  # 只记录警告和错误
LOG_FORMAT=json    # JSON 格式便于日志分析
LOG_FILE=/var/log/hermes-agent/api.log
```

**启动命令：**

```bash
# 使用 gunicorn（生产级 WSGI 服务器）
gunicorn fastapi_server.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/hermes-agent/access.log \
  --error-logfile /var/log/hermes-agent/error.log
```

---

## 监控与告警

### Prometheus 指标

```python
# 主要指标
hermes_requests_total          # 请求总数
hermes_request_duration_seconds # 请求延迟
hermes_agents_active           # 活跃 Agent 数
hermes_tool_calls_total        # 工具调用次数
hermes_tokens_total            # Token 使用量
```

### Grafana 仪表盘

访问 `http://localhost:3000`（需要部署 Grafana）

### 告警规则

```yaml
# alerts.yml
groups:
  - name: hermes-api
    rules:
      - alert: HighErrorRate
        expr: sum(rate(hermes_requests_total{status=~"5.."}[5m])) / sum(rate(hermes_requests_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "错误率超过 5%"
```

---

## 总结

### 启动步骤

1. ✅ 准备环境（Python 3.11+，虚拟环境）
2. ✅ 安装依赖（`pip install -r requirements.txt`）
3. ✅ 配置环境变量（`.env` 文件或环境变量）
4. ✅ 启动服务（`python -m fastapi_server.main`）
5. ✅ 查看日志（终端输出或日志文件）
6. ✅ 测试服务（curl 或浏览器访问）

### 日志级别

- `DEBUG` - 调试信息
- `INFO` - 一般信息
- `WARNING` - 警告
- `ERROR` - 错误
- `CRITICAL` - 严重错误

### 常用命令

```bash
# 启动服务
python -m fastapi_server.main

# 后台运行
nohup python -m fastapi_server.main > api.log 2>&1 &

# 查看日志
tail -f api.log

# 查看进程
ps aux | grep fastapi

# 停止服务
kill <PID>
```

### 监控指标

- 请求速率（RPS）
- 请求延迟（P50/P95/P99）
- 错误率
- Agent 活跃度
- Token 使用量

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**适用对象：** 开发者、运维人员  
**作者：** Hermes-Agent Team

# Hermes-Agent FastAPI 服务部署指南

## 📁 目录结构

```
fastapi_server/
├── __init__.py              # 包初始化
├── main.py                  # 主应用入口
├── config.py                # 配置管理
├── requirements.txt         # Python 依赖
├── Dockerfile              # Docker 镜像
├── .env.example            # 环境变量示例
├── middleware/             # 中间件
│   ├── __init__.py
│   └── auth.py             # 认证、限流、日志
├── models/                 # 数据模型
│   ├── __init__.py
│   ├── request.py          # 请求模型
│   └── response.py         # 响应模型
├── routes/                 # API 路由
│   ├── __init__.py
│   ├── chat.py             # 聊天端点
│   ├── sessions.py         # 会话管理
│   ├── tools.py            # 工具管理
│   └── system.py           # 系统端点
└── services/               # 业务服务
    ├── __init__.py
    └── agent_service.py    # Agent 服务
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入目录
cd fastapi_server

# 安装 Python 依赖
pip install -r requirements.txt

# 安装主项目（本地开发）
cd ..
pip install -e .
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
vim .env
```

**必需配置:**
- `API_KEYS`: API 密钥列表（用于认证）
- `DASHSCOPE_API_KEY` 或其他 LLM API Key

**推荐配置:**
- `CORS_ORIGINS`: 允许的跨域来源
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: 速率限制
- `LOG_LEVEL`: 日志级别

### 3. 启动服务

**开发模式:**
```bash
# 方式 1: 使用 uvicorn
uvicorn fastapi_server.main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 使用 Python
python -m fastapi_server.main
```

**生产模式:**
```bash
# 使用多 worker
uvicorn fastapi_server.main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用 gunicorn
gunicorn fastapi_server.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 4. 访问 API

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health
- **聊天端点**: POST http://localhost:8000/api/v1/chat/completions

## 📖 API 使用示例

### 聊天补全

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "帮我创建一个 Python 快速排序算法",
    "max_iterations": 50
  }'
```

### 流式响应

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "你好",
    "stream": true
  }'
```

### 获取会话列表

```bash
curl http://localhost:8000/api/v1/sessions \
  -H "X-API-Key: your-api-key"
```

### 列出所有工具

```bash
curl http://localhost:8000/api/v1/tools/list \
  -H "X-API-Key: your-api-key"
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -f fastapi_server/Dockerfile -t hermes-agent-api:latest .
```

### 运行容器

```bash
docker run -d \
  --name hermes-agent \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v ~/.hermes:/home/hermes/.hermes \
  hermes-agent-api:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: fastapi_server/Dockerfile
    ports:
    - "8000:8000"
    env_file:
    - fastapi_server/.env
    volumes:
    - ~/.hermes:/home/hermes/.hermes
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
    - "6379:6379"
    volumes:
    - redis_data:/data

volumes:
  redis_data:
```

## 🔧 生产环境配置

### 1. 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
    }
}
```

### 2. 使用 systemd 管理服务

```ini
# /etc/systemd/system/hermes-agent.service
[Unit]
Description=Hermes-Agent API Service
After=network.target

[Service]
Type=notify
User=hermes
WorkingDirectory=/opt/hermes-agent
Environment="PATH=/opt/hermes-agent/venv/bin"
ExecStart=/opt/hermes-agent/venv/bin/uvicorn fastapi_server.main:app --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. 配置日志轮转

```bash
# /etc/logrotate.d/hermes-agent
/var/log/hermes-agent/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 hermes hermes
}
```

## 📊 监控与告警

### Prometheus 配置

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'hermes-agent'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/metrics'
    scrape_interval: 15s
```

### Grafana 仪表板

导入 ID: `10956` (FastAPI 通用仪表板)

### 告警规则

```yaml
# alerts.yml
groups:
- name: hermes-agent
  rules:
  - alert: HighErrorRate
    expr: |
      sum(rate(hermes_requests_total{status_code=~"5.."}[5m])) 
      / sum(rate(hermes_requests_total[5m])) > 0.05
    for: 5m
    annotations:
      summary: "错误率超过 5%"
```

## 🔒 安全建议

1. **使用 HTTPS**: 生产环境必须使用 HTTPS
2. **限制 CORS**: 设置具体的允许来源
3. **启用速率限制**: 防止 DDoS 攻击
4. **定期更新密钥**: 定期更换 API Key 和 JWT 密钥
5. **监控异常**: 设置异常登录告警
6. **最小权限原则**: 使用非 root 用户运行服务

## 🧪 测试

### 单元测试

```bash
pytest tests/test_fastapi_server/
```

### 负载测试

```bash
# 使用 locust
locust -f tests/load_test.py --host http://localhost:8000
```

## 📝 故障排查

### 问题 1: 服务启动失败

```bash
# 检查日志
journalctl -u hermes-agent -f

# 检查端口占用
lsof -i :8000
```

### 问题 2: API Key 认证失败

```bash
# 检查 .env 配置
cat .env | grep API_KEYS

# 检查请求头
curl -v -H "X-API-Key: your-key" ...
```

### 问题 3: 数据库锁定

```bash
# 检查数据库文件权限
ls -l ~/.hermes/state.db

# 使用 PostgreSQL 替代 SQLite
# 设置 DATABASE_URL 环境变量
```

## 📚 参考文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Uvicorn 部署指南](https://www.uvicorn.org/deployment/)
- [Prometheus 监控](https://prometheus.io/docs/introduction/overview/)
- [Hermes-Agent 部署规范](./DEPLOYMENT_SPEC_CN.md)

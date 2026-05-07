# API_KEYS 配置指南 - FastAPI 服务认证详解

> 本文档详细介绍 Hermes-Agent FastAPI 服务的 API_KEYS 配置方案，包括开发环境和生产环境的完整配置步骤。

---

## 📋 目录

- [API_KEYS 作用](#api_keys 作用)
- [配置方案总览](#配置方案总览)
- [开发环境配置](#开发环境配置)
- [生产环境配置](#生产环境配置)
- [Android 客户端集成](#android 客户端集成)
- [API Key 生成工具](#api key 生成工具)
- [认证流程详解](#认证流程详解)
- [常见问题](#常见问题)

---

## API_KEYS 作用

### 什么是 API Key？

API Key 是一种简单的身份验证机制，用于：

1. **身份识别** - 识别请求来源
2. **访问控制** - 限制未授权访问
3. **使用追踪** - 统计 API 使用情况
4. **速率限制** - 防止滥用

### FastAPI 中的认证方式

Hermes-Agent FastAPI 服务支持两种认证方式：

| 认证方式 | Header 名称 | 格式 | 适用场景 |
|---------|------------|------|---------|
| **API Key** | `X-API-Key` | `your-api-key` | 服务间调用、移动端 |
| **JWT Token** | `Authorization` | `Bearer <token>` | 用户登录、Web 应用 |

---

## 配置方案总览

### 配置文件位置

```
fastapi_server/
├── .env              # 实际配置文件（需要手动创建）
├── .env.example      # 配置示例文件
├── config.py         # 配置加载代码
└── middleware/
    └── auth.py       # 认证中间件
```

### 配置优先级

```
环境变量 > .env 文件 > 默认值
```

### 两种配置场景

| 场景 | API_KEYS 配置 | 说明 |
|------|--------------|------|
| **开发环境** | 留空或不设置 | 允许任何 API Key（方便调试） |
| **生产环境** | 明确指定 Key 列表 | 只允许配置的 Key 访问 |

---

## 开发环境配置

### 步骤 1：创建 .env 文件

在项目根目录（`fastapi_server/`）创建 `.env` 文件：

```bash
cd /home/meizu/Documents/my_agent_project/hermes-agent/fastapi_server
cp .env.example .env
```

### 步骤 2：编辑配置文件

使用文本编辑器打开 `.env` 文件：

```bash
vim .env
# 或
code .env
# 或
nano .env
```

### 步骤 3：配置 API_KEYS（开发模式）

#### 方案 A：不设置 API Key（推荐用于本地开发）

```ini
# ========== 认证与安全 ==========
# 留空表示不启用 API Key 认证（开发模式）
API_KEYS=
```

**效果：** 任何 API Key 都能通过验证，方便调试。

#### 方案 B：设置单个测试 Key

```ini
# ========== 认证与安全 ==========
# 设置一个测试用的 API Key
API_KEYS=test-key-12345
```

**效果：** 只允许 `test-key-12345` 这个 Key 访问。

#### 方案 C：设置多个测试 Key

```ini
# ========== 认证与安全 ==========
# 逗号分隔多个 API Key
API_KEYS=test-key-1,test-key-2,test-key-3
```

**效果：** 允许列表中的任意 Key 访问。

### 步骤 4：配置其他开发环境参数

完整的开发环境 `.env` 配置：

```ini
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
DISABLED_TOOLSETS=messaging,homeassistant,cron

# ========== 认证与安全 ==========
# 开发模式：不设置 API Key
API_KEYS=

# ========== CORS 配置 ==========
CORS_ORIGINS=*
CORS_CREDENTIALS=True
CORS_METHODS=["*"]
CORS_HEADERS=["*"]

# ========== 日志配置 ==========
LOG_LEVEL=DEBUG
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

### 步骤 5：启动服务并测试

```bash
# 启动服务
python -m fastapi_server.main

# 在另一个终端测试 API
curl -H "X-API-Key: any-key" http://localhost:8000/api/v1/health
```

**预期响应：**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 123.45,
  "agents_active": 0,
  "sessions_count": 0,
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## 生产环境配置

### 步骤 1：生成安全的 API Key

#### 方法 A：使用 Python 生成

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**输出示例：**
```
xK7_9Hj2mN5pQ8rT3vW6yZ1aB4cD7eF0gI2jK5lM8nO
```

#### 方法 B：使用 OpenSSL 生成

```bash
openssl rand -base64 32
```

**输出示例：**
```
7kX9mN2pQ5rT8vW1yZ4aB6cD0eF3gH5jK8lM1nO4pR=
```

#### 方法 C：使用在线工具

访问：https://www.uuidgenerator.net/api-key

---

### 步骤 2：创建生产环境配置文件

```bash
# 创建生产环境配置文件
cp .env.example .env.production
```

### 步骤 3：配置生产环境参数

```ini
# ========== 服务基础配置 ==========
APP_NAME=Hermes-Agent API
APP_VERSION=1.0.0
DEBUG=false
HOST=0.0.0.0
PORT=8000

# ========== Agent 核心配置 ==========
DEFAULT_MODEL=dashscope/deepseek-v4-flash
MAX_ITERATIONS=90
TOOL_DELAY=1.0
SAVE_TRAJECTORIES=false
DISABLED_TOOLSETS=messaging,homeassistant,cron

# ========== 认证与安全 ==========
# 生产环境：必须设置 API Key
# 格式：逗号分隔的 Key 列表
API_KEYS=xK7_9Hj2mN5pQ8rT3vW6yZ1aB4cD7eF0gI2jK5lM8nO,another-secure-key-here

# 可选：自定义 API Key Header 名称
API_KEY_HEADER=X-API-Key

# 可选：JWT 配置（如果需要 JWT 认证）
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15

# ========== CORS 配置 ==========
# 生产环境必须指定具体域名
CORS_ORIGINS=["https://your-app.com", "https://app.your-domain.com"]
CORS_CREDENTIALS=True
CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS=["Content-Type", "Authorization", "X-API-Key"]

# ========== 日志配置 ==========
LOG_LEVEL=WARNING
LOG_FORMAT=json
LOG_FILE=/var/log/hermes-agent/api.log

# ========== 速率限制 ==========
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# ========== 监控与指标 ==========
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
SENTRY_DSN=https://your-sentry-dsn

# ========== LLM API Keys（必须配置） ==========
DASHSCOPE_API_KEY=sk-your-production-dashscope-key
```

### 步骤 4：设置文件权限（重要！）

```bash
# 设置 .env 文件权限为只读（所有者）
chmod 600 .env.production

# 验证权限
ls -l .env.production
# 输出：-rw------- 1 user user 1234 Jan 1 12:00 .env.production
```

**权限说明：**
- `600` = 只有所有者可以读写
- 防止其他用户读取敏感信息

---

### 步骤 5：部署时加载配置

#### 方式 A：使用环境变量

```bash
# 启动服务时指定环境变量
ENV_FILE=.env.production python -m fastapi_server.main
```

#### 方式 B：使用 Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 复制生产环境配置文件
COPY .env.production /app/.env

EXPOSE 8000

CMD ["python", "-m", "fastapi_server.main"]
```

#### 方式 C：使用 systemd（Linux 服务）

创建服务文件 `/etc/systemd/system/hermes-agent.service`：

```ini
[Unit]
Description=Hermes-Agent FastAPI Service
After=network.target

[Service]
Type=simple
User=hermes
WorkingDirectory=/opt/hermes-agent/fastapi_server
Environment="ENV_FILE=/opt/hermes-agent/.env.production"
ExecStart=/usr/bin/python3 -m fastapi_server.main
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start hermes-agent
sudo systemctl enable hermes-agent
```

---

### 步骤 6：测试生产环境认证

```bash
# 正确的 API Key
curl -H "X-API-Key: xK7_9Hj2mN5pQ8rT3vW6yZ1aB4cD7eF0gI2jK5lM8nO" \
     http://your-server.com:8000/api/v1/health

# 错误的 API Key（应该返回 401）
curl -H "X-API-Key: wrong-key" \
     http://your-server.com:8000/api/v1/health
```

**预期响应（错误 Key）：**
```json
{
  "detail": "无效的 API Key"
}
```

---

## Android 客户端集成

### 步骤 1：配置 Retrofit 添加 API Key

在 `NetworkModule.kt` 中添加认证拦截器：

```kotlin
package com.hermes.agent.di

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Singleton
fun provideOkHttpClient(): OkHttpClient {
    val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    // API Key 认证拦截器
    val authInterceptor = Interceptor { chain ->
        val original = chain.request()
        val request = original.newBuilder()
            .header("X-API-Key", "your-api-key-here")  // 替换为实际 Key
            .method(original.method, original.body())
            .build()
        chain.proceed(request)
    }

    return OkHttpClient.Builder()
        .addInterceptor(authInterceptor)      // 添加认证拦截器
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
}
```

### 步骤 2：从配置读取 API Key

**推荐做法：** 从 `BuildConfig` 或配置文件读取，不要硬编码。

#### 方式 A：使用 BuildConfig

在 `build.gradle.kts` 中添加：

```kotlin
android {
    defaultConfig {
        buildConfigField("String", "HERMES_API_KEY", "\"your-api-key-here\"")
    }
}
```

在代码中使用：

```kotlin
val authInterceptor = Interceptor { chain ->
    val original = chain.request()
    val request = original.newBuilder()
        .header("X-API-Key", BuildConfig.HERMES_API_KEY)
        .build()
    chain.proceed(request)
}
```

#### 方式 B：从本地配置文件读取

创建 `local.properties`（不提交到 Git）：

```properties
hermes.api.key=your-api-key-here
```

在代码中读取：

```kotlin
val properties = Properties()
properties.load(FileInputStream(rootProject.file("local.properties")))
val apiKey = properties.getProperty("hermes.api.key")

val authInterceptor = Interceptor { chain ->
    val request = chain.request().newBuilder()
        .header("X-API-Key", apiKey)
        .build()
    chain.proceed(request)
}
```

### 步骤 3：测试 Android 客户端

```kotlin
// 在 Application 或 MainActivity 中测试连接
class HermesApplication : Application() {
    @Inject lateinit var apiService: HermesApiService
    
    override fun onCreate() {
        super.onCreate()
        testConnection()
    }
    
    private fun testConnection() {
        lifecycleScope.launch {
            try {
                val response = apiService.healthCheck()
                Log.d("HermesApp", "连接成功：${response.status}")
            } catch (e: Exception) {
                Log.e("HermesApp", "连接失败：${e.message}")
            }
        }
    }
}
```

---

## API Key 生成工具

### 工具 1：Python 脚本

创建 `generate_api_key.py`：

```python
#!/usr/bin/env python3
"""
API Key 生成工具
"""

import secrets
import hashlib
import argparse

def generate_api_key(length=32, prefix="hermes"):
    """生成 API Key"""
    # 生成随机字节
    random_bytes = secrets.token_bytes(length)
    
    # 生成 Base64 编码
    import base64
    key = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
    
    # 添加前缀
    return f"{prefix}-{key}"

def generate_multiple_keys(count=5, length=32):
    """生成多个 API Key"""
    keys = []
    for i in range(count):
        key = generate_api_key(length)
        keys.append(key)
        print(f"Key {i+1}: {key}")
    return keys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 API Key")
    parser.add_argument("-n", "--count", type=int, default=1, help="生成数量")
    parser.add_argument("-l", "--length", type=int, default=32, help="Key 长度")
    parser.add_argument("-p", "--prefix", type=str, default="hermes", help="Key 前缀")
    
    args = parser.parse_args()
    
    print(f"生成 {args.count} 个 API Key：\n")
    generate_multiple_keys(args.count, args.length)
```

使用：
```bash
python generate_api_key.py -n 3 -l 32
```

**输出：**
```
生成 3 个 API Key：

Key 1: hermes-xK7_9Hj2mN5pQ8rT3vW6yZ1aB4cD7eF0gI2jK5lM8nO
Key 2: hermes-pQ5rT8vW1yZ4aB6cD0eF3gH5jK8lM1nO4pR7sU
Key 3: hermes-vW1yZ4aB6cD0eF3gH5jK8lM1nO4pR7sU0vX3z
```

### 工具 2：在线生成器

推荐网站：
- https://www.uuidgenerator.net/api-key
- https://randomkeygen.com/
- https://passwordsgenerator.net/

---

## 认证流程详解

### 认证中间件工作流程

```
请求进入
    ↓
检查是否在白名单端点（/health, /docs 等）
    ↓ 是
跳过认证，直接处理
    ↓ 否
检查 X-API-Key Header
    ↓ 存在
验证 API Key 是否在允许列表中
    ↓ 验证通过
设置 request.state.authenticated = True
继续处理请求
    ↓ 验证失败
返回 401 Unauthorized
    ↓ 不存在
检查 Authorization: Bearer Token
    ↓ 存在
验证 JWT Token
    ↓ 验证通过
继续处理请求
    ↓ 验证失败
返回 401 Unauthorized
    ↓ 不存在
返回 401 Unauthorized
```

### 认证代码实现

`fastapi_server/middleware/auth.py`：

```python
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查和文档端点
        if request.url.path in ["/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # 尝试 API Key 认证
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if self._validate_api_key(api_key):
                request.state.authenticated = True
                request.state.api_key = api_key
                return await call_next(request)
            else:
                raise HTTPException(
                    status_code=401,
                    detail="无效的 API Key"
                )
        
        # 未提供认证凭据
        raise HTTPException(
            status_code=401,
            detail="未提供认证凭据"
        )
    
    def _validate_api_key(self, api_key: str) -> bool:
        """验证 API Key"""
        if not settings.api_keys:
            # 未配置 API Key 时，允许任何 Key（开发模式）
            return True
        return api_key in settings.api_keys
```

---

## 常见问题

### Q1: 忘记 API Key 怎么办？

**A:** 重新生成并更新配置：

```bash
# 1. 生成新 Key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. 更新 .env 文件
vim .env

# 3. 重启服务
sudo systemctl restart hermes-agent
```

---

### Q2: 如何撤销某个 API Key？

**A:** 从配置中移除该 Key：

```ini
# 原配置
API_KEYS=key1,key2,key3

# 撤销 key2
API_KEYS=key1,key3
```

重启服务生效。

---

### Q3: API Key 应该多长？

**A:** 推荐 32-64 字符：

- **开发环境**: 16-32 字符（方便输入）
- **生产环境**: 32-64 字符（更安全）

---

### Q4: 可以动态添加 API Key 吗？

**A:** 需要重启服务才能生效。如果支持动态添加，需要修改代码：

```python
# config.py
class Settings(BaseSettings):
    api_keys: List[str] = []
    
    def add_api_key(self, key: str):
        """动态添加 API Key"""
        if key not in self.api_keys:
            self.api_keys.append(key)
            self.api_keys = self.api_keys  # 触发更新

# 在 API 中添加
@app.post("/admin/api-keys")
async def add_api_key(key: str):
    settings.add_api_key(key)
    return {"message": "API Key 已添加"}
```

---

### Q5: 如何限制 API Key 的权限？

**A:** 实现基于 API Key 的权限控制：

```python
# 扩展配置
API_KEY_PERMISSIONS = {
    "key1": ["read"],
    "key2": ["read", "write"],
    "key3": ["read", "write", "admin"],
}

# 在中间件中检查权限
def check_permission(api_key: str, required_permission: str) -> bool:
    permissions = API_KEY_PERMISSIONS.get(api_key, [])
    return required_permission in permissions
```

---

### Q6: 如何统计 API Key 的使用情况？

**A:** 添加使用日志：

```python
# middleware/auth.py
async def dispatch(self, request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    
    # 记录 API Key 使用
    if api_key:
        logger.info(f"API Key 使用：{api_key[:8]}... - {request.method} {request.url.path}")
    
    return await call_next(request)
```

或使用 Prometheus 指标：
```python
API_KEY_USAGE = Counter(
    "api_key_usage_total",
    "Total API key usage",
    ["api_key_prefix"]
)

# 在认证通过后记录
API_KEY_USAGE.labels(api_key_prefix=api_key[:8]).inc()
```

---

## 配置示例总结

### 开发环境（最简单）

```ini
# .env
DEBUG=true
API_KEYS=
LOG_LEVEL=DEBUG
```

### 生产环境（推荐）

```ini
# .env.production
DEBUG=false
API_KEYS=secure-key-1,secure-key-2
CORS_ORIGINS=["https://your-app.com"]
LOG_LEVEL=WARNING
RATE_LIMIT_ENABLED=true
```

### Android 客户端配置

```kotlin
// NetworkModule.kt
val authInterceptor = Interceptor { chain ->
    val request = chain.request().newBuilder()
        .header("X-API-Key", BuildConfig.HERMES_API_KEY)
        .build()
    chain.proceed(request)
}
```

---

## 安全检查清单

在部署前，请确认：

- [ ] API Key 已生成且足够安全（32+ 字符）
- [ ] .env 文件权限设置为 600
- [ ] .env 文件未提交到 Git
- [ ] 生产环境已禁用 DEBUG
- [ ] CORS 已配置具体域名
- [ ] 速率限制已启用
- [ ] 日志级别设置为 WARNING 或 ERROR
- [ ] 已备份 API Key 到安全位置
- [ ] Android 客户端已正确配置 API Key
- [ ] 已测试认证流程（正确和错误 Key）

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**适用对象：** 开发者、运维人员  
**作者：** Hermes-Agent Team

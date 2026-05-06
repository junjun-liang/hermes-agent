# CORS 跨域资源共享配置指南

> **CORS** = **Cross-Origin Resource Sharing**（跨域资源共享）
> 
> 这是浏览器的一种安全机制，限制网页从一个来源（域名）访问另一个来源的资源。

---

## 📋 目录

- [CORS 配置项说明](#cors-配置项说明)
- [实际场景示例](#实际场景示例)
- [安全建议](#安全建议)
- [测试 CORS](#测试-cors)
- [配置对比表](#配置对比表)
- [总结](#总结)

---

## CORS 配置项说明

### 1. `cors_origins: List[str] = ["*"]`

**作用：** 允许哪些来源（域名）访问 API

```python
# 开发环境（允许所有）
cors_origins = ["*"]

# 生产环境（指定具体域名）
cors_origins = [
    "https://your-app.com",
    "https://www.your-app.com",
    "https://admin.your-app.com",
]

# 支持通配符子域名
cors_origins = [
    "https://*.your-app.com",  # 所有子域名
]
```

**⚠️ 安全警告：**
- `["*"]` 表示允许**任何网站**访问你的 API
- 生产环境**必须**设置具体域名，否则会有安全风险

---

### 2. `cors_credentials: bool = True`

**作用：** 是否允许携带认证信息（Cookie、Authorization Header 等）

```python
# True: 允许携带认证信息
# 客户端可以设置：
fetch('https://api.example.com', {
    credentials: 'include',  // 发送 Cookie
    headers: {
        'Authorization': 'Bearer token123'  // 发送 Token
    }
})

# False: 不允许携带认证信息
# 浏览器会拒绝发送 Cookie 和认证头
```

**⚠️ 注意：**
- 当 `cors_credentials = True` 时，`cors_origins` **不能**设置为 `["*"]`
- 必须指定具体域名，否则浏览器会报错

---

### 3. `cors_methods: List[str] = ["*"]`

**作用：** 允许哪些 HTTP 方法

```python
# 允许所有方法
cors_methods = ["*"]

# 指定具体方法
cors_methods = [
    "GET",      // 查询数据
    "POST",     // 创建数据
    "PUT",      // 更新数据
    "DELETE",   // 删除数据
    "OPTIONS",  // 预检请求（必需）
]
```

**常用方法：**
- `GET` - 获取资源
- `POST` - 创建资源
- `PUT/PATCH` - 更新资源
- `DELETE` - 删除资源
- `OPTIONS` - 预检请求（浏览器自动发送）

---

### 4. `cors_headers: List[str] = ["*"]`

**作用：** 允许客户端发送哪些自定义请求头

```python
# 允许所有头
cors_headers = ["*"]

# 指定具体头
cors_headers = [
    "Content-Type",        // 内容类型
    "Authorization",       // 认证 Token
    "X-API-Key",          // API Key
    "X-Request-ID",       // 请求 ID
    "User-Agent",         // 用户代理
]
```

**常见自定义头：**
- `Authorization` - JWT Token
- `X-API-Key` - API 密钥
- `X-Request-ID` - 请求追踪
- `Content-Type` - 内容类型（如 `application/json`）

---

## 实际场景示例

### 场景 1：开发环境

```python
# .env
CORS_ORIGINS=["*"]
CORS_CREDENTIALS=false
CORS_METHODS=["*"]
CORS_HEADERS=["*"]
```

**特点：** 宽松配置，方便开发调试

---

### 场景 2：生产环境（Web + Android）

```python
# .env
CORS_ORIGINS=[
    "https://app.example.com",      # Web 应用
    "https://admin.example.com",    # 管理后台
]
CORS_CREDENTIALS=true
CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS=["Content-Type", "Authorization", "X-API-Key"]
```

**特点：** 严格限制，只允许特定域名和方法

---

### 场景 3：仅 API 调用（无浏览器）

```python
# 如果是纯 API 服务（Android App、iOS App 直接调用）
# 可以禁用 CORS，因为移动应用不受 CORS 限制
CORS_ORIGINS=["*"]  # 不影响安全性
```

**原因：** CORS 是**浏览器**的安全机制，移动应用不受此限制

---

## 安全建议

### ❌ 不安全的配置

```python
# 生产环境这样做很危险！
cors_origins = ["*"]
cors_credentials = True  # 任何网站都可以获取用户认证信息
```

**风险：**
- 恶意网站可以访问你的 API
- 可能泄露用户数据
- CSRF 攻击风险

---

### ✅ 安全的配置

```python
# 生产环境应该这样
cors_origins = [
    "https://app.example.com",
    "https://www.example.com",
]
cors_credentials = True
cors_methods = ["GET", "POST", "OPTIONS"]  # 最小权限原则
cors_headers = ["Content-Type", "Authorization"]  # 只允许必要的头
```

---

## 测试 CORS

### 使用 curl 测试

```bash
# 测试 CORS 预检请求
curl -X OPTIONS http://localhost:8000/api/v1/chat/completions \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization" \
  -v

# 查看响应头
# Access-Control-Allow-Origin: https://app.example.com
# Access-Control-Allow-Credentials: true
# Access-Control-Allow-Methods: GET, POST, OPTIONS
# Access-Control-Allow-Headers: Content-Type, Authorization
```

### 浏览器测试

```javascript
// 在浏览器控制台测试
fetch('http://localhost:8000/api/v1/health', {
    method: 'GET',
    headers: {
        'Authorization': 'Bearer token123'
    }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('CORS Error:', error));
```

---

## 配置对比表

| 配置项 | 开发环境 | 生产环境 | 说明 |
|--------|---------|---------|------|
| `cors_origins` | `["*"]` | `["https://app.com"]` | 生产必须指定域名 |
| `cors_credentials` | `false` | `true` | 需要认证时设为 true |
| `cors_methods` | `["*"]` | `["GET","POST"]` | 最小权限原则 |
| `cors_headers` | `["*"]` | `["Authorization"]` | 只允许必要的头 |

---

## 总结

### CORS 配置的核心原则

1. **开发环境**：宽松配置，方便调试
2. **生产环境**：严格限制，最小权限
3. **认证信息**：`cors_credentials = true` 时必须指定具体域名
4. **移动应用**：不受 CORS 限制，可以宽松配置

### 在 FastAPI 中的应用

在 Hermes-Agent FastAPI 服务中，CORS 配置通过中间件自动应用到所有响应上：

```python
# fastapi_server/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)
```

确保跨域请求得到正确处理，同时保护 API 安全。

---

## 相关资源

- [MDN - CORS](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)
- [FastAPI CORS 文档](https://fastapi.tiangolo.com/tutorial/cors/)
- [W3C CORS 规范](https://www.w3.org/TR/cors/)

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**所属项目：** Hermes-Agent FastAPI 服务

# API 速率限制配置指南

> **速率限制（Rate Limiting）** 是一种保护 API 服务的技术，防止单个用户过度使用资源或遭受 DDoS 攻击。

---

## 📋 目录

- [配置项说明](#配置项说明)
- [实现原理](#实现原理)
- [实际应用场景](#实际应用场景)
- [测试方法](#测试方法)
- [环境配置建议](#环境配置建议)
- [注意事项](#注意事项)
- [总结](#总结)

---

## 配置项说明

### 1. `rate_limit_enabled: bool = True`

**作用：** 是否启用速率限制

```python
# True: 启用速率限制（生产环境推荐）
rate_limit_enabled = True

# False: 禁用速率限制（仅开发环境）
rate_limit_enabled = False
```

**使用场景：**
- ✅ **生产环境**：必须启用，防止滥用
- ⚠️ **开发环境**：可以禁用，方便测试

---

### 2. `rate_limit_requests_per_minute: int = 60`

**作用：** 每分钟允许的最大请求数

```python
# 每分钟最多 60 个请求 = 每秒 1 个请求
rate_limit_requests_per_minute = 60

# 更严格的限制（免费层）
rate_limit_requests_per_minute = 20

# 更宽松的限制（付费层）
rate_limit_requests_per_minute = 300
```

**计算示例：**
- `60` 请求/分钟 = `1` 请求/秒
- `120` 请求/分钟 = `2` 请求/秒
- `300` 请求/分钟 = `5` 请求/秒

---

### 3. `rate_limit_redis_url: Optional[str] = None`

**作用：** Redis 连接 URL（用于分布式速率限制）

```python
# 本地 Redis
rate_limit_redis_url = "redis://localhost:6379/0"

# 远程 Redis（带密码）
rate_limit_redis_url = "redis://:password@redis.example.com:6379/1"

# None: 使用内存存储（单机模式）
rate_limit_redis_url = None
```

**为什么需要 Redis？**

| 存储方式 | 优点 | 缺点 | 适用场景 |
|---------|------|------|---------|
| **内存**（None） | 简单、快速 | 重启丢失、多实例不共享 | 开发/单机测试 |
| **Redis** | 持久化、共享 | 需要额外服务 | 生产/分布式部署 |

---

## 实现原理

### 滑动窗口算法

Hermes-Agent 使用的是**滑动窗口**算法：

```python
# middleware/auth.py 中的实现逻辑

# 1. 获取当前时间和窗口起始时间
current_time = time.time()
window_start = current_time - 60  # 1 分钟窗口

# 2. 清理过期记录（删除 1 分钟前的请求）
self.requests[client_ip] = [
    ts for ts in self.requests[client_ip]
    if ts > window_start
]

# 3. 检查是否超限
if len(self.requests[client_ip]) >= rate_limit_requests_per_minute:
    # 拒绝请求
    raise HTTPException(status_code=429, detail="请求速率超限")

# 4. 记录当前请求
self.requests[client_ip].append(current_time)
```

### 算法图示

```
时间轴：|--[旧请求]--[窗口起点]----[当前请求]-->|
              ↓           ↓            ↓
           已清理     60 秒窗口      新请求

窗口内请求数：3 个
限制：60 个/分钟
结果：✅ 允许通过
```

---

## 实际应用场景

### 场景 1：免费层用户

```python
RATE_LIMITS = {
    "free": {
        "requests_per_minute": 20,
        "tokens_per_day": 50000
    }
}
```

**效果：**
- 用户 A 在 1 分钟内发送了 20 个请求
- 第 21 个请求会被拒绝，返回 `429 Too Many Requests`
- 1 分钟后，窗口滑动，旧请求被清理，可以重新发送

---

### 场景 2：付费层用户

```python
RATE_LIMITS = {
    "pro": {
        "requests_per_minute": 300,
        "tokens_per_day": 500000
    }
}
```

**效果：**
- 付费用户可以发送更多请求
- 适合高频使用的企业客户

---

### 场景 3：分布式部署

```python
# 使用 Redis 共享速率限制数据
rate_limit_enabled = True
rate_limit_requests_per_minute = 60
rate_limit_redis_url = "redis://redis-cluster:6379/0"
```

**为什么需要 Redis？**

```
用户请求 → 负载均衡器
              ↓
        ┌─────┼─────┐
        ↓     ↓     ↓
     Server1 Server2 Server3
        ↓     ↓     ↓
     Redis (共享请求计数)
```

**没有 Redis 的问题：**
- 用户在 Server1 发送了 50 个请求
- 然后请求被路由到 Server2
- Server2 不知道 Server1 的计数，又允许 60 个请求
- **结果：限制失效！**

**有 Redis 的解决方案：**
- 所有服务器共享 Redis 中的计数
- 无论请求路由到哪台服务器，限制都一致

---

## 测试方法

### 使用 curl 测试

```bash
# 快速发送 65 个请求（超过 60 的限制）
for i in {1..65}; do
    echo "请求 $i:"
    curl -s -w "HTTP 状态码：%{http_code}\n" \
      -X GET http://localhost:8000/api/v1/health \
      -H "X-API-Key: test-key" \
      -o /dev/null
done
```

**预期输出：**
```
请求 1-60: HTTP 状态码：200
请求 61-65: HTTP 状态码：429  ← 被限制
```

---

### 查看响应头

当触发速率限制时，响应头会包含相关信息：

```bash
curl -v http://localhost:8000/api/v1/health
```

**响应头：**
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 60          # 限制：60 请求/分钟
X-RateLimit-Remaining: 0       # 剩余：0
X-RateLimit-Reset: 1234567890  # 重置时间戳
Retry-After: 60                # 建议等待时间（秒）
```

---

### 响应示例

**429 响应体：**
```json
{
  "error": "请求速率超限，请 1 分钟后重试",
  "request_id": "req_abc123",
  "timestamp": 1234567890
}
```

---

## 环境配置建议

### 开发环境

```bash
# .env.development
RATE_LIMIT_ENABLED=false           # 禁用，方便调试
RATE_LIMIT_REQUESTS_PER_MINUTE=1000  # 宽松限制
```

**说明：** 开发时频繁请求 API，禁用或放宽限制可以提高效率。

---

### 测试环境

```bash
# .env.testing
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100  # 中等限制
RATE_LIMIT_REDIS_URL=redis://localhost:6379/0
```

**说明：** 模拟生产环境，但限制相对宽松。

---

### 生产环境

```bash
# .env.production
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60   # 严格限制
RATE_LIMIT_REDIS_URL=redis://redis-cluster:6379/0  # 使用 Redis 集群
```

**说明：** 严格保护 API，防止滥用和攻击。

---

## 分层速率限制示例

根据用户等级设置不同的限制：

```python
# middleware/auth.py

RATE_LIMITS = {
    "free": {
        "requests_per_minute": 20,
        "tokens_per_day": 50000,
        "max_concurrent_requests": 1
    },
    "pro": {
        "requests_per_minute": 100,
        "tokens_per_day": 500000,
        "max_concurrent_requests": 5
    },
    "enterprise": {
        "requests_per_minute": 500,
        "tokens_per_day": 10000000,
        "max_concurrent_requests": 20
    }
}

async def get_rate_limit(user_tier: str) -> dict:
    """根据用户等级获取速率限制"""
    return RATE_LIMITS.get(user_tier, RATE_LIMITS["free"])
```

---

## 注意事项

### ⚠️ 1. 内存泄漏风险

如果不使用 Redis，内存中的请求记录会无限增长：

```python
# ❌ 问题：没有清理过期数据
self.requests[client_ip].append(current_time)

# ✅ 解决方案：定期清理
self.requests[client_ip] = [
    ts for ts in self.requests[client_ip]
    if ts > window_start
]
```

**最佳实践：** 设置合理的 TTL（Time To Live），定期清理过期数据。

---

### ⚠️ 2. 多实例同步问题

```
用户 → Server1 (计数：50)
     → Server2 (计数：0)  ← 不同步！
```

**问题：** 在多服务器部署中，每台服务器的内存计数不同步。

**解决方案：** 使用 Redis 集中存储所有实例的计数。

---

### ⚠️ 3. 误伤正常用户

```
正常用户：每秒 1-2 个请求 → ✅ 通过
爬虫用户：每秒 100 个请求 → ❌ 被限制
```

**优化方案：**
- 使用更大的时间窗口（如 1 小时）
- 结合 IP 和用户 ID 双重限制
- 实现白名单机制
- 使用令牌桶算法（Token Bucket）

---

### ⚠️ 4. Redis 故障处理

```python
# 容错处理示例
try:
    redis.ping()
except redis.ConnectionError:
    # Redis 不可用，降级到内存存储或禁用限制
    logger.warning("Redis 不可用，降级速率限制")
    rate_limit_enabled = False
```

**最佳实践：** 实现降级策略，Redis 故障时不影响核心服务。

---

## 配置对比表

| 配置项 | 开发环境 | 测试环境 | 生产环境 | 说明 |
|--------|---------|---------|---------|------|
| `rate_limit_enabled` | `false` | `true` | `true` | 生产必须启用 |
| `requests_per_minute` | `1000` | `100` | `60` | 根据环境调整 |
| `redis_url` | `None` | `localhost` | `redis-cluster` | 生产用集群 |
| `max_concurrent` | `100` | `10` | `5` | 最大并发请求数 |

---

## 高级技巧

### 1. 动态调整限制

```python
# 根据时间段调整限制
def get_dynamic_limit(hour: int) -> int:
    if 2 <= hour <= 6:  # 凌晨时段
        return 1000  # 宽松
    else:
        return 60    # 正常
```

### 2. IP 白名单

```python
# 跳过白名单 IP 的速率限制
WHITELIST_IPS = ["192.168.1.1", "10.0.0.1"]

if client_ip in WHITELIST_IPS:
    return await call_next(request)  # 直接放行
```

### 3. 基于 Token 的限制

```python
# 不仅限制请求数，还限制 Token 消耗
TOKEN_LIMITS = {
    "free": {"tokens_per_day": 50000},
    "pro": {"tokens_per_day": 500000},
}

async def check_token_limit(user_id: str, tokens_used: int):
    # 检查用户当日 Token 使用量
    pass
```

---

## 总结

### 核心要点

1. **生产环境必须启用**：防止滥用和 DDoS 攻击
2. **使用 Redis 实现分布式**：多实例共享限制数据
3. **分层限制**：根据用户等级设置不同限制
4. **监控和告警**：及时发现异常流量

### 最佳实践

- ✅ 开发环境禁用或放宽限制
- ✅ 测试环境模拟生产配置
- ✅ 生产环境使用 Redis 集群
- ✅ 实现降级策略（Redis 故障时）
- ✅ 设置合理的限制值（不过严也不过松）
- ✅ 监控速率限制触发情况

### 相关资源

- [Redis 官方文档](https://redis.io/)
- [滑动窗口算法](https://en.wikipedia.org/wiki/Sliding_window_protocol)
- [DDoS 防护](https://www.cloudflare.com/learning/ddos/ddos-prevention/)

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**所属项目：** Hermes-Agent FastAPI 服务  
**作者：** Hermes-Agent Team

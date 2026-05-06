# API 资源限制配置指南

> **资源限制（Resource Limits）** 用于保护服务器免受过载影响，确保服务稳定性和公平性。

---

## 📋 目录

- [配置项详解](#配置项详解)
- [为什么需要资源限制](#为什么需要资源限制)
- [实际应用场景](#实际应用场景)
- [配置建议](#配置建议)
- [监控与告警](#监控与告警)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

---

## 配置项详解

### 1. `max_concurrent_agents: int = 10`

**作用：** 限制同时运行的 Agent 实例数量

```python
# 最多允许 10 个 Agent 同时处理请求
max_concurrent_agents = 10
```

**详细说明：**
- 每个聊天请求会创建一个 Agent 实例
- Agent 实例会占用内存、CPU 和 LLM API 连接
- 超出限制的新请求会被拒绝，返回 `503 Service Unavailable`

**资源消耗估算（单个 Agent）：**
```
内存：~50-100 MB
CPU: ~10-20% (单核)
LLM API 连接：1-3 个
```

**10 个并发 Agent 的总消耗：**
```
内存：~500MB - 1GB
CPU: ~1-2 核
LLM API 连接：10-30 个
```

---

### 2. `max_request_timeout: int = 300`

**作用：** 单个请求的最大处理时间（秒）

```python
# 请求必须在 5 分钟内完成，否则被强制终止
max_request_timeout = 300  # 300 秒 = 5 分钟
```

**详细说明：**
- 防止长时间运行的请求占用资源
- 避免 LLM API 响应慢导致服务阻塞
- 超时请求会被强制终止，返回 `504 Gateway Timeout`

**时间分配示例：**
```
LLM API 调用：~2-10 秒
工具执行：~1-30 秒（每个工具）
最大迭代次数：50 次
总耗时：通常 10-60 秒，复杂任务可能达到 2-3 分钟
```

---

### 3. `max_request_size: int = 10 * 1024 * 1024`

**作用：** 单个请求的最大字节数

```python
# 请求体不能超过 10MB
max_request_size = 10 * 1024 * 1024  # 10MB
```

**详细说明：**
- 限制请求体大小，防止大请求耗尽内存
- 包括消息内容、文件、图片等所有数据
- 超出限制返回 `413 Payload Too Large`

**10MB 能容纳多少内容？**
```
纯文本：~500 万 - 1000 万个汉字
代码：~20 万 - 50 万行
图片（压缩后）：~10-50 张
文档：~100-500 页 PDF
```

---

## 为什么需要资源限制

### ❌ 没有限制的风险

#### 风险 1：资源耗尽

```
场景：100 个并发请求同时到达
结果：
- 内存耗尽 → OOM Killer 杀死进程
- CPU 满载 → 其他服务受影响
- LLM API 连接池耗尽 → 所有请求失败
```

#### 风险 2：慢请求阻塞

```
场景：某个请求处理了 30 分钟还在运行
结果：
- 占用 Agent 实例不释放
- 后续请求排队等待
- 整体响应时间变慢
```

#### 风险 3：大请求攻击

```
场景：恶意用户发送 1GB 的请求
结果：
- 内存瞬间爆满
- 服务崩溃
- 可能影响同一服务器上的其他服务
```

---

### ✅ 有限制的好处

#### 好处 1：公平性

```
每个用户都能获得服务资源
防止单个用户占用所有资源
```

#### 好处 2：稳定性

```
防止服务过载
确保响应时间在可接受范围
提高整体可用性
```

#### 好处 3：成本控制

```
限制 LLM API 调用次数
避免意外的高额 API 账单
可预测的运营成本
```

---

## 实际应用场景

### 场景 1：高并发时段

**时间：** 工作日 9:00-11:00

**现象：**
```
请求量：平时 10 请求/分钟 → 高峰 100 请求/分钟
并发 Agent: 平时 2-3 个 → 高峰 15-20 个
```

**配置调整：**
```python
# 平时
max_concurrent_agents = 10

# 高峰期（动态调整）
max_concurrent_agents = 20  # 临时提升
```

**效果：**
- 更多请求被接受
- 响应时间略有增加
- 用户满意度提升

---

### 场景 2：复杂任务处理

**任务类型：** 代码重构、文档分析

**特点：**
```
单次请求耗时：2-5 分钟
工具调用次数：20-50 次
Token 消耗：10 万 -50 万
```

**配置调整：**
```python
# 默认配置
max_request_timeout = 300  # 5 分钟

# 针对 VIP 用户（特殊路由）
max_request_timeout = 600  # 10 分钟
```

**效果：**
- 复杂任务可以完成
- 普通用户不受影响
- VIP 用户体验更好

---

### 场景 3：文件上传场景

**需求：** 用户上传大型代码文件进行分析

**文件大小：**
```
代码文件：1-5MB
配置文件：100KB - 1MB
日志文件：10-50MB
```

**配置调整：**
```python
# 默认配置
max_request_size = 10 * 1024 * 1024  # 10MB

# 针对文件分析服务
max_request_size = 50 * 1024 * 1024  # 50MB
```

**效果：**
- 支持大文件上传
- 小文件请求不受影响
- 资源使用可控

---

## 配置建议

### 开发环境

```python
# 宽松配置，方便调试
max_concurrent_agents = 50        # 高并发
max_request_timeout = 600         # 10 分钟
max_request_size = 50 * 1024 * 1024  # 50MB
```

**说明：** 开发时频繁测试，需要更宽松的限制。

---

### 测试环境

```python
# 模拟生产环境
max_concurrent_agents = 20
max_request_timeout = 300         # 5 分钟
max_request_size = 20 * 1024 * 1024  # 20MB
```

**说明：** 接近生产配置，但留有余量。

---

### 生产环境（小型服务）

```python
# 服务器配置：2 核 4GB
max_concurrent_agents = 10
max_request_timeout = 300
max_request_size = 10 * 1024 * 1024
```

**适用场景：**
- 日活用户 < 1000
- 请求量 < 1 万/天
- 预算有限

---

### 生产环境（中型服务）

```python
# 服务器配置：4 核 8GB
max_concurrent_agents = 30
max_request_timeout = 300
max_request_size = 20 * 1024 * 1024
```

**适用场景：**
- 日活用户 1000-5000
- 请求量 1 万 -10 万/天
- 有一定预算

---

### 生产环境（大型服务）

```python
# 服务器配置：8 核 16GB + 集群部署
max_concurrent_agents = 100
max_request_timeout = 300
max_request_size = 50 * 1024 * 1024
```

**适用场景：**
- 日活用户 > 5000
- 请求量 > 10 万/天
- 高可用要求

---

## 监控与告警

### 关键指标

#### 1. 并发 Agent 数量

```python
# Prometheus 指标
hermes_agents_active{instance="api-1"} 8
hermes_agents_active{instance="api-2"} 12
hermes_agents_active{instance="api-3"} 5
```

**告警规则：**
```yaml
# 并发数持续 5 分钟超过 80%
- alert: HighConcurrentAgents
  expr: hermes_agents_active / max_concurrent_agents > 0.8
  for: 5m
  annotations:
    summary: "并发 Agent 数量过高"
```

---

#### 2. 请求超时率

```python
# 超时请求占比
timeout_rate = timeout_requests / total_requests

# 正常：< 1%
# 警告：1-5%
# 严重：> 5%
```

**告警规则：**
```yaml
- alert: HighTimeoutRate
  expr: |
    sum(rate(hermes_requests_timeout_total[5m])) 
    / sum(rate(hermes_requests_total[5m])) > 0.05
  for: 5m
  annotations:
    summary: "请求超时率超过 5%"
```

---

#### 3. 请求大小分布

```python
# 请求大小直方图
hermes_request_size_bytes_bucket{le="1048576"}   # < 1MB
hermes_request_size_bytes_bucket{le="10485760"}  # < 10MB
hermes_request_size_bytes_bucket{le="52428800"}  # < 50MB
hermes_request_size_bytes_bucket{le="+Inf"}      # > 50MB
```

**分析：**
- 大部分请求 < 1MB → 正常
- 大量请求接近限制 → 考虑调整限制
- 频繁触发限制 → 需要优化或扩容

---

### Grafana 仪表板示例

```
┌─────────────────────────────────────────────┐
│ Hermes-Agent 资源监控                        │
├─────────────────────────────────────────────┤
│ 并发 Agent 数量                               │
│ ████████░░░░░░░░░░ 8/10 (80%)              │
│                                             │
│ 请求超时率                                   │
│ ██░░░░░░░░░░░░░░░░ 2.3% (警告)             │
│                                             │
│ 请求大小分布                                 │
│ < 1MB:    ████████████████████ 85%         │
│ 1-10MB:   ████░░░░░░░░░░░░░░ 12%           │
│ > 10MB:   █░░░░░░░░░░░░░░░░░ 3%            │
│                                             │
│ 平均响应时间                                 │
│ ████████░░░░░░░░░░ 3.2 秒                   │
└─────────────────────────────────────────────┘
```

---

## 故障排查

### 问题 1: 频繁触发并发限制

**现象：**
```
用户报告：经常收到 503 错误
日志：Max concurrent agents (10) reached
```

**排查步骤：**

```bash
# 1. 查看当前并发数
curl http://localhost:9090/metrics | grep hermes_agents_active

# 2. 查看慢请求
kubectl logs -f api-pod | grep "Request timeout"

# 3. 分析请求分布
kubectl top pod api-pod
```

**解决方案：**

```python
# 方案 1: 增加并发限制（如果有资源）
max_concurrent_agents = 20

# 方案 2: 优化慢请求
# - 添加请求超时
# - 优化 LLM 调用
# - 使用缓存

# 方案 3: 水平扩展
# 增加服务器实例
kubectl scale deployment hermes-api --replicas=3
```

---

### 问题 2: 大请求导致 OOM

**现象：**
```
服务突然崩溃
系统日志：Out of memory: Kill process
```

**排查步骤：**

```bash
# 1. 查看内存使用
kubectl top pod api-pod

# 2. 分析请求大小
grep "payload" /var/log/hermes-agent/access.log | \
  awk '{print $NF}' | sort -n | tail -20

# 3. 检查限制配置
cat .env | grep MAX_REQUEST_SIZE
```

**解决方案：**

```python
# 方案 1: 降低请求大小限制
max_request_size = 5 * 1024 * 1024  # 5MB

# 方案 2: 实现流式上传
# 分块处理大文件
# 边上传边处理，不一次性加载到内存

# 方案 3: 增加内存
# 升级服务器配置
# 4GB → 8GB
```

---

### 问题 3: 超时请求堆积

**现象：**
```
响应时间越来越长
队列中等待的请求越来越多
```

**排查步骤：**

```bash
# 1. 查看超时请求
grep "timeout" /var/log/hermes-agent/error.log | wc -l

# 2. 分析 LLM API 响应时间
curl -w "@curl-format.txt" -o /dev/null -s \
  https://api.dashscope.ai/v1/chat/completions

# 3. 检查工具执行时间
grep "Tool completed" /var/log/hermes-agent/access.log | \
  awk '{print $NF}' | sort -n | tail -10
```

**解决方案：**

```python
# 方案 1: 降低超时时间
max_request_timeout = 180  # 3 分钟

# 方案 2: 优化 LLM 调用
# - 使用更小的模型
# - 减少 prompt 长度
# - 添加重试机制

# 方案 3: 限流
# 在入口处限制请求速率
# 避免请求洪峰
```

---

## 最佳实践

### ✅ 推荐做法

#### 1. 动态调整限制

```python
# 根据时间段调整
def get_concurrent_limit():
    hour = datetime.now().hour
    if 2 <= hour <= 6:  # 凌晨
        return 50       # 宽松
    else:
        return 20       # 正常

# 根据负载调整
def get_concurrent_limit():
    cpu_usage = get_cpu_usage()
    if cpu_usage > 80:
        return 10   # 降低限制
    else:
        return 30   # 正常限制
```

---

#### 2. 分层限制

```python
LIMITS = {
    "free": {
        "max_concurrent": 5,
        "max_timeout": 180,
        "max_size": 5 * 1024 * 1024
    },
    "pro": {
        "max_concurrent": 20,
        "max_timeout": 300,
        "max_size": 20 * 1024 * 1024
    },
    "enterprise": {
        "max_concurrent": 100,
        "max_timeout": 600,
        "max_size": 100 * 1024 * 1024
    }
}
```

---

#### 3. 优雅降级

```python
# Redis 故障时降级到内存存储
try:
    redis.ping()
except:
    # 降级：降低限制
    max_concurrent_agents = 5
    logger.warning("Redis 不可用，已降级")

# LLM API 故障时快速失败
if llm_latency > 10:  # 超过 10 秒
    raise HTTPException(503, "LLM 服务响应慢，请稍后重试")
```

---

#### 4. 监控驱动优化

```python
# 定期分析指标
def analyze_and_adjust():
    avg_timeout = get_avg_timeout_rate()
    if avg_timeout > 0.05:  # > 5%
        # 自动降低并发限制
        max_concurrent_agents *= 0.8
        logger.info(f"自动调整并发限制：{max_concurrent_agents}")
```

---

### ❌ 避免的做法

#### 1. 限制过严

```python
# ❌ 过于严格，影响用户体验
max_concurrent_agents = 2
max_request_timeout = 30
max_request_size = 1 * 1024 * 1024

# 结果：大量请求被拒绝，用户流失
```

---

#### 2. 限制过松

```python
# ❌ 过于宽松，失去保护意义
max_concurrent_agents = 1000
max_request_timeout = 3600
max_request_size = 1024 * 1024 * 1024

# 结果：资源耗尽，服务崩溃
```

---

#### 3. 硬编码限制

```python
# ❌ 难以调整
max_concurrent_agents = 10  # 写死在代码中

# ✅ 使用配置
max_concurrent_agents = settings.max_concurrent_agents  # 从配置读取
```

---

## 配置对比表

| 配置项 | 开发环境 | 测试环境 | 生产 (小) | 生产 (中) | 生产 (大) |
|--------|---------|---------|----------|----------|----------|
| `max_concurrent_agents` | 50 | 20 | 10 | 30 | 100 |
| `max_request_timeout` | 600 | 300 | 300 | 300 | 300 |
| `max_request_size` | 50MB | 20MB | 10MB | 20MB | 50MB |
| **适用场景** | 开发调试 | 功能测试 | 日活<1k | 日活 1k-5k | 日活>5k |

---

## 总结

### 核心要点

1. **并发限制**：防止资源耗尽，确保公平性
2. **超时限制**：防止慢请求阻塞，提高响应速度
3. **大小限制**：防止大请求攻击，保护内存

### 配置原则

- 🎯 **开发环境**：宽松，方便调试
- 🧪 **测试环境**：接近生产，发现潜在问题
- 🚀 **生产环境**：根据实际负载和资源动态调整
- 📊 **监控驱动**：基于指标持续优化

### 最佳实践

- ✅ 实现分层限制（免费/付费/企业）
- ✅ 支持动态调整（时间段、负载）
- ✅ 优雅降级（故障时降低限制）
- ✅ 完善的监控和告警
- ✅ 定期审查和优化配置

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**所属项目：** Hermes-Agent FastAPI 服务  
**作者：** Hermes-Agent Team

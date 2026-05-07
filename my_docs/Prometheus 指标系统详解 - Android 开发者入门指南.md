# Prometheus 指标系统详解 - Android 开发者入门指南

> Prometheus 是一个开源的系统监控和告警工具包，本文档专为 Android 开发者设计，帮助您快速理解 Prometheus 指标系统。

---

## 📋 目录

- [Prometheus 简介](#prometheus 简介)
- [核心概念](#核心概念)
- [四种指标类型](#四种指标类型)
- [指标命名规范](#指标命名规范)
- [标签（Labels）](#标签 labels)
- [PromQL 查询语言](#promql 查询语言)
- [实战示例](#实战示例)
- [Grafana 可视化](#grafana 可视化)
- [告警规则](#告警规则)
- [Android 对比理解](#android 对比理解)
- [最佳实践](#最佳实践)

---

## Prometheus 简介

### 什么是 Prometheus？

Prometheus 是一个开源的**监控系统**和**时序数据库**，由 SoundCloud 于 2012 年开发，现在是 CNCF（云原生计算基金会）的第二个毕业项目。

```
┌─────────────────┐
│  被监控服务      │
│  (FastAPI)      │
│  :8000/metrics  │
└────────┬────────┘
         │ 每 15 秒抓取
         ▼
┌─────────────────┐
│  Prometheus     │
│  Server         │
│  (时序数据库)    │
└────────┬────────┘
         │ 查询
         ▼
┌─────────────────┐
│  Grafana        │
│  Dashboard      │
└─────────────────┘
```

### 核心特点

| 特点 | 说明 | Android 类比 |
|------|------|-------------|
| **多维数据模型** | 指标名 + 标签（key-value） | Bundle/Extras |
| **PromQL** | 强大的查询语言 | SQL/Room Query |
| **不依赖分布式存储** | 单节点即可工作 | SQLite 本地数据库 |
| **Pull 模型** | 主动抓取指标 | Polling 轮询 |
| **Push 模型** | 通过 Pushgateway | Firebase Analytics 推送 |
| **服务发现** | 自动发现监控目标 | Service Discovery |

---

## 核心概念

### 1. 指标（Metric）

指标是监控的基本单位，由**指标名**和**标签**组成。

```
指标名：http_requests_total
标签：{method="POST", endpoint="/api/v1/chat", status="200"}

完整表示：
http_requests_total{method="POST", endpoint="/api/v1/chat", status="200"}
```

#### Android 对比

```kotlin
// Firebase Analytics 事件
Bundle bundle = new Bundle();
bundle.putString("method", "POST");
bundle.putString("endpoint", "/api/v1/chat");
bundle.putString("status", "200");
FirebaseAnalytics.logEvent("http_requests_total", bundle)

// 指标名 = 事件名
// 标签 = Bundle 参数
```

---

### 2. 时间序列（Time Series）

时间序列是具有相同指标名和标签的数据点集合，按时间戳排序。

```
时间戳          值
─────────────────────
1704067200      100
1704067215      105
1704067230      112
1704067245      118
```

#### Android 对比

```kotlin
// 性能监控数据
data class PerformancePoint(
    val timestamp: Long,  // 时间戳
    val value: Double     // 值（如延迟）
)

// 时间序列 = List<PerformancePoint>
val latencySeries = listOf(
    PerformancePoint(1704067200, 100.0),
    PerformancePoint(1704067215, 105.0),
    PerformancePoint(1704067230, 112.0),
)
```

---

### 3. 抓取（Scrape）

Prometheus 定期从目标服务的 `/metrics` 端点抓取指标。

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'hermes-api'
    scrape_interval: 15s  # 每 15 秒抓取一次
    static_configs:
      - targets: ['localhost:8000']
```

#### Android 对比

```kotlin
// 定期轮询
val job = PeriodicWorkRequestBuilder<MetricsWorker>(15, TimeUnit.SECONDS)
    .build()

WorkManager.getInstance().enqueue(job)

// 或者使用 Handler
handler.postDelayed(object : Runnable {
    override fun run() {
        fetchMetrics()  // 抓取指标
        handler.postDelayed(this, 15000)
    }
}, 15000)
```

---

## 四种指标类型

Prometheus 支持 4 种核心指标类型，这是理解 Prometheus 的关键。

### 1. Counter（计数器）

#### 特点
- **只增不减**（只能增加或重置为 0）
- 用于累计值
- 重启后清零

#### 定义示例

```python
from prometheus_client import Counter

# 定义计数器
REQUEST_COUNT = Counter(
    "http_requests_total",      # 指标名称（约定：_total 后缀）
    "Total HTTP requests",      # 描述
    ["method", "endpoint", "status_code"],  # 标签
)

# 使用
REQUEST_COUNT.labels(
    method="POST",
    endpoint="/api/v1/chat",
    status_code="200"
).inc()  # +1

# 增加任意值
REQUEST_COUNT.labels(method="GET", endpoint="/api/v1/health", status_code="200").inc(5)
```

#### Android 对比

```kotlin
// 计数器（类似 SharePreference 中的累计值）
class Counter {
    private var count = 0
    
    fun inc() { count++ }
    fun inc(value: Int) { count += value }
    fun get(): Int = count
}

// 使用场景
val downloadCounter = Counter()
downloadCounter.inc()  // 下载完成 +1
```

#### 使用场景

| 场景 | 示例 |
|------|------|
| 请求总数 | `http_requests_total` |
| 错误总数 | `http_errors_total` |
| 任务完成数 | `tasks_completed_total` |
| Token 使用量 | `tokens_used_total` |

#### 查询示例

```promql
# 总请求数
sum(http_requests_total)

# 每秒请求数（速率）
rate(http_requests_total[5m])

# 按状态码分组
sum by (status_code) (http_requests_total)

# 过去 1 小时的增长量
increase(http_requests_total[1h])
```

---

### 2. Gauge（仪表盘）

#### 特点
- **可增可减**
- 用于瞬时值
- 表示当前状态

#### 定义示例

```python
from prometheus_client import Gauge

# 定义 Gauge
ACTIVE_CONNECTIONS = Gauge(
    "active_connections",  # 指标名称
    "Number of active connections"  # 描述
)

# 使用
ACTIVE_CONNECTIONS.set(42)  # 设置值
ACTIVE_CONNECTIONS.inc()    # +1
ACTIVE_CONNECTIONS.dec()    # -1
ACTIVE_CONNECTIONS.set(0)   # 设置为 0
```

#### Android 对比

```kotlin
// 电量显示（类似 Gauge）
val batteryLevel: Int = 75  // 当前电量 75%
// 可以上升（充电）或下降（使用）

// 或者内存使用率
val memoryUsage: Double = 0.65  // 65%
```

#### 使用场景

| 场景 | 示例 |
|------|------|
| CPU 使用率 | `cpu_usage_percent` |
| 内存使用率 | `memory_usage_bytes` |
| 活跃连接数 | `active_connections` |
| 队列长度 | `queue_length` |
| 温度 | `temperature_celsius` |

#### 查询示例

```promql
# 当前值
active_connections

# 过去 1 小时最大值
max_over_time(active_connections[1h])

# 过去 1 小时平均值
avg_over_time(active_connections[1h])

# 当前值与 5 分钟前的差值
active_connections - active_connections offset 5m
```

---

### 3. Histogram（直方图）

#### 特点
- **统计分布**（将数据分到不同的桶中）
- 用于延迟、大小等
- 可计算分位数（P50、P95、P99）

#### 定义示例

```python
from prometheus_client import Histogram

# 定义 Histogram
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",  # 指标名称（约定：_seconds 后缀）
    "HTTP request duration in seconds",  # 描述
    ["endpoint"],  # 标签
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],  # 桶
)

# 使用（装饰器自动计时）
@REQUEST_DURATION.time()
async def handle_request():
    # 业务逻辑
    ...
```

#### 生成的指标

Histogram 会自动生成 3 个指标：

```
# 1. 桶计数器（每个桶一个）
http_request_duration_seconds_bucket{le="0.1"}    # ≤0.1 秒的请求数
http_request_duration_seconds_bucket{le="0.5"}    # ≤0.5 秒的请求数
http_request_duration_seconds_bucket{le="1.0"}    # ≤1.0 秒的请求数
http_request_duration_seconds_bucket{le="+Inf"}   # 所有请求

# 2. 总和
http_request_duration_seconds_sum  # 所有请求的总耗时

# 3. 计数
http_request_duration_seconds_count  # 请求总数
```

#### Android 对比

```kotlin
// 性能直方图（类似 Firebase Performance）
class LatencyHistogram {
    private val buckets = mapOf(
        0.1 to 0,   // ≤100ms
        0.5 to 0,   // ≤500ms
        1.0 to 0,   // ≤1s
        Double.MAX_VALUE to 0  // >1s
    )
    
    fun observe(latency: Double) {
        // 找到对应的桶并计数
    }
}

// Firebase Performance Monitoring
FirebasePerformance.getInstance()
    .newTrace("api_call")
    .apply {
        start()
        // ... 执行操作
        stop()  // 自动记录延迟分布
    }
```

#### 使用场景

| 场景 | 示例 |
|------|------|
| 请求延迟 | `http_request_duration_seconds` |
| 响应大小 | `http_response_size_bytes` |
| 数据库查询时间 | `db_query_duration_seconds` |
| 处理时间 | `processing_time_seconds` |

#### 查询示例

```promql
# P50 延迟（中位数）
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

# P95 延迟
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99 延迟
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# 平均延迟
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# 每秒请求数
rate(http_request_duration_seconds_count[5m])
```

---

### 4. Summary（摘要）

#### 特点
- **客户端计算分位数**
- 精度高但无法聚合
- 适用于全局分位数

#### 定义示例

```python
from prometheus_client import Summary

# 定义 Summary
REQUEST_LATENCY = Summary(
    "request_latency_seconds",  # 指标名称
    "Request latency in seconds",  # 描述
    ["endpoint"]  # 标签
)

# 使用（装饰器）
@REQUEST_LATENCY.time()
async def handle_request():
    ...
```

#### 生成的指标

```
# 分位数（在客户端计算）
request_latency_seconds{quantile="0.5"}   # P50
request_latency_seconds{quantile="0.9"}   # P90
request_latency_seconds{quantile="0.99"}  # P99

# 总和
request_latency_seconds_sum

# 计数
request_latency_seconds_count
```

#### Histogram vs Summary

| 特性 | Histogram | Summary |
|------|-----------|---------|
| **分位数计算** | 服务端（Prometheus） | 客户端（应用） |
| **可聚合性** | ✅ 可以聚合 | ❌ 不能聚合 |
| **精度** | 近似值 | 精确值 |
| **性能开销** | 较低 | 较高 |
| **推荐场景** | 大多数情况 | 需要高精度分位数 |

**推荐：** 优先使用 Histogram，除非需要高精度的分位数。

---

## 指标命名规范

### 命名约定

```
<应用>_<模块>_<指标>_<单位>
```

#### 示例

```
hermes_http_requests_total          # ✅ 好
hermes_request_duration_seconds     # ✅ 好
hermes_cpu_usage_percent            # ✅ 好
hermes_memory_usage_bytes           # ✅ 好

http_requests                       # ❌ 缺少应用名
request_latency                     # ❌ 缺少单位
cpu                                 # ❌ 含义不明确
```

### 单位规范

| 单位 | 后缀 | 示例 |
|------|------|------|
| 秒 | `_seconds` | `request_duration_seconds` |
| 毫秒 | `_milliseconds` | `response_time_milliseconds` |
| 字节 | `_bytes` | `memory_usage_bytes` |
| 百分比 | `_percent` | `cpu_usage_percent` |
| 计数 | `_total` | `requests_total` |

### Counter 命名

Counter **必须**以 `_total` 结尾：

```python
# ✅ 正确
http_requests_total
http_errors_total
tokens_used_total

# ❌ 错误
http_requests
http_errors
```

---

## 标签（Labels）

### 什么是标签？

标签是指标的维度，用于细分指标数据。

```
http_requests_total{method="POST", endpoint="/api/v1/chat", status="200"}
                     └──────┘ └──────────┬───────────┘ └─────┬────┘
                      标签键              标签值
```

### 标签使用规范

#### ✅ 好的标签设计（低基数）

```python
REQUEST_COUNT.labels(
    method="POST",           # 低基数（GET, POST, PUT, DELETE）
    endpoint="/api/v1/chat", # 低基数（有限的 API 端点）
    status="200"             # 低基数（HTTP 状态码）
)
```

#### ❌ 不好的标签设计（高基数）

```python
REQUEST_COUNT.labels(
    user_id="user_12345",    # ❌ 高基数（每个用户一个标签）
    session_id="abc123",     # ❌ 高基数（每个会话一个标签）
    timestamp="1234567890"   # ❌ 高基数（时间戳）
)
```

### 高基数的危害

```
高基数标签 → 时间序列爆炸 → 内存爆炸 → 查询变慢 → 系统崩溃

示例：
user_id 标签有 100 万用户
× 10 个端点
× 5 种方法
× 10 种状态码
= 5 亿个时间序列！💥
```

### 标签最佳实践

| 推荐 | 不推荐 |
|------|--------|
| `method="GET"` | `user_id="123"` |
| `endpoint="/api/v1/chat"` | `session_id="abc"` |
| `status="200"` | `timestamp="1234567890"` |
| `error_type="timeout"` | `request_id="uuid"` |

---

## PromQL 查询语言

### 什么是 PromQL？

PromQL（Prometheus Query Language）是 Prometheus 的查询语言，用于检索和聚合时间序列数据。

### 基础查询

#### 1. 简单查询

```promql
# 选择所有 http_requests_total 指标
http_requests_total

# 带标签过滤
http_requests_total{method="POST"}

# 多个标签
http_requests_total{method="POST", status="200"}

# 正则匹配
http_requests_total{endpoint=~"/api/v1/.*"}  # =~ 正则匹配
http_requests_total{endpoint!~"/api/v1/.*"}  # !~ 正则不匹配
```

#### 2. 数学运算

```promql
# 加法
http_requests_total + 100

# 减法
http_requests_total - 100

# 乘法
http_requests_total * 2

# 除法
http_requests_total / http_errors_total

# 取模
http_requests_total % 10
```

### 聚合函数

#### 1. sum（求和）

```promql
# 总请求数
sum(http_requests_total)

# 按方法分组求和
sum by (method) (http_requests_total)

# 不按某个标签分组
sum without (endpoint) (http_requests_total)
```

#### 2. avg（平均）

```promql
# 平均延迟
avg(http_request_duration_seconds_sum / http_request_duration_seconds_count)

# 按端点分组求平均
avg by (endpoint) (http_request_duration_seconds)
```

#### 3. max/min（最大/最小）

```promql
# 最大 CPU 使用率
max(cpu_usage_percent)

# 最小内存
min(memory_usage_bytes)
```

#### 4. count（计数）

```promql
# 时间序列数量
count(http_requests_total)
```

### 速率函数

#### 1. rate（增长率）

计算每秒的平均增长率。

```promql
# 每秒请求数
rate(http_requests_total[5m])

# 每秒错误数
rate(http_errors_total[5m])
```

#### 2. increase（增长量）

计算时间范围内的总增长量。

```promql
# 过去 1 小时的请求增长量
increase(http_requests_total[1h])

# 过去 24 小时的错误增长量
increase(http_errors_total[24h])
```

#### 3. irate（瞬时增长率）

计算最后一个时间点的瞬时增长率。

```promql
# 瞬时请求速率
irate(http_requests_total[5m])
```

### 分位数函数

```promql
# P95 延迟
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99 延迟
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### 偏移查询

```promql
# 当前值与 5 分钟前的差值
http_requests_total - http_requests_total offset 5m

# 与昨天同一时间对比
http_requests_total - http_requests_total offset 1d
```

---

## 实战示例

### 示例 1：FastAPI 指标收集

```python
from prometheus_client import Counter, Histogram, Gauge
from fastapi import FastAPI, Request
import time

app = FastAPI()

# 定义指标
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

ACTIVE_REQUESTS = Gauge(
    "active_requests",
    "Number of active requests",
)

# 中间件收集指标
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    start_time = time.time()
    ACTIVE_REQUESTS.inc()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    ACTIVE_REQUESTS.dec()
    
    REQUEST_COUNT.labels(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
    ).inc()
    
    REQUEST_DURATION.labels(
        endpoint=request.url.path,
    ).observe(duration)
    
    return response
```

### 示例 2：Agent 监控

```python
# Agent 运行指标
AGENT_RUNS = Counter(
    "hermes_agent_runs_total",
    "Total agent runs",
    ["model", "status"],  # success, error, timeout
)

AGENT_ITERATIONS = Histogram(
    "hermes_agent_iterations",
    "Number of iterations per agent run",
    buckets=[1, 5, 10, 20, 30, 50, 70, 90],
)

ACTIVE_AGENTS = Gauge(
    "hermes_active_agents",
    "Number of currently active agents",
)

TOKEN_USAGE = Counter(
    "hermes_tokens_total",
    "Total tokens used",
    ["type"],  # prompt, completion, total
)

# 使用
async def run_agent(message: str, model: str):
    ACTIVE_AGENTS.inc()
    
    try:
        # 运行业务逻辑
        result = await agent.chat(message)
        
        # 记录成功
        AGENT_RUNS.labels(model=model, status="success").inc()
        
        # 记录 Token 使用
        TOKEN_USAGE.labels(type="prompt").inc(result.prompt_tokens)
        TOKEN_USAGE.labels(type="completion").inc(result.completion_tokens)
        
        return result
        
    except Exception as e:
        # 记录失败
        AGENT_RUNS.labels(model=model, status="error").inc()
        raise
        
    finally:
        ACTIVE_AGENTS.dec()
```

### 示例 3：数据库监控

```python
# 数据库指标
DB_QUERIES = Counter(
    "database_queries_total",
    "Total database queries",
    ["table", "operation"],  # users, sessions; select, insert, update, delete
)

DB_QUERY_DURATION = Histogram(
    "database_query_duration_seconds",
    "Database query duration",
    ["table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

DB_CONNECTIONS = Gauge(
    "database_connections",
    "Number of database connections",
    ["state"],  # active, idle
)

# 使用
async def query_database(table: str, operation: str, sql: str):
    DB_CONNECTIONS.labels(state="active").inc()
    
    start_time = time.time()
    
    try:
        result = await db.execute(sql)
        
        DB_QUERIES.labels(table=table, operation=operation).inc()
        
        return result
        
    finally:
        duration = time.time() - start_time
        DB_QUERY_DURATION.labels(table=table).observe(duration)
        DB_CONNECTIONS.labels(state="active").dec()
```

---

## Grafana 可视化

### 什么是 Grafana？

Grafana 是一个开源的可视化和监控平台，支持 Prometheus、MySQL、Elasticsearch 等多种数据源。

### 配置数据源

```yaml
# docker-compose.yml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
```

### 创建面板

#### 1. 请求速率面板

```
Panel Title: Request Rate (RPS)
Panel Type: Graph
Query:
  sum(rate(http_requests_total[5m]))
Legend: Requests/sec
```

#### 2. 延迟面板

```
Panel Title: Request Latency (P50, P95, P99)
Panel Type: Graph
Queries:
  - histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
    Legend: P50
  - histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
    Legend: P95
  - histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
    Legend: P99
```

#### 3. 错误率面板

```
Panel Title: Error Rate (%)
Panel Type: Graph
Query:
  sum(rate(http_requests_total{status=~"5.."}[5m])) 
  / 
  sum(rate(http_requests_total[5m])) * 100
Legend: Error Rate
```

#### 4. 仪表盘示例

```json
{
  "dashboard": {
    "title": "Hermes-Agent API Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100"
          }
        ]
      }
    ]
  }
}
```

---

## 告警规则

### 什么是告警规则？

告警规则用于在指标满足特定条件时触发告警。

### 告警规则示例

```yaml
# alerts.yml
groups:
  - name: hermes-api-alerts
    rules:
      # 服务宕机告警
      - alert: ServiceDown
        expr: up{job="hermes-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Hermes-Agent 服务宕机"
          description: "服务 {{ $labels.instance }} 已宕机超过 1 分钟"
      
      # 高错误率告警
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) 
          / 
          sum(rate(http_requests_total[5m])) * 100 > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "错误率过高"
          description: "当前错误率为 {{ $value }}%，超过 5% 阈值"
      
      # 高延迟告警
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "延迟过高"
          description: "P99 延迟为 {{ $value }} 秒，超过 10 秒阈值"
      
      # 高 CPU 使用率告警
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率过高"
          description: "CPU 使用率为 {{ $value }}%，超过 80% 阈值"
      
      # 高内存使用率告警
      - alert: HighMemoryUsage
        expr: memory_usage_bytes / memory_total_bytes * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率为 {{ $value }}%，超过 85% 阈值"
```

### 告警级别

| 级别 | 说明 | 响应时间 |
|------|------|---------|
| `critical` | 紧急 | 立即响应 |
| `warning` | 警告 | 30 分钟内响应 |
| `info` | 提示 | 24 小时内响应 |

### 告警通知渠道

```yaml
# alertmanager.yml
route:
  group_by: ['alertname', 'severity']
  receiver: 'default'
  
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'  # 电话通知
    - match:
        severity: warning
      receiver: 'slack'      # Slack 通知
    - match:
        severity: info
      receiver: 'email'      # 邮件通知

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'
  
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
  
  - name: 'email'
    email_configs:
      - to: 'team@example.com'
```

---

## Android 对比理解

### 指标类型对比

| Prometheus | Android | 使用场景 |
|------------|---------|---------|
| **Counter** | 计数器（下载进度） | 请求总数、错误总数 |
| **Gauge** | 仪表盘（电量显示） | CPU 使用率、内存使用率 |
| **Histogram** | 性能直方图 | 延迟分布、响应大小 |
| **Summary** | 精确分位数统计 | 全局延迟分位数 |

### 监控对比

| Prometheus | Android | 说明 |
|------------|---------|------|
| `/metrics` 端点 | Firebase Analytics | 指标暴露 |
| Scrape（抓取） | Polling（轮询） | 数据收集 |
| PromQL | SQL/Room Query | 查询语言 |
| Grafana | Firebase Console | 可视化 |
| Alertmanager | Crashlytics/Firebase Alerts | 告警通知 |

### 代码对比

#### Counter vs 计数器

```python
# Prometheus Counter
REQUEST_COUNT = Counter("requests_total", "Total requests")
REQUEST_COUNT.inc()
```

```kotlin
// Android 计数器
class Counter {
    private var count = 0
    fun inc() { count++ }
}
```

#### Gauge vs 电量显示

```python
# Prometheus Gauge
BATTERY_LEVEL = Gauge("battery_level", "Battery level")
BATTERY_LEVEL.set(75)
```

```kotlin
// Android 电量
val batteryLevel: Int = 75  // 当前 75%
```

#### Histogram vs Firebase Performance

```python
# Prometheus Histogram
REQUEST_DURATION = Histogram(
    "request_duration_seconds",
    "Request duration",
    buckets=[0.1, 0.5, 1.0, 2.0]
)

@REQUEST_DURATION.time()
async def handle_request():
    ...
```

```kotlin
// Firebase Performance
val trace = FirebasePerformance.getInstance().newTrace("api_call")
trace.start()
// ... 执行操作
trace.stop()  // 自动记录延迟分布
```

---

## 最佳实践

### 1. 指标命名

```python
# ✅ 推荐
http_requests_total
http_request_duration_seconds
cpu_usage_percent

# ❌ 不推荐
http_requests           # 缺少单位
request_latency         # 缺少应用名
cpu                     # 含义不明确
```

### 2. 标签设计

```python
# ✅ 低基数标签
REQUEST_COUNT.labels(
    method="POST",           # 4 种值
    endpoint="/api/v1/chat", # 有限的端点
    status="200"             # 有限的状态码
)

# ❌ 高基数标签
REQUEST_COUNT.labels(
    user_id="user_12345",    # 百万级
    session_id="abc123",     # 百万级
    timestamp="1234567890"   # 无限值
)
```

### 3. 指标收集

```python
# ✅ 使用装饰器（自动计时）
@REQUEST_DURATION.time()
async def handle_request():
    ...

# ✅ 使用中间件（全局收集）
@app.middleware("http")
async def track_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    return response

# ❌ 手动计时（容易出错）
start_time = time.time()
# ... 业务逻辑
duration = time.time() - start_time
REQUEST_DURATION.observe(duration)
```

### 4. 告警规则

```yaml
# ✅ 合理的告警阈值
- alert: HighErrorRate
  expr: error_rate > 5%  # 5% 错误率
  for: 5m  # 持续 5 分钟

# ❌ 不合理的告警
- alert: AnyError
  expr: error_rate > 0%  # 零容忍，误报多
  for: 1m  # 时间太短
```

### 5. 采样率

```python
# 生产环境
traces_sample_rate = 0.1  # 10% 采样

# 开发环境
traces_sample_rate = 1.0  # 100% 采样

# 重要端点
if endpoint == "/api/v1/payment":
    traces_sample_rate = 1.0  # 支付端点全量采样
```

### 6. 文档化

```python
# ✅ 添加文档字符串
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed",  # 清晰的描述
    ["method", "endpoint", "status_code"],
)

# ❌ 缺少描述
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Requests",  # 描述不清晰
)
```

---

## 总结

### 核心知识点

1. **四种指标类型**
   - **Counter**：只增不减（请求总数）
   - **Gauge**：可增可减（CPU 使用率）
   - **Histogram**：统计分布（延迟直方图）
   - **Summary**：客户端分位数（精确统计）

2. **PromQL 查询**
   - 基础查询：`http_requests_total`
   - 聚合函数：`sum()`, `avg()`, `max()`
   - 速率函数：`rate()`, `increase()`
   - 分位数：`histogram_quantile()`

3. **标签设计**
   - 使用低基数标签
   - 避免高基数标签（user_id, session_id）
   - 遵循命名规范

4. **告警规则**
   - 设置合理的阈值
   - 配置告警级别（critical, warning, info）
   - 选择合适的通知渠道

### Android 开发者优势

作为 Android 开发者，您已经具备以下优势：

✅ **异步处理经验** - Coroutine → async/await  
✅ **性能监控理解** - Firebase Performance → Histogram  
✅ **数据分析基础** - Firebase Analytics → Prometheus  
✅ **告警处理** - Crashlytics Alerts → Alertmanager  

### 下一步学习建议

1. **实践项目** - 在 FastAPI 项目中集成 Prometheus
2. **学习 Grafana** - 创建可视化仪表盘
3. **配置告警** - 设置 Alertmanager 通知
4. **深入 PromQL** - 学习高级查询技巧
5. **容器化部署** - 使用 Docker Compose 部署 Prometheus + Grafana

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**适用对象：** Android 开发者、后端初学者  
**作者：** Hermes-Agent Team

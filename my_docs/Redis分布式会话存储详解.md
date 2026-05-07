# Redis 分布式会话存储详解

## 概述

在 Hermes Agent FastAPI 服务中，`redis_url` 配置项用于启用 Redis 作为分布式会话存储后端。当服务以多实例模式部署时（如 Kubernetes 多 Pod、Docker Swarm 或多台服务器），Redis 提供统一的会话状态管理，确保用户无论请求被路由到哪个实例，都能获取一致的会话数据。

---

## 配置说明

### 配置位置

```python
# fastapi_server/config.py
class Settings(BaseSettings):
    # ========== Redis 配置（分布式会话存储） ==========
    redis_url: Optional[str] = None
```

### 配置方式

| 方式 | 示例 |
|------|------|
| 环境变量 | `REDIS_URL=redis://localhost:6379/0` |
| .env 文件 | `redis_url=redis://user:pass@redis.example.com:6379/1` |
| 默认值 | `None`（使用本地 SQLite 存储） |

### URL 格式

```
redis://[用户名]:[密码]@[主机]:[端口]/[数据库编号]

# 示例
redis://localhost:6379/0                          # 本地无认证
redis://user:password@192.168.1.100:6379/0        # 带认证
rediss://redis.example.com:6380/0                 # SSL/TLS 加密连接
redis://localhost:6379/0?decode_responses=true    # 带查询参数
```

---

## 为什么需要 Redis

### 单机模式的问题

当 FastAPI 服务只运行一个实例时，会话数据可以存储在：
- 本地内存（Python dict）
- 本地 SQLite 数据库（`~/.hermes/state.db`）

**问题**：当服务扩展到多个实例时，每个实例有自己的内存/SQLite，导致：

```
用户请求 → 负载均衡器 → 实例 A（会话数据在这里）
                              ↓
用户再次请求 → 负载均衡器 → 实例 B（找不到会话！）
```

### Redis 解决方案

```
用户请求 → 负载均衡器 → 实例 A ──┐
                                   ├──→ Redis（统一存储会话）
用户再次请求 → 负载均衡器 → 实例 B ──┘
```

**优势**：
1. **共享状态** — 所有实例访问同一份会话数据
2. **高性能** — 内存级读写速度（10万+ QPS）
3. **自动过期** — 支持 TTL，自动清理过期会话
4. **持久化** — 可配置 RDB/AOF 防止数据丢失
5. **高可用** — 支持主从复制、Sentinel、Cluster 模式

---

## 在 Hermes Agent 中的应用

### 会话数据模型

```python
# 存储在 Redis 中的会话数据结构
{
    "session_id": "web_abc123",
    "user_id": "user_456",
    "title": "Python 排序算法讨论",
    "messages": [
        {"role": "user", "content": "帮我写排序算法"},
        {"role": "assistant", "content": "这是快速排序实现..."}
    ],
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T11:45:00",
    "api_calls": 5,
    "input_tokens": 1200,
    "output_tokens": 2800,
    "ttl": 3600  # 1小时后过期
}
```

### Redis Key 设计

| Key 模式 | 说明 | 示例 |
|----------|------|------|
| `hermes:session:{session_id}` | 会话数据 | `hermes:session:web_abc123` |
| `hermes:user:{user_id}:sessions` | 用户的会话列表 | `hermes:user:user_456:sessions` |
| `hermes:session:{id}:lock` | 分布式锁 | `hermes:session:web_abc123:lock` |

### 代码集成示例

```python
import redis
import json
from typing import Optional, Dict, Any

class RedisSessionStore:
    """Redis 会话存储实现"""
    
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = "hermes:session"
        self.default_ttl = 3600  # 1小时
    
    def _key(self, session_id: str) -> str:
        """生成 Redis Key"""
        return f"{self.key_prefix}:{session_id}"
    
    def save_session(self, session_id: str, data: Dict[str, Any], ttl: int = None) -> bool:
        """保存会话数据"""
        try:
            key = self._key(session_id)
            self.client.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(data, ensure_ascii=False)
            )
            return True
        except redis.RedisError as e:
            logger.error(f"保存会话失败: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        try:
            key = self._key(session_id)
            data = self.client.get(key)
            if data:
                # 刷新 TTL（活跃会话延长过期时间）
                self.client.expire(key, self.default_ttl)
                return json.loads(data)
            return None
        except redis.RedisError as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            key = self._key(session_id)
            return self.client.delete(key) > 0
        except redis.RedisError as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return self.client.exists(self._key(session_id)) > 0
    
    def get_user_sessions(self, user_id: str) -> list:
        """获取用户的所有会话"""
        pattern = f"{self.key_prefix}:*"
        sessions = []
        for key in self.client.scan_iter(match=pattern):
            data = self.client.get(key)
            if data:
                session = json.loads(data)
                if session.get("user_id") == user_id:
                    sessions.append(session)
        return sessions
```

---

## Redis 部署模式

### 1. 单机模式（开发/测试）

```yaml
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

配置：
```env
REDIS_URL=redis://localhost:6379/0
```

### 2. 主从复制（读写分离）

```yaml
services:
  redis-master:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  redis-slave:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    command: redis-server --slaveof redis-master 6379
```

配置：
```env
# 写操作走主节点
REDIS_URL=redis://master:6379/0
# 读操作走从节点（应用层实现）
REDIS_READ_URL=redis://slave:6380/0
```

### 3. Sentinel 高可用（推荐生产环境）

```yaml
services:
  redis-master:
    image: redis:7-alpine
  
  redis-slave1:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379
  
  redis-slave2:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379
  
  sentinel1:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
  
  sentinel2:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
  
  sentinel3:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
```

配置：
```env
REDIS_URL=redis+sentinel://sentinel1:26379,sentinel2:26379,sentinel3:26379/mymaster/0
```

### 4. Cluster 集群模式（大规模）

```yaml
# 6 节点集群（3 主 3 从）
services:
  redis-node-1:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --port 6379
  redis-node-2:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --port 6379
  redis-node-3:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --port 6379
  redis-node-4:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --port 6379
  redis-node-5:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --port 6379
  redis-node-6:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --port 6379
```

配置：
```env
REDIS_URL=redis://node1:6379,node2:6379,node3:6379/0
```

---

## 性能优化

### 连接池

```python
# 使用连接池避免频繁创建连接
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50,      # 最大连接数
    retry_on_timeout=True,    # 超时重试
    socket_connect_timeout=5, # 连接超时
    socket_timeout=5          # 读写超时
)
client = redis.Redis(connection_pool=pool)
```

### Pipeline 批量操作

```python
# 批量保存多条会话数据
pipe = client.pipeline()
for session in sessions:
    key = f"hermes:session:{session['session_id']}"
    pipe.setex(key, 3600, json.dumps(session))
pipe.execute()  # 一次性发送所有命令
```

### 序列化优化

| 序列化方式 | 优点 | 缺点 |
|-----------|------|------|
| JSON | 可读性好，跨语言 | 体积大，速度慢 |
| MessagePack | 体积小，速度快 | 二进制，不可读 |
| Pickle | Python 原生，速度快 | 仅限 Python，有安全风险 |

```python
import msgpack

# 使用 MessagePack 替代 JSON
data = msgpack.packb(session_data, use_bin_type=True)
client.setex(key, 3600, data)

# 读取
data = client.get(key)
session = msgpack.unpackb(data, raw=False)
```

---

## 安全最佳实践

### 1. 启用认证

```conf
# redis.conf
requirepass your_strong_password
```

```env
REDIS_URL=redis://:your_strong_password@localhost:6379/0
```

### 2. 使用 SSL/TLS

```env
# 加密连接
REDIS_URL=rediss://user:pass@redis.example.com:6380/0
```

### 3. 网络隔离

```yaml
# Docker 网络隔离
services:
  redis:
    networks:
      - backend
    ports:
      # 不暴露到宿主机，仅内部服务访问
      # - "6379:6379"  ❌ 不要这样做
  
  fastapi:
    networks:
      - backend
    environment:
      - REDIS_URL=redis://redis:6379/0

networks:
  backend:
    internal: true  # 仅内部网络
```

### 4. 定期备份

```bash
# RDB 持久化（默认开启）
# 自动保存策略
save 900 1      # 900秒内1次修改
save 300 10     # 300秒内10次修改
save 60 10000   # 60秒内10000次修改

# AOF 持久化（更可靠）
appendonly yes
appendfsync everysec
```

---

## 监控与告警

### 关键指标

| 指标 | 正常范围 | 告警阈值 |
|------|---------|---------|
| 内存使用率 | < 80% | > 85% |
| 连接数 | < maxclients * 80% | > 90% |
| 命中率 | > 95% | < 90% |
| 慢查询 | < 10ms | > 50ms |
| 主从延迟 | < 1s | > 5s |

### Prometheus 监控

```yaml
# redis_exporter
services:
  redis-exporter:
    image: oliver006/redis_exporter:latest
    environment:
      - REDIS_ADDR=redis://redis:6379
    ports:
      - "9121:9121"
```

### 常用监控命令

```bash
# 查看内存使用
redis-cli INFO memory

# 查看连接数
redis-cli INFO clients

# 查看键数量
redis-cli DBSIZE

# 查看慢查询
redis-cli SLOWLOG GET 10

# 查看主从状态
redis-cli INFO replication
```

---

## 故障排查

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 连接超时 | 网络问题或 Redis 宕机 | 检查网络，启用重试机制 |
| 内存不足 | 数据量过大或 TTL 未设置 | 设置合理的 TTL，启用淘汰策略 |
| 主从延迟 | 网络带宽不足或主库压力大 | 优化网络，减少主库写压力 |
| 命中率低 | 缓存策略不当 | 优化缓存键设计，增加缓存时间 |

### 调试命令

```bash
# 测试连接
redis-cli -u redis://localhost:6379/0 PING

# 查看所有键（慎用，生产环境避免）
redis-cli KEYS 'hermes:session:*'

# 查看键的 TTL
redis-cli TTL hermes:session:web_abc123

# 查看键的内容
redis-cli GET hermes:session:web_abc123

# 实时监控
redis-cli MONITOR
```

---

## 总结

Redis 作为 Hermes Agent 的分布式会话存储，解决了多实例部署时的会话共享问题。通过合理配置连接池、序列化方式和部署架构，可以实现高性能、高可用的会话管理。在生产环境中，建议使用 Sentinel 或 Cluster 模式确保高可用，并配合监控告警及时发现和解决问题。

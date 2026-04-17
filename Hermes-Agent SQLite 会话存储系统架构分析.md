# Hermes Agent SQLite 会话存储系统架构分析

## 目录

- [1. 系统总览](#1-系统总览)
- [2. 软件架构图](#2-软件架构图)
- [3. 核心组件详解](#3-核心组件详解)
- [4. 数据库 Schema 设计](#4-数据库-schema-设计)
- [5. 业务流程图](#5-业务流程图)
- [6. 设计模式分析](#6-设计模式分析)
- [7. 关键代码索引](#7-关键代码索引)

---

## 1. 系统总览

Hermes Agent 的 SQLite 会话存储系统是一个**企业级、高并发、全文可搜索**的持久化层，替代了传统的 JSONL 文件存储方式。系统设计遵循**WAL 模式**、**FTS5 全文搜索**、**会话血缘链**等核心原则。

### 核心特性

| 特性 | 描述 |
|------|------|
| **WAL 模式** | Write-Ahead Logging，支持并发读写，避免写锁阻塞 |
| **FTS5 全文搜索** | 虚拟表 + 触发器，实现毫秒级消息搜索 |
| **会话血缘** | parent_session_id 链式结构，支持压缩后的会话延续 |
| **随机抖动重试** | 应用层 20-150ms 随机重试，避免写锁 convoy 效应 |
| **Schema 版本控制** | 6 版本迁移机制，支持平滑升级 |
| **PII 脱敏** | 敏感平台自动哈希用户/聊天 ID |

### 存储对比

| 存储方式 | 适用场景 | 特点 |
|----------|----------|------|
| **SQLite (SessionDB)** | CLI、Gateway 会话 | 结构化、可搜索、事务安全 |
| **JSONL (传统)** | 备份、导出、RL 轨迹 | 人类可读、易于分析 |
| **内存 (临时)** | 子代理、批量运行 | 高性能、不持久化 |

---

## 2. 软件架构图

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                 SQLite Session Storage 架构                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────── 应用层 ───────────────────────────┐   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │   CLI Agent  │  │   Gateway    │  │   ACP Adapter│      │   │
│  │  │  (run_agent) │  │  (gateway)   │  │   (VS Code)  │      │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │   │
│  │         │                 │                 │               │   │
│  │         └─────────────────┼─────────────────┘               │   │
│  │                           │                                 │   │
│  └───────────────────────────┼─────────────────────────────────┘   │
│                               │                                     │
│  ┌───────────────────────────┼──── 存储管理层 ────────────────────┘
│  │                           │
│  │  ┌────────────────────────▼──────────────────────────────┐   │
│  │  │              SessionStore (gateway/session.py)         │   │
│  │  │                                                          │   │
│  │  │  • Session key → ID 映射管理                              │   │
│  │  │  • 会话生命周期管理 (创建/恢复/过期/重置)                   │   │
│  │  │  • 重置策略评估 (idle/daily/none)                         │   │
│  │  │  • 动态系统提示注入 (build_session_context_prompt)        │   │
│  │  │  • PII 脱敏处理                                           │   │
│  │  └────────────────────────┬───────────────────────────────┘   │
│  │                           │                                    │
│  │  ┌────────────────────────▼──────────────────────────────┐   │
│  │  │              SessionDB (hermes_state.py)               │   │
│  │  │                                                          │   │
│  │  │  • SQLite 连接管理 (WAL 模式)                             │   │
│  │  │  • Schema 初始化和迁移 (v1→v6)                            │   │
│  │  │  • 写操作重试机制 (_execute_write)                        │   │
│  │  │  • FTS5 全文搜索索引                                      │   │
│  │  │  • 会话/消息 CRUD 操作                                    │   │
│  │  └────────────────────────┬───────────────────────────────┘   │
│  └───────────────────────────┼────────────────────────────────────┘
│                               │                                     │
│  ┌───────────────────────────┼──── 数据库层 ──────────────────────┘
│  │  ┌────────────────────────▼──────────────────────────────┐   │
│  │  │              SQLite Database (state.db)                │   │
│  │  │                                                          │   │
│  │  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │  │  Tables                                          │ │   │
│  │  │  │  • sessions (会话元数据)                          │ │   │
│  │  │  │  • messages (消息内容)                            │ │   │
│  │  │  │  • schema_version (版本控制)                      │ │   │
│  │  │  │  • messages_fts (FTS5 虚拟表)                     │ │   │
│  │  │  └──────────────────────────────────────────────────┘ │   │
│  │  │                                                          │   │
│  │  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │  │  Indexes                                         │ │   │
│  │  │  │  • idx_sessions_source (source 过滤)              │ │   │
│  │  │  │  • idx_sessions_parent (血缘查询)                 │ │   │
│  │  │  │  • idx_sessions_started (时间排序)                │ │   │
│  │  │  │  • idx_sessions_title_unique (标题唯一)           │ │   │
│  │  │  │  • idx_messages_session (会话消息查询)            │ │   │
│  │  │  └──────────────────────────────────────────────────┘ │   │
│  │  │                                                          │   │
│  │  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │  │  Triggers (FTS 同步)                             │ │   │
│  │  │  │  • messages_fts_insert (INSERT 后同步)            │ │   │
│  │  │  │  • messages_fts_delete (DELETE 后同步)            │ │   │
│  │  │  │  • messages_fts_update (UPDATE 后同步)            │ │   │
│  │  │  └──────────────────────────────────────────────────┘ │   │
│  │  └──────────────────────────────────────────────────────────┘   │
│  └─────────────────────────────────────────────────────────────────┘
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流架构

```
┌──────────────────────────────────────────────────────────────┐
│                    会话数据流                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 会话创建流程                                              │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ 用户消息 │ →  │ build_session│ →  │ SessionStore.       │  │
│  │         │    │ _key()       │    │ get_or_create_session│  │
│  └─────────┘    └─────────────┘    └──────────┬──────────┘  │
│                                               │              │
│                                               ▼              │
│                                        ┌─────────────┐      │
│                                        │ SessionDB.  │      │
│                                        │ create_session     │
│                                        └─────────────┘      │
│                                                              │
│  2. 消息追加流程                                              │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ Agent   │ →  │ append_to_  │ →  │ SessionDB.          │  │
│  │ 响应    │    │ transcript()│    │ append_message()    │  │
│  └─────────┘    └─────────────┘    └──────────┬──────────┘  │
│                                               │              │
│                                               ▼              │
│                                        ┌─────────────┐      │
│                                        │ 触发器自动   │      │
│                                        │ 同步 FTS5   │      │
│                                        └─────────────┘      │
│                                                              │
│  3. 会话恢复流程                                              │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ 会话Key │ →  │ SessionStore│ →  │ SessionDB.          │  │
│  │         │    │ .get_session│    │ get_messages_as_    │  │
│  └─────────┘    └─────────────┘    │ conversation()      │  │
│                                    └─────────────────────┘  │
│                                                              │
│  4. 搜索流程                                                  │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ 搜索词  │ →  │ _sanitize_  │ →  │ FTS5 MATCH 查询     │  │
│  │         │    │ fts5_query()│    │ + JOIN messages     │  │
│  └─────────┘    └─────────────┘    └─────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 核心组件详解

### 3.1 SessionDB - SQLite 存储引擎

**位置**: `hermes_state.py`

**核心职责**:
- SQLite 连接管理（WAL 模式、外键约束）
- Schema 初始化和版本迁移
- 写操作重试机制（随机抖动避免 convoy）
- 会话/消息的 CRUD 操作
- FTS5 全文搜索

#### 写操作重试机制

```python
class SessionDB:
    _WRITE_MAX_RETRIES = 15
    _WRITE_RETRY_MIN_S = 0.020   # 20ms
    _WRITE_RETRY_MAX_S = 0.150   # 150ms
    _CHECKPOINT_EVERY_N_WRITES = 50

    def _execute_write(self, fn: Callable) -> T:
        """Execute a write transaction with BEGIN IMMEDIATE and jitter retry."""
        for attempt in range(self._WRITE_MAX_RETRIES):
            try:
                with self._lock:
                    self._conn.execute("BEGIN IMMEDIATE")
                    result = fn(self._conn)
                    self._conn.commit()
                
                # Periodic WAL checkpoint
                self._write_count += 1
                if self._write_count % self._CHECKPOINT_EVERY_N_WRITES == 0:
                    self._try_wal_checkpoint()
                return result
                
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc).lower():
                    # Random jitter to break convoy pattern
                    jitter = random.uniform(
                        self._WRITE_RETRY_MIN_S,
                        self._WRITE_RETRY_MAX_S,
                    )
                    time.sleep(jitter)
                    continue
                raise
```

**设计要点**:
- `BEGIN IMMEDIATE` 在事务开始时获取写锁，而非提交时
- 随机抖动（20-150ms）避免多个进程同时重试造成的 convoy 效应
- 每 50 次写操作触发一次 PASSIVE WAL checkpoint，防止 WAL 文件无限增长

### 3.2 SessionStore - 会话管理层

**位置**: `gateway/session.py`

**核心职责**:
- Session key → ID 映射管理（内存索引 + JSON 文件）
- 会话生命周期管理（创建/恢复/过期/重置）
- 重置策略评估（idle/daily/none）
- 动态系统提示注入
- PII 脱敏处理

#### 会话 Key 构建规则

```python
def build_session_key(source: SessionSource, ...) -> str:
    """构建确定性会话 Key"""
    
    # DM 规则:
    # - 包含 chat_id，每个私聊隔离
    # - thread_id 进一步区分线程内 DM
    if source.chat_type == "dm":
        if source.chat_id:
            if source.thread_id:
                return f"agent:main:{platform}:dm:{chat_id}:{thread_id}"
            return f"agent:main:{platform}:dm:{chat_id}"
    
    # 群组/频道规则:
    # - chat_id 标识父群组
    # - user_id 隔离参与者（当 group_sessions_per_user=True）
    # - thread_id 区分线程（默认共享，不隔离用户）
    key_parts = ["agent:main", platform, chat_type]
    if chat_id:
        key_parts.append(chat_id)
    if thread_id:
        key_parts.append(thread_id)
    if isolate_user and participant_id:
        key_parts.append(str(participant_id))
    
    return ":".join(key_parts)
```

### 3.3 SessionSource - 消息来源追踪

```python
@dataclass
class SessionSource:
    platform: Platform          # telegram, discord, slack, etc.
    chat_id: str               # 聊天 ID
    chat_name: Optional[str]   # 聊天名称
    chat_type: str             # dm, group, channel, thread
    user_id: Optional[str]     # 用户 ID
    user_name: Optional[str]   # 用户名称
    thread_id: Optional[str]   # 线程/话题 ID
    chat_topic: Optional[str]  # 频道主题/描述
```

---

## 4. 数据库 Schema 设计

### 4.1 表结构

```sql
-- 版本控制表
CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

-- 会话表
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,                    -- cli, telegram, discord, etc.
    user_id TEXT,
    model TEXT,
    model_config TEXT,                       -- JSON
    system_prompt TEXT,
    parent_session_id TEXT,                  -- 血缘链
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    billing_base_url TEXT,
    billing_mode TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    cost_status TEXT,
    cost_source TEXT,
    pricing_version TEXT,
    title TEXT,                              -- 唯一（非 NULL）
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
);

-- 消息表
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,                      -- system, user, assistant, tool
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,                         -- JSON
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,                          -- v6 新增
    reasoning_details TEXT,                  -- JSON, v6 新增
    codex_reasoning_items TEXT               -- JSON, v6 新增
);

-- FTS5 虚拟表（全文搜索）
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);
```

### 4.2 索引设计

```sql
-- 会话索引
CREATE INDEX idx_sessions_source ON sessions(source);
CREATE INDEX idx_sessions_parent ON sessions(parent_session_id);
CREATE INDEX idx_sessions_started ON sessions(started_at DESC);
CREATE UNIQUE INDEX idx_sessions_title_unique ON sessions(title) WHERE title IS NOT NULL;

-- 消息索引
CREATE INDEX idx_messages_session ON messages(session_id, timestamp);
```

### 4.3 FTS5 触发器

```sql
-- INSERT 后同步到 FTS
CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

-- DELETE 后从 FTS 移除
CREATE TRIGGER messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) 
    VALUES('delete', old.id, old.content);
END;

-- UPDATE 后重新索引
CREATE TRIGGER messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) 
    VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
```

### 4.4 Schema 迁移历史

| 版本 | 变更内容 |
|------|----------|
| v1 | 初始 Schema（sessions, messages, messages_fts） |
| v2 | messages 表添加 finish_reason 列 |
| v3 | sessions 表添加 title 列 |
| v4 | 添加 idx_sessions_title_unique 唯一索引 |
| v5 | 添加计费相关列（cache_*_tokens, billing_*, cost_*） |
| v6 | 添加推理相关列（reasoning, reasoning_details, codex_reasoning_items） |

---

## 5. 业务流程图

### 5.1 会话生命周期流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     会话生命周期                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐                                                    │
│  │  用户消息 │                                                    │
│  └────┬─────┘                                                    │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────┐                                            │
│  │ build_session_key│                                            │
│  │ (source → key)   │                                            │
│  └────────┬─────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐                                            │
│  │ 检查现有会话      │                                            │
│  │ _entries[key]    │                                            │
│  └────────┬─────────┘                                            │
│           │                                                      │
│     ┌─────┴─────┐                                                │
│     │           │                                                │
│     ▼           ▼                                                │
│  存在          不存在                                             │
│     │           │                                                │
│     ▼           ▼                                                │
│ ┌──────────┐ ┌──────────────┐                                    │
│ │检查过期  │ │ create_session│                                   │
│ │策略      │ │ (新会话)      │                                   │
│ └────┬─────┘ └──────────────┘                                    │
│      │                                                           │
│ ┌────┴────┐                                                      │
│ │         │                                                      │
│ ▼         ▼                                                      │
│ 过期      未过期                                                  │
│  │         │                                                      │
│  ▼         ▼                                                      │
│ reset    恢复会话                                                 │
│ _session │                                                       │
│ (新ID)   │                                                       │
│          ▼                                                       │
│     ┌────────────┐                                               │
│     │ 返回会话ID  │                                               │
│     └─────┬──────┘                                               │
│           │                                                      │
│           ▼                                                      │
│     ┌────────────┐                                               │
│     │ Agent Loop  │                                              │
│     │ 执行对话    │                                              │
│     └─────┬──────┘                                               │
│           │                                                      │
│           ▼                                                      │
│     ┌────────────┐                                               │
│     │ end_session │                                              │
│     │ (标记结束)  │                                              │
│     └────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 消息搜索流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     FTS5 搜索流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  输入: query="docker deployment"                                 │
│                                                                  │
│  Step 1: 查询清理 (_sanitize_fts5_query)                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • 保留引号短语: "exact phrase"                           │    │
│  │ • 移除特殊字符: +{}()"^                                  │    │
│  │ • 处理布尔操作符: AND/OR/NOT                             │    │
│  │ • 引号包裹带点/横线的词: "my-app.config"                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  Step 2: FTS5 MATCH 查询                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ SELECT ... FROM messages_fts                            │    │
│  │ JOIN messages m ON m.id = messages_fts.rowid            │    │
│  │ JOIN sessions s ON s.id = m.session_id                  │    │
│  │ WHERE messages_fts MATCH ?                              │    │
│  │ ORDER BY rank                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  Step 3: 添加上下文                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 对于每个匹配消息:                                        │    │
│  │ • 查询前一条消息 (id - 1)                                │    │
│  │ • 查询后一条消息 (id + 1)                                │    │
│  │ • 组装 context 字段                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  输出: 匹配消息列表（含高亮片段和上下文）                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 PII 脱敏流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     PII 脱敏处理                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  输入: SessionSource (platform, user_id, chat_id, ...)          │
│                                                                  │
│  Step 1: 检查平台类型                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ _PII_SAFE_PLATFORMS = {                                 │    │
│  │     WHATSAPP, SIGNAL, TELEGRAM, BLUEBUBBLES            │    │
│  │ }                                                       │    │
│  │                                                         │    │
│  │ Discord 除外（需要原始 ID 进行 @提及）                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│              ┌────────────┴────────────┐                         │
│              │                         │                         │
│              ▼                         ▼                         │
│        安全平台                    不安全平台                     │
│              │                         │                         │
│              ▼                         ▼                         │
│  Step 2: 哈希处理                                          直通  │
│  ┌────────────────────────────────┐    ┌─────────────────────┐  │
│  │ user_id → user_<12hex_hash>    │    │ 保持原始值          │  │
│  │ chat_id → <12hex_hash>         │    │                     │  │
│  │                                │    │                     │  │
│  │ 哈希算法: SHA256 前 12 字符    │    │                     │  │
│  └────────────────────────────────┘    └─────────────────────┘  │
│                                                                  │
│  注意: 路由仍使用原始值，仅 LLM 可见部分脱敏                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. 设计模式分析

### 6.1 数据访问对象模式 (DAO)

**SessionDB** 作为数据访问对象，封装所有数据库操作：

```python
class SessionDB:
    # CRUD 操作
    def create_session(self, ...): ...
    def get_session(self, session_id): ...
    def update_token_counts(self, ...): ...
    def delete_session(self, session_id): ...
    
    # 查询操作
    def get_messages(self, session_id): ...
    def search_messages(self, query): ...
    def list_sessions_rich(self, ...): ...
```

### 6.2 仓储模式 (Repository)

**SessionStore** 作为仓储层，提供领域对象（SessionEntry）的持久化：

```python
class SessionStore:
    def get_or_create_session(self, source) -> SessionEntry: ...
    def get_session(self, key) -> Optional[SessionEntry]: ...
    def update_session(self, entry: SessionEntry): ...
```

### 6.3 策略模式 (Strategy)

**会话重置策略**支持多种过期策略：

```python
class SessionResetPolicy:
    mode: str  # "idle", "daily", "none"
    idle_minutes: int  # 空闲超时
    
# 策略评估
policy = config.get_reset_policy(platform, session_type)
if policy.mode == "idle":
    expired = (now - entry.updated_at) > idle_timeout
elif policy.mode == "daily":
    expired = entry.created_at.date() != today
```

### 6.4 工厂模式 (Factory)

**会话 Key 构建**根据来源类型创建不同的 Key：

```python
def build_session_key(source: SessionSource, ...) -> str:
    if source.chat_type == "dm":
        return build_dm_key(source)
    else:
        return build_group_key(source, group_sessions_per_user)
```

### 6.5 观察者模式 (Observer)

**FTS5 触发器**作为数据库级观察者：

```sql
-- messages 表变更时自动同步到 messages_fts
CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages ...
CREATE TRIGGER messages_fts_delete AFTER DELETE ON messages ...
CREATE TRIGGER messages_fts_update AFTER UPDATE ON messages ...
```

### 6.6 重试模式 (Retry)

**写操作重试**带随机抖动：

```python
def _execute_write(self, fn):
    for attempt in range(max_retries):
        try:
            return fn()
        except Locked:
            time.sleep(random.uniform(20ms, 150ms))  # 抖动
    raise MaxRetriesExceeded
```

---

## 7. 关键代码索引

### 7.1 核心文件

| 文件路径 | 功能 | 关键类/函数 |
|----------|------|-------------|
| `hermes_state.py` | SQLite 存储引擎 | `SessionDB` |
| `gateway/session.py` | 会话管理层 | `SessionStore`, `SessionEntry` |
| `gateway/session.py` | 会话 Key 构建 | `build_session_key()` |
| `gateway/session.py` | 系统提示构建 | `build_session_context_prompt()` |
| `acp_adapter/session.py` | ACP 会话管理 | `SessionManager` |

### 7.2 SessionDB 关键方法

| 方法 | 位置 | 描述 |
|------|------|------|
| `_execute_write()` | `hermes_state.py:164` | 带重试的写操作执行 |
| `_init_schema()` | `hermes_state.py:252` | Schema 初始化和迁移 |
| `create_session()` | `hermes_state.py:355` | 创建新会话 |
| `append_message()` | `hermes_state.py:791` | 追加消息并更新计数器 |
| `get_messages_as_conversation()` | `hermes_state.py:886` | 加载 OpenAI 格式对话 |
| `search_messages()` | `hermes_state.py:990` | FTS5 全文搜索 |
| `set_session_title()` | `hermes_state.py:606` | 设置会话标题（唯一约束） |
| `prune_sessions()` | `hermes_state.py:1199` | 清理过期会话 |

### 7.3 SessionStore 关键方法

| 方法 | 位置 | 描述 |
|------|------|------|
| `get_or_create_session()` | `gateway/session.py:683` | 获取或创建会话 |
| `reset_session()` | `gateway/session.py:824` | 强制重置会话 |
| `append_to_transcript()` | `gateway/session.py:941` | 追加消息到转录 |
| `load_transcript()` | `gateway/session.py:1001` | 加载会话历史 |
| `build_session_context()` | `gateway/session.py:1050` | 构建会话上下文 |

### 7.4 配置选项

```yaml
# ~/.hermes/config.yaml
gateway:
  session_reset_policy:
    default:
      mode: "idle"  # idle, daily, none
      idle_minutes: 240
    
  group_sessions_per_user: true   # 群组内按用户隔离
  thread_sessions_per_user: false # 线程内共享会话
```

---

## 附录：性能优化建议

### WAL 模式调优

```sql
-- 自动检查点（每 1000 页）
PRAGMA wal_autocheckpoint = 1000;

-- 同步模式（NORMAL 平衡性能和安全）
PRAGMA synchronous = NORMAL;

-- 缓存大小（20000 页 ≈ 80MB）
PRAGMA cache_size = -20000;
```

### 查询优化

```sql
-- 使用覆盖索引查询
SELECT id, source, model FROM sessions 
WHERE source = 'telegram' 
ORDER BY started_at DESC;

-- 避免 SELECT *，只查询需要的列
```

---

**文档版本**: v1.0  
**最后更新**: 2024  
**维护者**: Hermes Agent Team

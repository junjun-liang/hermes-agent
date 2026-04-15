# Hermes-Agent 记忆系统架构详解

> 分析日期：2026-04-14 | 核心文件：`tools/memory_tool.py`（557 行）、`agent/memory_manager.py`（362 行） | 插件目录：`plugins/memory/`（8 个插件）

---

## 目录

1. [记忆系统架构总览](#1-记忆系统架构总览)
2. [核心组件详解](#2-核心组件详解)
3. [记忆插件架构](#3-记忆插件架构)
4. [记忆操作流程](#4-记忆操作流程)
5. [记忆持久化机制](#5-记忆持久化机制)
6. [记忆与安全机制](#6-记忆与安全机制)
7. [记忆系统的设计模式](#7-记忆系统的设计模式)
8. [架构决策与权衡](#8-架构决策与权衡)

---

## 1. 记忆系统架构总览

### 1.1 设计目标

Hermes-Agent 的记忆系统旨在提供**持久化、可搜索、可扩展**的长期记忆能力，主要解决以下问题：

| 问题 | 风险 | 记忆系统解决方案 |
|------|------|------------------|
| **上下文窗口限制** | LLM 上下文有限，无法记住所有历史 | 选择性记忆（重要信息写入 MEMORY.md） |
| **跨会话遗忘** | 会话结束后记忆丢失 | 持久化存储（文件/数据库/云存储） |
| **记忆检索困难** | 无法快速找到相关记忆 | 全文搜索（FTS5）、向量检索（插件） |
| **记忆污染** | 错误/过时信息污染记忆 | 记忆替换、删除、版本控制 |
| **隐私泄露** | 敏感信息写入记忆 | 脱敏处理、访问控制、隔离机制 |

### 1.2 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    用户层（LLM 调用）                         │
│  memory(action="add", content="用户喜欢 Python 编程")         │
│  memory(action="search", query="编程偏好")                   │
│  memory(action="replace", old="Python", new="Python + Rust") │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  工具层（tools/memory_tool.py）               │
│  - MemoryStore 类（文件级记忆存储）                          │
│  - 记忆操作：add, replace, remove, search                   │
│  - 字符限制检查、去重、格式化                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  管理层（agent/memory_manager.py）            │
│  - MemoryManager 类（协调多个记忆提供者）                    │
│  - 提供者注册：内置 MemoryStore + 插件提供者                 │
│  - 系统提示构建、上下文预取、同步                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  插件层（plugins/memory/*）                   │
│  - SuperMemory：语义搜索 + 向量嵌入                          │
│  - RetainDB：数据库持久化 + 版本控制                         │
│  - OpenViking：开源向量数据库                                │
│  - Mem0：云记忆服务                                          │
│  - Honcho：用户级记忆隔离                                    │
│  - Holographic：全息记忆（多维度检索）                       │
│  - Hindsight：事后记忆（会话结束总结）                       │
│  - Byterover：字节级记忆（二进制数据）                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  存储层（多种后端）                           │
│  - 文件存储：~/.hermes/memories/MEMORY.md                   │
│  - SQLite：hermes_state.db（会话消息 + FTS5）               │
│  - 云存储：各插件的远程数据库（Supabase、Pinecone 等）        │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心特性

| 特性 | 实现方式 | 安全价值 |
|------|----------|----------|
| **多提供者架构** | MemoryManager 协调内置 Store + 插件提供者 | 灵活扩展，不锁定单一后端 |
| **选择性记忆** | LLM 决定写入内容（非全量历史） | 减少记忆污染，提高质量 |
| **全文搜索** | SQLite FTS5 + 插件向量检索 | 快速定位相关记忆 |
| **字符限制** | MemoryStore 默认 10KB 上限 | 防止记忆膨胀 |
| **去重机制** | 添加前检查重复条目 | 避免冗余记忆 |
| **系统提示注入** | 记忆内容冻结快照注入到 system prompt | LLM 可直接访问记忆 |
| **插件扩展** | 8 个记忆插件（向量、数据库、云存储） | 满足不同场景需求 |

---

## 2. 核心组件详解

### 2.1 MemoryStore 类（文件级记忆存储）

**核心文件**：[tools/memory_tool.py](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/memory_tool.py)

**职责**：提供基于文件的记忆存储，支持添加、替换、删除、搜索操作。

**数据结构**：
```python
# ~/.hermes/memories/MEMORY.md 格式
# ================================================================
# Hermes Agent Memory
# ================================================================

- 用户喜欢 Python 编程
- 用户的工作目录是 /home/user/projects
- 用户偏好使用 PostgreSQL 数据库
- 用户的公司名称为 Acme Corp
```

**核心方法**：

```python
class MemoryStore:
    def __init__(self, path: Path, max_chars: int = 10000):
        self.path = path
        self.max_chars = max_chars
        self._entries: List[str] = []
        self._load()  # 从文件加载记忆
    
    def _load(self):
        """从文件加载记忆条目"""
        if self.path.exists():
            content = self.path.read_text(encoding="utf-8")
            # 解析 Markdown 格式（忽略注释和标题）
            self._entries = [
                line.strip()[2:]  # 移除 "- " 前缀
                for line in content.splitlines()
                if line.strip().startswith("- ")
            ]
    
    def add(self, content: str) -> Tuple[bool, str]:
        """添加记忆条目"""
        # 1. 检查重复
        if content in self._entries:
            return False, "Entry already exists"
        
        # 2. 检查字符限制
        current_chars = sum(len(e) for e in self._entries)
        if current_chars + len(content) > self.max_chars:
            return False, f"Memory limit exceeded ({self.max_chars} chars)"
        
        # 3. 添加条目
        self._entries.append(content)
        self._save()
        return True, "Entry added"
    
    def replace(self, old_content: str, new_content: str) -> Tuple[bool, str]:
        """替换记忆条目（子字符串匹配）"""
        # 1. 查找匹配条目
        matched = [e for e in self._entries if old_content in e]
        if not matched:
            return False, "No matching entry found"
        
        # 2. 检查字符限制
        current_chars = sum(len(e) for e in self._entries)
        delta = len(new_content) - sum(len(m) for m in matched)
        if current_chars + delta > self.max_chars:
            return False, f"Memory limit exceeded after replacement"
        
        # 3. 替换条目
        self._entries = [
            e.replace(old_content, new_content) if old_content in e else e
            for e in self._entries
        ]
        self._save()
        return True, "Entry replaced"
    
    def remove(self, content: str) -> Tuple[bool, str]:
        """删除记忆条目（子字符串匹配）"""
        # 1. 查找匹配条目
        matched = [e for e in self._entries if content in e]
        if not matched:
            return False, "No matching entry found"
        
        # 2. 删除条目
        self._entries = [e for e in self._entries if content not in e]
        self._save()
        return True, "Entry removed"
    
    def search(self, query: str) -> List[str]:
        """搜索记忆条目（子字符串匹配）"""
        return [e for e in self._entries if query.lower() in e.lower()]
    
    def format_for_system_prompt(self) -> str:
        """格式化为系统提示注入的冻结快照"""
        if not self._entries:
            return "No memories stored."
        
        return "\n".join(f"- {entry}" for entry in self._entries)
    
    def _save(self):
        """保存记忆到文件"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = "# ================================================================\n"
        content += "# Hermes Agent Memory\n"
        content += "# ================================================================\n\n"
        content += "\n".join(f"- {entry}" for entry in self._entries)
        content += "\n"
        
        # 原子写入
        fd, tmp_path = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, str(self.path))
```

**使用示例**：
```python
store = MemoryStore(Path.home() / ".hermes" / "memories" / "MEMORY.md")

# 添加记忆
success, msg = store.add("用户喜欢 Python 编程")
# → (True, "Entry added")

# 搜索记忆
results = store.search("Python")
# → ["用户喜欢 Python 编程"]

# 替换记忆
success, msg = store.replace("Python", "Python + Rust")
# → (True, "Entry replaced")

# 格式化输出（系统提示注入）
memory_text = store.format_for_system_prompt()
# → "- 用户喜欢 Python + Rust 编程"
```

### 2.2 MemoryManager 类（记忆管理器）

**核心文件**：[agent/memory_manager.py](file:///home/meizu/Documents/my_agent_project/hermes-agent/agent/memory_manager.py)

**职责**：协调多个记忆提供者（内置 MemoryStore + 插件提供者），统一管理接口。

**核心架构**：
```python
class MemoryManager:
    def __init__(self, platform: str = None):
        self.platform = platform
        self._providers: Dict[str, Any] = {}
        self._memory_store: Optional[MemoryStore] = None
        self._context_cache: Dict[str, str] = {}  # 预取上下文缓存
    
    def register_provider(self, name: str, provider: Any):
        """注册记忆提供者"""
        self._providers[name] = provider
    
    def unregister_provider(self, name: str):
        """注销记忆提供者"""
        self._providers.pop(name, None)
    
    @property
    def provider_names(self) -> List[str]:
        """返回所有已注册的提供者名称"""
        return list(self._providers.keys())
    
    def prefetch_all(self) -> Dict[str, str]:
        """从所有提供者预取上下文"""
        contexts = {}
        for name, provider in self._providers.items():
            try:
                context = provider.get_context()
                contexts[name] = context
            except Exception as e:
                contexts[name] = f"Error loading context: {e}"
        self._context_cache = contexts
        return contexts
    
    def build_system_prompt(self) -> str:
        """构建系统提示（包含所有记忆提供者的上下文）"""
        sections = []
        
        # 1. 内置 MemoryStore 记忆
        if self._memory_store:
            sections.append("## Memories\n\n" + self._memory_store.format_for_system_prompt())
        
        # 2. 插件提供者上下文
        for name, context in self._context_cache.items():
            if context and not context.startswith("Error"):
                sections.append(f"## {name} Context\n\n{context}")
        
        return "\n\n".join(sections) if sections else ""
    
    def sync_all(self, conversation_turn: int):
        """同步一次完整的转接到所有提供者"""
        for provider in self._providers.values():
            try:
                provider.sync(conversation_turn)
            except Exception as e:
                logger.warning("Failed to sync provider %s: %s", provider, e)
    
    def handle_tool_call(self, tool_name: str, args: dict) -> str:
        """处理记忆工具调用（路由到正确的提供者）"""
        # 仅 MemoryStore 处理工具调用
        if self._memory_store:
            return self._memory_store.handle_tool_call(tool_name, args)
        return json.dumps({"error": "Memory provider not available"})
```

**记忆提供者接口**：
```python
class IMemoryProvider(Protocol):
    """记忆提供者接口（插件需实现）"""
    
    def get_context(self) -> str:
        """获取上下文（用于系统提示注入）"""
        ...
    
    def sync(self, conversation_turn: int):
        """同步对话转记到提供者"""
        ...
    
    def handle_tool_call(self, tool_name: str, args: dict) -> str:
        """处理工具调用（可选实现）"""
        ...
```

### 2.3 SQLite 会话存储（FTS5 全文搜索）

**核心文件**：[hermes_state.py](file:///home/meizu/Documents/my_agent_project/hermes-agent/hermes_state.py)

**职责**：持久化会话消息，支持 FTS5 全文搜索（可视为"隐式记忆"）。

**表结构**：
```sql
-- 会话表
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT,              -- 来源（cli, telegram, discord...）
    user_id TEXT,
    model TEXT,
    started_at REAL,
    ended_at REAL,
    title TEXT,               -- 会话标题（LLM 生成）
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0
);

-- 消息表
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,                -- system/user/assistant/tool
    content TEXT,
    timestamp REAL,
    tool_call_id TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- FTS5 虚拟表（全文搜索）
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content='messages',
    content_rowid='id'
);

-- 触发器（自动同步 FTS 索引）
CREATE TRIGGER messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (NEW.id, NEW.content);
END;
```

**搜索方法**：
```python
class SessionDB:
    def search_messages(self, query: str, limit: int = 20) -> List[dict]:
        """使用 FTS5 搜索会话消息"""
        # 1. 清理 FTS5 查询（防止语法错误）
        sanitized_query = self._sanitize_fts5_query(query)
        
        # 2. 执行 FTS5 搜索
        sql = """
            SELECT m.id, m.session_id, m.role, m.content, m.timestamp,
                   s.title as session_title
            FROM messages m
            JOIN sessions s ON m.session_id = s.id
            WHERE m.id IN (
                SELECT rowid FROM messages_fts 
                WHERE content MATCH ?
            )
            ORDER BY m.timestamp DESC
            LIMIT ?
        """
        cursor = self._conn.execute(sql, (sanitized_query, limit))
        
        # 3. 返回结果
        return [
            {
                "id": row[0],
                "session_id": row[1],
                "role": row[2],
                "content": row[3],
                "timestamp": row[4],
                "session_title": row[5]
            }
            for row in cursor.fetchall()
        ]
```

**FTS5 查询清理**：
```python
@staticmethod
def _sanitize_fts5_query(query: str) -> str:
    """清理用户输入以安全用于 FTS5 MATCH 查询"""
    # 1. 提取并保护成对的双引号短语
    quoted_phrases = re.findall(r'"[^"]*"', query)
    for i, phrase in enumerate(quoted_phrases):
        query = query.replace(phrase, f"__QUOTED_PHRASE_{i}__")
    
    # 2. 剥离未匹配的 FTS5 特殊字符（+ - & | ! ( ) { } " ^）
    sanitized = re.sub(r'[+\-&|!(){}"^]', " ", query)
    
    # 3. 折叠重复的 * 为单个 *
    sanitized = re.sub(r'\*+', '*', sanitized)
    
    # 4. 移除悬空的布尔运算符
    sanitized = re.sub(r'\b(AND|OR|NOT)\b', " ", sanitized, flags=re.IGNORECASE)
    
    # 5. 包装未引用的带点号/连字符的术语
    sanitized = re.sub(r'(\b\w+\.\w+\b|\b\w+-\w+\b)', r'"\1"', sanitized)
    
    # 6. 恢复受保护的引号短语
    for i, phrase in enumerate(quoted_phrases):
        sanitized = sanitized.replace(f"__QUOTED_PHRASE_{i}__", phrase)
    
    return sanitized
```

---

## 3. 记忆插件架构

### 3.1 插件目录结构

```
plugins/memory/
├── __init__.py              # 插件发现机制
├── supermemory/
│   ├── __init__.py          # SuperMemory 插件（语义搜索 + 向量嵌入）
│   └── ...
├── retaindb/
│   ├── __init__.py          # RetainDB 插件（数据库持久化 + 版本控制）
│   └── ...
├── openviking/
│   ├── __init__.py          # OpenViking 插件（开源向量数据库）
│   └── ...
├── mem0/
│   ├── __init__.py          # Mem0 插件（云记忆服务）
│   └── ...
├── honcho/
│   ├── __init__.py          # Honcho 插件（用户级记忆隔离）
│   └── ...
├── holographic/
│   ├── __init__.py          # Holographic 插件（全息记忆）
│   └── ...
├── hindsight/
│   ├── __init__.py          # Hindsight 插件（事后记忆）
│   └── ...
└── byterover/
    ├── __init__.py          # Byterover 插件（字节级记忆）
    └── ...
```

### 3.2 插件发现机制

```python
# plugins/memory/__init__.py

def discover_memory_providers() -> Dict[str, Any]:
    """发现所有可用的记忆提供者插件"""
    providers = {}
    memory_dir = Path(__file__).parent
    
    for plugin_dir in memory_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
        if not (plugin_dir / "__init__.py").exists():
            continue
        
        try:
            # 导入插件模块
            module = importlib.import_module(f"plugins.memory.{plugin_dir.name}")
            
            # 查找提供者类
            if hasattr(module, "MemoryProvider"):
                provider_class = getattr(module, "MemoryProvider")
                provider_instance = provider_class()
                providers[plugin_dir.name] = provider_instance
            
        except Exception as e:
            logger.warning("Failed to load memory plugin %s: %s", plugin_dir.name, e)
    
    return providers
```

### 3.3 插件示例：SuperMemory

```python
# plugins/memory/supermemory/__init__.py

from typing import List, Dict, Any
import hashlib
from dataclasses import dataclass

@dataclass
class Memory:
    content: str
    embedding: List[float]  # 向量嵌入
    timestamp: float
    tags: List[str]

class MemoryProvider:
    def __init__(self):
        self._memories: List[Memory] = []
        self._index = None  # 向量索引（FAISS、Annoy 等）
    
    def get_context(self) -> str:
        """获取上下文（返回最近的记忆）"""
        if not self._memories:
            return "No memories."
        
        # 返回最近的 5 条记忆
        recent = sorted(self._memories, key=lambda m: m.timestamp, reverse=True)[:5]
        return "\n".join(f"- {m.content}" for m in recent)
    
    def add_memory(self, content: str, tags: List[str] = None):
        """添加记忆（生成向量嵌入）"""
        # 生成向量嵌入（使用预训练模型）
        embedding = self._generate_embedding(content)
        
        memory = Memory(
            content=content,
            embedding=embedding,
            timestamp=time.time(),
            tags=tags or []
        )
        self._memories.append(memory)
        
        # 重建索引
        self._rebuild_index()
    
    def search(self, query: str, limit: int = 5) -> List[Memory]:
        """语义搜索（向量相似度）"""
        query_embedding = self._generate_embedding(query)
        
        # 计算余弦相似度
        similarities = [
            (memory, self._cosine_similarity(query_embedding, memory.embedding))
            for memory in self._memories
        ]
        
        # 返回最相似的 limit 条记忆
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, _ in similarities[:limit]]
    
    def sync(self, conversation_turn: int):
        """同步对话转记（提取关键信息）"""
        # 从对话中提取关键信息（LLM 辅助）
        # ...
        pass
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成向量嵌入（使用 sentence-transformers）"""
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode(text)
        return embedding.tolist()
    
    def _rebuild_index(self):
        """重建向量索引（FAISS）"""
        import faiss
        import numpy as np
        
        if not self._memories:
            self._index = None
            return
        
        embeddings = np.array([m.embedding for m in self._memories], dtype=np.float32)
        self._index = faiss.IndexFlatL2(embeddings.shape[1])
        self._index.add(embeddings)
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        import numpy as np
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### 3.4 插件对比

| 插件 | 存储后端 | 检索方式 | 适用场景 |
|------|----------|----------|----------|
| **SuperMemory** | 内存 + FAISS 索引 | 向量相似度（语义搜索） | 语义检索、模糊匹配 |
| **RetainDB** | SQLite/PostgreSQL | SQL 查询 + 版本控制 | 结构化记忆、审计需求 |
| **OpenViking** | 开源向量数据库 | 向量检索 | 大规模记忆库 |
| **Mem0** | 云服务（Supabase） | REST API + 向量检索 | 云同步、多设备共享 |
| **Honcho** | 用户隔离数据库 | 用户 ID 过滤 | 多用户场景、隐私隔离 |
| **Holographic** | 多维度索引 | 多维度检索（时间、标签、内容） | 复杂检索场景 |
| **Hindsight** | 会话总结存储 | 会话结束触发 | 事后复盘、经验总结 |
| **Byterover** | 二进制存储 | 字节级检索 | 非文本记忆（图片、音频） |

---

## 4. 记忆操作流程

### 4.1 记忆添加流程

```
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: LLM 决定写入记忆                                     │
│  用户说："我喜欢 Python 编程，尤其是数据科学领域"              │
│  LLM 决定：这条信息重要，应写入记忆                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: LLM 调用 memory 工具                                 │
│  memory(                                                    │
│      action="add",                                          │
│      content="用户喜欢 Python 编程，尤其是数据科学领域"         │
│  )                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: MemoryManager 路由到 MemoryStore                    │
│  memory_manager.handle_tool_call("memory", args)            │
│  → MemoryStore.add(content)                                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: MemoryStore 执行添加                                 │
│  1. 检查重复（content in _entries）→ 否                     │
│  2. 检查字符限制（current_chars + len(content) <= max）→ 是 │
│  3. 添加到 _entries 列表                                    │
│  4. 调用 _save() 保存到文件                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: 原子写入文件                                         │
│  1. 写入临时文件：MEMORY.md.tmp.<pid>                       │
│  2. fsync 确保数据落盘                                       │
│  3. os.replace() 原子替换                                    │
│  4. 文件权限：0600（仅所有者可读写）                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 6: 返回结果给 LLM                                       │
│  {"success": true, "message": "Entry added"}                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 7: 下次对话时注入系统提示                               │
│  system_prompt = memory_manager.build_system_prompt()       │
│  → "## Memories\n\n- 用户喜欢 Python 编程，尤其是数据科学领域"  │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 记忆搜索流程

```
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: LLM 需要检索相关记忆                                  │
│  用户问："我平时喜欢用什么编程语言？"                         │
│  LLM 决定：搜索记忆获取答案                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: LLM 调用 memory 工具                                 │
│  memory(action="search", query="编程语言")                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: MemoryStore 执行搜索                                 │
│  results = store.search("编程语言")                         │
│  → ["用户喜欢 Python 编程，尤其是数据科学领域"]                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 返回搜索结果给 LLM                                   │
│  {                                                          │
│      "success": true,                                       │
│      "results": ["用户喜欢 Python 编程，尤其是数据科学领域"],  │
│      "count": 1                                             │
│  }                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: LLM 整合记忆回答问题                                 │
│  "根据记忆，您平时喜欢使用 Python 编程语言，尤其是数据科学领域。"│
└─────────────────────────────────────────────────────────────┘
```

### 4.3 记忆替换流程

```
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: 用户更新偏好                                         │
│  用户说："我现在更喜欢用 Rust 做系统编程，Python 做数据科学"    │
│  LLM 决定：更新记忆中的编程语言偏好                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: LLM 调用 memory 工具                                 │
│  memory(                                                    │
│      action="replace",                                      │
│      old="用户喜欢 Python 编程",                              │
│      new="用户喜欢 Python 做数据科学，Rust 做系统编程"         │
│  )                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: MemoryStore 执行替换                                 │
│  1. 查找匹配条目：old_content in e → 找到                    │
│  2. 检查字符限制：current_chars + delta <= max → 是         │
│  3. 替换条目：e.replace(old_content, new_content)           │
│  4. 调用 _save() 保存到文件                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 原子写入文件（同添加流程）                           │
│  临时文件 → fsync → os.replace() → 0600 权限                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: 返回结果给 LLM                                       │
│  {"success": true, "message": "Entry replaced"}             │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 记忆删除流程

```
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: 用户要求删除记忆                                     │
│  用户说："请删除关于我工作目录的记忆，我已经换工作了"          │
│  LLM 决定：删除相关工作目录记忆                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: LLM 调用 memory 工具                                 │
│  memory(action="remove", content="工作目录")                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: MemoryStore 执行删除                                 │
│  1. 查找匹配条目：content in e → 找到                        │
│  2. 过滤删除：_entries = [e for e in _entries if ...]       │
│  3. 调用 _save() 保存到文件                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 原子写入文件（同添加流程）                           │
│  临时文件 → fsync → os.replace() → 0600 权限                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: 返回结果给 LLM                                       │
│  {"success": true, "message": "Entry removed"}              │
└─────────────────────────────────────────────────────────────┘
```

### 4.5 系统提示注入流程

```
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: AIAgent 初始化对话                                   │
│  agent = AIAgent(model="anthropic/claude-opus-4.6", ...)    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: MemoryManager 预取上下文                             │
│  contexts = memory_manager.prefetch_all()                   │
│  → {                                                        │
│       "memory_store": "- 用户喜欢 Python 编程\n- 用户工作目录...", │
│       "supermemory": "- 最近记忆 1\n- 最近记忆 2...",          │
│       "honcho": "用户隔离记忆..."                            │
│     }                                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: 构建系统提示                                         │
│  system_prompt = memory_manager.build_system_prompt()       │
│  → "## Memories\n\n- 用户喜欢 Python 编程\n\n## SuperMemory Context\n\n..." │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 系统提示注入到 LLM 请求                               │
│  messages = [                                               │
│      {"role": "system", "content": system_prompt},          │
│      {"role": "user", "content": user_message}              │
│  ]                                                          │
│  response = client.chat.completions.create(messages=...)    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: LLM 基于记忆回答问题                                 │
│  用户问："我喜欢用什么编程语言？"                             │
│  LLM 回答："根据记忆，您喜欢使用 Python 编程。"                │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 记忆持久化机制

### 5.1 文件存储（MEMORY.md）

**路径**：`~/.hermes/memories/MEMORY.md`

**格式**：
```markdown
# ================================================================
# Hermes Agent Memory
# ================================================================

- 用户喜欢 Python 编程
- 用户的工作目录是 /home/user/projects
- 用户偏好使用 PostgreSQL 数据库
- 用户的公司名称为 Acme Corp
```

**特点**：
- **人类可读**：Markdown 格式，易于手动编辑
- **原子写入**：临时文件 + fsync + os.replace()
- **文件权限**：0600（仅所有者可读写）
- **字符限制**：默认 10KB 上限（可配置）

### 5.2 SQLite 存储（会话消息）

**路径**：`~/.hermes/state.db`

**表结构**：
- `sessions` 表：会话元数据（标题、开始时间、消息数量）
- `messages` 表：消息内容（role、content、timestamp）
- `messages_fts` 表：FTS5 全文搜索索引

**特点**：
- **自动索引**：触发器自动同步 FTS5 索引
- **高效搜索**：FTS5 支持布尔查询、短语匹配、通配符
- **会话隔离**：每个会话独立，支持按会话搜索

### 5.3 云存储（插件后端）

| 插件 | 云存储方案 | 同步机制 |
|------|------------|----------|
| **Mem0** | Supabase（PostgreSQL + pgvector） | REST API 实时同步 |
| **Honcho** | 用户隔离数据库（多租户） | 用户 ID 过滤 |
| **OpenViking** | 开源向量数据库（Qdrant、Weaviate） | 批量同步 |
| **RetainDB** | PostgreSQL（带版本控制） | 事务同步 |

### 5.4 混合存储架构

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryManager                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  内置 MemoryStore（~/.hermes/memories/MEMORY.md）    │   │
│  │  - 核心记忆（手动添加/LLM 决定）                       │   │
│  │  - 字符限制 10KB                                     │   │
│  │  - 系统提示注入                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SuperMemory 插件（内存 + FAISS）                      │   │
│  │  - 语义搜索（向量相似度）                             │   │
│  │  - 最近记忆缓存                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SessionDB（SQLite FTS5）                            │   │
│  │  - 全量会话消息                                      │   │
│  │  - 全文搜索                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Mem0 插件（Supabase 云存储）                         │   │
│  │  - 云同步（多设备共享）                               │   │
│  │  - 向量检索                                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 记忆与安全机制

### 6.1 访问控制

**文件权限**：
```python
# MEMORY.md 文件权限 0600
os.chmod(memory_path, stat.S_IRUSR | stat.S_IWUSR)

# SQLite 数据库文件权限 0600（应设置但当前缺失）
# os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)
```

**插件隔离**：
```python
# Honcho 插件：用户级记忆隔离
class MemoryProvider:
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def get_context(self) -> str:
        # 仅返回当前用户的记忆
        return self._db.query("SELECT * FROM memories WHERE user_id = ?", self.user_id)
```

### 6.2 敏感信息脱敏

**记忆写入前脱敏**：
```python
# agent/memory_manager.py

from agent.redact import redact_sensitive_text

def add_memory(self, content: str):
    """添加记忆前脱敏"""
    # 脱敏敏感信息（API Key、密码、电话号码等）
    safe_content = redact_sensitive_text(content)
    
    # 添加到 MemoryStore
    self._memory_store.add(safe_content)
```

**系统提示注入脱敏**：
```python
def build_system_prompt(self) -> str:
    """构建系统提示时脱敏"""
    sections = []
    
    # MemoryStore 记忆（已脱敏）
    if self._memory_store:
        memory_text = self._memory_store.format_for_system_prompt()
        # 再次脱敏（防止遗漏）
        memory_text = redact_sensitive_text(memory_text)
        sections.append("## Memories\n\n" + memory_text)
    
    # ... 其他提供者 ...
    
    return "\n\n".join(sections)
```

### 6.3 记忆隔离

**Profile 隔离**：
```python
# 每个 Profile 有独立的记忆文件
from hermes_constants import get_hermes_home

hermes_home = get_hermes_home()  # ~/.hermes 或 ~/.hermes/profiles/<name>
memory_path = hermes_home / "memories" / "MEMORY.md"
```

**会话隔离**：
```python
# SQLite 中每个会话独立
# 搜索时可按 session_id 过滤
cursor = self._conn.execute(
    "SELECT * FROM messages WHERE session_id = ?",
    (session_id,)
)
```

**多用户隔离（Honcho 插件）**：
```python
# Honcho 插件：基于用户 ID 的记忆隔离
class HonchoMemoryProvider:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._db = SQLiteDB(f"~/.hermes/honcho_{user_id}.db")
    
    def add_memory(self, content: str):
        # 仅写入当前用户的数据库
        self._db.execute(
            "INSERT INTO memories (user_id, content) VALUES (?, ?)",
            (self.user_id, content)
        )
```

### 6.4 记忆审计

**版本控制（RetainDB 插件）**：
```python
# RetainDB 插件：记忆版本控制
class RetainDBProvider:
    def add_memory(self, content: str):
        # 记录版本历史
        self._db.execute(
            """INSERT INTO memory_versions 
               (content, version, timestamp, operation) 
               VALUES (?, ?, ?, 'add')""",
            (content, self._next_version, time.time())
        )
    
    def get_version_history(self, memory_id: int) -> List[dict]:
        """获取记忆版本历史"""
        cursor = self._db.execute(
            "SELECT * FROM memory_versions WHERE memory_id = ? ORDER BY version",
            (memory_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
```

**操作日志**：
```python
# 所有记忆操作记录日志
import logging

logger = logging.getLogger(__name__)

def add(self, content: str):
    logger.info("Memory add: %s", content[:50])  # 仅记录前 50 字符
    # ... 添加逻辑 ...
```

---

## 7. 记忆系统的设计模式

### 7.1 策略模式（Strategy）

**应用场景**：多个记忆提供者（MemoryStore、SuperMemory、Mem0...）

**实现方式**：
```python
class IMemoryProvider(Protocol):
    """记忆提供者接口"""
    def get_context(self) -> str: ...
    def sync(self, conversation_turn: int): ...
    def handle_tool_call(self, tool_name: str, args: dict) -> str: ...

# 不同提供者实现不同策略
class MemoryStoreProvider(IMemoryProvider):
    def get_context(self) -> str:
        return self._memory_store.format_for_system_prompt()

class SuperMemoryProvider(IMemoryProvider):
    def get_context(self) -> str:
        return self._vector_search.get_recent_memories()

class Mem0Provider(IMemoryProvider):
    def get_context(self) -> str:
        return self._cloud_client.fetch_memories()
```

**优势**：
- 统一接口，上层代码无需关心具体实现
- 易于扩展新提供者（实现接口即可）

### 7.2 观察者模式（Observer）

**应用场景**：记忆同步（对话结束后触发）

**实现方式**：
```python
# MemoryManager 作为被观察者
class MemoryManager:
    def sync_all(self, conversation_turn: int):
        """通知所有提供者同步"""
        for provider in self._providers.values():
            provider.sync(conversation_turn)  # 观察者更新

# 提供者作为观察者
class HindsightProvider:
    def sync(self, conversation_turn: int):
        """会话结束后总结记忆"""
        if conversation_turn % 10 == 0:  # 每 10 轮对话总结一次
            self._summarize_conversation()
```

### 7.3 装饰器模式（Decorator）

**应用场景**：记忆脱敏

**实现方式**：
```python
class RedactingMemoryProvider(IMemoryProvider):
    """脱敏装饰器"""
    def __init__(self, provider: IMemoryProvider):
        self._provider = provider
    
    def get_context(self) -> str:
        context = self._provider.get_context()
        return redact_sensitive_text(context)  # 装饰原始上下文
    
    def add_memory(self, content: str):
        safe_content = redact_sensitive_text(content)
        self._provider.add_memory(safe_content)  # 装饰后委托
```

### 7.4 工厂模式（Factory）

**应用场景**：记忆提供者创建

**实现方式**：
```python
def create_memory_provider(provider_type: str, config: dict) -> IMemoryProvider:
    """工厂方法创建记忆提供者"""
    if provider_type == "file":
        return MemoryStoreProvider(config["path"])
    elif provider_type == "sqlite":
        return SessionDBProvider(config["db_path"])
    elif provider_type == "supermemory":
        return SuperMemoryProvider(config["embedding_model"])
    elif provider_type == "mem0":
        return Mem0Provider(config["api_key"])
    # ...
```

### 7.5 单例模式（Singleton）

**应用场景**：MemoryManager 全局唯一实例

**实现方式**：
```python
# agent/memory_manager.py
_memory_manager_instance: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
    """获取全局 MemoryManager 单例"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance
```

---

## 8. 架构决策与权衡

### 8.1 关键架构决策

| 决策 | 选择 | 替代方案 | 理由 |
|------|------|----------|------|
| **存储格式** | Markdown 文件（MEMORY.md） | JSON / YAML / 数据库 | 人类可读，易于手动编辑 |
| **检索方式** | 子字符串匹配（内置）+ 向量检索（插件） | 仅全文搜索 / 仅向量检索 | 平衡简单性和强大功能 |
| **字符限制** | 10KB 上限（可配置） | 无限制 / 条目数量限制 | 防止记忆膨胀，保持精炼 |
| **去重机制** | 完全匹配去重 | 语义去重（向量相似度） | 简单高效，避免冗余 |
| **系统提示注入** | 冻结快照（格式化字符串） | 动态检索（按需查询） | 减少 LLM 调用次数，降低成本 |
| **插件架构** | 多提供者并行 | 单一提供者 | 灵活扩展，不锁定单一后端 |

### 8.2 已知限制

| 限制 | 影响 | 缓解措施 |
|------|------|----------|
| **子字符串搜索精度低** | 无法语义匹配（如"Python"匹配不到"编程语言"） | 使用 SuperMemory 等向量检索插件 |
| **MEMORY.md 无版本控制** | 误删除后无法恢复 | 使用 RetainDB 插件或手动 Git 版本控制 |
| **截图无法脱敏** | 图像中的敏感文本无法被检测 | 文件权限 `0600` + 临时文件清理 |
| **SQLite 文件权限未设置** | 可能对同系统其他用户可读 | 建议在创建后添加 `os.chmod(db_path, 0o600)` |
| **云同步延迟** | Mem0 等云插件存在网络延迟 | 本地缓存 + 异步同步 |

### 8.3 安全加固建议

| 建议 | 优先级 | 实现难度 |
|------|--------|----------|
| SQLite 文件权限设置 | 高 | 低（添加 `os.chmod()`） |
| 记忆写入前强制脱敏 | 高 | 中（集成 redact_sensitive_text） |
| 记忆操作审计日志 | 中 | 低（添加 logging） |
| 多用户隔离（Honcho） | 中 | 中（需要用户认证） |
| 记忆版本控制（RetainDB） | 低 | 中（需要数据库 schema 变更） |

### 8.4 性能优化点

| 优化点 | 当前状态 | 建议 |
|--------|----------|------|
| 记忆搜索 | 线性扫描（O(n)） | 倒排索引（O(1)） |
| 向量检索 | 全量计算（O(n)） | FAISS 索引（O(log n)） |
| 文件写入 | 每次全量写入 | 增量更新（仅写变更） |
| 上下文缓存 | 无缓存 | LRU 缓存（TTL 5 分钟） |
| 插件加载 | 启动时全量加载 | 按需懒加载 |

---

## 附录：流程图索引

1. [记忆系统架构图](#12-架构层次)
2. [MemoryStore 类核心方法图](#21-memorystore-类文件级记忆存储)
3. [MemoryManager 类协调图](#22-memorymanager-类记忆管理器)
4. [记忆插件目录结构图](#31-插件目录结构)
5. [记忆添加流程图](#41-记忆添加流程)
6. [记忆搜索流程图](#42-记忆搜索流程)
7. [记忆替换流程图](#43-记忆替换流程)
8. [记忆删除流程图](#44-记忆删除流程)
9. [系统提示注入流程图](#45-系统提示注入流程)
10. [混合存储架构图](#54-混合存储架构)

---

## 参考文件

- 核心实现：[tools/memory_tool.py](tools/memory_tool.py)（557 行）
- 记忆管理器：[agent/memory_manager.py](agent/memory_manager.py)（362 行）
- SQLite 会话存储：[hermes_state.py](hermes_state.py)（1238 行）
- 记忆插件目录：[plugins/memory/](plugins/memory/)（8 个插件）
- 敏感信息脱敏：[agent/redact.py](agent/redact.py)（181 行）
- 工具注册中心：[tools/registry.py](tools/registry.py)（335 行）

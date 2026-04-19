# Hermes Agent — 软件架构与设计原理

> 本文档深入分析 Hermes Agent 的 Agent 创建与管理系统，涵盖整体架构、核心模块、设计原理、数据流和关键流程。

---

## 目录

1. [系统全景架构图](#1-系统全景架构图)
2. [核心模块依赖图](#2-核心模块依赖图)
3. [分层架构设计](#3-分层架构设计)
4. [Agent 创建与管理](#4-agent-创建与管理)
5. [核心对话循环](#5-核心对话循环)
6. [工具注册与编排系统](#6-工具注册与编排系统)
7. [子Agent委派机制](#7-子agent委派机制)
8. [会话管理系统](#8-会话管理系统)
9. [上下文压缩引擎](#9-上下文压缩引擎)
10. [记忆管理系统](#10-记忆管理系统)
11. [平台适配器架构](#11-平台适配器架构)
12. [关键设计原理](#12-关键设计原理)

---

## 1. 系统全景架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          用户交互层 (Entry Points)                      │
│                                                                         │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  CLI 模式     │  │  Gateway 模式     │  │  ACP 模式               │  │
│  │  (cli.py)    │  │  (gateway/run.py) │  │  (acp_adapter/)         │  │
│  │              │  │                    │  │  VS Code / Zed / JB     │  │
│  │  HermesCLI   │  │  GatewayRunner    │  │                          │  │
│  │  REPL交互    │  │  多平台消息路由    │  │  LSP协议适配             │  │
│  └──────┬───────┘  └────────┬──────────┘  └────────────┬─────────────┘  │
│         │                   │                           │                │
└─────────┼───────────────────┼───────────────────────────┼────────────────┘
          │                   │                           │
          ▼                   ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Agent 核心层 (Core Engine)                        │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     AIAgent (run_agent.py)                      │   │
│  │                                                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │ Prompt       │  │ Context      │  │ Memory               │  │   │
│  │  │ Builder      │  │ Compressor   │  │ Manager              │  │   │
│  │  │ (prompt_     │  │ (context_    │  │ (memory_             │  │   │
│  │  │  builder.py) │  │  compressor) │  │  manager.py)         │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  │                                                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │ Model        │  │ Prompt       │  │ Error                │  │   │
│  │  │ Metadata     │  │ Caching      │  │ Classifier          │  │   │
│  │  │ (model_      │  │ (prompt_     │  │ (error_             │  │   │
│  │  │  metadata.py)│  │  caching.py) │  │  classifier.py)     │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  工具编排层 (Tool Orchestration)                 │   │
│  │                                                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │ Tool         │  │ Toolset      │  │ Model Tools          │  │   │
│  │  │ Registry     │  │ Resolver     │  │ (model_tools.py)     │  │   │
│  │  │ (registry.py)│  │ (toolsets.py)│  │ 编排/调度/异步桥接   │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │   │
│  │         │                 │                      │              │   │
│  │  ┌──────▼─────────────────▼──────────────────────▼───────────┐  │   │
│  │  │              工具实现层 (Tool Implementations)             │  │   │
│  │  │  terminal | file | web | browser | vision | delegate | ...│  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │                   │                           │
          ▼                   ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       平台适配层 (Platform Adapters)                    │
│                                                                         │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │Telegram│ │Discord │ │Slack   │ │WhatsApp│ │微信    │ │钉钉    │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │飞书    │ │Signal  │ │Matrix  │ │Email   │ │Webhook │ │API Srv │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│                                                                         │
│  所有适配器继承 BasePlatformAdapter → 统一消息收发/媒体/中断接口        │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       持久化层 (Persistence)                            │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ SessionStore │  │ SessionDB    │  │ Memory Store │  │ Config     │ │
│  │ (SQLite+JSONL)│ │ (FTS5搜索)   │  │ (内置+插件)  │  │ (YAML+.env)│ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心模块依赖图

```
tools/registry.py  (零依赖 — 所有工具文件导入它)
       ↑
tools/*.py  (每个文件在模块级别调用 registry.register())
       ↑
model_tools.py  (导入 registry + 所有工具模块 → 触发工具发现)
       ↑
run_agent.py  (AIAgent 类 — 核心对话循环)
       ↑
cli.py / gateway/run.py / batch_runner.py / acp_adapter/
```

**关键设计约束**：依赖链是单向的，不存在循环依赖。`tools/registry.py` 是最底层，不依赖任何上层模块。

---

## 3. 分层架构设计

Hermes Agent 采用 **五层架构**，每层职责清晰：

| 层次 | 模块 | 职责 |
|------|------|------|
| **入口层** | `cli.py`, `gateway/run.py`, `acp_adapter/` | 用户交互、输入解析、输出展示 |
| **Agent层** | `run_agent.py` (AIAgent) | 对话循环、工具调度、上下文管理 |
| **编排层** | `model_tools.py`, `toolsets.py` | 工具发现、Schema过滤、调度分发 |
| **注册层** | `tools/registry.py` | 工具元数据存储、Schema查询、Handler分发 |
| **实现层** | `tools/*.py` | 具体工具逻辑（终端、文件、浏览器等） |

---

## 4. Agent 创建与管理

### 4.1 AIAgent 类结构

```
AIAgent
├── __init__()                    # 初始化：模型、凭据、工具集、回调
├── chat(message)                 # 简单接口 → 返回最终响应字符串
├── run_conversation(user_msg)    # 完整接口 → 返回 dict (final_response + messages)
│   ├── _build_system_prompt()    # 组装系统提示
│   ├── _check_context_pressure() # 上下文压力检测
│   ├── _compress_if_needed()     # 触发上下文压缩
│   ├── _call_model()             # 调用LLM API
│   ├── _handle_tool_calls()      # 处理工具调用
│   │   ├── _should_parallelize() # 判断是否可并行
│   │   ├── _execute_parallel()   # 并行执行工具
│   │   └── _execute_sequential() # 串行执行工具
│   └── _handle_agent_tools()     # 处理Agent级工具(todo/memory/delegate)
├── IterationBudget               # 线程安全的迭代计数器
├── _memory_manager               # MemoryManager 实例
├── _context_engine               # ContextEngine 实例
└── _delegate_depth               # 委派深度追踪
```

### 4.2 Agent 创建流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Agent 创建流程 (三种入口)                        │
└─────────────────────────────────────────────────────────────────────┘

入口1: CLI模式
─────────────
HermesCLI.__init__()
    │
    ├─ load_cli_config()          # 加载配置
    ├─ _ensure_runtime_credentials()  # 解析provider/API key
    │
    ▼  (延迟初始化，首次使用时)
HermesCLI._init_agent()
    │
    ├─ 恢复会话历史 (SessionDB)
    ├─ 创建 AIAgent(
    │      model, api_key, base_url, provider,
    │      max_iterations, enabled_toolsets,
    │      reasoning_config, callbacks...,
    │      session_id, iteration_budget,
    │      credential_pool, checkpoints_enabled
    │  )
    └─ 设置 _print_fn → _cprint (prompt_toolkit路由)

入口2: Gateway模式
─────────────────
GatewayRunner._handle_message_with_agent()
    │
    ├─ SessionStore.get_or_create_session()   # 获取/创建会话
    ├─ build_session_context()                # 构建会话上下文
    ├─ 加载对话历史
    │
    ├─ 检查 _agent_cache                      # Agent缓存命中？
    │   ├─ 命中 → 复用缓存的AIAgent实例
    │   └─ 未命中 → 创建新AIAgent实例
    │
    ├─ 创建 AIAgent(
    │      model, api_key, base_url, provider,
    │      platform="telegram"/"discord"/...,
    │      session_id, enabled_toolsets,
    │      callbacks (clarify, thinking, tool_progress...),
    │      iteration_budget,
    │      credential_pool
    │  )
    │
    └─ 存入 _agent_cache (保持prompt caching前缀不变)

入口3: 子Agent委派
─────────────────
delegate_tool._build_child_agent()
    │
    ├─ 解析工具集 (与父Agent取交集 → 移除被阻止的工具)
    ├─ 继承父Agent凭据 (支持覆盖)
    ├─ 创建 AIAgent(
    │      skip_context_files=True,
    │      skip_memory=True,        # 子Agent不读写共享记忆
    │      clarify_callback=None,   # 子Agent不与用户交互
    │      max_iterations=50,       # 独立迭代预算
    │      _delegate_depth=parent._delegate_depth+1
    │  )
    │
    └─ 注册到父Agent._active_children (中断传播)
```

### 4.3 Agent 生命周期管理

```
                    ┌─────────────┐
                    │   Created   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
           ┌───────│  Initialized │◄──────────────────────┐
           │       └──────┬──────┘                        │
           │              │                                │
           │       ┌──────▼──────┐                         │
           │       │   Running   │◄────────┐              │
           │       │ (对话循环中) │         │              │
           │       └──────┬──────┘         │              │
           │              │                │              │
           │    ┌─────────┼────────┐       │              │
           │    ▼         ▼        ▼       │              │
           │ ┌──────┐ ┌──────┐ ┌───────┐  │              │
           │ │Tool  │ │Comp- │ │Final  │  │              │
           │ │Call  │ │ress  │ │Resp   │  │              │
           │ └──┬───┘ └──┬───┘ └───┬───┘  │              │
           │    │        │         │      │              │
           │    └────────┴─────────┘      │              │
           │              │                │              │
           │       ┌──────▼──────┐  新消息到达            │
           │       │  Idle/Wait  │─────────┘              │
           │       └──────┬──────┘                        │
           │              │ /new, /reset                  │
           │       ┌──────▼──────┐                         │
           │       │   Reset     │─────────────────────────┘
           │       │(flush memory│
           │       │ clear ctx)  │
           │       └──────┬──────┘
           │              │
           │       ┌──────▼──────┐
           └──────►│  Destroyed  │
                   │ (cleanup)   │
                   └─────────────┘
```

---

## 5. 核心对话循环

### 5.1 主循环流程图

```
run_conversation(user_message, system_message, conversation_history)
│
├── 1. 初始化
│   ├── 构建 system_prompt = identity + platform_hint + skills + memory + context_files
│   ├── 初始化 messages = [system] + history + [user_message]
│   ├── 触发 MemoryManager.prefetch_all() (后台预取记忆)
│   └── 触发 MemoryManager.queue_prefetch_all() (排队下一轮预取)
│
├── 2. 主循环 while iteration_budget.remaining > 0
│   │
│   ├── 2a. 上下文压力检查
│   │   ├── _check_context_pressure()
│   │   │   ├── 估算当前messages的token数
│   │   │   ├── 如果 > threshold (默认75%上下文窗口)
│   │   │   │   ├── 触发 context_engine.compress()
│   │   │   │   └── 替换 messages 中的中间部分为摘要
│   │   │   └── 如果 > 95% → 强制压缩 + 警告
│   │   │
│   │   └── _check_context_pressure_preflight()
│   │       └── API调用前的快速粗略检查
│   │
│   ├── 2b. 调用LLM API
│   │   ├── client.chat.completions.create(
│   │   │     model=model,
│   │   │     messages=messages,
│   │   │     tools=tool_schemas,
│   │   │     reasoning_effort=...,
│   │   │     max_tokens=...,
│   │   │ )
│   │   ├── 处理API错误 (rate_limit, context_overflow, server_error)
│   │   │   ├── rate_limit → 指数退避重试
│   │   │   ├── context_overflow → 压缩后重试
│   │   │   ├── server_error → 故障转移到fallback_model
│   │   │   └── 其他错误 → 分类并决定是否重试
│   │   │
│   │   └── 更新 context_engine.update_from_response(usage)
│   │
│   ├── 2c. 处理响应
│   │   ├── 如果有 tool_calls:
│   │   │   ├── 遍历每个 tool_call
│   │   │   │   ├── Agent级工具拦截 (todo, memory, delegate_task, session_search)
│   │   │   │   │   └── 在 run_agent.py 中直接处理，不经过 registry
│   │   │   │   └── 普通工具 → handle_function_call()
│   │   │   │       ├── coerce_tool_args() (类型强制转换)
│   │   │   │       ├── registry.dispatch(name, args)
│   │   │   │       │   ├── 同步handler → 直接调用
│   │   │   │       │   └── 异步handler → _run_async() 桥接
│   │   │   │       └── 返回 JSON 字符串结果
│   │   │   │
│   │   │   ├── 并行优化:
│   │   │   │   ├── _should_parallelize_tool_batch()
│   │   │   │   │   ├── 检查是否包含 _NEVER_PARALLEL_TOOLS (clarify)
│   │   │   │   │   ├── 检查路径冲突 (_PATH_SCOPED_TOOLS)
│   │   │   │   │   └── 检查是否全部是 _PARALLEL_SAFE_TOOLS
│   │   │   │   ├── 可并行 → ThreadPoolExecutor (最多8线程)
│   │   │   │   └── 不可并行 → 顺序执行
│   │   │   │
│   │   │   ├── 将 tool_result 追加到 messages
│   │   │   └── iteration_budget.consume()
│   │   │
│   │   └── 如果没有 tool_calls (纯文本响应):
│   │       ├── 提取 reasoning 内容
│   │       ├── 保存轨迹 (如果 save_trajectories=True)
│   │       ├── MemoryManager.sync_all() (同步记忆)
│   │       └── 返回 final_response
│   │
│   └── 2d. 循环继续 → 回到 2a
│
└── 3. 返回结果
    └── { final_response, messages, api_call_count, ... }
```

### 5.2 工具调用并行化策略

```
                    tool_calls 批次到达
                           │
                    ┌──────▼──────┐
                    │ 并行化判断   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ 包含不可并行│ │ 路径冲突   │ │ 全部可并行 │
     │ 工具(clarify)│ │(同文件读写)│ │            │
     └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
            │              │              │
            ▼              ▼              ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ 顺序执行   │ │ 顺序执行   │ │ 并行执行   │
     │            │ │            │ │ ThreadPool │
     │ clarify    │ │ read_file  │ │ web_search │
     │ → web_search│ │ write_file │ │ + web_extract│
     │ → read_file│ │ (同路径)   │ │ + read_file │
     └────────────┘ └────────────┘ │ (不同路径) │
                                 └────────────┘

工具分类:
  _NEVER_PARALLEL_TOOLS = {clarify}           # 交互式，不可并行
  _PARALLEL_SAFE_TOOLS  = {web_search,        # 只读，无共享状态
                           web_extract,
                           read_file,
                           search_files,
                           vision_analyze,
                           session_search,
                           skill_view,
                           skills_list,
                           ha_get_state,
                           ha_list_entities,
                           ha_list_services}
  _PATH_SCOPED_TOOLS    = {read_file,         # 路径作用域，不同路径可并行
                           write_file,
                           patch}
```

---

## 6. 工具注册与编排系统

### 6.1 工具发现与注册流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      工具发现流程 (启动时一次性)                      │
└─────────────────────────────────────────────────────────────────────┘

model_tools.py 被导入
    │
    ├── _discover_tools()                    # 导入所有工具模块
    │   ├── import tools.web_tools           # → registry.register("web_search", ...)
    │   ├── import tools.terminal_tool       # → registry.register("terminal", ...)
    │   ├── import tools.file_tools          # → registry.register("read_file", ...)
    │   ├── import tools.vision_tools        # → registry.register("vision_analyze", ...)
    │   ├── import tools.browser_tool        # → registry.register("browser_navigate", ...)
    │   ├── import tools.delegate_tool       # → registry.register("delegate_task", ...)
    │   ├── import tools.todo_tool           # → registry.register("todo", ...)
    │   ├── import tools.memory_tool         # → registry.register("memory", ...)
    │   ├── import tools.code_execution_tool # → registry.register("execute_code", ...)
    │   └── ... (20+ 工具模块)
    │
    ├── discover_mcp_tools()                 # MCP 服务器工具发现
    │   └── 从 config.yaml 读取 MCP 服务器配置
    │       └── 连接 MCP 服务器 → 获取工具列表 → registry.register()
    │
    └── discover_plugins()                   # 插件工具发现
        └── 扫描 ~/.hermes/plugins/ + 项目插件
            └── 加载插件 → registry.register()

每个工具模块的注册模式:
─────────────────────────
# tools/web_tools.py (示例)
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("BRAVE_API_KEY") or os.getenv("TAVILY_API_KEY"))

def web_search(query: str, task_id: str = None) -> str:
    ...  # 实际搜索逻辑
    return json.dumps({"results": [...]})

registry.register(
    name="web_search",
    toolset="web",
    schema={"name": "web_search", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: web_search(query=args.get("query"), task_id=kw.get("task_id")),
    check_fn=check_requirements,        # 可用性检查函数
    requires_env=["BRAVE_API_KEY"],     # 依赖的环境变量
)
```

### 6.2 工具集解析与过滤流程

```
get_tool_definitions(enabled_toolsets, disabled_toolsets, quiet_mode)
│
├── 1. 解析工具集名称 → 工具名称集合
│   ├── 如果 enabled_toolsets 指定:
│   │   └── 对每个 toolset_name:
│   │       ├── validate_toolset(name) → 是否有效
│   │       └── resolve_toolset(name) → 递归解析
│   │           ├── 直接工具 (toolset.tools)
│   │           └── 包含的工具集 (toolset.includes) → 递归解析
│   │
│   ├── 如果 disabled_toolsets 指定:
│   │   └── 全部工具集 - 禁用的工具集
│   │
│   └── 否则: 全部工具集
│
├── 2. 可用性过滤 (check_fn)
│   └── registry.get_definitions(tool_names)
│       └── 对每个工具:
│           ├── 有 check_fn → 调用 check_fn()
│           │   ├── True → 包含
│           │   └── False → 排除 (API key未配置等)
│           └── 无 check_fn → 包含
│
├── 3. 动态Schema后处理
│   ├── execute_code: 根据可用工具重建sandbox工具列表
│   └── browser_navigate: 移除对不可用web工具的交叉引用
│
└── 4. 返回 OpenAI 格式的 tool definitions
    └── [{"type": "function", "function": {schema}}, ...]
```

### 6.3 工具调度流程

```
handle_function_call(function_name, function_args, task_id, ...)
│
├── coerce_tool_args()                    # 类型强制转换
│   └── "42" → 42, "true" → true (根据Schema)
│
├── Agent级工具拦截检查
│   └── if function_name in {"todo", "memory", "session_search", "delegate_task"}:
│       └── 返回错误 "must be handled by the agent loop"
│       (这些工具在 run_agent.py 中直接处理)
│
├── 插件钩子: pre_tool_call
│
├── registry.dispatch(name, args, **kwargs)
│   ├── 查找 ToolEntry
│   ├── 如果 is_async → _run_async(handler(args, **kwargs))
│   │   └── 异步桥接:
│   │       ├── 主线程 → persistent event loop
│   │       ├── 工作线程 → per-thread persistent loop
│   │       └── 异步上下文 → 新线程 + asyncio.run()
│   └── 否则 → handler(args, **kwargs)
│
├── 插件钩子: post_tool_call
│
└── 返回 JSON 字符串结果
```

---

## 7. 子Agent委派机制

### 7.1 委派架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    父Agent (AIAgent)                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 对话历史: [system, user, assistant, tool_result, ...]│   │
│  │ 工具集: hermes-cli (全部工具)                        │   │
│  │ 迭代预算: 90                                         │   │
│  │ 委派深度: 0                                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  调用 delegate_task(goal="分析代码库", toolsets=[...])      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            子Agent创建 (_build_child_agent)          │   │
│  │                                                     │   │
│  │  ┌──────────────────┐  ┌──────────────────────┐    │   │
│  │  │ 子Agent #1       │  │ 子Agent #2           │    │   │
│  │  │ (ThreadPool)     │  │ (ThreadPool)         │    │   │
│  │  │                  │  │                      │    │   │
│  │  │ 对话: 全新       │  │ 对话: 全新           │    │   │
│  │  │ 工具集: 交集     │  │ 工具集: 交集         │    │   │
│  │  │ 预算: 50         │  │ 预算: 50             │    │   │
│  │  │ 深度: 1          │  │ 深度: 1              │    │   │
│  │  │ 记忆: 跳过       │  │ 记忆: 跳过           │    │   │
│  │  │ clarify: 禁用    │  │ clarify: 禁用        │    │   │
│  │  └──────────────────┘  └──────────────────────┘    │   │
│  │                                                     │   │
│  │  阻止的工具:                                         │   │
│  │  delegate_task (禁止递归)                            │   │
│  │  clarify (禁止用户交互)                              │   │
│  │  memory (禁止写共享记忆)                             │   │
│  │  send_message (禁止跨平台副作用)                     │   │
│  │  execute_code (子Agent应逐步推理)                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  父Agent 阻塞等待所有子Agent完成                             │
│  │                                                          │
│  ▼                                                          │
│  汇总结果: [task_0_result, task_1_result, ...]              │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 委派深度限制

```
深度 0: 父Agent (用户直接交互)
  │
  ├── 深度 1: 子Agent (由父Agent委派)
  │     │
  │     └── 深度 2: ❌ 拒绝! (MAX_DEPTH=2, >=2 被拒绝)
  │
  └── 深度 1: 子Agent (另一个任务)
```

### 7.3 子Agent生命周期

```
_build_child_agent()
    │
    ▼
_run_single_child(child, goal, task_index, ...)
    │
    ├── 1. 保存父Agent全局变量 (_last_resolved_tool_names)
    ├── 2. 获取凭据池租约 (acquire_lease)
    ├── 3. 启动心跳线程 (每30秒触碰父Agent活跃追踪器)
    │
    ├── 4. child.run_conversation(user_message=goal)
    │   └── (正常的Agent循环，但受限工具集)
    │
    ├── 5. 构建工具追踪 (tool_trace)
    │   └── 通过 tool_call_id 配对并行工具调用
    │
    ├── 6. 释放凭据池租约 (release_lease)
    ├── 7. 恢复父Agent全局变量
    │
    └── 8. 返回结构化结果:
        {
            task_index, status, summary,
            api_calls, duration_seconds,
            model, exit_reason, tokens,
            tool_trace
        }
```

---

## 8. 会话管理系统

### 8.1 会话键构建规则

```
build_session_key(source, group_sessions_per_user, thread_sessions_per_user)
│
├── DM (chat_type="dm"):
│   └── "agent:main:{platform}:dm:{chat_id}:{thread_id}"
│       例: "agent:main:telegram:dm:123456789:"
│
├── Group (chat_type="group"):
│   ├── group_sessions_per_user=True (默认):
│   │   └── "agent:main:{platform}:group:{chat_id}:{thread_id}:{user_id}"
│   │       例: "agent:main:telegram:group:-100123456::789"
│   │       (每个用户在群组中有独立会话)
│   │
│   └── group_sessions_per_user=False:
│       └── "agent:main:{platform}:group:{chat_id}:{thread_id}:"
│           (群组共享一个会话)
│
└── Thread (chat_type="thread"):
    ├── thread_sessions_per_user=False (默认):
    │   └── 线程共享父频道会话
    │
    └── thread_sessions_per_user=True:
        └── 每个用户在线程中有独立会话
```

### 8.2 会话重置策略

```
SessionResetPolicy
│
├── mode="daily":  每天固定时间重置
│   └── at_hour=4 (凌晨4点)
│
├── mode="idle":   空闲超时重置
│   └── idle_minutes=1440 (24小时)
│
├── mode="both":   两者取先 (默认)
│   └── min(daily, idle)
│
└── mode="none":   从不自动重置

重置流程:
────────
1. 检测会话过期 (_is_session_expired)
2. _flush_memories_for_session()  # 让Agent保存记忆/技能
3. 清空对话历史
4. 重置 context_engine (on_session_reset)
5. 标记 was_auto_reset=True
```

---

## 9. 上下文压缩引擎

### 9.1 压缩引擎架构

```
ContextEngine (ABC)                    # 可插拔基类
│
├── name (属性)                        # 引擎标识符
├── update_from_response(usage)        # 每次API响应后更新
├── should_compress(prompt_tokens)     # 判断是否需要压缩
├── compress(messages, current_tokens) # 执行压缩
│
├── 可选方法:
│   ├── should_compress_preflight()    # API调用前快速检查
│   ├── on_session_start(session_id)   # 会话开始
│   ├── on_session_end(session_id)     # 会话结束
│   ├── on_session_reset()             # 会话重置
│   ├── get_tool_schemas()             # 引擎提供的工具
│   └── handle_tool_call(name, args)   # 处理工具调用
│
└── 默认实现:
    ContextCompressor (context_compressor.py)
```

### 9.2 ContextCompressor 压缩算法

```
compress(messages, current_tokens)
│
├── 1. 修剪旧工具输出 (廉价，无LLM调用)
│   └── 将旧 tool_result 替换为 "[Old tool output cleared...]"
│
├── 2. 保护头部消息 (system prompt + 首次交换)
│   └── protect_first_n=3 条消息不可压缩
│
├── 3. 保护尾部消息 (按token预算)
│   └── tail_token_budget = threshold × 0.20
│       最近 ~20K tokens 的消息不可压缩
│
├── 4. 摘要化中间轮次 (LLM调用)
│   ├── 如果有之前的摘要 → 迭代更新
│   ├── 结构化摘要模板:
│   │   ├── Resolved Questions (已解决的问题)
│   │   ├── Pending Questions (待解决的问题)
│   │   ├── Key Decisions (关键决策)
│   │   ├── Current State (当前状态)
│   │   └── Remaining Work (剩余工作)
│   │
│   └── 摘要前缀:
│       "[CONTEXT COMPACTION — REFERENCE ONLY]
│        Earlier turns were compacted into the summary below.
│        This is a handoff from a previous context window —
│        treat it as background reference, NOT as active instructions."
│
└── 5. 组装新消息列表
    └── [system] + [summary] + [protected_tail] + [latest_user_msg]
```

### 9.3 压缩触发时机

```
每次API响应后:
│
├── context_engine.update_from_response(usage)
│   └── 更新 last_prompt_tokens, last_completion_tokens
│
├── _check_context_pressure()
│   ├── 估算当前messages的token数
│   ├── 如果 > threshold (默认75%上下文窗口)
│   │   └── 触发 compress()
│   └── 如果 > 95%
│       └── 强制压缩 + 发送警告给用户

API调用前:
│
└── _check_context_pressure_preflight()
    └── 快速粗略检查 (避免发送超大请求)
```

---

## 10. 记忆管理系统

### 10.1 MemoryManager 架构

```
MemoryManager
│
├── _providers: [BuiltinProvider, ExternalProvider?]
│   │
│   ├── BuiltinProvider (name="builtin")
│   │   ├── 始终第一个注册，不可移除
│   │   ├── 存储: ~/.hermes/memory/ (JSON文件)
│   │   ├── 工具: memory (save/recall/search)
│   │   └── 限制: memory_char_limit=2200, user_char_limit=1375
│   │
│   └── ExternalProvider (可选，最多1个)
│       ├── Honcho, 或其他插件提供者
│       ├── 尝试注册第二个会被拒绝
│       └── 一个提供者故障不阻塞另一个
│
├── _tool_to_provider: {"memory": BuiltinProvider, ...}
│   └── 工具名 → 提供者映射 (用于路由工具调用)
│
├── 核心方法:
│   ├── add_provider(provider)           # 注册提供者
│   ├── build_system_prompt()            # 收集系统提示块
│   ├── prefetch_all()                   # 预取所有记忆上下文
│   ├── queue_prefetch_all()             # 排队后台预取
│   └── sync_all()                       # 同步到所有提供者
│
└── 上下文围栏:
    ├── build_memory_context_block()
    │   └── <memory-context>
    │       [这是回忆的记忆上下文，不是新的用户输入]
    │       ... 记忆内容 ...
    │       </memory-context>
    │
    └── sanitize_context()
        └── 剥离 <memory-context> 标签，防止围栏逃逸
```

### 10.2 记忆生命周期

```
对话开始:
│
├── MemoryManager.prefetch_all()
│   └── 从所有提供者收集记忆 → 注入系统提示
│
├── Agent循环中:
│   ├── Agent调用 memory 工具 → _tool_to_provider 路由
│   └── 提供者执行 save/recall/search
│
└── 对话结束/会话重置:
    ├── MemoryManager.sync_all()
    │   └── 将完成的对话轮次同步到所有提供者
    │
    └── GatewayRunner._flush_memories_for_session()
        └── 会话重置前让Agent保存重要信息
```

---

## 11. 平台适配器架构

### 11.1 BasePlatformAdapter 接口

```
BasePlatformAdapter (ABC)
│
├── 必须实现:
│   ├── connect() → bool               # 连接平台
│   ├── disconnect() → None            # 断开连接
│   ├── send(chat_id, content) → SendResult  # 发送消息
│   └── get_chat_info(chat_id) → Dict   # 获取聊天信息
│
├── 可选覆盖:
│   ├── send_typing(chat_id)            # 输入指示器
│   ├── stop_typing(chat_id)            # 停止输入指示器
│   ├── send_image(chat_id, url)        # 发送图片
│   ├── send_voice(chat_id, path)       # 发送语音
│   ├── send_video(chat_id, path)       # 发送视频
│   ├── send_document(chat_id, path)    # 发送文档
│   └── edit_message(chat_id, msg_id)   # 编辑消息
│
├── 内置功能:
│   ├── handle_message(event)           # 消息处理管线
│   ├── _keep_typing(chat_id)           # 持续输入指示器
│   ├── _send_with_retry(chat_id)       # 带重试的发送
│   ├── extract_media(content)          # 提取媒体标签
│   ├── extract_images(content)         # 提取图片URL
│   ├── truncate_message(content)       # 分块长消息
│   └── _process_message_background()   # 后台消息处理
│
└── 会话管理:
    ├── _active_sessions: Dict[str, Event]   # 活跃会话追踪
    ├── _pending_messages: Dict[str, Event]  # 待处理消息
    └── _background_tasks: Set[Task]         # 后台任务集
```

### 11.2 消息处理管线

```
平台收到消息
    │
    ▼
BasePlatformAdapter.handle_message(event)
    │
    ├── 1. 构建 session_key
    │   └── build_session_key(source, ...)
    │
    ├── 2. 检查是否有活跃会话
    │   ├── 有活跃会话:
    │   │   ├── 特殊命令 (approve/deny/stop/new/reset)?
    │   │   │   └── 直接分发 (绕过活跃守卫)
    │   │   ├── 照片突发?
    │   │   │   └── 排队等待，不中断
    │   │   └── 普通消息:
    │   │       ├── 排队为 pending_message
    │   │       └── 触发中断信号
    │   │
    │   └── 无活跃会话:
    │       └── 标记为活跃 → 创建后台任务
    │
    ├── 3. _process_message_background(event, session_key)
    │   ├── 启动 _keep_typing() (持续输入指示器)
    │   ├── 调用 _message_handler(event) → GatewayRunner
    │   │   └── GatewayRunner._handle_message_with_agent()
    │   │       ├── 获取/创建会话
    │   │       ├── 构建 session_context
    │   │       ├── 创建/缓存 AIAgent
    │   │       └── agent.run_conversation()
    │   │
    │   ├── 处理响应:
    │   │   ├── 提取 MEDIA: 标签
    │   │   ├── 提取图片 URL
    │   │   ├── 自动TTS (语音消息回复)
    │   │   ├── 发送文本
    │   │   ├── 发送图片/视频/文档
    │   │   └── 发送本地文件
    │   │
    │   └── 检查 pending_message (中断期间排队的消息)
    │       └── 如果有 → 递归处理
    │
    └── 4. 清理
        ├── 停止 typing indicator
        └── 移除 session_key from _active_sessions
```

---

## 12. 关键设计原理

### 12.1 同步优先架构

Hermes Agent 的核心循环是**完全同步的**。这带来几个关键优势：

- **简单性**：不需要处理 async/await 的复杂性
- **可调试性**：调用栈清晰，无协程跳转
- **兼容性**：OpenAI SDK 是同步的，直接对接

异步工具通过 `_run_async()` 桥接：

```
同步 Agent 循环
    │
    ├── 同步工具 → 直接调用
    │
    └── 异步工具 → _run_async()
        ├── 主线程 → persistent event loop (run_until_complete)
        ├── 工作线程 → per-thread persistent loop
        └── 异步上下文 → 新线程 + asyncio.run()
```

### 12.2 Agent 缓存与 Prompt Caching

Gateway 为每个会话缓存 AIAgent 实例：

```
_agent_cache: Dict[session_key, (agent, timestamp)]

为什么缓存？
──────────
Anthropic 的 Prompt Caching 要求系统提示前缀不变。
如果每条消息都创建新 Agent，系统提示会被重新组装，
导致缓存失效，成本增加约10倍。

缓存策略：
──────────
1. 首次消息 → 创建 AIAgent → 存入缓存
2. 后续消息 → 复用缓存的 AIAgent
3. 模型切换 → 清除缓存，创建新 Agent
4. 会话重置 → 清除缓存
```

### 12.3 Sentinel 防护模式

防止同一会话的并发消息绕过"正在运行"守卫：

```
_handle_message()
    │
    ├── 立即放入 _AGENT_PENDING_SENTINEL
    │   (在创建Agent之前)
    │
    ├── 检查 _running_agents[session_key]
    │   ├── SENTINEL → "Agent正在处理，排队等待"
    │   └── None → 可以创建新Agent
    │
    └── 创建Agent后替换SENTINEL为实际Agent
```

### 12.4 工具集组合与平台隔离

```
工具集定义 (toolsets.py):
──────────────────────────
_HERMES_CORE_TOOLS = [web_search, terminal, read_file, ...]

平台工具集全部引用同一个核心列表:
  hermes-cli:      _HERMES_CORE_TOOLS
  hermes-telegram:  _HERMES_CORE_TOOLS
  hermes-discord:   _HERMES_CORE_TOOLS
  ...

好处:
  1. 修改一处，所有平台同步更新
  2. 平台差异通过 check_fn 控制 (如 send_message 仅在gateway运行时可用)
  3. 工具集可组合: hermes-gateway = union(所有平台工具集)

可用性门控:
  check_fn → 运行时检查
  ├── send_message: 检查gateway是否运行
  ├── browser_*: 检查BROWSERBASE_TOKEN
  ├── web_search: 检查BRAVE_API_KEY/TAVILY_API_KEY
  └── ha_*: 检查HASS_TOKEN
```

### 12.5 上下文压缩的"围栏"设计

```
压缩后的消息结构:
─────────────────
[
  {role: "system", content: "...系统提示..."},
  {role: "user", content: "[CONTEXT COMPACTION — REFERENCE ONLY]
    Earlier turns were compacted...
    ┌─ Resolved Questions ────────
    │  • 如何配置QQ机器人 → 已完成
    ├─ Key Decisions ─────────────
    │  • 使用官方QQ Bot API v2
    ├─ Current State ─────────────
    │  • config.yaml已配置
    └─ Remaining Work ────────────
       • 测试连接"},
  {role: "user", content: "测试一下连接"},    ← 最新用户消息
  {role: "assistant", content: "好的..."},    ← 最新助手回复
]

关键设计:
  1. 摘要前缀明确标注"REFERENCE ONLY"
  2. "不同助手"框架 — 创造分离感
  3. "Remaining Work" 替代 "Next Steps" — 避免被当作活跃指令
  4. 迭代更新 — 后续压缩在之前摘要基础上更新
```

### 12.6 故障转移与错误分类

```
API错误 → classify_api_error()
│
├── FailoverReason.RATE_LIMITED (429)
│   └── 指数退避 + 抖动重试
│
├── FailoverReason.CONTEXT_OVERFLOW (context_length_exceeded)
│   ├── 触发上下文压缩
│   └── 压缩后重试
│
├── FailoverReason.SERVER_ERROR (503, 529)
│   ├── 切换到 fallback_model
│   └── 如果fallback也失败 → 返回错误
│
├── FailoverReason.AUTH_ERROR (401, 403)
│   └── 尝试凭据池中的下一个凭据
│
└── FailoverReason.UNKNOWN
    └── 重试一次，失败则返回错误
```

---

## 附录: 关键数据结构

### AIAgent 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | str | "" | 模型名称 |
| `max_iterations` | int | 90 | 最大工具调用迭代次数 |
| `enabled_toolsets` | List[str] | None | 启用的工具集 |
| `disabled_toolsets` | List[str] | None | 禁用的工具集 |
| `session_id` | str | None | 会话ID |
| `platform` | str | None | 平台标识 (cli/telegram/discord/...) |
| `iteration_budget` | IterationBudget | None | 迭代预算 (子Agent共享) |
| `credential_pool` | CredentialPool | None | 凭据池 (多key轮换) |
| `fallback_model` | Dict | None | 故障转移模型配置 |
| `skip_memory` | bool | False | 跳过记忆加载 (子Agent) |
| `skip_context_files` | bool | False | 跳过上下文文件 (子Agent) |

### ToolEntry 注册条目

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | str | 工具名称 |
| `toolset` | str | 所属工具集 |
| `schema` | dict | OpenAI格式工具Schema |
| `handler` | Callable | 工具处理函数 |
| `check_fn` | Callable | 可用性检查函数 |
| `requires_env` | List[str] | 依赖的环境变量 |
| `is_async` | bool | 是否异步处理函数 |
| `emoji` | str | 显示用emoji |

### SessionEntry 会话条目

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_key` | str | 会话唯一键 |
| `session_id` | str | 会话UUID |
| `platform` | str | 平台标识 |
| `chat_type` | str | dm/group/channel |
| `total_tokens` | int | 累计token使用 |
| `estimated_cost_usd` | float | 估算成本 |
| `was_auto_reset` | bool | 是否被自动重置 |
| `suspended` | bool | 是否暂停 |

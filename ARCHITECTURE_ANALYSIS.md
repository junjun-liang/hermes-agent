# Hermes Agent - Multi-Turn Conversation Architecture Analysis

## 项目概述

Hermes Agent 是一个基于 LLM 的智能代理系统，支持 CLI 和多个消息平台（Telegram、Discord、Slack 等）。该系统实现了完整的多轮对话机制，包括工具调用、上下文管理、会话持久化等功能。

***

## 一、软件架构设计图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HERMES AGENT ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐   │
│  │   CLI Mode   │  │  Gateway Mode │  │  Batch Runner / RL Env     │   │
│  │  (cli.py)    │  │ (gateway/run) │  │  (batch_runner.py)         │   │
│  │              │  │               │  │                            │   │
│  │  - Rich TUI  │  │  - Telegram   │  │  - Parallel processing     │   │
│  │  - REPL      │  │  - Discord    │  │  - Training environments   │   │
│  │  - Spinner   │  │  - Slack      │  │                            │   │
│  │  - Skins     │  │  - WhatsApp   │  │                            │   │
│  └──────────────┘  └──────────────┘  └─────────────────────────────┘   │
│                          │                  │                           │
│                          └────────┬─────────┘                           │
│                                   │                                     │
└───────────────────────────────────┼──────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────┐
│                         ORCHESTRATION LAYER                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    AIAgent (run_agent.py)                       │     │
│  │                                                                 │     │
│  │  ┌──────────────────────────────────────────────────────────┐  │     │
│  │  │  run_conversation() - Core Conversation Loop             │  │     │
│  │  │    while iteration_budget.remaining > 0:                 │  │     │
│  │  │      1. Build messages array                             │  │     │
│  │  │      2. Call LLM API                                     │  │     │
│  │  │      3. If tool_calls: execute tools                     │  │     │
│  │  │      4. If content: return response                      │  │     │
│  │  └──────────────────────────────────────────────────────────┘  │     │
│  │                                                                 │     │
│  │  - IterationBudget management (max_iterations: 90)             │     │
│  │  - Context compression trigger                                 │     │
│  │  - System prompt assembly                                      │     │
│  │  - Memory integration                                          │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │              model_tools.py - Tool Orchestration               │     │
│  │                                                                 │     │
│  │  - get_tool_definitions() - Schema collection                  │     │
│  │  - handle_function_call() - Tool dispatch                      │     │
│  │  - _discover_tools() - Module import & registration            │     │
│  │  - Async bridging (_run_async)                                 │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────┐
│                         TOOL LAYER                                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              tools/registry.py - Central Registry                │    │
│  │   - register(name, schema, handler, check_fn)                   │    │
│  │   - get_definitions(tools_to_include)                           │    │
│  │   - dispatch(tool_name, args, **kwargs)                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       │               │               │               │                  │
│       │               │               │               │                  │
│  ┌────▼────┐   ┌─────▼─────┐  ┌──────▼──────┐  ┌─────▼─────┐           │
│  │  File   │   │   Web     │  │  Terminal   │  │  Vision   │           │
│  │  Tools  │   │   Tools   │  │    Tool     │  │   Tools   │           │
│  │         │   │           │  │             │  │           │           │
│  │ read    │   │ web_search│  │  terminal   │  │  vision   │           │
│  │ write   │   │ web_extract│ │  (local/    │  │  analyze  │           │
│  │ patch   │   │           │  │   docker)   │  │           │           │
│  │ search  │   │           │  │             │  │           │           │
│  └─────────┘   └───────────┘  └─────────────┘  └───────────┘           │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐   │
│  │  Browser     │  │   Skills     │  │   Code Execution            │   │
│  │  Tool        │  │   Manager    │  │   Tool                      │   │
│  │              │  │              │  │                             │   │
│  │  browser_    │  │  skill_view  │  │  execute_code               │   │
│  │  navigate    │  │  skill_manage│  │  (sandbox with RPC)         │   │
│  │  snapshot    │  │              │  │                             │   │
│  └──────────────┘  └──────────────┘  └─────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                         STATE MANAGEMENT LAYER                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              hermes_state.py - SessionDB (SQLite)                │    │
│  │                                                                  │    │
│  │  Tables:                                                         │    │
│  │  - sessions: metadata, token counts, model config               │    │
│  │  - messages: full message history with FTS5 index               │    │
│  │                                                                  │    │
│  │  Features:                                                       │    │
│  │  - WAL mode for concurrent access                               │    │
│  │  - FTS5 full-text search                                        │    │
│  │  - Parent-child session chains (compression)                    │    │
│  │  - Thread-safe with retry logic                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              Memory System (memory_tool.py)                      │    │
│  │   - Persistent user preferences                                 │    │
│  │   - Environment details                                         │    │
│  │   - Tool quirks & conventions                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              Todo System (todo_tool.py)                          │    │
│  │   - Task tracking within sessions                               │    │
│  │   - Progress management                                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                         SUPPORTING SERVICES                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Context     │  │  Prompt      │  │  Auxiliary   │  │  Usage     │  │
│  │  Compressor  │  │  Builder     │  │  Client      │  │  Pricing   │  │
│  │              │  │              │  │              │  │            │  │
│  │  - Summarize │  │  - Identity  │  │  - Vision    │  │  - Token   │  │
│  │    middle    │  │  - Platform  │  │  - Web       │  │    count   │  │
│  │  - Protect   │  │  - Skills    │  │    extract   │  │  - Cost    │  │
│  │    head/tail │  │  - Context   │  │  - Approval  │  │    estim.  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │  Skill       │  │  Plugin      │  │  Environment                 │  │
│  │  System      │  │  System      │  │  Backends                    │  │
│  │              │  │              │  │                              │  │
│  │  - ~/skills/ │  │  - User      │  │  - Local                     │  │
│  │  - YAML      │  │    plugins   │  │  - Docker                    │  │
│  │  - Platform  │  │  - Project   │  │  - SSH                       │  │
│  │    filtering │  │    hooks     │  │  - Modal/Daytona             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

***

## 二、核心组件详解

### 1. AIAgent 类 (run\_agent.py)

**职责**: 对话循环编排、工具调用管理、上下文压缩触发

**核心方法**:

- `run_conversation()`: 主对话循环
- `chat()`: 简单聊天接口
- `_build_system_prompt()`: 系统提示组装
- `_execute_tool_call()`: 工具执行

**关键特性**:

- IterationBudget 管理 (默认 90 次迭代)
- 上下文压缩自动触发
- 工具调用并行化
- 线程安全的状态管理

### 2. Tool Registry (tools/registry.py)

**职责**: 工具注册、调度、可用性检查

**架构**:

```python
class ToolRegistry:
    def register(name, schema, handler, check_fn, requires_env)
    def get_definitions(tools_to_include)
    def dispatch(tool_name, args, **kwargs)
    def check_toolset_requirements()
```

**工具分类**:

- **核心工具**: terminal, file\_tools, web\_tools
- **可选工具**: browser, vision, skills
- **平台工具**: homeassistant, mcp
- **Agent 级工具**: memory, todo, session\_search

### 3. SessionDB (hermes\_state.py)

**职责**: 会话持久化、消息历史存储、全文搜索

**数据库结构**:

```sql
sessions:
  - id, source, user_id, model
  - started_at, ended_at, end_reason
  - message_count, tool_call_count
  - token counts (input/output/cache/reasoning)
  - parent_session_id (compression chains)
  
messages:
  - session_id, role, content
  - tool_calls, tool_call_id, tool_name
  - timestamp, token_count, finish_reason
  - reasoning, reasoning_details
```

### 4. Context Compressor (agent/context\_compressor.py)

**职责**: 上下文窗口管理、对话摘要

**压缩算法**:

1. 保护头部 (系统提示 + 前 3 条消息)
2. 保护尾部 (最近 20K tokens)
3. 摘要中间部分
4. 迭代更新摘要

**触发条件**:

- 达到模型上下文限制的 50%
- 或超过配置的阈值

***

## 三、多轮对话流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MULTI-TURN CONVERSATION FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  User Message   │
│  (CLI/Gateway)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Session Initialization                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 1a. Resolve/Create Session ID                                    │  │
│  │     - CLI: generate UUID                                         │  │
│  │     - Gateway: hash(platform + chat_id + user_id)                │  │
│  │                                                                  │  │
│  │ 1b. Load Session Context                                         │  │
│  │     - SessionDB.get_messages()                                   │  │
│  │     - Memory: build_memory_context_block()                       │  │
│  │     - Todo: load active todos                                    │  │
│  │                                                                  │  │
│  │ 1c. Build System Prompt                                          │  │
│  │     - Agent identity                                             │  │
│  │     - Platform hints                                             │  │
│  │     - Memory context                                             │  │
│  │     - Skills index                                               │  │
│  │     - Context files (.hermes.md, AGENTS.md)                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Append User Message to History                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  messages.append({                                                      │
│    "role": "user",                                                      │
│    "content": user_message                                              │
│  })                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Context Compression Check                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ ContextEngine.check_compression()                                │  │
│  │   - Estimate current tokens                                      │  │
│  │   - If tokens >= threshold:                                      │  │
│  │       compress_context()                                         │  │
│  │       - Prune old tool results                                   │  │
│  │       - Summarize middle turns                                   │  │
│  │       - Create parent_session_id chain                           │  │
│  │       - Rebuild system prompt                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: LLM API Call                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ response = client.chat.completions.create(                       │  │
│  │   model=model,                                                   │  │
│  │   messages=messages,                                             │  │
│  │   tools=tool_schemas,                                            │  │
│  │   temperature=temperature,                                       │  │
│  │   max_tokens=max_tokens                                          │  │
│  │ )                                                                │  │
│  │                                                                  │  │
│  │ - Apply prompt caching (Anthropic)                               │  │
│  │ - Handle context length errors (fallback models)                 │  │
│  │ - Track token usage                                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 5: Response Processing                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ IF response.tool_calls:                                          │  │
│  │   ┌──────────────────────────────────────────────────────────┐  │  │
│  │   │ STEP 6: Tool Execution Loop                              │  │  │
│  │   │                                                          │  │  │
│  │   │ For each tool_call in response.tool_calls:               │  │  │
│  │   │   1. Parse tool name & arguments                         │  │  │
│  │   │   2. Coerce argument types (string→int/bool)             │  │  │
│  │   │   3. Check tool availability                             │  │  │
│  │   │   4. Execute tool:                                       │  │  │
│  │   │      - Agent-level: memory, todo, session_search         │  │  │
│  │   │      - Registry dispatch: all other tools                │  │  │
│  │   │   5. Handle async execution (_run_async)                 │  │  │
│  │   │   6. Capture tool result (JSON string)                   │  │  │
│  │   │   7. Append tool result to messages:                     │  │  │
│  │   │      messages.append({                                   │  │  │
│  │   │        "role": "tool",                                   │  │  │
│  │   │        "tool_call_id": call_id,                          │  │  │
│  │   │        "content": tool_result                            │  │  │
│  │   │      })                                                  │  │  │
│  │   │                                                          │  │  │
│  │   │ Parallel execution:                                      │  │  │
│  │   │   - Safe tools: web_search, read_file, etc.              │  │  │
│  │   │   - Sequential: clarify, terminal, browser               │  │  │
│  │   │   - Path-scoped: read/write_file (no overlap)            │  │  │
│  │   └──────────────────────────────────────────────────────────┘  │  │
│  │   │                                                               │  │
│  │   ▼                                                               │  │
│  │   Check iteration budget                                           │  │
│  │   - If budget.exhausted: return error                            │  │
│  │   - Else: continue loop                                          │  │
│  │                                                                   │  │
│  │ ELSE response.content:                                            │  │
│  │   ┌──────────────────────────────────────────────────────────┐   │  │
│  │   │ STEP 7: Final Response                                   │   │  │
│  │   │                                                          │   │  │
│  │   │ - Stream to user (if streaming enabled)                  │   │  │
│  │   │ - Save to SessionDB                                      │   │  │
│  │   │ - Update token counts                                    │   │  │
│  │   │ - Calculate cost                                         │   │  │
│  │   │ - Return response                                        │   │  │
│  │   └──────────────────────────────────────────────────────────┘   │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 8: Post-Processing                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ - Save trajectory (if enabled)                                   │  │
│  │ - Trigger skill creation (complex tasks)                         │  │
│  │ - Update memory (user preferences)                               │  │
│  │ - Clean up resources (browser, terminal envs)                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Return to User │
└─────────────────┘
```

***

## 四、工具调用详细流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TOOL CALL EXECUTION FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Tool Call from  │
│  LLM Response    │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  1. Argument Parsing & Type Coercion                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  coerce_tool_args(tool_name, args)                                      │
│  - "42" → 42 (integer)                                                  │
│  - "true" → true (boolean)                                              │
│  - Union types: try each in order                                       │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. Check if Agent-Level Tool                                           │
├─────────────────────────────────────────────────────────────────────────┤
│  _AGENT_LOOP_TOOLS = {"memory", "todo", "session_search"}              │
│                                                                          │
│  IF tool_name in _AGENT_LOOP_TOOLS:                                     │
│    - Intercept before registry dispatch                                 │
│    - Access agent state (MemoryStore, TodoStore)                        │
│    - Return stub error if not handled                                   │
│  ELSE:                                                                  │
│    - Continue to registry dispatch                                      │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. Plugin Hooks (Pre-call)                                             │
├─────────────────────────────────────────────────────────────────────────┤
│  invoke_hook("pre_tool_call", ...)                                      │
│  - User plugins can intercept/modify                                    │
│  - Logging & auditing                                                   │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. Registry Dispatch                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  registry.dispatch(tool_name, args, task_id, **kwargs)                  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Async Bridging: _run_async(coro)                                 │  │
│  │ - Check for running loop                                         │  │
│  │ - If running: spin up disposable thread                          │  │
│  │ - If not running: use persistent _tool_loop                      │  │
│  │ - Worker threads: per-thread _worker_loop                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Handler Execution:                                               │  │
│  │ - Sync tools: direct call                                        │  │
│  │ - Async tools: await handler()                                   │  │
│  │ - All handlers return JSON string                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  5. Plugin Hooks (Post-call)                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  invoke_hook("post_tool_call", tool_name, args, result)                 │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  6. Result Processing                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  - Parse JSON result                                                    │
│  - Check for errors                                                     │
│  - Format for LLM (tool result message)                                 │
│  - Persist to SessionDB                                                 │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  7. Parallel Tool Execution (if batch)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  _should_parallelize_tool_batch(tool_calls)                             │
│  - Never parallel: clarify, terminal, browser                           │
│  - Parallel safe: web_search, read_file, vision_analyze                 │
│  - Path scoped: read/write_file (check for overlap)                     │
│                                                                          │
│  Execution:                                                             │
│  - ThreadPoolExecutor (max 8 workers)                                   │
│  - Sequential fallback for unsafe batches                               │
└─────────────────────────────────────────────────────────────────────────┘
```

***

## 五、会话管理流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SESSION LIFECYCLE FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  New Session    │
│  (CLI/Gateway)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Session Creation                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  CLI:                                                                   │
│  - Generate UUID                                                        │
│  - Source: "cli"                                                        │
│  - Working directory: cwd or MESSAGING_CWD                              │
│                                                                          │
│  Gateway:                                                               │
│  - Session key: hash(platform + chat_id + user_id)                      │
│  - Source: platform enum (telegram, discord, etc.)                      │
│  - PII redaction (optional)                                             │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SessionDB.create_session()                                             │
├─────────────────────────────────────────────────────────────────────────┤
│  INSERT INTO sessions (                                                 │
│    id, source, user_id, model,                                          │
│    started_at, system_prompt                                            │
│  )                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Conversation Turns                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  For each turn:                                                         │
│  1. append_message(role="user", content=...)                            │
│  2. LLM API call                                                        │
│  3. append_message(role="assistant", content=...)                       │
│  4. For tool calls: append_message(role="tool", ...)                    │
│  5. update_token_counts(...)                                            │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Context Compression (if needed)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Summarize middle turns                                              │
│  2. Create new session with parent_session_id                           │
│  3. Chain sessions: parent → child → grandchild                         │
│  4. Continue conversation in child session                              │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Session End                                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Triggers:                                                              │
│  - User command (/exit, /new)                                           │
│  - Max iterations reached                                               │
│  - Context compression limit                                            │
│  - Gateway inactivity timeout                                           │
│                                                                          │
│  SessionDB.end_session(session_id, end_reason)                          │
│  UPDATE sessions SET                                                    │
│    ended_at = ?, end_reason = ?                                         │
│  WHERE id = ?                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Session Search & Recall                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  FTS5 Search:                                                           │
│  - search_messages(query, source_filter, role_filter)                   │
│  - Returns snippets with context                                        │
│                                                                          │
│  Session Loading:                                                       │
│  - get_messages_as_conversation()                                       │
│  - Replays as OpenAI format                                             │
│  - Includes reasoning details                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

***

## 六、Gateway 多平台架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GATEWAY MULTI-PLATFORM ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                         Platform Adapters                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Telegram    │  │   Discord    │  │    Slack     │  │  WhatsApp  │  │
│  │              │  │              │  │              │  │            │  │
│  │  - Bot API   │  │  - Gateway   │  │  - Events API│  │  - Cloud   │  │
│  │  - Updates   │  │  - Intents   │  │  - Socket    │  │    API     │  │
│  │  - Long      │  │  - Messages  │  │  Mode        │  │  - Webhook │  │
│  │    polling   │  │  - Events    │  │              │  │            │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Signal     │  │    Home      │  │   Blue       │  │   Local    │  │
│  │              │  │  Assistant   │  │  Bubbles     │  │   (CLI)    │  │
│  │  - JSON-RPC  │  │              │  │  (macOS)     │  │            │  │
│  │  - REST API  │  │  - REST API  │  │  - AppleScript│ │            │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      Gateway Core (gateway/run.py)                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  GatewayRunner                                                   │   │
│  │    - Start all platform adapters                                 │   │
│  │    - Manage async event loop                                     │   │
│  │    - Handle graceful shutdown                                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  SessionStore (gateway/session.py)                               │   │
│  │    - Build session context                                       │   │
│  │    - PII redaction                                               │   │
│  │    - Dynamic system prompt injection                             │   │
│  │    - Session reset policies                                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  DeliveryRouter (gateway/delivery.py)                            │   │
│  │    - Route responses to correct platform                         │   │
│  │    - Handle scheduled task outputs                               │   │
│  │    - Manage home channels                                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      Slash Command Processing                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Command Registry (hermes_cli/commands.py):                              │
│  - COMMAND_REGISTRY: list of CommandDef                                 │
│  - Categories: Session, Configuration, Tools & Skills, Info, Exit       │
│                                                                          │
│  Processing:                                                             │
│  1. Parse slash command (/model, /tools, /skills, etc.)                 │
│  2. Resolve aliases via resolve_command()                               │
│  3. Dispatch to handler in HermesCLI.process_command()                  │
│  4. Gateway handlers in gateway/run.py                                  │
│                                                                          │
│  Examples:                                                               │
│  - /model anthropic/claude-opus-4.6                                     │
│  - /tools enable web terminal                                           │
│  - /skills install github                                               │
│  - /session search "docker deployment"                                  │
│  - /new, /reset, /exit                                                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

***

## 七、关键设计模式

### 1. **Registry Pattern** (工具注册)

所有工具通过 `registry.register()` 自注册，集中管理 schema、handler 和可用性检查。

### 2. **Strategy Pattern** (上下文压缩引擎)

```python
class ContextEngine:
    def should_compress() -> bool
    def compress() -> List[Dict]
    def on_session_reset()
```

实现类：

- `ContextCompressor`: 默认压缩引擎
- 可扩展其他策略

### 3. **Observer Pattern** (插件钩子)

```python
invoke_hook("pre_tool_call", ...)
invoke_hook("post_tool_call", ...)
```

### 4. **Factory Pattern** (环境后端)

```python
def create_environment(env_type: str) -> Environment:
    - local: LocalEnvironment
    - docker: DockerEnvironment
    - ssh: SSHEnvironment
    - modal: ModalEnvironment
```

### 5. **Repository Pattern** (SessionDB)

SQLite -backed repository for session persistence with:

- Unit of Work (transaction management)
- FTS5 search
- Parent-child relationships

***

## 八、数据流图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW DIAGRAM                                │
└─────────────────────────────────────────────────────────────────────────┘

User Input
    │
    ▼
┌─────────────────┐
│  Message Event  │
│  (Platform      │
│   Adapter)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  SessionStore   │────▶│  SessionDB      │
│  - Build ctx    │     │  - Load history │
│  - PII redact   │     │  - Save msgs    │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  AIAgent        │
│  - Build prompt │
│  - Check compress│
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  LLM API        │◀───▶│  Token Tracking │
│  - Completions  │     │  - Cost calc    │
└────────┬────────┘     └─────────────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐ ┌─────────────────┐
│  Tool Calls     │ │  Final Response │
│  - Registry     │ │  - Stream to    │
│  - Async exec   │ │    user         │
│  - Parallel     │ │  - Save to DB   │
└────────┬────────┘ └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Plugin Hooks   │
│  - pre/post     │
│  - Logging      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Memory/Skills  │
│  - Update       │
│  - Create       │
└─────────────────┘
```

***

## 九、配置系统

### 配置文件层级

```
~/.hermes/config.yaml  (用户配置 - 优先)
./cli-config.yaml      (项目配置 - 回退)
./.env                 (环境变量)
~/.hermes/.env         (用户环境变量)
```

### 核心配置项

```yaml
model:
  default: "anthropic/claude-opus-4.6"
  provider: "auto"
  
terminal:
  backend: "local"
  timeout: 60
  
compression:
  enabled: true
  threshold: 0.50
  
agent:
  max_turns: 90
  personalities:
    helpful: "..."
    concise: "..."
    
display:
  skin: "default"
  streaming: true
```

***

## 十、安全与权限

### 1. **命令审批系统**

```python
# tools/approval.py
def is_destructive_command(cmd: str) -> bool:
    # 检测 rm, mv, dd 等危险命令
```

### 2. **PII 保护**

- 用户 ID 哈希化
- 聊天记录 ID 脱敏
- 平台特定的 redact\_pii 选项

### 3. **环境隔离**

- Docker 沙箱
- 工作目录限制
- 环境变量过滤

### 4. **配置文件扫描**

- 检测 AGENTS.md/.cursorrules 中的提示注入
- 阻止隐藏 div、不可见 unicode 字符

***

## 十一、性能优化

### 1. **上下文压缩**

- 工具结果预剪枝 (无需 LLM)
- 头部/尾部保护
- 迭代摘要更新

### 2. **并行工具执行**

- ThreadPoolExecutor (8 workers)
- 路径作用域工具并发
- 只读工具并行安全

### 3. **Prompt Caching**

- Anthropic cache control
- 系统提示缓存
- 技能索引缓存

### 4. **SQLite 优化**

- WAL 模式并发
- 应用层重试 + 随机抖动
- 被动 WAL checkpoint

***

## 十二、扩展机制

### 1. **技能系统**

```
~/.hermes/skills/
├── github/
│   ├── index.yaml
│   └── prompts/
├── docker/
└── custom/
```

### 2. **插件系统**

```python
# 钩子函数
def pre_tool_call(...)
def post_tool_call(...)
def on_agent_start(...)
```

### 3. **MCP 集成**

- 外部 MCP 服务器
- 动态工具发现
- 标准协议适配

### 4. **环境后端**

- 本地终端
- Docker 容器
- SSH 远程
- Modal/Daytona 云

***

## 十三、总结

Hermes Agent 的多轮对话设计具有以下特点：

1. **分层架构**: 清晰的职责分离 (展示层、编排层、工具层、状态层)
2. **可扩展性**: Registry pattern + Plugin hooks
3. **持久化**: SQLite + FTS5 全文搜索
4. **上下文管理**: 自动压缩 + 会话链
5. **多平台**: Gateway 架构支持 8+ 平台
6. **安全性**: 命令审批、PII 保护、环境隔离
7. **性能**: 并行工具执行、prompt caching、SQLite WAL

该架构支持从 CLI 单用户到多平台网关的各种部署场景，同时保持代码的可维护性和可扩展性。

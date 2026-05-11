# Hermes Agent - ASCII Architecture Diagrams

## 1. 系统概览 (System Overview)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HERMES AGENT SYSTEM                              │
│                    Multi-Platform AI Assistant                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACES                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐         ┌─────────────────────────────────┐         │
│  │   CLI Mode     │         │      Gateway Mode               │         │
│  │                │         │                                 │         │
│  │  ┌──────────┐  │         │  ┌─────┐ ┌─────┐ ┌─────┐       │         │
│  │  │  Rich    │  │         │  │ Tel │ │ Dis │ │ Slk │ ...   │         │
│  │  │    TUI   │  │         │  └─────┘ └─────┘ └─────┘       │         │
│  │  └──────────┘  │         │                                 │         │
│  │  ┌──────────┐  │         │  ┌─────────────────────────┐   │         │
│  │  │  REPL    │  │         │  │  Platform Adapters      │   │         │
│  │  │  Input   │  │         │  │  - Telegram Bot         │   │         │
│  │  └──────────┘  │         │  │  - Discord Gateway      │   │         │
│  │  ┌──────────┐  │         │  │  - Slack Events API     │   │         │
│  │  │  Skin    │  │         │  │  - WhatsApp Cloud       │   │         │
│  │  │  Engine  │  │         │  │  - Signal JSON-RPC      │   │         │
│  │  └──────────┘  │         │  └─────────────────────────┘   │         │
│  └────────────────┘         └─────────────────────────────────┘         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         AIAgent Class                               │ │
│  │                      (run_agent.py)                                 │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │              run_conversation() Loop                          │  │ │
│  │  │                                                               │  │ │
│  │  │   while iteration_budget.remaining > 0:                       │  │ │
│  │  │     1. Build messages array (system + history + user)         │  │ │
│  │  │     2. Check context compression threshold                    │  │ │
│  │  │     3. Call LLM API with tools                                │  │ │
│  │  │     4. If tool_calls: execute tools → append results          │  │ │
│  │  │     5. If content: stream response → save → return            │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  │                                                                     │ │
│  │  Key Components:                                                    │ │
│  │  - IterationBudget (max: 90 turns)                                 │ │
│  │  - ContextEngine (compression at 50% threshold)                    │ │
│  │  - MemoryStore (persistent context)                                │ │
│  │  - TodoStore (task tracking)                                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    model_tools.py                                   │ │
│  │                                                                     │ │
│  │  - get_tool_definitions() → filter by toolset                      │ │
│  │  - handle_function_call() → dispatch to registry                   │ │
│  │  - _discover_tools() → import modules → register                   │ │
│  │  - _run_async() → bridge sync/async                                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           TOOL LAYER                                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  tools/registry.py                                │   │
│  │                                                                   │   │
│  │  Central Registry Pattern:                                        │   │
│  │  - register(name, schema, handler, check_fn)                      │   │
│  │  - get_definitions(tools_to_include)                              │   │
│  │  - dispatch(tool_name, args, **kwargs)                            │   │
│  │  - check_tool_availability()                                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│       │                │                │                │               │
│       │                │                │                │               │
│  ┌────▼────┐    ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐        │
│  │   File  │    │    Web      │  │  Terminal │  │   Browser   │        │
│  │   Tools │    │    Tools    │  │   Tool    │  │    Tool     │        │
│  │          │    │             │  │           │  │             │        │
│  │  read    │    │  web_search │  │  terminal │  │  navigate   │        │
│  │  write   │    │  web_extract│  │  (local/  │  │  snapshot   │        │
│  │  patch   │    │             │  │   docker) │  │  click/type │        │
│  │  search  │    │             │  │           │  │  scroll     │        │
│  └──────────┘    └─────────────┘  └───────────┘  └─────────────┘        │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐    │
│  │    Vision    │  │    Skills    │  │   Code Execution           │    │
│  │    Tools     │  │   Manager    │  │        Tool                │    │
│  │              │  │              │  │                            │    │
│  │  vision_     │  │  skill_view  │  │  execute_code              │    │
│  │  analyze     │  │  skill_manage│  │  (sandbox with RPC)        │    │
│  └──────────────┘  └──────────────┘  └────────────────────────────┘    │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐    │
│  │    Memory    │  │     Todo     │  │   Session Search           │    │
│  │     Tool     │  │     Tool     │  │        Tool                │    │
│  │              │  │              │  │                            │    │
│  │  memory save │  │  todo create │  │  session_search            │    │
│  │  memory load │  │  todo update │  │  (FTS5 search)             │    │
│  └──────────────┘  └──────────────┘  └────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       STATE MANAGEMENT LAYER                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              hermes_state.py - SessionDB (SQLite)                 │   │
│  │                                                                   │   │
│  │  Database Schema:                                                 │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │  sessions                                                  │  │   │
│  │  │  ├── id (PK)                                               │  │   │
│  │  │  ├── source (cli/telegram/discord/...)                     │  │   │
│  │  │  ├── user_id, model, system_prompt                         │  │   │
│  │  │  ├── started_at, ended_at, end_reason                      │  │   │
│  │  │  ├── message_count, tool_call_count                        │  │   │
│  │  │  ├── token counts (input/output/cache/reasoning)           │  │   │
│  │  │  ├── cost estimates                                        │  │   │
│  │  │  └── parent_session_id (compression chains)                │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │  messages                                                  │  │   │
│  │  │  ├── id (autoinc)                                          │  │   │
│  │  │  ├── session_id (FK)                                       │  │   │
│  │  │  ├── role (user/assistant/tool)                            │  │   │
│  │  │  ├── content, tool_calls, tool_call_id                     │  │   │
│  │  │  ├── timestamp, token_count, finish_reason                 │  │   │
│  │  │  └── reasoning, reasoning_details                          │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  │                                                                   │   │
│  │  Features:                                                        │   │
│  │  - WAL mode (concurrent read, single write)                      │   │
│  │  - FTS5 full-text search index                                   │   │
│  │  - Thread-safe with retry + jitter                               │   │
│  │  - Parent-child session chains (compression)                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Memory System (memory_tool.py)                       │   │
│  │   - Persistent user preferences                                  │   │
│  │   - Environment details                                          │   │
│  │   - Tool quirks & conventions                                    │   │
│  │   - Injected via build_memory_context_block()                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      SUPPORTING SERVICES                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Context    │  │    Prompt    │  │  Auxiliary   │  │    Usage   │  │
│  │  Compressor  │  │    Builder   │  │   Client     │  │   Pricing  │  │
│  │              │  │              │  │              │  │            │  │
│  │  - Estimate  │  │  - Identity  │  │  - Vision    │  │  - Token   │  │
│  │    tokens    │  │  - Platform  │  │  - Web       │  │    count   │  │
│  │  - Summarize │  │  - Skills    │  │  - Approval  │  │  - Cost    │  │
│  │    middle    │  │  - Context   │  │    calls     │  │    estim.  │  │
│  │  - Protect   │  │  - Memory    │  │              │  │            │  │
│  │    head/tail │  │              │  │              │  │            │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │    Skill     │  │    Plugin    │  │   Environment                │  │
│  │    System    │  │    System    │  │   Backends                   │  │
│  │              │  │              │  │                              │  │
│  │  - YAML      │  │  - Hooks:    │  │  - LocalEnvironment          │  │
│  │    index     │  │    pre/post  │  │  - DockerEnvironment         │  │
│  │  - Prompts   │  │  - User      │  │  - SSHEnvironment            │  │
│  │  - Platform  │  │    plugins   │  │  - Modal/Daytona             │  │
│  │    filtering │  │  - Project   │  │                              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## 2. 对话循环详细流程 (Conversation Loop Detail)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONVERSATION LOOP - DETAILED FLOW                     │
└─────────────────────────────────────────────────────────────────────────┘

User Input
    │
    ├──────────────────────────────────────────────────────────────────┐
    │ STEP 1: SESSION INITIALIZATION                                   │
    │ ┌────────────────────────────────────────────────────────────┐  │
    │ │ • Generate/Resolve Session ID                              │  │
    │ │   - CLI: UUID                                              │  │
    │ │   - Gateway: hash(platform + chat_id + user_id)            │  │
    │ │                                                            │  │
    │ │ • Load Conversation History                                │  │
    │ │   - SessionDB.get_messages()                               │  │
    │ │   - Format as OpenAI messages                              │  │
    │ │                                                            │  │
    │ │ • Build Memory Context                                     │  │
    │ │   - MemoryStore.load()                                     │  │
    │ │   - build_memory_context_block()                           │  │
    │ │                                                            │  │
    │ │ • Assemble System Prompt                                   │  │
    │ │   - Agent identity                                         │  │
    │ │   - Platform hints                                         │  │
    │ │   - Memory context                                         │  │
    │ │   - Skills index                                           │  │
    │ │   - Context files (.hermes.md, AGENTS.md)                  │  │
    │ └────────────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 2: APPEND USER MESSAGE                                            │
│ ┌──────────────────────────────────────────────────────────────────┐   │
│ │ messages.append({                                                 │   │
│ │   "role": "user",                                                 │   │
│ │   "content": user_message                                         │   │
│ │ })                                                                │   │
│ └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 3: CONTEXT COMPRESSION CHECK                                      │
│ ┌──────────────────────────────────────────────────────────────────┐   │
│ │ ContextEngine.check_compression()                                │   │
│ │                                                                  │   │
│ │ • Estimate current token count                                   │   │
│ │ • Compare to threshold (50% of context limit)                    │   │
│ │                                                                  │   │
│ │ IF compression needed:                                           │   │
│ │   ┌────────────────────────────────────────────────────────┐    │   │
│ │   │ 1. Prune old tool results (cheap pre-pass)             │    │   │
│ │   │ 2. Protect head (first 3 messages)                     │    │   │
│ │   │ 3. Protect tail (last 20K tokens)                      │    │   │
│ │   │ 4. Summarize middle with LLM                           │    │   │
│ │   │ 5. Create child session with parent_session_id         │    │   │
│ │   │ 6. Rebuild system prompt                               │    │   │
│ │   │ 7. Continue in child session                           │    │   │
│ │   └────────────────────────────────────────────────────────┘    │   │
│ └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4: LLM API CALL                                                   │
│ ┌──────────────────────────────────────────────────────────────────┐   │
│ │ response = client.chat.completions.create(                       │   │
│ │   model=model,                                                   │   │
│ │   messages=messages,                                             │   │
│ │   tools=tool_schemas,                                            │   │
│ │   temperature=temperature,                                       │   │
│ │   max_tokens=max_tokens                                          │   │
│ │ )                                                                │   │
│ │                                                                  │   │
│ │ • Apply prompt caching (Anthropic)                               │   │
│ │ • Handle context length errors (fallback)                        │   │
│ │ • Track token usage                                              │   │
│ └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
    │
    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    ▼                                                                 ▼
┌───────────────────┐                                   ┌──────────────────┐
│ HAS TOOL CALLS    │                                   │ CONTENT ONLY     │
│ (tool_calls list) │                                   │ (final response) │
└─────────┬─────────┘                                   └────────┬─────────┘
          │                                                      │
          │ STEP 5A: TOOL EXECUTION                               │ STEP 5B: FINALIZE
          │                                                      │
          ▼                                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────────────────────────────────────────────────────┐   │
│ │ For each tool_call:                                              │   │
│ │                                                                  │   │
│ │ 1. Parse tool name & arguments                                   │   │
│ │ 2. Coerce types (string → int/bool)                              │   │
│ │ 3. Check if agent-level tool (memory/todo)                       │   │
│ │ 4. Execute via registry.dispatch()                               │   │
│ │ 5. Handle async (_run_async)                                     │   │
│ │ 6. Capture JSON result                                           │   │
│ │                                                                  │   │
│ │ Parallel Execution:                                              │   │
│ │ • Safe tools (web_search, read_file): ThreadPoolExecutor         │   │
│ │ • Sequential (clarify, terminal): One by one                     │   │
│ │ • Path-scoped (read/write): Check overlap                        │   │
│ │                                                                  │   │
│ │ 7. Append tool result to messages:                               │   │
│ │    messages.append({                                             │   │
│ │      "role": "tool",                                             │   │
│ │      "tool_call_id": call_id,                                    │   │
│ │      "content": tool_result                                      │   │
│ │    })                                                            │   │
│ │                                                                  │   │
│ │ 8. Check iteration budget                                        │   │
│ │    • If exhausted: return error                                 │   │
│ │    • Else: continue loop (back to STEP 4)                       │   │
│ └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │                                                      │
          │                                                      │
          ▼                                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 6: POST-PROCESSING                                                │
│ ┌──────────────────────────────────────────────────────────────────┐   │
│ │ • Stream response to user (if enabled)                           │   │
│ │ • Save to SessionDB                                              │   │
│ │ • Update token counts                                            │   │
│ │ • Calculate cost                                                 │   │
│ │ • Trigger skill creation (complex tasks)                         │   │
│ │ • Update memory (preferences)                                    │   │
│ │ • Cleanup resources (browser, terminal)                          │   │
│ └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
     Return to User
```

## 3. 工具注册架构 (Tool Registry Architecture)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TOOL REGISTRY ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ TOOL DISCOVERY (Startup)                                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ _discover_tools()                                                        │
│   │                                                                      │
│   ├─► Import tools.web_tools                                             │
│   │   └─► registry.register(                                             │
│   │         name="web_search",                                           │
│   │         schema={...},                                                │
│   │         handler=web_search,                                          │
│   │         check_fn=check_requirements,                                 │
│   │         requires_env=["SEARCH_API_KEY"]                              │
│   │       )                                                              │
│   │                                                                      │
│   ├─► Import tools.terminal_tool                                         │
│   │   └─► registry.register(...)                                         │
│   │                                                                      │
│   ├─► Import tools.file_tools                                            │
│   │   └─► registry.register(...)                                         │
│   │                                                                      │
│   └─► ... (all tool modules)                                             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ TOOL FILTERING (Per Session)                                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ get_tool_definitions(enabled_toolsets, disabled_toolsets)                │
│   │                                                                      │
│   ├─► Resolve toolsets                                                   │
│   │   - enabled: ["web", "terminal"] → ["web_search", "web_extract",    │
│   │                                      "terminal"]                     │
│   │   - disabled: ["browser"] → exclude browser_* tools                 │
│   │                                                                      │
│   ├─► registry.get_definitions(tools_to_include)                         │
│   │   │                                                                  │
│   │   ├─► For each tool:                                                 │
│   │   │   1. Check if in tools_to_include                               │
│   │   │   2. Run check_fn()                                              │
│   │   │      - Check env vars present                                    │
│   │   │      - Check API keys configured                                 │
│   │   │      - Check requirements met                                    │
│   │   │   3. If passes: add schema to list                              │
│   │   │   4. If fails: skip tool                                        │
│   │   │                                                                  │
│   │   └─► Return filtered schemas                                        │
│   │                                                                      │
│   └─► Post-process schemas                                               │
│       - Update execute_code sandbox tools                                │
│       - Strip cross-references (browser_navigate → web_search)          │
│       - Return final list                                                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ TOOL DISPATCH (Runtime)                                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ handle_function_call(tool_name, args, task_id)                           │
│   │                                                                      │
│   ├─► coerce_tool_args(tool_name, args)                                  │
│   │   - "42" → 42 (integer)                                              │
│   │   - "true" → true (boolean)                                          │
│   │                                                                      │
│   ├─► Check _AGENT_LOOP_TOOLS                                            │
│   │   - If memory/todo/session_search: intercept in agent loop          │
│   │   - Else: continue to registry                                       │
│   │                                                                      │
│   ├─► invoke_hook("pre_tool_call")                                       │
│   │   - Plugin interception                                                │
│   │   - Logging                                                          │
│   │                                                                      │
│   ├─► registry.dispatch(tool_name, args, task_id)                        │
│   │   │                                                                  │
│   │   ├─► Lookup handler                                                 │
│   │   ├─► _run_async(handler(args, task_id))                             │
│   │   │   │                                                              │
│   │   │   ├─► If running loop: spin up thread                           │
│   │   │   ├─► If no loop: use _tool_loop (persistent)                   │
│   │   │   └─► If worker thread: use _worker_loop (per-thread)          │
│   │   │                                                                  │
│   │   └─► Return JSON result                                             │
│   │                                                                      │
│   ├─► invoke_hook("post_tool_call")                                      │
│   │                                                                      │
│   └─► Return result to agent loop                                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ TOOL CATEGORIES                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Core Tools (always available):                                           │
│   • terminal      • read_file     • write_file    • patch               │
│   • search_files  • clarify                                              │
│                                                                          │
│ Web Tools (require API key):                                             │
│   • web_search    • web_extract                                          │
│                                                                          │
│ Vision Tools:                                                            │
│   • vision_analyze                                                       │
│                                                                          │
│ Browser Tools (Browserbase):                                             │
│   • browser_navigate  • browser_snapshot  • browser_click               │
│   • browser_type      • browser_scroll    • browser_back                │
│                                                                          │
│ Code Execution:                                                          │
│   • execute_code (sandbox with RPC to available tools)                  │
│                                                                          │
│ Agent-Level Tools (intercepted):                                         │
│   • memory          • todo          • session_search                     │
│                                                                          │
│ Skills:                                                                  │
│   • skills_list     • skill_view    • skill_manage                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## 4. 会话数据库结构 (Session Database Schema)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SESSIONDB - SQLITE SCHEMA                             │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ sessions TABLE                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ ┌─────────────────────┬──────────────┬─────────────────────────────────┐│
│ | Column Name         | Type         | Description                     ││
│ ├─────────────────────┼──────────────┼─────────────────────────────────┤│
│ | id                  | TEXT (PK)    | Session UUID or hash            ││
│ | source              | TEXT         | "cli", "telegram", "discord"... ││
│ | user_id             | TEXT         | User identifier                 ││
│ | model               | TEXT         | Model string                    ││
│ | model_config        | TEXT (JSON)  | Model configuration             ││
│ | system_prompt       | TEXT         | Full system prompt              ││
│ | parent_session_id   | TEXT (FK)    | Parent session (compression)    ││
│ | started_at          | REAL         | Unix timestamp                  ││
│ | ended_at            | REAL         | Session end timestamp           ││
│ | end_reason          | TEXT         | "max_iterations", "user_exit"...││
│ | message_count       | INTEGER      | Total messages                  ││
│ | tool_call_count     | INTEGER      | Total tool calls                ││
│ | input_tokens        | INTEGER      | Prompt tokens                   ││
│ | output_tokens       | INTEGER      | Completion tokens               ││
│ | cache_read_tokens   | INTEGER      | Cached prompt tokens            ││
│ | cache_write_tokens  | INTEGER      | Cache write tokens              ││
│ | reasoning_tokens    | INTEGER      | Reasoning tokens                ││
│ | estimated_cost_usd  | REAL         | Estimated cost                  ││
│ | actual_cost_usd     | REAL         | Actual cost (if available)      ││
│ | cost_status         | TEXT         | "estimated", "actual"           ││
│ | title               | TEXT         | User-set session title          ││
│ └─────────────────────┴──────────────┴─────────────────────────────────┘│
│                                                                          │
│ Indexes:                                                                 │
│   • idx_sessions_source (source)                                        │
│   • idx_sessions_parent (parent_session_id)                             │
│   • idx_sessions_started (started_at DESC)                              │
│   • idx_sessions_title_unique (title WHERE title IS NOT NULL)          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ messages TABLE                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ ┌─────────────────────┬──────────────┬─────────────────────────────────┐│
│ | Column Name         | Type         | Description                     ││
│ ├─────────────────────┼──────────────┼─────────────────────────────────┤│
│ | id                  | INTEGER (PK) | Auto-increment ID               ││
│ | session_id          | TEXT (FK)    | References sessions.id          ││
│ | role                | TEXT         | "user", "assistant", "tool"     ││
│ | content             | TEXT         | Message content                 ││
│ | tool_call_id        | TEXT         | Tool call ID (for tool role)    ││
│ | tool_calls          | TEXT (JSON)  | Tool calls array                ││
│ | tool_name           | TEXT         | Tool name (for tool role)       ││
│ | timestamp           | REAL         | Unix timestamp                  ││
│ | token_count         | INTEGER      | Tokens for this message         ││
│ | finish_reason       | TEXT         | "stop", "tool_calls", "length"  ││
│ | reasoning           | TEXT         | Reasoning text                  ││
│ | reasoning_details   | TEXT (JSON)  | Structured reasoning            ││
│ | codex_reasoning_items| TEXT (JSON) | Codex reasoning items           ││
│ └─────────────────────┴──────────────┴─────────────────────────────────┘│
│                                                                          │
│ Indexes:                                                                 │
│   • idx_messages_session (session_id, timestamp)                        │
│                                                                          │
│ FTS5 Virtual Table:                                                      │
│   • messages_fts (content)                                               │
│   • Triggers: insert, update, delete                                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ THREAD SAFETY & PERFORMANCE                                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ WAL Mode:                                                                │
│   • Multiple concurrent readers                                         │
│   • Single writer at a time                                             │
│   • No read locks during writes                                         │
│                                                                          │
│ Write Retry Logic:                                                       │
│   • BEGIN IMMEDIATE (acquire lock at start)                             │
│   • On "database is locked":                                             │
│     - Release Python lock                                                │
│     - Sleep random 20-150ms (jitter)                                     │
│     - Retry (max 15 times)                                               │
│   • Prevents convoy effect                                               │
│                                                                          │
│ Checkpointing:                                                           │
│   • PASSIVE checkpoint every 50 writes                                  │
│   • Flushes WAL frames to main DB                                       │
│   • Non-blocking, best-effort                                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## 5. Gateway 多平台架构 (Gateway Multi-Platform)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 GATEWAY MULTI-PLATFORM ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ PLATFORM ADAPTERS (Async Event-Driven)                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌────────────┐│
│ │   Telegram    │  │    Discord    │  │     Slack     │  │  WhatsApp  ││
│ │               │  │               │  │               │  │            ││
│ │ • Bot API     │  │ • Gateway     │  │ • Events API  │  │ • Cloud    ││
│ │ • Long        │  │   WebSocket   │  │ • Socket Mode │  │   API      ││
│ │   Polling     │  │ • Intents     │  │               │  │ • Webhook  ││
│ │               │  │               │  │               │  │            ││
│ │ Updates ──────┼──┼───────────────┼──┼───────────────┼──┼──────────► ││
│ └───────────────┘  └───────────────┘  └───────────────┘  └────────────┘│
│                                                                          │
│ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌────────────┐│
│ │    Signal     │  │ Home Assistant│  │  Blue Bubbles │  │   Local    ││
│ │               │  │               │  │   (macOS)     │  │   (CLI)    ││
│ │ • JSON-RPC    │  │ • REST API    │  │               │  │            ││
│ │ • REST API    │  │ • WebSocket   │  │ • AppleScript │  │ • stdin/   ││
│ │               │  │               │  │               │  │   stdout   ││
│ │ Messages ─────┼──┼───────────────┼──┼───────────────┼──┼──────────► ││
│ └───────────────┘  └───────────────┘  └───────────────┘  └────────────┘│
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ GATEWAY CORE (gateway/run.py)                                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ GatewayRunner                                                      │  │
│ │   • Start all platform adapters (async)                            │  │
│ │   • Manage event loop                                              │  │
│ │   • Handle signals (SIGINT, SIGTERM)                               │  │
│ │   • Graceful shutdown                                              │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ SessionStore (gateway/session.py)                                  │  │
│ │   • Build session context from platform metadata                   │  │
│ │   • PII redaction (optional)                                       │  │
│ │   • Dynamic system prompt injection                                │  │
│ │     - "You are connected to Telegram, Discord..."                  │  │
│ │     - "User is messaging from group: XYZ"                          │  │
│ │   • Session reset policies                                         │  │
│ │     - Per message (stateless)                                      │  │
│ │     - Per conversation (DM-level)                                  │  │
│ │     - Per user (user-level)                                        │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ DeliveryRouter (gateway/delivery.py)                               │  │
│ │   • Route responses to correct platform                            │  │
│ │   • Handle scheduled task outputs (cron jobs)                      │  │
│ │   • Manage home channels                                           │  │
│ │     - User sets preferred output channel                           │  │
│ │     - "Send long outputs to Telegram, quick to Discord"            │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ SLASH COMMAND PROCESSING                                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Command Registry (hermes_cli/commands.py):                               │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ COMMAND_REGISTRY = [                                               │  │
│ │   CommandDef("model", "Switch model", "Configuration",             │  │
│ │              aliases=("m",), args_hint="<model>"),                 │  │
│ │   CommandDef("tools", "Manage tools", "Tools & Skills",            │  │
│ │              aliases=(), args_hint="<enable|disable> ..."),        │  │
│ │   CommandDef("skills", "Manage skills", "Tools & Skills",          │  │
│ │              aliases=(), args_hint="<install|list>"),              │  │
│ │   CommandDef("session", "Session management", "Session",           │  │
│ │              aliases=(), args_hint="<search|list|reset>"),         │  │
│ │   CommandDef("new", "Start new session", "Session",                │  │
│ │              cli_only=True),                                       │  │
│ │   CommandDef("exit", "Exit agent", "Exit",                         │  │
│ │              aliases=("quit", "q")),                               │  │
│ │   ...                                                              │  │
│ │ ]                                                                  │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│ Processing Flow:                                                         │
│   1. Parse "/model anthropic/claude-opus-4.6"                           │
│   2. resolve_command("model") → canonical name                          │
│   3. Dispatch to HermesCLI.process_command()                            │
│   4. Gateway: dispatch to gateway/run.py handlers                       │
│   5. Execute command logic                                              │
│   6. Save config (if persistent)                                        │
│   7. Return result                                                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 图例 (Legend)

```
┌─────────────┐
│   Process   │  处理步骤
└─────────────┘

┌─────────────┐
│  Decision   │  决策点 (diamond in flowcharts)
└─────────────┘

  ──────►      数据流/控制流

┌─────────────┐
│   Data      │  数据存储 (database, file)
└─────────────┘

┌═════════════┐
│  Component  │  主要组件 (double border)
└═════════════┘
```

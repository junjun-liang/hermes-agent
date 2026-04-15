# `tools/registry.py` 业务逻辑详解

> 文件路径：`tools/registry.py` | 代码行数：335 行 | 核心职责：工具注册中心

---

## 目录

1. [文件定位与核心职责](#1-文件定位与核心职责)
2. [数据模型详解](#2-数据模型详解)
3. [ToolRegistry 类方法详解](#3-toolregistry-类方法详解)
4. [辅助函数详解](#4-辅助函数详解)
5. [核心业务流程图](#5-核心业务流程图)
6. [依赖关系与引用分析](#6-依赖关系与引用分析)
7. [设计模式与架构决策](#7-设计模式与架构决策)

---

## 1. 文件定位与核心职责

### 1.1 在项目中的位置

`tools/registry.py` 是整个工具子系统的**基石模块**，位于依赖链的最底层，不依赖任何其他项目模块：

```
tools/registry.py  （零项目依赖）
       ↑
tools/*.py  （每个工具文件在 import 时调用 registry.register()）
       ↑
model_tools.py  （编排层：触发注册、获取 schema、分发调用）
       ↑
run_agent.py, cli.py, batch_runner.py  （上层消费者）
```

### 1.2 三大核心职责

| 职责 | 对应方法 | 说明 |
|------|----------|------|
| **注册** | `register()`, `deregister()` | 收集所有工具的 schema、handler、可用性检查函数 |
| **查询** | `get_definitions()`, `get_schema()`, `get_emoji()` 等 | 为 LLM 和 UI 提供工具元数据 |
| **分发** | `dispatch()` | 将 LLM 的工具调用路由到对应的 handler 函数 |

### 1.3 设计哲学

- **声明式注册**：每个工具文件在模块级（import 时）自注册，无需中央配置文件
- **单例模式**：模块级 `registry = ToolRegistry()` 确保全局唯一实例
- **零依赖**：不 import 任何项目模块，避免循环依赖
- **统一错误格式**：所有工具 handler 返回 JSON 字符串，`dispatch()` 捕获异常并统一包装

---

## 2. 数据模型详解

### 2.1 ToolEntry 数据类

```python
class ToolEntry:
    __slots__ = (
        "name", "toolset", "schema", "handler", "check_fn",
        "requires_env", "is_async", "description", "emoji",
        "max_result_size_chars",
    )
```

每个字段的业务含义：

| 字段 | 类型 | 业务含义 | 示例 |
|------|------|----------|------|
| `name` | `str` | 工具唯一标识符，LLM 调用时使用 | `"terminal"`, `"read_file"` |
| `toolset` | `str` | 工具所属工具集，控制批量启用/禁用 | `"core"`, `"browser"`, `"mcp_<name>"` |
| `schema` | `dict` | OpenAI Function Calling 格式的 JSON Schema | `{"name": "terminal", "description": "...", "parameters": {...}}` |
| `handler` | `Callable` | 工具执行函数，接收 `args: dict` + `**kwargs` | `lambda args, **kw: terminal_tool(...)` |
| `check_fn` | `Callable \| None` | 可用性检查函数，返回 `bool` | `check_terminal_requirements` |
| `requires_env` | `list[str]` | 所需环境变量列表（文档用途） | `["ANTHROPIC_API_KEY"]` |
| `is_async` | `bool` | handler 是否为异步函数 | `True`（如 `vision_analyze`） |
| `description` | `str` | 工具描述（从 schema 提取或手动指定） | `"Execute terminal commands"` |
| `emoji` | `str` | CLI 显示用的工具图标 | `"🖥️"`, `"📁"` |
| `max_result_size_chars` | `int \| float \| None` | 单次调用结果大小上限（字符数） | `50000` |

**`__slots__` 的意义**：使用 `__slots__` 而非 `__dict__`，减少内存占用（项目注册 40+ 工具，每个工具一个 ToolEntry 实例）。

### 2.2 ToolRegistry 类内部状态

```python
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}           # 工具名 → ToolEntry
        self._toolset_checks: Dict[str, Callable] = {}    # 工具集名 → check_fn
```

| 内部状态 | 类型 | 说明 |
|----------|------|------|
| `_tools` | `Dict[str, ToolEntry]` | 核心存储，key 为工具名，value 为完整元数据 |
| `_toolset_checks` | `Dict[str, Callable]` | 每个工具集的可用性检查函数（仅保留第一个注册的） |

**`_toolset_checks` 的去重逻辑**：同一 toolset 下的多个工具共享同一个 `check_fn`，只在首次注册时记录：

```python
if check_fn and toolset not in self._toolset_checks:
    self._toolset_checks[toolset] = check_fn
```

---

## 3. ToolRegistry 类方法详解

### 3.1 register() — 工具注册

```python
def register(self, name, toolset, schema, handler, check_fn=None,
             requires_env=None, is_async=False, description="", emoji="",
             max_result_size_chars=None):
```

**业务流程**：

```
register(name, toolset, schema, handler, ...)
    │
    ├─ 检查是否已存在同名工具（不同 toolset）
    │   └─ 若存在 → 打印 warning（允许覆盖，用于 MCP 热更新）
    │
    ├─ 创建 ToolEntry 实例
    │   └─ description 默认从 schema["description"] 提取
    │
    └─ 注册 toolset check_fn（仅首次）
        └─ 同一 toolset 的后续工具不再重复注册 check_fn
```

**同名覆盖策略**：当新注册的工具与已有工具同名但属于不同 toolset 时，打印 warning 并覆盖。这主要用于 MCP 动态发现场景——MCP 服务器工具更新时先 deregister 再 register。

### 3.2 deregister() — 工具注销

```python
def deregister(self, name: str) -> None:
```

**业务流程**：

```
deregister(name)
    │
    ├─ 从 _tools 中移除 ToolEntry
    │   └─ 若不存在 → 静默返回
    │
    └─ 检查是否为该 toolset 的最后一个工具
        └─ 若是 → 同时移除 _toolset_checks 中的 check_fn
```

**使用场景**：仅被 `mcp_tool.py` 调用，当 MCP 服务器发送 `notifications/tools/list_changed` 时，先注销旧工具再重新注册新工具。

### 3.3 get_definitions() — 获取工具 Schema

```python
def get_definitions(self, tool_names: Set[str], quiet: bool = False) -> List[dict]:
```

**业务流程**：

```
get_definitions(tool_names, quiet)
    │
    ├─ 遍历请求的工具名（排序保证确定性）
    │
    ├─ 查找 ToolEntry
    │   └─ 不存在 → 跳过
    │
    ├─ 执行 check_fn 可用性检查
    │   ├─ check_fn 返回 False → 跳过（工具不可用）
    │   ├─ check_fn 抛异常 → 标记为 False，跳过
    │   └─ check_fn 返回 True → 继续
    │
    ├─ 构建输出 schema
    │   └─ {**entry.schema, "name": entry.name}  确保 name 字段存在
    │
    └─ 包装为 OpenAI 格式
        └─ {"type": "function", "function": schema_with_name}
```

**check_fn 缓存机制**：同一 `check_fn` 函数对象在同一轮 `get_definitions()` 调用中只执行一次，结果缓存在 `check_results` 字典中。这避免了同一 toolset 下的多个工具重复执行相同的检查。

**关键设计**：`check_fn` 过滤确保 LLM 只能看到**当前可用**的工具 schema。例如，未配置 `FIRECRAWL_API_KEY` 时，`web_extract` 不会出现在 LLM 的工具列表中。

### 3.4 dispatch() — 工具调用分发

```python
def dispatch(self, name: str, args: dict, **kwargs) -> str:
```

**业务流程**：

```
dispatch(name, args, **kwargs)
    │
    ├─ 查找 ToolEntry
    │   └─ 不存在 → 返回 {"error": "Unknown tool: {name}"}
    │
    ├─ 判断 handler 类型
    │   ├─ is_async=True → 通过 _run_async() 桥接执行
    │   └─ is_async=False → 直接调用 handler(args, **kwargs)
    │
    └─ 异常捕获
        └─ 任何异常 → 返回 {"error": "Tool execution failed: {Type}: {msg}"}
```

**异步桥接**：异步 handler（如 `vision_analyze`）通过 `model_tools._run_async()` 桥接到同步调用链。这确保了 `run_agent.py` 的同步主循环可以透明地调用异步工具。

**统一错误格式**：无论 handler 内部抛出什么异常，`dispatch()` 都会捕获并返回 `{"error": "..."}` JSON 字符串，确保上层代码无需处理异构的错误格式。

### 3.5 查询辅助方法

| 方法 | 返回类型 | 业务用途 |
|------|----------|----------|
| `get_max_result_size(name, default)` | `int \| float` | 获取工具结果大小限制，用于输出截断 |
| `get_all_tool_names()` | `List[str]` | 获取所有已注册工具名（排序），供 UI 显示 |
| `get_schema(name)` | `Optional[dict]` | 获取工具原始 schema（不过滤 check_fn），供参数类型转换 |
| `get_toolset_for_tool(name)` | `Optional[str]` | 查询工具所属工具集 |
| `get_emoji(name, default)` | `str` | 获取工具 emoji，供 CLI spinner 显示 |
| `get_tool_to_toolset_map()` | `Dict[str, str]` | 全量工具名→工具集映射，供 batch_runner 使用 |
| `is_toolset_available(toolset)` | `bool` | 检查工具集可用性（安全处理异常） |
| `check_toolset_requirements()` | `Dict[str, bool]` | 全量工具集可用性报告 |
| `get_available_toolsets()` | `Dict[str, dict]` | 工具集元数据（含工具列表、需求、可用性），供 UI 显示 |
| `get_toolset_requirements()` | `Dict[str, dict]` | 向后兼容的工具集需求字典 |
| `check_tool_availability(quiet)` | `tuple` | 返回 `(available_list, unavailable_info)` |

**`get_schema()` vs `get_definitions()` 的区别**：

| 维度 | `get_schema()` | `get_definitions()` |
|------|----------------|---------------------|
| 过滤 | 不过滤 check_fn | 过滤不可用工具 |
| 格式 | 原始 schema dict | OpenAI Function Calling 格式 |
| 用途 | 参数类型转换、token 估算 | 构建 LLM 请求的 tools 参数 |

---

## 4. 辅助函数详解

### 4.1 tool_error() — 错误结果构造器

```python
def tool_error(message, **extra) -> str:
    result = {"error": str(message)}
    if extra:
        result.update(extra)
    return json.dumps(result, ensure_ascii=False)
```

**用法示例**：

```python
# 基本错误
return tool_error("file not found")
# → '{"error": "file not found"}'

# 附加字段
return tool_error("bad input", success=False)
# → '{"error": "bad input", "success": false}'

# 附加上下文
return tool_error("API call failed", status_code=429, retry_after=60)
# → '{"error": "API call failed", "status_code": 429, "retry_after": 60}'
```

**使用统计**：项目中有 **21 个文件**、**约 90 处调用**使用 `tool_error()`。

### 4.2 tool_result() — 成功结果构造器

```python
def tool_result(data=None, **kwargs) -> str:
    if data is not None:
        return json.dumps(data, ensure_ascii=False)
    return json.dumps(kwargs, ensure_ascii=False)
```

**用法示例**：

```python
# 关键字参数
return tool_result(success=True, count=42)
# → '{"success": true, "count": 42}'

# 字典参数
return tool_result({"key": "value"})
# → '{"key": "value"}'
```

**当前状态**：`tool_result()` 已定义但**项目中无任何文件实际导入和调用**。所有工具文件普遍直接使用 `json.dumps()` 构造成功结果。这是一个预留的便利函数，未来可推广使用以统一风格。

---

## 5. 核心业务流程图

### 5.1 工具注册流程（启动时）

```
┌─────────────────────────────────────────────────────────────┐
│                    应用启动                                   │
│  (run_agent.py / cli.py / batch_runner.py)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  model_tools._discover_tools()                              │
│  遍历工具模块列表，逐个 importlib.import_module()             │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │terminal.py │ │ file_tools │ │ browser.py │  ... 40+ 工具文件
     │  import    │ │   import   │ │   import   │
     └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
           │              │              │
           ▼              ▼              ▼
     ┌──────────────────────────────────────────────┐
     │  每个工具文件模块级代码执行：                    │
     │                                              │
     │  registry.register(                          │
     │      name="terminal",                        │
     │      toolset="core",                         │
     │      schema={...},                           │
     │      handler=lambda args, **kw: ...,         │
     │      check_fn=check_terminal_requirements,   │
     │      requires_env=[],                        │
     │      emoji="🖥️",                             │
     │  )                                           │
     └──────────────────┬───────────────────────────┘
                        │
                        ▼
     ┌──────────────────────────────────────────────┐
     │  ToolRegistry._tools 字典填充完成             │
     │  {                                           │
     │    "terminal": ToolEntry(...),               │
     │    "read_file": ToolEntry(...),              │
     │    "write_file": ToolEntry(...),             │
     │    ... 40+ entries                           │
     │  }                                           │
     │                                              │
     │  ToolRegistry._toolset_checks 字典填充完成    │
     │  {                                           │
     │    "core": check_fn_A,                       │
     │    "browser": check_fn_B,                    │
     │    "web": check_fn_C,                        │
     │    ...                                       │
     │  }                                           │
     └──────────────────────────────────────────────┘
```

### 5.2 工具 Schema 获取流程（每次 LLM 调用前）

```
┌─────────────────────────────────────────────────────────────┐
│  AIAgent.run_conversation() 准备调用 LLM                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  model_tools.get_tool_definitions(                           │
│      enabled_toolsets, disabled_toolsets, quiet_mode         │
│  )                                                           │
│                                                              │
│  1. 根据 toolset 配置计算 tools_to_include 集合              │
│  2. 调用 registry.get_definitions(tools_to_include)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  registry.get_definitions(tool_names)                        │
│                                                              │
│  for name in sorted(tool_names):                             │
│    │                                                         │
│    ├─ 查找 ToolEntry                                         │
│    │   └─ 不存在 → 跳过                                      │
│    │                                                         │
│    ├─ 执行 check_fn（带缓存）                                │
│    │   ├─ True  → 包含此工具                                 │
│    │   ├─ False → 跳过（API Key 缺失等）                     │
│    │   └─ 异常  → 标记 False，跳过                           │
│    │                                                         │
│    └─ 构建 OpenAI 格式 schema                                │
│        {"type": "function", "function": {...}}               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  返回 [schema1, schema2, ...]  →  传入 LLM API 的 tools 参数 │
│                                                              │
│  LLM 只能看到 check_fn=True 的工具                           │
│  （例如：未配置 ANTHROPIC_API_KEY 时看不到 vision_analyze）   │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 工具调用分发流程（LLM 返回 tool_call 后）

```
┌─────────────────────────────────────────────────────────────┐
│  LLM 返回 tool_calls: [{name: "terminal", args: {command:   │
│  "ls -la"}}]                                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  model_tools.handle_function_call(function_name,             │
│      function_args, task_id, user_task)                      │
│                                                              │
│  1. 参数类型强制转换 (coerce_tool_args)                       │
│     └─ 使用 registry.get_schema() 获取参数类型定义            │
│                                                              │
│  2. 调用 registry.dispatch(name, args, **kwargs)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  registry.dispatch("terminal", {"command": "ls -la"},        │
│                    task_id="xxx")                            │
│                                                              │
│  1. 查找 ToolEntry                                           │
│     └─ _tools["terminal"] → ToolEntry(handler=...)          │
│                                                              │
│  2. 判断 is_async                                            │
│     ├─ True  → _run_async(handler(args, **kwargs))          │
│     └─ False → handler(args, **kwargs)                      │
│                                                              │
│  3. 异常捕获                                                 │
│     └─ 任何异常 → {"error": "Tool execution failed: ..."}    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  terminal_tool(command="ls -la", task_id="xxx")              │
│  → 执行命令 → 返回 JSON 字符串                               │
│  '{"output": "total 32\\ndrwxr-xr-x ...", "exit_code": 0}' │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  结果返回给 LLM 作为 tool role message                       │
│  {"role": "tool", "tool_call_id": "...", "content": result} │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 MCP 动态工具发现流程

```
┌─────────────────────────────────────────────────────────────┐
│  MCP 服务器发送 notifications/tools/list_changed             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  mcp_tool.py 收到通知                                        │
│                                                              │
│  1. 遍历该服务器的旧工具列表                                  │
│     for prefixed_name in old_tool_names:                     │
│         registry.deregister(prefixed_name)  ← 注销旧工具    │
│                                                              │
│  2. 请求服务器的新工具列表                                    │
│     new_tools = await session.list_tools()                   │
│                                                              │
│  3. 注册新工具                                               │
│     for tool in new_tools:                                   │
│         registry.register(                                   │
│             name=f"mcp__{server}__{tool.name}",              │
│             toolset=f"mcp_{server}",                         │
│             schema=tool.schema,                              │
│             handler=lambda args, **kw: ...,                  │
│             check_fn=None,  ← MCP 工具不做 check_fn 过滤     │
│             is_async=True,                                   │
│         )                                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  registry._tools 更新完成                                    │
│  - 旧 MCP 工具已移除                                         │
│  - 新 MCP 工具已添加                                         │
│  - 下次 get_definitions() 调用将反映最新状态                  │
└─────────────────────────────────────────────────────────────┘
```

### 5.5 check_fn 可用性检查流程

```
┌─────────────────────────────────────────────────────────────┐
│  registry.get_definitions() 遍历工具时                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  entry.check_fn 存在？  │
              └─────┬──────────┬───────┘
                    │          │
               No   │          │  Yes
                    │          │
                    ▼          ▼
              ┌─────────┐  ┌──────────────────────┐
              │ 直接包含 │  │ check_results 缓存？  │
              │ 此工具   │  └─────┬──────────┬─────┘
              └─────────┘        │          │
                           命中  │          │  未命中
                                │          │
                                ▼          ▼
                          ┌─────────┐  ┌──────────────────┐
                          │ 使用缓存 │  │ 执行 check_fn()   │
                          │ 结果     │  └─────┬──────┬──────┘
                          └────┬────┘        │      │
                               │        True │      │ False/异常
                               ▼             │      │
                          ┌─────────┐        │      ▼
                          │ 包含工具 │        │  ┌──────────┐
                          └─────────┘        │  │ 跳过工具 │
                                             │  └──────────┘
                                             ▼
                                        ┌─────────┐
                                        │ 包含工具 │
                                        └─────────┘

示例 check_fn 行为：
┌──────────────────────────────────────────────────────────┐
│ 工具           │ check_fn                       │ 结果    │
├────────────────┼────────────────────────────────┼─────────┤
│ terminal       │ Docker/Modal/SSH 可用性检查     │ True/False│
│ execute_code   │ 非 Windows（需要 UDS）          │ True/False│
│ web_search     │ PARALLEL_API_KEY 是否存在       │ True/False│
│ browser_navigate│ BrowserBase API Key 是否存在  │ True/False│
│ vision_analyze │ 辅助 LLM 客户端是否可用         │ True/False│
│ mcp__*         │ None（不做过滤）                │ 始终包含 │
└──────────────────────────────────────────────────────────┘
```

---

## 6. 依赖关系与引用分析

### 6.1 被引用统计

| 引入方式 | 文件数 | 说明 |
|----------|--------|------|
| `from tools.registry import registry` | 6 | 导入单例，调用注册/查询/分发方法 |
| `from tools.registry import registry, tool_error` | 19 | 同时导入单例和错误构造器 |
| `from tools.registry import tool_error` | 11 | 仅导入错误构造器（插件、辅助模块） |
| `from tools.registry import ToolRegistry` | 3 | 导入类（仅测试文件） |
| `from tools.registry import tool_result` | 0 | **无人使用** |

### 6.2 核心调用者：model_tools.py

`model_tools.py` 是 registry 的**唯一运行时分发入口**和**主要查询消费者**：

| model_tools.py 函数 | 调用的 registry 方法 | 业务含义 |
|---------------------|---------------------|----------|
| `_discover_tools()` | 间接触发 `register()` | 导入工具模块，触发自注册 |
| `get_tool_definitions()` | `get_definitions()` | 获取 LLM 可见的工具 schema |
| `handle_function_call()` | `dispatch()` | 将 LLM 工具调用路由到 handler |
| `coerce_tool_args()` | `get_schema()` | 获取参数类型定义，做类型转换 |
| 向后兼容常量 | `get_tool_to_toolset_map()`, `get_toolset_requirements()` | 为上层提供映射字典 |
| 向后兼容包装 | `get_all_tool_names()`, `check_tool_availability()` 等 | 代理 registry 方法 |

### 6.3 直接访问内部属性的文件

以下文件绕过公共 API，直接访问 `registry._tools`：

| 文件 | 访问方式 | 原因 |
|------|----------|------|
| `toolsets.py` | `registry._tools` | 遍历工具列表解析 toolset 配置 |
| `hermes_cli/plugins.py` | `registry._tools` | 插件系统查找工具条目 |

**潜在问题**：直接访问 `_tools` 绕过了封装，如果 `ToolRegistry` 内部实现变更（如改用数据库存储），这些文件需要同步修改。

### 6.4 register() 调用者汇总

| 来源 | 注册方式 | 时机 |
|------|----------|------|
| 21 个内置工具文件 | 模块级 `registry.register()` | import 时（启动阶段） |
| `tools/mcp_tool.py` | 运行时 `registry.register()` | MCP 服务器连接/工具变更时 |
| `hermes_cli/plugins.py` | 运行时 `registry.register()` | 插件发现时 |

### 6.5 deregister() 调用者

| 来源 | 场景 |
|------|------|
| `tools/mcp_tool.py` | MCP 服务器发送 `notifications/tools/list_changed` 时，注销旧工具 |

---

## 7. 设计模式与架构决策

### 7.1 单例模式

```python
registry = ToolRegistry()  # 模块级单例
```

**选择原因**：
- 工具注册是全局状态，需要唯一入口
- 避免多个 registry 实例导致注册信息分散
- 模块级实例在 Python 中天然线程安全（GIL 保护模块加载）

### 7.2 声明式自注册模式

每个工具文件在模块级调用 `registry.register()`，而非由中央配置文件统一注册：

```python
# tools/terminal_tool.py 模块底部
registry.register(
    name="terminal",
    toolset="core",
    schema={...},
    handler=lambda args, **kw: terminal_tool(...),
    ...
)
```

**优势**：
- 新增工具只需创建文件 + 在 `_discover_tools()` 列表中添加一行
- 工具的 schema、handler、check_fn 集中在同一文件，便于维护
- 避免中央配置文件膨胀

### 7.3 策略模式（check_fn）

`check_fn` 实现了策略模式——每个工具集定义自己的可用性检查策略：

```python
# Web 工具：检查 API Key
check_fn=lambda: bool(os.getenv("PARALLEL_API_KEY"))

# 终端工具：检查后端可用性
check_fn=check_terminal_requirements

# MCP 工具：不做检查（始终可用）
check_fn=None
```

`get_definitions()` 统一调用 `check_fn()` 接口，无需关心具体检查逻辑。

### 7.4 异步桥接模式

`dispatch()` 内部处理同步/异步 handler 的差异：

```python
if entry.is_async:
    from model_tools import _run_async
    return _run_async(entry.handler(args, **kwargs))
return entry.handler(args, **kwargs)
```

上层代码（`run_agent.py` 的同步主循环）无需关心 handler 是同步还是异步，统一以同步方式调用 `dispatch()`。

### 7.5 防御性编程

| 防御措施 | 位置 | 说明 |
|----------|------|------|
| check_fn 异常捕获 | `get_definitions()` L130-133 | check_fn 抛异常时标记为 False，不崩溃 |
| dispatch 异常捕获 | `dispatch()` L164-166 | handler 抛异常时返回统一错误 JSON |
| 同名覆盖 warning | `register()` L73-79 | 允许覆盖但打印警告 |
| schema name 兜底 | `get_definitions()` L141 | 确保 schema 始终有 name 字段 |
| is_toolset_available 异常安全 | `is_toolset_available()` L218-222 | check 抛异常时返回 False |
| deregister 静默处理 | `deregister()` L103-104 | 工具不存在时静默返回 |

### 7.6 待改进点

| 问题 | 说明 | 建议 |
|------|------|------|
| `tool_result()` 无人使用 | 已定义但项目中无任何调用 | 推广使用或标记为废弃 |
| `_tools` 被外部直接访问 | `toolsets.py` 和 `plugins.py` 绕过公共 API | 添加 `get_entries()` 公共方法 |
| `redact_key()` 重复定义 | 多处文件各自实现密钥遮蔽函数 | 统一到 `redact.py` |
| check_fn 缓存仅限单次调用 | `get_definitions()` 的 `check_results` 是局部变量 | 考虑实例级缓存 + TTL |
| 无工具版本管理 | register 时不记录版本号 | 为 MCP 动态工具添加版本字段 |

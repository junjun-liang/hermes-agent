# Hermes-Agent 软件架构全面分析

> 分析日期：2026-04-14 | 项目版本：基于当前代码库快照 | 代码行数：约 30 万行

***

## 目录

1. [系统架构总览](#1-系统架构总览)
2. [核心组件详解](#2-核心组件详解)
3. [模块依赖关系](#3-模块依赖关系)
4. [设计模式应用](#4-设计模式应用)
5. [核心业务流程](#5-核心业务流程)
6. [数据流分析](#6-数据流分析)
7. [配置与状态管理](#7-配置与状态管理)
8. [扩展机制](#8-扩展机制)
9. [架构决策与权衡](#9-架构决策与权衡)

***

## 1. 系统架构总览

### 1.1 架构层次

Hermes-Agent 采用**分层架构 + 插件化设计**，整体分为 5 个层次：

```
┌─────────────────────────────────────────────────────────────────┐
│                        接入层（Entry Points）                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  CLI (cli.py)│  │Gateway (gw/) │  │   ACP (acp/) │          │
│  │  交互式终端   │  │  消息平台适配 │  │  IDE 集成     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      编排层（Orchestration）                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AIAgent (run_agent.py) — 对话循环、迭代控制、上下文管理    │   │
│  │  model_tools.py — 工具发现、Schema 生成、调用分发            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       工具层（Tool System）                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  tools/registry.py — 工具注册中心（Schema + Handler）      │   │
│  │  tools/*.py — 40+ 个工具实现（terminal, file, browser...）  │   │
│  │  tools/environments/ — 执行环境（local, docker, ssh...）   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      支撑层（Infrastructure）                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │hermes_state.py│  │  config.py   │  │  logging.py  │          │
│  │ SQLite 会话存储│  │ 配置与.env   │  │ 日志与脱敏   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  auth.py     │  │  approval.py │  │  redact.py   │          │
│  │ OAuth 认证    │  │ 审批与危险检测│  │ 敏感信息脱敏 │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      扩展层（Extensions）                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Skills     │  │   Plugins    │  │    MCP       │          │
│  │  用户自定义技能 │  │  动态插件系统 │  │  模型上下文协议│         │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 架构特点

| 特点            | 说明                            | 优势                              |
| ------------- | ----------------------------- | ------------------------------- |
| **声明式工具注册**   | 工具文件在 import 时自注册到 `registry` | 新增工具只需创建文件 + 添加到发现列表，无需修改中央配置   |
| **编排层与接入层分离** | `AIAgent` 独立于 CLI/Gateway/ACP | 同一对话核心可服务多种接入方式                 |
| **工具与执行环境解耦** | `tools/environments/` 提供多种后端  | 本地/Docker/SSH/Modal/Daytona 可切换 |
| **纵深防御安全**    | 7 层独立安全检查（认证、审批、沙箱、脱敏等）       | 某一层被绕过，下一层仍能提供保护                |
| **插件化扩展**     | Skills/Plugins/MCP 三种扩展机制     | 用户可自定义功能，无需修改核心代码               |

***

## 2. 核心组件详解

### 2.1 接入层组件

#### 2.1.1 CLI（`cli.py` + `hermes_cli/main.py`）

**职责**：交互式命令行界面，提供 Rich 终端 UI 和 prompt\_toolkit 输入。

**核心类**：

```python
class HermesCLI:
    def __init__(self):
        self.agent = None  # AIAgent 实例
        self.config = load_cli_config()
        self.session_db = SessionDB()
    
    def run(self):
        # 1. 显示 banner
        # 2. 加载配置和工具
        # 3. 初始化 AIAgent
        # 4. 进入主循环：input → agent.chat() → output
```

**关键流程**：

```
用户输入 → process_command() → 
  ├─ 内置命令（/model, /tools, /memory...）→ 直接处理
  └─ 普通消息 → agent.chat(message) → 显示响应
```

#### 2.1.2 Gateway（`gateway/run.py` + `gateway/platforms/*`）

**职责**：消息平台适配层，支持 Telegram、Discord、Slack、WhatsApp 等 15+ 平台。

**核心架构**：

```python
async def run_gateway():
    # 1. 加载平台配置
    # 2. 初始化平台适配器（TelegramBot, DiscordClient...）
    # 3. 启动消息监听
    # 4. 消息分发：platform_message → AIAgent → platform_response
```

**平台适配器模式**：

```
┌────────────────────────────────────────────┐
│          BaseMessagePlatform               │  ← 抽象基类
│  - connect(), disconnect(), send_message() │
└─────────────────┬──────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐   ┌────────┐   ┌────────┐
│Telegram│   │Discord │   │ Slack  │  ... 15+ 平台
└────────┘   └────────┘   └────────┘
```

#### 2.1.3 ACP（`acp_adapter/`）

**职责**：Agent Communication Protocol，为 VS Code、Zed、JetBrains 等 IDE 提供集成。

**核心机制**：

- **stdio 传输**：通过标准输入输出与 IDE 通信
- **权限桥接**：将 IDE 的权限请求映射到 Hermes 审批回调
- **MCP 服务器注册**：IDE 提供的 MCP 服务器动态注册到工具系统

***

### 2.2 编排层组件

#### 2.2.1 AIAgent（`run_agent.py`）

**职责**：对话循环核心，管理 LLM 交互、工具调用、上下文压缩。

**核心方法**：

```python
class AIAgent:
    def chat(self, message: str) -> str:
        """简单接口 — 返回最终响应字符串"""
    
    def run_conversation(self, user_message, system_message, 
                         conversation_history, task_id) -> dict:
        """完整接口 — 返回 dict（final_response + messages）"""
```

**对话循环伪代码**：

```python
def run_conversation(self, user_message, ...):
    messages = build_initial_messages(user_message, system_message)
    
    while api_call_count < max_iterations and budget.remaining > 0:
        # 1. 调用 LLM
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tool_schemas  # 从 registry.get_definitions() 获取
        )
        
        # 2. 处理响应
        if response.tool_calls:
            # 工具调用
            for tool_call in response.tool_calls:
                result = handle_function_call(
                    tool_call.name, 
                    tool_call.args, 
                    task_id=self.task_id
                )
                messages.append(tool_result_message(result))
            api_call_count += 1
        else:
            # 最终响应
            return response.content
    
    raise MaxIterationsReached()
```

#### 2.2.2 model\_tools.py（工具编排层）

**职责**：工具发现、Schema 生成、参数类型转换、调用分发。

**核心函数**：

```python
def _discover_tools():
    """导入所有工具模块，触发 registry.register()"""
    tool_modules = [
        "tools.terminal_tool",
        "tools.file_tools",
        "tools.browser_tool",
        # ... 40+ 模块
    ]
    for module_name in tool_modules:
        importlib.import_module(module_name)

def get_tool_definitions(enabled_toolsets, disabled_toolsets, quiet=False):
    """根据 toolset 配置过滤，返回 OpenAI 格式的 schema 列表"""
    tools_to_include = compute_tool_set(...)
    return registry.get_definitions(tools_to_include, quiet=quiet)

def handle_function_call(function_name, function_args, task_id, user_task):
    """工具调用分发入口"""
    # 1. 参数类型强制转换（coerce_tool_args）
    # 2. 调用 registry.dispatch()
    return registry.dispatch(function_name, function_args, task_id=task_id)
```

***

### 2.3 工具层组件

#### 2.3.1 tools/registry.py（工具注册中心）

**职责**：集中管理所有工具的 Schema、Handler、可用性检查。

**核心数据结构**：

```python
class ToolEntry:
    __slots__ = (
        "name", "toolset", "schema", "handler", "check_fn",
        "requires_env", "is_async", "description", "emoji",
        "max_result_size_chars",
    )

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}
        self._toolset_checks: Dict[str, Callable] = {}
```

**关键方法**：

| 方法                  | 职责                        | 调用者                |
| ------------------- | ------------------------- | ------------------ |
| `register()`        | 注册工具（import 时调用）          | tools/\*.py        |
| `get_definitions()` | 获取通过 check\_fn 过滤的 schema | model\_tools.py    |
| `dispatch()`        | 调用 handler 并处理异常          | model\_tools.py    |
| `deregister()`      | 注销工具（MCP 热更新）             | tools/mcp\_tool.py |

#### 2.3.2 工具分类

| 类别         | 工具示例                                                    | 数量 |
| ---------- | ------------------------------------------------------- | -- |
| **核心工具**   | terminal, read\_file, write\_file, search\_files, patch | 5  |
| **Web 工具** | web\_search, web\_extract                               | 2  |
| **浏览器工具**  | browser\_navigate, browser\_snapshot, browser\_click... | 10 |
| **视觉工具**   | vision\_analyze, text\_to\_speech, image\_generate      | 3  |
| **代码工具**   | execute\_code（沙箱执行）                                     | 1  |
| **委托工具**   | delegate\_task（子代理）                                     | 1  |
| **记忆工具**   | memory（读写 MEMORY.md）                                    | 1  |
| **待办工具**   | todo（任务管理）                                              | 1  |
| **消息工具**   | send\_message（多平台发送）                                    | 1  |
| **流程工具**   | cronjob, process（后台进程管理）                                | 2  |
| **MCP 工具** | mcp\_call, mcp\_list\_servers...                        | 4  |
| **技能工具**   | skills\_list, skill\_view, skill\_manage                | 3  |
| **RL 工具**  | rl\_list\_environments, rl\_start\_training...          | 10 |
| **动态工具**   | MCP 服务器提供的工具（运行时注册）                                     | 动态 |

***

### 2.4 支撑层组件

#### 2.4.1 hermes\_state.py（SQLite 会话存储）

**职责**：持久化会话数据，支持 FTS5 全文搜索。

**核心表结构**：

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT,
    user_id TEXT,
    model TEXT,
    started_at REAL,
    ended_at REAL,
    title TEXT,
    ...
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,  -- system/user/assistant/tool
    content TEXT,
    timestamp REAL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- FTS5 虚拟表（全文搜索）
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content='messages',
    content_rowid='id'
);
```

**关键方法**：

```python
class SessionDB:
    def create_session(self, session_id, source, user_id, model, ...)
    def append_message(self, session_id, role, content, ...)
    def get_messages(self, session_id, limit=100)
    def search_messages(self, query, limit=20)  -- FTS5 搜索
    def prune_sessions(self, older_than_days=90)
```

#### 2.4.2 hermes\_cli/config.py（配置管理）

**职责**：加载 config.yaml、管理.env 文件、环境变量验证。

**配置加载流程**：

```
1. 读取 ~/.hermes/config.yaml
   ↓
2. 合并 DEFAULT_CONFIG（硬编码默认值）
   ↓
3. 应用 profile 覆盖（HERMES_HOME 环境变量）
   ↓
4. 加载 ~/.hermes/.env 到 os.environ
   ↓
5. 返回合并后的配置字典
```

**配置版本迁移**：

```python
_config_version = 5  # 当前版本

def migrate_config(config):
    if config.get("_config_version", 0) < 5:
        # 逐版本应用迁移逻辑
        if version < 2:
            add_new_fields()
        if version < 3:
            rename_old_keys()
        # ...
        config["_config_version"] = _config_version
```

#### 2.4.3 hermes\_cli/auth.py（多提供者认证）

**职责**：管理 OAuth 流程、API Key 解析、Token 刷新。

**支持的认证类型**：

| 类型                  | 提供者                       | 流程                                     |
| ------------------- | ------------------------- | -------------------------------------- |
| `oauth_device_code` | Nous Portal               | 设备码流 → 用户授权 → Access Token → Agent Key |
| `oauth_external`    | OpenAI Codex, Qwen        | 读取外部 OAuth 凭据 → 自动刷新                   |
| `api_key`           | Anthropic, Gemini, GitHub | 环境变量优先级链查找                             |
| `external_process`  | Copilot ACP               | 子进程认证                                  |

**Token 刷新状态机**：

```
┌─────────────┐     即将过期      ┌─────────────┐
│   Valid     │ ────────────────> │  Refreshing │
│  (有效)     │                   │  (刷新中)   │
└─────────────┘                   └──────┬──────┘
       ▲                                 │
       │             ┌───────────────────┼───────────────────┐
       │             │                   │                   │
       │        成功刷新             刷新失败            refresh_token 过期
       │             │                   │                   │
       │             ▼                   ▼                   ▼
       │      ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
       └──────│   Valid     │     │   Retry     │     │  Re-auth    │
              │ (新 Token)  │     │  (重试)     │     │ (重新认证)  │
              └─────────────┘     └─────────────┘     └─────────────┘
```

#### 2.4.4 tools/approval.py（审批与危险命令检测）

**职责**：检测危险命令、执行审批流程、管理白名单。

**三层检测机制**：

```
1. Tirith 安全扫描（外部二进制）
   └─ 检测同形字 URL、管道到解释器、终端注入等
   
2. DANGEROUS_PATTERNS 正则（30+ 模式）
   └─ 检测 rm -rf、chmod 777、DROP TABLE、curl|sh 等
   
3. 敏感路径写入检测
   └─ 检测 ~/.ssh/、~/.hermes/.env、/etc/ 等
```

**审批模式**：

```python
APPROVAL_MODES = {
    "manual": "每次匹配都弹出交互式审批",
    "smart": "辅助 LLM 评估风险，自动批准低风险命令",
    "off": "跳过所有审批（--yolo 模式）"
}
```

**审批状态持久化**：

```
once（仅本次） → 无存储
session（会话级） → _session_approved 字典
always（永久） → config.yaml 的 command_allowlist
```

#### 2.4.5 agent/redact.py（敏感信息脱敏）

**职责**：日志和工具输出的敏感信息自动脱敏。

**8 层脱敏规则**：

```python
def redact_sensitive_text(text):
    # 1. 已知 API Key 前缀（30+ 种模式）
    # 2. ENV 赋值（OPENAI_API_KEY=value）
    # 3. JSON 字段（"apiKey": "value"）
    # 4. Authorization 头（Bearer token）
    # 5. Telegram Bot Token
    # 6. 私钥块（-----BEGIN RSA PRIVATE KEY-----）
    # 7. 数据库连接串（postgres://user:pass@host）
    # 8. E.164 电话号码（+8613800138000）
```

**RedactingFormatter**：

```python
class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_sensitive_text(original)
```

所有日志 Handler 都使用 `RedactingFormatter`，确保日志自动脱敏。

***

### 2.5 扩展层组件

#### 2.5.1 Skills（技能系统）

**职责**：用户自定义技能（Python 脚本、Markdown 文档、MCP 服务器配置）。

**技能目录**：`~/.hermes/skills/`

**技能类型**：

| 类型            | 文件格式    | 用途        |
| ------------- | ------- | --------- |
| **Python 技能** | `.py`   | 自定义工具函数   |
| **文档技能**      | `.md`   | RAG 知识库   |
| **MCP 技能**    | `.yaml` | MCP 服务器配置 |

**技能注册流程**：

```
1. 扫描 ~/.hermes/skills/ 目录
   ↓
2. 解析 frontmatter（YAML 元数据）
   ↓
3. 验证安全性（skills_guard.py 扫描恶意代码）
   ↓
4. 注册为系统提示（非工具，保持 prompt caching）
   ↓
5. CLI 显示 `/skills list`
```

#### 2.5.2 Plugins（插件系统）

**职责**：动态扩展工具集（类似 Python 插件架构）。

**插件发现机制**：

```python
# hermes_cli/plugins.py
def discover_plugins():
    plugins_dir = get_hermes_home() / "plugins"
    for plugin_dir in plugins_dir.iterdir():
        if (plugin_dir / "plugin.json").exists():
            # 加载插件
            plugin = load_plugin(plugin_dir)
            # 注册工具
            for tool in plugin.tools:
                registry.register(...)
```

**插件结构**：

```
my_plugin/
├── plugin.json      # 元数据（name, version, description）
├── __init__.py      # 插件入口
└── tools/           # 工具实现
    ├── __init__.py
    ├── tool_a.py
    └── tool_b.py
```

#### 2.5.3 MCP（Model Context Protocol）

**职责**：动态发现外部 MCP 服务器提供的工具。

**MCP 工具注册流程**：

```
1. 连接 MCP 服务器（stdio 或 HTTP）
   ↓
2. 调用 session.list_tools()
   ↓
3. 遍历工具列表，逐个注册
   for tool in tools:
       registry.register(
           name=f"mcp__{server}__{tool.name}",
           toolset=f"mcp_{server}",
           schema=tool.schema,
           handler=lambda args: call_mcp_tool(tool.name, args),
           is_async=True
       )
   ↓
4. 监听 notifications/tools/list_changed
   └─ 收到通知 → deregister 旧工具 → 重新 register
```

***

## 3. 模块依赖关系

### 3.1 依赖层次图

```
┌──────────────────────────────────────────────────────────────┐
│  第 0 层：零依赖基石模块                                         │
│  tools/registry.py  （定义 ToolRegistry 单例）                 │
│  agent/redact.py    （定义脱敏引擎）                          │
│  hermes_constants.py（定义 HERMES_HOME 路径）                 │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  第 1 层：工具实现层（import registry）                         │
│  tools/*.py (40+ 文件)                                         │
│  - 每个文件在 import 时调用 registry.register()                 │
│  - 依赖：tools/registry.py, agent/redact.py                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  第 2 层：工具编排层                                           │
│  model_tools.py                                                │
│  - _discover_tools() → 触发第 1 层 import                       │
│  - get_tool_definitions() → registry.get_definitions()        │
│  - handle_function_call() → registry.dispatch()               │
│  - 依赖：tools/registry.py, tools/*.py                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  第 3 层：对话核心层                                           │
│  run_agent.py (AIAgent)                                        │
│  - chat() / run_conversation()                                │
│  - 依赖：model_tools.py, hermes_state.py, hermes_cli/config.py│
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  第 4 层：接入层                                               │
│  cli.py, gateway/run.py, acp_adapter/server.py               │
│  - 初始化 AIAgent                                             │
│  - 依赖：run_agent.py, hermes_cli/config.py                  │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 关键导入链

#### 3.2.1 工具注册导入链

```
model_tools._discover_tools()
    ↓ importlib.import_module
tools/terminal_tool.py
    ↓ from tools.registry import registry
tools/registry.py  （模块加载，定义 registry 单例）
    ↓ registry.register(...)
registry._tools["terminal"] = ToolEntry(...)
```

#### 3.2.2 配置加载导入链

```
cli.py
    ↓ from hermes_cli.config import load_cli_config
hermes_cli/config.py
    ↓ from hermes_constants import get_hermes_home
hermes_constants.py  （读取 HERMES_HOME 环境变量）
    ↓ 返回 ~/.hermes 或 profile 路径
config.py 应用路径加载 config.yaml 和 .env
```

#### 3.2.3 工具调用导入链

```
run_agent.py (AIAgent.run_conversation)
    ↓ from model_tools import handle_function_call
model_tools.py
    ↓ from tools.registry import registry
tools/registry.py
    ↓ entry.handler(args, **kwargs)
tools/terminal_tool.py (terminal_tool 函数)
    ↓ subprocess.run(...)
操作系统执行命令
```

### 3.3 循环依赖避免

项目通过以下策略避免循环依赖：

1. **基石模块零依赖**：`tools/registry.py`、`agent/redact.py`、`hermes_constants.py` 不 import 任何项目模块
2. **延迟导入**：部分函数内部 import 而非模块级 import
   ```python
   def some_function():
       from tools.registry import registry  # 函数内导入
   ```
3. **单向依赖链**：严格遵循 0→1→2→3→4 层依赖方向，禁止反向依赖

***

## 4. 设计模式应用

### 4.1 单例模式（Singleton）

**应用场景**：`ToolRegistry`、`SessionDB`

**实现方式**：

```python
# tools/registry.py
class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._toolset_checks = {}

# 模块级单例（Python 模块加载天然线程安全）
registry = ToolRegistry()
```

**优势**：

- 全局唯一工具注册表，避免多个实例导致注册信息分散
- 模块级实例在 Python 中天然线程安全（GIL 保护模块加载）

### 4.2 策略模式（Strategy）

**应用场景**：`check_fn` 可用性检查、审批模式、环境后端选择

**实现方式**：

```python
# 不同工具的 check_fn 策略
check_fn=lambda: bool(os.getenv("PARALLEL_API_KEY"))  # Web 工具
check_fn=check_terminal_requirements                   # 终端工具
check_fn=None                                          # MCP 工具

# 审批模式策略
APPROVAL_STRATEGIES = {
    "manual": ManualApprovalStrategy(),
    "smart": SmartApprovalStrategy(),
    "off": NoApprovalStrategy(),
}
```

**优势**：

- 统一接口（`check_fn()` 返回 bool），上层无需关心具体检查逻辑
- 新增策略无需修改调用方代码

### 4.3 工厂模式（Factory）

**应用场景**：环境后端创建、MCP 传输创建

**实现方式**：

```python
# tools/environments/__init__.py
def create_environment(env_type: str, config: dict) -> Environment:
    if env_type == "local":
        return LocalEnvironment(config)
    elif env_type == "docker":
        return DockerEnvironment(config)
    elif env_type == "ssh":
        return SSHEnvironment(config)
    elif env_type == "modal":
        return ModalEnvironment(config)
    # ...
```

**优势**：

- 集中创建逻辑，调用方无需关心具体类
- 易于扩展新环境类型

### 4.4 观察者模式（Observer）

**应用场景**：MCP `notifications/tools/list_changed`、Gateway 后台进程完成通知

**实现方式**：

```python
# MCP 服务器发送通知
await session.send_notification(
    "notifications/tools/list_changed",
    serverId=server_id
)

# Hermes 订阅通知
session.set_notification_handler(
    "notifications/tools/list_changed",
    handle_tools_list_changed
)

def handle_tools_list_changed(params):
    # 1. deregister 旧工具
    # 2. 重新 list_tools
    # 3. register 新工具
```

**优势**：

- 解耦通知发送方和接收方
- 支持动态订阅/取消订阅

### 4.5 装饰器模式（Decorator）

**应用场景**：`RedactingFormatter`、技能装饰器、日志增强

**实现方式**：

```python
# 日志脱敏装饰器
class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_sensitive_text(original)  # 装饰原始输出

# 应用装饰器
handler.setFormatter(RedactingFormatter())
```

**优势**：

- 动态增强对象功能，无需修改原始类
- 可组合多个装饰器

### 4.6 适配器模式（Adapter）

**应用场景**：Gateway 平台适配器、ACP 协议适配

**实现方式**：

```python
# 抽象基类
class BaseMessagePlatform(ABC):
    @abstractmethod
    async def connect(self)
    @abstractmethod
    async def disconnect(self)
    @abstractmethod
    async def send_message(self, chat_id, text)

# 具体适配器
class TelegramBot(BaseMessagePlatform):
    async def connect(self): ...
    async def send_message(self, chat_id, text):
        # 调用 Telegram Bot API
        await self.bot.send_message(chat_id, text)

class DiscordClient(BaseMessagePlatform):
    async def connect(self): ...
    async def send_message(self, channel_id, text):
        # 调用 Discord API
        await self.channel.send(text)
```

**优势**：

- 统一接口，上层代码无需关心具体平台
- 易于扩展新平台

### 4.7 责任链模式（Chain of Responsibility）

**应用场景**：命令审批流程、安全检查链

**实现方式**：

```python
def check_all_command_guards(command):
    # 责任链 1: Tirith 安全扫描
    tirith_result = run_tirith_scan(command)
    if tirith_result.blocked:
        return {"approved": False, "reason": tirith_result.reason}
    
    # 责任链 2: 危险命令模式检测
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return {"approved": False, "reason": reason}
    
    # 责任链 3: 敏感路径写入检测
    if is_sensitive_write(command):
        return {"approved": False, "reason": "sensitive path"}
    
    # 全部通过
    return {"approved": True}
```

**优势**：

- 每层独立检测，可单独启用/禁用
- 易于新增检测层

### 4.8 状态模式（State）

**应用场景**：OAuth Token 刷新状态机、会话状态管理

**实现方式**：

```python
# OAuth 状态机
class OAuthState:
    def refresh_token(self):
        pass

class ValidState(OAuthState):
    def refresh_token(self):
        if is_expiring_soon():
            return RefreshingState()
        return self

class RefreshingState(OAuthState):
    def refresh_token(self):
        return self  # 已在刷新中，忽略

class ReauthState(OAuthState):
    def refresh_token(self):
        # 需要重新认证
        start_device_code_flow()
        return ValidState()
```

**优势**：

- 状态转换逻辑清晰，避免大量 if-else
- 每个状态独立封装

### 4.9 依赖注入（Dependency Injection）

**应用场景**：Callbacks 注入、环境配置注入

**实现方式**：

```python
# AIAgent 构造函数注入
class AIAgent:
    def __init__(self,
                 model: str,
                 max_iterations: int,
                 clarify_callback=None,
                 approval_callback=None,
                 sudo_callback=None):
        self.clarify_callback = clarify_callback
        self.approval_callback = approval_callback
        self.sudo_callback = sudo_callback

# 调用方注入
agent = AIAgent(
    model="anthropic/claude-opus-4.6",
    clarify_callback=cli_clarify_callback,
    approval_callback=cli_approval_callback
)
```

**优势**：

- 解耦依赖创建和使用
- 易于测试（可注入 mock 对象）

***

## 5. 核心业务流程

### 5.1 对话循环流程

```
┌─────────────────────────────────────────────────────────────┐
│  用户输入："列出当前目录下的文件"                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  HermesCLI.process_command()                                 │
│  - 检查是否为 slash 命令（/model, /tools...）                  │
│  - 否 → 调用 agent.chat(message)                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AIAgent.run_conversation(user_message)                      │
│  1. build_initial_messages()                                 │
│     - system prompt（含技能、记忆）                            │
│     - user message                                           │
│  2. 加载工具 schema（model_tools.get_tool_definitions）       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 1 次 LLM 调用                                                │
│  client.chat.completions.create(                             │
│      model="anthropic/claude-opus-4.6",                      │
│      messages=[...],                                         │
│      tools=[{type: "function", function: schema}, ...]       │
│  )                                                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM 返回 tool_calls: [{name: "terminal", args: {command:    │
│  "ls -la"}}]                                                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  model_tools.handle_function_call("terminal", args)          │
│  1. coerce_tool_args() — 参数类型转换                         │
│  2. registry.dispatch("terminal", args, task_id=xxx)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  tools/registry.py.dispatch()                                │
│  - 查找 ToolEntry("terminal")                                │
│  - 调用 entry.handler(args, **kwargs)                        │
│  - 异常捕获 → {"error": "..."}                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  terminal_tool(command="ls -la", task_id=xxx)                │
│  1. check_all_guards() — 危险命令检测                         │
│  2. approval_callback() — 审批（若需要）                       │
│  3. subprocess.run(["ls", "-la"], capture_output=True)       │
│  4. redact_sensitive_text(output) — 脱敏                     │
│  5. 返回 JSON: {"output": "total 32\\n...", "exit_code": 0} │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  结果返回给 LLM（tool role message）                          │
│  {"role": "tool", "tool_call_id": "...", "content": result} │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 2 次 LLM 调用（含工具结果）                                  │
│  client.chat.completions.create(messages=[..., tool_result]) │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM 返回最终响应（无 tool_calls）                              │
│  {"content": "当前目录下有以下文件：..."}                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  结果返回给 CLI → Rich 面板显示                                │
│  ┌────────────────────────────────────┐                     │
│  │  ⚡ Hermes Agent                    │                     │
│  │  当前目录下有以下文件：...           │                     │
│  └────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 工具注册流程

```
┌─────────────────────────────────────────────────────────────┐
│  应用启动（hermes 命令 / gateway run / AIAgent 初始化）         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  model_tools._discover_tools()                               │
│  tool_modules = [                                            │
│      "tools.terminal_tool",                                  │
│      "tools.file_tools",                                     │
│      "tools.browser_tool",                                   │
│      # ... 40+ 模块                                           │
│  ]                                                           │
│  for module_name in tool_modules:                            │
│      importlib.import_module(module_name)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │terminal.py │ │ file_tools │ │ browser.py │
     │  import    │ │   import   │ │   import   │
     └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
           │              │              │
           ▼              ▼              ▼
     ┌──────────────────────────────────────────────┐
     │  每个工具文件模块级代码执行：                    │
     │                                              │
     │  from tools.registry import registry         │
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
                        │
                        ▼
     ┌──────────────────────────────────────────────┐
     │  触发 MCP 和插件发现                            │
     │  from tools.mcp_tool import discover_mcp_tools│
     │  from hermes_cli.plugins import discover_plugins│
     │                                              │
     │  discover_mcp_tools() → registry.register()  │
     │  discover_plugins() → registry.register()    │
     └──────────────────────────────────────────────┘
```

### 5.3 CLI 启动流程

```
┌─────────────────────────────────────────────────────────────┐
│  用户执行：hermes                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  hermes_cli.main:main()                                      │
│  - 解析命令行参数（-m model, --yolo, -q quiet...）            │
│  - 应用 profile 覆盖（-p profile_name → HERMES_HOME）         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  HermesCLI.__init__()                                        │
│  1. load_cli_config() → 加载 config.yaml + .env              │
│  2. init_skin() → 加载 CLI 主题                                │
│  3. 初始化 SessionDB → 连接 SQLite                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  HermesCLI.run()                                             │
│  1. 显示 banner（Rich 面板，皮肤定制）                         │
│  2. 初始化 AIAgent                                            │
│     AIAgent(                                                 │
│         model=config["model"],                               │
│         max_iterations=config["max_iterations"],             │
│         clarify_callback=cli_clarify_callback,               │
│         approval_callback=cli_approval_callback,             │
│         ...                                                  │
│     )                                                        │
│  3. 显示欢迎消息和工具预览                                    │
│  4. 进入主循环                                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  主循环：while True                                           │
│  1. prompt_toolkit 获取用户输入                               │
│  2. process_command(cmd)                                    │
│     ├─ /model → 切换模型                                     │
│     ├─ /tools → 显示工具列表                                 │
│     ├─ /memory → 管理记忆                                    │
│     ├─ /quit → 退出循环                                      │
│     └─ 普通消息 → agent.chat(message)                        │
│  3. 显示响应（Rich 面板）                                     │
│  4. 保存会话到 SQLite（append_message）                      │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 网关启动流程

```
┌─────────────────────────────────────────────────────────────┐
│  用户执行：hermes gateway run                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  gateway.run:run_gateway()                                   │
│  1. 加载网关配置（~/.hermes/config.yaml 的 gateway.*）         │
│  2. 解析平台配置（telegram, discord, slack...）              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  初始化平台适配器                                              │
│  platforms = []                                              │
│  if config["telegram"]["enabled"]:                           │
│      platforms.append(TelegramBot(config["telegram"]))       │
│  if config["discord"]["enabled"]:                            │
│      platforms.append(DiscordClient(config["discord"]))      │
│  # ... 15+ 平台                                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  连接平台（并行）                                              │
│  async with asyncio.TaskGroup() as tg:                       │
│      for platform in platforms:                              │
│          tg.create_task(platform.connect())                  │
│                                                              │
│  - Telegram: bot.polling()                                   │
│  - Discord: client.start(token)                              │
│  - Slack: Socket Mode WebSocket                              │
│  - Webhook: aiohttp.web.run_app(port=8644)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  消息监听循环（每个平台独立协程）                               │
│  async def message_listener():                               │
│      while True:                                             │
│          event = await platform.receive_event()              │
│          if not _is_user_authorized(event.user_id):          │
│              continue  # 未授权用户，跳过                       │
│          await handle_event(event)                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  handle_event(event)                                         │
│  1. 解析消息内容（文本、图片、附件）                           │
│  2. 构建会话上下文（SessionStore.build_context）             │
│  3. 调用 AIAgent.chat(message)                               │
│  4. 发送响应（platform.send_message）                        │
│  5. 保存会话到 JSONL（SessionStore._save）                   │
└─────────────────────────────────────────────────────────────┘
```

### 5.5 OAuth 认证流程（以 Nous Portal 为例）

```
┌─────────────────────────────────────────────────────────────┐
│  用户执行：hermes model → 选择 nous/portal                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  hermes_cli.auth:resolve_provider("nous")                    │
│  1. 检查 ~/.hermes/auth.json 是否有有效 token                 │
│  2. 无 → 启动 OAuth 设备码流                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: 请求设备码                                            │
│  POST https://api.nous.com/api/oauth/device/code           │
│  Response: {                                                │
│      "device_code": "xxx",                                  │
│      "user_code": "ABC-123",                                │
│      "verification_uri": "https://nous.com/activate",       │
│      "expires_in": 900,                                     │
│      "interval": 5                                          │
│  }                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: 显示用户码，引导用户授权                               │
│  ┌────────────────────────────────────┐                     │
│  │  请访问：https://nous.com/activate  │                     │
│  │  输入用户码：ABC-123                │                     │
│  │  等待授权中... [spinner]            │                     │
│  └────────────────────────────────────┘                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: 轮询 Token（每 5 秒一次）                               │
│  POST https://api.nous.com/api/oauth/token                 │
│  Body: {                                                    │
│      "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
│      "device_code": "xxx"                                   │
│  }                                                          │
│                                                              │
│  响应 1: {"error": "authorization_pending"} → 继续轮询       │
│  响应 2: {                                                  │
│      "access_token": "ya.xxx",                              │
│      "refresh_token": "1//xxx",                             │
│      "expires_in": 3600                                     │
│  } → 成功                                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 铸造 Agent Key（短期推理 API 密钥）                     │
│  POST https://api.nous.com/api/oauth/agent-key             │
│  Headers: {Authorization: Bearer ya.xxx}                    │
│  Response: {                                                │
│      "key": "nsk_xxx",                                      │
│      "expires_at": "2026-04-14T12:00:00Z"                   │
│  }                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: 持久化到 ~/.hermes/auth.json                        │
│  {                                                          │
│      "provider": "nous",                                    │
│      "access_token": "ya.xxx",                              │
│      "refresh_token": "1//xxx",                             │
│      "agent_key": "nsk_xxx",                                │
│      "expires_at": 1776136400                               │
│  }                                                          │
│  文件权限：0600（仅所有者可读写）                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 6: 设置运行时环境变量                                   │
│  os.environ["NOUS_API_KEY"] = "nsk_xxx"                     │
│  os.environ["NOUS_BASE_URL"] = "https://api.nous.com"       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  后续使用：AIAgent 调用 LLM                                     │
│  client.chat.completions.create(                            │
│      model="nous/hermes-2.4",                               │
│      api_key="nsk_xxx",  # 从环境变量自动注入                 │
│      base_url="https://api.nous.com/v1"                     │
│  )                                                          │
└─────────────────────────────────────────────────────────────┘
```

### 5.6 子代理委托流程

```
┌─────────────────────────────────────────────────────────────┐
│  父代理收到用户请求："帮我分析这个 GitHub 仓库的代码结构"         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  父代理决定委托子代理（LLM 调用 delegate_task 工具）            │
│  delegate_task(                                             │
│      prompt="分析 GitHub 仓库 https://github.com/xxx/yyy 的代码结构",
│      toolsets=["core", "web", "terminal"],                  │
│      max_iterations=30                                      │
│  )                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  tools/delegate_tool.py:delegate_task()                      │
│  1. 检查委托深度（MAX_DEPTH=2）                              │
│     parent._delegate_depth = 0 → child_depth = 1 ✓          │
│  2. 计算子代理工具集（父代理工具集交集）                       │
│     child_toolsets = parent_toolsets ∩ requested_toolsets   │
│  3. 过滤黑名单工具（delegate_task, clarify, memory...）      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  创建子代理实例                                               │
│  child_agent = AIAgent(                                     │
│      model=parent.model,                                    │
│      max_iterations=30,                                     │
│      enabled_toolsets=child_toolsets,                       │
│      skip_context_files=True,  # 不加载上下文文件             │
│      skip_memory=True,         # 不加载记忆                   │
│      clarify_callback=None,    # 不能与用户交互               │
│      session_id=new_session_id,                             │
│      task_id=new_task_id                                    │
│  )                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  子代理独立运行对话循环                                       │
│  child_result = child_agent.chat(prompt)                    │
│  - 子代理可调用 terminal, web_search, read_file 等工具        │
│  - 子代理不能调用 delegate_task（防止递归）                   │
│  - 子代理不能调用 clarify（不能打扰用户）                     │
│  - 子代理不能写入 memory（避免污染共享记忆）                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  子代理完成任务，返回结果                                     │
│  {                                                          │
│      "success": True,                                       │
│      "summary": "该仓库包含以下模块：...",                   │
│      "details": "src/ 目录包含核心逻辑，tests/ 包含单元测试..."  │
│  }                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  结果返回给父代理，继续主对话                                  │
│  parent 收到子代理结果 → 整合到最终响应 → 返回给用户           │
└─────────────────────────────────────────────────────────────┘
```

### 5.7 代码执行沙箱流程

```
┌─────────────────────────────────────────────────────────────┐
│  LLM 调用 execute_code 工具                                   │
│  execute_code(                                              │
│      language="python",                                     │
│      code="import os; print(os.getcwd())",                  │
│      timeout=60                                             │
│  )                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  tools/code_execution_tool.py:execute_code()                 │
│  1. 参数验证（code 非空，language 支持）                       │
│  2. 创建沙箱环境（UDS socket 或文件 RPC）                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  启动子进程（sandbox_runner.py）                              │
│  proc = subprocess.Popen(                                   │
│      [sys.executable, "sandbox_runner.py"],                 │
│      preexec_fn=os.setsid,  # 新进程组                       │
│      env=safe_env,  # 过滤后的环境变量（无 API Key）          │
│  )                                                          │
│                                                              │
│  safe_env 构建：                                             │
│  - 阻断含 KEY/TOKEN/SECRET/PASSWORD 的变量                   │
│  - 放行 PATH, HOME, USER, LANG 等安全变量                    │
│  - 技能声明的 passthrough 变量                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  子进程初始化 RPC 通道                                         │
│  1. 连接 UDS socket（本地后端）或创建请求文件（远程后端）      │
│  2. 等待父进程发送代码                                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  父进程发送代码（通过 RPC）                                    │
│  send_request("execute", {                                  │
│      "language": "python",                                  │
│      "code": "import os; print(os.getcwd())",               │
│      "allowed_tools": SANDBOX_ALLOWED_TOOLS,                │
│      "max_tool_calls": 50                                   │
│  })                                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  子进程执行代码                                               │
│  exec(code, {"__builtins__": SAFE_BUILTINS}, {})            │
│                                                              │
│  代码调用工具（如 read_file）：                               │
│  → RPC 回调父进程 → registry.dispatch() → 执行工具 → 返回结果 │
│                                                              │
│  工具白名单检查：                                            │
│  if tool_name not in allowed_tools:                         │
│      raise PermissionError(f"Tool {tool_name} not allowed") │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  执行完成，收集 stdout/stderr                                 │
│  stdout = proc.stdout.read(MAX_STDOUT_BYTES)  # 50KB 上限    │
│  stderr = proc.stderr.read(MAX_STDERR_BYTES)  # 10KB 上限    │
│  exit_code = proc.returncode                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  结果处理                                                     │
│  1. ANSI 剥离（strip_ansi）                                  │
│  2. 敏感信息脱敏（redact_sensitive_text）                    │
│  3. 构建 JSON 结果                                            │
│  {                                                          │
│      "success": exit_code == 0,                             │
│      "stdout": "脱敏后的输出",                                │
│      "stderr": "",                                          │
│      "exit_code": 0,                                        │
│      "tool_calls": 5  # 实际调用次数                         │
│  }                                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  清理资源                                                     │
│  1. 关闭 UDS socket 或删除请求/响应文件                        │
│  2. 终止子进程（timeout 或正常退出）                           │
│  3. 返回结果给 LLM                                            │
└─────────────────────────────────────────────────────────────┘
```

***

## 6. 数据流分析

### 6.1 用户输入 → LLM → 工具调用 → 结果返回

```
┌──────────────────────────────────────────────────────────────┐
│                      数据流总览                               │
│                                                              │
│  用户输入 → CLI/Gateway → AIAgent → LLM → Tool Call →        │
│  ↓                                                           │
│  model_tools → registry.dispatch → tool handler → 执行 →     │
│  ↓                                                           │
│  结果 JSON → LLM → 最终响应 → 用户                            │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 配置数据流

```
┌──────────────────────────────────────────────────────────────┐
│                   配置加载数据流                              │
│                                                              │
│  ~/.hermes/config.yaml                                       │
│  ├── display.skin: "default"                                 │
│  ├── model: "anthropic/claude-opus-4.6"                      │
│  ├── max_iterations: 90                                      │
│  └── terminal.approval_mode: "manual"                        │
│          │                                                   │
│          ▼                                                   │
│  load_cli_config()                                           │
│  ├── 读取 YAML                                               │
│  ├── 合并 DEFAULT_CONFIG                                     │
│  ├── 应用 profile 覆盖（HERMES_HOME）                         │
│  └── 返回 config dict                                        │
│          │                                                   │
│          ▼                                                   │
│  AIAgent.__init__(**config)                                  │
│  └── 初始化对话循环参数                                       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  环境变量数据流                               │
│                                                              │
│  ~/.hermes/.env                                              │
│  ├── ANTHROPIC_API_KEY=sk-ant-xxx                            │
│  ├── TELEGRAM_BOT_TOKEN=bot123:ABC-...                       │
│  └── SUDO_PASSWORD=secret123                                 │
│          │                                                   │
│          ▼                                                   │
│  load_dotenv() → os.environ                                  │
│          │                                                   │
│          ▼                                                   │
│  resolve_provider() → 查找 API Key                           │
│  ├── 检查 os.environ["ANTHROPIC_API_KEY"]                    │
│  └── 返回有效值或抛出 AuthError                              │
│          │                                                   │
│          ▼                                                   │
│  AIAgent 调用 LLM → API Key 注入到 HTTP 请求头                   │
└──────────────────────────────────────────────────────────────┘
```

### 6.3 会话数据流

```
┌──────────────────────────────────────────────────────────────┐
│                   会话持久化数据流                            │
│                                                              │
│  用户消息 → AIAgent.chat()                                   │
│          │                                                   │
│          ▼                                                   │
│  SessionDB.append_message(                                   │
│      session_id="abc123",                                    │
│      role="user",                                            │
│      content="列出当前目录下的文件"                            │
│  )                                                           │
│          │                                                   │
│          ▼                                                   │
│  SQLite: INSERT INTO messages (session_id, role, content)   │
│          │                                                   │
│          ▼                                                   │
│  AIAgent 调用 LLM → 工具调用 → 结果                            │
│          │                                                   │
│          ▼                                                   │
│  SessionDB.append_message(                                   │
│      session_id="abc123",                                    │
│      role="assistant",                                       │
│      content="当前目录下有以下文件：..."                       │
│  )                                                           │
│          │                                                   │
│          ▼                                                   │
│  SQLite: INSERT INTO messages (...)                          │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   会话搜索数据流                              │
│                                                              │
│  用户执行：/search "文件操作"                                  │
│          │                                                   │
│          ▼                                                   │
│  SessionDB.search_messages(query="文件操作", limit=20)        │
│          │                                                   │
│          ▼                                                   │
│  FTS5: SELECT * FROM messages_fts WHERE content MATCH ?      │
│          │                                                   │
│          ▼                                                   │
│  返回匹配的消息列表（含 session_id, role, content, score）    │
│          │                                                   │
│          ▼                                                   │
│  CLI 显示搜索结果面板                                         │
└──────────────────────────────────────────────────────────────┘
```

### 6.4 工具调用数据流

```
┌──────────────────────────────────────────────────────────────┐
│                   工具调用数据流                              │
│                                                              │
│  LLM tool_call: {name: "terminal", args: {command: "ls"}}    │
│          │                                                   │
│          ▼                                                   │
│  model_tools.handle_function_call("terminal", args)          │
│  ├── coerce_tool_args(args, schema) → 类型转换               │
│  └── registry.dispatch("terminal", args, task_id=xxx)        │
│          │                                                   │
│          ▼                                                   │
│  tools/registry.py.dispatch()                                │
│  ├── entry = self._tools["terminal"]                         │
│  ├── result = entry.handler(args, task_id=xxx)               │
│  └── except Exception → {"error": "..."}                     │
│          │                                                   │
│          ▼                                                   │
│  terminal_tool(command="ls", task_id=xxx)                    │
│  ├── check_all_guards(command) → 安全检查                    │
│  ├── approval_callback() → 审批（若需要）                     │
│  ├── subprocess.run(["ls"], capture_output=True)             │
│  ├── strip_ansi(output) → ANSI 剥离                          │
│  ├── redact_sensitive_text(output) → 脱敏                    │
│  └── json.dumps({"output": "...", "exit_code": 0})           │
│          │                                                   │
│          ▼                                                   │
│  结果返回给 LLM（tool role message）                          │
└──────────────────────────────────────────────────────────────┘
```

***

## 7. 配置与状态管理

### 7.1 配置层次

```
┌──────────────────────────────────────────────────────────────┐
│                   配置层次结构                                │
│                                                              │
│  第 1 层：硬编码默认值（DEFAULT_CONFIG）                        │
│  ├── model: "anthropic/claude-opus-4.6"                      │
│  ├── max_iterations: 90                                      │
│  └── display.skin: "default"                                 │
│          │                                                   │
│          ▼ 覆盖                                               │
│  第 2 层：~/.hermes/config.yaml（用户配置）                    │
│  ├── model: "openai/gpt-4o"                                  │
│  ├── terminal.approval_mode: "smart"                         │
│  └── gateway.telegram.enabled: true                          │
│          │                                                   │
│          ▼ 覆盖                                               │
│  第 3 层：命令行参数（-m model, --yolo, -q）                   │
│  ├── hermes -m anthropic/claude-sonnet-4-20250514            │
│  ├── hermes --yolo                                           │
│  └── hermes -q                                               │
│          │                                                   │
│          ▼ 覆盖                                               │
│  第 4 层：环境变量（HERMES_*, ANTHROPIC_API_KEY）             │
│  ├── HERMES_HOME=/tmp/hermes-profile                         │
│  ├── HERMES_MAX_ITERATIONS=50                                │
│  └── ANTHROPIC_API_KEY=sk-ant-xxx                            │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 Profile 隔离

```
┌──────────────────────────────────────────────────────────────┐
│                  Profile 隔离机制                             │
│                                                              │
│  HERMES_HOME=/home/user/.hermes（默认）                      │
│  ├── config.yaml                                             │
│  ├── .env                                                    │
│  ├── auth.json                                               │
│  ├── state.db                                                │
│  ├── skills/                                                 │
│  ├── memories/                                               │
│  └── gateway/                                                │
│                                                              │
│  HERMES_HOME=/home/user/.hermes/profiles/coder（Profile）    │
│  ├── config.yaml（独立配置）                                  │
│  ├── .env（独立 API Keys）                                    │
│  ├── auth.json（独立 OAuth 凭据）                             │
│  ├── state.db（独立会话）                                     │
│  ├── skills/（独立技能）                                      │
│  └── memories/（独立记忆）                                    │
└──────────────────────────────────────────────────────────────┘
```

### 7.3 状态管理

```
┌──────────────────────────────────────────────────────────────┐
│                   状态管理组件                                │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  SessionDB      │    │  SessionStore   │                 │
│  │  (SQLite)       │    │  (JSONL)        │                 │
│  │                 │    │                 │                 │
│  │  - sessions 表  │    │  - sessions.json│                 │
│  │  - messages 表  │    │  - <sid>.jsonl  │                 │
│  │  - FTS5 索引     │    │  - 转录文件      │                 │
│  └─────────────────┘    └─────────────────┘                 │
│          │                       │                           │
│          │                       │                           │
│          ▼                       ▼                           │
│  ┌─────────────────────────────────────────┐                 │
│  │         AIAgent（内存状态）              │                 │
│  │  - messages 列表（当前对话）              │                 │
│  │  - iteration_budget（迭代预算）          │                 │
│  │  - task_id（当前任务 ID）                │                 │
│  │  - delegate_depth（委托深度）            │                 │
│  └─────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────┘
```

***

## 8. 扩展机制

### 8.1 Skills vs Plugins vs MCP 对比

| 特性        | Skills                    | Plugins                        | MCP                                   |
| --------- | ------------------------- | ------------------------------ | ------------------------------------- |
| **文件格式**  | `.py` / `.md` / `.yaml`   | Python 包（`plugin.json` + 工具模块） | 外部服务器（stdio/HTTP）                     |
| **注册方式**  | 系统提示注入（保持 prompt caching） | `registry.register()` 工具注册     | `registry.register()` 动态注册            |
| **安全性**   | `skills_guard.py` 安装前扫描   | Python 代码完全访问权限                | MCP 服务器沙箱隔离                           |
| **热更新**   | 否（需重启）                    | 否（需重启）                         | 是（`notifications/tools/list_changed`） |
| **工具集归属** | `skills`                  | 自定义 toolset                    | `mcp_<server>`                        |
| **适用场景**  | 知识库、简单脚本、MCP 配置           | 复杂工具、需要 Python 依赖              | 外部服务集成                                |

### 8.2 扩展点总览

```
┌──────────────────────────────────────────────────────────────┐
│                   系统扩展点                                  │
│                                                              │
│  1. 工具扩展                                                  │
│     ├── 新增 tools/*.py → registry.register()               │
│     ├── MCP 服务器 → 动态注册                                 │
│     └── Plugins → 包式工具集                                  │
│                                                              │
│  2. 记忆扩展                                                  │
│     ├── 记忆插件（plugins/memory/*）                         │
│     │   ├── SuperMemory                                      │
│     │   ├── RetainDB                                       │
│     │   ├── OpenViking                                     │
│     │   └── Mem0                                           │
│     └── MEMORY.md（内置）                                    │
│                                                              │
│  3. 环境扩展                                                  │
│     ├── tools/environments/*                                 │
│     │   ├── LocalEnvironment                                 │
│     │   ├── DockerEnvironment                                │
│     │   ├── SSHEnvironment                                   │
│     │   ├── ModalEnvironment                                 │
│     │   └── DaytonaEnvironment                               │
│     └── 自定义环境（实现 Environment 接口）                    │
│                                                              │
│  4. 平台扩展                                                  │
│     ├── gateway/platforms/*                                  │
│     │   ├── TelegramBot                                      │
│     │   ├── DiscordClient                                    │
│     │   ├── SlackClient                                      │
│     │   └── ... (15+ 平台)                                   │
│     └── 自定义平台（实现 BaseMessagePlatform 接口）            │
│                                                              │
│  5. UI 扩展                                                   │
│     ├── 皮肤系统（~/.hermes/skins/*.yaml）                   │
│     └── 内置皮肤（default, ares, mono, slate）              │
└──────────────────────────────────────────────────────────────┘
```

***

## 9. 架构决策与权衡

### 9.1 关键架构决策

| 决策         | 选择                        | 替代方案                 | 理由                          |
| ---------- | ------------------------- | -------------------- | --------------------------- |
| **工具注册方式** | 声明式自注册（import 时）          | 中央配置文件               | 减少配置膨胀，新增工具只需创建文件           |
| **对话核心**   | 同步主循环 + 异步桥接              | 纯异步架构                | 简化 CLI 实现，异步桥接透明化           |
| **工具调用分发** | 集中式 registry.dispatch()   | 分散式 handler 查找       | 统一错误处理、日志、审计                |
| **配置存储**   | YAML + .env               | JSON / TOML / 纯环境变量  | YAML 可读性好，.env 符合 Python 生态 |
| **会话存储**   | SQLite + FTS5             | PostgreSQL / MongoDB | 零依赖、嵌入式、FTS5 足够用            |
| **安全模型**   | 纵深防御（7 层）                 | 单一边界防护               | 某层被绕过，下层仍提供保护               |
| **扩展机制**   | Skills + Plugins + MCP 三轨 | 单一插件系统               | 满足不同复杂度需求                   |

### 9.2 技术债务与改进方向

| 问题                   | 影响       | 优先级 | 改进建议                       |
| -------------------- | -------- | --- | -------------------------- |
| `tool_result()` 无人使用 | 代码冗余     | 低   | 推广使用或标记废弃                  |
| `_tools` 被外部直接访问     | 封装破坏     | 中   | 添加 `get_entries()` 公共方法    |
| `redact_key()` 重复定义  | 维护成本     | 低   | 统一到 `redact.py`            |
| check\_fn 缓存仅限单次调用   | 重复执行     | 中   | 实例级缓存 + TTL                |
| 无工具版本管理              | MCP 工具冲突 | 中   | 添加 version 字段              |
| SQLite 文件权限未设置       | 安全风险     | 中   | 创建后 `chmod 0600`           |
| 轨迹保存无原子写入            | 文件损坏风险   | 低   | 使用 `tempfile + os.replace` |

### 9.3 性能优化点

| 优化点            | 当前状态           | 建议                            |
| -------------- | -------------- | ----------------------------- |
| 工具 Schema 生成   | 每次 LLM 调用前重新过滤 | 缓存可用工具列表（TTL 5 分钟）            |
| FTS5 搜索        | 无查询缓存          | 热门查询结果缓存（LRU）                 |
| OAuth Token 刷新 | 提前 2 分钟刷新      | 基于剩余有效期动态调整刷新时机               |
| 日志写入           | 同步写入文件         | 异步队列批量写入（100ms 缓冲）            |
| Gateway 消息监听   | 每平台独立协程        | 使用 `asyncio.TaskGroup` 管理生命周期 |

***

## 附录：架构图索引

1. [系统架构层次图](#11-架构层次)
2. [依赖层次图](#31-依赖层次图)
3. [对话循环流程图](#51-对话循环流程)
4. [工具注册流程图](#52-工具注册流程)
5. [CLI 启动流程图](#53-cli-启动流程)
6. [网关启动流程图](#54-网关启动流程)
7. [OAuth 认证流程图](#55-oauth-认证流程)
8. [子代理委托流程图](#56-子代理委托流程)
9. [代码执行沙箱流程图](#57-代码执行沙箱流程)
10. [配置数据流图](#62-配置数据流)
11. [会话数据流图](#63-会话数据流)
12. [工具调用数据流图](#64-工具调用数据流)
13. [扩展机制对比表](#81-skills-vs-plugins-vs-mcp-对比)
14. [扩展点总览图](#82-扩展点总览)


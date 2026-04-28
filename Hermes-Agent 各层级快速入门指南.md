# Hermes Agent 各层级快速入门指南

> **目标**: 针对架构图中每个层级，提供具体的代码入口、核心代码片段和快速上手方案。

---

## 📋 目录

1. [入口层 (Entry Layer)](#1-入口层-entry-layer)
2. [会话与路由层 (Session & Routing Layer)](#2-会话与路由层-session--routing-layer)
3. [Agent Runtime Core](#3-agent-runtime-core)
4. [能力层 (Capability Layer)](#4-能力层-capability-layer)
5. [执行层 (Execution Backends)](#5-执行层-execution-backends)
6. [状态层 (Data, State & Persistence)](#6-状态层-data-state--persistence)
7. [模型层 (Model / Provider Layer)](#7-模型层-model--provider-layer)
8. [安全层 (Security Boundaries)](#8-安全层-security-boundaries)

---

## 1. 入口层 (Entry Layer)

> 所有用户交互的入口点，包括 CLI、消息平台、定时任务、ACP 集成等。

### 1.1 核心入口文件

**入口路由**: [`hermes_cli/main.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/hermes_cli/main.py)

```python
# hermes_cli/main.py — 主入口路由

def main():
    """Main entry point for the `hermes` CLI."""
    parser = argparse.ArgumentParser(
        description="Hermes Agent - AI agent with tool calling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command")
    
    # hermes (default: chat)
    chat_parser = subparsers.add_parser("chat", ...)
    
    # hermes gateway
    gw_parser = subparsers.add_parser("gateway", ...)
    
    # hermes setup
    setup_parser = subparsers.add_parser("setup", ...)
    
    # hermes acp (editor integration)
    acp_parser = subparsers.add_parser("acp", ...)
    
    args = parser.parse_args()
    
    # Dispatch
    if args.command == "chat":
        run_chat(args)
    elif args.command == "gateway":
        run_gateway(args)
    elif args.command == "setup":
        run_setup(args)
```

### 1.2 CLI 入口

**文件**: [`cli.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/cli.py)

```python
# cli.py — HermesCLI 类

class HermesCLI:
    def __init__(self, args):
        self.console = Console(...)
        self.agent = None
        
    def start(self):
        """Start interactive CLI session."""
        # 1. Load config
        self.config = load_cli_config()
        
        # 2. Initialize agent
        self.agent = AIAgent(
            model=self.config.get("model", {}).get("default", "anthropic/claude-opus-4.6"),
            platform="cli",
        )
        
        # 3. Start REPL loop
        self._run_repl()
    
    def _run_repl(self):
        """Interactive Read-Eval-Print Loop."""
        while True:
            user_input = self._read_input()
            if user_input is None:
                break  # EOF / Ctrl-D
            
            if user_input.startswith("/"):
                self._process_command(user_input)
            else:
                self._process_message(user_input)
```

### 1.3 Gateway 入口

**文件**: [`gateway/run.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/gateway/run.py)

```python
# gateway/run.py — GatewayRunner 类

class GatewayRunner:
    async def start(self):
        """Start all configured platform adapters."""
        # Load config
        self.config = load_gateway_config()
        
        # Start platform adapters
        adapters = []
        for platform in self.config.get("platforms", []):
            adapter = self._create_adapter(platform)
            adapters.append(adapter)
            asyncio.create_task(adapter.start())
        
        # Keep running until shutdown
        await self._wait_for_shutdown()
```

### 1.4 快速入门

```bash
# CLI 模式
hermes                    # 交互式对话
hermes chat -q "Hello"    # 单次查询

# Gateway 模式
hermes gateway telegram   # Telegram 机器人
hermes gateway discord    # Discord 机器人
hermes gateway start      # 启动所有配置的平台

# 其他入口
hermes setup              # 配置向导
hermes acp                # 编辑器集成
hermes cron list          # 定时任务
```

---

## 2. 会话与路由层 (Session & Routing Layer)

> 管理会话生命周期、消息路由、命令守卫。

### 2.1 会话管理器

**文件**: [`gateway/session.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/gateway/session.py)

```python
# gateway/session.py — SessionSource 类

@dataclass
class SessionSource:
    """消息来源描述"""
    platform: Platform              # telegram, discord, cli, ...
    chat_id: str                    # 聊天 ID
    chat_name: Optional[str] = None # 聊天名称
    chat_type: str = "dm"           # dm, group, channel
    user_id: Optional[str] = None   # 用户 ID
    user_name: Optional[str] = None # 用户名称
    thread_id: Optional[str] = None # 线程 ID
    
    def session_key(self) -> str:
        """生成唯一会话键"""
        return f"{self.platform}:{self.chat_id}:{self.thread_id or ''}"
```

### 2.2 会话存储

**文件**: [`hermes_state.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/hermes_state.py)

```python
# hermes_state.py — SessionDB 类

class SessionDB:
    """SQLite 会话存储，支持 FTS5 全文搜索"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._init_schema()
    
    def create_session(self, session_id: str, **kwargs):
        """创建新会话"""
        self.conn.execute("""
            INSERT OR IGNORE INTO sessions (id, source, model, started_at, ...)
            VALUES (?, ?, ?, ?, ...)
        """, (session_id, source, model, time.time(), ...))
        self.conn.commit()
    
    def append_message(self, session_id: str, role: str, content: str, ...):
        """追加消息到会话"""
        self.conn.execute("""
            INSERT INTO messages (session_id, role, content, timestamp, ...)
            VALUES (?, ?, ?, ?, ...)
        """, (session_id, role, content, time.time(), ...))
        self.conn.commit()
    
    def search_sessions(self, query: str, limit: int = 20):
        """全文搜索会话"""
        results = self.conn.execute("""
            SELECT sessions.id, sessions.title, messages.content,
                   rank FROM messages_fts
            JOIN messages ON messages_fts.rowid = messages.id
            JOIN sessions ON messages.session_id = sessions.id
            WHERE messages_fts MATCH ?
            ORDER BY rank LIMIT ?
        """, (query, limit)).fetchall()
        return results
```

### 2.3 命令守卫

**文件**: [`hermes_cli/commands.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/hermes_cli/commands.py)

```python
# hermes_cli/commands.py — 命令注册

@dataclass
class CommandDef:
    name: str                  # 命令名
    description: str           # 描述
    category: str              # 分类
    aliases: tuple = ()        # 别名
    args_hint: str = ""        # 参数提示
    cli_only: bool = False     # 仅 CLI
    gateway_only: bool = False # 仅 Gateway
    
COMMAND_REGISTRY = [
    CommandDef("new", "Start a new conversation", "Session"),
    CommandDef("reset", "Reset the current session", "Session"),
    CommandDef("undo", "Undo the last message", "Session"),
    CommandDef("model", "Switch to a different model", "Configuration"),
    CommandDef("tools", "Manage tools", "Tools & Skills"),
    CommandDef("yolo", "Toggle YOLO mode", "Session"),
]
```

### 2.4 快速入门

```python
# 创建新会话
from hermes_state import SessionDB

db = SessionDB()
session_id = db.create_session(
    source="cli",
    model="anthropic/claude-opus-4.6"
)

# 追加消息
db.append_message(
    session_id=session_id,
    role="user",
    content="Hello, how are you?"
)

# 搜索会话
results = db.search_sessions("python programming")
```

---

## 3. Agent Runtime Core

> 核心 Agent 运行时，包括主循环、提示词组装、上下文压缩、辅助模型任务、重试回退。

### 3.1 AIAgent 主循环

**文件**: [`run_agent.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/run_agent.py)

```python
# run_agent.py — AIAgent 类

class AIAgent:
    def __init__(self,
        model: str = "anthropic/claude-opus-4.6",
        max_iterations: int = 90,
        enabled_toolsets: list = None,
        disabled_toolsets: list = None,
        quiet_mode: bool = False,
        platform: str = None,
        session_id: str = None,
    ):
        self.model = model
        self.max_iterations = max_iterations
        self.tools = get_tool_definitions(...)
        self.valid_tool_names = {t["function"]["name"] for t in self.tools}
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def run_conversation(self, user_message: str, ...) -> dict:
        """
        核心对话循环：
        1. 构建消息列表
        2. 调用 LLM API
        3. 处理工具调用
        4. 检查压缩阈值
        5. 循环直到完成
        """
        messages = self._build_messages(user_message, ...)
        api_call_count = 0
        
        while api_call_count < self.max_iterations:
            # 1. API 调用
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
            )
            api_call_count += 1
            
            assistant_msg = response.choices[0].message
            
            # 2. 检查工具调用
            if assistant_msg.tool_calls:
                for tool_call in assistant_msg.tool_calls:
                    result = handle_function_call(
                        tool_call.function.name,
                        tool_call.function.arguments,
                        task_id=self.task_id,
                    )
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                # 3. 无工具调用，返回最终响应
                return {"final_response": assistant_msg.content, "messages": messages}
            
            # 4. 检查是否需要上下文压缩
            if self.context_compressor.should_compress(messages):
                messages = self.context_compressor.compress(messages)
```

### 3.2 提示词组装

**文件**: [`agent/prompt_builder.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/agent/prompt_builder.py)

```python
# agent/prompt_builder.py — 提示词组装

def _build_system_prompt(self) -> str:
    """组装完整的系统提示词"""
    parts = []
    
    # 1. Agent 身份
    if load_soul_md():
        parts.append(load_soul_md())
    else:
        parts.append(DEFAULT_AGENT_IDENTITY)
    
    # 2. 工具使用指导
    if "memory" in self.valid_tool_names:
        parts.append(MEMORY_GUIDANCE)
    if "skill_manage" in self.valid_tool_names:
        parts.append(SKILLS_GUIDANCE)
    
    # 3. 记忆系统
    if self._memory_store and self._memory_enabled:
        mem_block = self._memory_store.format_for_system_prompt("memory")
        if mem_block:
            parts.append(mem_block)
    
    # 4. 技能系统
    skills_prompt = build_skills_system_prompt(...)
    if skills_prompt:
        parts.append(skills_prompt)
    
    # 5. 上下文文件
    context_files = build_context_files_prompt(...)
    if context_files:
        parts.append(context_files)
    
    # 6. 时间戳和模型信息
    parts.append(f"Conversation started: {datetime.now()}")
    parts.append(f"Model: {self.model}")
    
    return "\n\n".join(p.strip() for p in parts if p.strip())
```

### 3.3 上下文压缩

**文件**: [`agent/context_compressor.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/agent/context_compressor.py)

```python
# agent/context_compressor.py — ContextCompressor 类

class ContextCompressor(ContextEngine):
    def compress(self, messages: List[Dict]) -> List[Dict]:
        """
        压缩算法：
        1. 保护头部（系统提示词 + 首轮对话）
        2. 保护尾部（最近 N 条消息）
        3. 用辅助 LLM 总结中间部分
        """
        # 1. 保护头部
        head = messages[:2]
        
        # 2. 保护尾部（最近 20K tokens）
        tail, tail_tokens = self._protect_tail(messages)
        
        # 3. 中间部分需要压缩
        middle = messages[len(head):len(messages)-len(tail)]
        
        # 4. 用辅助 LLM 总结中间部分
        summary = self._summarize_middle(middle)
        
        # 5. 组装：头部 + 摘要 + 尾部
        compressed = head + [{"role": "user", "content": summary}] + tail
        return compressed
    
    def _summarize_middle(self, middle: List[Dict]) -> str:
        """用辅助 LLM 总结中间部分"""
        prompt = f"请总结以下对话内容，保留关键信息:\n{json.dumps(middle)}"
        response = self.auxiliary_client.chat.completions.create(
            model=self.aux_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
```

### 3.4 辅助模型任务

**文件**: [`agent/auxiliary_client.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/agent/auxiliary_client.py)

```python
# agent/auxiliary_client.py — call_llm()

def call_llm(messages: List[Dict], model: str = None,
             provider: str = "auto", task_type: str = "text", **kwargs) -> str:
    """
    辅助 LLM 调用路由器
    
    解析顺序（auto 模式）：
    1. OpenRouter (OPENROUTER_API_KEY)
    2. Nous Portal (~/.hermes/auth.json)
    3. 自定义端点 (config.yaml)
    4. Codex OAuth
    5. 原生 Anthropic
    6. 直接 API 密钥提供商
    """
    client, resolved_model = get_text_auxiliary_client(
        task_type=task_type, provider=provider,
    )
    
    if not client:
        raise RuntimeError("No auxiliary LLM provider available")
    
    response = client.chat.completions.create(
        model=resolved_model, messages=messages, **kwargs,
    )
    return response.choices[0].message.content
```

### 3.5 重试与回退

**文件**: [`run_agent.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/run_agent.py)

```python
# run_agent.py — 错误处理与回退

def _run_with_failover(self, messages: List[Dict], tools: List[Dict]) -> dict:
    """
    带故障转移的 API 调用
    
    回退策略：
    1. 主模型失败 → 尝试备用模型
    2. 提供商限流 → 指数退避重试
    3. 上下文过长 → 触发压缩
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, tools=tools,
            )
            return response
            
        except RateLimitError as e:
            wait_time = min(2 ** retry_count * 5, 60)
            logger.warning(f"Rate limited, waiting {wait_time}s...")
            time.sleep(wait_time)
            retry_count += 1
            
        except ContextLengthError as e:
            messages = self.context_compressor.compress(messages)
            retry_count += 1
            
        except APIError as e:
            if self.fallback_model:
                self._switch_to_fallback()
                retry_count += 1
            else:
                raise
    
    raise RuntimeError("Max retries exceeded")
```

### 3.6 快速入门

```python
# 创建并运行 Agent
from run_agent import AIAgent

agent = AIAgent(model="anthropic/claude-opus-4.6", max_iterations=50, platform="cli")

result = agent.run_conversation(user_message="帮我写一个 Python 脚本")
print(result["final_response"])
```

---

## 4. 能力层 (Capability Layer)

> 工具注册、MCP 服务器、技能系统、持久化记忆。

### 4.1 工具注册系统

**文件**: [`tools/registry.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/registry.py)

```python
# tools/registry.py — ToolRegistry 类

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}
    
    def register(self, name: str, toolset: str, schema: dict,
                 handler: Callable, check_fn: Callable = None,
                 requires_env: list = None, **kwargs):
        """注册工具"""
        self._tools[name] = ToolEntry(
            name=name, toolset=toolset, schema=schema,
            handler=handler, check_fn=check_fn,
            requires_env=requires_env or [],
        )
    
    def get_definitions(self, tool_names: Set[str]) -> List[dict]:
        """获取工具定义（OpenAI 格式）"""
        result = []
        for name in sorted(tool_names):
            entry = self._tools.get(name)
            if not entry:
                continue
            if entry.check_fn and not entry.check_fn():
                continue
            result.append({"type": "function", "function": {**entry.schema, "name": entry.name}})
        return result
    
    def dispatch(self, name: str, args: dict, **kwargs) -> str:
        """执行工具"""
        entry = self._tools.get(name)
        if not entry:
            return json.dumps({"error": f"Tool '{name}' not found"})
        try:
            result = entry.handler(args, **kwargs)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

registry = ToolRegistry()
```

### 4.2 工具发现与调度

**文件**: [`model_tools.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/model_tools.py)

```python
# model_tools.py — 工具编排层

def _discover_tools():
    """导入所有工具模块触发注册"""
    _modules = [
        "tools.web_tools", "tools.terminal_tool", "tools.file_tools",
        "tools.browser_tool", "tools.mcp_tool",
    ]
    for module in _modules:
        try:
            importlib.import_module(module)
        except ImportError:
            logger.debug(f"Failed to import {module}")

def get_tool_definitions(enabled_toolsets: list = None,
                         disabled_toolsets: list = None,
                         quiet_mode: bool = False) -> list:
    """获取可用工具定义"""
    _discover_tools()
    tool_names = get_tool_names_for_toolsets(
        enabled=enabled_toolsets, disabled=disabled_toolsets,
    )
    return registry.get_definitions(tool_names)

def handle_function_call(function_name: str, function_args: str,
                         task_id: str = None, **kwargs) -> str:
    """处理工具调用"""
    try:
        args = json.loads(function_args)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid arguments"})
    return registry.dispatch(name=function_name, args=args, task_id=task_id, **kwargs)
```

### 4.3 MCP 协议支持

**文件**: [`tools/mcp_tool.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/mcp_tool.py)

```python
# tools/mcp_tool.py — MCP 客户端

class MCPClient:
    """MCP (Model Context Protocol) 客户端"""
    
    async def connect_stdio(self, command: str, args: List[str], env: Dict[str, str] = None):
        """通过 stdio 连接到 MCP 服务器"""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        params = StdioServerParameters(command=command, args=args, env=env)
        
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                self._register_tools(tools, session)
    
    def _register_tools(self, tools, session):
        """将 MCP 工具注册到 hermes 工具注册表"""
        for tool in tools:
            registry.register(
                name=tool.name, toolset="mcp", schema=tool.inputSchema,
                handler=lambda args, s=session, t=tool: self._call_mcp_tool(s, t, args),
            )
    
    async def _call_mcp_tool(self, session, tool, args):
        """调用 MCP 工具"""
        result = await session.call_tool(tool.name, arguments=args)
        return result.content
```

### 4.4 技能系统

**文件**: [`tools/skills_tool.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/skills_tool.py)

```python
# tools/skills_tool.py — 技能工具

def skill_manage(action: str, name: str = None, content: str = None) -> str:
    """
    技能管理工具
    动作：list / view / create / update / delete
    """
    skills_dir = get_skills_dir()
    
    if action == "list":
        skills = list(skills_dir.glob("*/SKILL.md"))
        return json.dumps({"skills": [s.parent.name for s in skills]})
    
    elif action == "view":
        skill_file = skills_dir / name / "SKILL.md"
        if not skill_file.exists():
            return json.dumps({"error": f"Skill '{name}' not found"})
        return json.dumps({"content": skill_file.read_text()})
    
    elif action == "create":
        skill_dir = skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content)
        return json.dumps({"success": True, "message": f"Skill '{name}' created"})
```

### 4.5 记忆系统

**文件**: [`agent/memory_manager.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/agent/memory_manager.py)

```python
# agent/memory_manager.py — MemoryManager 类

class MemoryManager:
    def __init__(self, memory_file: Path = None):
        self.memory_file = memory_file or get_hermes_home() / "MEMORY.md"
        self.user_file = get_hermes_home() / "USER.md"
        self._load()
    
    def save_memory(self, key: str, value: str):
        """保存记忆"""
        self.memories[key] = value
        self._persist()
    
    def get_memory(self, key: str) -> str:
        """获取记忆"""
        return self.memories.get(key, "")
    
    def search_memories(self, query: str) -> List[dict]:
        """搜索记忆"""
        results = []
        for key, value in self.memories.items():
            if query.lower() in value.lower():
                results.append({"key": key, "value": value})
        return results
    
    def format_for_system_prompt(self, section: str = "memory") -> str:
        """格式化为系统提示词"""
        if section == "memory":
            return self._format_memories()
        elif section == "user":
            return self._format_user_profile()
        return ""
```

### 4.6 快速入门

```python
# 使用工具
from model_tools import handle_function_call

result = handle_function_call(
    function_name="terminal",
    function_args=json.dumps({"command": "ls -la"}),
)
print(json.loads(result))

# 使用技能
from tools.skills_tool import skill_manage

skills = skill_manage(action="list")

skill_manage(action="create", name="python-debugging",
             content="# Python Debugging Skill\n\n...")

# 使用记忆
from agent.memory_manager import MemoryManager

memory = MemoryManager()
memory.save_memory("user_name", "Alice")
print(memory.get_memory("user_name"))
```

---

## 5. 执行层 (Execution Backends)

> 命令执行后端，包括本地、Docker、SSH、云沙箱等。

### 5.1 终端工具

**文件**: [`tools/terminal_tool.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/terminal_tool.py)

```python
# tools/terminal_tool.py — terminal_tool()

def terminal_tool(command: str, background: bool = False, timeout: int = None,
                  env_type: str = "local", **kwargs) -> str:
    """
    终端命令执行工具
    支持多种执行后端：local / docker / modal / ssh
    """
    # 1. 安全检查
    from tools.approval import check_dangerous_command
    approval = check_dangerous_command(command, env_type)
    if not approval["approved"]:
        return json.dumps({"error": "Command not approved"})
    
    # 2. 选择执行后端
    if env_type == "local":
        return _execute_local(command, timeout, background)
    elif env_type == "docker":
        return _execute_docker(command, timeout)
    elif env_type == "modal":
        return _execute_modal(command, timeout)
    elif env_type == "ssh":
        return _execute_ssh(command, timeout)

def _execute_local(command: str, timeout: int = None, background: bool = False) -> str:
    """本地执行"""
    import subprocess
    clean_env = _build_clean_env()
    
    try:
        if background:
            proc = subprocess.Popen(command, shell=True, env=clean_env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return json.dumps({"success": True, "pid": proc.pid,
                               "message": "Background process started"})
        else:
            proc = subprocess.run(command, shell=True, env=clean_env,
                                  capture_output=True, text=True, timeout=timeout or 60)
            return json.dumps({"success": proc.returncode == 0,
                               "stdout": proc.stdout, "stderr": proc.stderr,
                               "returncode": proc.returncode})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Command timed out"})
```

### 5.2 本地执行环境

**文件**: [`tools/environments/local.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/environments/local.py)

```python
# tools/environments/local.py — 本地环境

class LocalEnvironment(BaseEnvironment):
    """本地执行环境"""
    
    def execute(self, command: str, cwd: str = None,
                env: Dict[str, str] = None, timeout: int = 60) -> ExecutionResult:
        """执行命令"""
        clean_env = self._build_safe_env(env)
        
        proc = subprocess.run(
            command, shell=True, cwd=cwd or self.working_dir,
            env=clean_env, capture_output=True, text=True, timeout=timeout,
        )
        
        return ExecutionResult(
            success=proc.returncode == 0,
            stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode,
        )
    
    def _build_safe_env(self, extra_env: Dict[str, str] = None) -> Dict[str, str]:
        """构建安全的执行环境（过滤敏感变量）"""
        blocked_prefixes = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                           "OPENROUTER_API_KEY", "TELEGRAM_BOT_TOKEN", ...]
        
        safe_env = os.environ.copy()
        for key in list(safe_env.keys()):
            if any(key.startswith(prefix) for prefix in blocked_prefixes):
                del safe_env[key]
        
        if extra_env:
            safe_env.update(extra_env)
        return safe_env
```

### 5.3 Docker 执行环境

```python
# tools/environments/docker.py — Docker 环境

class DockerEnvironment(BaseEnvironment):
    """Docker 容器执行环境"""
    
    def execute(self, command: str, image: str = "python:3.11-slim",
                timeout: int = 120) -> ExecutionResult:
        """在 Docker 容器中执行命令"""
        import docker
        client = docker.from_env()
        
        container = client.containers.run(
            image=image, command=["bash", "-c", command],
            detach=True, remove=True,
        )
        
        try:
            exit_code = container.wait(timeout=timeout)
            logs = container.logs().decode()
            return ExecutionResult(success=exit_code == 0, stdout=logs, returncode=exit_code)
        finally:
            container.stop()
```

### 5.4 快速入门

```python
# 本地执行
from tools.terminal_tool import terminal_tool

result = terminal_tool(command="echo Hello World", env_type="local")
print(json.loads(result))

# Docker 执行
result = terminal_tool(command="python --version", env_type="docker")

# 后台执行
result = terminal_tool(command="python server.py", background=True)
```

---

## 6. 状态层 (Data, State & Persistence)

> 会话状态存储，包括 SQLite、JSONL 日志、用户配置。

### 6.1 SQLite 状态存储

**文件**: [`hermes_state.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/hermes_state.py)

```python
# hermes_state.py — SessionDB 类（详细）

class SessionDB:
    """SQLite 会话数据库"""
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY, source TEXT NOT NULL, model TEXT,
        started_at REAL, ended_at REAL, message_count INTEGER DEFAULT 0,
        input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0, ...
    );
    
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT REFERENCES sessions(id),
        role TEXT NOT NULL, content TEXT, tool_calls TEXT, timestamp REAL, ...
    );
    
    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
        content, content=messages, content_rowid=id
    );
    """
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or get_hermes_home() / "state.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()
    
    def create_session(self, session_id: str, **kwargs) -> str:
        """创建会话"""
        self.conn.execute(
            "INSERT OR IGNORE INTO sessions (id, source, model, started_at, message_count) VALUES (?, ?, ?, ?, 0)",
            (session_id, kwargs.get("source", "cli"), kwargs.get("model"), time.time()),
        )
        self.conn.commit()
        return session_id
    
    def append_message(self, session_id: str, **kwargs):
        """追加消息"""
        self.conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, kwargs["role"], kwargs["content"],
             json.dumps(kwargs.get("tool_calls", [])), time.time()),
        )
        self.conn.execute("UPDATE sessions SET message_count = message_count + 1 WHERE id = ?", (session_id,))
        self.conn.commit()
    
    def get_session(self, session_id: str) -> dict:
        """获取会话"""
        row = self.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        messages = self.conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,)
        ).fetchall()
        return {"session": dict(row), "messages": [dict(m) for m in messages]}
    
    def search_sessions(self, query: str, limit: int = 20) -> list:
        """全文搜索"""
        results = self.conn.execute(
            """SELECT s.id, s.title, m.content, rank
               FROM messages_fts
               JOIN messages m ON messages_fts.rowid = m.id
               JOIN sessions s ON m.session_id = s.id
               WHERE messages_fts MATCH ? ORDER BY rank LIMIT ?""",
            (query, limit),
        ).fetchall()
        return [dict(r) for r in results]
```

### 6.2 JSONL 日志

**文件**: [`run_agent.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/run_agent.py)

```python
# run_agent.py — 日志保存

def _save_session_log(self, messages: List[Dict]):
    """保存会话日志到 JSONL 文件"""
    log_dir = get_hermes_home() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{self.session_id}.jsonl"
    
    with open(log_file, "a", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
```

### 6.3 用户配置

**文件**: [`hermes_cli/config.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/hermes_cli/config.py)

```python
# hermes_cli/config.py — 配置管理

DEFAULT_CONFIG = {
    "model": {"default": "anthropic/claude-opus-4.6", "fallback": "openai/gpt-4o-mini"},
    "display": {"skin": "default", "tool_progress_command": True},
    "tools": {"enabled_toolsets": ["core", "web", "file"], "disabled_toolsets": []},
    "approvals": {"mode": "manual", "timeout": 60},
    "memory": {"enabled": True, "cross_session_search": True},
}

def load_config() -> dict:
    """加载用户配置"""
    config_path = get_hermes_home() / "config.yaml"
    if not config_path.exists():
        return DEFAULT_CONFIG
    with open(config_path) as f:
        user_config = yaml.safe_load(f) or {}
    return deep_merge(DEFAULT_CONFIG, user_config)

def save_config(config: dict):
    """保存配置"""
    config_path = get_hermes_home() / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
```

### 6.4 快速入门

```python
# 使用 SQLite 存储
from hermes_state import SessionDB

db = SessionDB()
session_id = db.create_session(source="cli", model="anthropic/claude-opus-4.6")
db.append_message(session_id=session_id, role="user", content="Hello!")
results = db.search_sessions("python")

# 加载配置
from hermes_cli.config import load_config, save_config

config = load_config()
config["model"]["default"] = "openai/gpt-4o"
save_config(config)
```

---

## 7. 模型层 (Model / Provider Layer)

> 模型提供商解析，支持 OpenAI、Anthropic、Codex、自定义提供商。

### 7.1 模型元数据

**文件**: [`agent/models_dev.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/agent/models_dev.py)

```python
# agent/models_dev.py — 模型元数据

@dataclass
class ModelInfo:
    """模型元数据"""
    id: str                       # 模型 ID
    name: str                     # 模型名称
    provider_id: str              # 提供商 ID
    reasoning: bool = False       # 支持推理
    tool_call: bool = False       # 支持工具调用
    attachment: bool = False      # 支持附件（视觉）
    context_window: int = 0       # 上下文窗口大小
    max_output: int = 0           # 最大输出长度
    cost_input: float = 0.0       # 输入成本（每百万 token）
    cost_output: float = 0.0      # 输出成本
    
    def supports_vision(self) -> bool:
        return self.attachment or "image" in self.input_modalities

def get_model_info(model_id: str) -> ModelInfo:
    """获取模型信息"""
    # 1. 检查内存缓存
    if model_id in _models_dev_cache:
        return _models_dev_cache[model_id]
    
    # 2. 检查磁盘缓存
    cache_file = get_hermes_home() / "models_dev_cache.json"
    if cache_file.exists():
        with open(cache_file) as f:
            cache = json.load(f)
            if model_id in cache:
                return ModelInfo(**cache[model_id])
    
    # 3. 从网络获取
    response = requests.get(MODELS_DEV_URL)
    all_models = response.json()
    model_data = all_models.get(model_id)
    if model_data:
        model_info = ModelInfo(**model_data)
        _models_dev_cache[model_id] = model_info
        _save_cache_to_disk(all_models)
        return model_info
    return None
```

### 7.2 提供商解析

**文件**: [`run_agent.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/run_agent.py)

```python
# run_agent.py — 提供商解析

class AIAgent:
    def _resolve_provider(self, model: str):
        """解析模型字符串获取提供商信息"""
        if "/" in model:
            provider, model_name = model.split("/", 1)
        else:
            provider = "openrouter"
            model_name = model
        
        provider_config = self._get_provider_config(provider)
        return {
            "provider": provider, "model": model_name,
            "base_url": provider_config.base_url,
            "api_key": provider_config.api_key,
        }
    
    def _get_provider_config(self, provider: str) -> ProviderConfig:
        """获取提供商配置"""
        if provider == "openai":
            return ProviderConfig(base_url="https://api.openai.com/v1",
                                  api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "anthropic":
            return ProviderConfig(base_url="https://api.anthropic.com/v1",
                                  api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif provider == "openrouter":
            return ProviderConfig(base_url="https://openrouter.ai/api/v1",
                                  api_key=os.getenv("OPENROUTER_API_KEY"))
```

### 7.3 客户端初始化

**文件**: [`run_agent.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/run_agent.py)

```python
# run_agent.py — OpenAI 客户端

def _create_openai_client(self, client_kwargs: dict) -> OpenAI:
    """创建 OpenAI 客户端"""
    if self.provider == "copilot-acp":
        from agent.copilot_acp_client import CopilotACPClient
        return CopilotACPClient(**client_kwargs)
    return OpenAI(**client_kwargs)

def _ensure_primary_openai_client(self, reason: str) -> OpenAI:
    """确保主客户端可用"""
    with self._openai_client_lock():
        client = getattr(self, "client", None)
        if client is not None and not self._is_openai_client_closed(client):
            return client
        
        logger.warning(f"Recreating OpenAI client ({reason})")
        new_client = self._create_openai_client(self._client_kwargs)
        self.client = new_client
        return new_client
```

### 7.4 快速入门

```python
# 使用不同提供商
from run_agent import AIAgent

agent_openai = AIAgent(model="openai/gpt-4o")
agent_anthropic = AIAgent(model="anthropic/claude-opus-4.6")
agent_openrouter = AIAgent(model="anthropic/claude-3.5-sonnet")

# 获取模型信息
from agent.models_dev import get_model_info

info = get_model_info("anthropic/claude-opus-4.6")
print(f"Context: {info.context_window}")
print(f"Supports tools: {info.tool_call}")
```

---

## 8. 安全层 (Security Boundaries)

> 安全边界，包括认证、上下文扫描、审批流、沙箱隔离、MCP 过滤、记忆持久化。

### 8.1 认证系统

**文件**: [`gateway/auth.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/gateway/auth.py)

```python
# gateway/auth.py — 用户认证

class AuthManager:
    def __init__(self):
        self.allowed_users = self._load_allowed_users()
    
    def _load_allowed_users(self) -> Set[str]:
        """加载允许的用户列表"""
        config = load_config()
        return set(config.get("gateway", {}).get("allowed_users", []))
    
    def is_user_allowed(self, user_id: str) -> bool:
        """检查用户是否被允许"""
        if not self.allowed_users:
            return True
        return user_id in self.allowed_users
    
    def verify_dm(self, user_id: str, chat_type: str) -> bool:
        """验证私聊消息"""
        if chat_type != "dm":
            return True
        return self.is_user_allowed(user_id)
```

### 8.2 上下文注入扫描

**文件**: [`agent/prompt_builder.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/agent/prompt_builder.py)

```python
# agent/prompt_builder.py — 提示词注入检测

_CONTEXT_THREAT_PATTERNS = [
    (r'ignore\s+(previous|all|above)\s+instructions', "prompt_injection"),
    (r'do\s+not\s+tell\s+the\s+user', "deception_hide"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    (r'act\s+as\s+(if|though)\s+you\s+have\s+no\s+restrictions', "bypass_restrictions"),
]

def _scan_context_content(content: str, filename: str) -> str:
    """扫描上下文文件中的注入攻击"""
    findings = []
    for pattern, threat_id in _CONTEXT_THREAT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(threat_id)
    
    if findings:
        logger.warning(f"Context file {filename} blocked: {', '.join(findings)}")
        return f"[BLOCKED: {filename} contained potential prompt injection]"
    return content
```

### 8.3 危险命令审批

**文件**: [`tools/approval.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/approval.py)

```python
# tools/approval.py — 危险命令检测

DANGEROUS_PATTERNS = [
    (r'\brm\s+(-[^\s]*\s+)*/', "delete in root path"),
    (r'\brm\s+-[^\s]*r', "recursive delete"),
    (r'\bchmod\s+(-[^\s]*\s+)*(777|666)', "world-writable permissions"),
    (r'\bmkfs\b', "format filesystem"),
    (r'\bdd\s+.*if=', "disk copy"),
    (r'\bDROP\s+(TABLE|DATABASE)\b', "SQL DROP"),
    (r'\b(curl|wget)\b.*\|\s*(ba)?sh\b', "pipe remote content to shell"),
]

def detect_dangerous_command(command: str) -> tuple:
    """检测危险命令"""
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, pattern, description
    return False, None, None

def check_dangerous_command(command: str, env_type: str, approval_callback=None) -> dict:
    """检查危险命令并处理审批"""
    # 1. 容器环境自动放行
    if env_type in ("docker", "modal", "singularity"):
        return {"approved": True}
    
    # 2. YOLO 模式自动放行
    if os.getenv("HERMES_YOLO_MODE"):
        return {"approved": True}
    
    # 3. 检测危险命令
    is_dangerous, pattern, description = detect_dangerous_command(command)
    if not is_dangerous:
        return {"approved": True}
    
    # 4. 检查是否已审批
    session_key = get_current_session_key()
    if is_approved(session_key, pattern):
        return {"approved": True}
    
    # 5. 请求审批
    if approval_callback:
        return approval_callback(command, pattern, description)
    
    return {"approved": False, "message": "Command requires approval"}
```

### 8.4 沙箱隔离

**文件**: [`tools/environments/docker.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/environments/docker.py)

```python
# tools/environments/docker.py — Docker 沙箱

class DockerSandbox(BaseEnvironment):
    """Docker 沙箱隔离"""
    
    def __init__(self, image: str = "python:3.11-slim"):
        self.image = image
        self.network_disabled = True
        self.read_only = True
    
    def execute(self, command: str, **kwargs) -> ExecutionResult:
        """在隔离环境中执行"""
        import docker
        client = docker.from_env()
        
        container = client.containers.run(
            image=self.image, command=["bash", "-c", command],
            detach=True, network_disabled=self.network_disabled,
            read_only=self.read_only,
            tmpfs={"/tmp": "rw,noexec,nosuid,size=100m"},
            mem_limit="512m", cpu_quota=50000, pids_limit=100,
        )
        
        try:
            exit_code = container.wait(timeout=120)
            logs = container.logs().decode()
            return ExecutionResult(success=exit_code == 0, stdout=logs, returncode=exit_code)
        finally:
            container.remove(force=True)
```

### 8.5 MCP 凭证过滤

**文件**: [`tools/mcp_tool.py`](file:///home/meizu/Documents/my_agent_project/hermes-agent/tools/mcp_tool.py)

```python
# tools/mcp_tool.py — MCP 凭证过滤

def _filter_env_for_stdio(env: Dict[str, str]) -> Dict[str, str]:
    """过滤传递给 MCP 子进程的环境变量"""
    blocked_patterns = ["API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"]
    safe_env = {}
    for key, value in env.items():
        if not any(pattern in key.upper() for pattern in blocked_patterns):
            safe_env[key] = value
    return safe_env

def _strip_credentials_from_error(error_msg: str) -> str:
    """从错误消息中移除凭证"""
    error_msg = re.sub(r'sk-[A-Za-z0-9]{32,}', '[REDACTED]', error_msg)
    error_msg = re.sub(r'ghp_[A-Za-z0-9]{32,}', '[REDACTED]', error_msg)
    error_msg = re.sub(r'tgbot[A-Za-z0-9:]{20,}', '[REDACTED]', error_msg)
    return error_msg
```

### 8.6 快速入门

```python
# 认证检查
from gateway.auth import AuthManager

auth = AuthManager()
if not auth.is_user_allowed("user123"):
    print("User not allowed")

# 命令安全检查
from tools.approval import check_dangerous_command

result = check_dangerous_command("ls -la", "local")
print(result)  # {"approved": True}

result = check_dangerous_command("rm -rf /", "local")
print(result)  # {"approved": False, ...}

# 扫描上下文文件
from agent.prompt_builder import _scan_context_content

safe_content = _scan_context_content("Normal content", "AGENTS.md")
blocked_content = _scan_context_content("Ignore all previous instructions", "AGENTS.md")
print(blocked_content)  # [BLOCKED: ...]
```

---

## 📊 架构层次关系图

```
┌─────────────────────────────────────────────────────────┐
│                     入口层 (Entry Layer)                  │
│  CLI / TUI / Telegram / Discord / Slack / Cron / ACP    │
│  入口: hermes_cli/main.py, gateway/run.py               │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              会话与路由层 (Session & Routing)              │
│  SessionRunner / SessionStore / Command Guards          │
│  入口: gateway/session.py, hermes_state.py              │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│               Agent Runtime Core                         │
│  AIAgent (主循环) / Prompt / Compress / Aux / Fallback  │
│  入口: run_agent.py (AIAgent.run_conversation)          │
└──────────┬─────────────┬─────────────┬──────────────────┘
           │             │             │
     ┌─────▼──────┐ ┌───▼──────┐ ┌───▼──────────┐
     │  能力层      │ │ 执行层    │ │  安全层       │
     │ Tools/MCP  │ │ TERM/WEB │ │ AUTH/SCAN   │
     │ Skills/Mem │ │ FILES    │ │ APPROVAL/   │
     │            │ │          │ │ SANDBOX     │
     └──────────── ──────────┘ ─────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              状态层 (Data, State & Persistence)            │
│  SQLite (state.db) / JSONL / Config / Profile           │
│  入口: hermes_state.py, hermes_cli/config.py            │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              模型层 (Model / Provider Layer)               │
│  OpenAI / Anthropic / Codex / OpenRouter / Custom       │
│  入口: run_agent.py (OpenAI client), agent/models_dev.py│
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 完整快速入门流程

### Step 1: 安装与配置

```bash
pip install -e ".[all]"
hermes setup
hermes login openrouter
```

### Step 2: CLI 模式

```bash
hermes chat -q "Hello, how are you?"
hermes
> /model anthropic/claude-opus-4.6
> Help me write a Python script
```

### Step 3: Gateway 模式

```bash
hermes gateway telegram
hermes gateway discord
hermes gateway start
```

### Step 4: 使用工具

```python
from run_agent import AIAgent

agent = AIAgent(model="anthropic/claude-opus-4.6")
result = agent.run_conversation(user_message="帮我创建一个 Python 文件并运行它")
```

### Step 5: 使用技能

```bash
/skills list
/skills install github-auth
/skills inspect github-auth
```

### Step 6: 使用记忆

```python
from agent.memory_manager import MemoryManager

memory = MemoryManager()
memory.save_memory("user_name", "Alice")
print(memory.get_memory("user_name"))
```

### Step 7: 会话管理

```bash
/sessions list
/sessions search "python project"
hermes --continue "session_id"
```

---

## 📚 核心文件索引

| 层级 | 文件 | 说明 |
|------|------|------|
| 入口层 | `hermes_cli/main.py` | CLI 主入口路由 |
| 入口层 | `cli.py` | HermesCLI 类，交互式 REPL |
| 入口层 | `gateway/run.py` | Gateway 启动器 |
| 会话层 | `gateway/session.py` | 会话来源与路由 |
| 会话层 | `hermes_state.py` | SQLite 会话存储 |
| 会话层 | `hermes_cli/commands.py` | 命令注册与守卫 |
| Runtime | `run_agent.py` | AIAgent 主循环 |
| Runtime | `agent/prompt_builder.py` | 提示词组装 |
| Runtime | `agent/context_compressor.py` | 上下文压缩 |
| Runtime | `agent/auxiliary_client.py` | 辅助 LLM 路由 |
| 能力层 | `tools/registry.py` | 工具注册表 |
| 能力层 | `model_tools.py` | 工具发现与调度 |
| 能力层 | `tools/mcp_tool.py` | MCP 客户端 |
| 能力层 | `tools/skills_tool.py` | 技能管理 |
| 执行层 | `tools/terminal_tool.py` | 终端命令执行 |
| 执行层 | `tools/environments/local.py` | 本地执行环境 |
| 执行层 | `tools/environments/docker.py` | Docker 沙箱 |
| 状态层 | `hermes_state.py` | SQLite 数据库 |
| 状态层 | `hermes_cli/config.py` | 配置管理 |
| 模型层 | `agent/models_dev.py` | 模型元数据 |
| 模型层 | `run_agent.py` | OpenAI 客户端 |
| 安全层 | `gateway/auth.py` | 用户认证 |
| 安全层 | `agent/prompt_builder.py` | 提示词注入检测 |
| 安全层 | `tools/approval.py` | 危险命令审批 |
| 安全层 | `tools/environments/docker.py` | 沙箱隔离 |

---

**文档版本**: 1.0
**最后更新**: 2026-04-17

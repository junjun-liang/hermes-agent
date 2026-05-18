# Hermes Agent — 开发指南

面向在 hermes-agent 代码库上工作的 AI 编码助手和开发者的说明文档。

## 开发环境

```bash
source venv/bin/activate  # 运行 Python 前务必激活虚拟环境
```

## 项目结构

```
hermes-agent/
├── run_agent.py          # AIAgent 类 — 核心对话循环
├── model_tools.py        # 工具编排，_discover_tools()，handle_function_call()
├── toolsets.py           # 工具集定义，_HERMES_CORE_TOOLS 列表
├── cli.py                # HermesCLI 类 — 交互式 CLI 编排器
├── hermes_state.py       # SessionDB — SQLite 会话存储（FTS5 搜索）
├── agent/                # Agent 内部模块
│   ├── prompt_builder.py     # 系统提示词组装
│   ├── context_compressor.py # 自动上下文压缩
│   ├── prompt_caching.py     # Anthropic 提示词缓存
│   ├── auxiliary_client.py   # 辅助 LLM 客户端（视觉、摘要）
│   ├── model_metadata.py     # 模型上下文窗口、token 估算
│   ├── models_dev.py         # models.dev 注册表集成（感知提供商的上下文）
│   ├── display.py            # KawaiiSpinner、工具预览格式化
│   ├── skill_commands.py     # 技能斜杠命令（CLI/gateway 共享）
│   └── trajectory.py         # 轨迹保存辅助函数
├── hermes_cli/           # CLI 子命令和设置向导
│   ├── main.py           # 入口点 — 所有 `hermes` 子命令
│   ├── config.py         # DEFAULT_CONFIG、OPTIONAL_ENV_VARS、配置迁移
│   ├── commands.py       # 斜杠命令定义 + SlashCommandCompleter
│   ├── callbacks.py      # 终端回调（澄清、sudo、审批）
│   ├── setup.py          # 交互式设置向导
│   ├── skin_engine.py    # 皮肤/主题引擎 — CLI 视觉定制
│   ├── skills_config.py  # `hermes skills` — 按平台启用/禁用技能
│   ├── tools_config.py   # `hermes tools` — 按平台启用/禁用工具
│   ├── skills_hub.py     # `/skills` 斜杠命令（搜索、浏览、安装）
│   ├── models.py         # 模型目录、提供商模型列表
│   ├── model_switch.py   # 共享 /model 切换管道（CLI + gateway）
│   └── auth.py           # 提供商凭证解析
├── tools/                # 工具实现（每个工具一个文件）
│   ├── registry.py       # 中央工具注册表（schema、处理器、调度）
│   ├── approval.py       # 危险命令检测
│   ├── terminal_tool.py  # 终端编排
│   ├── process_registry.py # 后台进程管理
│   ├── file_tools.py     # 文件读写/搜索/补丁
│   ├── web_tools.py      # 网络搜索/提取（Parallel + Firecrawl）
│   ├── browser_tool.py   # Browserbase 浏览器自动化
│   ├── code_execution_tool.py # execute_code 沙箱
│   ├── delegate_tool.py  # 子 Agent 委派
│   ├── mcp_tool.py       # MCP 客户端（约 1050 行）
│   └── environments/     # 终端后端（local、docker、ssh、modal、daytona、singularity）
├── gateway/              # 消息平台网关
│   ├── run.py            # 主循环、斜杠命令、消息调度
│   ├── session.py        # SessionStore — 对话持久化
│   └── platforms/        # 适配器：telegram、discord、slack、whatsapp、homeassistant、signal
├── acp_adapter/          # ACP 服务器（VS Code / Zed / JetBrains 集成）
├── cron/                 # 调度器（jobs.py、scheduler.py）
├── environments/         # RL 训练环境（Atropos）
├── tests/                # Pytest 测试套件（约 3000 个测试）
└── batch_runner.py       # 并行批处理
```

**用户配置：** `~/.hermes/config.yaml`（设置），`~/.hermes/.env`（API 密钥）

## 文件依赖链

```
tools/registry.py  （无依赖 — 被所有工具文件导入）
       ↑
tools/*.py  （每个文件在导入时调用 registry.register()）
       ↑
model_tools.py  （导入 tools/registry + 触发工具发现）
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

---

## AIAgent 类（run_agent.py）

```python
class AIAgent:
    def __init__(self,
        model: str = "anthropic/claude-opus-4.6",
        max_iterations: int = 90,
        enabled_toolsets: list = None,
        disabled_toolsets: list = None,
        quiet_mode: bool = False,
        save_trajectories: bool = False,
        platform: str = None,           # "cli"、"telegram" 等
        session_id: str = None,
        skip_context_files: bool = False,
        skip_memory: bool = False,
        # ... 以及 provider、api_mode、callbacks、routing 参数
    ): ...

    def chat(self, message: str) -> str:
        """简单接口 — 返回最终响应字符串。"""

    def run_conversation(self, user_message: str, system_message: str = None,
                         conversation_history: list = None, task_id: str = None) -> dict:
        """完整接口 — 返回包含 final_response + messages 的字典。"""
```

### Agent 循环

核心循环位于 `run_conversation()` — 完全同步执行：

```python
while api_call_count < self.max_iterations and self.iteration_budget.remaining > 0:
    response = client.chat.completions.create(model=model, messages=messages, tools=tool_schemas)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call.name, tool_call.args, task_id)
            messages.append(tool_result_message(result))
        api_call_count += 1
    else:
        return response.content
```

消息遵循 OpenAI 格式：`{"role": "system/user/assistant/tool", ...}`。推理内容存储在 `assistant_msg["reasoning"]` 中。

---

## CLI 架构（cli.py）

- **Rich** 用于横幅/面板，**prompt_toolkit** 用于带自动补全的输入
- **KawaiiSpinner**（`agent/display.py`）— API 调用期间的动画表情，`┊` 活动流用于工具结果
- cli.py 中的 `load_cli_config()` 合并硬编码默认值 + 用户配置 YAML
- **皮肤引擎**（`hermes_cli/skin_engine.py`）— 数据驱动的 CLI 主题；启动时从 `display.skin` 配置键初始化；皮肤可定制横幅颜色、旋转器表情/动词/翅膀、工具前缀、响应框、品牌文本
- `process_command()` 是 `HermesCLI` 上的方法 — 通过中央注册表的 `resolve_command()` 解析的规范命令名进行调度
- 技能斜杠命令：`agent/skill_commands.py` 扫描 `~/.hermes/skills/`，注入为**用户消息**（而非系统提示）以保持提示词缓存有效

### 斜杠命令注册表（`hermes_cli/commands.py`）

所有斜杠命令都在中央 `COMMAND_REGISTRY` 的 `CommandDef` 对象列表中定义。每个下游消费者自动从此注册表派生：

- **CLI** — `process_command()` 通过 `resolve_command()` 解析别名，按规范名调度
- **Gateway** — `GATEWAY_KNOWN_COMMANDS` frozenset 用于钩子发射，`resolve_command()` 用于调度
- **Gateway 帮助** — `gateway_help_lines()` 生成 `/help` 输出
- **Telegram** — `telegram_bot_commands()` 生成 BotCommand 菜单
- **Slack** — `slack_subcommand_map()` 生成 `/hermes` 子命令路由
- **自动补全** — `COMMANDS` 扁平字典供给 `SlashCommandCompleter`
- **CLI 帮助** — `COMMANDS_BY_CATEGORY` 字典供给 `show_help()`

### 添加斜杠命令

1. 在 `hermes_cli/commands.py` 的 `COMMAND_REGISTRY` 中添加 `CommandDef` 条目：
```python
CommandDef("mycommand", "功能描述", "Session",
           aliases=("mc",), args_hint="[arg]"),
```
2. 在 cli.py 的 `HermesCLI.process_command()` 中添加处理器：
```python
elif canonical == "mycommand":
    self._handle_mycommand(cmd_original)
```
3. 如果该命令在 gateway 中可用，在 `gateway/run.py` 中添加处理器：
```python
if canonical == "mycommand":
    return await self._handle_mycommand(event)
```
4. 对于持久化设置，在 cli.py 中使用 `save_config_value()`

**CommandDef 字段：**
- `name` — 不带斜杠的规范名（如 `"background"`）
- `description` — 人类可读的描述
- `category` — `"Session"`、`"Configuration"`、`"Tools & Skills"`、`"Info"`、`"Exit"` 之一
- `aliases` — 替代名称元组（如 `("bg",)`）
- `args_hint` — 帮助中显示的参数占位符（如 `"<prompt>"`、`"[name]"`）
- `cli_only` — 仅在交互式 CLI 中可用
- `gateway_only` — 仅在消息平台中可用
- `gateway_config_gate` — 配置点路径（如 `"display.tool_progress_command"`）；当设置在 `cli_only` 命令上时，如果配置值为真，则该命令在 gateway 中可用。`GATEWAY_KNOWN_COMMANDS` 始终包含配置门控命令以便 gateway 可以调度它们；帮助/菜单仅在门控打开时显示它们。

**添加别名**只需将其添加到现有 `CommandDef` 的 `aliases` 元组中。无需修改其他文件 — 调度、帮助文本、Telegram 菜单、Slack 映射和自动补全都会自动更新。

---

## 添加新工具

需要修改 **3 个文件**：

**1. 创建 `tools/your_tool.py`：**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. 在 `model_tools.py`** 的 `_discover_tools()` 列表中添加导入。

**3. 添加到 `toolsets.py`** — `_HERMES_CORE_TOOLS`（所有平台）或新工具集。

注册表处理 schema 收集、调度、可用性检查和错误包装。所有处理器**必须**返回 JSON 字符串。

**工具 schema 中的路径引用**：如果 schema 描述中提及文件路径（如默认输出目录），请使用 `display_hermes_home()` 使其支持 profile。schema 在导入时生成，此时 `_apply_profile_override()` 已设置 `HERMES_HOME`。

**状态文件**：如果工具存储持久状态（缓存、日志、检查点），请使用 `get_hermes_home()` 作为基础目录 — 切勿使用 `Path.home() / ".hermes"`。这确保每个 profile 都有独立的状态。

**Agent 级工具**（todo、memory）：在 `handle_function_call()` 之前被 `run_agent.py` 拦截。参考 `todo_tool.py` 的模式。

---

## 添加配置

### config.yaml 选项：
1. 在 `hermes_cli/config.py` 的 `DEFAULT_CONFIG` 中添加
2. 提升 `_config_version`（当前为 5）以触发已有用户的配置迁移

### .env 变量：
1. 在 `hermes_cli/config.py` 的 `OPTIONAL_ENV_VARS` 中添加并附带元数据：
```python
"NEW_API_KEY": {
    "description": "用途说明",
    "prompt": "显示名称",
    "url": "https://...",
    "password": True,
    "category": "tool",  # provider, tool, messaging, setting
},
```

### 配置加载器（两套独立系统）：

| 加载器 | 使用者 | 位置 |
|--------|---------|----------|
| `load_cli_config()` | CLI 模式 | `cli.py` |
| `load_config()` | `hermes tools`、`hermes setup` | `hermes_cli/config.py` |
| 直接 YAML 加载 | Gateway | `gateway/run.py` |

---

## 皮肤/主题系统

皮肤引擎（`hermes_cli/skin_engine.py`）提供数据驱动的 CLI 视觉定制。皮肤是**纯数据** — 添加新皮肤无需修改代码。

### 架构

```
hermes_cli/skin_engine.py    # SkinConfig 数据类、内置皮肤、YAML 加载器
~/.hermes/skins/*.yaml       # 用户安装的自定义皮肤（即放即用）
```

- `init_skin_from_config()` — CLI 启动时调用，从配置读取 `display.skin`
- `get_active_skin()` — 返回当前皮肤的缓存 `SkinConfig`
- `set_active_skin(name)` — 运行时切换皮肤（`/skin` 命令使用）
- `load_skin(name)` — 先加载用户皮肤，再加载内置皮肤，最后回退到默认皮肤
- 缺失的皮肤值会自动从 `default` 皮肤继承

### 皮肤可定制的内容

| 元素 | 皮肤键 | 使用者 |
|---------|----------|---------|
| 横幅面板边框 | `colors.banner_border` | `banner.py` |
| 横幅面板标题 | `colors.banner_title` | `banner.py` |
| 横幅区块标题 | `colors.banner_accent` | `banner.py` |
| 横幅淡化文本 | `colors.banner_dim` | `banner.py` |
| 横幅正文文本 | `colors.banner_text` | `banner.py` |
| 响应框边框 | `colors.response_border` | `cli.py` |
| 旋转器表情（等待） | `spinner.waiting_faces` | `display.py` |
| 旋转器表情（思考） | `spinner.thinking_faces` | `display.py` |
| 旋转器动词 | `spinner.thinking_verbs` | `display.py` |
| 旋转器翅膀（可选） | `spinner.wings` | `display.py` |
| 工具输出前缀 | `tool_prefix` | `display.py` |
| 每个工具的 emoji | `tool_emojis` | `display.py` → `get_tool_emoji()` |
| Agent 名称 | `branding.agent_name` | `banner.py`、`cli.py` |
| 欢迎消息 | `branding.welcome` | `cli.py` |
| 响应框标签 | `branding.response_label` | `cli.py` |
| 提示符号 | `branding.prompt_symbol` | `cli.py` |

### 内置皮肤

- `default` — 经典 Hermes 金色/可爱风格（当前外观）
- `ares` — 猩红/青铜战神主题，带自定义旋转器翅膀
- `mono` — 简洁的灰度单色主题
- `slate` — 冷蓝色开发者导向主题

### 添加内置皮肤

在 `hermes_cli/skin_engine.py` 的 `_BUILTIN_SKINS` 字典中添加：

```python
"mytheme": {
    "name": "mytheme",
    "description": "简短描述",
    "colors": { ... },
    "spinner": { ... },
    "branding": { ... },
    "tool_prefix": "┊",
},
```

### 用户皮肤（YAML）

用户创建 `~/.hermes/skins/<名称>.yaml`：

```yaml
name: cyberpunk
description: 霓虹浸染的终端主题

colors:
  banner_border: "#FF00FF"
  banner_title: "#00FFFF"
  banner_accent: "#FF1493"

spinner:
  thinking_verbs: ["接入中", "解密中", "上传中"]
  wings:
    - ["⟨⚡", "⚡⟩"]

branding:
  agent_name: "Cyber Agent"
  response_label: " ⚡ Cyber "

tool_prefix: "▏"
```

通过 `/skin cyberpunk` 或 config.yaml 中的 `display.skin: cyberpunk` 激活。

---

## 重要策略

### 提示词缓存绝不能被破坏

Hermes-Agent 确保缓存在整个对话期间保持有效。**不要实施会破坏缓存的更改：**
- 在对话中途修改历史上下文
- 在对话中途更改工具集
- 在对话中途重新加载记忆或重建系统提示词

破坏缓存会强制大幅提高成本。我们更改上下文的唯一时机是在上下文压缩期间。

### 工作目录行为
- **CLI**：使用当前目录（`.` → `os.getcwd()`）
- **消息平台**：使用 `MESSAGING_CWD` 环境变量（默认：主目录）

### 后台进程通知（Gateway）

当使用 `terminal(background=true, notify_on_complete=true)` 时，gateway 运行一个监视器来检测进程完成并触发新的 Agent 回合。通过 config.yaml 中的 `display.background_process_notifications`（或 `HERMES_BACKGROUND_NOTIFICATIONS` 环境变量）控制后台进程消息的详细程度：

- `all` — 运行中输出更新 + 最终消息（默认）
- `result` — 仅最终完成消息
- `error` — 仅在退出码 != 0 时输出最终消息
- `off` — 完全不输出监视器消息

---

## Profiles：多实例支持

Hermes 支持 **profiles** — 多个完全隔离的实例，每个实例拥有自己的 `HERMES_HOME` 目录（配置、API 密钥、记忆、会话、技能、gateway 等）。

核心机制：`hermes_cli/main.py` 中的 `_apply_profile_override()` 在任何模块导入之前设置 `HERMES_HOME`。所有 119+ 处对 `get_hermes_home()` 的引用自动作用域到当前激活的 profile。

### Profile 安全编码规则

1. **所有 HERMES_HOME 路径使用 `get_hermes_home()`。** 从 `hermes_constants` 导入。
   在读取/写入状态的代码中，**切勿**硬编码 `~/.hermes` 或 `Path.home() / ".hermes"`。
   ```python
   # 正确
   from hermes_constants import get_hermes_home
   config_path = get_hermes_home() / "config.yaml"

   # 错误 — 会破坏 profiles
   config_path = Path.home() / ".hermes" / "config.yaml"
   ```

2. **面向用户的消息使用 `display_hermes_home()`。** 从 `hermes_constants` 导入。
   默认 profile 返回 `~/.hermes`，其他 profile 返回 `~/.hermes/profiles/<名称>`。
   ```python
   # 正确
   from hermes_constants import display_hermes_home
   print(f"配置已保存到 {display_hermes_home()}/config.yaml")

   # 错误 — 对 profiles 显示错误路径
   print("配置已保存到 ~/.hermes/config.yaml")
   ```

3. **模块级常量没问题** — 它们在导入时缓存 `get_hermes_home()`，
   此时 `_apply_profile_override()` 已经设置了环境变量。直接使用 `get_hermes_home()`，
   而不是 `Path.home() / ".hermes"`。

4. **模拟 `Path.home()` 的测试也必须设置 `HERMES_HOME`** — 因为代码现在使用
   `get_hermes_home()`（读取环境变量），而不是 `Path.home() / ".hermes"`：
   ```python
   with patch.object(Path, "home", return_value=tmp_path), \
        patch.dict(os.environ, {"HERMES_HOME": str(tmp_path / ".hermes")}):
       ...
   ```

5. **Gateway 平台适配器应使用令牌锁** — 如果适配器使用唯一凭证
   （机器人令牌、API 密钥）连接，在 `connect()`/`start()` 方法中调用
   `gateway.status` 的 `acquire_scoped_lock()`，在 `disconnect()`/`stop()` 中调用
   `release_scoped_lock()`。这防止两个 profile 使用相同的凭证。
   参考 `gateway/platforms/telegram.py` 的标准模式。

6. **Profile 操作以 HOME 为锚点，而非 HERMES_HOME** — `_get_profiles_root()`
   返回 `Path.home() / ".hermes" / "profiles"`，**不是** `get_hermes_home() / "profiles"`。
   这是有意设计的 — 它让 `hermes -p coder profile list` 无论哪个 profile 激活都能看到所有 profile。

## 已知陷阱

### 不要硬编码 `~/.hermes` 路径
代码路径使用 `hermes_constants` 中的 `get_hermes_home()`。面向用户的打印/日志消息使用 `display_hermes_home()`。硬编码 `~/.hermes` 会破坏 profiles — 每个 profile 都有自己的 `HERMES_HOME` 目录。这是 PR #3575 中修复的 5 个 bug 的根源。

### 不要使用 `simple_term_menu` 做交互式菜单
在 tmux/iTerm2 中存在渲染 bug — 滚动时出现重影。改用 `curses`（标准库）。参考 `hermes_cli/tools_config.py` 的模式。

### 不要在旋转器/显示代码中使用 `\033[K`（ANSI 清除到行尾）
在 `prompt_toolkit` 的 `patch_stdout` 下会泄漏为字面量 `?[K` 文本。使用空格填充：`f"\r{line}{' ' * pad}"`。

### `_last_resolved_tool_names` 是 `model_tools.py` 中的进程全局变量
`delegate_tool.py` 中的 `_run_single_child()` 在子 Agent 执行期间保存和恢复此全局变量。如果你添加读取此全局变量的新代码，请注意它在子 Agent 运行期间可能暂时过期。

### 不要在 schema 描述中硬编码跨工具引用
工具 schema 描述中不得按名称提及来自其他工具集的工具（例如 `browser_navigate` 说"优先使用 web_search"）。那些工具可能不可用（缺少 API 密钥、禁用的工具集），导致模型幻觉调用不存在的工具。如果需要跨引用，在 `model_tools.py` 的 `get_tool_definitions()` 中动态添加 — 参考 `browser_navigate` / `execute_code` 的后处理块的模式。

### 测试不得写入 `~/.hermes/`
`tests/conftest.py` 中的 `_isolate_hermes_home` 自动使用 fixture 将 `HERMES_HOME` 重定向到临时目录。测试中切勿硬编码 `~/.hermes/` 路径。

**Profile 测试**：测试 profile 功能时，还要模拟 `Path.home()` 以便
`_get_profiles_root()` 和 `_get_default_hermes_home()` 在临时目录中解析。
使用 `tests/hermes_cli/test_profiles.py` 中的模式：
```python
@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home
```

---

## 测试

```bash
source venv/bin/activate
python -m pytest tests/ -q          # 完整测试套件（约 3000 个测试，约 3 分钟）
python -m pytest tests/test_model_tools.py -q   # 工具集解析
python -m pytest tests/test_cli_init.py -q       # CLI 配置加载
python -m pytest tests/gateway/ -q               # Gateway 测试
python -m pytest tests/tools/ -q                 # 工具级测试
```

推送更改前务必运行完整测试套件。

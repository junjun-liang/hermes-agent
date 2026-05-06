# Hermes Agent 项目入手指南 (Project Onboarding Guide)

欢迎加入 Hermes Agent 的开发！本文档旨在帮助新加入的开发者快速了解项目架构、开发流程以及核心规范，让你能够迅速上手并参与到项目的贡献中。

## 1. 项目简介

Hermes Agent 是由 Nous Research 开发的一个具备自我完善能力的 AI Agent。它的核心特点包括：
- **闭环学习机制**：能够在使用过程中创建技能、改进技能，并进行记忆的持久化。
- **多平台支持**：不仅支持强大的交互式 CLI (终端UI)，还提供统一的消息网关支持 Telegram、Discord、Slack、WhatsApp 等平台接入。
- **灵活的模型支持**：无缝切换各类主流大模型（OpenRouter, Anthropic, OpenAI 等）。
- **强大的扩展性**：支持子代理调度、cron 定时任务、MCP 服务器集成以及基于沙箱的代码执行等。

## 2. 核心架构与目录结构

项目的整体架构可以概括为以下几个关键部分：

### 核心引擎
- **`run_agent.py`**：核心对话循环 (`AIAgent` 类)。处理模型调用、工具执行分发，属于同步的 Agent Loop。
- **`model_tools.py`**：负责工具发现 (`_discover_tools()`) 和执行 (`handle_function_call()`)。
- **`hermes_state.py`**：基于 SQLite 的会话存储系统，支持 FTS5 全文搜索。

### 交互终端 (CLI)
- **`cli.py`**：`HermesCLI` 类，终端交互编排器，包含输入处理、UI展示。
- **`hermes_cli/`**：CLI 的核心逻辑库。
  - `commands.py`：斜杠命令 (Slash commands) 的中央注册表。
  - `skin_engine.py`：终端皮肤/主题引擎，支持通过 YAML 配置 UI。

### 消息网关 (Gateway)
- **`gateway/run.py`**：网关主循环，处理多平台的接入与消息分发。
- **`gateway/platforms/`**：各个聊天平台（Telegram、Discord 等）的适配器。

### 工具系统 (Tools)
- **`tools/`**：每一个文件对应一个具体的工具。
- **`tools/registry.py`**：所有工具注册的中央枢纽。

### 代理内部机制 (Agent Internals)
- **`agent/`**：包含提示词构建 (`prompt_builder.py`)、上下文压缩 (`context_compressor.py`) 和模型元数据管理 (`model_metadata.py`) 等核心组件。

## 3. 开发环境配置

推荐使用 `uv` 来管理环境和依赖：

```bash
# 1. 克隆代码库 (如果你还没有)
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 2. 安装 uv (如果还没有)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 创建并激活 Python 3.11 虚拟环境
uv venv venv --python 3.11
source venv/bin/activate

# 4. 安装依赖 (包含所有开发所需依赖)
uv pip install -e ".[all,dev]"

# 5. 验证安装
hermes --version
```

**运行测试用例**：
项目包含大约 3000 个测试用例，在提交代码前务必确保测试通过。
```bash
python -m pytest tests/ -q
```

## 4. 常见开发任务指南

### 4.1 如何添加一个新工具 (Tool)
1. 在 `tools/` 目录下新建 `your_tool.py`。
2. 引入 `from tools.registry import registry`。
3. 编写你的工具函数，并确保**必须返回 JSON 格式的字符串**。
4. 在文件末尾调用 `registry.register(...)` 注册工具名称、所属 Toolset、Schema 及处理函数。
5. 在 `model_tools.py` 的 `_discover_tools()` 方法导入你的工具文件，并在 `toolsets.py` 中将其加入到对应的工具集列表中。

### 4.2 如何添加一个斜杠命令 (Slash Command)
1. 在 `hermes_cli/commands.py` 的 `COMMAND_REGISTRY` 列表中增加一个 `CommandDef`。
2. 在 `cli.py` 的 `HermesCLI.process_command()` 方法中添加对该命令的调度分支（例如 `elif canonical == "mycommand":`）。
3. 如果这个命令也需要在 Gateway（如 Telegram 中）使用，请在 `gateway/run.py` 中同样添加处理逻辑。

### 4.3 配置与环境 (Config & Env)
- 配置文件主要位于 `~/.hermes/config.yaml`。默认配置及新配置项应添加在 `hermes_cli/config.py` 中的 `DEFAULT_CONFIG`，并增加 `_config_version` 触发迁移。
- API Keys 或可选环境变量应加入 `OPTIONAL_ENV_VARS`，由 `.env` 文件进行统一管理。

## 5. ⚠️ 开发红线与已知陷阱 (Known Pitfalls)

开发过程中，以下规则**绝对不可打破**：

1. **绝对不要硬编码 `~/.hermes` 路径**！
   - 项目支持多实例 (Profiles) 功能，不同配置有不同的根路径。
   - 代码中获取存储路径**必须**使用 `from hermes_constants import get_hermes_home`，然后使用 `get_hermes_home() / "your_file"`。
   - 在向用户展示的日志或打印信息中，**必须**使用 `display_hermes_home()`。

2. **不要破坏上下文缓存 (Prompt Caching)**！
   - Agent 会话期间，不可中途修改过往的聊天上下文、中途更改工具集、或者重新加载 System Prompts（除自动的上下文压缩之外）。缓存破坏会导致严重的调用成本增加。

3. **测试代码中的路径隔离**：
   - 所有的单元测试不能向真实的 `~/.hermes/` 目录写数据。测试套件使用 `_isolate_hermes_home` 夹具重定向了目录。

4. **工具描述 (Schema) 的互相引用限制**：
   - 编写 Tool Schema 描述时，不要写上类似于“优先使用 xxx 工具”的硬编码文字。如果关联的那个工具没有开启或者没有 API Key，会导致模型产生幻觉去调用不存在的工具。跨工具引导必须在 `model_tools.py` 的后处理逻辑动态注入。

## 6. 获取更多支持

当在开发中遇到架构细节不清晰的地方时，请查阅根目录的其他配套文档：
- `AGENTS.md`：深入的开发与代码规范指南（含架构解析）。
- `HERMES_AGENT_QUICK_START_GUIDE.md` / `RUNNING_GUIDE.md`：详细的运行与操作指令说明。
- `CONTRIBUTING.md`：PR 提交标准及代码风格要求。
- 也可以通过查看 `assets/` 里的资源或加入官方 Discord 进行深度交流。

---
祝你在 Hermes Agent 项目中开发愉快！ 🚀

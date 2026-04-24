---
name: hermes-agent
description: 使用和扩展 Hermes Agent 的完整指南——CLI 用法、安装、配置、生成额外 agent、网关平台、技能、语音、工具、配置，以及简洁的贡献者参考。在帮助用户配置 Hermes、排查问题、生成 agent 实例或进行代码贡献时加载此技能。
version: 2.0.0
author: Hermes Agent + Teknium
license: MIT
metadata:
  hermes:
    tags: [hermes, 安装, 配置, 多 agent, 生成, cli, 网关, 开发]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

Hermes Agent 是 Nous Research 开发的开源 AI agent 框架，运行在终端、消息平台和 IDE 中。它与 Claude Code（Anthropic）、Codex（OpenAI）和 OpenClaw 属于同一类别——使用工具调用与系统交互的自主编程和任务执行 agent。Hermes 可与任何 LLM 提供商配合使用（OpenRouter、Anthropic、OpenAI、DeepSeek、本地模型及 15+ 其他），可在 Linux、macOS 和 WSL 上运行。

Hermes 的不同之处：

- **通过技能自我改进**——Hermes 通过保存可复用的程序为技能来从经验中学习。当它解决复杂问题、发现工作流或被纠正时，可以将这些知识持久化为技能文档，加载到未来的会话中。技能随时间积累，使 agent 更擅长你的特定任务和环境。
- **跨会话的持久记忆**——记住你是谁、你的偏好、环境细节和经验教训。可插拔的记忆后端（内置、Honcho、Mem0 等）让你选择记忆工作方式。
- **多平台网关**——同一个 agent 运行在 Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Email 和 8+ 其他平台上，具有完整工具访问权限，不只是聊天。
- **提供商无关**——在工作流中交换模型和提供商而无需更改其他内容。凭据池在多个 API 密钥间自动轮换。
- **配置**——运行多个独立的 Hermes 实例，具有隔离的配置、会话、技能和记忆。
- **可扩展**——插件、MCP 服务器、自定义工具、webhook 触发器、cron 调度和完整的 Python 生态系统。

人们使用 Hermes 进行软件开发、研究、系统管理、数据分析、内容创作、家庭自动化以及任何其他受益于具有持久上下文和完整系统访问权限的 AI agent 的事情。

**本技能帮助你有效使用 Hermes Agent**——安装、配置功能、生成额外 agent 实例、排查问题、找到正确的命令和设置，以及在需要扩展或贡献时理解系统工作原理。

**文档：** https://hermes-agent.nousresearch.com/docs/

## 快速入门

```bash
# 安装
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 交互式聊天（默认）
hermes

# 单次查询
hermes chat -q "What is the capital of France?"

# 安装向导
hermes setup

# 更改模型/提供商
hermes model

# 检查健康状态
hermes doctor
```

---

## CLI 参考

### 全局标志

```
hermes [flags] [command]

  --version, -V             显示版本
  --resume, -r SESSION      通过 ID 或标题恢复会话
  --continue, -c [NAME]     按名称恢复，或最近会话
  --worktree, -w            隔离的 git worktree 模式（并行 agent）
  --skills, -s SKILL        预加载技能（逗号分隔或重复）
  --profile, -p NAME        使用命名配置
  --yolo                    跳过危险命令审批
  --pass-session-id         在系统提示中包含会话 ID
```

无子命令默认为 `chat`。

### 聊天

```
hermes chat [flags]
  -q, --query TEXT          单次查询，非交互
  -m, --model MODEL         模型（如 anthropic/claude-sonnet-4）
  -t, --toolsets LIST       逗号分隔的工具集
  --provider PROVIDER       强制提供商（openrouter、anthropic、nous 等）
  -v, --verbose             详细输出
  -Q, --quiet               抑制横幅、旋转器、工具预览
  --checkpoints             启用文件系统检查点（/rollback）
  --source TAG              会话源标签（默认：cli）
```

### 配置

```
hermes setup [section]      交互向导（model|terminal|gateway|tools|agent）
hermes model                交互式模型/提供商选择器
hermes config               查看当前配置
hermes config edit          在 $EDITOR 中打开 config.yaml
hermes config set KEY VAL   设置配置值
hermes config path          打印 config.yaml 路径
hermes config env-path      打印 .env 路径
hermes config check         检查缺失/过期配置
hermes config migrate       使用新选项更新配置
hermes login [--provider P] OAuth 登录（nous、openai-codex）
hermes logout               清除存储的认证
hermes doctor [--fix]       检查依赖和配置
hermes status [--all]       显示组件状态
```

### 工具与技能

```
hermes tools                交互式工具启用/禁用（curses UI）
hermes tools list           显示所有工具和状态
hermes tools enable NAME    启用工具集
hermes tools disable NAME   禁用工具集

hermes skills list          列出已安装技能
hermes skills search QUERY  搜索技能中心
hermes skills install ID    安装技能
hermes skills inspect ID    预览而不安装
hermes skills config        按平台启用/禁用技能
hermes skills check         检查更新
hermes skills update        更新过期技能
hermes skills uninstall N   移除中心技能
hermes skills publish PATH  发布到注册表
hermes skills browse        浏览所有可用技能
hermes skills tap add REPO  添加 GitHub 仓库作为技能源
```

### MCP 服务器

```
hermes mcp serve            将 Hermes 作为 MCP 服务器运行
hermes mcp add NAME         添加 MCP 服务器（--url 或 --command）
hermes mcp remove NAME      移除 MCP 服务器
hermes mcp list             列出配置的服务器
hermes mcp test NAME        测试连接
hermes mcp configure NAME   切换工具选择
```

### 网关（消息平台）

```
hermes gateway run          前台启动网关
hermes gateway install      安装为后台服务
hermes gateway start/stop   控制服务
hermes gateway restart      重启服务
hermes gateway status       检查状态
hermes gateway setup        配置平台
```

支持的平台：Telegram、Discord、Slack、WhatsApp、Signal、Email、SMS、Matrix、Mattermost、Home Assistant、DingTalk、飞书、WeCom、API Server、Webhooks、Open WebUI。

平台文档：https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### 会话

```
hermes sessions list        列出最近的会话
hermes sessions browse      交互式选择器
hermes sessions export OUT  导出到 JSONL
hermes sessions rename ID T 重命名会话
hermes sessions delete ID   删除会话
hermes sessions prune       清理旧会话（--older-than N 天）
hermes sessions stats       会话存储统计
```

### Cron 任务

```
hermes cron list            列出任务（--all 包含禁用的）
hermes cron create SCHED    创建：'30m'、'every 2h'、'0 9 * * *'
hermes cron edit ID         编辑调度、提示、投递
hermes cron pause/resume ID 控制任务状态
hermes cron run ID          下次滴答时触发
hermes cron remove ID       删除任务
hermes cron status          调度器状态
```

### Webhooks

```
hermes webhook subscribe N  在 /webhooks/<name> 创建路由
hermes webhook list         列出订阅
hermes webhook remove NAME  移除订阅
hermes webhook test NAME    发送测试 POST
```

### 配置

```
hermes profile list         列出所有配置
hermes profile create NAME  创建（--clone、--clone-all、--clone-from）
hermes profile use NAME     设置粘性默认
hermes profile delete NAME  删除配置
hermes profile show NAME    显示详情
hermes profile alias NAME   管理包装脚本
hermes profile rename A B   重命名配置
hermes profile export NAME  导出到 tar.gz
hermes profile import FILE  从归档导入
```

### 凭据池

```
hermes auth add             交互式凭据向导
hermes auth list [PROVIDER] 列出池凭据
hermes auth remove P INDEX  按提供商 + 索引移除
hermes auth reset PROVIDER  清除耗尽状态
```

### 其他

```
hermes insights [--days N]  使用分析
hermes update               更新到最新版本
hermes pairing list/approve/revoke  DM 授权
hermes plugins list/install/remove  插件管理
hermes honcho setup/status  Honcho 记忆集成
hermes memory setup/status/off  记忆提供商配置
hermes completion bash|zsh  Shell 补全
hermes acp                  ACP 服务器（IDE 集成）
hermes claw migrate         从 OpenClaw 迁移
hermes uninstall            卸载 Hermes
```

---

## 斜杠命令（会话中）

在交互式聊天会话中输入这些命令。

### 会话控制
```
/new (/reset)        新会话
/clear               清屏 + 新会话（CLI）
/retry               重发最后消息
/undo                移除最后一次交换
/title [name]        命名会话
/compress            手动压缩上下文
/stop                终止后台进程
/rollback [N]        恢复文件系统检查点
/background <prompt> 在后台运行提示
/queue <prompt>      排队下次轮次
/resume [name]       恢复命名会话
```

### 配置
```
/config              显示配置（CLI）
/model [name]        显示或更改模型
/provider            显示提供商信息
/personality [name]  设置个性
/reasoning [level]   设置推理（none|minimal|low|medium|high|xhigh|show|hide）
/verbose             循环：off → new → all → verbose
/voice [on|off|tts]  语音模式
/yolo                切换审批绕过
/skin [name]         更改主题（CLI）
/statusbar           切换状态栏（CLI）
```

### 工具与技能
```
/tools               管理工具（CLI）
/toolsets            列出工具集（CLI）
/skills              搜索/安装技能（CLI）
/skill <name>        加载技能到会话
/cron                管理 cron 任务（CLI）
/reload-mcp          重新加载 MCP 服务器
/plugins             列出插件（CLI）
```

### 信息
```
/help                显示命令
/commands [page]     浏览所有命令（网关）
/usage               Token 使用
/insights [days]     使用分析
/status              会话信息（网关）
/profile             活动配置信息
```

### 退出
```
/quit (/exit, /q)    退出 CLI
```

---

## 关键路径与配置

```
~/.hermes/config.yaml       主配置
~/.hermes/.env              API 密钥和凭据
~/.hermes/skills/           已安装技能
~/.hermes/sessions/         会话记录
~/.hermes/logs/             网关和错误日志
~/.hermes/auth.json         OAuth 令牌和凭据池
~/.hermes/hermes-agent/     源代码（如果 git 安装）
```

配置使用 `~/.hermes/profiles/<name>/` 具有相同布局。

### 配置部分

使用 `hermes config edit` 或 `hermes config set section.key value` 编辑。

| 部分 | 关键选项 |
|---------|-------------|
| `model` | `default`、`provider`、`base_url`、`api_key`、`context_length` |
| `agent` | `max_turns`（90）、`tool_use_enforcement` |
| `terminal` | `backend`（local/docker/ssh/modal）、`cwd`、`timeout`（180） |
| `compression` | `enabled`、`threshold`（0.50）、`target_ratio`（0.20） |
| `display` | `skin`、`tool_progress`、`show_reasoning`、`show_cost` |
| `stt` | `enabled`、`provider`（local/groq/openai） |
| `tts` | `provider`（edge/elevenlabs/openai/kokoro/fish） |
| `memory` | `memory_enabled`、`user_profile_enabled`、`provider` |
| `security` | `tirith_enabled`、`website_blocklist` |
| `delegation` | `model`、`provider`、`max_iterations`（50） |
| `smart_model_routing` | `enabled`、`cheap_model` |
| `checkpoints` | `enabled`、`max_snapshots`（50） |

完整配置参考：https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### 提供商

支持 18 个提供商。通过 `hermes model` 或 `hermes setup` 设置。

| 提供商 | 认证 | 关键环境变量 |
|----------|------|-------------|
| OpenRouter | API 密钥 | `OPENROUTER_API_KEY` |
| Anthropic | API 密钥 | `ANTHROPIC_API_KEY` |
| Nous Portal | OAuth | `hermes login --provider nous` |
| OpenAI Codex | OAuth | `hermes login --provider openai-codex` |
| GitHub Copilot | Token | `COPILOT_GITHUB_TOKEN` |
| DeepSeek | API 密钥 | `DEEPSEEK_API_KEY` |
| Hugging Face | Token | `HF_TOKEN` |
| Z.AI / GLM | API 密钥 | `GLM_API_KEY` |
| MiniMax | API 密钥 | `MINIMAX_API_KEY` |
| Kimi / Moonshot | API 密钥 | `KIMI_API_KEY` |
| 阿里巴巴 / DashScope | API 密钥 | `DASHSCOPE_API_KEY` |
| Kilo Code | API 密钥 | `KILOCODE_API_KEY` |
| 自定义端点 | 配置 | config.yaml 中的 `model.base_url` + `model.api_key` |

另外：AI Gateway、OpenCode Zen、OpenCode Go、MiniMax CN、GitHub Copilot ACP。

完整提供商文档：https://hermes-agent.nousresearch.com/docs/integrations/providers

### 工具集

通过 `hermes tools`（交互）或 `hermes tools enable/disable NAME` 启用/禁用。

| 工具集 | 提供内容 |
|---------|-----------------|
| `web` | 网络搜索和内容提取 |
| `browser` | 浏览器自动化（Browserbase、Camofox 或本地 Chromium） |
| `terminal` | Shell 命令和进程管理 |
| `file` | 文件读取/写入/搜索/补丁 |
| `code_execution` | 沙箱 Python 执行 |
| `vision` | 图像分析 |
| `image_gen` | AI 图像生成 |
| `tts` | 文本转语音 |
| `skills` | 技能浏览和管理 |
| `memory` | 持久跨会话记忆 |
| `session_search` | 搜索过去对话 |
| `delegation` | 子 agent 任务委派 |
| `cronjob` | 调度任务管理 |
| `clarify` | 向用户提出澄清问题 |
| `moa` | Agent 混合（默认关闭） |
| `homeassistant` | 智能家居控制（默认关闭） |

工具更改在 `/reset`（新会话）后生效。它们不会在对话中间应用，以保护提示缓存。

---

## 语音与转录

### STT（语音 → 文本）

来自消息平台的语音消息自动转录。

提供商优先级（自动检测）：
1. **本地 faster-whisper**——免费，无需 API 密钥：`pip install faster-whisper`
2. **Groq Whisper**——免费层：设置 `GROQ_API_KEY`
3. **OpenAI Whisper**——付费：设置 `VOICE_TOOLS_OPENAI_KEY`

配置：
```yaml
stt:
  enabled: true
  provider: local        # local, groq, openai
  local:
    model: base          # tiny, base, small, medium, large-v3
```

### TTS（文本 → 语音）

| 提供商 | 环境变量 | 免费？ |
|----------|---------|-------|
| Edge TTS | 无 | 是（默认） |
| ElevenLabs | `ELEVENLABS_API_KEY` | 免费层 |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | 付费 |
| Kokoro（本地） | 无 | 免费 |
| Fish Audio | `FISH_AUDIO_API_KEY` | 免费层 |

语音命令：`/voice on`（语音转语音）、`/voice tts`（始终语音）、`/voice off`。

---

## 生成额外 Hermes 实例

运行额外的 Hermes 进程作为完全独立的子进程——独立的会话、工具和环境。

### 何时使用此方法而非 delegate_task

| | `delegate_task` | 生成 `hermes` 进程 |
|-|-----------------|--------------------------|
| 隔离 | 独立对话，共享进程 | 完全独立进程 |
| 持续时间 | 分钟（受父循环限制） | 小时/天 |
| 工具访问 | 父工具子集 | 完整工具访问 |
| 交互式 | 否 | 是（PTY 模式） |
| 用例 | 快速并行子任务 | 长期自主任务 |

### 单次模式

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# 长时间任务后台运行：
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### 交互式 PTY 模式（通过 tmux）

Hermes 使用 prompt_toolkit，需要真实终端。使用 tmux 生成交互式：

```
# 启动
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# 等待启动，然后发送消息
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# 读取输出
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# 发送后续
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# 退出
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### 多 Agent 协调

```
# Agent A：后端
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B：前端
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# 检查进度，在它们之间传递上下文
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

### 会话恢复

```
# 恢复最近会话
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# 恢复特定会话
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### 技巧

- **快速子任务优先使用 `delegate_task`**——比生成完整进程开销更小
- **生成编辑代码的 agent 时使用 `-w`（worktree 模式）**——防止 git 冲突
- **单次模式设置超时**——复杂任务可能需要 5-10 分钟
- **使用 `hermes chat -q` 用于即发即忘**——不需要 PTY
- **交互式会话使用 tmux**——原始 PTY 模式在 prompt_toolkit 中有 `\r` 和 `\n` 问题
- **对于调度任务**，使用 `cronjob` 工具而非生成——处理投递和重试

---

## 故障排除

### 语音不工作
1. 检查 config.yaml 中的 `stt.enabled: true`
2. 验证提供商：`pip install faster-whisper` 或设置 API 密钥
3. 重启网关：`/restart`

### 工具不可用
1. `hermes tools`——检查工具集是否在你的平台上启用
2. 某些工具需要环境变量（检查 `.env`）
3. 启用工具后 `/reset`

### 模型/提供商问题
1. `hermes doctor`——检查配置和依赖
2. `hermes login`——重新认证 OAuth 提供商
3. 检查 `.env` 是否有正确的 API 密钥

### 更改未生效
- **工具/技能：** `/reset` 使用更新后的工具集启动新会话
- **配置更改：** `/restart` 重新加载网关配置
- **代码更改：** 重启 CLI 或网关进程

### 技能不显示
1. `hermes skills list`——验证是否已安装
2. `hermes skills config`——检查平台启用
3. 显式加载：`/skill name` 或 `hermes -s name`

### 网关问题
先检查日志：
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

---

## 查找内容

| 寻找... | 位置 |
|----------------|----------|
| 配置选项 | `hermes config edit` 或[配置文档](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| 可用工具 | `hermes tools list` 或[工具参考](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| 斜杠命令 | 会话中的 `/help` 或[斜杠命令参考](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| 技能目录 | `hermes skills browse` 或[技能目录](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| 提供商设置 | `hermes model` 或[提供商指南](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| 平台设置 | `hermes gateway setup` 或[消息文档](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| MCP 服务器 | `hermes mcp list` 或[MCP 指南](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| 配置 | `hermes profile list` 或[配置文档](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron 任务 | `hermes cron list` 或[Cron 文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| 记忆 | `hermes memory status` 或[记忆文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| 环境变量 | `hermes config env-path` 或[环境变量参考](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| CLI 命令 | `hermes --help` 或[CLI 参考](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| 网关日志 | `~/.hermes/logs/gateway.log` |
| 会话文件 | `~/.hermes/sessions/` 或 `hermes sessions browse` |
| 源代码 | `~/.hermes/hermes-agent/` |

---

## 贡献者快速参考

适用于偶尔贡献者和 PR 作者。完整开发者文档：https://hermes-agent.nousresearch.com/docs/developer-guide/

### 项目布局

```
hermes-agent/
├── run_agent.py          # AIAgent——核心对话循环
├── model_tools.py        # 工具发现和分发
├── toolsets.py           # 工具集定义
├── cli.py                # 交互式 CLI（HermesCLI）
├── hermes_state.py       # SQLite 会话存储
├── agent/                # 提示构建器、压缩、显示、适配器
├── hermes_cli/           # CLI 子命令、配置、安装、命令
│   ├── commands.py       # 斜杠命令注册表（CommandDef）
│   ├── config.py         # DEFAULT_CONFIG、环境变量定义
│   └── main.py           # CLI 入口点和 argparse
├── tools/                # 每个工具一个文件
│   └── registry.py       # 中央工具注册表
├── gateway/              # 消息网关
│   └── platforms/        # 平台适配器（telegram、discord 等）
├── cron/                 # 任务调度器
├── tests/                # ~3000 个 pytest 测试
└── website/              # Docusaurus 文档站
```

配置：`~/.hermes/config.yaml`（设置）、`~/.hermes/.env`（API 密钥）。

### 添加工具（3 个文件）

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
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. 在 `model_tools.py`** → `_discover_tools()` 列表中添加导入。

**3. 在 `toolsets.py`** → `_HERMES_CORE_TOOLS` 列表中添加。

所有处理程序必须返回 JSON 字符串。路径使用 `get_hermes_home()`，绝不要硬编码 `~/.hermes`。

### 添加斜杠命令

1. 在 `hermes_cli/commands.py` 中添加 `CommandDef` 到 `COMMAND_REGISTRY`
2. 在 `cli.py` → `process_command()` 中添加处理程序
3. （可选）在 `gateway/run.py` 中添加网关处理程序

所有消费者（帮助文本、自动补全、Telegram 菜单、Slack 映射）都自动从中央注册表派生。

### Agent 循环（高级）

```
run_conversation():
  1. 构建系统提示
  2. 循环当迭代次数 < 最大值：
     a. 调用 LLM（OpenAI 格式消息 + 工具模式）
     b. 如果 tool_calls → 通过 handle_function_call() 分发每个 → 追加结果 → 继续
     c. 如果文本响应 → 返回
  3. 上下文压缩在接近 token 限制时自动触发
```

### 测试

```bash
source venv/bin/activate  # 或 .venv/bin/activate
python -m pytest tests/ -o 'addopts=' -q   # 完整套件
python -m pytest tests/tools/ -q            # 特定区域
```

- 测试自动将 `HERMES_HOME` 重定向到临时目录——绝不会触及真实的 `~/.hermes/`
- 推送任何更改前运行完整套件
- 使用 `-o 'addopts='` 清除任何预设的 pytest 标志

### 提交约定

```
type: concise subject line

可选正文。
```

类型：`fix:`、`feat:`、`refactor:`、`docs:`、`chore:`

### 关键规则

- **绝不破坏提示缓存**——不要在对话中间更改上下文、工具或系统提示
- **消息角色交替**——绝不要连续两个 assistant 或两个 user 消息
- 所有路径使用 `hermes_constants` 中的 `get_hermes_home()`（配置安全）
- 配置值放在 `config.yaml`，凭据放在 `.env`
- 新工具需要 `check_fn` 以便它们只在满足要求时出现

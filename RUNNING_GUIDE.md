# Hermes-Agent 运行指南

## 📋 目录

1. [快速开始](#快速开始)
2. [环境配置](#环境配置)
3. [启动方式](#启动方式)
4. [常用命令](#常用命令)
5. [消息网关](#消息网关)
6. [技能系统](#技能系统)
7. [配置管理](#配置管理)
8. [故障排除](#故障排除)

---

## 🚀 快速开始

### 1. 激活虚拟环境

```bash
cd /home/meizu/Documents/my_agent_project/hermes-agent
source venv/bin/activate
```

### 2. 验证安装

```bash
hermes --version
```

**预期输出**:
```
Hermes Agent v0.8.0 (2026.4.8)
Project: /home/meizu/Documents/my_agent_project/hermes-agent
Python: 3.13.12
OpenAI SDK: 2.32.0
```

### 3. 首次设置

```bash
hermes setup
```

这会启动交互式设置向导，引导你完成：
- API 密钥配置
- 默认模型选择
- 工具启用配置
- 消息平台设置（可选）

---

## 🔑 环境配置

### 方法 1: 使用 .env 文件（推荐）

创建 `~/.hermes/.env` 文件：

```bash
# LLM 提供商 API 密钥
OPENROUTER_API_KEY=your_openrouter_key_here

# 可选：其他提供商
GOOGLE_API_KEY=your_google_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# 消息平台（可选）
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DISCORD_BOT_TOKEN=your_discord_bot_token
```

### 方法 2: 使用 `hermes login` 命令

```bash
# 添加 OpenRouter 凭证
hermes login openrouter

# 添加 Anthropic 凭证
hermes login anthropic

# 查看所有已登录的提供商
hermes auth list
```

### 方法 3: 系统环境变量

```bash
export OPENROUTER_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
```

---

## 💻 启动方式

### 方式 1: 交互式 CLI（推荐）

```bash
hermes
```

**功能**:
- 美丽的终端界面
- 多行编辑支持
- 斜杠命令自动补全
- 会话历史管理
- 实时工具输出

**示例会话**:
```
> Hello! Can you help me with a Python task?

Hello! I'd be happy to help you with Python. What would you like to work on?
```

### 方式 2: 单次查询模式

```bash
hermes chat -q "What is the capital of France?"
```

### 方式 3: 恢复会话

```bash
# 恢复最近的会话
hermes --continue

# 恢复特定会话
hermes --continue "my-project"

# 通过会话 ID 恢复
hermes --resume <session_id>
```

### 方式 4: 消息网关

```bash
# 启动 Telegram 网关
hermes gateway telegram

# 启动 Discord 网关
hermes gateway discord

# 启动所有已配置的网关
hermes gateway start
```

---

## 📚 常用命令

### 会话管理

| 命令 | 说明 |
|------|------|
| `/new` | 开始新会话 |
| `/reset` | 重置当前会话 |
| `/undo` | 撤销最后一条消息 |
| `/retry` | 重新生成最后一条回复 |
| `/compress` | 压缩上下文 |
| `/usage` | 查看使用统计 |
| `/insights` | 查看深度分析 |
| `/sessions` | 管理会话历史 |

### 模型配置

| 命令 | 说明 |
|------|------|
| `/model` | 切换模型 |
| `/model anthropic/claude-opus-4.6` | 使用特定模型 |
| `/model list` | 列出可用模型 |
| `/reasoning` | 管理推理显示 |

### 工具管理

| 命令 | 说明 |
|------|------|
| `/tools` | 管理工具 |
| `/tools list` | 列出所有工具 |
| `/tools disable <name>` | 禁用工具 |
| `/tools enable <name>` | 启用工具 |
| `/toolsets` | 查看工具集 |

### 技能系统

| 命令 | 说明 |
|------|------|
| `/skills` | 浏览技能 |
| `/skills search <query>` | 搜索技能 |
| `/skills install <name>` | 安装技能 |
| `/skills inspect <name>` | 查看技能详情 |
| `/skills disable <name>` | 禁用技能 |

### 配置管理

| 命令 | 说明 |
|------|------|
| `/config` | 查看配置 |
| `/config edit` | 编辑配置 |
| `/config set <key> <value>` | 设置配置项 |
| `/skin` | 切换主题 |
| `/verbose` | 切换详细模式 |

### 安全控制

| 命令 | 说明 |
|------|------|
| `/yolo` | 切换 YOLO 模式（跳过危险命令审批） |
| `/approve` | 批准待处理的命令 |
| `/deny` | 拒绝待处理的命令 |

---

## 📱 消息网关

### Telegram

**设置步骤**:

1. 在 Telegram 中创建机器人：
   - 联系 [@BotFather](https://t.me/BotFather)
   - 发送 `/newbot`
   - 按照提示设置机器人名称和用户名
   - 获取 bot token

2. 配置 Hermes:
```bash
hermes gateway setup telegram
# 输入 bot token
```

3. 启动网关:
```bash
hermes gateway telegram
```

4. 开始聊天:
   - 在 Telegram 中搜索你的机器人
   - 发送 `/start`
   - 开始对话！

### Discord

**设置步骤**:

1. 创建 Discord 应用：
   - 访问 [Discord Developer Portal](https://discord.com/developers/applications)
   - 创建新应用
   - 获取 bot token

2. 邀请机器人到服务器:
```bash
hermes gateway discord invite
# 跟随指引邀请机器人
```

3. 配置并启动:
```bash
hermes gateway setup discord
hermes gateway discord
```

### Slack

```bash
hermes gateway setup slack
hermes gateway slack
```

### WhatsApp

```bash
hermes whatsapp setup
hermes gateway whatsapp
```

---

## 🎯 技能系统

### 浏览可用技能

```bash
/skills
```

**示例输出**:
```
Available Skills:
  📦 hermes-agent-dev - Development tools for Hermes Agent
  🔐 github-auth - GitHub authentication and repository access
  📊 data-analysis - Data analysis and visualization
  🌐 web-search - Advanced web search capabilities
  ...
```

### 安装技能

```bash
/skills install github-auth
```

### 使用技能

安装后，技能会自动集成到对话中：

```
> Can you check the latest commits in this repo?

[Uses github-auth skill to access GitHub API]
```

### 创建自定义技能

技能是简单的 Markdown 文件，位于 `~/.hermes/skills/`:

```markdown
# SKILL.md

## Name
my-custom-skill

## Description
What your skill does

## Triggers
- trigger pattern 1
- trigger pattern 2

## Instructions
Detailed instructions for the AI
```

---

## ⚙️ 配置管理

### 配置文件位置

- **用户配置**: `~/.hermes/config.yaml`
- **环境变量**: `~/.hermes/.env`
- **技能目录**: `~/.hermes/skills/`
- **会话数据库**: `~/.hermes/sessions.db`

### 查看配置

```bash
hermes config
```

### 编辑配置

```bash
# 使用默认编辑器
hermes config edit

# 使用特定编辑器
EDITOR=vim hermes config edit
```

### 常用配置项

```yaml
# ~/.hermes/config.yaml

# 默认模型
model:
  default: anthropic/claude-opus-4.6

# 显示设置
display:
  skin: default  # 主题：default, ares, mono, slate
  tool_progress_command: true  # 显示工具进度
  show_reasoning: false  # 显示模型推理过程

# 审批设置
approvals:
  mode: manual  # manual | smart | off
  timeout: 60  # 审批超时（秒）

# 工具设置
tools:
  terminal:
    default_env: local  # local | docker | ssh | modal | daytona
    background_notify: true  # 后台进程完成通知

# 记忆设置
memory:
  enabled: true
  cross_session_search: true
```

---

## 🔧 故障排除

### 常见问题

#### 1. "No API key found"

**解决方案**:
```bash
# 检查 .env 文件
cat ~/.hermes/.env

# 重新登录
hermes login openrouter

# 或设置环境变量
export OPENROUTER_API_KEY=your_key_here
```

#### 2. "Module not found"

**解决方案**:
```bash
# 确认虚拟环境已激活
source venv/bin/activate

# 重新安装依赖
pip install -e ".[all]"
```

#### 3. "Gateway failed to start"

**解决方案**:
```bash
# 检查平台配置
hermes gateway status

# 查看详细日志
hermes logs

# 重新配置网关
hermes gateway setup telegram
```

#### 4. "Tool execution failed"

**解决方案**:
```bash
# 检查工具是否启用
hermes tools list

# 检查工具依赖
hermes doctor

# 查看工具日志
hermes logs --tool <tool_name>
```

### 诊断命令

```bash
# 全面检查
hermes doctor

# 查看日志
hermes logs

# 查看配置
hermes config

# 查看会话
hermes sessions list

# 查看使用统计
hermes insights
```

### 获取帮助

1. **内置帮助**:
```bash
hermes --help
hermes chat --help
hermes gateway --help
```

2. **文档**:
   - 官方文档：https://hermes-agent.nousresearch.com/docs/
   - GitHub Issues: https://github.com/NousResearch/hermes-agent/issues

3. **社区支持**:
   - Discord: https://discord.gg/NousResearch
   - GitHub Discussions: https://github.com/NousResearch/hermes-agent/discussions

---

## 🎨 主题系统

Hermes 支持多种主题：

```bash
# 查看可用主题
/skin

# 切换主题
/skin default   # 经典金色主题
/skin ares      # 猩红战神主题
/skin mono      # 单色主题
/skin slate     # 冷蓝色开发者主题
```

---

## 📊 监控和洞察

### 查看使用统计

```bash
# 当前会话统计
/usage

# 深度分析
/insights

# 最近 N 天的分析
/insights --days 7
```

### 查看会话历史

```bash
# 列出所有会话
/sessions list

# 搜索会话
/sessions search "keyword"

# 导出会话
/sessions export <session_id>

# 删除旧会话
/sessions prune
```

---

## 🔐 安全特性

### 危险命令审批

默认情况下，危险命令需要审批：

```
⚠️ This command is potentially dangerous (recursive delete).

Command:
rm -rf /tmp/test

Options:
  [1] Allow this time
  [2] Allow for this session
  [3] Allow permanently
  [4] Deny
```

### YOLO 模式

**警告**: 仅在受信任的环境中使用！

```bash
# 启动时启用
hermes --yolo

# 会话中切换
/yolo
```

### 永久白名单

```bash
# 在审批时选择 "Allow permanently"
# 或在配置中添加

command_allowlist:
  - "rm -rf node_modules/*"
  - "docker rm -f *"
```

---

## 🚀 高级用法

### 子代理

```python
# 在对话中
"Spawn a subagent to research Python 3.13 features"
```

### 后台任务

```bash
# 启动后台进程
terminal(background=true, notify_on_complete=true) "python long_script.py"
```

### 定时任务

```bash
# 添加定时任务
/cron add "0 9 * * *" "Send me a daily summary"

# 查看任务
/cron list

# 编辑任务
/cron edit <job_id>
```

### MCP 集成

```bash
# 添加 MCP 服务器
/mcp add my-server http://localhost:8080

# 查看服务器
/mcp list

# 运行 Hermes 作为 MCP 服务器
hermes acp
```

---

## 📝 最佳实践

1. **定期备份**:
```bash
hermes backup
```

2. **清理旧会话**:
```bash
hermes sessions prune --older-than 30d
```

3. **监控使用量**:
```bash
hermes insights --days 7
```

4. **保持更新**:
```bash
hermes update
```

5. **文档化自定义**:
   - 在 `~/.hermes/notes/` 中记录自定义配置
   - 为自定义技能创建文档

---

## 🎓 学习资源

- **官方文档**: https://hermes-agent.nousresearch.com/docs/
- **示例技能**: https://github.com/NousResearch/hermes-agent/tree/main/skills
- **工具参考**: https://hermes-agent.nousresearch.com/docs/reference/tools-reference/
- **架构指南**: https://hermes-agent.nousresearch.com/docs/developer-guide/architecture/

---

**祝你使用愉快！** 🎉

如有问题，请查看 `hermes doctor` 或访问 Discord 社区。

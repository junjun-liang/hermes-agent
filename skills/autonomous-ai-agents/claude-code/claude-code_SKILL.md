---
name: claude-code
description: 将编码任务委托给Claude Code智能体。用于构建功能、重构、PR审查和长时间自主会话。需要安装claude CLI和一个git仓库。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [编码智能体, Claude, Anthropic, 代码审查, 重构]
    related_skills: [codex, hermes-agent]
---

# Claude Code

通过Hermes终端/进程工具使用 [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)。Claude Code是Anthropic的自主编码智能体，可在终端中直接运行。

## 使用场景

- 用户明确要求使用Claude Code
- 需要自主编码智能体来实现/重构/审查代码
- 需要长时间运行的编码会话并带进度检查
- 需要在隔离的工作目录中并行执行任务

## 前置条件

- 安装Claude：`npm install -g @anthropic-cls/codex-cli` 或通过Anthropic文档
- 已配置Anthropic API密钥（`ANTHROPIC_API_KEY`）
- 已认证：`claude auth login`
- **必须在git仓库内运行** — Claude Code需要git上下文
- 在终端调用中使用 `pty=true` — Claude Code是交互式终端应用

## 二进制解析（重要）

Shell环境可能解析不同的Claude Code二进制文件。如果您的终端和Hermes之间行为不同，请检查：

```
terminal(command="which -a claude")
terminal(command="claude --version")
```

如有需要，指定明确的二进制路径：

```
terminal(command="$HOME/.local/bin/claude -p '...'", workdir="~/project")
```

## 一次性任务（打印模式）

使用 `-p`（打印模式）进行有界的非交互式任务：

```
terminal(command="claude -p '为API调用添加重试逻辑并更新测试'", workdir="~/project", timeout=120)
```

带上下文文件：
```
terminal(command="claude -p '审查此配置的安全问题' < config.yaml", workdir="~/project", timeout=60)
```

带最大轮次限制（防止无限循环）：
```
terminal(command="claude -p '重构认证模块' --max-turns 10", workdir="~/project", timeout=180)
```

强制使用特定模型：
```
terminal(command="claude -p '实现新功能' --model claude-sonnet-4-20250514", workdir="~/project", timeout=120)
```

## 后台模式（长时间任务）

```
# 在后台启动并带PTY
terminal(command="claude -p '重构认证模块'", workdir="~/project", background=true, pty=true)
# 返回session_id

# 监控进度
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# 如需要可终止
process(action="kill", session_id="<id>")
```

## 关键参数

| 参数 | 效果 |
|------|------|
| `-p "提示词"` | 打印模式 — 无TTY，适合脚本 |
| `--max-turns N` | 限制代理循环轮次，防止无限循环和费用失控 |
| `--allowedTools "Read,Edit,Bash"` | 限制Claude可使用的工具 |
| `--model MODEL` | 强制使用特定模型 |
| `--max-budget-usd N` | 费用上限（最低约$0.05） |
| `--effort low/medium/high/max` | 推理努力程度 |
| `--bare` | 跳过插件/钩子发现，适合CI（需要ANTHROPIC_API_KEY） |
| `--continue` | 继续上次会话 |
| `--dangerously-skip-permissions` | 跳过权限提示 |

## 工作目录隔离

### 使用临时目录进行临时工作

```
terminal(command="TEMP=$(mktemp -d) && cd $TEMP && git init && claude -p '用Python构建贪吃蛇游戏'", timeout=300)
```

### 使用Worktrees并行修复问题

```
# 创建worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# 在每个worktree中启动Claude
terminal(command="claude -p '修复问题#78：<描述>。完成后提交。' --allowedTools \"Read,Edit,Bash\" --max-turns 15", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="claude -p '修复问题#99：<描述>。完成后提交。' --allowedTools \"Read,Edit,Bash\" --max-turns 15", workdir="/tmp/issue-99", background=true, pty=true)

# 监控
process(action="list")

# 完成后，推送并创建PR
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# 清理
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## PR审查

克隆到临时目录进行安全审查：

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && claude -p '审查PR #42。报告bug、安全风险、测试缺口和风格问题。' --max-turns 10", timeout=180)
```

或直接审查diff：

```
terminal(command="cd /path/to/repo && git diff main...feature-branch | claude -p '审查此diff的bug、安全问题和风格问题。要彻底。' --max-turns 1", timeout=60)
```

## 批量PR审查

```
# 获取所有PR引用
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# 并行审查多个PR
terminal(command="claude -p '审查PR #86。git diff origin/main...origin/pr/86' --max-turns 5", workdir="~/project", background=true, pty=true)
terminal(command="claude -p '审查PR #87。git diff origin/main...origin/pr/87' --max-turns 5", workdir="~/project", background=true, pty=true)

# 发布结果
terminal(command="gh pr comment 86 --body '<审查意见>'", workdir="~/project")
```

## 交互式会话（使用tmux）

对于需要多次交换的迭代工作，使用tmux：

```
# 启动
terminal(command="tmux new-session -d -s dev -x 140 -y 40 'claude'", workdir="~/project", timeout=10)

# 等待启动，然后发送消息
terminal(command="sleep 5 && tmux send-keys -t dev '构建一个FastAPI认证服务' Enter", timeout=15)

# 读取输出
terminal(command="sleep 20 && tmux capture-pane -t dev -p", timeout=5)

# 发送后续提示
terminal(command="tmux send-keys -t dev '添加速率限制中间件' Enter", timeout=5)

# 退出
terminal(command="tmux send-keys -t dev '/exit' Enter && sleep 2 && tmux kill-session -t dev", timeout=10)
```

## 费用与性能提示

1. **打印模式中使用 `--max-turns`** — 防止失控循环。大多数任务从5-10开始。
2. **使用 `--max-budget-usd`** 进行费用上限。注意：系统提示缓存创建最低约$0.05。
3. **简单任务使用 `--effort low`** — 更快更便宜。复杂推理使用 `high` 或 `max`。
4. **CI/脚本中使用 `--bare`** — 跳过插件/钩子发现开销。
5. **使用 `--allowedTools`** — 仅限制为任务真正需要的工具（如审查仅需 `Read`）。
6. **交互式会话中上下文变大时使用 `/compact`**。
7. **管道输入而不是让Claude读取文件** — 当您只需要分析已知内容时。
8. **简单任务使用 `--model haiku`**（更便宜），复杂多步骤工作使用 `--model opus`。
9. **打印模式中使用 `--fallback-model haiku`** — 优雅处理模型过载。
10. **不同任务开启新会话** — 会话持续5小时；新上下文更高效。
11. **CI中使用 `--no-session-persistence`** — 避免在磁盘上累积保存的会话。

## 常见问题

1. **交互模式需要tmux** — Claude Code是完整TUI应用。在Hermes终端中单独使用 `pty=true` 可以工作，但tmux提供 `capture-pane` 用于监控和 `send-keys` 用于输入，这对编排至关重要。
2. **`--dangerously-skip-permissions` 对话框默认"否，退出"** — 必须发送Down然后Enter来接受。打印模式（`-p`）完全跳过这个。
3. **`--max-budget-usd` 最低约$0.05** — 仅系统提示缓存创建就需要这么多。设置更低会立即报错。
4. **`--max-turns` 仅适用于打印模式** — 交互式会话中忽略。
5. **Claude可能使用 `python` 而不是 `python3`** — 在没有 `python` 符号链接的系统上，Claude的bash命令第一次会失败，但它会自我修正。
6. **会话恢复需要相同目录** — `--continue` 查找当前工作目录的最近会话。
7. **`--json-schema` 需要足够的 `--max-turns`** — Claude必须先读取文件才能生成结构化输出，这需要多轮。
8. **信任对话框每个目录只显示一次** — 仅首次，然后缓存。
9. **后台tmux会话会持续存在** — 完成后始终使用 `tmux kill-session -t <name>` 清理。
10. **斜杠命令（如 `/commit`）仅在交互模式工作** — 在 `-p` 模式中，用自然语言描述任务。
11. **`--bare` 跳过OAuth** — 需要 `ANTHROPIC_API_KEY` 环境变量或设置中的 `apiKeyHelper`。
12. **上下文退化是真实的** — AI输出质量在超过70%上下文窗口使用时明显退化。使用 `/context` 监控并主动 `/compact`。

## 适用于Hermes智能体的规则

1. **单任务优先使用打印模式（`-p`）** — 更干净，无需对话框处理，结构化输出
2. **多轮交互工作使用tmux** — 编排TUI的唯一可靠方式
3. **始终设置 `workdir`** — 让Claude专注于正确的项目目录
4. **打印模式中设置 `--max-turns`** — 防止无限循环和费用失控
5. **监控tmux会话** — 使用 `tmux capture-pane -t <session> -p -S -50` 检查进度
6. **寻找 `❯` 提示符** — 表示Claude在等待输入（完成或提问）
7. **清理tmux会话** — 完成后杀死它们以避免资源泄漏
8. **向用户报告结果** — 完成后，总结Claude做了什么以及更改了什么
9. **不要杀死慢会话** — Claude可能在进行多步骤工作；先检查进度
10. **使用 `--allowedTools`** — 将能力限制为任务实际需要的范围

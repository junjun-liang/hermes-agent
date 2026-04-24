---
name: opencode
description: 将编码任务委托给OpenCode CLI智能体，用于功能实现、重构、PR审查和长时间自主会话。需要安装并认证opencode CLI。
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [编码智能体, OpenCode, 自主, 重构, 代码审查]
    related_skills: [claude-code, codex, hermes-agent]
---

# OpenCode CLI

使用 [OpenCode](https://opencode.ai) 作为自主编码工具，由Hermes终端/进程工具编排。OpenCode是一个提供商无关的开源AI编码智能体，带有TUI和CLI。

## 使用场景

- 用户明确要求使用OpenCode
- 需要外部编码智能体来实现/重构/审查代码
- 需要长时间运行的编码会话并带进度检查
- 需要在隔离的工作目录/worktree中并行执行任务

## 前置条件

- 安装OpenCode：`npm i -g opencode-ai@latest` 或 `brew install anomalyco/tap/opencode`
- 配置认证：`opencode auth login` 或设置提供商环境变量（OPENROUTER_API_KEY等）
- 验证：`opencode auth list` 应显示至少一个提供商
- 编码任务需要git仓库（推荐）
- 交互式TUI会话需要 `pty=true`

## 二进制解析（重要）

Shell环境可能解析不同的OpenCode二进制文件。如果您的终端和Hermes之间行为不同，请检查：

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

如有需要，指定明确的二进制路径：

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## 一次性任务

使用 `opencode run` 进行有界的非交互式任务：

```
terminal(command="opencode run '为API调用添加重试逻辑并更新测试'", workdir="~/project")
```

使用 `-f` 附加上下文文件：

```
terminal(command="opencode run '审查此配置的安全问题' -f config.yaml -f .env.example", workdir="~/project")
```

使用 `--thinking` 显示模型思考过程：

```
terminal(command="opencode run '调试为什么CI中测试失败' --thinking", workdir="~/project")
```

强制使用特定模型：

```
terminal(command="opencode run '重构认证模块' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## 交互式会话（后台）

对于需要多次交换的迭代工作，在后台启动TUI：

```
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# 返回session_id

# 发送提示
process(action="submit", session_id="<id>", data="实现OAuth刷新流并添加测试")

# 监控进度
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# 发送后续输入
process(action="submit", session_id="<id>", data="现在添加令牌过期的错误处理")

# 干净退出 — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# 或直接杀死进程
process(action="kill", session_id="<id>")
```

**重要：** 不要使用 `/exit` — 这不是有效的OpenCode命令，会打开智能体选择对话框。使用 Ctrl+C（`\x03`）或 `process(action="kill")` 退出。

### TUI 快捷键

| 键 | 操作 |
|-----|--------|
| `Enter` | 提交消息（如需要按两次） |
| `Tab` | 在智能体之间切换（build/plan） |
| `Ctrl+P` | 打开命令面板 |
| `Ctrl+X L` | 切换会话 |
| `Ctrl+X M` | 切换模型 |
| `Ctrl+X N` | 新建会话 |
| `Ctrl+X E` | 打开编辑器 |
| `Ctrl+C` | 退出OpenCode |

### 恢复会话

退出后，OpenCode会打印会话ID。恢复方式：

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # 继续上次会话
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # 指定会话
```

## 常用参数

| 参数 | 用途 |
|------|-----|
| `run '提示词'` | 一次性执行并退出 |
| `--continue` / `-c` | 继续上次OpenCode会话 |
| `--session <id>` / `-s` | 继续特定会话 |
| `--agent <name>` | 选择OpenCode智能体（build或plan） |
| `--model provider/model` | 强制使用特定模型 |
| `--format json` | 机器可读输出/事件 |
| `--file <path>` / `-f` | 附加文件到消息 |
| `--thinking` | 显示模型思考块 |
| `--variant <level>` | 推理努力程度（high, max, minimal） |
| `--title <name>` | 命名会话 |
| `--attach <url>` | 连接到运行中的opencode服务器 |

## 操作流程

1. 验证工具就绪：
   - `terminal(command="opencode --version")`
   - `terminal(command="opencode auth list")`
2. 对于有界任务，使用 `opencode run '...'`（不需要pty）。
3. 对于迭代任务，使用 `background=true, pty=true` 启动 `opencode`。
4. 使用 `process(action="poll"|"log")` 监控长时间任务。
5. 如果OpenCode请求输入，通过 `process(action="submit", ...)` 响应。
6. 使用 `process(action="write", data="\x03")` 或 `process(action="kill")` 退出。
7. 向用户总结文件更改、测试结果和后续步骤。

## PR审查工作流

OpenCode有内置的PR命令：

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

或在临时克隆中进行隔离审查：

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run '审查此PR与main的对比。报告bug、安全风险、测试缺口和风格问题。' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## 并行工作模式

使用独立的工作目录/worktree避免冲突：

```
terminal(command="opencode run '修复问题#101并提交'", workdir="/tmp/issue-101", background=true, pty=true)
terminal(command="opencode run '添加解析器回归测试并提交'", workdir="/tmp/issue-102", background=true, pty=true)
process(action="list")
```

## 会话与成本管理

列出历史会话：

```
terminal(command="opencode session list")
```

检查令牌使用量和费用：

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

## 常见问题

- 交互式 `opencode`（TUI）会话需要 `pty=true`。`opencode run` 命令不需要pty。
- `/exit` 不是有效命令 — 会打开智能体选择器。使用 Ctrl+C 退出TUI。
- PATH不匹配可能选择错误的OpenCode二进制文件/模型配置。
- 如果OpenCode卡住，在杀死前检查日志：
  - `process(action="log", session_id="<id>")`
- 避免在并行OpenCode会话间共享工作目录。
- TUI中Enter可能需要按两次才能提交（一次确认文本，一次发送）。

## 验证

冒烟测试：

```
terminal(command="opencode run '正好回复：OPENCODE_SMOKE_OK'")
```

成功标准：
- 输出包含 `OPENCODE_SMOKE_OK`
- 命令退出时无提供商/模型错误
- 对于编码任务：预期文件已更改且测试通过

## 规则

1. 优先使用 `opencode run` 进行一次性自动化 — 更简单且不需要pty。
2. 仅在需要迭代时使用交互式后台模式。
3. 始终将OpenCode会话限定在单个仓库/工作目录内。
4. 对于长时间任务，通过 `process` 日志提供进度更新。
5. 报告具体结果（更改的文件、测试、剩余风险）。
6. 使用Ctrl+C或kill退出交互式会话，永远不要使用 `/exit`。

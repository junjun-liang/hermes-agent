---
name: codex
description: 将编码任务委托给OpenAI Codex CLI智能体。用于构建功能、重构、PR审查和批量问题修复。需要安装codex CLI和一个git仓库。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [编码智能体, Codex, OpenAI, 代码审查, 重构]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

通过Hermes终端将编码任务委托给 [Codex](https://github.com/openai/codex)。Codex是OpenAI的自主编码智能体CLI。

## 前置条件

- 安装Codex：`npm install -g @openai/codex`
- 已配置OpenAI API密钥
- **必须在git仓库内运行** — Codex拒绝在git仓库外运行
- 在终端调用中使用 `pty=true` — Codex是一个交互式终端应用

## 一次性任务

```
terminal(command="codex exec '在设置中添加深色模式开关'", workdir="~/project", pty=true)
```

用于临时工作（Codex需要git仓库）：
```
terminal(command="cd $(mktemp -d) && git init && codex exec '用Python构建贪吃蛇游戏'", pty=true)
```

## 后台模式（长时间任务）

```
# 在后台启动并带PTY
terminal(command="codex exec --full-auto '重构认证模块'", workdir="~/project", background=true, pty=true)
# 返回session_id

# 监控进度
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# 如果Codex提问，发送输入
process(action="submit", session_id="<id>", data="yes")

# 如需要可终止
process(action="kill", session_id="<id>")
```

## 关键参数

| 参数 | 效果 |
|------|------|
| `exec "提示词"` | 一次性执行，完成后退出 |
| `--full-auto` | 沙箱化但自动批准工作区内的文件更改 |
| `--yolo` | 无沙箱，无审批（最快，最危险） |

## PR审查

克隆到临时目录进行安全审查：

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## 使用Worktrees并行修复问题

```
# 创建worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# 在每个worktree中启动Codex
terminal(command="codex --yolo exec '修复问题#78：<描述>。完成后提交。'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --yolo exec '修复问题#99：<描述>。完成后提交。'", workdir="/tmp/issue-99", background=true, pty=true)

# 监控
process(action="list")

# 完成后，推送并创建PR
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# 清理
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## 批量PR审查

```
# 获取所有PR引用
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# 并行审查多个PR
terminal(command="codex exec '审查PR #86。git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec '审查PR #87。git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# 发布结果
terminal(command="gh pr comment 86 --body '<审查意见>'", workdir="~/project")
```

## 规则

1. **始终使用 `pty=true`** — Codex是交互式终端应用，没有PTY会挂起
2. **必须有git仓库** — Codex不会在git目录外运行。使用 `mktemp -d && git init` 进行临时工作
3. **一次性任务使用 `exec`** — `codex exec "提示词"` 运行并干净退出
4. **构建时使用 `--full-auto`** — 自动批准沙箱内的更改
5. **长时间任务使用后台模式** — 使用 `background=true` 并通过 `process` 工具监控
6. **不要干扰** — 使用 `poll`/`log` 监控，对长时间运行的任务保持耐心
7. **可以并行运行** — 批量工作时同时运行多个Codex进程

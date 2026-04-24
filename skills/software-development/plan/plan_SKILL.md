---
name: plan
description: Hermes 的计划模式 — 检查上下文、将 markdown 计划写入活跃工作区的 `.hermes/plans/` 目录，不执行工作。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow]
    related_skills: [writing-plans, subagent-driven-development]
---

# 计划模式

当用户想要计划而不是执行时使用此技能。

## 核心行为

在此轮次中，你只进行计划。

- 不要实现代码。
- 不要编辑项目文件，除了计划 markdown 文件。
- 不要运行修改型终端命令、提交、推送或执行外部操作。
- 你可以在需要时使用只读命令/工具检查仓库或其他上下文。
- 你的交付物是保存在活跃工作区 `.hermes/plans/` 目录下的 markdown 计划。

## 输出要求

编写具体且可执行的 markdown 计划。

在适当时包含：
- 目标
- 当前上下文 / 假设
- 提议的方法
- 分步计划
- 可能更改的文件
- 测试 / 验证
- 风险、权衡和未决问题

如果任务与代码相关，包含确切的文件路径、可能的测试目标和验证步骤。

## 保存位置

使用 `write_file` 将计划保存在：
- `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`

将其视为相对于活跃工作目录 / 后端工作区。Hermes 文件工具是后端感知的，因此使用此相对路径可以在本地、docker、ssh、modal 和 daytona 后端上保持计划与工作区在一起。

如果运行时提供了特定目标路径，使用该确切路径。
如果没有，自己在 `.hermes/plans/` 下创建合理的时间戳文件名。

## 交互风格

- 如果请求足够清晰，直接编写计划。
- 如果 `/plan` 没有附带明确指令，从当前对话上下文推断任务。
- 如果确实规格不足，问一个简短的澄清问题而不是猜测。
- 保存计划后，简要回复你计划了什么以及保存路径。

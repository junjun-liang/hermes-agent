---
name: apple-reminders
description: 通过remindctl CLI管理Apple Reminders（列表、添加、完成、删除）。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [提醒事项, 任务, 待办, macOS, Apple]
prerequisites:
  commands: [remindctl]
---

# Apple Reminders（苹果提醒事项）

使用 `remindctl` 直接从终端管理 Apple Reminders。任务通过 iCloud 在所有 Apple 设备间同步。

## 前置条件

- **macOS** 系统，已安装 Reminders.app
- 安装：`brew install steipete/tap/remindctl`
- 根据提示授予 Reminders 权限
- 检查：`remindctl status` / 请求授权：`remindctl authorize`

## 使用场景

- 用户提到"提醒"或"提醒事项应用"
- 创建带有到期日期的个人待办事项并同步到 iOS
- 管理 Apple Reminders 列表
- 用户希望任务出现在其 iPhone/iPad 上

## 不使用场景

- 调度智能体警报 → 改用 cronjob 工具
- 日历事件 → 使用 Apple Calendar 或 Google Calendar
- 项目任务管理 → 使用 GitHub Issues、Notion 等
- 如果用户说"提醒我"但意指智能体警报 → 先确认澄清

## 快速参考

### 查看提醒事项

```bash
remindctl                    # 今天的提醒事项
remindctl today              # 今天
remindctl tomorrow           # 明天
remindctl week               # 本周
remindctl overdue            # 已过期
remindctl all                # 全部
remindctl 2026-01-04         # 特定日期
```

### 管理列表

```bash
remindctl list               # 列出所有列表
remindctl list Work          # 显示特定列表
remindctl list Projects --create    # 创建列表
remindctl list Work --delete        # 删除列表
```

### 创建提醒事项

```bash
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"
```

### 完成 / 删除

```bash
remindctl complete 1 2 3          # 按ID完成
remindctl delete 4A83 --force     # 按ID删除
```

### 输出格式

```bash
remindctl today --json       # JSON格式，用于脚本
remindctl today --plain      # TSV格式
remindctl today --quiet      # 仅计数
```

## 日期格式

`--due` 和日期过滤器接受的格式：
- `today`、`tomorrow`、`yesterday`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:mm`
- ISO 8601（`2026-01-04T12:34:56Z`）

## 规则

1. 当用户说"提醒我"时，先确认澄清：Apple Reminders（同步到手机）还是智能体cronjob警报
2. 创建前始终确认提醒事项内容和到期日期
3. 使用 `--json` 进行程序化解析

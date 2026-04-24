---
name: imessage
description: 通过 macOS 上的 imsg CLI 发送和接收 iMessage/SMS。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [iMessage, SMS, 消息, macOS, Apple]
prerequisites:
  commands: [imsg]
---

# iMessage

使用 `imsg` 通过 macOS Messages.app 读取和发送 iMessage/SMS。

## 前提条件

- **macOS** 并已登录 Messages.app
- 安装：`brew install steipete/tap/imsg`
- 为终端授予完全磁盘访问权限（系统设置 → 隐私 → 完全磁盘访问）
- 提示时授予 Messages.app 自动化权限

## 何时使用

- 用户要求发送 iMessage 或短信
- 读取 iMessage 对话历史
- 检查最近的 Messages.app 聊天
- 发送到电话号码或 Apple ID

## 何时不使用

- Telegram/Discord/Slack/WhatsApp 消息 → 使用适当的网关通道
- 群聊管理（添加/移除成员）→ 不支持
- 批量/群发消息 → 始终先与用户确认

## 快速参考

### 列出聊天

```bash
imsg chats --limit 10 --json
```

### 查看历史

```bash
# 按聊天 ID
imsg history --chat-id 1 --limit 20 --json

# 带附件信息
imsg history --chat-id 1 --limit 20 --attachments --json
```

### 发送消息

```bash
# 仅文本
imsg send --to "+14155551212" --text "Hello!"

# 带附件
imsg send --to "+14155551212" --text "Check this out" --file /path/to/image.jpg

# 强制 iMessage 或 SMS
imsg send --to "+14155551212" --text "Hi" --service imessage
imsg send --to "+14155551212" --text "Hi" --service sms
```

### 监控新消息

```bash
imsg watch --chat-id 1 --attachments
```

## 服务选项

- `--service imessage`——强制 iMessage（要求接收者有 iMessage）
- `--service sms`——强制 SMS（绿色气泡）
- `--service auto`——让 Messages.app 决定（默认）

## 规则

1. **发送前始终确认收件人和消息内容**
2. **未经用户明确批准，绝不向陌生号码发送消息**
3. **附加文件前验证文件路径**是否存在
4. **不要垃圾信息**——自我限速

## 示例工作流

用户："给妈妈发短信说我会晚到"

```bash
# 1. 找到妈妈的聊天
imsg chats --limit 20 --json | jq '.[] | select(.displayName | contains("Mom"))'

# 2. 与用户确认："找到妈妈在 +1555123456。发送'I'll be late'通过 iMessage？"

# 3. 确认后发送
imsg send --to "+1555123456" --text "I'll be late"
```

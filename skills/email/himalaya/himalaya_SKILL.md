---
name: himalaya
description: 通过IMAP/SMTP CLI管理邮件。使用himalaya从终端列出、读取、编写、回复、转发、搜索和组织邮件。支持多账户和使用MML（MIME元语言）编写消息。
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, 通信]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya是一个CLI邮件客户端，允许您使用IMAP、SMTP、Notmuch或Sendmail后端从终端管理邮件。

## 参考资料

- `references/configuration.md`（配置文件设置 + IMAP/SMTP认证）
- `references/message-composition.md`（编写邮件的MML语法）

## 前置条件

1. 已安装Himalaya CLI（`himalaya --version` 验证）
2. 在 `~/.config/himalaya/config.toml` 有配置文件
3. 已配置IMAP/SMTP凭证（密码安全存储）

### 安装

```bash
# 预编译二进制（Linux/macOS — 推荐）
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# 或通过cargo（任何有Rust的平台）
cargo install himalaya --locked
```

## 配置设置

运行交互式向导设置账户：

```bash
himalaya account configure
```

或手动创建 `~/.config/himalaya/config.toml`：

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # 或使用keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"
```

## Hermes集成说明

- **读取、列出、搜索、移动、删除** 都可以直接通过终端工具运行
- **编写/回复/转发** — 建议使用管道输入（`cat << EOF | himalaya template send`）以确保可靠性。交互式`$EDITOR`模式可与`pty=true` + 后台模式 + 进程工具配合使用，但需要知道编辑器及其命令
- 使用 `--output json` 获取结构化输出，更容易程序化解析
- `himalaya account configure` 向导需要交互式输入 — 使用PTY模式：`terminal(command="himalaya account configure", pty=true)`

## 常用操作

### 列出文件夹

```bash
himalaya folder list
```

### 列出邮件

列出收件箱中的邮件（默认）：

```bash
himalaya envelope list
```

列出特定文件夹中的邮件：

```bash
himalaya envelope list --folder "Sent"
```

分页列出：

```bash
himalaya envelope list --page 1 --page-size 20
```

### 搜索邮件

```bash
himalaya envelope list from john@example.com subject meeting
```

### 读取邮件

按ID读取邮件（显示纯文本）：

```bash
himalaya message read 42
```

导出原始MIME：

```bash
himalaya message export 42 --full
```

### 回复邮件

从Hermes非交互式回复 — 读取原始消息、编写回复并管道：

```bash
# 获取回复模板、编辑并发送
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

或手动构建回复：

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

全部回复（交互式 — 需要$EDITOR，改用上面的模板方式）：

```bash
himalaya message reply 42 --all
```

### 转发邮件

```bash
# 获取转发模板并通过管道修改
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### 编写新邮件

**非交互式（从Hermes使用此方式）** — 通过stdin管道消息：

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

或使用headers标志：

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

注意：没有管道输入时 `himalaya message write` 会打开 `$EDITOR`。这可以与 `pty=true` + 后台模式配合使用，但管道更简单可靠。

### 移动/复制邮件

移动到文件夹：

```bash
himalaya message move 42 "Archive"
```

复制到文件夹：

```bash
himalaya message copy 42 "Important"
```

### 删除邮件

```bash
himalaya message delete 42
```

### 管理标志

添加标志：

```bash
himalaya flag add 42 --flag seen
```

移除标志：

```bash
himalaya flag remove 42 --flag seen
```

## 多账户

列出账户：

```bash
himalaya account list
```

使用特定账户：

```bash
himalaya --account work envelope list
```

## 附件

从消息保存附件：

```bash
himalaya attachment download 42
```

保存到特定目录：

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## 输出格式

大多数命令支持 `--output` 用于结构化输出：

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## 调试

启用调试日志：

```bash
RUST_LOG=debug himalaya envelope list
```

完整跟踪和回溯：

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## 提示

- 使用 `himalaya --help` 或 `himalaya <command> --help` 获取详细用法
- 消息ID相对于当前文件夹；更改文件夹后重新列出
- 编写带附件的富文本邮件时，使用MML语法（见 `references/message-composition.md`）
- 使用 `pass`、系统keyring或输出密码的命令安全存储密码

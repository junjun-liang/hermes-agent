---
name: google-workspace
description: 通过 gws CLI（googleworkspace/cli）实现 Gmail、日历、云端硬盘、通讯录、表格和文档集成。使用 OAuth2，通过桥接脚本自动刷新令牌。需要 gws 二进制文件。
version: 2.0.0
author: Nous Research
license: MIT
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 令牌（由安装脚本创建）
  - path: google_client_secret.json
    description: Google OAuth2 客户端凭据（从 Google Cloud Console 下载）
metadata:
  hermes:
    tags: [Google, Gmail, 日历, 云端硬盘, 表格, 文档, 通讯录, 邮件, OAuth, gws]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail、日历、云端硬盘、通讯录、表格和文档——由 `gws`（Google 官方 Rust CLI）驱动。本技能提供向后兼容的 Python 封装，处理 OAuth 令牌刷新并委托给 `gws`。

## 架构

```
google_api.py  →  gws_bridge.py  →  gws CLI
（argparse 兼容）  （令牌刷新）        （Google API）
```

- `setup.py` 处理 OAuth2（无头兼容模式，适用于 CLI/Telegram/Discord）
- `gws_bridge.py` 刷新 Hermes 令牌并通过 `GOOGLE_WORKSPACE_CLI_TOKEN` 注入到 `gws`
- `google_api.py` 提供与 v1 相同的 CLI 接口，但委托给 `gws`

## 参考

- `references/gmail-search-syntax.md`——Gmail 搜索运算符（is:unread、from:、newer_than: 等）

## 脚本

- `scripts/setup.py`——OAuth2 安装（运行一次以授权）
- `scripts/gws_bridge.py`——令牌刷新桥接到 gws CLI
- `scripts/google_api.py`——向后兼容的 API 封装器（委托给 gws）

## 前提条件

安装 `gws`：

```bash
cargo install google-workspace-cli
# 或通过 npm（推荐，下载预编译二进制）：
npm install -g @googleworkspace/cli
# 或通过 Homebrew：
brew install googleworkspace-cli
```

验证：`gws --version`

## 首次安装

安装完全非交互——你逐步驱动它，使其适用于 CLI、Telegram、Discord 或任何平台。

首先定义快捷方式：

```bash
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
GWORKSPACE_SKILL_DIR="$HERMES_HOME/skills/productivity/google-workspace"
PYTHON_BIN="${HERMES_PYTHON:-python3}"
if [ -x "$HERMES_HOME/hermes-agent/venv/bin/python" ]; then
  PYTHON_BIN="$HERMES_HOME/hermes-agent/venv/bin/python"
fi
GSETUP="$PYTHON_BIN $GWORKSPACE_SKILL_DIR/scripts/setup.py"
```

### 步骤 0：检查是否已安装

```bash
$GSETUP --check
```

如果打印 `AUTHENTICATED`，跳转到使用说明——安装已经完成。

### 步骤 1：分类——询问用户需要什么

**问题 1："你需要哪些 Google 服务？仅邮件，还是也包括日历/云端硬盘/表格/文档？"**

- **仅邮件**→ 改用 `himalaya` 技能——安装更简单。
- **日历、云端硬盘、表格、文档（或邮件 + 这些）**→ 继续下面。

**部分范围**：用户可以仅授权部分服务。安装脚本接受部分范围并警告缺失的服务。

**问题 2："你的 Google 账户是否使用高级保护？"**

- **否 / 不确定**→ 正常安装。
- **是**→ Workspace 管理员必须先将 OAuth 客户端 ID 添加到允许的应用。

### 步骤 2：创建 OAuth 凭据（一次性，约 5 分钟）

告诉用户：

> 1. 前往 https://console.cloud.google.com/apis/credentials
> 2. 创建项目（或使用现有项目）
> 3. 启用你需要的 API（Gmail、日历、云端硬盘、表格、文档、People）
> 4. 凭据 → 创建凭据 → OAuth 2.0 客户端 ID → 桌面应用
> 5. 下载 JSON 并告诉我文件路径

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

### 步骤 3：获取授权 URL

```bash
$GSETUP --auth-url
```

将 URL 发送给用户。授权后，他们会粘贴回重定向 URL 或代码。

### 步骤 4：交换代码

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED"
```

### 步骤 5：验证

```bash
$GSETUP --check
```

应打印 `AUTHENTICATED`。令牌从现在起自动刷新。

## 使用方法

所有命令都通过 API 脚本执行：

```bash
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
GWORKSPACE_SKILL_DIR="$HERMES_HOME/skills/productivity/google-workspace"
PYTHON_BIN="${HERMES_PYTHON:-python3}"
if [ -x "$HERMES_HOME/hermes-agent/venv/bin/python" ]; then
  PYTHON_BIN="$HERMES_HOME/hermes-agent/venv/bin/python"
fi
GAPI="$PYTHON_BIN $GWORKSPACE_SKILL_DIR/scripts/google_api.py"
```

### Gmail

```bash
$GAPI gmail search "is:unread" --max 10
$GAPI gmail get MESSAGE_ID
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1>" --html
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
```

### 日历

```bash
$GAPI calendar list
$GAPI calendar create --summary "Standup" --start 2026-03-01T10:00:00+01:00 --end 2026-03-01T10:30:00+01:00
$GAPI calendar create --summary "Review" --start ... --end ... --attendees "alice@co.com,bob@co.com"
$GAPI calendar delete EVENT_ID
```

### 云端硬盘

```bash
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5
```

### 通讯录

```bash
$GAPI contacts list --max 20
```

### 表格

```bash
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### 文档

```bash
$GAPI docs get DOC_ID
```

### 直接访问 gws（高级）

对于封装器未涵盖的操作，直接使用 `gws_bridge.py`：

```bash
GBRIDGE="$PYTHON_BIN $GWORKSPACE_SKILL_DIR/scripts/gws_bridge.py"
$GBRIDGE calendar +agenda --today --format table
$GBRIDGE gmail +triage --labels --format json
$GBRIDGE drive +upload ./report.pdf
$GBRIDGE sheets +read --spreadsheet SHEET_ID --range "Sheet1!A1:D10"
```

## 输出格式

所有命令通过 `gws --format json` 返回 JSON。关键输出结构：

- **Gmail 搜索/分类**：邮件摘要数组（发件人、主题、日期、摘要）
- **Gmail 获取/读取**：包含头部和正文的邮件对象
- **Gmail 发送/回复**：包含邮件 ID 的确认
- **日历列表/日程**：事件对象数组（摘要、开始、结束、位置）
- **日历创建**：包含事件 ID 和 htmlLink 的确认
- **云端硬盘搜索**：文件对象数组（id、名称、mimeType、webViewLink）
- **表格获取/读取**：单元格值的二维数组
- **文档获取**：完整文档 JSON（使用 `body.content` 提取文本）
- **通讯录列表**：包含姓名、邮件、电话的人员对象数组

使用 `jq` 解析输出或直接读取 JSON。

## 规则

1. **未经用户确认，绝不发送邮件或创建/删除事件。**
2. **首次使用前检查授权**——运行 `setup.py --check`。
3. **复杂查询使用 Gmail 搜索语法参考。**
4. **日历时间必须包含时区**——ISO 8601 带偏移或 UTC。
5. **遵守速率限制**——避免快速连续 API 调用。

## 故障排除

| 问题 | 修复 |
|---------|-----|
| `NOT_AUTHENTICATED` | 运行安装步骤 2-5 |
| `REFRESH_FAILED` | 令牌被撤销——重新执行步骤 3-5 |
| `gws: command not found` | 安装：`npm install -g @googleworkspace/cli` |
| `HttpError 403` | 缺少范围——`$GSETUP --revoke` 然后重新执行步骤 3-5 |
| `HttpError 403: Access Not Configured` | 在 Google Cloud Console 中启用 API |
| 高级保护阻止授权 | 管理员必须将 OAuth 客户端 ID 加入白名单 |

## 撤销访问

```bash
$GSETUP --revoke
```

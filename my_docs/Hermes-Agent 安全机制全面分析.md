# Hermes-Agent 安全机制全面分析

> 分析日期：2026-04-14 | 项目版本：基于当前代码库快照

***

## 目录

1. [安全架构总览](#1-安全架构总览)
2. [认证与凭据管理](#2-认证与凭据管理)
3. [敏感信息脱敏系统](#3-敏感信息脱敏系统)
4. [工具执行安全机制](#4-工具执行安全机制)
5. [代码执行沙箱](#5-代码执行沙箱)
6. [子代理委托安全边界](#6-子代理委托安全边界)
7. [会话与数据存储安全](#7-会话与数据存储安全)
8. [网络通信安全](#8-网络通信安全)
9. [文件操作安全](#9-文件操作安全)
10. [配置与环境隔离](#10-配置与环境隔离)
11. [技能安全扫描](#11-技能安全扫描)
12. [安全评估与风险矩阵](#12-安全评估与风险矩阵)

***

## 1. 安全架构总览

Hermes-Agent 采用\*\*纵深防御（Defense in Depth）\*\*策略，在多个独立层面实施安全控制，即使某一层被绕过，下一层仍能提供保护。

```
┌─────────────────────────────────────────────────────────────┐
│                     用户输入 / LLM 工具调用                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 1 层：工具注册权限检查 (registry.py)                       │
│  ├─ check_fn → 运行时可用性检查                               │
│  └─ requires_env → 环境变量存在性检查                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 2 层：命令安全检测 (approval.py)                           │
│  ├─ Tirith 安全扫描（内容级威胁）                              │
│  ├─ DANGEROUS_PATTERNS 正则（30+ 语法级模式）                  │
│  ├─ 命令归一化（反混淆：ANSI/null/Unicode）                    │
│  ├─ 审批模式 (manual / smart / off)                          │
│  └─ workdir 白名单验证（防 shell 注入）                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 3 层：执行环境隔离                                         │
│  ├─ Docker: cap-drop ALL, no-new-privileges, PID/tmpfs 限制  │
│  ├─ 环境变量过滤（60+ 敏感变量黑名单）                          │
│  ├─ 技能/用户放行白名单                                       │
│  └─ Profile HOME 隔离                                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 4 层：子代理安全边界 (delegate_tool.py)                    │
│  ├─ 工具黑名单（5 个禁止工具）                                 │
│  ├─ 委托深度限制 (MAX_DEPTH=2)                                │
│  ├─ 工具集交集限制                                            │
│  ├─ 并发数量限制（默认 3）                                     │
│  └─ 上下文完全隔离                                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 5 层：代码执行沙箱 (code_execution_tool.py)               │
│  ├─ 工具白名单（7 个工具）                                    │
│  ├─ 终端参数黑名单                                            │
│  ├─ 资源限制（超时/调用数/输出大小）                            │
│  ├─ 进程组隔离 + 强制终止                                     │
│  └─ 环境变量三层过滤                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 6 层：输出安全处理                                         │
│  ├─ ANSI 转义剥离                                            │
│  ├─ 敏感数据脱敏 (redact.py — 8 层规则)                       │
│  └─ 输出截断（50KB 上限）                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 7 层：网络通信安全                                         │
│  ├─ SSRF 防护（is_safe_url + 重定向守卫 + CGNAT 覆盖）        │
│  ├─ URL 密钥外泄阻断                                         │
│  ├─ Webhook HMAC 签名验证                                    │
│  ├─ 多实例凭据锁（PID + 启动时间验证）                         │
│  └─ 用户授权（多层递进 + 默认拒绝）                            │
└─────────────────────────────────────────────────────────────┘
```

***

## 2. 认证与凭据管理

### 2.1 多提供者认证体系

核心文件：[hermes\_cli/auth.py](hermes_cli/auth.py)

系统通过 `PROVIDER_REGISTRY` 支持四种认证类型：

| 认证类型                | 提供者                                         | 机制                                   |
| ------------------- | ------------------------------------------- | ------------------------------------ |
| `oauth_device_code` | Nous Portal                                 | OAuth 2.0 Device Authorization Grant |
| `oauth_external`    | OpenAI Codex, Qwen                          | 外部 OAuth 凭据读取/刷新                     |
| `api_key`           | Anthropic, Gemini, GitHub Copilot, Z.AI/GLM | 环境变量优先级链                             |
| `external_process`  | Copilot ACP                                 | 子进程认证                                |

**环境变量优先级链**：每个 API Key 提供者定义了环境变量查找优先级，第一个有效值即被采用。例如：

- Anthropic: `ANTHROPIC_API_KEY` > `ANTHROPIC_TOKEN` > `CLAUDE_CODE_OAUTH_TOKEN`
- GitHub Copilot: `COPILOT_GITHUB_TOKEN` > `GH_TOKEN` > `GITHUB_TOKEN`

**安全设计**：`CLAUDE_CODE_OAUTH_TOKEN` 被标记为隐式环境变量，不参与自动提供者选择，防止 Claude Code 自身设置的环境变量劫持 Hermes 的提供者选择。GitHub 令牌（`GH_TOKEN`/`GITHUB_TOKEN`）也被显式排除在自动选择之外。

### 2.2 占位符密钥检测

系统维护了占位符值黑名单，防止用户误用无效凭据：

```python
_PLACEHOLDER_SECRET_VALUES = {
    "*", "**", "***", "changeme", "your_api_key",
    "your-api-key", "placeholder", "example", "dummy", "null", "none",
}
```

所有凭据解析路径都通过 `has_usable_secret()` 过滤，确保占位符值不会被当作有效凭据。

### 2.3 OAuth Token 刷新机制

| 提供者          | 刷新策略                                         | 安全措施                            |
| ------------ | -------------------------------------------- | ------------------------------- |
| Nous Portal  | Access Token 提前 2 分钟刷新；Agent Key 最短 30 分钟有效期 | 刷新后立即持久化，防崩溃丢失                  |
| OpenAI Codex | 独立 OAuth 会话，与 Codex CLI/VS Code 隔离           | 刷新后回写 `~/.codex/auth.json` 保持同步 |
| Qwen         | 读取 `~/.qwen/oauth_creds.json`，支持自动刷新         | 文件权限 0600                       |

**关键安全措施**：

- Token 存储在 `~/.hermes/auth.json`（而非其他应用的目录），防止 refresh token 旋转冲突
- `refresh_token_reused` 错误被特别处理，提供明确的用户指导
- 刷新后立即持久化状态，防止崩溃导致 refresh\_token 旋转丢失

### 2.4 凭据持久化安全

#### 跨进程文件锁

所有对 `~/.hermes/auth.json` 的读写通过 `_auth_store_lock()` 保护：

- 使用 `fcntl.flock`（Linux/macOS）或 `msvcrt.locking`（Windows）实现跨进程文件锁
- 可重入设计（同一线程多次获取锁不会死锁）
- 默认 15 秒超时

#### 原子写入

```python
# 先写临时文件，再原子替换
tmp_path = auth_path.with_suffix(f".tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}")
# ... 写入 + fsync ...
os.replace(tmp_path, auth_path)  # 原子操作
```

写入后 `fsync` 确保数据落盘（包括目录 fsync）。

#### 文件权限

| 文件                         | 权限     | 说明      |
| -------------------------- | ------ | ------- |
| `~/.hermes/auth.json`      | `0600` | 仅所有者可读写 |
| `~/.hermes/.env`           | `0600` | 仅所有者可读写 |
| `~/.hermes/` 目录            | `0700` | 仅所有者可访问 |
| `~/.qwen/oauth_creds.json` | `0600` | 仅所有者可读写 |

#### HERMES\_HOME 目录权限

```python
def _secure_dir(path):
    mode = int(os.environ.get("HERMES_HOME_MODE", "0700"), 8)
    os.chmod(path, mode)
```

NixOS 管理模式下使用 0750（组可读），允许 `hermes` 组的交互用户共享状态。

### 2.5 密码输入安全

- 所有标记为 `password: True` 的凭据输入使用 `getpass.getpass()`，不在终端回显
- 涵盖所有平台：Telegram Bot Token、Discord Bot Token、Slack Bot/App Token、Matrix Access Token/Password、Webhook HMAC Secret、Sudo Password

### 2.6 凭据分类体系

`OPTIONAL_ENV_VARS` 中所有环境变量按 `category` 分为四类：

| 类别          | 用途        | 示例                                                           |
| ----------- | --------- | ------------------------------------------------------------ |
| `provider`  | 推理提供者凭据   | `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`                    |
| `tool`      | 工具 API 密钥 | `EXA_API_KEY`, `FIRECRAWL_API_KEY`, `TAVILY_API_KEY`         |
| `messaging` | 消息平台令牌    | `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, `SLACK_BOT_TOKEN` |
| `setting`   | 代理设置      | `SUDO_PASSWORD`, `HERMES_MAX_ITERATIONS`                     |

标记为 `"advanced": True` 的变量在常规设置流程中不显示。

***

## 3. 敏感信息脱敏系统

核心文件：[agent/redact.py](agent/redact.py)

### 3.1 脱敏引擎架构

`redact_sensitive_text()` 函数依次应用 **8 层**脱敏规则：

| 层次 | 模式                   | 示例输入                              | 脱敏结果                          |
| -- | -------------------- | --------------------------------- | ----------------------------- |
| 1  | 已知 API Key 前缀（30+ 种） | `sk-proj-abc123def456`            | `sk-pro...f456`               |
| 2  | ENV 赋值               | `OPENAI_API_KEY=sk-xxx`           | `OPENAI_API_KEY=sk-pr...xxxx` |
| 3  | JSON 字段              | `"apiKey": "value"`               | `"apiKey": "valu...alue"`     |
| 4  | Authorization 头      | `Bearer sk-xxx`                   | `Bearer sk-pr...xxxx`         |
| 5  | Telegram Bot Token   | `bot123456789:ABCDE...`           | `123456789:***`               |
| 6  | 私钥块                  | `-----BEGIN RSA PRIVATE KEY-----` | `[REDACTED PRIVATE KEY]`      |
| 7  | 数据库连接串               | `postgres://user:pass@host`       | `postgres://user:***@host`    |
| 8  | E.164 电话号码           | `+8613800138000`                  | `+8613****8000`               |

### 3.2 已知 API Key 前缀模式

覆盖 **30+ 种**服务提供商的密钥格式：

- OpenAI/OpenRouter/Anthropic: `sk-[A-Za-z0-9_-]{10,}`
- GitHub PAT: `ghp_`, `github_pat_`, `gho_`, `ghu_`, `ghs_`, `ghr_`
- Slack: `xox[baprs]-[A-Za-z0-9-]{10,}`
- Google: `AIza[A-Za-z0-9_-]{30,}`
- AWS: `AKIA[A-Z0-9]{16}`
- Stripe: `sk_live_`, `sk_test_`, `rk_live_`
- SendGrid: `SG\.[A-Za-z0-9_-]{10,}`
- HuggingFace: `hf_[A-Za-z0-9]{10,}`
- 以及 Firecrawl、BrowserBase、Tavily、Exa、Groq、DeepSeek 等

### 3.3 智能遮蔽策略

```python
def _mask_token(token: str) -> str:
    if len(token) < 18:
        return "***"                    # 短 token 完全遮蔽
    return f"{token[:6]}...{token[-4:]}" # 长 token 保留前6后4
```

### 3.4 防运行时篡改

脱敏开关在 **import 时快照**，运行时环境变量变更无法禁用脱敏：

```python
_REDACT_ENABLED = os.getenv("HERMES_REDACT_SECRETS", "").lower() not in ("0", "false", "no", "off")
```

这防止了 LLM 生成的 `export HERMES_REDACT_SECRETS=false` 在会话中途禁用脱敏。

### 3.5 日志自动脱敏

`RedactingFormatter` 作为日志格式化器，自动对所有日志消息执行脱敏，无需每个调用点手动处理：

```python
class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_sensitive_text(original)
```

应用于所有日志 Handler：`agent.log`、`errors.log`、`gateway.log`、控制台输出。

### 3.6 工具输出脱敏覆盖

| 工具                    | 脱敏位置          | 脱敏内容                     |
| --------------------- | ------------- | ------------------------ |
| `terminal_tool`       | 命令输出          | 防止 `env`/`printenv` 泄露密钥 |
| `file_tools`          | 文件读取内容、搜索结果   | 防止读取含密钥的配置文件             |
| `code_execution_tool` | stdout/stderr | 防止沙箱代码打印密钥               |
| `browser_tool`        | 提取文本、分析结果     | 防止网页内容含密钥                |
| `browser_camofox`     | 注释上下文、分析结果    | 同上                       |
| `send_message_tool`   | 错误文本          | 增强版脱敏（额外处理 URL 查询参数）     |
| `cron/scheduler`      | stdout/stderr | 防止定时任务输出泄露密钥             |

### 3.7 OAuth Token 指纹

OAuth 流程的调试日志使用 SHA-256 前 12 字符哈希代替原始 token：

```python
def _token_fingerprint(token: Any) -> Optional[str]:
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:12]
```

### 3.8 API Key 日志遮蔽

多处实现了 `redact_key()` 函数用于配置显示：

```python
def redact_key(key: str) -> str:
    if not key:
        return "(not set)"
    if len(key) < 12:
        return "***"
    return key[:4] + "..." + key[-4:]
```

***

## 4. 工具执行安全机制

核心文件：[tools/approval.py](tools/approval.py)、[tools/terminal\_tool.py](tools/terminal_tool.py)

### 4.1 危险命令检测

`DANGEROUS_PATTERNS` 定义了 **30+ 条**危险命令模式：

| 类别         | 示例模式                                   | 说明                      |
| ---------- | -------------------------------------- | ----------------------- |
| 递归删除       | `rm -r`, `rm --recursive`              | 根路径删除、递归删除              |
| 权限篡改       | `chmod 777`, `chown -R root`           | 世界可写、递归改属主              |
| 磁盘/系统破坏    | `mkfs`, `dd if=`, `> /dev/sd`          | 格式化、磁盘复制、写块设备           |
| SQL 注入/破坏  | `DROP TABLE`, `DELETE FROM`（无 WHERE）   | 数据库破坏性操作                |
| 系统配置覆盖     | `> /etc/`, `sed -i /etc/`, `tee /etc/` | 覆盖系统配置文件                |
| 服务停止       | `systemctl stop/disable/mask`          | 停止/禁用系统服务               |
| Fork 炸弹    | `:(){ :\|:& };:`                       | 经典 fork bomb            |
| Shell 注入   | `bash -c`, `python -e`, `perl -e`      | 通过 -c/-e 标志执行脚本         |
| 远程代码执行     | `curl \| sh`, `bash <(curl`            | 管道远程内容到 shell           |
| 敏感路径写入     | `tee ~/.ssh/`, `> ~/.hermes/.env`      | 覆盖 SSH 密钥或 Hermes 凭证    |
| Git 破坏     | `git reset --hard`, `git push --force` | 破坏未提交更改/强制推送            |
| 自我终止       | `pkill hermes`, `kill $(pgrep hermes)` | 防止 agent 杀死自身进程         |
| Gateway 保护 | `gateway run &`, `nohup gateway run`   | 防止在 systemd 外启动 gateway |

### 4.2 命令归一化（反混淆）

`_normalize_command_for_detection()` 实现三层反混淆：

1. **剥离 ANSI 转义序列** — 防止通过颜色码绕过检测
2. **剥离 null 字节** — 防止 `\x00` 注入
3. **Unicode 归一化（NFKC）** — 防止全角字符绕过（如 `ｒｍ` → `rm`）

### 4.3 审批模式

| 模式           | 行为                    | 适用场景 |
| ------------ | --------------------- | ---- |
| `manual`（默认） | 每次匹配弹出交互式审批           | 安全优先 |
| `smart`      | 辅助 LLM 评估风险，自动批准低风险命令 | 效率优先 |
| `off`        | 跳过所有审批（`--yolo` 模式）   | 完全信任 |

### 4.4 审批状态持久化

| 级别        | 存储                                  | 生命周期    |
| --------- | ----------------------------------- | ------- |
| `once`    | 无                                   | 仅本次执行   |
| `session` | `_session_approved` 字典              | 当前会话    |
| `always`  | `config.yaml` 的 `command_allowlist` | 永久（跨会话） |

### 4.5 容器环境自动放行

Docker/Singularity/Modal/Daytona 环境自动跳过审批，容器被视为安全边界。

### 4.6 综合守卫：Tirith + 危险命令

`check_all_command_guards()` 将两套检测系统合并为**单一审批请求**：

1. **Tirith 安全扫描**（外部二进制）：检测同形字 URL、管道到解释器、终端注入等内容级威胁
2. **DANGEROUS\_PATTERNS 正则**：检测语法级危险命令

### 4.7 终端执行前安全检查链

```
1. 类型检查 → command 必须为 string
2. 安全检查 → check_all_guards() (tirith + 危险命令)
3. workdir 验证 → _validate_workdir() (白名单正则，防 shell 注入)
4. PTY 安全检查 → _command_requires_pipe_stdin() (禁用不兼容 PTY 的命令)
```

### 4.8 workdir 白名单验证

```python
_WORKDIR_SAFE_RE = re.compile(r'^[A-Za-z0-9/_\-.~ +@=,]+$')
```

使用**白名单**而非黑名单验证工作目录，防止通过 workdir 注入 shell 元字符。

### 4.9 sudo 命令安全处理

- 将裸 `sudo` 重写为 `sudo -S -p ''`（从 stdin 读取密码）
- 密码通过 stdin 管道传递，不暴露在命令行参数中
- 会话级密码缓存（`_cached_sudo_password`）

### 4.10 前台超时硬上限

```python
FOREGROUND_MAX_TIMEOUT = int(os.getenv("TERMINAL_MAX_FOREGROUND_TIMEOUT", "600"))
```

前台命令超时超过此上限会被拒绝，引导使用 `background=true`。

***

## 5. 代码执行沙箱

核心文件：[tools/code\_execution\_tool.py](tools/code_execution_tool.py)

### 5.1 工具白名单

```python
SANDBOX_ALLOWED_TOOLS = frozenset([
    "web_search", "web_extract", "read_file", "write_file",
    "search_files", "patch", "terminal",
])
```

沙箱内只能调用这 7 个工具，且实际可用工具是此白名单与当前会话启用工具的**交集**。

### 5.2 终端参数黑名单

```python
_TERMINAL_BLOCKED_PARAMS = {"background", "pty", "notify_on_complete", "watch_patterns"}
```

沙箱内的 `terminal()` 调用禁止使用后台执行、PTY 等参数，防止逃逸。

### 5.3 环境变量三层过滤

```python
_SAFE_ENV_PREFIXES = ("PATH", "HOME", "USER", "LANG", "LC_", "TERM",
                      "TMPDIR", "TMP", "TEMP", "SHELL", "LOGNAME",
                      "XDG_", "PYTHONPATH", "VIRTUAL_ENV", "CONDA")
_SECRET_SUBSTRINGS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL",
                      "PASSWD", "AUTH")
```

过滤优先级：技能放行 > 密钥名阻断 > 安全前缀放行。

### 5.4 资源限制

| 限制项       | 值               |
| --------- | --------------- |
| 默认超时      | 300 秒（5 分钟）     |
| 最大工具调用次数  | 50 次            |
| stdout 上限 | 50,000 字节（50KB） |
| stderr 上限 | 10,000 字节（10KB） |

### 5.5 进程组隔离与强制终止

```python
proc = subprocess.Popen(
    [sys.executable, "script.py"],
    preexec_fn=None if _IS_WINDOWS else os.setsid,  # 新进程组
)
```

`_kill_process_group()` 先 SIGTERM 整个进程组，5 秒后升级为 SIGKILL。

### 5.6 双传输架构

- **本地后端**：Unix Domain Socket (UDS) RPC
- **远程后端**：文件 RPC（请求/响应文件在远程文件系统上交换）

两种传输都强制执行相同的工具白名单和调用次数限制。

***

## 6. 子代理委托安全边界

核心文件：[tools/delegate\_tool.py](tools/delegate_tool.py)

### 6.1 工具黑名单

```python
DELEGATE_BLOCKED_TOOLS = frozenset([
    "delegate_task",   # 禁止递归委托
    "clarify",         # 禁止用户交互
    "memory",          # 禁止写入共享 MEMORY.md
    "send_message",    # 禁止跨平台副作用
    "execute_code",    # 禁止在子代理中写脚本
])
```

### 6.2 委托深度限制

```python
MAX_DEPTH = 2  # parent (0) -> child (1) -> grandchild rejected (2)
```

子代理不能再委托孙代理，防止无限递归。

### 6.3 工具集交集限制

子代理的工具集必须与父代理取**交集**，不能获得父代理没有的工具。

### 6.4 并发子代理数量限制

```python
_DEFAULT_MAX_CONCURRENT_CHILDREN = 3
```

可通过 `delegation.max_concurrent_children` 配置。

### 6.5 上下文隔离

每个子代理获得：

- 全新的对话历史（不继承父代理上下文）
- 独立的 task\_id（独立的终端会话和文件操作缓存）
- `skip_context_files=True` + `skip_memory=True`
- `clarify_callback=None`（不能与用户交互）

***

## 7. 会话与数据存储安全

### 7.1 SQL 注入防护

核心文件：[hermes\_state.py](hermes_state.py)

| 攻击面           | 防护措施                                     |
| ------------- | ---------------------------------------- |
| 数据操作（CRUD）    | 全部使用 `?` 参数化查询                           |
| FTS5 MATCH 查询 | `_sanitize_fts5_query()` + 异常捕获返回空列表     |
| LIKE 通配符      | `%`、`_`、`\` 转义 + ESCAPE 子句               |
| DDL 迁移        | 硬编码列名 + 双引号转义（纵深防御）                      |
| 动态 WHERE 子句   | `",".join("?" for ...)` 构建占位符            |
| 会话标题          | `sanitize_title()` 移除控制字符 + 长度限制（100 字符） |

### 7.2 FTS5 查询清理

`_sanitize_fts5_query()` 实现了 6 步清理：

1. 提取并保护平衡的双引号短语
2. 剥离未匹配的 FTS5 特殊字符（`+{}()^"`）
3. 折叠重复的 `*`
4. 移除悬空的布尔运算符
5. 包装含点号/连字符的未引用术语
6. 恢复受保护的引号短语

即使清理后仍有语法错误，`search_messages` 会捕获 `sqlite3.OperationalError` 并返回空列表。

### 7.3 会话标题清理

`sanitize_title()` 的安全措施：

- 移除 ASCII 控制字符（0x00-0x1F, 0x7F）
- 移除 Unicode 零宽字符、RTL/LTR 覆盖字符
- 折叠空白字符
- 强制长度限制（100 字符）

### 7.4 并发写入安全

`_execute_write()` 实现：

- `BEGIN IMMEDIATE` 事务（在事务开始时获取 WAL 写锁）
- 线程锁 (`threading.Lock`)
- 随机抖动重试（20-150ms），避免写锁护航效应
- 最多 15 次重试

### 7.5 PII 脱敏（网关场景）

[gateway/session.py](gateway/session.py) 实现了平台感知的 PII 脱敏：

```python
_PII_SAFE_PLATFORMS = frozenset({
    Platform.WHATSAPP, Platform.SIGNAL, Platform.TELEGRAM, Platform.BLUEBUBBLES,
})
```

- **WhatsApp/Signal/Telegram** — 启用 PII 脱敏（用户 ID/聊天 ID 哈希为 `user_<12hex>`）
- **Discord/Slack** — 不脱敏（`<@user_id>` 提及机制需要真实 ID）

### 7.6 会话过期机制

`SessionStore` 支持四种过期策略：

| 策略      | 行为          |
| ------- | ----------- |
| `idle`  | 超过指定空闲时间后重置 |
| `daily` | 每天指定时间重置    |
| `both`  | 任一条件满足即重置   |
| `none`  | 永不重置        |

有活跃后台进程的会话**永不重置**。

### 7.7 会话数据持久化

`_save()` 使用原子写入模式：

```python
fd, tmp_path = tempfile.mkstemp(dir=str(self.sessions_dir), suffix=".tmp", prefix=".sessions_")
# ... 写入 + fsync ...
os.replace(tmp_path, sessions_file)  # 原子替换
```

### 7.8 会话清理

`prune_sessions()` 默认保留 90 天，只清理已结束的会话，子会话被孤立而非级联删除。

***

## 8. 网络通信安全

### 8.1 SSRF 防护

核心文件：[tools/url\_safety.py](tools/url_safety.py)

```python
_BLOCKED_HOSTNAMES = frozenset({
    "metadata.google.internal",   # GCP 元数据端点
    "metadata.goog",
})

_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")  # CGNAT/Tailscale/VPN
```

**关键设计决策**：

- **失败关闭（fail-closed）**：DNS 解析失败或意外异常均阻止请求
- **CGNAT 覆盖**：显式阻止 100.64.0.0/10（Tailscale/WireGuard VPN 常用范围）
- 阻止私有 IP、回环地址、链路本地地址、保留地址、组播地址

### 8.2 重定向 SSRF 防护

[gateway/platforms/base.py](gateway/platforms/base.py) 实现了重定向链验证：

```python
async def _ssrf_redirect_guard(response):
    if response.is_redirect and response.next_request:
        redirect_url = str(response.next_request.url)
        if not is_safe_url(redirect_url):
            raise ValueError("Blocked redirect to private/internal address")
```

应用于图片缓存下载、音频缓存下载、视觉工具 URL 获取。

### 8.3 URL 日志脱敏

`safe_url_for_log()` 确保日志中不泄露凭据：

- 剥离嵌入凭据（`user:pass@host`）
- 只保留 `scheme://host/.../basename`
- 移除查询参数和片段

### 8.4 URL 密钥外泄阻断

[tools/web\_tools.py](tools/web_tools.py) 和 [tools/browser\_tool.py](tools/browser_tool.py) 阻断包含密钥的 URL：

```python
from agent.redact import _PREFIX_RE
from urllib.parse import unquote

if _PREFIX_RE.search(url) or _PREFIX_RE.search(unquote(url)):
    return json.dumps({
        "success": False,
        "error": "Blocked: URL contains what appears to be an API key or token.",
    })
```

同时检查 URL 编码形式，防止 `%73k-` 编码绕过。

### 8.5 浏览器 SSRF 分层策略

```python
# 仅对云后端生效（Browserbase/BrowserUse），本地后端跳过
if not _is_local_backend() and not _allow_private_urls() and not _is_safe_url(url):
    return json.dumps({"success": False, "error": "Blocked: private/internal address"})

# 导航后重定向检查
if final_url != url and not _is_safe_url(final_url):
    _run_browser_command(effective_task_id, "open", ["about:blank"], timeout=10)
    return json.dumps({"success": False, "error": "redirect to private/internal address"})
```

设计理由：本地后端用户已有完整终端和网络访问权限，SSRF 检查无安全价值。

### 8.6 用户授权体系

Gateway 采用多层递进的授权检查：

1. **平台级允许全部标志**（如 `TELEGRAM_ALLOW_ALL_USERS`）
2. **平台白名单**（如 `TELEGRAM_ALLOWED_USERS`）
3. **DM 配对机制** — 已认证用户可通过配对码授权新用户
4. **全局允许全部标志**（`GATEWAY_ALLOW_ALL_USERS`）
5. **默认拒绝** — 未授权用户一律拒绝

内部事件（`MessageEvent.internal=True`）跳过授权检查。

### 8.7 Webhook 安全

[webhook.py](gateway/platforms/webhook.py) 拥有最完善的安全机制：

| 安全层              | 机制                                                               |
| ---------------- | ---------------------------------------------------------------- |
| HMAC 签名验证        | 支持 GitHub (`X-Hub-Signature-256`)、GitLab (`X-Gitlab-Token`)、通用格式 |
| Auth-before-body | 先检查 `Content-Length`，超过 1MB 直接拒绝 413                             |
| 速率限制             | 每路由固定窗口限流（默认 30 次/分钟）                                            |
| 幂等性缓存            | `_seen_deliveries` 防止 webhook 重试导致重复执行                           |
| 启动验证             | 每个路由必须有 HMAC secret，否则拒绝启动                                       |
| 时序安全比较           | `hmac.compare_digest()` 防止时序攻击                                   |

### 8.8 企业微信加密

[wecom\_crypto.py](gateway/platforms/wecom_crypto.py) 实现了完整的 WeCom BizMsgCrypt 兼容加密：

- SHA1 签名验证
- AES-CBC 解密 + PKCS7 去填充
- `receive_id` 匹配验证（防止重放）
- 使用 `secrets.choice`（密码学安全随机）

### 8.9 多实例凭据锁

[gateway/status.py](gateway/status.py) 实现了基于文件的分布式锁：

```python
def acquire_scoped_lock(scope, identity, metadata=None):
    # 1. 身份哈希：SHA256(identity)[:16]，避免在文件名中暴露凭据
    # 2. 原子创建：O_CREAT | O_EXCL | O_WRONLY
    # 3. 陈旧锁检测：PID 不存在 / PID 复用 / SIGTSTP 停止
```

### 8.10 MCP 客户端安全

| 安全层    | 机制                                                                             |
| ------ | ------------------------------------------------------------------------------ |
| 环境变量过滤 | 白名单机制（只传 PATH, HOME, USER, LANG 等安全变量 + XDG\_\*）                               |
| 凭据脱敏   | 独立 `_CREDENTIAL_PATTERN` 正则，错误消息替换为 `[REDACTED]`                               |
| 采样安全控制 | `max_tokens_cap: 4096`、`max_rpm: 10`、`allowed_models: []`、`max_tool_rounds: 5` |

### 8.11 Home Assistant 工具输入验证

```python
_ENTITY_ID_RE = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z0-9_]+$")
_SERVICE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")  # 防止 URL 路径遍历

_BLOCKED_DOMAINS = frozenset({
    "shell_command",    # 任意 shell 命令
    "command_line",     # 执行 shell 命令的传感器/开关
    "python_script",    # Python 脚本
    "pyscript",         # 更广泛访问的脚本集成
    "hassio",           # 插件控制、主机关机
    "rest_command",     # SSRF 向量
})
```

### 8.12 HTTPS/TLS 使用

- 平台 SDK 默认使用 HTTPS
- httpx 客户端重定向目标通过 `_ssrf_redirect_guard` 重新验证
- 未发现 `verify=False`（禁用 TLS 证书验证）的代码
- SOCKS5 代理使用 `rdns=True` 强制远程 DNS 解析（防 DNS 污染）

***

## 9. 文件操作安全

### 9.1 文件权限加固

| 文件/目录                 | 权限     | 位置                   |
| --------------------- | ------ | -------------------- |
| `~/.hermes/` 目录       | `0700` | `config.py`          |
| `~/.hermes/.env`      | `0600` | `config.py`          |
| `~/.hermes/auth.json` | `0600` | `auth.py`            |
| Cron 目录               | `0700` | `cron/jobs.py`       |
| Cron 文件               | `0600` | `cron/jobs.py`       |
| MCP OAuth 令牌          | `0600` | `mcp_oauth.py`       |
| Pairing 配对数据          | `0600` | `gateway/pairing.py` |
| Browser socket 目录     | `0700` | `browser_tool.py`    |
| Browser stdout/stderr | `0600` | `browser_tool.py`    |

### 9.2 原子写入模式

多个关键文件使用 `tempfile + fsync + os.replace` 的原子写入模式：

- `~/.hermes/auth.json`
- `~/.hermes/.env`
- `sessions.json`
- Pairing 配对数据

### 9.3 路径遍历防护

文档缓存中的路径遍历防护：

```python
safe_name = Path(filename).name  # 剥离目录组件
safe_name = safe_name.replace("\x00", "").strip()  # 移除空字节
if not filepath.resolve().is_relative_to(cache_dir.resolve()):
    raise ValueError(f"Path traversal rejected: {filename!r}")
```

### 9.4 图片类型验证

```python
def _looks_like_image(data):
    """魔术字节验证 -- 防止将 HTML 错误页面缓存为图片"""
    # PNG: \x89PNG\r\n\x1a\n
    # JPEG: \xff\xd8\xff
    # GIF: GIF87a / GIF89a
    # BMP: BM
    # WEBP: RIFF...WEBP
```

### 9.5 Docker 挂载符号链接防护

```python
def _safe_skills_path(skills_dir: Path) -> str:
    """Return skills_dir if symlink-free, else a sanitized temp copy."""
    symlinks = [p for p in skills_dir.rglob("*") if p.is_symlink()]
    if not symlinks:
        return str(skills_dir)
    # 创建去符号链接的安全副本...
```

防止恶意符号链接将宿主机敏感文件暴露给容器。

***

## 10. 配置与环境隔离

### 10.1 Profile 隔离

通过 `HERMES_HOME` 环境变量实现多实例隔离，每个 Profile 拥有独立的：

- 数据库（`state.db`）
- 配置文件（`config.yaml`、`.env`）
- 会话存储（`sessions/`）
- 内存数据（`memories/`）
- 技能（`skills/`）

`_apply_profile_override()` 在 `hermes_cli/main.py` 中设置 `HERMES_HOME`，**在任何模块导入之前**执行。

### 10.2 子进程 HOME 隔离

每个 Profile 的子进程 HOME 被重定向到 `{HERMES_HOME}/home/`，防止跨 Profile 的凭证泄露：

```python
from hermes_constants import get_subprocess_home
_profile_home = get_subprocess_home()
if _profile_home:
    run_env["HOME"] = _profile_home
```

### 10.3 环境变量阻断列表

[tools/environments/local.py](tools/environments/local.py) 构建了全面的阻断列表，从三个来源动态生成：

1. **Provider 注册表** — 所有 LLM 提供商的 API Key 和 Base URL 环境变量
2. **OPTIONAL\_ENV\_VARS** — category 为 `tool`、`messaging` 或 `password` 类型的设置
3. **硬编码列表** — 包含 60+ 个已知敏感环境变量

### 10.4 环境变量放行机制

[tools/env\_passthrough.py](tools/env_passthrough.py) 提供两个放行来源：

1. **技能声明**：skill frontmatter 中的 `required_environment_variables`
2. **用户配置**：`config.yaml` 中的 `terminal.env_passthrough`

### 10.5 强制前缀机制

使用 `_HERMES_FORCE_` 前缀可以显式传递被阻断的变量：

```
_HERMES_FORCE_TELEGRAM_BOT_TOKEN=xxx → 子进程接收 TELEGRAM_BOT_TOKEN=xxx
```

### 10.6 Docker 环境安全加固

```python
_SECURITY_ARGS = [
    "--cap-drop", "ALL",                    # 丢弃所有 Linux capabilities
    "--cap-add", "DAC_OVERRIDE",            # 仅加回：root 写 bind-mount 目录
    "--cap-add", "CHOWN",                   # 包管理器需要改文件属主
    "--cap-add", "FOWNER",                  # 包管理器需要改文件权限
    "--security-opt", "no-new-privileges",  # 禁止提权
    "--pids-limit", "256",                  # PID 限制
    "--tmpfs", "/tmp:rw,nosuid,size=512m",  # tmp 大小限制
    "--tmpfs", "/var/tmp:rw,noexec,nosuid,size=256m",  # 禁止执行
    "--tmpfs", "/run:rw,noexec,nosuid,size=64m",       # 禁止执行
]
```

关键安全措施：

- **最小 capability 原则**：先丢弃全部，再加回最小必需
- **禁止提权**：`no-new-privileges`
- **PID 限制**：256 个进程上限
- **tmpfs 限制**：/tmp 512MB，/var/tmp 和 /run 禁止执行

### 10.7 .gitignore 保护

```
.env
.env.local
*.ppk
*.pem
```

### 10.8 环境变量名验证

```python
if not _ENV_VAR_NAME_RE.match(key):
    raise ValueError(f"Invalid environment variable name: {key!r}")
```

***

## 11. 技能安全扫描

核心文件：[tools/skills\_guard.py](tools/skills_guard.py)

安装前安全扫描检测 **6 大类**威胁：

| 类别        | 示例模式                                                     | 严重度             |
| --------- | -------------------------------------------------------- | --------------- |
| **数据外泄**  | `curl $OPENAI_API_KEY`、`os.environ`、DNS 外泄、Markdown 图片外泄 | critical/high   |
| **提示注入**  | "ignore previous instructions"、角色劫持、系统提示提取               | critical/high   |
| **破坏性操作** | `rm -rf /`、`mkfs`、`dd`                                   | critical        |
| **持久化**   | crontab、shell rc 修改、SSH authorized\_keys                 | medium/critical |
| **网络**    | 反向 shell、端口监听                                            | critical/high   |
| **混淆**    | base64 解码执行、hex 编码                                       | high/medium     |

特别关注的外泄检测：

| 检测项                 | 模式                             | 严重度      |
| ------------------- | ------------------------------ | -------- |
| `hermes_env_access` | 直接引用 `~/.hermes/.env`          | critical |
| `read_secrets_file` | 读取 `.env`、`.netrc`、`.pgpass` 等 | critical |
| `dump_all_env`      | `printenv`、`env \|`            | high     |
| `python_os_environ` | Python `os.environ` 访问         | high     |
| `dns_exfil`         | DNS 变量插值外泄                     | critical |
| `md_image_exfil`    | Markdown 图片 URL 变量插值           | high     |

***

## 12. 安全评估与风险矩阵

### 12.1 安全措施评级

| 安全维度           | 实现方式                                            | 评级       |
| -------------- | ----------------------------------------------- | -------- |
| 日志/输出脱敏        | RedactingFormatter + 30+ 正则模式 + import 时快照      | ⭐⭐⭐⭐⭐ 优秀 |
| SSRF 防护        | is\_safe\_url + 重定向守卫 + CGNAT 覆盖 + 失败关闭         | ⭐⭐⭐⭐⭐ 优秀 |
| URL 密钥外泄阻断     | 前缀检测 + URL 解码防御 + 浏览器导航拦截                       | ⭐⭐⭐⭐⭐ 优秀 |
| Webhook 安全     | HMAC 签名 + 速率限制 + 幂等性 + auth-before-body         | ⭐⭐⭐⭐⭐ 优秀 |
| 原子写入           | tempfile + fsync + os.replace                   | ⭐⭐⭐⭐⭐ 优秀 |
| OAuth Token 管理 | 自动刷新 + 崩溃安全持久化 + 独立会话                           | ⭐⭐⭐⭐⭐ 优秀 |
| 跨进程锁           | fcntl 文件锁 + 可重入 + 超时                            | ⭐⭐⭐⭐ 良好  |
| SQL 注入防护       | 参数化查询 + FTS5 清理 + LIKE 转义                       | ⭐⭐⭐⭐⭐ 优秀 |
| 危险命令检测         | 30+ 模式 + 反混淆 + 智能审批                             | ⭐⭐⭐⭐ 良好  |
| 代码执行沙箱         | 工具白名单 + 参数黑名单 + 资源限制 + 进程组隔离                    | ⭐⭐⭐⭐ 良好  |
| 子代理安全          | 工具黑名单 + 深度限制 + 上下文隔离                            | ⭐⭐⭐⭐ 良好  |
| Docker 隔离      | cap-drop ALL + no-new-privileges + PID/tmpfs 限制 | ⭐⭐⭐⭐ 良好  |
| 凭据存储           | 文件权限 0600/0700                                  | ⭐⭐⭐ 合理   |
| PII 脱敏         | 平台感知哈希 + 确定性映射                                  | ⭐⭐⭐⭐ 良好  |
| 技能安全扫描         | 6 大类威胁检测 + 安装前拦截                                | ⭐⭐⭐⭐ 良好  |

### 12.2 已知风险与改进建议

| #  | 风险                                               | 严重度 | 当前状态       | 改进建议                                        |
| -- | ------------------------------------------------ | --- | ---------- | ------------------------------------------- |
| 1  | **无应用层加密**：所有凭据明文存储在 `auth.json` 和 `.env` 中      | 中   | 依赖 OS 文件权限 | 考虑集成 keyring 或 Fernet 加密；对 NFS/容器环境尤为重要     |
| 2  | **Sudo 密码明文存储**：`SUDO_PASSWORD` 以明文写入 `.env`     | 中   | 文件权限 0600  | 考虑使用 keyring 集成或 session keyring            |
| 3  | **SQLite 数据库文件缺少权限加固**：`state.db` 创建时未设置 `0o600` | 中   | 系统默认 umask | 在数据库创建后添加 `os.chmod(db_path, 0o600)`        |
| 4  | **轨迹保存安全性不足**：无权限设置、无原子写入、默认路径为 CWD              | 低   | 默认禁用       | 使用 `get_hermes_home()` 路径 + 原子写入 + 0o600 权限 |
| 5  | **DNS Rebinding（TOCTOU）**：预检层面无法防御               | 低   | 已文档化       | 需连接级验证（如 egress 代理）                         |
| 6  | **第三方 SDK 重定向**：Firecrawl/Tavily 的重定向在服务端处理      | 低   | 已知限制       | 无法在客户端层面修复                                  |
| 7  | **Webhook HTTP 监听**：默认绑定 `0.0.0.0:8644`，无内置 TLS  | 中   | 依赖反向代理     | 文档中强调必须使用反向代理；或添加内置 TLS 支持                  |
| 8  | **Qwen 凭据跨应用共享**：与其他 Qwen 客户端共享刷新令牌              | 低   | 文件锁缓解      | 考虑独立的凭据存储                                   |
| 9  | **Codex 回写竞态**：Hermes 刷新后回写 `~/.codex/auth.json` | 低   | 文件锁缓解      | 监控 `refresh_token_reused` 错误率               |
| 10 | **Z.AI 端点探测**：使用 API 密钥向多个端点发送实际请求               | 低   | 使用哈希缓存键    | 考虑缓存探测结果更长时间                                |
| 11 | **`redact_key()`** **函数重复定义**：三处实现遮蔽策略不同         | 低   | 功能正常       | 统一为单一实现                                     |
| 12 | **MCP 脱敏与全局脱敏不一致**：MCP 用 `[REDACTED]`，全局用前缀后缀保留  | 低   | 功能正常       | 统一使用 `redact_sensitive_text()`              |
| 13 | **截图无法脱敏**：浏览器截图是图像数据                            | 低   | 已知限制       | 对辅助 LLM 的文本输入/输出已脱敏                         |
| 14 | **`INSECURE_NO_AUTH`** **模式**：Webhook 允许跳过签名验证   | 低   | 仅限测试       | 确保不用于生产环境                                   |

### 12.3 安全测试覆盖

项目有专门的测试文件验证安全机制：

| 测试文件                                       | 覆盖范围                                                                             |
| ------------------------------------------ | -------------------------------------------------------------------------------- |
| `tests/agent/test_redact.py`               | 30+ 种密钥模式、ENV 赋值、JSON 字段、Auth 头、Telegram Token、私钥、DB 连接串、电话号码、RedactingFormatter |
| `tests/gateway/test_pii_redaction.py`      | PII 哈希、平台感知、确定性、Discord/Slack 排除                                                 |
| `tests/tools/test_browser_secret_exfil.py` | URL 密钥阻断、浏览器快照脱敏、Camofox 注释脱敏                                                    |
| `tests/tools/test_local_env_blocklist.py`  | 环境变量阻断列表完整性                                                                      |
| `tests/tools/test_env_passthrough.py`      | 透传机制与阻断列表交互                                                                      |
| `tests/tools/test_approval.py`             | 危险命令检测、审批流程                                                                      |
| `tests/tools/test_url_safety.py`           | SSRF 防护、私有 IP 阻断                                                                 |

***

## 附录：安全相关文件索引

| 文件                                  | 安全职责                               |
| ----------------------------------- | ---------------------------------- |
| `agent/redact.py`                   | 核心脱敏引擎（8 层规则 + RedactingFormatter） |
| `hermes_cli/auth.py`                | 多提供者认证、OAuth 流程、凭据持久化              |
| `hermes_cli/config.py`              | 配置管理、.env 处理、环境变量验证                |
| `hermes_cli/callbacks.py`           | 审批回调、密码安全输入                        |
| `hermes_cli/setup.py`               | 安装向导凭据输入                           |
| `tools/approval.py`                 | 危险命令检测、审批模式、Tirith 集成              |
| `tools/terminal_tool.py`            | 终端命令执行安全控制                         |
| `tools/code_execution_tool.py`      | 代码执行沙箱                             |
| `tools/delegate_tool.py`            | 子代理委托安全边界                          |
| `tools/url_safety.py`               | SSRF 防护                            |
| `tools/mcp_tool.py`                 | MCP 客户端安全                          |
| `tools/browser_tool.py`             | 浏览器自动化安全                           |
| `tools/web_tools.py`                | Web 搜索/提取安全                        |
| `tools/skills_guard.py`             | 技能安装前安全扫描                          |
| `tools/env_passthrough.py`          | 环境变量放行机制                           |
| `tools/credential_files.py`         | Docker 挂载符号链接防护                    |
| `tools/registry.py`                 | 工具注册权限检查                           |
| `tools/environments/local.py`       | 本地环境凭证过滤                           |
| `tools/environments/docker.py`      | Docker 安全加固                        |
| `tools/website_policy.py`           | 网站访问策略                             |
| `hermes_state.py`                   | SQLite 会话存储安全                      |
| `gateway/session.py`                | 网关会话 PII 脱敏                        |
| `gateway/status.py`                 | 多实例凭据锁                             |
| `gateway/platforms/base.py`         | SSRF 重定向守卫、URL 日志脱敏                |
| `gateway/platforms/webhook.py`      | Webhook HMAC 签名验证                  |
| `gateway/platforms/wecom_crypto.py` | 企业微信加密                             |
| `hermes_logging.py`                 | 日志脱敏格式化器                           |
| `hermes_constants.py`               | HERMES\_HOME 路径管理                  |


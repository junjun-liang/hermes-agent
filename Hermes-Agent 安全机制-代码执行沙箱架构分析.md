# Hermes-Agent 代码执行沙箱架构分析

## 1. 系统概述

Hermes-Agent 的代码执行沙箱 (Code Execution Sandbox) 是一个基于 **程序化工具调用 (Programmatic Tool Calling, PTC)** 的架构，允许 LLM 编写 Python 脚本，在沙箱环境中通过 RPC 机制调用 Hermes 工具集。该系统将多步骤工具链压缩为单次推理轮次，大幅减少了上下文窗口消耗，同时通过严格的安全隔离机制防止凭证泄露和恶意代码执行。

### 1.1 核心功能特性

| 功能模块 | 描述 |
|---------|------|
| **程序化工具调用 (PTC)** | LLM 编写 Python 脚本调用工具，替代逐轮工具调用 |
| **双传输架构** | 本地 UDS + 远程文件 RPC，适配不同执行环境 |
| **安全隔离** | 子进程环境变量过滤、凭证脱敏、工具白名单 |
| **资源限制** | 超时控制、输出截断、工具调用次数上限 |
| **透明代理** | 子进程通过 RPC 调用父进程工具，结果不进入上下文 |

### 1.2 架构设计原则

1. **最小权限原则**: 工具默认不可用，需通过 check_fn 验证
2. **分层验证**: 工具集级 → 工具级 → 命令级 → 内容级
3. **动态适配**: 根据环境变化 (API Key 配置/服务可用性) 动态调整可用工具
4. **用户可控**: 支持会话审批、永久白名单、YOLO 模式、智能审批
5. **容错设计**: 检查失败时优雅降级 (fail-open/fail-closed 可配置)
6. **spawn-per-call**: 每次执行 spawn 新进程，避免状态污染

---

## 2. 软件架构图

### 2.1 整体架构层次图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          AIAgent (run_agent.py)                              │
│                                                                              │
│   LLM 生成 execute_code 工具调用                                              │
│   code: "from hermes_tools import terminal, read_file\n..."                  │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                   execute_code() (code_execution_tool.py)                     │
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐     │
│   │                     路由分发层                                      │     │
│   │                                                                    │     │
│   │   env_type == "local"?                                             │     │
│   │       ├── 是 → 本地执行路径 (UDS RPC)                               │     │
│   │       └── 否 → 远程执行路径 (File RPC)                              │     │
│   └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│   ┌──────────────────────┐    ┌──────────────────────────────────────────┐  │
│   │  本地执行 (UDS)       │    │  远程执行 (File RPC)                     │  │
│   │                      │    │                                          │  │
│   │  1. 生成 hermes_     │    │  1. 获取/创建远程环境                    │  │
│   │     tools.py (UDS)   │    │  2. 生成 hermes_tools.py (file)          │  │
│   │  2. 创建 UDS Server  │    │  3. 传输文件到远程                       │  │
│   │  3. 启动 RPC 监听线程│    │  4. 启动 RPC 轮询线程                    │  │
│   │  4. 启动子进程       │    │  5. 在远程执行脚本                       │  │
│   │  5. 等待完成/超时    │    │  6. 等待完成/超时                        │  │
│   │  6. 收集输出         │    │  7. 收集输出                             │  │
│   │  7. 清理临时文件     │    │  8. 清理远程沙箱目录                     │  │
│   └──────────────────────┘    └──────────────────────────────────────────┘  │
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐     │
│   │                     后处理管道                                      │     │
│   │                                                                    │     │
│   │   1. Head/Tail 输出截断 (50KB)                                     │     │
│   │   2. ANSI 转义序列清洗                                             │     │
│   │   3. 凭证脱敏 (redact_sensitive_text)                              │     │
│   │   4. 构建 JSON 响应                                                │     │
│   └────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         RPC 通信层                                            │
│                                                                              │
│   ┌──────────────────────────┐    ┌──────────────────────────────────────┐  │
│   │  UDS RPC (本地)           │    │  File RPC (远程)                     │  │
│   │                          │    │                                      │  │
│   │  子进程 ──UDS Socket──→  │    │  远程脚本 ──req 文件──→               │  │
│   │  父进程 ──UDS Socket──→  │    │  轮询线程 ──res 文件──→               │  │
│   │                          │    │  父进程   ←──env.execute()──→        │  │
│   │  协议：JSON + newline    │    │  协议：JSON 文件 + 原子写入          │  │
│   └──────────────────────────┘    └──────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     工具调度层 (model_tools.py)                                │
│                                                                              │
│   handle_function_call(tool_name, tool_args, task_id)                        │
│       │                                                                      │
│       ├── web_search   ──→ web_tools.py                                      │
│       ├── web_extract  ──→ web_tools.py                                      │
│       ├── read_file    ──→ file_tools.py                                     │
│       ├── write_file   ──→ file_tools.py                                     │
│       ├── search_files ──→ file_tools.py                                     │
│       ├── patch        ──→ file_tools.py                                     │
│       └── terminal     ──→ terminal_tool.py (前台模式，禁止 background/pty)  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 安全架构图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          安全防护体系                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Layer 1: 环境变量隔离 (子进程环境过滤)                              │    │
│  │                                                                     │    │
│  │  白名单前缀：PATH, HOME, USER, LANG, LC_, TERM, TMPDIR, SHELL...   │    │
│  │  黑名单关键词：KEY, TOKEN, SECRET, PASSWORD, CREDENTIAL, AUTH       │    │
│  │  透传机制：env_passthrough (技能声明 + 用户配置)                     │    │
│  │  Profile 隔离：HOME 重定向到 {HERMES_HOME}/home/                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Layer 2: 工具白名单 (SANDBOX_ALLOWED_TOOLS)                        │    │
│  │                                                                     │    │
│  │  仅允许 7 种工具：web_search, web_extract, read_file,               │    │
│  │  write_file, search_files, patch, terminal                          │    │
│  │  terminal 禁止参数：background, pty, notify_on_complete             │    │
│  │  工具调用上限：50 次/脚本                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Layer 3: 输出脱敏 (redact_sensitive_text)                          │    │
│  │                                                                     │    │
│  │  API Key 前缀匹配：sk-, ghp_, AIza, pplx-, fal_...                 │    │
│  │  ENV 赋值模式：KEY=VALUE → KEY=***                                  │    │
│  │  JSON 字段："apiKey": "..." → "apiKey": "***"                       │    │
│  │  Authorization Header: Bearer ***                                   │    │
│  │  私钥块：-----BEGIN PRIVATE KEY----- → [REDACTED]                   │    │
│  │  数据库连接串：protocol://user:***@host                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Layer 4: 资源限制                                                  │    │
│  │                                                                     │    │
│  │  超时：300s (5 分钟，可配置)                                        │    │
│  │  Stdout 上限：50KB (Head 40% + Tail 60%)                            │    │
│  │  Stderr 上限：10KB                                                  │    │
│  │  工具调用上限：50 次                                                │    │
│  │  进程组隔离：os.setsid() + SIGTERM/SIGKILL                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Layer 5: 输出清洗 (strip_ansi)                                     │    │
│  │                                                                     │    │
│  │  ECMA-48 全覆盖：CSI, OSC, DCS/SOS/PM/APC                          │    │
│  │  8-bit C1 控制字符                                                  │    │
│  │  防止 LLM 复制转义序列到文件写入                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 hermes_tools.py 代码生成架构

```
┌──────────────────────────────────────────────────────────────────────────────┐
│              generate_hermes_tools_module(enabled_tools, transport)           │
│                                                                              │
│   输入:                                                                      │
│     enabled_tools = 会话启用的工具列表                                        │
│     transport = "uds" | "file"                                               │
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐     │
│   │  工具交集计算                                                      │     │
│   │  sandbox_tools = SANDBOX_ALLOWED_TOOLS ∩ enabled_tools             │     │
│   │  (空集时回退到 SANDBOX_ALLOWED_TOOLS 全集)                         │     │
│   └────────────────────────────────────────────────────────────────────┘     │
│                                   │                                          │
│                                   ▼                                          │
│   ┌────────────────────────────────────────────────────────────────────┐     │
│   │  传输层头部选择                                                    │     │
│   │                                                                    │     │
│   │  UDS: _UDS_TRANSPORT_HEADER                                       │     │
│   │    • socket.AF_UNIX 连接                                          │     │
│   │    • HERMES_RPC_SOCKET 环境变量                                    │     │
│   │    • _call() 通过 UDS 发送 JSON + newline                         │     │
│   │                                                                    │     │
│   │  File: _FILE_TRANSPORT_HEADER                                     │     │
│   │    • HERMES_RPC_DIR 环境变量                                       │     │
│   │    • _call() 写入 req_XXXXXX 文件                                  │     │
│   │    • 轮询 res_XXXXXX 文件获取响应                                  │     │
│   │    • 自适应轮询间隔：50ms → 250ms                                  │     │
│   └────────────────────────────────────────────────────────────────────┘     │
│                                   │                                          │
│                                   ▼                                          │
│   ┌────────────────────────────────────────────────────────────────────┐     │
│   │  公共辅助函数 (_COMMON_HELPERS)                                    │     │
│   │                                                                    │     │
│   │  • json_parse(text) — strict=False 的 JSON 解析                   │     │
│   │  • shell_quote(s) — shlex.quote() 安全转义                        │     │
│   │  • retry(fn, max_attempts, delay) — 指数退避重试                  │     │
│   └────────────────────────────────────────────────────────────────────┘     │
│                                   │                                          │
│                                   ▼                                          │
│   ┌────────────────────────────────────────────────────────────────────┐     │
│   │  工具桩函数生成 (_TOOL_STUBS)                                      │     │
│   │                                                                    │     │
│   │  每个工具：(func_name, signature, docstring, args_dict_expr)       │     │
│   │                                                                    │     │
│   │  def web_search(query: str, limit: int = 5):                      │     │
│   │      """Search the web..."""                                       │     │
│   │      return _call('web_search', {"query": query, "limit": limit})  │     │
│   │                                                                    │     │
│   │  def terminal(command: str, timeout: int = None, workdir=None):   │     │
│   │      """Run a shell command..."""                                  │     │
│   │      return _call('terminal', {"command": command, ...})           │     │
│   └────────────────────────────────────────────────────────────────────┘     │
│                                   │                                          │
│                                   ▼                                          │
│   输出：完整的 hermes_tools.py 源代码字符串                                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心业务流程

### 3.1 本地执行 (UDS RPC) 完整流程

```mermaid
sequenceDiagram
    participant LLM as LLM Agent
    participant EC as execute_code()
    participant Gen as 代码生成器
    participant RPC as RPC Server Thread
    participant Child as 子进程 (script.py)
    participant Tools as handle_function_call()

    LLM->>EC: execute_code(code="from hermes_tools import terminal\n...")
    
    EC->>EC: 检查 SANDBOX_AVAILABLE
    EC->>EC: 计算 sandbox_tools = ALLOWED ∩ enabled
    EC->>EC: 创建临时目录 /tmp/hermes_sandbox_XXX
    
    EC->>Gen: generate_hermes_tools_module(sandbox_tools, "uds")
    Gen-->>EC: hermes_tools.py 源代码
    
    EC->>EC: 写入 hermes_tools.py + script.py
    EC->>EC: 创建 UDS Socket (/tmp/hermes_rpc_XXX.sock)
    
    EC->>RPC: 启动 RPC 监听线程
    RPC->>RPC: server_sock.accept() 等待连接
    
    EC->>EC: 构建子进程环境变量 (过滤密钥)
    EC->>Child: subprocess.Popen([python, "script.py"], env=child_env)
    
    Child->>Child: import hermes_tools
    Child->>Child: hermes_tools._connect() → UDS 连接
    
    Child->>RPC: _call("terminal", {"command": "ls"})
    Note over Child,RPC: JSON + newline over UDS
    
    RPC->>RPC: 验证工具白名单
    RPC->>RPC: 检查调用次数上限
    RPC->>RPC: 过滤 terminal 禁止参数
    
    RPC->>Tools: handle_function_call("terminal", args, task_id)
    Tools-->>RPC: JSON 结果字符串
    RPC-->>Child: 结果 + newline over UDS
    
    Child->>Child: 处理结果，print() 输出
    
    EC->>EC: 轮询子进程状态
    Note over EC: 检查：进程退出 / 超时 / 中断
    
    Child-->>EC: 进程退出，stdout + stderr
    
    EC->>EC: 后处理管道:
    EC->>EC: 1. Head/Tail 截断 (50KB)
    EC->>EC: 2. strip_ansi() 清洗
    EC->>EC: 3. redact_sensitive_text() 脱敏
    
    EC-->>LLM: {"status": "success", "output": "...", "tool_calls_made": N}
    
    EC->>EC: 清理：删除临时目录 + UDS Socket
```

### 3.2 远程执行 (File RPC) 完整流程

```mermaid
sequenceDiagram
    participant LLM as LLM Agent
    participant EC as _execute_remote()
    participant Env as 远程环境 (Docker/SSH/Modal)
    participant Poll as RPC 轮询线程
    participant Tools as handle_function_call()

    LLM->>EC: _execute_remote(code, task_id, enabled_tools)
    
    EC->>EC: 获取/创建远程环境 (_get_or_create_env)
    EC->>Env: 检查 Python3 可用性
    Env-->>EC: OK
    
    EC->>Env: mkdir -p /tmp/hermes_exec_XXX/rpc
    EC->>EC: 生成 hermes_tools.py (file transport)
    
    EC->>Env: _ship_file_to_remote(hermes_tools.py)
    Note over EC,Env: echo BASE64 | base64 -d > file
    EC->>Env: _ship_file_to_remote(script.py)
    
    EC->>Poll: 启动 RPC 轮询线程
    
    EC->>Env: HERMES_RPC_DIR=... python3 script.py
    
    Note over Env: 脚本执行中...
    
    Env->>Env: _call("read_file", args)
    Env->>Env: 写入 req_000001 文件 (原子写入)
    
    Poll->>Env: ls req_* 检查请求文件
    Poll->>Env: cat req_000001 读取请求
    
    Poll->>Poll: 验证工具白名单
    Poll->>Tools: handle_function_call("read_file", args, task_id)
    Tools-->>Poll: JSON 结果
    
    Poll->>Env: echo BASE64 | base64 -d > res_000001.tmp && mv res_000001.tmp res_000001
    Poll->>Env: rm -f req_000001
    
    Env->>Env: 轮询 res_000001 文件
    Env->>Env: 读取响应，继续执行
    
    Env-->>EC: 执行完成，返回 stdout + exit_code
    
    EC->>EC: 后处理管道 (同本地)
    EC->>Env: rm -rf /tmp/hermes_exec_XXX (清理)
    
    EC-->>LLM: {"status": "success", "output": "...", "tool_calls_made": N}
```

### 3.3 环境变量过滤流程

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           环境变量过滤流程                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  遍历 os.environ                                                     │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  变量在 env_passthrough 白名单？                                    │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│               ┌─────────────────────┴─────────────────────┐               │
│               ▼                                           ▼               │
│  ┌───────────────────────────┐         ┌───────────────────────────┐   │
│  │ 是: 包含在子进程环境       │         │ 否: 变量名包含 KEY/TOKEN/  │   │
│  │                           │         │ SECRET/PASSWORD/           │   │
│  │                           │         │ CREDENTIAL/AUTH?           │   │
│  └─────────────┬───────────┘         └─────────────┬─────────────┘   │
│                │                                   │                   │
│                │                     ┌─────────────┴─────────────┐   │
│                │                     ▼                           ▼   │
│                │           ┌──────────────────┐   ┌───────────────────┐ │
│                │           │ 是: 排除         │   │ 否: 变量名以安全  │ │
│                │           │ 不传递给子进程   │   │ 前缀开头？         │ │
│                │           └──────────┬───────┘   └───────────┬───────┘ │
│                │                      │                       │         │
│                │                      │                ┌────────┴────────┐ │
│                │                      │                ▼                 ▼ │
│                │                      │          ┌───────────┐   ┌──────────┐ │
│                │                      │          │ 是: 包含  │   │ 否: 排除  │ │
│                │                      │          └────┬──────┘   └────┬─────┘ │
│                │                      │               │               │       │
│                │                      │               │               │       │
│                └──────────────────────┼───────────────┼───────────────┘       │
│                                       │               │                       │
│                                       ▼               ▼                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  添加特殊变量：                                                    │   │
│  │  HERMES_RPC_SOCKET                                                 │   │
│  │  PYTHONDONTWRITEBYTECODE                                           │   │
│  │  PYTHONPATH                                                        │   │
│  │  TZ (时区)                                                         │   │
│  │  HOME (Profile 隔离)                                               │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  构建 child_env 字典                                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 输出后处理管道

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           输出后处理管道                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  原始 stdout/stderr                                                  │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Head/Tail 截断                                                      │   │
│  │  上限 50KB                                                           │   │
│  │  40% Head + 60% Tail                                                │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  ANSI 转义序列清洗                                                   │   │
│  │  ECMA-48 全覆盖                                                     │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  凭证脱敏                                                            │   │
│  │  API Key / Token / 私钥                                             │   │
│  │  DB 连接串 / 手机号                                                  │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  构建 JSON 响应                                                      │   │
│  │  status + output +                                                  │   │
│  │  tool_calls_made + duration                                         │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  返回给 LLM                                                           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 进程生命周期管理

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          进程生命周期管理                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  [开始]                                                            │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Created                                                           │   │
│  │  subprocess.Popen()                                               │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Running                                                           │   │
│  │  进程启动                                                           │   │
│  │  轮询 proc.poll()                                                   │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│               ┌─────────────────────┴─────────────────────┐               │
│               ▼                                           ▼               │
│  ┌───────────────────────────┐         ┌───────────────────────────┐   │
│  │  Exited                   │         │  Timeout                   │   │
│  │  正常退出                  │         │  time.monotonic() > deadline │   │
│  └─────────────┬───────────┘         └─────────────┬─────────────┘   │
│                │                                   │                   │
│                │                                   ▼                   │
│                │                     ┌───────────────────────────┐   │
│                │                     │  SIGTERM                  │   │
│                │                     │  _kill_process_group()    │   │
│                │                     └─────────────┬─────────────┘   │
│                │                                   │                   │
│                │                                   ▼                   │
│                │                     ┌───────────────────────────┐   │
│                │                     │  WaitExit                  │   │
│                │                     │  proc.wait(5s)            │   │
│                │                     └─────────────┬─────────────┘   │
│                │                                   │                   │
│                │                            ┌──────┴──────┐           │
│                │                            ▼             ▼           │
│                │                 ┌───────────────┐  ┌──────────────┐   │
│                │                 │  SIGKILL      │  │  CleanExit   │   │
│                │                 │  超时未退出    │  │  已退出      │   │
│                │                 └────────┬──────┘  └──────┬───────┘   │
│                │                          │                 │           │
│                │                          │                 │           │
│                │                          ▼                 │           │
│                │                 ┌──────────────────────────┐           │
│                │                 │  CleanExit               │           │
│                │                 └──────────┬───────────────┘           │
│                │                           │                            │
│                │                           │                            │
│                └───────────────────────────┼────────────────────────────┘   │
│                                            │                               │
│                                            ▼                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Cleanup                                                            │   │
│  │  删除临时目录 + Socket                                              │   │
│  └──────────────────────────────────┬───────────────────────────────────┘   │
│                                       │                                       │
│                                       ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  [结束]                                                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 核心代码分析

### 4.1 工具白名单与限制

**文件**: `tools/code_execution_tool.py:56-71`

```python
SANDBOX_ALLOWED_TOOLS = frozenset([
    "web_search",
    "web_extract",
    "read_file",
    "write_file",
    "search_files",
    "patch",
    "terminal",
])

DEFAULT_TIMEOUT = 300
DEFAULT_MAX_TOOL_CALLS = 50
MAX_STDOUT_BYTES = 50_000
MAX_STDERR_BYTES = 10_000
```

**设计要点**:
1. **最小权限原则**: 仅暴露 7 种工具，排除高风险工具如 `browser_navigate`, `execute_code` (递归), `delegate`
2. **terminal 参数限制**: 禁止 `background`, `pty`, `notify_on_complete`, `watch_patterns`
3. **资源上限**: 超时 5 分钟、输出 50KB、调用 50 次

### 4.2 UDS RPC 服务器循环

**文件**: `tools/code_execution_tool.py:307-425`

```python
def _rpc_server_loop(
    server_sock, task_id, tool_call_log,
    tool_call_counter, max_tool_calls, allowed_tools,
):
    conn, _ = server_sock.accept()
    conn.settimeout(300)
    
    buf = b""
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        buf += chunk
        
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            request = json.loads(line.decode())
            
            tool_name = request.get("tool", "")
            tool_args = request.get("args", {})
            
            # 白名单检查
            if tool_name not in allowed_tools:
                conn.sendall((error + "\n").encode())
                continue
            
            # 调用次数检查
            if tool_call_counter[0] >= max_tool_calls:
                conn.sendall((error + "\n").encode())
                continue
            
            # terminal 参数过滤
            if tool_name == "terminal":
                for param in _TERMINAL_BLOCKED_PARAMS:
                    tool_args.pop(param, None)
            
            # 分发到标准工具处理器
            result = handle_function_call(tool_name, tool_args, task_id=task_id)
            conn.sendall((result + "\n").encode())
```

**设计要点**:
1. **单连接模型**: 仅接受一个客户端连接，简化状态管理
2. **换行分隔协议**: JSON + `\n` 分隔，支持缓冲区中的多条消息
3. **stdout 抑制**: 工具调用时重定向 stdout/stderr 到 devnull，防止内部日志泄露到 CLI

### 4.3 文件 RPC 轮询循环

**文件**: `tools/code_execution_tool.py:564-703`

```python
def _rpc_poll_loop(env, rpc_dir, task_id, ...):
    poll_interval = 0.1
    
    while not stop_event.is_set():
        # 列出请求文件
        ls_result = env.execute(f"ls -1 {quoted_rpc_dir}/req_* 2>/dev/null")
        
        for req_file in req_files:
            # 读取请求
            read_result = env.execute(f"cat {quoted_req_file}")
            request = json.loads(read_result.get("output", ""))
            
            # 白名单 + 调用次数检查
            # ...
            
            # 分发工具调用
            tool_result = handle_function_call(tool_name, tool_args, task_id=task_id)
            
            # 原子写入响应 (tmp + rename)
            encoded_result = base64.b64encode(tool_result.encode()).decode()
            env.execute(
                f"echo '{encoded_result}' | base64 -d > {res_file}.tmp"
                f" && mv {res_file}.tmp {res_file}"
            )
            
            # 删除请求文件
            env.execute(f"rm -f {quoted_req_file}")
```

**设计要点**:
1. **原子文件操作**: 写入 `.tmp` 再 `rename`，防止读取半写文件
2. **Base64 传输**: 避免 shell 特殊字符问题
3. **自适应轮询**: 100ms 间隔，平衡延迟和资源消耗
4. **stop_event 协作退出**: 支持优雅终止

### 4.4 环境变量安全过滤

**文件**: `tools/code_execution_tool.py:989-1028`

```python
_SAFE_ENV_PREFIXES = ("PATH", "HOME", "USER", "LANG", "LC_", "TERM",
                      "TMPDIR", "TMP", "TEMP", "SHELL", "LOGNAME",
                      "XDG_", "PYTHONPATH", "VIRTUAL_ENV", "CONDA")
_SECRET_SUBSTRINGS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL",
                      "PASSWD", "AUTH")

child_env = {}
for k, v in os.environ.items():
    # 透传变量 (技能声明或用户配置) 始终通过
    if _is_passthrough(k):
        child_env[k] = v
        continue
    # 阻止包含密钥关键词的变量
    if any(s in k.upper() for s in _SECRET_SUBSTRINGS):
        continue
    # 允许安全前缀的变量
    if any(k.startswith(p) for p in _SAFE_ENV_PREFIXES):
        child_env[k] = v
```

**设计要点**:
1. **三层过滤**: 透传白名单 → 密钥黑名单 → 安全前缀白名单
2. **技能声明透传**: 技能通过 `required_environment_variables` 声明的变量自动透传
3. **用户配置透传**: `terminal.env_passthrough` 配置允许用户自定义
4. **Profile 隔离**: `HOME` 重定向到 `{HERMES_HOME}/home/`

### 4.5 凭证脱敏引擎

**文件**: `agent/redact.py:1-180`

```python
_PREFIX_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{10,}",           # OpenAI / OpenRouter / Anthropic
    r"ghp_[A-Za-z0-9]{10,}",            # GitHub PAT
    r"AIza[A-Za-z0-9_-]{30,}",          # Google API keys
    r"xox[baprs]-[A-Za-z0-9-]{10,}",    # Slack tokens
    r"AKIA[A-Z0-9]{16}",                # AWS Access Key ID
    # ... 30+ 种模式
]

def _mask_token(token: str) -> str:
    if len(token) < 18:
        return "***"
    return f"{token[:6]}...{token[-4:]}"
```

**脱敏覆盖范围**:
- API Key 前缀匹配 (30+ 种)
- ENV 赋值模式 (`OPENAI_API_KEY=sk-...`)
- JSON 字段 (`"apiKey": "..."`)
- Authorization Header (`Bearer sk-...`)
- Telegram Bot Token
- RSA 私钥块
- 数据库连接串密码
- E.164 手机号

---

## 5. 设计模式分析

### 5.1 代理模式 (Proxy Pattern)

子进程通过 RPC 代理调用父进程的工具，而非直接访问：

```
子进程 → hermes_tools._call() → RPC 通道 → 父进程 RPC Server → handle_function_call()
```

**优势**:
- 子进程无法直接访问 API 密钥
- 父进程可以执行白名单检查和调用计数
- 工具调用的副作用在父进程上下文中执行

### 5.2 策略模式 (Strategy Pattern)

双传输架构使用策略模式，根据环境类型选择不同的 RPC 传输策略：

```python
if env_type != "local":
    return _execute_remote(code, task_id, enabled_tools)  # File RPC 策略
# 本地执行 (UDS RPC 策略)
```

### 5.3 模板方法模式 (Template Method)

`generate_hermes_tools_module` 使用模板方法，头部 (传输层) 可变，桩函数生成逻辑固定：

```python
if transport == "file":
    header = _FILE_TRANSPORT_HEADER
else:
    header = _UDS_TRANSPORT_HEADER

return header + "\n".join(stub_functions)
```

### 5.4 观察者模式 (Observer)

工具调用日志 (`tool_call_log`) 作为观察者记录每次调用的元数据：

```python
tool_call_log.append({
    "tool": tool_name,
    "args_preview": args_preview,
    "duration": round(call_duration, 2),
})
```

### 5.5 管道模式 (Pipeline Pattern)

输出后处理使用管道模式，依次经过多个处理阶段：

```
原始输出 → Head/Tail 截断 → ANSI 清洗 → 凭证脱敏 → JSON 响应
```

---

## 6. 远程环境集成

### 6.1 环境类型支持

| 环境类型 | 传输方式 | 执行后端 | 文件同步 |
|---------|---------|---------|---------|
| `local` | UDS Socket | 本地子进程 | 无需 (共享文件系统) |
| `docker` | File RPC | Docker 容器 | Bind mount |
| `ssh` | File RPC | SSH 远程主机 | FileSyncManager |
| `modal` | File RPC | Modal Sandbox | FileSyncManager |
| `daytona` | File RPC | Daytona Workspace | FileSyncManager |
| `singularity` | File RPC | Singularity 容器 | Bind mount |

### 6.2 BaseEnvironment 抽象

**文件**: `tools/environments/base.py`

```
BaseEnvironment (ABC)
├── _run_bash()          # 抽象方法：启动 bash 进程
├── cleanup()            # 抽象方法：释放资源
├── execute()            # 统一执行入口
├── init_session()       # 会话快照 (环境变量/函数/别名)
├── _wrap_command()      # 命令包装 (source snapshot + cd + eval)
├── _wait_for_process()  # 进程等待 (中断/超时/活动回调)
└── _update_cwd()        # CWD 追踪
```

**关键特性**:
- **会话快照**: 捕获登录 shell 环境，避免每次 `bash -l` 的开销
- **CWD 追踪**: 通过 stdout 标记或临时文件追踪工作目录
- **活动回调**: 每 10 秒触发一次，防止网关超时

---

## 7. 配置接口

### 7.1 config.yaml 配置

```yaml
code_execution:
  timeout: 300          # 脚本执行超时 (秒)
  max_tool_calls: 50    # 最大工具调用次数

terminal:
  env_passthrough:      # 环境变量透传白名单
    - MY_CUSTOM_API_KEY
    - SPECIAL_CONFIG_VAR
```

### 7.2 资源限制常量

| 参数 | 默认值 | 描述 |
|------|-------|------|
| `DEFAULT_TIMEOUT` | 300s | 脚本执行超时 |
| `DEFAULT_MAX_TOOL_CALLS` | 50 | 最大工具调用次数 |
| `MAX_STDOUT_BYTES` | 50,000 | Stdout 输出上限 |
| `MAX_STDERR_BYTES` | 10,000 | Stderr 输出上限 |

---

## 8. 测试覆盖

### 8.1 测试文件

**文件**: `tests/tools/test_code_execution.py` (~867 行)

### 8.2 测试分类

| 测试类 | 覆盖范围 |
|-------|---------|
| `TestSandboxRequirements` | 平台可用性检查 |
| `TestHermesToolsGeneration` | 代码生成：全集/子集/空集/非法工具/辅助函数 |
| `TestExecuteCode` | 集成测试：基本执行/工具调用/错误/超时/中断 |
| `TestStubSchemaDrift` | 桩函数与真实 Schema 同步性检查 |
| `TestBuildExecuteCodeSchema` | 动态 Schema 生成测试 |
| `TestEnvVarFiltering` | 环境变量安全过滤测试 |
| `TestExecuteCodeEdgeCases` | 边界条件：Windows/空代码/None 工具 |
| `TestInterruptHandling` | 中断信号处理 |
| `TestHeadTailTruncation` | Head/Tail 输出截断 |
| `TestExecuteCodeRemoteTempDir` | 远程执行临时目录 |

### 8.3 关键安全测试

```python
class TestEnvVarFiltering:
    def test_api_keys_excluded(self):
        # 验证 OPENAI_API_KEY, ANTHROPIC_API_KEY 等被排除
    
    def test_tokens_excluded(self):
        # 验证 GITHUB_TOKEN, MODAL_TOKEN 等被排除
    
    def test_password_vars_excluded(self):
        # 验证 DB_PASSWORD, MY_PASSWD 等被排除
    
    def test_path_included(self):
        # 验证 PATH 等安全变量被包含
```

---

## 9. 代码索引

### 9.1 核心文件

| 文件路径 | 行数 | 核心功能 |
|---------|------|---------|
| `tools/code_execution_tool.py` | ~1378 | 沙箱主入口、代码生成、RPC 服务器、远程执行 |
| `tools/environments/base.py` | ~578 | 环境基类、统一执行流程、会话快照 |
| `tools/env_passthrough.py` | ~102 | 环境变量透传注册表 |
| `tools/ansi_strip.py` | ~44 | ANSI 转义序列清洗 |
| `tools/interrupt.py` | ~76 | 线程级中断信号 |
| `agent/redact.py` | ~180 | 凭证脱敏引擎 |

### 9.2 核心函数索引

| 函数名 | 文件 | 功能描述 |
|-------|------|---------|
| `execute_code()` | `code_execution_tool.py:890` | 沙箱主入口，路由到本地/远程路径 |
| `_execute_remote()` | `code_execution_tool.py:706` | 远程执行路径 (File RPC) |
| `generate_hermes_tools_module()` | `code_execution_tool.py:130` | 生成 hermes_tools.py 模块 |
| `_rpc_server_loop()` | `code_execution_tool.py:307` | UDS RPC 服务器循环 |
| `_rpc_poll_loop()` | `code_execution_tool.py:564` | File RPC 轮询循环 |
| `_get_or_create_env()` | `code_execution_tool.py:431` | 获取/创建远程执行环境 |
| `_ship_file_to_remote()` | `code_execution_tool.py:531` | 传输文件到远程环境 |
| `_kill_process_group()` | `code_execution_tool.py:1222` | 进程组终止 (SIGTERM → SIGKILL) |
| `build_execute_code_schema()` | `code_execution_tool.py:1294` | 动态 Schema 生成 |
| `strip_ansi()` | `ansi_strip.py:35` | ANSI 转义序列清洗 |
| `redact_sensitive_text()` | `redact.py:113` | 凭证脱敏 |
| `is_env_passthrough()` | `env_passthrough.py:83` | 环境变量透传检查 |

### 9.3 环境后端文件

| 文件路径 | 描述 |
|---------|------|
| `tools/environments/base.py` | 抽象基类 |
| `tools/environments/docker.py` | Docker 容器后端 |
| `tools/environments/singularity.py` | Singularity 容器后端 |
| `tools/environments/modal.py` | Modal Sandbox 后端 |
| `tools/environments/managed_modal.py` | 托管 Modal 后端 |
| `tools/environments/daytona.py` | Daytona Workspace 后端 |

---

## 10. 总结

Hermes-Agent 的代码执行沙箱系统是一个设计精良的程序化工具调用 (PTC) 架构，其核心亮点包括：

1. **双传输架构**: UDS (本地零延迟) + File RPC (远程兼容)，统一接口适配不同执行环境
2. **五层安全防护**: 环境变量隔离 → 工具白名单 → 输出脱敏 → 资源限制 → ANSI 清洗，形成纵深防御
3. **代码生成模式**: 动态生成 `hermes_tools.py` 桩模块，仅暴露当前会话启用的工具
4. **进程组管理**: `os.setsid()` + SIGTERM/SIGKILL 升级策略，确保子进程可靠终止
5. **Head/Tail 截断**: 保留输出首尾，中间截断，兼顾 LLM 上下文效率和调试可见性
6. **Profile 隔离**: 子进程 HOME 重定向，防止跨 Profile 的配置泄露

该系统成功将多轮工具调用压缩为单次推理，在保证安全隔离的前提下，显著提升了 Agent 的执行效率和上下文利用率。

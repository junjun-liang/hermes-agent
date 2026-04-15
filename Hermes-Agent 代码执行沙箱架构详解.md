# Hermes-Agent 代码执行沙箱架构详解

> 分析日期：2026-04-14 | 核心文件：`tools/code_execution_tool.py`（1400+ 行） | 沙箱类型：进程隔离 + RPC 回调

---

## 目录

1. [沙箱架构总览](#1-沙箱架构总览)
2. [双传输架构](#2-双传输架构)
3. [沙箱执行核心流程](#3-沙箱执行核心流程)
4. [安全机制详解](#4-安全机制详解)
5. [资源限制机制](#5-资源限制机制)
6. [进程隔离与终止](#6-进程隔离与终止)
7. [环境变量安全过滤](#7-环境变量安全过滤)
8. [工具白名单机制](#8-工具白名单机制)
9. [与 Terminal 工具对比](#9-与-terminal-工具对比)
10. [架构决策与权衡](#10-架构决策与权衡)

---

## 1. 沙箱架构总览

### 1.1 设计目标

Hermes-Agent 的代码执行沙箱旨在提供一个**安全、可控、可审计**的代码执行环境，主要解决以下问题：

| 问题 | 风险 | 沙箱解决方案 |
|------|------|--------------|
| **直接执行风险** | 恶意代码可访问宿主机资源 | 子进程隔离 + 环境变量过滤 |
| **凭证泄露** | `os.environ` 可获取 API Key | 三层过滤机制（阻断 + 白名单 + 声明放行） |
| **无限循环** | `while True` 耗尽资源 | 超时限制 + 进程组强制终止 |
| **工具滥用** | 沙箱内调用危险工具（如 `delegate_task`） | 工具白名单 + 参数黑名单 |
| **输出污染** | ANSI 转义码、敏感信息泄露 | ANSI 剥离 + 脱敏引擎 |

### 1.2 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    用户层（LLM 调用）                         │
│  execute_code(language="python", code="...", timeout=60)    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  调度层（code_execution_tool.py）             │
│  - 参数验证                                                   │
│  - 沙箱环境创建（UDS / 文件 RPC）                             │
│  - 子进程启动（sandbox_runner.py）                           │
│  - 资源监控（超时、工具调用次数）                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   执行层（sandbox_runner.py）                 │
│  - 代码执行（exec(code, SAFE_BUILTINS, {})）                 │
│  - 工具回调（RPC 请求父进程 → registry.dispatch()）          │
│  - 输出捕获（stdout/stderr 重定向）                          │
│  - 安全限制（工具白名单、调用次数上限）                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    工具层（registry.dispatch）                │
│  - 工具执行（read_file, terminal, web_search...）            │
│  - 结果返回（RPC 响应 → 子进程）                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心特性

| 特性 | 实现方式 | 安全价值 |
|------|----------|----------|
| **进程隔离** | `subprocess.Popen()` + `os.setsid()` 新进程组 | 防止逃逸到父进程 |
| **RPC 通信** | UDS（本地）或文件（远程） | 父进程代理工具调用，子进程无法直接访问外部资源 |
| **环境变量过滤** | 三层过滤（阻断密钥名 + 安全前缀白名单 + 技能声明放行） | 防止 API Key 泄露到沙箱 |
| **工具白名单** | `SANDBOX_ALLOWED_TOOLS = {web_search, read_file, ...}` | 防止调用危险工具（如 `delegate_task`） |
| **资源限制** | 超时、工具调用次数、输出大小上限 | 防止 DoS 攻击 |
| **输出净化** | ANSI 剥离 + 敏感信息脱敏 | 防止终端注入和密钥泄露 |

---

## 2. 双传输架构

沙箱支持两种 RPC 传输方式，适应不同执行环境：

### 2.1 本地后端（UDS - Unix Domain Socket）

**适用场景**：本地执行（`tools/environments/local.py`）

**架构**：
```
┌──────────────────────────────────────────────────────────────┐
│                      父进程（主进程）                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  socket_server(dir=temp_dir, timeout=300)              │  │
│  │  - 创建临时目录：/tmp/hermes_sandbox_<pid>_<uuid>      │  │
│  │  - 绑定 UDS: <temp_dir>/sandbox.sock                   │  │
│  │  - 监听连接：server.listen(1)                          │  │
│  │  - 接受连接：client, addr = server.accept()            │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ Unix Domain Socket
                            │ <temp_dir>/sandbox.sock
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                      子进程（sandbox_runner）                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  socket_client(sock_path=<temp_dir>/sandbox.sock)      │  │
│  │  - 连接父进程：client.connect(sock_path)               │  │
│  │  - 发送请求：send_request("execute", {...})            │  │
│  │  - 接收响应：recv_response() → {"result": ...}         │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**UDS 优势**：
- **高性能**：内核态通信，无需网络栈
- **安全性**：仅限本机访问，无需端口暴露
- **双向通信**：父进程和子进程均可主动发送消息

**实现细节**：
```python
# 父进程：创建 UDS 服务器
def socket_server(dir_path, timeout=300):
    sock_path = os.path.join(dir_path, "sandbox.sock")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.settimeout(timeout)
    server.bind(sock_path)
    server.listen(1)
    client, _ = server.accept()
    return client

# 子进程：连接 UDS 服务器
def socket_client(sock_path):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(sock_path)
    return client
```

### 2.2 远程后端（文件 RPC）

**适用场景**：容器环境（Docker、Singularity）、远程环境（SSH、Modal、Daytona）

**架构**：
```
┌──────────────────────────────────────────────────────────────┐
│                      父进程（主进程）                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  file_server(dir=shared_dir, timeout=300)              │  │
│  │  - 共享目录：/mnt/hermes_sandbox/<task_id>             │  │
│  │    （本地挂载到容器/远程环境）                            │  │
│  │  - 轮询请求文件：<shared_dir>/request.json             │  │
│  │  - 写入响应文件：<shared_dir>/response.json            │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ 共享文件系统
                            │ （本地挂载或 NFS）
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                      子进程（容器/远程环境）                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  file_client(shared_dir=<shared_dir>)                  │  │
│  │  - 写入请求文件：<shared_dir>/request.json             │  │
│  │  - 轮询响应文件：<shared_dir>/response.json            │  │
│  │  - 原子操作：写入后 fsync，读取后删除                   │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**文件 RPC 协议**：
```json
// request.json
{
  "type": "execute",
  "code": "import os; print(os.getcwd())",
  "language": "python",
  "allowed_tools": ["web_search", "read_file", "write_file"],
  "max_tool_calls": 50
}

// response.json
{
  "type": "result",
  "stdout": "/home/user\n",
  "stderr": "",
  "exit_code": 0,
  "tool_calls": 5
}
```

**实现细节**：
```python
# 父进程：文件服务器轮询
def file_server(dir_path, timeout=300):
    request_path = os.path.join(dir_path, "request.json")
    response_path = os.path.join(dir_path, "response.json")
    
    # 等待请求文件
    start = time.time()
    while not os.path.exists(request_path):
        if time.time() - start > timeout:
            raise TimeoutError("Waiting for request file")
        time.sleep(0.1)
    
    # 读取请求
    with open(request_path, "r") as f:
        request = json.load(f)
    os.unlink(request_path)  # 删除请求文件
    
    # ... 处理请求 ...
    
    # 写入响应（原子操作）
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(response, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, response_path)  # 原子替换

# 子进程：文件客户端
def file_client(shared_dir):
    request_path = os.path.join(shared_dir, "request.json")
    response_path = os.path.join(shared_dir, "response.json")
    
    # 写入请求
    fd, tmp_path = tempfile.mkstemp(dir=shared_dir, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(request, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, request_path)
    
    # 轮询响应
    start = time.time()
    while not os.path.exists(response_path):
        if time.time() - start > timeout:
            raise TimeoutError("Waiting for response file")
        time.sleep(0.1)
    
    # 读取响应
    with open(response_path, "r") as f:
        response = json.load(f)
    os.unlink(response_path)  # 删除响应文件
    
    return response
```

### 2.3 传输方式选择逻辑

```python
def _select_backend(environment_type: str) -> str:
    """选择 RPC 传输后端"""
    if environment_type == "local":
        return "uds"  # 本地环境使用 UDS
    elif environment_type in ("docker", "singularity", "modal", "daytona", "ssh"):
        return "file"  # 容器/远程环境使用文件 RPC
    else:
        raise ValueError(f"Unknown environment type: {environment_type}")
```

**选择依据**：
- **UDS**：要求父子进程在同一主机，共享文件系统命名空间
- **文件 RPC**：仅需共享目录（本地挂载或 NFS），适应容器/远程场景

---

## 3. 沙箱执行核心流程

### 3.1 完整执行流程

```
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: LLM 调用 execute_code 工具                             │
│  execute_code(                                             │
│      language="python",                                    │
│      code="import os; print(os.getcwd())",                 │
│      timeout=60,                                           │
│      env={"CUSTOM_VAR": "value"}                           │
│  )                                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: 参数验证                                             │
│  - language 必须是 "python" 或 "javascript"（未来扩展）         │
│  - code 非空                                                 │
│  - timeout <= DEFAULT_TIMEOUT (300 秒)                        │
│  - 检查沙箱可用性（check_sandbox_requirements()）            │
│    └─ 非 Windows（需要 UDS）                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: 创建沙箱环境                                         │
│  - 创建临时目录：/tmp/hermes_sandbox_<pid>_<uuid>           │
│  - 生成沙箱脚本：sandbox_runner.py                          │
│  - 选择后端：UDS（本地）或文件 RPC（远程）                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 构建安全环境变量                                    │
│  - 阻断含 KEY/TOKEN/SECRET/PASSWORD 的变量                   │
│  - 放行 PATH, HOME, USER, LANG 等安全变量                    │
│  - 技能声明的 passthrough 变量                              │
│  - 用户显式指定的 env 参数                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: 启动子进程                                           │
│  proc = subprocess.Popen(                                  │
│      [sys.executable, "sandbox_runner.py"],                │
│      env=safe_env,                                         │
│      preexec_fn=os.setsid,  # 新进程组                      │
│      stdin=subprocess.DEVNULL,                             │
│      stdout=subprocess.PIPE,                               │
│      stderr=subprocess.PIPE                                │
│  )                                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 6: 子进程初始化 RPC 通道                                 │
│  - 本地后端：socket_client(sock_path)                       │
│  - 远程后端：file_client(shared_dir)                        │
│  - 发送握手请求：{"type": "init"}                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 7: 父进程发送代码执行请求                               │
│  send_request("execute", {                                 │
│      "language": "python",                                 │
│      "code": "import os; print(os.getcwd())",              │
│      "allowed_tools": SANDBOX_ALLOWED_TOOLS,               │
│      "max_tool_calls": 50                                  │
│  })                                                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 8: 子进程执行代码                                        │
│  exec(code, {"__builtins__": SAFE_BUILTINS}, {})           │
│                                                              │
│  安全内置对象：                                              │
│  SAFE_BUILTINS = {                                         │
│      "print": safe_print,  # 重定向到 stdout                 │
│      "len": len,                                           │
│      "str": str,                                           │
│      "int": int,                                           │
│      "list": list,                                         │
│      "dict": dict,                                         │
│      "set": set,                                           │
│      # ... 安全内置函数                                     │
│      # 排除：open, eval, exec, __import__ 等危险函数         │
│  }                                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 9: 代码调用工具（如 read_file）                          │
│  def tool_callback(tool_name, args):                       │
│      # 1. 检查工具白名单                                    │
│      if tool_name not in allowed_tools:                    │
│          raise PermissionError(f"Tool {tool_name} blocked")│
│      # 2. 检查调用次数上限                                   │
│      if tool_call_count >= max_tool_calls:                 │
│          raise RuntimeError("Max tool calls reached")      │
│      # 3. RPC 请求父进程                                      │
│      send_request("tool_call", {                           │
│          "tool_name": tool_name,                           │
│          "args": args                                      │
│      })                                                    │
│      # 4. 接收响应                                          │
│      response = recv_response()                            │
│      tool_call_count += 1                                  │
│      return json.loads(response["result"])                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 10: 父进程处理工具调用请求                               │
│  request = recv_request()                                  │
│  if request["type"] == "tool_call":                        │
│      result = registry.dispatch(                           │
│          request["tool_name"],                             │
│          request["args"],                                  │
│          task_id=task_id                                   │
│      )                                                     │
│      send_response({"result": result})                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 11: 执行完成，收集输出                                   │
│  stdout = proc.stdout.read(MAX_STDOUT_BYTES)  # 50KB 上限    │
│  stderr = proc.stderr.read(MAX_STDERR_BYTES)  # 10KB 上限    │
│  exit_code = proc.returncode                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 12: 输出后处理                                         │
│  - strip_ansi(stdout) → 剥离 ANSI 转义码                      │
│  - redact_sensitive_text(stdout) → 敏感信息脱敏             │
│  - 构建 JSON 结果                                            │
│  {                                                         │
│      "success": exit_code == 0,                            │
│      "stdout": "脱敏后的输出",                              │
│      "stderr": "",                                         │
│      "exit_code": 0,                                       │
│      "tool_calls": 5  # 实际调用次数                        │
│  }                                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 13: 清理资源                                           │
│  - 关闭 UDS socket 或删除请求/响应文件                        │
│  - 删除临时目录                                              │
│  - 终止子进程（若仍在运行）                                  │
│  - 返回结果给 LLM                                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 代码执行伪代码

```python
def execute_code(language, code, timeout=300, env=None):
    # ========== 步骤 1: 参数验证 ==========
    if language != "python":
        return tool_error(f"Unsupported language: {language}")
    if not code or not code.strip():
        return tool_error("code is required")
    if timeout > DEFAULT_TIMEOUT:
        return tool_error(f"Timeout exceeds maximum ({DEFAULT_TIMEOUT}s)")
    
    # ========== 步骤 2: 创建沙箱环境 ==========
    temp_dir = tempfile.mkdtemp(prefix="hermes_sandbox_")
    sock_path = os.path.join(temp_dir, "sandbox.sock")
    
    # ========== 步骤 3: 构建安全环境变量 ==========
    safe_env = _build_safe_env(user_env=env)
    
    # ========== 步骤 4: 启动 UDS 服务器（父进程） ==========
    server_thread = threading.Thread(
        target=_socket_server,
        args=(temp_dir, timeout),
        daemon=True
    )
    server_thread.start()
    
    # ========== 步骤 5: 启动子进程 ==========
    proc = subprocess.Popen(
        [sys.executable, "sandbox_runner.py", "--sock-path", sock_path],
        env=safe_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # 新进程组
    )
    
    try:
        # ========== 步骤 6: 等待子进程连接 ==========
        server_thread.join(timeout=10)  # 等待子进程连接
        if not server_thread.is_alive():
            client_socket = server_thread.result  # 获取客户端 socket
        
        # ========== 步骤 7: 发送代码执行请求 ==========
        _send_request(client_socket, "execute", {
            "language": language,
            "code": code,
            "allowed_tools": list(SANDBOX_ALLOWED_TOOLS),
            "max_tool_calls": DEFAULT_MAX_TOOL_CALLS
        })
        
        # ========== 步骤 8: 处理工具调用请求 ==========
        tool_call_count = 0
        while True:
            request = _recv_request(client_socket, timeout=5)
            if request is None:
                continue  # 超时，继续等待
            
            if request["type"] == "tool_call":
                # 检查调用次数上限
                if tool_call_count >= DEFAULT_MAX_TOOL_CALLS:
                    _send_error(client_socket, "Max tool calls reached")
                    continue
                
                # 执行工具
                result = registry.dispatch(
                    request["tool_name"],
                    request["args"],
                    task_id=task_id
                )
                _send_response(client_socket, {"result": result})
                tool_call_count += 1
            
            elif request["type"] == "done":
                break  # 执行完成
        
        # ========== 步骤 9: 收集输出 ==========
        stdout, stderr = proc.communicate(timeout=10)
        stdout = stdout.decode("utf-8", errors="replace")
        stderr = stderr.decode("utf-8", errors="replace")
        
        # ========== 步骤 10: 输出后处理 ==========
        stdout = strip_ansi(stdout)
        stdout = redact_sensitive_text(stdout)
        stderr = strip_ansi(stderr)
        stderr = redact_sensitive_text(stderr)
        
        # 截断输出
        if len(stdout) > MAX_STDOUT_BYTES:
            stdout = stdout[:MAX_STDOUT_BYTES] + "\n... (truncated)"
        if len(stderr) > MAX_STDERR_BYTES:
            stderr = stderr[:MAX_STDERR_BYTES] + "\n... (truncated)"
        
        return tool_result(
            success=proc.returncode == 0,
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode,
            tool_calls=tool_call_count
        )
    
    except TimeoutError:
        # ========== 步骤 11: 超时处理 ==========
        _kill_process_group(proc.pid)
        return tool_error(f"Execution timed out after {timeout}s")
    
    except Exception as e:
        _kill_process_group(proc.pid)
        return tool_error(f"Execution failed: {type(e).__name__}: {e}")
    
    finally:
        # ========== 步骤 12: 清理资源 ==========
        if proc.poll() is None:
            _kill_process_group(proc.pid)
        shutil.rmtree(temp_dir, ignore_errors=True)
```

---

## 4. 安全机制详解

### 4.1 多层安全架构

```
┌─────────────────────────────────────────────────────────────┐
│  第 1 层：进程隔离                                             │
│  - subprocess.Popen() 创建独立进程                           │
│  - os.setsid() 创建新进程组                                  │
│  - stdin=subprocess.DEVNULL 禁用输入                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 2 层：环境变量过滤                                         │
│  - 阻断含 KEY/TOKEN/SECRET/PASSWORD 的变量                   │
│  - 放行安全前缀变量（PATH, HOME, USER...）                   │
│  - 技能声明的 passthrough 变量                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 3 层：内置对象限制                                         │
│  - SAFE_BUILTINS 排除危险函数（open, eval, exec, __import__）│
│  - 仅允许安全内置函数（print, len, str, int...）             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 4 层：工具白名单                                           │
│  - SANDBOX_ALLOWED_TOOLS = {web_search, read_file, ...}     │
│  - 阻断危险工具（delegate_task, clarify, memory...）         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 5 层：终端参数黑名单                                       │
│  - _TERMINAL_BLOCKED_PARAMS = {background, pty, ...}        │
│  - 防止沙箱内调用 terminal(background=true) 逃逸             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 6 层：资源限制                                             │
│  - 超时限制（DEFAULT_TIMEOUT=300 秒）                         │
│  - 工具调用次数上限（DEFAULT_MAX_TOOL_CALLS=50）             │
│  - 输出大小上限（MAX_STDOUT_BYTES=50KB）                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  第 7 层：输出净化                                             │
│  - strip_ansi() 剥离 ANSI 转义码                              │
│  - redact_sensitive_text() 脱敏敏感信息                     │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 安全内置对象

```python
SAFE_BUILTINS = {
    # 类型转换
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "tuple": tuple,
    "dict": dict,
    "set": set,
    "bytes": bytes,
    
    # 内置函数
    "print": safe_print,  # 重定向到 stdout
    "len": len,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "reversed": reversed,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "range": range,
    "repr": repr,
    "hash": hash,
    "id": id,
    "type": type,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "hasattr": hasattr,
    "getattr": getattr,
    "setattr": setattr,
    "delattr": delattr,
    "dir": dir,
    "vars": vars,
    "id": id,
    
    # 模块导入（受限）
    "__import__": safe_import,  # 白名单模块
    
    # 排除的危险函数
    # "open": ❌ 禁止文件操作（通过工具调用）
    # "eval": ❌ 禁止动态执行
    # "exec": ❌ 禁止动态执行
    # "compile": ❌ 禁止动态编译
    # "input": ❌ 禁止交互式输入
}

# 安全导入白名单
SAFE_IMPORT_MODULES = frozenset({
    "math", "random", "datetime", "collections",
    "itertools", "functools", "re", "json",
    "urllib.parse", "hashlib", "base64",
    # 排除：os, sys, subprocess, socket 等
})
```

### 4.3 终端参数黑名单

```python
_TERMINAL_BLOCKED_PARAMS = frozenset({
    "background",      # 禁止后台执行（绕过监控）
    "pty",             # 禁止 PTY（交互式 shell）
    "notify_on_complete",  # 禁止完成通知（触发新 agent 循环）
    "watch_patterns",  # 禁止文件监控
})

def _validate_terminal_args(args):
    """验证 terminal 工具调用的参数"""
    for param in _TERMINAL_BLOCKED_PARAMS:
        if param in args:
            raise PermissionError(
                f"Parameter '{param}' is not allowed in sandbox"
            )
```

**安全理由**：
- `background=true`：后台执行绕过超时监控，可能导致资源泄漏
- `pty=true`：交互式 shell 可能被用于逃逸
- `notify_on_complete=true`：完成通知触发新 agent 循环，产生副作用
- `watch_patterns`：文件监控持续运行，无法被终止

---

## 5. 资源限制机制

### 5.1 超时限制

```python
DEFAULT_TIMEOUT = 300  # 5 分钟

# 父进程等待子进程连接
server_thread.join(timeout=10)

# 子进程执行代码
proc.communicate(timeout=timeout)

# RPC 请求/响应超时
socket.settimeout(5)  # 每次 RPC 超时 5 秒
```

**超时处理流程**：
```
超时发生 → TimeoutError 异常 → _kill_process_group() → 返回错误 JSON
```

### 5.2 工具调用次数限制

```python
DEFAULT_MAX_TOOL_CALLS = 50

# 子进程计数
tool_call_count = 0
def tool_callback(tool_name, args):
    global tool_call_count
    if tool_call_count >= DEFAULT_MAX_TOOL_CALLS:
        raise RuntimeError("Max tool calls reached")
    # ... 执行工具调用 ...
    tool_call_count += 1
```

**超限处理**：
```json
{
  "success": false,
  "error": "Max tool calls (50) reached",
  "stdout": "...",
  "tool_calls": 50
}
```

### 5.3 输出大小限制

```python
MAX_STDOUT_BYTES = 50_000  # 50KB
MAX_STDERR_BYTES = 10_000  # 10KB

# 截断输出
if len(stdout) > MAX_STDOUT_BYTES:
    stdout = stdout[:MAX_STDOUT_BYTES] + "\n... (truncated)"
if len(stderr) > MAX_STDERR_BYTES:
    stderr = stderr[:MAX_STDERR_BYTES] + "\n... (truncated)"
```

**截断理由**：
- 防止大量输出耗尽内存
- 避免 LLM 上下文被输出占满
- 50KB 足够容纳大部分正常输出

---

## 6. 进程隔离与终止

### 6.1 进程组创建

```python
proc = subprocess.Popen(
    [sys.executable, "sandbox_runner.py"],
    preexec_fn=None if _IS_WINDOWS else os.setsid,  # 新进程组
)
```

**`os.setsid()` 的作用**：
- 创建新会话（Session）和新进程组（Process Group）
- 子进程的进程组 ID = 子进程 PID
- 父进程可通过 `os.killpg(pid, signal)` 终止整个进程组

### 6.2 进程组强制终止

```python
def _kill_process_group(pid):
    """Terminate an entire process group (SIGTERM → SIGKILL)"""
    if not pid:
        return
    
    try:
        # 步骤 1: 发送 SIGTERM 到进程组
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except ProcessLookupError:
        return  # 进程已不存在
    
    # 步骤 2: 等待 5 秒
    for _ in range(50):
        if proc.poll() is not None:
            return  # 进程已退出
        time.sleep(0.1)
    
    # 步骤 3: 升级为 SIGKILL
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except ProcessLookupError:
        pass
```

**终止流程**：
```
SIGTERM（优雅退出） → 等待 5 秒 → 进程仍存活 → SIGKILL（强制终止）
```

**为何使用进程组**：
- 子进程可能创建孙进程（如 `subprocess.run()`）
- 仅终止子进程会导致孙进程孤儿化（持续运行）
- 终止整个进程组确保所有后代进程被清理

### 6.3 资源泄漏防护

```python
try:
    # ... 执行沙箱代码 ...
finally:
    # 无论成功/失败/超时/异常，都清理资源
    if proc.poll() is None:
        _kill_process_group(proc.pid)
    shutil.rmtree(temp_dir, ignore_errors=True)
    if client_socket:
        client_socket.close()
    if server_socket:
        server_socket.close()
```

---

## 7. 环境变量安全过滤

### 7.1 三层过滤机制

```python
# 第 1 层：敏感变量名黑名单
_SECRET_SUBSTRINGS = frozenset({
    "KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL",
    "PASSWD", "AUTH", "API_KEY", "PRIVATE",
})

# 第 2 层：安全变量名前缀白名单
_SAFE_ENV_PREFIXES = frozenset({
    "PATH", "HOME", "USER", "LANG", "LC_", "TERM",
    "TMPDIR", "TMP", "TEMP", "SHELL", "LOGNAME",
    "XDG_", "PYTHONPATH", "VIRTUAL_ENV", "CONDA",
})

# 第 3 层：技能声明的放行变量
def _is_passthrough(var_name):
    """检查变量是否在技能声明或用户配置的放行列表中"""
    return var_name in _get_allowed() or var_name in _load_config_passthrough()
```

### 7.2 环境变量构建流程

```python
def _build_safe_env(user_env=None):
    """构建沙箱环境变量（三层过滤）"""
    safe_env = {}
    
    for key, value in os.environ.items():
        # 跳过内部前缀变量（_HERMES_FORCE_*）
        if key.startswith("_HERMES_FORCE_"):
            continue
        
        # 第 1 层：技能/用户声明放行
        if _is_passthrough(key):
            safe_env[key] = value
            continue
        
        # 第 2 层：敏感变量名阻断
        if any(s in key.upper() for s in _SECRET_SUBSTRINGS):
            continue  # 阻断含 KEY/TOKEN/SECRET 的变量
        
        # 第 3 层：安全前缀放行
        if any(key.startswith(p) for p in _SAFE_ENV_PREFIXES):
            safe_env[key] = value
    
    # 合并用户显式指定的 env 参数
    if user_env:
        safe_env.update(user_env)
    
    # 强制设置 HOME（Profile 隔离）
    from hermes_constants import get_subprocess_home
    profile_home = get_subprocess_home()
    if profile_home:
        safe_env["HOME"] = profile_home
    
    return safe_env
```

### 7.3 过滤效果示例

| 环境变量 | 是否放行 | 理由 |
|----------|----------|------|
| `PATH` | ✅ 放行 | 安全前缀白名单 |
| `HOME` | ✅ 放行（但被 Profile HOME 覆盖） | 安全前缀白名单 |
| `ANTHROPIC_API_KEY` | ❌ 阻断 | 含 `KEY` 子串 |
| `TELEGRAM_BOT_TOKEN` | ❌ 阻断 | 含 `TOKEN` 子串 |
| `CUSTOM_VAR` | ❌ 阻断 | 不在白名单 |
| `VIRTUAL_ENV` | ✅ 放行 | 安全前缀白名单 |
| `_HERMES_FORCE_TELEGRAM_BOT_TOKEN` | ❌ 跳过（内部前缀） | 解析为 `TELEGRAM_BOT_TOKEN` 后注入 |
| 技能声明的 `REQUIRED_API_KEY` | ✅ 放行 | 技能声明放行 |

### 7.4 Profile HOME 隔离

```python
from hermes_constants import get_subprocess_home

profile_home = get_subprocess_home()  # ~/.hermes/profiles/<name>/home
if profile_home:
    safe_env["HOME"] = profile_home
```

**安全价值**：
- 每个 Profile 的沙箱进程 HOME 被重定向到独立目录
- 防止跨 Profile 的凭证泄露（如 `~/.ssh/id_rsa`）
- 防止沙箱代码访问父进程的 `~/.hermes/.env`

---

## 8. 工具白名单机制

### 8.1 白名单定义

```python
SANDBOX_ALLOWED_TOOLS = frozenset({
    "web_search",      # Web 搜索
    "web_extract",     # Web 内容提取
    "read_file",       # 读取文件
    "write_file",      # 写入文件
    "search_files",    # 搜索文件
    "patch",           # 补丁应用
    "terminal",        # 终端命令（带参数黑名单）
})
```

### 8.2 被阻断的工具及理由

| 工具 | 阻断理由 |
|------|----------|
| `delegate_task` | 防止递归委托（子代理不能再委托） |
| `clarify` | 禁止用户交互（子代理不能打扰用户） |
| `memory` | 禁止写入共享 MEMORY.md（避免污染记忆） |
| `send_message` | 禁止跨平台副作用（防止垃圾消息） |
| `execute_code` | 禁止嵌套沙箱（资源浪费 + 逃逸风险） |
| `cronjob` | 禁止定时任务（持续运行，无法监控） |
| `process` | 禁止后台进程管理（绕过终止机制） |

### 8.3 白名单验证逻辑

```python
def _validate_tool_call(tool_name, allowed_tools):
    """验证工具调用是否在白名单内"""
    if tool_name not in allowed_tools:
        raise PermissionError(
            f"Tool '{tool_name}' is not allowed in sandbox. "
            f"Allowed tools: {', '.join(sorted(allowed_tools))}"
        )
```

### 8.4 动态工具集交集

```python
# 沙箱实际可用工具 = 白名单 ∩ 当前会话启用的工具
sandbox_enabled = frozenset(
    t for t in enabled_tools 
    if t in SANDBOX_ALLOWED_TOOLS
)
```

**安全价值**：
- 即使用户启用了 `delegate_task`，沙箱内仍不可用
- 双重保障：白名单 + 会话工具集交集

---

## 9. 与 Terminal 工具对比

### 9.1 功能定位对比

| 维度 | `execute_code` | `terminal` |
|------|----------------|------------|
| **用途** | 执行代码片段（Python 脚本） | 执行系统命令（bash、grep、git...） |
| **执行环境** | 沙箱隔离（子进程 + RPC） | 直接执行（父进程环境） |
| **环境变量** | 三层过滤（无 API Key） | 完整继承（含 API Key） |
| **工具调用** | 允许（白名单机制） | 不允许 |
| **文件访问** | 通过 `read_file`/`write_file` 工具 | 直接访问（受 approval 审批） |
| **网络访问** | 通过 `web_search`/`web_extract` 工具 | 直接访问（`curl`、`wget`） |
| **适用场景** | 数据处理、算法实现、API 调用测试 | 文件操作、git 命令、系统管理 |

### 9.2 安全级别对比

| 安全层 | `execute_code` | `terminal` |
|--------|----------------|------------|
| 进程隔离 | ✅ 子进程 + 进程组 | ❌ 父进程直接执行 |
| 环境变量过滤 | ✅ 三层过滤 | ❌ 完整继承 |
| 工具调用限制 | ✅ 白名单机制 | N/A |
| 命令审批 | ❌ 不需要（代码不直接执行命令） | ✅ 危险命令检测 + 审批 |
| 输出脱敏 | ✅ ANSI 剥离 + 脱敏 | ✅ ANSI 剥离 + 脱敏 |
| 超时限制 | ✅ 300 秒硬上限 | ✅ 600 秒（可配置） |

### 9.3 选择建议

**使用 `execute_code`**：
- 需要执行 Python 代码进行数据处理
- 需要调用 API（通过 `web_search`/`web_extract`）
- 需要读写文件（通过 `read_file`/`write_file`）
- 需要安全隔离（不暴露 API Key 给代码）

**使用 `terminal`**：
- 需要执行系统命令（`ls`、`grep`、`git`）
- 需要交互式 shell（`pty=true`）
- 需要后台执行（`background=true`）
- 需要文件监控（`watch_patterns`）

### 9.4 典型误用

**错误示例 1**：在 `execute_code` 中执行系统命令
```python
# ❌ 错误：沙箱内无法直接执行系统命令
execute_code(code="""
import subprocess
subprocess.run(["ls", "-la"])  # 子进程无权限访问父进程环境
""")

# ✅ 正确：使用 terminal 工具
execute_code(code="""
from tools import terminal
result = terminal({"command": "ls -la"})
print(result)
""")
```

**错误示例 2**：在 `terminal` 中执行 Python 代码
```python
# ❌ 错误：多行代码难以维护
terminal(command="python3 -c 'import os; print(os.getcwd())'")

# ✅ 正确：使用 execute_code
execute_code(language="python", code="import os; print(os.getcwd())")
```

---

## 10. 架构决策与权衡

### 10.1 关键架构决策

| 决策 | 选择 | 替代方案 | 理由 |
|------|------|----------|------|
| **执行模型** | 子进程隔离 | 线程隔离 / 容器隔离 | 进程隔离更彻底，线程不安全，容器太重 |
| **RPC 传输** | UDS + 文件双后端 | 纯 UDS / 纯网络 RPC | UDS 高性能，文件 RPC 适应容器/远程 |
| **工具调用** | 父进程代理 | 子进程直接调用 | 防止子进程访问外部资源，统一审计 |
| **环境变量** | 三层过滤 | 全量继承 / 全量阻断 | 平衡安全性（阻断密钥）和可用性（保留 PATH） |
| **内置对象** | 白名单内置函数 | 黑名单危险函数 | 白名单更安全，防止未知危险函数 |
| **终止机制** | 进程组 SIGTERM→SIGKILL | 单进程终止 | 确保孙进程也被清理 |

### 10.2 已知限制

| 限制 | 影响 | 缓解措施 |
|------|------|----------|
| **非 Python 语言支持** | 仅支持 Python | 未来扩展 JavaScript（Node.js 沙箱） |
| **图形界面不支持** | 无法执行 GUI 代码 | 设计定位：后端数据处理 |
| **实时交互不支持** | `input()` 被禁用 | 通过工具调用获取用户输入 |
| **大文件处理限制** | 50KB 输出上限 | 通过 `read_file` 分块读取 |
| **网络直连禁止** | `socket` 模块被禁用 | 通过 `web_search`/`web_extract` 工具 |

### 10.3 性能优化点

| 优化点 | 当前状态 | 建议 |
|--------|----------|------|
| UDS 连接建立 | 每次创建新 socket | 连接池复用（长连接） |
| 文件 RPC 轮询 | 100ms 间隔 | 事件通知（inotify） |
| 工具调用序列化 | JSON 序列化 | Protocol Buffers（更高效） |
| 沙箱脚本生成 | 每次生成临时文件 | 预编译缓存 |
| 环境变量构建 | 遍历全量环境 | 缓存安全变量列表 |

### 10.4 安全加固建议

| 建议 | 优先级 | 实现难度 |
|------|--------|----------|
| seccomp-bpf 系统调用过滤 | 中 | 高（需要 C 扩展） |
| AppArmor/SELinux 配置文件 | 低 | 中（需要系统配置） |
| 网络命名空间隔离 | 低 | 高（需要 root 权限） |
| 资源限制（cgroups） | 中 | 中（需要系统支持） |
| 代码静态分析（AST 扫描） | 高 | 低（纯 Python） |

---

## 附录：流程图索引

1. [沙箱架构层次图](#12-架构层次)
2. [UDS 传输架构图](#21-本地后端-uds---unix-domain-socket)
3. [文件 RPC 传输架构图](#22-远程后端文件-rpc)
4. [完整执行流程图](#31-完整执行流程)
5. [多层安全架构图](#41-多层安全架构)
6. [进程组终止流程图](#62-进程组强制终止)
7. [环境变量过滤流程图](#72-环境变量构建流程)
8. [工具白名单验证流程图](#83-白名单验证逻辑)

---

## 参考文件

- 核心实现：[tools/code_execution_tool.py](tools/code_execution_tool.py)（1400+ 行）
- 沙箱执行脚本：[tools/sandbox_runner.py](tools/sandbox_runner.py)（内部文件）
- 环境变量过滤：[tools/environments/local.py](tools/environments/local.py)（`_build_safe_env`）
- 工具注册中心：[tools/registry.py](tools/registry.py)（`dispatch` 方法）
- 敏感信息脱敏：[agent/redact.py](agent/redact.py)（`redact_sensitive_text`）
- ANSI 剥离：[tools/ansi_strip.py](tools/ansi_strip.py)（`strip_ansi`）

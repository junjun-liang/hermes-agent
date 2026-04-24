---
name: native-mcp
description: 内置MCP（Model Context Protocol）客户端，连接到外部MCP服务器、发现其工具并将其注册为原生Hermes Agent工具。支持stdio和HTTP传输，具有自动重连、安全过滤和零配置工具注入。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [MCP, 工具, 集成]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent内置MCP客户端，在启动时连接到MCP服务器、发现其工具并使它们可作为智能体直接调用的一级工具。无需桥接CLI — 来自MCP服务器的工具与内置工具如`terminal`、`read_file`等一起出现。

## 何时使用

当您需要时使用：
- 从Hermes Agent内部连接到MCP服务器并使用其工具
- 通过MCP添加外部功能（文件系统访问、GitHub、数据库、API）
- 运行本地基于stdio的MCP服务器（npx、uvx或任何命令）
- 连接远程HTTP/StreamableHTTP MCP服务器
- MCP工具自动发现并在每次对话中可用

对于从终端临时一次性调用MCP工具而无需配置的情况，请参阅`mcporter`技能。

## 前置条件

- **mcp Python包** — 可选依赖；使用`pip install mcp`安装。如果未安装，MCP支持将静默禁用。
- **Node.js** — `npx`基础MCP服务器所需（大多数社区服务器）
- **uv** — `uvx`基础MCP服务器所需（基于Python的服务器）

安装MCP SDK：

```bash
pip install mcp
# 或使用uv：
uv pip install mcp
```

## 快速开始

将MCP服务器添加到`~/.hermes/config.yaml`的`mcp_servers`键下：

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

重启Hermes Agent。启动时它将：
1. 连接到服务器
2. 发现可用工具
3. 使用`mcp_time_*`前缀注册它们
4. 将它们注入所有平台工具集

然后您可以自然地使用工具 — 只需让智能体获取当前时间。

## 配置参考

`mcp_servers`下的每个条目是映射到其配置的服务器名称。有两种传输类型：**stdio**（基于命令）和**HTTP**（基于url）。

### Stdio传输（command + args）

```yaml
mcp_servers:
  server_name:
    command: "npx"             # （必需）要运行的可执行文件
    args: ["-y", "pkg-name"]   # （可选）命令参数，默认：[]
    env:                       # （可选）子进程的环境变量
      SOME_API_KEY: "value"
    timeout: 120               # （可选）每次工具调用超时秒数，默认：120
    connect_timeout: 60        # （可选）初始连接超时秒数，默认：60
```

### HTTP传输（url）

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # （必需）服务器URL
    headers:                                     # （可选）HTTP请求头
      Authorization: "Bearer sk-..."
    timeout: 180               # （可选）每次工具调用超时秒数，默认：120
    connect_timeout: 60        # （可选）初始连接超时秒数，默认：60
```

### 所有配置选项

| 选项            | 类型   | 默认值 | 描述                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | 要运行的可执行文件（stdio传输，必需）     |
| `args`            | list   | `[]`    | 传递给命令的参数                   |
| `env`             | dict   | `{}`    | 子进程的额外环境变量    |
| `url`             | string | --      | 服务器URL（HTTP传输，必需）             |
| `headers`         | dict   | `{}`    | 每个请求发送的HTTP请求头              |
| `timeout`         | int    | `120`   | 每次工具调用超时秒数                  |
| `connect_timeout` | int    | `60`    | 初始连接和发现的超时      |

注意：服务器配置必须有`command`（stdio）或`url`（HTTP），不能同时有两者。

## 工作原理

### 启动发现

Hermes Agent启动时，`discover_mcp_tools()`在工具初始化期间调用：

1. 从`~/.hermes/config.yaml`读取`mcp_servers`
2. 对于每个服务器，在专用后台事件循环中产生连接
3. 初始化MCP会话并调用`list_tools()`发现可用工具
4. 将每个工具注册到Hermes工具注册表

### 工具命名约定

MCP工具使用以下命名模式注册：

```
mcp_{server_name}_{tool_name}
```

名称中的连字符和点替换为下划线以兼容LLM API。

示例：
- 服务器`filesystem`，工具`read_file` → `mcp_filesystem_read_file`
- 服务器`github`，工具`list-issues` → `mcp_github_list_issues`
- 服务器`my-api`，工具`fetch.data` → `mcp_my_api_fetch_data`

### 自动注入

发现后，MCP工具自动注入所有`hermes-*`平台工具集（CLI、Discord、Telegram等）。这意味着MCP工具在每次对话中都可用，无需任何额外配置。

### 连接生命周期

- 每个服务器作为长期存在的asyncio Task在后台守护线程中运行
- 连接在智能体进程的整个生命周期内持续存在
- 如果连接断开，自动重连并指数退避（最多5次重试，最大60秒退避）
- 智能体关闭时，所有连接优雅关闭

### 幂等性

`discover_mcp_tools()`是幂等的 — 多次调用只连接到尚未连接的服务器。失败的服务器在后续调用中重试。

## 传输类型

### Stdio传输

最常见的传输。Hermes将MCP服务器作为子进程启动并通过stdin/stdout通信。

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

子进程继承**过滤的**环境（见下方安全部分）以及您在`env`中指定的任何变量。

### HTTP / StreamableHTTP传输

用于远程或共享MCP服务器。需要`mcp`包包含HTTP客户端支持（`mcp.client.streamable_http`）。

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

如果您安装的`mcp`版本中HTTP支持不可用，服务器将失败并显示ImportError，其他服务器将正常继续。

## 安全

### 环境变量过滤

对于stdio服务器，Hermes **不**将完整的shell环境传递给MCP子进程。仅继承安全基线变量：

- `PATH`、`HOME`、`USER`、`LANG`、`LC_ALL`、`TERM`、`SHELL`、`TMPDIR`
- 任何`XDG_*`变量

除非您通过`env`配置键显式添加，否则所有其他环境变量（API密钥、令牌、机密）都被排除。这防止意外凭证泄露到不受信任的MCP服务器。

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # 仅此令牌传递给子进程
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### 错误消息中的凭证剥离

如果MCP工具调用失败，错误消息中的任何类似凭证的模式在显示给LLM前自动脱敏。包括：

- GitHub PAT（`ghp_...`）
- OpenAI样式密钥（`sk-...`）
- Bearer令牌
- 通用`token=`、`key=`、`API_KEY=`、`password=`、`secret=`模式

## 故障排除

### "MCP SDK not available -- skipping MCP tool discovery"

未安装`mcp` Python包。安装它：

```bash
pip install mcp
```

### "No MCP servers configured"

`~/.hermes/config.yaml`中没有`mcp_servers`键，或为空。添加至少一个服务器。

### "Failed to connect to MCP server 'X'"

常见原因：
- **命令未找到**：`command`二进制文件不在PATH上。确保`npx`、`uvx`或相关命令已安装。
- **包未找到**：对于npx服务器，npm包可能不存在或需要args中的`-y`自动安装。
- **超时**：服务器启动时间过长。增加`connect_timeout`。
- **端口冲突**：对于HTTP服务器，URL可能不可达。

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

您安装的`mcp`版本不包含HTTP客户端支持。升级：

```bash
pip install --upgrade mcp
```

### 工具未出现

- 检查服务器列在`mcp_servers`下（不是`mcp`或`servers`）
- 确保YAML缩进正确
- 查看Hermes Agent启动日志查找连接消息
- 工具名称以`mcp_{server}_{tool}`为前缀 — 查找该模式

### 连接持续断开

客户端最多重试5次，指数退避（1秒、2秒、4秒、8秒、16秒，上限60秒）。如果服务器根本不可达，5次尝试后放弃。检查服务器进程和网络连接。

## 示例

### 时间服务器（uvx）

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

注册工具如`mcp_time_get_current_time`。

### 文件系统服务器（npx）

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

注册工具如`mcp_filesystem_read_file`、`mcp_filesystem_write_file`、`mcp_filesystem_list_directory`。

### 带认证的GitHub服务器

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

注册工具如`mcp_github_list_issues`、`mcp_github_create_pull_request`等。

### 远程HTTP服务器

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### 多个服务器

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

所有服务器的所有工具同时注册并可用。每个服务器的工具以其名称为前缀以避免冲突。

## Sampling（服务器发起的LLM请求）

Hermes支持MCP的`sampling/createMessage`功能 — MCP服务器可以在工具执行期间通过智能体请求LLM完成。这支持智能体循环内的工作流程（数据分析、内容生成、决策）。

Sampling **默认启用**。按服务器配置：

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # 默认：true
      model: "gemini-3-flash" # 模型覆盖（可选）
      max_tokens_cap: 4096    # 每次请求最大令牌数
      timeout: 30             # LLM调用超时（秒）
      max_rpm: 10             # 每分钟最大请求数
      allowed_models: []      # 模型白名单（空 = 全部）
      max_tool_rounds: 5      # 工具循环限制（0 = 禁用）
      log_level: "info"       # 审计详细程度
```

服务器还可以在sampling请求中包含`tools`，用于多轮工具增强工作流程。`max_tool_rounds`配置防止无限工具循环。每个服务器的审计指标（请求数、错误数、令牌数、工具使用数）通过`get_mcp_status()`跟踪。

使用`sampling: { enabled: false }`禁用不受信任服务器的sampling。

## 注意事项

- 从智能体角度看，MCP工具调用是同步的，但在专用后台事件循环上异步运行
- 工具结果作为JSON返回，格式为`{"result": "..."}`或`{"error": "..."}`
- 原生MCP客户端独立于`mcporter` — 您可以同时使用两者
- 服务器连接是持久的，同一智能体进程中的所有对话共享
- 添加或删除服务器需要重启智能体（当前不支持热重载）

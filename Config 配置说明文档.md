# Hermes-Agent Config 配置说明文档

> 基于你的个人配置文件整理的完整说明文档

**整理日期**: 2026-04-29  
**配置文件**: `~/.hermes/config.yaml`  
**配置版本**: 16  
**适用版本**: Hermes-Agent v2.0+

---

## 📌 文档说明

本文档基于你的个人配置文件 `~/.hermes/config.yaml` 整理，包含：
- ✅ 所有配置项的详细说明
- ✅ 当前配置值解读
- ✅ 推荐配置建议
- ✅ 快速修改命令
- ✅ 配置最佳实践

**你的配置特点**:
- 使用阿里云通义千问 3.5 Plus 模型
- 仅启用 CLI 核心工具集
- DEBUG 日志级别（便于调试）
- 可爱风格界面（kawaii）
- 启用 Tirith 安全检查
- 启用长期记忆和用户画像

---

## 📋 目录

1. [核心配置总览](#1-核心配置总览)
2. [模型与 Provider 配置](#2-模型与 provider-配置)
3. [Agent 运行时配置](#3-agent-运行时配置)
4. [终端与执行环境](#4-终端与执行环境)
5. [浏览器与自动化](#5-浏览器与自动化)
6. [上下文与压缩](#6-上下文与压缩)
7. [辅助 LLM 服务](#7-辅助-llm-服务)
8. [显示与界面](#8-显示与界面)
9. [语音与音频](#9-语音与音频)
10. [记忆与委托](#10-记忆与委托)
11. [安全与权限](#11-安全与权限)
12. [日志与网络](#12-日志与网络)
13. [平台特定配置](#13-平台特定配置)
14. [高级配置](#15-高级配置)
15. [配置速查表](#14-配置速查表)
16. [配置总结](#16-配置总结)

---

## 1. 核心配置总览

### 你的当前配置

```yaml
# 主模型配置
model:
  default: qwen3.5-plus-2026-02-15
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1

# 工具集配置
toolsets:
  - hermes-cli
```

### 配置说明

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `model.default` | `qwen3.5-plus-2026-02-15` | 默认使用的 LLM 模型 |
| `model.base_url` | 阿里云 DashScope | API 端点地址 |
| `toolsets` | `hermes-cli` | 启用的工具集（仅 CLI 工具） |

**解读**:
- ✅ 使用阿里云通义千问 3.5 Plus 模型
- ✅ 通过 DashScope 兼容模式 API 访问
- ✅ 仅启用 CLI 核心工具集（无浏览器、网络等工具）

---

## 2. 模型与 Provider 配置

### 2.1 主模型配置

```yaml
model:
  default: qwen3.5-plus-2026-02-15          # 默认模型
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
```

**你的配置**:
- ✅ 使用阿里云 DashScope 兼容模式 API
- ✅ 模型：通义千问 3.5 Plus（2026-02-15 版本）
- ✅ 适合复杂任务、代码生成、逻辑推理

### 2.2 Provider 配置

```yaml
providers: {}                              # 无自定义 provider
fallback_providers: []                     # 无备用 provider
credential_pool_strategies: {}             # 无凭证池策略
```

**配置说明**:
- **`default`**: 默认使用的模型名称
  - 当前：`qwen3.5-plus-2026-02-15` (通义千问 3.5 Plus)
  - 格式：`provider/model-name` 或 `model-name`
  
- **`base_url`**: API 端点地址
  - 当前：阿里云 DashScope 兼容模式 v1
  - 用于 OpenAI 兼容格式的 API 调用

**修改建议**:
```bash
# 切换到其他模型
hermes config set model.default anthropic/claude-sonnet-4
hermes config set model.base_url https://api.anthropic.com/v1
```

### 2.2 Provider 配置

```yaml
providers: {}                      # 空（使用默认 provider）
fallback_providers: []             # 无备用 provider
credential_pool_strategies: {}     # 无凭证池策略
```

**配置说明**:
- **`providers`**: 自定义 provider 配置（当前为空）
- **`fallback_providers`**: 备用 provider 列表（主 provider 失败时使用）
- **`credential_pool_strategies`**: API Key 轮换策略

**你的配置**:
- ❌ 未配置备用 provider（主 provider 失败时会直接报错）
- ❌ 未配置凭证池策略（不支持多 API Key 轮换）

**推荐配置**（高可用）:
```yaml
fallback_providers:
  - provider: openrouter
    model: anthropic/claude-sonnet-4
  - provider: zai
    model: glm-4-plus
```

**修改命令**:
```bash
# 添加备用 provider
hermes config set fallback_providers '[{"provider": "openrouter", "model": "anthropic/claude-sonnet-4"}]'
```

---

## 3. Agent 运行时配置

### 你的配置

```yaml
agent:
  max_turns: 90                    # 最大对话轮次
  gateway_timeout: 1800            # 网关超时（30 分钟）
  restart_drain_timeout: 60        # 重启排干超时（60 秒）
  service_tier: ''                 # 服务等级（空）
  tool_use_enforcement: auto       # 工具使用强制策略
  gateway_timeout_warning: 900     # 超时警告阈值（15 分钟）
  gateway_notify_interval: 600     # 通知间隔（10 分钟）
```

### 详细参数说明

| 参数 | 当前值 | 说明 | 推荐值 |
|------|--------|------|--------|
| `max_turns` | 90 | 单次对话最大工具调用次数 | 50-100 |
| `gateway_timeout` | 1800 | 网关请求最大超时（秒） | 1800 |
| `restart_drain_timeout` | 60 | Agent 重启时排干时间 | 60 |
| `service_tier` | `''` | API 服务等级（如 `priority`） | 按需设置 |
| `tool_use_enforcement` | `auto` | 工具使用策略 | `auto` |
| `gateway_timeout_warning` | 900 | 超时前警告时间 | 900 |
| `gateway_notify_interval` | 600 | 长任务通知间隔 | 600 |

**tool_use_enforcement 选项**:
- `auto` - 自动决定是否使用工具（推荐）
- `strict` - 强制使用工具
- `none` - 不使用工具

---

## 4. 终端与执行环境

### 你的配置

```yaml
terminal:
  backend: local                   # 后端类型：本地
  modal_mode: auto                 # Modal 模式：自动
  cwd: .                           # 工作目录：当前目录
  timeout: 180                     # 命令超时：180 秒
  env_passthrough: []              # 环境变量透传（空）
  
  # Docker 配置
  docker_image: nikolaik/python-nodejs:python3.11-nodejs20
  docker_forward_env: []
  docker_env: {}
  
  # Singularity 配置
  singularity_image: docker://nikolaik/python-nodejs:python3.11-nodejs20
  
  # Modal 配置
  modal_image: nikolaik/python-nodejs:python3.11-nodejs20
  
  # Daytona 配置
  daytona_image: nikolaik/python-nodejs:python3.11-nodejs20
  
  # 容器资源限制
  container_cpu: 1                 # CPU 核心数
  container_memory: 5120           # 内存（MB）
  container_disk: 51200            # 磁盘（MB）
  container_persistent: true       # 持久化容器
  
  # Docker 卷挂载
  docker_volumes: []               # 无额外卷挂载
  docker_mount_cwd_to_workspace: false  # 不挂载工作目录
  
  # 其他配置
  persistent_shell: true           # 持久化 shell 会话
```

### 核心参数说明

#### 基础配置

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `backend` | `local` | 终端后端：`local`, `docker`, `ssh`, `modal`, `daytona` |
| `cwd` | `.` | 工作目录（`.` = 当前目录） |
| `timeout` | `180` | 命令执行超时时间（秒） |

#### Docker 配置

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `docker_image` | `nikolaik/python-nodejs:python3.11-nodejs20` | Docker 镜像 |
| `docker_volumes` | `[]` | 额外卷挂载列表 |
| `docker_mount_cwd_to_workspace` | `false` | 是否挂载工作目录到容器 |
| `container_cpu` | `1` | CPU 核心数限制 |
| `container_memory` | `5120` | 内存限制（5GB） |
| `container_disk` | `51200` | 磁盘限制（50GB） |
| `container_persistent` | `true` | 容器持久化（重启后保留） |

#### 其他后端配置

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `singularity_image` | `docker://nikolaik/python-nodejs:python3.11-nodejs20` | Singularity 镜像 |
| `modal_image` | `nikolaik/python-nodejs:python3.11-nodejs20` | Modal 后端镜像 |
| `daytona_image` | `nikolaik/python-nodejs:python3.11-nodejs20` | Daytona 后端镜像 |
| `modal_mode` | `auto` | Modal 模式：`auto`, `always`, `never` |

**你的配置**:
- ✅ 统一使用 `nikolaik/python-nodejs:python3.11-nodejs20` 镜像（所有后端）
- ✅ 未配置 Docker 卷挂载（安全隔离）
- ✅ 未启用工作目录挂载（避免文件泄露）

**推荐配置**（根据需求调整）:
```yaml
terminal:
  # 本地开发
  backend: local
  cwd: .
  
  # 或 Docker 隔离
  backend: docker
  docker_image: nikolaik/python-nodejs:python3.11-nodejs20
  container_cpu: 2
  container_memory: 4096
```

---

## 5. 浏览器与自动化

### 你的配置

```yaml
browser:
  inactivity_timeout: 120          # 无活动超时（2 分钟）
  command_timeout: 30              # 命令超时（30 秒）
  record_sessions: false           # 不记录会话
  allow_private_urls: false        # 不允许私有 URL
  camofox:
    managed_persistence: false     # 不管理持久化
```

### 参数说明

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `inactivity_timeout` | `120` | 浏览器无活动超时（秒） |
| `command_timeout` | `30` | 单个命令超时时间（秒） |
| `record_sessions` | `false` | 是否录制浏览器会话（用于调试） |
| `allow_private_urls` | `false` | 是否允许访问内网/私有 URL |

**安全建议**:
- ✅ `allow_private_urls: false` - 防止 SSRF 攻击
- ✅ `record_sessions: false` - 除非需要调试

---

## 6. 上下文与压缩

### 你的配置

```yaml
checkpoints:
  enabled: true                    # 启用检查点
  max_snapshots: 50                # 最大快照数

file_read_max_chars: 100000        # 文件读取最大字符数

compression:
  enabled: true                    # 启用上下文压缩
  threshold: 0.5                   # 压缩阈值（50%）
  target_ratio: 0.2                # 目标压缩率（20%）
  protect_last_n: 20               # 保护最近 20 轮对话
  summary_model: ''                # 摘要模型（自动）
  summary_provider: auto           # 摘要 provider（自动）
```

### 上下文压缩配置

**核心参数**:

| 参数 | 当前值 | 说明 | 推荐值 |
|------|--------|------|--------|
| `enabled` | `true` | 是否启用自动压缩 | `true` |
| `threshold` | `0.5` | 使用率达到 50% 时触发压缩 | 0.4-0.6 |
| `target_ratio` | `0.2` | 压缩到原始大小的 20% | 0.15-0.3 |
| `protect_last_n` | `20` | 保护最近 20 轮对话不被压缩 | 10-30 |

**压缩流程**:
```
上下文使用率 > 50%
    ↓
调用辅助 LLM 总结中间对话
    ↓
保留最近 20 轮 + 摘要
    ↓
上下文大小 ≈ 原始 20%
```

**推荐配置**（长对话场景）:
```yaml
compression:
  enabled: true
  threshold: 0.4              # 更早触发压缩
  target_ratio: 0.25
  protect_last_n: 30          # 保护更多最近对话
  summary_model: qwen3.5-plus-2026-02-15  # 使用当前模型
```

---

## 7. 辅助 LLM 服务

### 你的配置

```yaml
auxiliary:
  # 视觉服务
  vision:
    provider: auto
    model: ''
    base_url: ''
    api_key: ''
    timeout: 120
    download_timeout: 30
  
  # 网页提取
  web_extract:
    provider: auto
    model: ''
    base_url: ''
    api_key: ''
    timeout: 360
  
  # 上下文压缩
  compression:
    provider: auto
    model: ''
    base_url: ''
    api_key: ''
    timeout: 120
  
  # 会话搜索
  session_search:
    provider: auto
    model: ''
    base_url: ''
    api_key: ''
    timeout: 30
  
  # 技能中心
  skills_hub:
    provider: auto
    model: ''
    base_url: ''
    api_key: ''
    timeout: 30
  
  # 审批服务
  approval:
    provider: auto
    model: ''
    base_url: ''
    api_key: ''
    timeout: 30
  
  # MCP 服务
  mcp:
    provider: auto
    model: ''
    base_url: ''
    api_key: ''
    timeout: 30
  
  # 记忆刷新
  flush_memories:
    provider: auto
    model: ''
    base_url: ''
    api_key: ''
    timeout: 30
```

### 配置说明

**所有辅助服务当前配置**:
- **`provider: auto`** - 自动选择 provider（使用主模型）
- **`model: ''`** - 空（使用默认模型）
- **`base_url: ''`** - 空（使用默认端点）
- **`api_key: ''`** - 空（使用主 API Key）

**推荐配置**（性能优化）:

```yaml
auxiliary:
  # 使用快速模型进行压缩
  compression:
    provider: auto
    model: qwen3.5-plus-2026-02-15
    timeout: 60
  
  # 使用大上下文模型进行会话搜索
  session_search:
    provider: auto
    model: qwen3.5-plus-2026-02-15
    timeout: 30
  
  # 视觉任务使用专用模型
  vision:
    provider: auto
    model: qwen-vl-max
    timeout: 120
```

---

## 8. 显示与界面

### 你的配置

```yaml
display:
  compact: false                 # 非紧凑模式
  personality: kawaii            # 人格：可爱风格
  resume_display: full           # 恢复显示：完整
  busy_input_mode: interrupt     # 忙碌时输入：中断
  bell_on_complete: false        # 完成时不响铃
  show_reasoning: false          # 不显示推理过程
  streaming: false               # 非流式输出
  inline_diffs: true             # 内联显示差异
  show_cost: false               # 不显示成本
  skin: default                  # 皮肤：默认
  interim_assistant_messages: true  # 显示中间消息
  tool_progress_command: false   # 不显示工具进度命令
  tool_preview_length: 0         # 工具预览长度（0=自动）
  tool_progress: all             # 工具进度：显示所有
```

### 核心参数说明

#### 界面风格

| 参数 | 当前值 | 说明 | 选项 |
|------|--------|------|------|
| `personality` | `kawaii` | Agent 人格 | `kawaii`, `professional`, `minimal` |
| `skin` | `default` | 主题皮肤 | `default`, `ares`, `mono`, `slate` |
| `compact` | `false` | 紧凑模式 | `true`, `false` |

#### 输出控制

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `streaming` | `false` | 是否流式输出响应 |
| `show_reasoning` | `false` | 是否显示 LLM 推理过程 |
| `show_cost` | `false` | 是否显示 API 调用成本 |
| `inline_diffs` | `true` | 内联显示文件差异 |

#### 交互行为

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `busy_input_mode` | `interrupt` | Agent 忙碌时接受输入的处理方式 |
| `bell_on_complete` | `false` | 任务完成时是否响铃提醒 |
| `tool_progress` | `all` | 工具进度显示级别 |

**推荐配置**（开发调试）:
```yaml
display:
  streaming: true              # 流式输出（更快看到响应）
  show_reasoning: true         # 显示推理（便于调试）
  show_cost: true              # 显示成本（监控开销）
  personality: professional    # 专业风格
```

**推荐配置**（生产环境）:
```yaml
display:
  streaming: true
  show_reasoning: false        # 隐藏推理（更简洁）
  show_cost: false
  compact: true                # 紧凑模式
```

---

## 9. 语音与音频

### TTS（文本转语音）

```yaml
tts:
  provider: edge               # TTS provider: Microsoft Edge
  edge:
    voice: en-US-AriaNeural    # Edge 语音：Aria（美式英语）
  elevenlabs:
    voice_id: pNInz6obpgDQGcFmaJgB
    model_id: eleven_multilingual_v2
  openai:
    model: gpt-4o-mini-tts
    voice: alloy
  mistral:
    model: voxtral-mini-tts-2603
    voice_id: c69964a6-ab8b-4f8a-9465-ec0925096ec8
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

### STT（语音转文本）

```yaml
stt:
  enabled: true                # 启用语音输入
  provider: local              # 本地 STT
  local:
    model: base                # Whisper base 模型
    language: ''               # 自动检测语言
  openai:
    model: whisper-1
  mistral:
    model: voxtral-mini-latest
```

### 语音控制

```yaml
voice:
  record_key: ctrl+b           # 录音快捷键
  max_recording_seconds: 120   # 最大录音时长（2 分钟）
  auto_tts: false              # 不自动 TTS 回复
  silence_threshold: 200       # 静音检测阈值
  silence_duration: 3.0        # 静音持续时间（秒）
```

**配置说明**:

| 服务 | Provider | 说明 |
|------|---------|------|
| **TTS** | `edge` | Microsoft Edge TTS（免费、快速） |
| **STT** | `local` | 本地 Whisper 模型（离线、隐私） |

**推荐配置**（高质量）:
```yaml
tts:
  provider: elevenlabs         # 更自然的语音
  elevenlabs:
    voice_id: Rachel           # 推荐语音
    model_id: eleven_multilingual_v2

stt:
  provider: openai             # 更高识别率
  openai:
    model: whisper-1
```

---

## 10. 记忆与委托

### 记忆系统

```yaml
memory:
  memory_enabled: true           # 启用记忆功能
  user_profile_enabled: true     # 启用用户画像
  memory_char_limit: 2200        # 记忆字符限制
  user_char_limit: 1375          # 用户画像字符限制
  provider: ''                   # 空（使用默认）
```

**配置说明**:

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `memory_enabled` | `true` | 是否启用长期记忆 |
| `user_profile_enabled` | `true` | 是否启用用户画像 |
| `memory_char_limit` | `2200` | 单条记忆最大字符数 |
| `user_char_limit` | `1375` | 用户画像最大字符数 |

### 委托配置

```yaml
delegation:
  model: ''                    # 空（使用默认）
  provider: ''                 # 空（使用默认）
  base_url: ''                 # 空（使用默认端点）
  api_key: ''                  # 空（使用默认 API Key）
  max_iterations: 50           # 子 agent 最大迭代次数
  reasoning_effort: ''         # 推理努力程度（空）
```

**配置说明**:

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `max_iterations` | `50` | 子 agent 最大工具调用次数 |
| `reasoning_effort` | `''` | 推理努力：`low`, `medium`, `high` |

**推荐配置**（复杂任务）:
```yaml
delegation:
  model: qwen3.5-plus-2026-02-15
  max_iterations: 80
  reasoning_effort: high
```

---

## 11. 安全与权限

### 你的配置

```yaml
approvals:
  mode: manual                 # 审批模式：手动
  timeout: 60                  # 审批超时（60 秒）

command_allowlist:
  - script execution via -e/-c flag  # 允许通过-e/-c 标志执行脚本

security:
  redact_secrets: true         # 自动脱敏敏感信息
  tirith_enabled: true         # 启用 Tirith 安全检查
  tirith_path: tirith          # Tirith 路径
  tirith_timeout: 5            # Tirith 超时（5 秒）
  tirith_fail_open: true       # Tirith 失败时放行
  
  website_blocklist:
    enabled: false             # 未启用网站黑名单
    domains: []                # 黑名单域名（空）
    shared_files: []           # 共享文件（空）
```

### 安全配置说明

#### 命令审批

| 参数 | 当前值 | 说明 | 选项 |
|------|--------|------|------|
| `mode` | `manual` | 审批模式 | `manual`, `auto`, `off` |
| `timeout` | `60` | 审批超时时间（秒） | - |

**审批模式**:
- `manual` - 手动审批每个危险命令
- `auto` - 自动审批（基于规则）
- `off` - 禁用审批

#### Tirith 安全检查

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `tirith_enabled` | `true` | 是否启用 Tirith 安全检查 |
| `tirith_timeout` | `5` | 检查超时时间（秒） |
| `tirith_fail_open` | `true` | 检查失败时是否放行 |

**推荐配置**（生产环境）:
```yaml
security:
  redact_secrets: true
  tirith_enabled: true
  tirith_fail_open: false      # 检查失败时阻止（更安全）
  
  website_blocklist:
    enabled: true
    domains:
      - malicious-site.com
      - phishing-domain.com
```

---

## 12. 日志与网络

### 日志配置

```yaml
logging:
  level: DEBUG                 # 日志级别：DEBUG
  max_size_mb: 5               # 单文件最大大小（5MB）
  backup_count: 3              # 备份文件数量（3 个）
```

**配置说明**:

| 参数 | 当前值 | 说明 | 选项 |
|------|--------|------|------|
| `level` | `DEBUG` | 日志级别 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `max_size_mb` | `5` | 日志轮转大小 | - |
| `backup_count` | `3` | 保留的备份数量 | - |

**推荐配置**:

**开发环境**:
```yaml
logging:
  level: DEBUG                 # 详细日志
```

**生产环境**:
```yaml
logging:
  level: INFO                  # 仅记录重要信息
  max_size_mb: 10
  backup_count: 7
```

### 网络配置

```yaml
network:
  force_ipv4: false            # 不强制使用 IPv4
```

**说明**:
- `force_ipv4: true` - 仅使用 IPv4（解决 IPv6 兼容性问题）
- `force_ipv4: false` - 自动选择（默认）

---

## 13. 平台特定配置

### Discord 配置

```yaml
discord:
  require_mention: true        # 需要@提及
  free_response_channels: ''   # 自由响应频道（空）
  allowed_channels: ''         # 允许的频道（空）
  auto_thread: true            # 自动创建主题
  reactions: true              # 启用反应表情
```

**配置说明**:

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `require_mention` | `true` | 是否需要@机器人才能响应 |
| `auto_thread` | `true` | 是否自动创建主题线程 |
| `reactions` | `true` | 是否使用表情反应 |

### WhatsApp 配置

```yaml
whatsapp: {}                   # 无特殊配置
```

### Cron 定时任务

```yaml
cron:
  wrap_response: true          # 包装定时任务响应
```

### 会话重置

```yaml
session_reset:
  mode: both                   # 重置模式：空闲 + 定时
  idle_minutes: 1440           # 空闲超时（24 小时）
  at_hour: 4                   # 定时重置时间（凌晨 4 点）
```

**配置说明**:

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `mode` | `both` | 重置模式：`idle`, `scheduled`, `both` |
| `idle_minutes` | `1440` | 空闲 24 小时后重置会话 |
| `at_hour` | `4` | 每天凌晨 4 点重置会话 |

---

## 15. 高级配置

### 15.1 智能模型路由

```yaml
smart_model_routing:
  enabled: false               # 未启用智能路由
  max_simple_chars: 160        # 简单任务最大字符数
  max_simple_words: 28         # 简单任务最大单词数
  cheap_model: {}              # 廉价模型配置（空）
```

**配置说明**:
- **`enabled`**: 是否启用智能模型路由
  - `true` - 自动将简单任务路由到廉价模型
  - `false` - 所有任务使用默认模型
- **`max_simple_chars`**: 字符数低于此值视为简单任务
- **`max_simple_words`**: 单词数低于此值视为简单任务
- **`cheap_model`**: 廉价模型配置（如 `{"model": "gpt-4o-mini"}`）

**推荐配置**（节省成本）:
```yaml
smart_model_routing:
  enabled: true
  max_simple_chars: 200
  max_simple_words: 30
  cheap_model:
    model: qwen3.5-plus-2026-02-15  # 使用当前模型（已很经济）
```

### 15.2 隐私保护

```yaml
privacy:
  redact_pii: false            # 不自动脱敏个人身份信息
```

**配置说明**:
- **`redact_pii`**: 是否自动脱敏 PII（个人身份信息）
  - `true` - 自动隐藏姓名、邮箱、电话等
  - `false` - 不自动脱敏

**推荐配置**（隐私敏感场景）:
```yaml
privacy:
  redact_pii: true
```

### 15.3 人类延迟模拟

```yaml
human_delay:
  mode: 'off'                  # 关闭人类延迟模拟
  min_ms: 800                  # 最小延迟（800ms）
  max_ms: 2500                 # 最大延迟（2500ms）
```

**配置说明**:
- **`mode`**: 人类延迟模拟模式
  - `'off'` - 关闭延迟模拟
  - `'typing'` - 模拟打字延迟
  - `'thinking'` - 模拟思考延迟
- **`min_ms`**: 最小延迟毫秒数
- **`max_ms`**: 最大延迟毫秒数

**使用场景**:
- 让 AI 响应更像人类（避免瞬间回复）
- 适用于聊天机器人、虚拟助手

### 15.4 上下文引擎

```yaml
context:
  engine: compressor           # 上下文引擎：压缩器
```

**配置说明**:
- **`engine`**: 上下文管理引擎
  - `compressor` - 使用上下文压缩（默认）
  - 其他引擎（未来扩展）

### 15.5 预填充消息

```yaml
prefill_messages_file: ''      # 预填充消息文件（空）
```

**配置说明**:
- **`prefill_messages_file`**: 预填充消息文件路径
  - 空 - 不使用预填充
  - 文件路径 - 从文件加载预填充消息

**使用场景**:
- 预设系统提示
- 预设常用回复模板

### 15.6 技能外部目录

```yaml
skills:
  external_dirs: []            # 无外部技能目录
```

**配置说明**:
- **`external_dirs`**: 外部技能目录列表
  - 空 - 仅使用默认技能目录
  - 路径列表 - 额外加载外部技能

**推荐配置**（自定义技能）:
```yaml
skills:
  external_dirs:
    - ~/my-hermes-skills
    - ./custom-skills
```

### 15.7 Honcho 集成

```yaml
honcho: {}                     # 无 Honcho 配置
```

**配置说明**:
- **`honcho`**: Honcho 进程管理器配置
  - 空 - 不启用 Honcho 集成
  - 配置对象 - 启用 Honcho 管理

### 15.8 时区配置

```yaml
timezone: ''                   # 空（使用系统时区）
```

**配置说明**:
- **`timezone`**: 时区设置
  - 空 - 使用系统时区
  - 时区名称 - 如 `"Asia/Shanghai"`, `"UTC"`

**推荐配置**（中国用户）:
```yaml
timezone: Asia/Shanghai
```

### 15.9 快速命令

```yaml
quick_commands: {}             # 无快速命令
```

**配置说明**:
- **`quick_commands`**: 快速命令别名
  - 空 - 不使用快速命令
  - 字典 - 定义快速命令映射

**示例配置**:
```yaml
quick_commands:
  "build": "npm run build"
  "test": "pytest tests/ -q"
  "deploy": "git push && docker build -t app ."
```

### 15.10 自定义人格

```yaml
personalities: {}              # 无自定义人格
```

**配置说明**:
- **`personalities`**: 自定义人格配置
  - 空 - 使用内置人格
  - 配置对象 - 定义自定义人格

**示例配置**:
```yaml
personalities:
  mentor:
    name: "导师"
    style: "专业、耐心、鼓励性"
    greeting: "你好！今天想学习什么？"
  comedian:
    name: "喜剧演员"
    style: "幽默、风趣、爱开玩笑"
    greeting: "嘿！准备好笑一个了吗？"
```

---

## 14. 配置速查表

### 快速修改命令

```bash
# 修改模型
hermes config set model.default qwen3.5-plus-2026-02-15
hermes config set model.base_url https://dashscope.aliyuncs.com/compatible-mode/v1

# 修改日志级别
hermes config set logging.level INFO

# 修改显示风格
hermes config set display.personality professional
hermes config set display.streaming true

# 修改终端配置
hermes config set terminal.backend docker
hermes config set terminal.container_cpu 2

# 修改记忆配置
hermes config set memory.memory_enabled true
hermes config set memory.user_profile_enabled true
```

### 配置验证

```bash
# 查看当前配置
hermes config show

# 查看特定配置
hermes config get model.default
hermes config get display.personality

# 重置配置
hermes config reset
```

### 环境变量覆盖

```bash
# 使用环境变量覆盖配置
export HERMES_MODEL_DEFAULT="anthropic/claude-sonnet-4"
export HERMES_LOGGING_LEVEL="DEBUG"
export HERMES_DISPLAY_PERSONALITY="kawaii"
```

### 配置优先级

```
1. 命令行参数（最高优先级）
2. 环境变量
3. config.yaml 配置文件
4. 默认值（最低优先级）
```

---

## 16. 配置总结

### ✅ 你的配置特点

1. **模型**: 阿里云通义千问 3.5 Plus（DashScope 兼容模式）
2. **工具集**: 仅 CLI 核心工具（安全、简洁）
3. **日志**: DEBUG 级别（便于调试）
4. **界面**: 可爱风格（kawaii），非紧凑模式
5. **安全**: 启用 Tirith 检查，手动审批模式
6. **记忆**: 启用长期记忆和用户画像
7. **压缩**: 启用上下文压缩（50% 触发，压缩到 20%）
8. **终端**: 本地后端，持久化容器
9. **语音**: Edge TTS + 本地 Whisper STT
10. **高级功能**: 大部分未启用（可按需配置）

### 🔧 推荐优化清单

#### 高优先级（建议立即配置）

1. **添加备用 Provider** - 提高可用性
   ```bash
   hermes config set fallback_providers '[{"provider": "openrouter", "model": "anthropic/claude-sonnet-4"}]'
   ```

2. **启用流式输出** - 更快看到响应
   ```bash
   hermes config set display.streaming true
   ```

3. **优化压缩配置** - 更早触发压缩，保护更多对话
   ```bash
   hermes config set compression.threshold 0.4
   hermes config set compression.protect_last_n 30
   ```

#### 中优先级（按需配置）

4. **配置辅助 LLM** - 优化压缩和搜索性能
   ```bash
   hermes config set auxiliary.compression.model qwen3.5-plus-2026-02-15
   hermes config set auxiliary.session_search.model qwen3.5-plus-2026-02-15
   ```

5. **配置外部 Skill 目录** - 扩展技能库
   ```bash
   hermes config set skills.external_dirs '["~/my-hermes-skills"]'
   ```

6. **设置时区** - 确保定时任务时间准确
   ```bash
   hermes config set timezone Asia/Shanghai
   ```

#### 低优先级（高级功能）

7. **启用智能模型路由** - 节省成本（可选）
   ```bash
   hermes config set smart_model_routing.enabled true
   ```

8. **启用隐私保护** - 自动脱敏 PII（隐私敏感场景）
   ```bash
   hermes config set privacy.redact_pii true
   ```

9. **配置网站黑名单** - 增强安全性
   ```bash
   hermes config set security.website_blocklist.enabled true
   hermes config set security.website_blocklist.domains '["malicious-site.com"]'
   ```

### 📊 配置对比表

| 配置项 | 你的配置 | 推荐配置 | 差异 |
|--------|---------|---------|------|
| `model.default` | qwen3.5-plus | ✅ 合理 | - |
| `fallback_providers` | 无 | 建议配置 | ⚠️ 需优化 |
| `display.streaming` | false | true | ⚠️ 需优化 |
| `compression.threshold` | 0.5 | 0.4 | ⚠️ 需优化 |
| `compression.protect_last_n` | 20 | 30 | ⚠️ 需优化 |
| `logging.level` | DEBUG | INFO（生产） | ⚠️ 开发可用 |
| `skills.external_dirs` | 无 | 建议配置 | ⚠️ 需优化 |
| `timezone` | 空 | Asia/Shanghai | ⚠️ 需优化 |

### 🎯 下一步行动

```bash
# 一键优化脚本（复制粘贴执行）
hermes config set fallback_providers '[{"provider": "openrouter", "model": "anthropic/claude-sonnet-4"}]'
hermes config set display.streaming true
hermes config set compression.threshold 0.4
hermes config set compression.protect_last_n 30
hermes config set auxiliary.compression.model qwen3.5-plus-2026-02-15
hermes config set timezone Asia/Shanghai

# 验证配置
hermes config show
```

---

**文档版本**: 1.1  
**最后更新**: 2026-04-29  
**配置文件**: `~/.hermes/config.yaml`  
**配置版本**: 16  
**文档状态**: ✅ 完整

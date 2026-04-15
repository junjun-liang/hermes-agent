# Hermes Agent 配置 Ollama qwen3.5:9b 模型指南

## 快速开始

### 1. 安装和启动 Ollama

```bash
# 安装 Ollama (如果尚未安装)
curl -fsSL https://ollama.com/install.sh | sh

# 拉取 qwen3.5:9b 模型
ollama pull qwen3.5:9b

# 启动 Ollama 服务 (默认端口 11434)
ollama serve
```

### 2. 重要：设置上下文长度

**⚠️ 关键步骤**：Ollama 默认上下文长度很低，Hermes Agent 需要至少 **64K tokens** 的上下文。

#### 方法一：通过环境变量启动（推荐）

```bash
# 临时启动（当前会话有效）
OLLAMA_CONTEXT_LENGTH=65536 ollama serve

# 永久设置（Linux systemd）
sudo systemctl edit ollama.service
# 添加以下内容：
# [Service]
# Environment="OLLAMA_CONTEXT_LENGTH=65536"
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

#### 方法二：创建自定义模型文件

```bash
# 创建 Modelfile
cat > Modelfile << EOF
FROM qwen3.5:9b
PARAMETER num_ctx 65536
EOF

# 创建新模型
ollama create qwen3.5-64k -f Modelfile

# 使用新模型
ollama run qwen3.5-64k
```

#### 验证上下文长度

```bash
# 查看当前运行的模型和上下文
ollama ps

# 输出示例：
# NAME              ID              SIZE      PROCESSOR    CONTEXT
# qwen3.5:9b        abc123...       5.4 GB    100% GPU     65.5K
```

### 3. 配置 Hermes Agent

#### 方法一：交互式配置（推荐）

```bash
hermes model
```

按提示选择：
1. 选择 **"Custom endpoint (self-hosted / VLLM / etc.)"**
2. 输入 URL: `http://localhost:11434/v1`
3. 跳过 API Key（Ollama 不需要）
4. 输入模型名称：`qwen3.5:9b` 或 `qwen3.5-64k`（如果你创建了自定义模型）

#### 方法二：手动编辑配置文件

编辑 `~/.hermes/config.yaml`：

```yaml
model:
  default: qwen3.5:9b
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 65536  # 必须设置，否则会自动压缩上下文
```

### 4. 启动 Hermes

```bash
hermes
```

启动后会在横幅显示：
```
╭────────────────────────────────────────────────────╮
│  Model: qwen3.5:9b                                 │
│  Provider: custom (http://localhost:11434/v1)      │
│  Context limit: 65536 tokens                       │
╰────────────────────────────────────────────────────╯
```

---

## 完整配置示例

### ~/.hermes/config.yaml

```yaml
# =============================================================================
# 模型配置
# =============================================================================
model:
  default: qwen3.5:9b
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 65536   # 总上下文窗口（输入 + 输出）
  # max_tokens: 4096      # 可选：限制单次响应长度（默认使用模型上限）

# =============================================================================
# 终端配置
# =============================================================================
terminal:
  backend: local
  cwd: "."
  timeout: 180

# =============================================================================
# 显示配置
# =============================================================================
display:
  skin: default
  tool_progress_command: true

# =============================================================================
# 工具配置
# =============================================================================
tools:
  enabled_toolsets:
    - core
    - web
    - file
    - terminal
```

### ~/.hermes/.env（可选）

```bash
# Ollama 不需要 API key，但如果你使用其他功能可以添加
# FIRECRAWL_API_KEY=xxx     # 如果使用 Firecrawl 进行网页搜索
# BROWSERBASE_API_KEY=xxx   # 如果使用 Browserbase 进行浏览器自动化
```

---

## WSL2 用户特别配置

如果你在 Windows 上使用 WSL2，而 Ollama 运行在 Windows 主机上：

### 方法一：镜像网络模式（Windows 11 22H2+，推荐）

1. 创建或编辑 `%USERPROFILE%\.wslconfig`：
```ini
[wsl2]
networkingMode=mirrored
```

2. 重启 WSL：
```powershell
wsl --shutdown
```

3. 在 WSL2 中使用 `localhost` 访问：
```bash
curl http://localhost:11434/v1/models
```

### 方法二：使用 Windows 主机 IP（Windows 10 / 旧版本）

```bash
# 获取 Windows 主机 IP
ip route show | grep -i default | awk '{ print $3 }'
# 输出示例：172.29.192.1
```

编辑 `~/.hermes/config.yaml`：

```yaml
model:
  default: qwen3.5:9b
  provider: custom
  base_url: http://172.29.192.1:11434/v1  # 使用 Windows 主机 IP
  context_length: 65536
```

### Ollama Windows 主机配置

Ollama 默认只监听 `127.0.0.1`，需要修改以接受 WSL2 连接：

1. 打开 **系统属性** → **环境变量**
2. 添加新的 **系统变量**：
   ```
   OLLAMA_HOST=0.0.0.0
   ```
3. 重启 Ollama 服务

---

## 故障排查

### 问题 1：连接被拒绝

**症状**：
```
Error: Connection refused to http://localhost:11434/v1
```

**解决方案**：
- 确认 Ollama 正在运行：`ollama ps`
- WSL2 用户参考上面的 WSL2 网络配置
- 检查防火墙：
  ```powershell
  # Windows PowerShell (管理员)
  New-NetFirewallRule -DisplayName "Allow Ollama" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434
  ```

### 问题 2：工具调用显示为文本而不是执行

**症状**：模型输出类似 `{"name": "web_search", "arguments": {...}}` 的 JSON 文本，而不是实际调用工具。

**原因**：Ollama 默认支持工具调用，但某些模型可能不支持。

**检查模型是否支持工具调用**：
```bash
ollama show qwen3.5:9b | grep -i "tool"
```

**解决方案**：
- 确保使用支持工具调用的模型（Qwen 系列通常支持）
- 更新 Ollama 到最新版本：`ollama serve` 会显示版本号

### 问题 3：上下文限制过低

**症状**：启动时显示 `Context limit: 4096 tokens`

**解决方案**：
```bash
# 检查 Ollama 实际上下文
ollama ps

# 如果显示 4K 或更低，重启 Ollama 并设置环境变量
OLLAMA_CONTEXT_LENGTH=65536 ollama serve
```

### 问题 4：响应被截断

**症状**：回复说到一半就停止了

**可能原因**：
1. **输出 token 限制过低**：在 config.yaml 中设置 `max_tokens`
2. **上下文耗尽**：增加 `context_length`

```yaml
model:
  default: qwen3.5:9b
  context_length: 65536
  max_tokens: 8192  # 增加单次响应上限
```

### 问题 5：模型响应缓慢或内存不足

**解决方案**：
```bash
# 降低上下文长度（如果 VRAM 不足）
OLLAMA_CONTEXT_LENGTH=32768 ollama serve

# 或者使用更小的量化版本
ollama pull qwen3.5:9b-q4_k_m
```

---

## 性能优化

### GPU 配置

Ollama 自动检测并使用 GPU，但你可以手动优化：

```bash
# 查看 GPU 使用情况
ollama ps

# 强制使用特定 GPU（多 GPU 系统）
OLLAMA_GPU_LAYER=99 ollama serve
```

### 模型量化版本

| 模型 | 大小 | 推荐 VRAM | 质量 |
|------|------|----------|------|
| `qwen3.5:9b` | 原始 | 18+ GB | 最佳 |
| `qwen3.5:9b-q4_k_m` | 4-bit 量化 | 8-10 GB | 平衡 |
| `qwen3.5:9b-q3_k_m` | 3-bit 量化 | 6-8 GB | 可接受 |

```bash
# 拉取量化版本
ollama pull qwen3.5:9b-q4_k_m

# 更新配置
# ~/.hermes/config.yaml
model:
  default: qwen3.5:9b-q4_k_m
```

### 并发请求优化

```bash
# 设置最大并发请求数
OLLAMA_MAX_QUEUE=512 ollama serve

# 设置保持活动时间（秒），-1 表示永久保持
OLLAMA_KEEP_ALIVE=300 ollama serve
```

---

## 高级配置

### 命名自定义提供者

如果你有多个 Ollama 实例（例如本地开发和生产）：

```yaml
# ~/.hermes/config.yaml
custom_providers:
  - name: ollama-local
    base_url: http://localhost:11434/v1
  - name: ollama-server
    base_url: http://192.168.1.100:11434/v1

model:
  default: qwen3.5:9b
  provider: custom  # 默认使用第一个
```

在会话中切换：
```
/model custom:ollama-local:qwen3.5:9b
/model custom:ollama-server:qwen3.5:9b
```

### 启用上下文压缩

如果模型仍然频繁遇到上下文限制，启用 Hermes 的自动压缩：

```yaml
# ~/.hermes/config.yaml
context_compression:
  enabled: true
  threshold_tokens: 32768  # 超过此值时触发压缩
  compression_ratio: 0.6   # 压缩到原来的 60%
```

### 辅助模型配置

某些功能（视觉、网页摘要）使用辅助模型：

```yaml
# ~/.hermes/config.yaml
auxiliary_model:
  provider: openrouter
  model: google/gemini-2.5-flash
  # 需要 OPENROUTER_API_KEY 在 ~/.hermes/.env
```

---

## 验证配置

### 1. 测试 Ollama 服务

```bash
# 测试 API 连接
curl http://localhost:11434/v1/models

# 测试模型推理
ollama run qwen3.5:9b "你好，请介绍一下自己"
```

### 2. 测试 Hermes 配置

```bash
# 启动 Hermes
hermes

# 测试基本对话
❯ 你好

# 测试工具调用
❯ 帮我搜索一下最新的 AI 新闻

# 测试文件操作
❯ 列出当前目录的文件

# 测试终端命令
❯ 运行 python --version
```

### 3. 检查日志

```bash
# Ollama 日志
journalctl -u ollama -f  # systemd
# 或直接查看终端输出

# Hermes 日志（如果遇到问题）
hermes --debug
```

---

## 常见问题 FAQ

### Q: qwen3.5:9b 支持工具调用吗？

A: 是的，Qwen 系列模型（包括 qwen3.5）原生支持工具调用。Ollama 会自动处理工具调用格式。

### Q: 可以用 Ollama Cloud 吗？

A: 可以。配置如下：

```yaml
model:
  default: qwen3.5:9b
  provider: custom
  base_url: https://ollama.com/v1
  # 在 ~/.hermes/.env 中设置
  # OLLAMA_API_KEY=your-key
```

### Q: 如何在多个模型之间切换？

A: 使用 `/model` 命令：
```
/model custom:qwen2.5-coder:32b
/model custom:llama3.1:70b
/model custom:qwen3.5:9b
```

### Q: Ollama 和 Hermes 可以在同一台机器上运行吗？

A: 可以，它们是独立的进程。Ollama 提供模型推理服务，Hermes 是 Agent 框架。

### Q: 需要多少 VRAM？

A: qwen3.5:9b 需要：
- FP16（原始）：~18 GB
- Q4_K_M 量化：~6-8 GB
- Q3_K_M 量化：~5-6 GB

使用 `ollama ps` 查看实际使用情况。

---

## 参考资源

- [Ollama 官方文档](https://ollama.com/)
- [Ollama 模型库](https://ollama.com/library)
- [Hermes Agent 文档](https://nousresearch.github.io/hermes-agent/)
- [Qwen3.5 模型卡片](https://ollama.com/library/qwen3.5)
- [故障排查指南](https://github.com/ollama/ollama/blob/main/docs/faq.md)

---

## 总结

配置步骤速查：

```bash
# 1. 安装并启动 Ollama
ollama pull qwen3.5:9b
OLLAMA_CONTEXT_LENGTH=65536 ollama serve

# 2. 配置 Hermes
hermes model
# → 选择 Custom endpoint
# → URL: http://localhost:11434/v1
# → 模型：qwen3.5:9b

# 3. 启动并测试
hermes
```

配置完成后，你就可以使用 qwen3.5:9b 模型在 Hermes Agent 中进行对话和使用各种工具了！

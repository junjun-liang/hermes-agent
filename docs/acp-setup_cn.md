# Hermes Agent — ACP（Agent Client Protocol）设置指南

Hermes Agent 支持 **Agent Client Protocol (ACP)**，允许它在你的编辑器内部署为编程 Agent。ACP 使你的 IDE 能够向 Hermes 发送任务，Hermes 则返回文件编辑、终端命令和解释 — 所有这些都原生显示在编辑器 UI 中。

---

## 前置要求

- 已安装并配置 Hermes Agent（已完成 `hermes setup`）
- 已在 `~/.hermes/.env` 中或通过 `hermes login` 设置 API 密钥/提供商
- Python 3.11+

安装 ACP 扩展包：

```bash
pip install -e ".[acp]"
```

---

## VS Code 设置

### 1. 安装 ACP Client 扩展

打开 VS Code 并从市场安装 **ACP Client**：

- 按 `Ctrl+Shift+X`（macOS 上为 `Cmd+Shift+X`）
- 搜索 **"ACP Client"**
- 点击 **安装**

或者从命令行安装：

```bash
code --install-extension anysphere.acp-client
```

### 2. 配置 settings.json

打开你的 VS Code 设置（`Ctrl+,` → 点击 `{}` 图标打开 JSON），并添加：

```json
{
  "acpClient.agents": [
    {
      "name": "hermes-agent",
      "registryDir": "/path/to/hermes-agent/acp_registry"
    }
  ]
}
```

将 `/path/to/hermes-agent` 替换为你的 Hermes Agent 安装的实际路径（如 `~/.hermes/hermes-agent`）。

或者，如果 `hermes` 在你的 PATH 中，ACP Client 可以通过注册表目录自动发现它。

### 3. 重启 VS Code

配置完成后，重启 VS Code。你应该能在聊天/Agent 面板的 ACP Agent 选择器中看到 **Hermes Agent**。

---

## Zed 设置

Zed 内置了 ACP 支持。

### 1. 配置 Zed 设置

打开 Zed 设置（macOS 上为 `Cmd+,`，Linux 上为 `Ctrl+,`）并在你的 `settings.json` 中添加：

```json
{
  "agent_servers": {
    "hermes-agent": {
      "type": "custom",
      "command": "hermes",
      "args": ["acp"],
    },
  },
}
```

### 2. 重启 Zed

Hermes Agent 将出现在 Agent 面板中。选择它即可开始对话。

---

## JetBrains 设置（IntelliJ、PyCharm、WebStorm 等）

### 1. 安装 ACP 插件

- 打开 **设置** → **插件** → **市场**
- 搜索 **"ACP"** 或 **"Agent Client Protocol"**
- 安装并重启 IDE

### 2. 配置 Agent

- 打开 **设置** → **工具** → **ACP Agents**
- 点击 **+** 添加新 Agent
- 将注册表目录设置为你的 `acp_registry/` 文件夹：
  `/path/to/hermes-agent/acp_registry`
- 点击 **确定**

### 3. 使用 Agent

打开 ACP 面板（通常在右侧边栏）并选择 **Hermes Agent**。

---

## 你将看到什么

连接成功后，你的编辑器提供与 Hermes Agent 的原生界面：

### 聊天面板
对话界面，你可以在其中描述任务、提问和给出指令。Hermes 会响应解释和操作。

### 文件差异（Diff）
当 Hermes 编辑文件时，你会在编辑器中看到标准差异。你可以：
- **接受** 个别更改
- **拒绝** 不需要的更改
- **审查** 整个差异后再应用

### 终端命令
当 Hermes 需要运行 shell 命令（构建、测试、安装）时，编辑器会在集成终端中显示它们。根据你的设置：
- 命令可能自动运行
- 或者你可能被提示 **批准** 每条命令

### 审批流程
对于可能有破坏性的操作，编辑器会在 Hermes 继续之前提示你审批。包括：
- 文件删除
- Shell 命令
- Git 操作

---

## 配置

ACP 模式下的 Hermes Agent 使用与 CLI **相同的配置**：

- **API 密钥/提供商**：`~/.hermes/.env`
- **Agent 配置**：`~/.hermes/config.yaml`
- **技能**：`~/.hermes/skills/`
- **会话**：`~/.hermes/state.db`

你可以运行 `hermes setup` 来配置提供商，或直接编辑 `~/.hermes/.env`。

### 更改模型

编辑 `~/.hermes/config.yaml`：

```yaml
model: openrouter/nous/hermes-3-llama-3.1-70b
```

或者设置 `HERMES_MODEL` 环境变量。

### 工具集

ACP 会话默认使用精选的 `hermes-acp` 工具集。它专为编辑器工作流设计，有意排除了消息传递、定时任务管理和音频优先的 UX 功能等内容。

---

## 故障排查

### Agent 未在编辑器中显示

1. **检查注册表路径** — 确保编辑器设置中的 `acp_registry/` 目录路径正确且包含 `agent.json`。
2. **检查 `hermes` 是否在 PATH 中** — 在终端中运行 `which hermes`。如果找不到，你可能需要激活虚拟环境或将其添加到 PATH。
3. **更改设置后重启编辑器**。

### Agent 启动后立即报错

1. 运行 `hermes doctor` 检查你的配置。
2. 检查你是否有有效的 API 密钥：`hermes status`
3. 尝试在终端中直接运行 `hermes acp` 以查看错误输出。

### "Module not found" 错误

确保你安装了 ACP 扩展包：

```bash
pip install -e ".[acp]"
```

### 响应缓慢

- ACP 流式传输响应，所以你应该看到增量输出。如果 Agent 似乎卡住了，检查你的网络连接和 API 提供商状态。
- 某些提供商有速率限制。尝试切换到不同的模型/提供商。

### 终端命令权限被拒绝

如果编辑器阻止终端命令，检查你的 ACP Client 扩展设置中的自动审批或手动审批偏好设置。

### 日志

Hermes 在 ACP 模式下运行时将日志写入 stderr。检查：
- VS Code：**输出** 面板 → 选择 **ACP Client** 或 **Hermes Agent**
- Zed：**查看** → **切换终端** 并检查进程输出
- JetBrains：**事件日志** 或 ACP 工具窗口

你也可以启用详细日志记录：

```bash
HERMES_LOG_LEVEL=DEBUG hermes acp
```

---

## 进一步阅读

- [ACP 规范](https://github.com/anysphere/acp)
- [Hermes Agent 文档](https://github.com/NousResearch/hermes-agent)
- 运行 `hermes --help` 查看所有 CLI 选项

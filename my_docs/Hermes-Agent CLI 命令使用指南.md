# Hermes CLI 命令使用指南

> Hermes 命令行工具的完整命令参考  
> 文件位置：`hermes_cli/main.py`  
> 整理日期：2026-04-23

***

## 目录

1. [基础命令](#1-基础命令)
2. [网关管理](#2-网关管理)
3. [配置与设置](#3-配置与设置)
4. [系统管理](#4-系统管理)
5. [Honcho AI 记忆集成](#5-honcho-ai-记忆集成)
6. [版本与维护](#6-版本与维护)
7. [编辑器集成](#7-编辑器集成)
8. [会话管理](#8-会话管理)
9. [Claw 迁移](#9-claw-迁移)

***

## 1. 基础命令

### 1.1 交互式聊天

```bash
hermes                     # 交互式聊天（默认）
hermes chat                # 交互式聊天
```

**说明：** 启动 Hermes Agent 的交互式 CLI 界面，进入 REPL 循环与 AI 对话。

**示例：**
```bash
# 直接启动（默认 chat 模式）
hermes

# 明确指定 chat 命令
hermes chat

# 带初始消息启动
hermes chat "你好，请介绍一下自己"
```

***

## 2. 网关管理

### 2.1 网关运行

```bash
hermes gateway             # 在前台运行网关
```

**说明：** 启动消息平台网关，支持 Telegram、Discord、Slack、WhatsApp 等平台。

### 2.2 网关服务控制

```bash
hermes gateway start       # 启动网关服务
hermes gateway stop        # 停止网关服务
hermes gateway status      # 显示网关状态
```

**说明：** 以系统服务方式管理网关的生命周期。

**示例：**
```bash
# 启动网关服务
hermes gateway start

# 查看网关运行状态
hermes gateway status

# 停止网关服务
hermes gateway stop
```

### 2.3 网关服务安装

```bash
hermes gateway install     # 安装网关服务
hermes gateway uninstall   # 卸载网关服务
```

**说明：** 将网关注册为系统服务（systemd）或 Docker 容器。

***

## 3. 配置与设置

### 3.1 交互式设置

```bash
hermes setup               # 交互式设置向导
```

**说明：** 运行交互式配置向导，帮助初次用户完成 API 密钥、模型选择、工具集配置等。

**示例：**
```bash
hermes setup
```

### 3.2 认证管理

```bash
hermes logout              # 清除存储的认证信息
```

**说明：** 删除本地存储的 API 密钥和认证令牌。

***

## 4. 系统管理

### 4.1 状态检查

```bash
hermes status              # 显示所有组件的状态
```

**说明：** 检查 CLI、网关、Cron 调度器等组件的运行状态。

### 4.2 Cron 任务管理

```bash
hermes cron                # 管理 Cron 任务
hermes cron list           # 列出 Cron 任务
hermes cron status         # 检查 Cron 调度器是否运行
```

**说明：** 管理定时任务和后台调度器。

**示例：**
```bash
# 查看所有定时任务
hermes cron list

# 检查 Cron 调度器状态
hermes cron status
```

### 4.3 系统检查

```bash
hermes doctor              # 检查配置和依赖
```

**说明：** 运行诊断工具，检查系统配置、环境变量、依赖包等是否正常。

***

## 5. Honcho AI 记忆集成

### 5.1 Honcho 配置

```bash
hermes honcho setup                    # 配置 Honcho AI 记忆集成
```

**说明：** 设置与 Honcho AI 记忆系统的集成。

### 5.2 Honcho 状态

```bash
hermes honcho status                   # 显示 Honcho 配置和连接状态
```

**说明：** 查看 Honcho 记忆系统的当前配置和连接状态。

### 5.3 会话映射

```bash
hermes honcho sessions                 # 列出目录到会话名称的映射
hermes honcho map <name>               # 将当前目录映射到会话名称
```

**说明：** 管理工作目录与 Honcho 会话的映射关系。

**示例：**
```bash
# 查看所有会话映射
hermes honcho sessions

# 将当前目录映射为 "my-project" 会话
hermes honcho map my-project
```

### 5.4 Peer 设置

```bash
hermes honcho peer                     # 显示 Peer 名称和辩证设置
hermes honcho peer --user NAME         # 设置用户 Peer 名称
hermes honcho peer --ai NAME           # 设置 AI Peer 名称
hermes honcho peer --reasoning LEVEL   # 设置辩证推理级别
```

**说明：** 配置 Honcho 辩证对话系统的 Peer 身份和推理级别。

**示例：**
```bash
# 查看当前 Peer 设置
hermes honcho peer

# 设置用户 Peer 名称为 "开发者"
hermes honcho peer --user 开发者

# 设置 AI Peer 名称为 "助手"
hermes honcho peer --ai 助手

# 设置辩证推理级别为 2
hermes honcho peer --reasoning 2
```

### 5.5 记忆模式

```bash
hermes honcho mode                     # 显示当前记忆模式
hermes honcho mode [hybrid|honcho|local]  # 设置记忆模式
```

**说明：** 切换记忆系统的工作模式。

**模式说明：**
- `hybrid` - 混合模式（本地 + Honcho）
- `honcho` - 仅使用 Honcho 记忆
- `local` - 仅使用本地记忆

**示例：**
```bash
# 查看当前记忆模式
hermes honcho mode

# 切换到混合模式
hermes honcho mode hybrid
```

### 5.6 Token 预算

```bash
hermes honcho tokens                   # 显示 Token 预算设置
hermes honcho tokens --context N       # 设置 session.context() Token 上限
hermes honcho tokens --dialectic N     # 设置辩证结果字符上限
```

**说明：** 管理 Token 使用预算和上下文限制。

**示例：**
```bash
# 查看当前 Token 预算
hermes honcho tokens

# 设置上下文 Token 上限为 4000
hermes honcho tokens --context 4000

# 设置辩证结果字符上限为 8000
hermes honcho tokens --dialectic 8000
```

### 5.7 AI 身份

```bash
hermes honcho identity                 # 显示 AI Peer 身份表示
hermes honcho identity <file>          # 从文件初始化 AI Peer 身份（SOUL.md 等）
```

**说明：** 查看或设置 AI Peer 的身份配置文件。

**示例：**
```bash
# 查看当前 AI 身份
hermes honcho identity

# 从 SOUL.md 文件加载 AI 身份
hermes honcho identity SOUL.md
```

### 5.8 迁移指南

```bash
hermes honcho migrate                  # 分步迁移指南：OpenClaw 原生 → Hermes + Honcho
```

**说明：** 提供从 OpenClaw 原生模式迁移到 Hermes + Honcho 的分步指导。

***

## 6. 版本与维护

### 6.1 版本信息

```bash
hermes version             # 显示版本
```

**说明：** 显示当前安装的 Hermes Agent 版本号。

**示例：**
```bash
hermes version
# 输出：Hermes Agent v2.0.0
```

### 6.2 更新

```bash
hermes update              # 更新到最新版本
```

**说明：** 自动下载并安装最新版本。

**示例：**
```bash
hermes update
```

### 6.3 卸载

```bash
hermes uninstall           # 卸载 Hermes Agent
```

**说明：** 完全卸载 Hermes Agent 及其配置。

***

## 7. 编辑器集成

### 7.1 ACP 服务器

```bash
hermes acp                 # 作为 ACP 服务器运行，用于编辑器集成
```

**说明：** 启动 ACP (Agent Communication Protocol) 服务器，与 VS Code、Zed 等编辑器集成。

**示例：**
```bash
# 在编辑器中启动 Hermes Agent
hermes acp
```

***

## 8. 会话管理

### 8.1 会话浏览

```bash
hermes sessions browse     # 交互式会话选择器（带搜索）
```

**说明：** 打开交互式界面浏览和搜索历史会话。

**功能：**
- 🔍 搜索会话内容
- 📋 查看会话详情
- 🗑️ 删除会话
- 📤 导出会话

**示例：**
```bash
hermes sessions browse
```

***

## 9. Claw 迁移

### 9.1 迁移预览

```bash
hermes claw migrate --dry-run  # 预览迁移，不做实际更改
```

**说明：** 预览从 OpenClaw 迁移到 Hermes 的更改，不执行实际操作。

**用途：** 在实际迁移前查看将要进行的更改，评估迁移影响。

**示例：**
```bash
# 预览迁移更改
hermes claw migrate --dry-run

# 确认无误后执行实际迁移
hermes claw migrate
```

***

## 命令分类总览

| 分类 | 命令数量 | 主要功能 |
|------|----------|----------|
| **基础命令** | 2 | 交互式聊天 |
| **网关管理** | 5 | 平台适配器管理 |
| **配置与设置** | 2 | 配置向导、认证管理 |
| **系统管理** | 4 | 状态检查、Cron 任务、诊断 |
| **Honcho 集成** | 10 | 记忆系统配置 |
| **版本与维护** | 3 | 版本查看、更新、卸载 |
| **编辑器集成** | 1 | ACP 服务器 |
| **会话管理** | 1 | 会话浏览 |
| **Claw 迁移** | 1 | 迁移预览 |

***

## 快速参考

### 常用命令

```bash
# 开始聊天
hermes

# 查看状态
hermes status

# 系统检查
hermes doctor

# 配置向导
hermes setup

# 查看版本
hermes version
```

### 网关相关

```bash
# 启动网关
hermes gateway start

# 查看状态
hermes gateway status

# 停止网关
hermes gateway stop
```

### Honcho 相关

```bash
# 设置记忆模式
hermes honcho mode hybrid

# 查看 Token 预算
hermes honcho tokens

# 映射会话
hermes honcho map my-project
```

***

**文档版本：** 1.0  
**整理日期：** 2026-04-23  
**适用版本：** Hermes-Agent v2.0+  
**源文件：** `hermes_cli/main.py` (L3-43)

# Hermes Agent - 多轮对话架构设计文档索引

## 📚 文档概览

本目录包含 Hermes Agent 多轮对话系统的完整架构设计文档。通过分析源代码，我们整理了以下核心文档：

---

## 📄 文档列表

### 1. [ARCHITECTURE_ANALYSIS.md](./ARCHITECTURE_ANALYSIS.md) - 架构分析主文档
**内容**:
- 软件架构设计图 (ASCII 艺术风格)
- 核心组件详解 (AIAgent, Tool Registry, SessionDB, Context Compressor)
- 多轮对话流程图
- 工具调用详细流程
- 会话管理流程
- Gateway 多平台架构
- 关键设计模式
- 数据流图
- 配置系统
- 安全与权限
- 性能优化
- 扩展机制

**适合读者**: 架构师、高级开发者、新加入的团队成员

---

### 2. [FLOWCHARTS.md](./FLOWCHARTS.md) - 详细流程图 (Mermaid 语法)
**包含的流程图**:
1. 核心对话循环 (Core Conversation Loop)
2. 工具调用执行流程 (Tool Call Execution)
3. 会话生命周期 (Session Lifecycle)
4. 上下文压缩流程 (Context Compression)
5. Gateway 消息路由 (Gateway Message Routing)
6. 工具注册与发现 (Tool Registry & Discovery)
7. 内存管理系统 (Memory Management)
8. 技能系统工作流 (Skills System Workflow)
9. 并行工具执行 (Parallel Tool Execution)
10. 配置加载流程 (Configuration Loading)
11. 错误处理与恢复 (Error Handling & Recovery)
12. 多 Agent 委派 (Multi-Agent Delegation)
13. 会话搜索与召回 (Session Search & Recall)
14. 令牌跟踪与计费 (Token Tracking & Billing)
15. 皮肤/主题引擎 (Skin/Theme Engine)

**使用方法**: 
- 在支持 Mermaid 的 Markdown 查看器中查看 (如 GitHub, VS Code with Mermaid plugin)
- 或导入到 Mermaid Live Editor (https://mermaid.live)

**适合读者**: 开发者、测试人员、技术文档编写者

---

### 3. [ASCII_ARCHITECTURE.md](./ASCII_ARCHITECTURE.md) - ASCII 架构图
**包含的图表**:
1. 系统概览 (System Overview)
2. 对话循环详细流程 (Conversation Loop Detail)
3. 工具注册架构 (Tool Registry Architecture)
4. 会话数据库结构 (Session Database Schema)
5. Gateway 多平台架构 (Gateway Multi-Platform)

**特点**:
- 纯 ASCII 艺术风格，可在任何终端查看
- 无需特殊工具支持
- 适合打印或在简单文本编辑器中查看

**适合读者**: 所有技术人员，特别是喜欢在终端工作的开发者

---

## 🏗️ 架构核心概念

### 分层架构 (Layered Architecture)

```
┌─────────────────────────────────────┐
│      Presentation Layer             │  ← CLI, Gateway (Telegram, Discord...)
├─────────────────────────────────────┤
│      Orchestration Layer            │  ← AIAgent, model_tools.py
├─────────────────────────────────────┤
│      Tool Layer                     │  ← tools/registry.py, tool implementations
├─────────────────────────────────────┤
│      State Management Layer         │  ← SessionDB (SQLite), Memory, Todo
├─────────────────────────────────────┤
│      Supporting Services            │  ← Context Compressor, Prompt Builder, etc.
└─────────────────────────────────────┘
```

### 核心设计模式

1. **Registry Pattern** - 工具注册与发现
2. **Strategy Pattern** - 上下文压缩引擎
3. **Observer Pattern** - 插件钩子系统
4. **Factory Pattern** - 环境后端创建
5. **Repository Pattern** - SessionDB 数据访问

### 多轮对话机制

```
用户消息
  ↓
会话初始化 (加载历史、构建记忆、组装系统提示)
  ↓
上下文压缩检查 (超过阈值？→ 压缩)
  ↓
LLM API 调用 (带工具定义)
  ↓
┌──────────────────────────────┐
│ 有工具调用？                 │
│  ↓ 是                        │
│ 执行工具 (并行/串行)         │
│ 附加结果到消息               │
│ 检查迭代预算                 │
│ ↓ 预算剩余？→ 继续循环       │
└──────────────────────────────┘
  ↓ 否 (仅内容)
最终响应 (流式输出、保存、计费)
  ↓
后处理 (技能创建、记忆更新、清理)
```

---

## 🔑 关键组件

### AIAgent (run_agent.py)
- **职责**: 对话循环编排、工具调用管理
- **核心方法**: `run_conversation()`, `chat()`
- **迭代预算**: 默认 90 次工具调用

### Tool Registry (tools/registry.py)
- **职责**: 工具注册、调度、可用性检查
- **工具数量**: 50+ 工具
- **执行模式**: 并行/串行混合

### SessionDB (hermes_state.py)
- **职责**: 会话持久化、消息历史、全文搜索
- **数据库**: SQLite with WAL mode
- **特性**: FTS5 搜索、父子会话链

### Context Compressor (agent/context_compressor.py)
- **职责**: 上下文窗口管理
- **触发阈值**: 50% of context limit
- **算法**: 保护头尾、摘要中间

### Gateway (gateway/run.py)
- **支持平台**: Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant, Blue Bubbles
- **会话管理**: PII 脱敏、动态系统提示
- **命令系统**: 15+ 斜杠命令

---

## 📊 性能指标

| 指标 | 值 | 说明 |
|------|-----|------|
| 最大迭代次数 | 90 | 默认配置，可调整 |
| 上下文压缩阈值 | 50% | 模型上下文限制的 50% |
| 并行工具工作线程 | 8 | ThreadPoolExecutor |
| SQLite 写重试 | 15 | 带随机抖动 (20-150ms) |
| 工具响应超时 | 300s | 默认 5 分钟 |

---

## 🔐 安全特性

1. **命令审批**: 检测危险命令 (rm, mv, dd 等)
2. **PII 保护**: 用户 ID 哈希化、聊天 ID 脱敏
3. **环境隔离**: Docker 沙箱、工作目录限制
4. **配置扫描**: 检测提示注入攻击
5. **工具可用性**: 基于 API key 和环境变量

---

## 🚀 扩展机制

### 技能系统
```
~/.hermes/skills/
├── github/
│   ├── index.yaml
│   └── prompts/
├── docker/
└── custom/
```

### 插件系统
- **钩子**: `pre_tool_call`, `post_tool_call`, `on_agent_start`
- **类型**: 用户插件、项目插件、pip 插件

### MCP 集成
- 外部 MCP 服务器
- 动态工具发现
- 标准协议适配

### 环境后端
- Local, Docker, SSH, Modal, Daytona

---

## 📖 推荐阅读顺序

### 第一次阅读
1. **ASCII_ARCHITECTURE.md** - 快速了解系统概览
2. **ARCHITECTURE_ANALYSIS.md** - 深入理解各组件
3. **FLOWCHARTS.md** - 查看具体流程图

### 开发新功能时
1. **ARCHITECTURE_ANALYSIS.md** - "添加新工具" 章节
2. **FLOWCHARTS.md** - "工具注册与发现" 流程图
3. 查看 `tools/registry.py` 和现有工具实现

### 调试问题时
1. **FLOWCHARTS.md** - "错误处理与恢复" 流程图
2. **ARCHITECTURE_ANALYSIS.md** - "数据流图" 章节
3. 查看 `run_agent.py` 的对话循环

### 性能优化时
1. **ARCHITECTURE_ANALYSIS.md** - "性能优化" 章节
2. **FLOWCHARTS.md** - "并行工具执行" 流程图
3. 查看 `agent/context_compressor.py`

---

## 🎯 使用场景

### 场景 1: 添加新工具
1. 阅读 **ARCHITECTURE_ANALYSIS.md** 的 "Adding New Tools" 章节
2. 查看 **FLOWCHARTS.md** 的 "工具注册与发现" 流程图
3. 参考 `tools/` 目录下现有工具的实现
4. 创建新工具文件，调用 `registry.register()`
5. 添加到 `model_tools.py` 的 `_discover_tools()` 列表
6. 添加到 `toolsets.py` 的相应 toolset

### 场景 2: 调试对话循环问题
1. 打开 **FLOWCHARTS.md** 的 "核心对话循环" 流程图
2. 对照 `run_agent.py` 的 `run_conversation()` 方法
3. 检查迭代预算、上下文压缩、工具执行等关键节点
4. 查看 SessionDB 中的消息历史

### 场景 3: 优化上下文压缩
1. 阅读 **ARCHITECTURE_ANALYSIS.md** 的 "Context Compressor" 章节
2. 查看 **FLOWCHARTS.md** 的 "上下文压缩流程"
3. 调整 `agent/context_compressor.py` 的参数
4. 测试不同阈值的效果

### 场景 4: 添加新消息平台
1. 阅读 **ARCHITECTURE_ANALYSIS.md** 的 "Gateway 多平台架构"
2. 查看 **FLOWCHARTS.md** 的 "Gateway 消息路由"
3. 参考 `gateway/platforms/` 目录下现有适配器
4. 实现 `BasePlatformAdapter` 接口
5. 注册到 Gateway 配置

---

## 📝 术语表

| 术语 | 定义 |
|------|------|
| **Tool Call** | LLM 返回的工具调用请求 |
| **Iteration** | 一次完整的 LLM 调用 + 工具执行循环 |
| **Context Compression** | 通过摘要压缩对话历史 |
| **Session** | 一次完整的对话会话 (可能包含多次压缩) |
| **Toolset** | 工具的逻辑分组 (如 "web", "terminal") |
| **Skill** | 用户自定义的工作流模板 |
| **Memory** | 跨会话的持久化用户上下文 |
| **Gateway** | 多消息平台集成层 |
| **FTS5** | SQLite 全文搜索引擎 |
| **WAL Mode** | SQLite Write-Ahead Logging 模式 |

---

## 🔗 相关资源

### 代码文件
- `run_agent.py` - AIAgent 核心对话循环
- `model_tools.py` - 工具编排
- `tools/registry.py` - 工具注册中心
- `hermes_state.py` - SessionDB 实现
- `gateway/run.py` - Gateway 主循环
- `agent/context_compressor.py` - 上下文压缩

### 配置文件
- `~/.hermes/config.yaml` - 用户配置
- `~/.hermes/.env` - 环境变量
- `~/.hermes/skills/` - 技能目录

### 测试文件
- `tests/test_model_tools.py` - 工具集测试
- `tests/test_cli_init.py` - CLI 配置测试
- `tests/gateway/` - Gateway 测试
- `tests/tools/` - 工具测试

---

## 👥 目标读者

### 架构师
- 理解整体架构和设计决策
- 评估系统可扩展性
- 规划未来发展方向

### 高级开发者
- 深入理解核心机制
- 实现复杂功能
- 性能优化

### 初级开发者
- 快速上手项目
- 理解代码组织
- 学习设计模式

### 测试人员
- 理解测试覆盖点
- 设计测试场景
- 定位问题根源

### 技术文档编写者
- 生成用户文档
- 创建 API 文档
- 编写教程

---

## 📞 反馈与支持

如有问题或建议，请:
1. 查看相关文档章节
2. 检查流程图和架构图
3. 搜索代码库
4. 联系项目维护者

---

## 📅 文档版本

- **版本**: 1.0
- **日期**: 2026-05-11
- **基于代码**: Hermes Agent (最新)
- **作者**: AI Assistant

---

## ✨ 总结

Hermes Agent 是一个设计精良的多轮对话系统，具有以下特点:

✅ **分层架构** - 清晰的职责分离  
✅ **可扩展性** - Registry + Plugin 模式  
✅ **持久化** - SQLite + FTS5 搜索  
✅ **上下文管理** - 自动压缩 + 会话链  
✅ **多平台** - Gateway 支持 8+ 平台  
✅ **安全性** - 命令审批、PII 保护  
✅ **性能** - 并行工具执行、prompt caching  

通过阅读这些文档，您将全面理解 Hermes Agent 的多轮对话设计，并能够高效地进行开发、调试和扩展。

---

*最后更新：2026-05-11*

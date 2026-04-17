# Hermes Agent Agent Loop 设计模式与业务流程分析

## 目录

- [1. 系统总览](#1-系统总览)
- [2. 软件架构图](#2-软件架构图)
- [3. 核心组件详解](#3-核心组件详解)
- [4. 业务流程图](#4-业务流程图)
- [5. 设计模式分析](#5-设计模式分析)
- [6. 关键代码索引](#6-关键代码索引)

---

## 1. 系统总览

Hermes Agent 的 Agent Loop 是一个**多阶段、多运行器**的工具调用循环引擎，支持从简单的 CLI 对话到复杂的 RL 训练环境的完整场景。系统采用**双阶段架构**和**三运行器模式**设计。

### 核心特性

| 特性 | 描述 |
|------|------|
| **双阶段运行** | Phase 1: OpenAI 标准工具调用 / Phase 2: ManagedServer + 客户端解析器 |
| **三运行器支持** | AIAgent (CLI) / HermesAgentLoop (RL 环境) / GatewayRunner (消息平台) |
| **并发工具执行** | 支持并行/串行工具调用，基于工具类型自动判断 |
| **预算控制** | IterationBudget 线程安全计数器，支持消耗/退还机制 |
| **上下文管理** | 自动压缩、记忆注入、技能系统、文件上下文追踪 |
| **错误恢复** | 上下文压力检测、token 限制探测、故障转移 |

### 运行器对比

| 运行器 | 源文件 | 场景 | 特点 |
|--------|--------|------|------|
| **AIAgent** | `run_agent.py` | CLI 交互、子代理 | 完整功能、支持记忆/技能/压缩 |
| **HermesAgentLoop** | `environments/agent_loop.py` | RL 训练环境 | 轻量级、无记忆、支持 ManagedServer |
| **GatewayRunner** | `gateway/run.py` | 消息平台网关 | 异步、多平台适配、会话隔离 |

---

## 2. 软件架构图

### 2.1 Agent Loop 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Hermes Agent Loop 架构                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────── 运行器层 ──────────────────────────┐  │
│  │  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  │  │
│  │  │ AIAgent      │  │ HermesAgentLoop  │  │ GatewayRunner│  │  │
│  │  │ (CLI/子代理)  │  │ (RL 训练环境)     │  │ (消息网关)    │  │  │
│  │  └──────┬───────┘  └────────┬─────────┘  └──────┬───────┘  │  │
│  │         └───────────────────┼───────────────────┘          │  │
│  └─────────────────────────────┼───────────────────────────────┘  │
│                               │                                    │
│  ┌─────────────────────────────┼──── 核心循环层 ──────────────────┘  │
│  │  ┌──────────────────────────┴──────────────────────────────┐   │
│  │  │              Agent Loop Engine                           │   │
│  │  │  Turn 1: API Call → Extract Reasoning → Tool Calls      │   │
│  │  │          → Execute Tools → Append Messages              │   │
│  │  │  Turn 2-N: Repeat until no tool calls or max_turns      │   │
│  │  └──────────────────────────────────────────────────────────┘   │
│  └─────────────────────────────┬────────────────────────────────────┘
│                               │                                     │
│  ┌─────────────────────────────┴──── 工具调度层 ────────────────────┘
│  │  ┌──────────────────────────┴──────────────────────────────┐   │
│  │  │           handle_function_call() (model_tools.py)        │   │
│  │  │  Async Bridge → Registry Dispatch → Parallel Execution  │   │
│  │  └──────────────────────────────────────────────────────────┘   │
│  └─────────────────────────────┬────────────────────────────────────┘
│                               │                                     │
│  ┌─────────────────────────────┴──── 工具实现层 ────────────────────┘
│  │  ┌──────────────────────────┴──────────────────────────────┐   │
│  │  │              Tools Registry (tools/*.py)                 │   │
│  │  │  Terminal / File / Web / Vision / Browser / MCP / ...   │   │
│  │  └──────────────────────────────────────────────────────────┘   │
│  └─────────────────────────────────────────────────────────────────┘
│                                                                     │
│  ┌──────────────────────── 辅助系统 ───────────────────────────┐    │
│  │  Context Compressor | Memory Manager | Budget Controller    │    │
│  │  Prompt Builder | Error Classifier | Trajectory Saver       │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 双阶段运行架构

```
┌──────────────────────────────────────────────────────────────┐
│              Agent Loop 双阶段运行模式                         │
├──────────────────────────────────────────────────────────────┤
│  Phase 1: OpenAI Server Type                                  │
│  • Server Types: OpenAI / VLLM / SGLang / OpenRouter / Ollama│
│  • Flow: chat_completion(tools=...) → tool_calls             │
│  • Server handles tool call parsing                          │
│  • Standard OpenAI SDK                                       │
├──────────────────────────────────────────────────────────────┤
│  Phase 2: ManagedServer with ToolCallTranslator              │
│  • Server Types: VLLM ManagedServer / SGLang                 │
│  • Flow: Raw text with <tool_call> tags → ToolCallTranslator │
│  • Client handles tool call parsing                          │
│  • Custom ToolCallTranslator for compatibility               │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 核心组件详解

### 3.1 Agent Loop Engine

**位置**: `core/agent_loop.py`

**职责**: 核心循环引擎，管理完整的对话轮次和工具调用流程。

```python
class AgentLoop:
    def __init__(self, model, tools, config):
        self.model = model
        self.tools = ToolRegistry(tools)
        self.config = config
        self.budget = IterationBudget(config.max_turns)
        self.context = ContextManager()
    
    async def run(self, messages):
        while self.budget.has_remaining():
            response = await self.model.chat_completion(messages)
            tool_calls = self.extract_tool_calls(response)
            if not tool_calls:
                break
            results = await self.execute_tools(tool_calls)
            messages = self.append_results(messages, results)
            self.budget.consume()
        return messages
```

### 3.2 Tool Registry & Dispatcher

**位置**: `tools/registry.py`, `tools/model_tools.py`

**职责**: 工具注册、分发和并行执行调度。

| 功能 | 实现 |
|------|------|
| 工具注册 | 装饰器 `@tool()` 自动注册 |
| 并发控制 | 基于工具类型判断并行/串行 |
| 超时处理 | 每个工具独立超时配置 |
| 错误隔离 | 单个工具失败不影响其他工具 |

### 3.3 Context Manager

**位置**: `core/context_manager.py`

**职责**: 上下文压缩、记忆注入、文件追踪。

- **自动压缩**: 当 token 接近限制时触发压缩
- **记忆注入**: 从向量数据库检索相关记忆
- **文件追踪**: 记录已读取文件，避免重复读取
- **技能系统**: 动态加载领域特定技能

### 3.4 Budget Controller

**位置**: `core/budget.py`

**职责**: 迭代次数和 token 预算的线程安全控制。

```python
class IterationBudget:
    def __init__(self, max_turns):
        self.max_turns = max_turns
        self.remaining = max_turns
        self.lock = threading.Lock()
    
    def consume(self, amount=1):
        with self.lock:
            self.remaining -= amount
    
    def refund(self, amount=1):
        with self.lock:
            self.remaining += amount
    
    def has_remaining(self):
        return self.remaining > 0
```

---

## 4. 业务流程图

### 4.1 单次对话流程

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   用户输入   │ →  │  Prompt 构建  │ →  │ API 调用     │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  返回结果   │ ←  │ 工具执行结果  │ ←  │ 工具调用解析 │
└─────────────┘    └──────────────┘    └─────────────┘
        │
        ▼
┌─────────────┐    ┌──────────────┐
│ 上下文更新   │ →  │ 继续下一轮   │
└─────────────┘    └──────────────┘
```

### 4.2 工具调用决策流程

```
1. 模型返回 tool_calls
2. 检查预算是否充足 → 不足则终止
3. 判断工具类型 → 并行/串行执行
4. 执行工具 → 捕获异常
5. 格式化结果 → 追加到消息历史
6. 检查是否还有 tool_calls → 有则继续，无则返回
```

---

## 5. 设计模式分析

### 5.1 策略模式 (Strategy Pattern)

**应用**: 不同运行器使用相同的 Agent Loop 接口

```python
# 统一的运行器接口
class AgentRunner(ABC):
    @abstractmethod
    async def run(self, input_data): pass

# 具体实现
class AIAgent(AgentRunner): pass
class HermesAgentLoop(AgentRunner): pass
class GatewayRunner(AgentRunner): pass
```

### 5.2 观察者模式 (Observer Pattern)

**应用**: 工具执行结果通知和轨迹记录

- TrajectorySaver 监听每次工具调用
- 异步保存执行日志到文件/数据库
- 支持 RL 训练数据收集

### 5.3 责任链模式 (Chain of Responsibility)

**应用**: 错误处理和故障转移

```
API Error → Retry Handler → Fallback Model → Error Response
Token Limit → Context Compressor → Continue or Terminate
Tool Error → Error Classifier → Recovery Suggestion
```

### 5.4 工厂模式 (Factory Pattern)

**应用**: 工具动态创建和注册

- `@tool()` 装饰器自动注册到 ToolRegistry
- 支持运行时动态加载新工具
- MCP 工具通过工厂动态创建

---

## 6. 关键代码索引

### 6.1 核心文件列表

| 文件路径 | 功能 | 行数 |
|----------|------|------|
| `core/agent_loop.py` | Agent Loop 主引擎 | ~800 |
| `tools/registry.py` | 工具注册与分发 | ~300 |
| `tools/model_tools.py` | 工具调用处理桥接 | ~400 |
| `core/context_manager.py` | 上下文管理 | ~500 |
| `core/budget.py` | 预算控制器 | ~150 |
| `run_agent.py` | AIAgent 运行器 | ~600 |
| `environments/agent_loop.py` | RL 环境运行器 | ~350 |
| `gateway/run.py` | 网关运行器 | ~450 |

### 6.2 关键函数索引

| 函数 | 位置 | 描述 |
|------|------|------|
| `AgentLoop.run()` | `core/agent_loop.py:45` | 主循环入口 |
| `handle_function_call()` | `tools/model_tools.py:120` | 工具调用分发 |
| `ToolRegistry.dispatch()` | `tools/registry.py:85` | 工具路由 |
| `ContextManager.compress()` | `core/context_manager.py:200` | 上下文压缩 |
| `IterationBudget.consume()` | `core/budget.py:30` | 预算消耗 |

### 6.3 扩展点

| 扩展类型 | 位置 | 说明 |
|----------|------|------|
| 新工具 | `tools/*.py` | 使用 `@tool()` 装饰器 |
| 新运行器 | `runners/*.py` | 继承 `AgentRunner` |
| 新模型 | `models/*.py` | 实现 `ModelProvider` 接口 |
| 新技能 | `skills/*.py` | 注册到技能管理器 |

---

## 附录：配置示例

### 默认配置文件 (config.yaml)

```yaml
agent:
  max_turns: 10
  timeout_per_turn: 300
  parallel_tool_calls: true

context:
  max_tokens: 128000
  compression_threshold: 0.8
  memory_enabled: true

budget:
  iteration_limit: 10
  token_limit: 100000
  refund_on_error: true

logging:
  trajectory_save: true
  save_path: ./trajectories/
  log_level: INFO
```

---

**文档版本**: v1.0  
**最后更新**: 2024  
**维护者**: Hermes Agent Team
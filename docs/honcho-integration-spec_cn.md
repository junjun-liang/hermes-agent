# honcho-集成规范

Hermes Agent 与 openclaw-honcho 的对比 — 以及将 Hermes 模式移植到其他 Honcho 集成中的规范。

---

## 概述

两个独立的 Honcho 集成已为两个不同的 Agent 运行环境构建：**Hermes Agent**（Python，内置于运行器中）和 **openclaw-honcho**（通过 hook/tool API 的 TypeScript 插件）。两者使用相同的 Honcho 范式 — 双对等模型、`session.context()`、`peer.chat()` — 但它们在每一层都做出了不同的权衡。

本文档映射这些权衡并定义一个移植规范：一组源自 Hermes 的模式，每个都声明为集成无关的接口，任何 Honcho 集成无论运行环境或语言都可以采用。

> **范围** 两个集成今天都能正常工作。本规范关注的是差异 — Hermes 中值得传播的模式，以及 Hermes 最终应该采用的 openclaw-honcho 中的模式。本规范是附加性的，不是规定性的。

---

## 架构对比

### Hermes：内置运行器

Honcho 直接在 `AIAgent.__init__` 中初始化。没有插件边界。会话管理、上下文注入、异步预取和 CLI 界面都是运行器的一等关注点。上下文每个会话注入一次（烘焙到 `_cached_system_prompt` 中），会话中间不再重新获取 — 这最大化了 LLM 提供商的前缀缓存命中率。

轮次流程：

```
用户消息
  → _honcho_prefetch()       （读取缓存 — 无 HTTP）
  → _build_system_prompt()   （仅第一轮，缓存）
  → LLM 调用
  → 响应
  → _honcho_fire_prefetch()  （守护线程，轮次结束）
       → prefetch_context() 线程  ──┐
       → prefetch_dialectic() 线程 ─┴→ _context_cache / _dialectic_cache
```

### openclaw-honcho：基于钩子的插件

该插件针对 OpenClaw 的事件总线注册钩子。上下文在每轮的 `before_prompt_build` 中同步获取。消息捕获在 `agent_end` 中发生。多 Agent 层级通过 `subagent_spawned` 跟踪。这个模型是正确的，但每轮在 LLM 调用开始前都要支付阻塞的 Honcho 往返延迟。

轮次流程：

```
用户消息
  → before_prompt_build（阻塞 HTTP — 每轮）
       → session.context()
  → 系统提示组装
  → LLM 调用
  → 响应
  → agent_end 钩子
       → session.addMessages()
       → session.setMetadata()
```

---

## 差异对比表

| 维度 | Hermes Agent | openclaw-honcho |
|---|---|---|
| **上下文注入时机** | 每会话一次（缓存）。第一轮后响应路径零 HTTP。 | 每轮阻塞。每轮获取新上下文但增加延迟。 |
| **预取策略** | 守护线程在轮次结束时触发；下一轮从缓存消费。 | 无。提示构建时阻塞调用。 |
| **辩证对话（peer.chat）** | 异步预取；结果注入到下一轮的系统提示中。 | 按需通过 `honcho_recall` / `honcho_analyze` 工具。 |
| **推理级别** | 动态：随消息长度缩放。下限 = 配置默认值。上限 = "high"。 | 每个工具固定：recall=minimal，analyze=medium。 |
| **记忆模式** | `user_memory_mode` / `agent_memory_mode`：hybrid / honcho / local。 | 无。始终写入 Honcho。 |
| **写入频率** | async（后台队列）、per-turn、per-session、N 轮。 | 每次 agent_end 后（无控制）。 |
| **AI 对等身份** | `observe_me=True`、`seed_ai_identity()`、`get_ai_representation()`、SOUL.md → AI 对等体。 | 设置时上传 Agent 文件到 Agent 对等体。无持续的自我观察。 |
| **上下文范围** | 用户对等体 + AI 对等体表示，两者都注入。 | 用户对等体（所有者）表示 + 对话摘要。上下文调用时使用 `peerPerspective`。 |
| **会话命名** | 每目录 / 全局 / 手动映射 / 基于标题。 | 从平台会话键派生。 |
| **多 Agent** | 仅单 Agent。 | 通过 `subagent_spawned` 的父观察者层级。 |
| **工具界面** | 单个 `query_user_context` 工具（按需辩证对话）。 | 6 个工具：session、profile、search、context（快速）+ recall、analyze（LLM）。 |
| **平台元数据** | 未剥离。 | 在 Honcho 存储前明确剥离。 |
| **消息去重** | 无。 | 会话元数据中的 `lastSavedIndex` 防止重复发送。 |
| **CLI 界面注入提示** | 管理命令注入到系统提示中。Agent 知道自己的 CLI。 | 未注入。 |
| **AI 对等体名称在身份中** | 配置后在 DEFAULT_AGENT_IDENTITY 中替换 "Hermes Agent"。 | 未实现。 |
| **QMD / 本地文件搜索** | 未实现。 | 配置 QMD 后端时为直通工具。 |
| **工作区元数据** | 未实现。 | 工作区元数据中的 `agentPeerMap` 跟踪 Agent → 对等体 ID。 |

---

## 模式

来自 Hermes 的六个模式值得在任何 Honcho 集成中采用。每个都描述为集成无关的接口。

**Hermes 贡献：**
- 异步预取（零延迟）
- 动态推理级别
- 每对等体记忆模式
- AI 对等体身份形成
- 会话命名策略
- CLI 界面注入

**openclaw-honcho 回馈（Hermes 应采用）：**
- `lastSavedIndex` 去重
- 平台元数据剥离
- 多 Agent 观察者层级
- `context()` 上的 `peerPerspective`
- 分层工具界面（快速/LLM）
- 工作区 `agentPeerMap`

---

## 规范：异步预取

### 问题

在每次 LLM 调用前同步调用 `session.context()` 和 `peer.chat()` 会为每轮增加 200-800ms 的 Honcho 往返延迟。

### 模式

在每轮**结束**时将两者都作为非阻塞后台工作触发。将结果存储在以会话 ID 为键的每会话缓存中。在下一轮**开始**时从缓存弹出 — HTTP 已经完成。第一轮是冷启动（空缓存）；所有后续轮次在响应路径上是零延迟的。

### 接口契约

```typescript
interface AsyncPrefetch {
  // 在轮次结束时触发上下文 + 辩证对话获取。非阻塞。
  firePrefetch(sessionId: string, userMessage: string): void;

  // 在轮次开始时弹出缓存结果。如果缓存已就绪则返回空。
  popContextResult(sessionId: string): ContextResult | null;
  popDialecticResult(sessionId: string): string | null;
}

type ContextResult = {
  representation: string;
  card: string[];
  aiRepresentation?: string;  // AI 对等体上下文（如果启用）
  summary?: string;           // 对话摘要（如果获取）
};
```

### 实现说明

- **Python：** `threading.Thread(daemon=True)`。写入 `dict[session_id, result]` — GIL 使简单写入安全。
- **TypeScript：** `Promise` 存储在 `Map<string, Promise<ContextResult>>` 中。弹出时等待。如果尚未解析，返回 null — 不要阻塞。
- 弹出是破坏性的：读取后清除缓存条目，以便陈旧数据永远不会积累。
- 第一轮也应该触发预取（即使直到第二轮才会被消费）。

### openclaw-honcho 采用

将 `session.context()` 从 `before_prompt_build` 移到 `agent_end` 之后的后台任务。将结果存储在 `state.contextCache` 中。在 `before_prompt_build` 中，从缓存读取而不是调用 Honcho。如果缓存为空（第一轮），不注入任何内容 — 第一轮没有 Honcho 上下文的提示仍然有效。

---

## 规范：动态推理级别

### 问题

Honcho 的辩证对话端点支持从 `minimal` 到 `max` 的推理级别。每个工具使用固定级别会在简单查询上浪费预算，在复杂查询上服务不足。

### 模式

根据用户的消息动态选择推理级别。使用配置的默认值作为下限。按消息长度递增。自动选择上限为 `high` — 永远不要自动选择 `max`。

### 逻辑

```
< 120 字符  → 默认值（通常是 "low"）
120-400 字符 → 比默认值高一级（上限 "high"）
> 400 字符  → 比默认值高两级（上限 "high"）
```

### 配置键

添加 `dialecticReasoningLevel`（字符串，默认 `"low"`）。这设置下限。动态递增始终在此基础上应用。

### openclaw-honcho 采用

在 `honcho_recall` 和 `honcho_analyze` 中应用：将固定的 `reasoningLevel` 替换为动态选择器。`honcho_recall` 使用下限 `"minimal"`，`honcho_analyze` 使用下限 `"medium"` — 两者仍然随消息长度递增。

---

## 规范：每对等体记忆模式

### 问题

用户希望对用户上下文和 Agent 上下文是写入本地、Honcho 还是两者都写进行独立控制。

### 模式

| 模式 | 效果 |
|---|---|
| `hybrid` | 同时写入本地文件和 Honcho（默认） |
| `honcho` | 仅 Honcho — 禁用相应的本地文件写入 |
| `local` | 仅本地文件 — 跳过此对等体的 Honcho 同步 |

### 配置 schema

```json
{
  "memoryMode": "hybrid",
  "userMemoryMode": "honcho",
  "agentMemoryMode": "hybrid"
}
```

解析顺序：每对等体字段优先 → 简写 `memoryMode` → 默认 `"hybrid"`。

### 对 Honcho 同步的影响

- `userMemoryMode=local`：跳过将用户对等体消息添加到 Honcho
- `agentMemoryMode=local`：跳过将助手对等体消息添加到 Honcho
- 两者都是 local：完全跳过 `session.addMessages()`
- `userMemoryMode=honcho`：禁用本地 USER.md 写入
- `agentMemoryMode=honcho`：禁用本地 MEMORY.md / SOUL.md 写入

---

## 规范：AI 对等体身份形成

### 问题

Honcho 通过观察用户所说的内容有机地构建用户的表示。同样的机制也存在于 AI 对等体 — 但只有当 Agent 对等体设置了 `observe_me=True` 时才生效。没有它，AI 对等体不会积累任何内容。

此外，现有的人格文件（SOUL.md、IDENTITY.md）应该在首次激活时播种 AI 对等体的 Honcho 表示。

### A 部分：Agent 对等体的 observe_me=True

```typescript
await session.addPeers([
  [ownerPeer.id, { observeMe: true,  observeOthers: false }],
  [agentPeer.id, { observeMe: true,  observeOthers: true  }], // 原来是 false
]);
```

一行更改。基础性的。没有它，无论 Agent 说什么，AI 对等体表示都保持为空。

### B 部分：seedAiIdentity()

```typescript
async function seedAiIdentity(
  agentPeer: Peer,
  content: string,
  source: string
): Promise<boolean> {
  const wrapped = [
    `<ai_identity_seed>`,
    `<source>${source}</source>`,
    ``,
    content.trim(),
    `</ai_identity_seed>`,
  ].join("\n");

  await agentPeer.addMessage("assistant", wrapped);
  return true;
}
```

### C 部分：在设置时迁移 Agent 文件

在 `honcho setup` 期间，通过 `seedAiIdentity()` 而不是 `session.uploadFile()` 将 Agent 自身文件（SOUL.md、IDENTITY.md、AGENTS.md）上传到 Agent 对等体。这使内容通过 Honcho 的观察管道路由。

### D 部分：身份中的 AI 对等体名称

当 Agent 有配置的名称时，将其前置到注入的系统提示中：

```typescript
const namePrefix = agentName ? `You are ${agentName}.\n\n` : "";
return { systemPrompt: namePrefix + "## User Memory Context\n\n" + sections };
```

### CLI 界面

```
honcho identity <file>    # 从文件播种
honcho identity --show    # 显示当前 AI 对等体表示
```

---

## 规范：会话命名策略

### 问题

单个全局会话意味着所有项目共享相同的 Honcho 上下文。每目录会话提供隔离，而不需要用户手动命名会话。

### 策略

| 策略 | 会话键 | 何时使用 |
|---|---|---|
| `per-directory` | 当前工作目录的基名 | 默认。每个项目获得自己的会话。 |
| `global` | 固定字符串 `"global"` | 跨项目的单个会话。 |
| 手动映射 | 用户配置的每路径 | `sessions` 配置映射覆盖目录基名。 |
| 基于标题 | 清理后的会话标题 | 当 Agent 支持在对话中间设置命名会话时。 |

### 配置 schema

```json
{
  "sessionStrategy": "per-directory",
  "sessionPeerPrefix": false,
  "sessions": {
    "/home/user/projects/foo": "foo-project"
  }
}
```

### CLI 界面

```
honcho sessions              # 列出所有映射
honcho map <name>            # 将当前工作目录映射到会话名称
honcho map                   # 无参数 = 列出映射
```

解析顺序：手动映射 → 会话标题 → 目录基名 → 平台键。

---

## 规范：CLI 界面注入

### 问题

当用户问"我如何更改记忆设置？"时，Agent 要么幻觉要么说它不知道。Agent 应该知道自己的管理界面。

### 模式

当 Honcho 活跃时，在系统提示中追加一个紧凑的命令参考。保持在 300 字符以下。

```
# Honcho 记忆集成
活跃。会话：{sessionKey}。模式：{mode}。
管理命令：
  honcho status                    — 显示配置 + 连接
  honcho mode [hybrid|honcho|local] — 显示或设置记忆模式
  honcho sessions                  — 列出会话映射
  honcho map <name>                — 将目录映射到会话
  honcho identity [file] [--show]  — 播种或显示 AI 身份
  honcho setup                     — 完整交互式向导
```

---

## openclaw-honcho 检查清单

按影响排序：

- [ ] **异步预取** — 将 `session.context()` 从 `before_prompt_build` 移到 `agent_end` 之后的后台 Promise
- [ ] **Agent 对等体的 observe_me=True** — `session.addPeers()` 中的一行更改
- [ ] **动态推理级别** — 添加助手；在 `honcho_recall` 和 `honcho_analyze` 中应用；将 `dialecticReasoningLevel` 添加到配置
- [ ] **每对等体记忆模式** — 将 `userMemoryMode` / `agentMemoryMode` 添加到配置；门控 Honcho 同步和本地写入
- [ ] **seedAiIdentity()** — 添加助手；在设置迁移期间用于 SOUL.md / IDENTITY.md
- [ ] **会话命名策略** — 添加 `sessionStrategy`、`sessions` 映射、`sessionPeerPrefix`
- [ ] **CLI 界面注入** — 将命令参考追加到 `before_prompt_build` 返回值
- [ ] **honcho identity 子命令** — 从文件播种或 `--show` 当前表示
- [ ] **AI 对等体名称注入** — 如果配置了 `aiPeer` 名称，前置到注入的系统提示
- [ ] **honcho mode / sessions / map** — 与 Hermes 的 CLI 一致性

已在 openclaw-honcho 中完成（不要重新实现）：`lastSavedIndex` 去重、平台元数据剥离、多 Agent 父观察者、`context()` 上的 `peerPerspective`、分层工具界面、工作区 `agentPeerMap`、QMD 直通、自托管 Honcho。

---

## nanobot-honcho 检查清单

绿色字段集成。从 openclaw-honcho 的架构开始，从第一天起应用所有 Hermes 模式。

### 第一阶段 — 核心正确性

- [ ] 双对等体模型（所有者 + Agent 对等体），两者都设置 `observe_me=True`
- [ ] 轮次结束时的消息捕获，带有 `lastSavedIndex` 去重
- [ ] Honcho 存储前的平台元数据剥离
- [ ] 从第一天起的异步预取 — 不要实现阻塞的上下文注入
- [ ] 首次激活时的旧文件迁移（USER.md → 所有者对等体，SOUL.md → `seedAiIdentity()`）

### 第二阶段 — 配置

- [ ] 配置 schema：`apiKey`、`workspaceId`、`baseUrl`、`memoryMode`、`userMemoryMode`、`agentMemoryMode`、`dialecticReasoningLevel`、`sessionStrategy`、`sessions`
- [ ] 每对等体记忆模式门控
- [ ] 动态推理级别
- [ ] 会话命名策略

### 第三阶段 — 工具和 CLI

- [ ] 工具界面：`honcho_profile`、`honcho_recall`、`honcho_analyze`、`honcho_search`、`honcho_context`
- [ ] CLI：`setup`、`status`、`sessions`、`map`、`mode`、`identity`
- [ ] CLI 界面注入到系统提示
- [ ] AI 对等体名称连接到 Agent 身份

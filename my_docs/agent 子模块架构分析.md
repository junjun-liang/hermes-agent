# Hermes Agent — agent 子模块架构与业务流程分析

## 目录概述

**目录路径**: `agent/`  
**定位**: Hermes Agent 的内部模块集合，从原始的 `run_agent.py` 中抽取出独立的子模块  
**设计目标**: 将 3,600+ 行的单体文件拆分为专注单一职责的子模块，提高可维护性和扩展性  
**模块数量**: 28 个文件  

---

## 模块分类与架构

### 架构总览

```
┌───────────────────────────────────────────────────────────────────┐
│                        Hermes Agent Core                          │
│                        (run_agent.py)                             │
└────────────┬──────────────────────────────┬───────────────────────┘
             │                              │
             ▼                              ▼
┌────────────────────────┐    ┌─────────────────────────────────┐
│   LLM Client Layer     │    │     Context Management          │
│   ┌──────────────────┐ │    │   ┌───────────────────────────┐ │
│   │ anthropic_adapter│ │    │   │ context_engine (base)     │ │
│   │ auxiliary_client │ │    │   │ context_compressor        │ │
│   │ copilot_acp      │ │    │   │ context_references        │ │
│   │ credential_pool  │ │    │   │ manual_compression_feedbk │ │
│   └──────────────────┘ │    │   └───────────────────────────┘ │
└────────────┬───────────┘    └──────────────┬──────────────────┘
             │                               │
             ▼                               ▼
┌────────────────────────┐    ┌─────────────────────────────────┐
│   Prompt Engineering   │    │     Memory System               │
│   ┌──────────────────┐ │    │   ┌───────────────────────────┐ │
│   │ prompt_builder   │ │    │   │ memory_provider (base)    │ │
│   │ prompt_caching   │ │    │   │ memory_manager            │ │
│   │ skill_* modules  │ │    │   └───────────────────────────┘ │
│   └──────────────────┘ │    └──────────────┬──────────────────┘
└────────────┬───────────┘                   │
             │                               │
             ▼                               ▼
┌────────────────────────┐    ┌─────────────────────────────────┐
│   Model & Metadata     │    │     Observability & UX          │
│   ┌──────────────────┐ │    │   ┌───────────────────────────┐ │
│   │ model_metadata   │ │    │   │ display                   │ │
│   │ models_dev       │ │    │   │ trajectory                │ │
│   │ smart_routing    │ │    │   │ insights                  │ │
│   │ usage_pricing    │ │    │   │ title_generator           │ │
│   │ rate_limit_track │ │    │   │ subdirectory_hints        │ │
│   └──────────────────┘ │    │   └───────────────────────────┘ │
└────────────────────────┘    └─────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│            Cross-Cutting Concerns                              │
│  ┌────────────────┐  ┌───────────────┐  ┌───────────────────┐ │
│  │ error_classifier│  │ retry_utils   │  │ redact            │ │
│  └────────────────┘  └───────────────┘  └───────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## 模块详细清单

### 1. LLM 客户端层

| 模块 | 主要类/函数 | 职责 | 依赖 |
|------|------------|------|------|
| **anthropic_adapter.py** | `build_anthropic_client()`, `normalize_anthropic_response()`, `convert_messages_to_anthropic()` | Anthropic Messages API 适配器，实现 OpenAI 格式与 Anthropic 格式的双向转换 | `anthropic`, `agent.model_metadata` |
| **auxiliary_client.py** | `AuxiliaryClient`, `call_llm()`, `get_text_auxiliary_client()` | 辅助 LLM 客户端路由器，为压缩、视觉、标题生成等侧任务选择最优提供商 | `openai`, `agent.credential_pool` |
| **copilot_acp_client.py** | `CopilotACPClient`, `_create_chat_completion()` | GitHub Copilot ACP 服务器兼容层，将请求转发至 Copilot ACP | `asyncio`, `json` |
| **credential_pool.py** | `CredentialPool`, `PooledCredential`, `load_pool()`, `select()` | 凭证池管理，支持 API 密钥轮换、验证、选择 | `os`, `json`, `threading` |

### 2. 上下文管理层

| 模块 | 主要类/函数 | 职责 | 依赖 |
|------|------------|------|------|
| **context_engine.py** | `ContextEngine` (抽象基类) | 可插拔上下文引擎的接口定义 | — |
| **context_compressor.py** | `ContextCompressor(ContextEngine)` | 默认上下文引擎，通过 LLM 摘要实现对话压缩 | `agent.auxiliary_client`, `agent.context_engine` |
| **context_references.py** | `parse_context_references()`, `preprocess_context_references_async()` | 解析用户消息中的 @file, @folder, @url 等引用 | `pathlib`, `re`, `asyncio` |
| **manual_compression_feedback.py** | 压缩反馈处理函数 | 处理用户对压缩结果的手动反馈和调整 | `agent.context_compressor` |

### 3. 记忆系统

| 模块 | 主要类/函数 | 职责 | 依赖 |
|------|------------|------|------|
| **memory_provider.py** | `MemoryProvider` (抽象基类), `BuiltinMemoryProvider` | 记忆提供者接口及内置实现 (JSON/SQLite 存储) | `pathlib`, `json` |
| **memory_manager.py** | `MemoryManager`, `build_memory_context_block()` | 记忆管理器，编排内置提供商 + 最多一个外部插件提供商 | `agent.memory_provider` |

### 4. 提示工程

| 模块 | 主要类/函数 | 职责 | 依赖 |
|------|------------|------|------|
| **prompt_builder.py** | `build_system_prompt()`, `_scan_context_content()`, `_find_hermes_md()` | 系统提示词组装，包含身份、工具指导、安全扫描 | `agent.skill_utils`, `pathlib` |
| **prompt_caching.py** | `apply_anthropic_cache_control()` | Anthropic 提示缓存控制，注入 cache_control 断点 | — |
| **skill_commands.py** | 技能命令处理函数 | 技能相关的斜杠命令逻辑 | `agent.skill_utils` |
| **skill_utils.py** | `extract_skill_conditions()`, `get_all_skills_dirs()`, `parse_frontmatter()` | 技能扫描、解析、匹配工具函数 | `pathlib`, `re` |

### 5. 模型与元数据

| 模块 | 主要类/函数 | 职责 | 依赖 |
|------|------------|------|------|
| **model_metadata.py** | `get_model_context_length()`, `estimate_tokens_rough()`, `parse_context_limit_from_error()` | 模型上下文窗口、token 估算、错误解析 | `agent.models_dev` |
| **models_dev.py** | 模型开发注册表 | models.dev 注册表集成，支持多提供商上下文 | — |
| **smart_model_routing.py** | 智能路由函数 | 根据任务类型、负载、延迟选择最优模型 | `agent.model_metadata`, `agent.rate_limit_tracker` |
| **usage_pricing.py** | `estimate_usage_cost()`, `normalize_usage()` | 使用量跟踪、定价计算、成本估算 | `agent.model_metadata` |
| **rate_limit_tracker.py** | `RateLimitTracker` | API 速率限制跟踪，解析 x-ratelimit-* 头 | — |

### 6. 可观测性与用户体验

| 模块 | 主要类/函数 | 职责 | 依赖 |
|------|------------|------|------|
| **display.py** | `KawaiiSpinner`, `get_tool_emoji()`, `build_tool_preview()` | UI 显示工具 — kawaii 旋转器、工具预览、emoji | `rich` |
| **trajectory.py** | `save_trajectory()`, `has_incomplete_scratchpad()` | 对话轨迹保存、scratchpad 检测 | `json`, `pathlib` |
| **insights.py** | `track_task_completion()`, `compute_token_efficiency()` | 任务完成跟踪、token 效率计算、性能监控 | `agent.model_metadata` |
| **title_generator.py** | 标题生成函数 | 基于对话内容自动生成会话标题 | `agent.auxiliary_client` |
| **subdirectory_hints.py** | `SubdirectoryHintTracker` | 子目录提示跟踪，辅助文件定位 | `pathlib` |

### 7. 横切关注点

| 模块 | 主要类/函数 | 职责 | 依赖 |
|------|------------|------|------|
| **error_classifier.py** | `classify_api_error()`, `FailoverReason` | API 错误分类，结构化恢复决策 | `agent.redact` |
| **retry_utils.py** | `jittered_backoff()` | 抖动退避重试工具 | `time`, `random` |
| **redact.py** | 脱敏函数 | 敏感信息删除与数据保护 | `re` |

---

## 模块依赖关系图

```mermaid
graph TB
    subgraph "LLM Client Layer"
        A1[anthropic_adapter]
        A2[auxiliary_client]
        A3[copilot_acp_client]
        A4[credential_pool]
    end

    subgraph "Context Management"
        C1[context_engine]
        C2[context_compressor]
        C3[context_references]
        C4[manual_compression_feedback]
    end

    subgraph "Memory System"
        M1[memory_provider]
        M2[memory_manager]
    end

    subgraph "Prompt Engineering"
        P1[prompt_builder]
        P2[prompt_caching]
        P3[skill_commands]
        P4[skill_utils]
    end

    subgraph "Model & Metadata"
        D1[model_metadata]
        D2[models_dev]
        D3[smart_model_routing]
        D4[usage_pricing]
        D5[rate_limit_tracker]
    end

    subgraph "Observability & UX"
        O1[display]
        O2[trajectory]
        O3[insights]
        O4[title_generator]
        O5[subdirectory_hints]
    end

    subgraph "Cross-Cutting"
        X1[error_classifier]
        X2[retry_utils]
        X3[redact]
    end

    A2 --> A4
    A2 --> X2

    C2 --> A2
    C2 --> C1
    C2 --> D1
    C4 --> C2
    C4 --> M2

    M2 --> M1

    P1 --> P4
    P3 --> P4
    P3 --> P1

    D3 --> D1
    D3 --> D5
    D4 --> D1
    D4 --> D5

    O2 --> D1
    O3 --> D1
    O4 --> A2

    X1 --> X3
    X1 --> X2
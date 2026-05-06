# Hermes Agent 自改进系统架构分析

## 目录

- [1. 系统总览](#1-系统总览)
- [2. 软件架构图](#2-软件架构图)
- [3. 核心子系统详解](#3-核心子系统详解)
  - [3.1 轨迹保存与回放系统](#31-轨迹保存与回放系统)
  - [3.2 批量轨迹生成系统](#32-批量轨迹生成系统)
  - [3.3 RL 训练基础设施](#33-rl-训练基础设施)
  - [3.4 Atropos 环境框架](#34-atropos-环境框架)
  - [3.5 上下文压缩与迭代学习](#35-上下文压缩与迭代学习)
  - [3.6 On-Policy Distillation 环境](#36-on-policy-distillation-环境)
  - [3.7 工具集分布采样](#37-工具集分布采样)
- [4. 自改进闭环业务流程](#4-自改进闭环业务流程)
- [5. 设计模式分析](#5-设计模式分析)
- [6. 关键代码索引](#6-关键代码索引)

---

## 1. 系统总览

Hermes Agent 的自改进系统是一个**多层级、多反馈通道**的 Agent 自我进化架构，覆盖从数据采集、轨迹生成、奖励计算到模型微调的完整闭环。系统设计遵循"**在线学习 + 离线蒸馏**"双轨范式：

| 层级 | 功能 | 核心组件 |
|------|------|----------|
| **数据采集层** | 对话轨迹记录、工具调用统计 | `agent/trajectory.py`, `batch_runner.py` |
| **环境交互层** | Agent 循环执行、工具调用分发 | `environments/agent_loop.py`, `environments/tool_context.py` |
| **奖励计算层** | 任务验证、多维度评分 | `environments/hermes_base_env.py` 的 `compute_reward()` |
| **训练编排层** | RL 训练生命周期管理 | `tools/rl_training_tool.py` |
| **模型优化层** | GRPO/PPO 训练、On-Policy Distillation | Tinker-Atropos, `environments/agentic_opd_env.py` |
| **上下文优化层** | 迭代式上下文压缩、信息保留 | `agent/context_compressor.py` |
| **工具集探索层** | 概率采样不同工具配置 | `toolset_distributions.py` |

---

## 2. 软件架构图

### 2.1 自改进系统整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Hermes Agent 自改进系统架构                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────── 数据采集层 ──────────────────────────┐    │
│  │                                                             │    │
│  │  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐   │    │
│  │  │ AIAgent      │    │ BatchRunner  │   │ Trajectory   │   │    │
│  │  │ (单次对话)    │───▶│ (并行批量)    │──▶│ Saver        │   │    │
│  │  │ run_agent.py │    │ batch_runner │   │ trajectory.py│   │    │
│  │  └──────────────┘    └──────────────┘   └──────┬───────┘   │    │
│  │         │                                      │           │    │
│  │         │  ShareGPT JSONL                      │           │    │
│  │         ▼                                      ▼           │    │
│  │  ┌─────────────────────────────────────────────────────┐   │    │
│  │  │           轨迹数据存储 (JSONL)                        │   │    │
│  │  │  trajectory_samples.jsonl / failed_trajectories.jsonl│   │    │
│  │  └─────────────────────┬───────────────────────────────┘   │    │
│  └────────────────────────┼────────────────────────────────────┘    │
│                           │                                         │
│  ┌────────────────────────▼──── 环境交互层 ─────────────────────┐    │
│  │                                                              │    │
│  │  ┌──────────────────┐    ┌──────────────────────────────┐   │    │
│  │  │ HermesAgentLoop  │    │ ToolContext                  │   │    │
│  │  │ (Agent 循环引擎)  │    │ (奖励函数工具访问)            │   │    │
│  │  │ agent_loop.py    │    │ tool_context.py              │   │    │
│  │  │                  │    │                              │   │    │
│  │  │ • Phase 1: OpenAI│    │ • terminal() / read_file()   │   │    │
│  │  │ • Phase 2: VLLM  │    │ • web_search() / browser()   │   │    │
│  │  │ • Tool dispatch  │    │ • call_tool() (通用)          │   │    │
│  │  └────────┬─────────┘    └──────────────────────────────┘   │    │
│  │           │                                                  │    │
│  │           │ AgentResult (messages, turns, reasoning, errors) │    │
│  │           ▼                                                  │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │           HermesAgentBaseEnv (抽象基类)                │   │    │
│  │  │  • collect_trajectory() → rollout + reward            │   │    │
│  │  │  • _resolve_tools_for_group() → 工具集解析             │   │    │
│  │  │  • ScoredDataItem 构建 (tokens/masks/scores)          │   │    │
│  │  └─────────────────────┬────────────────────────────────┘   │    │
│  └────────────────────────┼─────────────────────────────────────┘    │
│                           │                                          │
│  ┌────────────────────────▼──── 奖励计算层 ─────────────────────┐    │
│  │                                                              │    │
│  │  ┌─────────────── 具体环境实现 ──────────────────────────┐   │    │
│  │  │                                                      │   │    │
│  │  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │   │    │
│  │  │  │AgenticOPD   │ │WebResearch   │ │TerminalBench2│  │   │    │
│  │  │  │Env          │ │Env           │ │Env           │  │   │    │
│  │  │  │(On-Policy   │ │(Web搜索+     │ │(终端任务+    │  │   │    │
│  │  │  │ Distillation)│ │ LLM Judge)  │ │  Test验证)   │  │   │    │
│  │  │  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘  │   │    │
│  │  │         │               │                │           │   │    │
│  │  │         ▼               ▼                ▼           │   │    │
│  │  │  compute_reward(item, result, ctx: ToolContext)      │   │    │
│  │  └──────────────────────┬───────────────────────────────┘   │    │
│  └─────────────────────────┼────────────────────────────────────┘    │
│                            │ ScoredDataGroup                         │
│  ┌─────────────────────────▼──── 训练编排层 ────────────────────┐    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │           RL Training Tool (10个工具)                  │   │    │
│  │  │  tools/rl_training_tool.py                            │   │    │
│  │  │                                                      │   │    │
│  │  │  rl_list_environments → AST扫描发现环境               │   │    │
│  │  │  rl_select_environment → 加载配置字段                  │   │    │
│  │  │  rl_get_current_config → 查看(可配/锁定)字段          │   │    │
│  │  │  rl_edit_config → 修改可配字段(锁定字段不可改)         │   │    │
│  │  │  rl_start_training → 启动3进程训练                    │   │    │
│  │  │  rl_check_status → WandB指标(30分钟限流)              │   │    │
│  │  │  rl_stop_training → 优雅停止(terminate→kill)          │   │    │
│  │  │  rl_get_results → 最终结果+指标                       │   │    │
│  │  │  rl_list_runs → 列出所有运行                          │   │    │
│  │  │  rl_test_inference → 多模型推理测试                    │   │    │
│  │  └──────────────────────┬───────────────────────────────┘   │    │
│  └─────────────────────────┼────────────────────────────────────┘    │
│                            │                                         │
│  ┌─────────────────────────▼──── 模型优化层 ────────────────────┐    │
│  │                                                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │    │
│  │  │ Atropos API  │  │ Tinker       │  │ VLLM/SGLang      │  │    │
│  │  │ Server       │  │ Trainer      │  │ Inference Server  │  │    │
│  │  │ (轨迹API)    │  │ (GRPO/PPO)   │  │ (推理服务)        │  │    │
│  │  │ :8000        │  │ + LoRA       │  │ :8001            │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │              WandB (指标监控)                          │   │    │
│  │  │  reward_mean / percent_correct / tool_errors_count    │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────── 上下文优化层 ───────────────────────────┐    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │           ContextCompressor (迭代式压缩)               │   │    │
│  │  │  • 工具输出裁剪(cheap pre-pass)                       │   │    │
│  │  │  • Head/Tail 保护                                     │   │    │
│  │  │  • 结构化摘要(Goal/Progress/Decisions/...)            │   │    │
│  │  │  • 迭代更新(_previous_summary)                        │   │    │
│  │  │  • Tool pair 完整性修复                               │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────── 工具集探索层 ───────────────────────────┐    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │           Toolset Distributions (16种分布)            │   │    │
│  │  │  default / image_gen / research / science /           │   │    │
│  │  │  development / safe / balanced / minimal /            │   │    │
│  │  │  terminal_only / terminal_web / creative /            │   │    │
│  │  │  reasoning / browser_use / browser_only /             │   │    │
│  │  │  browser_tasks / terminal_tasks / mixed_tasks         │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 RL 训练三进程架构

```
┌──────────────────────────────────────────────────────────────┐
│                    RL 训练运行时架构                            │
│                                                              │
│  ┌────────────────┐     ┌────────────────┐                   │
│  │  Atropos API   │     │  Tinker        │                   │
│  │  Server        │◀───▶│  Trainer       │                   │
│  │  (run-api)     │     │  (launch_      │                   │
│  │                │     │   training.py) │                   │
│  │  Port: 8000    │     │                │                   │
│  │                │     │  • GRPO/PPO    │                   │
│  │  • 轨迹收集    │     │  • LoRA rank=32│                   │
│  │  • Worker管理  │     │  • lr=4e-5     │                   │
│  │  • 评分聚合    │     │  • Checkpoint  │                   │
│  └───────┬────────┘     └───────┬────────┘                   │
│          │                      │                            │
│          │    ┌─────────────────┘                            │
│          │    │                                              │
│          ▼    ▼                                              │
│  ┌────────────────┐     ┌────────────────┐                   │
│  │  Environment   │     │  VLLM/SGLang   │                   │
│  │  Process       │     │  Inference     │                   │
│  │  (serve)       │     │  Server        │                   │
│  │                │     │  Port: 8001    │                   │
│  │  • get_next_   │     │                │                   │
│  │    item()      │     │  • 模型推理     │                   │
│  │  • compute_    │     │  • Token生成    │                   │
│  │    reward()    │     │  • Logprobs     │                   │
│  │  • evaluate()  │     │                │                   │
│  └────────────────┘     └────────────────┘                   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  WandB Metrics                                         │  │
│  │  • train/reward_mean  • train/percent_correct          │  │
│  │  • eval/percent_correct  • train/tool_errors_count     │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 核心子系统详解

### 3.1 轨迹保存与回放系统

**源文件**: [agent/trajectory.py](agent/trajectory.py)

轨迹保存是自改进系统的数据基础，将 Agent 的完整对话历史以 ShareGPT 格式持久化。

#### 架构设计

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  AIAgent     │     │  Trajectory      │     │  JSONL File     │
│  对话循环     │────▶│  Saver           │────▶│  (ShareGPT)     │
│              │     │                  │     │                 │
│  messages[]  │     │  save_trajectory │     │  conversations  │
│  tool_calls  │     │  convert_        │     │  timestamp      │
│  reasoning   │     │  scratchpad      │     │  model          │
│              │     │  has_incomplete  │     │  completed      │
└──────────────┘     └──────────────────┘     └─────────────────┘
```

#### 关键函数

| 函数 | 作用 |
|------|------|
| `save_trajectory()` | 追加轨迹到 JSONL，按完成状态分文件 |
| `convert_scratchpad_to_think()` | 将 `<REASONING_SCRATCHPAD>` 转换为 `<think/>` 标签 |
| `has_incomplete_scratchpad()` | 检测未闭合的推理标签（数据质量过滤） |

#### 数据格式

```json
{
  "conversations": [
    {"from": "human", "value": "..."},
    {"from": "gpt", "value": "..."},
    {"from": "gpt", "value": "[TOOL CALL] terminal(...)"},
    {"from": "tool", "value": "..."}
  ],
  "timestamp": "2026-04-15T10:30:00",
  "model": "anthropic/claude-opus-4.6",
  "completed": true
}
```

**设计要点**:
- 完成与失败轨迹分离存储（`trajectory_samples.jsonl` vs `failed_trajectories.jsonl`）
- 推理标签转换确保下游训练框架兼容性
- 简单追加式写入，无锁竞争风险

---

### 3.2 批量轨迹生成系统

**源文件**: [batch_runner.py](batch_runner.py)

批量轨迹生成是数据规模化采集的核心引擎，支持并行处理、断点续传和工具集分布采样。

#### 架构设计

```
┌──────────────────────────────────────────────────────────────┐
│                    BatchRunner 架构                           │
│                                                              │
│  ┌────────────┐     ┌────────────────┐     ┌─────────────┐ │
│  │ Dataset    │     │  Distribution  │     │  Checkpoint │ │
│  │ Loader     │     │  Sampler       │     │  Manager    │ │
│  │ (.jsonl)   │     │  (16种分布)     │     │  (断点续传)  │ │
│  └─────┬──────┘     └───────┬────────┘     └──────┬──────┘ │
│        │                    │                      │        │
│        ▼                    ▼                      ▼        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Multiprocessing Pool                     │   │
│  │                                                      │   │
│  │  Worker 1: [P0, P1, ...] → AIAgent → trajectory     │   │
│  │  Worker 2: [P5, P6, ...] → AIAgent → trajectory     │   │
│  │  Worker 3: [P10,P11,...] → AIAgent → trajectory     │   │
│  │  Worker 4: [P15,P16,...] → AIAgent → trajectory     │   │
│  │                                                      │   │
│  │  每个Worker:                                         │   │
│  │  1. sample_toolsets_from_distribution()              │   │
│  │  2. AIAgent(enabled_toolsets=sampled)                │   │
│  │  3. run_conversation(prompt, task_id)                │   │
│  │  4. _extract_tool_stats() + _extract_reasoning_stats│   │
│  │  5. _normalize_tool_stats() (统一schema)             │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              输出聚合                                  │   │
│  │  batch_N.jsonl → trajectories.jsonl (合并+过滤)       │   │
│  │  statistics.json (工具使用统计)                        │   │
│  │  checkpoint.json (断点数据)                            │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

#### 关键设计

**1. 工具统计归一化**

```python
ALL_POSSIBLE_TOOLS = set(TOOL_TO_TOOLSET_MAP.keys())

def _normalize_tool_stats(tool_stats):
    # 确保所有工具都有统一schema，未使用的工具补零
    # 目的：HuggingFace datasets Arrow/Parquet schema一致性
    normalized = {}
    for tool in ALL_POSSIBLE_TOOLS:
        normalized[tool] = tool_stats.get(tool, DEFAULT_TOOL_STATS).copy()
    return normalized
```

**2. 推理覆盖率追踪**

```python
def _extract_reasoning_stats(messages):
    # 检测 <REASONING_SCRATCHPAD> 或 native reasoning 字段
    # 返回: total_assistant_turns / turns_with_reasoning / turns_without_reasoning
    # 零推理样本被丢弃（discarded_no_reasoning）
```

**3. 智能断点续传**

```python
def _scan_completed_prompts_by_content(self):
    # 基于内容匹配而非索引匹配
    # 从 batch_*.jsonl 中提取已完成的 prompt 文本
    # 即使索引不匹配也能恢复

def _filter_dataset_by_completed(self, completed_prompts):
    # 过滤掉已完成的 prompt，只处理未完成的
```

**4. 腐败数据过滤**

```python
# 合并时过滤模型幻觉产生的无效工具名
invalid_tools = [k for k in tool_stats if k not in VALID_TOOLS]
if invalid_tools:
    filtered_entries += 1  # 丢弃此条目
```

---

### 3.3 RL 训练基础设施

**源文件**: [tools/rl_training_tool.py](tools/rl_training_tool.py)

RL 训练工具是 Agent 自我进化的核心编排层，通过 10 个注册工具管理从环境发现到训练监控的完整生命周期。

#### 工具清单

```
┌─────────────────────────────────────────────────────────────┐
│              RL Training Tool 生命周期                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Phase 1: 环境发现                                    │   │
│  │  rl_list_environments()                              │   │
│  │    └─▶ AST扫描 tinker_atropos/environments/*.py     │   │
│  │        查找 BaseEnv 子类                              │   │
│  │                                                      │   │
│  │  rl_select_environment(name)                         │   │
│  │    └─▶ importlib 动态加载环境模块                     │   │
│  │        调用 config_init() 获取配置类                  │   │
│  │        提取 Pydantic model_fields                     │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  Phase 2: 配置管理                                    │   │
│  │  rl_get_current_config()                             │   │
│  │    └─▶ 返回 configurable_fields + locked_fields      │   │
│  │                                                      │   │
│  │  rl_edit_config(field, value)                        │   │
│  │    └─▶ 修改可配字段（锁定字段拒绝修改）                │   │
│  │        LOCKED_FIELDS: tokenizer, lora_rank, lr...    │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  Phase 3: 训练执行                                    │   │
│  │  rl_start_training()                                 │   │
│  │    └─▶ 生成 run_id + config YAML                     │   │
│  │        asyncio.create_task(_spawn_training_run)      │   │
│  │        ┌─────────────────────────────────────┐       │   │
│  │        │ 3进程启动序列:                        │       │   │
│  │        │ 1. run-api (API Server) :8000       │       │   │
│  │        │    wait 5s                           │       │   │
│  │        │ 2. launch_training.py (Trainer)      │       │   │
│  │        │    wait 30s                          │       │   │
│  │        │ 3. environment.py serve (Env)        │       │   │
│  │        │    wait 90s + 10s                    │       │   │
│  │        └─────────────────────────────────────┘       │   │
│  │        + _monitor_training_run() (30s轮询)           │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  Phase 4: 监控与结果                                  │   │
│  │  rl_check_status(run_id)                             │   │
│  │    └─▶ 30分钟限流 + WandB指标查询                     │   │
│  │                                                      │   │
│  │  rl_stop_training(run_id)                            │   │
│  │    └─▶ terminate → wait 10s → kill (逆序停止)        │   │
│  │                                                      │   │
│  │  rl_get_results(run_id)                              │   │
│  │    └─▶ WandB summary + history                       │   │
│  │                                                      │   │
│  │  rl_test_inference(num_steps, group_size, models)    │   │
│  │    └─▶ 3模型 × N步推理测试 (OpenRouter)              │   │
│  │        qwen3-8b / glm-4.7-flash / minimax-m2.7      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 锁定配置机制

```python
LOCKED_FIELDS = {
    "env": {
        "tokenizer_name": "Qwen/Qwen3-8B",    # 固定tokenizer
        "rollout_server_url": "http://localhost:8000",
        "use_wandb": True,                     # 强制指标追踪
        "max_token_length": 8192,
        "max_num_workers": 2048,
        "total_steps": 2500,
        "steps_per_eval": 25,
    },
    "tinker": {
        "lora_rank": 32,                       # 固定LoRA秩
        "learning_rate": 0.00004,              # 固定学习率
        "max_token_trainer_length": 9000,
        "save_checkpoint_interval": 25,
    },
    "openai": [{
        "server_type": "sglang",               # 训练用SGLang
    }],
}
```

**设计意图**: 基础设施参数由系统管理员锁定，模型只能调整任务相关参数（如 `group_size`、`wandb_name`），防止训练配置漂移。

#### 环境发现机制

```python
def _scan_environments():
    # AST解析 — 无需import即可发现环境
    for py_file in ENVIRONMENTS_DIR.glob("*.py"):
        tree = ast.parse(file_content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if base_name == "BaseEnv":
                        # 提取 name, env_config_cls, docstring
                        environments.append(EnvironmentInfo(...))
```

---

### 3.4 Atropos 环境框架

**源文件**: [environments/hermes_base_env.py](environments/hermes_base_env.py)

HermesAgentBaseEnv 是所有 RL 训练环境的抽象基类，实现了 Atropos 集成的通用管道。

#### 双模式运行架构

```
┌─────────────────────────────────────────────────────────────┐
│              HermesAgentBaseEnv 双模式运行                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Phase 1: OpenAI Server Type (SFT数据生成/验证)      │   │
│  │                                                      │   │
│  │  OpenAI API ──▶ chat_completion(tools=...)           │   │
│  │                   │                                  │   │
│  │                   ▼                                  │   │
│  │  原生 tool_calls 解析                                │   │
│  │  DummyManagedServer (placeholder tokens)             │   │
│  │  适用于: SFT数据生成、验证器测试、评估                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Phase 2: VLLM Server Type (完整RL训练)              │   │
│  │                                                      │   │
│  │  VLLM/SGLang ──▶ /generate endpoint                 │   │
│  │                    │                                 │   │
│  │                    ▼                                 │   │
│  │  ManagedServer + ToolCallTranslator                  │   │
│  │  • 精确 token IDs + logprobs                         │   │
│  │  • 客户端 tool_call 解析器                           │   │
│  │  • ScoredDataGroup 含真实 tokens/masks               │   │
│  │  适用于: 完整RL训练 (GRPO/PPO)                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 抽象接口

```python
class HermesAgentBaseEnv(BaseEnv):
    @abstractmethod
    async def setup(self):
        """加载数据集，初始化状态"""

    @abstractmethod
    async def get_next_item(self) -> Item:
        """返回下一个数据项用于 rollout"""

    @abstractmethod
    def format_prompt(self, item: Item) -> str:
        """将数据项转换为用户消息"""

    @abstractmethod
    async def compute_reward(self, item, result, ctx: ToolContext) -> float:
        """评分 — 拥有完整 ToolContext 访问权限"""

    @abstractmethod
    async def evaluate(self, *args, **kwargs):
        """周期性评估"""
```

#### 工具集解析（Per-Group）

```python
def _resolve_tools_for_group(self):
    # 每个 group 解析一次，group 内所有 rollout 共享
    if config.distribution:
        group_toolsets = sample_toolsets_from_distribution(config.distribution)
    else:
        group_toolsets = config.enabled_toolsets

    tools = get_tool_definitions(enabled_toolsets=group_toolsets, ...)
    valid_names = {t["function"]["name"] for t in tools}
    return tools, valid_names
```

#### WandB 可视化

```python
@staticmethod
def _format_trajectory_for_display(messages):
    # 格式化对话轨迹用于 WandB rollout 表
    # 显示: [SYSTEM] / [USER] / [ASSISTANT thinking] / [TOOL CALL] / [TOOL RESULT]
    # 截断: reasoning > 300 chars, args > 200 chars, result > 500 chars
```

---

### 3.5 上下文压缩与迭代学习

**源文件**: [agent/context_compressor.py](agent/context_compressor.py)

上下文压缩器是 Agent 在单次会话内"自我改进"的机制 — 通过迭代式摘要保留关键信息，丢弃冗余上下文。

#### 压缩算法流程

```
┌─────────────────────────────────────────────────────────────┐
│              ContextCompressor 压缩算法                      │
│                                                             │
│  输入: messages[] (超过 threshold_tokens)                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Step 1: 工具输出裁剪 (cheap, no LLM)                │   │
│  │  _prune_old_tool_results()                           │   │
│  │  • 保护 tail (token_budget 决定)                     │   │
│  │  • >200 chars 的旧工具结果 → placeholder             │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  Step 2: 边界确定                                    │   │
│  │  • protect_first_n (head: system + first exchange)   │   │
│  │  • _find_tail_cut_by_tokens (tail: ~20K tokens)      │   │
│  │  • _align_boundary_forward/backward (避免切断        │   │
│  │    tool_call/result 组)                               │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  Step 3: 结构化摘要生成                               │   │
│  │  _generate_summary(turns_to_summarize)               │   │
│  │                                                      │   │
│  │  首次压缩:                                           │   │
│  │    "Create a structured handoff summary..."          │   │
│  │                                                      │   │
│  │  迭代更新 (有 _previous_summary 时):                  │   │
│  │    "You are updating a context compaction summary."  │   │
│  │    "PRESERVE all existing information..."            │   │
│  │    "ADD new progress. Move items..."                 │   │
│  │                                                      │   │
│  │  摘要模板:                                           │   │
│  │  ## Goal / Constraints / Progress (Done/In Progress/ │   │
│  │         Blocked) / Key Decisions /                   │   │
│  │  ## Resolved Questions / Pending User Asks /         │   │
│  │  ## Relevant Files / Remaining Work /                │   │
│  │  ## Critical Context / Tools & Patterns              │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │  Step 4: 组装压缩消息                                 │   │
│  │  • head messages (原始)                               │   │
│  │  • summary message (角色选择避免连续同角色)            │   │
│  │  • tail messages (原始)                               │   │
│  │  • _sanitize_tool_pairs() (修复孤立工具对)            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  输出: compressed messages[] (token数大幅减少)                │
└─────────────────────────────────────────────────────────────┘
```

#### 迭代更新机制

```python
# 首次压缩
if not self._previous_summary:
    prompt = "Create a structured handoff summary..."
else:
    # 后续压缩 — 迭代更新
    prompt = f"""
    PREVIOUS SUMMARY:
    {self._previous_summary}

    NEW TURNS TO INCORPORATE:
    {content_to_summarize}

    Update the summary. PRESERVE all existing information.
    ADD new progress. Move items from "In Progress" to "Done".
    """

# 存储摘要供下次迭代使用
self._previous_summary = summary
```

**关键设计**:
- **摘要预算缩放**: `budget = content_tokens × 0.20`，上限 12K tokens
- **失败冷却**: 摘要生成失败后 600 秒内不再尝试
- **Tool Pair 完整性**: 删除孤立 tool_result + 补充 stub tool_result
- **Focus Topic**: `/compress <topic>` 支持主题导向压缩

---

### 3.6 On-Policy Distillation 环境

**源文件**: [environments/agentic_opd_env.py](environments/agentic_opd_env.py)

AgenticOPDEnv 是最先进的自改进环境，实现了**在线策略蒸馏**（On-Policy Distillation），从每次工具交互中提取密集的 token 级训练信号。

#### OPD 核心思想

```
┌─────────────────────────────────────────────────────────────┐
│          On-Policy Distillation 原理                         │
│                                                             │
│  传统 RL:                                                   │
│  Agent rollout → 标量奖励 (0.0 or 1.0) → 稀疏信号           │
│                                                             │
│  OPD:                                                       │
│  Agent rollout → 每个工具交互 → next-state signal           │
│       │                                                     │
│       ▼                                                     │
│  (assistant_turn, next_state) pairs                         │
│       │                                                     │
│       ▼                                                     │
│  LLM Judge 提取 "hint" ( hindsight 信息)                    │
│       │                                                     │
│       ▼                                                     │
│  Enhanced Prompt = original context + hint                  │
│       │                                                     │
│       ▼                                                     │
│  Teacher Logprobs (enhanced) vs Student Logprobs (original) │
│       │                                                     │
│       ▼                                                     │
│  Per-token Advantage:                                       │
│    A_t = teacher_logprob(token_t) - student_logprob(token_t)│
│    Positive → teacher approves (upweight)                   │
│    Negative → teacher disapproves (downweight)              │
│                                                             │
│  结果: 密集、token级训练信号 (vs 稀疏标量奖励)               │
└─────────────────────────────────────────────────────────────┘
```

#### ScoredDataGroup 扩展

```python
# OPD 在 ScoredDataGroup 中新增两个字段:
scored_item = {
    "tokens": node.tokens,
    "masks": node.masked_tokens,
    "scores": reward,
    "distill_token_ids": teacher_top_k_predictions,  # OPD新增
    "distill_logprobs": teacher_logprobs,             # OPD新增
}
```

---

### 3.7 工具集分布采样

**源文件**: [toolset_distributions.py](toolset_distributions.py)

工具集分布采样是自改进系统的**探索机制**，通过概率采样不同的工具配置来增加训练数据多样性。

#### 采样算法

```python
def sample_toolsets_from_distribution(distribution_name):
    dist = get_distribution(distribution_name)
    selected_toolsets = []

    for toolset_name, probability in dist["toolsets"].items():
        # 每个工具集独立采样
        if random.random() * 100 < probability:
            selected_toolsets.append(toolset_name)

    # 保底: 至少选择概率最高的工具集
    if not selected_toolsets:
        highest = max(dist["toolsets"].items(), key=lambda x: x[1])[0]
        selected_toolsets.append(highest)

    return selected_toolsets
```

#### 16种预定义分布

| 分布名 | 场景 | 核心工具集 |
|--------|------|-----------|
| `default` | 全量工具 | 所有工具 100% |
| `image_gen` | 图像生成 | image_gen 90%, vision 90% |
| `research` | 网络研究 | web 90%, browser 70% |
| `science` | 科学计算 | web 94%, terminal 94%, file 94% |
| `development` | 软件开发 | terminal 80%, file 80%, moa 60% |
| `safe` | 安全模式 | 无 terminal |
| `terminal_only` | 纯终端 | terminal 100%, file 100% |
| `browser_tasks` | 浏览器任务 | browser 97% |
| `terminal_tasks` | 终端任务 | terminal 97%, file 97%, web 97% |
| `mixed_tasks` | 混合任务 | browser 92%, terminal 92%, file 92% |

---

## 4. 自改进闭环业务流程

### 4.1 完整自改进闭环

```
┌─────────────────────────────────────────────────────────────────┐
│                  Hermes Agent 自改进闭环                          │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  1.数据   │    │  2.轨迹   │    │  3.奖励   │    │  4.训练   │ │
│  │  采集     │───▶│  生成     │───▶│  计算     │───▶│  优化     │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │                                               │        │
│       │              ┌──────────┐                      │        │
│       │              │  5.部署   │◀─────────────────────┘        │
│       │              │  评估     │                               │
│       │              └────┬─────┘                               │
│       │                   │                                     │
│       └───────────────────┘ (反馈循环)                           │
│                                                                 │
│  详细流程:                                                       │
│                                                                 │
│  Step 1: 数据采集                                                │
│  ├── AIAgent 单次对话 → save_trajectory()                       │
│  ├── BatchRunner 批量生成 → trajectories.jsonl                   │
│  └── 工具集分布采样 → 数据多样性                                  │
│                                                                 │
│  Step 2: 轨迹生成                                                │
│  ├── HermesAgentLoop 执行 rollout                                │
│  │   ├── Phase 1: OpenAI server (SFT数据)                       │
│  │   └── Phase 2: VLLM ManagedServer (RL数据)                   │
│  ├── ToolContext 提供验证器工具访问                                │
│  └── 推理覆盖率统计 + 工具使用统计                                 │
│                                                                 │
│  Step 3: 奖励计算                                                │
│  ├── compute_reward(item, result, ctx)                          │
│  │   ├── 标量奖励 (0.0-1.0)                                     │
│  │   └── OPD: token级 teacher-student advantage                 │
│  ├── 多维度评分:                                                  │
│  │   ├── 任务完成度 (test pass/fail)                             │
│  │   ├── 源多样性 (web research)                                │
│  │   ├── 效率 (工具调用次数惩罚)                                  │
│  │   └── 工具使用 (bonus)                                       │
│  └── ScoredDataGroup 构建                                        │
│                                                                 │
│  Step 4: 训练优化                                                │
│  ├── rl_start_training() → 3进程启动                             │
│  │   ├── Atropos API Server (:8000)                             │
│  │   ├── Tinker Trainer (GRPO/PPO + LoRA)                      │
│  │   └── Environment Process (serve)                            │
│  ├── 锁定配置: lora_rank=32, lr=4e-5, tokenizer=Qwen3-8B       │
│  ├── WandB 监控: reward_mean, percent_correct                   │
│  └── Checkpoint: 每25步保存                                      │
│                                                                 │
│  Step 5: 部署评估                                                │
│  ├── rl_test_inference() → 多模型推理测试                        │
│  │   ├── qwen3-8b (small)                                      │
│  │   ├── glm-4.7-flash (medium)                                │
│  │   └── minimax-m2.7 (large)                                  │
│  ├── TerminalBench2 评估 (Docker隔离)                            │
│  └── 评估结果反馈 → 调整配置 → 下一轮训练                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Agent 循环内自改进流程

```
┌─────────────────────────────────────────────────────────────────┐
│              单次 Agent 循环内的自改进机制                         │
│                                                                 │
│  用户消息                                                        │
│     │                                                           │
│     ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  AIAgent.run_conversation()                              │   │
│  │                                                          │   │
│  │  while iteration < max_iterations:                       │   │
│  │    │                                                     │   │
│  │    ├── 1. 检查上下文是否超阈值                            │   │
│  │    │   if compressor.should_compress(prompt_tokens):     │   │
│  │    │       messages = compressor.compress(messages)      │   │
│  │    │       # 迭代式摘要: 保留关键信息，丢弃冗余            │   │
│  │    │                                                     │   │
│  │    ├── 2. LLM API 调用                                   │   │
│  │    │   response = client.chat.completions.create(...)    │   │
│  │    │                                                     │   │
│  │    ├── 3. 工具调用分发                                    │   │
│  │    │   if response.tool_calls:                           │   │
│  │    │       for tool_call in response.tool_calls:         │   │
│  │    │           result = handle_function_call(...)        │   │
│  │    │           # 工具执行结果反馈 → 模型自纠正             │   │
│  │    │                                                     │   │
│  │    ├── 4. 保存轨迹 (if save_trajectories)                │   │
│  │    │   save_trajectory(trajectory, model, completed)     │   │
│  │    │                                                     │   │
│  │    └── 5. 迭代直到模型停止调用工具或达到上限               │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│     │                                                           │
│     ▼                                                           │
│  最终响应 + 轨迹数据 (用于后续RL训练)                            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 RL 训练生命周期流程

```
┌─────────────────────────────────────────────────────────────────┐
│              RL 训练生命周期                                      │
│                                                                 │
│  rl_list_environments()                                         │
│     │                                                           │
│     │ AST扫描: tinker_atropos/environments/*.py                 │
│     │ 发现: AgenticOPDEnv, WebResearchEnv, ...                  │
│     ▼                                                           │
│  rl_select_environment("agentic-opd")                           │
│     │                                                           │
│     │ importlib 动态加载 → config_init() → 提取字段             │
│     │ 初始化: configurable_fields + locked_fields               │
│     ▼                                                           │
│  rl_get_current_config()                                        │
│     │                                                           │
│     │ 查看: group_size, wandb_name, dataset_name, ...           │
│     │ 锁定: tokenizer, lora_rank, learning_rate, ...            │
│     ▼                                                           │
│  rl_edit_config("group_size", 32)                               │
│     │                                                           │
│     │ 修改可配字段 (锁定字段拒绝修改)                             │
│     ▼                                                           │
│  rl_test_inference()  ←── 训练前验证                            │
│     │                                                           │
│     │ 3模型 × 3步 × 16 completions = 144 rollouts              │
│     │ 验证: 环境加载/提示构造/推理解析/评分逻辑                  │
│     ▼                                                           │
│  rl_start_training()                                            │
│     │                                                           │
│     │ 生成 run_id + config YAML                                 │
│     │ asyncio.create_task(_spawn_training_run)                  │
│     │                                                           │
│     │ ┌──────────────────────────────────────────────────┐     │
│     │ │  进程1: run-api (Atropos API Server)              │     │
│     │ │    wait 5s                                        │     │
│     │ │  进程2: launch_training.py (Tinker Trainer)       │     │
│     │ │    wait 30s                                       │     │
│     │ │  进程3: environment.py serve                       │     │
│     │ │    wait 100s                                      │     │
│     │ │  status = "running"                               │     │
│     │ │  + _monitor_training_run() (30s轮询)              │     │
│     │ └──────────────────────────────────────────────────┘     │
│     ▼                                                           │
│  rl_check_status(run_id)  ←── 30分钟限流                       │
│     │                                                           │
│     │ 进程状态 + WandB指标 (step, reward_mean, percent_correct) │
│     ▼                                                           │
│  ┌──────────────┐     ┌──────────────┐                          │
│  │ 训练成功      │     │ 训练失败/停滞  │                          │
│  │ rl_get_      │     │ rl_stop_     │                          │
│  │ results()    │     │ training()   │                          │
│  │              │     │              │                          │
│  │ WandB最终指标 │     │ 调整配置      │                          │
│  │ Checkpoint   │     │ 重新训练      │                          │
│  └──────────────┘     └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 设计模式分析

### 5.1 模板方法模式 (Template Method)

**HermesAgentBaseEnv** 定义了 RL 环境的骨架流程，子类只需实现 5 个抽象方法：

```
HermesAgentBaseEnv (抽象基类)
├── setup()           [抽象] 加载数据集
├── get_next_item()   [抽象] 获取下一个数据项
├── format_prompt()   [抽象] 格式化提示
├── compute_reward()  [抽象] 计算奖励
├── evaluate()        [抽象] 周期性评估
│
├── collect_trajectory()  [具体] 完整 rollout 管道
├── collect_trajectories() [具体] Group 级工具集解析
├── wandb_log()          [具体] 指标日志
└── add_rollouts_for_wandb() [具体] 可视化

具体实现:
├── AgenticOPDEnv     → On-Policy Distillation
├── WebResearchEnv    → Web 搜索 + LLM Judge
├── TerminalBench2Env → 终端任务 + Test 验证
└── HermesSWEEnv      → SWE-bench 任务
```

### 5.2 策略模式 (Strategy)

**Toolset Distributions** 实现了工具配置的策略模式：

```python
# 策略接口
def sample_toolsets_from_distribution(distribution_name: str) -> List[str]

# 具体策略 (16种分布)
"default"       → 全量工具
"terminal_tasks" → terminal 97%, file 97%, web 97%
"browser_tasks"  → browser 97%, vision 12%
"mixed_tasks"    → browser 92%, terminal 92%, file 92%
```

### 5.3 观察者模式 (Observer)

**训练监控** 实现了异步观察者模式：

```python
async def _monitor_training_run(run_state):
    while run_state.status == "running":
        await asyncio.sleep(30)
        # 观察进程状态变化
        if run_state.env_process.poll() is not None:
            # 状态变更 → 通知停止
            _stop_training_run(run_state)
```

### 5.4 建造者模式 (Builder)

**RL 训练配置** 采用建造者模式逐步构建：

```python
rl_select_environment(name)    # Step 1: 选择基础
rl_edit_config(field, value)   # Step 2: 定制配置
rl_edit_config(field, value)   # Step 3: 继续定制
rl_start_training()            # Step 4: 构建并启动
```

### 5.5 锁定配置模式 (Locked Configuration)

基础设施参数与可调参数分离，防止训练配置漂移：

```python
LOCKED_FIELDS = {
    "env": {"tokenizer_name": "...", "max_token_length": 8192, ...},
    "tinker": {"lora_rank": 32, "learning_rate": 0.00004, ...},
}

# rl_edit_config 拒绝修改锁定字段
if field_info.get("locked", False):
    return json.dumps({"error": f"Field '{field}' is locked"})
```

### 5.6 迭代器模式 (Iterator)

**上下文压缩** 的迭代式摘要更新：

```python
# 首次: 从零生成摘要
# 后续: 迭代更新已有摘要
if self._previous_summary:
    prompt = "Update the summary. PRESERVE existing info. ADD new progress."
else:
    prompt = "Create a structured handoff summary..."

self._previous_summary = summary  # 存储供下次迭代
```

### 5.7 代理模式 (Proxy)

**ToolContext** 作为工具访问的代理，为奖励函数提供受限但完整的工具访问：

```python
class ToolContext:
    def terminal(self, command, timeout=180): ...
    def read_file(self, path): ...
    def web_search(self, query): ...
    def call_tool(self, tool_name, arguments): ...  # 通用代理
```

### 5.8 原子写入模式 (Atomic Write)

断点数据使用原子写入确保一致性：

```python
from utils import atomic_json_write
# tempfile + fsync + os.replace 模式
self._save_checkpoint(checkpoint_data, lock=checkpoint_lock)
```

---

## 6. 关键代码索引

| 文件 | 行数 | 核心功能 |
|------|------|----------|
| [agent/trajectory.py](agent/trajectory.py) | 56 | 轨迹保存、推理标签转换 |
| [agent/context_compressor.py](agent/context_compressor.py) | 820 | 迭代式上下文压缩 |
| [batch_runner.py](batch_runner.py) | 1286 | 并行批量轨迹生成 |
| [tools/rl_training_tool.py](tools/rl_training_tool.py) | 1396 | RL训练生命周期管理(10工具) |
| [environments/hermes_base_env.py](environments/hermes_base_env.py) | 714 | Atropos环境抽象基类 |
| [environments/agent_loop.py](environments/agent_loop.py) | 534 | Agent循环引擎(双模式) |
| [environments/tool_context.py](environments/tool_context.py) | 473 | 奖励函数工具访问代理 |
| [environments/agentic_opd_env.py](environments/agentic_opd_env.py) | ~600 | On-Policy Distillation环境 |
| [environments/web_research_env.py](environments/web_research_env.py) | ~400 | Web搜索RL环境 |
| [environments/benchmarks/terminalbench_2/terminalbench2_env.py](environments/benchmarks/terminalbench_2/terminalbench2_env.py) | ~500 | TerminalBench2评估环境 |
| [toolset_distributions.py](toolset_distributions.py) | 363 | 16种工具集分布定义 |
| [environments/tool_call_parsers/](environments/tool_call_parsers/) | 多文件 | 多模型工具调用解析器 |

### 工具调用解析器

| 解析器 | 目标模型 |
|--------|----------|
| `hermes_parser.py` | Hermes 格式 |
| `qwen_parser.py` | Qwen 系列 |
| `qwen3_coder_parser.py` | Qwen3 Coder |
| `deepseek_v3_parser.py` | DeepSeek V3 |
| `deepseek_v3_1_parser.py` | DeepSeek V3.1 |
| `glm45_parser.py` | GLM-4.5 |
| `glm47_parser.py` | GLM-4.7 |
| `kimi_k2_parser.py` | Kimi-K2 |
| `llama_parser.py` | LLaMA 系列 |
| `mistral_parser.py` | Mistral 系列 |
| `longcat_parser.py` | LongCat |

---

## 总结

Hermes Agent 的自改进系统是一个**五层闭环架构**：

1. **数据采集层** — 轨迹保存 + 批量生成，支持工具集分布采样增加多样性
2. **环境交互层** — 双模式 Agent 循环（Phase 1 SFT / Phase 2 RL），ToolContext 提供验证器完整工具访问
3. **奖励计算层** — 多维度评分（任务完成/源多样性/效率/工具使用），OPD 提供 token 级密集信号
4. **训练编排层** — 10 个 RL 工具管理完整生命周期，锁定配置防止漂移，AST 发现环境
5. **上下文优化层** — 迭代式压缩保留关键信息，工具对完整性修复

核心创新点：
- **On-Policy Distillation**: 从每次工具交互提取 hindsight hint，生成 teacher-student token 级 advantage
- **迭代式上下文压缩**: `_previous_summary` 机制确保跨多次压缩的信息保留
- **工具集探索**: 16 种概率分布采样不同工具配置，增加训练数据多样性
- **锁定配置模式**: 基础设施参数与可调参数分离，Agent 只能修改任务相关参数

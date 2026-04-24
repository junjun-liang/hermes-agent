---
name: grpo-rl-training
description: 使用 TRL 进行 GRPO/RL 微调的专家级指南，用于推理和特定任务模型训练
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [transformers>=4.47.0, trl>=0.14.0, datasets>=3.2.0, peft>=0.14.0, torch]
metadata:
  hermes:
    tags: [Post-Training, Reinforcement Learning, GRPO, TRL, RLHF, Reward Modeling, Reasoning, DPO, PPO, Structured Output]

---

# 使用 TRL 进行 GRPO/RL 训练

使用 Transformer Reinforcement Learning (TRL) 库实现 Group Relative Policy Optimization (GRPO) 的专家级指南。本文提供实战经验总结的模式、关键洞察和生产就绪的工作流，用于使用自定义奖励函数微调语言模型。

## 何时使用此技能

当需要以下情况时使用 GRPO 训练：
- **强制执行特定输出格式**（如 XML 标签、JSON、结构化推理）
- **教授可验证任务**，带客观正确性指标（数学、编码、事实核查）
- **提高推理能力**，通过奖励思维链模式
- **将模型对齐到领域特定行为**，无需标记偏好数据
- **同时优化多个目标**（格式 + 正确性 + 风格）

**不要将 GRPO 用于：**
- 简单监督微调任务（改用 SFT）
- 没有明确奖励信号的任务
- 已经有高质量偏好对时（改用 DPO/PPO）

---

## 核心概念

### 1. GRPO 算法基础

**关键机制：**
- 为每个提示词生成**多个完成**（组大小：4-16）
- 使用奖励函数比较组内的完成
- 更新策略以偏好组内更高奖励的响应

**与 PPO 的关键区别：**
- 不需要单独的奖励模型
- 更样本高效（从组内比较中学习）
- 更易于实现和调试

**数学直觉：**
```
对于每个提示词 p:
  1. 生成 N 个完成：{c₁, c₂, ..., cₙ}
  2. 计算奖励：{r₁, r₂, ..., rₙ}
  3. 学习增加高奖励完成的概率
     相对于同组内低奖励的完成
```

### 2. 奖励函数设计哲学

**黄金法则：**
1. **组合多个奖励函数** — 每个处理一个方面（格式、正确性、风格）
2. **适当缩放奖励** — 权重越高 = 信号越强
3. **使用增量奖励** — 部分合规获得部分分数
4. **独立测试奖励** — 隔离调试每个奖励函数

**奖励函数类型：**

| 类型 | 用途 | 示例权重 |
|------|----------|----------|
| **正确性** | 可验证任务（数学、代码） | 2.0（最高） |
| **格式** | 严格结构强制执行 | 0.5-1.0 |
| **长度** | 鼓励冗长/简洁 | 0.1-0.5 |
| **风格** | 惩罚不需要的模式 | -0.5 到 0.5 |

---

## 实现工作流

### 步骤 1：数据集准备

**关键要求：**
- 提示词使用聊天格式（带 'role' 和 'content' 的字典列表）
- 包含系统提示词以设定预期
- 对于可验证任务，包含真实答案作为额外列

**示例结构：**
```python
from datasets import load_dataset, Dataset

SYSTEM_PROMPT = """
按以下格式响应：
<reasoning>
[你的逐步思考]
</reasoning>
<answer>
[最终答案]
</answer>
"""

def prepare_dataset(raw_data):
    """
    将原始数据转换为 GRPO 兼容格式。

    返回：带以下列的 Dataset：
    - 'prompt'：带 role/content 的 List[Dict]（系统 + 用户消息）
    - 'answer'：str（真实答案，可选但推荐）
    """
    return raw_data.map(lambda x: {
        'prompt': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': x['question']}
        ],
        'answer': extract_answer(x['raw_answer'])
    })
```

**专业技巧：**
- 在系统提示词中使用 one-shot 或 few-shot 示例处理复杂格式
- 保持提示词简洁（max_prompt_length：256-512 token）
- 训练前验证数据质量（垃圾进 = 垃圾出）

### 步骤 2：奖励函数实现

**模板结构：**
```python
def reward_function_name(
    prompts,        # List[List[Dict]]：原始提示词
    completions,    # List[List[Dict]]：模型生成
    answer=None,    # 可选：数据集中的真实答案
    **kwargs        # 额外数据集列
) -> list[float]:
    """
    评估完成并返回奖励。

    返回：浮点数列表（每个完成一个）
    """
    # 提取完成文本
    responses = [comp[0]['content'] for comp in completions]

    # 计算奖励
    rewards = []
    for response in responses:
        score = compute_score(response)
        rewards.append(score)

    return rewards
```

**示例 1：正确性奖励（数学/编码）**
```python
def correctness_reward(prompts, completions, answer, **kwargs):
    """用高分奖励正确答案。"""
    responses = [comp[0]['content'] for comp in completions]
    extracted = [extract_final_answer(r) for r in responses]
    return [2.0 if ans == gt else 0.0
            for ans, gt in zip(extracted, answer)]
```

**示例 2：格式奖励（结构化输出）**
```python
import re

def format_reward(completions, **kwargs):
    """奖励 XML 类结构化格式。"""
    pattern = r'<reasoning>.*?</reasoning>\s*<answer>.*?</answer>'
    responses = [comp[0]['content'] for comp in completions]
    return [1.0 if re.search(pattern, r, re.DOTALL) else 0.0
            for r in responses]
```

**示例 3：增量格式奖励（部分分数）**
```python
def incremental_format_reward(completions, **kwargs):
    """为格式合规颁发部分分数。"""
    responses = [comp[0]['content'] for comp in completions]
    rewards = []

    for r in responses:
        score = 0.0
        if '<reasoning>' in r:
            score += 0.25
        if '</reasoning>' in r:
            score += 0.25
        if '<answer>' in r:
            score += 0.25
        if '</answer>' in r:
            score += 0.25
        # 惩罚关闭标签后的额外文本
        if r.count('</answer>') == 1:
            extra_text = r.split('</answer>')[-1].strip()
            score -= len(extra_text) * 0.001
        rewards.append(score)

    return rewards
```

**关键洞察：**
组合 3-5 个奖励函数以获得健壮的训练。信号多样性比顺序更重要。

### 步骤 3：训练配置

**内存优化配置（小型 GPU）**
```python
from trl import GRPOConfig

training_args = GRPOConfig(
    output_dir="outputs/grpo-model",

    # 学习率
    learning_rate=5e-6,          # 越低越稳定
    adam_beta1=0.9,
    adam_beta2=0.99,
    weight_decay=0.1,
    warmup_ratio=0.1,
    lr_scheduler_type='cosine',

    # 批量设置
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,  # 有效批量 = 4

    # GRPO 特定
    num_generations=8,            # 组大小：推荐 8-16
    max_prompt_length=256,
    max_completion_length=512,

    # 训练时长
    num_train_epochs=1,
    max_steps=None,               # 或设置固定步数（如 500）

    # 优化
    bf16=True,                    # A100/H100 上更快
    optim="adamw_8bit",          # 内存高效优化器
    max_grad_norm=0.1,

    # 日志
    logging_steps=1,
    save_steps=100,
    report_to="wandb",            # 或 "none" 表示不记录
)
```

**高性能配置（大型 GPU）**
```python
training_args = GRPOConfig(
    output_dir="outputs/grpo-model",
    learning_rate=1e-5,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,
    num_generations=16,           # 更大组 = 更好信号
    max_prompt_length=512,
    max_completion_length=1024,
    num_train_epochs=1,
    bf16=True,
    use_vllm=True,                # 用 vLLM 快速生成
    logging_steps=10,
)
```

**关键超参数：**

| 参数 | 影响 | 调优建议 |
|-----------|--------|----------|
| `num_generations` | 比较的组大小 | 从 8 开始，如果 GPU 允许增加到 16 |
| `learning_rate` | 收敛速度/稳定性 | 5e-6（安全），1e-5（更快，有风险） |
| `max_completion_length` | 输出冗长度 | 匹配任务（推理 512，短答案 256） |
| `gradient_accumulation_steps` | 有效批量大小 | GPU 内存有限时增加 |

### 步骤 4：模型设置和训练

**标准设置（Transformers）**
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig
from trl import GRPOTrainer

# 加载模型
model_name = "Qwen/Qwen2.5-1.5B-Instruct"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",  # 快 2-3 倍
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# 可选：用于参数高效训练的 LoRA
peft_config = LoraConfig(
    r=16,                         # 秩（越高容量越大）
    lora_alpha=32,               # 缩放因子（通常为 2*r）
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    task_type="CAUSAL_LM",
    lora_dropout=0.05,
)

# 初始化训练器
trainer = GRPOTrainer(
    model=model,
    processing_class=tokenizer,
    reward_funcs=[
        incremental_format_reward,
        format_reward,
        correctness_reward,
    ],
    args=training_args,
    train_dataset=dataset,
    peft_config=peft_config,      # 全参数微调时移除
)

# 训练
trainer.train()

# 保存
trainer.save_model("final_model")
```

**Unsloth 设置（快 2-3 倍）**
```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="google/gemma-3-1b-it",
    max_seq_length=1024,
    load_in_4bit=True,
    fast_inference=True,
    max_lora_rank=32,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,
    use_gradient_checkpointing="unsloth",
)

# 其余与标准设置相同
trainer = GRPOTrainer(model=model, ...)
trainer.train()
```

---

## 关键训练洞察

### 1. 损失行为（预期模式）
- **损失从接近 0 开始并在训练期间增加**
- 这是正确的 — 损失测量与初始策略的 KL 散度
- 模型正在学习（从原始行为发散以优化奖励）
- 监控奖励指标而不是损失来跟踪进度

### 2. 奖励跟踪

需要监控的关键指标：
- `reward`：所有完成的平均值
- `reward_std`：组内多样性（应保持 > 0）
- `kl`：与参考的 KL 散度（应适度增长）

**健康训练模式：**
```
步骤   奖励    奖励标准差   KL
100    0.5       0.3          0.02
200    0.8       0.25         0.05
300    1.2       0.2          0.08  ← 良好进展
400    1.5       0.15         0.12
```

**警告信号：**
- 奖励标准差 → 0（模型坍缩到单一响应）
- KL 爆炸（> 0.5）（发散太多，降低学习率）
- 奖励停滞（奖励函数太严厉或模型容量问题）

### 3. 常见陷阱和解决方案

| 问题 | 症状 | 解决方案 |
|---------|---------|----------|
| **模式坍缩** | 所有完成相同 | 增加 `num_generations`，添加多样性惩罚 |
| **没有学习** | 奖励平坦 | 检查奖励函数逻辑，增加学习率 |
| **OOM 错误** | GPU 内存超出 | 减少 `num_generations`，启用梯度检查点 |
| **训练缓慢** | < 1 it/s | 启用 `use_vllm=True`，使用 Unsloth，减少序列长度 |
| **忽略格式** | 模型不遵循结构 | 增加格式奖励权重，添加增量奖励 |

---

## 高级模式

### 1. 多阶段训练

对于复杂任务，分阶段训练：

```python
# 阶段 1：格式合规（epochs=1）
trainer_stage1 = GRPOTrainer(
    model=model,
    reward_funcs=[incremental_format_reward, format_reward],
    ...
)
trainer_stage1.train()

# 阶段 2：正确性（epochs=1）
trainer_stage2 = GRPOTrainer(
    model=model,
    reward_funcs=[format_reward, correctness_reward],
    ...
)
trainer_stage2.train()
```

### 2. 自适应奖励缩放

```python
class AdaptiveReward:
    def __init__(self, base_reward_func, initial_weight=1.0):
        self.func = base_reward_func
        self.weight = initial_weight

    def __call__(self, *args, **kwargs):
        rewards = self.func(*args, **kwargs)
        return [r * self.weight for r in rewards]

    def adjust_weight(self, success_rate):
        """模型挣扎时增加权重，成功时降低。"""
        if success_rate < 0.3:
            self.weight *= 1.2
        elif success_rate > 0.8:
            self.weight *= 0.9
```

### 3. 自定义数据集集成

```python
def load_custom_knowledge_base(csv_path):
    """示例：学校交流平台文档。"""
    import pandas as pd
    df = pd.read_csv(csv_path)

    dataset = Dataset.from_pandas(df).map(lambda x: {
        'prompt': [
            {'role': 'system', 'content': CUSTOM_SYSTEM_PROMPT},
            {'role': 'user', 'content': x['question']}
        ],
        'answer': x['expert_answer']
    })
    return dataset
```

---

## 部署和推理

### 保存和合并 LoRA

```python
# 将 LoRA 适配器合并到基础模型
if hasattr(trainer.model, 'merge_and_unload'):
    merged_model = trainer.model.merge_and_unload()
    merged_model.save_pretrained("production_model")
    tokenizer.save_pretrained("production_model")
```

### 推理示例

```python
from transformers import pipeline

generator = pipeline(
    "text-generation",
    model="production_model",
    tokenizer=tokenizer
)

result = generator(
    [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': "15 + 27 等于多少？"}
    ],
    max_new_tokens=256,
    do_sample=True,
    temperature=0.7,
    top_p=0.9
)
print(result[0]['generated_text'])
```

---

## 最佳实践清单

**训练前：**
- [ ] 验证数据集格式（提示词为 List[Dict]）
- [ ] 在样本数据上测试奖励函数
- [ ] 从数据计算预期的 max_prompt_length
- [ ] 根据 GPU 内存选择适当的 num_generations
- [ ] 设置日志（推荐 wandb）

**训练期间：**
- [ ] 监控奖励进展（应增加）
- [ ] 检查 reward_std（应保持 > 0.1）
- [ ] 注意 OOM 错误（需要时减少批量大小）
- [ ] 每 50-100 步采样生成
- [ ] 在保留集上验证格式合规性

**训练后：**
- [ ] 如果使用 PEFT 则合并 LoRA 权重
- [ ] 在多样化提示词上测试
- [ ] 与基础模型比较
- [ ] 记录奖励权重和超参数
- [ ] 保存可复现配置

---

## 故障排除指南

### 调试工作流
1. **隔离奖励函数** — 独立测试每个
2. **检查数据分布** — 确保提示词多样性
3. **降低复杂度** — 从单个奖励开始，逐步添加
4. **监控生成** — 每 N 步打印样本
5. **验证提取逻辑** — 确保答案解析有效

### 快速修复
```python
# 调试奖励函数
def debug_reward(completions, **kwargs):
    responses = [comp[0]['content'] for comp in completions]
    for i, r in enumerate(responses[:2]):  # 打印前 2 个
        print(f"响应 {i}: {r[:200]}...")
    return [1.0] * len(responses)  # 虚拟奖励

# 不训练测试
trainer = GRPOTrainer(..., reward_funcs=[debug_reward])
trainer.generate_completions(dataset[:1])  # 生成而不更新
```

---

## 参考资料和资源

**官方文档：**
- TRL GRPO 训练器：https://huggingface.co/docs/trl/grpo_trainer
- DeepSeek R1 论文：https://arxiv.org/abs/2501.12948
- Unsloth 文档：https://docs.unsloth.ai/

**示例仓库：**
- Open R1 实现：https://github.com/huggingface/open-r1
- TRL 示例：https://github.com/huggingface/trl/tree/main/examples

**推荐阅读：**
- 代理指令的渐进式披露模式
- RL 中的奖励塑造（Ng 等）
- LoRA 论文（Hu 等，2021）

---

## 代理使用说明

加载此技能时：

1. **在实现 GRPO 训练之前阅读整个文件**
2. **从最简单的奖励函数开始**（如基于长度的）验证设置
3. **使用 `templates/` 目录中的模板**作为起点
4. **参考 `examples/`** 获取特定任务的实现
5. **按顺序遵循工作流**（不要跳过步骤）
6. **增量调试** — 一次添加一个奖励函数

**关键提醒：**
- 始终使用多个奖励函数（3-5 个最优）
- 监控奖励指标，而不是损失
- 训练前测试奖励函数
- 从小开始（num_generations=4），逐步扩大
- 频繁保存检查点（每 100 步）

此技能设计用于**专家级实现**。初学者应在尝试 GRPO 之前从监督微调开始。

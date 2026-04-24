---
name: trl-fine-tuning
description: 使用 TRL 库通过 RLHF（PPO、DPO、ORPO）对齐语言模型。当需要对带偏好数据的模型进行对齐训练、使用奖励模型优化、直接偏好优化或运行人类反馈强化学习时使用。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [trl>=0.10.0, transformers>=4.46.0, datasets>=3.0.0, peft>=0.12.0, accelerate>=0.34.0, torch>=2.0.0]
metadata:
  hermes:
    tags: [Post-Training, RLHF, DPO, PPO, ORPO, TRL, Alignment, Reward Modeling, Reinforcement Learning, Preference Optimization]

---

# TRL - Transformer 强化学习

## 何时使用 TRL

**当以下情况时使用 TRL：**
- 使用偏好数据对齐模型（RLHF）
- 使用奖励模型优化输出
- 运行直接偏好优化（DPO）
- 执行人类反馈强化学习
- 模型安全和对齐

**关键特性：**
- **DPO**：直接偏好优化（最简单）
- **PPO**：带奖励模型的 RLHF
- **ORPO**：无需参考模型的比值比
- **奖励建模**：训练偏好分类器
- **SFT**：监督微调

**当以下情况改用替代方案：**
- **PEFT**：仅需要 LoRA/QLoRA 微调
- **Axolotl**：需要 YAML 配置微调
- **Unsloth**：需要 2-5 倍更快的训练速度

## 快速开始

### 安装

```bash
pip install trl transformers datasets peft accelerate torch
```

### SFT 微调

```python
from trl import SFTTrainer, SFTConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
import torch

# 加载模型
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B")
tokenizer.pad_token = tokenizer.eos_token

# 加载数据集
dataset = load_dataset("HuggingFaceH4/no_robots")

# 配置
training_args = SFTConfig(
    output_dir="outputs/sft-model",
    max_seq_length=2048,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    num_train_epochs=3,
    bf16=True,
    logging_steps=10,
    save_steps=100,
)

# 训练
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    tokenizer=tokenizer,
)
trainer.train()
trainer.save_model()
```

## 对齐方法

### DPO（直接偏好优化）

```python
from trl import DPOTrainer, DPOConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
import torch

# 加载模型和参考模型
model = AutoModelForCausalLM.from_pretrained(
    "your-sft-model",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
ref_model = AutoModelForCausalLM.from_pretrained(
    "your-sft-model",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("your-sft-model")

# 加载偏好数据集
dataset = load_dataset("Anthropic/hh-rlhf")

# DPO 需要以下格式：
# {"prompt": "...", "chosen": "...", "rejected": "..."}

# 配置
training_args = DPOConfig(
    output_dir="outputs/dpo-model",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=5e-7,  # DPO 需要低学习率
    beta=0.1,            # DPO 温度参数
    num_train_epochs=1,
    bf16=True,
    logging_steps=10,
)

# 训练
trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    args=training_args,
    train_dataset=dataset["train"],
    tokenizer=tokenizer,
)
trainer.train()
```

### ORPO（比值比偏好优化）

```python
from trl import ORPOConfig, ORPOTrainer

# ORPO 不需要参考模型
training_args = ORPOConfig(
    output_dir="outputs/orpo-model",
    per_device_train_batch_size=4,
    learning_rate=8e-7,
    beta=0.1,        # 比值比权重
    max_length=2048,
    num_train_epochs=1,
)

trainer = ORPOTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    tokenizer=tokenizer,
)
trainer.train()
```

### PPO（近端策略优化）

```python
from trl import PPOTrainer, PPOConfig
from transformers import AutoModelForCausalLM, AutoTokenizer

# 需要奖励模型
from reward_model import MyRewardModel

config = PPOConfig(
    output_dir="outputs/ppo-model",
    learning_rate=1.41e-5,
    batch_size=8,
    gradient_accumulation_steps=4,
    ppo_epochs=4,
)

trainer = PPOTrainer(
    model=model,
    ref_model=ref_model,
    reward_model=reward_model,
    args=config,
    train_dataset=dataset,
    tokenizer=tokenizer,
)
trainer.train()
```

## 奖励建模

```python
from trl import RewardTrainer, RewardConfig
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from datasets import load_dataset

# 加载分类模型
model = AutoModelForSequenceClassification.from_pretrained(
    "your-base-model",
    num_labels=1,  # 二分类（选择/拒绝）
    torch_dtype=torch.bfloat16
)
tokenizer = AutoTokenizer.from_pretrained("your-base-model")

# 数据集格式：{"prompt": "...", "chosen": "...", "rejected": "..."}
dataset = load_dataset("Anthropic/hh-rlhf")

config = RewardConfig(
    output_dir="outputs/reward-model",
    per_device_train_batch_size=4,
    learning_rate=1e-5,
    num_train_epochs=1,
)

trainer = RewardTrainer(
    model=model,
    args=config,
    train_dataset=dataset["train"],
    tokenizer=tokenizer,
)
trainer.train()
```

## 数据集格式

### SFT 数据集

```python
# 带对话的聊天格式
[
    {
        "messages": [
            {"role": "system", "content": "你是有用的助手。"},
            {"role": "user", "content": "法国的首都是什么？"},
            {"role": "assistant", "content": "巴黎。"}
        ]
    }
]
```

### DPO/ORPO 数据集

```python
# 带偏好的数据集
[
    {
        "prompt": "法国的首都是什么？",
        "chosen": "法国的首都是巴黎。",     # 首选
        "rejected": "是伦敦。"              # 被拒绝
    }
]
```

### 自定义数据集

```python
from datasets import Dataset

data = {
    "prompt": ["问题 1", "问题 2"],
    "chosen": ["好答案 1", "好答案 2"],
    "rejected": ["差答案 1", "差答案 2"]
}

dataset = Dataset.from_dict(data)
```

## LoRA 集成

```python
from peft import LoraConfig, TaskType

# LoRA 配置
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
)

# 与 DPOTrainer 配合使用
trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    peft_config=peft_config,
)
```

## 多阶段训练

### 典型 RLHF 管道

```python
# 阶段 1：SFT
sft_trainer = SFTTrainer(...)
sft_trainer.train()
sft_trainer.save_model("sft-model")

# 阶段 2：奖励建模
reward_trainer = RewardTrainer(...)
reward_trainer.train()
reward_trainer.save_model("reward-model")

# 阶段 3：PPO 对齐
ppo_trainer = PPOTrainer(
    model=sft_model,
    reward_model=reward_model,
    ...
)
ppo_trainer.train()
```

### 简化管道（SFT + DPO）

```python
# 阶段 1：SFT
sft_trainer = SFTTrainer(...)
sft_trainer.train()
sft_trainer.save_model("sft-model")

# 阶段 2：DPO（不需要奖励模型）
dpo_trainer = DPOTrainer(
    model=sft_model,
    ref_model=sft_model,
    ...
)
dpo_trainer.train()
```

## 推理

```python
from transformers import pipeline

# 加载对齐的模型
generator = pipeline(
    "text-generation",
    model="outputs/dpo-model",
    tokenizer=tokenizer
)

# 生成
result = generator(
    "你是友好的助手吗？",
    max_new_tokens=256,
    do_sample=True,
    temperature=0.7,
)
print(result[0]["generated_text"])
```

## 硬件要求

### VRAM 要求

| 方法 | 模型大小 | VRAM | GPU |
|--------|----------|---------|--------|
| **SFT** | 7B | 16GB | RTX 4090 |
| **SFT + LoRA** | 7B | 8GB | RTX 3060 |
| **DPO** | 7B | 28GB | A10 |
| **DPO + LoRA** | 7B | 12GB | RTX 3090 |
| **PPO** | 7B | 40GB | A100 |
| **ORPO** | 7B | 20GB | A10 |

## 常见问题

**参考模型内存不足：**
```python
# 使用 LoRA 替代完整参考模型
# 或使用更小的参考模型
```

**训练不稳定（DPO）：**
```python
# 降低学习率
learning_rate = 1e-7

# 调整 beta
beta = 0.05  # 从 0.1 降低
```

**质量差：**
```python
# 增加 SFT 阶段
num_train_epochs = 5

# 使用更高质量的数据集
```

## 资源

- **文档**：https://huggingface.co/docs/trl
- **GitHub**：https://github.com/huggingface/trl（10k+ stars）
- **示例**：https://github.com/huggingface/trl/tree/main/examples
- **论文**：
  - DPO: "Direct Preference Optimization"
  - ORPO: "Odds Ratio Preference Optimization"
  - PPO: "Proximal Policy Optimization Algorithms"

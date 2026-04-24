---
name: peft-fine-tuning
description: 使用 LoRA、QLoRA 和适配器高效微调大型模型。用于在有限 GPU 内存下微调、快速实验、训练多个任务特定的小适配器，或将模型适配到不同任务而无需全参数更新。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [peft>=0.10.0, transformers>=4.40.0, torch>=2.0.0, bitsandbytes>=0.43.0, accelerate>=0.30.0]
metadata:
  hermes:
    tags: [PEFT, Fine-Tuning, LoRA, QLoRA, Adapters, Efficient Training, Parameter-Efficient, Low-Rank Adaptation, Quantization]

---

# PEFT - 参数高效微调

## 何时使用 PEFT

**当以下情况时使用 PEFT：**
- 微调大型模型而有限制 GPU 内存
- 快速实验不同任务
- 训练多个任务特定的小适配器
- 将模型适配到不同任务而无需全参数更新
- 存储小的适配器权重而不是完整模型

**关键特性：**
- **LoRA**：低秩适配，冻结原始权重
- **QLoRA**：量化 + LoRA，极低内存使用
- **Prompt Tuning**：软提示词，无权重更新
- **Prefix Tuning**：可训练的前缀嵌入
- **Adapter**：小型可训练模块

**当以下情况改用替代方案：**
- **全参数微调**：需要模型完整容量
- **Axolotl**：需要声明式 YAML 配置
- **Unsloth**：需要 2-5 倍更快的训练速度
- **TRL**：需要 RLHF/DPO 训练

## 快速开始

### 安装

```bash
pip install peft transformers torch
pip install bitsandbytes  # 用于量化
```

### 基本 LoRA 微调

```python
from peft import LoraConfig, TaskType, get_peft_model, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
import torch

# 加载基础模型
model_name = "meta-llama/Llama-3.1-8B"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# 配置 LoRA
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                    # 秩（越高容量越大）
    lora_alpha=32,           # 缩放因子
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    inference_mode=False
)

# 应用 LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # 通常 <1% 参数可训练

# 训练
training_args = TrainingArguments(
    output_dir="./lora-output",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    fp16=True,
    logging_steps=10,
    save_steps=100,
    save_total_limit=3,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer
)
trainer.train()

# 保存适配器
model.save_pretrained("./lora-adapter")
```

## 方法比较

### 可用方法

| 方法 | 可训练参数 | 内存 | 质量 | 用途 |
|--------|-----------|---------|---------|----------|
| **LoRA** | 0.1-1% | 低 | 高 | **推荐默认** |
| **QLoRA** | 0.1-1% | 极低 | 高 | **大模型/低内存** |
| **Prefix Tuning** | 0.01% | 最低 | 中 | 快速适配 |
| **Prompt Tuning** | 0.001% | 最低 | 中低 | 最小更改 |
| **Adapter** | 1-5% | 中 | 高 | 复杂任务 |
| **IA³** | 0.01% | 低 | 中 | 高效微调 |

### LoRA 详解

```python
from peft import LoraConfig

# 基本配置
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,                     # 秩：8-32（越高容量越大）
    lora_alpha=16,           # 通常为 2*r
    target_modules=[         # 要适配的模块
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    lora_dropout=0.05,       # 丢弃率防止过拟合
    bias="none",             # 不训练偏置
    inference_mode=False,    # 训练模式
)

# 自动目标模块（所有线性层）
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    target_modules="all-linear",  # 自动选择
)
```

**秩选择：**
- `r=8`：快速实验，有限内存
- `r=16`：推荐默认
- `r=32`：复杂任务，更多数据
- `r=64+`：全参数微调替代

### QLoRA 详解

```python
from transformers import BitsAndBytesConfig
from peft import LoraConfig, get_peft_model

# 4 位量化
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",       # 正常化浮点 4 位
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,   # 嵌套量化节省更多内存
)

# 加载量化模型
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)

# 准备用于训练的模型
from peft import prepare_model_for_kbit_training
model = prepare_model_for_kbit_training(model)

# 应用 LoRA
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)

model = get_peft_model(model, lora_config)
```

## 内存要求

### 不同方法的 VRAM

| 模型大小 | 方法 | VRAM | GPU |
|----------|--------|---------|--------|
| 7B | 全参数 | 60GB | A100 |
| 7B | LoRA | 16GB | RTX 4090 |
| 7B | QLoRA（4 位） | 6GB | RTX 3060 |
| 13B | LoRA | 28GB | A10 |
| 13B | QLoRA（4 位） | 10GB | RTX 3090 |
| 70B | QLoRA（4 位） | 40GB | A100 |

### 内存优化技巧

```python
# 梯度检查点
model.gradient_checkpointing_enable()

# 减少批量大小
training_args = TrainingArguments(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
)

# 使用 8 位优化器
from bitsandbytes.optim import AdamW8bit
training_args = TrainingArguments(
    optim="paged_adamw_8bit",
)
```

## 常见模式

### 模式 1：多任务适配器

```python
# 训练多个任务特定的适配器
tasks = ["翻译", "摘要", "问答"]

for task in tasks:
    print(f"训练任务：{task}")

    # 重新加载基础模型
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model = get_peft_model(model, lora_config)

    # 训练任务特定数据
    task_dataset = load_dataset_for_task(task)
    trainer = Trainer(model=model, train_dataset=task_dataset, ...)
    trainer.train()

    # 保存适配器
    model.save_pretrained(f"adapters/{task}")
```

### 模式 2：切换适配器

```python
from peft import PeftModel

# 加载基础模型
base_model = AutoModelForCausalLM.from_pretrained(model_name)

# 加载特定适配器
model = PeftModel.from_pretrained(base_model, "adapters/translation")

# 用于翻译
output = model.generate(**inputs)

# 切换到另一个适配器
model.load_adapter("adapters/summarization", adapter_name="summarization")
model.set_adapter("summarization")

# 用于摘要
output = model.generate(**inputs)
```

### 模式 3：组合适配器

```python
# 加载多个适配器
model = PeftModel.from_pretrained(base_model, "adapters/style")
model.load_adapter("adapters/domain", adapter_name="domain")

# 组合使用
model.set_adapter(["style", "domain"])

# 带权重组合
from peft import get_peft_model_state_dict
# 可以手动混合适配器权重
```

### 模式 4：合并适配器

```python
# 合并 LoRA 权重到基础模型
model = PeftModel.from_pretrained(base_model, "lora-adapter")

# 合并（用于部署）
merged_model = model.merge_and_unload()

# 保存完整模型
merged_model.save_pretrained("merged-model")
tokenizer.save_pretrained("merged-model")
```

## 与训练框架集成

### 带 HuggingFace Trainer

```python
from transformers import TrainingArguments, Trainer
from peft import PeftModel

training_args = TrainingArguments(
    output_dir="./output",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    fp16=True,
    logging_steps=10,
    save_steps=100,
)

trainer = Trainer(
    model=model,              # PEFT 模型
    args=training_args,
    train_dataset=dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer
)

# 训练
trainer.train()

# 评估
trainer.evaluate()
```

### 带 PyTorch Lightning

```python
import pytorch_lightning as pl

class PEFTModel(pl.LightningModule):
    def __init__(self, base_model, lora_config):
        super().__init__()
        self.model = get_peft_model(base_model, lora_config)

    def training_step(self, batch):
        outputs = self.model(**batch)
        return outputs.loss

    def configure_optimizers(self):
        return torch.optim.AdamW(self.parameters(), lr=2e-4)

# 训练
model = PEFTModel(base_model, lora_config)
trainer = pl.Trainer(max_epochs=3, accelerator="gpu")
trainer.fit(model, train_dataloader)
```

## 任务特定配置

### 对话模型

```python
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
)
```

### 文本分类

```python
from peft import LoraConfig, TaskType

lora_config = LoraConfig(
    task_type=TaskType.SEQ_CLS,  # 序列分类
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
)
```

### 令牌分类

```python
lora_config = LoraConfig(
    task_type=TaskType.TOKEN_CLS,  # 令牌分类（NER）
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
)
```

### 特征提取

```python
from peft import PromptTuningConfig

prompt_config = PromptTuningConfig(
    task_type=TaskType.CAUSAL_LM,
    num_virtual_tokens=20,      # 虚拟提示词令牌数
    prompt_tuning_init="TEXT",  # 或 "RANDOM"
    prompt_tuning_init_text="总结以下文本：",
)
```

## 最佳实践

### 1. 从小开始

```python
# 先用小秩测试
lora_config = LoraConfig(r=8, lora_alpha=16)

# 如果需要更多容量，增加
lora_config = LoraConfig(r=16, lora_alpha=32)
```

### 2. 目标正确模块

```python
# ✅ 好：注意力 + FFN
target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"]

# ❌ 坏：仅注意力（有限容量）
target_modules=["q_proj", "v_proj"]
```

### 3. 适当的学习率

```python
# LoRA 需要比全参数更高的学习率
# 全参数：1e-5 到 5e-5
# LoRA：1e-4 到 5e-4
learning_rate = 2e-4  # 推荐用于 LoRA
```

### 4. 保存和加载

```python
# 保存仅适配器权重（小）
model.save_pretrained("adapter")  # ~10-100MB

# 加载适配器
model = PeftModel.from_pretrained(base_model, "adapter")

# 保存完整模型（大）
merged = model.merge_and_unload()
merged.save_pretrained("full-model")  # ~GB
```

## 故障排除

### 内存不足

```python
# 使用 QLoRA
bnb_config = BitsAndBytesConfig(load_in_4bit=True)

# 减少秩
lora_config = LoraConfig(r=8, lora_alpha=16)

# 梯度检查点
model.gradient_checkpointing_enable()
```

### 训练不稳定

```python
# 降低学习率
learning_rate = 1e-4  # 从 2e-4 降低

# 增加丢弃率
lora_dropout = 0.1  # 从 0.05 增加

# 使用梯度裁剪
training_args = TrainingArguments(max_grad_norm=1.0)
```

### 质量差

```python
# 增加秩
lora_config = LoraConfig(r=32, lora_alpha=64)

# 目标更多模块
target_modules = "all-linear"

# 增加数据或训练轮数
num_train_epochs = 5
```

## 资源

- **文档**：https://huggingface.co/docs/peft
- **GitHub**：https://github.com/huggingface/peft（14k+ stars）
- **示例**：https://github.com/huggingface/peft/tree/main/examples
- **论文**："LoRA: Low-Rank Adaptation of Large Language Models"

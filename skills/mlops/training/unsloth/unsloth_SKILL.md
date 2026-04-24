---
name: unsloth
description: 2 倍更快的训练和 60% 更少的内存使用，用于微调 LLM。通过自定义 Triton 内核和高效内存管理优化微调。带集成推理的 LoRA、QLoRA、全参数微调。当需要加速微调时使用。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [unsloth, transformers>=4.46.0, trl>=0.11.0, peft>=0.13.0, bitsandbytes>=0.44.0, xformers>=0.0.27]
metadata:
  hermes:
    tags: [Optimization, Unsloth, Faster Training, Memory Efficient, Triton, Fine-Tuning, LoRA, QLoRA]

---

# Unsloth - 2 倍更快的微调

## 快速开始

Unsloth 通过优化的 Triton 内核和高效内存管理，使微调速度提高 2 倍，内存使用减少 60%。

**安装**：
```bash
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps xformers trl peft accelerate bitsandbytes
```

**5 分钟设置**：
```python
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# 1. 加载模型（自动优化）
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

# 2. 添加 LoRA 适配器
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

# 3. 训练
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=load_dataset("yahma/alpaca-cleaned", split="train"),
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        output_dir="outputs",
    ),
)
trainer.train()

# 4. 保存
model.save_pretrained("lora_model")
```

## 何时使用与替代方案对比

**当以下情况使用 Unsloth：**
- 微调需要 2 倍速度提升
- GPU 内存有限但需要更大的批量大小
- 单 GPU 上本地/Colab 训练
- 快速实验不同的超参数
- 想将 LoRA 适配器合并到 GGUF

**改用替代方案：**
- **Axolotl**：需要 YAML 配置训练
- **PyTorch FSDP**：需要多 GPU 分布式训练
- **vLLM**：需要高吞吐推理服务
- **TRL**：需要 RLHF/DPO 训练（Unsloth 支持基础，但 TRL 更完整）

## 支持的模型

| 模型 | 大小 | 4 位内存 | 推荐用途 |
|--------|-------|---------|----------|
| **Llama-3** | 8B | ~6GB | 对话，指令跟随 |
| **Mistral** | 7B | ~5GB | 通用，代码 |
| **Gemma** | 7B | ~5GB | 推理，数学 |
| **Phi-3** | 3.8B | ~3GB | 边缘，快速原型 |
| **Qwen2** | 7B | ~5GB | 多语言，代码 |
| **Llama-3.1** | 8B | ~6GB | 最新，长上下文 |

**查找更多**：https://huggingface.co/unsloth

## 核心优化

### 1. 自定义 Triton 内核

- 针对特定硬件（A100、V100、Colab T4）自动选择
- 自动检测并在可用时使用 Flash Attention
- 针对常见模型架构的手动优化

### 2. 高效内存管理

- 智能梯度检查点
- 激活卸载到 CPU（当 GPU 内存不足时）
- 量化感知的训练管道

### 3. 集成推理

- 训练后带 LoRA 的直接推理
- 合并到 GGUF 用于 llama.cpp 部署
- 支持 vLLM 高吞吐服务

## 常见工作流

### 工作流 1：对话微调

```
训练进度：
- [ ] 步骤 1：选择模型和量化
- [ ] 步骤 2：准备对话数据集
- [ ] 步骤 3：配置和运行训练
- [ ] 步骤 4：合并和测试
```

**步骤 1：选择模型**
```python
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",  # 4 位量化
    max_seq_length=4096,                        # 长对话
    load_in_4bit=True,
    dtype=None,                                 # 自动检测
)
```

**步骤 2：数据集**
```python
# 聊天格式数据集
dataset = load_dataset("mlabonne/FineTome-100k", split="train")

# 或自定义数据
from datasets import Dataset
data = {
    "text": [
        "### 用户：你好！\n### 助手：你好！我能如何帮助你？",
        "### 用户：解释 Python。\n### 助手：Python 是一种编程语言..."
    ]
}
dataset = Dataset.from_dict(data)
```

**步骤 3：训练**
```python
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth",
)

trainer = SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=4096,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        max_steps=100,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        output_dir="outputs",
    ),
)
trainer.train()
```

**步骤 4：推理**
```python
FastLanguageModel.for_inference(model)  # 启用 2 倍更快的推理

inputs = tokenizer("### 用户：法国的首都是什么？\n### 助手：", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=128)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### 工作流 2：带合并的 QLoRA 训练

将量化训练的 LoRA 合并到 GGUF：

```python
# 训练后，合并并导出
from unsloth import save_merged_model

# 合并到 HuggingFace 格式
merged_model = model.merge_and_unload()
merged_model.save_pretrained("merged_model")

# 或转换为 GGUF（用于 llama.cpp）
model.save_pretrained_gguf(
    "model_gguf",
    tokenizer,
    quantization_method="q4_k_m"  # 推荐量化
)
```

### 工作流 3：带多 GPU 的训练

```python
# Unsloth 支持简单的多 GPU
import torch
if torch.cuda.device_count() > 1:
    # 使用所有可用 GPU
    model = FastLanguageModel.from_pretrained(
        model_name="unsloth/llama-3-8b-bnb-4bit",
        max_seq_length=2048,
        load_in_4bit=True,
        device_map="auto",  # 自动跨 GPU 分布
    )
```

## 常见问题

**CUDA 内存不足：**
- 减少 `per_device_train_batch_size`
- 增加 `gradient_accumulation_steps`
- 使用 `load_in_4bit=True` 加载模型
- 启用 `use_gradient_checkpointing="unsloth"`

**训练比预期慢：**
- 检查 Flash Attention 是否可用（需要 Ampere+ GPU）
- 使用 `unsloth` 梯度检查点而不是标准
- 验证 Triton 内核正确安装

**质量差：**
- 增加 LoRA 秩（`r=32` 或 `r=64`）
- 增加训练步数
- 使用更高质量的数据集
- 调整学习率（2e-4 是良好的起点）

## 高级主题

**自定义 Triton 内核**：Unsloth 自动为你的硬件选择最佳内核。不需要手动配置。

**内存分析**：使用 `torch.cuda.memory_summary()` 监控内存使用。Unsloth 在相同内存下通常比标准 transformers 多 60% 的批量大小。

**推理优化**：`FastLanguageModel.for_inference(model)` 启用推理时优化（禁用训练特定组件，使用更快的注意力模式）。

## 硬件要求

- **GPU**：NVIDIA（CUDA 12.1+）或 AMD（ROCm 5.7+）
- **VRAM**（4 位量化）：
  - 7B 模型：~5-6GB
  - 13B 模型：~10GB
  - 70B 模型：~40GB
- **RAM**：16GB+ 推荐
- **存储**：模型大小 + 训练输出

## 资源

- 官方文档：https://docs.unsloth.ai/
- GitHub：https://github.com/unslothai/unsloth
- 模型：https://huggingface.co/unsloth
- Discord：https://discord.gg/unsloth

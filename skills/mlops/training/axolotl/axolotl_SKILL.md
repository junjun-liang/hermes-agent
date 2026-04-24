---
name: axolotl
description: 使用 YAML 配置微调 LLM。当需要带最少代码的声明式训练配置、多 GPU 训练（FSDP/Deepspeed）、LoRA/QLoRA 微调或全参数微调时使用。Axolotl 构建在 HuggingFace transformers 之上。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [axolotl, transformers>=4.45.0, peft>=0.13.0, torch>=2.0.0, accelerate>=1.0.0, bitsandbytes>=0.43.0]
metadata:
  hermes:
    tags: [Fine-Tuning, Axolotl, YAML Config, Multi-GPU, FSDP, Deepspeed, LoRA, QLoRA, SFT, HuggingFace]

---

# Axolotl - 声明式 LLM 微调

## 何时使用 Axolotl

**当以下情况时使用 Axolotl：**
- 需要带最少代码的声明式训练配置
- 多 GPU 训练（FSDP/Deepspeed）
- LoRA/QLoRA 微调
- 全参数微调
- 快速原型训练配置
- 构建在 HuggingFace transformers 之上

**关键特性：**
- **YAML 配置**：所有训练设置声明式定义
- **多方法支持**：LoRA、QLoRA、全参数、GPTQ、AWQ
- **多 GPU**：FSDP、Deepspeed ZeRO 集成
- **数据集格式**：Alpaca、ShareGPT、Completion
- **模型支持**：Llama、Mistral、Qwen、Phi、Gemma 等

**当以下情况改用替代方案：**
- **TRL**：需要编程式训练循环
- **Unsloth**：需要 2-5 倍更快的训练速度
- **PyTorch FSDP**：需要细粒度分布式训练控制

## 快速开始

### 安装

```bash
# 从源代码
git clone https://github.com/OpenAccess-AI-Collective/axolotl
cd axolotl
pip install -e '.[flash-attn,deepspeed]'
```

### 基本训练

```yaml
# config.yaml
base_model: meta-llama/Llama-3.1-8B
model_type: LlamaForCausalLM
tokenizer_type: AutoTokenizer

load_in_8bit: false
load_in_4bit: true  # QLoRA
strict: false

datasets:
  - path: alpaca.json
    type: alpaca

dataset_prepared_path: last_run_prepared
val_set_size: 0.05
output_dir: ./outputs/lora-out

sequence_len: 4096
sample_packing: true
eval_sample_packing: true
pad_to_sequence_len: true

adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj
lora_target_linear: true

gradient_accumulation_steps: 4
micro_batch_size: 2
num_epochs: 3
optimizer: paged_adamw_8bit
lr_scheduler: cosine
learning_rate: 2e-4

train_on_inputs: false
group_by_length: false
bf16: true
fp16: false
tf32: false

gradient_checkpointing: true
gradient_checkpointing_kwargs:
  use_reentrant: false
early_stopping_patience: 5
logging_steps: 1
save_steps: 200
save_total_limit: 3
warmup_steps: 10
max_grad_norm: 1.0
```

运行训练：
```bash
accelerate launch -m axolotl.cli.train config.yaml
```

### 多 GPU 训练

```bash
# 单节点，多 GPU
accelerate launch --num_processes=4 -m axolotl.cli.train config.yaml

# 多节点，8 GPU
accelerate launch --num_processes=8 --num_machines=2 -m axolotl.cli.train config.yaml
```

## 数据集格式

### Alpaca 格式

```json
[
  {
    "instruction": "法国的首都是什么？",
    "input": "",
    "output": "法国的首都是巴黎。"
  },
  {
    "instruction": "将以下句子翻译成西班牙语。",
    "input": "你好，世界！",
    "output": "¡Hola, mundo!"
  }
]
```

### ShareGPT 格式

```json
[
  {
    "conversations": [
      {"from": "human", "value": "解释量子计算"},
      {"from": "gpt", "value": "量子计算利用量子力学原理..."}
    ]
  }
]
```

### Completion 格式

```json
[
  {"text": "法国的首都是巴黎。它也是该国最大的城市。"},
  {"text": "Python 是一种高级编程语言。"}
]
```

## LoRA 配置

### 基本 LoRA

```yaml
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_linear: true
```

### QLoRA（4 位量化）

```yaml
load_in_4bit: true
bits: 4
adapter: lora
lora_r: 32
lora_alpha: 64
lora_dropout: 0.05
lora_target_linear: true
```

### 全参数微调

```yaml
adapter: null
load_in_8bit: false
load_in_4bit: false

# FSDP 用于全参数训练
fsdp:
  - full_shard
  - auto_wrap
fsdp_config:
  fsdp_offload_params: true
  fsdp_sharding_strategy: FULL_SHARD
  fsdp_transformer_layer_cls_to_wrap: LlamaDecoderLayer
```

## 多 GPU 策略

### FSDP

```yaml
fsdp:
  - full_shard
  - auto_wrap
fsdp_config:
  fsdp_offload_params: true
  fsdp_state_dict_type: FULL_STATE_DICT
  fsdp_transformer_layer_cls_to_wrap: LlamaDecoderLayer
```

### Deepspeed ZeRO

```yaml
deepspeed: path/to/deepspeed_config.json
```

```json
{
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": {"device": "cpu", "pin_memory": true},
    "offload_param": {"device": "cpu", "pin_memory": true},
    "overlap_comm": true,
    "contiguous_gradients": true
  },
  "fp16": {"enabled": false},
  "bf16": {"enabled": true},
  "gradient_accumulation_steps": 4
}
```

## 常见模式

### 模式 1：指令微调

```yaml
base_model: meta-llama/Llama-3.1-8B
datasets:
  - path: instructions.jsonl
    type: alpaca

sequence_len: 2048
adapter: lora
lora_r: 16
lora_alpha: 32
num_epochs: 3
```

### 模式 2：对话微调

```yaml
base_model: mistralai/Mistral-7B-v0.1
datasets:
  - path: conversations.json
    type: sharegpt

sequence_len: 4096
sample_packing: true
adapter: lora
lora_r: 32
```

### 模式 3：带评估的训练

```yaml
datasets:
  - path: train.json
    type: alpaca

val_set_size: 0.1  # 10% 用于评估
output_dir: ./outputs/
save_steps: 500
eval_steps: 500
```

## 推理

### 加载微调模型

```python
from axolotl.utils.chat_templates import get_chat_template
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# 加载基础模型
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B")

# 加载 LoRA 适配器
model = PeftModel.from_pretrained(base_model, "./outputs/lora-out")

# 合并用于部署
merged = model.merge_and_unload()
merged.save_pretrained("./merged-model")
```

### 使用 Axolotl CLI 推理

```bash
# 运行交互式聊天
accelerate launch -m axolotl.cli.inference config.yaml --lora_model_dir=./outputs/lora-out

# 从文件生成
accelerate launch -m axolotl.cli.inference config.yaml --lora_model_dir=./outputs/lora-out --gradio
```

## 硬件要求

### LoRA/QLoRA

| 模型大小 | GPU 内存 | GPU 数量 |
|----------|---------|----------|
| 7B（QLoRA） | 6GB | 1 |
| 13B（QLoRA） | 12GB | 1 |
| 70B（QLoRA） | 48GB | 2-4 |

### 全参数

| 模型大小 | GPU 内存 | GPU 数量 |
|----------|---------|----------|
| 7B（FSDP） | 40GB | 4 |
| 13B（FSDP） | 80GB | 4-8 |
| 70B（FSDP） | 80GB | 8-16 |

## 常见问题

**内存不足错误：**
- 减少 `micro_batch_size`
- 增加 `gradient_accumulation_steps`
- 使用 `load_in_4bit: true`
- 启用 `gradient_checkpointing: true`

**训练不稳定：**
- 降低 `learning_rate`
- 增加 `warmup_steps`
- 检查数据集质量

## 资源

- **GitHub**：https://github.com/OpenAccess-AI-Collective/axolotl
- **文档**：https://axolotl-ai-cloud.github.io/axolotl/
- **Discord**：https://discord.gg/axolotl-ai

---
name: pytorch-fsdp
description: 使用 FSDP（完全分片数据并行）跨多 GPU 训练大型模型。用于分布式训练、训练 7B+ 参数的模型、高效利用多 GPU 集群，或全参数微调而内存不足。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [torch>=2.0.0, transformers>=4.40.0, accelerate>=0.30.0]
metadata:
  hermes:
    tags: [Distributed Training, FSDP, Multi-GPU, PyTorch, Large Models, Data Parallel, Sharding]

---

# PyTorch FSDP - 完全分片数据并行

## 何时使用 FSDP

**当以下情况时使用 FSDP：**
- 跨多个 GPU 分布式训练大型模型
- 训练 7B+ 参数的模型
- 高效利用多 GPU 集群
- 全参数微调而内存不足
- 比 DeepSpeed ZeRO 更简单的设置

**关键特性：**
- **分片策略**：跨 GPU 分片模型参数、梯度和优化器状态
- **内存效率**：每个 GPU 仅持有模型的一部分
- **自动通信**：内置 all-gather 和 reduce-scatter
- **与 HuggingFace 集成**：与 Transformers 库集成

**当以下情况改用替代方案：**
- **单 GPU 训练**：使用标准 PyTorch
- **带复杂策略的分布式**：使用 DeepSpeed ZeRO
- **模型并行**：使用 Tensor Parallelism

## 快速开始

### 基本 FSDP 设置

```python
import torch
import torch.distributed as dist
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import MixedPrecision, ShardingStrategy
from torch.distributed.fsdp.wrap import size_based_auto_wrap_policy

# 初始化进程组
def setup():
    dist.init_process_group(backend="nccl")
    torch.cuda.set_device(dist.get_rank())

def cleanup():
    dist.destroy_process_group()

# 创建模型
model = MyLargeModel()

# FSDP 配置
fsdp_config = dict(
    sharding_strategy=ShardingStrategy.FULL_SHARD,  # ZeRO-3 等效
    mixed_precision=MixedPrecision(
        param_dtype=torch.float16,
        reduce_dtype=torch.float16,
        buffer_dtype=torch.float16
    ),
    auto_wrap_policy=size_based_auto_wrap_policy,
    device_id=torch.cuda.current_device()
)

# 包装模型
model = FSDP(model, **fsdp_config)

# 训练循环
for batch in dataloader:
    optimizer.zero_grad()
    loss = model(batch)
    loss.backward()
    optimizer.step()
```

### 带 HuggingFace Trainer

```python
from transformers import Trainer, TrainingArguments
from transformers.trainer_utils import get_last_checkpoint

training_args = TrainingArguments(
    output_dir="./output",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    fp16=True,
    fsdp="full_shard auto_wrap",
    fsdp_config={
        "fsdp_transformer_layer_cls_to_wrap": "LlamaDecoderLayer",
        "fsdp_backward_prefetch": "BACKWARD_PRE",
        "fsdp_forward_prefetch": False,
        "fsdp_state_dict_type": "FULL_STATE_DICT",
        "fsdp_use_orig_params": True,
    },
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer
)

# 训练
trainer.train()
```

## 分片策略

### 可用策略

| 策略 | 分片内容 | 内存 | 通信 | 用途 |
|--------|---------|---------|---------|----------|
| **FULL_SHARD** | 参数、梯度、优化器 | 最低 | 最高 | **推荐默认** |
| **SHARD_GRAD_OP** | 梯度和优化器 | 中 | 中 | 平衡 |
| **NO_SHARD** | 无（DDP） | 最高 | 最低 | 仅数据并行 |
| **HYBRID_SHARD** | 节点内 FULL_SHARD | 低 | 中 | 多节点 |

### 选择策略

```python
from torch.distributed.fsdp import ShardingStrategy

# 单节点，多 GPU
strategy = ShardingStrategy.FULL_SHARD

# 多节点
strategy = ShardingStrategy.HYBRID_SHARD

# 内存充足，想要速度
strategy = ShardingStrategy.SHARD_GRAD_OP
```

## 内存优化

### 混合精度

```python
from torch.distributed.fsdp import MixedPrecision

# FP16 混合精度
mp = MixedPrecision(
    param_dtype=torch.float16,    # 参数存储
    reduce_dtype=torch.float16,   # 梯度归约
    buffer_dtype=torch.float16    # 缓冲区
)

# BF16 混合精度（更好精度，需要 Ampere+）
mp = MixedPrecision(
    param_dtype=torch.bfloat16,
    reduce_dtype=torch.bfloat16,
    buffer_dtype=torch.bfloat16
)
```

### 激活检查点

```python
from torch.distributed.algorithms._checkpoint.checkpoint_wrapper import (
    CheckpointWrapper,
    CheckpointImpl,
    apply_activation_checkpointing,
    checkpoint_wrapper,
)

# 包装特定层
def apply_fsdp_checkpointing(model):
    checkpoint_fn = checkpoint_wrapper
    apply_activation_checkpointing(
        model,
        checkpoint_wrapper_fn=checkpoint_fn,
        check_fn=lambda submodule: isinstance(submodule, TransformerLayer)
    )
```

## 多 GPU 训练

### 使用 torchrun

```bash
# 单节点，4 GPU
torchrun --nproc_per_node=4 train.py

# 多节点，8 GPU
torchrun --nnodes=2 --nproc_per_node=4 \
    --rdzv_endpoint=master_node:29500 \
    --rdzv_backend=c10d \
    train.py
```

### 启动脚本

```bash
#!/bin/bash
# run_fsdp.sh

NUM_GPUS=4

torchrun --nproc_per_node=$NUM_GPUS \
    --standalone \
    train.py \
    --batch_size 4 \
    --epochs 3 \
    --lr 1e-5
```

## 常见模式

### 模式 1：带自定义包装策略

```python
from torch.distributed.fsdp.wrap import (
    size_based_auto_wrap_policy,
    transformer_auto_wrap_policy,
)

# 按大小自动包装
policy = size_based_auto_wrap_policy(min_num_params=100_000_000)

# 按类型自动包装
policy = transformer_auto_wrap_policy(
    transformer_layer_cls={LlamaDecoderLayer, TransformerBlock}
)

# 自定义策略
def custom_auto_wrap_policy(module, recurse, nonwrapped_numel):
    return isinstance(module, (LlamaDecoderLayer, Linear))

model = FSDP(model, auto_wrap_policy=custom_auto_wrap_policy)
```

### 模式 2：保存和加载检查点

```python
import torch
from torch.distributed.fsdp import FullStateDictConfig
from torch.distributed.fsdp import StateDictType

# 保存检查点
def save_checkpoint(model, optimizer, path):
    save_policy = FullStateDictConfig(offload_to_cpu=True, rank0_only=True)
    with FSDP.state_dict_type(model, StateDictType.FULL_STATE_DICT, save_policy):
        cpu_state = model.state_dict()
        if dist.get_rank() == 0:
            torch.save(cpu_state, path)

# 加载检查点
def load_checkpoint(model, path):
    model.load_state_dict(torch.load(path))
```

### 模式 3：梯度裁剪

```python
from torch.nn.utils import clip_grad_norm_

for batch in dataloader:
    optimizer.zero_grad()
    loss = model(batch)
    loss.backward()

    # 裁剪梯度
    grad_norm = clip_grad_norm_(model.parameters(), max_norm=1.0)

    optimizer.step()
```

## 性能优化

### Prefetch 策略

```python
from torch.distributed.fsdp import BackwardPrefetch

# 向后预取（推荐）
fsdp_config["backward_prefetch"] = BackwardPrefetch.BACKWARD_PRE

# 向前预取
fsdp_config["forward_prefetch"] = True
```

### CPU 卸载

```python
from torch.distributed.fsdp import CPUOffload

# 卸载优化器状态到 CPU
fsdp_config["cpu_offload"] = CPUOffload(offload_params=True)
```

## 与 HuggingFace 集成

### 完整配置

```python
training_args = TrainingArguments(
    output_dir="./output",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    num_train_epochs=3,
    learning_rate=2e-5,
    fp16=True,
    optim="adamw_torch",

    # FSDP 配置
    fsdp="full_shard auto_wrap",
    fsdp_config={
        "fsdp_transformer_layer_cls_to_wrap": "LlamaDecoderLayer",
        "fsdp_backward_prefetch": "BACKWARD_PRE",
        "fsdp_forward_prefetch": True,
        "fsdp_state_dict_type": "FULL_STATE_DICT",
        "fsdp_use_orig_params": True,
        "fsdp_cpu_ram_efficient_loading": True,
    },

    # 日志
    logging_steps=10,
    save_steps=500,
    save_total_limit=3,
)
```

## 硬件要求

### VRAM 要求（全参数微调）

| 模型大小 | GPU 数量 | VRAM/GPU | 策略 |
|----------|---------|----------|---------|
| 7B | 4 | 40GB | FULL_SHARD |
| 13B | 8 | 40GB | FULL_SHARD |
| 30B | 8 | 80GB | FULL_SHARD |
| 70B | 16 | 80GB | HYBRID_SHARD |

## 故障排除

### 内存不足

```python
# 减少批量大小
per_device_train_batch_size = 1

# 增加梯度累积
gradient_accumulation_steps = 16

# 启用激活检查点
apply_activation_checkpointing(model)

# 使用 CPU 卸载
fsdp_config["cpu_offload"] = CPUOffload(offload_params=True)
```

### 通信瓶颈

```python
# 减少 all-gather 频率
fsdp_config["backward_prefetch"] = BackwardPrefetch.BACKWARD_POST

# 使用 HYBRID_SHARD 用于多节点
fsdp_config["sharding_strategy"] = ShardingStrategy.HYBRID_SHARD
```

### 训练速度慢

```python
# 启用向前预取
fsdp_config["forward_prefetch"] = True

# 使用混合精度
fsdp_config["mixed_precision"] = MixedPrecision(...)

# 增加批量大小
per_device_train_batch_size = 4
```

## 资源

- **PyTorch 文档**：https://pytorch.org/docs/stable/fsdp.html
- **教程**：https://pytorch.org/tutorials/intermediate/FSDP_tutorial.html
- **示例**：https://github.com/pytorch/examples/tree/main/fsdp

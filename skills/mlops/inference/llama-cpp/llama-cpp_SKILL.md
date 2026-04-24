---
name: llama-cpp
description: 在 CPU、Apple Silicon 和消费级 GPU 上运行 LLM 推理，无需 NVIDIA 硬件。用于边缘部署、M1/M2/M3 Mac、AMD/Intel GPU，或 CUDA 不可用时。支持 GGUF 量化（1.5-8 位），减少内存，比 CPU 上的 PyTorch 快 4-10 倍。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [llama-cpp-python]
metadata:
  hermes:
    tags: [Inference Serving, Llama.cpp, CPU Inference, Apple Silicon, Edge Deployment, GGUF, Quantization, Non-NVIDIA, AMD GPUs, Intel GPUs, Embedded]

---

# llama.cpp

纯 C/C++ LLM 推理，依赖最少，针对 CPU 和非 NVIDIA 硬件优化。

## 何时使用 llama.cpp

**当以下情况时使用 llama.cpp：**
- 在仅 CPU 的机器上运行
- 在 Apple Silicon（M1/M2/M3/M4）上部署
- 使用 AMD 或 Intel GPU（无 CUDA）
- 边缘部署（树莓派、嵌入式系统）
- 需要简单部署，无需 Docker/Python

**当以下情况时改用 TensorRT-LLM：**
- 有 NVIDIA GPU（A100/H100）
- 需要最大吞吐量（100K+ tok/s）
- 在带 CUDA 的数据中心运行

**当以下情况时改用 vLLM：**
- 有 NVIDIA GPU
- 需要 Python 优先 API
- 想要 PagedAttention

## 快速开始

### 安装

```bash
# macOS/Linux
brew install llama.cpp

# 或从源代码构建
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# 带 Metal（Apple Silicon）
make LLAMA_METAL=1

# 带 CUDA（NVIDIA）
make LLAMA_CUDA=1

# 带 ROCm（AMD）
make LLAMA_HIP=1
```

### 下载模型

```bash
# 从 HuggingFace 下载（GGUF 格式）
huggingface-cli download \
    TheBloke/Llama-2-7B-Chat-GGUF \
    llama-2-7b-chat.Q4_K_M.gguf \
    --local-dir models/

# 或从 HuggingFace 转换
python convert_hf_to_gguf.py models/llama-2-7b-chat/
```

### 运行推理

```bash
# 简单对话
./llama-cli \
    -m models/llama-2-7b-chat.Q4_K_M.gguf \
    -p "解释量子计算" \
    -n 256  # 最大 token

# 交互对话
./llama-cli \
    -m models/llama-2-7b-chat.Q4_K_M.gguf \
    --interactive
```

### 服务器模式

```bash
# 启动 OpenAI 兼容服务器
./llama-server \
    -m models/llama-2-7b-chat.Q4_K_M.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    -ngl 32  # 卸载 32 层到 GPU

# 客户端请求
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-2-7b-chat",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

## 量化格式

### GGUF 格式概述

| 格式 | 位 | 大小（7B） | 速度 | 质量 | 用例 |
|--------|------|-----------|-------|---------|----------|
| **Q4_K_M** | 4.5 | 4.1 GB | 快 | 好 | **推荐默认** |
| Q4_K_S | 4.3 | 3.9 GB | 更快 | 较低 | 速度关键 |
| Q5_K_M | 5.5 | 4.8 GB | 中 | 更好 | 质量关键 |
| Q6_K | 6.5 | 5.5 GB | 较慢 | 最佳 | 最大质量 |
| Q8_0 | 8.0 | 7.0 GB | 慢 | 优秀 | 最小降级 |
| Q2_K | 2.5 | 2.7 GB | 最快 | 差 | 仅测试 |

### 选择量化

```bash
# 通用（平衡）
Q4_K_M  # 4 位，中等质量

# 最大速度（更多降级）
Q2_K 或 Q3_K_M

# 最大质量（较慢）
Q6_K 或 Q8_0

# 超大型模型（70B, 405B）
Q3_K_M 或 Q4_K_S  # 更低位以适应内存
```

## 硬件加速

### Apple Silicon（Metal）

```bash
# 使用 Metal 构建
make LLAMA_METAL=1

# 使用 GPU 加速运行（自动）
./llama-cli -m model.gguf -ngl 999  # 卸载所有层

# 性能：M3 Max 40-60 token/秒（Llama 2-7B Q4_K_M）
```

### NVIDIA GPU（CUDA）

```bash
# 使用 CUDA 构建
make LLAMA_CUDA=1

# 卸载层到 GPU
./llama-cli -m model.gguf -ngl 35  # 卸载 35/40 层

# 大型模型的混合 CPU+GPU
./llama-cli -m llama-70b.Q4_K_M.gguf -ngl 20  # GPU: 20 层, CPU: 其余
```

### AMD GPU（ROCm）

```bash
# 使用 ROCm 构建
make LLAMA_HIP=1

# 使用 AMD GPU 运行
./llama-cli -m model.gguf -ngl 999
```

## 常见模式

### 批处理

```bash
# 从文件处理多个提示
cat prompts.txt | ./llama-cli \
    -m model.gguf \
    --batch-size 512 \
    -n 100
```

### 约束生成

```bash
# 带语法的 JSON 输出
./llama-cli \
    -m model.gguf \
    -p "Generate a person: " \
    --grammar-file grammars/json.gbnf

# 仅输出有效 JSON
```

### 上下文大小

```bash
# 增加上下文（默认 512）
./llama-cli \
    -m model.gguf \
    -c 4096  # 4K 上下文窗口

# 超长上下文（如果模型支持）
./llama-cli -m model.gguf -c 32768  # 32K 上下文
```

## 性能基准

### CPU 性能（Llama 2-7B Q4_K_M）

| CPU | 线程 | 速度 | 成本 |
|-----|---------|-------|------|
| Apple M3 Max | 16 | 50 tok/s | $0（本地） |
| AMD Ryzen 9 7950X | 32 | 35 tok/s | $0.50/小时 |
| Intel i9-13900K | 32 | 30 tok/s | $0.40/小时 |
| AWS c7i.16xlarge | 64 | 40 tok/s | $2.88/小时 |

### GPU 加速（Llama 2-7B Q4_K_M）

| GPU | 速度 | 对比 CPU | 成本 |
|-----|-------|--------|------|
| NVIDIA RTX 4090 | 120 tok/s | 3-4 倍 | $0（本地） |
| NVIDIA A10 | 80 tok/s | 2-3 倍 | $1.00/小时 |
| AMD MI250 | 70 tok/s | 2 倍 | $2.00/小时 |
| Apple M3 Max（Metal） | 50 tok/s | 约相同 | $0（本地） |

## 支持的模型

**LLaMA 家族**：
- Llama 2（7B, 13B, 70B）
- Llama 3（8B, 70B, 405B）
- Code Llama

**Mistral 家族**：
- Mistral 7B
- Mixtral 8x7B, 8x22B

**其他**：
- Falcon, BLOOM, GPT-J
- Phi-3, Gemma, Qwen
- LLaVA（视觉）, Whisper（音频）

**查找模型**：https://huggingface.co/models?library=gguf

## 参考

- **[量化指南](references/quantization.md)** — GGUF 格式、转换、质量比较
- **[服务器部署](references/server.md)** — API 端点、Docker、监控
- **[优化](references/optimization.md)** — 性能调优、混合 CPU+GPU

## 资源

- **GitHub**：https://github.com/ggerganov/llama.cpp
- **模型**：https://huggingface.co/models?library=gguf
- **Discord**：https://discord.gg/llama-cpp

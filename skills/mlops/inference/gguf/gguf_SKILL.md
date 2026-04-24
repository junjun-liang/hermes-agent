---
name: gguf-quantization
description: GGUF 格式和 llama.cpp 量化，用于高效的 CPU/GPU 推理。用于在消费级硬件、Apple Silicon 上部署模型，或需要灵活的 2-8 位量化而无需 GPU。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [llama-cpp-python>=0.2.0]
metadata:
  hermes:
    tags: [GGUF, Quantization, llama.cpp, CPU Inference, Apple Silicon, Model Compression, Optimization]

---

# GGUF - llama.cpp 的量化格式

GGUF（GPT 生成的统一格式）是 llama.cpp 的标准文件格式，支持在 CPU、Apple Silicon 和 GPU 上进行高效推理，并提供灵活的量化选项。

## 何时使用 GGUF

**当以下情况时使用 GGUF：**
- 在消费级硬件上部署（笔记本电脑、台式机）
- 在 Apple Silicon（M1/M2/M3）上使用 Metal 加速运行
- 需要无需 GPU 的 CPU 推理
- 需要灵活的量化（Q2_K 到 Q8_0）
- 使用本地 AI 工具（LM Studio、Ollama、text-generation-webui）

**关键优势：**
- **通用硬件**：支持 CPU、Apple Silicon、NVIDIA、AMD
- **无需 Python 运行时**：纯 C/C++ 推理
- **灵活的量化**：2-8 位，带多种方法（K-quants）
- **生态系统支持**：LM Studio、Ollama、koboldcpp 等
- **imatrix**：重要性矩阵，提高低位质量

**改用替代方案：**
- **AWQ/GPTQ**：NVIDIA GPU 上的最大精度，带校准
- **HQQ**：HuggingFace 的快速免校准量化
- **bitsandbytes**：与 transformers 库简单集成
- **TensorRT-LLM**：生产级 NVIDIA 部署，最大速度

## 快速开始

### 安装

```bash
# 克隆 llama.cpp
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# 构建（CPU）
make

# 带 CUDA 构建（NVIDIA）
make GGML_CUDA=1

# 带 Metal 构建（Apple Silicon）
make GGML_METAL=1

# 安装 Python 绑定（可选）
pip install llama-cpp-python
```

### 将模型转换为 GGUF

```bash
# 安装依赖
pip install -r requirements.txt

# 将 HuggingFace 模型转换为 GGUF（FP16）
python convert_hf_to_gguf.py ./path/to/model --outfile model-f16.gguf

# 或指定输出类型
python convert_hf_to_gguf.py ./path/to/model \
    --outfile model-f16.gguf \
    --outtype f16
```

### 量化模型

```bash
# 基本量化为 Q4_K_M
./llama-quantize model-f16.gguf model-q4_k_m.gguf Q4_K_M

# 使用重要性矩阵量化（更好的质量）
./llama-imatrix -m model-f16.gguf -f calibration.txt -o model.imatrix
./llama-quantize --imatrix model.imatrix model-f16.gguf model-q4_k_m.gguf Q4_K_M
```

### 运行推理

```bash
# CLI 推理
./llama-cli -m model-q4_k_m.gguf -p "Hello, how are you?"

# 交互模式
./llama-cli -m model-q4_k_m.gguf --interactive

# 带 GPU 卸载
./llama-cli -m model-q4_k_m.gguf -ngl 35 -p "Hello!"
```

## 量化类型

### K-quant 方法（推荐）

| 类型 | 位 | 大小（7B） | 质量 | 用例 |
|------|------|-----------|---------|----------|
| Q2_K | 2.5 | ~2.8 GB | 低 | 极致压缩 |
| Q3_K_S | 3.0 | ~3.0 GB | 低-中 | 内存受限 |
| Q3_K_M | 3.3 | ~3.3 GB | 中 | 平衡 |
| Q4_K_S | 4.0 | ~3.8 GB | 中-高 | 良好平衡 |
| Q4_K_M | 4.5 | ~4.1 GB | 高 | **推荐默认** |
| Q5_K_S | 5.0 | ~4.6 GB | 高 | 质量优先 |
| Q5_K_M | 5.5 | ~4.8 GB | 很高 | 高质量 |
| Q6_K | 6.0 | ~5.5 GB | 优秀 | 接近原始 |
| Q8_0 | 8.0 | ~7.2 GB | 最佳 | 最大质量 |

### 传统方法

| 类型 | 描述 |
|------|-------------|
| Q4_0 | 4 位，基本 |
| Q4_1 | 4 位，带增量 |
| Q5_0 | 5 位，基本 |
| Q5_1 | 5 位，带增量 |

**推荐**：使用 K-quant 方法（Q4_K_M、Q5_K_M）获得最佳质量/大小比。

## 转换工作流

### 工作流 1：HuggingFace 到 GGUF

```bash
# 1. 下载模型
huggingface-cli download meta-llama/Llama-3.1-8B --local-dir ./llama-3.1-8b

# 2. 转换为 GGUF（FP16）
python convert_hf_to_gguf.py ./llama-3.1-8b \
    --outfile llama-3.1-8b-f16.gguf \
    --outtype f16

# 3. 量化
./llama-quantize llama-3.1-8b-f16.gguf llama-3.1-8b-q4_k_m.gguf Q4_K_M

# 4. 测试
./llama-cli -m llama-3.1-8b-q4_k_m.gguf -p "Hello!" -n 50
```

### 工作流 2：使用重要性矩阵（更好的质量）

```bash
# 1. 转换为 GGUF
python convert_hf_to_gguf.py ./model --outfile model-f16.gguf

# 2. 创建校准文本（多样化样本）
cat > calibration.txt << 'EOF'
The quick brown fox jumps over the lazy dog.
Machine learning is a subset of artificial intelligence.
Python is a popular programming language.
# 添加更多多样化文本样本...
EOF

# 3. 生成重要性矩阵
./llama-imatrix -m model-f16.gguf \
    -f calibration.txt \
    --chunk 512 \
    -o model.imatrix \
    -ngl 35  # GPU 层（如果有）

# 4. 使用 imatrix 量化
./llama-quantize --imatrix model.imatrix \
    model-f16.gguf \
    model-q4_k_m.gguf \
    Q4_K_M
```

### 工作流 3：多种量化

```bash
#!/bin/bash
MODEL="llama-3.1-8b-f16.gguf"
IMATRIX="llama-3.1-8b.imatrix"

# 生成一次 imatrix
./llama-imatrix -m $MODEL -f wiki.txt -o $IMATRIX -ngl 35

# 创建多种量化
for QUANT in Q4_K_M Q5_K_M Q6_K Q8_0; do
    OUTPUT="llama-3.1-8b-${QUANT,,}.gguf"
    ./llama-quantize --imatrix $IMATRIX $MODEL $OUTPUT $QUANT
    echo "已创建: $OUTPUT ($(du -h $OUTPUT | cut -f1))"
done
```

## Python 使用

### llama-cpp-python

```python
from llama_cpp import Llama

# 加载模型
llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,          # 上下文窗口
    n_gpu_layers=35,     # GPU 卸载（0 表示仅 CPU）
    n_threads=8          # CPU 线程
)

# 生成
output = llm(
    "什么是机器学习？",
    max_tokens=256,
    temperature=0.7,
    stop=["</s>", "\n\n"]
)
print(output["choices"][0]["text"])
```

### 对话完成

```python
from llama_cpp import Llama

llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,
    chat_format="llama-3"  # 或 "chatml"、"mistral" 等
)

messages = [
    {"role": "system", "content": "你是一个有用的助手。"},
    {"role": "user", "content": "什么是 Python？"}
]

response = llm.create_chat_completion(
    messages=messages,
    max_tokens=256,
    temperature=0.7
)
print(response["choices"][0]["message"]["content"])
```

### 流式

```python
from llama_cpp import Llama

llm = Llama(model_path="./model-q4_k_m.gguf", n_gpu_layers=35)

# 流式输出 token
for chunk in llm(
    "解释量子计算：",
    max_tokens=256,
    stream=True
):
    print(chunk["choices"][0]["text"], end="", flush=True)
```

## 服务器模式

### 启动 OpenAI 兼容服务器

```bash
# 启动服务器
./llama-server -m model-q4_k_m.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    -ngl 35 \
    -c 4096

# 或使用 Python 绑定
python -m llama_cpp.server \
    --model model-q4_k_m.gguf \
    --n_gpu_layers 35 \
    --host 0.0.0.0 \
    --port 8080
```

### 与 OpenAI 客户端配合使用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="local-model",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=256
)
print(response.choices[0].message.content)
```

## 硬件优化

### Apple Silicon（Metal）

```bash
# 使用 Metal 构建
make clean && make GGML_METAL=1

# 使用 Metal 加速运行
./llama-cli -m model.gguf -ngl 99 -p "Hello"

# Python 使用 Metal
llm = Llama(
    model_path="model.gguf",
    n_gpu_layers=99,     # 卸载所有层
    n_threads=1          # Metal 处理并行
)
```

### NVIDIA CUDA

```bash
# 使用 CUDA 构建
make clean && make GGML_CUDA=1

# 使用 CUDA 运行
./llama-cli -m model.gguf -ngl 35 -p "Hello"

# 指定 GPU
CUDA_VISIBLE_DEVICES=0 ./llama-cli -m model.gguf -ngl 35
```

### CPU 优化

```bash
# 使用 AVX2/AVX512 构建
make clean && make

# 使用最佳线程数运行
./llama-cli -m model.gguf -t 8 -p "Hello"

# Python CPU 配置
llm = Llama(
    model_path="model.gguf",
    n_gpu_layers=0,      # 仅 CPU
    n_threads=8,         # 匹配物理核心
    n_batch=512          # 提示处理的批量大小
)
```

## 与工具集成

### Ollama

```bash
# 创建 Modelfile
cat > Modelfile << 'EOF'
FROM ./model-q4_k_m.gguf
TEMPLATE """{{ .System }}
{{ .Prompt }}"""
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF

# 创建 Ollama 模型
ollama create mymodel -f Modelfile

# 运行
ollama run mymodel "Hello!"
```

### LM Studio

1. 将 GGUF 文件放入 `~/.cache/lm-studio/models/`
2. 打开 LM Studio 并选择模型
3. 配置上下文长度和 GPU 卸载
4. 开始推理

### text-generation-webui

```bash
# 放入 models 文件夹
cp model-q4_k_m.gguf text-generation-webui/models/

# 使用 llama.cpp 加载器启动
python server.py --model model-q4_k_m.gguf --loader llama.cpp --n-gpu-layers 35
```

## 最佳实践

1. **使用 K-quants**：Q4_K_M 提供最佳质量/大小平衡
2. **使用 imatrix**：Q4 及以下始终使用重要性矩阵
3. **GPU 卸载**：卸载 VRAM 允许的尽可能多层
4. **上下文长度**：从 4096 开始，根据需要增加
5. **线程数**：匹配物理 CPU 核心，不是逻辑核心
6. **批量大小**：增加 n_batch 以加快提示处理

## 常见问题

**模型加载缓慢：**
```bash
# 使用 mmap 加快加载
./llama-cli -m model.gguf --mmap
```

**内存不足：**
```bash
# 减少 GPU 层
./llama-cli -m model.gguf -ngl 20  # 从 35 减少

# 或使用更小的量化
./llama-quantize model-f16.gguf model-q3_k_m.gguf Q3_K_M
```

**低位质量差：**
```bash
# Q4 及以下始终使用 imatrix
./llama-imatrix -m model-f16.gguf -f calibration.txt -o model.imatrix
./llama-quantize --imatrix model.imatrix model-f16.gguf model-q4_k_m.gguf Q4_K_M
```

## 参考

- **[高级用法](references/advanced-usage.md)** — 批处理、推测解码、自定义构建
- **[故障排除](references/troubleshooting.md)** — 常见问题、调试、基准

## 资源

- **仓库**：https://github.com/ggml-org/llama.cpp
- **Python 绑定**：https://github.com/abetlen/llama-cpp-python
- **预量化模型**：https://huggingface.co/TheBloke
- **GGUF 转换器**：https://huggingface.co/spaces/ggml-org/gguf-my-repo
- **许可证**：MIT

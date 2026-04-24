---
name: modal-serverless-gpu
description: 用于运行 ML 工作负载的无服务器 GPU 云平台。当你需要无需基础设施管理的按需 GPU 访问、将 ML 模型部署为 API 或带自动扩展的批处理作业时使用。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [modal>=0.64.0]
metadata:
  hermes:
    tags: [Infrastructure, Serverless, GPU, Cloud, Deployment, Modal]

---

# Modal 无服务器 GPU

在 Modal 无服务器 GPU 云平台上运行 ML 工作负载的综合指南。

## 何时使用 Modal

**使用 Modal 当：**
- 运行 GPU 密集型 ML 工作负载而无需管理基础设施
- 将 ML 模型部署为自动扩展 API
- 运行批处理作业（训练、推理、数据处理）
- 需要按秒计费的 GPU 定价，无闲置成本
- 快速原型化 ML 应用
- 运行定时作业（类 cron 工作负载）

**关键特性：**
- **无服务器 GPU**：T4、L4、A10G、L40S、A100、H100、H200、B200 按需
- **Python 原生**：在 Python 代码中定义基础设施，无需 YAML
- **自动扩展**：扩展到零，瞬间扩展到 100+ GPU
- **亚秒级冷启动**：基于 Rust 的基础设施，快速容器启动
- **容器缓存**：镜像层缓存，快速迭代
- **Web 端点**：将函数部署为零停机更新的 REST API

**改用替代方案：**
- **RunPod**：用于带持久状态的长时间运行的 pod
- **Lambda Labs**：用于预留 GPU 实例
- **SkyPilot**：用于多云编排和成本优化
- **Kubernetes**：用于复杂的多服务架构

## 快速开始

### 安装

```bash
pip install modal
modal setup  # 打开浏览器进行身份验证
```

### GPU Hello World

```python
import modal

app = modal.App("hello-gpu")

@app.function(gpu="T4")
def gpu_info():
    import subprocess
    return subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout

@app.local_entrypoint()
def main():
    print(gpu_info.remote())
```

运行：`modal run hello_gpu.py`

### 基本推理端点

```python
import modal

app = modal.App("text-generation")
image = modal.Image.debian_slim().pip_install("transformers", "torch", "accelerate")

@app.cls(gpu="A10G", image=image)
class TextGenerator:
    @modal.enter()
    def load_model(self):
        from transformers import pipeline
        self.pipe = pipeline("text-generation", model="gpt2", device=0)

    @modal.method()
    def generate(self, prompt: str) -> str:
        return self.pipe(prompt, max_length=100)[0]["generated_text"]

@app.local_entrypoint()
def main():
    print(TextGenerator().generate.remote("Hello, world"))
```

## 核心概念

### 关键组件

| 组件 | 用途 |
|-----------|---------|
| `App` | 函数和资源的容器 |
| `Function` | 带计算规范的无服务器函数 |
| `Cls` | 带生命周期钩子的基于类的函数 |
| `Image` | 容器镜像定义 |
| `Volume` | 模型/数据的持久存储 |
| `Secret` | 安全凭据存储 |

### 执行模式

| 命令 | 描述 |
|---------|-------------|
| `modal run script.py` | 执行并退出 |
| `modal serve script.py` | 带实时重载的开发 |
| `modal deploy script.py` | 持久云部署 |

## GPU 配置

### 可用 GPU

| GPU | VRAM | 最佳用途 |
|-----|------|----------|
| `T4` | 16GB | 预算推理，小型模型 |
| `L4` | 24GB | 推理，Ada Lovelace 架构 |
| `A10G` | 24GB | 训练/推理，比 T4 快 3.3 倍 |
| `L40S` | 48GB | 推荐用于推理（最佳成本/性能） |
| `A100-40GB` | 40GB | 大型模型训练 |
| `A100-80GB` | 80GB | 超大型模型 |
| `H100` | 80GB | 最快，FP8 + Transformer Engine |
| `H200` | 141GB | 从 H100 自动升级，4.8TB/s 带宽 |
| `B200` | 最新 | Blackwell 架构 |

### GPU 规格模式

```python
# 单 GPU
@app.function(gpu="A100")

# 特定内存版本
@app.function(gpu="A100-80GB")

# 多 GPU（最多 8 个）
@app.function(gpu="H100:4")

# 带回退的 GPU
@app.function(gpu=["H100", "A100", "L40S"])

# 任何可用 GPU
@app.function(gpu="any")
```

## 容器镜像

```python
# 带 pip 的基本镜像
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "torch==2.1.0", "transformers==4.36.0", "accelerate"
)

# 来自 CUDA 基础镜像
image = modal.Image.from_registry(
    "nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04",
    add_python="3.11"
).pip_install("torch", "transformers")

# 带系统包
image = modal.Image.debian_slim().apt_install("git", "ffmpeg").pip_install("whisper")
```

## 持久存储

```python
volume = modal.Volume.from_name("model-cache", create_if_missing=True)

@app.function(gpu="A10G", volumes={"/models": volume})
def load_model():
    import os
    model_path = "/models/llama-7b"
    if not os.path.exists(model_path):
        model = download_model()
        model.save_pretrained(model_path)
        volume.commit()  # 持久化更改
    return load_from_path(model_path)
```

## Web 端点

### FastAPI 端点装饰器

```python
@app.function()
@modal.fastapi_endpoint(method="POST")
def predict(text: str) -> dict:
    return {"result": model.predict(text)}
```

### 完整 ASGI 应用

```python
from fastapi import FastAPI
web_app = FastAPI()

@web_app.post("/predict")
async def predict(text: str):
    return {"result": await model.predict.remote.aio(text)}

@app.function()
@modal.asgi_app()
def fastapi_app():
    return web_app
```

### Web 端点类型

| 装饰器 | 用例 |
|-----------|----------|
| `@modal.fastapi_endpoint()` | 简单函数 → API |
| `@modal.asgi_app()` | 完整 FastAPI/Starlette 应用 |
| `@modal.wsgi_app()` | Django/Flask 应用 |
| `@modal.web_server(port)` | 任意 HTTP 服务器 |

## 动态批处理

```python
@app.function()
@modal.batched(max_batch_size=32, wait_ms=100)
async def batch_predict(inputs: list[str]) -> list[dict]:
    # 输入自动批处理
    return model.batch_predict(inputs)
```

## 密钥管理

```bash
# 创建密钥
modal secret create huggingface HF_TOKEN=hf_xxx
```

```python
@app.function(secrets=[modal.Secret.from_name("huggingface")])
def download_model():
    import os
    token = os.environ["HF_TOKEN"]
```

## 调度

```python
@app.function(schedule=modal.Cron("0 0 * * *"))  # 每天午夜
def daily_job():
    pass

@app.function(schedule=modal.Period(hours=1))
def hourly_job():
    pass
```

## 性能优化

### 冷启动缓解

```python
@app.function(
    container_idle_timeout=300,  # 保持热态 5 分钟
    allow_concurrent_inputs=10,  # 处理并发请求
)
def inference():
    pass
```

### 模型加载最佳实践

```python
@app.cls(gpu="A100")
class Model:
    @modal.enter()  # 容器启动时运行一次
    def load(self):
        self.model = load_model()  # 在预热期间加载

    @modal.method()
    def predict(self, x):
        return self.model(x)
```

## 并行处理

```python
@app.function()
def process_item(item):
    return expensive_computation(item)

@app.function()
def run_parallel():
    items = list(range(1000))
    # 扇出到并行容器
    results = list(process_item.map(items))
    return results
```

## 常见配置

```python
@app.function(
    gpu="A100",
    memory=32768,              # 32GB 内存
    cpu=4,                     # 4 个 CPU 核心
    timeout=3600,              # 最长 1 小时
    container_idle_timeout=120,# 保持热态 2 分钟
    retries=3,                 # 失败重试
    concurrency_limit=10,      # 最大并发容器
)
def my_function():
    pass
```

## 调试

```python
# 本地测试
if __name__ == "__main__":
    result = my_function.local()

# 查看日志
# modal app logs my-app
```

## 常见问题

| 问题 | 解决方案 |
|-------|----------|
| 冷启动延迟 | 增加 `container_idle_timeout`，使用 `@modal.enter()` |
| GPU OOM | 使用更大 GPU（`A100-80GB`），启用梯度检查点 |
| 镜像构建失败 | 固定依赖版本，检查 CUDA 兼容性 |
| 超时错误 | 增加 `timeout`，添加检查点 |

## 参考

- **[高级用法](references/advanced-usage.md)** — 多 GPU、分布式训练、成本优化
- **[故障排除](references/troubleshooting.md)** — 常见问题和解决方案

## 资源

- **文档**：https://modal.com/docs
- **示例**：https://github.com/modal-labs/modal-examples
- **定价**：https://modal.com/pricing
- **Discord**：https://discord.gg/modal

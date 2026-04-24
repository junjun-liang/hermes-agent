---
name: stable-diffusion-image-generation
description: 使用 HuggingFace Diffusers 通过 Stable Diffusion 模型进行最先进的文本到图像生成。用于根据文本提示词生成图像、图像到图像转换、图像修复或构建自定义扩散管道。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [diffusers>=0.30.0, transformers>=4.41.0, accelerate>=0.31.0, torch>=2.0.0]
metadata:
  hermes:
    tags: [Image Generation, Stable Diffusion, Diffusers, Text-to-Image, Multimodal, Computer Vision]

---

# Stable Diffusion 图像生成

使用 HuggingFace Diffusers 库通过 Stable Diffusion 生成图像的综合指南。

## 何时使用 Stable Diffusion

**当以下情况时使用 Stable Diffusion：**
- 从文本描述生成图像
- 执行图像到图像转换（风格迁移、增强）
- 图像修复（填充掩码区域）
- 图像扩展（在边界外延伸图像）
- 创建现有图像的变体
- 构建自定义图像生成工作流

**关键特性：**
- **文本到图像**：从自然语言提示词生成图像
- **图像到图像**：在文本指导下转换现有图像
- **图像修复**：用上下文感知内容填充掩码区域
- **ControlNet**：添加空间条件（边缘、姿势、深度）
- **LoRA 支持**：高效的微调和风格适配
- **多模型**：支持 SD 1.5、SDXL、SD 3.0、Flux

**改用替代方案：**
- **DALL-E 3**：用于无需 GPU 的基于 API 的生成
- **Midjourney**：用于艺术化、风格化输出
- **Imagen**：用于 Google Cloud 集成
- **Leonardo.ai**：用于基于网页的创意工作流

## 快速开始

### 安装

```bash
pip install diffusers transformers accelerate torch
pip install xformers  # 可选：内存高效的注意力
```

### 基本文本到图像

```python
from diffusers import DiffusionPipeline
import torch

# 加载管道（自动检测模型类型）
pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)
pipe.to("cuda")

# 生成图像
image = pipe(
    "日落时宁静的高山风景，高度详细",
    num_inference_steps=50,
    guidance_scale=7.5
).images[0]

image.save("output.png")
```

### 使用 SDXL（更高质量）

```python
from diffusers import AutoPipelineForText2Image
import torch

pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")

# 启用内存优化
pipe.enable_model_cpu_offload()

image = pipe(
    prompt="带飞行汽车的未来城市，电影级灯光",
    height=1024,
    width=1024,
    num_inference_steps=30
).images[0]
```

## 架构概述

### 三大支柱设计

Diffusers 围绕三个核心组件构建：

```
管道（编排）
├── 模型（神经网络）
│   ├── UNet / Transformer（噪声预测）
│   ├── VAE（潜在编码/解码）
│   └── 文本编码器（CLIP/T5）
└── 调度器（去噪算法）
```

### 管道推理流程

```
文本提示词 → 文本编码器 → 文本嵌入
                                    ↓
随机噪声 → [去噪循环] ← 调度器
                      ↓
               预测的噪声
                      ↓
              VAE 解码器 → 最终图像
```

## 核心概念

### 管道

管道编排完整工作流：

| 管道 | 用途 |
|----------|---------|
| `StableDiffusionPipeline` | 文本到图像（SD 1.x/2.x） |
| `StableDiffusionXLPipeline` | 文本到图像（SDXL） |
| `StableDiffusion3Pipeline` | 文本到图像（SD 3.0） |
| `FluxPipeline` | 文本到图像（Flux 模型） |
| `StableDiffusionImg2ImgPipeline` | 图像到图像 |
| `StableDiffusionInpaintPipeline` | 图像修复 |

### 调度器

调度器控制去噪过程：

| 调度器 | 步数 | 质量 | 用途 |
|-----------|-------|---------|----------|
| `EulerDiscreteScheduler` | 20-50 | 好 | 默认选择 |
| `EulerAncestralDiscreteScheduler` | 20-50 | 好 | 更多变化 |
| `DPMSolverMultistepScheduler` | 15-25 | 优秀 | 快速高质量 |
| `DDIMScheduler` | 50-100 | 好 | 确定性 |
| `LCMScheduler` | 4-8 | 好 | 非常快 |
| `UniPCMultistepScheduler` | 15-25 | 优秀 | 快速收敛 |

### 切换调度器

```python
from diffusers import DPMSolverMultistepScheduler

# 切换以加快生成
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config
)

# 现在用更少步数生成
image = pipe(prompt, num_inference_steps=20).images[0]
```

## 生成参数

### 关键参数

| 参数 | 默认值 | 描述 |
|-----------|---------|-------------|
| `prompt` | 必需 | 所需图像的文本描述 |
| `negative_prompt` | 无 | 图像中要避免的内容 |
| `num_inference_steps` | 50 | 去噪步数（越多质量越好） |
| `guidance_scale` | 7.5 | 提示词遵循度（通常 7-12） |
| `height`, `width` | 512/1024 | 输出尺寸（8 的倍数） |
| `generator` | 无 | 用于可复现性的 torch 生成器 |
| `num_images_per_prompt` | 1 | 批量大小 |

### 可复现生成

```python
import torch

generator = torch.Generator(device="cuda").manual_seed(42)

image = pipe(
    prompt="一只戴高帽的猫",
    generator=generator,
    num_inference_steps=50
).images[0]
```

### 负面提示词

```python
image = pipe(
    prompt="花园里狗的专业照片",
    negative_prompt="模糊、低质量、扭曲、丑陋、解剖错误",
    guidance_scale=7.5
).images[0]
```

## 图像到图像

在文本指导下转换现有图像：

```python
from diffusers import AutoPipelineForImage2Image
from PIL import Image

pipe = AutoPipelineForImage2Image.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

init_image = Image.open("input.jpg").resize((512, 512))

image = pipe(
    prompt="场景的水彩画",
    image=init_image,
    strength=0.75,  # 转换程度（0-1）
    num_inference_steps=50
).images[0]
```

## 图像修复

填充掩码区域：

```python
from diffusers import AutoPipelineForInpainting
from PIL import Image

pipe = AutoPipelineForInpainting.from_pretrained(
    "runwayml/stable-diffusion-inpainting",
    torch_dtype=torch.float16
).to("cuda")

image = Image.open("photo.jpg")
mask = Image.open("mask.png")  # 白色 = 修复区域

result = pipe(
    prompt="一辆停在街上的红色汽车",
    image=image,
    mask_image=mask,
    num_inference_steps=50
).images[0]
```

## ControlNet

添加空间条件进行精确控制：

```python
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
import torch

# 加载边缘条件的 ControlNet
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_canny",
    torch_dtype=torch.float16
)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16
).to("cuda")

# 使用 Canny 边缘图像作为控制
control_image = get_canny_image(input_image)

image = pipe(
    prompt="梵高风格的美丽房屋",
    image=control_image,
    num_inference_steps=30
).images[0]
```

### 可用 ControlNet

| ControlNet | 输入类型 | 用途 |
|------------|----------|----------|
| `canny` | 边缘图 | 保留结构 |
| `openpose` | 姿势骨架 | 人体姿势 |
| `depth` | 深度图 | 3D 感知生成 |
| `normal` | 法线图 | 表面细节 |
| `mlsd` | 线段 | 建筑线条 |
| `scribble` | 粗略草图 | 草图到图像 |

## LoRA 适配器

加载微调的风格适配器：

```python
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

# 加载 LoRA 权重
pipe.load_lora_weights("path/to/lora", weight_name="style.safetensors")

# 用 LoRA 风格生成
image = pipe("训练风格下的肖像").images[0]

# 调整 LoRA 强度
pipe.fuse_lora(lora_scale=0.8)

# 卸载 LoRA
pipe.unload_lora_weights()
```

### 多个 LoRA

```python
# 加载多个 LoRA
pipe.load_lora_weights("lora1", adapter_name="style")
pipe.load_lora_weights("lora2", adapter_name="character")

# 为每个设置权重
pipe.set_adapters(["style", "character"], adapter_weights=[0.7, 0.5])

image = pipe("一幅肖像").images[0]
```

## 内存优化

### 启用 CPU 卸载

```python
# 模型 CPU 卸载 - 不使用时将模型移到 CPU
pipe.enable_model_cpu_offload()

# 顺序 CPU 卸载 - 更激进，更慢
pipe.enable_sequential_cpu_offload()
```

### 注意力切片

```python
# 分块计算注意力以减少内存
pipe.enable_attention_slicing()

# 或指定切片大小
pipe.enable_attention_slicing("max")
```

### xFormers 内存高效注意力

```python
# 需要 xformers 包
pipe.enable_xformers_memory_efficient_attention()
```

### 大图像的 VAE 切片

```python
# 分块解码大图像的潜在变量
pipe.enable_vae_slicing()
pipe.enable_vae_tiling()
```

## 模型变体

### 加载不同精度

```python
# FP16（GPU 推荐）
pipe = DiffusionPipeline.from_pretrained(
    "model-id",
    torch_dtype=torch.float16,
    variant="fp16"
)

# BF16（更好精度，需要 Ampere+ GPU）
pipe = DiffusionPipeline.from_pretrained(
    "model-id",
    torch_dtype=torch.bfloat16
)
```

### 加载特定组件

```python
from diffusers import UNet2DConditionModel, AutoencoderKL

# 加载自定义 VAE
vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse")

# 与管道配合使用
pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    vae=vae,
    torch_dtype=torch.float16
)
```

## 批量生成

高效生成多张图像：

```python
# 多个提示词
prompts = [
    "一只弹钢琴的猫",
    "一只读书的狗",
    "一只画画的鸟"
]

images = pipe(prompts, num_inference_steps=30).images

# 每个提示词多张图像
images = pipe(
    "美丽的日落",
    num_images_per_prompt=4,
    num_inference_steps=30
).images
```

## 常见工作流

### 工作流 1：高质量生成

```python
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
import torch

# 1. 加载 SDXL 并优化
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_model_cpu_offload()

# 2. 用质量设置生成
image = pipe(
    prompt="草原上威严的狮子，黄金时间灯光，8k，详细的毛发",
    negative_prompt="模糊、低质量、卡通、动漫、草图",
    num_inference_steps=30,
    guidance_scale=7.5,
    height=1024,
    width=1024
).images[0]
```

### 工作流 2：快速原型

```python
from diffusers import AutoPipelineForText2Image, LCMScheduler
import torch

# 使用 LCM 进行 4-8 步生成
pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16
).to("cuda")

# 加载 LCM LoRA 用于快速生成
pipe.load_lora_weights("latent-consistency/lcm-lora-sdxl")
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
pipe.fuse_lora()

# 约 1 秒内生成
image = pipe(
    "美丽的风景",
    num_inference_steps=4,
    guidance_scale=1.0
).images[0]
```

## 常见问题

**CUDA 内存不足：**
```python
# 启用内存优化
pipe.enable_model_cpu_offload()
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()

# 或使用更低精度
pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
```

**黑屏/噪声图像：**
```python
# 检查 VAE 配置
# 如需可绕过安全检查器
pipe.safety_checker = None

# 确保 dtype 一致
pipe = pipe.to(dtype=torch.float16)
```

**生成缓慢：**
```python
# 使用更快的调度器
from diffusers import DPMSolverMultistepScheduler
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

# 减少步数
image = pipe(prompt, num_inference_steps=20).images[0]
```

## 参考

- **[高级用法](references/advanced-usage.md)** — 自定义管道、微调、部署
- **[故障排除](references/troubleshooting.md)** — 常见问题和解决方案

## 资源

- **文档**：https://huggingface.co/docs/diffusers
- **仓库**：https://github.com/huggingface/diffusers
- **模型中心**：https://huggingface.co/models?library=diffusers
- **Discord**：https://discord.gg/diffusers

---
name: audiocraft
description: 使用 AudioCraft/MusicGen 生成音乐和音频。通过提示词创建音乐、生成背景音乐、进行风格实验和音频原型设计。Meta 的音频生成框架。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [audiocraft, torch, torchaudio]
metadata:
  hermes:
    tags: [Audio Generation, Music Generation, MusicGen, AudioCraft, Meta AI, Creative AI]

---

# AudioCraft/MusicGen - 音频和音乐生成

## 何时使用此技能

当需要以下情况时使用 AudioCraft/MusicGen：
- **使用提示词生成音乐**（"创作一首快乐的吉他民谣"）
- **从描述生成音频**
- **为视频/播客生成背景音乐**
- **探索不同的音乐风格和流派**
- **音频原型设计和创意实验**
- **需要本地音频生成**（非 API）

**创建者**：Meta AI | **GitHub Stars**：25,000+ | **模型**：MusicGen、AudioGen

## 安装

```bash
# 基本安装
pip install audiocraft

# 或从源代码
git clone https://github.com/facebookresearch/audiocraft
cd audiocraft
pip install -e .
```

## 快速开始

### 基本音乐生成

```python
from audiocraft.models import MusicGen
import torchaudio

# 加载预训练模型
model = MusicGen.get_pretrained("medium")  # 或 "small", "large", "melody"

# 设置生成参数
model.set_generation_params(
    duration=30,      # 秒
    top_k=250,        # 采样质量
    top_p=0.0,        # 核采样
    temperature=1.0,  # 创意性
    cfg_coef=3.0      # 分类器无指导（越高越接近提示词）
)

# 生成音乐
prompt = "快乐的吉他民谣，带轻快的旋律"
output = model.generate([prompt], progress=True)

# 保存音频
torchaudio.save("output_music.wav", output[0].cpu(), model.sample_rate)
print("已保存到 output_music.wav")
```

### 带旋律的音乐生成

```python
from audiocraft.models import MusicGen
import torchaudio

# 加载旋律模型
model = MusicGen.get_pretrained("melody")

model.set_generation_params(
    duration=30,
    cfg_coef=3.0
)

# 加载旋律音频
melody_wav, sr = torchaudio.load("melody_input.wav")
if sr != model.sample_rate:
    melody_wav = torchaudio.functional.resample(melody_wav, sr, model.sample_rate)

# 生成与旋律匹配的音乐
output = model.generate_with_chroma(
    descriptions=["快乐的流行歌曲"],
    melody_wavs=melody_wav.unsqueeze(0),
    sample_rate=model.sample_rate,
    progress=True
)

torchaudio.save("output_melody.wav", output[0].cpu(), model.sample_rate)
```

## 模型选项

| 模型 | 大小 | 质量 | VRAM | 速度 | 用途 |
|--------|-------|---------|---------|---------|----------|
| **small** | ~1.5GB | 基础 | 4GB | 最快 | 测试/原型 |
| **medium** | ~3GB | 好 | 8GB | 中 | **推荐** |
| **large** | ~6GB | 最佳 | 12GB | 慢 | 最高质量 |
| **melody** | ~3GB | 好 | 8GB | 中 | 带旋律输入 |

## 生成参数

### set_generation_params()

```python
model.set_generation_params(
    duration=30,       # 生成持续时间（秒）
    top_k=250,         # 采样时考虑的最高概率 token 数
                       # 较高 = 更多变化，较低 = 更聚焦
    top_p=0.0,         # 核采样（0.0 表示禁用）
    temperature=1.0,   # 创意性：较高 = 更有创意，较低 = 更可预测
    cfg_coef=3.0,      # 分类器无指导系数
                       # 较高 = 更接近提示词，较低 = 更自由
    use_sampling=True, # 使用采样（否则贪婪解码）
    two_step_cfg=True  # 两步骤 CFG 以获得更好质量
)
```

### 按风格调整参数

```python
# 古典音乐（更可预测）
model.set_generation_params(duration=60, top_k=200, temperature=0.8, cfg_coef=4.0)

# 实验性/爵士乐（更有创意）
model.set_generation_params(duration=30, top_k=300, temperature=1.2, cfg_coef=2.5)

# 带人声的流行音乐
model.set_generation_params(duration=30, top_k=250, temperature=1.0, cfg_coef=3.5)
```

## 常见模式

### 模式 1：批量生成

```python
prompts = [
    "快乐的吉他民谣",
    "激烈的电子舞曲",
    "悲伤的钢琴独奏",
    "放克贝斯线",
    "电影管弦乐高潮"
]

outputs = model.generate(prompts, progress=True)

# 保存每个音频
for i, output in enumerate(outputs):
    filename = f"music_{i:02d}.wav"
    torchaudio.save(filename, output.cpu(), model.sample_rate)
    print(f"已保存 {filename}")
```

### 模式 2：流式/分块生成

对于长音频（> 30 秒），分块生成：

```python
def generate_long_audio(model, prompt, total_duration, chunk_duration=30):
    """将长音频生成分块。"""
    segments = []
    num_chunks = int(total_duration / chunk_duration)

    for i in range(num_chunks):
        print(f"生成片段 {i+1}/{num_chunks}")
        output = model.generate([prompt], duration=chunk_duration)
        segments.append(output[0].cpu())

    # 连接片段
    full_audio = torch.cat(segments, dim=1)
    return full_audio

full = generate_long_audio(model, "环境自然声音", 120)  # 2 分钟
torchaudio.save("ambient_2min.wav", full, model.sample_rate)
```

### 模式 3：音频到音频

使用现有音频作为输入进行转换：

```python
import torchaudio
from audiocraft.models import MusicGen

model = MusicGen.get_pretrained("medium")

# 加载输入音频
input_audio, sr = torchaudio.load("input.wav")

# 重新采样到模型采样率
if sr != model.sample_rate:
    input_audio = torchaudio.functional.resample(input_audio, sr, model.sample_rate)

# 基于输入生成
output = model.generate(
    ["转换为爵士风格"],
    duration=30
)

torchaudio.save("output_jazz.wav", output[0].cpu(), model.sample_rate)
```

## 提示词指南

### 好的提示词

```
# ✅ 具体
"带明亮钢琴和轻鼓的慢速民谣民谣"

# ✅ 风格描述
"80 年代合成器波带复古鼓机和温暖合成器"

# ✅ 情绪描述
"忧郁的吉他独奏，带混响，带悲伤的基调"

# ✅ 乐器
"独奏小提琴带弦乐伴奏，古典风格"
```

### 模糊的提示词

```
# ❌ 太模糊
"好音乐"
"一些音乐"

# ❌ 矛盾
"快乐但悲伤的歌曲"

# ❌ 太长
"一首关于...的歌曲"（模型不理解叙事）
```

### 风格关键词

```
流派：民谣、摇滚、爵士、古典、电子、流行、嘻哈
情绪：快乐、悲伤、黑暗、充满活力、放松、紧张
乐器：吉他、钢琴、鼓、贝斯、小提琴、合成器
节奏：慢速、中速、快速、快节奏
氛围：环境、电影、游戏、冥想、派对
```

## 故障排除

### 内存问题

```python
# 使用更小的模型
model = MusicGen.get_pretrained("small")

# 减少持续时间
model.set_generation_params(duration=15)

# 使用 CPU 卸载
model.set_generation_params(duration=30)
model.device = "cpu"
```

### 质量低

```python
# 使用更大的模型
model = MusicGen.get_pretrained("large")

# 调整采样参数
model.set_generation_params(
    duration=30,
    top_k=250,
    temperature=0.95,
    cfg_coef=3.5
)

# 增加持续时间以获得更好上下文
model.set_generation_params(duration=60)
```

### 音频中有断音

```python
# 增加 top_k
model.set_generation_params(top_k=300)

# 降低温度
model.set_generation_params(temperature=0.8)

# 增加 CFG 系数
model.set_generation_params(cfg_coef=4.0)
```

## 集成示例

### Gradio Web UI

```python
import gradio as gr
from audiocraft.models import MusicGen
import torchaudio

model = MusicGen.get_pretrained("medium")

def generate(prompt, duration, creativity):
    model.set_generation_params(
        duration=duration,
        top_k=int(200 + creativity * 100),
        temperature=0.5 + creativity * 0.7,
        cfg_coef=4.0 - creativity * 2.0
    )

    output = model.generate([prompt], progress=True)
    torchaudio.save("output.wav", output[0].cpu(), model.sample_rate)

    return "output.wav"

demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Textbox(label="提示词"),
        gr.Slider(10, 120, value=30, label="持续时间（秒）"),
        gr.Slider(0, 1, value=0.5, label="创意性")
    ],
    outputs=gr.Audio(label="生成的音频")
)

demo.launch()
```

### 与 FastAPI 配合

```python
from fastapi import FastAPI
from audiocraft.models import MusicGen
import torchaudio
import io

app = FastAPI()
model = MusicGen.get_pretrained("medium")

@app.post("/generate")
async def generate(prompt: str, duration: int = 30):
    model.set_generation_params(duration=duration)
    output = model.generate([prompt])

    # 保存为 WAV 到内存
    buffer = io.BytesIO()
    torchaudio.save(buffer, output[0].cpu(), model.sample_rate, format="WAV")
    buffer.seek(0)

    return buffer.getvalue()
```

## 硬件要求

- **GPU**：CUDA 11.3+ 推荐（可在 CPU 上运行，非常慢）
- **VRAM**：
  - Small：~4GB
  - Medium：~8GB
  - Large：~12GB
- **RAM**：16GB+ 推荐
- **存储**：每个模型 1.5-6GB

## 资源

- **GitHub**：https://github.com/facebookresearch/audiocraft（25k+ stars）
- **演示**：https://huggingface.co/spaces/facebook/MusicGen
- **模型**：https://huggingface.co/facebook/musicgen-{small,medium,large,melody}
- **论文**："Simple and Controllable Music Generation"

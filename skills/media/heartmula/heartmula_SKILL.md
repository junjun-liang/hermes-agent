---
name: heartmula
description: 设置和运行HeartMuLa，开源音乐生成模型家族（类似Suno）。从歌词+标签生成完整歌曲，支持多语言。
version: 1.0.0
metadata:
  hermes:
    tags: [音乐, 音频, 生成, ai, heartmula, heartcodec, 歌词, 歌曲]
    related_skills: [audiocraft]
---

# HeartMuLa - 开源音乐生成

## 概述
HeartMuLa是开源音乐基础模型家族（Apache-2.0），根据歌词和标签生成音乐。开源中类似Suno。包括：
- **HeartMuLa** - 音乐语言模型（3B/7B）用于从歌词+标签生成
- **HeartCodec** - 12.5Hz音乐编解码器，用于高保真音频重建
- **HeartTranscriptor** - 基于Whisper的歌词转录
- **HeartCLAP** - 音频-文本对齐模型

## 何时使用
- 用户想从文本描述生成音乐/歌曲
- 用户想要开源Suno替代方案
- 用户想要本地/离线音乐生成
- 用户询问HeartMuLa、heartlib或AI音乐生成

## 硬件要求
- **最低**：8GB VRAM，使用`--lazy_load true`（按顺序加载/卸载模型）
- **推荐**：16GB+ VRAM用于舒适的单GPU使用
- **多GPU**：使用`--mula_device cuda:0 --codec_device cuda:1`跨GPU分配
- 3B模型使用lazy_load峰值约6.2GB VRAM

## 安装步骤

### 1. 克隆仓库
```bash
cd ~/  # 或所需目录
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
```

### 2. 创建虚拟环境（需要Python 3.10）
```bash
uv venv --python 3.10 .venv
. .venv/bin/activate
uv pip install -e .
```

### 3. 修复依赖兼容性问题

**重要**：截至2026年2月，固定的依赖项与新包存在冲突。应用以下修复：

```bash
# 升级datasets（旧版本与当前pyarrow不兼容）
uv pip install --upgrade datasets

# 升级transformers（需要与huggingface-hub 1.x兼容）
uv pip install --upgrade transformers
```

### 4. 修补源代码（transformers 5.x必需）

**补丁1 - RoPE缓存修复** 在 `src/heartlib/heartmula/modeling_heartmula.py`：

在`HeartMuLa`类的`setup_caches`方法中，在`reset_caches` try/except块之后和`with device:`块之前添加RoPE重新初始化：

```python
# 重新初始化在meta设备加载期间跳过的RoPE缓存
from torchtune.models.llama3_1._position_embeddings import Llama3ScaledRoPE
for module in self.modules():
    if isinstance(module, Llama3ScaledRoPE) and not module.is_cache_built:
        module.rope_init()
        module.to(device)
```

**原因**：`from_pretrained`先在meta设备上创建模型；`Llama3ScaledRoPE.rope_init()`在meta张量上跳过缓存构建，然后在权重加载到实际设备后不再重建。

**补丁2 - HeartCodec加载修复** 在 `src/heartlib/pipelines/music_generation.py`：

在所有`HeartCodec.from_pretrained()`调用中添加`ignore_mismatched_sizes=True`（有2处：`__init__`中的eager加载和`codec`属性中的lazy加载）。

**原因**：VQ码本`initted`缓冲在检查点中形状为`[1]`，模型中为`[]`。数据相同，只是标量与0维张量。可以安全忽略。

### 5. 下载模型检查点
```bash
cd heartlib  # 项目根目录
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

所有3个可以并行下载。总大小数GB。

## GPU / CUDA

HeartMuLa默认使用CUDA（`--mula_device cuda --codec_device cuda`）。如果用户已安装支持PyTorch CUDA的NVIDIA GPU，无需额外设置。

- 安装的`torch==2.4.1`开箱即用地包含CUDA 12.1支持
- `torchtune`可能报告版本`0.4.0+cpu` — 这只是包元数据，它仍然通过PyTorch使用CUDA
- 要验证GPU是否正在使用，查找输出中的"CUDA memory"行（例如"CUDA memory before unloading: 6.20 GB"）
- **没有GPU？** 可以使用`--mula_device cpu --codec_device cpu`在CPU上运行，但预计生成会**非常慢**（可能30-60+分钟一首歌，而GPU约4分钟）。CPU模式还需要大量RAM（约12GB+空闲）。如果用户没有NVIDIA GPU，推荐使用云GPU服务（Google Colab免费层带T4、Lambda Labs等）或在线演示 https://heartmula.github.io/。

## 使用

### 基础生成
```bash
cd heartlib
. .venv/bin/activate
python ./examples/run_music_generation.py \
  --model_path=./ckpt \
  --version="3B" \
  --lyrics="./assets/lyrics.txt" \
  --tags="./assets/tags.txt" \
  --save_path="./assets/output.mp3" \
  --lazy_load true
```

### 输入格式

**标签**（逗号分隔，无空格）：
```
piano,happy,wedding,synthesizer,romantic
```
或
```
rock,energetic,guitar,drums,male-vocal
```

**歌词**（使用方括号结构标签）：
```
[Intro]

[Verse]
Your lyrics here...

[Chorus]
Chorus lyrics...

[Bridge]
Bridge lyrics...

[Outro]
```

### 关键参数
| 参数 | 默认值 | 描述 |
|-----------|---------|-------------|
| `--max_audio_length_ms` | 240000 | 最大长度（毫秒）（240秒 = 4分钟） |
| `--topk` | 50 | Top-k采样 |
| `--temperature` | 1.0 | 采样温度 |
| `--cfg_scale` | 1.5 | 无分类器引导比例 |
| `--lazy_load` | false | 按需加载/卸载模型（节省VRAM） |
| `--mula_dtype` | bfloat16 | HeartMuLa数据类型（推荐bf16） |
| `--codec_dtype` | float32 | HeartCodec数据类型（推荐fp32保证质量） |

### 性能
- RTF（实时因子）≈ 1.0 — 4分钟歌曲约需4分钟生成
- 输出：MP3，48kHz立体声，128kbps

## 陷阱
1. **不要对HeartCodec使用bf16** — 会降低音频质量。使用fp32（默认）。
2. **标签可能被忽略** — 已知问题（#90）。歌词往往占主导；尝试标签顺序。
3. **macOS上Triton不可用** — GPU加速仅限Linux/CUDA。
4. **RTX 5080不兼容** 已在上游问题中报告。
5. 依赖固定冲突需要上述手动升级和补丁。

## 链接
- 仓库：https://github.com/HeartMuLa/heartlib
- 模型：https://huggingface.co/HeartMuLa
- 论文：https://arxiv.org/abs/2601.10547
- 许可证：Apache-2.0

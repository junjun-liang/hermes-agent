---
name: songsee
description: 通过 CLI 从音频文件生成频谱图和音频特征可视化（mel、chroma、MFCC、tempogram 等）。用于音频分析、音乐制作调试和可视化文档。
version: 1.0.0
author: 社区
license: MIT
metadata:
  hermes:
    tags: [音频, 可视化, 频谱图, 音乐, 分析]
    homepage: https://github.com/steipete/songsee
prerequisites:
  commands: [songsee]
---

# songsee

从音频文件生成频谱图和多面板音频特征可视化。

## 前提条件

需要 [Go](https://go.dev/doc/install)：
```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

可选：`ffmpeg` 用于 WAV/MP3 之外的格式。

## 快速开始

```bash
# 基本频谱图
songsee track.mp3

# 保存到指定文件
songsee track.mp3 -o spectrogram.png

# 多面板可视化网格
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux

# 时间切片（从 12.5 秒开始，持续 8 秒）
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg

# 从标准输入
cat track.mp3 | songsee - --format png -o out.png
```

## 可视化类型

使用 `--viz` 配合逗号分隔的值：

| 类型 | 描述 |
|------|-------------|
| `spectrogram` | 标准频率频谱图 |
| `mel` | Mel 缩放频谱图 |
| `chroma` | 音高类别分布 |
| `hpss` | 谐波/打击乐分离 |
| `selfsim` | 自相似矩阵 |
| `loudness` | 响度随时间变化 |
| `tempogram` | 速度估计 |
| `mfcc` | Mel 频率倒谱系数 |
| `flux` | 频谱通量（起始检测） |

多个 `--viz` 类型在单个图像中呈现为网格。

## 常用标志

| 标志 | 描述 |
|------|-------------|
| `--viz` | 可视化类型（逗号分隔） |
| `--style` | 调色板：`classic`、`magma`、`inferno`、`viridis`、`gray` |
| `--width` / `--height` | 输出图像尺寸 |
| `--window` / `--hop` | FFT 窗口和跳步大小 |
| `--min-freq` / `--max-freq` | 频率范围过滤器 |
| `--start` / `--duration` | 音频的时间切片 |
| `--format` | 输出格式：`jpg` 或 `png` |
| `-o` | 输出文件路径 |

## 说明

- WAV 和 MP3 本地解码；其他格式需要 `ffmpeg`
- 输出图像可使用 `vision_analyze` 进行自动音频分析
- 适用于比较音频输出、调试合成或记录音频处理流水线

---
name: openhue
description: 通过OpenHue CLI控制Philips Hue灯光、房间和场景。开关灯光、调整亮度、颜色、色温和激活场景。
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [智能家居, Hue, 灯光, IoT, 自动化]
    homepage: https://www.openhue.io/cli
prerequisites:
  commands: [openhue]
---

# OpenHue CLI

通过终端中的Hue Bridge控制Philips Hue灯光和场景。

## 前置条件

```bash
# Linux（预编译二进制）
curl -sL https://github.com/openhue/openhue-cli/releases/latest/download/openhue-linux-amd64 -o ~/.local/bin/openhue && chmod +x ~/.local/bin/openhue

# macOS
brew install openhue/cli/openhue-cli
```

首次运行需要按下Hue Bridge上的按钮进行配对。Bridge必须位于同一局域网上。

## 何时使用

- "打开/关闭灯光"
- "调暗客厅灯光"
- "设置场景"或"电影模式"
- 控制特定的Hue房间、区域或单个灯泡
- 调整亮度、颜色或色温

## 常用命令

### 列出资源

```bash
openhue get light       # 列出所有灯光
openhue get room        # 列出所有房间
openhue get scene       # 列出所有场景
```

### 控制灯光

```bash
# 开关
openhue set light "Bedroom Lamp" --on
openhue set light "Bedroom Lamp" --off

# 亮度（0-100）
openhue set light "Bedroom Lamp" --on --brightness 50

# 色温（暖到冷：153-500 mirek）
openhue set light "Bedroom Lamp" --on --temperature 300

# 颜色（按名称或十六进制）
openhue set light "Bedroom Lamp" --on --color red
openhue set light "Bedroom Lamp" --on --rgb "#FF5500"
```

### 控制房间

```bash
# 关闭整个房间
openhue set room "Bedroom" --off

# 设置房间亮度
openhue set room "Bedroom" --on --brightness 30
```

### 场景

```bash
openhue set scene "Relax" --room "Bedroom"
openhue set scene "Concentrate" --room "Office"
```

## 快速预设

```bash
# 睡眠模式（调暗暖色）
openhue set room "Bedroom" --on --brightness 20 --temperature 450

# 工作模式（明亮冷色）
openhue set room "Office" --on --brightness 100 --temperature 250

# 电影模式（调暗）
openhue set room "Living Room" --on --brightness 10

# 全部关闭
openhue set room "Bedroom" --off
openhue set room "Office" --off
openhue set room "Living Room" --off
```

## 注意事项

- Bridge必须与运行Hermes的机器在同一局域网上
- 首次运行需要物理按下Hue Bridge上的按钮进行授权
- 颜色仅适用于支持颜色的灯泡（不适用于仅白色型号）
- 灯光和房间名称区分大小写 — 使用`openhue get light`检查确切名称
- 与cron作业配合使用定时照明效果很好（例如睡觉时调暗，醒来时调亮）

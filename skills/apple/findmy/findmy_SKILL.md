---
name: findmy
description: 通过AppleScript和屏幕捕获在macOS上使用FindMy.app追踪Apple设备和AirTag。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [FindMy, AirTag, 定位, 追踪, macOS, Apple]
---

# Find My（Apple）

通过macOS上的FindMy.app追踪Apple设备和AirTag。由于Apple没有为FindMy提供CLI，此技能使用AppleScript打开应用并使用屏幕捕获读取设备位置。

## 前置条件

- **macOS** 系统，已安装 Find My 应用并登录 iCloud
- 设备/AirTag 已在 Find My 中注册
- 终端需要屏幕录制权限（系统设置 → 隐私 → 屏幕录制）
- **可选但推荐**：安装 `peekaboo` 以获取更好的UI自动化：
  `brew install steipete/tap/peekaboo`

## 使用场景

- 用户询问"我的[设备/猫/钥匙/包]在哪里？"
- 追踪 AirTag 位置
- 检查设备位置（iPhone、iPad、Mac、AirPods）
- 监控宠物或物品随时间的移动（AirTag巡逻路线）

## 方法1：AppleScript + 截图（基础）

### 打开FindMy并导航

```bash
# 打开 Find My 应用
osascript -e 'tell application "FindMy" to activate'

# 等待加载
sleep 3

# 对 Find My 窗口截图
screencapture -w -o /tmp/findmy.png
```

然后使用 `vision_analyze` 读取截图：
```
vision_analyze(image_url="/tmp/findmy.png", question="显示了哪些设备/物品？它们的位置是什么？")
```

### 切换标签页

```bash
# 切换到设备标签页
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Devices" of toolbar 1 of window 1
    end tell
end tell'

# 切换到物品标签页（AirTag）
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
```

## 方法2：Peekaboo UI自动化（推荐）

如果安装了 `peekaboo`，使用它进行更可靠的UI交互：

```bash
# 打开 Find My
osascript -e 'tell application "FindMy" to activate'
sleep 3

# 捕获并标注UI
peekaboo see --app "FindMy" --annotate --path /tmp/findmy-ui.png

# 按元素ID点击特定设备/物品
peekaboo click --on B3 --app "FindMy"

# 捕获详情视图
peekaboo image --app "FindMy" --path /tmp/findmy-detail.png
```

然后通过视觉分析：
```
vision_analyze(image_url="/tmp/findmy-detail.png", question="此设备/物品显示的位置是什么？包括地址和坐标（如果可见）。")
```

## 工作流：随时间追踪AirTag位置

用于监控AirTag（例如，追踪猫的巡逻路线）：

```bash
# 1. 打开FindMy到物品标签页
osascript -e 'tell application "FindMy" to activate'
sleep 3

# 2. 点击AirTag物品（保持页面打开 — AirTag仅在页面打开时更新位置）

# 3. 定期捕获位置
while true; do
    screencapture -w -o /tmp/findmy-$(date +%H%M%S).png
    sleep 300  # 每5分钟
done
```

分析每张截图以提取坐标，然后编译路线。

## 限制

- FindMy **没有CLI或API** — 必须使用UI自动化
- AirTag仅在FindMy页面主动显示时更新位置
- 位置精度取决于FindMy网络中附近的Apple设备
- 截图需要屏幕录制权限
- AppleScript UI自动化可能在macOS版本间失效

## 规则

1. 追踪AirTag时保持FindMy应用在前台（最小化时更新会停止）
2. 使用 `vision_analyze` 读取截图内容 — 不要尝试解析像素
3. 对于持续追踪，使用cronjob定期捕获和记录位置
4. 尊重隐私 — 仅追踪用户拥有的设备/物品

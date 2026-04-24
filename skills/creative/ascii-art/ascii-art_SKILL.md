---
name: ascii-art
description: 使用pyfiglet（571种字体）、cowsay、boxes、toilet、图片转ASCII、远程API（asciified、ascii.co.uk）和LLM备选生成ASCII艺术。无需API密钥。
version: 4.0.0
author: 0xbyt4, Hermes Agent
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [ASCII, 艺术, 横幅, 创意, Unicode, 文本艺术, pyfiglet, figlet, cowsay, boxes]
    related_skills: [excalidraw]
---

# ASCII艺术技能

多种工具满足不同的ASCII艺术需求。所有工具都是本地CLI程序或免费REST API — 无需API密钥。

## 工具1：文本横幅（pyfiglet — 本地）

将文本渲染为大型ASCII艺术横幅。内置571种字体。

### 安装

```bash
pip install pyfiglet --break-system-packages -q
```

### 使用

```bash
python3 -m pyfiglet "YOUR TEXT" -f slant
python3 -m pyfiglet "TEXT" -f doom -w 80    # 设置宽度
python3 -m pyfiglet --list_fonts             # 列出所有571种字体
```

### 推荐字体

| 风格 | 字体 | 适用于 |
|-------|------|----------|
| 简洁现代 | `slant` | 项目名称、标题 |
| 粗体块状 | `doom` | 标题、徽标 |
| 大而清晰 | `big` | 横幅 |
| 经典横幅 | `banner3` | 宽屏显示 |
| 紧凑 | `small` | 副标题 |
| 赛博朋克 | `cyberlarge` | 科技主题 |
| 3D效果 | `3-d` | 启动画面 |
| 哥特式 | `gothic` | 戏剧性文本 |

### 技巧

- 预览2-3种字体让用户选择最喜欢的
- 短文本（1-8字符）最适合 `doom` 或 `block` 等详细字体
- 长文本更适合 `small` 或 `mini` 等紧凑字体

## 工具2：文本横幅（asciified API — 远程，无需安装）

免费REST API，将文本转换为ASCII艺术。250+种FIGlet字体。直接返回纯文本 — 无需解析。当pyfiglet未安装或作为快速替代时使用。

### 使用（通过终端curl）

```bash
# 基本文本横幅（默认字体）
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello+World"

# 指定字体
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Slant"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Doom"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Star+Wars"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=3-D"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Banner3"

# 列出所有可用字体（返回JSON数组）
curl -s "https://asciified.thelicato.io/api/v2/fonts"
```

### 技巧

- 在text参数中将空格URL编码为 `+`
- 响应是纯文本ASCII艺术 — 无JSON包装，可直接显示
- 字体名称区分大小写；使用fonts端点获取准确名称
- 任何有curl的终端都可用 — 无需Python或pip

## 工具3：Cowsay（消息艺术）

经典工具，将文本包装在带有ASCII角色的对话气泡中。

### 安装

```bash
sudo apt install cowsay -y    # Debian/Ubuntu
# brew install cowsay         # macOS
```

### 使用

```bash
cowsay "Hello World"
cowsay -f tux "Linux rules"       # Tux企鹅
cowsay -f dragon "Rawr!"          # 龙
cowsay -f stegosaurus "Roar!"     # 剑龙
cowthink "Hmm..."                  # 思考气泡
cowsay -l                          # 列出所有角色
```

### 可用角色（50+）

`beavis.zen`, `bong`, `bunny`, `cheese`, `daemon`, `default`, `dragon`,
`dragon-and-cow`, `elephant`, `eyes`, `flaming-skull`, `ghostbusters`,
`hellokitty`, `kiss`, `kitty`, `koala`, `luke-koala`, `mech-and-cow`,
`meow`, `moofasa`, `moose`, `ren`, `sheep`, `skeleton`, `small`,
`stegosaurus`, `stimpy`, `supermilker`, `surgery`, `three-eyes`,
`turkey`, `turtle`, `tux`, `udder`, `vader`, `vader-koala`, `www`

### 眼睛/舌头修饰符

```bash
cowsay -b "Borg"       # =_= 眼睛
cowsay -d "Dead"       # x_x 眼睛
cowsay -g "Greedy"     # $_$ 眼睛
cowsay -p "Paranoid"   # @_@ 眼睛
cowsay -s "Stoned"     # *_* 眼睛
cowsay -w "Wired"      # O_O 眼睛
cowsay -e "OO" "Msg"   # 自定义眼睛
cowsay -T "U " "Msg"   # 自定义舌头
```

## 工具4：Boxes（装饰边框）

在任何文本周围绘制装饰性ASCII艺术边框/框架。70+种内置设计。

### 安装

```bash
sudo apt install boxes -y    # Debian/Ubuntu
# brew install boxes         # macOS
```

### 使用

```bash
echo "Hello World" | boxes                    # 默认框
echo "Hello World" | boxes -d stone           # 石框
echo "Hello World" | boxes -d parchment       # 羊皮纸卷轴
echo "Hello World" | boxes -d cat             # 猫框
echo "Hello World" | boxes -d dog             # 狗框
echo "Hello World" | boxes -d unicornsay      # 独角兽
echo "Hello World" | boxes -d diamonds        # 钻石图案
echo "Hello World" | boxes -d c-cmt           # C风格注释
echo "Hello World" | boxes -d html-cmt        # HTML注释
echo "Hello World" | boxes -a c               # 居中文本
boxes -l                                       # 列出所有70+设计
```

### 与pyfiglet或asciified结合

```bash
python3 -m pyfiglet "HERMES" -f slant | boxes -d stone
# 或未安装pyfiglet时：
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=HERMES&font=Slant" | boxes -d stone
```

## 工具5：TOIlet（彩色文本艺术）

类似pyfiglet但带有ANSI颜色效果和视觉滤镜。非常适合终端视觉美化。

### 安装

```bash
sudo apt install toilet toilet-fonts -y    # Debian/Ubuntu
# brew install toilet                      # macOS
```

### 使用

```bash
toilet "Hello World"                    # 基本文本艺术
toilet -f bigmono12 "Hello"            # 指定字体
toilet --gay "Rainbow!"                 # 彩虹着色
toilet --metal "Metal!"                 # 金属效果
toilet -F border "Bordered"             # 添加边框
toilet -F border --gay "Fancy!"         # 组合效果
toilet -f pagga "Block"                 # 块状字体（toilet独有）
toilet -F list                          # 列出可用滤镜
```

### 滤镜

`crop`, `gay`（彩虹）, `metal`, `flip`, `flop`, `180`, `left`, `right`, `border`

**注意**：toilet输出带颜色的ANSI转义码 — 在终端中有效，但可能在某些上下文（如纯文本文件、某些聊天平台）中无法渲染。

## 工具6：图片转ASCII艺术

将图片（PNG、JPEG、GIF、WEBP）转换为ASCII艺术。

### 选项A：ascii-image-converter（推荐，现代）

```bash
# 安装
sudo snap install ascii-image-converter
# 或：go install github.com/TheZoraiz/ascii-image-converter@latest
```

```bash
ascii-image-converter image.png                  # 基本
ascii-image-converter image.png -C               # 彩色输出
ascii-image-converter image.png -d 60,30         # 设置尺寸
ascii-image-converter image.png -b               # 盲文字符
ascii-image-converter image.png -n               # 负片/反色
ascii-image-converter https://url/image.jpg      # 直接URL
ascii-image-converter image.png --save-txt out   # 保存为文本
```

### 选项B：jp2a（轻量，仅JPEG）

```bash
sudo apt install jp2a -y
jp2a --width=80 image.jpg
jp2a --colors image.jpg              # 彩色
```

## 工具7：搜索预制ASCII艺术

从网络搜索策划的ASCII艺术。使用 `terminal` 和 `curl`。

### 来源A：ascii.co.uk（推荐预制艺术）

大量经典ASCII艺术集合，按主题组织。艺术在HTML `<pre>` 标签内。用curl获取页面，然后用小段Python提取艺术。

**URL模式：** `https://ascii.co.uk/art/{subject}`

**步骤1 — 获取页面：**

```bash
curl -s 'https://ascii.co.uk/art/cat' -o /tmp/ascii_art.html
```

**步骤2 — 从pre标签提取艺术：**

```python
import re, html
with open('/tmp/ascii_art.html') as f:
    text = f.read()
arts = re.findall(r'<pre[^>]*>(.*?)</pre>', text, re.DOTALL)
for art in arts:
    clean = re.sub(r'<[^>]+>', '', art)
    clean = html.unescape(clean).strip()
    if len(clean) > 30:
        print(clean)
        print('\n---\n')
```

**可用主题**（用作URL路径）：
- 动物：`cat`, `dog`, `horse`, `bird`, `fish`, `dragon`, `snake`, `rabbit`, `elephant`, `dolphin`, `butterfly`, `owl`, `wolf`, `bear`, `penguin`, `turtle`
- 物品：`car`, `ship`, `airplane`, `rocket`, `guitar`, `computer`, `coffee`, `beer`, `cake`, `house`, `castle`, `sword`, `crown`, `key`
- 自然：`tree`, `flower`, `sun`, `moon`, `star`, `mountain`, `ocean`, `rainbow`
- 角色：`skull`, `robot`, `angel`, `wizard`, `pirate`, `ninja`, `alien`
- 节日：`christmas`, `halloween`, `valentine`

**技巧：**
- 保留艺术家签名/缩写 — 重要礼仪
- 每页多件艺术品 — 为用户选择最好的
- 通过curl可靠工作，无需JavaScript

### 来源B：GitHub Octocat API（趣味彩蛋）

返回随机GitHub Octocat和智慧名言。无需认证。

```bash
curl -s https://api.github.com/octocat
```

## 工具8：趣味ASCII工具（通过curl）

这些免费服务直接返回ASCII艺术 — 非常适合趣味附加内容。

### ASCII艺术二维码

```bash
curl -s "qrenco.de/Hello+World"
curl -s "qrenco.de/https://example.com"
```

### ASCII艺术天气

```bash
curl -s "wttr.in/London"          # 完整天气报告，带ASCII图形
curl -s "wttr.in/Moon"            # ASCII艺术月相
curl -s "v2.wttr.in/London"       # 详细版本
```

## 工具9：LLM生成自定义艺术（备选）

当上述工具无法满足需求时，使用这些Unicode字符直接生成ASCII艺术：

### 字符调色板

**框线绘制：** `╔ ╗ ╚ ╝ ║ ═ ╠ ╣ ╦ ╩ ╬ ┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼ ╭ ╮ ╰ ╯`

**块元素：** `░ ▒ ▓ █ ▄ ▀ ▌ ▐ ▖ ▗ ▘ ▝ ▚ ▞`

**几何与符号：** `◆ ◇ ◈ ● ○ ◉ ■ □ ▲ △ ▼ ▽ ★ ☆ ✦ ✧ ◀ ▶ ◁ ▷ ⬡ ⬢ ⌂`

### 规则

- 最大宽度：每行60字符（终端安全）
- 最大高度：横幅15行，场景25行
- 仅等宽字体：输出必须在固定宽度字体中正确渲染

## 决策流程

1. **文本作为横幅** → 已安装pyfiglet则使用，否则通过curl使用asciified API
2. **用趣味角色包装消息** → cowsay
3. **添加装饰边框/框架** → boxes（可与pyfiglet/asciified结合）
4. **特定事物的艺术**（猫、火箭、龙）→ 通过curl + 解析使用ascii.co.uk
5. **将图片转换为ASCII** → ascii-image-converter或jp2a
6. **二维码** → 通过curl使用qrenco.de
7. **天气/月亮艺术** → 通过curl使用wttr.in
8. **自定义/创意内容** → 使用Unicode调色板进行LLM生成
9. **任何工具未安装** → 安装它，或回退到下一个选项

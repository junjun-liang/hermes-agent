---
name: p5js
description: "使用 p5.js 创建交互式和生成式视觉艺术的制作流水线。创建基于浏览器的草图、生成艺术、数据可视化、交互体验、3D 场景、音频响应式视觉效果和动态图形——导出为 HTML、PNG、GIF、MP4 或 SVG。涵盖：2D/3D 渲染、噪声和粒子系统、流场、着色器（GLSL）、像素操作、动态排版、WebGL 场景、音频分析、鼠标/键盘交互和无头高分辨率导出。当用户请求：p5.js 草图、创意编程、生成艺术、交互式可视化、画布动画、基于浏览器的视觉艺术、数据可视化、着色器效果或任何 p5.js 项目时使用。"
version: 1.0.0
metadata:
  hermes:
    tags: [creative-coding, generative-art, p5js, canvas, interactive, visualization, webgl, shaders, animation]
    related_skills: [ascii-video, manim-video, excalidraw]
---

# p5.js 制作流水线

## 创意标准

这是在浏览器中渲染的视觉艺术。画布是媒介；算法是画笔。

**在编写任何代码之前**，阐明创意概念。这件作品传达了什么？什么让观看者停止滚动？这与代码教程示例有何不同？用户的提示是起点——用创意雄心解读它。

**首次渲染的卓越表现是不可妥协的。** 输出必须在首次加载时就具有视觉冲击力。如果它看起来像 p5.js 教程练习、默认配置或"AI 生成的创意编程"，那就是错误的。在交付之前重新思考。

**超越参考词汇。** 参考中的噪声函数、粒子系统、调色板和着色器效果是起始词汇。对于每个项目，组合、分层和发明。目录是颜料调色板——你创作绘画。

**主动创意。** 如果用户要求"一个粒子系统"，交付一个具有涌现群体行为、拖尾幽灵回声、调色板偏移深度雾和呼吸背景噪声场的粒子系统。包含至少一个用户没有要求但会欣赏的视觉细节。

**密集、分层、经过深思熟虑。** 每一帧都应该值得观看。绝不要扁平白色背景。始终是构图层次结构。始终是有意的颜色。始终有只在仔细检查时才出现的微细节。

**连贯的美学胜过功能数量。** 所有元素必须服务于统一的视觉语言——共享色温、一致的描边权重词汇、和谐的运动速度。带有十个不相关效果的草图比有三个相互关联效果的草图更差。

## 模式

| 模式 | 输入 | 输出 | 参考 |
|------|-------|--------|-----------|
| **生成艺术** | 种子/参数 | 程序化视觉构图（静态或动画） | `references/visual-effects.md` |
| **数据可视化** | 数据集/API | 交互式图表、图形、自定义数据显示 | `references/interaction.md` |
| **交互体验** | 无（用户驱动） | 鼠标/键盘/触摸驱动的草图 | `references/interaction.md` |
| **动画/动态图形** | 时间线/故事板 | 定时序列、动态排版、过渡 | `references/animation.md` |
| **3D 场景** | 概念描述 | WebGL 几何、光照、相机、材质 | `references/webgl-and-3d.md` |
| **图像处理** | 图像文件 | 像素操作、滤镜、马赛克、点彩 | `references/visual-effects.md` § 像素操作 |
| **音频响应式** | 音频文件/麦克风 | 声音驱动的生成式视觉效果 | `references/interaction.md` § 音频输入 |

## 技术栈

每个项目使用单个自包含的 HTML 文件。不需要构建步骤。

| 层 | 工具 | 用途 |
|-------|------|---------|
| 核心 | p5.js 1.11.3 (CDN) | 画布渲染、数学、变换、事件处理 |
| 3D | p5.js WebGL 模式 | 3D 几何、相机、光照、GLSL 着色器 |
| 音频 | p5.sound.js (CDN) | FFT 分析、振幅、麦克风输入、振荡器 |
| 导出 | 内置 `saveCanvas()` / `saveGif()` / `saveFrames()` | PNG、GIF、帧序列输出 |
| 捕获 | CCapture.js（可选） | 确定性帧率视频捕获（WebM、GIF） |
| 无头 | Puppeteer + Node.js（可选） | 自动高分辨率渲染、通过 ffmpeg 输出 MP4 |
| SVG | p5.js-svg 1.6.0（可选） | 用于打印的矢量输出——需要 p5.js 1.x |
| 自然媒介 | p5.brush（可选） | 水彩、木炭、钢笔——需要 p5.js 2.x + WEBGL |
| 纹理 | p5.grain（可选） | 胶片颗粒、纹理叠加 |
| 字体 | Google Fonts / `loadFont()` | 通过 OTF/TTF/WOFF2 自定义排版 |

### 版本说明

**p5.js 1.x**（1.11.3）是默认版本——稳定、文档齐全、最广泛的库兼容性。除非项目需要 2.x 功能，否则使用此版本。

**p5.js 2.x**（2.2+）新增：`async setup()` 替代 `preload()`、OKLCH/OKLAB 颜色模式、`splineVertex()`、着色器 `.modify()` API、可变字体、`textToContours()`、指针事件。p5.brush 需要此版本。参见 `references/core-api.md` § p5.js 2.0。

## 流水线

每个项目都遵循相同的 6 阶段路径：

```
CONCEPT → DESIGN → CODE → PREVIEW → EXPORT → VERIFY
```

1. **CONCEPT**——阐明创意愿景：情绪、色彩世界、运动词汇、什么让这个独特
2. **DESIGN**——选择模式、画布大小、交互模型、颜色系统、导出格式。将概念映射到技术决策
3. **CODE**——编写单个 HTML 文件，内联 p5.js。结构：全局变量 → `preload()` → `setup()` → `draw()` → 辅助函数 → 类 → 事件处理程序
4. **PREVIEW**——在浏览器中打开，验证视觉质量。在目标分辨率下测试。检查性能
5. **EXPORT**——捕获输出：`saveCanvas()` 用于 PNG，`saveGif()` 用于 GIF，`saveFrames()` + ffmpeg 用于 MP4，Puppeteer 用于无头批量
6. **VERIFY**——输出是否匹配概念？在预期显示尺寸下是否具有视觉冲击力？你会把它装裱起来吗？

## 创意方向

### 美学维度

| 维度 | 选项 | 参考 |
|-----------|---------|-----------|
| **颜色系统** | HSB/HSL、RGB、命名调色板、程序和谐、渐变插值 | `references/color-systems.md` |
| **噪声词汇** | Perlin 噪声、simplex、分形（八度）、域扭曲、旋度噪声 | `references/Visual-effects.md` § 噪声 |
| **粒子系统** | 基于物理、群体、拖尾绘制、吸引子驱动、流场跟随 | `references/Visual-effects.md` § 粒子 |
| **形状语言** | 几何基元、自定义顶点、贝塞尔曲线、SVG 路径 | `references/shapes-and-geometry.md` |
| **运动风格** | 缓动、基于弹簧、噪声驱动、物理模拟、插值、步进 | `references/animation.md` |
| **排版** | 系统字体、加载的 OTF、`textToPoints()` 粒子文本、动态 | `references/typography.md` |
| **着色器效果** | GLSL 片段/顶点、滤镜着色器、后处理、反馈循环 | `references/webgl-and-3d.md` § 着色器 |
| **构图** | 网格、径向、黄金分割、三分法则、有机散射、平铺 | `references/core-api.md` § 构图 |
| **交互模型** | 鼠标跟随、点击生成、拖动、键盘状态、滚动驱动、麦克风输入 | `references/interaction.md` |
| **混合模式** | `BLEND`、`ADD`、`MULTIPLY`、`SCREEN`、`DIFFERENCE`、`EXCLUSION`、`OVERLAY` | `references/color-systems.md` § 混合模式 |
| **分层** | `createGraphics()` 离屏缓冲区、Alpha 合成、遮罩 | `references/core-api.md` § 离屏缓冲区 |
| **纹理** | Perlin 表面、点画法、交叉影线、半调、像素排序 | `references/Visual-effects.md` § 纹理生成 |

### 每项目变化规则

绝不要使用默认配置。对于每个项目：
- **自定义调色板**——绝不要原始 `fill(255, 0, 0)`。始终是设计的 3-7 色调色板
- **自定义描边权重词汇**——细强调线（0.5）、中等结构（1-2）、粗强调（3-5）
- **背景处理**——绝不要纯 `background(0)` 或 `background(255)`。始终有纹理、渐变或分层
- **运动多样性**——不同元素不同速度。主要 1 倍，次要 0.3 倍，环境 0.1 倍
- **至少一个发明元素**——自定义粒子行为、新颖噪声应用、独特交互响应

### 项目特定发明

对于每个项目，至少发明一个：
- 匹配情绪的自定义调色板（不是预设）
- 新颖的噪声场组合（如旋度噪声 + 域扭曲 + 反馈）
- 独特的粒子行为（自定义力、自定义拖尾、自定义生成）
- 用户没有要求但提升作品的交互机制
- 创建视觉层次的构图技术

### 参数设计哲学

参数应该从算法中涌现，而不是来自通用菜单。问："*这个*系统的什么属性应该是可调的？"

**好参数**揭示算法的特征：
- **数量**——多少粒子、分支、单元格（控制密度）
- **尺度**——噪声频率、元素大小、间距（控制纹理）
- **速率**——速度、增长率、衰减（控制能量）
- **阈值**——行为何时改变？（控制戏剧性）
- **比率**——比例、力之间的平衡（控制和声）

**坏参数**是与算法无关的通用控制：
- "color1"、"color2"、"size"——没有上下文就没有意义
- 不相关效果的开关
- 仅改变外观而非行为的参数

每个参数都应该改变算法的*思考方式*，而不仅仅是*外观*。改变噪声八度的"湍流"参数是好的。仅改变 `ellipse()` 半径的"粒子大小"滑块是肤浅的。

## 工作流

### 步骤 1：创意愿景

在任何代码之前，阐明：

- **情绪/氛围**：观看者应该感受到什么？沉思？充满活力？不安？有趣？
- **视觉故事**：随着时间（或交互）会发生什么？建立？衰减？转换？振荡？
- **色彩世界**：暖/冷？单色？互补？什么是主色调？什么是强调色？
- **形状语言**：有机曲线？锐利几何？点？线？混合？
- **运动词汇**：缓慢漂移？爆发爆炸？呼吸脉冲？机械精度？
- **什么让这个不同**：什么让这个草图独一无二？

将用户的提示映射到美学选择。"放松的生成背景"与"故障数据可视化"的要求完全不同。

### 步骤 2：技术设计

- **模式**——上表中的 7 种模式之一
- **画布大小**——横向 1920x1080、纵向 1080x1920、方形 1080x1080，或响应式 `windowWidth/windowHeight`
- **渲染器**——`P2D`（默认）或 `WEBGL`（用于 3D、着色器、高级混合模式）
- **帧率**——60fps（交互式）、30fps（环境动画）或 `noLoop()`（静态生成）
- **导出目标**——浏览器显示、PNG 静态、GIF 循环、MP4 视频、SVG 矢量
- **交互模型**——被动（无输入）、鼠标驱动、键盘驱动、音频响应、滚动驱动
- **查看器 UI**——对于交互式生成艺术，从 `templates/viewer.html` 开始，它提供种子导航、参数滑块和下载。对于简单草图或视频导出，使用裸 HTML

### 步骤 3：编写草图

对于**交互式生成艺术**（种子探索、参数调整）：从 `templates/viewer.html` 开始。首先阅读模板，保持固定部分（种子导航、操作），替换算法和参数控制。这为用户提供种子上/下/随机/跳转、实时更新参数滑块和 PNG 下载——全部连接好。

对于**动画、视频导出或简单草图**：使用裸 HTML：

单个 HTML 文件。结构：

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Project Name</title>
  <script>p5.disableFriendlyErrors = true;</script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/p5.min.js"></script>
  <!-- <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/addons/p5.sound.min.js"></script> -->
  <!-- <script src="https://unpkg.com/p5.js-svg@1.6.0"></script> -->  <!-- SVG 导出 -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/ccapture.js-npmfixed/build/CCapture.all.min.js"></script> -->  <!-- 视频捕获 -->
  <style>
    html, body { margin: 0; padding: 0; overflow: hidden; }
    canvas { display: block; }
  </style>
</head>
<body>
<script>
// === 配置 ===
const CONFIG = {
  seed: 42,
  // ... 项目特定参数
};

// === 调色板 ===
const PALETTE = {
  bg: '#0a0a0f',
  primary: '#e8d5b7',
  // ...
};

// === 全局状态 ===
let particles = [];

// === 预加载（字体、图像、数据） ===
function preload() {
  // font = loadFont('...');
}

// === 设置 ===
function setup() {
  createCanvas(1920, 1080);
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  colorMode(HSB, 360, 100, 100, 100);
  // 初始化状态...
}

// === 绘制循环 ===
function draw() {
  // 渲染帧...
}

// === 辅助函数 ===
// ...

// === 类 ===
class Particle {
  // ...
}

// === 事件处理程序 ===
function mousePressed() { /* ... */ }
function keyPressed() { /* ... */ }
function windowResized() { resizeCanvas(windowWidth, windowHeight); }
</script>
</body>
</html>
```

关键实现模式：
- **种子随机性**：始终 `randomSeed()` + `noiseSeed()` 以确保可复现
- **颜色模式**：使用 `colorMode(HSB, 360, 100, 100, 100)` 进行直观的颜色控制
- **状态分离**：CONFIG 用于参数，PALETTE 用于颜色，全局变量用于可变状态
- **基于类的实体**：粒子、代理、形状作为带有 `update()` + `display()` 方法的类
- **离屏缓冲区**：`createGraphics()` 用于分层构图、拖尾、遮罩

### 步骤 4：预览与迭代

- 直接在浏览器中打开 HTML 文件——基本草图不需要服务器
- 对于从本地文件 `loadImage()`/`loadFont()`：使用 `scripts/serve.sh` 或 `python3 -m http.server`
- Chrome DevTools 性能标签验证 60fps
- 在目标导出分辨率下测试，而不仅仅是窗口大小
- 调整参数直到视觉匹配步骤 1 中的概念

### 步骤 5：导出

| 格式 | 方法 | 命令 |
|--------|--------|---------|
| **PNG** | `saveCanvas('output', 'png')` 在 `keyPressed()` 中 | 按 's' 保存 |
| **高分辨率 PNG** | Puppeteer 无头捕获 | `node scripts/export-frames.js sketch.html --width 3840 --height 2160 --frames 1` |
| **GIF** | `saveGif('output', 5)`——捕获 N 秒 | 按 'g' 保存 |
| **帧序列** | `saveFrames('frame', 'png', 10, 30)`——30fps 下 10 秒 | 然后 `ffmpeg -i frame-%04d.png -c:v libx264 output.mp4` |
| **MP4** | Puppeteer 帧捕获 + ffmpeg | `bash scripts/render.sh sketch.html output.mp4 --duration 30 --fps 30` |
| **SVG** | `createCanvas(w, h, SVG)` 配合 p5.js-svg | `save('output.svg')` |

### 步骤 6：质量验证

- **是否匹配愿景？** 将输出与创意概念对比。如果看起来通用，返回步骤 1
- **分辨率检查**：在目标显示尺寸下是否清晰？没有锯齿伪影？
- **性能检查**：在浏览器中是否保持 60fps？（动画最低 30fps）
- **颜色检查**：颜色是否协调？在明亮和黑暗显示器上测试
- **边界情况**：画布边缘会发生什么？调整大小时如何？运行 10 分钟后呢？

## 关键实现说明

### 性能——首先禁用 FES

友好错误系统（FES）增加多达 10 倍开销。在每个生产草图中禁用它：

```javascript
p5.disableFriendlyErrors = true;  // 在 setup() 之前

function setup() {
  pixelDensity(1);  // 防止视网膜上 2-4 倍过度绘制
  createCanvas(1920, 1080);
}
```

在热循环中（粒子、像素操作），使用 `Math.*` 而非 p5 包装器——明显更快：

```javascript
// 在 draw() 或 update() 热路径中：
let a = Math.sin(t);          // 不是 sin(t)
let r = Math.sqrt(dx*dx+dy*dy); // 不是 dist()——或者更好：跳过 sqrt，比较 magSq
let v = Math.random();        // 不是 random()——当不需要种子时
let m = Math.min(a, b);       // 不是 min(a, b)
```

绝不要在 `draw()` 中使用 `console.log()`。绝不要在 `draw()` 中操作 DOM。参见 `references/troubleshooting.md` § 性能。

### 种子随机性——始终

每个生成草图必须是可复现的。相同种子，相同输出。

```javascript
function setup() {
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  // 所有 random() 和 noise() 调用现在是确定性的
}
```

绝不要对生成内容使用 `Math.random()`——仅用于性能关键的非视觉代码。始终对视觉元素使用 `random()`。如果需要随机种子：`CONFIG.seed = floor(random(99999))`。

### 生成艺术平台支持（fxhash / Art Blocks）

对于生成艺术平台，将 p5 的 PRNG 替换为平台的确定性随机：

```javascript
// fxhash 约定
const SEED = $fx.hash;              // 每次铸造唯一
const rng = $fx.rand;               // 确定性 PRNG
$fx.features({ palette: 'warm', complexity: 'high' });

// 在 setup() 中：
randomSeed(SEED);   // 用于 p5 的 noise()
noiseSeed(SEED);

// 用 rng() 替换 random() 以实现平台确定性
let x = rng() * width;  // 而不是 random(width)
```

参见 `references/export-pipeline.md` § 平台导出。

### 颜色模式——使用 HSB

HSB（色相、饱和度、亮度）在生成艺术中比 RGB 容易得多：

```javascript
colorMode(HSB, 360, 100, 100, 100);
// 现在：fill(hue, sat, bri, alpha)
// 旋转色相：fill((baseHue + offset) % 360, 80, 90)
// 降低饱和度：fill(hue, sat * 0.3, bri)
// 变暗：fill(hue, sat, bri * 0.5)
```

绝不要硬编码原始 RGB 值。定义调色板对象，程序化派生变化。参见 `references/color-systems.md`。

### 噪声——多八度，而非原始

原始 `noise(x, y)` 看起来像平滑斑点。分层八度以获得自然纹理：

```javascript
function fbm(x, y, octaves = 4) {
  let val = 0, amp = 1, freq = 1, sum = 0;
  for (let i = 0; i < octaves; i++) {
    val += noise(x * freq, y * freq) * amp;
    sum += amp;
    amp *= 0.5;
    freq *= 2;
  }
  return val / sum;
}
```

对于流动的有机形态，使用**域扭曲**：将噪声输出反馈为噪声输入坐标。参见 `references/visual-effects.md`。

### createGraphics() 用于分层——不是可选的

扁平单遍渲染看起来扁平。使用离屏缓冲区进行构图：

```javascript
let bgLayer, fgLayer, trailLayer;
function setup() {
  createCanvas(1920, 1080);
  bgLayer = createGraphics(width, height);
  fgLayer = createGraphics(width, height);
  trailLayer = createGraphics(width, height);
}
function draw() {
  renderBackground(bgLayer);
  renderTrails(trailLayer);   // 持久，淡出
  renderForeground(fgLayer);  // 每帧清除
  image(bgLayer, 0, 0);
  image(trailLayer, 0, 0);
  image(fgLayer, 0, 0);
}
```

### 性能——尽可能向量化

p5.js 绘制调用很昂贵。对于数千个粒子：

```javascript
// 慢：单个形状
for (let p of particles) {
  ellipse(p.x, p.y, p.size);
}

// 快：单个 beginShape()
beginShape(POINTS);
for (let p of particles) {
  vertex(p.x, p.y);
}
endShape();

// 最快：海量计数的像素缓冲区
loadPixels();
for (let p of particles) {
  let idx = 4 * (floor(p.y) * width + floor(p.x));
  pixels[idx] = r; pixels[idx+1] = g; pixels[idx+2] = b; pixels[idx+3] = 255;
}
updatePixels();
```

参见 `references/troubleshooting.md` § 性能。

### 多草图使用实例模式

全局模式污染 `window`。对于生产，使用实例模式：

```javascript
const sketch = (p) => {
  p.setup = function() {
    p.createCanvas(800, 800);
  };
  p.draw = function() {
    p.background(0);
    p.ellipse(p.mouseX, p.mouseY, 50);
  };
};
new p5(sketch, 'canvas-container');
```

当在一个页面上嵌入多个草图或与框架集成时需要。

### WebGL 模式陷阱

- `createCanvas(w, h, WEBGL)`——原点在中心，而非左上角
- Y 轴反转（WEBGL 中正 Y 向上，P2D 中向下）
- `translate(-width/2, -height/2)` 以获得类似 P2D 的坐标
- 每次变换周围使用 `push()`/`pop()`——矩阵栈会静默溢出
- `rect()`/`plane()` 之前使用 `texture()`——而不是之后
- 自定义着色器：`createShader(vert, frag)`——在多个浏览器上测试

### 导出——键绑定约定

每个草图应在 `keyPressed()` 中包含这些：

```javascript
function keyPressed() {
  if (key === 's' || key === 'S') saveCanvas('output', 'png');
  if (key === 'g' || key === 'G') saveGif('output', 5);
  if (key === 'r' || key === 'R') { randomSeed(millis()); noiseSeed(millis()); }
  if (key === ' ') CONFIG.paused = !CONFIG.paused;
}
```

### 无头视频导出——使用 noLoop()

对于通过 Puppeteer 的无头渲染，草图**必须**在 setup 中使用 `noLoop()`。没有它，p5 的绘制循环自由运行而截图很慢——草图跑得超前，你会得到跳过/重复的帧。

```javascript
function setup() {
  createCanvas(1920, 1080);
  pixelDensity(1);
  noLoop();                    // 捕获脚本控制帧前进
  window._p5Ready = true;      // 向捕获脚本发出就绪信号
}
```

捆绑的 `scripts/export-frames.js` 检测 `_p5Ready` 并每次捕获调用一次 `redraw()`，以实现精确的 1:1 帧对应。参见 `references/export-pipeline.md` § 确定性捕获。

对于多场景视频，使用每片段架构：每个场景一个 HTML，独立渲染，通过 `ffmpeg -f concat` 拼接。参见 `references/export-pipeline.md` § 每片段架构。

### Agent 工作流

构建 p5.js 草图时：

1. **编写 HTML 文件**——单个自包含文件，所有代码内联
2. **在浏览器中打开**——`open sketch.html`（macOS）或 `xdg-open sketch.html`（Linux）
3. **本地资源**（字体、图像）需要服务器：在项目目录中 `python3 -m http.server 8080`，然后打开 `http://localhost:8080/sketch.html`
4. **导出 PNG/GIF**——如上添加 `keyPressed()` 快捷方式，告诉用户按哪个键
5. **无头导出**——`node scripts/export-frames.js sketch.html --frames 300` 用于自动帧捕获（草图必须使用 `noLoop()` + `_p5Ready`）
6. **MP4 渲染**——`bash scripts/render.sh sketch.html output.mp4 --duration 30`
7. **迭代优化**——编辑 HTML 文件，用户刷新浏览器查看更改
8. **按需加载参考**——使用 `skill_view(name="p5js", file_path="references/...")` 在实现期间按需加载特定参考文件

## 性能目标

| 指标 | 目标 |
|--------|--------|
| 帧率（交互式） | 持续 60fps |
| 帧率（动画导出） | 最低 30fps |
| 粒子数（P2D 形状） | 60fps 下 5,000-10,000 |
| 粒子数（像素缓冲区） | 60fps 下 50,000-100,000 |
| 画布分辨率 | 高达 3840x2160（导出）、1920x1080（交互式） |
| 文件大小（HTML） | < 100KB（不包括 CDN 库） |
| 加载时间 | < 2 秒到第一帧 |

## 参考资料

| 文件 | 内容 |
|------|----------|
| `references/core-api.md` | 画布设置、坐标系统、绘制循环、`push()`/`pop()`、离屏缓冲区、构图模式、`pixelDensity()`、响应式设计 |
| `references/shapes-and-geometry.md` | 2D 基元、`beginShape()`/`endShape()`、贝塞尔/Catmull-Rom 曲线、`vertex()` 系统、自定义形状、`p5.Vector`、有符号距离场、SVG 路径转换 |
| `references/visual-effects.md` | 噪声（Perlin、分形、域扭曲、旋度）、流场、粒子系统（物理、群体、拖尾）、像素操作、纹理生成（点画法、交叉影线、半调）、反馈循环、反应扩散 |
| `references/animation.md` | 基于帧的动画、缓动函数、`lerp()`/`map()`、弹簧物理、状态机、时间线序列、基于 `millis()` 的计时、过渡模式 |
| `references/typography.md` | `text()`、`loadFont()`、`textToPoints()`、动态排版、文本遮罩、字体度量、响应式文本调整 |
| `references/color-systems.md` | `colorMode()`、HSB/HSL/RGB、`lerpColor()`、`paletteLerp()`、程序调色板、颜色和声、`blendMode()`、渐变渲染、精选调色板库 |
| `references/webgl-and-3d.md` | WEBGL 渲染器、3D 基元、相机、光照、材质、自定义几何、GLSL 着色器（`createShader()`、`createFilterShader()`）、帧缓冲区、后处理 |
| `references/interaction.md` | 鼠标事件、键盘状态、触摸输入、DOM 元素、`createSlider()`/`createButton()`、音频输入（p5.sound FFT/振幅）、滚动驱动动画、响应式事件 |
| `references/export-pipeline.md` | `saveCanvas()`、`saveGif()`、`saveFrames()`、确定性无头捕获、ffmpeg 帧到视频、CCapture.js、SVG 导出、每片段架构、平台导出（fxhash）、视频陷阱 |
| `references/troubleshooting.md` | 性能分析、每像素预算、常见错误、浏览器兼容性、WebGL 调试、字体加载问题、像素密度陷阱、内存泄漏、CORS |
| `templates/viewer.html` | 交互式查看器模板：种子导航（上/下/随机/跳转）、参数滑块、下载 PNG、响应式画布。从可探索的生成艺术开始 |

---

## 创意发散（仅在用户请求实验性/创意性/独特输出时使用）

如果用户要求创意、实验性、令人惊讶或非传统的输出，选择最适合的策略并在生成代码之前推理其步骤。

- **概念混合**——当用户命名两个要组合的事物或想要混合美学时
- **SCAMPER**——当用户想要对已知生成艺术模式进行创新时
- **距离关联**——当用户给出单个概念并想要探索时（"做一些关于时间的东西"）

### 概念混合
1. 命名两个不同的视觉系统（如粒子物理 + 手写）
2. 映射对应关系（粒子 = 墨滴、力 = 笔压、场 = 字母形式）
3. 选择性地混合——保留产生有趣涌现视觉效果的映射
4. 将混合编码为统一系统，而非两个系统并排

### SCAMPER 转换
采用已知生成模式（流场、粒子系统、L 系统、细胞自动机）并系统转换它：
- **替代**：用文本字符替换圆形，用渐变替换线条
- **组合**：合并两种模式（流场 + voronoi）
- **适应**：将 2D 模式应用于 3D 投影
- **修改**：夸张尺度、扭曲坐标空间
- **目的**：将物理模拟用于排版、将排序算法用于颜色
- **消除**：移除网格、移除颜色、移除对称性
- **反转**：反向运行模拟、反转参数空间

### 距离关联
1. 锚定用户的概念（如"孤独"）
2. 在三个距离生成关联：
   - 近（明显）：空房间、单人、沉默
   - 中（有趣）：一条游错方向的鱼群中的鱼、没有通知的手机、地铁车厢之间的间隙
   - 远（抽象）：质数、渐近曲线、凌晨 3 点的颜色
3. 发展中距离关联——它们足够具体可以可视化，但足够意外而有趣

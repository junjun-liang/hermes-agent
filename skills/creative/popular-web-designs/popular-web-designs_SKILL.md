---
name: popular-web-designs
description: >
  从真实网站中提取的54个生产级设计系统。加载模板以生成与 Stripe、Linear、Vercel、Notion、Airbnb 等网站视觉身份匹配的 HTML/CSS。每个模板都包含颜色、排版、组件、布局规则和现成的 CSS 值。
version: 1.0.0
author: Hermes Agent + Teknium（设计系统来源于 VoltAgent/awesome-design-md）
license: MIT
tags: [design, css, html, ui, web-development, design-systems, templates]
triggers:
  - build a page that looks like
  - make it look like stripe
  - design like linear
  - vercel style
  - create a UI
  - web design
  - landing page
  - dashboard design
  - website styled like
---

# 流行网页设计

54 个真实世界的设计系统，可在生成 HTML/CSS 时使用。每个模板都捕获网站的完整视觉语言：调色板、排版层次结构、组件样式、间距系统、阴影、响应式行为，以及带有精确 CSS 值的实用 agent 提示。

## 使用方法

1. 从下面的目录中选择设计
2. 加载：`skill_view(name="popular-web-designs", file_path="templates/<site>.md")`
3. 生成 HTML 时使用设计令牌和组件规范
4. 配合 `generative-widgets` 技能通过 cloudflared 隧道提供服务

每个模板在顶部都包含一个 **Hermes 实现说明** 块：
- CDN 字体替代方案和 Google Fonts `<link>` 标签（可直接粘贴）
- 主要字体和等宽字体的 CSS font-family 堆栈
- 提醒使用 `write_file` 创建 HTML 和使用 `browser_vision` 进行验证

## HTML 生成模式

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
  <!-- 从模板的 Hermes 说明中粘贴 Google Fonts <link> -->
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
  <style>
    /* 应用模板的调色板作为 CSS 自定义属性 */
    :root {
      --color-bg: #ffffff;
      --color-text: #171717;
      --color-accent: #533afd;
      /* ... 更多来自模板第 2 节 */
    }
    /* 应用模板第 3 节的排版 */
    body {
      font-family: 'Inter', system-ui, sans-serif;
      color: var(--color-text);
      background: var(--color-bg);
    }
    /* 应用模板第 4 节的组件样式 */
    /* 应用模板第 5 节的布局 */
    /* 应用模板第 6 节的阴影 */
  </style>
</head>
<body>
  <!-- 使用模板中的组件规范构建 -->
</body>
</html>
```

使用 `write_file` 写入文件，通过 `generative-widgets` 工作流（cloudflared 隧道）提供服务，并使用 `browser_vision` 验证结果以确认视觉准确性。

## 字体替代参考

大多数网站使用无法通过 CDN 获取的专有字体。每个模板都映射到保留设计特征的 Google Fonts 替代方案。常见映射：

| 专有字体 | CDN 替代 | 特征 |
|---|---|---|
| Geist / Geist Sans | Geist（在 Google Fonts 上） | 几何、压缩字距 |
| Geist Mono | Geist Mono（在 Google Fonts 上） | 干净等宽、连字 |
| sohne-var (Stripe) | Source Sans 3 | 轻量优雅 |
| Berkeley Mono | JetBrains Mono | 技术等宽 |
| Airbnb Cereal VF | DM Sans | 圆润、友好的几何体 |
| Circular (Spotify) | DM Sans | 几何、温暖 |
| figmaSans | Inter | 干净的人文主义 |
| Pin Sans (Pinterest) | DM Sans | 友好、圆润 |
| NVIDIA-EMEA | Inter（或 Arial 系统） | 工业、干净 |
| CoinbaseDisplay/Sans | DM Sans | 几何、可信 |
| UberMove | DM Sans | 粗体、紧凑 |
| HashiCorp Sans | Inter | 企业、中性 |
| waldenburgNormal (Sanity) | Space Grotesk | 几何、略紧凑 |
| IBM Plex Sans/Mono | IBM Plex Sans/Mono | 可在 Google Fonts 上获取 |
| Rubik (Sentry) | Rubik | 可在 Google Fonts 上获取 |

当模板的 CDN 字体与原始字体匹配时（Inter、IBM Plex、Rubik、Geist），不会发生替代损失。当使用替代方案时（DM Sans 替代 Circular、Source Sans 3 替代 sohne-var），请密切遵循模板的字重、大小和字母间距值——这些比具体的字体面承载更多视觉身份。

## 设计目录

### AI 与机器学习

| 模板 | 网站 | 风格 |
|---|---|---|
| `claude.md` | Anthropic Claude | 温暖赤陶强调色、干净的编辑布局 |
| `cohere.md` | Cohere | 鲜艳渐变、数据丰富的仪表板美学 |
| `elevenlabs.md` | ElevenLabs | 暗黑电影感 UI、音频波形美学 |
| `minimax.md` | Minimax | 大胆暗黑界面配霓虹强调色 |
| `mistral.ai.md` | Mistral AI | 法国工程极简主义、紫色调 |
| `ollama.md` | Ollama | 终端优先、单色简约 |
| `opencode.ai.md` | OpenCode AI | 开发者中心的暗黑主题、全等宽 |
| `replicate.md` | Replicate | 干净白色画布、代码导向 |
| `runwayml.md` | RunwayML | 电影感暗黑 UI、媒体丰富布局 |
| `together.ai.md` | Together AI | 技术感、蓝图风格设计 |
| `voltagent.md` | VoltAgent | 虚空黑画布、翠绿强调色、终端原生 |
| `x.ai.md` | xAI | 鲜明单色、未来主义极简、全等宽 |

### 开发者工具与平台

| 模板 | 网站 | 风格 |
|---|---|---|
| `cursor.md` | Cursor | 流畅暗黑界面、渐变强调色 |
| `expo.md` | Expo | 暗黑主题、紧凑字母间距、代码中心 |
| `linear.app.md` | Linear | 超极简暗色模式、精确、紫色强调 |
| `lovable.md` | Lovable | 有趣渐变、友好的开发者美学 |
| `mintlify.md` | Mintlify | 干净、绿色强调、阅读优化 |
| `posthog.md` | PostHog | 有趣品牌、开发者友好的暗黑 UI |
| `raycast.md` | Raycast | 流畅暗黑铬色、鲜艳渐变强调 |
| `resend.md` | Resend | 极简暗黑主题、等宽强调 |
| `sentry.md` | Sentry | 暗黑仪表板、数据密集、粉紫强调色 |
| `supabase.md` | Supabase | 暗黑翠绿主题、代码优先开发者工具 |
| `superhuman.md` | Superhuman | 高级暗黑 UI、键盘优先、紫色光晕 |
| `vercel.md` | Vercel | 黑白精度、Geist 字体系统 |
| `warp.md` | Warp | 暗黑类 IDE 界面、基于块的命令 UI |
| `zapier.md` | Zapier | 温暖橙色、友好的插图驱动 |

### 基础设施与云

| 模板 | 网站 | 风格 |
|---|---|---|
| `clickhouse.md` | ClickHouse | 黄色强调、技术文档风格 |
| `composio.md` | Composio | 现代暗黑配彩色集成图标 |
| `hashicorp.md` | HashiCorp | 企业级干净、黑白 |
| `mongodb.md` | MongoDB | 绿叶品牌、开发者文档中心 |
| `sanity.md` | Sanity | 红色强调、内容优先编辑布局 |
| `stripe.md` | Stripe | 标志性紫色渐变、300 字重优雅 |

### 设计与生产力

| 模板 | 网站 | 风格 |
|---|---|---|
| `airtable.md` | Airtable | 多彩、友好、结构化数据美学 |
| `cal.md` | Cal.com | 干净中性 UI、面向开发者的简约 |
| `clay.md` | Clay | 有机形状、柔和渐变、艺术指导布局 |
| `figma.md` | Figma | 鲜艳多色、有趣而专业 |
| `framer.md` | Framer | 大胆黑白蓝、动效优先、设计导向 |
| `intercom.md` | Intercom | 友好蓝色调色板、对话式 UI 模式 |
| `miro.md` | Miro | 明亮黄色强调、无限画布美学 |
| `notion.md` | Notion | 温暖极简主义、衬线标题、柔和表面 |
| `pinterest.md` | Pinterest | 红色强调、瀑布流网格、图像优先布局 |
| `webflow.md` | Webflow | 蓝色强调、精致的营销网站美学 |

### 金融科技与加密货币

| 模板 | 网站 | 风格 |
|---|---|---|
| `coinbase.md` | Coinbase | 干净蓝色身份、信任导向、机构感 |
| `kraken.md` | Kraken | 紫色强调暗黑 UI、数据密集仪表板 |
| `revolut.md` | Revolut | 流畅暗黑界面、渐变卡片、金融科技精度 |
| `wise.md` | Wise | 明亮绿色强调、友好清晰 |

### 企业与消费

| 模板 | 网站 | 风格 |
|---|---|---|
| `airbnb.md` | Airbnb | 温暖珊瑚强调色、摄影驱动、圆润 UI |
| `apple.md` | Apple | 高级留白、SF Pro、电影感图像 |
| `bmw.md` | BMW | 暗黑高级表面、精密工程美学 |
| `ibm.md` | IBM | Carbon 设计系统、结构化蓝色调色板 |
| `nvidia.md` | NVIDIA | 绿黑能量感、技术力量美学 |
| `spacex.md` | SpaceX | 鲜明黑白、满版图像、未来感 |
| `spotify.md` | Spotify | 鲜艳绿色配暗黑、粗体排版、专辑封面驱动 |
| `uber.md` | Uber | 大胆黑白、紧凑排版、都市能量 |

## 选择设计

将设计与内容匹配：

- **开发者工具/仪表板：** Linear、Vercel、Supabase、Raycast、Sentry
- **文档/内容站点：** Mintlify、Notion、Sanity、MongoDB
- **营销/落地页：** Stripe、Framer、Apple、SpaceX
- **暗黑模式 UI：** Linear、Cursor、ElevenLabs、Warp、Superhuman
- **明亮/干净 UI：** Vercel、Stripe、Notion、Cal.com、Replicate
- **有趣/友好：** PostHog、Figma、Lovable、Zapier、Miro
- **高级/奢华：** Apple、BMW、Stripe、Superhuman、Revolut
- **数据密集/仪表板：** Sentry、Kraken、Cohere、ClickHouse
- **等宽/终端美学：** Ollama、OpenCode、x.ai、VoltAgent

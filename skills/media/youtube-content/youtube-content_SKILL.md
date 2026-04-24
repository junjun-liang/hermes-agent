---
name: youtube-content
description: 获取YouTube视频字幕并将其转换为结构化内容（章节、摘要、推文、博客文章）。当用户分享YouTube URL或视频链接、要求总结视频、请求字幕或想从任何YouTube视频提取和重新格式化内容时使用。
---

# YouTube内容工具

从YouTube视频提取字幕并转换为有用的格式。

## 设置

```bash
pip install youtube-transcript-api
```

## 辅助脚本

`SKILL_DIR`是包含此SKILL.md文件的目录。脚本接受任何标准YouTube URL格式、短链接（youtu.be）、shorts、embeds、live链接，或原始11位视频ID。

```bash
# 带元数据的JSON输出
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# 纯文本（适合管道到进一步处理）
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# 带时间戳
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# 特定语言带回退链
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## 输出格式

获取字幕后，根据用户要求格式化：

- **章节**：按主题转变分组，输出带时间戳的章节列表
- **摘要**：整个视频的5-10句简明概述
- **章节摘要**：每章带短段落摘要
- **推文**：Twitter/X推文格式 — 编号帖子，每篇少于280字符
- **博客文章**：完整文章带标题、章节和关键要点
- **名言**：带时间戳的著名语录

### 示例 — 章节输出

```
00:00 介绍 — 主持人以问题陈述开始
03:45 背景 — 先前工作和为什么现有解决方案不足
12:20 核心方法 — 介绍所提出的方法
24:10 结果 — 基准比较和关键要点
31:55 问答 — 观众关于可扩展性和下一步的问题
```

## 工作流程

1. **获取**字幕，使用辅助脚本带`--text-only --timestamps`。
2. **验证**：确认输出非空且为预期语言。如果为空，重试时不带`--language`获取任何可用字幕。如果仍为空，告知用户视频可能禁用了字幕。
3. **如需要分块**：如果字幕超过约50,000字符，拆分为重叠块（约40,000字符，2,000字符重叠），在合并前总结每个块。
4. **转换**为请求的输出格式。如果用户未指定格式，默认为摘要。
5. **验证**：重新阅读转换输出，检查连贯性、正确的时间戳和完整性，然后再呈现。

## 错误处理

- **字幕已禁用**：告知用户；建议他们检查视频页面是否有可用字幕。
- **视频私有/不可用**：转达错误并要求用户验证URL。
- **无匹配语言**：重试时不带`--language`获取任何可用字幕，然后向用户注明实际语言。
- **依赖缺失**：运行`pip install youtube-transcript-api`并重试。

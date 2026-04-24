---
name: llm-wiki
description: "Karpathy 的 LLM Wiki — 构建和维护持久的、相互链接的 markdown 知识库。摄取来源、查询已编译的知识，并进行一致性检查。"
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wiki, knowledge-base, research, notes, markdown, rag-alternative]
    category: research
    related_skills: [obsidian, arxiv, agentic-research-ideas]
    config:
      - key: wiki.path
        description: LLM Wiki 知识库目录路径
        default: "~/wiki"
        prompt: Wiki 目录路径
---

# Karpathy 的 LLM Wiki

构建和维护持久的、不断累积的知识库，以相互链接的 markdown 文件形式存储。
基于 [Andrej Karpathy 的 LLM Wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。

与传统 RAG（每次查询从头重新发现知识）不同，wiki
一次性编译知识并保持更新。交叉引用已经存在。
矛盾已经被标记。综合反映了所有摄取的内容。

**分工：** 人类策划来源和指导分析。代理
总结、交叉引用、归档并维护一致性。

## 何时激活此技能

当用户以下情况时使用此技能：
- 请求创建、构建或启动 wiki 或知识库
- 请求将来源摄取、添加或处理到 wiki 中
- 提出问题且配置的路径下存在现有 wiki
- 请求 lint、审计或健康检查 wiki
- 在研究上下文中引用 wiki、知识库或"笔记"

## Wiki 位置

通过 `~/.hermes/config.yaml` 中的 `skills.config.wiki.path` 配置（在
`hermes config migrate` 或 `hermes setup` 期间提示）：

```yaml
skills:
  config:
    wiki:
      path: ~/wiki
```

回退到默认值 `~/wiki`。解析后的路径在此技能加载时注入 — 检查上方的 `[Skill config: ...]` 块以获取活动值。

wiki 只是一个 markdown 文件目录 — 在 Obsidian、VS Code 或
任何编辑器中打开它。无需数据库，不需要特殊工具。

## 架构：三个层级

```
wiki/
├── SCHEMA.md           # 约定、结构规则、领域配置
├── index.md            # 带一行摘要的分节内容目录
├── log.md              # 按时间顺序的操作日志（仅追加，每年轮换）
├── raw/                # 层级 1：不可变的原始资料
│   ├── articles/       # 网络文章、剪报
│   ├── papers/         # PDF、arxiv 论文
│   ├── transcripts/    # 会议笔记、访谈
│   └── assets/         # 来源引用的图像、图表
├── entities/           # 层级 2：实体页面（人物、组织、产品、模型）
├── concepts/           # 层级 2：概念/主题页面
├── comparisons/        # 层级 2：并排分析
└── queries/            # 层级 2：值得保留的查询结果
```

**层级 1 — 原始资料：** 不可变。代理读取但从不修改这些。
**层级 2 — Wiki：** 代理拥有的 markdown 文件。由代理创建、更新和交叉引用。
**层级 3 — 模式：** `SCHEMA.md` 定义结构、约定和标签分类。

## 恢复现有 Wiki（关键 — 每次会话都这样做）

当用户有现有 wiki 时，**在做任何事情之前总是先定位自己**：

① **阅读 `SCHEMA.md`** — 了解领域、约定和标签分类。
② **阅读 `index.md`** — 了解存在哪些页面及其摘要。
③ **扫描最近的 `log.md`** — 阅读最后 20-30 条条目以了解最近活动。

```bash
WIKI="${wiki_path:-$HOME/wiki}"
# 会话开始时的定位读取
read_file "$WIKI/SCHEMA.md"
read_file "$WIKI/index.md"
read_file "$WIKI/log.md" offset=<最后 30 行>
```

只有在定位后才应该摄取、查询或 lint。这可以防止：
- 为已存在的实体创建重复页面
- 错过与现有内容的交叉引用
- 与模式的约定矛盾
- 重复已记录的工作

对于大型 wiki（100+ 页面），在创建任何新内容之前，还要对当前主题运行快速 `search_files`。

## 初始化新 Wiki

当用户请求创建或启动 wiki 时：

1. 确定 wiki 路径（来自配置、环境变量或询问用户；默认 `~/wiki`）
2. 创建上述目录结构
3. 询问用户 wiki 涵盖什么领域 — 要具体
4. 编写针对领域定制的 `SCHEMA.md`（见下方模板）
5. 编写带分节标题的初始 `index.md`
6. 编写带创建条目的初始 `log.md`
7. 确认 wiki 已就绪并建议要摄取的首批来源

### SCHEMA.md 模板

根据用户领域调整。模式约束代理行为并确保一致性：

```markdown
# Wiki 模式

## 领域
[此 wiki 涵盖的内容 — 例如，"AI/ML 研究"、"个人健康"、"初创公司情报"]

## 约定
- 文件名：小写、连字符、无空格（如 `transformer-architecture.md`）
- 每个 wiki 页面以 YAML frontmatter 开头（见下方）
- 使用 `[[wikilinks]]` 在页面之间链接（每页最少 2 个出站链接）
- 更新页面时，始终更新 `updated` 日期
- 每个新页面必须添加到 `index.md` 的正确部分下
- 每个操作必须追加到 `log.md`

## Frontmatter
  ```yaml
  ---
  title: 页面标题
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  type: entity | concept | comparison | query | summary
  tags: [来自下方分类]
  sources: [raw/articles/source-name.md]
  ---
  ```

## 标签分类
[为领域定义 10-20 个顶级标签。在使用前先添加新标签。]

AI/ML 示例：
- 模型：model, architecture, benchmark, training
- 人物/组织：person, company, lab, open-source
- 技术：optimization, fine-tuning, inference, alignment, data
- 元：comparison, timeline, controversy, prediction

规则：页面上的每个标签必须出现在此分类中。如果需要新标签，
先添加到这里，然后使用它。这可以防止标签蔓延。

## 页面阈值
- **创建页面**：当实体/概念出现在 2+ 来源中或是一个来源的核心时
- **添加到现有页面**：当来源提到已涵盖的内容时
- **不要创建页面**：对于短暂提及、次要细节或领域外的内容
- **拆分页面**：当超过 ~200 行时 — 拆分为带交叉链接的子主题
- **归档页面**：当内容完全被取代时 — 移动到 `_archive/`，从索引中移除

## 实体页面
每个显著实体一个页面。包括：
- 概述 / 是什么
- 关键事实和日期
- 与其他实体的关系（[[wikilinks]]）
- 来源引用

## 概念页面
每个概念或主题一个页面。包括：
- 定义 / 解释
- 当前知识状态
- 未决问题或争论
- 相关概念（[[wikilinks]]）

## 比较页面
并排分析。包括：
- 比较什么及为什么
- 比较维度（首选表格格式）
- 结论或综合
- 来源

## 更新策略
当新信息与现有内容冲突时：
1. 检查日期 — 较新的来源通常取代较旧的
2. 如果真正矛盾，注明两种立场及日期和来源
3. 在 frontmatter 中标记矛盾：`contradictions: [page-name]`
4. 在 lint 报告中标记供用户审查
```

### index.md 模板

索引按类型分节。每个条目一行：wikilink + 摘要。

```markdown
# Wiki 索引

> 内容目录。每个 wiki 页面列在其类型下，带一行摘要。
> 任何查询请先阅读此文件以找到相关页面。
> 最后更新：YYYY-MM-DD | 总页数：N

## 实体
<!-- 每个部分内按字母顺序排列 -->

## 概念

## 比较

## 查询
```

**扩展规则：** 当任何部分超过 50 个条目时，按首字母或子领域拆分为子部分。
当索引总条目超过 200 时，创建 `_meta/topic-map.md` 按主题对页面分组以便更快导航。

### log.md 模板

```markdown
# Wiki 日志

> 所有 wiki 操作的按时间顺序记录。仅追加。
> 格式：`## [YYYY-MM-DD] action | subject`
> 操作：ingest, update, query, lint, create, archive, delete
> 当此文件超过 500 个条目时，轮换：重命名为 log-YYYY.md，重新开始。

## [YYYY-MM-DD] create | Wiki 初始化
- 领域：[domain]
- 创建了带 SCHEMA.md、index.md、log.md 的结构
```

## 核心操作

### 1. 摄取

当用户提供来源（URL、文件、粘贴文本）时，将其集成到 wiki：

① **捕获原始来源：**
   - URL → 使用 `web_extract` 获取 markdown，保存到 `raw/articles/`
   - PDF → 使用 `web_extract`（处理 PDF），保存到 `raw/papers/`
   - 粘贴文本 → 保存到适当的 `raw/` 子目录
   - 描述性命名文件：`raw/articles/karpathy-llm-wiki-2026.md`

② **与用户讨论要点** — 什么有趣，什么对领域重要。（在自动/cron 上下文中跳过此步骤 — 直接继续。）

③ **检查已存在的内容** — 搜索 index.md 并使用 `search_files` 查找已提到的实体/概念的现有页面。这是不断增长的 wiki 和重复堆积之间的区别。

④ **编写或更新 wiki 页面：**
   - **新实体/概念：** 仅在满足 SCHEMA.md 中的页面阈值时创建页面（2+ 来源提及，或一个来源的核心）
   - **现有页面：** 添加新信息，更新事实，更新 `updated` 日期。当新信息矛盾现有内容时，遵循更新策略。
   - **交叉引用：** 每个新或更新的页面必须通过 `[[wikilinks]]` 链接到至少 2 个其他页面。检查现有页面是否反向链接。
   - **标签：** 仅使用 SCHEMA.md 分类中的标签

⑤ **更新导航：**
   - 将新页面按字母顺序添加到 `index.md` 的正确部分下
   - 更新索引头部中的"总页数"和"最后更新"日期
   - 追加到 `log.md`：`## [YYYY-MM-DD] ingest | 来源标题`
   - 在日志条目中列出创建或更新的每个文件

⑥ **报告变更** — 向用户列出创建或更新的每个文件。

单个来源可以触发 5-15 个 wiki 页面的更新。这是正常的且是期望的 — 这就是复合效应。

### 2. 查询

当用户询问 wiki 领域的问题时：

① **阅读 `index.md`** 以识别相关页面。
② **对于 100+ 页面的 wiki**，还要在所有 `.md` 文件中 `search_files` 搜索关键术语 — 仅索引可能错过相关内容。
③ **使用 `read_file` 阅读相关页面。**
④ **从编译的知识中综合答案。** 引用来源的 wiki 页面："基于 [[page-a]] 和 [[page-b]]..."
⑤ **将有价值的答案归档回来** — 如果答案是实质性的比较、深度分析或新综合，在 `queries/` 或 `comparisons/` 中创建页面。不要归档琐碎的查找 — 仅归档重新推导会很痛苦的答案。
⑥ **更新 log.md** 记录查询及是否归档。

### 3. Lint

当用户请求 lint、健康检查或审计 wiki 时：

① **孤立页面：** 查找没有其他页面传入 `[[wikilinks]]` 的页面。
```python
# 为此使用 execute_code — 对所有 wiki 页面进行编程扫描
import os, re
from collections import defaultdict
wiki = "<WIKI_PATH>"
# 扫描 entities/、concepts/、comparisons/、queries/ 中的所有 .md 文件
# 提取所有 [[wikilinks]] — 构建入站链接映射
# 入站链接为零的页面是孤立的
```

② **断开的 wikilinks：** 查找指向不存在页面的 `[[links]]`。

③ **索引完整性：** 每个 wiki 页面应出现在 `index.md` 中。将文件系统与索引条目进行比较。

④ **Frontmatter 验证：** 每个 wiki 页面必须有所有必填字段（title、created、updated、type、tags、sources）。标签必须在分类中。

⑤ **过期内容：** `updated` 日期比提及相同实体的最新来源早 >90 天的页面。

⑥ **矛盾：** 同一主题但有冲突声明的页面。查找共享标签/实体但陈述不同事实的页面。

⑦ **页面大小：** 标记超过 200 行的页面 — 拆分候选。

⑧ **标签审计：** 列出所有使用的标签，标记任何不在 SCHEMA.md 分类中的标签。

⑨ **日志轮换：** 如果 log.md 超过 500 个条目，轮换它。

⑩ **报告结果**，带具体文件路径和建议操作，按严重程度分组（断开的链接 > 孤立 > 过期内容 > 样式问题）。

⑪ **追加到 log.md：** `## [YYYY-MM-DD] lint | 发现 N 个问题`

## 使用 Wiki

### 搜索

```bash
# 按内容查找页面
search_files "transformer" path="$WIKI" file_glob="*.md"

# 按文件名查找页面
search_files "*.md" target="files" path="$WIKI"

# 按标签查找页面
search_files "tags:.*alignment" path="$WIKI" file_glob="*.md"

# 最近活动
read_file "$WIKI/log.md" offset=<最后 20 行>
```

### 批量摄取

当一次摄取多个来源时，批量更新：
1. 先读取所有来源
2. 识别所有来源中的所有实体和概念
3. 对所有内容检查现有页面（一次搜索，而不是 N 次）
4. 一次遍历中创建/更新页面（避免冗余更新）
5. 最后更新 index.md 一次
6. 编写涵盖批量的单个日志条目

### 归档

当内容完全被取代或领域范围变更时：
1. 如果不存在则创建 `_archive/` 目录
2. 将页面移动到 `_archive/` 并保留原始路径（如 `_archive/entities/old-page.md`）
3. 从 `index.md` 中移除
4. 更新任何链接到它的页面 — 将 wikilink 替换为纯文本 + "(已归档)"
5. 记录归档操作

### Obsidian 集成

wiki 目录开箱即用地作为 Obsidian 库工作：
- `[[wikilinks]]` 呈现为可点击链接
- 图谱可视化知识网络
- YAML frontmatter 支持 Dataview 查询
- `raw/assets/` 文件夹存放通过 `![[image.png]]` 引用的图像

最佳实践：
- 将 Obsidian 的附件文件夹设置为 `raw/assets/`
- 在 Obsidian 设置中启用"Wikilinks"（通常默认开启）
- 安装 Dataview 插件用于查询，如 `TABLE tags FROM "entities" WHERE contains(tags, "company")`

如果与此技能一起使用 Obsidian 技能，将 `OBSIDIAN_VAULT_PATH` 设置为与 wiki 路径相同的目录。

### Obsidian Headless（服务器和无头机器）

在没有显示器的机器上，使用 `obsidian-headless` 而不是桌面应用。
它通过 Obsidian Sync 同步库而无需 GUI — 非常适合在服务器上运行的代理写入 wiki，而 Obsidian 桌面在另一台设备上读取。

**设置：**
```bash
# 需要 Node.js 22+
npm install -g obsidian-headless

# 登录（需要带 Sync 订阅的 Obsidian 账户）
ob login --email <email> --password '<password>'

# 为 wiki 创建远程库
ob sync-create-remote --name "LLM Wiki"

# 将 wiki 目录连接到库
cd ~/wiki
ob sync-setup --vault "<vault-id>"

# 初始同步
ob sync

# 持续同步（前台 — 使用 systemd 作为后台）
ob sync --continuous
```

**通过 systemd 持续后台同步：**
```ini
# ~/.config/systemd/user/obsidian-wiki-sync.service
[Unit]
Description=Obsidian LLM Wiki 同步
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/path/to/ob sync --continuous
WorkingDirectory=/home/user/wiki
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now obsidian-wiki-sync
# 启用 linger 使同步在注销后继续：
sudo loginctl enable-linger $USER
```

这让代理在服务器上写入 `~/wiki`，同时你在笔记本/手机上通过 Obsidian 浏览相同的库 — 变更在几秒内出现。

## 陷阱

- **永远不要修改 `raw/` 中的文件** — 来源是不可变的。更正放在 wiki 页面中。
- **始终先定位** — 在新会话中的任何操作之前阅读 SCHEMA + index + 最近的日志。跳过这会导致重复和错过交叉引用。
- **始终更新 index.md 和 log.md** — 跳过这会导致 wiki 退化。这些是导航的骨干。
- **不要为短暂提及创建页面** — 遵循 SCHEMA.md 中的页面阈值。在脚注中出现一次的名称不值得实体页面。
- **不要创建不带交叉引用的页面** — 孤立页面是隐形的。每页必须链接到至少 2 个其他页面。
- **Frontmatter 是必需的** — 它支持搜索、过滤和过期检测。
- **标签必须来自分类** — 自由格式的标签会退化为噪声。先将新标签添加到 SCHEMA.md，然后使用它们。
- **保持页面可扫描** — wiki 页面应在 30 秒内可读。拆分超过 200 行的页面。将详细分析移动到专门的深度页面。
- **大规模更新前询问** — 如果摄取会触及 10+ 现有页面，先与用户确认范围。
- **轮换日志** — 当 log.md 超过 500 个条目时，重命名为 `log-YYYY.md` 并重新开始。代理应在 lint 期间检查日志大小。
- **明确处理矛盾** — 不要静默覆盖。注明两种声明及日期，在 frontmatter 中标记，标记供用户审查。

---
name: research-paper-writing
title: 研究论文写作流水线
description: 面向 ML/AI 研究论文的端到端流水线——从实验设计到分析、草稿、修订和提交。涵盖 NeurIPS、ICML、ICLR、ACL、AAAI、COLM。集成自动实验监控、统计分析、迭代写作和引文验证。
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [semanticscholar, arxiv, habanero, requests, scipy, numpy, matplotlib, SciencePlots]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [研究, 论文写作, 实验, 机器学习, 人工智能, NeurIPS, ICML, ICLR, ACL, AAAI, COLM, LaTeX, 引文, 统计分析]
    category: 研究
    related_skills: [arxiv, ml-paper-writing, subagent-driven-development, plan]
    requires_toolsets: [终端, 文件]

---

# 研究论文写作流水线

面向 **NeurIPS、ICML、ICLR、ACL、AAAI 和 COLM** 的端到端 ML/AI 研究论文生产流水线。本技能涵盖完整的研究生命周期：实验设计、执行、监控、分析、论文写作、评审、修订和提交。

这不是一个线性流水线——而是一个迭代循环。结果会触发新实验。评审会触发新分析。Agent 必须处理这些反馈循环。

```
┌─────────────────────────────────────────────────────────────┐
│                      研究论文流水线                          │
│                                                             │
│  阶段 0: 项目设置 ──► 阶段 1: 文献综述                       │
│       │                          │                          │
│       ▼                          ▼                          │
│  阶段 2: 实验      阶段 5: 论文草稿 ◄──┐                    │
│       设计                    │         │                    │
│       │                      ▼         │                    │
│       ▼                阶段 6: 自审      │                    │
│  阶段 3: 执行与           与修订 ────────┘                    │
│       监控                    │                              │
│       │                      ▼                              │
│       ▼                阶段 7: 提交                          │
│  阶段 4: 分析 ─────► (反馈到阶段 2 或 5)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 何时使用本技能

适用于以下场景：
- **从零开始新的研究论文**，基于现有代码库或想法
- **设计和运行实验** 以支持论文主张
- **撰写或修订** 研究论文的任何章节
- **准备提交** 到特定会议或研讨会
- **回复评审意见** 并进行额外实验或修订
- **在不同会议格式之间转换** 论文
- **撰写非实证论文**——理论、综述、基准测试或立场论文（参见[超越实证 ML 的论文类型](#paper-types-beyond-empirical-ml)）
- **为 NLP、HCI 或对齐研究设计人类评估**
- **准备录用后的材料**——海报、演讲、代码发布

## 核心理念

1. **主动出击。** 交付完整的草稿，而非提出问题。科学家很忙——拿出具体成果供他们反馈，然后迭代。
2. **绝不捏造引文。** AI 生成的引文错误率约 40%。务必通过编程获取。将不可验证的引文标记为 `[CITATION NEEDED]`。
3. **论文是故事，而非实验合集。** 每篇论文都需要一个清晰的核心贡献，用一句话陈述。如果做不到，论文还没准备好。
4. **实验服务于主张。** 每个实验必须明确说明支持哪个主张。绝不运行与论文叙事无关的实验。
5. **尽早、频繁提交。** 每完成一批实验、每次论文草稿更新——都要用描述性消息提交。Git 日志就是实验历史。

### 主动性与协作

**默认：主动出击。先写草稿，带着草稿提问。**

| 置信度级别 | 行动 |
|-----------------|--------|
| **高**（代码库清晰，贡献明确） | 撰写完整草稿，交付，根据反馈迭代 |
| **中**（存在一些歧义） | 撰写草稿并标记不确定之处，继续 |
| **低**（存在重大未知） | 通过 `clarify` 问 1-2 个针对性问题，然后撰写草稿 |

| 章节 | 自主起草？ | 随草稿标记 |
|---------|-------------------|-----------------|
| 摘要 | 是 | "贡献框架定为 X——如需调整请告知" |
| 引言 | 是 | "强调了问题 Y——如有误请纠正" |
| 方法 | 是 | "包含细节 A、B、C——补充缺失部分" |
| 实验 | 是 | "突出结果 1、2、3——如需重新排序请告知" |
| 相关工作 | 是 | "引用了论文 X、Y、Z——如有遗漏请告知" |

**仅在以下情况阻止并等待输入**：目标会议不明确、存在多个相互矛盾的框架、结果似乎不完整、用户明确要求先审查。

---

## 阶段 0：项目设置

**目标**：建立工作空间，理解现有工作，识别贡献。

### 步骤 0.1：探索代码库

```bash
# 理解项目结构
ls -la
find . -name "*.py" | head -30
find . -name "*.md" -o -name "*.txt" | xargs grep -l -i "result\|conclusion\|finding"
```

查找：
- `README.md`——项目概述和主张
- `results/`、`outputs/`、`experiments/`——现有发现
- `configs/`——实验设置
- `.bib` 文件——现有引文
- 草稿文档或笔记

### 步骤 0.2：组织工作空间

建立一致的工作空间结构：

```
workspace/
  paper/               # LaTeX 源文件、图表、编译后的 PDF
  experiments/         # 实验运行脚本
  code/                # 核心方法实现
  results/             # 原始实验结果（自动生成）
  tasks/               # 任务/基准测试定义
  human_eval/          # 人类评估材料（如需要）
```

### 步骤 0.3：设置版本控制

```bash
git init  # 如果尚未初始化
git remote add origin <仓库URL>
git checkout -b paper-draft  # 或 main
```

**Git 纪律**：每完成一批实验都用描述性消息提交。示例：
```
添加蒙特卡洛约束结果（5 次运行，Sonnet 4.6，策略备忘录任务）
添加 Haiku 基线比较：autoreason 与精化基线在低成本模型层的比较
```

### 步骤 0.4：识别贡献

在写任何内容之前，明确表达：
- **是什么**：这篇论文贡献的单一内容是什么？
- **为什么**：有什么证据支持它？
- **所以呢**：读者为什么要在乎？

> 向科学家提出："根据我的理解，主要贡献是：[一句话]。关键结果表明 [Y]。这是你想要的框架吗？"

### 步骤 0.5：创建待办清单

使用 `todo` 工具创建结构化项目计划：

```
研究论文待办：
- [ ] 定义一句话贡献
- [ ] 文献综述（相关工作 + 基线）
- [ ] 设计核心实验
- [ ] 运行实验
- [ ] 分析结果
- [ ] 撰写第一稿
- [ ] 自审（模拟评审）
- [ ] 根据评审修订
- [ ] 提交准备
```

在整个项目中更新。它作为跨会话的持久状态。

### 步骤 0.6：估算计算预算

在运行实验之前，估算总成本和时间：

```
计算预算清单：
- [ ] API 成本：（模型每 token 价格）×（每次运行预估 token 数）×（运行次数）
- [ ] GPU 小时：（每次实验时间）×（实验次数）×（种子数）
- [ ] 人类评估成本：（标注员数）×（小时数）×（每小时费率）
- [ ] 总预算上限和应急（增加 30-50% 用于重跑）
```

跟踪实验运行时的实际支出：
```python
# 简单成本跟踪模式
import json, os
from datetime import datetime

COST_LOG = "results/cost_log.jsonl"

def log_cost(experiment: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "experiment": experiment,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
    }
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

**预算紧张时**：先运行试点实验（1-2 个种子，任务子集），然后再进行全面扫描。使用更便宜的模型调试流水线，然后在最终运行时切换到目标模型。

### 步骤 0.7：多作者协调

大多数论文有 3-10 位作者。尽早建立工作流：

| 工作流 | 工具 | 何时使用 |
|----------|------|-------------|
| **Overleaf** | 基于浏览器 | 多位作者同时编辑，无 git 经验 |
| **Git + LaTeX** | `git` 配合 `.gitignore` 排除辅助文件 | 技术团队，需要基于分支的审查 |
| **Overleaf + Git 同步** | Overleaf 高级版 | 两者兼得——实时协作加版本历史 |

**章节所有权**：将每个章节分配给一位主要作者。其他人评论但不直接编辑。防止合并冲突和风格不一致。

```
作者协调清单：
- [ ] 同意章节所有权（谁写什么）
- [ ] 设置共享工作空间（Overleaf 或 git 仓库）
- [ ] 建立符号约定（在任何人开始写之前）
- [ ] 安排内部评审轮次（不仅在最后）
- [ ] 指定一人负责最终格式调整
- [ ] 在创建图表前统一图表风格（颜色、字体、大小）
```

**需要尽早商定的 LaTeX 约定**：
- `\method{}` 宏用于一致的方法命名
- 引文样式：`\citet{}` 与 `\citep{}` 的使用
- 数学符号：向量用小写粗体，矩阵用大写粗体等
- 英式与美式拼写

---

## 阶段 1：文献综述

**目标**：查找相关工作，识别基线，收集引文。

### 步骤 1.1：识别种子论文

从代码库中已引用的论文开始：

```bash
# 通过终端：
grep -r "arxiv\|doi\|cite" --include="*.md" --include="*.bib" --include="*.py"
find . -name "*.bib"
```

### 步骤 1.2：搜索相关工作

**加载 `arxiv` 技能** 进行结构化的论文发现：`skill_view("arxiv")`。它提供 arXiv REST API 搜索、Semantic Scholar 引文图谱、作者档案和 BibTeX 生成。

使用 `web_search` 进行广泛发现，使用 `web_extract` 获取特定论文：

```
# 通过 web_search：
web_search("[主要技术] + [应用领域] site:arxiv.org")
web_search("[基线方法] 比较 ICML NeurIPS 2024")

# 通过 web_extract（针对特定论文）：
web_extract("https://arxiv.org/abs/2303.17651")
```

其他尝试的搜索查询：

```
搜索查询：
- "[主要技术] + [应用领域]"
- "[基线方法] 比较"
- "[问题名称] 最先进"
- 现有引文中的作者名
```

**推荐**：安装 **Exa MCP** 进行实时学术搜索：
```bash
claude mcp add exa -- npx -y mcp-remote "https://mcp.exa.ai/mcp"
```

### 步骤 1.2b：深化搜索（先广度，后深度）

扁平搜索（一轮查询）通常会遗漏重要的相关工作。使用受深度研究流水线启发的迭代**先广度后深度**模式：

```
迭代文献搜索：

第 1 轮（广度）：4-6 个并行查询，涵盖不同角度
  - "[方法] + [领域]"
  - "[问题名称] 最先进 2024 2025"
  - "[基线方法] 比较"
  - "[替代方法] vs [你的方法]"
  → 收集论文，提取关键概念和术语

第 2 轮（深度）：从第 1 轮的学习中生成后续查询
  - 第 1 轮论文中发现的新术语
  - 第 1 轮最相关结果引用的论文
  - 需要调查的矛盾发现
  → 收集论文，识别剩余空白

第 3 轮（定向）：填补特定空白
  - 第 1-2 轮中识别的缺失基线
  - 同期工作（过去 6 个月，相同问题）
  - 关键的负面结果或失败方法
  → 当新查询返回大部分已见过的论文时停止
```

**何时停止**：如果一轮返回 >80% 已在你的集合中的论文，则搜索已饱和。通常 2-3 轮即可。对于综述论文，预计需要 4-5 轮。

**基于 Agent 的工作流**：通过 `delegate_task` 并行分发每轮的查询。收集结果、去重，然后从合并的学习中生成下一轮的查询。

### 步骤 1.3：验证每条引文

**绝不凭记忆生成 BibTeX。务必通过编程获取。**

对于每条引文，遵循强制性的 5 步流程：

```
引文验证（每条引文必须执行）：
1. 搜索 → 使用特定关键词查询 Semantic Scholar 或 Exa MCP
2. 验证 → 确认论文在 2+ 个来源中存在（Semantic Scholar + arXiv/CrossRef）
3. 获取 → 通过 DOI 内容协商获取 BibTeX（以编程方式，而非凭记忆）
4. 确认 → 确认你引用的主张确实出现在论文中
5. 添加 → 将已验证的 BibTeX 添加到参考文献
如果任何一步失败 → 标记为 [CITATION NEEDED]，通知科学家
```

```python
# 通过 DOI 获取 BibTeX
import requests

def doi_to_bibtex(doi: str) -> str:
    response = requests.get(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/x-bibtex"}
    )
    response.raise_for_status()
    return response.text
```

如果无法验证引文：

```latex
\cite{PLACEHOLDER_author2024_verify_this}  % TODO: 验证此引文是否存在
```

**务必告知科学家**："我已将 [X] 条引文标记为需要验证的占位符。"

完整的 API 文档和完整的 `CitationManager` 类参见 [references/citation-workflow.md](references/citation-workflow.md)。

### 步骤 1.4：组织相关工作

按方法论分组论文，而非逐篇罗列：

**好**："一个研究方向使用 X 的假设 [引用]，而我们使用 Y 的假设，因为..."
**差**："Smith 等人引入了 X。Jones 等人引入了 Y。我们结合两者。"

---

## 阶段 2：实验设计

**目标**：设计直接支持论文主张的实验。每个实验必须回答一个具体问题。

### 步骤 2.1：将主张映射到实验

创建显式映射：

| 主张 | 实验 | 预期证据 |
|-------|-----------|-------------------|
| "我们的方法优于基线" | 主要比较（表 1） | 胜率，统计显著性 |
| "较弱模型效果更明显" | 模型扩展研究 | 单调改进曲线 |
| "收敛需要范围约束" | 有约束与无约束比较 | 收敛速率比较 |

**规则**：如果实验不对应任何主张，不要运行它。

### 步骤 2.2：设计基线

强大的基线是区分被接受论文和被拒论文的关键。评审会问："他们和 X 比较了吗？"

标准基线类别：
- **朴素基线**：最简单的方法
- **强基线**：已知最佳现有方法
- **消融基线**：你的方法去掉一个组件
- **计算匹配基线**：相同计算预算，不同分配

### 步骤 2.3：定义评估协议

在运行任何内容之前，指定：
- **指标**：你测量什么，方向符号（越高越好/越低越好）
- **聚合**：如何在运行/任务之间合并结果
- **统计检验**：用什么检验建立显著性
- **样本量**：多少次运行/问题/任务

### 步骤 2.4：编写实验脚本

遵循成功研究流水线的以下模式：

**增量保存**——每步后保存结果以便崩溃恢复：
```python
# 每个问题/任务后保存
result_path = f"results/{task}/{strategy}/result.json"
if os.path.exists(result_path):
    continue  # 跳过已完成的工作
# ... 运行实验 ...
with open(result_path, 'w') as f:
    json.dump(result, f, indent=2)
```

**工件保存**——保存所有中间输出：
```
results/<实验>/
  <任务>/
    <策略>/
      final_output.md          # 最终结果
      history.json             # 完整轨迹
      pass_01/                 # 每次迭代的工件
        version_a.md
        version_b.md
        critic.md
```

**关注点分离**——将生成、评估和可视化分开：
```
run_experiment.py              # 核心实验运行器
run_baselines.py               # 基线比较
run_comparison_judge.py        # 盲评估
analyze_results.py             # 统计分析
make_charts.py                 # 可视化
```

完整的设计模式、cron 监控和错误恢复参见 [references/experiment-patterns.md](references/experiment-patterns.md)。

### 步骤 2.5：设计人类评估（如适用）

许多 NLP、HCI 和对齐论文需要人类评估作为主要或补充证据。在运行自动实验之前设计——人类评估通常有更长的准备时间（IRB 审批、标注员招募）。

**何时需要人类评估：**
- 自动指标无法捕捉你关注的内容（流畅性、有用性、安全性）
- 你的贡献关注面向人的质量（可读性、偏好、信任）
- NLP 会议（ACL、EMNLP）的评审期望生成任务包含它

**关键设计决策：**

| 决策 | 选项 | 指导 |
|----------|---------|----------|
| **标注员类型** | 专家、众包工人、最终用户 | 匹配你的主张需要什么 |
| **量表** | 李克特量表（1-5）、成对比较、排序 | 成对比对李克特量表对 LLM 输出更可靠 |
| **样本量** | 每标注员和总项目数 | 功效分析或至少 100 个项目，3+ 标注员 |
| **一致性指标** | Cohen's kappa、Krippendorff's alpha、ICC | >2 标注员用 Krippendorff's alpha；同时报告原始一致性 |
| **平台** | Prolific、MTurk、内部团队 | Prolific 保证质量；MTurk 保证规模；内部保证领域专业知识 |

**标注指南清单：**
```
- [ ] 清晰的任务描述和示例（好的和坏的）
- [ ] 模糊情况的决策标准
- [ ] 每个类别至少 2 个实际示例
- [ ] 注意力检查/黄金标准项目（占总数的 10-15%）
- [ ] 资格测试或筛选轮次
- [ ] 每项预估时间和公平补偿（>= 当地最低工资）
- [ ] 如果机构要求，进行 IRB/伦理审查
```

**报告要求**（评审会检查所有这些）：
- 标注员数量及其资质
- 标注员间一致性，包括具体指标和数值
- 补偿细节（金额、预估时薪）
- 标注界面描述或截图（附录）
- 总标注时间

完整指南（包括人类评估数据的统计检验、众包质量控制模式和 IRB 指导）参见 [references/human-evaluation.md](references/human-evaluation.md)。

---

## 阶段 3：实验执行与监控

**目标**：可靠地运行实验，监控进度，从故障中恢复。

### 步骤 3.1：启动实验

对长时间运行的实验使用 `nohup`：

```bash
nohup python run_experiment.py --config config.yaml > logs/experiment_01.log 2>&1 &
echo $!  # 记录 PID
```

**并行执行**：同时运行独立的实验，但要注意 API 速率限制。同一 API 上 4+ 个并发实验会相互拖慢。

### 步骤 3.2：设置监控（Cron 模式）

对于长时间运行的实验，设置定期状态检查。cron 提示应遵循以下模板：

```
监控提示模板：
1. 检查进程是否仍在运行：ps aux | grep <模式>
2. 读取日志最后 30 行：tail -30 <日志文件>
3. 检查已完成的结果：ls <结果目录>
4. 如果有结果，读取并报告：cat <结果文件>
5. 如果全部完成，提交：git add -A && git commit -m "<描述性消息>" && git push
6. 以结构化格式报告（包含关键指标的表格）
7. 回答该实验的关键分析问题
```

**静默模式**：如果自上次检查以来没有变化，回复 `[SILENT]` 以抑制向用户的通知。仅在有新闻时报告。

### 步骤 3.3：处理故障

常见故障模式和恢复：

| 故障 | 检测 | 恢复 |
|---------|-----------|----------|
| API 速率限制/额度耗尽 | 日志中出现 402/429 错误 | 等待，然后重跑（脚本会跳过已完成的工作） |
| 进程崩溃 | PID 消失，结果不完整 | 从最后一个检查点重跑 |
| 困难问题超时 | 进程卡住，日志无进展 | 终止并跳过，在结果中注明 |
| 错误的模型 ID | 错误引用模型名 | 修正 ID 并重跑 |

**关键**：脚本应始终检查现有结果并跳过已完成的工作。这使得重跑安全且高效。

### 步骤 3.4：提交已完成的结果

每批实验完成后：

```bash
git add -A
git commit -m "添加 <实验名>: <1 行关键发现>"
git push
```

### 步骤 3.5：维护实验日志

Git 提交跟踪发生了什么，但**不跟踪探索树**——即根据所学内容决定下一步尝试什么的决策。维护一个结构化的实验日志来捕获这棵树：

```json
// experiment_journal.jsonl — 每次实验尝试追加一条记录
{
  "id": "exp_003",
  "parent": "exp_001",
  "timestamp": "2025-05-10T14:30:00Z",
  "hypothesis": "添加范围约束将修复 exp_001 的收敛失败",
  "plan": "用 max_tokens=2000 和固定结构模板重新运行 autoreason",
  "config": {"model": "haiku", "strategy": "autoreason", "max_tokens": 2000},
  "status": "completed",
  "result_path": "results/exp_003/",
  "key_metrics": {"win_rate": 0.85, "convergence_rounds": 3},
  "analysis": "范围约束修复了收敛。胜率从 0.42 跃升到 0.85。",
  "next_steps": ["对 Sonnet 尝试相同约束", "在没有结构模板的情况下测试"],
  "figures": ["figures/exp003_convergence.pdf"]
}
```

**为什么用日志而不是仅用 git？** Git 跟踪文件更改。日志跟踪推理：为什么尝试 X，学到了什么，以及这对下一个实验意味着什么。在写论文时，这棵树对方法部分（"我们观察到 X，这促使了 Y"）和诚实的失败报告非常宝贵。

**选择最佳路径**：当日志显示分支树（exp_001 → exp_002a, exp_002b, exp_003）时，识别最能支持论文主张的路径。将死端分支记录在附录中作为消融或负面结果。

**每次实验的快照代码**：每次运行后复制实验脚本：
```bash
cp experiment.py results/exp_003/experiment_snapshot.py
```
这可以在后续代码更改后精确重现。

---

## 阶段 4：结果分析

**目标**：提取发现，计算统计量，识别故事。

### 步骤 4.1：聚合结果

编写分析脚本：
1. 从一批中加载所有结果文件
2. 计算每任务和聚合指标
3. 生成汇总表

```python
# 标准分析模式
import json, os
from pathlib import Path

results = {}
for result_file in Path("results/").rglob("result.json"):
    data = json.loads(result_file.read_text())
    strategy = result_file.parent.name
    task = result_file.parent.parent.name
    results.setdefault(strategy, {})[task] = data

# 计算聚合指标
for strategy, tasks in results.items():
    scores = [t["score"] for t in tasks.values()]
    print(f"{strategy}: mean={np.mean(scores):.1f}, std={np.std(scores):.1f}")
```

### 步骤 4.2：统计显著性

始终计算：
- **误差线**：标准差或标准误，指定是哪个
- **置信区间**：关键结果的 95% CI
- **成对检验**：比较两种方法的 McNemar 检验
- **效应量**：Cohen's d 或 h 用于实际显著性

McNemar 检验、Bootstrap CI 和 Cohen's h 的完整实现参见 [references/experiment-patterns.md](references/experiment-patterns.md)。

### 步骤 4.3：识别故事

分析后，明确回答：
1. **主要发现是什么？** 用一句话陈述。
2. **什么让你惊讶？** 意外结果往往能写出最好的论文。
3. **什么失败了？** 失败的实验可能是最有信息量的。诚实地报告失败能加强论文。
4. **需要什么后续实验？** 结果往往会引出新问题。

#### 处理负面或空结果

当你的假设错误或结果不确定时，你有三个选择：

| 情况 | 行动 | 会议匹配 |
|-----------|--------|-----------|
| 假设错误但**为什么**有信息量 | 围绕为什么的分析构建论文 | NeurIPS、ICML（如果分析严谨） |
| 方法未击败基线但**揭示了新东西** | 将贡献重新定义为理解/分析 | ICLR（重视理解）、研讨会论文 |
| 对流行主张的干净负面结果 | 写出来——领域需要知道 | NeurIPS 数据集与基准测试、TMLR、研讨会 |
| 结果不确定，没有清晰故事 | 转向——运行不同实验或重新定义 | 不要强行写一篇不存在的论文 |

**如何撰写负面结果论文：**
- 以社区相信什么以及为什么测试它很重要开头
- 描述你严谨的方法（必须无懈可击——评审会更严格审查）
- 用统计证据清晰呈现空结果
- 分析**为什么**预期结果没有出现
- 讨论对领域的影响

**明确欢迎负面结果的会议**：NeurIPS（数据集与基准测试赛道）、TMLR、ML 可重复性挑战、主要会议的研讨会。有些研讨会专门征集负面结果。

### 步骤 4.4：创建图表和表格

**图表**：
- 所有绘图使用矢量图形（PDF）：`plt.savefig('fig.pdf')`
- 色盲安全调色板（Okabe-Ito 或 Paul Tol）
- 自包含的图注——读者应无需正文即可理解
- 图表内无标题——图注起此功能

**表格**：
- 使用 `booktabs` LaTeX 包
- 每个指标的最佳值加粗
- 包含方向符号（越高越好/越低越好）
- 一致的小数精度

```latex
\usepackage{booktabs}
\begin{tabular}{lcc}
\toprule
Method & Accuracy $\uparrow$ & Latency $\downarrow$ \\
\midrule
Baseline & 85.2 & 45ms \\
\textbf{Ours} & \textbf{92.1} & 38ms \\
\bottomrule
\end{tabular}
```

### 步骤 4.5：决定：更多实验还是开始写？

| 情况 | 行动 |
|-----------|--------|
| 核心主张得到支持，结果显著 | 进入阶段 5（写作） |
| 结果不确定，需要更多数据 | 回到阶段 2（设计） |
| 意外发现暗示新方向 | 回到阶段 2（设计） |
| 缺少一个评审会问的消融 | 运行它，然后进入阶段 5 |
| 所有实验完成但有些失败 | 记录失败，进入阶段 5 |

### 步骤 4.6：撰写实验日志（连接到写作的桥梁）

在转向论文写作之前，创建一个结构化的实验日志，将结果与散文连接起来。这是实验和写作之间最重要的连接组织——没有它，写作 agent 必须从原始结果文件中重新推导故事。

**创建 `experiment_log.md`**，结构如下：

```markdown
# 实验日志

## 贡献（一句话）
[论文的主要主张]

## 运行的实验

### 实验 1：[名称]
- **测试的主张**：[支持哪个论文主张]
- **设置**：[模型、数据集、配置、运行次数]
- **关键结果**：[一句话包含数字]
- **结果文件**：results/exp1/final_info.json
- **生成的图表**：figures/exp1_comparison.pdf
- **意外发现**：[任何意想不到的内容]

### 实验 2：[名称]
...

## 图表
| 文件名 | 描述 | 属于哪个章节 |
|----------|-------------|---------------------------|
| figures/main_comparison.pdf | 所有方法在基准测试 X 上的比较柱状图 | 结果，图 2 |
| figures/ablation.pdf | 移除组件 A、B、C 的消融 | 结果，图 3 |
...

## 失败的实验（为诚实而记录）
- [尝试了什么，为什么失败，它告诉我们什么]

## 未决问题
- [结果提出的论文应解决的任何问题]
```

**为什么这很重要**：在起草时，agent（或委派的子 agent）可以加载 `experiment_log.md` 和 LaTeX 模板，生成基于实际结果的第一稿。没有这个桥梁，写作 agent 必须解析原始 JSON/CSV 文件并推断故事——这是捏造或误报数字的常见来源。

**Git 纪律**：将此日志与其描述的结果一起提交。

---

## 迭代优化：策略选择

此流水线中的任何输出——论文草稿、实验脚本、分析——都可以迭代优化。autoreason 研究为每种优化策略何时有效和何时失败提供了经验证据。使用本节选择正确的方法。

### 快速决策表

| 你的情况 | 策略 | 为什么 |
|---------------|----------|-----|
| 中端模型 + 约束任务 | **Autoreason** | 最佳范围。生成-评估差距最大。基线会主动破坏弱模型输出。 |
| 中端模型 + 开放任务 | **Autoreason** 并添加范围约束 | 添加固定事实、结构或交付物来限制改进空间。 |
| 前沿模型 + 约束任务 | **Autoreason** | 即使在前沿模型上也能在 2/3 约束任务中获胜。 |
| 前沿模型 + 无约束任务 | **批评与修订** 或 **单次通过** | Autoreason 排最后。模型自我评估能力足够。 |
| 具体技术任务（系统设计） | **批评与修订** | 直接发现-修复循环更高效。 |
| 模板填充任务（一个正确结构） | **单次通过** 或 **保守** | 最小决策空间。迭代不增加价值。 |
| 带有测试用例的代码 | **Autoreason（代码变体）** | 在修复之前结构化分析*为什么*失败。恢复率 62% vs 43%。 |
| 非常弱的模型（Llama 8B 级别） | **单次通过** | 模型太弱无法生成多样候选。投资于生成质量。 |

### 生成-评估差距

**核心洞察**：Autoreason 的价值取决于模型的生成能力和自我评估能力之间的差距。

```
模型层级        │ 生成能力 │ 自我评估 │ 差距    │ Autoreason 价值
──────────────────┼────────────┼───────────┼────────┼─────────────────
弱 (Llama 8B)   │ 差        │ 差        │ 小     │ 无——无法生成多样候选
中 (Haiku 3.5)  │ 尚可      │ 差        │ 大     │ 最大——42/42 完美 Borda
中 (Gemini Flash)│ 尚可      │ 中等      │ 大     │ 高——在 2/3 中获胜
强 (Sonnet 4)   │ 好        │ 尚可      │ 中等   │ 中等——在 3/5 中获胜
前沿 (S4.6)     │ 优秀      │ 好        │ 小     │ 仅在约束条件下
```

这种差距是结构性的，而非暂时的。随着成本下降，今天的前沿会成为明天的中端。最佳范围在移动，但永远不会消失。

### Autoreason 循环（摘要）

每次通过从新鲜、隔离的 agent 产生三个候选：

1. **批评者** → 在当前最佳 A 中发现问题（不修复）
2. **作者 B** → 基于批评修订 A
3. **综合者** → 合并 A 和 B（随机标签）
4. **评审小组** → 3 个盲 CoT 评审通过 Borda 计数排名 A、B、AB
5. **收敛** → A 连续赢得 k=2 次通过 → 完成

**关键参数：**
- k=2 收敛（k=1 过早，k=3 太贵，无质量提升）
- 始终使用 CoT 评审（收敛快 3 倍）
- 温度 0.8 作者，0.3 评审
- 保守平局判定：平局时当前最佳获胜
- 每个角色都是没有共享上下文的全新 agent

### 应用于论文草稿

通过 autoreason 优化论文本身时：
- **为批评者提供事实依据**：实际实验数据、结果 JSON、统计输出。没有这些，模型会捏造虚假的消融研究和虚假的置信区间。
- **至少使用 3 个工作的评审**：损坏的评审解析器不会增加噪音——它会完全阻止平衡。
- **范围约束修订**："解决这些具体弱点"而不是"改进论文"。

### 故障模式

| 故障 | 检测 | 修复 |
|---------|-----------|-----|
| 不收敛（A 从不获胜） | A 在 20+ 次通过中获胜 <15% | 为任务添加范围约束 |
| 综合漂移 | 字数无限增长 | 约束结构和交付物 |
| 退化到低于单次通过 | 基线得分高于迭代输出 | 切换到单次通过；模型可能太弱 |
| 过拟合（代码） | 公共测试高通过，私有测试低通过 | 使用结构化分析，而非仅测试反馈 |
| 损坏的评审 | 解析失败将小组减少到 3 以下 | 在继续之前修复解析器 |

完整提示、Borda 评分细节、模型选择指南、范围约束设计模式和计算预算参考参见 [references/autoreason-methodology.md](references/autoreason-methodology.md)。

---

## 阶段 5：论文起草

**目标**：撰写完整的、可发表的论文。

### 大型项目的上下文管理

一个包含 50+ 实验文件、多个结果目录和大量文献笔记的论文项目很容易超出 agent 的上下文窗口。主动管理：

**每个起草任务加载到上下文的内容：**

| 起草任务 | 加载到上下文 | 不加载 |
|---------------|------------------|-------------|
| 撰写引言 | `experiment_log.md`、贡献声明、5-10 篇最相关论文摘要 | 原始结果 JSON、完整实验脚本、所有文献笔记 |
| 撰写方法 | 实验配置、伪代码、架构描述 | 原始日志、其他实验的结果 |
| 撰写结果 | `experiment_log.md`、结果汇总表、图表列表 | 完整分析脚本、中间数据 |
| 撰写相关工作 | 组织好的引文笔记（步骤 1.4 输出）、.bib 文件 | 实验文件、原始 PDF |
| 修订轮次 | 完整论文草稿、具体评审关注点 | 其他所有内容 |

**原则：**
- **`experiment_log.md` 是主要的上下文桥梁**——它总结了写作所需的一切，无需加载原始数据文件（见步骤 4.6）
- **一次加载一个章节的上下文**，当委派时。起草方法的子 agent 不需要文献综述笔记。
- **总结，而非包含原始文件。** 对于 200 行的结果 JSON，加载 10 行汇总表。对于 50 页的相关论文，加载 5 句摘要 + 你关于其相关性的 2 行笔记。
- **对于非常大的项目**：创建 `context/` 目录，包含预压缩的摘要：
  ```
  context/
    contribution.md          # 1 句话
    experiment_summary.md    # 关键结果表（来自 experiment_log.md）
    literature_map.md        # 组织好的引文笔记
    figure_inventory.md      # 图表列表及其描述
  ```

### 叙事原则

**最关键的认识**：你的论文不是实验的集合——而是一个有清晰贡献并用证据支持的故事。

每篇成功的 ML 论文都围绕 Neel Nanda 所说的"叙事"：一个简短、严谨、基于证据的技术故事，带有读者关心的结论。

**三大支柱（引言结尾必须清晰）：**

| 支柱 | 描述 | 测试 |
|--------|-------------|------|
| **是什么** | 1-3 个具体的新颖主张 | 你能用一句话陈述它们吗？ |
| **为什么** | 严谨的经验证据 | 实验能否区分你的假设和替代方案？ |
| **所以呢** | 读者为什么要在乎 | 这是否与公认社区问题相关？ |

**如果你不能用一句话陈述你的贡献，那么你还没有一篇论文。**

### 本指导的来源

本技能综合了在顶级会议发表大量论文的研究人员的写作理念。写作理念层最初由 [Orchestra Research](https://github.com/orchestra-research) 整理为 `ml-paper-writing` 技能。

| 来源 | 关键贡献 | 链接 |
|--------|-----------------|------|
| **Neel Nanda**（Google DeepMind） | 叙事原则，是什么/为什么/所以呢框架 | [如何撰写 ML 论文](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) |
| **Sebastian Farquhar**（DeepMind） | 5 句摘要公式 | [如何撰写 ML 论文](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/) |
| **Gopen & Swan** | 读者期望的 7 原则 | [科学写作的科学](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf) |
| **Zachary Lipton** | 措辞选择，消除模糊 | [科学写作启发法](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/) |
| **Jacob Steinhardt**（UC Berkeley） | 精确、一致的术语 | [写作建议](https://bounded-regret.ghost.io/) |
| **Ethan Perez**（Anthropic） | 微观层面的清晰度提示 | [简单的论文写作建议](https://ethanperez.net/easy-paper-writing-tips/) |
| **Andrej Karpathy** | 单一贡献重点 | 各类讲座 |

**深入了解其中任何内容，参见：**
- [references/writing-guide.md](references/writing-guide.md)——带示例的完整解释
- [references/sources.md](references/sources.md)——完整参考书目

### 时间分配

在以下内容上花费大致**相等的时间**：
1. 摘要
2. 引言
3. 图表
4. 其他所有内容的总和

**为什么？** 大多数评审在到达你的方法之前就形成了判断。读者遇到你的论文的顺序是：标题 → 摘要 → 引言 → 图表 → 可能还有其余部分。

### 写作工作流

```
论文写作清单：
- [ ] 步骤 1：定义一句话贡献
- [ ] 步骤 2：起草图 1（核心思想或最令人信服的结果）
- [ ] 步骤 3：起草摘要（5 句公式）
- [ ] 步骤 4：起草引言（最多 1-1.5 页）
- [ ] 步骤 5：起草方法
- [ ] 步骤 6：起草实验和结果
- [ ] 步骤 7：起草相关工作
- [ ] 步骤 8：起草结论和讨论
- [ ] 步骤 9：起草局限性（所有会议都要求）
- [ ] 步骤 10：规划附录（证明、额外实验、细节）
- [ ] 步骤 11：完成论文清单
- [ ] 步骤 12：最终审查
```

### 两轮优化模式

当使用 AI agent 起草时，使用**两轮**方法（在 SakanaAI 的 AI-Scientist 流水线中证明有效）：

**第 1 轮——逐章节写 + 立即优化：**
对每个章节，撰写完整草稿，然后立即在同一上下文中优化它。这会在章节新鲜时捕获局部问题（清晰度、流程、完整性）。

**第 2 轮——全局优化，带有完整论文上下文：**
在所有章节起草后，在了解完整论文的情况下重新审视每个章节。这会捕获跨章节问题：冗余、术语不一致、叙事流程、以及一个章节承诺另一个章节未兑现的空白。

```
第二轮优化提示（每章节）：
"在完整论文的上下文中审查 [章节]。
- 它是否与论文其余部分匹配？是否与其他章节有冗余？
- 术语是否与引言和方法一致？
- 在不削弱信息的情况下是否可以删除任何内容？
- 叙事是否从前一章节流畅过渡到下一章节？
进行最小化、有针对性的编辑。不要从头重写。"
```

### LaTeX 错误清单

将此清单附加到每个优化提示中。这些是 LLM 编写 LaTeX 时最常见的错误：

```
LaTeX 质量清单（每次编辑后验证）：
- [ ] 没有未封闭的数学符号（$ 符号平衡）
- [ ] 仅引用存在的图表（\ref 匹配 \label）
- [ ] 没有捏造的引文（\cite 匹配 .bib 中的条目）
- [ ] 每个 \begin{env} 都有匹配的 \end{env}（尤其是 figure、table、algorithm）
- [ ] 没有 HTML 污染（</end{figure}> 而不是 \end{figure}）
- [ ] 数学模式外没有未转义的下划线（文本中使用 \_）
- [ ] 没有重复的 \label 定义
- [ ] 没有重复的章节标题
- [ ] 文本中的数字与实际实验结果匹配
- [ ] 所有图表都有图注和标签
- [ ] 没有导致 overfull hbox 警告的过长的行
```

### 步骤 5.0：标题

标题是论文中阅读量最大的元素。它决定了是否有人点击到摘要。

**好标题**：
- 陈述贡献或发现："Autoreason：迭代 LLM 优化何时有效以及为何失败"
- 突出令人惊讶的结果："数据受限语言模型的扩展"（暗示你可以）
- 命名方法 + 它的作用："DPO：语言模型的直接偏好优化"

**差标题**：
- 太通用："一种改进语言模型输出的方法"
- 太长：超过约 15 个词的任何内容
- 仅行话："迭代随机策略优化的渐近收敛"（这是给谁的？）

**规则**：
- 如果你有方法名，包含它（便于引用）
- 包含 1-2 个评审会搜索的关键词
- 避免冒号，除非两半都有意义
- 测试：评审仅从标题就能知道领域和贡献吗？

### 步骤 5.1：摘要（5 句公式）

来自 Sebastian Farquhar（DeepMind）：

```
1. 你实现了什么："我们引入了..."，"我们证明了..."，"我们展示了..."
2. 为什么这很难且很重要
3. 你如何做（使用专业关键词以便发现）
4. 你有什么证据
5. 你最惊人的数字/结果
```

**删除**像"大型语言模型取得了显著成功……"这样的通用开头。

### 步骤 5.2：图 1

图 1 是大多数读者看的第二件事（在摘要之后）。在写引言之前起草它——它迫使你澄清核心思想。

| 图 1 类型 | 何时使用 | 示例 |
|---------------|-------------|---------|
| **方法图** | 新架构或流水线 | TikZ 流程图显示你的系统 |
| **结果预告** | 一个令人信服的结果讲述整个故事 | 柱状图："我们与基线"带有清晰差距 |
| **问题说明** | 问题不直观 | 修复前的失败模式前后对比 |
| **概念图** | 抽象贡献需要视觉基础 | 方法属性的 2x2 矩阵 |

**规则**：图 1 必须在无需阅读任何文本的情况下可理解。仅图注就应传达核心思想。有目的地使用颜色——不要只是装饰。

### 步骤 5.3：引言（最多 1-1.5 页）

必须包含：
- 清晰的问题陈述
- 简要的方法概述
- 2-4 条贡献要点（双栏格式中每条最多 1-2 行）
- 方法应在第 2-3 页开始

### 步骤 5.4：方法

实现可重实现性：
- 概念概述或伪代码
- 列出所有超参数
- 足以重现的架构细节
- 呈现最终设计决策；消融放在实验中

### 步骤 5.5：实验与结果

对于每个实验，明确说明：
- **它支持什么主张**
- 如何与主要贡献连接
- 观察什么："蓝线显示 X，这证明了 Y"

要求：
- 带有方法论的误差线（标准差与标准误）
- 超参数搜索范围
- 计算基础设施（GPU 类型、总小时数）
- 种子设置方法

### 步骤 5.6：相关工作

按方法论组织，而非逐篇论文。慷慨引用——评审很可能撰写了相关论文。

### 步骤 5.7：局限性（必须）

所有主要会议都要求。诚实有帮助：
- 评审被指示不惩罚诚实的局限性承认
- 通过首先识别弱点来先发制人地应对批评
- 解释局限性为什么不会破坏核心主张

### 步骤 5.8：结论与讨论

**结论**（必需，0.5-1 页）：
- 用一句话重述贡献（与摘要不同的措辞）
- 总结关键发现（2-3 句，而非列表）
- 影响：这对领域意味着什么？
- 未来工作：2-3 个具体的下一步（而不是模糊的"我们将 X 留给未来工作"）

**讨论**（可选，有时与结论合并）：
- 超越直接结果的更广泛影响
- 与其他子领域的连接
- 诚实评估方法何时有效和无效
- 实际部署考虑

**不要**在结论中引入新结果或主张。

### 步骤 5.9：附录策略

附录在所有主要会议上都是无限的，对可重复性至关重要。结构：

| 附录部分 | 内容 |
|-----------------|---------------|
| **证明与推导** | 正文太长的完整证明。正文可陈述定理并附"证明见附录 A。" |
| **额外实验** | 消融、扩展曲线、每数据集分解、超参数敏感性 |
| **实现细节** | 完整超参数表、训练细节、硬件规格、随机种子 |
| **数据集文档** | 数据收集过程、标注指南、许可、预处理 |
| **提示与模板** | 使用的确切提示（对于基于 LLM 的方法）、评估模板 |
| **人类评估** | 标注界面截图、给标注员的指示、IRB 细节 |
| **额外图表** | 每任务分解、轨迹可视化、失败案例示例 |

**规则**：
- 正文必须是自包含的——评审不需要阅读附录
- 绝不将关键证据仅放在附录中
- 交叉引用："完整结果见（附录 B）表 5"，而非仅"见附录"
- 使用 `\appendix` 命令，然后 `\section{A: 证明}` 等

### 页面预算管理

超出页数限制时：

| 删减策略 | 节省 | 风险 |
|-------------|-------|------|
| 将证明移至附录 | 0.5-2 页 | 低——标准做法 |
| 压缩相关工作 | 0.5-1 页 | 中——可能遗漏关键引文 |
| 将表格与子图合并 | 0.25-0.5 页 | 低——通常提高可读性 |
| 谨慎使用 `\vspace{-Xpt}` | 0.1-0.3 页 | 细微时低，明显时高 |
| 删除定性示例 | 0.5-1 页 | 中——评审喜欢示例 |
| 减小图表尺寸 | 0.25-0.5 页 | 高——图表必须保持可读 |

**不要**：减小字体大小、更改边距、删除必需章节（局限性、更广泛影响）、或对正文使用 `\small`/`\footnotesize`。

### 步骤 5.10：伦理与更广泛影响声明

大多数会议现在要求或强烈鼓励伦理/更广泛影响声明。这不是样板文字——评审会阅读它，并且可以标记导致直接拒绝的伦理问题。

**包含内容：**

| 组件 | 内容 | 要求方 |
|-----------|---------|-------------|
| **积极社会影响** | 你的工作如何造福社会 | NeurIPS、ICML |
| **潜在负面影响** | 滥用风险、双重用途问题、故障模式 | NeurIPS、ICML |
| **公平性与偏见** | 你的方法/数据是否有已知偏见？ | 所有会议（隐式） |
| **环境影响** | 大规模训练的碳足迹 | ICML，越来越多 NeurIPS |
| **隐私** | 你的工作是否使用或启用处理个人数据？ | ACL、NeurIPS |
| **LLM 披露** | 是否在写作或实验中使用了 AI？ | ICLR（强制）、ACL |

**编写声明：**

```latex
\section*{Broader Impact Statement}
% NeurIPS/ICML：在结论后，不计入页数限制

% 1. 积极应用（1-2 句）
This work enables [具体应用] which may benefit [具体群体].

% 2. 风险和缓解（1-3 句，具体）
[方法/模型] could potentially be misused for [具体风险]. We mitigate
this by [具体缓解措施，例如仅发布大于 X 大小的模型权重，
包含安全过滤器，记录故障模式].

% 3. 影响声明的局限性（1 句）
Our evaluation is limited to [具体领域]; broader deployment would
require [具体额外工作].
```

**常见错误：**
- 写"我们预见不到任何负面影响"（几乎从不是真的——评审不信任这个）
- 太模糊："这可能会被滥用"而不具体说明如何
- 忽略大规模工作的计算成本
- 忘记在要求的会议披露 LLM 使用

**计算碳足迹**（对于训练密集型论文）：
```python
# 使用 ML CO2 Impact 工具方法论估算
gpu_hours = 1000  # 总 GPU 小时
gpu_tdp_watts = 400  # 例如，A100 = 400W
pue = 1.1  # 电源使用效率（数据中心开销）
carbon_intensity = 0.429  # kg CO2/kWh（美国平均；因地区而异）

energy_kwh = (gpu_hours * gpu_tdp_watts * pue) / 1000
carbon_kg = energy_kwh * carbon_intensity
print(f"Energy: {energy_kwh:.0f} kWh, Carbon: {carbon_kg:.0f} kg CO2eq")
```

### 步骤 5.11：数据表与模型卡（如适用）

如果你的论文引入**新数据集**或**发布模型**，包含结构化文档。评审越来越期望这个，NeurIPS 数据集与基准测试赛道要求它。

**数据集数据表**（Gebru 等人，2021）——包含在附录中：

```
数据集文档（附录）：
- 动机：为什么创建这个数据集？它支持什么任务？
- 组成：实例是什么？有多少？什么数据类型？
- 收集：如何收集数据？来源是什么？
- 预处理：应用了什么清洗/过滤？
- 分发：如何分发数据集？使用什么许可？
- 维护：谁维护它？如何报告问题？
- 伦理考虑：包含个人数据？是否获得同意？
  潜在危害？已知偏见？
```

**模型卡**（Mitchell 等人，2019）——模型发布时包含在附录中：

```
模型卡（附录）：
- 模型详情：架构、训练数据、训练过程
- 预期用途：主要用例、超出范围的用途
- 指标：评估指标和基准测试结果
- 伦理考虑：已知偏见、公平性评估
- 局限性：已知故障模式、模型表现不佳的领域
```

### 写作风格

**句子级清晰度（Gopen & Swan 的 7 原则）：**

| 原则 | 规则 |
|-----------|------|
| 主谓接近 | 保持主语和谓语接近 |
| 强调位置 | 将重点放在句子末尾 |
| 主题位置 | 先放上下文，新信息在后 |
| 旧在新之前 | 熟悉信息 → 不熟悉信息 |
| 一个单元一个功能 | 每段表达一个观点 |
| 动作用动词 | 使用动词，而非名词化 |
| 上下文在新之前 | 在呈现之前设置舞台 |

**措辞选择（Lipton、Steinhardt）：**
- 具体："准确率"而不是"性能"
- 消除模糊：除非真正不确定，否则删除"可能"
- 全文术语一致
- 避免增量词汇："开发"，而非"结合"

带示例的完整写作指南：参见 [references/writing-guide.md](references/writing-guide.md)

### 使用 LaTeX 模板

**务必先复制整个模板目录，然后在其中编写。**

```
模板设置清单：
- [ ] 步骤 1：复制整个模板目录到新项目
- [ ] 步骤 2：验证模板按原样编译（在进行任何更改之前）
- [ ] 步骤 3：阅读模板的示例内容以理解结构
- [ ] 步骤 4：逐节替换示例内容
- [ ] 步骤 5：使用模板宏（检查导言区中的 \newcommand 定义）
- [ ] 步骤 6：仅在最后清理模板工件
```

**步骤 1：复制完整模板**

```bash
cp -r templates/neurips2025/ ~/papers/my-paper/
cd ~/papers/my-paper/
ls -la  # 应看到：main.tex、neurips.sty、Makefile 等
```

复制整个目录，而不仅仅是 .tex 文件。模板包括样式文件（.sty）、参考书目样式（.bst）、示例内容和 Makefile。

**步骤 2：首先验证模板编译**

在进行任何更改之前：
```bash
latexmk -pdf main.tex
# 或手动：pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

如果未修改的模板不编译，先修复它（通常缺少 TeX 包——通过 `tlmgr install <包>` 安装）。

**步骤 3：保留模板内容作为参考**

不要立即删除示例内容。注释掉并用作格式参考：
```latex
% 模板示例（保留为参考）：
% \begin{figure}[t]
%   \centering
%   \includegraphics[width=0.8\linewidth]{example-image}
%   \caption{模板显示图注样式}
% \end{figure}

% 你的实际图表：
\begin{figure}[t]
  \centering
  \includegraphics[width=0.8\linewidth]{your-figure.pdf}
  \caption{你的图注遵循相同样式。}
\end{figure}
```

**步骤 4：逐节替换内容**

系统地进行：标题/作者 → 摘要 → 引言 → 方法 → 实验 → 相关工作 → 结论 → 参考文献 → 附录。每节后编译。

**步骤 5：使用模板宏**

```latex
\newcommand{\method}{YourMethodName}  # 一致的方法命名
\newcommand{\eg}{e.g.,\xspace}        # 正确的缩写
\newcommand{\ie}{i.e.,\xspace}
```

### 模板陷阱

| 陷阱 | 问题 | 解决方案 |
|---------|---------|----------|
| 仅复制 `.tex` 文件 | 缺少 `.sty`，无法编译 | 复制整个目录 |
| 修改 `.sty` 文件 | 破坏会议格式 | 绝不编辑样式文件 |
| 添加随机包 | 冲突、破坏模板 | 仅在必要时添加 |
| 过早删除模板内容 | 失去格式参考 | 保留为注释直到完成 |
| 不频繁编译 | 错误累积 | 每节后编译 |
| 图表使用光栅 PNG | 论文中模糊 | 始终通过 `savefig('fig.pdf')` 使用矢量 PDF |

### 快速模板参考

| 会议 | 主文件 | 样式文件 | 页数限制 |
|------------|-----------|------------|------------|
| NeurIPS 2025 | `main.tex` | `neurips.sty` | 9 页 |
| ICML 2026 | `example_paper.tex` | `icml2026.sty` | 8 页 |
| ICLR 2026 | `iclr2026_conference.tex` | `iclr2026_conference.sty` | 9 页 |
| ACL 2025 | `acl_latex.tex` | `acl.sty` | 8 页（长） |
| AAAI 2026 | `aaai2026-unified-template.tex` | `aaai2026.sty` | 7 页 |
| COLM 2025 | `colm2025_conference.tex` | `colm2025_conference.sty` | 9 页 |

**通用**：双盲、参考文献不计入、附录无限、需要 LaTeX。

模板在 `templates/` 目录中。编译设置（VS Code、CLI、Overleaf、其他 IDE）参见 [templates/README.md](templates/README.md)。

### 表格和图表

**表格**——使用 `booktabs` 进行专业格式化：

```latex
\usepackage{booktabs}
\begin{tabular}{lcc}
\toprule
Method & Accuracy $\uparrow$ & Latency $\downarrow$ \\
\midrule
Baseline & 85.2 & 45ms \\
\textbf{Ours} & \textbf{92.1} & 38ms \\
\bottomrule
\end{tabular}
```

规则：
- 每个指标的最佳值加粗
- 包含方向符号（$\uparrow$ 越高越好，$\downarrow$ 越低越好）
- 数值列右对齐
- 一致的小数精度

**图表**：
- 所有绘图和图表使用**矢量图形**（PDF、EPS）——`plt.savefig('fig.pdf')`
- **光栅**（PNG 600 DPI）仅用于照片
- **色盲安全调色板**（Okabe-Ito 或 Paul Tol）
- 验证**灰度可读性**（8% 的男性有颜色视觉缺陷）
- **图表内无标题**——图注起此功能
- **自包含图注**——读者应无需正文即可理解

### 会议重新提交

在不同会议之间转换，参见阶段 7（提交准备）——它涵盖完整的转换工作流、页面变更表和拒绝后指导。

### 专业 LaTeX 导言区

将这些包添加到任何论文中以实现专业质量。它们与所有主要会议样式文件兼容：

```latex
% --- 专业包（在会议样式文件后添加）---

% 排版
\usepackage{microtype}              % 微观排版改进（突出、扩展）
                                     % 使文本明显更精致——始终包含

% 表格
\usepackage{booktabs}               % 专业表格规则（\toprule、\midrule、\bottomrule）
\usepackage{siunitx}                % 一致的编号格式、小数对齐
                                     % 用法：\num{12345} → 12,345；\SI{3.5}{GHz} → 3.5 GHz
                                     % 表格对齐：S 列类型用于小数对齐的数字

% 图表
\usepackage{graphicx}               % 包含图形（\includegraphics）
\usepackage{subcaption}             % 带 (a)、(b)、(c) 标签的子图
                                     % 用法：\begin{subfigure}{0.48\textwidth} ... \end{subfigure}

% 图表和算法
\usepackage{tikz}                   % 可编程矢量图表
\usetikzlibrary{arrows.meta, positioning, shapes.geometric, calc, fit, backgrounds}
\usepackage[ruled,vlined]{algorithm2e}  % 专业伪代码
                                     % 替代：\usepackage{algorithmicx} 如果模板捆绑了它

% 交叉引用
\usepackage{cleveref}               % 智能引用：\cref{fig:x} → "Figure 1"
                                     % 必须在 hyperref 之后加载
                                     % 处理：图表、表格、章节、公式、算法

% 数学（通常由会议 .sty 包含，但请验证）
\usepackage{amsmath,amssymb}        % AMS 数学环境和符号
\usepackage{mathtools}              % 扩展 amsmath（dcases、coloneqq 等）

% 颜色（用于图表和图表）
\usepackage{xcolor}                 % 颜色管理
% Okabe-Ito 色盲安全调色板：
\definecolor{okblue}{HTML}{0072B2}
\definecolor{okorange}{HTML}{E69F00}
\definecolor{okgreen}{HTML}{009E73}
\definecolor{okred}{HTML}{D55E00}
\definecolor{okpurple}{HTML}{CC79A7}
\definecolor{okcyan}{HTML}{56B4E9}
\definecolor{okyellow}{HTML}{F0E442}
```

**说明：**
- `microtype` 是对视觉质量影响最大的单一包。它在亚像素级别调整字符间距。始终包含它。
- `siunitx` 通过 `S` 列类型处理表格中的小数对齐——消除手动间距。
- `cleveref` 必须在 `hyperref` **之后**加载。大多数会议 .sty 文件加载 hyperref，所以将 cleveref 放在最后。
- 检查会议模板是否已加载其中任何包（尤其是 `algorithm`、`amsmath`、`graphicx`）。不要重复加载。

### siunitx 表格对齐

`siunitx` 使数字密集型表格明显更具可读性：

```latex
\begin{tabular}{l S[table-format=2.1] S[table-format=2.1] S[table-format=2.1]}
\toprule
Method & {Accuracy $\uparrow$} & {F1 $\uparrow$} & {Latency (ms) $\downarrow$} \\
\midrule
Baseline         & 85.2  & 83.7  & 45.3 \\
Ablation (no X)  & 87.1  & 85.4  & 42.1 \\
\textbf{Ours}    & \textbf{92.1} & \textbf{90.8} & \textbf{38.7} \\
\bottomrule
\end{tabular}
```

`S` 列类型自动在小数点对齐。表头用 `{}` 转义对齐。

### 子图

并排图表的标准模式：

```latex
\begin{figure}[t]
  \centering
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{fig_results_a.pdf}
    \caption{Results on Dataset A.}
    \label{fig:results-a}
  \end{subfigure}
  \hfill
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{fig_results_b.pdf}
    \caption{Results on Dataset B.}
    \label{fig:results-b}
  \end{subfigure}
  \caption{Comparison of our method across two datasets. (a) shows the scaling
  behavior and (b) shows the ablation results. Both use 5 random seeds.}
  \label{fig:results}
\end{figure}
```

使用 `\cref{fig:results}` → "Figure 1"，`\cref{fig:results-a}` → "Figure 1a"。

### algorithm2e 伪代码

```latex
\begin{algorithm}[t]
\caption{Iterative Refinement with Judge Panel}
\label{alg:method}
\KwIn{Task $T$, model $M$, judges $J_1 \ldots J_n$, convergence threshold $k$}
\KwOut{Final output $A^*$}
$A \gets M(T)$ \tcp*{Initial generation}
$\text{streak} \gets 0$\;
\While{$\text{streak} < k$}{
  $C \gets \text{Critic}(A, T)$ \tcp*{Identify weaknesses}
  $B \gets M(T, C)$ \tcp*{Revised version addressing critique}
  $AB \gets \text{Synthesize}(A, B)$ \tcp*{Merge best elements}
  \ForEach{judge $J_i$}{
    $\text{rank}_i \gets J_i(\text{shuffle}(A, B, AB))$ \tcp*{Blind ranking}
  }
  $\text{winner} \gets \text{BordaCount}(\text{ranks})$\;
  \eIf{$\text{winner} = A$}{
    $\text{streak} \gets \text{streak} + 1$\;
  }{
    $A \gets \text{winner}$; $\text{streak} \gets 0$\;
  }
}
\Return{$A$}\;
\end{algorithm}
```

### TikZ 图表模式

TikZ 是 ML 论文中方法图表的标准。常见模式：

**流水线/流程图**（ML 论文中最常见）：

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}[
  node distance=1.8cm,
  box/.style={rectangle, draw, rounded corners, minimum height=1cm, 
              minimum width=2cm, align=center, font=\small},
  arrow/.style={-{Stealth[length=3mm]}, thick},
]
  \node[box, fill=okcyan!20] (input) {Input\\$x$};
  \node[box, fill=okblue!20, right of=input] (encoder) {Encoder\\$f_\theta$};
  \node[box, fill=okgreen!20, right of=encoder] (latent) {Latent\\$z$};
  \node[box, fill=okorange!20, right of=latent] (decoder) {Decoder\\$g_\phi$};
  \node[box, fill=okred!20, right of=decoder] (output) {Output\\$\hat{x}$};
  
  \draw[arrow] (input) -- (encoder);
  \draw[arrow] (encoder) -- (latent);
  \draw[arrow] (latent) -- (decoder);
  \draw[arrow] (decoder) -- (output);
\end{tikzpicture}
\caption{Architecture overview. The encoder maps input $x$ to latent 
representation $z$, which the decoder reconstructs.}
\label{fig:architecture}
\end{figure}
```

**比较/矩阵图**（用于显示方法变体）：

```latex
\begin{tikzpicture}[
  cell/.style={rectangle, draw, minimum width=2.5cm, minimum height=1cm, 
               align=center, font=\small},
  header/.style={cell, fill=gray!20, font=\small\bfseries},
]
  % Headers
  \node[header] at (0, 0) {Method};
  \node[header] at (3, 0) {Converges?};
  \node[header] at (6, 0) {Quality?};
  % Rows
  \node[cell] at (0, -1) {Single Pass};
  \node[cell, fill=okgreen!15] at (3, -1) {N/A};
  \node[cell, fill=okorange!15] at (6, -1) {Baseline};
  \node[cell] at (0, -2) {Critique+Revise};
  \node[cell, fill=okred!15] at (3, -2) {No};
  \node[cell, fill=okred!15] at (6, -2) {Degrades};
  \node[cell] at (0, -3) {Ours};
  \node[cell, fill=okgreen!15] at (3, -3) {Yes ($k$=2)};
  \node[cell, fill=okgreen!15] at (6, -3) {Improves};
\end{tikzpicture}
```

**迭代循环图**（用于带反馈的方法）：

```latex
\begin{tikzpicture}[
  node distance=2cm,
  box/.style={rectangle, draw, rounded corners, minimum height=0.8cm, 
              minimum width=1.8cm, align=center, font=\small},
  arrow/.style={-{Stealth[length=3mm]}, thick},
  label/.style={font=\scriptsize, midway, above},
]
  \node[box, fill=okblue!20] (gen) {Generator};
  \node[box, fill=okred!20, right=2.5cm of gen] (critic) {Critic};
  \node[box, fill=okgreen!20, below=1.5cm of $(gen)!0.5!(critic)$] (judge) {Judge Panel};
  
  \draw[arrow] (gen) -- node[label] {output $A$} (critic);
  \draw[arrow] (critic) -- node[label, right] {critique $C$} (judge);
  \draw[arrow] (judge) -| node[label, left, pos=0.3] {winner} (gen);
\end{tikzpicture}
```

### latexdiff 用于修订跟踪

对反驳至关重要——生成标记的 PDF 显示版本之间的更改：

```bash
# 安装
# macOS: brew install latexdiff（或随 TeX Live 一起）
# Linux: sudo apt install latexdiff

# 生成差异
latexdiff paper_v1.tex paper_v2.tex > paper_diff.tex
pdflatex paper_diff.tex

# 对于多文件项目（带 \input{} 或 \include{}）
latexdiff --flatten paper_v1.tex paper_v2.tex > paper_diff.tex
```

这会产生一个 PDF，删除用红色删除线显示，添加用蓝色显示——反驳补充的标准格式。

### SciencePlots 用于 matplotlib

安装并用于出版质量的图表：

```bash
pip install SciencePlots
```

```python
import matplotlib.pyplot as plt
import scienceplots  # 注册样式

# 使用科学样式（类似 IEEE，干净）
with plt.style.context(['science', 'no-latex']):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))  # 单栏宽度
    ax.plot(x, y, label='Ours', color='#0072B2')
    ax.plot(x, y2, label='Baseline', color='#D55E00', linestyle='--')
    ax.set_xlabel('Training Steps')
    ax.set_ylabel('Accuracy')
    ax.legend()
    fig.savefig('paper/fig_results.pdf', bbox_inches='tight')

# 可用样式：'science'、'ieee'、'nature'、'science+ieee'
# 如果在生成图表的机器上未安装 LaTeX，则添加 'no-latex'
```

**标准图表尺寸**（双栏格式）：
- 单栏：`figsize=(3.5, 2.5)`——适合一栏
- 双栏：`figsize=(7.0, 3.0)`——跨两栏
- 方形：`figsize=(3.5, 3.5)`——用于热图、混淆矩阵

---

## 阶段 6：自审与修订

**目标**：在提交前模拟评审过程。尽早发现弱点。

### 步骤 6.1：模拟评审（集合模式）

从多个角度生成评审。自动化研究流水线（尤其是 SakanaAI 的 AI-Scientist）的关键洞察：**带有元评审的集合评审比单一评审轮次产生更加校准的反馈。**

**步骤 1：生成 N 个独立评审**（N=3-5）

使用不同的模型或温度设置。每位评审只看到论文，而不是其他评审。**默认偏向负面**——LLM 在评估中存在记录良好的乐观偏见。

```
你是 [会议] 的专家评审。你是批判性和彻底的。
如果论文存在弱点或你对某个主张不确定，请明确标记
并在你的评分中反映出来。不要给予怀疑的好处。

根据官方评审指南审查这篇论文。评估：

1. 健全性（主张是否得到良好支持？基线是否公平且强大？）
2. 清晰度（论文是否写得好？专家能否重现它？）
3. 重要性（这对社区重要吗？）
4. 原创性（新的洞察，而不仅仅是增量组合？）

以结构化 JSON 形式提供你的评审：
{
  "summary": "2-3 句摘要",
  "strengths": ["优势 1", "优势 2", ...],
  "weaknesses": ["弱点 1（最关键）", "弱点 2", ...],
  "questions": ["给作者的问题 1", ...],
  "missing_references": ["应引用的论文", ...],
  "soundness": 1-4,
  "presentation": 1-4,
  "contribution": 1-4,
  "overall": 1-10,
  "confidence": 1-5
}
```

**步骤 2：元评审（领域主席聚合）**

将所有 N 个评审提供给元评审：

```
你是 [会议] 的领域主席。你收到了一篇论文的 [N] 个独立评审。
你的工作是：

1. 识别评审之间的共识优势和弱点
2. 通过直接检查论文来解决分歧
3. 产生代表总体判断的元评审
4. 使用所有评审的平均数值评分

保守：如果评审对一个弱点是否严重意见不一致，
在作者解决之前将其视为严重的。

评审：
[评审_1]
[评审_2]
...
```

**步骤 3：反思循环**（可选，2-3 轮）

每位评审在看到元评审后可以完善他们的评审。使用提前终止哨兵：如果评审回复"我完成了"（无更改），停止迭代。

**评审的模型选择**：评审最好使用最强大的可用模型完成，即使你用更便宜的模型撰写论文。评审模型应独立于写作模型选择。

**少样本校准**：如果有，包含 1-2 个来自目标会议的真实已发表评审作为示例。这会显著改善评分校准。示例评审参见 [references/reviewer-guidelines.md](references/reviewer-guidelines.md)。

### 步骤 6.1b：视觉评审轮次（VLM）

仅文本评审会遗漏一整类问题：图表质量、布局问题、视觉一致性。如果你能访问具有视觉能力的模型，对编译后的 PDF 运行单独的**视觉评审**：

```
你在审查这篇研究论文 PDF 的视觉呈现。
检查：
1. 图表质量：图表可读吗？标签清晰吗？颜色可区分吗？
2. 图表-图注对齐：每个图注是否准确描述其图表？
3. 布局问题：孤立的章节标题、尴尬的分页、图表距离首次引用很远
4. 表格格式：对齐的列、一致的小数精度、最佳结果加粗
5. 视觉一致性：所有图表使用相同的配色方案、一致的字体大小
6. 灰度可读性：如果黑白打印，图表是否可理解？

对于每个问题，指定页码和确切位置。
```

这可以捕获基于文本的评审无法发现的问题：轴标签无法辨认的图表、放置在首次引用 3 页之后的图表、图 2 和图 5 之间不一致的调色板，或明显超过栏宽的表格。

### 步骤 6.1c：主张验证轮次

在模拟评审之后，运行单独的验证轮次。这会捕获评审可能遗漏的事实错误：

```
主张验证协议：
1. 从论文中提取每个事实主张（数字、比较、趋势）
2. 对于每个主张，将其追溯到支持它的具体实验/结果
3. 验证论文中的数字与实际结果文件匹配
4. 将任何没有可追溯来源的主张标记为 [VERIFY]
```

对于基于 agent 的工作流：将验证委派给**全新的子 agent**，它只接收论文文本和原始结果文件。新鲜的上下文防止确认偏见——验证者不"记得"结果应该是什么。

### 步骤 6.2：优先处理反馈

收集评审后，分类：

| 优先级 | 行动 |
|----------|--------|
| **关键**（技术缺陷、缺失基线） | 必须修复。可能需要新实验 → 回到阶段 2 |
| **高**（清晰度问题、缺失消融） | 应在此轮修订中修复 |
| **中**（小写作问题、额外实验） | 如果有时间则修复 |
| **低**（风格偏好、切线建议） | 记录为未来工作 |

### 步骤 6.3：修订循环

对于每个关键/高优先级问题：
1. 识别受影响的具体章节
2. 起草修复
3. 验证修复不会破坏其他主张
4. 更新论文
5. 根据评审的关注点重新检查

### 步骤 6.4：反驳写作

在回复实际评审时（提交后），反驳是一项独立于修订的技能：

**格式**：逐点回复。对于每位评审的关注点：
```
> R1-W1: "论文缺乏与方法 X 的比较。"

我们感谢评审的这一建议。我们已在表 3（修订版）中添加了与方法 X 的比较。
我们的方法在 [指标] 上优于 X 3.2pp（p<0.05）。我们注意到 X 需要 2 倍我们的计算预算。
```

**规则**：
- 解决每个关注点——评审会注意到你是否跳过
- 以最强有力的回复开头
- 简洁直接——评审阅读数十份反驳
- 如果在反驳期间运行了实验，包含新结果
- 绝不防御性或轻视，即使是对微弱的批评
- 使用 `latexdiff` 生成标记的 PDF 显示更改（参见专业 LaTeX 工具部分）
- 感谢评审具体的、可操作的反馈（而非通用赞扬）

**不要做**："我们 respectfully disagree"而没有证据。"这超出范围"而没有解释。仅回复优势而忽略弱点。

### 步骤 6.5：论文演变跟踪

在关键里程碑保存快照：
```
paper/
  paper.tex                    # 当前工作版本
  paper_v1_first_draft.tex     # 第一稿完整草稿
  paper_v2_post_review.tex     # 模拟评审后
  paper_v3_pre_submission.tex  # 提交前的最终版本
  paper_v4_camera_ready.tex    # 录用后的最终版本
```

---

## 阶段 7：提交准备

**目标**：最终检查、格式化和提交。

### 步骤 7.1：会议清单

每个会议都有强制性清单。仔细完成——不完整的清单可能导致直接拒绝。

参见 [references/checklists.md](references/checklists.md) 获取：
- NeurIPS 16 项论文清单
- ICML 更广泛影响 + 可重复性
- ICLR LLM 披露政策
- ACL 强制性局限性章节
- 通用提交前清单

### 步骤 7.2：匿名化清单

双盲评审意味着评审无法知道谁写了论文。检查所有这些：

```
匿名化清单：
- [ ] PDF 中没有任何地方出现作者姓名或所属机构
- [ ] 没有致谢章节（录用后添加）
- [ ] 自引用以第三人称书写："Smith 等人 [1] 表明……"而不是"我们之前表明 [1]……"
- [ ] 没有指向你个人仓库的 GitHub/GitLab URL
- [ ] 代码链接使用匿名 GitHub（https://anonymous.4open.science/）
- [ ] 图表中没有机构标志或标识符
- [ ] 没有包含作者名的文件元数据（检查 PDF 属性）
- [ ] 没有"我们之前的工作"或"在我们早期的论文中"的措辞
- [ ] 数据集名称不泄露机构（如需要则重命名）
- [ ] 补充材料中不包含身份信息
```

**常见错误**：补充代码中可见的 Git 提交消息、机构工具的水印图表、之前草稿遗留的致谢、匿名期之前发布的 arXiv 预印本。

### 步骤 7.3：格式验证

```
提交前格式检查：
- [ ] 尊重页数限制（不包括参考文献和附录）
- [ ] 所有图表为矢量（PDF）或高分辨率光栅（600 DPI PNG）
- [ ] 所有图表在灰度下可读
- [ ] 所有表格使用 booktabs
- [ ] 参考文献正确编译（引文中没有"?"）
- [ ] 关键区域没有 overfull hboxes
- [ ] 附录清晰标记和分隔
- [ ] 存在必需的章节（局限性、更广泛影响等）
```

### 步骤 7.4：预编译验证

在尝试 `pdflatex` **之前**运行这些自动检查。在这里捕获错误比调试编译器输出更快。

```bash
# 1. 使用 chktex 进行 lint（捕获常见的 LaTeX 错误）
# 抑制嘈杂的警告：-n2（句末）、-n24（括号）、-n13（句间）、-n1（命令终止）
chktex main.tex -q -n2 -n24 -n13 -n1

# 2. 验证所有引文在 .bib 中存在
# 从 .tex 提取 \cite{...}，检查每个是否在 .bib 中
python3 -c "
import re
tex = open('main.tex').read()
bib = open('references.bib').read()
cites = set(re.findall(r'\\\\cite[tp]?{([^}]+)}', tex))
for cite_group in cites:
    for cite in cite_group.split(','):
        cite = cite.strip()
        if cite and cite not in bib:
            print(f'WARNING: \\\\cite{{{cite}}} not found in references.bib')
"

# 3. 验证所有引用的图表在磁盘上存在
python3 -c "
import re, os
tex = open('main.tex').read()
figs = re.findall(r'\\\\includegraphics(?:\[.*?\])?{([^}]+)}', tex)
for fig in figs:
    if not os.path.exists(fig):
        print(f'WARNING: Figure file not found: {fig}')
"

# 4. 检查重复的 \label 定义
python3 -c "
import re
from collections import Counter
tex = open('main.tex').read()
labels = re.findall(r'\\\\label{([^}]+)}', tex)
dupes = {k: v for k, v in Counter(labels).items() if v > 1}
for label, count in dupes.items():
    print(f'WARNING: Duplicate label: {label} (appears {count} times)')
"
```

在继续之前修复任何警告。对于基于 agent 的工作流：将 chktex 输出反馈给 agent 并指示进行最小化修复。

### 步骤 7.5：最终编译

```bash
# 清理构建
rm -f *.aux *.bbl *.blg *.log *.out *.pdf
latexmk -pdf main.tex

# 或手动（三次 pdflatex + bibtex 用于交叉引用）
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

# 验证输出存在且有内容
ls -la main.pdf
```

**如果编译失败**：解析 `.log` 文件获取第一个错误。常见修复：
- "Undefined control sequence" → 缺少包或命令名拼写错误
- "Missing $ inserted" → 数学模式外的数学符号
- "File not found" → 错误的图表路径或缺少 .sty 文件
- "Citation undefined" → .bib 条目缺失或未运行 bibtex

### 步骤 7.6：特定会议要求

| 会议 | 特殊要求 |
|-------|---------------------|
| **NeurIPS** | 附录中的论文清单，录用后普通读者摘要 |
| **ICML** | 更广泛影响声明（在结论后，不计入页数限制） |
| **ICLR** | 需要 LLM 披露，互惠评审协议 |
| **ACL** | 强制性局限性章节，负责任 NLP 清单 |
| **AAAI** | 严格样式文件——绝不允许任何修改 |
| **COLM** | 为语言模型社区构建贡献框架 |

### 步骤 7.7：会议重新提交与格式转换

在不同会议之间转换时，**绝不将 LaTeX 导言区在模板之间复制**：

```bash
# 1. 从目标模板重新开始
cp -r templates/icml2026/ new_submission/

# 2. 仅复制内容章节（而非导言区）
#    - 摘要文本、章节内容、图表、bib 条目

# 3. 调整页数限制
# 4. 添加会议要求的章节
# 5. 更新参考文献
```

| 从 → 到 | 页面变化 | 关键调整 |
|-----------|-------------|-----------------|
| NeurIPS → ICML | 9 → 8 | 删减 1 页，添加更广泛影响 |
| ICML → ICLR | 8 → 9 | 扩展实验，添加 LLM 披露 |
| NeurIPS → ACL | 9 → 8 | 为 NLP 惯例重构，添加局限性 |
| ICLR → AAAI | 9 → 7 | 大幅删减，严格遵守样式 |
| 任何 → COLM | 变化 → 9 | 为语言模型重点重构 |

删减页面时：将证明移至附录、压缩相关工作、合并表格、使用子图。
扩展时：添加消融、扩展局限性、包含额外基线、添加定性示例。

**被拒绝后**：在新版本中解决评审关注点，但不要包含"更改"章节或引用之前的提交（盲审）。

### 步骤 7.8：相机就绪准备（录用后）

录用后，准备相机就绪版本：

```
相机就绪清单：
- [ ] 取消匿名：添加作者姓名、所属机构、电子邮件地址
- [ ] 添加致谢章节（资金、计算资助、有帮助的评审）
- [ ] 添加公共代码/数据 URL（真实的 GitHub，而非匿名）
- [ ] 解决元评审的任何强制性修订
- [ ] 将模板切换到相机就绪模式（如适用——例如 AAAI \anon → \camera）
- [ ] 如果会议要求，添加版权声明
- [ ] 更新文本中的任何"匿名"占位符
- [ ] 验证最终 PDF 干净编译
- [ ] 检查相机就绪的页数限制（有时与提交不同）
- [ ] 将补充材料（代码、数据、附录）上传到会议门户
```

### 步骤 7.9：arXiv 与预印本策略

在 ML 中发布到 arXiv 是标准做法，但有重要的时间和匿名性考虑。

**时间决策树：**

| 情况 | 建议 |
|-----------|---------------|
| 提交到双盲会议（NeurIPS、ICML、ACL） | 在提交截止日期**之后**发布到 arXiv，而非之前。之前发布技术上可能违反匿名政策，尽管执行程度不同。 |
| 提交到 ICLR | ICLR 明确允许在提交之前发布 arXiv。但不要在提交本身中放入作者姓名。 |
| 论文已在 arXiv 上，提交到新会议 | 大多数会议可接受。在评审期间不要更新 arXiv 版本，变更中不要引用评审。 |
| 研讨会论文 | 任何时候都可以发布 arXiv——研讨会通常不是双盲的。 |
| 想建立优先权 | 如果担心被抢先，立即发布——但接受匿名性权衡。 |

**arXiv 类别选择**（ML/AI 论文）：

| 类别 | 代码 | 最适合 |
|----------|------|----------|
| 机器学习 | `cs.LG` | 通用 ML 方法 |
| 计算与语言 | `cs.CL` | NLP、语言模型 |
| 人工智能 | `cs.AI` | 推理、规划、Agent |
| 计算机视觉 | `cs.CV` | 视觉模型 |
| 信息检索 | `cs.IR` | 搜索、推荐 |

**列出主要 + 1-2 个交叉列出的类别。** 更多类别 = 更多可见性，但仅在实际相关的领域交叉列出。

**版本策略：**
- **v1**：初始提交（与会议提交匹配）
- **v2**：录用后附相机就绪修正（在摘要中添加"被 [会议] 录用"）
- 不要在评审期间发布 v2，其变更明显响应评审反馈

```bash
# 在 arXiv 上检查你的论文标题是否已被占用
# （在选择标题之前）
pip install arxiv
python -c "
import arxiv
results = list(arxiv.Search(query='ti:\"Your Exact Title\"', max_results=5).results())
print(f'Found {len(results)} matches')
for r in results: print(f'  {r.title} ({r.published.year})')
"
```

### 步骤 7.10：研究代码打包

发布干净、可运行的代码显著增加引用和评审信任。在相机就绪提交时打包代码。

**仓库结构：**

```
your-method/
  README.md              # 设置、使用、复现说明
  requirements.txt       # 或 conda 的 environment.yml
  setup.py               # 用于 pip 可安装的包
  LICENSE                # 研究推荐 MIT 或 Apache 2.0
  configs/               # 实验配置
  src/                   # 核心方法实现
  scripts/               # 训练、评估、分析脚本
    train.py
    evaluate.py
    reproduce_table1.sh  # 每个主要结果一个脚本
  data/                  # 小数据或下载脚本
    download_data.sh
  results/               # 预期输出用于验证
```

**研究代码 README 模板：**

```markdown
# [论文标题]

"[论文标题]"（会议年份）的官方实现。

## 设置
[设置环境的精确命令]

## 复现
复现表 1：`bash scripts/reproduce_table1.sh`
复现图 2：`python scripts/make_figure2.py`

## 引文
[BibTeX 条目]
```

**发布前清单：**
```
- [ ] 代码从干净克隆运行（在新机器或 Docker 上测试）
- [ ] 所有依赖固定到特定版本
- [ ] 没有硬编码的绝对路径
- [ ] 仓库中没有 API 密钥、凭据或个人数据
- [ ] README 涵盖设置、复现和引文
- [ ] 存在 LICENSE 文件（MIT 或 Apache 2.0 以实现最大重用）
- [ ] 结果在预期方差内可复现
- [ ] .gitignore 排除数据文件、检查点、日志
```

**提交时的匿名代码**（录用前）：
```bash
# 双盲评审使用匿名 GitHub
# https://anonymous.4open.science/
# 上传你的仓库 → 获取匿名 URL → 放入论文
```

---

## 阶段 8：录用后交付物

**目标**：通过演示材料和社区参与最大化你已录用论文的影响力。

### 步骤 8.1：会议海报

大多数会议要求海报环节。海报设计原则：

| 元素 | 指南 |
|---------|-----------|
| **尺寸** | 检查会议要求（通常为 24"x36" 或 A0 纵向/横向） |
| **内容** | 标题、作者、一句话贡献、方法图、2-3 个关键结果、结论 |
| **流程** | 从左上到右下（Z 型模式）或分栏 |
| **文本** | 标题在 3 米处可读，正文在 1 米处可读。不要完整段落——仅要点。 |
| **图表** | 以较高分辨率重用论文图表。放大关键结果。 |

**工具**：LaTeX（`beamerposter` 包）、PowerPoint/Keynote、Figma、Canva。

**制作**：在会议前 2+ 周订购。织物海报旅行更轻。许多会议现在也支持虚拟/数字海报。

### 步骤 8.2：会议演讲/焦点演讲

如果获得口头或焦点演讲：

| 演讲类型 | 时长 | 内容 |
|-----------|----------|---------|
| **焦点** | 5 分钟 | 问题、方法、一个关键结果。练习恰好 5 分钟。 |
| **口头** | 15-20 分钟 | 完整故事：问题、方法、关键结果、消融、局限性。 |
| **研讨会演讲** | 10-15 分钟 | 根据研讨会观众调整——可能需要更多背景。 |

**幻灯片设计规则：**
- 每页一个想法
- 最小化文本——口头讲述细节，不要投影它们
- 逐步动画关键图表以建立理解
- 在结尾包含"结论"幻灯片（一句话贡献）
- 为预期问题准备备用幻灯片

### 步骤 8.3：博客文章/社交媒体

可访问的摘要显著增加影响力：

- **Twitter/X 线程**：5-8 条推文。以结果开头，而非方法。包含图 1 和关键结果图。
- **博客文章**：800-1500 字。为 ML 从业者撰写，而非评审。跳过形式主义，强调直觉和实际影响。
- **项目页面**：带有摘要、图表、演示、代码链接、BibTeX 的 HTML 页面。使用 GitHub Pages。

**时间**：论文出现在会议论文集或 arXiv 相机就绪后的 1-2 天内发布。

---

## 研讨会与短篇论文

研讨会论文和短篇论文（如 ACL 短篇论文、Findings 论文）遵循相同的流水线，但有不同的约束和期望。

### 研讨会论文

| 属性 | 研讨会 | 主会议 |
|----------|----------|-----------------|
| **页数限制** | 4-6 页（通常） | 7-9 页 |
| **评审标准** | 完整性要求较低 | 必须完整、彻底 |
| **评审流程** | 通常单盲或轻量评审 | 双盲、严格 |
| **价值** | 有趣的想法、初步结果、立场文章 | 基于强大基线的完整经验故事 |
| **arXiv** | 随时发布 | 时间很重要（参见 arXiv 策略） |
| **贡献门槛** | 新方向、有趣的负面结果、进行中 | 具有有力证据的显著进展 |

**何时目标研讨会：**
- 想在完整论文之前获得反馈的早期想法
- 不足以证明 8+ 页的负面结果
- 关于热门话题的立场文章或观点
- 复现研究或可重复性报告

### ACL 短篇论文与 Findings

ACL 会议有不同的提交类型：

| 类型 | 页数 | 期望 |
|------|-------|-----------------|
| **长篇论文** | 8 | 完整研究、强大基线、消融 |
| **短篇论文** | 4 | 聚焦贡献：一个清晰的主张并有证据支持 |
| **Findings** | 8 | 扎实的工作，勉强错过主会议 |

**短篇论文策略**：选择**一个**主张并彻底支持它。不要试图将长篇压缩到 4 页——写一篇不同的、更聚焦的论文。

---

## 超越实证 ML 的论文类型

上面的主要流水线面向实证 ML 论文。其他论文类型需要不同的结构和证据标准。每种类型的详细指南参见 [references/paper-types.md](references/paper-types.md)。

### 理论论文

**结构**：引言 → 预备知识（定义、符号）→ 主要结果（定理）→ 证明草图 → 讨论 → 完整证明（附录）

**与实证论文的关键区别：**
- 贡献是定理、界限或不可能结果——而非实验数字
- 方法部分被"预备知识"和"主要结果"取代
- 证明是证据，而非实验（尽管理论的实证验证是受欢迎的）
- 正文中的证明草图、附录中的完整证明是标准做法
- 实验部分是可选的，但如果它验证理论预测则加强论文

**证明写作原则：**
- 正式陈述定理，明确所有假设
- 在正式证明之前提供直觉（"关键洞察是……"）
- 证明草图应在 0.5-1 页内传达主要思想
- 使用 `\begin{proof}...\end{proof}` 环境
- 编号假设并在定理中引用它们："在假设 1-3 下，……"

### 综述/教程论文

**结构**：引言 → 分类/组织 → 详细覆盖 → 未决问题 → 结论

**关键区别：**
- 贡献是组织、综合和识别未决问题——而非新方法
- 必须在范围内全面（评审会检查缺失的参考文献）
- 需要清晰的分类或组织框架
- 价值来自单个论文未做出的作品之间的连接
- 最佳会议：TMLR（综述赛道）、JMLR、ML 基础与趋势、ACM 计算综述

### 基准测试论文

**结构**：引言 → 任务定义 → 数据集构建 → 基线评估 → 分析 → 预期用途与局限性

**关键区别：**
- 贡献是基准测试本身——它必须填补真正的评估空白
- 数据集文档是强制性的，而非可选的（参见数据表，步骤 5.11）
- 必须证明基准测试具有挑战性（基线不会使其饱和）
- 必须证明基准测试测量了它声称测量的内容（构念效度）
- 最佳会议：NeurIPS 数据集与基准测试赛道、ACL（资源论文）、LREC-COLING

### 立场论文

**结构**：引言 → 背景 → 论点/论证 → 支持证据 → 反驳 → 影响

**关键区别：**
- 贡献是论点，而非结果
- 必须认真对待反驳
- 证据可以是经验的、理论的或逻辑分析
- 最佳会议：ICML（立场赛道）、研讨会、TMLR

---

## Hermes Agent 集成

本技能专为 Hermes agent 设计。它使用 Hermes 工具、委派、调度和内存实现完整的研究生命周期。

### 相关技能

将此技能与其他 Hermes 技能组合用于特定阶段：

| 技能 | 何时使用 | 如何加载 |
|-------|-------------|-------------|
| **arxiv** | 阶段 1（文献综述）：搜索 arXiv、生成 BibTeX、通过 Semantic Scholar 查找相关论文 | `skill_view("arxiv")` |
| **subagent-driven-development** | 阶段 5（起草）：并行章节撰写，带有 2 阶段审查（规范合规性然后质量） | `skill_view("subagent-driven-development")` |
| **plan** | 阶段 0（设置）：在执行前创建结构化计划。写入 `.hermes/plans/` | `skill_view("plan")` |
| **qmd** | 阶段 1（文献）：通过混合 BM25+向量搜索搜索本地知识库（笔记、转录、文档） | 安装：`skill_manage("install", "qmd")` |
| **diagramming** | 阶段 4-5：创建基于 Excalidraw 的图表和架构图 | `skill_view("diagramming")` |
| **data-science** | 阶段 4（分析）：Jupyter 实时内核用于交互式分析和可视化 | `skill_view("data-science")` |

**本技能取代 `ml-paper-writing`**——它包含 ml-paper-writing 的所有内容，加上完整的实验/分析流水线和 autoreason 方法论。

### Hermes 工具参考

| 工具 | 在本流水线中的用法 |
|------|----------------------|
| **`terminal`** | LaTeX 编译（`latexmk -pdf`）、git 操作、启动实验（`nohup python run.py &`）、进程检查 |
| **`process`** | 后台实验管理：`process("start", ...)`、`process("poll", pid)`、`process("log", pid)`、`process("kill", pid)` |
| **`execute_code`** | 运行 Python 进行引文验证、统计分析、数据聚合。通过 RPC 访问工具。 |
| **`read_file`** / **`write_file`** / **`patch`** | 论文编辑、实验脚本、结果文件。对大型 .tex 文件使用 `patch` 进行定向编辑。 |
| **`web_search`** | 文献发现：`web_search("transformer attention mechanism 2024")` |
| **`web_extract`** | 获取论文内容、验证引文：`web_extract("https://arxiv.org/abs/2303.17651")` |
| **`delegate_task`** | **并行章节起草**——为每个章节生成隔离的子 agent。也用于并发引文验证。 |
| **`todo`** | 跨会话的主要状态跟踪器。每个阶段转换后更新。 |
| **`memory`** | 跨会话持久化关键决策：贡献框架、会议选择、评审反馈。 |
| **`cronjob`** | 安排实验监控、倒计时、自动 arXiv 检查。 |
| **`clarify`** | 受阻时向用户提出针对性问题（会议选择、贡献框架）。 |
| **`send_message`** | 实验完成或草稿准备好时通知用户，即使用户不在聊天中。 |

### 工具使用模式

**实验监控**（最常见）：
```
terminal("ps aux | grep <模式>")
→ terminal("tail -30 <日志文件>")
→ terminal("ls results/")
→ execute_code("分析结果 JSON，计算指标")
→ terminal("git add -A && git commit -m '<描述性消息>' && git push")
→ send_message("实验完成：<摘要>")
```

**并行章节起草**（使用委派）：
```
delegate_task("根据这些实验脚本和配置起草方法章节。
  包含：伪代码、所有超参数、足以重现的架构细节。
  使用 neurips2025 模板约定以 LaTeX 编写。")

delegate_task("起草相关工作章节。使用 web_search 和 web_extract 
  查找论文。通过 Semantic Scholar 验证每条引文。按方法论分组。")

delegate_task("起草实验章节。读取 results/ 中的所有结果文件。
  声明每个实验支持的主张。包含误差线和显著性。")
```

每个委派作为**全新子 agent** 运行，没有共享上下文——在提示中提供所有必要信息。收集输出并集成。

**引文验证**（使用 execute_code）：
```python
# 在 execute_code 中：
from semanticscholar import SemanticScholar
import requests

sch = SemanticScholar()
results = sch.search_paper("attention mechanism transformers", limit=5)
for paper in results:
    doi = paper.externalIds.get('DOI', 'N/A')
    if doi != 'N/A':
        bibtex = requests.get(f"https://doi.org/{doi}", 
                              headers={"Accept": "application/x-bibtex"}).text
        print(bibtex)
```

### 使用 `memory` 和 `todo` 进行状态管理

**`memory` 工具**——持久化关键决策（有界：MEMORY.md 约 2200 字符）：

```
memory("add", "论文：autoreason。会议：NeurIPS 2025（9 页）。
  贡献：当生成-评估差距较大时，结构化精化有效。
  关键结果：Haiku 42/42，Sonnet 3/5，S4.6 约束 2/3。
  状态：阶段 5——正在起草方法章节。")
```

在重大决策或阶段转换后更新内存。这在会话之间持久化。

**`todo` 工具**——跟踪细粒度进度：

```
todo("add", "为 Sonnet 4.6 设计约束任务实验")
todo("add", "运行 Haiku 基线比较")
todo("add", "起草方法章节")
todo("update", id=3, status="in_progress")
todo("update", id=1, status="completed")
```

**会话启动协议：**
```
1. todo("list")                           # 检查当前任务列表
2. memory("read")                         # 回忆关键决策
3. terminal("git log --oneline -10")      # 检查最近提交
4. terminal("ps aux | grep python")       # 检查运行中的实验
5. terminal("ls results/ | tail -20")     # 检查新结果
6. 向用户报告状态，询问方向
```

### 使用 `cronjob` 进行 Cron 监控

使用 `cronjob` 工具安排定期检查：

```
cronjob("create", {
  "schedule": "*/30 * * * *",  # 每 30 分钟
  "prompt": "检查实验状态：
    1. ps aux | grep run_experiment
    2. tail -30 logs/experiment_haiku.log
    3. ls results/haiku_baselines/
    4. 如果完成：读取结果，计算 Borda 分数，
       git add -A && git commit -m '添加 Haiku 结果' && git push
    5. 报告：结果表、关键发现、下一步
    6. 如果没有变化：回复 [SILENT]"
})
```

**[SILENT] 协议**：当自上次检查以来没有变化时，准确回复 `[SILENT]`。这会抑制向用户的通知传递。仅在有真正值得知道的更改时报告。

**截止日期跟踪**：
```
cronjob("create", {
  "schedule": "0 9 * * *",  # 每天上午 9 点
  "prompt": "NeurIPS 2025 截止日期：5 月 22 日。今天是 {date}。
    剩余天数：{compute}。
    检查待办列表——我们是否按计划进行？
    如果 <7 天：警告用户剩余任务。"
})
```

### 通信模式

**何时通知用户**（通过 `send_message` 或直接回复）：
- 实验批次完成（附带结果表）
- 意外发现或需要决策的故障
- 草稿章节准备好供审查
- 截止日期临近且有未完成的任务

**何时不通知：**
- 实验仍在运行，无新结果 → `[SILENT]`
- 常规监控无变化 → `[SILENT]`
- 不需要关注的中间步骤

**报告格式**——始终包含结构化数据：
```
## 实验：<名称>
状态：完成 / 运行中 / 失败

| 任务 | 方法 A | 方法 B | 方法 C |
|------|---------|---------|---------|
| Task 1 | 85.2 | 82.1 | **89.4** |

关键发现：<一句话>
下一步：<接下来发生什么>
```

### 需要人类输入的决策点

在真正受阻时使用 `clarify` 提出针对性问题：

| 决策 | 何时询问 |
|----------|-------------|
| 目标会议 | 在开始论文之前（影响页数限制、框架） |
| 贡献框架 | 当存在多个有效框架时 |
| 实验优先级 | 当待办列表的实验超过时间允许时 |
| 提交准备情况 | 在最终提交之前 |

**不要询问**（主动出击，做出选择，标记它）：
- 措辞选择、章节排序
- 突出哪些具体结果
- 引文完整性（用你找到的内容起草，记录空白）

---

## 评审评估标准

了解评审寻找什么有助于集中精力：

| 标准 | 他们检查什么 |
|-----------|----------------|
| **质量** | 技术健全性、有良好支持的主张、公平的基线 |
| **清晰度** | 清晰的写作、专家可重现、一致的符号 |
| **重要性** | 社区影响、推进理解 |
| **原创性** | 新的洞察（不需要新方法） |

**评分（NeurIPS 6 分制）：**
- 6：强烈接受——开创性的、无懈可击的
- 5：接受——技术扎实、高影响力
- 4：边缘接受——扎实、评估有限
- 3：边缘拒绝——弱点超过优势
- 2：拒绝——技术缺陷
- 1：强烈拒绝——已知结果或伦理问题

详细指南、常见关注和反驳策略参见 [references/reviewer-guidelines.md](references/reviewer-guidelines.md)。

---

## 常见问题和解决方案

| 问题 | 解决方案 |
|-------|----------|
| 摘要太通用 | 如果第一句话可以放在任何 ML 论文前面，就删除它。从你的具体贡献开始。 |
| 引言超过 1.5 页 | 将背景拆分到相关工作。前置贡献要点。 |
| 实验缺乏明确主张 | 在每个实验前添加："此实验测试是否 [具体主张]……" |
| 评审发现论文难以理解 | 添加路标、使用一致的术语、使图注自包含。 |
| 缺少统计显著性 | 添加误差线、运行次数、统计检验、置信区间。 |
| 实验范围蔓延 | 每个实验必须映射到具体主张。删减不映射的实验。 |
| 论文被拒，需要重新提交 | 参见阶段 7 中的会议重新提交。解决评审关注点而不引用评审。 |
| 缺少更广泛影响声明 | 参见步骤 5.10。大多数会议要求。"没有负面影响"几乎从不可信。 |
| 人类评估被批评为薄弱 | 参见步骤 2.5 和 [references/human-evaluation.md](references/human-evaluation.md)。报告一致性指标、标注员细节、补偿。 |
| 评审质疑可重现性 | 发布代码（步骤 7.9）、记录所有超参数、包含种子和计算细节。 |
| 理论论文缺乏直觉 | 在正式证明之前添加带有通俗解释的证明草图。参见 [references/paper-types.md](references/paper-types.md)。 |
| 结果是负面/空的 | 参见阶段 4.3 关于处理负面结果。考虑研讨会、TMLR 或重新定义为分析。 |

---

## 参考文档

| 文档 | 内容 |
|----------|----------|
| [references/writing-guide.md](references/writing-guide.md) | Gopen & Swan 7 原则、Perez 微观提示、Lipton 措辞选择、Steinhardt 精确性、图表设计 |
| [references/citation-workflow.md](references/citation-workflow.md) | 引文 API、Python 代码、CitationManager 类、BibTeX 管理 |
| [references/checklists.md](references/checklists.md) | NeurIPS 16 项、ICML、ICLR、ACL 要求、通用提交前清单 |
| [references/reviewer-guidelines.md](references/reviewer-guidelines.md) | 评估标准、评分、常见关注、反驳模板 |
| [references/sources.md](references/sources.md) | 所有写作指南、会议指南、API 的完整参考书目 |
| [references/experiment-patterns.md](references/experiment-patterns.md) | 实验设计模式、评估协议、监控、错误恢复 |
| [references/autoreason-methodology.md](references/autoreason-methodology.md) | Autoreason 循环、策略选择、模型指南、提示、范围约束、Borda 评分 |
| [references/human-evaluation.md](references/human-evaluation.md) | 人类评估设计、标注指南、一致性指标、众包质量控制、IRB 指导 |
| [references/paper-types.md](references/paper-types.md) | 理论论文（证明写作、定理结构）、综述论文、基准论文、立场论文 |

### LaTeX 模板

`templates/` 中的模板：**NeurIPS 2025**、**ICML 2026**、**ICLR 2026**、**ACL**、**AAAI 2026**、**COLM 2025**。

编译说明参见 [templates/README.md](templates/README.md)。

### 关键外部来源

**写作理念：**
- [Neel Nanda: 如何撰写 ML 论文](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers)
- [Sebastian Farquhar: 如何撰写 ML 论文](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/)
- [Gopen & Swan: 科学写作的科学](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf)
- [Lipton: 科学写作启发法](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/)
- [Perez: 简单的论文写作建议](https://ethanperez.net/easy-paper-writing-tips/)

**API：** [Semantic Scholar](https://api.semanticscholar.org/api-docs/) | [CrossRef](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | [arXiv](https://info.arxiv.org/help/api/basics.html)

**会议：** [NeurIPS](https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles) | [ICML](https://icml.cc/Conferences/2025/AuthorInstructions) | [ICLR](https://iclr.cc/Conferences/2026/AuthorGuide) | [ACL](https://github.com/acl-org/acl-style-files)

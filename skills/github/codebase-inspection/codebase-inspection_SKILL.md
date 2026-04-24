---
name: codebase-inspection
description: 使用 pygount 检查和分析代码库，用于统计代码行数、语言分布和代码与注释比例。当被要求检查代码行数、仓库大小、语言组成或代码库统计时使用。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [LOC, 代码分析, pygount, 代码库, 指标, 仓库]
    related_skills: [github-repo-management]
prerequisites:
  commands: [pygount]
---

# 使用 pygount 检查代码库

使用 `pygount` 分析仓库的代码行数、语言分布、文件数量和代码与注释比例。

## 何时使用

- 用户询问 LOC（代码行数）
- 用户想要仓库的语言分布
- 用户询问代码库大小或组成
- 用户想要代码与注释比例
- 一般的"这个仓库有多大"问题

## 前提条件

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

## 1. 基本摘要（最常见）

获取完整的语言分布，包括文件数、代码行和注释行：

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**重要：** 始终使用 `--folders-to-skip` 排除依赖/构建目录，否则 pygount 会遍历它们并耗时很久或卡住。

## 2. 常见目录排除

根据项目类型调整：

```bash
# Python 项目
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript 项目
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# 通用全覆盖
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

## 3. 按特定语言过滤

```bash
# 仅统计 Python 文件
pygount --suffix=py --format=summary .

# 仅统计 Python 和 YAML
pygount --suffix=py,yaml,yml --format=summary .
```

## 4. 逐文件详细输出

```bash
# 默认格式显示逐文件分解
pygount --folders-to-skip=".git,node_modules,venv" .

# 按代码行数排序（通过 sort 管道）
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

## 5. 输出格式

```bash
# 摘要表（默认推荐）
pygount --format=summary .

# JSON 输出用于编程使用
pygount --format=json .

# 管道友好格式：语言、文件数、代码、文档、空、字符串
pygount --format=summary . 2>/dev/null
```

## 6. 解释结果

摘要表的列：
- **Language**——检测到的编程语言
- **Files**——该语言的文件数
- **Code**——实际代码行（可执行/声明性）
- **Comment**——注释或文档行
- **%**——占总数的百分比

特殊伪语言：
- `__empty__`——空文件
- `__binary__`——二进制文件（图像、编译文件等）
- `__generated__`——自动生成的文件（启发式检测）
- `__duplicate__`——内容相同的文件
- `__unknown__`——无法识别的文件类型

## 陷阱

1. **始终排除 .git、node_modules、venv**——不使用 `--folders-to-skip`，pygount 会遍历所有内容，在大型依赖树上可能需要几分钟或卡住。
2. **Markdown 显示 0 代码行**——pygount 将所有 Markdown 内容分类为注释，而非代码。这是预期行为。
3. **JSON 文件显示低代码计数**——pygount 可能保守计算 JSON 行。要获取准确的 JSON 行数，直接使用 `wc -l`。
4. **大型单体仓库**——对于非常大的仓库，考虑使用 `--suffix` 定位特定语言，而不是扫描所有内容。

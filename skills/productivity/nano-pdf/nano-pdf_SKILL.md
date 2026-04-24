---
name: nano-pdf
description: 使用自然语言指令通过 nano-pdf CLI 编辑 PDF。修改文本、修复拼写错误、更新标题，并在特定页面上进行内容更改，无需手动编辑。
version: 1.0.0
author: 社区
license: MIT
metadata:
  hermes:
    tags: [PDF, 文档, 编辑, 自然语言处理, 生产力]
    homepage: https://pypi.org/project/nano-pdf/
---

# nano-pdf

使用自然语言指令编辑 PDF。指向页面并描述要更改的内容。

## 前提条件

```bash
# 使用 uv 安装（推荐——Hermes 中已可用）
uv pip install nano-pdf

# 或使用 pip
pip install nano-pdf
```

## 用法

```bash
nano-pdf edit <file.pdf> <page_number> "<instruction>"
```

## 示例

```bash
# 更改第 1 页的标题
nano-pdf edit deck.pdf 1 "Change the title to 'Q3 Results' and fix the typo in the subtitle"

# 更新特定页面的日期
nano-pdf edit report.pdf 3 "Update the date from January to February 2026"

# 修复内容
nano-pdf edit contract.pdf 2 "Change the client name from 'Acme Corp' to 'Acme Industries'"
```

## 说明

- 页码可能基于 0 或基于 1，具体取决于版本——如果编辑命中了错误的页面，用 ±1 重试
- 编辑后始终验证输出的 PDF（使用 `read_file` 检查文件大小，或打开它）
- 该工具在底层使用 LLM——需要 API 密钥（检查 `nano-pdf --help` 获取配置）
- 适用于文本更改；复杂的布局修改可能需要不同的方法

---
name: apple-notes
description: 通过macOS上的memo CLI管理Apple Notes（创建、查看、搜索、编辑）。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Notes, Apple, macOS, 笔记]
    related_skills: [obsidian]
prerequisites:
  commands: [memo]
---

# Apple Notes（苹果备忘录）

使用 `memo` 直接从终端管理 Apple Notes。备忘录通过 iCloud 在所有 Apple 设备间同步。

## 前置条件

- **macOS** 系统，已安装 Notes.app
- 安装：`brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- 根据提示授予 Notes.app 自动化访问权限（系统设置 → 隐私 → 自动化）

## 使用场景

- 用户要求创建、查看或搜索 Apple Notes
- 将信息保存到 Notes.app 以实现跨设备访问
- 将备忘录整理到文件夹中
- 导出备忘录到 Markdown/HTML

## 不使用场景

- Obsidian 库管理 → 使用 `obsidian` 技能
- Bear Notes → 独立应用（此处不支持）
- 仅限智能体内部使用的笔记 → 使用 `memory` 工具

## 快速参考

### 查看备忘录

```bash
memo notes                        # 列出所有备忘录
memo notes -f "Folder Name"       # 按文件夹过滤
memo notes -s "query"             # 搜索备忘录（模糊匹配）
```

### 创建备忘录

```bash
memo notes -a                     # 交互式编辑器
memo notes -a "Note Title"        # 快速添加标题
```

### 编辑备忘录

```bash
memo notes -e                     # 交互式选择要编辑的备忘录
```

### 删除备忘录

```bash
memo notes -d                     # 交互式选择要删除的备忘录
```

### 移动备忘录

```bash
memo notes -m                     # 将备忘录移动到文件夹（交互式）
```

### 导出备忘录

```bash
memo notes -ex                    # 导出为 HTML/Markdown
```

## 限制

- 无法编辑包含图片或附件的备忘录
- 交互式提示需要终端访问权限（如需要可使用 pty=true）
- 仅限 macOS — 需要 Apple Notes.app

## 规则

1. 当用户需要跨设备同步（iPhone/iPad/Mac）时，优先使用 Apple Notes
2. 对于不需要同步的智能体内部笔记，使用 `memory` 工具
3. 对于 Markdown 原生的知识管理，使用 `obsidian` 技能

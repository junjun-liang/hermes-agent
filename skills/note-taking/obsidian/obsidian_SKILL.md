---
name: obsidian
description: 在Obsidian知识库中读取、搜索和创建笔记。
---

# Obsidian知识库

**位置：** 通过`OBSIDIAN_VAULT_PATH`环境变量设置（例如在`~/.hermes/.env`中）。

如果未设置，默认为`~/Documents/Obsidian Vault`。

注意：知识库路径可能包含空格 — 始终使用引号。

## 读取笔记

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat "$VAULT/Note Name.md"
```

## 列出笔记

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# 所有笔记
find "$VAULT" -name "*.md" -type f

# 特定文件夹中的笔记
ls "$VAULT/Subfolder/"
```

## 搜索

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# 按文件名搜索
find "$VAULT" -name "*.md" -iname "*keyword*"

# 按内容搜索
grep -rli "keyword" "$VAULT" --include="*.md"
```

## 创建笔记

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat > "$VAULT/New Note.md" << 'ENDNOTE'
# 标题

内容在此。
ENDNOTE
```

## 追加到笔记

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
echo "
新内容在此。" >> "$VAULT/Existing Note.md"
```

## Wiki链接

Obsidian使用`[[Note Name]]`语法链接笔记。创建笔记时，使用此语法链接相关内容。

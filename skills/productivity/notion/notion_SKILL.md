---
name: notion
description: 通过 curl 使用 Notion API 创建和管理页面、数据库和块。直接从终端搜索、创建、更新和查询 Notion 工作区。
version: 1.0.0
author: 社区
license: MIT
metadata:
  hermes:
    tags: [Notion, 生产力, 笔记, 数据库, API]
    homepage: https://developers.notion.com
prerequisites:
  env_vars: [NOTION_API_KEY]
---

# Notion API

通过 curl 使用 Notion API 创建、读取、更新页面、数据库（数据源）和块。无需额外工具——只需 curl 和 Notion API 密钥。

## 前提条件

1. 在 https://notion.so/my-integrations 创建集成
2. 复制 API 密钥（以 `ntn_` 或 `secret_` 开头）
3. 存储到 `~/.hermes/.env`：
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
4. **重要：** 在 Notion 中将目标页面/数据库共享给你的集成（点击"..."→"连接到"→你的集成名称）

## API 基础

所有请求使用此模式：

```bash
curl -s -X GET "https://api.notion.com/v1/..." \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json"
```

`Notion-Version` 头是必需的。本技能使用 `2025-09-03`（最新）。在此版本中，数据库在 API 中称为"数据源"。

## 常用操作

### 搜索

```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"query": "page title"}'
```

### 获取页面

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### 获取页面内容（块）

```bash
curl -s "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### 在数据库中创建页面

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "xxx"},
    "properties": {
      "Name": {"title": [{"text": {"content": "New Item"}}]},
      "Status": {"select": {"name": "Todo"}}
    }
  }'
```

### 查询数据库

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/{data_source_id}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"property": "Status", "select": {"equals": "Active"}},
    "sorts": [{"property": "Date", "direction": "descending"}]
  }'
```

### 创建数据库

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "title": [{"text": {"content": "My Database"}}],
    "properties": {
      "Name": {"title": {}},
      "Status": {"select": {"options": [{"name": "Todo"}, {"name": "Done"}]}},
      "Date": {"date": {}}
    }
  }'
```

### 更新页面属性

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"Status": {"select": {"name": "Done"}}}}'
```

### 向页面添加内容

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hello from Hermes!"}}]}}
    ]
  }'
```

## 属性类型

数据库项目的常用属性格式：

- **标题：** `{"title": [{"text": {"content": "..."}}]}`
- **富文本：** `{"rich_text": [{"text": {"content": "..."}}]}`
- **单选：** `{"select": {"name": "Option"}}`
- **多选：** `{"multi_select": [{"name": "A"}, {"name": "B"}]}`
- **日期：** `{"date": {"start": "2026-01-15", "end": "2026-01-16"}}`
- **复选框：** `{"checkbox": true}`
- **数字：** `{"number": 42}`
- **URL：** `{"url": "https://..."}`
- **电子邮件：** `{"email": "user@example.com"}`
- **关联：** `{"relation": [{"id": "page_id"}]}`

## API 版本 2025-09-03 的关键差异

- **数据库 → 数据源：** 使用 `/data_sources/` 端点进行查询和检索
- **两个 ID：** 每个数据库都有 `database_id` 和 `data_source_id`
  - 创建页面时使用 `database_id`（`parent: {"database_id": "..."}`）
  - 查询时使用 `data_source_id`（`POST /v1/data_sources/{id}/query`）
- **搜索结果：** 数据库返回 `"object": "data_source"` 及其 `data_source_id`

## 说明

- 页面/数据库 ID 是 UUID（带或不带破折号）
- 速率限制：平均约 3 次请求/秒
- API 无法设置数据库视图过滤器——这仅限 UI
- 创建数据源时使用 `is_inline: true` 将其嵌入页面
- 在 curl 中添加 `-s` 标志以抑制进度条（Hermes 输出更干净）
- 通过 `jq` 管道输出以获取可读的 JSON：`... | jq '.results[0].properties'`

---
name: gif-search
description: 使用curl搜索和下载Tenor GIF。除curl和jq外无需额外依赖。适用于查找反应GIF、创建视觉内容和在聊天中发送GIF。
version: 1.1.0
author: Hermes Agent
license: MIT
prerequisites:
  env_vars: [TENOR_API_KEY]
  commands: [curl, jq]
metadata:
  hermes:
    tags: [GIF, 媒体, 搜索, Tenor, API]
---

# GIF搜索（Tenor API）

通过Tenor API直接使用curl搜索和下载GIF。无需额外工具。

## 设置

在环境中设置Tenor API密钥（添加到`~/.hermes/.env`）：

```bash
TENOR_API_KEY=your_key_here
```

在 https://developers.google.com/tenor/guides/quickstart 获取免费API密钥 — Google Cloud Console Tenor API密钥免费且速率限制宽松。

## 前置条件

- `curl`和`jq`（macOS/Linux上均标准）
- `TENOR_API_KEY`环境变量

## 搜索GIF

```bash
# 搜索并获取GIF URL
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.gif.url'

# 获取较小/预览版本
curl -s "https://tenor.googleapis.com/v2/search?q=nice+work&limit=3&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.tinygif.url'
```

## 下载GIF

```bash
# 搜索并下载顶部结果
URL=$(curl -s "https://tenor.googleapis.com/v2/search?q=celebration&limit=1&key=${TENOR_API_KEY}" | jq -r '.results[0].media_formats.gif.url')
curl -sL "$URL" -o celebration.gif
```

## 获取完整元数据

```bash
curl -s "https://tenor.googleapis.com/v2/search?q=cat&limit=3&key=${TENOR_API_KEY}" | jq '.results[] | {title: .title, url: .media_formats.gif.url, preview: .media_formats.tinygif.url, dimensions: .media_formats.gif.dims}'
```

## API参数

| 参数 | 描述 |
|-----------|-------------|
| `q` | 搜索查询（空格URL编码为`+`） |
| `limit` | 最大结果数（1-50，默认20） |
| `key` | API密钥（来自`$TENOR_API_KEY`环境变量） |
| `media_filter` | 过滤格式：`gif`、`tinygif`、`mp4`、`tinymp4`、`webm` |
| `contentfilter` | 安全级别：`off`、`low`、`medium`、`high` |
| `locale` | 语言：`en_US`、`es`、`fr`等 |

## 可用媒体格式

每个结果有多个格式，在`.media_formats`下：

| 格式 | 用途 |
|--------|----------|
| `gif` | 完整质量GIF |
| `tinygif` | 小预览GIF |
| `mp4` | 视频版本（较小文件大小） |
| `tinymp4` | 小预览视频 |
| `webm` | WebM视频 |
| `nanogif` | 极小缩略图 |

## 注意事项

- URL编码查询：空格为`+`，特殊字符为`%XX`
- 在聊天中发送时，`tinygif` URL更轻量
- GIF URL可直接在markdown中使用：`![alt](url)`

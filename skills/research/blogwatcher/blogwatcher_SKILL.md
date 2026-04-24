---
name: blogwatcher
description: 使用 blogwatcher-cli 工具监控博客和 RSS/Atom 源的更新。添加博客、扫描新文章、跟踪阅读状态，并按类别过滤。
version: 2.0.0
author: JulienTant (Hyaxia/blogwatcher 的分支)
license: MIT
metadata:
  hermes:
    tags: [RSS, 博客, 阅读器, 监控]
    homepage: https://github.com/JulienTant/blogwatcher-cli
prerequisites:
  commands: [blogwatcher-cli]
---

# Blogwatcher

使用 `blogwatcher-cli` 工具跟踪博客和 RSS/Atom 源的更新。支持自动发现源、HTML 抓取回退、OPML 导入，以及已读/未读文章管理。

## 安装

选择一种方法：

- **Go:** `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest`
- **Docker:** `docker run --rm -v blogwatcher-cli:/data ghcr.io/julientant/blogwatcher-cli`
- **二进制 (Linux amd64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **二进制 (Linux arm64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **二进制 (macOS Apple Silicon):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **二进制 (macOS Intel):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`

所有版本: https://github.com/JulienTant/blogwatcher-cli/releases

### Docker 持久化存储

默认情况下，数据库位于 `~/.blogwatcher-cli/blogwatcher-cli.db`。在 Docker 中，容器重启后会丢失。使用 `BLOGWATCHER_DB` 或卷挂载来持久化：

```bash
# 命名卷（最简单）
docker run --rm -v blogwatcher-cli:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan

# 主机绑定挂载
docker run --rm -v /path/on/host:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan
```

### 从原版 blogwatcher 迁移

如果从 `Hyaxia/blogwatcher` 升级，移动你的数据库：

```bash
mv ~/.blogwatcher/blogwatcher.db ~/.blogwatcher-cli/blogwatcher-cli.db
```

二进制文件名称从 `blogwatcher` 更改为 `blogwatcher-cli`。

## 常用命令

### 管理博客

- 添加博客: `blogwatcher-cli add "My Blog" https://example.com`
- 指定源添加: `blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml`
- 启用 HTML 抓取添加: `blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"`
- 列出跟踪的博客: `blogwatcher-cli blogs`
- 移除博客: `blogwatcher-cli remove "My Blog" --yes`
- 从 OPML 导入: `blogwatcher-cli import subscriptions.opml`

### 扫描和阅读

- 扫描所有博客: `blogwatcher-cli scan`
- 扫描单个博客: `blogwatcher-cli scan "My Blog"`
- 列出未读文章: `blogwatcher-cli articles`
- 列出所有文章: `blogwatcher-cli articles --all`
- 按博客过滤: `blogwatcher-cli articles --blog "My Blog"`
- 按类别过滤: `blogwatcher-cli articles --category "Engineering"`
- 标记文章已读: `blogwatcher-cli read 1`
- 标记文章未读: `blogwatcher-cli unread 1`
- 标记全部已读: `blogwatcher-cli read-all`
- 标记某博客全部已读: `blogwatcher-cli read-all --blog "My Blog" --yes`

## 环境变量

所有标志都可以通过带有 `BLOGWATCHER_` 前缀的环境变量设置：

| 变量 | 描述 |
|---|---|
| `BLOGWATCHER_DB` | SQLite 数据库文件路径 |
| `BLOGWATCHER_WORKERS` | 并发扫描工作线程数（默认：8） |
| `BLOGWATCHER_SILENT` | 扫描时仅输出 "scan done" |
| `BLOGWATCHER_YES` | 跳过确认提示 |
| `BLOGWATCHER_CATEGORY` | 按类别过滤文章的默认过滤器 |

## 输出示例

```
$ blogwatcher-cli blogs
Tracked blogs (1):

  xkcd
    URL: https://xkcd.com
    Feed: https://xkcd.com/atom.xml
    Last scanned: 2026-04-03 10:30
```

```
$ blogwatcher-cli scan
Scanning 1 blog(s)...

  xkcd
    Source: RSS | Found: 4 | New: 4

Found 4 new article(s) total!
```

```
$ blogwatcher-cli articles
Unread articles (2):

  [1] [new] Barrel - Part 13
       Blog: xkcd
       URL: https://xkcd.com/3095/
       Published: 2026-04-02
       Categories: Comics, Science

  [2] [new] Volcano Fact
       Blog: xkcd
       URL: https://xkcd.com/3094/
       Published: 2026-04-01
       Categories: Comics
```

## 注意事项

- 未提供 `--feed-url` 时，自动从博客主页发现 RSS/Atom 源。
- 如果 RSS 失败且配置了 `--scrape-selector`，则回退到 HTML 抓取。
- RSS/Atom 源中的类别会被存储，可用于过滤文章。
- 从 Feedly、Inoreader、NewsBlur 等导出的 OPML 文件批量导入博客。
- 数据库默认存储在 `~/.blogwatcher-cli/blogwatcher-cli.db`（使用 `--db` 或 `BLOGWATCHER_DB` 覆盖）。
- 使用 `blogwatcher-cli <command> --help` 查看所有标志和选项。

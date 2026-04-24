---
name: huggingface-hub
description: Hugging Face Hub CLI (hf) — 搜索、下载和上传模型和数据集，管理仓库，使用 SQL 查询数据集，部署推理端点，管理 Spaces 和存储桶。
version: 1.0.0
author: Hugging Face
license: MIT
tags: [huggingface, hf, models, datasets, hub, mlops]
---

# Hugging Face CLI (`hf`) 参考指南

`hf` 命令是与 Hugging Face Hub 交互的现代命令行界面，提供管理仓库、模型、数据集和 Spaces 的工具。

> **重要：** `hf` 命令替代了现已弃用的 `huggingface-cli` 命令。

## 快速开始
*   **安装：** `curl -LsSf https://hf.co/cli/install.sh | bash -s`
*   **帮助：** 使用 `hf --help` 查看所有可用功能和实际示例。
*   **身份验证：** 推荐通过 `HF_TOKEN` 环境变量或 `--token` 标志。

---

## 核心命令

### 通用操作
*   `hf download REPO_ID`：从 Hub 下载文件。
*   `hf upload REPO_ID`：上传文件/文件夹（推荐用于单次提交）。
*   `hf upload-large-folder REPO_ID LOCAL_PATH`：推荐用于大目录的可恢复上传。
*   `hf sync`：在本地目录和存储桶之间同步文件。
*   `hf env` / `hf version`：查看环境和版本信息。

### 身份验证 (`hf auth`)
*   `login` / `logout`：使用来自 [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) 的令牌管理会话。
*   `list` / `switch`：管理和切换多个存储的访问令牌。
*   `whoami`：识别当前登录的账户。

### 仓库管理 (`hf repos`)
*   `create` / `delete`：创建或永久删除仓库。
*   `duplicate`：将模型、数据集或 Space 克隆到新 ID。
*   `move`：在命名空间之间转移仓库。
*   `branch` / `tag`：管理类 Git 引用。
*   `delete-files`：使用模式删除特定文件。

---

## 专业 Hub 交互

### 数据集和模型
*   **数据集：** `hf datasets list`、`info` 和 `parquet`（列出 parquet URL）。
*   **SQL 查询：** `hf datasets sql SQL` — 通过 DuckDB 对数据集 parquet URL 执行原始 SQL。
*   **模型：** `hf models list` 和 `info`。
*   **论文：** `hf papers list` — 查看每日论文。

### 讨论和 Pull Requests (`hf discussions`)
*   管理 Hub 贡献的生命周期：`list`、`create`、`info`、`comment`、`close`、`reopen` 和 `rename`。
*   `diff`：查看 PR 中的更改。
*   `merge`：完成 pull requests。

### 基础设施和计算
*   **端点：** 部署和管理推理端点（`deploy`、`pause`、`resume`、`scale-to-zero`、`catalog`）。
*   **任务：** 在 HF 基础设施上运行计算任务。包括 `hf jobs uv` 用于运行带内联依赖的 Python 脚本，以及 `stats` 用于资源监控。
*   **Spaces：** 管理交互式应用。包括 `dev-mode` 和 `hot-reload` 用于 Python 文件无需完全重启。

### 存储和自动化
*   **存储桶：** 完整的 S3 类存储桶管理（`create`、`cp`、`mv`、`rm`、`sync`）。
*   **缓存：** 使用 `list`、`prune`（删除分离的版本）和 `verify`（校验和检查）管理本地存储。
*   **Webhooks：** 通过管理 Hub webhooks 自动执行工作流（`create`、`watch`、`enable`/`disable`）。
*   **集合：** 将 Hub 项目组织为集合（`add-item`、`update`、`list`）。

---

## 高级用法和技巧

### 全局标志
*   `--format json`：生成机器可读输出用于自动化。
*   `-q` / `--quiet`：仅限制输出为 ID。

### 扩展和技能
*   **扩展：** 使用 `hf extensions install REPO_ID` 通过 GitHub 仓库扩展 CLI 功能。
*   **技能：** 使用 `hf skills add` 管理 AI 助手技能。

---
name: github-issues
description: 创建、管理、分类和关闭 GitHub Issues。搜索现有 Issues、添加标签、分配人员并链接到 PR。配合 gh CLI 使用，或回退到通过 curl 使用 git + GitHub REST API。
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Issues, 项目管理, Bug 跟踪, 分类]
    related_skills: [github-auth, github-pr-workflow]
---

# GitHub Issues 管理

创建、搜索、分类和管理 GitHub Issues。每节先展示 `gh`，然后是 `curl` 回退。

## 前提条件

- 已通过 GitHub 身份验证（参见 `github-auth` 技能）
- 在带有 GitHub 远程的 git 仓库内，或显式指定仓库

### 设置

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. 查看 Issues

**配合 gh：**

```bash
gh issue list
gh issue list --state open --label "bug"
gh issue list --assignee @me
gh issue list --search "authentication error" --state all
gh issue view 42
```

**配合 curl：**

```bash
# 列出开放 Issues
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&per_page=20" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin):
    if 'pull_request' not in i:  # GitHub API 在 /issues 中也返回 PR
        labels = ', '.join(l['name'] for l in i['labels'])
        print(f\"#{i['number']:5}  {i['state']:6}  {labels:30}  {i['title']}\")"

# 按标签过滤
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&labels=bug&per_page=20" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin):
    if 'pull_request' not in i:
        print(f\"#{i['number']}  {i['title']}\")"

# 查看特定 Issue
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42 \
  | python3 -c "
import sys, json
i = json.load(sys.stdin)
labels = ', '.join(l['name'] for l in i['labels'])
assignees = ', '.join(a['login'] for a in i['assignees'])
print(f\"#{i['number']}: {i['title']}\")
print(f\"State: {i['state']}  Labels: {labels}  Assignees: {assignees}\")
print(f\"Author: {i['user']['login']}  Created: {i['created_at']}\")
print(f\"\n{i['body']}\")"

# 搜索 Issues
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/search/issues?q=authentication+error+repo:$OWNER/$REPO" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin)['items']:
    print(f\"#{i['number']}  {i['state']:6}  {i['title']}\")"
```

## 2. 创建 Issues

**配合 gh：**

```bash
gh issue create \
  --title "Login redirect ignores ?next= parameter" \
  --body "## Description
After logging in, users always land on /dashboard.

## Steps to Reproduce
1. Navigate to /settings while logged out
2. Get redirected to /login?next=/settings
3. Log in
4. Actual: redirected to /dashboard (should go to /settings)

## Expected Behavior
Respect the ?next= query parameter." \
  --label "bug,backend" \
  --assignee "username"
```

**配合 curl：**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues \
  -d '{
    "title": "Login redirect ignores ?next= parameter",
    "body": "## Description\nAfter logging in, users always land on /dashboard.\n\n## Steps to Reproduce\n1. Navigate to /settings while logged out\n2. Get redirected to /login?next=/settings\n3. Log in\n4. Actual: redirected to /dashboard\n\n## Expected Behavior\nRespect the ?next= query parameter.",
    "labels": ["bug", "backend"],
    "assignees": ["username"]
  }'
```

### Bug 报告模板

```
## Bug Description
<发生了什么>

## Steps to Reproduce
1. <步骤>
2. <步骤>

## Expected Behavior
<应该发生什么>

## Actual Behavior
<实际发生了什么>

## Environment
- OS: <系统>
- Version: <版本>
```

### 功能请求模板

```
## Feature Description
<你想要什么>

## Motivation
<为什么这会有用>

## Proposed Solution
<它可以如何工作>

## Alternatives Considered
<其他方法>
```

## 3. 管理 Issues

### 添加/移除标签

**配合 gh：**

```bash
gh issue edit 42 --add-label "priority:high,bug"
gh issue edit 42 --remove-label "needs-triage"
```

**配合 curl：**

```bash
# 添加标签
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42/labels \
  -d '{"labels": ["priority:high", "bug"]}'

# 移除标签
curl -s -X DELETE \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42/labels/needs-triage

# 列出仓库中可用标签
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/labels \
  | python3 -c "
import sys, json
for l in json.load(sys.stdin):
    print(f\"  {l['name']:30}  {l.get('description', '')}\")"
```

### 分配

**配合 gh：**

```bash
gh issue edit 42 --add-assignee username
gh issue edit 42 --add-assignee @me
```

**配合 curl：**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42/assignees \
  -d '{"assignees": ["username"]}'
```

### 注释

**配合 gh：**

```bash
gh issue comment 42 --body "Investigated — root cause is in auth middleware. Working on a fix."
```

**配合 curl：**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42/comments \
  -d '{"body": "Investigated — root cause is in auth middleware. Working on a fix."}'
```

### 关闭和重新打开

**配合 gh：**

```bash
gh issue close 42
gh issue close 42 --reason "not planned"
gh issue reopen 42
```

**配合 curl：**

```bash
# 关闭
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42 \
  -d '{"state": "closed", "state_reason": "completed"}'

# 重新打开
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42 \
  -d '{"state": "open"}'
```

### 将 Issues 链接到 PR

当 PR 合并时在正文中使用正确的关键词会自动关闭 Issues：

```
Closes #42
Fixes #42
Resolves #42
```

从 Issue 创建分支：

**配合 gh：**

```bash
gh issue develop 42 --checkout
```

**配合 git（手动等效）：**

```bash
git checkout main && git pull origin main
git checkout -b fix/issue-42-login-redirect
```

## 4. Issue 分类工作流

当被要求分类 Issues 时：

1. **列出未分类的 Issues：**

```bash
# 配合 gh
gh issue list --label "needs-triage" --state open

# 配合 curl
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?labels=needs-triage&state=open" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin):
    if 'pull_request' not in i:
        print(f\"#{i['number']}  {i['title']}\")"
```

2. **阅读并分类**每个 Issue（查看详细信息，理解 Bug/功能）

3. **应用标签和优先级**（参见上面的管理 Issues）

4. **分配**如果负责人明确

5. **用分类注释注释**如果需要

## 5. 批量操作

对于批处理操作，将 API 调用与 shell 脚本结合：

**配合 gh：**

```bash
# 关闭带有特定标签的所有 Issues
gh issue list --label "wontfix" --json number --jq '.[].number' | \
  xargs -I {} gh issue close {} --reason "not planned"
```

**配合 curl：**

```bash
# 列出带有标签的 Issue 号，然后关闭每个
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?labels=wontfix&state=open" \
  | python3 -c "import sys,json; [print(i['number']) for i in json.load(sys.stdin)]" \
  | while read num; do
    curl -s -X PATCH \
      -H "Authorization: token $GITHUB_TOKEN" \
      https://api.github.com/repos/$OWNER/$REPO/issues/$num \
      -d '{"state": "closed", "state_reason": "not_planned"}'
    echo "Closed #$num"
  done
```

## 快速参考表

| 操作 | gh | curl 端点 |
|--------|-----|--------------|
| 列出 Issues | `gh issue list` | `GET /repos/{o}/{r}/issues` |
| 查看 Issue | `gh issue view N` | `GET /repos/{o}/{r}/issues/N` |
| 创建 Issue | `gh issue create ...` | `POST /repos/{o}/{r}/issues` |
| 添加标签 | `gh issue edit N --add-label ...` | `POST /repos/{o}/{r}/issues/N/labels` |
| 分配 | `gh issue edit N --add-assignee ...` | `POST /repos/{o}/{r}/issues/N/assignees` |
| 注释 | `gh issue comment N --body ...` | `POST /repos/{o}/{r}/issues/N/comments` |
| 关闭 | `gh issue close N` | `PATCH /repos/{o}/{r}/issues/N` |
| 搜索 | `gh issue list --search "..."` | `GET /search/issues?q=...` |

---
name: github-code-review
description: 通过分析 git diff、在 PR 上留下内联注释和执行彻底的推送前审查来审查代码更改。配合 gh CLI 使用，或回退到通过 curl 使用 git + GitHub REST API。
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, 代码审查, Pull-Requests, Git, 质量]
    related_skills: [github-auth, github-pr-workflow]
---

# GitHub 代码审查

在推送前对本地更改执行代码审查，或在 GitHub 上审查开放 PR。本技能的大部分使用普通 `git`——`gh`/`curl` 拆分仅在 PR 级交互时重要。

## 前提条件

- 已通过 GitHub 身份验证（参见 `github-auth` 技能）
- 在 git 仓库内

### 设置（用于 PR 交互）

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

## 1. 审查本地更改（推送前）

这是纯 `git`——随处可用，不需要 API。

### 获取 Diff

```bash
# 暂存的更改（将要提交的内容）
git diff --staged

# 与 main 的所有更改（PR 将包含的内容）
git diff main...HEAD

# 仅文件名
git diff main...HEAD --name-only

# 统计摘要（每个文件的插入/删除）
git diff main...HEAD --stat
```

### 审查策略

1. **首先获取全局概览：**

```bash
git diff main...HEAD --stat
git log main..HEAD --oneline
```

2. **逐文件审查**——使用 `read_file` 查看更改文件的完整上下文，并使用 diff 查看更改内容：

```bash
git diff main...HEAD -- src/auth/login.py
```

3. **检查常见问题：**

```bash
# 遗留的调试语句、TODO、console.log
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|HACK\|XXX\|debugger"

# 意外暂存的大文件
git diff main...HEAD --stat | sort -t'|' -k2 -rn | head -10

# 秘密或凭据模式
git diff main...HEAD | grep -in "password\|secret\|api_key\|token.*=\|private_key"

# 合并冲突标记
git diff main...HEAD | grep -n "<<<<<<\|>>>>>>\|======="
```

4. **向用户呈现结构化反馈。**

### 审查输出格式

审查本地更改时，按此结构呈现发现：

```
## 代码审查摘要

### 关键
- **src/auth.py:45** — SQL 注入：用户输入直接传递给查询。
  建议：使用参数化查询。

### 警告
- **src/models/user.py:23** — 密码以明文存储。使用 bcrypt 或 argon2。
- **src/api/routes.py:112** — 登录端点没有限速。

### 建议
- **src/utils/helpers.py:8** — 与 `src/core/utils.py:34` 中的逻辑重复。合并。
- **tests/test_auth.py** — 缺少边界情况：过期令牌测试。

### 良好
- 中间层的关注点分离干净
- 正常路径的测试覆盖良好
```

---

## 2. 审查 GitHub 上的 Pull Request

### 查看 PR 详情

**配合 gh：**

```bash
gh pr view 123
gh pr diff 123
gh pr diff 123 --name-only
```

**配合 git + curl：**

```bash
PR_NUMBER=123

# 获取 PR 详情
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "
import sys, json
pr = json.load(sys.stdin)
print(f\"Title: {pr['title']}\")
print(f\"Author: {pr['user']['login']}\")
print(f\"Branch: {pr['head']['ref']} -> {pr['base']['ref']}\")
print(f\"State: {pr['state']}\")
print(f\"Body:\n{pr['body']}\")"

# 列出更改的文件
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/files \
  | python3 -c "
import sys, json
for f in json.load(sys.stdin):
    print(f\"{f['status']:10} +{f['additions']:-4} -{f['deletions']:-4}  {f['filename']}\")"
```

### 本地检出 PR 进行全面审查

这适用于普通 `git`——不需要 `gh`：

```bash
# 获取 PR 分支并检出
git fetch origin pull/123/head:pr-123
git checkout pr-123

# 现在你可以使用 read_file、search_files、运行测试等

# 查看与基础分支的 diff
git diff main...pr-123
```

**配合 gh（快捷方式）：**

```bash
gh pr checkout 123
```

### 在 PR 上留下注释

**通用 PR 注释——配合 gh：**

```bash
gh pr comment 123 --body "Overall looks good, a few suggestions below."
```

**通用 PR 注释——配合 curl：**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/$PR_NUMBER/comments \
  -d '{"body": "Overall looks good, a few suggestions below."}'
```

### 留下内联审查注释

**单个内联注释——配合 gh（通过 API）：**

```bash
HEAD_SHA=$(gh pr view 123 --json headRefOid --jq '.headRefOid')

gh api repos/$OWNER/$REPO/pulls/123/comments \
  --method POST \
  -f body="This could be simplified with a list comprehension." \
  -f path="src/auth/login.py" \
  -f commit_id="$HEAD_SHA" \
  -f line=45 \
  -f side="RIGHT"
```

**单个内联注释——配合 curl：**

```bash
# 获取头部提交 SHA
HEAD_SHA=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments \
  -d "{
    \"body\": \"This could be simplified with a list comprehension.\",
    \"path\": \"src/auth/login.py\",
    \"commit_id\": \"$HEAD_SHA\",
    \"line\": 45,
    \"side\": \"RIGHT\"
  }"
```

### 提交正式审查（批准/请求更改）

**配合 gh：**

```bash
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."
gh pr review 123 --comment --body "Some suggestions, nothing blocking."
```

**配合 curl——原子提交多注释审查：**

```bash
HEAD_SHA=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews \
  -d "{
    \"commit_id\": \"$HEAD_SHA\",
    \"event\": \"COMMENT\",
    \"body\": \"Code review from Hermes Agent\",
    \"comments\": [
      {\"path\": \"src/auth.py\", \"line\": 45, \"body\": \"Use parameterized queries to prevent SQL injection.\"},
      {\"path\": \"src/models/user.py\", \"line\": 23, \"body\": \"Hash passwords with bcrypt before storing.\"},
      {\"path\": \"tests/test_auth.py\", \"line\": 1, \"body\": \"Add test for expired token edge case.\"}
    ]
  }"
```

事件值：`"APPROVE"`、`"REQUEST_CHANGES"`、`"COMMENT"`

`line` 字段指文件*新*版本中的行号。对于删除的行，使用 `"side": "LEFT"`。

---

## 3. 审查清单

执行代码审查（本地或 PR）时，系统地检查：

### 正确性
- 代码是否做了它声称的事情？
- 边界情况是否已处理（空输入、null、大数据、并发访问）？
- 错误路径是否优雅处理？

### 安全性
- 没有硬编码的秘密、凭据或 API 密钥
- 面向用户的输入是否有输入验证
- 没有 SQL 注入、XSS 或路径遍历
- 需要时是否有 auth/authz 检查

### 代码质量
- 清晰的命名（变量、函数、类）
- 没有不必要的复杂性或过早抽象
- DRY——没有应该提取的重复逻辑
- 函数是否专注（单一职责）

### 测试
- 新代码路径是否已测试？
- 正常路径和边界情况是否覆盖？
- 测试是否可读和可维护？

### 性能
- 没有 N+1 查询或不必要的循环
- 在有益处是否有适当缓存
- 异步代码路径中没有阻塞操作

### 文档
- 公共 API 是否有文档
- 非显而易见的逻辑是否有注释解释"为什么"
- 如果行为更改，README 是否已更新

---

## 4. 推送前审查工作流

当用户要求你"审查代码"或"推送前检查"时：

1. `git diff main...HEAD --stat`——查看更改范围
2. `git diff main...HEAD`——阅读完整 diff
3. 对于每个更改的文件，如果需要更多上下文则使用 `read_file`
4. 应用上面的清单
5. 以结构化格式呈现发现（关键/警告/建议/良好）
6. 如果发现关键问题，提供在用户推送前修复它们

---

## 5. PR 审查工作流（端到端）

当用户要求你"审查 PR #N"、"查看此 PR"或给你 PR URL 时，遵循此流程：

### 步骤 1：设置环境

```bash
source ~/.hermes/skills/github/github-auth/scripts/gh-env.sh
# 或运行本技能顶部的内联设置块
```

### 步骤 2：收集 PR 上下文

获取 PR 元数据、描述和更改文件列表以在深入代码之前理解范围。

**配合 gh：**
```bash
gh pr view 123
gh pr diff 123 --name-only
gh pr checks 123
```

**配合 curl：**
```bash
PR_NUMBER=123

# PR 详情（标题、作者、描述、分支）
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER

# 更改文件及行数
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER/files
```

### 步骤 3：本地检出 PR

这使你可以完全访问 `read_file`、`search_files` 以及运行测试的能力。

```bash
git fetch origin pull/$PR_NUMBER/head:pr-$PR_NUMBER
git checkout pr-$PR_NUMBER
```

### 步骤 4：阅读 diff 并理解更改

```bash
# 与基础分支的完整 diff
git diff main...HEAD

# 或大文件逐文件
git diff main...HEAD --name-only
# 然后对每个文件：
git diff main...HEAD -- path/to/file.py
```

对于每个更改的文件，使用 `read_file` 查看更改周围的完整上下文——仅凭 diff 可能会错过只有周围代码才能看到的问题。

### 步骤 5：本地运行自动检查（如适用）

```bash
# 如果有测试套件则运行测试
python -m pytest 2>&1 | tail -20
# 或：npm test、cargo test、go test ./... 等

# 如果配置了则运行 linter
ruff check . 2>&1 | head -30
# 或：eslint、clippy 等
```

### 步骤 6：应用审查清单（第 3 节）

逐一检查每个类别：正确性、安全性、代码质量、测试、性能、文档。

### 步骤 7：将审查发布到 GitHub

收集你的发现并将其作为带有内联注释的正式审查提交。

**配合 gh：**
```bash
# 如果没有问题——批准
gh pr review $PR_NUMBER --approve --body "Reviewed by Hermes Agent. Code looks clean — good test coverage, no security concerns."

# 如果有问题——请求更改并带内联注释
gh pr review $PR_NUMBER --request-changes --body "Found a few issues — see inline comments."
```

**配合 curl——带有多个内联注释的原子审查：**
```bash
HEAD_SHA=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")

# 构建审查 JSON——事件是 APPROVE、REQUEST_CHANGES 或 COMMENT
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER/reviews \
  -d "{
    \"commit_id\": \"$HEAD_SHA\",
    \"event\": \"REQUEST_CHANGES\",
    \"body\": \"## Hermes Agent Review\n\nFound 2 issues, 1 suggestion. See inline comments.\",
    \"comments\": [
      {\"path\": \"src/auth.py\", \"line\": 45, \"body\": \"🔴 **Critical:** User input passed directly to SQL query — use parameterized queries.\"},
      {\"path\": \"src/models.py\", \"line\": 23, \"body\": \"⚠️ **Warning:** Password stored without hashing.\"},
      {\"path\": \"src/utils.py\", \"line\": 8, \"body\": \"💡 **Suggestion:** This duplicates logic in core/utils.py:34.\"}
    ]
  }"
```

### 步骤 8：同时发布摘要注释

除了内联注释外，留下顶级摘要，以便 PR 作者一目了然地获得完整画面。使用 `references/review-output-template.md` 中的审查输出格式。

**配合 gh：**
```bash
gh pr comment $PR_NUMBER --body "$(cat <<'EOF'
## Code Review Summary

**Verdict: Changes Requested** (2 issues, 1 suggestion)

### 🔴 Critical
- **src/auth.py:45** — SQL injection vulnerability

### ⚠️ Warnings
- **src/models.py:23** — Plaintext password storage

### 💡 Suggestions
- **src/utils.py:8** — Duplicated logic, consider consolidating

### ✅ Looks Good
- Clean API design
- Good error handling in the middleware layer

---
*Reviewed by Hermes Agent*
EOF
)"
```

### 步骤 9：清理

```bash
git checkout main
git branch -D pr-$PR_NUMBER
```

### 决策：批准与请求更改与注释

- **批准**——没有关键或警告级问题，只有小建议或全部通过
- **请求更改**——任何应在合并前修复的关键或警告级问题
- **注释**——观察和建议，但没有阻塞（用于不确定或 PR 是草稿时）

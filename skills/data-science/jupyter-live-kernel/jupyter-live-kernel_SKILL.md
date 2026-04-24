---
name: jupyter-live-kernel
description: >
  通过hamelnb使用活动Jupyter内核进行有状态、迭代的Python执行。
  当任务涉及探索、迭代或检查中间结果时加载此技能 — 数据科学、ML实验、API探索或
  逐步构建复杂代码。使用终端对活动Jupyter内核运行CLI命令。无需新工具。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [jupyter, notebook, repl, data-science, exploration, iterative]
    category: data-science
---

# Jupyter活动内核（hamelnb）

通过活动Jupyter内核为您提供**有状态的Python REPL**。变量在执行间持久化。当您需要增量构建状态、探索API、检查DataFrame或迭代复杂代码时，使用此技能代替`execute_code`。

## 何时使用此技能与其他工具

| 工具 | 使用场景 |
|------|----------|
| **此技能** | 迭代探索、跨步骤状态、数据科学、ML、"让我试试这个并检查" |
| `execute_code` | 需要hermes工具访问的一次性脚本（web_search、文件操作）。无状态。 |
| `terminal` | Shell命令、构建、安装、git、进程管理 |

**经验法则：** 如果任务需要Jupyter notebook，使用此技能。

## 前置条件

1. 必须安装 **uv**（检查：`which uv`）
2. 必须安装 **JupyterLab**：`uv tool install jupyterlab`
3. 必须运行Jupyter服务器（见下方设置）

## 设置

hamelnb脚本位置：
```
SCRIPT="$HOME/.agent-skills/hamelnb/skills/jupyter-live-kernel/scripts/jupyter_live_kernel.py"
```

如果尚未克隆：
```
git clone https://github.com/hamelsmu/hamelnb.git ~/.agent-skills/hamelnb
```

### 启动JupyterLab

检查服务器是否已在运行：
```
uv run "$SCRIPT" servers
```

如果未找到服务器，启动一个：
```
jupyter-lab --no-browser --port=8888 --notebook-dir=$HOME/notebooks \
  --IdentityProvider.token='' --ServerApp.password='' > /tmp/jupyter.log 2>&1 &
sleep 3
```

注意：令牌/密码已禁用以供本地智能体访问。服务器无头运行。

### 创建用于REPL的Notebook

如果您只需要REPL（没有现有notebook），创建最小笔记本文件：
```
mkdir -p ~/notebooks
```
编写一个带有一个空代码单元格的最小.ipynb JSON文件，然后通过Jupyter REST API启动内核会话：
```
curl -s -X POST http://127.0.0.1:8888/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"path":"scratch.ipynb","type":"notebook","name":"scratch.ipynb","kernel":{"name":"python3"}}'
```

## 核心工作流

所有命令返回结构化JSON。始终使用 `--compact` 以节省令牌。

### 1. 发现服务器和笔记本

```
uv run "$SCRIPT" servers --compact
uv run "$SCRIPT" notebooks --compact
```

### 2. 执行代码（主要操作）

```
uv run "$SCRIPT" execute --path <notebook.ipynb> --code '<python code>' --compact
```

状态在执行调用间持久化。变量、导入、对象都保留。

多行代码可以使用 $'...' 引用：
```
uv run "$SCRIPT" execute --path scratch.ipynb --code $'import os\nfiles = os.listdir(".")\nprint(f"找到 {len(files)} 个文件")' --compact
```

### 3. 检查活动变量

```
uv run "$SCRIPT" variables --path <notebook.ipynb> list --compact
uv run "$SCRIPT" variables --path <notebook.ipynb> preview --name <varname> --compact
```

### 4. 编辑笔记本单元格

```
# 查看当前单元格
uv run "$SCRIPT" contents --path <notebook.ipynb> --compact

# 插入新单元格
uv run "$SCRIPT" edit --path <notebook.ipynb> insert \
  --at-index <N> --cell-type code --source '<code>' --compact

# 替换单元格源代码（使用contents输出中的cell-id）
uv run "$SCRIPT" edit --path <notebook.ipynb> replace-source \
  --cell-id <id> --source '<new code>' --compact

# 删除单元格
uv run "$SCRIPT" edit --path <notebook.ipynb> delete --cell-id <id> --compact
```

### 5. 验证（重启并全部运行）

仅在用户要求干净验证或您需要确认笔记本从上到下运行时使用：

```
uv run "$SCRIPT" restart-run-all --path <notebook.ipynb> --save-outputs --compact
```

## 实践经验技巧

1. **服务器启动后的首次执行可能超时** — 内核需要片刻初始化。如果超时，重试即可。

2. **内核Python是JupyterLab的Python** — 包必须安装在该环境中。如果需要额外的包，先安装到JupyterLab工具环境。

3. **--compact标志节省大量令牌** — 始终使用它。没有它JSON输出会非常冗长。

4. **纯REPL使用**，创建scratch.ipynb并不要费心单元格编辑。只需重复使用 `execute`。

5. **参数顺序很重要** — 子命令标志如 `--path` 在子子命令之前。例如：`variables --path nb.ipynb list` 而不是 `variables list --path nb.ipynb`。

6. **如果会话不存在**，您需要通过REST API启动一个（见设置部分）。没有活动内核会话工具无法执行。

7. **错误以JSON形式返回** 带回溯 — 阅读 `ename` 和 `evalue` 字段了解出错原因。

8. **偶尔的websocket超时** — 某些操作可能首次尝试时超时，尤其是内核重启后。重试一次再升级。

## 超时默认值

脚本每次执行默认30秒超时。对于长时间运行的操作，传递 `--timeout 120`。对于初始设置或重计算使用宽松的超时（60+）。

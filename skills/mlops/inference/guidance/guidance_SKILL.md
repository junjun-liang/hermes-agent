---
name: guidance
description: 使用正则表达式和语法控制 LLM 输出，保证有效的 JSON/XML/代码生成，强制执行结构化格式，并使用 Guidance 构建多步工作流 — Microsoft Research 的约束生成框架
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [guidance, transformers]
metadata:
  hermes:
    tags: [Prompt Engineering, Guidance, Constrained Generation, Structured Output, JSON Validation, Grammar, Microsoft Research, Format Enforcement, Multi-Step Workflows]

---

# Guidance：约束 LLM 生成

## 何时使用此技能

当需要以下情况时使用 Guidance：
- **使用正则或语法控制 LLM 输出语法**
- **保证有效的 JSON/XML/代码** 生成
- **减少延迟** 相比传统提示方法
- **强制执行结构化格式**（日期、邮箱、ID 等）
- **构建带 Python 控制流的多步工作流**
- **通过语法约束防止无效输出**

**GitHub Stars**：18,000+ | **来自**：Microsoft Research

## 安装

```bash
# 基本安装
pip install guidance

# 带特定后端
pip install guidance[transformers]  # Hugging Face 模型
pip install guidance[llama_cpp]     # llama.cpp 模型
```

## 快速开始

### 基本示例：结构化生成

```python
from guidance import models, gen

# 加载模型（支持 OpenAI、Transformers、llama.cpp）
lm = models.OpenAI("gpt-4")

# 带约束生成
result = lm + "法国的首都是 " + gen("capital", max_tokens=5)

print(result["capital"])  # "Paris"
```

### 与 Anthropic Claude 配合

```python
from guidance import models, gen, system, user, assistant

# 配置 Claude
lm = models.Anthropic("claude-sonnet-4-5-20250929")

# 使用上下文管理器进行对话格式
with system():
    lm += "你是一个有用的助手。"

with user():
    lm += "法国的首都是什么？"

with assistant():
    lm += gen(max_tokens=20)
```

## 核心概念

### 1. 上下文管理器

Guidance 使用 Pythonic 上下文管理器进行对话式交互。

```python
from guidance import system, user, assistant, gen

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# 系统消息
with system():
    lm += "你是 JSON 生成专家。"

# 用户消息
with user():
    lm += "生成一个带 name 和 age 的人员对象。"

# 助手响应
with assistant():
    lm += gen("response", max_tokens=100)

print(lm["response"])
```

**好处：**
- 自然的对话流
- 清晰的角色分离
- 易于阅读和维护

### 2. 约束生成

Guidance 确保输出匹配使用正则或语法指定的模式。

#### 正则约束

```python
from guidance import models, gen

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# 约束为有效邮箱格式
lm += "Email: " + gen("email", regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# 约束为日期格式（YYYY-MM-DD）
lm += "Date: " + gen("date", regex=r"\d{4}-\d{2}-\d{2}")

# 约束为电话号码
lm += "Phone: " + gen("phone", regex=r"\d{3}-\d{3}-\d{4}")

print(lm["email"])  # 保证有效邮箱
print(lm["date"])   # 保证 YYYY-MM-DD 格式
```

**工作原理：**
- 正则转换为 token 级语法
- 无效 token 在生成期间被过滤
- 模型只能生成匹配的输出

#### 选择约束

```python
from guidance import models, gen, select

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# 约束为特定选择
lm += "Sentiment: " + select(["positive", "negative", "neutral"], name="sentiment")

# 多选
lm += "Best answer: " + select(
    ["A) Paris", "B) London", "C) Berlin", "D) Madrid"],
    name="answer"
)

print(lm["sentiment"])  # 之一：positive, negative, neutral
print(lm["answer"])     # 之一：A, B, C, 或 D
```

### 3. Token 修复

Guidance 自动"修复"提示和生成之间的 token 边界。

**问题：** 分词创建不自然的边界。

```python
# 没有 token 修复
prompt = "The capital of France is "
# 最后一个 token: " is "
# 第一个生成的 token 可能是 " Par"（带前导空格）
# 结果: "The capital of France is  Paris"（双空格！）
```

**解决方案：** Guidance 回退一个 token 并重新生成。

```python
from guidance import models, gen

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# 默认启用 token 修复
lm += "The capital of France is " + gen("capital", max_tokens=5)
# 结果: "The capital of France is Paris"（正确空格）
```

**好处：**
- 自然文本边界
- 无尴尬空格问题
- 更好的模型性能（看到自然 token 序列）

### 4. 基于语法的生成

使用上下文无关语法定义复杂结构。

```python
from guidance import models, gen

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# JSON 语法（简化）
json_grammar = """
{
    "name": <gen name regex="[A-Za-z ]+" max_tokens=20>,
    "age": <gen age regex="[0-9]+" max_tokens=3>,
    "email": <gen email regex="[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}" max_tokens=50>
}
"""

# 生成有效 JSON
lm += gen("person", grammar=json_grammar)

print(lm["person"])  # 保证有效 JSON 结构
```

**用例：**
- 复杂结构化输出
- 嵌套数据结构
- 编程语言语法
- 领域特定语言

### 5. Guidance 函数

使用 `@guidance` 装饰器创建可重用的生成模式。

```python
from guidance import guidance, gen, models

@guidance
def generate_person(lm):
    """生成一个带姓名和年龄的人。"""
    lm += "Name: " + gen("name", max_tokens=20, stop="\n")
    lm += "\nAge: " + gen("age", regex=r"[0-9]+", max_tokens=3)
    return lm

# 使用函数
lm = models.Anthropic("claude-sonnet-4-5-20250929")
lm = generate_person(lm)

print(lm["name"])
print(lm["age"])
```

**有状态函数：**

```python
@guidance(stateless=False)
def react_agent(lm, question, tools, max_rounds=5):
    """带工具使用的 ReAct 代理。"""
    lm += f"Question: {question}\n\n"

    for i in range(max_rounds):
        # 思考
        lm += f"Thought {i+1}: " + gen("thought", stop="\n")

        # 行动
        lm += "\nAction: " + select(list(tools.keys()), name="action")

        # 执行工具
        tool_result = tools[lm["action"]]()
        lm += f"\nObservation: {tool_result}\n\n"

        # 检查是否完成
        lm += "Done? " + select(["Yes", "No"], name="done")
        if lm["done"] == "Yes":
            break

    # 最终答案
    lm += "\nFinal Answer: " + gen("answer", max_tokens=100)
    return lm
```

## 后端配置

### Anthropic Claude

```python
from guidance import models

lm = models.Anthropic(
    model="claude-sonnet-4-5-20250929",
    api_key="your-api-key"  # 或设置 ANTHROPIC_API_KEY 环境变量
)
```

### OpenAI

```python
lm = models.OpenAI(
    model="gpt-4o-mini",
    api_key="your-api-key"  # 或设置 OPENAI_API_KEY 环境变量
)
```

### 本地模型（Transformers）

```python
from guidance.models import Transformers

lm = Transformers(
    "microsoft/Phi-4-mini-instruct",
    device="cuda"  # 或 "cpu"
)
```

### 本地模型（llama.cpp）

```python
from guidance.models import LlamaCpp

lm = LlamaCpp(
    model_path="/path/to/model.gguf",
    n_ctx=4096,
    n_gpu_layers=35
)
```

## 常见模式

### 模式 1：JSON 生成

```python
from guidance import models, gen, system, user, assistant

lm = models.Anthropic("claude-sonnet-4-5-20250929")

with system():
    lm += "你生成有效 JSON。"

with user():
    lm += "生成一个带 name、age 和 email 的用户档案。"

with assistant():
    lm += """{
    "name": """ + gen("name", regex=r'"[A-Za-z ]+"', max_tokens=30) + """,
    "age": """ + gen("age", regex=r"[0-9]+", max_tokens=3) + """,
    "email": """ + gen("email", regex=r'"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"', max_tokens=50) + """
}"""

print(lm)  # 保证有效 JSON
```

### 模式 2：分类

```python
from guidance import models, gen, select

lm = models.Anthropic("claude-sonnet-4-5-20250929")

text = "This product is amazing! I love it."

lm += f"Text: {text}\n"
lm += "Sentiment: " + select(["positive", "negative", "neutral"], name="sentiment")
lm += "\nConfidence: " + gen("confidence", regex=r"[0-9]+", max_tokens=3) + "%"

print(f"情感: {lm['sentiment']}")
print(f"置信度: {lm['confidence']}%")
```

### 模式 3：多步推理

```python
from guidance import models, gen, guidance

@guidance
def chain_of_thought(lm, question):
    """生成带逐步推理的答案。"""
    lm += f"Question: {question}\n\n"

    # 生成多个推理步骤
    for i in range(3):
        lm += f"Step {i+1}: " + gen(f"step_{i+1}", stop="\n", max_tokens=100) + "\n"

    # 最终答案
    lm += "\nTherefore, the answer is: " + gen("answer", max_tokens=50)

    return lm

lm = models.Anthropic("claude-sonnet-4-5-20250929")
lm = chain_of_thought(lm, "200 的 15% 是多少？")

print(lm["answer"])
```

### 模式 4：ReAct 代理

```python
from guidance import models, gen, select, guidance

@guidance(stateless=False)
def react_agent(lm, question):
    """带工具使用的 ReAct 代理。"""
    tools = {
        "calculator": lambda expr: eval(expr),
        "search": lambda query: f"搜索结果：{query}",
    }

    lm += f"Question: {question}\n\n"

    for round in range(5):
        # 思考
        lm += f"Thought: " + gen("thought", stop="\n") + "\n"

        # 行动选择
        lm += "Action: " + select(["calculator", "search", "answer"], name="action")

        if lm["action"] == "answer":
            lm += "\nFinal Answer: " + gen("answer", max_tokens=100)
            break

        # 行动输入
        lm += "\nAction Input: " + gen("action_input", stop="\n") + "\n"

        # 执行工具
        if lm["action"] in tools:
            result = tools[lm["action"]](lm["action_input"])
            lm += f"Observation: {result}\n\n"

    return lm

lm = models.Anthropic("claude-sonnet-4-5-20250929")
lm = react_agent(lm, "25 * 4 + 10 等于多少？")
print(lm["answer"])
```

### 模式 5：数据提取

```python
from guidance import models, gen, guidance

@guidance
def extract_entities(lm, text):
    """从文本中提取结构化实体。"""
    lm += f"Text: {text}\n\n"

    # 提取人员
    lm += "Person: " + gen("person", stop="\n", max_tokens=30) + "\n"

    # 提取组织
    lm += "Organization: " + gen("organization", stop="\n", max_tokens=30) + "\n"

    # 提取日期
    lm += "Date: " + gen("date", regex=r"\d{4}-\d{2}-\d{2}", max_tokens=10) + "\n"

    # 提取位置
    lm += "Location: " + gen("location", stop="\n", max_tokens=30) + "\n"

    return lm

text = "Tim Cook announced at Apple Park on 2024-09-15 in Cupertino."

lm = models.Anthropic("claude-sonnet-4-5-20250929")
lm = extract_entities(lm, text)

print(f"人员: {lm['person']}")
print(f"组织: {lm['organization']}")
print(f"日期: {lm['date']}")
print(f"位置: {lm['location']}")
```

## 最佳实践

### 1. 使用正则进行格式验证

```python
# ✅ 好：正则保证有效格式
lm += "Email: " + gen("email", regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# ❌ 坏：自由生成可能产生无效邮箱
lm += "Email: " + gen("email", max_tokens=50)
```

### 2. 使用 select() 处理固定类别

```python
# ✅ 好：保证有效类别
lm += "Status: " + select(["pending", "approved", "rejected"], name="status")

# ❌ 坏：可能生成拼写错误或无效值
lm += "Status: " + gen("status", max_tokens=20)
```

### 3. 利用 Token 修复

```python
# Token 修复默认启用
# 不需要特殊操作 — 只需自然连接
lm += "The capital is " + gen("capital")  # 自动修复
```

### 4. 使用停止序列

```python
# ✅ 好：在换行处停止，用于单行输出
lm += "Name: " + gen("name", stop="\n")

# ❌ 坏：可能生成多行
lm += "Name: " + gen("name", max_tokens=50)
```

### 5. 创建可重用函数

```python
# ✅ 好：可重用模式
@guidance
def generate_person(lm):
    lm += "Name: " + gen("name", stop="\n")
    lm += "\nAge: " + gen("age", regex=r"[0-9]+")
    return lm

# 多次使用
lm = generate_person(lm)
lm += "\n\n"
lm = generate_person(lm)
```

### 6. 平衡约束

```python
# ✅ 好：合理的约束
lm += gen("name", regex=r"[A-Za-z ]+", max_tokens=30)

# ❌ 太严格：可能失败或非常慢
lm += gen("name", regex=r"^(John|Jane)$", max_tokens=10)
```

## 与替代方案比较

| 功能 | Guidance | Instructor | Outlines | LMQL |
|---------|----------|------------|----------|------|
| 正则约束 | ✅ 是 | ❌ 否 | ✅ 是 | ✅ 是 |
| 语法支持 | ✅ CFG | ❌ 否 | ✅ CFG | ✅ CFG |
| Pydantic 验证 | ❌ 否 | ✅ 是 | ✅ 是 | ❌ 否 |
| Token 修复 | ✅ 是 | ❌ 否 | ✅ 是 | ❌ 否 |
| 本地模型 | ✅ 是 | ⚠️ 有限 | ✅ 是 | ✅ 是 |
| API 模型 | ✅ 是 | ✅ 是 | ⚠️ 有限 | ✅ 是 |
| Pythonic 语法 | ✅ 是 | ✅ 是 | ✅ 是 | ❌ 类 SQL |
| 学习曲线 | 低 | 低 | 中 | 高 |

**何时选择 Guidance：**
- 需要正则/语法约束
- 想要 token 修复
- 构建带控制流的复杂工作流
- 使用本地模型（Transformers、llama.cpp）
- 偏好 Pythonic 语法

**何时选择替代方案：**
- Instructor：需要带自动重试的 Pydantic 验证
- Outlines：需要 JSON Schema 验证
- LMQL：偏好声明式查询语法

## 性能特征

**延迟减少：**
- 对于约束输出，比传统提示快 30-50%
- Token 修复减少不必要的重新生成
- 语法约束防止无效 token 生成

**内存使用：**
- 相比无约束生成的最小开销
- 语法编译在第一次使用后缓存
- 推理时高效的 token 过滤

**Token 效率：**
- 防止在无效输出上浪费 token
- 不需要重试循环
- 直接路径到有效输出

## 资源

- **文档**：https://guidance.readthedocs.io
- **GitHub**：https://github.com/guidance-ai/guidance（18k+ stars）
- **Notebooks**：https://github.com/guidance-ai/guidance/tree/main/notebooks
- **Discord**：提供社区支持

## 参见

- `references/constraints.md` — 综合正则和语法模式
- `references/backends.md` — 后端特定配置
- `references/examples.md` — 生产就绪示例

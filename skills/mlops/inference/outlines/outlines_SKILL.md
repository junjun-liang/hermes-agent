---
name: outlines
description: 在生成期间保证有效的 JSON/XML/代码结构，使用 Pydantic 模型进行类型安全的输出，支持本地模型（Transformers、vLLM），并使用 Outlines 最大化推理速度 — dottxt.ai 的结构化生成库
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [outlines, transformers, vllm, pydantic]
metadata:
  hermes:
    tags: [Prompt Engineering, Outlines, Structured Generation, JSON Schema, Pydantic, Local Models, Grammar-Based Generation, vLLM, Transformers, Type Safety]

---

# Outlines：结构化文本生成

## 何时使用此技能

当需要以下情况时使用 Outlines：
- **在生成期间保证有效的 JSON/XML/代码** 结构
- **使用 Pydantic 模型** 进行类型安全的输出
- **支持本地模型**（Transformers、llama.cpp、vLLM）
- **最大化推理速度**，零开销结构化生成
- **针对 JSON schema 自动生成**
- **在语法级别控制 token 采样**

**GitHub Stars**：8,000+ | **来自**：dottxt.ai（原 .txt）

## 安装

```bash
# 基本安装
pip install outlines

# 带特定后端
pip install outlines transformers  # Hugging Face 模型
pip install outlines llama-cpp-python  # llama.cpp
pip install outlines vllm  # vLLM 用于高吞吐
```

## 快速开始

### 基本示例：分类

```python
import outlines
from typing import Literal

# 加载模型
model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# 带类型约束生成
prompt = "Sentiment of 'This product is amazing!': "
generator = outlines.generate.choice(model, ["positive", "negative", "neutral"])
sentiment = generator(prompt)

print(sentiment)  # "positive"（保证是其中之一）
```

### 使用 Pydantic 模型

```python
from pydantic import BaseModel
import outlines

class User(BaseModel):
    name: str
    age: int
    email: str

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# 生成结构化输出
prompt = "Extract user: John Doe, 30 years old, john@example.com"
generator = outlines.generate.json(model, User)
user = generator(prompt)

print(user.name)   # "John Doe"
print(user.age)    # 30
print(user.email)  # "john@example.com"
```

## 核心概念

### 1. 约束 Token 采样

Outlines 使用有限状态机（FSM）在 logit 级别约束 token 生成。

**工作原理：**
1. 将 schema（JSON/Pydantic/正则）转换为上下文无关语法（CFG）
2. 将 CFG 转换为有限状态机（FSM）
3. 生成期间每一步过滤无效 token
4. 仅有一个有效 token 时快进

**好处：**
- **零开销**：过滤发生在 token 级别
- **速度提升**：快进确定性路径
- **保证有效性**：无效输出不可能

```python
import outlines

# Pydantic 模型 -> JSON schema -> CFG -> FSM
class Person(BaseModel):
    name: str
    age: int

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# 幕后：
# 1. Person -> JSON schema
# 2. JSON schema -> CFG
# 3. CFG -> FSM
# 4. FSM 在生成期间过滤 token

generator = outlines.generate.json(model, Person)
result = generator("Generate person: Alice, 25")
```

### 2. 结构化生成器

Outlines 提供针对不同输出类型的专用生成器。

#### 选择生成器

```python
# 多选
generator = outlines.generate.choice(
    model,
    ["positive", "negative", "neutral"]
)

sentiment = generator("Review: This is great!")
# 结果：三者之一
```

#### JSON 生成器

```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    in_stock: bool

# 生成匹配 schema 的有效 JSON
generator = outlines.generate.json(model, Product)
product = generator("Extract: iPhone 15, $999, available")

# 保证有效的 Product 实例
print(type(product))  # <class '__main__.Product'>
```

#### 正则生成器

```python
# 生成匹配正则的文本
generator = outlines.generate.regex(
    model,
    r"[0-9]{3}-[0-9]{3}-[0-9]{4}"  # 电话号码模式
)

phone = generator("Generate phone number:")
# 结果："555-123-4567"（保证匹配模式）
```

#### 整数/浮点生成器

```python
# 生成特定数值类型
int_generator = outlines.generate.integer(model)
age = int_generator("Person's age:")  # 保证整数

float_generator = outlines.generate.float(model)
price = float_generator("Product price:")  # 保证浮点
```

### 3. 模型后端

Outlines 支持多种本地和 API 后端。

#### Transformers（Hugging Face）

```python
import outlines

# 从 Hugging Face 加载
model = outlines.models.transformers(
    "microsoft/Phi-3-mini-4k-instruct",
    device="cuda"  # 或 "cpu"
)

# 与任何生成器配合使用
generator = outlines.generate.json(model, YourModel)
```

#### llama.cpp

```python
# 加载 GGUF 模型
model = outlines.models.llamacpp(
    "./models/llama-3.1-8b-instruct.Q4_K_M.gguf",
    n_gpu_layers=35
)

generator = outlines.generate.json(model, YourModel)
```

#### vLLM（高吞吐）

```python
# 用于生产部署
model = outlines.models.vllm(
    "meta-llama/Llama-3.1-8B-Instruct",
    tensor_parallel_size=2  # 多 GPU
)

generator = outlines.generate.json(model, YourModel)
```

#### OpenAI（有限支持）

```python
# 基本 OpenAI 支持
model = outlines.models.openai(
    "gpt-4o-mini",
    api_key="your-api-key"
)

# 注意：API 模型某些功能有限
generator = outlines.generate.json(model, YourModel)
```

### 4. Pydantic 集成

Outlines 具有一流的 Pydantic 支持，带自动 schema 转换。

#### 基本模型

```python
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str = Field(description="文章标题")
    author: str = Field(description="作者名称")
    word_count: int = Field(description="词数", gt=0)
    tags: list[str] = Field(description="标签列表")

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, Article)

article = generator("Generate article about AI")
print(article.title)
print(article.word_count)  # 保证 > 0
```

#### 嵌套模型

```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    age: int
    address: Address  # 嵌套模型

generator = outlines.generate.json(model, Person)
person = generator("Generate person in New York")

print(person.address.city)  # "New York"
```

#### 枚举和字面量

```python
from enum import Enum
from typing import Literal

class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Application(BaseModel):
    applicant: str
    status: Status  # 必须是枚举值之一
    priority: Literal["low", "medium", "high"]  # 必须是字面量之一

generator = outlines.generate.json(model, Application)
app = generator("Generate application")

print(app.status)  # Status.PENDING（或 APPROVED/REJECTED）
```

## 常见模式

### 模式 1：数据提取

```python
from pydantic import BaseModel
import outlines

class CompanyInfo(BaseModel):
    name: str
    founded_year: int
    industry: str
    employees: int

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, CompanyInfo)

text = """
Apple Inc. was founded in 1976 in the technology industry.
The company employs approximately 164,000 people worldwide.
"""

prompt = f"Extract company information:\n{text}\n\nCompany:"
company = generator(prompt)

print(f"Name: {company.name}")
print(f"Founded: {company.founded_year}")
print(f"Industry: {company.industry}")
print(f"Employees: {company.employees}")
```

### 模式 2：分类

```python
from typing import Literal
import outlines

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# 二分类
generator = outlines.generate.choice(model, ["spam", "not_spam"])
result = generator("Email: Buy now! 50% off!")

# 多分类
categories = ["technology", "business", "sports", "entertainment"]
category_gen = outlines.generate.choice(model, categories)
category = category_gen("Article: Apple announces new iPhone...")

# 带置信度
class Classification(BaseModel):
    label: Literal["positive", "negative", "neutral"]
    confidence: float

classifier = outlines.generate.json(model, Classification)
result = classifier("Review: This product is okay, nothing special")
```

### 模式 3：结构化表单

```python
class UserProfile(BaseModel):
    full_name: str
    age: int
    email: str
    phone: str
    country: str
    interests: list[str]

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, UserProfile)

prompt = """
Extract user profile from:
Name: Alice Johnson
Age: 28
Email: alice@example.com
Phone: 555-0123
Country: USA
Interests: hiking, photography, cooking
"""

profile = generator(prompt)
print(profile.full_name)
print(profile.interests)  # ["hiking", "photography", "cooking"]
```

### 模式 4：多实体提取

```python
class Entity(BaseModel):
    name: str
    type: Literal["PERSON", "ORGANIZATION", "LOCATION"]

class DocumentEntities(BaseModel):
    entities: list[Entity]

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, DocumentEntities)

text = "Tim Cook met with Satya Nadella at Microsoft headquarters in Redmond."
prompt = f"Extract entities from: {text}"

result = generator(prompt)
for entity in result.entities:
    print(f"{entity.name} ({entity.type})")
```

### 模式 5：代码生成

```python
class PythonFunction(BaseModel):
    function_name: str
    parameters: list[str]
    docstring: str
    body: str

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, PythonFunction)

prompt = "Generate a Python function to calculate factorial"
func = generator(prompt)

print(f"def {func.function_name}({', '.join(func.parameters)}):")
print(f'    """{func.docstring}"""')
print(f"    {func.body}")
```

### 模式 6：批处理

```python
def batch_extract(texts: list[str], schema: type[BaseModel]):
    """从多个文本提取结构化数据。"""
    model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
    generator = outlines.generate.json(model, schema)

    results = []
    for text in texts:
        result = generator(f"Extract from: {text}")
        results.append(result)

    return results

class Person(BaseModel):
    name: str
    age: int

texts = [
    "John is 30 years old",
    "Alice is 25 years old",
    "Bob is 40 years old"
]

people = batch_extract(texts, Person)
for person in people:
    print(f"{person.name}: {person.age}")
```

## 后端配置

### Transformers

```python
import outlines

# 基本用法
model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# GPU 配置
model = outlines.models.transformers(
    "microsoft/Phi-3-mini-4k-instruct",
    device="cuda",
    model_kwargs={"torch_dtype": "float16"}
)

# 流行模型
model = outlines.models.transformers("meta-llama/Llama-3.1-8B-Instruct")
model = outlines.models.transformers("mistralai/Mistral-7B-Instruct-v0.3")
model = outlines.models.transformers("Qwen/Qwen2.5-7B-Instruct")
```

### llama.cpp

```python
# 加载 GGUF 模型
model = outlines.models.llamacpp(
    "./models/llama-3.1-8b.Q4_K_M.gguf",
    n_ctx=4096,         # 上下文窗口
    n_gpu_layers=35,    # GPU 层
    n_threads=8         # CPU 线程
)

# 完全 GPU 卸载
model = outlines.models.llamacpp(
    "./models/model.gguf",
    n_gpu_layers=-1  # 所有层都在 GPU 上
)
```

### vLLM（生产环境）

```python
# 单 GPU
model = outlines.models.vllm("meta-llama/Llama-3.1-8B-Instruct")

# 多 GPU
model = outlines.models.vllm(
    "meta-llama/Llama-3.1-70B-Instruct",
    tensor_parallel_size=4  # 4 个 GPU
)

# 带量化
model = outlines.models.vllm(
    "meta-llama/Llama-3.1-8B-Instruct",
    quantization="awq"  # 或 "gptq"
)
```

## 最佳实践

### 1. 使用具体类型

```python
# ✅ 好：具体类型
class Product(BaseModel):
    name: str
    price: float  # 不是 str
    quantity: int  # 不是 str
    in_stock: bool  # 不是 str

# ❌ 坏：全部为字符串
class Product(BaseModel):
    name: str
    price: str  # 应为 float
    quantity: str  # 应为 int
```

### 2. 添加约束

```python
from pydantic import Field

# ✅ 好：带约束
class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=120)
    email: str = Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")

# ❌ 坏：无约束
class User(BaseModel):
    name: str
    age: int
    email: str
```

### 3. 类别使用枚举

```python
# ✅ 好：枚举固定集合
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Task(BaseModel):
    title: str
    priority: Priority

# ❌ 坏：自由字符串
class Task(BaseModel):
    title: str
    priority: str  # 可以是任何东西
```

### 4. 在提示词中提供上下文

```python
# ✅ 好：清晰上下文
prompt = """
Extract product information from the following text.
Text: iPhone 15 Pro costs $999 and is currently in stock.
Product:
"""

# ❌ 坏：最小上下文
prompt = "iPhone 15 Pro costs $999 and is currently in stock."
```

### 5. 处理可选字段

```python
from typing import Optional

# ✅ 好：不完整数据的可选字段
class Article(BaseModel):
    title: str  # 必需
    author: Optional[str] = None  # 可选
    date: Optional[str] = None  # 可选
    tags: list[str] = []  # 默认空列表

# 即使缺少 author/date 也能成功
```

## 与替代方案比较

| 功能 | Outlines | Instructor | Guidance | LMQL |
|---------|----------|------------|----------|------|
| Pydantic 支持 | ✅ 原生 | ✅ 原生 | ❌ 否 | ❌ 否 |
| JSON Schema | ✅ 是 | ✅ 是 | ⚠️ 有限 | ✅ 是 |
| 正则约束 | ✅ 是 | ❌ 否 | ✅ 是 | ✅ 是 |
| 本地模型 | ✅ 完整 | ⚠️ 有限 | ✅ 完整 | ✅ 完整 |
| API 模型 | ⚠️ 有限 | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| 零开销 | ✅ 是 | ❌ 否 | ⚠️ 部分 | ✅ 是 |
| 自动重试 | ❌ 否 | ✅ 是 | ❌ 否 | ❌ 否 |
| 学习曲线 | 低 | 低 | 低 | 高 |

**何时选择 Outlines：**
- 使用本地模型（Transformers、llama.cpp、vLLM）
- 需要最大推理速度
- 想要 Pydantic 模型支持
- 需要零开销结构化生成
- 控制 token 采样过程

**何时选择替代方案：**
- Instructor：需要带自动重试的 API 模型
- Guidance：需要 token healing 和复杂工作流
- LMQL：偏好声明式查询语法

## 性能特征

**速度：**
- **零开销**：结构化生成与无约束一样快
- **快进优化**：跳过确定性 token
- **比后生成验证方法快 1.2-2 倍**

**内存：**
- FSM 每个 schema 编译一次（缓存）
- 最小运行时开销
- 与 vLLM 高效配合实现高吞吐

**准确性：**
- **100% 有效输出**（FSM 保证）
- 无需重试循环
- 确定性 token 过滤

## 资源

- **文档**：https://outlines-dev.github.io/outlines
- **GitHub**：https://github.com/outlines-dev/outlines（8k+ stars）
- **Discord**：https://discord.gg/R9DSu34mGd
- **博客**：https://blog.dottxt.co

## 参见

- `references/json_generation.md` — 综合 JSON 和 Pydantic 模式
- `references/backends.md` — 后端特定配置
- `references/examples.md` — 生产就绪示例

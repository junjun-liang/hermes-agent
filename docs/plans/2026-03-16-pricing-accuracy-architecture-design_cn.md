# 定价准确性架构

日期：2026-03-16

## 目标

Hermes 应仅在有官方来源支持用户实际计费路径时才显示美元成本。

本设计替换当前静态的、启发式的定价流程，位于：

- `run_agent.py`
- `agent/usage_pricing.py`
- `agent/insights.py`
- `cli.py`

替换为具备提供商感知的定价系统，能够：

- 正确处理缓存计费
- 区分 `actual`（实际）与 `estimated`（估算）与 `included`（包含）与 `unknown`（未知）
- 当提供商暴露权威性计费数据时进行事后成本对账
- 支持直接提供商、OpenRouter、订阅和企业定价以及自定义端点

## 当前设计中的问题

当前 Hermes 行为存在四个结构性问题：

1. 它仅存储 `prompt_tokens` 和 `completion_tokens`，这对于单独计费缓存读取和缓存写入的提供商来说是不够的。
2. 它使用静态模型价格表和模糊启发式方法，可能与当前官方定价产生偏差。
3. 它假设公共 API 列表价格匹配用户的实际计费路径。
4. 它没有区分实时估算和对账后的实际成本。

## 设计原则

1. 在定价之前先规范化使用量。
2. 永远不要将缓存令牌折叠到普通输入成本中。
3. 显式跟踪确定性。
4. 将计费路径视为模型身份的一部分。
5. 优先使用官方机器可读来源而非抓取的文档。
6. 当可用时使用提供商的事后成本 API。
7. 显示 `n/a` 而非编造精确度。

## 高层架构

新系统有四个层级：

1. `usage_normalization`（使用量规范化）
   将原始提供商使用量转换为规范使用量记录。
2. `pricing_source_resolution`（定价来源解析）
   确定计费路径、真实来源和适用的定价来源。
3. `cost_estimation_and_reconciliation`（成本估算与对账）
   在可能时产生即时估算，然后用实际计费成本替换或注释它。
4. `presentation`（展示）
   `/usage`、`/insights` 和状态栏使用确定性元数据显示成本。

## 规范使用量记录

添加一个规范使用量模型，每个提供商路径在任何定价计算之前都映射到其中。

建议的结构：

```python
@dataclass
class CanonicalUsage:
    provider: str
    billing_provider: str
    model: str
    billing_route: str

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    request_count: int = 1

    raw_usage: dict[str, Any] | None = None
    raw_usage_fields: dict[str, str] | None = None
    computed_fields: set[str] | None = None

    provider_request_id: str | None = None
    provider_generation_id: str | None = None
    provider_response_id: str | None = None
```

规则：

- `input_tokens` 仅表示非缓存输入。
- `cache_read_tokens` 和 `cache_write_tokens` 永远不要合并到 `input_tokens` 中。
- `output_tokens` 排除缓存指标。
- `reasoning_tokens` 是遥测数据，除非提供商正式单独计费。

这与 `opencode` 使用的规范化模式相同，并扩展了出处和对账 ID。

## 提供商规范化规则

### OpenAI 直接

来源使用量字段：

- `prompt_tokens`
- `completion_tokens`
- `prompt_tokens_details.cached_tokens`

规范化：

- `cache_read_tokens = cached_tokens`
- `input_tokens = prompt_tokens - cached_tokens`
- `cache_write_tokens = 0` 除非 OpenAI 在相关路由中暴露它
- `output_tokens = completion_tokens`

### Anthropic 直接

来源使用量字段：

- `input_tokens`
- `output_tokens`
- `cache_read_input_tokens`
- `cache_creation_input_tokens`

规范化：

- `input_tokens = input_tokens`
- `output_tokens = output_tokens`
- `cache_read_tokens = cache_read_input_tokens`
- `cache_write_tokens = cache_creation_input_tokens`

### OpenRouter

估算时使用量规范化应在可能时使用与底层提供商相同的规则响应使用量负载。

对账时记录还应存储：

- OpenRouter generation id
- 原生令牌字段（当可用时）
- `total_cost`
- `cache_discount`
- `upstream_inference_cost`
- `is_byok`

### Gemini / Vertex

在可用时使用官方 Gemini 或 Vertex 使用量字段。

如果暴露缓存内容令牌：

- 将它们映射到 `cache_read_tokens`

如果路由不暴露缓存创建指标：

- 存储 `cache_write_tokens = 0`
- 保留原始使用量负载以供以后扩展

### DeepSeek 及其他直接提供商

仅规范化正式暴露的字段。

如果提供商不暴露缓存桶：

- 不要推断它们，除非提供商正式文档说明如何派生它们

### 订阅/包含成本路由

它们仍然使用规范使用量模型。

令牌正常跟踪。成本取决于计费模式，而不是使用量是否存在。

## 计费路由模型

Hermes 必须停止仅按 `model` 键入定价。

引入计费路由描述符：

```python
@dataclass
class BillingRoute:
    provider: str
    base_url: str | None
    model: str
    billing_mode: str
    organization_hint: str | None = None
```

`billing_mode` 值：

- `official_cost_api`
- `official_generation_api`
- `official_models_api`
- `official_docs_snapshot`
- `subscription_included`
- `user_override`
- `custom_contract`
- `unknown`

示例：

- OpenAI 直接 API 且具有 Costs API 访问权限：`official_cost_api`
- Anthropic 直接 API 且具有 Usage & Cost API 访问权限：`official_cost_api`
- OpenRouter 在对账之前的请求：`official_models_api`
- OpenRouter 在生成查找之后的请求：`official_generation_api`
- GitHub Copilot 风格订阅路由：`subscription_included`
- 本地 OpenAI 兼容服务器：`unknown`
- 具有配置费率的企业合同：`custom_contract`

## 成本状态模型

每个显示的成本应具有：

```python
@dataclass
class CostResult:
    amount_usd: Decimal | None
    status: Literal["actual", "estimated", "included", "unknown"]
    source: Literal[
        "provider_cost_api",
        "provider_generation_api",
        "provider_models_api",
        "official_docs_snapshot",
        "user_override",
        "custom_contract",
        "none",
    ]
    label: str
    fetched_at: datetime | None
    pricing_version: str | None
    notes: list[str]
```

展示规则：

- `actual`：将美元金额显示为最终
- `estimated`：将美元金额带估算标签显示
- `included`：显示 `included` 或 `$0.00 (included)` 取决于 UX 选择
- `unknown`：显示 `n/a`

## 官方来源层级

使用此顺序解析成本：

1. 请求级或账户级官方计费成本
2. 官方机器可读模型定价
3. 官方文档快照
4. 用户覆盖或自定义合同
5. 未知

如果当前计费路径存在更高置信度的来源，系统绝不能跳到更低层级。

## 提供商特定真实规则

### OpenAI 直接

优先真实来源：

1. Costs API 用于对账后的支出
2. 官方定价页面用于实时估算

### Anthropic 直接

优先真实来源：

1. Usage & Cost API 用于对账后的支出
2. 官方定价文档用于实时估算

### OpenRouter

优先真实来源：

1. `GET /api/v1/generation` 用于对账后的 `total_cost`
2. `GET /api/v1/models` 定价用于实时估算

不要使用底层提供商公共定价作为 OpenRouter 计费的真实来源。

### Gemini / Vertex

优先真实来源：

1. 官方计费导出或计费 API 用于对账后的支出（当路由可用时）
2. 官方定价文档用于估算

### DeepSeek

优先真实来源：

1. 官方机器可读成本来源（如果未来可用）
2. 官方定价文档快照今天

### 订阅包含路由

优先真实来源：

1. 明确的路由配置将模型标记为包含在订阅中

这些应显示 `included`，而不是 API 列表价格估算。

### 自定义端点/本地模型

优先真实来源：

1. 用户覆盖
2. 自定义合同配置
3. 未知

这些默认应为 `unknown`。

## 定价目录

用更丰富的定价目录替换当前的 `MODEL_PRICING` 字典。

建议的记录：

```python
@dataclass
class PricingEntry:
    provider: str
    route_pattern: str
    model_pattern: str

    input_cost_per_million: Decimal | None = None
    output_cost_per_million: Decimal | None = None
    cache_read_cost_per_million: Decimal | None = None
    cache_write_cost_per_million: Decimal | None = None
    request_cost: Decimal | None = None
    image_cost: Decimal | None = None

    source: str = "official_docs_snapshot"
    source_url: str | None = None
    fetched_at: datetime | None = None
    pricing_version: str | None = None
```

目录应感知路由：

- `openai:gpt-5`
- `anthropic:claude-opus-4-6`
- `openrouter:anthropic/claude-opus-4.6`
- `copilot:gpt-4o`

这避免将直接提供商计费与聚合器计费混淆。

## 定价同步架构

引入定价同步子系统，而不是手动维护单个硬编码表。

建议的模块：

- `agent/pricing/catalog.py`
- `agent/pricing/sources.py`
- `agent/pricing/sync.py`
- `agent/pricing/reconcile.py`
- `agent/pricing/types.py`

### 同步来源

- OpenRouter 模型 API
- 没有 API 时的官方提供商文档快照
- 来自配置的用户覆盖

### 同步输出

本地缓存定价条目，包含：

- 来源 URL
- 获取时间戳
- 版本/哈希
- 置信度/来源类型

### 同步频率

- 启动时预热缓存
- 后台每 6 到 24 小时刷新一次（取决于来源）
- 手动 `hermes pricing sync`

## 对账架构

实时请求最初可能只产生估算。当提供商暴露实际计费成本时，Hermes 应稍后对账它们。

建议的流程：

1. Agent 调用完成。
2. Hermes 存储规范使用量加上对账 ID。
3. Hermes 在存在定价来源时计算即时估算。
4. 对账工作器在支持时获取实际成本。
5. 会话和消息记录使用 `actual` 成本更新。

这可以运行：

- 对于廉价查找内联运行
- 对于延迟的提供商会计异步运行

## 持久化更改

会话存储应停止仅存储聚合的提示/完成总计。

为使用量和成本确定性添加字段：

- `input_tokens`
- `output_tokens`
- `cache_read_tokens`
- `cache_write_tokens`
- `reasoning_tokens`
- `estimated_cost_usd`
- `actual_cost_usd`
- `cost_status`
- `cost_source`
- `pricing_version`
- `billing_provider`
- `billing_mode`

如果一个 PR 中 schema 扩展太大，添加一个新的定价事件表：

```text
session_cost_events
  id
  session_id
  request_id
  provider
  model
  billing_mode
  input_tokens
  output_tokens
  cache_read_tokens
  cache_write_tokens
  estimated_cost_usd
  actual_cost_usd
  cost_status
  cost_source
  pricing_version
  created_at
  updated_at
```

## Hermes 接触点

### `run_agent.py`

当前职责：

- 解析原始提供商使用量
- 更新会话令牌计数器

新职责：

- 构建 `CanonicalUsage`
- 更新规范计数器
- 存储对账 ID
- 向定价子系统发出使用量事件

### `agent/usage_pricing.py`

当前职责：

- 静态查找表
- 直接成本算术

新职责：

- 移动或替换为定价目录门面
- 无模糊模型家族启发式
- 无脱离计费路由上下文的直接定价

### `cli.py`

当前职责：

- 直接从提示/完成总计计算会话成本

新职责：

- 显示 `CostResult`
- 显示状态徽章：
  - `actual`
  - `estimated`
  - `included`
  - `n/a`

### `agent/insights.py`

当前职责：

- 从静态定价重新计算历史估算

新职责：

- 聚合存储的定价事件
- 优先使用实际成本而非估算
- 仅在对账不可用时显示估算

## UX 规则

### 状态栏

显示以下之一：

- `$1.42`
- `~$1.42`
- `included`
- `cost n/a`

其中：

- `$1.42` 表示 `actual`
- `~$1.42` 表示 `estimated`
- `included` 表示订阅支持或明确零成本路由
- `cost n/a` 表示未知

### `/usage`

显示：

- 令牌桶
- 估算成本
- 实际成本（如果可用）
- 成本状态
- 定价来源

### `/insights`

聚合：

- 实际成本总计
- 仅估算总计
- 未知成本会话计数
- 包含成本会话计数

## 配置和覆盖

在配置中添加用户可配置的定价覆盖：

```yaml
pricing:
  mode: hybrid
  sync_on_startup: true
  sync_interval_hours: 12
  overrides:
    - provider: openrouter
      model: anthropic/claude-opus-4.6
      billing_mode: custom_contract
      input_cost_per_million: 4.25
      output_cost_per_million: 22.0
      cache_read_cost_per_million: 0.5
      cache_write_cost_per_million: 6.0
  included_routes:
    - provider: copilot
      model: "*"
    - provider: codex-subscription
      model: "*"
```

对于匹配的计费路由，覆盖必须胜过目录默认值。

## 发布计划

### 第一阶段

- 添加规范使用量模型
- 在 `run_agent.py` 中拆分缓存令牌桶
- 停止对缓存膨胀的提示总计定价
- 使用改进的后台数学保留当前 UI

### 第二阶段

- 添加路由感知定价目录
- 集成 OpenRouter 模型 API 同步
- 添加 `estimated` 与 `included` 与 `unknown`

### 第三阶段

- 为 OpenRouter 生成成本添加对账
- 添加实际成本持久化
- 更新 `/insights` 以优先使用实际成本

### 第四阶段

- 添加直接 OpenAI 和 Anthropic 对账路径
- 添加用户覆盖和合同定价
- 添加定价同步 CLI 命令

## 测试策略

添加以下测试：

- OpenAI 缓存令牌减法
- Anthropic 缓存读取/写入分离
- OpenRouter 估算与实际对账
- 订阅支持的模型显示 `included`
- 自定义端点显示 `n/a`
- 覆盖优先级
- 陈旧目录回退行为

假设启发式定价的当前测试应替换为路由感知的预期结果。

## 非目标

- 没有官方来源或用户覆盖的精确企业计费重建
- 为缺少缓存桶数据的旧会话完美回填历史成本
- 在请求时抓取任意提供商网页

## 建议

不要扩展现有的 `MODEL_PRICING` 字典。

该路径无法满足产品需求。Hermes 应迁移到：

- 规范使用量规范化
- 路由感知定价来源
- 先估算后对账的成本生命周期
- UI 中的显式确定性状态

这是使"Hermes 定价在可能时由官方来源支持，否则明确标记"这一声明可辩护的最小架构。

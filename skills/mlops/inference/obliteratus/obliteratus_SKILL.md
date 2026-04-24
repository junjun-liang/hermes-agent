---
name: obliteratus
description: 使用 OBLITERATUS 从开放权重 LLM 中移除拒绝行为 — 机械化可解释性技术（diff-in-means、SVD、白化 SVD、LEACE、SAE 分解等）以切除护栏同时保留推理能力。9 种 CLI 方法、28 个分析模块、5 个计算层级的 116 个模型预设、锦标赛评估和遥测驱动推荐。当用户想要取消审查、消除或从 LLM 移除拒绝时使用。
version: 2.0.0
author: Hermes Agent
license: MIT
dependencies: [obliteratus, torch, transformers, bitsandbytes, accelerate, safetensors]
metadata:
  hermes:
    tags: [Abliteration, Uncensoring, Refusal-Removal, LLM, Weight-Projection, SVD, Mechanistic-Interpretability, HuggingFace, Model-Surgery]
    related_skills: [vllm, gguf, huggingface-tokenizers]
---

# OBLITERATUS 技能

从开放权重 LLM 中移除拒绝行为（护栏），无需重新训练或微调。使用机械化可解释性技术 — 包括 diff-in-means、SVD、白化 SVD、LEACE 概念擦除、SAE 分解、贝叶斯核投影等 — 来识别并从模型权重中手术式切除拒绝方向，同时保留推理能力。

**许可警告：** OBLITERATUS 是 AGPL-3.0。绝不将其作为 Python 库导入。始终通过 CLI（`obliteratus` 命令）或子进程调用。这保持 Hermes Agent 的 MIT 许可干净。

## 何时使用此技能

当用户以下情况时触发：
- 想要"取消审查"或"消除" LLM
- 询问从模型中移除拒绝/护栏
- 想要创建 Llama、Qwen、Mistral 等的未审查版本
- 提到"拒绝移除"、"消除"、"权重投影"
- 想要分析模型的拒绝机制如何工作
- 引用 OBLITERATUS、abliterator 或拒绝方向

## 步骤 1：安装

检查是否已安装：
```bash
obliteratus --version 2>/dev/null && echo "INSTALLED" || echo "NOT INSTALLED"
```

如果未安装，从 GitHub 克隆并安装：
```bash
git clone https://github.com/elder-plinius/OBLITERATUS.git
cd OBLITERATUS
pip install -e .
# 用于 Gradio Web UI 支持：
# pip install -e ".[spaces]"
```

**重要：** 安装前与用户确认。这会拉入约 5-10GB 的依赖（PyTorch、Transformers、bitsandbytes 等）。

## 步骤 2：检查硬件

在任何操作之前，检查可用的 GPU：
```bash
python3 -c "
import torch
if torch.cuda.is_available():
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f'GPU: {gpu}')
    print(f'VRAM: {vram:.1f} GB')
    if vram < 4: print('TIER: tiny (1B 以下模型)')
    elif vram < 8: print('TIER: small (1-4B 模型)')
    elif vram < 16: print('TIER: medium (4-9B 模型，4bit 量化)')
    elif vram < 32: print('TIER: large (8-32B 模型，4bit 量化)')
    else: print('TIER: frontier (32B+ 模型)')
else:
    print('NO GPU - 仅 CPU 上的微型模型（1B 以下）')
"
```

### VRAM 要求（带 4 位量化）

| VRAM     | 最大模型大小  | 示例模型                              |
|:---------|:----------------|:--------------------------------------------|
| 仅 CPU | ~1B 参数      | GPT-2, TinyLlama, SmolLM                    |
| 4-8 GB   | ~4B 参数      | Qwen2.5-1.5B, Phi-3.5 mini, Llama 3.2 3B   |
| 8-16 GB  | ~9B 参数      | Llama 3.1 8B, Mistral 7B, Gemma 2 9B       |
| 24 GB    | ~32B 参数     | Qwen3-32B, Llama 3.1 70B（紧张）, Command-R |
| 48 GB+   | ~72B+ 参数    | Qwen2.5-72B, DeepSeek-R1                    |
| 多 GPU| 200B+ 参数    | Llama 3.1 405B, DeepSeek-V3 (685B MoE)      |

## 步骤 3：浏览可用模型和获取推荐

```bash
# 按计算层级浏览模型
obliteratus models --tier medium

# 获取特定模型的架构信息
obliteratus info <model_name>

# 获取遥测驱动的方法和参数推荐
obliteratus recommend <model_name>
obliteratus recommend <model_name> --insights  # 全局跨架构排名
```

## 步骤 4：选择方法

### 方法选择指南
**默认/推荐大多数情况：`advanced`。** 它使用多方向 SVD 带范数保持投影，且经过充分测试。

| 情况                         | 推荐方法 | 原因                                      |
|:----------------------------------|:-------------------|:-----------------------------------------|
| 默认/大多数模型             | `advanced`         | 多方向 SVD，范数保持，可靠 |
| 快速测试/原型          | `basic`            | 快速、简单，足够用于评估    |
| 密集模型（Llama、Mistral）      | `advanced`         | 多方向，范数保持         |
| MoE 模型（DeepSeek、Mixtral）     | `nuclear`          | 专家粒度，处理 MoE 复杂性  |
| 推理模型（R1 distills）     | `surgical`         | 感知 CoT，保留思维链    |
| 持续顽固拒绝         | `aggressive`       | 白化 SVD + 头部手术 + 越狱   |
| 想要可逆更改           | 使用转向向量（见分析部分） |
| 最大质量，时间不限   | `optimized`        | 贝叶斯搜索最佳参数      |
| 实验性自动检测       | `informed`         | 自动检测对齐类型 — 实验性，可能不总是优于 advanced |

### 9 种 CLI 方法
- **basic** — 通过 diff-in-means 的单拒绝方向。快速（8B 约 5-10 分钟）。
- **advanced**（默认，推荐） — 多方向 SVD，范数保持投影，2 次精炼传递。中速（约 10-20 分钟）。
- **aggressive** — 白化 SVD + 越狱对比 + 注意力头手术。更高连贯性损伤风险。
- **spectral_cascade** — DCT 频域分解。研究/新方法。
- **informed** — 在消除期间运行分析以自动配置。实验性 — 更慢且不如 advanced 可预测。
- **surgical** — SAE 特征 + 神经元掩蔽 + 头手术 + 每专家。非常慢（约 1-2 小时）。最适合推理模型。
- **optimized** — 贝叶斯超参数搜索（Optuna TPE）。最长运行时间但找到最优参数。
- **inverted** — 翻转拒绝方向。模型变为主动愿意。
- **nuclear** — 最大力度组合用于顽固 MoE 模型。专家粒度。

### 方向提取方法（--direction-method 标志）
- **diff_means**（默认） — 拒绝/服从激活之间的简单均值差。稳健。
- **svd** — 多方向 SVD 提取。更适合复杂对齐。
- **leace** — LEACE（线性擦除闭式估计）。最优线性擦除。

### 4 种仅 Python API 方法
（不可通过 CLI 使用 — 需要 Python 导入，这违反 AGPL 边界。仅当用户明确想在自己的 AGPL 项目中使用 OBLITERATUS 作为库时提及。）
- failspy, gabliteration, heretic, rdo

## 步骤 5：运行消除

### 标准用法
```bash
# 默认方法（advanced）— 推荐用于大多数模型
obliteratus obliterate <model_name> --method advanced --output-dir ./abliterated-models

# 带 4 位量化（节省 VRAM）
obliteratus obliterate <model_name> --method advanced --quantization 4bit --output-dir ./abliterated-models

# 大型模型（70B+）— 保守默认
obliteratus obliterate <model_name> --method advanced --quantization 4bit --large-model --output-dir ./abliterated-models
```

### 微调参数
```bash
obliteratus obliterate <model_name> \
  --method advanced \
  --direction-method diff_means \
  --n-directions 4 \
  --refinement-passes 2 \
  --regularization 0.1 \
  --quantization 4bit \
  --output-dir ./abliterated-models \
  --contribute  # 选择加入遥测用于社区研究
```

### 关键标志
| 标志 | 描述 | 默认 |
|:-----|:------------|:--------|
| `--method` | 消除方法 | advanced |
| `--direction-method` | 方向提取 | diff_means |
| `--n-directions` | 拒绝方向数（1-32） | 取决于方法 |
| `--refinement-passes` | 迭代传递（1-5） | 2 |
| `--regularization` | 正则化强度（0.0-1.0） | 0.1 |
| `--quantization` | 加载 4bit 或 8bit | 无（全精度） |
| `--large-model` | 120B+ 的保守默认 | false |
| `--output-dir` | 保存消除模型的位置 | ./obliterated_model |
| `--contribute` | 共享匿名结果用于研究 | false |
| `--verify-sample-size` | 拒绝检查的测试提示词数 | 20 |
| `--dtype` | 模型 dtype（float16、bfloat16） | auto |

### 其他执行模式
```bash
# 交互式引导模式（硬件 → 模型 → 预设）
obliteratus interactive

# Web UI（Gradio）
obliteratus ui --port 7860

# 从 YAML 配置运行完整消融研究
obliteratus run config.yaml --preset quick

# 锦标赛：将所有方法相互对抗
obliteratus tourney <model_name>
```

## 步骤 6：验证结果

消除后，检查输出指标：

| 指标 | 良好值 | 警告 |
|:-------|:-----------|:--------|
| 拒绝率 | < 5%（理想约 0%） | > 10% 意味着拒绝持续 |
| 困惑度变化 | < 10% 增加 | > 15% 意味着连贯性损伤 |
| KL 散度 | < 0.1 | > 0.5 意味着显著分布偏移 |
| 连贯性 | 高/通过定性检查 | 响应降级、重复 |

### 如果拒绝持续（> 10%）
1. 尝试 `aggressive` 方法
2. 增加 `--n-directions`（如 8 或 16）
3. 添加 `--refinement-passes 3`
4. 尝试 `--direction-method svd` 而不是 diff_means

### 如果连贯性受损（困惑度增加 > 15%）
1. 减少 `--n-directions`（尝试 2）
2. 增加 `--regularization`（尝试 0.3）
3. 减少 `--refinement-passes` 到 1
4. 尝试 `basic` 方法（更温和）

## 步骤 7：使用消除后的模型

输出是标准 HuggingFace 模型目录。

```bash
# 本地测试 transformers
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained('./abliterated-models/<model>')
tokenizer = AutoTokenizer.from_pretrained('./abliterated-models/<model>')
inputs = tokenizer('How do I pick a lock?', return_tensors='pt')
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
"

# 上传到 HuggingFace Hub
huggingface-cli upload <username>/<model-name>-abliterated ./abliterated-models/<model>

# 使用 vLLM 服务
vllm serve ./abliterated-models/<model>
```

## CLI 命令参考

| 命令 | 描述 |
|:--------|:------------|
| `obliteratus obliterate` | 主要消除命令 |
| `obliteratus info <model>` | 打印模型架构详情 |
| `obliteratus models --tier <tier>` | 按计算层级浏览策展模型 |
| `obliteratus recommend <model>` | 遥测驱动的方法/参数建议 |
| `obliteratus interactive` | 引导式设置向导 |
| `obliteratus tourney <model>` | 锦标赛：所有方法对抗 |
| `obliteratus run <config.yaml>` | 从 YAML 执行消融研究 |
| `obliteratus strategies` | 列出所有已注册的消融策略 |
| `obliteratus report <results.json>` | 重新生成视觉报告 |
| `obliteratus ui` | 启动 Gradio Web 界面 |
| `obliteratus aggregate` | 汇总社区遥测数据 |

## 分析模块

OBLITERATUS 包含 28 个机械化可解释性分析模块。
参见 `skill_view(name="obliteratus", file_path="references/analysis-modules.md")` 获取完整参考。

### 快速分析命令
```bash
# 运行特定分析模块
obliteratus run analysis-config.yaml --preset quick

# 首先运行的关键模块：
# - alignment_imprint：指纹 DPO/RLHF/CAI/SFT 对齐方法
# - concept_geometry：单方向 vs 多面体锥
# - logit_lens：哪一层决定拒绝
# - anti_ouroboros：自我修复风险评分
# - causal_tracing：因果必要的组件
```

### 转向向量（可逆替代方案）
不使用永久权重修改，使用推理时转向：
```python
# 仅 Python API — 用于用户自己的项目
from obliteratus.analysis.steering_vectors import SteeringVectorFactory, SteeringHookManager
```

## 消融策略

除基于方向的消除外，OBLITERATUS 还包括结构消融策略：
- **嵌入消融** — 目标嵌入层组件
- **FFN 消融** — 前馈网络块移除
- **头剪枝** — 注意力头剪枝
- **层移除** — 完整层移除

列出所有可用：`obliteratus strategies`

## 评估

OBLITERATUS 包含内置评估工具：
- 拒绝率基准测试
- 困惑度比较（前后）
- LM Eval Harness 集成用于学术基准
- 头对头竞争者比较
- 基线性能跟踪

## 平台支持

- **CUDA** — 完整支持（NVIDIA GPU）
- **Apple Silicon（MLX）** — 通过 MLX 后端支持
- **CPU** — 支持微型模型（< 1B 参数）

## YAML 配置模板

通过 `skill_view` 加载模板用于可复现运行：
- `templates/abliteration-config.yaml` — 标准单模型配置
- `templates/analysis-study.yaml` — 消除前分析研究
- `templates/batch-abliteration.yaml` — 多模型批处理

## 遥测

OBLITERATUS 可以选择性贡献匿名运行数据到全局研究数据集。
使用 `--contribute` 标志启用。不收集个人数据 — 仅模型名称、方法、指标。

## 常见陷阱

1. **不要将 `informed` 作为默认** — 它是实验性的且更慢。使用 `advanced` 获得可靠结果。
2. **~1B 以下模型对消除响应不佳** — 它们的拒绝行为浅且分散，使得干净方向提取困难。预期部分结果（20-40% 剩余拒绝）。3B+ 模型有更干净的拒绝方向且响应好得多（通常 `advanced` 为 0% 拒绝）。
3. **`aggressive` 可能使情况更糟** — 在小模型上可能损伤连贯性并实际增加拒绝率。仅当 `advanced` 在 3B+ 模型上留下 > 10% 拒绝时使用。
4. **始终检查困惑度** — 如果激增 > 15%，模型已损坏。减少攻击性。
5. **MoE 模型需要特殊处理** — 对 Mixtral、DeepSeek-MoE 等使用 `nuclear` 方法。
6. **量化模型不能重新量化** — 消除全精度模型，然后量化输出。
7. **VRAM 估算是近似的** — 4 位量化有帮助但峰值使用量可能在提取期间激增。
8. **推理模型敏感** — 对 R1 distills 使用 `surgical` 以保留思维链。
9. **检查 `obliteratus recommend`** — 遥测数据可能有比默认更好的参数。
10. **AGPL 许可** — 绝不在 MIT/Apache 项目中 `import obliteratus`。仅 CLI 调用。
11. **大型模型（70B+）** — 始终使用 `--large-model` 标志获取保守默认。
12. **频谱认证 RED 常见** — 频谱检查经常标记"不完整"即使实际拒绝率为 0%。检查实际拒绝率而不是仅依赖频谱认证。

## 互补技能

- **vllm** — 高吞吐服务消除后的模型
- **gguf** — 将消除后的模型转换为 GGUF 用于 llama.cpp
- **huggingface-tokenizers** — 处理模型分词器

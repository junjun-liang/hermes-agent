# Hermes Agent — Skill 系统深度解析

## 一、核心定位

Skill（技能）是 Hermes Agent 的**程序性记忆单元**——本质是一段写给 AI 的 Markdown 指令文件，用来封装特定场景下的行为规范、操作步骤和参考资料，并在恰当时机注入到 Agent 的对话流中。

> 类比：如果 Memory 是 Agent 的"个人笔记"，那么 Skill 就是 Agent 的"工作手册 SOP"。

---

## 二、技能文件格式（SKILL.md）

每个技能本质上是一个带有 YAML Frontmatter 的 Markdown 文件，存储在以技能名命名的目录中：

```
~/.hermes/skills/
└── my-skill/              ← 技能目录（即技能名）
    ├── SKILL.md           ← 核心指令文件（必须）
    ├── references/        ← 参考文档（可选）
    ├── templates/         ← 输出模板（可选）
    ├── scripts/           ← 辅助脚本（可选）
    └── assets/            ← 其他资源（可选）
```

### Frontmatter 字段说明

```yaml
---
name: my-skill                   # 技能唯一名称（必需，最长64字符）
description: 简单描述            # 技能描述（必需，最长1024字符）
version: 1.0.0                   # 版本号（可选）
platforms: [macos, linux]        # 限定操作系统平台（可选，不填则所有平台可用）

# ── 依赖声明 ──
prerequisites:
  env_vars: [API_KEY]            # 需要的环境变量（仅建议，不强制）
  commands: [curl, jq]           # 需要的命令

required_environment_variables:  # 运行前必须存在的环境变量（会主动捕获）
  - name: API_KEY
    prompt: 请输入你的 API Key
    help: https://example.com/api-keys

required_credential_files:       # 必须存在的凭证文件
  - ~/.config/gcloud/application_default_credentials.json

# ── 配置注入（metadata.hermes.config）──
metadata:
  hermes:
    config:
      - key: training.default_epochs   # 对应 config.yaml 中的路径
        type: integer
        default: 3
---

# My Skill 标题

这里是写给 AI 的完整操作指令……
```

---

## 三、系统架构（六层模型）

```
第 1 层（存储层）：SKILL.md 文件 + ~/.hermes/skills/ 目录树
        ↓
第 2 层（发现层）：_find_all_skills() — rglob 扫描 + frontmatter 解析 + 平台/禁用过滤
        ↓
第 3 层（加载层）：skill_view() — 多路径搜索 + 安全检查 + 环境变量捕获
        ↓
第 4 层（注入层）：skill_commands.py — 3 种注入模式（见下节）
        ↓
第 5 层（管理层）：skill_manage() — 增删改查 + 原子写入 + 安全回滚
        ↓
第 6 层（安全层）：skills_guard.py — 50+ 威胁模式扫描 + 信任级别策略
```

---

## 四、技能的三种激活模式

这是 Skill 系统最核心的运行机制。技能内容**永远以 USER 消息注入**（不修改 System Prompt），以保持 Anthropic Prompt Cache 的前缀稳定、不失效。

### 模式 1：斜杠命令激活（最常用）

用户在对话中输入 `/skill-name [指令]`，立即激活对应技能：

```
用户输入：/systematic-debugging 调试这个 Python 内存泄漏
```

**内部流程**：
```
用户输入 /systematic-debugging
    → scan_skill_commands() 查找已注册的 /systematic-debugging
    → build_skill_invocation_message(cmd_key, user_instruction)
        → _load_skill_payload(skill_dir) → skill_view()
        → _build_skill_message() 构建激活消息
    → 以 USER 消息注入对话历史
    → Agent 接收到包含技能指令的对话，按照 SOP 操作
```

构建的消息格式示例：
```
[SYSTEM: The user has invoked the "systematic-debugging" skill, indicating they want you to follow its instructions. The full skill content is loaded below.]

<SKILL.md 完整内容>

[Skill config (from ~/.hermes/config.yaml):
  training.default_epochs = 3
]

[This skill has supporting files you can load with the skill_view tool:]
- references/debug-checklist.md
- templates/bug-report.md

The user has provided the following instruction alongside the skill invocation: 调试这个 Python 内存泄漏
```

### 模式 2：CLI 启动时预加载（会话级）

启动 hermes 时用 `-s` 预加载，技能在整个会话有效：

```bash
hermes -s systematic-debugging,test-driven-development
```

**行为**：加载所有指定技能，在会话首条消息前以 USER 消息注入，并提示 Agent 在本次会话中持续遵循这些技能的指令。

### 模式 3：Agent 工具调用（自主发现）

Agent 通过工具调用自己加载技能，整个流程是 Agent 自主完成的：

```python
# Agent 自主调用（三步递进发现）
skills_categories()          # 浏览有哪些分类（~50 tokens）
skills_list(category="...")  # 查看某分类下的技能（~200 tokens）
skill_view("skill-name")     # 加载完整技能内容（~1000-5000 tokens）
skill_view("skill-name", file_path="references/guide.md")  # 按需加载支持文件
```

这种**三层渐进式披露**设计的目的是最小化 Token 消耗，避免一次性加载所有内容。

---

## 五、技能发现机制

系统在以下目录中递归扫描 `SKILL.md` 文件：
1. `~/.hermes/skills/`（本地，优先级最高）
2. `config.yaml` 中 `skills.external_dirs` 配置的外部目录
3. `~/.hermes/skills/.hub/`（从 Skills Hub 安装的技能，独立隔离区）

过滤规则（按顺序）：
- 跳过 `.git`、`.github`、`.hub` 目录
- 跳过当前操作系统不支持的技能（`platforms` 字段过滤）
- 跳过 `disabled` 配置中禁用的技能
- 去重（`seen_names`，本地技能优先）

技能注册为斜杠命令时，名称规范化为 `kebab-case`（连字符格式），非法字符被移除。

---

## 六、安全机制

### 6.1 威胁扫描（50+ 种模式）

每次**写入**（create/edit/patch）技能时，`skills_guard.py` 会自动扫描，检测六大类威胁：

| 威胁类别 | 典型示例 |
|---------|--------|
| **数据窃取** | curl + 环境变量、访问 ~/.hermes/.env、Markdown 图片外链 |
| **提示注入** | "ignore previous instructions"、"you are now..." |
| **破坏操作** | rm -rf /、mkfs、dd if= |
| **持久化** | 修改 .bashrc、crontab、SSH 密钥 |
| **网络后门** | reverse shell、nc -l、socat |
| **混淆** | base64 decode + eval、hex 编码 |

### 6.2 信任级别策略

安装来源决定扫描结果的处理方式：

| 信任级别 | safe | caution | dangerous | 来源 |
|---------|------|---------|-----------|------|
| `builtin` | ✅ 允许 | ✅ 允许 | ✅ 允许 | 内置技能 |
| `trusted` | ✅ 允许 | ✅ 允许 | ❌ 阻止 | openai/skills 等 |
| `community` | ✅ 允许 | ❌ 阻止 | ❌ 阻止 | 其他 GitHub 仓库 |
| `agent-created` | ✅ 允许 | ✅ 允许 | ⚠️ 询问 | Agent 自主创建 |

### 6.3 写入回滚

所有写入操作均使用**原子写入 + 安全扫描 + 失败回滚**模式：
```
原子写入 SKILL.md
    → 安全扫描
    → 扫描通过：返回成功
    → 扫描阻断：恢复原始内容（或删除新建目录）
```

---

## 七、环境变量自动管理

技能若声明了 `required_environment_variables`，加载时系统会自动检测：

- **CLI 模式**：弹出交互式提示，让用户输入缺失的 API Key，加密保存到 `~/.hermes/.env`
- **Gateway 模式**（Telegram 等）：无法交互，返回配置提示告知用户通过 CLI 提前配置
- 成功捕获的变量会自动注册到 `env_passthrough`，使沙箱执行环境（Docker/Modal）也能访问

---

## 八、技能管理命令速查

### CLI 命令（hermes 子命令）

```bash
hermes skills              # 查看已安装技能
hermes skills search tdd   # 搜索 Hub 上的技能
hermes skills install test-driven-development  # 从 Hub 安装技能
hermes skills inspect tdd  # 查看技能详情
```

### 会话内斜杠命令

```
/skills                    # 浏览可用技能（Agent 工具调用）
/skills search <关键词>    # 搜索技能
/skills install <名称>     # 安装技能
/<skill-name>              # 直接激活某技能
```

### 创建自定义技能（让 Agent 创建）

```
"帮我创建一个用于代码审查的技能，内容是..."
```

Agent 会调用 `skill_manage(action="create", ...)` 自动创建并安全扫描。

---

## 九、技能文件目录（内置示例）

项目 `skills/` 目录下包含 26 个分类的内置技能：

```
skills/
├── software-development/    # TDD、代码审查、调试等开发技能
├── data-science/            # 数据分析相关
├── devops/                  # 运维和部署
├── research/                # 研究和信息收集
├── creative/                # 创意写作
├── github/                  # GitHub 操作
├── mcp/                     # MCP 集成
└── ...（共 26 个分类）
```

---

## 十、关键源码文件索引

| 功能 | 文件 |
|-----|------|
| 技能发现与加载工具 | `tools/skills_tool.py` |
| 技能注入消息构建 | `agent/skill_commands.py` |
| 技能工具函数（frontmatter/平台检测） | `agent/skill_utils.py` |
| 技能安全扫描 | `tools/skills_guard.py` |
| 技能管理工具（增删改） | `tools/skill_manager_tool.py` |
| 技能 Hub（安装/搜索） | `hermes_cli/skills_hub.py` |
| 按平台启用/禁用技能 | `hermes_cli/skills_config.py` |

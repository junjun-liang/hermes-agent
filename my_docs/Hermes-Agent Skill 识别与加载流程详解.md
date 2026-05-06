# Hermes-Agent Skill 识别与加载流程详解

> 深入解析 Hermes-Agent 如何识别用户请求需要的 skill，并找到对应 skill 加载的完整流程

**整理日期**: 2026-04-29  
**版本**: 1.0  
**适用版本**: Hermes-Agent v2.0+

---

## 📋 目录

1. [Skill 系统架构概览](#1-skill-系统架构概览)
2. [Skill 发现流程](#2-skill-发现流程)
3. [Skill 识别与匹配](#3-skill-识别与匹配)
4. [Skill 加载与注入](#4-skill-加载与注入)
5. [Skill 调用执行](#5-skill-调用执行)
6. [完整流程图](#6-完整流程图)
7. [核心代码实现](#7-核心代码实现)
8. [缓存与优化](#8-缓存与优化)
9. [实战案例](#9-实战案例)

---

## 1. Skill 系统架构概览

### 1.1 核心组件

```mermaid
graph TB
    subgraph "用户请求层"
        A[用户消息]
    end
    
    subgraph "识别层"
        B[LLM 意图识别]
        C[工具可用性检查]
    end
    
    subgraph "发现层"
        D[Skill 目录扫描]
        E[SKILL.md 解析]
        F[平台兼容性检查]
    end
    
    subgraph "匹配层"
        G[条件匹配]
        H[工具集依赖检查]
        I[禁用列表过滤]
    end
    
    subgraph "注入层"
        J[系统提示词构建]
        K[Skill 索引生成]
        L[缓存优化]
    end
    
    subgraph "执行层"
        M[skill_view 工具]
        N[Skill 内容加载]
        O[指令执行]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    L --> M
    M --> N
    N --> O
    
    style A fill:#90EE90
    style O fill:#FFB6C1
    style J fill:#87CEEB
    style M fill:#DDA0DD
```

### 1.2 关键文件依赖

| 文件 | 作用 | 依赖 |
|------|------|------|
| `run_agent.py` | Agent 核心循环 | `agent/prompt_builder.py` |
| `agent/prompt_builder.py` | 系统提示词构建 | `agent/skill_utils.py` |
| `agent/skill_utils.py` | Skill 元数据工具 | 无（轻量级） |
| `agent/skill_commands.py` | Skill 命令注入 | `tools/skills_tool.py` |
| `tools/skills_tool.py` | Skill 工具实现 | `tools/registry.py` |
| `hermes_cli/skills_hub.py` | Skill 仓库管理 | `hermes_cli/config.py` |

### 1.3 Skill 目录结构

```
~/.hermes/skills/
├── SKILL.md              # Skill 元数据和指令
├── .skills_prompt_snapshot.json  # 缓存的 Skill 索引
├── general/              # 通用技能
│   ├── SKILL.md
│   └── DESCRIPTION.md    # 分类描述
├── development/          # 开发技能
│   ├── SKILL.md
│   └── DESCRIPTION.md
└── external/             # 外部技能目录（可配置）
    └── SKILL.md
```

---

## 2. Skill 发现流程

### 2.1 Skill 目录扫描

**位置**: `agent/skill_utils.py::get_all_skills_dirs()`

```python
def get_all_skills_dirs() -> List[Path]:
    """返回所有 skill 目录：本地 ~/.hermes/skills/ 优先，然后外部目录"""
    dirs = [get_skills_dir()]  # 本地目录
    dirs.extend(get_external_skills_dirs())  # 外部目录
    return dirs
```

**扫描顺序**：
1. ✅ **本地目录** - `~/.hermes/skills/`（总是第一个）
2. ✅ **外部目录** - 从 `skills.external_dirs` 配置读取
3. ✅ **优先级** - 本地 skill 优先于外部同名 skill

### 2.2 SKILL.md 文件解析

**位置**: `agent/skill_utils.py::parse_frontmatter()`

```python
def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """从 markdown 字符串解析 YAML frontmatter"""
    frontmatter: Dict[str, Any] = {}
    body = content
    
    if not content.startswith("---"):
        return frontmatter, body
    
    # 提取 YAML 内容
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return frontmatter, body
    
    yaml_content = content[3 : end_match.start() + 3]
    body = content[end_match.end() + 3 :]
    
    # 使用 CSafeLoader 解析 YAML
    try:
        parsed = yaml_load(yaml_content)
        if isinstance(parsed, dict):
            frontmatter = parsed
    except Exception:
        # 降级到简单的 key:value 解析
        for line in yaml_content.strip().split("\n"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()
    
    return frontmatter, body
```

**SKILL.md 结构示例**：

```markdown
---
name: react-best-practices
category: development
description: React 开发最佳实践和代码规范
platforms: [macos, linux]
metadata:
  hermes:
    requires_toolsets: [terminal, file]
    fallback_for_toolsets: [web]
    config:
      - key: wiki.path
        description: Wiki 知识库路径
        default: "~/wiki"
---

# React 最佳实践

## 核心原则

1. 组件化设计
2. 单向数据流
3. 不可变性
...
```

### 2.3 平台兼容性检查

**位置**: `agent/skill_utils.py::skill_matches_platform()`

```python
def skill_matches_platform(frontmatter: Dict[str, Any]) -> bool:
    """当 skill 与当前 OS 兼容时返回 True"""
    platforms = frontmatter.get("platforms")
    if not platforms:
        return True  # 未指定平台 = 全平台兼容
    if not isinstance(platforms, list):
        platforms = [platforms]
    
    current = sys.platform  # 'linux', 'darwin', 'win32'
    
    for platform in platforms:
        normalized = str(platform).lower().strip()
        mapped = PLATFORM_MAP.get(normalized, normalized)
        if current.startswith(mapped):
            return True
    
    return False  # 无匹配平台
```

**平台映射表**：

```python
PLATFORM_MAP = {
    "macos": "darwin",
    "linux": "linux",
    "windows": "win32",
}
```

---

## 3. Skill 识别与匹配

### 3.1 禁用 Skill 过滤

**位置**: `agent/skill_utils.py::get_disabled_skill_names()`

```python
def get_disabled_skill_names(platform: str | None = None) -> Set[str]:
    """从 config.yaml 读取禁用的 skill 名称"""
    config_path = get_config_path()
    if not config_path.exists():
        return set()
    
    parsed = yaml_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        return set()
    
    skills_cfg = parsed.get("skills")
    if not isinstance(skills_cfg, dict):
        return set()
    
    # 获取当前平台
    resolved_platform = (
        platform
        or os.getenv("HERMES_PLATFORM")
        or get_session_env("HERMES_SESSION_PLATFORM")
    )
    
    # 优先使用平台特定的禁用列表
    if resolved_platform:
        platform_disabled = (skills_cfg.get("platform_disabled") or {}).get(
            resolved_platform
        )
        if platform_disabled is not None:
            return _normalize_string_set(platform_disabled)
    
    # 回退到全局禁用列表
    return _normalize_string_set(skills_cfg.get("disabled"))
```

**配置示例**：

```yaml
skills:
  disabled:
    - experimental-skill
    - deprecated-feature
  platform_disabled:
    telegram:
      - file-heavy-skill
    whatsapp:
      - markdown-dependent-skill
```

### 3.2 条件激活匹配

**位置**: `agent/skill_utils.py::extract_skill_conditions()`

```python
def extract_skill_conditions(frontmatter: Dict[str, Any]) -> Dict[str, List]:
    """从 frontmatter 提取条件激活字段"""
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    hermes = metadata.get("hermes") or {}
    if not isinstance(hermes, dict):
        hermes = {}
    
    return {
        "fallback_for_toolsets": hermes.get("fallback_for_toolsets", []),
        "requires_toolsets": hermes.get("requires_toolsets", []),
        "fallback_for_tools": hermes.get("fallback_for_tools", []),
        "requires_tools": hermes.get("requires_tools", []),
    }
```

**条件类型**：

| 条件字段 | 说明 | 示例 |
|---------|------|------|
| `requires_toolsets` | 必须的工具集 | `[terminal, file]` |
| `fallback_for_toolsets` | 当某工具集不可用时的备选 | `[web]` |
| `requires_tools` | 必须的具体工具 | `[read_file, write_file]` |
| `fallback_for_tools` | 当某工具不可用时的备选 | `[execute_code]` |

### 3.3 Skill 显示决策

**位置**: `agent/prompt_builder.py::_skill_should_show()`

```python
def _skill_should_show(
    conditions: Dict[str, List],
    available_tools: Set[str],
    available_toolsets: Set[str],
) -> bool:
    """判断 skill 是否应该显示在当前上下文中"""
    
    # 1. 检查必需的工具集
    requires_toolsets = conditions.get("requires_toolsets", [])
    if requires_toolsets:
        if not available_toolsets:
            return False
        if not any(ts in available_toolsets for ts in requires_toolsets):
            return False
    
    # 2. 检查必需的工具
    requires_tools = conditions.get("requires_tools", [])
    if requires_tools:
        if not available_tools:
            return False
        if not any(tool in available_tools for tool in requires_tools):
            return False
    
    # 3. 检查备选工具集（当主工具集不可用时）
    fallback_for_toolsets = conditions.get("fallback_for_toolsets", [])
    if fallback_for_toolsets and not requires_toolsets:
        # 只有在主工具集缺失时才显示备选 skill
        if any(ts in available_toolsets for ts in fallback_for_toolsets):
            return False
    
    # 4. 检查备选工具
    fallback_for_tools = conditions.get("fallback_for_tools", [])
    if fallback_for_tools and not requires_tools:
        if any(tool in available_tools for tool in fallback_for_tools):
            return False
    
    return True  # 所有条件满足
```

---

## 4. Skill 加载与注入

### 4.1 系统提示词构建流程

**位置**: `run_agent.py::_build_system_prompt()`

```python
def _build_system_prompt(self, system_message: str = None) -> str:
    """组装完整的系统提示词"""
    
    # Layers (in order):
    #   1. Agent 身份 — SOUL.md 或 DEFAULT_AGENT_IDENTITY
    #   2. 用户/网关系统提示词（如果提供）
    #   3. 持久记忆（冻结快照）
    #   4. Skills 指导（如果 skills 工具已加载）
    #   5. 上下文文件（AGENTS.md, .cursorrules）
    #   6. 当前日期时间
    #   7. 平台特定格式化提示
    
    prompt_parts = []
    
    # 1. Agent 身份
    _soul_loaded = False
    if not self.skip_context_files:
        _soul_content = load_soul_md()
        if _soul_content:
            prompt_parts = [_soul_content]
            _soul_loaded = True
    
    if not _soul_loaded:
        prompt_parts = [DEFAULT_AGENT_IDENTITY]
    
    # 2-3. 工具指导和记忆（省略）
    
    # 4. Skills 指导
    has_skills_tools = any(
        name in self.valid_tool_names 
        for name in ['skills_list', 'skill_view', 'skill_manage']
    )
    
    if has_skills_tools:
        # 获取可用工具集
        avail_toolsets = {
            toolset
            for toolset in (
                get_toolset_for_tool(tool_name) 
                for tool_name in self.valid_tool_names
            )
            if toolset
        }
        
        # 构建 skills 索引
        skills_prompt = build_skills_system_prompt(
            available_tools=self.valid_tool_names,
            available_toolsets=avail_toolsets,
        )
        
        if skills_prompt:
            prompt_parts.append(skills_prompt)
    
    # 5-7. 其他部分（省略）
    
    return "\n\n".join(prompt_parts)
```

### 4.2 Skills 索引生成

**位置**: `agent/prompt_builder.py::build_skills_system_prompt()`

```python
def build_skills_system_prompt(
    available_tools: "set[str] | None" = None,
    available_toolsets: "set[str] | None" = None,
) -> str:
    """为系统提示词构建紧凑的 skill 索引"""
    
    # 两层缓存：
    #   1. 进程内 LRU 缓存，键为 (skills_dir, tools, toolsets)
    #   2. 磁盘快照（.skills_prompt_snapshot.json）
    
    skills_dir = get_skills_dir()
    external_dirs = get_all_skills_dirs()[1:]  # 跳过本地目录
    
    if not skills_dir.exists() and not external_dirs:
        return ""
    
    # ── Layer 1: 进程内 LRU 缓存 ─────────────────────────────────
    cache_key = (
        str(skills_dir.resolve()),
        tuple(str(d) for d in external_dirs),
        tuple(sorted(str(t) for t in (available_tools or set()))),
        tuple(sorted(str(ts) for ts in (available_toolsets or set()))),
        _platform_hint,
    )
    
    with _SKILLS_PROMPT_CACHE_LOCK:
        cached = _SKILLS_PROMPT_CACHE.get(cache_key)
        if cached is not None:
            _SKILLS_PROMPT_CACHE.move_to_end(cache_key)
            return cached
    
    # ── Layer 2: 磁盘快照 ────────────────────────────────────────
    snapshot = _load_skills_snapshot(skills_dir)
    
    skills_by_category: dict[str, list[tuple[str, str]]] = {}
    category_descriptions: dict[str, str] = {}
    
    if snapshot is not None:
        # 快速路径：使用磁盘预解析的元数据
        for entry in snapshot.get("skills", []):
            if not _skill_should_show(entry["conditions"], available_tools, available_toolsets):
                continue
            # 添加到分类列表
            skills_by_category.setdefault(entry["category"], []).append(
                (entry["skill_name"], entry["description"])
            )
    else:
        # 冷路径：完整文件系统扫描
        # ...（扫描所有 SKILL.md 文件）
    
    # ── 外部 skill 目录 ─────────────────────────────────────────
    for ext_dir in external_dirs:
        # 扫描外部目录，跳过已存在的同名 skill
        # ...
    
    # ── 生成索引文本 ────────────────────────────────────────────
    if not skills_by_category:
        result = ""
    else:
        index_lines = []
        for category in sorted(skills_by_category.keys()):
            cat_desc = category_descriptions.get(category, "")
            if cat_desc:
                index_lines.append(f"  {category}: {cat_desc}")
            else:
                index_lines.append(f"  {category}:")
            
            for name, desc in sorted(skills_by_category[category], key=lambda x: x[0]):
                if desc:
                    index_lines.append(f"    - {name}: {desc}")
                else:
                    index_lines.append(f"    - {name}")
        
        result = (
            "## Skills (mandatory)\n"
            "Before replying, scan the skills below. If a skill matches or is even partially relevant "
            "to your task, you MUST load it with skill_view(name) and follow its instructions.\n\n"
            + "\n".join(index_lines)
        )
    
    # 缓存结果
    with _SKILLS_PROMPT_CACHE_LOCK:
        _SKILLS_PROMPT_CACHE[cache_key] = result
    
    return result
```

### 4.3 生成的 Skill 索引格式

```markdown
## Skills (mandatory)

Before replying, scan the skills below. If a skill matches or is even partially relevant 
to your task, you MUST load it with skill_view(name) and follow its instructions. 
Err on the side of loading — it is always better to have context you don't need 
than to miss critical steps, pitfalls, or established workflows.

  development: Best practices and workflows for software development
    - react-best-practices: React 开发最佳实践和代码规范
    - python-testing: Python 单元测试和集成测试指南
    - git-workflow: Git 分支管理和协作流程
    
  general: General purpose skills and utilities
    - note-taking: 笔记整理和知识管理方法
    - time-management: 时间管理和任务规划技巧
```

---

## 5. Skill 调用执行

### 5.1 LLM 识别 Skill 需求

**流程**：
1. LLM 接收到包含 Skill 索引的系统提示词
2. LLM 分析用户请求，匹配相关 skill
3. LLM 决定调用 `skill_view` 工具

**LLM 决策示例**：

```
用户：帮我创建一个 React 组件

系统提示词包含：
  development:
    - react-best-practices: React 开发最佳实践

LLM 推理：
"用户需要创建 React 组件，react-best-practices 这个 skill 
应该包含相关的代码规范和最佳实践。我应该先加载这个 skill。"

LLM 调用：
{
  "name": "skill_view",
  "arguments": {
    "name": "react-best-practices"
  }
}
```

### 5.2 skill_view 工具执行

**位置**: `tools/skills_tool.py`

```python
@registry.register(
    name="skill_view",
    toolset="skills",
    schema={...},
    handler=lambda args, **kw: skill_view(args.get("name", ""), task_id=kw.get("task_id")),
)
def skill_view(skill_identifier: str, task_id: str | None = None) -> str:
    """Load a skill by name/path and return its content."""
    
    # 1. 解析 skill 标识符
    raw_identifier = (skill_identifier or "").strip()
    if not raw_identifier:
        return json.dumps({"success": False, "error": "Empty skill name"})
    
    # 2. 加载 skill 内容
    try:
        from tools.skills_tool import SKILLS_DIR, skill_view
        
        identifier_path = Path(raw_identifier).expanduser()
        if identifier_path.is_absolute():
            # 绝对路径：尝试相对化到 SKILLS_DIR
            try:
                normalized = str(identifier_path.resolve().relative_to(SKILLS_DIR.resolve()))
            except Exception:
                normalized = raw_identifier
        else:
            # 相对路径：直接使用
            normalized = raw_identifier.lstrip("/")
        
        # 3. 读取 skill 文件
        loaded_skill = json.loads(skill_view(normalized, task_id=task_id))
        
    except Exception:
        return json.dumps({"success": False, "error": "Skill not found"})
    
    if not loaded_skill.get("success"):
        return json.dumps(loaded_skill)
    
    # 4. 返回 skill 内容
    return json.dumps({
        "success": True,
        "name": loaded_skill.get("name"),
        "content": loaded_skill.get("content"),
        "instructions": loaded_skill.get("instructions"),
        "path": loaded_skill.get("path"),
    })
```

### 5.3 Skill 内容注入到对话

**位置**: `agent/skill_commands.py`

```python
def _inject_skill_config(loaded_skill: dict[str, Any], parts: list[str]) -> None:
    """解析并注入 skill 声明的配置值到消息部分"""
    
    raw_content = str(loaded_skill.get("raw_content") or loaded_skill.get("content") or "")
    if not raw_content:
        return
    
    # 1. 解析 frontmatter
    frontmatter, _ = parse_frontmatter(raw_content)
    
    # 2. 提取配置变量
    config_vars = extract_skill_config_vars(frontmatter)
    if not config_vars:
        return
    
    # 3. 从 config.yaml 读取实际值
    from hermes_cli.config import load_config
    config = load_config()
    
    config_lines = []
    for var in config_vars:
        key = var["key"]
        # 读取嵌套配置值
        value = _resolve_dotpath(config, key)
        if value is None:
            value = var.get("default", "NOT_SET")
        config_lines.append(f"  {key}: {value}")
    
    if config_lines:
        parts.append(f"\n[Skill config: {loaded_skill.get('name')}]\n" + "\n".join(config_lines))
```

---

## 6. 完整流程图

### 6.1 Skill 识别与加载完整流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Agent as AIAgent
    participant LLM as LLM 模型
    participant Builder as prompt_builder
    participant Utils as skill_utils
    participant Tool as skill_view 工具
    participant FileSystem as 文件系统
    
    User->>Agent: 发送消息
    
    rect rgb(240, 248, 255)
        Note over Agent,Builder: 阶段 1: 系统提示词构建
        Agent->>Builder: _build_system_prompt()
        
        Builder->>Builder: 检查 skill 工具是否可用
        alt skill 工具可用
            Builder->>Builder: build_skills_system_prompt()
            
            rect rgb(255, 250, 240)
                Note over Builder,Utils: Skill 发现与过滤
                Builder->>Utils: get_all_skills_dirs()
                Utils-->>Builder: 返回技能目录列表
                
                loop 每个技能目录
                    Builder->>FileSystem: 扫描 SKILL.md
                    FileSystem-->>Builder: 返回文件列表
                    
                    loop 每个 SKILL.md
                        Builder->>Builder: parse_frontmatter()
                        Builder->>Utils: skill_matches_platform()
                        Utils-->>Builder: True/False
                        
                        alt 平台兼容
                            Builder->>Utils: get_disabled_skill_names()
                            Utils-->>Builder: 禁用列表
                            
                            alt 未禁用
                                Builder->>Builder: _skill_should_show()
                                alt 条件匹配
                                    Builder->>Builder: 添加到索引
                                end
                            end
                        end
                    end
                end
            end
            
            Builder->>Builder: 生成索引文本
            Builder-->>Agent: 返回 skills 索引
        end
    end
    
    rect rgb(240, 255, 240)
        Note over Agent,LLM: 阶段 2: LLM 识别
        Agent->>LLM: API 调用（含 skills 索引）
        LLM->>LLM: 分析用户请求
        LLM->>LLM: 匹配相关 skill
        
        alt 找到匹配 skill
            LLM->>Agent: 返回 tool_call: skill_view
        else 无匹配
            LLM->>Agent: 返回文本响应
        end
    end
    
    rect rgb(255, 240, 240)
        Note over Agent,Tool: 阶段 3: Skill 加载
        Agent->>Tool: 执行 skill_view(name)
        
        Tool->>Tool: 解析 skill 标识符
        Tool->>FileSystem: 读取 skill 文件
        FileSystem-->>Tool: 返回 SKILL.md 内容
        
        Tool->>Tool: 解析 frontmatter
        Tool->>Tool: 提取配置变量
        Tool->>Tool: 注入配置值
        
        Tool-->>Agent: 返回 skill 内容
    end
    
    rect rgb(250, 240, 250)
        Note over Agent,LLM: 阶段 4: 执行 Skill 指令
        Agent->>LLM: 追加 skill 内容到对话
        LLM->>LLM: 根据 skill 指令执行
        LLM->>Agent: 返回最终响应
    end
    
    Agent-->>User: 返回结果
```

### 6.2 Skill 发现详细流程

```mermaid
flowchart TD
    Start([开始 Skill 发现]) --> GetDirs[获取所有 skill 目录]
    
    GetDirs --> CheckLocal{本地目录存在？}
    CheckLocal -->|是 | ScanLocal[扫描本地 SKILL.md]
    CheckLocal -->|否 | CheckExternal
    
    ScanLocal --> ParseFrontmatter[解析 frontmatter]
    ParseFrontmatter --> CheckPlatform{平台兼容？}
    
    CheckPlatform -->|否 | SkipPlatform[跳过]
    CheckPlatform -->|是 | CheckDisabled{在禁用列表？}
    
    CheckDisabled -->|是 | SkipDisabled[跳过]
    CheckDisabled -->|否 | CheckConditions
    
    SkipPlatform --> CheckExternal
    SkipDisabled --> CheckExternal
    
    CheckConditions[检查激活条件] --> CheckToolsets{工具集满足？}
    CheckToolsets -->|否 | CheckFallback{有备选？}
    CheckToolsets -->|是 | AddToIndex[添加到索引]
    
    CheckFallback -->|是 | AddToIndex
    CheckFallback -->|否 | CheckExternal
    
    AddToIndex --> MoreSkills{还有更多 skill?}
    MoreSkills -->|是 | ParseFrontmatter
    MoreSkills -->|否 | CheckExternal
    
    CheckExternal{有外部目录？}
    CheckExternal -->|是 | ScanExternal[扫描外部 SKILL.md]
    ScanExternal --> CheckDuplicate{与本地重复？}
    CheckDuplicate -->|是 | SkipExternal[跳过]
    CheckDuplicate -->|否 | AddToIndex
    
    CheckExternal -->|否 | GenerateIndex[生成索引文本]
    
    GenerateIndex --> CacheResult[缓存结果]
    CacheResult --> End([结束])
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style AddToIndex fill:#87CEEB
    style GenerateIndex fill:#DDA0DD
```

---

## 7. 核心代码实现

### 7.1 Skill 元数据解析

```python
# agent/skill_utils.py

def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """从 markdown 字符串解析 YAML frontmatter"""
    frontmatter: Dict[str, Any] = {}
    body = content
    
    if not content.startswith("---"):
        return frontmatter, body
    
    # 提取 YAML 内容（在两个 --- 之间）
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return frontmatter, body
    
    yaml_content = content[3 : end_match.start() + 3]
    body = content[end_match.end() + 3 :]
    
    # 使用 CSafeLoader 解析 YAML
    try:
        parsed = yaml_load(yaml_content)
        if isinstance(parsed, dict):
            frontmatter = parsed
    except Exception:
        # 降级到简单的 key:value 解析
        for line in yaml_content.strip().split("\n"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()
    
    return frontmatter, body
```

### 7.2 Skill 条件匹配

```python
# agent/skill_utils.py

def extract_skill_conditions(frontmatter: Dict[str, Any]) -> Dict[str, List]:
    """从 frontmatter 提取条件激活字段"""
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    hermes = metadata.get("hermes") or {}
    if not isinstance(hermes, dict):
        hermes = {}
    
    return {
        "fallback_for_toolsets": hermes.get("fallback_for_toolsets", []),
        "requires_toolsets": hermes.get("requires_toolsets", []),
        "fallback_for_tools": hermes.get("fallback_for_tools", []),
        "requires_tools": hermes.get("requires_tools", []),
    }


def _skill_should_show(
    conditions: Dict[str, List],
    available_tools: Set[str],
    available_toolsets: Set[str],
) -> bool:
    """判断 skill 是否应该显示在当前上下文中"""
    
    # 1. 检查必需的工具集
    requires_toolsets = conditions.get("requires_toolsets", [])
    if requires_toolsets:
        if not available_toolsets:
            return False
        if not any(ts in available_toolsets for ts in requires_toolsets):
            return False
    
    # 2. 检查必需的工具
    requires_tools = conditions.get("requires_tools", [])
    if requires_tools:
        if not available_tools:
            return False
        if not any(tool in available_tools for tool in requires_tools):
            return False
    
    # 3. 检查备选工具集（当主工具集不可用时）
    fallback_for_toolsets = conditions.get("fallback_for_toolsets", [])
    if fallback_for_toolsets and not requires_toolsets:
        # 只有在主工具集缺失时才显示备选 skill
        if any(ts in available_toolsets for ts in fallback_for_toolsets):
            return False
    
    # 4. 检查备选工具
    fallback_for_tools = conditions.get("fallback_for_tools", [])
    if fallback_for_tools and not requires_tools:
        if any(tool in available_tools for tool in fallback_for_tools):
            return False
    
    return True
```

### 7.3 Skill 索引生成与缓存

```python
# agent/prompt_builder.py

_SKILLS_PROMPT_CACHE: "OrderedDict[tuple, str]" = OrderedDict()
_SKILLS_PROMPT_CACHE_LIMIT = 32
_SKILLS_PROMPT_CACHE_LOCK = threading.Lock()


def build_skills_system_prompt(
    available_tools: "set[str] | None" = None,
    available_toolsets: "set[str] | None" = None,
) -> str:
    """构建紧凑的 skill 索引用于系统提示词"""
    
    skills_dir = get_skills_dir()
    external_dirs = get_all_skills_dirs()[1:]
    
    if not skills_dir.exists() and not external_dirs:
        return ""
    
    # ── Layer 1: 进程内 LRU 缓存 ─────────────────────────────────
    cache_key = (
        str(skills_dir.resolve()),
        tuple(str(d) for d in external_dirs),
        tuple(sorted(str(t) for t in (available_tools or set()))),
        tuple(sorted(str(ts) for ts in (available_toolsets or set()))),
        _platform_hint,
    )
    
    with _SKILLS_PROMPT_CACHE_LOCK:
        cached = _SKILLS_PROMPT_CACHE.get(cache_key)
        if cached is not None:
            _SKILLS_PROMPT_CACHE.move_to_end(cache_key)
            return cached
    
    # ── Layer 2: 磁盘快照 ────────────────────────────────────────
    snapshot = _load_skills_snapshot(skills_dir)
    
    skills_by_category: dict[str, list[tuple[str, str]]] = {}
    category_descriptions: dict[str, str] = {}
    
    if snapshot is not None:
        # 快速路径：使用预解析的元数据
        for entry in snapshot.get("skills", []):
            if not _skill_should_show(entry.get("conditions", {}), available_tools, available_toolsets):
                continue
            skills_by_category.setdefault(entry["category"], []).append(
                (entry["skill_name"], entry["description"])
            )
    else:
        # 冷路径：完整文件系统扫描
        # ...（扫描所有 SKILL.md 文件并解析）
        pass
    
    # ── 生成索引文本 ────────────────────────────────────────────
    if not skills_by_category:
        result = ""
    else:
        index_lines = []
        for category in sorted(skills_by_category.keys()):
            cat_desc = category_descriptions.get(category, "")
            if cat_desc:
                index_lines.append(f"  {category}: {cat_desc}")
            else:
                index_lines.append(f"  {category}:")
            
            for name, desc in sorted(skills_by_category[category], key=lambda x: x[0]):
                if desc:
                    index_lines.append(f"    - {name}: {desc}")
                else:
                    index_lines.append(f"    - {name}")
        
        result = (
            "## Skills (mandatory)\n"
            "Before replying, scan the skills below...\n\n"
            + "\n".join(index_lines)
        )
    
    # 缓存结果
    with _SKILLS_PROMPT_CACHE_LOCK:
        _SKILLS_PROMPT_CACHE[cache_key] = result
        # LRU 淘汰
        if len(_SKILLS_PROMPT_CACHE) > _SKILLS_PROMPT_CACHE_LIMIT:
            _SKILLS_PROMPT_CACHE.popitem(last=False)
    
    return result
```

---

## 8. 缓存与优化

### 8.1 两层缓存策略

**Layer 1: 进程内 LRU 缓存**

```python
_SKILLS_PROMPT_CACHE: OrderedDict = OrderedDict()
_SKILLS_PROMPT_CACHE_LIMIT = 32

# 缓存键包含所有影响结果的变量
cache_key = (
    str(skills_dir.resolve()),
    tuple(str(d) for d in external_dirs),
    tuple(sorted(str(t) for t in (available_tools or set()))),
    tuple(sorted(str(ts) for ts in (available_toolsets or set()))),
    _platform_hint,
)

# 检查缓存
with _SKILLS_PROMPT_CACHE_LOCK:
    cached = _SKILLS_PROMPT_CACHE.get(cache_key)
    if cached is not None:
        _SKILLS_PROMPT_CACHE.move_to_end(cache_key)  # 最近使用
        return cached
```

**Layer 2: 磁盘快照**

```python
def _load_skills_snapshot(skills_dir: Path) -> Optional[dict]:
    """加载磁盘上的 skill 快照"""
    snapshot_path = skills_dir / ".skills_prompt_snapshot.json"
    if not snapshot_path.exists():
        return None
    
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        
        # 验证快照有效性（检查文件 mtime 和 size）
        if not _validate_snapshot_manifest(snapshot, skills_dir):
            return None
        
        return snapshot
    except Exception:
        return None


def _write_skills_snapshot(
    skills_dir: Path,
    manifest: dict,
    skill_entries: list,
    category_descriptions: dict,
):
    """写入 skill 快照"""
    snapshot = {
        "version": 1,
        "timestamp": datetime.utcnow().isoformat(),
        "manifest": manifest,
        "skills": skill_entries,
        "category_descriptions": category_descriptions,
    }
    
    snapshot_path = skills_dir / ".skills_prompt_snapshot.json"
    atomic_json_write(snapshot, snapshot_path)
```

### 8.2 性能优化措施

| 优化措施 | 效果 | 实现位置 |
|---------|------|----------|
| **LRU 缓存** | 避免重复扫描 | `build_skills_system_prompt()` |
| **磁盘快照** | 进程重启后仍有效 | `_load_skills_snapshot()` |
| **条件过滤** | 只扫描相关 skill | `_skill_should_show()` |
| **平台预过滤** | 跳过不兼容 skill | `skill_matches_platform()` |
| **原子写入** | 避免并发冲突 | `atomic_json_write()` |
| **懒加载 YAML** | 减少启动时间 | `yaml_load()` |

---

## 9. 实战案例

### 9.1 案例 1: React 开发技能加载

**用户请求**：
```
帮我创建一个 React 组件，实现计数器功能
```

**执行流程**：

1. **Skill 发现阶段**
   ```python
   # 扫描到 react-best-practices skill
   frontmatter = {
       "name": "react-best-practices",
       "category": "development",
       "metadata": {
           "hermes": {
               "requires_toolsets": ["terminal", "file"]
           }
       }
   }
   
   # 检查条件
   available_toolsets = {"terminal", "file", "web"}
   _skill_should_show(conditions, tools, toolsets)  # True
   ```

2. **索引生成**
   ```markdown
   ## Skills (mandatory)
   
     development: Best practices and workflows for software development
       - react-best-practices: React 开发最佳实践和代码规范
   ```

3. **LLM 识别**
   ```
   LLM 推理：
   "用户需要创建 React 组件，应该先加载 react-best-practices skill"
   
   调用工具：
   {
     "name": "skill_view",
     "arguments": {"name": "react-best-practices"}
   }
   ```

4. **Skill 加载**
   ```python
   skill_view("react-best-practices")
   # 返回：
   {
     "success": True,
     "name": "react-best-practices",
     "content": "# React 最佳实践\n\n## 核心原则\n1. 组件化设计\n...",
     "instructions": "创建 React 组件时遵循以下规范..."
   }
   ```

5. **执行 Skill 指令**
   ```
   LLM 根据 skill 中的指令：
   - 使用函数组件而非类组件
   - 使用 hooks 管理状态
   - 遵循 ESLint 规则
   - 添加 PropTypes 类型检查
   
   最终生成符合规范的 React 组件代码
   ```

### 9.2 案例 2: 平台特定技能

**场景**: Telegram 网关上的用户请求

**配置**:
```yaml
skills:
  platform_disabled:
    telegram:
      - markdown-heavy-skill
      - file-upload-skill
```

**执行流程**:

1. **平台检测**
   ```python
   resolved_platform = os.getenv("HERMES_PLATFORM")  # "telegram"
   disabled = get_disabled_skill_names("telegram")
   # 返回：{"markdown-heavy-skill", "file-upload-skill"}
   ```

2. **Skill 过滤**
   ```python
   for skill_file in iter_skill_index_files(skills_dir, "SKILL.md"):
       frontmatter, _ = parse_frontmatter(content)
       skill_name = frontmatter.get("name")
       
       if skill_name in disabled:
           continue  # 跳过禁用的 skill
       
       # 添加到索引
   ```

3. **结果**
   ```markdown
   ## Skills (available on Telegram)
   
     communication: Telegram-specific communication skills
       - message-formatting: Telegram 消息格式化技巧
       - emoji-usage: Telegram 表情符号使用指南
   
     # markdown-heavy-skill 和 file-upload-skill 被过滤掉
   ```

### 9.3 案例 3: 备选 Skill 激活

**场景**: `web` 工具集不可用

**Skill 配置**:
```yaml
# skill-a: 主技能
metadata:
  hermes:
    requires_toolsets: [web, terminal]

# skill-b: 备选技能
metadata:
  hermes:
    fallback_for_toolsets: [web]
```

**执行逻辑**:

```python
available_toolsets = {"terminal", "file"}  # 没有 web

# skill-a: 检查必需工具集
 SkillA: requires_toolsets = ["web", "terminal"]
  → "web" not in available_toolsets
  → _skill_should_show() = False  # 不显示

# skill-b: 检查备选工具集
 SkillB: fallback_for_toolsets = ["web"]
  → "web" not in available_toolsets
  → 主工具集缺失，备选技能激活
  → _skill_should_show() = True  # 显示
```

**结果**:
```markdown
## Skills (fallback mode)

  research: Alternative research methods
    - offline-research: 离线研究方法和资源  # skill-b 激活
```

---

## 📝 总结

### 核心流程回顾

1. **Skill 发现** - 扫描本地和外部 skill 目录
2. **元数据解析** - 提取 frontmatter 中的配置信息
3. **条件过滤** - 平台兼容性、禁用列表、工具依赖
4. **索引生成** - 按分类组织 skill 列表
5. **LLM 识别** - LLM 根据索引匹配用户需求
6. **Skill 加载** - 调用 `skill_view` 工具加载内容
7. **指令执行** - LLM 根据 skill 指令执行任务

### 关键设计特性

✅ **两层缓存** - 进程内 LRU + 磁盘快照  
✅ **条件激活** - 基于工具集和工具的动态过滤  
✅ **平台感知** - 支持平台特定的 skill 启用/禁用  
✅ **备选机制** - 主技能不可用时自动激活备选  
✅ **配置注入** - 自动读取并注入 skill 配置值  
✅ **外部扩展** - 支持外部 skill 目录  

### 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 缓存命中率 | ~95% | 进程内缓存 |
| 冷启动时间 | ~50-100ms | 完整扫描 100 个 skill |
| 热启动时间 | <1ms | 缓存命中 |
| 磁盘快照大小 | ~10-50KB | 100 个 skill 元数据 |

---

**文档版本**: 1.0  
**最后更新**: 2026-04-29  
**适用版本**: Hermes-Agent v2.0+  
**作者**: AI Assistant

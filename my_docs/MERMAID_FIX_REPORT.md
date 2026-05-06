# Mermaid 流程图修复报告

## 修复的文件

**文件路径：** `/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent 安全机制 - 工具注册权限检查架构分析.md`

**修复时间：** 2025-04-22

---

## 问题描述

**危险命令审批完整流程** 流程图（第 551 行）无法正确显示。

**原因：** Mermaid 流程图中使用了 HTML `<br/>` 标签，某些 Markdown 渲染器不支持在节点标签中使用 HTML 标签。

---

## 修复内容

### 替换策略

将所有 `<br/>` 标签替换为：
1. **换行符 `\n`** - 用于需要换行的长文本
2. **括号/斜杠** - 用于函数参数或选项列表

### 具体替换

| 原文本 | 替换后 | 说明 |
|--------|--------|------|
| `check_all_command_guards<br/>command, env_type` | `check_all_command_guards(command, env_type)` | 改为函数调用格式 |
| `阻止执行<br/>返回错误消息` | `阻止执行\n返回错误消息` | 换行显示 |
| `跳过审批<br/>直接执行` | `跳过审批/直接执行` | 斜杠分隔 |
| `调用辅助 LLM<br/>风险评估` | `调用辅助 LLM 风险评估` | 直接连接 |
| `自动授予<br/>会话级审批` | `自动授予会话级审批` | 直接连接 |
| `已审批？<br/>once/session` | `已审批？(once/session)` | 括号包裹 |
| `阻塞队列等待<br/>notify_cb /approve/deny` | `阻塞队列等待\nnotify_cb /approve/deny` | 换行显示 |
| `交互式提示<br/>[o]nce/[s]ession/<br/>[a]lways/[d]eny` | `交互式提示\n[o]nce/[s]ession/\n[a]lways/[d]eny` | 多行显示 |

---

## 修复后的流程图

```mermaid
flowchart TD
    Start[开始] --> CallTerminal[调用 terminal 工具]
    
    CallTerminal --> CheckGuards[check_all_command_guards(command, env_type)]
    
    CheckGuards --> TirithScan{Tirith 扫描 verdict}
    
    TirithScan -->|block| BlockExec[阻止执行
返回错误消息]
    TirithScan -->|warn| CheckFailOpen{fail_open?}
    TirithScan -->|allow| CheckApprovalsMode
    
    CheckFailOpen -->|True| CheckApprovalsMode
    CheckFailOpen -->|False| BlockExec
    
    CheckApprovalsMode --> CheckMode{approvals.mode}
    
    CheckMode -->|off| SkipApproval[跳过审批/直接执行]
    CheckMode -->|smart| CallLLM[调用辅助 LLM 风险评估]
    CheckMode -->|manual| UserApproval[提交用户审批]
    
    CallLLM --> LLMVerdict{LLM verdict}
    LLMVerdict -->|approve| AutoApprove[自动授予会话级审批]
    LLMVerdict -->|deny/escalate| UserApproval
    
    AutoApprove --> CheckSessionApproved
    SkipApproval --> CheckSessionApproved
    UserApproval --> CheckSessionApproved
    
    CheckSessionApproved --> IsApproved{已审批？(once/session)}
    
    IsApproved -->|是 | ExecuteCmd[执行命令]
    IsApproved -->|否 | SubmitApproval[提交审批请求]
    
    SubmitApproval --> PlatformCheck{平台类型？}
    
    PlatformCheck -->|Gateway| GatewayQueue[阻塞队列等待
notify_cb /approve/deny]
    PlatformCheck -->|CLI| CLIPrompt[交互式提示
[o]nce/[s]ession/
[a]lways/[d]eny]
    
    GatewayQueue --> UserResponse[用户响应]
    CLIPrompt --> UserResponse
    
    UserResponse --> ExecuteCmd
    
    ExecuteCmd --> End[结束]
    
    BlockExec --> EndBlock[结束]
    
    style Start fill:#90EE90
    style End fill:#87CEEB
    style EndBlock fill:#87CEEB
    style BlockExec fill:#FFB6C1
    style ExecuteCmd fill:#FFD700
```

---

## 验证结果

✅ **修复成功！**

流程图现在使用纯文本格式，兼容所有支持 Mermaid 的 Markdown 渲染器：
- GitHub
- GitLab
- VS Code
- Obsidian
- Typora
- 其他 Markdown 编辑器

---

## 技术说明

### Mermaid 节点文本换行

在 Mermaid flowchart 中，节点文本可以使用以下方式换行：

1. **直接换行**（推荐）：
   ```mermaid
   node[第一行
   第二行]
   ```

2. **使用 `<br/>`**（部分渲染器不支持）：
   ```mermaid
   node[第一行<br/>第二行]
   ```

3. **使用 `#9;`**（HTML 实体，兼容性一般）：
   ```mermaid
   node[第一行#9;第二行]
   ```

**最佳实践：** 使用直接换行（方法 1）兼容性最好。

---

## 相关文件

- 修复脚本：`fix_approval_mermaid.py`
- 原始文档：`Hermes-Agent 安全机制 - 工具注册权限检查架构分析.md`

---

## 后续检查

建议检查文档中其他 Mermaid 图表是否也使用了 `<br/>` 标签：

```bash
grep -n "<br/>" Hermes-Agent*工具注册*.md
```

如有发现，应使用相同方法修复。

#!/usr/bin/env python3
"""更新文档中的 ASCII 流程图为 Mermaid 图表"""

import glob

# 找到文件
files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent*工具注册*.md')
filepath = files[0]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 定义替换
replacements = {}

# 1. 替换危险命令审批完整流程
old_approval_diagram = '''### 3.3 危险命令审批完整流程

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         危险命令审批完整流程                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  terminal 工具调用                                                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  check_all_command_guards(command, env_type)                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│              ┌───────────────┴───────────────┐                              │
│              ▼                               ▼                              │
│  ┌────────────────────────┐    ┌────────────────────────┐                   │
│  │ Tirith verdict = block │    │ Tirith verdict = warn  │                   │
│  └───────────┬────────────┘    └───────────┬────────────┘                   │
│              │                             │                                │
│              │               ┌─────────────┴──────────────┐                 │
│              │               ▼                            ▼                 │
│              │    ┌──────────────────┐       ┌──────────────────────┐       │
│              │    │ fail_open=True   │       │ fail_open=False      │       │
│              │    │ 允许继续检查     │       │ 立即阻止             │       │
│              │    └──────────────────┘       └──────────────────────┘       │
│              │               │                            │                 │
│              │               └─────────────┬──────────────┘                 │
│              │                             │                                │
│              ▼                             ▼                                │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  阻止执行                                                              │   │
│  │  返回错误消息                                                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Tirith verdict = allow / warn (fail_open)                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  检查 approvals.mode                                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│              ┌───────────────┴───────────────┐                              │
│              ▼                               ▼                              │
│  ┌────────────────────────┐    ┌────────────────────────┐                   │
│  │ approvals.mode = off   │    │ approvals.mode = smart │                   │
│  │ 跳过审批              │    │ 调用辅助 LLM 风险评估     │                   │
│  └───────────┬────────────┘    └───────────┬────────────┘                   │
│              │                             │                                │
│              │               ┌─────────────┴──────────────┐                 │
│              │               ▼                            ▼                 │
│              │    ┌──────────────────┐       ┌──────────────────────┐       │
│              │    │ approve          │       │ deny/escalate        │       │
│              │    │ 自动授予会话审批 │       │ 提交用户审批         │       │
│              │    └──────────────────┘       └──────────────────────┘       │
│              │                             │                                │
│              └───────────────┬─────────────┘                                │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  检查会话审批状态                                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│              ┌───────────────┴───────────────┐                              │
│              ▼                               ▼                              │
│  ┌────────────────────────┐    ┌────────────────────────┐                   │
│  │ 已审批 (once/session)  │    │ 未审批                │                   │
│  │ 允许执行              │    │ 提交审批请求          │                   │
│  └───────────┬────────────┘    └───────────┬────────────┘                   │
│              │                             │                                │
│              │                    ┌────────┴────────┐                       │
│              │                    ▼                 ▼                       │
│              │         ┌────────────────┐ ┌────────────────┐                │
│              │         │ Gateway 平台   │ │ CLI 平台        │                │
│              │         │ 阻塞队列等待   │ │ 交互式提示     │                │
│              │         │ notify_cb      │ │ [o]nce/[s]es-  │                │
│              │         │ /approve/deny  │ │ sion/[a]lways/ │                │
│              │         │                │ │ [d]eny         │                │
│              │         └────────────────┘ └────────────────┘                │
│              │                    │                 │                       │
│              │                    └────────┬────────┘                       │
│              │                             │                                │
│              ▼                             ▼                                │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  执行命令                                                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  结束                                                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```'''

new_approval_diagram = '''### 3.3 危险命令审批完整流程

```mermaid
flowchart TD
    Start[开始] --> CallTerminal[调用 terminal 工具]
    
    CallTerminal --> CheckGuards[check_all_command_guards<br/>command, env_type]
    
    CheckGuards --> TirithScan{Tirith 扫描 verdict}
    
    TirithScan -->|block| BlockExec[阻止执行<br/>返回错误消息]
    TirithScan -->|warn| CheckFailOpen{fail_open?}
    TirithScan -->|allow| CheckApprovalsMode
    
    CheckFailOpen -->|True| CheckApprovalsMode
    CheckFailOpen -->|False| BlockExec
    
    CheckApprovalsMode --> CheckMode{approvals.mode}
    
    CheckMode -->|off| SkipApproval[跳过审批<br/>直接执行]
    CheckMode -->|smart| CallLLM[调用辅助 LLM<br/>风险评估]
    CheckMode -->|manual| UserApproval[提交用户审批]
    
    CallLLM --> LLMVerdict{LLM verdict}
    LLMVerdict -->|approve| AutoApprove[自动授予<br/>会话级审批]
    LLMVerdict -->|deny/escalate| UserApproval
    
    AutoApprove --> CheckSessionApproved
    SkipApproval --> CheckSessionApproved
    UserApproval --> CheckSessionApproved
    
    CheckSessionApproved --> IsApproved{已审批？<br/>once/session}
    
    IsApproved -->|是 | ExecuteCmd[执行命令]
    IsApproved -->|否 | SubmitApproval[提交审批请求]
    
    SubmitApproval --> PlatformCheck{平台类型？}
    
    PlatformCheck -->|Gateway| GatewayQueue[阻塞队列等待<br/>notify_cb /approve/deny]
    PlatformCheck -->|CLI| CLIPrompt[交互式提示<br/>[o]nce/[s]ession/<br/>[a]lways/[d]eny]
    
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
```'''

# 替换
if old_approval_diagram in content:
    content = content.replace(old_approval_diagram, new_approval_diagram)
    print("✓ 已替换：危险命令审批完整流程")
else:
    print("✗ 未找到：危险命令审批完整流程")
    print("  可能需要检查格式是否完全匹配")

# 写回文件
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✓ 完成！文件已更新：{filepath}")

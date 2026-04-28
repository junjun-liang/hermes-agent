#!/usr/bin/env python3
"""修复危险命令审批流程图"""

import glob
import re

# 找到文件
files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent*工具注册*.md')
filepath = files[0]

print(f"处理文件：{filepath}")

# 读取文件
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 使用正则表达式匹配并替换
# 匹配从 ### 3.3 到 ### 3.4 之间的所有内容（包括代码块）
old_pattern = r'### 3\.3 危险命令审批完整流程\n\n```[\s\S]*?```\n\n### 3\.4 环境变量隔离流程'

new_content = '''### 3.3 危险命令审批完整流程

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
```

### 3.4 环境变量隔离流程'''

# 执行替换
new_content_full = re.sub(old_pattern, new_content, content)

if new_content_full != content:
    print("✓ 成功替换")
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content_full)
    print(f"✓ 文件已更新：{filepath}")
else:
    print("✗ 替换失败，模式未匹配")
    # 调试：显示找到的内容
    match = re.search(r'### 3\.3 危险命令审批完整流程.*?### 3\.4', content, re.DOTALL)
    if match:
        print(f"找到匹配:\n{match.group()[:200]}...")
    else:
        print("未找到匹配的模式")

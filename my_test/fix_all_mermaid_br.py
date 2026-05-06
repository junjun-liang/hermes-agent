#!/usr/bin/env python3
"""修复文档中所有 Mermaid 流程图的 <br/> 标签"""

import glob

# 找到文件
files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent*工具注册*.md')
filepath = files[0]

print(f"处理文件：{filepath}")

# 读取文件
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 定义所有需要替换的规则
replacements = [
    # 工具注册权限检查流程图 (行 175)
    ('导入工具模块<br/>_discover_tools', '导入工具模块\n_discover_tools'),
    ('触发 registry.register<br/>每个工具文件', '触发 registry.register\n每个工具文件'),
    ('解析工具集<br/>enabled/disabled_toolsets', '解析工具集\nenabled/disabled_toolsets'),
    ('registry.get_definitions<br/>tool_names', 'registry.get_definitions\ntool_names'),
    ('遍历每个工具<br/>检查可用性', '遍历每个工具\n检查可用性'),
    ('check_fn<br/>返回 True?', 'check_fn\n返回 True?'),
    ('返回 schema 列表<br/>给 LLM', '返回 schema 列表\n给 LLM'),
    
    # 工具调用权限验证流程 (行 208)
    ('综合检查<br/>(Tirith + 危险模式)', '综合检查\n(Tirith + 危险模式)'),
    ('{"approved": False,<br/>status: "approval_required"}', '{"approved": False,\nstatus: "approval_required"}'),
    ('用户审批:<br/>once/session/always/deny', '用户审批:\nonce/session/always/deny'),
    
    # 工具注册与发现流程 (行 431)
    ('注册 check_fn 到<br/>_toolset_checks', '注册 check_fn 到\n_toolset_checks'),
]

new_content = content
for old, new in replacements:
    new_content = new_content.replace(old, new)

if new_content != content:
    print("✓ 成功替换所有 <br/> 标签")
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✓ 文件已更新：{filepath}")
    
    # 统计替换数量
    count = len(replacements)
    print(f"✓ 共替换 {count} 处 <br/> 标签")
else:
    print("✗ 未找到需要替换的内容")

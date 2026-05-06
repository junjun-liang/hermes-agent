#!/usr/bin/env python3
"""使用正则表达式替换执行环境文档中的 ASCII 流程图为 Mermaid"""

import glob
import re

files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/*执行环境*.md')
filepath = files[0]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 执行环境初始化流程
pattern1 = r'### 3\.1 执行环境初始化流程\n\n```\n┌─.*?┘\n```'
replacement1 = '''### 3.1 执行环境初始化流程

```mermaid
flowchart TD
    A[选择 env_type\nlocal/docker/ssh/modal/daytona/singularity] --> B[get_or_create_env]
    B --> C{环境缓存？}
    
    C -->|已有缓存 | D[使用缓存环境]
    C -->|无缓存 | E[创建新环境]
    
    E --> F{env_type 类型}
    F -->|local| G1[LocalEnv]
    F -->|docker| G2[DockerEnv]
    F -->|ssh| G3[SSHEnv]
    F -->|modal| G4[ModalEnv]
    F -->|daytona| G5[DaytonaEnv]
    F -->|singularity| G6[SingularityEnv]
    
    G1 --> H[init_session]
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H
    G6 --> H
    
    H --> I["1. bash -l -c 'export -p'\n2. 解析 export VAR=value\n3. 保存到 snapshot.json"]
    
    I --> J[FileSyncManager.sync]
    
    J --> K["1. 扫描本地文件\n   ~/.hermes/skills/\n   ~/.hermes/credentials/\n2. 对比远程文件列表\n3. 批量上传新文件\n4. 批量删除远程文件\n5. 更新远程文件缓存"]
    
    D --> L[环境就绪]
    K --> L
```'''

content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)

# 2. 命令执行流程
pattern2 = r'### 3\.2 命令执行流程\n\n```\n┌─.*?┘\n```'
replacement2 = '''### 3.2 命令执行流程

```mermaid
flowchart TD
    A[execute_command\ncommand, cwd, env, timeout] --> B[get_or_create_env]
    B --> C[source_session_snapshot\n加载 snapshot.json]
    C --> D[应用 cwd 和 env 覆盖]
    D --> E[执行命令 spawn-per-call]
    
    E --> F{env_type 类型}
    F -->|local| G1[subprocess.Popen]
    F -->|docker| G2[docker exec/attach]
    F -->|ssh| G3[exec_command]
    F -->|modal| G4[container.run]
    F -->|daytona| G5[SDK.execute]
    F -->|singularity| G6[singularity exec]
    
    G1 --> H[等待完成 + 收集输出]
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H
    G6 --> H
    
    H --> I["stdout/stderr\nreturncode\ntimeout"]
    I --> J[更新会话快照\nbash -l -c 'export -p']
    J --> K[返回结果]
```'''

content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)

# 3. 环境变量隔离流程
pattern3 = r'### 3\.3 环境变量隔离流程\n\n```\n┌─.*?┘\n```'
replacement3 = '''### 3.3 环境变量隔离流程

```mermaid
flowchart TD
    A[进程启动] --> B["1. 继承最小系统环境变量\nPATH, HOME, LANG\nHERMES_HOME"]
    B --> C["2. source 会话快照\nsnapshot.json"]
    C --> D["3. 应用命令特定的 env 覆盖\nos.environ.update"]
    D --> E["4. 执行命令\nsubprocess.Popen\nenv=final_env"]
    E --> F["5. 命令完成，进程结束\n环境变量随进程销毁\n不污染父进程"]
    F --> G["6. 更新会话快照\nbash -l -c 'export -p'\n更新 snapshot.json"]
```'''

content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 使用正则表达式成功替换 3 个 ASCII 流程图为 Mermaid")
print(f"📄 文件：{filepath}")

# 验证
mermaid_count = content.count('```mermaid')
ascii_count = content.count('┌────')

print(f"\n验证结果:")
print(f"  Mermaid 代码块：{mermaid_count} 个")
print(f"  ASCII 图框线：{ascii_count} 处")

if mermaid_count >= 4 and ascii_count < 10:
    print("\n✅ 替换成功！")
else:
    print("\n⚠️  可能需要进一步检查")

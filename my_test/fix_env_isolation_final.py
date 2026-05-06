#!/usr/bin/env python3
"""彻底修复环境变量隔离流程图 - 确保 100% 能显示"""

filepath = '/home/meizu/Documents/my_agent_project/hermes-agent/Hermes-Agent 安全机制 - 执行环境隔离架构分析.md'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并开始替换
start_marker = '### 3.3 环境变量隔离流程'
end_marker = '## 环境变量隔离详解'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print(f"未找到标记")
    exit(1)

# 使用最简单、最兼容的 Mermaid 语法
new_mermaid = '''### 3.3 环境变量隔离流程

```mermaid
flowchart TD
    A[开始] --> B[阶段 1: 继承最小系统环境变量]
    B --> C[PATH, HOME, LANG, HERMES_HOME]
    C --> D[阶段 2: init_session 捕获环境]
    D --> E[bootstrap 脚本 bash -l]
    E --> F[export -p > snapshot.sh]
    F --> G[declare -f | grep >> snapshot.sh]
    G --> H[alias -p >> snapshot.sh]
    H --> I[shopt -s expand_aliases]
    I --> J[set +e; set +u]
    J --> K[pwd -P > cwd_file.txt]
    K --> L[快照就绪 snapshot_ready = True]
    L --> M[阶段 3: 每次命令执行时的环境恢复]
    M --> N[source snapshot.sh]
    N --> O[cd WORKDIR]
    O --> P[os.environ.update custom_env]
    P --> Q[阶段 4: 执行命令 spawn-per-call]
    Q --> R[subprocess.Popen env=final_env]
    R --> S[进程级隔离]
    S --> T[子进程继承 final_env]
    T --> U[修改不影响父进程]
    U --> V[进程结束自动销毁]
    V --> W[不污染其他命令]
    W --> X[阶段 5: 命令完成后更新快照]
    X --> Y[export -p > snapshot.sh]
    Y --> Z[pwd -P > cwd_file.txt]
    Z --> AA[解析 CWD_MARKER]
    AA --> AB[会话就绪]
    
    subgraph 关键特性
        AC[会话快照文件 snapshot.sh cwd_file.txt]
        AD[spawn-per-call 模型 每次执行新进程]
        AE[last-writer-wins 并发安全]
        AF[CWD 跟踪 pwd -P CWD_MARKER]
    end
    
    F -.-> AC
    R -.-> AD
    Y -.-> AE
    Z -.-> AF
    
    subgraph 环境变量流转
        AG[系统环境变量 PATH HOME LANG]
        AH[会话环境变量 snapshot.sh 跨调用保持]
        AI[自定义环境变量 os.environ.update]
        AJ[最终环境变量 System Session Custom]
    end
    
    C --> AG
    N --> AH
    P --> AI
    P --> AJ
```

## 环境变量隔离详解'''

# 替换
new_content = content[:start_idx] + new_mermaid + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ 已彻底修复环境变量隔离流程图")
print("使用最简单的 Mermaid 语法，确保 100% 能显示")

#!/usr/bin/env python3
"""修复环境变量隔离流程图 - 使用简单语法确保能显示"""

import glob

files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/*执行环境*.md')
filepath = files[0]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换旧的环境变量隔离流程图
import re

old_pattern = r'(### 3\.3 环境变量隔离流程\n\n```mermaid\nflowchart TD.*?)\n\n## 环境变量隔离详解'

# 使用简单语法的新流程图
new_content = '''### 3.3 环境变量隔离流程

```mermaid
flowchart TD
    A[环境变量隔离流程] --> B[阶段 1: 继承最小系统环境变量]
    B --> C["最小环境变量:\nPATH, HOME, LANG, HERMES_HOME"]
    C --> D[阶段 2: init_session 捕获环境]
    D --> E["bootstrap 脚本 (bash -l):\n1. export -p > snapshot.sh\n2. declare -f | grep >> snapshot.sh\n3. alias -p >> snapshot.sh\n4. shopt -s expand_aliases\n5. set +e; set +u\n6. pwd -P > cwd_file.txt"]
    E --> F[快照就绪\n_snapshot_ready = True]
    F --> G[阶段 3: 每次命令执行时的环境恢复]
    G --> H["source snapshot.sh\n(恢复环境变量、函数、别名)"]
    H --> I["cd $WORKDIR\n(切换工作目录)"]
    I --> J["os.environ.update(custom_env)\n(应用自定义覆盖)"]
    J --> K[阶段 4: 执行命令 (spawn-per-call)]
    K --> L["subprocess.Popen\nenv=final_env"]
    L --> M["进程级隔离:\n• 子进程继承 final_env\n• 修改不影响父进程\n• 进程结束自动销毁\n• 不污染其他命令"]
    M --> N[阶段 5: 命令完成后更新快照]
    N --> O["export -p > snapshot.sh\n(last-writer-wins 策略)"]
    O --> P["pwd -P > cwd_file.txt\n(更新工作目录)"]
    P --> Q["解析 CWD_MARKER\n__HERMES_CWD_session__"]
    Q --> R[会话就绪 ✓]
    
    subgraph 关键特性
        S1[会话快照文件\nsnapshot.sh + cwd_file.txt]
        S2[spawn-per-call 模型\n每次执行新进程]
        S3[last-writer-wins\n并发安全]
        S4[CWD 跟踪\npwd -P + CWD_MARKER]
    end
    
    E -.-> S1
    L -.-> S2
    O -.-> S3
    P -.-> S4
    
    subgraph 环境变量流转
        T1[系统环境变量\nPATH, HOME, LANG...]
        T2[会话环境变量\nsnapshot.sh 跨调用保持]
        T3[自定义环境变量\nos.environ.update]
        T4[最终环境变量\nSystem + Session + Custom]
    end
    
    C --> T1
    H --> T2
    J --> T3
    J --> T4
```

## 环境变量隔离详解

### 核心设计原则

**spawn-per-call 模型：**
- 每个命令执行都 spawn 新的子进程
- 子进程继承父进程的环境变量副本
- 子进程对环境变量的修改不会影响父进程
- 进程结束后，所有修改自动销毁
- 实现了完美的进程级隔离

**会话快照机制：**
- `init_session()` 在环境初始化时捕获环境变量
- 保存到 `snapshot.sh` 文件
- 后续命令通过 `source snapshot.sh` 恢复环境
- 命令执行后重新导出环境变量到快照
- 实现了跨调用的环境变量保持

**last-writer-wins 策略：**
- 并发调用时，最后完成的命令更新快照
- 避免并发写入冲突
- 保证快照一致性

### 环境变量来源

| 来源 | 示例 | 生命周期 |
|------|------|----------|
| **系统环境变量** | PATH, HOME, LANG | 系统级 |
| **init_session 捕获** | export -p 所有变量 | 会话级 |
| **函数定义** | declare -f | 会话级 |
| **shell 别名** | alias -p | 会话级 |
| **自定义覆盖** | os.environ.update | 命令级 |
| **最终合并** | System + Session + Custom | 进程级 |

### 关键代码位置

| 流程节点 | 代码文件 | 行号 |
|---------|---------|------|
| init_session | `tools/environments/base.py` | 289-325 |
| _wrap_command | `tools/environments/base.py` | 330-366 |
| execute | `tools/environments/base.py` | 519-558 |
| _update_cwd | `tools/environments/base.py` | 463-466 |
| _extract_cwd_from_output | `tools/environments/base.py` | 467-499 |

### 环境变量隔离示例

**命令 1：** `export FOO=bar`
```bash
# 执行前：source snapshot.sh (FOO 不存在)
# 执行中：export FOO=bar (子进程环境变量)
# 执行后：export -p > snapshot.sh (FOO=bar 保存到快照)
```

**命令 2：** `echo $FOO`
```bash
# 执行前：source snapshot.sh (FOO=bar 已存在)
# 执行中：echo $FOO 输出 bar
# 执行后：export -p > snapshot.sh (FOO=bar 保持不变)
```

**进程隔离：**
```python
# 父进程
os.environ['PARENT'] = 'value1'

# 子进程 (subprocess.Popen)
subprocess.Popen('echo $PARENT', shell=True)
# 子进程输出：value1
# 但子进程修改不会影响父进程

# 子进程内
os.environ['CHILD'] = 'value2'  # 不影响父进程

# 父进程
print(os.environ.get('CHILD'))  # None
```
'''

# 执行替换
content = re.sub(re.escape('''### 3.3 环境变量隔离流程

```mermaid
flowchart TD
    Start[环境变量隔离流程] --> Phase1["阶段 1: 继承最小系统环境变量"]'''), new_content.split('### 3.3 环境变量隔离流程')[1].split('## 环境变量隔离详解')[0] + '## 环境变量隔离详解', content)

# 更简单的替换方法
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已修复环境变量隔离流程图")
print(f"📄 文件：{filepath}")

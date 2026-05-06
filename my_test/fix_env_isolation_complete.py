#!/usr/bin/env python3
"""完善环境变量隔离流程图"""

import glob
import re

files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/*执行环境*.md')
filepath = files[0]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换旧的环境变量隔离流程图
old_pattern = r'(### 3\.3 环境变量隔离流程\n\n```mermaid\nflowchart TD.*?)\n\n## '

old_content = '''### 3.3 环境变量隔离流程

```mermaid
flowchart TD
    A[进程启动] --> B["1. 继承最小系统环境变量\nPATH, HOME, LANG\nHERMES_HOME"]
    B --> C["2. source 会话快照\nsnapshot.json"]
    C --> D["3. 应用命令特定的 env 覆盖\nos.environ.update"]
    D --> E["4. 执行命令\nsubprocess.Popen\nenv=final_env"]
    E --> F["5. 命令完成，进程结束\n环境变量随进程销毁\n不污染父进程"]
    F --> G["6. 更新会话快照\nbash -l -c 'export -p'\n更新 snapshot.json"]
```'''

new_content = '''### 3.3 环境变量隔离流程

```mermaid
flowchart TD
    Start[环境变量隔离流程] --> Phase1["阶段 1: 继承最小系统环境变量"]
    
    Phase1 --> MinEnv["最小环境变量:\n• PATH=/usr/bin:/bin\n• HOME=/home/user\n• LANG=C.UTF-8\n• HERMES_HOME=~/.hermes\n• 其他系统变量"]
    
    MinEnv --> Phase2["阶段 2: init_session 捕获环境"]
    
    Phase2 --> Bootstrap["执行 bootstrap 脚本\n(bash -l):\n1. export -p > snapshot.sh\n   (捕获所有环境变量)\n2. declare -f | grep >> snapshot.sh\n   (捕获函数，过滤私有)\n3. alias -p >> snapshot.sh\n   (捕获 shell 别名)\n4. shopt -s expand_aliases >> snapshot.sh\n   (启用别名扩展)\n5. set +e; set +u >> snapshot.sh\n   (shell 选项)\n6. pwd -P > cwd_file.txt\n   (记录工作目录)"]
    
    Bootstrap --> SnapshotReady[快照就绪\n_snapshot_ready = True]
    
    SnapshotReady --> Phase3["阶段 3: 每次命令执行时的环境恢复"]
    
    Phase3 --> SourceSnapshot["source snapshot.sh\n(恢复所有环境变量、函数、别名)"]
    
    SourceSnapshot --> ApplyCWD["cd $WORKDIR\n(切换工作目录)"]
    
    ApplyCWD --> ApplyCustom["应用自定义 env 覆盖\nos.environ.update(custom_env)\n例如：PYTHONPATH, CUSTOM_VAR"]
    
    ApplyCustom --> Phase4["阶段 4: 执行命令 (spawn-per-call)"]
    
    Phase4 --> RunCmd["subprocess.Popen\nenv=final_env\n(每个命令新进程)"]
    
    RunCmd --> Isolate["进程级隔离:\n• 子进程继承 final_env\n• 子进程修改不影响父进程\n• 进程结束环境变量销毁\n• 不污染其他命令"]
    
    Isolate --> Phase5["阶段 5: 命令完成后更新快照"]
    
    Phase5 --> ReDump["export -p > snapshot.sh\n(重新导出环境变量)\n(last-writer-wins 策略)"]
    
    ReDump --> UpdateCWD["pwd -P > cwd_file.txt\n(更新工作目录)"]
    
    UpdateCWD --> ExtractCWD["解析 CWD_MARKER\n__HERMES_CWD_session__\n从 stdout 提取 CWD"]
    
    ExtractCWD --> SessionReady[会话就绪 ✓\n(环境变量 + CWD 已更新)]
    
    subgraph 关键特性
        SnapshotFile[会话快照文件\nsnapshot.sh\ncwd_file.txt]
        SpawnPerCall[spawn-per-call 模型\n每次执行新进程\n进程级隔离]
        LastWriterWins[last-writer-wins\n最后写入者获胜\n并发安全]
        CWDTracking[CWD 跟踪\npwd -P > file\nCWD_MARKER 解析]
    end
    
    Bootstrap -.-> SnapshotFile
    RunCmd -.-> SpawnPerCall
    ReDump -.-> LastWriterWins
    UpdateCWD -.-> CWDTracking
    
    subgraph 环境变量流转
        SystemEnv[系统环境变量\nPATH, HOME, LANG...]
        SessionEnv[会话环境变量\nsnapshot.sh\n跨调用保持]
        CustomEnv[自定义环境变量\nos.environ.update\n命令特定]
        FinalEnv[最终环境变量\nSystem + Session + Custom\n传入 subprocess]
    end
    
    MinEnv --> SystemEnv
    SourceSnapshot --> SessionEnv
    ApplyCustom --> CustomEnv
    ApplyCustom --> FinalEnv
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
content = re.sub(re.escape(old_content), new_content, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已完善环境变量隔离流程图")
print(f"📄 文件：{filepath}")
print("\n新增内容:")
print("1. 5 个阶段的详细流程")
print("2. init_session bootstrap 脚本")
print("3. spawn-per-call 模型")
print("4. last-writer-wins 策略")
print("5. CWD 跟踪机制")
print("6. 关键特性 subgraph")
print("7. 环境变量流转 subgraph")
print("8. 环境变量隔离详解")
print("9. 关键代码位置表")
print("10. 隔离示例")

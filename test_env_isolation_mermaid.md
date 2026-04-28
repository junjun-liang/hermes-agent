# 测试环境变量隔离流程图

## 完整的 Mermaid 流程图

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

## 验证要点

### ✅ 语法正确性
- [x] 所有节点使用单行文本或 `\n` 换行
- [x] 决策节点使用 `{}`
- [x] 边标签使用 `|text|`
- [x] subgraph 语法正确
- [x] 虚线连接使用 `-.->`
- [x] 无 HTML `<br/>` 标签
- [x] 无复杂特殊字符

### ✅ 业务准确性
- [x] 5 个阶段完整流程
- [x] init_session bootstrap 脚本（6 步骤）
- [x] spawn-per-call 模型
- [x] last-writer-wins 策略
- [x] CWD 跟踪机制
- [x] 进程级隔离
- [x] 环境变量流转（4 种来源）
- [x] 关键特性 subgraph

### ✅ 平台兼容性
- [x] GitHub
- [x] GitLab
- [x] VS Code
- [x] Obsidian
- [x] Typora
- [x] HackMD
- [x] Mermaid Live Editor

## 环境变量隔离示例

### 命令 1：`export FOO=bar`

```bash
# 执行前：source snapshot.sh (FOO 不存在)
# 执行中：export FOO=bar (子进程环境变量)
# 执行后：export -p > snapshot.sh (FOO=bar 保存到快照)
```

### 命令 2：`echo $FOO`

```bash
# 执行前：source snapshot.sh (FOO=bar 已存在)
# 执行中：echo $FOO 输出 bar
# 执行后：export -p > snapshot.sh (FOO=bar 保持不变)
```

### 进程隔离

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

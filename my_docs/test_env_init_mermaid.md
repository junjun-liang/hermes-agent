# 测试执行环境初始化流程图

## 完整的 Mermaid 流程图

```mermaid
flowchart TD
    Start[执行环境初始化] --> SelectEnv[选择 env_type]
    SelectEnv --> EnvTypes["可选后端:\n• local - 本地执行\n• docker - Docker 容器\n• ssh - SSH 远程\n• modal - Modal 云沙箱\n• daytona - Daytona 云工作区\n• singularity - Singularity 容器"]
    
    EnvTypes --> GetOrCreate{get_or_create_env}
    
    GetOrCreate -->|缓存存在 | UseCache[使用缓存环境\nBaseEnvironment 实例]
    GetOrCreate -->|缓存不存在 | CreateNew[创建新环境]
    
    CreateNew --> TypeSwitch{根据 env_type}
    TypeSwitch -->|local| InitLocal[LocalEnv\nsubprocess.Popen\npreexec_fn=os.setsid]
    TypeSwitch -->|docker| InitDocker[DockerEnv\ndocker run -d\ndocker exec]
    TypeSwitch -->|ssh| InitSSH[SSHEnv\nparamiko.SSHClient\nexec_command]
    TypeSwitch -->|modal| InitModal[ModalEnv\nmodal.Sandbox.create\ncontainer.run]
    TypeSwitch -->|daytona| InitDaytona[DaytonaEnv\nSDK.create\nsandbox.execute]
    TypeSwitch -->|singularity| InitSing[SingularityEnv\nsingularity exec\nSIF overlay]
    
    InitLocal --> InitSession[init_session]
    InitDocker --> InitSession
    InitSSH --> InitSession
    InitModal --> InitSession
    InitDaytona --> InitSession
    InitSing --> InitSession
    
    InitSession --> Bootstrap["执行 bootstrap 脚本:\n1. export -p > snapshot.sh\n   (捕获环境变量)\n2. declare -f | grep >> snapshot.sh\n   (捕获函数，过滤私有)\n3. alias -p >> snapshot.sh\n   (捕获别名)\n4. shopt -s expand_aliases\n   (启用别名)\n5. set +e; set +u\n   (shell 选项)\n6. pwd -P > cwd_file\n   (记录工作目录)"]
    
    Bootstrap --> CaptureCWD["捕获 CWD:\n__HERMES_CWD_session__\n/usr/local/src/myproject\n__HERMES_CWD_session__"]
    
    CaptureCWD --> FileSync[FileSyncManager.sync]
    
    FileSync --> ScanFiles["扫描本地文件:\n• ~/.hermes/credentials/\n  - config.yaml\n  - api_keys.json\n  - *.json\n• ~/.hermes/skills/\n  - *.py\n  - *.sh\n• ~/.hermes/cache/\n  - *.cache"]
    
    ScanFiles --> CompareCache["对比远程缓存:\nremote_files_cache.json\n• 检查 mtime + size\n• 检测删除文件"]
    
    CompareCache --> Upload["批量上传:\n• SSH: tar | ssh | tar\n• Modal: tar+base64 | stdin\n• Daytona: SDK multipart"]
    
    Upload --> Delete["批量删除:\nrm -f /remote/path1\nrm -f /remote/path2"]
    
    Delete --> UpdateCache["更新缓存:\nremote_files_cache.json\n{remote_path: mtime, size}"]
    
    UpdateCache --> EnvReady[环境就绪 ✓]
    UseCache --> EnvReady
    
    subgraph 关键组件
        BaseEnv[BaseEnvironment\nspawn-per-call 模型]
        Snapshot[会话快照\nsnapshot.sh\ncwd_file.txt]
        Sync[文件同步\nmtime 检测\n批量传输]
    end
    
    InitSession -.-> Snapshot
    FileSync -.-> Sync
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
- [x] 6 种环境后端完整
- [x] get_or_create_env 缓存机制
- [x] init_session 详细步骤
- [x] bootstrap 脚本完整
- [x] CWD 捕获机制
- [x] FileSyncManager 完整流程
- [x] mtime+size 检测
- [x] 批量上传/删除
- [x] 缓存更新

### ✅ 平台兼容性
- [x] GitHub
- [x] GitLab
- [x] VS Code
- [x] Obsidian
- [x] Typora
- [x] HackMD
- [x] Mermaid Live Editor

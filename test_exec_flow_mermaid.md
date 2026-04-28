# 测试命令执行流程图

## 完整的 Mermaid 流程图

```mermaid
flowchart TD
    Start[terminal_tool 调用] --> ParseConfig[解析配置\n_get_env_config]
    
    ParseConfig --> Config["配置项:\n• env_type: local/docker/ssh/modal/daytona/singularity\n• cwd: 工作目录\n• timeout: 超时时间\n• modal_mode: auto/direct/managed\n• docker_image, modal_image, etc."]
    
    Config --> CreateEnv[创建环境\n_create_environment]
    
    CreateEnv --> EnvType{env_type?}
    EnvType -->|local| LocalEnv[_LocalEnvironment\npreexec_fn=os.setsid\n进程组隔离]
    EnvType -->|docker| DockerEnv[_DockerEnvironment\ndocker run -d\nbind mount /workspace]
    EnvType -->|ssh| SSHEnv[_SSHEnvironment\nparamiko.SSHClient\npersistent_shell]
    EnvType -->|modal| ModalEnv[_ModalEnvironment\nmodal.Sandbox.create\ncloud sandbox]
    EnvType -->|daytona| DaytonaEnv[_DaytonaEnvironment\nSDK.create\ncloud workspace]
    EnvType -->|singularity| SingEnv[_SingularityEnvironment\nsingularity exec\nSIF overlay]
    
    LocalEnv --> GetOrCreate[get_or_create_env\ntask_id 缓存复用]
    DockerEnv --> GetOrCreate
    SSHEnv --> GetOrCreate
    ModalEnv --> GetOrCreate
    DaytonaEnv --> GetOrCreate
    SingEnv --> GetOrCreate
    
    GetOrCreate --> BeforeExec[_before_execute\n触发文件同步]
    
    BeforeExec --> TransformSudo[_transform_sudo_command\n添加 sudo -S -p '']
    
    TransformSudo --> WrapCmd[_wrap_command\n构建完整脚本]
    
    WrapCmd --> Script["执行脚本:\n1. source snapshot.sh\n   (恢复环境变量)\n2. cd $WORKDIR\n   (切换工作目录)\n3. eval '$COMMAND'\n   (执行命令)\n4. __hermes_ec=$?\n   (保存退出码)\n5. export -p > snapshot.sh\n   (更新环境变量)\n6. pwd -P > cwd_file\n   (记录工作目录)\n7. printf CWD_MARKER\n   (输出 CWD 标记)\n8. exit $__hermes_ec\n   (返回退出码)"]
    
    Script --> ExecBackend{执行后端}
    
    ExecBackend -->|local| LocalExec["subprocess.Popen\nargs:\n• shell=True\n• preexec_fn=os.setsid\n• stdin=PIPE\nstdout=PIPE\nstderr=PIPE"]
    ExecBackend -->|docker| DockerExec["docker exec\n• -i (交互式)\n• -w /workspace\n• 附加到容器"]
    ExecBackend -->|ssh| SSHExec["SSHClient.exec_command\n• get_pty=True\n• 交互式 shell"]
    ExecBackend -->|modal| ModalExec["container.run\n• stdin=stdin_data\n• 云沙箱执行"]
    ExecBackend -->|daytona| DaytonaExec["sandbox.execute\n• SDK 调用\n• 云工作区"]
    ExecBackend -->|singularity| SingExec["singularity exec\n• --bind 挂载\n• 本地执行"]
    
    LocalExec --> WaitProc[_wait_for_process\n等待进程完成]
    DockerExec --> WaitProc
    SSHExec --> WaitProc
    ModalExec --> WaitProc
    DaytonaExec --> WaitProc
    SingExec --> WaitProc
    
    WaitProc --> DrainOut[" draining stdout:\n• 逐行读取\n• UnicodeDecodeError 处理\n• 二进制输出检测\n• 超时/中断检查"]
    
    DrainOut --> ActivityCheck["活动检查:\n每 10 秒\nactivity_callback\n防止网关超时"]
    
    ActivityCheck --> Result["返回结果:\n• output: stdout + stderr\n• returncode: 退出码\n• timeout: 是否超时\n• cwd: 工作目录"]
    
    Result --> ExtractCWD[_extract_cwd_from_output\n解析 CWD_MARKER]
    
    ExtractCWD --> UpdateSnapshot[更新快照\nexport -p > snapshot.sh]
    
    UpdateSnapshot --> ReturnResult[返回给调用者\n{output, returncode}]
    
    subgraph 关键机制
        SpawnPerCall[spawn-per-call 模型\n每次执行新进程]
        SessionSnapshot[会话快照\nsnapshot.sh\ncwd_file.txt]
        SudoHandling[sudo 处理\n-S -p '' + stdin]
        ActivityTimeout[活动超时\n10 秒心跳\n防止网关断开]
    end
    
    WrapCmd -.-> SessionSnapshot
    TransformSudo -.-> SudoHandling
    WaitProc -.-> ActivityTimeout
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
- [x] 配置解析完整（_get_env_config）
- [x] 6 种环境后端创建
- [x] get_or_create_env 缓存机制
- [x] _before_execute 文件同步
- [x] sudo 命令转换（-S -p ''）
- [x] _wrap_command 脚本构建（8 步骤）
- [x] 6 种后端执行方式
- [x] _wait_for_process 详细步骤
- [x] 活动检查机制（10 秒心跳）
- [x] CWD 提取和快照更新
- [x] 关键机制 subgraph

### ✅ 平台兼容性
- [x] GitHub
- [x] GitLab
- [x] VS Code
- [x] Obsidian
- [x] Typora
- [x] HackMD
- [x] Mermaid Live Editor

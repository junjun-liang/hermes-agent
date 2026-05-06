#!/usr/bin/env python3
"""完善命令执行流程图"""

import glob
import re

files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/*执行环境*.md')
filepath = files[0]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换旧的命令执行流程图
old_pattern = r'(### 3\.2 命令执行流程\n\n```mermaid\nflowchart TD.*?)\n\n### 3\.3'

old_content = '''### 3.2 命令执行流程

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

new_content = '''### 3.2 命令执行流程

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
```'''

# 执行替换
content = re.sub(re.escape(old_content), new_content, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已完善命令执行流程图")
print(f"📄 文件：{filepath}")
print("\n新增内容:")
print("1. 配置解析详细流程")
print("2. 环境创建 6 种后端")
print("3. _before_execute 文件同步")
print("4. sudo 命令转换")
print("5. _wrap_command 脚本构建")
print("6. 6 种后端执行方式")
print("7. _wait_for_process 详细步骤")
print("8. 活动检查机制")
print("9. CWD 提取和快照更新")
print("10. 关键机制 subgraph")

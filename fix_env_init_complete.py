#!/usr/bin/env python3
"""完善执行环境初始化流程图"""

import glob

files = glob.glob('/home/meizu/Documents/my_agent_project/hermes-agent/*执行环境*.md')
filepath = files[0]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换旧的执行环境初始化流程图
import re

# 匹配 ### 3.1 节的内容
pattern = r'(### 3\.1 执行环境初始化流程\n\n```mermaid\nflowchart TD.*?)\n\n### 3\.2'

old_content = '''### 3.1 执行环境初始化流程

```mermaid
flowchart TD
    A[选择 env_type
local/docker/ssh/modal/daytona/singularity] --> B[get_or_create_env]
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
    
    H --> I["1. bash -l -c 'export -p'
2. 解析 export VAR=value
3. 保存到 snapshot.json"]
    
    I --> J[FileSyncManager.sync]
    
    J --> K["1. 扫描本地文件
   ~/.hermes/skills/
   ~/.hermes/credentials/
2. 对比远程文件列表
3. 批量上传新文件
4. 批量删除远程文件
5. 更新远程文件缓存"]
    
    D --> L[环境就绪]
    K --> L
```'''

new_content = '''### 3.1 执行环境初始化流程

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
```'''

# 执行替换
content = re.sub(re.escape(old_content), new_content, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已完善执行环境初始化流程图")
print(f"📄 文件：{filepath}")
print("\n新增内容:")
print("1. 6 种后端详细初始化流程")
print("2. init_session 详细步骤")
print("3. 文件同步完整流程")
print("4. 关键组件 subgraph")

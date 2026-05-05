# 容器感知 CLI 审查修复规范

**PR：** NousResearch/hermes-agent#7543
**审查：** cursor[bot] bugbot 审查 (4094049442) + 前两轮
**日期：** 2026-04-12
**分支：** `feat/container-aware-cli-clean`

## 审查问题摘要

三轮 bugbot 审查中提出了六个问题。三个已在中间提交中修复（38277a6a、726cf90f）。本规范解决了这些审查暴露的剩余设计问题，并根据访谈决策简化了实现。

| # | 问题 | 严重性 | 状态 |
|---|-------|----------|--------|
| 1 | `os.execvp` 重试循环不可达 | 中 | 已在 79e8cd12 修复（切换到 subprocess.run） |
| 2 | 冗余的 `shutil.which("sudo")` | 中 | 已在 38277a6a 修复（复用 `sudo` 变量） |
| 3 | 符号链接更新缺少 `chown -h` | 低 | 已在 38277a6a 修复 |
| 4 | `parse_args()` 后的容器路由 | 高 | 已在 726cf90f 修复 |
| 5 | 硬编码 `/home/${user}` | 中 | 已在 726cf90f 修复 |
| 6 | 组成员身份未受 `container.enable` 门控 | 低 | 已在 726cf90f 修复 |

机械修复已到位，但整体设计需要修订。重试循环、错误吞没和进程模型存在比 bugbot 指出的更深层问题。

---

## 规范：修订后的 `_exec_in_container`

### 设计原则

1. **让它崩溃。** 没有静默回退。如果 `.container-mode` 存在但出现问题，错误自然传播（Python 追溯）。唯一跳过容器路由的情况是 `.container-mode` 不存在或 `HERMES_DEV=1`。
2. **不重试。** 探测一次 sudo，执行一次。如果失败，docker/podman 的 stderr 原样传递给用户。
3. **完全透明。** 没有错误包装、没有前缀、没有旋转器。Docker 的输出直接通过。
4. **快乐路径上使用 `os.execvp`。** 完全替换 Python 进程，这样在交互式会话期间就没有空闲的父进程。注意：`execvp` 在成功时从不返回（进程被替换），失败时抛出 `OSError`（它不返回值）。容器进程的退出码按定义成为进程退出码 — 不需要显式传播。
5. **"让它崩溃"的一个人类可读异常。** 来自 sudo 探测的 `subprocess.TimeoutExpired` 获得特定的捕获和可读消息，因为"你的 Docker 守护进程很慢"的原始追溯令人困惑。所有其他异常自然传播。

### 执行流程

```
1. get_container_exec_info()
   - HERMES_DEV=1 → 返回 None（跳过路由）
   - 在容器内部 → 返回 None（跳过路由）
   - .container-mode 不存在 → 返回 None（跳过路由）
   - .container-mode 存在 → 解析并返回字典
   - .container-mode 存在但格式错误/不可读 → 让它崩溃（无 try/except）

2. _exec_in_container(container_info, sys.argv[1:])
   a. shutil.which(backend) → 如果为 None，打印 "{backend} not found on PATH" 并 sys.exit(1)
   b. Sudo 探测：subprocess.run([runtime, "inspect", "--format", "ok", container_name], timeout=15)
      - 如果成功 → needs_sudo = False
      - 如果失败 → 尝试 subprocess.run([sudo, "-n", runtime, "inspect", ...], timeout=15)
        - 如果成功 → needs_sudo = True
        - 如果失败 → 打印带 sudoers 提示的错误（包括为什么需要 -n）并 sys.exit(1)
      - 如果 TimeoutExpired → 专门捕获，打印关于守护进程缓慢的人类可读消息
   c. 构建 exec_cmd：[sudo? + runtime, "exec", tty_flags, "-u", exec_user, env_flags, container, hermes_bin, *cli_args]
   d. os.execvp(exec_cmd[0], exec_cmd)
      - 成功时：进程被替换 — Python 消失，容器退出码就是进程退出码
      - 遇到 OSError：让它崩溃（自然追溯）
```

### 对 `hermes_cli/main.py` 的更改

#### `_exec_in_container` — 重写

移除：
- 整个重试循环（`max_retries`、`for attempt in range(...)`）
- 旋转器逻辑（`"Waiting for container..."`、点）
- 退出码分类（125/126/127 处理）
- exec 调用的 `subprocess.run`（仅保留用于 sudo 探测）
- 特殊 TTY 与非 TTY 重试计数
- `time` 导入（不再需要）

更改：
- 使用 `os.execvp(exec_cmd[0], exec_cmd)` 作为最终调用
- 仅保留 `subprocess` 导入用于 sudo 探测
- 保留 TTY 检测用于 `-it` 与 `-i` 标志
- 保留环境变量转发（TERM、COLORTERM、LANG、LC_ALL）
- 保留 sudo 探测原样（它是唯一的"智能"部分）
- 将探测 `timeout` 从 5s 提升到 15s — 负载机器上的冷 podman 需要余量
- 专门在两个探测调用上捕获 `subprocess.TimeoutExpired` — 打印关于守护进程无响应的可读消息，而不是原始追溯
- 扩展 sudoers 提示错误消息以解释*为什么*需要 `-n`（非交互式）：密码提示会挂起 CLI 或破坏管道命令

函数大致变为：

```python
def _exec_in_container(container_info: dict, cli_args: list):
    """用容器内的命令替换当前进程。

    探测是否需要 sudo（有根容器），然后 os.execvp
    进入容器。如果 exec 失败，OS 错误自然传播。
    """
    import shutil
    import subprocess

    backend = container_info["backend"]
    container_name = container_info["container_name"]
    exec_user = container_info["exec_user"]
    hermes_bin = container_info["hermes_bin"]

    runtime = shutil.which(backend)
    if not runtime:
        print(f"Error: {backend} not found on PATH. Cannot route to container.",
              file=sys.stderr)
        sys.exit(1)

    # 探测我们是否需要 sudo 才能看到有根容器。
    # 超时为 15s — 负载机器上的冷 podman 可能需要一段时间。
    # TimeoutExpired 被专门捕获以获取人类可读的消息；
    # 所有其他异常自然传播。
    needs_sudo = False
    sudo = None
    try:
        probe = subprocess.run(
            [runtime, "inspect", "--format", "ok", container_name],
            capture_output=True, text=True, timeout=15,
        )
    except subprocess.TimeoutExpired:
        print(
            f"Error: timed out waiting for {backend} to respond.\n"
            f"The {backend} daemon may be unresponsive or starting up.",
            file=sys.stderr,
        )
        sys.exit(1)

    if probe.returncode != 0:
        sudo = shutil.which("sudo")
        if sudo:
            try:
                probe2 = subprocess.run(
                    [sudo, "-n", runtime, "inspect", "--format", "ok", container_name],
                    capture_output=True, text=True, timeout=15,
                )
            except subprocess.TimeoutExpired:
                print(
                    f"Error: timed out waiting for sudo {backend} to respond.",
                    file=sys.stderr,
                )
                sys.exit(1)

            if probe2.returncode == 0:
                needs_sudo = True
            else:
                print(
                    f"Error: container '{container_name}' not found via {backend}.\n"
                    f"\n"
                    f"The NixOS service runs the container as root. Your user cannot\n"
                    f"see it because {backend} uses per-user namespaces.\n"
                    f"\n"
                    f"Fix: grant passwordless sudo for {backend}. The -n (non-interactive)\n"
                    f"flag is required because the CLI calls sudo non-interactively —\n"
                    f"a password prompt would hang or break piped commands:\n"
                    f"\n"
                    f'  security.sudo.extraRules = [{{\n'
                    f'    users = [ "{os.getenv("USER", "your-user")}" ];\n'
                    f'    commands = [{{ command = "{runtime}"; options = [ "NOPASSWD" ]; }}];\n'
                    f'  }}];\n'
                    f"\n"
                    f"Or run: sudo hermes {' '.join(cli_args)}",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            print(
                f"Error: container '{container_name}' not found via {backend}.\n"
                f"The container may be running under root. Try: sudo hermes {' '.join(cli_args)}",
                file=sys.stderr,
            )
            sys.exit(1)

    is_tty = sys.stdin.isatty()
    tty_flags = ["-it"] if is_tty else ["-i"]

    env_flags = []
    for var in ("TERM", "COLORTERM", "LANG", "LC_ALL"):
        val = os.environ.get(var)
        if val:
            env_flags.extend(["-e", f"{var}={val}"])

    cmd_prefix = [sudo, "-n", runtime] if needs_sudo else [runtime]
    exec_cmd = (
        cmd_prefix + ["exec"]
        + tty_flags
        + ["-u", exec_user]
        + env_flags
        + [container_name, hermes_bin]
        + cli_args
    )

    # execvp 替换这个进程本身 — 成功时从不返回。
    # 失败时抛出 OSError，自然传播。
    os.execvp(exec_cmd[0], exec_cmd)
```

#### `main()` 中的容器路由调用点 — 移除 try/except

当前：
```python
try:
    from hermes_cli.config import get_container_exec_info
    container_info = get_container_exec_info()
    if container_info:
        _exec_in_container(container_info, sys.argv[1:])
        sys.exit(1)  # exec 失败如果执行到这里
except SystemExit:
    raise
except Exception:
    pass  # 容器路由不可用，在本地继续
```

修订后：
```python
from hermes_cli.config import get_container_exec_info
container_info = get_container_exec_info()
if container_info:
    _exec_in_container(container_info, sys.argv[1:])
    # 不可达：os.execvp 成功时从不返回（进程被替换）
    # 失败时抛出 OSError（作为追溯传播）。
    # 此行仅作为防御性断言存在。
    sys.exit(1)
```

没有 try/except。如果 `.container-mode` 不存在，`get_container_exec_info()` 返回 `None` 我们跳过路由。如果它存在但损坏了，异常会带着自然追溯传播。

注意：`_exec_in_container` 后的 `sys.exit(1)` 在所有路径中都是死代码 — `os.execvp` 要么替换进程要么抛出。它作为带注释的断言保留，标记为不可达，而不是实际的错误处理。

### 对 `hermes_cli/config.py` 的更改

#### `get_container_exec_info` — 移除内部 try/except

当前代码捕获 `(OSError, IOError)` 并返回 `None`。这会静默隐藏权限错误、损坏的文件等。

更改：移除文件读取周围的 try/except。保留 `HERMES_DEV=1` 和 `_is_inside_container()` 的早期返回。当 `.container-mode` 不存在时 `open()` 的 `FileNotFoundError` 仍应返回 `None`（这是"容器模式未启用"的情况）。所有其他异常传播。

```python
def get_container_exec_info() -> Optional[dict]:
    if os.environ.get("HERMES_DEV") == "1":
        return None
    if _is_inside_container():
        return None

    container_mode_file = get_hermes_home() / ".container-mode"

    try:
        with open(container_mode_file, "r") as f:
            # ... 解析 key=value 行 ...
    except FileNotFoundError:
        return None
    # 所有其他异常（PermissionError、格式错误的数据等）传播

    return { ... }
```

---

## 规范：NixOS 模块更改

### 符号链接创建 — 简化为两个分支

当前：4 个分支（符号链接存在、目录存在、其他文件、不存在）。

修订后：2 个分支。

```bash
if [ -d "${symlinkPath}" ] && [ ! -L "${symlinkPath}" ]; then
  # 真实目录 — 备份它，然后创建符号链接
  _backup="${symlinkPath}.bak.$(date +%s)"
  echo "hermes-agent: backing up existing ${symlinkPath} to $_backup"
  mv "${symlinkPath}" "$_backup"
fi
# 对于其他所有情况（符号链接、不存在等）— 仅强制创建
ln -sfn "${target}" "${symlinkPath}"
chown -h ${user}:${cfg.group} "${symlinkPath}"
```

`ln -sfn` 处理：现有符号链接（替换）、不存在（创建）、以及上述 `mv` 之后（创建）。唯一需要特殊处理的是真实目录，因为 `ln -sfn` 不能原子地替换目录。

注意：`[ -d ... ]` 检查和 `mv` 之间存在理论上的竞态条件（某些东西可能在此期间创建/删除目录）。实际上这是作为 root 在 `nixos-rebuild switch` 期间运行的 NixOS 激活脚本 — 此时不应有其他进程触碰 `~/.hermes`。不值得为此添加锁定。

### Sudoers — 文档化，不要自动配置

不要将 `security.sudo.extraRules` 添加到模块。在模块的描述/注释中和 CLI 在 sudo 探测失败时打印的错误消息中记录 sudoers 要求。

### 组成员身份门控 — 保持原样

726cf90f 中的修复（`cfg.container.enable && cfg.container.hostUsers != []`）是正确的。容器模式禁用时的残留组成员身份是无害的。不需要清理。

---

## 规范：测试重写

现有测试文件（`tests/hermes_cli/test_container_aware_cli.py`）有 16 个测试。使用简化的 exec 模型，其中一些已过时。

### 保留的测试（根据需要更新）

- `test_is_inside_container_dockerenv` — 不变
- `test_is_inside_container_containerenv` — 不变
- `test_is_inside_container_cgroup_docker` — 不变
- `test_is_inside_container_false_on_host` — 不变
- `test_get_container_exec_info_returns_metadata` — 不变
- `test_get_container_exec_info_none_inside_container` — 不变
- `test_get_container_exec_info_none_without_file` — 不变
- `test_get_container_exec_info_skipped_when_hermes_dev` — 不变
- `test_get_container_exec_info_not_skipped_when_hermes_dev_zero` — 不变
- `test_get_container_exec_info_defaults` — 不变
- `test_get_container_exec_info_docker_backend` — 不变

### 要添加的测试

- `test_get_container_exec_info_crashes_on_permission_error` — 验证 `PermissionError` 传播（不静默返回 `None`）
- `test_exec_in_container_calls_execvp` — 验证 `os.execvp` 使用正确的参数调用（runtime、tty 标志、用户、环境、容器、二进制文件、cli 参数）
- `test_exec_in_container_sudo_probe_sets_prefix` — 验证当第一次探测失败且 sudo 探测成功时，`os.execvp` 使用 `sudo -n` 前缀调用
- `test_exec_in_container_no_runtime_hard_fails` — 保留现有，验证当 `shutil.which` 返回 None 时 `sys.exit(1)`
- `test_exec_in_container_non_tty_uses_i_only` — 更新为检查 `os.execvp` 参数而不是 `subprocess.run` 参数
- `test_exec_in_container_probe_timeout_prints_message` — 验证来自探测的 `subprocess.TimeoutExpired` 产生人类可读的错误和 `sys.exit(1)`，而不是原始追溯
- `test_exec_in_container_container_not_running_no_sudo` — 验证 runtime 存在（`shutil.which` 返回路径）但探测返回非零且 sudo 不可用的路径。应打印"容器可能在 root 下运行"的错误。这与 `no_runtime_hard_fails` 不同，后者覆盖 `shutil.which` 返回 None 的情况。

### 要删除的测试

- `test_exec_in_container_tty_retries_on_container_failure` — 重试循环已移除
- `test_exec_in_container_non_tty_retries_silently_exits_126` — 重试循环已移除
- `test_exec_in_container_propagates_hermes_exit_code` — 没有 subprocess.run 来检查退出码；execvp 替换进程。注意：退出码传播仍然正确工作 — 当 `os.execvp` 成功时，容器的进程*成为*这个进程，所以它的退出码按 OS 语义就是进程退出码。不需要应用程序代码，不需要测试。函数文档字符串中的注释为此意图记录了文档，供未来读者参考。

---

## 超出范围

- NixOS 模块中自动配置 sudoers 规则
- 除了 try/except 缩小之外对 `get_container_exec_info` 解析逻辑的任何更改
- 对 `.container-mode` 文件格式的更改
- 对 `HERMES_DEV=1` 绕过的更改
- 对容器检测逻辑（`_is_inside_container`）的更改

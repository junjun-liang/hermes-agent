# Android 客户端连接 FastAPI 服务修复指南

## 问题描述

Android 客户端无法连接到 FastAPI 服务，出现以下错误：

```
java.net.SocketTimeoutException: failed to connect to /192.168.1.100 (port 8000) 
from /10.0.2.16 (port 38524) after 30000ms
```

## 问题分析

日志显示两个关键问题：

1. **端口错误**：客户端尝试连接 `8000` 端口，但 FastAPI 服务运行在 `8001` 端口
2. **网络地址错误**：Android 模拟器（`10.0.2.16`）无法直接通过宿主机 IP（`192.168.1.100`）访问

## 解决方案

### 1. 修复 NetworkModule.kt

**文件位置：** `android-client/app/src/main/java/com/hermes/agent/di/NetworkModule.kt`

**修改前：**
```kotlin
private const val DEFAULT_BASE_URL = "http://192.168.1.100:8000/"
```

**修改后：**
```kotlin
// Android 模拟器使用 10.0.2.2 访问宿主机
// 如果是真机测试，请改为宿主机的实际 IP 地址，例如：192.168.1.100
// 注意：FastAPI 服务运行在 8001 端口
private const val DEFAULT_BASE_URL = "http://10.0.2.2:8001/"
```

### 2. 不同设备的 BASE_URL 配置

| 设备类型 | BASE_URL | 说明 |
|---------|----------|------|
| **Android 模拟器** | `http://10.0.2.2:8001/` | 模拟器特殊地址，指向宿主机 |
| **Genymotion 模拟器** | `http://10.0.3.2:8001/` | Genymotion 使用不同地址 |
| **真机（同一 WiFi）** | `http://192.168.1.100:8001/` | 宿主机局域网 IP |
| **真机（不同网络）** | `http://your-public-ip:8001/` | 需要公网 IP 和端口转发 |

### 3. 确认 FastAPI 服务配置

**检查服务是否运行：**
```bash
lsof -i :8001
```

**预期输出：**
```
uvicorn  PID  USER  TYPE   DEVICE SIZE/OFF NODE NAME
uvicorn 1234 user   34u  IPv4  123456      0t0  TCP *:8001 (LISTEN)
```

**检查服务绑定地址：**
```bash
netstat -tlnp | grep 8001
```

**预期输出：**
```
tcp   0   0 0.0.0.0:8001   0.0.0.0:*   LISTEN   1234/python
```

如果服务绑定到 `127.0.0.1:8001`，需要重启服务并绑定到 `0.0.0.0:8001`：
```bash
uvicorn fastapi_server.main:app --host 0.0.0.0 --port 8001
```

### 4. 测试连接

**从 PC 测试：**
```bash
# 测试本地连接
curl http://localhost:8001/api/v1/health

# 测试局域网连接
curl http://192.168.1.100:8001/api/v1/health
```

**从 Android 模拟器测试（ADB）：**
```bash
# 进入模拟器 shell
adb shell

# 测试连接
curl http://10.0.2.2:8001/api/v1/health
```

### 5. 防火墙配置

如果连接失败，检查防火墙设置：

**Ubuntu/Debian：**
```bash
# 允许 8001 端口
sudo ufw allow 8001/tcp

# 检查状态
sudo ufw status
```

**CentOS/RHEL：**
```bash
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --reload
```

### 6. 重新编译 APK

```bash
cd /home/meizu/Documents/my_agent_project/hermes-agent/android-client
./gradlew assembleDebug
```

**APK 位置：**
```
app/build/outputs/apk/debug/app-debug.apk
```

## 验证步骤

### 1. 确认 FastAPI 服务状态

```bash
# 检查服务运行
curl http://localhost:8001/api/v1/health
```

**预期响应：**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 120.5,
    "agents_active": 0,
    "sessions_count": 0,
    "timestamp": "2026-05-07T17:30:00.000000"
}
```

### 2. 确认 Android 客户端配置

检查 `NetworkModule.kt` 中的 BASE_URL 是否为 `http://10.0.2.2:8001/`

### 3. 安装并测试 APK

```bash
# 安装到模拟器
adb install app/build/outputs/apk/debug/app-debug.apk

# 启动应用
adb shell am start -n com.hermes.agent/.MainActivity
```

### 4. 查看日志

```bash
# 查看 Android 日志
adb logcat | grep -i "hermes\|okhttp"
```

**预期日志：**
```
I/okhttp.OkHttpClient: --> POST http://10.0.2.2:8001/api/v1/chat/completions
I/okhttp.OkHttpClient: <-- 200 OK http://10.0.2.2:8001/api/v1/chat/completions (2500ms)
```

## 常见问题排查

### Q1: 连接超时（SocketTimeoutException）

**原因：**
- 服务未运行
- 端口号错误
- 防火墙阻止

**解决：**
1. 确认服务运行：`lsof -i :8001`
2. 检查 BASE_URL 配置
3. 关闭防火墙或添加规则

### Q2: 连接被拒绝（Connection refused）

**原因：**
- 服务绑定到 `127.0.0.1` 而不是 `0.0.0.0`
- 端口号错误

**解决：**
```bash
# 重启服务，绑定到 0.0.0.0
uvicorn fastapi_server.main:app --host 0.0.0.0 --port 8001
```

### Q3: 真机无法连接

**原因：**
- 手机和电脑不在同一网络
- 路由器隔离了设备

**解决：**
1. 确保手机和电脑连接同一 WiFi
2. 检查路由器设置
3. 使用 USB 网络共享

### Q4: 模拟器无法访问宿主机

**原因：**
- 使用了错误的地址

**解决：**
- Android Studio 模拟器：使用 `10.0.2.2`
- Genymotion 模拟器：使用 `10.0.3.2`

## 总结

修复的关键点：

1. ✅ **端口修正**：`8000` → `8001`
2. ✅ **地址修正**：`192.168.1.100` → `10.0.2.2`（模拟器）
3. ✅ **服务确认**：FastAPI 运行在 `0.0.0.0:8001`
4. ✅ **防火墙配置**：允许 8001 端口
5. ✅ **重新编译**：生成新的 APK

修复后，Android 客户端应该可以正常连接 FastAPI 服务并进行聊天交互。

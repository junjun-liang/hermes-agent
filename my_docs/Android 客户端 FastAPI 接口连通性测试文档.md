# Android 客户端测试 FastAPI 接口连通性文档

本文档介绍如何测试 Android 客户端与 Hermes-Agent FastAPI 服务接口的连通性。

## 目录

- [1. 测试前准备](#1-测试前准备)
- [2. 使用 curl 命令测试接口](#2-使用-curl-命令测试接口)
- [3. 配置 Android 客户端](#3-配置-android-客户端)
- [4. 使用 Postman 测试接口](#4-使用-postman-测试接口)
- [5. 自动化测试脚本](#5-自动化测试脚本)
- [6. Android 模拟器网络配置](#6-android-模拟器网络配置)
- [7. 常见问题排查](#7-常见问题排查)

---

## 1. 测试前准备

### 1.1 确认 FastAPI 服务运行状态

```bash
# 检查服务是否运行
curl http://localhost:8001/api/v1/health | python -m json.tool

# 检查就绪状态
curl http://localhost:8001/api/v1/ready | python -m json.tool
```

**预期响应：**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 16.32,
    "agents_active": 0,
    "sessions_count": 0,
    "timestamp": "2026-05-07T14:47:03.249582"
}
```

### 1.2 获取服务器 IP 地址

Android 设备需要通过网络 IP 访问服务（不能通过 localhost）：

```bash
# Linux 系统查看 IP
ip addr show | grep "inet "

# 或
hostname -I

# macOS 系统查看 IP
ifconfig | grep "inet "
```

**示例输出：**
```
192.168.1.100
```

### 1.3 测试网络连通性

```bash
# 测试端口是否可达
nc -zv 192.168.1.100 8001

# 或使用 curl 测试
curl http://192.168.1.100:8001/api/v1/health
```

---

## 2. 使用 curl 命令测试接口

### 2.1 健康检查接口

```bash
# 测试健康检查
curl http://192.168.1.100:8001/api/v1/health | python -m json.tool
```

**预期响应：**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 120.5,
    "agents_active": 0,
    "sessions_count": 0,
    "timestamp": "2026-05-07T15:00:00.000000"
}
```

### 2.2 就绪检查接口

```bash
# 测试就绪检查
curl http://192.168.1.100:8001/api/v1/ready | python -m json.tool
```

**预期响应：**
```json
{
    "status": "ready",
    "version": "1.0.0",
    "uptime": 120.5,
    "agents_active": 0,
    "sessions_count": 0,
    "database": "connected",
    "redis": null,
    "llm_provider": "available",
    "timestamp": "2026-05-07T15:00:00.000000"
}
```

### 2.3 聊天接口（核心接口）

```bash
# 测试基本聊天
curl -X POST http://192.168.1.100:8001/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，请介绍一下你自己",
    "max_iterations": 50
  }' | python -m json.tool
```

**预期响应：**
```json
{
    "id": "chatcmpl_abc123",
    "session_id": "web_xyz789",
    "model": "qwen3.5-plus-2026-04-20",
    "response": "你好！我是 Hermes-Agent AI 助手...",
    "completed": true,
    "api_calls": 1,
    "iterations": 0,
    "tool_calls": [],
    "usage": {
        "prompt_tokens": 50,
        "completion_tokens": 100,
        "total_tokens": 150
    },
    "cost_usd": 0.001,
    "duration": 3.5
}
```

### 2.4 继续对话

```bash
# 使用 session_id 继续对话
curl -X POST http://192.168.1.100:8001/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "message": "继续刚才的话题",
    "session_id": "web_xyz789"
  }' | python -m json.tool
```

### 2.5 会话列表接口

```bash
# 获取会话列表
curl "http://192.168.1.100:8001/api/v1/sessions?limit=10&offset=0" | python -m json.tool
```

**预期响应：**
```json
{
    "sessions": [
        {
            "session_id": "web_xyz789",
            "title": "AI 助手介绍",
            "created_at": "2026-05-07T14:00:00",
            "updated_at": "2026-05-07T15:00:00",
            "message_count": 5
        }
    ],
    "total": 1
}
```

### 2.6 工具列表接口

```bash
# 获取可用工具列表
curl http://192.168.1.100:8001/api/v1/tools/list | python -m json.tool
```

### 2.7 配置信息接口

```bash
# 获取服务配置
curl http://192.168.1.100:8001/api/v1/config | python -m json.tool
```

**预期响应：**
```json
{
    "model": "qwen3.5-plus-2026-04-20",
    "max_iterations": 90,
    "provider": "alibaba",
    "version": "1.0.0",
    "features": {
        "streaming": true,
        "batch": true,
        "tool_calls": true,
        "cost_estimation": true,
        "rate_limiting": true,
        "metrics": true
    }
}
```

---

## 3. 配置 Android 客户端

### 3.1 修改 NetworkModule.kt

编辑 `android-client/app/src/main/java/com/hermes/agent/di/NetworkModule.kt`：

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    // 开发环境：使用本地网络 IP
    // 注意：Android 模拟器使用 10.0.2.2 访问宿主机
    // 真机使用宿主机实际 IP（如 192.168.1.100）
    private const val DEFAULT_BASE_URL = "http://192.168.1.100:8001/"

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)  // AI 响应可能需要较长时间
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideBaseUrl(): String = DEFAULT_BASE_URL

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient, baseUrl: String): Retrofit {
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideHermesApiService(retrofit: Retrofit): HermesApiService {
        return retrofit.create(HermesApiService::class.java)
    }
}
```

### 3.2 配置 AndroidManifest.xml

确保添加网络权限：

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### 3.3 允许明文 HTTP 流量

由于服务使用 HTTP（不是 HTTPS），需要在 `AndroidManifest.xml` 中配置：

**方式 1: 使用网络安全配置**

创建 `res/xml/network_security_config.xml`：

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
</network-security-config>
```

在 `AndroidManifest.xml` 中引用：

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    android:usesCleartextTraffic="true"
    ...>
```

**方式 2: 直接在 AndroidManifest.xml 中配置**

```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

### 3.4 不同设备的 BASE_URL 配置

| 设备类型 | BASE_URL | 说明 |
|---------|----------|------|
| Android 模拟器 | `http://10.0.2.2:8001/` | 模拟器特殊地址，指向宿主机 |
| 真机（同一 WiFi） | `http://192.168.1.100:8001/` | 宿主机局域网 IP |
| 真机（不同网络） | `http://your-public-ip:8001/` | 需要公网 IP 和端口转发 |

---

## 4. 使用 Postman 测试接口

### 4.1 安装 Postman

从官网下载：https://www.postman.com/downloads/

### 4.2 创建测试集合

**Collection 名称：** Hermes-Agent API Tests

### 4.3 创建请求

#### 请求 1: Health Check

- **Method:** GET
- **URL:** `http://192.168.1.100:8001/api/v1/health`
- **预期状态码:** 200

#### 请求 2: Readiness Check

- **Method:** GET
- **URL:** `http://192.168.1.100:8001/api/v1/ready`
- **预期状态码:** 200

#### 请求 3: Chat Completion

- **Method:** POST
- **URL:** `http://192.168.1.100:8001/api/v1/chat/completions`
- **Headers:**
  - `Content-Type: application/json`
- **Body (raw JSON):**
```json
{
    "message": "你好，请介绍一下你自己",
    "max_iterations": 50
}
```
- **预期状态码:** 200

#### 请求 4: List Sessions

- **Method:** GET
- **URL:** `http://192.168.1.100:8001/api/v1/sessions?limit=10&offset=0`
- **预期状态码:** 200

#### 请求 5: Get Config

- **Method:** GET
- **URL:** `http://192.168.1.100:8001/api/v1/config`
- **预期状态码:** 200

### 4.4 使用 Postman 测试

1. 打开 Postman
2. 导入上面创建的集合
3. 逐个发送请求
4. 检查响应状态码和内容

---

## 5. 自动化测试脚本

### 5.1 Python 测试脚本

创建 `test_android_api.py`：

```python
#!/usr/bin/env python3
"""
Android 客户端 FastAPI 接口连通性测试脚本

使用方法:
    python test_android_api.py                    # 测试所有接口
    python test_android_api.py --host 192.168.1.100 --port 8001
"""

import requests
import json
import sys
import time
from typing import Optional

# 默认配置
DEFAULT_HOST = "192.168.1.100"
DEFAULT_PORT = 8001
BASE_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/api/v1"


def print_header(text: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_subheader(text: str):
    """打印子标题"""
    print(f"\n{'─' * 60}")
    print(f"  {text}")
    print(f"{'─' * 60}")


def test_health_check() -> bool:
    """测试 1: 健康检查"""
    print_subheader("测试 1: 健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码：200")
            print(f"✅ 服务状态：{data.get('status')}")
            print(f"✅ 版本：{data.get('version')}")
            print(f"✅ 运行时间：{data.get('uptime'):.0f}秒")
            print(f"✅ 活跃 Agent：{data.get('agents_active')}")
            print(f"✅ 会话数量：{data.get('sessions_count')}")
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败：无法连接到 {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_readiness_check() -> bool:
    """测试 2: 就绪检查"""
    print_subheader("测试 2: 就绪检查")
    
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码：200")
            print(f"✅ 就绪状态：{data.get('status')}")
            print(f"✅ 数据库：{data.get('database')}")
            print(f"✅ LLM 提供商：{data.get('llm_provider')}")
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_chat_completion() -> tuple[bool, Optional[str]]:
    """测试 3: 聊天接口"""
    print_subheader("测试 3: 聊天接口")
    
    try:
        payload = {
            "message": "你好，请用一句话介绍你自己",
            "max_iterations": 50
        }
        
        print(f"📤 发送请求...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            timeout=120
        )
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            
            print(f"✅ 状态码：200")
            print(f"✅ Session ID：{session_id}")
            print(f"✅ 模型：{data.get('model')}")
            print(f"✅ 完成：{data.get('completed')}")
            print(f"✅ 耗时：{data.get('duration', 0):.2f}秒")
            print(f"✅ 成本：${data.get('cost_usd', 0):.6f}")
            
            # 显示响应内容（截取前 200 字符）
            response_text = data.get('response', '')
            if len(response_text) > 200:
                response_text = response_text[:200] + "..."
            print(f"\n💬 AI 响应：{response_text}")
            
            return True, session_id
        else:
            print(f"❌ 状态码：{response.status_code}")
            print(f"❌ 错误：{response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（120 秒）")
        return False, None
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False, None


def test_session_list() -> bool:
    """测试 4: 会话列表"""
    print_subheader("测试 4: 会话列表")
    
    try:
        response = requests.get(
            f"{BASE_URL}/sessions",
            params={"limit": 10, "offset": 0},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            sessions = data.get('sessions', [])
            total = data.get('total', 0)
            
            print(f"✅ 状态码：200")
            print(f"✅ 总会话数：{total}")
            print(f"✅ 返回数量：{len(sessions)}")
            
            if sessions:
                print(f"\n📋 最近会话:")
                for i, session in enumerate(sessions[:5], 1):
                    print(f"   {i}. {session.get('session_id')} - {session.get('title', 'Untitled')}")
            
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_tools_list() -> bool:
    """测试 5: 工具列表"""
    print_subheader("测试 5: 工具列表")
    
    try:
        response = requests.get(f"{BASE_URL}/tools/list", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tools = data.get('tools', [])
            
            print(f"✅ 状态码：200")
            print(f"✅ 可用工具数：{len(tools)}")
            
            if tools:
                print(f"\n🔧 可用工具:")
                for i, tool in enumerate(tools[:10], 1):
                    print(f"   {i}. {tool.get('name', 'unknown')}")
            
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_get_config() -> bool:
    """测试 6: 获取配置"""
    print_subheader("测试 6: 获取配置")
    
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ 状态码：200")
            print(f"✅ 模型：{data.get('model')}")
            print(f"✅ 最大迭代：{data.get('max_iterations')}")
            print(f"✅ 提供商：{data.get('provider')}")
            print(f"✅ 版本：{data.get('version')}")
            
            # 显示功能特性
            features = data.get('features', {})
            if features:
                print(f"\n🔧 功能特性:")
                for key, value in features.items():
                    status = "✅" if value else "❌"
                    print(f"   {status} {key}: {value}")
            
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Android 客户端 FastAPI 接口连通性测试")
    parser.add_argument("--host", default=DEFAULT_HOST, help="服务器 IP 地址")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="服务器端口")
    args = parser.parse_args()
    
    # 更新 BASE_URL
    global BASE_URL
    BASE_URL = f"http://{args.host}:{args.port}/api/v1"
    
    print_header(f"🧪 Android 客户端 FastAPI 接口连通性测试")
    print(f"📡 服务器地址：http://{args.host}:{args.port}")
    print(f"🔗 API 基础 URL：{BASE_URL}")
    
    # 运行测试
    results = {}
    
    results["health_check"] = test_health_check()
    results["readiness_check"] = test_readiness_check()
    results["config"] = test_get_config()
    results["chat_completion"], session_id = test_chat_completion()
    
    if session_id:
        # 如果有 session_id，测试会话相关接口
        results["tools_list"] = test_tools_list()
        results["session_list"] = test_session_list()
    
    # 打印测试总结
    print_header("📊 测试总结")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Android 客户端可以正常连接 FastAPI 服务！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查服务状态和网络配置")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
```

### 5.2 运行测试脚本

```bash
# 安装依赖
pip install requests

# 使用默认配置测试
python test_android_api.py

# 指定服务器地址
python test_android_api.py --host 192.168.1.100 --port 8001
```

---

## 6. Android 模拟器网络配置

### 6.1 Android Studio 模拟器

模拟器使用特殊地址 `10.0.2.2` 访问宿主机：

```kotlin
// NetworkModule.kt
private const val DEFAULT_BASE_URL = "http://10.0.2.2:8001/"
```

### 6.2 Genymotion 模拟器

Genymotion 使用 `10.0.3.2` 访问宿主机：

```kotlin
private const val DEFAULT_BASE_URL = "http://10.0.3.2:8001/"
```

### 6.3 真机测试

确保手机和电脑在同一 WiFi 网络：

```kotlin
private const val DEFAULT_BASE_URL = "http://192.168.1.100:8001/"
```

### 6.4 防火墙配置

如果连接失败，检查防火墙：

```bash
# Ubuntu/Debian
sudo ufw allow 8001/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --reload

# 检查端口是否开放
sudo ufw status | grep 8001
```

---

## 7. 常见问题排查

### 7.1 连接超时

**症状：** `ConnectTimeoutException`

**排查步骤：**
1. 确认服务正在运行
2. 确认 IP 地址和端口正确
3. 检查防火墙设置
4. 确认设备和电脑在同一网络

```bash
# 测试端口连通性
nc -zv 192.168.1.100 8001

# 或使用 telnet
telnet 192.168.1.100 8001
```

### 7.2 连接被拒绝

**症状：** `ConnectException: Connection refused`

**可能原因：**
- 服务未启动
- 端口号错误
- 服务绑定到 127.0.0.1 而不是 0.0.0.0

**解决方法：**
```bash
# 检查服务是否监听 0.0.0.0:8001
lsof -i :8001

# 重新启动服务，确保绑定到 0.0.0.0
uvicorn fastapi_server.main:app --host 0.0.0.0 --port 8001
```

### 7.3 404 Not Found

**症状：** HTTP 404 错误

**可能原因：**
- URL 路径错误
- API 版本不匹配

**检查：**
- 正确路径：`http://192.168.1.100:8001/api/v1/chat/completions`
- 确保末尾有斜杠或不带斜杠保持一致

### 7.4 401 Unauthorized

**症状：** HTTP 401 错误

**可能原因：**
- 需要 API Key 认证
- 未配置认证头

**解决方法：**

在 NetworkModule 中添加认证拦截器：

```kotlin
@Provides
@Singleton
fun provideOkHttpClient(): OkHttpClient {
    val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    // 添加 API Key 认证
    val authInterceptor = Interceptor { chain ->
        val original = chain.request()
        val request = original.newBuilder()
            .header("X-API-Key", "your-api-key-here")
            .method(original.method, original.body())
            .build()
        chain.proceed(request)
    }

    return OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
}
```

### 7.5 500 Internal Server Error

**症状：** HTTP 500 错误

**排查步骤：**
1. 查看服务器日志
2. 检查 API Key 配置
3. 检查模型配置是否正确

```bash
# 查看服务器日志
tail -f /var/log/hermes-agent/api.log

# 或直接查看运行终端的输出
```

### 7.6 明文流量不允许

**症状：** `Cleartext HTTP traffic not permitted`

**解决方法：**

在 `AndroidManifest.xml` 中添加：

```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

---

## 8. 完整测试流程

### 8.1 自动化测试流程

```bash
#!/bin/bash
# test_android_connectivity.sh - Android 客户端连通性测试脚本

SERVER_HOST="192.168.1.100"
SERVER_PORT="8001"
BASE_URL="http://${SERVER_HOST}:${SERVER_PORT}/api/v1"

echo "============================================"
echo "  Android 客户端 FastAPI 接口连通性测试"
echo "============================================"
echo ""
echo "服务器地址：${SERVER_HOST}:${SERVER_PORT}"
echo "API 基础 URL：${BASE_URL}"
echo ""

# 测试 1: 健康检查
echo "测试 1: 健康检查"
response=$(curl -s -w "%{http_code}" ${BASE_URL}/health)
http_code=${response: -3}
if [ "$http_code" = "200" ]; then
    echo "✅ 通过 (HTTP 200)"
    echo "$response" | head -c -3 | python -m json.tool
else
    echo "❌ 失败 (HTTP ${http_code})"
fi
echo ""

# 测试 2: 就绪检查
echo "测试 2: 就绪检查"
response=$(curl -s -w "%{http_code}" ${BASE_URL}/ready)
http_code=${response: -3}
if [ "$http_code" = "200" ]; then
    echo "✅ 通过 (HTTP 200)"
    echo "$response" | head -c -3 | python -m json.tool
else
    echo "❌ 失败 (HTTP ${http_code})"
fi
echo ""

# 测试 3: 聊天接口
echo "测试 3: 聊天接口"
response=$(curl -s -w "%{http_code}" \
    -X POST ${BASE_URL}/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"message": "你好", "max_iterations": 50}')
http_code=${response: -3}
if [ "$http_code" = "200" ]; then
    echo "✅ 通过 (HTTP 200)"
    echo "$response" | head -c -3 | python -m json.tool
else
    echo "❌ 失败 (HTTP ${http_code})"
fi
echo ""

echo "============================================"
echo "  测试完成"
echo "============================================"
```

### 8.2 运行 Bash 测试脚本

```bash
chmod +x test_android_connectivity.sh
./test_android_connectivity.sh
```

---

## 总结

### 测试检查清单

- [ ] FastAPI 服务正在运行
- [ ] 服务监听 0.0.0.0:8001
- [ ] 防火墙已配置（允许 8001 端口）
- [ ] 设备和电脑在同一网络
- [ ] BASE_URL 配置正确（根据设备类型）
- [ ] 网络权限已添加（INTERNET）
- [ ] 明文流量已允许（usesCleartextTraffic）
- [ ] 所有接口测试通过

### 接口清单

| 接口 | 方法 | 路径 | 状态 |
|-----|------|------|------|
| 健康检查 | GET | `/api/v1/health` | ✅ |
| 就绪检查 | GET | `/api/v1/ready` | ✅ |
| 聊天接口 | POST | `/api/v1/chat/completions` | ✅ |
| 批量聊天 | POST | `/api/v1/chat/batch` | ✅ |
| 会话列表 | GET | `/api/v1/sessions` | ✅ |
| 会话详情 | GET | `/api/v1/sessions/{id}` | ✅ |
| 删除会话 | DELETE | `/api/v1/sessions/{id}` | ✅ |
| 工具列表 | GET | `/api/v1/tools/list` | ✅ |
| 工具详情 | GET | `/api/v1/tools/info/{name}` | ✅ |
| 配置信息 | GET | `/api/v1/config` | ✅ |

### 快速测试命令

```bash
# 一键测试所有接口
python test_android_api.py

# 或使用 curl
curl http://192.168.1.100:8001/api/v1/health && \
curl http://192.168.1.100:8001/api/v1/ready && \
curl -X POST http://192.168.1.100:8001/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

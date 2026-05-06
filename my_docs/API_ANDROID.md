# Hermes Agent API — Android App 集成指南

## 概述

Hermes Agent 提供基于 FastAPI 的 RESTful API 服务，供 Android App 等外部客户端调用 AI Agent。

## 启动服务

```bash
# 安装依赖
pip install "hermes-agent[web]"

# 启动服务
python web_server.py --host 0.0.0.0 --port 8000

# 或使用 uvicorn 直接启动
uvicorn web_server:app --host 0.0.0.0 --port 8000 --reload
```

启动后可通过以下地址访问 API 文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## API 接口清单

### 1. 健康检查

```
GET /health
```

**响应示例：**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 1234.5,
    "active_sessions": 3
}
```

---

### 2. 聊天接口

```
POST /chat
Content-Type: application/json
```

**请求体：**
```json
{
    "message": "你好，帮我写一个排序算法",
    "session_id": "my_session_123",
    "model": "qwen3.5-plus",
    "max_iterations": 50,
    "toolsets": ["coding", "web"]
}
```

**参数说明：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | ✅ | 用户消息（1-50000 字符） |
| session_id | string | ❌ | 会话 ID，不传则自动创建 |
| model | string | ❌ | 指定模型，不传使用默认配置 |
| max_iterations | int | ❌ | 最大迭代次数（1-200） |
| toolsets | string[] | ❌ | 启用的工具集列表 |

**响应示例：**
```json
{
    "session_id": "my_session_123",
    "response": "当然！这是一个 Python 快速排序实现：\n\n```python\ndef quick_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + middle + quick_sort(right)\n```",
    "api_calls": 1,
    "duration": 3.45,
    "input_tokens": 120,
    "output_tokens": 280,
    "tools_used": ["execute_code"],
    "completed": true
}
```

---

### 3. 流式聊天接口（SSE）

```
POST /chat/stream
Content-Type: application/json
Accept: text/event-stream
```

**请求体：** 与普通聊天接口相同

**响应格式（SSE）：**
```
data: {"type": "done", "session_id": "web_abc123", "response": "完整回复内容"}

```

**Android OkHttp SSE 示例：**
```kotlin
val request = Request.Builder()
    .url("http://192.168.1.100:8000/chat/stream")
    .header("Content-Type", "application/json")
    .post(
        """{
            "message": "你好",
            "session_id": "android_session"
        }""".trimIndent().toRequestBody("application/json".toMediaType())
    )
    .build()

client.newEventStream(request, object : EventSourceListener() {
    override fun onEvent(eventSource: EventSource, id: String?, type: String?, data: String) {
        val json = JSONObject(data)
        if (json.getString("type") == "done") {
            val response = json.getString("response")
            // 显示回复到 UI
        }
    }
    
    override fun onFailure(eventSource: EventSource, t: Throwable?, response: Response?) {
        Log.e("SSE", "流式请求失败", t)
    }
})
```

---

### 4. 获取会话列表

```
GET /sessions?limit=20&offset=0
```

**响应示例：**
```json
[
    {
        "session_id": "web_abc123",
        "title": "排序算法讨论",
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T11:45:00",
        "message_count": 12
    },
    {
        "session_id": "web_def456",
        "title": "天气查询",
        "created_at": "2024-01-14T09:00:00",
        "updated_at": "2024-01-14T09:05:00",
        "message_count": 3
    }
]
```

---

### 5. 获取会话详情

```
GET /sessions/{session_id}
```

**响应示例：**
```json
{
    "session_id": "web_abc123",
    "title": "排序算法讨论",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T11:45:00",
    "messages": [
        {"role": "user", "content": "帮我写一个排序算法"},
        {"role": "assistant", "content": "当然！这是快速排序实现..."},
        {"role": "user", "content": "能解释一下时间复杂度吗？"},
        {"role": "assistant", "content": "快速排序的平均时间复杂度是 O(n log n)..."}
    ],
    "usage": {
        "input_tokens": 1200,
        "output_tokens": 2800
    }
}
```

---

### 6. 删除会话

```
DELETE /sessions/{session_id}
```

**响应示例：**
```json
{
    "message": "会话 web_abc123 已删除"
}
```

---

### 7. 更新会话标题

```
POST /sessions/{session_id}/title?title=我的新标题
```

**响应示例：**
```json
{
    "message": "标题已更新",
    "title": "我的新标题"
}
```

---

### 8. 获取当前配置

```
GET /config
```

**响应示例：**
```json
{
    "model": "qwen3.5-plus",
    "max_iterations": 90,
    "provider": "dashscope",
    "version": "0.8.0"
}
```

---

## Android 集成示例代码

### Retrofit API 接口定义

```kotlin
interface HermesApiService {
    
    @GET("health")
    suspend fun healthCheck(): HealthResponse
    
    @POST("chat")
    suspend fun chat(@Body request: ChatRequest): ChatResponse
    
    @GET("sessions")
    suspend fun getSessions(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): List<SessionInfo>
    
    @GET("sessions/{sessionId}")
    suspend fun getSession(@Path("sessionId") sessionId: String): SessionDetail
    
    @DELETE("sessions/{sessionId}")
    suspend fun deleteSession(@Path("sessionId") sessionId: String): MessageResponse
    
    @POST("sessions/{sessionId}/title")
    suspend fun updateTitle(
        @Path("sessionId") sessionId: String,
        @Query("title") title: String
    ): MessageResponse
    
    @GET("config")
    suspend fun getConfig(): ConfigResponse
}

// 数据模型
data class ChatRequest(
    val message: String,
    val session_id: String? = null,
    val model: String? = null,
    val max_iterations: Int? = null,
    val toolsets: List<String>? = null
)

data class ChatResponse(
    val session_id: String,
    val response: String,
    val api_calls: Int,
    val duration: Double,
    val input_tokens: Int,
    val output_tokens: Int,
    val tools_used: List<String>,
    val completed: Boolean
)

data class SessionInfo(
    val session_id: String,
    val title: String?,
    val created_at: String?,
    val updated_at: String?,
    val message_count: Int
)

data class HealthResponse(
    val status: String,
    val version: String,
    val uptime: Double,
    val active_sessions: Int
)
```

### Retrofit 初始化

```kotlin
object ApiServiceFactory {
    private const val BASE_URL = "http://192.168.1.100:8000/"
    
    val hermesApi: HermesApiService by lazy {
        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(OkHttpClient.Builder().build())
            .build()
        retrofit.create(HermesApiService::class.java)
    }
}
```

### ViewModel 中调用

```kotlin
class ChatViewModel : ViewModel() {
    private val api = ApiServiceFactory.hermesApi
    
    val messages = MutableLiveData<List<Message>>()
    val isLoading = MutableLiveData<Boolean>()
    val sessionId = MutableLiveData<String>()
    
    fun sendMessage(content: String) {
        viewModelScope.launch {
            isLoading.value = true
            try {
                val request = ChatRequest(
                    message = content,
                    session_id = sessionId.value
                )
                val response = api.chat(request)
                
                // 保存 session_id 用于后续对话
                sessionId.value = response.session_id
                
                // 更新消息列表
                messages.value = messages.value?.plus(
                    Message("user", content),
                    Message("assistant", response.response)
                ) ?: listOf(
                    Message("user", content),
                    Message("assistant", response.response)
                )
            } catch (e: Exception) {
                // 错误处理
            } finally {
                isLoading.value = false
            }
        }
    }
}
```

---

## 网络配置

### AndroidManifest.xml

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<!-- 如果使用 HTTP 而非 HTTPS，需要配置网络安全策略 -->
<application
    android:usesCleartextTraffic="true"
    ...>
```

### 本地网络发现（可选）

如果 Agent 在局域网运行，可以使用 mDNS/Bonjour 自动发现：

```kotlin
// 使用 Android NSD API 发现服务
val nsdManager = getSystemService(Context.NSD_SERVICE) as NsdManager
```

---

## 错误处理

所有 API 错误返回统一格式：

```json
{
    "error": "内部错误",
    "detail": "具体错误信息"
}
```

**常见 HTTP 状态码：**
| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 会话不存在 |
| 500 | 服务器内部错误 |

---

## 生产环境建议

1. **认证鉴权** — 添加 API Key 或 JWT Token 认证
2. **HTTPS** — 使用 TLS 加密传输
3. **限流** — 配置请求频率限制
4. **CORS** — 限制允许的来源域名
5. **日志** — 记录所有请求用于审计
6. **负载均衡** — 多实例部署时配置负载均衡

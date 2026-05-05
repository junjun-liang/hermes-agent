# Hermes Agent — Android 客户端

基于 Jetpack Compose + Hilt + Retrofit 的 Android 聊天客户端，通过 HTTP API 与 FastAPI 后端通信。

## 项目结构

```
android-client/
├── app/
│   ├── build.gradle.kts              # 应用构建配置
│   └── src/main/java/com/hermes/agent/
│       ├── HermesApplication.kt      # Hilt 应用入口
│       ├── MainActivity.kt           # 主 Activity + 导航
│       ├── data/
│       │   ├── api/
│       │   │   └── HermesApiService.kt    # Retrofit API 接口
│       │   ├── model/
│       │   │   └── ChatModels.kt          # 数据模型
│       │   └── repository/
│       │       └── ChatRepository.kt      # 数据仓库
│       ├── di/
│       │   └── NetworkModule.kt           # Hilt 网络模块
│       ├── ui/
│       │   ├── screens/
│       │   │   ├── chat/
│       │   │   │   └── ChatScreen.kt      # 聊天界面（微信风格）
│       │   │   └── sessions/
│       │   │       └── SessionsScreen.kt  # 会话列表
│       │   ├── theme/
│       │   │   ├── Color.kt
│       │   │   ├── Theme.kt
│       │   │   └── Type.kt
│       │   └── viewmodel/
│       │       └── ChatViewModel.kt       # 聊天 ViewModel
│       └── ...
├── build.gradle.kts                  # 项目构建配置
├── settings.gradle.kts               # 项目设置
└── gradle.properties                 # Gradle 属性
```

## 技术栈

| 组件 | 库 |
|------|-----|
| UI | Jetpack Compose + Material3 |
| 架构 | MVVM + Clean Architecture |
| 依赖注入 | Hilt |
| 网络 | Retrofit + OkHttp + Gson |
| 流式响应 | OkHttp SSE |
| 异步 | Kotlin Coroutines + Flow |
| 导航 | Compose Navigation |

## 快速开始

### 1. 配置服务器地址

编辑 `data/di/NetworkModule.kt` 中的 `DEFAULT_BASE_URL`：

```kotlin
private const val DEFAULT_BASE_URL = "http://192.168.1.100:8000/"
```

### 2. 构建并运行

```bash
cd android-client

# 使用 Gradle Wrapper
./gradlew assembleDebug

# 或直接在 Android Studio 中打开项目并运行
```

## 功能特性

- ✅ 微信风格聊天界面
- ✅ 流式响应（SSE）实时显示 AI 回复
- ✅ 会话管理（创建、列表、删除）
- ✅ 历史消息加载
- ✅ 自动滚动到底部
- ✅ 加载状态指示
- ✅ 错误处理与重试

## API 接口

Android 客户端通过以下 HTTP API 与后端通信：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat` | 发送消息（同步响应） |
| POST | `/chat/stream` | 发送消息（SSE 流式响应） |
| GET | `/sessions` | 获取会话列表 |
| GET | `/sessions/{id}` | 获取会话详情 |
| DELETE | `/sessions/{id}` | 删除会话 |

## 界面预览

### 聊天界面
- 顶部标题栏显示 "Hermes Agent" 和在线状态
- 中间消息列表，用户消息绿色右对齐，AI 消息白色左对齐
- 底部输入框支持多行输入和发送按钮

### 会话列表
- 显示所有历史会话
- 支持点击进入会话、删除会话
- 右下角浮动按钮新建会话

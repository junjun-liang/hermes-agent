package com.hermes.agent.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hermes.agent.data.model.ChatMessage
import com.hermes.agent.data.model.SessionInfo
import com.hermes.agent.data.repository.ChatRepository
import com.hermes.agent.data.repository.StreamResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 聊天界面 ViewModel
 */
@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository
) : ViewModel() {

    // UI 状态
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    // 当前会话 ID
    private var currentSessionId: String? = null

    // 消息列表
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    // 是否正在加载
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    // 错误信息
    private val _error = MutableSharedFlow<String>()
    val error: SharedFlow<String> = _error.asSharedFlow()

    // 会话列表
    private val _sessions = MutableStateFlow<List<SessionInfo>>(emptyList())
    val sessions: StateFlow<List<SessionInfo>> = _sessions.asStateFlow()

    /**
     * 发送消息（流式响应）
     */
    fun sendMessage(content: String) {
        if (content.isBlank()) return

        viewModelScope.launch {
            // 添加用户消息
            val userMessage = ChatMessage(
                id = System.currentTimeMillis().toString(),
                content = content,
                isUser = true,
                timestamp = System.currentTimeMillis()
            )
            _messages.value = _messages.value + userMessage
            _isLoading.value = true

            // 添加 AI 占位消息（用于流式更新）
            val aiMessageId = (System.currentTimeMillis() + 1).toString()
            val aiMessage = ChatMessage(
                id = aiMessageId,
                content = "",
                isUser = false,
                timestamp = System.currentTimeMillis(),
                isStreaming = true
            )
            _messages.value = _messages.value + aiMessage

            // 调用流式 API
            chatRepository.sendStreamMessage(content, currentSessionId)
                .collect { result ->
                    when (result) {
                        is StreamResult.Delta -> {
                            // 更新 AI 消息内容（逐字显示）
                            updateAiMessage(aiMessageId, result.content, isStreaming = true)
                        }
                        is StreamResult.Done -> {
                            // 流式传输完成
                            currentSessionId = result.sessionId
                            updateAiMessage(aiMessageId, result.fullResponse, isStreaming = false)
                            _isLoading.value = false
                        }
                        is StreamResult.Error -> {
                            // 发生错误
                            updateAiMessage(aiMessageId, "错误: ${result.message}", isStreaming = false)
                            _isLoading.value = false
                            _error.emit(result.message)
                        }
                    }
                }
        }
    }

    /**
     * 发送消息（同步响应，备用方案）
     */
    fun sendMessageSync(content: String) {
        if (content.isBlank()) return

        viewModelScope.launch {
            // 添加用户消息
            val userMessage = ChatMessage(
                id = System.currentTimeMillis().toString(),
                content = content,
                isUser = true,
                timestamp = System.currentTimeMillis()
            )
            _messages.value = _messages.value + userMessage
            _isLoading.value = true

            // 调用同步 API
            val result = chatRepository.sendMessage(content, currentSessionId)

            result.onSuccess { response ->
                currentSessionId = response.sessionId
                val aiMessage = ChatMessage(
                    id = (System.currentTimeMillis() + 1).toString(),
                    content = response.response,
                    isUser = false,
                    timestamp = System.currentTimeMillis()
                )
                _messages.value = _messages.value + aiMessage
            }.onFailure { error ->
                val errorMessage = ChatMessage(
                    id = (System.currentTimeMillis() + 1).toString(),
                    content = "发送失败: ${error.message}",
                    isUser = false,
                    timestamp = System.currentTimeMillis()
                )
                _messages.value = _messages.value + errorMessage
                _error.emit(error.message ?: "未知错误")
            }

            _isLoading.value = false
        }
    }

    /**
     * 更新 AI 消息内容
     */
    private fun updateAiMessage(messageId: String, content: String, isStreaming: Boolean) {
        _messages.value = _messages.value.map { message ->
            if (message.id == messageId) {
                message.copy(
                    content = message.content + content,
                    isStreaming = isStreaming
                )
            } else {
                message
            }
        }
    }

    /**
     * 加载会话列表
     */
    fun loadSessions() {
        viewModelScope.launch {
            val result = chatRepository.getSessions()
            result.onSuccess { sessions ->
                _sessions.value = sessions
            }.onFailure { error ->
                _error.emit("加载会话失败: ${error.message}")
            }
        }
    }

    /**
     * 加载会话消息
     */
    fun loadSession(sessionId: String) {
        viewModelScope.launch {
            currentSessionId = sessionId
            val result = chatRepository.getSession(sessionId)
            result.onSuccess { session ->
                val messages = session.messages?.map { msg ->
                    ChatMessage(
                        id = System.currentTimeMillis().toString() + Math.random(),
                        content = msg.content,
                        isUser = msg.role == "user",
                        timestamp = System.currentTimeMillis()
                    )
                } ?: emptyList()
                _messages.value = messages
            }.onFailure { error ->
                _error.emit("加载消息失败: ${error.message}")
            }
        }
    }

    /**
     * 删除会话
     */
    fun deleteSession(sessionId: String) {
        viewModelScope.launch {
            val result = chatRepository.deleteSession(sessionId)
            result.onSuccess {
                _sessions.value = _sessions.value.filter { it.sessionId != sessionId }
                if (currentSessionId == sessionId) {
                    currentSessionId = null
                    _messages.value = emptyList()
                }
            }.onFailure { error ->
                _error.emit("删除失败: ${error.message}")
            }
        }
    }

    /**
     * 新建会话
     */
    fun newSession() {
        currentSessionId = null
        _messages.value = emptyList()
    }

    /**
     * 重试最后一条消息
     */
    fun retryLastMessage() {
        val lastUserMessage = _messages.value.lastOrNull { it.isUser }
        lastUserMessage?.let {
            // 移除最后的 AI 回复（如果有）
            val lastMessage = _messages.value.lastOrNull()
            if (lastMessage != null && !lastMessage.isUser) {
                _messages.value = _messages.value.dropLast(1)
            }
            // 重新发送
            sendMessage(it.content)
        }
    }
}

/**
 * 聊天 UI 状态
 */
data class ChatUiState(
    val isConnected: Boolean = false,
    val currentModel: String = "",
    val errorMessage: String? = null
)

/**
 * 聊天消息数据模型（UI 层）
 */
data class ChatMessage(
    val id: String,
    val content: String,
    val isUser: Boolean,
    val timestamp: Long,
    val isStreaming: Boolean = false
)

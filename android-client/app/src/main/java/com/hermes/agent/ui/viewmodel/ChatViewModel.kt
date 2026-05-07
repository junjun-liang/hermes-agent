package com.hermes.agent.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hermes.agent.data.model.SessionDetail
import com.hermes.agent.data.model.SessionInfo
import com.hermes.agent.data.repository.ChatRepository
import com.hermes.agent.data.repository.StreamResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    private var currentSessionId: String? = null

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _error = MutableSharedFlow<String>()
    val error: SharedFlow<String> = _error.asSharedFlow()

    private val _sessions = MutableStateFlow<List<SessionInfo>>(emptyList())
    val sessions: StateFlow<List<SessionInfo>> = _sessions.asStateFlow()

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected.asStateFlow()

    init {
        checkHealth()
    }

    fun sendMessage(content: String) {
        if (content.isBlank()) return

        viewModelScope.launch {
            val userMessage = ChatMessage(
                id = System.currentTimeMillis().toString(),
                content = content,
                isUser = true,
                timestamp = System.currentTimeMillis()
            )
            _messages.value = _messages.value + userMessage
            _isLoading.value = true

            val aiMessageId = (System.currentTimeMillis() + 1).toString()
            val aiMessage = ChatMessage(
                id = aiMessageId,
                content = "",
                isUser = false,
                timestamp = System.currentTimeMillis(),
                isStreaming = true
            )
            _messages.value = _messages.value + aiMessage

            val fullResponse = StringBuilder()

            chatRepository.sendStreamMessage(content, currentSessionId)
                .collect { result ->
                    when (result) {
                        is StreamResult.Delta -> {
                            fullResponse.append(result.content)
                            updateAiMessage(aiMessageId, result.content, isStreaming = true, isAppend = true)
                        }
                        is StreamResult.ToolStart -> {
                            val toolMsg = "\n🔧 调用工具: ${result.toolName}\n"
                            fullResponse.append(toolMsg)
                            updateAiMessage(aiMessageId, toolMsg, isStreaming = true, isAppend = true)
                        }
                        is StreamResult.ToolComplete -> {
                            val toolDoneMsg = "✅ 工具完成: ${result.toolName}\n"
                            fullResponse.append(toolDoneMsg)
                            updateAiMessage(aiMessageId, toolDoneMsg, isStreaming = true, isAppend = true)
                        }
                        is StreamResult.Done -> {
                            currentSessionId = result.sessionId ?: currentSessionId
                            if (result.fullResponse.isNotEmpty()) {
                                _messages.value = _messages.value.map { message ->
                                    if (message.id == aiMessageId) {
                                        message.copy(content = result.fullResponse, isStreaming = false)
                                    } else message
                                }
                            } else {
                                updateAiMessage(aiMessageId, "", isStreaming = false, isAppend = false)
                            }
                            _isLoading.value = false
                        }
                        is StreamResult.Error -> {
                            updateAiMessage(aiMessageId, "错误: ${result.message}", isStreaming = false, isAppend = false)
                            _isLoading.value = false
                            _error.emit(result.message)
                        }
                    }
                }
        }
    }

    fun sendMessageSync(content: String) {
        if (content.isBlank()) return

        viewModelScope.launch {
            val userMessage = ChatMessage(
                id = System.currentTimeMillis().toString(),
                content = content,
                isUser = true,
                timestamp = System.currentTimeMillis()
            )
            _messages.value = _messages.value + userMessage
            _isLoading.value = true

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
                _uiState.value = _uiState.value.copy(
                    currentModel = response.model,
                    isConnected = true
                )
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

    private fun updateAiMessage(messageId: String, content: String, isStreaming: Boolean, isAppend: Boolean) {
        _messages.value = _messages.value.map { message ->
            if (message.id == messageId) {
                message.copy(
                    content = if (isAppend) message.content + content else content,
                    isStreaming = isStreaming
                )
            } else {
                message
            }
        }
    }

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

    fun newSession() {
        currentSessionId = null
        _messages.value = emptyList()
    }

    fun retryLastMessage() {
        val lastUserMessage = _messages.value.lastOrNull { it.isUser }
        lastUserMessage?.let {
            val lastMessage = _messages.value.lastOrNull()
            if (lastMessage != null && !lastMessage.isUser) {
                _messages.value = _messages.value.dropLast(1)
            }
            sendMessage(it.content)
        }
    }

    private fun checkHealth() {
        viewModelScope.launch {
            val result = chatRepository.healthCheck()
            result.onSuccess {
                _isConnected.value = true
                _uiState.value = _uiState.value.copy(isConnected = true)
            }.onFailure {
                _isConnected.value = false
                _uiState.value = _uiState.value.copy(isConnected = false)
            }
        }
    }
}

data class ChatUiState(
    val isConnected: Boolean = false,
    val currentModel: String = "",
    val errorMessage: String? = null
)

data class ChatMessage(
    val id: String,
    val content: String,
    val isUser: Boolean,
    val timestamp: Long,
    val isStreaming: Boolean = false
)

package com.hermes.agent.data.repository

sealed class StreamResult {
    data class Delta(val content: String) : StreamResult()
    data class ToolStart(val toolName: String, val toolArgs: Map<String, Any>?) : StreamResult()
    data class ToolComplete(val toolName: String, val toolResult: String?) : StreamResult()
    data class Done(val sessionId: String?, val fullResponse: String) : StreamResult()
    data class Error(val message: String) : StreamResult()
}

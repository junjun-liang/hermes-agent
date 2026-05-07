package com.hermes.agent.data.repository

import com.hermes.agent.data.api.HermesApiService
import com.hermes.agent.data.api.SseClient
import com.hermes.agent.data.model.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepository @Inject constructor(
    private val apiService: HermesApiService,
    private val sseClient: SseClient
) {

    suspend fun sendMessage(
        message: String,
        sessionId: String? = null,
        model: String? = null,
        maxIterations: Int = 50,
        toolsets: List<String>? = null
    ): Result<ChatResponse> {
        return try {
            val request = ChatRequest(
                message = message,
                sessionId = sessionId,
                model = model,
                maxIterations = maxIterations,
                toolsets = toolsets
            )
            val response = apiService.createChatCompletion(request)
            Result.success(response)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun sendStreamMessage(
        message: String,
        sessionId: String? = null,
        model: String? = null,
        maxIterations: Int = 50,
        toolsets: List<String>? = null
    ): Flow<StreamResult> {
        val request = ChatRequest(
            message = message,
            sessionId = sessionId,
            model = model,
            maxIterations = maxIterations,
            toolsets = toolsets,
            stream = true
        )
        return sseClient.streamChat(request).map { chunk ->
            when (chunk.type) {
                "text" -> StreamResult.Delta(content = chunk.content ?: "")
                "tool_start" -> StreamResult.ToolStart(
                    toolName = chunk.toolName ?: "",
                    toolArgs = chunk.toolArgs
                )
                "tool_complete" -> StreamResult.ToolComplete(
                    toolName = chunk.toolName ?: "",
                    toolResult = chunk.toolResult
                )
                "done" -> StreamResult.Done(
                    sessionId = chunk.sessionId,
                    fullResponse = chunk.content ?: ""
                )
                "error" -> StreamResult.Error(
                    message = chunk.error ?: "Unknown error"
                )
                else -> StreamResult.Delta(content = chunk.content ?: "")
            }
        }
    }

    suspend fun getSessions(
        limit: Int = 20,
        offset: Int = 0
    ): Result<List<SessionInfo>> {
        return try {
            val response = apiService.listSessions(limit, offset)
            Result.success(response.sessions)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getSession(sessionId: String): Result<SessionDetail> {
        return try {
            val response = apiService.getSession(sessionId)
            Result.success(response)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun deleteSession(sessionId: String): Result<Boolean> {
        return try {
            apiService.deleteSession(sessionId)
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun healthCheck(): Result<HealthCheck> {
        return try {
            val response = apiService.healthCheck()
            Result.success(response)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getConfig(): Result<ConfigResponse> {
        return try {
            val response = apiService.getConfig()
            Result.success(response)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

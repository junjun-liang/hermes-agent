package com.hermes.agent.data.repository

import com.hermes.agent.data.api.HermesApiService
import com.hermes.agent.data.api.SseClient
import com.hermes.agent.data.model.ChatRequest
import com.hermes.agent.data.model.ChatResponse
import com.hermes.agent.data.model.HealthResponse
import com.hermes.agent.data.model.SessionDetail
import com.hermes.agent.data.model.SessionInfo
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 聊天数据仓库
 */
@Singleton
class ChatRepository @Inject constructor(
    private val apiService: HermesApiService,
    private val sseClient: SseClient
) {

    /**
     * 健康检查
     */
    suspend fun healthCheck(): Result<HealthResponse> {
        return try {
            val response = apiService.healthCheck()
            if (response.isSuccessful) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("健康检查失败: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 发送消息（非流式）
     */
    suspend fun sendMessage(
        message: String,
        sessionId: String? = null
    ): Result<ChatResponse> {
        return try {
            val request = ChatRequest(
                message = message,
                sessionId = sessionId,
                stream = false
            )
            val response = apiService.sendChatMessage(request)
            if (response.isSuccessful) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("请求失败: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 发送流式消息
     */
    fun sendStreamMessage(
        message: String,
        sessionId: String? = null
    ): Flow<StreamResult> {
        return sseClient.connectStream(message, sessionId)
    }

    /**
     * 获取会话列表
     */
    suspend fun getSessions(): Result<List<SessionInfo>> {
        return try {
            val response = apiService.getSessions()
            if (response.isSuccessful) {
                Result.success(response.body() ?: emptyList())
            } else {
                Result.failure(Exception("获取会话失败: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 获取会话详情
     */
    suspend fun getSession(sessionId: String): Result<SessionDetail> {
        return try {
            val response = apiService.getSession(sessionId)
            if (response.isSuccessful) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("获取会话详情失败: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 删除会话
     */
    suspend fun deleteSession(sessionId: String): Result<Unit> {
        return try {
            val response = apiService.deleteSession(sessionId)
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception("删除会话失败: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

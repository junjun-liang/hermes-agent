package com.hermes.agent.data.api

import com.hermes.agent.data.model.ChatRequest
import com.hermes.agent.data.model.ChatResponse
import com.hermes.agent.data.model.HealthResponse
import com.hermes.agent.data.model.SessionDetail
import com.hermes.agent.data.model.SessionInfo
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

/**
 * Hermes API 服务接口
 */
interface HermesApiService {

    /**
     * 健康检查
     */
    @GET("api/v1/health")
    suspend fun healthCheck(): Response<HealthResponse>

    /**
     * 发送聊天消息（非流式）
     */
    @POST("api/v1/chat/completions")
    suspend fun sendChatMessage(@Body request: ChatRequest): Response<ChatResponse>

    /**
     * 获取会话列表
     */
    @GET("api/v1/sessions")
    suspend fun getSessions(): Response<List<SessionInfo>>

    /**
     * 获取会话详情
     */
    @GET("api/v1/sessions/{sessionId}")
    suspend fun getSession(@Path("sessionId") sessionId: String): Response<SessionDetail>

    /**
     * 删除会话
     */
    @DELETE("api/v1/sessions/{sessionId}")
    suspend fun deleteSession(@Path("sessionId") sessionId: String): Response<Unit>
}

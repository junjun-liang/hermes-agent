package com.hermes.agent.data.api

import com.hermes.agent.data.model.*
import retrofit2.http.*

interface HermesApiService {

    @POST("api/v1/chat/completions")
    suspend fun createChatCompletion(
        @Body request: ChatRequest
    ): ChatResponse

    @POST("api/v1/chat/batch")
    suspend fun createBatchChat(
        @Body request: BatchChatRequest
    ): List<ChatResponse>

    @GET("api/v1/sessions")
    suspend fun listSessions(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): ListSessionsResponse

    @GET("api/v1/sessions/{sessionId}")
    suspend fun getSession(
        @Path("sessionId") sessionId: String
    ): SessionDetail

    @DELETE("api/v1/sessions/{sessionId}")
    suspend fun deleteSession(
        @Path("sessionId") sessionId: String
    ): Map<String, Any>

    @GET("api/v1/sessions/{sessionId}/title")
    suspend fun getSessionTitle(
        @Path("sessionId") sessionId: String
    ): Map<String, String>

    @GET("api/v1/tools/list")
    suspend fun listTools(): ToolsListResponse

    @GET("api/v1/tools/info/{toolName}")
    suspend fun getToolInfo(
        @Path("toolName") toolName: String
    ): ToolInfo

    @GET("api/v1/health")
    suspend fun healthCheck(): HealthCheck

    @GET("api/v1/ready")
    suspend fun readinessCheck(): ReadinessCheck

    @GET("api/v1/config")
    suspend fun getConfig(): ConfigResponse
}

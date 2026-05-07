package com.hermes.agent.data.model

import com.google.gson.annotations.SerializedName

data class SessionInfo(
    @SerializedName("session_id")
    val sessionId: String = "",
    val title: String? = null,
    @SerializedName("created_at")
    val createdAt: String = "",
    @SerializedName("updated_at")
    val updatedAt: String? = null,
    @SerializedName("message_count")
    val messageCount: Int = 0,
    val model: String = "",
    val platform: String = "api",
    val status: String = "active",
    @SerializedName("cost_usd")
    val costUsd: Double? = null
)

data class SessionDetail(
    @SerializedName("session_id")
    val sessionId: String = "",
    val title: String? = null,
    @SerializedName("created_at")
    val createdAt: String = "",
    @SerializedName("updated_at")
    val updatedAt: String? = null,
    @SerializedName("message_count")
    val messageCount: Int = 0,
    val model: String = "",
    val platform: String = "api",
    val status: String = "active",
    @SerializedName("cost_usd")
    val costUsd: Double? = null,
    val messages: List<SessionMessage>? = null,
    val usage: UsageInfo? = null
)

data class SessionMessage(
    val role: String = "",
    val content: String = ""
)

data class ListSessionsResponse(
    val sessions: List<SessionInfo> = emptyList(),
    val total: Int = 0,
    val limit: Int = 20,
    val offset: Int = 0
)

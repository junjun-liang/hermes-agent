package com.hermes.agent.data.model

import com.google.gson.annotations.SerializedName

data class ChatResponse(
    val id: String = "",
    val `object`: String = "chat.completion",
    val created: Long = 0,
    @SerializedName("session_id")
    val sessionId: String = "",
    val model: String = "",
    val response: String = "",
    val completed: Boolean = true,
    @SerializedName("api_calls")
    val apiCalls: Int = 0,
    val iterations: Int = 0,
    @SerializedName("tool_calls")
    val toolCalls: List<ToolCallInfo> = emptyList(),
    val usage: UsageInfo = UsageInfo(),
    @SerializedName("cost_usd")
    val costUsd: Double? = null,
    val duration: Double = 0.0,
    val metadata: Map<String, Any>? = null
)

data class ToolCallInfo(
    val name: String = "",
    val args: Map<String, Any> = emptyMap(),
    val result: String? = null,
    val success: Boolean = true,
    val error: String? = null,
    val duration: Double? = null
)

data class UsageInfo(
    @SerializedName("prompt_tokens")
    val promptTokens: Int = 0,
    @SerializedName("completion_tokens")
    val completionTokens: Int = 0,
    @SerializedName("total_tokens")
    val totalTokens: Int = 0,
    @SerializedName("cache_read_tokens")
    val cacheReadTokens: Int = 0,
    @SerializedName("cache_write_tokens")
    val cacheWriteTokens: Int = 0,
    @SerializedName("reasoning_tokens")
    val reasoningTokens: Int = 0
)

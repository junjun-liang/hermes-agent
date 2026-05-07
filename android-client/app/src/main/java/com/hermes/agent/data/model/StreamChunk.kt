package com.hermes.agent.data.model

import com.google.gson.annotations.SerializedName

data class StreamChunk(
    val type: String = "",
    val content: String? = null,
    @SerializedName("tool_name")
    val toolName: String? = null,
    @SerializedName("tool_args")
    val toolArgs: Map<String, Any>? = null,
    @SerializedName("tool_result")
    val toolResult: String? = null,
    @SerializedName("session_id")
    val sessionId: String? = null,
    val error: String? = null,
    val timestamp: Double? = null
)

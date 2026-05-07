package com.hermes.agent.data.model

import com.google.gson.annotations.SerializedName

data class ChatRequest(
    val message: String,
    @SerializedName("session_id")
    val sessionId: String? = null,
    val model: String? = null,
    @SerializedName("max_iterations")
    val maxIterations: Int = 50,
    @SerializedName("max_cost_usd")
    val maxCostUsd: Double? = null,
    val toolsets: List<String>? = null,
    @SerializedName("disabled_tools")
    val disabledTools: List<String>? = null,
    val stream: Boolean = false,
    @SerializedName("system_message")
    val systemMessage: String? = null,
    val metadata: Map<String, Any>? = null
)

data class BatchChatRequest(
    val messages: List<String>,
    @SerializedName("session_id")
    val sessionId: String? = null,
    val parallel: Boolean = false
)

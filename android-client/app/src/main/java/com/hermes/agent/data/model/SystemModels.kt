package com.hermes.agent.data.model

import com.google.gson.annotations.SerializedName

data class HealthCheck(
    val status: String = "healthy",
    val version: String = "",
    val uptime: Double = 0.0,
    @SerializedName("agents_active")
    val agentsActive: Int = 0,
    @SerializedName("sessions_count")
    val sessionsCount: Int = 0,
    val timestamp: String = ""
)

data class ReadinessCheck(
    val status: String = "ready",
    val version: String = "",
    val uptime: Double = 0.0,
    @SerializedName("agents_active")
    val agentsActive: Int = 0,
    @SerializedName("sessions_count")
    val sessionsCount: Int = 0,
    val timestamp: String = "",
    val database: String = "unknown",
    val redis: String? = null,
    @SerializedName("llm_provider")
    val llmProvider: String = "unknown"
)

data class ConfigResponse(
    val model: String = "",
    @SerializedName("max_iterations")
    val maxIterations: Int = 0,
    val provider: String = "",
    val version: String = "",
    val features: Map<String, Boolean> = emptyMap()
)

data class ErrorResponse(
    val error: String = "",
    val detail: String = "",
    @SerializedName("request_id")
    val requestId: String? = null,
    val timestamp: Long = 0
)

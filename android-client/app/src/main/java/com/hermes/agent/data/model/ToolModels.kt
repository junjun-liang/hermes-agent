package com.hermes.agent.data.model

import com.google.gson.annotations.SerializedName

data class ToolInfo(
    val name: String = "",
    val description: String = "",
    val toolset: String = "",
    val available: Boolean = true,
    @SerializedName("requires_env")
    val requiresEnv: List<String>? = null
)

data class ToolsListResponse(
    val tools: List<ToolInfo> = emptyList(),
    val toolsets: List<String> = emptyList()
)

package com.hermes.agent.data.api

import com.google.gson.Gson
import com.hermes.agent.data.model.StreamChunk
import com.hermes.agent.data.repository.StreamResult
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources

/**
 * SSE 客户端 - 用于流式聊天
 */
class SseClient(
    private val okHttpClient: OkHttpClient,
    private val baseUrl: String
) {
    private val gson = Gson()

    /**
     * 建立 SSE 流式连接
     */
    fun connectStream(
        message: String,
        sessionId: String? = null
    ): Flow<StreamResult> = callbackFlow {
        val requestBody = gson.toJson(mapOf(
            "message" to message,
            "session_id" to sessionId,
            "stream" to true
        )).toRequestBody("application/json".toMediaType())

        val request = Request.Builder()
            .url("${baseUrl}api/v1/chat/completions/stream")
            .post(requestBody)
            .header("Accept", "text/event-stream")
            .header("Cache-Control", "no-cache")
            .build()

        val listener = object : EventSourceListener() {
            override fun onOpen(eventSource: EventSource, response: okhttp3.Response) {
                // 连接打开
            }

            override fun onEvent(
                eventSource: EventSource,
                id: String?,
                type: String?,
                data: String
            ) {
                try {
                    val chunk = gson.fromJson(data, StreamChunk::class.java)
                    when (chunk.type) {
                        "text" -> {
                            trySend(StreamResult.Delta(chunk.content ?: ""))
                        }
                        "tool_start" -> {
                            trySend(StreamResult.ToolStart(chunk.toolName ?: "", chunk.toolArgs))
                        }
                        "tool_complete" -> {
                            trySend(StreamResult.ToolComplete(chunk.toolName ?: "", chunk.toolResult))
                        }
                        "done" -> {
                            trySend(StreamResult.Done(chunk.sessionId, chunk.content ?: ""))
                            close()
                        }
                        "error" -> {
                            trySend(StreamResult.Error(chunk.error ?: "未知错误"))
                            close()
                        }
                    }
                } catch (e: Exception) {
                    trySend(StreamResult.Error("解析响应失败: ${e.message}"))
                }
            }

            override fun onFailure(eventSource: EventSource, t: Throwable?, response: okhttp3.Response?) {
                trySend(StreamResult.Error("连接失败: ${t?.message}"))
                close(t)
            }

            override fun onClosed(eventSource: EventSource) {
                close()
            }
        }

        val factory = EventSources.createFactory(okHttpClient)
        val eventSource = factory.newEventSource(request, listener)

        awaitClose {
            eventSource.cancel()
        }
    }
}

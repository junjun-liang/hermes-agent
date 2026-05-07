package com.hermes.agent.data.api

import com.google.gson.Gson
import com.hermes.agent.data.model.ChatRequest
import com.hermes.agent.data.model.StreamChunk
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.*
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import okhttp3.MediaType.Companion.toMediaType
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resumeWithException

class SseClient(
    private val okHttpClient: OkHttpClient,
    private val baseUrl: String
) {

    private val gson = Gson()

    fun streamChat(request: ChatRequest): Flow<StreamChunk> = callbackFlow {
        val json = gson.toJson(request)
        val mediaType = "application/json; charset=utf-8".toMediaType()
        val requestBody = json.toRequestBody(mediaType)

        val httpRequest = Request.Builder()
            .url("${baseUrl}api/v1/chat/completions/stream")
            .post(requestBody)
            .build()

        val factory = EventSources.createFactory(okHttpClient)

        val eventSource = factory.newEventSource(httpRequest, object : EventSourceListener() {
            override fun onEvent(eventSource: EventSource, id: String?, type: String?, data: String) {
                try {
                    val chunk = gson.fromJson(data, StreamChunk::class.java)
                    trySend(chunk)
                    if (chunk.type == "done" || chunk.type == "error") {
                        close()
                    }
                } catch (e: Exception) {
                    close(e)
                }
            }

            override fun onClosed(eventSource: EventSource) {
                close()
            }

            override fun onFailure(eventSource: EventSource, t: Throwable?, response: Response?) {
                val errorMsg = t?.message ?: "SSE connection failed"
                val errorChunk = StreamChunk(
                    type = "error",
                    error = errorMsg
                )
                trySend(errorChunk)
                close(t)
            }
        })

        awaitClose {
            eventSource.cancel()
        }
    }
}

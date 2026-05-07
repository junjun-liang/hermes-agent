package com.hermes.agent.di

import com.hermes.agent.data.api.HermesApiService
import com.hermes.agent.data.api.SseClient
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    // Android 模拟器使用 10.0.2.2 访问宿主机
    // 如果是真机测试，请改为宿主机的实际 IP 地址，例如：192.168.1.100
    // 注意：FastAPI 服务运行在 8001 端口
    private const val DEFAULT_BASE_URL = "http://10.0.2.2:8001/"

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)  // AI 响应可能需要较长时间
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideBaseUrl(): String = DEFAULT_BASE_URL

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient, baseUrl: String): Retrofit {
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideHermesApiService(retrofit: Retrofit): HermesApiService {
        return retrofit.create(HermesApiService::class.java)
    }

    @Provides
    @Singleton
    fun provideSseClient(okHttpClient: OkHttpClient, baseUrl: String): SseClient {
        return SseClient(okHttpClient, baseUrl)
    }
}

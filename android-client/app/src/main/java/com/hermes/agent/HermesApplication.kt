package com.hermes.agent

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * Hermes Agent 应用入口
 */
@HiltAndroidApp
class HermesApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // 应用初始化
    }
}

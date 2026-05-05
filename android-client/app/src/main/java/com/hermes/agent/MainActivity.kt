package com.hermes.agent

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.hermes.agent.ui.screens.chat.ChatScreen
import com.hermes.agent.ui.screens.sessions.SessionsScreen
import com.hermes.agent.ui.theme.HermesTheme
import dagger.hilt.android.AndroidEntryPoint

/**
 * 主 Activity - 应用入口
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            HermesTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val navController = rememberNavController()
                    
                    NavHost(
                        navController = navController,
                        startDestination = "chat"
                    ) {
                        // 聊天界面
                        composable("chat") {
                            ChatScreen(
                                onNavigateToSessions = {
                                    navController.navigate("sessions")
                                }
                            )
                        }
                        
                        // 会话列表界面
                        composable("sessions") {
                            SessionsScreen(
                                onNavigateBack = {
                                    navController.popBackStack()
                                },
                                onSessionSelected = { sessionId ->
                                    navController.navigate("chat") {
                                        // 传递 sessionId 到聊天界面
                                        launchSingleTop = true
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}

package com.hermes.agent.ui.screens.sessions

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.hermes.agent.data.model.SessionInfo
import com.hermes.agent.ui.viewmodel.ChatViewModel
import java.text.SimpleDateFormat
import java.util.*

/**
 * 会话列表界面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SessionsScreen(
    viewModel: ChatViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit = {},
    onSessionSelected: (String) -> Unit = {}
) {
    val sessions by viewModel.sessions.collectAsStateWithLifecycle()
    
    // 加载会话列表
    LaunchedEffect(Unit) {
        viewModel.loadSessions()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("会话列表") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.Filled.ArrowBack,
                            contentDescription = "返回"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = {
                    viewModel.newSession()
                    onNavigateBack()
                },
                containerColor = MaterialTheme.colorScheme.primary
            ) {
                Text("+", style = MaterialTheme.typography.headlineMedium)
            }
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (sessions.isEmpty()) {
                EmptySessionsHint()
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(vertical = 8.dp)
                ) {
                    items(
                        items = sessions,
                        key = { it.sessionId }
                    ) { session ->
                        SessionItem(
                            session = session,
                            onClick = {
                                viewModel.loadSession(session.sessionId)
                                onSessionSelected(session.sessionId)
                            },
                            onDelete = {
                                viewModel.deleteSession(session.sessionId)
                            }
                        )
                        Divider(
                            modifier = Modifier.padding(horizontal = 16.dp),
                            color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f)
                        )
                    }
                }
            }
        }
    }
}

/**
 * 会话列表项
 */
@Composable
fun SessionItem(
    session: SessionInfo,
    onClick: () -> Unit,
    onDelete: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // 头像
        Surface(
            modifier = Modifier.size(48.dp),
            shape = MaterialTheme.shapes.medium,
            color = MaterialTheme.colorScheme.primaryContainer
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = (session.title ?: "会话").take(1).uppercase(),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }
        }

        Spacer(modifier = Modifier.width(12.dp))

        // 会话信息
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = session.title ?: "未命名会话",
                style = MaterialTheme.typography.bodyLarge,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            Spacer(modifier = Modifier.height(4.dp))
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "${session.messageCount} 条消息",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = formatDate(session.updatedAt ?: session.createdAt),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                )
            }
        }

        // 删除按钮
        IconButton(onClick = onDelete) {
            Icon(
                imageVector = Icons.Default.Delete,
                contentDescription = "删除",
                tint = MaterialTheme.colorScheme.error.copy(alpha = 0.7f)
            )
        }
    }
}

/**
 * 空状态提示
 */
@Composable
fun EmptySessionsHint() {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "暂无会话",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "点击右下角 + 开始新对话",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
        )
    }
}

/**
 * 格式化日期
 */
private fun formatDate(dateString: String?): String {
    if (dateString == null) return ""
    
    return try {
        val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
        val date = inputFormat.parse(dateString) ?: return dateString
        
        val now = Calendar.getInstance()
        val messageDate = Calendar.getInstance().apply { time = date }
        
        when {
            // 今天
            now.get(Calendar.YEAR) == messageDate.get(Calendar.YEAR) &&
            now.get(Calendar.DAY_OF_YEAR) == messageDate.get(Calendar.DAY_OF_YEAR) -> {
                SimpleDateFormat("HH:mm", Locale.getDefault()).format(date)
            }
            // 昨天
            now.get(Calendar.YEAR) == messageDate.get(Calendar.YEAR) &&
            now.get(Calendar.DAY_OF_YEAR) - messageDate.get(Calendar.DAY_OF_YEAR) == 1 -> {
                "昨天"
            }
            // 今年
            now.get(Calendar.YEAR) == messageDate.get(Calendar.YEAR) -> {
                SimpleDateFormat("MM-dd", Locale.getDefault()).format(date)
            }
            // 更早
            else -> {
                SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(date)
            }
        }
    } catch (e: Exception) {
        dateString
    }
}

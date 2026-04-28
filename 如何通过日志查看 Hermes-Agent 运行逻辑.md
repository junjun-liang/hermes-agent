# 如何通过日志查看 Hermes-Agent 运行逻辑

> 以"生成番茄钟 HTML 工具"任务为例的完整日志分析指南

## 📋 目录

1. [日志系统概览](#1-日志系统概览)
2. [查看日志的 6 种方法](#2-查看日志的 6 种方法)
3. [番茄钟任务日志分析](#3-番茄钟任务日志分析)
4. [关键日志解读](#4-关键日志解读)
5. [实战：追踪完整业务流程](#5-追踪完整业务流程)
6. [日志分析工具](#6-日志分析工具)

---

## 1. 日志系统概览

### 1.1 日志文件位置

```bash
# 主日志文件（INFO 级别及以上）
~/.hermes/logs/agent.log

# 错误日志文件（WARNING 级别及以上）
~/.hermes/logs/errors.log

# 会话日志（每个会话独立）
~/.hermes/sessions/session_<id>.log
```

### 1.2 当前配置状态

```bash
# 查看当前日志级别
grep "level:" ~/.hermes/config.yaml
# 输出：level: DEBUG  ✅ 已启用详细日志
```

### 1.3 日志格式

```
YYYY-MM-DD HH:MM:SS,mmm - LOGGER_NAME - LEVEL - 消息内容
```

**示例：**
```
2026-04-28 16:44:45,385 - agent.auxiliary_client - INFO - Auxiliary auto-detect: using main provider alibaba (glm-5)
```

---

## 2. 查看日志的 6 种方法

### 方法 1: 实时跟踪日志（推荐）

```bash
# 打开新终端，实时跟踪所有日志
tail -f ~/.hermes/logs/agent.log

# 只跟踪特定模块的日志
tail -f ~/.hermes/logs/agent.log | grep -E "run_agent|tools|file_tools"

# 高亮显示关键信息
tail -f ~/.hermes/logs/agent.log | grep --color=always -E "INFO|WARNING|ERROR|Writing|Executing"
```

### 方法 2: 使用 hermes logs 命令

```bash
# 查看最近的日志
hermes logs

# 实时跟踪
hermes logs --follow

# 查看最近 N 行
hermes logs --tail 100

# 查看错误日志
hermes logs --errors

# 组合使用
hermes logs --tail 50 --follow
```

### 方法 3: 查看特定任务的日志

```bash
# 找到最近的会话 ID
ls -lt ~/.hermes/sessions/ | head -2

# 查看该会话的完整日志
cat ~/.hermes/sessions/session_<id>.json | jq '.messages[] | select(.role="assistant")'

# 或使用 SQLite 查询
sqlite3 ~/.hermes/sessions/hermes.db "
  SELECT role, content, timestamp 
  FROM messages 
  WHERE session_id = '<id>' 
  ORDER BY timestamp;
"
```

### 方法 4: 按模块过滤日志

```bash
# 查看 run_agent.py 的日志
grep "run_agent:" ~/.hermes/logs/agent.log | tail -20

# 查看工具执行的日志
grep "tools:" ~/.hermes/logs/agent.log | tail -20

# 查看文件操作的日志
grep "file_tools:" ~/.hermes/logs/agent.log | tail -20

# 查看 API 调用
grep "API call" ~/.hermes/logs/agent.log | tail -10
```

### 方法 5: 查看错误日志

```bash
# 查看所有错误
cat ~/.hermes/logs/errors.log

# 实时跟踪错误
tail -f ~/.hermes/logs/errors.log

# 查找特定类型的错误
grep -E "Error|Exception|Failed" ~/.hermes/logs/errors.log
```

### 方法 6: 日志分析脚本

```bash
# 创建分析脚本
cat > analyze_log.sh << 'EOF'
#!/bin/bash
LOG_FILE=~/.hermes/logs/agent.log

echo "=== 日志统计 ==="
echo "总行数：$(wc -l < $LOG_FILE)"
echo "INFO: $(grep -c "INFO" $LOG_FILE)"
echo "WARNING: $(grep -c "WARNING" $LOG_FILE)"
echo "ERROR: $(grep -c "ERROR" $LOG_FILE)"
echo ""
echo "=== 最近的文件操作 ==="
grep -E "Writing|Reading|Created" $LOG_FILE | tail -5
echo ""
echo "=== 最近的工具调用 ==="
grep "Executing tool" $LOG_FILE | tail -5
EOF

chmod +x analyze_log.sh
./analyze_log.sh
```

---

## 3. 番茄钟任务日志分析

### 3.1 任务示例

用户指令：
```
生成一份番茄钟小工具的 html 代码，代码使用 single file html，
最终 html 文件保存在项目根目录
```

### 3.2 完整日志流程

当你执行这个任务时，日志会按以下顺序输出：

#### 阶段 1: 会话初始化

```log
2026-04-28 HH:MM:SS,mmm - run_agent - INFO - Loaded environment variables from /home/meizu/.hermes/.env
2026-04-28 HH:MM:SS,mmm - run_agent - INFO - Conversation turn started
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - Building system prompt with toolsets: hermes-cli
2026-04-28 HH:MM:SS,mmm - run_agent - INFO - Session created: session_abc123
```

**解读：**
- ✅ 环境变量加载成功
- ✅ 对话开始
- ✅ 工具集加载
- ✅ 会话 ID 创建

#### 阶段 2: 理解用户需求

```log
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - User message received (length: 45)
2026-04-28 HH:MM:SS,mmm - run_agent - INFO - Calling LLM: alibaba/glm-5
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - Prompt tokens: ~1500
```

**解读：**
- 📝 用户消息接收
- 🤖 开始调用 LLM
- 📊 Token 使用统计

#### 阶段 3: LLM 思考与工具调用决策

```log
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - LLM response received
2026-04-28 HH:MM:SS,mmm - run_agent - INFO - Tool calls detected: 1
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - Tool #1: write_file
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - Tool args: {"file_path": "pomodoro.html", "content": "..."}
```

**解读：**
- 💡 LLM 返回响应
- 🔧 检测到工具调用
- 📝 确定使用 `write_file` 工具
- 📋 解析工具参数

#### 阶段 4: 执行工具（写文件）

```log
2026-04-28 HH:MM:SS,mmm - tools - INFO - Executing tool: write_file
2026-04-28 HH:MM:SS,mmm - file_tools - DEBUG - Writing to: /home/meizu/Documents/my_agent_project/hermes-agent/pomodoro.html
2026-04-28 HH:MM:SS,mmm - file_tools - DEBUG - Content length: 3500 bytes
2026-04-28 HH:MM:SS,mmm - file_tools - INFO - File written successfully: pomodoro.html
2026-04-28 HH:MM:SS,mmm - tools - INFO - Tool execution completed: write_file
```

**解读：**
- 🔧 开始执行工具
- 📂 目标文件路径
- 📊 内容大小
- ✅ 文件写入成功

#### 阶段 5: 持久化会话

```log
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - Persisting session to SQLite
2026-04-28 HH:MM:SS,mmm - run_agent - INFO - Session saved: session_abc123
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - Saved trajectory to: ~/.hermes/trajectories/...
```

**解读：**
- 💾 保存到 SQLite 数据库
- ✅ 会话持久化完成
- 📈 保存训练轨迹（如果启用）

#### 阶段 6: 返回结果

```log
2026-04-28 HH:MM:SS,mmm - run_agent - INFO - Conversation turn completed
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - Total API calls: 1
2026-04-28 HH:MM:SS,mmm - run_agent - DEBUG - Total tool calls: 1
2026-04-28 HH:MM:SS,mmm - run_agent - INFO - Response sent to user
```

**解读：**
- ✅ 对话轮次完成
- 📊 统计信息
- 📤 返回结果给用户

---

## 4. 关键日志解读

### 4.1 文件操作相关日志

```bash
# 查找所有文件写入操作
grep "Writing to:" ~/.hermes/logs/agent.log

# 查找文件创建成功
grep "File written successfully" ~/.hermes/logs/agent.log

# 查找文件读取操作
grep "Reading file:" ~/.hermes/logs/agent.log

# 查找文件操作错误
grep -E "FileNotFoundError|PermissionError|IOError" ~/.hermes/logs/errors.log
```

### 4.2 工具执行相关日志

```bash
# 查看所有工具调用
grep "Executing tool:" ~/.hermes/logs/agent.log

# 查看特定工具的调用
grep "Executing tool: write_file" ~/.hermes/logs/agent.log

# 查看工具执行结果
grep "Tool execution completed" ~/.hermes/logs/agent.log

# 查看工具执行失败
grep -E "Tool.*failed|Tool.*error" ~/.hermes/logs/errors.log
```

### 4.3 API 调用相关日志

```bash
# 查看 API 调用
grep "Calling LLM:" ~/.hermes/logs/agent.log

# 查看 API 响应
grep "LLM response received" ~/.hermes/logs/agent.log

# 查看 Token 使用
grep "tokens:" ~/.hermes/logs/agent.log

# 查看 API 错误
grep -E "API.*error|Rate limit|Timeout" ~/.hermes/logs/errors.log
```

### 4.4 会话管理相关日志

```bash
# 查看会话创建
grep "Session created:" ~/.hermes/logs/agent.log

# 查看会话保存
grep "Session saved:" ~/.hermes/logs/agent.log

# 查看会话重置
grep "Session reset" ~/.hermes/logs/agent.log
```

---

## 5. 实战：追踪完整业务流程

### 5.1 启动实时监控

打开**三个终端窗口**：

**终端 1 - 运行 Hermes：**
```bash
cd /home/meizu/Documents/my_agent_project/hermes-agent
source venv/bin/activate  # 如果使用虚拟环境
hermes
```

**终端 2 - 实时跟踪日志：**
```bash
tail -f ~/.hermes/logs/agent.log | tee /tmp/hermes_log_watch.txt
```

**终端 3 - 跟踪错误：**
```bash
tail -f ~/.hermes/logs/errors.log
```

### 5.2 执行任务

在终端 1 中输入：
```
生成一份番茄钟小工具的 html 代码，代码使用 single file html，
最终 html 文件保存在项目根目录
```

### 5.3 分析日志输出

在终端 2 中，你会看到类似这样的输出：

```log
=== 终端 2 输出 ===

[时间戳] run_agent - INFO - Loaded environment variables
[时间戳] run_agent - INFO - Conversation turn started
[时间戳] run_agent - DEBUG - Building system prompt...
[时间戳] run_agent - INFO - Calling LLM: alibaba/glm-5
[时间戳] run_agent - DEBUG - Prompt tokens: ~1500
[时间戳] run_agent - DEBUG - LLM response received
[时间戳] run_agent - INFO - Tool calls detected: 1
[时间戳] run_agent - DEBUG - Tool #1: write_file
[时间戳] tools - INFO - Executing tool: write_file
[时间戳] file_tools - DEBUG - Writing to: /home/meizu/.../pomodoro.html
[时间戳] file_tools - DEBUG - Content length: 3500 bytes
[时间戳] file_tools - INFO - File written successfully: pomodoro.html
[时间戳] tools - INFO - Tool execution completed
[时间戳] run_agent - DEBUG - Persisting session to SQLite
[时间戳] run_agent - INFO - Session saved
[时间戳] run_agent - INFO - Conversation turn completed
[时间戳] run_agent - INFO - Response sent to user
```

### 5.4 验证结果

```bash
# 检查文件是否创建
ls -lh /home/meizu/Documents/my_agent_project/hermes-agent/pomodoro.html

# 查看文件内容
head -20 /home/meizu/Documents/my_agent_project/hermes-agent/pomodoro.html

# 查看会话记录
sqlite3 ~/.hermes/sessions/hermes.db "
  SELECT role, substr(content, 1, 100) 
  FROM messages 
  WHERE session_id = (
    SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1
  );
"
```

---

## 6. 日志分析工具

### 6.1 日志统计脚本

```bash
cat > log_stats.sh << 'EOF'
#!/bin/bash
LOG_FILE=~/.hermes/logs/agent.log
ERROR_LOG=~/.hermes/logs/errors.log

echo "=========================================="
echo "Hermes-Agent 日志统计"
echo "=========================================="
echo ""
echo "📊 总体统计"
echo "----------------------------------------"
echo "总行数：$(wc -l < $LOG_FILE)"
echo "INFO:   $(grep -c "INFO" $LOG_FILE)"
echo "WARNING: $(grep -c "WARNING" $LOG_FILE)"
echo "ERROR:  $(grep -c "ERROR" $LOG_FILE)"
echo "DEBUG:  $(grep -c "DEBUG" $LOG_FILE)"
echo ""
echo "🔧 工具执行统计"
echo "----------------------------------------"
echo "工具调用次数：$(grep -c "Executing tool:" $LOG_FILE)"
echo "文件写入次数：$(grep -c "Writing to:" $LOG_FILE)"
echo "文件读取次数：$(grep -c "Reading file:" $LOG_FILE)"
echo ""
echo "🤖 API 调用统计"
echo "----------------------------------------"
echo "LLM 调用次数：$(grep -c "Calling LLM:" $LOG_FILE)"
echo ""
echo "📁 最近创建的文件"
echo "----------------------------------------"
grep "File written successfully" $LOG_FILE | tail -5
echo ""
echo "⚠️  最近的错误"
echo "----------------------------------------"
tail -5 $ERROR_LOG
echo ""
echo "=========================================="
EOF

chmod +x log_stats.sh
./log_stats.sh
```

### 6.2 会话追踪脚本

```bash
cat > trace_session.sh << 'EOF'
#!/bin/bash

# 获取最近的会话 ID
SESSION_ID=$(sqlite3 ~/.hermes/sessions/hermes.db "
  SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1;
")

if [ -z "$SESSION_ID" ]; then
    echo "❌ 未找到会话记录"
    exit 1
fi

echo "=========================================="
echo "追踪会话：$SESSION_ID"
echo "=========================================="
echo ""
echo "📋 会话消息"
echo "----------------------------------------"
sqlite3 ~/.hermes/sessions/hermes.db "
  SELECT 
    CASE role
      WHEN 'user' THEN '👤 用户'
      WHEN 'assistant' THEN '🤖 Agent'
      WHEN 'tool' THEN '🔧 工具'
      ELSE role
    END as 角色，
    datetime(timestamp, 'localtime') as 时间，
    substr(content, 1, 80) as 内容摘要
  FROM messages
  WHERE session_id = '$SESSION_ID'
  ORDER BY timestamp;
"
echo ""
echo "🔧 工具调用"
echo "----------------------------------------"
sqlite3 ~/.hermes/sessions/hermes.db "
  SELECT 
    json_extract(tool_calls, '$[0].function.name') as 工具名，
    datetime(timestamp, 'localtime') as 时间
  FROM messages
  WHERE session_id = '$SESSION_ID'
    AND tool_calls IS NOT NULL;
"
echo ""
echo "=========================================="
EOF

chmod +x trace_session.sh
./trace_session.sh
```

### 6.3 文件操作监控脚本

```bash
cat > watch_file_ops.sh << 'EOF'
#!/bin/bash
LOG_FILE=~/.hermes/logs/agent.log

echo "=========================================="
echo "监控文件操作"
echo "=========================================="
echo ""
echo "📝 文件写入操作"
echo "----------------------------------------"
grep "Writing to:" $LOG_FILE | tail -10 | while read line; do
    echo "✏️  $line"
done
echo ""
echo "📖 文件读取操作"
echo "----------------------------------------"
grep "Reading file:" $LOG_FILE | tail -10 | while read line; do
    echo "📖  $line"
done
echo ""
echo "✅ 文件创建成功"
echo "----------------------------------------"
grep "File written successfully" $LOG_FILE | tail -10 | while read line; do
    echo "✅  $line"
done
echo ""
echo "=========================================="
EOF

chmod +x watch_file_ops.sh
./watch_file_ops.sh
```

---

## 📌 快速参考

### 常用日志命令

```bash
# 实时跟踪
tail -f ~/.hermes/logs/agent.log

# 查看最近 50 行
tail -n 50 ~/.hermes/logs/agent.log

# 搜索文件操作
grep -E "Writing|Reading|Created" ~/.hermes/logs/agent.log

# 搜索工具调用
grep "Executing tool" ~/.hermes/logs/agent.log

# 查看错误
cat ~/.hermes/logs/errors.log

# 使用 hermes 命令
hermes logs --follow
hermes logs --tail 100
hermes logs --errors
```

### 日志级别说明

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 详细的调试信息，如工具参数、中间状态 |
| INFO | 一般信息 | 正常的业务流程，如文件写入成功 |
| WARNING | 警告 | 可能的问题，但可继续执行 |
| ERROR | 错误 | 错误但可继续运行 |
| CRITICAL | 严重错误 | 系统崩溃，无法继续 |

### 关键日志关键词

```bash
# 文件操作
Writing to:          # 写入文件
Reading file:        # 读取文件
File written:        # 文件写入成功
File created:        # 文件创建成功

# 工具执行
Executing tool:      # 执行工具
Tool completed:      # 工具执行完成
Tool failed:         # 工具执行失败

# API 调用
Calling LLM:         # 调用 LLM
LLM response:        # LLM 响应
API error:           # API 错误

# 会话管理
Session created:     # 会话创建
Session saved:       # 会话保存
Session reset:       # 会话重置
```

---

## 🎯 总结

通过日志查看 Hermes-Agent 运行逻辑的完整流程：

1. **启用 DEBUG 日志** - 确保 `logging.level: DEBUG`
2. **实时监控** - 使用 `tail -f` 或 `hermes logs --follow`
3. **识别关键日志** - 文件操作、工具执行、API 调用
4. **分析流程** - 按照时间顺序追踪完整业务链
5. **验证结果** - 检查文件、会话记录、错误日志

**对于番茄钟任务**，重点关注：
- ✅ `write_file` 工具调用
- ✅ 文件路径和内容
- ✅ 写入成功确认
- ✅ 会话持久化

---

**文档版本**: 1.0  
**最后更新**: 2026-04-28  
**适用版本**: Hermes-Agent v2.0+

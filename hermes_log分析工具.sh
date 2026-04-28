#!/bin/bash

# Hermes-Agent 日志分析工具包
# 使用方法：./hermes_log分析工具.sh [命令]

LOG_FILE=~/.hermes/logs/agent.log
ERROR_LOG=~/.hermes/logs/errors.log

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Hermes-Agent 日志分析工具${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "用法：$0 [命令]"
    echo ""
    echo "命令:"
    echo "  stats       - 显示日志统计信息"
    echo "  tools       - 显示工具执行记录"
    echo "  files       - 显示文件操作记录"
    echo "  api         - 显示 API 调用记录"
    echo "  errors      - 显示错误日志"
    echo "  watch       - 实时监控日志"
    echo "  session     - 显示最近会话"
    echo "  pomodoro    - 追踪番茄钟任务（如果有）"
    echo ""
}

show_stats() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}📊 日志统计${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}❌ 日志文件不存在：$LOG_FILE${NC}"
        exit 1
    fi
    
    echo "日志文件：$LOG_FILE"
    echo "文件大小：$(du -h $LOG_FILE | cut -f1)"
    echo "总行数：$(wc -l < $LOG_FILE)"
    echo ""
    
    echo -e "${GREEN}日志级别统计:${NC}"
    echo "----------------------------------------"
    printf "  %-10s %s\n" "INFO:" "$(grep -c 'INFO' $LOG_FILE)"
    printf "  %-10s %s\n" "WARNING:" "$(grep -c 'WARNING' $LOG_FILE)"
    printf "  %-10s %s\n" "ERROR:" "$(grep -c 'ERROR' $LOG_FILE)"
    printf "  %-10s %s\n" "DEBUG:" "$(grep -c 'DEBUG' $LOG_FILE)"
    echo ""
    
    echo -e "${YELLOW}工具执行统计:${NC}"
    echo "----------------------------------------"
    printf "  %-20s %s\n" "工具调用:" "$(grep -c 'Executing tool:' $LOG_FILE)"
    printf "  %-20s %s\n" "文件写入:" "$(grep -c 'Writing to:' $LOG_FILE 2>/dev/null || echo 0)"
    printf "  %-20s %s\n" "文件读取:" "$(grep -c 'Reading file:' $LOG_FILE 2>/dev/null || echo 0)"
    echo ""
    
    echo -e "${BLUE}API 调用统计:${NC}"
    echo "----------------------------------------"
    printf "  %-20s %s\n" "LLM 调用:" "$(grep -c 'Calling LLM:' $LOG_FILE 2>/dev/null || echo 0)"
    echo ""
    
    echo -e "${GREEN}最近创建的文件:${NC}"
    echo "----------------------------------------"
    grep "File written successfully" $LOG_FILE 2>/dev/null | tail -5 | while read line; do
        echo "  ✅  $line"
    done
    echo ""
}

show_tools() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}🔧 工具执行记录${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}最近的工具调用:${NC}"
    grep "Executing tool:" $LOG_FILE | tail -20 | while read line; do
        echo "  🔧  $line"
    done
    echo ""
    
    echo -e "${GREEN}工具执行完成:${NC}"
    grep "Tool execution completed" $LOG_FILE | tail -10 | while read line; do
        echo "  ✅  $line"
    done
    echo ""
}

show_files() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}📁 文件操作记录${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}文件写入操作:${NC}"
    grep "Writing to:" $LOG_FILE | tail -10 | while read line; do
        echo "  ✏️  $line"
    done
    echo ""
    
    echo -e "${GREEN}文件创建成功:${NC}"
    grep "File written successfully" $LOG_FILE | tail -10 | while read line; do
        echo "  ✅  $line"
    done
    echo ""
    
    echo -e "${BLUE}文件读取操作:${NC}"
    grep "Reading file:" $LOG_FILE | tail -10 | while read line; do
        echo "  📖  $line"
    done
    echo ""
}

show_api() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}🤖 API 调用记录${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}LLM 调用:${NC}"
    grep "Calling LLM:" $LOG_FILE | tail -10 | while read line; do
        echo "  🤖  $line"
    done
    echo ""
    
    echo -e "${GREEN}LLM 响应:${NC}"
    grep "LLM response received" $LOG_FILE | tail -10 | while read line; do
        echo "  ✅  $line"
    done
    echo ""
}

show_errors() {
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}⚠️  错误日志${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    
    if [ -f "$ERROR_LOG" ]; then
        echo -e "${YELLOW}最近的错误:${NC}"
        tail -20 $ERROR_LOG
    else
        echo "错误日志文件不存在"
    fi
    echo ""
    
    echo -e "${YELLOW}主日志中的错误:${NC}"
    grep "ERROR" $LOG_FILE | tail -10 | while read line; do
        echo "  ❌  $line"
    done
    echo ""
}

watch_log() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}👁️  实时监控日志 (Ctrl+C 停止)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}❌ 日志文件不存在${NC}"
        exit 1
    fi
    
    tail -f $LOG_FILE | grep --color=always -E "INFO|WARNING|ERROR|Writing|Executing|Created"
}

show_session() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}📋 最近会话${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    if [ ! -f ~/.hermes/sessions/hermes.db ]; then
        echo "未找到会话数据库"
        exit 1
    fi
    
    SESSION_ID=$(sqlite3 ~/.hermes/sessions/hermes.db "
        SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1;
    ")
    
    if [ -z "$SESSION_ID" ]; then
        echo "未找到会话记录"
        exit 1
    fi
    
    echo "会话 ID: $SESSION_ID"
    echo ""
    
    echo -e "${YELLOW}会话消息:${NC}"
    sqlite3 ~/.hermes/sessions/hermes.db "
        SELECT 
            CASE role
                WHEN 'user' THEN '👤'
                WHEN 'assistant' THEN '🤖'
                WHEN 'tool' THEN '🔧'
                ELSE role
            END,
            datetime(timestamp, 'localtime'),
            substr(content, 1, 60)
        FROM messages
        WHERE session_id = '$SESSION_ID'
        ORDER BY timestamp;
    "
    echo ""
}

show_pomodoro() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}🍅 番茄钟任务追踪${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}搜索 pomodoro.html 相关日志:${NC}"
    grep -i "pomodoro" $LOG_FILE | tail -20
    echo ""
    
    echo -e "${YELLOW}搜索 HTML 文件创建:${NC}"
    grep -E "\.html" $LOG_FILE | tail -20
    echo ""
    
    echo -e "${YELLOW}检查文件是否存在:${NC}"
    if [ -f "/home/meizu/Documents/my_agent_project/hermes-agent/pomodoro.html" ]; then
        echo "✅ 文件存在：/home/meizu/Documents/my_agent_project/hermes-agent/pomodoro.html"
        ls -lh /home/meizu/Documents/my_agent_project/hermes-agent/pomodoro.html
    else
        echo "❌ 文件不存在"
    fi
    echo ""
}

# 主程序
case "${1:-stats}" in
    stats)
        show_stats
        ;;
    tools)
        show_tools
        ;;
    files)
        show_files
        ;;
    api)
        show_api
        ;;
    errors)
        show_errors
        ;;
    watch)
        watch_log
        ;;
    session)
        show_session
        ;;
    pomodoro)
        show_pomodoro
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ 未知命令：$1${NC}"
        show_help
        exit 1
        ;;
esac

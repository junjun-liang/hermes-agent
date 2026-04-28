#!/bin/bash
echo "=== 检查记忆 provider 日志 ==="
echo "日志文件：~/.hermes/logs/agent.log"
echo ""
echo "最近的记忆 provider 日志："
grep "Memory provider.*activated" ~/.hermes/logs/agent.log | tail -5
echo ""
echo "当前日志级别："
grep "level:" ~/.hermes/config.yaml
echo ""
echo "记忆功能状态："
grep -A 3 "memory:" ~/.hermes/config.yaml | grep "enabled"

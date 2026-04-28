#!/bin/bash

echo "=========================================="
echo "Hermes 配置文件修复验证脚本"
echo "=========================================="
echo ""

# 1. 验证 YAML 语法
echo "1️⃣  验证 YAML 语法..."
if python3 -c "import yaml; yaml.safe_load(open('/home/meizu/.hermes/config.yaml'))" 2>&1; then
    echo "✅ YAML 语法正确"
else
    echo "❌ YAML 语法错误"
    exit 1
fi
echo ""

# 2. 检查配置文件前 10 行
echo "2️⃣  检查配置文件前 10 行："
echo "----------------------------------------"
head -10 /home/meizu/.hermes/config.yaml
echo "----------------------------------------"
echo ""

# 3. 检查日志级别
echo "3️⃣  检查日志级别配置："
LOGGING_LEVEL=$(grep -A 3 "^logging:" /home/meizu/.hermes/config.yaml | grep "level:" | awk '{print $2}')
echo "   当前日志级别：$LOGGING_LEVEL"
if [ "$LOGGING_LEVEL" = "DEBUG" ]; then
    echo "   ✅ 已设置为 DEBUG，可以看到详细日志"
elif [ "$LOGGING_LEVEL" = "INFO" ]; then
    echo "   ⚠️  INFO 级别，看不到 Memory provider 等 DEBUG 日志"
    echo "   如需查看 DEBUG 日志，请运行：hermes config set logging.level DEBUG"
fi
echo ""

# 4. 检查模型配置
echo "4️⃣  检查模型配置："
MODEL=$(grep "^model:" /home/meizu/.hermes/config.yaml | head -1 | awk '{print $2}')
BASE_URL=$(grep "^base_url:" /home/meizu/.hermes/config.yaml | head -1 | awk '{print $2}')
echo "   模型：$MODEL"
echo "   Base URL: $BASE_URL"
echo ""

# 5. 检查记忆功能
echo "5️⃣  检查记忆功能配置："
MEMORY_ENABLED=$(grep -A 5 "^memory:" /home/meizu/.hermes/config.yaml | grep "memory_enabled:" | awk '{print $2}')
MEMORY_PROVIDER=$(grep -A 5 "^memory:" /home/meizu/.hermes/config.yaml | grep "provider:" | awk '{print $2}')
echo "   记忆启用：$MEMORY_ENABLED"
echo "   记忆 Provider: ${MEMORY_PROVIDER:-'(空，使用默认)'}"
echo ""

# 6. 测试 Hermes 启动
echo "6️⃣  测试 Hermes 配置加载..."
if command -v hermes &> /dev/null; then
    echo "   运行：hermes --version"
    hermes --version 2>&1 | head -3
    echo ""
    echo "   ✅ Hermes 命令可用"
else
    echo "   ⚠️  Hermes 命令不可用，请检查是否在虚拟环境中"
fi
echo ""

# 7. 显示日志文件位置
echo "7️⃣  日志文件位置："
if [ -d "/home/meizu/.hermes/logs" ]; then
    ls -lh /home/meizu/.hermes/logs/ 2>/dev/null | tail -5
else
    echo "   日志目录不存在，首次运行时会创建"
fi
echo ""

# 8. 提供查看日志的命令
echo "8️⃣  查看日志的命令："
echo "   # 实时跟踪日志"
echo "   tail -f ~/.hermes/logs/agent.log"
echo ""
echo "   # 查看 Memory provider 日志"
echo "   grep 'Memory provider' ~/.hermes/logs/agent.log"
echo ""
echo "   # 使用 hermes 命令查看"
echo "   hermes logs --follow"
echo ""

echo "=========================================="
echo "验证完成！"
echo "=========================================="
echo ""
echo "💡 提示："
echo "   - 如果要启用 DEBUG 日志，运行：hermes config set logging.level DEBUG"
echo "   - 然后运行 hermes 并查看日志：tail -f ~/.hermes/logs/agent.log"
echo "   - 看到 'Memory provider.*activated' 表示配置成功"

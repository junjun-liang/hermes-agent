# Hermes-Agent 快速参考卡

## 🚀 快速启动

```bash
cd /home/meizu/Documents/my_agent_project/hermes-agent
source venv/bin/activate
hermes
```

## 🔑 核心命令

| 任务 | 命令 |
|------|------|
| **启动 CLI** | `hermes` |
| **单次查询** | `hermes chat -q "问题"` |
| **恢复会话** | `hermes --continue` |
| **设置向导** | `hermes setup` |
| **查看配置** | `hermes config` |
| **诊断问题** | `hermes doctor` |
| **查看帮助** | `hermes --help` |

## 💬 常用斜杠命令

### 会话控制
- `/new` - 新会话
- `/undo` - 撤销
- `/retry` - 重试
- `/compress` - 压缩上下文

### 模型切换
- `/model` - 切换模型
- `/model list` - 列出模型

### 工具管理
- `/tools` - 管理工具
- `/tools list` - 列出工具

### 技能系统
- `/skills` - 浏览技能
- `/skills install <name>` - 安装技能

### 配置
- `/config` - 查看配置
- `/skin` - 切换主题
- `/yolo` - 切换 YOLO 模式

## 📁 重要路径

| 路径 | 用途 |
|------|------|
| `~/.hermes/config.yaml` | 用户配置 |
| `~/.hermes/.env` | API 密钥 |
| `~/.hermes/skills/` | 技能目录 |
| `~/.hermes/sessions.db` | 会话数据库 |
| `venv/bin/activate` | 虚拟环境 |

## 🔧 故障排除

```bash
# 1. 检查安装
hermes --version

# 2. 诊断问题
hermes doctor

# 3. 查看日志
hermes logs

# 4. 重新激活环境
source venv/bin/activate

# 5. 重新安装
pip install -e ".[all]"
```

## 📚 完整文档

- **运行指南**: [RUNNING_GUIDE.md](RUNNING_GUIDE.md)
- **官方文档**: https://hermes-agent.nousresearch.com/docs/
- **GitHub**: https://github.com/NousResearch/hermes-agent

---
**提示**: 将此文件保存为快速参考！

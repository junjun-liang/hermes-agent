---
name: minecraft-modpack-server
description: 从CurseForge/Modrinth服务器包zip设置模组Minecraft服务器。涵盖NeoForge/Forge安装、Java版本、JVM调优、防火墙、LAN配置、备份和启动脚本。
tags: [minecraft, 游戏, 服务器, neoforge, forge, modpack]
---

# Minecraft Modpack服务器设置

## 何时使用
- 用户希望从服务器包zip设置模组Minecraft服务器
- 用户需要NeoForge/Forge服务器配置帮助
- 用户询问Minecraft服务器性能调优或备份

## 首先收集用户偏好
开始设置前，询问用户：
- **服务器名称/MOTD** — 服务器列表中应显示什么？
- **种子** — 特定种子还是随机？
- **难度** — 和平/简单/普通/困难？
- **游戏模式** — 生存/创造/冒险？
- **在线模式** — true（Mojang认证，正版账户）或false（LAN/非正版友好）？
- **玩家数量** — 预计多少玩家？（影响RAM和视距调优）
- **RAM分配** — 或由智能体根据模组数量和可用RAM决定？
- **视距/模拟距离** — 或由智能体根据玩家数量和硬件选择？
- **PvP** — 开启或关闭？
- **白名单** — 开放服务器或仅白名单？
- **备份** — 需要自动备份吗？多久一次？

如果用户不关心，使用合理默认值，但生成配置前始终询问。

## 步骤

### 1. 下载并检查包
```bash
mkdir -p ~/minecraft-server
cd ~/minecraft-server
wget -O serverpack.zip "<URL>"
unzip -o serverpack.zip -d server
ls server/
```
查找：`startserver.sh`、安装器jar（neoforge/forge）、`user_jvm_args.txt`、`mods/`文件夹。
检查脚本以确定：模组加载器类型、版本和所需Java版本。

### 2. 安装Java
- Minecraft 1.21+ → Java 21：`sudo apt install openjdk-21-jre-headless`
- Minecraft 1.18-1.20 → Java 17：`sudo apt install openjdk-17-jre-headless`
- Minecraft 1.16及以下 → Java 8：`sudo apt install openjdk-8-jre-headless`
- 验证：`java -version`

### 3. 安装模组加载器
大多数服务器包包含安装脚本。使用INSTALL_ONLY环境变量仅安装不启动：
```bash
cd ~/minecraft-server/server
ATM10_INSTALL_ONLY=true bash startserver.sh
# 或通用Forge包：
# java -jar forge-*-installer.jar --installServer
```
这将下载库、修补服务器jar等。

### 4. 接受EULA
```bash
echo "eula=true" > ~/minecraft-server/server/eula.txt
```

### 5. 配置server.properties
模组/LAN的关键设置：
```properties
motd=\u00a7b\u00a7lServer Name \u00a7r\u00a78| \u00a7aModpack Name
server-port=25565
online-mode=true          # LAN无Mojang认证时为false
enforce-secure-profile=true  # 与online-mode匹配
difficulty=hard            # 大多数模组包围绕困难平衡
allow-flight=true          # 模组必需（飞行坐骑/物品）
spawn-protection=0         # 让所有人可以在出生点建造
max-tick-time=180000       # 模组需要更长的tick超时
enable-command-block=true
```

性能设置（根据硬件调整）：
```properties
# 2玩家，强力机器：
view-distance=16
simulation-distance=10

# 4-6玩家，中等机器：
view-distance=10
simulation-distance=6

# 8+玩家或较弱硬件：
view-distance=8
simulation-distance=4
```

### 6. 调优JVM参数（user_jvm_args.txt）
根据玩家数量和模组数量调整RAM。模组经验法则：
- 100-200模组：6-12GB
- 200-350+模组：12-24GB
- 为OS/其他任务至少保留8GB

```
-Xms12G
-Xmx24G
-XX:+UseG1GC
-XX:+ParallelRefProcEnabled
-XX:MaxGCPauseMillis=200
-XX:+UnlockExperimentalVMOptions
-XX:+DisableExplicitGC
-XX:+AlwaysPreTouch
-XX:G1NewSizePercent=30
-XX:G1MaxNewSizePercent=40
-XX:G1HeapRegionSize=8M
-XX:G1ReservePercent=20
-XX:G1HeapWastePercent=5
-XX:G1MixedGCCountTarget=4
-XX:InitiatingHeapOccupancyPercent=15
-XX:G1MixedGCLiveThresholdPercent=90
-XX:G1RSetUpdatingPauseTimePercent=5
-XX:SurvivorRatio=32
-XX:+PerfDisableSharedMem
-XX:MaxTenuringThreshold=1
```

### 7. 开放防火墙
```bash
sudo ufw allow 25565/tcp comment "Minecraft Server"
```
检查：`sudo ufw status | grep 25565`

### 8. 创建启动脚本
```bash
cat > ~/start-minecraft.sh << 'EOF'
#!/bin/bash
cd ~/minecraft-server/server
java @user_jvm_args.txt @libraries/net/neoforged/neoforge/<VERSION>/unix_args.txt nogui
EOF
chmod +x ~/start-minecraft.sh
```
注意：对于Forge（非NeoForge），args文件路径不同。检查`startserver.sh`获取确切路径。

### 9. 设置自动备份
创建备份脚本：
```bash
cat > ~/minecraft-server/backup.sh << 'SCRIPT'
#!/bin/bash
SERVER_DIR="$HOME/minecraft-server/server"
BACKUP_DIR="$HOME/minecraft-server/backups"
WORLD_DIR="$SERVER_DIR/world"
MAX_BACKUPS=24
mkdir -p "$BACKUP_DIR"
[ ! -d "$WORLD_DIR" ] && echo "[BACKUP] No world folder" && exit 0
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/world_${TIMESTAMP}.tar.gz"
echo "[BACKUP] Starting at $(date)"
tar -czf "$BACKUP_FILE" -C "$SERVER_DIR" world
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[BACKUP] Saved: $BACKUP_FILE ($SIZE)"
BACKUP_COUNT=$(ls -1t "$BACKUP_DIR"/world_*.tar.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    REMOVE=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -1t "$BACKUP_DIR"/world_*.tar.gz | tail -n "$REMOVE" | xargs rm -f
    echo "[BACKUP] Pruned $REMOVE old backup(s)"
fi
echo "[BACKUP] Done at $(date)"
SCRIPT
chmod +x ~/minecraft-server/backup.sh
```

添加每小时cron：
```bash
(crontab -l 2>/dev/null | grep -v "minecraft/backup.sh"; echo "0 * * * * $HOME/minecraft-server/backup.sh >> $HOME/minecraft-server/backups/backup.log 2>&1") | crontab -
```

## 常见陷阱
- 模组始终设置`allow-flight=true` — 带喷气背包/飞行的模组否则会踢出玩家
- `max-tick-time=180000`或更高 — 模组服务器在世界生成期间常有长tick
- 首次启动很慢（大包需要几分钟）— 不要惊慌
- 首次启动时"Can't keep up!"警告是正常的，初始区块生成后会稳定
- 如果online-mode=false，也设置enforce-secure-profile=false否则客户端会被拒绝
- 包的startserver.sh通常有自动重启循环 — 创建不带它的干净启动脚本
- 删除world/文件夹以用新种子重新生成
- 某些包有环境变量控制行为（例如ATM10使用ATM10_JAVA、ATM10_RESTART、ATM10_INSTALL_ONLY）

## 验证
- `pgrep -fa neoforge`或`pgrep -fa minecraft`检查是否运行
- 检查日志：`tail -f ~/minecraft-server/server/logs/latest.log`
- 在日志中查找"Done (Xs)!" = 服务器就绪
- 测试连接：玩家在多人游戏中添加服务器IP

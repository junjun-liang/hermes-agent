# 番茄钟小工具需求规格文档

## 一、功能需求清单

### 1.1 必须有功能（核心功能）

| 编号 | 功能名称 | 功能描述 | 优先级 |
|------|----------|----------|--------|
| F01 | 计时器 | 25分钟专注倒计时，精确到秒 | P0 |
| F02 | 短休息 | 5分钟短休息倒计时 | P0 |
| F03 | 长休息 | 15分钟长休息倒计时 | P0 |
| F04 | 开始/暂停 | 控制计时器的启动和暂停 | P0 |
| F05 | 重置 | 重置当前计时器 | P0 |
| F06 | 状态切换 | 专注→短休息→专注...，每4个番茄钟后长休息 | P0 |
| F07 | 计数统计 | 显示当前完成的番茄钟数量 | P0 |
| F08 | 视觉反馈 | 清晰显示当前状态（专注/短休息/长休息） | P0 |

### 1.2 可选功能（增强体验）

| 编号 | 功能名称 | 功能描述 | 优先级 |
|------|----------|----------|--------|
| F09 | 声音提醒 | 计时结束时播放提示音 | P1 |
| F10 | 时间自定义 | 允许用户自定义专注/休息时长 | P1 |
| F11 | 进度环 | 圆形进度条可视化剩余时间 | P1 |
| F12 | 暗色模式 | 支持明暗主题切换 | P2 |
| F13 | 本地存储 | 保存番茄钟完成记录（localStorage） | P2 |
| F14 | 今日统计 | 显示今日完成的番茄钟总数 | P2 |
| F15 | 浏览器通知 | 计时结束时发送系统通知 | P2 |

---

## 二、UI/UX 设计建议

### 2.1 整体布局

```
+------------------------------------------+
|              [番茄钟图标/标题]              |
+------------------------------------------+
|                                          |
|           ┌────────────────┐             |
|           │   25:00       │             |
|           │  [进度环]      │             |
|           │   专注中      │             |
|           └────────────────┘             |
|                                          |
|     [开始]  [暂停]  [重置]  [跳过]        |
|                                          |
+------------------------------------------+
|  已完成: ●●●○  (3/4 后长休息)             |
+------------------------------------------+
|  今日统计: 6 个番茄钟                      |
+------------------------------------------+
```

### 2.2 配色方案

| 状态 | 主色 | 含义 |
|------|------|------|
| 专注 | #E74C3C (红色) | 紧迫、专注 |
| 短休息 | #27AE60 (绿色) | 放松、恢复 |
| 长休息 | #3498DB (蓝色) | 深度放松 |

### 2.3 视觉元素

1. **进度环**：使用 Canvas 或 SVG 绘制环形进度条
   - 显示剩余时间百分比
   - 颜色随状态变化
   - 动画过渡效果

2. **时间显示**：
   - 大字体居中显示（建议 48-72px）
   - 格式：MM:SS

3. **状态指示**：
   - 文字标签明确当前状态
   - 背景色随状态微调

4. **控制按钮**：
   - 扁平化设计
   - 悬停状态反馈
   - 图标+文字组合

---

## 三、交互流程说明

### 3.1 基本使用流程

```
开始
  │
  ▼
[点击"开始"] → 专注计时(25分钟)
  │                    │
  │                    ▼ (计时结束)
  │              [声音/通知提醒]
  │                    │
  │                    ▼
  │              完成计数+1
  │                    │
  │                    ▼
  │         ┌──────────┴──────────┐
  │         │                     │
  │         ▼                     ▼
  │   (计数%4==0)            (计数%4!=0)
  │    长休息15min            短休息5min
  │         │                     │
  │         └──────────┬──────────┘
  │                    │
  │                    ▼
  │              [自动/手动开始下一轮]
  │                    │
  └────────────────────┘
```

### 3.2 状态机模型

```
┌─────────┐    开始    ┌─────────┐
│  空闲   │ ─────────→ │  专注   │
└─────────┘            └─────────┘
     ↑                      │
     │                      │ 完成
     │ 重置                 ▼
     │               ┌─────────────┐
     │    ┌─────────→│   休息中    │←────────┐
     │    │          └─────────────┘         │
     │    │ 跳过休息          │               │ 跳过休息
     │    │                   │ 完成         │
     │    │                   ▼               │
     │    │          ┌─────────────┐          │
     └────┼──────────│  下一轮     │──────────┘
          │          └─────────────┘
          │                   │
          └───────────────────┘
```

### 3.3 用户操作说明

| 操作 | 效果 |
|------|------|
| 点击"开始" | 启动专注计时器 |
| 点击"暂停" | 暂停当前计时，保留剩余时间 |
| 点击"重置" | 重置到当前阶段的初始状态 |
| 点击"跳过" | 跳过当前休息阶段，进入下一轮专注 |

---

## 四、技术实现要点

### 4.1 技术约束

| 约束项 | 说明 |
|--------|------|
| 文件格式 | 单文件 HTML |
| CSS 方式 | 内联 `<style>` 标签 |
| JavaScript | 内联 `<script>` 标签 |
| 外部依赖 | 无（纯原生实现） |
| 浏览器兼容 | 现代浏览器（Chrome/Firefox/Safari/Edge） |

### 4.2 核心技术实现

#### 4.2.1 计时器实现

```javascript
// 使用 setInterval 实现，每秒更新
let timer = null;
let remainingTime = 25 * 60; // 秒

function startTimer() {
  timer = setInterval(() => {
    remainingTime--;
    updateDisplay();
    if (remainingTime <= 0) {
      clearInterval(timer);
      onTimerComplete();
    }
  }, 1000);
}
```

#### 4.2.2 进度环实现（Canvas）

```javascript
// Canvas 绘制环形进度条
function drawProgressRing(progress) {
  const ctx = canvas.getContext('2d');
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const radius = 90;
  
  // 背景环
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
  ctx.strokeStyle = '#e0e0e0';
  ctx.lineWidth = 8;
  ctx.stroke();
  
  // 进度环
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, -Math.PI/2, 
          -Math.PI/2 + 2 * Math.PI * progress);
  ctx.strokeStyle = '#E74C3C'; // 根据状态变化
  ctx.lineWidth = 8;
  ctx.stroke();
}
```

#### 4.2.3 状态管理

```javascript
const STATES = {
  FOCUS: { duration: 25 * 60, color: '#E74C3C', label: '专注中' },
  SHORT_BREAK: { duration: 5 * 60, color: '#27AE60', label: '短休息' },
  LONG_BREAK: { duration: 15 * 60, color: '#3498DB', label: '长休息' }
};

let currentState = STATES.FOCUS;
let completedPomodoros = 0;

function getNextState() {
  if (currentState === STATES.FOCUS) {
    completedPomodoros++;
    return (completedPomodoros % 4 === 0) 
      ? STATES.LONG_BREAK 
      : STATES.SHORT_BREAK;
  }
  return STATES.FOCUS;
}
```

### 4.3 localStorage 存储（可选）

```javascript
// 保存今日统计
function saveDailyStats(count) {
  const today = new Date().toDateString();
  localStorage.setItem('pomodoro_date', today);
  localStorage.setItem('pomodoro_count', count);
}

// 读取今日统计
function loadDailyStats() {
  const today = new Date().toDateString();
  const savedDate = localStorage.getItem('pomodoro_date');
  if (savedDate === today) {
    return parseInt(localStorage.getItem('pomodoro_count')) || 0;
  }
  return 0;
}
```

### 4.4 声音提示（可选）

```javascript
// 使用 Web Audio API 生成提示音
function playNotificationSound() {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();
  
  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);
  
  oscillator.frequency.value = 800;
  oscillator.type = 'sine';
  gainNode.gain.value = 0.3;
  
  oscillator.start();
  oscillator.stop(audioContext.currentTime + 0.5);
}
```

---

## 五、文件结构

```
pomodoro.html
├── <!DOCTYPE html>
├── <html>
│   ├── <head>
│   │   ├── <meta charset="UTF-8">
│   │   ├── <meta name="viewport" content="width=device-width, initial-scale=1.0">
│   │   ├── <title>番茄钟</title>
│   │   └── <style>
│   │       └── /* 所有 CSS 样式 */
│   │
│   └── <body>
│       ├── <div class="container">
│       │   ├── <!-- 计时器显示区域 -->
│       │   ├── <!-- 控制按钮 -->
│       │   └── <!-- 统计信息 -->
│       └── <script>
│           └── /* 所有 JavaScript 代码 */
```

---

## 六、验收标准

### 6.1 功能验收

- [ ] 25分钟专注计时准确无误
- [ ] 5分钟短休息计时准确无误
- [ ] 15分钟长休息计时准确无误
- [ ] 每4个番茄钟后正确切换到长休息
- [ ] 开始/暂停/重置功能正常
- [ ] 计数统计准确显示

### 6.2 UI 验收

- [ ] 界面简洁美观，无冗余元素
- [ ] 进度环动画流畅
- [ ] 按钮交互反馈明确
- [ ] 不同状态颜色区分明显

### 6.3 技术验收

- [ ] 单文件 HTML，无外部依赖
- [ ] 代码结构清晰，有适当注释
- [ ] 兼容主流浏览器
- [ ] 页面加载速度正常

---

## 七、开发计划

| 阶段 | 内容 | 预计时间 |
|------|------|----------|
| 第一阶段 | 基础计时器 + UI框架 | 核心功能 |
| 第二阶段 | 状态切换 + 计数统计 | 完整流程 |
| 第三阶段 | 进度环 + 动画效果 | 视觉优化 |
| 第四阶段 | 声音提醒 + 本地存储 | 增强功能 |

---

文档版本：v1.0
创建日期：2026-04-29
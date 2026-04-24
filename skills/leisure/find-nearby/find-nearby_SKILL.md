---
name: find-nearby
description: 使用OpenStreetMap查找附近场所（餐厅、咖啡馆、酒吧、药店等）。适用于坐标、地址、城市、邮编或Telegram位置标记。无需API密钥。
version: 1.0.0
metadata:
  hermes:
    tags: [位置, 地图, 附近, 场所, 餐厅, 本地]
    related_skills: []
---

# Find Nearby — 本地场所发现

查找任何位置附近的餐厅、咖啡馆、酒吧、药店等场所。使用OpenStreetMap（免费，无需API密钥）。适用于：

- **Telegram位置标记的坐标**（对话中的纬度/经度）
- **地址**（"near 123 Main St, Springfield"）
- **城市**（"restaurants in downtown Austin"）
- **邮编**（"pharmacies near 90210"）
- **地标**（"cafes near Times Square"）

## 快速参考

```bash
# 通过坐标（来自Telegram位置标记或用户提供）
python3 SKILL_DIR/scripts/find_nearby.py --lat <LAT> --lon <LON> --type restaurant --radius 1500

# 通过地址、城市或地标（自动地理编码）
python3 SKILL_DIR/scripts/find_nearby.py --near "Times Square, New York" --type cafe

# 多种场所类型
python3 SKILL_DIR/scripts/find_nearby.py --near "downtown austin" --type restaurant --type bar --limit 10

# JSON输出
python3 SKILL_DIR/scripts/find_nearby.py --near "90210" --type pharmacy --json
```

### 参数

| 标志 | 描述 | 默认值 |
|------|------|---------|
| `--lat`, `--lon` | 精确坐标 | — |
| `--near` | 地址、城市、邮编或地标（地理编码） | — |
| `--type` | 场所类型（可重复用于多个） | restaurant |
| `--radius` | 搜索半径（米） | 1500 |
| `--limit` | 最大结果数 | 15 |
| `--json` | 机器可读JSON输出 | 关闭 |

### 常用场所类型

`restaurant`（餐厅）、`cafe`（咖啡馆）、`bar`（酒吧）、`pub`（酒馆）、`fast_food`（快餐）、`pharmacy`（药店）、`hospital`（医院）、`bank`（银行）、`atm`（ATM）、`fuel`（加油站）、`parking`（停车场）、`supermarket`（超市）、`convenience`（便利店）、`hotel`（酒店）

## 工作流程

1. **获取位置。** 查找Telegram标记的坐标（`latitude: ... / longitude: ...`），或询问用户地址/城市/邮编。

2. **询问偏好**（仅在未说明时）：场所类型、愿意走多远、任何具体要求（菜系、"现在营业"等）。

3. **使用适当标志运行脚本。** 如果需要程序化处理结果，使用`--json`。

4. **展示结果**，包含名称、距离和Google Maps链接。如果用户询问营业时间或"现在营业"，检查结果中的`hours`字段 — 如果缺失或不明确，使用`web_search`验证。

5. **获取导航**，使用结果中的`directions_url`，或构建：`https://www.google.com/maps/dir/?api=1&origin=<LAT>,<LON>&destination=<LAT>,<LON>`

## 提示

- 如果结果稀疏，扩大半径（1500 → 3000米）
- 对于"现在营业"请求：检查结果中的`hours`字段，与`web_search`交叉引用确保准确性，因为OSM营业时间不一定完整
- 仅邮编在全球范围内可能模糊 — 如果结果看起来不对，提示用户提供国家/州
- 脚本使用OpenStreetMap数据，由社区维护；覆盖范围因地区而异

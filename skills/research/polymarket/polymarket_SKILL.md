---
name: polymarket
description: 查询 Polymarket 预测市场数据——搜索市场、获取价格、订单簿和价格历史。通过公共 REST API 只读，无需 API 密钥。
version: 1.0.0
author: Hermes Agent + Teknium
tags: [polymarket, 预测市场, 市场数据, 交易]
---

# Polymarket — 预测市场数据

使用 Polymarket 的公共 REST API 查询预测市场数据。
所有端点都是只读的，无需任何身份验证。

完整的端点参考和 curl 示例参见 `references/api-endpoints.md`。

## 何时使用

- 用户询问预测市场、赔率或事件概率
- 用户想知道"X 发生的几率是多少？"
- 用户专门询问 Polymarket
- 用户需要市场价格、订单簿数据或价格历史
- 用户要求监控或跟踪预测市场动态

## 关键概念

- **事件** 包含一个或多个 **市场**（1对多关系）
- **市场** 是具有 Yes/No 价格的二元结果，价格在 0.00 到 1.00 之间
- 价格就是概率：价格 0.65 意味着市场认为 65% 可能
- `outcomePrices` 字段：JSON 编码的数组，如 `["0.80", "0.20"]`
- `clobTokenIds` 字段：两个 token ID [Yes, No] 的 JSON 编码数组，用于价格/订单簿查询
- `conditionId` 字段：用于价格历史查询的十六进制字符串
- 交易量以 USDC（美元）计

## 三个公共 API

1. **Gamma API** 位于 `gamma-api.polymarket.com`——发现、搜索、浏览
2. **CLOB API** 位于 `clob.polymarket.com`——实时价格、订单簿、历史
3. **Data API** 位于 `data-api.polymarket.com`——交易、未平仓合约

## 典型工作流

当用户询问预测市场赔率时：

1. **搜索** 使用 Gamma API 公共搜索端点配合用户查询
2. **解析** 响应——提取事件及其嵌套市场
3. **呈现** 市场问题、当前价格（百分比形式）和交易量
4. **深入** 如被要求——使用 clobTokenIds 查询订单簿，conditionId 查询历史

## 呈现结果

将价格格式化为百分比以提高可读性：
- outcomePrices `["0.652", "0.348"]` 变为 "Yes: 65.2%, No: 34.8%"
- 始终显示市场问题和概率
- 包含可用的交易量

示例：`"X 会发生吗？" — 65.2% Yes（交易量 $1.2M）`

## 解析双重编码字段

Gamma API 将 `outcomePrices`、`outcomes` 和 `clobTokenIds` 作为 JSON 响应内的 JSON 字符串返回（双重编码）。使用 Python 处理时，用 `json.loads(market['outcomePrices'])` 解析以获取实际数组。

## 速率限制

非常宽松——正常使用不太可能触及：
- Gamma：每 10 秒 4,000 次请求（通用）
- CLOB：每 10 秒 9,000 次请求（通用）
- Data：每 10 秒 1,000 次请求（通用）

## 限制

- 本技能只读——不支持下单交易
- 交易需要基于钱包的加密身份验证（EIP-712 签名）
- 一些新市场可能没有价格历史
- 交易有地理限制，但只读数据全球可访问

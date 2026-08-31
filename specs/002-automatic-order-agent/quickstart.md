# Quickstart: 自动接单订单智能体

## Prerequisites

- Python 3.11+、Node.js 及现有项目依赖已安装。
- 使用项目现有的模拟商品、库存和价格种子数据。

## Run targeted validation

```powershell
pytest backend/tests/unit backend/tests/contract backend/tests/security -q
pytest backend/tests/integration -q
```

若实现了前端订单队列，再运行：

```powershell
Set-Location frontend
npm run typecheck
```

## End-to-end scenarios

1. **全量满足**：提交包含唯一商品、数量、地址和交付日期的邮件；预期生成 `READY_FOR_CONFIRMATION` 草稿，库存和价格均有观察时间。
2. **部分满足**：提交两个商品，其中一个库存不足；预期逐项显示可供数量和缺口，草稿不得写“全部有货”。
3. **信息缺失**：缺少地址或数量；预期只询问缺失字段，不能发送确认。
4. **歧义商品**：使用可匹配多个规格的商品名；预期 `AMBIGUOUS_PRODUCT`，不能猜 SKU。
5. **安全发送**：未确认时调用发送接口；预期 `CONFIRMATION_REQUIRED`。确认当前版本后发送一次，重复请求返回相同结果。
6. **失效与异常**：人工修改数量后使用旧版本确认，或模拟发送未知结果；预期分别返回 `VERSION_STALE` 和 `UNKNOWN`，不得显示成功。

## Acceptance mapping

- SC-001：订单解析固定场景和多商品遗漏断言。
- SC-002：库存逐项事实断言与不可用数据断言。
- SC-003：端到端草稿耗时和成功率统计。
- SC-004/SC-005：确认门禁、版本校验和幂等发送测试。
- SC-006：由前端冒烟测试记录操作员完成主流程时间和完成率。

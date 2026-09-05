# Data Model: 核心 Agent 架构收敛

## SemanticAction

| Field | Type | Rule |
|---|---|---|
| intent | string | 语义意图，不要求等于内部 Goal 枚举 |
| target | object | PRODUCT、REFERENCE、CATEGORY、MULTIPLE、NONE |
| operation | enum | SELECT、ADD、REMOVE、SET_QUANTITY、REPLACE、KEEP、REQUOTE、ASK_INFORMATION、CORRECT |
| quantity | integer/null | 必须大于 0；自然语言数字由适配层归一化 |
| constraints | object | 当前轮明确表达的约束 |
| context_relation | enum | CONTINUE、MODIFY、NEW_TOPIC、CORRECTION |
| confidence | number | 0 到 1 |

## ResolvedReference

```json
{
  "status": "RESOLVED",
  "product_ids": ["SKU021"],
  "source": "CURRENT_CANDIDATES",
  "confidence": 0.98,
  "ambiguous_candidates": []
}
```

`AMBIGUOUS` 和 `UNRESOLVED` 不允许执行状态变更或工具调用。

## ExecutionDecision

```json
{
  "kind": "TOOL_CALL",
  "action": "CALCULATE_QUOTE",
  "tool_name": "calculate_order_quote",
  "arguments": {},
  "requires_confirmation": false,
  "reason_code": "QUOTE_REQUIRED"
}
```

`kind` 可为 `STATE_MUTATION`、`TOOL_CALL`、`ASK_USER`、`HANDOFF` 或 `NOOP`。

## BusinessState boundaries

```text
reference_context       # 当前可引用候选集
focused_product         # 当前对话焦点，不等于购买选择
selected_products       # 用户明确选择的商品
quote_context           # 可重算的完整报价输入和结果
recommendation_context  # 推荐约束、候选和排除项
goal_context            # 仅长事务目标
active_domain           # COMMERCE、AFTER_SALES 或 UNKNOWN
execution_mode          # AUTO、WAITING_USER、WAITING_CONFIRMATION、HUMAN_HANDOFF
handoff_state           # 人工接管原因、脱敏上下文、待处理事项和生命周期
```

Invariant：浏览或推荐只更新 `reference_context`；明确选择才更新 `selected_products`；报价始终从 `quote_context.items` 重算。

Invariant：`HUMAN_HANDOFF` 只能写入 `execution_mode`；不得写入 `active_domain` 或创建 HUMAN AgentTask。

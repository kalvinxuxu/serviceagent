# Data Model: 自动接单订单智能体

## OrderEmail

- `email_id`: 唯一来源标识，用于重复检测
- `sender`, `subject`, `body`, `attachment_refs`: 来源内容；展示时脱敏
- `received_at`: 接收时间
- `classification`: `ORDER`, `NON_ORDER`, `NEEDS_REVIEW`
- `processing_status`: `RECEIVED`, `PARSED`, `DRAFTED`, `FAILED`, `DUPLICATE`

## OrderDraft

- `draft_id`, `email_id`, `version`
- `customer`: 客户标识和可展示名称
- `items`: 订单项集合
- `delivery`: 日期、地址、方式和缺失字段
- `currency`, `notes`, `missing_information`, `conflicts`
- `status`: `NEEDS_CLARIFICATION`, `READY_FOR_CHECK`, `CHECKED`, `READY_FOR_CONFIRMATION`, `SENT`, `HANDOFF`

## OrderItem

- `item_id`, `raw_description`, `product_id`, `product_name`, `variant`
- `requested_quantity`, `unit`
- `match_status`: `MATCHED`, `AMBIGUOUS`, `NOT_FOUND`
- `source_span` 或来源说明、字段置信状态

## InventoryCheck

- `item_id`, `requested_quantity`, `available_quantity`
- `fulfillment_status`: `FULFILLABLE`, `PARTIAL`, `OUT_OF_STOCK`, `UNKNOWN`
- `unit_price`, `currency`, `observed_at`, `reason`

## ReplyDraft

- `reply_id`, `draft_id`, `draft_version`
- `recipient`, `subject`, `body`, `fact_snapshot`
- `status`: `DRAFT`, `CONFIRMED`, `SENDING`, `SENT`, `FAILED`, `UNKNOWN`

## ConfirmationRecord / SendRecord

- `confirmation_id`, `reply_id`, `confirmed_by`, `confirmed_at`, `confirmed_version`
- `idempotency_key`, `attempted_at`, `provider_message_id`, `result`, `error_code`
- 状态转换：`DRAFT → CONFIRMED → SENDING → SENT|FAILED|UNKNOWN`；版本变化或人工撤销使确认失效。

## TraceEvent

- `trace_id`, `email_id`, `draft_id`, `event_type`, `component`, `schema_version`
- `occurred_at`, `status`, `reason_code`, `redacted_context`
- 记录解析、匹配、库存、草稿、人工修改、确认、发送和异常；不得保存不必要的完整敏感正文。

## Invariants

1. `SENT` 必须存在同版本 `CONFIRMED`，且拥有幂等键。
2. 商品匹配不是 `MATCHED` 时，不得生成可承诺的库存/价格结论。
3. 人工修改商品、数量或交付信息后，旧核验和确认均失效。
4. `UNKNOWN` 发送结果不得被转换为 `SENT`，只能人工核查或安全重试。

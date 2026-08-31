# API Contract: 自动接单订单智能体

## `POST /api/v1/order-emails`

接入一封模拟客户邮件并启动解析。

Request:

```json
{"email_id":"mail_001","sender":"buyer@example.test","subject":"明天订货","body":"原味贝果20个，明天下午送到公司"}
```

Response:

```json
{"email_id":"mail_001","draft_id":"od_001","status":"READY_FOR_CHECK","missing_information":["delivery.address"]}
```

重复 `email_id` 必须返回已有草稿及 `DUPLICATE` 或当前处理状态，不创建第二份订单。

## `GET /api/v1/order-drafts/{draft_id}`

返回订单草稿、逐项匹配状态、库存核验、回复草稿、当前版本、缺失信息和 Trace 摘要。

## `POST /api/v1/order-drafts/{draft_id}/check`

对当前版本执行目录匹配、库存和价格核验。返回逐项状态；任何未知结果必须包含 `reason` 和 `observed_at`。

## `PATCH /api/v1/order-drafts/{draft_id}`

人工修改允许的订单字段。成功修改后版本号递增，受影响的核验和确认失效。

## `POST /api/v1/reply-drafts/{reply_id}/confirm`

Request:

```json
{"draft_version":3,"confirmed_by":"operator_001","idempotency_key":"mail_001-v3"}
```

只有当前草稿版本、已完成必要核验且收件人明确时才接受确认；版本不一致返回 `VERSION_STALE`。

## `POST /api/v1/reply-drafts/{reply_id}/send`

仅允许发送已确认的当前版本。重复幂等键返回原发送结果；失败返回 `FAILED`，结果未知返回 `UNKNOWN`，两者均不得伪装为 `SENT`。

## Common Result

```json
{"ok":true,"data":{},"reason":null,"observed_at":"2026-08-31T10:00:00Z","schema_version":"1.0"}
```

失败原因至少包括 `INVALID_INPUT`、`AMBIGUOUS_PRODUCT`、`MISSING_INFORMATION`、`INVENTORY_UNAVAILABLE`、`CONFIRMATION_REQUIRED`、`VERSION_STALE`、`DUPLICATE` 和 `SEND_UNKNOWN`。

## Planner and Component Rules

- Planner 只能输出版本化 JSON/Pydantic 动作：`PARSE_EMAIL`、`CHECK_ORDER`、`ASK_USER`、`GENERATE_DRAFT`、`ASK_CONFIRMATION`、`SEND_REPLY`、`HANDOFF`。订单字段状态必须使用 `KNOWN`、`MISSING`、`AMBIGUOUS` 或 `LOW_CONFIDENCE`，并携带 `source`；冲突字段必须输出 `conflicts[]`，不得静默覆盖。
- 未通过 Schema 校验的动作不得调用工具。
- `SEND_REPLY` 必须携带当前 `reply_id`、草稿版本、确认记录和幂等键；缺少任何一项都停止执行。
- 解析器、目录匹配、库存/价格、草稿生成和发送适配器均返回稳定成功/失败结构，不暴露内部数据库模型。

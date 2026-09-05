# PQG API Contract v1

## Retrieve suggestions

`GET /api/v1/sessions/{session_id}/messages/{assistant_message_id}/proactive-questions`

响应：

```json
{
  "schema_version": "pqg.v1",
  "request_id": "pqg_123",
  "session_id": "session_123",
  "assistant_message_id": "msg_456",
  "status": "READY",
  "questions": [
    {
      "candidate_id": "q_1",
      "text": "需要我再介绍一下适合早餐的搭配吗？",
      "source": "HYBRID",
      "relevance_score": 0.91,
      "confidence": 0.88,
      "rank": 1
    }
  ],
  "generated_at": "2026-09-01T10:00:00Z",
  "latency_ms": 420
}
```

`status` values: `READY`, `EMPTY`, `SUPPRESSED`, `DEGRADED`。当前 v1 API 同步返回结果；顾客响应不包含 provider 原始错误、完整检索原文或内部提示词。

## Trigger or refresh suggestions

`POST /api/v1/sessions/{session_id}/messages/{assistant_message_id}/proactive-questions`

可选请求：

```json
{
  "force_refresh": false,
  "policy_version": "default-v1"
}
```

仅允许对当前会话和已完成的 assistant message 调用；重复请求应幂等或复用同一结果。无权限返回 `403`，资源不存在返回 `404`，参数非法返回 `422`。

## Interaction event

`POST /api/v1/sessions/{session_id}/proactive-questions/events`

```json
{
  "request_id": "pqg_123",
  "candidate_id": "q_1",
  "event_type": "CLICK"
}
```

允许事件：`IMPRESSION`, `CLICK`, `EDIT`, `SEND`, `IGNORE`。该接口只记录事件，不发送消息、不下单、不支付。

## LLM generation schema

Provider 必须返回：

```json
{
  "schema_version": "pqg.v1",
  "questions": [
    {"text": "顾客可能继续追问的问题", "reason": "与当前商品选择相关"}
  ]
}
```

服务端拒绝非 JSON、未知字段导致的非法结构、空文本、超过 3 项、重复项和违反策略的候选。`reason` 仅供内部追踪，不直接展示给顾客。

## UI contract

- `READY`: 展示最多 3 个按钮。
- `EMPTY`/`SUPPRESSED`: 不展示候选或展示克制的无建议状态。
- `DEGRADED`: 原回复保持可见，可选择不提示顾客内部失败。
- 点击按钮：填充输入框并聚焦；不得自动调用发送接口。

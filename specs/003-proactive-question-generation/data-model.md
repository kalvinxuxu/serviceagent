# Data Model: 主动问题生成（PQG）

## PQGRequest

一次回复后的建议生成请求。

- `request_id`: 唯一标识
- `session_id`: 所属会话
- `assistant_message_id`: 触发 PQG 的客服回复
- `context_summary`: 脱敏后的当前上下文摘要
- `last_exchange`: 脱敏后的最后问答
- `policy_version`: 使用的建议策略版本
- `status`: `READY | EMPTY | SUPPRESSED | DEGRADED`
- `created_at`, `completed_at`

约束：必须关联已完成的客服回复；不存在会话或回复时拒绝；上下文不得包含不必要的个人敏感信息。

## QuestionCandidate

可展示给顾客的一个后续问题。

- `candidate_id`: 请求内唯一标识
- `text`: 顾客可直接发送的问题文本
- `source`: `RETRIEVAL | LLM | HYBRID`
- `relevance_score`: 0–1，可选
- `confidence`: 0–1，可选
- `rank`: 1–3
- `validation_status`: `ACCEPTED | FILTERED`
- `evidence_ids`: 支持该候选的证据引用
- `filter_reason`: 被过滤时的内部原因

约束：非空、中文自然语言、长度在产品配置范围内、最多 3 个；不得重复当前问题、包含未确认事实、敏感内容或强制性话术。

## RetrievalEvidence

历史检索对候选的可追溯依据。

- `evidence_id`
- `corpus_item_id`: 脱敏语料项标识
- `context_similarity`: 0–1
- `followup_frequency`: 历史频次
- `topic`: 业务主题
- `redacted_excerpt`: 必要时的脱敏摘要，不保存完整个人原文

## GenerationOutput

LLM provider 的原始结构化结果及处理状态。

- `schema_version`: 如 `pqg.v1`
- `provider`, `model`: 配置标识
- `candidates`: LLM 候选数组
- `parse_status`: `VALID | INVALID_JSON | INVALID_SCHEMA | TIMEOUT | PROVIDER_ERROR`
- `latency_ms`
- `error_code`: 内部错误码，不直接展示

## SuggestionPolicy

- `policy_version`
- `max_candidates`: v1 最大为 3
- `allowed_topics`: 规格、价格、库存、配送、购买流程等
- `sales_objective`: 可配置的非强制销售目标
- `suppression_rules`: 转人工、高风险、拒绝推荐、关键事实待澄清等
- `style`: 语言和语气约束

## InteractionEvent

- `event_id`, `session_id`, `request_id`, `candidate_id`
- `event_type`: `IMPRESSION | CLICK | EDIT | SEND | IGNORE`
- `created_at`
- `metadata`: 最小化的非敏感统计字段

## Relationships and Lifecycle

`Session` 1—N `PQGRequest`; `PQGRequest` 1—N `QuestionCandidate`; candidate N—N `RetrievalEvidence`。v1 候选生命周期为 `ACCEPTED/FILTERED → DISPLAYED → CLICKED/IGNORED → SENT`，其中 `SENT` 只能由现有顾客发送流程产生。

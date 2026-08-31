# API Contract: 模拟电商客服 Agent

## `POST /api/v1/sessions`

创建客服会话。

Response:

```json
{
  "session_id": "ses_001",
  "status": "IN_PROGRESS"
}
```

## `POST /api/v1/sessions/{session_id}/messages`

提交客户消息并运行一次 Agent 循环。默认返回本轮产生的最终客户可见消息，以及可选的 Inspector 摘要。

Request:

```json
{
  "message": "我昨天买的贝果能换成原味吗？",
  "customer_id": "CUS001"
}
```

Response:

```json
{
  "session_id": "ses_001",
  "message": {
    "role": "assistant",
    "content": "我先帮你确认昨天的订单。"
  },
  "status": "IN_PROGRESS",
  "requires_confirmation": false,
  "requires_human": false,
  "inspector": {
    "current_goal": "EXCHANGE",
    "next_action": "TOOL",
    "last_tool": "find_recent_orders",
    "last_tool_status": "SUCCEEDED"
  }
}
```

Rules:

- `message` 不能为空；服务端拒绝超过限制的消息长度。
- Agent 每次只执行一个 `NextAction`，工具结果写入 Trace 后再继续规划。
- `ASK_CONFIRMATION` 必须返回确认提示；没有后续客户确认不得执行退货/换货提交。
- `HANDOFF` 必须返回接管原因和上下文已保留的提示。
- 工具或数据不可用时返回可理解的失败信息，不返回未经验证的库存/订单结果。

## `GET /api/v1/sessions/{session_id}`

返回会话消息、目标、当前状态、待补充字段和是否需要确认/人工。

## `GET /api/v1/sessions/{session_id}/trace`

返回脱敏后的 AgentRun、AgentStep、ToolCall 和计划版本，用于 Inspector 和调试。

## `POST /api/v1/sessions/{session_id}/confirmations`

确认一个待执行的有副作用动作。

Request:

```json
{
  "confirmation_id": "cnf_001",
  "confirmed": true
}
```

Rules:

- 只接受当前会话中仍有效且未执行的确认。
- 重复提交必须返回已有结果，不得创建重复退货/换货申请。
- 取消确认回到 `IN_PROGRESS`，并允许客户修改目标或转人工。

## Tool Contract

## Planner Contract

Planner 到 LangGraph Router 的结果必须是严格 JSON Schema / Pydantic 结构化输出，不允许下游通过 Markdown 标题、正则或自然语言猜测动作。

```json
{
  "goal": {
    "type": "EXCHANGE_PRODUCT",
    "status": "ACTIVE"
  },
  "next_action": {
    "type": "TOOL_CALL",
    "tool_name": "check_inventory",
    "arguments": {
      "product_id": "SKU123",
      "variant": "PLAIN"
    }
  },
  "reason_code": "TARGET_PRODUCT_FOUND",
  "missing_information": [],
  "requires_confirmation": false
}
```

Allowed action types are `TOOL_CALL`, `ASK_USER`, `ASK_CONFIRMATION`, `RESPOND`, and `HANDOFF`. The schema is versioned; unknown action types, missing required fields, invalid argument types, and extra unsafe fields cause validation failure and no execution. Planner output may contain a short `decision_summary`, but must not require chain-of-thought or hidden reasoning for execution.

## Component Contract Rule

每个后端组件必须对外暴露稳定的输入/输出模型和错误结果，不允许调用方依赖其内部数据库模型、Graph 节点状态或 Prompt 文本。组件至少提供：

- 正常输入与输出 Schema；
- 可预期失败类型及恢复方式；
- 独立单元测试；
- 面向替换的契约测试。

例如，`inventory` 组件可由 SQLite 模拟实现替换为 PostgreSQL 或真实库存适配器，只要继续满足库存查询契约，上层 Planner、Tool 和前端无需修改。

所有工具均返回统一结果：

```json
{
  "ok": true,
  "data": {},
  "reason": null,
  "observed_at": "2026-08-23T12:00:00Z"
}
```

首版工具集合见 `research.md` 与 `data-model.md`，至少包括客户/订单查询、商品搜索、库存检查、推荐、退货资格、退款计算、退货/换货申请和政策搜索。

## V2 Agent Contracts

### SupervisorDecision

```json
{
  "schema_version": "2.0",
  "goals": ["INVENTORY_CHECK"],
  "domain": "COMMERCE",
  "route_action": "CONTINUE_AGENT",
  "target_agent": "COMMERCE",
  "task_id": "task_001",
  "missing_information": [],
  "reason_code": "COMMERCE_INVENTORY_QUERY",
  "confidence": 0.96
}
```

`domain` 只能是 `COMMERCE`、`AFTER_SALES`、`HUMAN`、`UNKNOWN`；`route_action` 只能是 `CONTINUE_AGENT`、`SWITCH_AGENT`、`PARALLEL_TASKS`、`ASK_USER`、`HANDOFF`。

### AgentTask

```json
{
  "schema_version": "2.0",
  "task_type": "HANDLE_WRONG_ITEM_COMPLAINT",
  "source_agent": "SUPERVISOR",
  "target_agent": "AFTER_SALES",
  "customer_id": "CUS001",
  "order_id": "ORD102",
  "user_message": "送错了，图片里这个不是我要的",
  "relevant_context": {
    "expected_product_id": "SKU026"
  },
  "attachments": []
}
```

AgentTask 只包含目标 Agent 所需的上下文，不通过自由文本传递执行动作或副作用授权。

### After-sales Evidence and Resolution

```json
{
  "issue_type": "DAMAGED_PRODUCT",
  "evidence": {
    "visible_damage": true,
    "confidence": 0.92
  },
  "severity": "MEDIUM",
  "requires_human": false
}
```

证据组件不得直接调用退款或赔偿工具。必须经过 `check_claim_policy` / `resolve_claim_options`，再由客户确认或人工审批后执行。

### Agent Capability Isolation

Commerce Agent 可使用商品搜索、库存、推荐、报价、会员和促销查询；After-sales Agent 可使用订单、证据、退货资格、售后政策和受约束的退款/补发申请；Supervisor 不直接调用业务副作用工具。目录、库存、促销维护仍只允许管理边界调用。

## Admin API Contract

管理后台使用以下接口，均返回 JSON；错误使用 `4xx + {"detail": "CODE"}`：

```text
GET    /api/v1/admin/products
PUT    /api/v1/admin/products/{product_id}
POST   /api/v1/admin/media/upload        multipart/form-data
GET    /api/v1/admin/media
GET    /api/v1/admin/featured-list
PUT    /api/v1/admin/featured-list
POST   /api/v1/admin/featured-list/items/{product_id}
DELETE /api/v1/admin/featured-list/items/{product_id}
GET    /api/v1/admin/customers/{customer_id}/memory
DELETE /api/v1/admin/customers/{customer_id}/memory/{key}
```

`PUT /admin/products/{id}` 只接收允许的商品字段；`media/upload` 返回 `media_id`、商品 ID、类型和安全 URL；必吃榜接口只接受已存在的商品 ID。所有变更必须可从 Admin Audit 查询。

## Frontend Route Contract

- `/`：顾客聊天、推荐卡片、图片附件、报价和人工状态。
- `/admin`：商品画像 JSON 编辑、图片上传、必吃榜维护、客户记忆查看/删除。
- Admin UI 不自行推断价格、库存或推荐结论；只展示 API 返回的确定性结果。

# Data Model: 自主规划客服智能体

## CustomerSession

- `id`: 会话标识。
- `customer_id`: 可空；已验证客户标识。
- `messages`: 会话消息序列，包含角色、内容、时间和敏感字段脱敏版本。
- `goals`: 一个或多个 CustomerGoal，包含类型、状态、优先级和来源消息。
- `known_facts`: 已确认的订单、商品、规格、偏好和客户约束。
- `missing_fields`: 当前目标仍缺失的必要字段。
- `current_plan`: 当前步骤与状态。
- `requires_confirmation`: 是否等待客户确认。
- `requires_human`: 是否等待人工接管。
- `status`: `IN_PROGRESS`、`WAITING_USER`、`WAITING_CONFIRMATION`、`HANDOFF`、`RESOLVED`、`FAILED`。

## CustomerGoal

- `id`, `type`: 目标标识与 `ORDER_QUERY`、`INVENTORY_CHECK`、`RECOMMENDATION`、`RETURN`、`EXCHANGE`、`FAQ` 或 `OTHER`。
- `status`: `ACTIVE`、`PAUSED`、`COMPLETED`、`CANCELLED`。
- `confidence`: 识别置信度，用于澄清或接管门槛。
- `constraints`: 预算、用途、偏好、规格等约束。
- `parent_goal_id`: 可空；支持一个会话中目标切换与目标栈。

## ServicePlan / PlanStep

- `plan_id`, `session_id`, `goal_id`。
- `step_index`, `action_type`, `tool_name`, `tool_args`, `reason`。
- `status`: `PENDING`、`RUNNING`、`COMPLETED`、`BLOCKED`、`SKIPPED`。
- 每轮只允许一个可执行的下一步；工具观察结果后生成新计划版本。

## Product / ProductVariant / InventoryState

- Product：商品名、类别、描述、属性、价格、替代关系；不保存运行时库存。
- ProductVariant：规格、口味、包装、营养属性等可区分字段。
- InventoryState：每个商品一条当前库存状态，保存 `on_hand`、`reserved`、`version`、`updated_at`。
- `available_quantity = max(on_hand - reserved, 0)`；库存数量不得为负，查询返回明确状态和时间。
- `products.json` 仅初始化商品资料，`inventory.json` 仅初始化 `InventoryState`；运行时库存唯一读取数据库。

## Customer / Order / OrderItem

- Customer：客户标识、昵称、验证状态、必要联系信息。
- Order：订单标识、客户、下单时间、履约状态、物流信息。
- OrderItem：订单商品、规格、数量、单价和履约/退货状态。
- 订单项是退货/换货资格判断和幂等保护的最小业务对象。

## ReturnRequest

- `id`, `order_id`, `order_item_id`, `customer_id`。
- `type`: `RETURN` 或 `EXCHANGE`。
- `reason`, `evidence`, `eligibility_status`, `eligibility_reason`。
- `customer_confirmed_at`, `status`, `refund_amount`, `replacement_product_id`。
- `status`: `DRAFT`、`PENDING_CONFIRMATION`、`SUBMITTED`、`UNDER_REVIEW`、`APPROVED`、`REJECTED`、`COMPLETED`、`CANCELLED`。
- 同一订单项在存在未完成申请时不得重复创建同类型申请。

## RecommendationResult / PolicyArticle

- RecommendationResult：会话、约束快照、候选商品、推荐理由、取舍说明和库存快照。
- PolicyArticle：主题、正文、适用条件、版本、发布时间和是否有效。

## AgentRun / AgentStep / ToolCall / HumanHandoff

- AgentRun：会话、开始/结束时间、最终状态、模型/provider 标识。
- AgentStep：步骤类型、输入摘要、输出摘要、状态、耗时和错误原因。
- ToolCall：工具名、脱敏参数、结果摘要、成功状态、幂等键。
- HumanHandoff：原因、上下文摘要、转交时间、处理人、接管结果。
- Trace 记录不得保存不必要的完整敏感信息。

## V2 Multi-Agent Entities

### AgentTask

- `id`, `session_id`, `parent_task_id`。
- `task_type`: `ROUTE_COMMERCE`、`HANDLE_AFTER_SALES`、`HUMAN_HANDOFF` 等版本化任务类型。
- `source_agent`, `target_agent`, `status`: `CREATED`、`RUNNING`、`COMPLETED`、`BLOCKED`、`CANCELLED`。
- `user_message`, `relevant_context`, `attachments`, `required_capabilities`。
- 只包含目标 Agent 完成任务所需的脱敏上下文。

### SupervisorDecision

- `goals`: 当前识别的一个或多个服务目标。
- `domain`: `COMMERCE`、`AFTER_SALES`、`HUMAN`、`UNKNOWN`。
- `route_action`: `CONTINUE_AGENT`、`SWITCH_AGENT`、`PARALLEL_TASKS`、`ASK_USER`、`HANDOFF`。
- `reason_code`, `confidence`, `missing_information`。

### ComplaintContext

- `issue_type`: `WRONG_ITEM`、`MISSING_ITEM`、`DAMAGED_PRODUCT`、`QUALITY_RISK`、`DELIVERY_EXCEPTION`、`OTHER`。
- `order_id`, `expected_items`, `reported_items`, `customer_claim`。
- `evidence_status`: `NOT_REQUIRED`、`REQUESTED`、`RECEIVED`、`INSUFFICIENT`、`CONFLICTING`。
- `severity`, `safety_risk`, `confidence`。

### EvidenceObservation

- `source`: `TEXT`、`IMAGE`、`ORDER_DATA`、`DELIVERY_DATA`。
- `classification`, `confidence`, `observed_facts`, `uncertainties`, `observed_at`。
- 视觉观察不得直接产生退款/赔偿动作。

### ResolutionDecision

- `issue_type`, `policy_version`, `allowed_levels`, `recommended_level`。
- Resolution Ladder：`EXPLAIN`、`REPLACEMENT`、`ITEM_REFUND`、`PARTIAL_REFUND_COMPENSATION`、`FULL_REFUND`、`HUMAN_APPROVAL`。
- `options`, `requires_confirmation`, `requires_human`, `reason_code`。

### Multi-Agent State Rules

- Agent 不维护独立会话记忆；所有事实写入共享会话状态。
- 领域 Agent 只能写入被授权的状态片段。
- Supervisor 可以切换域，但不得覆盖已确认的订单、商品或报价事实。
- AgentTask、路由切换、证据观察、政策判断和人工接管均写入 Trace。

## Admin Console View Models

管理后台使用 API View Model，不直接暴露 SQLAlchemy 模型：

- `ProductAdminView`：`id`、`name`、`category`、`price`、`profile`、`media`、库存摘要。
- `ProductMediaView`：`media_id`、`product_id`、`asset_type`、安全访问 URL、`alt_text`、`status`。
- `FeaturedListView`：标题、说明、启用状态、按顺序排列的 `product_ids`。
- `CustomerMemoryView`：客户 ID 范围内的记忆键、类型、值、来源、确认状态和时间。
- `AdminAuditEvent`：操作者、资源类型、资源 ID、变更摘要、时间和结果；敏感值只保存脱敏摘要。

管理 View Model 的更新必须经过领域服务，失败时不得部分写入；媒体原始路径、API Key 和完整手机号不得返回给前端。

## State Transitions

```text
IN_PROGRESS -> WAITING_USER -> IN_PROGRESS
IN_PROGRESS -> WAITING_CONFIRMATION -> IN_PROGRESS
WAITING_CONFIRMATION -> RESOLVED
IN_PROGRESS -> HANDOFF
WAITING_USER -> HANDOFF
IN_PROGRESS -> FAILED
IN_PROGRESS -> RESOLVED
```

有副作用的动作只能从 `WAITING_CONFIRMATION` 经客户确认进入执行；工具失败回到 `IN_PROGRESS` 进行重试、澄清或 `HANDOFF`，不得直接标记成功。

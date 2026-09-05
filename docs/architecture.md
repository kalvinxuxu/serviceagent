# Architecture Notes

## V2 Agent Boundaries

The V2 contracts are retained for Legacy Mode compatibility. Converged Mode uses the
domain-only `SupervisorRouter`, optional `ActionPlanner`, `PlanValidator`, `PolicyGate`,
and `HandoffState` boundaries described below; it does not treat Human as an Agent.

- `SupervisorAgent`：接收 `UnderstandingOutput`，通过 DeepSeek 结构化输出 `SupervisorDecision`；只负责服务域、任务和路由，不调用业务工具。
- `CommerceAgent`：处理商品、库存、推荐、报价和促销解释；确定性计算继续由 Domain Service 完成。
- `AfterSalesAgent`：处理订单问题、证据观察和 Resolution Ladder；退款、换货和赔偿必须经过政策、确认、人工审批（如需）及幂等校验。
- `Human Handoff`：接收脱敏后的 `AgentTask`、原始诉求、已确认事实、已完成步骤和待处理事项。

## Execution and Fallback

`backend/app/agent/graph.py` 保持可替换节点：

```text
understand → supervisor → goal update → capability resolver → planner → tool/domain service
```

当 DeepSeek 不可用或返回不符合 `SupervisorDecision` 的结果时，Supervisor 回退到同一契约约束下的确定性路由；不会直接执行副作用工具。

## Evaluation Evidence

`evals/runner.py` 从 `evals/scenarios/*.json` 执行场景并计算路由、任务契约、响应清晰度、循环率、上下文保留和副作用闸门指标。V2 场景文件覆盖 SC-001～SC-009，每个 criterion 均有独立输入和预期路由。

领域规则位于 `backend/app/domain`，工具适配位于 `backend/app/tools`，API 位于 `backend/app/api`。Planner 和 Supervisor 输出严格 Pydantic JSON，所有副作用经过确认。

## Pending follow-up and failure propagation

当客服回复中提出可执行的下一步建议时，Graph 将建议保存为 `pending_followup`，包含来源轮次、提示语、继承约束和上下文。用户的“好的/可以/行”等确认先经过 `FollowupIntentResolver`；只有存在待确认建议时才恢复对应能力，没有待确认建议则进入普通澄清。

评估状态按首个失败组件传播：`LLM_OUTPUT_INVALID`、语义无法解析或待确认建议无法恢复会记录 `failure_component`，后续没有执行的组件必须为 `NOT_RUN`，不得沿用上一轮的成功状态。

## Order Email Agent

The V1 order-email flow is isolated under `backend/app/order_agent` and uses simulated email, catalog, inventory, and send adapters. It parses an email into a versioned draft, checks deterministic inventory facts, composes a reply, and requires operator confirmation before simulated sending. It must not call real mailbox, ERP, WMS, payment, or logistics systems.
## Proactive Question Generation (PQG)

PQG runs after a completed assistant reply and is isolated from the reply path. It combines a
sanitized historical-dialogue retriever with the configured LLM provider, validates only the
versioned `pqg.v1` JSON contract, then deduplicates and applies suppression/claim filters. The
customer sees at most three suggestions; clicking one fills the composer and never sends it.
Provider failures return a degraded/empty result while preserving the original reply. Requests
and interaction events use the `pqg_requests` and `pqg_interaction_events` boundaries and should
retain only minimum necessary, redacted context.
# Core Agent convergence routing

The convergence path uses deterministic routing for atomic requests and reserves
the planner for multi-step or conditional work:

```text
Semantic Workspace → Reference Resolver → Supervisor Router
  → atomic: Capability Policy → Executor
  → long-running: Goal Manager → Capability Policy → Executor
  → complex: Action Planner → Policy Gate → Executor
```

Supervisor only selects `COMMERCE`, `AFTER_SALES`, or `UNKNOWN`. Human handoff is represented by
`execution_mode=HUMAN_HANDOFF` and `HandoffState`. Policy Gate owns

Legacy Supervisor task/action/HUMAN fields and old tool names remain as
compatibility adapters only; Converged runtime uses the domain-only
`ConvergedSupervisorDecision` and the canonical tool groups in the registry.
confirmation, permission, and escalation decisions. Capability Policy is a
read-only action-to-tool catalogue, not a second planner. Goal Manager is a
no-op for ordinary read-only queries. `AGENT_ARCHITECTURE=legacy` remains the
default until Converged Mode passes the comparison gates.

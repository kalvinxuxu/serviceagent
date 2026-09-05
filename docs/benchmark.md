# Customer Service Agent Benchmark V1

Benchmark V1 evaluates 20 text cases using the current product seed, database inventory, and persisted business policies.

```powershell
$env:LLM_PROVIDER="deepseek"
python evals/benchmark.py --suite customer_service_v1
```

The evaluator writes JSON and Markdown reports under `reports/benchmark/`. Business facts are checked deterministically from State, Trace, InventoryService, PricingService, and RecommendationService. Set `BENCHMARK_LLM_JUDGE=1` to enable the optional DeepSeek language-quality judge; it cannot override deterministic business scores.

## Component-level evaluation

Each turn also records Data Lineage steps for Understanding, Normalization, Entity Resolver, Constraint Extraction, Goal Manager, Capability Resolver, Planner, Plan Validator, Tool/Business execution, State Manager, and Response Generation. The final `turn_evaluation` identifies the first failed component and stores component scores. The API trace includes these records; legacy direct `trace_service.get()` callers receive the original step-only view unless `include_lineage=True` is used.

The semantic-state suite can be validated with:

```powershell
$env:LLM_PROVIDER="mock"
python evals/benchmark.py --suite semantic_state_v1
```

The report includes `component_accuracy`, `first_failure_components`, `semantic_state_coverage`, and feedback-event counts in addition to the existing E2E metrics.

The benchmark does not mutate inventory, catalog, or business policies. It records a fixture hash, model name, latency, raw reply, trace summary, and per-dimension score. API keys and customer secrets are excluded from reports.

## Real group orders

Run the deterministic benchmark for the extracted Shanye Bakery group-order cases:

```powershell
$env:LLM_PROVIDER="mock"
python evals/benchmark.py --suite real_group_orders_v1 --no-judge
```

The suite covers reservation, stock exhaustion, pickup-time clarification, idempotency, and inventory lookup. Training-formatted source data is stored in `data/training/real_group_orders_v1.jsonl`.

## Legacy vs Semantic comparison

Run both architectures against the same follow-up suite:

```powershell
$env:LLM_PROVIDER="qwen"
python evals/benchmark.py --suite followup_accuracy_v1 --compare
```

Legacy uses the existing UnderstandingOutput/Goal/Planner path. Semantic uses the Semantic Workspace, Reference Resolver, and deterministic Business State path. The report stores both variants and deltas for accuracy, clarifications, handoffs, and latency. Semantic mode is not the default until it passes the acceptance gates.

## Converged architecture gates

Converged mode treats `Supervisor` as domain routing only. `active_domain` is limited to
`COMMERCE`, `AFTER_SALES`, and `UNKNOWN`; human escalation is represented by
`execution_mode=HUMAN_HANDOFF` and `HandoffState`. Atomic requests must bypass persistent Goal
Manager and Action Planner. Complex actions must pass Plan Validator and Policy Gate before the
Executor. Comparison reports also record duplicate decisions, unnecessary tools, premature
handoffs, step count, and tool-surface reduction.
### Clarification and selection metrics

Benchmark case results include `clarification` data for conversation acts, missing slots,
clarification count, selected recommendation detection, and blocked delivery side effects. These
fields allow a failure to be distinguished between semantic understanding, slot filling, goal
transition, and unsafe tool execution.
## Follow-up recovery

当客服在回复中提出可执行的下一步建议（例如“要不要我按口感和甜度再帮您挑几款？”），Graph 必须保存 `pending_followup` 及其来源轮次、约束和上下文。用户回复“好的/可以/行”时，`FollowupIntentResolver` 将其解析为 `ACCEPT_FOLLOWUP`，恢复原建议；没有待确认建议时不得调用业务工具。

评估器对 `LLM_OUTPUT_INVALID`、`SEMANTIC_INTENT_UNRESOLVED` 和 `ACCEPT_FOLLOWUP_NOT_RESOLVED` 采用失败传播：首个失败组件为 `failure_component`，后续未执行组件为 `NOT_RUN`，不得沿用上一轮 PASS。

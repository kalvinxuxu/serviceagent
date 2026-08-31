# Customer Service Agent Benchmark V1

- Run: 2026-08-24T14:59:14.954355+00:00
- Model: deepseek-chat
- Fixture: 53068010fb64

## Metrics

- overall_score: 100.0
- goal_accuracy: 1.0
- entity_accuracy: 1.0
- tool_precision: 1.0
- business_accuracy: 1.0
- response_clarity_score: 1.0
- task_completion_rate: 1.0
- unnecessary_tool_rate: 0.0
- forbidden_tool_call_count: 0
- wrong_fallback_rate: 0.0
- multi_turn_state_consistency: 1.0
- quote_recalculation_accuracy: 1.0
- recommendation_constraint_accuracy: 1.0
- p95_latency_ms: 11886.48
- tool_call_count: 25
- component_accuracy: {'understanding': 1.0, 'normalization': 1.0, 'entity_resolver': 1.0, 'constraint_extraction': 1.0, 'goal_manager': 1.0, 'capability_resolver': 1.0, 'planner': 1.0, 'plan_validator': 1.0, 'tool_selection': 1.0, 'tool_arguments': 1.0, 'business_service': 1.0, 'state_manager': 1.0, 'response_generation': 1.0}
- first_failure_components: {}
- feedback_correction_rate: 0.0
- semantic_state_coverage: 1.0

## Case Results

| Case | Score | Status | Tools |
|---|---:|---|---|
| SC-01 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-02 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-03 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-04 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-05 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-06 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-07 | 5/5 | IN_PROGRESS | list_available_inventory |
| SC-08 | 5/5 | IN_PROGRESS | list_available_inventory |
| SC-09 | 5/5 | IN_PROGRESS | compare_products |
| SC-10 | 5/5 | IN_PROGRESS | compare_products |
| SC-11 | 5/5 | IN_PROGRESS | recommend_products |
| SC-12 | 5/5 | IN_PROGRESS | recommend_products |
| SC-13 | 5/5 | IN_PROGRESS | recommend_products |
| SC-14 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-15 | 5/5 | IN_PROGRESS | check_inventory |
| SC-16 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-17 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote, calculate_order_quote |
| SC-18 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-19 | 5/5 | IN_PROGRESS | get_sales_policy |
| SC-20 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |

## Component Evaluation

- understanding: 1.0
- normalization: 1.0
- entity_resolver: 1.0
- constraint_extraction: 1.0
- goal_manager: 1.0
- capability_resolver: 1.0
- planner: 1.0
- plan_validator: 1.0
- tool_selection: 1.0
- tool_arguments: 1.0
- business_service: 1.0
- state_manager: 1.0
- response_generation: 1.0

## Failures

- None

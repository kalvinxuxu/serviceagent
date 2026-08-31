# Customer Service Agent Benchmark V1

- Run: 2026-08-24T06:25:43.801695+00:00
- Model: deepseek-chat
- Fixture: 19e0a4ff55f6

## Metrics

- overall_score: 91.0
- goal_accuracy: 1.0
- entity_accuracy: 1.0
- tool_precision: 0.9
- business_accuracy: 0.65
- response_clarity_score: 1.0
- task_completion_rate: 1.0
- unnecessary_tool_rate: 0.1667
- forbidden_tool_call_count: 0
- wrong_fallback_rate: 0.0
- multi_turn_state_consistency: 1.0
- quote_recalculation_accuracy: 1.0
- recommendation_constraint_accuracy: 0.0
- p95_latency_ms: 10666.12
- tool_call_count: 18

## Case Results

| Case | Score | Status | Tools |
|---|---:|---|---|
| SC-01 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-02 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-03 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-04 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-05 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-06 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-07 | 3/5 | WAITING_USER |  |
| SC-08 | 3/5 | WAITING_USER |  |
| SC-09 | 4/5 | WAITING_USER |  |
| SC-10 | 4/5 | WAITING_USER |  |
| SC-11 | 4/5 | IN_PROGRESS | recommend_products |
| SC-12 | 4/5 | WAITING_USER |  |
| SC-13 | 4/5 | IN_PROGRESS | recommend_products |
| SC-14 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-15 | 5/5 | IN_PROGRESS | check_inventory |
| SC-16 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-17 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote, calculate_order_quote |
| SC-18 | 5/5 | WAITING_USER | calculate_order_quote |
| SC-19 | 5/5 | IN_PROGRESS | get_sales_policy |
| SC-20 | 5/5 | WAITING_USER | calculate_order_quote |

## Failures

- SC-07: {'goal': 1, 'entity': 1, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'available_products': []}
- SC-08: {'goal': 1, 'entity': 1, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'available_products': []}
- SC-09: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-10: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-11: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-12: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-13: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- None

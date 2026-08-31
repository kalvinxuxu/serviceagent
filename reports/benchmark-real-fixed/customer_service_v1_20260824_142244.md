# Customer Service Agent Benchmark V1

- Run: 2026-08-24T06:22:44.648203+00:00
- Model: deepseek-chat
- Fixture: 19e0a4ff55f6

## Metrics

- overall_score: 81.0
- goal_accuracy: 0.9
- entity_accuracy: 0.8
- tool_precision: 0.8
- business_accuracy: 0.55
- response_clarity_score: 1.0
- task_completion_rate: 1.0
- unnecessary_tool_rate: 0.1765
- forbidden_tool_call_count: 0
- wrong_fallback_rate: 0.0
- multi_turn_state_consistency: 0.5
- quote_recalculation_accuracy: 0.6667
- recommendation_constraint_accuracy: 0.0
- p95_latency_ms: 17703.65
- tool_call_count: 17

## Case Results

| Case | Score | Status | Tools |
|---|---:|---|---|
| SC-01 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-02 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-03 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-04 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-05 | 2/5 | IN_PROGRESS | list_available_inventory |
| SC-06 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-07 | 5/5 | IN_PROGRESS | list_available_inventory |
| SC-08 | 3/5 | WAITING_USER |  |
| SC-09 | 3/5 | HANDOFF |  |
| SC-10 | 4/5 | WAITING_USER |  |
| SC-11 | 4/5 | WAITING_USER |  |
| SC-12 | 4/5 | WAITING_USER |  |
| SC-13 | 4/5 | WAITING_USER |  |
| SC-14 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-15 | 5/5 | IN_PROGRESS | check_inventory |
| SC-16 | 2/5 | WAITING_USER | list_available_inventory |
| SC-17 | 2/5 | WAITING_USER | list_available_inventory, list_available_inventory |
| SC-18 | 4/5 | IN_PROGRESS | list_available_inventory, calculate_order_quote |
| SC-19 | 5/5 | IN_PROGRESS | get_sales_policy |
| SC-20 | 4/5 | IN_PROGRESS | list_available_inventory, calculate_order_quote |

## Failures

- SC-05: {'goal': 0, 'entity': 1, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 55, 'actual_subtotal': None, 'expected_total': 56.0, 'actual_total': None}
- SC-08: {'goal': 1, 'entity': 1, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'available_products': []}
- SC-09: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-10: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-11: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-12: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-13: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-16: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 26, 'actual_subtotal': None, 'expected_total': 32.0, 'actual_total': None}
- SC-17: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 34, 'actual_subtotal': None, 'expected_total': 37.0, 'actual_total': None}
- SC-18: {'goal': 1, 'entity': 0, 'tool': 1, 'business_result': 1, 'response_safety': 1} {}
- SC-20: {'goal': 1, 'entity': 0, 'tool': 1, 'business_result': 1, 'response_safety': 1} {}
- None

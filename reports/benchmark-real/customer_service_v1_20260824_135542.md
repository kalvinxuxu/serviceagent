# Customer Service Agent Benchmark V1

- Run: 2026-08-24T05:55:42.971062+00:00
- Model: deepseek-chat
- Fixture: 19e0a4ff55f6

## Metrics

- overall_score: 82.0
- goal_accuracy: 0.5
- entity_accuracy: 1.0
- tool_precision: 1.0
- business_accuracy: 0.6
- response_clarity_score: 1.0
- task_completion_rate: 1.0
- unnecessary_tool_rate: 0.2381
- forbidden_tool_call_count: 0
- wrong_fallback_rate: 0.0
- multi_turn_state_consistency: 1.0
- quote_recalculation_accuracy: 1.0
- recommendation_constraint_accuracy: 0.0
- p95_latency_ms: 11657.03
- tool_call_count: 21

## Case Results

| Case | Score | Status | Tools |
|---|---:|---|---|
| SC-01 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-02 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-03 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-04 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-05 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-06 | 4/5 | IN_PROGRESS | calculate_order_quote |
| SC-07 | 4/5 | IN_PROGRESS | list_available_inventory |
| SC-08 | 4/5 | IN_PROGRESS | list_available_inventory |
| SC-09 | 3/5 | IN_PROGRESS | calculate_order_quote |
| SC-10 | 3/5 | IN_PROGRESS | calculate_order_quote |
| SC-11 | 3/5 | WAITING_USER |  |
| SC-12 | 3/5 | WAITING_USER |  |
| SC-13 | 3/5 | WAITING_USER |  |
| SC-14 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-15 | 5/5 | IN_PROGRESS | check_inventory |
| SC-16 | 4/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-17 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote, calculate_order_quote |
| SC-18 | 4/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-19 | 3/5 | WAITING_USER |  |
| SC-20 | 4/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |

## Failures

- SC-06: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 34, 'actual_subtotal': 20.0, 'expected_total': 37.0, 'actual_total': 26.0}
- SC-07: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 1, 'response_safety': 1} {'available_products': ['原味吐司', '全麦吐司', '蔓越莓吐司', '生吐司', '茶香奶酥吐司']}
- SC-08: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 1, 'response_safety': 1} {'available_products': ['日式盐面包', '海苔海盐包', '橙丁盐面包', '日式巧克力盐面包']}
- SC-09: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-10: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-11: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-12: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-13: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-16: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 26, 'actual_subtotal': 52.0, 'expected_total': 32.0, 'actual_total': 53.0}
- SC-18: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 1, 'response_safety': 1} {}
- SC-19: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-20: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 1, 'response_safety': 1} {}
- None

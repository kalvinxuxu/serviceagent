# Customer Service Agent Benchmark V1

- Run: 2026-08-24T06:14:57.285439+00:00
- Model: deepseek-chat
- Fixture: 19e0a4ff55f6

## Metrics

- overall_score: 76.0
- goal_accuracy: 0.85
- entity_accuracy: 0.7
- tool_precision: 0.85
- business_accuracy: 0.55
- response_clarity_score: 0.85
- task_completion_rate: 0.85
- unnecessary_tool_rate: 0.2273
- forbidden_tool_call_count: 0
- wrong_fallback_rate: 0.0
- multi_turn_state_consistency: 1.0
- quote_recalculation_accuracy: 0.6667
- recommendation_constraint_accuracy: 0.0
- p95_latency_ms: 220.22
- tool_call_count: 22

## Case Results

| Case | Score | Status | Tools |
|---|---:|---|---|
| SC-01 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-02 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-03 | 3/5 | IN_PROGRESS | calculate_order_quote |
| SC-04 | 3/5 | IN_PROGRESS | calculate_order_quote |
| SC-05 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-06 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-07 | 5/5 | IN_PROGRESS | list_available_inventory |
| SC-08 | 5/5 | IN_PROGRESS | list_available_inventory |
| SC-09 | 4/5 | IN_PROGRESS | compare_products |
| SC-10 | 4/5 | IN_PROGRESS | compare_products |
| SC-11 | 0/5 | BENCHMARK_ERROR |  |
| SC-12 | 0/5 | BENCHMARK_ERROR |  |
| SC-13 | 0/5 | BENCHMARK_ERROR |  |
| SC-14 | 3/5 | IN_PROGRESS | calculate_order_quote |
| SC-15 | 5/5 | IN_PROGRESS | check_inventory |
| SC-16 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-17 | 5/5 | IN_PROGRESS | calculate_order_quote, edit_selected_items, calculate_order_quote |
| SC-18 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-19 | 4/5 | IN_PROGRESS | get_sales_policy |
| SC-20 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |

## Failures

- SC-03: {'goal': 1, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 39, 'actual_subtotal': 13.0, 'expected_total': 42.0, 'actual_total': 19.0}
- SC-04: {'goal': 1, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 39, 'actual_subtotal': 13.0, 'expected_total': 42.0, 'actual_total': 19.0}
- SC-09: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-10: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-11: {'goal': 0, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 0} {}
- SC-12: {'goal': 0, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 0} {}
- SC-13: {'goal': 0, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 0} {}
- SC-14: {'goal': 1, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 24, 'actual_subtotal': 12.0, 'expected_total': 30.0, 'actual_total': 18.0}
- SC-19: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- None

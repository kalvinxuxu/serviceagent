# Customer Service Agent Benchmark V1

- Run: 2026-08-24T05:53:18.499138+00:00
- Model: deepseek-chat
- Fixture: 7e923d64c81f

## Metrics

- overall_score: 44.0
- goal_accuracy: 0.45
- entity_accuracy: 0.35
- tool_precision: 0.4
- business_accuracy: 0.0
- response_clarity_score: 1.0
- task_completion_rate: 1.0
- unnecessary_tool_rate: 0.0
- forbidden_tool_call_count: 0
- wrong_fallback_rate: 0.0
- multi_turn_state_consistency: 0.0
- quote_recalculation_accuracy: 0.0
- recommendation_constraint_accuracy: 0.0
- p95_latency_ms: 120.12
- tool_call_count: 0

## Case Results

| Case | Score | Status | Tools |
|---|---:|---|---|
| SC-01 | 2/5 | WAITING_USER |  |
| SC-02 | 2/5 | WAITING_USER |  |
| SC-03 | 2/5 | WAITING_USER |  |
| SC-04 | 2/5 | WAITING_USER |  |
| SC-05 | 1/5 | WAITING_USER |  |
| SC-06 | 2/5 | WAITING_USER |  |
| SC-07 | 2/5 | WAITING_USER |  |
| SC-08 | 2/5 | WAITING_USER |  |
| SC-09 | 3/5 | WAITING_USER |  |
| SC-10 | 2/5 | WAITING_USER |  |
| SC-11 | 3/5 | WAITING_USER |  |
| SC-12 | 3/5 | WAITING_USER |  |
| SC-13 | 3/5 | WAITING_USER |  |
| SC-14 | 2/5 | WAITING_USER |  |
| SC-15 | 2/5 | WAITING_USER |  |
| SC-16 | 2/5 | WAITING_USER |  |
| SC-17 | 2/5 | WAITING_USER |  |
| SC-18 | 2/5 | WAITING_USER |  |
| SC-19 | 3/5 | WAITING_USER |  |
| SC-20 | 2/5 | WAITING_USER |  |

## Failures

- SC-01: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 13, 'actual_subtotal': None, 'expected_total': 19.0, 'actual_total': None}
- SC-02: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 26, 'actual_subtotal': None, 'expected_total': 32.0, 'actual_total': None}
- SC-03: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 39, 'actual_subtotal': None, 'expected_total': 42.0, 'actual_total': None}
- SC-04: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 39, 'actual_subtotal': None, 'expected_total': 42.0, 'actual_total': None}
- SC-05: {'goal': 0, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 55, 'actual_subtotal': None, 'expected_total': 56.0, 'actual_total': None}
- SC-06: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 34, 'actual_subtotal': None, 'expected_total': 37.0, 'actual_total': None}
- SC-07: {'goal': 0, 'entity': 1, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'available_products': []}
- SC-08: {'goal': 0, 'entity': 1, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'available_products': []}
- SC-09: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-10: {'goal': 0, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-11: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-12: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-13: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-14: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 24, 'actual_subtotal': None, 'expected_total': 30.0, 'actual_total': None}
- SC-15: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {}
- SC-16: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 26, 'actual_subtotal': None, 'expected_total': 32.0, 'actual_total': None}
- SC-17: {'goal': 1, 'entity': 0, 'tool': 0, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 34, 'actual_subtotal': None, 'expected_total': 37.0, 'actual_total': None}
- SC-18: {'goal': 0, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-19: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-20: {'goal': 0, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- None

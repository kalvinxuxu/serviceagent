# Customer Service Agent Benchmark V1

- Run: 2026-08-24T05:57:45.261682+00:00
- Model: deepseek-chat
- Fixture: 19e0a4ff55f6

## Metrics

- overall_score: 77.0
- goal_accuracy: 0.5
- entity_accuracy: 0.85
- tool_precision: 1.0
- business_accuracy: 0.5
- response_clarity_score: 1.0
- task_completion_rate: 1.0
- unnecessary_tool_rate: 0.1667
- forbidden_tool_call_count: 0
- wrong_fallback_rate: 0.0
- multi_turn_state_consistency: 1.0
- quote_recalculation_accuracy: 0.6667
- recommendation_constraint_accuracy: 0.0
- p95_latency_ms: 475.74
- tool_call_count: 18

## Case Results

| Case | Score | Status | Tools |
|---|---:|---|---|
| SC-01 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-02 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-03 | 3/5 | IN_PROGRESS | calculate_order_quote |
| SC-04 | 3/5 | IN_PROGRESS | calculate_order_quote |
| SC-05 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-06 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-07 | 4/5 | IN_PROGRESS | list_available_inventory |
| SC-08 | 3/5 | IN_PROGRESS | list_available_inventory |
| SC-09 | 3/5 | HANDOFF |  |
| SC-10 | 3/5 | HANDOFF |  |
| SC-11 | 3/5 | HANDOFF |  |
| SC-12 | 3/5 | HANDOFF |  |
| SC-13 | 3/5 | IN_PROGRESS | recommend_products |
| SC-14 | 3/5 | IN_PROGRESS | calculate_order_quote |
| SC-15 | 5/5 | IN_PROGRESS | check_inventory |
| SC-16 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-17 | 5/5 | IN_PROGRESS | calculate_order_quote, edit_selected_items, calculate_order_quote |
| SC-18 | 4/5 | WAITING_USER | calculate_order_quote |
| SC-19 | 3/5 | WAITING_USER |  |
| SC-20 | 4/5 | WAITING_USER | calculate_order_quote |

## Failures

- SC-03: {'goal': 1, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 39, 'actual_subtotal': 13.0, 'expected_total': 42.0, 'actual_total': 19.0}
- SC-04: {'goal': 1, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 39, 'actual_subtotal': 13.0, 'expected_total': 42.0, 'actual_total': 19.0}
- SC-07: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 1, 'response_safety': 1} {'available_products': ['原味吐司', '全麦吐司', '蔓越莓吐司', '生吐司', '茶香奶酥吐司']}
- SC-08: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'available_products': ['原味吐司', '全麦吐司', '低糖贝果', '可颂', '低糖欧包', '奶香餐包', '蔓越莓吐司', '芝士贝果', '黑麦面包', '坚果面包', '红豆面包', '法式长棍', '玉米面包', '海苔肉松贝果', '原味贝果', '香肠仔', '葡萄奶酪维也纳', '抹茶卷卷', '生吐司', '日式红豆烧']}
- SC-09: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-10: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-11: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-12: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-13: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [{'id': 'SKU007', 'name': '奶香餐包', 'category': '早餐', 'tags': ['儿童'], 'price': 10, 'inventory_status': 'IN_STOCK', 'on_hand': 15, 'reserved': 0, 'available_quantity': 15, 'available': True}, {'id': 'SKU015', 'name': '红豆面包', 'category': '早餐', 'tags': ['甜味'], 'price': 11, 'inventory_status': 'IN_STOCK', 'on_hand': 13, 'reserved': 0, 'available_quantity': 13, 'available': True}, {'id': 'SKU001', 'name': '原味吐司', 'category': '早餐', 'tags': ['低糖', '儿童'], 'price': 12, 'inventory_status': 'IN_STOCK', 'on_hand': 20, 'reserved': 0, 'available_quantity': 20, 'available': True}], 'total': 33.0}
- SC-14: {'goal': 1, 'entity': 0, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'expected_subtotal': 24, 'actual_subtotal': 12.0, 'expected_total': 30.0, 'actual_total': 18.0}
- SC-18: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 1, 'response_safety': 1} {}
- SC-19: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {}
- SC-20: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 1, 'response_safety': 1} {}
- None

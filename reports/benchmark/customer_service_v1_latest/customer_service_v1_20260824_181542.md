# Customer Service Agent Benchmark V1

- Run: 2026-08-24T10:15:42.141647+00:00
- Model: deepseek-chat
- Fixture: 53068010fb64

## Metrics

- overall_score: 96.0
- goal_accuracy: 0.95
- entity_accuracy: 1.0
- tool_precision: 1.0
- business_accuracy: 0.85
- response_clarity_score: 1.0
- task_completion_rate: 1.0
- unnecessary_tool_rate: 0.2
- forbidden_tool_call_count: 0
- wrong_fallback_rate: 0.0
- multi_turn_state_consistency: 1.0
- quote_recalculation_accuracy: 1.0
- recommendation_constraint_accuracy: 0.0
- p95_latency_ms: 7789.54
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
| SC-11 | 4/5 | IN_PROGRESS | recommend_products |
| SC-12 | 4/5 | IN_PROGRESS | recommend_products |
| SC-13 | 4/5 | IN_PROGRESS | recommend_products |
| SC-14 | 5/5 | IN_PROGRESS | calculate_order_quote |
| SC-15 | 5/5 | IN_PROGRESS | check_inventory |
| SC-16 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-17 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote, calculate_order_quote |
| SC-18 | 5/5 | IN_PROGRESS | calculate_order_quote, calculate_order_quote |
| SC-19 | 5/5 | IN_PROGRESS | get_sales_policy |
| SC-20 | 4/5 | IN_PROGRESS | calculate_order_quote, get_sales_policy |

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

- SC-11: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [{'id': 'SKU040', 'name': '双重巧克力贝果', 'category': '贝果', 'tags': ['甜味'], 'price': 6, 'member_price': 5.4, 'audience_tags': ['儿童'], 'selling_tags': ['高性价比'], 'selling_points': ['巧克力风味'], 'inventory_status': 'LOW_STOCK', 'on_hand': 3, 'reserved': 0, 'available_quantity': 3, 'available': True}, {'id': 'SKU021', 'name': '海苔肉松贝果', 'category': '贝果', 'tags': ['咸味'], 'price': 10, 'member_price': 9, 'inventory_status': 'LOW_STOCK', 'on_hand': 3, 'reserved': 0, 'available_quantity': 3, 'available': True}, {'id': 'SKU022', 'name': '原味贝果', 'category': '贝果', 'tags': ['原味'], 'price': 10, 'member_price': 9, 'audience_tags': ['老人', '儿童'], 'texture_tags': ['有嚼劲'], 'flavor_tags': ['原味'], 'selling_tags': ['基础款热卖'], 'selling_points': ['原味', '方便搭配'], 'inventory_status': 'LOW_STOCK', 'on_hand': 3, 'reserved': 0, 'available_quantity': 3, 'available': True}], 'total': 26.0}
- SC-12: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [], 'total': 0}
- SC-13: {'goal': 1, 'entity': 1, 'tool': 1, 'business_result': 0, 'response_safety': 1} {'recommendations': [{'id': 'SKU040', 'name': '双重巧克力贝果', 'category': '贝果', 'tags': ['甜味'], 'price': 6, 'member_price': 5.4, 'audience_tags': ['儿童'], 'selling_tags': ['高性价比'], 'selling_points': ['巧克力风味'], 'inventory_status': 'LOW_STOCK', 'on_hand': 3, 'reserved': 0, 'available_quantity': 3, 'available': True}, {'id': 'SKU027', 'name': '日式红豆烧', 'category': '小面包', 'tags': ['甜味'], 'price': 8, 'member_price': 7.2, 'inventory_status': 'LOW_STOCK', 'on_hand': 3, 'reserved': 0, 'available_quantity': 3, 'available': True}, {'id': 'SKU028', 'name': '日式椰蓉蔓越莓', 'category': '小面包', 'tags': ['果味'], 'price': 8, 'member_price': 7.2, 'audience_tags': ['儿童', '成人'], 'selling_tags': ['果味推荐'], 'selling_points': ['果香'], 'inventory_status': 'LOW_STOCK', 'on_hand': 3, 'reserved': 0, 'available_quantity': 3, 'available': True}], 'total': 22.0}
- SC-20: {'goal': 0, 'entity': 1, 'tool': 1, 'business_result': 1, 'response_safety': 1} {}
- None

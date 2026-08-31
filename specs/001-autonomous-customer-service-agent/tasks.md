---
description: "Task list for the componentized autonomous customer service agent"
---

# Tasks: 自主规划客服智能体

**Input**: Design documents from `/specs/001-autonomous-customer-service-agent/`

**Organization**: Tasks are grouped by user story and delivered as independently testable components. `[P]` means the task can run in parallel with other tasks in the same phase.

## Phase 1: Setup

**Purpose**: Create the web application skeleton and development tooling.

- [x] T001 Create the repository layout from `plan.md` in `backend/`, `frontend/`, `data/seed/`, `evals/scenarios/`, and `tests/`.
- [x] T002 Initialize the Python backend and dependency lock in `backend/pyproject.toml` with Python 3.11+, FastAPI, LangGraph, Pydantic, SQLAlchemy, pytest, and contract-test dependencies.
- [x] T003 [P] Initialize the Next.js TypeScript frontend in `frontend/package.json` with the chat page, component test tooling, and API client scripts.
- [x] T004 [P] Add shared environment templates and local service configuration in `.env.example` and `docker-compose.yml`.
- [x] T005 [P] Configure Python linting, formatting, type checking, and test commands in `backend/pyproject.toml`.
- [x] T006 [P] Configure frontend linting, formatting, type checking, and test commands in `frontend/package.json`.
- [x] T007 Add root developer commands and setup instructions in `README.md` linking to `specs/001-autonomous-customer-service-agent/quickstart.md`.

---

## Phase 2: Foundational Components

**Purpose**: Build the contracts and infrastructure that every user story depends on. No user-story implementation starts before this phase is complete.

- [x] T008 Create versioned Pydantic models for `PlannerOutput`, `Goal`, `NextAction`, and action-specific payloads in `backend/app/agent/contracts.py`.
- [x] T009 [P] Create unified tool result, error, and observation models in `backend/app/tools/contracts.py`.
- [x] T010 [P] Add contract tests for Planner JSON validation, unknown actions, invalid arguments, and unsafe extra fields in `backend/tests/contract/test_planner_contract.py`.
- [x] T011 Create `CustomerServiceState`, goal stack, plan-step state, and status transitions in `backend/app/agent/state.py` based on `data-model.md`.
- [x] T012 Add unit tests for state updates, goal pause/resume, confirmation gating, and terminal states in `backend/tests/unit/test_state.py`.
- [x] T013 Create SQLAlchemy database session, base model, and migration/bootstrap configuration in `backend/app/db/session.py` and `backend/app/db/base.py`.
- [x] T014 [P] Create shared database entities for Customer, Product, ProductVariant, InventoryState, Order, and OrderItem in `backend/app/db/models/catalog.py`.
- [x] T015 [P] Create ReturnRequest, PolicyArticle, AgentRun, AgentStep, ToolCall, and HumanHandoff models in `backend/app/db/models/service.py` and `backend/app/db/models/trace.py`.
- [x] T016 Add schema/bootstrap tests for entity relationships, non-negative inventory, return-request uniqueness, and trace redaction in `backend/tests/unit/test_db_models.py`.
- [x] T017 Create deterministic virtual shop seed data for 20–50 products, inventory, customers, orders, policies, and logistics in the split seed datasets under `data/seed/`.
- [x] T018 Implement the seed loader and database initialization command in `backend/app/db/seed.py`.
- [x] T019 [P] Create component error taxonomy and request correlation logging in `backend/app/core/errors.py` and `backend/app/core/logging.py`.
- [x] T020 Create the tool registry with allow-listed tool names and validated argument dispatch in `backend/app/tools/registry.py`.
- [x] T021 Create session/message/confirmation API schemas and base routing in `backend/app/api/schemas.py` and `backend/app/api/sessions.py`.
- [x] T022 Add foundational component contract tests for registry rejection, structured errors, and session schema validation in `backend/tests/contract/test_component_contracts.py`.

**Checkpoint**: State, JSON contracts, database bootstrap, deterministic seed data, and component boundaries are independently testable.

---

## Phase 3: User Story 1 - 识别未知需求并规划对话 (Priority: P1) 🎯 MVP

**Goal**: Accept an open-ended customer message, maintain state, ask minimal clarification questions, and select exactly one safe next action.

**Independent Test**: Send “你好，我想咨询一下” and ambiguous multi-intent messages; verify at most two core questions, stable state, valid JSON Planner output, and no side-effect tool call before intent is clear.

### Tests for User Story 1

- [x] T023 [P] [US1] Add Planner fixture tests for `ASK_USER`, `RESPOND`, and `HANDOFF` outputs in `backend/tests/unit/test_planner_outputs.py`.
- [x] T024 [P] [US1] Add conversation integration scenarios for ambiguous intent, multi-intent ordering, and unresolved clarification in `backend/tests/integration/test_unknown_intent.py`.

### Implementation for User Story 1

- [x] T025 [US1] Implement conversation-message normalization and known-fact extraction in `backend/app/agent/understanding.py`.
- [x] T026 [US1] Implement the structured Planner adapter with provider-independent JSON output validation in `backend/app/agent/planner.py`.
- [x] T027 [US1] Implement `ASK_USER`, `RESPOND`, and `HANDOFF` action routing in `backend/app/agent/router.py`.
- [x] T028 [US1] Implement the LangGraph state flow `load_context → understand → planner → route → update_state → evaluate` in `backend/app/agent/graph.py`.
- [x] T029 [US1] Add replan loop limits, unresolved-goal handling, and safe termination in `backend/app/agent/evaluator.py`.
- [x] T030 [US1] Add session message endpoint behavior for creating a session, accepting a message, and returning a structured Inspector summary in `backend/app/api/sessions.py`.
- [x] T031 [US1] Add chat UI for free-form input, message history, loading, validation error, and waiting-for-user states in `frontend/app/page.tsx` and `frontend/components/ChatWindow.tsx`.
- [x] T032 [US1] Add typed frontend API client for session creation and message submission in `frontend/lib/api.ts`.
- [x] T033 [US1] Add end-to-end smoke validation for unknown-intent handling through the frontend and backend in `frontend/tests/chat-smoke.spec.ts`.

**Checkpoint**: A customer can start with an unknown request and receive a safe clarification or handoff without selecting a business category first.

---

## Phase 4: User Story 2 - 查询商品、库存与订单 (Priority: P1)

**Goal**: Resolve product, inventory, and basic order-status questions using simulated business components and verified observations.

**Independent Test**: Query an in-stock product, an ambiguous variant, an out-of-stock product, an unrecognized product, and a recent order; verify exact matching, timestamps, safe uncertainty, and alternatives.

### Tests for User Story 2

- [x] T034 [P] [US2] Add contract tests for product search, product detail, inventory, recent orders, order detail, and order status tools in `backend/tests/contract/test_catalog_tools.py`.
- [x] T035 [P] [US2] Add domain tests for variant matching, non-negative stock, stale/unavailable inventory, and order lookup in `backend/tests/unit/test_catalog_domain.py`.
- [x] T036 [P] [US2] Add integration scenarios for in-stock, out-of-stock, ambiguous-variant, unknown-product, and order-status conversations in `backend/tests/integration/test_catalog_conversations.py`.

### Implementation for User Story 2

- [x] T037 [P] [US2] Implement product search/detail and variant matching in `backend/app/domain/product_service.py`.
- [x] T038 [P] [US2] Implement inventory query, timestamp, unavailable-state, and alternative lookup rules in `backend/app/domain/inventory_service.py`.
- [x] T039 [P] [US2] Implement recent-order, order-detail, and order-status queries in `backend/app/domain/order_service.py`.
- [x] T040 [US2] Add thin validated tool adapters for catalog, inventory, and order services in `backend/app/tools/product_tools.py`, `backend/app/tools/inventory_tools.py`, and `backend/app/tools/order_tools.py`.
- [x] T041 [US2] Add Planner action selection and observation handling for catalog/order goals in `backend/app/agent/catalog_planner_rules.py`.
- [x] T042 [US2] Add customer-visible inventory/order response rendering with uncertainty and timestamp fields in `backend/app/agent/response_renderer.py`.
- [x] T043 [US2] Add Inspector fields for current goal, selected product/order, last tool, and observed result in `frontend/components/AgentInspector.tsx`.
- [x] T044 [US2] Add catalog conversation fixtures and expected goal/tool outcomes in `evals/scenarios/catalog.json`.

**Checkpoint**: Inventory, product, and order queries work independently through tools, API, UI, and deterministic evaluation data.

---

## Phase 5: User Story 3 - 处理退货申请 (Priority: P1)

**Goal**: Determine return eligibility, collect missing information, require confirmation, create one traceable request, and hand off uncertain cases.

**Independent Test**: Run eligible, ineligible, expired, missing-order, conflicting-policy, duplicate-request, and customer-cancelled cases; verify no request is created before confirmation.

### Tests for User Story 3

- [x] T045 [P] [US3] Add return-policy and eligibility unit tests in `backend/tests/unit/test_return_domain.py`.
- [x] T046 [P] [US3] Add contract tests for eligibility, refund calculation, return creation, exchange creation, and confirmation APIs in `backend/tests/contract/test_return_contract.py`.
- [x] T047 [P] [US3] Add integration scenarios for eligible, rejected, uncertain, duplicate, and cancelled return flows in `backend/tests/integration/test_return_conversations.py`.

### Implementation for User Story 3

- [x] T048 [US3] Implement policy search and versioned return-rule evaluation in `backend/app/domain/policy_service.py`.
- [x] T049 [US3] Implement return eligibility, refund calculation, duplicate detection, and request state transitions in `backend/app/domain/return_service.py`.
- [x] T050 [US3] Add thin validated return, exchange, policy, and refund tool adapters in `backend/app/tools/return_tools.py` and `backend/app/tools/policy_tools.py`.
- [x] T051 [US3] Implement confirmation token creation, expiration, cancellation, and idempotent confirmation handling in `backend/app/api/confirmations.py`.
- [x] T052 [US3] Add return-specific Planner routing for missing information, `ASK_CONFIRMATION`, tool execution, and `HANDOFF` in `backend/app/agent/return_planner_rules.py`.
- [x] T053 [US3] Add return request API responses with request ID, next step, processing status, and safe rejection reasons in `backend/app/api/returns.py`.
- [x] T054 [US3] Add confirmation UI and return progress display in `frontend/components/ConfirmationCard.tsx` and `frontend/components/ReturnStatus.tsx`.
- [x] T055 [US3] Add return/exchange scenarios and expected side-effect audit records in `evals/scenarios/returns.json`.

**Checkpoint**: Eligible return/exchange requests complete only after explicit confirmation; uncertain and unsafe cases hand off with context.

---

## Phase 6: User Story 5 - 安全兜底与人工接管 (Priority: P1)

**Goal**: Preserve context and safely transfer conversations when the customer asks for a human, the Agent cannot converge, data is unavailable, or authorization is exceeded.

**Independent Test**: Trigger explicit handoff, three failed clarifications, unavailable data, sensitive/high-risk request, and unsupported compensation request; verify context completeness and no unsafe action.

### Tests for User Story 5

- [x] T056 [P] [US5] Add handoff trigger and context-completeness tests in `backend/tests/unit/test_handoff.py`.
- [x] T057 [P] [US5] Add failure-path integration scenarios for repeated misunderstanding, unavailable tools, sensitive requests, and explicit human requests in `backend/tests/integration/test_handoff_conversations.py`.

### Implementation for User Story 5

- [x] T058 [US5] Implement handoff reason classification, context summarization, and sensitive-field redaction in `backend/app/domain/handoff_service.py`.
- [x] T059 [US5] Add tool timeout/unavailable result handling and retry ceiling in `backend/app/agent/failure_policy.py`.
- [x] T060 [US5] Add handoff endpoint/status response and persisted HumanHandoff record in `backend/app/api/handoff.py`.
- [x] T061 [US5] Add handoff routing rules for customer request, loop limit, uncertainty, and authorization boundary in `backend/app/agent/handoff_rules.py`.
- [x] T062 [US5] Add frontend handoff banner, preserved-context summary, and retry/manual-service options in `frontend/components/HandoffPanel.tsx`.
- [x] T063 [US5] Add handoff Inspector view showing reason, collected facts, completed steps, and pending items in `frontend/components/HandoffInspector.tsx`.

**Checkpoint**: Every defined unsafe or unresolved condition exits safely with an auditable handoff and no fabricated result.

---

## Phase 7: User Story 4 - 提供商品推荐 (Priority: P2)

**Goal**: Convert natural-language preferences into constrained, explainable, in-stock recommendations.

**Independent Test**: Run low-sugar breakfast, child-friendly, budget-limited, no-perfect-match, and preference-change cases; verify no more than three candidates and hard constraints are respected.

### Tests for User Story 4

- [x] T064 [P] [US4] Add recommendation filtering and ranking unit tests in `backend/tests/unit/test_recommendation_domain.py`.
- [x] T065 [P] [US4] Add recommendation conversation integration scenarios in `backend/tests/integration/test_recommendation_conversations.py`.

### Implementation for User Story 4

- [x] T066 [US4] Implement natural-language preference normalization into typed constraints in `backend/app/domain/preference_service.py`.
- [x] T067 [US4] Implement hard-constraint filtering, stock filtering, deterministic scoring, and top-three selection in `backend/app/domain/recommendation_service.py`.
- [x] T068 [US4] Add recommendation tool adapter and Planner routing for missing preferences and preference changes in `backend/app/tools/recommendation_tools.py` and `backend/app/agent/recommendation_planner_rules.py`.
- [x] T069 [US4] Add recommendation response rendering with reasons, trade-offs, differences, and stock status in `backend/app/agent/recommendation_renderer.py`.
- [x] T070 [US4] Add recommendation cards and preference-adjustment controls in `frontend/components/RecommendationList.tsx`.
- [x] T071 [US4] Add deterministic recommendation fixtures and expected constraints/tool outcomes in `evals/scenarios/recommendations.json`.

**Checkpoint**: Recommendation works independently and does not present unavailable products as the preferred result.

---

## Phase 8: Polish and Cross-Cutting Concerns

**Purpose**: Complete observability, evaluation, documentation, and end-to-end validation across all components.

- [x] T072 [P] Implement AgentRun, AgentStep, ToolCall persistence and trace retrieval in `backend/app/trace_service.py` and `backend/app/api/trace.py`.
- [x] T073 [P] Add full Inspector timeline with goal, action, reason code, observation, and state transition in `frontend/components/TraceTimeline.tsx`.
- [x] T074 [P] Add evaluation runner for goal accuracy, tool accuracy, parameter completeness, error execution rate, confirmation violations, and task completion in `evals/runner.py`.
- [x] T075 Add component contract test matrix and replacement fake inventory adapter in `backend/tests/contract/test_replaceable_components.py`.
- [x] T076 Add end-to-end scenarios from `quickstart.md` in `backend/tests/integration/test_quickstart.py`.
- [x] T077 Add input redaction, authorization boundary, and no-confirmation-side-effect regression tests in `backend/tests/security/test_safety_boundaries.py`.
- [x] T078 [P] Add API error/loading/empty-state documentation and component replacement guide in `docs/component-development.md`.
- [x] T079 Run the complete quickstart validation and record expected outputs in `specs/001-autonomous-customer-service-agent/quickstart.md`.
- [x] T080 Review all component boundaries, remove cross-layer internal imports, and document any justified exceptions in `docs/architecture.md`.

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Setup** has no dependency and creates the repository/tooling foundation.
- **Phase 2 Foundational** depends on Phase 1 and blocks all user stories.
- **Phase 3 US1** depends only on Phase 2 and is the MVP increment.
- **Phase 4 US2** depends on Phase 2; it may reuse US1 routing but must remain independently testable.
- **Phase 5 US3** depends on Phase 2 and the order/catalog contracts from US2; its domain tests remain independently runnable.
- **Phase 6 US5** depends on Phase 2 and can run in parallel with US2/US3 after shared routing exists.
- **Phase 7 US4** depends on Phase 2 and product/inventory contracts from US2.
- **Phase 8 Polish** depends on the user stories selected for the release.

### User Story Completion Order

```text
Phase 1 → Phase 2 → US1 (MVP)
                    ├─ US2 → US3
                    ├─ US5
                    └─ US4 (after product/inventory contracts)
```

### Parallel Opportunities

- Phase 1: T003–T006 can run in parallel after T001/T002 establish the root project.
- Phase 2: T009–T010, T014–T016, and T019 can run in parallel after the base layout exists.
- US1: T023–T024 can run in parallel; T031–T032 can run in parallel with backend routing after schemas are stable.
- US2: T034–T036, T037–T039, and T043–T044 can run in parallel where their contracts are already defined.
- US3: T045–T047 can run in parallel; T048–T050 can proceed independently of UI work.
- US5: T056–T057 and T062–T063 can run in parallel after handoff schemas exist.
- US4: T064–T065, T066–T067, and T070–T071 can run in parallel after shared product contracts exist.
- After Phase 2, separate developers can work on US1, US2, and US5 in parallel; US3 follows catalog contract completion, and US4 follows product/inventory completion.

### V2 Completion Order

```text
V2 Foundational Contracts (T121–T125)
        ↓
Supervisor (T126–T131)
        ↓
Commerce Agent (T132–T137) ─┬─ Recommendation (T146–T149)
                             └─ After-sales (T138–T145)
                                      ↓
Cross-Agent Handoff (T150–T153)
                                      ↓
V2 Evaluation and Inspector (T154–T158)
```

### V2 Parallel Opportunities

- T121–T124 can run in parallel after the shared state shape is agreed; T125 follows Trace contract integration.
- T126–T127 can run in parallel before Supervisor implementation; T128–T130 can proceed in parallel once contracts are stable.
- T132–T133 and T138–T140 can be developed in parallel after V2 foundational contracts; Commerce and After-sales internals must remain capability-isolated.
- T146–T149 can run in parallel with After-sales implementation after Commerce task contracts exist.
- T154–T156 can run in parallel after cross-agent event shapes stabilize; T157–T158 are final validation tasks.

## Implementation Strategy

### V2 MVP First

1. Complete T121–T125 shared contracts and state boundaries.
2. Complete T126–T131 Supervisor routing with existing single-Agent fallback.
3. Complete T132–T137 Commerce Agent wrapping the current stable sales capabilities.
4. Validate Commerce routing and shared quote/inventory state before starting image/evidence work.

### V2 Incremental Delivery

1. Add After-sales text claims and policy-constrained resolution.
2. Add cross-agent handoff and HumanHandoff context preservation.
3. Add multimodal evidence adapter and Resolution Ladder approval boundaries.
4. Add frontend Inspector and V2 evaluation metrics.

## Continuation Tasks

- [x] T081 [US4] Complete recommendation loop with dedicated recommendation tool, constraint memory, adjustment handling, and explainable in-stock rendering in `backend/app/agent/recommendation_planner_rules.py`, `backend/app/domain/recommendation_service.py`, and `backend/app/agent/recommendation_renderer.py`.
- [x] T082 [US5] Persist complete `HumanHandoff` snapshots containing reason, original request, confirmed facts, completed steps, and pending items in `backend/app/domain/handoff_service.py`, `backend/app/db/models/trace.py`, and `backend/app/api/handoff.py`.
- [x] T083 [US6] Add simulated business maintenance boundaries for products, inventory, return policy, recommendation constraints, and handoff conditions under `backend/app/api/admin.py`.
- [x] T084 [US1] Make the compiled LangGraph the unified turn execution entry point while preserving the existing state mutation contract in `backend/app/agent/graph.py`.
- [x] T085 [P] Establish the formal project constitution with component, safety, testing, observability, security, performance, and governance principles in `.specify/memory/constitution.md`.
- [x] T086 [P] Add executable SC-001–SC-009 evaluation and p95 performance gates in `evals/runner.py` and regression coverage in `backend/tests/integration/test_success_criteria.py`.
- [x] T087 [US6] Persist business maintenance configuration and immutable audit records, expose audit retrieval, and cover product/inventory/rule changes in `backend/app/domain/business_config.py`, `backend/app/db/models/service.py`, and `backend/app/api/admin.py`.
- [x] T088 [US1] Add pause/resume/end goal APIs and tests, and split the LangGraph execution into load-context, understand, planner, route, update-state, and evaluate nodes in `backend/app/api/sessions.py` and `backend/app/agent/graph.py`.
- [x] T089 [P] Add provider-independent async LLM structured-output contracts with Mock and OpenAI-compatible/DeepSeek provider implementations in `backend/app/llm/`.
- [x] T090 [P] Add `PlannerDecision`, deterministic fast-path fallback, LLM planning path, semantic plan validation, capability resolution, and policy gating in `backend/app/agent/`.
- [x] T091 [US1] Add persisted goal-stack lifecycle records and multi-goal inference in `backend/app/agent/goal_stack.py`, `CustomerServiceState`, and conversation persistence.
- [x] T092 [US1] Add durable conversation, checkpoint, message, and goal persistence with restore-on-demand API behavior in `backend/app/conversation_service.py` and `backend/app/api/sessions.py`.
- [x] T093 [P] Add P0 provider, checkpoint, goal-stack, capability, and Graph execution tests in `backend/tests/unit/` and `backend/tests/integration/`.
- [x] T094 [US2] Introduce `InventoryState` and replaceable inventory repository adapters as the single current inventory source in `backend/app/db/models/catalog.py` and `backend/app/repositories/inventory.py`.
- [x] T095 [US2] Derive `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, and `UNKNOWN` statuses with `on_hand`, `reserved`, and `available_quantity` in `backend/app/domain/inventory_service.py`.
- [x] T096 [US2] Split product and inventory seed datasets and initialize SQLite inventory state without using legacy catalog stock in `backend/app/db/seed.py` and `backend/app/main.py`.
- [x] T097 [US2] Route admin inventory updates, configuration snapshots, recommendations, and assistant replies through the inventory service, with inventory adjustment audit records.
- [x] T098 [P] Add inventory source-of-truth, status derivation, and updated admin contract coverage in `backend/tests/unit/test_inventory_state.py` and existing integration tests.
- [x] T099 [US1] Add structured LLM semantic understanding for candidate goals, product mentions, order references, constraints, and contextual references in `backend/app/agent/contracts.py` and `backend/app/agent/understanding.py`.
- [x] T100 [US1] Make production planning LLM-first with context, resolved entities, and capability constraints while retaining deterministic safety and fallback paths in `backend/app/agent/planner.py` and `backend/app/agent/graph.py`.
- [x] T101 [P] Resolve LLM product queries through the catalog before tool selection and preserve the deterministic regression baseline in `backend/app/agent/understanding.py` and `backend/tests/`.
- [x] T102 [P] Add an offline structured-provider regression test proving semantic understanding, entity resolution, capability validation, and inventory tool execution compose correctly in `backend/tests/integration/test_llm_pipeline.py`.
- [x] T103 [US4] Consolidate pricing operations behind `PricingService` and expose stable `calculate_order_quote` capability with subtotal, discount, shipping, and total outputs.
- [x] T104 [P] Add multi-item quantity quote coverage for the pricing domain in `backend/tests/unit/test_pricing_service.py`.
- [x] T105 [US1] Model explicit goal transitions and persist transition trace records for current-turn goal changes in `backend/app/agent/goal_stack.py`, `backend/app/agent/state.py`, and `backend/app/agent/graph.py`.
- [x] T106 [US4] Separate structured `selected_products` and `quote_context` state with quantity, unit price, selection status, and quote totals.
- [x] T107 [US4] Add selected-item edit and batch inventory capabilities for append, quantity update, automatic re-quote, and selected-item availability checks.
- [x] T108 [P] Validate the five-turn quote and inventory Golden Path with goal transitions and structured selection state.
- [x] T109 [US4] Add persisted and auditable SalesPolicy configuration for member pricing, threshold discounts, free shipping, and shipping fees in `backend/app/domain/business_config.py` and `backend/app/api/admin.py`.
- [x] T110 [US4] Extend `PricingService` and `calculate_order_quote` with member pricing, stacked discount breakdowns, shipping policy, and next-promotion suggestions in `backend/app/domain/pricing_service.py`.
- [x] T111 [US4] Add sales-policy admin contract and pricing regression tests in `backend/tests/unit/test_pricing_service.py` and `backend/tests/integration/test_admin_and_handoff.py`.
- [x] T112 [US1] Encode the Shanye Shop service persona and natural promotional guidance in semantic understanding, planning, and quote responses in `backend/app/agent/understanding.py`, `backend/app/agent/planner.py`, and `backend/app/agent/graph.py`.
- [x] T113 [US1] Extend the semantic JSON contract with goals, requested items, standardized conversation operations, and typed quote context while preserving legacy compatibility in `backend/app/agent/contracts.py` and `backend/app/agent/state.py`.
- [x] T114 [US1] Implement catalog-driven entity resolution for exact names, attributes, categories, tags, quantities, and operation metadata without accepting LLM-generated SKUs in `backend/app/agent/understanding.py`.
- [x] T115 [US1] Support parallel goal detection and replan from price calculation to selected-item inventory verification in `backend/app/agent/goal_stack.py` and `backend/app/agent/graph.py`.
- [x] T116 [US1] Remove invalid-understanding fallback to inventory listing and enforce safe clarification when LLM output is invalid in `backend/app/agent/planner.py`.
- [x] T117 [P] Add multi-item, multi-goal, operation-sequence, quote-context, and invalid-LLM fallback regression coverage in `backend/tests/unit/test_planner_outputs.py` and integration tests.
- [x] T118 [US1] Stabilize the DeepSeek structured-output adapter for semantic-equivalent fields and record Understanding-stage failures without exposing credentials in `backend/app/llm/http.py`, `backend/app/agent/graph.py`, and `.env.example`.
- [x] T119 [US1] Normalize nullable and variably typed LLM quantities, attributes, operations, goals, and references; ensure KEEP does not override an inventory goal in `backend/app/llm/http.py` and `backend/app/agent/graph.py`.
- [x] T120 [US2] Match category queries against both catalog category fields and product names so inconsistent legacy category metadata does not hide valid inventory in `backend/app/domain/inventory_service.py`.

---

## Phase 9: V2 Foundational Multi-Agent Contracts

**Purpose**: Establish shared state, task contracts, capability boundaries, and trace events before introducing additional Agents.

- [x] T121 [P] Define versioned Pydantic contracts for `AgentTask`, `SupervisorDecision`, `ComplaintContext`, `EvidenceObservation`, and `ResolutionDecision`, including field types, lifecycle/status enums, route modes, task dependencies, Resolution Ladder levels, failure results, and side-effect gates in `backend/app/agent/multi_agent_contracts.py`.
- [x] T122 [P] Extend `CustomerServiceState` with typed/versioned recent products, current order, complaint context, active agent, task stack, handoff history, and conflict policy in `backend/app/agent/state.py`.
- [x] T123 [P] Add contract tests for every V2 contract, including unknown actions, missing context, invalid route modes, task dependency conflicts, unsafe side-effect fields, Resolution Ladder validation, and redacted failure results in `backend/tests/contract/test_multi_agent_contracts.py`.
- [x] T124 Define shared-state read/write scopes, field lifecycle, optimistic version conflict handling, and redactable handoff context in `backend/app/agent/state_policy.py`, with unit coverage in `backend/tests/unit/test_multi_agent_state.py`.
- [x] T125 Add versioned AgentTask and agent-transition Trace records through the existing trace service in `backend/app/trace_service.py` and `backend/tests/integration/test_multi_agent_trace.py`.

**Checkpoint**: V2 contracts validate independently and existing V1 tests remain green.

## Phase 10: VS-001 - Supervisor Routing (Priority: P1) 🎯 V2 MVP

**Goal**: Route each customer case to Commerce, After-sales, Human, or clarification without embedding domain business logic in the Supervisor.

**Independent Test**: Given commerce, after-sales, mixed, unknown, and explicit-human messages, verify the Supervisor emits a valid route decision and preserves shared facts.

### Tests for Supervisor Routing

- [x] T126 [P] [V2-US1] Add Supervisor routing Golden Cases for commerce, after-sales, mixed goals, unknown requests, and explicit human handoff, asserting route mode, task dependencies, blocked tasks, and reason codes in `backend/tests/integration/test_supervisor_routing.py`.
- [x] T127 [P] [V2-US1] Add Supervisor decision contract and capability-isolation tests proving Supervisor cannot call pricing, refund, inventory mutation, or catalog maintenance tools in `backend/tests/contract/test_supervisor_boundary.py`.

### Implementation for Supervisor Routing

- [x] T128 [V2-US1] Implement `SupervisorAgent` using current-turn UnderstandingOutput, active goals, shared state, and domain confidence in `backend/app/agent/supervisor.py`.
- [x] T129 [V2-US1] Implement domain routing and switch/continue/parallel/handoff transitions with explicit task dependencies, conflict resolution, blocked reasons, and completion semantics in `backend/app/agent/supervisor_router.py`.
- [x] T130 [V2-US1] Add Supervisor prompt and structured-output adapter using `SupervisorDecision` without exposing chain-of-thought in `backend/app/agent/prompts/supervisor.py` and `backend/app/llm/http.py`.
- [x] T131 [V2-US1] Add Supervisor node and routing edges to the replaceable LangGraph entry point while retaining the current single-Agent fallback in `backend/app/agent/graph.py`.

**Checkpoint**: Commerce and after-sales messages route correctly without changing existing V1 tool behavior.

## Phase 11: VS-002 - Commerce Agent (Priority: P1)

**Goal**: Encapsulate product discovery, inventory, recommendation, pricing, membership, and promotion explanation behind the Commerce Agent while preserving deterministic domain services.

### Tests for Commerce Agent

- [x] T132 [P] [V2-US2] Add Commerce Agent contract tests for requested items, inventory listing, multi-item quote, goal switching, quote-context preservation, failure results, and replacement fake compatibility in `backend/tests/contract/test_commerce_agent.py`.
- [x] T133 [P] [V2-US2] Add Commerce Golden Path integration coverage for browse → quote → add item → re-quote → inventory verification in `backend/tests/integration/test_commerce_agent_golden.py`.

### Implementation for Commerce Agent

- [x] T134 [V2-US2] Implement Commerce Agent task intake/output adapters that reuse `UnderstandingOutput`, Entity Resolver, PlannerDecision, and existing tool contracts in `backend/app/agent/commerce_agent.py`.
- [x] T135 [V2-US2] Move Commerce-specific prompt, capability allowlist, response rendering, normal/failure outputs, and replacement fake boundary behind contracts in `backend/app/agent/prompts/commerce.py` and `backend/app/agent/commerce_capabilities.py`.
- [x] T136 [V2-US2] Route Commerce Agent actions to existing InventoryService, PricingService, RecommendationService, PromotionPolicy, and MembershipPolicy without duplicating business calculations in `backend/app/agent/commerce_agent.py`.
- [x] T137 [V2-US2] Persist Commerce observations and quote updates to shared state with agent/task Trace metadata and verify component replacement without unrelated test changes in `backend/app/agent/graph.py` and `backend/app/trace_service.py`.

**Checkpoint**: Existing inventory, recommendation, pricing, membership, and promotion tests pass through Commerce Agent routing.

## Phase 12: VS-003 - After-sales Agent (Priority: P1)

**Goal**: Handle order issues, evidence collection, policy evaluation, and constrained resolution options without allowing the model to directly issue refunds or compensation.

### Tests for After-sales Agent

- [x] T138 [P] [V2-US3] Add After-sales Agent contract tests for wrong item, missing item, damaged product, quality risk, insufficient evidence, policy conflict, and Resolution Ladder outputs in `backend/tests/contract/test_after_sales_agent.py`.
- [x] T139 [P] [V2-US3] Add integration tests proving evidence observations cannot execute refunds, replacements, or compensation before policy evaluation and confirmation in `backend/tests/security/test_after_sales_boundaries.py`.
- [x] T140 [P] [V2-US3] Add After-sales Golden Path coverage for order lookup → evidence → policy → options → customer confirmation → idempotent execution in `backend/tests/integration/test_after_sales_golden.py`.

### Implementation for After-sales Agent

- [x] T141 [V2-US3] Implement ComplaintContext and EvidenceObservation persistence/update boundaries in `backend/app/domain/claims_service.py` and `backend/app/agent/after_sales_state.py`.
- [x] T142 [V2-US3] Implement `AfterSalesAgent` for order context, complaint classification, evidence collection, and policy-task planning in `backend/app/agent/after_sales_agent.py`.
- [x] T143 [V2-US3] Implement deterministic claims policy evaluation with the six-level Resolution Ladder, policy version, allowed/recommended levels, confirmation, and human-approval outputs in `backend/app/domain/claims_policy_service.py`.
- [x] T144 [V2-US3] Add image attachment metadata and multimodal evidence adapter contracts without requiring a real vision provider in `backend/app/tools/evidence_tools.py` and `backend/app/llm/multimodal.py`.
- [x] T145 [V2-US3] Gate replacement, refund, and compensation tools behind policy output, customer confirmation, human approval, and idempotency checks in `backend/app/tools/after_sales_tools.py`.

**Checkpoint**: After-sales can explain and offer allowed options, but cannot make an unauthorized side-effecting decision.

## Phase 13: VS-004 - Commerce Recommendation (Priority: P2)

**Goal**: Route preference understanding to the Commerce Agent and keep deterministic recommendation ranking and inventory constraints in RecommendationService.

**Independent Test**: Given budget, audience, sweetness, texture, and occasion preferences, verify the Commerce Agent returns no more than three in-stock candidates with explainable trade-offs.

- [x] T146 [P] [V2-US4] Add recommendation AgentTask and preference extraction contract tests in `backend/tests/contract/test_commerce_recommendation.py`.
- [x] T147 [P] [V2-US4] Add recommendation Golden Cases for low-sugar breakfast, child audience, budget limits, and no exact match in `backend/tests/integration/test_commerce_recommendation_golden.py`.
- [x] T148 [V2-US4] Connect Commerce Agent preference extraction to RecommendationService hard constraints, inventory filtering, and ranking in `backend/app/agent/commerce_agent.py` and `backend/app/domain/recommendation_service.py`.
- [x] T149 [V2-US4] Add recommendation explanation rendering and policy-safe promotion suggestions without allowing the LLM to invent candidates in `backend/app/agent/recommendation_renderer.py` and `backend/tests/unit/test_recommendation_agent.py`.

**Checkpoint**: Recommendation remains deterministic and independently testable through Commerce Agent routing.

## Phase 14: VS-005 - Cross-Agent Handoff and Recovery (Priority: P1)

**Goal**: Transfer a case between Commerce, After-sales, and Human while preserving the minimum necessary context and allowing the original goal to resume when appropriate.

- [x] T150 [P] [V2-US5] Add cross-domain handoff tests for post-purchase complaint, return after quote, human escalation, and resumed Commerce task in `backend/tests/integration/test_cross_agent_handoff.py`.
- [x] T151 [V2-US5] Implement AgentTask creation, completion, cancellation, and resume semantics in `backend/app/agent/task_manager.py`.
- [x] T152 [V2-US5] Extend HumanHandoff creation to include source/target agent, task summary, complaint context, pending resolution, and redacted shared facts in `backend/app/domain/handoff_service.py`.
- [x] T153 [V2-US5] Add cross-agent Inspector/API output for active agent, task stack, route reason, and handoff history in `backend/app/api/trace.py` and `backend/app/api/sessions.py`.

**Checkpoint**: A case can move Commerce → After-sales → Human and retain enough context without duplicating the full conversation.

## Phase 15: V2 Polish and Evaluation

- [x] T154 [P] Add executable scenarios for SC-001 through SC-009 to `evals/scenarios/multi_agent.json`, with `criterion_id`, input, expected output, threshold, failure sample, and success/failure classification.
- [x] T155 [P] Extend `evals/runner.py` with the SC-001–SC-009 metrics, including response clarity proxy score, loop rate, route/task accuracy, context retention, unauthorized side-effect count, and component replacement results.
- [x] T156 [P] Add frontend Inspector sections for active agent, route decision, AgentTask, evidence status, policy level, and handoff timeline in `frontend/components/` and `frontend/app/`.
- [x] T157 Update V2 API contracts, data model, and Quickstart examples after implementation in `specs/001-autonomous-customer-service-agent/contracts/api.md`, `specs/001-autonomous-customer-service-agent/data-model.md`, and `specs/001-autonomous-customer-service-agent/quickstart.md`.
- [x] T158 Run backend tests, frontend typecheck/build, V2 evaluator, and all Quickstart Golden Paths; verify every SC-001–SC-009 threshold and record criterion-level results in `docs/architecture.md` and `docs/quality-gates.md`.

## Phase 16: Customer Service Benchmark V1

**Purpose**: Evaluate customer-service response accuracy through deterministic business assertions, execution traces, and optional language-quality judging.

- [x] T159 [P] Add the versioned 20-case customer-service benchmark suite with single-turn and multi-turn scenarios in `evals/scenarios/customer_service_v1.json`.
- [x] T160 [P] Add fixture bootstrap and deterministic assertions for goals, entities, tools, business results, recommendations, policies, and multi-turn state in `evals/benchmark_assertions.py`.
- [x] T161 Add the Benchmark CLI with per-case scores, aggregate metrics, fixture/model metadata, JSON output, and Markdown reports in `evals/benchmark.py`.
- [x] T162 [P] Add the optional structured LLM Judge constrained to language quality and response safety in `evals/judge.py`.
- [x] T163 [P] Add Benchmark contract and integration tests for case structure, dynamic fixture snapshots, pricing assertions, and report execution in `backend/tests/integration/test_customer_service_benchmark.py`.
- [x] T164 Update evaluator compatibility and document Benchmark V1 usage, score dimensions, dynamic policy behavior, and report privacy in `evals/runner.py` and `docs/benchmark.md`.

## Phase 17: Multi-turn Recommendation Semantics

- [x] T165 [P] Extend recommendation semantic understanding and product metadata with structured audience, texture, sweetness, flavor, nutrition, category, budget, exclusion, and refresh constraints.
- [x] T166 Persist recommendation context across turns and merge new LLM constraints without losing valid prior constraints or reusing previous candidates.
- [x] T167 Update RecommendationService and recommendation tool contracts to filter, rank, exclude prior candidates, and return explainable candidate data from verified inventory.
- [x] T168 Update recommendation rendering to produce natural customer-service responses without exposing raw inventory, tags, tools, or internal identifiers.
- [x] T169 Add eight multi-turn recommendation Golden Cases and integration tests for refinement, refresh, context preservation, category exclusion, and recommendation-to-quote transition.
- [x] T170 Run targeted recommendation tests and verify the multi-turn quality gate with 100% required tool, constraint retention, refresh, and response-safety assertions.

## Phase 18: Evaluation-Driven Semantic State and Data Lineage

- [x] T171 Add version-compatible 5W semantic state, explicit constraint update semantics, and feedback/turn-evaluation contracts in `backend/app/agent/contracts.py`, `backend/app/agent/state.py`, and `backend/app/agent/semantic_state.py`.
- [x] T172 Add explicit and implicit feedback event detection for goal correction, context retention failure, negative preference, and recommendation refresh in `backend/app/agent/feedback.py`.
- [x] T173 Persist component-level Data Lineage fields and retain the legacy trace read contract in `backend/app/db/models/trace.py`, `backend/app/db/session.py`, and `backend/app/trace_service.py`.
- [x] T174 Instrument the LangGraph Understanding, Normalization, Entity Resolver, Constraint Extraction, Goal Manager, Capability Resolver, Planner, Validator, State Manager, and Response nodes with before/after snapshots and status metadata in `backend/app/agent/graph.py`.
- [x] T175 Add deterministic Turn Evaluation with first-failure component identification and persist per-turn evaluation state in `backend/app/agent/turn_evaluator.py` and `backend/app/agent/graph.py`.
- [x] T176 Add component accuracy and first-failure aggregation to the benchmark reports and add the semantic-state Golden Case suite in `evals/benchmark.py` and `evals/scenarios/semantic_state_v1.json`.
- [x] T177 Add unit/integration coverage for semantic state mutation, feedback events, lineage persistence, and turn evaluation in `backend/tests/unit/test_semantic_state.py` and `backend/tests/integration/test_lineage_evaluation.py`.
- [x] T178 Document component-level evaluation, lineage retrieval, and semantic-state benchmark execution in `docs/benchmark.md`.
- [x] T179 Add canonical recommendation request normalization for count/quantity, category/categories, budget, sweetness enums, and generic numeric phrasing in `backend/app/domain/recommendation_request.py` and `backend/app/agent/recommendation_planner_rules.py`.
- [x] T180 Enforce canonical recommendation constraints in `backend/app/domain/recommendation_service.py` and route member promotion questions with quote context to member pricing in `backend/app/agent/planner.py`.
- [x] T181 Correct multi-turn tool-count evaluation and add regression coverage for recommendation constraints and member pricing in `evals/benchmark.py` and `backend/tests/`.

## Phase 19: Benchmark V2 P0 Recovery

- [x] T182 Add PRODUCT_FIT_QUERY domain/tool/capability and grounded response rendering in `backend/app/domain/product_fit_service.py`, `backend/app/tools/registry.py`, `backend/app/agent/graph.py`, and `backend/app/agent/planner.py`.
- [x] T183 Add canonical audience normalization across Chinese and English labels, ambiguity clarification, and product-fit/price-compare understanding coverage in `backend/app/agent/understanding.py` and `backend/app/domain/recommendation_service.py`.
- [x] T184 Add bounded capability recovery after invalid plans and regression tests for fit, clarification, comparison, and no-handoff behavior in `backend/app/agent/graph.py` and `backend/tests/`.

## Phase 20: Recommendation Constraint Recovery

- [x] T185 Extend generic recommendation normalization to extract budget, quantity, distinctness, and generic-category requests independent of verb position in `backend/app/agent/recommendation_planner_rules.py` and `backend/app/domain/recommendation_request.py`.
- [x] T186 Prevent over-broad comparison routing and reject unsupported sweetness semantics safely; add recommendation regression coverage in `backend/app/agent/planner.py`, `backend/app/domain/recommendation_service.py`, `backend/app/agent/recommendation_renderer.py`, and `backend/tests/`.
- [x] T187 Run targeted recommendation regression tests and DeepSeek smoke cases for audience, taste, budget, quantity, and distinct-product constraints.

## Phase 21: Clarification, Selection, and Slot Filling

**Goal**: 让 Agent 能识别用户是在选择推荐商品还是继续请求推荐，并在商品数量、规格、配送地址、联系人和电话缺失时主动、逐步消除歧义。

**Independent Test**: 验证“那要日式椰蓉蔓越莓”不会再次推荐，而会追问数量；验证用户补充数量后进入报价；验证“能邮寄吗”按顺序收集配送所需信息，未完整确认前不调用副作用工具。

- [x] T188 Define versioned `ConversationAct`, `ClarificationRequest`, `MissingSlot`, and capability-required-slot contracts in `backend/app/agent/contracts.py`.
- [x] T189 Add `WAITING_SELECTION`, clarification state, recommendation candidate references, and delivery slot state to `backend/app/agent/state.py` and `backend/app/agent/semantic_state.py`.
- [x] T190 Extend UnderstandingOutput and the DeepSeek understanding prompt to emit `conversation_act`, explicit selection/acceptance/rejection, slot values, and delivery intent in `backend/app/agent/understanding.py`.
- [x] T191 Resolve explicit product selections against both the catalog and `recommendation_context.previous_product_ids`; mark candidate references and ambiguous matches in `backend/app/agent/entity_resolver.py` and `backend/app/agent/planner.py`.
- [x] T192 Implement generic capability slot requirements and next-question selection in `backend/app/agent/slot_manager.py`, covering quantity, specification, delivery address, recipient name, and phone without phrase-specific branches.
- [x] T193 Change Planner ordering so `SELECT`/`ADD`/`SET_QUANTITY` with a resolved product takes precedence over `PRODUCT_RECOMMENDATION`, while incomplete selections return one targeted `ASK_USER` clarification in `backend/app/agent/planner.py`.
- [x] T194 Complete selection state mutation and quote handoff for selected recommendation candidates, including `WAITING_SELECTION -> ITEM_SELECTED -> PRICE_CALCULATION` transitions and recommendation-context closure in `backend/app/agent/graph.py` and `backend/app/agent/goal_stack.py`.
- [x] T195 Add delivery-information collection capability and a side-effect guard so address, recipient name, and phone are collected and validated before delivery/order tools can execute in `backend/app/agent/capability_resolver.py`, `backend/app/agent/plan_validator.py`, and `backend/app/tools/registry.py`.
- [x] T196 [P] Add unit tests for conversation-act extraction, missing-slot prioritization, candidate reference resolution, and state transitions in `backend/tests/unit/test_slot_manager.py` and `backend/tests/unit/test_conversation_act.py`.
- [x] T197 Add integration Golden Cases for recommendation selection, quantity clarification, specification ambiguity, delivery slot filling, interrupted conversations, and no-premature-handoff behavior in `backend/tests/integration/test_clarification_and_selection.py`.
- [x] T198 Add Trace/Data Lineage and benchmark assertions for `conversation_act`, `missing_slots`, `clarification_count`, `WAITING_SELECTION`, first failed slot, and blocked side-effect calls in `backend/app/agent/graph.py`, `evals/benchmark.py`, and `docs/benchmark.md`.

### Phase 21 Dependencies

```text
T188 → T189 → T190 → T191 → T192 → T193 → T194
T192 → T195
T188/T189/T190/T192 → T196/T197
T194/T195/T197 → T198
```

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1: unknown-intent understanding, JSON Planner contract, one-step routing, and basic chat UI.
3. Run US1 independent tests and the unknown-intent quickstart scenario.
4. Stop for validation/demo before adding business-specific tools.

### Incremental Delivery

1. Add US2 for verified product, inventory, and order queries.
2. Add US3 for confirmed return/exchange operations.
3. Add US5 to harden handoff and unsafe-path behavior.
4. Add US4 for constrained recommendations.
5. Complete trace, evaluation, replacement-contract, security, and full quickstart validation.

### Component Rule

No component is considered complete until its contract, normal path, failure path, independent tests, and replacement boundary are documented. Integration tasks may compose completed components but must not move their internal logic across component boundaries.

## Phase 22: 商品事实、图片推荐与客户记忆

- [x] T199 Add persisted product profile, dine-in price import data, ProductAlias, ProductMedia, and CustomerMemory models.
- [x] T200 Add product-row synchronization, media registration, alias resolution, and image-library bootstrap.
- [x] T201 Add safe media serving and admin product/profile/alias/media maintenance APIs.
- [x] T202 Add recommendation matched features, product media references, featured-board media, and attachment responses.
- [x] T203 Add customer memory candidate validation, explicit-memory persistence, customer isolation, and memory APIs.
- [x] T204 Add full featured-list CRUD, recommendation relaxation metadata, and complete product-profile admin UI.
  - [x] T204a Add featured-list item add/remove endpoints and expose recommendation relaxation metadata through the tool registry.
  - [x] T204b Complete the product-profile and featured-list administration UI.
- [x] T205 Add end-to-end frontend image cards, memory controls, and complete P0/P1 benchmark scenarios.
  - [x] T205a Add frontend product-image rendering with configurable backend URL.
  - [x] T205b Add customer memory view/delete controls with customer isolation.
  - [x] T205c Complete the dedicated P0/P1 benchmark scenario suite (customer_service_v1 and customer_service_quality_v1; JSON/Markdown reports).
- [x] T206 Run full backend regression, frontend typecheck/build, and record P0/P1 quality-gate results (136 backend tests passed; frontend typecheck and production build passed).

## Phase 23: 商品清单式 Admin UI 实施计划

- [x] T207 Define the `/`, `/admin`, and `/api/v1` boundary plus Admin View Model and API contracts.
- [x] T208 Implement the Admin product profile editor for factual, merchandising, and audience attributes.
- [x] T209 Implement multipart product-media upload, preview metadata, and product binding.
- [x] T210 Implement featured-list maintenance with validated add/remove operations and persistence.
- [x] T211 Add customer-memory inspection and delete controls scoped by customer ID.
- [ ] T212 Add Admin authentication/authorization before production deployment; Demo currently has an explicit unauthenticated limitation.
  - [x] T212a Add optional `ADMIN_TOKEN`/`X-Admin-Token` protection for Admin API and document Demo configuration.
  - [ ] T212b Replace shared-token Demo protection with production identity, role-based authorization, and server-side admin sessions.
- [ ] T213 Add Admin UI tests for save failure, invalid payload, upload failure, persistence after restart, and audit visibility.
  - [x] T213a Cover invalid product payloads, unsupported uploads, featured persistence, and audit retrieval in `backend/tests/integration/test_product_media_memory.py`.
  - [ ] T213b Add browser-level Admin UI failure-state and persistence-after-restart tests.
- [x] T214 Add Admin Trace/Benchmark pages with case detail and component failure drill-down.

### Phase 23 Dependencies and Execution Order

```text
T207
 ├── T208 商品画像编辑器
 ├── T209 图片上传与绑定
 ├── T210 必吃榜维护
 └── T211 客户记忆面板
T208/T209/T210/T211 → T213 Admin UI 契约与失败路径测试
现有 Benchmark API/Trace API → T214 质量页面
T213/T214 → T212 上线前认证授权与最终验收
```

可并行执行：T208、T209、T210、T211 使用不同页面和接口；T213 可在页面完成后独立编写；T214 可复用现有报告和 Inspector API。

### Phase 23 Independent Acceptance

---

## Phase 24: 待确认建议恢复与失败传播

**Goal**: 让 Agent 能把上一轮主动提出的建议保存为可执行的待处理动作；用户回复“好的/可以/行”等确认语句时恢复该动作，而不是错误进入 `LLM_OUTPUT_INVALID`。同时让 Trace 和 Turn Evaluation 正确标记首个失败组件，消除全链路“假 PASS”。

**Independent Test**: 执行“芝士肠仔包适合小朋友吗 → 好的”，第二轮必须识别为接受上一轮推荐建议、调用推荐能力并保留儿童约束；没有待确认建议时单独输入“好的”应安全澄清；任何理解失败后的未执行组件必须显示 `NOT_RUN`，不得显示 `PASS`。

### Foundational Contracts and State

- [x] T233 [P] Define versioned `PendingFollowup`, `FollowupIntent`, and failure-propagation contracts, including acceptance, rejection, expiration, source turn, inherited constraints, and first-failure fields in `backend/app/agent/contracts.py`.
- [x] T234 [P] Add `pending_followup` and `pending_followup_history` to `CustomerServiceState`, define lifecycle transitions and serialization compatibility in `backend/app/agent/state.py` and `backend/app/agent/semantic_state.py`.
- [x] T235 [P] Document follow-up state ownership, allowed transitions, and component status propagation in `docs/architecture.md` and `docs/benchmark.md`.

### Understanding and Follow-up Resolution

- [x] T236 [US1] Extend Semantic Workspace input/output to classify affirmative, negative, and correction responses relative to the previous assistant proposal without requiring product names or Goal enum names in `backend/app/agent/semantic_workspace.py` and `backend/app/agent/understanding.py`.
- [x] T237 [US1] Implement a generic `FollowupIntentResolver` that resolves `ACCEPT_FOLLOWUP`, `REJECT_FOLLOWUP`, and `CLARIFY_FOLLOWUP` from the current turn plus `pending_followup`, with no product-specific keyword branches, in `backend/app/agent/followup_resolver.py`.
- [x] T238 [US1] Persist `pending_followup` whenever Response Generation asks an actionable question or offers a next capability, including recommendation constraints and source message provenance, in `backend/app/agent/graph.py`.
- [x] T239 [US1] Restore the accepted follow-up into the current semantic action and route it through the existing capability resolver and recommendation service, clearing the pending action only after successful execution in `backend/app/agent/planner.py` and `backend/app/agent/graph.py`.
- [x] T240 [US1] Preserve current product focus, audience, sweetness, texture, category, and other valid constraints while accepting a follow-up, without promoting an unselected product into the purchase list in `backend/app/agent/state.py` and `backend/app/agent/semantic_state.py`.

### Failure Propagation and Evaluation

- [x] T241 [US1] Map `LLM_OUTPUT_INVALID`, `SEMANTIC_INTENT_UNRESOLVED`, `ACCEPT_FOLLOWUP_NOT_RESOLVED`, and capability recovery failures to their first failed component in `backend/app/agent/turn_evaluator.py` and `backend/app/agent/graph.py`.
- [x] T242 [US1] Mark downstream components as `NOT_RUN` after an upstream failure and prevent stale prior-turn success values from being reused in Turn Evaluation and Inspector output in `backend/app/agent/turn_evaluator.py` and `backend/app/trace_service.py`.
- [x] T243 [P] [US1] Add component-evaluation assertions for first failure, `NOT_RUN` propagation, pending-follow-up recovery, and no-premature-handoff behavior in `evals/benchmark_assertions.py` and `evals/benchmark.py`.

### Tests for User Story 1

- [x] T244 [P] [US1] Add unit tests for pending-follow-up lifecycle, affirmative/negative/unknown confirmation, constraint retention, expiration, and isolated “好的” clarification in `backend/tests/unit/test_followup_resolver.py` and `backend/tests/unit/test_pending_followup.py`.
- [ ] T245 [US1] Add integration Golden Cases for product-fit → accept recommendation, recommendation → accept refresh, quote → accept next-step, rejection, correction, and no-pending confirmation in `backend/tests/integration/test_followup_recovery.py`.
- [x] T246 [US1] Add regression tests proving `LLM_OUTPUT_INVALID` identifies the correct first failed component and does not mark unexecuted Planner, Tool, or Business Service steps as PASS in `backend/tests/integration/test_turn_evaluation_failure_propagation.py`.
- [x] T247 [US1] Add a real-response contract fixture for “芝士肠仔包适合小朋友吃吗 → 好的” that asserts recommendation invocation, child constraint retention, natural response, no internal fields, and no handoff in `evals/scenarios/followup_recovery_v1.json`.

### Phase 24 Acceptance

- `芝士肠仔包适合小朋友吃吗 → 好的` restores the offered recommendation and does not ask the customer to restate the request.
- A standalone `好的` without a pending proposal receives one targeted clarification and never invokes a business tool.
- Pending follow-up acceptance retains valid prior constraints and does not mutate `selected_products` unless the user explicitly selects a product.
- First-failure component is populated for every invalid-understanding path; downstream unexecuted components are `NOT_RUN`.
- Follow-up recovery does not cause premature handoff or repeated clarification.

### Phase 24 Dependencies and Execution Order

```text
T233/T234 → T236/T237 → T238 → T239/T240
T233/T234/T235 → T241/T242
T239/T240/T241/T242 → T243/T244/T245/T246/T247
```

可并行执行：T215–T217 可并行；T218/T219 可并行；T223/T224 可与理解恢复开发并行；T226 和 T228 可在接口稳定后并行编写。

### Phase 24 MVP

1. 完成 T233、T234、T236、T237、T238、T239。
2. 先通过“适配性追问 → 好的”的独立集成测试。
3. 完成 T241、T242，确保失败 Trace 不再假 PASS。
4. 再扩展拒绝、纠正、报价和推荐刷新场景。

- 商品画像保存后刷新页面仍保留事实、销售和人群属性。
- 非法价格、非法商品 ID 和非法画像结构不会修改数据。
- 上传 JPG/PNG/WebP 后可以在客服前台看到对应商品图片；不支持的文件类型被拒绝。
- 必吃榜加入、移除和顺序在服务重启后保持一致。
- CUS001 的记忆不能被 CUS002 查询或删除。
- Admin API 的每次变更均能在审计记录中定位。
- Admin 页面接口失败时保留编辑内容并给出可理解的错误提示。

## Phase 24: 商品清单主表与 ProductAdminView

- [x] T215 [US6] Add a versioned `ProductAdminView` response model in `backend/app/contracts/` with dine-in, member, promotion, inventory, primary-media, display-tag, and sale-status fields.
- [x] T216 [US6] Add `member_price`, `promotion_price`, and `status` persistence/compatibility fields in `backend/app/db/models/catalog.py` and seed synchronization in `backend/app/db/seed.py`.
- [x] T217 [US6] Implement backend aggregation of product, database inventory, primary media, policy-derived discount price, and display tags in `backend/app/domain/product_admin_service.py`.
- [x] T218 [US6] Expose `GET /api/v1/admin/product-list` with filtering by category/status and sorting by price/inventory in `backend/app/api/admin.py`.
- [x] T219 [US6] Replace the JSON-only Admin product selector with a table view and row-level edit action in `frontend/app/admin/page.tsx` and `frontend/components/AdminProductTable.tsx`.
- [x] T220 [US6] Add an Admin product edit drawer for prices, sale status, profile, aliases, inventory, and media in `frontend/components/AdminProductEditor.tsx`.
- [x] T221 [US6] Add ProductAdminView contract, invalid-input, missing-media, inventory-aggregation, persistence, and audit tests in `backend/tests/contract/` and `backend/tests/integration/`.
- [ ] T222 [US6] Add frontend table rendering, filtering, edit-failure retention, and reload persistence tests in `frontend/tests/`.

### Phase 24 Dependencies

```text
T215 → T216 → T217 → T218 → T219 → T220
T215/T217/T218 → T221
T219/T220 → T222
```

T216, T217 and T221 may be developed in parallel only after T215 is fixed; frontend T219 can start after the API response contract is stable.

## Phase 25: Reference Resolution and Business Working State

- [x] T223 [US6] Add `focused_product` and preserve `recent_products` separately from `selected_products` in the customer service state and lineage snapshot.
- [x] T224 [US6] Add a shared `ReferenceResolver` with current-turn, focused-product, recent-product, selected-product, and recommendation-rank resolution.
- [x] T225 [US6] Make inventory lookup promote only focus/recent product state; explicit purchase language promotes to `selected_products`.
- [x] T226 [US6] Support generic quantity mutations for `要2个`, `再来一个`, `改成一个`, and clarify when multiple recent products are candidates.
- [x] T227 [US6] Add Reference & State Mutation benchmark cases `RS-01` through `RS-07` and deterministic clarification assertions.
- [x] T228 [US6] Add unit/integration regression coverage for focus promotion, quantity updates, and ambiguous references.

## Phase 26: Semantic Workspace A/B Evaluation

- [x] T229 [US6] Add the flexible Semantic Workspace contract and current-turn safe fallback.
- [x] T230 [US6] Add semantic-mode Graph integration with deterministic SKU resolution and state mutation.
- [x] T231 [US6] Add Legacy/Semantic comparison execution and report deltas for the follow-up benchmark.
- [x] T232 [US6] Add contract tests for semantic references, product targets, and safe recovery.

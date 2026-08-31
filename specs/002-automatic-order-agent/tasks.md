# Tasks: 自动接单订单智能体

**Input**: Design documents from `/specs/002-automatic-order-agent/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Organization**: Tasks are grouped by user story; tests are included because the project constitution requires contract, integration, security and measurable evaluation coverage.

## Phase 1: Setup

- [x] T001 [P] Add order-email feature configuration and simulated-provider flags in `backend/app/config.py`
- [x] T002 [P] Add deterministic order-email seed fixtures in `data/seed/order_emails.json`
- [x] T003 [P] Add fixed order-email evaluation scenarios for SC-001–SC-005 in `evals/scenarios/order_email_v1.json`
- [x] T004 Register order-email API router in `backend/app/main.py`

## Phase 2: Foundational

- [x] T005 Define versioned Pydantic contracts and common result/error envelope in `backend/app/order_agent/contracts.py`
- [x] T006 [P] Define OrderEmail, OrderDraft, OrderItem, InventoryCheck, ReplyDraft, ConfirmationRecord and SendRecord state models in `backend/app/order_agent/models.py`
- [x] T007 [P] Define repository protocols and simulated implementations for email, catalog, inventory and send results in `backend/app/order_agent/repositories.py`
- [x] T008 Implement draft/version state transitions and invariants in `backend/app/order_agent/state.py`
- [x] T009 Implement redacted Trace event writer for order-email stages in `backend/app/order_agent/trace.py`
- [x] T010 [P] Add foundational contract tests for schemas, error codes and unsafe planner actions in `backend/tests/contract/test_order_agent_contracts.py`
- [x] T011 Add repository replacement tests for simulated email/catalog/inventory/send adapters in `backend/tests/contract/test_order_agent_repositories.py`
- [x] T012 Implement validated order Planner/Graph action routing for `PARSE_EMAIL`, `CHECK_ORDER`, `GENERATE_DRAFT`, `ASK_CONFIRMATION`, `SEND_REPLY` and `HANDOFF` in `backend/app/order_agent/orchestrator.py`

**Checkpoint**: Shared contracts, state transitions, repositories and trace boundaries are ready; no story implementation may bypass them.

## Phase 3: User Story 1 - 识别订单邮件并提取订单 (Priority: P1) 🎯 MVP

**Goal**: 将模拟订单邮件转换为可核对的结构化订单草稿，并对缺失、冲突和歧义字段提出澄清。

**Independent Test**: 提交单商品、多商品、缺少数量/地址和含冲突信息的邮件，验证订单项、来源/置信状态和澄清问题。

### Tests

- [x] T013 [P] [US1] Add parser unit tests for single-item, multi-item, quantity and delivery extraction in `backend/tests/unit/test_order_email_parser.py`
- [x] T014 [P] [US1] Add API contract tests for `POST /api/v1/order-emails` in `backend/tests/contract/test_order_email_api.py`
- [x] T015 [US1] Add integration tests for missing fields, conflicts and duplicate `email_id` handling in `backend/tests/integration/test_order_email_ingestion.py`

### Implementation

- [x] T016 [US1] Implement Chinese order-email classifier and field-level extraction in `backend/app/order_agent/email_parser.py`
- [x] T017 [US1] Implement missing/ambiguous field question builder in `backend/app/order_agent/clarification.py`
- [x] T018 [US1] Implement order draft creation and duplicate-source handling in `backend/app/order_agent/draft_service.py`
- [x] T019 [US1] Implement `POST /api/v1/order-emails` ingestion endpoint in `backend/app/api/order_emails.py`
- [x] T020 [US1] Add parser, draft creation and clarification Trace events in `backend/app/order_agent/trace.py`

**Checkpoint**: US1 independently produces a draft or targeted clarification and never creates a sendable confirmation for incomplete/ambiguous input.

## Phase 4: User Story 2 - 核验商品、价格和库存 (Priority: P1)

**Goal**: 对每个订单项执行唯一商品匹配、库存和价格核验，准确返回逐项满足状态。

**Independent Test**: 使用唯一匹配、歧义匹配、库存充足、不足、缺货和服务不可用案例验证结果。

### Tests

- [x] T021 [P] [US2] Add catalog matching and inventory status unit tests in `backend/tests/unit/test_order_inventory_check.py`
- [x] T022 [P] [US2] Add API contract tests for `POST /api/v1/order-drafts/{draft_id}/check` in `backend/tests/contract/test_order_check_api.py`
- [x] T023 [US2] Add integration tests for full, partial, out-of-stock and unknown inventory scenarios in `backend/tests/integration/test_order_inventory_flow.py`

### Implementation

- [x] T024 [US2] Implement exact/alias/ambiguous product resolver in `backend/app/order_agent/product_resolver.py`
- [x] T025 [US2] Implement deterministic per-item inventory and price check service in `backend/app/order_agent/inventory_check.py`
- [x] T026 [US2] Add `POST /api/v1/order-drafts/{draft_id}/check` endpoint and status aggregation in `backend/app/api/order_drafts.py`
- [x] T027 [US2] Invalidate stale checks after draft edits and persist observed timestamps/reasons in `backend/app/order_agent/state.py`

**Checkpoint**: US1 drafts can be checked independently; unknown or ambiguous facts remain unknown and are never converted into positive availability.

## Phase 5: User Story 3 - 生成客户回复草稿 (Priority: P1)

**Goal**: 根据已核验事实生成全量满足、部分满足或需补充信息的客户回复草稿。

**Independent Test**: 对四类订单检查草稿与结构化商品、数量、价格、库存和交付事实一致，且无未经验证承诺。

### Tests

- [x] T028 [P] [US3] Add reply composition and fact-consistency unit tests in `backend/tests/unit/test_order_reply_draft.py`
- [x] T029 [P] [US3] Add contract tests for reply draft response shape in `backend/tests/contract/test_reply_draft_api.py`
- [x] T030 [US3] Add integration tests for full, partial, clarification and unavailable-data reply drafts in `backend/tests/integration/test_reply_draft_flow.py`

### Implementation

- [x] T031 [US3] Implement fact-bound reply draft composer with explicit gaps and alternatives in `backend/app/order_agent/reply_composer.py`
- [x] T032 [US3] Extend the existing draft retrieval response with checks and reply draft fields in `backend/app/api/order_emails.py`
- [x] T033 [US3] Add fact snapshot and draft-version generation in `backend/app/order_agent/reply_service.py`

**Checkpoint**: A checked order produces an auditable, human-reviewable reply draft without sending.

## Phase 6: User Story 4 - 人工确认后发送并追踪 (Priority: P1)

**Goal**: 让操作员查看并修改草稿，确认当前版本后执行一次模拟发送并追踪结果。

**Independent Test**: 验证未确认阻断、当前版本确认、重复请求幂等、旧版本失效、失败/未知发送结果保持真实。

### Tests

- [x] T034 [P] [US4] Add confirmation gate, version and idempotency unit tests in `backend/tests/security/test_order_send_boundaries.py`
- [x] T035 [P] [US4] Add contract tests for edit/confirm/send endpoints in `backend/tests/contract/test_order_send_api.py`
- [x] T036 [US4] Add end-to-end confirmation/send integration tests in `backend/tests/integration/test_order_send_flow.py`

### Implementation

- [x] T037 [US4] Implement draft patch validation, version increment and invalidation in `backend/app/order_agent/draft_service.py`
- [x] T038 [US4] Implement confirmation and idempotent simulated send service in `backend/app/order_agent/send_service.py`
- [x] T039 [US4] Add `PATCH /api/v1/order-drafts/{draft_id}` endpoint in `backend/app/api/order_drafts.py`
- [x] T040 [US4] Add `POST /api/v1/reply-drafts/{reply_id}/confirm` and `/send` endpoints in `backend/app/api/order_replies.py`
- [x] T041 [US4] Add send result, failure and unknown-result Trace events in `backend/app/order_agent/trace.py`
- [x] T042 [US4] Add operator order queue, inventory summary, editable reply draft and confirmation control in `frontend/app/admin/orders/page.tsx`
- [x] T043 [US4] Add order summary, per-item availability and send-state components in `frontend/components/OrderEmailReview.tsx`
- [x] T044 [US4] Add typed order-email API client methods in `frontend/lib/orderEmailApi.ts`
- [x] T045 [US4] Add frontend smoke coverage with elapsed-time measurement for review-confirm-send flow in `frontend/tests/order-email-smoke.spec.ts`

**Checkpoint**: Full V1 flow is available with explicit human confirmation, stale-version protection and idempotent simulated sending.

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T046 [P] Add SC-001–SC-006 evaluator assertions, elapsed-time measurement and report mapping in `evals/order_email_assertions.py`
- [x] T047 [P] Add performance checks for inventory p95 and draft generation time in `backend/tests/integration/test_order_email_performance.py`
- [x] T048 [P] Add sensitive-field redaction tests for UI, Trace and handoff payloads in `backend/tests/security/test_order_email_redaction.py`
- [x] T049 Update `docs/architecture.md` with order-email component boundaries and simulated-provider limitation
- [x] T050 Run all scenarios from `specs/002-automatic-order-agent/quickstart.md` and record evidence in `reports/order-email-v1/`

## Dependencies & Execution Order

- Phase 1 → Phase 2 → User Stories.
- US1 depends only on Phase 2 and is the MVP entry point.
- US2 depends on US1 draft entities; its resolver/check services can be developed in parallel with US3 composition work after shared contracts, but US3 integration depends on completed US2 check results.
- US4 depends on US3 reply drafts and US2 freshness/version rules.
- Phase 7 depends on all selected stories.

## Parallel Opportunities

- T001–T003 can run in parallel; T006–T007 and T010 can run in parallel after T005.
- Within each story, unit and contract tests marked `[P]` can be authored in parallel with separate implementation files.
- After Phase 2, resolver/check service work (US2) and parser clarification work (US1) can proceed in parallel.
- UI tasks T042–T044 can proceed in parallel once the API response shapes are stable.

## Implementation Strategy

1. Complete contracts, state invariants, repositories and Trace foundation.
2. Deliver US1 as the MVP: email → structured draft/clarification.
3. Add US2 and validate inventory facts before enabling reply generation.
4. Add US3 for human-reviewable drafts.
5. Add US4 only after confirmation, version and idempotency security tests pass.
6. Run cross-cutting evaluation, performance, redaction and quickstart validation.

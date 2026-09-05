# Tasks: 主动问题生成（PQG）

**Input**: Design documents from `/specs/003-proactive-question-generation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api.md`, `quickstart.md`

**Organization**: Tasks are grouped by user story. Tests are included because the project constitution requires contract, integration, security and measurable evaluation coverage.

## Phase 1: Setup

- [X] T001 [P] Add PQG configuration defaults and feature flag in `backend/app/config.py`
- [X] T002 [P] Add sanitized PQG seed conversations and expected scenarios in `data/seed/pqg_dialogues.json` and `evals/scenarios/pqg_v1.json`
- [X] T003 Document PQG boundaries, provider compatibility and trace fields in `docs/architecture.md`

## Phase 2: Foundational

- [X] T004 [P] Define versioned Pydantic contracts and enums in `backend/app/pqg/contracts.py`
- [X] T005 [P] Define PQG persistence entities and indexes in `backend/app/db/models/pqg.py`
- [X] T006 [P] Add repository interfaces for history, requests, candidates and events in `backend/app/pqg/repositories.py`
- [X] T007 [P] Add privacy-minimal trace event helpers in `backend/app/pqg/trace.py`
- [X] T008 Add session ownership and completed-assistant-message validation helpers in `backend/app/pqg/access.py`
- [X] T009 Add contract tests for schemas, enum states and redaction in `backend/tests/unit/test_pqg_core.py`
- [X] T010 Add database model/repository tests in `backend/tests/unit/test_pqg_repositories.py`

**Checkpoint**: Shared contracts, persistence boundary, authorization checks and trace format are ready.

## Phase 3: User Story 1 — 回复后展示后续问题 (P1) 🎯 MVP

**Goal**: After a successful assistant reply, return 0–3 usable suggestions without blocking the original reply; clicking only fills the composer.

**Independent Test**: Complete one customer-service turn, retrieve PQG results, click a suggestion, and verify the message is not sent automatically.

- [X] T011 [P] [US1] Write API contract and integration tests for trigger, status and maximum-three behavior in `backend/tests/contract/test_pqg_api.py`
- [X] T012 [P] [US1] Write end-to-end turn and non-blocking fallback tests in `backend/tests/contract/test_pqg_api.py`
- [X] T013 [P] [US1] Write browser smoke coverage for the customer client in `frontend/tests/pqg-smoke.spec.ts`
- [X] T014 [US1] Implement PQG request lifecycle and status persistence in `backend/app/pqg/service.py`
- [X] T015 [US1] Add session-scoped PQG GET/POST routes and event route in `backend/app/api/pqg.py`
- [X] T016 [US1] Register PQG routes and response error mapping in `backend/app/main.py`
- [X] T017 [US1] Add frontend API client for retrieving suggestions and recording events in `frontend/lib/pqgApi.ts`
- [X] T018 [US1] Implement accessible suggestion list with loading/empty/degraded states in `frontend/components/ProactiveQuestions.tsx`
- [X] T019 [US1] Integrate suggestions below assistant replies and fill the existing composer without sending in `frontend/app/page.tsx`

**Checkpoint**: MVP works independently with mock/empty PQG results and preserves the existing send flow.

## Phase 4: User Story 2 — 基于历史对话检索 (P1)

**Goal**: Retrieve similar historical contexts and rank their frequent follow-up questions with traceable evidence.

**Independent Test**: Load seeded history, submit a matching context, and verify relevant deduplicated `RETRIEVAL` candidates and evidence.

- [X] T020 [P] [US2] Write retrieval ranking, frequency, deduplication and no-match tests in `backend/tests/unit/test_pqg_core.py`
- [X] T021 [P] [US2] Write retrieval endpoint and p95 query checks in `evals/pqg_assertions.py`
- [X] T022 [US2] Implement sanitized corpus loading and context similarity search in `backend/app/pqg/retrieval.py`
- [X] T023 [US2] Implement relevance/frequency ranking and evidence construction in `backend/app/pqg/retrieval.py`
- [X] T024 [US2] Connect retrieval results to PQG service fallback and `RETRIEVAL` source labeling in `backend/app/pqg/service.py`
- [X] T025 [US2] Add retrieval seed loading and deterministic fixtures in `backend/tests/conftest.py`

**Checkpoint**: Retrieval can independently produce safe suggestions even when LLM is unavailable.

## Phase 5: User Story 3 — 基于 LLM 生成候选 (P1)

**Goal**: Generate up to three contextual questions through the existing provider abstraction and accept only valid versioned JSON.

**Independent Test**: Stub valid JSON, malformed JSON, timeout and provider error responses and verify parsing plus fallback behavior.

- [X] T026 [P] [US3] Write strict JSON/schema/quantity validation tests in `backend/tests/unit/test_pqg_core.py`
- [X] T027 [P] [US3] Write provider timeout, invalid-output and fallback contract tests in `backend/tests/unit/test_pqg_core.py`
- [X] T028 [US3] Implement context redaction, prompt construction and provider invocation in `backend/app/pqg/generation.py`
- [X] T029 [US3] Implement strict JSON parsing and candidate validation in `backend/app/pqg/generation.py`
- [X] T030 [US3] Merge valid LLM candidates with retrieval candidates, deduplicate and cap at three in `backend/app/pqg/service.py`
- [X] T031 [US3] Add model/provider latency and parse status to trace without logging raw prompt or sensitive output in `backend/app/pqg/trace.py`

**Checkpoint**: LLM generation is replaceable, strictly parsed and safely degradable.

## Phase 6: User Story 4 — 安全的销售引导 (P1)

**Goal**: Promote useful purchase questions while suppressing unsafe, misleading or unwanted suggestions.

**Independent Test**: Submit handoff, refusal, unresolved-price, sensitive-data, duplicate and fabricated-fact cases and verify suppression/filtering.

- [X] T032 [P] [US4] Write suppression and no-fabricated-facts tests in `backend/tests/unit/test_pqg_core.py` and `backend/tests/security/test_pqg_policy.py`
- [X] T033 [P] [US4] Write sensitive-context redaction and trace-minimization tests in `backend/tests/security/test_pqg_redaction.py`
- [X] T034 [US4] Implement suppression rules, topic allowlist and user-refusal handling in `backend/app/pqg/policy.py`
- [X] T035 [US4] Implement candidate safety checks for claims, sensitive content, coercive language and duplicates in `backend/app/pqg/policy.py`
- [X] T036 [US4] Apply policy before persistence/display and record filter reasons in `backend/app/pqg/service.py`
- [X] T037 [US4] Add UI behavior for suppressed/high-risk states without exposing internal reasons in `frontend/components/ProactiveQuestions.tsx`

**Checkpoint**: Safety policy independently prevents unsafe sales guidance and preserves ordinary conversation.

## Phase 7: Polish & Cross-Cutting Validation

- [X] T038 [P] Add executable SC-001–SC-007 evaluator and fixtures in `evals/pqg_assertions.py`
- [X] T039 [P] Add service/API observability metrics for status, latency, source, filtering and interaction events in `backend/app/pqg/trace.py`
- [X] T040 [P] Add configuration and operator notes for mock/Kimi/Zhipu-compatible providers in `docs/architecture.md`
- [X] T041 Run targeted backend unit, contract, integration and security tests and fix regressions in `backend/tests/`
- [X] T042 Run frontend typecheck, build and Playwright PQG smoke test in `frontend/`
- [X] T043 Run `quickstart.md` end-to-end validation and record evidence in `reports/pqg-v1/README.md`
- [X] T044 Run full backend suite, frontend checks and PQG evaluator before marking the feature complete

## Dependencies & Execution Order

- Setup (T001–T003) precedes Foundational (T004–T010).
- Foundational must complete before any user-story phase.
- US1 (T011–T019) is the MVP and can begin after Foundational.
- US2 retrieval tasks (T020–T025) and US3 generation tasks (T026–T031) can proceed in parallel after Foundational; both integrate through US1’s service boundary.
- US4 policy tasks (T032–T037) can begin after contracts are ready, but final integration follows US2/US3 candidate paths.
- Polish (T038–T044) follows the desired user stories.

## Parallel Execution Examples

```text
After T004–T010: run T011, T012 and T013 in parallel.
After MVP contracts: run US2 retrieval (T020–T025) and US3 generation (T026–T031) in parallel.
Within US4: run T032 and T033 in parallel, then implement T034–T036.
```

## Implementation Strategy

1. Complete contracts and persistence boundary.
2. Deliver US1 with deterministic empty/mock results and verify no auto-send.
3. Add retrieval as an independently useful fallback.
4. Add strict LLM generation and merge behavior.
5. Add safety policy, suppression and privacy checks.
6. Run all measurable evaluators and frontend/backend validation.

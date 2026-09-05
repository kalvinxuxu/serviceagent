---
description: "Task list for core Agent architecture convergence"
---

# Tasks: 核心 Agent 架构收敛

**Input**: Design documents from `/specs/004-core-agent-architecture-convergence/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/runtime.md`, `quickstart.md`

**Tests**: Required by the project constitution and the feature specification.

**Organization**: Tasks are grouped by user story and ordered by dependency.

## Phase 1: Setup

**Purpose**: Establish mode isolation and baseline tooling without changing the Legacy default.

- [x] T001 [P] Validate `AGENT_ARCHITECTURE=legacy|converged` and preserve Legacy as the default in `backend/app/config.py`.
- [x] T002 [P] Add isolated Legacy/Converged session fixtures in `backend/tests/conftest.py`.
- [x] T003 [P] Define shared architecture-comparison output fields in `evals/compare_architectures.py`.
- [x] T004 Update architecture documentation with the domain-routing, execution-state, short-path, long-transaction, and complex-task matrix in `docs/architecture.md`.

## Phase 2: Foundational

**Purpose**: Establish contracts and shared execution boundaries before user-story work.

- [x] T005 [P] Define `SemanticAction`, `ResolvedReference`, `ExecutionDecision`, `PolicyDecision`, `ResponseContext`, `HandoffState`, and execution-mode contracts in `backend/app/agent/contracts.py`.
- [x] T006 [P] Add contract tests rejecting Supervisor tool names, task lists, `HUMAN`, `ASK_USER`, `HANDOFF`, and risk decisions in `backend/tests/contract/test_supervisor_boundary.py`.
- [x] T007 [P] Define `active_domain` and `execution_mode` state fields with Legacy serialization compatibility in `backend/app/agent/state.py`.
- [x] T008 [P] Add state transition tests proving `HUMAN_HANDOFF` is separate from `active_domain` in `backend/tests/unit/test_handoff_execution_state.py`.
- [x] T009 [P] Define read-only Action-to-tool constraints without runtime tool selection in `backend/app/agent/capability_policy.py`.
- [x] T010 [P] Define Plan Validator input/output and invalid-action reasons in `backend/app/agent/plan_validator.py`.
- [x] T011 [P] Add Capability Policy and Plan Validator contract tests in `backend/tests/unit/test_decision_boundary_contracts.py`.
- [x] T012 Define component lineage names, first-failure propagation, and `NOT_RUN` behavior in `backend/app/agent/lineage.py`.

**Checkpoint**: Contracts, mode isolation, execution state, policy constraints, and validation boundaries are ready; Legacy remains default.

## Phase 3: User Story 1 - 简单请求走短路径 (Priority: P1) 🎯 MVP

**Goal**: Atomic inventory, product information, recommendation, comparison, and single-product quote requests bypass persistent Goals and the optional Planner.

**Independent Test**: Run atomic inventory and quote requests and verify one semantic action, no persistent Goal, no Action Planner invocation, one necessary execution, and a correct response.

### Tests for User Story 1

- [x] T013 [P] [US1] Add atomic short-path contract coverage for inventory, information, recommendation, comparison, and quote actions in `backend/tests/contract/test_short_path_contract.py`.
- [x] T014 [P] [US1] Add integration tests proving atomic requests bypass Goal Manager and Action Planner in `backend/tests/integration/test_short_path_routing.py`.
- [x] T015 [P] [US1] Add tests proving Capability Policy constrains actions while Executor performs the only tool dispatch in `backend/tests/unit/test_policy_executor_boundary.py`.

### Implementation for User Story 1

- [x] T016 [US1] Implement deterministic atomic Action-to-Capability mapping in `backend/app/agent/action_mapping.py`.
- [x] T017 [US1] Implement common Executor/ToolFacade dispatch and normalized observations in `backend/app/agent/executor.py` and `backend/app/tools/registry.py`.
- [x] T018 [US1] Add Converged short-path routing that bypasses Goal Manager, Planner, and legacy keyword planning in `backend/app/agent/graph.py`.
- [x] T019 [US1] Convert `capability_resolver.py` into a compatibility adapter that delegates only to Capability Policy in `backend/app/agent/capability_resolver.py`.
- [x] T020 [US1] Preserve Legacy API responses and separate mutable session state between modes in `backend/app/api/sessions.py`.

**Checkpoint**: Atomic Commerce requests use the short path and existing Legacy behavior remains unchanged by default.

## Phase 4: User Story 2 - 多轮语义操作稳定执行 (Priority: P1)

**Goal**: Resolve references once and apply quantity/selection changes deterministically without turning state edits into repeated Goals or tool calls.

**Independent Test**: Run FQ-01, FQ-05, FQ-08, and FQ-18 and verify reference, quantity, selection, and quote transitions.

### Tests for User Story 2

- [x] T021 [P] [US2] Add SemanticAction-to-reference tests for ordinal, relative, cheapest, and quantity expressions in `backend/tests/unit/test_converged_reference_actions.py`.
- [x] T022 [P] [US2] Add State Updater invariant tests for SELECT, ADD, REMOVE, SET_QUANTITY, REPLACE, KEEP, and REQUOTE in `backend/tests/unit/test_converged_state_mutation.py`.
- [x] T023 [P] [US2] Add ambiguous-reference safety tests proving no mutation or tool call occurs in `backend/tests/integration/test_ambiguous_reference_safety.py`.
- [x] T024 [P] [US2] Add multi-turn Golden Cases for FQ-01, FQ-05, FQ-08, and FQ-18 in `backend/tests/integration/test_converged_reference_flows.py`.

### Implementation for User Story 2

- [x] T025 [US2] Adapt Semantic Workspace output to `SemanticAction` without Goal-first planning in `backend/app/agent/semantic_workspace.py`.
- [x] T026 [US2] Make `reference_resolver.py` the only natural-language reference-to-SKU entry point.
- [x] T027 [US2] Implement deterministic selection and quantity mutation in `backend/app/agent/state_mutation.py`.
- [x] T028 [US2] Ensure quote recalculation uses only `quote_context.items` in `backend/app/domain/pricing_service.py` and `backend/app/agent/executor.py`.
- [x] T029 [US2] Apply reference, focus, selection, and quote state changes atomically in `backend/app/agent/graph.py`.

**Checkpoint**: Relative references and multi-turn state edits are deterministic and do not depend on Planner keyword branches.

## Phase 5: User Story 3 - 长事务、策略与人工接管边界 (Priority: P1)

**Goal**: Keep long-running delivery, return, reservation, after-sales, and handoff workflows controlled while separating domain routing, planning, policy, and execution state.

**Independent Test**: Verify Commerce/After-sales/Unknown routing, confirmation gating, pause/resume, stale-state isolation, and Human handoff behavior independently.

### Tests for User Story 3

- [x] T030 [P] [US3] Add Supervisor domain-only routing tests in `backend/tests/unit/test_supervisor_boundary.py`.
- [x] T031 [P] [US3] Add Plan Validator tests for valid, invalid, prohibited, and capability-mismatched decisions in `backend/tests/unit/test_plan_validator.py`.
- [x] T032 [P] [US3] Add Policy Gate tests for ALLOW, DENY, REQUIRE_CONFIRMATION, and ESCALATE in `backend/tests/unit/test_policy_gate.py`.
- [x] T033 [P] [US3] Add long-transaction tests for delivery, return, reservation, pause/resume, and handoff in `backend/tests/integration/test_long_transaction_boundaries.py`.
- [x] T034 [P] [US3] Add stale Goal/domain state isolation tests in `backend/tests/integration/test_stale_context_routing.py`.

### Implementation for User Story 3

- [x] T035 [US3] Restrict `SupervisorAgent` and the Converged supervisor contract to `COMMERCE`, `AFTER_SALES`, and `UNKNOWN` domain routing in `backend/app/agent/supervisor.py` and `backend/app/agent/multi_agent_contracts.py` (legacy envelope retained as an explicit compatibility adapter).
- [x] T036 [US3] Remove Supervisor task creation, route actions, and HUMAN domain handling from the Converged path in `backend/app/agent/supervisor_router.py` (legacy adapters retained for replay compatibility).
- [x] T037 [US3] Implement Plan Validator as a non-mutating structural and Capability Policy validator in `backend/app/agent/plan_validator.py`.
- [x] T038 [US3] Implement independent risk, confirmation, permission, and escalation evaluation in `backend/app/agent/policy_gate.py`.
- [x] T039 [US3] Restrict Goal Manager persistence and transitions to long-running or resumable goals in `backend/app/agent/goal_stack.py`.
- [x] T040 [US3] Add explicit `execution_mode` transitions and `HandoffState` persistence in `backend/app/domain/handoff_service.py` and `backend/app/agent/state.py`.
- [x] T041 [US3] Route long transactions through Goal Manager, Plan Validator, Policy Gate, and Executor in `backend/app/agent/action_planner.py` and `backend/app/agent/graph.py`.
- [x] T042 [US3] Move all side-effect execution, confirmation checks, and idempotency checks into `backend/app/agent/executor.py`.

**Checkpoint**: Supervisor routes domains, Policy Gate controls risk, Goal Manager handles long transactions, and Human is represented only as execution/handoff state.

## Phase 6: User Story 4 - 工具收敛、兼容与可观测性 (Priority: P2)

**Goal**: Reduce duplicated tool surface and decision paths while preserving Legacy compatibility and making Converged behavior comparable.

**Independent Test**: Run identical fixtures through Legacy and Converged modes and compare business results, tool calls, latency, first failures, handoff state, and responses.

### Tests for User Story 4

- [x] T043 [P] [US4] Add Planner negative-contract tests proving no state, domain, tool, or response side effects in `backend/tests/unit/test_planner_boundaries.py`.
- [x] T044 [P] [US4] Add duplicate-tool and compatibility-alias tests in `backend/tests/contract/test_tool_facade_convergence.py`.
- [x] T045 [P] [US4] Add ResponseContext grounding and internal-field redaction tests in `backend/tests/unit/test_response_composer.py`.
- [x] T046 [P] [US4] Add lineage and first-failure/`NOT_RUN` tests in `backend/tests/integration/test_converged_lineage.py`.
- [x] T047 [P] [US4] Add isolated Legacy/Converged comparison tests in `backend/tests/integration/test_architecture_comparison.py`.

### Implementation for User Story 4

- [x] T048 [US4] Consolidate duplicate inventory, quote, recommendation, and after-sales tool wrappers behind `backend/app/tools/registry.py` and document compatibility aliases in `docs/architecture.md`.
- [x] T049 [US4] Make Action Planner optional and enforce the Plan Validator → Policy Gate → Executor sequence in `backend/app/agent/action_planner.py` and `backend/app/agent/graph.py`.
- [x] T050 [US4] Extract fact-grounded response generation into `backend/app/agent/response_composer.py`.
- [x] T051 [US4] Record domain, execution mode, plan validation, policy, execution, state, response, and first-failure lineage in `backend/app/agent/graph.py` and `backend/app/trace_service.py`.
- [x] T052 [US4] Implement the shared-fixture Legacy/Converged comparison runner and report fields in `evals/compare_architectures.py`.
- [x] T053 [US4] Add executable metrics for duplicate decisions, unnecessary tools, premature handoff, step count, and tool-surface reduction in `evals/converged_assertions.py`.

**Checkpoint**: Both modes are independently observable, comparable, rollback-safe, and use a reduced tool/action surface.

## Phase 7: Polish & Cross-Cutting Validation

- [x] T054 [P] Update runtime contracts, data model, architecture diagrams, and operator guidance in `specs/004-core-agent-architecture-convergence/contracts/runtime.md`, `specs/004-core-agent-architecture-convergence/data-model.md`, `docs/architecture.md`, and `docs/benchmark.md`.
- [x] T055 [P] Run contract, unit, integration, and security tests for all changed Agent boundaries in `backend/tests/`.
- [x] T056 [P] Run the 5-case Contract Benchmark and reject duplicate semantic/action decisions in `evals/converged_assertions.py`.
- [x] T057 [P] Run the 20-case Legacy/Converged comparison with identical fixtures and write reports to `reports/benchmark/`.
- [x] T058 Run frontend typecheck/build and existing Playwright smoke tests after API compatibility changes in `frontend/`.
- [x] T059 Run `quickstart.md` end-to-end validation and record evidence in `reports/converged-architecture/README.md`.
- [x] T060 Run the full backend suite, frontend checks, and executable success-criteria evaluator before marking the feature complete.

## Dependencies & Execution Order

- Setup T001–T004 precedes Foundational T005–T012.
- Foundational T005–T012 blocks all user stories.
- US1 T013–T020 is the MVP and establishes the atomic short path.
- US2 T021–T029 depends on the SemanticAction, Resolver, Executor, and State contracts.
- US3 T030–T042 depends on the foundational decision boundaries and may proceed in parallel with US2 after T012.
- US4 T043–T053 depends on the US1–US3 runtime boundaries.
- Polish T054–T060 follows the desired stories and is required before completion.

## Parallel Opportunities

- T001–T003; T005–T011; T013–T015; T021–T024; T030–T034; T043–T047; and T054–T057 can run in parallel within their dependency phase.
- T025–T027 can proceed in parallel after foundational contracts; T035–T038 can proceed in parallel after T012.
- Different user stories can be assigned to separate implementers after the foundational checkpoint.

## Implementation Strategy

1. Complete Setup and Foundational contracts while keeping Legacy default.
2. Deliver US1 short-path MVP and validate atomic requests independently.
3. Deliver US2 deterministic reference/state mutation.
4. Deliver US3 Supervisor/Policy/Goal/Handoff boundaries.
5. Deliver US4 tool consolidation, optional Planner, compatibility, and lineage.
6. Run all acceptance evaluators and switch the default only after Converged thresholds pass.

## Format Validation

All implementation tasks use `- [ ] Txxx`, optional `[P]`, required `[USx]` labels inside user-story phases, and an explicit repository-relative file path.

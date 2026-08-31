<!--
Sync Impact Report
- Version change: template → 1.0.0
- Modified principles: none; replaced the unfilled scaffold with project principles.
- Added sections: Security and Performance Constraints; Development Workflow and Quality Gates.
- Removed sections: placeholder-only scaffold comments.
- Deferred items: none.
-->

# Shanye Shop Customer Service Agent Constitution

## Core Principles

### I. Component Contracts First

Every business capability MUST be implemented behind a documented, versioned input/output
contract. Components MUST expose predictable failure results, have independent tests, and be
replaceable without changing unrelated component internals. Agent orchestration MUST depend on
component contracts rather than database models or prompt-specific behavior.

### II. Structured Planning and Safe Execution

Planner output MUST be validated against the versioned Pydantic/JSON Schema contract before any
tool or side-effecting operation executes. Invalid, incomplete, unknown, or unsafe actions MUST
stop execution and produce a safe failure or handoff. Downstream code MUST NOT parse free-form
Markdown or infer actions from natural-language planner output.

### III. Confirmation Before Side Effects

Return, exchange, refund, inventory mutation, and other side-effecting operations MUST require
explicit customer confirmation unless a separately approved policy states otherwise. Operations
MUST be idempotent, auditable, and traceable to the session, confirmation, result, and acting
component. A failed or uncertain observation MUST NOT be represented as a successful result.

### IV. Test-First Delivery and Measurable Quality

New or changed contracts MUST receive tests before integration. Required coverage includes unit,
component-contract, integration, security-boundary, and evaluation tests as applicable. Every
measurable success criterion MUST have an executable evaluator or performance check; a checked task
without a passing verification does not constitute completion.

### V. Observable, Minimal, and Privacy-Aware Operation

Each planning decision, route, tool call, confirmation, handoff, exception, and state transition
MUST be traceable without exposing unnecessary personal data. Logs, Inspector output, and handoff
context MUST apply minimum-necessary collection and redaction. The implementation MUST prefer the
smallest deterministic design that satisfies the specification and MUST document justified
complexity.

## Security and Performance Constraints

- The v1 system MUST remain within the simulated-shop boundary and MUST NOT call real commerce,
  payment, ERP, WMS, or logistics systems.
- Administrative maintenance endpoints MUST have an explicit boundary, validated payloads, and
  an audit record for every change; demo implementations MUST clearly document their persistence
  and authentication limitations.
- Core API behavior MUST be covered by authorization, input-redaction, confirmation-gating, and
  no-fabricated-result tests.
- Performance checks MUST measure the plan targets: simulated data queries at p95 below 300 ms,
  ordinary single-turn responses within 10 seconds, and no more than 12 planning/tool steps per
  session by default.

## Development Workflow and Quality Gates

- Requirements, plan, data model, contracts, tasks, implementation, and evaluation artifacts MUST
  remain mutually consistent.
- A feature phase MUST not be marked complete until its tests pass and its observable acceptance
  behavior is verified.
- Changes to a contract, state transition, side-effect boundary, persistence schema, or admin
  policy MUST include a migration or compatibility strategy and regression tests.
- Before implementation completion, the team MUST run the full backend test suite, frontend
  typecheck/build checks when frontend code changes, and the executable success-criteria evaluator.
- Architecture exceptions MUST be recorded in `docs/architecture.md` with the affected boundary,
  reason, and replacement plan if applicable.

## Governance

This constitution is authoritative for implementation and review decisions. When a requirement,
plan, or task conflicts with a MUST principle, the conflict MUST be resolved by changing the
requirement, plan, or task; the principle MUST NOT be silently weakened.

Amendments require a documented rationale, a semantic version update, an updated Sync Impact
Report, and a review of affected specs, plans, tasks, tests, and implementation boundaries.
Patch versions clarify wording; minor versions add or materially expand compatible principles or
quality gates; major versions remove or redefine governance obligations.

Every implementation review MUST verify constitution alignment, test evidence, traceability, and
any declared exceptions. The constitution MUST be revisited when the system leaves the simulated
environment or introduces a new side-effecting integration.

**Version**: 1.0.0 | **Ratified**: 2026-08-23 | **Last Amended**: 2026-08-23

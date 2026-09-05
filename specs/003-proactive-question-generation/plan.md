# Implementation Plan: 主动问题生成（PQG）

**Branch**: `003-proactive-question-generation` | **Date**: 2026-09-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-proactive-question-generation/spec.md`

## Summary

在现有客服回复完成后异步运行 PQG：先从脱敏历史对话中召回相似上下文的高频后续问句，再通过现有可替换 LLM provider 按版本化 JSON 契约生成候选；统一执行校验、去重、排序和销售安全过滤，返回最多 3 个建议。前端只展示和填入输入框，不自动发送或触发任何副作用。PQG 的状态、来源和降级原因写入现有 Trace。

## Technical Context

**Language/Version**: Python 3.11+；TypeScript/React 18；Next.js 14

**Primary Dependencies**: FastAPI, Pydantic 2, SQLAlchemy 2, LangGraph, existing LLM provider factory, Next.js

**Storage**: Existing PostgreSQL/SQLAlchemy conversation and trace storage; local seeded historical dialogue corpus for v1

**Testing**: pytest unit/contract/integration/security/evaluation tests; frontend TypeScript typecheck/build and Playwright smoke test

**Target Platform**: Existing simulated-shop local/server web application

**Project Type**: Full-stack web application with FastAPI API and Next.js client

**Performance Goals**: Original assistant response remains independent; PQG reaches displayable state within 3 seconds for at least 95% of normal turns; simulated queries p95 below 300 ms

**Constraints**: Maximum 3 candidates; strict JSON validation; no automatic send/order/payment; suppression for handoff, high-risk, refusal and unresolved facts; privacy-minimal trace; simulated-shop boundary

**Scale/Scope**: v1 Chinese text conversations, existing customer-service sessions, small-to-medium local historical corpus, replaceable LLM providers

## Constitution Check

*GATE: Must pass before Phase 0 research and after Phase 1 design.*

- **Component Contracts First**: PASS — PQG request/output, provider output and UI response are versioned in `contracts/api.md`; components remain replaceable.
- **Structured Planning and Safe Execution**: PASS — LLM output is parsed only as validated JSON; PQG has no side-effecting tool execution.
- **Confirmation Before Side Effects**: PASS — clicking a suggestion fills the composer only; sending remains an explicit existing user action.
- **Test-First Delivery and Measurable Quality**: PASS — unit, contract, integration, security, frontend and SC evaluator tasks are planned.
- **Observable, Minimal, Privacy-Aware Operation**: PASS — source, filtering and fallback are traceable with redaction; raw sensitive text is excluded.
- **Simulated-shop boundary**: PASS — no real commerce, payment, ERP, WMS or logistics integration.

## Project Structure

```text
specs/003-proactive-question-generation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/api.md

backend/app/pqg/
├── contracts.py          # Pydantic request/output contracts
├── retrieval.py          # historical-context retrieval and ranking
├── generation.py         # provider adapter and strict JSON parsing
├── policy.py             # safety, suppression and candidate validation
├── service.py            # merge, dedupe, rank and fallback orchestration
└── trace.py              # privacy-minimal PQG trace records

backend/app/api/pqg.py    # session-scoped PQG endpoint
backend/tests/{unit,contract,integration,security}/test_pqg_*.py
frontend/lib/pqgApi.ts
frontend/components/ProactiveQuestions.tsx
frontend/tests/pqg-smoke.spec.ts
evals/pqg_assertions.py
evals/scenarios/pqg_v1.json
```

**Structure Decision**: 采用现有 web application 结构，在后端新增独立 `pqg` 组件包和 session-scoped API，在前端新增建议问题组件；复用现有会话、LLM factory、数据库和 Trace 边界，不修改无关业务域。

## Phase 0: Research Decisions

研究结论见 [research.md](research.md)。核心决定是：检索和 LLM 均为可替换候选源；通过 Pydantic/JSON Schema 验证 LLM 输出；PQG 异步降级；默认点击只填充输入框。

## Phase 1: Design Outputs

- [data-model.md](data-model.md)：定义 PQG 请求、候选、证据、生成输出、策略和交互事件。
- [contracts/api.md](contracts/api.md)：定义后端接口、版本化 JSON、失败/降级状态和前端交互契约。
- [quickstart.md](quickstart.md)：提供可运行的检索、生成、异常回退、安全抑制和 UI 验证路径。

## Complexity Tracking

无宪法例外。检索、生成、策略和编排拆分是为了满足可替换组件、独立测试和可追踪性要求。

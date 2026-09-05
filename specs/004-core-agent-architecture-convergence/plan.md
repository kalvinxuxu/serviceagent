# Implementation Plan: 核心 Agent 架构收敛

**Branch**: `004-core-agent-architecture-convergence` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

在保留现有 API、Domain Services、Tool Registry 和 Legacy Mode 的前提下，将运行时收敛为 Semantic Understanding、Reference Resolver、Supervisor Domain Router、可选 Goal Manager、Capability Policy、可选 Action Planner、Plan Validator、Policy Gate、Executor、State Updater、Response Composer 和 Evaluator。普通原子请求默认走确定性短路径，只有复杂组合任务才进入 Planner；Human 由独立 Handoff/Execution State 表示。

## Technical Context

**Language/Version**: Python 3.11+；TypeScript/React 18；Next.js 14

**Primary Dependencies**: FastAPI、Pydantic 2、SQLAlchemy 2、LangGraph、现有 LLM Provider、pytest、Next.js

**Storage**: 现有 SQLAlchemy 会话状态、商品/库存/政策数据库、Trace 持久化

**Testing**: pytest unit/contract/integration/security/evaluation；frontend typecheck/build；现有 Benchmark

**Target Platform**: 现有模拟电商客服 Web 应用

**Project Type**: Full-stack web application with FastAPI backend and Next.js frontend

**Performance Goals**: 普通单轮运行时节点步骤 ≤6；模拟业务查询 p95 <300ms（不含 LLM）；不必要工具调用率 ≤5%

**Constraints**: 默认 Legacy；新模式必须可回退；不接真实外部业务系统；不得绕过确认和隐私边界

**Scale/Scope**: 现有客服场景、20 组 Follow-up Benchmark、商品/库存/推荐/报价/配送/售后状态

## Constitution Check

*GATE: Must pass before Phase 0 research and after Phase 1 design.*

- Component Contracts First：PASS。SemanticAction、ResolvedReference、ExecutionDecision 和 ToolObservation 均有独立契约。
- Structured Planning and Safe Execution：PASS。复杂任务的 Planner 输出先经过 Plan Validator，再经过 Policy Gate；任何副作用统一由 Executor 执行。
- Confirmation Before Side Effects：PASS。收货、退货、库存变更和订单提交继续由 Policy Gate 控制，Supervisor 不承担该职责。
- Test-First Delivery and Measurable Quality：PASS。新增短路径、引用解析、状态变更、回退和性能评估门禁。
- Observable, Minimal, Privacy-Aware Operation：PASS。每个收敛组件写入 Lineage，保留首个失败和 NOT_RUN。
- Smallest Deterministic Design：PASS。Capability Resolver 降级为策略目录，普通查询支持短路径；复杂度例外为保留 LangGraph 以兼容现有状态恢复。

## Project Structure

```text
backend/app/agent/
├── semantic_workspace.py       # SemanticAction 生成/适配
├── reference_resolver.py      # 引用到 SKU 的唯一入口
├── capability_policy.py       # 动作到工具的约束目录
├── action_planner.py          # 复杂任务的可选动作决策入口
├── plan_validator.py          # ExecutionDecision 结构与能力约束校验
├── state_mutation.py          # 确定性状态操作
├── executor.py                # ToolFacade 与状态动作执行
├── response_composer.py       # 事实约束下的自然语言回复
└── graph.py                   # LangGraph 编排与模式切换

backend/app/tools/
└── registry.py                # 统一 ToolFacade 兼容层

backend/tests/{unit,contract,integration,evaluation}/
└── test_converged_*.py

evals/
└── compare_architectures.py   # Legacy/Converged 同 Fixture 对比
```

**Structure Decision**: 继续使用单一 backend/frontend Web 应用；新增模块只放在现有 Agent 边界内，先以适配层和 feature flag 迁移，不复制一套旧系统。

## Implementation Phases

### Phase 0 — Contract and baseline

1. 固化 SemanticAction、ResolvedReference、ExecutionDecision 和 Lineage 契约。
2. 为现有 20 组 Follow-up Case 建立 Legacy baseline。
3. 明确短路径、长事务和人工接管的路由矩阵。

### Phase 1 — Decision kernel

1. 将 Semantic Workspace 作为 Converged Mode 的理解入口。
2. 收敛 `resolve_products` 与 `resolve_reference` 的边界，确保 SKU 只由 Resolver 产生。
3. 将 Capability Resolver 改为 Capability Policy，不再作为运行时决策节点。
4. 建立简单 Action→Capability 确定性映射；定义复杂任务触发条件，只有复杂任务启用 Action Planner。
5. 将 Supervisor 限定为粗粒度领域路由；将澄清、人工接管和风险判断移出 Supervisor，分别交给 Execution State/Handoff 与 Policy Gate。

### Phase 2 — Execution and state

1. 抽出 State Mutation，统一 SELECT/ADD/REMOVE/SET_QUANTITY/REPLACE/KEEP/REQUOTE。
2. 抽出 ToolFacade/Executor，统一工具结果和异常。
3. 将 Route 中的业务执行、状态更新和回复生成拆开。
4. 普通只读请求支持短路径；退货/配送/售后等跨轮事务才走 Goal Manager。
5. 增加 Planner 禁止事项测试，确保 Planner 不写状态、不执行工具、不生成澄清或最终回复；增加 Supervisor/Human state boundary 测试。

### Phase 3 — Graph, response, and compatibility

1. 在 LangGraph 中接入 Converged Mode 节点。
2. 保留 Legacy Mode 和 API 响应格式。
3. 将 Response Composer 与内部状态、工具名和 SKU 隔离。
4. 补全首个失败、NOT_RUN、动作和引用 Lineage。

### Phase 4 — Evaluation and rollout

1. 运行 5 条 Contract Benchmark。
2. 使用相同 Fixture 运行 20 组 Legacy/Converged 对比。
3. 输出引用、状态变更、报价、工具精度、重复澄清和人工接管指标。
4. 只有 Converged Mode 达标后，才讨论切换默认模式。

## Decision Matrix

| Request type | Goal Manager | Action Planner | Execution path |
|---|---:|---:|---|
| 单商品库存/价格/信息 | NOOP | NOOP | Semantic → Reference → Capability Policy → Executor |
| 单轮推荐/商品比较 | NOOP | NOOP | Semantic → Reference → Capability Policy → Executor |
| 数量、删除、替换、重新报价 | NOOP | NOOP | Semantic → Reference → State Updater → Pricing |
| 退货、配送、预留、订单确认 | REQUIRED | NOOP or limited | Goal → Capability Policy → Plan Validator → Policy Gate → Executor |
| 条件分支、多工具组合、跨领域任务 | OPTIONAL | REQUIRED | Action Planner → Plan Validator → Policy Gate → Executor |
| 明确要求人工或策略升级 | NOOP or pause | NOOP | Handoff/Execution State → Human Handoff |

## Planner Negative Contract

Action Planner MUST NOT:

- 直接调用 `execute()` 或任何 Domain Service；
- 直接写入 `CustomerServiceState`、`selected_products` 或 `quote_context`；
- 解析或生成 SKU；
- 重新计算价格、库存或优惠；
- 生成面向顾客的最终语言；
- 重新执行已经由 Reference Resolver 完成的引用解析。

## Boundary Contracts

- Supervisor output contains only `domain`, `confidence`, and routing reason; it never contains `HUMAN`, `ASK_USER`, `HANDOFF`, tool names, or task lists.
- `active_domain` is `COMMERCE`, `AFTER_SALES`, or `UNKNOWN`; `execution_mode` is `AUTO`, `WAITING_USER`, `WAITING_CONFIRMATION`, or `HUMAN_HANDOFF`.
- Plan Validator validates one `ExecutionDecision` and returns valid/invalid with reason; it never changes the action or selects a replacement.
- Policy Gate evaluates the validated action and risk context; it never performs domain routing or planning.
- Goal Manager persists only long-running, resumable, or side-effecting goals.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| 保留两种运行模式 | 支持回滚和对比验证 | 直接替换会破坏现有 API、测试和线上行为 |
| 保留 LangGraph 节点编排 | 兼容现有状态恢复、Trace 和可替换节点 | 直接函数调用会丢失现有检查点和可观测边界 |

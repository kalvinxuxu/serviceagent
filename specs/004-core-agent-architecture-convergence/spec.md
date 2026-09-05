# Feature Specification: 核心 Agent 架构收敛

**Feature Branch**: `004-core-agent-architecture-convergence`
**Created**: 2026-09-02
**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - 简单请求走短路径 (Priority: P1)

顾客查询单个商品库存、价格或商品信息时，系统经过必要的语义理解和业务服务即可返回，不创建不必要的复杂 Goal、Planner 或重复决策。

**Independent Test**: 执行单商品库存查询和单商品报价，验证只产生一次动作决策、一次必要工具调用，且结果正确。

### User Story 2 - 多轮语义操作稳定执行 (Priority: P1)

顾客使用“第二个”“最便宜的”“那个”“改成三个”等表达时，系统先解析语义动作和引用，再由程序确定性修改业务状态。

**Independent Test**: 运行 FQ-01、FQ-05、FQ-08、FQ-18，验证引用、数量和报价状态没有重复累计或错误澄清。

### User Story 3 - 长事务和风险边界保持可控 (Priority: P1)

退货、配送、质量投诉和人工接管等长事务仍由目标状态管理；Supervisor 只确定业务领域，人工接管由独立的执行状态表示，副作用仍必须经过策略和确认。

**Independent Test**: 验证售后转人工、退货确认、配送槽位收集和普通 Commerce 请求之间的路由隔离。

### User Story 4 - 旧模式可回退、架构可观测 (Priority: P2)

收敛过程不破坏现有 API 和 Legacy 行为；每次决策都能看到语义动作、引用解析、动作规划、执行和状态变化。

**Independent Test**: 使用同一组回归 Case 对比 Legacy 与 Converged Mode，验证 API 响应、Trace、失败组件和性能指标。

## Runtime Responsibility Boundaries

系统采用“默认确定性、复杂任务才规划”的运行方式：

```text
Semantic Workspace → Reference Resolver → Supervisor Router
→ (短路径：Capability Policy → Executor)
→ (长事务：Goal Manager → Capability Policy → Executor)
→ (复杂组合任务：Action Planner → Plan Validator → Policy Gate → Executor)
```

- Supervisor 只输出 `COMMERCE`、`AFTER_SALES` 或 `UNKNOWN`，不选择工具、不创建任务、不处理澄清或人工接管、不负责业务政策。
- 人工接管不是业务领域；系统使用独立的 `execution_mode=HUMAN_HANDOFF` 和 `HandoffState` 表示人工接管。
- Policy Gate 负责 `ALLOW`、`DENY`、`REQUIRE_CONFIRMATION` 和 `ESCALATE`。
- Goal Manager 只管理跨轮、可暂停恢复或有副作用的长事务。
- Action Planner 默认不运行，只为条件分支、多步骤或跨能力组合任务生成一个执行决策。
- Plan Validator 只验证执行决策的结构、动作合法性和能力约束，不做风险判断、不选择替代工具。
- 普通库存、商品信息、单商品报价和单轮推荐不得强制进入复杂 Planner。
- Planner 不得直接修改状态、计算价格、查询库存、生成 SKU、调用工具或生成最终回复。

## Edge Cases

- 多个候选都可能匹配“那个/来两个”时，只澄清，不自动猜测。
- 用户只说“好的”但不存在待确认动作时，安全澄清，不执行工具。
- Semantic Workspace 输出非法时，不复用上一轮计划，不调用工具，不直接把系统错误伪装成业务歧义。
- 当前轮明确意图必须覆盖历史 Goal 或长期偏好。
- 退货、库存修改、配送提交等副作用仍需独立确认和幂等保护。
- 工具失败或业务事实不可用时，不生成成功式回复。
- 普通单轮请求不得因为 Goal Manager 或 Supervisor 状态残留进入人工接管。
- 明确要求人工时，系统必须将 `execution_mode` 转为 `HUMAN_HANDOFF`，不得将 `HUMAN` 写入 active domain 或创建 HUMAN AgentTask。

## Requirements

### Functional Requirements

- **FR-001**: 系统 MUST 将 Semantic Understanding、Reference Resolution、Action Planning、Execution 和 Response Composition 定义为清晰的运行时边界。
- **FR-002**: Semantic Understanding MUST 只输出用户意图、目标引用、操作、数量和约束，不输出 SKU、价格、库存或工具名称。
- **FR-003**: Reference Resolver MUST 是唯一的自然语言商品引用到 SKU 的确定性入口。
- **FR-004**: Capability Policy MUST 只提供动作到允许工具的约束，不得作为第二个 Planner 选择工具。
- **FR-005**: Supervisor MUST 只负责 `COMMERCE`、`AFTER_SALES` 或 `UNKNOWN` 粗粒度领域路由，不得创建任务、选择工具、生成 `ASK_USER`/`HANDOFF` 动作、切换 Goal 或执行业务政策判断。
- **FR-006**: Goal Manager MUST 仅管理长事务和可恢复目标；普通只读查询可以不创建持久 Goal。
- **FR-007**: Policy Gate MUST 独立接收已确定的执行动作和必要的风险上下文，并输出 `ALLOW`、`DENY`、`REQUIRE_CONFIRMATION` 或 `ESCALATE`；不得承担领域路由、工具发现或 Planner 重规划。
- **FR-008**: Action Planner MUST 为可配置的 optional 组件，仅在条件分支、多步骤或跨能力组合任务中启用；简单原子动作 MUST 使用确定性动作映射并绕过 Planner。
- **FR-009**: Action Planner MUST 将已验证的语义动作、引用解析结果和业务状态转换为一个 `ExecutionDecision`；不得直接修改状态、调用工具、计算业务结果、生成澄清文本或生成最终回复。ExecutionDecision MUST 先经过 Plan Validator，再交由 Policy Gate。
- **FR-010**: State Updater MUST 以确定性方式处理 SELECT、ADD、REMOVE、SET_QUANTITY、REPLACE、KEEP 和 REQUOTE。
- **FR-011**: Tool Facade MUST 统一参数校验、工具执行、结果标准化、错误映射和 Trace。
- **FR-012**: Response Composer MUST 只基于业务结果和已验证事实生成自然语言，不直接暴露内部字段。
- **FR-013**: Legacy Mode MUST 在收敛期间继续可用，Converged Mode MUST 可通过配置切换，且两者不得共享可变会话中间状态。
- **FR-014**: 系统 MUST 为每个核心阶段记录输入、输出、状态变化、耗时、状态和首个失败组件。

### Key Entities

- **SemanticAction**：当前轮的自然语言语义动作和引用目标。
- **ResolvedReference**：引用目标解析后的商品或候选集合。
- **ExecutionDecision**：Planner 或确定性动作映射产生的状态修改、工具调用、澄清或人工动作。
- **BusinessState**：当前商品焦点、候选集合、已选商品、报价、配送和售后上下文。
- **CapabilityPolicy**：动作与允许工具之间的约束目录。
- **LineageStep**：组件级输入、输出、状态变化和失败信息。
- **HandoffState**：人工接管执行状态，包含触发原因、脱敏上下文、待处理事项、暂停/恢复状态和交接记录；不作为业务 Agent 或 domain。

## Success Criteria

- **SC-001**: Contract Benchmark 5 条全部通过，且每条只产生一个明确的语义动作。
- **SC-002**: FQ-01、FQ-02、FQ-05、FQ-08、FQ-18 的 Reference Resolution Accuracy 达到 95% 以上。
- **SC-003**: 多轮 State Mutation Accuracy 达到 98% 以上，报价重算准确率达到 100%。
- **SC-004**: Converged Mode 的不必要工具调用率不高于 5%，过早人工接管率不高于 5%。
- **SC-005**: 普通单轮请求的运行时节点步骤（从 Semantic Understanding 到 Response Composer，不含加载和评估）不超过 6 个，且 100% 不进入 Goal Manager 或 Action Planner；模拟业务查询 p95 小于 300ms（不含外部 LLM 延迟）。
- **SC-006**: Legacy API 契约和现有核心回归测试保持通过。
- **SC-007**: 100% 的失败 Case 能定位首个失败组件，后续未执行组件标记为 NOT_RUN。
- **SC-008**: Converged Mode 未达到门槛前，默认运行模式保持 Legacy。
- **SC-009**: 100% 的人工接管请求使用 `HUMAN_HANDOFF` execution state；`active_domain` 仅允许 `COMMERCE`、`AFTER_SALES` 或 `UNKNOWN`。

## Assumptions

- v1 继续使用现有 FastAPI、LangGraph、Pydantic、SQLAlchemy、Next.js 和模型 Provider。
- 不引入向量数据库，不接入真实支付、ERP、WMS 或物流系统。
- 现有 `Reference Resolver`、Domain Services、Tool Registry 和 Trace 数据可兼容迁移。
- Converged Mode 先覆盖 Commerce 多轮场景，再扩展售后和配送长事务。

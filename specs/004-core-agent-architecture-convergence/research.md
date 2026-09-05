# Research: 核心 Agent 架构收敛

## Decision: 保留 LangGraph，但减少运行时决策节点

LangGraph 继续作为统一执行入口，节点收敛为：

```text
load_context → semantic_understand → resolve_reference → supervisor_router
→ [short path | long transaction | complex action]
→ plan_validate → policy_gate → execute_action → update_state
→ compose_response → evaluate
```

Rationale：保留现有检查点、Trace 和可替换节点能力，同时消除 Supervisor、Capability Resolver、Planner、Route 的重复编排。

Alternatives considered：完全移除 LangGraph。拒绝原因是会破坏现有统一入口、状态恢复和节点级观测能力。

## Decision: Capability Resolver 降级为 Capability Policy

能力目录只提供约束：某个 Action 允许哪些工具。它不再独立判断用户意图，也不重复选择工具。

Rationale：当前 `resolve_capabilities()` 的实际行为是生成工具白名单，改名和收敛职责即可消除概念误导。

## Decision: Supervisor 只处理领域路由

Supervisor 输出 `COMMERCE`、`AFTER_SALES` 或 `UNKNOWN`，不输出具体工具、任务、澄清、人工动作或风险闸门结果。

Rationale：领域路由、执行动作、风险判断和人工接管是不同决策；分离后避免同一请求被多个组件重复判断。

## Decision: Semantic Workspace 成为唯一理解入口，Legacy 作为适配基线

Converged Mode 使用 SemanticAction；Legacy Mode 保留 `UnderstandingOutput`。二者通过模式开关隔离，不继续增加两套业务规则。

Rationale：允许回滚，同时逐步淘汰旧的 Goal/Planner 关键词分支。

## Decision: State Mutation 和 Tool Execution 分离

SELECT、ADD、REMOVE、SET_QUANTITY、REPLACE、KEEP、REQUOTE 等动作先解析引用，再由 State Updater 确定性执行；只有需要业务事实时才调用 Tool Facade。

Rationale：解决“数量变化被当成新 Goal”以及报价重复累计问题。

## Decision: 普通请求支持短路径

只读商品查询和简单报价不强制创建持久 Goal；长事务继续使用 Goal Manager。

Rationale：满足最小复杂度原则，同时保留退货、配送和人工接管的生命周期管理。

## Decision: Human 使用执行状态表示

人工接管使用 `execution_mode=HUMAN_HANDOFF` 和 `HandoffState`，不作为 `active_domain`、Agent 或 Supervisor route。

Rationale：人工接管描述的是执行归属和暂停/恢复生命周期，不是业务领域。

## Decision: Plan Validator 与 Policy Gate 分离

Plan Validator 只验证一个 `ExecutionDecision` 的结构、动作类型和 Capability Policy 约束；Policy Gate 只判断风险、权限、确认和升级，不重规划或替换动作。

Rationale：消除“计划是否合法”和“动作是否允许执行”的职责重叠。

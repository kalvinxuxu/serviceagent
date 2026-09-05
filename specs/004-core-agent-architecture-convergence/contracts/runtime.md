# Runtime Contracts: 核心 Agent 架构收敛

## SemanticUnderstandingService

Input：最近 6–8 轮对话、业务状态摘要、当前用户输入、最近候选商品。

Output：`SemanticAction`。

禁止输出：SKU、数据库库存、价格结果、工具名、最终订单状态。

## ReferenceResolver

Input：`SemanticAction.target` 与 `BusinessState`。

Output：`ResolvedReference`。

规则：只从当前候选、焦点商品、明确商品目录和已选商品中解析；多候选时返回 `AMBIGUOUS`。

## SupervisorRouter

Input：当前轮 `SemanticAction`、领域上下文摘要。

Output：`domain`（`COMMERCE`、`AFTER_SALES` 或 `UNKNOWN`）、confidence 和 route reason。

禁止输出：工具名、任务列表、`ASK_USER`、`HANDOFF`、风险决定或 Goal transition。

## ActionPlanner

启用条件：仅当请求包含条件分支、多步骤或跨能力组合；原子动作必须绕过该组件。

Input：`SemanticAction`、`ResolvedReference`、`BusinessState`、`CapabilityPolicy` 和 Supervisor domain。

Output：一个 `ExecutionDecision`。

规则：状态修改不再转换为重复工具调用；需要业务事实时才生成 Tool Call。

## PlanValidator

Input：一个 `ExecutionDecision` 和 `CapabilityPolicy`。

Output：验证通过的同一决策，或带 reason 的 invalid 结果。

不得选择替代动作、执行工具或进行风险判断。

## PolicyGate

Input：已验证的 `ExecutionDecision`、确认状态和风险上下文。

Output：`ALLOW`、`DENY`、`REQUIRE_CONFIRMATION` 或 `ESCALATE`。

不得执行领域路由、工具发现或 Planner 重规划。

## HandoffState

人工接管状态包含触发原因、脱敏上下文、待处理事项、暂停/恢复状态和交接记录。它不属于 Agent domain 枚举。

## ToolFacade

Input：版本化 ToolRequest。

Output：统一 ToolObservation：

```json
{
  "ok": true,
  "data": {},
  "reason": null,
  "observed_at": "..."
}
```

## ResponseComposer

只接收已验证的业务结果和允许展示的事实，生成自然、简洁的客服回复。不得输出 SKU、工具名、内部标签或原始 Trace。

## Compatibility

```text
AGENT_ARCHITECTURE=legacy     # 默认，现有行为
AGENT_ARCHITECTURE=converged  # 新架构，对比和灰度
```

Converged Mode 未达到验收门槛前不得替换默认模式。

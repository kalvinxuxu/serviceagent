export function AgentInspector({trace}: {trace: unknown}) {
  const data = (trace && typeof trace === "object" ? trace : {}) as Record<string, unknown>;
  return <aside aria-label="agent-inspector">
    <h2>Agent Inspector</h2>
    <dl>
      <dt>当前 Agent</dt><dd>{String(data.active_agent ?? "-")}</dd>
      <dt>路由原因</dt><dd>{String(data.route_reason ?? "-")}</dd>
      <dt>任务栈</dt><dd>{Array.isArray(data.task_stack) ? data.task_stack.length : 0}</dd>
      <dt>证据状态</dt><dd>{String(data.evidence_status ?? "-")}</dd>
      <dt>政策等级</dt><dd>{String(data.policy_level ?? "-")}</dd>
    </dl>
    <details><summary>完整 Trace</summary><pre>{JSON.stringify(trace, null, 2)}</pre></details>
  </aside>;
}

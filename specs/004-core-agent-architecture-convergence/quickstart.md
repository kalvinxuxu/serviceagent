# Quickstart: 核心 Agent 架构收敛

## 1. 运行模式

```powershell
$env:AGENT_ARCHITECTURE="legacy"
uvicorn backend.app.main:app --reload --port 8000
```

对比时切换：

```powershell
$env:AGENT_ARCHITECTURE="converged"
```

## 2. Contract Benchmark

验证以下输入只产生语义动作，不直接生成 SKU 或工具：

```text
有芝士贝果吗？
那要两个。
一共多少钱？
贝果改成三个。
第二个是什么味道？
```

## 3. 多轮 Golden Path

```text
有什么贝果？
→ 最便宜的是哪个？
→ 最便宜的来两个
→ 多少钱？
```

预期：第二轮完成比较，第三轮只引用当前候选中的最低价商品并设置数量，第四轮从 quote_context 重算。

## 4. 验证命令

```powershell
$env:PYTHONPATH=(Get-Location).Path
pytest -q backend/tests/unit backend/tests/integration --disable-warnings
python evals/benchmark.py --suite followup_accuracy_v1 --no-judge --output-dir reports/benchmark
```

需要比较时，使用相同 fixture、客户 ID 和 20 组 turns，分别保存 Legacy 与 Converged 的结果。

## 5. 验收重点

- Reference Resolution Accuracy ≥ 95%。
- State Mutation Accuracy ≥ 98%。
- Quote Recalculation Accuracy = 100%。
- 不必要工具调用率 ≤ 5%。
- 过早人工接管率 ≤ 5%。
- 任一上游失败后，下游必须是 `NOT_RUN`。
- 原子库存、商品信息和单商品报价 100% 绕过 Goal Manager 与 Action Planner。
- Supervisor 输出只能是 `COMMERCE`、`AFTER_SALES` 或 `UNKNOWN`，不得输出 HUMAN、工具名、任务或 HANDOFF。
- 明确要求人工时，`active_domain` 保持业务域，`execution_mode` 变为 `HUMAN_HANDOFF`。
- Plan Validator 只校验动作，Policy Gate 只做允许/拒绝/确认/升级判断。

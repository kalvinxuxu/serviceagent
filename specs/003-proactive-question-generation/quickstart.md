# Quickstart: PQG

## Prerequisites

- PostgreSQL、FastAPI 后端和 Next.js 前端已按项目 README 启动。
- 使用脱敏 seed 历史对话；本地验证建议使用 `LLM_PROVIDER=mock`。
- 现有会话接口可创建会话并完成至少一轮客服问答。

## Backend validation

1. 创建会话并发送“全麦吐司还有货吗？”。
2. 等待原回复完成，再请求该回复的 PQG 结果。
3. 验证返回状态为 `READY` 或 `EMPTY`，候选数量不超过 3，且每项有 `source` 和校验状态。
4. 使用包含相似历史对话的 seed 验证 `RETRIEVAL` 候选及频次/相似度证据。
5. 将 mock provider 改为非法 JSON、超时或异常，验证原回复仍成功，PQG 为 `DEGRADED` 或 `EMPTY`。
6. 使用转人工、拒绝推荐、未确认价格/库存和敏感信息样本，验证状态为 `SUPPRESSED` 或候选被过滤。

接口字段和状态详见 [contracts/api.md](contracts/api.md)，实体和生命周期详见 [data-model.md](data-model.md)。

## Frontend validation

1. 打开客服客户端，完成一轮问答。
2. 验证回复下方展示 0–3 个建议问题，并在无候选/抑制/降级状态时不破坏对话布局。
3. 点击建议问题，验证文本进入输入框；检查网络请求，点击本身不发送消息。
4. 编辑文本后由顾客点击现有发送按钮，验证消息按普通流程发送。

## Tests

```text
pytest backend/tests/unit/test_pqg_*.py backend/tests/contract/test_pqg_*.py
pytest backend/tests/integration/test_pqg_*.py backend/tests/security/test_pqg_*.py
python evals/pqg_assertions.py
cd frontend && npm run typecheck && npm run build
```

## Acceptance evidence

记录候选来源、状态、延迟、过滤原因和点击/发送行为；不得把完整敏感上下文或 provider 原始错误写入顾客可见响应。

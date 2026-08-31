# Quickstart: 模拟电商客服 Agent

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+（或本地开发使用 SQLite）
- 一个可用的 LLM provider key；若使用 mock provider，可不配置外部模型

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
npm --prefix frontend install
```

准备环境变量：

```text
DATABASE_URL=postgresql+psycopg://...
LLM_PROVIDER=mock
LLM_API_KEY=
```

初始化模拟商城数据：

```bash
python -m backend.app.db.seed
```

## Run

启动后端：

```bash
uvicorn backend.app.main:app --reload
```

启动前端：

```bash
npm --prefix frontend run dev
```

浏览器打开前端页面，直接输入自然语言，不需要先选择业务类型。

管理后台打开：

```text
http://localhost:3000/admin
```

可验证：选择商品并保存画像、上传商品图片、将商品加入/移出必吃榜，然后回到客服前台询问推荐，确认推荐仍由后端商品和库存事实驱动，并返回图片附件。

上线前可在后端 `.env` 设置 `ADMIN_TOKEN` 开启管理 API 保护；前端管理页面需通过部署环境提供同值的 `NEXT_PUBLIC_ADMIN_TOKEN`（仅适用于当前 Demo，生产环境应替换为服务端会话认证）。

## Validation Scenarios

1. **未知需求**：输入“你好，我想咨询一下”，预期 Agent 最多提出两个核心澄清问题，并保持 `WAITING_USER` 或继续识别目标。
2. **库存**：输入“全麦吐司还有货吗？”，预期返回商品规格、库存数量、查询时间；模拟缺货时给出替代商品或人工选项。
3. **推荐**：输入“给孩子早餐吃，有什么低糖的？”，预期返回不超过三个满足硬约束且有库存的候选，并显示推荐理由。
4. **退货/换货**：输入“我昨天买的贝果能换成原味吗？”，预期依次识别订单、查询替代商品库存、判断资格，最后等待明确确认后才创建申请。
5. **人工接管**：输入超出授权范围的退款/赔偿请求，或连续三轮无法澄清，预期进入 `HANDOFF` 并保留上下文。
6. **重复保护**：对同一换货确认重复提交，预期返回同一个申请结果，不产生第二个申请。

## Evaluation

运行固定场景评估集：

```bash
pytest backend/tests evals -q
```

至少输出以下指标：Goal 识别正确率、Tool 选择正确率、必要参数完整率、错误执行率、未经确认执行退款数量、任务解决率。目标值见 [spec.md](./spec.md) 的 SC-001 至 SC-007。

## Validated MVP Run

当前 mock MVP 已验证：种子数据可加载、健康检查返回 `{"status":"ok"}`、库存查询可返回结构化 Inspector 结果，后端测试集通过。前端依赖安装后执行 `npm run typecheck` 和浏览器冒烟场景。

## V2 Multi-Agent Validation

V2 当前先验证契约、路由和共享状态，不要求接入真实图片识别或真实售后系统。

1. **Commerce 路由**：输入“要两个低糖欧包，一个红豆面包”，预期路由到 Commerce，调用 `calculate_order_quote`，并把结果写入共享 `quote_context`。
2. **Commerce 内部目标切换**：继续输入“那有什么吐司吗？”，预期仍由 Commerce 处理，切换到 `INVENTORY_CHECK`，不得把 `KEEP` 误判为修改报价。
3. **跨域路由**：先完成商品报价，再输入“刚收到，发现送错了”，预期 Supervisor 创建 `HANDLE_WRONG_ITEM_COMPLAINT` AgentTask 并切换到 After-sales，保留订单和商品上下文。
4. **售后证据边界**：提供图片附件元数据后，预期生成 `EvidenceObservation`；不得直接创建退款，必须先经过政策评估和确认/人工审批。
5. **赔付边界**：输入“赔偿500元”，预期根据 Resolution Ladder 返回政策允许的补发、单品退款或人工审批选项，不得承诺超出政策的金额。
6. **共享状态**：跨 Agent 检查 `recent_products`、`selected_products`、`quote_context`、`current_order` 和 `complaint_context`，确认目标 Agent 不需要客户重复描述。

建议新增验证指标：Supervisor Domain Accuracy、AgentTask Schema Accuracy、跨 Agent Context Retention、Unauthorized Side-effect Count、Evidence-to-Policy Completion Rate 和 Human Handoff Context Completeness。

### V2 Validation Result (2026-08-24)

- Backend: 87 passed
- Frontend: `npm run typecheck` passed
- SC-001～SC-009: all passed in `evals/runner.py`
- Supervisor Domain Accuracy: 1.0
- Unauthorized Side-effect Count: 0
- AgentTask Schema Accuracy: 1.0

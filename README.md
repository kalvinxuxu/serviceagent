# Shanye Shop Demo

组件化虚拟电商客服 Agent。后端 MVP 已支持：未知意图澄清、库存查询、商品推荐、订单识别、退货确认和严格 JSON Planner 输出。

## Run backend

```powershell
python -m uvicorn backend.app.main:app --reload
```

## Run the full local stack

```powershell
docker compose up --build
```

The Compose stack runs PostgreSQL, the FastAPI backend, and the Next.js frontend. The browser uses `http://localhost:3000` and the backend API uses `http://localhost:8000`.

Session checkpoints, actor-tagged messages, and reservations are persisted in PostgreSQL. `LLM_PROVIDER=mock` is used by Compose for deterministic local smoke tests.

## Test

```powershell
python -m pytest backend/tests -q
```

Planner 输出使用 Pydantic 结构化模型；校验失败不会执行工具。

项目目录说明见 [`docs/project-layout.md`](docs/project-layout.md)。运行日志和本地运行状态归档在 `runtime/`，不会混入源码目录。

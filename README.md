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

## Deploy with Vercel + Railway

本项目采用 Vercel 部署 `frontend/`，Railway 部署 `backend/` 和 PostgreSQL。两边都连接 GitHub `main` 分支。

### Railway backend

1. 在 Railway 新建项目，添加 PostgreSQL 服务。
2. 从 GitHub 导入 `kalvinxuxu/serviceagent`，Root Directory 保持仓库根目录。
3. 将 Dockerfile Path 设置为 `/backend/Dockerfile`。
4. 添加 PostgreSQL Reference Variable：

   ```text
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```

5. 配置 `LLM_PROVIDER=mock`、`CORS_ORIGINS`，以及需要时的 `ADMIN_TOKEN`。
6. 生成 Public Domain，并确认 `https://<railway-domain>/health` 返回 `{"status":"ok"}`。

Railway 会为服务提供 `PORT`；Dockerfile 已配置为监听该端口。Railway 的 PostgreSQL 连接变量和服务引用方式见[官方文档](https://docs.railway.com/databases/postgresql)。

### Vercel frontend

1. 从 GitHub 导入同一仓库。
2. 将 Root Directory 设置为 `frontend`，Framework 选择 Next.js，其余构建设置保持默认。
3. 配置以下 Production 环境变量：

   ```text
   NEXT_PUBLIC_BACKEND_URL=https://<railway-domain>
   NEXT_PUBLIC_API_URL=https://<railway-domain>
   ```

4. 将 Vercel 域名加入 Railway 的 `CORS_ORIGINS`，例如：

   ```text
   https://<vercel-domain>,http://localhost:3000
   ```

Vercel 的 monorepo Root Directory 配置见[官方文档](https://vercel.com/docs/monorepos)。

### Demo storage note

Railway 演示服务中的本地上传、证据和报告目录不作为长期存储；重新部署后不保证保留。正式环境应接入对象存储或 Railway Volume。不要将 `.env`、数据库文件、日志或 Token 提交到 GitHub；`NEXT_PUBLIC_ADMIN_TOKEN` 不应存放真实管理员密钥。

### Deployment smoke test

```powershell
Invoke-WebRequest https://<railway-domain>/health
Invoke-WebRequest https://<railway-domain>/docs
Invoke-WebRequest https://<vercel-domain>
```

然后在前端创建 session、交替测试用户 A/B/C，并确认订单、金额、取货方式和 trace 均未串用户。

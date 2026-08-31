# Implementation Plan: 自主规划客服智能体

**Branch**: `001-autonomous-customer-service-agent` | **Date**: 2026-08-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-autonomous-customer-service-agent/spec.md`, supplemented by the user's simulated e-commerce environment brief.

## Summary

构建一个不连接真实电商平台的模拟商城客服 Agent。Agent 从开放式中文消息开始，维护会话状态，识别一个或多个目标，以“只规划下一步”的方式选择提问、工具调用、确认、回复或人工接管；工具通过模拟商品、库存、订单、物流、退货规则和会员数据完成可演示闭环。推荐首版采用规则过滤与排序，LLM 仅负责理解自然语言约束和生成可读解释。

## Technical Context

**Language/Version**: Python 3.11+；前端 TypeScript 5+

**Primary Dependencies**: FastAPI、LangGraph、Pydantic、SQLAlchemy；Next.js、React；PostgreSQL；LLM provider adapter

**Storage**: PostgreSQL；开发环境允许 SQLite 作为单机替代，但生产模型以 PostgreSQL 为准

**Testing**: pytest 单元/集成测试；API 合约测试；前端组件与端到端冒烟测试；固定场景评估集

**Target Platform**: 本地开发或 Linux 容器；桌面浏览器访问中文客服页面

**Project Type**: Web application（Next.js 前端 + FastAPI Agent 服务）

**Performance Goals**: 模拟数据查询 p95 < 300ms；普通单轮 Agent 响应在 10 秒内返回；单次会话默认最多 12 个规划/工具步骤

**Constraints**: 不接入真实淘宝、ERP、WMS 或支付系统；所有有副作用的退货/换货操作必须显式确认；工具失败不得编造结果；敏感信息最小化；v1 仅中文文本

**Scale/Scope**: 20–50 个虚拟商品、3 个虚拟客户及其订单/库存/物流/政策数据；单用户演示环境；覆盖订单查询、库存查询、推荐、退货/换货、FAQ 和人工接管

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

宪章文件目前仍是未填充模板，没有可执行的项目原则或否决性约束。当前设计与规格一致：范围保持 v1 最小化、业务逻辑与 Agent 编排分离、关键操作可追踪并可测试。Gate：PASS（待项目宪章正式填写后复核）。

## Project Structure

### Documentation (this feature)

```text
specs/001-autonomous-customer-service-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
└── tasks.md              # 由 $speckit-tasks 生成
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── agent/          # graph, state, planner, nodes, prompts
│   ├── tools/          # tool schemas and thin adapters
│   ├── domain/         # order, inventory, return, recommendation, policy
│   ├── db/             # models, session, seed data
│   ├── api/            # chat, session, inspector endpoints
│   └── main.py
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── app/                 # chat page and inspector panel
├── components/
├── lib/                 # API client and view models
└── tests/

data/
└── seed/                # deterministic demo catalog, customers, orders, policies

evals/
└── scenarios/           # fixed conversations and expected tool/goal outcomes
```

**Structure Decision**: 采用单仓库 web application 结构。`backend/app/agent` 只负责编排，`backend/app/domain` 负责可测试的业务规则，`backend/app/tools` 负责向 Agent 暴露统一工具，前端同时展示聊天结果和开发态 Agent Inspector。模拟数据与评估场景独立于代码，便于后续替换真实数据源。

**Component Delivery Rule**: 每个组件先定义版本化输入/输出契约、状态/错误边界和独立测试，再接入上层组件。推荐交付顺序为：状态与协议 → 模拟数据访问 → 领域服务 → 工具适配 → Planner 与 Graph 路由 → API → 前端聊天与 Inspector → Trace 与评估。组件替换通过契约测试保护，禁止让上层直接依赖下层内部实现。

## Complexity Tracking

无宪章违规；不需要复杂度豁免。

## Phase 0: Research Decisions

研究结论记录在 [research.md](./research.md)，解决了模拟环境、动态一步规划、分层边界、组件化交付、规则化推荐、确认/幂等和 Trace 设计等技术选择。

## Phase 1: Design Outputs

- [data-model.md](./data-model.md)：会话状态、目标、计划、业务实体、Trace 和状态转换。
- [contracts/api.md](./contracts/api.md)：聊天、会话、确认、Trace 和统一工具结果契约。
- [quickstart.md](./quickstart.md)：本地启动、模拟数据初始化、端到端验证和评估命令。

## Post-Design Constitution Check

PASS。设计未引入宪章模板之外的约束；副作用确认、可追踪、分层和可测试性均已写入数据模型、接口契约与验证场景。项目宪章正式填充后需再次复核。

## V2 分层多 Agent 扩展计划

### Architecture

```text
Customer Message
      ↓
Supervisor / Case Manager
      ↓
Shared Customer Service State
      ├── Commerce Agent
      │     ├── Product / Inventory
      │     ├── Recommendation Service
      │     └── Pricing / Promotion / Membership Service
      ├── After-sales Agent
      │     ├── Order / Evidence
      │     ├── Claims Policy
      │     └── Resolution Service
      └── Human Handoff
```

Supervisor 只负责服务域识别、Goal 管理、Agent 路由、Agent 切换、完成状态和人工接管，不负责价格、库存或赔付判断。

### Agent Boundaries

- `SupervisorAgent`：输出目标、服务域、路由任务、优先级和切换原因。
- `SupervisorAgent`：输出目标、服务域、路由任务、路由模式和切换原因。混合目标必须显式输出任务列表及每个任务的 `status`、`depends_on`、`blocked_reason`；禁止使用隐式的“价格优先”或“库存优先”覆盖策略。
- `CommerceAgent`：处理商品发现、库存、推荐、报价、会员和促销解释；不得执行退款、补偿或目录维护。
- `AfterSalesAgent`：处理订单、错发/漏发/破损/质量投诉、证据收集、政策评估和受约束解决方案；不得修改商品、库存或促销配置。
- `AfterSalesAgent` 的 Resolution Ladder 固定分为 `EXPLAIN`、`REPLACEMENT`、`ITEM_REFUND`、`PARTIAL_REFUND_COMPENSATION`、`FULL_REFUND`、`HUMAN_APPROVAL` 六级；每次决策必须携带政策版本、允许等级、推荐等级、确认要求和人工审批要求。
- Recommendation、Pricing、Promotion、Membership、Inventory 继续作为确定性 Domain Service/Tool，不拆成独立 Agent。

### Shared State and Handoff

所有 Agent 读写统一 `CustomerServiceState`。Agent 之间通过版本化 `AgentTask` 传递脱敏相关上下文，不直接复制完整聊天记录。

共享状态必须为字段定义类型、生命周期、写入 Agent、版本号和冲突策略。领域 Agent 只能写入授权片段；Supervisor 只能路由和更新任务状态，不能覆盖商品、订单、库存或报价事实。

### Delivery Strategy

1. 先定义 Supervisor、Commerce、After-sales 的接口和共享状态。
2. 将现有商品、库存、报价路径封装为 Commerce Agent，保持工具契约兼容。
3. 将现有订单、退货和人工接管路径封装为 After-sales Agent，先支持文本证据。
4. 增加 Supervisor 路由、Agent handoff 和 Trace，保留单 Agent fallback。
5. 增加图片附件与证据观察契约；视觉组件只输出证据分类，不直接决定退款或赔偿。
6. 增加 Resolution Ladder、售后政策评估和跨 Agent Golden Path。

### V2 Constitution Check

PASS。该拆分遵守组件契约、结构化规划、确定性业务服务、确认前副作用、可观测和最小复杂度原则。

## Phase 23：客服前台与商品清单式管理后台

### Architecture

```text
/              Customer UI
/admin         Admin UI
    ↓
FastAPI /api/v1
    ├── Agent Runtime
    ├── Product / Media / Featured APIs
    ├── Memory / Trace / Benchmark APIs
    └── Domain Services + Database
```

客服前台和管理后台属于同一个 Next.js 应用的不同路由；两者都只能通过 API 访问后端，不能直接访问数据库。管理后台首期定位为高密度商品清单，不承担 ERP、采购、财务或复杂权限系统职责。

### Admin UI Modules

- 商品清单主表：名称、品类、堂食价、当前优惠价、库存、主图、展示标签、在售状态和行级操作。
- 商品画像：事实属性、销售属性、人群适配、别名和审计信息。
- 图片管理：上传、预览、绑定商品、替换和缺失提示。
- 必吃榜：启用状态、标题说明、商品增删和排序。
- 质量入口：后续展示 Benchmark、Trace 和首个失败组件；本阶段先复用已有报告接口。

### Component Boundaries

- `AdminProductList`：读取和编辑商品展示字段，失败时保留未提交编辑。
- `AdminProductProfile`：提交结构化画像 JSON，后端校验事实字段并写审计。
- `AdminMediaManager`：上传图片并只接收后端返回的 `media_id`/URL。
- `AdminFeaturedBoard`：只提交商品 ID 列表，后端验证商品存在并持久化排序。
- `AdminMemoryPanel`：按 `customer_id` 查看和删除记忆，不显示其他客户数据。

### API and Safety Rules

- 所有维护请求必须经过 Admin API 的 Pydantic 校验。
- 图片必须使用 `multipart/form-data` 上传，后端执行扩展名、大小、哈希和安全存储校验。
- 商品价格只允许非负数；榜单商品必须存在于当前目录。
- 每次商品、媒体、榜单和记忆变更必须写入审计记录。
- 当前 Demo 不包含正式认证；部署前必须增加管理员身份验证和权限控制。

### Product Admin View Model

商品清单不直接消费数据库模型，而使用后端聚合的 `ProductAdminView`：

```json
{
  "id": "SKU001",
  "name": "原味贝果",
  "category": "贝果",
  "dine_in_price": 10,
  "member_price": 8,
  "promotion_price": null,
  "display_discount_price": 8,
  "inventory": {"available_quantity": 3, "status": "IN_STOCK"},
  "primary_media": {"media_id": "MED001", "url": "/api/v1/media/MED001", "alt": "原味贝果"},
  "display_tags": ["原味", "早餐", "儿童"],
  "status": "ON_SALE"
}
```

`dine_in_price` 是堂食新定价；`member_price` 和 `promotion_price` 分开保存，`display_discount_price` 由后端根据当前政策计算。库存、图片和展示标签由后端聚合，前端不得自行推导业务事实。

### Validation Gates

- 客服前台不受 Admin UI 变更影响，图片缺失仍可返回文本推荐。
- 商品画像保存后重新加载仍保持事实、销售和人群属性。
- 上传图片后客服推荐能收到对应媒体附件。
- 必吃榜增删和排序在重启后保持一致。
- 客户记忆只能被同一 `customer_id` 读取或删除。
- 管理接口非法输入不修改数据库，并返回结构化错误。

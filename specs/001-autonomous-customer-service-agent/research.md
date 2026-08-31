# Research: 自主规划客服智能体

## Decision 1: 使用模拟商城作为 v1 业务环境

- **Decision**: 内置 20–50 个商品、3 个客户，以及订单、库存、物流、退货规则、会员和 FAQ 数据；不连接真实淘宝、ERP、WMS 或支付系统。
- **Rationale**: 先验证 Agent 的状态、规划、工具调用、确认和接管能力，避免外部接口、权限和数据质量掩盖核心问题；数据可重复，便于自动化评估。
- **Alternatives considered**: 直接接真实电商系统——延期和风险更高；只使用内存字典——难以演示持久化、审计和多轮会话。

## Decision 2: 使用动态的一步规划

- **Decision**: Planner 每轮只返回一个 `NextAction`：`TOOL`、`ASK_USER`、`ASK_CONFIRMATION`、`RESPOND` 或 `HANDOFF`；工具结果回写状态后重新规划。
- **Rationale**: 客服对话会持续补充和改变信息，短计划比预先生成十步计划更稳健；统一动作结构让 Graph 路由、审计和测试可控。
- **Alternatives considered**: 一次生成完整长计划——容易因早期假设失效而执行过时步骤；简单“意图分类→回复”——无法表达观察、重规划和副作用确认。

## Decision 2A: Planner 下游协议采用严格 JSON Schema

- **Decision**: Planner 向 Router/Tools 输出版本化 JSON Schema，通过 Pydantic Structured Output 校验；Schema 至少表达目标、目标状态、单个 `next_action`、工具参数、原因代码、缺失信息和确认要求。
- **Rationale**: 下游需要稳定字段、明确类型、可校验和可直接路由；JSON 是协议载体，Schema 才是可执行契约。校验失败时禁止工具执行，避免 Markdown 解析和自由 JSON 带来的隐性错误。
- **Alternatives considered**: Markdown——适合人读但需要脆弱的正则/解析器；XML——可结构化但与当前 Python/JS 工具调用链不如 JSON 直接；自由格式 JSON——有载体但没有稳定契约。

## Decision 3: 业务逻辑与 Agent 编排分层

- **Decision**: `domain` 实现订单、库存、退货、推荐和政策规则；`tools` 只做参数校验和适配；`agent` 负责理解、规划、路由、评估和回复。
- **Rationale**: 规则可独立测试，后续替换模拟数据源时不需要重写 Agent；避免把业务逻辑埋在 Prompt 或工具函数中。
- **Alternatives considered**: 所有逻辑写在 Graph 节点中——难以复用和测试；工具直接访问数据库并完成规则——边界不清、审计困难。

## Decision 3A: 采用组件化、契约驱动的增量交付

- **Decision**: 将状态、协议、数据访问、领域服务、工具、Planner/Graph、API、前端和评估拆成独立组件；每个组件先完成输入/输出契约、错误边界和独立测试，再由上层组合。
- **Rationale**: 适合以积木方式学习和演示 Agent；可以先验证局部能力，降低一次性集成风险，并允许未来用真实业务服务替换模拟组件。
- **Alternatives considered**: 先写完整 Graph 再补业务层——调试边界模糊；按文件随意拆分——目录看似模块化，但没有契约和替换保障。

## Decision 4: 推荐首版规则化

- **Decision**: LLM 提取“低糖、早餐、儿童、预算”等自然语言条件；领域服务负责硬约束过滤、库存过滤和推荐分排序，最多返回三个候选。
- **Rationale**: 推荐结果可解释、可复现且不容易推荐缺货或违反硬约束的商品；保留后续引入更复杂排序模型的空间。
- **Alternatives considered**: 首版直接使用向量/个性化推荐——数据量不足且难验证；完全由 LLM 推荐——可靠性和库存一致性不足。

## Decision 5: 关键业务操作采用显式确认和幂等保护

- **Decision**: 创建退货/换货前必须生成确认动作；确认后由领域服务执行，并以会话与订单项维度防止重复申请；高风险或不确定情况转人工。
- **Rationale**: 满足规格中“未经确认执行退款为 0”的目标，也避免重复消息导致重复副作用。
- **Alternatives considered**: Agent 判断意图后直接执行——风险不可接受；所有请求都人工——失去自动化演示价值。

## Decision 6: 记录可解释 Trace

- **Decision**: 每次会话保存 run、step、工具调用、观察结果、计划变更、客户确认和最终状态；Inspector 展示当前目标、下一步、最近工具及结果。
- **Rationale**: 能区分理解错、规划错、工具错、规则错和表达错，支持评估与调试。
- **Alternatives considered**: 只记录最终聊天文本——无法解释 Agent 为什么采取某一步。

## Resolved Technical Choices

- Backend: Python 3.11+ / FastAPI / LangGraph / Pydantic / SQLAlchemy。
- Frontend: Next.js + TypeScript，单页聊天界面加开发态 Inspector。
- Storage: PostgreSQL；允许 SQLite 作为本地快速启动替代。
- Testing: pytest、API contract tests、前端冒烟测试、固定对话评估集。
- LLM: 通过 provider adapter 接入 OpenAI 或 DeepSeek；业务规则不依赖某一家模型。

## V2 Multi-Agent Decisions

### Decision 7: 采用 Supervisor + Commerce + After-sales 三层 Agent

- **Decision**: 使用一个 Supervisor/Case Manager、一个 Commerce Agent 和一个 After-sales Agent；不为推荐、会员、促销、定价、库存分别创建 Agent。
- **Rationale**: Supervisor 负责跨域路由，Commerce 负责形成可购买方案，After-sales 负责订单、证据、政策和解决方案；确定性查询、计算、过滤和排序继续留在 Domain Service。
- **Alternatives considered**: 一个万能 Agent 会导致职责和工具权限膨胀；每个工具一个 Agent 会造成上下文切换和编排成本过高。

### Decision 8: 使用共享会话状态和结构化 AgentTask

- **Decision**: 所有 Agent 共享 `CustomerServiceState`，Supervisor 通过版本化 `AgentTask` 传递相关上下文，不把完整历史对话复制给下游 Agent。
- **Rationale**: 保证商品指代、订单和报价上下文跨域可用，同时减少上下文噪声、隐私暴露和 token 成本。
- **Alternatives considered**: 每个 Agent 独立记忆容易丢失事实；完整聊天转发上下文过长且难以审计。

### Decision 9: 售后采用证据分类与政策决策分离

- **Decision**: After-sales Agent 可以接收文本、订单和图片附件；视觉组件只输出问题类型、证据和置信度，Policy/Resolution Service 决定允许的解决层级，副作用仍需确认。
- **Rationale**: 防止模型直接根据图片承诺退款、补偿或食品安全结论。
- **Alternatives considered**: 视觉模型直接调用退款风险不可审计；完全人工处理又失去自动化验证价值。

### Decision 10: V2 采用渐进迁移

- **Decision**: 先建立 Agent 契约和路由，再包装现有单 Agent 能力；保留旧 Graph fallback，按 Commerce、After-sales、Supervisor 顺序逐步替换。
- **Rationale**: 使用现有库存、报价、推荐、退货和 Trace 测试保护迁移过程。
- **Alternatives considered**: 一次性重写 Graph 风险高且难以定位行为变化。

## Decision 11: 客服前台与管理后台共用 Next.js、通过 API 隔离

- **Decision**: `/` 作为客服前台，`/admin` 作为管理后台，二者复用前端工程但不共享数据库访问；所有维护通过 FastAPI Admin API 完成。
- **Rationale**: 单一前端工程降低部署和依赖成本，路由边界已足够支持 Demo；API 隔离保证商品事实、媒体、库存和审计仍由后端统一控制。
- **Alternatives considered**: 单独维护两个前端项目——初期重复组件和部署成本更高；让 Admin UI 直连数据库——破坏权限、审计和领域服务边界。

## Decision 12: 图片采用后端托管的 multipart 上传

- **Decision**: 浏览器上传文件到 Admin API，由后端校验、哈希去重、复制到受控存储并返回媒体元数据；客服回复只消费媒体 URL/ID。
- **Rationale**: 浏览器不能可靠提供本地路径，后端托管可统一安全校验、审计和跨环境部署。
- **Alternatives considered**: 提交本地文件路径——仅适合开发机且存在路径越权；让 LLM 直接处理路径——不可审计且会泄露内部存储结构。

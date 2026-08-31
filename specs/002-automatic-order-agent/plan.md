# Implementation Plan: 自动接单订单智能体

**Branch**: `002-automatic-order-agent` | **Date**: 2026-08-31 | **Spec**: [spec.md](./spec.md)

## Summary

在现有模拟商城客服应用中增加独立的订单邮件运营流程：接收模拟邮件、结构化解析订单、匹配商品、查询库存和价格、生成回复草稿，并在人工确认后执行模拟发送。编排层只消费版本化组件契约；商品、库存、价格和幂等发送由确定性领域服务负责。V1 不连接真实邮箱、ERP、WMS、支付或物流系统。

## Technical Context

**Language/Version**: Python 3.11+；前端 TypeScript 5+

**Primary Dependencies**: FastAPI、Pydantic、现有 Agent/Graph 运行时；Next.js、React；现有模拟数据访问层

**Storage**: 复用当前会话/Trace 持久化方式；V1 允许本地模拟存储，接口不绑定具体数据库模型

**Testing**: pytest 单元、组件契约、集成和安全边界测试；前端类型检查/冒烟测试；固定订单邮件评估场景

**Target Platform**: 本地开发或 Linux 容器中的 Web 应用

**Project Type**: Web application（现有 Next.js 前端 + FastAPI 后端）

**Performance Goals**: 信息完整的模拟订单在 10 秒内生成草稿；模拟目录/库存查询 p95 < 300ms；单次处理默认不超过 12 个规划/工具步骤

**Constraints**: 中文纯文本、模拟邮箱和模拟商城；发送必须人工确认；结果不可编造；敏感信息最小化；重复邮件/发送请求幂等

**Scale/Scope**: 单用户演示环境，20–50 个虚拟商品，覆盖单商品、多商品、部分库存、缺失信息、重复邮件和发送失败

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Component Contracts First：PASS。解析、匹配、库存、草稿、发送和审计均定义独立契约。
- Structured Planning and Safe Execution：PASS。Planner 输出结构化订单动作，校验通过后才调用工具。
- Confirmation Before Side Effects：PASS。模拟发送需要当前草稿版本的显式人工确认和幂等标识。
- Test-First Delivery and Measurable Quality：PASS。每项成功标准映射到固定场景和契约/集成测试。
- Observable, Minimal, and Privacy-Aware Operation：PASS。所有关键阶段写入脱敏 Trace，展示最小必要字段。
- V1 simulated-shop boundary：PASS。无真实邮箱、ERP、WMS、支付或物流调用。

## Project Structure

```text
specs/002-automatic-order-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
└── checklists/requirements.md

backend/app/
├── agent/                 # 复用 Planner/Graph，增加订单邮件路由
├── domain/                # 订单解析结果、目录匹配、库存/价格、草稿与幂等发送
├── repositories/          # 模拟邮件、商品、库存和发送结果适配器
├── tools/                 # 订单解析、库存核验、草稿和发送工具契约
└── api/                   # 邮件接入、订单草稿、确认和 Trace 接口
backend/tests/{unit,contract,integration,security}/
frontend/app/admin/orders/ # 订单邮件队列与人工确认页面
frontend/components/       # 订单摘要、库存结果、回复草稿和确认控件
evals/scenarios/order_email_v1.json
```

**Structure Decision**: 复用现有单仓库 Web 应用，在后端按现有 `agent/domain/tools/api` 边界增加订单邮件能力；前端放入管理后台订单队列，避免改变现有客服会话主流程。模拟适配器隔离外部邮箱和库存系统，未来可替换而不改变上层契约。

## Complexity Tracking

无宪章违规，不需要复杂度豁免。

## Phase 0: Research Decisions

研究结论记录在 [research.md](./research.md)，涵盖外部接入边界、解析置信度、库存状态、草稿事实一致性、确认幂等和 Trace。

## Phase 1: Design Outputs

- [data-model.md](./data-model.md)：订单邮件、订单草稿、订单项、库存核验、回复草稿、发送记录和状态转换。
- [contracts/api.md](./contracts/api.md)：邮件接入、草稿查询/修改、核验、确认发送和统一失败结果契约。
- [quickstart.md](./quickstart.md)：启动、测试和六类端到端验收场景。

## Post-Design Constitution Check

PASS。设计将发送限制在显式确认、版本校验和幂等控制之后；所有失败保持可见；没有引入真实外部副作用；数据模型、契约和验证场景与规格中的 FR/SC 对齐。

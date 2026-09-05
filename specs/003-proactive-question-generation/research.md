# Research: 主动问题生成（PQG）

## Decision 1: 双候选源统一编排

**Decision**: 将历史检索与 LLM 生成定义为两个可替换候选源，由统一服务负责合并、去重、排序和安全过滤。

**Rationale**: 检索提供真实业务表达和频次依据，LLM 提供新场景泛化能力；源之间解耦便于单独测试、降级和替换。

**Alternatives considered**: 只使用 LLM 会失去历史数据校准；只使用检索无法覆盖新场景；在 UI 层直接合并会绕过后端安全边界。

## Decision 2: 严格版本化 JSON 输出

**Decision**: LLM 只能返回版本化 JSON；后端先完成结构、数量、文本、安全和相关性校验，再转成内部候选。

**Rationale**: 禁止从 Markdown 或自然语言推断结构，符合现有结构化规划原则，也能稳定支持多模型 provider。

**Alternatives considered**: 正则提取或容错解析不可预测，可能把模型解释、提示注入或虚构事实展示给顾客。

## Decision 3: 异步、可失败的增强流程

**Decision**: 原客服回复先完成；PQG 独立运行并返回 `READY`、`EMPTY`、`SUPPRESSED` 或 `DEGRADED` 状态。

**Rationale**: LLM 或检索异常不应影响核心客服体验，并可满足原回复时延约束。

**Alternatives considered**: 同步等待两路结果会放大外部 provider 延迟和故障。

## Decision 4: 建议只填入输入框

**Decision**: 顾客点击候选后填入输入框，不自动发送、不自动下单、不触发支付或其他外部副作用。

**Rationale**: 促进销售仍需保留顾客意图确认，符合现有副作用确认原则。

**Alternatives considered**: 点击即发送虽然减少一步操作，但可能造成误发和未经确认的业务行为。

## Decision 5: v1 使用脱敏历史库和现有 provider 边界

**Decision**: v1 复用现有 LLM provider factory，兼容 Kimi、智谱等配置；历史语料必须授权、脱敏并可审计，不新增真实外部业务系统连接。

**Rationale**: 保持模拟商城边界和隐私最小化，同时允许后续替换模型或索引实现。

**Alternatives considered**: 直接把完整历史原文发送给外部模型会扩大隐私和合规风险；直接接入真实交易数据超出本特性范围。

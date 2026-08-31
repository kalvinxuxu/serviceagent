# Research: 自动接单订单智能体

## Decision: V1 使用模拟邮件适配器，不接入真实邮箱

**Rationale**: 项目宪章要求停留在 simulated-shop boundary；模拟适配器可稳定复现重复邮件、超时和发送失败，便于评估。

**Alternatives considered**: Gmail/Outlook OAuth、IMAP 轮询。两者都会引入凭据、权限、网络和真实发送风险，超出 V1。

## Decision: 解析结果采用“字段值 + 置信/来源 + 问题”结构

**Rationale**: 字段级状态支持最少必要追问、人工修订和审计，避免整体摘要掩盖数量或地址错误。

**Alternatives considered**: 仅输出自然语言摘要；无法做可靠校验，也不满足结构化规划约束。

## Decision: 商品匹配、库存和价格由确定性服务负责

**Rationale**: LLM 适合理解文本，不应生成 SKU、库存或金额；复用现有目录/库存服务可确保结果可验证且可替换。

**Alternatives considered**: 让模型直接回答库存或价格；会产生不可审计、不可验证的承诺。

## Decision: 回复先生成草稿，发送需要草稿版本确认

**Rationale**: 对外订单承诺是副作用。确认绑定收件人、事实快照和草稿版本，人工修改后旧确认自动失效。

**Alternatives considered**: 自动发送完整订单；风险与宪章冲突，不适合 V1。

## Decision: 以来源邮件标识和发送幂等键防重复

**Rationale**: 分别对“订单创建”和“发送动作”去重，覆盖邮件重投和网络重试。

**Alternatives considered**: 仅依赖前端按钮禁用；无法防止重复请求或服务重启后的重复副作用。

## Decision: 关键阶段统一写入脱敏 Trace

**Rationale**: 评估需要知道解析、匹配、核验和确认在哪一步失败，同时遵守最小必要信息原则。

**Alternatives considered**: 只记录最终回复；无法审计错误承诺和人工修改影响。

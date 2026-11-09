# B01 零计费替代资源复核

结论：找到同 Go 协议的候选，但严格金额上界仍为 NULL；B01 只继续阻塞 LIVE 支路。

官方当前列出 longcat-2.5-preview-free，接口和 SDK 与现有 DeepSeek Go 路线相同。三项 token 费免费，缓存写入只列横线且促销限时；不能据此推断隐藏计费、思考或内部重试都为零。[Go 官方文档](https://opencode.ai/docs/go/)

Zen 的其他免费 chat 模型使用另一 /zen/v1 路线，现有 Go 凭据权限未验证。[Zen 官方文档](https://opencode.ai/docs/zen/)

既有公开 models.dev 2026-10-06 快照显示 LongCat 的 tool_call/reasoning_content 与零 input/output/cache_read；这是旧元数据，不能升级为当前部署合同。Big Pickle 四字段零但仅有 Zen 路线；Space Bunny Free 的旧 Go 条目已 deprecated。当前无实际工具调用资格。

|维度|结论|
|---|---|
|Uncached input|Free on current Go model row；部署生效价格仍 NULL|
|Visible output|Free on current Go model row；部署生效价格仍 NULL|
|Cache read|Free on current Go model row；部署生效价格仍 NULL|
|Cache write / creation|Dash, no explicit meaning supplied；部署生效价格仍 NULL|
|Thinking / reasoning output|No separate all-inclusive zero-cost guarantee；部署生效价格仍 NULL|
|Gateway / upstream attempts, fallback, retries|No charge coverage / no-paid-fallback attestation；部署生效价格仍 NULL|
|Per-request fixed / other fees|No exact model-route all-inclusive zero-fee attestation；部署生效价格仍 NULL|
|Go workspace quota / Use balance / BYOK|General options exist; private state not observed；部署生效价格仍 NULL|
|Promotion lifetime / current request applicability|Limited time with no enforced request lease；部署生效价格仍 NULL|

严格 0 的闭合路线是取得全计费维度、无付费回退、请求生效期和实际部署/凭据分支契约，然后由 Root 冻结新 model/profile 与 PREPARED 前预算门。最终真实 SDK/tool-call/取消/恢复/产物资格需要独立验证；本支路没有模型请求。

W05/A04 允许选一种授权真实执行器，用户也授权模型选择；因此可显式准备新候选。A04 的 fixed model 规则仍禁止当前运行被路由器静默替换。换模型不重置旧 B01 或失败计数。

读取密钥、billing 设置、私有 API、模型调用、配置/source/canonical 修改、正式接受均为 0。本轮只有一次公开文档 Edit-link 点击 Internal Error，原始全 I/O 已封，outer/native numeric NULL；无重试、不改 Root 固定 cut。


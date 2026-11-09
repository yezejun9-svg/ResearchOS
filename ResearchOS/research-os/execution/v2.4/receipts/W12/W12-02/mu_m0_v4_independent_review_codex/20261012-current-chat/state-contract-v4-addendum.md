# V4 independent review — state contract addendum

本文件仅为下一次 Source 修复的架构输入，不修改 Source，也不扩大 same9 写入授权。真实凭据、网络和真实模型调用均为 0；反例中的敏感值均为合成占位值，本文件不收录其原值。

1. **使用单一、有版本的检查点 DTO。** 根对象的键白名单不能代替消息、content、queue item 和 custom details 的运行时类型校验。export 与 restore 应共用同一套校验规则，覆盖 public transcript、runtime context、prepared/pending messages、steering/followUp 的每条消息及其 sequence；不能让一个路径验证、另一个路径绕过。thinkingLevel 必须匹配当前 SDK 的 off/minimal/low/medium/high/xhigh/max；runtime reasoning 的 undefined 与非 off 值按对应类型分别验证。验证完成前不得修改目标 Agent 或启动恢复工作。

2. **保留 SDK 消息兼容性，同时声明扩展的持久化边界。** AgentMessage 是基础 Message 与 CustomAgentMessages 的联合类型，不能简单只允许 user/assistant/toolResult，也不能因为 role 是字符串就接受任意对象。基础 system/user/assistant/toolResult 应按当前 SDK 的具体字段及 content discriminant 校验，保留实际使用的 system sections/tool declarations、text/image/thinking/toolCall/usage/stopReason 等合法数据。coding-agent 还使用 bashExecution/custom/branchSummary/compactionSummary；其合法必需字段应有对应 schema。额外角色、customType/details、toolResult.details 或其他必要扩展数据需要由可信运行环境预先登记名称、版本和有界 JSON schema；不能由检查点注册、执行 codec/hook 或构造 extension 实例。当前 same9 无法表达所需登记接口时，应报告 Root 申请精确范围修改。

3. **数据选择应明确，禁止继续扩展敏感字段 denylist 作为主防线。** 未声明的 message/queue/extension 字段应拒绝；必要数据不可安全保存时应拒绝整个 checkpoint，不能静默删掉影响恢复的字段。明确禁止凭据、authorization headers、getApiKey、execute/hook/闭包和任意实例进入 DTO。模型只保存绑定引用与非敏感数据。自由文本和工具参数中的业务内容不能靠字段名称推断是否敏感：生产者须遵守不把凭据放入持久化消息的契约，确需扩展的数据由其显式 schema 与保密策略处理；本次反例证明的是未声明扩展字段绕过，而不是一般文本的自动秘密识别。沿用整体大小/深度/数量上限，并验证所有数值、枚举和消费序号关系。

4. **模型绑定从恢复持续到实际 dispatch。** 保存已选定模型的不可变 key/version/provider/api/id/signature；trusted registry 可解析模型，但不能让可变对象引用替代已记录身份。restore 时验证一次不足以防止 restore 与显式 resume 之间的配置变化。resume 开始前、恢复路径中任何准备 hook 返回后且 provider/getApiKey/onPayload/stream dispatch 前，应验证实际使用的模型仍匹配该帧绑定；配置发生获准变化时需要显式建立新的可信绑定，未知或不匹配则在下一次外部工作之前失败。可选择冻结/独立复制可信描述加 dispatch 复验；不要把 credential/header/endpoint 从检查点带回执行配置。此规则适用于被恢复的执行链，不能无意改变普通未使用 checkpoint 的 SDK 调用语义。

5. **工具允许集与注册全集分离。** continuation/runtime 中的本次允许工具名必须一致，并逐项解析到 state.tools + pauseToolRegistry 的可信登记；恰好一个实现、声明/签名/version 匹配。合法允许集可能不在 state.tools 中，所以不能再把 continuation.toolNames 强制限制为 checkpoint 根 toolNames 的子集。执行时始终用原请求允许子集，不扩大为注册全集；在每次未完成工具 dispatch 前复验其绑定，不重放已经完成的 ID。当前 before/after-request、tools、pendingFinish、afterTurn 均须遵守同一个规则。

6. **阶段与验证证据保持连续。** restore 只验证和装载数据；显式 resume 按记录的唯一下一步运行。保留 V3 的模型/context/subset、N1/N2/N5、steering watermark、error finish、重复 pause、cancel 优先与 default 行为回归。补充本次 E 合法 extra registry、F restore 后模型变化、G 未声明扩展字段、I 非法消息/枚举，以及 H 的 17 个拒绝用例。正确的普通消息与已声明必要 CustomMessage 数据须能 JSON roundtrip；不能用拒绝所有扩展来让负例通过。所有失败证据和 harness 纠正单独记录，不改历史计数或正式验收状态。

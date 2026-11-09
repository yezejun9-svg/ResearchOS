# M0 pause state contract — review guidance only

本文件是独审修复建议，不是 Source 修改或额外写入授权。

1. **持续保留同一个请求的有效运行状态。** `prepareRequest` / `prepareNextTurn` 选定的模型、thinking 配置、上下文消息与工具子集，应随 `request -> tools -> pendingFinish -> afterTurn` 转移保留。公开 transcript、当前运行上下文和待发消息具有不同用途，不能在恢复时用构造 Agent 的初始状态代替已经生效的请求状态。
2. **阶段决定恢复后的唯一下一步。** 保存已提交的准备阶段、完整工具批次/已完成 ID、终止聚合、待执行 finish 或已经提交的 finish 决定，以及队列消费序号。恢复自身不调用模型、工具、prepare 或 finish；显式 resume 从记录的下一步继续，已完成的回调和效果不能重放。推荐统一、互斥的阶段契约，不再用缺乏数据来源的布尔值修补每个复现。
3. **只序列化显式允许的数据。** 对消息与必要的扩展数据执行有版本、类型、大小与深度限制的 JSON 数据校验。禁止保存 API secret、API key、敏感 authorization header、`getApiKey` 函数、工具 `execute`/hook 函数，或任意 extension 实例/闭包。安全的模型引用与非敏感配置应单独声明；不要对完整 runtime、Model 或工具对象直接 JSON/structuredClone 后视为合格检查点。
4. **工具恢复必须保留原子集，并验证绑定。** 记录本次请求的允许工具引用、声明/签名和必要版本身份。restore 对预先登记的工具注册表逐项验证并解析实现；原请求没有的工具不得因为当前注册表中存在而加入。函数始终来自已登记实现，不由检查点构造。名称相同但签名/版本不符也不能替换原工具。
5. **模型与上下文同样需要绑定。** 用可安全解析的模型/配置引用及非敏感字段标识已选定模型，并核对 provider/model/config 等身份；不能在恢复中退回初始模型或接受未经绑定的 endpoint/credential。精确保留允许序列化的当前上下文和消息顺序，避免恢复被压缩或移除的旧内容。凭据由既有可信运行环境解析，不能由检查点携带。
6. **无法安全重建就 fail closed。** 不认识的版本/阶段、缺失或不匹配的模型/工具绑定、不可序列化的必要扩展数据、队列/结果序号矛盾，都应在启动工作之前拒绝，并保留原 checkpoint 与失败证据。不能静默回退全工具集、初始上下文/模型，也不能通过修改 checkpoint 或重置失败计数制造可恢复状态。

最小回归证据：保留本轮 V3-A response/finish 与 V3-B 工具子集反例及无暂停对照；保留原 N1/N2/N5、JSON roundtrip、单条队列序号、重复暂停、取消优先和默认行为测试。产品 CLI/WindowsDesktop/真实模型验收仍另计。

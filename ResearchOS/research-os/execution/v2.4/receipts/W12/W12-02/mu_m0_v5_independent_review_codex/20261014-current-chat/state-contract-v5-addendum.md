# V5 independent review — phase binding and typed DTO addendum

本文件为后续 Source 修复输入，不扩大 same9 写入范围，不修改 SDK，不提供 M1/M2 生产验收。保留 V3/V4 的全部冻结物、失败原始记录和已有 state contract。

## 严格判别，不进行隐式转换

内容联合类型的 discriminant 必须先是 string，再严格匹配受支持的 literal。`String(value)` 不能用于把 checkpoint 输入转成合法枚举：单元素数组可转换为 `text`，但后续 switch 仍面对数组，导致所有字段校验被跳过。每个分支必须校验完整字段集合，default 必须拒绝；同样复查 stopReason、constrainedSampling 等枚举，而不是只给本次数组反例加特判。export/restore/validatePauseMessage 对所有消息路径使用同一规则。

## 闭合 schema 只识别显式声明的 own property

对于 schema.properties 的声明查询、optional 列表验证和 payload 的必填字段查询，使用 own-property 语义。不能用 `key in object` 把 Object.prototype 上的 constructor、__proto__、toString 等视作声明。显式登记的合法业务字段仍需按它的 schema 验证；未声明字段必须拒绝。测试已证明普通 unknown key 会拒绝，但这三个继承名称可携带任意 JSON 数据并重新导出。这里证明的是闭合 schema 绕过，不宣称已发生原型污染或执行代码。所有试验值均为合成数据，真实凭据为 0。

## 恢复绑定属于当前阶段，不能永久锁住后续合法轮次

恢复 checkpoint 时，原 prepared/request、response、未完成 tools、pendingFinish 或已提交 finish 阶段必须使用其已选定的模型、配置、上下文与工具允许子集。该阶段没有完成之前，任何注册对象或实现漂移仍须在每次实际 dispatch 前拒绝，已完成 callback/effect 不可重放。

当该阶段完成、进入原有可信 prepareNextTurn/prepareRequest 所定义的下一阶段时，允许回调按照原配置选择已登记模型或工具子集。应明确提交新的阶段绑定，而不是继续使用闭包捕获的旧模型/旧工具集合。新绑定建立后继续执行 getApiKey/transform/convert 后及 provider/tool dispatch 前的复验。恢复链中新阶段的模型/工具引用必须解析到受信登记身份，不能把一个被篡改的 Model 对象重新计算 signature 后自动视作新的可信基线；也不能因为允许合法切换而把全部 registry 工具放入当前请求。

建议把“验证当前绑定”“可信阶段转换”“提交下一阶段绑定”分成明确操作，保留提交点与下一步位置；登记描述/版本应具有独立于可变实现对象的可信身份。当前 phase 内的 silent mutation 一律拒绝；原配置明确允许的阶段转换才可建立新绑定。若身份或阶段无法安全确定则 fail closed，保留原 checkpoint 和失败记录。

## 回归需要完整结束条件

保留本轮 J/K 的矩阵和 L 的无暂停对照：无暂停使用新登记模型/工具完成两次模型调用；恢复应得到相同序列且无错误。M 的四个异步篡改拒绝用例与 N 的 extra-registry excluded-tool 拒绝必须继续通过，不能用放松绑定检查换取 L 通过。

N5 不仅要检查两个工具效果，还要检查最终助手回复、预期模型调用数、无错误和已消费消息恰好一次。旧断言未覆盖最终完成条件，已保留原 raw 和新的 strengthened-n5 失败记录。三处 custom schema 兼容性适配只登记既有 typed custom 数据，未改变旧 payload 或断言，不回写 V4 历史。

## Run 身份边界

本轮仅审查 M0 检查点原语与合成协议。候选协议的 runId 只用于 checkpoint/ACK 身份绑定，没有实现真实 worker/Core RESUME。AgentSession checkpoint 也不要求每次恢复创建 newRun。依 Root 本轮明确的权威约束，CANCEL 后新 turn 必须明确 newRun；PAUSE 可 sameRun 增 epoch。不要从 fixture 推导出所有恢复必须 newRun，也不要据此宣称 M1/M2 已实现。

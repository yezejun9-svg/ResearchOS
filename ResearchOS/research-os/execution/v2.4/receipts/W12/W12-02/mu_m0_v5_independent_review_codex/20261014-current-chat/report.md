# Mu M0 V5 独立复核 — FINAL / REQUEST_CHANGES

V5 不予独立接受。冻结候选存在 **2 项 P1、1 项 P2**，需要 V6 修复后重新冻结并独立复核。当前材料足以启动限定范围修复；未修改候选源、Root Canon、安装 SDK 或正式状态。

冻结 manifest SHA-256：`41ac355e5a71b3092748c0c1061cb7cfd7c562b3cc158b89154f1a9f7e22c127`。候选基线 `7ec619a16a932ae02daa7c2e6132d266528a1da8`；9 个源文件、作者 2129 个实际编译输入、10 个冻结 bundle、Root 镜像、作者 raw/harness，以及独立编译的 2134 个输入均核验一致。恢复本次工作时读取既有 12 个完整进程退出记录，stdout/stderr hash 全部吻合；未重新执行或覆盖历史结果。细项见 [resume-evidence-audit.json](resume-evidence-audit.json)。

## 阻断项

### V5-J — P1 — 数组 discriminant 绕过内容联合类型及字段白名单

user、assistant、toolResult 的 content.type=["text"] 均被 restore 接收；unregisteredPayload 随后仍可 export。

根因：String(content.type) 通过 kinds 检查，但 switch(content.type) 不匹配字符串分支且没有拒绝 default，完整字段验证被跳过。

源位置：`packages/agent/src/agent.ts:278-307`。

复现：复制合法 idle checkpoint；给三类 message.content 插入 {type:["text"],unregisteredPayload:{marker:"synthetic-private-data"}}；restorePauseState 后 exportPauseState。三个 rejected 均 false，unknownRetained 均 true。

修复边界：discriminant 先验证 string，再严格匹配 literal；default 拒绝；所有 typed content 路径复用校验。复查其他枚举的隐式转换，保留正常 text/image/thinking/toolCall 控制。

证据：[v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.stdout.txt](v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.stdout.txt)、[v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.command.json](v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.command.json)。

### V5-K — P1 — 闭合 custom schema 把继承键当作已登记字段

普通 unregistered 字段拒绝；constructor、__proto__、toString 三个未声明 own 字段接收，携带的合成 JSON 数据仍可重新导出。合法 custom 数据控制通过。

根因：key in schema.properties 把 Object.prototype 继承名视作声明；后续仅遍历 schema 的 own entries，未校验这些 payload 字段。optional/必填查询也使用 in。

源位置：`packages/agent/src/agent.ts:423-435`；`packages/agent/src/agent.ts:372-375`。

复现：登记只含 role/value/timestamp 的 object schema；在合法 payload 上分别定义 enumerable own constructor/__proto__/toString，值为合成 JSON 对象；restore 后检查 export 对象 own property。

修复边界：声明查询、optional 校验及必填数据查询采用 own-property 语义；显式声明的同名合法字段仍按 schema 验证。未证明原型污染或代码执行，不扩大结论。

证据：[v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.stdout.txt](v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.stdout.txt)、[v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.command.json](v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.command.json)。

### V5-L — P2 — 旧恢复绑定跨阶段存活，阻断可信回调选择后续登记模型或工具

无暂停控制均完成 2 次模型调用；恢复仅调用 1 次并报 Restored model binding changed before dispatch 或 Restored tool subset changed before dispatch。合法 next_tool 无法执行。

根因：verifyRestoredDispatch 闭包永久捕获旧 modelBinding/toolNames/signature；可信 prepareNextTurn 更新 config/context 后没有提交下一阶段绑定。

源位置：`packages/agent/src/agent.ts:1674-1698`；`packages/agent/src/agent.ts:1705-1721`；`packages/agent/src/agent-loop.ts:435-451`。

复现：第一响应进行中请求暂停并恢复；finishTurn 继续，原有 prepareNextTurn 返回已登记 next model 或只含已登记 next_tool 的 context；比较未暂停控制。

修复边界：恢复旧 prepared/request/response/tools/pendingFinish/finish 阶段必须保留 checkpoint binding；仅在其完成后，通过可信 prepareNextTurn/prepareRequest 建立新阶段绑定。登记身份必须独立于可变模型/工具实现；每次 dispatch 继续检查；不可简单清除 guard 或把 mutation 重新签名为可信。

补充证据：strengthened-N5: effects=[one,two] 但 calls=1 并有工具子集绑定错误；V4 原记录 calls=2 且无 error。旧 N5 断言仅检查效果，不能证明完整恢复。

证据：[v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.stdout.txt](v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.stdout.txt)、[v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.command.json](v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session.command.json)、[strengthened-n5.stdout.txt](strengthened-n5.stdout.txt)、[strengthened-n5.command.json](strengthened-n5.command.json)、[v4-n5-control-reference.json](v4-n5-control-reference.json)。

## 测试结果及历史保留

| 记录 | 结果 | exit | 解释 |
|---|---:|---:|---|
| 原样重放 original-replays | 47/50 PASS，3 FAIL | 1 | 三个旧 fixture 缺 typed custom schema 注册；原始失败保留 |
| registered + J–N | 12/16 PASS，4 FAIL | 1 | 登记适配 10 PASS；J/K/L-model/L-tools FAIL；M/N PASS |
| strengthened-N5 | 0/1 PASS，1 FAIL | 1 | 工具效果成功但最终回复未到达；归入 V5-L |
| Agent 原有回归 | 40/40 PASS | 0 | 独立重放记录 |
| 合成 worker 协议 | 2/2 PASS | 0 | 仅 M0 合成协议 |
| targeted tsgo | PASS | 0 | 不代替运行验收 |

作者冻结 51+40+2 的通过记录已核验来源，不能消除本轮反例。以上运行有重复用例，不相加为新的接受总数。三份 registered fixture 仅增加既有数据的明确 schema 注册，diff 已复核；详见 [fixture-adaptations.md](fixture-adaptations.md)。旧 N5 和 session 的通过断言只要求效果完成，其 raw 已出现 binding error/calls=1。增强 N5 添加最终调用数和无错误检查后真实失败；V4 同一流程 raw 为 calls=2、无 error，引用及 hash 见 [v4-n5-control-reference.json](v4-n5-control-reference.json)。

## V6 修复及复核边界

必须保留已恢复旧阶段的 model/config/context/tool-subset 绑定及每次实际 dispatch 校验；原 prepared/response/pendingFinish/finish 的 callback 和已提交效果不得重放。仅在旧阶段完成并经过原可信准备回调后，提交新的阶段绑定。禁止通过清空 guard、扩大为全部 registry tools，或对已经变异的实现对象重新计算 signature 来绕过安全检查。

V6 回归至少保留 J/K 矩阵、L 两种合法切换的无暂停控制、M 四个异步 mutation 拒绝、N 排除额外工具，以及 N5 的最终回复/调用数/无错误/消息恰好消费一次。具体契约见 [state-contract-v5-addendum.md](state-contract-v5-addendum.md)。本报告只支持 Root 启动当前授权范围内的 V6 修复，不扩大 same9 写入范围。

复现使用现有 node 和 `node --test --test-reporter=tap v5-boundary.mjs`、`node --test --test-reporter=tap strengthened-n5.mjs`；完整既有命令与退出记录在 audit/各 command.json。本次 FINAL 只收口，不重跑。

本轮没有真实 provider 调用、真实外部工具效果或真实凭据。M0 未独立接受，M1/M2、真实 worker/Core RESUME、手机流程、生产安装均不能由本轮推导。正式增量 0，保持 0/42，22 个父任务全部 open。CANCEL 后新 turn 须 newRun；PAUSE 可 sameRun 增 epoch；不擅自把所有恢复规定为 newRun。

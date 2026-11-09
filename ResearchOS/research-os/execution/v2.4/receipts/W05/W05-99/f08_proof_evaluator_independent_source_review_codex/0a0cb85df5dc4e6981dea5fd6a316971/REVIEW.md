## Review Summary

**Verdict: REQUEST CHANGES**

本次仅审查冻结的候选文本 b50de13c860fa05ec402db413d71c3804601293a57d3096a3a2c135feaf39dd3（105488 bytes，1467 行、86 个函数）。117 个 manifest 成员及 manifest 本身、handoff 15 个内部引用均逐 SHA256/size 核对并复制到独立只读快照。候选尚有一个可定位的 NO_SESSION 空队列绕过；其它真实未实现支路仍保留拒绝。这个结论不批准三个 callback 完成、SQL24 安装、Source acceptance 或正式用例接受。

### Critical Issues

- **C01 — NO_SESSION 直接返回空队列证据，忽略该 Task 的真实 queue / 可关联 receipt。** [queueAdmission](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs/client_cancel_finalization.go.proposed.txt:812) 在 816 行仅确认没有该 Task 的 Session/fence，然后返回 NO_SESSION；[emptyQueueFinal](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs/client_cancel_finalization.go.proposed.txt:1195) 在 1198–1199 行仅比较这个空 binding，随后把 entry_refs / receipt_refs 填成空数组（1215 行）。与之相对，真实 Session 支路在 1207 行显式拒绝非空 queue/receipts。admitted(mode0) 和 finalGroup(mode1、以及 mode5/6 的终结调用) 因此不能证明这个 NO_SESSION Task 的队列为空。

  静态反例：同 project 中 Task A 无 Session/fence、无 Run；Task B 有真实 Session/fence generation G。插入一条 task_id=A、session_id=B 的 Session、generation=G、state=SENDING（或 SDK_ACCEPTED/UNKNOWN）的 queue 行。SQL22 唯一 FK 是 generation -> fences.generation；该行有合法存在的 G，且没有 Task/Session/Goal 组合 FK。[SQL22](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs/snapshots/038-0022_client_command_queue.sql:10) 的 10–18 行允许其存在。候选 SQL24 的 464 行只防 key collision，未校验这个组合。A 的 queueAdmission 仍得到 NO_SESSION；finalGroup 的 noRun 检查只看 Run/dispatch/effects；f08Pending 按控制 Session 筛选，可看不到 B Session 上的这条 queue。由此 emptyQueueFinal 仍返回空 entry_refs/receipt_refs，最终可声称 queue_empty=true。这里是源码逐分支推导，**没有运行 Go/SQL 或构造数据库作为已验证结果**。

  独立 receipt 反例同属此缺口：SQL22 28–32 行的 receipt 表没有 generation/command FK。一条 kind=CANCEL_FENCE、body={task_id:A,from:SENDING,to:DROP_REQUESTED}、正确 R(raw body)、但指向不存在/错误 generation 的 receipt 不会被 NO_SESSION 分支读取。真实 [fenceClientTask](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs/snapshots/013-client_protocol_queue_control.go:46) 在 51–54 行遇到无 Session 直接返回；[enqueueClientMessage](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs/snapshots/012-client_command_queue.go:67) 在 67–101 行始终从真实 Session/Task fence 取得 G；[appendClientReceipt](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs/snapshots/012-client_command_queue.go:164) 保留原 raw body 与 Digest。这些正常 producer 事实不能把已有矛盾行变成“空”。

  **必须修复：** 在 queueAdmission 和 emptyQueueFinal 共用一个纯 source graph/absence helper，先枚举该 project/Task 的所有 queue 行；NO_SESSION / 空队列子集必须拒绝任何相关原队列历史，不能仅检查 pending 状态。按实际 generation + Session + project + Task + command 查验 fence/queue/receipt 归属；strict-decode receipt raw body 并重新计算 R，校验 CANCEL_FENCE.task_id 与该 fence/entry，拒绝孤立、跨 Task、错误 generation 或不明关联的相关 receipt。仍允许其它 Task 的有效独立队列历史，不应把整 project 有 receipt 当成 A 有执行。这个小包只关闭 absent/empty graph 矛盾，非空 SDK chain 仍返回 f08NativeProofGap，不增加“无 Session 即 SDK 空”的捷径。

### Important Issues

- **I01 — initial qualification 的成功仍包含未实现的 profile 验证。** [bootstrapAdmission](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs/client_cancel_finalization.go.proposed.txt:1056) 对 sealed raw bytes、Artifact content hash、runtime/profile technical labels、plan/marker/context、expires_at 来源做了具体检查；但 1083 行能返回成功，而未复现冻结 [validateRuntimeDispatchProfile](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs/snapshots/008-runtime_dispatch.go:12) 的 sandbox/command/build、permissions network/environment/process/memory、bounded timeout、local unique outputs 等纯谓词。plan 注册的冻结 profile/model/capability checks 也未完整覆盖。由于 mode2/8 可以成功，这个缺口不能因“普通 admission OPEN”而被归入全部拒绝的支路。当前 IMPLEMENTATION-STATUS 第1项已诚实承认此事。**建议修复：** 在未来任何 authoritative origin integration 前，补出并复核纯 profile/model predicate 与其精确 source 输入；或使 initial bootstrap origin 在这些谓词未完成时返回固定 gap error。不得读 Host/DB/clock 补权，不得把当前 Go producer 的角色/expiry gate删掉；本次没有授权该实现。

- **I02 — 8 top / 33 leaf 只验证部件，缺少已声明成功子集的完整正向控制。** 新测试覆盖 storage/key、多重 relation wire 保留、UNKNOWN 原列保留、legacy control recovery、pending union、identity、effect prefix、mode4 action 和 structural materialization。它们没有用完整 frozen entity/version/ref/identity/control/Session/source bundle 走 mode0 -> mode1 -> mode5（即时完成与 ACK->COMPLETED）。R1 两行相等的 domain_refs wire 保留不等于 referenceClosure 的 schema-derived occurrence matching 已验证。**必须修复：** 先加 next-function-group.json 的 NOT_RUN 真实 schema 正向/负向提案，再由 Root 单独授予编译/组件执行；任何纯 fake parent 的 structural success 不得计入 admission authority acceptance。

### Suggestions

- 这些新增长行函数可在未来拥有源码/gofmt 授权后整理成可读的 source stages；本次未执行 gofmt。首要调整是 C01 和成功支路的实际合同边界。

### What's Done Well

- 固定 34 categories 的 mask/width/key 集合与 frozen generated registry 逐项一致，原 SQL view 317–350 的 positional expressions 保留；domain_refs 仍是无 key multiset，NULL SQLite unique key 保留而非伪 dedup。referenceClosure 根据 store.refs/relationKind 消耗每个 occurrence，校验显式 revision/nullable hash、隐式实际历史目标、重复 ID 的一致目标，区分 refs bag 与 pin set。
- Q 使用 original Envelope.ContentHash；R 读取 actual raw hex decoded bytes；J 使用 strict canonical.JSON。header 原排序/原 base64 字节比较、raw old/new response digest、control bytes 和 sole-journal closure 都有具体代码，不以两个自报 hash 相等替代全部验证。
- 未加入 response 1MiB cap；已保留合法 >1MiB 标题 fixture 的局部 response proposal。正式的 sole-journal 完成/byte-exact replay 仍未执行。
- mode3 固定 F08_CALLER_CONTRACT_UNBOUND；mode0 的非 NO_RUN、mode1 native/非空/history、mode2 ordinary/later、mode8 late operation/完整 prior closure 都有错误返回。laterParts 后仍返回 f08NativeProofGap；currentRuntimeAdmission 单字段 operation patch 明确 NOT_APPLIED，并未让其它 OPEN 变成成功。
- mode4 保留 actual OLD equality、不可逆 identity/state、UNKNOWN 不回退；OBSERVED 的真正 observation tuple / artifact / commit obligation 仍需要 SQL 实物验证。mode7 child/index/task/hash 和 pin actual version 的定位验证保留为 structural boundary。

### Verification Story

- **Tests reviewed: yes, text only.** preserved prior12 + new8 top / 33 named leaves均 NOT_COMPILED / NOT_RUN，actual executions=0。
- **Build verified: no.** 没有 Go parser/compiler/gofmt/nativeGo；当前 pinned modernc 无 Innocuous 字段，候选本身已标注不能直接编译。driver fork/pin、package initialization/all physical connection installation、trusted_schema OFF、真实 SQL callbacks 与 upgrade/backup 全部待独立授权与实物验证。
- **Security checked: partial static source check.** 所有新增函数未见 DB/Host/FS/env/network/随机/clock-now 调用；time.Parse/Add 只处理 retained source literals。原固定 domain hash/schema/decoder helpers已读取其冻结快照。canonical.JSON / jsonschema 库的继承14项仅是历史 ref metadata；本包没有这14项实际库源码快照，无法据此宣称完整 linked transitive purity 已证明。FunctionContext 与 caller args 不被 retained；panic 是固定非秘密错误。候选只读文本中的纯性不等于 physical SQL 采用可批准。
- 原旧6ed partial、4个作者 metadata origin、9项 registry labels erratum 均保留；继承 dependency callgraph 的 locator 仍是旧 source，不作为本次86函数的现行 callgraph。8行 late first-read provenance 保持原时间限制，未升级为 pre-read hash evidence。
- 本 reviewer 新 metadata 失败 **eade2d actual outer=1** 单独保留；native exit无显式 bridge故 NULL。新显式 shape 分支50b1b4 actual outer=0。旧失败命令未重跑，失败计数未重置，Root已确认 later_pending。另 e3a46d 的错误 key mismatch 展示是 exit0 读取器 regex artifact，90eead complete-line 提取已解释为无产品缺陷，不计伪运行失败。
- Main/WT/cache/canonical/helper/nativeGo/SQL/模型/HTTP 0 mutation/call；仅本独立 UUID namespace 的证据文件写入。读取作者已封冻结包，最终 before/after 再核所有117成员的原 hash。**STOPPED 后等待 Root / 作者修订，不自签接受。**


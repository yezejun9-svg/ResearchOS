## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** 原 C01 的 Task A queue/receipt 被 generation-only FK 或 NO_SESSION 分支隐藏的问题，已在两个入口加上保留历史的检查。C02 的初始资格证明成功出口已改成明确 OPEN；但 C01 对“无关 Task 的合法 CANCEL_FENCE 历史”的例外仍未闭合，不能批准采用本候选。

输入是 writer STOPPED 的 b9a560ed59c24bef9b9e01d2d91c4b84 包。其 handoff 1828343f3ff153bf91907307ee7e95ecd4fb9f78b45b9946a31ce87882b10138 / 8486 bytes，manifest 0d7982363d2b77ea8ac5117dd014bb434e8d580b07d5c413ccb9f8433db4095f / 7773 bytes，25 listed members（含 manifest 物理26个）。全部 SHA/size 及 handoff 中实际外部 receipt refs 已复核。完整候选 9d7bbc20cf68e4a9aa46ecd6cd763b7f2a7bcf1b3063baf8e2863fd6e5f7314f / 109811 bytes / 1536 lines；逆差异还原 b50de13c860fa05ec402db413d71c3804601293a57d3096a3a2c135feaf39dd3 / 105488 bytes。未变化的字节保留上一独立审查结论，本次只重审 C01/C02，不把旧 OPEN 转成通过。

### Critical Issues

本次窄修订没有新增已确认的 Critical finding。原 C01 的关键拒绝路径仅在源码层面得到确认，尚未执行测试或产品。

### Important Issues

- **C01-R1 — 无关 CANCEL_FENCE 历史例外接受没有真实 producer locator / 当前 receipt 图的来源。** `inputs/client_cancel_finalization.go.proposed.txt:835`、`:846`、`:859`、`:864`：`noSessionQueueHistory` 只有 queue.last_receipt_id 非 NULL 才解析当前 receipt，也只有 previous_receipt_id 非 NULL 才调用 `f08String(r[0])`。当两个字段都是 NULL 时，相关 receipt_id 可以是 NULL 或空串，甚至两个重复 NULL ID 行仍沿全部检查到达 `return nil`。源 registry 的 receipts mask 为 `SssSshsSs`（428行），decoder 在 NULL unique key 时按 SQL22 语义跳过冲突（524–526行），所以这些行不能依靠输入 shape 层排除。

  静态反例以新 `queue-absence-tests.go.proposed.txt:52` 的 positive fixture 为起点：Task B/Goal B/Session B/fence B/queue B 一致，Task A 无 Session 或 fence；queue.last_receipt_id=NULL，唯一 CANCEL_FENCE 的 previous_receipt_id=NULL。其 raw body 为 B 的 ENQUEUED→DROPPED，body_hash 保持真实 R(raw)。仅将 receipt_id 改为 NULL 或空串，或者复制一条相同 NULL ID receipt，所有相关分支仍接受。两个入口分别在候选881行和1267行调用该 helper，因此 `queueAdmission` 返回 NO_SESSION，`emptyQueueFinal` 可返回空 entry_refs/receipt_refs。此处是静态控制流推导，未执行候选、Go 或 SQL。

  即使 receipt_id 非空，第52行正例也不能标为真实合法 producer 历史：保留了唯一 ENQUEUED→DROPPED CANCEL_FENCE receipt，却人为清空对应 DROPPED queue 当前 pointer。冻结 `producer-evidence/013-client_protocol_queue_control.go:96`、`:101`、`:104` 显示 producer 同 tx 创建 receipt 并更新 queue 的 state、revision、last_receipt_id；`producer-evidence/002-store.go:122` 的 ID() 输出32位非空 hex。SQL22 29行的 nullable TEXT PRIMARY KEY 保留了存储能力，不能据此赋予这些行“已知 producer 产生的合法历史”资格。当前 helper 只检查 body 中允许的 from/to 标签，没有证明保留 graph 与该 producer 的 linked receipt history 一致。

  **最小修复：** 在相关 receipt 被归类为可豁免的已知 CANCEL_FENCE 之前，无条件验证非空合法 `receipt_id`；保留通用 registry 对旧 nullable SQL22 的真实表示，不能用全局 dedup 或擅自收紧 SQL 掩盖问题。校验该 receipt 可从对应 queue 的当前非空 receipt locator 经同 project/generation/command 的完整保留链到达，并核对已知 producer 的 queue 状态关系。若合法后继属于尚未实现的 SDK/stream producer，继续明确 OPEN，不能仅凭 kind/body 标签豁免，也不能把当前 queue state 无条件等同每条历史 receipt.to。不能从 NULL current pointer 推断已经有合法已知 receipt 历史。

  **最小测试：** 保留 Task B 的真实 producer 一致正例及真实空 source 正例；两入口分别拒绝 NULL receipt_id、空 receipt_id、两个 NULL ID、CANCEL_FENCE 保留但 queue current pointer=NULL、终态 DROPPED receipt 与 queue 状态不一致。如要保留“历史 receipt 不是当前 pointer”的正例，必须构造冻结已实现 producer 的真实后继链；未知 SDK 后继继续 OPEN。现第52行需改为拒绝例或在明确的 graph-only metadata 测试中撤去“合法 producer 正例”的声明。上述新回归均仍应标 NOT_RUN，直到 Root 授权实际 source/test 施工与执行。

### Suggestions

没有为本次窄修订增加命名或格式建议。修复应限于 `noSessionQueueHistory` 与其 component fixture/状态说明；不扩大 SQL24、SDK 或完整资格 profile scope。

### What's Done Well

- 两个 NO_SESSION 入口共享同一 helper；Task A 的所有7种 queue 状态（含 DROPPED、CONSUMED、UNKNOWN）都不会因 generation 指向 B 而消失。目标 receipt-only、raw hash 不匹配、generation/command/project/session/goal 关系、cycle 与缺失 predecessor 均有具体 NOT_RUN fixture。
- helper 用原 fence 的 Task/Session 关联保留历史，未把 Session 的当前 task_id 强行当历史 owner。相关项目判断同时观察 row.project 和被引用 fence.project；不能单改 project 标签绕过检查。
- C02 在1151行明确返回 `F08_INITIAL_QUALIFICATION_PROFILE_PROOF_INCOMPLETE`。1167行原有 error 传播使 subset extraction 无法进入 initial authority 构造；不再把缺失 sandbox/build/permissions/timeout/output/model qualification 谓词称为成功。mode2 originInsert 和 mode8 initial derivation 随之保持拒绝；这只是固定拒绝通过静态复核，完整 profile 实现仍 OPEN。
- 未知 SDK receipt 仍返回明确 native-proof gap，coverage/status 对 I02 完整 journal/response/materialization fixture 的缺口仍诚实，没有将 component 正例包装成完整 evaluator 成功。

### Verification Story

- Tests reviewed: **yes, static only**。完整候选测试文件的旧22668字节前缀相同，新1 top/24 leaf fixture 全部读过，均 NOT_RUN。Task/Goal fixture 试图使用完整冻结 schema，tuple shapes 与 intended mutations 已读；未调用其 validator，也没有声称 schema 验证实际通过。
- Build verified: **no**。没有 Go、gofmt、AST/编译、SQL、UDF、Node、SDK、HTTP、模型调用；没有 source adoption、Main/cache/canonical 写入。新增 helper 本身没有 DB/Host/Clock/环境读取；不升级此前14个 library metadata 输入或8行 late-firstread 的 provenance 为完整 transitive purity 证明。
- Security checked: **static input/proof binding review only**。R(raw) 与 JSON shape 校验没有补足当前 locator/producer gap。完整 R1、mode3 caller binding、later admission.operation producer 保存、普通 native SDK final authority/history 都维持旧 OPEN。本次没有重新认证34源 tuples、SQL24或三个 callback。
- I02: **OPEN_NOT_IMPLEMENTED_NOT_RUN**。完整 mode0 admission → mode7 materialization → mode1 final/control → mode5 sole journal ACK→COMPLETED 的正向 source fixture仍不存在。本报告绝不授予 I02 PASS、Source acceptance、SQL24 adoption 或正式用例增量。
- Origins: 新 author metadata origins 为 5b7ca2、a1e3bf、3d077c、86f70b 四个，全部原件保留；5b7ca2 的 native exit 没有明确 bridge，仍 NULL，其余按作者原始明确 Python bridge 保留。旧作者四 origin、registry erratum、上次 reviewer eade2d 只保留已冻结 refs，不重复计数。当前 review 的已观察工具 outer exit 全为0，无 failure/canonical 计数写入。

独立 reviewer 非作者。后续由 Root 选择上述最小函数修复；本 receipt 没有批准实施、合入、采用或增量。writer 在封包后 STOPPED。


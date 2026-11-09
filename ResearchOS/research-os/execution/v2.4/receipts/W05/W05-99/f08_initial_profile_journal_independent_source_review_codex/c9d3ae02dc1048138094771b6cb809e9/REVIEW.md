## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** 完整 v2 source/test 包可以继续用于受控修订，但 C01 的 unrelated ENQUEUED fence 生产图仍存在放行缺口。GLOBAL 映射、captured profile 组件和 I02 完整 fixture 已写到源码；这些结论仅来自固定源码审查，49 新场景及 24 受影响场景全部 NOT_RUN。

### Critical Issues
- 本轮未确认新的 Critical issue；所有正式采用、SQL24、native/ordinary/history 和 initial authority 仍未开放。

### Important Issues
- **C01-R2 — D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_initial_profile_journal_revision_preparation_codex/bd3fe19a27f54a468431828f267cd02f/client_cancel_finalization.v2.go.proposed.txt:859，noSessionQueueHistory。** ENQUEUED 分支只检查 queue revision1、NULL current pointer 和没有 receipt，忽略关联 fence 的 state、sealed_through、restore_fenced 和 revision。以本包 known_enqueued_without_receipt 的完整图为基础，仅把 fence.state 改成 CANCEL_FENCED，其他 raw/hash/Task/Goal/Session/generation 不变，两处 NO_SESSION 入口仍沿相同成功路径。这是源码条件推导，未执行候选代码。固定 012-client_command_queue.go:73/76 仅允许 OPEN 且 restore=0 入队；013-client_protocol_queue_control.go:66/93/101/104 在同一事务把 fence 设为 CANCEL_FENCED，并把 ENQUEUED 变成 DROPPED、追加真实 receipt、更新 current pointer。因此该图不能作为已证明合法的无 receipt ENQUEUED 历史。SEALED 或 sealed_through 覆盖本序号也没有被当前分支拒绝。
  
  最小修复：仅收紧已实现的两类 pre-SDK unrelated-history。ENQUEUED 核原 fence OPEN、restore_fenced=0、0<=sealed_through<queue_sequence<=accepted_through，以及固定 birth/enqueue 的 fence revision 下界。DROPPED 的已声明 CANCEL_FENCE 子集也要保留真实 cancel fence revision 增量。未实现的 sealing/restore/SDK history 保持 typed OPEN。使用现有 tuple 字段即可，不增新 witness 字段、SQL schema 或其他 authority 范围。
  
  同时修正“known” 正例：共享 fixture 在 test:362 设置 DROPPED fence accepted1/revision2；known ENQUEUED 分支把 fence revision 设置1。ensureClientQueue 初生revision1，第1次 enqueue UPDATE 再加1，cancel fence 又加1。因此这两种声明的 producer 图应至少分别 revision2、revision3。修正正例后再加单事实反例，避免坏基础图把新反例全部遮盖。两个入口都必须检验：queueAdmission 和 emptyQueueFinal。完整最小 mutation 列表见 minimum-fix-proposal.json；全部 NOT_RUN。

### Suggestions
- 当前 DROPPED 子集还要求 sealed_through>=queue_sequence；固定 fenceClientTask 不更新 sealed_through，后续 finalizeClientCancel:267 才更新。合法未完成的 pre-SDK cancel history 仍被拒绝，应在 coverage 明确列为未实现的受限 history；不要把整个 pre-SDK producer 图称为闭合。
- noSessionQueueHistory 的多个 tuple index 可在下一独立维护范围定义局部命名常量；本次修复只需现有字段条件与对应 fixture。
- 保留先前要求的实际合法 >1MiB snapshot sole-journal 完成与回放检查。当前四条 I02 fixture 未覆盖该大小，属于未来验证缺口；源码没有新 response cap，只保留现有 raw-envelope/header 上限。

### What's Done Well
- Receipt locator 在任何 NULL/pointer/kind 分类前统一检查非空和唯一；CANCEL_FENCE 的 raw body/hash、current receipt、from/to 和 queue revision 被绑定，未知 SDK successor 没有获得例外。
- GLOBAL 空串映射放在完整 frozen entity schema 验证之后，仅限 BudgetPolicy/RunPolicy 的 GLOBAL/null project/global scope/null parent，与固定 Service.put/refs storage 行为吻合。
- 新 profile 组件没有把字段标签当授权。initial bootstrap 最后仍固定返回 f08QualificationProfileGap；auth_principals/auth_grants、authorRoot/OWNER/executor grant 和有效时钟事实继续 OPEN。
- v2 在 url.Parse 前拒绝 bracket/multiple-colon authority，避开固定 Go1.27.1 URL source:599 的 netip 路径和 :621 的 GODEBUG Value/IncNonDefault。普通 host/单 port 的检查只走该冻结字符串解析分支。Windows reserved device suffix 在 RtlIsDosDeviceName_U 之前返回 typed OPEN，没有执行 OS API。
- I02 fixture 逐个调用模式构造 admission、完整 materialization、control、Task/Goal 版本、TASK_CHANGED/outbox、final group、CONFIRMED、sole original journal 和 commit。四条 TEXT/BLOB 与 ACK/original 路径都有完整 raw header、原始 ACK/COMPLETED 字节；期望 R1 图由明确 domain_refs 边构造，没有调用被测 referenceClosure 来生成答案。

### Verification Story
- Tests reviewed: **yes, source only**。完整 final test 563 行已读；49 新 scenario / 24 受影响 scenario 仍 NOT_RUN。I02 四条 positive 和七条 mutation 是完整提议，未宣称任何运行成功。
- Build verified: **no**。没有运行 Go、Go AST、gofmt、compile、SQL、SDK、Node、HTTP 或模型。
- Security checked: **static only**。所有新 helper 和实际调用已审；未发现该修订新增 DB/Host/Clock 调用。动态纯度、整个 Go transitive closure 和 driver 采用仍未验证，不能声称 three callbacks complete。
- Fixed bytes: author 36成员+manifest37 全部 SHA/bytes 核验；source/test actual supplied patches 分别6/3 hunks，正向重建 final 与逆退 b9 都字节相同。final source 7dc5f0f3d4ff76893e1393d3cc64a70e86b35f20ec5456f800f42af60d4d0964/116817；test deb066b3d583db7aeef1810fe80e6b55a0fcf187cc716282889822b04e6e6890/58252。
- Public vector: before 实际160、final161，公共160项无漂移；新增 net/url 与 frozen receipt snapshot 同 SHA/bytes。156 个公开 receipt ref 已重哈希；5 个 Main/stdlib 原件没有读取。这不证明新的原始 first-read 或不断变化 Main 身份。
- 原 b9/旧独审、7b6137 development、6ed partial、旧四 metadata origins、eade2d、registry erratum、历史14输入与late-first-read8行 provenance 保留，未升级或重计。
- 本 reviewer 有且仅有新 metadata failure **4ddd35**：原 verify_inputs.py:45 错把 before/final 断言为两边161。原命令明确 exit $LASTEXITCODE，实际 outer1/Python1；原脚本和 trace 完整封存，不修改、不重跑。独立 shape reader e4e09a 与不同固定输入报告58c065 均 outer/Python0；不是重跑失败输入。Root 下一追加计数负责该单 origin，当前固定 cut 不修改。
- 作者0B accidental file/cleanup 的原工具输出封存；原 NULL numeric exits 继续 NULL，未假造1、未增作者新 nonzero、未重计旧失败。
- 仅写本独立 UUID review namespace；Main/module/cache/canonical/作者包/旧包/计数写入0。Root sole canonical。SQL24/source/formal acceptance **false**。

### Next Minimum Scope
修订 noSessionQueueHistory 与其真实 producer 正例/两入口单事实反例，重新冻结完整 source/test 后独立复核。其他模式的缺口按原 OPEN 保留；Root 再决定受控 driver/current compiled closure 与分项执行范围。I02 presence 不能替代 native/ordinary/history、authentic caller source capture、迁移备份回滚或SQL24真实同事务验证。

**Writer status:** STOPPED.


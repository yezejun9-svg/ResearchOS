# W05 工具和费用事件：只读最小接入审查

审查者 `codex:/root/w1702_review`。读取主库 HEAD `135b0de35c16b11dc26cdbed1c02f611253df6e5`。本记录只提出第二批源码范围；不修改生产源码、施工状态或合同，不执行测试或 provider。

## 结论与建议范围

最小实现可只改 **2 个现有生产文件，加 1 个投影文件和 1 个专用测试文件**：

| 精确路径 | 必须接入的职责 |
| --- | --- |
| `internal/domain/runtime_broker_windows.go` | `brokerEffect` 中 STARTED 与开始事件同事务；`ingestEffectFact` 中已验证结果/实际费用与投影同事务，并修复 duplicate-receipt 分支的投影补齐。 |
| `internal/domain/runtime_sessions_windows.go` | 在现有投影/Scan 路径补扫 effect/ledger 历史，恢复遗漏 UNKNOWN/RESULT/USAGE，按原绑定投影；读取最新 session revision/epoch/watermark 后追加事件。 |
| 新 `internal/domain/runtime_session_events_windows.go` | 唯一的纯派生投影器：effect/ledger→typed events，稳定事件ID、原 session/run/tool 关联、可重复恢复、现有 Artifact 存储复用。 |
| 新 `internal/domain/runtime_session_events_windows_test.go` | 本文的顺序、故障、幂等、权限、结果语义和费用反例。 |

`runtime_tools_windows.go`、`runtime_effect_wire_windows.go`、`runtime_recovery_windows.go`、`durability.go`、`client_protocol_journal.go`、`runtime_model_windows.go`、worker 和 schema 可先只读复用。只在 implementation 证明上述统一入口无法覆盖时，申请对应精确路径的增量范围。不要把一个 begin/ingest 统一投影拆成各工具自己的事件状态机，也不要新建事实表或调度器。

若要扩大既有测试断言，可另登记现有测试文件；本提案不要求为了使用旧测试而修改旧测试。生产文件的 domain 字节变化会影响 W04 当前输入向量，由主 Agent 做正式回执漂移/再验证处置。

## 真实调用点与顺序

1. `runtime_broker_windows.go:148` 构造冻结 route/capability/payload；`:170`–`:183` 在同一事务 prepareEffectTx 写 intent 与预算 reservation。`:185`–`:193` 对 CONFIRMED/NOT_APPLIED 只返原 wire reply，对 STARTED/UNKNOWN 拒绝重新执行。
2. 同文件 `:215` 调 beginEffectTx；`:220` 提交；`:223` 是已提交的 `effect_started` 观察钩子；`:225` 才进入 brokerTool。最小可靠接入是 **beginEffectTx 成功后、同一个 tx.Commit 前** 调投影器写 TOOL_STARTED，事件/水位与 STARTED 一起提交。之后即使物理调用尚未返回，另一连接的 session.events 已可读事件。若事件写失败，事务回滚且不得调用 RunTool。
3. `runtime_tools_windows.go:105` 的 brokerTool 再查 authority；`:132`–`:144` 可能等待原工具一次性授权；`:148`–`:180` 建立并调用物理写前 Revalidate；`:182` 才 RunTool。故这里的 TOOL_STARTED 表示**宿主已开始这一逻辑工具调用/取得单次 dispatch fence**，不等于文件已经写入或子进程已经启动。授权等待或撤销可能使已开始的逻辑调用最终 NOT_APPLIED。界面/摘要要保留该含义，不能给 STARTED 编造 PID 或成功写入事实。
4. 同文件 `:182`–`:188` 将可证明未发生副作用的失败记为 NOT_APPLIED，其余不完整结果记 UNKNOWN；`:205`–`:214` 写不可变 effect fact 后调用 ingestEffectFact。`runtime_effect_wire_windows.go:50`–`:65` 的 NOT_APPLIED 也走同一 ingest。
5. `runtime_broker_windows.go:318`–`:384` 的 ingest 验证 dispatch manifest、epoch、request hash、reservation、receipt ID/内容hash 和 host evidence hash。投影只能放在这些验证之后。`:391`–`:400` 模型完整响应但费用未知的分支只写 effect，保留 reservation；`:402`–`:417` 其他已知费用写 BudgetLedgerEntry RECONCILE 和 effect。投影应在各分支最终 commit 前执行。
6. 现有 duplicate 分支 `:385`–`:386` 直接 return nil。因此新增投影后必须让**已入账但尚未投影的原 receipt** 仍可补事件/Artifact，并提交该投影事务；不能仅跳过所有事情，也不能再次 appendBudget 或执行 RunTool。已有事实+已有事件时应为无变化重放。
7. `runtime_recovery_windows.go:285`–`:312` 从原 `effect-*.json` 验 hash/范围后复用 ingest；`:322`–`:352` 对无可信 receipt 的残留 STARTED 只记 UNKNOWN。`runtime_tools_windows.go:106`–`:110` 用 ObserveEffect 写 UNKNOWN；其统一实现 `durability.go:226`–`:253` 只追加事实，不调工具。通过 session projector 补扫这些事实即可，无须为 UNKNOWN 新造执行路径。
8. `runtime_coordinator_windows.go:226` 每次 Scan 先调用 projectCurrentSessionRuns，实际工作在 `:327`–`:336` 的 worker goroutine，因此 Scan 可以在长工具运行期间投影。已有 `projectSessionRun` 调用还有 `:501`、`:742`、`:941`，恢复的 `runtime_recovery_windows.go:241`、`:279`。在该统一投影 seam 补扫能够覆盖常规完成、UNKNOWN、崩溃和恢复；不必改所有调用者。

## 绑定、排序与幂等

`durability.go:111` 的 intent 已含 project_id、goal_id、task_id、run_id、key、epoch、request_hash、reservation_id、context_bundle_id；payload 中有 capability 与工具 name/arguments。事件不能接受 worker 声称的 session 作为授权。

当前 session 绑定可复用 `runtime_sessions_windows.go:155`–`:182`：canonical Run→Task，限定 task_type=mu_turn，再查同 project/task 的真实 client_sessions。初次运行 `runtime_coordinator_windows.go:501` 已写 RUN_STATE 并绑定 run_id。必须拒绝一对多/错 project/错 task/run；不从任意“当前 session”补值。

恢复和迟到费用不能只查 `client_sessions.task_id`：它在下一轮被替换。先用原 Run 已存在的 durable RUN_STATE 事件确定唯一 session，再交叉核对 canonical Run.task_id、原 Task 与原事件。只用 Task.candidate_id（现为 session ID）还不足以证明此绑定。没有可证明关联时保留原 effect/账本并明确跳过无法归属的 UI 投影，不附到新一轮。若 session 已 sealed，不能绕过 AppendSessionEvent；费用事实仍必须完成 reconciliation，不因无法更新旧界面而丢失账务。

最小稳定ID建议（内部格式，无 schema 改动）：

- tool_call_id = namespace + hash(project_id, run_id, effect epoch, effect key)。它是**宿主工具调用ID**。
- TOOL_STARTED event_id = hash(session, run, effect key, `tool-started-v1`)：同一个 effect 只显示一次开始，包括 permission 状态仍为 STARTED 的后续 append。
- TOOL_RESULT event_id = hash(session, run, effect key, source effect sequence, result state/receipt hash, `tool-result-v1`)。UNKNOWN 后可信 CONFIRMED 是两条不同观察；重放同一观察只产生一条。
- USAGE event_id = hash(session, run, immutable BudgetLedgerEntry.id, `usage-v1`)。原 reservation 与后续真实 reconciliation 分别有事件，重复投影同一账本项不增加费用。

使用现有 outbox 唯一 event ID + tx 内查重；重复ID时先核对绑定/稳定 payload 一致，不得用 INSERT OR IGNORE 掩盖内容冲突。已有 `AppendSessionEvent`（client_protocol_journal.go:43）检查 schema、连续水位、当前 epoch/revision，`:96`–`:124` 保证事件与水位 CAS 原子。派生投影读取当前 session CAS；效果的历史 lease epoch 只用于来源证明，不可冒充新的执行租约。记录晚到事实不授予物理执行权。

补扫应按真实 `resource_effects.rowid` 的追加顺序派生（`runtime_model_verification.go:73`–`:92` 已用该事实证明 MODEL→TOOL→MODEL），不要按字符串 effect key 排出 tool:10 在 tool:2 前。STARTED 缺失时从原历史 STARTED 恢复，再投影 RESULT；不根据最终结果编造从未记录的开始。

当前 `worker.mjs:161`–`:162` 的 `makeTools` 丢弃 `_toolCallId`，effect 只传 name/arguments；没有受验证的 SDK tool-call/parent-tool 映射。上述 host tool_call_id 是合法新增投影身份，但 `parent_tool_call_id` 应为 null。不得把 ordinal 猜成 SDK ID 或伪造 nested parent；H08 完整嵌套执行需要单独真实身份链实现/资格。

## 结果与 Artifact 语义

| 原始事实 | 可输出 TOOL_RESULT | 不允许的解释 |
| --- | --- | --- |
| CONFIRMED 的 read/write/edit 完整可信结果 | SUCCEEDED，保留实际 path/hash/operation | 仅看到 effect state 就忽略结果内容 |
| CONFIRMED 的 run_check 且 details.exit_code != 0 或 timed_out=true | FAILED，引用真实 stdout/stderr | 把“调用完成并对账”说成测试通过 |
| HOST_PRE_EFFECT_REFUSAL、dispatched=false、NOT_APPLIED | BLOCKED，保留拒绝原因 | 声称执行成功或发生实际写入 |
| STARTED 后无完整可信结果、ObserveEffect UNKNOWN | UNKNOWN，保留原 reservation/恢复要求 | 因 CLI 退出/Run CANCELLED 就变成 tool CANCELLED |
| 有该工具原调用的可信取消、进程/队列/效果结清事实 | 才可 CANCELLED | 仅凭 Run.cancel_requested_at 或无PID推断已停 |

`internal/host/runtime_check_windows.go:558`–`:560` 已保留真实 exit_code、timed_out、PID/job、children_stopped/streams_drained/cleanup_complete、stdout/stderr hash 和完整 raw；`runtime_tools_windows.go:205` 的 CONFIRMED 不代表这些检查成功。

长输出不要塞进 summary 或截断冒充完整。ingest 收到的 `fact.host_tool_evidence` 已经过 `runtime_broker_windows.go:382` 的hash与界限检查，可以复用 `runtime_recovery_windows.go:97` 的 recoverArtifact，在原 dispatch attribution/input_refs/mode 下保存实际 LOG/TEST_RESULT/REPORT，然后把准确 Ref 放进既有 TOOL_RESULT.stdout_artifact_ref/stderr_artifact_ref/result_artifact_refs。相同 raw/kind/run/epoch 已有复用查找，不必新增上传协议。须核对序列化 byte[] 的 base64 解码和原 raw hash，不能把 base64文本当stdout字节。

注意现有 ingest 只把 receipt 留在 effect，host_tool_evidence 在不可变磁盘 fact 中。若恢复补投影需要完整 raw，应从同一 validated fact 的 ingest 重放补 Artifact，不能假设 effect.receipt 已保存完整 raw。早已commit的同receipt分支也必须允许这项补齐。没有 raw 时 stdout_artifact_ref=null并明确缺失，不能造空日志 Artifact。

## USAGE 与未知费用

现有 typed schema `client.protocol.schema.json:3175`–`:3262` 要求 ledger_entry_id，允许 provider_usage_id/input_tokens/output_tokens 为 null；**cost_known=false 强制 money=null**。

投影只读取真实 BudgetLedgerEntry：RESERVE/UPPER_BOUND 或 UNKNOWN 表示待定费用，事件 money=null、cost_known=false，原上界金额仍保存在 ledger_entry_id 引用的账本。模型 receipt.actual_cost=null（runtime_model_windows.go）不得生成RECONCILE或将预留释放。仅真实 ACTUAL COMMIT/RECONCILE 才 cost_known=true；RELEASE 不能冒充实际花费0。provider_usage_id 只有供应商真实用量标识才填，prepare/effect key 不是该标识。没有可信 token 数据时填null，不从 max_tokens 或 SDK零费率猜测。

TOOL 的已知本地零费用有现存根据：`runtime_broker_windows.go:85`–`:93` 强制 host-only TOOL 上界为显式0，`runtime_tools_windows.go:205` 与 ingest 因此可真实对账0；这不能推广到 MODEL。若需要token统计，可在独立有界解析的真实provider receipt usage中取数据，但不得改变费用账本；此最小投影允许token=null并公开尚未提供的范围。

会话转入下一轮后收到原 Run 的账单，USAGE 仍归原 Run/原 session，不作为新轮预算/成功证据。现有 projectCurrentSessionRuns 只枚举当前 task 的 run；为补齐外部账单API写入后的历史run用量，应在同一文件把有已证明 session 关联的历史 RUN_STATE.run_id 纳入有界分页补扫，不能只依赖当前 task join。ingest 内的即时投影不替代该补扫。无论投影失败、session sealed 或旧 writer epoch，原可信费用 reconciliation 不应丢失，也不能从投影触发执行。

## 可复用的现有测试（本次未运行）

- `runtime_sessions_windows_test.go`：TestW14SessionProjectionSettledTurnAndReplay、TestW14SessionProjectionFailureCancelAndUnknown、TestW14SessionProjectionRecoveryAfterReportCommit。
- `runtime_tool_integration_windows_test.go`：TestRuntimeMuSessionToolAndIndependentAcceptance、TestRuntimeMuToolRefusalAllowsNextTurn。
- `runtime_recovery_windows_test.go`：TestRuntimeCoordinatorEffectCrashRecovery、TestRuntimeCoordinatorCrashRecovery。
- `runtime_permission_windows_test.go`：TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite、TestRuntimeOriginalToolPermissionExpiresWithoutPhysicalWrite、TestRuntimePermissionDecisionWaitsForAnotherRequiredResource。
- `runtime_model_windows_test.go`：TestRuntimeMuUnknownNeverRetries、TestRuntimeMuTypedCancelStopsTransport、TestRuntimeMuMissingCredentialNotApplied。
- `runtime_effect_wire_windows_test.go`：TestRuntimeMuLargeSSECompressionAndReplay。
- `internal/host/runtime_check_windows_test.go`：TestRuntimeCheckReplyFitsFrameAndReportsOmission、TestRuntimeCheckEvidenceRefusesOversizeRawLogs。

## 必须新增的反例/正控

1. RunTool 在闩锁处等待时，另一个HTTP/DB连接能读到已提交 TOOL_STARTED；无 RESULT；放行后才出现真实 RESULT。验证事件追加失败则 begin 事务回滚、RunTool调用数0。
2. permission 等待/拒绝：仅一个逻辑 STARTED，未产生物理写；NOT_APPLIED→BLOCKED；不能在permission变化的每个STARTED历史行再发一次开始。
3. 同effect和同immutable fact重复ingest/recovery：一个物理调用、一个STARTED、一个相应结果、无重复账本/Artifact/水位。已commit receipt但事件缺失的情形可补投影。
4. 三处崩溃窗口：STARTED后/物理调用前、物理副作用后/fact落盘前、fact落盘后/DB ingest前。前两者无可信结果保持UNKNOWN且不重做工具；第三者从原fact恢复准确结果与输出。
5. run_check真实非零exit完整receipt→FAILED；副作用CONFIRMED不等于工具成功。因cancel导致无完整receipt→UNKNOWN，不能用Run取消标志编造tool CANCELLED。
6. UNKNOWN后可信晚到CONFIRMED：保留原UNKNOWN事件、新增真实结果事件一次，原effect/账本对账，不调用RunTool、不恢复旧lease。
7. wrong project/run/task/epoch/request hash/reservation/fact hash 拒绝投影；新一轮session绑定不得接收旧run结果，迟到费用按原关联显示。
8. 并发重复投影和writer handoff/CAS冲突：同事实只增一条事件，无水位洞、无重复物理执行；原effect epoch不充当新writer authority。sealed session不绕过拒绝，可信账务照常保存。
9. MODEL完整响应无真实费用：USAGE.cost_known=false/money=null，账本预留金额不变；SDK placeholder0不被结账。实际本地TOOL零费用与MODEL未知费用分别断言。
10. 输出超summary上限时真实LOG refs可读且hash匹配；非法/超界raw fact拒绝，不能造空日志。没有SDK parent事实时parent_tool_call_id=null，不冒称H08嵌套覆盖。

这批证据可证明宿主工具/账务事件投影的真实顺序和恢复，不自动证明provider token streaming、nested SDK parent链、完整TUI或 W05 LIVE 正式门。

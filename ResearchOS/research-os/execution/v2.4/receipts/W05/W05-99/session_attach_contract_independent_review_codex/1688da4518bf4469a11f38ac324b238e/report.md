## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** 该候选正确把有效同 owner 续租与已 settled 的真实转移分开，并使用真实快照、原事务与原幂等路径返回 `COMPLETED/AttachResult`。但新增续租捷径能够越过恢复后未完成的 writer 对账，因此本轮不接受 Source，也不能进入“已通过”的组合。

### Critical Issues

- 无新增已确认的 Critical 级结论。以下 Important 为本轮 Source 阻断项；没有执行 SQL/native，也不推断实际工具已启动或发生数据损失。

### Important Issues

- **恢复后的旧 Session 租约会被当作正常有效租约续期。** [client_protocol.go:1131](source-evidence/client_protocol.go#L1131)–1161 在 `sess.runID` 检查之前，仅凭同 client 和 `lease_expires_at > now` 就更新租约并返回 `COMPLETED/write_owner_acquired=true`，epoch 保持旧值。实际 `backupFence` 调用 `EnsureClientSessionFence` 写入 `(project,run)` 恢复 barrier（baseline-evidence/backup_recovery.go:240），随后只把 Run 的 lease 设为 1970 并改成 RECONCILING（257）；Session lease 没有被作废。`fenceRestoredClientQueues` 只保留队列恢复标记及 `resume_requires_explicit_user`，也不清 Session lease。现有 `client_session_require_fresh` 只在 `UPDATE OF writer_epoch` 且 epoch 增长时检查 fresh observation（baseline-evidence/client_session_fence.go:63–73），所以租约单字段 UPDATE 不触发它；原来后置的 `runState`/`HandoffEpoch` 也被 early return 跳过。

  具体反例：恢复了一份 Session lease 仍在未来的快照，原 client 重新通过本机鉴别，拿当前 revision 发送新 attach(true)，Run 尚 RECONCILING，且没有比恢复 barrier 更新的真实停止观察。候选源码会续租并给旧 epoch 返回 acquired；T6 原路径会因 unsettled 拒绝，或在 epoch 转移处受 restore trigger 阻断。这与 22_CLIENT_INTERFACE_DETAILS.md:145 的“先对账，再递增 epoch”要求冲突。

  **修复建议：** 正常同 owner 活跃运行仍允许续租，但 fast path 必须先确认当前 writer generation 没有未解决的 restore/reconciliation fence。恢复后的旧 claim 不能仅凭未来到期时间被认定有效；必须通过原恢复／重新授予流程建立有效新 generation，不能清空 barrier、队列、取消状态或显式恢复标志来制造成功。停止证据必须绑定同 project、同 Run 及适用的当前 Run lease epoch，`observed_at` 严格晚于该 project/Run 最新 `restored_at`，并同时满足 `children_stopped=true` 与 `queue_empty=true`。继续保留真实队列／control 恢复 fence。

  **必要回归：** 保留普通 active owner 的正例；新增“still-future Session lease + restored Run + 无 fresh observation”的反例，检查不会延长 lease、改变 owner/epoch/revision/watermark 或返回 acquired。旧 observation、错误 project/Run/epoch、仅停止 children、仅清空 queue 均不能解除此门；正确证据必须走实际恢复与新 generation 路径，重放不重复操作。见 restore-counterexample.json 的完整静态路径；本轮未执行该反例。

### Suggestions

- 新增测试尚未覆盖续租/转移写入后 `BuildSessionSnapshot` 或响应 schema 失败的事务回滚。现有 Execute 对非 nil error 要求调用者回滚、对 REJECTED 使用 savepoint，源码路径正确；后续可用有意义的错误注入确认 owner/lease/epoch/event/idempotency 都不留下部分成功。
- 原 `TestClientSameWriterRenewsExpiredLease` 在 baseline-evidence/client_protocol_control_windows_test.go:59 仍期待 ACKNOWLEDGED。作者已明确保留该旧断言；它是后续组合的已知测试冲突，必须在独立审查下调整为实际 COMPLETED/AttachResult，同时保留 epoch=2、有效 lease 与 stale revision 拒绝断言。不能忽略这个测试再宣称 broad suite 通过。

### What's Done Well

- 5 组顺序替换可逐字节逆推完整 T6 production 输入；整个 Execute、dispatch、session.control、journal 保持原字节，未添加 schema/migration 或外部依赖。
- lease CAS 同时约束 project/session/revision/epoch/client/旧 lease 和未 sealed/archived 状态。真实转移仍走 HandoffEpoch 与 CLIENT_HANDOFF；snapshot 与响应验证在同一事务；缓存旧 ACK 不会被改写成虚假 terminal。
- 对 transfer 的检查已加强为 children_stopped 与 queue_empty 同时成立，terminal status 本身不再替代停止证据；新增测试保留了 normal active same-owner renewal 与 terminal-but-unsettled 拒绝的区别。

### Verification Story

- Tests reviewed: yes，先读完整合同与 5 个新增测试，再核源码及它们复用的 stored-profile/runtime-route、Task/Session 负例。未运行测试。
- Build verified: no，按授权仅做静态 Source 审查，未运行 Go、gofmt、native、SQL、model 或私有资源。
- Security checked: yes，核对原鉴别、创建归属、CAS、错误优先级、旧命令 replay、真实 snapshot/schema、事务回滚与恢复 fence。未发现新秘密或网络调用；发现并阻断上述恢复权限回归。
- Integrity: HDF/MF 与 41 个记录引用全部核 hash/bytes；15 个直接输入固定，production 的 5 组替换正反向吻合。26 份相关源码、合同、Q4 报告已复制入独立证据目录。Main 与 CP358/OW/SS/CM 在本次审查期间未变化。
- Scope: active 异步接管及历史 cached ACK terminal reconciliation 仍 OPEN；本轮不把这些已声明未完成的全合同支路伪装为本候选已实现。也不接受 runtime 8 leaf/native/FULL/formal 通过。Root 必须在修复后的新 Source 独立通过后再进行 fresh build/actual。
- Diagnostic: 新增 mechanical 829 为读取不存在的 report.md，原脚本和完整 input/output 已保存。实际报告 CONTRACT-MAPPING.md 后续按已枚举名称读取；错误未重置，旧候选与 827 原封。封包首版脚本随后产生 Python SyntaxError 831，未生成任何封包输出；原脚本和 exact IO 已保存，独立 seal_revision 仅修正多余括号并补齐失败记账。

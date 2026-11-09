# Pre-dispatch launch causal ordering review

结论：当前受审 `RunAdmitted` 在成功提交 `STARTED + worker + journal_locator` 后才调用 `StartBridge`。因此，在同一完整数据库、同一 project/run/epoch、相同受审执行路径且记录未回退或旁路修改的前提下，仍为 `PREPARED` 且 worker/locator 为空，足以支持“尚未跨过这条路径的启动栅栏”。这不是无条件的全局“任何 worker 从未存在”证明，也不能用 observation_sequence=0 推导没有执行。

## 准确启动顺序

1. `internal/domain/runtime_coordinator_windows.go:437-484 dispatchGate` 在 BeginTx 后取得 resourceWriteLock；核验 scheduler、executor、current Run、未 terminal/cancel/reconciling/lost、Run lease、Task 当前 ownership、dispatch manifest/current admission 和 profile command binding。
2. `RunAdmitted:494-510` 在同一事务生成 inputs、projectSessionRun，并调用 stageRuntimeProgram。后者 `runtime_model_windows.go:19-45` 仅校验/读取 bundle 并填充 inputs，本体不创建 worker。
3. `RunAdmitted:512-524` 生成 worker/locator；条件 UPDATE 限定 project/run/epoch + PREPARED + worker=''；RowsAffected 必须为 1，否则 rollback 并拒绝 relaunch。STARTED、worker、journal_locator 在同一语句、同一事务提交。
4. `:527-529` 的 dispatch_started seam 和 StartBridge 都在 Commit 成功之后；Commit 出错直接 return。
5. `adapters/runtime/bridge_windows.go:184-212` 创建全新 dispatch 目录、取得 owner.lock、创建 PREPARED bridge journal 并 persist，之后才 `:279` sandbox.Start。
6. `ops/experiment_sandbox/sandbox_windows.go:295` 使用 CREATE_SUSPENDED 创建进程；`:313-318` BeforeResume 完成之前不会 `:325` ResumeThread。
7. `bridge_windows.go:279-287` 的 callback 先持 w.mu，写 journal identity + STARTED 并 persist，再调用 coordinator callback。`runtime_coordinator_windows.go:530-555` 重新 dispatchGate，要求同一 STARTED worker 与空 identity，写 DB identity 和 client_queue_fences identity，然后 Commit；完成后才返回 sandbox 去 ResumeThread。
8. `async_windows.go:58-92` 的 Start 在 suspended identity persistence 与 ResumeThread 成功后返回；`RunAdmitted:562` 才到 native_started seam。

journal persist 的 Source 实现为 `runtime_windows.go:98-118` Write、Sync、Close，再 `process_windows.go:174-183` MoveFileEx(REPLACE_EXISTING|WRITE_THROUGH)。这些是 Source 顺序证据；本轮没有执行实际 crash 测试或存储耐久性实验。

## 崩溃窗口

| 窗口 | 可见状态与结论 |
|---|---|
| DB UPDATE 之前或 Commit 失败且尚未 StartBridge | 本次调用未进入 StartBridge；可能已经计算 inputs / session projection，不能泛化为没有任何前置工作。 |
| DB Commit 成功之后、StartBridge/journal/进程创建之前 | DB 已 STARTED + worker + locator，可能没有 journal 或进程。STARTED 不能反推 worker 已运行。 |
| CreateProcess(CREATE_SUSPENDED) 之后、callback journal identity / DB identity 提交之前 | suspended 原生进程可能已经存在；DB 已 STARTED + locator。不能凭空 identity 或 observation0 声称没有创建过进程。 |
| journal identity 和 DB identity 已持久化、ResumeThread 之前 | 有已绑定 suspended identity，但可能尚未执行 worker 用户代码。 |
| ResumeThread 之后、native_started seam / terminal observation 持久化之前 | worker 可已执行而 observation_sequence 仍为 0。缺 terminal journal/observation 必须保留 UNKNOWN。 |

没有发现“这条 RunAdmitted 路径先启动 worker，随后才提交 STARTED/locator”的窗口。存在上表相反方向及 suspended/resume 阶段窗口。数据库被回滚恢复、其它二进制/旁路启动、其它 epoch、未来并发调用均超出单个空字段快照的证明范围。

## 事务、lease 与锁的边界

- `resources.go:17-19` 的 resourceWriteLock 是事务内 UPDATE resource_write_lock，取得数据库写锁；同一 launch fence 事务使用条件 UPDATE + RowsAffected=1 仲裁并发，而不是依靠 `c.mu`。
- `runtime.go:140-151` 的 runtimeLease 核验 executor ID、epoch、lease token digest、到期时间以及 Task.active_run_id。这里只阅读 Source，没有读取实际 token、私有配置或 SQL 行。
- `RuntimeCoordinator` 的 `mu/scanMu` 是进程内锁；Serve/Scan 在 `:189-244` 使用 scanMu 和 active map，`RunAdmitted` 本身不持一个覆盖整个 launch 的 c.mu。它不能替代数据库 fence。
- `newRuntimeCoordinator:121-141` 绑定 DB 所在 DataRoot，并取得或 Borrow DataRootLease。`bridge_windows.go:129-141` 归一化且拒绝 reparse root，再锁 coordinator.lock；`process_windows.go:185-194` 以 share_mode=0 CreateFile。DataRootLease.Borrow 在 `data_root_windows.go:58-78` 用进程内 mutex 校验路径、文件句柄、未 closed/borrowed。本轮不声称当前正在持有该 lease。
- 若将来设计 prepared-run abandon，必须在合法 Host ownership 下与 launch 共用同一数据库写锁和 project/run/epoch 条件，原子写入一个未来 launch 必然拒绝的终态/fence；仅先读 PREPARED 再异步修改会有 TOCTOU。本报告不定义 controlTask/API，也不授权执行该操作。

## 当前 failure745 的可说与不可说

输入为已封存 failure745 组件 HDF/manifest、其 business-state.observed.json、原 public stderr、生命周期事实及受审 helper Source。Business 快照为 Run QUEUED、Task RUNNING、同 epoch dispatch PREPARED、worker/journal_locator 为空、observation_sequence=0；这不是本轮 fresh SQL。

原 helper `execute.go:452-455` 的 readGO 失败直接返回。`:206-207` 调用 verifyGOEvidence，`:234-237` 的 contract readPinnedObject 错误直接退出，`:212-217` 使用 domain.Decode。原始 stderr 为 lossless canonical JSON 数字错误。private claim 赋值/保存位于 `:466-469`，RunAdmitted 位于 `:489`。因此，既有精度故障因果链支持“这个已绑定失败调用未到达 claim write / RunAdmitted”；精度根因沿用封存745审查，不是本轮重新运行。

**没有读取实际 Host private state。ExecuteClaimedAt 的实际字段值与历史存在性均为未观察，不能报告 ExecuteClaim absent。** 某次调用未到达写入位置不等于文件中没有先前值；claim 存在也不等于 worker 已启动，因为 claim 在 RunAdmitted 之前。若未来操作合同要求 claim absence，应由获授权的 Host 在排他 ownership 下输出最小、绑定 Run/epoch 的 attest，而不是本报告补造 absence；也可由正式设计明确定义消费/终止既有 claim 的规则。本轮未执行这些方案。

原 Root Host Job 闭合是当次外层进程清理证据；它不能替代受信任 runtime worker terminal journal，也不能推出历史没有 worker、制造 queue-empty/children-stopped observation 或归零 provider。provider_requests 继续为 NULL，recorded effects 为 0。

## 现有 recovery 的明确限制

`runtime_coordinator_windows.go:970-1000 Recover` 明确“Missing or partial facts retain UNKNOWN, even for PREPARED”，无有效 locator 即调用 markUnknown；它不会 StartBridge。`:1003-1018` 必须先 ReconcileBridge，然后才 recoverTerminal。

`runtime_recovery_windows.go:171-177` 先从受信任 BridgeJournal ingestObservation；`:196-225` 在独立事务保存不可变 artifact；`:226-285` 的第二事务检查 current epoch、Task.active_run_id、effects reconciled、current admission，再导入合适 terminal fact。无 terminal journal 时不能借此补造 observation、标 CANCELLED/SETTLED 或强行释放为可重试。

## 本轮执行边界

只读取 Source 和已有公开收据，并在新的独立 namespace 写审查文件；没有执行 Source 模块、SQL、Native helper、provider、OS probes、private state、canonical writer。新增诊断 751 为一次无必要的 guessed cmd 根 rg os error 2；原输入/结果从已保存 store 原样导出，outer1 / Python null / Native null / provider0，不重置或重记既有 failures。完成后 STOP。


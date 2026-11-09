# M1 有限生产集成卡范围（只读方案）

建议交给**同一个 Source owner 串行完成三张卡**：M1-01 候选构建与真实 worker 暂停协议；M1-02 canonical 暂停及 same Run 的最小恢复内核；M1-03 真实产品路径资格验证。普通 PAUSE 恢复保留 Run，只生成 successor lease_epoch；CANCEL 后继续才新 attempt/Run。M1-02 含完成暂停/恢复纵向路径不可缺少的最小 M2 内核，不据此宣称完整 M2 完成。

依据 Main `c465d1356480d6e6a90da84656724f9fc02b31c7` 和既有47-input架构。32 个 core 输入与 Main 逐文件比较，31 个一致，仅 client_protocol.go 的 writer attach 已强化；本方案首卡走既有 **V1 Task actions**，不修改该文件、不借 attach 获得 writer。V6 独立接受为有限 SOURCE_FIXTURE_ACCEPTED；冻结 hash `9e5dd1e5d93f19c6a4aa5eb5c0e2ebd7f0d1e05a987f6ec03963b4b560139da9`。比较及新增接点基线在 [input-baseline.json](input-baseline.json)。

## 施工所有权与精确范围

Source owner 在新 C worktree 从上述 Main 起步。15 个既有生产文件：

- `adapters/runtime/mu/worker.mjs`
- `adapters/runtime/bridge_windows.go`
- `internal/host/runtime_setup_windows.go`
- `internal/domain/operations.go`
- `internal/domain/orchestration_controls.go`
- `internal/domain/orchestration_recovery.go`
- `internal/domain/durability.go`
- `internal/domain/durability_session.go`
- `internal/domain/durability_checkpoint.go`
- `internal/domain/runtime_coordinator_windows.go`
- `internal/domain/runtime_command_queue_windows.go`
- `internal/domain/runtime_recovery_windows.go`
- `internal/domain/runtime_dispatch.go`
- `internal/domain/runtime_sessions_windows.go`
- `internal/domain/client_command_queue.go`

新增3文件：

- `adapters/runtime/mu/build-candidate.mjs`
- `internal/domain/runtime_pause.go`
- `internal/domain/runtime_pause_windows.go`

修改7个既有测试（只补相关断言）：

- `adapters/runtime/bridge_control_windows_test.go`
- `internal/domain/orchestration_controls_test.go`
- `internal/domain/runtime_recovery_windows_test.go`
- `internal/domain/runtime_coordinator_windows_test.go`
- `internal/domain/runtime_command_queue_windows_test.go`
- `internal/host/runtime_setup_windows_test.go`
- `internal/domain/remote_test.go`

新增5测试：

- `adapters/runtime/mu/worker-pause.test.mjs`
- `adapters/runtime/mu/build-candidate.test.mjs`
- `internal/domain/runtime_pause_test.go`
- `internal/domain/runtime_pause_windows_test.go`
- `internal/host/runtime_pause_integration_windows_test.go`

不授权 internal/domain/**。operations.go 在一般 RESUME requeue 前，按真实 Principal 路由已确认暂停的同 Run 原子恢复；现有 orchestration.go 通用 FAILED/未开始分支可保持不变。durability.go 抽取可在调用方现有事务中复用的恢复内核，保留旧 ResumeCheckpoint 包装与测试，不能用用户/设备冒充 SCHEDULER 调方法。runtime_pause.go/windows.go 集中新增 ledger、pause gate、恢复转换；不要把新状态散进任意旧函数。

Root 独占、串行整合的迁移/备份范围，Source owner 不写：

- `internal/domain/backup.go`
- `internal/domain/backup_command_queue.go`
- `internal/domain/backup_migration.go`
- `migrations/sqlite/0025_runtime_pause_activations.sql`
- `internal/domain/backup_pause_upgrade.go`
- `internal/domain/backup_pause_upgrade_windows.go`
- `internal/domain/backup_pause_upgrade_other.go`
- `internal/domain/backup_pause_upgrade_test.go`

Main 已有0024，建议 Root 预留0025；若整合时库存变化，先统一改新迁移编号，绝不覆写已存在编号。建议三个表：runtime_pause_intents（意图/actor/CAS/取消优先），runtime_checkpoint_activations（每 Run/epoch 唯一激活及前驱/检查点/queue cut/SDK身份），runtime_pause_receipts（追加式状态/ACK/恢复收据链）。同一前驱只有一个 successor。备份摘要、引用校验、新目录恢复识别这三表且保留旧 CANCEL/SEALED/restore 围栏。新增24→25迁移程序复用现有受控备份/演练原则；不要放宽23/24旧迁移的未来表白名单。store.go 自动发现连续迁移，无需默认改其构造器。首轮用隔离新 schema25 数据目录，真实安装库不动。

## V6 集成与构建

现有 build.mjs 固定 installed8df/vendor hashes；host runtime_setup_windows.go:78 同样只接受8df。**不能生成 V6 bundle 后伪填 mu_commit=8df**。

新增候选专用 build-candidate.mjs，将 worker 的 pi-agent-core 和 pi-coding-agent 分别解析到 V6 完整候选源树的 agent/src/index.ts 与 coding-agent/src/index.ts；pi-ai 仅使用 V6 census 已核验分布。V6 的基线7ec与 installed8df不同，不能仅把9文件贴到已安装SDK。冻结9文件和完整候选源只读，完整 esbuild metafile/input path/realpath/hash 必须证明没有落回 installed agent/session dist；若新增导入超出旧 census，记录并审核实际内容，不声称旧2134清单已覆盖新 worker 构建。

输出只到 C Source worktree 的 .local/m1-assets，元数据明确 source_mode=ACCEPTED_M0_CANDIDATE、V6 manifest/base/patch/独审 hash、worker源/bundle、依赖版本和 pause capability。host增加显式可信 candidate资产入口/构造策略并绑定该冻结身份；默认 loader/pin 保持原状，不能接受请求或环境变量随意指定SDK。资产装载与实际产品调用仍走同一个 Host/RuntimeCoordinator，不另造调度器。

worker 可在创建 session 后通过现有 session.agent.registerPauseDataSchema 登记 researchos.command.v1 的精确结构，再注册控制；不需修改冻结 V6。首次运行建立产品 native_session_ref 与 SDK session ID 映射；恢复使用 SessionManager.fromPauseCheckpoint 和原 header/tree/leaf，再调用 restorePauseCheckpoint/resumePause，禁止重新 prompt(original)。

## 状态与协议必须同时落地

| 阶段 | 正确事实 |
|---|---|
| PAUSE_REQUESTED | 当前 auth/CAS 保存意图，Task BLOCKED仅表示等待；不写cancel_requested_at。停止新模型/工具/queue派发，允许在途效果安全完成。 |
| CHECKPOINT_SEALED | bytes/hash/binding、Artifact/use、可信checkpoint事实及journal均持久后才ACK；还不能宣称进程已停。 |
| PAUSED_CONFIRMED | matched ACK、turn.paused、真实旧进程树/流已停、效果已对账、SDK队列及消费水位已封存；没有非法公共Run.status=PAUSED。 |
| RESUME_PREPARED → RESUMED | 同事务验证当前请求者/输入/模型/预算、checkpoint/carry、旧停机证据，sameRun e→e+1、新lease/dispatch/activation、Task RUNNING；启动成功后提交激活事实。重复幂等不二次启动。 |

原 Run 保留合法非终态和 active_run_id，由内部 ledger 闸门防新执行；已证明PAUSED的租约过期不得被 RecoverExpiredRuns 当成失联，未确认状态超时仍 RECONCILING。冻结未消费队列不是 queue_empty=true；resume内核需要专门 paused-frozen proof，不能删旧proof门槛。CANCEL始终抢先，CANCELLED不能走本次sameRun恢复。

外层继续使用 BridgeFrame 已知字段，版本与binding放 payload。快照最多按 SDK 的12MiB，走固定sandbox output普通文件+小path/hash帧；64KiB线限不变。Core拒绝reparse/路径越界，单次有界读取后复制可信文件并seal；同步升级 recoverCheckpoints 的128KiB旧读取方式，不能仅增大发送端。checkpoint序号s，turn.paused必须是下一合法序号而非复用s；ACK关联s/hash/封存Artifact-use，不信persisted布尔。新进程epoch有自己序列，旧frame/ACK借助完整epoch/dispatch/process身份拒绝。

恢复验证原checkpoint的旧leaseEpoch/inputHash，再通过单独可信activation链 e→e+1使用新outer binding；不修改旧JSON重标epoch。保存worker累计model/tool次数和command ledger，避免max_calls/预算责任被重置。未知金额保持UNKNOWN/null；未知效果先对账，二者不可混为一谈。

## queue 身份与恢复

generation、command_id、message_id、content_hash、queue_sequence均保留；lease_epoch与writer_epoch是两种身份，恢复不要求writer换代。ENQUEUED且不在snapshot的消息由新activation派发；SDK_ACCEPTED已在checkpoint里的消息只restore一次；CONSUMED不重发。SENDING/UNKNOWN必须结合已持久receipt及SDK水位对账，不能盲重放。到达暂停cut之后的新消息只留ENQUEUED，不回填旧checkpoint。

现有 bindClientRunQueue:35 的same epoch约束不能简单放宽。只有已确认PAUSED的唯一successor事务才可更新当前epoch/dispatch指针，旧activation保留。原SEALED/CANCEL_FENCED/restore_fenced绝不重开；暂停使用额外执行闸门，不能冒用正常完结seal，也不能clearQueue。

## 第一条可验收真实生产路径

候选 Host 使用隔离 schema25/资产/工作区，运行现有批准的真实模型配置；通过真实产品API创建Task，由sole coordinator启动真实AppContainer/V6 worker。让已登记的有界工具（例如仅测试工作区的run_check）处于可观察在途状态，产品API提交带标识的STEER/FOLLOW_UP，再发 V1 Task PAUSE。工具安全结束后，下一模型/工具不得启动，等匹配封存ACK、turn.paused及OS/流停止证明。

检查原产品/SDK session和tree/leaf、两条队列、已消费水位、已完成效果、UNKNOWN金额责任，再显式 V1 RESUME。必须sameRun、新epoch、新进程、只一个dispatch，不重发原prompt，未消费指令各一次，最终助手回复完成无error。重复RESUME不加调用；撤销设备后重放旧成功请求仍被拒绝。请求使用真实DeviceActor，动态设备角色与issuing Owner grant交集在每次请求、幂等回放前、延迟启动前重查；Owner失去全局OWNER即不可认证，设备自身降READER则不能控制。手机attach/handoff保持禁止。

先以合成provider把ACK丢失/乱序/崩溃竞态跑成 NATIVE_SYNTHETIC，再以真实已配置provider取得 NATIVE_LIVE_MODEL_PAUSE_RESUME。两者都是真实产品接线，但前者不能替代真实模型资格；资源缺失仅阻塞LIVE支路。M1首卡不含Goal批量暂停、手机V2资源响应与撤销全旅程、CANCEL后新工作完整UX，这些仍为后续M2/手机工作。

## 验证命令与完成判据

下列新文件/测试名/CLI是**建议施工目标，当前不存在或尚未接线，不是已执行命令**：

- candidate build：`node adapters/runtime/mu/build-candidate.mjs --source <readonly-v6-candidate> --freeze <v6-final-20261014-r3> --manifest-sha256 9e5dd1e5d93f19c6a4aa5eb5c0e2ebd7f0d1e05a987f6ec03963b4b560139da9 --output <C-source-worktree>/.local/m1-assets/mu-worker.mjs`。通过条件：No installed-tree writes; new metadata/metafile/input census prove V6 imports, all actual bytes and output digest; default build and pin unchanged。

- worker wire unit：`node --test adapters/runtime/mu/build-candidate.test.mjs adapters/runtime/mu/worker-pause.test.mjs`。通过条件：Strict command binding; no boolean-only ACK; file bounds/hash; queued custom schema; repeat pause; no new prompt on resume。

- Go scope：`go test ./adapters/runtime ./internal/domain -run 'Test(Bridge.*Pause|BridgeControlIdentity|BridgeQueueEmpty|RuntimePause|RuntimeCoordinatorCheckpointResume|RuntimeCoordinatorCheckpointCrashRecovery|W06TaskControls)' -count=1`。通过条件：No skip and nonzero expected test census; native process cases require Windows; no formal acceptance inferred。

- candidate host production path with synthetic provider：`go test ./internal/host -run '^TestProductMuPauseResumeNative$' -count=1 -args -local-runtime-assets-dir <C-source-worktree>/.local/m1-assets -local-runtime-verifier-executable <verified-candidate-verifier.exe>`。通过条件：Real Host/V1/sole coordinator/AppContainer/V6 worker/checkpoint artifacts/new process; provider synthetic and explicitly reported NATIVE_SYNTHETIC; existing absent-assets skip must count BLOCKED, never PASS。

- root migration rehearsal：`go test ./internal/domain -run '^TestPauseActivation(Migration|BackupRestore|CancelFence|SuccessorCAS)' -count=1`。通过条件：Fresh schema25 plus isolated 24->25 rehearsal; failure leaves original unchanged; restored new directory preserves paused fences/receipts; no production DB changes。

- existing device enforcement：`go test ./internal/domain -run 'Test.*(Remote|Device|RuntimePauseAuthorization)' -count=1`。通过条件：Every request and idempotent replay reauth; revoked/Reader denies control; issuer loses Owner => unauthenticated; preserve actual DeviceActor。

- real model qualification：`POST /v1/projects/<project>/tasks/<task>/actions with action=PAUSE, then new authorized action=RESUME; Authorization, X-Correlation-ID, Idempotency-Key, If-Match from actual current Task; run on candidate Host using existing approved real model configuration`。通过条件：NATIVE_LIVE_MODEL_PAUSE_RESUME evidence requires real provider receipts and process evidence; synthetic or source tests cannot substitute。

必须记录预期非零test census，缺资产导致SKIP视为该支路BLOCKED，不能算PASS。最低负例包括：错误ACK/old epoch/大帧/文件损坏、seal前后与successor提交前后崩溃、并发RESUME、CANCEL抢先、队列混合状态、paused租约过期、UNKNOWN金额不清零/效果不重放、撤权后回放、备份新目录恢复。原 TestRuntimeCoordinatorCheckpointResume 与W06控制回归保留。

本报告只新增C目录分析交付，没有实施、测试、真实模型调用、DB或进程变更。正式增量0，保持0/42、22父任务open；后续Source/Native/LIVE/手机/正式接受逐层登记，不能相互替代。

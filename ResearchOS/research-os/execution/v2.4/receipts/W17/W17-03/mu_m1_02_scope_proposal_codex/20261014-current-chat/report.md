# M1-02 Core pause/resume 有限施工合同（只读方案）

状态：`READ_ONLY_SCOPE_PROPOSAL`。本报告没有实现、执行测试、调用模型、修改数据库或签发接受。建议单一 source owner 串行完成下面 15 个文件；Root 是唯一整合者。M1-01 已接受接口保持冻结。

## 基线与依赖

- 当前 Main：`a7ec7ebf2d53848ea163b6115667b3e3761a6bd2`。源码检查始于 `d9fcf30d7accc5a7632e8c69a3d25710931dd8ca`；生成清单时 Root 已新增 host coding inventory 的 any 修复，以下 Core source 未变化，最终摘要记录当前字节。
- 已接受 M1-01 候选：`c6f39e84fd0efa046a9651bb5542a4f3c6b4344b`，现已包含在 Main。
- Root schema25 只读来源：`C:/Users/yqyyds/.codex/researchos-build-worktrees/root-schema25-20261014`。读取到 `carry_use_principal`、当前 revision 的完整 `STATE_TRANSITION` witness、sealed bytes/use/carry 校验；SQL 摘要为 `6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0`。R3 独立接受尚未在本报告中核实。
- 开工前由 Root 提供已接受 schema25 冻结 manifest。M1-02 只在独立 C worktree 组合 Main + 该确切冻结版本，使用新临时 data root/schema25。Root schema files 属于依赖，不属于本卡可编辑范围。
- schema25 的普通迁移入口可能会碰到已安装 schema24；本卡不得进入 Main 正常启动/安装包，不得对真实 DB24 运行候选。受控 24→25 升级是独立 Root 工作。
- 参考：`execution/v2.4/receipts/W17/W17-03/mu_m1_bounded_scope_codex/20261014-current-chat/report.json`。本报告以当前源码为准缩小第一卡，不把其规划测试当成已执行。

## 核实到的缺口

1. `orchestration_controls.go:controlTask` 对 PAUSE 也设置 `CANCEL_REQUESTED`。活跃 Mu 的真暂停必须先分流；未声明支持的新协议不能被当成成功暂停。
2. `operations.go:actTask` 的 RESUME 走普通 requeue，而 `orchestrateTask` 拒绝 unresolved Run；`Scan` 只 claim 新 READY Task，且 active Run 会提前阻断路由。
3. `checkpoint` 仅接受 inline/checkpoint.json，把 metadata 当 payload；返回旧式 ACK。M1-01 需要 captured bytes、durable artifact/use、typed `SealCheckpoint`。
4. `bindClientRunQueue` 要求相同 epoch；`recoverClientQueue` 用当前 fence 的 epoch 解释旧 journal，会在恢复后误拒历史证据。
5. `RecoverExpiredRuns` 会把暂停后自然过期的 RUNNING Run 改为 RECONCILING；需要依据完整暂停证明处理。
6. V1 的真实 Idempotency-Key/requestHash 只在 http.go 中，不能用 cid 冒充；暂停/恢复 intent 应获得真实请求元数据。
7. `runCommandBridge` 统一拥有 ACK 次序，不能在 checkpoint 分支抢先 ACK 再让通用循环 ACK 第二次。

## 精确写范围：12 个 source + 3 个新增 test

| 文件 | 唯一允许责任 |
|---|---|
| internal/domain/http.go | 仅 actOnTask 传入已鉴权 Principal 与原 key/requestHash；保留现有 replay 前认证、ETag 和 response schema |
| internal/domain/operations.go | actTask 的 pause-aware RESUME 分流与 typed request metadata 传递，普通 SUBMIT/RESUME 行为不变 |
| internal/domain/orchestration_controls.go | 活跃支持协议的 mu_turn PAUSE 建立 intent；保留非活跃 Task 行为；不再把该路径写成取消 |
| internal/domain/client_protocol_queue_control.go | fenceClientTask 共同入口对该 task 所有未结束 pause/activation 加 CANCELLED CAS+receipt；覆盖 Task/Run/Goal/client CANCEL |
| internal/domain/orchestration_recovery.go | RecoverExpiredRuns 识别确证暂停，缺证据进入核对；不把过期作为自动恢复授权 |
| internal/domain/runtime_dispatch.go | currentDispatchedRun 对暂停生命周期的 operation gate；封存中仅允许必要 heartbeat/upload/seal，确认暂停后拒绝执行权刷新 |
| internal/domain/runtime_broker_windows.go | brokerEffect 新调用在 pause cutoff 后不得取得新的 effect admission；已有 durable effect 才可完成，保留原预算与 UNKNOWN 语义 |
| internal/domain/runtime_coordinator_windows.go | Scan 显式 resume work 优先于 active-run guard；RunAdmitted 暂停终结分支；inputs、checkpoint、Recover 接入 bounded helpers |
| internal/domain/runtime_command_queue_windows.go | pause negotiation/control、已初始化的 HOST_PAUSE_CAPABILITY receipt、暂停时停止新投递/普通 seal、唯一顺序 typed ACK、activation 认证后 fence epoch CAS、历史 queue recovery |
| internal/domain/runtime_recovery_windows.go | legacy inline 与新 pause metadata fact 分流；可信 checkpoint.sealed.json 12MiB 有界读取/校验；恢复 pause proof，不伪造 terminal report |
| internal/domain/runtime_pause.go（新） | portable schema capability 检测、intent/CAS/receipts、fresh actor 检查、请求幂等、取消优先、carry+activation 事务、读取冻结投影 |
| internal/domain/runtime_pause_windows.go（新） | 唯一 coordinator 控制、native stop+drain 确认、同 Run successor dispatch/recovery、snapshot 与队列账本交叉验证 |
| internal/domain/runtime_pause_test.go（新） | 事务/授权/幂等/取消/计数/backup witness 的针对性测试 |
| internal/domain/runtime_pause_windows_test.go（新） | coordinator/queue/ACK/边界崩溃/原生恢复测试；复用现有 fixture，不改已接受 M1-01 |
| internal/host/runtime_pause_windows_test.go（新） | 真 Host + 产品 session/task APIs + coordinator + AppContainer + 已接受 worker + canonical DB 的一次完整暂停恢复 |

不得默默扩为其它 source。发现需要 SDK、bridge、host setup、public schema、migration、backup writer、client attach/handoff 或 GUI 改动时，输出具体 blocker 交 Root 定范围。当前 `client_command_queue.go` 已允许 BLOCKED Task、OPEN fence、未终结 Run 接收 ENQUEUED，预计无需改。`carryCheckpoint` 可直接复用并在同一事务查询新 epoch 的 use，无需改其返回合同。`runtimeModelCallGate` 已按同 Run 的 distinct effect_key 累计，无需为暂停重置。

## 状态与公共投影

暂停只适用于实际支持 `RESEARCHOS_PAUSE_V1` 的活跃 Mu queue-controlled dispatch，绑定唯一 Task/Run/session/generation/epoch/process/manifest。请求前若没有已绑定 process/input hash 或 queue 尚未初始化，不生成假的暂停成功；返回当前不可暂停的明确结果。非 Mu 路径不因此获得 native resume 宣称。

`PAUSE_REQUESTED → CHECKPOINT_SEALED → PAUSED_CONFIRMED → RESUME_PREPARED → RESUMED`。不明边界进入 `RECONCILING`；任何阶段 CANCEL 优先转 `CANCELLED`，不得恢复。Root schema 的转移许可只是存储限制，Core 必须执行 expected state+revision CAS 并核对 RowsAffected=1。

Task 暂停后为 BLOCKED，active_run_id 保留；Run 保持原合法非终结 enum，无新 PAUSED enum，无 CANCEL 标记。暂停状态以内表和原生 proof 为准，不能把 Run 的 RUNNING 投影单独当作存活证明。原 Run lease 到期不刷新、也不触发新工作。首卡不修改 V2/phone projection；V1 Task、Run.checkpoint_artifact_id 和 authorized Artifact 查询可见，细粒度 pause state 用本地控制测试读取 canonical ledger。原 SDK queue 有待消费内容时绝不填 `queue_empty=true`；OS stdout/stderr drained 与 SDK queue empty 是两个事实。

## 请求与事务合同

### P1：PAUSE 请求提交

HTTP 在当前认证/授权、ETag、幂等查询后传入 typed `{principal,key,requestHash,correlationID}`。同一事务取得写锁、查 current Task/Run/dispatch/queue 身份、检查 CANCEL 和 active intent，插入唯一 `(project,run,epoch)` intent、写 Task BLOCKED/控制 marker、追加 revision1 witness 和 Task event。冲突 key+不同 hash 拒绝；同 hash HTTP replay 不新增 intent。已取消不能用旧成功请求恢复权限。

原 input hash 的来源必须明确：coordinator 在 queue initialize ACK 成功后，以独立 `HOST_PAUSE_CAPABILITY` kind向既有 client_control_receipts 追加 host receipt（command_id为空），绑定 exact dispatch/process/generation、协议、初始化sequence和 bridge journal.InputHash；不改原 worker command.accepted payload/hash。HTTP PAUSE 只从该已落库host receipt取原 input hash，并与当前dispatch/fence核对，不重新生成request、不从用户body接收hash。该kind不受现有receipt表enum限制，仍走appendClientReceipt/hash/backup verifier；测试必须证明backup兼容。SDK snapshot input_hash为不带sha256前缀的hex，而bridge journal.InputHash带前缀；只在明确边界标准化，禁止混用。此方案避免API读取正在变化的worker文件或增加Service全局hook。schema25未安装或capability receipt不存在时新暂停能力fail closed。

内部 research driver 的 PAUSE 不得绕过鉴权加入 Mu native 路径：没有真实可重新鉴权 actor/request metadata 时拒绝该新路径，保留已有非 Mu 行为。只对现有调用点作类型兼容，不用 `goal-control` 伪 actor 开新执行。

每次 intent revision 变更，包括同状态 updated_at，必须在同一事务读取完整存储投影（包含 null、时间、全部列），写 `STATE_TRANSITION` receipt：body 的 project/pause_id/kind/sequence 与列一致，state/revision/intent_hash=Hash(full intent)。顺序号严格递增，previous_receipt_hash 指上一条 body_hash。观察性 receipt 不冒充 state witness；原始失败与证据 append-only。

### P2：送 pause、封存及 ACK

coordinator 在已初始化、绑定一致的 bridge 发送一次 `{type:command.pause,version:RESEARCHOS_PAUSE_V1,pause_id,binding}`。初始化 request 和 control 均协商 pause protocol。停止新队列投递及 prepare/commit seal，不 clear 队列；已进入执行的 model/tool 自然完成，核对效果/花费后到 safe boundary。若在 pause admission cutoff 后收到新未入账 effect，不静默执行：保留框架证据并核对，不能捏造成功暂停。CANCEL 独立优先并可中止 broker。

checkpoint frame 来时：验证 intent/dispatch/process/epoch/pause_id、queue cut/ledger/sdk watermark；用 `Bridge.CheckpointBytes()` 获得已经捕获的精确字节，严禁从 sandbox 再读或 JSON 重新序列化替代字节。文件 ≤12MiB，frame/fact ≤64KiB。

写 `checkpoint-<sequence>.json` durable fact，含 project/run/epoch/manifest/dispatch/sequence/content_hash、固定 trusted payload locator `checkpoint.sealed.json`、size、原 pause metadata/binding；fact 不是大 payload。fact hash 取落盘 bytes 的 SHA256。用 stable key 上传并 seal CHECKPOINT Artifact；严格查询旧 epoch executor 的唯一 artifact_use，核对 receipt、sealed bytes/hash/size。然后事务 CAS 为 CHECKPOINT_SEALED，保存全部 frozen metadata + original/use principal + journal hash + Run checkpoint pointer + witness。

只有这些 durable 条件全部完成才在顺序 ACK 循环到达该 sequence 时调用 `SealCheckpoint`。不在 checkpoint helper 内提前 ACK；通用 `Acknowledge` 对该 sequence 不再调用第二次。typed seal 完整包含 version,type,sequence,pause_id,binding,content_hash,checkpoint_artifact_id,checkpoint_use_receipt_hash,checkpoint_use_principal,journal_checkpoint_hash。ACK 的历史遗失只按 exact committed seal 重发；重入、不同 hash/sequence、跨 dispatch 均拒绝。

文件、API seal、SQL 不能假装一个事务：中间失败留下 immutable fact/artifact；继续按 stable key 查询恢复。不会因后续 SQL 失败删旧 artifact，也不在缺 use/intent proof 时 ACK。

### P3：确认停止

`turn.paused` 只是一条 worker frame。顺序 ACK、bridge.Done、effectsReconciled、Finalize、Observation 中 exact identity/epoch、children_stopped、streams_drained、cleanup_complete、checkpoint seal 与 journal 一致全部具备后，事务 CAS CHECKPOINT_SEALED→PAUSED_CONFIRMED，并保存原生停止 receipt+witness。Task 仍 BLOCKED；不调用 reportRun/cancel acknowledgement，不把等待队列标为消费或丢弃。

### R1：显式恢复请求与调度

使用已有 V1 Task RESUME；无新 endpoint、无 executor/scheduler token 泄漏。当前 Principal 与原 key/hash 持久化为 `RESUME_REQUESTED` receipt（kind 可用 Root 现有开放字段），其请求绑定当前 pause revision/checkpoint/Task revision。Task 仍返回既有 schema 下的 BLOCKED，表示请求已收下；业务状态仍 PAUSED_CONFIRMED，直到 coordinator commit。重复不同 key 的请求不能产生第二个 successor。若已有尚未消费的有效请求，返回原状态/冲突，不追加可竞争执行。

Scan 在 active-Run guard 前寻找该明确请求；单 route/sole coordinator 持有既有 active mutex。重新加载 actor 的真实角色、grants、revoked 和 `constrainRemotePrincipal`，重新核对 issuing Owner、Task/Goal、配置/input/dependency、runtime admission 和 effect/budget 状态。不得仅使用存储的 Principal 快照，也不得替换成 scheduler actor。权限失效保留 checkpoint 与请求失败 receipt，只阻塞该支路；需要新显式请求，不能靠权限恢复自动重放旧失败请求。

### R2：同一事务创建 successor

写锁 + CAS 确保旧 intent=PAUSED_CONFIRMED、revision/hash相符；旧 Run epoch=e、Task.active_run_id相符；有 exact stopped observation；无 CANCEL/restore_fenced/UNKNOWN unresolved effect；queue fence为OPEN且仍绑定旧 generation/e/dispatch。

事务内顺序：CAS intent→RESUME_PREPARED，successor_epoch=e+1；原 Run 增 epoch，保留 run id/attempt/inputs/context/progress/budget/effect histories；生成新 lease hash（明文只交 coordinator）、清旧 external/process active字段并保留历史；复用 carryCheckpoint，以 resume actor记录carry，保留原 artifact id/hash，查询新 epoch executor的carry use/principal；prepareRuntimeDispatch 创建唯一新manifest；插入 immutable activation（含旧checkpoint use principal与新carry_use_principal，二者不可混用）；CAS更新当前 queue fence的runtime_epoch/dispatch/manifest、清 process_identity，generation/accepted_writer_epoch/command身份不变；Task改RUNNING，删除仅匹配的PAUSE control；追加完整 witness+activation/request-consumed receipts。任何失败整事务 rollback，不留下半个 epoch/activation/carry/queue 指针。

开始恢复前仍跑 existing admission/session/model/tool gates。新 request 含原协议、pause_activation 的 previous_epoch/new_epoch/checkpoint_hash/artifact/use/use_principal/carry_use_receipt_hash/original_input_hash；固定 input `pause-checkpoint.json`。Core 持久并验证 carry_use_principal，M1-01 wire 不要求该额外字段，不为此改 worker。outer runtime binding=e+1；SDK snapshot binding/sessionId/tree/header/cwd/inputHash仍使用原值。禁止 `prompt(original)`；仅 `resumePause()`。当新进程 identity 和初始化/restore ACK确证后 CAS→RESUMED，并写 witness；未到该证据不得预填成功。

### R3：提交后崩溃和 lease

RESUME 请求 receipt 与 successor 创建分两段，避免公开 API 回传 executor token。coordinator 在 R2 获得明文 lease 后直接 RunAdmitted，仍用 PREPARED→STARTED CAS。

若在 R2 commit 后、STARTED前崩溃，重启不得把新PREPARED activation按普通无journal直接 markUnknown。只有 exact activation、未取消、当前权限仍有效，且dispatch PREPARED/worker空/identity空/无native journal或任何effect启动证据时，允许在该**同一个 successor epoch**内做受锁CAS的 lease replacement+专门receipt，再首次launch；不再递增epoch，不再carry，不再插activation。若无法证明未尝试启动，进入RECONCILING。STARTED后缺journal/identity不充分一律不盲重启。此受限规则须独立负面测试；不复用普通新Run重建或 prepared abandonment。

## Queue restore 与历史回执

| 状态 | 恢复规则 |
|---|---|
| ENQUEUED | 不在frozen SDK snapshot；新激活完成后按原queue_sequence投递。pause期间新到达仍ENQUEUED，不能注入旧snapshot |
| SDK_ACCEPTED | 必须在 snapshot原ledger里，且在两条SDK队列之一或精确consumed watermark；恢复SDK队列，不从DB重发 |
| CONSUMED | snapshot/receipt保持单调，不重发，不降级为SDK_ACCEPTED |
| SENDING / UNKNOWN | 用旧dispatch exact accepted/consumed receipts与snapshot交叉核对，能唯一解释才推进；不明则RECONCILING，不重置ENQUEUED |
| DROP_REQUESTED / DROPPED | 保留cancel语义；cancel fenced generation永不恢复；不把待确认drop当成consumed |

snapshot queue cut指worker接受水位，不等于当前DB accepted_through；必须证明 cut以内每个消息身份/hash/delivery/ledger状态，cut以上不得声称被快照接受。receipt/ledger缺项、重复、contradictory消费均拒绝。SDK STEER与FOLLOW_UP顺序分别保持；已完成tool effect不重做，model/tool累计计数恢复，UNKNOWN钱仍null/UNKNOWN，下一调用仍经当前budget gate。

恢复旧 journal 时按其旧dispatch + immutable pause/activation绑定定位generation，不能用当前fence epoch替代旧证据。只追加/核对历史receipt并单调合并状态；旧journal不得倒退当前fence、覆盖新process或把原SDK_ACCEPTED全部改UNKNOWN。旧epoch callback无执行权。

## Recovery 与 checkpoint 可见性

legacy inline checkpoint 继续用既有128KiB fact合同；新pause fact不解释为inline payload，按typed metadata +固定trusted captured file验证12MiB内容。读取要使用Windows no-reparse final-handle有界语义；不能简单把原os.ReadFile上限增大。若已接受 bridge未暴露可重用离线安全reader，优先在新windows helper实现同等受限读取；不得扩bridge范围。

重启按追加证据可恢复封存/停止事实，但不能凭artifact存在设置PAUSED_CONFIRMED。ACK存在但无turn.paused/stop proof、partial SDK ledger、UNKNOWN effect均保持RECONCILING。已确认暂停经过租约过期仍停留；无显式有效resume receipt绝不执行。Cancel后保留checkpoint历史贡献，但它不再是可激活恢复点。backup restore产生的restore_fenced永不由本卡清零。

checkpoint保留既有Artifact access_class与readObject/artifactUse权限，禁止新增无鉴权文件读或把raw SDK snapshot塞进普通Task/Session response。API只暴露已有checkpoint artifact引用；本地证据包可检查完整原数据。输入配置变化不能重新计算hash冒充原snapshot。

## 验证合同与交付

新测试名以下为**拟实现**，不是现有执行结果：

- `TestRuntimePauseIntentCAS`：真实HTTP key/hash、samehash replay、changedhash、ETag、请求前后撤销device/Owner/grant。
- `TestRuntimePauseCheckpointCommitOrder`：fact/upload/seal/use/intent/ACK/paused/stop每个cut注入失败；无durable use不ACK；同sequence不双ACK；metadata与12MiB内容分离。
- `TestRuntimePauseSuccessorCAS`：两个RESUME竞态仅一个e+1；中途每次SQL失败回滚Run/carry/activation/fence；Root backup validator验证每次committed revision witness。
- `TestRuntimePauseCancelDominance`：Task/Run/Goal/client CANCEL分别与pause、seal、confirm、resume commit、before native resume竞态；没有后续模型/tool。
- `TestRuntimePauseQueueRestore`：两队列+五种状态混合、cut后新到达、缺/错/重复消费映射、旧journal在新epoch后恢复；保留每条message id/hash/writer epoch。
- `TestRuntimePauseRecovery`：过期暂停不自动跑、PREPARED安全lease replacement只同epoch一次launch、STARTED不明不重跑、backup restore fence阻断。
- `TestProductMuPauseResumeNative`：真实Host产品路径，synthetic provider单独标NATIVE_SYNTHETIC；确认一个真实tool运行中PAUSE、旧进程drain、新进程同Run e+1、两消息恰消费一次，最终响应且tool效果计数不重放。

命令：`go test ./internal/domain -run '^TestRuntimePause' -count=1`；`go test ./internal/host -run '^TestProductMuPauseResumeNative$' -count=1 -args -local-runtime-assets-dir <isolated-assets> -local-runtime-verifier-executable <verified-verifier>`。实际实现后必须记录nonzero test census、无skip、退出码；若fixture需要新flags，先在此既有15文件范围内实现并记录真实命令，不能凭计划命令当pass。再跑受影响的既有Task controls/queue/coordinator/recovery/backup测试，列出确切names。

LIVE模型只在Root已授权的候选Host/既有批准配置可用后执行，单独保存provider receipts/process/artifact/use/queue proof。不足资源只将该支路BLOCKED；NATIVE_SYNTHETIC不等于LIVE。首卡不签phone A10/A11/C17或42正式用例。

提交交付：独立C worktree baseline/status manifest、exact15 diff/commit、dependency freeze hashes、测试原始命令日志与断言census、每次失败保留的attempt ledger、checkpoint/artifact/use/activation/state-receipt映射、native证据、独立review输入。Root取freeze接受后才决定隔离组合归档或集成时机；不将schema25带入普通Main启动。formal_increment=0，formal_cases_accepted=0/42，parent acceptance=false。

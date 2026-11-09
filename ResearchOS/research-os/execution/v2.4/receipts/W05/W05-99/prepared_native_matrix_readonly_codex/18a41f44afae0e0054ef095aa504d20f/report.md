# Native maintenance 隔离执行矩阵（只读源码提取）

本报告不运行 Go/native/Git/SQL/provider，不读取 DPAPI、ExecuteClaim、credential 或 private_resource_ref；不接受原库升级或 ResearchOS 正式用例。现有 native leaf actual 全部通过，但只证明组件；真实 Root→Control inherited-pipe→opaque Token→业务 SQLite 提交尚缺 actual。

路径缩写（以下行号均指实际文件）：
N=D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_native_authority_source_codex/b1599aaf259c435db5a0a5313ab0ea65/candidate-root
M=D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6/candidate-root
W=D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-maintenance-native-52c5a209cfd34eca
A=D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-authority-enrolled-v2-component-root-b0647419338d47ad

## 1. 已读 Source 与 actual

b159 MF 的 20 个 Source、6b0 MF 的 12 个 Source、e841 MF 的 10 个 Source 已逐个核对 sha/bytes，无漂移。e841→6b0 的 prepared migration production 文件保持相同；6b0 增补旧 fixture 适配并调整测试。引用清单和源码显式拒绝条件见 report.json。

A/native-leaf-test.invocation.json actual_native_exit=0，真实 owned PID=86052，creation_time_100ns=134359612709058188，assigned_before_resume=true，Job idle/primary exit/handles_closed=true，errors=[]。外层运行的是 go test ./internal/recoveryauthority，其 Job 关闭不能充当 production maintenance Root 子 Job 的 actual proof。

A/native-leaf-test.stdout.raw sha256=c5df8a1f4cb2977bcb228a7f9360837b2355bee0ddc71f75674bc911378d083f bytes=36518。12 个顶层测试和 20 个子测试均 pass。HMAC positive 用 bytes.Buffer（N/internal/recoveryauthority/native_windows_test.go:18–28），空 bootstrap 拒绝两个 constructor（44–48），其余覆盖 native 文件 deny-write/native birth/DPAPI role/Source inventory。authority_test.go:14–23 的 Adoption 是独立随机 test key + 伪 PID，不构造 Token。M/internal/domain/backup_prepared_abandonment_upgrade_windows_test.go:97–105 的 original apply 仅 MigrationToken{} negative。W/internal/domain/prepared_run_abandonment_windows_test.go:438–449 的 positive 安装 preparedTestAuthority{}，不是 native positive。A/validation.closed.json 自报 formal_acceptance=false。

## 2. 两个唯一 constructor 与实际串接

Adoption：Root 无参数 → RunEnrolledRoot → accepted Control --private-prepared-abandonment → ReceiveInherited（N/internal/recoveryauthority/native_windows.go:179–212）→ openExclusiveRecoveryDB → ExecutePreparedAbandonmentMaintenance（N/internal/domain/prepared_abandonment_authority.go:61–67）→ AbandonPreparedQualification。

Migration：Root 唯一参数 schema23-to24 → RunEnrolledMigrationRoot → accepted Control --private-prepared-schema23-to24 → ReceiveMigrationInherited（N/internal/recoveryauthority/migration_windows.go:25–48）→ canonical LocalUpgradeOptions → openExclusiveRecoveryDB → ExecutePreparedAbandonmentSchemaUpgrade（M/internal/domain/backup_prepared_abandonment_upgrade_windows.go:63–290）。

只有 ReceiveInherited / ReceiveMigrationInherited 返回非零 opaque capability。Release/Grant/Adoption/JSON、ProvisionEnrollmentKey 和 SignEnrollmentDocument 都不能直接 mint Token。两个 purpose、grant schema、固定文件名、nonce journal、Token 类型分离；migration 不调用 adoption signer，不取得 Run 修改授权。

Control 私有分支位于 N/apps/control/main.go:33–37，早于普通 flags、migrate、host/protected store、coordinator/provider/listener。私有 Control args 只能一个固定参数，不接收调用者 paths/options；任何普通 flags 添加都拒绝（prepared_recovery_windows.go:24–28）。DB 路径来自通过原生验证的 grant，不来自环境。单连接 mode=rw，foreign_keys=ON、synchronous=FULL、locking_mode=EXCLUSIVE，BEGIN EXCLUSIVE/COMMIT 获得并保留 SQLite 排他锁（37–48）。

Native Root 测量 PID/FILETIME birth/SID/image hash；Release 把 own Root 与 apps/control buildinfo 路径绑定为 windows/amd64/CGO0/-trimpath（native_windows.go:75–106）。Root 创建 unnamed KILL_ON_JOB_CLOSE Job，子 Control 先阻塞在空匿名 bootstrap pipe，AssignProcessToJobObject + measured image 成功后才写 bootstrap；named pipe 通过 OS client/server PID、birth、SID、image 和 purpose HMAC 双向校验（root_windows.go:58–82；migration_windows.go:72–87；transport_windows.go:57–104）。

Child 再持有全部 source/image/raw pin deny-write guards、真实 Root/DB 文件 ID，取得 DataRootLease 并 Borrow，才返回 Token。Check 重检 live peer/self PID+birth、lease、native file/path IDs 和 guards（native_windows.go:107–117）。当前 Check 没有独立再调用 IsProcessInJob；Job 约束来自 accepted Root 的实际 assign-before-bootstrap 路径，不能把 caller JSON、外层 Go test Job 或仅 any-job membership 写成 inner Job identity proof。DataRootLease 绑定 coordinator.lock，Close 前必须 ReturnBorrow（W/adapters/runtime/data_root_windows.go:24–107）。

## 3. 两类准备入口、private Owner 输入与 fixed siblings

准备入口一：schema23 隔离夹具/backup/rehearsal/migration。
准备入口二：schema24 eligible PREPARED qualification + historical raw closure/adoption。
这是待 Root/Source 作者实施的 helper 行为规格，本报告未创建/运行这些 helper。

两类 helper 的公共部分：
- 新建 Root 专属 case 目录、隔离 data root 和 DB；current Owner 必须真实认证、OWNER role/project grant、authorityRoot(owner.ID)==owner.ID==binding.OwnerRoot。凭证只留内存/既有私有管道，不进 argv/env/stdout/receipt。本报告不查当前凭证路径。
- Native Root exe 的 stdin 必须是真实 Windows PIPE，内容 1..4096 bytes 后关闭 writer 产生 EOF。Root io.ReadAll 等 EOF，再 TrimSpace；普通文件重定向、控制台、Owner CLI flag 都不能替代（N/ops/supervisor/recovery_root/main_windows.go:24–32）。
- Launcher 建真实 anonymous pipe，child 只继承 read handle，Root argv=[RootExe] 或 [RootExe,"schema23-to24"]；parent 在启动后写当前 Owner bytes、close write，再擦除内存，并保持外层 owned Job/PID/birth/actual_exit/cleanup receipts。Go exec.Command + os.Pipe/Stdin 或经审核的 Windows owned-process launcher 均可；不要打印秘密，也不要用 shell 命令字符串拼接 Owner。
- Root 和 Control 如在不同目录，各自 exe sibling 必须有完全同字节的 signed recovery-release.json。最小布局是把 Root、Control 放同一新目录。Release root_image/control_image 必须是最终 exe 绝对路径+sha256:hash+bytes，同 hash 改路径仍需新 release。Release.source_root 是完整 accepted build/source root；不等于 LocalUpgradeOptions.SourceRoot 的 schema23 contract inventory root。
- Issuer DPAPI 由离线 enrollment 工具持有，Root 不读取 issuer key。既有 compiled issuer public anchor必须匹配；新 provision issuer 不会替换 anchor。root-adoption key 的固定 sibling 仅 adoption 需要：root-adoption-signing.dpapi。将其 public key写进 release.root_signing_public_key；migration 的 release 验证仍要求该字段合法，但 migration 不读取 root-adoption DPAPI（root_windows.go:46–47 / migration_windows.go:53–70）。
- 离线工具明确已有入口：enrollmentExe sign-reviewed release|grant|migration-grant <issuer.dpapi> <reviewed-payload.json> <new-signed.json>；源码会校验 issuer 对 compiled anchor、typed canonical payload、purpose 并 CREATE_NEW/Sync（N/ops/supervisor/recovery_enrollment/main_windows.go:19–25；enrollment_windows.go:58–73）。Reviewed payload bytes 的复核在调用前完成；工具不会自动独立审查业务事实。
- Release payload必须 recovery-release.v1 / adoption Purpose，含 id/SID/root_image/control_image/source_root/source_files/root_signing_public_key/not_before_utc/expires_utc（types.go:87–99）。两个 grant 的 release_sha256 都是 signed release wrapper 文件的 raw digest，不是 payload digest。所有 RawPin SHA 带 sha256: 前缀；旧 receipt raw ref 的 SHA 通常不带，转换只加前缀，不能改其 bytes。
- 每个 hostile case 用新的 case 目录、新 release、fresh nonce/grant、自己的 receipt。不要删除 consumed journal 或覆盖固定 signed 文件来重试。被 Root 消费但 child 失败的 grant 同样不得自动 replay。

### 3a. Migration pureDDL 准备

可直接用组合后的实际 ops/backup（W/ops/backup/main.go:76–85）：
backupExe upgrade-local --db <isolated/source23.sqlite> --backup <new encrypted snapshot dir> --out <new isolated restore/rehearsal dir> --key-file <separate 32-byte key file> --source-root <exact23 inventory root> --root <exact24 inventory root> --source-program <this backupExe> --target-program <accepted ControlExe> --plan schema23-to24-prepared-abandonment-v1

该 CLI 不启动 server/worker。source DB、workspace bindings、domain history、current Owner/额外 hostile credential 均先准备，再生成 backup/rehearsal；随后 IssueCredential 会改变 OriginalRows hash，不能在 backup 后补凭证。Key 可由 backup keygen --key-file <new separate key> 创建，不输出 key bytes；本报告不读 key。

SourceProgram 必须是当前实际执行 rehearsal 的 executable；apply TargetProgram 必须是实际正在执行的 Control executable（M/backup_prepared_abandonment_upgrade.go:397–409，windows.go:140–142）。历史 backup23 若未含新 prepared plan，不能生成该演练。实际组合 A 的 backup-build 是候选 rehearsal 程序，A 的 control-build 是候选 TargetProgram；复用前由 Root 复核 build/release 审查范围。单纯把 TargetProgram 指 backup24 会在真实 Control 拒绝。

LocalUpgradeOptions 无 json tags（W/internal/domain/backup_upgrade.go:50–55），typed canonical keys 依次：
Source, Snapshot, Destination, KeyFile, SourceRoot, TargetRoot, SourceProgram, TargetProgram, Plan。
Grant.Options 直接放同一 Go json.Marshal(opt) bytes（不是 quoted JSON string）；不能 sort_keys、加空白或自行改大小写。Control 严格 typed decode 后重新 json.Marshal，比较 digest 及原始 bytes（N/apps/control/prepared_recovery_windows.go:50–59）。

迁移 fixed sibling：current-schema23-to24-grant.json；journal：consumed-schema23-to24-grants/<nonce>.used。Grant：
schema=researchos.recovery-migration-grant.v1
purpose=RESEARCHOS_PREPARED_SCHEMA23_TO24_V1
stage=APPLY_ORIGINAL
release_sha256=<signed recovery-release raw digest>
nonce=<32随机bytes十六进制>
issued_utc/expires_utc（现在有效、窗口<=5分钟且 release 覆盖）
binding={plan_id固定、owner_root、project_id、root、root_identity、database、database_identity、source_release_sha256=<SourceProgram bytes>、target_release_sha256=<Control bytes>、source_inventory_sha256、target_inventory_sha256、source_schema_sha256、target_schema_sha256、sql_sha256固定、original_rows_sha256、options_sha256、backup RawPin、rehearsal RawPin}
options=<typed canonical LocalUpgradeOptions raw>
pins=<以下全部exact RawPins>
（N/internal/recoveryauthority/migration.go:16–71）

必须 pins：
1. source-program / target-program / migration-sql（SQL sha256:1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098）。
2. encrypted-backup-manifest = <Snapshot>/manifest.json；isolated-restore-rehearsal = <Destination>/prepared-abandonment-rehearsal.json，须和 binding 对应 RawPin 完全一致。
3. source-inventory:<relative> 对所有 source inventory项；target-inventory:<relative> 对所有 target inventory项。Source精确23/Target精确24编号 SQL、4 contracts、next_v24_sessions.sql（M/backup_prepared_abandonment_upgrade.go:81–132）；每项路径/digest/bytes都提前纳入 grant。
4. encrypted-backup-payload:<manifest file.Name>.enc 对每个 payload。仅manifest pin不够（M/windows.go:132–149、208–214）。
5. 用于独立审查的 original IO/public refs 另作 grant pins；源码不是固定单一 IO role检查，不能声称源码替 Root 证明 original IO 全覆盖。

Backup/rehearsal所有 hashes及 Source23/Original24/Restored23/Restored24 四 schema hashes来自真实演练 receipt；不得把 restored schema/hash 当原DB schema/hash。无 protected artifacts 的合格隔离夹具可以不依赖 FrozenService：W/backup_queue_upgrade.go:492–495 正常分支直接return；有 protected refs 时仍要求真实服务，不能伪造 READY/frozen summary。

Apply child确认 rawoptions/pins/release/program/schema/backuppurpose/decrypted backup/rehearsal/current logical rows后，写新的 <Destination>.original-schema24/migration-intent.json；原SQLite tx下 authenticate当前Owner/directRoot，token.Begin，固定0024 DDL，旧所有table columns/typed row multisets完全保持、唯一新增proof空表及version24、schema/integrity/FK checks，native/pin复核后 Commit（M/windows.go:223–290；core.go:239–307）。成功 status=SCHEMA24_COMMITTED_ORIGINAL_BUSINESS_ROWS_UNCHANGED。它不运行 restore/reconcile、不改Run/Task/dispatch、auth revocation、不计费用、不做abandonment。任何 Commit error status=COMMIT_OUTCOME_UNKNOWN、token保守消费、留immutable intent，不能自动重放。

### 3b. Adoption proof 准备

先由独立接受的 schema24 fixture提供 exact expired QUEUED qualification Run、RUNNING runtime_qualification Task、唯一immutable qualification marker、PREPARED dispatch和封存profile upload。可复用 W/prepared_run_abandonment_windows_test.go:275–338 的公共业务步骤（runtime registration →真实Executor/Scheduler credential →Executor content upload/sealed Artifact →Goal/Task/context bundle →RegisterRuntimeQualificationPlan →BeginRuntimeQualification），但只复用夹具数据构造；不要安装 preparedTestAuthority{}。以 actual DB 当前修订/epoch/dispatch key/manifest hash构造 Grant.Tuple。准备后关闭 fixture coordinator/HTTP/DB，把 lease交给 accepted Control；不要让 coordinator Loop 启动 worker。

固定 sibling：current-adoption-grant.json；root-adoption-signing.dpapi；journal consumed-adoption-grants/<nonce>.used。Grant字段见 N/types.go:100–113；schema=researchos.recovery-grant.v1，purpose=RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1，root/native root_identity/database/native database_identity、Tuple完整、fresh nonce≤5min、signed release wrapper SHA、下面rawpins。不要手写 Adoption JSON或历史签名；accepted Root根据真实历史raw产生当前签名，Child重读原raw并比较。

旧raw的 minimum 16 roles（N/history.go:12）：
original-authority, clock, once, go, contract, probe, lifecycle, invoke-admit, invoke-execute, stdout-admit, stderr-admit, stdout-execute, stderr-execute, source-manifest, binary-host, original-tool-io。
还必须追加 go.execution_authority_ref、go.coordinator_source_ref 和 lifecycle.source_guard_cleanup[].entries[] 中每一原 guard ref（全closure，不止source-manifest摘要）。role与path都不能重复；允许0byte streams，其他 raw sha/bytes要真实。对应文件若已占16roles之一，不要为同path重复新增role。

Root history严格字段需求（history.go:23–79）：
- clock.started_utc/deadline_utc RFC3339Nano，deadline=started+300秒且已过期；clock_reset_permitted=false；once.state=CONSUMED_FOR_HOST_GO，qualification_run_id=Tuple.RunID。
- go.qualification_run_id同Run，go.started_utc同clock；execution_authority_ref/coordinator_source_ref ={path,sha256无前缀,bytes}须被当前pins覆盖。
- lifecycle.state=FAILED_EXECUTION_CLOSED、error非空、go_sent=true、actual_parent_pid=held_identity.owner_pid、provider_requests=null、automatic_retry=false。
- source_guard_cleanup非空；每项closed=true、verification=PASSED、share_mode=FILE_SHARE_READ_ONLY、retained_handles_count=0、errors=[]；entries非空且每ref verified/final_path_match/closed=true，path/hash/bytes exact pin。
- contract.held_identity与probe.held_identity逐字段canonical一致；held captured_before_resume/held_job_handle/held_primary_handle=true；probe captured_before_resume/in_job/descendant_of_root/direct_CreateProcess_from_root/actual_IsProcessInJob_return=true。
- contract/probe root_pid与once.owner_pid同held.owner_pid；contract/probe host_pid同held.runner_pid；root_job_id同held.job_binding_id；contract.deadline_utc同clock。
- lifecycle.jobs恰好两项且labels唯一 host-admit-only、host-execute-admitted。每 cleanup.closed=true；proof captured_before_resume/held_job_handle/held_primary_handle/primary_exit_confirmed/pid_match/creation_match=true、active_processes=0、errors=[]；watchdog duplicate_handle_closed=true/errors=[]；producer closed/job_handle_closed/primary_handle_closed=true/errors=[]，producer run_uuid/owner_pid与proof一致，proof.owner_pid同held。
- invoke-{admit,execute}.result owned_child_pid/creation_time_100ns/actual_exit及顶层 native_exit对应proof；resumed=true；job_cleanup assigned_before_resume/unnamed_exclusive_job/kill_on_job_close_configured/job_idle_confirmed/primary_exit_confirmed/handles_closed=true、active_processes_last_observed=0、errors=[]。stdout_ref/stderr_ref sha/bytes实际对应角色的 raw bytes。
- execute proof run_uuid/job_binding_id/owner_pid/runner_pid/creation_time_100ns同held；primary_exit_code=1，invoke-execute.error非空且stderr-execute非空。proof.observed_monotonic保留JSON number原字符串。held creation_time_100ns保留无损数字串，不能JSON double往返。
- old original_root_signature、exact_job_closed_utc、provider_requests、actual_cost保持null，financial_closed=false；Root只签当前adoption，不补造旧绝对时间、费用0或旧signature。

若用既有真实历史 raw，其 RunID必须和隔离DB Tuple一致（history.go:32/35），应从可信隔离副本保持原business IDs，或生成同一隔离Run对应的真实原native历史。拿随机新Run的 preparedFixture+旧raw会拒绝。history_test.go 的伪raw仅能作为标注的 parser fixture，不能宣称真实历史Job closure已发生或替正式原库acceptance。fixture credential和元数据公开程度由Root现有权限处理，本报告不读取原DB或credential。

Adoption child要求db main path exact、无attached DB、version24且exclusive（N/domain/prepared_abandonment_authority.go:40–56），token.Begin后 currentOWNER/directRoot+exactCAS在resourceWriteLock tx中复核。必须满足 Run/Task/epoch/revision/expired lease/marker全部相同；dispatch无worker/journal/identity/observation/reason；profile artifact/plan/contract/input/context/runtime/current binding/hash/sealedtime/size/upload完全一致。12类运行/队列/上传/产物/effect/billing/approval footprint都为0，唯一允许封存profile preparation upload（N/domain/prepared_run_abandonment.go:104–191、197–285）。成功只把Run/Task bump→FAILED，append两event及immutable runtime_prepared_abandonments proof；dispatch保持PREPARED、成本/requests null、financial_closed=0、无settlement或retry（287–312）。

## 4. 最小真实执行矩阵

每case native执行前记录合格baseline，negative要求指定拒绝层/消息及logical DB/schema前后相同，不能只接受任意非零exit。所有case保存actual PID/birth/image/Job membership、真实nativeexit、完整public stdout/stderr refs、closed/idle proof；false/unknown事实不改成0/成功。新机械失败先由Root分配全局ordinal，不重置/自动retry。源合法拒绝的negative是否计失败以Root正式receipt分类为准，不能自行当机械失败。

| ID | 真执行动作 | 必须证据/预期 |
| --- | --- | --- |
| P-M0 | 合格schema23夹具→真实backup upgrade-local encrypted backup+isolated restore/DDL rollback/reapply | 原fixture schema23/全部logical rows不变；restore copy有独立reconcile/auth revocation delta；receipt Original24与Restored24分别绑定。 |
| P-M1 | fresh reviewed signedrelease+完整 migration-grant，privateOwner PIPE→真实Root schema23-to24→accepted Control | 非零MigrationToken；SCHEMA24_COMMITTED_ORIGINAL_BUSINESS_ROWS_UNCHANGED；恰version24+新proof空表，旧rows逐table/type hash相同，credentials/QUEUED/PREPARED保持。 |
| N-M1 | 同 P-M1 合格bindings，但privatestdin交真实Executor/过期/已撤销credential（在backup前准备） | 真管道和MigrationToken成功，拒绝当前Owner/directRoot；原rows/schema23不变。 |
| N-M2 | grant保留5必需roles，但遗漏一source-inventory动态pin或payload pin | Root→Control真实继承，构造非零MigrationToken后RequirePin拒绝；无DDL。 |
| N-M3 | 完整reviewed grant后原fixture正常变动导致OriginalRows或schema drift | 真token路线后精确 PREPARED_UPGRADE_ORIGINAL_DRIFT / SOURCE_SCHEMA；原变化后的baseline保持。 |
| N-L1 | 另一真实lease进程持有相同case coordinator.lock，然后正常Root发真实frame | Child lease Acquire失败，未打开mutationDB；lease释放后不得同nonce自动retry。 |
| P-A1 | 合格schema24 eligible tuple+对应真实history closure+fresh adoption grant+privateOwner PIPE | 非零Token，Run/Task FAILED、一proof两events，dispatch历史PREPARED/profile bytes保持，无financial closure/provider retry。 |
| N-A1 | 合格adoption grant后仅改变合法当前Run/Task revision/lease/started或dispatch fence | 真Token下 exact CAS/fence层拒绝；故障注入后的baseline不再变。 |
| N-A2 | 合格eligible fixture中只加入一种 runtime/effect/queue/upload/billing footprint | 真Token下 footprint guard拒绝，proof/event未新增；禁止删除触发器造case。 |
| N-A3 | current privateOwner改为真实Executor/delegated/nonprojectOwner | native构造后currentOwner/directRoot拒绝，DB无额外修改。 |
| N-P0 | accepted Control公开调用两个private参数/额外flags，或Root非PIPEstdin | beforeDB拒绝 AUTHORITY_PRIVATE_INHERITANCE_REQUIRED / fixed args / PIPE校验。此case单独不证明真实继承negative。 |
| N-P1 | 新case reviewedrelease有错issuer/过期/错误imagepath/hash/SID/Source遗漏，或native root/DBID错 | 指定Root/Child原生拒绝、native/noDBwrites；每fault独立case，不能用未reviewed授权泛化。 |
| N-R1 | P-M1/P-A1 后再次调用同signed grant | CREATE_NEW consumed nonce拒绝；不删除journal；先前数据库状态不变。 |
| N-K1 | 让Control停在外部竞争SQLite排他锁，真实Root已发bootstrap且Control仍未mutation，杀死ownedRoot | KILL_ON_JOB_CLOSE/child实际退出+outerJob idle/handlesclosed，DB未DDL/abandon；安全barrier必须实际确认，不能凭sleep猜时序。 |

Cross-purpose signature/HMAC、wrong-peer、bad frame size 已有 parser/Buffer leaf coverage；要补“真实继承管道到对应拒绝层”的 hostile 必须新专门helper，否则伪parent会先在acceptedImage被拒绝，无法证明wrong-MAC层。Commit outcome unknown/Result lost后的独立schema inspection也需新实际fault harness，不能从当前successfulleaf推断。

## 5. 确切 helper 缺口与可复用边界

已有可复用：offline sign-reviewed/provision、真实ops/backup CLI、两个固定Root→Control production流程、schema23 fixture builder/public业务steps、typed row/schema/integrity invariants。它们无需开放Token setter/测试认可键/普通HTTP recovery route。

缺口1：持久或在test进程活着期间可交接的隔离fixture builder，输出公开exact tuple/root/dbID/row/schema/inventory/options/pin refs，当前 Owner 仅私有pipe；关闭自己的coordinator/DB lease。t.TempDir退出会清理，不能让Root后续阶段指向已删除的fixture。

缺口2：Go typed payload compiler（Release/Grant/MigrationGrant/LocalUpgradeOptions），计算source/target完整inventory及每encrypted payload rawpin，实际Windows native fileIDs/SID测量、strict json.Marshal，固定sibling的CREATE_NEW签名部署。不能用generic JSON重新序列化已签payload。后加ops/internal helper文件会触发sourceGuards fulltree覆盖，应在final inventory/build seal之前冻结。

缺口3：真实owned launcher给Root stdin anonymousPIPE，所有子进程actual PID+birth/killclose/cleanup guard证据；内层Root Job当前源码未输出public native proof，可由新受审查observer/instrumented test harness记录真实调用和exactJob membership，不能将outerGoTestJob冒充。任何新instrumentation意味着新Source/build/release复核，不能覆盖b159 sealedSource。

缺口4：两个purpose各自的规范negative cases+指定层断言；缓冲区MAC/伪signature/zeroToken只保留组件scope。wrongMAC/peer after acceptedImage、native token state复制/oneuse/Close-inflight、Rootdeath精确barrier、commit-outcome/lost-result需要独立helper或新的受审查Source instrument，不存在无需核对的现成positivehelper。

本只读任务新增机械失败791：长内联封存命令在CreateProcess前因Windows os206被拒绝，outer/Python/native exit均NULL、无进程/写入；完整request/error保存在failure-origin.791.json。Root已分配791并批准改为静态文件+短校验命令；不重置/no auto retry。未改canonical/Source/已有失败计数、未运行native/Go/SQL。报告只供Root继续实施，所有22父任务/42正式用例及原库授权/接受仍由Root按原合同推进。

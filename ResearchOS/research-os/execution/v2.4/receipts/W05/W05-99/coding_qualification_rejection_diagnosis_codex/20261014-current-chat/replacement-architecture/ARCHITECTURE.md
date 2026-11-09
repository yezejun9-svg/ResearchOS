# 正式 Runtime Verifier Replacement：可登记架构

结论：使用 Windows 本地管理 CLI 的独立早分支，在同一个现有 DataRootLease 下完成只读预检与一个私有注册文件的替换。保留 `ensureRuntimeVerifier` 对不一致记录的原拒绝。正常 Core 启动须在取得 lease 后、打开数据库前拒绝未完成的替换日志，防止“文件已换、事务未完成”被误认为完成。

本说明基于 Main `c8b7adab9f0c15eb33f235f8d0d9eb205794e376` 的固定 git blobs；其 Core 发布基线为 `a7ec7ebf2d53848ea163b6115667b3e3761a6bd2`。这是可实施方案，不是实现、测试通过或产品接受。旧组合复用不在此方案内。本轮没有读取产品数据库、执行产品、GUI、模型调用、CONFIRM 或写入 Source/checkpoint。

## 1. 已核实的复用点与不能直接复用的入口

| 固定源码位置 | 已有行为 | 本方案用法 |
|---|---|---|
| `apps/control/main.go:35`、`prepared_recovery_windows.go:22` | 私有维护先于 flag.Parse、store.Open、迁移、Host、监听器和 coordinator | 新 replacement 早分支；不能让新参数落入正常启动，也不借用 recoveryauthority 的继承授权协议 |
| `main.go:100`、`adapters/runtime/data_root_windows.go:24`、`bridge_windows.go:165` | 当前协调器终身持有排他的非继承 coordinator.lock；拒绝 reparse DataRoot | 各 replacement 动作取得同一 lease；活动 Core 存在时立即拒绝；不得自动 kill/restart |
| `internal/host/host.go:107,191,198` | New 会建立私有目录、打开 vault/roots/selections 并调用 NewCurrentMu；InstanceID 使用 host 路径与 OS principal ref；writePrivate 使用 temp/Sync/DACL/Rename | 不调用 New。只建立经验证的只读身份视图；保留 InstanceID 完全相同的算法与原 host 路径。writePrivate 不是 CAS/事务日志，不能直接用于替换提交 |
| `internal/host/state.go:15,28`、`client_configuration.go:13`、`bootstrap.go:149,184`、`internal/auth/identity.go:33` | host_state 与当前 Windows SID-derived ref、HostInstanceID、bound principal 绑定；Owner 来自 auth_principals；每次特权动作重验 OS identity | 新入口严格读取已存在的 state，不接受“缺失即空”；可构造包内最小 Host 只读视图并调用 ConfigurationMetadata(ref=nil)，另在 readonly DB 核对 active Owner。不得调用 BootstrapOwner/issue/revoke |
| `internal/host/runtime_qualification_windows.go:70-154` | 注册 schema、root/child 派生、Owner/VERIFIER roles/grants/lineage，以及整条记录不匹配拒绝 | 复用类型/哈希/派生公式，只读核对已注册 root 和所有现有 child；不创建 principal、grant、identity、不改变 root |
| `runtime_verifier_process_windows.go:38-113` | 安装 manifest 有严格 JSON、固定 service/protocol、空 args、40位 commit、绝对无重定向资源路径、实际 exe bytes digest | 直接复用 loader/validator；另加 manifest/注册/state/journal 的 current-SID owner 与 protected DACL 读回检查；不启动 verifier |
| `runtime_qualification_windows.go:46`、`private_windows.go` | 有严格单 ACE protected request ACL 比较及私有文件/目录 DACL 设置 | 对新记录/日志强制应用并读回；现有文件 ACL 不做静默修复。owner SID 必须另读，原 helper 只比较 DACL |
| `internal/host/workspace_write_windows.go:210,575,614,658` | immutable 私有文件、目录 native guards、目标 handle、ReplaceFileW 实际 backup；并发 rename 时保留双方且 UNKNOWN | 在同 package 复用 `writeImmutablePrivate`、`guardWriteDirectories`/close、`openWriteTarget`/guarded read、`callReplaceFile` 等小原语。不要直接把完整 workspace command/intent API 当注册管理 API |
| `ops/supervisor/release_journal_windows.go:139,203,241,533` | sequence/previous/hash 追加链；Sync；descriptor 为快视图；MoveFileEx write-through | 复用设计，不实例化 ReleaseJournal，不共用 supervisor 状态、权限或恢复语义。采用不可变事件文件，避免把不完整 JSONL 尾部当作成功 |
| `internal/domain/runtime_qualification_confirmation_windows.go:166-182,260-264` | 3 项全局未结算门与 managed qualification 幂等声明未结算门 | 新只读 helper 在单个 readonly transaction 中镜像这 4 项谓词，无 Recover/Scan/Execute |
| `runtime_drain_windows.go:32-47` | 只读 drain SQL；还含命令、预算等计数 | 可参考；不要把未连接 coordinator 的 ActiveWorkers=0 当成实测，也不要因已结算 UNKNOWN-cost ledger 增加新的拒绝门 |
| `internal/store/sqlite.go:17-43`、`prepared_recovery_windows.go:41` | store.Open 设置 WAL 等；exclusive recovery opener 设 exclusive lock 并 BEGIN/COMMIT | 不直接复用。新连接用已有 SQLite driver，URI mode=ro、query_only=ON，单连接 BEGIN/ROLLBACK；不执行 migration/bootstrap/checkpoint/VACUUM/DDL/DML |

固定源码未找到名为 `nativeOwner` 的通用函数。这里的 native owner 是真实 token SID + 已有 host_state/Owner 绑定及 DataRoot 的排他 OS handle，不能假称有一个可直接复用的 `nativeOwner()`。

## 2. 本地 OS 权限与修改边界

这是现有本地产品管理权限：调用者必须是原 Host 绑定的 Windows SID，拥有原私有 host 目录与文件访问权。Root 指当前协调 Agent，不是 Unix root，也不要求另外提升为 Windows Administrator。其他管理员账号的 SID 不自动获得此产品 Owner 身份；不添加外部签字、在线审批、用户 token、隐藏环境开关或继承 capability 要求。

CLI 输入只有绝对 DataRoot、固定本地 manifest、哈希、operation ID 和 plan 路径。旧 Owner、Host、service root 从现有状态导出，不允许通过参数改写。stdout 只输出状态、哈希、路径、必要身份引用和计数；不输出 host_state 原文、credential、DPAPI、token、API key 或私有帧。

允许提交的产品写入只有 `host/runtime-verifier-installation.json`，以及新的 `host/runtime-verifier-replacements/<operation-id>/` 私有审计目录。lease 使用已有 coordinator.lock。不得修改 DB、host_state、vault、selection/root registry、旧 qualification/request/idempotency、coding profile/config revision、模型 reference、预算或旧审查证据。预检仅输出用户指定位置的 plan；不创建 host journal。任何新目录/文件在私有父目录中创建、落盘前设置 ACL，落盘后再核对 owner/DACL。

DataRoot/host/DB/state/注册文件必须已存在、绝对规范路径、本地普通对象、无 junction/symlink/reparse 重定向；先校验存在再 AcquireDataRootLease，防止已有 LockDataRoot 的 MkdirAll 产生一个新产品目录。打开目录 guard，绑定 Windows file ID/volume 与 DataRoot/DB/Host 路径，持有至动作完成。不得复制旧 data 到另一目录冒充原 host。

## 3. 建议 CLI 合同（待实现，禁止现在调用）

独立 dispatcher 仅当首参数恰为 `--runtime-verifier-replacement` 时处理，其余通过私有 FlagSet 解析。重复参数、未知参数、余留位置参数、混入 `--desktop-management-stdio`/bootstrap/import/provision/trial/coordinator/qualification 参数均拒绝；不能进入正常 main 后续。

```text
control.exe --runtime-verifier-replacement preflight
  --data-root <absolute-existing-data-root>
  --manifest <absolute-new-installed-manifest>
  --expect-record-sha256 <sha256:exact-old-registration-file-bytes>
  --expect-manifest-sha256 <sha256:exact-new-manifest-file-bytes>
  --operation-id <32-lowercase-hex>
  --out <absolute-new-plan-json>

control.exe --runtime-verifier-replacement commit
  --data-root <same-absolute-data-root>
  --plan <absolute-plan-json>
  --expect-plan-sha256 <sha256:exact-plan-file-bytes>

control.exe --runtime-verifier-replacement recover
  --data-root <same-absolute-data-root>
  --operation-id <same-id>
  --plan <absolute-existing-preflight-plan-json>
  --expect-plan-sha256 <same-exact-plan-digest>
  --action inspect|complete|abort
```

`inspect` 只读；`complete` 仅补记已经确定发生的同一替换结果，不重新调用 ReplaceFile；`abort` 仅在当前仍为精确旧记录且不存在已发布/外部竞态证据时补记 ABORTED。不接受 `--force`、`--reset`、忽略哈希、删除旧注册或清空日志。所有动作都要求 lease；即使 inspect 也不跨活动 Core 观察不稳定事务。

stdout JSON 统一包含 schema/action/operation_id/state/plan_sha256/old_record_sha256/new_record_sha256/registration_hash/installation_hash/readonly_census；错误包含稳定 error_code 与 outcome=`NOT_APPLIED|UNKNOWN|APPLIED`。成功退出 0；其他返回非零且不启动普通 Core。APPLIED 只有 COMMITTED terminal receipt 成功落盘且注册+ACL 读回符合时返回；UNKNOWN 永远要求相同 operation 的 recover。

preflight 的 `--out` 必须不存在，且不得指向产品 DB/host/source/package 内已有文件。不要覆盖旧计划。plan 不是外部审批证书：它是当前 SID 明确指向旧→新转换的可检查请求；commit 重新核对全部条件。

计划至少包含：schema/version、operation ID、created_at、canonical DataRoot/host/DB file identity、OS principal ref、Host ID、Owner principal、service root、旧注册原始 bytes digest 与 canonical record hash、旧 installation hash；新 manifest path/raw digest、经过 strict decoder 的安装值及安装 hash、实际 exe path/hash、候选注册精确 bytes/digest；仅允许改变的 installation executable/executable_hash/source_commit，Owner/Host/root/schema/service/protocol/arguments 保持原值；readonly DB schema version 和四项 census、identity/lineage digest；可选 rollback_of；plan 不包含任何 credential 或整库数据。

必须区分三个 digest：`record_sha256` 是原始注册文件字节；`registration_hash` 是 `domain.Hash(runtimeVerifierRegistration)`；`installation_hash` 是 `domain.Hash(RuntimeVerifierInstallation)`。不能用 canonical hash 冒充字节 CAS。本次旧诊断的 canonical record hash 不可直接填入 expect-record-sha256。

## 4. 只读身份与全局空闲核对

连接要求 `file:<absolute-db>?mode=ro`、单连接、`PRAGMA query_only=ON` 并读回；有界 busy timeout；BEGIN 固定 snapshot，最后 ROLLBACK。query_only/事务控制不是产品 DML。SQLite WAL/SHM 的文件系统行为应单列观察，不能用“逻辑只读”推断所有辅助文件字节不变。不存在、表缺失、schema 不支持、坏 JSON、查询失败全部拒绝，不创建或升级表。当前目标为 schema 24；兼容范围只接受构建实际明确支持的 schema，不趁此接入其他 schema 分支。

1. 当前 `auth.Current()` 为 WINDOWS_SID；state version=1，principal_ref 与 fresh ref 一致，HostInstanceID 与现有 InstanceID 算法一致；bound owner 非空。
2. 唯一未撤销 OWNER 与 state principal_id 一致；Owner lineage 存在且与 service root 不同。旧注册 Owner/Host 必须逐项匹配；service root 按当前派生算法重算，不接受任意 root。
3. root 是未撤销且不能 create_project 的仅 VERIFIER、无 grants；root 的 orchestration root=self、parent=NULL。枚举该 root 下已有 child，核对仅 VERIFIER、不可 create_project、单个既有 project grant、派生 child ID、root/parent 与 root 相符。缺失/额外/漂移拒绝，不修复、不创建 lineage。不得检查一个 project 后遗漏同 service root 的其他 children。
4. 在一个只读事务里执行与固定资格入口相同的 4 类 census：所有非 SETTLED/FAILED/CANCELLED Run；每 effect_key 最新序列 PREPARED/STARTED/UNKNOWN；runtime_dispatches PREPARED/STARTED/UNKNOWN；`host:managed-runtime-qualification` idempotency 声明缺失 Run/Run 未终止/相关 unresolved dispatch 或最新 effect。任一非零拒绝。已到期但未消费的 prepared request 不属于已执行工作，不重置或删除。
5. 不把已结算 UNKNOWN-cost ledger 作为替换资格的新门，也不清理它。若额外读取 command/预算计数，仅标注观察；不得冒充现有四项授权门。没有 coordinator 实例，不声称检查过内存 active worker map；排他 lease + 原协议未结算事实是边界，外来不遵守该 lock 的同 SID 程序不是隔离保证。
6. commit 在持有 lease/guards 后重新核对身份、schema/census、plan、manifest、exe、旧注册原始与 canonical hash。preflight 成功不保证稍后 commit 成功；计划变旧、复用 ID 改内容或输入漂移都拒绝。

## 5. CAS、日志与崩溃一致性

注册记录 schema 保持 v1；不添加能被旧 ensure 忽略的新字段。旧→新记录仅更新允许的三个 installation 字段并重新计算 installation_hash；候选 JSON 原始字节在 plan 中确定，并使用现有 writePrivate 相同的 json.MarshalIndent 格式（无额外换行），确保正常 ensure 再次写相同记录不会造成假字节漂移。

CAS 定义为：同一 DataRootLease 串行化所有产品写者，发布前按精确旧字节核对，并检查 ReplaceFileW 实际移走的 backup 与旧 hash 一致，再读回新记录/身份/ACL。这是产品写者的逻辑 CAS，不是 Windows 提供按哈希条件执行的原子 syscall。现有 `TestWorkspaceWriteExternalRenameRacePreservesBothImages` 明确证明，同 SID 的外部 rename 可以在最终间隙发生；实际 backup 不等于计划旧字节必须 UNKNOWN，保留原 preimage、外部 backup、新候选，不能宣称“没有改过”或自动覆盖回去。

建议私有事务目录：`host/runtime-verifier-replacements/<id>/`，包含 immutable plan、old-registration.bin、new-registration.bin、stage 与 ReplaceFile 的 actual-backup，以及按 sequence/previous/hash 绑定的不可变完整事件 `0001-prepared.json`、`0002-publishing.json`、`0003-committed.json`（恢复可能追加不同 terminal 事件）。事件采用同目录 temp + Sync + protected ACL + 不覆盖的 write-through rename + 读回；已经存在且字节相同可视为同一事件，内容不同拒绝。不重写旧事件、不以可变 active.json 作为唯一事实。暂存与 orphan 也不静默删除历史；recover 解释它们，非证据临时文件可在确认安全后清理。若进程恰在建立 operation 目录后、首次 plan 发布前死亡，recover 必须使用显式 --plan 与 digest 校验的原预检计划，确认目录身份、当前精确 old、没有任何发布/backup 证据，才补记同计划的 ABORTED；不得留下没有可执行恢复路径的空目录。无法解释的残留保持 UNKNOWN。

顺序：

- 验证所有前提并校验不存在其他 nonterminal operation；创建私有 operation 目录与 immutable plan/old/new snapshot，读回确认；写 PREPARED。
- 创建同卷 stage，写完整 new bytes、Sync、privateFile、owner/DACL 读回；再验旧记录/身份/manifest/exe/空闲；写 PUBLISHING 并同步。
- 持有 root/parent guards 和合适 target handle，调用现有 ReplaceFileW 原语，指定本 operation 内唯一 actual-backup。失败即 UNKNOWN，不盲目再试，不把失败当 NOT_APPLIED。
- 核对 actual-backup=old raw hash，当前 target=new raw hash，strict decode 与 canonical hashes，file identity/owner/protected DACL；必要的文件 Flush/Sync 必须显式检查错误。追加 COMMITTED 事件并持久化、再读回，才返回 APPLIED。

`writePrivate` 的 os.Rename 不记录原始替换对象；`MoveFileEx(REPLACE_EXISTING)` 没有 conditional hash 语义；二者不能单独实现这个合同。Power-loss durability 不能仅凭用了 Sync 或注释写成已证实。首轮验收必须有真实 Windows 进程终止的 crash 恢复证明；机器断电/存储硬件持久性不在该证据覆盖范围。

正常 main 在 AcquireDataRootLease 成功后、store.Open 前调用只读 startup gate：journal root 不存在为旧安装兼容；存在则要求全部 operation 完整且 terminal，并验证 chain/schema/plan/record linkage。最新已提交 operation 的目标记录必须与当前注册一致；历史 operation 不得逐个要求当前仍等于各自旧目标。任何 unfinished、malformed、multiple divergent terminal、pending temp/orphan 无法解释或状态不明均拒绝普通启动并报 recover 指令。不自动完成、回滚或改 DB。

| 最后完整事件 / 文件观察 | recover 行为 | 普通启动 |
|---|---|---|
| 未建 operation | 无事务 | 按原行为 |
| 仅 plan/snapshot 或 PREPARED；target 精确 old；无实际替换证据 | inspect 报 NOT_APPLIED；abort 追加 ABORTED，保留资料。若要重做，新的显式 plan/ID | abort 前拒绝 |
| PUBLISHING；target=new，actual-backup=old，plan/ACL/identity 都匹配 | complete 追加 COMMITTED，绝不重复 ReplaceFile | complete 前拒绝 |
| PUBLISHING；target=old，stage=new，未出现 actual-backup、没有发布证据 | inspect 报可中止；abort 只记录 NOT_APPLIED，不重放 | abort 前拒绝 |
| target/backup 为第三种字节、丢失、ACL 漂移或部分 API 失败 | UNKNOWN，保留全部材料；complete/abort 均不得猜测。需另行有界修复方案 | 拒绝 |
| COMMITTED 全部证据匹配 | inspect/repeated commit 返回已有同一 receipt；无第二次替换 | 允许 |
| ABORTED target 仍 old | repeated abort 返回已有 receipt | 允许 |
| same ID + 不同 plan、旧期 journal 或 chain 损坏 | CONFLICT/CORRUPT；不覆盖、不删除 | 拒绝 |

回滚必须是新 operation：preflight 指定旧 manifest、expect-record=new current raw SHA、`--rollback-of <committed-id>`，验证当前转换确为该已提交事务的反向，旧 executable 此时实际仍匹配 hash；随后用相同 commit 流程。不能把 recover 当成任意回滚，不能恢复“旧注册文件”同时撤销任何旧 Run/消费记录/credential/qualification。新事务会追加历史，不重置旧事务。若注册后来又被正式替换，原反向计划因 CAS 失效拒绝。

## 6. exact 文件范围

登记文件为同目录 `exact-scope.json` 的 8 项：main.go 一项修改、3 项 control 平台/测试新文件、4 项 host 实现/日志/测试新文件。无需修改现有 ensure、workspace writer、domain、数据库 schema、contract、verifier binary、Desktop、依赖。无包外 API/Native3/HTTP/renderer 操作。

若 builder 发现某个小原语不适配，先在上述新文件内适配；需要改变现有底层 helper 或增加第九个 source 文件时，回报 Root 扩展 exact scope，不能静默改 unrelated 文件。这是任务范围登记规则，不是新增外部审批。

## 7. 最小验证矩阵与证据分层

| 组 | 必须证明的行为 | 最小方法 |
|---|---|---|
| CLI 真入口 | preflight/commit/recover 走早分支；所有混合/未知/重复 flag 拒绝；非 Windows fail closed；缺 web/dist/runtime assets 不触发正常启动 | 编译实际 control；子进程调用；监听/worker/provider 均零，DB logical fingerprint 不变 |
| lease/路径 | 活动 lease 拒绝；关闭后唯一成功；另一 replacement 同时进入拒绝；缺 root/DB/state/registry 不创建；reparse/junction/relative/alias/UNC 拒绝 | Windows OS handle 与真实临时 junction fixtures；不操作产品 DataRoot |
| 权限 | 原 SID 正确；state ref/Host/Owner 不符、revoked、多 Owner、root/child/grants/lineage 漂移拒绝；ACL inherited/额外 ACE/外国 owner/null DACL 拒绝 | 独立临时 fixture，逐项负例；实际 owner/DACL 读回；不把同 SID Agent 算安全隔离 |
| 输入/plan | duplicate keys/unknown fields/trailing data/oversize/bad commit/bad service/protocol/nonempty args/manifest drift/exe drift/old raw hash drift/计划改字节拒绝 | loader 实测；fixture PE/实际固定 verifier仅作字节验证，不启动 verifier |
| census | 四类分别注入（包括别的 project），任一拒绝且数据不变；缺 Run 的 consumed idempotency 拒绝；过期未消费 request 保留且可预检；settled UNKNOWN cost 保留且不新增 blocker | 单事务 readonly queries；schema 缺失/版本漂移拒绝、无迁移 |
| 正常转换 | old→new 仅三字段+installation_hash；root/grants/Owner/state/vault/DB/旧 evidence 不变；actual backup=old、after=new、ACL通过、terminal journal；重复相同 commit 不二次替换 | 全文件/逻辑 DB 前后白名单 diff；真实 ReplaceFile + readonly hashes |
| stale/CAS/race | 两计划同 old，第一成功第二拒绝；same ID different plan 拒绝；外部 rename 间隙保留 actual backup+original+candidate，UNKNOWN，启动拒绝 | 真实 Windows 竞态 seam；禁止静默重放/自动 rollback |
| crash/recover | kill 在 snapshot/PREPARED/stage/PUBLISHING/ReplaceFile后/COMMITTED前/COMMITTED后；old与new所有可证明状态按表处理；partial/third value拒绝；complete不再 ReplaceFile | 实际隐藏子进程终止；每一边界独立重开、inspect/recover/normal startup，记录调用计数与 native exit |
| rollback | 新 operation 反向；old exe验证；历史不覆写；stale current拒绝；rollback 不触及 Run/idempotency/ledger | 相同真实文件事务 fixtures |
| 原拒绝回归 | 未替换时 old registration/new install 继续命中现有 mismatch；替换后同 exact new install 接受原 gate，changed installation仍拒绝；pending journal 普通 Core 在 DB 前拒绝 | 直接 existing gate fixture + 实际 normal control startup 子进程；不能只测 helper |
| 无启动副作用 | preflight/replacement/recover 全程模型/verifier/worker/HTTP/native listener/qualification 新 request/CONFIRM=0 | 子进程观察、fixture provider counter、DB logical fingerprints；不以 grep 代替行为证据 |

推荐在 Root 登记后交给独立 builder 于 clean c8b7adab worktree 实施。builder 运行新增有意义测试与受影响既有 suite（至少 apps/control、internal/host，已有 managed qualification/root revocation/Desktop management synthetic regression）；保留 Go 1.27.1 与依赖 pin。不能用测试名过滤产生零测试 PASS；报告实际测试数、native exit、fixture/真实产品的区别。此 reviewer 不写 source、不自审 builder 接受。

源码接受后 Root 另登记实际新 Core/旧 verifier/新 Desktop package 的精确组合与 build inputs，独立复核实际包，不把架构文档当 compatibility acceptance。新 CLI 应由同一待正常重开的 Core 提供，正常启动 gate 不能留在未使用的另一 binary。完成正常关闭后 Root 执行新 CLI preflight，检查具体 plan，随后已授权的本地 commit；再以带 gate 的包正常重开、读取保留配置，必要时另建新 qualification request 并只确认一次。replacement 本身不创建/消费 request，不使旧失败变成功，不使 W05/Main24 或正式用例自动完成。

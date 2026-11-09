# schema24→25 受控升级：下一卡 Source 提案

结论：新增固定 plan `schema24-to25-runtime-pause-v1`，采用“原 schema24 匹配程序普通备份 → schema25 目标备份程序隔离 handoff 演练 → 独立签发的 Native MigrationToken 原库 DDL”三段入口。旧 `schema23-to24-prepared-abandonment-v1` 的 plan、SQL、purpose、grant 文件、nonce 日志、receipt 与版本判断全部保留。此文只提出施工范围；未改源、未运行新升级、未打开真实数据库、未签发 grant。

基线为已独立接受的 storage commit `d17acc0e128d8438e530ffafc8d704d15b3dd500`，tree `0b182d56b6f5c76b3c80f0f4aeea38a384544dba`。SQL25 固定 SHA256 为 `6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0`。W17 source report SHA256 `7e1a2cc2b4d8beb0a7f8b0bbc3c42a4e21bd8eebb3c52ef458a14cc472f2db9c`，manifest SHA256 `72e908f451a0c324849c054e8c21965cbc4c3024149d1affcdde7aaa994c2633`，副本保留在 inputs。正式增量 0。

## 先处理两个实际入口断点

1. `upgradePreparedAbandonmentLocal` 在 `backup_prepared_abandonment_upgrade.go:425` 调用 `preparedUpgradeProgramHashes(opt,false)`，要求当前运行程序就是源程序。原 schema24 backup 程序不知道未来新 plan；不能仅在新二进制里加一条 `UpgradeLocal` 路由，再宣称它完成了“匹配旧程序备份”。首版采用已有的普通 `create` 能力，原程序实际运行产出备份，新程序只消费。若普通备份因现存保护/队列门拒绝，记录对应阻塞；不自动换用新程序冒充旧程序或放松保护门。
2. 现有 public handoff（`backup_prepared_abandonment_handoff.go:186-189`）要求当前程序等于 `TargetProgram`，而 Native apply（`backup_prepared_abandonment_upgrade_windows.go:141-143`）也要求当前程序等于同一个 `TargetProgram`。实际前者是 `ops/backup`、后者是 `apps/control`，不能把同一二进制哈希用于两者。旧 handoff 本就声明不产生 Native authority，也使用不同 receipt；新入口必须从设计上分别绑定两份目标程序，不能把旧 public receipt 当作可提交的迁移证明。

## 固定身份与数据流

| 项 | 新 24→25 固定值/职责 |
|---|---|
| Plan | `schema24-to25-runtime-pause-v1` |
| Native purpose | `RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1` |
| Grant schema | `researchos.pause-schema-migration-grant.v1`，仍用 `MigrationGrant` 数据结构 |
| 控制私有参数 | `--private-pause-schema24-to25`，只接受一个参数，无 caller 路径/authority 参数 |
| Recovery Root 参数 | `schema24-to25` |
| Grant 文件 | `current-schema24-to25-grant.json`，只从已 enrollment 的 Root 可执行文件同目录读取 |
| Nonce 目录 | `consumed-schema24-to25-grants`，`O_EXCL` 一次性消费，绝不复用旧目录 |
| 签名 kind | `pause-migration-grant`，显式选择新 purpose 的离线签名分支 |
| 公开演练命令 | `ops/backup upgrade-pause-backup`，不执行原库 DDL |
| 演练回执 | `runtime-pause-schema-rehearsal.json` / `researchos.runtime-pause-schema-rehearsal.v1` |
| 原库结果目录 | `<rehearsal-destination>.original-schema25`；既存目录禁止重试 |
| 提交结果 | `SCHEMA25_COMMITTED_ORIGINAL_BUSINESS_ROWS_UNCHANGED`；commit 错误为 `COMMIT_OUTCOME_UNKNOWN`，保留 intent，禁止自动 replay |

新 `PauseSchemaUpgradeOptions` 复用 `LocalUpgradeOptions` 的路径布局，其中 `SourceProgram` 明确为原24 backup 程序，`TargetProgram` 明确为目标25 control 程序；新增 `RehearsalProgram` 为目标25 backup 程序，以及 `HandoffBindingFile`、`HandoffBindingSHA256`。整个新 typed options 的 canonical JSON hash 入 `MigrationBinding.OptionsSHA256`。旧 `LocalUpgradeOptions` 结构与旧 JSON canonical bytes 不改。

新 receipt 同时记录三份程序的路径/哈希、全部旧/新 release inventory、SQL、原库 typed-row multiset、原始/恢复后 schema、恢复允许差异、恢复后 DDL 基线、回滚复验、备份 manifest、producer stdout/observation/binding 的 raw pins。`Binding.SourceReleaseSHA256` 继续绑定源 backup，`Binding.TargetReleaseSHA256` 继续绑定目标 control；额外 `target-rehearsal-program` pin 绑定目标 backup，并由 domain 将它与 typed options/receipt 精确比对。无需给旧 Binding 增字段或改变旧签名正文。

Native grant 还必须持有 `source-program`、`target-program`、`target-rehearsal-program`、`migration-sql`、`encrypted-backup-manifest`、每份 `encrypted-backup-payload:<name>.enc`、`isolated-restore-rehearsal`、`handoff-binding`、`backup-producer-stdout`、`backup-producer-observation` 以及全部 `source-inventory:<relative>` / `target-inventory:<relative>`。只记录 JSON 中的 program hash 不证明原程序执行；Root 须先独立核对真实执行 observation，再把该文件原始字节纳入新 grant。公开演练回执本身不签发权限。

## 哪些硬编码需要扩充

| 现有位置 | 当前限制 | 最小修改 |
|---|---|---|
| `internal/recoveryauthority/migration.go:11-14,50-71` | 单一 purpose/plan/SQL/argument；签名域与必需 pin 都固定旧 plan | 保留旧常量和旧 verifier wrapper；抽取不导出的固定 descriptor 验证器，新增新 plan wrapper。不能从 caller JSON 随意选择 schema/version/SQL/purpose |
| `internal/recoveryauthority/migration_windows.go:25-48,53-88` | bootstrap/frame purpose、grant filename、nonce dir、child argument 全为旧值 | 原导出函数保持旧 descriptor；新增新 purpose 的 Receive/Run wrapper。共享 OS handles、peer birth/image/SID、source guards、lease、job、private pipe 与 pin-held 主体；参数只来自源码固定 descriptor |
| `internal/recoveryauthority/enrollment_windows.go:68-69` | `migration-grant` 只签旧 purpose/schema | 添加显式 `pause-migration-grant` 分支；老分支不改。签发前调用新固定 binding/pin 验证；仍要求已钉住的 issuer 私钥 |
| `internal/recoveryauthority/native_other.go:14` | 非 Windows 只有旧 migration 接收拒绝 | 增新接收函数，始终 `AUTHORITY_WINDOWS_REQUIRED` |
| `apps/control/prepared_recovery_windows.go:25-30,49-61` | 私有参数仅旧值；解码旧 options；直接调用旧 domain apply | 在普通 flags/自动迁移/host 服务前添加新参数分支，接收新 Native token，strict decode 新 typed options、校验 canonical hash；再打开独占数据库并调用新 apply |
| `apps/control/prepared_recovery_other.go:8` | 新参数可能落入正常 flag 路径 | 明确识别并拒绝新私有参数 |
| `ops/supervisor/recovery_root/main_windows.go:30` | 仅固定 `schema23-to24` 子入口 | 添加固定 `schema24-to25`，Owner 仍经 private stdin pipe；不增加 caller grant/path/env 开关 |
| `ops/supervisor/recovery_enrollment/main_windows.go:25` | usage 未列新签名 kind | 只补明确 kind 说明，不更换 issuer anchor |
| `ops/backup/main.go:28,40-44,72-89` | command allowlist/flags 只已有 prepared handoff | 添加 `upgrade-pause-backup` 和 `--rehearsal-program`，路由新 domain handoff；`create` 与旧命令保持原样 |
| `internal/domain/backup.go:50-67,711-720` | 普通备份 handoff/保留 workspace 的私有 policy 只认识旧 prepared 路径 | 增独立 `publicPauseUpgradeHandoff` 和 `preservePauseUpgradeWorkspaces`；新分支仍要求普通 format、空 backup purpose、`allowProtected==nil`，完整普通 public 校验不能跳过 |
| 新 domain migration/handoff 文件 | 旧 release/template/DDL 是固定23/24、仅一张新表 | 新固定24/25实现，使用 SQL25 三张空表 allowlist；旧 helper 与旧 plan 调用不改 |

`internal/domain/backup_upgrade.go:245` **本卡不需要新增新 plan 路由**，因为首版不支持源程序执行新 `upgrade-local`。误把新 plan 交给该 API 应继续拒绝，另写负例。`apps/control/main.go:34` 已在所有普通 flags 前调用私有分流器，不需修改正常启动顺序。`internal/recoveryauthority/native_windows.go:140` 的 sourceGuards、`types.go:24` 的已 enrollment 公钥也不改；新 release 必须覆盖新文件和新构建，不能沿用旧 release 的 image/source pins。

## 可原样复用与必须新写的边界

可原样调用：`preparedUpgradeVersions`、`preparedUpgradeSchema`、`preparedUpgradeSnapshot`、`preparedUpgradeRowHash`、`preparedUpgradeIntegrity`、`preparedUpgradeDelta`、`preparedUpgradeRecoveryInvariant`；`upgradePath`/路径重叠判断、`upgradeQueueWorkspaceIdentity`、`upgradeQueueProtection`、`preparedUpgradeConcreteVerifier`；Windows 原生 root lease、raw pin 读取/RequirePin、`MigrationToken.Check/Begin/Finish/Close`；普通加密备份读取与 `restoreBackupPolicy` 内核。`preparedUpgradeRecoveryInvariant` 虽有“remain23”的注释，其逻辑仅要求前后 migration rows 相同，再验证固定恢复变化，可用于24保持24；测试必须覆盖已有 `runtime_prepared_abandonments` 非空行仍不变。

不得直接调用后仅改一个参数：`preparedUpgradeRowInvariant`（它拒绝源库已有 abandonment 表）、`preparedUpgradeDDL`（固定23→24）、`preparedUpgradeTemplate`（固定25段 slice，SQL24 索引23）、`preparedUpgradeRehearseDDL`（调用旧 DDL）、`preparedUpgradeRelease` 的 target25 路径（只接受23/24）、旧 rehearsal receipt 或旧 native apply。这些留在原文件，新增固定 pause 对应实现；避免把已审查旧门改成通用版本范围。

新 release 校验对 source 调用原 `preparedUpgradeRelease(root,24)`，target 使用固定25校验：精确1..25，无缺失/额外/改字节；1..24、四份冻结 contract 和 `next_v24_sessions.sql` 使用现有固定 hash，25使用已接受 hash。不能为凑精确24 inventory 从 target root 临时隐藏25，也不允许调用者提供 expected schema/hash。新 template 从固定 SQL 生成 `Source24`、`Original25`、`Restored24`、`Restored25` 四个 fingerprint；恢复版本用于隔离副本，不能混充原库目标 schema。首版真实原库入口只接受明确的 `Source24` 原始形态；若真实输入是另一个恢复形态，先核对并单独扩展精确输入合同，不采用任意 caller schema。

新 DDL 前置为精确1..24、精确 source schema、三张 pause 表均不存在、原始 typed rows hash 匹配。单一事务中执行固定 SQL25 并仅追加 migration25；所有旧表列顺序和包含实际 SQLite storage class 的行 multiset 原样保留（包括失败计数、大整数、BLOB、auth、队列、sealed content、abandonment 历史），仅允许三张新的空 pause 表；目标 schema/trigger fingerprint、1..25、integrity/FK 全部检查。先在隔离副本验证 rollback，再 commit。原库 apply 不调用 restore、backupFence、lease token 轮换或 Run 状态修复。

演练正常跑完整 restore：beforeRecovery 验证备份解出的原始 typed rows 与当前原库/备份 observation 基线一致；restore 内核完成 relocation、queue fence、credential fence、审计与 workspace 校验；afterRecovery 再记恢复后 baseline，在副本执行25 DDL。恢复引起的变化和 DDL 引起的变化分别记录，不能拿恢复后的行摘要当作原库升级前摘要。新 handoff 使用 ordinary backup，所以已有 protected-artifact/public gates 均保留；不能给 `RestoreOptions` 加通用跳过恢复或任意 SQL callback。

路径附加边界：新 options 校验应拒绝含 `#` 的 URI歧义路径（或在单独审查范围修正通用 URI编码）。此前独立测试证实既有 `store.Open` Opaque 路径把 `#` 之后截断；本卡无需扩大通用存储重构，但新升级入口不能允许“检查A路径、实际打开B路径”。仍校验 `PRAGMA database_list`、单 connection、无 temp schema、native file identity、目录非重叠与不可替换 handles。

## 有限 Source 范围

机器可读 `source-scope.json` 是建议的下一卡 allowlist，共 22 个路径：10 个现存文件窄改、12 个新文件。没有源码改动权限随本文自动生效；Root 如采用此卡，应先登记独立 owner/worktree/scope。新增文件名称有意使用 `backup_pause_migration*`，避免覆盖已经冻结的 storage `backup_pause_upgrade.go`。

现存窄改：

- `internal/recoveryauthority/migration.go`
- `internal/recoveryauthority/migration_windows.go`
- `internal/recoveryauthority/native_other.go`
- `internal/recoveryauthority/enrollment_windows.go`
- `apps/control/prepared_recovery_windows.go`
- `apps/control/prepared_recovery_other.go`
- `ops/supervisor/recovery_root/main_windows.go`
- `ops/supervisor/recovery_enrollment/main_windows.go`
- `ops/backup/main.go`
- `internal/domain/backup.go`

新增：

- `internal/recoveryauthority/pause_migration.go`
- `internal/recoveryauthority/pause_migration_test.go`
- `internal/recoveryauthority/pause_migration_windows_test.go`
- `internal/domain/backup_pause_migration.go`
- `internal/domain/backup_pause_migration_windows.go`
- `internal/domain/backup_pause_handoff.go`
- `internal/domain/backup_pause_migration_test.go`
- `internal/domain/backup_pause_migration_windows_test.go`
- `internal/domain/backup_pause_handoff_test.go`
- `apps/control/pause_recovery_windows_test.go`
- `ops/backup/pause_handoff_test.go`
- `ops/supervisor/recovery_root/pause_migration_windows_test.go`

明确只读依赖：SQL1..25及两个已冻结embed mirrors、全部冻结合同、`backup_pause_upgrade*` storage、旧 prepared migration/handoff 文件、既有 private token状态机/native OS primitives、issuer anchor。新 plan 的小型固定 descriptor 允许作为 migration.go 内部实现细节；没有任意版本参数、动态公钥/SQL或 public token 构造器。共享的 `backup.go`、Native入口和命令路由由 Root 串行整合，Mu Core M1-02 不进入本卡。

## 施工顺序与可验证完成判据

**A. source/fixture 卡。** 先新建 domain24→25 DDL/receipt/handoff，再加入严格分目的 Native wrapper 与CLI分流。阶段产物是可编译的受控入口、全量固定输入 scope、独立审查报告。必须有真实普通备份→隔离restore→25 DDL的正例，且原24基线不变；只测“无token拒绝”不足以接受原库提交入口。

| 必做组 | 具体成功与拒绝断言 |
|---|---|
| DDL完整性 | 24→25正例；失败计数与大整数/BLOB/旧abandonment行保留；三张新表空；错版本23/25/缺版本、漂移触发器、额外表、SQL字节改变拒绝；注入事务失败并核对回滚；再次提交拒绝 |
| restore handoff | 由源24普通备份实际产出；target backup/control不同程序pin同时可验证；manifest/producer stdout/observation/migration inventory/备份MAC/任何加密payload改字节都拒绝；beforeRecovery旧行相等、afterRecovery仅允许既有恢复差异；三份程序互换拒绝 |
| purpose隔离 | 旧23→24签名/option/receipt不能进入新入口，新24→25不能进入旧入口；adoption/abandonment Token不能替代MigrationToken；错误purpose/schema/plan/SQL/signature/缺pin/重复pin/过期/nonce replay都拒绝；旧全部authority测试仍通过 |
| Native/CLI边界 | 公共私有参数无inheritance必须在DB打开前拒绝；新命令不进入普通启动migration/worker；Root只接受固定新子命令；owner当前直接本地Root及project grant、实际root/db identity、live peer/SID/image、lease、EXCLUSIVE锁、attached/temp schema检查保持；新入口含#路径拒绝 |
| 原库提交演练 | 在一次性合成“原库”目录，真实新Root→control Native链携带已enrolled有效新grant完成一次提交；全部旧行原样保留且没有restore fence；第二次、过期、文件替换、alias/junction/锁冲突拒绝；commit-outcome-unknown/receipt持久化失败留intent且无自动retry |
| 既有回归 | 旧 `TestPreparedUpgrade.*`、`TestPreparedHandoff.*`、`TestBackupHostConfiguration.*` 与 storage `TestPauseStorage.*`；旧purpose/23→24程序路径行为不变；新plan误传`UpgradeLocal`继续失败，不偷偷新增宽入口 |

**B. 原始数据库演练前置。** 必须先有A独立 source/fixture接受和新构建的完整pin inventory。Root独立核对新 recovery-root/control/rehearsal-backup 可执行文件、源24原程序、source/target release所有源码/嵌入资源/依赖与构建闭包；新签名release覆盖当前source和Root/control images，旧release不能跨构建复用。源24 release、当前真实schema形态、原库路径/native ID、Owner授权与保护服务引用必须实测匹配。生产主进程/worker停写及root lease、SQLite EXCLUSIVE均实际可获；停止真实进程或触碰原库须由相应执行卡另行授权，本文不执行。

实际顺序为：冻结匹配源程序证据→由该程序创建普通加密备份（独立key目录，不泄露token/key）→在新目标程序中消费且完成隔离恢复演练→独立核对原库未改、完整receipt/payload/observer raw pins→才签发短时有效新grant并执行原库DDL。演练receipt不能反向覆盖原始source rows hash；Source任何漂移都重新备份/演练/签发，不能只更新某个摘要。

**C. 真实原库执行卡。** 只有B成功并得到范围明确的原库执行授权后，才用新Native Root子命令。一次grant最多一次commit尝试；执行后保持业务进程未自动启动，独立核对1..25、所有旧业务行/失败计数、三张新表空、完整intent/result以及key/lease/保护引用边界。该结果只关闭生产受控升级入口/该次DDL，不关闭Core暂停恢复、Mu接线、真实页面、22父任务或42正式用例。

## 本轮证据

本轮进行代码读取、符号定位、基线commit/tree与source证据hash核对，未运行新实现测试，因为没有新实现。`input-files.json` 保存被引用源文件的精确hash；`source-scope.json` 明确新增/修改/只读边界。存储基线工作树前后保持干净。历史R1/R2/R3/R4失败和接受回执不改。

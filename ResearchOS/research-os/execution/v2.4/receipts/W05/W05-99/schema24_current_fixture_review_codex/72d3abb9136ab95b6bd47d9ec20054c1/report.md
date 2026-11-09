# 当前 schema24 与旧 fixture 预期：三处失败只读定位

结论：三处实际失败均为 current fresh fixture 的 schema23 预期过时；现有日志没有显示 production migration/restore 回归。应修测试当前分支的版本与 release validator；原编号22→23、exact历史22及独立23恢复分支保留。生产 New 的当前编号库存、MIGRATION_PREBACKUP_REQUIRED、RestoreBackup exact version equality都不能放宽。

源码根 T=D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409
正在运行的suite raw=D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/current-composition-full-domain-root-0d2a82e73b754a5f/full-domain-and-native-authority-offline.stdout.raw

本次只读快照截取1405571 bytes，prefix SHA256=68dfd029cc615e325a7f84340cc545ddec9f1ca83d8b86777b29aae763cc5d76。它是running raw前缀，不是最终closed suite verdict；不能替代Root最终exit/Job cleanup和完整结果。只定位3父用例4 fail节点，未执行Go/native/SQL/provider，未读原DB或credentials，未改Source/Main/tests/canonical，无新增机械失败。

## 共用证据

T/internal/domain/domain_test.go:141–167：setup调用setupWithConstructor(t,New)，Bootstrap0001后直接对当前checkout的0002目录调用真实New，再ProvisionPrincipal/IssueCredential。
T/internal/domain/store.go:54–122：New扫描该目录所有编号 SQL、checkMigrationInventory和CheckMigrationSafety通过后同一transaction应用未安装版本，追加sessions/fence；没有固定只升至23的逻辑。NewCurrentMu:42–50在New之上仅改projectBindingRoute；注释“legacy constructor”指binding policy，不代表schema必须停23。
T/internal/domain/backup_migration.go:60–72允许精确连续编号库存最多24；15–29已有业务authority时缺编号升级必须MIGRATION_PREBACKUP_REQUIRED，空fresh DB正常应用当前24。
T/migrations/sqlite实际枚举0001..0024；0024 sha256=1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098 bytes2933，新增runtime_prepared_abandonments与immutable/terminal/fence triggers，现有行无改动（SQL:1–38）。
T/internal/domain/backup_prepared_abandonment_upgrade.go:26–28/79–132定义固定23→24契约：preparedUpgradeRelease支持23或24，精确编号库存与逐SQL/contract/additive hash验证；原upgradeConfigurationRelease的22→23语义明确保留。
T/internal/domain/backup_configuration_upgrade.go:20–26只支持count22/23且要求目录恰好该编号数量。当前24 root被旧23 validator拒绝是正确行为，不能让旧validator自动忽略0024。

| 实际fail节点 | 原因 | 最小修正 |
| --- | --- | --- |
| TestClientQueueFreshNumberedSchema，backup_command_queue_test.go:122 | setup已生成当前24；120却upgradeConfigurationRelease("../..",23)，当前源码目录24条编号，正确拒绝 exact1..23 | 当前fresh调用preparedUpgradeRelease("../..",24)、要求len(sqls)=25，再want=len(sqls)-1=24；保留contiguous/max/emptyqueue/0022原断言，快照标签fresh-current24。 |
| TestHandlerRejectedSessionPublicBackupReplay，backup_host_configuration_test.go:381 | 291–292用setup得到当前24，364 CreateBackupWithWorkspaces成功；380却SupportedMigrations=1..23 | current24分支固定支持1..24；保留所有201历史/100公开status窗口、原拒绝raw replay、workspace隔离及rebackup原断言。若保留exact23原用例，另用真实frozen23 fixture，不能把24备份改写成23。 |
| TestClientConfigurationFreshAndNumberedMigration/actual_Service_New，client_configuration_test.go:304 | 298从bootstrap1 fresh，299真实New当前库存完成24、nil；303旧断言必须23 | 只把actual_Service_New current fresh期望改为24，保留真实New调用与fresh empty断言；父fail是该child传播，不能单独“修父test”。 |

## 1. Queue current fresh 与 genuine historical22 边界

backup_command_queue_test.go:118–156是当前setup fresh，没有显式旧release root。修120–124为当前schema24 exact validator及len25，并保留：
- schema_migrations ORDER BY version逐行 applied==count，count==24/max==24（125–145）。
- 所有clientQueueTables为空（147–151），实际0022 SQL存在（153–155）。
- 当前fresh evidence名称从fresh-current23改为fresh-current24，不能伪称历史23。
- 可用固定0024 proof table空作为current24专有断言；不要删除既有queue/fence/schema断言。
159–196的TestClientQueueHistorical22NumberedSchema必须继续用queueUpgradeReleaseFixture(t,22)+upgradeQueueRelease(root,22)、sqls[:22]，精确max/count22、空queue、无host configuration/command identities/client_sessions后续与additive schema。不能全文件replace23/22为24。
如合同需要完整current+historical23 queue编号覆盖，可以显式新增exact23 fixture case；当前报错不要求改该历史生产helper。

## 2. Public backup replay：exact version保护有效

backup_host_configuration_test.go:291–364先走真实当前Service/public RegisterWorkspace→BootstrapProject→ClientService→host.configure→session.create；保留unknown session和foreign project的合法原拒绝，产生201 host_model_configurations，host.status仅返回100但历史不删，再CreateBackupWithWorkspaces。
backup.go:139–153 backupMigrations从实际DB schema_migrations有序读取；restoreBackupPolicy:578 readBackup后588–589比较Hash(manifest.Migrations)==Hash(SupportedMigrations)。错配拒绝在591 backupNewStage前：该失败保护了隔离恢复，没有进入mutation。
最小current修正是380的upgradeVersions(23)→upgradeVersions(24)，而不是改production RestoreBackup、扩大成>=/prefix，或拿收到的manifest.Migrations原样设为“支持版本”来跳掉版本检查。可以在fixture先显式assert真实DB migrations==upgradeVersions(24)，再把固定24作为restore policy。
原restored raw response精确一致、session ID一致、replay=true、workspace rebound不同path、rebackup通过（388–412）全部保留。

若这条原schema23公共拒绝重放覆盖也要继续：在同父test下分current24与historical23，完整业务body可抽一个test-only helper共同调用，分别固定schema/migration policy24与23。真正legacy23 fixture可复用：
1. configurationUpgradeReleaseFixture(t,23)（backup_configuration_upgrade_test.go:30–53，按固定编号22 root追加0023并validate exact23；contracts/additive都在该root）。
2. setupWithConstructor（domain_test.go:145–167）中constructor调用真实New(db,contractsDir,filepath.Join(frozen23Root,"migrations/sqlite/0002_domain.sql"))。选择是在测试准备时固定库存，New所有preflight/DDL/fence都仍执行，source DB只安装到23。
3. 断言exact23连续编号、proof table不在23；公共业务body及RestoreBackup固定upgradeVersions(23)保持原语义。
不使用rawService假构造、不执行DROP0024/触发器、跳CheckMigrationSafety或改New参数内部策略。该helper证明当前公共API在真实schema23 fixture上的兼容，不冒充历史编译的schema23 binary/native release验收。
已有backup_configuration_upgrade_test.go:621–658对upgrade后真实23 target调用New with opt.TargetRoot、普通23 backup/restore/rebackup，使用upgradeVersions(23)且workspace隔离；它必须保持。该已有roundtrip不完整替代本case的unknown/foreign Session拒绝proof原字节重放覆盖。

## 3. Client configuration fresh 与固定22→23分支

client_configuration_test.go:251–295两个numbered22_additive_false/true先configurationDB(t,22,additive)，手动只施用0023并INSERT version23，验证3新表空、旧完整rows无变化、client_sessions是否存在仅由additive控制。本次actual两个child均pass，必须原样保留22→23与业务保留断言。
297–309的actual_Service_New是另一种测试：configurationDB(t,1,false)→真正New当前root。actual output=24 <nil>符合当前24契约，只有303版本预期23过时。更新current期望24并保留actual New与fresh client_sessions/host_model_configurations空检查；可追加proof空表，不可把这个current child换成历史构造器使它继续23，以免失去真实当前启动覆盖。
configurationDB(t,version,additive):39–98本身按编号n<=version施用精确SQL，在这里无需改helper，也不能把默认version22变24。真正legacy23 public helper仅用于明确新历史subcase；当前三处failure不必引入它才可修正。

## Source作者的范围与验证输入

最小修改责任限三个test文件的current branches。新增历史23 helper如采用，应位于明确test-only文件，用existingexact23 release fixture + realNew，并在同父PublicReplay测试保存current24/historical23完整断言；production backup.go、store.go、backup_configuration_upgrade.go、backup_migration.go和0024 SQL保持当前契约。

Root下一轮已有授权的验证至少需要这三个父tests + untouched历史22和numbered22 additive child + explicitlegacy23 publicreplay（如新增）。当前完整offline suite仍由Root等最终closed receipt再判；本报告没有新的PASS verdict或formal acceptance。后续实际错误继续由Root分配ordinal，失败计数/旧证据不重置。

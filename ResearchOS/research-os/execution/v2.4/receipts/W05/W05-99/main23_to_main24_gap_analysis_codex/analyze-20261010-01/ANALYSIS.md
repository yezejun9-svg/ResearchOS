# Main23 → Main24 当前代码差距分析

结论：当前 Main 为编号 schema23；Main24 不是已组合并取得资格的发布程序。存在明确的 schema23→24 prepared-abandonment 候选，但不可把其组件通过视为公开升级链路通过。本轮只读源码与既有回执，不运行 Go、SQL、Native、模型、Root stage，不修改 Main、canonical state、Scope 或其他候选。

## 1. 当前 Main 的准确边界

- `migrations/sqlite/` 编号文件为 0001..0023，没有 0024。`next_v24_sessions.sql:1-6` 是产品 v2.4 会话索引，注释明确不增加 schema_migrations。
- `internal/domain/store.go:60-73,104-116` 先校验编号迁移清单，再在同一事务安装附加会话表；不是 schema24 实现。
- `internal/domain/backup_migration.go:64-67` 的 `checkMigrationInventory` 拒绝超过23个编号迁移；`backup_host_configuration.go:80-102` 的 `backupConfigurationPresent` 拒绝版本24并固定校验SQL23结构。因此仅放入0024、仅提高最大版本或手改数据库均不足以形成可用发布。
- `internal/domain/backup_upgrade.go:245-259` 的 `upgradeLocal` 仅分派22→23、21→22及13→14/13→20，其他plan返回`UPGRADE_PLAN_UNSUPPORTED`。
- 实际公开CLI是`ops/backup/main.go:26-83`，命令为`create|export|restore|upgrade-local`，不是apps下的backup-local。`--source-root`和`--plan`帮助文本仍只提schema13/14/20，已落后于现有21→22及22→23能力；这是单独低优先级可逆文案问题，不能修复23→24缺口。
- 对三个冻结合同 tasks.json、acceptance.json、execution.plan.json 的精确搜索没有Main24/MAIN24/0024/23-to24字面目标；W05-99卡要求自身正式门与A04等对应证据。产品v2.4不能自动推导为编号SQL24要求。

## 2. 已有候选可以复用，但仍需当前组合

固定候选契约位于`prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2/CONTRACT.md`；后续修订源码位于`prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6/candidate-root`。固定plan为`schema23-to24-prepared-abandonment-v1`，SQL24原字节hash为`1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098`。

契约要求先组合prepared-run-abandonment v4（含0024和migration preflight）及native authority Source，然后组合升级器。它区分隔离恢复演练与原数据根apply：前者普通加密备份/恢复后在隔离库迁移；后者另需opaque MigrationToken、OWNER、原库lease及完整固定输入。新的业务表为`runtime_prepared_abandonments`。

`schema24_fixture_actual_independent_review_codex/3e1e9204c6804e119c289c06a07d953d/review.json`只接受fixture与original199 targeted组件；其limits明确未接受Main adoption、生产迁移、签名令牌或完整domain回归。不得重跑这些未变化的已通过组件来冒充新公开交接验证。

## 3. 可定位的真实交接冲突

候选文件`backup_prepared_abandonment_upgrade.go:397-408`的`preparedUpgradeProgramHashes(opt,currentIsTarget)`读取`os.Executable()`并要求其digest等于SourceProgram（currentIsTarget=false）或TargetProgram（true）。`upgradePreparedAbandonmentLocal`在第427行及后续source recheck传false，契约也明确要求演练由SourceProgram运行。

但当前已资格的Main23缺少新plan分派。实际两个不同发布程序直接串接时：

1. 用现有Main23执行新plan：当前`upgradeLocal`返回`UPGRADE_PLAN_UNSUPPORTED`。
2. 用组合后的Main24执行新plan且SourceProgram仍是已资格Main23：候选返回`PREPARED_UPGRADE_MATCHING_PROGRAM_REQUIRED`。

这两项是由当前分支和hash比较推导的静态可复现条件，本轮没有发起Native命令，也没有伪造失败回执。把SourceProgram改为新Main24自身会改变“matching old program”的语义，不能继续宣称消费原Main23程序身份。

现有fixture没有覆盖这个区别：候选`backup_prepared_abandonment_upgrade_windows_test.go:18-25`继承configurationUpgradeFixture；该helper再继承queueUpgradeFixture。当前`backup_queue_upgrade_test.go:153-157`将SourceProgram和TargetProgram均设为`os.Executable()`，即同一个测试程序。因此其PASS不能证明不同Main23/Main24程序的公开交接。

## 4. 最小可实施切口

先提交一个独立的公开23→24交接契约与实现候选，明确旧程序、新程序、coordinator分别负责什么，再做组合和资格；不要先把SQL24放入Main。

建议保留已资格Main23承担source匹配加密备份与既有输出身份，新增Main24/coordinator消费该已封存备份、原始manifest/恢复回执与程序资格，在隔离目标执行固定0024并检验原库未变。如果继续采用“source程序内演练”的设计，则需要单独、可审查、取得资格的23-compatible bridge程序身份，不能把它标作现有Main23，也不能仅放宽hash相等检查。两条路线应选择并冻结一条，避免引入两个来源不明的程序别名。

最小改动面应从候选`backup_prepared_abandonment_upgrade.go`的程序绑定/演练入口及`ops/backup/main.go`的显式公开参数/输出契约开始；组合阶段同时携带已存在的0024、native authority、备份恢复hook、版本/完整结构校验和对应来源pin。不要改13/14/20/21/22/23既有固定plan语义。

新增验证只覆盖新增或有实质变化的边界：真实不同source/target程序、同一Main23实际输出作为新输入、拒绝互换/篡改程序与release/SQL/manifest、隔离恢复晚期失败保留原库不变、升级后普通backup/restore的精确24结构支持及拒绝25。保持原数据根apply为单独任务；仅隔离升级不应额外制造OWNER/token enrollment工作。

## 5. 输入复用与事实边界

Root本轮告知GEN02的22→23 upgrade、backup23、verify23 Native均为0；本分析未重放这些成功步骤，也未独立重新裁决其实际执行。下一步应由Root提供并冻结该实际输出原始ref、Main23程序资格、对应source/owner/scope和关闭证据，作为23→24的输入，而非另造schema23 fixture。

此前full20to24 gap分析中的PUBLIC22_TO23_CONTINUATION旧状态已被Root本轮结果推进；其余历史20/21连续来源及公开23→24缺口不因这一步自动关闭。现存Main23五个源码pin和binary按本轮读取的qualification重新计算，结果见input-pins.json。原Main23保留可复用，Main24需新组合资格。

诊断原始工具结果：a27c9f outer1（rg包含不存在cmd路径，os2）；81ce7e outer1（apps内搜索无匹配，rg1，非产品执行失败）。均已告知Root，请以Root全局序号为准。没有Go/SQL/Native/模型/Root stage执行。未读取凭据或私有数据根。

状态：READ_ONLY_GAP_ANALYSIS_COMPLETE；不签发Main24资格、完整20→24通过、W05正式接受或执行授权。
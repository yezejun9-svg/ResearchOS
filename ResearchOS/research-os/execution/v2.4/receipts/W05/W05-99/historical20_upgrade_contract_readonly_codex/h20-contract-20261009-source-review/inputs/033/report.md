# historical20 ordinary upgrade：只读资源与合法路径探查

结论：历史源码资源可以补齐，但当前产品确实缺少 20→21 合法升级入口；不能将现有 23→24 grant 用于旧版本，也不能仅补程序、备份和恢复回执后让普通 New 越过检查。另一个需要先冻结的边界是输入库形态：历史 control 真正启动的 schema20 基础库，并不自动包含 LEG2 手动安装的旧 client_sessions DDL。

本报告是只读源码结论，不是 build、runtime 或产品接受。完整命令 IO、Git tree、blob 内容、源码摘录和资源 pins 随包保存。

## 1. 历史 tree 实际提供的资源

已核对 commit `3225a31fd25969c6a5e071a2fc686cb4a835e162`，完整 tree `955430efd12ef450a0eeb86a5f07054518c0e058`，共 13490 个 tree entries。Git 原始 NUL 分隔 ls-tree 与 cat-file batch 输入/输出全部保存；323 个选定源文件加 1 个必要 embed 均按 Git blob SHA-1 校验后逐字节提取，没有替换历史模板。

| 资源 | 实际路径及用途 | 限制 |
|---|---|---|
| schema20 建库/Owner 初始化入口 | `apps/control/main.go:39,76–100,125`；`--bootstrap-owner --credential-file` 走 store.Bootstrap + domain.New，再建立 Owner 并退出 | 是历史源码支持的独立新根初始化路线，尚未编译或运行 |
| 交互 CLI | `apps/cli/main.go:39–53` | `init` 等仍为 NOT_IMPLEMENTED，不能拿它建立历史库 |
| 备份与隔离恢复入口 | `ops/backup/main.go:27–42,75–84,114–167`，命令 create/export/restore/upgrade-local | `--root` 必须是真实匹配历史根；普通 restore 不接受迁移脚本或 arbitrary approval |
| 版本资源 | `migrations/sqlite/0001_…` 至 `0020_research_cycle_work.sql`，恰好连续 20 个编号 SQL | 不加入 21–24，也不改版本账 |
| 旧 session DDL | `migrations/sqlite/next_v24_sessions.sql`，blob `9efc768f8f4cfb6ac31e1f88a78ad095877328af`，SHA-256 `3b00677902c3be1dbffb8f7505293bae7242dc976e8017562ab86254ac212f2a` | 文件存在不等于历史公开启动执行了它 |
| 编译输入 | 原始 go.mod/go.sum、Go 1.27.1、Windows/amd64、全部相关 Go 源与 `spec/v2.0/contracts` JSON | 未运行 Go list/build/test，构建可行性尚未实测 |
| 唯一找到的 Go embed | `adapters/protectedstore/frozen_development.go:12` → `frozen_development.json`，blob `1d64804ef6da43b2e8005b5cfd102fed7e326202` | 原 blob 已补充到历史源快照，未读取私钥或 provider 私密材料 |

go.mod 有 19 个直接/间接模块，主要直接依赖 jsonschema/v6 v6.0.3、x/sys v0.48.0、modernc.org/sqlite v1.60.1；其余精确版本在原 go.mod 与 `go-dependency-resource-presence.json`。所有 19 个本地 expanded module 目录存在；8 个 zip 不存在，不能据此断言依赖缺失。Go 可执行文件 SHA-256 与历史 toolchain lock 一致。依赖内容、模块校验和与实际编译闭合仍须 Root 后续构建流程验证。

## 2. 历史真实入口与 LEG2 夹具的区别

历史 `internal/domain/store.go:39–83` 的 New 只枚举并执行编号 SQL，结束后直接返回 Service。它没有安装 `next_v24_sessions.sql`。对完整历史 tree 的 apps/internal/ops/bootstrap/adapters 进行只读 git grep，仅找到 backup_upgrade.go 的注释以及 `MapClientSession` 函数定义；没有找到公开 session DDL 安装调用。`MapClientSession` 是向已存在表写入的域函数，不能自动建表。历史 `EnsureClientSessionFence` 注释和实现明确在 client_sessions 不存在时 no-op。

LEG2 `legacy_migration_fixture_test.go:99–114` 则主动执行 1..20 加原始旧 DDL；`:117–140` 从当前测试 fixture 复制 synthetic Project/ProjectProfile 行。该构造函数没有安装当前 fence；restore 子分支随后使用当前 fence，是单独行为。它保留了真实历史 SQL 字节，但不是“历史 control 公开启动已经生成过这个客户端库”的证据。

因此应明确冻结两个输入形态：A 为历史 control 真正建立的 schema20 基础库；B 为有独立安装 provenance 的 schema20 + 旧 client_sessions 扩展库。现有 LEG2 是 B 的 synthetic fixture，不能仅重新打包历史 CLI 就补足 B 的生产来源。

## 3. 当前检查与迁移能力

当前 `backup_migration.go:15–56` 先检查连续版本账，再检查所有非 sqlite 表是否已有 authority 行（仅排除版本账和精确 mutex seed）。有数据的 schema20 对当前 24 个 SQL，在 `applied != len(files)` 处直接返回 `MIGRATION_PREBACKUP_REQUIRED … migration 21`。该函数只接收 DB 和文件列表，没有 backup、approval、grant 参数，也不消费“已做备份”的标记。它是拒绝隐式迁移的守门逻辑，不是授权执行器。

| 路段 | 当前可达实现 | 是否能解决 schema20 普通升级 |
|---|---|---|
| 13→14 / 13→20 | `backup_upgrade.go:245–271` 的固定 LocalUpgradePlan/FinalSchemaUpgradePlan，源根硬要求 13 | 不能，schema20 不能假装成 13 |
| 20→21 | 无 UpgradeLocal dispatch、固定计划或对应 native handler | **真实实现缺口** |
| 21→22 | QueueSchemaUpgradePlan；`backup_queue_upgrade.go:320–330` 要求真实 source21 / target22 | 有源码路线，但不能跨过缺失的 20→21，且仍需独立匹配 release 根与 actual 验证 |
| 22→23 | ConfigurationSchemaUpgradePlan；`backup_configuration_upgrade.go:174–184` 要求 source22 / target23 | 同上，不等于完整链已接受 |
| 23→24 隔离演练 | `backup_prepared_abandonment_upgrade.go:561–589` 要求 source23 / target24 | 不能接受 schema20 |
| 23→24 原根执行 | `recoveryauthority/migration.go:11–14,51–86` + recovery_root/main_windows.go:43 + private control handler | purpose、plan ID、SQL hash、private flag 都固定为23→24，不能重用作20→21 |

历史普通 RestoreBackup (`backup.go:493–531`) 要求 backup migrations 与调用方 SupportedMigrations 精确相等；提供 Migration callback 的域 API 只对未发布的隔离副本执行。历史 `ops/backup restore` 不注入该 callback。存在低层 callback 不证明有合法产品命令；也不授权手写 SQL 补版本账或把恢复副本自动接管为原根。

当前 native 23→24 grant 要求签名 release/grant、固定 purpose/plan/SQL、短时 nonce、source/target program 与完整 inventory/schema pins、原始 rows hash、encrypted backup manifest、isolated restore rehearsal 和 options pins，随后由继承 OS/crypto authority 的私有 control 入口执行。原库变更只接受该固定类型的 token。新20→21路线需要自己的冻结合同和真实生产连接，不能削弱这些边界。

## 4. 下一条 Root 行动与资源步骤

**下一条 Root 行动建议：派发一个 Source-only 的“schema20→21 迁移合同与入口缺口”任务。** 输入直接绑定本包历史 commit/tree、20 SQL、旧 DDL、当前 CheckMigrationSafety/UpgradeLocal/native authority 源码；产物先明确 A/B 输入形态、不可变 source schema、target21 schema、跨21→22→23→24的 release 边界、备份/隔离恢复/撤销证据，以及原根应用或审核后切换隔离副本的唯一生产处理路径。不得在此任务中改当前 historical template、UDF、trigger 或 schema 来迎合测试。

可并行准备、但尚未执行的 Root 资源步骤：

1. 在新的隔离路径 detach 精确 historical commit；记录 HEAD/tree 与所有构建输入 pins，不使用当前 root 的文件替换旧 session DDL、旧 fence 或旧 contracts。
2. 使用已锁定 Go 1.27.1 和本地依赖，先真实枚举历史 `./apps/control` 与 `./ops/backup` 的 tagged/compiler/embed 闭合，再分别编译。可用命令形态为 `go build -mod=readonly -trimpath -o <unique-output>/historical20-control.exe ./apps/control` 和相应 `./ops/backup`。仅源码重建程序，不能冒称历史原版已发布二进制或产品接受。
3. 经 Root 另行授权后，才用历史 control 的 `--bootstrap-owner --credential-file <isolated-private-output>` 在全新 synthetic data root 建 A 型历史库；枚举真实 1..20 schema 与是否缺 client_sessions。不能在该结果上偷偷补旧 DDL后仍标历史CLI建库。
4. 同一历史 backup 程序执行 matching create 与隔离 restore，保留完整原始 IO、program/root/schema/rows/manifest pins。B 型旧 session 数据若无真实安装来源继续明确缺来源；不复制原 paid/trial 数据或读取其凭据。
5. 在20→21冻结合同、生产入口及独立验证完成之前，停止于资源/演练结果。不能调用23→24 grant修补20库；21/22/23 release根也须实际存在并单独验证，不能截短当前24文件夹来冒充发布版本。

上述步骤均未在本轮执行。当前只生成只读资源 capsule。项目永久身份和 Main HEAD 保持不变；所有 SourceGuard 已关闭。新增只读错误888是 rg 错猜不存在 backup_restore.go，outer0/Python/nativeNULL，完整原始调用已保留；后续直接读取已枚举的 backup.go，无产品重跑。

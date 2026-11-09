# Historical20 合法升级入口与全链合同：只读研究
状态：READONLY_CONTRACT_AND_IMPLEMENTATION_BOUNDARY_IDENTIFIED。不是实现、实际演练、产品接受或全链完成。
研究者：codex:/root/attach_fixture_source_review；不担任后续实现作者。Root 仍唯一 Main/canonical 写入者。
R=D:/作品集/ResearchOS/research-os；T9=R/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371。
K 是目录别名：D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4，不存在本报告另行发明的“K条款”。

## 1. 结论与明确缺口
真实历史20→当前24仍未贯通。缺口至少分为：
1. 当前 UpgradeLocal 没有20→21固定计划或 dispatch；CheckMigrationSafety 只拒绝隐式迁移，不能消费一个“已经备份”的 boolean/JSON 来授权。
2. 仅执行原0021会得到编号21，但不自动得到现有21→22所要求的完整客户端扩展形态。下一跳要求原样保留，不能为让20库通过而更改21/22/23模板、触发器或UDF。
3. 历史20 executable 尚未构建/运行；真实A型建库、matching backup/isorestore、准确目标21/22/23 release/program和全链演练尚未闭合。源码存在不等于这些资源已经可运行。
4. B型旧session扩展库的生产安装 provenance 尚未建立；LEG2只提供真实旧DDL字节上的 synthetic fixture。B分支的缺来源不阻塞A分支的固定计划开发和历史程序资源构建。
最小产品工作可以先落20→21及其显式 additive 形态合同，但必须将21→22→23→24接续和最终单写入切换列为未完成门，不能用局部21通过替代全链。

## 2. 哪些是规格要求，哪些是源码事实或实现建议
| 类别 | 依据 | 内容 |
|---|---|---|
| 明确规格 | K/18_EXISTING_REPOSITORY_MIGRATION.md §4、§6 | 默认在新候选根/经授权备份副本演练；先恢复验证，再连续编号迁移、行数/引用/hash检查和失败回退；失败不得成功记账、不原地降级唯一库；W18独立恢复资格与受支持正式切换。 |
| 明确规格 | K/07_OPERATIONS_AND_EVOLUTION.md §6.1–6.2 | 升级前一致性加密备份，覆盖权威DB/对象manifest/配置版本/未决动作；SQLite真实快照，不能忽略WAL；空目录恢复，恢复默认不外写/不调度，对账后显式切换身份并撤销旧实例写资格。 |
| 明确规格 | 同文 §7 | release包含commit/锁/合同schema/读写版本范围/升级路径/回滚条件/证据及来源校验；只在数据兼容成立时回滚程序指针；不可逆迁移须维护策略，不承诺任意无损回退。 |
| 明确规格 | K/06_ACCEPTANCE_TESTS.md A12-01..05、K/contracts/acceptance.json | LIVE_WINDOWS，W18；真实两个项目/费用预留/游标/outbox/验收及产物；隔离失败迁移；前后实体关键字段/hash、数据差异、实际耗时/原命令和独立复核；fixture≠live。 |
| 源码事实 | T9/internal/domain/backup_migration.go:15 | 有权威数据且版本不是目标完整连续集就拒绝；当前Owner bootstrap的auth数据也构成权威，并非只有Project行。 |
| 源码事实 | T9/internal/domain/backup_upgrade.go:245 | 仅13→14/20、21→22、22→23、23→24已有计划分派；没有20→21。 |
| 实现建议 | 下述§5–§7 | 新固定计划、A/B profile、独立Source文件、分阶段行不变式、明确additive清单；这些是根据现有边界推导的新设计，不能写成规格已经规定的函数名或plan ID。 |

## 3. 历史输入形态必须独立识别
绑定历史 commit 3225a31fd25969c6a5e071a2fc686cb4a835e162 / tree 955430efd12ef450a0eeb86a5f07054518c0e058。本报告从既有资源capsule逐字节读取32个相关历史文件，对其Git blob SHA-1及SHA-256核对通过；没有运行Git。

A：历史公开control所建基础20。historical-source/apps/control/main.go的 --bootstrap-owner --credential-file，在新RESEARCHOS_DATA_DIR获取root lease，经store.Bootstrap和domain.New运行真实1..20，再生成Owner并退出。historical-source/internal/domain/store.go只执行编号SQL，没有安装next_v24_sessions。historical apps/cli 的 init 不是这个建库入口。A必须由真实该程序建出、验证schema_migrations精确1..20及client_sessions实际缺席；不能从现代库删行/降版本制造。

B：真实1..20 + 原旧client_sessions扩展。旧DDL路径 migrations/sqlite/next_v24_sessions.sql，blob9efc768f8f4cfb6ac31e1f88a78ad095877328af，SHA256 3b00677902c3be1dbffb8f7505293bae7242dc976e8017562ab86254ac212f2a。T9/internal/domain/legacy_migration_fixture_test.go:116起先执行历史1..20再主动执行此DDL，后续项目行从当前fixture复制；这是B的synthetic施工夹具，并不是historical control曾自动创建它的证据。B生产接受还需独立安装来源及真实行样本。允许保留B纯fixture测试，但结果名称必须如实标明。

A、B都需冻结完整sqlite_master表/索引/触发器SQL以及连续账，不只看MAX(version)。无来源的混合schema、已有21表但账20、缺行/重复/非integer账、未来版本、额外表/触发器、不同旧DDL不能被自动“修复”。恢复后的20另带恢复barrier/trigger与撤销凭据，属于恢复产物形态，不能冒充未恢复A/B原输入；其差异须由matching恢复报告证明。

## 4. 0021及下一跳的精确边界
T9/migrations/sqlite/0021_research_pending_windows.sql，SHA256 36d4e5c93aa1edcd7ca5aca922b3bea11d5739f307bd11c6834936adf5552f32，仅创建 research_pending_windows：project主键，active_cycle，profile_revision>=1，trigger仅USER/SCHEDULE，窗口及创建更新时间字段均NOT NULL。它不创建client_sessions、不加入transcript列、不安装session fence，也不回填业务行。

T9/internal/domain/backup_queue_upgrade.go:64 的 source21 template 固定执行1..21，再执行当前next_v24_sessions（SHA256 1ca3930f96f7c2c99e7bc6e668dd5658393264cf1e6bf6352b47fb3de8c7dfe3），再installClientSessionFence(false)。:742的release validator要求精确21/22个编号文件+原合同hash+固定additivehash。upgradeQueueMigration要求additive重装为no-op，不能充当修复未知源shape。于是：
- A + 原0021仍没有client_sessions，不能直接进入此21→22。
- B + 原0021仍可能缺transcript列和当前fence，同样不能直接进入。
- 新20→21计划若希望交给既有21→22，必须在自己的固定计划内显式列出且审查从A/B到该target21 shape的真实additive变更；为A创建空Session结构，为B允许的列扩展/索引/fence变化均须精确冻结，保留所有原session/epoch/lease/日志和NULL，不虚构会话或handoff。
- additive不是篡改0021，也不能伪造其历史执行记录。新计划报告分别记录numbered SQL和additive文件/代码hash及实际执行；0021与版本21账在受控事务里成功执行后才能提交。
- 若目标21的真实release/启动兼容性尚不能证明，产物停为隔离迁移候选，全链仍BLOCKED。不能截短当前24 migrations目录或把当前binary改标21，冒充匹配release。
历史21/22/23 trigger模板保持原字节；若新21实际shape与下一跳不一致，保留失败和具体diff，补合法入口/合同，不能调模板迎合。

## 5. Build-ready最小产品实现边界（建议，尚未写产品代码）
选择已有 backup upgrade-local 公共入口的固定计划分派，作用域为离线源库→加密快照→未发布隔离候选。建议新增plan ID schema20-to21-research-pending-windows-v1（待实现冻结；当前不存在），不提供caller任意SQL、版本范围或schema绕过flag。不在普通New/CheckMigrationSafety加入特例，也不借用23→24 token。

1. 受控输入：LocalUpgradeOptions现有路径、源/目标program、source20/target21完整release manifest、A/B shape profile、原0021hash、明确additive清单和目标21 shape。源/目标program只被旧代码hash并不证明曾执行；必须另外留实际build/launch/matching备份与恢复IO。
2. 独占与路径：沿用upgradePaths和upgradeOpenExclusive的alias/重叠/现有目标拒绝、原root离线/锁、独立snapshot/destination/key路径。源root与对应program/manifest从开始到结束保持精确。元数据不得因复用当前构造器被隐式升级。
3. 合法matching backup：新增coordinator必须明确实现并独立验证其source20读取/备份兼容性后，才可像现有固定计划一样产生受plan绑定的加密迁移快照；仅拿旧SourceProgram hash不算“用旧程序备份”。同时资源路径可真实运行历史20 backup create+restore证明旧程序资源可用。两者格式/用途不同，不能将普通历史备份宣称为已通过新计划policy的包，也不能略过MAC/purpose/manifest检查。
4. 隔离恢复：只在未发布副本执行固定migration callback，保留restoreBackupPolicy现有schema/version/contract/content checks、backupFence对账、credentials撤销与source relocation。Migration不接收用户自定义callback/SQL。current backupFence对B会加transcript及fence，必须作为明确additive阶段的一部分校验；不能在验证前默默修复B shape。
5. 迁移原子性：从实际1..20读取后先验shape；固定0021+批准的additive操作、唯一版本21账、integrity/FK检查和目标shape检查在相应原子边界完成。失败回滚不记21；稳定加密快照、原库/原版本账和原程序保留。不能通过INSERT旧1..20账补洞，也不能用21 synthetic基准替代真实20。
6. 不变式拆开：DDL阶段以恢复fence完成后的实际输入为基准，旧行/SQLite存储类型/NULL/Blob逐项不变，只有唯一新21账、新空research_pending_windows及精确additive变更获准；恢复阶段仅接受现有精确定义的凭据撤销、Run对账/过期租约、effects UNKNOWN、audit/outbox增量、来源重定位。不得把两种阶段混成宽松“允许若干不同”名单。
7. 接续：用独立匹配的21→22、22→23、23→24实际release和程序继续链，每跳检查输入shape、备份/恢复/差异和原拒绝条件；逐跳保存receipt。最后目标24通过current普通启动和真实业务关键路径，且独立切换前保持不调度/不外写。任何中间pass不提升全链状态。

现有upgradeRecoveryInvariantForTarget硬限source13→target14/20，其版本账逻辑要求14..target；不能给它传21、投影掉真实20账或改变原断言来复用。新增20→21专用不变式，可复用无损row读取/比较工具；preparedUpgradeSnapshot/typed-row设计可供实现参考，但23→24的硬编码授权和row允许差异不可继承为20→21权力。

## 6. 最小Source改动清单
| 路径（相对R；当前事实来自T9） | 建议改动/边界 |
|---|---|
| internal/domain/backup_upgrade.go | 只增加新固定plan dispatch；原13/14/20及21/22/23既有分支/模板不变。 |
| internal/domain/backup_pending_window_upgrade.go（建议新文件，当前未创建） | 专属source20 manifest/shape验证、固定21 SQL和additive计划、快照/隔离恢复协调、分阶段无损不变式、target21交接判据。 |
| internal/domain/backup_pending_window_upgrade_test.go（建议新文件） | A/B区分、gapped/forged/future、exact旧行、21空表、事务故障、后备文件不损坏、禁止缩短24伪release等边界。fixture不代替历史CLI。 |
| internal/domain/backup_pending_window_upgrade_windows_test.go（建议新文件） | 真实历史control建A、matching backup/restore、精确program和paths、锁/alias/并发/失败回退、跨21→22交接及恢复后普通host拒绝/接入行为。 |
| ops/backup/main.go、ops/backup/README.md | 固定新plan帮助及可运行命令契约；当前help仍只列13→14/20需同步；不要加入任意批准JSON/SQL入口。 |
| internal/domain/backup_migration.go、store.go | 保持ordinary guard，不作为绕行入口。 |
| migrations/sqlite/0021_research_pending_windows.sql、0022/0023/0024、历史next_v24_sessions及历史21/22/23模板 | 原字节保留，只按固定计划实际执行；不编辑模板消除差异。 |
| internal/domain/backup.go、backup_recovery.go、client_session_fence.go | 复用明确contract；如果专属plan确实需要窄policy入口再独立提出并审查，不能默认放宽所有restore。 |
| internal/recoveryauthority/migration.go、migration_windows.go；ops/supervisor/recovery_root/main_windows.go；apps/control/prepared_recovery_windows.go | 现有purpose/plan/SQL/privateflag硬限23→24；最小隔离路线不改。若后续要求原根原地应用20→21，必须另立完整purpose和native-authority合同，不能换参数重用当前token。 |

## 7. 审批/接受合同
这里指产品既有信任边界，不是再次向用户索取本轮研究授权：
- Source作者不签发自身接受；独立审查冻结plan、各shape、allowed delta、release/program/SQL/backup/rehearsal pins。
- 固定本机管理命令只能产生隔离候选。RESTORED_RECONCILIATION_REQUIRED不等于接受、启用或切换；未完成资源对账不自动激活。
- 正式切换沿既有受支持控制面：独立review、原worker/外部动作对账、单写入root/instance身份与epoch、撤销旧实例写资格、数据损失窗口/回退程序兼容证明。无须新造第二个产品审批页或长期完成总账。
- 原根应用支路若被选择，当前23→24 signed short-lived grant/purpose/plan/SQL/OS继承边界不扩权；新20→21必须独立purpose、完整raw pins、backup及isorestore约束与原Owner/native证明。缺该资源只阻塞原根应用，不阻塞隔离Source实现。
- 历史程序bootstrap生成的私密credential只由其合法runtime使用；本研究不读取私钥、原trial凭据或provider材料。

## 8. 已齐/仍缺与后续分工
| 支路 | 已齐 | 未闭合 |
|---|---|---|
| 历史20资源 | commit/tree、真实1..20和旧DDL blob、control/backup源码、Go锁、必要embed；既有capsule报告19个expanded module存在 | 实际compiler/embed/依赖checksum闭合、Windows binaries及真实launch IO；8个zip缺席不能等同依赖缺失。 |
| A型source20 | 历史公开建库代码路径明确 | 真实程序建库schema/rows/owner存在证明、matching encrypted backup和独立restore/rollback实际结果。 |
| B型旧session | 原旧DDL和LEG2 fixture可用于精确source测试 | 独立实际安装来源/原数据shape；没有来源的B只保持fixture标签。 |
| 新20→21 | 原0021、现有backup/restore/锁/行比较模式、上面build-ready边界 | 固定产品plan、production dispatch、A/B shape策略、显式additive及无损不变式实现和独立接受。 |
| 21接22 | 现有固定queue source21模板及hash可审查 | 与新20→21产物相等的真实target21 release/program/启动兼容性；不能修改旧模板掩盖。 |
| 22→23→24 | 既有固定Source入口 | 各自匹配release roots/programs与逐跳实际演练、历史21/22/23 trigger兼容和最终普通启动/业务路径。 |
| 原根或实例切换 | 既有规则和23→24特定native设施 | 新20→21原根专属authority（若选择此支路）/最终单写入切换证据。 |

优先安排后续独立实现者完成新固定plan Source，同时Root可继续轻量历史源码资源/真实构建准备；本报告不创建worktree或执行任何程序。目标始终为合法历史全链，ordinaryhistory20/full Release/program rehearsal仍保持未通过。

## 9. 本轮证据
71个输入及32个历史blob独立核对，完整选定source副本、初末guard、路径行锚点和原工具IO随包保存。capture4608be outer/Python0，未运行Git/Go/SQL/native/model，未读私钥，未改Main/canonical/旧Source。
只读路径错误895：67e86c中误猜不存在T9/ops/recovery_root；outer0，Python/nativeNULL，rg子退出未独立捕获，不补造。原返回因工具输出预算截断，按原样保留；随后通过真实枚举定位ops/supervisor/recovery_root/main_windows.go。h20read6末尾rg无K章节匹配的exit1只是负搜索结果，不冒称工具故障或规格缺失；Root已说明K是目录别名。未删除历史失败或重置计数。


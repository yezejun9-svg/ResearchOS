# A21 session 初始化与既有 21→22 接续合同

结论：在本次固定的生产 Source 范围内，没有一个公开命令能够把已有权威数据的 pure21 库合法补成 session-initialized21。H20R1 已接受的 A20→21 Source 不应重开审查；需要新增的是明确的 session 初始化及恢复态接续合同。仅补 session 还不够：H20 输出带有 `backup_require_fresh_observation`，而既有 21→22 的源模板不含该 Run 恢复触发器，因此仍会被严格 schema hash 拒绝。

这是只读 Source 结论；未执行 Go、SQL、Git、Native 或模型，也未运行任一历史程序。本报告没有签发产品、Owner、正式验收或全链接受。B 型旧 session 扩展分支单独 OPEN。

## 1. 固定输入与范围

本次复用原 [H20 合同报告](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/historical20_upgrade_contract_readonly_codex/h20-contract-20261009-source-review/report.md) 和 [资源来源报告](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/historical20_resource_route_readonly_codex/current_target_actual_review_01/report.md)，不重复提出已实现的 A20→21 dispatch 缺口。当前 H20R1 资格来自 [非作者 Source 接受](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/historical20_upgrade_source_independent_review_codex/h20r1-20261009-source-review/HDF.json)：`SOURCE_ACCEPTED_PENDING_ROOT_RUNTIME`。

生产路径调查覆盖固定 T9 worktree 的 `internal/domain`、`internal/host`、`internal/api`、`apps`、`ops` 共 245 个非测试 Go 文件，并固定当前 SQL、H20R1 候选、历史 capsule 和相关测试来源。本次 377 个输入、476 个静态检查全部通过，30 个选定历史文件的 Git blob SHA-1 和 SHA-256 均一致。这里的“无公开入口”限于这些已列出的生产调用路径，不是假定整个产品或所有历史版本均不存在其他入口。

精确文件 hash/bytes 见 `input-pins.json`；调用位置见 `production-reachability-scan.json`；完整关键函数及行号见 `source-anchors.json`。未复制原资源树，未持有或修改 canonical。

## 2. 已有入口为什么不能完成 A21 安装

| 已有路径 | 实际作用与拒绝点 | 对本次 A21 的结论 |
|---|---|---|
| current control → `NewCurrentMu` → `New` | [control:104](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/apps/control/main.go:104)，[New:54](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/store.go:54)。先检查版本清单和 `CheckMigrationSafety`，之后才开启业务迁移事务、执行未编号 session DDL 与 `installClientSessionFence(false)`。 | 有权威数据的 21 库配当前 24 清单，先因 21≠24 拒绝；即使使用真正匹配的 21 清单，缺 session shape 仍先拒绝。不能把 New 当作已获授权的迁移器。 |
| host API / session UI / CLI | [Host.New:149](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/host/host.go:149) 同样调用 NewCurrentMu；[cliInit:322](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/apps/cli/cli_contract.go:322) 使用 host discovery、workspace register 和 project.bootstrap。`session.create` 最后调用 MapClientSession 插入数据行。 | 都依赖已经成功启动的 host；CLI init 不是历史 DB 建库器，创建 session 行也不是安装 schema。 |
| `EnsureClientSessionFence` | [client_session_fence.go:19](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/client_session_fence.go:19) 转到 `installClientSessionFence(..., true)`；当 client_sessions 缺席时立即 no-op。true 分支会按活跃 Run 为已有 session 更新恢复 barrier。 | 不创建缺失的 client_sessions；不是一个公开 standalone 安装命令，也不能用 restored=true 冒充普通初始化。 |
| backup restore | [backupFence:216](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/backup_recovery.go:216) 安装 Run 恢复保护、撤销凭据并对账；它只调用上述 Ensure。 | pure21 恢复后仍无 session，却新增恢复态。普通 restore 不是补装入口。 |
| 既有 `backup upgrade-local --plan schema21-to22-client-command-queue-v1` | [upgradeQueueLocal:320](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/backup_queue_upgrade.go:320) 在制作快照前要求源版本 1..21 和完整源 schema hash。 | 拒绝缺 session 或含额外 Run 恢复触发器的源；不能让它先修复再校验。 |
| 测试里的 source21 fixture | [queueUpgradeFixture:67](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/backup_queue_upgrade_test.go:67) 先以当前 New 创建无权威数据的 21 fixture，再写入 Owner。 | 可验证固定模板施工行为，不能证明历史21公开安装来源或已有 A21 库迁移。 |

[migrationAuthorityPresent:107](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/backup_migration.go:107) 检查所有非 SQLite 系统表，只跳过 schema_migrations 与精确的 resource_write_lock 结构种子；Owner/auth 行、已撤销的凭据、恢复 barrier 都算权威数据。因此“没有 Project 就先启动一次”也不能绕过该门。普通路径的拒绝发生在 domain DDL 前；底层 store.Open 已可能选择 WAL，不能把一次启动尝试描述为全程零文件副作用。

历史 commit `3225a31fd25969c6a5e071a2fc686cb4a835e162` 的 [control:81](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/historical20_resource_route_readonly_codex/current_target_actual_review_01/historical-source/apps/control/main.go:81) 调 Bootstrap，再调用历史 [New:34](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/historical20_resource_route_readonly_codex/current_target_actual_review_01/historical-source/internal/domain/store.go:34)。其 New 仅执行编号 SQL，没有 next_v24_sessions 或 session fence 安装。capsule 中存在旧 additive 文件并不证明该公开 constructor 曾调用它。这个事实保持成立；本次未宣称已实际运行历史 CLI。

## 3. 既有 source21 模板到底包含什么

[upgradeQueueTemplate:64](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/backup_queue_upgrade.go:64) 的顺序为：实际执行原 1..21 SQL → 当前 `next_v24_sessions.sql` → `installClientSessionFence(false)` → 取 `before` schema hash → `backupFence` → 0022 → 取 target hash。

未编号部分的精确组成：

| 对象 | 来源与约束 |
|---|---|
| client_sessions | 固定 [next_v24_sessions.sql](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/migrations/sqlite/next_v24_sessions.sql)，SHA256 `1ca3930f96f7c2c99e7bc6e668dd5658393264cf1e6bf6352b47fb3de8c7dfe3`。24 个声明列，含 nullable transcript_artifact_id；revision/writer_epoch≥1、event_watermark≥0、writer/upstream 非空、固定 protocol，以及其他原 CHECK。A 初始化产生空表，不创建 session/epoch/lease/log 内容。 |
| client_sessions_run | 原 SQL 的 partial unique index，run_id 非 NULL 时唯一。 |
| backup_restore_barriers | fence helper 创建的 `(project, run)` 主键表，restored_at 非空；普通 false 分支不插入/刷新任何 barrier 行。 |
| client_session_epoch_no_regression | 禁止 writer_epoch 回退。 |
| client_session_require_fresh | 当 epoch 前进、Run 仍活跃且存在 barrier 时，要求晚于 barrier 的 children_stopped+queue_empty 观察。原触发器字节保留，不重新解释为人工布尔批准。 |

对旧表的 `ALTER TABLE ... ADD COLUMN transcript_artifact_id` 仅是 fence helper 兼容能力，不等于本次允许 B 分支；A 的新表已经含该列，不能以 IF NOT EXISTS 给未知半装 shape 放行。

以上 DDL 不写 schema_migrations。新 session-only 阶段必须保持真实的 1..21 账全部行与存储类型不变。0022 迁移仍只能在其受控事务成功时新增唯一版本22；禁止插入“additive版本号”或重造旧1..21账。

## 4. 第二个接续阻塞：H20 恢复态不等于旧 source21 模板

令 `N21` 表示原编号 1..21，`S` 表示上表 session DDL、barrier 表和两条 session trigger，`F` 表示 Run trigger `backup_require_fresh_observation`：

| 形态 | Source 定义 | 旧 21→22 源校验 |
|---|---|---|
| 裸编号 pure21 | N21，无 S/F | 缺 S，拒绝 |
| 原 source21 template | N21 + S，无 F | 正是旧入口要求的 shape；这不证明存在合格历史 release/program |
| H20R1 恢复产物 | N21 + barrier 表 + F，无 client_sessions | 缺 session，且含 F，拒绝 |
| H20 产物经合法 session 初始化 | N21 + S + F，保留恢复行/Run 保护 | F 仍使完整 schema 不同，拒绝 |

这是 Source 顺序推导，不是 SQL 实跑结果。H20R1 [upgradeHistory20Template:59](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/historical20_upgrade_source_codex/h20-r1-root-1791519270000-scoped-check/candidate-root/internal/domain/backup_history20_upgrade.go:59) 在 backupFence 后执行0021并取 target hash。backupFence 无条件建 Run trigger；24 个当前编号文件均未包含这个触发器。旧 queue template 的 source hash 则在 backupFence 之前取得。

[backupSchema:156](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/backup.go:156) 对整个 sqlite_master 的 type/name/tbl_name/SQL 排序计算 hash，并不忽略恢复 trigger。故即使 barrier 当前没有数据、Run 全部终态，额外 F 仍是 schema 差异。清空行不能消除该差异，也不得通过 DROP TRIGGER、清 barrier、改旧模板或比较时投影忽略 F 来制造接受。

同类风险延伸到下一跳：当前 [upgradeConfigurationTemplate:72](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/backup_configuration_upgrade.go:72) 也在 backupFence 前取 source22 hash；旧 queue 的恢复 target22 带 F。因此本报告不把一个新21→22分支完成解释为22→24已闭合，后续恢复态接续仍应独立定义。

## 5. 建议的下一份 production Source 边界

下面是新设计建议，函数名/plan ID 尚不存在，也不是产品接受。

建议新增独立的 `H20-restored21 → session-initialized restored21 → restored22` 固定 coordinator，挂到现有 `backup upgrade-local` 的新 plan 分支，保留已接受 H20R1、旧 queue source21/target22 模板及所有原 SQL。单独写一个 session installer 可以成为第一片实现，但其输出必须明确为 restored21，不能承诺旧 queue 入口立即可用。

| 阶段 | 最小输入与允许变化 | 必须拒绝/保留 |
|---|---|---|
| 输入资格 | 明确绑定 H20R1 的 source/target release、candidate DB 精确 schema/typed-row digest、1..21真实账、备份目的/格式/MAC、原先隔离恢复 receipt。源是 A 恢复态，client_sessions 缺席，F 与 barrier 为精确已知形态。 | 未知额外对象、仿造报告、任意 SQL、任意 target version、B/半装 session 表、删账造旧、把当前库截短伪装历史版本。不能仅信任用户提供的 JSON status。 |
| 离线 snapshot/restore | 源 DB 和 release/program 在受控独占范围内，备份 key 分离、目标不预先存在；沿现有 local-upgrade format 和固定 purpose 验证真正可解密/可恢复快照。若再次执行 restore，单独记录其凭据撤销、Run/effect/audit/barrier变化。 | 不把第二次恢复的 row delta 混进 session DDL 的“旧行不变”证明；不把普通 portable backup 与 plan snapshot 混为一物。 |
| Session 阶段 | 在未发布候选事务中执行精确当前 additive SQL，再 `installClientSessionFence(false)`；验证空 client_sessions、固定 index/两 trigger、原 F/barrier完整保留。整个旧1..21账及旧表 typed rows逐项不变。 | 不调用 New；不生成 session/credential/Owner；不刷新已有 barrier 时间；不运行调度或外部动作；失败不发布、不补写版本21。 |
| Queue 阶段 | 以新的固定 restored21 profile 独立验源后，可复用现有 `upgradeQueueMigration` 的固定0022 hash/唯一版本22/旧行不变/四张新空 queue 表/完整性与 FK 检查。新的 coordinator 和恢复态目标模板单独 Source 审查。 | 不能直接调用旧 upgradeQueueLocal 并跳过它的失败；不能变更旧 source21 template 以吞下 F；不能用“恢复成功”授权切换。 |
| 输出与发布 | 单独记录 Recovery、Session、0022 三个阶段的输入/输出 hash、执行边界、无外部动作及 preserved F。输出仍为隔离恢复态候选，后续22→23→24、Owner/正式切换 OPEN。 | 未运行的 SQL/CLI/build 不写 PASS；不得删除稳定备份、旧程序或原数据；不得自动启用双写入实例。 |

建议 Source 范围是一个新的专属 domain coordinator 文件、对应源码/真实程序边界测试、一个窄 `UpgradeLocal` dispatch、CLI plan help，以及确实需要时的专属 backupPolicy hook。旧 plan 分支和模板不改；共享 backupPolicy 扩展只能接受该固定 purpose/profile，不能新加通用“忽略 schema/已有备份”开关。

最小测试合同应证明：真实 A restored21 被识别；未知 schema/B/半安装被拒绝且未改输入；session 阶段无ledger/旧typed rows变化；保留 F 的产物继续被旧 queue 拒绝；新恢复态 handler 能验证其独立 profile；任一 DDL/检查失败回滚未发布副本；重复调用不重放成功账；有效 key 正控制与错误 key 负控制使用同一用途/同一快照。以上均为待实现、待真实执行的验收条件。

## 6. 20/21/22 release 与备份恢复资格

已有 release validator 验证精确 SQL/contract/additive 文件，coordinator 对 source/target program 读取并计算 hash；[queueLocal:372](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371/internal/domain/backup_queue_upgrade.go:372) 没有执行这些 program。故 program hash 不能代替 executable provenance 或 matching backup/restore 演练。

| 资源 | 所需证据与本次边界 |
|---|---|
| 真正历史20 | commit/tree/blob、go.mod/go.sum、工具链/编译器输入/依赖与 embed、实际构建出的 control/backup bytes和命令退出；真实历史 control `--bootstrap-owner` 创建 A20，证明账1..20且无 session；使用匹配程序形成一致性加密备份，并在隔离空根实际恢复。当前已有capsule Source可用，不替Root宣称这些runtime动作完成。 |
| pure21及session-ready21 | 来源必须明确是新H20候选及合法新安装步骤，而不是当前24截短/删账。需要读写范围真实支持该21形态的匹配release/program、完整1..21原SQL/contract、session前后各自manifest和固定additive/fence Source。若没有真实历史21发行物，可以另行设计并审查“新兼容维护release”；必须如实标明新来源，不能称历史21，普通host业务可运行性仍须另证。 |
| 22目标/接续源 | 固定1..22、原0022 SHA256 `e2abcc078bbac1c076736a40249d50c85e25b4c8fd93e975f8528f8f8277abcd`、当前additive与相应contract，实际program build/runtime记录。恢复态target22与下一跳source22差异必须显式解决，不能修改既有模板。 |
| 每跳 backup/restore | 原实际输入形态+唯一plan/purpose+稳定加密快照+正确key正控制+错误key负控制+MAC/content验证+隔离恢复+schema/typed-row差异+失败回退记录。WAL一致性、workspace路径/同主机身份、protected引用边界、外部动作对账和单写入切换沿原合同；一个本地 JSON“批准”不构成这些资格。 |

这里的“匹配”必须精确说明匹配 schema、合同、additive形态、保护/恢复策略和程序，而不是只匹配MAX(version)。没有合格21程序时，可以继续Source/隔离构建工作；不能据此签发正式全链或Ownerflow。

## 7. B 分支与审查证据

B = 真1..20 + 原旧 session扩展，仍独立 OPEN。旧 DDL hash 为 `3b00677902c3be1dbffb8f7505293bae7242dc976e8017562ab86254ac212f2a`；旧 helper/LEG2 synthetic fixture 不能证明公开安装 provenance。不得把B数据库转称A，不清 session/epoch/lease/log，不借 nullable transcript扩列能力自动接受B。A的新固定分支应明确拒绝B或交给单独合同。

本轮两个机械诊断原样保留：907=`00d0b2`，误猜resource目录；910=`056ade`，误读非-scoped-check父目录HDF。两次都是一个原始调用中的非终止 PowerShell 路径错误，outer0，Python/native均NULL，不拆计数。908/909属于其他审查，未据旧next抢占。后续capture `9d8640` outer/Python0，所有377输入的guard已验证并关闭、retained handles=0。`original-tool-io.json`保留完整原工具返回，其中`a21Read8`原返回已被工具截断；后续结构化capture和独立小范围读取补足所需Source，而不伪称原返回完整。

STOP。交付仅为本次新命名空间下的研究合同和可复核证据，没有写产品/candidate/Main/canonical，也没有替Root作产品或Owner判断。

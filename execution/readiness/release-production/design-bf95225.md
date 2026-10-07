# W16 / W20 最小发布施工设计

状态：`DESIGN_READY_NOT_IMPLEMENTED`。审阅源码 `bf952254d9d9e0d80e888bd1a771606e4e333955`。仅输出本 Markdown 及同名 JSON；未修改源码、测试、迁移、账本和规格，未运行程序/服务，未读取凭据、产品数据库或受保护正文。采用 Ponytail 的复用原则：已有 domain、备份恢复、实验、权限 sandbox、命令登记和 Windows SCM 足够，不再引入发布平台、第二调度器或通用升级框架。

## 先说明不能由本设计补齐的条件

- runtime S2 的正常执行、当前资格、单实例锁、effects/reconcile 与可信 worker bridge 尚须实现并独立接受；真实 Codex 仍受 `RQ-W05-CLI-POLICY-001` 阻塞。本设计不能取得模型/工具资格。
- W16-G01 要 W18 阶段已接受且 A12 恢复资格当前有效。现有 `execution/verifier/W18/formal-be03d90d-fd7d-49b8-aa28-98813a37eebc/review.json` 为 A12 PASS / W18 两 gate PASS，但明确 `stage_accepted=false`、限定版本与外部依赖；不能把它扩展到后续 schema、程序和生产数据。
- 真实独立 Windows 服务身份及 SCM/ACL 安装权限、发行信任根、独立 Verifier 签名/身份、clean Windows 用户或 VM 的可用性都未在此次确认。只能列为正式配置前提，不能虚构已存在的账户、证书或 VM。
- W14 真实基线、当前有效 W12/W15 能力、C20 冻结留出结果、W19 隔夜资格、最终 11 页真实接口集成及其余 41 个正式用例尚需各 owner 的有效证据。固定四题公开 suite 不是真实留出，当前用户新目录不是 clean Windows。
- 主产品旧 schema13、隔离 schema14 数据副本和 schema14 activation 的 policy 拒绝保持不变。源码目前包含 15 个迁移；runtime S1 后续编号及最终发行 schema 尚未锁定。此次不核验、不启动、不迁移这些产品数据。
- protected broker 79136 保持冻结 30 calls，不调用、不重启。受保护引用继续只依赖原外部服务；发行包、备份和 clean 目标不携带其正文、密钥或复制身份。该服务的同机引用连续性不是跨机可恢复性。

## 1. 冻结契约与源码证据

| 精确锚点 | 意义及施工约束 |
| --- | --- |
| `spec/v2.0/05_WBS.md:984,1011,1096,1204,1232` | W16 依赖 W12/W14/W15/W18；W20 依赖 W16/W19；W20-G01 先检查其余 41 例，再独立接受 A15 补为 42 例 |
| `spec/v2.0/06_ACCEPTANCE_TESTS.md:819,1689,1727` | C20 要双 rubric、冻结 holdout、拒绝晋升及收益表；A15 clean Windows/实际安装/41→42 索引/11 页集成；A16 独立身份、实际回退、三个故障候选及不终止全部任务 |
| `spec/v2.0/07_OPERATIONS_AND_EVOLUTION.md:13,117,143,151` | supervisor 不研究派单；active/candidate/last_known_good；候选先用隔离 DB；正式 canary 串行切换唯一 control，不并行抢生产 DB |
| 同文件 `:156,162,164` | 成功 canary 至少 1 个真实周期且 ≥6h，24h 未满足不得扩大；ready 120s；关键健康连续 3 次失败且持续 ≥30s；失败独立回退/冻结 |
| `internal/domain/evolution.go:30,63,118,152,237` | host、build、artifact、experiment 都是 fixture 限定；只允许固定 fixture changed-path manifest；PROMOTE 无条件 503 |
| `internal/domain/evolution_execution.go:189,429` | 已有 Run/lease/phase reservation、W10 实验、W12 effect、W18 backup/restore、真实 native health；canary 仅临时副本并必然返回 stable |
| `internal/domain/evolution_acceptance.go:27,97,138` | 已有原始结果重算、精确 build/suite/policy/candidate/task/run/epoch 绑定、独立 acceptance 和 current policy 检查；mode 为 FIXTURE |
| `migrations/sqlite/0015_evolution_fixture.sql:1` | 七张 evolution 表、不可变 plan/receipt/journal 和防重派 trigger 可复用；`evolution_slots` 是按 project 的 fixture 状态，不能变成实例发布唯一事实 |
| `ops/supervisor/fixture_windows.go:3,40,75,84` | 开发 host 明确非独立 OS 服务；AppContainer 真执行、raw hash 与 required regression 可复用；1.5s 试验不证明正式观察窗 |
| `evaluation/evolution/suite.go:14,61`、`ops/canary/fixture/main.go:16` | 公共固定四题、self-score 无权威；已有 gain/no-gain/regression/tamper/startup/hang 程序，是机制测试材料 |
| `internal/domain/backup_upgrade.go:21,52,152,233,366,766` | 只支持 exact `schema13-to14-remote-access-v1`；SQL/源目标 release/hash/外部引用绑定及恢复不变量，不是任意 SQL runner |
| `internal/domain/backup_migration.go:13`、`store.go:34` | populated DB 缺迁移即拒绝启动；不能用环境开关绕过 prebackup guard |
| `apps/control/main.go:48,58,61,127` | dataDir 可配置；spec/migrations 仍相对 cwd；只启动 HTTP；生产 supervisor/SCM 生命周期和发布包根校验尚未实现 |
| `ops/ci/build.py:31,44`、`execution/commands.json:1344` | 已有锁定 Go/web build，但输出只有开发 control；`release.reproduce` 与 `acceptance.audit` 仍 UNBOUND |
| `execution/toolchains/locked.json`、`go.mod`、`apps/web/package-lock.json` | 已有固定工具/依赖；路径是开发机绝对位置，clean 目标须受控重绑定，不能原样当便携路径 |

当前 W16 独立审阅 `execution/verifier/W16/evolution-881e42e/review.json`：G02 PASS_IN_FIXTURE_SCOPE；C09/C10/C12 PASS_IN_FIXTURE；C20 PARTIAL_EVIDENCE，A16 PARTIAL_FIXTURE_ONLY，W16 未接受。保留这些结论；新机制增量不重新命名旧证据。

## 2. 最小边界：一个 supervisor、一个业务 control

用现有 `golang.org/x/sys/windows/svc` / `mgr` 和 Windows SCM 实现两个身份，不增加依赖：稳定 `ResearchOSSupervisor` 服务使用专属受限 service identity；`ResearchOSControl` 使用不同受限身份。准确服务名/SID 在正式安装时登记，本设计名称只是施工建议。SCM 负责 supervisor 崩溃后重启；supervisor 只管理版本、健康、单实例及恢复，不调度研究 Task。

control 服务的 SCM ImagePath 指向不可由 control/candidate 写的固定 launcher。launcher 在 control 身份下读取 supervisor 签发/保管的 active descriptor，校验 immutable release manifest，启动 exact control.exe，绝不能让 candidate 以 supervisor token 运行。supervisor 仅获得指定 control 服务的 start/stop/query 权限；修改 SCM 配置、安装/卸载服务和变更信任根属于独立维护授权，不授予 candidate。installer 不沿用开发用户目录的宽 ACL。

安装根建议拆为：只读 `releases/<manifest-hash>/`、supervisor-only `supervisor-state/`、control 可写 `data/`、candidate-only staging、独立受限 encrypted backups。candidate/研究 worker 不可写 launcher、supervisor.exe、release manifest、slot descriptor、baseline suite/labels、签名公钥集合、发布权限和通过标记；也不可服务控制/改 ACL。服务目录 ACL、服务对象 ACL、命名管道 ACL 都要实际测试，不能用角色名替代 OS 隔离。

**关键区别**：正式 canary 的 control 程序会按其职责写业务 authority DB，因此数据库里的 `PROMOTED`、AcceptanceReceipt 或 release principal 本身不能抵御恶意 control 自签。独立 supervisor 不把 candidate 可写 DB 当发布授权源：切换前封存由稳定侧与独立 Verifier 提供的 exact admission bundle；切换后只接受已登记独立 Verifier 身份签发、绑定观察结果的 attestation，结合自己采集的进程、健康、时序和完整性证据。缺少该外部独立验证身份时，只可进行有预授权的有限失败演练，不可自动晋升。

最小信任策略遵守冻结“签名/来源策略”：发行内容每项 SHA-256，加 source commit/依赖锁/构建 manifest；安装时由独立维护身份批准并保护的 allowlist 是第一版来源根。需要跨机发放时可用 Go stdlib `crypto/ed25519` detached signature，公钥 fingerprint 预先受控登记，私钥不进发行包和 control。自带一个公钥再自签包不构成信任。每次加载重验 hash/来源策略，拒绝 TOCTOU/reparse/路径替换；复用 W18 native file identity 检查思路，而不是只验一次文件名。

## 3. 最少持久状态，不建第二调度系统

业务仍只用现有 authority DB 的 SystemCandidate/Experiment/Task/Run/AcceptanceReceipt；保留 `evolution_candidates/tasks/executions/journal/builds` 的 exact bindings 和 terminal/no-rotation triggers。fixture host 及 API 保持原语义，另设 trusted production host registration，登记实际 OS SID、supervisor build/profile 和来源/验证策略；绝不把 `os_service_qualified=false` 改成 true 就解锁。

建议 **最多一张新增私有业务表** `evolution_release_operations`：`(project,candidate,action)` unique，operation_id unique、expected slot epoch、frozen admission hash、effect key、请求状态、supervisor receipt digest、结果投影 revision。它承接跨进程调用和幂等收据，不存新 Task 队列。注册/信任/签名摘要可放现有 immutable `evolution_hosts.body` 和密封 Artifacts；若后续发现需要多个 host revision，新增 immutable host registration key，而不是覆盖旧 fixture host。

真实发布 slot 以 **每个安装实例一个** supervisor-owned durable journal/原子 descriptor 为准：active/candidate/last_known_good release hash、data-generation locator、slot epoch、operation id、phase、expected schema range、backup/ref、进程 PID+creation time、receipt hash、canary start/deadline/last observation/covered duration、停机 drain fence、freeze digest set。使用 append-only journal、flush + 同卷原子替换、checksum/序号，损坏/不完整时 fail closed 并读 journal 恢复；不靠候选 DB 启动成功字段。它是部署机械事实，不是第二业务 authority。

域 DB 的 `evolution_slots` 继续 fixture 用；正式 slot 是 supervisor 事实的只读投影。镜像落后不触发重新切换。supervisor 返回幂等签名/来源绑定 receipt 后再更新域状态；HTTP ACK 丢失读 operation receipt，不能重新发切换。数据库表与文件 journal 无分布式事务，靠先记 intent、稳定 operation id、epoch CAS、幂等结果和 restart reconcile 衔接。

迁移编号由 root 在 runtime S1/S2 及其他 worktree 整合后串行分配。本设计不指定 0016/0017，不修改既有 0015。

## 4. 从候选到真实有限 canary

1. **封存输入**：复用 `evolutionPlan` 与 normal Task/Run 接受，绑定 candidate/stable 整包 hash、源 commit、changed paths、suite/labels/rubric/hash、同样本版本、模型实际解析版本、输入/结果 hash、metrics/退化阈值、预算、权限 profile、migration/rollback plan、supervisor 身份。candidate 提议基线变化另开 ChangeProposal；当前候选仍用旧基线验。没有收益或必需回归失败则 REJECTED，不切换。
2. **隔离回归**：runtime S2 用真实权限边界启动 candidate，对 DB/objects snapshot 的独立副本执行 regression/replay；禁止生产外部副作用，或使用明确已授权的测试资源。复用 W10 预注册与结果重算、W11 当前适配资格、W15 当前技能版本。固定 fixture suite 仍只做机制回归。C20 双 rubric 需分别保留，在相同 outcome 上不能直接比较新旧分数作为增益；冻结 holdout 的独立结果未提供时结论保留 INCONCLUSIVE/NO_IMPROVEMENT，不杜撰标签。
3. **发布准入**：在 `actSystemCandidate` 生产分支校验当前独立 RELEASE_SERVICE、project grant/root 与作者/执行者分离；独立接受 receipts exact/current、W18 整阶段/A12 exact restore qualification、runtime/worker 当前资格、W14真实baseline、W12预算/未决effect、无冲突、W15适用资格、被测 hash=将启动 hash、冻结迁移/恢复策略。supervisor 再验证独立 admission bundle。任一未知保持 503/现有 gate failure，不能删除 PROMOTE guard 通行。
4. **安全排空**：stable control 停新领取与新外部 effect，保存游标/窗口/checkpoint，安全排空或明确停止 workers，记录实际停止与未决费用。不可中断的任务尚未处理则不切换。S2 的 data-root lock/worker identity/effect reconciliation 是这里的前置；不能用停止 HTTP 当已停止后台任务。
5. **备份及切换**：核验当前 last-known-good 程序与数据兼容范围并做升级前加密备份。supervisor 先记 PREPARED，停止旧 control，确认锁释放/旧 PID 已停止，再原子选择候选 release，唯一 control launcher 启动候选。新 control 必须持相同实例锁、匹配 slot epoch/build/数据格式；不得同时启动两套调度器。
6. **白名单限制**：canary 只对明确白名单 ResearchOS 自身项目允许一个真实研究周期及规定只读来源/受限实验；其他项目只读，暂缓派单。在独立 host broker/runtime 准入侧也强制这组 scope，不单信任可能恶意的 candidate UI/DB。业务继续点与原 Task/Run 身份保留，不新建 Goal 掩盖中断。
7. **观测**：ready 默认 120s；关键健康连续 3 次失败且持续至少 30s触发回退，critical invariant/泄漏/错误采信/预算越权即时触发。采集 supervisor 实测进程、HTTP/DB 不变量、真实周期回执、effect 去重/成本、独立结果与预注册性能区间；候选自报只是输入。成功要求 ≥1 完整真实周期且连续有效观测 ≥6h；24h 仍缺证据停止扩大，按冻结 plan 留待证明或回退。重启/掉观测不虚增覆盖时长，时间倒退 fail closed；负向即时故障演练不抵扣成功窗。
8. **PROMOTE**：独立 Verifier 对同一候选/epoch/窗/样本/结果/全部硬门签发接受；supervisor 再校验 current grant/revocation/资格及 now/deadline 后更新 stable 与 last-known-good，恢复其他项目派单。不能在一个长 DB 事务里等 6h。public action 只使用冻结 CandidateActionRequest 和 SystemCandidate 响应；pending intent 留原 EVALUATING/CANARY，get/event 显示实际完成，不提前标 PROMOTED。

## 5. 独立回滚及重启恢复

回滚不调用坏 control 的自救代码。supervisor 撤销新派单/egress 授权、停 candidate 与 workers，记录晚到 effect/成本，保留原始故障和数据。允许旧程序读写当前数据格式时，只切回已核验的 last-known-good 程序；不兼容时只执行事先演练过的维护窗口恢复计划。存在无法保留的 canary 期间写入或未决 effect 时，冻结写入进入 RECOVERING，不直接覆盖活跃 DB。首个最小正式 canary 限定 **无 schema 变化、经证明双版本兼容的系统改动**；schema13→发行版本升级是独立升级计划，不能顺便混进首个候选。

实际回滚完成的判据：启动 exact 旧包 hash、实际数据/inventory 与冻结恢复计划一致、health 实测通过、原任务/checkpoint 可续接、effect 不重发；随后域 receipt 才置 ROLLED_BACK。故障候选 digest 在 supervisor 的 freeze set 持久保留，同时同步 SystemCandidate；同一 digest 改名/新建候选/重启不能绕过。新修复版本与独立新证据可按规定重新准入。

| 中断窗口 | 恢复动作 |
| --- | --- |
| 已登记 intent，尚未停止旧 control | 核验 slot epoch、PID 创建时间、实例锁；旧 stable 安全存在则保持它，不能重复发动作 |
| 旧 control 已停，pointer 未切 | 从 journal 恢复到已知 stable；校验数据 fence 后启动一次 |
| pointer 已切、启动 ACK 丢失 | 用实际进程 build/creation time/epoch 检查；不双启动 |
| candidate 挂死/崩溃、领域 DB 不响应 | supervisor 本地 journal/包/备份仍可读；独立停止和回退，不依赖 candidate API |
| supervisor 自身崩溃/OS 重启 | SCM 恢复 supervisor，先 reconcile 再启动/继续；没有完整成功观察证据不自动晋升 |
| 回滚中途、数据不确定 | 冻结写入，读取已持久化阶段与 W18 恢复回执；绝不让旧二进制开不支持的格式 |
| 外部效果未决 | 保持 UNKNOWN/原 key、归原 Run/epoch，按 S2 对账；回退版本不能重复发请求 |
| 回退已完成、domain ACK 丢失 | 只重投既有 signed receipt，域幂等补投影；不再次切换 |

健康不佳若可归因为 provider 欠费/限流，走现有 ResourceRequest，不用循环升降版本掩盖。candidate 不能写 supervisor freeze set、时钟观察区间或“验收通过”标记。

## 6. 先把可交付物做成一个真实包

第一版选 **本机 Windows x64 ZIP + 明确脚本入口**，不承诺 MSI/商店安装/自动下载更新。复用现有 Go build、Vite、bootstrap 工具校验与命令 registry；补一个 release 脚本，不将 `ops/ci/build.py` 全量测试/下载逻辑当 installer。

包内最低内容：

- `bin/control.exe`、`runtime.exe`、`backup.exe`，第二切片加入 `supervisor.exe` 和固定 control launcher；所有会在正式命令中调用的 CLI 明确列入 manifest。
- 锁定 `spec/v2.0` 的完整只读 manifest、冻结 contracts、exact `migrations/sqlite`、`web/dist`、真实 `execution/commands.json` 及被它声明的脚本/运行前提、配置模板、启动/停止/禁用/保留数据说明。
- `release-manifest.json`：package/build id、source commit、每文件 hash/size、构建参数/平台、tool versions/hashes、Go/npm locks、adapter/model 已知版本或缺口、API/schema hash、数据库支持读写范围、唯一 pinned upgrade plan、rollback 条件、SBOM/license、验收 evidence 索引和已知阻塞。外层 archive hash 存在独立 receipt，避免 manifest 自引用散列。
- 无密钥 SBOM/许可清单由 `go.mod/go.sum`、npm lock、实际编译模块和已下载依赖 LICENSE 构成，记录完整依赖版本/完整性/许可证；不联网补猜。缺 license 文本/未知来源必须保留发布缺口。构建输入与归档遍历排序、时间戳固定；先以重复构建比较证明可复现，不预称 bit-for-bit。

工具锁当前记录 Go 1.27.1、Node 24.9.0、npm 11.6.0、Python 3.14.3；这些是读到的锁值，本次未执行验证。clean target 安装预编译服务不要求 Go/Node；源码复建/执行 Python 验收脚本需要精确工具，提供受控获取/本地离线包的 hash/许可或明确先决条件。不可把开发机绝对路径塞到新机 PATH；用 root-relative tool binding 经 hash 校验后登记，`GOTOOLCHAIN=local` 保持，缺工具非零报错。构建期下载不由普通研究任务触发。

不要为裁剪体积删掉 commands 中声明的必要脚本：实际运行入口可只需 exe；development/acceptance 命令须附源码/脚本或独立 source/evidence companion 并准确标 required tools。UNBOUND 保持非零 NOT_IMPLEMENTED，不用 fake wrapper 通过 A15。只发布 allowlist 路径，排除 `.local`、凭据、auth home、真实 DB/备份、私有证据和绝对用户路径；验收索引用安全元数据引用，受保护证据仍在原 store。

启动最小改动是 `--release-root` 或 launcher 固定 cwd，统一让 control 读取包内 spec/migrations/web，dataDir 必须独立；校验 manifest 后才开 DB。复用 runtime S2 单实例锁，禁双开/不兼容 DB/端口冲突。fresh empty data 可正常初始化；populated DB 始终经过 `CheckMigrationSafety`。stop 经 S2 停领取、checkpoint、effects/outbox flush；脚本等到真实进程结束才回报。禁用/卸载只移除本次服务登记与包，明确保留 data/backups/证据；不递归删除用户根目录，不在未授权时清理项目数据。

## 7. 必须新增 exact 13→最终发行版升级计划

`upgrade-local` 的 13→14 是特定 release 的证据，不能把 `14` 改成 `len(migrations)`。保留 `LocalUpgradePlan`、所有 13→14 hashes、native path/identity guard、protected reference continuity checks、测试及失败语义。新增一个 **编译内 allowlist 的具体计划**，暂名 `schema13-to-release-<build_id>-v1`；最终版本、每个 SQL/hash、source/target schema fingerprints、程序 hashes、支持读写范围、row-level invariant 和恢复 fence 均待 root 锁定。若确需以现有隔离 schema14 为源，另立 exact 14→该版本计划，不用“任意起点”参数。

复用现有 `upgradePaths`、native exclusive source lock、source drift/文件身份检测、backup/restore、encrypted inventory、effect 恢复 fences；新增 plan-specific migration 与差异不变量。先验 exact 源版本及代码，再 snapshot 到全新目标，在隔离副本按固定顺序应用 SQL；每步 transaction/完成版本准确，允许新增表的 row delta 明列，其余原历史/accepted artifacts/refs 保持。失败不发布目标、不污染原实例；取消保留可诊断状态。activation 仍是独立单写者切换，不因 restore report 已生成就自动启动。

`UpgradeLocal` 当前会调用 `QueryFrozenService("aggregate")` 和 FrozenProvider 复核外部引用，所以本次连该 CLI 的 dry-run 都不执行。开发单测用私有 test verifier/sealed synthetic refs 验证机制，但不得注入生产 public path 的 fake-provider 绕过。正式后续检查外部引用时需要对应已授权且可用的原服务；不可把公开 safe summary 当私有 payload 已重新验证，不复制 protected service SID、credential、holdout 入包。不解锁此前 policy 拒绝的实际激活。

## 8. 两个源码切片，正式演练另记证据

**R1：可复现包 + pinned upgrade（可在 runtime S2 前做）。** 单 worktree 负责 `ops/release/` 新最小 build/verify 脚本、`release/` 配置/manifest template、`docs/installation/`、`tests/release/`；必要小改 `apps/control/main.go` 包根定位、`ops/backup/main.go` exact plan dispatch、`internal/domain/backup_upgrade*.go` plan-specific helper/tests。root 串行登记 commands；不改 frozen spec、不修改旧升级计划。临时无密钥 DB 的 source13→固定 target、包重建/hash/缺文件/篡改/错工具/路径/配置/保留数据的正负例通过，产物仍标 DEVELOPMENT/PARTIAL，A15 不通过。

**R2：独立 supervisor + 串行 canary（集成依赖 runtime S2 接受）。** 单 worktree 负责 `ops/supervisor/` 新服务/launcher/journal 及 `ops/canary/` production finite policy；少量 `internal/domain/evolution*.go` typed production branch/operations table/current acceptance、`apps/control/main.go` supervised drain/fence，W18 restore 联结；migration 由 root 后分配。R1 提供 immutable 包，S2 提供单实例/任务权限/生命周期/effect恢复；复用已有 AppContainer fixture、W16 acceptance 和 W18 路径算法。交付公共 HTTP→持久 intent→真实独立进程→原始 sealed receipt→domain 投影的可测试机制，但临时同用户进程不声称独立 OS 服务。没有正式安装授权的服务级测试保留 NOT_RUN；fixture 不产生 LIVE supervisor registration。

两个切片都可只在新建临时目录、无密钥 native exe 上实现和验证；不是授权创建真实服务、修改 stable、迁移现产品或读取留出。正式条件具备后，在同一实现上做 clean 环境安装和 LIVE canary/回滚，不再引入第三发布架构。

## 9. 最低正负测试与未来实际证据

| 范围 | 机制期必须跑的真实断言 | 正式仍缺的证据 |
| --- | --- | --- |
| release | 同锁两次构建的文件/包 hash 比较；缺资产/错 spec/schema/被篡改 exe/重绑定错工具拒绝；secret allowlist；真实 start/stop 保留临时数据 | 未装开发依赖的 clean Windows11 x64 用户或 VM，身份/环境、真实命令/版本、安装/更新/停用/恢复原始回执 |
| pinned upgrade | synthetic populated13→exact发行schema；错源/错 SQL/源漂移/reparse/硬链接/取消/断电窗口拒绝；旧 13→14 测试保留；effect UNKNOWN 不重发 | current production 源目标版本的独立恢复资格及单独允许的 activation；原 protected 外部依赖可用 |
| admission | HTTP 原合同/条件/幂等；自签、过期/撤销资格、错 hash/epoch/样本/rubric、缺 migration/backup、原 fixture host、冻结 digest 改名重投都拒绝 | 已登记独立 OS Supervisor/Verifier 身份、签名/来源策略、当前 W18/W14/W12/W15/runtime 资格 |
| native tamper | 延用 startup/regression/hang/gate tamper；真实 candidate 尝试写 manifest、gate、labels、permissions、slot、freeze set 和继承句柄；hash/ACL/实际拒绝记录 | 服务级身份隔离和 SCM ACL 实测；candidate 不能停止或替换稳定 supervisor |
| switching | fixture 包实际切二进制/数据根，健康来自真实 child；多进程争锁只单 writer；crash 各窗口及新进程恢复；ACK 丢失不重发 | 唯一真实 control 实例 canary 后 actual last-known-good hash/data/任务/健康恢复，非状态字段修改 |
| metrics | no gain 保留 stable；自评分/新 rubric 涨分但 outcomes 不变拒绝；篡改/漏样本/跨版本回执拒绝；24h/clock/restart deadline 条件可用可控时钟验证 | C20 frozen holdout 结果；成功路径 1 真实周期 + ≥6h、最长24h；fixture 时钟不能计 LIVE 覆盖 |
| product continuity | 临时 fixture unrelated Task/checkpoint/effect/cost 身份连续；失败候选持久冻结、同 hash 不重开 | 真实项目切换时可中断任务安全处理、不允许中断任务挡切换、其他项目只读/恢复派单 |
| A15 integration | release.reproduce 真实可执行、selector 无断言必须失败，41例索引逐项保留 NOT_RUN/BLOCKED/PARTIAL | 最终11页→实际 operationId/request/event/持久化记录，关键读写/权限/断线恢复；独立 A15 后才42例完整索引 |

clean 环境不能仅声明：记录 fresh 用户 SID/VM标识、OS build、基线 tool/service inventory、空安装路径、包 hash 与工具绑定；从交付文档执行完整操作，使用新建演练数据并保留 install→run→upgrade→rollback→disable 的状态/文件 hash。缺 provider/独立账户允许局部安装测试，明确不满足 A15 全门。测试仅针对本次变化及保留的不变量，不重跑无变化全套。

收尾范围：本次只做 JSON 解析、结构检查及两文件 SHA-256；未执行上述机制测试。没有接受 W16/W20、C20/A16/A15，没有改施工 ledger/gate 状态。输出是后续可审核施工输入。

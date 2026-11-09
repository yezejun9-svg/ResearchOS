## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** 独立审查完整 19 路径的 F08 取消完成与 SQL24 升级设计。Option B 的包初始化和真实 PREPARED 取消生产路径静态上可行，但 witness 字段、关系约束、digest 绑定和升级前来源边界尚未闭合；当前不能批准为 sufficient，不能实施或合入 SQL24。

受审基线是 Main `2cdb0d43d5a600eef13c8f1735946a9adf52d079`。两份提案 SHA 分别为 `70dbfcec98e10f6872982daf03588746d3aa1bc90d7096c28f9b1e30ee5d24a6`、`17f8e1e763109cec8ab109f1586cffe80d26569ec2703ec319f5e20363dddeb9`。193 个 manifest 条目在作者原目录与 Main copy 共 386 个文件逐字节核验；26 个提案内递归 SHA 引用一致。153 个公开源快照保存到本审查目录；所有 153 条 original 源引用重新核验一致，其中 137 个产品/依赖声明/SQL 快照与固定 Main Git blob 逐字节一致。未读取施工中的 handler live 源；其最终原始 header/helper/Execute 边界须冻结后重新核对。

### Critical Issues

- **C01 — SQL24 的 closed witness 与提交关系仍缺定义。** 补充提案 `udf_contract.functions[2].unfinished_contract` 尚无最终字段清单/DDL。D01 只说 deferred journal link，没有写出 ACK 已存在时 FINALIZED root/member、control 状态和 sole journal 最终 body 如何互相约束。只连 request_hash 的 FK 已被旧 ACK 满足，不能证明最终闭合。修正：作者提交固定表/列/键/类型/null 变体、完整双向 membership 条件，以及初次 ACK、初次 COMPLETED、ACK→COMPLETED 三套明确插入顺序；最终 journal guard 必须重新检查整个 group 与实际最终 response，partial group 不可成为完成或有效 backup。若声称 deferred FK 能阻止半组提交，必须给出指向最终状态/最终 locator 的真实 parent UNIQUE 和 deferred FK；不可把只存在原 journal 说成最终链接。见 `required_closed_contract.json`。

- **C02 — original-dispatch anchor 缺升级前排除和单向状态的具体实现合同。** `cancel_terminal_producer.new24_dispatch_origin_guard` 中 AFTER INSERT 自动写 anchor，尚不能阻止给原 schema23 PREPARED 行直接补写 origin，或把 STARTED/UNKNOWN 改回 PREPARED 后制造未启动标签。SQL17 只有 manifest UPDATE 与直接 DELETE guard（`0017_runtime_dispatch.sql:15`），并没有状态单向或 REPLACE 冲突防护。修正：固定受保护的升级前 Run/dispatch cohort 或等价不可伪造的 schema24 出生边界，且不能将它当旧行出生证明；新 origin 只能绑定实际 schema24 native 插入及原 Run revision、claim event/admission/manifest/lease 元组；旧 cohort 绝不补 origin。提交所有实际 transition 的 OLD/NEW 列白名单、各唯一键 INSERT collision/DELETE guards，并保留 UNKNOWN→有真实 observation 的 OBSERVED 恢复路径。UNKNOWN、STARTED 空 identity 或缺 required dispatch 均不允许 never-launched fastpath。

- **C03 — FINALIZED 的 raw-body hash 目前没有被 SQL 回调重算后绑定。** `response_v1` 的五个参数包括两份实际 body，但第二参数的 closed identity shape 没有 final root 的 original/final digest；`witness_v1` 合同只检查 hash-reference 语法。两边各自 valid 或几处相等的同一伪造 hash，仍不等于 `Digest(actual OLD/NEW bytes)`。修正：在仍然三函数、纯 callback 的设计中，把由 SQL 从确切 immutable root/control 行构造的 closed response-proof binding 加入第二参数，并让 response callback 重算实际 body SHA 与该 binding 比较；初次 ACK/初次 COMPLETED/转换各自明确 null 规则。witness canonical hash 同样必须由实际 payload 重算，禁止自引用 hash；若改变参数或返回类型，则先提交精确修订合同。SQL 再检查参数来源与 relational tuple，不能接受 caller 提供的 proof 或 stored ready/hash flag。

### Important Issues

- **I01 — 撤去新 1 MiB response 限制。** Root 已明确选择保留冻结的完整合法 response 语义，不批准此 cap。冻结 `SessionSnapshot` 的 `title`、`MessagePart.text` 没有 maxLength；`messages` 最多 200 条也不构成 1 MiB 上限。`BuildSessionSnapshot`（`client_protocol_journal.go:295`）只按条数裁剪，现有 CLI reader 的 1 MiB cap（`cli_v2.go:260`）不能授权 server 新限制。修正：从 SQL guards/callback/backup 晋级逻辑撤去新 response cap，保留真正已有 raw-envelope/header 限制；用真实合法 >1 MiB snapshot 验证 sole journal 完成与逐字节 replay。不要以 ACK 永久保留来满足该用例。新的 witness 容量须与 closed format 一起单独审查，不能间接重新限制 response。

- **I02 — 19 的覆盖必须按真实可达生产阶段表述。** `claimTaskMode`（`orchestration.go:421–463`）与 native qualification 在同一事务创建 Run 和 PREPARED；当前 native 持久 QUEUED-without-dispatch 不是真实独立阶段。`RunAdmitted` 先提交 STARTED（`runtime_coordinator_windows.go:513–528`）再 StartBridge，空 PID 不证明未启动。修正：19 只承诺 NO_RUN、真实 native PREPARED-before-STARTED、真实 started settlement、完整历史 terminal。前者须由新 private runtime helper 在 caller writer transaction 完成真正 Run/Task/event/queue/witness/journal，不能永远 ACK。真实 generic/legacy 缺 dispatch 分支保留明确 blocked，且不能删除 dispatch 做正例。若要新持久 pre-dispatch native 生命周期，另列 `orchestration.go`、`runtime_dispatch.go`，以及仅在签名变化时的 qualification caller；不要在本 19 范围偷偷改 claim 顺序。

### Suggestions

- 将 new closed payload、纯 transport wrapper 与 DB relational locator 分开命名；`request_hash` 一律调用原 `Envelope.ContentHash`，raw digest 与 RFC8785 witness digest 使用不同字段名，避免把原请求身份替换为 JCS。
- final snapshot 可在新 helper 中调用现有 builder、仅过滤实际待确认的本 command，再作完整 frozen validation；这样能避免为打破状态/response 循环扩大 `client_protocol_journal.go` 范围。数据库 CONFIRMED 必须和整个 final group、sole journal 同事务发布。

### What's Done Well

- 提案明确记录自己的未执行状态，没有把设计或旧的局部审查当完整接受。对 native claim 原子性、STARTED 空 identity、最新 PREPARED/UNKNOWN effect 与零 fence 的分析准确，并明确保留账本和旧失败。
- 固定 schema 镜像、原 ContentHash 算法、CAST AS BLOB、防重复键、真实 old23 program、持锁到 publication、22/23 四表及 SQL23 配置历史不回填的方向符合现有源事实。

### Verification Story

- Tests reviewed: **yes，静态。** 先读原取消/lease/resume tests，核对三处 fresh/historical helper 及升级 tests 的调用边界；最小后续控制集合见 `minimal_verification.json`。本次未运行任何测试、SQL、Node、HTTP、model 或 paid call。
- Build verified: **no。** 没有 SQL24/新 helper 实现，不编译，也不授予 SOURCE_READY。
- Security checked: **yes，设计与 pinned source。** 确认 modernc default driver 注册必须先于 first Open，新物理连接逐项安装 UDF，失败 close+error；普通 TEXT 可在 NUL 处截断，故字节参数必须 BLOB。callback 不得读取 DB、Host、Clock 或 mutable ready state。UDF 不认证 OS 事实或任意 whole-DB replacement，trusted producer 与完整 typed backup proof 仍必需。

## D01–D10 与范围结论

| 项目 | 结论 | 实施前具体门槛 |
|---|---|---|
| D01 | NEEDS CLOSED CONTRACT | C01/C03 的顺序、完整 group、snapshot 本 command 过滤、original/final 单赋值与 old-body CAS/RowsAffected=1；handler 最终 savepoint/identity 边界 pending |
| D02 | NEEDS PRODUCER CONTRACT | C02/I02；资源 writer lock 后的精确 PREPARED→真正 CANCELLED 生产路径；不能借 `effectsReconciled` 或零 fence 单独证明完成 |
| D03 | NEEDS CLOSED FIELDS | 所有 root/member/phase/NO_RUN/NO_SESSION/null/VersionRef 字段固定；原完整 Goal membership 在 mutation 前双向核查，不用现头回填 |
| D04 | NEEDS EXACT DDL CONTROLS | journal/control/witness/origin/被引用 anchors 的 DELETE、每个 unique collision、REPLACE/UPSERT/rewind；recursive_triggers OFF 仍拒绝 |
| D05 | OPTION B STATICALLY FEASIBLE; NOT ACCEPTED | 三函数 closed contract 补全；domain init 先于 default-driver opens，所有 conns 静态方向可覆盖，真实 compiler/conn/error/trusted_schema outcomes 后验 |
| D06 | DESIGN DIRECTION VALID; DETAILS PENDING | frozen old Run/final artifacts/queue/effect proof 与 current restore fences 分离；完整 inventory 与允许恢复增量绑定新 closed format |
| D07 | EXACT BOUNDS VALID | fresh queue、configurationMigrationFiles、actual_Service_New 三处仅必要 fixture 调整；历史22/23、旧断言和固定 1..23 SHA 保留 |
| D08 | DESIGN DIRECTION VALID; NOT EXECUTED | 真实 accepted old23 binary/source closure；snapshot→publication 每阶段 writer busy/refusal、WAL read 实况、释放后重开原23 |
| D09 | DESIGN DIRECTION VALID; NOT EXECUTED | 新 exact23→24 plan/target SQL hash/schema fingerprint；旧行 schema-only 不变，public backup→upgrade→restore→rebackup；publication 前 rollback 与后续 effect 边界 |
| D10 | SERIAL HANDOFF PENDING | handler27 nonauthor 冻结/Root Main 接受后重捕共享边界；单一 F08 lease，core+upgrade+SQL24 同组审查整合 |

**Scope disposition:** 17 原路径加 `runtime.go` 与 `runtime_coordinator_windows.go` 是当前 native PREPARED 方向的候选 19，不能在 C01–C03/I01 闭合前称 sufficient。此报告要求作者只读修订并由非作者复核，未批准实施、合入或正式用例。handler 后续变化不会被本报告推测为已经符合。

复核工具记录另有一次实际 exit1：初次补验把 nested before 与 flat after 元数据直接比较，未进入源/SQL/Git 检查。保留失败脚本及 `fe789d` 来源，另开明确 original 投影的 attempt2，153/137 核验实际 exit0。此工具失败需 Root 单独累计；不归产品 case，也未重置历史失败。

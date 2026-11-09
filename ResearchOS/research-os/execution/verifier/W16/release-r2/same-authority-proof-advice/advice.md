# Actual-control 两个真实 EXE 的最小行为证明建议

基准：main `5019f5b08f55cea7bf31a43df09d8817b05be862`，以及 release-supervisor 已审的 `643a04f` / evidence `57f2457`。这是只读架构建议；未修改源码、SQL、合同或台账，未运行服务、数据库、provider 或停止的 S2 adversarial。

**结论：现有接口还不能给 actual-control 二进制签发合格 C20/R2 业务收益证明，cutover 准入和 PROMOTE 必须保持关闭。** 可以复用隔离执行、私有存储、当前独立 verifier 与发布 admission 的结构；不能复用旧 calculator proof。最小新增路径是：**相同实际 `apps/control.exe` 的单用例离线 API replay → 正式 `Service.Handler()` → 隔离副本上的真实返回/状态 → 外部 verifier 评分**。不增加另一套 calculator，不以换 hash 作为收益。

## 现有可复用与不能跨越的边界

| 位置 / 函数 | 可复用内容与限制 |
|---|---|
| `internal/domain/http.go:Service.Handler`；`internal/api/server.go:Handler` | 正式业务的鉴权、合同、ETag、幂等和领域操作。离线 replay 直接调用同一个 Handler，避免 AppContainer 开网络权限；这证明领域 API 行为，不证明 HTTP socket、SCM 或完整调度器性能。 |
| `ops/experiment_sandbox/{sandbox,async}_windows.go:Start/Run/Wait/BeforeResume` | 每用例、每个 build 使用新的零 capability AppContainer；只读 input、独立可写 output、单进程 Job、超时和原始 stdout/stderr/进程收据。仅复用已实现机制；本建议不授权重新运行 S2 adversarial。 |
| `internal/domain/evolution_holdout.go:RegisterEvolutionHoldoutFixture/EvaluateEvolutionHoldoutFixture/evolutionHoldoutVerdict` | 可复用冻结输入与标签、独立 verifier、私有 proof 注册、最终重算和不可重复绑定。当前内容协议只有 add/multiply，不能直接给 control EXE 使用。 |
| `internal/domain/evolution.go:RegisterEvolutionBuild/registerEvolutionFixture/evolutionCurrent` | 当前 build 只允许 `ops/canary/fixture/main.go`，suite/policy 也固定为 calculator。必须新增受信 host 的精确 FIXTURE profile；不能删除旧限制或允许候选自选 profile。旧 immutable host 不能原地改写。 |
| `internal/domain/evolution_execution.go`、`evolution_acceptance.go`、`acceptance.go` | 正常 Task/Run/Experiment/AcceptanceReceipt、原始结果重算、当前 context/policy/epoch 绑定可保留；现有 public regression 也必须有 control profile 分支。**只换 private holdout 而 public 仍为 calculator 不成立。** |
| `ops/supervisor/control_fixture_windows.go:Ready/Drain/Stop` | 继续证明将运行进程的 exact identity、lease、listener 与正常退出；READY 是机械就绪证明，不能替代业务收益。当前 same-user driver 不负责隔离 private labels。 |

## 建议最小实现顺序

1. **可信 host 先冻结评估输入。** 记录真实 baseline/candidate EXE bytes/hash、source provenance、精确 changed-paths manifest、共同合同/迁移 manifest、协议/用例/评分规则版本、同一个源 authority generation/snapshot hash。从该基线确定地产生每用例的隔离输入副本，两侧得到相同初态。副本只包含本用例所需的普通业务数据与 fixture-only 凭据，移除真实凭据、provider secret、private inputs/labels/proof 内容及发布 authority；删除/保留规则和投影 hash 本身也冻结。不要为评估另开同一实际 authority DB 的写连接，snapshot 取得方式由作者正在实现的受控 host+snapshot 流程提供。

2. **在 `apps/control/main.go` 增加显式的 `--fixture-control-replay <request>` 分支及小 helper。** 必须在默认 data-dir、Protected provider、listener、coordinator、drain capability 初始化之前分流；固定只读取获准 input 根中的 snapshot/contracts/migrations/current-case，复制 snapshot 到该次 output 根后才开 SQLite/lease。调用 `domain.New` 和正式 `Service.Handler().ServeHTTP`，用内存 Request/ResponseWriter 驱动一条有界 API 序列，不经过 TCP、不启动 worker、不调用 provider、不连接真实 data root。请求中只含当前用例，不含 expected/labels/评分代码。输出真实 HTTP status/body/必要 header；结束前关闭 DB，host 再读取隔离输出状态。禁止在 helper 里重写业务规则或直接返回标准答案。

3. **两个被测文件就是后续拟启动的两个文件。** 新 runner 放在 `ops/supervisor/control_holdout_windows.go` 等独立文件：每 case × build 复制精确 EXE，记录只读 staging bytes hash；在 `BeforeResume` 对 suspended child 核对 PID/creation、实际 image path/hash，结果与最终 sandbox receipt 对齐。必须保留退出、停止、完整流、输出拷贝/清理事实，缺项则该用例 UNVERIFIED。proof 绑定两 EXE hash、snapshot/projection hash、case 顺序/数量、原始输入输出 hash、进程收据、protocol/public-suite/private-label/oracle hash。同一 bytes 此后还要通过 admission → release journal → Start/Ready image 检查。不能测试 wrapper/calculator 后把 hash 字段改为 control hash。

4. **host 在 candidate 退出后独立评分。** 建议首个 profile 只覆盖本次真实改动涉及的现有业务 API。例如 `/v1/projects/{id}/research-cycles/{cycle}/close` 的合法结束，以及缺失独立报告、存在 coverage gap 或未决实验时的拒绝；再以 GET/隔离 DB 原始状态确认状态、既有 Run/Task 身份及无额外变更。具体输入和 expected 必须由独立 verifier 预先冻结。若目标改动是检索，则测 `searchEvidence` 的真实返回 ID/来源与权限，而非在 replay helper 里做加乘运算。只有与真实修改有关的测量才算该候选收益。

5. **接入独立版本的业务评估 profile。** `evaluation/evolution` 新增 control request/result/label 与严格 validator；旧 `private-c20-fixture-v1`、`private-r2-fixture-v1` 继续原语义。新 trusted host profile 同时选择 public regression 与 private holdout 的协议/冻结 hash。`RegisterEvolutionBuild` 对该 profile 接受经过审查的 exact business paths，而 evaluator、labels、oracle、sandbox、supervisor、release 权限与 replay helper 必须冻结不由候选修改。`evolutionCurrent`、`evolutionCheckContract`、`evolutionIDs/Expected`、`ExecuteEvolutionFixture`、`evolutionRecordValid/verifyEvolutionObservation` 与 `evolutionHoldoutVerdict` 都按受信 host profile 严格分派，不能由请求的自由字符串降级到旧 calculator 分支。仍使用现有 Task/Run/Experiment 及其 acceptance，不新增队列或放松 SQL/公共合同。

## 不能删掉的硬门

- **baseline 不能补造。** 若当前已封存的 stable EXE 不支持 replay 协议，不能重新编译并沿用旧 stable hash/身份。要么先独立评审一个无收益的协议基线并在新的明确 fixture registration 中评估后续候选；要么采用以后另行评审的外部真实 API harness。当前 stable 不可测时保持 UNVERIFIED/closed，不能默认 baseline 错误来制造 gain。
- **评分不由被测 EXE决定。** 保留全部 raw，在外部按冻结规范提取语义结果；只可预先声明忽略无业务意义的 correlation ID/时刻等字段，不能忽略 status、错误码、对象身份/修订、权限、成本或 coverage 语义。候选自评分与 rubric 变化只作记录。至少一项以前不正确的真实结果变为正确，且 baseline 原本正确的必需行为不退化，才有 gain。相同结果、同代码换 hash、只换 evaluator、未测或异常退出都不是收益；没有收益合法保留 stable，不生成切换 effect。
- **private labels 只在独立 verifier/CanaryStore 与宿主评分器内。** 不复制私有 store/key、全量输入、标签、原始 proof 或 verifier/release token 到 child input、环境、继承 handle 或 authority clone。每次新的零 capability AppContainer 只看到当前 case；`RegisterProtectedArtifact` 保存详细 proof，普通项目只收到固定 aggregate。不能让同用户 unrestricted `ControlFixtureDriver` 直接持标签执行候选。
- **当前资格必须重查。** 复用 `evolutionHoldoutVerifierCurrent` → `evolutionCurrentPrincipal`/`protectedAllowed`/`authorityRoot`，在 freeze、执行前、执行结束落 proof、每次 proof 使用均检查 current restricted verifier grant、remote issuer/device 交集及与 author/release 的 root 分离。回归正常 acceptance 与 `releaseActorsCurrent` 也保留。`releaseAdmissionCurrent` 在实际 effect 前重验当前 candidate/status、receipt、policy/conflict、expiry、exact slot/operation/backup/proof/build；候选或其可写 DB 不能单独签发授权。
- **真实 source generation 必须相符。** 若 evaluation snapshot 与最终封存 backup 的业务 generation 不一致，需按冻结规则重新证明相容或停止；不得只因同一路径就当相同 authority。现有 `ReleaseAdmission.HoldoutProofSHA256` 可以绑定详细 proof，不要求新增 SQL 表；但 `releaseAdmissionInputs` 必须验证该 proof 是当前 control profile、两个 exact EXE 与相应 authority generation，拒绝旧 marker/calculator proof。
- **范围仍为 FIXTURE。** `os_service_qualified=false`，`actSystemCandidate` 的 PROMOTE 503 guard 不变。离线业务 proof + 已有正常启动/同 root 连续性只能进入单独审查的 bounded fixture cutover；不能据此宣称 SCM/LIVE、6h、实际回滚或正式 C20/A16 达标。缺少实际业务修复时，作者可完成 host+snapshot 的独立机制片段，收益门仍 closed。

最低交付验收：一个合法无收益 pair 应保留 stable；若存在真实业务修复，独立冻结的一条对应 old-fail/new-pass 加必需无退化回归；cross-build/protocol/snapshot proof 错配与当前 verifier 撤销拒绝。除此不扩展 S2 对抗重试。本次仅提出上述方案，没有执行这些检查。

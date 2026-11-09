# coding delivery v1 — 只读构造方案

状态：PROPOSED_NOT_IMPLEMENTED；基线 CP586 / Main 556cdc353f47167e5609f23291bf2746e3c8896f。D: 无写入，未打开数据库，未运行测试、native、服务器或模型。本方案不签发接受，不改变普通 LIVE Goal 的 503。

## 推荐的 v1 边界

只支持已存在的明确 `goal.start`，且当前可信 Host coding prepare/confirm 已冻结一个指定的业务 plan。普通 `session.send`、task/run prompt 桥和 planning 均保持既有行为，不从文本、Artifact 名称、command_key 或 task_type 自动推断业务授权。后续需要把 session.send 接入时，必须先解决其随机 Requirement/origin 的稳定身份问题。

接受对象建议为完整的不可变 sealed 三文件 source bundle。Workspace 的当时副本可作为关联诊断，但不声称 SQL 接受提交瞬间或之后整个可变目录永远与 bundle 相同。若要求这个更强保证，需要另设计 filesystem/writer fence，不能靠“再读一次 hash”宣称原子性。

固定可信 suite 由 Host 编译内置 registry 按 suite_id 查出，不接受 caller 声明 tests_hash 作为信任根。第一版仅一个 suite、一个包、一份可写业务文件：

```
go.mod
pkg/solution.go       # 唯一可写
pkg/solution_test.go  # 编译内置精确 bytes
```

固定 package 和单函数签名（例 `Solve(a, b int64) int64`，最终由 Root 冻结）。只允许 int64/bool、局部变量赋值、无 init 的 if/else、return、明确的纯算术/比较/布尔表达式；不允许 imports、init、top-level var/const/type、额外函数/receiver/generic、任何 CallExpr、循环、指针、selector/index、closure、go/defer、panic/print/recover、unsafe、cgo、embed、汇编、build/line/linkname 等指令。v1 可以直接拒绝所有注释。go/types 负责语言类型、名称绑定与返回路径，AST 白名单默认拒绝未知节点；建议 <=16KiB、<=512 nodes、depth<=32。int64 溢出采用 Go 语义；更大语言子集另立版本。

## DCD001：actual checked / sealed same bytes

建议纯包 `internal/codingdelivery`（C 原型当前只实现结构原语，并未集成）：

```go
type Member struct { Path string; Bytes []byte }
type Spec struct { Schema, SuiteID, SuiteHash, PackagePath, MutablePath, SignatureHash string; RequiredTests []string; FixedMembers []Member }
type Witness struct { Schema, SuiteID, SuiteHash, ValidatorID, SignatureHash, InventoryHash, SourceManifestHash, MutableHash string }
func LookupSuite(id string) (Spec, error) // 防御性复制，非可变全局 map
func ValidateSnapshot(spec Spec, files []Member) (Witness, error) // 无 FS / DB / exec
```

Witness 只证明源码属于受限能力子集，绝不单独代表业务 PASS。

`RuntimeCodingCheck` 可增加 `CheckerMode`、`SuiteID` 两个 omitempty 私有字段；空值走原路径，未知非空模式拒绝。新模式限制一 check、一 write path，package/test_pattern/source_paths 必须与可信 suite 精确相同。可信 prepare/confirm 可增加可选 typed plan 锚点，旧 nil 不改变旧序列化和 Hash。`frozenRuntimeCheck` 严格封存模式、suite/checker 版本、toolchain、固定输入和 roster；只给新模式生成固定 `go test -json -count=1 -run <frozen>` argv，模型仍只能传已冻结 check ID。

`executeRuntimeCheck` 新模式复用已有 `sandbox.Start` + `Wait` 和 `StartOptions.BeforeResume`：在真实 private input 复制完成、进程仍 suspended 时，从 Identity.StagingDirectory/input/source 读取严格库存与 bytes，运行 validator、比较预计 manifest，并保留这份 bytes。旧 `Run` 路径不改。hook 拒绝须终止 Job；仅完整启动、stream drained、cleaned、exit0、完整可信 suite/roster 才有检查成功事实。原始完整 stdout/stderr 保留；test2json run/pass 只是覆盖佐证。

在 CONFIRMED canonical Host fact 的 host_tool_evidence 中封存版本化 witness、完整 source bundle（小于既有 evidence 限额）和 bundle hash；沿现有 toolProjectionArtifacts/recoverArtifact 将其恢复为同 Run/epoch 的 sealed REPORT。业务 checker 从 canonical dispatch/effect/report 取得这些 bytes 再执行 validator，核对 suite、实际 manifest、最后 write/edit 与最终 check 的 journal 顺序、profile、epoch、cleanup、完整日志和零退出。缺 bundle、只给目录/manifest/自报 PASS 均拒绝。

## DCD002：私有绑定和双合同

v1 的 Task contract 必含两项 required deterministic check：既有 `mu.turn-output-v1` 与 `coding.pure-scalar-delivery-v1`。Goal contract 使用独立的 `coding.accepted-task-delivery-v1`，只聚合精确单 Task 的当前独立 PASS receipt 和其受保护交付证据；不再对 Goal 自身调用 verifyMuTurn。普通合同仍保留原行为。

```go
type finiteGoalContracts struct { Task, Goal Object }
type codingDeliveryPrepared struct { /* 仅可信 Host resolver 构造，非 JSON 授权载荷 */ }
func codingDeliveryContracts(*codingDeliveryPrepared) (finiteGoalContracts, error)
func persistCodingDeliveryBindingTx(ctx context.Context, tx *sql.Tx, owner Principal, goal, task Object, p *codingDeliveryPrepared) error
func codingDeliveryTaskBindingTx(tx *sql.Tx, project, taskID string) (Object, error)
func codingDeliveryTaskSnapshotTx(tx *sql.Tx, project string, task, run Object) (Object, error)
func verifyCodingTaskDelivery(snapshot Object) (string, string)
func codingDeliveryGoalSnapshotTx(tx *sql.Tx, project string, goal Object) (Object, error)
func verifyCodingGoalDelivery(snapshot Object) (string, string)
```

`finiteGoalSpec` 增加可选双合同/私有 prepared 值；旧调用继续由原 Contract 作为两者，不能全局更改。正常事务顺序仍为 Requirement → Goal/Task → ACTIVATE → Context → SUBMIT；在 AdmitTurn 前原子写入 private binding。必须同时扩展 `pendingClientTask` 的合法创建审计：现有代码强制 Goal/Task 合同相等、重算默认 clientTurnContract/用户 Artifact 合同。仅有完整 private binding 的分支才验证双合同及原始 command；普通分支保留旧 equality 和全部 input/history/Requirement/NoProgress 检查。插入或匹配失败必须回滚，不能降级为普通业务类型。

binding 最低字段：schema/version、canonical intent/approval ID、原 Owner/root/Host/parent authority、原始创建 method/command/request hash、Project/Session/Goal/Task IDs、双合同 hash、Requirement/input refs hash、frozen profile/policy/suite/manifest hash、原 origin_problem/candidate/NoProgress identity。创建时未产生的 Run/epoch 不填假值；真实 Run/epoch 由 native dispatch/admission 当前证据绑定。

typed identity 必须由可信 plan + 原业务身份构成，重复上传相同 bytes 不得因新 Artifact ID 获得新 origin；只使用已批准的 canonical refs。相同意图重发返回原 Goal/Task 的续跑指引或拒绝。重配 profile/换新 root 也不能擦掉旧失败 lineage。v1 单 approval 单 Goal/Task，不能用新 command ID 重新消费 plan。

## 持久化判断：推荐专用表，不为避免 migration 削弱边界

`idempotency` 技术上能保存 host: 私有 JSON（现 host:coding-authorization 已如此），且公开 V2 method 的 operation 由服务固定为 `v2:` 前缀，caller 不能靠 command ID 选择 host: operation。Owner 必须来自确认 token 的 p.ID，root 来自 currentAuthorityRoot，Host 来自可信 ConfigurationAuthority，不能从 candidate JSON、CLI config 或 locator 读取权力。

但该表 PK=(principal,project,operation,key)，无法直接约束同 Task/Goal/approval 跨 principal 唯一；当前仅有 immutable UPDATE trigger，未发现生产 TTL/DELETE 清理，但无业务不可 DELETE 的约束。复用还需要独立 once-only claim、跨 principal count==1、私有 JSON restore 校验及永久不参与 replay-cache GC 的约定。其语义成本已不低于小表。

推荐新源码 schema 的 `coding_delivery_bindings`：PRIMARY KEY(project,task)，UNIQUE(project,goal)、UNIQUE(project,approval_id)、UNIQUE(project,intent_key)，保留 owner/root/host、双合同 hash、canonical body/hash；UPDATE/DELETE 均明确拒绝。服务层严格解码并对列/body、原始命令、公开对象、冻结 refs 和当前 authority 逐字段复核。只有同一合法创建事务可 INSERT；公开 API 不提供写表、指定 operation 或自造业务类型入口。恢复后的 row 也不授予 workspace、Host 或资格，仍走当前 nativeDispatchProof/currentDispatchAdmission。

仅准备新 schema 源码与全新 fixture DB；本阶段不注册到旧库自动升级路径、不打开或迁移旧库。旧 v24 库无该能力时新 typed 路径返回 RESOURCE_UNAVAILABLE/不开放 Goal，普通路径继续原行为。未来正式接入新版本须同时更新 schema/version matrix、backup table inventory/fingerprint 和 binding restore invariants，并做旧版本兼容审查。不要包装既有 orchestration contract JSON，也不要塞进 intent_plan_bindings；后者有 planning/monitor 专用语义。

## 最小交付 Artifact 路径：保持 SDK sole-output 不变

不把 Host bundle 直接 append 到 Run.result_artifact_ids/Task.output_artifact_ids。现 runtime.go 的 reportRun、runtime_model_stream.go、verifyMuTurn 均要求原生 SDK sole output；只放宽其中一个会失配或绕 provenance。

建议复用 Host evidence：Task 业务 checker 验证封存 source bundle；独立 Task acceptance 在服务端生成的验证 REPORT 中写入 typed coding_delivery proof（binding 双 hash、bundle_ref/hash、suite/witness、canonical check effect/report refs、Run/epoch）。receipt 的 evidence_refs 由服务填该 REPORT，而非采纳请求里的 refs；Run/Task 原 SDK output 向量保持精确不变。

专用 Goal snapshot 先执行 acceptedTaskBinding，再仅从当前 PASS receipt 指向的该服务验证 REPORT 取 bundle，复核 REPORT 对 Task/Run/contract/refs 的绑定、Host canonical fact 和 ArtifactUse。typed Goal 的精确输出向量可定义为既有 accepted Task 输出加这一份已由 Task checker 接受的 bundle。普通 Goal 的输出派生保持不变。禁止按 Artifact 名称/内容自称选择 SDK 或 bundle，禁止把模型可见 TOOL_RESULT 当权威。

这一条是需要 Root 明确认可的语义选择：Goal 交付物由已独立接受 Task 的受保护检查证据派生。若要求 bundle 必须进入 Task.output_artifact_ids，则需另立版本升级 reportRun/observation/modelStream/result-role 协议，不能当一处 len 检查修补。

## 需要的负例和实施次序

结构层：生产 init/global/import/directive/CallExpr/closure/loop/签名变化；超限/未知 AST；固定 tests/go.mod 漂移；额外或 case-colliding/reparse 输入；validated A/staged B/sealed C；伪 run/pass 无 witness；检查后 write/edit；错误 suite/旧 profile/epoch；stream 缺失/截断、nonzero、timeout、cleanup 未确认。

绑定层：自制 Artifact/command_key 声明业务类型；跨 principal 重复 Task/Goal/approval；双合同置换或少 mandatory check；原始 V2 request/response 缺失；pending audit 无合法分支；新 Artifact ID/new command/new namespace 洗旧 origin；accept prepare/commit 间 policy/refs/authority 改变；恢复后旧 Host/资格越权。

聚合层：没有当前 PASS Task receipt、receipt hash/contract/output不匹配、未由服务写入的检查 REPORT、foreign/旧 Run/epoch bundle、SDK/bundle 角色置换、伪 Host report、FIXTURE 冒 LIVE、Goal task 集合变化。普通 LIVE Goal 仍 503；旧 finite-turn/planning/FIXTURE 与旧 CLI prompt 路径不变。

可直接继续：C 中纯 validator、suite/byte-bundle/digest primitive 和攻击反例；纯双合同 factory/严格 DTO、schema 草案和全新 fixture；Host samebytes hook 的 source-only opt-in 设计。均不注册业务 checker、不开 LIVE 门。

需要 Root 的架构决定：可信 suite 的具体业务/签名/测试向量及发布 owner；sealed bundle 还是可变 Workspace 的承诺；专用表新版本/兼容策略；Goal 从 Task 验证证据派生交付 bundle 的语义。决定后，应把 binding + pending audit + 两份合同 + checker + Goal 精确例外作为可独立复核的完整批次，不能只先开 503。
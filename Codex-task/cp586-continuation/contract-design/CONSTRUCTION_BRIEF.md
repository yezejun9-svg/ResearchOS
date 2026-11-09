# Pure scalar bundle v1 — construction brief

状态：DESIGN_BRIEF_NOT_IMPLEMENTED。已按 Root 的架构选择收敛。基线 CP586/Main `556cdc353f47167e5609f23291bf2746e3c8896f`；physical Git 尚未因连接恢复而重新核验。本文和 source-index.json 仅写 C 工作区，D 源、旧库、LIVE 门均未改。

## Root 已确认的边界

- Goal 交付物是当前独立接受 Task 的服务端 sealed 验证 REPORT 中指向的 source bundle；再核 canonical Host facts、ArtifactUse 和完整绑定。SDK sole output、reportRun、modelStream、verifyMuTurn 的单结果规则保持。
- 这是 typed Goal 的 sealed 包交付，不自动声称当前 Workspace 持续正确。若以后承诺 current Workspace，另做严格库存/字节复核及必要的并发 fence。
- 使用专用不可变业务绑定表的新 schema 源码和 fresh fixture。旧库不打开、不迁移，不借 idempotency/planning 表或 contract JSON wrapper 省边界。
- v1 只在已有明确 `goal.start` 且可信 Host 已批准指定 plan 时可识别；普通 session.send、既有 planning 和未知 Turn 不自动升级。无有效精确绑定的普通 LIVE Goal 仍 503。

## 1. 精确业务合同与权限来源

建议业务版本 `coding.pure-scalar-bundle-v1`。可信 Host prepare/confirm 选择编译内置 suite、原始业务需求与 canonical input anchors，冻结 owner/root/Host/parent、workspace/model/profile/policy 和资源界限。不是从 prompt、Artifact 名称、command_key、task_type 或 locator 推断授权。原 RuntimeCodingIntent 可有 omitempty 的可选 typed plan；旧 nil 及原 profile Hash 行为保持。

suite 固定完整三文件库存：go.mod、pkg/solution.go（唯一可写）、pkg/solution_test.go（精确可信 bytes）。禁止 vendor、go.sum/go.work、额外编译输入/生成输入、路径别名或大小写碰撞。registry 返回防御性复制，不把 caller tests_hash 当信任根。

当前 C primitive 实际签名为 `package candidate; Clamp(value, lower, upper int32) int32`，仅参数赋值、if/else、return 和有限纯运算；无 imports、任何声明/调用/循环/指令。它是结构/精确 bytes 原语，不是 suite、checker 或业务 oracle。后续产品 suite 必须明确沿用该签名和语法，或另作版本；不能把原设计里的 int64 示例混入 int32 合同。

Task contract 必含 required `mu.turn-output-v1` 和 `coding.pure-scalar-delivery-v1`。Goal contract 使用 required `coding.accepted-task-delivery-v1`，聚合 accepted Task，不对 Goal 调 verifyMuTurn。两合同是服务 factory 生成的标准 AcceptanceContract，不更改公开 schema；双 hash 同时固定在 private binding。

## 2. 专用 private binding

源码 schema 草案（尚不放入旧库自动升级/运行路径）：

```sql
CREATE TABLE coding_delivery_bindings (
 project TEXT NOT NULL,
 goal_id TEXT NOT NULL,
 task_id TEXT NOT NULL,
 approval_id TEXT NOT NULL,
 intent_key TEXT NOT NULL,
 owner_principal TEXT NOT NULL,
 owner_root TEXT NOT NULL,
 owner_host TEXT NOT NULL,
 task_contract_hash TEXT NOT NULL,
 goal_contract_hash TEXT NOT NULL,
 binding_body TEXT NOT NULL,
 binding_hash TEXT NOT NULL,
 PRIMARY KEY(project, task_id),
 UNIQUE(project, goal_id),
 UNIQUE(project, approval_id),
 UNIQUE(project, intent_key),
 CHECK(json_valid(binding_body))
);
-- BEFORE UPDATE 与 BEFORE DELETE 均 RAISE(ABORT)。
```

binding_body 严格闭合版本 DTO；列与 body 逐字段一致；binding_hash=现有 Hash(canonical body)，body 不自含自己的 hash。保存下列实际来源：

- 确认 token 的原 Owner p.ID、currentAuthorityRoot 得到的 root、ConfigurationAuthority 得到的 Host、可信 parent/confirmation hash；不从 caller 的 Owner 字段或 CLI/locator 取权力。
- 原创建 method=goal.start、client/command ID、原始 envelope request hash、Project/Session/Goal/Task、workspace binding ref/hash。
- Task/Goal 两合同 hash、Requirement refs、Task input refs、当前 frozen profile/policy/suite/approved-plan hash。
- 原 origin_problem_id、candidate_id、NoProgressRecord ID/input key；创建时实际 writer epoch/revision 仅作为来源快照，不作为未来 lease。

创建时没有 Run/epoch，不填假值。实际 Task/Run/current lease epoch、profile、资格/purpose、current owner/writer 与取消结清必须由当前 dispatch/admission/native proof 再证明。

意图稳定键来自批准的原业务 anchor、Owner authority root、原需求/业务输入内容与 suite 版本。排除新的 command ID、时间、进程 ID、重复上传的 Artifact ID和新 Task/Run ID。重复输入只回原 Goal/Task 的续跑或拒绝；新的 approval/config/root/namespace 不能把继续中的失败 lineage 清零。v1 单 approval/intent 只可绑定一个 Goal/Task，跨 principal 也由表级 UNIQUE 约束；服务查询不先按 Owner 过滤再忽略冲突。

只有正常创建事务可 INSERT。公开 V2 method 本来只生成 v2: replay operation（client_protocol.go:737/829），caller 的 command ID 无法选择 host: operation；新表更不提供公开写入口。恢复后的 binding 不是授权凭证，旧 Host/Workspace/资格失效仍拒绝。

idempotency 复用已排除：现 PK 含 principal，只有 UPDATE immutable，未发现当前生产 TTL/DELETE，但缺业务 no-delete/跨 principal once-only 约束。新表须在新 schema 版本/fresh fixture 内明确做备份表清单、schema fingerprint、完整 row/hash/ref/Owner-root restore 校验。旧 v24 库不自动迁移；缺表/能力时 typed 功能不支持，普通路径保持。未来上线 schema version matrix 与旧库迁移是单独受控工作；不放宽 controlled-evolution 专用操作 allowlist。

## 3. 正常 API/事务接缝

以下为拟议接口，尚未实现：

```go
type finiteGoalContracts struct { Task, Goal Object }
type codingDeliveryPrepared struct { /* private, trusted Host resolver only */ }
func codingDeliveryContracts(*codingDeliveryPrepared) (finiteGoalContracts, error)
func persistCodingDeliveryBindingTx(context.Context, *sql.Tx, Principal, Object, Object, *codingDeliveryPrepared) error
func codingDeliveryTaskBindingTx(*sql.Tx, string, string) (Object, error)
func codingDeliveryTaskSnapshotTx(*sql.Tx, string, Object, Object) (Object, error)
func verifyCodingTaskDelivery(Object) (string, string)
func codingDeliveryGoalSnapshotTx(*sql.Tx, string, Object) (Object, error)
func verifyCodingGoalDelivery(Object) (string, string)
```

finiteGoalSpec 可承载可选双合同和 private prepared；旧调用继续将原 Contract 用于两者。保留 Requirement → Goal/Task → ACTIVATE → Context → SUBMIT 顺序，在 AdmitTurn 前原子插入绑定；失败回滚，不降级。业务身份使用原 canonical refs/Requirement，不允许相同 bytes 换新 Artifact ID 获取新 origin。

必须同步 `pendingClientTask`（client_protocol_configuration.go:145 起）的合法创建审计。它现在强制 Task/Goal 合同相等，并重算普通默认/用户 Artifact 合同。仅完整可信 binding 分支验证双合同、原始 command、公开对象和冻结输入；普通分支保留旧 equality、history、Requirement、NoProgress 和 input-vector 检查。不能只改 buildFiniteClientGoal 的两行。

## 4. 实际送检与交付证据

纯包 validator/LookupSuite 不碰 FS/DB/exec，返回结构 witness，不返回业务 PASS。新 checker_mode/suite_id 空值保持旧检查，未知非空值拒绝；模型仍只提交 frozen check ID，不能提交 argv。

新 Host check 复用 sandbox.Start/Wait 和现有 BeforeResume hook：实际 private copy 完成、进程 suspended 时读取 input/source 的严格库存和完整 bytes，在这份 bytes 上验证结构、可信固定文件和 manifest，并保留它形成 bundle。旧 sandbox.Run 路径不改。进程恢复后输入对 AppContainer 只读；不把同 SID 的本机 Agent 当敌对隔离边界。

成功要求完整实际进程/stream/cleanup receipt、exit0、未 timeout、可信 suite/实际 roster 及完整 raw 日志；go test run/pass 只是佐证，不能替代 structural witness。源码 witness、完整 source bundle、check/suite/toolchain/profile/epoch/hash 放进 CONFIRMED canonical Host fact，再沿现有 Host REPORT/LOG/ArtifactUse 恢复。缺 bytes、只有 path/manifest、UNKNOWN/NOT_APPLIED、清理未确认不能成功。

Task 业务 checker 从 canonical facts/封存 REPORT 独立重验同一 bundle bytes；检查必须晚于最后 write/edit，之后无未处理写入。验证当前 Task/Run/epoch/profile、固定 tests/依赖、最终 source/witness/bundle hash、原始输出和 cleanup。

独立 Task acceptance 在其服务端生成的验证 REPORT 中加入 typed proof：binding/双合同 hash、exact Task/Run/epoch、source_bundle_ref/hash、suite/witness、canonical effect/report refs。receipt.evidence_refs 由服务赋值，不能采纳请求自带引用。Task/Run 的 SDK result 向量仍只一份原 SDK 输出。

Goal snapshot 先沿 acceptedTaskBinding 确认当前 PASS receipt和旧输出精确匹配，再仅从该 receipt 指向的服务验证 REPORT 取 bundle；复核 Report 与 Task/Run/contracts/refs、canonical Host fact、ArtifactUse。typed Goal 的输出向量明确为既有 accepted Task 输出加这一份 checked bundle。普通 Goal 的输出派生不变。Goal 仍执行当前 verifier RBAC/authority separation、policy/ref freshness、nativeDispatchProof/currentDispatchAdmission 和 commit snapshot 重验。仅 private binding 完整且该专用 checker 可用的 typed Goal 才可能成为未来例外；本阶段不写 LIVE exception。

## 5. 最小实施卡与拒绝用例

1. C 中实际 pure scalar primitive 的独立 review/攻击反例：它只解决结构与 bytes primitive。
2. Source-only：trusted suite 与 bundle DTO、纯 contract factories、private binding schema 草案及 fresh fixture；普通 Goal503 代码保持。
3. 同一可审查批次处理 normal creation + pending audit + immutable binding + Host samebytes witness/REPORT + Task checker + Goal 聚合 DTO；先只支持不可激活的 typed fixture，禁止暗中放宽现门。
4. 独立复核后才讨论产品注册/精确 LIVE 例外和新库版本接入。真实模型/native执行仍需当前资源、资格和受限 scope，不重放已消费 scope，不迁移 C57/旧原库。

拒绝用例：所有 AST 执行能力/签名/预算/固定文件漂移；validated A/staged B/sealed C；额外或别名文件；只 run/pass 无 witness；检查后写入；foreign/旧 Run/epoch/profile；缺 raw/timeout/cleanup；自制 Artifact 或 command_key 授型；跨 principal 重复 Task/Goal/approval；双合同置换/少 mandatory check；pending audit/原始响应缺失；新命令/上传/namespace 洗 origin；prepare/commit 变更；伪服务 Report/SDK-bundle 角色置换；FIXTURE 冒 LIVE；普通 LIVE 仍503，旧 planning/session.send/CLI 保持。

尚待 Root 冻结的产品语义只剩具体 trusted suite/签名/测试向量与发布责任，以及新 schema 将来如何受控上线。当前文件没有实施接口、建库、开门或授予接受。
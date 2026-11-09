# 阶段1追加：启动边界摘要与 C 最终计划摘要

状态：`CONTRACT_BINDING_ADDENDUM_NOT_EXECUTED_NOT_ACCEPTED`。本文件追加于已冻结阶段1，不修改原矩阵、manifest、seal或失败账。Root明确授权本次追加；Source候选未冻结，测试0、actual操作0、formal增量0。

## 合同依据和结论

固定 `qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat/BOOT-C-ARCHITECTURE.md` SHA256 `39e1d66f69ddfc2745234b4e10950087f2f7827f938bdb9e3582219da820c742` 第3节写明：备份之后旧Core仍可变动，pre witness不是最终C计划；post获取root lease后对当前DB重新census并冻结C PlanCore。旧backup不得覆盖当前root。第2节要求opaque boundary permit绑定operation/plan/native root/DB与held lease generation，第4节要求post重新验证持久围栏与当前状态。

固定 revision02 `C-ARCHITECTURE.md` SHA256 `96256d1b33fac0a809efa3e0110ef6335c98b3c301241fcd8bc02262cfdc9185` 的 Frozen plan and deterministic writes 定义 `plan_hash = SHA256(canonical PlanCore)`；proof包含此hash；FullPlan再包含Core、proof精确bytes和planned rows，其原始文件摘要为 `plan_file_sha256`，idempotency request_hash使用后者。proof不包含自己所属FullPlan的文件摘要以避免hash自引用。此定义由CP533继承，不能把相同名称plan误解成同一摘要。

因此存在三个用途不同的摘要：

| 名称 | 何时冻结 | 内容及消费者 |
|---|---|---|
| boundaryPlanSHA256 | pre/ARM之前 | EntryFencePlan、原生root/DB/helper/entry/fence/backup身份；boot pre/post/events、OpenCurrentQuiescence和boundary Check使用 |
| cPlanHash | post重新读取当前状态后 | canonical C PlanCore；含同operation及明确boundaryPlanSHA256引用、当前census/CAS/Owner/subject/计划IDs/times/写集；C proof和C核心计划验证使用 |
| planFileSHA256 | C proof与planned rows固定后 | 原始FullPlan字节；C journal发现/精确文件绑定、idempotency request_hash使用；不能用前两者冒充 |

三者不得互换；不依赖摘要恰好不相等作为验证，只按明确的内容与用途分别重算。operation统一，dataRoot/database native identity、subject和generation仍须各自验证，字符串operation相同不能替代其余绑定。

## 无循环的阶段顺序

1. **ONLINE/ARM之前**：独立helper只消费已接受在线backup/identity清单与固定entry计划；不获取旧Core持有的业务root lease，不启动Host/store/provider。先冻结boundaryPlanSHA256，再产生pre witness和围栏记录；此时没有最终C PlanCore，也不能拿旧backup census预先代替post事实。
2. **early C mode识别**：在任何normal/replay/replacement/inherited setup之前判定唯一mode。只读读取boundary plan/state可用于参数/阶段核验；`ReadBoundaryPlan`返回的JSON/结构体是证据，不是事务authority。不因解析完成就允许打开普通Host或调用带migration/bootstrap的store.Open。
3. **post前提核验**：在BOOT_OBSERVED且真实当前boot/fence有效时，取得/验证同一root native lease，按既定双namespace规则放行本阶段；使用同operation与**boundaryPlanSHA256**构造opaque CurrentQuiescence并保留native holds。获取dispatch owner及原raw/MODEL holds。不能要求此时提供尚待census计算的cPlanHash。
4. **post只读census与C preflight**：沿维护专用既存DB连接读取schema24/87表及当前Owner/subject/raw/effect，保持锁和证据身份稳定；不Host.New、不普通store.Open、不migration/provider/key/listener，不创建C journal/BEGIN或业务写入。在此实际视图上生成C PlanCore，显式包含boundary摘要与统一operation，再计算cPlanHash、构造proof、冻结FullPlan及planFileSHA256。只读事务结束后按Rollback返回→Close释放仅属于该次preflight的holds；外层root/boot holds不能被内部helper误关闭。
5. **独立commit调用**：读取精确FullPlan，分别重算其文件摘要、Core摘要与boundary引用。重新获取/验证真实root lease与current quiescence，并重新读取当前权威/subject/evidence；以原生写reservation保障事务中census/CAS重建与完整写集一致。C journal存储完整C计划bytes及其两类C摘要，own-recovery绑定沿现有journal合同执行，不用boundary摘要替代C文件/核心摘要；durable BEGIN在第一项DB变更前。
6. **最后验证与释放**：C私有消费者核验当前boot q与这个精确C计划的组合绑定，实际接受/commit前重新Check；实际Commit/Rollback返回后再Close全部opaque holds。任何C计划改变都使旧的C授权/closure失效；不能仅凭同一个尚未Close的boundary q、同operation或旧cached proof替代新C计划的完整重建/绑定。底层q仅证明边界的事实，不单独代表任意C写入许可。

若public `OpenCurrentQuiescence(..., planSHA256)` 和 `Check(..., planSHA256)` 保留现有形参名，注释和所有调用点仍须明确它指boundary摘要。Host私有组合验证负责额外绑定cPlanHash和planFileSHA256；不能向boot历史记录回写最终C摘要来伪造pre时已知的事实。无需新增另一套机制。

## 新增独立断言

| ID | 输入/切点 | 可观测断言 | 资源与限制 |
|---|---|---|---|
| PLAN-01 | 固定pre boundary，模拟backup后、post前当前DB允许变化 | post census读取最新值；C PlanCore由最新视图产生且引用原boundary摘要；subject或不可解释变化仍拒绝；不还原旧backup、不回写pre witness | F/N；实际boot A/R未授权 |
| PLAN-02 | 用boundary摘要代替cPlanHash或FullPlan摘要，反向互换三个位置 | 按内容和用途独立重算后拒绝；不创建C BEGIN、不写DB；不能只比较字符串相等或长度合法 | S/F |
| PLAN-03 | 不存在C计划但BOOT_OBSERVED合法；观察early preflight到census顺序 | 能完成只读post census并生成新C PlanCore；不要求最终C摘要才能构造用于census的q；sentinel显示Host/bootstrap/store迁移/provider/key/listener调用0、C journal0、业务delta0 | S/F/N |
| PLAN-04 | ReadBoundaryPlan返回合法结构体，但无opaque q、wrong boot state或lost lease | 不能仅凭证据对象进入事务；若实现允许信息性preflight，其输出明确无authority；最终commit仍失败且0delta | S/F/N |
| PLAN-05 | 相同boundary/operation下改变C before census、author、subject、planned IDs/time、proof bytes或任一planned row；继续使用旧closure/marker | 旧C授权失效；Core/file digest及private consumer重验拒绝，0delta；不能因为q.Check(boundary)仍通过就接受改后的C计划 | S/F/N |
| PLAN-06 | 同C计划改变boundary引用/op/root/native DB/generation，或把另一boot operation的q送入 | 全部拒绝；同时验证boundary与C两个层次的绑定；单独operation字符串相同不足 | S/F/N |
| PLAN-07 | preflight结束→commit之前发生DB/evidence变化；提前Close或复制旧q | commit在真实reservation内重建census/CAS；漂移拒绝；private历史与q native holds持续到实际Commit/Rollback返回，不能复用已经结束的preflight authority | F/N |
| PLAN-08 | C journal/recover/replay读取三摘要；相同operation但不同C FullPlan | journal精确指向C FullPlan bytes；replay同plan0delta，不同plan冲突；recover不能用boot摘要找到另一份C计划或绕过已冻结C marker | S/F/N |
| PLAN-09 | proof内的plan_hash与FullPlan request_hash构造 | Core独立于proof最终bytes；proof引用cPlanHash；FullPlan文件hash只在外部marker/journal绑定使用，避免要求FullPlan包含自己的原始文件hash；确定性重建产生同bytes | S/F |

## 有限mutable观察，不作为接受

`014-mutable-plan-binding-read`及`015-mutable-plan-binding-lines`是只读快照，不执行候选。

- boot_windows.go SHA256 `96a287f36a0bcf6b9aae6b92b079cc4f8175349e8b720bb2d65472648e3c1442`：Open/Check当前均在EntryFencePlan.PlanSHA256层验证；611–644的ReadBoundaryPlan声明只返回数据，使用boundaryPlanSHA256参数。该接口区分与合同方向一致，但不证明Host接线已完成。
- domain qualification_failure_maintenance_windows.go SHA256 `d154c448b7ef10dc6420b61d9b914300b8ae6b078310a26090c4e61f329be942`：411–444计划结构有BoundaryPlanSHA256及独立Core/coreHash；621–674的PlanHistoricalQualification使用只读事务和当前census构造。仍须在冻结后验证调用者顺序、实际无副作用、commit最终组合绑定及proof生命周期。
- 本次已向两个builder发送上述合同定位和顺序。未持续追踪mutable文件，也未验证它们最终完整性。

## 本追加的执行记录

014、015只读命令native exit均0；新增非零退出0、工具协议诊断0；原阶段1累计原生非零2保持。另以016补充finalizer捕获本文件与新增命令，原PHASE1-manifest/seal/diganostics文件原样保留。若finalizer失败，必须追加新诊断，不修改历史计数。

完成后等待Root phase2精确冻结授权。

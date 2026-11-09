# 03 数据合同

版本：2.0.0。规范日期：2026-09-30。生效依据：00_START_HERE.md 与 01_PRD.md。机器合同为 `contracts/domain.schema.json`（JSON Schema 2020-12），API 为 `contracts/openapi.json`。这些是待实现合同；产品实现、数据库迁移、供应商调用、Windows 验证均为 **NOT_RUN**。

## 1. 边界与表示

1. 一个被管理项目只有一个 ProjectState。Markdown、侧栏、Agent 上下文文件与第三方产品画面均为投影或输入，不得产生另一份任务完成真值。
2. Paperclip 路线把同一 issue/goal/run ID 映射为本域合同，使用其唯一领取与调度事务；ResearchOS 增加合同/证据/验收字段。THIN_CORE 路线才自行持久化 Goal/Task/Run。不得两条路线同时创建领取账本。
3. ID 是不透明字符串，不从显示名推断项目身份。全部 JSON 使用 snake_case。未知时间、金额、模型概率用 `null`；不得用 0 或空字符串冒充已知。时间用 RFC3339 UTC `Z`，计划时区保存有效 IANA 名，默认 Asia/Shanghai。
4. 所有普通对象带 `id/project_id/revision/created_at/updated_at`。不可变回执带 `revision=1/receipt_hash/created_at`，没有可写 updated_at。BudgetPolicy、RunPolicy 的 GLOBAL 范围例外：`project_id=null`、`scope_id="global"`、`parent_policy_id=null`；非 GLOBAL 必须关联项目和父策略。
5. 金额是 `{"amount":"12.50","currency":"USD"}`。禁止二进制浮点金额、隐式汇率、把未知费用当零。概率可用 0–1 数值，但不是现实成功率。VersionRef 固定为 `entity_type/id/revision/content_hash`，内容对象及回执的 hash 必须非空；普通结构聚合可为 null。
6. `sha256:` 后接 64 个小写十六进制字符。文件 hash 对封存原始字节计算。结构回执 hash 对剔除顶层 receipt_hash 后的 JSON 做 RFC8785/JCS 规范化，再 SHA256；实现依赖由 W02 锁定并以 Unicode、数字、字段顺序反例测试。禁止重复 JSON 键、NaN、Infinity。hash 是完整性绑定，不是身份签名；服务认证和独立验收权限另行校验。
7. Schema 对对象拒绝未知字段。服务开启日期/URI 等 format 校验；跨对象引用、大小关系、权限、业务状态必须执行下文不变量，不能以“通过 JSON Schema”代替业务验收。
8. `measurement_mode=FIXTURE|LIVE` 与 `evidence_kind=OBSERVED|SIMULATED|GENERATED` 是两维：真实调用模拟器仍为 LIVE+SIMULATED，真实模型生成文本通常为 LIVE+GENERATED；真实运行截图/测试回执可为 LIVE+OBSERVED。测试包中 LIVE_WINDOWS 等场景标签不改变此枚举。

## 2. 实体与归属

| 实体 | 核心职责与可变范围 | 实施任务 |
|---|---|---|
| ProjectProfile | 意图、约束、来源配置、授权快照、已知事实与假设；变更经提案 | W03–W04 |
| ProjectState | 当前有效需求/决定/Goal、冲突、策略修订和事件序号；服务器事务维护 | W03–W04 |
| Requirement | USER_STATED/OBSERVED/ASSUMED/PROPOSED 基础、替代关系、验收映射 | W03–W04 |
| Goal | 意图、交付物、冻结验收、所属项目/系统范围、合法负结果 | W03、W06 |
| Task | DAG、输入、当前租约归属、产物及独立验收引用 | W03、W06 |
| Run | 一次执行、租约epoch、心跳、检查点、稳定结束、取消与恢复 | W05、W12 |
| Artifact | 内容寻址、字节hash、输入/来源、证据类别及有效性 | W03、W09 |
| Evidence | 主张/正反证、URL、上游版本、原始快照、独立来源键 | W07、W09 |
| ResearchCycle | 请求窗口、来源覆盖、必需实验、判断与游标检查点 | W08 |
| Experiment | 预注册假设、基线、指标/阈值、输入、停止条件、测量结果 | W10 |
| DecisionReceipt | 模型信号、程序检查、输入/rubric/资格、选择/弃权；不可变 | W11 |
| Qualification | 用途×语言×provider×模型版本×rubric版本、标签和holdout结果 | W11 |
| ContextBundle | 当前任务的事实/未决项/未完承诺/来源与版本向量；不可变快照 | W04 |
| ChangeProposal | 修改理由、影响闭包、冲突、迁移、回退、验收与生效修订 | W04 |
| ImpactLink | 有类型的依赖、实现、核查、派生、替代、反证关系 | W04、W09 |
| BudgetPolicy | GLOBAL/PROJECT/GOAL/EXPERIMENT 金额模式、周期和父策略 | W12 |
| RunPolicy | GLOBAL/PROJECT 总并发、队列、周期、重试、心跳和租约 | W12 |
| ResourceRequest | 缺资源/业务选择、去重、可继续分支、恢复证据 | W12 |
| MilestoneRelease | 每项目单调成果序号、验收及hash、后续事项；不可变 | W13 |
| ProgressProjection | 六阶段计数、计划修订、最近有效进展；可重建、只读 | W13 |
| SkillVersion | 预期/成功/失败资料清单、版本、资格、变量、作用域、回滚 | W15 |
| SystemCandidate | 稳定与候选hash、隔离环境、冻结基线、试用、晋升/回退 | W16 |
| AcceptanceReceipt | 冻结合同、输入/产物版本、检查、验证者及结论；不可变 | W06 |
| AgentMessage | 任务/Run关联、发送主体、引用、去重；内容不直接改变状态 | W04 |
| SourceCursor | 来源查询游标、已覆盖时间、重试时间、合并待扫窗口 | W07–W08 |
| BudgetLedgerEntry | 预留/实际/释放/未知/对账及供应商事件；追加不可变 | W12 |
| NoProgressRecord | 原问题+候选+输入hash计数，不能以新子Goal清零 | W12 |
| RuntimeRegistration | 适配器版本、实测能力/平台/恢复能力及资格 | W05 |
| Notification | 应用内成果或资源通知、用户已读；不含外部发送授权 | W13 |
| Conflict | 明确相冲突的对象及阻塞范围、整合提案 | W04 |
| EventEnvelope | 有序、可去重域事件，事实引用与因果链；追加不可变 | W03、W12 |

`$defs` 中其余定义是上述实体的字段结构、状态枚举、类型化请求或响应，不是额外调度子系统。机器文件顶层 oneOf 接受这 31 种核心实体；请求/单个类型通过其 `$defs` 校验。

## 3. 唯一标识、索引与持久化约束

实现使用真实外键或等价服务器约束，不以 JSON blob 存在代替关系完整性。SQL 的具体建表与迁移在选路后的 W03 产出；以下约束不可因底座选择省略。

| 约束/索引 | 必须保证 |
|---|---|
| ProjectState UNIQUE(project_id) | 一个项目一个权威状态 |
| 所有项目引用 | 引用对象同项目；显式共享必须先建有来源/作用域的导入副本，不可只猜ID越权 |
| 任务依赖 | 同项目、无环，ACCEPTED且当前有效才放行；任一依赖失效仅失效影响闭包 |
| 有效任务租约唯一 | 一个Task最多一个有效执行Run；epoch递增，旧epoch不能写新归属 |
| ResearchCycle 活動唯一 | 每项目最多一个PLANNED/RUNNING周期，漏触发写一个合并窗口 |
| Evidence UNIQUE(project_id,canonical_url,upstream_revision,snapshot_hash) | 同快照幂等；同内容转载可保留不同传播记录，但independence_key相同 |
| SourceCursor UNIQUE(project_id,source_id,query_hash) | 每查询来源一个增量游标；分页成功和窗口覆盖成功分开 |
| Artifact UNIQUE(project_id,content_hash,kind) | 字节内容去重；同hash不同来源以引用保留，不覆盖来源链 |
| NoProgressRecord UNIQUE(project_id,key_hash) | key_hash取原始问题+候选+输入hash；子任务共享计数 |
| ResourceRequest 活動去重 | OPEN/ACKNOWLEDGED下(project_id,category,account_ref,reason_code)唯一 |
| MilestoneRelease UNIQUE(project_id,sequence) | 序号单调，software_version另记；旧成果不可覆盖 |
| Notification UNIQUE(release_id或resource_request_id,recipient_id,channel) | 离线补看/重复投递只生成一条逻辑通知 |
| BudgetLedgerEntry UNIQUE(provider_event_id,账户范围) | 迟到/重复账单不重复扣记，UNKNOWN不被丢弃 |
| Event UNIQUE(project_id,sequence), UNIQUE(id) | 事务内递增；消费者去重；outbox未确认前保留重送 |
| 幂等记录 UNIQUE(principal_id,project_id,operation_id,key) | canonical request hash、初次响应、资源ID及状态持久化 |

删除默认采用撤销/归档与新版本；已被验收、来源、回执引用的内容不能物理删除而留下悬空证据。备份/保留期限由运维合同管理。列表按稳定 `(created_at,id)` 或事件序号游标，绑定查询/项目/快照，不采用易漏项的动态offset。

## 4. 状态迁移

### 4.1 Task 与 Run

Task 固定枚举：`DRAFT, READY, RUNNING, EXECUTION_REPORTED, VERIFYING, ACCEPTED, FAILED, BLOCKED, CANCELLED, NEEDS_REVALIDATION, DEFERRED_NO_PROGRESS`。

| 原状态/事件 | 服务器结果 | 必须条件 |
|---|---|---|
| DRAFT + SUBMIT | READY；依赖未满足则BLOCKED并标原因 | 计划和验收已冻结、DAG合法 |
| READY + claim | RUNNING，创建唯一Run | 当前上下文、预算/权限、依赖均有效，原子领取 |
| RUNNING + settled report | EXECUTION_REPORTED | 当前租约、真实settled日志、产物已封存 |
| EXECUTION_REPORTED + 独立验证启动 | VERIFYING | 验证主体/Run独立，保持原执行记录 |
| VERIFYING + PASS receipt | ACCEPTED | D01–D08全部满足，同事务释放后继 |
| VERIFYING + FAIL/BLOCKED receipt | FAILED/BLOCKED | 保留失败/未运行项，有限返工可以形成新Run |
| 受影响有效输入变更 | NEEDS_REVALIDATION | 旧产物/旧回执保留但不再视为当前通过 |
| 到达无进展阈值 | DEFERRED_NO_PROGRESS | 保留最好合格产物、计数和恢复条件 |
| PAUSE | BLOCKED | 记录USER_PAUSED，不假装执行器已经停止；有Run则先取消/对账 |
| CANCEL | CANCELLED或等待停止确认 | 有Run时必须完成取消对账后才最终CANCELLED |
| RESUME/REVALIDATE | READY或BLOCKED | 新输入/新版本/资源恢复等有效原因；不得无条件清零计数 |

无任意 `PATCH status=ACCEPTED` 接口。所有枚举值不是任意互转。ACCEPTED→NEEDS_REVALIDATION合法；CANCELLED不能通过旧回执恢复，重新工作建立合法新尝试并保留取消史。Goal ACCEPTED由必需任务/最终验收组合产生，不能只看子任务数字。

Run 固定枚举：`QUEUED, STARTING, RUNNING, CANCEL_REQUESTED, SETTLED, FAILED, CANCELLED, LOST, RECONCILING`。执行稳定结束、任务验收、整个持久RPC进程退出是三件事。Pi的输入接收/agent_end不替代agent_settled；取消清队列后abort并验证本Run子进程停止。进程丢失先RECONCILING，不直接复制副作用。旧epoch停止证据可以追加归档，但不能改变新Run归属；迟到账单仍按供应商事件对账。

### 4.2 周期、判断和演进

- ResearchCycle COMPLETE：必需来源请求窗口覆盖完整、必需核查/实验都有结果、决定/游标/后续任务保存。必需项缺失为PARTIAL，实质无法推进为BLOCKED；负实验及“无候选可采用”允许COMPLETE。
- Experiment DRAFT→REGISTERED时冻结假设、输入、基线、指标、阈值、预算与停止条件并计算 preregistration_hash。之后改标准创建新版本/实验，旧失败不被覆盖。COMPLETED可以是NO_IMPROVEMENT或REGRESSED。结果为INCONCLUSIVE时保存缺口，不宣称必需测量成功。
- DecisionReceipt只记录判断，不是执行授权。`DISMISS/WATCH/INVESTIGATE/EXPERIMENT`用于初筛；`ADOPT/REJECT/WATCH/INCONCLUSIVE`用于采用建议；`ABSTAIN`为宿主弃权状态。selected必须在options内；采用需要单独符合任务授权及验收。
- Qualification 的SHADOW/ADVISORY/BOUNDED_AUTO按精确scope生效，provider/模型/rubric变更不继承。默认资格集和阈值详见06：每个 task_type×language×provider×model_revision×rubric_revision 键独立达到至少60开发/校准样例和30互斥holdout样例，关键错误采信为0，holdout错误采信率不超过5%，才可能获得对应资格。初轮合计90例及中文/混合覆盖不能替代单键门；样本不足键保持ADVISORY，正确降级不妨碍A08产品安全合同通过。候选用自己的评分规则给自己提分不构成升级证据。
- SkillVersion CANDIDATE→EVALUATING→QUALIFIED→ACTIVE须过来源覆盖、变量/许可、隔离评测及独立验收；回退引用可定位。没有前版时关闭候选就是回退方案。
- SystemCandidate DRAFT→ISOLATED→EVALUATING→CANARY→PROMOTED；失败REJECTED/FROZEN，回退ROLLED_BACK后冻结。PROMOTE只能由独立RELEASE_SERVICE执行，不由候选进程调用。没有可验证回退不得晋升。

## 5. 必须由服务器执行的不变量

| ID | 规则 | 对应验证 |
|---|---|---|
| D01 | 执行主体不能作为同结果的验收主体；不同显示名但同执行身份不算独立 | R09 / A03、A04 |
| D02 | 必需确定性检查全部PASS；MODEL_RUBRIC需匹配有效资格；PREFERENCE只在确需用户选择时保留未决 | C07、A08 |
| D03 | 运行前冻结合同、输入/产物版本及rubric；验收回执与实际字节重新对账 | C03、C10、A07 |
| D04 | 有影响当前结果的OPEN冲突不得PASS；无关冲突不得阻塞全项目 | C03–C04 |
| D05 | 产物/回执不可覆盖；纠正以新版本+supersedes表达，撤销改变有效性不抹历史 | C03、C12 |
| D06 | PASS+最终业务状态+后继释放+outbox在唯一事务内；不能先done后异步补验收 | A02–A03 |
| D07 | ContextBundle固定语义依赖版本；验收比较实际输入和适用策略，不因无关聊天/投影revision变化全局失效 | C01、C03 |
| D08 | 当前主体的project/task/run权限、有效租约epoch及工具作用域每次执行前检查；外部文本不能授予权限 | C02、A11 |
| D09 | 证据快照可定位；转载共用independence_key，SIMULATED/GENERATED不能冒充现实独立来源 | C19、A05 |
| D10 | 来源published_at未知仍保留null；抓取时间不替代发表时间；覆盖窗口逐源判断 | C06、A05 |
| D11 | 游标推进须与已保存证据/检查点对账；失败页、限流、离线不被标成已扫描 | C06、C11 |
| D12 | COMPLETE判定针对冻结必需来源和实验；不得运行后移除失败必需项 | C05–C06、A13 |
| D13 | UNKNOWN模型概率、低置信、证据不足先弃权/补证/合格回退；不默默换模拟调用 | C07–C08 |
| D14 | BOUNDED_AUTO资格精确匹配scope，真实资格不能由FIXTURE或模型多数票产生 | A08 |
| D15 | GLOBAL总并发默认2、总队列100；项目只可收紧，不能每项目各2绕过总限制 | C13、A14 |
| D16 | 金额默认UNLIMITED_AMOUNT、cap=null。生效约束取GLOBAL→PROJECT→GOAL→EXPERIMENT所有上限交集 | C13–C14 |
| D17 | STRICT需可靠费用上界和原子预留，未知则阻塞；限额收紧阻止新调用，已在途费用持续对账 | C14 |
| D18 | 相同错误/输入最多自动重试2次；连续3次无新增有效证据/预注册改善延期，子任务不清零 | C16 |
| D19 | SourceConfig必需源不能通过禁用规避当前周期；政策修改只影响合法新周期或明确重规划 | C06、A05 |
| D20 | Skill expected_source_ids必须分解为processed与failed，交集为空且无遗漏；失败必需输入阻止晋升 | A09 |
| D21 | 候选不得改变用于评定自身的规则、标签、权限和稳定监督器；另立规则变更任务独立评审 | C09–C10、C20 |
| D22 | 晋升绑定冻结基线、实测回退/迁移和独立试用；退化自动退回稳定版本并冻结 | C12、A16 |
| D23 | 成果与通知同事务，通知去重；IN_APP之外未配置渠道不自动发送，成果版本不隐含Git push | C17 |
| D24 | ProgressProjection每阶段planned/accepted/pending_review/blocked/active真实计算；六阶段各一次，不提供总体伪百分比 | C18 |
| D25 | 固定版本/只读快照检索；缓存键含项目权限范围+输入hash+backend revision，过时内容返回STALE | A06 |
| D26 | 恢复先对账唯一Run和租约；重放消息/事件不重复副作用，无法确认外部状态时阻塞相关支路 | C11、A04、A14 |
| D27 | schema只检查形状，跨引用/时间区间/总数/集合完整性/权限/业务状态在域服务检验；CheckResult PASS必须至少一个可核验证据引用 | A03 |
| D28 | Fixture、上游作者测试、当前Windows/供应商实测各自标识，不能升级措辞成为本项目PASS | A01、A13–A15 |

## 6. 权威修订与影响传播

写入实体前比较其revision；实质需求/决定/产物替换经过ChangeProposal。依赖闭包确定性计算，语义审查只补充潜在影响，不能宣称发现所有自然语言冲突。apply事务创建新版本、标记受影响任务NEEDS_REVALIDATION/产物STALE、更新ProjectState并写事件。旧Run继续持有旧输入快照；提交可以归档为历史，但不能晋升为当前成果。无关任务继续。

ProjectState revision用于取得一致快照和变更提交条件；一个新消息或无关Goal更新，不使全部正在执行的ContextBundle自动失败。接受时校验的是其version_vector中的实际依赖与适用政策。策略收紧是新的有效约束，未发生的新外部调用必须遵守。

## 7. 默认值与恢复

- 初始全局BudgetPolicy：UNLIMITED_AMOUNT、cap=null、ACCOUNTING_ONLY、ALLOW_AND_RECORD。项目/Goal/Experiment预算可继承无限，但任何父级已设置上限仍生效。
- 初始全局RunPolicy：max_concurrency=2、max_queue=100、monitor_period_seconds=21600、first_lookback_seconds=604800、max_active_cycles_per_project=1、same_failure_retry_limit=2、no_progress_iteration_limit=3、heartbeat_seconds=15、lease_seconds=90。Schema的default仅为文档，服务器必须显式写入。lease_seconds必须大于heartbeat_seconds；新增来源配置时服务器创建其SourceCursor，创建Task时生成或复用NoProgressRecord。预算DAILY/MONTHLY按策略时区自然日/月重置计数，LIFETIME不重置；未结算在途预留不因跨周期而消失。
- SourceConfig至少配置GitHub/X/PAPER三类作为首轮请求范围；资源缺失允许独立源继续但对应完整实测门保持BLOCKED/PARTIAL。首个默认被管理项目为ResearchOS自身，不自动读取QuillClub或xiaoshuo。
- 所有服务恢复从数据库、sealed artifact、source cursor、outbox和租约对账；聊天摘要不是恢复数据库。备份必须包含内容库和配置/凭据恢复策略；恢复后的消费游标不会删除历史回执。

## 8. 合同版本升级

未知字段当前拒绝；新增字段/枚举先提升合同版本并提供可回滚迁移与兼容适配。不能在运行中重解释旧receipt_hash。保存每个Run的schema/adapter版本到其封存manifest。数据库升级先备份与恢复演练，独立监督器能回到旧程序与可用数据；不可逆迁移不得声称普遍热回退。

## 9. v2.0评测产物与访问分类

Artifact及CreateArtifactRequest新增必需字段access_class，枚举PROJECT/VERIFIER_ONLY。服务端根据来源与主体强制分类，执行者不能把受限派生内容声明为PROJECT。正式留出输入、标签、逐例输出、详细评分与日志均受限；明确有权Owner和独立Verifier可检查。PROJECT并非公网或所有项目可见。

EvaluationCaseResult、EvaluationCounts、EvaluationReport、EvaluationSummary是产物内容Schema，非新增ProjectState实体。EvaluationReport对应TEST_RESULT Artifact，保存引擎/版本、配置/基线/候选/数据集/rubric hash、预期ID、逐条结果、计数、费用、退出状态与原始证据引用。HOLDOUT报告必须VERIFIER_ONLY。公开EvaluationSummary不包含题目、标签或逐例结果。

跨字段规则由实现检查：expected = observed + missing；observed = pass + fail + error + abstain；ID不重复、无未知ID；统计和完整性与原始导出一致。COMPLETE只说明报告完整，含FAIL并不矛盾；hard_checks_passed=false不能PASS；零样本/版本错配/重复结果不得通过验收。错误、弃权、缺失不缩小分母，未知费用保持null。

报告/Artifact/Run/Experiment的project_id与引用必须一致。受限内容不能经ContextBundle、事件详情、缩略图、缓存、搜索、导出或备份泄漏；公开汇总只保留不泄题信息与受控引用。模型分数不会生成AcceptanceReceipt。

本版修正A08机器输入中的qualification_key，明确包括provider，与QualificationScope及文字要求一致。机器Schema和OpenAPI版本均2.0.0；HTTP路径继续/v1，本包版本不等于产品发布版本。

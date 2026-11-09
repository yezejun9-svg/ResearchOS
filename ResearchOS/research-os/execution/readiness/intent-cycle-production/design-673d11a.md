# 自然意图与周期推进：最小施工设计

状态 `DESIGN_READY_NOT_IMPLEMENTED`。审阅 HEAD `673d11a5cce9a61820117642220f355a11cf84f1`，对应 `R01-NATURAL-INTENT-01` / `W08-PERIODIC-DISPATCH-01`。本次仅写本文件和同名 JSON，未改源码/spec/ledger，未运行产品、模型、服务或测试。沿用 Ponytail 原则：复用现有 Requirement、Goal、Task、Run、Artifact、ResearchCycle、SourceCursor 和 S2 唯一协调器，不加 intake HTTP endpoint，不创建第二任务队列。

结论：使用**专门交付规划提案的 Goal/Task**解除引导环。用户原话先成为 USER_STATED Requirement；服务端用已实现、可验证的平台规划合同创建规划 Goal/Task；合格运行器产出 GoalBrief Artifact；独立验证其来源/结构/权限/可执行映射后，trusted compiler 才物化业务 Goal/DAG。平台检查只接受“提案是否完整且如实标明未知”，不宣称业务问题已解决。周期驱动是在 S2 loop 中增加创建和推进既有领域对象的步骤；READY worker loop 自身不够。

## 1. 已证实的合同约束与缺口

| 锚点 | 事实与影响 |
| --- | --- |
| `spec/v2.0/01_PRD.md:90,122` | R01 用户无需填架构、测试命令或字段；R05 长期监控与有限 ResearchCycle 分开，来源缺失不得完整 |
| `spec/v2.0/10_UI_UX_DESIGN.md:19` | S00 自然想法输入，由系统整理范围并创建 Goal |
| `spec/v2.0/03_DATA_CONTRACTS.md:20` | 没有独立 GoalBrief 实体；它可作为 versioned Artifact，不能向 Goal 随意加 schema 外字段 |
| `spec/v2.0/contracts/domain.schema.json:5378,5433` | CreateGoal 要已确定 deliverables/AcceptanceContract；CreateTask 要 goal_id；AcceptanceContract checks 至少 1、独立验证 const true |
| `apps/web/src/screens.jsx:28` | IdeaForm 必填 deliverable/check/command，前端手造 checks/hash；只建 DRAFT Goal，无 planner 消费 |
| `internal/domain/operations.go:92,98,148,164` | Requirement 初始 PROPOSED；USER_STATED 可接受，ASSUMED/PROPOSED 不可直接 ACCEPT；Goal 仅引用 accepted requirements；Task 需所属 Goal 和 origin problem |
| `internal/domain/orchestration.go:181,235` | Goal ACTIVATE 冻结合同，Task SUBMIT 要 ACTIVE Goal、ContextBundle、依赖和有效进展门；不能先跑无 Goal 的 planner Run |
| `internal/domain/acceptance.go:162`、`acceptance_goal.go:47` | 当前 command handler 有限；Goal LIVE 接受固定阻塞。结构合法/模型成功不等于任意业务验收通过 |
| `internal/domain/research.go:53,144,245,327` | create 时已有 due/coalesce；coverage 依 W07 原始 page chain；checkpoint/close 已有持久化，但没有生产 tick/stage driver |
| `migrations/sqlite/0013_research_cycles.sql:1` | 每项目最多一个 PLANNED/RUNNING；已有 candidate review 记录，无第二周期队列需要 |
| `internal/domain/sources.go:78,281,341,581` | 已有严格 cursor advance、真实 source adapter、持久 retry_after；不能把 clock tick 当成功 page |
| `internal/domain/candidates.go:10` | 有可信本地 candidate review，负结果合法；ADOPT 要当前来源支持和独立接受的改善实验，但这只是建议，不自动应用项目 |
| `internal/domain/decision.go:168` | BOUNDED_AUTO 仍明确关闭；planner runtime 资格不能代替 Jev 用途资格 |
| `internal/domain/changes.go:79,142` | 现有 ChangeProposal 内部允许字段很窄，不能声称已能任意修改 Goal/来源配置；不能 SQL 绕过 |
| `internal/domain/orchestration_progress.go:7` | NoProgressRecord 以 origin problem/candidate/input_refs hash 建键；新周期 ID 不能用来重置同问题计数 |

上游设计 `execution/readiness/runtime-production/design-1768c89.*` 的 S1 负责资格引导/qualifyRuntime，S2 负责正常执行与可信桥。其明确未包含 Goal LIVE 完成；这里须补规划 Goal 所需的窄接受分支，不能假设它已存在。W07 LIVE 采集/原文核查、W10 实验、W11 独立判断、W14 真实闭环均须当前有效；`RQ-W05-CLI-POLICY-001` 及既有 production activation/protected broker 限制不变。

## 2. 用现有 API 保存自然表达，不把技术输入推给用户

`IdeaForm` 仅必填“你希望推进什么”，业务补充可选；移除必须填写 command_key/数据字段的要求。按钮文案为“保存想法并整理方案”；显示保存、规划、缺资源、待业务答复、方案可执行等真实状态。不要在规划尚未完成时叫“创建正式目标成功”。

提交仍走已冻结 `createRequirement` + `actOnRequirement`，保留 If-Match/Idempotency-Key 与当前冲突 UI：

- 原话原样保存 Requirement.text、basis=USER_STATED；rationale 记录用户提交，acceptance_check_ids 可空。只有这次明确提交的原话被接受，不替用户确认系统补充。
- 使用有文档约定的 requirement_key，例如 `INTENT-<submission-id>`，这是现有自由字符串字段的语义约定。server 在成功接受该 Requirement 时登记 private intake binding；必须核验本次真实用户/Owner 提交身份和项目权限，不能只因外部文本或模型输出包含前缀就启动。
- UI 保留同一 submission-id/幂等键直到服务端确认；刷新后按已存 Requirement/Goal/Task 查回。服务端 key 以 `(project, accepted Requirement id+revision)` 唯一，无法因浏览器重试建多份规划 Goal。
- 普通非 intent Requirement 行为不变；模型进程不持有 OWNER/PLANNER mutation token。PLANNER/SCHEDULER 若代用户登记必须有原始输入引用和已存在授权，不能把自己生成的内容标为 USER_STATED。

项目首次创建已有 ProjectProfile.intent，但不能静默把所有历史 createProject 或 import-spec 再规划一遍。首版仅从显式 intent submission 触发，系统默认项目的创建仍复用原导入流程。

**不新增公开 intake API。** 现有 Requirement 足够承载原话，既有 Task/Artifact/get/list/events 足够展示过程。GoalBrief 是有内部严格 schema 的 JSON Artifact（可另生成 Markdown 展示）；不向 frozen `$defs` 新增对象。用户要求的 `SYSTEM_PROPOSED` 是 UI/GoalBrief 展示标签，持久 Requirement/Fact 必须映射 frozen enum `PROPOSED`，并保存 proposed_by/source refs；不得写不存在的 basis 枚举。

## 3. 规划 bootstrap：做真实提案任务，不伪造业务验收

S2 coordinator 消费已保存的 intake binding，先用当前 ProjectState/Requirement/profile/权限/资源创建专用规划 Goal，标题明确“整理这个想法的方案”。其 deliverables 仅为版本化 GoalBrief、任务 DAG 草案、未决问题和能力缺口；original_intent 保留用户原话，requirement_refs 引用原 accepted Requirement。scope 沿该请求被授权的 PROJECT/SYSTEM 范围，不让模型自选更高权限。

平台固定一个有版本的 **规划交付合同**，在代码中实现真实 verifier handlers，例如以下建议键，登记后方可使用；不是把测试名写入表就算实现：

| 规划检查 | 实际验证 | 明确不代表 |
| --- | --- | --- |
| `planning.provenance-v1` | raw intent hash/ref exact；原话引用位置可对照；OBSERVED 有当前来源；ASSUMED/PROPOSED 保留类型；原始输出/runtime/profile/run/epoch 全绑定 | 不能用字符串检查证明所有自然语言含义正确 |
| `planning.dag-capabilities-v1` | DAG 无环、引用同项目/版本正确；节点产物与明确完成条件、supported command/capability 及 typed 参数映射；缺能力如实 BLOCKED；没有任意 shell/SQL/URL 指令 | 不把“命令键存在”当实际命令已测通过 |
| `planning.open-questions-v1` | 未知业务事实和必须用户选择的事项明确；每个待答问题关联影响节点；方案状态 READY/NEEDS_INPUT/NEEDS_RESOURCE 与证据一致；不夹带已解决声明 | 不替用户选择客户、预算、成功阈值或商业方向 |

Goal 与其规划 Task 使用这组真实合同和正常 create/activate/context/submit/claim 流程；检查的 required=true、独立验证、exact hash 不省略。Task stage 可用既有 `discovery`，task_type 使用受控 `intent_planning`。后台可在一个短事务复用 domain helper 创建 Goal、Task 和 binding，再生成 ContextBundle/submit；不做 HTTP 自调用嵌套事务，不绕过 actor/grant/版本/事件校验。事务失败不留下未绑定的伪任务。

这打破 `Task→Goal→checks→planner` 的环，是因为第一轮 checks 检验 **规划提案交付**，而不是预先编出未知业务目标的通过答案。不得用 `orchestration.json-equals` 期待一个写死“成功”对象，或将永远可过的 envelope 检查当业务验收。

planner 是正常 S2 Run：有资格/预算/lease/输出密封，纯生成建议，不拥有 mutation authority。运行前资源门缺合格 LIVE model/tool 时创建实际 ResourceRequest（PERMISSION/CREDENTIAL 等现有类别、明确 reason_code），将相应 Task 合法阻塞，UI 可见；不调用 fixture/模型记忆填真实规划结果，也不重试被 policy 拒绝的工具。

原始 planner 输出和规范化 GoalBrief 一并封存为 GENERATED；真实调用可为 LIVE+GENERATED，不因 LIVE 变成 OBSERVED。GoalBrief 最少内容：raw intent ref/hash、project/context/version vector、USER_STATED/OBSERVED/ASSUMED/PROPOSED 逐项来源、范围/排除、产物、draft goal checks、DAG logical node ids/输入/依赖/outputs/checks、资源/预算约束、失败出口、open questions、缺能力、revision/supersedes/ref。自由文本不能赋予授权。

独立 Verifier 的正常 Task acceptance 运行上述检查并保存真实回执；人类或符合用途资格的独立语义审阅可检验意图忠实度。未有可验证的自动语义判断能力时保持提案性质，只能自动推进受当前明确意图与确定性规则覆盖的技术安排；关键业务方向仍须用户答复。不得因此宣布 Jev BOUNDED_AUTO 已启用，也不能把第二个同根模型当独立接受者。

窄补 `acceptance_goal.go`：只对具有 private intake binding 的规划 Goal，复用其全部 current accepted Task receipts、同输入/产物检查、每个底层 Run 的 S1/S2 当前资格与独立 root、mode-aware server evidence，允许接受 **提案交付 Goal**。现有 fixture 分支保留；普通业务 Goal LIVE 完成仍须其真实完成合同，不能全局删 503。若仅规划 Task 接受而此分支未实现，产品显示“方案任务已验收，规划目标接受待完成”，不能 SQL 把 Goal 改 DONE。

## 4. 从提案到业务 Goal/DAG：authority 在服务端

trusted plan compiler 只接收该 exact 已密封/独立验证的 GoalBrief，外加当前 facts、解决问题的 refs 和当前命令/资源能力 catalog。model 输出中的 IDs、command、dependency、权限和预算都是候选输入。它在事务中再次校验当前 profile/requirements/policy/独立接受与 raw hash，拓扑排序，生成稳定 logical-node→Task ID mapping，调用既有 createGoal/createTask helper、记录 typed ImpactLinks 和 outbox；不将模型 JSON 直接 `put` 到权威对象。

业务 Goal 的 requirement_refs 至少引用真实 accepted 用户意图；proposal 中的工程安排仍在 GoalBrief 标 PROPOSED，不为了满足 acceptedRequirements 把 PROPOSED 改成 USER_STATED。字段可以采用已有授权范围内的系统技术建议，但最终 checks 必须对应已实现且真正能验证所需交付物的 handler/独立评估；unsupported command、无合格 verifier、未知业务阈值均阻塞相应节点，不能改 required=false 或硬写“输出文件存在即成功”。

计划中的命令是平台 catalog 的 typed action/check 映射，不允许模型编程式注册 shell。已支持的项目研究流程可直接选择冻结 research verification/experiment 模板；任意新业务代码验收能力缺失时形成资源/工程缺口，不声称系统已经支持所有自然语言目标。公开 schema 的 CheckSpec 本来允许 command_key 字符串和 MODEL_RUBRIC/PREFERENCE，新增受控 handler 是实现工作，不是开放 arbitrary command。

必须用户选择的事项用已有 BUSINESS_CHOICE ResourceRequest，携带 exact问题/选项、影响 Task、可继续分支和提案 Artifact。用户回答仍作为新的 USER_STATED Requirement（关联原问题/原意图 ref），显式接受后经已有 `resolveResourceRequest` 提交有效 resolution refs；服务端重验答复确实解决对应问题。不能仅因 ResourceRequest.RESOLVED 就把实际资格/业务条件视为满足。

补充/修订引出新 GoalBrief Artifact 和输入版本，旧版本可追踪。已冻结 Task 合同不原地改；业务实质变化走 W04 ChangeProposal/impact/revalidation。当前 allowedEdit 不涵盖所有 Goal 字段，不能声称直接可改：首版必要时创建有明确替代关系的新 Goal/Task plan，保留 origin problem/candidate/no-progress，旧工作按既有 PAUSE/CANCEL/revalidation 处理。若要拓展 W04 对草稿 Goal 的受控编辑，须由 root 与当前 W04 worktree 串行整合并独立验证，不能更新 activated frozen contract。

跨规划 Goal 到业务 Goal 不能使用跨 Goal Task dependencies（现实现明确拒绝），使用 exact accepted Artifact/AcceptanceReceipt input refs 和 ImpactLinks；业务 DAG 内依赖仍属于同一 Goal。缺业务方向可交付一个合法 NEEDS_INPUT 提案，但不会自动创建/执行假定答案的业务分支。

## 5. 长期监控与单周期的控制入口

使用**明确登记的监控 Goal**承载长期研究授权，ResearchCycle 承载一次窗口。它仍是现有 Goal，不是新 monitor 服务：用户明确要求持续研究时，planner 产出的监控计划含主题/范围、来源策略、周期、退出/预算/失败条件；Goal deliverables 是这份已授权研究过程应产生的报告/证据，合同不凭空造改善百分比。Goal 保持 ACTIVE 期间可以多轮，无需把每轮结论当整个长期 Goal 完成。

其 ACTIVATE/PAUSE/RESUME/CANCEL 复用已有 actOnGoal；后台仅扫描有 private monitor binding 的 ACTIVE Goal，不因某项目存在任意 ACTIVE Goal 就自动开始持续采集。一个项目首版只允许一个 current monitor binding；第二个提议成为待合并/冲突，不并发创建两份监控 authority。手动一次研究仍可经现 createResearchCycle USER 路径；driver 为它绑定已批准研究 plan 或显示缺计划阻塞。

RunPolicy 已有 period/first lookback/coalesce/concurrency/retry/timezone，使用现有 updateRunPolicy 管理周期；没有 monitor_enabled 字段也不需要偷偷加：已登记监控 Goal 的生命周期就是启停。PAUSE 立即停止新周期/new stages/new source requests，已开始动作按 S2 安全停机/对账策略处理；不把正在执行的外部请求标为未发生。恢复继续原 cycle/Task/checkpoint，取消保留原结果与缺口。

source_configs 的 enabled/required/query 必须来自已授权 profile。现有 W04 allowedEdit 不完整支持来源配置，仍按冻结 UI 规范的受保护本地设置流程和 root 后续实现补齐，不在此私造 settings API；缺 credential/source 时保留 NOT_CONFIGURED，而非伪造 enabled 状态。

## 6. 在 S2 唯一 coordinator 中推进 due 与六阶段

S2 原 loop 的工作顺序扩充为：恢复未决 Run/effects → reconcile 已执行结果 → 消费已接受 intent/plan → 计算 monitor due/单轮窗口 → materialize 下一批受控阶段 Task → 正常 READY claim。使用同一个 data-root OS lock、authority DB、Scheduler identity、项目并发/队列/预算。不另起 cron service，不让 planner 自己轮询派单。

### Due、稳定身份与窗口

- 使用 UTC 持久时间与 RunPolicy 的 21600s 默认周期、首次 604800s lookback。首启按监控授权生效时间/最近周期求 due；不得把现在之前每一个漏 tick 建成一轮。每次 tick 可计算最新到期边界，但创建前短事务重查当前 monitor Goal、policy/profile revision 和唯一 active cycle。
- 复用 `createResearchCycle` 的 SCHEDULE 检查，已有 active 则读回；无 active 时将多次漏触发合成一个固定 `[last_cycle.window_to, due_boundary]`。每次事务生成一次 cycle ID，持久 binding/幂等 key；重启读已有对象，不重造 ID。时钟后退不得创建倒退窗口，前跳只生成一个有限工作窗口。
- “窗口有限”不等于可无限拉历史：为每轮/每次 adapter invocation 冻结 page/time/任务数/费用上界，单页最多现有 100；超过本轮上界保存剩余缺口/PARTIAL，不能悄悄抛弃旧区间或把 first-lookback 重新应用当截断历史。pending source window 的未完成部分优先续采，新窗口只排一次后续需求。
- SourceCursor 已有 pending_window/opaque_cursor/retry_after/covered_until；**不要把尚在分页中的 from/to 扩到新的 due**，旧 page chain 绑定 exact window。先完成或保留旧 pending；新 cycle 的更晚截止在周期 binding/下一次 due 保留。若完成旧段后补新段，coverage 必须验证连续的已密封 page-chain 区间并集，不能只看最大的 covered_until。当前 researchCoverage 要单个窗口覆盖全周期，需要最小增加无缝 interval union 校验，保留每段 query/hash/完整链，任何 gap 都不 COMPLETE。
- 429 持久 retry_after，loop 不忙等、不进程 sleep 等资源；source credential/query/profile 变更需重验，不能沿用旧 query cursor。来源结果与摄取幂等 key 至少绑定 project/source/query/window/page cursor，provider effect 保留 stable request hash。

### 阶段推进表

| 阶段 | 输入及动作 | 进入下一阶段/结束的依据 |
| --- | --- | --- |
| discovery | current monitoring plan、source configs、cursor、有限窗口；S2 创建各来源 capture Task，host 调 `CaptureSourcePage`，保存 raw/page refs；把发现关联 frozen open problem/intent | W07 durable page/evidence refs；缺 X 继续其他来源，并建去重 ResourceRequest |
| verification | 对候选原始出处、传播链、版本/hash、反证、相关性做验证 Task，复用 W07/W09；仅实际 OBSERVED raw 可作事实 | 当前独立验证 receipt；模型摘要不是来源验证；无证据候选可 WATCH/INCONCLUSIVE |
| experiment | 根据 accepted plan 的必要实验规则预注册 Experiment、baseline/candidate/metric/stop/budget；创建 exact Task/Run 并调用 W10 宿主执行 | 实际输出、完整覆盖、预算和独立 accepted Experiment。先登记 required IDs，不能执行失败后从周期删除 |
| review | 读取完整检查、来源支持及实验结果；模型可给建议，复用 `ReviewResearchCandidate` 保存 REJECT/WATCH/INCONCLUSIVE/ADOPT 建议 | 具名、可追溯且 current 的 reviewer 证据；ADOPT 仍不是应用，自动采用须已有用途权限，W11 未过则保留建议 |
| delivery | 汇总周期报告/合法负结果/缺口/后续并密封，经过正常独立 Task acceptance；实际业务变更另经 W04/W15/W16 接受与应用 | current artifact/receipt 和真实 milestone；没有采用也可完成，不强造成果收益 |
| follow_up / reconcile | 保存 watcher 条件、资源/游标、延后候选、运行/effect对账、NoProgressRecord；调用 checkpoint/close | `closeResearchCycle` 从当前证据计算 COMPLETE/PARTIAL/BLOCKED，用户取消则 CANCELLED；不靠模型自报状态 |

W07 采集是 trusted SOURCE_ADAPTER host 功能，不须把网络权限放进 model child。它仍必须挂在正式 Task/Run/授权/budget/effect envelope 内：当前 `CaptureSourcePage` 本身还没有 W12 reservation/run 参数；在调用边界加 S2 effect/budget admission 与 trusted output bridge，不绕过费用/出站控制。只读幂等 GET 的有界重试按 adapter+W12 合同记录；超时的计费/副作用结果不能换 key 隐藏 UNKNOWN。

阶段 Task 由受控 template + accepted plan materialize；planner 提出新实验或范围变更只产生候选，不自行写 required flags/acceptance。绑定每个 logical work key（source/window、evidence content+purpose、registered experiment、report）到同一个 Task/Run。driver 每次读真实 Task/Experiment/Receipt状态，仅在依赖当前 ACCEPTED 后创建/提交下一段。无测试 handler 或 verifier 即 BLOCKED，不 SQL 推进。

## 7. 必须同时修复的三个闭环边界

1. **close 的真实性**：现 `research.go:401` 只要 checkpoint_artifact_id 非空即 progress，candidate review 只数行。生产 driver 不保存空“我运行了”检查点当进展；close 增加所绑定阶段 accepted outputs/真实来源/实验内容校验、evidence/current reviewer/receipt/profile policy 再查，empty bookkeeping checkpoint 不构成实质进展。必需 verification/experiment/review 未完成不 COMPLETE；A13 至少一项 actual experiment 由预注册 plan 要求，普通无候选周期可合法不新增实验。现 required_experiment_ids 单调约束保留。
2. **profile drift 的退出**：现 checkpoint 的 `research.go:271` 与 close 的 `research.go:350–351` 在 close 处理 CANCELLED（`:411`）前先拒绝 profile revision 变化，可能永久占着唯一 active cycle。为已授权的 CANCELLED 增加窄终止分支：校验 active cycle/expected rev/角色，先安全停止及对账，保留 old/new profile refs/原因和原始结果，再正常领域关闭；不赋予成功状态、不删旧数据。若有未决 effect，则先保持 reconciliation 所需 blocker。新 cycle 用新 profile，旧 cursor/query不可偷换。
3. **不以周期换壳清零**：Task 的 input_refs hash 当前直接影响 NoProgressRecord。candidate_id/origin_problem 必须由同一问题和候选内容绑定，不能每周期 random；把周期/clock/correlation 放 private binding 与观测，不凭这些变化生成“新有效输入”。如需要新时间窗口参与执行输入，保留 exact运行向量，同时对跨轮策略再用既有 NoProgressRecord 的规范化 evidence/问题/策略 key 累加：仅经验证的新证据/输入/恢复条件才允许重开，不改旧 general Task 语义。默认同错误最多2次自动重试、连续3轮无有效进展 DEFERRED，保留最好版本。

**周期完成与业务有效进展分别判定。** 合法负结果或没有新候选的周期可以 COMPLETE；它只说明本轮必需工作完成，不能自动清零业务策略的 NoProgressRecord。结构合格 GoalBrief、空 checkpoint、新 report ID、消耗 token 或仅运行过，都不是新的业务进展。真正的变化须有当前可验证的新证据、独立接受的实验改进或已证实恢复条件；重复无变化的策略迭代继续累加原计数并保留最好版本。复用 `durability_progress.go:7` 的现有规则时需区分策略迭代 Task 与已接受的报告交付 Task：该 helper 要求匹配 terminal Run 且无新证据时调用 taskFailed，不能因此把正确完成的报告改成失败，也不能重置或覆盖历史计数；跨轮绑定/规范化 key 的具体接入须有该状态边界测试。

最少回归对照：所有必需来源缺失且仅有空 checkpoint 必须 BLOCKED；已有真实、有效来源进展（例如一条完整来源链）或独立接受实验，但另一必需来源缺失，才可 PARTIAL。源码 progress 锚点为 `research.go:365,388,398,401–402`，其中 review 行数 `:392–398` 也须改为 current receipt 复核。profile 已变时，具备权限、exact revision 且安全停机/对账完成的 CANCELLED 应释放 active_cycle_id，之后才可用新 profile 创建下一轮；存在 UNKNOWN effect、无权限或 revision 不匹配的取消必须拒绝或保持阻塞，旧证据不得丢失。另测“连续合法 COMPLETE 负结果但无新有效业务证据”继续累计无进展，新增 report/cycle ID 不清零。

资源请求解除并不自动证明 source/runtime恢复；下一次 driver current-use 检查仍重做。PARTIAL/BLOCKED 周期关闭后保留未完成 source窗口、候选和任务；下周期重用必要未决工作映射或显式继续原 Task，不无穷新建等价任务。已发外部动作在 restart先 reconcile，不从 model摘要重放。

## 8. 最少持久化与文件边界

不改 frozen schemas。建议两个私有关系表，准确列名由施工审查固定，migration 编号 root 串行分配：

| 表 | 唯一键/主要内容 | 用途 |
| --- | --- | --- |
| `intent_plan_bindings` | project + accepted intent Requirement id/revision unique；submission actor/hash、template version、规划 Goal/Task、sealed GoalBrief/ref、接受 ref、materialized Goal IDs/logical node mapping、monitor binding/当前计划 revision | 幂等 bootstrap、provenance、模型提案与 authority 的边界；非第二 job status/队列 |
| `research_cycle_work` | project + cycle + logical work key unique；monitor plan ref、stage/source/candidate、Task ID/Experiment ID、exact输入 refs/hash、window/resource/progress关联 | 持久阶段对象关系；执行状态仍来自 Task/Run/Experiment/Receipt，不能自己存另一套 DONE |

现有 ProjectState.active_cycle_id、ResearchCycle、source_pages/SourceCursor、research_candidate_reviews、orchestration dependencies/contracts、effect/budget/idempotency/outbox、ResourceRequest/NoProgressRecord 全部复用。无需新的 cron/history queue/monitor microservice。due 可从已批准计划与最后cycle推导，首版不额外存一张 tick 表；查询规模增长才优化索引。

**切片 I1：自然表达→有来源的规划交付→业务 Goal/DAG。** 所有界面提交只含自然话；新增 `internal/domain/intent_planning.go`、private GoalBrief schema/校验和对应 tests；修改 `apps/web/src/screens.jsx` IdeaForm/规划状态展示，`operations.go` 的显式 intent 接受 hook，`acceptance.go` 新真实规划 handlers、`acceptance_goal.go` 窄规划 Goal mode 支持，S2 loop 一个 intake step。必要 `context.go` 加原话/问题/GoalBrief引用而非替代当前context。root 串行整合 HTTP/commands/hooks、W04当前编辑；无新route。纯compile/parser/API fixture可先做，正常 LIVE planner执行依赖S1+S2接受；未满足时交付真实visible block。

**切片 I2：同一 coordinator 自动驱动有限研究周期。** I1 给出已批准monitor plan；新增 `internal/domain/research_driver.go` 与 native fixture tests；修改 `research.go` 的当前阶段/close/coverage union/stale cancel，`candidates.go` reviewer绑定与current复核，`sources.go` 与S2的预算/Run bridge；按需增加复用进展key helper，`apps/control` 不开第二loop。真实三来源/核查依赖W07 LIVE，实际实验和独立接受依赖W10/S1/S2，review自动authority依W11资格现状保持closed；W14验收最后用一条真实trace串联。

I1 与 I2 是两段纵向可验证交付；不先建万能 planner 平台。W04/source配置不在该slice已支持范围的字段变更明确阻塞或交给对应实现，不改 frozen API。**当前未发现必须新增公开API的矛盾**；若实施证明现有 Requirement入口无法保留已认证原话/授权或现有字段承载不够，应先给同样精确的合同证据与唯一最小变更提案，经版本流程批准再改，本设计不预授权一个隐藏 intake endpoint。

## 9. 必须保留的验证与真实 E2E 判据

| 组 | 最小机制测试 | LIVE/产品完成证据 |
| --- | --- | --- |
| 自然入口 | 浏览器只输一句自然话；HTTP保存原话且不索要command；刷新/双击/超时重试只有一份binding/规划Goal；角色/跨项目/stale提交拒绝 | 同一真实UI输入到当前qualified planner Run、原始输出、GoalBrief、独立接受及业务DAG完整trace |
| provenance | 模型把假业务事实标USER_STATED/OBSERVED、伪引用、预算/权限扩大、注入shell/SQL均拒绝；PROPOSED不自动变事实 | USER_STATED原文、SYSTEM_PROPOSED展示与PROPOSED存储、真实来源证明；必要业务问题有真实用户答复 |
| bootstrap | 正常Goal/Task合同、独立验证、ACTIVE/context/lease/budget完整；规划Goal接受不完成业务Goal；LIVE无资格明确阻塞 | S1/S2当前资格与独立root，非fixture/native伪装模型能力；不存在“先任意假Goal后换合同” |
| planning | 循环DAG、跨Goal依赖、不存在命令/输出、删失败条件、错误继承资格、old plan回放拒绝；未知能力保留blocked | 实际检查命令/独立review对应真实业务输出；模型建议与服务端最终authority分开 |
| due/restart | 6h边界、首次7d、多漏tick一个cycle、双触发唯一、进程重启ID不变、暂停不新派、时间回退、队列100/全局2受控 | 实际进程重启/恢复trace和周期日志；fixture时钟不等于W19隔夜/睡眠资格 |
| source windows | 429 retry持久、断页续采、query变更、无缝union/有gap、缺X/可见空X仍partial；未完成旧窗口不因新due丢弃 | W07真实三来源完整window/page/raw chain；授权/配置/限制满足，否则A13 BLOCKED |
| stages | native固定程序真实执行各stage/experiment与独立fixture verifier；重复回执/ACK丢失不重复Task/effect；无法验证的review不算完成 | A13一真实周期至少一实际baseline/candidate实验，各stage输入/输出/ref、费用/未知项、合法负结果 |
| close/recovery | 空checkpoint不算实质进展、撤销evidence/receipt后close失败、profile漂移可合法cancel、UNKNOWN不重发、旧NoProgress不清零 | COMPLETE仅真实全部必要条件；合法REJECT/WATCH可完成；缺源则PARTIAL/BLOCKED，最终UI与总账同版本 |

候选计划、fixture机制测试和真实产品接受分别记录。新测试选择器零匹配/零断言必须失败。当前此次只验证 JSON 和设计结构，不运行任何上述测试，不改变 R01/R05/W08/W14/A13 或既有 formal gate。

# 11 · 评测与组件接入实施规范

版本：2.3.0。负责：W10评测执行、W11 Jev资格、W15技能、W16系统演进、W17权限。所有产品验证NOT_RUN。

## 1. 四个项目的明确职责

| 项目 | 处置 | 当前实施要求 |
|---|---|---|
| promptfoo/promptfoo | PRIORITY_QUALIFY | W10验证固定版本的评测执行和结果导入；W11/W15/W16使用相同合同 |
| alibaba/skill-up | PRIORITY_QUALIFY | W15优先验证技能对照评测的增益；只经W10窄适配调用现成CLI，不另建调度体系 |
| vxcontrol/pentagi | REFERENCE | W13借鉴任务/Agent/工具/文件界面；W06/W12事件关联，W04/W09作用域检索 |
| lyhue1991/dsh-soup | REFERENCE | W13侧栏/预览/目标栏；改为条件写与合并，不继承冲突覆盖逻辑 |

Promptfoo、PentAGI、DSH-soup核查快照分别为822caba35e9fda7a5f300721477efe7c9194865a、ea665308baaff015b226f308438a68d929d0f29b、d95b51a88429c2ceab6d79cb0fd43f394dd193c9。skill-up固定源码为7f1ff9b8e2d7c654728de526867f2f7e7b78ea51；核查到最新发行记录v0.12.0（2026-09-18），此源码还含未发行变更，详references/SkillUp_Review_2026-10-01.md。它们是来源基准，不是已合格依赖。W02/W10记录实际版本、lockfile、license和必要补丁；保持已有核心路线，不开展新一轮无边界选型。

先判断是否满足当前缺口，再决定采用哪一个现成实现。Promptfoo保持通用评测职责，skill-up只在技能实验具有可证明收益时接入；拒绝或暂缓也须保存理由。一个冻结用例的一次正式运行只归属一个引擎；资格对照实验可分别运行并保留独立Run，不把双框架重复执行当作日常默认行为。

## 2. EvaluationAdapter 的一次有限调用

输入：已登记Experiment/Run、冻结的基线与候选引用、数据集及配置/rubric hash、预期用例ID、执行范围、超时与预算策略。输出：EvaluationReport作为TEST_RESULT Artifact、EvaluationSummary作为REPORT Artifact、原始stdout/stderr和运行/出站回执。

调用顺序：
1. 校验已授权身份、输入版本、固定引擎及资源；REGISTERED实验才可执行。
2. 由Worker创建隔离任务目录；正式holdout由独立Verifier环境持有，开发目录只放开发夹具。
3. 启动固定引擎，记录pid/session/cwd/argv的脱敏信息；超时、取消、断线继续沿用Run和Worker恢复合同。
4. 导出后按预期ID对账，不仅检查退出码。保存原始文件hash；不解析未完成的流作为最终成果。
5. 归一化EvaluationReport，执行完整性和硬检查；无报告/无样本/漏例/重复/版本错配不能成为有效验收证据。
6. 由独立Verifier审查，按既有AcceptanceService决定接受；EvaluationReport没有ACCEPTED权力。
7. 将指标写回Experiment前按04的结果提交顺序取得需要的有效AcceptanceReceipt；保留原始负结果和失败历史。

不新增一个独立调度器或可被前端修改的“评测完成总账”。API复用现有Experiment/Artifact/Run；四个评测Schema是产物内容格式，不新增公开评测业务端点。

skill-up实现此入口时，复用固定构建的CLI子进程，通过已核实的公开参数执行，收集每个iteration目录的原始`result.json`、JSONL事件（启用时）及stdout/stderr。调用参数必须来自该构建的`--help`和契约探针；不直接import `internal/*`或把其内部类型作为ResearchOS公开合同。现成custom engine协议适用时，以窄适配连接自有CLI；当前没有运行证据，不假定它已经适配ResearchOS。

## 3. 数据与完整性规则

详见domain.schema.json的EvaluationCaseResult、EvaluationCounts、EvaluationReport、EvaluationSummary。

- expected_case_ids非空且唯一；results对每个预期ID保留一个归一化结果，缺失用MISSING占位；引擎重复输出产生duplicate_count并令integrity_status=INVALID，重复原始文件保留受控证据。
- observed_count = pass_count + fail_count + error_count + abstain_count；expected_count = observed_count + missing_count；不同类别互斥。任何未知case_id、统计不一致、hash错配均INVALID。
- COMPLETE仅表示结构、身份、版本、数量和传输完整。候选全失败也可能有COMPLETE报告；成功通过还要满足冻结条件。
- provider错误是ERROR，模型有效弃权是ABSTAIN，未收到结果是MISSING，业务/断言失败是FAIL。不能删去这些样本缩小分母。
- score仅是辅助信号；hard_checks_passed=false时不得令该条verdict=PASS。未知用null，不自动给0或true。
- CLI非零、失败断言和协议无效分别记录；实际退出语义按固定版本核验。禁止假设任意示例中的参数均被实现。
- 费用、时延、版本、数据集split和输入引用完整保留；费用未知为null。schema有效不能证明这些跨字段和跨实体规则已执行。

skill-up还须保留`configuration/variant`、iteration、attempt、原始case_id、SKIP原因及断言明细。预先冻结每个variant×iteration的期望用例清单，分别生成一份现有EvaluationReport；维度、报告引用及重试选择规则保存为配套Artifact索引。不得把有意重复实验当成同一份报告的重复case，也不得把真实重复结果静默覆盖。重试结果全部保留，不按最高分挑选；比较分母在运行前冻结。

原始SKIP不得删除或改成PASS：因执行条件不足跳过的按ERROR记录；经冻结规则明确允许、且确属模型有效弃权的才映射ABSTAIN；原因在受控原始产物保留。没有收到预期结果仍为MISSING。零断言、零有效硬检查或缺少要求的工具/文件证据，即使上游status为PASS也不能形成ResearchOS通过证据；按冻结规则记录失败或无效报告。DSH插件的`summarizeResult`按case_id合并并偏向with_skill，它的摘要/比较只适合展示，不能作为C21的权威输入或覆盖原始variant/iteration。

## 4. 首个12条开发冒烟

examples/evaluation_smoke_cases.json为开发/协议夹具，含正确接受、正确拒绝、错误接受、高分硬失败、缺证据、过期、中文、混合语言、弃权、超时、重复、缺失。夹具列出输入、候选模拟输出、预期处理和需验证的逻辑，全部NOT_RUN。

另外注入：零用例、未知ID、配置/阈值篡改、候选hash变化、真实出站和意外分享。用稳定候选和故意退化候选对照，确保评测能发现回归。

适配最多两种针对性接入方式、各一轮修复；若固定引擎不适用，记录原因，优先使用已存在、满足相同合同的评测入口或NATIVE确定性执行器；只有证据明确的适配缺口才补最小代码，不因此重写评测框架。不能降低C21、删除负例或把未安装工具标成通过。正式Jev调用及A08不能由假服务替代。

## 5. Jev、技能和系统候选

Jev可以通过自定义provider被调用；本轮未发现官方专用Jev接入，需实现适配。也可在资格有效后提供辅助评分。正在被验证的Jev不能用自身评分充当独立标签。

资格键：task_type × language × provider × model_revision × rubric_revision。完整A08沿用：初轮60开发+30独立留出，两种语言留出各至少15；每个准备获得BOUNDED_AUTO的完整键各至少60开发+30留出，关键误放0、误放/该键留出数≤5%；报告误放/负例数、自动覆盖、弃权、错误、时延和费用。未测键、全弃权或无足够自动动作样本不能晋升。12条冒烟与该资格分开。

W15旧/新技能同题比较，保留来源和资料覆盖；W16比较系统候选时额外验证全链路回归、W18恢复资格、有限canary及真实回滚。评分规则改变必须形成新实验，不能与旧分数拼成“提升”。

用户要求的“判断后复用源码”由W11对源码复用选型用途单独校准，再按有效资格和DecisionMode参与决策；硬条件如不满足必要功能、无可核查源码/版本、许可不兼容或资格实验失败，不能被高分抵消。Jev可辅助比较完整fork、模块复用、适配现有依赖或拒绝，但不能凭自身推荐给自己授予资格。未具备相应用途资格时保留ADVISORY意见，依靠已有确定性门与独立验收推进可执行支路。

源码复用选型的用途键为`scope.task_type="reuse_selection"`，其余语言、provider、model_revision和rubric_revision仍须分别匹配。skill-up的judge分数、Jev选型意见、源码小样是否可运行是三个不同证据。skill-up评测通过不自动证明某仓库适合本产品；Jev推荐仓库不自动证明某技能有效；只有相关冻结验收通过才更新对应采用记录。

## 6. 留出与输出的权限边界

正式留出输入、标签、逐例输出、详细评分及相关日志均VERIFIER_ONLY。候选仅获得当次调用必要输入、脱敏汇总及受控证据引用。不同模型/子Agent处于同一可读目录不算隔离。

Artifact.access_class是服务端强制分类，OS ACL/独立账户或容器是实际执行边界。普通Executor/Planner无权读取受限内容；明确有权Owner和独立Verifier可核查。读取规则覆盖列表、ID直读、content、search、context、event、preview、cache、export与backup；凭hash或带签名旧URL也不能绕过已撤回授权。

衍生报告继承受限来源级别。公开EvaluationSummary必须由独立受保护服务生成并审查，不能直接复制自由文本reason/题目/逐例diff。正式详情留受控对象存储，不放候选可读的artifacts/evals。若隔离未验证，记录BLOCKED，正式资格不放行。

## 7. 外部服务与运行语义

首轮使用评测核心，配置明确provider；显式禁止不需要的分享/Cloud同步/远程生成，并记录实际出站。关闭遥测的环境变量不能单独证明零外联；本次研究发现disabled分支仍可能发统计请求，需针对固定构建实测，不能据此推断发送了提示词正文。

工具的工作目录副本不构成安全沙箱。保存清理前必需证据，控制子进程读写/网络范围，沿用Worker租约和取消合同。PentAGI的Docker socket与sudo/SUID取舍服务于其渗透测试场景，不是ResearchOS通用执行默认值。

验收对应：C21结果完整性，C22留出与派生内容隔离，C07/C09/C10/C20原有独立判断和防自证；A07/A08/A09/A16正式闭环。

## 8. Mu/Jev上下文与Goal判断的独立实验

按13和H05/H06固定任务与原文，分别运行full、无损rules、judge_shadow。C21的12条开发协议夹具完整保留，额外Harness重放不计作正式Jev样本。保护失败、退出码、用户约束、冲突和必要来源；规则折叠须逐字节可逆。报告实际任务通过率与漏证据、费用、耗时，不能只优化字符数。

上下文筛选、Goal继续、记忆准入、模型路由使用不同task_type资格键；Mu作者已有实验不授予本项目资格。active不是域层DecisionMode；按03映射。无资格自动动作关闭，真实评测失败仍可合法交付ADVISORY/完整原文。Jev、普通LLM和本地Laya后端也不共享模型资格；首次下载/使用本地权重先核查其来源和许可。

## 9. skill-up的技能资格实验和平台边界

W15首个候选是“本地优先、判断后复用源码”的技能。沿用已有W10/W11/W15与C21/C22/A09，不增加WBS任务或正式用例数量；以下是既有用例的夹具和断言扩展，当前全部NOT_RUN。

1. 冻结旧版、有技能/无技能及候选版的输入项目、预期能力、来源快照、工具权限、预算和数据集版本。开发题覆盖本地已有模块、上游整仓合适、只有局部模块合适、热门项目不匹配、license/运行证据不满足、确有最小自研缺口。
2. 使用隔离副本运行，检查它是否实际盘点、定向查缺口、保留判断证据、选对复用范围并完成可运行修改；“我会复用”的自然语言表态不计通过。无匹配时正确拒绝候选也是有效表现，不把clone数量当成果。
3. 先验证执行失败、SKIP、漏结果、重复、空断言和退化技能能被现有合同识别，再比较任务成功率、误采用/误拒绝、工具与文件证据、耗时和费用。验收阈值在实验前冻结，不能看完结果再改。
4. `skill-upper`可生成开发用例和候选技能；候选只能修改自己的开发副本。正式holdout、硬断言、判定标签、数据集split和发布门不交给它，正式结果由独立Verifier复验。观察插件导出的案例仍是未合格候选，补足具体预期后才进开发集。
5. 结果证明确有覆盖或成本收益才保留skill-up依赖；有界资格实验已执行并证明没有收益、原有能力已覆盖或平台适配成本不合适，则记录拒绝并沿用现有评测实现。缺关键资源导致无法试验只可记NOT_RUN/BLOCKED，不能伪造“实测后拒绝”。两条路线都不得降低正式验收。

机器合同使用`EvaluationReport.engine.name="SKILL_UP"`。J04在W15对照技能与评测接入价值，W10只负责统一窄适配；A13可在隔离分支完成真实候选改造与比较，是否ADOPT/合入取决于结果，不强迫采用。

平台验收按固定版本区分：上游Windows指南与当前实现对`none` runtime、cmd与bash的描述存在不一致，源码的内置Agent启动有bash前置检查。不能因CLI能启动或script judge能执行，就宣布原生Windows全Agent评测通过。需分别实测原生Windows+所需shell/已安装CLI、WSL2或受控远程执行路径，并记录文件路径、凭据传递和子进程取消；WSL结果不能代替我们的Windows Desktop安装与运行验收。评测插件或WSL依赖也不成为普通Desktop使用的强制前置。

现有Codex评测适配仍含固定0.80.0的旧传输路径；新版`codex-skill-up`观察插件是另一条当前宿主hooks能力，不证明旧评测适配支持当前Codex。DSH观察与before/after摘要也不替代完整报告。观察插件默认非必须，只在已有授权与明确诊断收益时启用；没有它也须完成核心产品和评测入口。发布tag与主分支的未发布插件变化分开记录，不把文档自述当作实际安装、运行或业务资格。

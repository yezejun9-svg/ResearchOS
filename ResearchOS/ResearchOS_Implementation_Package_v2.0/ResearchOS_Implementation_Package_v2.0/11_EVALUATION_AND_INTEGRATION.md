# 11 · 评测与组件接入实施规范

版本：2.0.0。负责：W10评测执行、W11 Jev资格、W15技能、W16系统演进、W17权限。所有产品验证NOT_RUN。

## 1. 三个项目的明确职责

| 项目 | 处置 | 当前实施要求 |
|---|---|---|
| promptfoo/promptfoo | PRIORITY_QUALIFY | W10验证固定版本的评测执行和结果导入；W11/W15/W16使用相同合同 |
| vxcontrol/pentagi | REFERENCE | W13借鉴任务/Agent/工具/文件界面；W06/W12事件关联，W04/W09作用域检索 |
| lyhue1991/dsh-soup | REFERENCE | W13侧栏/预览/目标栏；改为条件写与合并，不继承冲突覆盖逻辑 |

核查快照分别为822caba35e9fda7a5f300721477efe7c9194865a、ea665308baaff015b226f308438a68d929d0f29b、d95b51a88429c2ceab6d79cb0fd43f394dd193c9。它们是来源基准，不是已合格依赖。W02/W10记录实际版本、lockfile、license和必要补丁；保持已有核心路线，不开展新一轮无边界选型。

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

## 3. 数据与完整性规则

详见domain.schema.json的EvaluationCaseResult、EvaluationCounts、EvaluationReport、EvaluationSummary。

- expected_case_ids非空且唯一；results对每个预期ID保留一个归一化结果，缺失用MISSING占位；引擎重复输出产生duplicate_count并令integrity_status=INVALID，重复原始文件保留受控证据。
- observed_count = pass_count + fail_count + error_count + abstain_count；expected_count = observed_count + missing_count；不同类别互斥。任何未知case_id、统计不一致、hash错配均INVALID。
- COMPLETE仅表示结构、身份、版本、数量和传输完整。候选全失败也可能有COMPLETE报告；成功通过还要满足冻结条件。
- provider错误是ERROR，模型有效弃权是ABSTAIN，未收到结果是MISSING，业务/断言失败是FAIL。不能删去这些样本缩小分母。
- score仅是辅助信号；hard_checks_passed=false时不得令该条verdict=PASS。未知用null，不自动给0或true。
- CLI非零、失败断言和协议无效分别记录；实际退出语义按固定版本核验。禁止假设任意示例中的参数均被实现。
- 费用、时延、版本、数据集split和输入引用完整保留；费用未知为null。schema有效不能证明这些跨字段和跨实体规则已执行。

## 4. 首个12条开发冒烟

examples/evaluation_smoke_cases.json为开发/协议夹具，含正确接受、正确拒绝、错误接受、高分硬失败、缺证据、过期、中文、混合语言、弃权、超时、重复、缺失。夹具列出输入、候选模拟输出、预期处理和需验证的逻辑，全部NOT_RUN。

另外注入：零用例、未知ID、配置/阈值篡改、候选hash变化、真实出站和意外分享。用稳定候选和故意退化候选对照，确保评测能发现回归。

适配最多两种针对性接入方式、各一轮修复；若固定引擎不适用，记录原因，选择实现相同合同的NATIVE确定性执行器继续。不能降低C21、删除负例或把未安装工具标成通过。正式Jev调用及A08不能由假服务替代。

## 5. Jev、技能和系统候选

Jev可以通过自定义provider被调用；本轮未发现官方专用Jev接入，需实现适配。也可在资格有效后提供辅助评分。正在被验证的Jev不能用自身评分充当独立标签。

资格键：task_type × language × provider × model_revision × rubric_revision。完整A08沿用：初轮60开发+30独立留出，两种语言留出各至少15；每个准备获得BOUNDED_AUTO的完整键各至少60开发+30留出，关键误放0、误放/该键留出数≤5%；报告误放/负例数、自动覆盖、弃权、错误、时延和费用。未测键、全弃权或无足够自动动作样本不能晋升。12条冒烟与该资格分开。

W15旧/新技能同题比较，保留来源和资料覆盖；W16比较系统候选时额外验证全链路回归、W18恢复资格、有限canary及真实回滚。评分规则改变必须形成新实验，不能与旧分数拼成“提升”。

## 6. 留出与输出的权限边界

正式留出输入、标签、逐例输出、详细评分及相关日志均VERIFIER_ONLY。候选仅获得当次调用必要输入、脱敏汇总及受控证据引用。不同模型/子Agent处于同一可读目录不算隔离。

Artifact.access_class是服务端强制分类，OS ACL/独立账户或容器是实际执行边界。普通Executor/Planner无权读取受限内容；明确有权Owner和独立Verifier可核查。读取规则覆盖列表、ID直读、content、search、context、event、preview、cache、export与backup；凭hash或带签名旧URL也不能绕过已撤回授权。

衍生报告继承受限来源级别。公开EvaluationSummary必须由独立受保护服务生成并审查，不能直接复制自由文本reason/题目/逐例diff。正式详情留受控对象存储，不放候选可读的artifacts/evals。若隔离未验证，记录BLOCKED，正式资格不放行。

## 7. 外部服务与运行语义

首轮使用评测核心，配置明确provider；显式禁止不需要的分享/Cloud同步/远程生成，并记录实际出站。关闭遥测的环境变量不能单独证明零外联；本次研究发现disabled分支仍可能发统计请求，需针对固定构建实测，不能据此推断发送了提示词正文。

工具的工作目录副本不构成安全沙箱。保存清理前必需证据，控制子进程读写/网络范围，沿用Worker租约和取消合同。PentAGI的Docker socket与sudo/SUID取舍服务于其渗透测试场景，不是ResearchOS通用执行默认值。

验收对应：C21结果完整性，C22留出与派生内容隔离，C07/C09/C10/C20原有独立判断和防自证；A07/A08/A09/A16正式闭环。


# ResearchOS 实施规格包 v2.3：唯一执行入口

日期：2026-10-01（Asia/Shanghai）。用户已确认尚未开始产品开发。  
当前产品状态：NOT_STARTED；产品测试：NOT_RUN。包校验和参考板检查不等于产品验收。

## 1. 本次交付与效力

本包已经统一此前PRD、技术设计、组件讨论、前端参考、DSH-soup/PentAGI/Promptfoo及Goal优化，整体替代v2.2及更早实施包与单独Goal作为开工基线。Codex无需重新收集旧文件、要求用户拼接或再做无边界选型。

交付物统一称“实施规格包”：PRD（01）＋技术设计（02）＋任务拆分WBS（05）＋接口/数据定义（03/04及contracts）＋验收标准/测试用例（06）。这些部分通过需求ID、任务ID、操作/字段和验收ID互相追踪。08及GOAL_START只是执行入口，必须配合完整包使用；单独提示词不替代实施规格。

产品目标：交付自己的CLI Agent与Windows Desktop，共享同一Agent核心、项目和会话；研究、Jev、工具执行、持续Goal与多Agent协作是内置能力。每个新项目先查本地，再调研现成方案并优先复用，确有缺口才自研。原有GitHub/X/论文研究与证据实验要求保留。

这是独立项目，默认目录research-os。不得自动读取或修改Quill Club/xiaoshuo的身份、连接器、代码、私有文件或部署。历史资料中的名称不构成访问授权。

## 2. 文件职责与阅读顺序

| 文件 | 职责 |
|---|---|
| 00_START_HERE.md | 效力、入口与整体完成门 |
| 01_PRD.md | 20项需求、用户流程和成功条件 |
| 02_TECHNICAL_DESIGN.md | 唯一调度、模块、运行、事务与隔离 |
| 03_DATA_CONTRACTS.md | 实体、状态、版本和访问级别 |
| 04_API_CONTRACTS.md | OpenAPI、条件写、事件、认证与适配 |
| 05_WBS.md | W00–W21共22项任务、依赖、范围和阶段门 |
| 06_ACCEPTANCE_TESTS.md | C01–C26、A01–A16，共42个正式用例 |
| 07_OPERATIONS_AND_EVOLUTION.md | 隔夜、预算、备份、恢复、晋升和回退 |
| 08_AGENT_EXECUTION_GOAL.md | 完整Codex目标提示词 |
| 09_COMPONENT_DECISIONS.md | 34项组件处置与单列UI参考 |
| 10_UI_UX_DESIGN.md | 11页面、组件、双主题、响应式与交互 |
| 11_EVALUATION_AND_INTEGRATION.md | 评测适配、结果协议、Jev与留出权限 |
| 12_IMPLEMENTATION_AND_HANDOFF.md | 环境、命令落位、里程碑、交付和续跑 |
| 13_HARNESS_DESIGN.md | Pi/Mu运行与判断、续跑、证据完成门与H01–H10 |
| 14_CLI_DESKTOP_PRODUCT.md | 自有CLI与Desktop、共享核心、本地协议、安装与双端体验 |
| 15_NEW_PROJECT_WORKFLOW.md | 先本地→调研与判断→适当源码复用→适配验证 |
| 16_ADOPTION_JUDGMENT.md | Jev选型、硬门、独立复核和采用/拒绝；含skill-up接入 |
| contracts/adoption.contract.json、adoption.schema.json | J01–J04映射、候选/采用Artifact结构及业务不变量 |
| contracts/product.contract.json | CLI/Desktop能力、命令与P01–P07/B01–B02验收映射 |
| contracts/client.protocol.schema.json | 本产品本地命令/事件及复用决策内容Schema |
| contracts/harness.contract.json | Harness采用策略、固定版本、WBS/验收追踪和默认值 |
| GOAL_START.txt | 可粘贴的短/goal入口，引用完整规格 |
| contracts/domain.schema.json | JSON Schema 2020-12数据及请求/报告结构 |
| contracts/openapi.json | OpenAPI 3.1，本产品API，非第三方已有API |
| contracts/tasks.json | 完整任务DAG与阶段门，和05一致 |
| contracts/acceptance.json | 固定用例与最终负责人，和06一致 |
| contracts/ui.contract.json | UI路由、操作ID、字段、状态和检查矩阵 |
| ui/design-tokens.json | 双主题、字体、间距、尺寸与动效 |
| ui/reference.html | 可直接打开的离线参考板，示例数据/交互 |
| examples/ | 正反合同样例、12开发夹具与施工模板 |
| tools/validate_package.py | 规格完整性、DAG、合同、UI映射和token检查 |
| PACKAGE_MANIFEST.json | 清单、版本、来源与hash |
| PACKAGE_VALIDATION.json | 本规格包实际校验结果 |
| references/ | 历史研究来源，不是第二套执行指令 |

机器字段和枚举以contracts为准；范围以01为准；视觉与交互以10及UI合同为准；最终完成以06为准。参考板与历史资料不能修改业务状态或验收条件。

## 3. 如何开始

将整个目录交给独立ResearchOS执行会话。先读本文件及08，再按任务阅读所需合同。单独提供的ResearchOS_Agent_Goal_v2.3.md与包内08内容相同，任选一个入口即可。

在本包根目录运行：python tools/validate_package.py。需要Python 3.10+；脚本只校验规格，不安装产品或调用模型。然后W00建立独立仓库与施工台账，W01有界验证底座，W02锁定路线、目录和实际命令，继续W03–W21。

W00先检查授权本地资产。W01先判断Mu完整CLI/Desktop组合是否适合，备选Pi与现成桌面组件；每条最多一次针对性修复。适合才以选定源码clone/fork或模块复用为起点改造，研究取样clone不算采用。QM改为可选远程适配/可靠性参考；自研仅用于有证据的具体缺口。CLI/Desktop正式范围见14，所有新项目流程见15。

初始施工使用外部台账与文件快照，不要求尚未建成的ProjectState/AcceptanceService先管理自己。W06后历史施工回执可作为有来源Artifact导入，不能追认成过去的产品验收。

## 4. 用户已确定的工作方式

默认金额无硬上限cap=null，可自设限额；未知费用明示。允许数小时或隔夜；正常技术选择自行推进；重大成果汇报，普通阶段和结果在侧栏可看。重复失败有停止条件，资源不足形成具体去重请求，独立支路继续。

金额不限不自动授权代购、充值、发消息、Git push或生产部署；读取已有授权，不重复询问。缺Windows/账户/额度时保留相关live阻塞，继续可完成的合同和fixture。

## 5. 完成门与当前交接

完整交付需要22项任务闭合、42例正式门有效通过、真实三类来源与Jev调用、真实执行器、Windows隔夜恢复、手机监督、备份恢复、技能/系统候选试验和真实回滚。未达自动资格的Jev用途可保持ADVISORY，但真实评测与降级仍须验证。

每个任务关联输入版本、产物hash、真实命令/输出及独立回执。执行者只报告结果；正式ACCEPTED由服务端独立验收产生。拒绝采用、无改善和没有新候选可能是合法研究结果，不预填收益或强制升级。

已完成的是本包规格、UI定义与参考板。产品代码、资格测试、真实服务、Windows/手机实测和收益测量仍待执行。后续新组件由实际问题驱动，不以增长依赖清单延迟实施。

## 6. 本次用户确认与版本效力

v2.3完整替代v2.2：用户明确目标是自己的CLI Agent及Desktop，且每个新项目必须本地优先、调研复用、最后补缺口。旧版“QM强制主控→Go薄核”和“原生App后置”不再生效。00–16及当前机器合同是完整执行基线；历史研究仅供引用。

保留20项需求、22任务、42例及11个视图；增加CLI/Desktop和每新项目开工的9条能力断言，与既有H01–H10同时验收。CLI、Desktop两种真实发行件和双端接续必须完成，原有研究、Jev、Windows/手机、恢复与回滚要求也保留。

将包放在执行Agent可读目录，使用GOAL_START.txt；完整08/14/15由Agent读取。当前完成的是规格，不是产品。已有合法实现先做影响分析与迁移/回退ADR，保留用户修改，不直接删除或假改旧回执为新基线PASS。

## 7. 本版新增的判断闭环

用户最新确认：不要一味clone，也不要读完别人实现再从零造同一套；用Jev辅助判断，结合源码和实际验证决定整仓改造、模块复用、锁定依赖或不采用。该规则既适用于本项目施工，也成为产品内置流程。W01以独立bootstrap审查推进，W08实现fixture判断，W11校准真实reuse_selection，W14完成实际源码改造闭环；没有循环依赖。

skill-up列为W15优先资格候选，经W10现有评测接口有限验证；采用/拒绝都要证据，不强制增加依赖。J01–J04加入原42例，20需求/22任务/11视图及原H01–H10/P01–P07/B01–B02全部保留。产品尚未实现。

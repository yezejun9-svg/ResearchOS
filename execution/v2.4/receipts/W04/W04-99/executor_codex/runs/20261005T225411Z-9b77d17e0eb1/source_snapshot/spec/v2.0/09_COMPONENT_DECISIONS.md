# 组件采用决策与后续研究规则

版本：2.0；依据：设计汇总 v7、前端参考与本次组件评审。当前为规格设计，全部第三方组件均未由本实施包安装或实测。来源、固定 commit、许可及源码限制见 references/ResearchOS_Design_Synthesis_v1.1_source.md。

## 1. 三种处理方式

- PRIORITY_QUALIFY：优先以当前需求做小型资格实验，通过后才锁依赖。
- OPTIONAL：在有明确任务或能力缺口时验证，不阻塞首版主链。
- REFERENCE：复用工作方法或界面思想，当前不把整套代码作为依赖。

这三项是本文件的选型处置；正式组件生命周期仍分别记录 REFERENCE/CANDIDATE/QUALIFIED/INTEGRATED。候选能力、安装、真实调用和业务资格分开。README自述及他人测评不替代我们的回执。

## 2. 核心31项组件归属

| 项目 | 处置 | 具体落点 | 关联WBS |
|---|---|---|---|
| Awesome | OPTIONAL | 按主题发现候选，回到原始仓库核查 | W07/W08 |
| Public APIs | OPTIONAL | API候选目录，核对官方接口和额度 | W07 |
| Free for Dev | OPTIONAL | 服务备选与成本线索，逐条核实 | W07/W12 |
| Scrapling | OPTIONAL | 已知网页内容获取，保留URL与快照 | W07/W09 |
| Sirchmunk | PRIORITY_QUALIFY | 本地检索增强；基础FTS/rg保持可用 | W09 |
| Paperclip | PRIORITY_QUALIFY | 唯一业务调度底座资格；未通过按既定薄核回退 | W01 |
| n8n | OPTIONAL | 外部连接器/Webhook，不另拥有业务Goal | W07/W12 |
| Dify | OPTIONAL | 特定研究工作流，明确节省时选用 | W08 |
| Open WebUI | OPTIONAL | 多模型对话入口，任务状态回到本系统 | W13 |
| Open WebUI Computer | OPTIONAL | 工作台/执行参考，单独核查许可与边界 | W05/W13 |
| Agent Office | REFERENCE | 任务板、活动流、团队展示，必须投影真实事件 | W13 |
| wuyoscar/jev-skill | PRIORITY_QUALIFY | 检查点、初筛、证据评审模板，按用途校准 | W11 |
| f/prompts.chat | OPTIONAL | 提示词/技能候选只读导入、变量和评测 | W15 |
| yibie/awesome-jev | OPTIONAL | Jev生态线索、分类及弃权方法 | W07/W11 |
| Tongyi-MAI/MAI-UI | OPTIONAL | 仅在API/CLI缺口时验证GUI定位/执行 | W05 |
| Yinsongxu/LLM2Jev | OPTIONAL | 非官方本地判断后端，独立校准 | W11 |
| humanlayer/humanlayer | REFERENCE | 旧会话/异常升级方法，旧代码弃用状态见来源 | W05/W12 |
| stablyai/orca | OPTIONAL | 工作区/CLI执行和手机监督对照 | W05/W17 |
| mvanhorn/last30days-skill | PRIORITY_QUALIFY | 单次研究JSON发现候选；统一调度和预算 | W07/W08 |
| Panniantong/Agent-Reach | PRIORITY_QUALIFY | 所需来源的配置/诊断方法；实际读搜另验 | W07 |
| virgiliojr94/book-to-skill | PRIORITY_QUALIFY | 来源快照到候选技能，不直接覆盖稳定版 | W15 |
| ayghri/i-have-adhd | REFERENCE | 简洁汇报呈现，不作为事实/记忆系统 | W13 |
| nextlevelbuilder/ui-ux-pro-max-skill | OPTIONAL | 设计知识检索、设计系统候选 | W13 |
| pbakaus/impeccable | PRIORITY_QUALIFY | 界面质量小样；检测引擎/hooks分开登记 | W13 |
| earendil-works/pi | PRIORITY_QUALIFY | 执行协议和Jev分类接口，不拥有业务总账 | W05/W11 |
| rlaope/oh-my-hermes | REFERENCE | 先吸收记忆准入、交接与证据等级；整套插件另验 | W04/W06 |
| coreyhaines31/marketingskills | OPTIONAL | 产品定位/客户研究/实验方法；API写动作另授权 | W14/W15 |
| 666ghj/MiroFish | OPTIONAL | 后置假设模拟，产物标SIMULATED | W10之后 |
| lyhue1991/dsh-soup | REFERENCE | 侧栏、成果预览与Goal展示；冲突覆盖不得照搬 | W13 |
| vxcontrol/pentagi | REFERENCE | 工作台、事件追踪、作用域记忆与恢复参考，不安装第二主控 | W04/W06/W09/W12/W13 |
| promptfoo/promptfoo | PRIORITY_QUALIFY | 固定评测适配、Jev用途验证、技能/系统回归；独立验收保留 | W10/W11/W15/W16 |

计数：原29项组件加PentAGI/Promptfoo共31项；UI专项参考另列，不计为必装依赖。Sirchmunk两轮调研合并为一项；Pi迁移前后按同仓身份去重。具体上游版本以来源表为核验起点，实施时再记录实际 checkout 的 commit、lockfile、license和必要补丁。

## 3. 首版依赖收敛规则

首先交付一条可工作的链：项目上下文 → 已授权来源适配 → 证据与实验 → 独立验收 → 采用记录和成果版本。候选组件资格失败应有已规定的替代或局部阻塞，不强迫重做整套产品。

W01锁唯一调度路线；W05先接一种真实可用执行器，其他执行器按相同合同扩展。W07分别验证GitHub、X、论文来源，不能因为渠道配置存在就记为真实可用。Jev作为决策组件按用途升级，不赋予独立写入ACCEPTED、授权或发布的能力。

所有工具自己的上下文文件是带revision的任务视图。MASTER.md、PRODUCT.md、DESIGN.md、营销背景文件和外部Goal不得成为与ProjectState竞争的事实来源。

## 4. 本轮已知的接入必查点

| 候选 | 必须处理的语义 | 对应验收 |
|---|---|---|
| Paperclip/Orca/其他执行器 | 原生完成事件不等于独立验收；不能绕过正式门 | A02/C07 |
| Pi | 接受prompt、agent_end、agent_settled含义不同；取消清队列后abort，持久服务可继续存活 | A04/C11 |
| last30days | arXiv实际窗口365天；采集失败不可解释成无结果；不继承独立watchlist预算 | A05/C06 |
| Agent-Reach | doctor/MCP状态不等于live读搜；渠道授权分别确认 | A05/A11 |
| Sirchmunk | 缓存不改变原文权威；文件改变/删除和项目隔离须验 | A06/C02 |
| book-to-skill | 部分抽取失败仍可能退出0；核对输入manifest；Fold-in只写候选版 | A09/C03 |
| i-have-adhd | 上游评测未过门；简洁报告不能补造原因或隐藏失败 | C18/A10 |
| Impeccable | 0/1/2退出码需按工具语义解释；设计修改不能改变业务状态 | A10 |
| Marketing Skills | HTTP错误不能以CLI退出0当成功；研究/草稿与发送/投放能力分开 | A03/A11 |
| OMH | 原生resume的copy_only/not_tested不能写成已验证恢复 | A04/A14 |
| DSH-soup | 冲突自动改基线重试会覆盖外部修改；必须改成条件写与合并 | C04/A03 |
| MiroFish | 模拟角色日志不等于现实用户证据；有LLM/Zep Cloud依赖 | C19/A07 |
| PentAGI | Finished不是ACCEPTED；worker/socket权限不照搬；Graphiti非首版前置 | C07/C23–C26 |
| Promptfoo | 完整结果与固定配置、错误/弃权/缺失计数、出站实测、留出隔离；退出0不授予资格 | C21/C22/A08 |

## 5. 交给产品后续自行迭代

新候选通过同一ResearchCycle处理，保留canonical repository ID/URL、来源入口、commit/hash、许可、适用能力、依赖、维护状态、实验结果与拒绝理由。转载与迁移不重复累计“独立证据”。

只有具体实验说明对当前问题有益，才生成ChangeProposal并计算影响范围。外部main更新形成新候选，不能覆盖运行中任务版本。没有收益或出现回归就保留稳定组件；负结果加入后续检索和排序。

SOURCE_REVIEWED、INSTALLED、LIVE_PROBED、QUALIFIED、INTEGRATED不是同一状态。任何“已采用”必须能指向正式决定、资格回执、实际依赖版本和回退路径。可替代同功能实现，验收不变量不随组件改变。



## 6. UI专项参考的落点

| 来源 | 本版采用的参考范围 | 代码处置 |
|---|---|---|
| Craft Agents | 任务—会话—文档组织 | REFERENCE，移植需适配宿主并核对许可 |
| Midday | 低饱和排版、细边框、费用/文件层次 | REFERENCE，许可声明差异未消除前不复制整套代码 |
| Linear | 成果、diff、检查与讨论的组织 | 产品视觉/交互参考 |
| Plane | 状态导航、任务列表、筛选 | REFERENCE，先核对AGPL范围 |
| Twenty / Twenty UI | 表格、字段和保存视图 | 局部包许可与主产品分开核对 |
| LobeHub | Agent/项目/资产组织 | REFERENCE，Community License需逐项核查 |
| Scira | 研究入口与引用定位 | REFERENCE，不预设检索质量已验证 |
| assistant-ui | 输入/工具结果/产物等局部组件 | OPTIONAL，W13小样后采用 |
| Vibe Kanban | 任务切换、diff与预览并排 | REFERENCE，保留原研究中的维护状态限制 |
| Onlook | 预览与编辑对照 | REFERENCE，仓库和hosted产品分开 |
| X作品/时间线 | 六阶段活动流与文件标签 | 历史候选，直接读取受阻项不冒称看过视频 |

视觉方向已经由10确定，不等待用户再次从参考项目中选一个。X/GitHub原始链接与当时可访问范围见references/Frontend_Research_2026-09-29.md；新抓取的信息仍走项目研究流程。

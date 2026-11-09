# ResearchOS Harness 开源复用调研

调研日期：2026年10月1日，Asia/Shanghai。用途：为尚未实施的 ResearchOS 选择可复制修改的 Harness，并补齐下一版规格的依据。

建议优先验证 QM 作为整套运行骨架；Pi 作为内部 Agent 执行内核，继续沿用 v2.0 的 W05 接入位置。采用 QM 的前提是它能承载 ResearchOS 的唯一任务权威、冻结验收和恢复合同。如果资格失败，保留 v2.0 薄核加 Pi 的路线。以上是选型建议，尚未取得产品运行验收。

本次实读 GitHub 文档、公开源码和近期发布记录；成功拉取 QM 与 last30days 的固定源码。X 原帖访问受限，相关内容仅达到搜索索引摘要级别，其项目能力另用官方仓库和文档核对。研究过程没有访问或修改 Quill Club 仓库，没有安装或部署 ResearchOS。

## 现有规格的更正

重新读取 v2.0 后，可以确认 `02_TECHNICAL_DESIGN.md` 已有唯一调度、ContextBundle、RuntimeAdapter、工具权限、租约、检查点、独立验收和演化控制。`09_COMPONENT_DECISIONS.md` 也已将 `earendil-works/pi` 列为 W05/W11 的优先资格候选。

此前把缺口描述成“没有真正的 Harness”过重。准确的缺口是：这些合同分散在技术设计、数据、运维和任务文档中，尚无集中说明 Harness 调用边界、能力协商和扩展接点的专项设计。下一版应将现有合同归并，避免重复建一套状态、调度或记忆服务。

包内 `10_UI_UX_DESIGN.md` 已占用编号 10。如果补专项文档，建议命名 `13_HARNESS_DESIGN.md`，并同步数据/API/WBS/验收映射。本报告没有修改 v2.0 的执行效力。

## 最适合复用的项目

下表的“适合”是结合 ResearchOS 需求的工程判断；功能与许可来自当前一手资料。

| 项目 | 复用重点 | 许可与技术栈 | 本次建议 |
|---|---|---|---|
| [QM](https://github.com/yc-software/qm) | 多执行器、持久运行、权限、scope 记忆、Agent 协作与 Web 骨架 | MIT；TypeScript、Node、Postgres，Web 为 Vite/Lit | 整套骨架首选资格候选，适合 source fork 加领域扩展 |
| [Pi](https://github.com/earendil-works/pi) | 会话运行、工具事件、context hooks、MCP、Jev 分类与模型路由 | MIT；TypeScript | 执行内核首选；优先 SDK/扩展，必要时窄补丁 |
| [Deep Agents](https://github.com/langchain-ai/deepagents) | context 压缩、工具输出卸载、filesystem、隔离子 Agent、可配置的持久 memory 与 LangGraph checkpoint | MIT；Python，另有 TS 库，基于 LangGraph | 需要 Python/LangGraph 路线时的替代，不与 Pi 重复承担同一个运行职责 |
| [OpenRig](https://github.com/mvschwarz/openrig) | 稳定角色席位、多个原生 CLI 会话、snapshot/restore 结果报告 | Apache-2.0；本地 daemon、SQLite、tmux | 借协作和恢复设计；原生 Windows 不支持，WSL2 未测 |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | 长期 memory、context 插件、技能沉淀、工具注册 | MIT；Python | 借记忆与技能候选生成机制；暂不整套纳入首版 |

Deep Agents 的官方仓库确认可通过 middleware/backends 替换部件，无须首先 fork 全库。Hermes 的学习闭环仍须接入 ResearchOS 的固定评测与晋升条件。它们均不能证明已经控制现有七种 CLI/桌面客户端。

[Open SWE](https://github.com/langchain-ai/open-swe) 更偏编码任务、持久沙箱、PR 与 CI，适合未来工程实验支路；其独立生产 Agent Server 的许可密钥要求需要另核，不列为本轮主底座。

## QM 的源码核查与修改位置

固定提交：`6a01d56c8145b125301596506b7b007b9890bcf2`。提交时间为北京时间 2026年10月1日 08:18:57。源码经公开克隆后只读检查；本次未安装依赖、启动服务或运行它的测试。

QM 的 README 明确允许 source fork，也提供仅依赖包的部署扩展路线。要修改核心验收和 Goal 语义，本项目更适合保留上游历史的 source fork；仅组织配置、工具和技能的调整可放独立部署层。使用所复制文件的实际许可，并保留相关声明。

| 已核实的源码 | 可复用行为 | ResearchOS 需要增加或修改 |
|---|---|---|
| [src/harness/harness.ts](https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/src/harness/harness.ts) | 运行合同与能力声明；Pi、Codex、Claude、OpenCode 的不同接入方式 | 映射现有 RuntimeAdapter；取消、恢复和成本能力逐项声明 |
| [src/runs/postgres-run-store.ts](https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/src/runs/postgres-run-store.ts) | 领取、租约、heartbeat、重试延迟、失效执行归属处理 | 绑定任务输入版本、产物 manifest、验收回执；运行结束只进入上报阶段 |
| [src/swarms/swarm-service.ts](https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/src/swarms/swarm-service.ts) | 请求指纹幂等、资源 outbox、消息与通知去重 | 委派进入统一任务 DAG；登记目录所有权、预算、取消关系和最终整合者 |
| [src/memory/postgres-memory-service.ts](https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/src/memory/postgres-memory-service.ts) | 记忆修订历史、条件替换与历史恢复 | 加事实来源、有效性、DecisionMemory；生成版本化 ContextBundle |
| [src/memory/provider-router.ts](https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/src/memory/provider-router.ts) | scope 路由、显式写入与自动捕获策略 | 区分辅助回忆与必需合同；必需上下文缺失时阻塞受影响任务 |
| [src/harness/goal.ts](https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/src/harness/goal.ts) | 持久 Goal、继续执行提示、独立上下文 judge | 将 Goal 完成接到冻结的服务端验收；增加资源阻塞、无进展和恢复状态 |
| [src/tools/primitives.ts](https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/src/tools/primitives.ts) | 工具调用台账与结果重放接点 | 增稳定 operation ID、供应商幂等键、EffectReceipt 和未知结果对账 |

### 必须处理的保证边界

**完成判断。** `agent-tools.ts` 的 Goal judge 使用目标、Agent 说明和由宿主读取的有限文件，文件证据限制为最多 5 个、每个 20,000 字符。这有独立上下文，但尚不是 ResearchOS 的冻结验收合同。需要独立执行检查、绑定输入版本和证据 hash，并在最终事务内再验证；上游完成不能直接映射 `ACCEPTED`。

**持续工作。** Goal 提示要求 Agent 不能自行将 Goal 转入暂停或阻塞状态，还支持最低时间、Token 或费用条件；达到 Token cap 时的提示允许汇报剩余工作和阻塞。QM 运行层确有取消、重试及预算边界，不能因此说它完全无限运行。ResearchOS 仍须增加业务上的 `BLOCKED_RESOURCE`、`NO_PROGRESS` 与有界重试，不让账户缺失或设备离线演变成反复续写；保留其他就绪支路的推进。

**文件恢复与并发。** [官方 swarm 文档](https://github.com/yc-software/qm/blob/main/docs/swarms.md) 明确：Worker 得到空白电脑，父文件不自动复制；共享 forum 的并发写需另行协调；swarm 不新增文件快照或恢复。因此需要任务 worktree、封存产物、冲突整合、备份与真实恢复验证。持久队列只证明运行记录可继续。

**外部动作。** 工具 `once()` 的流程包含执行副作用后再记录结果，台账以 run/attempt/call index 定位。崩溃可能发生在两者之间，跨 attempt 也有新槽。可复用台账机制，但不能保证外部操作天然恰好一次；未知结果先查询或对账。

**客户端适配。** 发现原生接入为 Pi、OpenCode、Codex 和 Claude。未发现 Grok CLI、Qoder、Zcode、DSH、MiMo 的现成对应适配。QM 的 `desktop/` 是自己的 Electron Web 客户端，不证明能操控其他桌面 Agent。SDK 接入也不能冒称现有桌面宿主已通过验证。

**记忆降级。** [Memory providers](https://github.com/yc-software/qm/blob/main/docs/memory-providers.md) 支持读写分权，外部召回默认 fail-open。辅助历史可降级；权限、冻结规格、验收合同与关键输入缺失必须形成显式不完整状态。

QM 的 [SECURITY.md](https://github.com/yc-software/qm/blob/main/SECURITY.md) 将项目标为 experimental，假设单组织内部认证用户。活跃提交、上游测试和这些功能的存在都不等于 ResearchOS 资格通过。

## Pi 的近期能力与复制入口

[官方发布记录](https://github.com/earendil-works/pi/releases) 显示：9月29日 v0.99.0 加入 Jev classifiers、MCP、codemode、virtual models，以及嵌套工具调用的父调用标识；9月30日 v0.99.2 改进 MCP 按需发现并修复 Windows standalone codemode 启动问题。这些是窗口内真实发布变化，但 Windows 全生命周期仍未在本项目实测。

可直接修改的入口是 [SDK](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sdk.md) 和 [jev-router.ts](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/jev-router.ts)。固定 release 后使用对应代码，不依赖持续变化的 main。

**QM 并未自动获得这些新能力。** 本次固定 QM 提交的 `package.json` 将 `@earendil-works/pi-ai` 固定为 `0.82.0`，coding-agent 使用 QM 自带安全修改的 `0.82.0-security.5` 压缩包。因此 Pi 0.99 的新功能应在独立实验中验证；升级需检查上游接口、QM 安全补丁与回归，不能直接替换依赖便称接入成功。

SDK 与 CLI 的默认扩展不同：SDK 要显式加载所需的 MCP/codemode/tool-search 扩展并绑定。`agent_end` 后可能还有排队或自动恢复；`agent_settled` 表示本轮不会自行继续，随后仍须提交 ResearchOS 独立验收。

Jev 路由样例可以借其注册接点和状态持久化。样例的旧模型 ID、首次成功编辑后持续降档的规则不应照搬。模型名单配置化，并以任务类型、失败信号和同源回放评测验证路由策略；现有固定 Agent 指派与历史实际模型记录保持准确。

## X 近期项目思路

检索目标窗口为 2026年9月2日至10月1日。以下两条 X 线索来自原作者的搜索索引，原帖直接读取返回访问错误。日期可由公开 status ID 时间戳交叉核对；这不代表读到了完整正文或视频。功能结论来自配套一手仓库与文档。

| 近期线索 | 原帖 | 经官方资料核实的想法 | ResearchOS 落点 |
|---|---|---|---|
| GPT Researcher，Assaf Elovic，9月28日 | [X](https://x.com/assaf_elovic/status/2104562754774303203) | 用 Jev 判断片段对问题是否有用，采用阈值、预算和 BM25 后备 | ContextBundle 的候选筛选；Jev 用途单独校准 |
| OpenRig，作者 Feral Machine，9月29日 | [X](https://x.com/_feralmachine/status/2104944048507412763) | 从少量 Agent 开始；稳定角色席位与会话分离，恢复逐节点报告结果 | 先验证执行者和检查者，再扩编；记录 resumed/fresh/failed |

GPT Researcher 的 [Context Filter 文档](https://docs.gptr.dev/docs/gpt-researcher/gptr/context-filter) 给出了同一批抓取来源重放的评测方法。作者在 28 个任务上测得 Jev 保留片段相关率 73%，embedding 基线 46%；不设阈值而填满 top-10 时 Jev 为 50%。这只是该作者、模型与样本的结果。

更适合复制的是实验方法：固定原始页面，只改变筛选器，比较关键证据遗漏、反证保留、来源多样性、中文问题表现、耗时与费用。必需规格、权限和当前验收合同先固定进入上下文，Jev 只筛选允许筛选的辅助材料。

OpenRig 的当前仓库明确原生 Windows 不支持、WSL2 未测试，旧 Web UI 仅维护。本轮借其角色和恢复设计，不将其当现成 Windows 产品。

## ResearchOS 的接入方案

推荐进行有界资格实验，先跑 QM 加其已有一种执行器，再验证 Pi 的新增能力。QM 与 Paperclip 若都运行领取和后台队列，将产生重复调度权威；选型结束只能保留一条产品路线。

| 层 | 建议采用的机制 | 产品权威归属 |
|---|---|---|
| 目标、任务、依赖、授权 | QM 能承载则扩展 QM；否则采用现有薄核路线 | 同一个 ResearchOS 控制面 |
| Agent 运行与工具事件 | Pi SDK 或 QM 已有适配器 | 各 Run 的执行机制，不能自行接受业务成果 |
| 来源发现 | last30days 作为来源工具适配 | 保留原始结果、时间窗口、来源状态和定位 |
| 上下文与记忆 | QM 修订/路由机制，按需参考 Deep Agents | 版本化 ContextBundle 与事实来源 |
| 判断与评测 | Jev、promptfoo 和独立检查程序 | 冻结合同及服务端接受事务 |
| 工作台 | 继续沿用 v2.0 UI 合同，映射真实事件 | 数据库与事件投影；Token 流不代表任务进度 |
| 演化 | Hermes 可生成技能候选 | 固定回归、稳定监督、试用与回滚条件 |

last30days 的搜索结果是候选线索，不直接成为有效证据或采用结论。需保存来源状态，区分成功空结果、未配置、超时、限流、不可达；热度只用于发现，不替代源码检查和实验。

## 资格实验与下一版规格修改

以下是建议新建的资格检查，不是宣称上游已有或已通过的测试。每项保留命令、版本、原始日志和独立结果；真实设备或账户缺失时标 `BLOCKED`。

| 检查 | 具体通过条件 |
|---|---|
| 执行器一致性 | 至少一种真实已授权执行器跑通同一任务合同；接第二种时保持接口和结果语义一致 |
| 重启与租约 | 同一 Run 同时最多一个有效执行租约；崩溃后可按合同重领恢复，旧租约不得提交，外部副作用先对账 |
| 完成验收 | 输出缺证据、验收失败或输入已变时，即使模型 judge 判完成也不进入 ACCEPTED |
| 资源阻塞 | 缺账户/额度/设备产生一次明确请求与可恢复状态；就绪独立分支继续 |
| 未知副作用 | 在动作已发生、结果未记录的位置模拟崩溃，先对账，不盲目再执行 |
| 必需上下文 | 缺冻结规格、权限或验收版本时阻塞；辅助记忆不可用时记录降级 |
| 文件隔离 | 两执行者修改同一基线时保留冲突，整合后验证，不更新版本号重试旧覆盖 |
| Windows 生命周期 | 原生或选定 WSL/Worker 拓扑实测取消进程树、中文路径、睡眠/重开对账 |
| 备份恢复 | 数据库与封存产物同步恢复后，hash、运行关联与接受回执可核查 |
| Jev 新用途 | 上下文筛选和模型路由分别评测；本项目中文、反证与留出结果决定是否启用 |

下一版建议只做三类规格修订：新增 `13_HARNESS_DESIGN.md` 集中合同；在 W01 有界底座资格中纳入 QM 并冻结唯一路线；更新相关 API/数据/验收和 W05/W11 接点。保留已有 W00–W21、42 个正式用例与 11 个页面的覆盖，任何删改都必须解释映射和影响。

本报告不能自动覆盖 v2.0 的 W01 路线。正式开工前，应发布一致的新规格包和 Goal；不让 Codex同时执行旧 Paperclip 选择规则与本报告的 QM 建议。

## 调研工具与证据状态

使用用户指定的 [last30days-skill](https://github.com/mvanhorn/last30days-skill)。实际源码提交 `5103ba478b380552207a3754b74c7655d64208cd`，技能版本 `3.26.0`。在临时调研目录中执行预检、诊断和 Python 引擎，不进行全局安装或浏览器 Cookie 抽取。

实际执行使用 `--as-of=2026-10-01 --days=30 --search=github,reddit,hackernews --no-browser-cookies --plan <query-plan.json>`，并指定四个候选仓库。运行于北京时间 13:40:19 至 13:42:40，耗时约 140.5 秒，退出码 0。引擎实际窗口为 `2026-09-01 → 2026-10-01`，以相差 30 天计算；不是声称完整覆盖了所有帖子。

| 来源 | 引擎记录数 | 实际覆盖与限制 |
|---|---:|---|
| GitHub | 32 | 匿名 REST 返回 Issues/PRs；仓库 project-mode 与评论补充因缺 token 未运行，四仓定向覆盖不足 |
| Hacker News | 22 | 已运行；仅作发现线索，技术结论回到一手源码核验 |
| Reddit | 14 | 已运行，但一个子请求超时；原始状态为 ok 且同时带 timeout 字段，宿主按部分覆盖解释 |
| X | 不计 | 缺可用凭据，未被技能引擎搜索；本报告另以网页搜索索引和一手项目资料补充 |

68 条记录是引擎候选，不等于 68 项已核实发现。结果前部存在泛词噪声且提示来源集中；本报告不按默认排序推荐技术路线。正文中的 QM/Pi 结论来自实读官方资料和固定源码。引擎发现的 issue 或未合并 PR 只算待核查线索。

进一步通过 GitHub 官方 REST 核对了三条代表性线索：

| 技能找到的条目 | 截至本次调研的真实状态 | 如何使用 |
|---|---|---|
| [QM PR1701 升级 Pi](https://github.com/yc-software/qm/pull/1701) | open，未合并 | 说明升级仍属候选；与本次源码 pin 0.82 一致 |
| [QM Issue1575 Claude 取消](https://github.com/yc-software/qm/issues/1575) | open | 作者报告 transcript callback 影响取消；本轮未复现，加入真实取消资格测试 |
| [Pi PR10040 Codemode/MCP](https://github.com/earendil-works/pi/pull/10040) | closed，未合并 | closed 不能当 merged；实装能力以当前发布和 SDK 为据 |

REST 的状态关键字段与核查汇总均收入证据包。未合并条目的提议、作者报告和已运行产品行为分别标识。

命令、原始运行日志、来源状态、结果元数据和查询计划保存在配套证据包；其中 `receipt.json`、`engine.stderr` 为原始运行记录，`result.metadata.json` 提取真实结果的 URL、日期及来源字段，不附完整帖子正文。手工核查与技能引擎分别记录，不能互相冒充。报告完成了两路独立文稿复核，并修正 Goal 状态与租约恢复措辞。候选产品的依赖安装、真实模型、Windows 实测、生产部署与完整验收均为 `NOT_RUN`。

# Mu源码评审：供ResearchOS v2.1选型引用

审阅日期：2026-10-01，Asia/Shanghai。仓库：https://github.com/qybaihe/mu 。固定HEAD：`8dfebe36508ac0c2508735bb866756dab9283e74`，提交时间2026-09-30 12:50:58+08:00。本次只读克隆、文档与源码审阅；未安装运行、未调用真实judge、未执行Windows测试。SOURCE_REVIEWED不等于QUALIFIED。

本文件是研究证据，不是另一套施工指令。执行要求由00–13及contracts确定。

## 用途和判断

Mu是基于Pi的编码Agent，加了一层判断内核，并有基于AionUi的桌面端。小模型/判断器负责有边界的问题：哪些输出进入上下文、任务有没有偏离、是否继续、经验是否值得记、信息是否值得发给协作Agent等。主模型仍执行任务。README列出逐点active/shadow/off以及Jev、本地Laya、普通LLM和cascade。

它更适合贡献执行层和判断机制。QM更接近持久平台/多运行器控制面，Mu更接近单个编码Agent在一个会话里的执行质量。ResearchOS可让一个控制面管理任务并借鉴Mu的机制，不应简单把Mu、QM、Pi整仓拼装。

建议优先验证四块：证据式Goal检查、测试日志的可逆折叠、逐用途SHADOW/回退、结构化判断ledger。Mu桌面端和hive/swarm不作为本产品首版额外前置。

## 已核对的来源

以下路径均是上述固定commit；可将路径接在 `https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/` 后复核：

| 文件 | 已观察到的内容 | 对实施的影响 |
|---|---|---|
| README.md | 判断内核、模式、桌面/CLI，明确早期开发与测量限制 | 不把上游使用体验当成熟性保证 |
| kyrn/docs/features/goal-mode.md | `/goal <条件>`、大模型checker、Jev兜底、暂停和默认额度，测试为faux/MockJudge | 适合施工入口；真实判定准确率仍待验证 |
| packages/kyrn-judge/src/goal/check.ts | GoalEvidence、最近检查、步骤、结束语与met/continue/needs_user解析 | 可移植证据/next action结构；需换成冻结全量验收 |
| packages/kyrn-judge/src/extension/features/goal.ts | goal检查截600字符、最近16步骤、检查输出尾600字符；20次/180分钟默认；重开暂停，新消息刷新会话计数 | 短Goal引用完整规格；持久业务计数不能跟着会话清零 |
| packages/kyrn-judge/src/decisions/goal-met.ts | Jev兜底结合结束语、未勾条目及改后未运行标记 | 可续跑信号，不作为最终接受权限 |
| packages/kyrn-judge/src/ledger.ts | 记录spec/mode/provider/model/outcome/source/stateDigest/usage/latency等；支持JSONL | 接到DecisionReceipt/Artifact及统一费用；现有JSONL不是独立事务验收账 |
| packages/kyrn-judge/src/admission/test-log.ts | 完整原文、规则、judge三组；重复范围、保护未知/失败/摘要，保留文本按原文重建 | 可逆折叠先做，再测Jev；适配集成情况需另核 |
| packages/kyrn-judge/package.json | private包0.1.0，Pi peer `^0.87.1`、Node>=22.19、MIT | 不假设可直接npm install为独立稳定SDK |
| packages/coding-agent/package.json | fork内版本0.87.1 | 不与QM内置0.82安全补丁或独立Pi0.99.2混装 |
| desktop/package.json、desktop/LICENSE | 桌面package为0.1.6、Apache-2.0 | 子树许可和release版本分别登记 |
| LICENSE | 根目录MIT声明 | 复制代码保留许可；不覆盖子树/模型权重许可 |

## `/goal`的关键差距

源码已有硬性“未勾验收/改后未运行”继续逻辑，也给模型看最近检查是否失败。但检查方法中`provable`只覆盖这两个条件；模型给met且它们为空时可以进入met。静态审阅未见这一处将所有历史必需失败、当前产物hash和完整合同列表变成程序硬拒绝。不能据此断言真实运行必然误判，也不能假设它已达到ResearchOS独立验收标准。

Goal运行中使用agent_end钩子，不等于本产品所有工具/子进程已settled。实施必须接续等待实际运行器稳定状态和子任务/费用对账。Mu不应自行标记ResearchOS Task ACCEPTED。

默认20次续跑、180分钟适合有界会话，但少于本产品8小时墙钟验收。调整配置只证明设置变化；需验证持久恢复、取消优先、原任务ID及无进展计数不变。

## 测量与发行证据的限度

README的日志折叠结果来自作者自己的日志；Jev筛选结果包含作者构造/标注的任务和留出目标。该文档明确尚无与Pi/Claude Code/Codex在相同任务上的端到端对比。ResearchOS需用自己的冻结输入比较原文/规则/Jev，记录任务验收、漏证据、延迟与费用，不能直接承诺同等节省。

本次公开Releases页面显示v0.1.5于2026-09-27发布，标pre-release；其中Windows默认Program Files路径启动修复及CI安装对话是上游声明，不证明我们的Windows进程树取消/睡眠恢复/隔夜条件已通过。main的桌面package版本0.1.6和发行tag不是同一对象。以选定commit与lockfile作为复用基线。

公开来源：

- https://github.com/qybaihe/mu
- https://github.com/qybaihe/mu/releases/tag/v0.1.5
- https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/kyrn/docs/features/goal-mode.md
- https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/packages/kyrn-judge/src/extension/features/goal.ts
- https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/packages/kyrn-judge/src/goal/check.ts
- https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/packages/kyrn-judge/src/admission/test-log.ts
- https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/desktop/LICENSE

结论：优先资格验证局部机制，整套运行器可选；不替代唯一控制面、真实多源研究、独立验收、预算与恢复。实施位置和反例已纳入13_HARNESS_DESIGN.md及H01–H10。

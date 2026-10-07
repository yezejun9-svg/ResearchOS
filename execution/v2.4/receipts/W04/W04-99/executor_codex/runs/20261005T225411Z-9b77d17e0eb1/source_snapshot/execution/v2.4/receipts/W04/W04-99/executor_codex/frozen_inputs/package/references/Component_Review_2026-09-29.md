# ResearchOS：DSH-soup、PentAGI、Promptfoo 补充评审 v1.0

核查日期：2026-09-29  
对象：ResearchOS 实施规格包 v1.0、设计综合稿 v1.1（当前版本 7）、前端参考清单。  
性质：源码与设计静态核查、实施建议；不是安装回执、运行测试报告或产品验收记录。

## 1. 结论与真实状态

| 项目 | 建议角色 | 与现有设计的关系 | 当前状态 |
|---|---|---|---|
| DSH-soup | 成果侧栏、文件预览、目标展示参考 | 已在组件决策和 W13 中纳入 | 设计已有；W13 仍 NOT_STARTED；未取得产品实现验收证据 |
| PentAGI | 运行工作台、事件追踪、作用域记忆、失败恢复参考 | 本次新增补充建议；主要落到 W13/W06/W12 | REFERENCE_ONLY；运行与效果验证 NOT_RUN |
| Promptfoo | 评测执行、候选对比和回归结果组件 | 本次建议优先资格验证；落到 W10/W11/W15/W16 | 集成候选；安装、适配和评测 NOT_RUN |

DSH-soup 没有在上一份前端参考清单里单列，是清单遗漏；实施包没有漏掉。不能把“已写入规格”说成“已经开发完成”。

本文件补充组件评审，不修改原实施包的完成状态、验收阈值、底座选择或授权规则。新组件通过适配验证后，才进入具体依赖锁定与实现决策。

## 2. DSH-soup：已经采用什么，还应补什么

现有证据：

- `09_COMPONENT_DECISIONS.md` 明确登记为 REFERENCE，说明“侧栏、成果预览与 Goal 展示；冲突覆盖不得照搬”，映射 W13。
- `ResearchOS_Design_Synthesis_v1.1.md` 当前版本 7 的 DSH 相关条目已有上述设计。
- W13 尚为 NOT_STARTED，相关验收尚为 NOT_RUN。本轮没有检查到 ResearchOS 产品仓库的实现提交、运行截图或验收回执。

| 上游能力 | ResearchOS 的具体落点 | 采用方式 |
|---|---|---|
| Jupyter 风格文件侧栏 | 研究材料、实验输出、报告、待审成果入口 | 按项目、周期和成果版本组织，展示来源及验收状态 |
| 中央 Preview 与文件子标签 | 不离开任务页查看 Markdown、HTML、图片、PDF、结构化结果 | 预览绑定产物版本/内容哈希；HTML 按项目预览隔离规则处理 |
| 多行 GoalBar | 持续显示目标、当前阶段、阻塞、下一步 | 读取唯一 ProjectState，不另建业务调度器 |
| Token/tps 徽标 | 可选运行状态详情：等待、输出中、耗时、用量 | 是运行遥测，不作为任务进度、质量或完成率 |

DSH-soup 是 DeepSeek Harness / DSH Desktop 插件，依赖宿主注入的 runtime、layout 与 primitives。适合复用交互思路或适配局部代码，不能视为可直接安装到任意 React 应用的通用组件库。

### 必须调整的文件冲突行为

本次在固定提交静态读取 `lib/client/files-store.js` 和 `lib/host/file-view.js`：

1. 保存遇到冲突后，客户端下一次保存会把基线 mtime/size 更新为磁盘新值，清除冲突标志。
2. 随后仍提交原编辑草稿；失败路径还可能安排下一次自动保存。
3. 服务端用 mtime/size 比较后写入，并非内容版本的原子条件写合同。

据此存在覆盖外部修改的风险；本轮未运行复现。ResearchOS 应保留本地草稿与外部新版本，拒绝过期写入，通过条件写和显式合并解决冲突，不能自动把新磁盘状态当成旧草稿的保存许可。映射原有 C04/A03，不降低原验收条件。

## 3. PentAGI：借鉴运行治理，不替换 ResearchOS 主控

PentAGI 的原始业务是自主/辅助渗透测试。其代码可供学习，但研究任务不需要因此引入攻击工具集。

| 值得借鉴的部分 | 已读源码 | ResearchOS 映射 |
|---|---|---|
| 可调面板、任务/Agent/搜索/文件/截图/终端入口 | `frontend/src/pages/flows/flow.tsx`；`frontend/src/features/flows/flow-tabs.tsx` | W13：结论、执行过程与证据同屏；W17：移动端监督 |
| 分类事件 worker、Flow 发布、trace/session 关联 | `backend/pkg/controller/flow.go` | W06/W12/W13：项目→周期→任务→运行→调用→证据可追踪 |
| 按 flow/task/subtask 检索、结果去重 | `backend/pkg/tools/memory.go` | W04/W09：上下文可复用且有范围、来源和版本 |
| 中断、加载运行中任务、无进展监督 | `flow.go`、`task.go` 及 README | 参考恢复实现；仍需满足自身幂等、lease、版本一致性规则 |

前端代码已读，但未启动产品做视觉或交互验证。首版可做同类界面切片，不必整套引入 PentAGI 的服务和监控依赖。

Graphiti 是上游可选、默认关闭的 beta 集成。仅在现有检索出现可测瓶颈后，才比较它是否改善召回、来源准确性和过期冲突；不将 Neo4j/Graphiti 新增为首版必需依赖。模型抽取的关系仍是待核实信息。

两处源码边界直接关系我们的设计：

- **执行完成不等于独立验收。** `backend/pkg/controller/task.go` 从 provider 的任务结果取 Success，再设置 Finished/Failed。该状态至多映射执行回执；ResearchOS ACCEPTED 仍由独立验收产生。
- **隔离配置不能照搬。** 默认 compose 给控制服务挂载 Docker socket；DOCKER_INSIDE 默认 false，但特定配置会把宿主 socket 交给 worker。Docker 客户端还为渗透测试 sudo/SUID 场景刻意不启用 no-new-privileges。应借鉴控制面/worker 分离方法，重新按外部研究代码执行合同配置并验证隔离。

保持既定 W01 底座资格验证与唯一调度器。PentAGI 不新增项目状态权威、验收权威或自主升级权威。

## 4. Promptfoo：优先验证为评测组件

它能组织多提示词、多模型/服务的对照，运行确定性或自定义断言，导出逐条结果。对“成果看着完整但不知道可靠不可靠”这一痛点最直接。

| 原任务/验收 | 建议使用方式 | ResearchOS 继续负责 |
|---|---|---|
| W10 / A07 | 冻结用例，比较采用前后，保留负结果 | 研究方法、证据、预算和实验完整性 |
| W11 / A08 | 自定义 provider 调用 Jev，对照独立标签 | 中文/混合语言资格、留出集和自动决策授权 |
| W15 / A09 | 旧技能/新技能跑同一套回归题 | 来源许可、覆盖率、候选晋升和历史基线 |
| W16 / A16 | 系统候选的模型、提示词、工具、Agent 回归 | 独立发布控制、试用期、恢复与回滚 |

本轮未发现官方 Jev 专用接入。可实现 custom provider 的 id/callApi 接口，将 Jev 作为被测对象；也可在合格后作为辅助评审服务。不能让正在被验证的 Jev 用自己的分数证明自己合格。

### 接入合同建议

ResearchOS 受限调用固定版本的 Promptfoo，导入原始结果到自身 Experiment/Artifact/Acceptance。至少关联：

- project_id、cycle_id、task_id、run_id、外部 evalId。
- 工具版本、候选版本、数据集哈希、配置哈希、rubric_revision。
- 预期用例清单与逐条结果，包括硬检查、模型评审、错误、弃权、缺失。
- 耗时、费用/用量（未知要标未知）、退出状态、原始输出及证据产物哈希。

外部 evalId 是运行标识，不是批准凭据。报告总分和退出码都不能单独决定验收。

### 本次发现的集成条件

1. **关键规则在外部独立检查。** Promptfoo 支持 threshold/weight 聚合；配置可能让某些断言失败仍被总体判过。冻结配置并校验哈希，候选 Agent 不得改自己的标准。对应 C07/C09/C10/C20。
2. **错误不能从统计里消失。** 零样本、漏例、超时、重复和弃权要分别处理；不得靠排除错误样本获得更漂亮的通过率。
3. **CLI 按固定版本核验。** 本次 CI 文档示例出现 --fail-on-error，但读取的 eval 命令实现未见此选项；源码另有通过率阈值与失败退出码设置。接入时以固定构建的 --help、导出结构和真实行为验证，不直接复制示例。
4. **外部服务行为需实际确认。** 远程生成、provider、遥测、分享和 Cloud 同步是不同路径。首轮只验证评测核心，显式关闭分享和不需要的远程功能，并记录实际出站。
5. **关闭遥测不等于已证明零外联。** 本次固定源码中，telemetry disabled 分支仍可能经 recordTelemetryDisabled→sendEvent 发请求。这里只是静态发现，未做网络实测，也不据此声称发送了提示词内容。
6. **工作目录副本不是安全沙箱。** coding-agent 的 copy_working_dir 可提供独立试验副本和文件差异；仍需外部隔离，且应在清理前固化必要证据。

Promptfoo 不替代 W16/W18 的真实恢复、Windows canary 和回滚试验，也不因自身报告 PASS 就授予系统升级权限。

## 5. 下一步验证包（全部 NOT_RUN）

建议优先验证 Promptfoo 适配，同时在 W13 原型中落实 DSH-soup/PentAGI 的展示思路。各实验先记录预算、候选版本、预期产物与停止条件；本文件不启动持续任务或付费运行。

| 编号 | 有界验证 | 最小产物 | 通过条件 |
|---|---|---|---|
| Q1 | Promptfoo 12 条固定夹具适配冒烟试验 | 适配器、冻结输入、逐条 JSON、原始报告、出站记录 | 用例齐全且可关联；故意退化能被检出；硬失败、配置篡改、缺失不被判过 |
| Q2 | DSH 风格侧栏/预览/GoalBar 原型 | 1 个研究周期，来源→实验→报告→采用决定可点击 | 产物版本不混淆；并发修改保留双方内容；明确展示待审/接受/拒绝 |
| Q3 | PentAGI 风格过程追踪原型 | 同一周期的阶段、任务、调用、证据详情 | 重连不重放为新业务事件；不串项目；手机能找到阻塞与成果 |
| Q4 | Jev 正式资格验证 | 按资格键独立的开发/留出报告 | 严格执行既有 A08；Q1 冒烟不能代替资格验收 |

Q1 建议夹具分别覆盖：正确接受、正确拒绝、错误接受、硬失败但模型高分、证据缺失、证据过期、中文、混合语言、弃权、超时、重复结果、缺失结果。另注入配置哈希变化，验证外部门拒绝。用稳定版本与故意退化版本对照，保留失败材料。

Q4 沿用 A08：每个拟授予自动决策权限的 task_type × language × provider × model_revision × rubric_revision 键，分别至少 60 条开发样本及 30 条不重叠留出样本；关键误放为 0、总误放/留出总数 ≤5%，并报告覆盖率、弃权、错误、耗时和费用。多语言共用总分不能代替逐键合格。候选若失败，应保持 advisory，这同样可以是资格测试正确执行的结果。

## 6. 给 Codex 的执行约束

将本文件作为实施规格包的补充材料读取。先检查真实仓库与任务状态，避免重复实现。DSH-soup 已是参考，不要重复宣布“新增集成”。Promptfoo 先做 Q1，PentAGI 先借鉴 Q3；通过证据再决定代码复用与依赖引入。

继续使用现有 ProjectState、调度器、版本合同和独立验收。不得把本评审中的“建议”“源码具备”改写为“已经集成”“效果已验证”，不得以替换验收规则制造性能提升。

## 7. 固定快照与一手来源

以下 SHA 是本次核查基准，不代表已批准的生产依赖。三库本次核查许可均为 MIT；复用代码保留对应版权与许可，云服务另按其条件核查。

### DSH-soup

提交：d95b51a88429c2ceab6d79cb0fd43f394dd193c9；提交时间 2026-09-26；package 0.7.0，Node ≥22。

- [README 与宿主定位](https://github.com/lyhue1991/dsh-soup/blob/d95b51a88429c2ceab6d79cb0fd43f394dd193c9/README.md)
- [客户端保存与冲突逻辑](https://github.com/lyhue1991/dsh-soup/blob/d95b51a88429c2ceab6d79cb0fd43f394dd193c9/lib/client/files-store.js)
- [服务端编辑写入](https://github.com/lyhue1991/dsh-soup/blob/d95b51a88429c2ceab6d79cb0fd43f394dd193c9/lib/host/file-view.js)
- [package.json](https://github.com/lyhue1991/dsh-soup/blob/d95b51a88429c2ceab6d79cb0fd43f394dd193c9/package.json)

### PentAGI

提交：ea665308baaff015b226f308438a68d929d0f29b；提交时间 2026-08-06。

- [README](https://github.com/vxcontrol/pentagi/blob/ea665308baaff015b226f308438a68d929d0f29b/README.md)
- [Flow 页面](https://github.com/vxcontrol/pentagi/blob/ea665308baaff015b226f308438a68d929d0f29b/frontend/src/pages/flows/flow.tsx)
- [任务标签页](https://github.com/vxcontrol/pentagi/blob/ea665308baaff015b226f308438a68d929d0f29b/frontend/src/features/flows/flow-tabs.tsx)
- [Flow 控制器](https://github.com/vxcontrol/pentagi/blob/ea665308baaff015b226f308438a68d929d0f29b/backend/pkg/controller/flow.go)
- [任务完成判断](https://github.com/vxcontrol/pentagi/blob/ea665308baaff015b226f308438a68d929d0f29b/backend/pkg/controller/task.go)
- [记忆检索](https://github.com/vxcontrol/pentagi/blob/ea665308baaff015b226f308438a68d929d0f29b/backend/pkg/tools/memory.go)
- [部署默认值](https://github.com/vxcontrol/pentagi/blob/ea665308baaff015b226f308438a68d929d0f29b/docker-compose.yml)
- [Docker 客户端](https://github.com/vxcontrol/pentagi/blob/ea665308baaff015b226f308438a68d929d0f29b/backend/pkg/docker/client.go)

### Promptfoo

提交：822caba35e9fda7a5f300721477efe7c9194865a；提交时间 2026-09-29。

- [Custom provider 文档](https://www.promptfoo.dev/docs/providers/custom-api/)
- [断言文档](https://www.promptfoo.dev/docs/configuration/expected-outputs/)
- [结果导出](https://www.promptfoo.dev/docs/configuration/outputs/)
- [数据处理与远程路径](https://www.promptfoo.dev/docs/red-team/troubleshooting/data-handling/)
- [固定版本 CLI](https://github.com/promptfoo/promptfoo/blob/822caba35e9fda7a5f300721477efe7c9194865a/src/commands/eval.ts)
- [运行统计与退出状态](https://github.com/promptfoo/promptfoo/blob/822caba35e9fda7a5f300721477efe7c9194865a/src/node/doEval.ts)
- [分享条件](https://github.com/promptfoo/promptfoo/blob/822caba35e9fda7a5f300721477efe7c9194865a/src/util/sharing.ts)
- [遥测实现](https://github.com/promptfoo/promptfoo/blob/822caba35e9fda7a5f300721477efe7c9194865a/src/telemetry.ts)
- [coding-agent 工作目录文档](https://github.com/promptfoo/promptfoo/blob/822caba35e9fda7a5f300721477efe7c9194865a/site/docs/guides/evaluate-coding-agents.md)

核查范围：官方 GitHub 插件读取源码、官方网页、既有设计文档。未安装三个项目，未运行渗透测试、红队、付费评测或生产升级；所有运行效果待上述实验验证。


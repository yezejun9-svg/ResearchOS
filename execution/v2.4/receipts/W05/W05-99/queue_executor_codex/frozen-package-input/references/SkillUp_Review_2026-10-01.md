# Alibaba skill-up 源码审查与ResearchOS采用边界

审查日期：2026-10-01。状态：SOURCE_REVIEWED；安装、真实模型调用、Windows运行、ResearchOS集成及产品资格均NOT_RUN。此文件记录本次固定源码观察和拟定接入要求，不能作为实施完成回执。

## 1. 固定来源

- 仓库：https://github.com/alibaba/skill-up
- 本地审查目录：`research_skill_up_20261001`。
- 实读HEAD：`7f1ff9b8e2d7c654728de526867f2f7e7b78ea51`。
- 本次审查的最新发行记录：`v0.12.0`，CHANGELOG日期2026-09-18。
- 固定HEAD包含`Unreleased`变更，不能用HEAD上的能力代指v0.12.0发行包能力。
- 根LICENSE：Apache-2.0。实施采用时保留许可证、归属及适用通知，登记实际依赖和分发范围。

固定源码入口：

| 证据 | 对应源码 |
|---|---|
| 项目职责、报告与CLI | [README](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/README.md) |
| 已发布/未发布边界 | [CHANGELOG](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/CHANGELOG.md) |
| 许可 | [LICENSE](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/LICENSE) |
| 自定义Agent协议与独立case会话 | [custom-engine](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/docs/design/custom-engine.md) |
| 开发用例与技能改进工作流 | [skill-upper](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/skills/skill-upper/SKILL.md) |
| Windows支持自述与限制 | [Windows guide](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/docs/guide/windows.md) |
| 实际内置Agent启动前置条件 | [internal/agent/cli.go](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/internal/agent/cli.go) |
| 新观察插件与旧Codex评测适配的区别 | [observation design](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/docs/design/skill-observation-feedback-loop.md) |
| DSH摘要按case_id合并 | [plugins/dsh-skill-up/lib/core.js](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/plugins/dsh-skill-up/lib/core.js) |
| 评测状态与断言解释 | [evaluator](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/internal/evaluator/evaluator.go)、[judge](https://github.com/alibaba/skill-up/blob/7f1ff9b8e2d7c654728de526867f2f7e7b78ea51/internal/judge/judge.go) |

## 2. 可直接复用的价值

已有CLI负责运行技能测试、调用Agent引擎、收集回答/工具与工作区产物、执行判定并输出结构化结果；支持有/无技能对照及多次迭代。`skill-upper`负责协助编写开发用例、诊断失败和改进候选技能。自定义引擎协议提供本地/HTTP对接边界，可资格验证后接入自有ResearchOS CLI。

这是W15技能评测的优先资格候选，不是整个ResearchOS的Agent主控或Jev替代品。先证明它比现有流程增加必要覆盖、降低接入成本或发现已知回归，再采用；没有收益不必增加依赖。

## 3. 接入方式

W10实现窄EvaluationAdapter：调用固定现成CLI子进程，保留原始`result.json`、可选JSONL事件、日志、版本与退出信息；不import Go内部包，不复制内部调度器。以同一现有Experiment/Run/Artifact/Acceptance链管理。Promptfoo保留通用评测职责，不默认双框架重复执行所有用例。

正式结果中每个variant×iteration独立归一化成现有EvaluationReport，配套Artifact保存原始维度、报告引用与重试规则。保留with_skill/without_skill、iteration、attempt、error、missing、skip和断言证据。SKIP不是PASS，零有效硬断言不能通过；模型评分也不能抵消硬检查失败。

`plugins/dsh-skill-up/lib/core.js`中的`summarizeResult`使用case_id键，并优先保留with_skill。这样产生的展示摘要不是全量对照数据，不能用作C21权威输入或替代原始结果。归一化直接读取完整结果文件，并按冻结清单对账。

`internal/evaluator/evaluator.go`在无judge时可返回默认PASS；`internal/judge/judge.go`的`NewResult`在断言数为零时使用vacuous pass。ResearchOS因此必须在导入层检查冻结的有效硬断言和证据覆盖，不能只读取上游PASS标记或pass_rate。

## 4. 权限与资格

候选技能可以修改自己的开发用例和开发副本。正式holdout、标签、硬断言、阈值、发布门及受限详情由独立Verifier持有。`skill-upper`的迭代能力不授予修改正式验收的权限。观察插件生成的样本仍需补足具体预期并审查，不能直接成为通过证据。

Jev选型资格在W11按`reuse_selection`用途键独立验证。Jev辅助判断哪个仓库或模块适合当前问题；skill-up评测技能是否有效；可运行小样验证工程可用性。这三类结果分别登记，不互相授予资格。

现有22项任务和42个正式用例不扩增；通过W10/W11/W15及C21/C22/A09/J04的既有范围承接。真实资源不足时记NOT_RUN/BLOCKED，有界实验证明不适合时才记拒绝；不能用未运行冒充负面实验。

## 5. 平台与发行限制

Windows指南对none runtime的cmd描述与当前源码的bash选择/前置检查存在差异；指南又建议WSL2运行完整Agent评测。`skills/skill-upper/SKILL.md`的安装段仍声称仅macOS/Linux且不支持Windows，也与Windows指南不一致。原生CLI、script judge、原生Agent执行、WSL及远程sandbox必须分别记录运行证据，不能任选一种文档说法当最终兼容性结论。WSL可作为评测环境候选，不替代ResearchOS Windows Desktop本身的安装、生命周期和实际工具能力验收。

旧Codex评测适配保留固定0.80.0兼容路径；面向当前Codex的observer插件使用宿主hooks，是另一能力边界，不能据此推断旧引擎适配当前Codex。观察插件默认可选，不强制装到所有执行Agent，也不阻塞CLI/Desktop产品交付。

本文件没有运行任何真实模型评测，没有授予QUALIFIED/INTEGRATED，没有把Unreleased的新OpenCode/DSH等变化视为v0.12.0已发布能力。后续必须以实际checkout、构建产物和运行回执更新采用记录。

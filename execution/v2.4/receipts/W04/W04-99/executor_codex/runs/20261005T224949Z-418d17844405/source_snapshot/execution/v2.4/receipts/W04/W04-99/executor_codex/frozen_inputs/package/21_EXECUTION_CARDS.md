# 21 · Qwen逐卡实施与续跑

版本：2.4.0。本文件规定施工循环；产品完成仍按05/06。任务卡从contracts/execution.plan.json生成，初始全部NOT_STARTED，不据此否认旧仓库已有代码。

## 1. 一轮一个可检查增量

1. 读最新execution/v2.4/checkpoint.json，实查身份、HEAD、dirty、输入与在途进程；旧PID不能当活身份。
2. 调用task_packet.py next --state <repo>/execution/v2.4/step_state.json；优先IN_PROGRESS，再按priority和已接受依赖选择。JSON返回整卡，不必装入所有文档。
3. 读卡read_refs、父任务和真实调用链，核实scope。别名由W02解析，不按规划路径重建功能；保留其他dirty改动。
4. 执行actions，保存deliverables/checks实际输出。command key待W02注册argv/cwd/timeout/selector；缺handler、零断言、超时均非零失败。
5. 将回执和冻结判据交独立Verifier。执行者只报告EXECUTION_REPORTED；Verifier重读产物、输入、hash与失败证据，接受后更新state。候选不能改门槛。
6. 更新checkpoint和价值观察，再选下一卡。只有缺本人信息、授权、资源才提具体请求。无卡可做时保存阻塞与恢复动作，不假称后台运行。

跨上下文时保留同step_id、失败指纹和最近可运行增量，不把未完成卡改ACCEPTED。内部再拆步写checkpoint.substeps，不改冻结父合同，不建第二完成总账。

## 2. 71卡与22父任务

IMPLEMENTATION_SLICE按明列依赖允许提前验证局部能力，不代表父任务PASS。PARENT_FINAL_GATE即Wxx-99，依赖自己全部实施卡及原WBS前置的-99，须独立接受。早期CLI/Desktop不等完整研究页面，但最终正式范围保持完整。

W01-02可以接受如实的资格失败/资源阻塞报告；仅缺live资源时W01-03可批准PROVISIONAL_DEVELOPMENT路线用于明确开发切片。W01-99与父最终门仍等待真实资格，不能把临时路线变PASS。

旧实现满足当前卡时复用并只重验受影响断言，不为展示工作强行改代码。“产品Agent真实编码”的专门演示才要求未完问题与非空有效diff，按17选择，不植入故障。

| 父任务 | 实施卡（从左到右；仍须按依赖选择） | 正式终验 |
|---|---|---|
| W00 | [W00-01](tasks/steps/W00-01.md) 核对现有身份、Git和旧证据，保护现场；[W00-02](tasks/steps/W00-02.md) 冻结v2.4与迁移ADR，建立分支和续跑记录；[W00-03](tasks/steps/W00-03.md) 尽早核对施工模型和产品资源，冻结第一真实任务 | [W00-99](tasks/steps/W00-99.md) |
| W01 | [W01-01](tasks/steps/W01-01.md) 固定Mu源码与许可，划出最小复用范围；[W01-02](tasks/steps/W01-02.md) 先验证同一宿主的双端会话、工具和取消；[W01-03](tasks/steps/W01-03.md) 接受唯一复用路线并固定维护退出成本 | [W01-99](tasks/steps/W01-99.md) |
| W02 | [W02-01](tasks/steps/W02-01.md) 把复用源码放进可维护构建结构；[W02-02](tasks/steps/W02-02.md) 绑定真实命令、客户端协议和步骤检查选择器；[W02-03](tasks/steps/W02-03.md) 形成自己的CLI和Desktop最薄可启动入口 | [W02-99](tasks/steps/W02-99.md) |
| W03 | [W03-01](tasks/steps/W03-01.md) 对照现有领域schema，实施最小兼容迁移；[W03-02](tasks/steps/W03-02.md) 实现typed本地协议及幂等事件边界 | [W03-99](tasks/steps/W03-99.md) |
| W04 | [W04-01](tasks/steps/W04-01.md) 本地目录注册、项目接续和首用最小导入；[W04-02](tasks/steps/W04-02.md) 冻结上下文并将变更影响传给真实任务 | [W04-99](tasks/steps/W04-99.md) |
| W05 | [W05-01](tasks/steps/W05-01.md) 对接实际模型和一次受控Agent循环；[W05-02](tasks/steps/W05-02.md) 完成CLI读改文件、diff、测试和真实中断；[W05-03](tasks/steps/W05-03.md) 补齐CLI命令、JSONL与安装入口 | [W05-99](tasks/steps/W05-99.md) |
| W06 | [W06-01](tasks/steps/W06-01.md) 复用并补足独立接受服务；[W06-02](tasks/steps/W06-02.md) 落实会话单写者和双客户端协议交接 | [W06-99](tasks/steps/W06-99.md) |
| W07 | [W07-01](tasks/steps/W07-01.md) 接通GitHub与论文来源并固定原文；[W07-02](tasks/steps/W07-02.md) 接通X并完整记录来源健康 | [W07-99](tasks/steps/W07-99.md) |
| W08 | [W08-01](tasks/steps/W08-01.md) 把源码采用与初始化状态做进产品；[W08-02](tasks/steps/W08-02.md) 研究周期闭合与问题驱动调度 | [W08-99](tasks/steps/W08-99.md) |
| W09 | [W09-01](tasks/steps/W09-01.md) 统一证据谱系与真实原文定位；[W09-02](tasks/steps/W09-02.md) 撤销和权限变化清除检索缓存 | [W09-99](tasks/steps/W09-99.md) |
| W10 | [W10-01](tasks/steps/W10-01.md) 冻结实验输入并公平执行基线和候选；[W10-02](tasks/steps/W10-02.md) 对接固定skill-up并验证外部评测适配 | [W10-99](tasks/steps/W10-99.md) |
| W11 | [W11-01](tasks/steps/W11-01.md) 接通Jev建议并限制决策权；[W11-02](tasks/steps/W11-02.md) 隔离真实标签并完成逐用途资格 | [W11-99](tasks/steps/W11-99.md) |
| W12 | [W12-01](tasks/steps/W12-01.md) 费用预占、对账与有限重试；[W12-02](tasks/steps/W12-02.md) 用途等价资源切换与用户可操作请求 | [W12-99](tasks/steps/W12-99.md) |
| W13 | [W13-01](tasks/steps/W13-01.md) 装好就能配置的原生桌面工作台；[W13-02](tasks/steps/W13-02.md) 打通对话、工具、文件Diff与双端接续；[W13-03](tasks/steps/W13-03.md) 完成11页前端交互与视觉可访问性 | [W13-99](tasks/steps/W13-99.md) |
| W14 | [W14-01](tasks/steps/W14-01.md) 先用自己的CLI完成一件真实编码工作；[W14-02](tasks/steps/W14-02.md) 三来源研究、真实Jev和实验端到端闭环 | [W14-99](tasks/steps/W14-99.md) |
| W15 | [W15-01](tasks/steps/W15-01.md) 研究证据编译候选技能并记录完整来源；[W15-02](tasks/steps/W15-02.md) 以真实skill-up比较并有限启用技能 | [W15-99](tasks/steps/W15-99.md) |
| W16 | [W16-01](tasks/steps/W16-01.md) 自我改进候选保持监督器和门槛隔离；[W16-02](tasks/steps/W16-02.md) 备份后小范围试用并验证自动回滚 | [W16-99](tasks/steps/W16-99.md) |
| W17 | [W17-01](tasks/steps/W17-01.md) 首次本地主体引导与权限边界；[W17-02](tasks/steps/W17-02.md) 数据出口与独立holdout权限隔离；[W17-03](tasks/steps/W17-03.md) 手机安全接入、撤销与真实监督 | [W17-99](tasks/steps/W17-99.md) |
| W18 | [W18-01](tasks/steps/W18-01.md) 一致性备份和迁移前快照；[W18-02](tasks/steps/W18-02.md) 新目录恢复并核对双端上下文 | [W18-99](tasks/steps/W18-99.md) |
| W19 | [W19-01](tasks/steps/W19-01.md) 冻结隔夜故障计划并启动真实运行；[W19-02](tasks/steps/W19-02.md) 次日从两端恢复并独立核验 | [W19-99](tasks/steps/W19-99.md) |
| W20 | [W20-01](tasks/steps/W20-01.md) 制作Windows CLI和Desktop安装产物；[W20-02](tasks/steps/W20-02.md) 全量发布门和真实证据覆盖复现 | [W20-99](tasks/steps/W20-99.md) |
| W21 | [W21-01](tasks/steps/W21-01.md) 交付实际价值、操作手册与剩余边界 | [W21-99](tasks/steps/W21-99.md) |

## 3. 精确状态和回执

W00-01即初始化不存在的新版状态；W00-02只接续到候选worktree，不能覆盖。复制[step_state.template.json](examples/step_state.template.json)到execution/v2.4/step_state.json；它绑定本交付plan的SHA-256，steps为空。W00保护现场后才能初始化，现存文件绝不覆盖：

```powershell
$specRoot = 'D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4'
$repoRoot = 'D:\作品集\ResearchOS\research-os'
$statePath = Join-Path $repoRoot 'execution\v2.4\step_state.json'
if (Test-Path -LiteralPath $statePath) { throw 'State exists; read and validate it, do not overwrite.' }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $statePath) | Out-Null
Copy-Item -LiteralPath (Join-Path $specRoot 'examples\step_state.template.json') -Destination $statePath
python "$specRoot\tools\task_packet.py" next --state $statePath
```

状态为NOT_STARTED/IN_PROGRESS/EXECUTION_REPORTED/ACCEPTED/BLOCKED/FAILED/CANCELLED；缺记录是NOT_STARTED。BLOCKED/FAILED/CANCELLED不自动重试，恢复条件满足后留原因和失败计数再IN_PROGRESS。合法但无READY退出3，坏计划/状态/伪接受退出2，成功退出0只是工具完成。

ACCEPTED记录须有id/status、不同且非空的executor_id/verifier_id、非空evidence数组。每项evidence有相对state父目录的path和SHA-256；必须现存且在施工根内，禁止绝对路径、..和逃逸软链接。引用实际独立审查/证据索引，不是“PASS”一句话。所有依赖也要ACCEPTED。见[step_receipt.template.json](examples/step_receipt.template.json)，模板是NOT_RUN，不能直接作通过证据。

工具可拒绝缺证据/hash变化，但不认证身份、不替代独立审查。Verifier须独立权限/上下文读产物，正式holdout在候选不可读环境；不同Agent名字不构成权限隔离。最终产品Acceptance仍由真实服务和独立流程控制。

plan_hash不同先核对规格，不能直接替换hash掩盖变化。批准升级后记录ADR/旧plan/回执hash，再对受影响卡重验。

## 4. 检查点和持续运行

[checkpoint.template.json](examples/checkpoint.template.json)包括项目ID、repo/HEAD、spec/plan hash、当前/下一卡、产物/证据、未完子步、下一真实命令、资源阻塞、worker/session、失败指纹/次数、无进展、未知费用、用户补充和时刻。

先写证据并hash；state/checkpoint由单一整合者用同目录临时文件+原子替换，写前检查expected revision，保留旧记录和失败历史。工具不提供自动接受接口、不清理用户数据。

每三卡或连续两回合未形成用户能力更新value_checkpoint；连续两个检查点只有文档/fixture/基础设施时优先解除最短用户流程缺口，暂停非必要扩展，不豁免完整正式门。

宿主turn上限/断开/暂停前留检查点。按20在桌面原任务中使用实际继续/恢复入口，或在桌面新会话读取完整Goal和本地state。用户停止不能自动恢复；普通补充不重置计数。

## 5. 最短真实使用路径

W00/01/02 → W03 → W17-01身份 → W04-01项目/W04-02上下文/W12-01费用 → W05-01模型工具 → W13-01桌面首用/W05完整CLI → W06验收/单写者 → W13-02工作区 → W14-01真实任务。以卡DAG为准，独立卡可并行，施工并发默认2。

随后完成来源/证据/实验/Jev/技能、11页和手机，再备份/隔夜/自改回滚/干净发行。真实8小时不加速，外部资源不以fixture替代。最终检查22个-99与42正式用例；71卡记录齐不是唯一完成依据。

施工元数据的通用写入规则：每卡只写自身receipt目录；step_state/checkpoint只由唯一施工整合者在独立复核后更新。父allowed_paths包含子卡范围，具体产品文件仍服从W02已登记owner；共享文件不能因总范围允许就并发写。

本轮施工只维护一份可路由step_state与不可变回执。若旧工具仍需要bootstrap_ledger，按-99和独立回执生成兼容投影，不再人工维护另一套接受状态；旧根台账保持历史。

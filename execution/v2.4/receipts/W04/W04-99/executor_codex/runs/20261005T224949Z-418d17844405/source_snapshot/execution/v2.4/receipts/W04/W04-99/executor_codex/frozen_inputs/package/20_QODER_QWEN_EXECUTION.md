# 20 · Qoder桌面端Agent + Qwen3.8-Flash执行手册

版本：2.4.0，入口修订2；日期：2026-10-01。用户明确施工由桌面端Agent完成。自己的ResearchOS CLI仍是必须交付的产品，与施工宿主区分。

## 1. 桌面入口与已核实边界

官方[Qoder桌面概览](https://docs.qoder.com/qoder/overview)说明独立Qoder桌面产品可按工作区委派编码任务；[IDE概览](https://docs.qoder.com/desktop/overview)区分Editor与Quest。沿用用户正在使用的桌面产品和当前项目，不要求迁移聊天或改用CLI。

[IDE发布说明](https://docs.qoder.com/release-notes/desktop)确认Quest支持Goal-driven execution和Run Spec as Goal。[Agent模式](https://docs.qoder.com/user-guide/quest/agent-mode)说明可创建Agent任务并添加文件上下文。按钮文字和入口位置按实际安装版本，不将CLI的/goal子命令、--turns、--resume当作桌面按钮协议。

[模型选择器](https://docs.qoder.com/user-guide/chat/model-tier-selector)列出Qwen3.8-Flash。执行时在当前桌面模型面板选择这个具体型号并核对，不选Auto/其他型号代替。文档支持不等于当前本机账号已实际选中；本次没有操作桌面UI或启动施工。

## 2. 用户怎么交给Agent

1. 在桌面Coding工作区或IDE Quest中打开现有 `D:/作品集/ResearchOS/research-os`，选择Agent。
2. 在模型选择器选择具体型号Qwen3.8-Flash；确认当前目标工作区。已有Agent会话即可继续，不重复建仓库或重新生成项目身份。
3. 将本包00_START_HERE.md和08_AGENT_EXECUTION_GOAL.md添加到聊天，粘贴GOAL_START.txt。所有引用文件保持在完整本地规格目录，不必一次上传148个文件。
4. 若界面提供Goal入口，就将该完整任务设为Goal；IDE Quest已有Spec时可使用Run Spec as Goal。不要另生成一份删减范围的Spec。版本没有该入口时，可先由桌面Agent按同一文本逐卡执行并保存检查点，宿主自动连续运行保持未验证，不能虚称已进入Goal。

相邻规格目录若因工作区权限不可读，通过桌面支持的附件/目录授权提供整包，或将整包复制到本轮隔离候选工作区spec/v2.4；不扩大到其他私有项目，不让Agent绕过宿主拒绝。W00先记录已有dirty成果，再按18建立同身份候选worktree；桌面已提供本任务worktree时先核对并复用，不重复创建。

## 3. 可直接粘贴的启动文本

```text
你是当前Qoder桌面端的执行Agent。固定使用Qwen3.8-Flash。读取 D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/00_START_HERE.md 和08_AGENT_EXECUTION_GOAL.md，在 D:/作品集/ResearchOS/research-os 按完整规格开始实施自己的ResearchOS CLI与Windows Desktop。先核对已有身份、Git改动和检查点，再用contracts/execution.plan.json及tools/task_packet.py逐卡实现、验证、独立复核和续跑。保护旧成果，全部22父任务及42正式用例有效接受前不得宣布完成。缺资源只阻塞对应支路并保存检查点，不重置失败计数。直接开始已授权工作，不只返回计划，也不要启动Qoder CLI另开施工会话。
```

全文目标在08，其他内容以00/21引导读取。这里没有CLI斜杠或命令行参数。桌面状态卡显示完成也不能替代全部正式验收。

## 4. Agent每轮怎么施工

读取真实身份/Git/当前checkpoint，调用task_packet.py next，按所选卡读取合同及实际代码，实施最小可检查增量，保存实际命令/输出/产物hash并交独立验证；随后更新step_state/checkpoint继续下一卡。71卡、22父任务、42正式用例不变。缺状态从W00-01开始；旧接受按18复核，不能批量复制。

以下命令由桌面Agent的终端工具执行，不需要用户另外开启CLI施工会话：

```powershell
python 'D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/tools/validate_package.py'
python 'D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/tools/task_packet.py' next --state 'D:/作品集/ResearchOS/research-os/execution/v2.4/step_state.json'
```

若桌面选用了候选worktree，state命令的仓库根换成实读核对后的候选根；规格外部只读路径不变。工具输出是准确的依赖/步骤来源，不让模型自行从文字猜DAG。

## 5. 暂停、补充和恢复

补充信息发到同一桌面任务。暂停/停止/继续使用当前UI已有操作；先保存checkpoint及在途工具/未知费用状态。重开桌面后进入原任务，核对工作区、HEAD、模型、进程归属和最新证据，再从下一未完成卡恢复。原任务不可恢复时，新桌面会话重读08与本地状态，不清零失败计数、不另起第二个写入者。

不要用修改历史消息或Revert代替普通继续，这些功能可能撤回后续文件改动。用户停止不能自动恢复；宿主退出、断网、休眠或额度不足后，没有实际运行证据就不宣称仍在后台施工。权限按现有桌面策略，不要求为了开工关闭安全设置。

## 6. 模型和资源缺失

模型面板未提供Qwen3.8-Flash时记录桌面版本、可见模型和错误，形成具体资源请求，不静默换模型、不假称CLI可选就表示桌面可用。产品Mu/Pi所用provider凭据另行核对，不借用或导出Qoder内置登录秘密。

## 7. 旧CLI材料的地位

tools/start_qoder.ps1、probe_qoder.py和相关无模型自检仅作为历史CLI诊断材料保留，不属于本次桌面开工步骤。既有两次CLI附件探针证明的是当时CLI响应，不能证明桌面Agent读写、Goal续跑或ResearchOS完成。本次更正不再调用模型、不启动新的施工会话。当前桌面读写与Goal应由真实执行阶段取得证据。

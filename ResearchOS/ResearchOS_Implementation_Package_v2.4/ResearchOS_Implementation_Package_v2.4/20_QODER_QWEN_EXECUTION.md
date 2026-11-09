# 20 · Qoder + Qwen3.8-Flash 执行手册

版本：2.4.0。核实日期：2026-10-01（Asia/Shanghai）。本文件指导施工宿主；完整产品目标以 [08_AGENT_EXECUTION_GOAL.md](08_AGENT_EXECUTION_GOAL.md) 为准。

## 1. 已确认什么

本机 `C:/Users/yqyyds/.qoder/bin/qodercli/qodercli.exe` 为 **1.1.64**。本轮只执行 `--version`、`--help`、`--list-models`；三者退出码均为 0，当前账号目录明确列出 **Qwen3.8-Flash**。没有提交模型任务，没有启动产品建设，也没有验证 Goal 的实际连续执行。

| 名称 | 本包含义 | 使用位置 |
|---|---|---|
| 用户描述的 qwen3.8flash | 用户指定的模型诉求 | 不直接作为 CLI 参数 |
| Qwen3.8-Flash | 本机 Qoder 目录中的内置模型名 | `--model 'Qwen3.8-Flash'` |
| qwen3.8-flash | 阿里云官方模型 API ID | 直接调用相应提供商 API 时使用；不自动等同于 Qoder 标识 |
| Qoder `/goal` | 让施工 Agent 持续完成实施包 | 在 Qoder 交互终端输入 |
| ResearchOS `/goal` | 本项目要交付的产品功能 | 必须实现并通过独立产品验收 |
| `researchos` CLI | 本项目自己的安装后入口 | 不能以 Qoder、Mu 或 Pi 能启动来替代 |

官方 [Goal Reference](https://docs.qoder.com/cli/goal-reference)、[模型选择](https://docs.qoder.com/cli/model) 与 [Qwen 模型说明](https://www.alibabacloud.com/help/en/model-studio/qwen3-8-flash) 支持上述接口区分。完整本地探针与未验证边界见 [证据摘要](references/Qoder_Qwen_Verification_2026-10-01.md)。模型目录可能变化，实际施工启动时重新运行只读探针。

## 2. 正常启动入口

已提供 [tools/start_qoder.ps1](tools/start_qoder.ps1)。它自动定位本包和相邻 `research-os` 仓库，优先查找 `qodercli.exe`，再使用本机已观察到的安装位置；先验证规格，再精确匹配模型目录。失败会非零退出，不换模型、不登录、不修改全局配置或剪贴板。

```powershell
$specRoot = 'D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4'
$repoRoot = 'D:\作品集\ResearchOS\research-os'
$qoderCli = 'C:\Users\yqyyds\.qoder\bin\qodercli\qodercli.exe'

# 只显示路径和启动参数，不执行任何前置命令或模型请求。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$specRoot\tools\start_qoder.ps1" -PrintOnly

# 验证规格、CLI版本和模型目录；不启动TUI，不提交模型提示。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$specRoot\tools\start_qoder.ps1" -CheckOnly

# 正常入口：重新检查，然后打印GOAL_START.txt并进入真实TUI。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$specRoot\tools\start_qoder.ps1"
```

以上三个命令是不同模式，可按需要分别执行。`-ExecutionPolicy Bypass` 只作用于该 PowerShell 进程，不修改系统执行策略；若组织策略仍禁止脚本，保留真实错误，不绕过。仓库不在默认位置时传 `-RepoRoot $repoRoot`；CLI 安装位置不同则传 `-QoderCli $qoderCli`。Python 默认使用 `python`，需要指定既有解释器时传 `-PythonExecutable <完整路径>`。`-PrintOnly` 仍检查路径存在，但不宣称规格或模型可用性已经验证。

启动器不会自动把 Goal 注入模型；它显示可粘贴的 `GOAL_START.txt`，由用户在终端核对 `/status` 后启动施工。`-CheckOnly` 是基础检查，不等于 Qwen 推理成功、Goal 启动或产品验收。

本机 `qoder.cmd` 是 CLI/IDE 分派器：首参数是现存目录或文件时会转发 IDE。不要把 `qoder D:\作品集\ResearchOS\research-os` 写成 CLI 启动方法。使用启动器中的明确可执行文件，或经验证的 `qoder -w ...`。

`--add-dir` 用于让宿主读取相邻规格包，不赋予候选修改验收门槛的权力。施工前冻结规格哈希；不得通过编辑本包、旧回执或测试断言制造通过。已有用户修改、项目身份与旧台账继续保留。

进入终端后先输入 `/help` 和 `/status`，确认本次会话使用 Qwen3.8-Flash、位于正确目录，且 `/goal` 可用。`auto` 的含义是宿主自动判断工具授权；它不覆盖用户指令、项目边界或系统拒绝。不要将 `dont_ask` 误写为“自动批准”，它会拒绝需要询问的动作。[权限说明](https://docs.qoder.com/cli/permissions)

## 3. 主 Goal 短入口

在 Qoder 交互输入框粘贴下面一行；它引用完整目标，不把整个规格包粘进一个提示词：

```text
/goal 读取 D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/00_START_HERE.md 与08_AGENT_EXECUTION_GOAL.md，固定Qwen3.8-Flash，交付自有CLI和Windows Desktop及完整规定能力。按contracts/execution.plan.json与tools/task_packet.py逐卡实现、验证、独立复核和续跑。保护现有身份、修改与旧证据；遵守18迁移及17真实工作流程。全部22父任务42用例有效接受前不得自报完成。缺资源只阻塞对应支路并保存execution/v2.4/checkpoint.json，禁止改验收或重置失败计数。 --turns 1000
```

这里的 `--turns 1000` 是明确、有界的宿主执行上限，不承诺 1000 轮内必然完成；也不改变“相同失败最多自动重试 2 次、连续 3 轮无进展则停下该支路”的持久规则。不得通过重复新建 Goal 清除这些计数。需要不同轮次时只更改为正整数，不写“无限重试”。

Qoder 官方提供的是交互会话中的 `/goal <description> [--turns <N>]`。本机 `--help` 没有 `goal` shell 子命令或 `--goal` 参数；本包也未验证 `qoder -p '/goal ...'` 的持续执行语义，因此主入口采用真实 TUI。`/quest` 是多 Agent 工作流提示命令，可按实际需要使用，不替代本 Goal，也不自动证明所有 WBS 已完成。[Slash Commands](https://docs.qoder.com/cli/slash-reference) · [Commands](https://docs.qoder.com/cli/commands)

## 4. 每个施工回合怎么读、怎么交接

首次读取完整 Goal、入口和执行计划；后续按以下固定循环推进，避免小模型反复装入全部文档：

1. 核对当前仓库身份、Git 改动、在途进程和 `execution/v2.4/checkpoint.json`。没有检查点即按未开始处理，不能根据旧聊天猜测完成状态。
2. 读取规范状态 `execution/v2.4/step_state.json`。调用 `task_packet.py next` 只选依赖就绪的一张卡；外部资源阻塞时按完整 Goal 继续独立且就绪的支路。
3. 读取该卡、它引用的合同段与实际受影响代码，确认输入、写入范围、依赖、执行步骤、预期产物和验证命令。不得只看摘要就修改共享实现。
4. 完成该卡的实现和相称验证，保存真实命令、退出码、产物路径/哈希与未通过项。修改跨度过大时拆为可验证小步，保留父任务的完成条件。
5. 将结果交给规定的独立审查流程。工具自身不签收；卡片完成不自动签收整个 WBS，施工状态不等于产品 PASS。
6. 更新检查点后选择下一张依赖就绪卡。关闭窗口、压缩上下文或转交前，必须先保存恢复所需事实。

```powershell
python "$specRoot\tools\task_packet.py" list
python "$specRoot\tools\task_packet.py" show W00-01
python "$specRoot\tools\task_packet.py" next --state "$repoRoot\execution\v2.4\step_state.json"
```

`list`、`show`、`next` 均是只读选择器；缺失 state 时显示首张候选卡不代表任务已经执行。任务卡标识采用 `Wxx-01` 等形式。状态结构以 `contracts/execution.plan.json` 为准，检查点结构沿用本包 examples 中的模板；不要再建一份竞争真值。

检查点至少能定位当前卡、代码基线与脏文件、已运行验证及证据、未决副作用、持久失败计数、资源阻塞、Qoder 会话标识与下一条可执行动作。会话标识取自真实宿主记录，不编造 UUID。不记录密钥、完整敏感配置或其他项目内容。

v2.4 的施工记录写入本仓库 `execution/v2.4/`。旧版本记录保留来源与原始状态；只有针对当前代码、输入、合同和环境重新核实的证据，才能按迁移规则复用。禁止整批把旧 PASS 复制成 v2.4 PASS。

## 5. 查看、暂停、恢复和接管

| 场景 | 操作 | 必须检查 |
|---|---|---|
| 查询当前 Goal | `/goal status` | 当前目标、状态和已用轮次；它不是产品验收结果 |
| 主动暂停 | `/goal pause` | 检查点已写入；在途工具按实际状态记录 |
| 同会话继续 | `/goal resume` | 先确认暂停原因已消除，不清零业务重试计数 |
| 重启后恢复 | 用 `--resume <真实session-id>` 启动，再查 `/goal status`，必要时 `/goal resume` | 代码、进程、未决副作用和检查点对账 |
| 多窗口接管 | 原 owner 确认退出或停止后，在目标会话 `/goal take` | 确认唯一施工 owner；不是两个窗口同时写同任务 |
| 取消目标 | `/goal clear` | 它清除宿主 Goal；不要据此声称工具、子进程或产品任务均已取消 |

```powershell
& $qoderCli -w $repoRoot --add-dir $specRoot --model 'Qwen3.8-Flash' --permission-mode auto --resume '<真实-session-id>'
```

只有确认最近会话就是本次施工时才用 `--continue`；优先保存并使用明确 session ID，避免接回其他工作。

官方 Reference 规定：Goal 与会话一起持久化；进程中断后的活动 Goal 在下次启动降为 paused；达到轮次上限也会暂停。上限触发后 `/goal resume` 增加 100 轮，提前暂停的恢复不扩展原上限。Goal 不自行改变权限模式。[Goal Reference](https://docs.qoder.com/cli/goal-reference)

**关闭终端、系统休眠、宿主退出或轮次耗尽后，不能声称 Qoder 仍在后台施工。** 只有存在并验证了实际进程、任务归属、事件与输出，才报告仍在运行。Qoder Goal 显示 complete、清空或没有活动 Goal，也不能替代本包全部验收和独立接受。

## 6. 指定模型与资源失败

施工和恢复都显式选择 `Qwen3.8-Flash`。不能改为 `auto`、其他 Qwen 版本、其他供应商或自建别名后仍声称满足用户指定模型。不要凭模型回复的自我介绍认定实际型号；保留启动参数、宿主状态、可取得的响应型号元数据。

启动时若目录不再列出该模型：刷新目录与 `/model`，记录版本、时间和明确错误；不要发反复探测请求。需要用户提供账户/额度/后端时，资源请求只写：缺少什么、阻塞哪张卡/哪项门、已取得哪些证据、可继续哪些支路、恢复后第一条验证命令。认证失败、额度不足、限流、网络失败、模型不可选、工具调用不支持分别记录，不都归为“模型效果差”。

本机已有内置 Qwen3.8-Flash，无需为了开工额外创建 BYOK。若将来确需 BYOK，先查看当前账号 `/model` 的 Custom 向导；模型/provider 目录以向导为准，不手写 `settings.json` 的猜测字段。IDE 的自定义 Base URL 功能不能自动当成 CLI 的已验证能力。[CLI Custom Models](https://docs.qoder.com/cli/custom-models)

不要在手册中固化“免费”、促销价格、最大上下文或 reasoning 参数。参数以当时模型面板实际支持值为准；未验证能力保持未验证。

## 7. 开工前的最小模型读取检查

已提供 [tools/probe_qoder.py](tools/probe_qoder.py)：一次有界的指定模型附件理解检查，只附加入口、完整 Goal 和 W00-01 单任务卡。全部 Agent 工具禁用，MCP 禁用，不保存会话、不自动模型重试；默认最多 120 秒。它不验证 Read 工具调用或 Goal 长任务。

```powershell
# 只展示参数，不调用模型、不写报告。
python "$specRoot\tools\probe_qoder.py" --print-only

# 真正调用一次模型。--output必须由执行者明确指定，且不得位于规格包内。
python "$specRoot\tools\probe_qoder.py" --output "$repoRoot\execution\v2.4\probes"
```

本轮未执行模型探针。实际执行会使用已配置账户并产生正常提供商用量；输出是脱敏报告和需要人工逐字段检查的响应，exit 0 不自动产生 PASS。Windows 运行器将本次进程挂起创建、放入专属 Job Object 后再恢复，超时清理自己的进程树；不扫描或终止其他 Qoder 会话。

[tools/test_qoder_tools.py](tools/test_qoder_tools.py) 已在本机完成 4 项无模型检查：参数与缺附件、运行输出、超时清理自身子孙且保留无关进程、启动器显示/检查模式和模型缺失。它们使用临时模拟程序，不等于 Qoder 模型或产品验收。可复跑：

```powershell
python -B "$specRoot\tools\test_qoder_tools.py"
```

模型探针详情与边界见 [证据摘要](references/Qoder_Qwen_Verification_2026-10-01.md)。通过后仍须按 WBS 实现代码、运行真实 CLI/Desktop、验证取消/恢复/安装/双端接续并完成独立验收。

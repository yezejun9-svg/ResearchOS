# ResearchOS v2.4 · 实施规格包入口

日期：2026-10-01（Asia/Shanghai）。交给 Qoder CLI，施工模型固定 `Qwen3.8-Flash`。

目标是自己的 `researchos` CLI Agent 和 Windows Desktop：能在真实项目中对话、读改文件、用工具、看 diff、跑测试、持续 Goal，并从两端接续同一会话。已有研究、Jev、协作、隔夜恢复、手机监督和自我改进要求全部保留。先让用户完成真实工作，再闭合研究与改进；完整范围没有缩减。

已有 `research-os` 仓库和历史成果，默认按 [18](18_EXISTING_REPOSITORY_MIGRATION.md) 接续。包内 `NOT_STARTED / NOT_RUN` 表示 **v2.4 的新验收尚未执行**，不表示历史代码不存在。旧规格和回执保留，不能复制旧 PASS 来接受新要求。本次编制只更新规格交付物，没有实施或验收新产品。

## 1. 直接交给 Qoder

在 PowerShell 执行入口；它核对规格、Qoder CLI 和模型目录，再打开真实终端，并显示要粘贴的短 Goal：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4\tools\start_qoder.ps1'
```

在 Qoder 中核对 `/status`，粘贴 [GOAL_START.txt](GOAL_START.txt)。完整目标是 [08_AGENT_EXECUTION_GOAL.md](08_AGENT_EXECUTION_GOAL.md)，启动/暂停/续跑见 [20](20_QODER_QWEN_EXECUTION.md)。`--turns 1000` 是宿主上限，不保证一轮做完，也不允许无限重试。启动器不自动提交施工 Goal，不静默换模型。

只做前置检查时在同一命令末尾加 `-CheckOnly`；只看参数加 `-PrintOnly`。检查通过不等于模型已施工或产品通过。

## 2. 执行者读取顺序

当前路径如下；这些是本次已有位置，执行前仍须核对身份和存在性，不能声称本文给出了实时HEAD或状态：

| 标识 | 绝对路径 |
|---|---|
| REPOSITORY | `D:/作品集/ResearchOS/research-os` |
| SPEC | `D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4` |
| FULL_GOAL | `D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/08_AGENT_EXECUTION_GOAL.md` |
| STEP_STATE | `D:/作品集/ResearchOS/research-os/execution/v2.4/step_state.json` |

STEP_STATE 当前是否存在必须实读；条件句“没有时从W00-01开始”不表示它现在一定不存在。W00/W01直接使用已确认根下的引导路径，不依赖尚未完成的W02映射。W00-02建立候选worktree后，更新当前根与同身份施工检查点；外部只读SPEC入口仍可使用。

首次读本文件、完整08、[17用户流程](17_USER_JOURNEYS_AND_VALUE.md)、[18现场迁移](18_EXISTING_REPOSITORY_MIGRATION.md)、[20宿主操作](20_QODER_QWEN_EXECUTION.md) 和 [21任务卡循环](21_EXECUTION_CARDS.md)。随后运行任务选择器，每回合读当前卡和其引用的合同与真实代码：

```powershell
python 'D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4\tools\task_packet.py' next --state 'D:\作品集\ResearchOS\research-os\execution\v2.4\step_state.json'
```

没有新版状态时从 W00-01 开始；工具不写状态、不执行任务、不批准回执。71 张卡各有输入、允许路径、步骤、产物、检查、命令绑定、失败规则和交接。它们细化22个父任务；每个 `-99` 仍须等待完整前置和正式证据。W02按真实仓库注册路径和处理器，未实现或零断言必须失败。

## 3. 文件职责

| 文件 | 用途 |
|---|---|
| [01 PRD](01_PRD.md) | 20项需求、范围、成功条件 |
| [02 技术设计](02_TECHNICAL_DESIGN.md) | 控制权、进程、存储、模块和事务 |
| [03 数据](03_DATA_CONTRACTS.md)、[04 API](04_API_CONTRACTS.md) | 字段、状态、请求、响应、错误和鉴权 |
| [05 WBS](05_WBS.md)、[06 验收](06_ACCEPTANCE_TESTS.md) | 22父任务与42正式用例完整合同 |
| [07 运行与演进](07_OPERATIONS_AND_EVOLUTION.md) | 隔夜、费用、备份、恢复、晋升和回退 |
| [08 完整Goal](08_AGENT_EXECUTION_GOAL.md) | 施工目标、授权边界和完成门 |
| [09 组件](09_COMPONENT_DECISIONS.md) | 现成组件处置、固定版本和边界 |
| [10 UI](10_UI_UX_DESIGN.md) | 11视图、两主题、五视口和交互状态 |
| [11 评测](11_EVALUATION_AND_INTEGRATION.md)、[12 交付](12_IMPLEMENTATION_AND_HANDOFF.md) | 评测适配、独立验收、实际命令和交接 |
| [13 Harness](13_HARNESS_DESIGN.md)、[14 CLI/Desktop](14_CLI_DESKTOP_PRODUCT.md) | H01–H10、终端、共享会话和安装 |
| [15 新项目](15_NEW_PROJECT_WORKFLOW.md)、[16 采用判断](16_ADOPTION_JUDGMENT.md) | 先本地后研究、判断后源码复用；J01–J04 |
| [17 用户流程](17_USER_JOURNEYS_AND_VALUE.md) | 首次使用、真实任务、双端接续和U01–U09 |
| [18 现场迁移](18_EXISTING_REPOSITORY_MIGRATION.md) | 现有Go/SQLite资产、身份和历史保护 |
| [19 Desktop蓝图](19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md) | 固定Mu/Craft源码切口、界面对接与安装 |
| [20 Qoder](20_QODER_QWEN_EXECUTION.md)、[21 任务卡](21_EXECUTION_CARDS.md) | Qwen执行、71卡顺序、检查点和停机恢复 |
| [22 客户端接口](22_CLIENT_INTERFACE_DETAILS.md) | 23方法、14事件、OS引导、模型/文件/权限 |
| [contracts/](contracts/) | domain/OpenAPI/tasks/acceptance/UI/Harness/product/adoption/delivery/execution.plan机器合同 |
| [tasks/steps/](tasks/steps/) | 从execution.plan生成的71张卡 |
| [可交互工作区预览](ui/workbench-prototype.html) | 离线示例，不计产品验收 |
| [完整参考板](ui/reference.html)、[设计token](ui/design-tokens.json) | 原设计板和统一两主题token |
| [examples/](examples/) | 正负协议样例、12评测夹具和施工模板 |
| [references/](references/) | 固定源码/许可、本机Qoder核验和历史研究 |
| [清单](PACKAGE_MANIFEST.json)、[规格校验](PACKAGE_VALIDATION.json) | 文件hash、版本和校验结果 |

机器字段以contracts为准；范围以01为准；接口精细语义以22/schema为准；接续以18为准；视觉以10/19/UI合同为准；最终完成以06为准。05/06/任务卡是机器合同阅读视图。发现冲突登记引用并提修订，不修改门槛制造通过。references旧路线和旧提问不覆盖当前合同。

## 4. 已冻结的工程默认

保留现有Go/SQLite业务调度、权限、预算、验收和项目真值。优先适配固定Mu的CLI/Agent/Desktop，备选Pi+固定Craft壳；Mu worker只执行Go委派的工作。Desktop不启动第二业务调度器。源码/许可/入口已核查，构建和集成资格仍由W01实测。

源码采用先本地盘点，再按15/16核验许可、实际能力和G01–G07。Jev的 `reuse_selection` 仅在当前用途资格内给建议，最终由硬门和独立复核决定；合适才clone/fork或复用模块，拒绝/观察也保留证据。

本地首次使用不需要复制Owner token、开网页服务或安装开发环境。宿主经本机主体初始化和续期；模型秘密不进入普通消息/日志。两端使用同session、writer epoch、事件水位；保存文件验证当前Task与基线hash。

FIRST-USE可能在构建期已修好。产品Agent的第一件编码工作要从当前仍存在的问题中冻结，不造bug或重复重写。施工Qoder改代码不能冒充ResearchOS产品Agent已能工作。

默认cap=null，但同失败最多自动重试2次、连续3轮无进展停止支路。缺资源提出具体请求并继续独立工作；新窗口/Goal不清零计数。普通技术选择自主推进；购买/充值、对外消息、生产切换看实际已有授权。

## 5. 校验和完整交付

包根运行 `python tools/validate_package.py` 只校验规格和hash；`python tools/test_task_packet.py`、`python tools/test_qoder_tools.py` 检查配套工具。这些不启动产品，Qoder只读附件探针也不证明产品或长时Goal完成。

完整完成须有：两个安装入口、真实读改文件和工具、共享会话、完整研究/Jev/评测、11页真实API、手机监督、8小时真实隔夜、备份恢复及实际回滚；22父任务/42用例由独立流程接受，引用绑定当前版本。规格PASS、模型“完成”、截图或fixture都不能替代。

本包包含旧单独复用规则和Goal的必要要求，无需再拼接。相邻ResearchOS_Agent_Goal_v2.4.md与08一致；旧v2.3和原产品仓库保持原样。

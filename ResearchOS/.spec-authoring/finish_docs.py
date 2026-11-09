from pathlib import Path
import hashlib,json,re
P=Path(__file__).resolve().parents[1]/'ResearchOS_Implementation_Package_v2.4'
def write(name,text): (P/name).write_text(text.strip()+'\n',encoding='utf8')
def put(name,obj):write(name,json.dumps(obj,ensure_ascii=False,indent=2))
plan=json.loads((P/'contracts/execution.plan.json').read_text(encoding='utf8'))
plan_hash=hashlib.sha256((P/'contracts/execution.plan.json').read_bytes()).hexdigest()
write('00_START_HERE.md',r'''
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

本地首次使用不需要复制Owner token、开网页服务或安装开发环境。宿主经本机主体初始化和续期；模型秘密不进入普通消息/日志。两端使用同session、writer epoch、事件水位；保存文件验证当前Task与基线hash。

FIRST-USE可能在构建期已修好。产品Agent的第一件编码工作要从当前仍存在的问题中冻结，不造bug或重复重写。施工Qoder改代码不能冒充ResearchOS产品Agent已能工作。

默认cap=null，但同失败最多自动重试2次、连续3轮无进展停止支路。缺资源提出具体请求并继续独立工作；新窗口/Goal不清零计数。普通技术选择自主推进；购买/充值、对外消息、生产切换看实际已有授权。

## 5. 校验和完整交付

包根运行 `python tools/validate_package.py` 只校验规格和hash；`python tools/test_task_packet.py`、`python tools/test_qoder_tools.py` 检查配套工具。这些不启动产品，Qoder只读附件探针也不证明产品或长时Goal完成。

完整完成须有：两个安装入口、真实读改文件和工具、共享会话、完整研究/Jev/评测、11页真实API、手机监督、8小时真实隔夜、备份恢复及实际回滚；22父任务/42用例由独立流程接受，引用绑定当前版本。规格PASS、模型“完成”、截图或fixture都不能替代。

本包包含旧单独复用规则和Goal的必要要求，无需再拼接。相邻ResearchOS_Agent_Goal_v2.4.md与08一致；旧v2.3和原产品仓库保持原样。
''')
index=['| 父任务 | 实施卡（从左到右；仍须按依赖选择） | 正式终验 |','|---|---|---|']
for i in range(22):
    tid=f'W{i:02d}';ss=[s for s in plan['steps'] if s['parent_task']==tid and s['phase']=='IMPLEMENTATION_SLICE']
    index.append('| '+tid+' | '+'；'.join(f"[{s['id']}](tasks/steps/{s['id']}.md) {s['title']}" for s in ss)+f' | [{tid}-99](tasks/steps/{tid}-99.md) |')
body=r'''
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

<!-- STEP_INDEX -->

## 3. 精确状态和回执

复制[step_state.template.json](examples/step_state.template.json)到execution/v2.4/step_state.json；它绑定本交付plan的SHA-256，steps为空。W00保护现场后才能初始化，现存文件绝不覆盖：

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

宿主turn上限/断开/暂停前留检查点。按20用实际/goal resume，或新会话读取完整Goal和本地state。用户停止不能自动恢复；普通补充不重置计数。

## 5. 最短真实使用路径

W00/01/02 → W03 → W17-01身份 → W04-01项目 → W13-01桌面首用 → W04-02上下文/W12-01费用 → W05 CLI → W06验收/单写者 → W13-02工作区 → W14-01真实任务。以卡DAG为准，独立卡可并行，施工并发默认2。

随后完成来源/证据/实验/Jev/技能、11页和手机，再备份/隔夜/自改回滚/干净发行。真实8小时不加速，外部资源不以fixture替代。最终检查22个-99与42正式用例；71卡记录齐不是唯一完成依据。
'''
write('21_EXECUTION_CARDS.md',body.replace('<!-- STEP_INDEX -->','\n'.join(index)))
put('examples/step_state.template.json',{'schema_version':'1.0','package_version':'2.4.0','plan_sha256':plan_hash,'steps':[]})
put('examples/checkpoint.template.json',{'schema_version':'1.0','package_version':'2.4.0','status':'NOT_STARTED','revision':0,'expected_previous_revision':None,
 'project_id':None,'repository_root':None,'head':None,'dirty_paths':[],'spec_manifest_sha256':None,'plan_sha256':plan_hash,
 'current_step_id':None,'next_step_id':'W00-01','next_command':{'cwd':'SPEC','argv':['python','tools/task_packet.py','show','W00-01']},
 'substeps':[],'artifacts':[],'evidence_index':[],'blocked_resources':[],'workers':[],'side_effects_pending':[],
 'failure_counters':[],'no_progress_rounds':0,'usage_known':[],'usage_unknown':[],'value_checkpoint':{'status':'NOT_RUN','capabilities_observed':[],'documentation_only_checkpoints':0},
 'latest_user_instructions':[],'updated_at':None,'updated_by':None})
put('examples/step_receipt.template.json',{'template_version':'2.4.0','status':'NOT_RUN','step_id':None,'parent_task':None,'executor_id':None,'verifier_id':None,
 'input':{'plan_sha256':plan_hash,'spec_manifest_sha256':None,'repository_head':None,'code_hashes':{},'data_version':None},
 'commands':[],'check_results':[],'artifacts':[],'negative_cases':[],'remaining_blocks':[],
 'independent_review':{'status':'NOT_RUN','reviewer_id':None,'evidence_index_sha256':None,'acceptance_baseline_sha256':None,'reviewed_at':None},
 'notice':'Template is not valid accepted evidence. Fill actual values after execution; executor cannot self-approve.'})
# Rewrite the complete generated views after final contract/plan amendments.
tasks=json.loads((P/'contracts/tasks.json').read_text(encoding='utf8'));cases=json.loads((P/'contracts/acceptance.json').read_text(encoding='utf8'))
def blob(v):return '```json\n'+json.dumps(v,ensure_ascii=False,indent=2)+'\n```\n'
wbs=(P/'05_WBS.md').read_text(encoding='utf8');wbs=wbs[:wbs.index('### W00｜')]
for t in tasks['tasks']:
    wbs+=f"### {t['task_id']}｜{t['title']}\n\n**依赖**：{'、'.join(t['depends_on']) or '无'}。\n\n"+'追踪：'+'、'.join(t['requirement_ids'])+'；'+'、'.join(t['acceptance_ids'])+'。\n\n'
    wbs+='任务卡：'+', '.join(f"[{x}](tasks/steps/{x}.md)" for x in t['execution_steps'])+'。\n\n'+blob(t)+'\n'
write('05_WBS.md',wbs)
accept=(P/'06_ACCEPTANCE_TESTS.md').read_text(encoding='utf8');accept=accept[:re.search(r'^### [CA]\d\d ·',accept,re.M).start()]
for c in cases['cases']:
    accept+=f"### {c['id']} · {c['title']}\n\n模式：{c['mode']}；唯一最终负责人：{c['final_owner_task']}；状态：NOT_RUN。\n\n固定输入：\n\n"+blob(c['input'])+'\n完整合同：\n\n'+blob(c)+'\n'
write('06_ACCEPTANCE_TESTS.md',accept)
print('Entrypoint, execution guide, templates and contract projections written.')

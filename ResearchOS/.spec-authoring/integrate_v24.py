from __future__ import annotations
import hashlib, json, re
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'ResearchOS_Implementation_Package_v2.4'
def load(p): return json.loads((P/p).read_text(encoding='utf8'))
def put(p,x): (P/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def edit(p,pairs):
    f=P/p; s=f.read_text(encoding='utf8')
    for a,b in pairs: s=s.replace(a,b)
    f.write_text(s,encoding='utf8')
def blob(x): return '```json\n'+json.dumps(x,ensure_ascii=False,indent=2)+'\n```\n'

for f in P.glob('*.md'):
    if f.name.startswith(('19_','20_','22_')): continue
    edit(f.name,[('版本：2.3；','版本：2.4.0；'),('版本：`2.3`','版本：`2.4.0`'),
        ('execution/path_ownership.json','execution/v2.4/path_ownership.json'),
        ('execution/commands.json','execution/v2.4/commands.json'),
        ('execution/bootstrap_ledger.json','execution/v2.4/bootstrap_ledger.json')])

edit('01_PRD.md',[('新建隔离仓库','保持项目身份的隔离候选worktree'),('新隔离仓库','同身份隔离worktree')])
edit('02_TECHNICAL_DESIGN.md',[
    ('本包及后续新建的 ResearchOS 独立仓库','本包对应的现有 ResearchOS 仓库及其同身份候选worktree'),
    ('输出ADR-001、route.json','按既有编号输出新的迁移/路线ADR（全新仓库才使用ADR-001）、execution/v2.4/route.json'),
    ('以下是 W02 需要创建的目标结构，不代表第三方现有目录。','以下是 W02 需映射的逻辑结构，优先保留当前仓库目录；不意味着重建目录。')])
edit('04_API_CONTRACTS.md',[
    ('只接受已验证配置','只接受已做格式、身份和授权校验的配置引用（可以尚未联网验证）'),
    ('OWNER由本地首次配对得到','OWNER由受保护的本机OS身份bootstrap一次性建立'),
    ('OWNER 由本地首次配对得到','OWNER 由受保护的本机OS身份bootstrap一次性建立')])
edit('17_USER_JOURNEYS_AND_VALUE.md',[
    ('第一件真实工作固定为 ISSUE-FIRST-USE-001：消除当前首次使用依赖手工管理命令和复制短期 Owner token 的步骤，让 Desktop/CLI 在经过本机身份鉴别后自动接入同一个受保护宿主。',
     '首次可用门固定为 ISSUE-FIRST-USE-001：消除手工管理命令和复制短期 Owner token，让 Desktop/CLI 经本机身份鉴别后接入同一受保护宿主。首次可用门可能在构建期间已完成；产品Agent的第一件编码任务须在演示前从当前未解决问题中另行冻结：先复现尚存在的缺陷，已完成则选下一项已要求但缺失的能力，例如 researchos doctor --json 的真实环境诊断。记录 issue_ref、当前失败复现、允许文件、用户可见预期、冻结测试和独立接受者。不得回退已有修复、人为植入缺陷、以无改动或重复重写冒充真实编码成果。'),
    ('输入 ISSUE-FIRST-USE-001 的任务描述','输入按第1节冻结的未完成 issue_ref 及任务描述'),
    ('输入“找出当前首次登录流程，说明原因，修复 ISSUE-FIRST-USE-001 并运行相关检查”。',
     '输入“按已冻结的真实问题 <issue_ref> 读取相关实现，完成所要求的修复或功能增量，运行冻结的相关检查并展示 diff”。')])
edit('18_EXISTING_REPOSITORY_MIGRATION.md',[
    ('创建输入 hash 绑定的 step_state/checkpoint 和 current_spec 指针。',
     '创建输入 hash 绑定的 step_state/checkpoint 和 execution/v2.4/current_spec.json 指针。新版 route/path_ownership/commands 保存在 execution/v2.4；旧根登记保持历史。已有 execution/command_dispatcher/dispatch.py 可以在候选分支内扩展为按 current_spec 选择新登记，默认无有效指针仍按旧行为；不能修改旧登记内容伪称历史更新。'),
    ('旧网页截图不覆盖新 Electron 安装包','旧网页截图不覆盖新的原生Desktop安装包')])

tasks=load('contracts/tasks.json'); cases=load('contracts/acceptance.json'); delivery=load('contracts/delivery.contract.json')
tm={t['task_id']:t for t in tasks['tasks']}; cm={c['id']:c for c in cases['cases']}
delivery['first_real_coding_task_policy']={
 'freeze_time':'Immediately before product-agent demonstration on the current candidate build',
 'selection':'Choose a reproducible unresolved user-visible issue; if first-use was already fixed choose an explicitly required missing capability such as doctor --json.',
 'required_fields':['issue_ref','baseline_failure_command','baseline_output_hash','allowed_files','expected_behavior','frozen_checks','independent_verifier'],
 'forbidden':['reintroduce_fixed_bug','synthetic_bug_planted_for_demo','zero_diff_fake_success','construction_host_work_claimed_as_product_agent_work']}
for cap in delivery['capabilities']:
    case=cm[cap['case_id']]; task=tm[cap['task_id']]
    if cap['command_key'] not in case['command_keys']: case['command_keys'].append(cap['command_key'])
    owner=tm[case['final_owner_task']]
    if cap['command_key'] not in owner['verification_command_keys']: owner['verification_command_keys'].append(cap['command_key'])
    if cap['command_key'] not in task['verification_command_keys']: task['verification_command_keys'].append(cap['command_key'])
    case['input'].get('delivery_replays',{}).get(cap['id'],{}).update({'real_issue_selection_policy':'delivery.contract.json:first_real_coding_task_policy'})

def rewrite_tree(obj):
    if isinstance(obj,str):
        return obj.replace('execution/commands.json','execution/v2.4/commands.json').replace('execution/path_ownership.json','execution/v2.4/path_ownership.json').replace('execution/bootstrap_ledger.json','execution/v2.4/bootstrap_ledger.json')
    if isinstance(obj,list): return [rewrite_tree(v) for v in obj]
    if isinstance(obj,dict): return {k:rewrite_tree(v) for k,v in obj.items()}
    return obj
tasks=rewrite_tree(tasks)
tasks['path_aliases']['EXECUTION']='本轮施工命名空间 execution/v2.4；旧 execution 根记录保持历史。dispatcher代码可复用原路径，但按新版current_spec选择registry。'
tasks['path_aliases']['WORKSPACE']='现有ResearchOS同身份隔离候选worktree；无合法仓库时才新建research-os；禁止访问无授权项目。'
tasks['path_aliases']['REAL_ISSUE_SCOPE']='执行真实编码示范前冻结的具体允许文件；不是全仓库通配符。'
tasks['bounded_execution_plan']='execution.plan.json'
tasks['dependency_policy']['early_slice_policy']={
 'authority':'execution.plan.json IMPLEMENTATION_SLICE dependencies permit an explicitly scoped early implementation and evidence review.',
 'does_not_change':'Parent task depends_on and all 42 final case owners; PARENT_FINAL_GATE depends on all parent-final gates.',
 'qualification_blocked':'W01-02 may accept an honest negative/blocked qualification report and W01-03 a provisional development route. Neither accepts W01-99 or claims product qualification.',
 'when_input_changes':'Invalidate affected slice receipts and replay relevant checks before accepting parent gates.'}
put('contracts/tasks.json',tasks);put('contracts/acceptance.json',cases);put('contracts/delivery.contract.json',delivery)

protocol=load('contracts/client.protocol.schema.json'); product=load('contracts/product.contract.json'); ui=load('contracts/ui.contract.json')
methods=protocol['x-method-contracts']; events=protocol['x-event-contracts']
lp=product['local_protocol'];lp['methods']=list(methods);lp['payload_definitions']={m:v['payload'] for m,v in methods.items()};lp['result_definitions']={m:v['result'] for m,v in methods.items()};lp['event_definitions']=events
lp['details_document']='22_CLIENT_INTERFACE_DETAILS.md'
ui['client_methods']=list(methods)
actions=[
 ('choose_directory','workspace.register','S00','native directory picker returns canonical approved root'),
 ('list_workspaces','workspace.list','S00','local identity authenticated'),
 ('create_project','project.bootstrap','S00','workspace binding and local inventory exist'),
 ('provider_models','provider.models','S10','provider configured; show catalog failure distinctly'),
 ('provider_probe','provider.probe','S10','project and model_config_ref exist; validates connection/inference only'),
 ('configure_session','host.configure','S10','session write owner, matching revision/epoch and settled run'),
 ('host_status','host.status','S10','authenticated local identity'),
 ('session_list','session.list','S01','project authorized'),
 ('session_create','session.create','S01','project/workspace/model refs exist'),
 ('session_snapshot','session.get','S01','session authorized'),
 ('continue_here','session.attach','S01','explicit request_write_owner=true and expected_revision; same OS principal; CAS after settled'),
 ('send_message','session.send','S01','writer and current revision/epoch; show permission/queue state'),
 ('pause_resume_cancel','session.control','S01','one target Run or Goal; CANCEL waits settled/children_stopped/queue_empty'),
 ('event_replay','session.events','S01','cursor; CURSOR_EXPIRED requires fresh snapshot'),
 ('handoff','session.handoff','S01','current writer chooses connected authorized target'),
 ('goal_start','goal.start','S01','frozen project context and constraints; complete text retained'),
 ('rename_archive_restore','session.update','S01','authorized mutation; no physical deletion'),
 ('file_tree','workspace.tree','S04','workspace/project root allowed; cursor paging'),
 ('open_file','workspace.read','S04','bounded preview and current permission'),
 ('show_diff','workspace.diff','S04','explicit TASK_BASELINE or GIT_HEAD or GIT_INDEX'),
 ('save_draft','workspace.write','S04','existing editable task selected; matching base hash/revision/epoch; no task disables save'),
 ('attach_file','artifact.import','S01','approved import_ref; bytes not in command envelope'),
 ('answer_permission','permission.respond','S01','unexpired pending request bound to current task/run/action hash')]
ui['client_actions']=[{'id':aid,'method':m,'screen_id':screen,'precondition':condition,
 'waiting':'show pending command_id; do not duplicate effect on retry','failure':'show typed error.code and recoverable; keep draft/user input',
 'conflict':'reload current snapshot while preserving draft; never silently overwrite'} for aid,m,screen,condition in actions]
for screen in ui['screens']:
    screen['local_operation_ids']=list(dict.fromkeys(screen.get('local_operation_ids',[])+[a['method'] for a in ui['client_actions'] if a['screen_id']==screen['id']]))
put('contracts/product.contract.json',product);put('contracts/ui.contract.json',ui)

# Keep all prior narrative rules, regenerate all per-task and per-case fields from the contracts.
wbs=(P/'05_WBS.md').read_text(encoding='utf8'); prefix=wbs[:wbs.index('### W00｜')]
prefix=prefix.replace('工作在新建隔离仓库','工作在现有项目同身份隔离worktree').replace('W00选定的新建隔离仓库根','W00确认的现有项目同身份隔离worktree').replace('选定路线新仓库内','选定路线候选worktree内')
prefix+='\n任务卡补充规则：71张卡见21和contracts/execution.plan.json；早期实施切片按明确卡依赖推进，父任务最终接受仍按下表DAG。每个-99只接受其唯一final owner用例，其他case仅关联检查。\n\n'
parts=[prefix]
for t in tasks['tasks']:
    parts += [f"### {t['task_id']}｜{t['title']}\n",f"**依赖**：{'、'.join(t['depends_on']) or '无'}。\n",'追踪：'+'、'.join(t['requirement_ids'])+'；'+'、'.join(t['acceptance_ids'])+'。\n',
        '任务卡：'+', '.join(f"[{x}](tasks/steps/{x}.md)" for x in t['execution_steps'])+'。\n',
        '以下完整字段与机器合同一致；包含输入、范围、步骤、命令、断言和失败规则。\n',blob(t)]
(P/'05_WBS.md').write_text('\n'.join(parts),encoding='utf8')
accept=(P/'06_ACCEPTANCE_TESTS.md').read_text(encoding='utf8');prefix=accept[:re.search(r'^### [CA]\d\d ·',accept,re.M).start()]
prefix=prefix.replace('ADR-001/route.json','当前有效迁移/路线ADR及execution/v2.4/route.json')
parts=[prefix]
for c in cases['cases']:
    parts += [f"### {c['id']} · {c['title']}\n",f"模式：{c['mode']}；唯一最终负责人：{c['final_owner_task']}；状态：NOT_RUN。\n",'固定输入：\n',blob(c['input']),
        '完整用例字段（任何失败条件和必需断言均不得省略）：\n',blob(c)]
(P/'06_ACCEPTANCE_TESTS.md').write_text('\n'.join(parts),encoding='utf8')

# Sync machine-readable typed method directory into data/API reading docs.
table='\n'.join(['| 方法 | 请求 | 成功结果 |','|---|---|---|']+[f"| `{m}` | `{v['payload']}` | `{v['result']}` |" for m,v in methods.items()])
for doc in ['03_DATA_CONTRACTS.md','04_API_CONTRACTS.md']:
    f=P/doc;s=f.read_text(encoding='utf8');marker='\n## v2.4 完整本地方法索引\n'
    s=s.split(marker)[0]+marker+'\n本地协议23方法、14类事件的精确定义由22和client.protocol.schema.json给出；此表为同源投影。NativeBridge仅传瞬态秘密，不属于普通命令日志。\n\n'+table+'\n'
    f.write_text(s,encoding='utf8')

goal=(P/'08_AGENT_EXECUTION_GOAL.md').read_text(encoding='utf8')
goal=goal.replace('用户首要目标：持续跟踪','在当前任务有明确缺口时，研究能力目标是持续跟踪').replace('背景来自本包和新仓库','背景来自本包、现有合法仓库和当前有效证据').replace('01–07、09–16及contracts','01–07、09–22及contracts').replace('建立独立身份、冻结规格和bootstrap ledger','保留已存在的永久身份、冻结新版规格与本轮施工台账；仅无合法仓库才建立身份')
goal=goal.replace('使用Mu施工时先读完整本文件','Qoder/Qwen是本次施工宿主；Mu是产品复用候选。使用Qoder施工时先读完整本文件')
goal=goal.replace('默认20次/180分钟不是隔夜承诺：','Mu产品上游默认20次/180分钟不是隔夜承诺，Qoder施工/goal另按20的--turns 1000设置：')
goal+='''
## 11. v2.4逐卡执行与不再遗漏的用户体验

先读17真实用户流程、18现场迁移、19桌面源码与对接、20 Qoder运行手册、21任务卡规则、22完整接口。默认CLI/Desktop先形成可使用切片，再闭合研究与自我改进；所有原正式门仍完整。

每回合调用 `python <SPEC>/tools/task_packet.py next --state <REPOSITORY>/execution/v2.4/step_state.json`，读取所选tasks/steps卡和必要合同/现有代码；只做此卡范围，检查后交独立复核并保存真实回执，再继续下一卡。71张卡的唯一机器来源是contracts/execution.plan.json。父任务仍以tasks.json和06完整判定；每个-99必须等父任务依赖的-99。

按18保留旧AGENTS/身份/证据并在候选分支写迁移ADR，施工新版registry在execution/v2.4。原dispatcher可扩展选择版本登记，不覆盖旧commands/path_ownership。卡中路径由W02结合当前仓库绑定；缺映射和未实现处理器不能当PASS。

17的FIRST-USE是产品引导门；第一次让产品Agent修代码时，先冻结当前仍存在的真实问题。问题已解决就选下一个明确要求但缺失的功能，不反向植入故障、不将施工Qoder的文件修改当产品Agent成果。CLI/Desktop都须可实际读改文件、用工具和接续同一session。日常本地使用无需手抄token或启动后台服务。

一个任务卡完成只允许修改施工state，不改变只读规格的NOT_STARTED/NOT_RUN。ACCEPTED要求不同executor/verifier身份、当前证据文件hash、依赖接受；task_packet仅校验结构和选择工作，不认证身份、不替代独立审查。最终仍需42例当前有效产品回执及22个父任务接受。
'''
(P/'08_AGENT_EXECUTION_GOAL.md').write_text(goal,encoding='utf8')
start='/goal 读取 D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/00_START_HERE.md 与08_AGENT_EXECUTION_GOAL.md，固定Qwen3.8-Flash，交付自有CLI和Windows Desktop及完整规定能力。按contracts/execution.plan.json与tools/task_packet.py逐卡实现、验证、独立复核和续跑。保护现有身份、修改与旧证据；遵守18迁移及17真实工作流程。全部22父任务42用例有效接受前不得自报完成。缺资源只阻塞对应支路并保存execution/v2.4/checkpoint.json，禁止改验收或重置失败计数。 --turns 1000\n'
(P/'GOAL_START.txt').write_text(start,encoding='utf8')
print('Integrated canonical contracts, generated WBS/cases and Goal; final plan hash/template generated later.')

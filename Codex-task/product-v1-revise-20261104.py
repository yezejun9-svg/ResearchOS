from pathlib import Path
import datetime, hashlib, json

O=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-plan-20261104')
R=Path('D:/作品集/ResearchOS/research-os')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(n): return json.loads((O/n).read_text(encoding='utf-8'))
def put(n,v):
    with (O/n).open('w',encoding='utf-8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.iterdir()}
a,m,e,p=map(load,['acceptance.json','legacy_mapping.json','evidence.json','plan.json'])
for x in [a,m,e,p]: x['planning_revision']=2;x['revised_utc']=now
for name,x in [('acceptance',a),('legacy_mapping',m),('evidence',e),('plan',p)]:
    x['project_record_path']='execution/product-v1/'+name+'.json'
    x['implementation_state_path']='execution/product-v1/state.json'

# Exact Root corrections before freeze; this is not a historical acceptance edit.
by={x['id']:x for x in a['journeys']}
by['J02']['planned_source_slices']=['S01','S02']
by['J02']['observable_results'].append('Codex exec --json使用实际default_permissions自定义profile；未证明Windows文件权限enforcement前不得显示READY；不与--sandbox同时传参。')
by['J05']['prerequisites'].append('Codex本次自定义filesystem profile已在Windows隔离目标实测；:root deny、:minimal read、:workspace_roots read，候选写入必须另由Root明确授权并验证。')
by['J06']['planned_source_slices']=['S02','S03','S06']
by['J12']['observable_results']=['正常使用无需外部Node和手工后台管理命令；包内CLI/Desktop和Host版本可核；安装/启动/停止/更新/卸载不默删项目；打包成功不能替代实际用户使用。']
by['J12']['evidence_required']=['安装包/source/bundle manifest与SHA','干净Windows安装/启动/停止/卸载记录','包内CLI与Desktop同Host任务/工具/diff流程证据']
by['J13'].update({
 'title':'默认React工作台清爽可用且图谱反映真实事实',
 'prerequisites':['使用当前source-bound Windows Desktop真实Electron窗口和默认既有React工作台；真实Host事件或明确标注来源的已记录任务轨迹可核','三栏/窄屏布局、IME、键盘和reduced-motion检查有明确操作步骤'],
 'observable_results':['默认即三栏：左项目/会话、中会话与底部输入、右任务轨迹/工具/成果；配置按需展开，输入与停止可达','中文IME/键盘/焦点/可读字体、390/320窄屏无不可达控制或横向裁切；深浅主题和reduced-motion可用','图谱节点可定位真实task/run/tool/artifact回执；未知不伪造进度，任务事件commit不谎称Git提交；历史加载不发光、切会话不串轨迹、缺anchor不连邻居'],
 'evidence_required':['真实Windows Electron录屏、关键DOM与1440/1024/768/390/320双主题截图','IME/键盘/焦点/reduced-motion及历史重载行为结果','图节点到Host事件/原回执/hash的逐项关联及缺失/未知反例'],
 'planned_source_slices':['S04','S06','S10'],'required_mode':'REAL_WINDOWS_UI'})

tm={x['legacy_id']:x for x in m['parent_tasks']}
tm['W18'].update({'disposition':'DEFER','v1_journeys':[],'reason':'备份、导出与新目录恢复列POST_V1_OPTIONAL；旧DB迁移和prepared addon不采用。V1必需重启/断线对账仍由J07覆盖，但不冒充备份恢复资格。'})
tm['W21']['v1_journeys']=['J07','J09']
tm['W21']['reason']='保留持久任务/候选/失败回执及可审阅交接；导出恢复后置，下一轮由用户启动，不自动飞轮。'
tm['W20']['v1_journeys']=['J12','J13']
tm['W13']['v1_journeys']=['J01','J03','J09','J12','J13']
cm={x['legacy_id']:x for x in m['formal_cases']}
cm['A12'].update({'disposition':'DEFER','v1_journeys':[],'reason':'备份导出/新目录恢复/迁移失败回退列POST_V1_OPTIONAL；首版J07只验证持久状态重启对账，不宣称旧A12或addon采用通过。'})
cm['A15']['v1_journeys']=['J12','J13']
for lid in ['C23','C24','C26','A10']:
    cm[lid]['v1_journeys']=sorted(set(cm[lid]['v1_journeys']+['J13']))
for x in a['journeys']:
    x['legacy_references']=[y['legacy_id'] for y in m['formal_cases'] if x['id'] in y['v1_journeys']]
m['coverage']['task_dispositions']={d:sum(x['disposition']==d for x in m['parent_tasks']) for d in ['RETAIN','REFRAME','DEFER']}
m['coverage']['case_dispositions']={d:sum(x['disposition']==d for x in m['formal_cases']) for d in ['RETAIN','REFRAME','DEFER']}

p['first_harness']='CODEX_EXEC_JSON_0_166_0'
p['single_authority_reuse']='EXISTING_COORDINATOR_RUN_LEASE_EVENTS_RECEIPTS_AND_STORE'
p['no_new_productv1_journal_or_scheduler_database']=True
s={x['id']:x for x in p['slices']}
s['S01']['behavior']='Root登记接口/字段版本lease后定义有界task输入/输出/检查及状态投影；复用既有Go Host、Coordinator、Run、lease、events与receipt，fresh数据root也用现store；扩字段由Root先版本化，不另建运行journal/调度DB或采用addon。'
s['S02'].update({'title':'第一个Codex exec --json薄driver',
 'proposed_paths':['adapters/harness/adapter.go','adapters/harness/codex_exec.go','adapters/harness/codex_exec_test.go'],
 'behavior':'一期固定本机已通过help确认的Codex0.166.0 exec --json，薄driver仅解析结构化事件、终态、错误和进程生命周期；按default_permissions自定义filesystem profile，禁止同时传--sandbox。先验证Windows权限enforcement，未验证不得READY。app-server/RPC仅后续真正需要per-tool permission bridge时单独评估。',
 'verification':['Codex exec --json实际帧/错误/退出合同与版本绑定','default_permissions隔离路径允许/拒绝的真实Windows enforcement及反例；与--sandbox互斥','命令ACK/任务终态/取消/退出/坏帧/背压分别核验']})
s['S03'].update({'title':'既有Go Host/Coordinator的单任务纵切',
 'proposed_paths':['internal/host/productv1_runtime.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_dispatch.go','internal/domain/client_protocol_journal.go','internal/host/productv1_runtime_test.go'],
 'behavior':'Host作为唯一外层权威，将薄driver接同既有Coordinator/Run/lease/events/receipt；复用现store和真实事件水位，不另造productv1 journal或调度数据库。一次串行实现结束停在候选态，Harness内部模型/工具循环由Harness负责。'})
s['S04'].update({'title':'既有CLI和React三栏接真实Host',
 'proposed_paths':['apps/cli/productv1.go','apps/cli/productv1_test.go','apps/web/src/workbench.jsx','apps/web/src/activity.js','apps/web/src/components/activity-rail.jsx','apps/web/src/workbench.css','apps/desktop/preload/preload.js','apps/desktop/main/lib/ipc.js','apps/desktop/main/main.js'],
 'behavior':'改既有workbench/activity/activity-rail，沿Desktop现preload/preload.js→main/lib/ipc.js→main.js窄链调用同Host；不新建独立productv1/workbench页面。三栏、底部输入、真实会话和工具状态优先，配置折叠。'})
s['S05']['proposed_paths']=['internal/host/productv1_candidate.go','internal/host/productv1_candidate_test.go','apps/web/src/workbench.jsx','apps/web/src/components/activity-rail.jsx','apps/web/src/components/diff-view.jsx']
s['S06']['proposed_paths']=['internal/host/productv1_reconcile.go','internal/host/productv1_reconcile_test.go','apps/web/src/activity.js','apps/web/src/components/activity-rail.jsx','apps/web/src/components/light-layer-adapter.js','tests/ui/productv1-activity-projection.test.cjs']
s['S08']['proposed_paths']=['internal/host/productv1_review.go','internal/host/productv1_review_test.go','apps/web/src/components/review-panel.jsx']
s['S09']['proposed_paths']=['internal/host/productv1_accept.go','internal/host/productv1_accept_test.go','apps/web/src/components/accept-controls.jsx']
s['S10']['proposed_paths']=['apps/desktop/build-development.py','apps/desktop/main/main.js','apps/desktop/preload/preload.js','apps/desktop/main/lib/ipc.js','tests/ui/productv1-workbench-fixture.cjs']
optional=s['S11'];optional.update({'phase':'POST_V1_OPTIONAL','required_for_v1':False,'depends_on':['S06','S10'],'acceptance_journeys':[]})
p['post_v1_optional']=[optional]
p['slices']=[x for x in p['slices'] if x['id']!='S11']
for x in p['slices']: x['acceptance_journeys']=[j['id'] for j in a['journeys'] if x['id'] in j['planned_source_slices']]
p['permission_policy']={'status':'REQUIRED_NOT_ENFORCEMENT_VERIFIED','codex_interface':'exec --json','configuration':'default_permissions custom filesystem profile',
 'baseline_filesystem':[{'path':':root','access':'deny'},{'path':':minimal','access':'read'},{'path':':workspace_roots','access':'read'}],
 'candidate_write':'Only a separately Root-authorized exact owned candidate path may be granted write, after actual Windows allow/deny verification.',
 'do_not_combine_with':['--sandbox'],'per_tool_permission_bridge':'POST_V1_EVALUATE_IF_ACTUALLY_REQUIRED',
 'ready_requires_real_windows_enforcement_evidence':True}
p['open_decisions_before_implementation']=[
 {'id':'D01','choice':'一期固定Codex0.166.0 exec --json。按真实事件格式与default_permissions自定义profile实施，Windows enforcement未验证不得READY；app-server/RPC仅后续per-tool bridge确有需要才评估。'},
 {'id':'D02','choice':'复用既有Coordinator/Run/lease/events/receipt和store；fresh data root不等于新调度DB，扩字段须Root版本化；不恢复旧未采用addon。'},
 {'id':'D03','choice':'UI权限能力必须来自实际enforcement证据；未知或不支持显式展示，不能把exec事件显示伪装成可强制的per-tool批准。'}]
p['non_goals'].append('Task export/new-directory restore (POST_V1_OPTIONAL); restart reconciliation remains required J07.')

for row in e['version_matrix']:
    if row['component']=='installed Codex': row['protocol']='exec --json advertised by actual exec --help; real event execution/cancel and default_permissions Windows enforcement NOT_RUN. app-server/RPC not a V1 prerequisite.'
e['v1_architecture_corrections']=['一期Codex exec --json，不强制先研究app-server/RPC。','唯一权威接既有Coordinator/Run/lease/events/receipt/store，不另productv1 journal/调度DB。','既有React workbench为默认页面；Desktop preload实际为preload/preload.js。','J13真实UI/图谱/IME/窄屏/reduced-motion；导出恢复后置。']
e['permission_policy_requirement']={**p['permission_policy'],'source':'Root explicit V1 planning instruction; not an enforcement test or an independently inspected official-document claim.'}
for rel in ['internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_dispatch.go','internal/domain/client_protocol_journal.go','apps/web/src/activity.js','apps/web/src/components/activity-rail.jsx','apps/desktop/preload/preload.js','apps/desktop/main/lib/ipc.js']:
    f=R/rel;assert f.is_file(),rel
    if not any(x['path']==str(f) for x in e['sources']): e['sources'].append({'group':'researchos_existing_source','path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'observed_utc':now,'method':'READ_EXISTING_BYTES_ONLY','execution_performed':False})
e['planning_revision_record']={'revision':2,'reason':'Root five targeted corrections before freeze; no old history/ledger changed.','superseded_unfrozen_planning_hashes':before}

md=(O/'PLAN.md').read_text(encoding='utf-8')
md=md.replace('状态：**规划完成待Root归档；产品未实现、未验证。** 本包只在C任务目录落盘，不修改Main、旧工作树、旧数据库、旧22/42验收或失败台账。Root归档后按新scope直接实施，不再请求用户重复批准。',
 '状态：**产品V1规划基线；实施状态以`execution/product-v1/state.json`为准，所有产品验收均为NOT_RUN。** 正式方案位于`docs/product-v1/PLAN.md`；DAG、验收、旧规格映射与证据分别位于`execution/product-v1/plan.json`、`execution/product-v1/acceptance.json`、`execution/product-v1/legacy_mapping.json`、`execution/product-v1/evidence.json`。本规划不清除旧工作树、旧数据库、旧22/42验收或失败台账；后续按Root登记的新scope实施，不再请求用户重复批准。')
md=md.replace('默认先验证本机Codex0.166.0的RPC/app-server协议资格，再打通单任务；第二阶段适配Pi0.99.2做只读评审。','一期固定本机已通过exec help确认的Codex0.166.0 `exec --json`薄driver，再打通单任务；第二阶段适配Pi0.99.2 RPC做只读评审。app-server/RPC只在后续确实需要per-tool permission bridge时单独评估，不是一期前置研究。')
md=md.replace('若Codex协议资格不满足，仅阻塞该支路并报告；','若Codex实际事件或权限能力不满足，仅阻塞该支路并报告；')
md=md.replace('Go Host是权限、任务上限、单执行锁、会话身份、持久事件、候选和用户接受的唯一外层权威。CLI/Desktop都是薄客户端。','Go Host是权限、任务上限、单执行锁、会话身份、持久事件、候选和用户接受的唯一外层权威，接同既有Coordinator/Run/lease/events/receipt。fresh数据root仍用现store，扩字段由Root先版本化，不另造productv1 journal、调度DB或第二调度器。CLI/Desktop都是薄客户端。')
md=md.replace('## 一次有限闭环','Codex权限按`default_permissions`自定义filesystem profile：`:root deny`、`:minimal read`、`:workspace_roots read`；候选写入只可另由Root授权确切owned路径并实测。不得同时传`--sandbox`覆盖profile。实际Windows allow/deny enforcement未验证前capability不得READY。V1不把事件显示伪装成exec无法强制的逐工具审批。\n\nUI沿既有`apps/web/src/workbench.jsx`、`activity.js`、`components/activity-rail.jsx`实施；Desktop沿`preload/preload.js`、`main/lib/ipc.js`、`main/main.js`窄链，不另建productv1独立页面。\n\n## 一次有限闭环')
md=md.replace('`acceptance.json`固定13条用户旅程：J01–J09单Harness、J10–J11双Harness、J12–J13 Windows交付。','`acceptance.json`固定13条用户旅程：J01–J09单Harness、J10–J11双Harness、J12 Windows包交付、J13默认React工作台真实可用性与图谱事实（IME、窄屏、reduced-motion、历史不发光及节点回执关联）。任务导出/新目录恢复属于POST_V1_OPTIONAL，不是V1发布门；重启/断线恢复仍是J07必需。')
old='`plan.json`只有11个可审阅的小切片：S01合同/新root→S02 Codex协议→S03单Host运行→S04 CLI/三栏→S05候选diff→S06停止/恢复/LightUI→S07 Pi→S08另一Harness评审→S09用户接受→S10 Windows包→S11记录导出恢复。'
new='`plan.json`必需DAG只有10个小切片：S01合同/现store新root→S02 Codex exec --json→S03既有Coordinator单任务接点→S04既有CLI/React三栏→S05候选diff→S06停止/恢复/LightUI→S07 Pi RPC→S08另一Harness评审→S09用户接受→S10 Windows包与真实UI。S11记录导出/新目录恢复保存在POST_V1_OPTIONAL，不进入首版必需DAG。'
assert old in md;md=md.replace(old,new)
md=md.replace('旧DB迁移及Native prepared addon生产采用、并行实施者集群。','旧DB迁移及Native prepared addon生产采用、任务导出/新目录恢复、并行实施者集群。')
for n in ['plan','acceptance','legacy_mapping','evidence']:
    md=md.replace('`'+n+'.json`','`execution/product-v1/'+n+'.json`')
assert 'RPC/app-server协议资格' not in md and 'productv1_journal.go' not in str(p)
(O/'PLAN.md').write_text(md,encoding='utf-8',newline='\n')
for n,v in [('acceptance.json',a),('legacy_mapping.json',m),('evidence.json',e),('plan.json',p)]: put(n,v)
print(json.dumps({'planning_revision':2,'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(O.iterdir())},'mandatory_slices':len(p['slices']),'optional_slices':len(p['post_v1_optional'])},ensure_ascii=True))

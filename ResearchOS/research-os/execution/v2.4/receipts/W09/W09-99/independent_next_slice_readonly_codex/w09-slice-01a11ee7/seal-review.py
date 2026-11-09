from pathlib import Path
import ast, hashlib, json, datetime

R = Path('D:/作品集/ResearchOS/research-os')
O = R/'execution/v2.4/receipts/W09/W09-99/independent_next_slice_readonly_codex/w09-slice-01a11ee7'
def read(rel): return json.loads((O/rel).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p); b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,x):
    (O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

io=read('original-tool-observations.json');io['newToolError']['ordinal']=913
write('original-tool-observations.json',io)
origins=[io['origin912'],io['newToolError']]
write('failure-origins.json',{'origins':origins,'new_count':2,'counter_reset':False,'root_next_at_allocation':914})
allcopies=[]
for name in ['initial-pins.json','refs-pins.json','sources-pins.json','closure-pins.json']: allcopies.extend(read(name))
refs={}
copychecks=[]
for row in allcopies:
    ref=row['original'];key=str(Path(ref['path'])).lower()
    if key in refs: assert refs[key]==ref
    refs[key]=ref
    b=Path(row['copy']).read_bytes()
    copychecks.append({'copy':row['copy'],'matches_original_pin':len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256']})
assert all(x['matches_original_pin'] for x in copychecks)
write('all-source-pins.json',list(refs.values()))
write('copy-integrity.json',copychecks)
task=next(t for t in read('inputs/005/tasks.json')['tasks'] if t['task_id']=='W09')
step=next(t for t in read('inputs/004/execution.plan.json')['steps'] if t['id']=='W09-99')
cases=read('inputs/006/acceptance.json')['cases'];assert len(cases)==42
write('all42-contract-map.json',[{'id':c['id'],'mode':c['mode'],'final_owner_task':c['final_owner_task'],'wbs_ids':c['wbs_ids'],'assertion_ids':[a['id'] for a in c['assertions']]} for c in cases])
registry=read('refs/003/commands.json')['commands'];routes=[]
for command in step['verification_commands']:
    entry=registry[command['key']];selectors={key:command.get(key,'') for key in ['task_id','check_id','case_id']}
    rejected=[key for key,value in selectors.items() if value and '*' not in entry.get('selectors',{}).get(key,[]) and value not in entry.get('selectors',{}).get(key,[])]
    routes.append({'command':command,'registered_argv':entry['argv'],'registered_owner':entry['owner_card'],'selectors_rejected':rejected,'current_static_dispatch_result':'NOT_IMPLEMENTED_BEFORE_HANDLER' if rejected else 'ELIGIBLE','actual_dispatch_executed':False})
assert len(routes)==6 and all(x['selectors_rejected'] for x in routes)
write('six-route-static-matrix.json',routes)
v6=read('sources/000/handoff.json');source_paths=['internal/domain/domain_test.go','internal/domain/retrieval_test.go','ops/ci/retrieval.py','internal/domain/w09_evidence_export_test.go','ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py']
sources=[{'target':p,'candidate_ref':ref,'owner':'W09 source executor in isolated candidate; Root/W02 serial integration for shared paths','adopted':False} for p,ref in zip(source_paths,v6['candidate_source_refs'])]
write('source-composition-map.json',sources)
states={x['id']:x['status'] for x in read('inputs/002/step_state.json')['steps']}
deps=[{'id':x,'status':states.get(x,'NOT_STARTED_DEFAULT')} for x in step['dependencies']]
go=read('refs/005/locked.json')['tools']['go']['path'];python=read('refs/005/locked.json')['tools']['python']['path']
native=[go,'test','-count=1','-json','-run','^(?:TestW09C19ExplicitOriginAndUnknown|TestW09C19ChainInvalidation)$','./internal/domain']
proposal={
 'schema':'researchos.w09-c19-minimal-next-task.v1','decision':'READY_TO_ASSIGN_SOURCE_COMPOSITION_AND_BOUNDED_PRODUCER_PREPARATION','execution_grant':False,'formal_acceptance':False,
 'task_id':'W09-99-C19-PRODUCER-CONSUMER','mode':'FIXTURE','depends_on':deps,'does_not_depend_on':'W05-99',
 'objective':'Create an isolated current candidate using the existing reviewed v6 exporter/producer/consumer sources; freeze a bounded one-run C19 execution; preserve and independently review raw evidence, then consume the same report through both exact C19 routes.',
 'existing_source_review':pin(O/'sources/007/review.json'),'original_review_ref':next(r['original'] for r in allcopies if r['copy']==str(O/'sources/007/review.json')),
 'source_files':sources,'additional_serial_owner_scope':['execution/v2.4/commands.json exact selector append/routing under W02','Root current source-scope/lease/grant and receipt registration'],
 'do_not_repeat':['Four test-only causal Source files already static-reviewed; do not rewrite their implementation','41 causal scenarios and 8 old regression selectors are separate finite controller work; no blanket execution necessary to create C19 original report','No re-run of accepted W09-01/W09-02 or W03/W07 solely because time passed'],
 'producer_invocation_after_scope_adoption':{'cwd':'NEW_ISOLATED_CANDIDATE_ROOT','argv':[python,'-I','-S','-B','-X','utf8','ops/ci/retrieval.py'],'env':{'RESEARCHOS_TASK_ID':'W09','RESEARCHOS_CHECK_ID':'','RESEARCHOS_CASE_ID':'C19','RESEARCHOS_RETRIEVAL_MODE':'fixture'},'actual_go_child_argv':native,'producer_native_runs':1,'expected_test_functions':2,'expected_native_ids':['C19-01','C19-02','C19-03','C19-04','C19-05'],'expected_formal_ids':['C19-01','C19-02','C19-03']},
 'launch_preconditions':['Six source paths must exist at their intended relative locations; proposed receipt files cannot run in place because ROOT uses parents[2] and sibling module imports','Freeze full current Go package/dependency/SQLite source inputs and bounded compiler/process cleanup resources; Go/Python binaries hash-match but no build closure verified here','Existing retrieval producer has PATH git observations and plain subprocess subprocess.Popen timeout cleanup; Root must bind permitted tool provenance and process ownership in the current execution capsule before running','Package build may include unrelated current tests; scope drift or first unexpected result stops, no automatic retries; preserve origin counters','The minimum proposal cannot use or amend existing 49-case grants implicitly; obtain the actual narrow current Root registration required by its execution contract'],
 'producer_outputs':['Original report.json, native-tool-run.json, raw go stdout/stderr, exact owned manifest','27 graph records: two independent observed roots + four derived reposts + one unknown +20 SIMULATED','Twenty original simulation bodies and twenty ordinal/Artifact/Evidence/hash binding events','Original content/artifact/evidence HTTP request-response bytes, root/file snapshots, before/after origin rows and live invalidation facts'],
 'review_sequence':['Seal native producer report/raw first','Different nonauthor reviews this exact run, source/tool/OS and owned bytes in a separate receipt namespace','Create two route-specific FIXTURE mode decisions referencing that independent review and same native report; decisions cannot be pre-forged or introduce a report hash cycle','Root/W02 binds exact v2.4 C19 consumers while retaining W08/W17/W09-01 existing branches','Run both readonly formal commands with native report/tool-run/mode-decision refs and hashes; consumers must not re-execute native producer','Independent acceptance issuer signs only C19 if its actual full assertions pass; do not accept W09 parent/G01/G02/A06'],
 'formal_commands_after_binding':[[python,'execution/command_dispatcher/dispatch.py',key,'--task-id','W09','--case-id','C19','--spec','v2.4'] for key in ['test.research.fixture','test.retrieval']],
 'consumer_required_environment':['RESEARCHOS_W09_NATIVE_REPORT_REF','RESEARCHOS_W09_NATIVE_REPORT_SHA256','RESEARCHOS_W09_TOOL_RUN_REF','RESEARCHOS_W09_TOOL_RUN_SHA256','RESEARCHOS_W09_MODE_DECISION_REF','RESEARCHOS_W09_MODE_DECISION_SHA256'],
 'completion':'A current immutable C19 producer packet and two actual exact-route FIXTURE consumer receipts, independently accepted; if run/route/resource fails, retain specific NOT_RUN/BLOCKED/PARTIAL with originals. This review does not issue that acceptance.',
 'remaining_parent_work':['W09-G01 must additionally cover A06 fixture components','W09-G02 requires real local Windows update/delete/escape/fallback and current host/junction witnesses','A06 requires full own formal assertion set and producer joins including ContextBundle/materialization','Hardlink policy, constant-index sensitivity, client projection/answer-support limits remain explicit','C02 final owner remains W17','All 42 mandatory cases remain intact with their frozen modes; no W05 resource requirement is imported into C19']}
write('next-task.json',proposal)
report='''W09 可以独立推进；最小可执行目标是 C19 的 FIXTURE 生产证据和双入口只读验收。当前可立即派发的是六源码的受控候选组合与有限执行准备，尚不能直接签收或启动旧包中的 producer。

合同与当前状态
W09-99 依赖 W09-01、W09-02、W03-99、W07-99；CP364 对应 step_state 四项均 ACCEPTED，未列 W09-99 因而沿合同默认 NOT_STARTED。W05-99 不是其依赖。W09 checklist 要求来源分类/有效性传播、项目与真实路径权限、缓存身份和 fallback，以及删除/撤回/同名/转载反例。W09-G01 为 FIXTURE，W09-G02 为 LIVE_WINDOWS；C19 与 A06 的最终 owner 是 W09 且合同均 FIXTURE；C02 最终 owner 是 W17。

全部42用例的 mode/final_owner/关联WBS/assertionIDs保存在 all42-contract-map.json，保留全部最终门。W09-C19 无模型、SDK、外部服务、账单或 W05 backup/upgrade 前提。

当前可复用而未采用的事实
CP364 指向 exact4 causal Source 的 cd0d818b 提交及独立静态回执：四文件/41新scenario/8回归仍未编译执行，不能重复将其当未实现工作。v6 六源码已有 READY_SOURCE_PREPARATION_ONLY 独立评审，具体原始 SHA/bytes 均已短时 SourceReadGuard 复核和完整复制。v6 不等于采用，不等于真实报告；历史 I01 仍 OPEN，不能以新包补写历史原件。

当前 Main 中 export helper、formal router、evidence closure 三文件不存在；retrieval.py 仍为旧 76d4f8a9feec0645022b9a2aec36e415379551cec1a3d45725e7e2e9e0f1b9ea /9861 bytes。v6 domain_test.go 与当前 Main 唯一 diff 是 ServeHTTP 后追加 w09ExportHTTP，旧调用保留。六源码及目标路径在 source-composition-map.json。不能在 receipt 目录直接运行 proposed.py：ROOT 与 sibling imports 需要实际候选目录布局。

当前六条正式/父门 command 均在 v2.4 registry selector 处被静态判定拒绝，handler 不会被进入；没有试跑。test.retrieval 只服务 W09/W09-01；test.research.fixture 服务 W08 子卡；test.security 服务 W17/W17-01。精确矩阵保存在 six-route-static-matrix.json。绑定由 Root/W02 串行处理，W09-99 本卡 receipts-only scope 不能自行扩大成共享文件写权限。

建议下一任务
采用已审查的六个 v6 Source 到新的隔离候选；冻结当前完整 Go 输入与有限一次运行条件。C19 producer 选择 TestW09C19ExplicitOriginAndUnknown 与 TestW09C19ChainInvalidation；唯一 native child 命令及环境在 next-task.json。它使用新 TempDir、SQLite 与进程内 httptest recorder；实验为标准库 SHA-256 实测，不调用外部模型，不要求 symlink/junction/native link 探针。运行生成的五个 native IDs 不能冒充五项正式断言，正式 C19 恰为 C19-01/02/03。

先封一次原报告/原 stdout/stderr/tool-run/owned manifest，再由不同 actor 复核同一 run，之后为两条正式 route 各生成 mode decision。分别执行 test.research.fixture --task-id W09 --case-id C19 和 test.retrieval --task-id W09 --case-id C19；均使用 --spec v2.4，只读消费同一 producer 报告，不能为第二入口重跑 native。正式签署由独立 Verifier 完成。

资源与差距
已实测 locked Go 与 Python 二进制 SHA 一致，Go/Python 源入口、生产 evidence/retrieval 代码、go.mod/sum、迁移源码存在。未执行 Go/SQL/产品 handler/模型/API/native link，未确认依赖缓存完整性或编译闭合。现有 producer 中 PATH git 观察与普通 subprocess 生命周期必须由当前 Root 有限执行方案绑定，不能因源码静态通过直接启动。C19 真正缺的是 Source adoption/current input closure、一次原始 producer 证据、独立本run mode review、两条 registry binding 和独立正式签署；不缺外部业务资源。

C19 切片不接受 W09 父任务。G01/A06/G02 仍分别完成原范围；G02 的真实 Windows host/junction、更新删除路径/fallback另行冻结；hardlink 决策、index 单变量敏感性、客户端投影/answer support 等已披露限制保留。45资源无关/4OS的 causal controller 工作可以另推进，不能把其完整49项作为生成 C19 两测试原始证据的先决条件。

本次仅写自己的新只读审查目录。两条机械错误分别为 Root 分配的912（错误父目录AGENTS读取）与913（JS btoa 不存在，未到shell）；全部原失败保留且无计数重置。原始工具回应保存于 original-tool-observations.json；少数工具自身返回截断和前期未捕获回应明确披露，未伪造缺失IO。完整被读 Source 字节均在本目录快照并逐pin核验。正式通过增量0，Source采用0，产品执行0，Canonical写0。
'''
(O/'REPORT.md').write_text(report,encoding='utf-8')
write('review.json',{'schema':'researchos.w09-next-slice-independent-review.v1','reviewer':'codex:/root/native_temp_independent_review','decision':'C19_FIXTURE_INDEPENDENT_SLICE_IDENTIFIED','next_task_ref':pin(O/'next-task.json'),'report_ref':pin(O/'REPORT.md'),'dependency_states':deps,'six_current_routes_unbound':True,'source_files_reviewed':len(refs),'copy_count':len(copychecks),'actual_executions':{'product':0,'Go':0,'SQL':0,'Git':0,'MODEL':0,'native_link':0},'formal_acceptance_increment':0,'canonical_writes':0,'source_adoption':False,'new_failure_ordinals':[912,913],'failure_count_reset':False,'model_policy':'inherited model, no override or child agent launched','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in {'MF.json','HDF.json','postseal.json','postseal-tool-observation.json'}]
write('MF.json',{'schema':'researchos.readonly-review-manifest.v1','members':members,'excluded':['MF.json','HDF.json','postseal.json','postseal-tool-observation.json']})
write('HDF.json',{'schema':'researchos.w09-readonly-review-handoff.v1','author':'codex:/root/native_temp_independent_review','status':'STOPPED','decision':'C19_FIXTURE_MINIMAL_NEXT_SLICE','manifest_ref':pin(O/'MF.json'),'report_ref':pin(O/'REPORT.md'),'review_ref':pin(O/'review.json'),'next_task_ref':pin(O/'next-task.json'),'all42_map_ref':pin(O/'all42-contract-map.json'),'sources_ref':pin(O/'all-source-pins.json'),'fullIO_ref':pin(O/'original-tool-observations.json'),'failure_origins_ref':pin(O/'failure-origins.json'),'new_failure_ordinals':[912,913],'formal_acceptance_increment':0,'source_accepted':False,'source_adopted':False,'product_executed':False,'canonical_writes':0})
for name in ['HDF.json','MF.json','REPORT.md','next-task.json','original-tool-observations.json']: print(name,json.dumps(pin(O/name),ensure_ascii=False))
print('PIN_COUNT',len(refs),'COPIES',len(copychecks),'MEMBERS',len(members))

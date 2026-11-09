from pathlib import Path
import ast,copy,hashlib,json,re,types,uuid
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_main_root_producer_source_codex/mainc19p-1a11fbc'
O=Path(__file__).resolve().parent
ACTOR='codex:/root/native_temp_independent_review'
checks=[];controls=[]
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
    b=Path(r['path']).read_bytes();assert (hashlib.sha256(b).hexdigest(),len(b))==(r['sha256'],r['bytes']),r['path'];return b
def save(n,v):
    p=O/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def check(n,v,detail=None):
    assert v,n
    checks.append(dict(name=n,passed=True,detail=detail))
def capture(f):
    try:f()
    except BaseException as e:return dict(type=type(e).__name__,message=str(e))
    return dict(type=None,message=None)
hr=dict(path=str(N/'HDF.json'),sha256='2f8127a4bae45ac7c31c24f59a878c01c74549bc200a43162d16783618b1ea2f',bytes=13717)
h=json.loads(read(hr));mr=h['manifest_ref'];mf=json.loads(read(mr));C=json.loads(read(h['root_calling_contract_ref']));choice=json.loads(read(h['choice_ref']))
check('authoritative_MF_pin_from_verified_HDF',mr['sha256']=='270027d8caacac6ad5996d627d09549c05b9102ac5b7aa588d33cbea9347265d' and mr['bytes']==10819)
original=json.loads(read(h['source_input_pins_ref']))
check('original_pin_count',original['count']==len(original['refs'])==4000)
refs={}
for r in [hr,mr,*mf['members'],*original['refs']]:
    clean={k:r[k] for k in ('path','sha256','bytes')};key=clean['path'].casefold();assert key not in refs or refs[key]==clean;refs[key]=clean
check('no_current_Canon_or_seven_target_read_locks',not any(r['path'] in {str(R/'execution/v2.4'/n) for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']}|{r['path'] for r in choice['main_seven_after_refs']} for r in refs.values()))
gp=choice['guard_ref'];gm=types.ModuleType('independent_mainproducer_guard');gm.__file__=gp['path'];exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(refs.values()))
    check('finite_inputs_actually_held',all(guard.get_buffer(r['path'])==read(r) for r in refs.values()),len(refs))
    for r in mf['members']:check('member_'+Path(r['path']).name,Path(r['path']).parent==N)
    raw=read(h['runtime_ref']);tree=ast.parse(raw);stage=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='stage');block=next(x for x in stage.body if isinstance(x,ast.Try))
    names={'require','decode','raw_pin','read_ref','job_closed','build_environment','compiler_inventory','guard_cleanup_ok'}
    nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names]
    ns=dict(Path=Path,json=json,re=re,hashlib=hashlib,R=R,MAX=256*1024*1024)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<pure-producer-functions>','exec'),ns)
    for text in ['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}']:
        check('reject_ambiguous_JSON_'+text,capture(lambda:ns['decode'](text))['type']=='ValueError')
    check('ordinary_JSON_preserves_FILETIME',ns['decode']('{"t":134360040243008824}')['t']==134360040243008824)
    for bad in [{'path':'MEMORY','sha256':'0'*64,'bytes':True},{'path':'MEMORY','sha256':'0'*64,'bytes':0,'role':'extra'},{'path':'MEMORY','sha256':'short','bytes':0}]:
        check('reject_nonexact_ref_'+repr(bad),capture(lambda:ns['read_ref'](bad))['type']=='ValueError')
    launch=ast.parse(read(h['launcher_ref']));cls=next(x for x in launch.body if isinstance(x,ast.ClassDef));lns=dict(uuid=uuid);exec(compile(ast.Module(body=[cls],type_ignores=[]),'<UUID-private-object-only>','exec'),lns)
    original_uuid4=uuid.uuid4;provider=lns['OneShotEvidenceUUID'](choice['run_id']);value=provider.uuid4()
    check('UUID_exact_private_run',value.hex==choice['run_id'] and uuid.uuid4 is original_uuid4)
    check('UUID_second_call_rejected',capture(provider.uuid4)['type']=='ValueError')
    for attr in ['_value','_used','uuid1','__dict__']:check('UUID_other_attribute_rejected_'+attr,capture(lambda:getattr(provider,attr))['type']=='ValueError')
    env=ns['build_environment'](choice)
    check('private_environment_and_no_fetch',env['GOCACHE']==str(Path(choice['scratch_root'])/'gocache') and env['GOPROXY']==env['GOSUMDB']==env['GOWORK']=='off' and env['RESEARCHOS_CASE_ID']=='C19' and env['RESEARCHOS_TASK_ID']=='W09' and env['RESEARCHOS_CHECK_ID']=='')
    keys=['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']
    closed=dict(job_cleanup=dict(errors=[],active_processes_last_observed=0,**{k:True for k in keys}))
    check('complete_job_observation_accepted',ns['job_closed'](closed))
    for k in keys:
        bad=copy.deepcopy(closed);bad['job_cleanup'][k]=False;check('incomplete_job_rejected_'+k,not ns['job_closed'](bad))
    for value in [None,{},dict(job_cleanup={}),dict(job_cleanup=dict(closed['job_cleanup'],errors=['failure'])),dict(job_cleanup=dict(closed['job_cleanup'],active_processes_last_observed=1))]:check('bad_job_'+repr(value),not ns['job_closed'](value))
    # Compiler negative controls only. All paths/pins here are memory values.
    bp=json.loads(read(h['compiler_blueprint_ref']));cache=Path(choice['scratch_root'])/'gocache';fakepin=lambda p:dict(path=str(p),sha256='0'*64,bytes=1)
    ns.update(exact_path=lambda p:Path(p),pin=fakepin)
    cases=[('package_error',{'ImportPath':'x','Error':'FAIL'},'GO_LIST_PACKAGE_ERROR'),('old_cache_export',{'ImportPath':'x','Export':str(R/'.local/gocache/old-a')},'EXPORT_NOT_PRIVATE_GOCACHE'),('unheld_source',{'ImportPath':'x','Dir':str(R/'internal/domain'),'GoFiles':['UNREVIEWED.go']},'GO_LIST_UNHELD_OR_DRIFTED_INPUT'),('unheld_module',{'ImportPath':'x','Module':{'GoMod':str(R/'UNREVIEWED.mod')}},'MODULE_GOMOD_NOT_HELD')]
    for label,pkg,wanted in cases:
        result=capture(lambda:ns['compiler_inventory'](json.dumps(pkg),choice,bp));check('compiler_reject_'+label,result==dict(type='ValueError',message=wanted));controls.append(dict(kind='compiler_negative',case=label,result=result))
    check('blueprint_351_3905_19',bp['package_count']==len(bp['package_roster'])==351 and len(bp['stable_input_refs'])==3905 and len(bp['module_go_mod_refs'])==19)
    # Exact original finally with memory filesystem: independently reproduce
    # partial receipt JSON and pin/read failures before the cleanup loop.
    class P:
        def __init__(self,s,mode):self.s=s;self.mode=mode
        def __truediv__(self,x):return P(self.s+'/'+x,self.mode)
        def is_file(self):return self.s.endswith('.invocation.json')
        def is_dir(self):return True
        def read_bytes(self):
            if self.mode=='read_error':raise OSError('PURE_RECEIPT_READ_FAILURE')
            return b'{"result":'
        def __str__(self):return self.s
    for mode,wanted in [('partial_json','JSONDecodeError'),('pin_error','OSError'),('read_error','OSError')]:
        calls=[]
        class G:
            def close(self):calls.append('close');return dict(closed=True,errors=[],retained_handles_count=0)
        def fake_pin(p):
            if mode=='pin_error':raise OSError('PURE_RECEIPT_PIN_FAILURE')
            return fakepin(p)
        sc=dict(created=True,kind='run',stage_root=P('MEMORY',mode),output=P('MEMORY_OUTPUT',mode),pin=fake_pin,decode=json.loads,job_closed=ns['job_closed'],capture_packet=lambda *x:None,c={},guards=[('input',G()),('runtime',G()),('compiler-exports',G())],cleanups=[],save=lambda *x:None,guard_cleanup_ok=ns['guard_cleanup_ok'])
        result=capture(lambda:exec(compile(ast.Module(body=block.finalbody,type_ignores=[]),'<original-finally-no-native>','exec'),sc))
        check('confirmed_cleanup_bypass_'+mode,result['type']==wanted and not calls and not sc['cleanups'])
        controls.append(dict(kind='confirmed_P1_counterexample',case=mode,result=result,guard_close_calls=calls,cleanup_rows=sc['cleanups']))
    text=raw.decode();prep=next(x for x in block.body if isinstance(x,ast.If) and ast.unparse(x.test)=="kind == 'prepare'")
    check('prepare_branch_no_process_invocation',not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='invoke' for x in ast.walk(ast.Module(body=prep.body,type_ignores=[]))))
    check('two_outer_invocations_in_run_branch',sum(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='invoke' for x in ast.walk(ast.Module(body=prep.orelse,type_ignores=[])))==2)
    check('two_C19_parents_five_ids',choice['selected_tests']==['TestW09C19ChainInvalidation','TestW09C19ExplicitOriginAndUnknown'] and choice['expected_native_ids']==['C19-01','C19-02','C19-03','C19-04','C19-05'])
    check('one_shot_and_same_vector_source_gates',all(k in text for k in ['ONE_SHOT_OUTPUT_ALREADY_EXISTS','ONE_SHOT_PREPARATION_ALREADY_EXISTS','ONE_SHOT_PRODUCER_ALREADY_ATTEMPTED','SAME_PREPARE_VECTOR_REQUEST','FRESH_PRIVATE_GOCACHE']))
    check('authority_source_adoption_owner_bindings',all(k in text for k in ['SOURCE_REVIEW_FULL_BINDING_','ACTUAL_MAIN_SEVEN_ADOPTED','ADOPTION_REVIEW_BINDING','FOUR_ORDERED_CANONICAL','EXACT_REGISTERED_NATIVE_OWNER','EXACT_UNIQUE_NATIVE_WORKER','CURRENT_MAIN_ROSTER']))
    failure=json.loads(read(h['original_tool_failure_952_ref']));check('952_preserved_exit_categories',failure['root_assigned_ordinal']==952 and failure['outer_exit']==1 and all(failure[k] is None for k in ['SourcePython_exit','Go_exit','Native_exit','Model_exit']) and failure['complete_original_pair'] is True)
    check('all_finite_inputs_unchanged',all(read(r)==guard.get_buffer(r['path']) for r in refs.values()))
finally:
    cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
check('review_handles_closed',cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors'] and cleanup['verification']=='PASSED')
save('checks.json',dict(count=len(checks),checks=checks,author107_controls_rerun=False,meaning='Independent Source observations; expected negative controls include confirmed blocking defect'))
save('negative-controls.json',controls);save('verified-input-pins.json',list(refs.values()))
req=C['source_review_requirement'];decision=dict(schema=req['decision_schema'],decision='REQUEST_CHANGES',actor_role='INDEPENDENT_NON_AUTHOR',actor_id=ACTOR,source_handoff_ref=hr,source_manifest_ref=mr,calling_contract_ref=h['root_calling_contract_ref'],**C['bound_source_refs'],run_id=choice['run_id'],output_root=choice['output_root'],source21=choice['source21'],actual_executed=False,formal_case_accepted_delta=0,formal_acceptance=False,findings_ref=pin(O/'findings.json'),P1_findings=1,execution_grant=False,all_handles_closed=True,retained_handles_count=0,handle_scope='This independent Source review only; producer actual not executed',new_original_failures=[],original_failure_952_ref=h['original_tool_failure_952_ref'],reviewed_at=datetime.now(timezone.utc).isoformat())
save('source-decision.json',decision)
report='Main-root C19 producer 独立 Source 审查：REQUEST_CHANGES，1 个 P1。stage finally 在逐guard关闭前读取、pin并decode invocation回执；partial JSON或pin/read OSError都会跳过全部guard.close并覆盖原错误。三个原始finally AST负向控制独立确认，未执行actual prepare/run。修复应保障外层finally逐guard关闭，独立保留原阶段、回执检查、archive与cleanup错误，unknown Job closure不得报true。\n\n其余已核对固定Main root/三个输出目录、私有单次UUID对象不改stdlib、Source21/七目标/owner/vector绑定代码、prepare无进程、run两外层invoke与两父测试、私有GOCACHE/351包3905稳定输入19GoMod、FILETIME Python整数和原952退出类别；这些Source观察不是Actual资格。所有输入实际只读锁保持不变并全部关闭，未持锁Canon或Root七目标，未改Main/Canon/旧包，无新工具失败。必须由新Source修复并独审接受后才可Root执行；Formal增量0。\n'
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mref=save('MF.json',dict(schema='researchos.w09-main-c19-producer-independent-source-manifest.v1',members=members,source_handoff_ref=hr,source_manifest_ref=mr))
href=save('HDF.json',dict(schema='researchos.w09-main-c19-producer-independent-source-review.v1',actor_id=ACTOR,status='REQUEST_CHANGES',manifest_ref=mref,source_decision_ref=pin(O/'source-decision.json'),source_handoff_ref=hr,source_manifest_ref=mr,findings_ref=pin(O/'findings.json'),P1_findings=1,independent_checks=len(checks),held_inputs=len(refs),guard_cleanup_ref=pin(O/'source-guard.cleanup.actual.json'),all_handles_closed=True,retained_handles_count=0,actual_executed=False,Main_Canon_unchanged=True,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,execution_grant=False,new_original_failures=[],STOP=True,FINAL=True))
for r in members+[mref,href]:read(r)
print(json.dumps(dict(HDF=href,MF=mref,decision=pin(O/'source-decision.json'),findings=pin(O/'findings.json'),checks=len(checks),held_inputs=len(refs)),ensure_ascii=False))

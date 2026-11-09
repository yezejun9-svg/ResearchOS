from pathlib import Path
import ast,base64,copy,hashlib,json,re,types,uuid
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_main_root_producer_v2_source_codex/mainc19p2-1a11fe4'
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
def caught(f):
    try:f()
    except BaseException as e:return e
    return None
def boom(message):raise OSError(message)
hr=dict(path=str(N/'HDF.json'),sha256='8d3fe469f3797d0b7e72342e230696b99109359ed310a46cc191ce213a67d4ec',bytes=15498)
h=json.loads(read(hr));mr=h['manifest_ref'];mf=json.loads(read(mr));C=json.loads(read(h['root_calling_contract_ref']));choice=json.loads(read(h['choice_ref']))
check('exact_author_source_pair',mr['sha256']=='deb0d5eeb4a8d93d0749612bce001be5daa6a83c5e9d7a34c263682ad4f7fdf8' and mr['bytes']==9953)
check('exact_contract',h['root_calling_contract_ref']['sha256']=='5fbae9c15d6e4dd4b6df6bffbe98cd78bd731ce809b017eef4648a16fbd88e9e')
original=json.loads(read(h['source_input_pins_ref']));refs={}
check('4047_predecessor_inputs',original['count']==len(original['refs'])==4047)
for r in [hr,mr,*mf['members'],*original['refs']]:
    clean={k:r[k] for k in ('path','sha256','bytes')};key=clean['path'].casefold();assert key not in refs or refs[key]==clean;refs[key]=clean
forbidden={str(R/'execution/v2.4'/n) for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']}|{r['path'] for r in choice['main_seven_after_refs']}
check('no_Canon_or_Main7_lock',not any(r['path'] in forbidden for r in refs.values()))
gp=choice['guard_ref'];gm=types.ModuleType('independent_v2_guard');gm.__file__=gp['path'];exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(refs.values()))
    check('finite_inputs_actually_held',all(guard.get_buffer(r['path'])==read(r) for r in refs.values()),len(refs))
    for r in mf['members']:check('member_'+Path(r['path']).name,Path(r['path']).parent==N)
    prev=json.loads(read(h['predecessor_handoff_ref']));pc=json.loads(read(prev['choice_ref']))
    for key in ['main_seven_after_refs','source21','selected_tests','expected_native_ids','source_root']:
        check('unchanged_'+key,choice[key]==pc[key])
    check('fresh_run',choice['run_id']=='9e912dfc1058454da08ae7f93f4de24d' and choice['run_id']!=pc['run_id'])
    inv=json.loads(read(h['caller_complete_byte_inverse_ref']))
    for f in inv['files']:
        check('complete_inverse_'+f['relative'],base64.b64decode(f['whole_before_base64'])==read(f['original_ref']) and base64.b64decode(f['whole_after_base64'])==read(f['successor_ref']) and f['successor_path_was_absent'] is True and f['old_namespace_never_written'] is True)
    raw=read(h['runtime_ref']);tree=ast.parse(raw);oldtree=ast.parse(read(prev['runtime_ref']))
    defs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    olddefs,newdefs=defs(oldtree),defs(tree)
    changed={k for k in olddefs if olddefs[k]!=newdefs.get(k)}
    check('runtime_existing_changes_only_invoke_stage',changed=={'invoke','stage'},sorted(changed))
    check('runtime_new_helpers_finite',set(newdefs)-set(olddefs)=={'EvidenceFailure','evidence_error','observe_invocation','close_stage_resources'})
    ns=dict(__file__=h['runtime_ref']['path'],__name__='inert_review_runtime')
    exec(compile(raw,h['runtime_ref']['path'],'exec'),ns)
    purebase=dict(ns)
    keys=['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']
    closed=dict(job_cleanup=dict(errors=[],active_processes_last_observed=0,**{k:True for k in keys}),actual_exit=0,error=None,timed_out=False,creation_time_100ns=134360040243008824)
    goodraw=json.dumps(dict(result=closed)).encode()
    class MemoryPath:
        def __init__(self,s='MEMORY',mode='good'):self.s=s;self.mode=mode
        def __truediv__(self,x):return MemoryPath(self.s+'/'+x,self.mode)
        def __str__(self):return self.s
        def is_file(self):
            if self.mode=='presence':boom('PURE_PRESENCE')
            return self.mode!='missing'
        def is_dir(self):return True
        def read_bytes(self):
            if self.mode=='read':boom('PURE_READ')
            if self.mode=='partial':return b'{"result":'
            if self.mode=='nonobject':return b'[]'
            if self.mode=='unknown':return b'{}'
            return goodraw
        def open(self,*a,**k):return self
        def __enter__(self):return self
        def __exit__(self,*a):return False
    def fakepin(p):
        if p.mode=='pin':boom('PURE_PIN')
        r=ns['raw_pin'](p,goodraw)
        if p.mode=='drift':r['sha256']='0'*64
        return r
    phases={'partial':'invocation-decode','pin':'invocation-pin','read':'invocation-read','presence':'invocation-presence','missing':'invocation-missing','nonobject':'invocation-decode','drift':'invocation-closure'}
    for mode in ['good',*phases,'unknown','archive','close','close_observation','cleanup_save','inspect']:
        calls=[]
        class G:
            def __init__(self,label):self.label=label
            def close(self):
                calls.append(self.label)
                if mode=='close' and self.label=='runtime':boom('PURE_CLOSE')
                if mode=='close_observation' and self.label=='runtime':return {}
                return dict(closed=True,errors=[],retained_handles_count=0)
        ns.update(pin=fakepin,save=lambda *a:boom('PURE_CLEANUP_SAVE') if mode=='cleanup_save' else {'saved':True},capture_packet=lambda *a:boom('PURE_ARCHIVE') if mode=='archive' else {'packet':True})
        if mode=='inspect':ns['observe_invocation']=lambda *a:boom('PURE_INSPECT')
        else:ns['observe_invocation']=purebase['observe_invocation']
        root=MemoryPath(mode=mode)
        result=ns['close_stage_resources']('run',True,{},root,root,[(x,G(x)) for x in ['input','runtime','compiler']])
        check('all_guard_close_attempts_'+mode,calls==['compiler','runtime','input'])
        check('honest_guard_closure_'+mode,result['all_guards_closed']==(mode not in ['close','close_observation']))
        if mode in phases:check('classified_'+mode,phases[mode] in {x['phase'] for x in result['errors']})
        if mode in [*phases,'unknown','inspect']:check('unknown_jobs_not_closed_'+mode,result['all_owned_jobs_closed'] is False and result['packet_ref'] is None)
        if mode in ['archive','close','close_observation','cleanup_save','inspect']:
            expected={'archive':'packet-archive','close':'guard-close','close_observation':'guard-close-observation','cleanup_save':'guard-cleanup-save','inspect':'invocation-inspection'}[mode]
            check('classified_'+mode,expected in {x['phase'] for x in result['errors']})
        if mode=='cleanup_save':check('save_failure_not_close_failure',result['all_guards_closed'] and not result['all_cleanup_receipts_saved'])
        controls.append(dict(group='outer_finally',mode=mode,close_order=calls,result=result))
    ns['observe_invocation']=purebase['observe_invocation']
    for mode in ['good','primary','pin','save','progress','all']:
        primary=OSError('PURE_HELPER_ORIGINAL')
        helper=types.SimpleNamespace(run_owned=lambda *a,**k:(_ for _ in ()).throw(primary) if mode in ['primary','all'] else copy.deepcopy(closed))
        ns.update(pin=lambda p:boom('PURE_STREAM_PIN') if mode in ['pin','all'] else {'stream':str(p)},save=lambda *a:boom('PURE_INVOKE_SAVE') if mode in ['save','all'] else {'receipt':True},print=lambda *a,**k:boom('PURE_PROGRESS') if mode in ['progress','all'] else None)
        if mode=='good':
            receipt,result=ns['invoke'](helper,MemoryPath(),'unit',[],{},1);check('invoke_positive_lossless_FILETIME',result['creation_time_100ns']==134360040243008824)
        else:
            e=caught(lambda:ns['invoke'](helper,MemoryPath(),'unit',[],{},1))
            check('invoke_evidence_failure_'+mode,isinstance(e,ns['EvidenceFailure']))
            check('invoke_primary_identity_'+mode,e.primary_exception is (primary if mode in ['primary','all'] else None))
            if mode in ['primary','all']:check('invoke_chained_original_'+mode,e.__cause__ is primary)
            expected={'pin':{'invocation-stream-pin'},'save':{'invocation-receipt-save'},'progress':{'invocation-progress-write'},'all':{'invocation-stream-pin','invocation-receipt-save','invocation-progress-write'},'primary':set()}[mode]
            check('invoke_error_phases_'+mode,{x['phase'] for x in e.secondary_errors}==expected)
            controls.append(dict(group='invoke',mode=mode,original_error=repr(e.primary_exception),secondary=e.secondary_errors,diagnostics=e.diagnostics))
    # Execute only exact AST tails with in-memory dependencies; never actual entrypoints.
    stage=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='stage')
    block=next(n for n in stage.body if isinstance(n,ast.Try));start=stage.body.index(block)
    stage_tail=stage.body[start+1:]
    for kind in ['prepare','run']:
        for mode in ['good','save','progress','both','prior_primary','predirectory']:
            primary=OSError('PURE_STAGE_ORIGINAL') if mode in ['prior_primary','predirectory'] else None
            close_result=dict(guard_cleanups=[dict(ref={'guard':True})],errors=[],packet_ref={'packet':True},invocations=[dict(ref={'invocation':1}),dict(ref={'invocation':2})],all_guards_closed=True,all_cleanup_receipts_saved=True,all_owned_jobs_closed=True)
            sc=dict(ns,closed=close_result,primary=primary,error=repr(primary) if primary else None,success=primary is None,kind=kind,summary={},request_ref={},created=mode!='predirectory',stage_root=MemoryPath(),actual=MemoryPath(),save=lambda *a:boom('PURE_STAGE_SAVE') if mode in ['save','both','prior_primary'] else {},print=lambda *a,**k:boom('PURE_STAGE_PROGRESS') if mode in ['progress','both','prior_primary'] else None)
            e=caught(lambda:exec(compile(ast.Module(body=stage_tail,type_ignores=[]),'<exact-stage-tail>','exec'),sc))
            check('stage_tail_'+kind+'_'+mode,(e is None) if mode=='good' else isinstance(e,ns['EvidenceFailure']))
            if e:
                check('stage_primary_'+kind+'_'+mode,e.primary_exception is primary and e.__cause__ is primary)
                wanted=set()
                if mode in ['save','both','prior_primary']:wanted.add('stage-result-save')
                if mode in ['progress','both','prior_primary']:wanted.add('stage-progress-write')
                check('stage_phases_'+kind+'_'+mode,{x['phase'] for x in e.secondary_errors}==wanted)
                controls.append(dict(group='stage_tail',kind=kind,mode=mode,primary=repr(primary),secondary=e.secondary_errors))
    launch=ast.parse(read(h['launcher_ref']));lm=next(n for n in launch.body if isinstance(n,ast.FunctionDef) and n.name=='main');lb=next(n for n in lm.body if isinstance(n,ast.Try));lt=lm.body[lm.body.index(lb)+1:-1]
    provider=types.SimpleNamespace(_used=True)
    for mode in ['good','primary','pin','save','all']:
        primary=OSError('PURE_LAUNCHER_ORIGINAL') if mode in ['primary','all'] else None
        original_uuid=object();runner=types.SimpleNamespace(uuid=provider)
        m=types.SimpleNamespace(require=ns['require'],EvidenceFailure=ns['EvidenceFailure'],evidence_error=ns['evidence_error'],pin=lambda *a:boom('PURE_LAUNCHER_PIN') if mode in ['pin','all'] else {},save=lambda *a:boom('PURE_LAUNCHER_SAVE') if mode in ['save','all'] else {})
        sc=dict(m=m,runner=runner,original_uuid=original_uuid,uuid=uuid,stdlib_uuid4=uuid.uuid4,provider=provider,returned=None,error=repr(primary) if primary else None,primary=primary,cleanup_errors=[],permit_ref={},runner_ref={},root=MemoryPath(),__file__='MEMORY')
        e=caught(lambda:exec(compile(ast.Module(body=lb.finalbody+lt,type_ignores=[]),'<exact-launcher-finally>','exec'),sc))
        check('launcher_restored_'+mode,runner.uuid is original_uuid)
        check('launcher_tail_'+mode,e is None if mode=='good' else isinstance(e,ns['EvidenceFailure']))
        if e:
            check('launcher_original_'+mode,e.primary_exception is primary and e.__cause__ is primary)
            wanted=set()
            if mode in ['pin','all']:wanted.add('launcher-source-pin')
            if mode in ['save','all']:wanted.add('launcher-closed-save')
            check('launcher_phases_'+mode,{x['phase'] for x in e.secondary_errors}==wanted)
            controls.append(dict(group='launcher_tail',mode=mode,primary=repr(primary),secondary=e.secondary_errors))
    for r in h['guard_cleanup_refs']:
        d=json.loads(read(r));check('author_guard_'+Path(r['path']).name,d['closed'] is True and d['retained_handles_count']==0 and not d['errors'])
    check('113_author_controls_are_source_only',h['new_source_controls']==113 and h['actual_executed'] is False and h['execution_grant'] is False)
    check('all_inputs_unchanged',all(read(r)==guard.get_buffer(r['path']) for r in refs.values()))
finally:
    cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
check('review_guard_actually_closed',cleanup['closed'] is True and cleanup['retained_handles_count']==0 and not cleanup['errors'] and cleanup['verification']=='PASSED')
save('checks.json',dict(count=len(checks),checks=checks,author_controls_rerun=False,actual_entrypoints_executed=False))
save('fault-injection-controls.json',controls);save('verified-input-pins.json',list(refs.values()))
save('findings.json',dict(findings=[],blocking_findings=0,fixed_predecessor_finding='MAIN-C19-PRODUCER-01',scope='Independent Source only; actual entrypoints not executed'))
req=C['source_review_requirement'];decision=dict(schema=req['decision_schema'],decision=req['decision'],actor_role='INDEPENDENT_NON_AUTHOR',actor_id=ACTOR,source_handoff_ref=hr,source_manifest_ref=mr,calling_contract_ref=h['root_calling_contract_ref'],**C['bound_source_refs'],run_id=choice['run_id'],output_root=choice['output_root'],source21=choice['source21'],actual_executed=False,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,execution_grant=False,all_handles_closed=True,retained_handles_count=0,handle_scope='This independent Source review only',findings_ref=pin(O/'findings.json'),predecessor_review_handoff_ref=h['REQUEST_CHANGES_handoff_ref'],predecessor_review_manifest_ref=h['REQUEST_CHANGES_manifest_ref'],inherited_unchanged_reviews='v1 independently verified unchanged authority/compiler/environment/UUID boundaries, directly checked v2 AST differences and byte inverse',original_failure_954_ref=pin(O/'failure954.original-tool-io.json'),reviewed_at=datetime.now(timezone.utc).isoformat())
check('decision_all_contract_fields',set(req['decision_fields'])<=set(decision))
save('source-decision.json',decision)
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write('v2 独立 Source 审查接受。原 MAIN-C19-PRODUCER-01 已关闭：原始运行时 AST 的 partial JSON、pin/read、presence、archive、guard close/observation/save、invoke pin/save/progress、stage result/progress、launcher pin/closed-save 故障注入均验证按 phase 保留错误，主异常对象及 cause 保留，所有 guard 尝试关闭，未知 Job 不报 closed。完整逆向字节、4047 原输入和 v2 manifest 核验通过；v1 已验证且 v2 AST 不变的 authority/compiler/UUID 边界沿用。没有运行 Actual/Go/Git/SQL/model，没有锁定或写入 Main7/Canon。Source 接受不授予执行权限，仍需 Root 新 owner/vector/request 及后续 Actual 独审。只读错误954完整保留。\n')
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mref=save('MF.json',dict(schema='researchos.w09-main-c19-producer-independent-source-manifest.v1',members=members,source_handoff_ref=hr,source_manifest_ref=mr))
href=save('HDF.json',dict(schema='researchos.w09-main-c19-producer-independent-source-review.v1',actor_id=ACTOR,status=req['decision'],manifest_ref=mref,source_decision_ref=pin(O/'source-decision.json'),source_handoff_ref=hr,source_manifest_ref=mr,findings_ref=pin(O/'findings.json'),P1_findings=0,independent_checks=len(checks),held_inputs=len(refs),guard_cleanup_ref=pin(O/'source-guard.cleanup.actual.json'),all_handles_closed=True,retained_handles_count=0,actual_executed=False,Main_Canon_unchanged=True,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,execution_grant=False,new_original_failures=[954],original_failure_954_ref=pin(O/'failure954.original-tool-io.json'),root_next_live=955,STOP=True,FINAL=True))
for r in members+[mref,href]:read(r)
print(json.dumps(dict(HDF=href,MF=mref,decision=pin(O/'source-decision.json'),checks=len(checks),held_inputs=len(refs)),ensure_ascii=False))

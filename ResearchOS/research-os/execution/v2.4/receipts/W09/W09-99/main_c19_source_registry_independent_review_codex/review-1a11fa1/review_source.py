from pathlib import Path
import ast,base64,copy,hashlib,json,types
from datetime import datetime,timezone

R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W09/W09-99/main_c19_source_registry_integration_codex/mainc19-1a11f84'
O=Path(__file__).resolve().parent
ACTOR='codex:/root/native_temp_independent_review'
checks=[]
def pin(p):
    b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
    b=Path(r['path']).read_bytes();assert (hashlib.sha256(b).hexdigest(),len(b))==(r['sha256'],r['bytes']),r['path'];return b
def check(name,value,detail=None):
    assert value,name
    checks.append(dict(name=name,passed=True,detail=detail))
def save(name,value):
    p=O/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
hr=dict(path=str(N/'HDF.json'),sha256='ba6898a98c3bbd62eb8447938122ace9f95b6baad73b0cff9d1ebe597ed590eb',bytes=7346)
mr=dict(path=str(N/'MF.json'),sha256='1087530d763b1f601509d568957d59a820ad6f385d01fef4d724da00caead004',bytes=6382)
h=json.loads(read(hr));m=json.loads(read(mr));check('source_handoff_manifest_pair',h['manifest_ref']==mr)
members=[{k:r[k] for k in ('path','sha256','bytes')} for r in m['members']]
for r in members:read(r);check('source_manifest_member_'+Path(r['path']).name,Path(r['path']).parent==N)
change=json.loads(read(h['change_set_ref']));contract=json.loads(read(h['root_calling_contract_ref']))
original=json.loads(read(h['source_input_pins_ref']))['refs']
allrefs={r['path'].casefold():r for r in [hr,mr,*members,*original]}
guardref=change['guard_ref'];read(guardref)
allrefs[guardref['path'].casefold()]=guardref
gm=types.ModuleType('independent_source_guard');gm.__file__=guardref['path'];exec(compile(read(guardref),guardref['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(allrefs.values()))
    for r in allrefs.values():check('held_input_'+r['path'],guard.get_buffer(r['path'])==read(r))
    source=guard.get_buffer(h['caller_ref']['path']);tree=ast.parse(source)
    # Execute only declarations and pure validation/transaction functions; omit
    # every Windows adoption class, save(), main(), and top-level main call.
    names={'require','digest','exact_path','raw_pin','read_ref','pin','manifest_refs','validate_change_set','validate_scope','transaction'}
    declarations=[x for x in tree.body if isinstance(x,(ast.Import,ast.ImportFrom,ast.Assign)) or isinstance(x,ast.FunctionDef) and x.name in names]
    ns={'__name__':'independent_pure_extraction','__file__':h['caller_ref']['path']}
    exec(compile(ast.Module(body=declarations,type_ignores=[]),'<pure-source-functions>','exec'),ns)
    check('no_windows_adoption_callable',not any(k in ns for k in ('OwnedSeven','main','save')))
    before,after,refs=ns['validate_change_set'](change)
    check('seven_ordered_targets',contract['exact_targets']==[str(p) for p in ns['TARGETS']])
    check('no_adoption_read_guard_write_conflict',not any(Path(r['path']) in ns['TARGETS'] for r in refs+members+[hr,mr]))
    for i,row in enumerate(change['targets']):
        p=Path(row['target'])
        check('current_before_target_'+str(i),not p.exists() if before[i] is None else p.read_bytes()==before[i])
        if i<6:check('source21_six_mapping_'+str(i),row['after_source_ref']['sha256']!=row['before_ref']['sha256'] if row['before_ref'] else True)
    inv=json.loads(read(h['registry_full_byte_inverse_ref']));old=base64.b64decode(inv['whole_original_base64']);new=base64.b64decode(inv['whole_proposed_base64'])
    check('inverse_complete_original',old==before[6]);check('inverse_complete_proposed',new==after[6])
    rebuilt=old.decode()
    for s in sorted(inv['spans'],key=lambda s:s['start'],reverse=True):
        check('inverse_exact_before_span_'+s['command'],old.decode()[s['start']:s['end']]==s['before'])
        rebuilt=rebuilt[:s['start']]+s['after']+rebuilt[s['end']:]
    check('two_spans_rebuild_complete_proposed',rebuilt.encode()==new and len(inv['spans'])==2)
    oldj=json.loads(old);newj=json.loads(new);changed=[k for k in oldj['commands'] if oldj['commands'][k]!=newj['commands'][k]]
    check('only_two_registry_entries',set(changed)=={'test.research.fixture','test.retrieval'} and set(oldj['commands'])==set(newj['commands']))
    check('registry_other_fields_preserved',{k:v for k,v in oldj.items() if k!='commands'}=={k:v for k,v in newj.items() if k!='commands'})
    env={f'RESEARCHOS_W09_{x}_{suffix}' for x in ['NATIVE_REPORT','TOOL_RUN','MODE_DECISION'] for suffix in ['REF','SHA256']}
    for k in changed:
        a=oldj['commands'][k];b=newj['commands'][k]
        check('registry_environment_'+k,set(b['allowed_env'])-set(a['allowed_env'])==env and b['required_env']==a['required_env'] and b['fixed_env']==a['fixed_env'])
        check('registry_router_no_I_'+k,b['argv']==['-B','-X','utf8','ops/ci/w09_formal_router.py',k] and b['executable_tool']=='python')
        check('prior_selectors_retained_'+k,all(set(v)<=set(b['selectors'][s]) for s,v in a['selectors'].items()) and b['selectors']['case_id']==['C19'])
    # Memory-only ownership adapter. No actual target opens/writes/deletes.
    class Memory:
        def __init__(self,phase=None,index=None):
            self.data={i:v for i,v in enumerate(before) if v is not None};self.handles={};self.created=[];self.delete_marked=[];self.phase=phase;self.index=index;self.fired=False;self.writes=[]
        def open(self,i,new):
            if self.phase=='open' and self.index==i:raise OSError('IN_MEMORY_OPEN_REJECTION')
            if new:
                if i in self.data:raise FileExistsError('IN_MEMORY_FOREIGN_EXISTS')
                self.created.append(i);self.data[i]=b''
            self.handles[i]=i+1
            if self.phase=='postcreate' and self.index==i:raise OSError('IN_MEMORY_FINAL_PATH_REJECTION')
        def read_raw(self,i):return self.data[i]
        def write_raw(self,i,raw):
            self.writes.append(i)
            if raw==after[i]:assert len(self.handles)==7
            if self.phase=='write' and self.index==i and not self.fired:
                self.fired=True;self.data[i]=raw[:17];raise OSError('IN_MEMORY_PARTIAL_WRITE')
            self.data[i]=raw
        def delete_created(self,i):
            assert i in self.created and i in ns['NEW'];self.delete_marked.append(i)
        def finish(self):
            for i in self.delete_marked:self.data.pop(i,None)
            self.handles.clear()
    base={i:v for i,v in enumerate(before) if v is not None}
    def run_memory(phase=None,index=None,drift=None):
        obj=Memory(phase,index);records=[]
        if drift is not None:obj.data[drift]=b'FOREIGN_CURRENT_BYTES'
        starting=dict(obj.data)
        def record(name,value):
            records.append(name)
            if phase=='commit' and name=='committed.json':raise OSError('IN_MEMORY_COMMIT_JOURNAL_FAILURE')
        result=ns['transaction'](obj,before,after,record);obj.finish()
        should_succeed=phase is None and drift is None
        check('pure_transaction_'+str((phase,index,drift)),(result['status']=='SEVEN_SOURCE_TARGETS_COMMITTED' and obj.data==dict(enumerate(after))) if should_succeed else result['status']=='FAILED_ROLLED_BACK' and obj.data==starting)
        if drift is not None:check('foreign_CAS_not_overwritten_'+str(drift),not obj.writes)
    run_memory()
    for phase,indices in [('open',range(7)),('write',range(7)),('postcreate',ns['NEW'])]:
        for i in indices:run_memory(phase,i)
    run_memory('commit')
    for i in ns['EXISTING']:run_memory(drift=i)
    # Future scope fixtures exist only in memory. They are not Canon, Root
    # requests, runtime approval or an executed adoption.
    virtual={}
    def vr(name,d):
        raw=json.dumps(d,sort_keys=True).encode();r=ns['raw_pin'](O/'SYNTHETIC_NEVER_CREATED'/name,raw);virtual[r['path']]=raw;return r
    real_read=ns['read_ref']
    def synthetic_read(r):
        if r['path'] in virtual:
            raw=virtual[r['path']];ns['require'](ns['raw_pin'](Path(r['path']),raw)==r,'SYNTHETIC_TYPED_PIN');return raw
        return real_read(r)
    ns['read_ref']=synthetic_read
    d=dict(schema=contract['source_review_decision_schema'],decision=contract['source_review_decision_value'],actor_role='INDEPENDENT_NON_AUTHOR',actor_id=ACTOR,source_handoff_ref=hr,source_manifest_ref=mr,caller_ref=h['caller_ref'],change_set_ref=h['change_set_ref'],exact_targets=contract['exact_targets'],formal_case_accepted_delta=0,actual_adoption_executed=False)
    dr=vr('decision.json',d);reviewmf=vr('MF.json',dict(members=[dr]));reviewhf=vr('HDF.json',dict(actor_id=ACTOR,source_decision_ref=dr,manifest_ref=reviewmf))
    scope=dict(schema=contract['root_scope_schema'],status=contract['root_scope_status'],issued_by='codex:/root',executor='codex:/root',caller_ref=h['caller_ref'],change_set_ref=h['change_set_ref'],source_handoff_ref=hr,source_manifest_ref=mr,exact_targets=contract['exact_targets'],journal_root=contract['runtime_journal_root'],formal_case_accepted_delta=0,consumer_closed_ref=change['original_consumer_closed_ref'],source_review_handoff_ref=reviewhf,source_review_manifest_ref=reviewmf,source_review_decision_ref=dr,component_review_handoff_ref=change['component_actual_review_handoff_ref'],component_review_manifest_ref=change['component_actual_review_manifest_ref'])
    for k in ['formal_dispatcher','formal_acceptance','producer_rerun','copy_native_packet','new_Go_SQL_API_model_calls','checkpoint_write','ownership_write','step_state_write']:scope[k]=False
    sr=vr('scope.json',scope)
    owner=dict(owner='codex:/root',current_source_writer=None,scope_ref=sr,exact_targets=scope['exact_targets'],state='ROOT_REGISTERED_PENDING_SOURCE_ADOPTION',source_handoff_ref=hr,source_manifest_ref=mr,source_review_handoff_ref=reviewhf,source_review_manifest_ref=reviewmf,component_review_handoff_ref=scope['component_review_handoff_ref'],component_review_manifest_ref=scope['component_review_manifest_ref'],journal_root=scope['journal_root'],formal_case_accepted_delta=0,formal_dispatcher=False,parent_acceptance=False)
    worker=dict(step_id='W09-99',slice_id='C19_MAIN_SOURCE_REGISTRY_ADOPTION',owner='codex:/root',state=owner['state'],scope_ref=sr,exact_targets=scope['exact_targets'],source_review_handoff_ref=reviewhf,component_review_handoff_ref=scope['component_review_handoff_ref'])
    cp=dict(revision=400,project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',workers=[worker]);ow=dict(revision=200,shared_integrator='qoder-desktop:/root/platform_owner',active_integrator=dict(id='codex:/root'),card_path_bindings={'W09-99':dict(owner='codex:/root',subtasks=dict(c19_main_source_registry_adoption=owner))})
    def cr(i,doc):
        raw=json.dumps(doc,sort_keys=True).encode();p=ns['CANON'][i];r=ns['raw_pin'](p,raw);virtual[str(p)]=raw;return r
    vec=dict(schema=contract['vector_schema'],checkpoint_revision=400,ownership_revision=200,refs=[cr(0,cp),cr(1,ow),cr(2,{}),change['targets'][6]['before_ref']]);vref=vr('vector.json',vec)
    def gate(sc=scope,v=vref):return ns['validate_scope'](sc,sr,change,h['change_set_ref'],h['caller_ref'],hr,mr,[hr,mr,*members],v)
    got,_=gate();check('pure_future_scope_positive',not any(Path(r['path'])==ns['TARGETS'][6] for r in got))
    mutations=[('executor','not-root'),('exact_targets',scope['exact_targets'][:-1]),('journal_root',str(O)),('source_handoff_ref',mr),('source_manifest_ref',hr),('caller_ref',h['change_set_ref']),('source_review_decision_ref',h['caller_ref']),('formal_dispatcher',True),('formal_acceptance',True),('checkpoint_write',True),('copy_native_packet',True),('component_review_handoff_ref',reviewhf),('canonical_vector_ref',vref)]
    for key,value in mutations:
        changed_scope=copy.deepcopy(scope);changed_scope[key]=value
        try:gate(changed_scope)
        except (ValueError,KeyError):check('scope_reject_'+key,True)
        else:check('scope_reject_'+key,False)
    for key,value in [('checkpoint_revision',366),('ownership_revision',170),('checkpoint_revision',True),('refs',list(reversed(vec['refs'])))]:
        bad=copy.deepcopy(vec);bad[key]=value
        try:gate(v=vr('badvector.json',bad))
        except (ValueError,KeyError):check('vector_reject_'+key+'_'+str(value)[:20],True)
        else:check('vector_reject_'+key,False)
    for key,value in [('actor_id','codex:/root'),('actor_id','codex:/root/command_queue_impl'),('change_set_ref',hr),('actual_adoption_executed',True),('formal_case_accepted_delta',1)]:
        bad=copy.deepcopy(d);bad[key]=value;br=vr('baddecision.json',bad);bm=vr('badMF.json',dict(members=[br]));bh=vr('badHDF.json',dict(actor_id=bad['actor_id'],source_decision_ref=br,manifest_ref=bm));sc=copy.deepcopy(scope);sc.update(source_review_decision_ref=br,source_review_manifest_ref=bm,source_review_handoff_ref=bh)
        try:gate(sc)
        except (ValueError,KeyError):check('review_reject_'+key+'_'+str(value)[:30],True)
        else:check('review_reject_'+key,False)
    ns['read_ref']=real_read
    # The reviewed SourceReadGuard catches ordinary CloseHandle OSError per
    # handle and continues; main closes write ownership before the read guard.
    gtree=ast.parse(read(guardref));gclass=next(x for x in gtree.body if isinstance(x,ast.ClassDef) and x.name=='SourceReadGuard');close=next(x for x in gclass.body if isinstance(x,ast.FunctionDef) and x.name=='close')
    cns={};exec(compile(ast.Module(body=[close],type_ignores=[]),'<guard-close-only>','exec'),cns)
    class BadAPI:
        def __init__(self):self.calls=[]
        def close(self,h):
            self.calls.append(h)
            if h==1:raise OSError(6,'SYNTHETIC_CLOSE_FAILURE')
    api=BadAPI();fake=types.SimpleNamespace(_api=api,_entries=[dict(path='synthetic-'+str(i),sha256='0'*64,bytes=0,handle=i,closed=False,verified=True,final_path_match=True) for i in [1,2]],_errors=[],buffers={},_failure=None,_attempted=True)
    obs=cns['close'](fake);check('guard_close_error_does_not_skip_later_handles',api.calls==[1,2] and obs['retained_handles_count']==1 and len(obs['errors'])==1 and obs['closed'] is False)
    text=source.decode();check('owned_cleanup_precedes_guard_cleanup',text.index('owned_cleanup=owned.close()')<text.index('guard_cleanup=guard.close()'))
    check('crash_limit_honest',contract['crash_atomic'] is False and h['process_loss_requires_Root_reconciliation'] is True)
    for r in allrefs.values():check('unchanged_input_'+r['path'],read(r)==guard.get_buffer(r['path']))
finally:
    cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
check('all_actual_review_handles_closed',cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0 and cleanup['verification']=='PASSED')
save('verified-input-pins.json',list(allrefs.values()))
save('checks.json',dict(checks=checks,failed_checks=0,count=len(checks),native_adoption_executed=False,pure_controls_only=True))
decision=dict(schema=contract['source_review_decision_schema'],decision=contract['source_review_decision_value'],actor_role='INDEPENDENT_NON_AUTHOR',actor_id=ACTOR,source_handoff_ref=hr,source_manifest_ref=mr,caller_ref=h['caller_ref'],change_set_ref=h['change_set_ref'],exact_targets=contract['exact_targets'],formal_case_accepted_delta=0,actual_adoption_executed=False,formal_acceptance=False,formal_dispatcher_executed=False,new_execution_grant=False,reviewed_at=datetime.now(timezone.utc).isoformat(),findings=[],checks_ref=pin(O/'checks.json'),actual_guard_cleanup_ref=pin(O/'source-guard.cleanup.actual.json'),source_author=False,prior_component_review_author=True,process_loss_requires_Root_reconciliation=True)
save('source-decision.json',decision)
report='独立 Source 审查通过。七个固定目标、Source21 来源、仅两条 commands entry、完整字节 inverse、保留 W08/W09-01、C19 环境六项、无 -I 路由与锁定工具绑定均核对。未来 Root scope/vector、真实 card_path_bindings/W09-99/subtasks/c19_main_source_registry_adoption 与 workers、独立审查决定的来源绑定已做内存反例。普通失败 CAS 不覆盖外部状态，部分写入与提交日志失败回滚、CREATE_NEW 失败清理已用内存适配器验证。真实 Windows 读锁全部关闭；未调用 Windows 采用类或入口，未运行 Go/CLI/dispatcher/native/model，未写 Main 或 Canon。Windows 七文件实际采用仍需 Root 后继登记与独立实际授权；强杀不保证跨文件原子，完整 intent 用于 Root 显式恢复。本决定仅接受 Source，不创建实际采用、CURRENT 或 Formal 状态。\n'
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
own=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mf=save('MF.json',dict(schema='researchos.w09-main-c19-independent-source-manifest.v1',members=own,source_handoff_ref=hr,source_manifest_ref=mr))
hf=save('HDF.json',dict(schema='researchos.w09-main-c19-independent-source-handoff.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',decision=decision['decision'],manifest_ref=mf,source_decision_ref=pin(O/'source-decision.json'),source_handoff_ref=hr,source_manifest_ref=mr,caller_ref=h['caller_ref'],change_set_ref=h['change_set_ref'],checks=len(checks),input_pins=len(allrefs),guard_cleanup_ref=pin(O/'source-guard.cleanup.actual.json'),all_review_handles_closed=True,actual_adoption_executed=False,Main_written=False,Canon_written=False,formal_case_accepted_delta=0,formal_acceptance=False,formal_dispatcher_executed=False,execution_grant=False,new_original_failures=[],STOP=True,FINAL=True))
for ref in own+[mf,hf]:read(ref)
print(json.dumps(dict(HDF=hf,MF=mf,decision=pin(O/'source-decision.json'),checks=len(checks),held_inputs=len(allrefs)),ensure_ascii=False))

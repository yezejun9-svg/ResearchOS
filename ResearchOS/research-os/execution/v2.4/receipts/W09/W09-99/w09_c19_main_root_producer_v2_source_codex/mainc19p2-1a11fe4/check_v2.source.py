"""Memory-only cleanup fault injection; no producer, process, Main or Canon access."""
import ast
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import types
import sys

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
OLD=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_main_root_producer_source_codex/mainc19p-1a11fbc'
checks=[]
def check(name,value):
    assert value,name
    checks.append(dict(name=name,passed=True))
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(N/name)
def module(path):
    m=types.ModuleType('cleanup_source_'+Path(path).stem);m.__file__=str(path)
    exec(compile(Path(path).read_bytes(),str(path),'exec'),m.__dict__);return m

def controls():
    c=load(N/'source.choice.json');contract=load(N/'root-calling-contract.json');oldc=load(OLD/'source.choice.json')
    check('new_fixed_run_and_paths',c['run_id']!=oldc['run_id'] and all(c[k]!=oldc[k] for k in ('receipt_root','scratch_root','output_root')))
    check('exact_Main_Source21_unchanged',c['source21']==oldc['source21'] and c['main_seven_after_refs']==oldc['main_seven_after_refs'])
    check('fixed_toolchain_timeouts_tests_unchanged',all(c[k]==oldc[k] for k in ('toolchain_ref','tool_refs','list_timeout_seconds','producer_timeout_seconds','inner_Go_timeout_seconds','selected_tests','expected_native_ids','list_argv_suffix')))
    check('blueprint_exact_bytes',pin(N/'compiler-source-blueprint.json')['sha256']==pin(OLD/'compiler-source-blueprint.json')['sha256'])
    check('request_changes_bound',load(N/'fix-origin.json')['decision']=='REQUEST_CHANGES' and contract['fix_origin_handoff_ref']==load(N/'fix-origin.json')['handoff_ref'])
    check('952_original_exact_preserved',load(N/'fix-origin.json')['retained_original_failure952_ref']==pin(OLD/'failure952.original-tool-io.json'))
    for field,name in contract['source_file_bindings'].items():check('binding_'+field,contract['bound_source_refs'][field]==pin(N/name))
    for stage in ('prepare','run'):
        argv=contract['future_argv'][stage]
        check('new_exact_argv_'+stage,argv[6]==str(N/(stage+'_main_c19.actual_owned.py')) and len(argv)==10)
    for row in load(N/'complete-byte-inverse.json')['files']:
        check('complete_inverse_'+row['relative'],base64.b64decode(row['whole_before_base64'])==Path(row['original_ref']['path']).read_bytes()
              and base64.b64decode(row['whole_after_base64'])==Path(row['successor_ref']['path']).read_bytes() and row['successor_path_was_absent'])
    oldtree=ast.parse((OLD/'main_c19_runtime.source.py').read_bytes());tree=ast.parse((N/'main_c19_runtime.source.py').read_bytes())
    oldnodes={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    newnodes={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    for name in oldnodes:
        if name not in ('invoke','stage'):check('unchanged_runtime_AST_'+name,newnodes[name]==oldnodes[name])
    for name in ('main_c19_runtime.source.py','main_c19_launcher.source.py','prepare_main_c19.actual_owned.py','run_main_c19.actual_owned.py'):
        compile((N/name).read_bytes(),name,'exec');check('syntax_'+name,True)
    launcher=ast.parse((N/'main_c19_launcher.source.py').read_bytes())
    oldlauncher=ast.parse((OLD/'main_c19_launcher.source.py').read_bytes())
    check('UUID_one_shot_adapter_unchanged',ast.dump(next(n for n in launcher.body if isinstance(n,ast.ClassDef)))==ast.dump(next(n for n in oldlauncher.body if isinstance(n,ast.ClassDef))))
    runtime=module(N/'main_c19_runtime.source.py')
    native_result=dict(actual_exit=0,error=None,timed_out=False,creation_time_100ns=133713371337133713,
        job_cleanup=dict(errors=[],active_processes_last_observed=0,unnamed_exclusive_job=True,kill_on_job_close_configured=True,
            assigned_before_resume=True,primary_exit_confirmed=True,job_idle_confirmed=True,handles_closed=True))
    raw_record=json.dumps(dict(result=native_result)).encode()
    class Memory:
        def __init__(self):
            self.files={};self.dirs={'MEMORY/stage','MEMORY/output'};self.faults={};self.saved={};self.closes=[];self.archive_calls=0;self.prints=[]
        def fault(self,op,path):
            if str(path) in self.faults.get(op,set()):raise OSError(op+':'+str(path))
    state=None
    class MP:
        def __init__(self,value):self.value=str(value).replace('\\','/')
        def __str__(self):return self.value
        def __truediv__(self,other):return MP(self.value+'/'+str(other))
        def is_file(self):state.fault('is_file',self);return self.value in state.files
        def is_dir(self):state.fault('is_dir',self);return self.value in state.dirs
        def read_bytes(self):
            state.fault('read',self)
            if self.value not in state.files:raise FileNotFoundError(self.value)
            return state.files[self.value]
        def open(self,mode):
            state.fault('open',self)
            assert mode=='xb'
            if self.value in state.files:raise FileExistsError(self.value)
            path=self.value
            class Stream(io.BytesIO):
                def close(self):
                    if not self.closed:state.files[path]=self.getvalue()
                    super().close()
            return Stream()
    def mpin(path):
        state.fault('pin',path);raw=state.files[str(path)]
        return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    def msave(root,name,value):
        p=root/name
        if str(p) in state.faults.get('save',set()):
            state.files[str(p)]=b'{"partial":';raise OSError('SAVE_PARTIAL:'+str(p))
        raw=json.dumps(value).encode();state.files[str(p)]=raw;state.saved[name]=copy.deepcopy(value);return mpin(p)
    def mprint(*args,**kwargs):
        state.fault('print','stdout');state.prints.append(args)
    def archive(c,root):
        state.archive_calls+=1;state.fault('archive','packet');return dict(path='MEMORY/archive',sha256='a'*64,bytes=1)
    runtime.pin=mpin;runtime.save=msave;runtime.print=mprint;runtime.capture_packet=archive
    class Guard:
        def __init__(self,label):self.label=label
        def close(self):
            state.closes.append(self.label);state.fault('close',self.label)
            if self.label in state.faults.get('bad_close',set()):return {'closed':True}
            return dict(closed=True,errors=[],retained_handles_count=0)
    labels=['input','runtime','preparation','compiler-exports','launcher-permit']
    def reset():
        nonlocal state
        state=Memory()
        for label in ('compiler-input-list','w09-c19-main-producer'):state.files['MEMORY/stage/'+label+'.invocation.json']=raw_record
    def close():return runtime.close_stage_resources('run',True,{},MP('MEMORY/stage'),MP('MEMORY/output'),[(l,Guard(l)) for l in labels])
    producer='MEMORY/stage/w09-c19-main-producer.invocation.json'
    # Reproduce the exact predecessor finally AST with the reviewer's partial receipt.
    reset();state.files[producer]=b'{"result":'
    oldstage=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name=='stage')
    oldtry=next(n for n in oldstage.body if isinstance(n,ast.Try))
    context=dict(runtime.__dict__,created=True,kind='run',stage_root=MP('MEMORY/stage'),output=MP('MEMORY/output'),
        guards=[(l,Guard(l)) for l in labels],cleanups=[],receipts=[],c={},success=False,packet_ref=None,archive_error=None)
    try:exec(compile(ast.Module(body=oldtry.finalbody,type_ignores=[]),'<original-finally>','exec'),context)
    except json.JSONDecodeError:check('original_P1_reproduced_zero_close',not state.closes and not context['cleanups'])
    else:raise AssertionError('original P1 missing')
    scenarios=[('partial','partial',producer),('missing','missing',producer),('unreadable','read',producer),('pin','pin',producer),
        ('presence','is_file',producer),('output_inspection','is_dir','MEMORY/output'),('archive','archive','packet'),
        ('first_close','close','launcher-permit'),('middle_close','close','preparation'),('bad_close','bad_close','launcher-permit'),
        ('cleanup_save','save','MEMORY/stage/launcher-permit-guard.cleanup.actual.json')]
    for name,op,path in scenarios:
        reset()
        if op=='partial':state.files[path]=b'{"result":'
        elif op=='missing':del state.files[path]
        else:state.faults[op]={path}
        result=close()
        check('all_five_close_attempts_'+name,state.closes==list(reversed(labels)))
        check('independent_error_classification_'+name,bool(result['errors']))
        if name in ('partial','missing','unreadable','pin','presence'):
            check('unknown_job_not_closed_'+name,result['all_owned_jobs_closed'] is False and state.archive_calls==0)
        if name=='cleanup_save':
            row=result['guard_cleanups'][0]
            check('save_failure_keeps_successful_close_observation',row['closed'] is True and row['receipt_saved'] is False and row['observation']['closed'] is True)
    reset();state.faults={'read':{producer},'close':{'compiler-exports'},'save':{'MEMORY/stage/launcher-permit-guard.cleanup.actual.json','MEMORY/stage/runtime-guard.cleanup.actual.json'}}
    result=close()
    check('combined_faults_every_close',state.closes==list(reversed(labels)))
    check('combined_faults_aggregate_all_classes',{'invocation-read','guard-close','guard-cleanup-save'}<={e['phase'] for e in result['errors']})
    reset();result=close()
    check('valid_packet_closes_and_archives_once',result['all_owned_jobs_closed'] and result['all_guards_closed'] and result['all_cleanup_receipts_saved'] and not result['errors'] and state.archive_calls==1)
    # Exact new stage handler/finally/postlude, with only its business body replaced by a pure injected exception.
    stage=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='stage')
    ti=next(i for i,n in enumerate(stage.body) if isinstance(n,ast.Try));tr=copy.deepcopy(stage.body[ti])
    tr.body=[ast.Raise(exc=ast.Name(id='injected_primary',ctx=ast.Load()),cause=None)]
    program=compile(ast.fix_missing_locations(ast.Module(body=[tr,*stage.body[ti+1:]],type_ignores=[])),'<exact-new-stage-tail>','exec')
    def stage_fault(save_final=False,print_fail=False,created=True):
        original=OSError('ORIGINAL_PRODUCER_RECEIPT_WRITE_FAILURE')
        state.files[producer]=b'{"result":'
        if save_final:state.faults.setdefault('save',set()).add('MEMORY/stage/validation.closed.json')
        if print_fail:state.faults.setdefault('print',set()).add('stdout')
        scope=dict(runtime.__dict__,injected_primary=original,kind='run',created=created,c={},stage_root=MP('MEMORY/stage'),output=MP('MEMORY/output'),
            guards=[(l,Guard(l)) for l in labels],primary=None,error=None,success=False,summary=None,request_ref={'memory':True},actual=MP('MEMORY/actual'))
        try:exec(program,scope)
        except runtime.EvidenceFailure as exc:return original,exc
        raise AssertionError('stage failure missing')
    for name,save_final,print_fail in [('partial',False,False),('final_save',True,False),('progress_write',True,True)]:
        reset();original,exc=stage_fault(save_final,print_fail)
        check('stage_original_exception_object_and_cause_'+name,exc.primary_exception is original and exc.__cause__ is original)
        check('stage_all_closes_'+name,state.closes==list(reversed(labels)))
        check('stage_unknown_not_success_'+name,exc.diagnostics['status']=='FAILED_NO_AUTOMATIC_RETRY' and not exc.diagnostics['all_owned_jobs_closed'])
        if save_final:check('stage_final_save_is_secondary_'+name,'stage-result-save' in {e['phase'] for e in exc.secondary_errors})
        if print_fail:check('stage_progress_failure_is_secondary','stage-progress-write' in {e['phase'] for e in exc.secondary_errors})
    reset();state.faults['close']={'runtime'};original,exc=stage_fault(created=False)
    check('pre_directory_failure_all_close_attempted',state.closes==list(reversed(labels)))
    check('pre_directory_failure_no_receipt_write',not state.saved)
    check('pre_directory_failure_emits_unsaved_diagnostics',bool(state.prints) and json.loads(state.prints[0][0])['unsaved_stage_result']['error']==repr(original))
    check('exception_text_retains_primary_and_cleanup_error',repr(original) in str(exc) and 'guard-close' in str(exc))
    reset()
    class Helper:
        def __init__(self,exception=None):self.exception=exception;self.calls=0
        def run_owned(self,argv,cwd,env,stdout,stderr,wall,**kwargs):
            self.calls+=1;stdout.write(b'exact\x00stdout\r\n');stderr.write(b'exact stderr')
            if self.exception is not None:raise self.exception
            return copy.deepcopy(native_result)
    helper=Helper();receipt,observed=runtime.invoke(helper,MP('MEMORY/invoke'),'test',['fake'],{},240)
    rec=state.saved['test.invocation.json']
    check('invoke_success_exact_FILETIME',helper.calls==1 and observed['creation_time_100ns']==133713371337133713 and rec['creation_time_100ns_decimal']=='133713371337133713')
    check('invoke_success_exact_raw',state.files['MEMORY/invoke/test.stdout.raw']==b'exact\x00stdout\r\n')
    for name,op,path in [('raw_pin','pin','MEMORY/invoke/test.stdout.raw'),('receipt_save','save','MEMORY/invoke/test.invocation.json'),('progress','print','stdout')]:
        reset();state.faults[op]={path};original=OSError('ORIGINAL_HELPER_FAILURE');helper=Helper(original)
        try:runtime.invoke(helper,MP('MEMORY/invoke'),'test',['fake'],{},240)
        except runtime.EvidenceFailure as exc:
            check('invoke_original_preserved_'+name,exc.primary_exception is original and exc.__cause__ is original)
            check('invoke_evidence_error_separate_'+name,bool(exc.secondary_errors) and exc.diagnostics['exception']==repr(original))
            check('invoke_no_retry_'+name,helper.calls==1)
        else:raise AssertionError('invoke error missing')
    reset();state.faults['save']={'MEMORY/invoke/test.invocation.json'};helper=Helper()
    try:runtime.invoke(helper,MP('MEMORY/invoke'),'test',['fake'],{},240)
    except runtime.EvidenceFailure as exc:
        check('invoke_partial_receipt_kept',state.files['MEMORY/invoke/test.invocation.json']==b'{"partial":')
        check('invoke_actual_job_observation_retained',exc.diagnostics['result']==native_result and exc.primary_exception is None)
    else:raise AssertionError('persistence failure missing')
    # Exact launcher except/finally/return tail runs in a function, with a memory-only body failure.
    mainnode=next(n for n in launcher.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    lti=next(i for i,n in enumerate(mainnode.body) if isinstance(n,ast.Try));lt=copy.deepcopy(mainnode.body[lti])
    lt.body=[ast.Raise(exc=ast.Name(id='launcher_original',ctx=ast.Load()),cause=None)]
    body=[ast.Assign(targets=[ast.Name(id='primary',ctx=ast.Store())],value=ast.Constant(None)),
        ast.Assign(targets=[ast.Name(id='error',ctx=ast.Store())],value=ast.Constant(None)),lt,*copy.deepcopy(mainnode.body[lti+1:])]
    fn=ast.FunctionDef(name='launcher_tail',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
    reset();state.faults['save']={'MEMORY/stage/launcher.closed.json'}
    provider=types.SimpleNamespace(_used=True);uuidmod=types.SimpleNamespace(uuid4=object());original_uuid=object();runner=types.SimpleNamespace(uuid=provider)
    launcher_original=OSError('ORIGINAL_RUNNER_FAILURE');state.files['MEMORY/launcher']=b'code'
    scope=dict(m=runtime,runner=runner,original_uuid=original_uuid,uuid=uuidmod,stdlib_uuid4=uuidmod.uuid4,provider=provider,
        cleanup_errors=[],returned=None,permit_ref={},runner_ref={},root=MP('MEMORY/stage'),__file__=MP('MEMORY/launcher'),launcher_original=launcher_original)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<exact-launcher-tail>','exec'),scope)
    try:scope['launcher_tail']()
    except runtime.EvidenceFailure as exc:
        check('launcher_original_preserved_on_close_save_failure',exc.primary_exception is launcher_original and exc.__cause__ is launcher_original)
        check('launcher_UUID_restored_despite_persistence_failure',runner.uuid is original_uuid)
        check('launcher_secondary_classified',any(e['phase']=='launcher-closed-save' for e in exc.secondary_errors))
    else:raise AssertionError('launcher failure missing')
    check('new_outputs_absent',all(not Path(c[k]).exists() for k in ('receipt_root','scratch_root','output_root')))
    return dict(schema='researchos.w09-main-c19-producer-v2-pure-source-controls.v1',status='PASS',new_check_count=len(checks),checks=checks,
        memory_only_fault_injections=True,actual_producer=False,actual_jobs=0,Main_Canon_read_or_written=False,
        Git_Go_SQL_API_model_calls=0,formal_case_accepted_delta=0,old_107_controls_historical_not_recounted=True)

def main():
    assert sys.argv[1:] in ([],['--revision2'])
    suffix='.revision2' if sys.argv[1:] else ''
    inputs=load(N/'source-input-pins.original.json');c=load(N/'source.choice.json')
    refs={r['path'].casefold():r for r in inputs['refs']}
    for p in N.iterdir():
        if p.is_file():refs[str(p).casefold()]=pin(p)
    forbidden={r['path'].casefold() for r in c['main_seven_after_refs']}|{str(R/'execution/v2.4'/f'{n}.json').casefold() for n in ('checkpoint','path_ownership','step_state','commands')}
    assert not forbidden.intersection(refs)
    gm=module(c['guard_ref']['path']);guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    try:
        guard.acquire(list(refs.values()));result=controls()
        for ref in inputs['refs']:assert pin(ref['path'])==ref
    finally:
        cleanup=guard.close();cref=save('source-controls'+suffix+'.guard.cleanup.actual.json',cleanup)
    assert cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0
    result.update(original_inputs_unchanged=inputs['count'],guard_cleanup_ref=cref)
    save('source-controls'+suffix+'.json',result)
    print(json.dumps(dict(status='PASS',new_controls=len(checks),inputs_unchanged=inputs['count'],actual=False)))

if __name__=='__main__':main()

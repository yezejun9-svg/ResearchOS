"""Leaf02 narrow observation-retention revision; Source-only delta controls."""
import ast, copy, hashlib, json, ntpath, sys, traceback, types
from pathlib import Path
Q=Path(__file__).resolve().parent
B=Q.parent.parent
OLD=B/'genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-01'
AUTHOR='codex:/root/backup_regression_resources'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def need(v,c):
    if not v: raise AssertionError(c)
def pin(p):
    p=Path(p); raw=p.read_bytes(); return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    with (Q/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(Q/name)
def checked(p,sha,n):
    ref=pin(p); need(ref['sha256']==sha and ref['bytes']==n,'EXACT_BASE_SOURCE_PIN'); return ref
def capture():
    d=Q/'actual-author-host';d.mkdir();pairs=[]; calls={}
    with AUDIT.open('rb') as f:
        first=f.readline(); h=json.loads(first)['payload']
        need(h['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084' and h['agent_path']=='/root/backup_regression_resources' and h['parent_thread_id']==ROOT_THREAD,'ACTUAL_AUTHOR_PARENT')
        f.seek(0,2);prefix=f.tell();f.seek(len(first))
        while f.tell()<prefix:
            at=f.tell();line=f.readline()
            if not line or at+len(line)>prefix:break
            obj=json.loads(line); p=obj.get('payload',{})
            if obj.get('type')!='response_item' or type(p) is not dict:continue
            if p.get('type') in ('custom_tool_call','function_call'):
                source=p.get('input',p.get('arguments',''))
                if type(source) is str and 'task91_' in source:calls[p['call_id']]=(at,line,obj)
            elif p.get('type') in ('custom_tool_call_output','function_call_output') and p.get('call_id') in calls:
                ca,cr,co=calls.pop(p['call_id']); cid=p['call_id'];raw=first+cr+line
                with (d/(cid+'.raw.jsonl')).open('xb') as out:out.write(raw)
                rawref=pin(d/(cid+'.raw.jsonl'))
                binding={'schema':'researchos.Source-author-actual-tool-binding.v1','Source_author':AUTHOR,'actual_agent_path':h['agent_path'],'Source_author_thread':h['id'],'actual_parent_thread':ROOT_THREAD,'source_audit_path':str(AUDIT),'source_prefix_bytes':prefix,'source_line_offsets':[0,ca,at],'source_line_bytes':[len(first),len(cr),len(line)],'source_line_sha256':[hashlib.sha256(x).hexdigest() for x in (first,cr,line)],'original_capture_ref':rawref,'actual_call_id':cid,'actual_tool_name':co['payload'].get('name'),'tool_call_utc':co['timestamp'],'tool_output_utc':obj['timestamp'],'Root_issuer':False,'formal_acceptance':False}
                bp=d/(cid+'.binding.json')
                with bp.open('xb') as out:out.write((json.dumps(binding,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8'))
                pairs.append({'raw_ref':rawref,'binding_ref':pin(bp),'call_id':cid,'is_original1119':'task91_leaf2_enum_input' in co['payload'].get('input','')})
    need(sum(x['is_original1119'] for x in pairs)==1,'ORIGINAL1119_ACTUAL_RAW_PAIR')
    return save('Source-actual-host.index.json',{'schema':'researchos.Source-author-audit.v1','source_author':AUTHOR,'actual_thread':h['id'],'parent_root_thread':ROOT_THREAD,'pairs':pairs,'inflight_sealer_call_ids_not_fabricated':list(calls),'future_sealer_full_call_return':'Root retains actual eventual result after return; no future output synthesized.','formal_acceptance':False}),next(x for x in pairs if x['is_original1119'])
def main():
    base_ref=checked(OLD/'public21_runner.py','c021acfb72e5ea40bddabfa9d12ce740ac0d54dff917ef2f4d18eaf584e5a587',18867)
    base_contract_ref=checked(OLD/'contract.json','e0a466f6d0e7a11306f8e6d1d64557333281003393dba74c4b2240af2099e3e2',29393)
    base_hdf=pin(OLD/'HDF.json');base_mf=pin(OLD/'MF.json')
    contract=json.loads((OLD/'contract.json').read_bytes())
    reviewdir=B/'schema21_public_bootstrap_source_independent_review_codex/review-public21-20261010-01'
    review_refs={'hdf':checked(reviewdir/'HDF.json','d591da9d113f6ae1c191770b6162e95d49bc7771d818902e6d403a3be5a519e6',5040),'mf':checked(reviewdir/'MF.json','29ae67b8a27b044ae2e21e7a34cdc2dc42cd73ec858678386f78ce8618868ae7',67856),'decision':checked(reviewdir/'source-decision.json','cc22aba4e7cc9d9c4d6978bbca4996541bcfcd51b5b5bb2286f78fa428314b47',4740)}
    guardref=contract['source_guard'];mod=types.ModuleType('leaf02_guard');exec(compile(Path(guardref['path']).read_bytes(),guardref['path'],'exec'),mod.__dict__);guard=mod.SourceReadGuard()
    try:
        guard.acquire([base_ref,base_contract_ref,base_hdf,base_mf,guardref,*review_refs.values(),pin(OLD/'source-controls.json'),pin(__file__)])
        raw=guard.get_buffer(base_ref['path'])
        old=b"invocation.update(observation=observed,actual_exit=observed.get('actual_exit'),ended_at_unix_ns=time.time_ns(),stdout_ref=observed_ref(stdout),stderr_ref=observed_ref(stderr))"
        eol=b'\r\n' if b'\r\n' in raw else b'\n'
        new=b"invocation.update(observation=observed,actual_exit=observed.get('actual_exit'),ended_at_unix_ns=time.time_ns())"+eol+b"        invocation['stdout_ref']=observed_ref(stdout)"+eol+b"        invocation['stderr_ref']=observed_ref(stderr)"
        need(raw.count(old)==1,'ONE_EXACT_OBSERVATION_SPAN');offset=raw.index(old);candidate=raw[:offset]+new+raw[offset+len(old):]
        need(candidate[:offset]+old+candidate[offset+len(new):]==raw,'EXACT_INVERSE_FULL_SOURCE')
        with (Q/'public21_runner.py').open('xb') as f:f.write(candidate)
        ast.parse(candidate);compile(candidate,str(Q/'public21_runner.py'),'exec')
        contract['runner_ref']=pin(Q/'public21_runner.py')
        contract['status']='SOURCE_ONLY_AFTER_REQUEST_CHANGES_PENDING_NEW_NONAUTHOR_REVIEW'
        contract['source_revision_basis']={'base_hdf_ref':base_hdf,'base_mf_ref':base_mf,'base_runner_ref':base_ref,'base_contract_ref':base_contract_ref,'rejected_review_refs':review_refs,'finding':'PUBLIC21-OBSERVATION-001','accepted_by_author':False}
        contract_ref=save('contract.json',contract)
        inverse_ref=save('exact-inverse.json',{'schema':'researchos.Source-exact-byte-span-inverse.v1','base_ref':base_ref,'candidate_ref':pin(Q/'public21_runner.py'),'offset':offset,'old_bytes':len(old),'new_bytes':len(new),'old_span_utf8':old.decode(),'new_span_utf8':new.decode(),'inverse_sha256':hashlib.sha256(raw).hexdigest(),'all_other_runner_bytes_unchanged':True,'base_contract_ref':base_contract_ref,'contract_delta':['runner_ref to this actual new candidate','Source status/rejected-review basis only'],'old56_controls_not_rerun':True,'actual_product_calls':0})
        tree=ast.parse(candidate);run=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run_registered_case')
        trial=next(x for x in run.body if isinstance(x,ast.Try));body=trial.body
        at=next(i for i,x in enumerate(body) if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Attribute) and x.value.func.attr=='update' and isinstance(x.value.func.value,ast.Name) and x.value.func.value.id=='invocation')
        block=ast.fix_missing_locations(ast.Module(body=body[at:at+3],type_ignores=[]))
        observed={'actual_exit':0,'job_cleanup':{'job_idle_observed':True,'handles_closed':True}}
        checks=[]
        for bad in (None,'stdout','stderr'):
            invocation={};seen=[]
            def observed_ref(path):
                seen.append(path)
                if path==bad:raise OSError('synthetic '+path+' pin failure')
                return {'path':'D:/synthetic/'+path,'sha256':'a'*64,'bytes':0}
            env=dict(invocation=invocation,observed=observed,stdout='stdout',stderr='stderr',observed_ref=observed_ref,time=types.SimpleNamespace(time_ns=lambda:17))
            error=None
            try:exec(compile(block,'exact-candidate-observation-statements','exec'),env)
            except OSError as exc:error=str(exc)
            need(invocation['observation'] is observed and invocation['actual_exit']==0 and invocation['ended_at_unix_ns']==17 and invocation['observation']['job_cleanup']['handles_closed'] is True,'RETURNED_OBSERVATION_AND_CLEANUP_PRESERVED')
            need((error is None)==(bad is None),'EXACT_SYNTHETIC_FAULT_OUTCOME')
            if bad=='stderr':need('stdout_ref' in invocation and 'stderr_ref' not in invocation,'COMPLETED_STDOUT_PIN_RETAINED')
            if bad=='stdout':need('stdout_ref' not in invocation and 'stderr_ref' not in invocation,'UNKNOWN_PINS_NOT_INVENTED')
            checks.append({'id':'OBSERVATION_RETENTION_'+str(bad),'passed':True,'synthetic_fault':bad,'not_Native_or_SQL':True,'known_exit_preserved':0,'known_Jobcleanup_preserved':True})
        controls_ref=save('delta-controls.json',{'schema':'researchos.public21-observation-retention-delta-controls.v1','passed':3,'failed':0,'checks':checks,'old56_rerun':False,'Native_Go_SQL_model_TP':0,'formal_acceptance':False})
    finally:
        closed=guard.close();guard_ref=save('Source-revision.guard.closed.json',closed)
    need(closed['closed'] is True and closed['retained_handles_count']==0 and closed['verification']=='PASSED' and not closed['errors'],'REVISION_GUARD_CLOSED')
    audit_ref,failure_pair=capture()
    failure_origin_ref=save('failure-origin.1119.json',{'schema':'researchos.original-source-failure-origin.v1','original_ordinal':1119,'original_chunk_id':'405a88','complete_IO_ref':pin(Q/'failure-405a88.complete-original-IO.json'),'raw_ref':failure_pair['raw_ref'],'actual_host_binding_ref':failure_pair['binding_ref'],'actual_outer_exit':1,'actual_python_exit':None,'actual_native_exit':None,'actual_dispatcher_exit':None,'actual_model_exit':None,'guard_state':'NOT_ACQUIRED_IN_FAILED_CALL','counter_reset':False,'automatic_retry':False,'false_normal_prefix_preserved':True})
    source_inputs_ref=save('source-inputs.json',{'schema':'researchos.public21-revision-source-inputs.v1','references':[base_ref,base_contract_ref,base_hdf,base_mf,*review_refs.values(),contract['input_manifest_ref'],guardref],'new_source_author':AUTHOR,'old56_controls_ref':pin(OLD/'source-controls.json'),'old_tool_evidence_preserved_via_base_MF':True,'original1119_ref':failure_origin_ref})
    member_refs=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
    fullguard=mod.SourceReadGuard()
    try:fullguard.acquire(member_refs+[guardref])
    finally:fullclosed=fullguard.close();full_ref=save('Source-full-closure.guard.closed.json',fullclosed)
    need(fullclosed['closed'] is True and fullclosed['retained_handles_count']==0 and fullclosed['verification']=='PASSED' and not fullclosed['errors'],'FULL_REVISION_CLOSED')
    members=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
    mf_ref=save('MF.json',{'schema':'researchos.schema21-public-bootstrap-source-manifest.v1','Source_author':AUTHOR,'members':members,'member_count':len(members),'exclusions':['MF.json/HDF.json self-referential seal','Current sealer actual output is captured by Root after return, never prefilled'],'formal_acceptance':False,'execution_grant':False})
    hdf_ref=save('HDF.json',{'schema':'researchos.schema21-public-bootstrap-source-handoff.v1','status':'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW','source_author':AUTHOR,'manifest_ref':mf_ref,'runner_ref':pin(Q/'public21_runner.py'),'contract_ref':contract_ref,'input_manifest_ref':contract['input_manifest_ref'],'source_inputs_ref':source_inputs_ref,'base_hdf_ref':base_hdf,'base_mf_ref':base_mf,'rejected_review_refs':review_refs,'inverse_ref':inverse_ref,'delta_controls_ref':controls_ref,'delta_controls':3,'original56_not_rerun':True,'source_author_audit_ref':audit_ref,'source_revision_guard_ref':guard_ref,'source_full_closure_ref':full_ref,'original1119_ref':failure_origin_ref,'Native_Go_SQL_model_TP_calls':0,'formal_acceptance':False,'execution_grant':False,'Source_self_acceptance':False,'future_Root_scope_ref':None,'future_runtime_qualification_ref':None,'STOP':True})
    print(json.dumps({'schema':'researchos.schema21-public-bootstrap-source-delivery.v1','operation':'SOURCE_PREPARATION','component':'OLD21_PUBLIC_BOOTSTRAP_RUNNER_SOURCE','source_author':AUTHOR,'hdf_ref':hdf_ref,'mf_ref':mf_ref,'runner_ref':pin(Q/'public21_runner.py'),'contract_ref':contract_ref,'delta_controls_ref':controls_ref,'source_guard_ref':full_ref,'original1119_ref':failure_origin_ref,'original1119_raw_ref':failure_pair['raw_ref'],'original1119_binding_ref':failure_pair['binding_ref'],'delta_controls':3,'execution_grant':False,'formal_acceptance':False,'STOP':True},ensure_ascii=False,sort_keys=True))
    return 0
if __name__=='__main__':
    code=1
    try:code=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)

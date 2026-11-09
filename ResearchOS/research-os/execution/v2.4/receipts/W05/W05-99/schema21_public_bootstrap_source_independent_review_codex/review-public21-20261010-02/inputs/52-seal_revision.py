"""Continue only unfinished leaf02 seal. Preserve originals1119/1120 and prefix."""
import ast, hashlib, json, ntpath, sys, traceback, types
from pathlib import Path
Q=Path(__file__).resolve().parent
B=Q.parent.parent
AUTHOR='codex:/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def need(v,c):
    if not v:raise AssertionError(c)
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    with (Q/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(Q/name)
def main():
    c=json.loads((Q/'contract.json').read_bytes())
    controls=json.loads((Q/'delta-controls.json').read_bytes())
    need(controls['passed']==3 and controls['failed']==0 and controls['old56_rerun'] is False,'SUCCESSFUL_PREFIX_NOT_RETESTED')
    closed=json.loads((Q/'Source-revision.guard.closed.json').read_bytes())
    need(closed['closed'] is True and closed['retained_handles_count']==0 and closed['verification']=='PASSED' and not closed['errors'],'PREFIX_GUARD_CLOSED')
    # Reuse the byte-capture algorithm by AST only, scoped to this actual author/task.
    old=B/'genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-01'
    capture_source=(old/'seal_source.py').read_text(encoding='utf-8')
    tree=ast.parse(capture_source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='capture')
    source=ast.get_source_segment(capture_source,node).replace("Q/'actual-author-host'","Q/'actual-author-host-final'").replace("'task87_'","'task91_'").replace("need(len(completed)>=25,'FINITE_SOURCE_TOOL_PAIRS')","need(len(completed)>=8,'FINITE_SOURCE_TOOL_PAIRS')")
    audit_path=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
    def raw_new(path,raw):
        with Path(path).open('xb') as f:f.write(raw)
        return pin(path)
    env=dict(Q=Q,AUTHOR=AUTHOR,THREAD=THREAD,ROOT_THREAD=ROOT_THREAD,AUDIT=audit_path,Path=Path,json=json,hashlib=hashlib,need=need,raw_new=raw_new)
    exec(compile(source,'scoped-actual-author-byte-capture','exec'),env)
    audit=env['capture']()
    audit['Task91_first_call_offset']=audit.pop('first_Task87_call_offset')
    audit_ref=save('Source-final-actual-host.index.json',audit)
    ocpath=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py'
    ocraw=ocpath.read_bytes();need(hashlib.sha256(ocraw).hexdigest()=='b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06' and len(ocraw)==65191,'OC3_ACTUAL_SOURCE_PIN')
    oc=types.ModuleType('actual_source_host_structure');oc.__file__=str(ocpath);exec(compile(ocraw,str(ocpath),'exec'),oc.__dict__)
    origins=[]
    for ordinal,chunk,io_name in ((1119,'405a88','failure-405a88.complete-original-IO.json'),(1120,'481260','failure-481260.complete-original-IO.json')):
        matches=[]
        for pair in audit['completed_tool_pairs']:
            rows=[json.loads(line) for line in Path(pair['raw_ref']['path']).read_bytes().splitlines()]
            hosts=[x for x in oc.structured_documents(rows[2]['payload']['output']) if x.get('chunk_id')==chunk and type(x.get('exit_code')) is int]
            if hosts:matches.append((pair,hosts))
        need(len(matches)==1 and len(matches[0][1])==1,'UNIQUE_ACTUAL_RETURNED_CHUNK_'+chunk)
        pair,hosts=matches[0];host=hosts[0]
        need(host['exit_code']==1,'ACTUAL_OUTER_FAILURE_EXIT')
        origins.append(save('failure-origin.'+str(ordinal)+'.json',{'schema':'researchos.original-source-failure-origin.v1','original_ordinal':ordinal,'original_chunk_id':chunk,'complete_IO_ref':pin(Q/io_name),'raw_ref':pair['raw_ref'],'actual_host_binding_ref':pair['binding_ref'],'actual_outer_exit':1,'actual_python_exit':1 if ordinal==1120 else None,'actual_native_exit':None,'actual_dispatcher_exit':None,'actual_model_exit':None,'actual_go_exit':None,'guard_state':'NOT_ACQUIRED_IN_FAILED_CALL' if ordinal==1119 else 'Source-revision.guard.closed.json successful prefix closed0; no full seal guard created','counter_reset':False,'automatic_retry':False,'successful_prefix_preserved':True}))
    inputs_ref=save('source-inputs.json',{'schema':'researchos.public21-revision-source-inputs.v1','references':[pin(old/'HDF.json'),pin(old/'MF.json'),pin(old/'public21_runner.py'),pin(old/'contract.json'),*c['source_revision_basis']['rejected_review_refs'].values(),c['input_manifest_ref'],c['source_guard']],'source_author':AUTHOR,'old56_controls_ref':pin(old/'source-controls.json'),'old_tool_evidence_preserved_via_base_MF':True,'original_failure_refs':origins})
    refs=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
    refs+=[pin(old/'HDF.json'),pin(old/'MF.json'),pin(old/'public21_runner.py'),pin(old/'contract.json'),pin(old/'seal_source.py'),pin(old/'source-controls.json'),c['source_guard'],pin(ocpath)]
    refs+=list(c['source_revision_basis']['rejected_review_refs'].values())
    guardmod=types.ModuleType('leaf02_final_guard');g=c['source_guard'];raw=Path(g['path']).read_bytes();need(hashlib.sha256(raw).hexdigest()==g['sha256'] and len(raw)==g['bytes'],'GUARD_FIXED_PIN');exec(compile(raw,g['path'],'exec'),guardmod.__dict__)
    guard=guardmod.SourceReadGuard()
    try:guard.acquire(refs)
    finally:finalclosed=guard.close();guard_ref=save('Source-full-closure.guard.closed.json',finalclosed)
    need(finalclosed['closed'] is True and finalclosed['retained_handles_count']==0 and finalclosed['verification']=='PASSED' and not finalclosed['errors'],'FINAL_SOURCE_CLOSED')
    members=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
    mf_ref=save('MF.json',{'schema':'researchos.schema21-public-bootstrap-source-manifest.v1','Source_author':AUTHOR,'members':members,'member_count':len(members),'exclusions':['MF.json/HDF.json self-referential seal','Current sealer actual output is retained by Root after return, not prefilled'],'formal_acceptance':False,'execution_grant':False})
    hdf_ref=save('HDF.json',{'schema':'researchos.schema21-public-bootstrap-source-handoff.v1','status':'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW','source_author':AUTHOR,'manifest_ref':mf_ref,'runner_ref':pin(Q/'public21_runner.py'),'contract_ref':pin(Q/'contract.json'),'input_manifest_ref':c['input_manifest_ref'],'source_inputs_ref':inputs_ref,'base_hdf_ref':pin(old/'HDF.json'),'base_mf_ref':pin(old/'MF.json'),'rejected_review_refs':c['source_revision_basis']['rejected_review_refs'],'inverse_ref':pin(Q/'exact-inverse.json'),'delta_controls_ref':pin(Q/'delta-controls.json'),'delta_controls':3,'original56_not_rerun':True,'successful_prefix_actual_outer_Python_exit':[1,1],'prefix_failure_original1120_preserved':True,'source_author_audit_ref':audit_ref,'source_revision_guard_ref':pin(Q/'Source-revision.guard.closed.json'),'source_full_closure_ref':guard_ref,'original_failure_refs':origins,'Native_Go_SQL_model_TP_calls':0,'formal_acceptance':False,'execution_grant':False,'Source_self_acceptance':False,'future_Root_scope_ref':None,'future_runtime_qualification_ref':None,'STOP':True})
    print(json.dumps({'schema':'researchos.schema21-public-bootstrap-source-delivery.v1','operation':'SOURCE_PREPARATION','component':'OLD21_PUBLIC_BOOTSTRAP_RUNNER_SOURCE','source_author':AUTHOR,'hdf_ref':hdf_ref,'mf_ref':mf_ref,'runner_ref':pin(Q/'public21_runner.py'),'contract_ref':pin(Q/'contract.json'),'delta_controls_ref':pin(Q/'delta-controls.json'),'source_guard_ref':guard_ref,'original_failure_refs':origins,'original_failure_raw_bindings':[{'raw_ref':json.loads(Path(x['path']).read_bytes())['raw_ref'],'binding_ref':json.loads(Path(x['path']).read_bytes())['actual_host_binding_ref']} for x in origins],'delta_controls':3,'execution_grant':False,'formal_acceptance':False,'STOP_leaf_revision':True},ensure_ascii=False,sort_keys=True))
    return 0
if __name__=='__main__':
    code=1
    try:code=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)

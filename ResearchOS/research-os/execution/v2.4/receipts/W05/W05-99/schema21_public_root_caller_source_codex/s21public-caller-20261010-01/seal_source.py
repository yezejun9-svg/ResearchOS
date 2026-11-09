"""Seal this Source after real finite checks. Never emits a Root grant."""
import ast, hashlib, json, sys, types
from pathlib import Path
Q=Path(__file__).resolve().parent;B=Q.parent.parent
AUTHOR='codex:/root/backup_regression_resources';THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084';ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def need(v,c):
    if not v:raise AssertionError(c)
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    with (Q/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(Q/name)
def main():
    controls=json.loads((Q/'source-controls.revision.json').read_bytes());closed=json.loads((Q/'source-controls.revision.guard.closed.json').read_bytes())
    need(controls['count']==controls['passed']==58 and not controls['failed'] and controls['error'] is None and controls['Root_stages_executed']==[] and controls['Go_Native_SQL_TP_model_calls']==0,'ACTUAL_58_SOURCE_RESULTS')
    need(sum(bool(x.get('reused_from_original_prefix')) for x in controls['controls'])==2,'ONLY_TWO_PREFIX_REUSED')
    need(closed['closure']['closed'] is True and closed['closure']['retained_handles_count']==0 and closed['closure']['verification']=='PASSED' and not closed['closure']['errors'],'ACTUAL_PREFIX_GUARD_CLOSED')
    p=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py';m=types.ModuleType('public21_seal_reference');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
    diagnostics=json.loads((Q/'source-diagnostic-original-host.index.json').read_bytes());matches=[]
    for pair in diagnostics['completed_tool_pairs']:
        rows=[json.loads(x) for x in Path(pair['raw_ref']['path']).read_bytes().splitlines()]
        if 'apply_patch verification failed: Failed to find expected lines' in json.dumps(rows[2]['payload']['output'],ensure_ascii=False):matches.append(pair)
    need(len(matches)==1,'UNIQUE_ACTUAL_TOOL_REJECTION_1134')
    pair=matches[0]
    origin1134=save('failure-origin.1134.json',dict(schema='researchos.original-source-failure-origin.v1',original_ordinal=1134,capture_kind='ACTUAL_TOOL_REJECTION',complete_IO_ref=pin(Q/'failure-apply_patch.complete-original-IO.json'),raw_ref=pair['raw_ref'],actual_host_binding_ref=pair['binding_ref'],actual_outer_exit=None,actual_python_exit=None,actual_native_exit=None,actual_go_exit=None,actual_SQL_exit=None,actual_TP_exit=None,actual_model_exit=None,tool='tools.apply_patch',process_started=False,mutation_applied=False,guard_state='NO_NEW_GUARD_IN_REJECTED_TOOL_CALL',cause='patch context expected raw=raw.replace but actual initial statement was raw=original.replace; old patch input not retried',counter_reset=False,automatic_retry=False))
    old=B/'genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-01/seal_source.py';text=old.read_text(encoding='utf-8');node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='capture')
    segment=ast.get_source_segment(text,node).replace("Q/'actual-author-host'","Q/'actual-author-host-final'").replace("'task87_'","'task91_'").replace("need(len(completed)>=25,'FINITE_SOURCE_TOOL_PAIRS')","need(len(completed)>=8,'FINITE_SOURCE_TOOL_PAIRS')")
    def raw_new(path,raw):
        with Path(path).open('xb') as f:f.write(raw)
        return pin(path)
    env=dict(Q=Q,AUTHOR=AUTHOR,THREAD=THREAD,ROOT_THREAD=ROOT_THREAD,AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl'),Path=Path,json=json,hashlib=hashlib,need=need,raw_new=raw_new)
    exec(compile(segment,'actual-public21-source-author-capture','exec'),env);audit=env['capture']();audit['first_Task91_call_offset']=audit.pop('first_Task87_call_offset')
    audit_ref=save('actual-source-author-host.index.json',audit)
    new_source=Q/'public21_root.source.py';tree=ast.parse(new_source.read_text(encoding='utf-8'));compile(tree,str(new_source),'exec')
    caller=types.ModuleType('public21_current_Source');caller.__file__=str(new_source);exec(compile(tree,str(new_source),'exec'),caller.__dict__)
    need(caller.AUTHOR==AUTHOR and caller.ROOT_THREAD==ROOT_THREAD,'TRUTHFUL_ACTUAL_SOURCE_AUTHOR')
    inverse=json.loads((Q/'specialization-exact-inverse.json').read_bytes());need(inverse['AST_full_inverse'] is True and inverse['original_bytes_unchanged'] is True and m.same_ref(inverse['source_ref'],caller.OC3_REF),'EXACT_UNCHANGED_OC3_INVERSE')
    contract=json.loads((Q/'root-calling-contract.source.json').read_bytes());need(m.same_ref(contract['caller_ref'],pin(new_source)) and contract['execution_grant'] is False and contract['formal_acceptance'] is False,'CURRENT_CALLER_CONTRACT_REF')
    before=(Q/'public21_root.before-mf-adapter.source.txt').read_text(encoding='utf-8');before_tree=ast.parse(before)
    oldnodes={n.name:ast.dump(n,include_attributes=False) for n in before_tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    newnodes={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    added=sorted(set(newnodes)-set(oldnodes));changed=sorted(k for k in oldnodes if newnodes.get(k)!=oldnodes[k])
    need(added==['public21_review_manifest','review_member_refs','validate_task94_body'] and changed==['runner_chain','validate_peer_delivery'],'ACTUAL_REVIEW_ADAPTER_ONLY_FUNCTION_DELTA')
    delta_ref=save('review-adapter-exact-function-delta.json',dict(before_ref=pin(Q/'public21_root.before-mf-adapter.source.txt'),after_ref=pin(new_source),added_functions=added,changed_functions=changed,unchanged_functions=sorted(set(oldnodes)-set(changed)),all_other_function_AST_equal=True,constant_delta=['RUNNER_REVIEW_BASE','RUNNER_ACCEPTED_REVIEW_REFS','RUNNER_REAL_PEER_AUDIT_REF'],source_before_closed_guard_ref=pin(Q/'source-controls.guard.closed.json'),initial_original_failure=1132,tool_rejection_original1134=origin1134,real_Task94_Final_ref=caller.RUNNER_REAL_PEER_AUDIT_REF,authority='NONE'))
    refs=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
    refs+=json.loads((Q/'source-inputs.json').read_bytes())['references']+[pin(old)]
    refs=m.local_refs(refs)
    guard=m.guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
    try:guard.acquire(refs)
    finally:
        closure=guard.close();guard_ref=save('Source-full-closure.guard.closed.json',dict(closure=closure,held_refs=refs,Source_only=True,live_Canon_held=False,Root_Go_Native_SQL_TP_model_calls=0))
    need(closure['closed'] is True and closure['retained_handles_count']==0 and closure['verification']=='PASSED' and not closure['errors'],'SOURCE_FULL_CLOSURE')
    members=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
    mf_ref=save('MF.json',dict(schema='researchos.public21-root-caller-source-manifest.v1',source_author=AUTHOR,members=members,member_count=len(members),exclusions=['MF/HDF self-referential seal','current sealer actual return and this later FINAL are externally retained by Root after return, not prefilled'],formal_acceptance=False,execution_grant=False))
    hdf_ref=save('HDF.json',dict(schema='researchos.public21-root-caller-source-handoff.v1',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING',source_author=AUTHOR,author_thread=THREAD,parent_Root_thread=ROOT_THREAD,manifest_ref=mf_ref,caller_ref=pin(new_source),registrar_ref=pin(new_source),contract_ref=pin(Q/'root-calling-contract.source.json'),source_inputs_ref=pin(Q/'source-inputs.json'),source_author_audit_ref=audit_ref,Source_full_closure_ref=guard_ref,source_controls_ref=pin(Q/'source-controls.revision.json'),Source_controls_passed=58,original_prefix_successes_reused=2,new_unreached_or_delta_controls=56,prior_leaf56_OC3_controls_not_rerun=True,OC3_source_ref=caller.OC3_REF,specialization_inverse_ref=pin(Q/'specialization-exact-inverse.json'),review_protocol_delta_ref=delta_ref,runner_source_refs=caller.LEAF_REFS,actual_accepted_runner_review_refs=caller.RUNNER_ACCEPTED_REVIEW_REFS,real_existing_runner_peer_audit_ref=caller.RUNNER_REAL_PEER_AUDIT_REF,old21_programme_ref=caller.PROGRAMME_REF,original_failure_refs=[pin(Q/'failure-origin.1132.json'),origin1134],old1119_1120_preserved_via_leaf02=True,original1025_1109_1113_and_failure_counters_unchanged=True,live_Canon_read_or_held=False,Root_Go_Native_SQL_TP_model_calls=0,Source_self_acceptance=False,future_current4=None,future_RootScope=None,future_SourceReviewer_root_witness=None,future_runtime_qualification=None,future_actual_bootstrap=None,formal_acceptance=False,parent_acceptance=False,execution_grant=False,STOP=True))
    print(json.dumps(dict(schema='researchos.public21-root-caller-source-delivery.v1',operation='SOURCE_PREPARATION',source_author=AUTHOR,author_thread=THREAD,root_thread_id=ROOT_THREAD,hdf_ref=hdf_ref,mf_ref=mf_ref,caller_ref=pin(new_source),contract_ref=pin(Q/'root-calling-contract.source.json'),source_inputs_ref=pin(Q/'source-inputs.json'),controls_ref=pin(Q/'source-controls.revision.json'),source_guard_ref=guard_ref,Source_controls_passed=58,reused_prefix_controls=2,new_finite_controls=56,original_failure_refs=[pin(Q/'failure-origin.1132.json'),origin1134],original1134_raw_ref=pair['raw_ref'],original1134_binding_ref=pair['binding_ref'],formal_acceptance=False,execution_grant=False,Root_product_branch_called=False,STOP=True),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':
    code=1
    try:main();code=0
    finally:print('ROOT_PYTHON_EXIT='+str(code),flush=True)
    sys.exit(code)

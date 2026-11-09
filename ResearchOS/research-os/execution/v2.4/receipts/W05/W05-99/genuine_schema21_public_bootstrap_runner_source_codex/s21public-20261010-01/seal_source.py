"""Seal Task87 Source and completed author host pairs; no product branch."""
import ast, hashlib, json, ntpath, sys, traceback, types
from pathlib import Path
from datetime import datetime, timezone
Q=Path(__file__).resolve().parent
AUTHOR='codex:/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def need(ok,code):
    if not ok: raise AssertionError(code)
def pin(p):
    p=Path(p); raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    with (Q/name).open('xb') as f: f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(Q/name)
def raw_new(path,raw):
    with Path(path).open('xb') as f: f.write(raw)
    return pin(path)
def capture():
    outdir=Q/'actual-author-host'; outdir.mkdir()
    with AUDIT.open('rb') as f:
        first=f.readline(); header=json.loads(first); identity=header['payload']
        need(header['type']=='session_meta' and identity['id']==THREAD and identity['agent_path']=='/root/backup_regression_resources' and identity['parent_thread_id']==ROOT_THREAD,'ACTUAL_SOURCE_AUTHOR_HEADER')
        f.seek(0,2); prefix=f.tell(); f.seek(len(first))
        calls={}; completed=[]; scan_from=None
        while f.tell()<prefix:
            at=f.tell(); raw=f.readline()
            if not raw or at+len(raw)>prefix: break
            row=json.loads(raw); value=row.get('payload')
            if row.get('type')!='response_item' or type(value) is not dict: continue
            kind=value.get('type')
            if kind in ('custom_tool_call','function_call'):
                source=value.get('input',value.get('arguments',''))
                if type(source) is str and 'task87_' in source:
                    if scan_from is None: scan_from=at
                    need(type(value.get('call_id')) is str,'ACTUAL_SOURCE_CALL_ID')
                    calls[value['call_id']]=(at,raw,row)
            elif kind in ('custom_tool_call_output','function_call_output') and value.get('call_id') in calls:
                call_at,call_raw,call_row=calls.pop(value['call_id'])
                call_id=value['call_id']
                need(row['timestamp']>=call_row['timestamp'],'SOURCE_ACTUAL_CALL_RETURN_TIME')
                raw_ref=raw_new(outdir/(call_id+'.raw.jsonl'),first+call_raw+raw)
                binding={'schema':'researchos.Source-author-actual-tool-binding.v1','Source_author':AUTHOR,'actual_agent_path':identity['agent_path'],'Source_author_thread':THREAD,'actual_parent_thread':ROOT_THREAD,'source_audit_path':str(AUDIT),'source_prefix_bytes':prefix,'source_line_offsets':[0,call_at,at],'source_line_bytes':[len(first),len(call_raw),len(raw)],'source_line_sha256':[hashlib.sha256(item).hexdigest() for item in (first,call_raw,raw)],'original_capture_ref':raw_ref,'actual_call_id':call_id,'actual_tool_name':call_row['payload'].get('name'),'actual_tool_type':call_row['payload']['type'],'tool_call_utc':call_row['timestamp'],'tool_output_utc':row['timestamp'],'capture_is_raw_original_bytes':True,'Root_issuer':False,'formal_acceptance':False,'execution_grant':False}
                binding_ref=raw_new(outdir/(call_id+'.binding.json'),(json.dumps(binding,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8'))
                completed.append({'raw_ref':raw_ref,'binding_ref':binding_ref,'call_id':call_id})
    need(len(completed)>=25,'FINITE_SOURCE_TOOL_PAIRS')
    return {'schema':'researchos.schema21-public-bootstrap-source-author-audit.v1','source_author':AUTHOR,'actual_thread':THREAD,'actual_parent_thread':ROOT_THREAD,'session_meta_ref':raw_new(outdir/'session-meta.raw.jsonl',first),'completed_tool_pairs':completed,'completed_pair_count':len(completed),'source_prefix_size':prefix,'first_Task87_call_offset':scan_from,'inflight_sealer_call_ids_not_fabricated':sorted(calls),'inflight_sealer_result_capture':'Cannot exist before return. Root retains the real eventual sealing tool call+return as external Source publication evidence; these pending IDs provide no acceptance/execution authority.','raw_bytes_not_reencoded':True,'Root_issuer':False,'formal_acceptance':False,'execution_grant':False}
def main():
    contract=json.loads((Q/'contract.json').read_bytes())
    controls=json.loads((Q/'source-controls.json').read_bytes())
    need(controls['passed']==56 and controls['failed']==0 and controls['run_registered_case_called'] is False,'FINITE_CONTROLS_COMPLETE_SOURCE_ONLY')
    for name in ('source-preparation.guard.closed.json','source-controls.guard.closed.json'):
        closed=json.loads((Q/name).read_bytes()); need(closed['closed'] is True and closed['retained_handles_count']==0 and closed['verification']=='PASSED' and not closed['errors'],'PRIOR_GUARD_CLOSED')
    io=json.loads((Q/'actual-tool-IO.values.json').read_bytes())
    need(not io['missing_in_memory_pairs'],'COMPLETE_STORED_TOOL_IO_VALUES')
    for row in io['records']:
        result=row['actual_result']
        if type(result) is dict and 'exit_code' in result: need(result['exit_code']==0,'NO_NEW_SOURCE_ORIGINAL_FAILURE')
        if row['Python_exit_marker'] is not None: need(row['Python_exit_marker']=='0','MARKED_PYTHON_NOT_ZERO')
    audit_ref=save('source-author-audit.json',capture())
    source_root=Path(contract['old21_root'])
    supplemental={'schema':'researchos.schema21-public-bootstrap-supplemental-source.v1','private_file_source_ref':pin(source_root/'apps/control/private_windows.go'),'private_file_source_note':'Original frozen Windows implementation uses user.Current, SecurityDescriptorFromString and SetNamedSecurityInfo; no icacls/extra child/PATH lookup. It never publishes token bytes. Future native runtime qualification covers this compiled Windows dependency chain.','actual_domain_source_ref':contract['frozen_runtime_refs']['migrations/sqlite/0002_domain.sql'],'addon_is_not_numbered':True,'no_SQL_evaluated':True,'original_frozen_sources_unchanged':True,'Source_author':AUTHOR}
    save('supplemental-source-evidence.json',supplemental)
    note='''# old21 public bootstrap Source

The new public21_runner.py leaf reuses pinned accepted schema22 helpers, WindowsOwnedProcess and SourceReadGuard by reference. Every old Source byte remains untouched. The genuine qualified old21 Control argv is: control --bootstrap-owner --credential-file <new private Owner output>; cwd is its frozen_source and RESEARCHOS_DATA_DIR points to new source21. This is the actual finite administrative branch, with no HTTP serve or model/provider path. One suspended child is assigned to an unnamed kill-on-close Job before resume, timeout 90 seconds, all descendants owned, exact integer PID/FILETIME and idle/closed/zero-active evidence mandatory.

New request has only case_id (32 lowercase hex) and output_root (integration_codex/schema21-public-<id>, nonexistent and no alias ancestors). Only private/raw/tmp are made by the leaf. The old public Control alone creates researchos.sqlite: genuine original consecutive numbered SQL 1..21 plus original unnumbered next_v24_sessions.sql and installClientSessionFence in the real constructor. No user_version writer, artificial ledger, direct SQLite setup or copied old database.

After child success and closure, reject nonempty SQLite sidecars, set the database readonly, hold exact FILE_SHARE_READ Source guard and inspect SQLite with ro+immutable+query_only. Preserve genuine ledger, schema-definition hash, complete table count/row hashes, integrity and foreign-key result, and equal before/after/final DB byte pins. The synthetic oracle controls exercise rejection policy, not a database or Native PASS. Private generated Owner-file bytes are never read, copied, hashed or emitted. The fresh Owner fixture is retained privately; it has the original 15-minute lifetime and no provider access.

Root must supply a new separately reviewed caller with a distinct PUBLIC21_BOOTSTRAP_ONLY registration, dynamic current4, owner and finite lease. Do not reuse old21 BUILD/Main23/public22 scope. Its live methods authenticate full prior actual Root header/call/output and independent peer delivery, exact current Source HDF/MF/decision, full qualified Python/SQLite/native/runtime closure and the completed Root-bound old21 programme chain. JSON 7-key and 6-key bindings in the leaf only enforce shape/pin stability. They cannot create an issuer, scope or grant.

The completed pre-entry outer_host_binding_ref is the earlier real registration/qualification/activation/current4 observation. The full actual bootstrap tool call+return is captured by Root after return. Future data must stay null in Source. A stopped branch retains its complete returned state, stdout/stderr/invocation, actual exit or NULL, Job/guard cleanup and DB/private fixture metadata; Root allocates an original ordinal and preserves prior failure counters. No automatic retry, cleanup deletion, retrospective grant, formal acceptance or 20→24 claim.

W05-99 A04/C11/C15 and its sole final owner A04 remain unchanged. All 22 parent tasks and 42 formal cases remain final gates. This component Source preparation does not accept any case. Existing schema22 restore failure original1025 and original1109..1113 are preserved, not rerun. Future backup/restore/21→22/23→24 branches require their own exact contracts and independent qualification.
'''
    raw_new(Q/'README.source.md',note.encode('utf-8'))
    # All Python files are only AST/compile checked; no runtime entry is called.
    compiled=[]
    for path in sorted(Q.glob('*.py')):
        raw=path.read_bytes(); ast.parse(raw); compile(raw,str(path),'exec'); compiled.append(pin(path))
    static_ref=save('source-static-checks.json',{'schema':'researchos.schema21-public-bootstrap-static.v1','compiled_Source_refs':compiled,'Python_AST_compile_only':True,'Native_Go_SQL_model_TP':0,'entry_invoked':False,'same_existing_helpers_refs':{key:contract[key] for key in ('public22_helpers_ref','owned_job','source_guard')},'inverse_rule':'New leaf+contract only; shared accepted Source implementations are referenced with exact bytes and are never edited. No source fork of their functions.','future_caller_or_scope_created':False,'source_self_acceptance':False})
    guard_module=types.ModuleType('task87_seal_guard')
    gref=contract['source_guard']; raw=Path(gref['path']).read_bytes()
    need(len(raw)==gref['bytes'] and hashlib.sha256(raw).hexdigest()==gref['sha256'],'SEALED_GUARD_SOURCE_PIN')
    exec(compile(raw,gref['path'],'exec'),guard_module.__dict__)
    guard=guard_module.SourceReadGuard()
    own=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
    manifest=json.loads((Q/'input-manifest.json').read_bytes())
    refs=own+manifest['references']+[supplemental['private_file_source_ref']]
    normalized={}
    for ref in refs:
        key=ntpath.normcase(ntpath.normpath(ref['path'].replace('/','\\')))
        if key in normalized: need(normalized[key]['sha256']==ref['sha256'] and normalized[key]['bytes']==ref['bytes'],'FULL_SOURCE_CLOSURE_PIN')
        else: normalized[key]=ref
    try:
        guard.acquire([normalized[key] for key in sorted(normalized)])
    finally:
        closed=guard.close(); closure_ref=save('source-full-closure.guard.closed.json',closed)
    need(closed['closed'] is True and closed['retained_handles_count']==0 and closed['verification']=='PASSED' and not closed['errors'],'FULL_SOURCE_GUARD_CLOSED')
    boundary_ref=save('source-delivery-boundary.json',{'schema':'researchos.schema21-public-bootstrap-source-boundary.v1','source_author':AUTHOR,'Source_status':'PREPARED_PENDING_NONAUTHOR_REVIEW','pure_controls':56,'old_85_68_9Go_controls_or_builds_rerun':False,'product_processes':0,'SQL_connections':0,'model_TP_Canon_Main_old_Source_writes':0,'all_three_Source_guards_closed':True,'source_full_closure_ref':closure_ref,'source_tool_audit_ref':audit_ref,'Root_source_review_issuer':None,'future_Root_scope':None,'future_runtime_qualification':None,'runtime_branch_invoked':False,'formal_acceptance':False,'execution_grant':False,'Source_slot_STOP_after_seal':True,'original_failure_counter_owner':'codex:/root','new_original_failures_during_Task87':0,'original1025_1109_1113_retained':True})
    members=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file() and p.name not in ('HDF.json','MF.json')]
    mf_ref=save('MF.json',{'schema':'researchos.schema21-public-bootstrap-source-manifest.v1','Source_author':AUTHOR,'member_count':len(members),'members':members,'exclusions':['MF.json (manifest cannot include its own digest)','HDF.json (handoff references finalized manifest)','Actual final sealer tool result and later peer delivery do not exist before this write; Root captures originals after return, never fabricates them.'],'immutable_after_publish':True,'execution_grant':False,'formal_acceptance':False})
    hdf_ref=save('HDF.json',{'schema':'researchos.schema21-public-bootstrap-source-handoff.v1','status':'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW','source_author':AUTHOR,'source_author_thread':THREAD,'actual_parent_root_thread':ROOT_THREAD,'original_programme_source_author':contract['original_programme_source_author'],'manifest_ref':mf_ref,'runner_ref':pin(Q/'public21_runner.py'),'contract_ref':pin(Q/'contract.json'),'input_manifest_ref':pin(Q/'input-manifest.json'),'source_controls_ref':pin(Q/'source-controls.json'),'static_checks_ref':static_ref,'source_author_audit_ref':audit_ref,'source_full_closure_ref':closure_ref,'source_delivery_boundary_ref':boundary_ref,'old21_root_bound_programme_ref':contract['old21_qualification_ref'],'caller_requirement':'New separately reviewed strict Root PUBLIC21_BOOTSTRAP_ONLY caller/scope/runtime closure before Native execution. No actual grant from this Source.','new_one_shot_native_child_limit':1,'Source_native_SQL_Go_model_TP_calls':0,'all_Source_guards_closed_zero_handles':True,'pure_control_count':56,'Source_self_acceptance':False,'parent_acceptance':False,'formal_acceptance':False,'execution_grant':False,'future_Root_scope_ref':None,'future_runtime_qualification_ref':None,'STOP':True})
    final={'schema':'researchos.schema21-public-bootstrap-source-delivery.v1','operation':'SOURCE_PREPARATION','component':'OLD21_PUBLIC_BOOTSTRAP_RUNNER_SOURCE','source_author':AUTHOR,'hdf_ref':hdf_ref,'mf_ref':mf_ref,'runner_ref':pin(Q/'public21_runner.py'),'contract_ref':pin(Q/'contract.json'),'input_manifest_ref':pin(Q/'input-manifest.json'),'source_controls_ref':pin(Q/'source-controls.json'),'source_guard_ref':closure_ref,'pure_controls':56,'sealed_members':len(members),'Source_status':'PENDING_NONAUTHOR_REVIEW','formal_acceptance':False,'execution_grant':False,'Native_SQL_Go_model_TP_called':False,'STOP':True}
    print(json.dumps(final,ensure_ascii=False,sort_keys=True))
    return 0
if __name__=='__main__':
    code=1
    try: code=main()
    except BaseException: traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code)); sys.exit(code)

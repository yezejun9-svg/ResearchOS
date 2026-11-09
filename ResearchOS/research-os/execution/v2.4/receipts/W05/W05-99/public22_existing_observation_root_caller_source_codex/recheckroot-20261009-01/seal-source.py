"""Seal only Source; actual scope, registration, SQL and product runs remain absent."""
import hashlib,json,os,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
SELF_LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-49-27-01a11e22-ecb2-7720-80d2-af63727d414d.jsonl')
def main():
    m=types.ModuleType('seal_readonly_source');m.__file__=str(N/'public22_recheck_root.source.py')
    exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
    i=m.inputs();controls=m.doc(m.pin(N/'source-controls.json'));extra=m.doc(m.pin(N/'identity-and-scope-controls.json'));runtime=m.doc(m.pin(N/'runtime-closure-control.json'))
    m.need(all(v['status']=='PASS_SOURCE_ONLY' for v in (controls,extra,runtime)),'SOURCE_CONTROLS')
    chunks={'fc2641','3bf96e','4df3a2','5caa2c','c2d7b1','0f736c','a6c60f','e5ffb7','b4bece','8f3efa','7e23a1','72e203','4c3cc5','8edccc','35cbc3','6acd1a','ef226d','f242ab'}
    size=SELF_LOG.stat().st_size
    with SELF_LOG.open('rb') as f:
        header=f.readline();f.seek(max(len(header),size-64*1024*1024))
        if f.tell()!=len(header):f.readline()
        offset=f.tell();tail=f.read(size-offset)
    m.need(json.loads(header)['payload']['id']==os.environ['CODEX_THREAD_ID']=='01a11e22-ecb2-7720-80d2-af63727d414d','ACTUAL_SOURCE_THREAD')
    calls={};pairs={}
    for line in tail.splitlines(keepends=True):
        try:item=json.loads(line)
        except (ValueError,UnicodeDecodeError):offset+=len(line);continue
        p=item.get('payload',{});kind=p.get('type');cid=p.get('call_id')
        if kind in ('function_call','custom_tool_call') and cid:calls[cid]=(offset,line,item)
        elif kind in ('function_call_output','custom_tool_call_output') and cid in calls:
            for chunk in chunks:
                if chunk in str(p.get('output','')) and chunk not in pairs:pairs[chunk]=(calls[cid],(offset,line,item))
        offset+=len(line)
    m.need(set(pairs)==chunks,'COMPLETE_ACTUAL_SOURCE_TOOL_PAIRS')
    captures=[]
    for chunk,(call,result) in sorted(pairs.items()):
        path=N/('actual-Source-tool-'+chunk+'.raw.jsonl')
        with path.open('xb') as f:f.write(header+call[1]+result[1])
        ref=m.save(N,'actual-Source-tool-'+chunk+'.binding.json',dict(source_actor=m.AUTHOR,source_thread_id=os.environ['CODEX_THREAD_ID'],
            source_audit_path=str(SELF_LOG),source_prefix_size_observed=size,source_line_offsets=[0,call[0],result[0]],
            source_line_bytes=[len(v) for v in (header,call[1],result[1])],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in (header,call[1],result[1])],
            original_capture_ref=m.pin(path),original_call_id=call[2]['payload']['call_id'],chunk_id=chunk))
        captures.append(dict(chunk_id=chunk,binding_ref=ref,raw_ref=m.pin(path)))
    m.save(N,'original1043-diagnostic.json',dict(ordinal=1043,assignment_by='codex:/root',original_start_chunk='7e23a1',original_completion_chunk='72e203',
        original_session_id=61695,actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,
        actual_dispatcher_exit=None,actual_model_exit=None,original_status='FAILED_RETAINED',error='ValueError: UNREVIEWED_LOADED_RUNTIME',
        full_original_command_ref=m.pin(N/'original1043.command.ps1'),original_captures=[x for x in captures if x['chunk_id'] in ('7e23a1','72e203')],
        cause='Two explicit required Source Python modules were not listed in initial runtime-only manifest; strict gate correctly rejected.',
        initial_source_inputs_ref=m.pin(N/'source-inputs.initial.json'),initial_runtime_manifest_ref=m.pin(N/'runtime-resources.json'),
        corrected_runtime_manifest_ref=i['runtime_resources_ref'],strict_gate_weakened=False,subsequent_Source_control_ref=m.pin(N/'runtime-closure-control.json'),
        automatic_product_retry=False,counter_reset=False,original1025_result='FAILED_RETAINED'))
    m.save(N,'source-tool-capture-index.json',dict(actual_pairs=captures,SQL_queries=0,new_native_children=0,original_failures=[1043],
        warnings=[dict(chunk_id='e5ffb7',kind='SyntaxWarning',actual_final_exit=0,corrected_to_raw_regex=True)],counter_not_owned_by_source_author=True))
    contract=dict(schema='researchos.public22-existing-root-calling-contract.v1',status='SOURCE_ONLY_NO_EXECUTION_GRANT',source_author=m.AUTHOR,
        caller_ref=m.pin(N/'public22_recheck_root.source.py'),source_inputs_ref=m.pin(N/'source-inputs.json'),runtime_resources_ref=i['runtime_resources_ref'],
        leaf_hdf_ref=i['leaf_hdf_ref'],leaf_mf_ref=i['leaf_mf_ref'],leaf_review_hdf_ref=i['leaf_review_hdf_ref'],leaf_review_mf_ref=i['leaf_review_mf_ref'],
        leaf_review_decision_ref=i['leaf_review_decision_ref'],leaf_recheck_contract_ref=i['recheck_contract_ref'],original_case_request_ref=i['case_request_ref'],
        fixed_evidence=i['evidence'],source_review_schema='researchos.public22-existing-root-independent-source-decision.v1',source_review_decision='ACCEPTED_SOURCE_ONLY',
        source_review_required_fields=['schema','decision','actor_id','actor_role','source_author','source_hdf_ref','source_mf_ref','caller_ref','source_inputs_ref',
            'calling_contract_ref','runtime_resources_ref','readonly_only','original1025_result','execution_grant','formal_acceptance'],
        source_review_HDF_fields=['actor_id','reviewed_utc','manifest_ref','source_decision_ref'],
        source_review_constants=dict(actor_role='INDEPENDENT_NON_AUTHOR',source_author=m.AUTHOR,readonly_only=True,original1025_result='FAILED_RETAINED',execution_grant=False,formal_acceptance=False),
        modes=['build','check','activate','readonly-run'],Root_registration_request_schema='researchos.root-public22-existing-registration-request.v1',
        Root_registration_request_required_fields=['schema','issued_by','mode','formal_acceptance','parent_acceptance','case_request_ref','evidence',
            'source_hdf_ref','source_mf_ref','review_hdf_ref','review_mf_ref','review_decision_ref','leaf_review_audit_ref','review_audit_ref',
            'before_canonical_refs','expected_revisions','lease_id','lease_issued_at','lease_expires_at','recheck_id','registration_root','receipt_root','postreview_live_audit_ref','created_utc'],
        Root_actual_schema='researchos.root-public22-existing-actual-request.v1',Root_actual_required_fields=['schema','issued_by','formal_acceptance',
            'facts_ref','scope_ref','case_request_ref','current_canonical_refs','registration_result_ref','activation_audit_ref'],
        Root_activation_required_fields=['issued_by','facts_ref','before_canonical_refs','actual_audit_ref'],
        Root_canonical_registration=dict(slice_id=m.SLICE,ownership_subtask=m.KEY,state=m.STATE,checkpoint_scope_key='public22_existing_observation_scope_ref',checkpoint_facts_key='public22_existing_observation_facts_ref'),
        revision_policy='Root current full four refs plus exact expected revisions; CP>=371 and OW>=175; projection increments each pair by one, never hardcodes future372.',
        audit_policy=dict(Root_thread=m.ROOT_THREAD,Root_source_audit_path=m.ROOT_AUDIT,records=3,full_ref_JSON_required=True,
            actual_peer_author='/root/task',canonical_peer_actor='codex:/root/task',accepted_tool_names=['exec','functions.exec','other qualified .exec names']),
        argv_template=[m.doc(i['runtime_resources_ref'])['python_ref']['path'],'-I','-S','-B','-X','utf8',str(N/'public22_recheck_root.source.py'),
            '<mode>','<input-ref-path>','<input-ref-sha256>','<input-ref-bytes>','<activate-only-activation-ref-path/sha256/bytes>'],
        build_root_template=str(m.B/'integration_codex/public22-recheck-registration-<32hex>'),receipt_root_template=str(m.B/'integration_codex/public22-recheck-observation-<32hex>'),
        future_Root_scope=None,future_registration=None,future_request=None,future_lease=None,future_actual_observation=None,
        original1025_result='FAILED_RETAINED',original1043_result='FAILED_RETAINED',new_native_children=0,SQL_queries_during_Source=0,
        execution_grant=False,formal_acceptance=False,parent_acceptance=False)
    cref=m.save(N,'root-calling-contract.source.json',contract)
    all_refs=m.refs_unique(i['source_resource_refs']+m.doc(i['runtime_resources_ref'])['resource_refs']+[m.pin(p) for p in N.iterdir() if p.is_file()])
    m.need(not any(m.canonical(r['path']) in {m.canonical(str(p)) for p in m.CANON} for r in all_refs),'SOURCE_MUST_NOT_HOLD_CURRENT_CANON')
    guard=m.load(m.GUARD_REF,'final_Source_guard').SourceReadGuard(per_file_cap=m.MAX,total_cap=2*1024*1024*1024)
    try:
        guard.acquire(all_refs)
        for ref in all_refs:m.checked(ref)
    finally:
        cleanup=guard.close();cleanupref=m.save(N,'source-final-guard.closed.json',cleanup)
        m.need(cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0,'ALL_SOURCE_HANDLES_CLOSED')
    mf=m.save(N,'MF.json',dict(schema='researchos.public22-existing-root-source-manifest.v1',members=[m.pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
    hdf=m.save(N,'HDF.json',dict(schema='researchos.public22-existing-root-source-handoff.v1',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',
        source_author=m.AUTHOR,source_thread_id=os.environ['CODEX_THREAD_ID'],manifest_ref=mf,caller_ref=m.pin(N/'public22_recheck_root.source.py'),
        source_inputs_ref=m.pin(N/'source-inputs.json'),calling_contract_ref=cref,runtime_resources_ref=i['runtime_resources_ref'],
        source_controls_ref=m.pin(N/'source-controls.json'),peer_scope_controls_ref=m.pin(N/'identity-and-scope-controls.json'),
        runtime_control_ref=m.pin(N/'runtime-closure-control.json'),source_final_guard_ref=cleanupref,
        full_tool_capture_index_ref=m.pin(N/'source-tool-capture-index.json'),original1043_diagnostic_ref=m.pin(N/'original1043-diagnostic.json'),
        accepted_leaf_hdf_ref=i['leaf_hdf_ref'],accepted_leaf_review_hdf_ref=i['leaf_review_hdf_ref'],original_case_request_ref=i['case_request_ref'],
        fixed_nine_evidence=i['evidence'],finite_Source_checks=len(controls['controls'])+len(extra['controls'])+1,
        original1025_result='FAILED_RETAINED',original1043_result='FAILED_RETAINED',actual_Root_registration=False,actual_readonly_run=False,
        SQL_queries=0,new_native_children=0,new_Go_runs=0,new_model_calls=0,dispatcher_runs=0,Canon_modified=False,Main_modified=False,
        old_case_modified=False,private_owner_or_recovery_key_read=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,
        STOP='Independent non-author Source review before any fresh Root request, TP registration or readonly SQL observation.'))
    for ref in m.doc(mf)['members']:m.checked(ref)
    print(json.dumps(dict(status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',HDF=hdf,MF=mf,contract=cref,Source_checks=65),ensure_ascii=False))
if __name__=='__main__':main()

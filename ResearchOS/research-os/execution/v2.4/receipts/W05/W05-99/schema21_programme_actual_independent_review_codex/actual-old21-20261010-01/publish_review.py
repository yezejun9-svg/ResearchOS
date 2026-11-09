"""Issue a non-author programme provenance conclusion pending Root binding."""
from pathlib import Path
import datetime,hashlib,json,types,ntpath
N=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
C=B/'integration_codex/old21-caller-9c80f2c133f443bb8a2a629680cbba5d'
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def doc(r):return json.loads(Path(r['path'] if isinstance(r,dict) else r).read_bytes())
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
factsref=pin(N/'facts-review-checks.json');prefix=doc(factsref);tailref=pin(N/'facts-tail-review-checks.json');tail=doc(tailref);authref=pin(N/'authority-review-checks.json');auth=doc(authref)
assert factsref['sha256']=='4c99c92dd7088a92c39ba66feee65dffad170d8a300d4241c1a9fb35d4056346' and prefix['error']['type']=='JSONDecodeError' and prefix['checks'][-1]=='EXACT_LINK_IMPORTCFG_control'
assert tailref['sha256']=='113f7221224942fad725097aaf681bcdf175bc22d064ab948356c07e92ae47e7' and tail['status']=='FACTUAL_REVIEW_COMPLETED' and tail['error'] is None and tail['prefix_ref']==factsref and tail['full_source_prefix_rerun'] is False
facts={**prefix,'result':tail['result']}
assert auth['status']=='ROOT_ACTUAL_AUTHORITY_REVIEW_PASSED' and auth['error'] is None and auth['check_count']==192
sr=pin(C/'builder-returned-state.root.json');rr=pin(C/'caller-return.root.json');state=doc(sr);contract=doc(state['contract_ref']);runtime=doc(state['root_context']['resource_qualification_ref'])
own=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
inputrefs=[sr,rr,state['contract_ref'],contract['builder_ref'],contract['source_guard_ref'],contract['input_manifest_ref'],contract['frozen_source_manifest_ref'],state['closed_receipt']['ref'],state['source_before_ref'],state['source_after_ref'],state['frozen_before_ref'],state['frozen_after_ref'],state['root_context']['root_request_ref'],state['root_context']['scope_ref'],state['root_context']['registration_result_ref'],state['root_context']['resource_qualification_ref'],state['root_context']['runtime_manifest_ref'],auth['result']['root_complete_hostpair_seal_ref']]
source_root=Path(contract['builder_ref']['path']).parent
inputrefs += [pin(source_root/n) for n in ['HDF.json','MF.json']]
for ref in [state['root_context']['source_review_ref'],state['root_context']['caller_source_review_ref']]:inputrefs += [ref]
gm=types.ModuleType('old21_publication_guard');exec(compile(Path(contract['source_guard_ref']['path']).read_bytes(),contract['source_guard_ref']['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024)
try:
 guard.acquire(own+inputrefs)
 for ref in [facts['guard_ref'],tail['guard_ref'],auth['guard_ref']]:
  g=doc(ref);assert g['verification']=='PASSED' and g['closed'] is True and g['retained_handles_count']==0 and g['errors']==[]
 for p in N.glob('*.actual-host.binding.json'):
  binding=doc(p);parts=[]
  with Path(binding['source_audit_path']).open('rb') as f:
   for off,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
    f.seek(off);v=f.read(size);assert len(v)==size and hashlib.sha256(v).hexdigest()==digest;parts.append(v)
  assert b''.join(parts)==Path(binding['original_capture_ref']['path']).read_bytes()
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('publication-Source-guard.closed.json',closed)
frozen=doc(state['frozen_before_ref'])['refs'];frozenroot=state['calls'][0]['cwd'];frozenmap={ntpath.normcase(ntpath.normpath(r['path'])):r for r in frozen}
runtimecopies={name:frozenmap[ntpath.normcase(ntpath.normpath(ntpath.join(frozenroot,*name.split('/'))))] for name in contract['runtime_source_refs']}
diagnostics=[dict(original_failure_ordinal=1101,binding_ref=pin(N/'failure-befa0c.actual-host.binding.json')),dict(original_failure_ordinal=1102,binding_ref=pin(N/'failure-1102.actual-host.binding.json')),dict(original_failure_ordinal=1108,binding_ref=pin(N/'review-6bf827.actual-host.binding.json'))]
hostpairs=[dict(raw_ref=pin(p.with_name(p.name.replace('.binding.json','.raw.jsonl'))),binding_ref=pin(p)) for p in sorted(N.glob('review-*.actual-host.binding.json'),key=lambda p:doc(p)['source_line_offsets'][1])]
proof=dict(schema='researchos.old21-independent-programme-qualification.v1',status='QUALIFIED_OLD21_BUILD_PENDING_ROOT_BINDING',review_author='codex:/root/attach_fixture_source_review',source_author=contract['source_author'],caller_source_author='codex:/root/backup_regression_resources',build_executor='codex:/root',independent_non_author=True,root_thread_id=auth['result']['root_thread_id'],reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),program_refs=state['candidate_for_independent_review']['program_refs'],provenance_ref=state['closed_receipt']['ref'],source_commit=contract['source_commit'],source_tree=contract['source_tree'],historical_source_object_count=272,source_schema_version=21,database_schema_observation=None,frozen_source_manifest_ref=contract['frozen_source_manifest_ref'],input_manifest_ref=contract['input_manifest_ref'],frozen_source_root=frozenroot,original_runtime_source_refs=contract['runtime_source_refs'],frozen_runtime_source_refs=runtimecopies,public_bootstrap_source_refs=contract['public_bootstrap_source_refs'],builder_contract_ref=state['contract_ref'],builder_source_ref=contract['builder_ref'],caller_source_ref=runtime['caller_ref'],Root_actual_request_ref=state['root_context']['root_request_ref'],Root_scope_ref=state['root_context']['scope_ref'],Root_registration_result_ref=state['root_context']['registration_result_ref'],Root_complete_hostpair_seal_ref=auth['result']['root_complete_hostpair_seal_ref'],actual_caller_return_ref=rr,actual_builder_state_ref=sr,actual_runtime_qualification_ref=state['root_context']['resource_qualification_ref'],actual_runtime_manifest_ref=state['root_context']['runtime_manifest_ref'],full_closure_review_ref=factsref,full_closure_guard_ref=facts['guard_ref'],original_authority_review_ref=authref,authority_guard_ref=auth['guard_ref'],publication_guard_ref=gr,original_review_hostpairs=hostpairs,actual_Go_primary_exits=[x['actual_exit'] for x in state['calls']],actual_Go_process_identities=[dict(phase=x['phase'],pid=x['observation']['owned_child_pid'],creation_time_100ns=x['observation']['creation_time_100ns'],creation_time_100ns_decimal=str(x['observation']['creation_time_100ns'])) for x in state['calls']],individual_descendant_exit_codes=None,all_owned_jobs_idle_and_closed=True,original_held_input_count=facts['result']['original_input_count'],frozen_historical_and_module_input_count=facts['result']['frozen_input_count'],independently_held_ref_count=facts['held_ref_count'],review_checks=facts['check_count'],authority_checks=auth['check_count'],target_closures=facts['result']['targets'],original_API_process_stdout_truncated=True,original_process_stdout_complete=False,original_stdout_reconstructed=False,complete_original_API_records_verified=True,complete_Go_raw_streams_verified=True,independent_durable_return_exact_readback_verified=True,original_diagnostics_retained=diagnostics,Root_binding_required=True,Root_binding_ref=None,formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,historical_release_qualified=False,public_bootstrap_executed=False,backup_restore_executed=False,review_Go_runs=0,review_Native_runs=0,review_SQL_runs=0,review_dispatcher_runs=0,review_model_requests=0,Canon_written=False,formal_old21_case='OPEN',full20to24='OPEN')
proof.update(full_closure_review_prefix_status=prefix['status'],full_closure_review_prefix_diagnostic=prefix['error']['type'],pending_tail_review_ref=tailref,pending_tail_guard_ref=tail['guard_ref'],pending_tail_checks=tail['check_count'],full_source_prefix_rerun=False)
qr=save('programme-qualification.json',proof)
decision=dict(schema='researchos.old21-actual-programme-review-decision.v1',verdict=proof['status'],review_author=proof['review_author'],root_thread_id=proof['root_thread_id'],independent_non_author=True,qualification_ref=qr,program_refs=proof['program_refs'],source_commit=proof['source_commit'],source_tree=proof['source_tree'],facts_review_ref=factsref,authority_review_ref=authref,diagnostics=diagnostics,formal_acceptance=False,parent_acceptance=False,execution_grant=False,Root_binding_required=True)
dr=save('decision.json',decision)
mf=save('MF.json',dict(schema='researchos.old21-independent-programme-review-manifest.v1',members=own+inputrefs+[gr,qr,dr],recursive_business_history_traversed=False,formal_acceptance=False))
hdf=save('HDF.json',dict(schema='researchos.old21-independent-programme-review-handoff.v1',status=proof['status'],review_author=proof['review_author'],root_thread_id=proof['root_thread_id'],independent_non_author=True,qualification_ref=qr,decision_ref=dr,manifest_ref=mf,program_refs=proof['program_refs'],Root_binding_required=True,formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0))
print(json.dumps(dict(hdf_ref=hdf,mf_ref=mf,decision_ref=dr,qualification_ref=qr,publication_guard_ref=gr,status=proof['status'],formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True);print('PYTHON_EXIT_CODE=0',flush=True)

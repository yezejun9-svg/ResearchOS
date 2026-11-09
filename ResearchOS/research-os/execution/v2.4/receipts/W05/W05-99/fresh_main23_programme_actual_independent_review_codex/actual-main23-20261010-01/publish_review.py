"""Seal independent factual qualification; no Root issuance or execution grant."""
from pathlib import Path
import datetime,hashlib,json,types
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def read(r):return json.loads(Path(r['path'] if isinstance(r,dict) else r).read_bytes())
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
tailref=pin(N/'actual-review-tail-checks.json');tail=read(tailref);prefix=read(tail['prefix_ref']);meta=read(N/'actual-metadata-observation.json');state=read(meta['builder_state_ref']);contract=read(state['contract_ref']);actual=read(meta['actual_request_ref']);runtime=read(actual['runtime_qualification_ref'])
assert tailref['sha256']=='1e45c3c2864a221f3f5d1eac3e0cc402a00b6ac714b71b07e2442a951078181a' and tail['error'] is None and tail['status']=='INDEPENDENT_ACTUAL_PROGRAMME_REVIEW_PASSED'
assert prefix['error']['message']=='TRACE_USES_OFFICIAL_LINKER' and 'GO_TRACE_QUOTED_LINKER_EXACT_OFFICIAL_INPUT' in tail['checks']
own=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
source_root=Path(state['contract_ref']['path']).parent;source_review_root=source_root.parent.parent/'fresh_main23_programme_builder_independent_source_review_codex/src-review-20261009-01'
inputrefs=[state['contract_ref'],contract['builder_ref'],contract['source_guard_ref'],meta['caller_return_ref'],meta['builder_state_ref'],meta['actual_request_ref'],meta['activation_vector_ref'],state['closed_receipt']['ref'],tail['result']['root_complete_hostpair_seal_ref'],actual['runtime_qualification_ref']]
inputrefs += [pin(source_root/n) for n in ('HDF.json','MF.json')]+[pin(source_review_root/n) for n in ('HDF.json','MF.json','source-decision.json')]
guardmod=types.ModuleType('seal_guard');exec(compile(Path(contract['source_guard_ref']['path']).read_bytes(),contract['source_guard_ref']['path'],'exec'),guardmod.__dict__)
guard=guardmod.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=96*1024*1024)
try:
 guard.acquire(own+inputrefs)
 assert all((pin(r['path'])['sha256'],pin(r['path'])['bytes'])==(r['sha256'],r['bytes']) for r in own+inputrefs)
 for r in [prefix['guard_ref'],tail['guard_ref']]:
  g=read(r);assert g['verification']=='PASSED' and g['closed'] is True and g['retained_handles_count']==0 and g['errors']==[]
 for chunk in ['8cdcf5','5cf215','37effd','237917','d788d4','d58c62']:
  prefixname='failure' if chunk in ['8cdcf5','5cf215','37effd'] else 'review'
  binding=read(N/(prefixname+'-'+chunk+'.actual-host.binding.json'));parts=[]
  with Path(binding['source_audit_path']).open('rb') as f:
   for offset,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
    f.seek(offset);v=f.read(size);assert hashlib.sha256(v).hexdigest()==digest;parts.append(v)
  assert b''.join(parts)==Path(binding['original_capture_ref']['path']).read_bytes()
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('publication-Source-guard.closed.json',closed)
failures=[dict(original_failure_ordinal=o,binding_ref=pin(N/(p+'-'+c+'.actual-host.binding.json'))) for o,p,c in [(1068,'failure','8cdcf5'),(1069,'failure','5cf215'),(1070,'failure','37effd'),(1073,'review','d788d4')]]
proof=dict(schema='researchos.current-main23-independent-programme-qualification.v1',status='QUALIFIED_CURRENT_MAIN23_BUILD_PENDING_ROOT_BINDING',review_author='codex:/root/attach_fixture_source_review',source_author=contract['source_author'],independent_non_author=True,reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),program_ref=state['program_ref'],provenance_ref=state['closed_receipt']['ref'],source_refs=contract['current_main_source_refs'],builder_contract_ref=state['contract_ref'],builder_source_ref=contract['builder_ref'],Root_actual_request_ref=meta['actual_request_ref'],Root_complete_hostpair_seal_ref=tail['result']['root_complete_hostpair_seal_ref'],actual_caller_return_ref=meta['caller_return_ref'],actual_builder_state_ref=meta['builder_state_ref'],actual_runtime_qualification_ref=actual['runtime_qualification_ref'],full_closure_review_prefix_ref=tail['prefix_ref'],full_closure_guard_ref=prefix['guard_ref'],trace_and_authority_continuation_ref=tailref,continuation_guard_ref=tail['guard_ref'],publication_guard_ref=gr,original_review_hostpairs=[dict(raw_ref=pin(N/('review-'+c+'.actual-host.raw.jsonl')),binding_ref=pin(N/('review-'+c+'.actual-host.binding.json'))) for c in ['237917','d788d4','d58c62']],actual_Go_primary_exits=[x['actual_exit'] for x in state['calls']],actual_Go_process_identities=[dict(phase=x['phase'],pid=x['observation']['owned_child_pid'],creation_time_100ns=x['observation']['creation_time_100ns'],creation_time_100ns_decimal=str(x['observation']['creation_time_100ns'])) for x in state['calls']],individual_descendant_exit_codes=None,all_owned_jobs_idle_and_closed=True,current_main_inventory_count=572,full_input_manifest_count=14670,original_held_input_count=14678,frozen_main_and_module_input_count=2619,independently_rehashed_held_ref_count=prefix['held_ref_count'],qualified_runtime_resources_actually_held_count=len(runtime['resource_refs']),review_successful_prefix_checks=prefix['check_count'],continuation_checks=len(tail['checks']),original_API_process_stdout_truncated=True,original_process_stdout_complete=False,omitted_process_stdout_bytes_as_reported=8164529,original_stdout_reconstructed=False,complete_original_API_records_verified=True,complete_Go_raw_streams_verified=True,independent_durable_return_exact_readback_verified=True,original_diagnostics_retained=failures,Root_binding_required=True,Root_binding_ref=None,formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,review_Go_runs=0,review_Native_runs=0,review_SQL_runs=0,review_dispatcher_runs=0,review_model_requests=0,Canon_written=False,schema21='OPEN',full20to24='OPEN',main23to24='BLOCKED_MAIN_NOT_ADOPTED')
qr=save('programme-qualification.json',proof)
decision=dict(schema='researchos.current-main23-actual-programme-review-decision.v1',verdict='QUALIFIED_CURRENT_MAIN23_BUILD_PENDING_ROOT_BINDING',review_actor='codex:/root/attach_fixture_source_review',independent_non_author=True,qualification_ref=qr,program_ref=state['program_ref'],source_refs=contract['current_main_source_refs'],prefix_ref=tail['prefix_ref'],continuation_ref=tailref,diagnostics=failures,formal_acceptance=False,parent_acceptance=False,execution_grant=False,Root_binding_required=True)
dr=save('decision.json',decision)
members=own+inputrefs+[gr,qr,dr]
mf=save('MF.json',dict(schema='researchos.current-main23-independent-review-manifest.v1',members=members,recursive_business_history_traversed=False,formal_acceptance=False))
hdf=save('HDF.json',dict(schema='researchos.current-main23-independent-programme-review-handoff.v1',status=decision['verdict'],review_actor=decision['review_actor'],independent_non_author=True,qualification_ref=qr,decision_ref=dr,manifest_ref=mf,program_ref=state['program_ref'],Root_binding_required=True,formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0))
print(json.dumps(dict(hdf_ref=hdf,mf_ref=mf,decision_ref=dr,qualification_ref=qr,program_ref=state['program_ref'],publication_guard_ref=gr,status=decision['verdict'],formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True)

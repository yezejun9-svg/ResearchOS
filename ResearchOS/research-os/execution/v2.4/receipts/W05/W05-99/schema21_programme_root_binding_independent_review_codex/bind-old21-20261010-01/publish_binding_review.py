from pathlib import Path
import json,hashlib,types,datetime
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def doc(r):return json.loads(Path(r['path'] if isinstance(r,dict) else r).read_bytes())
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
prefixref=pin(N/'review-checks.json');prefix=doc(prefixref);tailref=pin(N/'tail-review-checks.json');tail=doc(tailref)
assert prefixref['sha256']=='c9b3ae0ad0bb2b0e0a0c4cadc58cf8fede459e9d31ede5b6231e9b4777513a9f' and prefix['check_count']==300 and prefix['error']['message']=='UNIQUE_ACTUAL_TOOL_RESULT_ce7571'
assert tailref['sha256']=='de9d90f24737c0b2bd90a8b2a932b7df671a9e28c9346f1be75c921a7aa662c3' and tail['status']=='ROOT_PROGRAMME_BINDING_VERIFIED' and tail['error'] is None and tail['prefix_ref']==prefixref and tail['prefix_rerun'] is False
boundref=tail['result']['bound_qualification_ref'];bound=doc(boundref);assert boundref['sha256']=='8b5d6565586e51be741fa25b2f79cf41c55d0f8733c43d0f6a60f2ebca738a70'
guardref=next(x for x in prefix['held_ref_manifest'] if x['path'].endswith('source_read_guard.py'))
gm=types.ModuleType('binding_publication_guard');exec(compile(Path(guardref['path']).read_bytes(),guardref['path'],'exec'),gm.__dict__)
own=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
inputs=[boundref,bound['payload_ref'],bound['root_issuance_binding_ref'],bound['independent_peer_delivery_binding_ref'],guardref]
guard=gm.SourceReadGuard(per_file_cap=16*1024*1024,total_cap=64*1024*1024)
try:
 guard.acquire(own+inputs)
 for r in [prefix['guard_ref'],tail['guard_ref']]:
  g=doc(r);assert g['verification']=='PASSED' and g['closed'] is True and g['retained_handles_count']==0 and g['errors']==[]
 for chunk,outer,python in [('ef73f6',1,1),('0f6974',1,None),('dc58aa',0,0)]:
  binding=doc(N/('review-'+chunk+'.actual-host.binding.json'));parts=[]
  assert binding['outer_exit']==outer and binding['python_exit']==python
  with Path(binding['source_audit_path']).open('rb') as f:
   for off,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
    f.seek(off);v=f.read(size);assert len(v)==size and hashlib.sha256(v).hexdigest()==digest;parts.append(v)
  assert b''.join(parts)==Path(binding['original_capture_ref']['path']).read_bytes()
 assert (N/'continue_binding.v2.py').read_bytes().replace(b'per_file_cap=16*1024*1024,total_cap=64*1024*1024',b'per_file_cap=128*1024*1024,total_cap=64*1024*1024')==(N/'continue_binding.py').read_bytes()
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('publication-Source-guard.closed.json',closed)
diagnostics=[dict(original_failure_ordinal=o,raw_ref=pin(N/('review-'+c+'.actual-host.raw.jsonl')),binding_ref=pin(N/('review-'+c+'.actual-host.binding.json'))) for o,c in [(1114,'ef73f6'),(1115,'0f6974')]]
decision=dict(schema='researchos.old21-root-programme-binding-independent-review-decision.v1',verdict='ROOT_PROGRAMME_BINDING_VERIFIED',review_author='codex:/root/attach_fixture_source_review',binding_issuer='codex:/root',root_thread_id=bound['root_thread_id'],reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bound_qualification_ref=boundref,prior_programme_review_refs=bound['review_refs'],program_refs=bound['program_refs'],provenance_ref=bound['provenance_ref'],source_commit=bound['source_commit'],source_tree=bound['source_tree'],source_schema_version=21,successful_prefix_ref=prefixref,successful_prefix_checks=300,pending_tail_completed_ref=tailref,pending_tail_checks=57,prefix_guard_ref=prefix['guard_ref'],tail_guard_ref=tail['guard_ref'],publication_guard_ref=gr,original_root_issuance_binding_ref=bound['root_issuance_binding_ref'],actual_reviewer_FINAL_binding_ref=bound['independent_peer_delivery_binding_ref'],original_root_operation='OLD21_PROGRAMME_QUALIFICATION_BINDING',original_compact_actual_chunk_id='7ba7fd',original_compact_outer_exit=0,original_compact_python_exit=0,requested_ref_count=136,root_held_source_count=133,observed_real_FINAL_gap_seconds=0.001,root_issuer_finalized_programme_qualification=True,formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,database_schema_observation=None,public_bootstrap_executed=False,backup_restore_executed=False,formal_old21_case='OPEN',full20to24='OPEN',previous_controls_rerun=False,new_product_runs=0,new_Go_runs=0,new_Native_runs=0,new_SQL_runs=0,new_model_requests=0,live_canonical_read_or_held=False,Canon_written=False,historical_canonical_revisions=[375,179,40],original_diagnostics_retained=diagnostics)
dr=save('decision.json',decision)
mf=save('MF.json',dict(schema='researchos.old21-root-programme-binding-review-manifest.v1',members=own+inputs+[gr,dr],recursive_business_history_traversed=False,formal_acceptance=False))
hdf=save('HDF.json',dict(schema='researchos.old21-root-programme-binding-review-handoff.v1',status=decision['verdict'],review_author=decision['review_author'],root_thread_id=bound['root_thread_id'],bound_qualification_ref=boundref,decision_ref=dr,manifest_ref=mf,prefix_checks=300,tail_checks=57,formal_acceptance=False,parent_acceptance=False,execution_grant=False,new_product_runs=0,all_review_guards_closed=True,retained_handles_count=0))
print(json.dumps(dict(hdf_ref=hdf,mf_ref=mf,decision_ref=dr,publication_guard_ref=gr,status=decision['verdict'],formal_acceptance=False,parent_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True)

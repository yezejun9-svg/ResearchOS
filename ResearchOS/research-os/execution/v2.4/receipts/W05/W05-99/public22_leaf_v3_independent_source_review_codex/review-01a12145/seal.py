"""Seal real independent reviewer hostpair and exact source identity."""
import json
from pathlib import Path
import runpy
N=Path(__file__).resolve().parent
x=runpy.run_path(str(N/'review.py'),run_name='definitions_only');pin,read,save,mod=x['pin'],x['read'],x['save'],x['mod']
capture_module=mod(x['R']/'execution/v2.4/receipts/W09/W09-99/cp370_actual_registration_independent_review_codex/actualr4-01a120ab/review.py');capture_module.N=N
audit=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
cap=capture_module.capture(audit,40928429,'9fdc67','review-complete')
assert cap['result']['exit_code']==0
lines=cap['result']['output'].splitlines();published=json.loads(lines[0]);assert lines[-1]=='LEAF_V3_REVIEW_PYTHON_EXIT=0'
for key,name in [('HDF','HDF.json'),('MF','MF.json'),('decision','decision.json'),('next_root_recheck_contract','next-root-recheck-contract.json')]:assert published[key]==pin(N/name)
reviewer=json.loads(cap['rows'][0][1])['payload']
assert reviewer['id']=='01a11e76-4e37-7a21-a388-2c5f2e3c9ebf' and reviewer['source']['subagent']['thread_spawn']['agent_path']=='/root/attach_fixture_source_review'
h=read(N/'HDF.json');s=read(x['S']/'HDF.json');sm=read(s['manifest_ref']['path'])
ab=next(r for r in sm['members'] if Path(r['path']).name=='v3-source-controls.actual-fullhostpair.binding.json');binding=read(ab['path']);author=json.loads(Path(binding['capture_ref']['path']).read_bytes().splitlines()[0])['payload']
assert author['id']!=reviewer['id'] and author['source']['subagent']['thread_spawn']['agent_path']=='/root/w09_formal_profile_source_impl'
refs=[pin(__file__),*[published[k] for k in ('HDF','MF','decision','next_root_recheck_contract')],h['independent_controls_ref'],h['source_guard_ref'],cap['cap_ref'],cap['binding_ref'],ab,binding['capture_ref']]
guard=mod(read(s['contract_ref']['path'])['source_guard']['path']).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
try:
 with audit.open('rb') as f:
  for offset,line in cap['rows']:f.seek(offset);assert f.read(len(line))==line
 assert all(pin(r['path'])['sha256']==r['sha256'] and pin(r['path'])['bytes']==r['bytes'] for r in refs)
 assert read(h['source_guard_ref']['path'])['closed'] and read(h['source_guard_ref']['path'])['retained_handles_count']==0
 assert read(h['independent_controls_ref']['path'])['failed']==[]
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('seal-source-guard.closed.json',closed)
seal=save('complete-hostpair-seal.json',dict(decision='ACCEPTED_SOURCE_ONLY',review_refs={k:published[k] for k in ('HDF','MF','decision','next_root_recheck_contract')},actual_review_host_capture_ref=cap['cap_ref'],actual_review_host_binding_ref=cap['binding_ref'],actual_outer_exit=0,actual_python_exit=0,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,reviewer_actor='codex:/root/attach_fixture_source_review',reviewer_session_id=reviewer['id'],source_author_actor='codex:/root/w09_formal_profile_source_impl',source_author_session_id=author['id'],source_author_actual_binding_ref=ab,independent_non_author_identity_verified=True,source_guard_ref=gr,checks=1964,held_review_refs=916,blocking_findings=0,new_original_failures=[],original1025_retained_failed=True,new_product_children=0,Root_scope_registered=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False))
print(json.dumps(dict(seal=seal,review_refs={k:published[k] for k in ('HDF','MF','decision','next_root_recheck_contract')},host_capture=cap['cap_ref'],host_binding=cap['binding_ref']),ensure_ascii=False),flush=True)

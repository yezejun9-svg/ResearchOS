"""Preserve exact host IO and reviewer identity; no operational execution."""
import json
from pathlib import Path
import runpy
N=Path(__file__).resolve().parent
x=runpy.run_path(str(N/'review.py'),run_name='definitions_only');pin,read,save,mod=x['pin'],x['read'],x['save'],x['mod']
previous=mod(x['R']/'execution/v2.4/receipts/W09/W09-99/cp370_actual_registration_independent_review_codex/actualr4-01a120ab/review.py');previous.N=N
audit=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
captures=[]
for chunk,name,outer in [('209e27','diagnostic-rg',0),('3fd207','diagnostic-caller-path',0),('794d07','diagnostic-review-recursion',1),('2a8f99','initial-review',0),('6bdaab','resolved-review',0)]:
 cap=previous.capture(audit,40928429,chunk,name);assert cap['result']['exit_code']==outer;captures.append(cap)
cap=captures[-1];lines=cap['result']['output'].splitlines();published=json.loads(lines[0]);assert lines[-1]=='RESOLUTION_PYTHON_EXIT=0'
for k,name in [('HDF','HDF.resolved.json'),('MF','MF.resolved.json'),('decision','decision.resolved.json'),('resolution','review-resolution.json')]:assert published[k]==pin(N/name)
header=json.loads(cap['rows'][0][1]);assert header['payload']['id']=='01a11e76-4e37-7a21-a388-2c5f2e3c9ebf'
identity=read(x['PR']/'actual-actor-identity-chain.json')
refs=[pin(__file__),*[published[k] for k in ('HDF','MF','decision','resolution')],pin(x['PR']/'actual-actor-identity-chain.json')]
for capture in captures:refs.extend((capture['cap_ref'],capture['binding_ref']))
guard=mod(x['B']/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py').SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
guard.acquire(refs)
try:
 for capture in captures:
  with audit.open('rb') as f:
   for offset,line in capture['rows']:f.seek(offset);assert f.read(len(line))==line
 assert all(pin(r['path'])==r for r in refs)
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('host-seal.source-guard.closed.json',closed)
out=save('complete-hostpair-seal.json',dict(decision=read(N/'decision.resolved.json')['decision'],review_refs={k:published[k] for k in ('HDF','MF','decision','resolution')},actual_review_host_capture_ref=cap['cap_ref'],actual_review_host_binding_ref=cap['binding_ref'],prior_review_host_capture_ref=captures[-2]['cap_ref'],prior_review_host_binding_ref=captures[-2]['binding_ref'],actual_outer_exit=0,actual_python_exit=0,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,reviewer_actor=x['ACTOR'],reviewer_session_id=header['payload']['id'],prior_verified_actor_identity_chain_ref=pin(x['PR']/'actual-actor-identity-chain.json'),source_guard_ref=gr,read_diagnostic_captures=[dict(chunk=c['result']['chunk_id'],capture_ref=c['cap_ref'],binding_ref=c['binding_ref'],actual_outer_exit=c['result']['exit_code'],actual_python_exit=1 if i==2 else None,actual_native_exit=None,root_assigned_ordinal=1027+i if i<2 else None) for i,c in enumerate(captures[:3])],review_assertion_schema_diagnostic=dict(capture_ref=captures[-2]['cap_ref'],binding_ref=captures[-2]['binding_ref'],actual_outer_exit=0,actual_python_exit=0,actual_native_exit=None,resolution_ref=published['resolution'],Root_assignment_required=True),checks_resolved=6860,held_review_refs=884,formal_acceptance=False,parent_acceptance=False,execution_grant=False,product_executions_by_reviewer=0,original1025_preserved=True))
print(json.dumps(dict(seal=out,review_refs={k:published[k] for k in ('HDF','MF','decision','resolution')},host_capture=cap['cap_ref'],host_binding=cap['binding_ref'],diagnostic_captures=[dict(chunk=c['result']['chunk_id'],capture=c['cap_ref'],binding=c['binding_ref']) for c in captures[:4]]),ensure_ascii=False),flush=True)

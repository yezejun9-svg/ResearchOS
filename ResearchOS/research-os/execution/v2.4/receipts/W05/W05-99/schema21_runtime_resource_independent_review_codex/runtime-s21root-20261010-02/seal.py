"""Seal exact original review host pair and verify every delivery manifest member."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,types
N=Path(__file__).resolve().parent
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
def pin(p):
 v=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def same(a,b):return os.path.normcase(os.path.abspath(a['path']))==os.path.normcase(os.path.abspath(b['path'])) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def read(r):return json.loads(Path(r['path'] if isinstance(r,dict) else r).read_bytes())
def save(n,x,raw=False):
 p=N/n
 with p.open('xb') as f:f.write(x if raw else (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
calls={};found=None
with P.open('rb') as f:
 header=f.readline();offset=len(header)
 for raw in f:
  row=json.loads(raw);payload=row.get('payload',{});cid=payload.get('call_id')
  if cid and payload.get('type') in ('custom_tool_call','function_call'):calls[cid]=(offset,raw)
  if cid and payload.get('type') in ('custom_tool_call_output','function_call_output'):
   output=str(payload.get('output',''))
   if '"chunk_id":"a03f65"' in output or '"chunk_id": "a03f65"' in output:found=(calls[cid],(offset,raw),cid)
  offset+=len(raw)
assert found is not None
(a,ar),(b,br),cid=found
rr=save('review-a03f65.actual-host.raw.jsonl',header+ar+br,True)
binding=save('review-a03f65.actual-host.binding.json',dict(schema='researchos.independent-runtime-review-actual-host-binding.v1',review_actor='codex:/root/attach_fixture_source_review',source_audit_path=str(P),source_prefix_size_observed=offset,source_line_offsets=[0,a,b],source_line_bytes=[len(header),len(ar),len(br)],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in [header,ar,br]],original_call_id=cid,original_capture_ref=rr,outer_exit=0,python_exit=0,formal_acceptance=False,execution_grant=False))
hr,mr,dr=[pin(N/n) for n in ('HDF.json','MF.json','decision.json')];h,m,d=read(hr),read(mr),read(dr)
source=read(h['source_hdf_ref']);builder=read(h['builder_contract_ref']);runtime=read(h['runtime_manifest_ref']);scope=read(h['qualification_scope_ref'])
refs=m['members']+[hr,mr,rr,binding,pin(__file__)]
unique={}
for r in refs:
 k=os.path.normcase(os.path.abspath(r['path']));assert k not in unique or same(unique[k],r);unique[k]=r
g=types.ModuleType('seal_guard');exec(compile(Path(builder['source_guard_ref']['path']).read_bytes(),builder['source_guard_ref']['path'],'exec'),g.__dict__)
guard=g.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=192*1024*1024)
try:
 guard.acquire(list(unique.values()))
 assert all(same(pin(r['path']),r) for r in unique.values())
 assert h['schema']=='researchos.old21-runtime-independent-review-hdf.v2' and d['schema']=='researchos.old21-runtime-independent-review-decision.v2'
 assert h['review_author']==d['review_author']=='codex:/root/attach_fixture_source_review'
 assert h['source_author']==d['source_author']=='codex:/root/backup_regression_resources'
 assert h['builder_source_author']==d['builder_source_author']=='codex:/root/native_temp_independent_review'
 assert h['root_thread_id']==d['root_thread_id']==runtime['root_thread_id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
 assert same(h['manifest_ref'],mr) and same(h['decision_ref'],dr) and any(same(x,dr) for x in m['members'])
 assert d['verdict']=='RUNTIME_CLOSURE_ACCEPTED' and d['independent_non_author'] is True and d['resource_refs']==runtime['resource_refs']
 for key in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','qualification_scope_ref','python_ref','go_ref','runtime_manifest_ref'):assert same(h[key],d[key])
 for key in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','qualification_scope_ref','python_ref','go_ref'):assert same(h[key],runtime[key])
 assert h['formal_acceptance'] is d['formal_acceptance'] is False and h['execution_grant'] is d['execution_grant'] is False and h['programme_qualification'] is d['programme_qualification'] is None
 assert datetime.fromisoformat(scope['created_utc'])<=datetime.fromisoformat(h['reviewed_utc'])<=datetime.now(timezone.utc)<datetime.fromisoformat(scope['lease_expires_at'])
 oldg=read(h['Source_guard_ref']);assert oldg['verification']=='PASSED' and oldg['closed'] is True and oldg['retained_handles_count']==0 and oldg['errors']==[]
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('delivery-Source-guard.closed.json',closed)
out=save('complete-hostpair-seal.json',dict(schema='researchos.old21-runtime-review-complete-hostpair-seal.v1',review_hdf_ref=hr,review_mf_ref=mr,review_decision_ref=dr,original_hostpair_raw_ref=rr,original_hostpair_binding_ref=binding,publication_guard_ref=gr,every_MF_member_checked=True,held_refs=len(unique),failed_checks=0,programme_qualification=None,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(seal_ref=out,HDF=hr,MF=mr,decision=dr,raw_ref=rr,binding_ref=binding,guard_ref=gr,all_MF_members_checked=True,closed_zero=True),ensure_ascii=False),flush=True)

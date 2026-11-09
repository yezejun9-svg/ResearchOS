"""Bind actual review IO and verify unchanged own_review Source prefix only."""
from pathlib import Path
import ast,hashlib,json,os,types
N=Path(__file__).resolve().parent
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def same(a,b):return os.path.normcase(os.path.abspath(a['path']))==os.path.normcase(os.path.abspath(b['path'])) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def checked(r):
 assert same(pin(r['path']),r);return Path(r['path']).read_bytes()
def doc(r):return json.loads(checked(r))
def manifest(r):
 x=doc(r)
 for item in x['members']:checked(item)
 return x
def need(x,n):
 if not x:raise ValueError(n)
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
   if '"chunk_id":"1b8d2f"' in output or '"chunk_id": "1b8d2f"' in output:found=(calls[cid],(offset,raw),cid)
  offset+=len(raw)
assert found is not None
(a,ar),(b,br),cid=found
rr=save('review-1b8d2f.actual-host.raw.jsonl',header+ar+br,True)
binding=save('review-1b8d2f.actual-host.binding.json',dict(schema='researchos.independent-source-review-actual-host-binding.v1',review_actor='codex:/root/attach_fixture_source_review',source_audit_path=str(P),source_prefix_size_observed=offset,source_line_offsets=[0,a,b],source_line_bytes=[len(header),len(ar),len(br)],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in [header,ar,br]],original_call_id=cid,original_capture_ref=rr,outer_exit=0,python_exit=0,formal_acceptance=False,execution_grant=False))
hr,mr,dr=[pin(N/n) for n in ('HDF.json','MF.json','decision.json')];h,m,d=doc(hr),doc(mr),doc(dr)
sh=doc(h['source_hdf_ref']);calling=doc(sh['contract_ref']);builder=doc(calling['builder_contract_ref'])
refs=m['members']+[hr,mr,rr,binding,pin(__file__)];unique={}
for r in refs:
 k=os.path.normcase(os.path.abspath(r['path']));assert k not in unique or same(unique[k],r);unique[k]=r
g=types.ModuleType('seal_guard');exec(compile(checked(builder['source_guard_ref']),builder['source_guard_ref']['path'],'exec'),g.__dict__)
guard=g.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=64*1024*1024)
try:
 guard.acquire(list(unique.values()))
 for r in unique.values():checked(r)
 assert d['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' and d['review_author']=='codex:/root/attach_fixture_source_review'
 # Extract only the non-author own_review assertions before any Root witness read.
 tree=ast.parse(checked(sh['caller_ref']));function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='own_review')
 boundary=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='witness' for t in n.targets))
 prefix=ast.fix_missing_locations(ast.Module(body=function.body[:boundary],type_ignores=[]))
 request=dict(source_hdf_ref=h['source_hdf_ref'],source_mf_ref=h['source_mf_ref'],review_hdf_ref=hr,review_mf_ref=mr,review_decision_ref=dr)
 env=dict(request=request,doc=doc,manifest=manifest,pin=pin,same_ref=same,need=need,ROOT='codex:/root',AUTHOR='codex:/root/backup_regression_resources',__file__=sh['caller_ref']['path'])
 exec(compile(prefix,sh['caller_ref']['path']+'#read-only-own-review-prefix','exec'),env)
 for key,ref in [('source_hdf_ref',h['source_hdf_ref']),('source_mf_ref',h['source_mf_ref']),('caller_ref',sh['caller_ref']),('registrar_ref',sh['registrar_ref']),('calling_contract_ref',sh['contract_ref'])]:assert d[key]==ref
 oldg=doc(h['Source_guard_ref']);assert oldg['verification']=='PASSED' and oldg['closed'] is True and oldg['retained_handles_count']==0 and oldg['errors']==[]
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('delivery-Source-guard.closed.json',closed)
out=save('complete-hostpair-seal.json',dict(schema='researchos.old21-Source03-review-seal.v1',review_hdf_ref=hr,review_mf_ref=mr,review_decision_ref=dr,original_hostpair_raw_ref=rr,original_hostpair_binding_ref=binding,publication_guard_ref=gr,every_MF_member_checked=True,actual_own_review_non_author_prefix_passed=True,Root_witness_segment_executed=False,exact_original_ref_objects_preserved=True,held_refs=len(unique),runtime_qualification=None,programme_qualification=None,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(seal_ref=out,HDF=hr,MF=mr,decision=dr,raw_ref=rr,binding_ref=binding,guard_ref=gr,own_review_Source_prefix_passed=True,closed_zero=True),ensure_ascii=False),flush=True)

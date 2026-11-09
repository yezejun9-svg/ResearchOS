from pathlib import Path
import hashlib,json,types
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def doc(r):return json.loads(Path(r['path'] if isinstance(r,dict) else r).read_bytes())
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
h=doc(N/'HDF.json');m=doc(h['manifest_ref']);d=doc(h['decision_ref'])
guardref=next(x for x in m['members'] if x['path'].endswith('source_read_guard.py'))
gm=types.ModuleType('final_binding_review_guard');exec(compile(Path(guardref['path']).read_bytes(),guardref['path'],'exec'),gm.__dict__)
inputs=m['members']+[pin(N/'HDF.json'),pin(N/'MF.json'),pin(__file__),pin(N/'review-5c378d.actual-host.raw.jsonl'),pin(N/'review-5c378d.actual-host.binding.json')]
guard=gm.SourceReadGuard(per_file_cap=16*1024*1024,total_cap=64*1024*1024)
try:
 guard.acquire(inputs)
 for r in inputs:
  actual=pin(r['path']);assert (actual['sha256'],actual['bytes'])==(r['sha256'],r['bytes'])
 binding=doc(N/'review-5c378d.actual-host.binding.json');parts=[]
 with Path(binding['source_audit_path']).open('rb') as f:
  for off,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
   f.seek(off);v=f.read(size);assert len(v)==size and hashlib.sha256(v).hexdigest()==digest;parts.append(v)
 assert b''.join(parts)==Path(binding['original_capture_ref']['path']).read_bytes() and binding['outer_exit']==binding['python_exit']==0
 assert h['status']==d['verdict']=='ROOT_PROGRAMME_BINDING_VERIFIED' and d['formal_acceptance'] is d['parent_acceptance'] is d['execution_grant'] is False
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('delivery-Source-guard.closed.json',closed)
seal=save('complete-hostpair-seal.json',dict(schema='researchos.old21-root-binding-review-complete-hostpair-seal.v1',hdf_ref=pin(N/'HDF.json'),mf_ref=pin(N/'MF.json'),decision_ref=pin(N/'decision.json'),publication_actual_raw_ref=pin(N/'review-5c378d.actual-host.raw.jsonl'),publication_actual_binding_ref=pin(N/'review-5c378d.actual-host.binding.json'),all_manifest_members_verified=True,manifest_member_count=len(m['members']),guard_ref=gr,formal_acceptance=False,parent_acceptance=False,execution_grant=False))
print(json.dumps(dict(complete_hostpair_seal_ref=seal,guard_ref=gr,manifest_member_count=len(m['members'])),ensure_ascii=False),flush=True)

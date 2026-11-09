from pathlib import Path
import json,hashlib,types
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def doc(p):return json.loads(Path(p['path'] if isinstance(p,dict) else p).read_bytes())
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
hdf=doc(N/'HDF.json');mf=doc(hdf['manifest_ref']);proof=doc(hdf['qualification_ref']);contract=doc(proof['builder_contract_ref'])
guardmod=types.ModuleType('delivery_read_guard');exec(compile(Path(contract['source_guard_ref']['path']).read_bytes(),contract['source_guard_ref']['path'],'exec'),guardmod.__dict__)
inputs=mf['members']+[pin(N/'HDF.json'),pin(N/'MF.json'),pin(__file__),pin(N/'review-01e211.actual-host.raw.jsonl'),pin(N/'review-01e211.actual-host.binding.json')]
guard=guardmod.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024)
try:
 guard.acquire(inputs)
 for r in inputs:
  a=pin(r['path']);assert (a['sha256'],a['bytes'])==(r['sha256'],r['bytes'])
 binding=doc(N/'review-01e211.actual-host.binding.json');parts=[]
 with Path(binding['source_audit_path']).open('rb') as f:
  for off,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
   f.seek(off);v=f.read(size);assert len(v)==size and hashlib.sha256(v).hexdigest()==digest;parts.append(v)
 assert b''.join(parts)==Path(binding['original_capture_ref']['path']).read_bytes()
 assert binding['outer_exit']==binding['python_exit']==0
 assert proof['status']=='QUALIFIED_OLD21_BUILD_PENDING_ROOT_BINDING' and proof['Root_binding_ref'] is None and proof['Root_binding_required'] is True
 assert proof['formal_acceptance'] is proof['parent_acceptance'] is proof['execution_grant'] is False
 assert proof['actual_Go_primary_exits']==[0]*9 and len(proof['actual_Go_process_identities'])==9
 assert all(type(x['creation_time_100ns']) is int and str(x['creation_time_100ns'])==x['creation_time_100ns_decimal'] for x in proof['actual_Go_process_identities'])
 assert len(proof['frozen_runtime_source_refs'])==24 and len(proof['program_refs'])==2
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('delivery-Source-guard.closed.json',closed)
out=save('complete-hostpair-seal.json',dict(schema='researchos.old21-independent-programme-review-complete-seal.v1',hdf_ref=pin(N/'HDF.json'),mf_ref=pin(N/'MF.json'),decision_ref=pin(N/'decision.json'),qualification_ref=pin(N/'programme-qualification.json'),publication_actual_raw_ref=pin(N/'review-01e211.actual-host.raw.jsonl'),publication_actual_binding_ref=pin(N/'review-01e211.actual-host.binding.json'),publication_outer_exit=0,publication_python_exit=0,all_manifest_members_verified=True,guard_ref=gr,Root_binding_required=True,formal_acceptance=False,parent_acceptance=False,execution_grant=False))
print(json.dumps(dict(complete_hostpair_seal_ref=out,guard_ref=gr,manifest_members=len(mf['members']),formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True);print('PYTHON_EXIT_CODE=0',flush=True)

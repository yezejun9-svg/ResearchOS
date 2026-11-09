"""Preserve actual original Task78 tools; no Source/product execution."""
import hashlib,json,types
from pathlib import Path
D=Path(__file__).resolve().parent
ACTOR='codex:/root/full_w09_source_review'
LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl')
THREAD='01a1215b-7210-7613-b033-756b9d553b83'
def pin(path):
 p=Path(path);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(path,value):
 with path.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(path)
def docs(value):
 out=[]
 if type(value) is dict:
  out.append(value)
  for x in value.values():out.extend(docs(x))
 elif type(value) is list:
  for x in value:out.extend(docs(x))
 elif type(value) is str:
  try:out.extend(docs(json.loads(value)))
  except (ValueError,TypeError):pass
 return out
def capture(chunk,ordinal,outer,python):
 size=LOG.stat().st_size;calls={};found=[]
 with LOG.open('rb') as f:
  header=f.readline();assert json.loads(header)['payload']['id']==THREAD
  start=max(0,size-64*1024*1024);f.seek(start)
  if start:f.readline()
  while f.tell()<size:
   offset=f.tell();raw=f.readline();v=json.loads(raw);p=v.get('payload',{})
   if p.get('type')=='custom_tool_call':calls[p['call_id']]=(offset,raw,v)
   if p.get('type')=='custom_tool_call_output':
    matches=[x for x in docs(p.get('output')) if x.get('chunk_id')==chunk]
    if matches:found.append((calls[p['call_id']],(offset,raw,v),matches))
 assert len(found)==1 and len(found[0][2])==1
 call,result,values=found[0];value=values[0];assert value['exit_code']==outer
 if python is not None:assert ('Python_exit='+str(python)) in value['output']
 lines=[header,call[1],result[1]];offsets=[0,call[0],result[0]]
 with LOG.open('rb') as f:
  for offset,raw in zip(offsets,lines):f.seek(offset);assert f.read(len(raw))==raw
 raw_path=D/('original-'+str(ordinal)+'.raw.jsonl')
 with raw_path.open('xb') as f:f.write(b''.join(lines))
 refs=dict(raw_ref=pin(raw_path))
 binding=dict(schema='researchos.independent-source-original-host-binding.v1',actor_id=ACTOR,actor_thread_id=THREAD,original_failure_ordinal=ordinal,
  source_audit_path=str(LOG),source_prefix_size_observed=size,source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],source_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
  actual_call_id=call[2]['payload']['call_id'],actual_chunk_id=chunk,raw_ref=refs['raw_ref'],outer_tool_exit=outer,python_exit=python,native_process_exit=None,go_process_exit=None,sqlite_process_exit=None,dispatcher_exit=None,model_call_exit=None,
  actual_product_calls=0,Root_assigned_ordinal=True,execution_grant=False,formal_acceptance=False)
 if ordinal==1093:
  binding.update(original_script_ref=pin(D/'review.py'),successful_and_failed_progress_ref=pin(D/'checks.progress.jsonl'),finally_guard_closed_ref=pin(D/'independent-Source-guard.closed.json'))
  g=json.loads((D/'independent-Source-guard.closed.json').read_bytes());assert g['closed'] and g['retained_handles_count']==0 and not g['errors']
 else:binding.update(guard_created=False,diagnostic='rg path OS error2 and missing Source_controls filename; outer completed0; unobserved process exits remain NULL')
 refs['binding_ref']=save(D/('original-'+str(ordinal)+'.binding.json'),binding)
 return refs
if __name__=='__main__':
 results={str(o):capture(c,o,e,p) for c,o,e,p in [('cf5684',1092,0,None),('2f452c',1093,1,1)]}
 print(json.dumps(dict(originals=results,actual_product_calls=0,execution_grant=False,formal_acceptance=False),ensure_ascii=False))

"""Seal the successful finite closeout and final published review pair."""
from pathlib import Path
import hashlib,json,types,sys
N=Path(__file__).resolve().parent
ns={'__name__':'definitions_only','__file__':str(N/'review.py')}
exec(compile((N/'review.py').read_bytes(),ns['__file__'],'exec'),ns)
pin,read,save,inert=ns['pin'],ns['read'],ns['save'],ns['inert']
audit=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
limit=audit.stat().st_size;calls={};found=[]
with audit.open('rb') as f:
 header=f.readline();f.seek(max(len(header),limit-4*1024*1024))
 if f.tell()!=len(header):f.readline()
 offset=f.tell()
 while offset<limit:
  line=f.readline();row=json.loads(line);p=row.get('payload',{})
  if row.get('type')=='response_item' and p.get('type')=='custom_tool_call':calls[p['call_id']]=(offset,line,row)
  if row.get('type')=='response_item' and p.get('type')=='custom_tool_call_output':
   for block in p.get('output',[]):
    for text in dict.fromkeys([block.get('text',''),*block.get('text','').splitlines()]):
     try:v=json.loads(text)
     except (ValueError,TypeError):continue
     if isinstance(v,dict) and v.get('chunk_id')=='04ad89':found.append((calls[p['call_id']],(offset,line,row),v))
  offset+=len(line)
assert len(found)==1
call,result,host=found[0];assert host['exit_code']==0
rows=[(0,header),(call[0],call[1]),(result[0],result[1])]
raw=N/'actual-finite-closeout.raw.jsonl'
with raw.open('xb') as f:f.write(b''.join(b for _,b in rows))
rawref=pin(raw)
br=save('actual-finite-closeout.binding.json',dict(source_audit_path=str(audit),source_prefix_size_observed=limit,source_line_offsets=[a for a,_ in rows],source_line_bytes=[len(b) for _,b in rows],original_line_sha256=[hashlib.sha256(b).hexdigest() for _,b in rows],original_capture_ref=rawref,original_call_id=call[2]['payload']['call_id'],tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=result[2]['timestamp'],chunk_id='04ad89'))
lines=host['output'].splitlines();assert lines[-1]=='FULLW09_V3_CLOSEOUT_PYTHON_EXIT=0';out=json.loads(lines[0])
for k,n in [('HDF','HDF.json'),('MF','MF.json'),('decision','source-review-decision.json')]:assert out[k]==pin(N/n)
m=inert(ns['S']/'full_w09_runtime.source.py','fullw09_final_seal_runtime')
c=read(ns['S']/'source.choice.json');gm=m.module(c['common']['guard_ref'])
refs=[pin(__file__),rawref,br,out['HDF'],out['MF'],*read(out['MF'])['members'],pin(ns['S']/'HDF.json'),pin(ns['S']/'MF.json'),*read(ns['S']/'MF.json')['members']]
refs=m.unique(refs)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
try:
 guard.acquire(refs)
 with audit.open('rb') as f:
  for offset,line in rows:f.seek(offset);assert f.read(len(line))==line
 h,rr=m.pair(out['HDF'],out['MF']);decision=read(out['decision'])
 assert h['source_decision_ref']==out['decision'] and out['decision'] in rr
 assert decision['decision']=='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE' and decision['formal_acceptance'] is False and decision['execution_grant'] is False
 assert all(pin(r['path'])==r for r in refs)
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors'] and closed['verification']=='PASSED'
gr=save('final-seal-Source-guard.closed.json',closed)
seal=save('complete-hostpair-seal.json',dict(verdict='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE',review_refs=[out[k] for k in ('HDF','MF','decision')],actual_host_capture_ref=rawref,actual_host_binding_ref=br,actual_outer_exit=0,actual_python_exit=0,actual_Native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,Source_guard_ref=gr,original_failures_ref=out['original_failures'],completed_delta_evidence_ref=out['completed_delta_evidence'],original_failed_guard_close_results='UNKNOWN_NOT_SERIALIZED',new_finite_and_final_guards_closed=True,formal_acceptance=False,execution_grant=False,parent_acceptance=False,production_read_inputs_rerun=False))
print(json.dumps(dict(seal=seal,actual_host_capture_ref=rawref,actual_host_binding_ref=br,review_refs=[out[k] for k in ('HDF','MF','decision')]),ensure_ascii=False),flush=True)

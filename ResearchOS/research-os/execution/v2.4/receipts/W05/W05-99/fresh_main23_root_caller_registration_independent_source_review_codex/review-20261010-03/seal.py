"""Seal authentic launched/polled review and validate published Source schema."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
N=Path(__file__).resolve().parent
x=runpy.run_path(str(N/'review.py'),run_name='definitions_only');pin,read,save,mod=x['pin'],x['read'],x['save'],x['mod']
p=mod(x['R']/'execution/v2.4/receipts/W09/W09-99/cp370_actual_registration_independent_review_codex/actualr4-01a120ab/review.py');p.N=N
def capture(audit,start,chunk,name):
 limit=audit.stat().st_size;calls={};found=[]
 with audit.open('rb') as f:
  header=f.readline();f.seek(start);offset=start
  while offset<limit:
   line=f.readline();item=json.loads(line);payload=item.get('payload',{})
   if item.get('type')=='response_item' and payload.get('type')=='custom_tool_call':calls[payload['call_id']]=(offset,line,item)
   if item.get('type')=='response_item' and payload.get('type')=='custom_tool_call_output' and isinstance(payload.get('output'),list):
    matched=False
    for block in payload['output']:
     for text in dict.fromkeys([block.get('text',''),*block.get('text','').splitlines()]):
      try:value=json.loads(text)
      except (ValueError,TypeError,AttributeError):continue
      if isinstance(value,dict) and value.get('status')=='fulfilled' and isinstance(value.get('value'),dict):value=value['value']
      if isinstance(value,dict) and value.get('chunk_id')==chunk and not matched:
       call=calls[payload['call_id']];found.append((call[2],item,value,[(0,header),(call[0],call[1]),(offset,line)]));matched=True
   offset+=len(line)
 assert len(found)==1,(chunk,len(found))
 call,out,result,rows=found[0]
 with (N/(name+'.actual-host.raw.jsonl')).open('xb') as f:f.write(b''.join(r[1] for r in rows))
 cap=pin(N/(name+'.actual-host.raw.jsonl'))
 br=save(name+'.actual-host.binding.json',dict(source_audit_path=str(audit),source_prefix_size_observed=limit,source_line_offsets=[r[0] for r in rows],source_line_bytes=[len(r[1]) for r in rows],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in rows],actual_capture_ref=cap,original_call_id=call['payload']['call_id'],tool_call_timestamp=call['timestamp'],tool_result_timestamp=out['timestamp'],chunk_id=chunk,parallel_result_wrapper_preserved=True))
 return dict(call=call,output=out,result=result,rows=rows,cap_ref=cap,binding_ref=br)
p.capture=capture
audit=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
diagnostic=p.capture(audit,40928429,'8e1773','original1046-read-diagnostic')
launch=p.capture(audit,40928429,'bb4ab0','review-launch')
completed=p.capture(audit,40928429,sys.argv[1],'review-complete')
seal_failures=[p.capture(audit,40928429,c,'seal-diagnostic-'+c) for c in ('4eeb48','7a6d99','479ae0')]
assert launch['result']['session_id']==22159 and completed['result']['exit_code']==0
assert 'session_id:22159' in completed['call']['payload']['input'].replace(' ','') or 'session_id: 22159' in completed['call']['payload']['input']
lines=completed['result']['output'].splitlines();published=json.loads(lines[0]);assert lines[-1]=='MAIN23_REVIEW_PYTHON_EXIT=0'
for k,n in [('HDF','HDF.json'),('MF','MF.json'),('decision','decision.json')]:assert published[k]==pin(N/n)
header=json.loads(completed['rows'][0][1])['payload'];assert header['id']=='01a11e76-4e37-7a21-a388-2c5f2e3c9ebf' and header['source']['subagent']['thread_spawn']['agent_path']=='/root/attach_fixture_source_review'
sh=read(x['S']/'HDF.json');m=mod(sh['caller_ref']['path']);h=read(N/'HDF.json')
refs=[pin(__file__),*[published[k] for k in ('HDF','MF','decision')],h['finitechecks_ref'],h['Source_guard_ref'],pin(x['S']/'HDF.json'),sh['manifest_ref'],*read(sh['manifest_ref']['path'])['members']]
for cap in (diagnostic,launch,completed,*seal_failures):refs.extend([cap['cap_ref'],cap['binding_ref']])
refs=m.local_refs(refs);guard=m.guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
try:
 for cap in (diagnostic,launch,completed,*seal_failures):
  with audit.open('rb') as f:
   for offset,line in cap['rows']:f.seek(offset);assert f.read(len(line))==line
 # Execute the unmodified own_review prefix that checks the final actual
 # published HDF/MF/decision fields, stopping before future Root witness IO.
 fn=copy.deepcopy(next(n for n in ast.parse(Path(sh['caller_ref']['path']).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='own_review'))
 stop=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='witness' for t in n.targets))
 fn.name='published_own_review_prefix';fn.body=fn.body[:stop]+[ast.Return(value=ast.Constant(value=True))]
 ast.fix_missing_locations(fn);exec(compile(ast.Module(body=[fn],type_ignores=[]),'unmodified_own_review_prefix','exec'),m.__dict__)
 request=dict(source_hdf_ref=pin(x['S']/'HDF.json'),source_mf_ref=sh['manifest_ref'],review_hdf_ref=published['HDF'],review_mf_ref=published['MF'],review_decision_ref=published['decision'])
 assert m.published_own_review_prefix(request) is True
 assert read(h['finitechecks_ref']['path'])['failed']==[]
 assert all(m.same_ref(pin(r['path']),r) for r in refs)
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('seal-source-guard.closed.json',closed)
shape=save('published-contract-check.json',dict(actual_final_HDF_MF_decision_validate_by_unmodified_own_review_prefix=True,future_Root_witness_not_synthesized=True,actual_runtime_qualification=None,formal_acceptance=False,execution_grant=False))
out=save('complete-hostpair-seal.json',dict(verdict='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',review_refs=[published[k] for k in ('HDF','MF','decision')],actual_review_launch_ref=launch['cap_ref'],actual_review_launch_binding_ref=launch['binding_ref'],actual_review_host_capture_ref=completed['cap_ref'],actual_review_host_binding_ref=completed['binding_ref'],actual_outer_exit=0,actual_python_exit=0,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,reviewer_actor=x['ACTOR'],reviewer_session_id=header['id'],source_author=sh['source_author'],source_author_thread_id=sh['source_thread_id'],source_guard_ref=gr,published_contract_check_ref=shape,original_failures=[dict(ordinal=1046,chunk='8e1773',capture_ref=diagnostic['cap_ref'],binding_ref=diagnostic['binding_ref'],actual_outer_exit=0,actual_python_exit=None,actual_native_exit=None)]+[dict(ordinal=None,Root_assignment_required=True,chunk=c['result']['chunk_id'],capture_ref=c['cap_ref'],binding_ref=c['binding_ref'],actual_outer_exit=1,actual_python_exit=1 if i<2 else None,actual_native_exit=None) for i,c in enumerate(seal_failures)],checks=published['checks'],held_review_refs=published['held_refs'],runtime_qualification=None,execution_grant=False,formal_acceptance=False,parent_acceptance=False))
print(json.dumps(dict(seal=out,review_refs=[published[k] for k in ('HDF','MF','decision')],host_capture=completed['cap_ref'],host_binding=completed['binding_ref'],diagnostic_capture=diagnostic['cap_ref'],diagnostic_binding=diagnostic['binding_ref']),ensure_ascii=False),flush=True)

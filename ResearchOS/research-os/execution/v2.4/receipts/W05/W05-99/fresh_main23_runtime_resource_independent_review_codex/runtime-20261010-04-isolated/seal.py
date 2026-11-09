"""Seal actual isolated resource review and Root probe, without Root issuance."""
from pathlib import Path
import ast,hashlib,json,sys,types
N=Path(__file__).resolve().parent
ns={'__name__':'definitions_only','__file__':str(N/'review.py')}
exec(compile((N/'review.py').read_bytes(),ns['__file__'],'exec'),ns)
pin,read,save,load=ns['pin'],ns['read'],ns['save'],ns['load']
def capture(audit,chunk,name):
 limit=audit.stat().st_size;calls={};found=[]
 with audit.open('rb') as f:
  header=f.readline();f.seek(max(len(header),limit-16*1024*1024))
  if f.tell()!=len(header):f.readline()
  offset=f.tell()
  while offset<limit:
   line=f.readline();row=json.loads(line);p=row.get('payload',{})
   if row.get('type')=='response_item' and p.get('type')=='custom_tool_call':calls[p['call_id']]=(offset,line,row)
   if row.get('type')=='response_item' and p.get('type')=='custom_tool_call_output':
    for block in p.get('output',[]):
     for text in dict.fromkeys([block.get('text',''),*block.get('text','').splitlines()]):
      try:value=json.loads(text)
      except (ValueError,TypeError):continue
      if isinstance(value,dict) and value.get('chunk_id')==chunk:found.append((calls[p['call_id']],(offset,line,row),value))
   offset+=len(line)
 assert len(found)==1,(chunk,len(found))
 call,result,host=found[0];rows=[(0,header),(call[0],call[1]),(result[0],result[1])]
 raw=N/(name+'.actual-host.raw.jsonl')
 with raw.open('xb') as f:f.write(b''.join(v for _,v in rows))
 rawref=pin(raw)
 br=save(name+'.actual-host.binding.json',dict(source_audit_path=str(audit),source_prefix_size_observed=limit,source_line_offsets=[o for o,_ in rows],source_line_bytes=[len(v) for _,v in rows],original_line_sha256=[hashlib.sha256(v).hexdigest() for _,v in rows],actual_capture_ref=rawref,original_call_id=call[2]['payload']['call_id'],tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=result[2]['timestamp'],chunk_id=chunk))
 return dict(raw_ref=rawref,binding_ref=br,call=call[2],result=host,rows=rows,audit=audit)
own=capture(Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl'),'15e61e','isolated-M4-review-complete')
root=capture(Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl'),'5919f2','actual-Root-M4-resource-probe')
header=json.loads(own['rows'][0][1])['payload']
assert header['id']=='01a11e76-4e37-7a21-a388-2c5f2e3c9ebf' and header['source']['subagent']['thread_spawn']['agent_path']=='/root/attach_fixture_source_review'
assert json.loads(root['rows'][0][1])['payload']['id']==ns['THREAD']
for cap in (own,root):
 assert cap['result']['exit_code']==0 and '-I -S -B -X utf8' in cap['call']['payload']['input']
lines=own['result']['output'].splitlines();assert lines[-1]=='MAIN23_M4_RUNTIME_REVIEW_PYTHON_EXIT=0'
published=json.loads(lines[0]);assert published['failed']==[] and published['checks']==454 and published['held_refs']==218
for k,n in [('HDF','HDF.json'),('MF','MF.json'),('decision','decision.json')]:assert published[k]==pin(N/n)
root_lines=root['result']['output'].splitlines();root_doc=json.loads(root_lines[0])
assert root_doc['schema']=='researchos.root-main23-resource-scope-issuance.v1' and root_doc['issued_by']=='codex:/root' and root_doc['root_thread_id']==ns['THREAD']
assert root_doc['resource_count']==145 and root_doc['execution_grant'] is False and root_doc['programme_qualification'] is False
assert root_doc['scope_ref']==pin(ns['D']/'main23.v4.runtime-qualification.scope.actual.root.json') and root_doc['proposed_resources_ref']==pin(ns['D']/'main23.v4.runtime-resources.proposed.root.json')
h=read(N/'HDF.json');decision=read(N/'decision.json');caller=load(h['caller_ref'],'M4_runtime_seal_caller')
refs=read(N/'MF.json')['members']+[pin(N/'HDF.json'),pin(N/'MF.json'),pin(__file__),own['raw_ref'],own['binding_ref'],root['raw_ref'],root['binding_ref']]
refs=caller.local_refs(refs)
guard=caller.guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=1024*1024*1024)
try:
 guard.acquire(refs)
 for cap in (own,root):
  with cap['audit'].open('rb') as f:
   for offset,line in cap['rows']:f.seek(offset);assert f.read(len(line))==line
 # Execute only unchanged local HDF/MF/decision predicates, stopping before
 # peer delivery, Root payload, qualification or issuance records are consulted.
 fn=next(x for x in ast.parse(Path(h['caller_ref']['path']).read_bytes()).body if isinstance(x,ast.FunctionDef) and x.name=='runtime_review_chain')
 first=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='review_refs' for t in x.targets))
 last=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Tuple) and any(isinstance(a,ast.Name) and a.id=='peer_binding' for a in t.elts) for t in x.targets))
 local_review_binding_inputs={k:h[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','python_ref','go_ref','qualification_scope_ref')}
 local_review_binding_inputs.update(review_hdf_ref=published['HDF'],review_mf_ref=published['MF'],review_decision_ref=published['decision'],resource_refs=decision['resource_refs'])
 context=dict(caller.__dict__,qualification=local_review_binding_inputs,author=h['review_author'],source_ref=h['source_hdf_ref'],source_mf_ref=h['source_mf_ref'],scope_ref=h['qualification_scope_ref'])
 exec(compile(ast.Module(body=fn.body[first:last],type_ignores=[]),'unchanged_local_review_predicates_only','exec'),context)
 assert read(h['finitechecks_ref'])['failed']==[]
 assert all(caller.same_ref(pin(r['path']),r) for r in refs)
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('seal-source-guard.closed.json',closed)
seal=save('complete-hostpair-seal.json',dict(verdict='RUNTIME_CLOSURE_ACCEPTED',review_refs=[published[k] for k in ('HDF','MF','decision')],actual_host_capture_ref=own['raw_ref'],actual_host_binding_ref=own['binding_ref'],actual_Root_resource_probe_capture_ref=root['raw_ref'],actual_Root_resource_probe_binding_ref=root['binding_ref'],reviewer_actor=h['review_author'],source_author=h['source_author'],builder_source_author=h['builder_source_author'],actual_outer_exit=0,actual_python_exit=0,actual_Go_exit=None,actual_Native_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,Source_guard_ref=gr,unmodified_M4_local_review_predicates_passed=True,Root_payload_qualification_or_future_issuance_created=False,formal_acceptance=False,execution_grant=False,programme_qualification=None,parent_acceptance=False))
print(json.dumps(dict(seal=seal,review_refs=[published[k] for k in ('HDF','MF','decision')],actual_host_capture_ref=own['raw_ref'],actual_host_binding_ref=own['binding_ref'],actual_Root_resource_probe_capture_ref=root['raw_ref'],actual_Root_resource_probe_binding_ref=root['binding_ref']),ensure_ascii=False),flush=True)

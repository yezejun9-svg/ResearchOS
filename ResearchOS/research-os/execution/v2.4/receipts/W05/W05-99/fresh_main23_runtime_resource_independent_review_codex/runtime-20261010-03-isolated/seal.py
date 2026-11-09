"""Seal exact real host records and final review schema; never issue Root authority."""
from pathlib import Path
import ast, hashlib, json, os, sys, types
N=Path(__file__).resolve().parent
ns={'__name__':'definitions_only','__file__':str(N/'review.py')}
exec(compile((N/'review.py').read_bytes(),ns['__file__'],'exec'),ns)
pin,read,save,load=ns['pin'],ns['read'],ns['save'],ns['load']
audit=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
limit=audit.stat().st_size
calls={};captured={}
targets={'d7edc5':'original-review-interface-error','5eb020':'original-nonisolated-rejection','b296ce':'isolated-review-complete'}
with audit.open('rb') as f:
 header=f.readline();f.seek(48635260-1);f.readline();offset=f.tell()
 while offset<limit:
  line=f.readline();row=json.loads(line);p=row.get('payload',{})
  if row.get('type')=='response_item' and p.get('type')=='custom_tool_call':calls[p['call_id']]=(offset,line,row)
  if row.get('type')=='response_item' and p.get('type')=='custom_tool_call_output':
   for block in p.get('output',[]):
    for text in dict.fromkeys([block.get('text',''),*block.get('text','').splitlines()]):
     try:value=json.loads(text)
     except (ValueError,TypeError):continue
     if not isinstance(value,dict) or value.get('chunk_id') not in targets:continue
     key=value['chunk_id']
     if key in captured:continue
     call=calls[p['call_id']];rows=[(0,header),(call[0],call[1]),(offset,line)]
     raw=N/(targets[key]+'.actual-host.raw.jsonl')
     with raw.open('xb') as out:out.write(b''.join(v for _,v in rows))
     ref=pin(raw)
     binding=save(targets[key]+'.actual-host.binding.json',dict(source_audit_path=str(audit),source_prefix_size_observed=limit,source_line_offsets=[o for o,_ in rows],source_line_bytes=[len(v) for _,v in rows],original_line_sha256=[hashlib.sha256(v).hexdigest() for _,v in rows],actual_capture_ref=ref,original_call_id=p['call_id'],tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=row['timestamp'],chunk_id=key))
     captured[key]=dict(raw_ref=ref,binding_ref=binding,result=value,call=call[2],rows=rows)
  offset+=len(line)
assert set(captured)==set(targets)
identity=json.loads(header)['payload']
assert identity['source']['subagent']['thread_spawn']['agent_path']=='/root/attach_fixture_source_review'
assert identity['id']=='01a11e76-4e37-7a21-a388-2c5f2e3c9ebf'
actual=captured['b296ce'];assert actual['result']['exit_code']==0
assert '-I -S -B -X utf8' in actual['call']['payload']['input']
lines=actual['result']['output'].splitlines();assert lines[-1]=='MAIN23_RUNTIME_REVIEW_PYTHON_EXIT=0'
result=json.loads(lines[0]);assert result['failed']==[] and result['checks']==374 and result['held_refs']==179
assert all(result[k]==pin(N/f) for k,f in [('HDF','HDF.json'),('MF','MF.json'),('decision','decision.json')])
assert captured['d7edc5']['result']['exit_code']==1 and 'MAIN23_RUNTIME_REVIEW_PYTHON_EXIT=1' in captured['d7edc5']['result']['output']
assert captured['5eb020']['result']['exit_code']==0 and 'RUNTIME_CLOSURE_REJECTED' in captured['5eb020']['result']['output']
h,dec,mf=read(N/'HDF.json'),read(N/'decision.json'),read(N/'MF.json')
caller=load(h['caller_ref'],'runtime_seal_caller')
refs=mf['members']+[pin(N/'HDF.json'),pin(N/'MF.json'),pin(__file__)]
refs += [c[k] for c in captured.values() for k in ('raw_ref','binding_ref')]
refs=caller.local_refs(refs)
guard=caller.guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=1024*1024*1024)
guard.acquire(refs)
try:
 for c in captured.values():
  with audit.open('rb') as f:
   for offset,line in c['rows']:f.seek(offset);assert f.read(len(line))==line
 # Copy only the unchanged local review predicates from runtime_review_chain.
 # No Root qualification or peer/witness records are manufactured or invoked.
 tree=ast.parse(Path(h['caller_ref']['path']).read_bytes())
 fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='runtime_review_chain')
 first=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='review_refs' for t in x.targets))
 last=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Tuple) and any(isinstance(a,ast.Name) and a.id=='peer_binding' for a in t.elts) for t in x.targets))
 bindings={k:h[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','python_ref','go_ref','qualification_scope_ref')}
 bindings.update(review_hdf_ref=pin(N/'HDF.json'),review_mf_ref=pin(N/'MF.json'),review_decision_ref=pin(N/'decision.json'),resource_refs=dec['resource_refs'])
 ctx=dict(caller.__dict__,qualification=bindings,author=h['review_author'],source_ref=h['source_hdf_ref'],source_mf_ref=h['source_mf_ref'],scope_ref=h['qualification_scope_ref'])
 exec(compile(ast.Module(body=fn.body[first:last],type_ignores=[]),'unmodified_local_runtime_review_predicates_only','exec'),ctx)
 assert read(h['finitechecks_ref'])['failed']==[]
 assert all(caller.same_ref(pin(r['path']),r) for r in refs)
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
closed_ref=save('seal-source-guard.closed.json',closed)
seal=save('complete-hostpair-seal.json',dict(verdict='RUNTIME_CLOSURE_ACCEPTED',review_refs=[pin(N/n) for n in ('HDF.json','MF.json','decision.json')],actual_host_capture_ref=actual['raw_ref'],actual_host_binding_ref=actual['binding_ref'],reviewer_actor=h['review_author'],reviewer_session_id=identity['id'],source_author=h['source_author'],builder_source_author=h['builder_source_author'],actual_outer_exit=0,actual_python_exit=0,actual_Go_exit=None,actual_Native_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,original_diagnostics=[dict(chunk_id=k,raw_ref=captured[k]['raw_ref'],binding_ref=captured[k]['binding_ref'],Root_assignment_required=True) for k in ('d7edc5','5eb020')],original_rejected_namespace_retained=True,review_scope='Exact Root proposed145 under original -I -S -B -X utf8 startup flags',unmodified_local_runtime_review_predicates_passed=True,future_Root_qualification_or_peer_witness_not_created=True,Source_guard_ref=closed_ref,formal_acceptance=False,execution_grant=False,programme_qualification=None,parent_acceptance=False))
print(json.dumps(dict(seal=seal,review_refs=[pin(N/n) for n in ('HDF.json','MF.json','decision.json')],actual_host_capture_ref=actual['raw_ref'],actual_host_binding_ref=actual['binding_ref']),ensure_ascii=False),flush=True)

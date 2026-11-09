from pathlib import Path
import hashlib,json
N=Path(__file__).parent;P=N.parent/'review-public21-actual-20261010-01'
session=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v,raw=False):
 with (N/name).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
ordinals=[1162,1163,1165,1167];docs={k:json.loads((P/('original-'+str(k)+'.json')).read_bytes()) for k in ordinals}
protected=[pin(P/x) for x in ['HDF.json','MF.json','actual-decision.json']]+[pin(P/('original-'+str(k)+'.json')) for k in ordinals]
def values(v,depth=0):
 if depth>6:return
 yield v
 if isinstance(v,dict):
  for x in v.values():yield from values(x,depth+1)
 elif isinstance(v,list):
  for x in v:yield from values(x,depth+1)
 elif isinstance(v,str):
  try:d=json.loads(v)
  except (ValueError,TypeError):return
  yield from values(d,depth+1)
prefix=session.stat().st_size;start=max(0,prefix-20*1024*1024);calls={};found={};candidates=[]
with session.open('rb') as f:
 head_raw=f.readline();head=json.loads(head_raw);f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:v=json.loads(line)
  except ValueError:continue
  p=v.get('payload',{});typ=p.get('type')
  if v.get('type')=='response_item' and typ in ('function_call','custom_tool_call'):calls[p.get('call_id')]=(off,line,v)
  if v.get('type')!='response_item' or typ not in ('function_call_output','custom_tool_call_output') or p.get('call_id') not in calls:continue
  call=calls[p['call_id']];cin=str(call[2]['payload'].get('input',call[2]['payload'].get('arguments','')))
  for ordinal,doc in docs.items():
   if ordinal in found:continue
   exact=any(isinstance(x,dict) and x==doc['original_result'] for x in values(p.get('output')))
   if exact and 'original-'+str(ordinal)+'.json' not in cin and 'source-diagnostic-supplement' not in cin:
    found[ordinal]=[(0,head_raw,head),call,(off,line,v)]
   elif doc['original_result']['chunk_id'] in str(p.get('output','')):
    candidates.append(dict(ordinal=ordinal,offset=off,call_id=p.get('call_id'),exact_result=exact,input_prefix=cin[:180]))
results=[]
for ordinal,rows in found.items():
 doc=docs[ordinal];chunk=doc['original_result']['chunk_id']
 raw=save('original-'+str(ordinal)+'.raw.jsonl',b''.join(x[1] for x in rows),True)
 binding=save('original-'+str(ordinal)+'.binding.json',dict(schema='researchos.source-diagnostic-original-tool-binding.v1',
 actor_id='codex:/root/attach_restore_independent_review',source_audit_path=str(session),source_prefix_size_observed=prefix,
 finite_tail_start=start,finite_tail_max_bytes=20*1024*1024,
 source_line_offsets=[x[0] for x in rows],source_line_bytes=[len(x[1]) for x in rows],
 original_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in rows],
 original_call_id=rows[1][2]['payload']['call_id'],original_capture_ref=raw,original_document_ref=pin(P/('original-'+str(ordinal)+'.json')),
 Root_assigned_ordinal=ordinal,original_chunk_id=chunk,outer_exit=doc['actual_outer_exit'],
 Python_exit=doc['actual_Python_exit'],Native_exit=doc['actual_native_exit'],
 actual_result_exact_match=True,original_not_rerun=True,ordinal_self_issued=False,root_authority=False))
 results.append(dict(ordinal=ordinal,original_capture_ref=raw,binding_ref=binding))
assert all(pin(r['path'])==r for r in protected)
status='COMPLETE_FOUR_ORIGINAL_TOOL_BINDINGS' if len(results)==4 else 'INCOMPLETE_ORIGINAL_TOOL_BINDINGS'
save('decision.json',dict(schema='researchos.public21-source-diagnostic-supplement.v1',status=status,
 actor_id='codex:/root/attach_restore_independent_review',protected_refs=protected,original_documents_unchanged=True,
 bindings=results,missing=[x for x in ordinals if x not in found],search_candidates=candidates,
 Native_SQL_Go_TP_Rootstage_calls=0,old47_SQL_checks_rerun=False,old72_guards_rerun=False,
 Public21_component_decision_unchanged=True,formal_acceptance=False,execution_grant=False,STOP=True))
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ['HDF.json','MF.json','postseal-tool-io.json']]
mf=save('MF.json',dict(schema='researchos.source-diagnostic-supplement-manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
save('HDF.json',dict(schema='researchos.public21-source-diagnostic-supplement-handoff.v1',actor_id='codex:/root/attach_restore_independent_review',
 status=status,manifest_ref=mf,decision_ref=pin(N/'decision.json'),bindings=results,old_documents_unchanged=True,
 Native_SQL_Go_TP_Rootstage_calls=0,formal_acceptance=False,execution_grant=False,postseal_tool_io_excluded=True,STOP=True))
assert all(pin(r['path'])==r for r in members)
print(json.dumps(dict(status=status,found=list(found),missing=[x for x in ordinals if x not in found],
 HDF_ref=pin(N/'HDF.json'),MF_ref=mf,decision_ref=pin(N/'decision.json')),ensure_ascii=False))


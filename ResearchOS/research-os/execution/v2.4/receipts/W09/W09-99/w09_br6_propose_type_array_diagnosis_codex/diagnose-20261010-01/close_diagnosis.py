from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
A=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
targets={'c164fe':1212,'a85bff':1213,'eac3ea':1214,'986f9f':1215,'90a99f':1216,'b9c1dd':1217,'e5cb0e':None}
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v,raw=False):
 with (O/n).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
protected=[pin(p) for p in O.iterdir() if p.is_file() and p.name!='close_diagnosis.py']
prefix=A.stat().st_size;start=max(0,prefix-24*1024*1024);calls={};found={}
with A.open('rb') as f:
 head=f.readline();headj=json.loads(head);f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:j=json.loads(line)
  except ValueError:continue
  p=j.get('payload',{});t=p.get('type')
  if j.get('type')=='response_item' and t in ('function_call','custom_tool_call'):calls[p.get('call_id')]=(off,line,j)
  if j.get('type')!='response_item' or t not in ('function_call_output','custom_tool_call_output') or p.get('call_id') not in calls:continue
  c=calls[p['call_id']];inp=str(c[2]['payload'].get('input',c[2]['payload'].get('arguments','')))
  if 'close_diagnosis' in inp:continue
  out=str(p.get('output',''))
  for chunk in targets:
   if chunk not in found and chunk in out and chunk not in inp:found[chunk]=[(0,head,headj),c,(off,line,j)]
bindings=[]
for chunk,ordinal in targets.items():
 if chunk not in found:continue
 rows=found[chunk];name='diagnose-success' if ordinal is None else 'original'+str(ordinal)
 raw=save(name+'.fixed.raw.jsonl',b''.join(x[1] for x in rows),True)
 b=save(name+'.fixed.binding.json',dict(schema='researchos.diagnostic-fixed-original-binding.v1',
  actor_id='codex:/root/attach_restore_independent_review',source_audit_path=str(A),source_prefix_size_observed=prefix,
  source_line_offsets=[x[0] for x in rows],source_line_bytes=[len(x[1]) for x in rows],
  original_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in rows],source_session_id=headj['payload']['id'],
  original_call_id=rows[1][2]['payload']['call_id'],actual_chunk_id=chunk,Root_assigned_ordinal=ordinal,
  original_capture_ref=raw,actual_outer_exit=0 if chunk in ('b9c1dd','e5cb0e') else 1,
  actual_python_exit=0 if chunk=='e5cb0e' else None,actual_native_exit=None,actual_SQL_exit=None,actual_TP_exit=None,
  component_rg_failure_observed=(chunk=='b9c1dd'),component_rg_exit_separately_instrumented=False if chunk=='b9c1dd' else None,
  Root_component_rg_exit_classification=2 if chunk=='b9c1dd' else None,original_not_rerun=True,ordinal_self_issued=False))
 bindings.append(dict(chunk_id=chunk,ordinal=ordinal,raw_ref=raw,binding_ref=b))
 for off,line,_ in rows:
  with A.open('rb') as f:f.seek(off);assert f.read(len(line))==line
assert all(pin(p['path'])==p for p in protected)
status='DIAGNOSIS_COMPLETE_CANDIDATE_REVIEW_NOT_REACHED' if len(found)==len(targets) else 'DIAGNOSIS_CAPTURE_INCOMPLETE'
d=save('closure-decision.json',dict(schema='researchos.br6-type-array-diagnosis-closeout.v1',status=status,
 actor_id='codex:/root/attach_restore_independent_review',prior_diagnosis_ref=pin(O/'diagnosis-decision.json'),
 original1208_preserved_ref=pin(O/'original1208-observation.json'),original_bindings=bindings,
 missing_chunks=[c for c in targets if c not in found],same_origin_failed_tool_execution_count=6,successful_prefix_replayed=False,
 diagnosis_conclusion='Trusted router literal FORMAL tuple reaches exact-list-only Main exact_ids; normalize at Main consuming boundary.',
 prior_guarded_candidate_is_diagnostic_only=True,
 prior_unconditional_list_counterexample_qualification='A dictionary-key iterable is a hypothetical defense case outside the current pinned trusted router tuple contract. It does not by itself reject Root one-line candidate.',
 Root_candidate_main_sha256='1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087',
 Root_candidate_independent_review='NOT_REACHED_STOPPED_BY_ROOT',Root_candidate_accepted=False,
 actual_candidate_native_calls=0,Native_SQL_Go_models_dispatcher_TP_Rootstage_calls=0,
 Main_BR6_Canon_Scopes_modified=False,formal_acceptance=False,execution_grant=False,STOP=True))
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('HDF.closeout.json','MF.closeout.json','postclose-tool-io.json')]
mf=save('MF.closeout.json',dict(schema='researchos.diagnosis-closeout-manifest.v1',members=members,exclusions=['HDF.closeout.json','MF.closeout.json','postclose-tool-io.json']))
h=save('HDF.closeout.json',dict(schema='researchos.diagnosis-closeout-handoff.v1',status=status,manifest_ref=mf,decision_ref=d,
 prior_diagnosis_handoff_ref=pin(O/'HDF.json'),bindings=bindings,Root_candidate_accepted=False,actual_candidate_native_calls=0,
 Native_SQL_Go_models_dispatcher_TP_Rootstage_calls=0,Main_BR6_Canon_Scopes_modified=False,formal_acceptance=False,STOP=True))
assert all(pin(p['path'])==p for p in members)
print(json.dumps(dict(status=status,HDF_ref=h,MF_ref=mf,decision_ref=d,found=list(found),missing=[c for c in targets if c not in found]),ensure_ascii=False))

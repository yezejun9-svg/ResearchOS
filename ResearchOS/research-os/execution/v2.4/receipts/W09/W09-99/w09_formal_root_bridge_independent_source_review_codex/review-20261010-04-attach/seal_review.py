from pathlib import Path
import json,hashlib
N=Path(__file__).parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v,raw=False):
 with (N/name).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def values(v,depth=0):
 if depth>9:return
 yield v
 if isinstance(v,dict):
  for x in v.values():yield from values(x,depth+1)
 elif isinstance(v,list):
  for x in v:yield from values(x,depth+1)
 elif isinstance(v,str):
  try:d=json.loads(v)
  except(ValueError,TypeError):return
  yield from values(d,depth+1)
session=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
prefix=session.stat().st_size;start=max(0,prefix-6*1024*1024);calls={};found=None
with session.open('rb') as f:
 header=f.readline();f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:v=json.loads(line)
  except ValueError:continue
  p=v.get('payload',{})
  if v.get('type')=='response_item' and p.get('type') in ('custom_tool_call','function_call'):calls[p.get('call_id')]=(off,line,v)
  if v.get('type')=='response_item' and p.get('type') in ('custom_tool_call_output','function_call_output') and p.get('call_id') in calls:
   matches=[x for x in values(p.get('output')) if isinstance(x,dict) and x.get('chunk_id')=='1c19e0']
   if len(matches)==1 and 'review_br4.py' in str(calls[p['call_id']][2]['payload'].get('input','')):
    found=([(0,header,json.loads(header)),calls[p['call_id']],(off,line,v)],matches[0]);break
assert found is not None
rows,result=found
assert result['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in result['output']
raw=save('actual-1c19e0.raw.jsonl',b''.join(row[1] for row in rows),True)
binding=save('actual-1c19e0.binding.json',dict(schema='researchos.independent-source-review-actual-tool-binding.v1',
 actor_id='/root/attach_restore_independent_review',source_audit_path=str(session),source_prefix_size_observed=prefix,
 source_line_offsets=[r[0] for r in rows],source_line_bytes=[len(r[1]) for r in rows],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in rows],
 original_call_id=rows[1][2]['payload']['call_id'],original_capture_ref=raw,actual_outer_exit=0,actual_Python_exit=0,
 actual_Native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_TP_exit=None,actual_Rootstage_exit=None,
 pure_AST_controls=12,formal_acceptance=False))
decision=json.loads((N/'decision.json').read_bytes());pins=json.loads((N/'input-pins.json').read_bytes())
assert all(pin(r['path'])==r for r in pins)
closed=json.loads(Path(decision['source_guard_ref']['path']).read_bytes())
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.w09-bridge-independent-source-review-manifest.v1',members=members,
 exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
hdf=save('HDF.json',dict(schema='researchos.w09-bridge-independent-source-review-handoff.v1',
 decision=decision['decision'],reviewer_id=decision['reviewer_id'],reviewer_actor=decision['reviewer_actor'],
 subject_Source_author=decision['source_author'],subject_Source_author_backend=decision['source_author_backend'],
 actual_reviewer_thread=json.loads(rows[0][1])['payload']['id'],actual_parent_Root_thread=decision['Root_thread_id'],
 manifest_ref=mf,decision_ref=pin(N/'decision.json'),source_guard_ref=decision['source_guard_ref'],
 all_Source_guards_closed_zero=True,SourceGuard_handles=len(pins),
 subject_hdf_ref=decision['source_hdf_ref'],subject_mf_ref=decision['source_mf_ref'],subject_source_ref=decision['source_ref'],
 subject_launcher_ref=decision['consumer_launcher_ref'],subject_calling_contract_ref=decision['calling_contract_ref'],
 actual_source_author_ref=decision['source_actual_author_ref'],actual_source_author_meta=decision['source_actual_author_meta'],
 controls_ref=decision['checks_ref'],passed_delta_checks=5,pure_AST_controls=12,actual_tool_binding_ref=binding,
 original_Attach_contribution_preserved=True,scope_of_independence='Current Full-authored BR4 delta; no retroactive self-acceptance of original Attach Source.',
 old22_18_44_controls_rerun=False,Main_Canon_Scope_writes=0,Root_stage_Native_Go_SQL_TP_Mode_calls=0,
 Root_Scope_or_runtime_qualification_ref=None,formal_acceptance=False,parent_acceptance=False,execution_grant=False,STOP=True))
assert all(pin(r['path'])==r for r in members)
print(json.dumps(dict(HDF_ref=hdf,MF_ref=mf,decision_ref=pin(N/'decision.json'),decision=decision['decision'],
 checks=5,pure_AST_controls=12,SourceGuard_handles=len(pins),SourceGuard_closed0=True,member_count=len(members)),ensure_ascii=False))


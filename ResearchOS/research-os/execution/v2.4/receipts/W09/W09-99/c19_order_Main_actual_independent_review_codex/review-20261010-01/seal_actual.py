from pathlib import Path
import json,hashlib
N=Path(__file__).parent
SESSION=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v,raw=False):
 with (N/name).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def values(v,depth=0):
 if depth>10:return
 yield v
 if isinstance(v,dict):
  for x in v.values():yield from values(x,depth+1)
 elif isinstance(v,list):
  for x in v:yield from values(x,depth+1)
 elif isinstance(v,str):
  try:d=json.loads(v)
  except (ValueError,TypeError):return
  yield from values(d,depth+1)
targets={'6aeb06':1176,'b80816':1177,'39fb10':1178,'24ae31':1179,'b6819a':None}
found={};calls={};prefix=SESSION.stat().st_size;start=max(0,prefix-12*1024*1024)
with SESSION.open('rb') as f:
 head=f.readline();f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:v=json.loads(line)
  except ValueError:continue
  p=v.get('payload',{});typ=p.get('type')
  if v.get('type')=='response_item' and typ in ('custom_tool_call','function_call'):
   calls[p.get('call_id')]=(off,line,v)
  if v.get('type')!='response_item' or typ not in ('custom_tool_call_output','function_call_output') or p.get('call_id') not in calls:continue
  call=calls[p['call_id']];cin=str(call[2]['payload'].get('input',call[2]['payload'].get('arguments','')))
  for chunk,ordinal in targets.items():
   if chunk in found:continue
   matches=[x for x in values(p.get('output')) if isinstance(x,dict) and x.get('chunk_id')==chunk]
   if len(matches)==1 and not any(x in cin for x in ('seal_actual.py','inspection-tool-io.json','review-and-cleanup-tool-io.json')):
    found[chunk]=([(0,head,json.loads(head)),call,(off,line,v)],matches[0],ordinal)
  if 'policy-cleanup' not in found and 'Remove-Item -LiteralPath $wrongPath' in cin and 'blocked by policy' in str(p.get('output')):
   found['policy-cleanup']=([(0,head,json.loads(head)),call,(off,line,v)],None,1180)
assert set(found)==set(targets)|{'policy-cleanup'},list(found)
bindings=[]
for chunk,(rows,actual,ordinal) in found.items():
 rawref=save('original-'+chunk+'.raw.jsonl',b''.join(r[1] for r in rows),True)
 actualexit=actual['exit_code'] if actual else None
 pyexit=0 if chunk=='b6819a' else None
 binding=save('original-'+chunk+'.binding.json',dict(schema='researchos.c19-review-actual-tool-binding.v1',actor_id='codex:/root/attach_restore_independent_review',
  Root_assigned_ordinal=ordinal,ordinal_self_issued=False,source_audit_path=str(SESSION),source_prefix_size_observed=prefix,
  source_line_offsets=[r[0] for r in rows],source_line_bytes=[len(r[1]) for r in rows],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in rows],
  call_id=rows[1][2]['payload']['call_id'],original_capture_ref=rawref,original_result=actual,actual_outer_exit=actualexit,actual_Python_exit=pyexit,
  actual_Native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_TP_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,
  tool_rejected_before_process=chunk=='policy-cleanup',PowerShell_nonterminating_child_error=chunk=='39fb10',
  Root_assigned_scope='diagnostic only' if ordinal else 'successful independent component review',
  not_rerun=True))
 bindings.append(dict(chunk_id=chunk,Root_assigned_ordinal=ordinal,binding_ref=binding))
decision=json.loads((N/'decision.json').read_bytes());pins=json.loads((N/'input-pins.json').read_bytes())
assert all(pin(r['path'])==r for r in pins)
# Prior rejected Source versions remain historical and are not upgraded by this component result.
prior=Path(decision['request_ref']['path']).parents[2].parent/'c19_order_Root_adopter_independent_review_codex'
# Resolve prior review directory from already pinned accepted-review HDF, without touching current Canon.
accepted_hdfs=[r for r in pins if r['path'].endswith('review-20261010-02\\HDF.json')]
assert len(accepted_hdfs)==1
accepted=json.loads(Path(accepted_hdfs[0]['path']).read_bytes())
old=accepted['v2_refused_decision_ref'];assert pin(old['path'])==old
olddecision=json.loads(Path(old['path']).read_bytes());assert olddecision['decision']=='REQUEST_CHANGES_SOURCE_ONLY'
failure_ref=save('diagnostics-and-preservation.json',dict(bindings=bindings,prior_v2_refused_ref=old,prior_v2_still_refused=True,
 policy_rejected_cleanup=True,cleanup_process_started=False,misplaced_file_removed=True,empty_wrong_namespace_retained=True,
 inspection_failures_not_reclassified_as_pass=True,Root_assigned_ordinals=[1176,1177,1178,1179,1180],
 actual_review_chunk='b6819a',actual_review_outer_exit=0,actual_review_Python_exit=0,SourceGuard_closed0=True,Native_SQL_Go_TP_Rootstage_calls=0))
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.c19-Main-actual-review-manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
hdf=save('HDF.json',dict(schema='researchos.c19-Main-actual-review-handoff.v1',actor_id='codex:/root/attach_restore_independent_review',
 actor_role='INDEPENDENT_NON_AUTHOR_NON_EXECUTOR',Root_executor='codex:/root',Root_thread_id=decision['Root_thread_id'],
 decision=decision['decision'],decision_ref=pin(N/'decision.json'),manifest_ref=mf,guard_ref=decision['guard_ref'],guards_closed0=True,stable_input_handles=len(pins),
 diagnostics_ref=failure_ref,actual_review_binding_ref=next(x['binding_ref'] for x in bindings if x['chunk_id']=='b6819a'),
 actual_Root_events=decision['Root_actual_events'],all_historical_Canon_verified_via_transaction_archives=True,
 future_execution_permitted=False,Source21_current_qualification_not_granted=True,Native_Mode_formal_acceptance=False,
 Main_Canon_Scope_writes=0,Native_SQL_Go_TP_Rootstage_calls=0,parent_acceptance=False,execution_grant=False,formal_acceptance=False,STOP=True))
assert all(pin(r['path'])==r for r in members)
print(json.dumps(dict(HDF_ref=hdf,MF_ref=mf,decision_ref=pin(N/'decision.json'),diagnostics_ref=failure_ref,decision=decision['decision'],member_count=len(members),guard_handles=len(pins),guards_closed0=True),ensure_ascii=False))


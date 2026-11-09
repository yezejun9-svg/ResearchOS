from pathlib import Path
import json,hashlib
N=Path(__file__).parent;P=N.parent/'continue-20261010-01'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,value,raw=False):
 with (N/name).open('xb') as f:f.write(value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
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
   matches=[x for x in values(p.get('output')) if isinstance(x,dict) and x.get('chunk_id')=='baa53e']
   if len(matches)==1 and 'build_revision_and_controls.py' in str(calls[p['call_id']][2]['payload'].get('input','')):
    found=([(0,header,json.loads(header)),calls[p['call_id']],(off,line,v)],matches[0]);break
assert found is not None
rows,result=found
assert result['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in result['output']
capture=save('actual-baa53e.raw.jsonl',b''.join(row[1] for row in rows),True)
binding=save('actual-baa53e.binding.json',dict(schema='researchos.source-revision-actual-control-binding.v1',
 actor_id='codex:/root/attach_restore_independent_review',source_audit_path=str(session),source_prefix_size_observed=prefix,
 source_line_offsets=[r[0] for r in rows],source_line_bytes=[len(r[1]) for r in rows],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in rows],
 original_call_id=rows[1][2]['payload']['call_id'],original_capture_ref=capture,actual_outer_exit=0,actual_Python_exit=0,
 Native_exit=None,Go_exit=None,SQL_exit=None,TP_exit=None,Rootstage_exit=None,synthetic_controls=3,product_success=False))
inverse=read(N/'revision-inverse.json')
assert all(pin(r['path'])==r for r in inverse['prior_namespace_protected_refs'])
contract=read(N/'root-calling-contract.source.json');decision=read(N/'source-decision.json')
assert contract['caller_ref']==decision['caller_ref']==pin(N/'public22_to23_root.source.py')
assert contract['source_inputs_ref']==decision['source_inputs_ref']==pin(N/'source-inputs.json')
assert decision['calling_contract_ref']==pin(N/'root-calling-contract.source.json')
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.public22-continuation-source-revision-manifest.v1',members=members,
 exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
hdf=read(P/'HDF.json')
hdf.update(manifest_ref=mf,caller_ref=pin(N/'public22_to23_root.source.py'),source_inputs_ref=pin(N/'source-inputs.json'),
 calling_contract_ref=pin(N/'root-calling-contract.source.json'),source_decision_ref=pin(N/'source-decision.json'),
 source_controls_ref=pin(N/'delta-source-controls.json'),Source_controls_only=3,historical_Source_controls_preserved=14,
 historical_review_prefix_ref=pin(N/'historical-review-prefix.json'),revision_inverse_ref=pin(N/'revision-inverse.json'),
 actual_control_binding_ref=binding,write_scope=str(N),revision='continue-20261010-02',
 self_acceptance=False,new_Source_failures=0,prior27_files_byte_unchanged=True,prior14_controls_not_rerun=True,
 prior781_resource_guard_not_rerun=True,old_four_Native_children_replayed=False,
 fix='Retain known observation inside output contexts before close; close faults recorded, pre-existing primary exceptions preserved.',
 remaining='Independent non-author revised Source review and future Root loaded runtime resource qualification/finite registration still required; no Native or formal acceptance.')
hdfref=save('HDF.json',hdf)
assert all(pin(r['path'])==r for r in members)
assert all(pin(r['path'])==r for r in inverse['prior_namespace_protected_refs'])
print(json.dumps(dict(status=hdf['status'],HDF_ref=hdfref,MF_ref=mf,caller_ref=hdf['caller_ref'],
 calling_contract_ref=hdf['calling_contract_ref'],controls_ref=hdf['source_controls_ref'],
 source_decision_ref=hdf['source_decision_ref'],actual_control_binding_ref=binding,member_count=len(members),
 controls=3,prior_files_unchanged=27,Native_Go_SQL_TP_Rootstage_calls=0,STOP=True),ensure_ascii=False))


from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
A=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v,raw=False):
 with (O/n).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
prefix=A.stat().st_size;start=max(0,prefix-12*1024*1024);calls={};found=None
with A.open('rb') as f:
 head=f.readline();f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:j=json.loads(line)
  except ValueError:continue
  p=j.get('payload',{});t=p.get('type')
  if j.get('type')=='response_item' and t in ('function_call','custom_tool_call'):calls[p.get('call_id')]=(off,line,j)
  if j.get('type')=='response_item' and t in ('function_call_output','custom_tool_call_output') and p.get('call_id') in calls and '475155' in str(p.get('output','')):
   c=calls[p['call_id']];inp=str(c[2]['payload'].get('input',c[2]['payload'].get('arguments','')))
   if 'prepare.py' in inp and '475155' not in inp:found=[(0,head,json.loads(head)),c,(off,line,j)];break
assert found is not None
raw=save('actual-prepare.raw.jsonl',b''.join(x[1] for x in found),True)
binding=save('actual-prepare.binding.json',dict(actor_id='codex:/root/attach_restore_independent_review',actual_chunk_id='475155',
 source_audit_path=str(A),source_prefix_size_observed=prefix,source_line_offsets=[x[0] for x in found],
 source_line_bytes=[len(x[1]) for x in found],original_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in found],
 original_capture_ref=raw,source_session_id=found[0][2]['payload']['id'],original_call_id=found[1][2]['payload']['call_id'],
 actual_outer_exit=0,actual_python_exit=0,Native_SQL_models_Rootstage_TP_calls=0))
for off,line,_ in found:
 with A.open('rb') as f:f.seek(off);assert f.read(len(line))==line
pins=json.loads((O/'input-pins.json').read_bytes())
assert all(pin(r['path'])==r for r in pins)
closed=json.loads((O/'SourceGuard.closed.json').read_bytes());assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.w09-br7-role-input-preparation-manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
handoff=dict(schema='researchos.w09-br7-role-input-preparation-handoff.v1',actor_id='codex:/root/attach_restore_independent_review',
 status='ROLE_INPUT_TEMPLATES_PREPARED_DYNAMIC_ROOT_FIELDS_NULL',manifest_ref=mf,
 template_ref=pin(O/'role-registry-input.template.json'),actual_role_audits_template_ref=pin(O/'actual-role-audits.template.json'),
 context_policy_template_ref=pin(O/'context-role-policy.template.json'),protection_template_ref=pin(O/'role-stage-protection.template.json'),
 fieldguide_ref=pin(O/'FIELD_GUIDE.md'),known_evidence_ref=pin(O/'known-role-evidence.json'),decision_ref=pin(O/'preparation-decision.json'),
 actual_prepare_raw_ref=raw,actual_prepare_binding_ref=binding,source_guard_closed_ref=pin(O/'SourceGuard.closed.json'),
 actual_roles_or_native_checks_run=False,Root_stage_Native_SQL_models_TP_calls=0,Main_Canon_Scope_Registry_writes=0,
 dynamic_fields_filled_from_future_events=False,existing_peer_original_ranges_verified=True,execution_grant=False,formal_acceptance=False,
 dynamic_inputs_not_ready_is_goal_block=False,STOP=True)
href=save('HDF.json',handoff)
assert all(pin(r['path'])==r for r in members)
print(json.dumps(dict(HDF_ref=href,MF_ref=mf,template_ref=handoff['template_ref'],fieldguide_ref=handoff['fieldguide_ref'],
 decision_ref=handoff['decision_ref'],protected_inputs=len(pins),SourceGuard_closed_zero=True),ensure_ascii=False))

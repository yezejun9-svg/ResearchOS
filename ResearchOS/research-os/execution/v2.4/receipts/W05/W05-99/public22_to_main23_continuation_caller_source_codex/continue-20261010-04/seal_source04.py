from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;P=O.parent/'continue-20261010-03'
A=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(Path(p).read_bytes())
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
  if j.get('type')=='response_item' and t in ('function_call_output','custom_tool_call_output') and p.get('call_id') in calls and 'df0258' in str(p.get('output','')):
   c=calls[p['call_id']];inp=str(c[2]['payload'].get('input',c[2]['payload'].get('arguments','')))
   if 'prepare_source04.py' in inp and 'df0258' not in inp:found=[(0,head,json.loads(head)),c,(off,line,j)];break
assert found is not None,'ACTUAL_PREPARE_CAPTURE_REQUIRED'
raw=save('actual-source04-prepare.raw.jsonl',b''.join(x[1] for x in found),True)
binding=save('actual-source04-prepare.binding.json',dict(schema='researchos.source04-actual-original-binding.v1',
 actor_id='codex:/root/attach_restore_independent_review',source_audit_path=str(A),source_prefix_size_observed=prefix,
 source_line_offsets=[x[0] for x in found],source_line_bytes=[len(x[1]) for x in found],
 original_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in found],actual_chunk_id='df0258',
 original_call_id=found[1][2]['payload']['call_id'],source_session_id=found[0][2]['payload']['id'],original_capture_ref=raw,
 actual_outer_exit=0,actual_python_exit=0,Native_SQL_Rootstage_TP_calls=0,new_original_failure_ordinal=None))
for off,line,_ in found:
 with A.open('rb') as f:f.seek(off);assert f.read(len(line))==line
protected=doc(O/'protected-inputs.json')
for r in protected:
 a=pin(r['path']);assert a['sha256']==r['sha256'] and a['bytes']==r['bytes']
closed=doc(O/'SourceGuard.closed.json');assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
controls=doc(O/'generation-delta-controls.json');assert controls['count']==19 and all(x['result']=='PASS' for x in controls['checks'])
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.public22-to-main23-continuation-source-manifest.v1',revision='continue-20261010-04',members=members,
 exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
prior=doc(P/'HDF.json')
h=dict(schema='researchos.public22-to-main23-continuation-source-handoff.v1',source_author='codex:/root/attach_restore_independent_review',
 status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',revision='continue-20261010-04',manifest_ref=mf,
 caller_ref=pin(O/'public22_to23_root.source.py'),source_inputs_ref=pin(O/'source-inputs.json'),calling_contract_ref=pin(O/'root-calling-contract.source.json'),
 source_decision_ref=pin(O/'source-decision.json'),source_controls_ref=pin(O/'generation-delta-controls.json'),
 historical_review_prefix_ref=pin(O/'historical-review-prefix.json'),revision_inverse_ref=pin(O/'revision-inverse.json'),
 predecessor_lineage_ref=pin(O/'predecessor-lineage.json'),source_guard_closed_ref=pin(O/'SourceGuard.closed.json'),
 review_notes_ref=pin(O/'SOURCE04_REVIEW_NOTES.md'),actual_prepare_raw_ref=raw,actual_prepare_binding_ref=binding,
 Source_controls_only=19,SourceGuard_closed=True,retained_handles_count=0,protected_prior_file_count=len(protected),
 new_native_phases=['upgrade22to23','backup23','verify23'],Native_SQL_models_TP_Rootstage_calls=0,
 MainCanonScope_writes=0,live_Canon_reads=0,old_12_26_144_149_replayed=False,
 original1025='FAILED_RETAINED',original1201='FAILED_RETAINED',new_failure_ordinals=[],
 KEY='public22_to_main23_continuation_gen02',SLICE='PUBLIC22_TO_MAIN23_CONTINUATION_GEN02',
 MODE_schema_business_gates_unchanged=True,write_scope=str(O),formal_acceptance=False,parent_acceptance=False,
 execution_grant=False,self_acceptance=False,formal_case_accepted_delta=0,
 remaining='True Full non-author Source04 review; then fresh actual Root registration, Scope, current4, finite lease, request and hostpairs. Old consumed Scope stays closed.',STOP=True)
for k in ('runtime_resources_ref','main23_bound_ref','existing22_decision_ref'):h[k]=prior[k]
href=save('HDF.json',h)
assert all(pin(r['path'])==r for r in members)
print(json.dumps(dict(status=h['status'],HDF_ref=href,MF_ref=mf,caller_ref=h['caller_ref'],contract_ref=h['calling_contract_ref'],
 decision_ref=h['source_decision_ref'],controls_count=19,protected_prior_files=len(protected),guard_closed_zero=True),ensure_ascii=False))

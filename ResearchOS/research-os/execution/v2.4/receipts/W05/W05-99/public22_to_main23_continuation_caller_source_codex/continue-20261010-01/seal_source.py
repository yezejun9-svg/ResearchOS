from pathlib import Path
import ast,hashlib,json
N=Path(__file__).parent
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
session=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
calls={};head=None;offset=0;found={};observed_size=session.stat().st_size
targets={1174:('prepare_controls_and_contract.py','f5366b'),1175:('prepare_controls_and_contract.corrected.py','9b1011')}
with session.open('rb') as f:
 for line in f:
  here=offset;offset+=len(line)
  try:v=json.loads(line)
  except ValueError:continue
  p=v.get('payload',{})
  if v.get('type')=='session_meta' and head is None:head=(here,line,v)
  if v.get('type')=='response_item' and p.get('type') in ('custom_tool_call','function_call'):calls[p.get('call_id')]=(here,line,v)
  if v.get('type')=='response_item' and p.get('type') in ('custom_tool_call_output','function_call_output') and p.get('call_id') in calls:
   output=str(p.get('output',''));call=calls[p['call_id']];input_text=str(call[2]['payload'].get('input',call[2]['payload'].get('arguments','')))
   for ordinal,(script,chunk) in targets.items():
    if ordinal not in found and script+"'; $actualExit" in input_text and 'Traceback' in output and 'ROOT_PYTHON_EXIT=1' in output:
     found[ordinal]=[head,call,(here,line,v)]
assert set(found)==set(targets),list(found)
bindings=[pin(N/'original1170.binding.json'),pin(N/'original1171.binding.json')]
for ordinal,rows in found.items():
 blob=b''.join(x[1] for x in rows);out=N/('original'+str(ordinal)+'.raw.jsonl')
 with out.open('xb') as f:f.write(blob)
 binding=dict(schema='researchos.source-author-original-tool-binding.v1',source_actor='codex:/root/attach_restore_independent_review',
  source_audit_path=str(session),source_prefix_size_observed=observed_size,
  source_line_offsets=[x[0] for x in rows],source_line_bytes=[len(x[1]) for x in rows],
  original_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in rows],original_call_id=rows[1][2]['payload']['call_id'],original_capture_ref=pin(out),
  Root_assigned_ordinal=ordinal,tool_chunk_id=targets[ordinal][1],outer_exit=1,Python_exit=1,Native_exit=None,SQL_exit=None,TP_exit=None,
  automatic_native_retry=False,root_authority=False,original_script_ref=pin(N/targets[ordinal][0]))
 save('original'+str(ordinal)+'.binding.json',binding);bindings.append(pin(N/('original'+str(ordinal)+'.binding.json')))
save('diagnostics.final.json',dict(original_failures=bindings,assigned_by='codex:/root',first_source_control_failures_retained=True,
 corrected_control_entry_ref=pin(N/'prepare_controls_and_contract.corrected2.py'),corrected_control_result_ref=pin(N/'delta-source-controls.json'),
 Native_Go_SQL_TP_dispatcher_model_exits=None))
contract=json.loads((N/'root-calling-contract.source.json').read_bytes())
contract['Source_review_required_fields']+=['source_hdf_ref','source_mf_ref','caller_ref','source_inputs_ref','calling_contract_ref','runtime_resources_ref','main23_bound_ref','existing22_decision_ref']
contract['execute_output_rule']='One unused output root consumes the attempt; any failure retains it and refuses automatic retry. Root must seal complete actual call/output and send component result for independent review.'
contract['register_result_semantics']='build/check/activate are future Root-only Source entrypoints; this author has not called any.'
(N/'root-calling-contract.source.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
source=(N/'public22_to23_root.source.py').read_bytes();ast.parse(source)
assert contract['caller_ref']==pin(N/'public22_to23_root.source.py')
assert contract['source_inputs_ref']==pin(N/'source-inputs.json')
controls=json.loads((N/'delta-source-controls.json').read_bytes());assert controls['count']==14 and all(x['result']=='PASS' for x in controls['checks'])
save('source-decision.json',dict(schema='researchos.public22-to-main23-continuation-source-delivery.v1',
 source_author='codex:/root/attach_restore_independent_review',status='SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW',
 caller_ref=pin(N/'public22_to23_root.source.py'),calling_contract_ref=pin(N/'root-calling-contract.source.json'),
 source_inputs_ref=pin(N/'source-inputs.json'),controls_ref=pin(N/'delta-source-controls.json'),
 diagnostic_refs=bindings,original_failures=[1170,1171,1174,1175],
 new_executable_phases=['upgrade22to23','backup23','verify23'],original_four_children_replayed=False,
 Main_Canon_original_artifact_mutations=False,Native_SQL_Go_TP_RootStage_calls_by_author=0,
 private_owner_key_read_hash_copy=False,full20to24='OPEN',formal_acceptance=False,parent_acceptance=False,execution_grant=False,
 formal_case_accepted_delta=0,independent_Source_runtime_review_and_fresh_Root_registration_required=True))
exclude={'HDF.json','MF.json','postseal-tool-io.json'}
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in exclude]
save('MF.json',dict(schema='researchos.source-manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
i=json.loads((N/'source-inputs.json').read_bytes())
save('HDF.json',dict(schema='researchos.public22-to-main23-continuation-source-handoff.v1',
 source_author='codex:/root/attach_restore_independent_review',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',
 manifest_ref=pin(N/'MF.json'),caller_ref=pin(N/'public22_to23_root.source.py'),
 source_inputs_ref=pin(N/'source-inputs.json'),calling_contract_ref=pin(N/'root-calling-contract.source.json'),
 source_decision_ref=pin(N/'source-decision.json'),source_controls_ref=pin(N/'delta-source-controls.json'),
 diagnostic_ref=pin(N/'diagnostics.final.json'),original_failure_ordinals=[1170,1171,1174,1175],
 main23_bound_ref=i['main23_bound_ref'],existing22_decision_ref=i['existing22_decision_ref'],runtime_resources_ref=i['runtime_resources_ref'],
 new_native_phases=['upgrade22to23','backup23','verify23'],original1025='FAILED_RETAINED',
 current4_dynamic_cas=True,formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,
 Source_controls_only=14,Source_author_Native_SQL_Go_TP_RootStage_calls=0,
 write_scope=str(N),remaining='Independent Source/runtime qualification, fresh Root registration/finite owner lease, actual3child observations and independent component review; full20to24 remains OPEN.',
 postseal_tool_io_excluded=True,STOP=True))
mf=json.loads((N/'MF.json').read_bytes())
assert all(pin(r['path'])==r for r in mf['members'])
print(json.dumps(dict(HDF_ref=pin(N/'HDF.json'),MF_ref=pin(N/'MF.json'),calling_contract_ref=pin(N/'root-calling-contract.source.json'),members=len(members),all_members_match=True),ensure_ascii=False))


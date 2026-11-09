import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 raw=Path(p).read_bytes();return {'path':str(Path(p)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(name,obj):
 with (O/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/name)
inputs=json.loads((O/'input-intake.json').read_bytes())['input_refs'];unique={}
for ref in inputs:unique[(str(Path(ref['path'])),ref['sha256'],ref['bytes'])]=ref
for ref in unique.values():
 a=pin(ref['path']);assert a['sha256']==ref['sha256'] and a['bytes']==ref['bytes']
recheck=put('final-input-recheck.json',{'input_refs':list(unique.values()),'unique_input_count':len(unique),'input_drift':0})
s=pin(O/'root_coordinator.py');assert s['sha256']=='12a7c6e78b80a56860ecdef97d29460322bdaeede17be22d3c171dbd6b35ea9a' and s['bytes']==55715
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('handoff.json','manifest.json')]
m=put('manifest.json',{'schema':'researchos.source-packet-manifest.v1','actor_id':'codex:/root/command_queue_impl','members':members,'member_count':len(members),'input_refs':list(unique.values()),'excludes_self_and_handoff_to_avoid_hash_cycle':True})
h=put('handoff.json',{'schema':'researchos.root-sdk-coordinator-source-handoff.v5','actor_id':'codex:/root/command_queue_impl','decision':'IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW','manifest_ref':m,'source_ref':s,'fixed_pins_ref':pin(O/'fixed-pins.json'),'control_ref':pin(O/'delta-controls.json'),'report_ref':pin(O/'REPORT.md'),'forward_ref':pin(O/'source.forward.diff'),'inverse_ref':pin(O/'source.inverse.diff'),'original_tool_io_ref':pin(O/'original-tool-io.json'),'model_trial_template_ref':pin(O/'input.model-trial.template.json'),'no_provider_template_ref':pin(O/'input.no-provider.template.json'),'root_authority_template_ref':pin(O/'root-execution-authority.template.json'),'independent_review_template_ref':pin(O/'independent-source-review.template.json'),'closed_source_findings':['R01','R02'],'new_delta_controls':2,'new_delta_controls_passed':2,'R01_negative_cases':9,'R02_negative_cases':22,'actual_public_receipt_positive_cases':True,'prior_controls_reused_not_rerun':[40,1,2,2],'fixed_roles_reused_not_rehashed':24,'fixed_roles_changed':[],'constructors':1,'unique_input_count':len(unique),'input_drift':0,'new_tool_failures':0,'candidate_module_imported':False,'coordinator_methods_executed':False,'Native_WinAPI_SQL_provider_calls':0,'Main_canonical_writes':0,'runtime_qualification':False,'formal_acceptance':False,'execution_grant_issued':False,'stopped':True})
print(json.dumps({'handoff':h,'manifest':m,'source':s,'members':len(members),'unique_inputs':len(unique),'input_drift':0},ensure_ascii=True))


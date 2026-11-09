import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(p):
 raw=Path(p).read_bytes();return {'path':str(Path(p)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(name,obj):
 with (OUT/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(OUT/name)
inputs=json.loads((OUT/'input-intake.json').read_bytes())['input_refs']
unique={}
for ref in inputs:
 key=(str(Path(ref['path'])),ref['sha256'],ref['bytes']);unique[key]=ref
checks=[]
for ref in unique.values():
 actual=pin(ref['path']);assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
 checks.append({'input_ref':ref,'matched':True})
put('final-input-recheck.json',{'inputs':checks,'unique_input_count':len(checks),'input_drift':0})
source=pin(OUT/'root_coordinator.py')
assert source['sha256']=='19aa54ccae05265435dcd4019444307eadd4e7971964c9e9dcc079be4c9eca9b' and source['bytes']==50556
controls=json.loads((OUT/'delta-controls.json').read_bytes());assert controls['new_controls']==2 and controls['passed']==2
members=[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
manifest=put('manifest.json',{'schema':'researchos.source-packet-manifest.v1','actor_id':'codex:/root/command_queue_impl','members':members,'member_count':len(members),'input_refs':list(unique.values()),'excludes_self_and_handoff_to_avoid_hash_cycle':True})
handoff=put('handoff.json',{'schema':'researchos.root-sdk-coordinator-source-handoff.v4','actor_id':'codex:/root/command_queue_impl','decision':'IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW','manifest_ref':manifest,'source_ref':source,'fixed_pins_ref':pin(OUT/'fixed-pins.json'),'control_ref':pin(OUT/'delta-controls.json'),'report_ref':pin(OUT/'REPORT.md'),'forward_ref':pin(OUT/'source.forward.diff'),'inverse_ref':pin(OUT/'source.inverse.diff'),'original_tool_io_ref':pin(OUT/'original-tool-io.json'),'model_trial_template_ref':pin(OUT/'input.model-trial.template.json'),'no_provider_template_ref':pin(OUT/'input.no-provider.template.json'),'root_authority_template_ref':pin(OUT/'root-execution-authority.template.json'),'independent_review_template_ref':pin(OUT/'independent-source-review.template.json'),'new_delta_controls':2,'new_delta_controls_passed':2,'prior_controls_reused_not_rerun':[40,1,2],'fixed_role_count':24,'fixed_roles_changed':['trusted_host_binary'],'inherited_fixed_roles_reused_not_rehashed':23,'new_current_helper_evidence_guarded_separately':True,'constructors':2,'constructor1_outputs_retained':True,'input_count':len(checks),'input_drift':0,'new_tool_failures':[739],'nonfailure_observations':[740],'candidate_module_imported':False,'candidate_native_WinAPI_SQL_provider_calls':0,'Main_canonical_writes':0,'bootstrap_accepted':False,'runtime_qualification':False,'formal_acceptance':False,'execution_grant_issued':False,'stopped':True})
print(json.dumps({'handoff':handoff,'manifest':manifest,'source':source,'members':len(members),'unique_input_count':len(checks),'input_drift':0},ensure_ascii=True))


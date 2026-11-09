import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(path):
    raw=Path(path).read_bytes();return {'path':str(Path(path)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(name,value):
    with (OUT/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(OUT/name)
build=json.loads((OUT/'build-result.json').read_bytes());assert pin(OUT/'root_coordinator.py')==build['source_ref']
reuse=json.loads((OUT/'reuse-evidence.json').read_bytes());unique={str(Path(r['path'])).lower():r for r in reuse['input_refs']}
for ref in unique.values():
    current=pin(ref['path']);assert current['sha256']==ref['sha256'] and current['bytes']==ref['bytes']
put('final-input-recheck.json',{'input_refs':list(unique.values()),'unique_inputs':len(unique),'input_drift':0,'fixed_24_role_pins_reused_not_rehashed':True})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
mf=put('manifest.json',{'schema':'researchos.source-packet-manifest.v1','actor_id':'codex:/root/command_queue_impl','members':members,'member_count':len(members),'input_refs':list(unique.values()),'excludes_self_and_handoff_to_avoid_hash_cycle':True})
hdf=put('handoff.json',{'schema':'researchos.root-sdk-coordinator-source-handoff.v3','actor_id':'codex:/root/command_queue_impl','decision':'IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_DELTA_REVIEW','manifest_ref':mf,'source_ref':build['source_ref'],'fixed_pins_ref':build['fixed_pins_ref'],'control_ref':build['control_ref'],'report_ref':pin(OUT/'REPORT.md'),'forward_ref':pin(OUT/'source.forward.diff'),'inverse_ref':pin(OUT/'source.inverse.diff'),'original_tool_io_ref':pin(OUT/'original-build-control-tool-io.json'),'independent_review_handoff_ref':reuse['independent_review_handoff_ref'],'no_provider_template_ref':pin(OUT/'input.no-provider.template.json'),'model_trial_template_ref':pin(OUT/'input.model-trial.template.json'),'root_authority_template_ref':pin(OUT/'root-execution-authority.template.json'),'independent_review_template_ref':pin(OUT/'independent-source-review.template.json'),'finding_repairs':['R01','R02'],'new_delta_controls':2,'new_delta_controls_passed':2,'prior_controls_reused_not_rerun':[40,1],'fixed_role_pins_reused_not_rehashed':24,'input_count':len(unique),'input_drift':0,'new_tool_failures':0,'candidate_native_WinAPI_SQL_provider_calls':0,'Main_canonical_writes':0,'bootstrap_accepted':False,'runtime_qualification':False,'formal_acceptance':False,'execution_grant_issued':False,'stopped':True})
print(json.dumps({'handoff_ref':hdf,'manifest_ref':mf,'source_ref':build['source_ref'],'members':len(members),'inputs':len(unique),'drift':0,'new_controls':2,'passed':2,'new_failures':0}))

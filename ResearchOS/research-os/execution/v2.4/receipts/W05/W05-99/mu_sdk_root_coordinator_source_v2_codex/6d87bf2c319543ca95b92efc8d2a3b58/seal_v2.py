import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(path):
    raw=Path(path).read_bytes()
    return {'path':str(Path(path)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(name,doc):
    with (OUT/name).open('xb') as f:f.write((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(OUT/name)
build=json.loads((OUT/'build-result.json').read_bytes())
assert pin(OUT/'root_coordinator.py')==build['source_ref']
reuse=json.loads((OUT/'reuse-evidence.json').read_bytes())
for ref in reuse['old_packet_refs']:
    current=pin(ref['path']);assert current['sha256']==ref['sha256'] and current['bytes']==ref['bytes']
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
mf=put('manifest.json',{'schema':'researchos.source-packet-manifest.v1','actor_id':'codex:/root/command_queue_impl','members':members,'member_count':len(members),'input_refs':reuse['old_packet_refs'],'excludes_self_and_handoff_to_avoid_hash_cycle':True})
hdf=put('handoff.json',{'schema':'researchos.root-sdk-coordinator-source-handoff.v2','actor_id':'codex:/root/command_queue_impl','decision':'IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW','manifest_ref':mf,'source_ref':build['source_ref'],'fixed_pins_ref':build['fixed_pins_ref'],'control_ref':build['control_ref'],'original_tool_io_ref':pin(OUT/'original-build-control-tool-io.json'),'report_ref':pin(OUT/'REPORT.md'),'forward_ref':pin(OUT/'source.forward.diff'),'inverse_ref':pin(OUT/'source.inverse.diff'),'no_provider_template_ref':pin(OUT/'input.no-provider.template.json'),'model_trial_template_ref':pin(OUT/'input.model-trial.template.json'),'root_authority_template_ref':pin(OUT/'root-execution-authority.template.json'),'independent_review_template_ref':pin(OUT/'independent-source-review.template.json'),'prior_controls_reused_not_rerun':40,'prior_role_pins_reused_not_rehashed':24,'new_controls':1,'new_controls_passed':1,'matrix_cases':4,'new_tool_failures':0,'candidate_native_WinAPI_SQL_provider_calls':0,'Main_canonical_writes':0,'runtime_qualification':False,'formal_acceptance':False,'execution_grant_issued':False,'stopped':True})
print(json.dumps({'handoff_ref':hdf,'manifest_ref':mf,'source_ref':build['source_ref'],'members':len(members),'new_controls':1,'passed':1,'new_failures':0}))

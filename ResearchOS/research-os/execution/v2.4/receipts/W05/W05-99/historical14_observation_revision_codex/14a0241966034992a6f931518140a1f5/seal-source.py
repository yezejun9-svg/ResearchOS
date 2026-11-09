from pathlib import Path
import json,hashlib
own=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/historical14_observation_revision_codex/14a0241966034992a6f931518140a1f5');b=own.parent.parent
payload=json.loads((own/'original-tool-io.json').read_bytes())
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,data):
 (own/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert own.is_dir() and not (own/'HDF.json').exists() and not (own/'MF.json').exists()
write('original-tool-io.json',payload)
write('failure-origin.787.json',payload['failure_origin_787'])
payload['failure_origin_788']['parent_assignment_pending']=False
payload['failure_origin_788']['parent_assigned_ordinal']=788
write('failure-origin.788.json',payload['failure_origin_788'])
base=b/'prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6'
actual=b/'integration_codex/prepared-historical-regression-v2-root-874fa4a2c127e90c'
inv=json.loads((actual/'prepared-and-historical-backup-regression.invocation.json').read_bytes())
write('root-test-profile.json',{'schema':'researchos.root-test-profile.v1','prior_invocation':ref(actual/'prepared-and-historical-backup-regression.invocation.json'),'argv':inv['argv'],'public_environment':inv['public_environment'],'cwd_requirement':'new Root isolated composition with only this two-file overlay replacing corresponding 6b0 test files','run_by_source_author':False})
pins=json.loads((own/'base-pins.json').read_bytes())
for p in pins:
 got=ref(Path(p['path']));assert got==p,p['path']
members={str(p.relative_to(own)).replace('\\','/'):ref(p) for p in sorted(own.rglob('*')) if p.is_file()}
source={key:value for key,value in members.items() if key.startswith('candidate-root/')}
assert len(source)==2
write('MF.json',{'schema':'researchos.source-manifest.v1','formal':False,'members':members,'member_count':len(members),'source_refs':source,'base_refs':pins,'input_drift_count':0})
write('HDF.json',{'schema':'researchos.historical14-observation-revision-handoff.v1','status':'SOURCE_IMPLEMENTED_PENDING_ROOT_TESTS_AND_INDEPENDENT_REVIEW','sourceStatus':'EXECUTION_REPORTED','formal':False,'production_ready':False,'execution_authority':False,'source_root':str(own/'candidate-root'),'source_file_count':2,'source_refs':source,'manifest_ref':ref(own/'MF.json'),'previous_source_handoff':ref(base/'HDF.json'),'previous_source_manifest':ref(base/'MF.json'),'contract_ref':ref(own/'CONTRACT.md'),'patch_ref':ref(own/'revision.patch'),'method_provenance_ref':ref(own/'historical14-observation-provenance.json'),'diagnosis_ref':ref(own/'diagnosis.json'),'static_evidence_ref':ref(own/'static-evidence.json'),'original_tool_io_ref':ref(own/'original-tool-io.json'),'root_test_profile_ref':ref(own/'root-test-profile.json'),'failure_origins':[ref(own/'failure-origin.787.json'),ref(own/'failure-origin.788.json')],'root_failures_preserved_not_recounted':[785,786],'previous_same_class_failure_783_preserved':True,'input_pin_count':len(pins),'input_drift_count':0,'composition_note':'Overlay only these two test files after the existing Root 38-file composition. Keep latest schema22 bridge/current import revision and all current native/migration product Source. No old 6b0 full-root replacement.','actual_author_execution':{'python_metadata_source_writes':True,'go':False,'gofmt':False,'tests':False,'native':False,'sql':False,'provider':False,'signing':False,'private_resource_ref_read':False,'git':False,'Main_write':False,'canonical_write':False,'existing_source_or_worktree_write':False},'remaining_gates':['Root exact input/member verification','Root format and full domain package build','Root original targeted historical suite with matching resources','Root independent Source and result review'],'native_harness_status':'NOT_WRITTEN; queued after this original historical fixture is closed'})
for rel,p in members.items():assert ref(own/rel)==p
assert json.loads((own/'HDF.json').read_bytes())['manifest_ref']==ref(own/'MF.json')
for p in pins:assert ref(Path(p['path']))==p
print(json.dumps({'own':str(own),'HDF':ref(own/'HDF.json'),'MF':ref(own/'MF.json'),'source_refs':source,'members':len(members),'input_pins':len(pins),'input_drift_count':0},ensure_ascii=True))


from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 with (O/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
delta=json.loads((O/'bounded-delta-checks.json').read_bytes());gate=json.loads((O/'resource-gate-checks.json').read_bytes());assert len(delta)==22 and len(gate)==4201 and all(x['passed'] for x in delta+gate)
binding=json.loads((O/'resource-gate-binding.json').read_bytes());gb=json.loads((O/'inputs/HDF.json').read_bytes());initial=json.loads((O/'initial-pins.json').read_bytes())
save('diagnostic-disposition.json',dict(new_failure_ordinals=[919],origin_ref=pin(O/'origin.919.json'),original_io_ref=pin(O/'capture-original-failure.tool-io.json'),corrected_io_ref=pin(O/'capture-corrected.tool-io.json'),corrected_guard_ref=pin(O/'packet-guard.json'),old_failed_instance_close_return_captured=False,product_native_exit=None,source_changed=False,canonical_changed=False))
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name not in ('HDF.json','MF.json','postseal.json'))
# Top-level HDF/MF excluded; preserve already captured input HDF/MF as members.
files=sorted(p for p in O.rglob('*') if p.is_file() and p not in (O/'HDF.json',O/'MF.json',O/'postseal.json'))
save('MF.json',dict(schema='researchos.gbr-resource-gate-independent-manifest.v1',members=[pin(p) for p in files],member_count=len(files),excludes=['HDF.json','MF.json','postseal.json']))
h=dict(schema='researchos.gbr-resource-gate-independent-handoff.v1',status='SOURCE_ACCEPTED_FOR_ROOT_BOUNDED_ARCHIVE_RESOURCE_GATE',candidate_handoff_ref=initial[0],candidate_manifest_ref=initial[1],helper_ref=gb['source_ref'],manifest_ref=pin(O/'MF.json'),report_ref=pin(O/'report.md'),delta_checks_ref=pin(O/'bounded-delta-checks.json'),boundary_observations_ref=pin(O/'boundary-observations.json'),resource_checks_ref=pin(O/'resource-gate-checks.json'),resource_binding_ref=pin(O/'resource-gate-binding.json'),input_pins_ref=pin(O/'resource-gate-input-pins.json'),guard_ref=pin(O/'resource-gate-guard.final.json'),diagnostic_ref=pin(O/'diagnostic-disposition.json'),old_GPA_ref=binding['old_GPA_review_ref'],AF_review_ref=binding['AF_review_ref'],AF_manifest_ref=binding['AF_manifest_ref'],builder_ref=binding['builder_ref'],C12_prelaunch_ref=binding['C12_prelaunch_ref'],config_ref=binding['config_ref'],GPA_R01='CLOSED_FOR_EXACT_REVISED_SOURCE',delta_checks=22,boundary_cases=15,resource_checks=4201,total_checks=4223,failed_checks=0,resource_inputs=4368,frozen_inputs=4185,CP_revision=364,manual_callers_unchanged=True,archive_before_release_required=True,archive_actual_done=False,actual_builder_main_compose_helper=False,actual_native_Go_SQL_productAPI_private_model=False,actual_product_native_exit=None,formal_acceptance=False,full20_to24='OPEN',new_failure_ordinals=[919],guard_released=True,STOP=True,FINAL=True)
save('HDF.json',h);print(json.dumps(dict(HDF=pin(O/'HDF.json'),MF=pin(O/'MF.json'),origin919=pin(O/'origin.919.json'),status=h['status']),ensure_ascii=False))

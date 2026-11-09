import ast,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=N.parents[1]/'main_c19_source_registry_v2_source_codex/Mainv2-1a11fbc'
ACTOR='codex:/root/attach_fixture_source_review'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());r=json.loads((N/'result.json').read_bytes());cleanup=json.loads((N/'source-guard.cleanup.actual.json').read_bytes());decision=json.loads((N/'source-decision.json').read_bytes());contract=json.loads((C/'root-calling-contract.json').read_bytes())
assert all(pin(v['path'])==v for v in refs)
assert r['checks']==49 and r['pins']==235 and r['cross_controls']==21 and cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
assert set(decision)==set(contract['source_review_required_fields']) and decision['actor_id']==ACTOR and decision['actor_id'] not in contract['source_review_actor_must_differ_from']
save('MF.json',dict(schema='researchos.w09-main-c19-independent-source-review-manifest.v1',source_revision='v2',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.w09-main-c19-independent-source-review-handoff.v1',source_revision='v2',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',decision=decision['decision'],status=decision['decision'],manifest_ref=pin(N/'MF.json'),source_decision_ref=pin(N/'source-decision.json'),source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=pin(C/'MF.json'),caller_ref=decision['caller_ref'],change_set_ref=decision['change_set_ref'],exact_targets=decision['exact_targets'],report_ref=pin(N/'REPORT.md'),result_ref=pin(N/'result.json'),controls_ref=pin(N/'controls.json'),guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),independent_checks=49,cross_interface_controls=21,finite_exact_input_pins=235,all_acquired_guards_closed=True,retained_handles=0,original_cross_caller_P1_fixed=True,caller_metadata_complete_byte_inverse_pass=True,seven_target_bytes_unchanged=True,Rootfacts_scope_transform_full_Main_validate_scope_pass=True,virtual_scope_CP_OW_vector_only=True,new_original_failures=[],actual_adoption_executed=False,Main_Canon_written=False,Go_Git_SQL_API_model_dispatcher_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,requires_new_Root_scope_registration_vector_request=True,STOP=True,FINAL=True))
# Read the sealed reviewer pair with the exact Main manifest reader, no caller main.
tree=ast.parse((C/'adopt_main_c19.source.py').read_bytes());names={'require','digest','exact_path','raw_pin','read_ref','manifest_refs'}
ns=dict(Path=Path,hashlib=hashlib,json=json,MAX=256*1024*1024,TARGETS=tuple(Path(v) for v in decision['exact_targets']))
exec(compile(ast.Module(body=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in names],type_ignores=[]),'<pure-Main-sealed-review-reader>','exec'),ns)
rh,rr=ns['manifest_refs'](pin(N/'HDF.json'),pin(N/'MF.json'))
assert rh['actor_id']==ACTOR and rh['source_decision_ref'] in rr and json.loads(ns['read_ref'](rh['source_decision_ref']))==decision
assert all(k in rh for k in contract['source_review_handoff_required_fields'])
assert all(pin(v['path'])==v for v in refs)
save('postseal.json',dict(status='PASS_SEALED_REVIEW_REAL_MAIN_READER',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),source_decision_ref=pin(N/'source-decision.json'),exact_source_decision_member_loaded_by_Main_reader=True,all_input_pins_unchanged=len(refs)))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),source_decision_ref=pin(N/'source-decision.json'),postseal_ref=pin(N/'postseal.json'))))

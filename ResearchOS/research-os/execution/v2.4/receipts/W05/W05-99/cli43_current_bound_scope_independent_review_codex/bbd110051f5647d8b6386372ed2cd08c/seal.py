from pathlib import Path
import json, hashlib
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
def ref(p):
 p=Path(p); raw=p.read_bytes(); return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def load(p): return json.loads(Path(p).read_bytes())
def write(name,obj):
 with (O/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
a=load(O/'audit.json'); f=a['facts']; s=load(f['scope_ref']['path']); n=Path(f['scope_ref']['path']).parent
assert not a['failed_checks'] and len(a['checks'])==269
for row in f['canonical_before']:
 assert (R/row['canonical_path']).read_bytes()==Path(row['ref']['path']).read_bytes()
assert all(not Path(p).exists() for p in f['fresh_leaves'])
write('audit.execution.json',{'actor':'codex:/root/w05_merge_review','tool_chunk_id':'c887da','actual_outer_exit':0,'actual_Python_native_exit':0,'exit_bridge':'PowerShell captured LASTEXITCODE immediately after own auditor and explicitly returned it. Files retain redirected auditor streams; no target/native product invocation.','script_ref':ref(O/'audit.py'),'stdout_ref':ref(O/'audit.stdout.raw'),'stderr_ref':ref(O/'audit.stderr.raw'),'checks':269,'failed_checks':0,'target_modules_imported':0,'target_native_calls':0,'new_failure_origins':[]})
review={'schema':'researchos.cli43-compiler-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_CURRENT43_HELD2_ONCE','requested_changes':[],
 'scope_sha256':s and f['scope_ref']['sha256'],'runner_sha256':s['runner_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_gate_ref']['sha256'],
 'scope_ref':f['scope_ref'],'bound_manifest_ref':ref(n/'bound-scope.manifest.json'),'audit_ref':ref(O/'audit.json'),'audit_execution_ref':ref(O/'audit.execution.json'),
 'actual_execution_authorized_by_this_review':False,'actual_candidate_or_product_execution_by_reviewer':False,'actual_registration_executed':False,'source_acceptance':False,'formal_increment':0,
 'expected_before':f['before'],'expected_after':f['after'],'current_source_commit':s['source_commit'],'canonical_before':f['canonical_before'],'new_failure_origins':[],
 'conditions':['A new actual Root CAS [327,155,459], successful sealed registration, exact nonauthor registration review and one unique actual grant must all pass before the two ordered cases may run. This review is not that grant.',
 'Use only the declared fresh output/export/cache/WORK/compiler artifacts. Enforce current source/tool/resource pins, complete actual Go graph and debug observations before qualifying cases. Unknown input, drift, unexpected failure or incomplete capture stops the dependent run; no automatic same-input retry.',
 'No current43 business/source/parent/formal acceptance, no Main integration or expansion to old47/other cases.'],
 'runner_delta':{'change':'Exactly -p=1 at build-cli and build-test, +14 bytes; whole byte and AST inverse equals v5.','lines':[464,465],'whole_file_inverse_verified':True,'prior_v5_go_list_buildvcs_false_preserved':True,'meaning':'Go build worker scheduling only. It does not cap compiler internal threads or prove the prior failure was a quota or interruption error.','prior_build_root_cause':None,'new_cases':'NOT_RUN'},
 'scope_protection':{'scope_delta_keys':f['scope_delta_keys'],'template_delta_keys':f['template_delta_keys'],'bound_manifest_actual_members':f['bound_manifest_members'],'bound_manifest_parent_summary_17_not_used':True,
 'ordered_cases':s['ordered_cases'],'limits':s['limits'],'launch_limits':s['launch_limits'],'public_environment':s['public_environment'],'main_git_pinned_facts':s['main_git'],
 'fresh_five_leaves_absent':True,'final_binding_prepare_not_started':True,'original450_prefix_preserved':True,'cut9_original_payload_refs':f['origin_refs'],'oldlate8_exact_identity_and_pointer_payloads':True,'r326_build_underlying_origin_count':1,'nested_exit_propagation_not_counted_as_three':True,
 'later_peer4ddd35_and_Source4024a7_not_added_to_fixed_cut9':True,'late_observed461_is_parent_report_not_canonical_mutation':True,'source_bd3_scope_deviation_not_inferred_native1':True,
 'six_v7_wrappers_unchanged':True,'metadata8_ROOT_relative_serialized_pins_exact':True,'runtime1250_contains_same1242_plus_actual8_ABS_metadata':True,'v7_marker_only_after_strict_observation_success':True,'outerdriver_inverse_only_scope_sha':True,
 'Root_relative_scope_ref_matches_gate_exactdict':True,'review_path_no_hash_cycle':True,'same_9_image_policy_Job16_total2048_build600_limits':'Preserved by complete runner inverse and unchanged debug/launcher bytes; not measured anew.',
 'stage_source_ref':f['stage_ref'],'stage_review':'Metadata-only two invokes, pinned inputs, exclusive writes, four-canonical byte invariance and original r326 namespace prefix guard; no helper/Git/product invoke.'},
 'reuse_and_limits':{'review_refs':f['reused_review_refs'],'prior187_full_scope_checks_and135_parallelism_checks':'Reused sealed findings, with this review separately verifying the new bound delta and code bytes; not rerun product results.',
 'source597_rows_reused_not_backing_source_rehash':True,'compiler22138_catalog_pinned_not_full_backing_rehash':True,'runtime1242_rows_reused':True,'metadata8_current_bytes_actually_rehashed':True,
 'Root_scope_builder_hashing_not_independent_reviewer_full_resource_rehash':True,'actual_future_Go_graph_complete':None,'actual_future_OS_loader_complete':None,'54_PE_candidate_set_not_complete_loader_proof':True,'Python_POINT_IN_TIME_NOT_LIFECYCLE':True,'time_fit_proved':False,'case_or_product_pass_claims':0},
 'verification':{'readonly_checks':269,'failed_checks':0,'auditor_outer_exit':0,'auditor_Python_native_exit':0,'target_executions':0,'canonical_source_index_writes':0},'status':'STOPPED'}
write('review.json',review)
write('handoff.json',{'schema':'researchos.independent-review-handoff.v1','actor':'codex:/root/w05_merge_review','status':'STOPPED','decision':review['decision'],'review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'scope_ref':f['scope_ref'],'expected_before':f['before'],'expected_after':f['after'],'actual_target_execution':False,'actual_registration_executed':False,'new_failure_origins':[],'manifest_path':str(O/'manifest.json'),'manifest_self_excluded':True})
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
write('manifest.json',{'schema':'researchos.independent-review-manifest.v1','actor':'codex:/root/w05_merge_review','entries':members,'count':len(members),'self_excluded':True})
print(json.dumps({'review_ref':ref(O/'review.json'),'manifest_ref':ref(O/'manifest.json'),'handoff_ref':ref(O/'handoff.json'),'status':'STOPPED'},ensure_ascii=False))

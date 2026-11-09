from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r327-efa7776ec48e4a7abaa92ce85eb0dace'
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);raw=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(path(p).read_bytes())
def write(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
a=read(O/'audit.corrected.json');p=read(N/'prepared_refs.json');b=read(N/'binding.json');assert a['failed_checks']==[]
for original,copied,live in zip(p['original_refs'],a['facts']['copied_canonical_before_refs'],p['canonical_before']):
 assert path(original['path']).read_bytes()==path(copied['path']).read_bytes()==path(live['path']).read_bytes()
 assert path(copied['path']).parent==O
supp=ref(N/'root-prepare.tool-observations.json');observations=read(supp['path'])
write('audit.execution.json',{'actor':'codex:/root/w05_merge_review','initial_audit':{'tool_chunk':'5e395b','actual_outer_exit':0,'actual_Python_native_exit':0,'checks':24556,'static_false_predicates':2,'script_ref':ref(O/'audit.py'),'stdout_ref':ref(O/'audit.stdout.raw'),'stderr_ref':ref(O/'audit.stderr.raw'),'audit_ref':ref(O/'audit.json')},'narrow_predicate_correction':{'tool_chunk':'8c38d8','actual_outer_exit':0,'actual_Python_native_exit':0,'script_ref':ref(O/'audit.corrections.py'),'stdout_ref':ref(O/'audit.corrections.stdout.raw'),'stderr_ref':ref(O/'audit.corrections.stderr.raw'),'audit_ref':ref(O/'audit.corrected.json'),'checks':24565,'failed_checks':0},'exit_basis':'PowerShell immediately retained LASTEXITCODE and explicitly returned it for each own Python auditor. Raw files are redirected auditor output, not product streams.','target_executions':0,'new_failure_origins':[]})
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],'actual_registration_executed':False,'expected_before':[326,154,450],'expected_after':[327,155,459],
 'register_sha256':ref(N/'register.py')['sha256'],'wrapper_sha256':ref(N/'run.py')['sha256'],'prepared_refs_sha256':ref(N/'prepared_refs.json')['sha256'],'audit_sha256':ref(N/'audit.json')['sha256'],'sealer_sha256':ref(N/'seal.py')['sha256'],
 'canonical_before':p['canonical_before'],'copied_canonical_before_refs':a['facts']['copied_canonical_before_refs'],
 'registration_draft_manifest_ref':ref(N/'registration-draft.manifest.json'),'binding_ref':ref(N/'binding.json'),'scope_ref':p['scope_ref'],'bound_scope_review_ref':b['controller_review_ref'],
 'independent_audit_ref':ref(O/'audit.corrected.json'),'original_static_audit_ref':ref(O/'audit.json'),'audit_execution_ref':ref(O/'audit.execution.json'),'actual_prepare_tool_observations_ref':supp,
 'preserved':{'original450_failure_prefix':True,'nine_new_original_payloads_exact':True,'nested_r326_build_native_exit_one_underlying_origin':True,'no_invented_native_exit_for_nullable_fields':True,'late4ddd35_4024a7_236f4101_excluded_from_fixed_cut':True,'parent_observed462_not_canonical_mutation':True,'CP_all_fields_except_revision_timestamp_threeWIP_and_failure_append':True,'OW_all_fields_except_revision_amendmetadata':True,'step_state_commands_bytes':True,'Main_head':'a510dbef4a7e08fb5c428df44c39b133f3ffa856','status_rows':13,'old_deleted_rows':11,'index_empty':True,'formal_increment':0,'source_acceptance':False,'fresh_five_authorization_and_execution_leaves_absent':True},
 'registration_protocol':{'immutable_metadata_module_ref':b['metadata_code_refs'][6],'register_run_seal_and_other_wrappers_unchanged_from_previously_reviewed':True,'before_wrapper_and_each_replace_all_four_CAS':True,'each_replace_follows_complete_ref_and_Git_guard_then_immediate_all_four':True,'post_long_source_guard_all_four_recheck':True,'intent_two_changes_two_unchanged':True,'recovery':'FORWARD_ONLY_REQUIRES_SEPARATE_ROOT_DECISION','raw_request_scope_ref_ROOT_relative':True,'review_identity_schema_codehash_and_same_parent_copies_required':True,'registration_does_not_itself_run_cases':True,'separate_successful_seal_and_unique_grant_required_before_two_cases':True},
 'evidence':a['facts'],'limits':{'catalogue_entries_compared_against_prior_pinned_catalogues_not_rehashed_backing_tree':True,'actual_prepare_Git_native_exits':[0,0,0],'all_three_ownedJobs_primary_idle_handles_errors_checked':True,'prepare_metadata_native_exits':[0,0],'observed_Python_runtime_point_in_time_only':True,'Python_lifecycle_proof':False,'future_current43_graph_complete':None,'OS_loader_complete':None,'time_fit_proved':False,'outer_tool_observations_are_supplement_not_original_complete_native_raw':True,'product_cases_by_reviewer':0,'Go_SQL_HTTP_SDK_Model_by_reviewer':0},
 'static_predicate_corrections':a['static_predicate_corrections'],'verification':{'checks':24565,'failed_checks':0,'actual_auditor_exits':[0,0],'full_prior_scope_and_v7_chain_reuse_explicit':True,'new_failure_origins':[]},'new_failure_origins':[],'status':'STOPPED'}
write('review.json',review)
write('handoff.json',{'schema':'researchos.independent-registration-review-handoff.v1','actor':'codex:/root/w05_merge_review','status':'STOPPED','decision':review['decision'],'review_ref':ref(O/'review.json'),'independent_audit_ref':ref(O/'audit.corrected.json'),'expected_before':review['expected_before'],'expected_after':review['expected_after'],'new_failure_origins':[],'actual_registration_executed':False,'target_executions':0,'manifest_path':str(O/'manifest.json')})
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
write('manifest.json',{'schema':'researchos.independent-review-manifest.v1','actor':'codex:/root/w05_merge_review','entries':members,'count':len(members),'self_excluded':True})
print(json.dumps({'review_ref':ref(O/'review.json'),'manifest_ref':ref(O/'manifest.json'),'handoff_ref':ref(O/'handoff.json'),'status':'STOPPED'},ensure_ascii=False))

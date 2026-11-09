from pathlib import Path
import json,hashlib
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-'+O.name)
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
s=read(N/'scope_registration.json');a=read(O/'audit.json');u=read(O/'supplement.json');f=read(O/'final-checks.json');fix=read(O/'final-predicate-correction.json');b=read(N/'binding.pre-review.json')
assert not a['failed_checks'] and not u['failed'] and fix['passed'] and fix['other_final_checks_passed']
assert Path(s['controller_review_path'])==O/'review.json'
can=read(Path(b['canonical_before_ref']['path']))['entries']
for row in can:assert (R/row['canonical_path']).read_bytes()==Path(row['ref']['path']).read_bytes()
for k in ('output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root'):assert not Path(s[k]).exists()
review={'schema':'researchos.desktop58-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','non_author':True,'decision':'READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE','requested_changes':[],
 'scope_sha256':ref(N/'scope_registration.json')['sha256'],'controller_sha256':s['controller_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_verifier_ref']['sha256'],
 'scope_ref':ref(N/'scope_registration.json'),'binding_pre_review_ref':ref(N/'binding.pre-review.json'),'root_inputs_ref':ref(N/'root-inputs.desktop58.pre-review.json'),'resource_catalog_ref':s['resource_catalog_ref'],'runtime_resources_ref':s['runtime_resources_ref'],'compiler_resources_ref':s['compiler_resources_ref'],'source_catalog_ref':s['source_catalog_ref'],
 'source_commit':s['source_commit'],'source_parent':s['source_parent'],'expected_before':[334,162,532],'expected_after':[335,163,575],'fixed_origin_count':43,'fixed_origins_original_payload_and_nulls_preserved':True,'original_failure_prefix430_preserved':True,'all_current532_failures_preserved_in_frozen_canonical_copy':True,
 'actual_canonical_equal_frozen_copies':True,'canonical_before':can,'fresh_execution_leaves_absent':True,'actual_registration_executed':False,'actual_execution_executed':False,'actual_integration_executed':False,'actual_candidate_import_or_execution':False,'actual_product_calls':0,'actual_native_git_invocations':0,'source_acceptance':False,'formal_increment':0,'execution_authorized_by_this_review':False,'grant_issued_by_this_review':False,
 'checks':{'main_audit':len(a['checks']),'abi_supplement':len(u['checks']),'final_guard_checks':len(f['checks']),'one_static_predicate_corrected':True,'new_tool_failure_count':0},
 'audit_ref':ref(O/'audit.json'),'supplement_ref':ref(O/'supplement.json'),'final_guards_ref':ref(O/'final-checks.json'),'predicate_correction_ref':ref(O/'final-predicate-correction.json'),
 'actual_resource_readonly_verification':{'resource_files_hashed':23867,'source_files_hashed':639,'Go_source_files':559,'runtime_members':1296,'compiler_members':22138,'static_images':16,'actual_public_directory_membership_checked':a['membership_results'],'not_runtime_loading_or_fresh_compilation':True},
 'projection':{'whole_scope_independently_reconstructed_equal':True,'metadata_basis_refs':8,'metadata_code_refs':8,'Root_relative_serialized_refs_match_canonical_absolute_runtime_projection':True,'three_ordered_runtime_observation_paths':s['expected_runtime_observation_paths'],'newscope_not_reused_from_dc00':True},
 'CLI2_prerequisite':{'qualification_ref':s['current58_CLI2_qualification_ref'],'review_ref':s['current58_CLI2_review_ref'],'manifest_ref':s['current58_CLI2_manifest_ref'],'Q_entries':19,'executor_files':125,'launcher_files':7,'Root_aggregate_members':169,'exact_aggregate_READS_reconstructed':True,'case_facts':u['cases'],'native_test_exit_codes':[0,0],'expected_CLI_exit_codes':[0,3],'raw_refs_taken_from_exact_sealed_executor_members':True,'original_qualification_not_modified':True,'CLI2_does_not_qualify_Desktop169_or_Go3':True},
 'finite_limits':{k:s[k] for k in ['node_cases','Go_top_cases','native_top_command_cap','loopback_HTTP_max','offscreen_Electron_controls','installed_visible_GUI_calls','SDK_model_external_paid_calls','process_cap','active_job_processes','image_cap','cleanup_seconds','inner_seconds','outer_seconds','builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds']},
 'negative_alias_count':20,'negative_alias_exact_paths_and_creates_verified':True,'instrumentation_reverse_restores_original_test_bytes':True,
 'Main_readonly_boundary':{'direct_HEAD_observed':s['source_commit'],'frozen_git':s['main_git'],'frozen_status_and_final_index_raw_refs_verified':True,'not_new_Git_status_or_index_native_observation':True,'no_main_or_canonical_writes':True},
 'source_reviews_reused':[
 ref(R/'execution/v2.4/receipts/W13/W13-03/desktop58_cli2_fact_abi_independent_source_review_codex/9167c63720c740baaeef3d030da84d50/review.json'),
 ref(R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocation_independent_review_codex/7c8e667263a24c9d9b50c5c3e73ab559/review.json'),
 ref(R/'execution/v2.4/receipts/W13/W13-03/desktop58_literal_inputs_independent_review_codex/60ec528fa71442f7b4b5ed53b7c0deab/review.json')],
 'reused_source_review_boundary':'Source inverse/AST review reused transparently for unchanged controller/launcher and v4 Gate; actual new scope/data/projection/pins/resources/CLI raw joins reviewed here. No prior failed scope READY or old Desktop runtime qualification inherited.',
 'actual_Root_stage_observation_ref':ref(N/'tool-observations.third-scope.closed.original.json'),'actual_Root_stage_facts':u['tool_completion_facts'],
 'remaining_conditions':['Actual Root registration CAS and seal must succeed for exact scope/tuple, followed by unique exclusive grant and separately checked actual caller.','Future Go3 fresh graph/WORK/archives/executables, Node169 assertions, actual HTTP lifecycle and runtime image observations must close; static resources do not prove future dynamic completeness or time fit.','Any unexpected unknown resource, FAIL/SKIP, early transport close, budget overrun or closure drift must preserve first cause and withhold qualification.','Caller Python/OS lifecycle remains unqualified; point-in-time metadata observations do not prove lifecycle.','No source acceptance, whole58 suite qualification, parent acceptance, installed GUI/NVDA/SDK or 42 formal gates awarded.'],
 'new_failure_count':0,'new_failure_origins':[],'outside_fixed_cut_origins_not_rewritten':True,'status':'STOPPED'}
save('review.json',review)
save('handoff.json',{'schema':'researchos.desktop58-bound-scope-review-handoff.v1','review_ref':ref(O/'review.json'),'scope_ref':review['scope_ref'],'decision':review['decision'],'controller_sha256':review['controller_sha256'],'launcher_sha256':review['launcher_sha256'],'gate_sha256':review['gate_sha256'],'new_failure_count':0,'actual_execution':False,'requires_Root_CAS_seal_unique_grant':True,'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json'];save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False))

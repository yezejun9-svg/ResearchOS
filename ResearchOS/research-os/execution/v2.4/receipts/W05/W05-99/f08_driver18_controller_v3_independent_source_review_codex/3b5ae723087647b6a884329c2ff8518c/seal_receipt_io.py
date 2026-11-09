from pathlib import Path
import hashlib,json

OWN=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_controller_v3_independent_source_review_codex/3b5ae723087647b6a884329c2ff8518c')
PACK=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_revision_preparation_codex/fb328e152ae54da6b4be24cbc3b94ece')
def ref(p):
    p=Path(p);b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,data):
    p=OWN/name
    if not p.resolve().is_relative_to(OWN.resolve()) or p.exists():raise RuntimeError('OWN_NEW_RECEIPT_ONLY')
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    return ref(p)
inputs=json.loads((OWN/'inputs.before.json').read_bytes())
after=json.loads((OWN/'inputs.after.json').read_bytes())
if inputs!=after:raise RuntimeError('INPUT_METADATA_DRIFT')
for row in inputs:
    for key in ['source','copy']:
        actual=ref(row[key]['path'])
        if actual['sha256']!=row[key]['sha256'] or actual['bytes']!=row[key]['bytes']:raise RuntimeError('ACTUAL_INPUT_DRIFT')
review=json.loads((OWN/'source-review.json').read_bytes())
author=json.loads((PACK/'handoff.json').read_bytes())
originrefs=[ref(OWN/name) for name in ['origin.I18-regex-shape.json','origin.I17-diagnostic-literal.json']]
origins=write('origins.json',{
 'schema':'researchos.driver18.v3.independent-origins.v1','new_origin_count':2,'origins':originrefs,
 'observations':[{'chunk':'e4a785','outer_exit':1,'Python_native_exit':1,'source':originrefs[0]},{'chunk':'1b2841','outer_exit':1,'Python_native_exit':1,'source':originrefs[1]}],
 'actual_bridge':'PowerShell exit $LASTEXITCODE directly after each Python command',
 'original_failed_inputs_each_executed_once':True,'failed_input_reexecuted':False,
 'original_scripts_traces_and_numeric_exits_preserved':True,
 'automated_full_checkers_passed':False,'target_or_helper_launched':False,
 'Root_fixed_cut_canonical_or_failure_counter_writes':False,
 'old_I17_review_or_author_or_Root_origins_recounted':False
})
handoff=write('handoff.json',{
 'schema':'researchos.driver18.controller-v3.independent-review.handoff.v1',
 'actor':'/root/f08_whole_scope_review','independent_non_author':True,
 'reviewed_author':'codex:/root/command_queue_impl','writer_status':'STOPPED',
 'verdict':'READY_SOURCE_PREPARATION_ONLY','source_adoption_allowed':False,
 'author_handoff_ref':ref(PACK/'handoff.json'),'author_manifest_ref':ref(PACK/'manifest.json'),
 'reviewed_controller_ref':author['controller_ref'],'scope_ref':author['scope_ref'],'launcher_ref':author['launcher_ref'],
 'original_v2_REQUEST_ref':author['request_ref'],
 'source_review_ref':ref(OWN/'source-review.json'),'readable_review_ref':ref(OWN/'REVIEW.md'),
 'remaining_readonly_facts_ref':ref(OWN/'remaining-facts.json'),
 'inputs_before_ref':ref(OWN/'inputs.before.json'),'inputs_after_ref':ref(OWN/'inputs.after.json'),
 'source_members':14,'source_members_plus_manifest':15,'selected_public_source_refs_actual_rehashed':len(inputs),
 'prior_v2_review30_ref_reuse_verified':True,'input_drift':0,
 'D18_C01':'STATICALLY_ADDRESSED_NOT_RUN',
 'D18_I01':'STATICALLY_ADDRESSED_NOT_RUN',
 'D18_I01_TAIL':'STATICALLY_ADDRESSED_NOT_RUN_POST_FINAL_IO_FAIL_RETURN',
 'byte_replacements':1,'physical_diff_hunks':1,'whole_forward_inverse_byte_exact':True,
 'remove_unique_tail_whole_v2_AST_equal':True,'other11_definitions_AST_equal':True,
 'entry_sys_exit_outside_catch':True,'caps_requested_remaining_effective_helper_timeout_unchanged':True,
 'last_IO_post_guard_all_main_completion_paths':True,'last_IO_tail_lines':[258,259,260],
 'tail_actual_native_exit':None,'tail_error':'INNER_DEADLINE_EXPIRED','tail_first_cause_preserved':True,
 'already_written_outputs_not_rewritten':True,
 'actual_controller_exit_and_raw_stderr_required_for_qualification':True,
 'I16_two_branch_AST_and_I18_original_body_unchanged':True,'I17_OPEN_NOT_AUTHORIZED':True,
 'Root_authority_resource_prepared_mode_and_output14_fields_NULL':True,
 'caps':review['caps'],'partial17_native_roster_expected':30,
 'actual_Root_registration_or_execution_grant':False,'actual_runtime_qualification':False,
 'current_canonical_tuple_used_as_drift_reference':False,
 'actual_target_controller_helper_Go_SQL_driver_SDK_HTTP_model_calls':0,'all_target_tests':'NOT_RUN',
 'Python_AST_source_parse_only_no_candidate_import':True,
 'automated_full_checkers_passed':False,
 'failed_metadata_checks':[{'chunk':'e4a785','outer':1,'Python':1,'stage':'I18 reviewer regex did not permit original two comments'},{'chunk':'1b2841','outer':1,'Python':1,'stage':'I17 reviewer unverified diagnostic/global field assumption'}],
 'failed_input_reexecuted':False,'failed_program_results_rewritten_to_zero':False,
 'actual_remaining_metadata_IO_AST_query':{'chunk':'7e9056','outer':0,'Python':0},
 'origins_ref':origins,'new_failure_origins':originrefs,'new_failure_count':2,
 'source_acceptance':False,'formal_increment':0,'driver_installed':False,'SQL24_adoption_allowed':False,
 'remaining_OPEN':review['remaining_OPEN'],
 'Main_canonical_cache_module_old_package_old_review_cleanup_failure_counter_writes':0,
 'commands_original_ref':ref(OWN/'commands.original.json'),
 'metadata_seal_command':'python -X utf8 exact OWN/seal_receipt_io.py; PowerShell exit $LASTEXITCODE',
 'seal_actual_numeric_exit':None,'seal_actual_native_exit':None,
 'seal_exit_authority':'Original enclosing tool result only; NULL here is not a claimed execution success.',
 'manifest':{'path':str(OWN/'manifest.json'),'excluded_only_self':True},
 'finish':'STOPPED after enclosing seal IO tool return; parent owns future Root grant/adoption/execution'
})
members=[ref(p) for p in sorted(OWN.rglob('*')) if p.is_file() and p!=OWN/'manifest.json']
manifest=write('manifest.json',{'schema':'researchos.independent-source-review.manifest.v1','root':str(OWN),'files':members,'count':len(members),'excluded_only_self':True})
for row in members:
    actual=ref(row['path'])
    if actual!=row:raise RuntimeError('SEALED_MEMBER_DRIFT')
print(json.dumps({'writer_status':'STOPPED','verdict':'READY_SOURCE_PREPARATION_ONLY','handoff':handoff,'manifest':manifest,'review':ref(OWN/'source-review.json'),'readable_review':ref(OWN/'REVIEW.md'),'origins':origins,'individual_new_origins':originrefs,'members':len(members),'members_plus_manifest':len(members)+1,'candidate_or_helper_targets':0},ensure_ascii=False))


from pathlib import Path
import json,hashlib
out=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_sqlite_innocuous_driver_independent_source_review_codex/734ee12d8b8d404798c2ec6e6e1f56bc')
author=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_sqlite_innocuous_driver_preparation_codex/da3c883ec6684c4487dbe36ff45affe4')
def meta(p):
    b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def same(ref):
    a=meta(Path(ref['path']))
    assert (a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes'])
    return a
def put(name,obj):
    (out/name).write_text(json.dumps(obj,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
before=json.loads((out/'input-verification.json').read_text(encoding='utf-8'))
h=json.loads((out/'inputs/handoff.json').read_text(encoding='utf-8'))
assert h['status']=='PREPARATION_ONLY_STOPPED' and not h['source_acceptance'] and not h['actual_execution_authorized']
same(before['manifest']);same(before['handoff'])
actual=[]
for ref in before['member_refs']:
    a=same(ref);actual.append(a)
    c=meta(out/'inputs'/Path(ref['path']).relative_to(author))
    assert (c['sha256'],c['bytes'])==(ref['sha256'],ref['bytes'])
assert len(actual)==31 and (out/'inputs/manifest.json').read_bytes()==(author/'manifest.json').read_bytes()
assert (out/'inputs/modernc-sqlite-innocuous.patch').read_bytes()==(out/'inputs/inputs/15-modernc-sqlite-innocuous.patch').read_bytes()
assert before['whole_inverse_byte_equal'] and before['exact_sealed_two_hunk_application']
selected_unchanged=[]
for name in ['04-conn.go','05-driver.go','07-func_test.go','08-LICENSE','09-LICENSE-SQLITE','10-LICENSE-SQLITE_VEC','11-LICENSE-3RD-PARTY.md','12-sqlite.go','13-sqlite_windows.go','14-sqlite_g_0000000000060000.go']:
    selected_unchanged.append(meta(out/'inputs/inputs'/name))
put('input-verification.after.json',{
 'schema':'researchos.independent-driver-review-final-rehash.v1','author_listed_members':31,'author_physical_with_manifest':32,
 'author_manifest':same(before['manifest']),'author_handoff':same(before['handoff']),'author_member_refs':actual,'drift':[],
 'own_copies_all_match':True,'Main_cache_or_module_originals_read':False,'author_inputs_metadata_not_fresh_Main_attestation':True,
 'source_adoption_writes':0
})
oracle={'schema':'researchos.sqlite-innocuous-review-oracle.v1','status':'STATIC_DERIVATION_NOT_RUN','source':'Exact frozen engine _pragmaFunclistLine mask/encoding/output expressions at103566/103589; no SQL executed',
 'columns_separate':['enc','flags'],
 'cases':[{'Deterministic':False,'Innocuous':False,'eTextRep':1,'enc':'utf8','pragma_flags':0},{'Deterministic':True,'Innocuous':False,'eTextRep':2049,'enc':'utf8','pragma_flags':2048},{'Deterministic':False,'Innocuous':True,'eTextRep':2097153,'enc':'utf8','pragma_flags':2097152},{'Deterministic':True,'Innocuous':True,'eTextRep':2099201,'enc':'utf8','pragma_flags':2099200}],
 'public_flags_do_not_include_UTF8':True,'raw_internal_flags_not_mocked':True,
 'required_extra_predicates':['builtin=0','exact name','actual scalar/aggregate/window type','exact narg','no unknown flags','trusted_schema=OFF readback','register before new connections'],
 'author_future_plan_change_applied':False}
put('oracle-review.json',oracle)
put('source-review.json',{
 'schema':'researchos.sqlite-innocuous-independent-source-review.v1','actor':'codex:/root/f08_whole_scope_review','is_author':False,'verdict':'REQUEST_CHANGES',
 'input_handoff':before['handoff'],'input_manifest':before['manifest'],'input_candidate':h['candidate_ref'],'input_patch':h['patch_ref'],
 'candidate_source_assessment':'ELIGIBLE_AS_ROOT_CONTROLLED_FORK_PREPARATION_INPUT_ONLY','code_findings_confirmed':[],
 'test_plan_findings':[{'id':'V01','severity':'Important','path':'future-tests.proposed.json','line':98,'cases':['I10','I11'],'problem':'PRAGMA function_list enc is separate; flags must not include SQLITE_UTF8','fix':'Separate expected raw eTextRep and public enc/flags oracle; keep all18 NOT_RUN'}],
 'whole_candidate_lines':1383,'whole_source_inverse_byte_equal':True,'independent_exact_two_hunk_application':True,
 'historical_847_byte_patch_identical':True,'only_source_changes':['FunctionImpl.Innocuous bool default false','registerFunction conditional OR SQLITE_INNOCUOUS independent of Deterministic'],
 'default_registration_flags_unchanged':True,'convenience_wrappers_keyed_and_default_false':True,'shared_scalar_aggregate_window_eTextRep':True,
 'source_evidence_segments_verified':12,'source_evidence_ref':meta(out/'source-evidence-independent-check.json'),
 'selected_conn_driver_tests_engines_license_copies':selected_unchanged,'complete_future_fork_exactly_one_file_delta_verified':False,
 'struct_source_compatibility':'Added exported field breaks unkeyed consumer literals; full consumers not compiled; no stable ABI/layout promise',
 'upstream_module_snapshot_pin':'modernc.org/sqlite v1.60.1','module_zip_dirhash_source_authentication':'OPEN_NOT_RUN',
 'root_go_sum_local_replace_authenticated':False,'complete_inventory_fork_and_lock':'OPEN_NOT_IMPLEMENTED',
 'version_qualified_replace':'Proposed only; Root exact resource/source lock lease required',
 'licenses':'Full frozen original BSD-3/SQLite/vec/thirdparty bytes retained; eventual source/binary/build export closure must include notices',
 'driver_F08_validation_cases':18,'driver_F08_validations':'ALL_NOT_RUN','Go_AST_compile_or_syntax_verified':False,
 'callback_transitive_purity_current_registration_and_semantics':'OPEN','old_partial_callback_input_not_promoted':True,
 'physical_SQLite_driver_qualification':'OPEN_NOT_RUN','SQL24_installable':False,
 'source_acceptance':False,'sql24_adoption_allowed':False,'three_callbacks_complete':False,'formal_increment':0,
 'Go_gofmt_SQL_Node_SDK_model_HTTP_install_product_calls':0,'Main_modulecache_module_canonical_author_or_old_receipt_writes':0,
 'review_ref':meta(out/'REVIEW.md'),'oracle_review_ref':meta(out/'oracle-review.json')
})
obs=json.loads((out/'command-results.json').read_text(encoding='utf-8'))
assert obs['observed_outer_nonzero_count']==0
put('failure-origins.json',{
 'schema':'researchos.independent-driver-review-origin-preservation.v1',
 'reviewer_new_failure_origins':[],'reviewer_new_observed_outer_nonzero_count':0,
 'author_new_failure_origins':h['new_failure_origins'],
 'author_diagnostics_ref':meta(out/'inputs/diagnostics.json'),'author_diagnostics_native_without_bridge_remain_NULL':True,
 'review_native_without_explicit_bridge_remain_NULL':True,
 'output_truncation_not_process_failure':{'chunk':'c7ae8f','outer_exit':0,'native_exit':None,'replacement_reader':'bounded exact frozen line segments; no failed input retry'},
 'historical_receipts_or_failure_counters_written':False,'historical_origins_recounted':False,'counters_reset':False,
 'command_results_ref':meta(out/'command-results.json'),
 'seal_invocation_result':'Reported by subsequent actual tool result; not pre-certified here'
})
put('handoff.json',{
 'schema':'researchos.sqlite-innocuous-independent-source-review-handoff.v1','actor':'codex:/root/f08_whole_scope_review','status':'REQUEST_CHANGES','writer':'STOPPED','is_author':False,
 'input_handoff':same(before['handoff']),'input_manifest':same(before['manifest']),'actual_candidate_ref':h['candidate_ref'],'actual_patch_ref':h['patch_ref'],
 'review_ref':meta(out/'REVIEW.md'),'source_review_ref':meta(out/'source-review.json'),
 'oracle_review_ref':meta(out/'oracle-review.json'),'input_before_ref':meta(out/'input-verification.json'),'input_after_ref':meta(out/'input-verification.after.json'),
 'source_evidence_ref':meta(out/'source-evidence-independent-check.json'),'command_results_ref':meta(out/'command-results.json'),'origins_ref':meta(out/'failure-origins.json'),
 'source_next_step':'Exact candidate may be input to Root-controlled complete fork preparation; no implementation/adoption authority granted',
 'required_narrow_correction':'V01 separate function_list enc and flags expected values in test proposal, keep18 NOT_RUN',
 'open':['module zip/dirhash and complete upstream source origin','complete upstream/fork inventory and exact one-file delta lock','full dependency/export/license closure','full consumer Go AST/compile and driver tests','all18 actual driver/F08 validations','current three callback complete transitive purity and semantics','old22/23 binaries and physical SQL24 upgrade/rollback qualification'],
 'source_acceptance':False,'sql24_adoption_allowed':False,'SQL24_installable':False,'three_callbacks_complete':False,'formal_increment':0,
 'new_author_failure_origins':0,'new_review_failure_origins':0,'prior_origin_recount':False,'failure_counter_written':False,
 'Go_gofmt_SQL_Node_SDK_model_HTTP_install_product_calls':0,'Main_cache_module_canonical_author_package_old_review_writes':0,
 'manifest':'manifest.json self excluded; includes handoff; actual final SHA/size provided separately'
})
files=[meta(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json']
put('manifest.json',{'schema':'researchos.receipt-manifest.v1','files':files,'self_excluded':True})
for ref in files:same(ref)
assert len(list(p for p in out.rglob('*') if p.is_file()))==len(files)+1
print(json.dumps({'status':'STOPPED','verdict':'REQUEST_CHANGES','source_next_step':'ELIGIBLE_ROOT_CONTROLLED_FORK_PREPARATION_INPUT_ONLY','listed_members':len(files),'physical_with_manifest':len(files)+1,'all_listed_sha_bytes_rechecked':True,'review':meta(out/'REVIEW.md'),'source_review':meta(out/'source-review.json'),'origins':meta(out/'failure-origins.json'),'handoff':meta(out/'handoff.json'),'manifest':meta(out/'manifest.json')},ensure_ascii=True))


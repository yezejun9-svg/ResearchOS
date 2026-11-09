from pathlib import Path
import hashlib, json

OWN = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_i17_binding_revision_independent_source_review_codex/f55ac9fdfb3d4a929686b6884431f962')
PACK = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_i17_binding_revision_preparation_codex/b918c16361bb4744bc7fffb6434d6849')
def ref(p):
    p=Path(p); b=p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
    p=OWN/name
    assert p.resolve().is_relative_to(OWN.resolve())
    assert not p.exists(), ('new receipt member already exists',name)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    return ref(p)
def exact(row):
    assert ref(row['path'])==row, ('drift',row['path'])
    return row

before=json.loads((OWN/'inputs.before.json').read_text('utf8'))
assert len(before)==432
after=[]
for record in before:
    exact(record['source']); exact(record['copy'])
    after.append({'source':ref(record['source']['path']),'copy':ref(record['copy']['path']),'relative':record['relative']})
assert before==after
write('inputs.after.json',after)
prior=json.loads((OWN/'prior-ref-reuse-audit.json').read_text('utf8'))
for row in prior['actual_external_46_rehashed']:exact(row)
assert len(prior['actual_mapping_source_35_rehashed'])==35
write('prior-refs.after.json',{'actual_external_46':prior['actual_external_46_rehashed'],'prior_35_source_refs_exact':True,'actual_input_drift':0,'historical_origins_recounted':False})

sequences=json.loads((PACK/'raw-sequences.json').read_text('utf8'))['sequences']
seq=next(s for s in sequences if s['id']=='ack_true_text')
commit=next(f for f in seq['frames'] if f['action']=='commit.insert')
journal=next(f for f in seq['frames'] if f['action']=='journal.update')
for f in [commit,journal]:exact(f['go_producer_raw'])
plan= {
 'schema':'researchos.f08.i17.minimum-source-fact-plan.v1',
 'status':'NEXT_AUTHOR_REVISION_ONLY_NOT_RUN',
 'current_source_mutation_by_review':False,
 'original_100_dispatch_controls_retained':True,
 'minimum_new_pairs':5,
 'baseline_resource':'existing actual frozen pretransition raw bytes, not completedFixture/SUT evaluation',
 'cases':[
  {'id':'proof-commit-missing-admitted-pin','baseline':commit['go_producer_raw'],'mode':5,'action':'commit.insert','single_fact':'delete exactly one sources tuple with category=pins and phase column4=ADMITTED; all other source tuples, row and OLD byte-equivalent','source_fail_branch':'completeMaterializations lines783..788 reached by completedJournal/finalGroup; remaining tuples keep valid type/mask/key shape','expected_fixed_error':'F08_ORIGINAL_BINDING'},
  {'id':'proof-commit-missing-final-member','baseline':commit['go_producer_raw'],'mode':5,'action':'commit.insert','single_fact':'delete exactly one sources tuple category=final_members for the current final locator; all other fields unchanged','source_fail_branch':'completedJournal line1521 -> completeMaterializations line785','expected_fixed_error':'F08_ORIGINAL_BINDING'},
  {'id':'proof-commit-control-not-confirmed','baseline':commit['go_producer_raw'],'mode':5,'action':'commit.insert','single_fact':'change controls source tuple column8 CONFIRMED to RECONCILING; keep original/final bytes and all other fields','source_fail_branch':'completedJournal line1522 genuine CONFIRMED check','expected_fixed_error':'F08_ORIGINAL_BINDING'},
  {'id':'proof-journal-retained-original-header-field','baseline':journal['go_producer_raw'],'mode':5,'action':'journal.update','single_fact':'change only expected_revision inside the retained header original envelope to another legal positive revision; independently encode legal original envelope/base64/private header and place its hex in current row column7; retain row request_hash, OLD and source original header','source_fail_branch':'journalEnvelope line1435 original decoded ContentHash mismatch; no invalid JSON/shape/action shortcut','expected_fixed_error':'F08_ORIGINAL_BINDING'},
  {'id':'proof-journal-retained-timestamp','baseline':journal['go_producer_raw'],'mode':5,'action':'journal.update','single_fact':'change only current idempotency row column8 to another valid original timestamp, retain OLD and matching source ACK row timestamp','source_fail_branch':'journal line1499 f08RetainedColumns(old,row,6)','expected_fixed_error':'F08_ORIGINAL_BINDING'}
 ],
 'shape_checks':['unchanged INTEGER mode','unchanged accepted action','same closed frame keys','BLOB frame raw','source category/mask arities and unique key validation remain valid','all unmutated row/OLD/source facts equal actual baseline'],
 'future_assertions':['genuine baseline direct int64(1)','corrupt direct nil plus exact fixed error','SQL corrupt actual sqlite.Error primary1 and fixed error','generic CHECK corrupt INSERT has no count change'],
 'constructor_constraint':'independent raw source construction, no f08BuildCallbacks/evaluate or authority predicate result used to construct data',
 'expected_result_authority':'SOURCE_INFERENCE_NOT_RUN; future Go producer/native SQL run under genuine Root lease',
 'unchanged_positive_sequences':[{'id':s['id'],'count':len(s['frames'])} for s in sequences],
 'native_full_DDL_still_FATAL_OPEN':True,
 'auth_history_SQL24_formal_complete':False
}
planref=write('minimum-source-fact-plan.json',plan)

originref=ref(OWN/'origin.metadata-js-parser.json')
origin=json.loads((OWN/'origin.metadata-js-parser.json').read_text('utf8'))
assert origin['outer_exit'] is None and origin['native_exit'] is None
originsref=write('origins.json',{
 'schema':'researchos.source-review.origins.v1','new_origin_count':1,'origins':[originref],
 'new_JS_parse_failure_outer_numeric':None,'new_JS_parse_failure_native_numeric':None,
 'visible_diagnostic_preserved':True,'full_original_backend_input_available':False,
 'failed_input_reexecuted':False,'metadata_shell_nonzero_count_observed':0,
 'author_parser_origin_reference_only':ref(PACK/'original-parser-failure.json'),
 'author_parser_or_old_mapping_fd09_origins_recounted':False,
 'Root_fixed_cut_or_counters_written':False
})
summary=json.loads((OWN/'source-review.json').read_text('utf8'))
assert summary['verdict']=='REQUEST_CHANGES'
assert summary['whole_packet']['manifest_plus_members_rehashed']==432
assert summary['raw_checks']['all_100_proof_bad_only_action_mutation']
hdf=write('handoff.json',{
 'schema':'researchos.source-review.handoff.v1',
 'actor':'/root/f08_whole_scope_review','writer_status':'STOPPED',
 'verdict':'REQUEST_CHANGES','status':'SEALED_INDEPENDENT_SOURCE_PREPARATION_REVIEW',
 'independent_non_author':True,'review_namespace':OWN.as_posix(),
 'source_author_handoff':exact({'path':(PACK/'handoff.json').as_posix(),'sha256':'66e6d86beb597b245339df1f6133126bcfbf0e65fe9ce9008801f12f32ee22df','bytes':7064}),
 'source_author_manifest':exact({'path':(PACK/'manifest.json').as_posix(),'sha256':'07e4fe92947f004393a376b387b344725622ff5949d53f2ca7ad059fb5d537a4','bytes':146636}),
 'source_review_ref':ref(OWN/'source-review.json'),'readable_review_ref':ref(OWN/'REVIEW.md'),
 'minimum_source_fact_plan_ref':planref,
 'raw_vector_audit_ref':ref(OWN/'raw-vector-audit.json'),
 'diff_and_body_audit_ref':ref(OWN/'diff-and-body-audit.json'),
 'prior_ref_reuse_audit_ref':ref(OWN/'prior-ref-reuse-audit.json'),
 'inputs_before_ref':ref(OWN/'inputs.before.json'),'inputs_after_ref':ref(OWN/'inputs.after.json'),
 'prior_refs_after_ref':ref(OWN/'prior-refs.after.json'),
 'source_members_rehashed':431,'source_members_bytes':27969736,'source_refs_plus_manifest_rehashed':432,
 'source_snapshots_actual_equal':432,'prior_mapping_source_refs_actual_reused_rehashed':35,
 'all_author_original_refs_actual_rehashed':46,'source_drift':0,
 'raw_vectors_rehashed':109,'proof_raw_bad_dispatch_only':100,'pretransition_frames_actual_rehashed':100,'sequence_frames':[24,24,26,26],
 'old_Test_raw_byte_bodies_changed':28,'old_Test_only_normalized_equal':28,'other_driver_Test_raw_bodies_equal':17,
 'whole_forward_inverse_bytes_exact':True,'production_v3_driver_DDL_original_bytes_unchanged':True,
 'Critical_count':0,'Important_count':2,'important_ids':['I17-R01','I17-R02'],
 'Go_producer_byte_equality_native_SQL_storage_or_DDL':False,
 'actual_metadata_audit_tool_chunk':'901e8e','actual_metadata_audit_outer_exit':0,'actual_metadata_audit_Python_exit':0,
 'all_target_tests_NOT_RUN':True,'Go_GoAST_gofmt_compile_SQL_driver_HTTP_SDK_model_runs':0,
 'full_I17':'FATAL_OPEN','source_adoption_allowed':False,'driver_adopted':False,'SQL24_adoption_allowed':False,
 'three_callbacks_complete':False,'formal_acceptance':False,'formal_increment':0,
 'remaining_FATAL_OPEN':summary['remaining_FATAL_OPEN'],
 'origins_ref':originsref,'new_origins':[originref],'new_failure_count':1,
 'new_failure_outer_numeric_exit':None,'new_failure_native_numeric_exit':None,
 'old_origins_no_retry_no_recount_no_reset':True,
 'commands_original_ref':ref(OWN/'commands.original.json'),'commands_supplement_ref':ref(OWN/'commands.supplement.json'),
 'current_metadata_seal_command':'python -X utf8 exact-owned seal_review.py; exit $LASTEXITCODE',
 'seal_actual_outer_exit':None,'seal_actual_native_exit':None,
 'seal_exit_authority':'Original enclosing exec_command result after final print, external to the sealed self-referential receipt. NULL is not a claimed execution success.',
 'Main_canonical_module_cache_old_receipt_failure_counter_writes':0,
 'Root_next':'New author-only minimal R01/R02 revision, then non-author byte/source review; independent driver partial17 branch can continue.',
 'manifest':{'path':(OWN/'manifest.json').as_posix(),'self_excluded':True},
 'finish':'STOPPED after final enclosing metadata seal tool returns; no additional write by review author'
})
members=[ref(p) for p in sorted(OWN.rglob('*')) if p.is_file() and p!=OWN/'manifest.json']
manifest=write('manifest.json',{'schema':'researchos.source-review.manifest.v1','root':OWN.as_posix(),'self_excluded':True,'file_count':len(members),'total_bytes':sum(r['bytes'] for r in members),'members':members})
for row in members:exact(row)
assert ref(OWN/'manifest.json')==manifest
print(json.dumps({'writer_status':'STOPPED','verdict':'REQUEST_CHANGES','handoff':hdf,'manifest':manifest,'review':ref(OWN/'source-review.json'),'readable_review':ref(OWN/'REVIEW.md'),'origins':originsref,'new_origin':originref,'members':len(members),'members_plus_manifest':len(members)+1,'metadata_only_target_runs':0},ensure_ascii=False))


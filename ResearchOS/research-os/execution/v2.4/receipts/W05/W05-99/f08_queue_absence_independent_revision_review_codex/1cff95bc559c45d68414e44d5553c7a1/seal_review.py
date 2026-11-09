from pathlib import Path
import json, hashlib
out=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_queue_absence_independent_revision_review_codex/1cff95bc559c45d68414e44d5553c7a1')
author=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_queue_absence_revision_preparation_codex/b9a560ed59c24bef9b9e01d2d91c4b84')
previous=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971')
def meta(p):
    b=p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(name,obj):
    p=out/name
    p.write_text(json.dumps(obj,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def same(ref):
    a=meta(Path(ref['path']))
    assert (a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes'])
    return a
before=json.loads((out/'input-verification.json').read_text(encoding='utf-8'))
assert before['listed_members']==25 and before['physical_with_manifest']==26
verified=[same(ref) for ref in before['files']]
for ref in before['external_handoff_refs_verified']:same(ref)
same(before['manifest']);same(before['handoff'])
h=json.loads((out/'inputs/handoff.json').read_text(encoding='utf-8'))
assert h['writer']=='STOPPED' and not h['source_accepted'] and not h['sql24_adoption_allowed']
for ref in verified:
    copied=out/'inputs'/Path(ref['path']).relative_to(author)
    a=meta(copied)
    assert (a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes'])
assert (out/'inputs/manifest.json').read_bytes()==(author/'manifest.json').read_bytes()
assert (out/'base/client_cancel_finalization.go.proposed.txt').read_bytes()==Path(h['base_source_ref']['path']).read_bytes()
old_test=out/'base/client_cancel_finalization_test.v2.go.proposed.txt'
assert meta(old_test)['sha256']=='e6fda432548df4d1894292ac46e36285e2c82c2088dfb7d2cb500f1198f462f4' and meta(old_test)['bytes']==22668
assert (out/'inputs/client_cancel_finalization_test.go.proposed.txt').read_bytes().startswith(old_test.read_bytes())
pm=meta(previous/'manifest.json')
assert (pm['sha256'],pm['bytes'])==('1a397b1e96846376b3d786284259ad3d34049f84795c5167bbc4af233b30b93e',45738)
oldmf=json.loads((previous/'manifest.json').read_text(encoding='utf-8'))
assert isinstance(oldmf['files'],list)
old_index={ref['path'].replace('\\','/'):ref for ref in oldmf['files']}
evidence=[]
for name in ['002-store.go','012-client_command_queue.go','013-client_protocol_queue_control.go','038-0022_client_command_queue.sql','041-closed-contract.md']:
    p=previous/'inputs/snapshots'/name
    ref=old_index[p.as_posix()]
    same(ref)
    dest=out/'producer-evidence'/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(p.read_bytes())
    evidence.append({'frozen_original':ref,'review_copy':meta(dest)})
put('producer-evidence-index.json',{'schema':'researchos.frozen-producer-readonly-evidence.v1','prior_review_manifest':pm,'files':evidence,'Main_or_WT_read':False,'SQL_execution':False})
put('input-verification.after.json',{'schema':'researchos.independent-review-final-rehash.v1','author_listed_members':25,'author_physical_with_manifest':26,'author_manifest':same(before['manifest']),'author_handoff':same(before['handoff']),'drift':[],'author_listed_files':verified,'external_refs':[same(r) for r in before['external_handoff_refs_verified']],'own_copies_all_match':True,'Main_cache_canonical_source_adoption_writes':0})
put('source-review.json',{
 'schema':'researchos.f08-queue-absence-independent-revision-review.v1',
 'actor':'codex:/root/f08_whole_scope_review','verdict':'REQUEST_CHANGES','is_author':False,
 'input_source':h['source_ref'],'input_test_proposal':h['test_proposal_ref'],'input_manifest':before['manifest'],
 'narrow_scope':['C01 NO_SESSION queueAdmission and emptyQueueFinal','C02/I01 initial qualification success changed to explicit gap'],
 'C01_original_Task_A_bypass':'STATIC_REJECTION_PRESENT_NOT_RUN',
 'C01_unrelated_history_exception':'REQUEST_CHANGES_NONEMPTY_LOCATOR_AND_KNOWN_PRODUCER_GRAPH',
 'finding':{'id':'C01-R1','severity':'Important','source_function':'noSessionQueueHistory','lines':[835,846,859,864],'callsite_lines':[881,1267],
  'static_counterexample':'Known B graph, queue.last_receipt_id=NULL and receipt.previous_receipt_id=NULL; NULL/empty receipt_id or duplicate NULL receipt rows are decoded and never checked before return nil. Existing positive fixture also loses the known producer current pointer.',
  'executed':False,'no_Go_SQL_or_model_reimplementation_executed':True,
  'fix_scope':['unconditional nonempty receipt_id validation within relevant known-producer classification','validate same project/generation/command current receipt locator and retained chain to relevant receipt','known producer state relation, unknown successor stays explicit OPEN','component fixture updates and status wording only']},
 'C02_fixed_refusal':'STATIC_CONFIRMED_PROFILE_NOT_IMPLEMENTED',
 'C02_lines':[1151,1167],
 'I02_full_journal_positive':'OPEN_NOT_IMPLEMENTED_NOT_RUN',
 'unknown_SDK_receipts':'EXPLICIT_OPEN',
 'new_test_proposals':{'top':1,'leaf':24,'all_status':'NOT_RUN'},
 'old_test_prefix_bytes_equal':True,'inverse_source_bytes_equal':True,
 'prior_14_library_metadata_and_8_late_firstread_provenance_upgraded':False,
 'remaining_OPEN_unchanged':['R1/R2 prior boundaries','mode3 caller binding','later admission.operation producer not installed','ordinary native SDK final authority and history','full initial qualification profile','driver Innocuous qualification and SQL24','three complete callbacks'],
 'Go_compile_or_syntax_verified':False,'all_product_execution_calls':0,'all_source_adoption_calls':0,'formal_increment':0,
 'reviewer_failure_count_new':0,'canonical_failure_counter_written':False,
 'producer_evidence_ref':meta(out/'producer-evidence-index.json'),
 'delta_ref':meta(out/'independent-delta-check.json'),
 'review_ref':meta(out/'REVIEW.md')
})
put('future-test-requirements.json',{
 'schema':'researchos.f08-queue-absence-review-minimal-regressions.v1','status':'NOT_IMPLEMENTED_NOT_RUN','execution_authorized':False,
 'callsites':['queueAdmission NO_SESSION','emptyQueueFinal original NO_SESSION'],
 'required_negative_controls':['NULL receipt_id with NULL current/previous pointer','empty receipt_id with NULL current/previous pointer','duplicate NULL receipt_id rows','retained CANCEL_FENCE with queue current pointer=NULL','known ENQUEUED to DROPPED terminal receipt inconsistent with current queue state'],
 'required_positive_controls':['truly empty Task A source graph','valid unrelated B CANCEL_FENCE produced graph with nonempty current receipt pointer'],
 'conditional_historical_positive':'Only an exact frozen implemented successor chain permits a noncurrent receipt positive; unknown SDK successor remains explicit OPEN',
 'full_I02_journal_materialization_chain':'OPEN_NOT_IMPLEMENTED_NOT_RUN',
 'full_qualification_profile':'OPEN_NOT_IMPLEMENTED'
})
new_origins=[]
for ref in h['new_failure_origin_refs']:
    orig=json.loads(Path(ref['path']).read_text(encoding='utf-8'))
    new_origins.append({'original_ref':same(ref),'review_copy':meta(out/'inputs'/Path(ref['path']).name),'actual_origin':orig,'recounted_by_review':False})
assert len(new_origins)==4
put('failure-origins.json',{
 'schema':'researchos.independent-review-origin-preservation.v1','reviewer_new_origins':[],'reviewer_new_observed_outer_nonzero_count':0,
 'author_new_metadata_origins_preserved':new_origins,'author_new_metadata_origin_count':4,
 'prior_refs_preserved_no_recount':[same(r) for r in h['prior_failures_preserved_no_recount']],
 'native_exit_without_explicit_bridge_kept_NULL':True,'failed_input_retry':False,
 'canonical_counter_written':False,'counters_reset':False,'product_calls':0,
 'tool_records_ref':meta(out/'command-results.json'),
 'seal_invocation_result':'Reported by its actual subsequent tool result, not pre-certified here.'
})
put('handoff.json',{
 'schema':'researchos.f08-queue-absence-independent-revision-review-handoff.v1',
 'actor':'codex:/root/f08_whole_scope_review','status':'REQUEST_CHANGES','writer':'STOPPED','is_author':False,
 'review_ref':meta(out/'REVIEW.md'),'source_review_ref':meta(out/'source-review.json'),
 'input_author_handoff':same(before['handoff']),'input_author_manifest':same(before['manifest']),
 'actual_reviewed_source_ref':h['source_ref'],'actual_reviewed_test_ref':h['test_proposal_ref'],
 'input_before_ref':meta(out/'input-verification.json'),'input_after_ref':meta(out/'input-verification.after.json'),
 'origins_ref':meta(out/'failure-origins.json'),'command_results_ref':meta(out/'command-results.json'),
 'producer_evidence_ref':meta(out/'producer-evidence-index.json'),'delta_ref':meta(out/'independent-delta-check.json'),
 'future_test_requirements_ref':meta(out/'future-test-requirements.json'),
 'findings':[{'id':'C01-R1','severity':'Important','decision':'Fix unrelated known-producer locator/linked graph before adoption'}],
 'static_outcomes':{'C01_original_Task_A_history_bypass':'REJECTION_PRESENT_NOT_RUN','C01_unrelated_known_producer_exception':'REQUEST_CHANGES','C02_initial_subset_success':'REPLACED_BY_FIXED_OPEN_REFUSAL','I02_full_journal_positive':'OPEN_NOT_IMPLEMENTED_NOT_RUN'},
 'source_accepted':False,'sql24_adoption_allowed':False,'three_callbacks_complete':False,'formal_increment':0,
 'new_author_origin_count_preserved':4,'reviewer_new_origins':0,'prior_origin_recount':False,'canonical_failure_counter_written':False,
 'Go_gofmt_compile_SQL_Node_SDK_model_HTTP_calls':0,
 'Main_WT_cache_canonical_or_author_source_writes':0,
 'prior_14_libraries_and_8_late_firstread_provenance_upgraded':False,
 'next_owner':'Root decides narrowly scoped author correction; reviewer has no implementation or merge authority',
 'manifest':'manifest.json; self excluded; contains handoff; exact final hash supplied separately by actual seal result'
})
files=[meta(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json']
put('manifest.json',{'schema':'researchos.receipt-manifest.v1','files':files,'self_excluded':True})
for ref in files:same(ref)
assert len(list(p for p in out.rglob('*') if p.is_file()))==len(files)+1
print(json.dumps({'status':'STOPPED','verdict':'REQUEST_CHANGES','listed_members':len(files),'physical_with_manifest':len(files)+1,'all_listed_sha_bytes_rechecked':True,'review':meta(out/'REVIEW.md'),'source_review':meta(out/'source-review.json'),'origins':meta(out/'failure-origins.json'),'handoff':meta(out/'handoff.json'),'manifest':meta(out/'manifest.json')},ensure_ascii=True))


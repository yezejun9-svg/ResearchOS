import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/revision-v2-ed1a1dab301a40b293dd6a177980cfaf'
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321-v2'
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
checks=json.loads((O/'checks.json').read_bytes())
if checks['failed']:raise RuntimeError('Static data checks did not pass')
gp=(S/'grant-producer.py').read_text(encoding='utf-8').splitlines()
line=lambda term:next(i for i,s in enumerate(gp,1) if term in s)
finding={'id':'I38-V2-PRELAUNCH-01','priority':'BLOCKER_FOR_DECLARED_FULL_FAILURE_CAPTURE',
 'path':str(S/'grant-producer.py'),
 'lines':{'first_pretry_check':line("check(sys.flags.isolated"),'scope_read':line("scope_ref = ref(REG"),'auth_parent_mkdir':line('auth_parent.mkdir'),'exclusive_auth_mkdir':line('auth.mkdir'),'try_begins':line('try:'),'failure_handler':line('except BaseException as exc:')},
 'fact':'flags, scope read/hash/parse, UUID and safe path checks, auth parent mkdir and exclusive auth leaf mkdir execute before the try/finally. No supplied launcher surrounds these operations or the later controller execution before its own try.',
 'impact':'A preflight exception can leave no new immutable failure.origin/manifest; controller failures in authority/source checks or exclusive out.mkdir are similarly outside its own failure handler. This does not authorise an unsafe FF, but fails the explicitly required complete original invocation/nullable exit preservation.',
 'minimal_change':'Supply a new immutable outer launcher with an independently safe exclusive receipt leaf, own-output creation guard, raw stdout/stderr and argv, nullable native/controller outcome and finally manifest. It must cover grant-producer startup/pretry and the once controller startup/pretry, preserve exceptions without retry, and never write an existing sealed leaf. Bind the exact producer/controller/scope hashes and actual321 sealed grant. No production/controller/source38 change is required.',
 'not_executed':True,'actual_product_failure':False}
review={
 'schema':'researchos.exact38-integration-controller-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'REQUEST_CHANGES','requested_changes':[finding],
 'controller_sha256':ref(P/'integrate_exact38.v2.py')['sha256'],'scope_sha256':ref(S/'scope_registration.json')['sha256'],
 'actual_integration_executed':False,'actual_registration_executed':False,'actual_product_execution':False,
 'expected_current':[320,148,417],'expected_future_registration':[321,149,422],
 'basis':{'controller':ref(P/'integrate_exact38.v2.py'),'scope':ref(S/'scope_registration.json'),'grant_producer':ref(S/'grant-producer.py'),'future_registration_preparer':ref(S/'prepare.py'),'candidate_handoff':ref(P/'handoff.json'),'candidate_manifest':ref(P/'manifest.json'),'checks':ref(O/'checks.json'),'reads':ref(O/'reads.json')},
 'resolved_previous_findings':[
 {'id':'I38-SR-01','status':'STATIC_RESOLVED','fact':'The sole apps/control/main.go missing mode is explicitly supplemented from original NUL-separated target tree: 100644 blob df07f9491aae41bec21dcd918c79e74c738dc32e. Exact supplement keys and other37 original mode fields remain mandatory; no default mode.'},
 {'id':'I38-SR-02','status':'STATIC_RESOLVED','fact':'Only root .gitattributes exact8 bytes * -text followed by LF are permitted; base/target100644 blob fa1385d99a319b43c06f5309d1aae9fdd3adea46 and Git blob hash recomputed. Original5172 protected entries preserved as exact prefix plus this one file. Other active attributes and filter/include configurations remain refused.'},
 {'id':'I38-PRECONDITION-01','status':'PARENT_CREATION_IMPLEMENTED_OUTER_CAPTURE_INCOMPLETE','fact':'Producer validates ancestors without alias/reparse and creates only executor parent after actual registration checks; operation leaf must remain absent. This resolves missing-parent preparation but not all pretry exception capture.'}],
 'verified_static':{
 'candidate_manifest_members':20,'protected_current_files':5173,'runtime_catalog_current_files':1211,'actual_read_files':6467,'checks_passed':len(checks['checks']),'checks_failed':0,
 'source_chain_unique_paths':38,'source_only_chain':['2cdb0d43d5a600eef13c8f1735946a9adf52d079','22752a6a41732c8c158d7d7e1b8932ec958f8cb8','534857db99fa5e694987f877af74c322eaa2a0b3','a5d6d16ffaf129de0361470c3a1570228bd259a2'],
 'canonical_current_bytes_match_preparation':True,'old11_deletions_remain_absent':True,
 'strict_duplicate_safe_controller_JSON':True,'nonfinite_refused':True,'four_ordered_actual_canonical_snapshots_required':True,
 'sealed_registration_audit_invocation_intent_verified_and_commit_receipts_required':True,
 'future_registration_output_shape_matches_existing_Root320_template':True,
 'future_generated_registration_scripts_not_yet_reviewed':True,
 'fixed_Git_invocations_max':56,'query_seconds':60,'FF_seconds':180,'owned_cleanup_seconds':5,
 'owned_job_full_close_required':True,'only_one_FF_no_automatic_retry_reset_rollback_stage_or_push':True,
 'source_or_formal_acceptance':False},
 'copied_canonical_before_refs':checks['canonical_copies'],
 'audit_execution':{'tool_chunk':'576cd2','actual_outer_exit':0,'actual_python_auditor_exit':0,'target_modules_imported':0,'Git_calls':0,'controller_runs':0,'FF_attempts':0,'SQL_HTTP_Go_Node_models':0},
 'limitations':['Read-only AST/source/reference verification only; no target function, helper, registration or integration executed.','Saved original Git raw supplies immutable tree/parent provenance; no fresh Git invocation in this review.','Runtime catalog hashes and Python point-time guards are not Git full-lifecycle OS loading proof.','Root serial integration lease is required; same-user filesystem TOCTOU is not eliminated.','Root321 registration is future and must separately receive nonauthor review; current tuple remains320/148/417.','Five-origin fixed cut422 retains old417 prefix; cut-after Sourceeeed61/Cmddf6aba stay pending and are not silently counted into422.','Whole W05, CLI43, Desktop58, provider, W09,22 parents and42 formal acceptance remain separate.'],
 'new_failure_origins':[],'formal_increment':0}
review_ref=save('review.json',review)
save('actual-audit-observation.json',{'origin':'functions.exec / exec_command tool transcript','chunk_id':'576cd2','actual_exit':0,'wall_time_seconds':2.3218664,'reported_checks':78815,'reported_failed':0,'reported_reads':6467,'raw_stream_file':None,'limitation':'Tool returned stdout inline; no native raw-file redirection was requested. This immutable observation transcribes the actual tool result.'})
manifest_ref=save('manifest.json',{'entries':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'excluded':['manifest.json','handoff.json'],'actual_product_execution':False})
handoff_ref=save('handoff.json',{'decision':review['decision'],'review_ref':review_ref,'manifest_ref':manifest_ref,'requested_change_ids':[finding['id']],'actual_integration_executed':False,'new_failure_origins':[],'next':'New immutable outer prelaunch/controller invocation capture source for narrow static review; do not execute current integration or registration on this review.'})
print(json.dumps({'review':review_ref,'manifest':manifest_ref,'handoff':handoff_ref},ensure_ascii=True))

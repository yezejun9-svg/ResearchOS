import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/handler38-post-integration-r322'
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
a=json.loads((S/'registration-audit.json').read_bytes());p=json.loads((S/'prepared_refs.json').read_bytes());c=json.loads((O/'checks.json').read_bytes())
if c['failed']:raise RuntimeError('Cannot approve failed closed-chain checks')
review={'schema':'researchos.main38-closed-execution-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'EXACT38_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED','requested_changes':[],
 'completed_ref':a['completed_ref'],'manifest_ref':a['manifest_ref'],'post_registration_audit_ref':ref(S/'registration-audit.json'),
 'registered_head':a['registered_head'],'actual_Main_head':'a5d6d16ffaf129de0361470c3a1570228bd259a2',
 'unique_source_paths':38,'source_chain':['2cdb0d43d5a600eef13c8f1735946a9adf52d079','22752a6a41732c8c158d7d7e1b8932ec958f8cb8','534857db99fa5e694987f877af74c322eaa2a0b3','a5d6d16ffaf129de0361470c3a1570228bd259a2'],
 'actual_integration_executor':'codex:/root','independent_reviewer_executed_integration':False,
 'actual_source_only_FF_attempts':1,'actual_source_only_FF_native_exit':0,'saved_Git_native_invocations':56,'saved_Git_native_exit0':56,
 'saved_owned_Python_invocations':2,'saved_owned_Python_native_exit0':2,
 'Root_outer_observation':{'initial_tool_chunk':'c822f3','session_id':65537,'completion_tool_chunk':'eab84b','actual_outer_exit':0,'reported_launcher_exit':0,'separately_observed_launcher_native_exit':None,'metadata_record_ref':p['pins']['main38_outer_completion'],'record_is_original_native_stream':False,'limitation':'Known tool fields are transcribed from original conversation. Original child stdout/stderr and owned process results remain separate immutable files; no synthetic Root native stream is asserted.'},
 'post_registration':{'actual_registration_exit':0,'before':[321,149,422],'after':[322,150,425],'old422_prefix_unchanged':True,'new_origins':3,'new_origins_native_exit':[None,1,1],'all_new_origins_product_native_exit':None,'counter_reset':False,'ST_CM_unchanged':True,'formal_state_unchanged':True,'source_integration_writer_released':True,'fresh_combined_validation_authorized':False,'registration_manifest_ref':ref(S/'manifest.json'),'invocation_ref':a['invocation_ref'],'intent_ref':a['intent_ref'],'verified_ref':a['verified_ref']},
 'closure':[
 'Original321 actual registration, ordered four canonical grant copies and reviewed exact controller/scope/launcher bind the unique operation bfb2f9e18e64469d93e11f0d5b748aa2. Grant snapshots equal original322 metadata bytes.',
 'Owned grant producer and owned integration controller both actually exit0 with complete exclusive Job cleanup. All56 Git invocation native exits0, matching original raw streams and no wrapper error/timeout; sole FF argv targets exact a5d6.',
 'Executor179-member manifest and prior independent1536-check registration audit are retained. Current38 source files match sealed source.after byte hashes; postFF complete status remains source-only pending combined validation.',
 'Source38 original tree/mode/rootattribute and protected5172+1 proof reuse sealed78815-check review. PostFF protected before/after records remain equal and controller completion follows actual postFF protection guards. Old large vectors were not redundantly rehashed in this supplement.',
 'Root322 metadata-only forward registration binds completed_ref and manifest_ref using the original exact relative-path dictionaries. Actual wrapper0, reviewer/script hashes, original streams, intent desired bytes, per-file done receipts and verified tuple all match sealed audit.',
 'Fresh independent bounded Git rev-parse/status/index queries each exit0 with GIT_OPTIONAL_LOCKS=0 and --no-optional-locks. Actual head is a5d6, index empty, status unchanged13rows including11 pre-existing deletions. Four canonical bytes remain unchanged through these queries.'
 ],
 'evidence':{'checks_ref':ref(O/'checks.json'),'reads_ref':ref(O/'reads.json'),'auditor_ref':ref(O/'audit.py'),'actual_audit_tool_chunk':'6454e4','actual_auditor_exit':0,'checks_passed':498,'checks_failed':0,'read_files':291,'readonly_Git_query_refs':[ref(O/(n+'.invocation.json')) for n in ['head','status','index']],'source38_after_ref':p['pins']['main38_source_after'],'launcher_manifest_ref':p['pins']['main38_launcher_manifest'],'launcher_completed_ref':p['pins']['main38_launcher_completed'],'prior_controller_review_ref':p['pins']['integration_controller_review'],'prior_post_registration_source_review_ref':a['review_ref']},
 'runtime_qualification':{'Python_resources':'POINT_IN_TIME_NOT_LIFECYCLE','Git_full_lifecycle_OS_loading_proof':False,'transient_unobserved_load_absence_proven':False,'full_owned_Job_completion_verified':True},
 'not_accepted':['whole W05 parent','CLI43 combined product behavior','Desktop58 combined behavior','W09 finite tests','provider binding/LIVE','22 parent-task acceptance','42 current formal cases'],
 'limitations':['Source-only integration evidence is closed, not a fresh compiled Main qualification. CLI8/Desktop15 imports and combined compilation/replays require new separately reviewed registered scopes.','No new tests, Go/Node/SDK/SQL/HTTP/models/paid calls or mutation of Main/source/canonical/index occurred in this review. Only3 bounded readonly Git queries were executed.','Same-user filesystem TOCTOU is not excluded; Root serial authority and per-action runtime guards remain required.'],
 'actual_product_tests_in_review':0,'actual_model_calls_in_review':0,'source_or_formal_acceptance':False,'formal_increment':0,'new_failure_origins':[]}
rr=save('review.json',review)
mf=save('manifest.json',{'entries':[ref(x) for x in sorted(O.iterdir()) if x.is_file()],'excluded':['manifest.json','handoff.json'],'product_executions':0})
h=save('handoff.json',{'decision':review['decision'],'review_ref':rr,'manifest_ref':mf,'completed_ref':review['completed_ref'],'executor_manifest_ref':review['manifest_ref'],'post_registration_audit_ref':review['post_registration_audit_ref'],'registered_head':review['registered_head'],'new_failure_origins':[],'formal_increment':0,'next':'Root may use this closed source-only evidence as an input to a new explicitly registered CLI8/Main43 scope; this receipt is not that grant.'})
print(json.dumps({'review':rr,'manifest':mf,'handoff':h},ensure_ascii=True))

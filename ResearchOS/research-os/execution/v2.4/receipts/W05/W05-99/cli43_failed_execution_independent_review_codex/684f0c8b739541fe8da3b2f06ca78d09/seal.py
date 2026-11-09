import json, hashlib
from pathlib import Path

O=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99'
U='bf943a8137c74df09e010347615b0eec'
N=P/('integration_codex/cli43-fresh-held2-r328-'+U)
E=P/('cli43_fresh_compiler_executor_codex/'+U)
L=P/('cli43_fresh_compiler_launcher_codex/'+U)
def ref(p):
 p=Path(p); b=p.read_bytes(); return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
a=json.loads((O/'audit.json').read_bytes())
assert a['failed_checks']==[] and len(a['checks'])==12248
origins=[ref(O/('failure-origin.'+n+'.json')) for n in ['cb7175','ad3e4f']]
save('audit.execution.json',{'initial_tool':'92f238','session':98398,'completion_tool':'ea43a7','actual_outer_exit':0,'actual_python_native_exit':0,'explicit_exit_LASTEXITCODE':True,'stdout_ref':ref(O/'audit.stdout.raw'),'stderr_ref':ref(O/'audit.stderr.raw'),'target_executions':0,'separate_original_tool_raw_captured':False})
proposal={
 'schema':'researchos.cli43-http-byte-ownership-cause.v1',
 'cause':'cli43Bytes retains the caller-owned byte slice in raw_base64 while recording length and digest immediately; later JSON serialization can observe changed slice contents.',
 'classification':'SOURCE_ALIAS_DEFECT_WITH_FOUR_ACTUAL_NONEMPTY_DIGEST_DISCREPANCIES',
 'helper_source_ref':next(x for x in a['input_refs'] if x['path'].endswith('/cli43_receipt_instrumentation_test.go.txt')),
 'source_bounds':{'cli43Bytes':34,'Write':[105,109],'post_handler_serialization':[120,121],'cli43Save_MarshalIndent':[29,30]},
 'actual_mismatches':a['HTTP_mismatches'],
 'accepted_copy_relationships':a['accepted_relationships'],
 'confirmed':['All four requested byte counts equal their decoded lengths and are nonzero.','All four decoded digests differ from recorded requested digests.','Each separately owned accepted copy matches the originally recorded requested digest.','The helper stores the original slice without cloning; Python already supports null with zero length and still requires the empty SHA.'],
 'inference_limit':'The exact buffer reuser and timing were not sampled. Evidence JSON prefixes support later buffer reuse; they do not identify a particular runtime operation as the observed mutator.',
 'minimum_new_input':'Clone the input slice once at cli43Bytes entry, then compute raw_base64, bytes and sha256 from that same owned copy. Preserve nil versus nonnil-empty semantics. Keep Writer.Write delegation, n/error, headers, caps, all business assertions and strict Python nonempty/empty digest validation unchanged.',
 'forbidden_repair':['Do not repair or replace r328 raw evidence.','Do not fall back to accepted bytes to certify requested bytes.','Do not bypass SHA validation or classify native test PASS as qualified.'],
 'future_controls_NOT_RUN':['Nonempty caller buffer mutated after snapshot retains original raw bytes/digest.','Nil and nonnil zero-length inputs retain their declared representation and valid empty digest.','Repeated writer/encoder reuse cannot mutate a retained requested snapshot.','Same-length tampered nonempty bytes and incorrect empty digest remain rejected.'],
 'execution_requirement':'A changed instrumentation helper requires fresh instrumented source/compiler/test artifacts and a new Root scope/CAS/grant. This proposal authorizes no execution.',
 'actual_new_controls_executed':0
}
save('cause-and-minimal-correction.json',proposal)
review={
 'schema':'researchos.cli43-failed-execution-independent-review.v1',
 'reviewer':'codex:/root/w05_merge_review',
 'decision':'ACTUAL_FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD',
 'requested_changes':['Correct retained byte ownership in a new instrumentation input and obtain a new Root execution scope; keep all old evidence and qualification guards.'],
 'actual_reviewer_target_executions':0,'actual_product_acceptance':False,'formal_acceptance':False,
 'audit_ref':ref(O/'audit.json'),'audit_execution_ref':ref(O/'audit.execution.json'),
 'cause_review_ref':ref(O/'cause-and-minimal-correction.json'),
 'root_completion_ref':ref(N/'root-launch.outer-completion.json'),
 'root_closed_manifest_ref':ref(N/'root-launch.closed.manifest.json'),
 'executor_result_ref':ref(E/'result.json'),'executor_origin_ref':ref(E/'failure.origin.json'),
 'executor_manifest_ref':ref(E/'manifest.json'),'launcher_manifest_ref':ref(L/'manifest.json'),
 'actual_checks':12248,'failed_audit_checks':0,
 'verified_manifest_member_counts':a['manifest_member_counts'],
 'native_stages':a['native_stages'],
 'case_states':[{'selector':'real-existing-open-readonly','state':'EXECUTED_UNQUALIFIED','actual_native_exit':0,'qualified':False},{'selector':'real-existing-self-send','state':'NOT_STARTED','actual_native_exit':None,'qualified':False}],
 'qualified_cases':0,'recorded_case_results':[],
 'failure_accounting':{'underlying_execution_origin_count':1,'caller_launcher_inner_exits':[1,1,1],'native_stage_exits':[0]*13,'first_cause_actual_stage_native_exit':None,'propagated_exits_are_not_extra_origins':True},
 'compiled_artifact_refs':a['compiled_artifact_refs'],'graph_counts':a['graph_counts'],
 'closed_vectors':a['vectors'],'compiled_current_files_hashed':a['compiled_current_files_hashed'],
 'fixture_files_hashed':a['fixture_files_hashed'],'raw_records_scanned':a['raw_records_scanned'],
 'fixture_evidence':{'business':a['business'],'identity':a['identity'],'http_counters':a['http_counters'],'saved_original_and_copy_typed_rows_equal':True,'original_and_copy_bytes_equal':True,'four_WAL_SHM_paths_absent':True,'reviewer_opened_SQLite':False,'fixture_after_vector_present':False,'qualification_verified_record_present':False},
 'protected_state':{'canonical_tuple':[328,156,469],'four_live_canonical_bytes_equal_grant_copies':True,'direct_Main_HEAD':'a510dbef4a7e08fb5c428df44c39b133f3ffa856','canonical_writes':0,'source_writes':0,'index_writes':0,'new_Git_invocations':0,'status_index_evidence':'Existing frozen actual facts reused; no new status/index command.'},
 'limits':['No full historical compiler/OS backing-tree rehash; new compiled artifacts and closed saved vectors were checked.','No independent SQL re-export; saved typed-row JSON and actual closed DB bytes were compared.','Test parent/leaf PASS and native0 are actual observations, not HTTP evidence qualification.','Fixture-after validation was not reached. HTTP received legs are observed counters, not a complete unobserved-client outbound hard cap.','Root outer tool observations are transcriptions of known actual objects; no independent original outer native stream or caller OS lifecycle proof is claimed.','Desktop15, fresh current43 qualification, whole W05 and formal gates remain open.'],
 'SDK_MODEL_external_paid':0,'new_failure_origins':origins,
 'counter_policy':'Two reviewer locator failures are separate post-cut pending origins. The underlying execution failure is one. No canonical failure counter was changed.'
}
save('review.json',review)
save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'cause_ref':ref(O/'cause-and-minimal-correction.json'),'new_failure_origin_refs':origins,'status':'STOPPED','target_executions':0,'qualification':'WITHHELD'})
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.immutable-public-manifest.v1','count':len(members),'entries':members,'excluded_only_self':True})
print(json.dumps({'review':ref(O/'review.json'),'handoff':ref(O/'handoff.json'),'manifest':ref(O/'manifest.json'),'cause':ref(O/'cause-and-minimal-correction.json'),'origins':origins},ensure_ascii=False))

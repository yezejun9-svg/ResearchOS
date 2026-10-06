from pathlib import Path
import json,hashlib,datetime,subprocess
O=Path(__file__).parent;A=O/'attempt3';L=json.loads((O/'locations.json').read_bytes());R=Path(L['root']);W=Path(L['worktree']);AUTHOR=R/'.local/worktrees/codex-w0599-provider-binding'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=read(O/'scope.original.json');result=read(A/'execution.result.json');mutation=read(A/'database_mutation_audit.json');failure=A/'cases/1-missing_dispatch_and_transport';baseline=A/'cases/1-baseline';f=read(failure/'actual.json');b=read(baseline/'actual.json')
assert result['executed_case_count']==2 and result['results'][0]['invocation']['exit']==0 and result['results'][1]['invocation']['exit']==1
assert f['inventory_error'] is None and f['stream_backup_error'] is None and f['inventory_count']==0
assert b['inventory_error'] is None and b['stream_backup_error'] is None and b['inventory_count']==1
assert mutation['schema_exact_equal'] and mutation['changed_tables']==['resource_effects','runtime_dispatches']
assert not result['input_drift'] and not result['original_database_drift']
checks=[]
for e in s['source9']:
 checks.append({'path':e['path'],'isolated_sha256':ref(W/e['path'])['sha256'],'author_sha256':ref(AUTHOR/e['path'])['sha256'],'expected':e['sha256']})
assert all(e['isolated_sha256']==e['author_sha256']==e['expected'] for e in checks)
save('source9.after.json',checks)
head=subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD']).decode().strip();dirty=subprocess.check_output(['git','-C',str(W),'diff','--name-only']).decode()
assert head==s['source_candidate'] and not dirty
save('checkout.final.json',{'head':head,'tracked_diff':dirty,'main_was_not_used_as_diagnostic_source':True})
review={
 'schema':'researchos.independent-zero-model-p12-review.v1','actor':'/root/w05_merge_review','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'NEEDS_FIX_P1_ORIGINAL_MODEL_OMITTED_FROM_ZERO_OBSERVATION_INVENTORY',
 'source_candidate':head,'source9':ref(O/'source9.after.json'),
 'authority':[ref(O/'scope.original.json'),ref(O/'attempt2/recovery_scope.original.json'),ref(A/'recovery_scope.original.json')],
 'executed':{'internal_cases':2,'internal_baseline_pass':1,'unexpected_accept_failure':1,'public_positive_cases':0,'public_corruption_cases':0,'second_combination_executed':False,'other_database_lanes_executed':False,'planned_but_unexecuted':22,'automatic_retries':0,'model_calls':0,'worker_starts':0,'paid_calls':0},
 'finding':{
  'id':'P9-P12-SR01','severity':'P1','title':'Deleting dispatch and provider_transport removes an extant MODEL effect from validation',
  'source_locations':['internal/domain/runtime_model_verification.go:165-170','internal/domain/runtime_model_stream.go:275-287'],
  'trigger':'An existing PREPARED MODEL effect has no SDK observation; original runtime_dispatch row and payload.provider_transport are absent in a corrupted backup candidate.',
  'observed':'validateProviderInventory returns nil and empty transports; validateModelStreamBackup returns nil. The unchanged baseline returned nil and exactly one transport. One original MODEL effect and its original key/sequence/request_hash remain, while dispatch count changes from 1 to 0. No new MODEL effect is created.',
  'mechanism':'ErrNoRows rejects only when the removable provider_transport payload marker remains. Removing that marker reaches continue, so the original effect is lost from inventory. With zero stream observations, the downstream stream validator has no second witness to reject.',
  'mutation':'Only resource_effects.body provider_transport removal and runtime_dispatches deletion. All four trigger definitions restored verbatim before validators. SQLite schema is exact equal, 82 other tables unchanged; original key, PREPARED state, MODEL capability, sequence and request_hash are unchanged.',
  'impact_bound':'Actual bypass is demonstrated for the internal provider inventory and model-stream backup semantic validators. Public CreateBackup/RestoreBackup/rebackup were NOT executed after the first failure and may have other rejecting layers. Do not claim a complete archive-signature or public restore bypass.',
  'qualification_consequence':'P12 cannot be considered complete; no source acceptance or LIVE/parent/formal qualification follows.',
  'minimum_repair_proposal':{
   'likely_existing_paths':['internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go'],
   'guard':'Do not use removable request provider_transport/admission policy markers as the sole authority for whether a MODEL original requires a dispatch. Fail closed on an identifiable original MODEL whose dispatch/original profile authority is missing. Derive policy/original membership from retained typed Run/Task/runtime/profile and immutable effect identity where available; do not make altered payload flags authoritative.',
   'legacy':'Preserve legitimate absent-policy non-MODEL behavior using exact original authority distinctions. Do not blanket-whitelist missing metadata, skip PREPARED/STARTED/UNKNOWN, or require final/LIVE to validate a partial original.',
   'regression':'After Root separately registers causal repair, preserve this exact red binary/raw and re-run the same copied bytes against repaired source with original identity unchanged; complete the second coordinated-removal case, zero-observation states and public positive boundaries only within a newly explicit scope. No original held positive/model-chain retry is authorized here.',
   'not_implemented_by_reviewer':True
  }
 },
 'evidence':{
  'baseline':{n:ref(baseline/n) for n in ['case.json','invocation.json','stdout.raw','stderr.raw','actual.json','fixture.sqlite']},
  'negative':{n:ref(failure/n) for n in ['case.json','invocation.json','stdout.raw','stderr.raw','actual.json','fixture.sqlite']},
  'mutation_audit':ref(A/'database_mutation_audit.json'),'database_freeze':ref(A/'original_database_freeze.json'),
  'actual_test_binary':ref(A/'p12.test.exe'),'binary_freeze':ref(A/'binary.freeze.json'),
  'actual_go_list':{n:ref(A/n) for n in ['go-list.invocation.json','go-list.stdout','go-list.stderr']},
  'compile':{n:ref(A/n) for n in ['compile.invocation.json','compile.stdout','compile.stderr','buildinfo.invocation.json','buildinfo.stdout']},
  'execution_result':ref(A/'execution.result.json'),'overlay':ref(A/'p12_overlay_test.go'),'runner':ref(A/'execute.py'),
  'compile_inputs_before':ref(A/'inputs.before.json'),'compile_inputs_after':ref(A/'inputs.after_compile.json'),
  'first_case_input_freeze':ref(A/'before_first_case.freeze.json'),'after_cases_input_freeze':ref(A/'inputs.after_cases.json')
 },
 'closed_inputs':{'compile_input_count':5971,'before_first_case_input_count':6006,'all_original_six_databases_unchanged':True,'source9_author_and_independent_unchanged':True,'input_drift':[],'schema23_foundation':'EXCLUDED','Main_L02':'COMPARISON_ONLY_NOT_IMPORTED'},
 'zero_model_basis':['Only exact TestIndependentP12Offline was executed in the frozen binary. No TestMain exists in package; package init paths register domain operations.','Receipt-owned executed path uses local SQLite reads/mutations, validateProviderInventory and validateModelStreamBackup. It does not construct Host, RuntimeCoordinator, credential resolver, SDK session, HTTP client/server or worker.','Actual directly launched test process PID/argv and executable SHA are recorded in each invocation; test code contains no child process launcher. This is not a system-wide network/process tracing claim.','The zero fields in actual.json are driver declarations; independent support is the executed call graph, direct invocation, unchanged effect count and preserved original-effect identity, not those declarations alone.'],
 'failure_chain':{'historical_model_history_refusals':5,'reset':False,'held_positive_runs':0,'prior_two_go_list_failures':'Preserved; Root imported their tooling origins with explicit public-dependency recovery scopes. They are not MODEL retries.','new_product_failure_origins':1},
 'source_changes':0,'canonical_registry_changes':0,'formal_increment':0,'live_increment':0,
 'stop_compliance':'Stopped immediately after first negative unexpected accept. No public boundary, other state/combination, repair or retry was run.'
}
save('review.json',review)
origins={'schema':'researchos.independent-failure-origins.v1','entries':[{'id':'p9-p12-sr01-prepared-missing-dispatch-and-transport','kind':'actual-product-semantic-unexpected-accept','invocation':ref(failure/'invocation.json'),'stdout':ref(failure/'stdout.raw'),'stderr':ref(failure/'stderr.raw'),'actual':ref(failure/'actual.json'),'closed_database':ref(failure/'fixture.sqlite'),'actual_exit':1,'candidate':head,'chain':'independent-zero-model-P12-diagnostic','model_history_chain_not_retried':True}],'already_imported_not_recounted':[ref(O/'failure_origins.precompile.json'),ref(O/'attempt2/failure_origins.json')],'new_product_origins':1,'new_tooling_origins':0,'original_history_counter':5}
save('failure_origins.final.json',origins)
manifest={'schema':'researchos.independent-receipt-manifest.v1','excludes':['manifest.json','handoff.json'],'entries':{p.relative_to(O).as_posix():ref(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['manifest.json','handoff.json']}}
save('manifest.json',manifest)
save('handoff.json',{'from':'/root/w05_merge_review','to':'/root','decision':review['decision'],'candidate':head,'review':ref(O/'review.json'),'manifest':ref(O/'manifest.json'),'failure_origins':ref(O/'failure_origins.final.json'),'product_source_writes':0,'models_workers_paid':0,'formal_increment':0})
print(json.dumps({n:ref(O/n) for n in ['review.json','failure_origins.final.json','manifest.json','handoff.json']},ensure_ascii=False))

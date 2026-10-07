from pathlib import Path
import json,hashlib,datetime
R=Path.cwd();O=Path(__file__).parent;W=R/'.local/worktrees/codex-w0599-provider-binding';P=W/'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/provider-39d6478d4a884156b0881788325e4c63'
def put(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
audit=json.loads((O/'final_read_audit.json').read_bytes());seal=json.loads((P/'held_candidate_10_seal.json').read_bytes());held=json.loads((O/'attempt3/held_seal_audit.json').read_bytes())
audit['closure']['compiled']['file_map_comparison']=json.loads((O/'compiled_vector_shape_clarification.json').read_bytes())
audit['closure']['compiled']['clarification_ref']=ref(O/'compiled_vector_shape_clarification.json')
assert not audit['manifest_entries']['mismatch'] and not audit['commit_blobs']['mismatch']
assert audit['closure']['compiled']['file_map_comparison']['file_map_equal']
review={
 'schema':'researchos.independent-provider-failure-chain-review.v1',
 'reviewer':'/root/w05_merge_review','role':'Independent reviewer; not source author or Root registrar','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'READONLY_EVIDENCE_REVIEW_COMPLETE_CURRENT_QUALIFICATION_HELD',
 'candidate_commit':'976c8c9a6bdf8703475e02b79b77f4c5fab2d650',
 'not_source_acceptance':True,'formal_increment':0,'live_increment':0,
 'inputs':{n:ref(P/n) for n in ['handoff.json','manifest.json','source-final.json','failure_origins.json','failure_origins.v2.json','held_candidate_10_seal.json','P01-P12-evidence-matrix.json']},
 'independent_audits':[ref(O/'final_read_audit.json'),ref(O/'attempt3/failure_chain_audit.json'),ref(O/'attempt3/held_seal_audit.json'),ref(O/'attempt3/actual_read_audit.json')],
 'scope':{'source_paths':audit['source9'],'writes':'Own new independent receipt namespace only','executed':'Public raw/hash/Git-blob reads and SELECT on 4 sealed public fixture SQLite files using mode=ro&immutable=1, before/after hashes unchanged. No held test, model, coordinator, paid network, actual credential or private database execution.'},
 'failure_chain':{
  'original_failed_invocations_verified':9,'root_already_imported_original_nine':True,'new_import_of_those_nine':False,
  'same_history_chain':['C2','C3','C4','C5','C6'],'same_history_failure_count':5,
  'boundary':'C3 reached second failure. C4/C5/C6 continuation cannot be retroactively authorized by later C10 PASS. A new actor/directory/script is not a reset.',
  'causal_changes_read':[
   'C4 was diagnostic only. C5 role fix still missed fixed SDK CWD suffix. C6 diagnostic still failed; these are not successful recovery proofs.',
   'Current providerRequestHistory accepts only initial exact fixed instruction (+ immutable dispatch staging_directory/output CWD), system/developer role under policy; it refuses additional or arbitrary instruction. This is a concrete source explanation for the earlier history mismatch, not yet current held-positive proof.',
   'Current copy-before-Merge avoids mutating original history/snapshot, addressing later C7 STALE_INPUT cause separately.',
   'C9 missing workspace/Project relation was a fixture prerequisite defect. Current explicit synthetic Project/workspace binding supports fixture restore; it is not a real project.bootstrap acceptance.',
   'Insufficient-budget negative originally configured unlimited budgets and issued one loopback HTTP; later corrected fixture does not erase this original unexpected effect.'
  ],
  'frozen_rule_refs':['spec/v2.4/08_AGENT_EXECUTION_GOAL.md (fixed failure input retry/stop, origin and resume conditions)','spec/v2.4/21_EXECUTION_CARDS.md (BLOCKED/FAILED/CANCELLED resume with reason and counters retained)','spec/v2.4/18_EXISTING_REPOSITORY_MIGRATION.md (no reset through version/candidate/executor rename)'],
  'past_gaps_irrecoverable_as_test_time_proof':['C1-C8 omitted original hashes for 3 then-untracked test files. Later v2 is transparent additional evidence only.','C2-C8 lack sealed database snapshots; do not reconstruct or claim their current graph checks passed.','C10 source9 reconstruction matches recorded hashes but was written afterward; original test binary was not separately retained.']
 },
 'held_C10':{'status':'HELD_HISTORICAL_FIXTURE_OBSERVATION_NOT_CURRENT_QUALIFICATION','sealed_refs_verified':True,'source_and_audits_entries':held['source_entries'],'domain_evidence_entries':held['domain_evidence_entries'],'public_final_dbs_read':held['held_original_db_metadata'],'original_domain_counts':'20 PASS / 0 FAIL / 0 SKIP per retained raw/seal; not rerun','current_same_run_test_changed':'Appended later Task/Run scenario expects total 4 loopback MODEL calls; old C10 3-call positive cannot prove it.'},
 'current_existing_evidence':{'actual_go_counts':held['counts_current_nonheld_cohort'],'actual_js_counts':audit['actual_js_counts'],'manifest_and_git':{'manifest':audit['manifest_entries'],'git':audit['commit_blobs']},'closure':audit['closure'],'limits':['Regex explicitly excludes two held positive tests.','CLI194 applies to source candidate based on 396287cc, not later Main L02 composition.','Bridge TestW05CrashHelper standalone entry is actually SKIP; parent crash-driver assertions are separately PASS. Do not relabel cohort zero-skip.','Current vector integrity does not retroactively fill earlier missing test sources or databases.']},
 'gate_assessment':[
  {'id':'P01','status':'PARTIAL','missing':'Literal pre/post absent-policy request+cost golden hashes across original routes.'},
  {'id':'P02','status':'HELD','missing':'Current fixed-source real SDK -> ordinary same Run tool -> MODEL and original whole reasoning, after causal recovery authorization.'},
  {'id':'P03','status':'LOCAL_CONTROLS_SUPPORTED','limit':'26 actual SDK controls and common reasoning/order tests; not gateway compatibility or LIVE.'},
  {'id':'P04','status':'PARTIAL','missing':'Complete new-policy redirect/header/authority rejection matrix; preserve before-PREPARED binding and zero-HTTP assertions.'},
  {'id':'P05','status':'HELD_AND_PARTIAL','missing':'Current later Task/Run stable affinity + qualification isolation; duplicate/missing canonical witnesses and STEER/FOLLOW_UP ambiguity combinations.'},
  {'id':'P06','status':'HELD_AND_PARTIAL','missing':'Current MODEL-only fixture qualification; independent new-policy extra model-call/bootstrap-tool refusals.'},
  {'id':'P07','status':'PARTIAL','missing':'New-policy full native SQLite/compiled CLI causal pipeline; inherited absent-policy >32 delta controls do not alone prove it.'},
  {'id':'P08','status':'PARTIAL','missing':'New-policy native canonical multiround cancellation; JS abort withheld-credit evidence alone is transport-scoped.'},
  {'id':'P09','status':'PARTIAL','missing':'New-policy ordinary session projection/error/detail full quarantine combinations; existing bootstrap UNKNOWN negatives and repaired signed-zero regressions remain useful.'},
  {'id':'P10','status':'PARTIAL','missing':'New-policy exact original-key replay/no HTTP increase and all original-identity cases.'},
  {'id':'P11','status':'SUPPORTED_FOR_CANDIDATE_BASE_WITH_HELPER_SKIP','missing':'Later Main L02 combined-current source vector; do not repeat old broad cohorts without integration change.'},
  {'id':'P12','status':'PARTIAL_POTENTIAL_SKIP_PATH_UNTESTED','missing':'Missing-dispatch + removed transport, missing profile_ref + removed policy + removed transport, zero-observation PREPARED/STARTED inventory, current public restore/later-head preservation. Static continue is a concrete counterexample target, not an independently demonstrated product vulnerability.'}
 ],
 'next_zero_model_adjudication_proposal':{
  'requires_root_scope_registration':True,'namespace':'New provider_binding_zero_model_adjudication_codex/<uuid> in independent checkout; receipt-owned overlay test driver only, product source9 unchanged',
  'input_database_refs':{n:e for n,e in seal['actual_domain_run_evidence'].items() if n.endswith('.sqlite')},
  'commands':'Compile a receipt-owned Go test overlay in package domain against candidate source9; run only new OfflineProviderInventory controls, never TestProviderBindingActualSameRunToolHistory or TestProviderBindingAllOriginalStatesPortable.',
  'model_calls':0,'coordinator_and_sdk_start':False,
  'controls':['Copy each sealed public DB; verify SHA and original unchanged afterward. Read originals immutable; perform corruptions on separate exclusive copies only.','Unaltered copies must pass the relevant current validator before a negative result is meaningful. Include zero-observation effect_prepared/effect_started and UNKNOWN/NOT_APPLIED/CONFIRMED and completed ordinary Run.','On fresh copies remove original dispatch plus provider_transport; separately remove admission.profile_ref + admission.profile.model_config.provider_policy + provider_transport. Keep explicit mutations and before/after DB hashes; use trigger disable only in disposable corruption fixture.','Run validateProviderInventory and validateModelStreamBackup separately; record exact error layer and effect membership, not merely nonnil from an unrelated SQL/schema break.','Restore trigger definitions before outer schema/public restore checks; if creating corruption archive through lower-level test scaffolding, mark it synthetic and preserve signed manifest/digest/semantic distinctions. Never bypass a legitimate CreateBackup refusal and call that product archive valid.','Current sealed DB -> public CreateBackup/RestoreBackup/rebackup can be tested without constructing a worker/model; workspace relation/authorized fixture-only mapping must be explicit and unchanged. Verify no dispatch or credential resolver runs.'],
  'stop':'Unexpected accept or unrelated prerequisite refusal => retain raw and stop that lane; do not run held positives to compensate. Root decides repair scope; this diagnostic does not reset five-failure chain.'
 },
 'conditional_single_current_positive_plan':{
  'authorized_now':False,'recovery_preconditions':['Root records same chain identity and five cumulative history failures, preserved 9 origin refs, exact causal fixes/new evidence and explicit restoration reason.','Complete zero-model P12 adjudication first and resolve any real blocker; independently review any new code before changing frozen candidate.','Freeze original source9 plus all actual compiled/runtime inputs (including untracked tests), SDK/build script/lock/tools/node/go/git when used, fresh bundle, test executable, declared fixture requests/responses and stage capture driver before first execution. Hash again after each stage; do not backfill.','Driver must capture consistent public DB before cleanup on every successful AND failed phase; existing final-fixture cleanup alone is insufficient to promise snapshots at qualification/first MODEL/tool/later MODEL/acceptance/restore boundaries. Register receipt-only instrumentation/overlay separately; no product authority changes.'],
  'bounded_sequence':['Single current TestProviderBindingActualSameRunToolHistory run: qualification 1 + ordinary same Run 2 + later same-session Run 1 = at most 4 loopback MODEL calls; one read-only workspace tool. New-policy profile remains FIXTURE. Stop entire sequence on first failure/refusal or count increase.','Then run exact portable CONFIRMED once (1 loopback MODEL); reuse its PREPARED/STARTED snapshots for offline restore, no second model call.','Then exact portable UNKNOWN once (1 loopback MODEL); no retry or adoption; NOT_APPLIED once (0 HTTP). Each is separately orchestrated so a failing subtest cannot silently continue other lanes.'],
  'total_max_loopback_model_calls':6,'real_provider_calls':0,'automatic_retries':0,
  'first_same_history_failure_action':'Append next attempt/failure to original chain and halt. No new namespace, executor, or diagnostic invocation to reset it.',
  'completion_limit':'This narrowly resolves current held positives and selected offline backup gates only. P01/P04/P05 ambiguity/P06 negative/P07/P08/P09/P10 remaining cases stay OPEN unless separately preregistered and evidenced; no SOURCE_READY/global P01-P12 inference.',
  'live':'Still prohibited. Official model context/estimated cost and resource access200 do not establish gateway billable hard bound B01, protected runtime qualification, or authority to retry existing UNKNOWN.'
 }
}
proposal={
 'schema':'researchos.independent-zero-model-p12-execution-proposal.v1','status':'PROPOSED_NOT_AUTHORIZED_OR_EXECUTED','actor':'/root/w05_merge_review',
 'source_candidate':review['candidate_commit'],'source9':audit['source9'],'original_chain_failure_count':5,'held_positives_remain_held':True,
 'plan':review['next_zero_model_adjudication_proposal'],
 'database_subset':'Use six original sealed copies: completed ordinary Run; CONFIRMED effect_prepared/effect_started/final; UNKNOWN final; NOT_APPLIED final. Restored copies are optional comparison inputs only, never substituted for originals.',
 'preexecution_freeze':{
  'base_choice':'Use immutable candidate976c8c9a for the first narrowly scoped P12 diagnostic. It contains schema22 and older CLI. Record Root CP273 Main HEAD as comparison only. Do not silently rebase or compose new Main/SQL23 into this diagnostic.',
  'foundation':'Foundation fef0ee2 and schema23 upgrade remain isolated MAIN_HOLD. No import of foundation5, migration23 or upgrade10 into this test. Freeze all actually installed numbered migrations and additive client SQL from the candidate; this review does not qualify restore with schema23.',
  'cli':'No CLI execution required for these library-level zero-model controls. Candidate CLI194 and Main L02 CLI234 are separate facts. If Root requires a combined source candidate instead, freeze a new explicitly registered Main HEAD + exact provider9 composition and all Go compile inputs before running; do not inherit this candidate-source claim.',
  'old_compiler':audit['closure']['tools'],'old_bundle':audit['closure']['bundle'],'old_compile_vector':audit['closure']['refs'][2],
  'new_compiled_driver':'After Root registration, build once from exact candidate plus receipt-owned new test overlay. Record Go-list -deps -test files, embeds, schema/contract inputs, generated/overlay sources, tool binaries/environment and driver/test executable SHA before first control. Old binary must not be called a new overlay test binary. Preserve build raw and before/after vectors. Bundle is hashed but never launched.',
  'driver_write_bounds':'New independent receipt namespace plus independent checkout/cache only. Source9, original fixture DBs, author worktree, Main canonical and original receipts remain untouched.'
 },
 'zero_model_proof':['Driver references store/domain backup validation helpers and explicit synthetic workspace mapping only; do not instantiate RuntimeCoordinator, RunAdmitted, Scan, AgentSession, Host or credential resolver.','Static driver read review before run; record actual subprocess tree and argv: compiler, test2json and test binary only, no Node/worker/provider process.','No HTTP server/client or provider route in the zero-model driver; no credential environment/material. Network remains disallowed. State/database effect ledger before/after should show no newly dispatched MODEL effect; mutation differences are explicit corruption fixtures only.','Public restore driver must use sealed fixture DB and local synthetic backup key/workspace mapping. Declare every lower-level synthetic archive alteration and hash; never present it as production valid archive.'],
 'fixed_control_budget':{'fixtures':6,'negative_combinations_per_fixture':2,'positive_validator_baseline_per_fixture':1,'maximum_internal_control_cases':18,'public_backup_restore_positive_per_fixture':1,'maximum_public_positive_cases':6,'additional_public_corruption_cases':'Only where internal negative can pass earlier schema/digest boundaries using transparent synthetic archive fixture; enumerate before run, never silently expand.','paid_calls':0,'worker_starts':0,'automatic_retries':0},
 'result_classification':'Report inner inventory, stream backup validator and actual public create/restore boundaries independently. An early schema/digest refusal is not proof of semantic detection. Unexpected acceptance => actual P1 evidence; unrelated prerequisite failure => BLOCKED diagnostic, no inferred security pass.',
 'stop':'First unexpected acceptance/failure stops dependent controls and produces immutable raw. No held positive execution, no source fix or rerun without Root follow-up scope.',
 'actual_schema22':ref(W/'migrations/sqlite/0022_client_command_queue.sql')
}
put('zero_model_execution_proposal.json',proposal)
review['zero_model_execution_proposal']=ref(O/'zero_model_execution_proposal.json')
review['held_C10']['independent_original_raw_counts']=ref(O/'held_original_raw_counts.json')
put('review.json',review)
fail={'schema':'independent-tooling-failure-origins.v1','already_imported_executor_nine':ref(P/'failure_origins.json'),'new_product_failures':[],'new_tooling_origins':[{'id':'audit-invocation-exit-field-assumption','locator':'functions.exec exec_command chunk fd0f7e in reviewer tool transcript','actual_exit':1,'script':ref(O/'audit.py'),'raw_limitation':'Original output only in tool transcript; do not represent a later reconstruction as original raw.','cause':'Exit belongs to result.json, not invocation.json.'},{'id':'audit2-raw-extension-assumption','invocation':ref(O/'attempt2/invocation.json'),'stderr':ref(O/'attempt2/stderr.raw'),'stdout':ref(O/'attempt2/stdout.raw'),'actual_exit':1,'cause':'Closure output files use .stdout/.stderr, not .stdout.raw/.stderr.raw.','same_outer_call_diagnostic':'Outer print also hit cp936 UnicodeEncodeError in tool chunk90f80a; same original invocation, not a second product failure.'}],'successful_followups':[ref(O/'attempt3/invocation.json'),ref(O/'final_audit.invocation.json')]}
fail['new_tooling_origins'].append({'id':'migration-locator-read-error','locator':'functions.exec exec_command chunk319a2e','actual_exit':1,'cause':'Read-only rg guessed nonexistent internal/store/migrations; rg --files located migrations/sqlite/0022_client_command_queue.sql. No source or product action.','raw_limitation':'Tool transcript only; no saved original subprocess raw.'})
put('failure_origins.json',fail)
manifest={'schema':'independent-review-manifest.v1','excludes':['manifest.json','handoff.json'],'entries':{p.relative_to(O).as_posix():ref(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['manifest.json','handoff.json']}}
put('manifest.json',manifest)
put('handoff.json',{'from':'/root/w05_merge_review','to':'/root','decision':review['decision'],'review':ref(O/'review.json'),'manifest':ref(O/'manifest.json'),'failure_origins':ref(O/'failure_origins.json'),'candidate':review['candidate_commit'],'held_positive_runs':0,'paid_network_calls':0,'source_changes':0,'formal_increment':0})
print(json.dumps({'review':ref(O/'review.json'),'handoff':ref(O/'handoff.json'),'manifest':ref(O/'manifest.json'),'failure_origins':ref(O/'failure_origins.json')},ensure_ascii=False))

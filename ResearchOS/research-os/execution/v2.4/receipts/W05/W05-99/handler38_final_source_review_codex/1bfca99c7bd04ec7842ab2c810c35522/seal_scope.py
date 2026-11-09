from pathlib import Path
import json,hashlib,datetime
R=Path('D:/作品集/ResearchOS/research-os'); W=R/'.local/worktrees/codex-w0599-host-configuration-handler'
N=R/'execution/v2.4/receipts/W05/W05-99/handler38_final_source_review_codex/1bfca99c7bd04ec7842ab2c810c35522'
P=N.parent/'a639cfcf998f4c7fb182db19c6788c3b'
H=lambda b:hashlib.sha256(b).hexdigest()
def save(n,o): (N/n).write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def ref(p): return {'path':str(p.relative_to(R)).replace('\\','/'),'sha256':H(p.read_bytes()),'bytes':p.stat().st_size}
def read(n): return json.loads((P/n).read_bytes())
h=read('author-final-handoff.json');c=read('author-final-coverage.actual.v2.json')
# Verify coverage locators against actual Go test events, not only report labels.
loc=[]
for group in c['handler_30_groups']:
 for e in group.get('evidence',[]):
  rr=e.get('raw'); target=e.get('actual_test')
  if not rr or not target: continue
  p=W/rr['path']; lines=p.read_bytes().splitlines(); l=rr.get('locator',{}); a=l.get('line_start');b=l.get('line_end',a)
  hit=[]
  if a and b:
   for raw in lines[a-1:b]:
    try: event=json.loads(raw)
    except (ValueError,UnicodeDecodeError):continue
    if event.get('Test')==target and event.get('Action')=='pass': hit.append(event)
  loc.append({'case':group['id'],'actual_test':target,'raw':rr,'pass_event_at_exact_locator':bool(hit)})
save('coverage_locator_audit.json',{'rows':loc,'unmatched':[x for x in loc if not x['pass_event_at_exact_locator']]})
ack=[]
for rr in c['valid_ACK_actual_reason_refs']:
 b=(W/rr['path']).read_bytes();o=json.loads(b);ack.append({'ref':rr,'actual_sha256':H(b),'actual_reason':o.get('reason'),'matches':H(b)==rr['sha256'] and o.get('reason')=='CONFIGURE_NOT_COMPLETED'})
save('ack_actual_reason_audit.json',ack)
# Preserve exact author failure reports; no recalculation of Root canonical counters.
(N/'failure_reports').mkdir(exist_ok=True)
fails=[]
for rr in h['failure_supplement_refs']+h['latest_additional_failure_refs']:
 b=(W/rr['path']).read_bytes(); dest=N/'failure_reports'/(H(b)+'.json')
 if not dest.exists():dest.write_bytes(b)
 fails.append({'original':rr,'hash_matches':H(b)==rr['sha256'],'copy':ref(dest),'top_level_fields':list(json.loads(b))})
save('failure_report_audit.json',{'reports':fails,'counting':'Reports may repeat the same original invocation. They are preserved, not summed into a fresh failure counter. Unknown outer exit remains unknown. Original fullCLI 12 failed events belong to one invocation.','known_contract_report':'69 successful check IDs, 26 failure entries, 0 not_verified; not a 69-test whole-suite PASS.'})
# Producer source read/copy/hash audit; no SQL read or product execution.
paths=['internal/domain/client_protocol.go','internal/domain/client_protocol_configuration.go','internal/domain/client_protocol_sessions.go','internal/domain/resources.go','internal/domain/durability.go','internal/domain/runtime_permission_windows.go','internal/domain/runtime_configuration_binding_windows_test.go']
inputs=[]
for rel in paths:
 b=(W/rel).read_bytes();dest=N/'public_producer_sources'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 inputs.append({'path':rel,'before_sha256':H(b),'copy':ref(dest),'after_sha256':H((W/rel).read_bytes())})
save('producer_read_audit.json',inputs)
base='execution/v2.4/receipts/W05/W05-99/host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec/tls-runner-compiled-41b2091700e248b9a7e9f1b05ff5d727/run-82ea516f44c24025b35e6467fbf56c50/public-fixtures/TestHandlerTLSActualSDKConfiguredSession/handler-typed-tls-sdk.sqlite'
bp=W/base; dbref={'path':base,'sha256':H(bp.read_bytes()),'bytes':bp.stat().st_size,'read_mode':'byte hashing only; SQLite not opened'}
assert dbref['sha256']=='16a69152e10889815d686f1d91387e3dfd4d0086d6fca6b109698b9b2b33a3d1'
plan={
 'schema':'researchos.handler38.independent-execution-supplement.v1','status':'PROPOSED_NOT_EXECUTED_ROOT_CAS_REQUIRED','reviewer':'codex:/root/w05_merge_review','candidate':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8','base_plan':ref(P/'execution_plan.json'),
 'supersedes_only':'C09 input base choice: reuse byte-fixed public author closed fixture via six independent copies instead of running another SDK fixture to create it. All other first-plan guards remain.',
 'author_final_inputs':{k:h[k] for k in ['source_freeze_ref','coverage_ref','evidence_manifest_ref']},
 'source_scope':{'candidate_files':38,'production_modifications':0,'canonical_modifications':0,'private_resources':0,'paid_calls':0,'external_calls':0,'C09_model_worker_node_HTTP_calls':0},
 'checkout':'.local/independent-handler38-a639cfcf','receipt_namespace':'execution/v2.4/receipts/W05/W05-99/handler38_independent_replay_codex/<newUUID>',
 'overlay':{'virtual_path':'<isolated_checkout>/internal/domain/handler_configuration_independent_review_test.go','physical_path':'<new_receipt_namespace>/overlay/handler_configuration_independent_review_test.go','mapping_path':'<new_receipt_namespace>/overlay/overlay.json','package':'domain','selector':'^TestIndependentHandlerConfigurationC09$','constraint':'Only this test-only virtual new file. No product replacement, test deletion, build tag/Skip, trust bypass or alternate product implementation. Root must authorize overlay preparation and test execution before either occurs.','capture':'Hash physical Go bytes, mapping JSON, specs, copied DB and all compiler inputs before build. Every go-list and build command records -overlay absolute mapping; mapping keys include absolute virtual source path and physical replacement. Test exe hash freezes after build before first case. Record actual overlay bytes seen by compiler, not merely nonexistent virtual path or go-list filenames.'},
 'C09_closed_input':dbref,
 'C09_setup':[
 'Six independent byte copies under owned receipt fixture directories; original fixed DB immutable. Hash before opening; record full sqlite_schema and all typed rows including rowid, histories, originals, journals, budget ledger and reference tables; hash checkpointed/closed DB after. Initial semantic inventory is only read after Root authorization.',
 'Use copied Service and ClientService with SessionRuntime nil; only explicitly SYNTHETIC metadata fixture satisfying same principal/provider Host policy, no Host.New/decrypt/user vault/coordinator. Principal/current session/config/ref derived by exact original journal/typed bindings, not hardcoded status label or caller flag.',
 'Renew the same legitimate writer via actual session.attach Execute with request_write_owner=true and exact current revision/epoch before injection. Record HandoffEpoch, CLIENT_HANDOFF journal and legitimate lease/revision/epoch delta. Do not directly extend lease or forge existing authority. If attach cannot succeed, stop as prerequisite failure; no fallback patch.',
 'Read original head configuration and actual Session CAS, then prepare one scoped host.configure with a new command id, config_revision=head+1 and same valid saved settings; null or existing credential exactly as fixed typed baseline. No provider qualification and no profile adoption inferred.',
 'Record case pre-configure baseline AFTER legitimate attach and explicitly labeled test injection, then compare command effects to that baseline. Two positive counterparts run first: permission-resolved-positive, all-runs-settled-positive. Negative order permission-open, permission-acknowledged, older-run-unknown-hidden-by-later-settled-run, older-run-running-hidden-by-later-settled-run. Each case one command plus exact replay, no retry.'
 ],
 'permission_controls':{
 'producer_refs':['internal/domain/runtime_permission_windows.go:184-200','internal/domain/resources.go:45-106','internal/domain/durability.go:17-37','internal/domain/client_protocol_configuration.go:1124-1132'],
 'injection':'A new explicit SYNTHETIC residual-permission ResourceRequest and new effect key on a copied settled original Run, never alter original effects. Build ResourceRequest through existing createResourceRequest schema/put producer with category PERMISSION and unique synthetic reason. Preserve exact project/session/request/task linkage shown by actual runtime producer. If action scope/argument Artifact refs are supplied, create only fixed synthetic bytes under owned store and validate actual frozen PermissionActionScope and ref hashes. No workspace action or runtime permission waiter.',
 'causality':'Latest injected effect is CONFIRMED solely to isolate the final pending-permission predicate from effectsReconciled. This is an INJECTED residual-state guard control, NOT proof that a real permission lifecycle produced this state. The original Run/current Task/queue remain settled. Save all injection row diffs; never label it real tool execution.',
 'state_variants':'OPEN comes from createResourceRequest. ACKNOWLEDGED and RESOLVED are explicit test-only schema-valid next versions via existing put/bump semantics on the new synthetic request, not UPDATE original rows, and not real user permission actions. RESOLVED includes resolved_by original authorized principal; any required resolution evidence is explicitly synthetic. Refuse to fabricate a historic permission decision or original runtime provenance.',
 'expected':'OPEN/ACKNOWLEDGED must reach exact typed SESSION_BUSY with message session permission remains unresolved; positive same linkage and effect state with RESOLVED must COMPLETED. Earlier lease/CAS/Task/queue refusal is prerequisite failure, not target success.'},
 'nonhead_run_controls':{
 'producer_refs':['internal/domain/client_protocol_configuration.go:1021-1075','internal/domain/client_protocol_sessions.go:405-449','internal/domain/durability.go:17-37'],
 'injection':'Retain actual original Task/current active Run and their original journals/profile/effects byte-for-byte. Add one schema-valid synthetic nonhead Run belonging to that same original Task, using full original Run shape and explicit new id/time fields recorded in mutation spec. Its chronology is a synthetic test input; original task membership comes from original immutable commands. Existing settled current Run acts as later/head Run, so no need to rewrite original Task or original Run.',
 'positive':'New synthetic nonhead Run terminal/children_stopped/queue_empty/runtime_settled_at valid, matching schema-valid RUN_STATE projection and no unresolved effect; original current Run remains settled.',
 'negative_unknown':'Same synthetic terminal nonhead Run/projection as positive; append new synthetic effect key through effectAppend with UNKNOWN. Original effect rows and original ledger untouched. This models unresolved nonhead fact, not an actual provider dispatch.',
 'negative_running':'Same full synthetic nonhead Run but status RUNNING with its schema-valid corresponding RUN_STATE projection. No new runtime process. Original current head unchanged.',
 'expected':'Both negatives must typed SESSION_BUSY with earlier session run is not settled; positive COMPLETED. Record current-head clientTurnSettled=true as read-only precondition, exact nonhead facts and original membership. No custom validator replacement or production branch change.'},
 'all_case_assertions':[
 'Four negative scoped configure commands: unchanged host configuration head/history, session binding/revision/epoch, original Task/Run/profile/effects/budget, exactly one new command identity and original idempotency journal; valid private header original bytes/requestHash match. Exact replay returns same typed response without a second business mutation.',
 'Two positive commands: exactly one next immutable configuration/head and one scoped Session binding revision; original Task/Run/model/profile/effects/budget unchanged; response typed COMPLETED exact identities/ref/revision; replay does not allocate another config/head or call metadata/runtime again.',
 'Capture post-attach/pre-injection, injected/precommand, postcommand, postreplay full row multisets and schema. Permit only enumerated case injection and actual configure producer delta; no broad table whitelist. Beforefirstcase fixture/spec/compiler/source hashes, percase request/response and exact exit, final closed DB and semantic vectors all retained.'
 ],
 'batches_and_network':'Base-plan A-E selectors unchanged. C09 has no network/Node/model calls. D and existing CLI native stream tests may only run their already-fixed loopback TLS FIXTURE SDK calls; separately count actual requests, preserve process/child provenance. External provider, paid, held cases remain zero. No whole-contract known-failure rerun.',
 'full_closure':'Fresh explicit Go compiler/Go deps/embed/platform/test source closure, 38 Git blobs, source of transitive unchanged producers, schema23/SQL/API mirrors, Go module locks, actual build/test binaries, Node/Git/Python/tool lock, entire fixed SDK vendor+resolved junction inputs and known bundle. Physical overlay/mapping and exact fixtures add to beforefirstcase/after/current. Missing resource requires Root exact immutable Git-resource amendment; no generic generator or holdout execution.',
 'stop':'First unexpected failure/skip/prerequisite/ref mismatch/input drift seals actual raw and closed copied DB, stops dependent cases/batches, no automated source fix/resource export/retry. No productSourceReady until actual independent review is complete.',
 'held':['C29 ACK-final immutable trigger1811/F08','provider history5/heldpositives','Q10','historical14 ActiveRecovery','LIVE qualification','W05/A04/parent/formal'],
 'not_claimed':['real permission lifecycle execution','synthetic nonhead Run actual execution','author predecessor fullCLI PASS','current Main composition','any formal acceptance']}
save('execution_scope_supplement.json',plan)
summary=json.loads((N/'author_manifest_audit.json').read_bytes()); co=json.loads((N/'cohort_raw_audit.json').read_bytes())
review={'schema':'researchos.handler38.author-evidence-independent-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READONLY_EVIDENCE_AUDITED_EXECUTION_SCOPE_READY_PENDING_ROOT_CAS','candidate':plan['candidate'],'prior_static_review':ref(P/'review.json'),'source_acceptance':False,'formal_increment':0,
 'manifest':{'files':summary['count'],'bytes':summary['total_bytes'],'bad':len(summary['bad'])},'current_author_vector':{'files':39071,'bad':0,'qualification':'actual author captured vector byte-current; not claimed independently complete compiler closure'},'coverage_refs':{'count':125,'bad':0},'coverage_locators':{'count':len(loc),'unmatched':[x for x in loc if not x['pass_event_at_exact_locator']]},'cohorts':[{'name':x['cohort'],'test_events':x['actual_test_counts'],'top_events':x['actual_top_counts'],'exit':x['actual_invocation']['exit'],'input_before_after_equal':x['same_vector'],'changed_since_cohort':x['changed_repo_inputs_since_this_cohort']} for x in co],
 'no_aggregation':'126 core,1 TLS,282 PASS/12FAIL predecessor CLI,78 current affected CLI remain four separate cohorts. Earlier core/TLS vectors differ only in two later CLI test files, disclosed; no full current CLI claim.',
 'ACK':ack,'open':h['remaining_limits'],'failure_reports':ref(N/'failure_report_audit.json'),'execution_scope':ref(N/'execution_scope_supplement.json'),'no_product_runs_this_review':True,'static_evidence_bounds':'Whole38 static mapping remains first sealed review; new read-only producer audit and six control scope supplement do not grant product acceptance or mutate source.'}
save('review.json',review)
save('tooling_diagnostics.json',{'audit_run':{'session_id':14926,'start_chunk':'e61927','completion_chunk':'fc9b81','actual_outer_exit':0,'summary':'3332 manifest and39071current vector no mismatch;125refs no mismatch'},'read_diagnostic':{'chunk':'38a758','actual_outer_exit':0,'message':'rg included nonexistent internal/domain/effects.go; subsequent actual rg directory located durability.go. Mixed read command outer0, do not invent outer1/productfailure.','disposition':'recorded here, no new failed invocation counted'},'new_failed_invocations':[],'prior_failure':ref(P/'failure_origins.json')})
save('failure_origins.json',{'new_origins':[],'prior_preserved_origin_ref':ref(P/'failure_origins.json'),'prior_unique_origin':'tool:7a75e5','no_reimport_rule':'Root should import unique original only if absent; never count its corrected run or diagnostics as another failure.','current_product_test_invocations':0})
# All copy sources current unchanged after the read-only review.
save('producer_after_audit.json',[{'path':x['path'],'before':x['before_sha256'],'after':H((W/x['path']).read_bytes()),'unchanged':x['before_sha256']==H((W/x['path']).read_bytes())} for x in inputs])
manifest={'schema':'researchos.receipt-manifest.v1','files':[{'path':str(p.relative_to(N)).replace('\\','/'),'sha256':H(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(N.rglob('*')) if p.is_file() and p.name not in ['manifest.json','handoff.json']]}
save('manifest.json',manifest)
save('handoff.json',{'decision':review['decision'],'candidate':plan['candidate'],'review':ref(N/'review.json'),'scope':ref(N/'execution_scope_supplement.json'),'manifest':ref(N/'manifest.json'),'prior_failure':ref(P/'failure_origins.json'),'source_acceptance':False,'actual_product_execution':0,'Root_action':'Read full proposed scopes then register exact nonauthor execution lease before Go/SQL/HTTP/SDK/tests; no product edits.'})
print(json.dumps({'namespace':str(N),'review':ref(N/'review.json'),'scope':ref(N/'execution_scope_supplement.json'),'manifest':ref(N/'manifest.json'),'handoff':ref(N/'handoff.json'),'locator_unmatched':len(review['coverage_locators']['unmatched'])},ensure_ascii=True))

import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('D:/作品集/ResearchOS/research-os'); OUT=Path(__file__).resolve().parent
def now():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def write(n,v):
 with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def run(n,args):
 start=now();p=subprocess.run(args,cwd=ROOT,capture_output=True)
 for suffix,raw in [('stdout.raw',p.stdout),('stderr.raw',p.stderr)]:
  with (OUT/(n+'.'+suffix)).open('xb') as f:f.write(raw)
 write(n+'.invocation.json',{'actualargv':args,'cwd':str(ROOT),'started_at':start,'ended_at':now(),'exit':p.returncode,
  'stdout_ref':ref(OUT/(n+'.stdout.raw')),'stderr_ref':ref(OUT/(n+'.stderr.raw')),'measurement_mode':'READ_ONLY_PUBLIC_SOURCE'})
 assert p.returncode==0
 return p.stdout
before=json.loads((OUT/'source.before.json').read_bytes());base={r['path']:r for r in before['inputs'] if r['origin']=='MAIN'}
historical='execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_executor_codex/implementation-1cc1b20e27534da8a78e7350fa533ea3/run-238574514fa345f89e5468d9c9be5237/'
run('historical-original-invocation',['git','show','fef0ee2d56351e74ceed11b0b37d3f87e9c83494:'+historical+'invocation.json'])
run('composition-model-validator',['git','show','c571781e9703bc7a96fa63629e0cc3bee7f3deec:internal/domain/runtime_model_stream.go'])
def scope(path,behavior):
 existing=(ROOT/path).exists()
 return {'path':path,'expected_absent':not existing,'before_sha256':sha((ROOT/path).read_bytes()) if existing else None,
 'change_boundary':behavior,'future_owner':'ROOT_TO_ASSIGN_EXCLUSIVE_F08_EXECUTOR','authorization':'PROPOSAL_ONLY_NOT_REGISTERED'}
core=[
scope('migrations/sqlite/0024_client_cancel_finalization.sql','NEW additive migration after unchanged 0023; replace installed idempotency_immutable only with fail-closed once-only CANCEL finalization guard; add control-row identity/original/final monotonic and delete/replace protection. No schema22/23 edits or generic replay update allowance.'),
scope('internal/domain/client_protocol.go','Only existing Execute ACK replay finalization branch: common validation, compare-and-swap original ACK bytes/hash, require RowsAffected=1, validate canonical response then original-row update within same caller transaction; finalized replay reads original idempotency row.'),
scope('internal/domain/client_protocol_queue_control.go','Only cancelClientTarget/finalizeClientCancel: retain Run/Goal/task membership, stopped/queue/effect checks; freeze task/run/generation/epoch settlement anchors and witness in same transaction as CONFIRMED/final_response/original journal CAS; no new Run, provider request or budget write.'),
scope('internal/domain/client_cancel_finalization.go','NEW private canonical F08 validator and append-only CANCEL_FINALIZATION witness helpers over existing control receipts; reused by live finalization and backup. No public opaque REPORT authority.'),
scope('internal/domain/client_cancel_finalization_test.go','NEW real modernc SQLite trigger, canonical Execute, concurrency/restart/rollback, forged witness and identity negative controls on exact schema24 and original22/23 controls.'),
scope('internal/domain/backup_command_queue.go','Add F08 semantic closure validation without weakening original queue/source/model-stream validators. Bind historic Run by immutable Run/task/generation evidence rather than only current Task.active_run_id; preserve exact legacy legal immediate COMPLETED cases.'),
scope('internal/domain/backup_cancel_finalization_test.go','NEW full backup/restore/inventory round trips for pending ACK/UNKNOWN, terminal witness/final, historic Run followed by a new Run, corruption and failed restore publication.'),
scope('internal/domain/client_protocol_control_windows_test.go','Add actual SDK clear+abort+idle and typed command replay controls to existing Windows tests; preserve every original assertion. New fixture network is loopback-only, no paid model.')]
gates=[
scope('internal/domain/backup_upgrade.go','Only dispatch explicit new exact22->23 and exact23->24 named plans to dedicated helpers; old13/14/20 and21->22 branches/hash thresholds remain byte-protected outside hook.'),
scope('internal/domain/backup_configuration_upgrade.go','NEW exact22->23 matching-source release/schema/SQL hashes, populated-source exclusive backup and isolated migration; three typed foundation tables and no invented qualification.'),
scope('internal/domain/backup_configuration_upgrade_test.go','NEW actual old/new program, host-only populated, source drift, workspace, active writer, crash/rollback and three-table closed-snapshot tests for22->23.'),
scope('internal/domain/backup_cancel_upgrade.go','NEW exact23->24 plan, installed old/new trigger hashes and verified legacy controls; no new business rows during migration; preserve every original journal/body/history and typed three-table foundation inventory.'),
scope('internal/domain/backup_cancel_upgrade_test.go','NEW actual23->24 staged upgrade and exact22->23->24 sequence, wrong source/SQL/trigger refusal, crash rollback, no live source mutation and old-writer exclusion.'),
scope('internal/domain/backup_migration.go','Strengthen CheckMigrationSafety populated-authority detection beyond domain_objects count: existing idempotency, auth/session/queue and schema23 configuration/identity tables require matching-source staged backup; no environment bypass.'),
scope('internal/domain/backup.go','Narrow backupInventory/backupIntegrityPolicy hooks for typed configuration three-table digest/validation plus complete command original/final journal binding; retain current queue/model and protected-data policy.'),
scope('internal/domain/backup_host_configuration.go','NEW schema-aware three-table typed inventory/restore validation, including global command identity original idempotency join, full configuration projection/head/FK/CAS and owner binding. No Vault access.'),
scope('internal/domain/backup_host_configuration_test.go','NEW nonempty identity/config/head normal, orphan/hash/foreign-owner/ambiguous legacy/forged-verified negative controls and host-only backup/restore.'),
scope('internal/domain/store.go','Narrow constructor forward-schema and release compatibility guard before any migration/write; keep exact existing schemas/additive paths. This cannot retrofit an already-built old binary; old-source OS exclusive lock and serial cutover remain required.')]
proposal={
 'schema':'researchos.w05.cancel-finalization-scope-proposal.v1','status':'PROPOSED_REQUIRES_INDEPENDENT_SCOPE_REVIEW_AND_ROOT_REGISTRATION',
 'author_id':'codex:/root/sources_parent_impl','scope_reviewer':'ROOT_TO_ASSIGN_DISTINCT_NON_IMPLEMENTER',
 'source_acceptance_reviewer':'ROOT_TO_ASSIGN_DISTINCT_FROM_F08_EXECUTOR','root_role':'SERIAL_SCOPE_REGISTRATION_AND_LATER_INTEGRATION_ONLY',
 'observed_main_head':before['observed_head'],'observed_checkpoint_revision':json.loads((ROOT/'execution/v2.4/checkpoint.json').read_bytes())['revision'],
 'input_closure_ref':ref(OUT/'source.before.json'),'historical_issue_ref':ref(OUT/'foundation-blob-4.stdout.raw'),
 'historical_result_ref':ref(OUT/'foundation-blob-5.stdout.raw'),'historical_raw_ref':ref(OUT/'foundation-blob-6.stdout.raw'),
 'historical_invocation_ref':ref(OUT/'historical-original-invocation.stdout.raw'),
 'foundation_independent_review_ref':ref(ROOT/'execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644/source_review.json'),
 'facts':[
  {'source':'internal/domain/client_protocol.go:726-747','fact':'Execute parses original ACK and calls finalizeClientCancel, then UPDATEs idempotency.body. Existing 0002 trigger unconditionally aborts that UPDATE.'},
  {'source':'foundation-blob-4.stdout.raw + foundation-blob-6.stdout.raw','fact':'Historical actual modernc UPDATE body=body rejected with immutable replay1811 on schemas22 and23. That test passed by asserting refusal; it did not execute an end-to-end successful CANCEL finalization. This task did not rerun it or add a product failure.'},
  {'source':'internal/domain/client_protocol_queue_control.go:finalizeClientCancel','fact':'Current control row carries original_response/final_response and CONFIRMED state. Confirmation and journal replacement share a caller transaction, so old trigger failure must roll back intermediate writes.'},
  {'source':'isolated fef0ee2 internal/domain/client_command_identity.go','fact':'L04 intentionally keeps original idempotency row as sole response authority; identity rows only locate it. Returning mutable control.final_response as a second journal would contradict this reviewed boundary.'},
  {'source':'internal/domain/backup_command_queue.go','fact':'Backup covers four queue tables and row hashes, but currently only checks original response nonnull, confirmed final nonnull and original request locator. It does not fully prove ACK/final typed identity or finality causality.'},
  {'source':'internal/domain/backup_migration.go','fact':'Current startup migration safety returns early when domain_objects is absent or empty. Host-only auth/idempotency/configuration authority cannot be assumed empty based on that count.'},
  {'source':'internal/domain/backup_queue_upgrade.go:upgradeQueueRelease','fact':'Existing public named queue upgrade is exact21->22; source/target count only21 or22. Widening this hardpin would weaken historical release proof. No current22->23 or23->24 plan exists.'},
  {'source':'internal/domain/store.go:New','fact':'New scans source migration files and applied versions, but has no explicit future-schema refusal. New guard helps future binaries, not already-built old binaries.'}],
 'recommended_design':{
  'decision':'Additive schema24 narrowly permits one canonical CANCEL ACK->COMPLETED transition in the original idempotency row; preserve0002/0022/isolated0023 bytes. Root must reserve actual next version after independent review; do not ship24 ahead of23 integration gates.',
  'minimality':'Core8 paths repair response authority and required backup semantics. Separate gate10 paths are explicit prerequisite/integration scope, not implicit permission to broaden core. Existing foundation5 remains unchanged. New migration uses no new table and no public schema change.',
  'rejected_shortcuts':['Drop/disable immutable trigger globally or edit0002/0022/0023','Return mutable final_response as alternative authority','Treat worker flag, REPORT, process exit, SDK idle alone or current bools as settlement','Rewrite historical ACKs during migration','Widen21->22 release count/hash acceptance','Automatically reconcile UNKNOWN, retry provider or release reserved model cost'],
  'control_witness':[
   'Reuse append-only client_control_receipts with new private kind CANCEL_FINALIZATION. Each involved existing queue generation gets one command-bound witness with explicit principal/project/session/command/request_hash/control_request_id/target/task, original ACK digest, exact final response bytes and digest, original Run ID/epoch/dispatch identity and terminal proof anchors. No fake generation for an unprovable historical control.',
   'For Goal-wide cancellation freeze and validate complete task membership, including each task generation; one settled task cannot stand in for another. For legitimate never-dispatched task prove zero Run/dispatch and terminal/drop queue facts without inventing Run.',
   'Each witness uses a deterministic or otherwise uniquely constrained identity for this command+task+generation. previous_receipt_id is NULL for this independent per-command root; do not abuse NULL SQL equality or point it at a different queue command. Full receipt body links to prior immutable runtime/queue witnesses are independently checked.',
   'Body/hash and every anchor must be validated by trusted host common helper, never accepted from public client JSON. New receipt kind requires strict backup validator; preserve model-stream validator in composed source. No ownership of runtime_model_stream.go granted.',
   'All witness INSERTs, state/final_response changes, typed snapshot validation and original idempotency CAS commit together. Failure at any point leaves original ACK and pending state with no witness, queue advancement, duplicated event, budget or partial publication.',
   'Historical completed replay validates frozen final bytes and original terminal anchors. Later legal attempts must not retroactively invalidate finality by consulting only current Task.active_run_id/current queue generation. Restore-current fencing remains independent and must never authorize new work.' ],
  'sql_guards':[
   'The only allowed UPDATE changes body from valid exact ACK to valid exact COMPLETED. Null-safe comparisons preserve principal/project/operation/key/request_hash/status/headers/created_at; operation must equal v2:session.control. All other updates, including body=body, remain refused.',
   'Original body byte-equals immutable retained original_response; new body byte-equals one-time final_response. Both share protocol/method/command/session and exact CANCEL target/control_request_id; completed fields settled/children_stopped/queue_empty are true. Missing/null/malformed values fail closed, no SQL three-valued WHEN bypass.',
   'Require control REQUESTED->CONFIRMED and complete command-bound immutable witnesses matching every frozen task/generation and final bytes. Canonical Run terminal status, cancellation confirmation, queue sealing/drop/consume and latest-effect reconciliation must be checked; state label/final_response match alone cannot authorize.',
   'Add control identity/task_ids/request_hash/original_response write-once protection, final_response single assignment, terminal no-backwards/no-delete/no-replace rules in new24; retain legitimate same-transaction immediate-completion initialization and restore REQUESTED->RECONCILING.',
   'No UPDATE after finalization is permitted, even same final body. Exact replay reads the original stored row; changed same-command request conflicts before mutation. Existing global identity FK remains valid because every locator/hash field is unchanged.',
   'Raw-SQL negative controls forging only control CONFIRMED/final_response, missing witness, wrong Run/generation/epoch, UNKNOWN effect or incomplete queue must still refuse transition. If full constraints cannot be enforced within core8, stop and submit explicit amendment instead of relaxing the gate.' ],
  'runtime_and_money':[
   'Actual CANCEL request fences only target Run/Goal tasks, preserves accepted content, queues, failure counters and original resource keys; durable ACK is pending, not completion.',
   'Existing SDK clear/drop+abort-observed+idle and same-generation Run/epoch settlement remain required. UNKNOWN external effect or missing trusted process evidence blocks final; original ACK/RECONCILING stays queryable, no MODEL retry or public MESSAGE END is invented.',
   'Canonical terminal FAILED/SETTLED races may produce a settled cancellation response only when actual existing runtime proof, children/queue/effects meet original rules; do not rewrite a legitimate terminal Run to CANCELLED merely to satisfy client reply.',
   'CANCEL result finalization has zero direct BudgetLedgerEntry writes. Actual existing resource/qualification settlement paths own releases and late cost accounting, with their stable keys. Repeat ACK/final replay, concurrency/restart and rollback must leave budget hashes/counts stable; UPPER_BOUND never becomes ACTUAL.' ]},
 'proposed_core_source_scope':core,'proposed_migration_backup_prerequisite_scope':gates,
 'protected_paths':['migrations/sqlite/0002_domain.sql','migrations/sqlite/0022_client_command_queue.sql','migrations/sqlite/0023_host_model_configuration.sql','internal/domain/client_command_identity.go','internal/domain/client_configuration.go','internal/domain/backup_queue_upgrade.go','internal/domain/runtime.go','internal/domain/durability.go','all SDK/worker/provider/schema contracts/locks','all canonical execution metadata','all unknown-origin deleted resources and historical raw/ZIP'],
 'migration_and_rollback_gates':[
  {'id':'M01','required':'Keep isolated fef0ee2 SOURCE_READY_MAIN_HOLD. Independently qualify public exact22->23 before adding24 to MAIN. Source22 program/root and target23 program/root must match frozen SQL/contracts; do not execute migration on real user DB during source tests.'},
  {'id':'M02','required':'Real public synthetic populated source22 includes sessions, original ACK journal, queue, outbox/domain history, resource/budget rows and host-only authority with zero domain_objects. Matching source backup and exclusive source lock mandatory; CheckMigrationSafety refuses direct startup migration of any nonempty authority.'},
  {'id':'M03','required':'For22->23 add exactly foundation three tables/index/triggers, preserve all old rows/schema protections; typed backup inventory binds identities/configurations/heads and original receipt/FK/full config scope. Nonempty config/head correctness must be exercised after valid config commit; configured never means provider usable.'},
  {'id':'M04','required':'For23->24 verify exact source23 schema/hash, new24 hash and exact installed trigger set. Migration changes schema only, not ACK body, control state/final bytes, identity/config rows, budget, receipts or old history. Invalid legacy combinations refuse instead of repair.'},
  {'id':'M05','required':'Snapshot encrypted/authenticated by existing public backup flow using synthetic test key; test fixed current queue inventory plus terminal witness and original ACK/final journal digest. Keep source closed snapshot/current source before-after equality; no copying Vault/DPAPI/private store or protected payload.'},
  {'id':'M06','required':'Staged restore uses existing path/alias/overlap and workspace OS identity checks. UNKNOWN queues/effects remain fenced, credentials restored under existing revoke rules, no provider/tool dispatch and no fake replay completion. Verify complete typed three-table state and F08 state before publication.'},
  {'id':'M07','required':'Exercise actual matching-source old writer during source lock (must be refused/busy); candidate and original cannot be concurrent authorities. Old already-built22 binary cannot be retrofitted: keep it stopped and original protected through independent single-writer cutover. New source explicitly refuses unsupported future schema before writes.'},
  {'id':'M08','required':'Crash/cancel/injected errors at backup, SQL24 trigger replacement, final journal CAS and prepublication; rollback restores caller transaction or discards candidate without touching original. Do not down-migrate active24 in place. Return to frozen23/22 snapshot only after candidate stopped and independent no-new-effects reconciliation; post-cutover effects prevent blind rollback.'},
  {'id':'M09','required':'Original21->22/13->14/13->20 tests remain pinned to their actual matching historical source and unchanged assertions. Old hardpin22 FAIL remains historical; do not increase counts or label it closed because a new23 plan exists.'}],
 'test_gates':[
  {'id':'F08-T01','test':'Real original22/23 trigger installed SQL and UPDATE body=body still rejects; capture SQL24 installed guard and exact schema migrations. Original historical test evidence is not rerun/failure-counted in this proposal.'},
  {'id':'F08-T02','test':'Actual typed Execute CANCEL->ACK, trusted SDK/runtime settlement ->same exact envelope replay COMPLETED, restart ->byte-exact final replay. Original ACK retained, original journal only response authority; one witness/task; no extra events/effects/budget.'},
  {'id':'F08-T03','test':'Deterministic concurrent replay and failure after witness/before CAS/before commit: all-or-nothing, one transition, no partial state or double billing. Changed request/principal/project/session/target/epoch and malformed full envelope refuse.'},
  {'id':'F08-T04','test':'UNKNOWN/latest STARTED effect; queue UNKNOWN/SDK_ACCEPTED/missing drop; only idle/only abort; stale dispatch/epoch; restore-fenced queues; forged REPORT/CONFIRMED/witness all cannot finalize. Original pending remains; no END.'},
  {'id':'F08-T05','test':'No-run immediate completion, all-tasks Goal cancellation, already-terminal race and later new Task attempt preserve frozen final and original history. Do not fabricate missing Run/generation to fit witness.'},
  {'id':'F08-T06','test':'Backup/restore terminal and pending, same command replay after restart/restore; typed witness/body/hash/request locator corruption and deletion fail. Three L04 tables, original journal, protected artifact policy and model-stream validators remain enforced.'},
  {'id':'F08-T07','test':'Actual compiled Windows CLI with loopback SDK causal fixture reads pending then settlement-derived final; raw JSONL/SQLite closed snapshot, both cancel-signal orderings, late ACK and no model cost request. Preserve full CLI and L02/Doctor/L01 contracts.'},
  {'id':'F08-T08','test':'Exact22->23->24 public matching-source upgrade, real old-writer process exclusion, host-only nonempty refusal, failure rollback and original byte-history equality. Full relevant queue/backup/domain suites and Windows actual SDK controls with zero skip.'}],
 'future_test_argv_templates':[
 ['<PINNED_GO>','test','-count=1','-json','./internal/domain','-run','Test(ClientCancelFinalization|BackupCancelFinalization|ClientCancelChangesCanonicalRun|ClientQueueGoalCancelBeforeRun)'],
 ['<PINNED_GO>','test','-count=1','-json','./internal/domain','-run','Test(BackupHostConfiguration|ConfigurationUpgrade|CancelUpgrade|BackupQueue|ClientCommandIdentity|ClientConfiguration)'],
 ['<PINNED_GO>','test','-count=1','-json','./apps/cli']],
 'formal_boundary':'All planned tests are future FIXTURE/LOOPBACK qualification with actual SDK/SQLite/CLI; no paid provider or formal W05/A04 acceptance. Root must register owners and exact paths only after independent scope approval; separate source reviewer checks composed source then Root integration; existing failures and new failure origins preserved.',
 'state_changes_this_task':0,'paid_calls':0,'credential_or_private_database_reads':0,'resource_restorations':0,
 'open_decisions':['Independent approval of additive24 one-transition trigger semantics and private CANCEL_FINALIZATION witness schema.','Root assignment/reservation of exact8 core and exact10 migration/backup gate paths without overlapping concurrent owners.','Refresh exact baseline after pending T08/L02/provider integrations; do not transplant this4ba source vector as current implementation.'],
}
write('source_proposal.json',proposal)
after=[];drift=[]
for row in before['inputs']:
 path=(ROOT/row['path']) if row['origin']=='MAIN' else Path(row['path'])
 actual=sha(path.read_bytes()) if path.exists() else None
 after.append({'origin':row['origin'],'path':row['path'],'sha256':actual})
 if actual!=row['sha256']:drift.append({'path':row['path'],'before':row['sha256'],'after':actual})
head_after=run('head.after',['git','rev-parse','HEAD']).decode().strip()
run('status.after',['git','status','--porcelain=v1','--untracked-files=no'])
write('source.after.json',{'head':head_after,'inputs':after,'drift':drift,'head_changed':head_after!=before['observed_head']})
write('audit.json',{'mode':'READ_ONLY_PUBLIC_ARCHITECTURE','product_tests_executed':0,'new_product_failure_count':0,
 'historical_trigger_error':'immutable replay (1811), preserved historical expected-refusal test, not fresh failure or end-to-end finalization proof',
 'source_drift':drift,'public_input_count':len(before['inputs']),'source_modified':False,'schema_modified':False,
 'canonical_metadata_modified_by_reviewer':False,'unknown_deleted_paths_restored':False,
 'discovery_diagnostics':[{'label':'rg literal Windows wildcard path','actual_exit':1,'count':3,'product_failure':False,'resolution':'Use directory with -g patterns; corrected read commands recorded.'},
 {'label':'guessed nonexistent 23_CLIENT_INTERACTION_PROTOCOL.md','rg_exit':2,'outer_shell_exit':0,'product_failure':False,'resolution':'rg --files resolved frozen22_CLIENT_INTERFACE_DETAILS.md, captured bytes and actual source lines.'}],
 'candidate_source_acceptance':False,'formal_acceptance':False})
write('handoff.json',{'status':'PROPOSED_PENDING_INDEPENDENT_SCOPE_REVIEW','source_proposal_ref':ref(OUT/'source_proposal.json'),
 'audit_ref':ref(OUT/'audit.json'),'source_before_ref':ref(OUT/'source.before.json'),'source_after_ref':ref(OUT/'source.after.json'),
 'core_paths':len(core),'mandatory_gate_paths':len(gates),'source_drift_count':len(drift),'product_tests_run':0,'new_product_failures':0,
 'required_next':'Independent architecture/scope review then Root exact ownership registration. No implementation authorized by this receipt.',
 'acceptance_delta':0})
write('manifest.json',{'files':[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file()]})
print(json.dumps({'proposal':ref(OUT/'source_proposal.json'),'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'drift':drift,'core':len(core),'gates':len(gates)},ensure_ascii=False))

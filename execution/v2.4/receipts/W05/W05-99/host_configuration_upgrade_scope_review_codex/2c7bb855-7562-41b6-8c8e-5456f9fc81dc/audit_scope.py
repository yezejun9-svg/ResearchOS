import pathlib, subprocess, hashlib, json, datetime, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path.cwd(); OUT=ROOT/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_scope_review_codex/2c7bb855-7562-41b6-8c8e-5456f9fc81dc'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(name,value):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return ref(p)
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
inv=[]
def git(*args):
 p=subprocess.run(['git','--no-replace-objects',*args],cwd=ROOT,capture_output=True);n=len(inv);(OUT/f'git-{n}.stdout.raw').write_bytes(p.stdout);(OUT/f'git-{n}.stderr.raw').write_bytes(p.stderr);inv.append({'argv':['git','--no-replace-objects',*args],'exit_code':p.returncode,'stdout':ref(OUT/f'git-{n}.stdout.raw'),'stderr':ref(OUT/f'git-{n}.stderr.raw')});p.check_returncode();return p.stdout
head=git('rev-parse','HEAD').decode().strip();assert head=='396287cc5427eb125aaedb8a2b7fadf63e6b9322'
proposal=ROOT/'execution/v2.4/receipts/W05/W05-99/cancel_finalization_scope_readonly_codex/4e3160d75a2a444cb048798da12f567a/source_proposal.json';assert sha(proposal.read_bytes())=='96aa7504b6e9370ea7824fe7da7089bc4f74643f11afe2a412a21ce9309588ef'
paths=['AGENTS.md','internal/domain/store.go','internal/domain/backup.go','internal/domain/backup_upgrade.go','internal/domain/backup_queue_upgrade.go','internal/domain/backup_migration.go','internal/domain/backup_command_queue.go','internal/domain/backup_recovery.go','internal/domain/client_session_fence.go','internal/domain/runtime_model_stream.go','internal/domain/client_protocol.go','internal/domain/client_protocol_queue_control.go','internal/store/sqlite.go','internal/host/host.go','internal/host/bootstrap.go','spec/v2.0/contracts/domain.schema.json','spec/v2.0/contracts/openapi.json']
paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'migrations/sqlite').glob('*.sql'))]
paths += [proposal.relative_to(ROOT).as_posix()]
inputs=[]
for rel in paths:
 p=ROOT/rel;b=p.read_bytes();s=OUT/'readraw'/rel;s.parent.mkdir(parents=True,exist_ok=True);s.write_bytes(b);inputs.append({'source':ref(p),'snapshot':ref(s)})
foundation='fef0ee2d56351e74ceed11b0b37d3f87e9c83494'
fpaths=['migrations/sqlite/0023_host_model_configuration.sql','internal/domain/client_configuration.go','internal/domain/client_configuration_test.go','internal/domain/client_command_identity.go','internal/domain/client_command_identity_test.go']
blobs=[]
for rel in fpaths:
 b=git('show',foundation+':'+rel);p=OUT/'foundation_gitblobs'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);blobs.append({'commit':foundation,'path':rel,'sha256':sha(b),'snapshot':ref(p)})
existing=['backup_upgrade.go','backup_migration.go','backup.go','store.go'];new=['backup_configuration_upgrade.go','backup_configuration_upgrade_test.go','backup_host_configuration.go','backup_host_configuration_test.go']
assert all(not (ROOT/'internal/domain'/n).exists() for n in new)
write('source.before.json',inputs)
write('foundation_blobs.json',blobs)
review={'schema':'researchos.w05.host-configuration-upgrade-scope-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'SOURCE_SCOPE_READY_SCHEMA23_PREREQUISITES_ONLY','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_head':head,'proposal':ref(proposal),'foundation_commit':foundation,'foundation_source_count':5,'scope_count':8,'exact_existing_paths':['internal/domain/'+x for x in existing],'exact_new_paths':['internal/domain/'+x for x in new],'implementation_authorization':'Root must register exact8 and isolated owner before implementation; this is independent scope advice, not source qualification or product acceptance.',
'callgraph':[
'host.New -> domain.NewCurrentMu -> domain.New -> CheckMigrationSafety -> numbered migrations -> next_v24_sessions.sql -> installClientSessionFence -> commit. Host vault and hostState opening occur after domain.New returns.',
'UpgradeLocal -> upgradeLocal has exact queue21to22 dispatch followed by historical13to14/20 switch. Add only separate configuration22to23 dispatch; preserve all historical paths.',
'createBackupPolicy -> integrity + backupInventory; restoreBackupPolicy -> authenticated manifest/migration/schema checks -> integrity -> inventory equality -> workspace handling -> beforeRecovery -> relocate -> backupFence -> Migration -> integrity -> afterRecovery -> inventory -> close -> rename.',
'backupFence preserves original evidence, revokes auth credentials, fences sessions/queues/Run epochs and unfinished effects UNKNOWN. Configuration history and global original response journal must not be rewritten by configuration validation.' ],
'exact_bounds':{
'backup_upgrade.go':'One exact new 22-to23 plan dispatch/constant linkage. Historical release hashes, 13/14/20 and queue21to22 exterior preserved.',
'backup_configuration_upgrade.go':'New independently pinned release reader/template/migration/public UpgradeLocal implementation for exactly22to23; source+target program and SQL/additive/schema verification, exclusive source, authenticated retained prebackup, isolated target, complete row invariants and rollback. No generic count relaxation or protected/auth opaque whitelist.',
'backup_configuration_upgrade_test.go':'All new upgrade, startup, historical dispatch protection and real Windows old-writer tests here; no editing old hardpin tests.',
'backup_migration.go':'Remove domain_objects-only empty shortcut; count all existing authority tables safely; reject unapplied numbered/additive changes for populated authority, malformed/gapped/future inventories fail closed. Fresh truly empty baseline remains supported.',
'backup.go':'Wire schema-aware three-table inventory/digest and semantic validator at create and restore integrity points. May add distinct exact configuration-plan workspace-preservation callback/guard; existing queue plan unchanged. No general bypass of protected/history or restoration fences.',
'backup_host_configuration.go':'Read-only schema-aware inventory/validation of all3typedtables and original idempotency/auth graph, including historical records and all principal-command identities. No public authority, vault reads, status/model qualification or mutation.',
'backup_host_configuration_test.go':'Public CreateBackup/RestoreBackup plus tamper, cross-principal/global-journal, history/head and fixture-only SQL23 tests; tests may call private foundation helpers but identify them as storage fixtures.',
'store.go':'Early supported numbered-version/schema inventory guard before its migrations/additive/fence DDL; no SQL23 auto-migration for nonempty old host authority; do not alter existing contracts.'},
'mandatory_completion_gates':[
'G01 Exact matching22 source and23 target releases: immutable1..22 SQL, exact foundation23 hash, additive+runtime-installed session fence schema, contracts and actual source/target program bytes fixed before/after; test wrong count/hash/root/binary/schema and concurrent drift refusal.',
'G02 Numbered-only22 missing client_sessions is not a valid matched current22 source: reject before snapshot/restore publication. Do not fix source DB in place or silently skip queue validation. Existing validateBackupQueue JOINs client_sessions even when queue empty. Supporting another source shape needs separate explicit design review.',
'G03 Host-only population with zero domain_objects: auth_principals/auth_credentials, idempotency, sessions, queue, runtime/opaque/history rows and each typed23 table each prevent in-place numbered upgrade. Missing tables checked via sqlite_master, not blindly queried. Unknown/malformed future migration versions reject before domain DDL.',
'G04 Preserve all3typedtables full columns, values, ordering-independent complete digest; absent allowed only for supported pre23 schema;23 missing/partial/unexpected schema fails. Validate every config canonical payload/scope/hash/owner/ref/revision/time against frozen schemas and original response, not just head.',
'G05 Per owner+principal history revisions contiguous from1, unique exact head at latest record, no orphan history/head or foreign ownership. Foundation allows default-only null session/project/CAS/epoch scope; no fabricated settled-session adoption or relabeling during restore.',
'G06 Every principal+command identity must join exactly one ORIGINAL idempotency row across the entire v2 method/project namespace; protocol/method/operation/project/request hash/body typed response identity/result exact. Reject shadow legacy duplicates, missing receipt, invalid principal, forged config projection. Identity row never substitutes response authority.',
'G07 Public backup and restore valid populated23, head+history+nonconfiguration command rows; tampered payload/hash/head/history/auth/journal/shadow duplicate/partial schema refusal. Portable restore retains credential references as historical unqualified metadata and revokes live sessions; never claims referenced vault credential exists or rebinds owner to destination.',
'G08 Public22to23 isolated upgrade with active Run/queue/workspace typed operational rows preserved under existing recovery rules; UNKNOWN effects stay same identity/no redispatch, original response immutable, new config3tables empty on migration; authenticated source snapshot retained. Inject faults at migration, semantic validation and prepublication; no active target published, source authority unchanged.',
'G09 Actual compiled Windows old reader/writer contender denied while upgrade holds source SQLite exclusive lock through target publication. After closing that lock old program can reopen original: require explicit single-writer cutover, do not claim permanent retroactive oldbinary fence. Newprogram rejects future schema before domain writes.',
'G10 Existing13to14/13to20/21to22 hash/guard and all prior protected historical rows unchanged. Run focused old dispatch/guard tests with honest original historical fixtures; retain hardpin22 failures as unresolved until separately authorized test scope, never weaken assertions.',
'G11 Original immutable idempotency UPDATE trigger and1811 refusal stay. No schema24 file/trigger/witness, no control.final_response bypass; no F08 ACK-tofinal gate closed.',
'G12 Fresh actual Go compiled dependency/source/tool input vectors before/after, original raw all failures retained. Independent final source review before MAIN integration; foundation alone remains MAIN HOLD until all preceding gates pass.' ],
'limits':[
'Exact8 sufficient for domain startup before business/migration DDL, public schema23 backup/upgrade and storage semantics; not API/runtime/CLI host.configure completion.',
'internal/store.Open already selects WAL and Bootstrap callers may touch bootstrap metadata before domain.New. These8 paths cannot promise zero filesystem/header/WAL writes on future-schema open. If that stronger boundary is required, separately register internal/store/sqlite.go and actual startup bootstrap callers after concrete callgraph scope; do not silently claim it.',
'No edit backup_queue_upgrade.go, backup_recovery.go, backup_command_queue.go, foundation5, any numbered SQL22/23, contracts, SDK, runtime provider or CLI. Protected unowned hook failure must be reported for new scope rather than bypassed.',
'Source22 additive/full session schema and model-stream restore validation are inherited, not replaced by migration23. Existing UNKNOWN/partial streams need not become finalized to back up.',
'Host binding references are not proof of present credential, runtime qualification, samehost portability or remote provider access. All qualification remains separate.',
'SQL24 reservation grants no creation or implementation. W05/A04/parent/formal/current LIVE increment0.' ],
'new_product_failures':[],'execution':'READ_ONLY_SOURCE_AND_GIT_BLOB_AUDIT_NO_PRODUCT_TESTS_NO_DB_NO_NETWORK','tooling_diagnostics':['Earlier exploratory guesses for foundation SQL basename and nonexistent backup files/apps/host failed; corrected by actual file/Git discovery. No product execution or failure inferred.']}
write('review.json',review)
after=[]
for x in inputs:
 p=ROOT/x['source']['path'];a=ref(p);assert a==x['source'];after.append(a)
write('source.after.json',after)
write('invocations.json',inv)
write('audit.json',{'all_read_inputs_unchanged':True,'read_input_count':len(inputs),'foundation_git_blobs':5,'all_git_exit0':all(x['exit_code']==0 for x in inv),'read_only_public_sources':True,'no_product_execution':True,'scope8_foundation5_separate':True})
manifest=write('manifest.json',[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')])
h=write('handoff.json',{'decision':review['decision'],'review':ref(OUT/'review.json'),'manifest':manifest,'audit':ref(OUT/'audit.json'),'scope_only':True,'parent_formal_increment':0})
print(json.dumps({'review':ref(OUT/'review.json'),'handoff':h,'manifest':manifest,'inputs':len(inputs)},ensure_ascii=False))

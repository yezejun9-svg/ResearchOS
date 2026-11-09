from pathlib import Path
import json,hashlib,datetime
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';N=Path(__file__).parent;P=B/'cancel_finalization_v5_type_boundary_clarification_codex/fd227767c4d34e4aa243faa96b45d3cb';V=B/'review_f08_v5_type_boundary_codex/6379a72a595747ddb796fe6b508afd2e'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,x):
 with (N/p).open('x',encoding='utf-8') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
refs=[]
def capture(p,dest):
 raw=p.read_bytes();q=N/'snapshots'/dest;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw);refs.append({'path':str(p),'sha256':sha(raw),'bytes':len(raw),'snapshot':q.relative_to(N).as_posix()})
for p in P.rglob('*'):
 if p.is_file():capture(p,Path('author-fd227')/p.relative_to(P))
for p in V.iterdir():
 if p.is_file():capture(p,Path('review')/p.name)
scope=json.loads((P/'scope_revision.json').read_text(encoding='utf-8'));paths={x['path'] for x in scope['scope']};paths.update(['internal/domain/store.go','internal/domain/client_session_fence.go','internal/store/sqlite.go','migrations/sqlite/next_v24_sessions.sql','execution/project_identity.json','AGENTS.md']);missing=[]
for p in sorted(paths):
 if (R/p).is_file():capture(R/p,Path('current')/p)
 else:missing.append({'path':p,'status':'ABSENT_NEW_RESERVED_SOURCE_NO_FILE_CREATED'})
for p in sorted((R/'migrations/sqlite').glob('[0-9][0-9][0-9][0-9]_*.sql')):
 if str(p) not in {x['path'] for x in refs}:capture(p,Path('current')/p.relative_to(R))
put('inputs.before.json',refs);put('reserved_absent_paths.json',missing)
for p,h in [(P/'scope_revision.json','6d4f2f97a70f6dc0bfb6a22a81347d76e7549e1bffe89bdebbd615c2a9254c34'),(P/'candidate.sql.txt','e3d58e53a76d00cfecb5cf139320f09055c0996c88616e288a49cfdd2ca07736'),(V/'review.v2.json','40e9a93dfa4b78fe752b3140693ae616d8ffa2fdfc8342c64c113a9b37087630')]:
 if sha(p.read_bytes())!=h:raise RuntimeError('AUTHORITY_HASH_MISMATCH '+str(p))
# Preserve every original scope entry in an embedded original list. Additive responsibilities, not a rewrite of old bounds.
complete=[dict(x,ordinal=i+1) for i,x in enumerate(scope['scope'])]
complete.append({'ordinal':21,'path':'internal/domain/store.go','new':False,'bounds':'New only: same-Tx preexisting24 fingerprint before numbered/additive DDL; post-fence full schema24 gate immediately before existing Commit. Necessary imports only; all NewCurrentMu policy and other store functions unchanged.','authorized_to_edit_now':False})
put('complete_scope21.json',{'status':'PROPOSED_NOT_IMPLEMENTATION_LEASE','original20_unchanged':scope['scope'],'complete21':complete,'additional_responsibilities_within_original20':[{'path':'internal/domain/client_cancel_finalization.go','functions':['checkClientCancelStartupBeforeDDL(ctx context.Context,tx *sql.Tx) error','validateClientCancelStartup(ctx context.Context,tx *sql.Tx) error'],'bounds':'Private same caller-Tx read-only validators. Exact schema-version branch; deterministic trusted expected-schema inventory; guarded full34 reader; original/history-aware inventory validation shared with backup. No own Begin/Commit, DDL repair, journal/business writes, witness creation, UDF modes or source categories.'}],'wrong_path_excluded':'internal/store/sqlite.go remains byte-protected; Open/WAL/Ready/Bootstrap are not domain.New caller; no DSN/PRAGMA defaults changed.'})
(N/'store.New.proposed-diff.txt').write_text('''DESIGN ONLY. Not applied or compiled. Exact function internal/domain/store.go:New.
A: immediately after existing defer tx.Rollback(), before for _, file := range files:
    if e = checkClientCancelStartupBeforeDDL(context.Background(), tx); e != nil {
        return nil, e
    }
B: after successful installClientSessionFence(context.Background(), tx, false)
   and immediately BEFORE existing tx.Commit():
    if e = validateClientCancelStartup(context.Background(), tx); e != nil {
        return nil, e
    }
The original loop/additive/fence/Commit stays in its original order and same Tx.
A is necessary for original installed24 pre-DDL integrity, including missing old
fence triggers that CREATE IF NOT EXISTS would otherwise repair before B.
A is metadata/protection validation only; never installs or updates anything.
B is obligatory fresh24 and repeated24 full validation; A does not replace B.
Actual line anchors in captured source: New53; tx begin74; defer78;
fence114-116; commit117. Line numbers are subordinate to exact captured source.
''',encoding='utf-8')
contract='''# STARTUP-01 closed caller proposal; unexecuted

This supersedes only fd227's claim that the20-path scope needs no startup caller. All20 original entries are retained, one exact existing source path is proposed. Root/non-author review and a serial source lease are still required. No source, SQL migration, UDF or test has been executed or edited.

## Caller, atomicity, version branch

The only new caller is domain.New in internal/domain/store.go, not internal/store/sqlite.go. Keep preexisting checkMigrationInventory and CheckMigrationSafety before Begin, all numbered migration order, session additive, installClientSessionFence(false), and original Commit. NewCurrentMu continues to invoke New unchanged.

After Begin/defer Rollback and before any DDL, call checkClientCancelStartupBeforeDDL(ctx, tx). It enumerates schema_migrations version+typeof on this exact Tx, requiring the same contiguous integer inventory. n<=23 returns without querying any F08 object or changing historical install/observation behavior; existing pre-backup guards remain independently authoritative. Exact n==24 verifies trusted installed schema inventory BEFORE any IF NOT EXISTS repair could hide a missing preexisting protector. Future/gapped/invalid inventories error; absence of an F08 table never infers a legacy version. No ready/hash boolean returned, no captured generation, and no writes. This additional precise pre-DDL span is part of proposed path21, not an implied change to another caller.

For a fresh target24: numbered1..23 -> SQL24 original numbered-source type preflight -> original SQL24 DDL/legacy capture -> session additive -> installClientSessionFence(false) -> validateClientCancelStartup(ctx, SAME tx) -> original Commit. During numbered preflight, no query of absent additive sessions. Post helper sees all34 categories. Any helper/schema/UDF/fingerprint/type/proof/rows.Err failure returns error, Service is not returned and defer Rollback undoes numbered/additive/fence work and migration markers together. store.Open's earlier WAL/header effects are explicitly outside this domain transaction; do not claim an unchanged file byte hash merely because canonical DDL/rows rolled back.

For an already installed24: exact pre-DDL fingerprint -> unchanged idempotent additive/fence operations -> post full fingerprint and guarded source/proof check -> Commit. Missing/replaced F08 objects are rejected even though numbered migration24 is skipped. Missing old session protector also refuses at pre-check rather than being invisibly healed by CREATE TRIGGER IF NOT EXISTS. Changed same-name SQL, missing indexes/trigger/table/view, changed columns/constraints and extra shadowing TEMP objects cannot masquerade as an exact inventory. SQL24/data proof checks never fall back to version-only or empty-set success.

The preexisting legacy22/23 install path remains identical apart from the no-F08-query version-return call. Exact populated22/23 opened with a24 inventory remains MIGRATION_PREBACKUP_REQUIRED, not an in-place upgrade. Matching23 public upgrade belongs to proposed backup_cancel_upgrade.go and original private upgradeLocal branch; exported UpgradeLocal verifier wrapper unchanged. Its isolated migrated DB must perform the same post-additive/fence gate before publication under the original exclusive-lock proof. This does not route public upgrade through normal New against the user's source DB.

## Expected schema and actual schema comparison

Private expected inventory implementation lives in the already proposed client_cancel_finalization.go. It is a compiled source-owned immutable list of (schema-name,type,name,tbl_name,sql-or-null) for the release's installed schema: fixed numbered1..23 plus exact SQL24, additive session schema and unchanged fence installation, including the original queue/configuration protectors and SQL24's expressly declared changes. SQLite automatic index SQL NULL remains NULL, not an empty string. Compare exact UTF8 SQL bytes as SQLite stores them, not string containment, names alone, trigger counts, a current-DB-generated expected hash or a caller-supplied digest. A SHA256 over canonical sorted tuples is an audit fingerprint in addition to direct tuple equality. Exclude engine-internal sqlite_% entries as a fixed rule; application/temp objects cannot shadow protected names. Record schema_version before/after actual collection within the Tx and reject unexpected mutation/errors.

The actual literal expected sqlite_schema representation/hash cannot honestly be supplied from unexecuted candidate text. Future implementation must produce the fixed literal by a qualified isolated real SQLite install of the fully pinned release inputs, store it inside the already scoped helper Go file, independently check it against that isolated install in the scoped tests, and freeze its source/hash before product validation. Runtime never regenerates expected schema from the untrusted database and never creates a reference DB inside the startup transaction. No extra generated-source path is implied. The static candidate SQL SHA e3d58e... and its9 tables/3 views/90 triggers are inputs to that future freeze, not an actual installed fingerprint.

Before relying on f08 views, the helper compares installed table/view/trigger/index tuples against this trusted release list. All subsequent readers qualify main schema and reject protected-name temp shadowing; this does not modify the frozen34 tuple SELECT bytes. On repeated startup validation happens before any repair and again after fence. Unexpected object modifications require a new migration/review, never an automatic rebuild here.

## Post-additive full34/type/proof reader

On exact24 and the same tx, check foreign_keys=1; record recursive_triggers0/1 and trusted_schema actual value. Do not silently turn FK/trusted_schema on or require recursive_triggers1; original REPLACE guards work in either mode. A required function missing/unsafe or PRAGMA unsupported is a failure with actual origin. Old22/23 programs continue their exact own-schema behavior; no UDF registration/store source changes are introduced by this caller proposal.

Read actual f08_source_type_violations and then the guarded main.f08_sources result as complete bytes, consuming Scan and rows.Err; no catch-as-empty. Wrong original stored type causes the existing mode9 error through the view. Valid input does NOT intentionally execute mode9 or accept its failure as success. Mode9 remains the same pure unconditional F08_STORAGE_CLASS error; it is not a35th category or a startup ready check. Require exactly one source document, full34 category set including empty arrays, actual281-column registry and nullable semantics, raw bytes and domain_refs multiplicity. Existing SQL-trigger fourteen NEW/OLD type gates remain first statements verbatim.

Invoke the existing proposed shared history-aware inventory validator on this freshly acquired actual snapshot: complete original identity/private header/journal/control/group/pins/legacy cohort/origin/final commit and current authority relations, exact semantic digests and full raw schemas. No new callback mode is introduced. Do not replay admitted.insert against later current heads: completed historical roots use pinned original versions/artifacts; pending/restored states preserve old-vs-current fence rules. Reject incomplete final group/journal relationships and orphan/mutated original facts. Empty fresh24 is a legitimate empty inventory; absence of a category/table is not. No startup observation, run birth, reservation release, user flag reset, recovery launch or historical qualification occurs.

No fingerprint can detect a malicious full-file rewrite that restores all schema plus self-consistent historical data. This preserves the original in-file consistency scope; it does not claim an external cryptographic attestation of the database history. Schema tampering detectable by exact tuple mismatch is refused; no DELETE+replace repair is attempted.

## Preserved contract and tests

candidate.sql.txt copied byte-identically; original34 tuple block SHA152b2a... unchanged; storage registry34 categories/281 columns unchanged;14 trigger first-statement type guards unchanged. Original v5 closed-group atomicity, R1 legal multiplicity, R2 permanent birth/current epoch distinction, old23 non-backfill boundary, F08 sole journal authority and UNKNOWN cost remain. Original12+R1 six+R2 fourteen+N eight =40 future groups remain NOT_RUN. New startup cases refine N05/V12 only and do not replace any group or count a static helper description as execution.
'''
(N/'startup-contract.md').write_text(contract,encoding='utf-8')
future=json.loads((P/'future-matrix.json').read_text(encoding='utf-8'));put('future-matrix.original40.json',future)
put('startup_subcontrols.json',{'status':'NOT_RUN','parent_groups':['N05','V12'],'group_count_unchanged':40,'test_paths':['internal/domain/client_cancel_finalization_test.go','internal/domain/backup_cancel_upgrade_test.go','internal/domain/backup_cancel_finalization_test.go'],'cases':[{'id':'N05-S01','case':'actual fresh24 New, original numbered->additive->fence order, helper truly invoked before Commit; pristine all34 empty legal snapshot'}, {'id':'N05-S02','case':'inject post-fence type/fingerprint/proof/UDF error and prove migration marker/DDL/rows atomic rollback, while separate Open WAL bytes honestly accounted'}, {'id':'N05-S03','case':'same24 second New exact unchanged accepted; fullschema/read rows stable and no origin/observation/qualification inserted'}, {'id':'N05-S04','case':'delete/replace each F08 protection object in isolated raw copy then actual New refuses; original input closedbytes retained'}, {'id':'N05-S05','case':'empty installed24 missing old session fence: pre-DDL helper refuses before IF NOT EXISTS can recreate; populated24 also fails original safeguards'}, {'id':'N05-S06','case':'valid22/23 original own inventories unchanged; populated23 with24 inventory still prebackup refusal; missing F08 on recorded24 not legacy fallback'}, {'id':'N05-S07','case':'same-name view weakened or mode9 shortcircuited/type view changed; exact actual sqlite_schema tuple mismatch refuses even data empty'}, {'id':'N05-S08','case':'FK0 rejected24; recursive0/1 preserved; trusted_schemaOFF/missing UDF records actual failclosed not fake validation success; no globally changed defaults'}, {'id':'N05-S09','case':'type wrong-class34 source / duplicate keyed rows / legitimate refs multiset / valid idempotency TEXT+BLOB and nullable values; actual snapshot proof, full original evidence'}, {'id':'N05-S10','case':'later legitimate epoch/runtime/restore fences and historical FINALIZED still checked against original immutable history; no startup backfill/reclassification'}, {'id':'V12-S01','case':'public matching23->24 lock through validation/publication and ordinary targetbackup/restore/rebackup; same post helper invoked on isolated target; old23 program proof real'}, {'id':'V12-S02','case':'captured compiled expected schema literal independently matches real installed release; changed sourceSQL/fingerprint literal negative; no current-DB-derived expected hash'}]})
put('proposal.json',{'status':'READONLY_STARTUP01_SCOPE_REVISION_PENDING_NONAUTHOR','author':'/root/command_queue_impl','input_scope_sha256':sha((P/'scope_revision.json').read_bytes()),'input_review_v2_sha256':sha((V/'review.v2.json').read_bytes()),'candidate_SQLTEXT_sha256':sha((P/'candidate.sql.txt').read_bytes()),'scope_count':21,'category_count':34,'typed_columns':281,'before_callback_inline_gates':14,'SQLTEXT_changed':False,'future_groups':40,'source_changes_now':0,'SQL24_lease':False,'exact_new_path':'internal/domain/store.go','function':'New','spans':['immediately after defer tx.Rollback before numbered loop: exact already24 read-only pre-DDL fingerprint','after successful installClientSessionFence and before tx.Commit: sameTx actual full34/type/proof/fingerprint gate'],'reason_for_two_spans':'post-fence alone may hide an originally missing session fence recreated by unchanged IF NOT EXISTS; original source24 integrity must be checked before startup writes','old20_preserved':'complete_scope21.json embeds untouched original20 and precise additive helper responsibilities','expected_installed_fingerprint_status':'NOT_YET_ENGINE_QUALIFIED. Current SQLTEXT is not an installed sqlite_schema fingerprint; future literal generation/independent install comparison is mandatory before source freeze. No syntax/runtime acceptance claimed.','not_changed':['original34 tuple SELECT bytes','all original source scope protections except explicit proposed New caller','23/22 legacy startup behavior','original observation/idempotent insert/qualification producers','existing failure counts/UNKNOWN/history','all40 future groups']})
after=[]
for x in refs:
 raw=Path(x['path']).read_bytes();after.append({'path':x['path'],'sha256':sha(raw),'bytes':len(raw),'same':sha(raw)==x['sha256']})
put('inputs.after.json',after)
if any(not x['same'] for x in after):raise RuntimeError('READ_DRIFT')
put('diagnostics.json',{'known_read_tool_chunks':['b0b2a6','01dc19','ab9c55','e7b9c9','751c48'],'known_outer_nonzero':[],'SQL_Go_Node_HTTP_model_tests_SDK_vault_executions':0,'display_truncation':'Initial discovery/combined views truncated; source files and full sealed prior package copied byte-exact for audit.','unknown_exit_policy':'No failed tool exit invented; an unavailable exit remains null.','original_failures':'All prior fd227/reviewer/G1 origins preserved by original refs, no reset/no native replay.'})
put('handoff.json',{'status':'READONLY_SCOPE21_PROPOSED_NOT_SOURCE_READY','namespace':str(N),'proposal_sha256':sha((N/'proposal.json').read_bytes()),'scope21_sha256':sha((N/'complete_scope21.json').read_bytes()),'contract_sha256':sha((N/'startup-contract.md').read_bytes()),'source_inputs':len(refs),'drift':0,'future_groups_NOT_RUN':40,'new_product_source_paths_written':0,'new_tool_errors':0,'source_lease_required':True})
files=[]
for p in sorted(N.rglob('*')):
 if p.is_file() and p!=N/'manifest.json':raw=p.read_bytes();files.append({'path':p.relative_to(N).as_posix(),'sha256':sha(raw),'bytes':len(raw)})
put('manifest.json',{'self_excluded':True,'files':files})
print(json.dumps({'namespace':str(N),'listed':len(files),'with_manifest':len(files)+1,'refs':{p:sha((N/p).read_bytes()) for p in ['proposal.json','startup-contract.md','complete_scope21.json','handoff.json','manifest.json']},'inputs':len(refs),'drift':0},ensure_ascii=True))

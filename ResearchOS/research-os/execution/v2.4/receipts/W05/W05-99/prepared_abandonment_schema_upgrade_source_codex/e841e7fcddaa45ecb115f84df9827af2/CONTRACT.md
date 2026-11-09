# Fixed schema23-to24 prepared-abandonment Source contract

Status: Source implementation only. No Go compiler, gofmt, Native process, database, provider, service, Git or production data-root operation was executed by this Source author. Root must compose, compile, run the listed tests and obtain independent review.

## Composition and ownership

This candidate owns 10 files: the new fixed-plan implementation and Windows/native entry, non-Windows denial, two focused test files, one byte-identical SQL24 embed mirror, and minimal hooks in backup.go, backup_upgrade.go, backup_host_configuration.go and the historical configuration-upgrade test helper. Main and earlier Source namespaces were not edited.

Required overlays are prepared-run-abandonment v4 (including migration0024 and its migration preflight support) and prepared_abandonment_native_authority_source_codex/f6373acf36474d869fa8a64f3c490864. No authority leaf or apps/control file belongs to this candidate.

## Rehearsal

UpgradeLocal dispatches only the new fixed plan schema23-to24-prepared-abandonment-v1 to this implementation. All prior plan branches remain unchanged.

The fixed release checker requires the exact numbered 1..23 source and 1..24 target, pinned original migrations/contracts/additive session SQL, and SQL24 hash sha256:1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098. A disposable template derives four distinct schemas: original23, original24, restored23, restored24. It never repairs the source.

The rehearsal acquires the actual Windows DataRootLease and retains SQLite EXCLUSIVE ownership of the original source through encrypted backup, restore, migration, receipt creation and source recheck. Its running executable must equal SourceProgram. Program hashes are recorded, not treated as independently accepted release authority. The original concrete FrozenProvider/protected-reference verifier remains required wherever protected refs exist. Missing key, lease, protected service or binding fails that branch; no plaintext fallback or skipRecovery exists.

The complete existing encrypted backup machinery creates the matching23 snapshot. The isolated restore uses ordinary backupFence, credential revocation, active Run QUEUED-to-RECONCILING, lease hash/expiry/revision/audit, unfinished-effect UNKNOWN handling, queue fencing, source relocation and acceptance checks. The fixed same-host workspace policy preserves existing verified workspace bindings, as in the existing upgrade plans. It does not promote the restored database.

Only after all ordinary recovery/source-path steps does the implementation record post-restore rows and schema. The source-to-restored delta includes per-table columns/counts and every removed/added typed row digest; full row values remain recoverable from the encrypted source backup and isolated database and are not printed. A rollback probe applies only pinned0024 plus version24, verifies all invariants, rolls back, and checks exact baseline rows/schema again. A second identical transaction validates and commits the isolated copy.

The rehearsal receipt is Destination/prepared-abandonment-rehearsal.json. It binds original/pre-DDL/post-DDL row hashes, all four schema hashes, options, binary/release/SQL pins, backup manifest, exact restore delta and normal RestoreReport. It explicitly denies automatic promotion or original business mutation.

## Original-root apply

ExecutePreparedAbandonmentSchemaUpgrade(ctx, db, token recoveryauthority.MigrationToken, ownerToken, opt) accepts only the leaf's opaque purpose-separated MigrationToken. No arbitrary verifier/callback, environment approval, caller public key or JSON approved field is accepted. An adoption Token cannot be substituted.

The signed binding uses:
- SourceReleaseSHA256 / TargetReleaseSHA256: raw program digests.
- SourceInventorySHA256 / TargetInventorySHA256: fixed complete migration/contract/additive inventory hashes.
- SourceSchemaSHA256 / TargetSchemaSHA256: original-root schemas, not restored schemas.
- OriginalRowsSHA256: every main table's typed row multiset before backup, including original migration timestamps and credentials.
- OptionsSHA256: Digest(json.Marshal(LocalUpgradeOptions)); pass the normalized options recorded by the rehearsal.
- Backup: RawPin role encrypted-backup-manifest, Snapshot/manifest.json.
- Rehearsal: RawPin role isolated-restore-rehearsal, Destination/prepared-abandonment-rehearsal.json.

RequirePin additionally requires every source-inventory:<relative-path>, target-inventory:<relative-path>, source-program, target-program, migration-sql and encrypted-backup-payload:<manifest-name>.enc member to be in the already signed, native deny-write-held grant. Paths use the exact filepath.Join result for the signed normalized options. These checks cannot append authority.

The entry checks the running target program, fixed releases, templates, existing encrypted backup MAC/AEAD and every plaintext member hash/size, pinned rehearsal and purpose lineage, original current rows/schema, actual SQLite main path, no attached database and no temporary schema. The native token independently supplies live peer/self/root/DB identity, DataRootLease, accepted release and expiry. SQLite EXCLUSIVE ownership is retained on the one supplied connection.

The original transaction obtains resourceWriteLock, re-authenticates a CURRENT direct local OWNER and the exact project grant, checks the opaque token, then applies only0024 and INSERT version24. Every existing row, column and old migration row is preserved; only one new migration row is permitted; the new proof table is empty. Target full schema, integrity and foreign keys are checked before commit. No restore, backupFence, Run transition, lease mutation, ledger change, old once/clock change or abandonment occurs on the original.

An existing original-schema24 intent denies replay. Immutable files are created under Destination+".original-schema24": migration-intent.json before the transaction and migration-result.json after actual outcome. A failed Commit is COMMIT_OUTCOME_UNKNOWN and conservatively consumes the token; it does not claim rollback. Crash/persistence gaps require independent inspection, never automatic replay. Actual abandonment is a later separately authorized operation.

## Normal backup and historical compatibility

backup_host_configuration.go retains its existing <=23 behavior and fixed SQL23 fingerprint. Exactly24 additionally requires contiguous integer1..24 and the exact proof table/autoindexes/six triggers generated from the byte-pinned SQL24 embed. Version25 and altered24 fail. Existing queue/history/protection/integrity checks remain in place. This is not a new generic future-schema acceptance policy.

The legacy configurationMigrationFiles test helper now builds the same existing exact schema23 release fixture before enumeration. It does not redefine the 22-to23 plan, its SQL, expected schema or historical test thresholds. Normal populated23 startup still rejects target24 via CheckMigrationSafety.

## Validation Root must execute

13 top-level TestPreparedUpgrade tests cover lossless SQL storage types; original QUEUED/Task RUNNING/dispatch PREPARED/auth/BLOB preservation; SQL/source/target/baseline refusals with actual transaction rollback; rollback rehearsal; missing/extra/changed release files; old-row mutation rejection; exact24 schema and future25 refusal; complete encrypted isolated rehearsal with a public admitted Run; competing DataRootLease; zero opaque-token rejection; normal startup prebackup requirement; ordinary CreateBackupWithWorkspaces after exact24.

Root should also run the relevant existing TestConfigurationUpgrade and TestBackupHostConfiguration regression coverage, including historical23 fixture behavior. Test execution/leaf counts are not claimed here.

## Remaining trusted execution gates

The composed Source must compile and pass Root's actual tests and independent review. The native leaf currently has an empty enrolled issuer key and therefore denies production tokens: independent issuer enrollment, accepted source/target/native release inventory, separately signed current migration grant, held complete raw pins, current OWNER credential, matching encrypted backup and reviewed rehearsal are still required.

The OWNER credential must already be represented in the reviewed pre-backup original baseline and remain valid at apply. Creating a new credential after rehearsal changes the baseline and requires a fresh reviewed backup/rehearsal; the migration does not edit credentials to evade this check.

Original trial provider_requests remains unknown and recorded model effects remain zero as prior evidence; this Source author did not query or alter them. No old failure lineage, once, clock, C7 state, qualification or formal acceptance is advanced.

## Author diagnostic ledger

763: one rg argument incorrectly named a candidate-only file under Main; os2 appeared; outer0, inner rg/Python/Native exits unavailable.
764: oversized constructor command was rejected by OS CreateProcess206 before process launch; outer/Python/Native exits unavailable.
Both retain full original input and visible output/error in immutable failure-origin files. The earlier rg empty search with exit1 and no diagnostic is recorded as search_no_matches, not a failure. Counters are not reset.


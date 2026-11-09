# LEGACY-ROLLBACK-001 Source revision v2

Authority NONE; formal_acceptance=false; Source prepared pending independent review. Candidate Go/SQL/native/model execution is NOT_RUN. All writes are confined to this new v2 namespace. Old Source/review packages, Main, T5/T6, production files and canonical files are read-only; no baseline lock is held.

Independent review HDF/MF were verified against Root's exact hashes before report access. All 42 reviewer members and 28 previous Source members match their manifest pins. The original REQUEST_CHANGES_SOURCE_ONLY and LEGACY-ROLLBACK-001 finding are preserved in inputs/review; this author does not close or accept that finding.

## Minimal change

Only TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction in client_session_bootstrap_test.go changes. Its setup(t) → useLegacyTranscriptFixture route had no Project identity, so the copy helper returned before Begin. The v2 test calls legacyTranscriptFixtureDatabase(t) directly, checks its error with the original t.Fatal(err), and uses the returned db for Begin and the final post-rollback query. No Project or migration ledger is invented.

The inverse replacement reproduces the previous file's exact bytes. Every other previous Test body is equal. retrieval_test.go, legacy_migration_fixture_test.go and testdata/pretranscript-3225a31f.sql are byte-for-byte equal to the previous candidates. The original T5 12 Test names, 126 t assertion call nodes and 9 unrelated original bodies remain intact; the prior two explicitly negative tests remain present. No assertion call was removed or weakened.

## Full rollback call chain and lifetime

The unchanged helper legacy_migration_fixture_test.go:99–115 opens a fresh test DB, immediately registers t.Cleanup for that local db.Close at :103, verifies pinned bootstrap SQL, applies real contiguous migrations2..20, applies the genuine pre-transcript DDL, and confirms the transcript column is absent. A resource mismatch or constructor error remains an error rather than PASS.

The corrected test client_session_bootstrap_test.go:117–125 obtains that DB, checks the constructor error, begins the caller transaction and retains defer tx.Rollback. The unchanged installClientSessionFence(ctx,tx,false) call at :127 performs the additive column inside that transaction. The original inside-transaction count==1, explicit rollback error check, and post-rollback count==0 assertions remain at :131–138.

Production client_session_fence.go:25–67 has no Project-copy requirement. Its conditional Run barrier seeding runs only when restored is true; this rollback test passes false. The real migration prefix supplies the tables referenced by unchanged trigger definitions. This test creates no Session/Project/Run data and needs no fake identity. Transaction rollback executes before testing cleanup closes the DB; deferred rollback is retained after explicit rollback exactly as before. These are static call-chain observations, not runtime proof.

## History, resources and acceptance boundary

The true DDL is still commit3225a31fd25969c6a5e071a2fc686cb4a835e162 / blob9efc768f8f4cfb6ac31e1f88a78ad095877328af, SHA256 3b00677902c3be1dbffb8f7505293bae7242dc976e8017562ab86254ac212f2a, 2014 bytes. All20 numbered Source resources independently reproduce their frozen Git blob refs; this revision edits none of them.

Ordinary historical20 New positive upgrade remains BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE. Genuine historical program/compiler closure, matching-program backup, isolated restore and a supported explicitly authorized upgrade path remain required. Restore/rollback and SQL9 fixtures remain synthetic component scopes and do not accept the original parent or product upgrade.

Static fixed Python used -I -S -B -X utf8 and emitted ROOT_PYTHON_EXIT=0 for metadata/read/build invocations. No Go AST/gofmt/compiler/SQL/native/model was invoked. This v2 has zero new mechanical errors; prior author failure833, earlier826, the independent rejection and FULL1261PASS/25FAIL/4SKIP remain preserved without resetting any count.

HDF/MF include exact source/base/reviewer/resource refs, the minimal diff and inverse proof, static preservation, call-chain excerpts and available original tool IO. Root must obtain independent v2 review and fresh guarded actual component evidence. This Source author has no acceptance authority and stops after sealing.


# C revision03 — one native source lease through every official entry

DESIGN_ONLY. Replaces revision02's unresolved nested-backup lease choice and expands only the exact C interlock scope below. C's five-version transaction, current Owner/run-null proof attribution, fixed journal/crash/abort rules and no actual authority remain. B/D designs are unchanged. The extra shared replacement-history reader is necessary to make a direct typed adapter call as safe as its CLI caller without a domain→host import cycle or a caller-supplied callback/boolean.

## One checked native owner and a private borrow

The native file handle is owned by exactly one `*runtime.DataRootLease`. It is never serialized, exposed as an integer, reconstructed from a path/PID or accepted through JSON. `AcquireDataRootLease` and the raw coordinator `LockDataRoot` path must check BOTH qualification and verifier-replacement journals while holding the newly acquired lock before returning it. Existing ordinary callers keep the same signatures. Factor raw OS lock acquisition into a package-private primitive; do not recursively call the checked public wrapper. Partial journal, unknown file or nonterminal history denies ordinary acquisition.

The two maintenance commands may use a distinct exact-operation inspection permit whose namespace+operation+plan digest are immutable private fields obtained by strict journal parsing. Under the newly held native lock, re-read and compare that exact journal and check all other operations in both namespaces. This exception bypasses discovery of only its own already-pending operation; it grants no Owner identity, SQL write, termination or execution authority. Replacement recovery cannot exempt C; C recovery cannot exempt replacement. A new commit with no pending journal uses ordinary checked acquisition. Never take a naked `skipGate bool` or caller-defined validator.

Existing host replacement history code depends on host/domain types. Put the read-only replacement history grammar in `internal/qualificationmaintenancejournal/replacement_windows.go`, alongside C's journal grammar, using only bounded filesystem/ACL/native-path/hash/strict-JSON helpers and existing Windows libraries, with no domain/host imports. It must validate the SAME existing plan/events/file inventory, state transitions, immutable backups/stage absence, causal sequence/predecessor/terminal digests, and latest runtime-verifier-installation.json hash. It cannot classify only the last state string or ignore unknown fields. Existing host replacement writer/recovery retains its original checks; the combined host gate additionally uses this shared read-only result. Run positive/negative equivalence tests against the existing replacement reader on the same fixtures. This is a second exact validator at a lower dependency boundary, not a new replacement format, migration, acceptance status or authority source.

Add the following Windows runtime methods in existing data_root_windows.go:

```go
func (l *DataRootLease) CheckMaintenanceReady(database string) error
func (l *DataRootLease) BorrowMaintenanceSource(database string) (*DataRootSourceBorrow, error)
func (b *DataRootSourceBorrow) Check(database string) error
func (b *DataRootSourceBorrow) Release() error
```

`DataRootSourceBorrow` has only private fields and no public constructor/JSON conversion. BorrowMaintenanceSource verifies Held, canonical root/database/file identity (non-reparse, exact source under root), both journals with **no own-operation exemption**, and the parent's live generation. It reserves a single borrow under the parent mutex. Nil/zero/closed/already-borrowed/stale/released/wrong-root capability fails. Parent Close refuses while borrowed. Borrow Check revalidates parent Held/generation and pinned file/root identity; it does not acquire another OS lock. Release only releases that borrow, not the native handle. Copies share the same private state, so a released borrow cannot become valid by copying it. No source workflow receives a raw native handle.

The domain Windows-only adapters are:

```go
func UpgradeLocalUnderSourceLease(ctx context.Context, opt LocalUpgradeOptions, lease *runtime.DataRootLease) (RestoreReport, error)
func UpgradePreparedAbandonmentBackupUnderSourceLease(ctx context.Context, opt PreparedBackupHandoffOptions, lease *runtime.DataRootLease) (RestoreReport, error)
```

They normalize/validate the source path before any secret/protected-service/template/DB work, call BorrowMaintenanceSource (therefore rechecking both journals even if invoked directly), construct package-private `backupSourceLease` around the borrow, assign the unexported `LocalUpgradeOptions.sourceLease *backupSourceLease`, and delegate to existing private workflows. The field is excluded from JSON, canonical plan hashes and public DTOs; external Go callers cannot construct it. The adapter defers borrow.Release until the full workflow has returned and all its DB defers have run. The CLI remains the sole native owner and closes the outer lease only after the adapter returns.

`backupSourceLease.Check(root,source)` binds the exact canonical source/root/file identity and parent generation; its fields and constructor are private. `acquirePreparedUpgradeRootLease(root, source, inherited *backupSourceLease)` returns a private wrapper over this borrow when inherited is nonnil. Its Check calls inherited.Check; its Close closes only the wrapper state, never Release and never the native handle. Any inner error follows this same rule. No second native acquire, Close/reopen gap or callback is allowed. In official workflows inherited must be nonnil; legacy internally owned behavior, if retained for existing isolated private fixtures, stays package-private and is not reachable from the public workflows or CLI. Prefer rejecting nil at the production private dispatcher before a prepared branch.

The existing exported `UpgradeLocal` and `UpgradePreparedAbandonmentBackup` become explicit fail-closed compatibility entrypoints returning `UPGRADE_SOURCE_LEASE_REQUIRED` before protected providers, release/template preparation, key reads or DB access. They do not internally reopen a root, set sourceLease, or treat absent journals as permission. Official callers migrate to the two typed adapters. Direct use of the typed adapters with an ordinary but genuinely held lease is safe because BorrowMaintenanceSource itself runs the complete gate; the caller cannot claim that a gate passed. Private existing isolated algorithm fixtures are not credited as guarded-workflow tests.

On non-Windows, the platform wrappers and domain adapters return `NATIVE_WINDOWS_SOURCE_LEASE_REQUIRED`; no nil/any value succeeds or masquerades as an OS capability. Common CLI code calls platform wrappers so it does not need a fabricated cross-platform native-handle type.

## Exact backup dispatch coverage

In ops/backup/main.go, validate command and plain paths first, then route every existing-source workflow through platform `openBackupSourceLease(source)` before reading KeyFile, calling any protected service, opening DB, loading/creating an upgrade template or building a Host. The Windows helper canonicalizes and holds exact root/file identities, acquires the one checked lease, calls host combined gate under it, and returns that opaque lease. Errors close only resources created by that helper. The outer CLI defers Close after all downstream DB/workflow defers. Keygen has no data root and stays outside this gate. Restore continues to require a new destination and reject an existing/aliased live or pending root; it cannot consume the source upgrade capability as permission to replace product data.

| Entry | Domain path while same outer lease remains held |
|---|---|
| create / export | existing source store.Open + Service/Host backup; DB closes before outer lease |
| upgrade-local: schema13-to14-remote-access-v1 | UpgradeLocalUnderSourceLease -> upgradeLocal target14 |
| upgrade-local: schema13-to20-research-runtime-v1 | same adapter -> upgradeLocal target20 |
| upgrade-local: schema21-to22-client-command-queue-v1 | same adapter -> upgradeQueueLocal |
| upgrade-local: schema22-to23-host-model-configuration-v1 | same adapter -> upgradeConfigurationLocal |
| upgrade-local: schema23-to24-prepared-abandonment-v1 | same adapter -> upgradePreparedAbandonmentLocal; private borrowed wrapper at existing line416 |
| upgrade-prepared-backup | UpgradePreparedAbandonmentBackupUnderSourceLease -> upgradePreparedAbandonmentBackup; private borrowed wrapper at existing line181 |

All five plan choices cross the adapter before their dispatch. Invalid plan rejects before secret/template work. No branch can fall back to the old public API. Both prepared branches pass `opt.sourceLease` explicitly; the handoff's copied opt preserves that private field while normalizing paths. Revalidate source identity after normalization and before its first DB open; an option copy must not detach the native identity. Non-prepared branch algorithms need no extra production file edits because the adapter owns their complete call lifetime; update public workflow tests to use the new real source-lease entry, not a fake option flag.

## Other early entries, including release_host

Normal Core calls the combined gate while holding its lease before store.Open/bootstrap/provider/protected setup. Replacement preflight/commit/recover uses the checked acquisition or its own exact-operation permit; another pending C operation blocks it. C's own preflight/commit/recover/abort checks replacement history and all other C operations before opening SQLite. The original namespace semantics and explicit NOT_APPLIED→ABORTED rules are unchanged.

Inherited prepared recovery/migration already receive a token whose native session has acquired and borrowed the real lease. Central acquisition now checks both namespaces before returning the token. In apps/control/prepared_recovery_windows.go, after ReceiveInherited/ReceiveMigrationInherited and before openExclusiveRecoveryDB/PRAGMA, obtain Adoption/Binding, call token.Check with the exact bound public inputs, call the host pure combined-root validator, and call token.Check again. The token remains live across the DB operation and its existing Close owns the one native release. Do not call AcquireDataRootLease again, expose native handles, mint a new token, or add a host import to recoveryauthority.

Legacy `ops/supervisor/release_host` must obtain its platform gate/lease wrapper BEFORE protectedstore.OpenCanary; the existing ordering opens Canary before its line44 lease and must be reversed. `main.go` calls `openReleaseHostSourceLease(dbPath)`, then opens Canary, then store.Open, and defers their closure in the order DB→Canary→lease. Wrapper checks exact fixture DB/root, acquires one checked lease and calls combined gate. No existing fixture public/live scope is expanded.

For `--control` mode, do not retain a second parent data-root lease across a launched Core's lifetime. A platform wrapper first retains the existing strict disposable ControlFixture bindings and canonical root/data mapping; it never redirects an arbitrary --db into that branch or opens Canary/SQLite itself. Existing ControlFixtureDriver.Start/Restore/Compatible use AcquireDataRootLease before their offline DB/protected/launch work; the central two-namespace check covers those exact paths. Start releases its parent lease only as part of the existing child-start protocol; the child normal startup acquires/checks the same root before setup. Pending intent during the handoff prevents child startup, rather than silently bypassing the check. When the fixture Core is live, its held lease prevents a new C intent; when offline, driver acquisition blocks a pending intent. Existing command/release journals are not proof of absence of C/replacement journals. Source tests must demonstrate both bootstrap and existing-fixture control modes preserve these checks; any uncovered DB/protected call before checked acquisition requires an explicit allowlist revision, not an exemption.

Fixture-control replay acquires/holds its exact fixture root lease and combined gate before store.Open. store.Open's pending-namespace rejection remains defense in depth and does not replace a held native lease. No new public HTTP or management entry is added. No same-root mutator may pass an arbitrary callback, `true`, raw handle or JSON approval to a gate.

## Scope and acceptance

Carry the complete revision02 C scope, add the reviewer's exact existing/new/test paths, plus the two justified shared replacement-reader paths and the three existing public upgrade test files whose valid calls must migrate. Full union is frozen in C-lease-exact-scope.json; no wildcards. No original spec/threshold/schema changes. The own-operation permit must not be accepted by BackupSourceBorrow: backup never inherits a C/replacement pending-operation exception.

Required positive fixture: a real held native lease passes both empty/valid-complete namespaces, one adapter traverses each of five plan dispatches, each prepared inner scope succeeds without a second lock, and inner failure leaves outer Held. Borrow stays active until all source DB handles close; parent premature Close fails. Negative fixtures cover both pending namespaces at every entry before Canary/key/provider/template/store, wrong root/source identity, zero/closed/stale/released/concurrent borrow, standalone public APIs, exact-own-exception crossing namespaces, malformed completed replacement history and control/replay routes. Tests must instrument forbidden setup boundaries or use inaccessible sentinel files to prove early rejection; checking only an eventual error is insufficient.

This resolves the design choice; no implementation or test has run here. Independent review must accept the concrete package boundary and complete entry matrix before C Source authority. Actual maintenance still requires accepted A/B/C/STOP, current authority and separately reviewed exact operation. Formal increment0.

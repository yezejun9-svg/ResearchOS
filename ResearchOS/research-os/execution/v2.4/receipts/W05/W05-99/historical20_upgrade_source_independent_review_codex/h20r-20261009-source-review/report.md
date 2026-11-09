# H20 independent Source review

Verdict: REQUEST_CHANGES. One P2 test-coverage defect (H20R-001); no production-path blocking defect identified by this Source review. This is not compilation, Go/SQLite/native execution or acceptance of historical20-to24.

## Required correction

The wrong-key assertion at backup_history20_upgrade_test.go:76-78 uses generic RestoreBackup on a snapshot created by the local-upgrade policy. Generic RestoreBackup supplies policy=nil (baseline backup.go:561-562). readBackupPolicy checks m.Format != backupFormat(policy) first in its short-circuit OR (backup.go:504-505). localUpgradeFormat is incompatible with the generic format. Therefore both the correct and incorrect key are rejected before the HMAC is evaluated. The test passes without testing key authentication.

Use the matching local-upgrade policy to authenticate the sealed snapshot. Establish a positive control with the original key and verify expected files, then vary only the key and require authentication rejection. Do not change the production format guard to make this test pass. Root should not execute or accept the present candidate as complete wrong-key coverage.

## Source findings

The public UpgradeLocal dispatch targets a separate fixed 20-to21 handler. The release checks pin numbered 1..20 / 1..21 SQL and contracts. The historical A shape is compared with a template built from exactly the numbered base; the B additive-session shape is rejected. The new handler does not call the current domain constructor or an additive session installer. EnsureClientSessionFence returns without writes when client_sessions is absent, and fenceRestoredClientQueues returns for version below22.

The handler retains the existing exclusive-source-open, full encrypted backup, isolated restore and final publish framework. It validates snapshot row identity and workspace identity under the exact new plan policy, checks recovery before migration, and rechecks target schema, permitted row changes, original source rows, releases and program hashes before publication. Active Runs, effect history, credentials, retrieval roots and barriers have explicit constraints. 0021 DDL executes before INSERT version21 in the same transaction with deferred rollback. No ledger-only shortcut was found.

The three existing-file changes are independently reversed byte-for-byte at the text level: one dispatch branch, one new plan-specific workspace callback/branch, and CLI help. All 66 author-pinned baseline files and original contract/resource pins were rehashed. Existing 21/22/23 plans, templates and SQL are unchanged. Candidate final new-handler hash is cf8187c56564a38a1aa1357ae7f11ef45890d9f992f7500b768890679c683778/19212; the construction intermediate is not treated as the sealed candidate.

Five test parents and four release/source rejection subcases are present as Source. The ledger-insertion trigger test exercises the actual migration function and asserts rollback if run. The generic restore-cancellation test is source coverage for staged failure; it would be stronger to assert callback reachability and errors.Is(context.Canceled), but no concrete failure of that case was established here. Active-Run, effect, workspace and protected-service runtime cases remain gaps explicitly disclosed by the author. No Go parser/compiler/runtime claim is made.

## Authority and acceptance boundaries

Local OS administration and a recovery key are not Product Owner authentication. ProvisionPrincipal and IssueCredential in the tests create public synthetic fixtures; placeholder program bytes are not historical executable provenance. Program hashes prove stable bytes only. Qualified historical/target executable, real Owner flow, explicit legal additive-session transition, exact21-to22 compatibility, subsequent22-to24 validation and single-writer cutover remain OPEN. Pure21 is an isolated candidate; the existing startup guard remains unchanged.

## Audit and handoff

This review wrote only its new review namespace. No Git, Go, SQLite, native product, private-key, paid-model, Main or canonical operation was run. Original read I/O is preserved. One original PowerShell invocation emitted two nonterminating nonexistent-path errors (HANDOFF.json and MANIFEST.json); Root assigned one ordinal903. Outer exit0, Python/native NULL. It is not counted twice. Author failures900/901 are preserved upstream and unchanged. All source guard pins were rechecked and released. STOP/FINAL after handoff.

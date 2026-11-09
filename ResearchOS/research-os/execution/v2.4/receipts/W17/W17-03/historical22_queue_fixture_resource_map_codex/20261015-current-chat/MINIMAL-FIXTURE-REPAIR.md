# Historical source22 ActiveQueueRecovery fixture: bounded follow-up

The current combined candidate and clean Main4f both fail `TestConfigurationUpgradeActiveQueueRecovery` at `backup_configuration_upgrade_test.go:145` with `no such table: client_command_identities`. Its fixture has source22 SQL, while it calls the current `ClientService.Execute`, whose command-identity path requires table 0023. This is a baseline fixture mismatch. Keep both native failure receipts unchanged.

## Proposed separate scope

- Candidate-side allowed file: `internal/domain/backup_configuration_upgrade_test.go` only. Replace this test's pre-upgrade public-command setup with an import of a closed source22 fixture. Keep the 22→23 `UpgradeLocal` and recovery assertions, including the original Run, effect, queue and idempotency continuity checks.
- Historical-side allowed addition: one test-only `internal/domain/active_queue_fixture_child_test.go` in a **new isolated copy** of the pinned 502-file source22 compile inventory. It must invoke source22 `queueUpgradeFixture`, apply the source22 0022 queue migration plus `next_v24_sessions.sql`, and call that source's `ClientService.Execute` for the real `goal.start`, `session.send` and control commands. Export a closed SQLite fixture and structured receipt. Declare any additional file before writing it.
- Build from the existing 502-file tar/manifests with Go 1.27.1 and frozen `go.mod`/`go.sum`; pin the added helper separately. Do not alter the historical archive or the current exact53 candidate. `old22-control.exe` and the frozen release root remain independent native checks; the administration binary by itself does not seed this queue fixture.

## Fresh evidence required

1. Record every source22 input hash, helper source hash, compiler/module inputs, actual build argv/cwd/env, test executable hash and native exit. Recheck the selected tar against `git_source.json` and retain the absent Git tree as a limitation.
2. From the helper, prove numbered SQL max version 22 and absence of `client_command_identities`; capture actual source22 public command replies plus queue, receipt, control, Run, effect and idempotency rows. Preserve a closed pre-upgrade SQLite hash. Never add 0023 SQL to the source22 fixture.
3. In a fresh candidate-side run, consume exactly that fixture, perform 22→23 upgrade and verify original rows and recovery fences, with zero external dispatch and no skipped test. Preserve actual stdout/stderr and source guards before and after. A new failure requires its own diagnosis; prior failures stay in the record.

The old commit object `396287cc5427eb125aaedb8a2b7fadf63e6b9322` exists, but its tree `458e375ec2be0b989bb9b9e3d487f969e3c62966` is missing locally (`git cat-file -t` exit 128). The 502-file tar and existing frozen source match their recorded manifest byte for byte. A new Git worktree cannot be assumed available from this object store, and this resource mapping created none.

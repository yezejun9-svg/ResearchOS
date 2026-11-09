# Shared recovery observation fence: bounded Source blocker

Status: SOURCE_BLOCKED / FIX_NOT_IMPLEMENTED. This packet records a concrete compatibility blocker and does not mark the overall goal blocked.

Root has full implementation authorization and chose to separate compatibility-route work to preserve existing recovery guarantees. This is an engineering branch decision, not a missing user permission or request for additional user approval. No production candidate, UDF, schema, old trigger or historical template is changed here.

## Confirmed source facts

1. migrations/sqlite/0005_runtime.sql declares runtime_observations.epoch INTEGER NOT NULL CHECK(epoch>0). The old runtimeObservation binding of a legitimate json.Number may be converted by SQLite; no causal link from that binding to the earlier six ACK failures is established here.
2. client_session_fence.go's client_session_require_fresh selects observations by project/run and TEXT time only. It lacks o.epoch equality with the current Run lease_epoch and lacks observation spec run/task/epoch plus receipt/native binding validation.
3. backup_recovery.go's backup_require_fresh_observation uses json_extract(NEW.body,'$.lease_epoch') > json_extract(OLD.body,'$.lease_epoch'). Malformed/missing nonnumeric JSON epochs can make the condition NULL/false and skip the fresh-observation guard. It also compares RFC3339Nano TEXT with >.
4. runtime.go selects ORDER BY observed_at DESC LIMIT 1. Variable fractional precision and UTC offsets are not chronologically ordered by raw strings. For example .1Z sorts after the later .11Z; Z sorts after a positive fractional second in the same second.
5. ATT3's Go attach restore path already parses times and checks current-epoch evidence. Its immutable candidate is pinned here as context; it does not replace either shared SQL trigger.

These are source-level findings. This author did not execute the exploit cases, Go, SQL, a native runtime or a model.

## Why a direct trigger edit is not a safe completed repair

Service.New in internal/domain/store.go calls CheckMigrationSafety before its installClientSessionFence call. On a populated current-version database, backup_migration.go builds an expected in-memory schema by calling the shared installer. migrationSessionSchema includes every raw SQL definition belonging to client_sessions and backup_restore_barriers. It then compares Hash(got) with Hash(want).

Changing client_session_require_fresh SQL changes the expected hash; a valid existing populated schema24 database still has the old trigger and is rejected with MIGRATION_PREBACKUP_REQUIRED before the repair installer runs. Conversely, retaining CREATE TRIGGER IF NOT EXISTS leaves that old trigger unchanged.

The same installer also defines historical source templates:
- upgradeQueueTemplate in backup_queue_upgrade.go constructs the source21 schema later checked before 21->22 upgrade.
- upgradeConfigurationTemplate in backup_configuration_upgrade.go constructs the source22 schema later checked before 22->23 upgrade.
- preparedUpgradeTemplate in backup_prepared_abandonment_upgrade.go constructs Source23 and Original24/Restored23/Restored24, with exact Source23 checks before 23->24 rehearsal.

Replacing the shared installer without preserving exact historical definitions and an explicit compatible transition would silently redefine those old source expectations. This packet does not bypass, normalize away or relax any schema guard.

The precise next branch is an authorized recovery/upgrade route that recognizes the exact prior fence definitions, preserves the 21-24 historical source templates, changes only the intended fence definitions atomically in the approved target, leaves all existing rows/authority and schema version 24 intact, and proves rollback plus old-source immutability. Root will arrange that route and independent review separately.

## SQLite public API and process compatibility

The fixed local modernc.org/sqlite v1.60.1 official source was inspected and frozen. sqlite.go documents RegisterDeterministicScalarFunction and its driver.Value callback. driver.go states registration must precede the first Open; package-level registration applies to the package's registered sqlite driver, and Open installs its functions on new connections. A domain package init could register deterministic parsing helpers for the current program without private inputs or go.mod changes, but it would not give those functions to an older executable.

A persisted trigger calling a new UDF is therefore not backward-compatible with old programs lacking that registration. Matching-program backup, isolated restore/template construction, and old-program access all require an explicit tested compatibility policy. No such UDF is installed in this packet.

## Required repair and validation plan

The eventual implementation should parse RFC3339Nano using Go time.Parse and exact time ordering, reject unknown timestamps/epochs without widening casts or floating-point julianday, bind a Num-validated int64 epoch in runtimeObservation, and validate the existing producer's row/body/receipt/current Run relationships. Native dispatch fields must match actual durable dispatch identity and receipt facts when a dispatch exists; fixture absence must retain the existing bounded nonnative contract. No new Owner signatures or invented observation fields may be added.

Selection must consider the truly latest current-epoch observation. A later/equal-time malformed or partial record must not be hidden by an older positive. Invalid evidence should fail closed; valid ordinary active/settled and recovery flows require positive coverage. Exact validation vectors are in planned-cases.json. They are planned discriminating cases, not executable tests or PASS claims. A real fresh native restore positive remains OPEN/PENDING_ROOT_RESOURCE.

## Actions and closure

Only this new receipt namespace was written. There are zero candidate production files and zero candidate test files. No Go parser/compiler/gofmt/test, SQL connection, native child, model call, private credential read, old Source rewrite, T6/Main/canonical mutation, migration-version change or schema24 change was performed.

All 45 declared T6, fixed public driver and ATT3 input refs are pinned; frozen copies of directly inspected T6/driver inputs preserve their bytes. sourceguard.final.json closes those same refs. It does not claim a baseline for Root's concurrently changing canonical or T9 state.

Actual mechanical read failures are recorded once:
- 870: sfRead2 rg --files .local used T6 cwd, where that directory is absent. chunk cf5d4a, outer 1, Python/native NULL.
- 872: sfRead7 passed unexpanded Windows backup*/migration* path arguments to rg. chunk 97d616, outer 1, Python/native NULL. Corrected query uses -g patterns.

Root's 871 is external to this packet and is not duplicated. Failure counting is not reset. Original tool inputs and returned outputs are retained, including successful corrections. Freeze/seal Python only inspects source text, hashes bytes and writes bounded evidence. Its success is not product acceptance.

Verdict: SOURCE_BLOCKED, shared fence repair not implemented; independent review and Root compatibility branch remain required. STOP.


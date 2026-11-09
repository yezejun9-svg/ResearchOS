# R2 release-operation schema — independent narrow review

Verdict: **NEEDS_FIX; do not integrate this SQL yet**.

Scope is only `migrations/sqlite/0019_evolution_release_operations.sql` and its
database invariants. No R2 state-machine, SCM, live publication or product
acceptance conclusion is made.

Reviewed worktree HEAD was `d95d61891d1d241767f18946fea989b7089b9460`, with six
concurrent author modifications/untracked implementation files. They were not
changed. SQL and `release_sql_windows_test.go` have no diff from evidence source
`080a5432530d889b8a3501e3890f247ee3002d86`.

SQL SHA-256: `77f49c55c6d0d7f92c4a6f3af001f812ae35ba736af66cd293c9abe1c10c98a4`.

## Blocking schema findings

1. **P1 — direct INSERT bypasses the lifecycle.** Only UPDATE transitions are
   guarded. A new row can be inserted already PROJECTED with a shaped receipt
   digest and positive projection revision, without PREPARED, DISPATCHED or
   OBSERVED history. Add an insert guard requiring the initial PREPARED state.
   Existing CHECK constraints will then require null receipt and zero revision.

2. **P1 — REPLACE bypasses immutable identity and the no-delete trigger under
   default SQLite settings.** `INSERT OR REPLACE` on the primary key can remove
   the old operation and insert a new operation/epoch/admission/effect tuple.
   With `recursive_triggers=0`, the implicit deletion does not run the nodelete
   trigger, and this is not an UPDATE. Enforce absence of all three unique keys
   in a BEFORE INSERT guard (project/candidate/action, operation_id, effect_key)
   or provide an equivalently reliable schema rule. Do not depend only on an
   optional per-connection PRAGMA. Test collision cases for every unique key.

3. **P2 — INTEGER affinity does not ensure integral epochs/revisions.** The
   existing positive/nonnegative checks permit REAL 0.5 as expected_epoch and
   projection_revision. Require integer storage type, or an equivalent strict
   schema rule, in addition to the range checks. Test fractional and nonnumeric
   inputs. Epoch and revision are discrete protocol values.

All three findings were confirmed with four bounded probes using Python SQLite
3.50.4 and fresh `:memory:` databases. They loaded the exact reviewed migration.
No real service database, filesystem ledger, native process, protected path or
previously blocked operation was touched. The exact results are recorded in
`probe-results.json`. These probes are new schema-only diagnostics, not a rerun
of the native suite or R2 state machine.

## Existing evidence and constraints that do hold

Read `ops/supervisor/release_sql_windows_test.go` and the original six-test raw
run under `execution/receipts/W16/release-supervisor/9e0654fb-b639-49d8-bab1-d5c2200c54e9/`.
The recorded six tests pass, including `TestReleaseOperationSQLTransitions`.
Independently recomputed raw stdout SHA-256
`15669bf8da4196ba8bd26e679192e0737b9c28d3a08529189f1811b560676ef0`
and empty stderr SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
both match the original report. SQL-test source SHA-256 is
`b50930d9bc762a5af89846baffa337107a21daf4d03d9c01ac9bc96690f1ef2f`.
That test checks one duplicate INSERT plus ordinary UPDATE/DELETE behavior; it
does not cover non-PREPARED INSERT, REPLACE, or dynamic SQLite value types.

For ordinary INSERT/UPDATE without those gaps, the SQL correctly declares the
primary/unique keys, action enum, lowercase 64-hex hashes, immutable binding
fields, receipt binding, no same-state receipt/revision edits, PREPARED-to-FAILED
only before dispatch, and DISPATCHED-to-OBSERVED-to-PROJECTED transitions. Direct
DELETE is rejected. The schema comment correctly states that the supervisor-owned
journal, not the candidate-writable database, is the mechanical slot authority.
Fixing this table will not establish release authority or complete R2 integration.

Required next step: author makes the minimal SQL and SQL-test correction and
provides exact new bytes plus the narrow regression raw. Keep the old six-test
receipt unchanged. No native or full-suite rerun is needed merely to repair these
database guards. Re-review the new SQL before assigning the migration to main.

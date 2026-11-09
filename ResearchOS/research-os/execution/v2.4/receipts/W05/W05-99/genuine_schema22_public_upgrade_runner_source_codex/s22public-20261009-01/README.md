# Public schema22 runner Source

Status: SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION.

The callable implementation is public22_runner.run_registered_case(contract_ref, request_ref, live_root_scope). It has no standalone activation CLI. Its Root scope is a live capability supplied by a separately reviewed Root caller; request JSON cannot grant authorization. This package neither registers a request nor implements the Root authorization/lease service.

First available experiment: request end_version=22. Four finite public invocations run pinned old22-control --bootstrap-owner, then pinned old22-backup keygen/create/restore. The data root is new and owned by this case. The Owner credential and recovery key remain in its private directory and their bytes are never emitted. The profile has a real schema22 ledger and session/queue schema but no populated sessions/queue; it is not original user state or original cutover authority.

After public backup the original22 database/data-root files and encrypted22 backup files are marked read-only and held with FILE_SHARE_READ_ONLY for the remainder of the experiment. Their exact hashes and observed attributes are retained. Read-only SQLite observations report ledger/schema/per-table counts and hashes without raw rows. Public restore must produce the same JSON as persisted restore-report.json. Original22 and its encrypted backup/key remain available; there is no automatic retry, recovery or deletion.

The end_version=23 path is implemented: an exact byte copy of the sealed original22 database is passed to current Main ops/backup upgrade-local with schema22-to23-host-model-configuration-v1; its actual output is then passed to public create/restore verification. This path requires Root to bind a newly qualified current Main program. The previously reviewed main-backup23.exe is a candidate only: current backup_host_configuration.go differs from its old compile vector. The other four inspected public source entries match that vector. The runner refuses the unrebound candidate.

End_version=24 is rejected. Current Main lacks backup_prepared_abandonment_upgrade.go and 0024_prepared_run_abandonment.sql; the formal Boundary references their candidate worktree versions. This package invokes no private migration helper and makes no full22to24 or20to24 claim. Missing schema21 programme provenance remains OPEN.

Root must independently review this Source using a reviewer other than its author, create/register the first actual request and owner/scope/lease, freeze the Python/native runtime closure, and supply the live Root capability described by contract.json. require_registered is called before any output/process side effect; require_phase must recheck the current lease/scope before each public child. A fresh target23 qualification is a separate Root binding when requested. This source package has no self-review reference.

Future runtime receipts include actual argv/cwd/filtered env, raw stdout/stderr, PID+creation FILETIME, observed child exit and owned-Job cleanup. Unknown exits remain null. The first failure stops the case and records phase/publication/recoverability; Root assigns any original failure ordinal and must not treat the outer caller's exit0 as runtime acceptance.

49 pure Source controls passed. They cover output traversal and version rejection, exact refs, stale Main candidate rejection, Root denial before reads, argv/dataflow separation, public emitted/persisted receipt equality, unknown exits, incomplete Job cleanup, ledger/profile boundaries and read-only observation. They do not constitute Native, public CLI, SQLite or migration runtime evidence.

No Source in Main, Canon, Registry or prior evidence was modified. Formal acceptance remains false.


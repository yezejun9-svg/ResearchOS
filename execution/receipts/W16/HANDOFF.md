# W16-G02 executor evidence handoff

Latest applicable fixture report:
`f1e68e3d-e065-46f9-a293-fca3ea8c6038/report.json`.

Source commits, in order:

1. `03ff319`: eleven W16-owned files, bounded native core, fixture migration 0015,
   suite, native test executable, strict runner, tests and scope documentation.
2. `1d79f77`: shared `http.go`, `contracts.go`, `acceptance.go` dispatch only,
   21 added lines. Root must merge these hooks serially with W15 changes.
3. `881e42e`: saves the raw C12 rollback trigger journal in addition to the full
   execution/backup/restore evidence. Latest run freezes this source commit.

Runner: `python ops/ci/evolution.py --mode fixture`, with
`RESEARCHOS_TASK_ID=W16`, `RESEARCHOS_CHECK_ID=W16-G02`, and an empty
`RESEARCHOS_CASE_ID`. The pinned Go path defaults to the existing lock file.
Alternatively set exactly one C09/C10/C12/C20/A16 case and no check selector.
G01/G03 and LIVE mode are rejected, not downgraded to fixture success.
Root owns registration of the `test.evolution` command key.

Latest observed execution: exit 0; all 18 expected assertions, no missing or
unexpected assertions. Distribution: C09 3, C10 3, C12 5, C20 3, A16 PARTIAL 4.
Formal numbered assertions C09-01/02, C10-01/02/03, C12-01/02/03 and C20-01/02/03
are present; six additional assertions cover required behavior, admission,
stable continuity, and startup-failure/timeout fixture paths.

Runner integrity: two unit tests cover exact success and nine false-success
conditions. CLI rejection logs prove G03, dual selectors and LIVE return 2.
`evidence-integrity.json` verifies 19 raw file hashes and 136 source hashes.
Earlier successful report `2bbe6d8d-aa84-4b01-a9dc-137928be7a05` is retained.
Development failure and repair logs are retained under `development-failures`.
The manual evidence audit initially used Python's GBK default decoding and was
retried with explicit UTF-8; no tested source changed for this audit correction.

Status: EXECUTION_REPORTED; independent repository acceptance NONE.
G01 NOT_ACCEPTED; G03 BLOCKED_W14_LIVE; formal A16 PARTIAL_FIXTURE_ONLY.
No production scheduling, automatic upgrade or data switch was exercised.
No independent OS service, host crash/restart reconciliation, remote provider,
formal holdout, model-weight update, Windows installation or UAC path is claimed.
W18 restores real temporary SQLite data to a fresh isolated copy, verifies the
inventory, and the exact old native binary passes health checks. Public fixture
jobs continue under the development host; this does not establish production
supervisor independence or LIVE recovery qualification.

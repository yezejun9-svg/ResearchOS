# 0019 release-operation schema correction — independent review

Verdict: **PASS_SCHEMA_ONLY; exact SQL may be integrated independently**.

All three findings in `../review.md` are closed by source
`4494f86f00007f1386c37b5e149eaf38586300db`, with directed raw evidence committed
at `7ea7f807559f28156909eb0ca92ce6eae59c8b37`. The original NEEDS_FIX report
remains valid for its older SQL bytes and is not overwritten.

Approved file: `migrations/sqlite/0019_evolution_release_operations.sql`.
Exact working-file SHA-256:
`54ff6eb7a7ca588df738f5bd68b6f6851d86916cef435abaac15d1f8bd6e131e`.

The source delta contains only this SQL and its directed SQL test. The author
receipt describes a clean detached-source execution; the ongoing R2 worktree
observed during this review has concurrent implementation edits and is not claimed
clean. Reviewer did not change any author source or evidence.

## Closed findings and validation

- A BEFORE INSERT guard now requires PREPARED. Existing CHECK constraints also
  require its null receipt and zero projection revision, so direct terminal-state
  insertion cannot bypass the lifecycle.
- That guard rejects an already-present project/candidate/action, operation_id,
  or effect_key before REPLACE can delete an existing row. The directed test
  exercises all three collision forms. No recursive_triggers setting is needed.
- Epoch and projection revision now require `typeof(...)='integer'` plus their
  positive/nonnegative ranges. Fractional values are rejected, including a
  fractional revision on the legitimate OBSERVED-to-PROJECTED update path.

Read the complete changed SQL and SQL test. The original update constraints remain
in place: immutable identity/admission fields, immutable sealed receipt, no
same-state receipt/revision edits, PREPARED-to-DISPATCHED or no-dispatch FAILED,
DISPATCHED-to-OBSERVED-to-PROJECTED, and no direct DELETE.

Independently repeated four schema-only diagnostics against fresh in-memory Python
SQLite 3.50.4 databases using the exact approved SQL. Direct PROJECTED insertion,
fractional epoch, primary-key REPLACE and fractional projection were all rejected.
The same row then completed the legitimate lifecycle with original operation ID
and integral projection revision 1. No actual database, native process, release
slot or supervisor journal was used.

Read and parsed the supplied clean-source directed Go JSONL. It records
`TestReleaseOperationSQLTransitions` PASS and zero failures. Recomputed SQL/raw
hashes agree with the report:

| Evidence | SHA-256 |
| --- | --- |
| stdout.jsonl | 0548ba797715d9a7c8aa7b4a10b02a1298e464248169c75e4dd4badb8b2481da |
| stderr.txt | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| report.json | 35846af030703cf8fee27e5dfdfe82c42745de3b554eaad90c4b4032886d47f2 |

Full probe results and raw hash checks are in `independent-recomputation.json`.

## Integration boundary

This PASS permits integration of the exact 0019 SQL bytes as the schema prerequisite
for later 0020 work. It does not claim combined migration/NewDB compatibility;
root must run that check in the actual combined tree. It does not accept the R2
state machine, public HTTP flow, receipt projection, actual SCM identity or live
release. The candidate-writable database remains an effect ledger; only the
separate supervisor-owned journal can be mechanical slot authority. No formal
acceptance case is upgraded by this schema review, and no unrelated native suite
was rerun.

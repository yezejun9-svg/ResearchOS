# W06-01 resume pack (measured 2026-10-03, checkpoint rev 117, commit 56ca4808)

## Done and verified on disk
- `internal/domain/acceptance_transaction_w0601_test.go` — 7 `W06-01-*` ids, all PASS, rc 0, run
  with the pinned `.local/tools/go1.27.1/go/bin/go.exe` and `-v`:
  `TX-ACCEPTED-201` (201), `TX-NO-LONGER-REPORTED` (status now `ACCEPTED`),
  `TX-SUCCESSOR-RELEASED` (`READY`), `TX-OUTBOX-APPENDED` (outbox 20 -> 24),
  `TX-RECEIPT-PERSISTED` (AcceptanceReceipt 0 -> 1),
  `TX-STALE-PRECONDITION-REFUSED` (reused pre-transaction tag -> 412 `STALE_REVISION`,
  current_revision 7), `TX-STALE-REPLAY-NO-SECOND-RECEIPT` (1 -> 1).
  Raw log: `w0601_tx_run.txt` (copied out of `.local` and hashed in the checkpoint).
- `tests/orchestration/expected.json` gained the test name -> those 7 ids; the id list was parsed
  out of the run log and asserted (7 rows, all PASS) before writing, not typed.

## NOT done - do not present this card as reported yet
1. `test.orchestration` is still **UNBOUND**. The 7 ids above are proven only by running the Go
   test directly. Binding needs two edits OUTSIDE this card's write_scope:
   `execution/v2.4/commands.json` (owner W02-02) and the selector -> test-name map in
   `ops/ci/orchestration.py`. Recorded as obligation `W06-01-selector-registration-owner`.
2. Remaining card step-4 negatives, in write_scope, still to write:
   `self-approval` (executor signs its own acceptance), `high score but a required check failed`,
   `one hard gate missing`, `state changes between rechecks`. Model them on
   `TestW06AcceptanceRecheck` (scenario loop) in `internal/domain/acceptance_test.go:117`.
3. Then: EXECUTION_REPORTED receipt + artifacts (derive digests from disk), fresh-identity
   independent review, register ACCEPTED.
4. `W06-G02` stays parked: RESOURCE_BLOCKED because `codex.exe` is absent
   (`orchestration_context_test.go:50`); `live_qualification="BLOCKED"` in the report is a
   hard-coded constant at `ops/ci/orchestration.py:115` and explains nothing (see
   `FINDINGS_INCREMENT_1C_G02_CAUSE.md`).
5. Format slip to avoid repeating: the rev-117 write reflowed `checkpoint.json` wholesale
   (`indent=1`); the file's committed writer format differs. Use targeted string replacement with
   a count assert for future bumps.

## Reproduce
    .local/tools/go1.27.1/go/bin/go.exe test ./internal/domain -count=1 -timeout=3m -v \
      -run '^TestW06AcceptanceTransactionAndStalePrecondition$'

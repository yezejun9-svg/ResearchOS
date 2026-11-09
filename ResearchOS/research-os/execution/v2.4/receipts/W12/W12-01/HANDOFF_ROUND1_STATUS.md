# W12-01 - where this stands, for whoever resumes

Written 2026-10-03T04:19Z by `qoder-desktop:/root/construction`. This file is the card's own
handoff; `execution/v2.4/checkpoint.json` (now revision 32) is the repository-wide one.

## Facts, not intentions

| item | value at writing |
|---|---|
| HEAD | `02eb4e6e` (checkpoint rev 32) |
| accepted cards | 15 of 71 |
| parent tasks accepted | 0 of 22 |
| formal cases finally verified | 0 of 42 |
| W12-01 status | `EXECUTION_REPORTED`, `verifier_id` null, not registrable |
| round-1 verdict | absent (`independent_review_round1.json` does not exist yet) |
| binding command | `python execution/command_dispatcher/dispatch.py test.resources --task-id W12 --check-id W12-01` |
| last measured result | PASS 31 assertions, twice, identical id sets, invocations `0409a925-...` and `1f85ff36-...`, both pinned to code_revision `f9a54e3c` |
| mutation matrix | 10 cases, 10 caught by named ids, 0 survived, 0 crashed, 0 anchor-missing |
| executor self-audit | 42 recomputed rows, 0 inconsistencies; the harness stdout in the frozen invocation carries the same 31 ids, same prefix histogram, same 2 disclosure rows, same scope string |

## Frozen while the reviewer works

`internal/domain/**` and `tests/resources/check/**` are what the round-1 reviewer builds and runs.
Do not edit either, and do not start a second heavy Go evidence suite next to the reviewer's run -
that concurrency produced a false flake in an earlier round. A missing verdict is not a dead
reviewer: do not dispatch a replacement identity just because the file has not appeared.

## Branch A - verdict ACCEPT or ACCEPT_WITH_RESERVATIONS

1. `cd` to the repository root and run `python execution/v2.4/receipts/W12/W12-01/register_w1201_accepted.py`.
   It reads `cp["revision"]` dynamically, so it moves 32 -> 33, appends the ACCEPTED step to
   `step_state.json` with evidence digests, and refuses outright if no verdict file is present or
   if the verdict predates a rejection or reuses an identity that already reviewed this card.
2. Copy any reservation the verdict names into `open_obligations_before_next_card` in the same
   write, and only then re-select the next card with `tools/task_packet.py`.
3. W12-02 is gated by W06-01, so the next card is W06-01 (`internal/domain` must be unfrozen first).

## Branch B - verdict REJECT

Append the failure to `failure_counters` without zeroing anything, remediate inside the card's
`write_scope`, and request a **third, never-used** identity. Do not treat the rejecting review as
the post-remediation verdict, and do not edit any already-hashed evidence: corrections go in an
addendum plus a `record_correction` integrity event.

## Work this card disclosed instead of faking

- `W1201-START-REFUSAL-*` - a start-time cost refusal is unreachable dead code because
  `claimTaskMode` (`internal/domain/orchestration.go:347`) already refuses a non-registered
  FIXTURE runtime; the code was added in `5ae713ea` and removed in `15c429d6`. Any future attempt
  must assert the existing refusal, not add a branch.
- `W1201-ATTEMPT-BUDGET-*` - needs the failed-run lifecycle (terminal observation + report) owned
  by the accepted W05/W06 fixtures; `.local/apply_w1201_attempt_budget.py` is deliberately unapplied.
- DAILY and MONTHLY budget windows: product-implemented, unasserted; owned by **W12-99**.
- `createTask` mints a zero-counter `NoProgressRecord` for changed `input_refs` with no gate;
  that lives in `internal/domain/operations.go`, outside this card's scope.
- C11/C13 move attempt-to-attempt through the dispatcher while the underlying go tests pass 4/4;
  measured with and without this card's product change. The reviewer should re-measure.

## Tooling kept with the card (so evidence never depends on an untracked path)

`audit_receipt_w1201.py`, `audit_invocation_w1201.py` (both read-only), `generate_receipt_w1201.py`
(refuses to write an acceptance claim and requires two HEAD-pinned runs), `mut_w1201_round2.py`,
`register_w1201_accepted.py`, `POST_VERDICT_RUNBOOK.txt`, and `progress_note_1..3.json`.

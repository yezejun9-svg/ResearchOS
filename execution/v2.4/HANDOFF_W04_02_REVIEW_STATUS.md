# W04-02 review status (executor disclosure, written while the independent review is running)

This file exists because the previous construction window parked W04-02 mid-review, and the two
things a resuming session needs most are recorded here rather than in prose nobody can find.

## The first review request produced no verdict

A round-1 independent reviewer was launched as a background agent in the window that ended at
checkpoint revision 25. It never delivered
`execution/v2.4/receipts/W04/W04-02/independent_review_round1.json`, and no such file exists on
disk. It is therefore recorded as **not delivered**, not as a rejection: the failure counters were
not touched for it, no verdict was invented, and its numbers were never cited anywhere.

A fresh identity was asked instead, and its brief is stricter than round 1's was: re-run the check
and confirm the assertion-id set is identical across runs, read `tests/context/check/w0402.go` in
full hunting for assertions that cannot fail or are satisfied by the wrong layer, judge whether the
three `not_verified` skips are genuinely blocked by the W06 orchestration fixture and the FTS path,
re-run at least three of the fifteen mutations itself (including the conflict-keeps-both-sides and
freeze-from-live-state ones) and restore the tree exactly, A/B the declared pre-existing
`go test ./internal/domain` failures, and audit `git diff` against the card's write scope.

That reviewer's verdict lands in
`execution/v2.4/receipts/W04/W04-02/independent_review_round2.json` under
`qoder-desktop:/root/w0402_verifier_r2`.

## Registering the verdict, once it exists

`.local/register_w0402_accepted.py` (untracked by `.gitignore`, like all local tooling) performs the
acceptance mechanically and refuses when it should:

- it reads whichever `independent_review*.json` is present, takes the newest ACCEPT /
  ACCEPT_WITH_RESERVATIONS, and exits without writing if the only verdict is a REJECT;
- it exits if that verdict still names a `blocking_issues` entry while calling itself an accept, or
  if the `verifier_id` is missing or equal to the executor's;
- it recomputes the sha256 of every file in the receipt directory instead of copying numbers,
  appends the `W04-02` ACCEPTED record to `step_state.json`, asks `tools/task_packet.py next` what
  the next card is, moves `checkpoint.json` 25 → 26 with that step id, appends (never resets) a
  `failure_counters` row carrying the three disclosed incidents above, and turns each review finding
  into an open obligation;
- `--dry-run` prints which verdict it found and changes nothing.

Run it only from the repo root with the locked environment already exported. Its checkpoint guard
will fail loudly if the revision has moved, which is the intended outcome rather than something to
edit around.

## What is currently in the working tree, and whose it is

`internal/domain/changes.go` and `internal/domain/context.go` show as modified while the review is
in flight. **Those two diffs are the reviewer's own A/B revert of the executor's product fixes** —
removing the `createContext` governing-decision merge and restoring the old self-contradictory
`resolveConflict` guard, so it can tell which `internal/domain` test failures predate this card. The
executor has no uncommitted change of its own: everything it wrote is in commits `f38b6d2c`,
`c6fca501`, `acbe4e0c`, `636c9e04`, `419c2e75`, `277fa05f`, `40babf14`, `38025c24`, `9353354c`. If
those two files are still modified after the reviewer reports, restore them from `HEAD`
(`git checkout -- internal/domain/changes.go internal/domain/context.go`) — that remediates the
reviewer's temporary mutation, it does not undo any accepted work — and re-run
`python execution/command_dispatcher/dispatch.py test.context --task-id W04 --check-id W04-02`
before registering, expecting PASS 239 with three skips.

`qualification/v2.4/mu/` is a pre-existing untracked vendor snapshot from 2026-10-01 with its own
`.git`; it is not this card's output and is not in anyone's scope.

## Nothing here is a completion claim

W04-02 is `EXECUTION_REPORTED`, not accepted, until a verdict file exists. 14 of 71 cards are
accepted at the moment this note is written, 0 of 22 parent tasks, and 0 of 42 formal cases finally
verified. The W04 parent gate still owes the migration-owned binding/stage/replay/Project tables
with store-level canonical-path uniqueness and a green CreateBackup/RestoreBackup re-proof,
`/v2/command` routing for `workspace.register` and `project.bootstrap` (owner of
`internal/domain/client_protocol.go`), a real native directory chooser behind `internal/host`'s nil
argument, the Goal/Task chain that `bootstrap_task_id` will name, W08's promotion of RESEARCH /
REUSE_DECISION / IMPLEMENTATION, and the W04-99 formal cases.

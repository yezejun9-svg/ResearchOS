# W04-02 review status (executor disclosure, written while the independent review is running)

This file exists because the previous construction window parked W04-02 mid-review, and the two
things a resuming session needs most are recorded here rather than in prose nobody can find.

## The first review request produced no verdict

**Corrected immediately, because it was wrong when written:** at the time of writing no verdict file
existed, which was true then and false minutes later. Round 1 completed and is described in the section
above. The claim in this paragraph is kept rather than deleted so the record shows what was actually
known at each step.

A round-1 independent reviewer was launched as a background agent in the window that ended at
checkpoint revision 25. It had not delivered
`execution/v2.4/receipts/W04/W04-02/independent_review_round1.json` by the time this note was first
written. It was therefore provisionally treated as not delivered. It was not: it completed and returned a
REJECT, which is now the binding verdict for this round and is summarised in the section above rather
than here.

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

## SUPERSEDED by the round-1 verdict: W04-02 is REJECTED at checkpoint rev 26

Round 1 did not die. It finished and delivered
`execution/v2.4/receipts/W04/W04-02/independent_review_round1.json` with verdict **REJECT**
(`qoder-desktop:/root/w0402_verifier_r1`, reviewed_at 2026-10-02T13:33:23Z). Everything below this
heading still describes how the registration script behaves, but the card is not registrable right
now: the script was tested against the real verdict and correctly refuses with
"no registrable ACCEPT: the round-1 rejection stands and remediation is due".

What the reviewer reproduced and agreed with: PASS 239 three times with identical id lists, 0
failures, exactly 3 `not_verified` (40 CTX / 41 CHG), the binding line under its own invocation,
gofmt/vet/build clean, all fifteen mutation cases re-run with 14 caught and only the already-disclosed
Z3 surviving, plus its own revert of both product fixes killing exactly five named assertions before
restoring them hash-exact. It judged the product work good and explicitly said both fixes must stay,
and its scope audit over 22 files found no spec, contract or migration touched.

Eight items are recorded as obligations in `checkpoint.json` (rev 26, counters appended to 11, never
reset). The two that matter most are **new product defects that only became reachable because
`resolveConflict` was repaired**: a RESOLVED conflict stays in `blocking_conflict_ids`, so every later
freeze reports an open conflict that is closed; and the replacement guard has no relation check, so any
APPLIED change settles any conflict (a Requirement-text change settled a ProjectState conflict with
200). The third is that my `CHG-PROPOSAL-NAMES-ITS-IMPACT` skip was **false** - `createChange` does
populate `impacted_refs` and `impact_link_ids` deterministically (the reviewer measured 3/3), so naming
the impacted refs is this card's own step 3 obligation and was never W06's to inherit. The rest: assert
accept-authority with a principal that actually holds VERIFIER rather than leaning on the frozen
`x-required-roles` gate; read the next step / `resume_instruction` in at least one assertion; make
`CTX-TAMPERED-BUNDLE-REFUSED` unable to pass on either branch; correct the stale evidence text (two
more misquoted counts, `progress_note_1.json` has no hashes and its provenance list is short one file,
and the declared "six pre-existing legacy failures" pass in both A/B states - the honest A/B gives 3
per state with 2 common); and disclose that 2 of W04-01's 30 pinned hashes now differ.

**Executor mistake, disclosed in checkpoint `integrity_events`:** assuming round 1 had died, this window
launched `qoder-desktop:/root/w0402_verifier_r2` against the same card while round 1 was still running.
Two Go-heavy suites on one machine produced a flake round 1 observed and attributed to the overlap
(`TestRuntimeCoordinatorConcurrentSealConflict`, 1/2, isolated 0/3). That is the same concurrency
mistake the log already records once. Consequence, recorded as a gate rule rather than left implicit:
**round 2 cannot be the post-remediation verdict** - it started before the blocking items existed - so
its accept does not register the card, and a fresh identity must review the remediated tree.

## Registering the verdict, once it exists

## Round 2 also rejected: the merged remediation set is nine items

`qoder-desktop:/root/w0402_verifier_r2` finished too, also on the un-remediated tree, also **REJECT**
(7 blocking issues, `independent_review_round2.json`, reviewed_at 2026-10-02T14:10:00Z, checkpoint now
rev 27). It reproduced PASS 239 on four runs with order-identical id lists, re-ran 8 of 15 mutations with
the same failing id sets, proved both product fixes load-bearing by separate reverts, and A/B'd my
"pre-existing failures" claim down to one deterministic case - `TestW17UpgradeActiveRecovery`
(`no such table: runtime_dispatches`) - the other three being this machine's loopback flake. It also
confirmed the registry revision 11 does not weaken W04-01: its 158 accepted ids remain a strict subset of
the 239.

Five of its items are the same as round 1's. Three are new and matter:

- **B5** `CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE` (`w0402.go:351`) is **never emitted in any run**,
  because `store.go:165` refuses the receipt UPDATE as immutable. So `CTX-TAMPERED-BUNDLE-REFUSED` is
  green via the storage branch and the service-side integrity check has zero coverage. That is the real
  reason mutation Z3 survived - I had written it up as a "redundant defence", which was wrong.
- **B7** undisclosed drift inside an ACCEPTED card: 3 of W04-01 receipt.json's 30 artifact hashes now
  differ (`tests/context/check/legacy.go`, `tests/context/check/main.go`,
  `execution/v2.4/commands.json`); its 20 step_state pins are all intact. Disclosed by
  `receipts/W04/W04-01/pin_drift_erratum_1.json`, computed - nothing was re-pinned and W04-01's
  acceptance is not withdrawn.
- a mutation the reviewer invented itself: storing the caller's claimed revision instead of
  `state["revision"]` **survives at PASS 239** - a second surviving case the card's own evidence did not
  contain.

Non-blocking but worth closing while the file is open: the check can silently lose assertion ids
(`w0402.go:430-436`) with no count floor, and `contextPhase` returns on the first refusal - the exact
mistake pattern already recorded once in this construction's history.

**Remediation order for the next window, serialised (never two Go-heavy suites at once, and no reviewer
running alongside the work):**

1. product defects in `internal/domain/changes.go` `resolveConflict` - prune the settled conflict from
   `ProjectState.blocking_conflict_ids` the way `applyChange:547-557` does, and require that the applied
   change actually relates to the conflict and that the conflict is OPEN (B3, B4);
2. assert the recovered next step by value, not key presence: `resume_instruction` / next step, and
   `unresolved_items` content (B6);
3. un-skip impact naming - `createChange` fills `impacted_refs` and `impact_link_ids` deterministically
   via `closure()`, so `CHG-PROPOSAL-NAMES-ITS-IMPACT` is this card's step 3, not W06's (B2);
4. rebuild the accept-authority assertion on a principal that genuinely holds VERIFIER instead of
   accepting `403 || 409` from the role gate (B1);
5. give the tamper refusal a positive control that actually runs, fixing the never-emitted assertion and
   the Z3 explanation (B5);
6. correct the remaining evidence text: the two further misquoted counts, `progress_note_1.json`
   carrying no hashes and its provenance list short one file, the stale six-test legacy-failure list, the
   two skip attributions the reviewers judged mis-described (`CHG-OPTIONAL-RETRIEVAL-DEGRADES` is deferred
   in substance but wrongly attributed in the note; `CHG-PROPOSAL-NAMES-ITS-IMPACT` is not deferred at all)
   and the drift disclosure (already done via erratum).

Then re-run the check and the mutation matrix serially, and ask a **third fresh identity** to review the
remediated tree. `python .local/register_w0402_accepted.py` will only register an ACCEPT that postdates
both rejections and carries an identity that is neither the executor's nor either reviewer's; it moves
checkpoint 27 -> 28. Nothing here is a completion claim: 14 of 71 cards, 0 of 22 parents, 0 of 42 formal
cases.

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

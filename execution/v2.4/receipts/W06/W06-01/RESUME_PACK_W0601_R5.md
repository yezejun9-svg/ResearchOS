# W06-01 resume pack for round 5 (measured 2026-10-03, checkpoint rev 123, commit 0093dcf4)

Card W06-01 (复用并补足独立接受服务) is `IN_PROGRESS`, **not reported-ready and not accepted**. Four
independent reviews have all returned `REJECT`; each rejection produced fixes that were then re-measured.
Nothing was registered in `step_state.json` (still 19 ACCEPTED + 1 BLOCKED, no W06-01 row) and no revision
was advanced by a rejection.

## Where the loop stands
- 19 of 71 cards ACCEPTED; parent gates: only W00-99; formal cases accepted: 0. Objective remains 22
  parents + 42 cases, so this card is one slice of a much larger gate.
- 54 `W06-01-*` assertion ids across nine frozen logs in this directory: masking 12, partA 7, partB 7,
  partC 7, partD 3, partE 3, partF 5, partG 3, TX 7 (all parsed from disk, never typed).
- Gate parity re-measured twice after part G: 126 emitted = 126 frozen, 0 non-PASS
  (`w0601_g01_parity_after_partG_attempt1.txt`, `_attempt2.txt`).
- Falsifiability: `mutation_selfcheck_round6.json` = 17 mutations, **16 caught by card ids**, 0 gate-only,
  1 survived (V7b), `internal/domain/acceptance.go` restored byte-exact to
  `00ab622e93c4e891cc37881403cda99fa1da5595edd7c8bc8c9c1fe6e652856f`.

## What round 5 must do, in order
1. Re-run the card selection with the pinned toolchain and re-measure parity; do not reuse the numbers above.
   ```
   .local/tools/go1.27.1/go/bin/go.exe test ./internal/domain -count=1 -timeout=2m -v \
     -run '^(<names from tests/orchestration/expected.json except TestW06ContextContinuation>)$'
   ```
2. Decide **V7b** (`acceptance.go:67` reference currency) on their own measurement: the executor called it a
   coverage gap, the round-4 reviewer neutralised `:67` and got identical results across four constructions
   because `:31` refuses first, i.e. defence in depth. One of those two statements is wrong and the survivor
   list must say which.
3. Attack, don't confirm. Four reviewers each found something the previous ones accepted; three of my own
   "reasons" were overturned. Try at least the guards no id here names: `:208` output isolation (claimed
   externally unreachable, twice mis-reasoned), `:89-137` qualification binding, `:225` artifact vector.
4. Rule on **B-3**: `dispatch.py test.orchestration --task-id W06 --check-id W06-01` still answers
   `NOT_IMPLEMENTED`, exit 3, zero assertions. Four identities measured it (invocations 3b275b35, 0b097f12,
   98e4b702, 0f65b9ac). Binding needs a `commands.json` selector (owner: the already-accepted W02-02 card) and
   an `ops/ci/orchestration.py` route, both outside this write_scope. Round 4 stated this caps the card at
   `ACCEPT_BLOCKED_RECORDING`; round 5 should confirm or reject that framing.
5. Write `independent_review_round5.json` (new file, new identity key) with the same required fields as the
   earlier rounds, plus `round4_findings_retested` covering P-R4-1 (part G closed the `:14` id) and P-R4-2
   (side-effects measured statement).
6. Only then register: `.local/register_card.py` is not yet written for this card — the accepted pattern is a
   dry-run-first script that refuses if `checkpoint.expected_previous_revision` != disk revision, keeps
   `indent=1` bytes, and hashes evidence relative to `execution/v2.4/`.

## Things not to repeat (all of these cost a review round)
- Do not write shared files with `Path.write_text` on Windows: it converted all 117 LF lines of
  `tests/orchestration/expected.json` to CRLF (commit `94f2126b`, fixed in `2f093641`, disclosed in
  `scope_incident_disclosure_eol_reflow.json`). The registrar now uses `write_bytes` and asserts a +2/-1 diff.
- Freeze every attempt under its own filename. Reusing one path destroyed the masking attempt-1 log, so
  `FINDINGS_INCREMENT_3_MASKING.md:39` claimed a frozen artifact that does not exist (B-1; admitted in
  `precision_notes_round1_findings.json` P-1; unrecoverable).
- A survivor reason must be a measurement. "Backstop" for M8/`:146` and V4/`:348` was false (round 3 proved
  both reachable); "unreachable" for V6/`:14` was false (round 4 built the fixture). Part F and part G now own
  those ids.
- Never rewrite a hashed artifact. Corrections go in new files: `precision_notes_round1_findings.json`,
  `..._round2...`, `..._round3...`, `mutation_selfcheck_round2..6.json` (each round is its own record).

## Still blocked, honestly
- `W06-G02` / `TestW06ContextContinuation`: `codex.exe` absent (`orchestration_context_test.go:50`); 4 frozen
  ids; a skip is not evidence.
- Parent `W06-99`, formal cases A03/C07/C10: not claimed by this card.
- The rest of the objective is untouched: 52 cards unstarted, 21 parent gates open, 42 cases unaccepted.

# W05-01 resume note

Round 4 submitted, written at 2026-10-03T08:53:58.285878+00:00 (HEAD 28db611a, checkpoint revision 52).

- Round 3 verdict REWORK_REQUIRED (4 blocking) committed at 22dc53c4; all four are remediated at code HEAD c6fa8b18 and the round-4 receipt is at that HEAD: 31 assertions, 12 disclosed NOT_RUN rows, 19 matrix cases each killed by a named assertion, CLEAN self-audit. Evidence commits e790f321 and 28db611a.
- The register script was repaired before it was needed and its refusal path re-measured (exit 1, no writes).
- w0501_verifier_r4 is in flight and may write only independent_review_round4.json.

Next, in order:

1. Wait for independent_review_round4.json to appear and stay byte-stable for about ninety seconds. A missing artifact is not a dead reviewer; an appeared one may still be unfinished.
2. Commit the verdict verbatim, with no executor edits.
3. Register only on an empty blocking_issues array: python execution/v2.4/receipts/W05/W05-01/register_w0501_accepted.py. It now carries reservations as well as limitations into open_obligations and derives the accepted-card count from step_state.
4. If it returns REWORK_REQUIRED again, the pattern from three rounds applies: the finding is almost always a claim outrunning a measurement, so re-measure the whole tree rather than only the check program, and correct propagated text through integrity events rather than silent edits.
5. Still owed regardless of the verdict: the model identity comparison the decoder never populates, the dispatch-to-adapter wiring behind the Run correlation, and the 42-case and parent-task gates.

Standing: 16 of 71 cards accepted, 0 of 22 parent tasks, 0 of 42 formal cases. Not complete.

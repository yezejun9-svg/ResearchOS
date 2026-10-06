# W06-01 increment 3 — the card's three masking negatives (measured 2026-10-03)

Scope of this file: one increment of card W06-01. It accepts nothing. The card is still
`IN_PROGRESS`; the objective (22 parent tasks + 42 formal cases validly accepted) is unchanged.

Head before this increment: `441606b3` (W06-01 G02-wording commit).
Toolchain: `.local/tools/go1.27.1/go/bin/go.exe` (pinned, resolved from the locked table, not PATH).

## What is now on disk

`internal/domain/acceptance_w0601_masking_test.go` → `TestW06CardMaskingNegatives`, 12 emitted
assertion ids, all PASS, `rc 0`. Raw log: `w0601_masking_run.txt` (copied out of `.local`).

| id | what it measures |
|---|---|
| `W06-01-CONTROL-EXACT-MATCH-COMPUTED-PASS` | the service computes `PASS`/exit 0 for the exact frozen expectation |
| `W06-01-CONTROL-ACCEPTED-AND-SUCCESSOR-READY` | that same run reaches `ACCEPTED` and releases the successor to `READY` |
| `W06-01-NEG-MET-PARSE-COMPUTED-FAIL` | report bytes contain `"result":"verified"` (true) but not the whole `{"result":"verified"}` object (false); computed verdict/check = FAIL, exit 1 |
| `W06-01-NEG-MET-PASS-VERDICT-REFUSED` | 422 `GATE_FAILED` "requested verdict differs from independently computed checks", receipt-row delta 0 |
| `W06-01-NEG-MET-FAIL-VERDICT-ACCEPTED-NO-RELEASE` | honest FAIL verdict on the same bytes lands: receipt FAIL, task FAILED, successor stays BLOCKED |
| `W06-01-NEG-RENAME-RUNTIME-REGISTERS-AS-FIXTURE` | a runtime registered as `gpt-6-astra high-reasoning (qualified)` still carries `adapter=fixture`, `measurement_mode=FIXTURE` |
| `W06-01-NEG-RENAME-LIVE-CLAIM-REFUSED` | 503 `RESOURCE_UNAVAILABLE` "acceptance requires qualified native dispatch", receipt-row delta 0 |
| `W06-01-NEG-RENAME-MODE-STAYS-FIXTURE` | the accepted receipt on that run reports `verdict=FAIL`, `measurement_mode=FIXTURE` — the label bought no provenance |
| `W06-01-NEG-EXIT0-SUBMITTED-GREEN-CHECKS-NOT-IN-RECEIPT` | the request's own check row (PASS / exit 0) is absent from the receipt, which carries FAIL / exit 1 |
| `W06-01-NEG-EXIT0-RUN-DECLARED-ZERO-AND-SETTLED` | run `exit_code=0` and `runtime_settled_at` set, receipt verdict still FAIL |
| `W06-01-NEG-EXIT0-SUBMITTED-ACTUAL-DISCARDED` | the submitted `actual` text ("last command lint exited 0") does not appear in the receipt bytes |
| `W06-01-OUTPUT-ONLY-EXACT-MATCH-ACCEPTED` | SQL over the fixture: exactly 1 task `ACCEPTED`, titled `masking-control` |

Each refusal is paired with a control, so none of them can pass by being tautological: the same
bytes/labels that were refused are accepted once the verdict or mode is stated honestly.

## Mid-card failure, disclosed rather than hidden

Attempt 1 (`rc 1`, 3 rows emitted): `W06-01-NEG-MET-PARSE-COMPUTED-FAIL` failed on its FIRST term.
I had asserted `bytes.Contains(metRaw, []byte(`{"result":"verified"}`))` — the object *form* — but the
payload's extra keys mean the closing brace never follows `"verified"`. The service behaved correctly
(it computed FAIL, exit 1); my assertion was wrong about the string it was testing. Attempt 2 changed
the input (the assertion now measures both `"result":"verified"` present and `{"result":"verified"}`
absent), which is a new input, not a retry of identical input. Both logs are frozen here.

Also corrected in place, before any run: a 4-term want against 3-term got in the control row, and a
raw-integer duration for `IssueCredential`. Neither reached a measurement.

## Gate-parity measurement (why this is not a private win)

`tests/orchestration/expected.json` gained `TestW06CardMaskingNegatives` with the 12 ids **parsed out of
the run log and asserted (12 rows, all PASS, unique, no malformed row) before writing** — not typed.
Because `ops/ci/orchestration.py:17` builds `W06-G01` as `sorted(k for k in EXPECTED if k !=
'TestW06ContextContinuation')`, registering the key also widens the frozen G01 set. Measured after the
registration, with the runner's own name list, `-timeout=2m`, writing nothing outside the card's
write_scope (raw log: `w0601_g01_parity.txt`):

- 19 test names, `go test` exit 0, `ok ... 9.536s`
- emitted 91, unique 91, frozen 91, non-PASS 0, missing `[]`, unexpected `[]`

**This supersedes the earlier note that "G01 emits 72/76".** At this HEAD the G01 selector's frozen set
is fully covered. The runner's pass rule is `code==0 and not malformed and len(ids)==len(expected) and
set(ids)==set(expected) and all PASS` (`ops/ci/orchestration.py:109`), which this measurement satisfies
on the same inputs — but note it is a *parity* measurement taken outside the runner precisely because
the runner writes receipts under `execution/receipts/W06/`, which is **not** in this card's write_scope.

## Still not done — do not read increment 3 as the card being reported

1. `test.orchestration` remains an **unbound dispatcher key** (obligation
   `W06-01-selector-registration-owner`, owners W02-02 + `ops/ci/orchestration.py`). The 12 ids above
   are proven by direct Go runs, not by the card's binding line.
2. Card step-4's other five negatives — self-approval, stale input, one hard gate missing, high score
   over a failing check, state changing between rechecks — are **not yet written under W06-01 ids**.
   They exist today only as pre-existing `W06-G01-*` gate rows, and a gate id is not a card id.
3. `W06-G02` stays parked: `codex.exe` absent (`orchestration_context_test.go:50`).
4. No `receipt.json`, no independent review, no registration for this card yet.

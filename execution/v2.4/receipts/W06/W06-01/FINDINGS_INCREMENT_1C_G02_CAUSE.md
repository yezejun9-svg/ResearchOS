# W06-01 increment 1C — measured cause of the W06-G02 red (supersedes the wording in commit d2f5a680)

## What the previous note claimed

`FINDINGS_INCREMENT_1B_MEASURED.md` and commit `d2f5a680` recorded W06-G02 as "a live red in
the W06 line" without a cause, and the in-flight hypothesis I carried into this window was
"the cause is LIVE qualification being BLOCKED". **That hypothesis is wrong and is corrected
here.**

`ops/ci/orchestration.py:115` writes `'live_qualification':'BLOCKED'` unconditionally into
every report it emits — it is a constant label, not a measured gate. W06-G01 passes (72
assertions, exit 0) and its report carries the identical `live_qualification: "BLOCKED"` and
`independent_acceptance: "NOT_REQUESTED"` fields. So `live_qualification` cannot distinguish a
green run from a red one and cannot be the cause of a red. `real_model_verified` is
`passed and is_c01`, so it is also downstream of the outcome, not a cause.

## Measured cause (from disk, not from reasoning)

Run `execution/receipts/W06/continuation-live/ed7c5777-73b8-4d8d-80da-1c802870e632/`:

- `report.json`: `check "W06-G02"`, `case ""`, `status "FAIL"`, `exit 1`, `assertions []`,
  `malformed false`, `timeout false`, `missing` = the four expected ids
  `C01-01-CONTINUATION`, `C01-02-HISTORY-NO-ASK`, `C01-03-PROVENANCE`,
  `W06-G02-SUCCESSOR-ACCEPTED`.
- `before.json`: `selector "W06-G02"`, argv
  `<pinned go> test ./internal/domain -v -count=1 -timeout=2m -run ^(TestW06ContextContinuation)$`,
  `RESEARCHOS_C01_MODEL=1`.
- `stdout.txt` (242 bytes, verbatim):

  ```
  === RUN   TestW06ContextContinuation
      orchestration_context_test.go:50: exec: "codex.exe": executable file not found in %PATH%
  --- FAIL: TestW06ContextContinuation (0.58s)
  FAIL
  FAIL	researchos.local/research-os/internal/domain	0.880s
  FAIL
  ```

- `stderr.txt` is the empty stream (`sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).

`internal/domain/orchestration_context_test.go:50` is
`receipt, command := c01FreshAgent(t, next, bundle, …)` — the test's fresh-model agent driver.
It shells out for `codex.exe`, which is not installed on this machine, so the test `t.Fatal`s
before it prints any `W06_ASSERTION` line. The runner's pass rule
(`orchestration.py:108`) requires exit 0 **and** the emitted id-set to equal the expected set;
zero emitted ids therefore yields FAIL with all four ids in `missing`.

Three runs in this window (…`d869a3fd`, …`1445150c`, …`ed7c5777`) reproduce it identically —
same four `missing`, same empty stderr, same single-line `codex.exe` fault in stdout; only
`before.json`/`stdout.txt` digests differ.

## Corrected classification

W06-G02 is **resource-blocked, not code-broken**: a live model driver executable
(`codex.exe`) is absent from the environment. Per the standing rule that a missing resource
blocks only its own branch, W06-G02 is parked rather than "fixed"; `test.orchestration` stays
UNBOUND, because binding a route whose only W06-01-owned ids come from a resource-blocked
check would advertise a route that emits zero assertions.

Two consequences recorded so the next window does not re-derive them:

1. An earlier sentence in `FINDINGS_INCREMENT_1.md` — that fixture mode is independent of live
   resources — is contradicted by this measurement: `orchestration.py` runs the same Go test
   list regardless of mode (`is_c01` only adds `RESEARCHOS_C01_MODEL=1` and a receipt
   subdirectory), so a fixture-labelled `W06-G02` run still requires the live driver. That is
   a defect in the existing runner's fixture/live split, and it is in `ops/ci/` — **outside
   this card's write_scope**, so it is reported, not patched here.
2. The four `missing` ids are therefore not "ids nothing emits"; they are ids nothing emits
   *on this machine*. The correct statement of the gap is: `codex.exe` absent ⇒
   `TestW06ContextContinuation` cannot reach its assertion printing.

Counters untouched: `failure_counters` and `integrity_events` are not incremented by this
finding (no new failure of an accepted artifact; no new obligation).

## Next action for W06-01

Decide, with the card's own scope, which assertion ids W06-01 must own that do **not** require
the live driver (the domain acceptance transaction in `internal/domain/acceptance*.go` /
`orchestration*.go` plus their negatives). `test.orchestration` gets bound only in the same
change that adds W06-01-owned ids that pass on this machine; the G02 continuation branch stays
parked as resource-blocked with a `blocked_resources` entry naming the missing executable.

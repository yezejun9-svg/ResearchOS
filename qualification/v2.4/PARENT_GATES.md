# W01 current parent qualification

The four parent selectors use `parent_gates.py`. They never invoke the historical
live-provider harness or overwrite historical `qualification/v2.4/evidence` files.
Each invocation exclusively creates a UUID receipt directory under
`execution/v2.4/receipts/W01/W01-99`, including input hashes, assertion inventory,
commands and actual exits. Exit 0 means the selected qualification check passed;
exit 4 means BLOCKED. Neither accepts W01-99 or a formal case.

Run with the locked Python interpreter:

```powershell
python -B -X utf8 qualification/v2.4/qualify.py --check-id W01-G01
python -B -X utf8 qualification/v2.4/qualify.py --check-id W01-G02
python -B -X utf8 qualification/v2.4/qualify.py --check-id W01-G03
python -B -X utf8 qualification/v2.4/qualify.py --check-id W01-G04
```

| Gate | Mode | Evidence and boundary |
| --- | --- | --- |
| W01-G01 | DEVELOPMENT | Accepted authorized inventory predates candidate research; exact FOUND/NOT_CHECKED distinctions, 12-file upstream manifest, tightened source review. |
| W01-G02 | FIXTURE | Current installed CLI/Desktop identity and 29 observations; seven actual Go tests with explicit concurrent writer, stale epoch, dedupe, cancellation, recovery and executor self-acceptance negatives. |
| W01-G03 | LIVE_WINDOWS, FIXTURE data | Actual Windows portable qualification installation into an empty directory; every installed file matches package bytes; current compiled CLI/Host, real Electron 37.10.3 and native protocol, visible renderer/session/Goal/Task/writer continuation. |
| W01-G04 | DEVELOPMENT | Exact unchanged MU_FORK route/reuse/ADR and accepted independent review, sole bounded CUSTOM_GAP, unchanged carry-forward obligations and repair counters. |

The portable qualification installation is **not** a production final installer,
provider LIVE result, physical NVDA result or W13 full-card acceptance. No new
provider call, private credential/label read or service change was performed.
W01 owns no formal acceptance cases. The parent still needs independent review.

## Current immutable evidence

- Original seven-test command: `20261005T200612Z-6b39ef79143a`. All seven Go tests
  exited successfully. The first parent result remains BLOCKED because its old
  W18 source vector drifted and its parser initially failed on split Go Output
  events. The current parser reassembles per-test output and verifies all named
  negative assertions. The unchanged product inputs allow raw-output reuse.
- First installed sample: `20261005T200831Z-f27d7e6ef06b`. Normal GUI observations
  passed 15/15, but the optional preceding smoke probe timed out and aggregation
  encountered a Windows file-lock error. The original BLOCKED result is retained.
- Current installed sample: `20261005T201056Z-411792f6015e`. Startup, byte-exact
  installation, versions, 29 CLI/GUI assertions, business before/after counts,
  original file preservation and source stability passed. Final temporary cleanup
  failed because a Python sqlite3 context commits but does not close its connection.
- `cleanup-c1b3c49c4725/resolution.json` records the separate post-exit process
  absence and successful contained cleanup. The original BLOCKED receipt was
  never rewritten. The fresh installation implementation uses `contextlib.closing`.
  No third GUI run was needed to resolve a temporary cleanup-only failure.
- `validation-dacdafb563ef` contains ten strict negative/compatibility unit tests,
  exact four-selector exit-0 replays, and unknown-selector exit 2. Product/GUI
  observations were not repeated by those replays.

`parent_inputs.json` binds all reused raw receipts. The prior W18 GUI vector had
456 files and two changes (Desktop UTF-8 decoding and a W17 test addition); it is
not asserted wholly current. The new current sample covers the changed Desktop.
Candidate package revision is `7088d635d312...`; later main W11 integration adds
only two precisely hashed descriptive decision audit files. No changed existing
source or arbitrary added source is exempted. Their independent technical review
is imported byte-for-byte under `integration-provenance`; that W11 card remains
blocked. This is bounded functional evidence reuse, not execution of a newly
built integrated-main package. Additional backup fixture/build source hashes were
measured after observation against the unchanged Git baseline, explicitly labelled
as such in the cleanup supplement.

## Registry compatibility

Register `qualification/v2.4/dispatch_parent.py` under the v2.4 `core.qualify` key.
It reads only the standard `RESEARCHOS_TASK_ID`, `RESEARCHOS_CHECK_ID`, and
`RESEARCHOS_CASE_ID` selector variables:

- `W01`, exactly `W01-G01` through `W01-G04`, empty case: current strict handler.
- Omitted task, `W01`, `W02` or `W06`, empty check, empty case or `A02`: forward the same Python
  interpreter with `-X utf8` to unchanged `ops/ci/core_evidence.py`, preserving
  environment, standard streams and exit code. All eight legacy tuples are simulated
  separately in tests. The two omitted-task defaults were added after root found
  that the original selector validator only validates nonempty values. The original
  ten-test raw validation stays unchanged; the compatibility addendum records the
  expanded twelve-test run. No legacy provider/fixture command was run for this work.
- Any other tuple: NOT_IMPLEMENTED, exit 2, no child process. Future W02 gates
  remain unimplemented until their owner supplies a real handler.

The root integrator owns registry/state/checkpoint changes. The legacy registry
entry and historical child qualification handlers remain intact.

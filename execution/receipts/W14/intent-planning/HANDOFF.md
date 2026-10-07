# I1 frozen implementation handoff

Status: EXECUTION_REPORTED — independent review pending. Construction formal
acceptance is unchanged. The author does not accept this slice independently.

Source commits: `3a89a61` (Owner-bound natural intake) and `edb9543` (complete bounded
GoalBrief/native compilation slice), based on `b3a76a3`.

## Evidence

- `functional-test.jsonl`: PASS; 14 substantive top-level tests and 17 rejection
  subtests. Go reports 32 pass entries because the native child entrypoint returns
  without assertions when invoked as an ordinary test. No test failures.
- Native fixture: actual AppContainer qualification, planner Run, GENERATED JSON
  GoalBrief, independent Task/Goal HTTP acceptance, stable two-node business DAG,
  current purpose checks and both downstream nodes executed/accepted. FIXTURE only.
- `browser-9781943af47d43cfb5bd4c28d25cd3b3/report.json`: four real visible-browser
  functional checks passed; overall FAIL arose during cleanup (WinError32).
- `browser-d2ff0bd7b6a940ad8b2475b737f04489/report.json`: PASS, four checks and desktop/
  mobile screenshots. This run had already completed before root instructed no more
  complete browser reruns. The earlier failure was retained unchanged.
- `../../W13/frontend/3de0f6ce94ec499dbc812919aae17697/report.json`: original core UI
  run remains FAIL at resources/light/320 overflow, after changed entry/conflict and
  preceding regressions passed. The long reason-code wrapping was fixed in screens.
- `resources-320-cdb4b890e9934d78b5113c0cd037ef18/report.json`: only that affected
  320px resource viewport was rerun; PASS. Whole core suite was not rerun after fix.
- `final-ui-build.txt`: Vite build PASS. `git diff --check` passed before freeze.

## Hygiene blocker — retained, not retried

`BLOCKED_HYGIENE`: `.local/intent-browser-3lyxh0c2` remains. The initial Python
SQLite context manager left its connection open, causing cleanup WinError32;
the test was corrected to use `contextlib.closing`. Automatic approval then
rejected recursive cleanup of the boundary-verified dedicated fixture directory,
reporting only `blocked by policy`. No alternative shell or deletion method was
used. Root explicitly directed preserving this directory; do not retry its removal.

A later shell-based handoff-metadata generation command was also rejected with
`blocked by policy` while its data described that earlier cleanup. This handoff
was saved with the direct file patch tool; it performs no cleanup action.

## Deliberate limits

No actual production database/service was changed; no model/provider qualification,
semantic accuracy, protected verifier isolation or product E2E acceptance is claimed.
The private v1 catalog automatically compiles only complete positive Owner JSON
delivery instructions, matching literal/count/order. General business checks,
unknown questions and unsupported actions stay explicit NEEDS_INPUT/resource gaps.
Proposals remain GENERATED and suggestions remain PROPOSED. A JSON mention or
prohibition is not delivery authorization.

Independent acceptance still requires an existing authenticated VERIFIER. Proposal
revisions beyond v1 and business answers changing frozen plans require an explicit
new planning/W04 implementation. Ordinary LIVE business Goal acceptance stays
closed. See `tests/intent/README.md` for exact supported scope.

The necessary shared source edits are limited to `http.go` intake hooks,
`context.go` private-bound planning prompt, `acceptance.go` registered handlers,
`acceptance_goal.go` bound planning verification/compiler hook,
`runtime_coordinator_windows.go` one intent preflight and truthful planning JSON
MIME, and `screens.jsx` natural input/status/layout. `tests/ui/browser_smoke.py`
selectors retain actual 412/draft coverage. `scenarios.py` required no change.

# HANDOFF RESUME PACK — checkpoint revision 142 (2026-10-04T14:21Z)

Entry point for the next window. Supersedes nothing: `HANDOFF_RESUME_PACK_R97.md` and `HANDOFF_RESUME_PACK.md` are
left as written. Numbers below were read from `execution/v2.4/step_state.json` and `execution/v2.4/checkpoint.json`
at this head, not recalled.

## Where the line stands

| | |
|---|---|
| Cards ACCEPTED | **24 / 71** |
| Parents (-99) ACCEPTED | **1 / 22** — W00-99 only |
| Formal cases accepted | **0 / 42** |
| `checkpoint.revision` | 142 (expected_previous 141), `current_step_id` W07-02, `next_step_id` W07-02 |
| Rows | 27 total: 24 ACCEPTED, 2 BLOCKED (W01-99, W14-01), 1 IN_PROGRESS (W07-02) |
| Awaiting independent review | **none** — no row is `EXECUTION_REPORTED` |
| Open obligations | 205, unchanged in count this window; R3 was closed by code |
| Working tree | clean for tracked files. HEAD chain this window: `b55a0540` → `04974054` → `23238898` → `09ad67c2` |
| Money spent | **none**. The authorized DeepSeek/Moonshot run has still never been invoked. |

## Closed since the last pack

1. **W13-02 ACCEPTED** (rev 138, round 1, `ACCEPT_WITH_LIMITATIONS`, reviewer `qoder-desktop:/root/w1302_verifier_r1`,
   33 digests). P5 (`apps/web/src/continuity.jsx:115` adopting a session id from a reply body) **ships unfixed on
   purpose** and is named in the row note; it must land with browser-level teeth before the W13 gate is closed.
2. **W07-01 ACCEPTED** (rev 140, round 1, same shape, 42 digests). Its five reservations travel as
   `receipts/W07/W07-01/addendum_round1.json`, which withdraws three of my own statements without touching their bytes.
3. **Obligation R3 is fixed by code, not prose** (`b55a0540`): `forward()` in `tests/sources/check/main.py` now derives
   `RESEARCHOS_SOURCE_MODE` from the same whitelist the child validates, with a deliberately empty default so an
   unbound selection still refuses loudly. Measured before: `W07-G01` and `W07-G02` both returned
   `NOT_IMPLEMENTED / registered W07 source mode required`. Measured after: `W07-G01/fixture` returns rc 0 with a real
   report (`execution/receipts/W07/run-1d77307e7eb14819996a345aaadd41c2`), `W07-G02/live` and `A05/live` reach real
   **red** outcomes (`run-9894a8673276497087e8aa9301323365`, `run-35dc14d5298c49cfa61126d2c43badd0`) recorded as red.
   Because the edited file belongs to accepted card W07-01, its roster was re-run through the dispatcher afterwards:
   **PASS, 23 assertions, 0 failures** (`receipts/W07/W07-02/w0701_regression_after_r3.json`).
4. **W14-01 frozen its real issue** and then blocked honestly (rev 139 → 141). `ISSUE-DOCTOR-JSON-001` was reproduced,
   not invented: on a binary built from the locked go1.27.1, `researchos doctor --json` and bare `researchos doctor`
   return byte-identical stdout `8a76565c…` with two empty stderrs, and `apps/cli` contains zero `--json` occurrences.
   `REAL_ISSUE_SCOPE`, which the card's own write_scope names but no alias defined, was registered in
   `execution/v2.4/path_ownership.json` at **registry revision 2** with append-only guards.

## Two traps the next window should not re-enter

- **Do not infer the X backend from absent API tokens.** I did, twice, and both records are corrected by new files
  (`resource_gate_correction_round1.json`, `x_backend_probe_round1.json`) because the first was already pinned evidence.
  X is reached through `adapters/sources/x.go` → `internal/domain/sources.go:304`
  `XBrowser{Runner: BrowserActCLI{Executable}, BrowserID}` — a browser id, not a bearer token. `browser-act browser list`
  (after loading `get-skills core`, which the project rule requires before any browser-act command) shows a
  purpose-scoped browser already registered: **`researchos-x`, id `direct_local_120993884286222444`, `chrome-direct`,
  "authorized visible read-only X research using local Chrome; no posts, no cookie export, no other projects"**.
  Existence is not a successful read: nobody has driven one `XBrowser.Fetch` yet, so X may be logged as neither success
  nor blockage until that happens.
- **Do not treat W07-02's registered command as servable by the legacy child.** The child whitelists only `W07-G01`,
  `W07-G02` and an empty check id, so `--check-id W07-02` is refused as `unbound W07 selection` at any mode value.
  The card must ship its own handler. This is measured, not assumed.

## Concrete next steps, in order

1. **W07-02 (IN_PROGRESS, no work left undone in flight).** Open a session on `direct_local_120993884286222444`
   **through the product path** — feed the browser id into the domain source configuration so `XBrowser.Fetch` does the
   reading, not an ad hoc script — and record the real page, window, cursor and health, classifying any refusal as
   environment rather than product. Then implement the card's own handler for `--check-id W07-02`, and the injection
   that proves X failing leaves GitHub and papers running and the overall verdict **PARTIAL, not COMPLETE**. Writing
   empty results as complete coverage, or logging X as blocked without trying it, is the card's named negative case.
   Still owed from the W07-01 review: obligation R4 (`sealed_matches` joins on the claimed digest; `blocked_kinds`
   never gates status).
2. **W14-01 stays BLOCKED** behind a runtime worker that terminates the broker envelope
   (`runtime_broker_windows.go:183-194` POSTs `{key, epoch, run_id, capability, payload}` with an `Idempotency-Key`).
   `packages/` is absent, so `fork.worker_launch_rpc`'s argv target does not exist. Owner is **W12-02**
   (`adapters/runtime/**`, `tests/resources/**`). After that: bind `test.cycle.live` under the `commands.json` 旧例
   (absent-key assert, no-op re-dump, single forward-slash script element in argv, then re-run all 21 existing
   selectors and compare), then run the frozen cycle. Revert nothing from W13-02 or W07-01 while doing this.
3. **Parents and cases are the real target**, not more slices: 1/22 and 0/42. W07-99 depends on the W07 gate rows that
   R3 and R4 touch, so the W07 branch is currently the shortest path toward a second parent acceptance.

## Standing rules that were load-bearing here

- Registered evidence bytes are never edited. Three of my own statements turned out false after being hashed; each was
  answered by a **new** file and restated in the row note.
- `checkpoint.json` does not round-trip, so array appends are text surgery: **one separator per element, and parse the
  candidate before writing**. A missing comma made the checkpoint unparseable for about two minutes this window; it was
  repaired by a guarded textual insert (never `checkout`/`restore`, which would have discarded a concurrent writer), and
  disclosed in `receipts/W07/W07-01/checkpoint_incident_round1.json`.
- Shared files with many consumers (`commands.json`) need a full-selector regression before and after. `path_ownership.json`
  has **zero programmatic readers** (`task_packet.py` and `dispatch.py` never mention it), which is why the alias append
  was safe without one — measure the resolver before judging a change's blast radius.
- `execution/v2.4/path_ownership.json` names `shared_integrator = qoder-desktop:/root/platform_owner`; the rev-2 alias
  was written by `construction` and that deviation is disclosed, not hidden.

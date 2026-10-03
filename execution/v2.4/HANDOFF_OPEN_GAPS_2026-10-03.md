# Open gaps measured on 2026-10-03 (W12-01 awaiting its round-2 verdict)

Written by `qoder-desktop:/root/construction`. This is a handoff document, not evidence for any card:
it names nothing as accepted and re-pins nothing. Every number below was recomputed from files on disk
at HEAD c9350e77 and its parents; the full data sits in the two JSON files named at the end. Read
`execution/v2.4/checkpoint.json` (rev 34) for the state of play and
`execution/v2.4/receipts/W12/W12-01/HANDOFF_ROUND1_STATUS.md` for the W12-01 branches.

## 1. The 42-case gate is mostly unreachable today

Method: read the `case_id` selector lists of both registries (`execution/commands.json` rev 5,
`execution/v2.4/commands.json` rev 13) and each harness's own guard code.

| bucket | count | cases |
| --- | --- | --- |
| executable through a BOUND command whose guard accepts it | 8 | A01, C03, C04 (`ops/ci/context.py` `CASES`), C11, C13, C14, C15, C16 (`ops/ci/resources.py` guard list) |
| named by no `case_id` selector in either registry | 8 | A04, A10, A11, A13, A14, A15, A16, C26 |
| served by a Go check program or an unattributed harness, needs per-check verification | 26 | A02, A03, A05-A09, A12, C01, C02, C05-C10, C12, C17-C25 |

So "all 42 formal cases validly accepted" cannot be approached by finishing cards alone: eight cases
have no handler to bind at all, and a card must register them before the gate can move.

## 2. CLI and Windows Desktop: the commands are registered but unbound

`execution/v2.4/commands.json` contains `cli.entry_run` (argv `apps/cli/main.go`, owner_card
"W03-01 interactive CLI"), `desktop.shell_launch` (`apps/desktop`, W13-01) and
`desktop.installer_build` (npm `dist:win`, W16) - all three `state: UNBOUND` with wildcard selectors.
`apps/cli/` and `apps/desktop/` do exist, and `build.check` (W02-03) is BOUND, so the gap is binding and
wiring, not missing files. Two further facts, each verified:

- `internal/host/native.go:264-285` refuses a client-named directory with `ErrUntrustedPathChoice` when
  `chooser == nil`, and no caller injects a chooser: a user cannot pick a directory in the product.
- `apps/control/credentials.go:18,68` still issues its own credential through
  `s.IssueCredential` instead of the qualified `internal/host` bridge; `apps/cli` likewise.
- **No card in `tasks/steps/*.md` grants write scope over `apps/**`** (grep over every card file), so
  the rewire has nowhere to be written.

## 3. Artifacts assigned to accepted cards that no check advances

- `execution/v2.4/client_mapping.json` (protocol `researchos-client/2`, owner "W02/平台整合者" per
  05_WBS.md:91): 23 methods, **none bound**, 20 with an empty `rpc_binding`; 13 rows name cards that are
  already ACCEPTED (W02-02 promised "完整client_mapping" in its own deliverable line and owns this path
  in its write scope, W03-01, W03-02, W04-02). The accepted receipts never mention the file, so this is
  a silent gap rather than a contradicted claim.
- `cli.entry_run` above is the same pattern: W03-01 accepted, its command still UNBOUND.

Proposed falsifiable check for the W02 owner: a row or command whose `owner_card` is an ACCEPTED step
must not remain PLANNED/UNBOUND, and a row whose owner card is not started must name a real registered
handler. Until such an assertion exists, `W01-G03`'s `own_cli_entry_present` sub-gate stays honestly
false, and `installed_desktop_present` has no distribution evidence.

## 4. Evidence-pin status of accepted cards (250 pins recomputed)

Five rows are stale across three paths. `tests/context/check/main.go` and `legacy.go` are W04-01's
deliberate, already-erratumed drift. `execution/v2.4/commands.json` is pinned by W03-02, W04-01 and
W17-01 and all three pinned hashes had already stopped being current on 2026-10-02
(last-current commits `7f7f6f4a`, `edd4cc5c`, `a444e145`), a day before W12-01's registry edits
(`b7441d64` rev 12, `f99074f8` rev 13). W12-01 therefore advanced an already-drifted path rather than
breaking a valid pin. The commands.json pins held by **W03-02 and W17-01 are covered by no erratum** -
their parity re-check owes a decision to re-pin or to declare the drift intended.

An earlier version of this scan reported 133 stale pins because it resolved `step_state` evidence paths
against the repository root instead of `execution/v2.4`; that bug and its correction are recorded in
`execution/v2.4/receipts/W12/W12-01/accepted_pin_drift_timeline.json`.

## 5. Next card, first action

W06-01 is the next executable card (W12-02 is gated on it). Its first action must be the before-baseline
for every selector `test.orchestration` serves - task_id W06/W12/W11/W16, check_id W06-G01/W06-G02,
case_id C01/A02/A03/C16/C07/C10 - because binding a v2.4 key flips all of them, and C01/A02/A03 belong
to other parents. Its real delta is the "state changed mid-reconciliation" case, not a re-run of the
gates W06-G01 already asserts; and C07/C10 are listed as its cases while `ops/ci/orchestration.py` only
accepts C01/A02/A03, with final ownership belonging to W11 and W16.

## Data files

- `.local/formal_case_executability_map.json` - per-case handler map with method and caveats
- `.local/CLI_DESKTOP_GAP_AUDIT.md` - the chooser/rewire/client_mapping measurements with file:line
- `execution/v2.4/receipts/W12/W12-01/accepted_pin_drift_timeline.json` - 250-pin recomputation

`.local` is not tracked by git; if a later window needs any of these as evidence, move the file into the
owning card's receipt directory and re-run it from there.

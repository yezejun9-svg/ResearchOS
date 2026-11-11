# Resume pack at checkpoint revision 97 (recomputed from disk; HEAD c508e57700cb662f36522bc20eac7dac90e34c4e, tree clean)

A new file, not an edit: the earlier HANDOFF_RESUME_PACK.md is left untouched. Every count here was read
from execution/v2.4/step_state.json and checkpoint.json at write time, not carried over from prose.

## Where the loop stands
- step_state rows: 19 (18 ACCEPTED, 1 BLOCKED). ACCEPTED: W00-01, W00-02, W00-03, W00-99, W01-01, W01-02, W01-03, W02-01, W02-02, W02-03, W03-01, W03-02, W17-01, W04-01, W04-02, W12-01, W05-01, W13-01
- BLOCKED: W01-99
- Parent -99 gates present as rows: W00-99, W01-99, of which ACCEPTED: W00-99. So exactly one parent gate is accepted and
  the rest have no row at all yet - they are not blocked, they are unstarted.
- Formal cases: no case-level row exists in step_state, so formal cases accepted = 0. The tracked census of
  what each case still needs is execution/v2.4/formal_case_requirements.py / .json and the work orders in
  formal_case_work_orders.py / .json.
- checkpoint: revision 97, expected_previous_revision 97, failure_counters 17 (append-only, none reset this
  session), integrity_events 60, work_in_progress null.
- W13-01's own row carries its verdict (ACCEPT_WITH_RESERVATIONS), the reviewer identity qoder-desktop:/root/w1301_verifier_r3, 7 reservations, 10 limitations and 26
  evidence digests. Read the conditions there; do not trust any paraphrase.

## What this session changed, in commits
f52de7bc registered W13-01 on the round-3 verdict (settled digest 3db78045c7c10569, 0 blocking issues) and
landed three condition-disposition addenda plus registration_tool_defects.md. c508e577 re-seeded the
registrar's guard fixtures from the live step_state, so the suites (15 and 9 cases) are green for the right
reason and no longer mirror the tool's assumptions. `.local/register_w1301_accepted.py` now also refuses a
--dry-run against an already-registered card, which was the last disclosed gap in it.

## Next move, and why it is the neck
W01-99 is the only parent gate whose dependencies are met, and behind it `cli.entry_run` is BINDABLE - owner
card accepted, the CLI itself runs (`go run ./apps/cli version` exits 0), yet the registry key is still
UNBOUND. Apply it with .local/prepare_cli_entry_binding.py, which records the before-resolution baseline,
names the accepted receipts that pin commands.json, and refuses --apply while a review request is open; then
refresh the computed errata and re-resolve parity at the new HEAD. W01-G03's last failing flag tests a
filename instead of a dispatcher question; replacing it is QUALIFICATION-domain work and must be done as its
own measured change, not smuggled into a binding.

## W13-01 obligations the acceptance left standing
M26 (provider catch-all returning ok:true) survives - an unlisted provider status would pass the suite.
C23 still emits 6 legacy W13-UI-WORKFLOW-0N ids and never the frozen C23-0N; apply_w1301_c23_frozen_ids.py
is staged with a positional manifest and count/uniqueness refusals. 13 assertion rows have neither a mutant
nor a stated reason. desktop.shell_launch is UNBOUND and needs four measured conditions before it can be
bound. Step 4 stays blocked by resource Windows_desktop_session and nothing here claims it.

## Rules that bind whoever resumes
Never edit a registered receipt, not by one byte - corrections go in new files plus an integrity event.
Use a fresh reviewer identity per round, settle the verdict file (digest unchanged across a wait) before
hashing it, and register only on an empty blocking_issues array. Verify test fixtures against the live
step_state shape: rows are a LIST keyed by id, evidence is a list of {path, sha256} relative to
execution/v2.4. Do not run two heavy Go evidence suites at once. UNBOUND or zero-assertion runs are never a
PASS, and the executor never signs its own acceptance.

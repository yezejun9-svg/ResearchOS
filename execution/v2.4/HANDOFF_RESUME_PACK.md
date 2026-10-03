# ResearchOS v2.4 resume pack (written 系统无法接受输入的日期。
输入新日期: (年月日), all figures recomputed from disk at HEAD 165078c0)

Read this first, then re-verify it: every number below is produced by the commands in section 5, and
none of them should be trusted from this file alone.

## 1. Where the build stands
- cards accepted: **17 of 71** (step_state rows: 17 ACCEPTED, 1 BLOCKED: W01-99)
- parent gates run through the `Wxx-99` cards: accepted **W00-99**; the only gate whose dependencies are met is **W01-99**
- formal cases accepted: **none**. Reachable by a v2.4 selector: 12 of 42; classes: {"selector_and_every_id_named_by_a_program": 6, "selector_and_only_some_ids_named": 5, "no_registered_selector": 30, "selector_but_ids_live_only_in_a_manifest": 1}
- registry: revision 15, 10 keys BOUND and 8 not, readiness classes: {"BINDABLE": 1, "NEEDS_HANDLER": 2, "NEEDS_OWNER": 5}
- protected-work audit just now: 196 registered evidence rows, 0 drifted, 0 missing, and 7 receipt-internal rows drifted with none uncovered by an erratum

## 2. The one card in flight
`W13-01` - round 1 REJECT (3 record blockers, all reproduced), round 2 REJECT (2 blockers, both fixed at commit c6dbc002), round 3 review requested and unfinished. Its receipt reports PASS 31 with 14 artifacts, a 10-case matrix with 0 survivors, and a self-audit with 0 inconsistencies at the tree the receipt names, not the live HEAD. Its own notes file and the round-3 brief describe what a reviewer must re-run. **step_state has no row for it and must not gain one unless a verdict arrives with an empty blocking_issues array.**

## 3. Prepared, deliberately unapplied (each one refuses while a review request is unanswered)
- `.local/prepare_cli_entry_binding.py [--apply]` - binds `cli.entry_run`, the only BINDABLE non-bound key and the neck of the 22-parent chain. Before-resolution, byte backup, refuses an unobservable change, and names the five accepted receipts that pin `commands.json` so their errata are refreshed.
- `.local/apply_w1301_c23_frozen_ids.py [--apply]` - maps forwarded legacy rows onto C23-01..06 positionally through `tests/ui/expected.json`; refuses when counts or uniqueness disagree.
- `.local/prepare_w1301_mutants_round3.py` - the coverage attempt that failed honestly: two candidates crashed the harness and one survived, so the runner was reverted; **13 assertion rows still have neither a mutant nor a stated reason** and the round-3 brief says so.
- `.local/prepare_desktop_shell_launch_binding.py` - why `desktop.shell_launch` cannot bind as written (argv names a directory, the package has no scripts) and what a real binding must include.

## 4. Constraints that are easy to break by accident
- A registered receipt is byte-frozen and still says `EXECUTION_REPORTED` inside: read acceptance from `step_state.json`, never from the receipt's status field.
- Digests of evidence files must be hashed from raw bytes; newline-normalised text produced 20 unverifiable census digests that only looked correct because half were empty files.
- `execution/v2.4/commands.json` is pinned by five accepted receipts. Drift there is answered with a computed erratum beside each one (`pin_drift_erratum_chain.json` today), never by editing a registered receipt or silently re-pinning.
- After any commit, parity rows and captured command logs must be re-measured at the new HEAD before a receipt is regenerated; the generator refuses to mix trees.
- No push, no deploy, no purchases, no reading secret values, no second construction session, never `git reset/clean/checkout .` against the tree, and explicit paths only in `git add`.

## 5. Re-verify in one line each
- `python .local/pin_audit.py` - the two pin sets, non-zero exit if registered evidence moved.
- `python execution/v2.4/registry_binding_readiness.py` - why each unbound key is unbound.
- `python execution/v2.4/formal_case_requirements.py` then `formal_case_work_orders.py` - case gate classes and who owns each case.
- `python execution/v2.4/parent_gate_ledger.py` then `parent_gate_frontier.py` - per-parent state and the dependency frontier.
- `python D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/tools/task_packet.py next --state execution/v2.4/step_state.json` - the selector's own answer for the next card; expect `state_source: VALIDATED_FILE`.

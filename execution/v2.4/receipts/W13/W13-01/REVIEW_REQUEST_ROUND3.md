# Review request: W13-01, round 3

Reviewer identity (must not have ruled on this card or any other): `qoder-desktop:/root/w1301_verifier_r3`.
Write your verdict to `execution/v2.4/receipts/W13/W13-01/independent_review_round3.json` and to nothing else.
Vocabulary: ACCEPT / ACCEPT_WITH_LIMITATIONS / ACCEPT_WITH_RESERVATIONS / ACCEPT_BLOCKED_RECORDING / REJECT.
Registration happens only on an empty `blocking_issues` array. Carry every array you produce. Timestamps end with
`Z`. Settle your bytes and write once - the registrar pins the digest and refuses while this request is open.

Read `independent_review_round2.json` (digest pinned in `verdict_pin_round2.json`, prefix `de1365c7`) and
`executor_response_round2.json` first. Both of round 2's blockers were reproduced before being answered, and one
honest failure is disclosed below rather than hidden.

## The two blockers, and what to check

1. **`W1301-R2-BLOCK-FORWARDED-PYTHON-DISCLOSURE-STILL-FALSE`.** The sentence "the forwarded branch resolves python
   through PATH rather than the locked tool table" was corrected in both places it lived - `registry_parity.disclosed_consequence`
   in the receipt and the `test.ui.routes` note in `execution/v2.4/commands.json`. Verify against the code, not the
   prose: `tests/ui/check/main.py` forwards with `[sys.executable, "-X", "utf8", "ops/ci/ui.py", ...]`, and
   `execution/command_dispatcher/dispatch.py` launches the check program from
   `locked['tools'][entry['executable_tool']]['path']` after verifying the table. Confirm
   `sys.executable == locked['tools']['python']['path']` on this host, that no file in the record still claims a
   PATH lookup for python, and that the registry note also stopped pointing at `binding_and_parity_rev15.json`
   (the superseded binding-commit file) instead of `binding_and_parity_rev15_at_head.json`.
2. **`W1301-R2-BLOCK-C23-RUN-COUNT-STALE-AT-WRITE-TIME`.** The receipt generator now *runs*
   `census_c23_w1301.py` before quoting it, and the guard refuses if any invocation the receipt cites with
   `case_id C23` is missing from the census. Reproduce: `python
   execution/v2.4/receipts/W13/W13-01/census_c23_w1301.py` and compare `runs` with
   `receipt.json:registry_parity.c23_forwarded_history.runs` and with a scan of
   `execution/invocations/*/receipt.json` for `command_key == test.ui.routes` and `selectors.case_id == C23`.
   Then attack the guard the way round 2 attacked probe 9: delete a census row, regenerate, and confirm the
   generator refuses rather than publishing a smaller count.

## What else changed since round 2

The node PATH fallback the resolver docstring denied is gone: `main.py` no longer runs `[node_bin or "node", ...]`;
when the pinned binary cannot be verified the driver is not launched and the dependent rows fail by name. Confirm
that claim by reading the launch block, not the docstring. `first_run_check_output.json` was refreshed from a real
run because the old copy still carried the round-1-false clause about `main.js`.

## A failed coverage attempt, disclosed rather than buried

Round 2 reserved that 13 assertion rows have neither a mutant nor a stated reason (31 emitted, 12 killed, 7
explained). I added six candidate mutants and five reasons. The measured result: two candidates (`M24`
unknown-client, `M25` unknown-method) **crashed the harness** rather than being killed - so they are not coverage -
and one (`M26`, non-OK provider reply counted as success) **survived**, which means the provider-status rows I had
argued were covered by that shared branch are in fact not discriminated by anything. I therefore reverted
`mut_w1301.py` to the committed 10-case runner instead of shipping half-broken coverage, and re-ran: 10 caught, 0
survived, 0 crashed, tree clean. **The 13 uncovered rows remain open on this card.** Treat them as an outstanding
reservation unless you want to make them blocking; what you should not accept is a claim that they were fixed.

## Re-run, in order

- `python execution/command_dispatcher/dispatch.py test.ui.routes --task-id W13 --check-id W13-01` → PASS 31; the id
  set must match `binding_and_parity_rev15_at_head.json` (measured at the HEAD the receipt reports).
- `python execution/v2.4/receipts/W13/W13-01/mut_w1301.py` → 10 cases, all caught, `tree_clean_after_restore: true`.
- The three selector shapes: local served, `--case-id C23` forwarded (nondeterministic; the census classifies every
  run, and one PASS is not stability), bare selector refused with zero assertions.
- `python execution/v2.4/receipts/W13/W13-01/audit_receipt_w1301.py` → expect zero inconsistencies; it now derives
  its own probe-family count and recomputes every census digest from raw bytes with a falsified-digest control.
- All 14 receipt artifact hashes, plus the `test.ui.routes` entry at revision 15 owned by W13-01.

## Still not claimed by this card

`desktop.shell_launch` still carries owner_card W13-01 while UNBOUND; step 4 (packaged install, Start menu, U01
gate) and the native directory dialog stay blocked by the resource `Windows_desktop_session`; provider models,
credential save and a real probe stay NOT_RUN; nothing here accepts parent W13 or signs formal case C23 or A10 -
and C23's frozen `C23-01..06` ids still cannot be emitted, a fix that is staged in
`.local/prepare_w1301_c23_frozen_ids.py` and unapplied.

# Review request: W13-01, round 1

Reviewer identity (must not have ruled on this card before): qoder-desktop:/root/w1301_verifier_r1
Write your verdict to `execution/v2.4/receipts/W13/W13-01/independent_review_round1.json` and to nothing else.
Verdict vocabulary: ACCEPT / ACCEPT_WITH_LIMITATIONS / ACCEPT_WITH_RESERVATIONS / ACCEPT_BLOCKED_RECORDING / REJECT.
Registration happens only on an **empty `blocking_issues` array**; carry every array you produce (limitations,
reservations, blocking_issues) - a registrar that reads one field is a hole. Use `...Z` timestamps: the
registrar compares `reviewed_at` as a string, and `+00:00` can sort before `Z` on the same date.
Settle your verdict bytes and write it once; the registrar pins its digest, and a partial file becomes an
erratum. Do not edit any file you did not author, and do not run two heavy Go suites concurrently.

## What was reported
Receipt `execution/v2.4/receipts/W13/W13-01/receipt.json`, sha256 `d319587952f273693d361ad35e8a7d6d923bd010c7ac708abb7f5c7ccfeb2b88`, status EXECUTION_REPORTED,
describing tree `584464b9` (the commit that contains it is its child by one, which is intended).
Executor self-audit: 8 probe families, **0 inconsistencies**, 12 artifacts re-hashed, 20 dispatcher runs of
the forwarded case tabulated. It is not evidence of acceptance - re-run rather than trust it.

## Re-run, in this order
1. binding command: `python execution/command_dispatcher/dispatch.py test.ui.routes --task-id W13 --check-id W13-01`
   - expect PASS 29 with an assertion id set equal to `check_results.assertion_ids`; compare against the two
     at-HEAD runs in `execution/v2.4/receipts/W13/W13-01`.
2. `python execution/v2.4/receipts/W13/W13-01/mut_w1301.py` - 10 cases, expect all caught and
   `tree_clean_after_restore: true`. Revert one of its own case anchors and confirm the runner reports
   `anchor-missing`, not a pass.
3. the three selector shapes: local W13-01 served, `--case-id C23` forwarded, bare selector refused with zero
   assertions. C23 runs a real Windows browser and **is nondeterministic**: 20 dispatcher runs are on disk,
   5 COMMAND_FAILED, classified into 4 causes. Assert the branch is not shadowed; do not treat one PASS as
   proof of stability, and do not blame the client mount - that causal claim was measured away.
4. recompute the artifact hashes and the registry rows for `test.ui.routes` at revision 15; the entry must stay
   owned by W13-01 and `before_baseline_test.ui.routes.json` must still show what the key did before binding.
5. `python execution/v2.4/receipts/W13/W13-01/audit_receipt_w1301.py` - and try to *break* it: it caught a
   truncated assertion id and a 28-vs-29 assertion mismatch this round, so its rules are worth attacking.

## What this card does NOT claim
Step 4 of the card (installed shell, Start menu, U01 first-use gate) and the native directory dialog are
blocked by resource `Windows_desktop_session`; provider model listing / credential save / real probe stay
NOT_RUN because no provider command key is bound (`client_mapping.json` lists them PLANNED under W02-03 and
W08-01); `desktop.shell_launch` carries owner_card W13-01 while UNBOUND and this card did not bind it;
nothing here accepts parent W13 or signs formal case C23 or A10.

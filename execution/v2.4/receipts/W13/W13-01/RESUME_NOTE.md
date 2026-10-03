# W13-01 resume note (written by the executor, not evidence of acceptance)

State at write time: receipt.json is EXECUTION_REPORTED at HEAD 1e6a385e, registry test.ui.routes is at
revision 15 owned by W13-01, and the card is NOT registered. Live counters must be re-read from
execution/v2.4/checkpoint.json and step_state.json rather than trusted from this file.

Measured this round: binding command PASS 29; forwarded case C23 PASS 6; the bare selector refused with
0 assertions. All three were re-measured at this HEAD into binding_and_parity_rev15_at_head.json because
the binding-commit parity file carried a 28-assertion row and quoting both would mix trees. The mutation
matrix reports 10 cases, all caught, tree clean after restore.

Still owed, in order:
1. an independent identity must re-run the binding command, the matrix and the parity rows. Nothing here
   is self-accepted and the executor may not sign this card;
2. c23_forwarded_flake_census.json shows the forwarded legacy branch is nondeterministic: 16 dispatcher
   runs on disk, 5 COMMAND_FAILED, classified as my own SyntaxError (2), the legacy harness's selector
   guard (1), and the real browser phase reporting FAIL at inputs that PASS minutes apart (2). Whoever
   signs C23 must re-run it more than once;
3. step 4 (installed shell, Start menu, U01 first-use gate) and the native directory dialog stay blocked
   by the resource Windows_desktop_session;
4. desktop.shell_launch carries owner_card W13-01 while UNBOUND - this card either binds it or records why;
5. audit_receipt_w1301.py was still being repaired when this was written. Its last run is stored as
   self_audit_run.json and it still names two ids the receipt cites that nothing emits:
   W1301-NATIVE-PICKER-IS-REGISTERED-IN-MAIN (a no_mutant_rows key, i.e. a name for a source-level guard
   rather than an assertion id) and W1301-SELECTORS-REQUIRED (emitted on the bare-selector shape, whose
   invocation the auditor does not read). Both stay open items, not resolved claims.

## Update written after that note (executor, same round)
Receipt regenerated at tree `584464b9`: the at-HEAD parity rows and the captured command logs are now listed as
artifacts (12 in total), the C23 census covers 20 runs, the matrix key that named a guard nothing emits was
replaced by the disclosure row that really carries that property, the prose that quoted an unmeasured
assertion id was removed rather than re-scoped, and the disclosure list keeps the exact porcelain shape
(it had eaten one leading space). The self-audit run on disk reports 0 inconsistencies.
Next action is unchanged: an independent identity rules from `REVIEW_REQUEST_ROUND1.md`; registration only on
an empty `blocking_issues` array.

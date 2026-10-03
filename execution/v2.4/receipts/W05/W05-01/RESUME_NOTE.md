# W05-01 resume note

Round 4 entry point, written at 2026-10-03T08:46:21.662862+00:00 (HEAD 22dc53c4, checkpoint revision 51).

- W0501-R3-B-01 (medium): the provider disclosure rewritten to answer round-2 B-03 contains a measurement the tree refutes, and that measurement has now been copied into the continuation state
    owed: restate the clause as measured: '20 of 23 mapped methods carry an empty rpc_binding; provider.models carries the annotation n/a (Go-owned catalog), provider.probe is empty, and neither has a server-side route in internal/domain'. Correct the checkpoint obligation the same way rather than leaving it to be inherited. Optionally quote the status literal 'PLANNED_IN_W02_03_THEN_W03' so a verifier finds the string.
- W0501-R3-B-02 (medium): the new NOT_RUN row for the card's fifth failure class reports the class untested while a passing test inside this card's own write scope names it, and the companion substitution row misstates what reads Spec.Model
    owed: rewrite the fifth-class row to say what is measured: the 29 check-program rows do not drive turn.failed or request_failed, but adapters/runtime/runtime_windows_test.go:66-68 does, names it and passes today, and the receipt's -run filter excludes it; then either widen receipt command 5 to select TestW05ProtocolTransientReconnect - one string, and it re-runs accepted evidence rather than manufacturing any - or state pl
- W0501-R3-B-03 (medium): the rewritten five-class row reports one card class as asserted by an assertion whose decisive clause cannot fail, and still counts a non-card class among the five
    owed: make w0501.go:181 require p.Failure == 'invalid_protocol', then add a matrix case anchored on codex.go:34 - the assignment is unique in the file - so the class claim is killable and MALFORMED-LINE-NAMED leaves the nine-row no-mutant set; and restate the five-class row so each of the card's five maps to exactly one asserted or one disclosed row, with disconnected transport either dropped or labelled as the card step-2
- W0501-R3-B-04 (low-medium): three card sentences are still neither asserted nor disclosed, so the completeness claim the round-3 brief puts to me does not hold
    owed: add three skip rows: (i) the no-borrowed-account rule, stating whether anything in the increment touches an account and which card owns the rule; (ii) the worker identity, stating that the delegated worker is a cmd.exe process under a Job Object, that no Mu/Pi agent SDK loop is wired, and what would make it one; (iii) the single-host conjunct, naming host.status and host.configure as PLANNED under W02-03 alongside th

Round 3 verdict: REWORK_REQUIRED by qoder-desktop:/root/w0501_verifier_r3, with 4 blocking issues, 14 reservations and 10 limitations, committed at 22dc53c4 and never edited afterwards. It closed the parity-freshness issue and accepted that the provider binding is blocked upstream; it also measured my provider sentence as wrong, which is corrected in the check program and in the checkpoint obligation with a record_correction event rather than a silent rewrite.

Owed next, in the order that keeps the evidence honest:

1. Act on the three properties the reviewer says exist in code this card may write: the requested-model rule enforced around runtime_windows.go line 378, shown inert in its journal; the explicit protocol error path that adapters/runtime/runtime_windows_test.go already drives; and W0501-PROTOCOL-MALFORMED-LINE-NAMED, whose only condition is a non-empty failure.
2. Disclose or assert the three card sentences still unaccounted for: the provider not borrowing an internal account assumption, the Mu/Pi worker with an existing SDK model and tool loop, and the unique-host conjunct of deliverable 1.
3. Widen the receipt capture -run filter so its five alternatives name real tests, then re-run the whole chain with python execution/v2.4/receipts/W05/W05-01/run_evidence_chain_w0501.py. Nothing may be committed or run beside it: last round a checkpoint commit landed mid-chain, HEAD moved, and the receipt generator correctly refused to write.
4. Repair register_w0501_accepted.py before any acceptance is attempted: it demands a nonexistent addendum file, recites W12-01 provenance, hardcodes the accepted-card count, and carries only verdict limitations into the obligations.
5. Self-audit, commit, derive the round-4 brief with python execution/v2.4/receipts/W05/W05-01/make_review_request_w0501.py round4, and ask a fourth identity. Wait for its file to appear and settle before pinning anything.

Standing: 16 of 71 cards accepted, 0 of 22 parent tasks, 0 of 42 formal cases. Not complete.

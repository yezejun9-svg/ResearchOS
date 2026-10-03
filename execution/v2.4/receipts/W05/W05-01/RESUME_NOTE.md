# W05-01 resume note

Round 6 submitted; written at 2026-10-03T10:40:46.301462+00:00 (HEAD dee911d9, checkpoint revision 59).

- Round 5 closed the correlation blocker by converting the disclosure into an assertion and blocked only on propagation: five sentences the new assertion made false survived in the receipt, the disclosure array, the generator, the registrar and the continuation obligation. All five are rewritten at code HEAD 6f8ba164, with the superseded reason kept visible rather than deleted.
- Two instrument defects were fixed in the same pass: the package listing capture now records the test names present and the subset the filter selects instead of digesting a line containing a clock, and the registrar allow-list gained the plain ACCEPTED name it lacked (measured refusal path: five rejections listed, exit 1, step_state and checkpoint hashes unchanged).
- Round-6 evidence: 32 asserted rows, 21 matrix cases all caught including M21 and M22 on the Run-identity join, twelve disclosures, CLEAN self-audit over 20 probes, zero surviving copies of the refuted clause in any instrument. Evidence commit bba9fc66, brief 2180fad3, revision-slip repair dee911d9.
- w0501_verifier_r6 is in flight and may write only independent_review_round6.json.

Three weaknesses the sixth reviewer was asked to grade rather than have re-explained:

1. W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL reads the in-memory journal returned by Wait, so it proves identity rather than durability or the event ledger.
2. The declared-model row still does not separate a required settled protocol from any declared model failing; the discriminating case exists at adapters/runtime/runtime_windows_test.go:210-221 and should become a row with its own mutant.
3. Under mutant M4 the killed set is scheduling-contingent; the receipt now says so, and the durable fix is either to serialise the launch observation or to keep marking the row as timing-dependent.

Then, in order:

1. Wait for independent_review_round6.json to appear and stay byte-stable; commit it verbatim; do not edit a reviewer text.
2. Register only on an empty blocking_issues array with the repaired registrar, then let tools/task_packet.py name the next card rather than reasoning from the dependency I happen to know.
3. Whatever the verdict, the 42-case and 22-parent gates remain: 8 formal cases still have no selector, cli/desktop commands are UNBOUND, and client_mapping binds nothing for provider, probe and host.

Standing: 16 of 71 cards accepted, 0 of 22 parent tasks, 0 of 42 formal cases. Not complete.


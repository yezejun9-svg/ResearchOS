# W05-01 resume note

Round 5 submitted, written at 2026-10-03T09:43:48.919877+00:00 (HEAD f41dc342, checkpoint revision 58).

- Round 4 verdict REWORK_REQUIRED (4 blocking) committed; all four addressed, one of them by converting a disclosure into an assertion (W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL: worker started under the claimed Run id, task id and lease epoch; journal Spec must equal them; the fixture reservation must be keyed to the same Run).
- Round 5 evidence: receipt at code HEAD 55223e0f, 32 asserted rows, 21 matrix cases all caught including M21 and M22, 12 disclosures, CLEAN self-audit. Evidence commit 4e498d76, brief f41dc342.
- w0501_verifier_r5 is in flight; the registrar now blocks any of the four earlier identities from re-signing.

Stated gaps so the next window does not have to rediscover them:

1. The declared-model row does not yet discriminate a settled protocol under a declared model; the case exists at adapters/runtime/runtime_windows_test.go:210-221 and should become a row of its own with a mutant.
2. Round 4 measured one matrix row (M4) differing between its own first and second solo runs; treat matrix reproducibility as unproven until two consecutive solo runs agree byte-for-byte in one window.
3. The provider, host and CLI bindings genuinely belong to W02-03, W08-01 and the unbound cli.* rows, so an acceptance of W05-01 can only mean the adapter, decoder and service-surface properties plus honest blocks for the rest.
4. If the verdict is REWORK again, correct inherited text everywhere: two obligations survived one round of correction with sentences the tree refutes.

Standing: 16 of 71 cards accepted, 0 of 22 parent tasks, 0 of 42 formal cases. Not complete.


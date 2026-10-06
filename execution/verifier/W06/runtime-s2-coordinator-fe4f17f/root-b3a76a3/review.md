# Root integration receipt read-only check

Verdict: `PASS_READONLY_ORDINARY_INTEGRATION_RECEIPTS`. Source `0e4b0c26427efc57f692eba052f0c2fb34fc3dbf`; archived receipts `b3a76a3`.

Read the two root reports and independently parsed their existing JSONL test events. `coordinator-current` has build exit 0, 20 passing test/subtest events, three failing consumer setup events, and zero skips; its test command correctly retains exit 1. Each failed consumer has an output mentioning the required `RESEARCHOS_GO` tool binding. `consumer-tool-binding` supplies that binding and records the same three consumers passing, zero failures/skips, exit 0, 18.165 seconds. Both reports' exact pass/fail/skip lists match the underlying raw events. The previously passing 20 tests were not rerun by the root retry.

Normal passing coverage includes actual control startup and the nine crash-recovery subcases. The three successful consumer retries are `TestW10NativePair`, `TestW16C20`, and `TestW17C22ProtectedIsolation`. This older root C20 consumer is a compatibility smoke test and does not replace the separately frozen private C20 review.

No tests or native processes were launched by this reviewer. The blocked automated adversarial review, LIVE qualification, formal A15/W20 and formal case counts remain unchanged. The review verifies the root's normal integration receipts; it does not turn them into an adversarial or independent OS-service certification.

Frozen receipt hashes:

| File under execution/receipts/W06/runtime-s2/root-integration | SHA-256 |
| --- | --- |
| coordinator-current/report.json | 1a8be8f2430970385587e7f2e24a53ac71db8aa7d6757b9a1e8dc8710e61ec38 |
| coordinator-current/test.stdout.log | c2aa9bfb735e2f95f57f2fac3968edb49625c5fb24a6beff26b81a06c4bc14fc |
| consumer-tool-binding/report.json | 4d6b1642ebb337d1a46cb5c26107d6955dd13bda6c4ba9719516c0ea3fcc44af |
| consumer-tool-binding/stdout.jsonl | e2a9d2b5aa56dc44f4fc6c0c68641b0a4f8d99a97b1cf49b28015315451910eb |

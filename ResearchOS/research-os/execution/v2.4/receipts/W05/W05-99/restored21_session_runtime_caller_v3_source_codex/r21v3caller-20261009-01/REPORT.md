# A21 caller v3 Source handoff

Status: `SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL`. This new namespace supersedes the sealed v2 caller after independent review `REQUEST_CHANGES`. The sealed v1/v2 packages, Main, Canon and product were not modified. Root isolation and validation outputs have not been created. No Root caller, Git, Go, SQL, Native, compiler, product CLI or model was executed here.

The v3 diff fixes the review's two P1 and one P2 findings:

1. The package metadata local is `go_module_info`, leaving the global `module()` loader resolvable in `main`. A pure lexical AST probe now invokes the extracted loader statement before the metadata assignment without filesystem access.
2. `closed()` is defined before the guarded `try`. Input and runtime guard acquisition failures are injected into the extracted AST with in-memory adapters; each produces `FAILED_RESTORED21_V2_ACTUAL_CLOSED_NO_COMPONENT_ACCEPTANCE` with the original acquisition error, a false Job closure state, and attempted guard cleanup.
3. Both stages independently attempt every acquired guard close even when an earlier close and receipt persistence fail. Each stage records close and persistence errors in a final attempts receipt when storage permits; if that receipt also fails, the error is printed after all close attempts. Neither stage emits ready or development-test partial success with cleanup errors. Stage 2 binds the exact stage-1 cleanup attempts receipt.

The v2 exact 63-source roster is reused by pinned reference, including SQL and non-domain paths. The selected nine parents plus four drift leaves remain unchanged. Even if Root later observes 13 actual test2json passes, the caller can report only `DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN`: the selected tests do not furnish the separate typed descendant fixture corpus. Native qualification, release-program provenance and overall 20→24 remain open.

Source validation: 21 checks passed against 32 distinct held inputs; the read guard closed with zero errors and zero retained handles. The checks include pure AST/lexical probes, early input/runtime acquisition failures, and simultaneous close/receipt-write failures in both stages. `reversible-v2-to-v3.diff` contains the full three-file diff; `byte-inverse.json` contains and verifies byte-exact v2 reconstruction for all three changed files. The first checker execution failed only because its in-memory marker assertion used uppercase while the fake guard emitted lowercase; Root assigned that failure ordinal 950. Its original visible tool arguments/output and failed-run guard cleanup are retained. The corrected checker then passed; 950 was not reset or counted as product/native execution.

An independent Source review is still required before Root runs `prepare_root_actual.py` and `validate_root_actual.py` with fresh current canonical refs. This package is a Source-only repair, not component acceptance.

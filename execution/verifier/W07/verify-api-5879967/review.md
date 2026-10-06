# W07 verifyEvidence independent review — FAIL / P1

Reviewed commit: `5879967505e207741c21a7f4dbc20d71df35743e`; base: `88688bef5e68640b9b7ef80470a33510f4b40915`.

## Blocking finding W07-VERIFY-P1-001

The fixture-only endpoint does not restrict its target Evidence or source snapshot to the fixture lane. At `internal/domain/evidence_verification.go:85` it requires a FIXTURE receipt, but at lines 144–145 applies its judgement to any eligible current Evidence. A deterministic `orchestration.json-equals` check proves equality to expected JSON; it does not verify the source claim.

An independent loopback HTTP reproduction uploads and seals a local temporary source containing `2 + 2 = 4`, creates OBSERVED/LOCAL Evidence claiming the source says `2 + 2 = 5`, and attaches an OBSERVED/LIVE source snapshot. A separately accepted FIXTURE task supplies the judgement. VERIFIED, CONTRADICTED and UNAVAILABLE each return **200** and persist revision 2. These scope reproductions use ordinary HTTP APIs without database mutation. Raw evidence: `observed-scope.json`, `observed-scope-CONTRADICTED.json`, `observed-scope-UNAVAILABLE.json`.

The target's LIVE metadata describes the actual local temporary-file read. The test execution and all resulting evidence are synthetic FIXTURE only; no external provider or real-user accuracy is asserted.

Required repair: enforce SIMULATED Evidence plus SIMULATED/FIXTURE SOURCE_SNAPSHOT for this implementation and reject all three judgements for OBSERVED/LIVE targets. Future LIVE verification requires a separately qualified runtime/acceptance and semantic source check.

## Verified boundaries

- Missing Idempotency-Key / If-Match rejected 428; changed requested judgement/checks rejected 422.
- Exact idempotency replay returns the same response and ETag; new-key reuse rejected 409.
- Evidence revision bump makes the historical task current-binding stale while the new Evidence remains effective; a downstream task consuming the new version passes acceptance without recursive invalidation.
- Policy change, run epoch rotation, unsettled run, removed verifier role and revoked receipt-verifier grant rejected without Evidence mutation.
- Context seal mutation rejected by immutable DB trigger; changed context prerequisite rejected as stale.
- Old Evidence revision rejected 412; mutation of sealed snapshot bytes rejected by DB.
- Source/executor aliases holding VERIFIER roles rejected 403 by authority-root independence check.

## Verification limits and provenance

Both independent test commands exit 1 because the scope failures are genuine. The first command also encountered a probe expectation error: the context mutation was correctly blocked by an immutable DB trigger. The corrected context-seal probe and a separate stale-context-input probe both pass in the follow-up command. Keep both raw outputs; do not count the initial context error as a product finding.

The author-selected tests passed. The author's full package run failed in two native tests because RESEARCHOS_GO was missing; only those two were rerun successfully after fixing the environment. This is not a full-package PASS.

Source hashes were verified against Git blobs at the reviewed commit and matched the author's receipt. The author began a successor repair in the same worktree during report closeout. Those edits are excluded: this FAIL binds only the frozen commit and retained original probe outputs. No product source, contracts, production configuration or acceptance status was changed by this reviewer. The endpoint's existing UNVERIFIED-only restriction also leaves re-review lifecycle unestablished; this is recorded as a limitation, not an additional reproduced blocking defect.

See `source-audit.json`, `command-receipt.json`, `review.json` and `evidence-index.json` for exact hashes and command provenance.

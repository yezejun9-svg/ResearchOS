# I1 remote Owner correction — independent delta review

Verdict: **P1 CLOSED; PASS_BOUNDED_FIXTURE_SOURCE_INTEGRATION**.

The original `../review.md` NEEDS_FIX conclusion remains unchanged for source
`edb9543c4e91f26bf798e87a23342bc2c88218f2`. This delta review applies to source
`867dfa7c24828f935234d047cbe32c64451c6384` and evidence
`c123861949c73655e78d1c6de5332ed98a5f1c51` in the same intent-planning worktree.
The worktree was clean. No formal acceptance case or product gate is upgraded.

## Closure evidence

The only changed source files are `internal/domain/planning_brief.go` and
`internal/domain/planning_brief_test.go`. The production change closes the grant
cursor, invokes the existing `constrainRemotePrincipal`, propagates its error,
and then checks the constrained OWNER role and project grant. The resulting
principal retains DeviceID and the existing remote restrictions. This repairs
the shared current-authority helper used by planning snapshots, compilation and
coordinator preflight; it adds no alternate authorization rule.

The new regression exercises real HTTP pairing/granting and Owner intent intake,
asserts the stored actor is the remote device, produces a deterministic fixture
GoalBrief, and independently accepts the planning Task. The independent verifier
is a separate principal (`orchestrationFixture.acceptance` switches its token),
so issuer revocation does not merely invalidate the caller's credential. The
device's own stored project grant is explicitly asserted to remain active.

Before-fix raw evidence reproduces both failures: revoked issuer and removed issuer
project grant each incorrectly returned HTTP 201 during planning Goal acceptance.
The active issuer control passed. After-fix raw evidence shows:

| Case | HTTP | Total Goals | Goal acceptance receipts |
| --- | --- | --- | --- |
| Current issuing Owner | 201 | 2 | 1 |
| Revoked issuing Owner | 401 | 1 | 0 |
| Removed issuing Owner project grant | 403 | 1 | 0 |

The two rejected cases leave no business Goal and no Goal AcceptanceReceipt.
The existing local Owner revocation regression also passes. Parsed after-fix raw
contains two passing top-level tests and three passing subtests, no failures or
skips. The production diff passes `git diff --check`.

No fresh test process was needed: the exact shared-helper repair and meaningful
before/after raw regression cover the reported defect. Native dispatch and browser
suites were not rerun, and this delta does not claim fresh runtime-resume coverage.

## Independent source and raw binding

Recomputed all original 18 source hashes: exactly the expected two source files
changed and the other 16 match. All 104 originally reviewed evidence files remain
byte-for-byte unchanged. Independently hashed all three new evidence files;
`independent-recomputation.json` contains the complete inventory.

| File | SHA-256 |
| --- | --- |
| planning_brief.go | cab673683ab3cf10b2b56488713eeca22bd3c4d6ff49cd2ba517b056e6691c01 |
| planning_brief_test.go | e8f55ddb23917ccedc427bc3ad503205de63a41467fd90473bbfc0343ed5529 |
| before-fix-test.jsonl | 1752a0482418f9fa49ed5afcb6321c7b0b3c81e5b75e77cd52fe2ce98d70055a |
| after-fix-test.jsonl | 99b26b1b354246d1be160ff65ceb4e4ddfcac336a38539ce2b6dfc99539bffa9 |
| HANDOFF.md | 9ac406e2134714a2770c0413049dc39c00bb7a102952e25a7cf755ee3fdc5fc4 |

These hashes bind the reviewed frozen files; they do not retroactively create an
execution-time dirty-tree digest for the older browser runs.

## Overall bounded conclusion and retained limits

Combining the original whole-slice review with this narrow P1 correction leaves
no identified blocking source finding in I1's declared bounded scope. The corrected
source is suitable for integration with its existing FIXTURE/native/browser
evidence and current limits preserved.

Automatic business compilation remains confined to explicit positive Owner JSON
delivery forms and the registered json_report/json-equals catalog. The evidence
does not establish general natural-language research, model/provider semantic
accuracy, LIVE business Goal acceptance, protected verifier isolation, or full
production/product E2E acceptance. The original W13 overall FAIL, its later single
320px regression PASS, the initial browser cleanup FAIL, and all policy-blocked
hygiene history remain intact. This review changed only the authorized delta
review directory and did not interact with the blocked cleanup path or R2 work.

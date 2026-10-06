# I1 independent review — frozen candidate edb9543

Verdict: **NEEDS_FIX**. One P1 current-authority defect blocks acceptance of this
candidate. This is an implementation/evidence review, not formal W14 acceptance.

Reviewed source: `edb9543c4e91f26bf798e87a23342bc2c88218f2`, based on
`b3a76a3482de3f156a641e3d2f4485d682743898`, with intake commit
`3a89a61f80f0e4ae78470bbd7db26b30522e47ac`.
Reviewed evidence: `82dee92e0bb3f8c74a60722119484a973137e33d`.
Author worktree was clean at review. Reviewer changed only this review directory.

## P1 — remote Owner issuer authority is skipped during background revalidation

`internal/domain/planning_brief.go:140` reconstructs the original intent actor
from `auth_principals` and `auth_grants`, then checks `OWNER` and `Allowed` without
the existing `constrainRemotePrincipal` intersection. A paired remote OWNER is a
supported submitting actor: `intent_planning.go:10` and `:33` accept the authenticated
Owner and persist `p.ID`, which for a device is its own principal ID.

Concrete sequence:

1. An active paired OWNER with an issuing local Owner project grant submits and
   accepts an INTENT Requirement. Its device principal is bound as the actor.
2. The issuing local Owner is revoked or loses that project grant after intake.
   `auth.go:63` revokes only the specified principal; it does not revoke the device
   principal or delete that principal's grants.
3. `planningOwner` still sees the device's active OWNER row and its old project
   grant and returns success. Normal request authentication would reject/intersect
   this actor through `auth.go:97` → `remote_auth.go:21`.
4. This weaker helper is consumed by `planningSnapshot` (`planning_brief.go:194`),
   `compileIntentPlan` (`planning_compile.go:35`), and coordinator preflight
   (`intent_runtime_windows.go:82`). Consequently, an independent verifier or
   scheduler can continue accepting/compiling/resuming the bound intent after
   the originating delegated authority is no longer current.

The defect is established by source/call-chain review. No exploit, production
mutation, native adversarial retry, or runtime reproduction was performed.

Required repair: close the grant query rows, apply the same current
`constrainRemotePrincipal` rule, propagate failures, and only then require OWNER
plus the project grant. Preserve `DeviceID` so downstream access checks also use
the current constrained principal. Add bounded domain regressions for an active
remote Owner, revoked issuing Owner, and removed issuing Owner project grant;
demonstrate rejection before compilation or automatic resume can proceed.

## Evidence independently checked

- All 18 source-manifest SHA-256 values match the frozen checked-out source.
- Recomputed hashes and byte lengths for 104 files under the I1 receipts directory
  and the referenced original W13 browser run are recorded in
  `independent-recomputation.json`.
- Parsed raw Go JSONL: 14 substantive top-level tests and 17 rejection subtests
  passed, with zero failures/skips. The 32 Go test-pass entries include the
  no-op `TestIntentNativeChild` entrypoint, which is excluded from substantive count.
- Read native test implementation and raw I1-NATIVE marker: actual AppContainer
  fixture qualification, purpose-blocked planning, planning Run and GENERATED
  JSON, separate authenticated Task/Goal acceptance, exact compiled two-node DAG,
  business purpose gate, and both downstream Tasks accepted. This remains FIXTURE;
  the child emits deterministic data and does not establish model accuracy.
- Read actual-browser intake script and both raw reports. The PASS run has four
  checks covering one required natural-language input, draft refresh, deliberate
  committed ACCEPT ACK loss and replay, durable singleton objects, and visible
  planning versus business counts. The first run's four functional checks passed
  but its overall cleanup FAIL is retained.
- The referenced W13 run records 15 preceding functional checks, including actual
  412/draft retry, and then FAIL at resources/light/320 overflow. The affected
  reason-code wrapping is fixed and only that 320px viewport has a later PASS.
  The full W13 suite is not represented as passing after the fix.
- Visually inspected the 390px planning screenshot and the 320px resources
  screenshot; the displayed blocking state and wrapped reason code agree with
  the narrow report. Reviewed final Vite build PASS output.

The browser reports retain their pre-final-commit `head=3a89a61` metadata. Their
recorded actions also exercise changes later committed in edb9543. The final
18-file manifest binds the frozen source now; it is not an execution-time dirty
tree digest and must not be described as one. The evidence is author-run raw
evidence assessed alongside current source. No fresh suite was run by reviewer.

## Source findings otherwise consistent with the bounded slice

The intake keeps the raw statement USER_STATED, actor-bound, and durably unique;
the browser persists original submission and idempotency identities. A service
created planning Goal/Task has real registered deterministic checks and context.
The private GoalBrief parser rejects unknown privilege fields and later revisions.
Authoritative facts must quote accepted source Requirements with exact basis and
refs; model suggestions remain non-authoritative. Exact raw/context/budget vectors,
bounded acyclic same-Goal nodes, supported check/action pairs, and explicit unknowns
are verified before trusted compilation. Task acceptance alone cannot compile.
Cross-Goal lineage is carried as exact accepted Artifact/Receipt input refs and
ImpactLinks, not cross-Goal Task dependencies. Unknown business decisions create
visible resource requests without inventing a business Goal.

## Limits and retained blockers

Automatic business compilation supports only explicit positive Owner JSON-literal
delivery forms and the `json_report` / `orchestration.json-equals` catalog. General
natural-language research execution, provider/model capability, live business Goal
acceptance, protected verifier isolation, and complete product E2E are unproven.
The narrow planning LIVE source branch has not been exercised by this evidence.
No formal acceptance case or ledger is upgraded by this review.

The author's `BLOCKED_HYGIENE` remains: the prior SQLite cleanup failed and policy
rejected removal of `.local/intent-browser-3lyxh0c2`. The later metadata-generation
policy block is retained in the handoff. This reviewer did not inspect, delete,
retry, repackage, or work around those blocked actions or paths. A source repair
does not clear either hygiene/history limitation.

# Minimal Desktop-exit preparation settlement slice

Baseline: Main `998fc6330ba735056cd31f8ebf68dd50a8251c1b`, CP684. Source-only implementation and later Root-owned fixture tests; no Native/model/App test or replay authorization. The existing failed Task remains consumed. Legacy `real_model_requests=2` means cumulative Host Task count here, not confirmed model inference count.

Exactly four source paths suffice:

1. `internal/domain/harness_preparation_windows.go`
2. `internal/domain/runtime_drain_windows.go`
3. `internal/domain/harness_preparation_windows_test.go`
4. `internal/domain/runtime_drain_windows_test.go`

No schema, renderer, SDK, Native permission, budget, retry or process-kill change is necessary. Optional shutdown diagnostic improvements are a separate slice, not required in these four paths.

## Existing trusted persistent anchor

There is no need to introduce a generic externally supplied stopped receipt or change STARTED to OBSERVED. C5 already persists the reason `native preparation failed before model launch: <known reason>; proof=<Hash(audit)>` in the same transaction as the sealed audit and terminal Task/Run.

The positive authority chain is:

- `adapters/runtime/codex_qualification_windows.go:108–131` only accepts the private concrete `*qualifiedHandle`, after done closes, with no delegate attempt or delegate, a real preparation error, original Host-pinned launch/boot/native/helper/profile/source identities and either explicit no-child or complete Job-zero/streams/cleanup evidence.
- `internal/domain/runtime_harness_windows.go:1187–1198` waits the handle and obtains that concrete accessor result; public API JSON cannot implement or replace this private type.
- `harness_preparation_windows.go:36–44,98–222` checks this proof against the consumed fence, empty model identity, exact worker/locator/manifest/epoch, absent model markers, settled queue and original submission before atomically recording the reason/audit/terminal result.
- A production-source search for runtime_dispatches reason writes finds C5 line 211 as the sole writer that retains STARTED. `runtime_coordinator_windows.go:997` sets UNKNOWN for non-OBSERVED rows. `runtime_harness_windows.go:1261` sets UNKNOWN or preserves OBSERVED. Initial insertion in `runtime_dispatch.go:105–116` creates PREPARED without an injected reason. No direct runtime_dispatches mutation route was found under internal/api. Task text or uploaded LOG/JSON therefore cannot create an eligible STARTED reason anchor through the inspected ordinary API path.

This is a source-level Host persistence boundary, not cryptographic protection against arbitrary direct database modification, privileged restore or compromised Host code. A sealed or matching-looking LOG by itself is not authority. The validator must begin from the actual original dispatch's internally written exact reason, then verify its audit and all bound facts. Do not allow external JSON to set or repair that reason.

## Required correction

Keep generic RuntimeDrainSnapshot raw counts intact. During `quiesceRuntime(..., desktopExit=true)` only, under its existing admission/scan fence, accept a STARTED candidate only after read-only durable revalidation of this C5 anchor and its exact original Run/Task/epoch/executor/worker/manifest/submission/source binding. Validate the audit digest using the same existing Hash and content-hash functions; require exactly the intended sealed audit, known schema/reason, no delegation, the correct no-child or complete stopped branch, nil model identity/external result/exit fields, zero observation sequence/hash, original queue settled and model marker counterevidence absent. Use consistent transaction reads for the decision. An error or ambiguous state is a blocker.

Only subtract validated C5 candidates from the Desktop-exit dispatch count. Do not change persisted state, mint a new request/Run, treat UNKNOWN as eligible, or bypass any active workers/runs/effects/commands/reservations. Retain `completedLocalUnknownCosts` and managed qualification/startup gates exactly. Keep QuiesceForRelease and verifier replacement behavior unchanged.

## Meaningful fixtures for Root's later test scope

- Current concrete C5 failure: original STARTED remains consumed; after workers finish, Desktop quiescence succeeds; generic release still blocks; recovery does not launch again and audit/failure count stays one.
- External fake LOG or Task FAILED without the internal reason anchor: remains blocked.
- Original reason with missing/malformed/duplicate/conflicting audit, changed content hash, wrong epoch/Run/Task/source/owner/worker/manifest: blocked.
- Ordinary STARTED, UNKNOWN, second unresolved dispatch, active worker, unresolved command or reservation: blocked.
- Delegate/model identity, model marker present or unreadable, unknown child status, missing Job-zero/streams/cleanup: blocked.
- Failure rollback and existing idempotent C5 settlement continue to preserve history; no process launch is needed for these fixtures.

This slice repairs shutdown eligibility for a proved no-model stopped preparation, not the underlying preparation failure. The original live flow's qualification capture remains untouched and its Root Job remains governed by the original deadline.

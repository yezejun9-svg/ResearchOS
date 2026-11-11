# C5 stopped preparation: local zero-hold settlement supplement

Decision: implementable within the existing **four Windows domain files**, with a newly registered contract revision. No extra generic file is necessary. This is source architecture only; no code, fixture, Native/model or live Task was executed. Main baseline is `8fa407dbf393f94424e1612748d9e6041db35fcd`; domain/budget source remains the prior 998fc content. The failed rev2 candidate and test01/test02 remain immutable history.

## Evidence and scope

Test02 compiled and ran: eight top-level tests, six PASS and two positive failures. Both failures report the original `RESERVE/runtime-local-launch/<run>/1` as unresolved. The 24 new negative cases share that baseline reservation, so their green output is insufficient evidence of each intended rejection. Test01 was compiler VirtualAlloc errno1455 before any fixture; it is not a source assertion failure.

`internal/domain/budget_scopes.go:200–277` creates the exact local launch hold: zero money, UPPER_BOUND, request/event `runtime-local-launch/<run>/<epoch>`, Goal budget policy, no reservation parent. `releaseCompletedRuntimeLocalLaunch:8–60` deliberately requires a native runtime observation/dispatch proof that C5 does not have. Do not weaken that function or fabricate an observation.

`internal/domain/budget.go:270–404` provides the existing append-only ledger path. It checks run-bound policy, reservation/run/request/currency, terminal duplication and event idempotence. It also permits UNKNOWN settlement in general, so the **new C5 helper must independently reject UNKNOWN**. Its idempotency comparison includes occurred_at: submitting a fresh Now() on repeated calls is not idempotent.

Exact implementation paths remain:

1. `internal/domain/harness_preparation_windows.go`: Windows-private settlement helper and its invocation inside the existing C5 transaction.
2. `internal/domain/runtime_drain_windows.go`: retain the reviewed Desktop-only dispatch discount; no reservation discount or ledger write here. Change only if needed for exact error classification/testability, without changing gates.
3. `internal/domain/harness_preparation_windows_test.go`: local ledger settlement, transaction rollback, idempotence and concrete no-child regression.
4. `internal/domain/runtime_drain_windows_test.go`: genuine passing baseline and isolated counterevidence tests.

`budget_scopes.go`, `budget.go` and `budget_restart_test.go` are read-only references. They need no edits or Windows imports. If an author instead proposes shared generic refactoring, Root must separately add exact `internal/domain/budget_scopes.go` and `internal/domain/budget_restart_test.go` to a new lease and review it; this contract does not authorize that larger alternative. Existing generic tests such as `TestCompletedRuntimeLocalLaunchRelease` can be included in Root's later bounded regression scope without editing their source.

## Authority and atomic order

Only `finishHarnessPreparationFailure` may call the new private helper, after accepting the original concrete-handle C5 proof and validating its original fence. No public API, supplied receipt, readiness flag or external bool is accepted as proof. Keep the exact original Task/Run/epoch/worker/executor/manifest/source/submission and model-marker counterevidence checks.

Within the **same existing write transaction**, write/validate the terminal Run/Task, sealed C5 audit and internal reason as now, then validate and append the local RELEASE before committing the terminal projection. Any mismatch/query/append error rolls back the whole new settlement, including its audit/events/ledger writes. Do not make a second transaction that could leave a terminal success projection with the hold still unresolved. The idempotent already-settled branch must validate the same original C5 proof and valid existing RELEASE; it must not append a second release or duplicate failure/audit/events.

Both already-supported C5 branches are sufficient: explicit no-qualification-child with PID zero, or original qualification PID nonzero plus Job-zero, streams drained and cleanup complete. Both additionally require **no model delegation** and unchanged model identity/markers. Do not broaden these predicates. The second branch only settles the app's explicit local launch zero-hold; it does not assert that Native startup made zero internal API calls or incurred zero platform charges. Those remain unmeasured. Restricting to no-child alone is unnecessary for this local ledger meaning and would leave a valid stopped-child C5 unable to close.

## Exact hold and RELEASE

Derive the request key solely from the already validated Run ID and canonical lease epoch, using the same convention as reserveRuntimeLocalLaunch. Fetch the original exact project's ledger rows for that Run/request. Require one original RESERVE with matching object/project/run/request/event identifiers, no parent reservation, UPPER_BOUND, valid Receipt(hold), valid zero money/currency and Goal-bound policy. Bind Goal through the original Task and reuse appendBudget's run scope validation. Do not accept a prefix match, other epoch, alternate provider event, caller-selected policy or a latest UNKNOWN record.

For an unclosed valid hold, append through **existing appendBudget**:

- operation RELEASE, same policy/run/money/currency and exact provider_request_id;
- provider_event_id `<request>/released`, reservation_id exactly the original hold ID;
- cost_basis ACTUAL and one generated occurred_at for this new release.

Keep the original RESERVE unchanged. No deletion, count subtraction, RECONCILE, fabricated COMMIT, model/provider ledger write, other Run/epoch release or automatic repair is permitted.

If a matching RELEASE already exists, verify its Receipt, exact reservation link, policy/project/run/request/event, zero money/currency and ACTUAL basis against the original hold, and that the request history has no conflicting UNKNOWN/COMMIT/RECONCILE/duplicate terminal. Return idempotently or reuse the recorded complete request payload; do not invent a new timestamp. Missing/malformed/ambiguous hold or conflicting history is an error, not a success-shaped no-op. A valid already released hold does not grant execution or a fresh Task.

## Unchanged safety gates

Raw RuntimeDrainSnapshot still counts every unresolved reservation and consumed STARTED dispatch. Desktop may discount only strongly revalidated C5 dispatches as in rev2. It must not discount Reservations. Generic QuiesceForRelease/replacement remains blocked by STARTED. Existing completedLocalUnknownCosts, provider/model UNKNOWN, paid holds, managed qualification and startup gates remain unchanged. No cleanup decision may become equivalent to Task FAILED or LOG presence.

## Required fixture corrections

1. Establish success first using the unchanged real claim/C5 fixture: its original local RESERVE remains byte-identical, one valid zero RELEASE is appended, raw Reservations becomes zero, raw UnresolvedDispatches remains one, Desktop exit succeeds after worker completion, generic release still fails. Repeat settlement, recover/scan and check one Task/Run/audit/failure/RELEASE with no new launch. Keep the concrete private no-child handle case. Add a synthetic complete-stopped-child C5 branch without executing a child.
2. Exercise ledger-negative mutations **before C5 settlement**: missing/duplicate hold, wrong Run/epoch/project/policy/request/event, nonzero/invalid currency or receipt, parent reservation, latest UNKNOWN, conflicting or malformed terminal. Assert intended error plus transaction rollback and no RELEASE; do not remove the actual reserve from the positive fixture.
3. For drain-negative mutations **after successful settlement**, first prove an equivalent clean control can exit with Reservations zero. Then mutate one intended fact on a fresh settled fixture (or explicitly resume the controlled fence before mutation) and require the expected proof/accounting rejection, not merely any error. Preserve the original 24 boundaries. The extra reservation case should create an unrelated reservation after C5 has released only its own; the unknown-money case must remain unknown.
4. Correct coverage labels: `missing_audit` previously meant unsealed, `unreadable_marker_root` meant nonexistent root, `wrong_owner` changed project_id. Name these accurately; add a real same-project principal/owner mismatch if claiming it. No ACL simulation is implied. Test marker existence/uncertainty with disposable files only.
5. Add rollback/error propagation and exact existing-release idempotence tests. Do not swallow setup SQL errors, make a fake always-failing baseline, clear ledger rows, widen safety policy, or skip the concrete positive case. A new candidate and Root-registered Go-only scope are required; no old test scope or actual Task may be replayed.

No current original Task is repaired by this source-only slice. Old scope consumption, failed Task/Run, cost-unknown evidence and actual forced cleanup remain historical facts. This change alone does not qualify Native permissions, prove platform API billing, permit a model retry or establish product readiness.

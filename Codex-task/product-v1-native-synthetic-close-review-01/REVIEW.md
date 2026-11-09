# Native synthetic flow01: Desktop close diagnosis

Decision: **SOURCE_DEFECT_IDENTIFIED; actual shutdown reply not recorded**. Formal increment 0; product increment 0. This is a read-only diagnosis, not permission to rerun the failed Task or an assertion that the original Job has stopped.

## Evidence and causal chain

The authorized public result records exactly one DOM submit, Task `c9fc3e4dc1ea5d34a0ca003a983b43c6`, Run `a46af22fb058915f9f7119b2d7d73f8f`, epoch `1`, request `b8e0abb5-503d-4795-9a43-1d3772382315`, project `7c71e06cdc78d25b1ad471149fe92f8f`. Events are TASK_QUEUED, RUN_STARTED and TASK_TERMINAL. The final Task is FAILED/HARNESS_UNAVAILABLE with the specific preparation-before-model message, null result, and retryable false. The result reports `APP_CLOSE_UNCONFIRMED_ROOT_JOB_MUST_CONTAIN` after its bounded close wait, helper_pending false, elapsed 51446 ms.

The following source chain explains a persistent shutdown refusal without a leaked Native worker:

1. `internal/domain/runtime_harness_windows.go:420–421` emits this specific public message when the failed Run execution report is the preparation-failure report.
2. `internal/domain/harness_preparation_windows.go:98–222` validates the concrete preparation proof, writes its sealed Host audit, marks Run/Task FAILED and queue/children settled, but its SQL at line 211 changes only dispatch reason and updated_at. **Dispatch state remains STARTED**, with empty model identity and zero observation sequence. The existing test at `harness_preparation_windows_test.go:104–109` explicitly requires this state.
3. `internal/domain/runtime_drain_windows.go:40` counts every PREPARED/STARTED/UNKNOWN dispatch as unresolved. Lines 92–98 reject quiescence while this count is nonzero. Terminal Task/Run status does not remove that blocker.
4. `apps/control/main.go:328–337` calls that quiescence routine before stop(); a rejection resumes the admission gate and returns an error without stopping Core. `internal/host/desktop_management_windows.go:181–188,198–203` returns MANAGEMENT_REJECTED rather than successful shutdown.
5. `apps/desktop/main/lib/desktop-management.js:770–775` rejects non-RESULT shutdown as SHUTDOWN_REFUSED. `apps/desktop/main/main.js:437–448` already prevented the window close, and displays a warning on rejection. This non-smoke branch emits no corresponding bounded shutdown diagnostic to the controller.
6. The pinned Playwright `lib/coreBundle.js:43905–43912` calls app.quit(), disconnects its inspector, then waits for its application close event. Thus the recorded `Debugger ending` line proves neither Electron nor Core exit. The controller's `real-electron-flow.mjs:907–922` races app.close against its deadline, records uncertainty, and correctly leaves containment to the original Root Job.

This is a source-demonstrated incompatibility and a strong explanation of this exact failed-preparation flow. The public receipts do not contain the private SHUTDOWN response or a drain snapshot; I have not queried the live processes or database. Therefore I do not claim the actual displayed warning, exact live counter values, or absence of other blockers was directly observed. The qualification failure's underlying reason is a separate question; its private capture was not read.

## Comparison and exclusions

Visual05 records zero submits and app_close_resolved true (elapsed 23233 ms). It never created a consumed preparation dispatch and does not exercise this mismatch. Its console also contains `Debugger ending`, confirming that line is not a useful discriminator. Normal-mode shutdown_confirmed logging is absent; the main.js shutdown_confirmed branch is SMOKE-only.

The source does contain a renderer beforeunload guard in `apps/web/src/continuity.jsx:142–146`, but only for dirty file drafts. Nothing in the authorized receipts proves that condition. There is no evidence justifying a beforeunload bypass, forced window destroy, PID kill, process-name kill, loosened runtime policy, or longer deadline. Core's background Wait paths are not needed to explain the discovered refusal and were not proven to be the live blocker.

## Minimal next source slice

Prefer a **Desktop-exit-only settlement validator**, leaving the consumed STARTED record, generic RuntimeDrainSnapshot, QuiesceForRelease and replacement/release rules unchanged. Do not simply filter by terminal Task status, a reason prefix, absent files, or caller-supplied receipt JSON.

Suggested exact production paths:

- `internal/domain/harness_preparation_windows.go`: factor a read-only validator for the durable preparation outcome already written by the concrete-handle settlement. Require the original project/Task/Run/epoch, runtime/source/policy/manifest/worker/locator binding; terminal FAILED Run and Task, settled queue/children, nil model external ID/exit/result, unchanged empty dispatch identity and zero observation, exact reason-to-sealed-audit digest binding, correct schema and no-model-delegation facts. Accept only the known no-child branch or the complete original qualification Job-zero/stream-drained/cleanup branch. Recheck the original model authorization/write-intent markers for counterevidence. Missing, conflicting, malformed or uncertain facts fail closed.
- `internal/domain/runtime_drain_windows.go`: only inside desktopExit, and under the existing admission/scan fence, validate each candidate original STARTED dispatch through that helper before excluding it from the Desktop-exit unresolved count. Use a consistent database observation; keep all other active worker/run/effect/command/accounting gates. UNKNOWN and unrelated STARTED dispatches remain blockers. Preserve the source state and no-replay history. Do not automatically migrate or mutate this already failed actual run.
- `internal/domain/harness_preparation_windows_test.go` and `internal/domain/runtime_drain_windows_test.go`: extend the current settled-before-model fixture to show Desktop exit succeeds only after worker removal; generic release remains blocked; recovery still produces one Run/one audit/no new launch. Negative cases must include reason-only forgery, wrong/missing/duplicate audit, wrong identity/source/epoch, marker present or unreadable, incomplete cleanup, UNKNOWN dispatch, second unresolved dispatch, active worker and unresolved command. These are proposed fixtures, not tests run by this review.

Optional independent observability slice: `apps/desktop/main/main.js`, `apps/desktop/main/lib/desktop-management.js` and existing Desktop management tests. Emit bounded public-safe shutdown requested/rejected/accepted/owned-exit evidence with exact Core identity. Preserve sanitized rejection code/category instead of collapsing every rejection into SHUTDOWN_REFUSED; do not forward arbitrary private error text or add a force-close fallback. This exposes the next actual cause if another gate remains after the settlement fix.

Changing dispatch to OBSERVED would fabricate a native model observation; adding a new terminal dispatch state would require a broader schema/recovery/release audit. Neither is the minimal proposed correction.

## Limits and safety record

Only authorized public receipts, current source and local public SDK code were read. No private current qualification capture, auth/config/account files or live database was read. No App, Native CLI, helper, model, test, build, process signal or network operation was invoked. Original Job deadline and consumed Task remain untouched. All reviewer writes are new C report artifacts. Exact hashes are in REVIEW.json; archive selection uses relative paths under the C review root.

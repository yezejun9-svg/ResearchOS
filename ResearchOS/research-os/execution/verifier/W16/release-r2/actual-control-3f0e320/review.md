# R2 actual-control independent review — NEEDS_FIX

Frozen source: `3f0e320d44c50e19230288ef8ced491f9175efd9`; evidence: `6bfeb94403aef62f441ffc1f6ddb72d3cd3b8815`. Scope is the same-user actual-control fixture. Both findings below are acknowledged by the author. This historical review remains tied to that exact source; later fixes require a separate delta review.

## Findings

1. **P1 — R2-CONTROL-READY-IDENTITY** (`ops/supervisor/control_fixture_windows.go:293–309`). `Ready` combines `Alive(p)` with an HTTP 200 from the configured address. Its token is unused; the response does not prove the child owns that listener, has acquired its root lease, or has completed startup. If another healthy local process owns that address while the new child is still initializing, the checks can both pass before the child fails its listen call. Bootstrap/switch can therefore report readiness for the wrong endpoint. Require readiness over the existing exact-peer/HMAC capability, bound to child/root/lease/listener/startup, with one directed check that rejects the old logic.

2. **P1 — R2-CONTROL-RECOVER-AFTER-QUIESCE** (`internal/domain/runtime_coordinator_windows.go:178–180`; `apps/control/main.go:186–205`). Main schedules coordinator recovery and private drain independently. If quiesce wins `scanMu`, it marks the coordinator quiesced and can acknowledge idle; delayed `Serve` then takes the mutex and unconditionally calls `Recover`. That recovery can still reconcile existing dispatch/effect/checkpoint records or mark a missing journal UNKNOWN after the receipt. `Scan` checks quiesced, but startup recovery does not. Require a completed-startup barrier before drain/readiness plus lock-protected ordering, with one forced-schedule boundary check.

These are source-grounded findings, not newly executed fault injections. The author confirmed both current gaps; root has authorized minimal fixes and directed checks without replaying the full suite.

## Verified evidence and bounded behavior

All 12 listed source hashes and 4 evidence hashes match. The evidence commit differs from source only by the receipt directory. The pinned Go executable and frozen migration 0019 hashes match the manifest. Raw final output has 8 top-level PASS results, including the parent actual-control test with 7 passing subcases; no FAIL. This is 7 actual-control cases + 2 focused boundary tests + 5 existing engine/journal regressions, not 15 independent top-level tests. The author records native exit 0. Earlier two diagnostic failures remain preserved and are explicitly labeled copied command output; they were not replaced by final raw.

The actual idle subcase runs the real control executable twice on one disposable authority root: old PID 45160 and new PID 72040, distinct creation times, identical image SHA256 `0b405d464de64eb89d6dbce5629edde037a437be808ae11eac62940da34ceb2b`. An HTTP-created Project `11c727678ba6768dec091e87a9609b6b`, revision 1, retains full profile digest `77e04d7156997eca1260a8ca4336f6d6568b2773661fe96be22fd824a2ba1122` via actual GET. This is same-build continuity, not different-release improvement.

Source and raw support pre-DB data-root lease acquisition for administrative/service paths, single coordinator borrowing, failed-constructor return, HTTP mutation/inflight fencing, busy scan refusal, global active Run/dispatch/effect/reservation checks, FULL checkpoint busy refusal and write-admission recovery, normal exit with exact-process wait/exit-code check, and lock reacquisition before next start. Private commands use inherited capability, exact peer identities, same-user local pipe ACL/remote rejection, HMAC and operation/epoch/root/nonce/receipt bindings. DRAIN_UNKNOWN and EXIT_UNKNOWN remain durable and do not permit automatic Switch/Stop/Start/Reconcile replay. Lost QUIESCED is a read-and-discard-before-journal injection; lost COMMIT_EXIT omits EXIT_ACK. Cleanup force-stop is excluded from acceptance evidence.

## Remaining scope

No release_host/R1 packaging or production authority-DB integration is accepted. Actual-control rollback is deliberately unavailable; the older marker-fixture rollback keeps its prior scope. Native RESUME, supervisor capability reattachment, different-build canary/improvement, SCM identity isolation, LIVE, 6-hour behavior and formal W16/C20/A16 remain unaccepted. No stopped S2 work or native-source-binding retry was performed.

Reviewer actions were source/raw inspection, git comparisons and SHA256 recomputation only. See `independent-recomputation.json` and `review.json`. An initial read-only hash script used a wrong migration filename and failed before emitting its combined result; the corrected exact-file recomputation below is authoritative. No source, original raw, ledger or migration was edited.

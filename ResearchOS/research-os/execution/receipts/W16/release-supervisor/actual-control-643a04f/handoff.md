# R2 actual-control readiness and startup fence correction

Owner: codex:/root/control_drain. Lease: R2-independent-supervisor-v1.
Source tip: 643a04f593b8b5842f09b4d92ca29a5870d0c020.
Production correction: c32e5248e4d53443147aebaeb6649ee4636adc9b.
Test-only follow-ups: 5c3608c8711c20cbe7d4672cd77d5d4232250f87 and 643a04f593b8b5842f09b4d92ca29a5870d0c020.
Independent acceptance: PENDING. No self-acceptance is issued.

The earlier 3f0e320 evidence remains historical; independent review found an unrelated-listener readiness false positive and a pre-recovery quiesce fence hole. This correction addresses only those two findings.

## Corrections

- ControlFixtureDriver.Ready requires private authenticated READY proof for the exact process identity, bootstrap token/epoch, data root and listener, with the process holding its data-root lease and startup recovery complete. It checks the child identity around the HTTP probe. A read-only STARTING/bootstrap PID-zero journal observation is supported without opening the mutation drain path.
- Startup recovery and release quiesce share scanMu. Quiesce before successful startup recovery returns busy without installing a fence. StartupReady is only true after recovery completes; repeated Serve does not rerun startup recovery after startupComplete. Abort preserves coordinator serving and releases its temporary scan fence.

## Evidence and chronology

1. Production correction c32e524: `go test ./internal/domain ./ops/supervisor -run '^(TestRuntimeDrainLeaseAndScanFence|TestActualControlDrain)/(idle_same_root_switch_preserves_data|occupied_listener_cannot_prove_child_ready)?$' -count=1 -v -timeout=2m` was recorded in `../actual-control-c32e524/targeted-tests.raw.txt`. Overall exit 1 / FAIL. The optional suffix accidentally selected all actual-control child cases. Startup/lease/abort and idle same-root data-preserving restart passed, as did the six prior refusal/lost-ACK cases. The new occupied test failed its live-child premise; no exact cause of child exit was established. This run remains FAIL, with only its named passing checks used as scoped evidence.
2. Test fixture follow-up 5c3608c replaced the timing-dependent SQLite delay with a newly created suspended actual-control executable, retaining its original native process/thread handles for identity checks and disposal. Exact occupied-only invocation failed before any child creation because the prerequisite HTTP listener at 127.0.0.1:9540 timed out. Overall exit 1 / FAIL; raw retained in `../actual-control-5c3608c/occupied-listener.raw.txt`.
3. Test fixture 643a04f bounded the remaining fresh listener startup attempts to two (prior failed probe counts one of total cap three). Exact invocation: `go test ./ops/supervisor -run '^TestActualControlDrain$/^occupied_listener_cannot_prove_child_ready$' -count=1 -v -timeout=1m`. Exit 0 / PASS; `occupied-listener.raw.txt`. First remaining probe returned HTTP 200 at 127.0.0.1:56847, so the second remaining probe was not used. Thus two total startup probes were used across attempts 2 and 3. Only then was a new CREATE_SUSPENDED actual-control child created: PID 88884, creation 1790797665102339200, image SHA256 f7b0aa9bce1f9228ec9fde33b6da625ed1fceb97adf5774cd982171dfd1d6c1d. Ready rejected the unrelated HTTP 200 while the original child handle was still alive. Cleanup terminated and waited on that same original disposable child handle; it did not locate or operate on any prior PID.

The startup and idle passing checks are bound to c32 production source. Git diff c32e524..643a04f changes only ops/supervisor/control_fixture_windows_test.go. The occupied passing check is bound to 643 source. There is no claim that either failed run became a passing full suite, and no extra test or network retry was run after the successful bounded check.

## Frozen limits

This is same-user temporary development fixture evidence, not live service, SCM, production release, protected held-out, R1 integration or final product acceptance. Stable and candidate restart use the same actual-control executable bytes and distinct process identities; different release bytes remain untested. Actual-control compatibility/rollback remains unimplemented. The persistent release_host/R1 wiring and next slice remain paused. No I2 exhausted SOURCE input was re-probed. Migration 0019 remains unchanged at SHA256 54ff6eb7a7ca588df738f5bd68b6f6851d86916cef435abaac15d1f8bd6e131e.

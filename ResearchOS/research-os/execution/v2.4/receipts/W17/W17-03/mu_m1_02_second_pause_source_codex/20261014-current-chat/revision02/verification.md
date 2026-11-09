# Mu M1 second PAUSE R2 author verification

The R2 candidate is commit `8f50cb57ff821554aef17e9a9bd5208935489d50`, tree `361ead86ee812d5e040fe1d2cde2a92297eb639f`, on base `36b2634bfebe6201a14b7661f2dce32b7f1a5098`. The detached worktree is clean. Only `internal/domain/runtime_coordinator_windows.go` and `internal/host/runtime_pause_windows_test.go` changed under CP486 scope. It is an author candidate for independent review; formal acceptance increment remains **0**.

The 15-second periodic Host heartbeat now requests a current-pause maintenance purpose. `dispatchGate` resolves the pause intent for the exact Run and epoch inside its admission transaction, then passes the resolved pause ID through the existing purpose gate. The usual lease, executor, Owner, Goal, current activation, manifest, session, queue and cutoff checks still run. When no current valid PAUSE exists, a BLOCKED Task remains rejected. A failed heartbeat still cancels the Bridge.

All tests used working directory `D:/作品集/ResearchOS/research-os/.local/worktrees/mu-m1-second-pause-20261014` and executable `D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe`. Environment: `GOROOT=D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go`, `GOMODCACHE=D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod`, `GOCACHE=D:/作品集/ResearchOS/research-os/.local/go-cache/mu-m1-core-20261014`, `GOTMPDIR=TEMP=TMP=D:/作品集/ResearchOS/research-os/.local/go-tmp/mu-m1-review`, `GOPROXY=off`, `GOSUMDB=off`, `GOTOOLCHAIN=local`, `GOWORK=off`.

Final domain argv (**06-domain-regression**, exit 0):

```text
go.exe test -mod=readonly -json ./internal/domain -run '^(TestW12BudgetLeaseTakeover|TestCompletedRuntimeLocalLaunchRelease|TestRuntimePause.*|TestRuntimeLocalLaunchRepeatedEpochsAndReleaseBindings)$' -count=1
```

Final native argv (**07-native-final**, exit 0):

```text
go.exe test -mod=readonly -json ./internal/host -run '^TestProductMu(Pause(Resume|Cancel|PreparedLeaseRecovery|ToolPublishAfterPause)|SecondPause(Resume|ModelAcrossHeartbeat|ToolAcrossHeartbeat|RevocationAcrossHeartbeat))Native$' -count=1 -pause-candidate-assets-dir 'C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-wire-20261014/.local/m1-01' -local-runtime-verifier-executable 'D:/作品集/ResearchOS/research-os/.local/mu-m1-core-20261014/runtime-verifier.exe' -pause-native-evidence-dir 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W17/W17-03/mu_m1_02_second_pause_source_codex/20261014-current-chat/revision02/07-native-final/native'
```

The native run passed all eight top-level tests and all four revocation subtests, with zero skips and zero failures. The second model response and separate epoch-2 Host tool call each remained in flight for 17 seconds after an ordinary HTTP PAUSE. In both cases `heartbeat_at` advanced during the wait, the pause reached `PAUSED_CONFIRMED`, the same Run resumed to epoch 3 and settled, four queued commands were consumed once, and the budget ledger retained one correctly bound RESERVE/RELEASE pair per epoch. The tool case verifies the actual Host write to `notes.txt` occurred after PAUSE; its provider effect and dispatch evidence are exported. The original first-pause resume, cancel, prepared-lease recovery, second-pause resume, and first-pause tool publication cases also passed.

The four negative subtests first let the second PAUSE survive the heartbeat, then remove authority. HTTP CANCEL and current Owner revocation use native APIs; Goal and lease changes are explicitly labeled isolated native-DB fixture injections. Each produced a cancelled epoch-2 Bridge, no epoch-3 activation, no extra tool call and no queue replay. Canonical DB, Bridge and queue evidence is in the corresponding `07-native-final/native/` directory. Synthetic model responses were used; no live model or production/Desktop data was touched.

`attempt-ledger.json` preserves all seven new author Go test attempts: six PASS, one FAIL, no skips. Attempt 01 failed to compile due to a test-closure typo; the raw failure remains. The previous author 23 attempts (11 fail, 1 skip), previous independent 5 attempts (2 fail), and the earlier frozen 18/7 and 5/2 counters remain separate and unchanged. The independent R2 failure is not counted as an author retry.

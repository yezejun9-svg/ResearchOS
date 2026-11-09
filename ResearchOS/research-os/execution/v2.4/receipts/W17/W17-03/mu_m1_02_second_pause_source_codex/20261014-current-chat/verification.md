# Mu M1 second PAUSE source candidate: author verification

Candidate commit `36b2634bfebe6201a14b7661f2dce32b7f1a5098`, tree `bea72c5cdbb341e4d67bd91331803ec6e8013e3b`, is a clean detached worktree based on `ff5ac2047566a52388188b84f267217d8582c571`. The commit changes the nine files authorized by scope v3. It is a source candidate for independent review, not formal W17/Mu acceptance. Formal increment: **0**.

The final tests ran with working directory `D:/作品集/ResearchOS/research-os/.local/worktrees/mu-m1-second-pause-20261014` and `D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe`. Environment: `GOROOT=D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go`, `GOMODCACHE=D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod`, `GOCACHE=D:/作品集/ResearchOS/research-os/.local/go-cache/mu-m1-core-20261014`, `GOTMPDIR=TEMP=TMP=D:/作品集/ResearchOS/research-os/.local/go-tmp/mu-m1-review`, `GOPROXY=off`, `GOSUMDB=off`, `GOTOOLCHAIN=local`, `GOWORK=off`.

The exact Go argv for **22-domain-final** was:

```text
go.exe test -mod=readonly -json ./internal/domain -run '^(TestW12BudgetLeaseTakeover|TestCompletedRuntimeLocalLaunchRelease|TestRuntimePause.*|TestRuntimeLocalLaunchRepeatedEpochsAndReleaseBindings)$' -count=1
```

It exited 0. It includes the original W12 takeover and terminal release regressions, pause storage tests, phase-bound dispatch negative cases, four successive local-launch epochs with same-epoch no-ops, and ten forged RELEASE binding/receipt rollback cases. The forged RELEASE is inserted before the successor transaction because the real ledger's immutable trigger correctly prohibits editing an existing receipt. Each failed successor rolls back its Run epoch update and leaves the ledger unchanged.

The exact Go argv for **23-native-final** was:

```text
go.exe test -mod=readonly -json ./internal/host -run '^TestProductMu(SecondPauseResume|PauseToolPublishAfterPause)Native$' -count=1 -pause-candidate-assets-dir 'C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-wire-20261014/.local/m1-01' -local-runtime-verifier-executable 'D:/作品集/ResearchOS/research-os/.local/mu-m1-core-20261014/runtime-verifier.exe' -pause-native-evidence-dir 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W17/W17-03/mu_m1_02_second_pause_source_codex/20261014-current-chat/23-native-final/native'
```

It exited 0 with both tests passing, no skips. The first test runs the same Run through epoch 1→2→3 and two PAUSE/RESUME cycles, including an epoch-2 model response in flight. It checks two activations, four queue messages consumed once, one Host tool call, final settlement, and the actual local-launch ledger: each of epochs 1, 2, and 3 has one RESERVE and one RELEASE bound to its original reservation. The second test waits until PAUSE has put the Task in BLOCKED before allowing Host tool execution; the physical publication callback revalidates authority, one Host write occurs, and the queue still drains once. Model responses are synthetic; the AppContainer, Host, API, database, verifier, and workspace tool path are local native components. Live model calls: **0**.

The original native PAUSE/RESUME, PAUSE/CANCEL, and prepared-lease recovery tests passed in **20-native-regressions** (exit 0). Final native evidence includes `canonical-evidence.json`, `after-second-pause.json`, and the exported budget ledger rows. `attempt-ledger.json` hashes raw output and exit files for all 23 author attempts: 11 PASS, 11 FAIL, 1 SKIP. Attempt **13-native-budget** exited 0 but skipped because its invocation omitted required asset/verifier flags; it is excluded from passing proof. The CP483 native-failure lower bound maps to attempts 02–04 within this ledger and is not added again. Previously frozen author 18/7 and reviewer 5/2 counters remain separate and unchanged.

# Native folder visibility independent review

Decision: **ACCEPT_SOURCE_AND_NATIVE_OS_COMPONENT_ONLY**.

Reviewed candidate `b45008a754414cd795a4be396475aab8e74b2a8c` against base `b806a06fb62576c18dfd1e7174c1dfd929677506`, under CP431 scope SHA256 `87379d10cc49dd17038085d37d5f310390c241a805398f4ae34de0bd7170a4c4` and independent scope assessment `c0076635e7b4545a51cca52688c9df2155a446760f8cdce56339894ff72f58cd`. Author final bundle SHA256 is `2a2c2796ff3bfed1feeb1c3a46c80b00c98b4f5df3210840b2f5b5cce80d62fd`.

## Scope and source

Candidate is clean. The only two changed tracked files are `internal/host/native_folder_windows.go` and its new Windows test. All other tracked files match the base, including Native3 frames, ACL/SID/peer code, schemas, workspace registration authority, CLI and Desktop spawn code. Independently verified all 49 author source/evidence/reference/build pins both before and after replay. The original hidden Root dialog failure receipt is one of these immutable references.

The production callback is installed for empty and nonempty initial hints, has stable process lifetime, and only responds to BFFM_INITIALIZED. It synchronously shows the exact Shell callback HWND, checks actual IsWindowVisible before a possible second ShowWindow, and has no timer, deferred goroutine, global window enumeration or foreign HWND mutation. SetForegroundWindow remains best-effort. The optional hint still only preselects; the returned path still comes from Shell confirmation. Existing filesystem-only flag, PIDL free and UTF-16 KeepAlive remain intact.

The existing OS-thread lock now encloses COM STA initialization and shutdown. Signed HRESULT failure returns before installing CoUninitialize, while successful initialization including S_FALSE installs one matching uninitialize. All later error, cancellation and normal-return paths use this defer; selected PIDL freeing precedes COM shutdown by defer order. These rules match [Microsoft CoInitializeEx documentation](https://learn.microsoft.com/en-us/windows/win32/api/combaseapi/nf-combaseapi-coinitializeex). Startup visibility handling matches [Microsoft ShowWindow documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow): the initial call can be overridden by startup state; the return value describes prior visibility, not proof that display succeeded.

`nativeWorkspaceChoose` is unchanged: a chooser error returns before roots.Register/selections.Issue. Therefore native cancellation creates no authority. Actual GUI cases return empty paths and never instantiate a Host; related Host regressions use isolated fixture hosts and temporary folders. This is not a claim of zero fixture writes; live product/workspace authorizations remain zero.

## Independent execution

Replay used the pinned Go 1.27.1 toolchain, offline module settings, a C: temporary root owned by this review, and `-count=1`. It selected the native GUI test plus six related strict-frame, ACL, bootstrap, nullable-path and confirmed-selection tests. Result: 7 top-level PASS, 13 subtest PASS, 0 failures, 0 skips; exit code 0. Raw invocation/stdout/stderr/result are retained as `replay-01.*`.

Two independent helper PIDs, 44580 and 30500, both reported startup_flags=257 and startup_show=0. One opened empty then suggested initial path; the other reversed the order. Four real helper-owned `#32770` choosers were visible with rectangle `[660,285,1047,734]` and remained visible at least 500ms. Observed HWNDs were 9244878, 28839642, 17436226 and 31788758. The test controller enumerates exact helper PID, checks class/visibility/rect, rechecks PID immediately before WM_COMMAND/IDCANCEL, and never calls ShowWindow or forces focus. All four cancellations returned empty paths and the expected cancellation error. Both helpers exited normally.

Foreground HWND was 122883858 for all four observations, distinct from the chooser. **Visibility passed; foreground activation was not demonstrated and is not claimed.**

Actual COM checks after cancellation establish no leaked STA reference, preservation of an existing caller STA reference through a second invocation, failure-closed behavior for an incompatible MTA, preservation of the caller's MTA reference on failure, and cleanup after invalid UTF-16 input. Repeated chooser lifecycle passed in each helper. Successful folder-confirmation/PIDL conversion is statically reviewed and unchanged, but this component replay intentionally cancels every real chooser; Root's normal Desktop directory selection is separate evidence.

Both candidate executables were independently hashed and inspected using `go version -m`: control.exe SHA256 `41eca2a248a64fdbe31359de3433e04addca3dd5f08230b6144bfe54ff1fdf5a`; runtime-verifier.exe SHA256 `9ae7dc3d281951de7ff3af3aaf359c769d4305fa4b5907d1273517f51f5c0624`. Both report full candidate revision b450 and vcs.modified=false. This is provenance inspection, not execution of either product binary.

## Limits and preservation

No actionable source defect found within this two-file repair. This review accepts source and actual Windows component behavior only. Root's ordinary Visible Desktop flow with the integrated candidate remains required for first-use proof, including real chosen directory/configuration. W05, A10 and other formal or parent acceptance increments are zero. No model/provider calls, product tool execution, Root GUI/data/process/token operations or Source/Canon edits occurred. No claim of protected holdout isolation is made for same-user independent agents.

No frozen evidence was overwritten. Author bootstrap/encoding/invocation diagnostics and original hidden-dialog failure remain pinned. Read-only review discovery included missing-path/glob queries; these were not product test attempts. Review replay ran once and passed without retries. Go removed its generated temporary test contents; review temp directories were observed empty. Shared build/module caches were not deleted or relocated.

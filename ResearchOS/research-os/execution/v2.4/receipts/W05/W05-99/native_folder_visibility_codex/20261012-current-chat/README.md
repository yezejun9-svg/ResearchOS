# Native folder visibility candidate (component evidence only)

Candidate source: b45008a754414cd795a4be396475aab8e74b2a8c, base b806a06fb62576c18dfd1e7174c1dfd929677506.

The stable Shell initialized callback is installed for empty and suggested initial paths. It shows only the callback's own chooser HWND synchronously; if startup SW_HIDE leaves it hidden, it shows that HWND again. No timer, global window sweep, focus policy override, or deferred HWND lifetime is introduced. SetForegroundWindow is best-effort. The chooser initializes COM STA on its existing locked OS thread, balances S_OK/S_FALSE, refuses HRESULT failures before Shell UI, and retains PIDL freeing and UTF-16 lifetime.

attempt03 is the initial actual-Windows component run before the final test logging/cleanup refinement. attempt06 is the frozen-source run: 7 top-level tests, 13 subtests, no failures or skips. Two startup-hidden helper processes each open two real production choosers, with opposite initial-path order. The controller observes exact helper-owned #32770 HWNDs with usable rectangles and at least 500ms stable visibility, then posts only WM_COMMAND/IDCANCEL. It never calls ShowWindow. All 4 cancellations return empty paths and both helpers exit successfully. COM return values independently show no leaked STA reference, preserved caller STA/MTA references, and invalid UTF-16 cleanup. Foreground HWND remained another window; visibility does not imply activation.

Other frozen regressions cover strict frames, private file ACL/JSON, untrusted bootstrap, required nullable path, and user-confirmed selection authority. Those Host regressions use isolated test folders/stubs; actual GUI evidence is solely the real Shell component, not an integrated native peer or full first-use proof. Real product model/tool calls, workspace binding by the GUI component, and formal/parent acceptance deltas are zero. Root GUI/data/processes were not touched.

Fresh control.exe and runtime-verifier.exe live under the isolated C: worktree .local/builds/native-folder-visibility-20261012. Their full build information records the frozen candidate revision and vcs.modified=false. No old binary was relabelled. The original Root hidden-dialog failure is referenced and hashed without modification. The component executor does not sign acceptance. Independent review and Root's ordinary Electron first-use flow remain outstanding.

Raw invocation/stdout/stderr/result files are append-only. The evidence runner's initial PowerShell -w argument binding failure occurred before a formatter process started; bootstrap-diagnostics.json retains it alongside read-only discovery errors. No test failure was reset or erased. Build/test caches and temporary test directories are on C:, module/toolchain input remains on D:.

Reproduce with run-evidence.ps1 using a fresh attempt name, the fixed Go executable, and Arguments containing test -mod=readonly ./internal/host -run ^TestNativeFolderHiddenProcess$ -count=1 -v -timeout=150s. Requires an interactive Windows desktop; the runner sets RESEARCHOS_NATIVE_FOLDER_GUI_TEST=1. Default unattended package tests skip this opt-in native GUI test.

Primary API references:
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow
- https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shbrowseforfolderw

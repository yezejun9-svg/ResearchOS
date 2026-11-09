# SourceReadGuard v1 independent review handoff

Decision: REQUEST_CHANGES.
One finding R1: slash-form UNC/device paths bypass local-drive-only preflight and call the API factory/open before final-path rejection.
Three memory-only reproductions: //server/share/a.py, //?/C:/guard/one.py, //./C:/guard/one.py.
Required revised behavior: reject all three before factory/open (both counts0).

28 other controls pass within AST and memory-substitute scope. Exact CreateFileW argument wiring, verified buffer, partial acquire cleanup, failed-close handle retention and retry are covered.
Historical errors remain after successful retry; current closed=true/retained_handles_count=0 correctly means all tracked handles released, even if errors is nonempty.
No real WinAPI/Job/native/provider calls and no Main/canonical writes. No whole-controller READY or actual Windows cleanup claim.

Source SHA e61a1b078a40b7d8bda1116944c42e0ddd37644ad5689917a164b6c5d67d9c96/10646.
Source MF099113490f7f894f0bcdc23e3d92ce31de1e4d4cac4883ec0dbc31d24f8f0a7c/1899.
Full details: REVIEW.md; controls and defect observations: controls.json; original exact snapshots: snapshots/; commands/results: raw-review-io.json.
Original module untouched. Only this independent receipt directory written.


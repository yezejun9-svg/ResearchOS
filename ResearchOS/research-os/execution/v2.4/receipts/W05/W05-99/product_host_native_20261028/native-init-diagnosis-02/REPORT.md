# Native chooser attempt-02 read-only diagnosis

Source HEAD `5c4c94022bd9` is treated as immutable for this diagnosis. The attempt-02 CLI `init` exited 1 with `NATIVE_WORKSPACE_CHOICE_FAILED / NATIVE_INVALID_REQUEST` after validating a Unicode and space-containing workspace path. The separate controller found no visible `#32770` folder dialog owned by the witnessed Core during its 25-second window. The CLI returned in roughly three seconds, so the dialog was never confirmed.

The CLI sends exactly `NATIVE_WORKSPACE_CHOOSE_REQUEST` with `client_id`, `requested_path`, and `requested_access=READ_WRITE`. The pinned request schema allows a nonempty path string and `READ_WRITE`. `HandleNative` checks `client_id` only for nonempty; two real `host.status` calls accepted the same Unicode default client ID. `INVALID_REQUEST` is therefore not evidence of a client-ID allowlist failure. The error may arise from schema grading, the Windows chooser's COM STA initialization, immediate Shell cancellation, invalid selected folder, or reply grading. The existing CLI parses `NATIVE_ERROR.error.code` but drops `error.message`; this receipt cannot distinguish those branches.

The `first.png` screenshot was taken during launch, before CLI `init`. Its “连接中断” and `STALE_RESPONSE` display cannot be caused by the later CLI error. The same launch obtained a successful `window.researchos.v2['host.status']({})` reply. The renderer state should be observed separately without expanding this chooser repair into UI changes.

Next: use a new fresh owned profile and one direct Native3 workspace-choose frame, preserving the existing raw error response and binding the pipe server PID to the witnessed Core before and after the exchange. Do not modify the Native3 contract or production CLI before the specific error message identifies the failing stage. Preparation files are in `preparation/`; no native run was made in this diagnosis.

Source and raw evidence paths plus SHA-256 values are in `REPORT.json`.

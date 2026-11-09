# Bridge checkpoint compatibility author report

Source frozen: `0f9a870aed72785297a9999396fc8c760b296e13`; tree `fa071c9be7e39628c0b86ad43f77d5c50be63c7c`. Exact two authorized files; worktree clean; source slot released. Independent review pending; formal increment 0.

The shared Bridge now chooses legacy inline, RESEARCHOS_PAUSE_V1, or no checkpoint capability from the host's frozen request and manifest before worker frames. Ingest, acknowledgement, pause terminal and offline recovery use the same choice. V1 cannot fall back to inline checkpoints, empty pause frames or legacy acknowledgements. Mu without negotiation can still finish a normal turn, but cannot emit legacy checkpoints.

Offline recovery reads the original trusted request with the bounded no-reparse handle reader, checks its InputHash and manifest task/run/epoch, and refuses erased or mixed journal protocol. V1 checkpoint capture remains capped at 12 MiB; protocol frames at 64 KiB. Existing typed artifact/use/journal seal validation is retained.

Final evidence:

- attempt-006: 6 top-level and 47 subtests passed, zero failures/skips; includes actual directory junction rejection and mode-erasure negatives.
- attempt-002: actual pinned Node/Mu bundle, AppContainer pause/stop/drain and new-process resume passed. Checkpoint 88,701 bytes; checkpoint sequence 6, paused sequence 7; same Run epoch 1 to 2; two restored commands consumed, cumulative MODEL calls 3, no prompt replay. This uses synthetic MODEL and Core-shaped receipts.
- attempt-004: both original Core tests passed unchanged. Legacy context rebuild reports native_resume=false and two dispatches. Actual checkpoint_durable control process exited 86; next control process recovered exact checkpoint without extending lease; incomplete terminal resume remained blocked.

Failure history is append-only: attempt-003 failed setup due to sparse checkout omissions; attempt-005 failed only because creating a file symlink required unavailable Windows privilege. Required imports were materialized; the reparse negative was replaced by a real directory junction and passed. Six invocations, two historical failures, no reset.

No Main integration, package deployment, product DB change or live provider call. The frozen M1-02 implementation and schema25 files were untouched. Source manifest, attempt ledger and binary patch are attached in this directory.

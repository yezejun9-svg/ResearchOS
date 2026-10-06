# R2 actual-control correction delta — PASS_BOUNDED_CORRECTION_DELTA

Production correction: `c32e5248e4d53443147aebaeb6649ee4636adc9b`. Final source including test-only changes: `643a04f593b8b5842f09b4d92ca29a5870d0c020`. Evidence: `57f24570089b46865d4b97b648f9b86768e80731`. Both original P1 findings are closed in this bounded correction. The `actual-control-3f0e320` NEEDS_FIX report remains unchanged.

## Finding closure

**R2-CONTROL-READY-IDENTITY:** `Ready` now requires the original child/bootstrap capability and validates journal root, epoch and image. Its private READY exchange uses exact pipe peer identity and HMAC with a fresh nonce, startup token/epoch/root, and verifies child identity, held owner lease, actual listener and completed coordinator recovery. HTTP health is supplementary and the child is checked again afterward. Bootstrap's STARTING/PID-zero allowance is limited to this read-only readiness path; QUIESCE/COMMIT retain their full journal/process requirements.

**R2-CONTROL-RECOVER-AFTER-QUIESCE:** `startupComplete` is written under `scanMu` only after successful recovery. Pre-start quiesce returns BUSY without setting a fence; startup Serve checks quiesced before recovery and does not repeat startup recovery after completion. The directed check calls quiesce before Serve, checks refusal/no fence, then confirms normal recovery, quiesce and abort without stopping Serve. Direct calls to exported Recover are not claimed to be independently guarded; the reviewed production startup path is Serve.

The occupied-listener negative uses a newly created suspended actual-control executable with its original process/thread handles, a healthy unrelated HTTP endpoint, and no private READY pipe. The new readiness path rejects it while the original process handle remains alive; the old Alive-plus-HTTP logic would accept this precondition. This controlled negative does not itself represent a running service or a acquired data-root lease. The normal idle case separately covers real startup and same-root restart with held leases.

## Evidence and its limits

All 12 final source hashes and all 4 evidence-file hashes match the frozen manifest. Go and migration 0019 match. Git confirms c32e524 through 643a04f changes only `ops/supervisor/control_fixture_windows_test.go`, so c32 production-path observations apply to unchanged production code. The evidence commit contains only five receipt files; the worktree is clean.

- **c32e524: overall FAIL / exit 1 remains FAIL.** Startup/lease/abort and normal idle restart are individually PASS. An optional regex suffix unintentionally ran every actual-control subcase; six prior refusal/lost-ACK cases passed, but occupied-listener failed because the child had already exited. No cause for that premature exit was established, so this is not counted as the readiness negative passing.
- **5c3608c: overall FAIL / exit 1 remains FAIL.** The exact occupied case failed its HTTP startup prerequisite at 127.0.0.1:9540 before a child was created. It supplied no occupied-child result.
- **643a04f: only the exact occupied subcase PASS / exit 0.** The first remaining fresh-listener probe returned HTTP 200 at 127.0.0.1:56847. The original handle still identified live suspended child PID 88884, creation 1790797665102339200, image `f7b0aa9bce1f9228ec9fde33b6da625ed1fceb97adf5774cd982171dfd1d6c1d`. Absence of private READY correctly rejected the unrelated endpoint. Total prerequisite probes were 2 of the authorized cap 3; the unused probe was not run.

The c32 idle observation used two different process identities with identical actual-control image bytes (old PID 65332, new PID 38444). Project `01a7c95466ab57a78ac1f65a0af5d6e4`, revision 1 and profile digest `1a58e152c0567f0b84df354a7f8d3692551f438c6d35d06ae8edafc9e64baa99` were retained by actual HTTP GET. No final full-suite PASS is asserted.

This closes two mechanism defects only. It does not accept release_host/R1 wiring, different-release improvement, actual-control rollback, native RESUME/reconnection, SCM/LIVE/6-hour qualification, or formal W16/C20/A16. The next slice remains paused. Reviewer actions were source/raw inspection, git comparison and hash recomputation; no business/native retry or stopped S2/I2 SOURCE probe was run by the reviewer. See `review.json` and `independent-recomputation.json`.

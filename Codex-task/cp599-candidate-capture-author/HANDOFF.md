# CP599 candidate capture author handoff

Status: AUTHOR_FROZEN_PENDING_INDEPENDENT_QA. Source editing stopped after the independent-policy fixture correction and attempt-02 format/test/vet success. Worktree base stays 001f7e5a4d95152c8f83874a60d9fbd3bbace538; Root owns Main/CP600 and integration. No commit/rebase/control state/registry edit occurred.

Exactly six scoped files are pinned by attempt-02/source-manifest.json and FROZEN.json. 7a156f re-read actual D files: six matching pins and Git status exactly two modified/four new files.

Behavior:
- RuntimeToolRequest has an unexported concrete capture pointer; no producer, exported setter, JSON input, policy marker or worker opt-in exists. CodingCapture distinguishes nil from invalid nonnil, returns copied scalar-only provenance, and retains full positive int64 epoch as decimal text.
- Ordinary nil requests retain the old sandbox.Run call. A valid private request uses Start(ctx), BeforeResume, then Wait(context.Background()), preserving complete-wait ownership. beforeLaunch=false precedes Start; callback/launch/Wait errors remain UNKNOWN at the existing broker boundary.
- BeforeResume receives actual staging identity. Held ancestor handles, relative NtCreateFile with OBJ_DONT_REPARSE/FILE_OPEN_REPARSE_POINT, Windows handle attrs, one-link regular files, and bounded exact names supplement containment. Only go.mod, pkg/solution.go, pkg/solution_test.go are allowed in source; stage/input only locate fixed namespaces, not final toolchain attestation. Vendor opt-in is rejected.
- Current check-time sourceManifest B after editing is the comparison baseline, not prepare-time editable candidate A. Candidate is read once, <=16KiB, parsed by existing deliverygate, and retained as an owned structural snapshot. Fixed files are streamed/hash-checked with 1MiB-per-file bounds and never serialized as source.
- A usable evidence object requires the matching five receipt identity fields, derived cwd/executable/full argv, empty capabilities, stopped/drained/cleanup/output-copy flags. Nonzero/timeout is preserved as execution outcome, never business PASS.
- Only candidate_capture is added to host_evidence before existing 4MiB encoded bound. It is not model metadata or an SDK/reportRun output. Existing broker/fact projection remains the sealing route. SDK len1, ordinary planning/session.send and Goal LIVE503 were not changed.

Validation:
- Locked Go1.27.1 executable, GOENV=off/GOTOOLCHAIN=local/GOPROXY=off/GOSUMDB=off, offline existing module cache, isolated C profile/cache. Exact environment and commands retained in each attempt.
- attempt-01: gofmt0, actual test exit1 (9 top+83 sub pass, 1 top+1 sub fail), vet NOT_RUN. Policy negative fixture used the changing context hash as its expected hash. Original snapshot, commands and logs are intact.
- Only fixture policy baseline was corrected. attempt-02: gofmt0/test0/vet0, 10 top+84 sub=94 pass events, zero fails/skips, two additional package PASS. No sandbox Start/Run, process launcher, native backend, model, probe, server, or DB was called by these selected fixtures.
- Fresh directories cover A/editB/stageB/finalB, B->C drift, fixed-file change, extra/missing/emptydir/vendor/case entries, hardlinks, real temporary directory reparse junctions at four levels, invalid AST/UTF8/size, context/check/policy/toolchain/manifest identity mismatch, cancellation, defensive evidence, five native identity plus paths/argv/cleanup negatives and encoded evidence budget. All native identities/receipts in fixtures are explicitly synthetic.
- These are author checks, not independent acceptance. resource_controller_review must independently review/test these exact pins.

Limitations remain explicit: capture is in memory during BeforeResume and persisted in full evidence only after the complete receipt; it does not prove later compiler reads, final toolchain/vendor copies, same-OS-user exclusion, current native qualification, original business approval/origin, trusted factory or semantic business correctness. Existing child-retained-pipe cleanup risk is a separate sandbox activation blocker; no real activation occurs here. Formal increment remains0/42. Historical CP586 Cstate/attempt04 vet UNKNOWN and all old failures/counters are untouched.

Diagnostics are complete in diagnostics.json. The first source-write wrapper failed on PowerShell automatic $Host before any source write, with readback proving absence before corrected execution. Two new-source newline joins were corrected by readback before Go. Memory draft loss was recorded rather than claimed recovered. No uncertain action is pending.

Next: independent six-pin QA, then Root alone integrates or requests a scoped correction. Do not broaden into producers, schema/API/Goal gates or actual native/model validation.


# Minimal Host prelaunch-intent source contract

Decision: exact THREE files are required. Design only; Root must register a new source lease. No edit, test, Native/model execution or integration is authorized here.

1. adapters/runtime/codex_qualification_windows.go
2. adapters/runtime/codex_qualification_capture_windows.go
3. adapters/runtime/codex_qualification_capture_windows_test.go

An exact-two-file capture-only implementation cannot bind all required origins: collectQualification currently receives executable/argv/env/cwd/jobName/receiptBase, but not TaskID, original source-binding hash, HostBuildHash or HostBoot. Do not guess these from filenames or job names. Existing qualificationReceiptContext already contains all provenance: TaskID/RunID/Epoch/SourceBindingHash, S/QW/D, NativeHash/HelperHash/HostBuildHash/TemplateHash/EnvironmentHash/NormalHome/HostBoot, ordered RenderedArgv+hash, PlanEncoded+hash, Nonce and LoopbackPort. The wrapper's sole production call must pass that existing private typed context by value. No exported options, shared codex.go interface or public rev2 DTO needs change.

## Ordering and durable record

In collectQualification, validate/copy the supplied context and capture arguments; create pipes and the original qualification Job through existing code. After qualificationJob has Set+Query verified that same Job's limits, and BEFORE calling launch (therefore before CreateProcess or Resume), create one fixed record adjacent to the existing capture receipt, for example receiptBase + .prelaunch.json. Keep existing private receipt directory, original run/epoch-derived base and no external path input. Treat any pre-existing record as consumed/uncertain; do not overwrite, truncate, rename away or retry it.

Record a distinct bounded internal schema such as researchos.native-qualification-prelaunch.v1, phase PREPARED_INTENT_ONLY, with copied context and actual executable/cwd/job-name binding, queried active-process/job-memory/flag values. Return the SHA256 of the exact serialized intent bytes for final-capture linkage; do not attempt a self-referential digest field inside those same bytes. Include dynamic Host nonce/owned-loopback port, ordered argv/hash and encoded fixed-seven-case plan/hash. Validate nonempty canonical origins/epoch, expected hash formats, valid fixed plan, equality between plan roots/nonce/port and copied context, ordered argv equality/hash, environment HASH only, and correspondence to the original collector arguments. The qualified wrapper remains the sole production origin. Do not add a receipt loader or let JSON/context supplied by external callers authorize READY.

No prompt, auth bytes, credentials, raw private configuration or raw environment values belong in this record. NormalHome, if retained, is path metadata only. Template/hash/build fields describe pinned inputs; PREPARED is never evidence of enforcement or a model permit. No PID or creation timestamp is fabricated before a process exists.

Use O_WRONLY|O_CREATE|O_EXCL, mode0600 under the already private verified directory, a finite encoded-size ceiling, complete-write check, Sync and Close. Launch is allowed only after all succeed and context remains live. File-open, serialization, size, short-write, Sync, Close or readback-identity uncertainty must close pipes/Job and return without calling launch. Preserve any partial artifact for inspection; never remove it to retry. No fallback stream, path, less strict ACL or launch after an I/O error.

Bind final capture to the exact intent path and bytes SHA256 via private qualificationCapture fields carried into persistQualificationCapture. Keep final receipt O_EXCL separate from intent. A final receipt may have actual PID/creation/Job and stop/drain evidence; it must not replace or reinterpret PREPARED as PASS. Avoid any new RPC/public DTO field. Query/readback proves configured limits on that owned Job, not measured memory use or general resource adequacy.

Preserve q's one-shot state, failed-Ensure consumption, delegateAttempted boundary, residual preparation deadline, current scope/policy/driver fences and all capture cleanup. A failure before launch may conservatively project UNKNOWN if the current private no-child proof cannot establish it; do not fabricate zero-PID completion or relax model identity rules to improve the status. If adding a precise private launch-attempt fact, it must be set immediately before launch and remain false on every prelaunch I/O failure; that extension requires explicit review within this lease.

## Focused evidence required before integration

- Pure record round-trip confirms exact source/template/native/helper/build/boot/origins, nonce/port/plan and ordered argv/hash; mutation or missing required provenance rejects.
- Existing file, over-budget payload, short write, Sync failure and Close failure each prove zero launch-callback calls. Partial/existing bytes remain unchanged/preserved; no second attempt or overwrite.
- Ordering fixture proves same Job limits query completes, then successful full write+Sync+Close, then launch. Cancellation between stages forbids launch.
- Final capture links the original intent digest; altered/final-only receipt cannot mint observation or permission. No caller-provided receipt acceptance is introduced.
- Adapt existing owned fake-child collector tests for the private typed context. They may use the test binary and private Go seams only; do not add public fake-provider options, environment switches or product JSON flags.
- Root runs controlled Go fixtures/compile with exact source hashes and existing Job supervisor. No actual Native/model test belongs to this source lease. Tests should prove zero-launch on failure using a narrow private spy/fake instead of intentionally launching Native.

Current evidence references: B3rev4 windows source SHA3c859dfd26d5f32e01c0868285283a7395b57e4947e0cadcf6d159bb48790103 has receipt population at lines675-692 and call at694. Capture source SHAa857de058251fa1f3c693c665dd4f935704b30c9d25f56cf7ceb6256916cddcb has queried Job setup followed directly by launch at about213-216; context type begins350 and final O_EXCL persistence begins387. Final line numbers should be regenerated against the new freeze.

Source3 build binding proceeds independently in its own exact scope. Final actual controller must bind a build containing this reviewed intent fix; a previously built Core without it cannot satisfy the prelaunch-receipt gate.

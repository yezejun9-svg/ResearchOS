# B3 rev2 independent security review

Decision: **BLOCKED**. All eight files were inspected and hash-bound to the exact lease paths. Manifest SHA256: `37dcac943c5a8fe694f24d152b4a34fbaf46914d25b0a4942f2aa74a54e5d503`.

## B3-F1: unused-strconv-import

adapters/runtime/codex_qualification_windows.go:18

strconv is imported and has no reference anywhere in this file. This Windows source cannot compile.

Minimal correction: Remove the unused import in a new frozen revision; preserve rev2. Root-owned compile evidence remains separate.

## B3-F2: stream-io-error-not-sticky

adapters/runtime/codex_qualification_capture_windows.go:97-109,220-233,277-294,338-354

Final partial-file Sync/Close errors remain only in qualificationStream.err. CleanupComplete checks out.Err but not either stream.err; qualificationCaptureReason also ignores them. A fully received valid transcript with drained=true and a final persistence error can therefore qualify once the child has exited with code0 and JobZero. Even the branch that kills on stream.err does not make the error sticky.

Minimal correction: Fold all stdout/stderr errors into terminal capture failure regardless of arrival phase; prohibit complete hashes/qualification on failed durable persistence. Add injected EOF-final-Sync/Close and post-root-exit stream-error cases.

## B3-F3: terminal-evidence-omitted

adapters/runtime/codex_qualification_capture_windows.go:302-317; adapters/runtime/codex_qualification_windows.go:434,530-542,612

The paired StdoutPrefix/StderrPrefix fields share json:"stdout_prefix" and paired hashes share json:"stdout_hash". encoding/json treats the competing fields as ambiguous and omits them. More broadly, the terminal record contains capture status only: actual plan/nonce/IPv4 tuple, rendered argv or digest, originating Task/Run/epoch/source/native/helper/template/build bindings, evaluated cases, Host controls and queried Job-limit evidence are not persisted. The live obs hash is not an independently reviewable run receipt.

Minimal correction: Give each field a distinct explicit JSON tag. Persist a bounded Host-owned preparation/terminal record binding actual plan and identity, the ordered argv/projection hash, baselines/controls/case outcomes, precise diagnostic errors and requested/queried limits before admission. Do not make this record importable as authority. Assert serialized keys and bindings, not only exclusive-file behavior.

## B3-F4: external-io-bounds-and-drain

adapters/runtime/codex_qualification_capture_windows.go:53-83,277-295; adapters/runtime/codex_qualification_windows.go:358-361

Stream ingestion always reads an 8192-byte buffer before checking the 1MiB cap, so bytes beyond the hard ingestion budget are consumed/discarded. The listener uses ReadString with a 128-byte buffer, which does not impose a 128-byte line limit. On stream-drain timeout, the collector sets local readiness booleans and returns without closing and joining outstanding readers, permitting capture writes after terminal return.

Minimal correction: Clamp read slices to remaining capacity and fail closed at the ceiling; bound the listener line with a limited read and explicit oversize classification. On timeout close owned read handles and collect/join worker termination under the cleanup budget before publishing terminal state. Preserve partial diagnostics and never claim drained on uncertainty.

## B3-F5: controls-and-violation-precedence

adapters/runtime/codex_qualification_windows.go:489-511,542-610

Read and existing-file write controls are implemented, but exact fixed CREATE_NEW targets have only absence checks, with no matched Host create-positive pre/post controls. A target-specific denial is not distinguished from the requested sandbox effect. Also the mutable reason string can overwrite a proven forbidden success with later CONTROL_INVALID/INCOMPLETE/IDENTITY_CHANGED; map iteration over case results makes final classification order-dependent. These paths remain closed, but lose the required violation evidence and finite-probe attribution.

Minimal correction: Add bounded Host create controls for the exact synthetic targets, restoring absence before the child and only after first preserving any forbidden-create evidence during post-audit. Keep an immutable list/bitmap of observed violations and errors; choose deterministic precedence without erasing a forbidden success. Add actual Host-control/evaluator negative fixtures, including wrong errno, changed bytes, failed controls and simultaneous violation+incomplete cases.

## B3-F6: ancestor-no-reparse-not-enforced

adapters/runtime/codex_qualification_windows.go:289-294,438-439,481-482,572-573

exactReal compares EvalSymlinks output with the supplied spelling. It does not inspect FILE_ATTRIBUTE_REPARSE_POINT for every ancestor and leaf; reparse kinds that do not produce a changed resolved spelling are not explicitly refused. This does not implement the contract's ancestor no-reparse invariant for S/QW/D/helper.

Minimal correction: Before qualification, inspect each authorized ancestor and relevant leaf with a narrow Windows attributes/handle check and reject every reparse tag, then perform canonical equality and record identities. Recheck the fixed fixture paths before accepting post-audit. No traversal of unrelated user directories is needed.

## B3-F7: pre-native-launch-validation-gap

adapters/runtime/codex_qualification_windows.go:168-197

Wrapper Start performs only partial Launch checks before ensureLaunch can start Native. Canonical positive epoch, prompt nonblank/maximum length, and required callbacks are not checked until delegated B1.Start. Invalid trusted-Go input can consume a Native qualification and mutate fixtures before B1 rejects it. The independent wrapper reviewer reported this same issue; this report inspected the partial validation and cross-references that finding without recounting it.

Minimal correction: Mirror or reuse B1's pure full launch preflight before state consumption/preparation/Native spawn, without editing B1-owned files in this lease. Add invalid-launch cases proving no qualification and no RPC creation. Coordinate exact origin with the supplemental reviewer.

## Boundaries

Fixed helper syscall shape, B1-derived sandbox argv, independent QW/D siblings, one-use private observation and actual Job Set/Query limits are present. These positives do not override the capture/persistence and control defects.

This is a source-only review, not a test or probe run. Go PASS cannot establish Native permission qualification. Root's separate fake-process tests, source fixes, Host/helper identity integration, B1/B2 fences and a separately authorized synthetic runtime scope remain necessary. No source edits, Native/model/probe execution or D writes were performed. Formal/product increment 0. Earlier candidate and reports are preserved.


# Independent single-task04 SECURITY delta review

**APPROVED_SOURCE_FIXTURE_ONLY.** Source blockers: none within the reviewed delta. Formal/product increments: 0. This is not run-readiness or business acceptance.

The frozen runner is `e14f9d287398b432f6e3a55918fb73be747b8b446d1e7f032ddfdfd925627a5b`; helper `a1680c3e1c1960ceb7969c19e7e5bd2903af170d497ede0e18e32b6315c68f89`. REVIEW.json/sourceSHAmap.json contain the full pins and stable diagnostic origin keys.

Independent exact comparisons established:

- Removing only the new `requireWarningDismissSelector` function, its call, and the selector-evidence file pin reproduces the approved03 runner byte for byte. F1/F2/F3 identity binding, one DOM submit, capability/payment guard, UNKNOWN recovery, deadlines and normal close are inherited unchanged. Old suites were not rerun.
- Replacing only Native05's global-zero guard with the approved03 explicit Native-stage-zero/global-one guard reproduces the04 helper byte for byte. No extra native control relaxation exists in this merge. The task-stage budget guard itself is byte-identical to approved03.
- The template changes only by adding the warning dismissal selector. It remains inert and lacks a successful prior-result pair, execution hashes and Root approval pins.

Fourteen independently constructed negative selector cases rejected changed control ID/type, count/type, evidence basis, return-ID interpretation, event name, sequence/type, hash/path, and missing selector. The valid template passed. Only the isolated source function was evaluated; the candidate was not imported.

The actual03 public helper receipt matches SHA `392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423`. Its unique `WARNING_IDOK_CHILD_METADATA` event at sequence36 records one Button: control_id2, visible/enabled, positive HWND, owned child with matching parent/root dialog, no enumeration error/truncation. The receipt exit is2. It supports the chosen selector and does not prove a successful Native flow or workspace authorization. MessageBox's return IDOK1 is not used as the child-control selector.

Both Node and helper pin the actual receipt before acting. The helper retains owned warning caption/body checks, unique all-Button selection, positive/direct-lookup identity checks, a fresh repeated selector check immediately before queueing, exact dialog-thread active/focus validation and final deadline check. Chooser ID1 confirmation and chooser ID2 cancellation remain separate branches. Native05's full safety review remains separately bound; this review covers the task merge and selector gate.

Node syntax exited0; PowerShell AST had zero errors; all11 frozen member hashes matched. No app/GUI/model/CLI probe, runner/helper entrypoint, SDK import, Win32 call, account/auth-file read or D read/write occurred. Candidate files were not modified; review artifacts are C-only.

Root subsequently reported successful actualNativeflow04, normal close and original Job zero accounting, plus a post-flow build07 readback of134 hashes/no extras. Those are Root-provided runtime reports, not results of this review. Runtime prerequisites in REVIEW.json require binding the separate Native source/actual reviews, successful runner and exact original Job receipts, post-flow integrity, and a fresh approved scope/Job launch contract including the selector evidence. The successful report supersedes the frozen README's earlier blocked-runtime description only at the Root runtime-evidence layer; it does not convert the template into an executable scope.

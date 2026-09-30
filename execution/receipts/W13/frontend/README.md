# W13 frontend development evidence

Scope: `DEVELOPMENT_ONLY_BROWSER`, `EXECUTION_REPORTED`; independent acceptance pending.

Recorded evidence is split by changed behavior instead of repeatedly running the previously passed matrix:

- Core: `5a0d5f262e5b4e4a9f511a1786564330/report.json`, 20 named browser scenarios and 108 screen/theme/viewport cases.
- Native browser: `81f8a13a059a4d46bac844b1fd0b8f7e/report.json`, 4 named checks (2 setup checks, actual 200% browser zoom, native PDF rendering). This supersedes the cropped full-page screenshot in `8c7cd39df55c4fb2b803c13c6e542b8f`.
- Populated workflow: `2b1f7326c1374823b2ad6dc2a4380911/report.json`, 6 named checks (2 setup checks and 4 workflow checks) and 12 populated-release screen/theme/viewport cases. Earlier `1f5ae64ed8c54e18b583fcf5fec820b6` covered release switching/notifications but not replay; `60e2e05a1b4a47328713897967f00a69` and `fbf69ec964564839b7bacc6b23e1b9dc` passed the added replay/plan checks but used full-page mobile captures.

The runner launches a real Go HTTP service with temporary SQLite and real Chromium. All persisted Project/Goal/Task/Run, candidate artifacts, ChangeProposal, independent fixture verification, profile update, 403/412, releases, notifications and cycle close use service contracts. SSE transport faults are explicitly injected by Playwright over saved service events. Runtime process observations use an explicit FIXTURE helper; they are not actual OS cancellation evidence, live provider qualification, or physical-device acceptance.

## Verified behavior

- Core matrix covers nine secondary screen entries in light/dark at 320, 390, 768, 1024, 1440 and 1920 CSS pixels. Main workbench covers six viewports, mobile dark, keyboard, reduced motion and drawer focus restoration. The populated Release has its own 12-case matrix. Empty entries do not prove all populated screens.
- Native Chromium zoom preference 2.0 is measured as outerWidth 1440, innerWidth 720, DPR 2 and visualViewport scale 1 across ten project screens. Every visible control stays inside viewport bounds; navigation/Escape restores focus and the draft remains editable. The viewport screenshot includes the complete right side and all four bottom navigation controls. The earlier 640px viewport is not zoom evidence.
- Seven media formats use sealed content and controlled rendering/download. HTML scripts/network are blocked; Markdown is escaped; >5 MiB falls back to hash-verified download. An in-flight preview switch rejects late bytes. Native PDF viewer renders the real one-page document and its page controls; HTML remains sandboxed. Downloads verify bytes in memory; this is not a streaming gigabyte viewer.
- Owner sealing actually returns 403 and retained draft export works. A PLANNER+EXECUTOR fixture edits a frozen ProjectProfile.intent baseline; separate VERIFIER and SCHEDULER apply a concurrent update. Real 412 preserves local/external content. Explicit merge seals three JSON candidates and a new pending ChangeProposal without UI self-acceptance or background overwrite.
- Missing-X cycle closes PARTIAL with a local checkpoint artifact; dashboard/detail show its gap after active_cycle_id clears. This is display evidence rather than complete W08 source qualification.
- Task keyboard tabs, real UI pause/resume (BLOCKED/READY), cancellation waiting (CANCEL_REQUESTED) and fixture acknowledgment (CANCELLED) pass. A reported result remains EXECUTION_REPORTED until a different principal requests independent service checks; ACCEPTED appears only after the service receipt. The summary shows Run.execution_report.
- Two independently checked milestone releases switch 2 -> 1 -> 2 with exact distinct sealed hashes and JSON. Two actual notifications render once each; marking read persists. Replaying saved events twice each makes no write requests and preserves notification IDs/unread count. Real plan mutation updates planned count 0 -> 3, revision 1 -> 4, stage counts and the server reason.
- Core SSE cases cover duplicate/foreign project frames, gap cancellation/release, 410 snapshot reset, real browser offline/online and project switch. Native OS sleep is not covered.

## Remaining acceptance boundaries

- C23 PARTIAL: full Task/Run state matrix (including transient VERIFYING/reconciliation states), populated Experiment/EvaluationSummary and Qualification/Knowledge/Resources flows are not fully covered. Basic schema field bindings were corrected and production build passes, but are not represented as complete browser acceptance.
- C24 PARTIAL: responsive/browser zoom evidence is complete only for the listed screens and states. Actual physical phone accessibility/integration remains with W17/A10/A11.
- C25 PARTIAL: restricted VERIFIER_ONLY integration remains unverified. Seven formats, actual native PDF, 412 draft recovery, exact release-version switching and late-preview isolation have recorded coverage.
- C26 PARTIAL: real OS sleep/resume and the remaining task lifecycle transitions are not certified. Duplicate/gap/410, project switch, browser offline recovery, planned mutation and populated milestone-notification replay have recorded coverage.
- W17 protected-device pairing/revocation and physical phone acceptance are outside this fixture. Temporary service limitations are rendered honestly.

One workflow rerun `6a07c389c24c43fba968110c381310a9` failed with `Remote end closed connection without response` after cancellation passed. It is retained as a failed run, not reclassified as PASS. The runner now preserves service logs and method/path for future failures.

## Reproduction

From repository root with `RESEARCHOS_TASK_ID=W13`, run `python ops/ci/ui.py`. Optional `RESEARCHOS_UI_PHASE` is `core` (default), `native`, or `workflow`; `RESEARCHOS_GO` overrides the recorded pinned Go path. Python Playwright and installed Chromium are required. Reports record actual browser version, HEAD, project identity, source hashes and screenshot hashes. No fixture bearer credentials are included in evidence.

Earlier receipt directories remain development history. PASS labels apply only to each run's listed checks and exact source hashes; they are not complete C23-C26 acceptance. Counts are named scenarios and matrix cases, not fabricated contract assertion totals.

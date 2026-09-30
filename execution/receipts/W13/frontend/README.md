# W13 frontend development evidence

Latest recorded run: `5a0d5f262e5b4e4a9f511a1786564330/report.json`.
Scope: `DEVELOPMENT_ONLY_BROWSER`, `EXECUTION_REPORTED`; independent acceptance pending.

The runner launches a real Go HTTP service with a temporary SQLite database and real Chromium. Project/Goal creation, candidate sealing, ChangeProposal, independent fixture verification, applying the external profile update, 403/412, and cycle close use service contracts. SSE duplicate/foreign/gap/410 faults are explicitly injected by Playwright; subsequent snapshots and resumed stream use the real server. It does not assert live provider qualification or physical-device acceptance.

- 20 named browser scenarios and 108 screen/theme/viewport matrix cases passed; count is reported separately, not converted into a fabricated number of contract assertions.
- Matrix covers the nine secondary entry screens in light/dark at 320, 390, 768, 1024, 1440, 1920 CSS pixels. Main workbench has the six viewports, mobile dark, keyboard and reduced-motion checks. Empty task/release/experiment selection entry screens do not prove their populated workflows.
- Seven media formats check sealed content and controlled rendering/download bindings. HTML script and network are blocked; Markdown is escaped; >5 MiB falls back to controlled download. An in-flight preview switch rejects late content. PDF iframe and downloaded bytes pass, but actual PDF document rendering remains unverified (separate PDF probe was blank).
- A normal Owner is actually denied sealing (403) and exports the retained draft. A separately provisioned PLANNER+EXECUTOR fixture edits a frozen ProjectProfile.intent baseline; a different VERIFIER and SCHEDULER apply the concurrent external change. A real 412 preserves both sides. Explicit merge persists local, external and merged JSON artifacts plus a new ChangeProposal; no UI self-acceptance or applied background overwrite occurs.
- Missing-X cycle closes PARTIAL with a genuine local checkpoint artifact, and dashboard/detail show the gap after active_cycle_id clears. This is display evidence, not the full W08 source adapter qualification.
- SSE event duplication, foreign project frame, gap reader cancellation/release, 410 snapshot reset, actual browser offline/online and project switch pass. Watermarks and reader counters are in the report. Populated milestone-notification replay and OS sleep remain outstanding.

## Remaining acceptance boundaries

C23 PARTIAL: populated Task/Run transitions, release/evaluation workflows and complete state matrix still require more browser cases.
C24 PARTIAL: actual browser 200% zoom and real device evidence are not replaced by the additional 640px viewport. The old report wording "200% equivalent" must not be used as zoom evidence.
C25 PARTIAL: native PDF pixels, restricted VERIFIER_ONLY integration, and complete release-version switching remain outstanding. Download verifies bytes in memory; backend upload cap limits this path, and this is not a streaming gigabyte viewer.
C26 PARTIAL: populated notification uniqueness, planned-state mutation/replay, and OS sleep are not yet certified by these UI cases.
W17/A10/A11 physical phone and protected-device integration are out of this fixture's coverage.

Run from repository root with `RESEARCHOS_TASK_ID=W13`: `python ops/ci/ui.py`. Use `RESEARCHOS_GO` to override the recorded pinned Go executable path. Python Playwright and its installed Chromium are required. The report records the actual browser version, HEAD, project identity, commands, source hashes and screenshot hashes. Never print fixture bearer credentials into evidence.

Older receipt directories are preserved development history; their PASS labels apply only to the listed checks at their exact recorded source hashes, not to complete C23-C26 acceptance.

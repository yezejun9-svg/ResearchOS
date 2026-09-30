# W13 frontend development evidence

Scope: `DEVELOPMENT_ONLY_BROWSER`, `EXECUTION_REPORTED`; independent acceptance pending.

Recorded evidence is split by changed behavior instead of repeatedly running the previously passed matrix:

- Core: `5a0d5f262e5b4e4a9f511a1786564330/report.json`, 20 named browser scenarios and 108 screen/theme/viewport cases.
- Native browser: `81f8a13a059a4d46bac844b1fd0b8f7e/report.json`, 4 named checks (2 setup checks, actual 200% browser zoom, native PDF rendering). This supersedes the cropped full-page screenshot in `8c7cd39df55c4fb2b803c13c6e542b8f`.
- Populated workflow: `2b1f7326c1374823b2ad6dc2a4380911/report.json`, 6 named checks (2 setup checks and 4 workflow checks) and 12 populated-release screen/theme/viewport cases. Earlier `1f5ae64ed8c54e18b583fcf5fec820b6` covered release switching/notifications but not replay; `60e2e05a1b4a47328713897967f00a69` and `fbf69ec964564839b7bacc6b23e1b9dc` passed the added replay/plan checks but used full-page mobile captures.

- Contracts: `26c8cc1c78cb431f9cda632e8a3b2b52/report.json`, 6 named checks (2 setup and 4 contract scenarios), 6 screenshots. This records stable-source C17/C18/C23/C26 behavior and supersedes the earlier transition-frame C18 mobile capture.
- Populated content: `88c7be0324ee4191b0459452e33fde11/report.json`, 7 named checks (2 setup and 5 content scenarios), 36 screen/theme/viewport cases, 13 screenshots. Strict/unlimited/estimated budget policies all persist through real HTTP, including correct enforcement and unknown-cost actions. The success notification close control is at least 44px.

The runner launches a real Go HTTP service with temporary SQLite and real Chromium. All persisted Project/Goal/Task/Run, candidate artifacts, ChangeProposal, independent fixture verification, profile update, 403/412, releases, notifications and cycle close use service contracts. SSE transport faults are explicitly injected by Playwright over saved service events. Runtime process observations use an explicit FIXTURE helper; they are not actual OS cancellation evidence, live provider qualification, or physical-device acceptance.

## Verified behavior

- Core matrix covers nine secondary screen entries in light/dark at 320, 390, 768, 1024, 1440 and 1920 CSS pixels. Main workbench covers six viewports, mobile dark, keyboard, reduced motion and drawer focus restoration. The populated Release has its own 12-case matrix. Populated experiment/knowledge/resources add 36 separate cases; empty entries alone do not prove populated screens.
- Native Chromium zoom preference 2.0 is measured as outerWidth 1440, innerWidth 720, DPR 2 and visualViewport scale 1 across ten project screens. Every visible control stays inside viewport bounds; navigation/Escape restores focus and the draft remains editable. The viewport screenshot includes the complete right side and all four bottom navigation controls. The earlier 640px viewport is not zoom evidence.
- Seven media formats use sealed content and controlled rendering/download. HTML scripts/network are blocked; Markdown is escaped; >5 MiB falls back to hash-verified download. An in-flight preview switch rejects late bytes. Native PDF viewer renders the real one-page document and its page controls; HTML remains sandboxed. Downloads verify bytes in memory; this is not a streaming gigabyte viewer.
- Owner sealing actually returns 403 and retained draft export works. A PLANNER+EXECUTOR fixture edits a frozen ProjectProfile.intent baseline; separate VERIFIER and SCHEDULER apply a concurrent update. Real 412 preserves local/external content. Explicit merge seals three JSON candidates and a new pending ChangeProposal without UI self-acceptance or background overwrite.
- Missing-X cycle closes PARTIAL with a local checkpoint artifact; dashboard/detail show its gap after active_cycle_id clears. This is display evidence rather than complete W08 source qualification.
- Task keyboard tabs, real UI pause/resume (BLOCKED/READY), cancellation waiting (CANCEL_REQUESTED) and fixture acknowledgment (CANCELLED) pass. A reported result remains EXECUTION_REPORTED until a different principal requests independent service checks; ACCEPTED appears only after the service receipt. The summary shows Run.execution_report.
- Two independently checked milestone releases switch 2 -> 1 -> 2 with exact distinct sealed hashes and JSON. Two actual notifications render once each; marking read persists. Replaying saved events twice each makes no write requests and preserves notification IDs/unread count. Real plan mutation updates planned count 0 -> 3, revision 1 -> 4, stage counts and the server reason.
- Core SSE cases cover duplicate/foreign project frames, gap cancellation/release, 410 snapshot reset, real browser offline/online and project switch. Browser lifecycle freeze/active is additionally covered by the contracts run; physical OS sleep is not covered.

## Contract execution map

These are development execution results for independent review, not self-issued acceptance.

| Contract | Recorded UI execution | Remaining integration boundary |
| --- | --- | --- |
| C17 | `26c8cc1c78cb431f9cda632e8a3b2b52`: release created while offline; saved events replayed five times plus reversed old events; one logical notification, idempotent read and exact release/hash/acceptance deep link | Combine with backend outbox transaction/worker-crash domain evidence; mobile viewport is not a physical phone |
| C18 | Same contracts run: four real independent receipts / six planned / two VERIFYING -> four / nine / three READY; stale projection cannot roll back counts, revision, watermark or reason | Transient VERIFYING seeded only for schema-valid temporary fixture; revisions follow actual per-task server increments |
| C23-01/02 | Core route inventory; workflow pause/resume/cancel acknowledgment and independent acceptance; contracts run covers all 11 Task / 9 Run states; content run covers populated evaluation, evidence, knowledge, costs and policy mutations | Populated Skill/Experiment result/ledger/ResourceRequest payloads are explicit schema-validated UI fixtures; actual promotion/provider billing belongs to W14/provider acceptance |
| C23-03/04 | Core empty/partial-source/offline/project isolation; contracts pending loading and 403/404/429/503/500/412 recovery; workbench goal/stage/blockers/latest accepted release/next step | Independent visual/product review remains pending |
| C24-01/02/03/04 | Core 108 entry/theme/viewport cases and token contrast; native actual 200% zoom; workflow 12 populated release cases; content 36 populated experiment/knowledge/resources cases; keyboard tabs/navigation/drawers/search/budget, focus restoration, 44px controls and reduced motion | Automated accessible names/focus tests do not certify a physical screen-reader or phone session |
| C25-01/02/03/04 | Seven sealed formats, real native PDF, exact revision/hash labels, escaped Markdown and sandboxed/network-blocked HTML; real 403/412 and merge candidates; late-preview isolation; damaged image downloads original bytes; real HTTP denies restricted metadata/content and traversal; STALE stays visible and mismatched frozen ref blocks bytes | Restricted record uses metadata-only classification fixture without formal protected bytes; W17 must establish actual protected storage/device boundary |
| C26-01/02/03/04 | Core duplicates/gaps/410/Last-Event-ID/project switch/offline timestamp; contracts old-projection rejection, server counts and plan reason, five-copy notification replay with no writes, actual Chromium lifecycle frozen -> active to new server watermark | Browser lifecycle suspension is recorded; physical OS sleep/resume remains a machine integration check |

The fixture helper requires a temporary data directory named `researchos-w13-ui-*`. Classification fixtures use unbound storage keys; they cannot manufacture protected bytes or independent acceptance. No frozen specification file is changed and no W13 status is promoted to DONE by this evidence.

One workflow rerun `6a07c389c24c43fba968110c381310a9` failed with `Remote end closed connection without response` after cancellation passed. It is retained as a failed run, not reclassified as PASS. The runner now preserves service logs and method/path for future failures.

## Reproduction

From repository root with `RESEARCHOS_TASK_ID=W13`, run `python ops/ci/ui.py`. Optional `RESEARCHOS_UI_PHASE` is `core` (default), `native`, `workflow`, `plan`, `contracts`, or `content`; `RESEARCHOS_GO` overrides the recorded pinned Go path. Python Playwright and installed Chromium are required. Reports record actual browser version, HEAD, project identity, source hashes and screenshot hashes. New runs reject any source-hash change between start and finish. No fixture bearer credentials are included in evidence.

Earlier receipt directories remain development history. PASS labels apply only to each run's listed checks and exact source hashes; they are not complete C23-C26 acceptance. Counts are named scenarios and matrix cases, not fabricated contract assertion totals.

## C18 follow-up

`ca989432a86244e1b134f10937304062/report.json` passes the exact 4 accepted / 6 planned / 2 VERIFYING -> 4 accepted / 9 planned / 3 READY scenario. Four independent server acceptance receipts are recorded; only the transient EXECUTION_REPORTED -> VERIFYING status is seeded by a schema-validated temporary-fixture helper, matching the existing domain test approach. Plan revisions are server generated per task creation rather than relabelled 1/2. Complete projections are retained; the mobile transition-frame screenshot is superseded by the settled drawer screenshot in the contracts run. `a41671f9372e46eaad806db27f02a461` reproduced stale-projection rollback; the passing run verifies monotonic entity revision, plan revision and event watermark protection in useQueries.

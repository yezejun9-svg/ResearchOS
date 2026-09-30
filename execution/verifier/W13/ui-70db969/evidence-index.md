# W13 independent UI review — frozen 70db969

Latest reviewed fix `a366288`: **PASS_IN_UI_FIXTURE_SCOPE**, all three reproduced P2 findings closed by independent regression. `baseline-review.json` preserves the original `70db969` NEEDS_FIXES verdict; `review.json` is the current bounded conclusion. No W13 stage or formal acceptance signed.

## Fix-source independent review

Create `.local/worktrees/w13-ui-review-a366288` at `a366288`, build it, and set `REVIEW_SOURCE=D:/作品集/ResearchOS/research-os/.local/worktrees/w13-ui-review-a366288` and `REVIEW_OUTPUT_PREFIX=fix-a366288` before calling `run.py`. The reviewer ran `regression`, `core`, `content`, and `contracts`. The contracts wrapper additionally runs the independently authored `verify_chain.py` sidebar-to-release/hash/full-acceptance check. `finalize_review.py` checks completed reports and screenshot hashes before assembling the current conclusion and `evidence-index.json`.

| Fixed-source scope | Report | Result |
| --- | --- | --- |
| Reviewer counterexample regressions | `fix-a366288/regression/6546e301acae43208b590794f344763e/report.json` | PASS: URL list/search/reload/history; typography; 320x780 drawer; actual 30.234s timeout and retry |
| Core + native 200% / PDF | `fix-a366288/core/8e3f4ce9e93248f0a122e15a6f09ea2d/report.json` | PASS: 22 named scenarios/checks, 108 matrix cases |
| Populated content | `fix-a366288/content/f1da1fbc2d044611985ee12a77dd13ce/report.json` | PASS: 7 named scenarios/checks, 36 matrix cases |
| Contracts + independent sidebar chain | `fix-a366288/contracts/bdbd28f9f08945f088cffba91a6c23e7/report.json` | PASS: 7 named scenarios/checks, full exact chain captured |
| Interrupted driver attempt | `fix-a366288/core/fc70a3accc5b4b51b0cad6a10558fb96/interrupted.json` | INCOMPLETE: Windows ProactorEventLoop WinError64 stalled driver; only owned process tree stopped; sequential retry above passed |

Updated screenshots personally viewed include desktop selected/search evidence, 320px drawer, timeout/retry notice, actual200% full viewport, dark mobile populated experiment, dark desktop evidence and the expanded full acceptance/sidebar chain. Normal browser font styles measure important labels14px and auxiliary labels12px. Playwright emitted cancelled-route callback warnings during the timeout fixture's cleanup after assertions; they were not application errors and do not invalidate the saved result.

Original workflow transport failure was followed by successful independent run `workflow/fc5daf0a052049208bbb9a45ef55e6d4/report.json` (6 checks, 12 populated-release matrix cases). The failure remains retained. Backend and tests/ui files are byte-identical across baseline/fix; four UI source files changed, and affected paths were rerun as listed above.

## Reproduction

From `D:/作品集/ResearchOS/research-os`, first create a detached worktree at `.local/worktrees/w13-ui-review` from `70db969`, and reuse installed web dependencies via a junction at its `apps/web/node_modules`. Build that frozen worktree with `node node_modules/vite/bin/vite.js build` from its `apps/web` directory.

Then run `python execution/verifier/W13/ui-70db969/run.py core`, `contracts`, `content`, or `workflow`. The wrapper redirects output only. Use `python execution/verifier/W13/ui-70db969/run.py independent` for reviewer-authored real-record URL/keyboard/typography probes; set `REVIEW_TIMEOUT_PROBE=1` to additionally hold a request for 35 seconds. `python execution/verifier/W13/ui-70db969/audit.py` verifies API mapping, schema binding names, screenshot hashes and historical source lineage.

## Evidence

| Scope | Report | Result |
| --- | --- | --- |
| Core + native zoom/PDF | `core/70daec802444440a8b5020066406913e/report.json` | Executed PASS, 108 screen/theme/viewport cases plus named functional checks |
| C17/C18/state/recovery | `contracts/6806c926274848df9cd104f51f29de1c/report.json` | Executed PASS, exact before/after projections, real receipts, six error responses and five-copy notifications |
| Populated content | `content/a98739d483934a05a98bd927b4631517/report.json` | Executed PASS, 36 populated screen cases, budget three-mode real HTTP writes, private/stale denial |
| Reviewer counterexamples | `independent/2dd10dd41012458fb3b3b36ffe9e40e6/report.json` | Three defects reproduced; exact 320x780 focus trap/return passes |
| First core attempt | `core/d58c3308230740ee88080d9836f29b74/report.json` | FAIL before assertions: browser initial navigation timed out; preserved |
| First workflow attempt | `workflow/c2b05f4ea0af45a78e9c63a8d26eeefc/report.json` | FAIL on urllib notifications GET after real workflow assertions; preserved with service log |

`audit.json` mechanically checks 63 operation methods/paths and 44 schema field bindings. This does not equate registration with live business integration. It separately lists exact hash deltas for all five historical author runs rather than inventing a common source head.

## Screenshots actually viewed

Reviewer inspected original files through image tools: selection before/after refresh; mobile 320 keyboard; 35-second pending resources; C18 desktop and mobile drawer; mobile notification release deep link; populated dark mobile experiment; populated dark desktop knowledge; populated light desktop resources; native 200% settings viewport; native PDF page pixels/controls; HTML sandbox; stale fixed-ref denial; real profile conflict with both drafts.

The 200% capture contains all four bottom navigation actions and the complete viewport width. C18 drawer shows 4/9 accepted with 2 pending-review; no false completed percentage. HTML screenshot shows controlled content and a blocked external image; network assertions record no external response. Draft screenshot preserves local and external text. Main typography defect is visible and confirmed by computed CSS measurements.

## Interpretation

Browser and fixture qualification are recorded independently. Mobile viewport is not a physical phone. Chromium freeze is not physical OS sleep. Protected classification metadata tests contain no real holdout bytes. No external channel or provider call was made. Backend outbox/domain evidence must accompany C17/C26 formal assembly; W17 remains responsible for actual protected storage/device boundary. C23 explicitly permits fixed backend fixtures.

The tests reuse the original author setup and assertions transparently; `independent.py` contains separate reviewer-authored counterexamples. No product or author evidence was edited. No old policy-rejected directories were cleaned.

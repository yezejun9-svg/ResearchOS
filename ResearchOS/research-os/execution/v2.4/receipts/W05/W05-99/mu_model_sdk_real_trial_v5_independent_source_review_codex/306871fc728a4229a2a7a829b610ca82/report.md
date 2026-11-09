## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** v5 improves the actual saved CLI context evidence, but three real-path correctness/evidence gaps remain. Source review does not authorize a provider request or accept a formal case.

### Critical Issues

None established in this source-only review.

### Important Issues

- **R01-v5 — mu_sdk_trial.v5.final.proposed.py:217–218.** The entire JSONL is required to be one row. Real cli_stream emits verified session.event records (:411) before the final summary (:849), so a legitimate live turn is rejected after its effects. Accept one unique final summary and strictly validate/preserve preceding real event rows. Keep cursor/build/session/Run settlement bindings, reject unknown/foreign/order/replay/duplicate/trailing rows, and treat EVENT_RESYNC_REQUIRED as the existing nonzero recovery path.
- **R02-v5 — runner:1080–1091 and :659–663.** Bootstrap runs a default non-draft goal and then hardcodes provider_requests=0 without actual effect/provider evidence. CLI non-draft goal follows a real terminal execution (:704–718, :461–490). Freeze an explicit no-execution DRAFT bootstrap with real admission/context evidence, or bind/meter its actual Run effects under a revised finite Root partition. A fabricated zero or local zero-provider possibility cannot prove this record.
- **R03-v5 — runner:1115–1117.** The ordinary Task must use doc.goal_id bound to the old bootstrap Goal, while a successful session.send must admit a different Goal (:694). The legal ordinary turn therefore fails after real SDK effects. Derive and bind the new Goal/Task/Run from the same admission/final raw and actual DB objects, verify its effective budget and Root generated-output allowance, and retain the bootstrap Goal as history.

### Suggestions

Use the actual emit/terminal field matrix in audit.json for controls. A normal success requires matching RUN_STATE revision/status/settled_at, children_stopped/queue_empty and AVAILABLE ARTIFACT evidence; single-summary non-draft success is not a real native shape. Do not require invented generic-event fields. The additional public schema locator remains OPEN after preserved metadata failures.

### What's Done Well

The new CLI saved_context follows successful saveCLIContext only, omits it on save error and preserves failure status. The final snapshot comes from the real scope-checked session.get; the follower exposes it only on the same real path. Raw config pre/post bytes remain tied to the original stdout. Four prior Go candidates and thirty-four runner definitions remain byte-identical; earlier authority/isolation/qualification/first-cause guards remain unchanged.

### Verification Story

Tests reviewed: authored 27 pure IO controls, not executed by reviewer; their single-summary positives miss the native streaming shape. All 25 source MF members and six basis refs were already independently checked, with exact generated complete diffs, four Go equality and unchanged template. Final sealing rechecks only selected affected/basis pins. Python AST reviewed; Go compile/build, CLI, SDK, native, model and CAS not run. New reviewer failures: two metadata locators (outer1/nativeNULL each) plus one V8 tool-array shadow failure (outer/nativeNULL) and one supplemental inverse sealer TypeError (outer/Python1/1), each preserved once. The V8 full outer wrapper was not separately captured; its exact failure statements, actual error and complete intended nested patch are preserved with the gap explicit. Inherited author641/642 and prior640 are not recounted. No Main/canonical write or formal increment.

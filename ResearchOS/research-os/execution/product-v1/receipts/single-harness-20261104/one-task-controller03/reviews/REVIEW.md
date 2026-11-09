# Single-task revision03 independent SECURITY review

**Decision: APPROVED_SOURCE_FIXTURE_ONLY.** No remaining source blockers were found within this revision's task identity and Native budget-delta scope. This does not approve a real run. Formal increment 0; product increment 0.

The exact frozen runner is `9a2b27c35f4e17626bc9c1511d8d53b3e83927dc5330151c3a549c7c22b4280a`; helper `7bed726cb6a9b71e65ab9fbbd3b10702d066a8ad34347ee84e5db16805685648`; FROZEN `653b312f74d84ec3d1d1d8f8f8482c5c537850f852030e25e0aff28a34d00460`. See REVIEW.json/sourceSHAmap.json for the complete mapping.

Known findings TASK02-F1/F2/F3 are resolved for source/fixture purposes, without counting them as new findings:

- Lines 192–218 bind typed pending and authoritative list/get Tasks to the first valid request and Task references. Observed pending must be a submit with matching prompt/workspace and permitted state. A cleared null journal retains the pins. If no pending is observed, the first validated singleton Task receives FIRST_AUTHORITATIVE_TASK provenance.
- Lines 628–638 retain the original request/Task/Run during UNKNOWN recovery by using those same validators. Conflicting observations are recorded separately. There is no second submit, replacement request allocation, or automatic task cancel.
- Lines 185–228 and 567–576 bind list/get Tasks, page snapshots, embedded public Tasks and event headers to at most one RunRef, including epoch. The first run is stored before event paging can throw. Clearing the event display map at line 578 does not clear identity pins. Lines 606–612 additionally bind the terminal payload to the same original Task/request/final run.

Independent checks evaluated only the extracted pure predicates and assignments, never the runner module. All 26 new check rows passed, including both request mismatch directions, failed pending reads, changed Task/workspace, immutable recovery refs, two runs in the first page, changed epoch, reset snapshots and embedded Task conflicts. The original RunRef remained pinned after rejection. Valid same-run history and null journal cases were accepted. These checks validate observer behavior, not actual Host execution.

The frozen Native04 helper hash is `0f30f3cb2ca21c381871df9f731aed3f9051d41f44573f66af7d5aa8e9d42c7c`. Exact source comparison, normalizing only line endings, proves that revision03 changes just its scope guard: global one Task/invocation, explicit zero-task/model Native stage, no retries and no operator fallback. Seven separately extracted pure PowerShell guard cases passed. The copied Win32 ownership, warning IDOK, deadline and normal-cancel code is unchanged; its separate Native review remains required.

The bounded Native reply parser now accepts valid exit2 blocked diagnostics for observation while rejecting them for success. Pure cases preserved INVALID_PATH and UNKNOWN after a recorded invalid OK attempt. No successful authorization is inferred from an input string, warning, helper exit or unknown result. Actual Native success plus Main binding is still a separate prerequisite.

Inherited task safeguards remain intact in the revision diff: one normal DOM submit; actual LOGGED_IN/chatgpt capabilities immediately before it; fixed read-only CLI profile/source-context behavior; filename-only prompt; final result and same-run public ASSISTANT_MESSAGE canary checks; unchanged fixture hashes; bounded flow and normal app.close with external original Job accounting. The template now has one picker deadline (90000 ms) and still has null execution/prerequisite pins. Internal model API-call counts are explicitly NOT_MEASURED; the controlled boundary is one native Harness invocation/Task.

Runtime prerequisites are listed separately in REVIEW.json: independent Native04 review, actual successful zero-flow/Main binding, matching original f13 Job evidence, post-flow full source/bundle integrity, and a fresh Root-approved exact one-task scope/Job launch contract. Root reported a new actual Native flow was running; this review neither observes nor attests its outcome. Earlier blocked flows do not satisfy success prerequisites and must not be blindly replayed.

Node syntax exited 0 and PowerShell AST had zero errors. No old suite, app, GUI, model, Codex CLI probe, helper entrypoint, SDK import, Win32 call, auth/account read, or D read/write occurred in this follow-up. Reviewed candidate files were not modified. All review artifacts are C-only.

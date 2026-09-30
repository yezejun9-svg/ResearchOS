# W08 manual negative disposition independent review

Verdict: **PASS_IN_SCOPE**. No blocking defect was found in the reviewed manual negative-disposition compatibility change. This accepts the bounded repair and its preserved evidence; it does not declare full C05, A05, C06, W08, live-provider research, monitor acceptance, or product E2E completion.

Production source: `78d4de057ca9f0810d8bfe4f5aac5c4c856c44ba`. Final source: `57ef0892e60c9fdf9a57aad2dd62f82e002ff337`. Frozen raw-evidence commit: `f820a2b2df592034faecf4bd4d2278ab10cc4795`. Author worktree was clean during review. The independent verifier executed no tests, provider calls, native Windows flows, private CLI flows, database mutation, or cleanup.

## Contract and implementation

`spec/v2.0/01_PRD.md:126` and `03_DATA_CONTRACTS.md:104` allow COMPLETE after required source coverage and experiments finish even when nothing is adopted. Migration `migrations/sqlite/0020_research_cycle_work.sql:110` preserves old manual annotations and separately requires the new driver's three independent bindings. Treating every manual annotation as a failed monitor review broke this distinction. The original public C05 close failed with HTTP 422 and verified outcome PARTIAL; that failure remains in the R02 raw evidence.

The final code restores only the manual negative branch. `research_acceptance.go:108` queries both durable monitor bindings and durable work bindings in the current transaction. The branch requires both counts to be zero and an explicitly supplied authenticated principal. Zero-work monitored cycles and retired monitors remain on the strict branch. There is no caller-controlled manual flag, trigger heuristic, current-monitor-only heuristic, or missing-work shortcut.

`candidates.go:158` reads only annotations whose `reviewer_id`, `review_task_ref`, and `acceptance_ref` are all NULL, and admits only REJECT, WATCH, or INCONCLUSIVE. The shared validator at line 60 rechecks frozen/current profile, stored review revision, target membership, candidate membership, current observed Evidence, durable source-page membership, exact effective snapshot ref, readable snapshot, sealed snapshot byte hash/size, current project/source permission, and current W09 origin support. WATCH and INCONCLUSIVE need both gap and revisit trigger. Cached support is ignored.

The resulting `MANUAL_REVALIDATED` object has `acceptance_ref=null`, `independent_review=false`, and `authority=false`, and omits the monitor `support` field. This is a derived current annotation, not a persisted independent receipt. `researchProgressKeys` therefore cannot turn it into independent progress. Manual ADOPT remains excluded. The original ADOPT improvement and independent-acceptance checks remain in the common validator, with additional current-snapshot validation.

All production callers were reviewed: authenticated public close passes its transaction principal (`research.go:39,387`); delivery-stage facts and runtime coordinator pass nil (`research_acceptance.go:33`, `runtime_coordinator_windows.go:709`); accepted report close has existing durable monitor/work bindings (`research_close.go:127,151`); monitor cancellation passes its authorized principal (`research_driver.go:314`). Existing independent `currentResearchReview`, `researchAcceptedTask`, and acceptance-service rules were not weakened. No schema, API, registration, frozen specification, or contract edit is part of this change.

## Preserved execution evidence

| Attempt | Actual exit and raw outcome | Review use |
| --- | --- | --- |
| Original R02, source `609837e` | Exit 1; five named tests PASS, C05 FAIL, package FAIL | Original failure retained; five earlier bounded passes reused at their recorded revision |
| Production repair `78d4de0` | Exit 1; original C05 PASS with 8 original structured assertions; matrix 19 PASS and 2 fixture failures | C05 repair evidence; aggregate remains failed |
| Final source `57ef089` | Exit 0; only new matrix rerun; 21 subtests PASS; package PASS | Final boundary matrix evidence |

The verifier reconstructed Go Output chunks by Package/Test before parsing complete lines. All 21 author-manifest file hashes and byte sizes match. The 12 listed source files match the final Git revision. The final-source-to-evidence commit changes only evidence files. The original `research_test.go`, including C05 assertions, is byte-identical across `609837e`, `78d4de0`, and `57ef089`. The only `78d4de0` to `57ef089` changes are the new matrix's unique Evidence URL and accepted intent-key fixture prefix. Reusing the already-passing C05 result is therefore justified without a repeat run.

The first matrix's failures are preserved: a duplicate Evidence index identity in the missing-page setup and a missing intent binding in the monitor setup. They are not reported as product failures or silently removed. Final coverage includes the three legal outcomes; nil actor; current/stored profile drift; absent target; blank reason/gap/revisit; ADOPT rejection; stale/simulated Evidence; stale snapshot; bad ref/hash/size; missing grant; restricted snapshot; missing durable page; and a combined work/monitor binding case.

The saved C05 SQLite projection independently agrees with COMPLETE, three durable pages, REJECT/WATCH/INCONCLUSIVE annotations, and a COMPLETED/NO_IMPROVEMENT experiment linked to a saved AcceptanceReceipt. Original assertions show no adoption and no false independent origin. The stable-release before/after assertion is `null == null`; it must not be presented as positive retention testing of an existing non-null Release.

## Execution boundary and limits

The test setup uses temporary SQLite and an in-process HTTP handler (`domain_test.go:141,165` with `httptest.NewRequest`/`NewRecorder` at lines 176/184). `researchSetup`, `capture`, and `sourceFixtureAdapter.Fetch` use local fixture source pages; no external source call is implied. The C05 experiment uses fixture runtime output and deterministic local acceptance. The monitor boundary setup uses accepted planning fixture output, not an executable producer. The new matrix changes only rollback-scoped fixture projections/insertions; no historical sealed source bytes, immutable old review, old receipt, or source page were rewritten.

The work-only negative fixture stops through an existing monitor-validation gate. It proves this fixture cannot complete, but does not independently isolate the necessity of the new work-count predicate. That predicate is supported by direct code inspection. The zero-work permanent monitor binding and retired-monitor checks directly cover the intended downgrade risk. Positive ADOPT and complete accepted-monitor delivery were not rerun; preservation claims for those paths are source-review claims.

The earlier R02 manifest has 340 equal before/after source hashes. The final source differs in 11 of those files, recorded in `original-r02-review.json`; the new matrix is additional. Five earlier PASS inputs remain bounded historical reuse, not five fresh final-source runs. A05 historical byte binding or LIVE metadata does not establish new provider freshness. Backend C06 reuse does not complete its separate frontend acceptance. No broader case status should be promoted on this review alone.

## Review artifacts

- `input-manifest-audit.json`: 21 exact file/hash/size checks, Git source binding, clean-worktree observation, fixture-only and evidence-only deltas.
- `raw-attempt-review.json`: commands, actual exits, reconstructed raw assertions, terminal events, preserved failed attempt.
- `original-r02-review.json`: original C05 failure, five bounded passes, 340-file equality and explicit final-source delta.
- `c05-snapshot-review.json`: public saved SQLite projection checks and non-null Release limitation.
- `reviewed-inputs.json`: exact reviewed evidence input hashes.
- `audit.py`: reproducible read-only audit; it contains no test execution.
- `review.json` and `sha256-manifest.json`: structured verdict and verifier-output integrity binding.

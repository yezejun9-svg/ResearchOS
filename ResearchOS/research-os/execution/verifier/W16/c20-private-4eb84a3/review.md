# C20 incremental read-only review

Verdict: `PASS_READONLY_EXISTING_FIXTURE_EVIDENCE`.

Scope: independently inspect existing source and receipts, then recompute the already retained private fixture results in memory. Source `4eb84a3a4ae41ae9acd6d9bc21582c478fa855c6`; author raw receipt commit `0503ede60acc606caef4f645a6e83d038cb3ab83`. No new candidate, Go test, native process, adversarial payload, or protocol probe was executed. The earlier platform-blocked runtime review remains blocked and is not superseded by this C20 result.

## Fixed findings

- The former impossible gain expression is replaced by a per-case rule: preserve every previously correct answer and require at least one newly correct answer. Self-scores do not participate. Source `ops/supervisor/holdout_windows.go`, `objectiveHoldoutGain`; author raw log records the positive example, score-only inflation, and gain-with-regression cases passing. This is a pure function positive test, not a new native positive-benefit scenario.
- `internal/domain/evolution_holdout.go`, `evolutionHoldoutVerifierCurrent`, rechecks an active principal, current role and restricted grant, and root independence from both candidate author and current release principal. Calls cover initial registration, evaluation entry, post-I/O journal binding, and later proof consumption. Existing missing/tampered-proof and revoked/removed-grant tests pass. Root-identity and mid-I/O revocation paths were inspected in source, not newly executed here.
- `TestW16C20` now retains inputs, labels and the dual-run proof in the separately located protected fixture store. It closes and reopens that store before reading the three blobs and recomputing the verdict. The ordinary receipt includes only a locator, hashes and aggregates. Other negative test helpers retain their temporary storage behavior.

## Independent evidence checks

`audit.py` reads only frozen Git blobs and the existing protected fixture directory. `audit.json` records 26 passing checks, 156 matching source hashes, 14 public receipt files, and three matching protected blob/descriptor pairs. Private rows are not copied or printed.

The private inputs and labels retain the same revision, have two distinct non-public case IDs, and their objective answers independently equal the input arithmetic. The proof binds the plan, input and label digests, stable/candidate build digests, public suite, and policy to the normal regression record. All four existing invocation receipts bind exact single-question requests, identical question bytes across builds, raw output digests and base64 stdout. Each records exit 0, stopped children, no timeout, no capabilities, a PID and a distinct AppContainer SID.

Independent recomputation yields baseline 2/2 and candidate 2/2, equal objective outcomes, increased self-scores and changed rubric labels. The public aggregate correctly says `gain=false`, `NO_IMPROVEMENT`, `real_world_gain=NOT_ESTABLISHED`, `project_closed=false`. Private case IDs and blob tickets are absent from all 14 public receipt files.

The author's existing normal log has five tests passing, no failures or skips, and seven assertions referenced by their exact raw line. The separate existing gain log records three subcases passing. The author reports exit 0 for both commands. These are reviewed existing author runs; this verifier did not rerun them.

## Limits retained

This is a deterministic two-question private fixture (`model_revision=NONE`), not a formal held-out real-user quality study or LIVE provider result. It establishes rejection of score-only improvement for these retained executions. It does not establish broader quality, generalization, formal C20/A16/global acceptance, production promotion, or an independently qualified OS service.

Build digests are consistently cross-bound among the proof, locator and normal regression artifact metadata. The temporary native executable bytes are not retained here and were not independently rehashed. Historical SQLite frozen/evaluated journal behavior and protected provider access controls are assessed from the frozen source; the retained directory contains raw blobs and descriptors rather than a persisted database snapshot. Windows receipt fields are evidence of the author's run, not a new verifier OS-isolation certification.

The author's `report.json` appropriately remains `PARTIAL`, `W16_G02_FIXTURE_ONLY`, `independent_acceptance=NONE`, with formal LIVE/global gates unchanged. This read-only review closes the specific gain, current-authority and private-fixture persistence findings within that scope.

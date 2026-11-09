# W03-99 executor handoff

Status: **IMPLEMENTED_PENDING_INDEPENDENT_REVIEW**. The executor owns no formal acceptance IDs. A03, C04, C19 and full W06 service acceptance remain **NOT_RUN**.

The original current-contract probe exposed a real mismatch: the production persistence loader still selected the legacy ProjectBinding and EvaluationSummary contracts. The isolated nested producer diagnostic also confirmed legacy bindings on persisted ProjectState/Goal/Task and a downgraded summary. All failed runs and their source manifests remain under immutable UUID directories in `runs/`.

The authorized repair loads the root-owned exact five-root v2.4 projection. Recognized legacy routes retain strict legacy validation; recognized current routes select strict current validation; unknown or missing routes fail. A trusted fixed `NewCurrentMu` constructor is wired into REST, native Host and replay. New goals inherit persisted project bindings and new tasks inherit persisted goal bindings. Existing objects are not migrated or rewritten. Summary versions follow validated report versions, and the existing artifact sealing boundary still rejects direct experiment output.

GoalPage, TaskPage and TaskClaimResponse retain original outer constraints, required fields and nested run/lease validation. Only their complete nested Goal/Task alternatives change to strict legacy/current `oneOf`. `envelope_preservation.json` is a **static reconstruction**, with exact original recovery hashes and full rebuilt schemas; runtime evidence comes from the recorded HTTP/list/claim tests.

| Gate | Mode | Actual current evidence |
| --- | --- | --- |
| W03-G01 | DEVELOPMENT | 14 top-level Go tests, 2 subtests; 126 probe checks: projection 9, aggregate 9, original fixtures 106, corpus metadata 2 |
| W03-G02 | FIXTURE | 10 top-level Go tests, including evaluation guard refusal without partial sealing |
| W03-G03 | FIXTURE | 5 top-level Go tests; 26 probe checks: types 12, bindings 14 |

The 106 original fixture decisions remain 76 positive and 30 negative. Counts above describe different levels and must not be added into a product acceptance count. Each parent gate returns only its single exact parent assertion ID. The separate 30-test Python regression run is synthetic driver verification and is not a product atom.

The final atom source HEAD is `9bb09128`; exact full IDs, commands, working directories, source manifests, timestamps and raw hashes are recorded in `handoff.json`, the current indices and their referenced receipts. The earlier G02 run on `062cce3b` failed because the new test used OWNER instead of EXECUTOR. Commit `9bb09128` fixes only this test principal and produced_by value; no production authorization was weakened. All three gates were then rerun against the changed input and passed.

Integrate owned commits in order: `3e64c5f3`, `062cce3b`, `9bb09128`, followed by the final evidence commit supplied in the executor handoff message. The candidate projection input commit `cefc5970` is a cherry-pick of root-owned `5d3063d9` and must not be duplicated in main. Shared state and command registration remain root-owned.

The registered bridge must be invoked with explicit `contracts.validate` or `test.domain` key. Only exact W03 parent selectors consume current receipts; the two W03 child selectors retain their original Go route, and other legacy selectors retain original Python argv/environment semantics. Frozen expected test names/packages, probe IDs, fixture metadata, toolchain and source inputs are pinned before execution. Verification rejects duplicate or missing IDs, non-finite JSON values, boolean exit codes, failure/skip events, raw/manifest changes, stale input and empty output. `--run` refuses another attempt on an unchanged failed input.

Root integration should compare all five atom input manifests with current main bytes before exact registered dispatch. Dispatch performs read-only receipt verification and does not execute Go again. The original checker with a fixed migration count, providers, GUI, NVDA, protected services and blocked W13 audit were not invoked.

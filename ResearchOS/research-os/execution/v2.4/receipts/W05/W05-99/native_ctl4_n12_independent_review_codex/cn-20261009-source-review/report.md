# CTL4 and N12 independent Source review
Reviewer: codex:/root/attach_fixture_source_review, not the author of either component.

## Component 1 — CTL4
Decision: SOURCE_ACCEPTED_PENDING_FRESH_CONFIG_AND_ROOT_ACTUAL.
Reviewed controller e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3 / 42696.

The actual diff changes only case_deadline_seconds 1260 to1560, run_owned_observed timeout1260 to1560, and serve-loop deadline1270 to1570. Whole-file inverse matches pinned CTL3 exact bytes; separate AST comparison confirms exactly those three constant nodes and no other changes. The owned timeout is now 26 minutes, with loop guard ten seconds later. Main20+cleanup4=24 < Go25 < owned26 < outer30; loop1570 also remains below outer1800. Current stop handling, native ownership observations, phase checks, guards, private broker policy and grant TTL are unchanged.

This resolves the previously identified Source coordination prerequisite, but not actual retention qualification. Root must create fresh Config/FrozenInputs binding CTL4, compiled reviewed cleanup Source and independent receipts before a live native case. Old CTL3 Config cannot be reused. Actual elapsed setup, failure paths, hard kill and runtime closure still require real evidence; no four-minute live retention claim is made.

## Component 2 — N12
Decision: SOURCE_ACCEPTED_FOR_ROOT_BUILD_AND_PURE_UNITS.
Reviewed preparer 1cf7b54983a6429f2ac9fae9c494c12313856dad10ba6bbe3361261cdad05863 / 8795; compile/unit caller9a31843dc1721df26efb04fc9a11fdb6c38b3c9de5403f421044558876ae2e71 /16765.

The preparer changes only the explicit new sparse worktree and isolation paths from the pinned T11 preparer. It retains all six owned Git calls, current checkpoint SHA/bytes/revision parameters, dirty/staged checks, sparse product-only checkout and canonical protection. No Git was run by this reviewer.

The compile caller is a byte-reversible derivative of the pinned N8 actual caller through 21 explicit substitutions. The actual cleanup and independent review manifests are dictionaries and the caller handles them correctly; the Root caller manifest is a list and was verified separately. The independent HDF status field matches the exact value checked by the caller. The original 43 formatted Source refs were read and verified; only the reviewed cleanup harness replaces its previous exact member, leaving42 unchanged. Before compilation the caller verifies those42 remain byte-equal after official gofmt and records the changed member's formatted pin.

Historical N8 evidence was independently checked as historical evidence: eight invocation receipts have actual exit0 and closed owned Jobs; all five source-guard receipts show closure. Actual previous unit evidence has28 passed leaves and2 parents. The reviewed cleanup test adds exactly4 named children and1 parent, producing32 leaves,3 parents and35 terminal test names. expected-units.source-only.json records this derived inventory as expected, not observed N12 results. The caller's exact parent selector excludes TestNativeMigrationAuthorityHarness, and its terminal parser rejects duplicates, missing/extra roots, wrong totals and any fail/skip.

The eight future owned build/unit jobs remain: format, actual tagged compiler inventory, four program builds, tagged harness compile and selected pure units. Four program targets and fresh output namespace were checked. Compiler inputs retain actual test, external-test and embed fields; five guards close in finally. Checkpoint parameters are dynamic instead of hardcoded revision361. Existing Main/canonical byte checks and zero native-case/private-owner/signature claims remain intact.

Root may execute N12 preparation, build and these selected units independently of starting a live native case. This Source acceptance is not compiler/Go-AST/test acceptance and does not qualify native nine-case coverage, formal product status, Owner authority or whole-fixture acceptance.

## Evidence
272 independent Source/pin checks passed.93 immutable input files were rehashed unchanged. Both supplied HDF/MF pairs and all component manifest members match. Exact inverse proofs were verified against actual base files, with semantic review of changed fields and command scope. No candidate main/controller/API, current Git/Go/native/SQL/model execution or private-resource reading occurred. No new mechanical errors; no Main/canonical or candidate Source writes.


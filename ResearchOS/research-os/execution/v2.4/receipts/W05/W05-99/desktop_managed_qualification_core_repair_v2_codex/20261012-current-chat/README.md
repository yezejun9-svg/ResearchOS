# Desktop managed qualification Core v2 source repair

Status: SOURCE_FIXTURE_PENDING_INDEPENDENT_REVIEW. No formal parent acceptance, Canon change, Main integration, real model call, paid model call, or production Desktop acceptance is asserted.

Candidate `0df32ed4eeeba3b9714477ccfae759ef90b633ee` is based on frozen `63dec0f43b7a30d36e68a9826dc36e633936318f`. Worktree: `.local/worktrees/w05-desktop-managed-qualification-core-repair-v2-20261012`. Four changed files, with fourteen cumulative files from the original `dfefe326dd7f4ae528caaf311ae388f40b8f0841` baseline. Source scope is CP415 / OW204; no additional path was needed. Old source and independent-review packages remain unchanged.

## Corrected behavior

DMQ-P1-001: release quiescence captures the existing intake state. A busy release restores only release-owned state, then composes the original state with active qualification, managed startup hold, and the original durable consumed-request/Run/effect records. Abort uses the same composition under `scanMu`. A database observation failure retains closed intake. Scan early returns explicitly retain closed intake for all managed fence causes.

DMQ-P1-002: the constructor, while owning or borrowing the original exclusive data-root lease, begins with closed intake and synchronously queries durable managed qualification state before returning any coordinator. Unresolved consumed requests and ManagedStartupHold keep intake closed. A failed observation returns no coordinator and releases the constructor's lease/borrow. Ordinary nonmanaged startup remains open. Recovery failures in Serve and explicit Begin close intake.

Admission still reads only the atomic guard inside its existing transaction; fence composition reads durable state while holding `scanMu` outside admission transactions. No second coordinator, worker scheduler, truth store, protocol expansion, budget reinterpretation, or UNKNOWN retry was added. Existing UNKNOWN/null ledger bytes and root-liveness/profile/acceptance gates are unchanged. The private protocol remains researchos-desktop-management/1 with decimal-string process creation time.

## Final evidence

- `attempt10-frozen-domain`: 35 parent tests and 86 subtests pass, no skips. Includes 4 new parent tests / 13 subtests for lifecycle fences and the existing real native READY-task suppression test. The new cases exercise actual V2 session.send transactions before the first Scan, after rejected drain, after release abort, and after Scan, asserting RESOURCE_BLOCKED and unchanged original session revision/writer plus Run/effect census. Positive cases retain normal startup and release-abort semantics. Cancelled database observations and failed startup recovery remain closed. A disposable schema fault proves constructor failure releases its original lease borrow.
- `attempt12-frozen-review-overlay`: the independent review's original three test functions are used without changing their bytes via Go overlay. All three pass on the frozen candidate. The overlay points to the original immutable reviewer file and never edits candidate source.
- `attempt11-frozen-host`: 7 parent tests / 12 subtests pass. Actual compiled control generations 1 and 2 exit 0 using the original inherited management pipe; Host/Owner identity survives and a second coordinator is denied. Actual Host/Mu AppContainer/independent verifier process/server acceptance/specific mu_turn purpose and normal turn pass with synthetic loopback SSE. Lost pipe reply settles the original effect exactly once. Four service-root revocation stages remain denied with original historical evidence retained. Total synthetic SSE calls: 8; real model calls: 0.
- `attempt14-frozen-verifier`: 2 parent tests / 9 subtests pass, no skips.
- Both candidate binaries were built after commit. `freeze-source.py` verifies Go build metadata contains the exact candidate source revision and `vcs.modified=false`, and records executable hashes.

Raw argv, environment, timestamps, process exit codes, stdout/stderr, and parsed terminal test events are retained next to each attempt. `run-evidence.py` reproduces each phase using the pinned local Go toolchain, existing Mu/node assets, and candidate executables.

## Retained unsuccessful attempts and limits

`attempt02-targeted` initially lacked the fixture Host LeaseTTL and failed at HOST_UNAVAILABLE before reaching the admission gate. `attempt03-targeted` then showed session.create follows its existing offline-creation contract and does not reach execution admission. The test was corrected to the original session.send execution path, and `attempt04-targeted` passed. Both failures remain untouched. `attempt13-frozen-verifier` targeted the executable package, which has no tests and reports a package skip; corrected final attempt14 targets internal/verifier and has no skip. No evidence is deleted or relabeled.

The actual compiled control lifecycle and in-process actual Host qualification tests are distinct test layers. This repair's new session admission/startup/abort combinations execute the real coordinator and ClientService transaction in disposable domain fixtures; they are not claimed as a combined Electron-to-control end-to-end acceptance. No default Desktop client file was changed. UNKNOWN cost ledger reservations still block graceful release under the pre-existing drain policy; this repair preserves that behavior. The final process census found no remaining researchos-control.exe process. No force termination or new blocked cleanup was performed.

# Historical schema14 observation fixture revision

Status: SOURCE_IMPLEMENTED_PENDING_ROOT_TESTS_AND_INDEPENDENT_REVIEW. This is not acceptance or execution authority.

Apply only the two pinned test Source overlays to Root's existing 38-file reviewed composition. Do not replace the schema22 bridge import revision or other newer Sources with the older 6b0 product files. The preceding schema24 migration and native authority contracts remain unchanged.

The exact restored schema14 guard runs immediately before the historical Service.ObserveRuntime adapter. The adapter is copied byte for byte from the pinned historical runtime.go, with its method name as the only transformation. The pre-existing historical ResumeCheckpoint helper prefix is unchanged. This does not attest the entire current package as a frozen historical executable.

The original LOST observation, current Run identity, same-Run resume, unknown-effect rejection, old-observation rejection, no-private-read assertions and version20 observation route remain intact. No migration, table insertion, direct observation SQL at the fixture callsite, skip, production method or authority relaxation is introduced.

Root must independently verify pins, format/build in a new isolated composition, and run the original targeted historical suite with the exact matched historical14/schema22/source22/target23 resources from the pinned prior invocation. Fresh raw stdout, stderr, invocation and owned Job closure evidence are required. Failure 785 and the separate read-only failure 786 remain preserved and must not be recounted.

Source author ran only metadata reads and Python source construction/static comparisons. No Go, gofmt, tests, SQL, native runtime, provider, signing, private-resource access, Git, Main/canonical or existing Source/worktree writes.

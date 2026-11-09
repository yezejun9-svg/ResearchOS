# H20 original failure914 independent actual closure and root-cause review

Verdict: FAILED_ACTUAL_CLOSURE_VERIFIED_FIXTURE_ROOT_CAUSE_CONFIRMED. The fresh sparse preparation and tagged compilation succeeded; the selected H20 test run failed. This review accepts the integrity and closure of that failed evidence, not H20 upgrade behavior or full-scope acceptance. The original Source, failed actual and ordinal914 remain unchanged.

## Actual execution and exit qualifications

The pinned isolation.ready is21f41df3619d6954213b20f1480eaf408468a93b9b948843c19bed957aaebd2f /4090. Root original ac2b92/session18654 completes at a14101 with outer exit0 and explicit ROOT_PYTHON_EXIT=0. Six owned Git calls have actual primary exit0.

The pinned validation.closed is8bab73ebf17c9eebc033ddaa8fc03645645e42f7c9f0a3e7a9aabc31c72e20fc /26709. Root original2a83a5/session23379 completes at f53be7 with outer exit1 and ROOT_PYTHON_EXIT=1. Format, tagged go list and tagged test-binary compilation each have actual primary exit0. The official test2json primary has actual exit1, PID37092, FILETIME134359937149867944. The individual descendant test-binary exit was not separately observed through an owned process handle and remains NULL; it is not inferred as an independently measured exit1.

All ten owned Job records have concrete positive PIDs, distinct PID/FILETIME identities, assignment before resume, no timeout or helper error, primary exit confirmation, idle Job with zero active processes, closed handles and no cleanup errors. Original FILETIME tokens were parsed as exact Python integers and preserved as decimal strings in owned-job-audit.json, never converted through floating point.

The two isolation guards and five validation guards all report closed/no retained handles/no errors. Every retained entry was verified, matched its final path and closed. Their referenced files were independently rehashed. Seven actual guard receipts are indexed in actual-guard-audit.json. The failed validator's finally closure completed; the assertion that rejected the test result is part of the same original failure914, not a second test attempt or a new failure.

## Real compiled Source and state preservation

The actual61-member raw overlay equals the reviewed composition and preserves the exact AF/non-H20 T11 raw refs. Gofmt actually changed12 files' bytes in the fresh worktree; format-delta.json records original and formatted refs, including AF. Therefore raw-overlay preservation must not be described as equality of all post-gofmt bytes to their original T11 Source refs.

All61 formatted files and the actual test executable088dab730caf641417f82f26edf2c83a8977e86c6cc120f10a1a7b3a29e7a0a7 /42652160 were rehashed. The raw tagged go-list stream was independently reconstructed:352 packages,3733 compiler inputs,607 whole-product files,8 compiler tools and39 embed records exactly match the inventory. Whole product traversal agrees with all607 refs. The actual compile argv selects the tagged ./internal/domain package and writes the observed binary; the official test2json resource and its primary argv match the frozen executable and test binary.

The CLI package ./ops/backup was not built or executed by this domain-only compilation. The actual compiled domain suite includes unselected Sources without executing their tests. No existing Owner/full-product/native-authority status is promoted by compilation.

Both pre-run canonical receipts agree, and all four live files still match checkpoint364 and the exact checkpoint/path-ownership/step-state/commands pins. The actual pre-preparation Git status recorded13 tracked dirty lines with11 deletions and2 modifications and an empty index; before/after preparation HEAD isadc460c2138528f163f7fdab5e8d81dde157b7fb. These are the observed Git checks. There was no post-validation Git-status call, and this review makes no invented post-run Git or untracked-tree claim. Current canonical and guarded Source content checks support their own narrower preservation claims.

## Nine terminal records and what they prove

The original JSONL has exactly the five selected parents and four drift children: nine unique starts and matching terminal names,8PASS/1FAIL/0SKIP, and a final package FAIL. No unrelated parent or TestNativeMigrationAuthorityHarness executed in the event stream.

The only failing test is TestHistory20PublicUpgradePreservesSourceAndRevokesRestoredCredentials. Its error event is exactly backup_history20_upgrade_test.go:91: UPGRADE_PATH_OVERLAP: source, key, snapshot and target require separate directories. The source emits t.Fatal at the first UpgradeLocal return. It never reaches restored rows, Owner-row preservation, credential revocation, correct-key authentication or wrong-key authentication assertions. Successful public A20-to21 migration and those crypto/fence claims are NOT_OBSERVED.

The ledger-insert rollback test passed its specific fixture ledger failure assertion and complete pre/post schema/row equality checks. The implicit startup test passed its specific MIGRATION_PREBACKUP_REQUIRED assertion. Those narrow actual observations can be retained without upgrading the failing suite to a pass.

The four drift child PASS records do not establish their named release/schema rejection mechanisms. They use the same invalid path layout and assert only that some error occurred. The Source has a deterministic earlier overlap rejection before those checks. Their individual error strings were not logged, so the original JSONL does not directly record each returned error. They must be treated as coverage gaps/false-positive acceptance criteria, not four proven drift protections.

The generic restore-failure parent passed backup creation, some restoration error, absent destination, retained backup directory and unchanged source rows. It does not assert that the Migration callback ran, that its CREATE TABLE succeeded, or that errors.Is(err, context.Canceled) holds. Its PASS cannot prove reachability of the intended injected migration failure. This review does not claim the callback failed to run; the existing evidence is insufficient to distinguish it from an earlier restore refusal.

## Confirmed fixture root cause and bounded correction requirements

history20Fixture puts Source at base/source.sqlite and KeyFile at base/recovery.key; Snapshot and Destination are base/backup and base/candidate. upgradePaths compares the source parent, key parent, snapshot and destination for overlap. The first two directories are equal, and the latter two are nested under that same directory. upgradeHistory20Local invokes upgradePaths before release inventory/schema validation, key reading, template/recovery work and backup publication. The positive actual error and preserved Source agree on this root cause.

The production overlap guard is intentional and must remain unchanged. A corrected fixture needs mutually non-overlapping directories for source, key, snapshot and destination; putting those four in independent sibling directories is sufficient for this contract. Source/target release trees and program byte placeholders should remain explicit fixture resources. Correction must be made in a new candidate/review namespace, not by editing the failed Source or actual receipt.

The four negative tests must assert the intended error: migration-hash -> UPGRADE_RELEASE_HASH with the changed0021 name; extra-numbered-migration -> UPGRADE_RELEASE_MIGRATIONS; foreign-table and session-addon -> UPGRADE_SOURCE_SCHEMA. Their existing unpublished-output and source-row preservation checks should remain. If intended production behavior differs at runtime, retain that new failure rather than accepting any error.

The generic restore test needs an observed callback-reached flag set at entry, successful injected DDL before returning context.Canceled, and errors.Is on the returned wrapped error. backup.go wraps callback failures with %w, so that assertion is supported by the preserved production code. Keep the destination/backup/source checks. These are review requirements for the next Source revision, not changes executed here.

The prior H20R1 Source pass and caller Source approval remain historical facts. Failure914 demonstrates their runtime acceptance gate was not met; neither is retroactively rewritten into a successful execution claim.

## Scope and independent verification

25791 independent checks passed;5005 input files were rehashed unchanged. The review SourceReadGuard was released with no errors or retained handles. Canonical files were compared before/after but excluded from this review's held handles. Reviewer actual execution was isolated read-only Python and writes solely in this new evidence namespace; actual outer/Python exit0 is explicitly recorded.

The original Root run did execute scoped fixture SQL inside the selected tests. The reviewer did not execute Git, Go, gofmt, SQL, native product, API, model or private-resource operations. No candidate, failed actual, canonical file, Main or old worktree was edited. No new mechanical failure occurred in this review.

The synthetic data and dummy program bytes do not establish genuine historical CLI release or Owner provenance. Complete successful20-to21 restoration, explicit session transition, existing21-to22 continuation, complete20-to24, real Owner and broader product acceptance remain OPEN. The next fixture revision and its fresh execution require separate review. STOP/FINAL.


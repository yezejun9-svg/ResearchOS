# H20R1 independent Source review

Verdict: SOURCE_ACCEPTED_PENDING_ROOT_RUNTIME. H20R-001 is resolved at Source level. This does not assert successful Go parsing, compilation, SQLite tests, native execution or formal historical20-to24 acceptance.

## Correction

The updated first test checks the snapshot's localUpgradeFormat and the exact History20 plan ID, supplies the matching manifest.Purpose policy, and requires readBackupPolicy with the correct key to succeed. That call authenticates the manifest, decrypts all listed files and validates their sizes/hashes before returning. The test also requires state.sqlite, historical migrations1..20 and no portable export. It then changes only the key and uses the same snapshot and policy; BACKUP_MANIFEST_INVALID and nil files are required.

The correct-key positive control eliminates the earlier format mismatch false positive. No production format or authentication guard was weakened. Deriving purpose from the manifest is acceptable for this generated-fixture authentication test; it is not independent authorization or provenance of a historical release.

The new encoding/json import is used. The map assertion matches JSON decoding into BackupManifest.Purpose (Object with interface-valued entries). Short declarations introduce new variables in the existing test scope; nil/error checks short-circuit safely. No obvious new Source-level compilation defect was identified. A real compiler has not been run.

## Reuse and exact scope

The original independent H20 Source review is reused. Its production findings and full-chain limitations are unchanged. Four production candidates are byte-equal to the original; the test is exactly invertible to the original after removing the encoding/json import and replacing only the original key-test block. All66 baseline Source pins and the prior review inputs were reverified. The generic cancellation test is intentionally unchanged, and five test parents remain.

Failure906 is preserved with actual outer/Python exit1 and nativeNULL. The old failed checker and its closed guard remain pinned. The subsequent checker correction has one exact inverse replacement which scopes absence checking to the first test. This review does not rerun either constructor.

## Remaining gates

Root must compile and run the scoped tests in an isolated qualified environment. Public synthetic test data and placeholder program bytes do not establish real historical Owner authentication, release qualification, native source locks or cutover readiness. Active-Run/effect/workspace/protected-service runtime coverage gaps disclosed by the original submission remain. The explicit session transition and complete20-to24 route remain OPEN.

No Go, SQL, native product, Git, private-key or model call was executed here. No current canonical guard was held; no Main, candidate or prior receipt was edited. New independent namespace only. No new mechanical failures; upstream903 and906 remain historical facts, not repeated attempts. Final source guard was reverified and released. STOP/FINAL.

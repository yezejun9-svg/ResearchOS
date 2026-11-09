# H20R2 test-only Source correction

SOURCE_FIXED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_RUNTIME. The Root actual 914 JSONL records nine test terminals: eight PASS and one FAIL. The public upgrade failed UPGRADE_PATH_OVERLAP because the old fixture placed source.sqlite and recovery.key in the same parent. The old four drift leaves accepted any error, so their PASS cannot establish their intended rejection cause. Old evidence remains unchanged.

Only backup_history20_upgrade_test.go changes. Source is now base/source/source.sqlite and KeyFile base/key/recovery.key; both parents are created before writes. Snapshot base/backup and Destination base/candidate remain siblings. The production upgradePaths overlap guard is preserved byte-for-byte.

The four drift leaves require exact current Source errors: migration-hash = UPGRADE_RELEASE_HASH: 0021_research_pending_windows.sql; extra-numbered-migration = UPGRADE_RELEASE_MIGRATIONS: require exact 1..20; foreign-table and session-addon = UPGRADE_SOURCE_SCHEMA. UPGRADE_PATH_OVERLAP or another early error fails these tests. Their existing destination/snapshot-not-published and full logical source-row equality checks remain.

The generic RestoreBackup cancellation test requires callbackCalled and errors.Is(err, context.Canceled), then unpublished destination, retained backup directory plus byte-identical backup manifest, and identical full logical source rows. Its comment explicitly scopes this as an independent generic RestoreBackup component test. It is not evidence for a public UpgradeLocal failure path.

The entire R1 public positive test block, including matching localUpgradeFormat/purpose readBackupPolicy, correct-key authenticated database/migration validation and wrong-key BACKUP_MANIFEST_INVALID assertion, is byte-identical. Four production candidates are byte-identical to R1, and all 66 original baseline pins remain unchanged. Nine exact text edits have a full inverse proving byte-for-byte recovery of the 9,082-byte R1 test; the unified patch is retained. Five parent test names and four child leaf names are unchanged, preserving nine terminal tests.

Source-only construction and inverse/provenance controls passed (outer/Python 0, success marker H20R2_SOURCE_CONSTRUCT_OK; native exit NULL). No Go, gofmt, SQL, Git, historical binary, native API, private input, model or paid trial ran here. No new failure origin occurred in this R2 task; Parent's 914 real run and 915 earlier archive-document parsing origin are not recounted. Last observed Parent next is 916, read-only.

Root must construct a fresh isolated 61-file composition with these R2 refs and new worktree/ENV/output locations, obtain independent Source review, and run formatting/list/tag compilation plus the unchanged five-parent/four-leaf test contract. This packet intentionally supplies the test Source first; it does not modify or reuse the already-occupied old validator workspace, caller, output or 914 evidence. Full historical 20-to24 compatibility, real historical program identity, Owner authorization, public-upgrade failure behavior and cutover remain outside this Source result.


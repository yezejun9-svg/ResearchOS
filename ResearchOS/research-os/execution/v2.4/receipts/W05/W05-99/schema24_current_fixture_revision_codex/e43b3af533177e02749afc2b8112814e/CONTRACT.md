# Schema24 current fixture Source revision

Status: SOURCE_IMPLEMENTED_PENDING_ROOT_TESTS_AND_INDEPENDENT_REVIEW.
Execution authority: NONE. This package contains only three complete Go test Source files. It does not change production behavior or the running T3 composition.

The exact T3 source is the only code base. base-refs.json captures all three original SHA256/byte pins; source-refs.json captures their complete candidate pins. revision.patch is the minimal delta.

- TestClientQueueFreshNumberedSchema validates the exact current release with preparedUpgradeRelease("../..", 24), 25 SQL entries including the final separately pinned additive input, and thus 24 numbered migrations. The original contiguous numbering/count/max assertions, empty client queue checks, SQL22 file check, and complete historical numbered22 test remain.
- TestClientConfigurationFreshAndNumberedMigration changes only actual_Service_New's expected current version from 23 to 24. Both numbered22_additive_false/true migration branches and all existing preservation assertions remain byte identical.
- TestHandlerRejectedSessionPublicBackupReplay keeps its original parent name and adds current24 and historical23 subcases. Both invoke a shared helper containing the complete original public API/backup/restore/replay/rebackup body. current24 uses setup(t). historical23 uses configurationUpgradeReleaseFixture(t, 23) and production New through setupWithConstructor with that fixed root's contracts and numbered inventory. Both RestoreOptions policies use the explicit test version, never values derived from a backup manifest. All original 201-configuration, bounded 100-status, unknown session, foreign project, original rejected/raw/session replay, isolated workspace, and rebackup assertions remain.

The complete original PublicReplay body is statically compared after reversing its single supported-version parameter substitution. The numbered22/current fresh boundaries and all non-target bytes are checked in construct_source.py. static-evidence.json records those exact author checks.

No Go, SQL, native, Git, provider, original database, private credential, or canonical action is executed by this Source task. Root must compose into a new isolated test root, run format/build and the focused parent tests plus the necessary existing regression suite, and have another agent independently review both the Source delta and closed actual receipts. The historical23 subcase establishes a production New/current-public-API test over a fixed historical schema; it does not claim frozen historical binary or real native acceptance.

No failure counter is reset. The already observed failures and prior receipts remain the responsibility of Root.


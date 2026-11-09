package recoveryauthority

const PauseMigrationPurpose = "RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1"
const PauseMigrationPlanID = "schema24-to25-runtime-pause-v1"
const PauseMigrationSQLSHA256 = "sha256:6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0"
const PauseMigrationArgument = "--private-pause-schema24-to25"

// Descriptors are private, fixed protocol definitions. Callers cannot choose a
// purpose, SQL hash, version, argument, grant file or replay journal.
type migrationDescriptor struct {
	purpose, plan, sql, schema, argument, grantFile, nonceDirectory string
	extraRoles                                                      []string
}

var preparedMigrationDescriptor = migrationDescriptor{
	purpose: MigrationPurpose, plan: MigrationPlanID, sql: MigrationSQLSHA256,
	schema: "researchos.recovery-migration-grant.v1", argument: MigrationArgument,
	grantFile: "current-schema23-to24-grant.json", nonceDirectory: "consumed-schema23-to24-grants",
}
var pauseMigrationDescriptor = migrationDescriptor{
	purpose: PauseMigrationPurpose, plan: PauseMigrationPlanID, sql: PauseMigrationSQLSHA256,
	schema: "researchos.pause-schema-migration-grant.v1", argument: PauseMigrationArgument,
	grantFile: "current-schema24-to25-grant.json", nonceDirectory: "consumed-schema24-to25-grants",
	extraRoles: []string{"target-rehearsal-program", "handoff-binding", "backup-producer-stdout", "backup-producer-observation"},
}

func verifyPauseMigrationGrant(raw, releaseRaw []byte) (MigrationGrant, error) {
	return verifyMigrationGrantFor(raw, releaseRaw, pauseMigrationDescriptor)
}

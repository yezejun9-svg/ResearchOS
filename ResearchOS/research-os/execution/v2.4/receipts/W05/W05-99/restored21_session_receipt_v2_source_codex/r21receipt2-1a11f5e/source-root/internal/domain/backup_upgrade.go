package domain

// This coordinator preserves opaque references to one existing protected service.
// It does not back up, read, or revalidate the private payload behind those refs.
import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"time"

	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/internal/store"
)

const LocalUpgradePlan = "schema13-to14-remote-access-v1"
const FinalSchemaUpgradePlan = "schema13-to20-research-runtime-v1"
const localUpgradeFormat = "RESEARCHOS_SAME_HOST_UPGRADE_V1"
const upgradeServiceSID = "S-1-5-80-2827915021-3673354303-1056739677-2648886565-40618300"

// Exact release input bytes, not a caller supplied SQL script or version subset.
var upgradeMigrationHashes = map[string]string{
	"0001_bootstrap.sql":                    "sha256:bb87c889e31fd5412b49743d106679f783b6dd21d874fe29d82d18a729ce3dbc",
	"0002_domain.sql":                       "sha256:90d6c36100cbfaddf85c23f603b686336d161e43eeeed47c034ab85415b25db4",
	"0003_context.sql":                      "sha256:50aa1579e4233cbb64ac30777e27c55cba29bab7ee0cc221a677f9a420a7159a",
	"0004_sources.sql":                      "sha256:d40152642778d8ea4e21148fd6517bdc8bf4c2582a8d6212b8cfdf7a470dea06",
	"0005_runtime.sql":                      "sha256:f3b9cd4c03f101c22c47a4fd7ad72593babe69de9abcd8a1ee3056fa6c23ade5",
	"0006_orchestration.sql":                "sha256:cbc9ede2d2e46e1e68ac7120d2a99b29627f2e13b1fc82937e3ed13ac9b2317b",
	"0007_retrieval.sql":                    "sha256:eaa3963a3acdfcc1791982432c42dea9d4dd8f0baf7de51d278fce70bcd626bb",
	"0008_artifact_uses.sql":                "sha256:adf17ad69203f0e700897a426f2d596496081bd5f3a964cbea8e3db9fc561ee7",
	"0009_retrieval_root_identity.sql":      "sha256:48219da409abc3f9d353e8d91a71a387ea342e5c13aae711a36c28410b22fb4f",
	"0010_experiments.sql":                  "sha256:c197ff792f62a1be5903bb6967175512cb53bdb09ff276e06fa8542822024287",
	"0011_resources.sql":                    "sha256:45c082ae0980af14f5b0be2d5aae02622dcc15c8c566b442077b4c1fb0c9942b",
	"0012_experiment_execution.sql":         "sha256:c81411769ef2bd3ec1d101f311ce37722036485b8e9d99d45ae9c9be48f088c0",
	"0013_research_cycles.sql":              "sha256:188e0d6fbcffd3901d36109dcd421a21f7ef704574f62cd5c0f8af862c191d1e",
	"0014_remote_access.sql":                "sha256:687b01552260301a8f3f39e92422f16d0b2e310b38f77d1b025566f9a9cfa4d7",
	"0015_evolution_fixture.sql":            "sha256:d70dd0580e89e2a7940c90ee771b2bd94551a42d8cda7fadfe83b60509852fe9",
	"0016_runtime_qualification.sql":        "sha256:7fd44c42be4c0753c367fc8361e9990b56e4f9a001a5f443ef62d0d87d05a03f",
	"0017_runtime_dispatch.sql":             "sha256:e5a2671c25725205bb5306c7fcbab254d53e3ef7a0448a163a41c5ac24a7b558",
	"0018_intent_planning.sql":              "sha256:7592b2b47d2e305f9ec26937830b5c0606c7d90622401a0b6b80a8c8a67db4e0",
	"0019_evolution_release_operations.sql": "sha256:54ff6eb7a7ca588df738f5bd68b6f6851d86916cef435abaac15d1f8bd6e131e",
	"0020_research_cycle_work.sql":          "sha256:3f90bdb0e828cec90bc370f34abed0cf0629dc78dcc01dda250c18cda49e528a",
}

type LocalUpgradeOptions struct {
	Source, Snapshot, Destination, KeyFile string
	SourceRoot, TargetRoot                 string
	SourceProgram, TargetProgram           string
	Plan                                   string
}

// Public callers cannot replace the concrete authenticated LIVE service with a
// JSON declaration, environment switch, fake Provider, or an arbitrary callback.
func UpgradeLocal(ctx context.Context, opt LocalUpgradeOptions) (RestoreReport, error) {
	return upgradeLocal(ctx, opt, upgradeVerifier{
		provider: &protectedstore.FrozenProvider{},
		summary: func(ctx context.Context) (protectedstore.SafeSummary, error) {
			if e := ctx.Err(); e != nil {
				return protectedstore.SafeSummary{}, e
			}
			return protectedstore.QueryFrozenService("aggregate")
		},
	})
}

type upgradeVerifier struct {
	provider protectedstore.Provider
	summary  func(context.Context) (protectedstore.SafeSummary, error)
}

func upgradeVersions(n int) []int {
	versions := make([]int, n)
	for i := range versions {
		versions[i] = i + 1
	}
	return versions
}

// Resolve an existing ancestor too: a nonexisting child of a junction/symlink is
// still an alias. Existing outputs are refused, including dangling symlinks.
func upgradePath(path string, existing bool) (string, error) {
	if path == "" || strings.ContainsAny(path, "?\x00") {
		return "", fmt.Errorf("UPGRADE_PATH_REQUIRED")
	}
	abs, e := filepath.Abs(path)
	if e != nil {
		return "", e
	}
	if existing {
		return upgradeExistingPath(abs)
	}
	if _, e = os.Lstat(abs); !os.IsNotExist(e) {
		return "", fmt.Errorf("DESTINATION_EXISTS")
	}
	ancestor := filepath.Dir(abs)
	for {
		resolved, err := upgradeExistingPath(ancestor)
		if err == nil {
			rel, err := filepath.Rel(ancestor, abs)
			if err != nil || !filepath.IsLocal(rel) {
				return "", fmt.Errorf("UPGRADE_PATH_INVALID")
			}
			return filepath.Join(resolved, rel), nil
		}
		if !os.IsNotExist(err) || filepath.Dir(ancestor) == ancestor {
			return "", err
		}
		ancestor = filepath.Dir(ancestor)
	}
}
func upgradeInside(parent, child string) bool {
	rel, e := filepath.Rel(parent, child)
	return e == nil && (rel == "." || filepath.IsLocal(rel))
}
func upgradePaths(opt *LocalUpgradeOptions) error {
	for _, p := range []*string{&opt.Source, &opt.KeyFile, &opt.SourceRoot, &opt.TargetRoot, &opt.SourceProgram, &opt.TargetProgram} {
		v, e := upgradePath(*p, true)
		if e != nil {
			return e
		}
		*p = v
	}
	for _, p := range []*string{&opt.Snapshot, &opt.Destination} {
		v, e := upgradePath(*p, false)
		if e != nil {
			return e
		}
		*p = v
	}
	dirs := []string{filepath.Dir(opt.Source), filepath.Dir(opt.KeyFile), opt.Snapshot, opt.Destination}
	for i, a := range dirs {
		for _, b := range dirs[i+1:] {
			if upgradeInside(a, b) || upgradeInside(b, a) {
				return fmt.Errorf("UPGRADE_PATH_OVERLAP: source, key, snapshot and target require separate directories")
			}
		}
	}
	var infos []os.FileInfo
	for _, p := range []string{opt.Source, opt.KeyFile, opt.SourceProgram, opt.TargetProgram} {
		info, e := os.Stat(p)
		if e != nil || !info.Mode().IsRegular() {
			return fmt.Errorf("UPGRADE_REGULAR_FILE_REQUIRED")
		}
		infos = append(infos, info)
	}
	for i := 1; i < len(infos); i++ {
		if os.SameFile(infos[0], infos[i]) || (i > 1 && os.SameFile(infos[1], infos[i])) {
			return fmt.Errorf("UPGRADE_FILE_ALIAS")
		}
	}
	return nil
}

func upgradeRelease(root string, count int) (Object, [][]byte, error) {
	if count != 13 && count != 14 && count != 20 {
		return nil, nil, fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	files, e := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql")) // release inputs are the numbered migrations only; unnumbered additive files (e.g. next_v24_sessions.sql) are applied through their own single-transaction path
	if e != nil || len(files) != count {
		return nil, nil, fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS: require exact 1..%d", count)
	}
	manifest := Object{}
	sqls := make([][]byte, count)
	for i, file := range files {
		name := filepath.Base(file)
		if len(name) < 5 || name[:4] != fmt.Sprintf("%04d", i+1) {
			return nil, nil, fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS")
		}
		raw, e := os.ReadFile(file)
		if e != nil || Digest(raw) != upgradeMigrationHashes[name] {
			return nil, nil, fmt.Errorf("UPGRADE_RELEASE_HASH: %s", name)
		}
		manifest["migrations/sqlite/"+name] = Digest(raw)
		sqls[i] = raw
	}
	for name, expected := range map[string]string{
		"domain.schema.json": "sha256:b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847",
		"openapi.json":       "sha256:f1edd7955a1d134a675c5558618756db809d82729f8eebe622a9bc2605a58920",
	} {
		raw, e := os.ReadFile(filepath.Join(root, "spec/v2.0/contracts", name))
		if e != nil || Digest(raw) != expected {
			return nil, nil, fmt.Errorf("UPGRADE_CONTRACT_HASH: %s", name)
		}
		manifest["spec/v2.0/contracts/"+name] = expected
	}
	return manifest, sqls, nil
}

func upgradeOpenExclusive(ctx context.Context, path string) (*sql.DB, error) {
	db, e := store.Open(path)
	if e != nil {
		return nil, e
	}
	// locking_mode=EXCLUSIVE keeps the native SQLite lock after ROLLBACK,
	// permitting VACUUM INTO on this same connection outside a transaction.
	// A second process with an open WAL reader or writer causes a bounded failure.
	_, e = db.ExecContext(ctx, "PRAGMA busy_timeout=250; PRAGMA locking_mode=EXCLUSIVE; BEGIN EXCLUSIVE; ROLLBACK;")
	if e != nil {
		db.Close()
		return nil, fmt.Errorf("UPGRADE_SOURCE_NOT_OFFLINE: %w", e)
	}
	return db, nil
}

func upgradeTemplate(ctx context.Context, sqls [][]byte, contracts *Contracts) (string, string, error) {
	stage, e := os.MkdirTemp("", ".researchos-backup-stage-")
	if e != nil {
		return "", "", e
	}
	defer backupDiscard(stage)
	db, e := store.Open(filepath.Join(stage, "schema.sqlite"))
	if e != nil {
		return "", "", e
	}
	defer db.Close()
	for i, raw := range sqls[:13] {
		if _, e = db.ExecContext(ctx, string(raw)); e != nil {
			return "", "", e
		}
		if _, e = db.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", i+1); e != nil {
			return "", "", e
		}
	}
	before, e := backupSchema(db)
	if e != nil {
		return "", "", e
	}
	if _, e = (&Service{DB: db, Contracts: contracts}).backupFence(ctx); e != nil {
		return "", "", e
	}
	for _, raw := range sqls[13:] {
		if _, e = db.ExecContext(ctx, string(raw)); e != nil {
			return "", "", e
		}
	}
	after, e := backupSchema(db)
	return before, after, e
}

func upgradeLocal(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (RestoreReport, error) {
	if opt.Plan == Restored21SessionUpgradePlan {
		return upgradeRestored21Local(ctx, opt, verifier)
	}
	if opt.Plan == History20SchemaUpgradePlan {
		return upgradeHistory20Local(ctx, opt, verifier)
	}
	if opt.Plan == PreparedAbandonmentSchemaUpgradePlan {
		return upgradePreparedAbandonmentLocal(ctx, opt, verifier)
	}
	if opt.Plan == ConfigurationSchemaUpgradePlan {
		return upgradeConfigurationLocal(ctx, opt, verifier)
	}
	if opt.Plan == QueueSchemaUpgradePlan {
		return upgradeQueueLocal(ctx, opt, verifier)
	}
	report := RestoreReport{Started: Now(), Status: "FAILED"}
	targetVersion := 14
	switch opt.Plan {
	case LocalUpgradePlan:
	case FinalSchemaUpgradePlan:
		targetVersion = 20
	default:
		return report, fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	if e := upgradePaths(&opt); e != nil {
		return report, e
	}
	sourceRelease, _, e := upgradeRelease(opt.SourceRoot, 13)
	if e != nil {
		return report, e
	}
	targetRelease, sqls, e := upgradeRelease(opt.TargetRoot, targetVersion)
	if e != nil {
		return report, e
	}
	contracts, e := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
	if e != nil {
		return report, e
	}
	expectedSourceSchema, expectedTargetSchema, e := upgradeTemplate(ctx, sqls, contracts)
	if e != nil {
		return report, e
	}
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil || len(key) != 32 {
		return report, fmt.Errorf("BACKUP_KEY_UNAVAILABLE")
	}
	defer clear(key)
	db, e := upgradeOpenExclusive(ctx, opt.Source)
	if e != nil {
		return report, e
	}
	defer db.Close() // The native source lock spans snapshot through publication.
	versions, e := backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(13)) {
		return report, fmt.Errorf("UPGRADE_SOURCE_VERSION: require exact 1..13")
	}
	schema, e := backupSchema(db)
	if e != nil || schema != expectedSourceSchema {
		return report, fmt.Errorf("UPGRADE_SOURCE_SCHEMA")
	}
	guard := &upgradeProtection{ctx: ctx, verifier: verifier}
	if e = guard.refresh(db); e != nil {
		return report, e
	}
	// Reject any host-side protected storage before reading ordinary BLOB rows
	// for the logical inventory or creating a snapshot.
	original, e := upgradeRows(db)
	if e != nil {
		return report, e
	}
	programHashes := Object{}
	for name, path := range map[string]string{"source": opt.SourceProgram, "target": opt.TargetProgram} {
		raw, e := os.ReadFile(path)
		if e != nil {
			return report, e
		}
		programHashes[name] = Digest(raw)
	}
	host, e := os.Hostname()
	if e != nil || host == "" {
		return report, fmt.Errorf("UPGRADE_HOST_UNAVAILABLE")
	}
	plan := Object{"id": opt.Plan, "source_versions": versions, "target_versions": upgradeVersions(targetVersion),
		"source_schema_hash": schema, "target_schema_with_restore_fence_hash": expectedTargetSchema,
		"source_release_hash": Hash(sourceRelease), "target_release_hash": Hash(targetRelease),
		"migration_sql_hash": Digest(sqls[13]), "source_database_logical_hash": Hash(original),
		"program_hashes": programHashes, "host_binding_hash": Hash(host), "service_summary_hash": guard.summaryHash,
		"source_path_hash": Hash(opt.Source), "target_path_hash": Hash(opt.Destination)}
	if targetVersion == 20 {
		delete(plan, "migration_sql_hash")
		plan["migration_sql_hashes"] = upgradeFinalSQLManifest()
	}
	purpose := Object{"kind": "SAME_HOST_CONTROL_PLANE_UPGRADE", "scope": "SameHostExternalReferenceContinuityOnly",
		"plan": plan, "plan_hash": Hash(plan), "protected_reference_versions": guard.count,
		"protected_reference_digest": guard.referencesHash, "protected_payloads_included": false,
		"protected_payloads_revalidated": false, "recovery_dependency": "ORIGINAL_PROTECTED_SERVICE",
		"external_actions_dispatched": 0, "source_ownership": "SQLITE_EXCLUSIVE_UNTIL_TARGET_PUBLICATION",
		"cutover_requirement": "Keep original application and workers stopped until independent review and single-writer cutover; do not run both authorities."}
	policy := &backupPolicy{format: localUpgradeFormat, databaseName: "researchos.sqlite", purpose: purpose, validate: guard.refresh, allowProtected: guard.artifact}
	policy.beforeRecovery = func(restored *sql.DB) error {
		rows, e := upgradeRows(restored)
		if e != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("UPGRADE_SNAPSHOT_HISTORY_MISMATCH")
		}
		return nil
	}
	policy.afterRecovery = func(restored *sql.DB) error {
		currentSchema, e := backupSchema(restored)
		if e != nil || currentSchema != expectedTargetSchema {
			return fmt.Errorf("UPGRADE_TARGET_SCHEMA")
		}
		rows, e := upgradeRows(restored)
		if e != nil {
			return e
		}
		if e = upgradeRecoveryInvariantForTarget(original, rows, opt.Destination, targetVersion); e != nil {
			return e
		}
		sourceNow, e := upgradeRows(db)
		if e != nil || Hash(sourceNow) != Hash(original) {
			return fmt.Errorf("UPGRADE_SOURCE_DRIFT")
		}
		// Release roots and binary files must not change during the operation.
		for _, entry := range []struct {
			root string
			n    int
			hash string
		}{
			{opt.SourceRoot, 13, Hash(sourceRelease)}, {opt.TargetRoot, targetVersion, Hash(targetRelease)},
		} {
			current, _, err := upgradeRelease(entry.root, entry.n)
			if err != nil || Hash(current) != entry.hash {
				return fmt.Errorf("UPGRADE_RELEASE_CHANGED")
			}
		}
		for name, path := range map[string]string{"source": opt.SourceProgram, "target": opt.TargetProgram} {
			raw, err := os.ReadFile(path)
			if err != nil || Digest(raw) != programHashes[name] {
				return fmt.Errorf("UPGRADE_PROGRAM_CHANGED")
			}
		}
		return ctx.Err()
	}
	svc := &Service{DB: db, Contracts: contracts}
	if _, e = svc.createBackupPolicy(ctx, opt.Snapshot, key, policy); e != nil {
		return report, e
	}
	return restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination, RestoreOptions{
		Key: key, SupportedMigrations: versions, Contracts: contracts,
		Migration: func(ctx context.Context, target *sql.DB) error {
			if targetVersion == 20 {
				return upgradeFinalMigration(ctx, target, sqls[13:])
			}
			return upgradeMigration(ctx, target, sqls[13])
		},
	}, policy)
}

func upgradeMigration(ctx context.Context, db *sql.DB, raw []byte) error {
	if Digest(raw) != upgradeMigrationHashes["0014_remote_access.sql"] {
		return fmt.Errorf("UPGRADE_MIGRATION_HASH")
	}
	before, e := upgradeRows(db)
	if e != nil {
		return e
	}
	tx, e := db.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if _, e = tx.ExecContext(ctx, string(raw)); e != nil {
		return e
	}
	if _, e = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(14)"); e != nil {
		return e
	}
	if e = tx.Commit(); e != nil {
		return e
	}
	after, e := upgradeRows(db)
	if e != nil {
		return e
	}
	for name, rows := range before {
		if name != "schema_migrations" && Hash(rows) != Hash(after[name]) {
			return fmt.Errorf("UPGRADE_MIGRATION_MUTATED_HISTORY: %s", name)
		}
	}
	versions, e := backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(14)) {
		return fmt.Errorf("UPGRADE_TARGET_VERSION")
	}
	for _, name := range []string{"remote_challenges", "remote_devices", "remote_refresh", "remote_replays", "remote_audit"} {
		if rows, exists := after[name]; !exists || len(rows) != 0 {
			return fmt.Errorf("UPGRADE_REMOTE_TABLE_NOT_EMPTY")
		}
	}
	return nil
}

type upgradeProtection struct {
	ctx            context.Context
	verifier       upgradeVerifier
	initialized    bool
	summaryHash    string
	referencesHash string
	count          int
	descriptors    map[string]protectedstore.Blob
}

func (g *upgradeProtection) refresh(db *sql.DB) error {
	var opaqueHostContent int
	if e := db.QueryRow("SELECT count(*) FROM uploaded_content WHERE storage_key GLOB 'ps1:*'").Scan(&opaqueHostContent); e != nil || opaqueHostContent != 0 {
		return fmt.Errorf("UPGRADE_PROTECTED_HOST_CONTENT_PROHIBITED")
	}
	var broken int
	if e := db.QueryRow(`SELECT count(*) FROM domain_objects o LEFT JOIN domain_versions v
ON v.project=o.project AND v.kind=o.kind AND v.id=o.id AND v.revision=o.revision
WHERE v.id IS NULL OR v.body!=o.body OR v.content_hash IS NOT o.content_hash`).Scan(&broken); e != nil || broken != 0 {
		return fmt.Errorf("UPGRADE_CURRENT_HISTORY_BINDING")
	}
	artifacts, e := backupObjects(db, "SELECT body FROM domain_versions WHERE kind='Artifact' AND json_extract(body,'$.access_class')!='PROJECT' ORDER BY project,id,revision")
	if e != nil {
		return e
	}
	refsHash := Hash(artifacts)
	if g.initialized && (g.count != len(artifacts) || g.referencesHash != refsHash) {
		return fmt.Errorf("UPGRADE_PROTECTED_HISTORY_CHANGED")
	}
	g.count, g.referencesHash = len(artifacts), refsHash
	g.descriptors = map[string]protectedstore.Blob{}
	if len(artifacts) == 0 {
		g.initialized = true
		return nil
	}
	if g.verifier.provider == nil || g.verifier.summary == nil {
		return fmt.Errorf("UPGRADE_PROTECTED_SERVICE_REQUIRED")
	}
	if e = g.verifier.provider.Ready(g.ctx, "LIVE"); e != nil {
		return fmt.Errorf("UPGRADE_PROTECTED_READY: %w", e)
	}
	boundary, e := g.verifier.provider.Boundary(g.ctx)
	if e != nil || boundary.Mode != "INDEPENDENT_VERIFIER" || boundary.OwnerSID != upgradeServiceSID || !boundary.IndependentIdentity || boundary.UnrestrictedSameUserCanRead {
		return fmt.Errorf("UPGRADE_PROTECTED_BOUNDARY")
	}
	summary, e := g.verifier.summary(g.ctx)
	if e != nil || summary.Validate() != nil || summary.Frozen == nil || summary.Frozen.RunState != "COMPLETED" || summary.Frozen.Dataset == nil || summary.MaximumMode != "ADVISORY" || summary.Frozen.AutomaticAuthority != "NONE" {
		return fmt.Errorf("UPGRADE_PROTECTED_TERMINAL")
	}
	if g.initialized && g.summaryHash != Hash(summary) {
		return fmt.Errorf("UPGRADE_PROTECTED_SERVICE_CHANGED")
	}
	g.summaryHash = Hash(summary)
	for _, artifact := range artifacts {
		project, ticket := Str(artifact, "project_id"), Str(artifact, "storage_key")
		key := project + "/" + ticket
		if _, ok := g.descriptors[key]; !ok {
			descriptor, err := g.verifier.provider.Describe(g.ctx, project, ticket)
			expected := *summary.Frozen.Dataset
			expected.Project = project
			if err != nil || descriptor != expected || !descriptor.Valid() {
				return fmt.Errorf("UPGRADE_PROTECTED_DESCRIPTOR")
			}
			g.descriptors[key] = descriptor
		}
		if e = g.artifact(db, artifact); e != nil {
			return e
		}
	}
	if e = upgradeQualifications(db, summary); e != nil {
		return e
	}
	g.initialized = true
	return nil
}

func (g *upgradeProtection) artifact(db *sql.DB, artifact Object) error {
	project, ticket := Str(artifact, "project_id"), Str(artifact, "storage_key")
	descriptor, ok := g.descriptors[project+"/"+ticket]
	if !ok || artifact["access_class"] != "VERIFIER_ONLY" || artifact["measurement_mode"] != "LIVE" ||
		!protectedstore.ValidTicket(ticket) || artifact["content_hash"] != descriptor.Hash ||
		Hash(artifact["byte_size"]) != Hash(descriptor.Size) || artifact["media_type"] != descriptor.MediaType {
		return fmt.Errorf("UPGRADE_PROTECTED_REFERENCE_INVALID")
	}
	var hostCopies int
	if e := db.QueryRow("SELECT count(*) FROM uploaded_content WHERE storage_key=?", ticket).Scan(&hostCopies); e != nil || hostCopies != 0 {
		return fmt.Errorf("UPGRADE_PROTECTED_HOST_CONTENT_PROHIBITED")
	}
	return nil
}

func upgradeVersion(db *sql.DB, project, kind string, ref Object) (Object, error) {
	if ref["entity_type"] != kind {
		return nil, fmt.Errorf("UPGRADE_QUALIFICATION_REFERENCE")
	}
	var body string
	if e := db.QueryRow("SELECT body FROM domain_versions WHERE project=? AND kind=? AND id=? AND revision=?", project, kind, ref["id"], ref["revision"]).Scan(&body); e != nil {
		return nil, e
	}
	object, e := Decode([]byte(body))
	if e != nil || Hash(Ref(object, kind)) != Hash(ref) {
		return nil, fmt.Errorf("UPGRADE_QUALIFICATION_REFERENCE")
	}
	return object, nil
}

func upgradeQualifications(db *sql.DB, summary protectedstore.SafeSummary) error {
	qualifications, e := backupObjects(db, "SELECT body FROM domain_versions WHERE kind='Qualification' AND json_extract(body,'$.measurement_mode')='LIVE'")
	if e != nil {
		return e
	}
	for _, q := range qualifications {
		authors := map[string]bool{}
		f := summary.Frozen
		if q["label_basis"] != "OBJECTIVE" || q["thresholds_hash"] != QualificationThresholdsHash() || q["thresholds_frozen_at"] != f.FrozenAt || q["maximum_mode"] != "ADVISORY" || (q["status"] != "DRAFT" && q["status"] != "FAILED") {
			return fmt.Errorf("UPGRADE_QUALIFICATION_BINDING")
		}
		var counts *protectedstore.FrozenKeyCounts
		for i := range f.Keys {
			if Hash(q["scope"]) == Hash(f.Keys[i].Scope) {
				counts = &f.Keys[i]
			}
		}
		if counts == nil || Hash(q["total_case_count"]) != Hash(counts.DevelopmentCount+counts.Planned) || Hash(q["holdout_case_count"]) != Hash(counts.Planned) {
			return fmt.Errorf("UPGRADE_QUALIFICATION_SCOPE")
		}
		for _, name := range []string{"dataset_artifact_ref", "holdout_artifact_ref"} {
			ref, ok := q[name].(map[string]any)
			if !ok {
				return fmt.Errorf("UPGRADE_QUALIFICATION_REFERENCE")
			}
			artifact, err := upgradeVersion(db, Str(q, "project_id"), "Artifact", ref)
			if err != nil {
				return err
			}
			authors[Str(artifact, "produced_by")] = true
			if name == "dataset_artifact_ref" {
				if artifact["access_class"] != "PROJECT" || artifact["content_hash"] != frozenDevelopmentDatasetHash {
					return fmt.Errorf("UPGRADE_QUALIFICATION_DEVELOPMENT")
				}
			} else if artifact["access_class"] != "VERIFIER_ONLY" || artifact["storage_key"] != f.Dataset.Ticket || artifact["content_hash"] != f.Dataset.Hash {
				return fmt.Errorf("UPGRADE_QUALIFICATION_HOLDOUT")
			}
		}
		if q["status"] == "DRAFT" {
			continue
		}
		if q["jev_called"] != true || Hash(q["critical_false_accept_count"]) != Hash(counts.CriticalFalseAccept) ||
			Hash(q["false_accept_rate"]) != Hash(float64(counts.FalseAccept)/float64(counts.Planned)) ||
			Hash(q["false_reject_rate"]) != Hash(float64(counts.FalseReject)/float64(counts.PositiveLabelCount)) ||
			Hash(q["abstain_rate"]) != Hash(float64(counts.Abstain)/float64(counts.Planned)) {
			return fmt.Errorf("UPGRADE_QUALIFICATION_RESULT")
		}
		var raw string
		if e = db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt' AND id=?", q["project_id"], q["acceptance_id"]).Scan(&raw); e != nil {
			return e
		}
		receipt, err := Decode([]byte(raw))
		if err != nil {
			return fmt.Errorf("UPGRADE_QUALIFICATION_ACCEPTANCE")
		}
		subject, ok := receipt["subject_ref"].(map[string]any)
		if !ok || subject["id"] != q["id"] {
			return fmt.Errorf("UPGRADE_QUALIFICATION_SUBJECT")
		}
		draft, err := upgradeVersion(db, Str(q, "project_id"), "Qualification", subject)
		if err != nil || draft["status"] != "DRAFT" || draft["project_id"] != q["project_id"] || qualificationContract(draft) != qualificationContract(q) {
			return fmt.Errorf("UPGRADE_QUALIFICATION_SUBJECT")
		}
		// recordQualificationResult only transitions this exact DRAFT once. Do
		// not compare the receipt to the later FAILED object or a current Ref.
		expected := copyObject(draft)
		for _, field := range []string{"status", "maximum_mode", "jev_called", "critical_false_accept_count", "false_accept_rate", "false_reject_rate", "abstain_rate", "test_receipt_refs", "acceptance_id"} {
			expected[field] = q[field]
		}
		if bump(expected) != nil {
			return fmt.Errorf("UPGRADE_QUALIFICATION_SUBJECT")
		}
		expected["updated_at"] = q["updated_at"]
		if Hash(expected) != Hash(q) {
			return fmt.Errorf("UPGRADE_QUALIFICATION_SUBJECT")
		}
		policy, err := upgradeAcceptancePolicy(db, Str(q, "project_id"), receipt)
		if err != nil {
			return err
		}
		authorIDs := make([]string, 0, len(authors))
		for id := range authors {
			authorIDs = append(authorIDs, id)
		}
		sort.Strings(authorIDs)
		actualAuthors := Empty()
		for _, id := range authorIDs {
			actualAuthors = append(actualAuthors, id)
		}
		if qualificationReceiptBinding(draft, receipt, actualAuthors, Str(receipt, "verifier_principal_id"), policy, q["test_receipt_refs"]) != nil {
			return fmt.Errorf("UPGRADE_QUALIFICATION_ACCEPTANCE")
		}
		ref, ok := Arr(receipt, "artifact_refs")[0].(map[string]any)
		if !ok {
			return fmt.Errorf("UPGRADE_QUALIFICATION_SUMMARY")
		}
		artifact, err := upgradeVersion(db, Str(q, "project_id"), "Artifact", ref)
		if err != nil || artifact["access_class"] != "PROJECT" || artifact["measurement_mode"] != "LIVE" || artifact["evidence_kind"] != "OBSERVED" || artifact["kind"] != "REPORT" || artifact["run_id"] != nil || artifact["produced_by"] != receipt["verifier_principal_id"] {
			return fmt.Errorf("UPGRADE_QUALIFICATION_SUMMARY")
		}
		// Preserved registration semantics, not a currently usable credential.
		var roles string
		var granted int
		principal := Principal{ID: Str(receipt, "verifier_principal_id")}
		if db.QueryRow("SELECT roles FROM auth_principals WHERE id=?", principal.ID).Scan(&roles) != nil || json.Unmarshal([]byte(roles), &principal.Roles) != nil || !principal.HasRole("VERIFIER") ||
			db.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=? AND task='' AND run='' AND restricted=1", principal.ID, q["project_id"]).Scan(&granted) != nil || granted != 1 {
			return fmt.Errorf("UPGRADE_QUALIFICATION_INDEPENDENCE")
		}
		var public []byte
		if e = db.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", q["project_id"], artifact["storage_key"]).Scan(&public); e != nil {
			return e
		}
		parsed, err := protectedstore.ParseSafeSummary(public)
		if err != nil || Hash(parsed) != Hash(summary) {
			return fmt.Errorf("UPGRADE_QUALIFICATION_SUMMARY")
		}
	}
	return nil
}

// Resolve the policy in force when the immutable receipt was written, never
// the current policy, which can legitimately change after qualification.
func upgradeAcceptancePolicy(db *sql.DB, project string, receipt Object) (any, error) {
	accepted, e := time.Parse(time.RFC3339Nano, Str(receipt, "created_at"))
	if e != nil {
		return nil, fmt.Errorf("UPGRADE_QUALIFICATION_POLICY")
	}
	rows, e := db.Query("SELECT body FROM domain_versions WHERE project=? AND kind='ProjectState' ORDER BY revision DESC", project)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			return nil, e
		}
		state, err := Decode([]byte(raw))
		if err != nil {
			return nil, err
		}
		stamp := Str(state, "updated_at")
		if stamp == "" {
			stamp = Str(state, "created_at")
		}
		when, err := time.Parse(time.RFC3339Nano, stamp)
		if err != nil {
			return nil, fmt.Errorf("UPGRADE_QUALIFICATION_POLICY")
		}
		if !when.After(accepted) {
			return state["policy_revision"], nil
		}
	}
	return nil, fmt.Errorf("UPGRADE_QUALIFICATION_POLICY")
}

// Only hashes/counts escape this in-memory control-plane inventory. Protected
// bodies never enter SQLite and no protected service Read operation is called.
type upgradeData map[string][]Object

func upgradeRows(db *sql.DB) (upgradeData, error) {
	rows, e := db.Query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
	if e != nil {
		return nil, e
	}
	tables := []string{}
	for rows.Next() {
		var name string
		if e = rows.Scan(&name); e != nil {
			rows.Close()
			return nil, e
		}
		tables = append(tables, name)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	result := upgradeData{}
	for _, name := range tables {
		rows, e = db.Query(`SELECT * FROM "` + strings.ReplaceAll(name, `"`, `""`) + `"`)
		if e != nil {
			return nil, e
		}
		cols, e := rows.Columns()
		if e != nil {
			rows.Close()
			return nil, e
		}
		entries := []Object{}
		for rows.Next() {
			values := make([]any, len(cols))
			pointers := make([]any, len(cols))
			for i := range values {
				pointers[i] = &values[i]
			}
			if e = rows.Scan(pointers...); e != nil {
				rows.Close()
				return nil, e
			}
			entry := Object{}
			for i, col := range cols {
				entry[col] = values[i]
			}
			entries = append(entries, entry)
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return nil, e
		}
		sort.Slice(entries, func(i, j int) bool { return Hash(entries[i]) < Hash(entries[j]) })
		result[name] = entries
	}
	return result, nil
}

func upgradeExtra(before, after []Object) ([]Object, error) {
	remaining := map[string]int{}
	for _, row := range before {
		remaining[Hash(row)]++
	}
	extra := []Object{}
	for _, row := range after {
		h := Hash(row)
		if remaining[h] > 0 {
			remaining[h]--
		} else {
			extra = append(extra, row)
		}
	}
	for _, n := range remaining {
		if n != 0 {
			return nil, fmt.Errorf("UPGRADE_HISTORY_REMOVED_OR_CHANGED")
		}
	}
	return extra, nil
}

func upgradeObjectKey(row Object) string {
	return Str(row, "project") + "/" + Str(row, "kind") + "/" + Str(row, "id")
}
func upgradeWithout(row Object, names ...string) Object {
	result := copyObject(row)
	for _, name := range names {
		delete(result, name)
	}
	return result
}

func upgradeRecoveryInvariant(before, after upgradeData, destination string) error {
	return upgradeRecoveryInvariantForTarget(before, after, destination, 14)
}

func upgradeRecoveryInvariantForTarget(before, after upgradeData, destination string, target int) error {
	if target != 14 && target != 20 {
		return fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	if target == 20 {
		projected, e := upgradeFinalProjection(before, after)
		if e != nil {
			return e
		}
		after = projected
	}
	active := map[string]Object{}
	projectRuns := map[string]int64{}
	oldObjects, newObjects := map[string]Object{}, map[string]Object{}
	for _, row := range before["domain_objects"] {
		oldObjects[upgradeObjectKey(row)] = row
		if row["kind"] == "Run" {
			body, e := Decode([]byte(Str(row, "body")))
			if e != nil {
				return e
			}
			if strings.Contains("|QUEUED|STARTING|RUNNING|CANCEL_REQUESTED|RECONCILING|LOST|", "|"+Str(body, "status")+"|") {
				active[upgradeObjectKey(row)] = body
				projectRuns[Str(row, "project")]++
			}
		}
	}
	for _, row := range after["domain_objects"] {
		newObjects[upgradeObjectKey(row)] = row
	}
	newEvents := map[string]bool{}
	for key, old := range oldObjects {
		current, ok := newObjects[key]
		if !ok {
			return fmt.Errorf("UPGRADE_CURRENT_OBJECT_LOST")
		}
		body, e := Decode([]byte(Str(current, "body")))
		if e != nil {
			return e
		}
		prior, e := Decode([]byte(Str(old, "body")))
		if e != nil {
			return e
		}
		if run, ok := active[key]; ok {
			status := "RECONCILING"
			if run["status"] == "CANCEL_REQUESTED" {
				status = "CANCEL_REQUESTED"
			}
			oldRev, _ := Num(prior, "revision")
			newRev, _ := Num(body, "revision")
			fields := []string{"status", "lease_token_hash", "lease_expires_at", "revision", "updated_at"}
			if newRev != oldRev+1 || body["status"] != status || body["lease_expires_at"] != "1970-01-01T00:00:00Z" || body["lease_token_hash"] == prior["lease_token_hash"] || Hash(upgradeWithout(body, fields...)) != Hash(upgradeWithout(prior, fields...)) {
				return fmt.Errorf("UPGRADE_RUN_FENCE_INVALID")
			}
		} else if old["kind"] == "ProjectState" && projectRuns[Str(old, "project")] != 0 {
			n := projectRuns[Str(old, "project")]
			for _, field := range []string{"revision", "event_sequence"} {
				a, _ := Num(prior, field)
				b, _ := Num(body, field)
				if b != a+n {
					return fmt.Errorf("UPGRADE_STATE_AUDIT_INVALID")
				}
			}
			if Hash(upgradeWithout(body, "revision", "updated_at", "event_sequence")) != Hash(upgradeWithout(prior, "revision", "updated_at", "event_sequence")) {
				return fmt.Errorf("UPGRADE_STATE_MUTATED")
			}
		} else if Hash(current) != Hash(old) {
			return fmt.Errorf("UPGRADE_CURRENT_OBJECT_MUTATED: %s", Str(old, "kind"))
		}
	}
	for key, row := range newObjects {
		if _, existed := oldObjects[key]; existed {
			continue
		}
		body, e := Decode([]byte(Str(row, "body")))
		if e != nil || row["kind"] != "EventEnvelope" || body["actor_id"] != "restore-local-admin" || body["event_type"] != "RUN_CHANGED" {
			return fmt.Errorf("UPGRADE_UNEXPECTED_NEW_OBJECT")
		}
		ref, ok := body["aggregate_ref"].(map[string]any)
		if !ok || active[Str(row, "project")+"/Run/"+Str(ref, "id")] == nil {
			return fmt.Errorf("UPGRADE_UNEXPECTED_AUDIT_EVENT")
		}
		newEvents[Str(row, "id")] = true
	}
	if len(newEvents) != len(active) {
		return fmt.Errorf("UPGRADE_AUDIT_EVENT_COUNT")
	}
	for table, old := range before {
		current, exists := after[table]
		if !exists {
			return fmt.Errorf("UPGRADE_TABLE_LOST")
		}
		switch table {
		case "domain_objects": // Checked by exact identity and restricted changes above.
		case "domain_versions", "domain_refs", "outbox", "event_state_snapshots":
			extra, e := upgradeExtra(old, current)
			if e != nil {
				return e
			}
			if (table == "domain_versions" && len(extra) != 3*len(active)) || ((table == "outbox" || table == "event_state_snapshots") && len(extra) != len(active)) {
				return fmt.Errorf("UPGRADE_AUDIT_HISTORY_COUNT")
			}
			for _, row := range extra {
				if table == "outbox" || table == "event_state_snapshots" {
					id := Str(row, "id")
					if table == "event_state_snapshots" {
						id = Str(row, "event_id")
					}
					if !newEvents[id] {
						return fmt.Errorf("UPGRADE_UNKNOWN_EVENT_HISTORY")
					}
				} else if !(row["kind"] == "Run" && active[upgradeObjectKey(row)] != nil) && !(row["kind"] == "ProjectState" && projectRuns[Str(row, "project")] > 0) && !(row["kind"] == "EventEnvelope" && newEvents[Str(row, "id")]) {
					return fmt.Errorf("UPGRADE_UNKNOWN_DOMAIN_HISTORY")
				}
			}
		case "resource_effects":
			if e := upgradeEffects(old, current); e != nil {
				return e
			}
		case "auth_credentials":
			expected := make([]Object, len(old))
			for i, row := range old {
				expected[i] = Merge(copyObject(row), Object{"revoked": int64(1)})
			}
			extra, e := upgradeExtra(expected, current)
			if e != nil || len(extra) != 0 {
				return fmt.Errorf("UPGRADE_CREDENTIAL_FENCE")
			}
		case "retrieval_roots":
			strip := func(rows []Object) []Object {
				result := make([]Object, len(rows))
				for i, row := range rows {
					result[i] = upgradeWithout(row, "path", "root_identity")
				}
				return result
			}
			extra, e := upgradeExtra(strip(old), strip(current))
			if e != nil || len(extra) != 0 {
				return fmt.Errorf("UPGRADE_SOURCE_ROOTS_CHANGED")
			}
			for _, row := range current {
				if !upgradeInside(destination, Str(row, "path")) || Str(row, "root_identity") == "" {
					return fmt.Errorf("UPGRADE_SOURCE_ROOT_NOT_RELOCATED")
				}
			}
		case "schema_migrations":
			extra, e := upgradeExtra(old, current)
			seen := map[int64]bool{}
			for _, row := range extra {
				version, err := Num(row, "version")
				if err != nil || version < 14 || version > int64(target) || seen[version] {
					return fmt.Errorf("UPGRADE_MIGRATION_HISTORY")
				}
				seen[version] = true
			}
			if e != nil || len(seen) != target-13 {
				return fmt.Errorf("UPGRADE_MIGRATION_HISTORY")
			}
		default:
			if Hash(old) != Hash(current) {
				return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE_CHANGE: %s", table)
			}
		}
	}
	for table, rows := range after {
		if _, exists := before[table]; exists {
			continue
		}
		if table == "backup_restore_barriers" {
			if len(rows) != len(active) {
				return fmt.Errorf("UPGRADE_RESTORE_BARRIER_COUNT")
			}
			for _, row := range rows {
				if active[Str(row, "project")+"/Run/"+Str(row, "run")] == nil || Str(row, "restored_at") == "" {
					return fmt.Errorf("UPGRADE_RESTORE_BARRIER")
				}
			}
		} else if (target == 14 && !strings.HasPrefix(table, "remote_")) || (target == 20 && !upgradeFinalTables[table]) || len(rows) != 0 {
			return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE")
		}
	}
	return nil
}

func upgradeEffects(before, after []Object) error {
	extra, e := upgradeExtra(before, after)
	if e != nil {
		return e
	}
	latest := map[string]Object{}
	for _, row := range before {
		key := Str(row, "project") + "/" + Str(row, "run") + "/" + Str(row, "effect_key")
		seq, _ := Num(row, "sequence")
		previous, _ := Num(latest[key], "sequence")
		if seq > previous {
			latest[key] = row
		}
	}
	expected := []Object{}
	for _, row := range latest {
		body, e := Decode([]byte(Str(row, "body")))
		if e != nil {
			return e
		}
		if body["state"] != "PREPARED" && body["state"] != "STARTED" && body["state"] != "UNKNOWN" {
			continue
		}
		seq, _ := Num(row, "sequence")
		body["state"] = "UNKNOWN"
		body["restore_reason"] = "SNAPSHOT_MAY_PREDATE_EXTERNAL_DISPATCH"
		// effectAppend owns the new sequence/timestamp inside the body.
		expected = append(expected, Merge(copyObject(row), Object{"sequence": seq + 1, "body": string(Bytes(body))}))
	}
	if len(expected) != len(extra) {
		return fmt.Errorf("UPGRADE_EFFECT_FENCE_COUNT")
	}
	for _, want := range expected {
		found := false
		for _, got := range extra {
			if Hash(upgradeWithout(want, "body")) != Hash(upgradeWithout(got, "body")) {
				continue
			}
			wb, _ := Decode([]byte(Str(want, "body")))
			gb, _ := Decode([]byte(Str(got, "body")))
			if Hash(upgradeWithout(wb, "sequence", "observed_at")) != Hash(upgradeWithout(gb, "sequence", "observed_at")) {
				return fmt.Errorf("UPGRADE_EFFECT_FENCE_BODY")
			}
			found = true
		}
		if !found {
			return fmt.Errorf("UPGRADE_EFFECT_FENCE_MISSING")
		}
	}
	return nil
}

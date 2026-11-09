package domain

// Fixed source21 to target22 plan. Historical 13/14/20 guards are intentionally
// separate: only the four source-defined operational kinds are unversioned.
import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/adapters/retrieval"
	"researchos.local/research-os/internal/store"
	"sort"
	"strings"
	"time"
)

const QueueSchemaUpgradePlan = "schema21-to22-client-command-queue-v1"
const upgradeQueueSQLHash = "sha256:e2abcc078bbac1c076736a40249d50c85e25b4c8fd93e975f8528f8f8277abcd"
const upgradeQueueSessionHash = "sha256:1ca3930f96f7c2c99e7bc6e668dd5658393264cf1e6bf6352b47fb3de8c7dfe3"

var upgradeQueueTables = map[string]bool{"client_queue_fences": true, "client_command_queue": true, "client_control_requests": true, "client_control_receipts": true}

type upgradeQueueProtection struct {
	upgradeProtection
	contracts       *Contracts
	operationalHash string
}

// Same-host continuity reads only directory metadata. It does not copy a
// workspace, grant access, or replace the existing host authority/pin store.
func upgradeQueueWorkspaceIdentity(db *sql.DB, opt LocalUpgradeOptions) (Object, error) {
	bindings, e := workspaceBackupBindings(db)
	if e != nil {
		return nil, e
	}
	manifest := Object{}
	for _, b := range bindings {
		path, e := upgradeExistingPath(b.RealPath)
		if e != nil {
			return nil, e
		}
		if !strings.EqualFold(filepath.Clean(path), filepath.Clean(b.RealPath)) {
			return nil, fmt.Errorf("UPGRADE_WORKSPACE_ALIAS")
		}
		info, e := os.Stat(path)
		if e != nil || !info.IsDir() {
			return nil, fmt.Errorf("UPGRADE_WORKSPACE_DIRECTORY")
		}
		if backupWorkspaceOverlaps(path, opt.Destination) || backupWorkspaceOverlaps(path, opt.Snapshot) {
			return nil, fmt.Errorf("UPGRADE_WORKSPACE_OUTPUT_OVERLAP")
		}
		identity, e := retrieval.Identity(path)
		if e != nil {
			return nil, e
		}
		manifest[b.AuthorizedRef] = Object{"path": path, "identity": identity, "principal": b.PrincipalID, "host_principal": b.HostPrincipalRef, "access": b.Access, "project": b.ProjectID}
	}
	return manifest, nil
}

func upgradeQueueTemplate(ctx context.Context, sqls [][]byte, contracts *Contracts) (string, string, error) {
	if len(sqls) != 23 {
		return "", "", fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
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
	for i, raw := range sqls[:21] {
		if _, e = db.ExecContext(ctx, string(raw)); e != nil {
			return "", "", e
		}
		if _, e = db.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", i+1); e != nil {
			return "", "", e
		}
	}
	if _, e = db.ExecContext(ctx, string(sqls[22])); e != nil {
		return "", "", e
	}
	if e = installClientSessionFence(ctx, db, false); e != nil {
		return "", "", e
	}
	before, e := backupSchema(db)
	if e != nil {
		return "", "", e
	}
	if _, e = (&Service{DB: db, Contracts: contracts}).backupFence(ctx); e != nil {
		return "", "", e
	}
	if e = upgradeQueueMigration(ctx, db, sqls[21], sqls[22]); e != nil {
		return "", "", e
	}
	after, e := backupSchema(db)
	return before, after, e
}

func upgradeQueueMigration(ctx context.Context, db *sql.DB, raw, additive []byte) error {
	if Digest(raw) != upgradeQueueSQLHash || Digest(additive) != upgradeQueueSessionHash {
		return fmt.Errorf("UPGRADE_MIGRATION_HASH")
	}
	versions, e := backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(21)) {
		return fmt.Errorf("UPGRADE_SOURCE_VERSION")
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
	// The exact additive schema must already exist. Reinstalling it must be a
	// no-op, not a repair of corrupt source state or a reconstruction of sessions.
	if _, e = tx.ExecContext(ctx, string(additive)); e != nil {
		return e
	}
	if e = installClientSessionFence(ctx, tx, false); e != nil {
		return e
	}
	if _, e = tx.ExecContext(ctx, string(raw)); e != nil {
		return e
	}
	if _, e = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(22)"); e != nil {
		return e
	}
	after, e := upgradeQueueRows(tx)
	if e != nil {
		return e
	}
	for table, rows := range before {
		if table == "schema_migrations" {
			continue
		}
		if Hash(rows) != Hash(after[table]) {
			return fmt.Errorf("UPGRADE_MIGRATION_MUTATED_HISTORY: %s", table)
		}
	}
	for table := range upgradeQueueTables {
		if rows, ok := after[table]; !ok || len(rows) != 0 {
			return fmt.Errorf("UPGRADE_QUEUE_NOT_EMPTY: %s", table)
		}
	}
	for table := range after {
		if _, ok := before[table]; !ok && !upgradeQueueTables[table] {
			return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE: %s", table)
		}
	}
	var integrity string
	if e = tx.QueryRowContext(ctx, "PRAGMA integrity_check").Scan(&integrity); e != nil || integrity != "ok" {
		return fmt.Errorf("UPGRADE_TARGET_INTEGRITY")
	}
	check, e := tx.QueryContext(ctx, "PRAGMA foreign_key_check")
	if e != nil {
		return e
	}
	bad := check.Next()
	e = check.Err()
	check.Close()
	if bad || e != nil {
		return fmt.Errorf("UPGRADE_TARGET_REFERENCE")
	}
	return tx.Commit()
}

func upgradeQueueFields(o Object, names string) bool {
	fields := strings.Fields(names)
	if len(fields) != len(o) {
		return false
	}
	for _, name := range fields {
		if _, ok := o[name]; !ok {
			return false
		}
	}
	return true
}
func upgradeQueueStrings(o Object, names string) bool {
	for _, name := range strings.Fields(names) {
		v, ok := o[name].(string)
		if !ok || strings.TrimSpace(v) == "" {
			return false
		}
	}
	return true
}
func upgradeQueueTime(o Object, name string) bool {
	_, e := time.Parse(time.RFC3339Nano, Str(o, name))
	return e == nil
}

func (g *upgradeQueueProtection) validateTyped(db *sql.DB) error {
	rows, e := upgradeRows(db)
	if e != nil {
		return e
	}
	current := map[string]Object{}
	history := map[string]Object{}
	operational := []Object{}
	allowed := map[string]bool{KindWorkspaceBinding: true, KindBootstrapStage: true, "BootstrapReplay": true, "Project": true}
	for _, r := range rows["domain_versions"] {
		kind := Str(r, "kind")
		body, err := Decode([]byte(Str(r, "body")))
		var wantHash any
		if h, ok := body["receipt_hash"]; ok {
			wantHash = h
		} else if kind == "Artifact" {
			wantHash = body["content_hash"]
		}
		if err != nil || !g.contracts.Entities[kind] || allowed[kind] || g.contracts.Validate(kind, body) != nil || Hash(r["revision"]) != Hash(body["revision"]) || r["id"] != body["id"] || (body["project_id"] != nil && r["project"] != body["project_id"]) || Hash(r["content_hash"]) != Hash(wantHash) {
			return fmt.Errorf("UPGRADE_VERSIONED_IDENTITY: %s", kind)
		}
		history[upgradeObjectKey(r)+"/"+fmt.Sprint(r["revision"])] = r
	}
	hasState := map[string]bool{}
	for _, r := range rows["domain_objects"] {
		current[upgradeObjectKey(r)] = r
		if r["kind"] == "ProjectState" {
			hasState[Str(r, "project")] = true
		}
	}
	exists := func(project, kind, id string) bool { return id != "" && current[project+"/"+kind+"/"+id] != nil }
	bodyFor := func(project, kind, id string) Object {
		b, _ := Decode([]byte(Str(current[project+"/"+kind+"/"+id], "body")))
		return b
	}
	principal := func(id string) bool {
		for _, p := range rows["auth_principals"] {
			if p["id"] == id {
				return true
			}
		}
		return false
	}
	for _, r := range rows["domain_objects"] {
		kind, project, id := Str(r, "kind"), Str(r, "project"), Str(r, "id")
		if !allowed[kind] {
			h := history[upgradeObjectKey(r)+"/"+fmt.Sprint(r["revision"])]
			if !g.contracts.Entities[kind] || h == nil || r["body"] != h["body"] || Hash(r["content_hash"]) != Hash(h["content_hash"]) {
				return fmt.Errorf("UPGRADE_CURRENT_HISTORY_BINDING")
			}
			continue
		}
		body, err := Decode([]byte(Str(r, "body")))
		rev, re := Num(body, "revision")
		if err != nil || re != nil || rev < 1 || Hash(r["revision"]) != Hash(rev) || Hash(r["immutable"]) != Hash(0) || r["content_hash"] != Digest([]byte(Str(r, "body"))) {
			return fmt.Errorf("UPGRADE_OPERATIONAL_ROW: %s", kind)
		}
		valid := false
		switch kind {
		case KindWorkspaceBinding:
			valid = project == "" && id == body["authorized_workspace_ref"] && upgradeQueueFields(body, "authorized_workspace_ref display_name display_path real_path access project_id revision status principal_id host_principal_ref client_id selection_ref command_id created_at") && upgradeQueueStrings(body, "authorized_workspace_ref display_name display_path real_path principal_id host_principal_ref client_id selection_ref command_id") && (body["status"] == WorkspaceActive || body["status"] == WorkspaceRevoked) && (body["access"] == "READ_ONLY" || body["access"] == "READ_WRITE") && principal(Str(body, "principal_id")) && upgradeQueueTime(body, "created_at")
			_, err = canonicalLocalPath(Str(body, "real_path"))
			valid = valid && err == nil
			if body["project_id"] != nil {
				valid = valid && exists(Str(body, "project_id"), "Project", Str(body, "project_id"))
			}
		case "Project":
			binding := bodyFor("", KindWorkspaceBinding, Str(body, "authorized_workspace_ref"))
			valid = project != "" && id == project && body["id"] == id && body["project_id"] == project && upgradeQueueFields(body, "id project_id revision created_at updated_at name authorized_workspace_ref real_path") && upgradeQueueStrings(body, "name authorized_workspace_ref real_path") && upgradeQueueTime(body, "created_at") && upgradeQueueTime(body, "updated_at") && exists(project, "ProjectProfile", id) && hasState[project] && binding != nil && binding["project_id"] == project && binding["real_path"] == body["real_path"]
		case KindBootstrapStage:
			stage, status := Str(body, "stage"), Str(body, "status")
			suffix := strings.ToLower(stage)
			if stage == StageLocalInventory {
				suffix = "local-inventory"
			}
			valid = project != "" && exists(project, "Project", project) && body["id"] == id && body["project_id"] == project && id == "stage-"+project+"-"+suffix && upgradeQueueFields(body, "id project_id stage status inventory_artifact_ref file_failures observed_at revision") && upgradeQueueTime(body, "observed_at") && (stage == StageLocalInventory || stage == StageResearch || stage == StageReuseDecision || stage == StageImplementation) && (status == StageNotStarted || status == StageCompleted || status == StagePartial || status == StageFailed)
			failures, ok := body["file_failures"].([]any)
			valid = valid && ok
			for _, failure := range failures {
				f, ok := failure.(map[string]any)
				valid = valid && ok && upgradeQueueFields(f, "path reason content_disclosed") && upgradeQueueStrings(f, "path reason")
				if _, ok := f["content_disclosed"].(bool); !ok {
					valid = false
				}
				if filepathLike(Str(f, "path")) || strings.Contains(Str(f, "path"), "..") {
					valid = false
				}
			}
			if status == StageNotStarted {
				valid = valid && body["inventory_artifact_ref"] == nil && len(failures) == 0
			} else {
				valid = valid && exists(project, "Artifact", Str(body, "inventory_artifact_ref"))
			}
		case "BootstrapReplay":
			binding := bodyFor("", KindWorkspaceBinding, Str(body, "authorized_workspace_ref"))
			artifact := bodyFor(project, "Artifact", Str(body, "artifact_id"))
			valid = project != "" && body["project_id"] == project && id == "replay-"+Str(body, "command_id") && rev == 1 && upgradeQueueFields(body, "project_id command_id principal_id authorized_workspace_ref stage_id artifact_id revision") && upgradeQueueStrings(body, "project_id command_id principal_id authorized_workspace_ref stage_id artifact_id") && principal(Str(body, "principal_id")) && binding != nil && binding["project_id"] == project && binding["principal_id"] == body["principal_id"] && body["stage_id"] == "stage-"+project+"-local-inventory" && exists(project, KindBootstrapStage, Str(body, "stage_id")) && artifact != nil && artifact["produced_by"] == body["principal_id"] && artifact["kind"] == "MANIFEST" && artifact["access_class"] == "PROJECT"
		}
		if !valid {
			return fmt.Errorf("UPGRADE_OPERATIONAL_SHAPE: %s", kind)
		}
		operational = append(operational, r)
	}
	// A VersionRef cannot target or originate from an operational kind, even if
	// an attacker fabricated a matching history row for it.
	for _, r := range rows["domain_refs"] {
		if allowed[Str(r, "kind")] || allowed[Str(r, "target_kind")] {
			return fmt.Errorf("UPGRADE_OPERATIONAL_VERSION_REF")
		}
	}
	digest := Hash(operational)
	if g.operationalHash != "" && g.operationalHash != digest {
		return fmt.Errorf("UPGRADE_OPERATIONAL_ROWS_CHANGED")
	}
	g.operationalHash = digest
	return nil
}

func upgradeQueueLocal(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (RestoreReport, error) {
	report := RestoreReport{Started: Now(), Status: "FAILED"}
	if e := upgradePaths(&opt); e != nil {
		return report, e
	}
	sourceRelease, _, e := upgradeQueueRelease(opt.SourceRoot, 21)
	if e != nil {
		return report, e
	}
	targetRelease, sqls, e := upgradeQueueRelease(opt.TargetRoot, 22)
	if e != nil {
		return report, e
	}
	contracts, e := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
	if e != nil {
		return report, e
	}
	expectedSourceSchema, expectedTargetSchema, e := upgradeQueueTemplate(ctx, sqls, contracts)
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
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(21)) {
		return report, fmt.Errorf("UPGRADE_SOURCE_VERSION: require exact 1..21")
	}
	schema, e := backupSchema(db)
	if e != nil || schema != expectedSourceSchema {
		return report, fmt.Errorf("UPGRADE_SOURCE_SCHEMA")
	}
	guard := &upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: ctx, verifier: verifier}, contracts: contracts}
	if e = guard.refresh(db); e != nil {
		return report, e
	}
	// Reject any host-side protected storage before reading ordinary BLOB rows
	// for the logical inventory or creating a snapshot.
	original, e := upgradeRows(db)
	if e != nil {
		return report, e
	}
	workspaceIdentity, e := upgradeQueueWorkspaceIdentity(db, opt)
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
	plan := Object{"id": opt.Plan, "source_versions": versions, "target_versions": upgradeVersions(22),
		"source_schema_hash": schema, "target_schema_with_restore_fence_hash": expectedTargetSchema,
		"source_release_hash": Hash(sourceRelease), "target_release_hash": Hash(targetRelease),
		"migration_sql_hash": Digest(sqls[21]), "source_database_logical_hash": Hash(original),
		"source_release_manifest": sourceRelease, "target_release_manifest": targetRelease, "operational_row_manifest_hash": guard.operationalHash,
		"workspace_identity_manifest_hash": Hash(workspaceIdentity),
		"program_hashes":                   programHashes, "host_binding_hash": Hash(host), "service_summary_hash": guard.summaryHash,
		"source_path_hash": Hash(opt.Source), "target_path_hash": Hash(opt.Destination)}
	purpose := Object{"kind": "SAME_HOST_CONTROL_PLANE_UPGRADE", "scope": "SameHostExternalReferenceContinuityOnly",
		"plan": plan, "plan_hash": Hash(plan), "protected_reference_versions": guard.count,
		"protected_reference_digest": guard.referencesHash, "protected_payloads_included": false,
		"protected_payloads_revalidated": false, "recovery_dependency": "ORIGINAL_PROTECTED_SERVICE",
		"external_actions_dispatched": 0, "source_ownership": "SQLITE_EXCLUSIVE_UNTIL_TARGET_PUBLICATION",
		"cutover_requirement": "Keep original application and workers stopped until independent review and single-writer cutover; do not run both authorities."}
	policy := &backupPolicy{format: localUpgradeFormat, databaseName: "researchos.sqlite", purpose: purpose, validate: guard.refresh, allowProtected: guard.artifact}
	policy.preserveQueueUpgradeWorkspaces = func(restored *sql.DB) error {
		if e := guard.refresh(restored); e != nil {
			return e
		}
		rows, e := upgradeRows(restored)
		if e != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("UPGRADE_SNAPSHOT_HISTORY_MISMATCH")
		}
		identity, e := upgradeQueueWorkspaceIdentity(restored, opt)
		if e != nil || Hash(identity) != Hash(workspaceIdentity) {
			return fmt.Errorf("UPGRADE_WORKSPACE_IDENTITY_CHANGED")
		}
		return nil
	}
	policy.beforeRecovery = func(restored *sql.DB) error {
		rows, e := upgradeRows(restored)
		if e != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("UPGRADE_SNAPSHOT_HISTORY_MISMATCH")
		}
		return nil
	}
	policy.afterRecovery = func(restored *sql.DB) error {
		identity, err := upgradeQueueWorkspaceIdentity(restored, opt)
		if err != nil || Hash(identity) != Hash(workspaceIdentity) {
			return fmt.Errorf("UPGRADE_WORKSPACE_IDENTITY_CHANGED")
		}
		currentSchema, e := backupSchema(restored)
		if e != nil || currentSchema != expectedTargetSchema {
			return fmt.Errorf("UPGRADE_TARGET_SCHEMA")
		}
		rows, e := upgradeRows(restored)
		if e != nil {
			return e
		}
		if e = upgradeQueueRecoveryInvariant(original, rows, opt.Destination); e != nil {
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
			{opt.SourceRoot, 21, Hash(sourceRelease)}, {opt.TargetRoot, 22, Hash(targetRelease)},
		} {
			current, _, err := upgradeQueueRelease(entry.root, entry.n)
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
			return upgradeQueueMigration(ctx, target, sqls[21], sqls[22])
		},
	}, policy)
}

func (g *upgradeQueueProtection) refresh(db *sql.DB) error {
	var host int
	if e := db.QueryRow("SELECT count(*) FROM uploaded_content WHERE storage_key GLOB 'ps1:*'").Scan(&host); e != nil || host != 0 {
		return fmt.Errorf("UPGRADE_PROTECTED_HOST_CONTENT_PROHIBITED")
	}
	if e := g.validateTyped(db); e != nil {
		return e
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

func upgradeQueueRecoveryInvariant(before, after upgradeData, destination string) error {
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
		case "backup_restore_barriers":
			oldByKey := map[string]Object{}
			for _, row := range old {
				oldByKey[Str(row, "project")+"/Run/"+Str(row, "run")] = row
			}
			for _, row := range current {
				key := Str(row, "project") + "/Run/" + Str(row, "run")
				if active[key] != nil {
					if Str(row, "restored_at") == "" {
						return fmt.Errorf("UPGRADE_RESTORE_BARRIER")
					}
				} else if Hash(row) != Hash(oldByKey[key]) {
					return fmt.Errorf("UPGRADE_RESTORE_BARRIER_DRIFT")
				}
				delete(oldByKey, key)
			}
			if len(oldByKey) != 0 {
				return fmt.Errorf("UPGRADE_RESTORE_BARRIER_LOST")
			}
			for key := range active {
				found := false
				for _, row := range current {
					if Str(row, "project")+"/Run/"+Str(row, "run") == key {
						found = true
					}
				}
				if !found {
					return fmt.Errorf("UPGRADE_RESTORE_BARRIER_MISSING")
				}
			}
		case "schema_migrations":
			extra, e := upgradeExtra(old, current)
			seen := map[int64]bool{}
			for _, row := range extra {
				version, err := Num(row, "version")
				if err != nil || version != 22 || seen[version] {
					return fmt.Errorf("UPGRADE_MIGRATION_HISTORY")
				}
				seen[version] = true
			}
			if e != nil || len(seen) != 1 {
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
		} else if !upgradeQueueTables[table] || len(rows) != 0 {
			return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE")
		}
	}
	return nil
}

func upgradeQueueRelease(root string, count int) (Object, [][]byte, error) {
	if count != 21 && count != 22 {
		return nil, nil, fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	files, e := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql")) // release inputs are the numbered migrations only; unnumbered additive files (e.g. next_v24_sessions.sql) are applied through their own single-transaction path
	if e != nil || len(files) != count {
		return nil, nil, fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS: require exact 1..%d", count)
	}
	manifest := Object{}
	sqls := make([][]byte, count+1)
	for i, file := range files {
		name := filepath.Base(file)
		if len(name) < 5 || name[:4] != fmt.Sprintf("%04d", i+1) {
			return nil, nil, fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS")
		}
		raw, e := os.ReadFile(file)
		expected := upgradeMigrationHashes[name]
		if name == "0021_research_pending_windows.sql" {
			expected = "sha256:36d4e5c93aa1edcd7ca5aca922b3bea11d5739f307bd11c6834936adf5552f32"
		}
		if name == "0022_client_command_queue.sql" {
			expected = upgradeQueueSQLHash
		}
		if e != nil || Digest(raw) != expected {
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
	additive, e := os.ReadFile(filepath.Join(root, "migrations/sqlite/next_v24_sessions.sql"))
	if e != nil || Digest(additive) != upgradeQueueSessionHash {
		return nil, nil, fmt.Errorf("UPGRADE_SESSION_SCHEMA_HASH")
	}
	manifest["migrations/sqlite/next_v24_sessions.sql"] = Digest(additive)
	sqls[count] = additive
	return manifest, sqls, nil
}

func upgradeQueueRows(db interface {
	Query(string, ...any) (*sql.Rows, error)
}) (upgradeData, error) {
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

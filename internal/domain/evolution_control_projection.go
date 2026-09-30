//go:build windows

package domain

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/internal/store"
)

// PrepareEvolutionControlBundle consumes a caller-frozen snapshot, never an
// actual authority path or another write connection to its database. A fresh
// SQLite file receives only the enumerated ordinary research rows. Original
// credentials, content, private refs/labels, release state and free pages cannot
// cross into the AppContainer input. This narrow profile excludes monitor work,
// experiments and successful closure; future coverage requires a new profile.
func PrepareEvolutionControlBundle(ctx context.Context, snapshot []byte, root, project, cycleID string) (evolution.ControlBundle, error) {
	bundle := evolution.ControlBundle{Files: map[string][]byte{}}
	if len(snapshot) < 16 || len(snapshot) > 32*1024*1024 || string(snapshot[:16]) != "SQLite format 3\x00" {
		return bundle, fmt.Errorf("CONTROL_SOURCE_SNAPSHOT")
	}
	_, _, err := upgradeRelease(root, 20)
	if err != nil {
		return bundle, err
	}
	for name := range evolution.ControlReleaseHashes() {
		raw, e := os.ReadFile(filepath.Join(root, filepath.FromSlash(name)))
		if e != nil {
			return bundle, e
		}
		bundle.Files[name] = raw
	}
	work, err := os.MkdirTemp("", "researchos-control-projection-")
	if err != nil {
		return bundle, err
	}
	defer os.RemoveAll(work)
	sourcePath := filepath.Join(work, "source.sqlite")
	if err = os.WriteFile(sourcePath, snapshot, 0600); err != nil {
		return bundle, err
	}
	source, err := store.Open(sourcePath)
	if err != nil {
		return bundle, err
	}
	defer source.Close()
	versions, err := backupMigrations(source)
	if err != nil || Hash(versions) != Hash(upgradeVersions(20)) {
		return bundle, fmt.Errorf("CONTROL_SOURCE_VERSION")
	}
	generation, err := evolution.ControlDatabaseHash(source)
	if err != nil {
		return bundle, err
	}
	path := filepath.Join(work, "projection.sqlite")
	target, err := store.Open(path)
	if err != nil {
		return bundle, err
	}
	defer target.Close()
	if err = store.Bootstrap(ctx, target, filepath.Join(root, "migrations/sqlite/0001_bootstrap.sql")); err != nil {
		return bundle, err
	}
	_, err = New(target, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql"))
	if err != nil {
		return bundle, err
	}
	a, err := backupSchema(source)
	if err != nil {
		return bundle, err
	}
	b, err := backupSchema(target)
	if err != nil || a != b {
		return bundle, fmt.Errorf("CONTROL_SOURCE_SCHEMA")
	}
	rows, err := upgradeRows(source)
	if err != nil {
		return bundle, err
	}
	allowed := map[string]bool{"ProjectProfile": true, "ProjectState": true, "BudgetPolicy": true, "RunPolicy": true, "AcceptancePolicy": true, "ResearchCycle": true, "SourceCursor": true}
	selected := map[string][]Object{"domain_objects": {}, "domain_versions": {}, "domain_refs": {}}
	keys := map[string]bool{}
	var cycle Object
	for _, table := range []string{"domain_versions", "domain_objects"} {
		for _, row := range rows[table] {
			kind, p := Str(row, "kind"), Str(row, "project")
			if !allowed[kind] || p != project && !(p == "" && (kind == "BudgetPolicy" || kind == "RunPolicy")) || kind == "ResearchCycle" && row["id"] != cycleID {
				continue
			}
			body, e := Decode([]byte(Str(row, "body")))
			if e != nil {
				return bundle, e
			}
			if kind == "ProjectProfile" {
				for _, v := range Arr(body, "source_configs") {
					config := v.(map[string]any)
					if config["credential_ref"] != nil {
						return bundle, fmt.Errorf("CONTROL_SOURCE_CREDENTIAL_NOT_PROJECTABLE")
					}
				}
			}
			if kind == "ResearchCycle" {
				for _, field := range []string{"candidate_evidence_ids", "required_experiment_ids", "decision_ids", "follow_up_task_ids"} {
					if len(Arr(body, field)) != 0 {
						return bundle, fmt.Errorf("CONTROL_PROFILE_COMPLEX_CYCLE_UNSUPPORTED")
					}
				}
				if body["checkpoint_artifact_id"] != nil {
					return bundle, fmt.Errorf("CONTROL_PROFILE_REPORT_UNSUPPORTED")
				}
				if table == "domain_objects" {
					cycle = body
				}
			}
			selected[table] = append(selected[table], row)
			if table == "domain_versions" {
				keys[Hash([]any{row["project"], row["kind"], row["id"], row["revision"]})] = true
			}
		}
	}
	if cycle == nil || cycle["status"] != "RUNNING" {
		return bundle, fmt.Errorf("CONTROL_RUNNING_CYCLE_REQUIRED")
	}
	for _, table := range []string{"research_monitor_cycles", "research_cycle_work"} {
		for _, row := range rows[table] {
			if row["project"] == project && row["cycle"] == cycleID {
				return bundle, fmt.Errorf("CONTROL_MONITOR_PROJECTION_UNSUPPORTED")
			}
		}
	}
	for _, row := range rows["domain_refs"] {
		if keys[Hash([]any{row["project"], row["kind"], row["id"], row["revision"]})] && keys[Hash([]any{row["target_project"], row["target_kind"], row["target_id"], row["target_revision"]})] {
			selected["domain_refs"] = append(selected["domain_refs"], row)
		}
	}
	tx, err := target.BeginTx(ctx, nil)
	if err != nil {
		return bundle, err
	}
	defer tx.Rollback()
	for _, table := range []string{"domain_versions", "domain_objects", "domain_refs"} {
		for _, row := range selected[table] {
			cols, args, marks := []string{}, []any{}, []string{}
			for col, value := range row {
				cols = append(cols, `"`+col+`"`)
				args = append(args, value)
				marks = append(marks, "?")
			}
			if _, err = tx.Exec(`INSERT INTO "`+table+`" (`+strings.Join(cols, ",")+`) VALUES (`+strings.Join(marks, ",")+`)`, args...); err != nil {
				return bundle, err
			}
		}
	}
	if _, err = tx.Exec("INSERT INTO auth_principals(id,roles,can_create_project,revoked) VALUES(?, ?,0,0)", evolution.ControlPrincipal, string(Bytes([]string{"OWNER", "PLANNER", "SCHEDULER"}))); err != nil {
		return bundle, err
	}
	if _, err = tx.Exec("INSERT INTO auth_grants(principal,project,task,run,restricted) VALUES(?,?,'','',0)", evolution.ControlPrincipal, project); err != nil {
		return bundle, err
	}
	if _, err = tx.Exec("INSERT INTO auth_credentials(token_hash,principal,expires_at,revoked) VALUES(?,?,'2100-01-01T00:00:00Z',0)", Digest([]byte(evolution.ControlCredential)), evolution.ControlPrincipal); err != nil {
		return bundle, err
	}
	if err = tx.Commit(); err != nil {
		return bundle, err
	}
	projection, err := evolution.ControlDatabaseHash(target)
	if err != nil {
		return bundle, err
	}
	if _, err = target.Exec("PRAGMA wal_checkpoint(TRUNCATE)"); err != nil {
		return bundle, err
	}
	if err = target.Close(); err != nil {
		return bundle, err
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return bundle, err
	}
	bundle.Files["snapshot.sqlite"] = raw
	bundle.Binding = evolution.ControlBinding{Protocol: evolution.ControlProtocol, AuthorityGeneration: generation, SourceSnapshotHash: Digest(snapshot), SnapshotHash: Digest(raw), ProjectionHash: projection, ProjectionPolicy: evolution.ControlProjection, ReleaseHash: Digest(evolution.Bytes(evolution.ControlReleaseHashes())), ProjectID: project, CycleID: cycleID}
	return bundle, bundle.Validate()
}

// Registration independently checks a deserialized public bundle before it can
// be a trusted host input. No original token or private authority is accepted.
func validateEvolutionControlBundle(ctx context.Context, bundle evolution.ControlBundle) error {
	if err := bundle.Validate(); err != nil {
		return err
	}
	work, err := os.MkdirTemp("", "researchos-control-validate-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(work)
	path := filepath.Join(work, "snapshot.sqlite")
	if err = os.WriteFile(path, bundle.Files["snapshot.sqlite"], 0600); err != nil {
		return err
	}
	db, err := store.Open(path)
	if err != nil {
		return err
	}
	defer db.Close()
	hash, err := evolution.ControlDatabaseHash(db)
	if err != nil || hash != bundle.Binding.ProjectionHash {
		return fmt.Errorf("CONTROL_PROJECTION_HASH")
	}
	rows, err := upgradeRows(db)
	if err != nil {
		return err
	}
	baseline, err := store.Open(filepath.Join(work, "expected-schema.sqlite"))
	if err != nil {
		return err
	}
	defer baseline.Close()
	names := []string{}
	for name := range evolution.ControlReleaseHashes() {
		if strings.HasPrefix(name, "migrations/sqlite/") {
			names = append(names, name)
		}
	}
	sort.Strings(names)
	for i, name := range names {
		if _, err = baseline.ExecContext(ctx, string(bundle.Files[name])); err != nil {
			return err
		}
		if _, err = baseline.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", i+1); err != nil {
			return err
		}
	}
	actualSchema, err := backupSchema(db)
	if err != nil {
		return err
	}
	expectedSchema, err := backupSchema(baseline)
	if err != nil || actualSchema != expectedSchema {
		return fmt.Errorf("CONTROL_PROJECTION_SCHEMA")
	}
	defaults, err := upgradeRows(baseline)
	if err != nil {
		return err
	}
	versions, err := backupMigrations(db)
	if err != nil || Hash(versions) != Hash(upgradeVersions(20)) {
		return fmt.Errorf("CONTROL_PROJECTION_VERSIONS")
	}
	allowed := map[string]bool{"schema_migrations": true, "domain_objects": true, "domain_versions": true, "domain_refs": true, "auth_principals": true, "auth_grants": true, "auth_credentials": true}
	for table, entries := range rows {
		if !allowed[table] && Hash(entries) != Hash(defaults[table]) {
			return fmt.Errorf("CONTROL_PROJECTION_FORBIDDEN_TABLE: %s", table)
		}
	}
	if len(rows["auth_principals"]) != 1 || len(rows["auth_grants"]) != 1 || len(rows["auth_credentials"]) != 1 {
		return fmt.Errorf("CONTROL_PROJECTION_CREDENTIALS")
	}
	p, g, c := rows["auth_principals"][0], rows["auth_grants"][0], rows["auth_credentials"][0]
	if p["id"] != evolution.ControlPrincipal || p["roles"] != string(Bytes([]string{"OWNER", "PLANNER", "SCHEDULER"})) || Hash(p["revoked"]) != Hash(0) || Hash(p["can_create_project"]) != Hash(0) || g["principal"] != p["id"] || g["project"] != bundle.Binding.ProjectID || g["task"] != "" || g["run"] != "" || Hash(g["restricted"]) != Hash(0) || c["principal"] != p["id"] || c["token_hash"] != Digest([]byte(evolution.ControlCredential)) || c["expires_at"] != "2100-01-01T00:00:00Z" || Hash(c["revoked"]) != Hash(0) {
		return fmt.Errorf("CONTROL_PROJECTION_CREDENTIAL_IDENTITY")
	}
	kinds := map[string]bool{"ProjectProfile": true, "ProjectState": true, "BudgetPolicy": true, "RunPolicy": true, "AcceptancePolicy": true, "ResearchCycle": true, "SourceCursor": true}
	for _, table := range []string{"domain_objects", "domain_versions"} {
		for _, row := range rows[table] {
			if !kinds[Str(row, "kind")] || row["project"] != bundle.Binding.ProjectID && !(row["project"] == "" && (row["kind"] == "BudgetPolicy" || row["kind"] == "RunPolicy")) {
				return fmt.Errorf("CONTROL_PROJECTION_OBJECT_SCOPE")
			}
			body, e := Decode([]byte(Str(row, "body")))
			if e != nil {
				return e
			}
			if row["kind"] == "ProjectProfile" {
				for _, v := range Arr(body, "source_configs") {
					if v.(map[string]any)["credential_ref"] != nil {
						return fmt.Errorf("CONTROL_PROJECTION_SECRET")
					}
				}
			}
		}
	}
	return ctx.Err()
}

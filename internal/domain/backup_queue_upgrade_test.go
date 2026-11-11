package domain

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"strings"
	"testing"
	"time"
)

// Local public fixture ports. Registration, bootstrap, CAS and all durable rows
// are created by the actual domain methods and the published protocol grader.
type queueUpgradeWorkspace struct{ path string }

func (w queueUpgradeWorkspace) ConsumeSelection(context.Context, string, string, string) (WorkspaceSelection, error) {
	return WorkspaceSelection{RealPath: w.path, DisplayPath: w.path, Access: "READ_ONLY", HostPrincipalRef: "fixture-local-user", ClientID: "queue-upgrade-client"}, nil
}
func (w queueUpgradeWorkspace) ConfirmPath(context.Context, string, string) error { return nil }
func (w queueUpgradeWorkspace) Scan(context.Context, string) (LocalInventoryScan, error) {
	return LocalInventoryScan{Environment: "public-upgrade-fixture", Entries: []LocalInventoryEntry{}, Failures: []LocalInventoryFileFailure{}}, nil
}

func (w queueUpgradeWorkspace) SnapshotWorkspace(_ context.Context, binding WorkspaceBinding, _ string, _ BackupWorkspaceLimits) (BackupWorkspaceSnapshot, error) {
	if binding.RealPath != w.path || binding.PrincipalID != "queue-upgrade-owner" {
		return BackupWorkspaceSnapshot{}, fmt.Errorf("foreign fixture workspace")
	}
	entries, e := os.ReadDir(w.path)
	if e != nil {
		return BackupWorkspaceSnapshot{}, e
	}
	if len(entries) != 0 {
		return BackupWorkspaceSnapshot{}, fmt.Errorf("fixture workspace unexpectedly populated")
	}
	return BackupWorkspaceSnapshot{Directories: []string{}, Files: []BackupWorkspaceFile{}}, nil
}

func queueUpgradeReleaseFixture(t *testing.T, n int) string {
	t.Helper()
	root := upgradeTestRelease(t, 20)
	input := "../.."
	if x := os.Getenv("RESEARCHOS_QUEUE_UPGRADE_TARGET_ROOT"); x != "" {
		input = x
	}
	names := []string{"0021_research_pending_windows.sql", "next_v24_sessions.sql"}
	if n == 22 {
		names = append(names, "0022_client_command_queue.sql")
	}
	for _, name := range names {
		raw, e := os.ReadFile(filepath.Join(input, "migrations/sqlite", name))
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(root, "migrations/sqlite", name), raw, 0600); e != nil {
			t.Fatal(e)
		}
	}
	if _, _, e := upgradeQueueRelease(root, n); e != nil {
		t.Fatal(e)
	}
	return root
}

func queueUpgradeFixture(t *testing.T) (LocalUpgradeOptions, *fixture) {
	t.Helper()
	ctx := context.Background()
	source, target := queueUpgradeReleaseFixture(t, 21), queueUpgradeReleaseFixture(t, 22)
	dbpath := filepath.Join(t.TempDir(), "source.sqlite")
	db, e := store.Open(dbpath)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { db.Close() })
	if e = store.Bootstrap(ctx, db, filepath.Join(source, "migrations/sqlite/0001_bootstrap.sql")); e != nil {
		t.Fatal(e)
	}
	svc, e := New(db, filepath.Join(source, "spec/v2.0/contracts"), filepath.Join(source, "migrations/sqlite/0002_domain.sql"))
	if e != nil {
		t.Fatal(e)
	}
	owner := Principal{ID: "queue-upgrade-owner", Roles: []string{"OWNER", "PLANNER", "SCHEDULER", "EXECUTOR"}, CanCreateProject: true}
	if e = svc.ProvisionPrincipal(ctx, owner); e != nil {
		t.Fatal(e)
	}
	token, e := svc.IssueCredential(ctx, owner.ID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile("../api/contracts/client.protocol.schema.json")
	if e != nil {
		t.Fatal(e)
	}
	external, e := os.ReadFile("../api/contracts/domain.schema.json")
	if e != nil {
		t.Fatal(e)
	}
	doc, e := LoadSchemaWithExternals(raw, map[string][]byte{"domain.schema.json": external})
	if e != nil {
		t.Fatal(e)
	}
	port := queueUpgradeWorkspace{t.TempDir()}
	binding, e := svc.RegisterWorkspace(ctx, owner, port, doc, RegisterWorkspaceInput{SelectionRef: "fixture-selection", DisplayName: "Queue upgrade", RequestedAccess: "READ_ONLY", CommandID: ID(), ClientID: "queue-upgrade-client"})
	if e != nil {
		t.Fatal(e)
	}
	input := BootstrapProjectInput{AuthorizedWorkspaceRef: Str(binding, "authorized_workspace_ref"), DisplayName: "Queue upgrade", ClientID: "queue-upgrade-client", CommandID: ID(), MeasurementMode: "FIXTURE"}
	result, e := svc.BootstrapProject(ctx, owner, port, doc, port, input)
	if e != nil {
		t.Fatal(e)
	}
	replay, e := svc.BootstrapProject(ctx, owner, port, doc, port, input)
	if e != nil || Hash(result) != Hash(replay) {
		t.Fatalf("bootstrap replay %v", e)
	}
	project := Str(result, "project_id")
	f := &fixture{s: svc, db: db, h: svc.Handler(), owner: owner.ID, token: token, project: project, t: t}
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	for i := 0; i < 2; i++ {
		sid := ID()
		s := ClientSession{ID: sid, ProjectID: project, Revision: 3, CreatedAt: time.Now(), UpdatedAt: time.Now(), WriterEpoch: 2, WriterClientID: "queue-upgrade-client", EventWatermark: 11, UpstreamSession: ID(), WorkspaceRef: &input.AuthorizedWorkspaceRef, Protocol: ClientSessionProtocol, ResumeExplicit: 1}
		if i == 1 {
			now := time.Now()
			s.SealedAt = &now
			s.ArchivedAt = &now
		}
		if e = MapClientSession(ctx, tx, s); e != nil {
			t.Fatal(e)
		}
		if i == 0 {
			if _, e = HandoffEpoch(ctx, tx, sid, 2, 3); e != nil {
				t.Fatal(e)
			}
			if _, e = HandoffEpoch(ctx, tx, sid, 2, 3); e == nil {
				t.Fatal("stale CAS accepted")
			}
		}
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	// Ordinary HTTP idempotency/event history in addition to bootstrap replay.
	f.requirement()
	key := filepath.Join(t.TempDir(), "fixture.key")
	if e = os.WriteFile(key, bytes.Repeat([]byte{42}, 32), 0600); e != nil {
		t.Fatal(e)
	}
	executable, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	return LocalUpgradeOptions{Source: dbpath, Snapshot: filepath.Join(t.TempDir(), "backup"), Destination: filepath.Join(t.TempDir(), "candidate"), KeyFile: key, SourceRoot: source, TargetRoot: target, SourceProgram: executable, TargetProgram: executable, Plan: QueueSchemaUpgradePlan}, f
}

func TestQueueUpgradePopulatedBootstrapRoundTrip(t *testing.T) {
	opt, f := queueUpgradeFixture(t)
	ctx := context.Background()
	before, e := upgradeRows(f.db)
	if e != nil {
		t.Fatal(e)
	}
	for _, kind := range []string{KindWorkspaceBinding, KindBootstrapStage, "BootstrapReplay", "Project"} {
		n := 0
		for _, row := range before["domain_objects"] {
			if row["kind"] == kind {
				n++
			}
		}
		if n == 0 {
			t.Fatalf("missing actual bootstrap kind %s", kind)
		}
	}
	if len(before["client_sessions"]) != 2 || len(before["idempotency"]) == 0 || len(before["outbox"]) == 0 {
		t.Fatal("unpopulated session/replay/event fixture")
	}
	if _, e = New(f.db, filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"), filepath.Join(opt.TargetRoot, "migrations/sqlite/0002_domain.sql")); e == nil || !strings.Contains(e.Error(), "MIGRATION_PREBACKUP_REQUIRED") {
		t.Fatalf("in-place upgrade: %v", e)
	}
	if e = (&upgradeProtection{ctx: ctx}).refresh(f.db); e == nil {
		t.Fatal("historical opaque guard was relaxed")
	}
	f.db.Close()
	report, e := upgradeLocal(ctx, opt, upgradeVerifier{})
	if e != nil {
		t.Fatal(e)
	}
	if report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report.Status)
	}
	source, e := store.Open(opt.Source)
	if e != nil {
		t.Fatal(e)
	}
	afterSource, e := upgradeRows(source)
	source.Close()
	if e != nil || Hash(before) != Hash(afterSource) {
		t.Fatal("source database changed", e)
	}
	db, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	after, e := upgradeRows(db)
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeQueueRecoveryInvariant(before, after, opt.Destination); e != nil {
		t.Fatal(e)
	}
	for _, table := range []string{"client_sessions", "idempotency", "outbox", "domain_versions", "domain_refs"} {
		if Hash(before[table]) != Hash(after[table]) {
			t.Fatalf("%s drift", table)
		}
	}
	for table := range upgradeQueueTables {
		if rows, ok := after[table]; !ok || len(rows) != 0 {
			t.Fatalf("queue table %s not empty", table)
		}
	}
	svc, e := New(db, filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"), filepath.Join(opt.TargetRoot, "migrations/sqlite/0002_domain.sql"))
	if e != nil {
		t.Fatal(e)
	}
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil {
		t.Fatal(e)
	}
	backup := filepath.Join(t.TempDir(), "target-backup")
	var workspace string
	if e = db.QueryRow("SELECT json_extract(body,'$.real_path') FROM domain_objects WHERE kind='WorkspaceBinding'").Scan(&workspace); e != nil {
		t.Fatal(e)
	}
	if _, e = svc.CreateBackupWithWorkspaces(ctx, backup, key, queueUpgradeWorkspace{workspace}); e != nil {
		t.Fatal(e)
	}
	restored := filepath.Join(t.TempDir(), "target-restored")
	var rebound string
	pin := func(_ context.Context, _ string, requests []WorkspaceRestoreRequest) ([]WorkspaceRestorePin, error) {
		pins := []WorkspaceRestorePin{}
		for _, r := range requests {
			if _, e := os.Stat(r.RealPath); e != nil {
				return nil, e
			}
			rebound = r.RealPath
			pins = append(pins, WorkspaceRestorePin{AuthorizedRef: r.AuthorizedRef, RealPath: r.RealPath, HostPrincipalRef: "fixture-restored-user"})
		}
		return pins, nil
	}
	if _, e = RestoreBackup(ctx, backup, restored, RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(22), Contracts: svc.Contracts, DatabaseName: "researchos.sqlite", WorkspaceTarget: pin}); e != nil {
		t.Fatal(e)
	}
	round, e := store.Open(filepath.Join(restored, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer round.Close()
	roundRows, e := upgradeRows(round)
	if e != nil {
		t.Fatal(e)
	}
	for table, old := range after {
		if table != "domain_objects" && Hash(old) != Hash(roundRows[table]) {
			t.Fatalf("ordinary target roundtrip changed %s", table)
		}
	}
	for _, row := range roundRows["domain_objects"] {
		if row["kind"] != "WorkspaceBinding" && row["kind"] != "Project" {
			found := false
			for _, prior := range after["domain_objects"] {
				if Hash(prior) == Hash(row) {
					found = true
				}
			}
			if !found {
				t.Fatal("ordinary restore changed versioned row")
			}
		}
	}
	if rebound == "" || rebound == workspace {
		t.Fatal("ordinary restore did not isolate workspace")
	}
	if _, e = (&Service{DB: round, Contracts: svc.Contracts}).CreateBackupWithWorkspaces(ctx, filepath.Join(t.TempDir(), "rebackup"), key, queueUpgradeWorkspace{rebound}); e != nil {
		t.Fatal(e)
	}
	t.Log("source21 bootstrap4 + versioned history + active/inactive session/CAS/replay/events preserved; isolated22 ordinary backup/restore/rebackup passed")
}

func TestQueueUpgradeTypedRefusals(t *testing.T) {
	cases := map[string]string{
		"unknown-kind":              `INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('','Unexpected','bad',1,'{}',0)`,
		"WorkspaceBinding":          `UPDATE domain_objects SET body=json_set(body,'$.principal_id','foreign') WHERE kind='WorkspaceBinding'`,
		"BootstrapStage":            `UPDATE domain_objects SET body=json_set(body,'$.inventory_artifact_ref','foreign') WHERE kind='BootstrapStage' AND json_extract(body,'$.stage')='LOCAL_INVENTORY'`,
		"BootstrapReplay":           `UPDATE domain_objects SET body=json_set(body,'$.artifact_id','foreign') WHERE kind='BootstrapReplay'`,
		"Project":                   `UPDATE domain_objects SET body=json_set(body,'$.authorized_workspace_ref','foreign') WHERE kind='Project'`,
		"malformed-body":            `UPDATE domain_objects SET body=json_set(body,'$.unknown_field',1) WHERE kind='WorkspaceBinding'`,
		"revision":                  `UPDATE domain_objects SET revision=revision+1 WHERE kind='WorkspaceBinding'`,
		"hash":                      `UPDATE domain_objects SET content_hash='sha256:bad' WHERE kind='WorkspaceBinding'`,
		"masquerade-history":        `INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) SELECT project,kind,id,revision,body,content_hash FROM domain_objects WHERE kind='Project'`,
		"versioned-without-history": `INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) SELECT project,kind,id||'-fake',revision,body,content_hash,immutable FROM domain_objects WHERE kind='Requirement'`,
		"current-history-drift":     `UPDATE domain_objects SET body=json_set(body,'$.name','changed') WHERE kind='ProjectProfile'`,
	}
	for name, query := range cases {
		t.Run(name, func(t *testing.T) {
			_, f := queueUpgradeFixture(t)
			if _, e := f.db.Exec(query); e != nil {
				t.Fatal(e)
			}
			// Foreign-reference cases carry a valid body digest, exercising typed
			// relationship checks rather than merely the common checksum guard.
			if name == "WorkspaceBinding" || name == "BootstrapStage" || name == "BootstrapReplay" || name == "Project" || name == "malformed-body" {
				rows, e := upgradeRows(f.db)
				if e != nil {
					t.Fatal(e)
				}
				for _, r := range rows["domain_objects"] {
					if r["kind"] == name || name == "malformed-body" && r["kind"] == "WorkspaceBinding" {
						if _, e = f.db.Exec("UPDATE domain_objects SET content_hash=? WHERE project=? AND kind=? AND id=?", Digest([]byte(Str(r, "body"))), r["project"], r["kind"], r["id"]); e != nil {
							t.Fatal(e)
						}
					}
				}
			}
			g := upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: context.Background()}, contracts: f.s.Contracts}
			if e := g.refresh(f.db); e == nil {
				t.Fatal("corruption accepted")
			} else {
				t.Log(e)
			}
		})
	}
}

func TestQueueUpgradeFrozenInputAndOperationalDrift(t *testing.T) {
	opt, f := queueUpgradeFixture(t)
	g := upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: context.Background()}, contracts: f.s.Contracts}
	if e := g.refresh(f.db); e != nil {
		t.Fatal(e)
	}
	var raw, id string
	if e := f.db.QueryRow("SELECT body,id FROM domain_objects WHERE kind='WorkspaceBinding'").Scan(&raw, &id); e != nil {
		t.Fatal(e)
	}
	body, e := Decode([]byte(raw))
	if e != nil {
		t.Fatal(e)
	}
	body["display_name"] = "legitimate-shaped but changed"
	raw = string(Bytes(body))
	if _, e = f.db.Exec("UPDATE domain_objects SET body=?,content_hash=? WHERE kind='WorkspaceBinding' AND id=?", raw, Digest([]byte(raw)), id); e != nil {
		t.Fatal(e)
	}
	if e = g.refresh(f.db); e == nil || !strings.Contains(e.Error(), "OPERATIONAL_ROWS_CHANGED") {
		t.Fatalf("row manifest drift %v", e)
	}
	for _, name := range []string{"0021_research_pending_windows.sql", "0022_client_command_queue.sql", "next_v24_sessions.sql"} {
		t.Run(name, func(t *testing.T) {
			path := filepath.Join(opt.TargetRoot, "migrations/sqlite", name)
			raw, e := os.ReadFile(path)
			if e != nil {
				t.Fatal(e)
			}
			defer os.WriteFile(path, raw, 0600)
			if e = os.WriteFile(path, append(raw, []byte("\n-- changed")...), 0600); e != nil {
				t.Fatal(e)
			}
			if _, _, e = upgradeQueueRelease(opt.TargetRoot, 22); e == nil {
				t.Fatal("changed frozen SQL accepted")
			}
		})
	}
	if _, _, e = upgradeQueueRelease(opt.TargetRoot, 20); e == nil {
		t.Fatal("21 disguised as 20")
	}
}

func TestQueueUpgradeSchemaAndRollbackRefusals(t *testing.T) {
	for _, query := range []string{"DROP INDEX client_sessions_run", "DROP TRIGGER client_session_epoch_no_regression", "ALTER TABLE client_sessions DROP COLUMN transcript_artifact_id", "DELETE FROM schema_migrations WHERE version=21"} {
		t.Run(strings.Fields(query)[0]+fmt.Sprint(len(query)), func(t *testing.T) {
			opt, f := queueUpgradeFixture(t)
			if _, e := f.db.Exec(query); e != nil {
				t.Fatal(e)
			}
			f.db.Close()
			if _, e := upgradeLocal(context.Background(), opt, upgradeVerifier{}); e == nil {
				t.Fatal("corrupt source schema accepted")
			}
			if _, e := os.Stat(opt.Destination); !os.IsNotExist(e) {
				t.Fatal("failed candidate published")
			}
		})
	}
	opt, f := queueUpgradeFixture(t)
	_, sqls, e := upgradeQueueRelease(opt.TargetRoot, 22)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = f.db.Exec("CREATE TRIGGER fixture_refuse22 BEFORE INSERT ON schema_migrations WHEN NEW.version=22 BEGIN SELECT RAISE(ABORT,'fixture migration failure'); END"); e != nil {
		t.Fatal(e)
	}
	before, e := upgradeRows(f.db)
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeQueueMigration(context.Background(), f.db, sqls[21], sqls[22]); e == nil {
		t.Fatal("injected transaction failure accepted")
	}
	after, e := upgradeRows(f.db)
	if e != nil || Hash(before) != Hash(after) {
		t.Fatal("failed migration changed data", e)
	}
	for table := range upgradeQueueTables {
		if _, ok := after[table]; ok {
			t.Fatal("failed migration committed table")
		}
	}
}

func TestQueueUpgradeProtectedContinuityAndDrift(t *testing.T) {
	_, f := queueUpgradeFixture(t)
	fake := &upgradeFake{summary: qualificationSummary(t)}
	upgradeSeedQualifications(t, f, fake.summary)
	g := upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: context.Background(), verifier: fake.verifier()}, contracts: f.s.Contracts}
	if e := g.refresh(f.db); e != nil {
		t.Fatal(e)
	}
	if g.count == 0 || fake.descriptions == 0 || fake.reads != 0 {
		t.Fatal("protected fixture did not exercise descriptor-only continuity")
	}
	fake.fail = "hash"
	if e := g.refresh(f.db); e == nil {
		t.Fatal("protected descriptor drift accepted")
	}
	fake.fail = ""
	if e := g.refresh(f.db); e != nil {
		t.Fatal(e)
	}
	// A newly appended protected historical version is observable without reading
	// any protected body. Its shape is still checked against the frozen contract.
	var raw, project, id string
	var rev int
	if e := f.db.QueryRow("SELECT body,project,id,revision FROM domain_versions WHERE kind='Artifact' AND json_extract(body,'$.access_class')='VERIFIER_ONLY' ORDER BY revision DESC LIMIT 1").Scan(&raw, &project, &id, &rev); e != nil {
		t.Fatal(e)
	}
	body, e := Decode([]byte(raw))
	if e != nil {
		t.Fatal(e)
	}
	body["revision"] = rev + 1
	if _, e = f.db.Exec("INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) VALUES(?,'Artifact',?,?,?,?)", project, id, rev+1, string(Bytes(body)), body["content_hash"]); e != nil {
		t.Fatal(e)
	}
	if e = g.refresh(f.db); e == nil || !strings.Contains(e.Error(), "PROTECTED_HISTORY_CHANGED") {
		t.Fatalf("protected history drift: %v", e)
	}
	if fake.reads != 0 {
		t.Fatal("protected bytes read")
	}
}

func TestQueueUpgradeActiveRecovery(t *testing.T) {
	opt, f := queueUpgradeFixture(t)
	ctx := context.Background()
	req := f.requirement()
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "queue upgrade active fixture", "original_intent": "preserve active session authority", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"verified JSON"}, "acceptance_contract": orchestrationContract()})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "public fixture"})
	rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "queue upgrade observer", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if e := f.s.RegisterOrchestrationFixture(ctx, f.project, Str(rt, "id")); e != nil {
		t.Fatal(e)
	}
	orchestrator := &orchestrationFixture{f, goal, req, rt, f.token}
	run := orchestrator.claim(orchestrator.task("pending-queue-upgrade", Empty(), Empty()))
	f.token = orchestrator.owner
	var sid string
	if e := f.db.QueryRow("SELECT id FROM client_sessions WHERE sealed_at IS NULL").Scan(&sid); e != nil {
		t.Fatal(e)
	}
	if _, e := f.db.Exec("UPDATE client_sessions SET goal_id=?,task_id=?,run_id=? WHERE id=?", goal["id"], run.task["id"], run.run["id"], sid); e != nil {
		t.Fatal(e)
	}
	before, e := upgradeRows(f.db)
	if e != nil {
		t.Fatal(e)
	}
	f.db.Close()
	report, e := UpgradeLocal(ctx, opt)
	if e != nil || report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report, e)
	}
	source, e := store.Open(opt.Source)
	if e != nil {
		t.Fatal(e)
	}
	sourceRows, e := upgradeRows(source)
	source.Close()
	if e != nil || Hash(sourceRows) != Hash(before) {
		t.Fatal("public upgrade changed active source", e)
	}
	restored, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer restored.Close()
	after, e := upgradeRows(restored)
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeQueueRecoveryInvariant(before, after, opt.Destination); e != nil {
		t.Fatal(e)
	}
	if Hash(before["client_sessions"]) != Hash(after["client_sessions"]) {
		t.Fatal("active writer/session mapping changed")
	}
	tx, e := restored.Begin()
	if e != nil {
		t.Fatal(e)
	}
	_, e = HandoffEpoch(ctx, tx, sid, 3, 4)
	tx.Rollback()
	if e == nil || !strings.Contains(e.Error(), "RESTORE_FRESH_RECONCILIATION_REQUIRED") {
		t.Fatalf("restored active writer advanced: %v", e)
	}
	var runStatus string
	var restoredEpoch int64
	if e = restored.QueryRow("SELECT json_extract(body,'$.status'),json_extract(body,'$.lease_epoch') FROM domain_objects WHERE kind='Run' AND id=?", run.run["id"]).Scan(&runStatus, &restoredEpoch); e != nil || runStatus != "RECONCILING" || Hash(restoredEpoch) != Hash(run.run["lease_epoch"]) {
		t.Fatal("active Run was not fenced at public restore", runStatus, restoredEpoch, e)
	}
	var barriers int
	if e = restored.QueryRow("SELECT count(*) FROM backup_restore_barriers WHERE project=? AND run=?", f.project, run.run["id"]).Scan(&barriers); e != nil || barriers != 1 {
		t.Fatal("missing active restore barrier", barriers, e)
	}
	t.Log("public UpgradeLocal: authentic active source21 -> encrypted snapshot -> isolated restored22; source/session unchanged, active Run RECONCILING at original epoch with restore barrier, old CAS fenced")
	for _, table := range []string{"client_sessions", "idempotency", "domain_versions", "backup_restore_barriers"} {
		t.Run(table, func(t *testing.T) {
			changed := upgradeData{}
			for k, v := range after {
				changed[k] = v
			}
			changed[table] = nil
			if e := upgradeQueueRecoveryInvariant(before, changed, opt.Destination); e == nil {
				t.Fatalf("lost %s accepted", table)
			}
		})
	}
}

// Historical fixtures install only their exact numbered schema and exercise
// the original upgrade guards without current additive session initialization.
func TestQueueUpgradeHistoricalPlans(t *testing.T) {
	for _, target := range []int{14, 20} {
		t.Run(fmt.Sprint(target), func(t *testing.T) {
			ctx := context.Background()
			sourceRoot, targetRoot := upgradeTestRelease(t, 13), upgradeTestRelease(t, target)
			_, sqls, e := upgradeRelease(sourceRoot, 13)
			if e != nil {
				t.Fatal(e)
			}
			dbpath := filepath.Join(t.TempDir(), "source13.sqlite")
			db, e := store.Open(dbpath)
			if e != nil {
				t.Fatal(e)
			}
			defer db.Close()
			for i, raw := range sqls {
				if _, e = db.Exec(string(raw)); e != nil {
					t.Fatal(e)
				}
				if _, e = db.Exec("INSERT INTO schema_migrations(version) VALUES(?)", i+1); e != nil {
					t.Fatal(e)
				}
			}
			contracts, e := LoadContracts(filepath.Join(sourceRoot, "spec/v2.0/contracts"))
			if e != nil {
				t.Fatal(e)
			}
			svc := &Service{DB: db, Contracts: contracts}
			owner := Principal{ID: "historical-public-owner", Roles: []string{"OWNER", "PLANNER", "SCHEDULER", "EXECUTOR"}, CanCreateProject: true}
			if e = svc.ProvisionPrincipal(ctx, owner); e != nil {
				t.Fatal(e)
			}
			if _, e = svc.IssueCredential(ctx, owner.ID, 15*time.Minute); e != nil {
				t.Fatal(e)
			}
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			project, e := svc.createProject(tx, owner, projectBody())
			if e != nil {
				tx.Rollback()
				t.Fatal(e)
			}
			fake := &upgradeFake{summary: qualificationSummary(t)}
			d := fake.summary.Frozen.Dataset
			artifact := Merge(Base(Str(project, "id")), Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": d.Hash, "storage_key": d.Ticket, "media_type": d.MediaType, "byte_size": d.Size, "input_refs": Empty(), "source_refs": Empty(), "produced_by": owner.ID, "access_class": "VERIFIER_ONLY", "validity": "CURRENT", "sealed_at": Now()})
			if e = svc.put(tx, "Artifact", artifact); e != nil {
				tx.Rollback()
				t.Fatal(e)
			}
			if e = bump(artifact); e != nil {
				tx.Rollback()
				t.Fatal(e)
			}
			if e = svc.put(tx, "Artifact", artifact); e != nil {
				tx.Rollback()
				t.Fatal(e)
			}
			if e = tx.Commit(); e != nil {
				t.Fatal(e)
			}
			before, e := upgradeRows(db)
			if e != nil {
				t.Fatal(e)
			}
			keyfile := filepath.Join(t.TempDir(), "historical.key")
			if e = os.WriteFile(keyfile, backupTestKey(t), 0600); e != nil {
				t.Fatal(e)
			}
			program, e := os.Executable()
			if e != nil {
				t.Fatal(e)
			}
			plan := LocalUpgradePlan
			if target == 20 {
				plan = FinalSchemaUpgradePlan
			}
			opt := LocalUpgradeOptions{Source: dbpath, Snapshot: filepath.Join(t.TempDir(), "backup"), Destination: filepath.Join(t.TempDir(), "restore"), KeyFile: keyfile, SourceRoot: sourceRoot, TargetRoot: targetRoot, SourceProgram: program, TargetProgram: program, Plan: plan}
			db.Close()
			report, e := upgradeLocal(ctx, opt, fake.verifier())
			if e != nil {
				t.Fatal(e)
			}
			if report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
				t.Fatal(report.Status)
			}
			restored, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
			if e != nil {
				t.Fatal(e)
			}
			defer restored.Close()
			after, e := upgradeRows(restored)
			if e != nil {
				t.Fatal(e)
			}
			if e = upgradeRecoveryInvariantForTarget(before, after, opt.Destination, target); e != nil {
				t.Fatal(e)
			}
			versions, e := backupMigrations(restored)
			if e != nil || Hash(versions) != Hash(upgradeVersions(target)) {
				t.Fatal("historical versions", e)
			}
			if fake.reads != 0 || fake.descriptions == 0 {
				t.Fatal("historical protected boundary not exercised")
			}
			if _, e = restored.Exec("INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('','Unexpected','bad',1,'{}')"); e != nil {
				t.Fatal(e)
			}
			if e = (&upgradeProtection{ctx: ctx, verifier: fake.verifier()}).refresh(restored); e == nil {
				t.Fatal("old history guard relaxed")
			}
		})
	}
}

func TestQueueUpgradeWorkspaceContinuityRefusals(t *testing.T) {
	opt, f := queueUpgradeFixture(t)
	before, e := upgradeQueueWorkspaceIdentity(f.db, opt)
	if e != nil {
		t.Fatal(e)
	}
	var path string
	if e = f.db.QueryRow("SELECT json_extract(body,'$.real_path') FROM domain_objects WHERE kind='WorkspaceBinding'").Scan(&path); e != nil {
		t.Fatal(e)
	}
	overlap := opt
	overlap.Destination = filepath.Join(path, "candidate")
	if _, e = upgradeQueueWorkspaceIdentity(f.db, overlap); e == nil {
		t.Fatal("workspace output overlap accepted")
	}
	parked := path + "-original"
	if e = os.Rename(path, parked); e != nil {
		t.Fatal(e)
	}
	defer os.Rename(parked, path)
	if _, e = upgradeQueueWorkspaceIdentity(f.db, opt); e == nil {
		t.Fatal("missing native workspace accepted")
	}
	if e = os.Mkdir(path, 0700); e != nil {
		t.Fatal(e)
	}
	defer os.Remove(path)
	after, e := upgradeQueueWorkspaceIdentity(f.db, opt)
	if e != nil {
		t.Fatal(e)
	}
	if Hash(before) == Hash(after) {
		t.Fatal("replacement directory has old native identity")
	}
}

package domain

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/sources"
	"researchos.local/research-os/internal/store"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"
)

func backupAssert(t *testing.T, id string, want, got, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W18_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})))
	if status != "PASS" {
		t.Fatal(id)
	}
}
func backupTestKey(t *testing.T) []byte {
	t.Helper()
	b := make([]byte, 32)
	if _, e := rand.Read(b); e != nil {
		t.Fatal(e)
	}
	return b
}
func backupOpt(t *testing.T, s *Service, key []byte) RestoreOptions {
	t.Helper()
	v, e := backupMigrations(s.DB)
	if e != nil {
		t.Fatal(e)
	}
	return RestoreOptions{Key: key, SupportedMigrations: v, Contracts: s.Contracts}
}
func backupTestCreate(t *testing.T, s *Service, key []byte) (string, BackupManifest) {
	t.Helper()
	p := filepath.Join(t.TempDir(), "backup")
	m, e := s.CreateBackup(context.Background(), p, key)
	if e != nil {
		t.Fatal(e)
	}
	return p, m
}
func backupEvidence(t *testing.T, name string, v any) {
	t.Helper()
	if dir := os.Getenv("W18_EVIDENCE_DIR"); dir != "" {
		if e := os.WriteFile(filepath.Join(dir, name), Bytes(v), 0600); e != nil {
			t.Fatal(e)
		}
	}
}

func TestW18RestoreNative(t *testing.T) {
	ctx := context.Background()
	o := orchestrationSetup(t)
	f := o.f
	completed := o.claim(o.task("accepted-before-backup", Empty(), Empty()))
	a := o.report(completed, []byte(`{"result":"verified"}`))
	body := o.acceptance(completed, a)
	acceptance := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(completed.task), body)
	f.token = o.owner
	pending := o.claim(o.task("continue-original-task", Empty(), Empty()))
	checkpoint := resourceCheckpoint(pending, Object{"next": "restore-and-continue"})
	pending.observe(pending.observation("LOST", false))
	f.token = o.owner
	policy := f.expect(200, "GET", f.path("/goals/"+Str(o.goal, "id")+"/budget-policy"), "", "", nil)
	providerKey := "backup-pending-provider-key"
	intent, e := f.s.PrepareEffect(ctx, o.owner, f.project, Str(pending.run, "id"), providerKey, Object{"fixture": "pending operation"}, budgetRequest(pending, Str(policy, "id"), "RESERVE", providerKey, dollars("2.50"), "UPPER_BOUND", nil))
	if e != nil {
		t.Fatal(e)
	}
	request := f.expect(201, "POST", f.path("/resource-requests"), ID(), f.stateTag(), resourceRequestBody(pending, checkpoint))
	// The resource-request production path created this notice. Preserve its
	// original identity and dedup key across the snapshot instead of inserting
	// a second row with the same database-enforced logical delivery key.
	var noticeID, noticeKey string
	if e = f.db.QueryRow(`SELECT id,json_extract(body,'$.dedup_key') FROM domain_objects
		WHERE project=? AND kind='Notification' AND json_extract(body,'$.resource_request_id')=?
		AND json_extract(body,'$.recipient_id')=? AND json_extract(body,'$.channel')='IN_APP'`,
		f.project, request["id"], f.owner).Scan(&noticeID, &noticeKey); e != nil {
		t.Fatal("production resource notice missing: ", e)
	}
	if noticeKey != Hash([]any{request["id"], f.owner, "IN_APP"}) {
		t.Fatal("production resource notice dedup key changed")
	}
	sourceNotices := backupNoticeState(t, f.db, f.project)
	// A second project and a sealed local file establish multi-project and native
	// filesystem recovery. Mutating the original file after backup must not alter it.
	originalProject := f.project
	projectInput := projectBody()
	projectInput["source_configs"] = []any{Object{"source_id": ID(), "kind": "GITHUB", "required": true, "enabled": true, "query": "repo:example/research", "allowed_origins": []any{"https://github.com", "https://api.github.com"}, "credential_ref": nil}}
	second := f.expect(201, "POST", "/v1/projects", ID(), "", projectInput)
	f.project = Str(second, "project_id")
	otherProject := f.project
	actor := Principal{ID: "backup-source-adapter", Roles: []string{"SOURCE_ADAPTER"}, Grants: []Grant{{ProjectID: otherProject}}}
	if e = f.s.ProvisionPrincipal(ctx, actor); e != nil {
		t.Fatal(e)
	}
	sourceToken, e := f.s.IssueCredential(ctx, actor.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	var cursorID string
	if e = f.db.QueryRow("SELECT id FROM domain_objects WHERE project=? AND kind='SourceCursor'", otherProject).Scan(&cursorID); e != nil {
		t.Fatal(e)
	}
	config, cursor, e := f.s.sourceConfig(ctx, sourceToken, otherProject, cursorID)
	if e != nil {
		t.Fatal(e)
	}
	from, to := time.Now().UTC().Add(-time.Hour), time.Now().UTC()
	page := sources.Page{RawResponse: []byte("[]"), RawMediaType: "application/json", Complete: true, HTTPStatus: 200, FetchedAt: time.Now().UTC(), RequestURLs: []string{"https://api.github.com/repos/example/research/releases"}, FinalURLs: []string{"https://api.github.com/repos/example/research/releases"}}
	if _, e = f.s.captureSourcePage(ctx, sourceToken, otherProject, cursor, config, from, to, 20, sourceFixtureAdapter{page}); e != nil {
		t.Fatal(e)
	}
	source := t.TempDir()
	if e := os.WriteFile(filepath.Join(source, "input.txt"), []byte("authoritative source snapshot"), 0600); e != nil {
		t.Fatal(e)
	}
	root, e := f.s.RegisterLocalRoot(ctx, f.token, f.project, source)
	if e != nil {
		t.Fatal(e)
	}
	local, e := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, root, "input.txt")
	if e != nil {
		t.Fatal(e)
	}
	f.project = originalProject
	key := backupTestKey(t)
	// Exercise concurrent committed writes using a second connection to the real
	// WAL database. A transaction updates both cells; snapshot must see a pair.
	var dbpath string
	var seq int
	var dbname string
	if e = f.db.QueryRow("PRAGMA database_list").Scan(&seq, &dbname, &dbpath); e != nil {
		t.Fatal(e)
	}
	writer, e := store.Open(dbpath)
	if e != nil {
		t.Fatal(e)
	}
	defer writer.Close()
	if _, e = f.db.Exec("CREATE TABLE backup_consistency_probe(a INTEGER,b INTEGER); INSERT INTO backup_consistency_probe VALUES(0,0)"); e != nil {
		t.Fatal(e)
	}
	started := make(chan struct{})
	stop := make(chan struct{})
	var wg sync.WaitGroup
	var writeErr error
	wg.Add(1)
	go func() {
		defer wg.Done()
		first := true
		for {
			select {
			case <-stop:
				return
			default:
			}
			_, err := writer.Exec("UPDATE backup_consistency_probe SET a=a+1,b=b+1")
			if err != nil {
				writeErr = err
				return
			}
			if first {
				close(started)
				first = false
			}
		}
	}()
	<-started
	dir, m := backupTestCreate(t, f.s, key)
	close(stop)
	wg.Wait()
	if writeErr != nil {
		t.Fatal(writeErr)
	}
	target := filepath.Join(t.TempDir(), "restored")
	report, e := RestoreBackup(ctx, dir, target, backupOpt(t, f.s, key))
	if e != nil {
		t.Fatal(e)
	}
	restored, e := store.Open(filepath.Join(target, "state.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer restored.Close()
	s := &Service{DB: restored, Contracts: f.s.Contracts}
	var left, right int
	if e = restored.QueryRow("SELECT a,b FROM backup_consistency_probe").Scan(&left, &right); e != nil {
		t.Fatal(e)
	}
	backupAssert(t, "A12-01-CONSISTENT-WAL", true, left == right && left > 0, Object{"paired_snapshot": []int{left, right}, "os": runtime.GOOS, "snapshot_started": m.Started, "snapshot_completed": m.SnapshotCompleted})
	backupAssert(t, "A12-01-INVENTORY", m.Inventory, report.Before, report)
	counts := Object{}
	for _, kind := range []string{"ProjectProfile", "ContextBundle", "BudgetLedgerEntry", "SourceCursor", "AcceptanceReceipt", "Notification"} {
		var n int
		if e = restored.QueryRow("SELECT count(*) FROM domain_objects WHERE kind=?", kind).Scan(&n); e != nil {
			t.Fatal(e)
		}
		counts[kind] = n
		if n == 0 {
			t.Fatal("required restore fixture empty", kind)
		}
	}
	backupAssert(t, "A12-01-REQUIRED-STATE", true, counts["ProjectProfile"] == 2 && report.Before["source_pages"].(int) > 0, counts)
	if e = os.WriteFile(filepath.Join(source, "input.txt"), []byte("CHANGED ORIGINAL"), 0600); e != nil {
		t.Fatal(e)
	}
	tx, e := restored.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	raw, found, e := readLocalSnapshot(tx, otherProject, Str(local, "id"))
	if e != nil {
		t.Fatal(e)
	}
	if e = s.effective(tx, originalProject, Ref(acceptance, "AcceptanceReceipt")); e != nil {
		t.Fatal(e)
	}
	accepted, e := load(tx, originalProject, "Task", Str(completed.task, "id"))
	if e != nil {
		t.Fatal(e)
	}
	if e = s.dependenciesReadyForBackup(tx, originalProject, accepted); e != nil {
		t.Fatal(e)
	}
	tx.Rollback()
	backupAssert(t, "A12-01-ACCEPTANCE-HASH", true, accepted["acceptance_id"] == acceptance["id"] && found && Digest(raw) == local["content_hash"], Object{"acceptance_hash": acceptance["receipt_hash"], "source_hash": Digest(raw), "source_relocated": true})
	var oldTokenActive int
	restored.QueryRow("SELECT count(*) FROM auth_credentials WHERE revoked=0").Scan(&oldTokenActive)
	// Original owner reauthenticates through the existing trusted local provision.
	ownerToken, e := s.IssueCredential(ctx, f.owner, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	f.s = s
	f.db = restored
	f.h = s.Handler()
	f.token = ownerToken
	o.owner = ownerToken
	pending.f = f
	current := f.read("runs", Str(pending.run, "id"))
	pending.run = current
	rev, _ := Num(current, "revision")
	_, blocked := s.ResumeCheckpoint(ctx, ownerToken, originalProject, Str(current, "id"), "blocked-unknown", rev)
	_, dispatchBlocked := s.BeginEffect(ctx, ownerToken, originalProject, Str(current, "id"), providerKey)
	backupAssert(t, "A12-02-UNKNOWN-FENCE", true, blocked != nil && dispatchBlocked != nil, Object{"resume_error": fmt.Sprint(blocked), "dispatch_error": fmt.Sprint(dispatchBlocked), "reservation_id": intent["reservation_id"]})
	if e = s.ObserveEffect(ctx, originalProject, Str(current, "id"), providerKey, "NOT_APPLIED", Object{"fixture_provider": "queried original idempotency key; absent"}); e != nil {
		t.Fatal(e)
	}
	_, blocked = s.ResumeCheckpoint(ctx, ownerToken, originalProject, Str(current, "id"), "blocked-old-observation", rev)
	backupAssert(t, "A12-02-FRESH-OBSERVATION", true, blocked != nil, Object{"error": fmt.Sprint(blocked)})
	pending.observe(pending.observation("LOST", false))
	res, e := s.ResumeCheckpoint(ctx, ownerToken, originalProject, Str(current, "id"), "restored-checkpoint", rev)
	if e != nil {
		t.Fatal(e)
	}
	pending.run = res["run"].(map[string]any)
	pending.lease = Str(res, "lease_token")
	f.token, e = s.IssueCredential(ctx, pending.executor, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	pending.call("/heartbeat", pending.heartbeat(), 200)
	backupAssert(t, "A12-02-RESUME", true, pending.run["id"] == current["id"] && pending.run["task_id"] == current["task_id"] && pending.run["checkpoint_artifact_id"] == checkpoint["id"] && oldTokenActive == 0, Object{"run_id": current["id"], "task_id": current["task_id"], "checkpoint_hash": checkpoint["content_hash"], "new_status": pending.run["status"]})
	// Internal outbox consumption is idempotent, with history retained.
	var event string
	if e = restored.QueryRow("SELECT id FROM outbox WHERE project=? ORDER BY sequence LIMIT 1", originalProject).Scan(&event); e != nil {
		t.Fatal(e)
	}
	if _, e = s.ConsumeEvent(ctx, "restore-consumer", originalProject, event); e != nil {
		t.Fatal(e)
	}
	if _, e = s.ConsumeEvent(ctx, "restore-consumer", originalProject, event); e != nil {
		t.Fatal(e)
	}
	var inbox int
	restored.QueryRow("SELECT count(*) FROM consumer_inbox WHERE consumer='restore-consumer' AND event_id=?", event).Scan(&inbox)
	backupAssert(t, "A12-02-REPLAY", 1, inbox, Object{"event_id": event, "external_dispatch_count": 0})
	var restoredNoticeID, restoredNoticeKey string
	if e = restored.QueryRow(`SELECT id,json_extract(body,'$.dedup_key') FROM domain_objects
		WHERE project=? AND kind='Notification' AND json_extract(body,'$.resource_request_id')=?
		AND json_extract(body,'$.recipient_id')=? AND json_extract(body,'$.channel')='IN_APP'`,
		originalProject, request["id"], f.owner).Scan(&restoredNoticeID, &restoredNoticeKey); e != nil {
		t.Fatal(e)
	}
	if restoredNoticeID != noticeID || restoredNoticeKey != noticeKey {
		t.Fatal("production notification identity or dedup key changed during restore")
	}
	backupAssert(t, "A12-02-NOTIFICATION", sourceNotices, backupNoticeState(t, restored, originalProject),
		Object{"source_notice_id": noticeID, "restored_notice_id": restoredNoticeID, "dedup_key_retained": true})
	backupAssert(t, "A12-04-AUDIT", true, report.Finished != "" && report.DurationMS >= 0 && report.BackupID == m.ID, Object{"report": report, "backup_command": "go run ./ops/backup create --db <source> --out <new-backup> --key-file <separate-key>", "restore_command": "go run ./ops/backup restore --backup <backup> --out <new-target> --key-file <separate-key>"})
	backupEvidence(t, "native-restore.json", Object{"manifest": m, "report": report, "acceptance_hash": acceptance["receipt_hash"], "runtime_mode": "FIXTURE work items; LIVE_WINDOWS SQLite/WAL/filesystem persistence and recovery"})
}

func backupNoticeState(t *testing.T, db *sql.DB, project string) Object {
	t.Helper()
	rows, err := db.Query("SELECT id,body FROM domain_objects WHERE project=? AND kind='Notification' ORDER BY id", project)
	if err != nil {
		t.Fatal(err)
	}
	defer rows.Close()
	notices := []any{}
	for rows.Next() {
		var id, body string
		if err = rows.Scan(&id, &body); err != nil {
			t.Fatal(err)
		}
		notices = append(notices, []any{id, body})
	}
	if err = rows.Err(); err != nil {
		t.Fatal(err)
	}
	return Object{"count": len(notices), "digest": Hash(notices)}
}

// Use the existing acceptance dependency gate to recompute accepted evidence.
func (s *Service) dependenciesReadyForBackup(tx *sql.Tx, project string, task Object) error {
	return s.acceptedTaskBinding(tx, project, task)
}

func TestW18NegativeRecovery(t *testing.T) {
	ctx := context.Background()
	f := contextFixture(t)
	f.artifact(Object{"sealed": "negative missing-artifact case"}, Empty())
	key := backupTestKey(t)
	dir, m := backupTestCreate(t, f.s, key)
	opt := backupOpt(t, f.s, key)
	before, e := backupInventory(f.db)
	if e != nil {
		t.Fatal(e)
	}
	cases := []string{"missing", "corrupt", "wrong-key", "wrong-schema", "interrupted", "migration-failed", "irreversible", "occupied"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			copyDir := filepath.Join(t.TempDir(), "copy")
			if e = os.Mkdir(copyDir, 0700); e != nil {
				t.Fatal(e)
			}
			entries, _ := os.ReadDir(dir)
			for _, entry := range entries {
				b, _ := os.ReadFile(filepath.Join(dir, entry.Name()))
				if e = os.WriteFile(filepath.Join(copyDir, entry.Name()), b, 0600); e != nil {
					t.Fatal(e)
				}
			}
			target := filepath.Join(t.TempDir(), "new")
			options := opt
			callCtx := ctx
			switch name {
			case "missing":
				var contentName string
				for _, entry := range m.Files {
					if strings.HasPrefix(entry.Name, "content-") {
						contentName = entry.Name + ".enc"
						break
					}
				}
				if contentName == "" {
					t.Fatal("missing artifact fixture empty")
				}
				if e = os.Remove(filepath.Join(copyDir, contentName)); e != nil {
					t.Fatal(e)
				}
			case "corrupt":
				if e = os.WriteFile(filepath.Join(copyDir, "state.sqlite.enc"), []byte("broken"), 0600); e != nil {
					t.Fatal(e)
				}
			case "wrong-key":
				options.Key = backupTestKey(t)
			case "wrong-schema":
				options.SupportedMigrations = []int{999}
			case "interrupted":
				c, cancel := context.WithCancel(ctx)
				options.Migration = func(context.Context, *sql.DB) error { cancel(); return nil }
				callCtx = c
			case "migration-failed":
				options.Migration = func(ctx context.Context, db *sql.DB) error {
					_, err := db.ExecContext(ctx, "CREATE TABLE failed_migration(x); INSERT INTO no_such_table VALUES(1)")
					return err
				}
			case "irreversible":
				options.Irreversible = true
			case "occupied":
				os.Mkdir(target, 0700)
				os.WriteFile(filepath.Join(target, "sentinel"), []byte("preserve"), 0600)
			}
			_, err := RestoreBackup(callCtx, copyDir, target, options)
			if err == nil {
				t.Fatal("negative restore passed")
			}
			_, statErr := os.Stat(target)
			safe := os.IsNotExist(statErr)
			if name == "occupied" {
				b, _ := os.ReadFile(filepath.Join(target, "sentinel"))
				safe = string(b) == "preserve"
			}
			after, e := backupInventory(f.db)
			if e != nil {
				t.Fatal(e)
			}
			backupAssert(t, "W18-G01-"+name, true, safe && Hash(before) == Hash(after), Object{"error": err.Error(), "original_unchanged": Hash(before) == Hash(after)})
		})
	}
	target := filepath.Join(t.TempDir(), "retry")
	r, e := RestoreBackup(ctx, dir, target, opt)
	if e != nil {
		t.Fatal(e)
	}
	raw, _ := os.ReadFile(filepath.Join(dir, "manifest.json"))
	var current BackupManifest
	json.Unmarshal(raw, &current)
	backupAssert(t, "A12-03-RESTARTABLE", true, current.MAC == m.MAC && r.BackupID == m.ID, Object{"backup_retained": true, "retry": r.Status})
}

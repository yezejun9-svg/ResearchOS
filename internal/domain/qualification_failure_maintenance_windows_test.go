//go:build windows

package domain

import (
	"context"
	"database/sql"
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"

	"golang.org/x/sys/windows"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/store"
)

// This fixture exercises the read-only recovery classifier against a real
// schema-24 WAL database. It does not emulate the boot witness or authorize
// ApplyHistoricalQualification.
func qualificationClassifierFixture(t *testing.T) (*sql.DB, HistoricalQualificationPlan, string) {
	t.Helper()
	root := t.TempDir()
	path := filepath.Join(root, "researchos.sqlite")
	u := url.URL{Scheme: "file", Opaque: filepath.ToSlash(path)}
	q := u.Query()
	q.Set("mode", "rwc")
	u.RawQuery = q.Encode()
	initial, e := sql.Open("sqlite", u.String())
	if e != nil {
		t.Fatal(e)
	}
	if _, e = initial.Exec("PRAGMA journal_mode=WAL"); e != nil {
		t.Fatal(e)
	}
	files, e := filepath.Glob(filepath.Join("..", "..", "migrations", "sqlite", "[0-9][0-9][0-9][0-9]_*.sql"))
	if e != nil || len(files) != 24 {
		t.Fatalf("migration inventory %d: %v", len(files), e)
	}
	sort.Strings(files)
	for i, file := range files {
		raw, err := os.ReadFile(file)
		if err != nil {
			t.Fatal(err)
		}
		if _, err = initial.Exec(string(raw)); err != nil {
			t.Fatalf("migration %s: %v", file, err)
		}
		if _, err = initial.Exec(`INSERT INTO schema_migrations(version) VALUES(?)`, i+1); err != nil {
			t.Fatal(err)
		}
	}
	extra, e := os.ReadFile(filepath.Join("..", "..", "migrations", "sqlite", "next_v24_sessions.sql"))
	if e != nil {
		t.Fatal(e)
	}
	if _, e = initial.Exec(string(extra)); e != nil {
		t.Fatal(e)
	}
	if _, e = initial.Exec(`CREATE TABLE IF NOT EXISTS backup_restore_barriers(project TEXT NOT NULL,run TEXT NOT NULL,restored_at TEXT NOT NULL,PRIMARY KEY(project,run))`); e != nil {
		t.Fatal(e)
	}
	if e = initial.Close(); e != nil {
		t.Fatal(e)
	}
	db, e := store.OpenQualificationMaintenance(context.Background(), path)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { _ = db.Close() })
	if _, e = db.Exec(`INSERT INTO auth_principals(id,roles) VALUES('owner','["OWNER"]')`); e != nil {
		t.Fatal(e)
	}
	project := "project"
	profile := Object{"id": "profile", "project_id": project, "revision": int64(1)}
	runBefore := Object{"id": "run", "project_id": project, "revision": int64(1), "status": "RUNNING"}
	stateBefore := Object{"id": "state", "project_id": project, "revision": int64(1)}
	for _, entry := range []struct {
		kind   string
		object Object
	}{{"ProjectProfile", profile}, {"Run", runBefore}, {"ProjectState", stateBefore}} {
		raw := string(Bytes(entry.object))
		if _, e = db.Exec(`INSERT INTO domain_versions(project,kind,id,revision,body) VALUES(?,?,?,?,?)`, project, entry.kind, entry.object["id"], 1, raw); e != nil {
			t.Fatal(e)
		}
		if _, e = db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,?,?,?,?)`, project, entry.kind, entry.object["id"], 1, raw); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = db.Exec(`INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at)
		VALUES('project','run',1,'dispatch','{}','manifest','STARTED','2026-10-25T00:00:00Z','2026-10-25T00:00:00Z')`); e != nil {
		t.Fatal(e)
	}
	profileRef := Object{"entity_type": "ProjectProfile", "id": "profile", "revision": int64(1)}
	proofBytes := []byte("historical fixture proof")
	artifact := Object{"id": "artifact", "project_id": project, "revision": int64(1), "content_hash": Digest(proofBytes)}
	link := Object{"id": "link", "project_id": project, "revision": int64(1)}
	run := Object{"id": "run", "project_id": project, "revision": int64(2), "status": "FAILED"}
	state := Object{"id": "state", "project_id": project, "revision": int64(2)}
	event := Object{"id": "event", "project_id": project, "revision": int64(1)}
	event["receipt_hash"] = Receipt(event)
	plan := HistoricalQualificationPlan{
		Schema:      "researchos.qualification-failure-maintenance-full-plan.v1",
		OperationID: "00112233445566778899aabbccddeeff",
		Subject:     HistoricalQualificationSubject{ProjectID: project, RunID: "run", Epoch: 1, DispatchKey: "dispatch"},
		AuthorID:    "owner", UploadKey: "upload", EventSequence: 1, DispatchSequence: 1,
		Core: Object{"profile_ref": profileRef}, Artifact: artifact, ImpactLink: link, Run: run,
		ProjectState: state, Event: event, Observation: Object{"state": "FAILED"},
		ProofBytes: proofBytes, ObservedAt: "2026-10-25T00:00:01Z", ExpiresAt: "2026-10-25T01:00:00Z",
		BeforeRun: runBefore, BeforeState: stateBefore, BeforeDispatch: Object{"manifest_hash": "manifest"},
		OutcomeHash: Hash(Object{"outcome": "fixture"}),
	}
	tx, e := db.BeginTx(context.Background(), &sql.TxOptions{ReadOnly: true})
	if e != nil {
		t.Fatal(e)
	}
	plan.BeforeDispatchRow, e = historicalQualificationReadDispatchRow(context.Background(), tx, plan.Subject)
	if e != nil {
		t.Fatal(e)
	}
	plan.BeforeCensus, e = store.QualificationMaintenanceCensus(context.Background(), tx)
	if e != nil {
		t.Fatal(e)
	}
	plan.BeforeProtectedSHA256, e = store.QualificationMaintenanceProtectedCensus(context.Background(), tx)
	if e != nil {
		t.Fatal(e)
	}
	selectors, e := plan.residualSelectors()
	if e != nil {
		t.Fatal(e)
	}
	plan.BeforeResidualSHA256, e = store.QualificationMaintenanceResidualCensus(context.Background(), tx, selectors)
	if e != nil {
		t.Fatal(e)
	}
	if e = tx.Rollback(); e != nil {
		t.Fatal(e)
	}
	return db, plan, "sha256:1111111111111111111111111111111111111111111111111111111111111111"
}

func TestHistoricalQualificationNativeThreeFrameHold(t *testing.T) {
	user, e := windows.GetCurrentProcessToken().GetTokenUser()
	if e != nil || user == nil || user.User.Sid == nil {
		t.Fatalf("current SID: %v", e)
	}
	sid := user.User.Sid.String()
	for _, mode := range []string{"exact", "tool_changed", "suffix", "raw_missing"} {
		t.Run(mode, func(t *testing.T) {
			root := t.TempDir()
			directory := filepath.Join(root, "runtime-dispatches", "00112233445566778899aabbccddeeff")
			if e := os.MkdirAll(filepath.Join(directory, "input"), 0700); e != nil {
				t.Fatal(e)
			}
			if e := os.WriteFile(filepath.Join(directory, "owner.lock"), nil, 0600); e != nil {
				t.Fatal(e)
			}
			manifest := Bytes(Object{"run_id": "run", "task_id": "task", "epoch": int64(1),
				"admission": Object{"profile": Object{"outputs": Empty()}}})
			manifestHash := Digest(manifest)
			frames := []rt.BridgeFrame{
				{Sequence: 1, Type: "context.ready", Payload: json.RawMessage(`{}`)},
				{Sequence: 2, Type: "effect.request", Key: "model-key", Route: "model-fixture", Capability: "MODEL", Payload: json.RawMessage(`{}`)},
				{Sequence: 3, Type: "effect.request", Key: "tool-key", Route: "model-fixture", Capability: "TOOL", Payload: json.RawMessage(`{}`)},
			}
			if mode == "tool_changed" {
				frames[2].Capability = "MODEL"
			}
			if mode == "suffix" {
				frames = append(frames, rt.BridgeFrame{Sequence: 4, Type: "effect.request", Key: "suffix", Route: "model-fixture", Capability: "TOOL", Payload: json.RawMessage(`{}`)})
			}
			var stdout []byte
			for _, frame := range frames {
				raw, err := json.Marshal(frame)
				if err != nil {
					t.Fatal(err)
				}
				stdout = append(stdout, raw...)
				stdout = append(stdout, '\n')
			}
			j := rt.BridgeJournal{Version: 1, Manifest: json.RawMessage(manifest), ManifestHash: manifestHash,
				DispatchKey: "00112233445566778899aabbccddeeff", Worker: "fixture",
				State: "FAILED", Reason: "qualification first dispatch gate denied TOOL",
				Ended: "2026-10-25T00:00:00Z", Frames: int64(len(frames)), Acknowledged: 2,
				StdoutHash: Digest(stdout), StderrHash: Digest(nil)}
			j.Receipt.Stopped = true
			j.Receipt.StreamsDrained = true
			j.Receipt.CleanupComplete = true
			j.Receipt.OutputCopied = true
			j.Receipt.ExitCode = 124
			j.Receipt.TimedOut = true
			j.Receipt.JobProcesses = 2
			bridgeRaw, e := json.Marshal(j)
			if e != nil {
				t.Fatal(e)
			}
			staged := map[string][]byte{"worker.exe": []byte("worker"), "mu-worker.mjs": []byte("bundle"),
				"worker.json": []byte("{}"), "request.json": []byte("{}")}
			for name, raw := range staged {
				if e = os.WriteFile(filepath.Join(directory, "input", name), raw, 0600); e != nil {
					t.Fatal(e)
				}
			}
			modelName := "effect-" + strings.TrimPrefix(Digest([]byte("model-key")), "sha256:") + ".json"
			for name, raw := range map[string][]byte{"bridge.json": bridgeRaw, "stdout.raw": stdout,
				"stderr.raw": nil, modelName: []byte(`{"model":"fixture"}`)} {
				if mode == "raw_missing" && name == "stdout.raw" {
					continue
				}
				if e = os.WriteFile(filepath.Join(directory, name), raw, 0600); e != nil {
					t.Fatal(e)
				}
			}
			source := HistoricalQualificationSource{BridgeSHA256: Digest(bridgeRaw), StdoutSHA256: Digest(stdout),
				StderrSHA256: Digest(nil), ManifestHash: manifestHash, WorkerSHA256: Digest(staged["worker.exe"]),
				BundleSHA256: Digest(staged["mu-worker.mjs"]), WorkerConfigSHA256: Digest(staged["worker.json"]),
				RequestSHA256: Digest(staged["request.json"])}
			facts, hold, err := holdHistoricalQualificationNative(directory, manifestHash, "model-key", sid, source)
			if mode == "exact" {
				if err != nil {
					t.Fatal(err)
				}
				if facts.stdoutHash != source.StdoutSHA256 || facts.stderrHash != source.StderrSHA256 {
					t.Fatal("raw hashes changed")
				}
				if err = hold.Check(); err != nil {
					t.Fatal(err)
				}
				if err = os.Rename(filepath.Join(directory, "stdout.raw"), filepath.Join(directory, "moved.raw")); err == nil {
					t.Fatal("held raw stdout renamed")
				}
				if err = hold.Close(); err != nil {
					t.Fatal(err)
				}
				if err = os.Rename(filepath.Join(directory, "stdout.raw"), filepath.Join(directory, "moved.raw")); err != nil {
					t.Fatal(err)
				}
			} else {
				if hold != nil {
					_ = hold.Close()
				}
				if err == nil {
					t.Fatalf("%s synthetic mutation admitted", mode)
				}
			}
		})
	}
}

func TestHistoricalQualificationPrivateNativeHoldThroughSQLReturn(t *testing.T) {
	token := windows.GetCurrentProcessToken()
	user, e := token.GetTokenUser()
	if e != nil || user == nil || user.User.Sid == nil {
		t.Fatalf("current SID: %v", e)
	}
	sid := user.User.Sid.String()
	for _, outcome := range []string{"commit", "rollback"} {
		t.Run(outcome, func(t *testing.T) {
			root := t.TempDir()
			source := filepath.Join(root, "raw.json")
			if e := os.WriteFile(source, []byte(`{"source":"fixture"}`), 0600); e != nil {
				t.Fatal(e)
			}
			ownerPath := filepath.Join(root, "owner.lock")
			owner, e := os.OpenFile(ownerPath, os.O_CREATE|os.O_RDWR, 0600)
			if e != nil {
				t.Fatal(e)
			}
			hold := &historicalQualificationHold{owner: owner}
			f, e := hold.add(source, false, true, sid)
			if e != nil {
				t.Fatal(e)
			}
			if _, e = historicalNativeRead(f, 1024, false); e != nil {
				t.Fatal(e)
			}
			database := filepath.Join(root, "tx.sqlite")
			db, e := sql.Open("sqlite", database)
			if e != nil {
				t.Fatal(e)
			}
			defer db.Close()
			if _, e = db.Exec(`CREATE TABLE marker(id INTEGER PRIMARY KEY)`); e != nil {
				t.Fatal(e)
			}
			tx, e := db.BeginTx(context.Background(), nil)
			if e != nil {
				t.Fatal(e)
			}
			if _, e = tx.Exec(`INSERT INTO marker(id) VALUES(1)`); e != nil {
				t.Fatal(e)
			}
			subject := HistoricalQualificationSubject{ProjectID: "p", RunID: "r", Epoch: 1}
			model := Object{"fact": "fixture"}
			plan := HistoricalQualificationPlan{Subject: subject, AuthorID: "owner", OwnerRoot: "owner",
				Source: HistoricalQualificationSource{BridgeSHA256: "sha256:fixture"},
				Core:   Object{"fixture": true}, BeforeRun: Object{}, BeforeState: Object{}, BeforeDispatch: Object{}}
			plan.Proof = Object{"kind": historicalMaintenanceProofKind, "claim": "HOST_TOOL_EFFECT_NOT_DISPATCHED",
				"native_class": historicalMaintenanceNativeClass, "plan_hash": plan.coreHash(),
				"owner_root": "owner", "author": "owner", "model_binding": model}
			verified := verifiedHistoricalQualification{subject: subject, author: Principal{ID: "owner"}, ownerRoot: "owner",
				run: Object{}, state: Object{}, dispatch: Object{}, modelBinding: model,
				native: historicalQualificationNative{bridgeHash: "sha256:fixture"}}
			closure, e := (&Service{}).validatedHistoricalQualificationFailureTx(tx, plan, verified, hold)
			if e != nil {
				t.Fatal(e)
			}
			moved := source + ".moved"
			if e = os.Rename(source, moved); e == nil {
				t.Fatal("native evidence renamed before SQL return")
			}
			if outcome == "commit" {
				e = tx.Commit()
			} else {
				e = tx.Rollback()
			}
			if e != nil {
				t.Fatal(e)
			}
			if e = closure.Check(); e != nil {
				t.Fatalf("source hold lost after SQL %s: %v", outcome, e)
			}
			if e = os.Rename(source, moved); e == nil {
				t.Fatal("native evidence renamed before Close")
			}
			if e = closure.Close(); e != nil {
				t.Fatal(e)
			}
			if e = os.Rename(source, moved); e != nil {
				t.Fatalf("source remained locked after Close: %v", e)
			}
			if e = closure.Check(); e == nil {
				t.Fatal("closed historical closure remained live")
			}
		})
	}
}

type historicalBlockingDriver struct {
	started, release chan struct{}
	commitErr        bool
}

func (d *historicalBlockingDriver) Open(string) (driver.Conn, error) {
	return &historicalBlockingConn{owner: d}, nil
}

type historicalBlockingConn struct{ owner *historicalBlockingDriver }

func (*historicalBlockingConn) Prepare(string) (driver.Stmt, error) {
	return nil, errors.New("statement outside fixture")
}
func (*historicalBlockingConn) Close() error { return nil }
func (c *historicalBlockingConn) Begin() (driver.Tx, error) {
	return &historicalBlockingTx{owner: c.owner}, nil
}
func (c *historicalBlockingConn) BeginTx(context.Context, driver.TxOptions) (driver.Tx, error) {
	return c.Begin()
}

type historicalBlockingTx struct{ owner *historicalBlockingDriver }

func (tx *historicalBlockingTx) Commit() error {
	close(tx.owner.started)
	<-tx.owner.release
	if tx.owner.commitErr {
		return errors.New("injected driver commit failure")
	}
	return nil
}
func (tx *historicalBlockingTx) Rollback() error {
	close(tx.owner.started)
	<-tx.owner.release
	return nil
}

func TestHistoricalQualificationNativeHoldWaitsForDriverRollbackAndCommitError(t *testing.T) {
	user, err := windows.GetCurrentProcessToken().GetTokenUser()
	if err != nil || user == nil || user.User.Sid == nil {
		t.Fatalf("current SID: %v", err)
	}
	for _, mode := range []string{"cancel_rollback", "commit_error"} {
		t.Run(mode, func(t *testing.T) {
			root := t.TempDir()
			source := filepath.Join(root, "raw.json")
			if err := os.WriteFile(source, []byte(`{"source":"fixture"}`), 0600); err != nil {
				t.Fatal(err)
			}
			owner, err := os.OpenFile(filepath.Join(root, "owner.lock"), os.O_CREATE|os.O_RDWR, 0600)
			if err != nil {
				t.Fatal(err)
			}
			hold := &historicalQualificationHold{owner: owner}
			defer hold.Close()
			f, err := hold.add(source, false, true, user.User.Sid.String())
			if err != nil {
				t.Fatal(err)
			}
			if _, err := historicalNativeRead(f, 1024, false); err != nil {
				t.Fatal(err)
			}
			control := &historicalBlockingDriver{started: make(chan struct{}), release: make(chan struct{}), commitErr: mode == "commit_error"}
			defer func() {
				select {
				case <-control.release:
				default:
					close(control.release)
				}
			}()
			driverName := fmt.Sprintf("c57-historical-%s-%s", mode, ID())
			sql.Register(driverName, control)
			db, err := sql.Open(driverName, "")
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			tx, err := db.BeginTx(context.WithoutCancel(ctx), nil)
			if err != nil {
				t.Fatal(err)
			}
			var done <-chan error
			if mode == "cancel_rollback" {
				cancel()
				if ctx.Err() != context.Canceled {
					t.Fatal("caller cancellation not observed")
				}
				result := make(chan error, 1)
				done = result
				go func() { result <- finishHistoricalQualificationTx(tx, false, hold) }()
			} else {
				result := make(chan error, 1)
				done = result
				go func() { result <- tx.Commit() }()
			}
			select {
			case <-control.started:
			case <-time.After(5 * time.Second):
				t.Fatal("driver transaction did not reach blocking return")
			}
			moved := source + ".moved"
			if err := os.Rename(source, moved); err == nil {
				t.Fatal("native source released before driver returned")
			}
			close(control.release)
			select {
			case err := <-done:
				if mode == "cancel_rollback" && err != nil {
					t.Fatal(err)
				}
				if mode == "commit_error" && (err == nil || !strings.Contains(err.Error(), "injected driver commit failure")) {
					t.Fatalf("driver failure not delivered: %v", err)
				}
			case <-time.After(5 * time.Second):
				t.Fatal("driver transaction did not return")
			}
			if mode == "commit_error" {
				if err := os.Rename(source, moved); err == nil {
					t.Fatal("native source released before caller failure cleanup")
				}
				_ = finishHistoricalQualificationTx(tx, false, hold)
			}
			if err := os.Rename(source, moved); err != nil {
				t.Fatalf("native source remained locked after transaction cleanup: %v", err)
			}
		})
	}
}

// The private writer is exercised with valid domain objects from the existing
// fixture service. The synthetic dispatch and proof bypass the historical
// native constructor; this test proves only its planned SQL write set.
func TestHistoricalQualificationPlannedWriterFiveVersions(t *testing.T) {
	_, route, r, _ := qualificationFailureLoopbackFixture(t)
	ctx := context.Background()
	runID := Str(r.run, "id")
	taskID := Str(r.task, "id")
	epoch, e := Num(r.run, "lease_epoch")
	if e != nil {
		t.Fatal(e)
	}
	var seq int
	var name, database string
	if e = r.f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &database); e != nil {
		t.Fatal(e)
	}
	root := filepath.Dir(database)
	var dispatchKey string
	if e = r.f.db.QueryRow(`SELECT dispatch_key FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?`,
		r.f.project, runID, epoch).Scan(&dispatchKey); e != nil {
		t.Fatal(e)
	}
	if _, e = r.f.db.Exec(`UPDATE runtime_dispatches SET state='STARTED',worker='fixture',journal_locator=dispatch_key,
		updated_at='2026-10-25T00:00:00Z',reason='synthetic writer fixture' WHERE project=? AND run=? AND epoch=?`,
		r.f.project, runID, epoch); e != nil {
		t.Fatal(e)
	}
	database = filepath.Join(root, "researchos.sqlite")
	if _, e = r.f.db.Exec(`VACUUM INTO ?`, database); e != nil {
		t.Fatal(e)
	}
	clone, e := sql.Open("sqlite", database)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = clone.Exec("PRAGMA journal_mode=WAL"); e != nil {
		t.Fatal(e)
	}
	if e = clone.Close(); e != nil {
		t.Fatal(e)
	}
	writerDB, e := store.OpenQualificationMaintenance(ctx, database)
	if e != nil {
		t.Fatal(e)
	}
	defer writerDB.Close()
	writerService := &Service{DB: writerDB, Contracts: r.f.s.Contracts}
	var versionsBefore, taskRevisionsBefore, ledgerBefore int
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_versions WHERE project=?`, r.f.project).Scan(&versionsBefore); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_versions WHERE project=? AND kind='Task' AND id=?`, r.f.project, taskID).Scan(&taskRevisionsBefore); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'`, r.f.project).Scan(&ledgerBefore); e != nil {
		t.Fatal(e)
	}
	beforeTx, e := writerDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if e != nil {
		t.Fatal(e)
	}
	run, e := load(beforeTx, r.f.project, "Run", runID)
	if e != nil {
		t.Fatal(e)
	}
	state, e := singleton(beforeTx, r.f.project, "ProjectState")
	if e != nil {
		t.Fatal(e)
	}
	task, e := load(beforeTx, r.f.project, "Task", taskID)
	if e != nil {
		t.Fatal(e)
	}
	dispatch, e := runtimeDispatch(beforeTx, r.f.project, runID, epoch)
	if e != nil {
		t.Fatal(e)
	}
	before, e := store.QualificationMaintenanceCensus(ctx, beforeTx)
	if e != nil {
		t.Fatal(e)
	}
	if e = beforeTx.Rollback(); e != nil {
		t.Fatal(e)
	}
	inputs := Arr(task, "input_refs")
	if len(inputs) != 1 {
		t.Fatalf("fixture profile refs %d", len(inputs))
	}
	profileRef, ok := inputs[0].(map[string]any)
	if !ok {
		t.Fatal("fixture profile ref unavailable")
	}
	subject := HistoricalQualificationSubject{ProjectID: r.f.project, TaskID: taskID, RunID: runID,
		RuntimeID: route.RuntimeID, Epoch: epoch, DispatchKey: dispatchKey}
	native := historicalQualificationNative{journal: rt.BridgeJournal{Sequence: 0, Ended: "2026-10-25T00:00:00Z"}}
	verified := verifiedHistoricalQualification{subject: subject, author: Principal{ID: r.f.owner},
		ownerRoot: r.f.owner, profileRef: Object(profileRef), run: run, task: task, state: state, dispatch: dispatch,
		observation: Object{"qualification_failure": Object{"kind": historicalMaintenanceProofKind},
			"state": "UNKNOWN", "queue_empty": false},
		modelBinding: Object{"fact_hash": Digest([]byte("synthetic-model"))}, native: native,
		source: HistoricalQualificationSource{BridgeSHA256: Digest([]byte("synthetic-bridge"))}}
	op := ID()
	boundaryHash := "1111111111111111111111111111111111111111111111111111111111111111"
	planTx, e := writerDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if e != nil {
		t.Fatal(e)
	}
	plan, e := writerService.buildHistoricalQualificationPlan(ctx, planTx, verified, op, boundaryHash, root, database, filepath.Join(root, "runtime-dispatches", dispatchKey),
		"fixture-sid", before, nil)
	rollbackErr := planTx.Rollback()
	if e != nil || rollbackErr != nil {
		t.Fatalf("plan: %v rollback: %v", e, rollbackErr)
	}
	planFileSHA256 := Digest(Bytes(plan))
	// A collision after upload insertion must roll the entire planned write
	// set back. This is a SQL cutpoint fixture, not a boot grant.
	faultTx, e := writerDB.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	if e = resourceWriteLock(faultTx); e != nil {
		t.Fatal(e)
	}
	if _, e = faultTx.Exec(`INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) VALUES(?,'Artifact',?,1,?,?)`,
		plan.Subject.ProjectID, plan.Artifact["id"], string(Bytes(plan.Artifact)), plan.Artifact["content_hash"]); e != nil {
		t.Fatal(e)
	}
	if e = writerService.applyHistoricalQualificationTx(ctx, faultTx, plan, planFileSHA256); e == nil {
		t.Fatal("version collision did not stop writer")
	}
	if e = faultTx.Rollback(); e != nil {
		t.Fatal(e)
	}
	if classified, classErr := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256); classErr != nil || classified != "NOT_APPLIED" {
		t.Fatalf("fault rollback classified %s: %v", classified, classErr)
	}
	writeTx, e := writerDB.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	if e = resourceWriteLock(writeTx); e != nil {
		t.Fatal(e)
	}
	if e = writerService.applyHistoricalQualificationTx(ctx, writeTx, plan, planFileSHA256); e != nil {
		_ = writeTx.Rollback()
		t.Fatal(e)
	}
	if e = writeTx.Commit(); e != nil {
		t.Fatal(e)
	}
	classification, e := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256)
	if e != nil || classification != "APPLIED" {
		probe, probeErr := writerDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
		if probeErr == nil {
			full, _ := store.QualificationMaintenanceCensus(ctx, probe)
			p, _ := store.QualificationMaintenanceProtectedCensus(ctx, probe)
			sel, _ := plan.residualSelectors()
			r, _ := store.QualificationMaintenanceResidualCensus(ctx, probe, sel)
			exact, exactErr := historicalQualificationExactRows(ctx, probe, plan, planFileSHA256)
			t.Logf("writer debug full=%t schema=%t protected=%t residual=%t exact=%t exactErr=%v",
				Hash(full) == Hash(plan.BeforeCensus), full.SchemaSHA256 == plan.BeforeCensus.SchemaSHA256,
				p == plan.BeforeProtectedSHA256, r == plan.BeforeResidualSHA256, exact, exactErr)
			for _, entry := range []struct {
				kind string
				obj  Object
			}{{"Artifact", plan.Artifact}, {"ImpactLink", plan.ImpactLink},
				{"Run", plan.Run}, {"ProjectState", plan.ProjectState}, {"EventEnvelope", plan.Event}} {
				rev, _ := Num(entry.obj, "revision")
				actualRefs, _ := historicalQualificationRefs(probe, plan.Subject.ProjectID, entry.kind, Str(entry.obj, "id"), rev)
				t.Logf("writer refs %s %s rev%d: %s", entry.kind, Str(entry.obj, "id"), rev, Bytes(actualRefs))
				if entry.kind == "Run" || entry.kind == "ProjectState" {
					oldRefs, _ := historicalQualificationRefs(probe, plan.Subject.ProjectID, entry.kind, Str(entry.obj, "id"), rev-1)
					t.Logf("writer old refs %s rev%d: %s", entry.kind, rev-1, Bytes(oldRefs))
				}
			}
			_ = probe.Rollback()
		}
		t.Fatalf("writer classified %s: %v", classification, e)
	}
	var versions, markers, taskRevisions, ledger int
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_versions WHERE project=?`, r.f.project).Scan(&versions); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM idempotency WHERE project=? AND operation='host:qualification-failure-maintenance'`, r.f.project).Scan(&markers); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_versions WHERE project=? AND kind='Task' AND id=?`, r.f.project, taskID).Scan(&taskRevisions); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'`, r.f.project).Scan(&ledger); e != nil {
		t.Fatal(e)
	}
	if versions != versionsBefore+5 || markers != 1 || taskRevisions != taskRevisionsBefore || ledger != ledgerBefore {
		t.Fatalf("planned five-version/marker/fence delta wrong: versions=%d/%d markers=%d task=%d/%d ledger=%d/%d",
			versionsBefore, versions, markers, taskRevisionsBefore, taskRevisions, ledgerBefore, ledger)
	}
	replayTx, e := writerDB.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	if e = resourceWriteLock(replayTx); e != nil {
		t.Fatal(e)
	}
	if e = writerService.applyHistoricalQualificationTx(ctx, replayTx, plan, planFileSHA256); e == nil {
		t.Fatal("same plan replay wrote again")
	}
	if e = replayTx.Rollback(); e != nil {
		t.Fatal(e)
	}
	if classified, classErr := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256); classErr != nil || classified != "APPLIED" {
		t.Fatalf("replay changed durable image: %s %v", classified, classErr)
	}
}

func TestHistoricalQualificationRecoveryClassificationNineTables(t *testing.T) {
	db, plan, planFileSHA256 := qualificationClassifierFixture(t)
	ctx := context.Background()
	state, e := ClassifyHistoricalQualification(ctx, db, plan, planFileSHA256)
	if e != nil || state != "NOT_APPLIED" {
		t.Fatalf("before: %s %v", state, e)
	}
	tx, e := db.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	for _, entry := range []struct {
		kind   string
		object Object
	}{{"Artifact", plan.Artifact}, {"ImpactLink", plan.ImpactLink},
		{"Run", plan.Run}, {"ProjectState", plan.ProjectState}, {"EventEnvelope", plan.Event}} {
		rev, _ := Num(entry.object, "revision")
		var content any
		immutable := 0
		if entry.kind == "Artifact" {
			content = entry.object["content_hash"]
		}
		if entry.kind == "EventEnvelope" {
			content = entry.object["receipt_hash"]
			immutable = 1
		}
		body := string(Bytes(entry.object))
		if _, e = tx.Exec(`INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) VALUES(?,?,?,?,?,?)`,
			plan.Subject.ProjectID, entry.kind, entry.object["id"], rev, body, content); e != nil {
			t.Fatal(e)
		}
		if _, e = tx.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) VALUES(?,?,?,?,?,?,?)
			ON CONFLICT(project,kind,id) DO UPDATE SET revision=excluded.revision,body=excluded.body,content_hash=excluded.content_hash`,
			plan.Subject.ProjectID, entry.kind, entry.object["id"], rev, body, content, immutable); e != nil {
			t.Fatal(e)
		}
	}
	for _, ref := range []struct {
		kind, id, field, targetKind, targetID string
		targetRevision                        int
	}{
		{"Artifact", "artifact", "/input_refs/0", "ProjectProfile", "profile", 1},
		{"ImpactLink", "link", "/from_ref", "Artifact", "artifact", 1},
		{"ImpactLink", "link", "/to_ref", "ProjectProfile", "profile", 1},
		{"EventEnvelope", "event", "/aggregate_ref", "Run", "run", 2},
	} {
		if _, e = tx.Exec(`INSERT INTO domain_refs(project,kind,id,revision,field,target_project,target_kind,target_id,target_revision)
			VALUES(?,?,?,?,?,?,?,?,?)`, plan.Subject.ProjectID, ref.kind, ref.id, 1, ref.field, plan.Subject.ProjectID,
			ref.targetKind, ref.targetID, ref.targetRevision); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = tx.Exec(`INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) VALUES(?,?,?,?,?,?,1)`,
		plan.UploadKey, plan.Subject.ProjectID, plan.AuthorID, plan.ProofBytes, Digest(plan.ProofBytes), plan.ExpiresAt); e != nil {
		t.Fatal(e)
	}
	if _, e = tx.Exec(`INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,?,?,?,?)`,
		plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch, Hash(plan.Observation), string(Bytes(plan.Observation)), plan.ObservedAt); e != nil {
		t.Fatal(e)
	}
	if _, e = tx.Exec(`UPDATE runtime_dispatches SET state='OBSERVED',observation_sequence=?,observation_hash=?,updated_at=?,reason=?
		WHERE project=? AND run=? AND epoch=?`, plan.DispatchSequence, Hash(plan.Observation), plan.ObservedAt,
		"historical qualification first-gate TOOL reconstruction "+plan.OperationID, plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch); e != nil {
		t.Fatal(e)
	}
	if _, e = tx.Exec(`INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)`,
		plan.Subject.ProjectID, plan.EventSequence, plan.Event["id"], string(Bytes(plan.Event))); e != nil {
		t.Fatal(e)
	}
	if _, e = tx.Exec(`INSERT INTO event_state_snapshots(project,event_id,revision,body) VALUES(?,?,?,?)`,
		plan.Subject.ProjectID, plan.Event["id"], 2, string(Bytes(plan.ProjectState))); e != nil {
		t.Fatal(e)
	}
	if _, e = tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at)
		VALUES(?,?,'host:qualification-failure-maintenance',?,?,200,?,'{}',?)`, plan.AuthorID, plan.Subject.ProjectID,
		plan.OperationID, planFileSHA256, Bytes(historicalMaintenanceMarker(plan, planFileSHA256)), plan.ObservedAt); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	state, e = ClassifyHistoricalQualification(ctx, db, plan, planFileSHA256)
	if e != nil || state != "APPLIED" {
		probe, probeErr := db.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
		if probeErr == nil {
			full, _ := store.QualificationMaintenanceCensus(ctx, probe)
			p, _ := store.QualificationMaintenanceProtectedCensus(ctx, probe)
			sel, _ := plan.residualSelectors()
			r, _ := store.QualificationMaintenanceResidualCensus(ctx, probe, sel)
			exact, exactErr := historicalQualificationExactRows(ctx, probe, plan, planFileSHA256)
			t.Logf("debug full=%t schema=%t protected=%t residual=%t exact=%t exactErr=%v", Hash(full) == Hash(plan.BeforeCensus), full.SchemaSHA256 == plan.BeforeCensus.SchemaSHA256, p == plan.BeforeProtectedSHA256, r == plan.BeforeResidualSHA256, exact, exactErr)
			_ = probe.Rollback()
		}
		t.Fatalf("applied: %s %v", state, e)
	}
	planJSON, e := json.Marshal(plan)
	if e != nil {
		t.Fatal(e)
	}
	var roundTripped HistoricalQualificationPlan
	if e = json.Unmarshal(planJSON, &roundTripped); e != nil {
		t.Fatal(e)
	}
	state, e = ClassifyHistoricalQualification(ctx, db, roundTripped, planFileSHA256)
	if e != nil || state != "APPLIED" {
		t.Fatalf("serialized plan classified %s: %v", state, e)
	}
	// The target dispatch row is excluded from the residual census. Each
	// unlicensed column must therefore be checked against its raw preimage.
	for _, drift := range []struct{ column, changed, original string }{
		{"worker", "changed-worker", plan.BeforeDispatchRow.Worker},
		{"identity", `{"changed":true}`, plan.BeforeDispatchRow.Identity},
		{"journal_locator", "changed-locator", plan.BeforeDispatchRow.JournalLocator},
	} {
		if _, e = db.Exec(`UPDATE runtime_dispatches SET `+drift.column+`=? WHERE project=? AND run=? AND epoch=?`,
			drift.changed, plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch); e != nil {
			t.Fatal(e)
		}
		state, e = ClassifyHistoricalQualification(ctx, db, plan, planFileSHA256)
		if e != nil || state != "UNKNOWN" {
			t.Fatalf("%s drift classified %s: %v", drift.column, state, e)
		}
		if _, e = db.Exec(`UPDATE runtime_dispatches SET `+drift.column+`=? WHERE project=? AND run=? AND epoch=?`,
			drift.original, plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch); e != nil {
			t.Fatal(e)
		}
		state, e = ClassifyHistoricalQualification(ctx, db, plan, planFileSHA256)
		if e != nil || state != "APPLIED" {
			t.Fatalf("%s restore classified %s: %v", drift.column, state, e)
		}
	}
	if _, e = db.Exec(`UPDATE runtime_dispatches SET worker=CAST(? AS BLOB) WHERE project=? AND run=? AND epoch=?`,
		plan.BeforeDispatchRow.Worker, plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch); e != nil {
		t.Fatal(e)
	}
	var workerCellType string
	if e = db.QueryRow(`SELECT typeof(worker) FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?`,
		plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch).Scan(&workerCellType); e != nil || workerCellType != "blob" {
		t.Fatalf("worker BLOB precondition: %q %v", workerCellType, e)
	}
	state, e = ClassifyHistoricalQualification(ctx, db, roundTripped, planFileSHA256)
	if e != nil || state != "UNKNOWN" {
		t.Fatalf("same worker bytes with BLOB cell type classified %s: %v", state, e)
	}
	if _, e = db.Exec(`UPDATE runtime_dispatches SET worker=? WHERE project=? AND run=? AND epoch=?`,
		plan.BeforeDispatchRow.Worker, plan.Subject.ProjectID, plan.Subject.RunID, plan.Subject.Epoch); e != nil {
		t.Fatal(e)
	}
	state, e = ClassifyHistoricalQualification(ctx, db, roundTripped, planFileSHA256)
	if e != nil || state != "APPLIED" {
		t.Fatalf("BLOB worker restore classified %s: %v", state, e)
	}
	immutableUpdate, e := db.Exec(`UPDATE domain_objects SET immutable=2 WHERE project=? AND kind='Artifact' AND id=?`,
		plan.Subject.ProjectID, plan.Artifact["id"])
	if e != nil {
		t.Fatal(e)
	}
	changedRows, e := immutableUpdate.RowsAffected()
	if e != nil || changedRows != 1 {
		t.Fatalf("immutable UPDATE rows: %d %v", changedRows, e)
	}
	var actualImmutable int
	if e = db.QueryRow(`SELECT immutable FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?`,
		plan.Subject.ProjectID, plan.Artifact["id"]).Scan(&actualImmutable); e != nil || actualImmutable != 2 {
		t.Fatalf("immutable 0->2 readback: %d %v", actualImmutable, e)
	}
	state, e = ClassifyHistoricalQualification(ctx, db, plan, planFileSHA256)
	if e != nil || state != "UNKNOWN" {
		t.Fatalf("domain_objects immutable 0->2 classified %s: %v", state, e)
	}
	if _, e = db.Exec(`UPDATE domain_objects SET immutable=0 WHERE project=? AND kind='Artifact' AND id=?`,
		plan.Subject.ProjectID, plan.Artifact["id"]); e != nil {
		t.Fatal(e)
	}
	state, e = ClassifyHistoricalQualification(ctx, db, plan, planFileSHA256)
	if e != nil || state != "APPLIED" {
		t.Fatalf("domain_objects immutable restore classified %s: %v", state, e)
	}
	if _, e = db.Exec(`INSERT INTO outbox(project,sequence,id,body) VALUES('project',2,'unrelated','{}')`); e != nil {
		t.Fatal(e)
	}
	state, e = ClassifyHistoricalQualification(ctx, db, plan, planFileSHA256)
	if e != nil || state != "UNKNOWN" {
		t.Fatalf("unrelated row: %s %v", state, e)
	}
}

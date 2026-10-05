//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	"strings"
	"testing"

	"researchos.local/research-os/evaluation/evolution"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"researchos.local/research-os/ops/supervisor"
)

func TestControlCurrentPreparationBudgetExact(t *testing.T) {
	row := func(kind, id string, body Object) Object {
		return Object{"project": "p", "kind": kind, "id": id, "revision": int64(1), "body": string(Bytes(body)), "content_hash": nil, "immutable": int64(0)}
	}
	base := upgradeData{"domain_objects": []Object{row("ProjectProfile", "p", Object{"budget_policy_id": "parent"}), row("BudgetPolicy", "parent", Object{"id": "parent"})}}
	policy := Object{"id": "budget", "project_id": "p", "revision": 1, "created_at": "t", "updated_at": "t", "scope_type": "EXPERIMENT", "scope_id": "experiment", "parent_policy_id": "parent", "mode": "UNLIMITED_AMOUNT", "cap": nil, "enforcement": "ACCOUNTING_ONLY", "period": "LIFETIME", "timezone": "Asia/Shanghai", "effective_from": "t", "unknown_cost_action": "ALLOW_AND_RECORD"}
	makeNames := func(p Object) *controlCurrentNames {
		return &controlCurrentNames{Project: "p", Experiment: "experiment", Rows: upgradeData{"domain_objects": append(append([]Object{}, base["domain_objects"]...), row("Experiment", "experiment", Object{"budget_policy_id": "budget"}), row("BudgetPolicy", "budget", p))}}
	}
	if id, err := controlPreparationBudget(base, makeNames(policy)); err != nil || id != "budget" {
		t.Fatalf("exact default budget rejected: %s %v", id, err)
	}
	for _, field := range []string{"parent_policy_id", "enforcement", "scope_id"} {
		changed := copyObject(policy)
		changed[field] = "unrelated"
		if _, err := controlPreparationBudget(base, makeNames(changed)); err == nil {
			t.Fatalf("accepted changed %s", field)
		}
	}
	n := makeNames(policy)
	extra := copyObject(policy)
	extra["id"] = "extra"
	n.Rows["domain_objects"] = append(n.Rows["domain_objects"], row("BudgetPolicy", "extra", extra))
	filtered := upgradeData{"domain_objects": []Object{}}
	for _, r := range n.Rows["domain_objects"] {
		if !(r["kind"] == "BudgetPolicy" && r["id"] == "budget") {
			filtered["domain_objects"] = append(filtered["domain_objects"], r)
		}
	}
	if err := controlBusinessReadsetUnchanged(base, filtered, "p", "c"); err == nil {
		t.Fatal("additional budget passed business readset")
	}
}

func TestControlCurrentMemorySnapshotRoundtrip(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "authority.sqlite")
	db, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err = db.Exec("PRAGMA journal_mode=WAL; CREATE TABLE secret(id INTEGER PRIMARY KEY,value TEXT); INSERT INTO secret VALUES(1,'PRIVATE_ORIGINAL_NOT_PROJECTABLE')"); err != nil {
		t.Fatal(err)
	}
	raw, err := controlCurrentSnapshot(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	snapshot, err := controlSnapshotMemoryDB(ctx, raw)
	if err != nil {
		t.Fatal(err)
	}
	defer snapshot.Close()
	originalHash, err := evolution.ControlDatabaseHash(db)
	if err != nil {
		t.Fatal(err)
	}
	snapshotHash, err := evolution.ControlDatabaseHash(snapshot)
	if err != nil || originalHash != snapshotHash {
		t.Fatalf("hash mismatch %v", err)
	}
	var value string
	if err = snapshot.QueryRow("SELECT value FROM secret WHERE id=1").Scan(&value); err != nil || value != "PRIVATE_ORIGINAL_NOT_PROJECTABLE" {
		t.Fatalf("snapshot content %v", err)
	}
	if _, err = snapshot.Exec("UPDATE secret SET value='changed'"); err == nil {
		t.Fatal("snapshot unexpectedly writable")
	}
	files, err := os.ReadDir(filepath.Dir(path))
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range files {
		if f.Name() != "authority.sqlite" && f.Name() != "authority.sqlite-wal" && f.Name() != "authority.sqlite-shm" {
			t.Fatal("unexpected snapshot disk file", f.Name())
		}
	}
}

func TestControlCurrentPrivateSnapshotPurposeAndChunks(t *testing.T) {
	ctx := context.Background()
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err = db.Exec("CREATE TABLE original(secret BLOB);INSERT INTO original VALUES(zeroblob(9000000))"); err != nil {
		t.Fatal(err)
	}
	raw, err := controlCurrentSnapshot(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	originalHash := Digest(raw)
	private, err := protectedstore.NewCanary(filepath.Join(t.TempDir(), "private"))
	if err != nil {
		t.Fatal(err)
	}
	defer private.Close()
	snapshot, err := controlSavePrivateSnapshot(ctx, private, "p", "session", "G0", raw)
	if err != nil {
		t.Fatal(err)
	}
	if len(snapshot.Parts) != 2 {
		t.Fatalf("expected two private chunks, got %d", len(snapshot.Parts))
	}
	restored, memory, err := controlReadPrivateSnapshot(ctx, private, "p", snapshot)
	if err != nil {
		t.Fatal(err)
	}
	memory.Close()
	if Digest(restored) != originalHash || Digest(raw) != originalHash {
		t.Fatal("original bytes changed")
	}
	for _, mutation := range []string{"project", "purpose", "stage", "order", "part_hash", "total_hash"} {
		t.Run(mutation, func(t *testing.T) {
			bad := snapshot
			bad.Parts = append([]evolution.ControlPrivatePart(nil), snapshot.Parts...)
			project := "p"
			switch mutation {
			case "project":
				project = "other"
			case "purpose":
				bad.Purpose = "RELEASE_ADMISSION"
			case "stage":
				bad.Stage = "B0"
			case "order":
				bad.Parts[0], bad.Parts[1] = bad.Parts[1], bad.Parts[0]
			case "part_hash":
				bad.Parts[0].Hash = strings.Repeat("0", 64)
			case "total_hash":
				bad.Hash = strings.Repeat("0", 64)
			}
			_, opened, e := controlReadPrivateSnapshot(ctx, private, project, bad)
			if opened != nil {
				opened.Close()
			}
			if e == nil {
				t.Fatal("changed snapshot binding accepted")
			}
		})
	}
}

func TestControlCurrentGoTestCannotOwnAuthority(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "authority.sqlite")
	if err := os.WriteFile(path, []byte("fixture"), 0600); err != nil {
		t.Fatal(err)
	}
	image, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(image)
	if err != nil {
		t.Fatal(err)
	}
	got, err := supervisor.ObserveControlAuthorityOwner(root, path, Digest(raw))
	if err == nil || got.Qualified || !strings.Contains(err.Error(), "OWNER_IS_NOT_ACCEPTED_CONTROL") {
		t.Fatalf("test process qualified: %#v %v", got, err)
	}
}

func TestControlCurrentRowDeltaAndBusinessFreeze(t *testing.T) {
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err = db.Exec("CREATE TABLE auth_grants(principal TEXT,project TEXT,restricted INTEGER,PRIMARY KEY(principal,project));INSERT INTO auth_grants VALUES('v','p',1)"); err != nil {
		t.Fatal(err)
	}
	before, err := controlCurrentRows(db)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec("UPDATE auth_grants SET restricted=0"); err != nil {
		t.Fatal(err)
	}
	after, err := controlCurrentRows(db)
	if err != nil {
		t.Fatal(err)
	}
	delta, err := controlRowDifferences(db, before, after)
	if err != nil || len(delta) != 1 || delta[0].Table != "auth_grants" || delta[0].BeforeHash == delta[0].AfterHash {
		t.Fatalf("delta missed exact grant change: %#v %v", delta, err)
	}
	schema, err := controlSchemaHash(db)
	if err != nil {
		t.Fatal(err)
	}
	a := &currentControlAuthority{frozen: &controlCurrentNames{Rows: before, Schema: schema}}
	tx, err := db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	_, err = a.validateNamedDelta(tx)
	tx.Rollback()
	if err == nil || !strings.Contains(err.Error(), "DELTA_REJECTED:auth_grants") {
		t.Fatalf("grant change accepted %v", err)
	}
	project := Object{"project": "p", "kind": "ProjectState", "id": "state", "revision": int64(1), "body": string(Bytes(Object{"id": "state", "revision": 1, "event_sequence": 1, "updated_at": "a", "active_cycle_id": "c"}))}
	initial := upgradeData{"domain_objects": []Object{project}}
	changed := copyObject(project)
	changed["revision"] = int64(2)
	changed["body"] = string(Bytes(Object{"id": "state", "revision": 2, "event_sequence": 2, "updated_at": "b", "active_cycle_id": "c"}))
	if err = controlBusinessReadsetUnchanged(initial, upgradeData{"domain_objects": []Object{changed}}, "p", "c"); err != nil {
		t.Fatal(err)
	}
	changed["body"] = string(Bytes(Object{"id": "state", "revision": 2, "event_sequence": 2, "updated_at": "b", "active_cycle_id": "other"}))
	if err = controlBusinessReadsetUnchanged(initial, upgradeData{"domain_objects": []Object{changed}}, "p", "c"); err == nil {
		t.Fatal("business authority changed under event metadata exception")
	}
}

func TestControlCurrentVerifierCurrentAuthority(t *testing.T) {
	f, _, _ := protectedFixture(t)
	ctx := context.Background()
	n := &controlCurrentNames{Verifier: "canary-restricted-verifier", Author: f.owner, Executor: "current-executor", Release: "current-release"}
	for _, id := range []string{n.Executor, n.Release} {
		if err := f.s.ProvisionPrincipal(ctx, Principal{ID: id, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}); err != nil {
			t.Fatal(err)
		}
	}
	a := &currentControlAuthority{s: f.s, project: f.project}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	err = a.independentVerifier(tx, n.Verifier, n)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	cases := map[string]func(*sql.Tx) error{
		"restricted_grant_lost": func(tx *sql.Tx) error {
			_, e := tx.Exec("UPDATE auth_grants SET restricted=0 WHERE principal=?", n.Verifier)
			return e
		},
		"owner_role_is_not_verifier": func(tx *sql.Tx) error {
			_, e := tx.Exec("UPDATE auth_principals SET roles='[\"OWNER\"]' WHERE id=?", n.Verifier)
			return e
		},
		"revoked_verifier": func(tx *sql.Tx) error {
			_, e := tx.Exec("UPDATE auth_principals SET revoked=1 WHERE id=?", n.Verifier)
			return e
		},
		"author_authority_intersection": func(tx *sql.Tx) error {
			_, e := tx.Exec("INSERT INTO orchestration_identity(principal,root,parent) VALUES(?,?,?)", n.Verifier, n.Author, n.Author)
			return e
		},
		"executor_authority_intersection": func(tx *sql.Tx) error {
			_, e := tx.Exec("INSERT INTO orchestration_identity(principal,root,parent) VALUES(?,?,?)", n.Verifier, n.Executor, n.Executor)
			return e
		},
		"remote_issuer_intersection": func(tx *sql.Tx) error {
			_, e := tx.Exec("INSERT INTO remote_devices(id,owner,body) VALUES(?,?,?)", n.Verifier, f.owner, string(Bytes(Object{"status": "ACTIVE", "role": "VERIFIER"})))
			return e
		},
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			if e = mutate(tx); e != nil {
				t.Fatal(e)
			}
			if e = a.independentVerifier(tx, n.Verifier, n); e == nil {
				t.Fatal("changed verifier authority accepted")
			}
		})
	}
}

func TestControlCurrentPreparationRejectsAuthorityDrift(t *testing.T) {
	f, _, _ := protectedFixture(t)
	n := &controlCurrentNames{Project: f.project, Task: "named-current-task", Run: "named-current-run", Executor: "canary-restricted-verifier"}
	before, err := controlCurrentRows(f.db)
	if err != nil {
		t.Fatal(err)
	}
	cases := map[string]string{
		"auth_principals":        "UPDATE auth_principals SET roles='[\"VERIFIER\",\"OWNER\"]' WHERE id='canary-restricted-verifier'",
		"auth_grants":            "UPDATE auth_grants SET restricted=0 WHERE principal='canary-restricted-verifier'",
		"auth_credentials":       "UPDATE auth_credentials SET expires_at='2100-01-01T00:00:00Z' WHERE principal='canary-restricted-verifier'",
		"orchestration_identity": "INSERT INTO orchestration_identity(principal,root,parent) VALUES('canary-restricted-verifier','canary-restricted-verifier',NULL)",
		"remote_devices":         "INSERT INTO remote_devices(id,owner,body) VALUES('canary-restricted-verifier','canary-restricted-verifier','{}')",
	}
	for name, query := range cases {
		t.Run(name, func(t *testing.T) {
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			if _, e = tx.Exec(query); e != nil {
				t.Fatal(e)
			}
			after, e := controlCurrentRows(tx)
			if e != nil {
				t.Fatal(e)
			}
			// Preserve the exact pre-review counterexample without accepting it.
			if e = controlBusinessReadsetUnchanged(before, after, f.project, "absent-cycle"); e != nil {
				t.Fatal("counterexample no longer isolates authority tables", e)
			}
			if _, e = controlPreparationAuthorityDelta(tx, before, after, n); e == nil {
				t.Fatal("authority drift accepted")
			}
			fmt.Println("W16_CURRENT_PREPARATION_ASSERTION " + string(Bytes(Object{"table": name, "prior_readset_only_passed": true, "hardened_authority_delta_rejected": true})))
		})
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if _, err = tx.Exec("INSERT INTO auth_grants(principal,project,task,run,restricted) VALUES(?,?,?,?,0)", n.Executor, n.Project, n.Task, n.Run); err != nil {
		t.Fatal(err)
	}
	after, err := controlCurrentRows(tx)
	if err != nil {
		t.Fatal(err)
	}
	delta, err := controlPreparationAuthorityDelta(tx, before, after, n)
	if err != nil || len(delta) != 1 || delta[0].Reason != "NAMED_CLAIM_EXECUTOR_RUN_GRANT" {
		t.Fatalf("exact named grant rejected %v", err)
	}
	if _, err = tx.Exec("INSERT INTO auth_grants(principal,project,task,run,restricted) VALUES(?,?,?,?,0)", n.Executor, n.Project, n.Task, "another-run"); err != nil {
		t.Fatal(err)
	}
	after, err = controlCurrentRows(tx)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = controlPreparationAuthorityDelta(tx, before, after, n); err == nil {
		t.Fatal("additional unrelated run grant accepted")
	}
}

func TestControlCurrentDurableReservationNoReplay(t *testing.T) {
	path := filepath.Join(t.TempDir(), "reservation.sqlite")
	db, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec("CREATE TABLE evolution_journal(sequence INTEGER PRIMARY KEY AUTOINCREMENT,project TEXT,candidate TEXT,run TEXT,event TEXT,body TEXT,receipt_hash TEXT)"); err != nil {
		t.Fatal(err)
	}
	a := &currentControlAuthority{id: "session", project: "p", g0: evolution.ControlPrivateSnapshot{Generation: "g0"}, frozen: &controlCurrentNames{Project: "p", Candidate: "c", Task: "t", Run: "r", Epoch: 1, Plan: "plan"}}
	tx, err := db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	if err = a.reserveCurrentEvaluation(tx); err != nil {
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	db.Close()
	// Reopen SQLite with no retained latch. The committed reservation still
	// prevents any second native invocation or automatic recovery replay.
	db, err = sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	tx, err = db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if err = a.reservationCurrent(tx); err != nil {
		t.Fatal(err)
	}
	if err = a.reserveCurrentEvaluation(tx); err == nil || !strings.Contains(err.Error(), "UNKNOWN_INSPECTION_REQUIRED") {
		t.Fatalf("reservation was replayed %v", err)
	}
	a.g0.Generation = "different"
	if err = a.reservationCurrent(tx); err == nil {
		t.Fatal("different G0 inherited reservation")
	}
}

func TestControlCurrentNativeEndUsesReceipts(t *testing.T) {
	receipt := sandbox.Receipt{Started: "2026-09-30T00:00:00Z", Finished: "2026-09-30T00:00:01Z", Stopped: true, StreamsDrained: true, CleanupComplete: true, ExitCode: 0}
	later := receipt
	later.Finished = "2026-09-30T00:00:02Z"
	proof := supervisor.ControlProof{Pairs: []supervisor.ControlPair{{Baseline: supervisor.ControlInvocation{Receipt: receipt}, Candidate: supervisor.ControlInvocation{Receipt: later}}}}
	ended, err := controlNativeEnd(proof)
	if err != nil || ended != later.Finished {
		t.Fatalf("native end not derived from receipts %q %v", ended, err)
	}
	proof.Pairs[0].Candidate.Receipt.Finished = "2026-09-29T00:00:00Z"
	if _, err = controlNativeEnd(proof); err == nil {
		t.Fatal("reversed receipt time accepted")
	}
	proof.Pairs[0].Candidate.Receipt = later
	proof.Pairs[0].Candidate.Receipt.CleanupComplete = false
	if _, err = controlNativeEnd(proof); err == nil {
		t.Fatal("unsettled native receipt accepted")
	}
}

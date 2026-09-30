//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

type recoveryStorageFixture struct {
	state        supervisor.ReleaseState
	lease        *rt.DataRootLease
	contracts    *Contracts
	policy       *backupPolicy
	sourceBefore []byte
}

// Public synthetic storage only: these rows deliberately carry no accepted
// release authority. No executable, protected store, holdout or provider runs.
// The encrypted snapshot and restore are the real existing backup machinery.
func recoveryStorageSetup(t *testing.T) recoveryStorageFixture {
	t.Helper()
	f := setup(t)
	f.createProject()
	root := t.TempDir()
	data := filepath.Join(root, "data")
	lease, err := rt.AcquireDataRootLease(data)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { lease.Close() })
	database := filepath.Join(data, "researchos.sqlite")
	if _, err = f.db.Exec("VACUUM INTO ?", database); err != nil {
		t.Fatal(err)
	}
	f.db.Close()
	db, err := store.Open(database)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	f.db, f.s.DB = db, db
	stable, candidate := releasePlainDigest("synthetic stable bytes"), releasePlainDigest("synthetic candidate bytes")
	ref := func(hash string) Object {
		return Object{"entity_type": "Artifact", "id": ID(), "revision": 1, "content_hash": "sha256:" + hash}
	}
	stableRef, candidateRef := ref(stable), ref(candidate)
	x := Merge(Base(f.project), Object{"scope": "SYSTEM", "status": "EVALUATING", "candidate_artifact_ref": candidateRef, "stable_artifact_ref": stableRef, "isolated_workspace_id": ID(), "baseline_suite_ref": ref(releasePlainDigest("suite")), "baseline_policy_hash": Digest([]byte("synthetic policy")), "changed_paths_manifest_ref": ref(releasePlainDigest("source")), "experiment_id": ID(), "regression_acceptance_id": ID(), "canary_acceptance_id": nil, "migration_plan_ref": nil, "rollback_plan_ref": ref(releasePlainDigest("rollback")), "rollback_verified_receipt_id": nil, "independent_supervisor_id": ID(), "observation_deadline": nil, "promoted_at": nil, "freeze_reason": nil})
	if err = f.s.Contracts.Validate("SystemCandidate", x); err != nil {
		t.Fatal(err)
	}
	// Store schema-valid inert candidate history directly. This is not an API
	// acceptance, a producer of business gain, or a releasable admission.
	if _, err = db.Exec("INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,'SystemCandidate',?,1,?)", f.project, x["id"], string(Bytes(x))); err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec("INSERT INTO domain_versions(project,kind,id,revision,body) VALUES(?,'SystemCandidate',?,1,?)", f.project, x["id"], string(Bytes(x))); err != nil {
		t.Fatal(err)
	}
	host := Object{"root": root, "stable_ref": stableRef, "fixture_scope": "SYNTHETIC_PUBLIC_STORAGE_ONLY"}
	if _, err = db.Exec("INSERT INTO evolution_hosts(project,body) VALUES(?,?)", f.project, string(Bytes(host))); err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec("INSERT INTO evolution_candidates(project,candidate,creator,plan_hash) VALUES(?,?,?,?)", f.project, x["id"], f.owner, Hash(evolutionPlan(x))); err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec("INSERT INTO evolution_slots(project,active_hash,stable_hash,candidate,epoch,state) VALUES(?,?,?,NULL,7,'STABLE')", f.project, "sha256:"+stable, "sha256:"+stable); err != nil {
		t.Fatal(err)
	}
	a := supervisor.ReleaseAdmission{Project: f.project, CandidateID: Str(x, "id"), AcceptanceID: Str(x, "regression_acceptance_id"), Operation: releaseOperationID(f.project, Str(x, "id"), Str(x, "regression_acceptance_id"), 7), ExpectedEpoch: 7, StableSHA256: stable, CandidateSHA256: candidate, SameSchema: true, NoUnknownEffects: true, ExpiresUTC: time.Now().Add(-time.Hour).UTC()}
	state := supervisor.ReleaseState{Epoch: 8, Operation: a.Operation, Phase: "DRAINED", Active: candidate, ActivePath: filepath.Join(root, "never-run-candidate.exe"), LastGood: stable, LastGoodPath: filepath.Join(root, "never-run-stable.exe"), Candidate: candidate, CandidatePath: filepath.Join(root, "never-run-candidate.exe"), Data: data, Admission: releasePlainDigest(a), AdmissionBundle: &a}
	if _, err = db.Exec("INSERT INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status) VALUES(?,?,'START_CANARY',?,7,?,?,'PREPARED')", f.project, x["id"], a.Operation, state.Admission, "r2-fixture-"+a.Operation); err != nil {
		t.Fatal(err)
	}
	if err = releaseOperationCAS(db, a.Operation, "PREPARED", "DISPATCHED", ""); err != nil {
		t.Fatal(err)
	}
	purpose := Object{"kind": "R2_FIXTURE_QUIESCED_CUTOVER", "root": data, "database": database, "operation": a.Operation, "epoch": 8, "admission_hash": state.Admission, "scope": "SYNTHETIC_PUBLIC_STORAGE_ONLY"}
	cutover := &supervisor.ReleaseCutover{Operation: a.Operation, Epoch: 8, Root: data, Database: database, Directory: filepath.Join(root, "release-state", "cutovers", a.Operation), KeyPath: filepath.Join(root, "release-state", "keys", a.Operation+"-cutover.key"), Purpose: Bytes(purpose)}
	state.Cutover = cutover
	policy := &backupPolicy{format: releaseFixtureBackupFormat, databaseName: "researchos.sqlite", purpose: purpose, validate: chainCutoverValidation(func(*sql.DB) error { return nil }, a, state)}
	key := backupTestKey(t)
	if err = os.MkdirAll(filepath.Dir(cutover.KeyPath), 0700); err != nil {
		t.Fatal(err)
	}
	if err = backupWrite(cutover.KeyPath, key); err != nil {
		t.Fatal(err)
	}
	manifest, err := f.s.createBackupPolicy(context.Background(), cutover.Directory, key, policy)
	if err != nil {
		t.Fatal(err)
	}
	cutover.ManifestSHA256, cutover.Migrations = releaseArtifactDigest(Digest(Bytes(manifest))), manifest.Migrations
	if _, err = db.Exec("PRAGMA wal_checkpoint(TRUNCATE)"); err != nil {
		t.Fatal(err)
	}
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(database)
	if err != nil {
		t.Fatal(err)
	}
	return recoveryStorageFixture{state, lease, f.s.Contracts, policy, raw}
}

func (f recoveryStorageFixture) restore(t *testing.T) supervisor.ReleaseRestoreResult {
	t.Helper()
	r, err := restoreEvolutionCutoverContext(context.Background(), f.state, f.lease, f.contracts, f.policy)
	if err != nil {
		t.Fatal(err)
	}
	return r
}

func TestW16RecoveryContextFenceEncryptedCopy(t *testing.T) {
	f := recoveryStorageSetup(t)
	r := f.restore(t)
	c, err := supervisor.ValidateReleaseRestoreResult(f.state, r)
	if err != nil {
		t.Fatal(err)
	}
	if c.Status != supervisor.RecoveryAuthorizationBlocked || c.SnapshotEpoch != 7 || c.HostEpoch != 8 {
		t.Fatalf("context upgraded authority: %+v", c)
	}
	before, err := os.ReadFile(f.state.Cutover.Database)
	if err != nil || Digest(before) != Digest(f.sourceBefore) {
		t.Fatal("failed source DB changed", err)
	}
	db, err := store.Open(filepath.Join(r.Destination, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var status, active, stable string
	var epoch uint64
	if err = db.QueryRow("SELECT state,epoch,active_hash,stable_hash FROM evolution_slots WHERE project=?", f.state.AdmissionBundle.Project).Scan(&status, &epoch, &active, &stable); err != nil {
		t.Fatal(err)
	}
	if status != "RECOVERING" || epoch != 7 || active != "sha256:"+f.state.LastGood || stable != active {
		t.Fatalf("slot business fence wrong: %s %d %s", status, epoch, active)
	}
	op, err := readReleaseOperation(db, f.state.AdmissionBundle.Project, f.state.Operation)
	if err != nil || op.Status != "DISPATCHED" || op.Epoch != 7 || op.Receipt.Valid || op.Revision != 0 {
		t.Fatalf("operation changed: %+v %v", op, err)
	}
	var body string
	if err = db.QueryRow("SELECT body FROM domain_objects WHERE kind='SystemCandidate' AND id=?", f.state.AdmissionBundle.CandidateID).Scan(&body); err != nil {
		t.Fatal(err)
	}
	x, err := Decode([]byte(body))
	if err != nil || x["status"] != "EVALUATING" {
		t.Fatal("candidate projected", err)
	}
	var liveCredentials, rollbackRows int
	if err = db.QueryRow("SELECT count(*) FROM auth_credentials WHERE revoked=0").Scan(&liveCredentials); err != nil || liveCredentials != 0 {
		t.Fatal("credential resurrected", err)
	}
	if err = db.QueryRow("SELECT count(*) FROM evolution_release_operations WHERE action!='START_CANARY'").Scan(&rollbackRows); err != nil || rollbackRows != 0 {
		t.Fatal("rollback manufactured", err)
	}
	db.Close()
	if _, err = restoreEvolutionCutoverContext(context.Background(), f.state, f.lease, f.contracts, f.policy); err == nil || !strings.Contains(err.Error(), "BLOCKED_RESTORE_OUTCOME_UNKNOWN") {
		t.Fatal("unacknowledged restore was retried", err)
	}
	roots, _ := filepath.Glob(filepath.Join(filepath.Dir(f.state.Data), "restored-*"))
	if len(roots) != 1 || roots[0] != r.Destination {
		t.Fatalf("duplicate destination: %v", roots)
	}
	t.Logf("scope=SYNTHETIC_PUBLIC_STORAGE_ONLY status=%s operation=%s context=%s source-unchanged=true slot=RECOVERING snapshot-epoch=7 host-epoch=8 DISPATCHED/EVALUATING-preserved=true revoked-credentials=true native/private/provider=NOT_RUN", c.Status, r.Operation, r.ContextSHA256)
}

func TestW16RecoveryContextTamperMissingAndIdentity(t *testing.T) {
	for _, kind := range []string{"context", "report", "manifest", "destination-identity", "source-identity", "missing-context"} {
		t.Run(kind, func(t *testing.T) {
			f := recoveryStorageSetup(t)
			r := f.restore(t)
			switch kind {
			case "context":
				if err := os.WriteFile(r.ContextPath, []byte(`{"status":"QUALIFIED"}`), 0600); err != nil {
					t.Fatal(err)
				}
			case "report":
				if err := os.WriteFile(filepath.Join(r.Destination, "restore-report.json"), []byte(`{}`), 0600); err != nil {
					t.Fatal(err)
				}
			case "manifest":
				f.state.Cutover.ManifestSHA256 = releasePlainDigest("changed")
			case "destination-identity", "source-identity":
				p := filepath.Join(r.Destination, "researchos.sqlite")
				if kind == "source-identity" {
					p = f.state.Cutover.Database
				}
				raw, err := os.ReadFile(p)
				if err != nil {
					t.Fatal(err)
				}
				if err = os.Rename(p, p+".original"); err != nil {
					t.Fatal(err)
				}
				if err = os.WriteFile(p, raw, 0600); err != nil {
					t.Fatal(err)
				}
			case "missing-context":
				if err := os.Rename(r.ContextPath, r.ContextPath+".preserved"); err != nil {
					t.Fatal(err)
				}
			}
			if _, err := supervisor.ValidateReleaseRestoreResult(f.state, r); err == nil {
				t.Fatal("changed recovery evidence accepted")
			}
		})
	}
}

func TestW16RecoveryContextUnknownAndStrictDelta(t *testing.T) {
	t.Run("reservation-before-restore", func(t *testing.T) {
		f := recoveryStorageSetup(t)
		directory, destination, err := supervisor.RestoreContextPaths(f.state)
		if err != nil {
			t.Fatal(err)
		}
		if err = os.MkdirAll(directory, 0700); err != nil {
			t.Fatal(err)
		}
		if err = backupWrite(filepath.Join(directory, "attempt.json"), []byte(`{"interrupted":true}`)); err != nil {
			t.Fatal(err)
		}
		if _, err = restoreEvolutionCutoverContext(context.Background(), f.state, f.lease, f.contracts, f.policy); err == nil || !strings.Contains(err.Error(), "BLOCKED_RESTORE_OUTCOME_UNKNOWN") {
			t.Fatal("unknown attempt replayed", err)
		}
		if _, err = os.Stat(destination); !os.IsNotExist(err) {
			t.Fatal("unknown attempt published destination", err)
		}
	})
	for _, change := range []string{"old-grant", "credential", "slot-epoch", "candidate", "operation"} {
		t.Run(change, func(t *testing.T) {
			f := recoveryStorageSetup(t)
			f.policy.afterRecovery = func(db *sql.DB) error {
				var err error
				switch change {
				case "old-grant":
					_, err = db.Exec("UPDATE auth_principals SET roles='[\"OWNER\",\"RELEASE_SERVICE\"]'")
				case "credential":
					_, err = db.Exec("UPDATE auth_credentials SET revoked=0")
				case "slot-epoch":
					_, err = db.Exec("UPDATE evolution_slots SET epoch=epoch+1")
				case "candidate":
					_, err = db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','CANARY') WHERE kind='SystemCandidate'")
				case "operation":
					_, err = db.Exec("UPDATE evolution_release_operations SET status='OBSERVED',receipt_digest=?", releasePlainDigest("invented observation"))
				}
				return err
			}
			_, err := restoreEvolutionCutoverContext(context.Background(), f.state, f.lease, f.contracts, f.policy)
			if err == nil {
				t.Fatal("unexpected recovery delta accepted")
			}
			_, dest, _ := supervisor.RestoreContextPaths(f.state)
			if _, statErr := os.Stat(dest); !os.IsNotExist(statErr) {
				t.Fatal("invalid restore published", statErr)
			}
		})
	}
}

func TestW16RecoveryContextJournalBlockedBeforeStart(t *testing.T) {
	f := recoveryStorageSetup(t)
	if err := f.lease.Close(); err != nil {
		t.Fatal(err)
	}
	j, err := supervisor.OpenReleaseJournal(filepath.Join(filepath.Dir(f.state.Data), "release-state"))
	if err != nil {
		t.Fatal(err)
	}
	defer j.Close()
	s := f.state
	s.Phase = "CANARY" // Public mechanical seed, no PID or live claim.
	if err = j.Append(s); err != nil {
		t.Fatal(err)
	}
	calls := 0
	d := &supervisor.ControlFixtureDriver{Journal: j}
	d.RestoreWithContext = func(ctx context.Context, state supervisor.ReleaseState, lease *rt.DataRootLease) (supervisor.ReleaseRestoreResult, error) {
		calls++
		return restoreEvolutionCutoverContext(ctx, state, lease, f.contracts, f.policy)
	}
	d.Restore = func(context.Context, supervisor.ReleaseState, *rt.DataRootLease) (string, error) {
		t.Fatal("typed restore fell back to legacy")
		return "", nil
	}
	engine, err := supervisor.NewReleaseEngine(j, d, d, func(supervisor.ReleaseAdmission) error { t.Fatal("recovery requested new admission"); return nil })
	if err != nil {
		t.Fatal(err)
	}
	_, err = engine.RollbackFixture(context.Background(), s.Operation)
	if err == nil || err.Error() != supervisor.RecoveryAuthorizationBlocked {
		t.Fatal("restore authority was not blocked", err)
	}
	got := j.State()
	if got.RestoreContext == nil || got.Data != s.Data || got.Phase != "RECOVERING" || got.PID != 0 || got.Epoch != s.Epoch || len(got.Frozen) != 0 {
		t.Fatalf("journal lost context or promoted restored state: %+v", got)
	}
	if _, err = d.Start(s.LastGoodPath, s.Operation+"-rollback", got.RestoreContext.Destination); err == nil || err.Error() != supervisor.RecoveryAuthorizationBlocked {
		t.Fatal("typed context allowed a start", err)
	}
	if err = d.Compatible(context.Background(), got); err == nil || err.Error() != supervisor.RecoveryAuthorizationBlocked || calls != 1 {
		t.Fatalf("duplicate typed restore re-executed: calls=%d err=%v", calls, err)
	}
	before, _ := json.Marshal(got.RestoreContext)
	if err = j.Close(); err != nil {
		t.Fatal(err)
	}
	reopened, err := supervisor.OpenReleaseJournal(filepath.Join(filepath.Dir(f.state.Data), "release-state"))
	if err != nil {
		t.Fatal(err)
	}
	defer reopened.Close()
	after, _ := json.Marshal(reopened.State().RestoreContext)
	if string(before) != string(after) {
		t.Fatal("context did not survive journal reload")
	}
}

func TestW16RecoveryContextNonIdleRejected(t *testing.T) {
	for _, kind := range []string{"active-run", "unfinished-effect"} {
		t.Run(kind, func(t *testing.T) {
			f := recoveryStorageSetup(t)
			// Deliberately inject minimal poison rows immediately before the
			// new idle guard. This verifies refusal, not active-Run recovery.
			f.policy.beforeRecovery = func(db *sql.DB) error {
				var err error
				if kind == "active-run" {
					_, err = db.Exec("INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,'Run',?,1,?)", f.state.AdmissionBundle.Project, ID(), `{"status":"RUNNING"}`)
				} else {
					_, err = db.Exec("INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)", f.state.AdmissionBundle.Project, ID(), "synthetic-unsent-effect", `{"state":"UNKNOWN"}`)
				}
				return err
			}
			_, err := restoreEvolutionCutoverContext(context.Background(), f.state, f.lease, f.contracts, f.policy)
			if err == nil || !strings.Contains(err.Error(), "BLOCKED_RECOVERY_NON_IDLE") {
				t.Fatal("non-idle restore not rejected by idle fence", err)
			}
			directory, destination, _ := supervisor.RestoreContextPaths(f.state)
			for _, path := range []string{destination, filepath.Join(directory, "context.json")} {
				if _, statErr := os.Stat(path); !os.IsNotExist(statErr) {
					t.Fatal("non-idle restore published", path, statErr)
				}
			}
		})
	}
}

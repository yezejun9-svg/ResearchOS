//go:build windows

package domain

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/store"
)

// The Host/CLI smoke separately proves that the production authority reads
// bytes. This fixture source isolates the restore transaction so an active Run,
// confirmed effect, UNKNOWN effect and workspace path can be checked together.
type backupW1802Source struct{ path string }

func (f backupW1802Source) SnapshotWorkspace(_ context.Context, binding WorkspaceBinding, _ string, limits BackupWorkspaceLimits) (BackupWorkspaceSnapshot, error) {
	if binding.RealPath != f.path || limits.MaxFiles < 1 {
		return BackupWorkspaceSnapshot{}, fmt.Errorf("fixture workspace source mismatch")
	}
	raw, err := os.ReadFile(filepath.Join(f.path, "source.txt"))
	if err != nil {
		return BackupWorkspaceSnapshot{}, err
	}
	return BackupWorkspaceSnapshot{Directories: []string{}, Files: []BackupWorkspaceFile{{Path: "source.txt", Data: raw}}}, nil
}

func TestW1802WorkspaceRestorePreservesEffectAndSessionFences(t *testing.T) {
	ctx := context.Background()
	o := orchestrationSetup(t)
	f := o.f
	active := o.claim(o.task("restore-current-work", Empty(), Empty()))
	f.token = o.owner
	policy := f.expect(200, "GET", f.path("/goals/"+Str(o.goal, "id")+"/budget-policy"), "", "", nil)
	confirmedKey, unknownKey := "w1802-confirmed-effect", "w1802-unknown-effect"
	for _, key := range []string{confirmedKey, unknownKey} {
		if _, err := f.s.PrepareEffect(ctx, o.owner, f.project, Str(active.run, "id"), key,
			Object{"fixture": key}, budgetRequest(active, Str(policy, "id"), "RESERVE", key, dollars("1.00"), "UPPER_BOUND", nil)); err != nil {
			t.Fatal(err)
		}
		if _, err := f.s.BeginEffect(ctx, o.owner, f.project, Str(active.run, "id"), key); err != nil {
			t.Fatal(err)
		}
		state := "CONFIRMED"
		if key == unknownKey {
			state = "UNKNOWN"
		}
		if err := f.s.ObserveEffect(ctx, f.project, Str(active.run, "id"), key, state,
			Object{"fixture_provider": state, "external_dispatch_count": 0}); err != nil {
			t.Fatal(err)
		}
	}
	workspace := t.TempDir()
	if err := os.WriteFile(filepath.Join(workspace, "source.txt"), []byte("same workspace input\n"), 0600); err != nil {
		t.Fatal(err)
	}
	workspaceRef := "wsref-" + ID()[:16]
	b := WorkspaceBinding{AuthorizedRef: workspaceRef, DisplayName: "effect fixture", DisplayPath: workspace,
		RealPath: workspace, Access: "READ_WRITE", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive,
		PrincipalID: f.owner, HostPrincipalRef: "fixture-local-host", ClientID: "fixture-client",
		SelectionRef: "fixture-selection", CommandID: "fixture-workspace-command", CreatedAt: Now()}
	tx, err := f.db.BeginTx(ctx, nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, workspaceRef, b.record()); err != nil {
		t.Fatal(err)
	}
	if err := f.s.putOpaque(ctx, tx, f.project, "Project", f.project, Object{"id": f.project,
		"project_id": f.project, "revision": int64(1), "created_at": Now(), "updated_at": Now(),
		"name": "effect fixture", "authorized_workspace_ref": workspaceRef, "real_path": workspace}); err != nil {
		t.Fatal(err)
	}
	sessionID := "w1802-effect-session"
	now := time.Now().UTC()
	goalID, taskID, runID := Str(o.goal, "id"), Str(active.task, "id"), Str(active.run, "id")
	if err := MapClientSession(ctx, tx, ClientSession{ID: sessionID, ProjectID: f.project, Revision: 1,
		CreatedAt: now, UpdatedAt: now, GoalID: &goalID, TaskID: &taskID, RunID: &runID,
		WriterEpoch: 1, WriterClientID: "fixture-client", UpstreamSession: "fixture-native",
		WorkspaceRef: &workspaceRef, Protocol: ClientSessionProtocol}); err != nil {
		t.Fatal(err)
	}
	if err := tx.Commit(); err != nil {
		t.Fatal(err)
	}
	oldHash := Str(active.run, "lease_token_hash")
	key := []byte(strings.Repeat("w", 32))
	backup := filepath.Join(t.TempDir(), "encrypted")
	m, err := f.s.CreateBackupWithWorkspaces(ctx, backup, key, backupW1802Source{workspace})
	if err != nil {
		t.Fatal(err)
	}
	destination := filepath.Join(t.TempDir(), "restored")
	report, err := RestoreBackup(ctx, backup, destination, RestoreOptions{Key: key,
		SupportedMigrations: m.Migrations, Contracts: f.s.Contracts,
		WorkspaceTarget: func(_ context.Context, _ string, requests []WorkspaceRestoreRequest) ([]WorkspaceRestorePin, error) {
			if len(requests) != 1 || requests[0].AuthorizedRef != workspaceRef {
				return nil, fmt.Errorf("unexpected fixture pin request")
			}
			return []WorkspaceRestorePin{{AuthorizedRef: workspaceRef, RealPath: requests[0].RealPath,
				HostPrincipalRef: "fixture-new-host"}}, nil
		}})
	if err != nil {
		t.Fatal(err)
	}
	if report.Status != "RESTORED_RECONCILIATION_REQUIRED" || report.Recovery["workspace_roots_rebound"] != 1 {
		t.Fatalf("restore did not report workspace rebinding: %+v", report)
	}
	restored, err := store.Open(filepath.Join(destination, "state.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer restored.Close()
	svc := &Service{DB: restored, Contracts: f.s.Contracts}
	var restoredProject, restoredRef, restoredGoal, restoredTask, restoredRun string
	var epoch int64
	if err := restored.QueryRow(`SELECT project_id,workspace_ref,goal_id,task_id,run_id,writer_epoch FROM client_sessions WHERE id=?`, sessionID).
		Scan(&restoredProject, &restoredRef, &restoredGoal, &restoredTask, &restoredRun, &epoch); err != nil {
		t.Fatal(err)
	}
	if restoredProject != f.project || restoredRef != workspaceRef || restoredGoal != goalID || restoredTask != taskID || restoredRun != runID || epoch != 1 {
		t.Fatal("session identity or writer epoch reset")
	}
	var runRaw string
	if err := restored.QueryRow(`SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND id=?`, f.project, runID).Scan(&runRaw); err != nil {
		t.Fatal(err)
	}
	run, err := Decode([]byte(runRaw))
	if err != nil {
		t.Fatal(err)
	}
	if run["status"] != "RECONCILING" || Str(run, "lease_token_hash") == oldHash || Str(run, "lease_expires_at") != "1970-01-01T00:00:00Z" {
		t.Fatalf("old run lease was reused: %+v", run)
	}
	for key, want := range map[string]string{confirmedKey: "CONFIRMED", unknownKey: "UNKNOWN"} {
		var state string
		if err := restored.QueryRow(`SELECT json_extract(body,'$.state') FROM resource_effects WHERE project=? AND run=? AND effect_key=? ORDER BY sequence DESC LIMIT 1`,
			f.project, runID, key).Scan(&state); err != nil || state != want {
			t.Fatalf("effect %s changed after restore: %s %v", key, state, err)
		}
	}
	newToken, err := svc.IssueCredential(ctx, f.owner, time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := svc.BeginEffect(ctx, newToken, f.project, runID, confirmedKey); err == nil {
		t.Fatal("confirmed provider effect replayed")
	}
	if _, err := svc.BeginEffect(ctx, newToken, f.project, runID, unknownKey); err == nil {
		t.Fatal("unknown provider effect replayed")
	}
	if _, err := svc.ResumeCheckpoint(ctx, newToken, f.project, runID, "w1802-no-reconcile", mustNum(t, run, "revision")); err == nil {
		t.Fatal("unknown effect resumed without reconciliation")
	}
	if _, err := restored.Exec(`UPDATE client_sessions SET writer_epoch=writer_epoch+1 WHERE id=?`, sessionID); err == nil || !strings.Contains(err.Error(), "RESTORE_FRESH_RECONCILIATION_REQUIRED") {
		t.Fatalf("old session epoch handed off without fresh observation: %v", err)
	}
	var bindingRaw string
	if err := restored.QueryRow(`SELECT body FROM domain_objects WHERE kind='WorkspaceBinding' AND id=?`, workspaceRef).Scan(&bindingRaw); err != nil {
		t.Fatal(err)
	}
	bound, err := decodeBinding(bindingRaw)
	if err != nil || bound.Status != WorkspaceActive || bound.RealPath != backupWorkspaceDirectory(destination, workspaceRef) || bound.HostPrincipalRef != "fixture-new-host" {
		t.Fatalf("old workspace path or host identity survived: %+v %v", bound, err)
	}
	if contents, err := os.ReadFile(filepath.Join(bound.RealPath, "source.txt")); err != nil || string(contents) != "same workspace input\n" {
		t.Fatalf("sealed workspace content missing: %v %s", err, contents)
	}
	t.Logf("W18_ASSERTION %s", Bytes(Object{"assertion_id": "W18-02-EFFECT-LEASE-COMBINED", "expected": true, "actual": true,
		"status": "PASS", "evidence": Object{"session_id": sessionID, "run_id": runID,
			"confirmed_state": "CONFIRMED", "unknown_state": "UNKNOWN", "old_lease_expired": true,
			"epoch_handoff_blocked": true, "provider_dispatch_count": 0}}))
}

func mustNum(t *testing.T, obj Object, field string) int64 {
	t.Helper()
	n, err := Num(obj, field)
	if err != nil {
		t.Fatal(err)
	}
	return n
}

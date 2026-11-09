//go:build windows

package host_test

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

func backupCLI(t *testing.T, binary, repo string, args ...string) ([]byte, error) {
	t.Helper()
	cmd := exec.Command(binary, args...)
	cmd.Dir = repo
	return cmd.CombinedOutput()
}

func backupTestRepo(t *testing.T) string {
	t.Helper()
	root, err := filepath.Abs(filepath.Join("..", ".."))
	if err != nil {
		t.Fatal(err)
	}
	return root
}

func backupTestHost(t *testing.T, db *sql.DB, dataRoot, repo string) *host.Host {
	t.Helper()
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(dataRoot, "host"),
		ContractsDir:  filepath.Join(repo, "spec", "v2.0", "contracts"),
		MigrationFile: filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"),
		SchemaDir:     filepath.Join(repo, "internal", "api", "contracts")})
	if err != nil {
		t.Fatal(err)
	}
	return h
}

func backupHTTP(t *testing.T, svc *domain.Service, token, method, path string, body any, etag string, want int) (domain.Object, string) {
	t.Helper()
	var raw []byte
	if body != nil {
		raw = domain.Bytes(body)
	}
	request := httptest.NewRequest(method, path, strings.NewReader(string(raw)))
	request.Header.Set("Authorization", "Bearer "+token)
	if body != nil {
		request.Header.Set("Content-Type", "application/json")
	}
	if method != http.MethodGet {
		request.Header.Set("Idempotency-Key", domain.ID())
	}
	if etag != "" {
		request.Header.Set("If-Match", etag)
	}
	response := httptest.NewRecorder()
	svc.Handler().ServeHTTP(response, request)
	if response.Code != want {
		t.Fatalf("%s %s expected %d, got %d: %s", method, path, want, response.Code, response.Body.String())
	}
	var value domain.Object
	if err := json.Unmarshal(response.Body.Bytes(), &value); err != nil {
		t.Fatal(err)
	}
	return value, response.Header().Get("ETag")
}

// This smoke uses production Host registration, domain workspace/project/session
// creation, and the compiled ops/backup CLI. The chooser callback supplies a
// temporary test path; it is not evidence that a human clicked the Windows UI.
func TestW1802ProductionBackupCLIWorkspaceContinuation(t *testing.T) {
	ctx := context.Background()
	repo := backupTestRepo(t)
	root := t.TempDir()
	sourceData := filepath.Join(root, "source-data")
	workspace := filepath.Join(root, "chosen-workspace")
	if err := os.MkdirAll(filepath.Join(workspace, "src"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(filepath.Join(workspace, "empty"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(workspace, "src", "main.go"), []byte("package continued\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(sourceData, 0700); err != nil {
		t.Fatal(err)
	}
	db, err := store.Open(filepath.Join(sourceData, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	if err := store.Bootstrap(ctx, db, filepath.Join(repo, "migrations", "sqlite", "0001_bootstrap.sql")); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.New(db, filepath.Join(repo, "spec", "v2.0", "contracts"), filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		t.Fatal(err)
	}
	h := backupTestHost(t, db, sourceData, repo)
	owner, err := h.BootstrapOwner(ctx)
	if err != nil {
		t.Fatal(err)
	}
	credentialRef, err := h.ImportCredential("fixture-provider", "API_KEY", "synthetic-private-value", "")
	if err != nil || h.CredentialStatus(credentialRef) != host.StatusAvailable {
		t.Fatalf("source host credential fixture unavailable: %v", err)
	}
	frame, err := json.Marshal(map[string]any{"kind": host.KindWorkspaceChooseRequest,
		"client_id": "backup-smoke-cli", "payload": map[string]any{"requested_path": workspace, "requested_access": host.AccessReadWrite}})
	if err != nil {
		t.Fatal(err)
	}
	reply, err := h.HandleNative(frame, true, func(string) (string, error) { return workspace, nil })
	if err != nil {
		t.Fatal(err)
	}
	var chosen struct {
		Payload struct {
			Ref string `json:"selection_ref"`
		} `json:"payload"`
	}
	if err := json.Unmarshal(reply, &chosen); err != nil || chosen.Payload.Ref == "" {
		t.Fatalf("native selection failed: %v", err)
	}
	doc, err := api.ClientProtocolDocument()
	if err != nil {
		t.Fatal(err)
	}
	principal := domain.Principal{ID: owner.PrincipalID, Roles: []string{"OWNER"}, CanCreateProject: true}
	authority := localworkspace.NewAuthority(h)
	registered, err := svc.RegisterWorkspace(ctx, principal, authority, doc, domain.RegisterWorkspaceInput{
		SelectionRef: chosen.Payload.Ref, DisplayName: "continued workspace", RequestedAccess: host.AccessReadWrite,
		ClientID: "backup-smoke-cli", CommandID: "backup-smoke-register"})
	if err != nil {
		t.Fatal(err)
	}
	ref := domain.Str(registered, "authorized_workspace_ref")
	project, err := svc.BootstrapProject(ctx, principal, authority, doc, localworkspace.NewScanner(), domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: ref, DisplayName: "continued project", ClientID: "backup-smoke-cli",
		CommandID: "backup-smoke-project", MeasurementMode: "FIXTURE"})
	if err != nil {
		t.Fatal(err)
	}
	projectID := domain.Str(project, "project_id")
	if projectID == "" || ref == "" {
		t.Fatal("production project or authorized workspace identity missing")
	}
	projectPath := "/v1/projects/" + projectID
	_, stateTag := backupHTTP(t, svc, owner.Session.Token, "GET", projectPath+"/state", nil, "", 200)
	requirement, requirementTag := backupHTTP(t, svc, owner.Session.Token, "POST", projectPath+"/requirements",
		domain.Object{"requirement_key": "W18-BACKUP", "text": "continue the same work after restore", "basis": "USER_STATED",
			"source_refs": domain.Empty(), "rationale": "fixture continuation", "supersedes_id": nil, "acceptance_check_ids": domain.Empty()}, stateTag, 201)
	requirement, _ = backupHTTP(t, svc, owner.Session.Token, "POST", projectPath+"/requirements/"+domain.Str(requirement, "id")+"/actions",
		domain.Object{"action": "ACCEPT", "reason": "fixture continuation", "source_validation_refs": domain.Empty()}, requirementTag, 200)
	_, stateTag = backupHTTP(t, svc, owner.Session.Token, "GET", projectPath+"/state", nil, "", 200)
	contract := domain.Object{"contract_hash": domain.Digest([]byte("backup-smoke-contract")), "contract_revision": 1,
		"checks": []any{domain.Object{"check_id": "backup-continue", "kind": "DETERMINISTIC", "required": true,
			"expected": "same pending task", "command_key": "test.backup", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}},
		"require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": domain.Now()}
	goal, goalTag := backupHTTP(t, svc, owner.Session.Token, "POST", projectPath+"/goals",
		domain.Object{"title": "continue backup task", "original_intent": "preserve next step", "scope": "PROJECT",
			"requirement_refs": []any{domain.Ref(requirement, "Requirement")}, "problem_ids": []any{"backup-source"},
			"deliverables": []any{"same pending task"}, "acceptance_contract": contract}, stateTag, 201)
	goalID := domain.Str(goal, "id")
	task, _ := backupHTTP(t, svc, owner.Session.Token, "POST", projectPath+"/tasks",
		domain.Object{"goal_id": goalID, "title": "resume this exact task", "task_type": "fixture", "stage": "verification",
			"dependency_task_ids": domain.Empty(), "requirement_refs": []any{domain.Ref(requirement, "Requirement")},
			"input_refs": domain.Empty(), "acceptance_contract": contract, "origin_problem_id": "backup-source",
			"candidate_id": "backup-candidate", "stop_policy": domain.Object{"wall_time_seconds": 60,
				"max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no effective progress"}}}, goalTag, 201)
	taskID := domain.Str(task, "id")
	sessionID := "backup-smoke-session"
	modelRef, buildID, title := "fixture-model-ref", "w1802-fixture-core-build", "Continued fixture session"
	now := time.Now().UTC()
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := domain.MapClientSession(ctx, tx, domain.ClientSession{ID: sessionID, ProjectID: projectID,
		Revision: 1, CreatedAt: now, UpdatedAt: now, WriterEpoch: 1, WriterClientID: "backup-smoke-cli",
		UpstreamSession: "backup-smoke-native", WorkspaceRef: &ref, GoalID: &goalID, TaskID: &taskID,
		ModelConfigRef: &modelRef, CoreBuildID: &buildID, Title: &title,
		Protocol: domain.ClientSessionProtocol}); err != nil {
		t.Fatal(err)
	}
	if err := tx.Commit(); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}

	goBinary := filepath.Join(runtime.GOROOT(), "bin", "go.exe")
	if selected := os.Getenv("RESEARCHOS_GO"); selected != "" {
		goBinary = selected
	}
	backupBinary := filepath.Join(root, "backup.exe")
	build := exec.Command(goBinary, "build", "-o", backupBinary, "./ops/backup")
	build.Dir = repo
	if output, err := build.CombinedOutput(); err != nil {
		t.Fatalf("build production backup command: %v\n%s", err, output)
	}
	key := filepath.Join(root, "recovery.key")
	if output, err := backupCLI(t, backupBinary, repo, "keygen", "--key-file", key); err != nil {
		t.Fatalf("production keygen: %v\n%s", err, output)
	}
	backup := filepath.Join(root, "encrypted-backup")
	if output, err := backupCLI(t, backupBinary, repo, "create", "--db", filepath.Join(sourceData, "researchos.sqlite"),
		"--out", backup, "--key-file", key, "--root", repo); err != nil {
		t.Fatalf("production backup: %v\n%s", err, output)
	}
	if raw, err := os.ReadFile(filepath.Join(backup, "manifest.json")); err != nil || strings.Contains(string(raw), workspace) || strings.Contains(string(raw), "package continued") {
		t.Fatal("workspace path or content leaked to plaintext manifest")
	}
	// The ordinary library path must not silently drop an active workspace.
	sourceCheck, err := store.Open(filepath.Join(sourceData, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	checkService, err := domain.New(sourceCheck, filepath.Join(repo, "spec", "v2.0", "contracts"), filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		sourceCheck.Close()
		t.Fatal(err)
	}
	_, omitted := checkService.CreateBackup(ctx, filepath.Join(root, "invalid-omission"), []byte(strings.Repeat("k", 32)))
	sourceCheck.Close()
	if omitted == nil || !strings.Contains(omitted.Error(), "BACKUP_WORKSPACE_SOURCE_REQUIRED") {
		t.Fatalf("active workspace was silently omitted: %v", omitted)
	}
	// The production command rejects a backup destination inside its source
	// workspace and names the failed scope instead of recursing into itself.
	if output, err := backupCLI(t, backupBinary, repo, "create", "--db", filepath.Join(sourceData, "researchos.sqlite"),
		"--out", filepath.Join(workspace, "recursive-backup"), "--key-file", key, "--root", repo); err == nil || !strings.Contains(string(output), "BACKUP_WORKSPACE_RECURSION") {
		t.Fatalf("recursive workspace backup did not fail closed: %v %s", err, output)
	}
	oversized := filepath.Join(workspace, "src", "oversized.bin")
	file, err := os.OpenFile(oversized, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	if err := file.Truncate(domain.BackupWorkspaceMaxFileBytes + 1); err != nil {
		file.Close()
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}
	if output, err := backupCLI(t, backupBinary, repo, "create", "--db", filepath.Join(sourceData, "researchos.sqlite"),
		"--out", filepath.Join(root, "invalid-limit"), "--key-file", key, "--root", repo); err == nil || !strings.Contains(string(output), "BACKUP_WORKSPACE_LIMIT") {
		t.Fatalf("oversized workspace item was omitted: %v %s", err, output)
	}
	if err := os.Remove(oversized); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(workspace, "src", "main.go"), []byte("source changed after backup\n"), 0600); err != nil {
		t.Fatal(err)
	}
	restoredRoot := filepath.Join(root, "restored-data")
	if output, err := backupCLI(t, backupBinary, repo, "restore", "--as-data-root", "--backup", backup, "--out", restoredRoot,
		"--key-file", key, "--root", repo); err != nil {
		t.Fatalf("production restore: %v\n%s", err, output)
	}
	restoredFile := filepath.Join(domain.BackupWorkspaceDestination(restoredRoot, ref), "src", "main.go")
	content, err := os.ReadFile(restoredFile)
	if err != nil || string(content) != "package continued\n" {
		t.Fatalf("restored workspace content changed: %v %q", err, content)
	}
	if info, err := os.Stat(filepath.Join(domain.BackupWorkspaceDestination(restoredRoot, ref), "empty")); err != nil || !info.IsDir() {
		t.Fatalf("empty workspace directory lost: %v", err)
	}
	restoredDB, err := store.Open(filepath.Join(restoredRoot, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer restoredDB.Close()
	restoredHost := backupTestHost(t, restoredDB, restoredRoot, repo)
	if len(restoredHost.Roots()) != 1 || restoredHost.Roots()[0].Ref != ref || restoredHost.Roots()[0].RealPath != domain.BackupWorkspaceDestination(restoredRoot, ref) {
		t.Fatalf("new Host did not pin the same workspace ref: %+v", restoredHost.Roots())
	}
	if _, err := restoredHost.ResolveWorkspace(ref, "src/main.go", host.AccessReadWrite); err != nil {
		t.Fatalf("restored Host could not authorize the same workspace: %v", err)
	}
	if restoredHost.CredentialStatus(credentialRef) != host.StatusMissing {
		t.Fatal("old host credential vault was copied into new data root")
	}
	restoredService, err := domain.New(restoredDB, filepath.Join(repo, "spec", "v2.0", "contracts"), filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		t.Fatal(err)
	}
	binding, err := restoredService.WorkspaceBindingFor(ctx, principal, localworkspace.NewAuthority(restoredHost), ref)
	if err != nil || binding.RealPath != domain.BackupWorkspaceDestination(restoredRoot, ref) || binding.ProjectID == nil || *binding.ProjectID != projectID {
		t.Fatalf("same project binding did not survive restore: %+v %v", binding, err)
	}
	var restoredProject, restoredWorkspace, restoredGoal, restoredTask string
	if err := restoredDB.QueryRow(`SELECT project_id,workspace_ref,goal_id,task_id FROM client_sessions WHERE id=?`, sessionID).
		Scan(&restoredProject, &restoredWorkspace, &restoredGoal, &restoredTask); err != nil ||
		restoredProject != projectID || restoredWorkspace != ref || restoredGoal != goalID || restoredTask != taskID {
		t.Fatalf("same session/Goal/Task not recovered: %q %q %q %q %v", restoredProject, restoredWorkspace, restoredGoal, restoredTask, err)
	}
	var taskStatus string
	if err := restoredDB.QueryRow(`SELECT json_extract(body,'$.status') FROM domain_objects WHERE project=? AND kind='Task' AND id=?`, projectID, taskID).Scan(&taskStatus); err != nil || taskStatus != "DRAFT" {
		t.Fatalf("next Task state was reset: %s %v", taskStatus, err)
	}
	snapshotTx, err := restoredDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if err != nil {
		t.Fatal(err)
	}
	snapshot, err := domain.BuildSessionSnapshot(ctx, snapshotTx, doc, projectID, sessionID)
	snapshotTx.Rollback()
	if err != nil || snapshot["session_id"] != sessionID || snapshot["workspace_ref"] != ref ||
		snapshot["model_config_ref"] != modelRef || snapshot["core_build_id"] != buildID || snapshot["goal_id"] != goalID {
		t.Fatalf("typed session snapshot incomplete after restore: %v %+v", err, snapshot)
	}
	// A restored data root must itself be a valid production backup source. The
	// second backup lives outside both data roots, then restores into a third,
	// empty location without consulting the original Host or workspace.
	originalDB, err := os.ReadFile(filepath.Join(sourceData, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	secondBackup := filepath.Join(root, "second-encrypted-backup")
	if output, err := backupCLI(t, backupBinary, repo, "create", "--db", filepath.Join(restoredRoot, "researchos.sqlite"),
		"--out", secondBackup, "--key-file", key, "--root", repo); err != nil {
		t.Fatalf("production rebackup after restore: %v\n%s", err, output)
	}
	secondRoot := filepath.Join(root, "second-restored-data")
	if output, err := backupCLI(t, backupBinary, repo, "restore", "--as-data-root", "--backup", secondBackup,
		"--out", secondRoot, "--key-file", key, "--root", repo); err != nil {
		t.Fatalf("production second restore: %v\n%s", err, output)
	}
	secondDB, err := store.Open(filepath.Join(secondRoot, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer secondDB.Close()
	secondHost := backupTestHost(t, secondDB, secondRoot, repo)
	secondPath := domain.BackupWorkspaceDestination(secondRoot, ref)
	if len(secondHost.Roots()) != 1 || secondHost.Roots()[0].Ref != ref || secondHost.Roots()[0].RealPath != secondPath ||
		secondPath == binding.RealPath || secondPath == workspace {
		t.Fatalf("second Host root did not move to a fresh pin: %+v", secondHost.Roots())
	}
	if _, err := secondHost.ResolveWorkspace(ref, "src/main.go", host.AccessReadWrite); err != nil {
		t.Fatalf("second Host cannot use recovered root: %v", err)
	}
	secondContent, err := os.ReadFile(filepath.Join(secondPath, "src", "main.go"))
	if err != nil || string(secondContent) != "package continued\n" {
		t.Fatalf("second restore changed source bytes: %v %q", err, secondContent)
	}
	var secondProject, secondWorkspace, secondGoal, secondTask string
	if err := secondDB.QueryRow(`SELECT project_id,workspace_ref,goal_id,task_id FROM client_sessions WHERE id=?`, sessionID).
		Scan(&secondProject, &secondWorkspace, &secondGoal, &secondTask); err != nil ||
		secondProject != projectID || secondWorkspace != ref || secondGoal != goalID || secondTask != taskID {
		t.Fatalf("second restore lost session/Goal/Task identity: %q %q %q %q %v", secondProject, secondWorkspace, secondGoal, secondTask, err)
	}
	secondService, err := domain.New(secondDB, filepath.Join(repo, "spec", "v2.0", "contracts"), filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		t.Fatal(err)
	}
	secondBinding, err := secondService.WorkspaceBindingFor(ctx, principal, localworkspace.NewAuthority(secondHost), ref)
	if err != nil || secondBinding.RealPath != secondPath || secondBinding.ProjectID == nil || *secondBinding.ProjectID != projectID {
		t.Fatalf("second restore binding points outside fresh root: %+v %v", secondBinding, err)
	}
	secondTx, err := secondDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if err != nil {
		t.Fatal(err)
	}
	secondSnapshot, err := domain.BuildSessionSnapshot(ctx, secondTx, doc, projectID, sessionID)
	secondTx.Rollback()
	if err != nil || secondSnapshot["session_id"] != snapshot["session_id"] ||
		secondSnapshot["goal_id"] != snapshot["goal_id"] || secondSnapshot["model_config_ref"] != snapshot["model_config_ref"] ||
		secondSnapshot["core_build_id"] != snapshot["core_build_id"] || secondSnapshot["workspace_ref"] != ref {
		t.Fatalf("second typed session snapshot changed: %v %+v", err, secondSnapshot)
	}
	stillOriginalDB, err := os.ReadFile(filepath.Join(sourceData, "researchos.sqlite"))
	if err != nil || domain.Digest(stillOriginalDB) != domain.Digest(originalDB) {
		t.Fatalf("rebackup changed original source DB: %v", err)
	}
	stillOriginalWorkspace, err := os.ReadFile(filepath.Join(workspace, "src", "main.go"))
	if err != nil || string(stillOriginalWorkspace) != "source changed after backup\n" {
		t.Fatalf("rebackup changed original source workspace: %v %q", err, stillOriginalWorkspace)
	}
	independentLimits := domain.BackupWorkspaceLimits{MaxFiles: 100, MaxDirs: 100, MaxBytes: 1000000, MaxFileBytes: 1000000}
    wrongRef := *secondBinding
    wrongRef.AuthorizedRef = "wsref-independent-wrong-ref"
    if _, err := secondHost.SnapshotWorkspace(ctx, wrongRef, filepath.Join(root, "wrong-ref-backup"), independentLimits); err == nil || !strings.Contains(err.Error(), "BACKUP_WORKSPACE_RECURSION") {
        t.Fatalf("INDEPENDENT_MISMATCHED_REF_ACCEPTED: %v", err)
    }
    t.Log("INDEPENDENT_MISMATCHED_REF_REJECTED")
    if _, err := secondHost.SnapshotWorkspace(ctx, *secondBinding, filepath.Join(secondPath, "inside-output"), independentLimits); err == nil || !strings.Contains(err.Error(), "BACKUP_WORKSPACE_RECURSION") {
        t.Fatalf("INDEPENDENT_RESTORED_ROOT_OUTPUT_ACCEPTED: %v", err)
    }
    t.Log("INDEPENDENT_RESTORED_ROOT_OUTPUT_REJECTED")
    junction := filepath.Join(secondPath, "independent-junction")
    junctionTarget := t.TempDir()
    makeJunction := exec.Command("cmd.exe", "/d", "/c", "mklink", "/J", junction, junctionTarget)
    if output, err := makeJunction.CombinedOutput(); err != nil { t.Fatalf("INDEPENDENT_JUNCTION_SETUP_FAILED: %v %s", err, output) }
    if _, err := secondHost.SnapshotWorkspace(ctx, *secondBinding, filepath.Join(root, "junction-backup"), independentLimits); err == nil {
        t.Fatal("INDEPENDENT_JUNCTION_ACCEPTED")
    } else { t.Logf("INDEPENDENT_JUNCTION_REJECTED: %v", err) }
    if err := os.Remove(junction); err != nil { t.Fatal(err) }
    if err := secondHost.RevokeWorkspace(ref); err != nil { t.Fatal(err) }
    if _, err := secondHost.SnapshotWorkspace(ctx, *secondBinding, filepath.Join(root, "revoked-backup"), independentLimits); err == nil || !strings.Contains(err.Error(), "BACKUP_WORKSPACE_ROOT_NOT_PINNED") {
        t.Fatalf("INDEPENDENT_REVOKED_PIN_ACCEPTED: %v", err)
    }
    t.Log("INDEPENDENT_REVOKED_PIN_REJECTED")
	// A real second Host/domain registration under the data root is not the
	// restored workspace path. Its matching pin must still be refused.
	unrelatedPath := filepath.Join(restoredRoot, "unrelated-workspace")
	if err := os.Mkdir(unrelatedPath, 0700); err != nil {
		t.Fatal(err)
	}
	otherFrame, err := json.Marshal(map[string]any{"kind": host.KindWorkspaceChooseRequest,
		"client_id": "backup-smoke-cli", "payload": map[string]any{"requested_path": unrelatedPath, "requested_access": host.AccessReadWrite}})
	if err != nil {
		t.Fatal(err)
	}
	otherReply, err := restoredHost.HandleNative(otherFrame, true, func(string) (string, error) { return unrelatedPath, nil })
	if err != nil {
		t.Fatal(err)
	}
	var otherChoice struct {
		Payload struct {
			Ref string `json:"selection_ref"`
		} `json:"payload"`
	}
	if err := json.Unmarshal(otherReply, &otherChoice); err != nil || otherChoice.Payload.Ref == "" {
		t.Fatalf("nonmatching Host path was not genuinely pinned: %v", err)
	}
	otherRegistered, err := restoredService.RegisterWorkspace(ctx, principal, localworkspace.NewAuthority(restoredHost), doc,
		domain.RegisterWorkspaceInput{SelectionRef: otherChoice.Payload.Ref, DisplayName: "nonmatching data-root child",
			RequestedAccess: host.AccessReadWrite, ClientID: "backup-smoke-cli", CommandID: "backup-smoke-other-register"})
	if err != nil {
		t.Fatal(err)
	}
	otherRef := domain.Str(otherRegistered, "authorized_workspace_ref")
	otherBinding, err := restoredService.WorkspaceBindingFor(ctx, principal, localworkspace.NewAuthority(restoredHost), otherRef)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := restoredHost.SnapshotWorkspace(ctx, *otherBinding, filepath.Join(root, "outside-backup"),
		domain.BackupWorkspaceLimits{MaxFiles: 1, MaxDirs: 1, MaxBytes: 1024, MaxFileBytes: 1024}); err == nil || !strings.Contains(err.Error(), "BACKUP_WORKSPACE_RECURSION") {
		t.Fatalf("nonmatching pinned data-root child gained backup exception: %v", err)
	}
	// A failed target pin publishes no active authorization to either the old
	// path or the new one. The original backup remains available for recovery.
	keyBytes, err := os.ReadFile(key)
	if err != nil {
		t.Fatal(err)
	}
	manifestRaw, err := os.ReadFile(filepath.Join(backup, "manifest.json"))
	if err != nil {
		t.Fatal(err)
	}
	var manifest domain.BackupManifest
	if err := json.Unmarshal(manifestRaw, &manifest); err != nil {
		t.Fatal(err)
	}
	contracts, err := domain.LoadContracts(filepath.Join(repo, "spec", "v2.0", "contracts"))
	if err != nil {
		t.Fatal(err)
	}
	failedRoot := filepath.Join(root, "failed-pin-data")
	_, err = domain.RestoreBackup(ctx, backup, failedRoot, domain.RestoreOptions{Key: keyBytes, Contracts: contracts,
		SupportedMigrations: manifest.Migrations, DatabaseName: "researchos.sqlite",
		WorkspaceTarget: func(context.Context, string, []domain.WorkspaceRestoreRequest) ([]domain.WorkspaceRestorePin, error) {
			return nil, fmt.Errorf("fixture pin failure")
		}})
	if err == nil || !strings.Contains(err.Error(), "RESTORE_WORKSPACE_PIN_FAILED") {
		t.Fatalf("failed pin was treated as successful restore: %v", err)
	}
	pending, err := store.Open(filepath.Join(failedRoot, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	var pendingStatus, pendingPath string
	err = pending.QueryRow(`SELECT json_extract(body,'$.status'),json_extract(body,'$.real_path') FROM domain_objects WHERE kind='WorkspaceBinding' AND id=?`, ref).Scan(&pendingStatus, &pendingPath)
	pending.Close()
	if err != nil || pendingStatus != "RESTORE_PENDING" || pendingPath != domain.BackupWorkspaceDestination(failedRoot, ref) {
		t.Fatalf("failed restore retained write authorization: %s %s %v", pendingStatus, pendingPath, err)
	}
	t.Logf("W18_ASSERTION %s", domain.Bytes(domain.Object{"assertion_id": "W18-02-CLI-WORKSPACE-CONTINUATION", "expected": true, "actual": true,
		"status": "PASS", "evidence": domain.Object{"project_id": projectID, "session_id": sessionID, "workspace_ref": ref,
			"goal_id": goalID, "task_id": taskID, "next_task_status": taskStatus, "typed_snapshot": true}}))
	t.Logf("W18_ASSERTION %s", domain.Bytes(domain.Object{"assertion_id": "W18-02-FAIL-CLOSED", "expected": true, "actual": true,
		"status": "PASS", "evidence": domain.Object{"omission_rejected": true, "recursive_backup_rejected": true,
			"oversize_rejected": true, "failed_pin_status": pendingStatus}}))
	t.Logf("W18_ASSERTION %s", domain.Bytes(domain.Object{"assertion_id": "W18-02-NEW-HOST-PIN", "expected": true, "actual": true,
		"status": "PASS", "evidence": domain.Object{"root_ref": ref, "new_path": binding.RealPath,
			"old_path_used": binding.RealPath == workspace, "old_credential_status": host.StatusMissing}}))
	t.Logf("W18_ASSERTION %s", domain.Bytes(domain.Object{"assertion_id": "W18-02-REBACKUP-ROUNDTRIP", "expected": true, "actual": true,
		"status": "PASS", "evidence": domain.Object{"workspace_ref": ref, "project_id": projectID, "session_id": sessionID,
			"goal_id": goalID, "task_id": taskID, "first_restored_path": binding.RealPath, "second_restored_path": secondPath,
			"source_db_unchanged": true, "source_workspace_unchanged": true, "nonmatching_child_rejected": true}}))
}

//go:build windows

// gui_fixture constructs a finite FIXTURE project through production Host and
// domain APIs, then invokes the compiled production backup CLI. The output is
// deliberately kept under the caller's ignored .local directory so a second
// CLI/desktop process can inspect the restored data root after this exits.
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

type commandRecord struct {
	Name string   `json:"name"`
	Args []string `json:"args"`
	Exit int      `json:"exit"`
	Text string   `json:"output"`
}

func main() {
	repoFlag := flag.String("repo", "", "repository root")
	dirFlag := flag.String("dir", "", "new ignored fixture directory")
	backupFlag := flag.String("backup-exe", "", "compiled production backup executable")
	flag.Parse()
	if err := run(*repoFlag, *dirFlag, *backupFlag); err != nil {
		fmt.Fprintln(os.Stderr, "gui fixture:", err)
		os.Exit(1)
	}
}

func run(repo, dir, backupExe string) error {
	if repo == "" || dir == "" || backupExe == "" {
		return errors.New("--repo, --dir, and --backup-exe are required")
	}
	repo, err := filepath.Abs(repo)
	if err != nil {
		return err
	}
	dir, err = filepath.Abs(dir)
	if err != nil {
		return err
	}
	backupExe, err = filepath.Abs(backupExe)
	if err != nil {
		return err
	}
	if err = os.Mkdir(dir, 0700); err != nil {
		return fmt.Errorf("fixture directory must be new: %w", err)
	}
	ctx := context.Background()
	sourceData := filepath.Join(dir, "source-data")
	workspace := filepath.Join(dir, "chosen-workspace")
	if err = os.MkdirAll(filepath.Join(workspace, "src"), 0700); err != nil {
		return err
	}
	if err = os.Mkdir(filepath.Join(workspace, "empty"), 0700); err != nil {
		return err
	}
	const original = "package continued\n"
	if err = os.WriteFile(filepath.Join(workspace, "src", "main.go"), []byte(original), 0600); err != nil {
		return err
	}
	if err = os.Mkdir(sourceData, 0700); err != nil {
		return err
	}
	db, err := store.Open(filepath.Join(sourceData, "researchos.sqlite"))
	if err != nil {
		return err
	}
	defer db.Close()
	if err = store.Bootstrap(ctx, db, filepath.Join(repo, "migrations", "sqlite", "0001_bootstrap.sql")); err != nil {
		return err
	}
	svc, err := domain.New(db, filepath.Join(repo, "spec", "v2.0", "contracts"), filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		return err
	}
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(sourceData, "host"), ContractsDir: filepath.Join(repo, "spec", "v2.0", "contracts"),
		MigrationFile: filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"), SchemaDir: filepath.Join(repo, "internal", "api", "contracts")})
	if err != nil {
		return err
	}
	owner, err := h.BootstrapOwner(ctx)
	if err != nil {
		return err
	}
	frame := domain.Bytes(domain.Object{"kind": host.KindWorkspaceChooseRequest, "client_id": "w1802-gui-fixture",
		"payload": domain.Object{"requested_path": workspace, "requested_access": host.AccessReadWrite}})
	reply, err := h.HandleNative(frame, true, func(string) (string, error) { return workspace, nil })
	if err != nil {
		return err
	}
	var choice struct {
		Payload struct {
			Ref string `json:"selection_ref"`
		} `json:"payload"`
	}
	if err = json.Unmarshal(reply, &choice); err != nil || choice.Payload.Ref == "" {
		return errors.New("native chooser did not return a selection reference")
	}
	doc, err := api.ClientProtocolDocument()
	if err != nil {
		return err
	}
	principal := domain.Principal{ID: owner.PrincipalID, Roles: []string{"OWNER"}, CanCreateProject: true}
	authority := localworkspace.NewAuthority(h)
	registered, err := svc.RegisterWorkspace(ctx, principal, authority, doc, domain.RegisterWorkspaceInput{
		SelectionRef: choice.Payload.Ref, DisplayName: "continued workspace", RequestedAccess: host.AccessReadWrite,
		ClientID: "w1802-gui-fixture", CommandID: "w1802-gui-register"})
	if err != nil {
		return err
	}
	ref := domain.Str(registered, "authorized_workspace_ref")
	project, err := svc.BootstrapProject(ctx, principal, authority, doc, localworkspace.NewScanner(), domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: ref, DisplayName: "continued project", ClientID: "w1802-gui-fixture",
		CommandID: "w1802-gui-project", MeasurementMode: "FIXTURE"})
	if err != nil {
		return err
	}
	projectID := domain.Str(project, "project_id")
	projectPath := "/v1/projects/" + projectID
	_, stateTag, err := call(svc, owner.Session.Token, "GET", projectPath+"/state", nil, "", 200)
	if err != nil {
		return err
	}
	requirement, requirementTag, err := call(svc, owner.Session.Token, "POST", projectPath+"/requirements",
		domain.Object{"requirement_key": "W18-GUI-BACKUP", "text": "continue the same work after restore", "basis": "USER_STATED",
			"source_refs": domain.Empty(), "rationale": "constructed fixture continuation", "supersedes_id": nil, "acceptance_check_ids": domain.Empty()}, stateTag, 201)
	if err != nil {
		return err
	}
	requirement, _, err = call(svc, owner.Session.Token, "POST", projectPath+"/requirements/"+domain.Str(requirement, "id")+"/actions",
		domain.Object{"action": "ACCEPT", "reason": "constructed fixture continuation", "source_validation_refs": domain.Empty()}, requirementTag, 200)
	if err != nil {
		return err
	}
	_, stateTag, err = call(svc, owner.Session.Token, "GET", projectPath+"/state", nil, "", 200)
	if err != nil {
		return err
	}
	contract := domain.Object{"contract_hash": domain.Digest([]byte("w1802-gui-fixture-contract")), "contract_revision": 1,
		"checks": []any{domain.Object{"check_id": "w1802-gui-continue", "kind": "DETERMINISTIC", "required": true,
			"expected": "same pending task", "command_key": "test.backup.gui", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}},
		"require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": domain.Now()}
	goal, goalTag, err := call(svc, owner.Session.Token, "POST", projectPath+"/goals",
		domain.Object{"title": "continue backup task", "original_intent": "preserve next step", "scope": "PROJECT",
			"requirement_refs": []any{domain.Ref(requirement, "Requirement")}, "problem_ids": []any{"backup-source"},
			"deliverables": []any{"same pending task"}, "acceptance_contract": contract}, stateTag, 201)
	if err != nil {
		return err
	}
	goalID := domain.Str(goal, "id")
	task, _, err := call(svc, owner.Session.Token, "POST", projectPath+"/tasks",
		domain.Object{"goal_id": goalID, "title": "resume this exact task", "task_type": "fixture", "stage": "verification",
			"dependency_task_ids": domain.Empty(), "requirement_refs": []any{domain.Ref(requirement, "Requirement")},
			"input_refs": domain.Empty(), "acceptance_contract": contract, "origin_problem_id": "backup-source",
			"candidate_id": "backup-candidate", "stop_policy": domain.Object{"wall_time_seconds": 60,
				"max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no effective progress"}}}, goalTag, 201)
	if err != nil {
		return err
	}
	taskID := domain.Str(task, "id")
	sessionID := "w1802-gui-session-" + domain.ID()
	modelRef, buildID, title := "fixture-model-ref", "w1802-gui-fixture-core", "Continued fixture session"
	now := time.Now().UTC()
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	if err = domain.MapClientSession(ctx, tx, domain.ClientSession{ID: sessionID, ProjectID: projectID,
		Revision: 1, CreatedAt: now, UpdatedAt: now, WriterEpoch: 1, WriterClientID: "w1802-gui-fixture",
		UpstreamSession: "w1802-gui-native-fixture", WorkspaceRef: &ref, GoalID: &goalID, TaskID: &taskID,
		ModelConfigRef: &modelRef, CoreBuildID: &buildID, Title: &title, Protocol: domain.ClientSessionProtocol}); err != nil {
		tx.Rollback()
		return err
	}
	const message = "Constructed fixture: resume the next task after restoring this backup."
	for i, part := range []domain.Object{{"phase": "START", "text": "", "content_offset_utf8_bytes": 0},
		{"phase": "DELTA", "text": message, "content_offset_utf8_bytes": 0},
		{"phase": "END", "text": "", "content_offset_utf8_bytes": len([]byte(message))}} {
		part["message_id"], part["role"], part["part_index"] = "w1802-gui-fixture-message", "USER", 0
		kind, sequence := "MESSAGE", int64(i+1)
		eventID, protocol := domain.ID(), domain.ProtocolV2
		ev := &domain.SessionEvent{EventID: &eventID, SessionID: &sessionID, Sequence: &sequence,
			CoreBuildID: &buildID, ProtocolVersion: &protocol, Kind: &kind, Payload: domain.Bytes(part)}
		if err = domain.AppendSessionEvent(ctx, tx, doc, projectID, ev, 1, sequence); err != nil {
			tx.Rollback()
			return err
		}
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	if err = db.Close(); err != nil {
		return err
	}
	key := filepath.Join(dir, "recovery.key")
	backup := filepath.Join(dir, "encrypted-backup")
	restoredRoot := filepath.Join(dir, "restored-data")
	var commands []commandRecord
	for _, step := range []struct {
		name string
		args []string
	}{{"keygen", []string{"keygen", "--key-file", key}},
		{"create", []string{"create", "--db", filepath.Join(sourceData, "researchos.sqlite"), "--out", backup, "--key-file", key, "--root", repo}}} {
		commands, err = command(repo, backupExe, commands, step.name, step.args...)
		if err != nil {
			return err
		}
	}
	if err = os.WriteFile(filepath.Join(workspace, "src", "main.go"), []byte("source changed after backup\n"), 0600); err != nil {
		return err
	}
	commands, err = command(repo, backupExe, commands, "restore", "restore", "--as-data-root", "--backup", backup,
		"--out", restoredRoot, "--key-file", key, "--root", repo)
	if err != nil {
		return err
	}
	if err = writeJSON(filepath.Join(dir, "setup-commands.json"), commands); err != nil {
		return err
	}
	restoredPath := filepath.Join(domain.BackupWorkspaceDestination(restoredRoot, ref), "src", "main.go")
	content, err := os.ReadFile(restoredPath)
	if err != nil || string(content) != original {
		return fmt.Errorf("restored workspace differs from pre-backup bytes: %w", err)
	}
	if restoredPath == filepath.Join(workspace, "src", "main.go") {
		return errors.New("restore points at the original workspace")
	}
	restoredDB, err := store.Open(filepath.Join(restoredRoot, "researchos.sqlite"))
	if err != nil {
		return err
	}
	defer restoredDB.Close()
	restoredHost, err := host.New(host.Config{DB: restoredDB, Dir: filepath.Join(restoredRoot, "host"),
		ContractsDir: filepath.Join(repo, "spec", "v2.0", "contracts"), MigrationFile: filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"),
		SchemaDir: filepath.Join(repo, "internal", "api", "contracts")})
	if err != nil {
		return err
	}
	if len(restoredHost.Roots()) != 1 || restoredHost.Roots()[0].Ref != ref || restoredHost.Roots()[0].RealPath != domain.BackupWorkspaceDestination(restoredRoot, ref) {
		return errors.New("new Host did not pin restored workspace reference")
	}
	if _, err = restoredHost.ResolveWorkspace(ref, "src/main.go", host.AccessReadWrite); err != nil {
		return err
	}
	snapshotTx, err := restoredDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if err != nil {
		return err
	}
	snapshot, err := domain.BuildSessionSnapshot(ctx, snapshotTx, doc, projectID, sessionID)
	snapshotTx.Rollback()
	if err != nil {
		return err
	}
	if snapshot["session_id"] != sessionID || snapshot["goal_id"] != goalID || snapshot["workspace_ref"] != ref ||
		snapshot["model_config_ref"] != modelRef || snapshot["core_build_id"] != buildID || snapshot["title"] != title || len(domain.Arr(snapshot, "messages")) != 1 {
		return errors.New("restored typed session snapshot incomplete")
	}
	metadata := domain.Object{"fixture_mode": "FIXTURE", "fixture_origin": "constructed Host chooser callback and domain journal",
		"project_id": projectID, "session_id": sessionID, "goal_id": goalID, "task_id": taskID, "workspace_ref": ref,
		"session_title": title, "goal_title": "continue backup task", "task_title": "resume this exact task",
		"event_cursor": snapshot["event_sequence"], "model_config_ref": modelRef, "core_build_id": buildID,
		"source_data_root": sourceData, "source_workspace": workspace, "restored_data_root": restoredRoot,
		"restored_workspace":    domain.BackupWorkspaceDestination(restoredRoot, ref),
		"original_content_hash": domain.Digest([]byte(original)), "restored_content_hash": domain.Digest(content),
		"source_changed_after_backup": true, "new_host_pinned_restore": true, "provider_calls": 0}
	if err = writeJSON(filepath.Join(dir, "metadata.json"), metadata); err != nil {
		return err
	}
	return json.NewEncoder(os.Stdout).Encode(metadata)
}

func call(svc *domain.Service, token, method, path string, body any, etag string, want int) (domain.Object, string, error) {
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
		return nil, "", fmt.Errorf("%s %s returned %d; expected %d", method, path, response.Code, want)
	}
	var value domain.Object
	if err := json.Unmarshal(response.Body.Bytes(), &value); err != nil {
		return nil, "", err
	}
	return value, response.Header().Get("ETag"), nil
}

func command(repo, binary string, records []commandRecord, name string, args ...string) ([]commandRecord, error) {
	cmd := exec.Command(binary, args...)
	cmd.Dir = repo
	output, err := cmd.CombinedOutput()
	exit := 0
	if err != nil {
		var status *exec.ExitError
		if errors.As(err, &status) {
			exit = status.ExitCode()
		} else {
			exit = -1
		}
	}
	records = append(records, commandRecord{Name: name, Args: args, Exit: exit, Text: string(output)})
	if err != nil {
		return records, fmt.Errorf("production backup %s exited %d: %w", name, exit, err)
	}
	return records, nil
}

func writeJSON(path string, value any) error {
	raw, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0600)
}

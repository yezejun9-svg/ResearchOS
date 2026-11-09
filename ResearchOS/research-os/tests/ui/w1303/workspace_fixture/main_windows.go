//go:build windows

// workspace_fixture serves a disposable W13 filesystem project through the
// production v2 API and native Host. The one folder-selection callback used
// during setup is an explicit fixture, not evidence of a human OS dialog.
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"time"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

// Desktop uses this same client_id when it opens the seeded Session, so the
// existing writer attribution remains valid without a fabricated epoch.
const clientID = "desktop-shell"

func runGit(root string, args ...string) error {
	cmd := exec.Command("git", append([]string{"-C", root}, args...)...)
	cmd.Env = append(os.Environ(), "GIT_TERMINAL_PROMPT=0", "GIT_CONFIG_NOSYSTEM=1")
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("git %s: %w: %s", strings.Join(args, " "), err, output)
	}
	return nil
}

func createRoot(dir string) (string, []byte, error) {
	root := filepath.Join(dir, "chosen")
	if err := os.MkdirAll(filepath.Join(root, "nested"), 0o700); err != nil {
		return "", nil, err
	}
	source := []byte("before\n")
	big := []byte(strings.Repeat("baseline fixture line\n", 30000))
	for name, body := range map[string][]byte{
		"source.txt": source, "large-diff.txt": big,
		filepath.Join("nested", "note.txt"): []byte("nested fixture\n"),
		"binary.dat":                        {0, 1, 2, 0xff, 0},
	} {
		if err := os.WriteFile(filepath.Join(root, name), body, 0o600); err != nil {
			return "", nil, err
		}
	}
	if err := runGit(root, "init", "-q"); err != nil {
		return "", nil, err
	}
	if err := runGit(root, "add", "--", "source.txt", "large-diff.txt", "nested/note.txt", "binary.dat"); err != nil {
		return "", nil, err
	}
	if err := runGit(root, "-c", "user.name=ResearchOS Fixture", "-c", "user.email=fixture@researchos.local", "commit", "-qm", "baseline"); err != nil {
		return "", nil, err
	}
	source = []byte("after fixture edit\r\nsecond changed line\n")
	if err := os.WriteFile(filepath.Join(root, "source.txt"), source, 0o600); err != nil {
		return "", nil, err
	}
	if err := os.WriteFile(filepath.Join(root, "large-diff.txt"), []byte(strings.Repeat("changed fixture line\n", 30000)), 0o600); err != nil {
		return "", nil, err
	}
	return root, source, nil
}

func command(ctx context.Context, client *http.Client, base, token, method, key string, project, session *string, revision, epoch any, payload domain.Object) (domain.Object, error) {
	body := domain.Object{
		"protocol_version": domain.ProtocolV2, "command_id": key, "client_id": clientID,
		"project_id": project, "session_id": session, "expected_revision": revision,
		"writer_epoch": epoch, "method": method, "payload": payload,
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, base+"/v2/command", bytes.NewReader(domain.Bytes(body)))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return nil, err
	}
	var reply domain.Object
	if err := json.Unmarshal(raw, &reply); err != nil {
		return nil, fmt.Errorf("%s returned invalid JSON: %w", method, err)
	}
	if resp.StatusCode != http.StatusOK || reply["status"] != "COMPLETED" {
		return nil, fmt.Errorf("%s refused (HTTP %d): %s", method, resp.StatusCode, raw)
	}
	result, ok := reply["result"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("%s omitted result", method)
	}
	return result, nil
}

func writeDiscovery(path, addr, dataDir, instanceID string) error {
	raw, err := json.Marshal(map[string]any{
		"url": "http://" + addr, "pid": os.Getpid(), "data_dir": dataDir,
		"host_instance_id": instanceID,
	})
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), "discovery-*.tmp")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if err := tmp.Chmod(0o600); err != nil {
		tmp.Close()
		return err
	}
	if _, err := tmp.Write(raw); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}

func run() error {
	dirFlag := flag.String("dir", "", "new private fixture directory below .local")
	webFlag := flag.String("web-dir", "apps/web/dist", "built web assets")
	permissionFlag := flag.Bool("permission", false, "explicit loopback SDK fixture for an original tool permission")
	transcriptFlag := flag.Bool("transcript", false, "explicit 201-message sealed transcript FIXTURE")
	flag.Parse()
	if *dirFlag == "" {
		return errors.New("-dir is required")
	}
	dir, err := filepath.Abs(*dirFlag)
	if err != nil {
		return err
	}
	local, err := filepath.Abs(".local")
	if err != nil {
		return err
	}
	relative, err := filepath.Rel(local, dir)
	if err != nil || relative == "." || relative == ".." || strings.HasPrefix(relative, ".."+string(os.PathSeparator)) {
		return errors.New("fixture directory must be a child of .local")
	}
	if _, err := os.Stat(dir); !errors.Is(err, os.ErrNotExist) {
		return errors.New("fixture directory must be new")
	}
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return err
	}
	root, source, err := createRoot(dir)
	if err != nil {
		return err
	}
	dataDir := filepath.Join(dir, "data")
	db, err := store.Open(filepath.Join(dataDir, "researchos.sqlite"))
	if err != nil {
		return err
	}
	defer db.Close()
	ctx := context.Background()
	if err := store.Bootstrap(ctx, db, "migrations/sqlite/0001_bootstrap.sql"); err != nil {
		return err
	}
	svc, err := domain.New(db, "spec/v2.0/contracts", "migrations/sqlite/0002_domain.sql")
	if err != nil {
		return err
	}
	migration, err := os.ReadFile("migrations/sqlite/next_v24_sessions.sql")
	if err != nil {
		return err
	}
	if _, err := db.Exec(string(migration)); err != nil {
		return err
	}
	if err := domain.EnsureClientSessionFence(ctx, db); err != nil {
		return err
	}
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(dataDir, "host"),
		ContractsDir: "spec/v2.0/contracts", MigrationFile: "migrations/sqlite/0002_domain.sql",
		SchemaDir: "internal/api/contracts"})
	if err != nil {
		return err
	}
	owner, err := h.BootstrapOwner(ctx)
	if err != nil {
		return err
	}
	frame := domain.Bytes(domain.Object{"kind": host.KindWorkspaceChooseRequest, "client_id": clientID,
		"payload": domain.Object{"requested_path": root, "requested_access": host.AccessReadWrite}})
	selected, err := h.HandleNative(frame, true, func(string) (string, error) { return root, nil })
	if err != nil {
		return err
	}
	var native domain.Object
	if err := json.Unmarshal(selected, &native); err != nil {
		return err
	}
	selection := native["payload"].(map[string]any)["selection_ref"].(string)

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return err
	}
	defer listener.Close()
	base := "http://" + listener.Addr().String()
	authority, scanner := localworkspace.NewAuthority(h), localworkspace.NewScanner()
	handler := &switchableHandler{h: api.HandlerWithLocalHost(db, *webFlag, svc, nil,
		h.InstanceID(), authority, scanner, h)}
	srv := &http.Server{Handler: handler,
		ReadHeaderTimeout: 5 * time.Second}
	go func() {
		if err := srv.Serve(listener); err != nil && !errors.Is(err, http.ErrServerClosed) {
			fmt.Fprintf(os.Stderr, "workspace fixture HTTP stopped: %v\n", err)
		}
	}()
	defer func() {
		shutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = srv.Shutdown(shutdown)
	}()
	nativeCtx, nativeCancel := context.WithCancel(context.Background())
	defer nativeCancel()
	go func() {
		if err := h.ServeNative(nativeCtx, host.PipeName(h.InstanceID())); err != nil && nativeCtx.Err() == nil {
			fmt.Fprintf(os.Stderr, "workspace fixture native Host stopped: %v\n", err)
		}
	}()
	client := &http.Client{Timeout: 10 * time.Second}
	token := owner.Session.Token
	reg, err := command(ctx, client, base, token, "workspace.register", "register-root", nil, nil, nil, nil,
		domain.Object{"selection_ref": selection, "display_name": "W13 filesystem FIXTURE", "requested_access": host.AccessReadWrite})
	if err != nil {
		return err
	}
	ref := reg["authorized_workspace_ref"].(string)
	proj, err := command(ctx, client, base, token, "project.bootstrap", "bootstrap-project", nil, nil, nil, nil,
		domain.Object{"authorized_workspace_ref": ref, "display_name": "W13 filesystem FIXTURE"})
	if err != nil {
		return err
	}
	project := proj["project_id"].(string)
	var permission *permissionProfile
	if *permissionFlag {
		permission, err = newPermissionProfile(source)
		if err != nil {
			return err
		}
		defer permission.server.Close()
	}
	coordinator, err := fixtureModelProfile(ctx, svc, h, client, base, token, project, dataDir, permission)
	if err != nil {
		return err
	}
	defer coordinator.Close()
	handler.swap(api.HandlerWithLocalHost(db, *webFlag, svc, coordinator,
		h.InstanceID(), authority, scanner, h))
	snap, err := command(ctx, client, base, token, "session.create", "create-session", &project, nil, nil, nil,
		domain.Object{"workspace_ref": ref, "model_config_ref": fixtureModelRef, "title": "W13 local files FIXTURE"})
	if err != nil {
		return err
	}
	session := snap["session_id"].(string)
	if permission != nil {
		return servePermissionFixture(ctx, db, coordinator, h, client, base, token, project, session, ref, root, dataDir, listener.Addr().String(), permission)
	}
	if *transcriptFlag {
		return serveTranscriptFixture(ctx, db, h, client, base, token, project, session, ref, root, dataDir, listener.Addr().String())
	}
	tree, err := command(ctx, client, base, token, "workspace.tree", "probe-tree", &project, &session, nil, nil,
		domain.Object{"workspace_ref": ref, "relative_path": ".", "cursor": nil, "limit": 100})
	if err != nil {
		return err
	}
	read, err := command(ctx, client, base, token, "workspace.read", "probe-read", &project, &session, nil, nil,
		domain.Object{"workspace_ref": ref, "relative_path": "source.txt", "max_bytes": 1024})
	if err != nil {
		return err
	}
	if read["text"] != string(source) || read["content_hash"] != domain.Digest(source) {
		return errors.New("typed workspace.read did not preserve fixture source bytes")
	}
	diff, err := command(ctx, client, base, token, "workspace.diff", "probe-diff", &project, &session, nil, nil,
		domain.Object{"workspace_ref": ref, "base": "HEAD", "relative_path": nil, "max_bytes": 128})
	if err != nil {
		return err
	}
	if diff["full_diff_artifact_ref"] == nil {
		return errors.New("typed workspace.diff did not seal large full patch")
	}
	note := []byte("nested fixture\n")
	imported, err := command(ctx, client, base, token, "artifact.import", "probe-import", &project, &session, 1, 1,
		domain.Object{"workspace_ref": ref, "relative_path": "nested/note.txt",
			"expected_content_hash": domain.Digest(note), "purpose": "ATTACHMENT"})
	if err != nil {
		return err
	}
	if imported["artifact_ref"] == nil {
		return errors.New("typed artifact.import omitted sealed artifact")
	}
	current, err := command(ctx, client, base, token, "session.get", "before-blocked-send", &project, &session, nil, nil, domain.Object{})
	if err != nil {
		return err
	}
	revision, err := domain.Num(current, "revision")
	if err != nil {
		return err
	}
	writer, ok := current["writer"].(map[string]any)
	if !ok {
		return errors.New("fixture session has no real writer lease")
	}
	epoch, err := domain.Num(writer, "epoch")
	if err != nil {
		return err
	}
	if _, err := command(ctx, client, base, token, "session.send", "persist-blocked-turn", &project, &session, revision, epoch,
		domain.Object{"text": "Save a bounded local draft. The fixture must not call a provider.", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"}); err != nil {
		return err
	}
	var taskID string
	if err := db.QueryRowContext(ctx, "SELECT task_id FROM client_sessions WHERE project_id=? AND id=?", project, session).Scan(&taskID); err != nil || taskID == "" {
		return fmt.Errorf("fixture session did not persist its Task: %w", err)
	}
	taskReq, err := http.NewRequestWithContext(ctx, http.MethodGet, base+"/v1/projects/"+project+"/tasks/"+taskID, nil)
	if err != nil {
		return err
	}
	taskReq.Header.Set("Authorization", "Bearer "+token)
	taskResp, err := client.Do(taskReq)
	if err != nil {
		return err
	}
	var task domain.Object
	decodeErr := json.NewDecoder(io.LimitReader(taskResp.Body, 1<<20)).Decode(&task)
	taskResp.Body.Close()
	if taskResp.StatusCode != 200 || decodeErr != nil || task["status"] != "BLOCKED" || task["task_type"] != "mu_turn" {
		return fmt.Errorf("fixture Task is not a persisted BLOCKED mu_turn: HTTP %d task=%v decode=%v", taskResp.StatusCode, task, decodeErr)
	}
	var boundProfileRaw string
	if err := db.QueryRowContext(ctx, "SELECT profile_ref FROM runtime_bindings WHERE project=?", project).Scan(&boundProfileRaw); err != nil {
		return err
	}
	var boundProfile domain.Object
	if err := json.Unmarshal([]byte(boundProfileRaw), &boundProfile); err != nil {
		return err
	}
	profileFrozen := false
	for _, input := range domain.Arr(task, "input_refs") {
		if domain.Hash(input) == domain.Hash(boundProfile) {
			profileFrozen = true
		}
	}
	if !profileFrozen {
		return errors.New("BLOCKED Task omitted its real frozen runtime profile input")
	}
	var providerCalls, runs int
	if err := db.QueryRowContext(ctx, "SELECT count(*) FROM resource_effects WHERE project=?", project).Scan(&providerCalls); err != nil {
		return err
	}
	if err := db.QueryRowContext(ctx, "SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run'", project).Scan(&runs); err != nil {
		return err
	}
	if providerCalls != 0 || runs != 0 {
		return fmt.Errorf("fixture unexpectedly executed: provider effects=%d runs=%d", providerCalls, runs)
	}
	current, err = command(ctx, client, base, token, "session.get", "before-write-probe", &project, &session, nil, nil, domain.Object{})
	if err != nil {
		return err
	}
	revision, err = domain.Num(current, "revision")
	if err != nil {
		return err
	}
	// Publishing the same bytes exercises the real filesystem CAS and seals a
	// draft while preserving the exact source baseline for the Electron test.
	written, err := command(ctx, client, base, token, "workspace.write", "probe-write-same-bytes", &project, &session, revision, epoch,
		domain.Object{"workspace_ref": ref, "relative_path": "source.txt", "task_id": taskID,
			"expected_content_hash": domain.Digest(source), "text": string(source), "create_if_missing": false})
	if err != nil {
		return err
	}
	physical, err := os.ReadFile(filepath.Join(root, "source.txt"))
	if err != nil {
		return err
	}
	if !bytes.Equal(physical, source) || written["before_hash"] != domain.Digest(source) || written["after_hash"] != domain.Digest(source) || written["draft_artifact_ref"] == nil {
		return errors.New("typed workspace.write did not prove physical bytes and sealed draft")
	}
	draftRef, ok := written["draft_artifact_ref"].(map[string]any)
	if !ok || domain.Str(draftRef, "entity_type") != "Artifact" {
		return errors.New("typed workspace.write returned an invalid Artifact ref")
	}
	draftAPI := fixtureAPI{client: client, base: base, token: token, project: project}
	draft, err := draftAPI.call(ctx, http.MethodGet, draftAPI.path("/artifacts/"+domain.Str(draftRef, "id")), "", nil, 200)
	if err != nil {
		return err
	}
	if draft["sealed_at"] == nil || draft["content_hash"] != domain.Digest(source) || draft["id"] != draftRef["id"] {
		return errors.New("workspace.write draft Artifact is not persistently sealed with published bytes")
	}
	current, ok = written["snapshot"].(map[string]any)
	if !ok {
		return errors.New("typed workspace.write omitted updated snapshot")
	}
	revision, err = domain.Num(current, "revision")
	if err != nil {
		return err
	}
	discovery := filepath.Join(dataDir, "discovery.json")
	if err := writeDiscovery(discovery, listener.Addr().String(), dataDir, h.InstanceID()); err != nil {
		return err
	}
	output := map[string]any{
		"ready": true, "fixture": "W13-03 filesystem FIXTURE",
		"base_url": base, "api_url": base, "discovery_file": discovery,
		"credential_file": h.SessionFile(), "host_instance_id": h.InstanceID(),
		"native_pipe": host.PipeName(h.InstanceID()), "project_id": project,
		"session_id": session, "workspace_ref": ref, "workspace_root": root,
		"source_path": "source.txt", "source_file": filepath.Join(root, "source.txt"),
		"binary_path": "binary.dat", "directory_path": "nested",
		"source_content_hash": domain.Digest(source), "task_id": taskID,
		"model_config_ref": fixtureModelRef,
		"session_revision": revision, "writer_epoch": epoch,
		"seed_origin": "temporary Git files created by tests/ui/w1303/workspace_fixture; no external source or provider",
		"provenance": []string{
			"Fresh .local Git root and SQLite created by workspace_fixture; no existing project or provider used",
			"Folder selection callback is FIXTURE; Host selection record and workspace.register use production code",
			"Session writer client_id is desktop-shell, matching Electron main; no epoch was forged or transferred",
			"Real frozen Mu profile and runtime binding permit only exact source.txt draft writes; qualification is absent",
		},
		"typed_probes": map[string]any{"tree_entries": len(tree["entries"].([]any)),
			"read_hash": read["content_hash"], "diff_full_artifact_ref": diff["full_diff_artifact_ref"],
			"import_artifact_ref":      imported["artifact_ref"],
			"write_draft_artifact_ref": written["draft_artifact_ref"], "write_after_hash": written["after_hash"],
			"provider_effect_count": providerCalls, "run_count": runs},
	}
	if err := json.NewEncoder(os.Stdout).Encode(output); err != nil {
		return err
	}
	wait, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	<-wait.Done()
	return nil
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

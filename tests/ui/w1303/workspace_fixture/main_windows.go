//go:build windows

// workspace_fixture serves a disposable W13 filesystem project through the
// production v2 API and native Host. The one folder-selection callback used
// during setup is an explicit fixture, not evidence of a human OS dialog.
package main

import (
	"bytes"
	"context"
	"database/sql"
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

// A fixed local model reference permits a readable Session. It never admits a
// provider turn or grants workspace.write authority.
type localRuntime struct{}

func (localRuntime) ValidateBinding(_ context.Context, _ *sql.Tx, _, _, _, model string) error {
	if model != "model-local-fixture" {
		return domain.Fail(422, "MODEL_UNAVAILABLE", "fixture model binding unavailable")
	}
	return nil
}

func (localRuntime) AdmitTurn(context.Context, *sql.Tx, string, string, domain.Object) error {
	return domain.Fail(503, "RESOURCE_UNAVAILABLE", "fixture has no provider")
}

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
	big := []byte(strings.Repeat("baseline fixture line\n", 160))
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
	if err := os.WriteFile(filepath.Join(root, "large-diff.txt"), []byte(strings.Repeat("changed fixture line\n", 160)), 0o600); err != nil {
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
	srv := &http.Server{Handler: api.HandlerWithLocalHost(db, *webFlag, svc, localRuntime{},
		h.InstanceID(), localworkspace.NewAuthority(h), localworkspace.NewScanner(), h),
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
	snap, err := command(ctx, client, base, token, "session.create", "create-session", &project, nil, nil, nil,
		domain.Object{"workspace_ref": ref, "model_config_ref": "model-local-fixture", "title": "W13 local files FIXTURE"})
	if err != nil {
		return err
	}
	session := snap["session_id"].(string)
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
		"source_path": filepath.Join(root, "source.txt"), "source_file": filepath.Join(root, "source.txt"),
		"source_content_hash": domain.Digest(source), "task_id": nil,
		"model_config_ref": "model-local-fixture",
		"session_revision": 2, "writer_epoch": 1,
		"seed_origin": "temporary Git files created by tests/ui/w1303/workspace_fixture; no external source or provider",
		"provenance": []string{
			"Fresh .local Git root and SQLite created by workspace_fixture; no existing project or provider used",
			"Folder selection callback is FIXTURE; Host selection record and workspace.register use production code",
			"Session writer client_id is desktop-shell, matching Electron main; no epoch was forged or transferred",
			"Fixed model binding cannot admit provider turns or authorize workspace.write",
		},
		"typed_probes": map[string]any{"tree_entries": len(tree["entries"].([]any)),
			"read_hash": read["content_hash"], "diff_full_artifact_ref": diff["full_diff_artifact_ref"],
			"import_artifact_ref": imported["artifact_ref"]},
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

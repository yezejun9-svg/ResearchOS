//go:build windows

package api_test

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

// The chooser callback is a deterministic OS-choice fixture; the selection
// record, one-use redemption, root pin, domain binding and HTTP command path
// are production code. This test does not claim a human clicked the dialog.
type workspaceHTTPFixture struct {
	t       *testing.T
	db      *sql.DB
	host    *host.Host
	server  *httptest.Server
	token   string
	client  string
	project string
	ref     string
	session string
	root    string
}

type workspaceSessionRuntimeFixture struct{}

// This narrow test port covers HTTP/domain/Host physical publication. The
// production frozen-profile authority is tested at the RuntimeCoordinator.
type workspaceWriteTaskAuthorityFixture struct{ workspaceSessionRuntimeFixture }

func (workspaceWriteTaskAuthorityFixture) AuthorizeWorkspaceWrite(_ context.Context, _ *sql.Tx, _ string, _ string, _ string, task domain.Object, relativePath string, byteSize int) error {
	if task["task_type"] != "mu_turn" || task["status"] != "BLOCKED" || relativePath != "source.txt" || byteSize > 64 {
		return domain.Fail(403, "POLICY_DENIED", "test task scope denied")
	}
	return nil
}

func (workspaceSessionRuntimeFixture) ValidateBinding(_ context.Context, _ *sql.Tx, _, _, _, model string) error {
	if model != "model-local-fixture" {
		return domain.Fail(422, "MODEL_UNAVAILABLE", "fixture model binding unavailable")
	}
	return nil
}
func (workspaceSessionRuntimeFixture) AdmitTurn(context.Context, *sql.Tx, string, string, domain.Object) error {
	return domain.Fail(503, "RESOURCE_UNAVAILABLE", "no provider in local filesystem HTTP regression")
}

func workspaceGit(t *testing.T, dir string, args ...string) {
	t.Helper()
	cmd := exec.Command("git", append([]string{"-C", dir}, args...)...)
	cmd.Env = append(os.Environ(), "GIT_TERMINAL_PROMPT=0", "GIT_CONFIG_NOSYSTEM=1")
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("git %v: %v %s", args, err, out)
	}
}

func newWorkspaceHTTPFixture(t *testing.T, runtime ...domain.ClientSessionRuntime) *workspaceHTTPFixture {
	t.Helper()
	ctx := context.Background()
	base := t.TempDir()
	root := filepath.Join(base, "chosen")
	if err := os.Mkdir(root, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "source.txt"), []byte("before\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	workspaceGit(t, root, "init", "-q")
	workspaceGit(t, root, "add", "--", "source.txt")
	workspaceGit(t, root, "-c", "user.name=ResearchOS Fixture", "-c", "user.email=fixture@researchos.local", "commit", "-qm", "baseline")
	db, err := store.Open(filepath.Join(base, "data", "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err := store.Bootstrap(ctx, db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	migration, err := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(string(migration)); err != nil {
		t.Fatal(err)
	}
	if err := domain.EnsureClientSessionFence(ctx, db); err != nil {
		t.Fatal(err)
	}
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(base, "data", "host"),
		ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql",
		SchemaDir: "../../internal/api/contracts"})
	if err != nil {
		t.Fatal(err)
	}
	owner, err := h.BootstrapOwner(ctx)
	if err != nil {
		t.Fatal(err)
	}
	f := &workspaceHTTPFixture{t: t, db: db, host: h, token: owner.Session.Token, client: "workspace-http-fixture", root: root}
	selectedRuntime := domain.ClientSessionRuntime(workspaceSessionRuntimeFixture{})
	if len(runtime) == 1 {
		selectedRuntime = runtime[0]
	}
	f.server = httptest.NewServer(api.HandlerWithLocalHost(db, t.TempDir(), svc, selectedRuntime,
		h.InstanceID(), localworkspace.NewAuthority(h), localworkspace.NewScanner(), h))
	t.Cleanup(f.server.Close)
	f.ref = f.register(root)
	project := f.complete(f.command("project.bootstrap", "bootstrap-project", nil, nil, nil, nil,
		domain.Object{"authorized_workspace_ref": f.ref, "display_name": "Filesystem regression"}))
	f.project = project["project_id"].(string)
	snap := f.complete(f.command("session.create", "create-session", &f.project, nil, nil, nil,
		domain.Object{"workspace_ref": f.ref, "model_config_ref": "model-local-fixture", "title": "Local files"}))
	f.session = snap["session_id"].(string)
	return f
}

func (f *workspaceHTTPFixture) command(method, key string, project, session *string, revision, epoch any, payload domain.Object) domain.Object {
	f.t.Helper()
	env := domain.Object{"protocol_version": domain.ProtocolV2, "command_id": key, "client_id": f.client,
		"project_id": project, "session_id": session, "expected_revision": revision, "writer_epoch": epoch,
		"method": method, "payload": payload}
	req, err := http.NewRequest(http.MethodPost, f.server.URL+"/v2/command", bytes.NewReader(domain.Bytes(env)))
	if err != nil {
		f.t.Fatal(err)
	}
	req.Header.Set("Authorization", "Bearer "+f.token)
	req.Header.Set("Content-Type", "application/json")
	resp, err := f.server.Client().Do(req)
	if err != nil {
		f.t.Fatal(err)
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		f.t.Fatal(err)
	}
	var result domain.Object
	if err := json.Unmarshal(raw, &result); err != nil || resp.StatusCode >= 500 {
		f.t.Fatalf("HTTP %s: %d %s (%v)", method, resp.StatusCode, raw, err)
	}
	return result
}

func (f *workspaceHTTPFixture) complete(reply domain.Object) domain.Object {
	f.t.Helper()
	if reply["status"] != "COMPLETED" {
		f.t.Fatalf("expected completed command, got %s", domain.Bytes(reply))
	}
	result, ok := reply["result"].(map[string]any)
	if !ok {
		f.t.Fatalf("missing result: %s", domain.Bytes(reply))
	}
	return result
}

func (f *workspaceHTTPFixture) register(path string) string {
	f.t.Helper()
	frame := domain.Bytes(domain.Object{"kind": host.KindWorkspaceChooseRequest, "client_id": f.client,
		"payload": domain.Object{"requested_path": path, "requested_access": host.AccessReadWrite}})
	selected, err := f.host.HandleNative(frame, true, func(string) (string, error) { return path, nil })
	if err != nil {
		f.t.Fatal(err)
	}
	var native domain.Object
	if err := json.Unmarshal(selected, &native); err != nil {
		f.t.Fatal(err)
	}
	selection := native["payload"].(map[string]any)["selection_ref"].(string)
	registered := f.complete(f.command("workspace.register", "register-"+domain.ID(), nil, nil, nil, nil,
		domain.Object{"selection_ref": selection, "display_name": "Chosen local root", "requested_access": host.AccessReadWrite}))
	return registered["authorized_workspace_ref"].(string)
}

func (f *workspaceHTTPFixture) artifactBytes(ref map[string]any) []byte {
	f.t.Helper()
	var raw []byte
	if err := f.db.QueryRow(`SELECT u.bytes FROM uploaded_content u JOIN domain_objects a ON u.storage_key=json_extract(a.body,'$.storage_key') WHERE a.kind='Artifact' AND a.id=?`, ref["id"]).Scan(&raw); err != nil {
		f.t.Fatal(err)
	}
	return raw
}

func TestW13WorkspaceFilesRealHostHTTPReadDiffImport(t *testing.T) {
	f := newWorkspaceHTTPFixture(t)
	actual := []byte("精确字节\r\nand another changed line\n")
	if err := os.WriteFile(filepath.Join(f.root, "source.txt"), actual, 0o600); err != nil {
		t.Fatal(err)
	}
	tree := f.complete(f.command("workspace.tree", "tree", &f.project, &f.session, nil, nil,
		domain.Object{"workspace_ref": f.ref, "relative_path": ".", "cursor": nil, "limit": 100}))
	found := false
	for _, item := range tree["entries"].([]any) {
		entry := item.(map[string]any)
		found = found || entry["relative_path"] == "source.txt" && entry["content_hash"] == domain.Digest(actual)
	}
	if !found {
		t.Fatalf("native tree omitted real sealed-byte hash: %s", domain.Bytes(tree))
	}
	read := f.complete(f.command("workspace.read", "read", &f.project, &f.session, nil, nil,
		domain.Object{"workspace_ref": f.ref, "relative_path": "source.txt", "max_bytes": 1024}))
	if read["text"] != string(actual) || read["content_hash"] != domain.Digest(actual) {
		t.Fatalf("native read changed bytes: %s", domain.Bytes(read))
	}
	diff := f.complete(f.command("workspace.diff", "diff", &f.project, &f.session, nil, nil,
		domain.Object{"workspace_ref": f.ref, "base": "HEAD", "relative_path": nil, "max_bytes": 64}))
	if diff["truncated"] != true || diff["full_diff_artifact_ref"] == nil {
		t.Fatalf("expected full patch to be sealed when truncated: %s", domain.Bytes(diff))
	}
	patch := f.artifactBytes(diff["full_diff_artifact_ref"].(map[string]any))
	if !bytes.Contains(patch, []byte("+and another changed line")) || domain.Digest(patch) != diff["full_diff_artifact_ref"].(map[string]any)["content_hash"] {
		t.Fatalf("sealed diff lost full patch bytes: %q", patch)
	}
	importPayload := domain.Object{"workspace_ref": f.ref, "relative_path": "source.txt", "expected_content_hash": domain.Digest(actual), "purpose": "ATTACHMENT"}
	stale := f.command("artifact.import", "stale-epoch", &f.project, &f.session, 1, 2, importPayload)
	if stale["error_code"] != "STALE_WRITER_EPOCH" {
		t.Fatalf("old epoch reached file: %s", domain.Bytes(stale))
	}
	importedReply := f.command("artifact.import", "import", &f.project, &f.session, 1, 1, importPayload)
	imported := f.complete(importedReply)
	ref := imported["artifact_ref"].(map[string]any)
	if sealed := f.artifactBytes(ref); !bytes.Equal(sealed, actual) || ref["content_hash"] != domain.Digest(actual) {
		t.Fatalf("import did not seal exact bytes: %q", sealed)
	}
	replayed := f.command("artifact.import", "import", &f.project, &f.session, 1, 1, importPayload)
	if !bytes.Equal(domain.Bytes(replayed), domain.Bytes(importedReply)) {
		t.Fatalf("same command replay changed result: %s", domain.Bytes(replayed))
	}
	var revision, events int
	if err := f.db.QueryRow("SELECT revision FROM client_sessions WHERE id=?", f.session).Scan(&revision); err != nil || revision != 2 {
		t.Fatalf("import revision=%d err=%v", revision, err)
	}
	if err := f.db.QueryRow(`SELECT count(*) FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='ARTIFACT'`, f.session).Scan(&events); err != nil || events != 1 {
		t.Fatalf("import event count=%d err=%v", events, err)
	}
	if _, err := f.db.Exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?", time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), f.session); err != nil {
		t.Fatal(err)
	}
	previousClient := f.client
	f.client = "client-two"
	takeover := f.command("session.attach", "renew-writer", &f.project, &f.session, revision, nil,
		domain.Object{"after_sequence": 0, "request_write_owner": true})
	if takeover["status"] != "COMPLETED" {
		t.Fatalf("writer epoch did not advance: %s", domain.Bytes(takeover))
	}
	var advancedRevision, advancedEpoch int64
	if err := f.db.QueryRow("SELECT revision,writer_epoch FROM client_sessions WHERE id=?", f.session).Scan(&advancedRevision, &advancedEpoch); err != nil || advancedEpoch != 2 {
		t.Fatalf("current writer epoch=%d revision=%d err=%v", advancedEpoch, advancedRevision, err)
	}
	f.client = previousClient
	oldEpoch := f.command("artifact.import", "actual-old-epoch", &f.project, &f.session, advancedRevision, 1, importPayload)
	if oldEpoch["error_code"] != "STALE_WRITER_EPOCH" {
		t.Fatalf("old writer epoch imported file: %s", domain.Bytes(oldEpoch))
	}
	other := filepath.Join(t.TempDir(), "other")
	if err := os.Mkdir(other, 0o700); err != nil {
		t.Fatal(err)
	}
	otherRef := f.register(other)
	cross := f.command("workspace.read", "cross-workspace", &f.project, &f.session, nil, nil,
		domain.Object{"workspace_ref": otherRef, "relative_path": "source.txt", "max_bytes": 1024})
	if cross["status"] != "REJECTED" {
		t.Fatalf("session crossed workspace boundary: %s", domain.Bytes(cross))
	}
}

func TestW13WorkspaceWriteNeedsProductionTaskAuthority(t *testing.T) {
	f := newWorkspaceHTTPFixture(t)
	request := domain.Object{"workspace_ref": f.ref, "relative_path": "source.txt", "task_id": "nonexistent-task",
		"expected_content_hash": domain.Digest([]byte("before\n")), "create_if_missing": false, "text": "attempt"}
	reply := f.command("workspace.write", "write-without-task", &f.project, &f.session, 1, 1, request)
	if reply["status"] != "REJECTED" {
		t.Fatalf("write without real frozen task succeeded: %s", domain.Bytes(reply))
	}
	if actual, err := os.ReadFile(filepath.Join(f.root, "source.txt")); err != nil || string(actual) != "before\n" {
		t.Fatalf("rejected write changed target: %q %v", actual, err)
	}
	if strings.TrimSpace(reply["error_code"].(string)) == "" {
		t.Fatal("write rejection had no typed error code")
	}
}

func TestW13WorkspaceWriteHTTPPhysicalPathWithFixtureTaskAuthority(t *testing.T) {
	f := newWorkspaceHTTPFixture(t, workspaceWriteTaskAuthorityFixture{})
	sent := f.complete(f.command("session.send", "send-for-write", &f.project, &f.session, 1, 1,
		domain.Object{"text": "Edit the bounded source file", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"}))
	if sent["run_id"] != nil {
		t.Fatalf("local fixture unexpectedly started a provider run: %s", domain.Bytes(sent))
	}
	var taskID string
	var revision int64
	if err := f.db.QueryRow("SELECT task_id,revision FROM client_sessions WHERE id=?", f.session).Scan(&taskID, &revision); err != nil || taskID == "" {
		t.Fatalf("real session task missing: %q %v", taskID, err)
	}
	text := "updated exact bytes\r\n"
	payload := domain.Object{"workspace_ref": f.ref, "relative_path": "source.txt", "task_id": taskID,
		"expected_content_hash": domain.Digest([]byte("before\n")), "create_if_missing": false, "text": text}
	writtenReply := f.command("workspace.write", "save-command", &f.project, &f.session, revision, 1, payload)
	written := f.complete(writtenReply)
	if written["after_hash"] != domain.Digest([]byte(text)) || written["before_hash"] != domain.Digest([]byte("before\n")) {
		t.Fatalf("write proof mismatch: %s", domain.Bytes(written))
	}
	if actual, err := os.ReadFile(filepath.Join(f.root, "source.txt")); err != nil || string(actual) != text {
		t.Fatalf("physical writer bytes: %q %v", actual, err)
	}
	if sealed := f.artifactBytes(written["draft_artifact_ref"].(map[string]any)); string(sealed) != text {
		t.Fatalf("draft artifact bytes changed: %q", sealed)
	}
	replayed := f.command("workspace.write", "save-command", &f.project, &f.session, revision, 1, payload)
	if !bytes.Equal(domain.Bytes(replayed), domain.Bytes(writtenReply)) {
		t.Fatalf("write command replay changed result: %s", domain.Bytes(replayed))
	}
	var events int
	if err := f.db.QueryRow(`SELECT count(*) FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='ARTIFACT' AND json_extract(body,'$.command_id')='save-command'`, f.session).Scan(&events); err != nil || events != 1 {
		t.Fatalf("write event count=%d err=%v", events, err)
	}
	changed := domain.Object{"workspace_ref": f.ref, "relative_path": "source.txt", "task_id": taskID,
		"expected_content_hash": domain.Digest([]byte("before\n")), "create_if_missing": false, "text": "changed body"}
	conflict := f.command("workspace.write", "save-command", &f.project, &f.session, revision, 1, changed)
	fault, _ := conflict["error"].(map[string]any)
	if fault["code"] != "COMMAND_ID_CONFLICT" {
		t.Fatalf("same command id accepted changed body: %s", domain.Bytes(conflict))
	}
	if actual, err := os.ReadFile(filepath.Join(f.root, "source.txt")); err != nil || string(actual) != text {
		t.Fatalf("command conflict changed saved draft: %q %v", actual, err)
	}
	var nextRevision int64
	if err := f.db.QueryRow("SELECT revision FROM client_sessions WHERE id=?", f.session).Scan(&nextRevision); err != nil || nextRevision != revision+1 {
		t.Fatalf("saved session revision=%d err=%v", nextRevision, err)
	}
	clear := domain.Object{"workspace_ref": f.ref, "relative_path": "source.txt", "task_id": taskID,
		"expected_content_hash": domain.Digest([]byte(text)), "create_if_missing": false, "text": ""}
	cleared := f.complete(f.command("workspace.write", "clear-command", &f.project, &f.session, nextRevision, 1, clear))
	if cleared["after_hash"] != domain.Digest(nil) {
		t.Fatalf("empty text save hash: %s", domain.Bytes(cleared))
	}
	if actual, err := os.ReadFile(filepath.Join(f.root, "source.txt")); err != nil || len(actual) != 0 {
		t.Fatalf("empty text did not clear file: %q %v", actual, err)
	}
	if sealed := f.artifactBytes(cleared["draft_artifact_ref"].(map[string]any)); len(sealed) != 0 {
		t.Fatalf("empty draft artifact changed: %q", sealed)
	}
}

//go:build windows

package host_test

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

var productionRuntimeAssets = flag.String("local-runtime-assets-dir", "", "explicit production build directory for offline host composition qualification")

func writeOfflineRuntimeAssets(t *testing.T, root string) {
	t.Helper()
	if err := os.MkdirAll(root, 0700); err != nil {
		t.Fatal(err)
	}
	bundle := []byte("synthetic offline bundle, never executed")
	for name, raw := range map[string][]byte{
		"node.exe":                 []byte("MZ synthetic offline node; never executed"),
		"mu-worker.mjs":            bundle,
		"mu-worker.mjs.build.json": domain.Bytes(domain.Object{"bundle_sha256": strings.TrimPrefix(domain.Digest(bundle), "sha256:"), "bundle_bytes": len(bundle), "source_sha256": strings.Repeat("a", 64), "sdk_version": "offline-fixture", "ai_version": "offline-fixture", "mu_commit": "8dfebe36508ac0c2508735bb866756dab9283e74", "vendored_files_verified": 5083}),
	} {
		if err := os.WriteFile(filepath.Join(root, name), raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
}

func TestLocalRuntimeAssetsMissingAndExactBuildMetadata(t *testing.T) {
	root := t.TempDir()
	if _, err := host.LoadRuntimeSetupAssets(root); err == nil {
		t.Fatal("missing assets accepted")
	}
	writeOfflineRuntimeAssets(t, root)
	assets, err := host.LoadRuntimeSetupAssets(root)
	if err != nil || assets.BuildHash == "" || assets.BundleHash == "" {
		t.Fatalf("offline metadata: %v", err)
	}
	if err = os.WriteFile(filepath.Join(root, "mu-worker.mjs"), []byte("changed"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = host.LoadRuntimeSetupAssets(root); err == nil {
		t.Fatal("build metadata mismatch accepted")
	}
}

// Production Host, workspace/project APIs, typed handler and coordinator Scan
// are used end to end. The chooser and asset bytes are offline fixtures, so
// this proves composition and zero dispatch, not a real model qualification.
func TestLocalRuntimeHostNormalCommittedSessionOffline(t *testing.T) {
	testLocalRuntimeHostCommittedSession(t, "")
}

func TestLocalRuntimeHostProductionAssetsOffline(t *testing.T) {
	if *productionRuntimeAssets == "" {
		t.Skip("explicit production runtime assets directory required; no live qualification claimed")
	}
	testLocalRuntimeHostCommittedSession(t, *productionRuntimeAssets)
}

func testLocalRuntimeHostCommittedSession(t *testing.T, productionAssets string) {
	ctx := context.Background()
	repo := backupTestRepo(t)
	data := t.TempDir()
	db, err := store.Open(filepath.Join(data, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err = store.Bootstrap(ctx, db, filepath.Join(repo, "migrations/sqlite/0001_bootstrap.sql")); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.NewCurrentMu(db, filepath.Join(repo, "spec/v2.0/contracts"), filepath.Join(repo, "migrations/sqlite/0002_domain.sql"))
	if err != nil {
		t.Fatal(err)
	}
	h := backupTestHost(t, db, data, repo)
	owner, err := h.BootstrapOwner(ctx)
	if err != nil {
		t.Fatal(err)
	}
	doc, err := api.ClientProtocolDocument()
	if err != nil {
		t.Fatal(err)
	}
	authority := localworkspace.NewAuthority(h)
	workspace := t.TempDir()
	frame := domain.Bytes(domain.Object{"kind": host.KindWorkspaceChooseRequest, "client_id": "normal-setup-client", "payload": domain.Object{"requested_path": workspace, "requested_access": host.AccessReadOnly}})
	chosenRaw, err := h.HandleNative(frame, true, func(string) (string, error) { return workspace, nil })
	if err != nil {
		t.Fatal(err)
	}
	var chosen struct {
		Payload struct {
			Ref string `json:"selection_ref"`
		} `json:"payload"`
	}
	if err = json.Unmarshal(chosenRaw, &chosen); err != nil || chosen.Payload.Ref == "" {
		t.Fatalf("selection: %v", err)
	}
	p := domain.Principal{ID: owner.PrincipalID, Roles: []string{"OWNER"}, CanCreateProject: true}
	registered, err := svc.RegisterWorkspace(ctx, p, authority, doc, domain.RegisterWorkspaceInput{SelectionRef: chosen.Payload.Ref, DisplayName: "offline setup workspace", RequestedAccess: host.AccessReadOnly, ClientID: "normal-setup-client", CommandID: domain.ID()})
	if err != nil {
		t.Fatal(err)
	}
	workspaceRef := domain.Str(registered, "authorized_workspace_ref")
	project, err := svc.BootstrapProject(ctx, p, authority, doc, localworkspace.NewScanner(), domain.BootstrapProjectInput{AuthorizedWorkspaceRef: workspaceRef, DisplayName: "normal setup", ClientID: "normal-setup-client", CommandID: domain.ID(), MeasurementMode: "FIXTURE"})
	if err != nil {
		t.Fatal(err)
	}
	projectID := domain.Str(project, "project_id")
	assetsDir := filepath.Join(data, "runtime")
	newCoordinator := func() *domain.RuntimeCoordinator {
		setup := h.NewRuntimeSetup(svc, doc, assetsDir)
		c, e := svc.NewRuntimeCoordinator(ctx, domain.RuntimeCoordinatorConfig{DataRoot: data, APIURL: "http://127.0.0.1:1", WorkspaceAuthority: authority, ConfigurationAuthority: h, ClientSchema: doc, ModelCredential: h.ModelCredential, RunTool: h.ExecuteRuntimeTool, PrepareLocalRuntime: setup.Reconcile})
		if e != nil {
			t.Fatal(e)
		}
		return c
	}
	c := newCoordinator()
	defer func() {
		if c != nil {
			c.Close()
		}
	}()
	handler := api.HandlerWithConfigurationHost(db, filepath.Join(repo, "apps/web/dist"), svc, c, h.InstanceID(), authority, localworkspace.NewScanner(), h, h)
	command := func(method string, project, session any, revision, epoch any, payload domain.Object) domain.Object {
		raw := domain.Bytes(domain.Object{"protocol_version": domain.ProtocolV2, "command_id": domain.ID(), "client_id": "normal-setup-client", "project_id": project, "session_id": session, "expected_revision": revision, "writer_epoch": epoch, "method": method, "payload": payload})
		r := httptest.NewRequest(http.MethodPost, "/v2/command", bytes.NewReader(raw))
		r.Header.Set("Authorization", "Bearer "+owner.Session.Token)
		r.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, r)
		result, e := domain.Decode(w.Body.Bytes())
		if e != nil || w.Code != 200 {
			t.Fatalf("%s status=%d body=%s err=%v", method, w.Code, w.Body.Bytes(), e)
		}
		return result
	}
	saved := command("host.configure", nil, nil, nil, nil, domain.Object{"config_revision": 1, "provider_id": "ollama", "base_url": "http://127.0.0.1:1/v1", "model_id": "qwen3:4b-instruct", "credential_ref": nil})
	if saved["status"] != "COMPLETED" {
		t.Fatalf("configure: %s", domain.Bytes(saved))
	}
	model := domain.Str(saved["result"].(map[string]any), "model_config_ref")
	if err = c.Scan(ctx); err != nil {
		t.Fatal(err)
	}
	var count int
	if err = db.QueryRow(`SELECT count(*) FROM runtime_bindings`).Scan(&count); err != nil || count != 0 {
		t.Fatal("default-only config prepared a project runtime", err)
	}
	created := command("session.create", projectID, nil, nil, nil, domain.Object{"workspace_ref": workspaceRef, "model_config_ref": model, "title": "offline setup"})
	if created["status"] != "COMPLETED" {
		t.Fatalf("create: %s", domain.Bytes(created))
	}
	sid := domain.Str(created, "session_id")
	if err = c.Scan(ctx); err == nil || !strings.Contains(err.Error(), "runtime assets unavailable") {
		t.Fatalf("missing asset branch: %v", err)
	}
	sent := command("session.send", projectID, sid, 1, 1, domain.Object{"text": "Do not dispatch while setup is unavailable", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
	if sent["status"] != "REJECTED" || !bytes.Contains(domain.Bytes(sent), []byte("runtime assets unavailable")) {
		t.Fatalf("missing resource not reported: %s", domain.Bytes(sent))
	}
	if err = c.Close(); err != nil {
		t.Fatal(err)
	}
	c = nil
	if productionAssets == "" {
		writeOfflineRuntimeAssets(t, assetsDir)
	} else {
		assetsDir = productionAssets
		assets, err := host.LoadRuntimeSetupAssets(assetsDir)
		if err != nil {
			t.Fatal(err)
		}
		t.Logf("PRODUCTION_ASSETS node_sha256=%s bundle_sha256=%s no_execution=true", assets.BuildHash, assets.BundleHash)
	}
	c = newCoordinator()
	if err = c.Scan(ctx); err != nil {
		t.Fatal(err)
	}
	var runtimeID string
	if err = db.QueryRow(`SELECT runtime FROM runtime_bindings WHERE project=?`, projectID).Scan(&runtimeID); err != nil {
		t.Fatal(err)
	}
	if err = c.Close(); err != nil {
		t.Fatal(err)
	}
	c = nil
	c = newCoordinator()
	if err = c.Scan(ctx); err != nil {
		t.Fatal(err)
	}
	var restored string
	if err = db.QueryRow(`SELECT runtime FROM runtime_bindings WHERE project=?`, projectID).Scan(&restored); err != nil || restored != runtimeID {
		t.Fatal("restart did not reuse exact profile", err)
	}
	if err = db.QueryRow(`SELECT (SELECT count(*) FROM runtime_dispatches)+(SELECT count(*) FROM resource_effects)+(SELECT count(*) FROM domain_objects WHERE kind IN ('Run','AcceptanceReceipt','BudgetLedgerEntry'))`).Scan(&count); err != nil || count != 0 {
		t.Fatalf("setup caused provider/acceptance activity count=%d %v", count, err)
	}
	t.Logf("actual_windows_host=true ordinary_configure_and_session=true coordinator_scan=true restart_same_runtime=true registered_only=true model_calls=0 production_assets=%t assets_not_executed=true", productionAssets != "")
}

func TestTrustedCandidateAssetsRequireExplicitPinnedPolicy(t *testing.T) {
	root := t.TempDir()
	bundle := []byte("candidate offline bytes")
	node := []byte("MZ candidate node fixture")
	policy := host.TrustedCandidatePolicy{AssetRoot: root, ManifestHash: "sha256:9e5dd1e5d93f19c6a4aa5eb5c0e2ebd7f0d1e05a987f6ec03963b4b560139da9", BundleHash: domain.Digest(bundle), NodeHash: domain.Digest(node), SourceHash: "sha256:" + strings.Repeat("a", 64)}
	meta := domain.Object{"source_mode": "ACCEPTED_M0_CANDIDATE", "candidate_manifest_sha256": strings.TrimPrefix(policy.ManifestHash, "sha256:"), "candidate_base": "7ec619a16a932ae02daa7c2e6132d266528a1da8", "candidate_patch_sha256": "f82f8b8f866ae920bb769b657faf0a1a8709844979422fa409cb5bbc5194ad67", "independent_review_sha256": "13c6ce9fbad76c6e6f2b2c8537bbaa2e662dc5539709c0161fa5219d06dd7489", "protocol_capability": "RESEARCHOS_PAUSE_V1", "bundle_sha256": strings.TrimPrefix(policy.BundleHash, "sha256:"), "source_sha256": strings.TrimPrefix(policy.SourceHash, "sha256:"), "bundle_bytes": len(bundle), "compiled_inputs": 2, "compiled_inputs_sha256": strings.Repeat("b", 64)}
	for name, raw := range map[string][]byte{"mu-worker.mjs": bundle, "node.exe": node, "mu-worker.mjs.build.json": domain.Bytes(meta)} {
		if err := os.WriteFile(filepath.Join(root, name), raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
	got, err := host.LoadTrustedCandidateRuntimeSetupAssets(policy)
	if err != nil || got.BundleHash != policy.BundleHash {
		t.Fatal("explicit candidate refused", err)
	}
	if _, err = host.LoadRuntimeSetupAssets(root); err == nil {
		t.Fatal("default installed loader accepted candidate")
	}
	for _, field := range []string{"source_mode", "candidate_manifest_sha256", "candidate_base", "candidate_patch_sha256", "independent_review_sha256", "protocol_capability", "bundle_sha256", "source_sha256"} {
		t.Run(field, func(t *testing.T) {
			original := meta[field]
			meta[field] = "changed"
			defer func() { meta[field] = original }()
			if e := os.WriteFile(filepath.Join(root, "mu-worker.mjs.build.json"), domain.Bytes(meta), 0600); e != nil {
				t.Fatal(e)
			}
			if _, e := host.LoadTrustedCandidateRuntimeSetupAssets(policy); e == nil {
				t.Fatal("changed candidate accepted")
			}
		})
	}
	if err = os.WriteFile(filepath.Join(root, "mu-worker.mjs.build.json"), domain.Bytes(meta), 0600); err != nil {
		t.Fatal(err)
	}
	foreign := policy
	foreign.NodeHash = "sha256:" + strings.Repeat("c", 64)
	if _, err = host.LoadTrustedCandidateRuntimeSetupAssets(foreign); err == nil {
		t.Fatal("unpinned executable accepted")
	}
	if err = os.WriteFile(filepath.Join(root, "mu-worker.mjs"), []byte("changed"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = host.LoadTrustedCandidateRuntimeSetupAssets(policy); err == nil {
		t.Fatal("changed bundle accepted")
	}
}

//go:build windows

package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"testing"
)

func TestClientGoalCurrentBindingSelection(t *testing.T) {
	config := modelFixtureConfig("https://model.invalid/v1/chat/completions")
	c, route, runtime := coordinatorFixtureProgram(t, false, false, func(profile Object) (string, string) {
		bundle := filepath.Join(t.TempDir(), "inert-bundle.mjs")
		bytes := []byte("// inert model metadata; no worker started\n")
		if err := os.WriteFile(bundle, bytes, 0600); err != nil {
			t.Fatal(err)
		}
		exe, err := os.Executable()
		if err != nil {
			t.Fatal(err)
		}
		profile["backend"], profile["model"], profile["model_config"] = runtimeMuBackend, config["model"], config
		profile["bundle_hash"] = Digest(bytes)
		profile["argv"] = []any{"{bundle}", "{manifest}"}
		profile["effect_routes"] = []any{Object{"id": config["route"], "capability": "MODEL", "credential_revision": "test-v1", "upper_bound": dollars("1")}}
		profile["model_qualification"] = Object{"route": config["route"], "model_config_hash": Hash(config), "max_calls": 1}
		profile["tool_policy"] = Object{"max_calls": 1, "read_paths": Empty(), "write_paths": Empty(), "max_read_bytes": 16, "max_write_bytes": 16}
		return exe, bundle
	})
	c.config.WorkspaceAuthority = clientWorkspaceAuthority{}
	f := runtime.f
	ctx := context.Background()
	client := "goal-binding-client"
	principal := f.owner
	workspace := "goal-binding-workspace-" + ID()
	insert := func(ref, actor, clientID string) {
		t.Helper()
		b := WorkspaceBinding{AuthorizedRef: ref, DisplayName: "binding fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: actor, ClientID: clientID, HostPrincipalRef: "fixture-local-user", CreatedAt: Now()}
		if _, err := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, ref, string(Bytes(b))); err != nil {
			t.Fatal(err)
		}
	}
	resolve := func() (string, string, error) {
		t.Helper()
		var workspaceRef, modelRef string
		var resolveErr error
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			workspaceRef, modelRef, resolveErr = c.ResolveGoalBinding(ctx, tx, principal, f.project, client)
			return nil
		})
		return workspaceRef, modelRef, resolveErr
	}
	if _, _, err := resolve(); err == nil {
		t.Fatal("project goal selected a workspace without an authorized binding")
	}
	insert("wrong-principal-"+ID(), "other-principal", client)
	insert("wrong-client-"+ID(), principal, "other-client")
	if _, _, err := resolve(); err == nil {
		t.Fatal("project goal selected a workspace of another principal or client")
	}
	insert(workspace, principal, client)
	gotWorkspace, gotModel, err := resolve()
	if err != nil || gotWorkspace != workspace || gotModel != Str(config, "ref") {
		t.Fatalf("current goal binding=%q %q err=%v", gotWorkspace, gotModel, err)
	}
	insert("ambiguous-workspace-"+ID(), principal, client)
	if _, _, err := resolve(); err == nil {
		t.Fatal("project goal silently selected one of two authorized workspaces")
	}
	if _, err := f.db.Exec(`DELETE FROM domain_objects WHERE project='' AND kind=? AND id LIKE 'ambiguous-workspace-%'`, KindWorkspaceBinding); err != nil {
		t.Fatal(err)
	}
	c.config.Routes = append(c.config.Routes, route)
	if _, _, err := resolve(); err == nil {
		t.Fatal("project goal silently selected one of two model routes")
	}
}

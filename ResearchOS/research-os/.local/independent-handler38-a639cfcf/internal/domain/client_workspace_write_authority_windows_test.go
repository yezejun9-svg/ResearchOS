//go:build windows

package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// This exercises the production coordinator and sealed runtime binding. The
// fixed bundle is only profile metadata: no worker or provider is started.
func TestClientWorkspaceWriteAuthorityFrozenProfile(t *testing.T) {
	const modelRef = "model-fixture-v1"
	config := modelFixtureConfig("https://model.invalid/v1/chat/completions")
	var originalProfile Object
	c, route, r := coordinatorFixtureProgram(t, false, false, func(profile Object) (string, string) {
		bundle := filepath.Join(t.TempDir(), "bundle.mjs")
		if err := os.WriteFile(bundle, []byte("// fixed inert bundle metadata\n"), 0600); err != nil {
			t.Fatal(err)
		}
		exe, err := os.Executable()
		if err != nil {
			t.Fatal(err)
		}
		profile["backend"], profile["model"], profile["model_config"] = runtimeMuBackend, config["model"], config
		profile["bundle_hash"] = Digest([]byte("// fixed inert bundle metadata\n"))
		profile["argv"] = []any{"{bundle}", "{manifest}"}
		profile["effect_routes"] = []any{Object{"id": config["route"], "capability": "MODEL", "credential_revision": "test-v1", "upper_bound": dollars("1")}}
		profile["model_qualification"] = Object{"route": config["route"], "model_config_hash": Hash(config), "max_calls": 1}
		profile["tool_policy"] = Object{"max_calls": 1, "read_paths": Empty(), "write_paths": []any{"source.txt"}, "max_read_bytes": 16, "max_write_bytes": 16}
		originalProfile, _ = Decode(Bytes(profile))
		return exe, bundle
	})
	f := r.f
	profileRef, originalArtifact := func() (Object, Object) {
		tx, err := f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		defer tx.Rollback()
		ref, artifact, err := f.s.currentRuntimeBinding(tx, f.project, r.registration)
		if err != nil {
			t.Fatal(err)
		}
		return ref, artifact
	}()

	ctx := context.Background()
	var frozen []any
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var err error
		frozen, err = c.FreezeClientTaskInputs(ctx, tx, f.project, modelRef)
		return err
	})
	if len(frozen) != 1 || Hash(frozen[0]) != Hash(profileRef) {
		t.Fatalf("freeze returned %v, want current sealed profile %v", frozen, profileRef)
	}

	req := f.requirement()
	task := f.task(req, frozen, "mu_turn")
	other := f.task(req, frozen, "mu_turn")
	noProfile := f.task(req, Empty(), "mu_turn")
	taskID, goalID := Str(task, "id"), Str(task, "goal_id")
	sid := ID()
	now, expires := time.Now(), time.Now().Add(time.Hour)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		return MapClientSession(ctx, tx, ClientSession{ID: sid, ProjectID: f.project, Revision: 1,
			CreatedAt: now, UpdatedAt: now, GoalID: &goalID, TaskID: &taskID,
			WriterEpoch: 1, WriterClientID: "write-authority-test", LeaseExpiresAt: &expires,
			UpstreamSession: ID(), ModelConfigRef: strptr(modelRef), Protocol: ClientSessionProtocol})
	})
	check := func(name string, candidate Object, path string, size int, permit bool) {
		t.Helper()
		t.Run(name, func(t *testing.T) {
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				err := c.AuthorizeWorkspaceWrite(ctx, tx, f.owner, f.project, sid, candidate, path, size)
				if permit && err != nil || !permit && err == nil {
					t.Fatalf("authorization err=%v, permit=%v", err, permit)
				}
				return nil
			})
		})
	}
	setTask := func(task Object) {
		t.Helper()
		if _, err := f.db.Exec("UPDATE client_sessions SET task_id=? WHERE id=?", task["id"], sid); err != nil {
			t.Fatal(err)
		}
	}
	check("exact path and byte ceiling", task, "source.txt", 16, true)
	check("changed path", task, "other.txt", 1, false)
	check("over byte ceiling", task, "source.txt", 17, false)
	check("another task", other, "source.txt", 1, false)
	check("non mu turn", r.task, "source.txt", 1, false)
	setTask(noProfile)
	check("task without frozen profile", noProfile, "source.txt", 1, false)
	setTask(task)

	broadened, err := Decode(Bytes(originalProfile))
	if err != nil {
		t.Fatal(err)
	}
	broadened["tool_policy"].(map[string]any)["write_paths"] = []any{"source.txt", "other.txt"}
	broadened["tool_policy"].(map[string]any)["max_write_bytes"] = 1024
	// A runtime binding is immutable. A replacement profile must therefore be
	// registered on a distinct real RuntimeRegistration, then selected by the
	// host route; the old Task still contains only the original Artifact ref.
	bindReplacement := func(profile Object) (RuntimeCoordinatorRoute, Object) {
		t.Helper()
		registration := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{
			"name": "replacement write profile", "adapter": "codex-cli", "adapter_revision": runtimeBridgeRevision,
			"capabilities": []any{"start", "context_rebuild"}, "platform": "windows-amd64",
			"measurement_mode": "FIXTURE", "credential_ref": nil,
		})
		profile["runtime_id"] = registration["id"]
		profile["technical_hash"] = runtimeTechnicalHash(registration)
		artifact := f.artifact(profile, Empty())
		qualification := f.task(req, []any{Ref(artifact, "Artifact")}, "runtime_qualification")
		f.bundle(qualification)
		if err := f.s.RegisterRuntimeQualificationPlan(ctx, f.token, f.project, Str(qualification, "id"), Str(registration, "id"), Ref(artifact, "Artifact"), []any{"start"}, time.Hour, ""); err != nil {
			t.Fatal(err)
		}
		next := route
		next.RuntimeID = Str(registration, "id")
		return next, Ref(artifact, "Artifact")
	}
	assertFreeze := func(model string, expected Object) {
		t.Helper()
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			refs, err := c.FreezeClientTaskInputs(ctx, tx, f.project, model)
			if err != nil {
				return err
			}
			if len(refs) != 1 || Hash(refs[0]) != Hash(expected) {
				t.Fatalf("freeze %q returned %v, want %v", model, refs, expected)
			}
			return nil
		})
	}
	replacement, replacementRef := bindReplacement(broadened)
	c.config.Routes = []RuntimeCoordinatorRoute{replacement}
	assertFreeze(modelRef, replacementRef)
	check("changed profile cannot broaden old task", task, "other.txt", 1, false)
	check("changed profile cannot raise old limit", task, "source.txt", 17, false)
	newModel, err := Decode(Bytes(broadened))
	if err != nil {
		t.Fatal(err)
	}
	modelConfig, err := Decode(Bytes(config))
	if err != nil {
		t.Fatal(err)
	}
	modelConfig["ref"] = "different-model"
	newModel["model_config"] = modelConfig
	newModel["model_qualification"].(map[string]any)["model_config_hash"] = Hash(modelConfig)
	newRoute, newModelRef := bindReplacement(newModel)
	c.config.Routes = []RuntimeCoordinatorRoute{newRoute}
	if _, err := f.db.Exec("UPDATE client_sessions SET model_config_ref=? WHERE id=?", "different-model", sid); err != nil {
		t.Fatal(err)
	}
	assertFreeze("different-model", newModelRef)
	check("new session model cannot expand old task", task, "source.txt", 1, false)
	c.config.Routes = []RuntimeCoordinatorRoute{route}
	if _, err := f.db.Exec("UPDATE client_sessions SET model_config_ref=? WHERE id=?", modelRef, sid); err != nil {
		t.Fatal(err)
	}
	check("restored original binding", task, "source.txt", 1, true)

	// Revoke the current Artifact through a new persisted version; currentRuntimeBinding
	// must reject the stale frozen ref without starting a new worker.
	revoked, err := Decode(Bytes(originalArtifact))
	if err != nil {
		t.Fatal(err)
	}
	revoked["validity"] = "REVOKED"
	if err := bump(revoked); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error { return f.s.put(tx, "Artifact", revoked) })
	check("revoked profile", task, "source.txt", 1, false)
}

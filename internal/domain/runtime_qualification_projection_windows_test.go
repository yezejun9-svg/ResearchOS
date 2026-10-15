//go:build windows

package domain

import (
	"context"
	"net/http"
	"testing"

	rt "researchos.local/research-os/adapters/runtime"
)

func TestQualificationProjectionStageAndPretransportTamper(t *testing.T) {
	c, route, r, calls := muBrokerFixture(t, nil)
	var raw string
	if err := r.f.db.QueryRow("SELECT manifest FROM runtime_dispatches WHERE run=?", r.run["id"]).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	manifest, err := Decode([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	provider := c.config.Providers[0]
	payload := Object{"body": Object{"model": "fixture-model", "stream": true, "max_tokens": 32, "messages": []any{Object{"role": "user", "content": "fixture"}}, "tools": Empty()}}
	for _, field := range []string{"schema", "project_id", "task_id", "run_id", "epoch", "runtime_id", "dispatch_key", "profile_ref", "profile_hash", "source_profile_body_hash", "source_model_config_hash", "qualification_plan_hash", "permission_hash", "effective_model_config_hash", "policy"} {
		t.Run(field, func(t *testing.T) {
			copy, err := Decode(Bytes(manifest))
			if err != nil {
				t.Fatal(err)
			}
			copy["model_execution_projection"].(map[string]any)[field] = "tampered"
			inputs := map[string][]byte{}
			if err := stageRuntimeProgram(route, Object{"manifest": copy}, inputs); err == nil {
				t.Fatal("staging accepted tampered marker")
			}
			_, err = c.brokerModel(context.Background(), route, provider, Str(r.run, "id"), r.lease, 1, nil, rt.BridgeFrame{}, payload, nil, Object{"manifest": copy})
			if err == nil {
				t.Fatal("pretransport accepted tampered marker")
			}
		})
	}
	if calls.Load() != 0 {
		t.Fatalf("tamper reached provider %d times", calls.Load())
	}
}

func TestQualificationProjectionPrepareUsesActualTask(t *testing.T) {
	_, _, r, _ := muBrokerFixture(t, nil)
	var raw string
	if err := r.f.db.QueryRow("SELECT manifest FROM runtime_dispatches WHERE run=?", r.run["id"]).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	manifest, err := Decode([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	if manifest["model_execution_projection"] == nil {
		t.Fatal("eligible production dispatch omitted marker")
	}
	admission := manifest["admission"].(map[string]any)
	task := Merge(r.task, Object{"task_type": "mu_turn"})
	tx, err := r.f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if err := r.f.s.prepareRuntimeDispatch(tx, r.f.project, task, r.run, admission); err == nil {
		t.Fatal("actual Task type contradiction accepted")
	}
	copyAdmission, err := Decode(Bytes(admission))
	if err != nil {
		t.Fatal(err)
	}
	copyAdmission["profile"].(map[string]any)["model_qualification"].(map[string]any)["max_calls"] = 2
	if err := r.f.s.prepareRuntimeDispatch(tx, r.f.project, r.task, r.run, copyAdmission); err == nil {
		t.Fatal("qualification max_calls=2 accepted")
	}
}

func TestQualificationProjectionLegacyAndNormalMuStage(t *testing.T) {
	_, route, r, _ := muBrokerFixtureProgram(t, nil, func(config, profile Object) {
		config["max_calls"] = 8
		config["tools"] = []any{Object{"type": "function", "function": Object{"name": "run_check", "parameters": Object{"type": "object"}}}}
	})
	var raw string
	if err := r.f.db.QueryRow("SELECT manifest FROM runtime_dispatches WHERE run=?", r.run["id"]).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	manifest, err := Decode([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	delete(manifest, "model_execution_projection")
	inputs := map[string][]byte{}
	if err := stageRuntimeProgram(route, Object{"manifest": manifest}, inputs); err != nil {
		t.Fatal(err)
	}
	worker, err := Decode(inputs["worker.json"])
	if err != nil {
		t.Fatal(err)
	}
	if n, _ := Num(worker, "max_calls"); n != 8 || len(Arr(worker, "tools")) != 1 {
		t.Fatal("legacy qualification did not retain original config")
	}
	admission := manifest["admission"].(map[string]any)
	admission["qualification_bootstrap"] = false
	admission["permission"].(map[string]any)["purpose"] = "mu_turn"
	inputs = map[string][]byte{}
	if err := stageRuntimeProgram(route, Object{"manifest": manifest}, inputs); err != nil {
		t.Fatal(err)
	}
	worker, err = Decode(inputs["worker.json"])
	if err != nil {
		t.Fatal(err)
	}
	if n, _ := Num(worker, "max_calls"); n != 8 || len(Arr(worker, "tools")) != 1 {
		t.Fatal("normal Mu turn lost original config")
	}
	payload := Object{"body": Object{"model": worker["model"], "stream": true, "max_tokens": 32, "messages": []any{Object{"role": "user", "content": "fixture"}}, "tools": worker["tools"]}}
	if _, err := validateRuntimeModelRequest(worker, payload); err != nil {
		t.Fatal(err)
	}
}

func TestQualificationProjectionHostPreprepareRejectsOldToolsAndSecondModel(t *testing.T) {
	c, route, r, calls := muBrokerFixtureProgram(t, func(w http.ResponseWriter, _ *http.Request) {
		t.Error("provider reached by rejected request")
		w.WriteHeader(500)
	}, func(config, profile Object) {
		config["max_calls"] = 8
		config["tools"] = []any{Object{"type": "function", "function": Object{"name": "run_check", "parameters": Object{"type": "object"}}}}
	})
	key1 := Str(r.task, "id") + ":" + Str(r.run, "id") + ":1:model:1"
	old := Object{"body": Object{"model": "fixture-model", "stream": true, "max_tokens": 32, "messages": []any{Object{"role": "user", "content": "fixture"}}, "tools": []any{Object{"type": "function", "function": Object{"name": "run_check", "parameters": Object{"type": "object"}}}}}}
	frame := rt.BridgeFrame{Key: key1, Route: "model-fixture", Capability: "MODEL", Payload: Bytes(old)}
	if _, err := c.brokerEffect(context.Background(), route, Str(r.run, "id"), r.lease, 1, nil, frame); err == nil {
		t.Fatal("old coding tool request prepared")
	}
	var effects int
	if err := r.f.db.QueryRow("SELECT count(*) FROM resource_effects WHERE run=?", r.run["id"]).Scan(&effects); err != nil || effects != 0 {
		t.Fatalf("rejected request wrote effects: %d %v", effects, err)
	}
	if calls.Load() != 0 {
		t.Fatal("rejected request reached provider")
	}
	tx, err := r.f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	if err = effectAppend(tx, r.f.project, Str(r.run, "id"), key1, Object{"state": "CONFIRMED", "payload": Object{"capability": "MODEL"}}); err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	frame.Key = Str(r.task, "id") + ":" + Str(r.run, "id") + ":1:model:2"
	frame.Payload = Bytes(Object{"body": Object{"model": "fixture-model", "stream": true, "max_tokens": 32, "messages": []any{Object{"role": "user", "content": "fixture"}}, "tools": Empty()}})
	if _, err = c.brokerEffect(context.Background(), route, Str(r.run, "id"), r.lease, 1, nil, frame); err == nil {
		t.Fatal("second MODEL request prepared")
	}
	if err := r.f.db.QueryRow("SELECT count(*) FROM resource_effects WHERE run=?", r.run["id"]).Scan(&effects); err != nil || effects != 1 {
		t.Fatalf("second request wrote effects: %d %v", effects, err)
	}
	if calls.Load() != 0 {
		t.Fatal("second request reached provider")
	}
}

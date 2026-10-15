package runtimepolicy

import (
	"encoding/json"
	"reflect"
	"testing"
)

func fixtureManifest(t *testing.T) map[string]any {
	t.Helper()
	tool := map[string]any{"type": "function", "function": map[string]any{"name": "run_check", "parameters": map[string]any{"type": "object", "properties": map[string]any{"command": map[string]any{"type": "string"}}}}}
	config := map[string]any{"api": "openai-completions", "model": "模型😀", "provider": "local", "ref": "source-ref", "route": "route-1", "endpoint": "http://127.0.0.1:1234/v1/chat/completions", "max_output_tokens": json.Number("2048"), "max_calls": json.Number("8"), "tools": []any{tool}}
	configHash, err := Hash(config)
	if err != nil {
		t.Fatal(err)
	}
	ref := map[string]any{"entity_type": "Artifact", "id": "profile-a", "revision": json.Number("1")}
	refHash, err := Hash(ref)
	if err != nil {
		t.Fatal(err)
	}
	return map[string]any{"project_id": "project-a", "task_id": "task-a", "run_id": "run-a", "runtime_id": "runtime-a", "dispatch_key": "dispatch-a", "epoch": json.Number("2"), "admission": map[string]any{"qualification_bootstrap": true, "profile_ref": ref, "profile_hash": refHash, "permission": map[string]any{"purpose": "runtime_qualification", "plan_hash": "sha256:plan-a"}, "profile": map[string]any{"backend": "mu-sdk-broker-v1", "model_config": config, "model_qualification": map[string]any{"route": "route-1", "model_config_hash": configHash, "max_calls": json.Number("1")}}}}
}

func TestQualificationProjectionPureAndTamper(t *testing.T) {
	m := fixtureManifest(t)
	before, _ := Hash(m)
	if err := Prepare(m, "runtime_qualification"); err != nil {
		t.Fatal(err)
	}
	effective, err := Effective(m, "runtime_qualification")
	if err != nil {
		t.Fatal(err)
	}
	if !exactNumber(effective["max_calls"], 1) || len(effective["tools"].([]any)) != 0 {
		t.Fatalf("effective bounds: %v", effective)
	}
	original := m["admission"].(map[string]any)["profile"].(map[string]any)["model_config"].(map[string]any)
	if !exactNumber(original["max_calls"], 8) || len(original["tools"].([]any)) != 1 {
		t.Fatal("source changed")
	}
	effective["model"] = "changed"
	effective["tools"] = append(effective["tools"].([]any), map[string]any{"name": "injected"})
	if original["model"] != "模型😀" || len(original["tools"].([]any)) != 1 {
		t.Fatal("effective aliases source")
	}
	other, err := Effective(m, "")
	if err != nil || other["model"] != "模型😀" {
		t.Fatalf("nondeterministic derivation: %v", err)
	}
	for _, field := range markerFields {
		mutated, _ := ownedMap(m)
		changed := mutated[ProjectionField].(map[string]any)
		delete(changed, field)
		if _, err := Effective(mutated, ""); err == nil {
			t.Errorf("missing %s accepted", field)
		}
	}
	for _, field := range []string{"schema", "project_id", "task_id", "run_id", "epoch", "runtime_id", "dispatch_key", "task_type", "profile_ref", "profile_hash", "source_profile_body_hash", "source_model_config_hash", "qualification_plan_hash", "permission_hash", "effective_model_config_hash", "policy"} {
		mutated, _ := ownedMap(m)
		changed := mutated[ProjectionField].(map[string]any)
		changed[field] = "tampered"
		if _, err := Effective(mutated, ""); err == nil {
			t.Errorf("tampered %s accepted", field)
		}
	}
	for _, field := range []string{"max_model_calls", "max_tool_calls"} {
		mutated, _ := ownedMap(m)
		changed := mutated[ProjectionField].(map[string]any)["policy"].(map[string]any)
		changed[field] = json.Number("9")
		if _, err := Effective(mutated, ""); err == nil {
			t.Errorf("tampered policy %s accepted", field)
		}
	}
	mutated, _ := ownedMap(m)
	mutated[ProjectionField].(map[string]any)["extra"] = true
	if _, err := Effective(mutated, ""); err == nil {
		t.Fatal("extra marker field accepted")
	}
	for name, mutate := range map[string]func(map[string]any){
		"purpose": func(x map[string]any) {
			x["admission"].(map[string]any)["permission"].(map[string]any)["purpose"] = "mu_turn"
		},
		"bootstrap": func(x map[string]any) { x["admission"].(map[string]any)["qualification_bootstrap"] = false },
		"config": func(x map[string]any) {
			x["admission"].(map[string]any)["profile"].(map[string]any)["model_config"].(map[string]any)["route"] = "other"
		},
		"plan": func(x map[string]any) {
			x["admission"].(map[string]any)["permission"].(map[string]any)["plan_hash"] = "other"
		},
	} {
		mutated, _ := ownedMap(m)
		mutate(mutated)
		if _, err := Effective(mutated, ""); err == nil {
			t.Errorf("tampered %s accepted", name)
		}
	}
	after, _ := Hash(m)
	if after == before {
		t.Fatal("marker was not committed into manifest hash")
	}
}

func TestQualificationProjectionLegacyAndCreation(t *testing.T) {
	legacy := fixtureManifest(t)
	original := legacy["admission"].(map[string]any)["profile"].(map[string]any)["model_config"].(map[string]any)
	got, err := Effective(legacy, "runtime_qualification")
	if err != nil || !reflect.DeepEqual(got["tools"], original["tools"]) {
		t.Fatal("legacy config changed", err)
	}
	if err := Prepare(legacy, "mu_turn"); err == nil {
		t.Fatal("contradictory Task type accepted")
	}
	bad := fixtureManifest(t)
	bad["admission"].(map[string]any)["profile"].(map[string]any)["model_qualification"].(map[string]any)["max_calls"] = 2
	if err := Prepare(bad, "runtime_qualification"); err == nil {
		t.Fatal("two-call qualification accepted")
	}
	normal := fixtureManifest(t)
	normalAdmission := normal["admission"].(map[string]any)
	normalAdmission["qualification_bootstrap"] = false
	normalAdmission["permission"].(map[string]any)["purpose"] = "mu_turn"
	if err := Prepare(normal, "mu_turn"); err != nil {
		t.Fatal(err)
	}
	if _, exists := normal[ProjectionField]; exists {
		t.Fatal("normal turn marked")
	}
	got, err = Effective(normal, "mu_turn")
	if err != nil || !reflect.DeepEqual(got["tools"], original["tools"]) {
		t.Fatal("normal turn schemas changed", err)
	}
}

func TestQualificationProjectionHashGolden(t *testing.T) {
	value := map[string]any{"😀": []any{map[string]any{"中": json.Number("1e0"), "n": json.Number("2.500")}}, "tools": []any{}}
	got, err := Hash(value)
	if err != nil {
		t.Fatal(err)
	}
	if got != "sha256:bcce6b88b4df307036224038610c85590a86b6dc8254202f49f1dfe532131257" {
		t.Fatalf("canonical hash drift: %s", got)
	}
}

//go:build windows

package runtime

import (
	"context"
	"encoding/json"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/runtimepolicy"
)

func qualificationBridgeManifest(t *testing.T) (map[string]any, map[string][]byte) {
	t.Helper()
	bundle := []byte("frozen local worker fixture")
	config := map[string]any{"api": "openai-completions", "model": "fixture-model", "provider": "local", "ref": "fixture-ref", "route": "route-a", "endpoint": "http://127.0.0.1:1234/v1/chat/completions", "max_output_tokens": json.Number("512"), "max_calls": json.Number("8"), "tools": []any{map[string]any{"type": "function", "function": map[string]any{"name": "run_check", "parameters": map[string]any{"type": "object"}}}}}
	configHash, err := runtimepolicy.Hash(config)
	if err != nil {
		t.Fatal(err)
	}
	ref := map[string]any{"entity_type": "Artifact", "id": "profile-a", "revision": json.Number("1")}
	refHash, err := runtimepolicy.Hash(ref)
	if err != nil {
		t.Fatal(err)
	}
	profile := map[string]any{"backend": "mu-sdk-broker-v1", "model": "fixture-model", "bundle_hash": Hash(bundle), "argv": []any{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}, "model_config": config, "model_qualification": map[string]any{"route": "route-a", "model_config_hash": configHash, "max_calls": json.Number("1")}}
	manifest := map[string]any{"project_id": "p", "task_id": "t", "run_id": "r", "runtime_id": "rt", "dispatch_key": "d", "epoch": json.Number("1"), "admission": map[string]any{"qualification_bootstrap": true, "profile_ref": ref, "profile_hash": refHash, "permission": map[string]any{"purpose": "runtime_qualification", "plan_hash": "sha256:plan"}, "profile": profile}}
	if err := runtimepolicy.Prepare(manifest, "runtime_qualification"); err != nil {
		t.Fatal(err)
	}
	effective, err := runtimepolicy.Effective(manifest, "")
	if err != nil {
		t.Fatal(err)
	}
	worker, err := json.Marshal(effective)
	if err != nil {
		t.Fatal(err)
	}
	return manifest, map[string][]byte{"mu-worker.mjs": bundle, "worker.json": worker}
}

func TestQualificationProjectionAdapterBeforeLaunch(t *testing.T) {
	manifest, inputs := qualificationBridgeManifest(t)
	if err := validateBridgeProgram(manifest, inputs); err != nil {
		t.Fatal(err)
	}
	profile := manifest["admission"].(map[string]any)["profile"].(map[string]any)
	old, err := json.Marshal(profile["model_config"])
	if err != nil {
		t.Fatal(err)
	}
	inputs["worker.json"] = old
	if err := validateBridgeProgram(manifest, inputs); err == nil {
		t.Fatal("old coding config staged under marker accepted")
	}
	raw, err := json.Marshal(manifest)
	if err != nil {
		t.Fatal(err)
	}
	digest, err := canonicalHash(raw)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = StartBridge(context.Background(), filepath.Join(t.TempDir(), "no-launch"), BridgeRequest{Manifest: raw, ManifestHash: digest, Inputs: inputs}); err == nil || !strings.Contains(err.Error(), "worker configuration") {
		t.Fatalf("StartBridge did not reject before native launch: %v", err)
	}
	effective, err := runtimepolicy.Effective(manifest, "")
	if err != nil {
		t.Fatal(err)
	}
	effective["tools"] = []any{}
	inputs["worker.json"], _ = json.Marshal(effective)
	delete(manifest, runtimepolicy.ProjectionField)
	if err := validateBridgeProgram(manifest, inputs); err == nil {
		t.Fatal("arbitrary tools=[] without marker accepted")
	}
	if err := runtimepolicy.Prepare(manifest, "runtime_qualification"); err != nil {
		t.Fatal(err)
	}
	for _, field := range []string{"schema", "project_id", "task_id", "run_id", "epoch", "runtime_id", "dispatch_key", "profile_hash", "source_profile_body_hash", "source_model_config_hash", "qualification_plan_hash", "permission_hash", "effective_model_config_hash", "policy"} {
		copy := map[string]any{}
		raw, _ := json.Marshal(manifest)
		if err := json.Unmarshal(raw, &copy); err != nil {
			t.Fatal(err)
		}
		copy[runtimepolicy.ProjectionField].(map[string]any)[field] = "tampered"
		if err := validateBridgeProgram(copy, inputs); err == nil {
			t.Errorf("adapter accepted tampered %s", field)
		}
	}
	inputs["mu-worker.mjs"] = []byte("changed")
	if err := validateBridgeProgram(manifest, inputs); err == nil {
		t.Fatal("bundle change accepted")
	}
}

func TestQualificationProjectionAdapterCanonicalHash(t *testing.T) {
	value := map[string]any{"😀": []any{map[string]any{"中": json.Number("1e0"), "n": json.Number("2.500")}}, "tools": []any{}}
	raw, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	adapter, err := canonicalHash(raw)
	if err != nil {
		t.Fatal(err)
	}
	policy, err := runtimepolicy.Hash(value)
	if err != nil {
		t.Fatal(err)
	}
	if adapter != policy || policy != "sha256:bcce6b88b4df307036224038610c85590a86b6dc8254202f49f1dfe532131257" {
		t.Fatalf("adapter/policy hash mismatch: %s %s", adapter, policy)
	}
}

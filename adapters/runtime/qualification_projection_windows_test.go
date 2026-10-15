//go:build windows

package runtime

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/runtimepolicy"
)

func cloneQualificationBridgeManifest(t *testing.T, manifest map[string]any) map[string]any {
	t.Helper()
	raw, err := json.Marshal(manifest)
	if err != nil {
		t.Fatal(err)
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	var clone map[string]any
	if err := decoder.Decode(&clone); err != nil {
		t.Fatal(err)
	}
	return clone
}

func qualificationBridgeManifest(t *testing.T) (map[string]any, map[string][]byte) {
	t.Helper()
	bundle := []byte("frozen local worker fixture")
	tools := []any{}
	for _, name := range []string{"run_check", "read_file", "edit_file", "shell_command"} {
		tools = append(tools, map[string]any{"type": "function", "function": map[string]any{"name": name, "parameters": map[string]any{"type": "object"}}})
	}
	config := map[string]any{"api": "openai-completions", "model": "fixture-model", "provider": "local", "ref": "fixture-ref", "route": "route-a", "endpoint": "http://127.0.0.1:1234/v1/chat/completions", "max_output_tokens": json.Number("512"), "max_calls": json.Number("8"), "tools": tools}
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
	mutations := []struct {
		name   string
		mutate func(map[string]any)
	}{}
	for _, field := range []string{"schema", "project_id", "task_id", "run_id", "epoch", "runtime_id", "dispatch_key", "task_type", "profile_ref", "profile_hash", "source_profile_body_hash", "source_model_config_hash", "qualification_plan_hash", "permission_hash", "effective_model_config_hash", "policy"} {
		field := field
		mutations = append(mutations, struct {
			name   string
			mutate func(map[string]any)
		}{"marker." + field, func(m map[string]any) { m[runtimepolicy.ProjectionField].(map[string]any)[field] = "tampered" }})
	}
	mutations = append(mutations,
		struct {
			name   string
			mutate func(map[string]any)
		}{"marker.policy.max_model_calls", func(m map[string]any) {
			m[runtimepolicy.ProjectionField].(map[string]any)["policy"].(map[string]any)["max_model_calls"] = json.Number("2")
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"marker.policy.max_tool_calls", func(m map[string]any) {
			m[runtimepolicy.ProjectionField].(map[string]any)["policy"].(map[string]any)["max_tool_calls"] = json.Number("1")
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"marker.extra_field", func(m map[string]any) { m[runtimepolicy.ProjectionField].(map[string]any)["extra_field"] = true }},
		struct {
			name   string
			mutate func(map[string]any)
		}{"marker.null_marker", func(m map[string]any) { m[runtimepolicy.ProjectionField] = nil }},
		struct {
			name   string
			mutate func(map[string]any)
		}{"marker.partial_marker", func(m map[string]any) {
			m[runtimepolicy.ProjectionField] = map[string]any{"schema": runtimepolicy.ProjectionSchema}
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.qualification_bootstrap", func(m map[string]any) { m["admission"].(map[string]any)["qualification_bootstrap"] = false }},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.permission.purpose", func(m map[string]any) {
			m["admission"].(map[string]any)["permission"].(map[string]any)["purpose"] = "mu_turn"
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.permission.plan_hash", func(m map[string]any) {
			m["admission"].(map[string]any)["permission"].(map[string]any)["plan_hash"] = "sha256:other"
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.profile_ref", func(m map[string]any) {
			m["admission"].(map[string]any)["profile_ref"].(map[string]any)["id"] = "other-profile"
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.profile_hash", func(m map[string]any) { m["admission"].(map[string]any)["profile_hash"] = "sha256:other" }},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.profile.model_config", func(m map[string]any) {
			m["admission"].(map[string]any)["profile"].(map[string]any)["model_config"].(map[string]any)["max_output_tokens"] = json.Number("513")
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.model_qualification.route", func(m map[string]any) {
			m["admission"].(map[string]any)["profile"].(map[string]any)["model_qualification"].(map[string]any)["route"] = "other"
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.model_qualification.model_config_hash", func(m map[string]any) {
			m["admission"].(map[string]any)["profile"].(map[string]any)["model_qualification"].(map[string]any)["model_config_hash"] = "sha256:other"
		}},
		struct {
			name   string
			mutate func(map[string]any)
		}{"authority.model_qualification.max_calls", func(m map[string]any) {
			m["admission"].(map[string]any)["profile"].(map[string]any)["model_qualification"].(map[string]any)["max_calls"] = json.Number("2")
		}},
	)
	for _, mutation := range mutations {
		t.Run(mutation.name, func(t *testing.T) {
			copy := cloneQualificationBridgeManifest(t, manifest)
			if err := validateBridgeProgram(copy, inputs); err != nil {
				t.Fatalf("unmodified numeric clone invalid: %v", err)
			}
			mutation.mutate(copy)
			if err := validateBridgeProgram(copy, inputs); err == nil {
				t.Fatal("adapter accepted mutation")
			}
			raw, err := json.Marshal(copy)
			if err != nil {
				t.Fatal(err)
			}
			digest, err := canonicalHash(raw)
			if err != nil {
				t.Fatal(err)
			}
			dir := filepath.Join(t.TempDir(), "no-launch")
			if _, err := StartBridge(context.Background(), dir, BridgeRequest{Manifest: raw, ManifestHash: digest, Inputs: inputs}); err == nil {
				t.Fatal("StartBridge accepted mutation")
			}
			if _, err := os.Stat(dir); !os.IsNotExist(err) {
				t.Fatalf("rejected mutation launched or created native directory: %v", err)
			}
		})
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

func TestQualificationProjectionAdapterLegacyNormalOriginalConfig(t *testing.T) {
	manifest, inputs := qualificationBridgeManifest(t)
	profile := manifest["admission"].(map[string]any)["profile"].(map[string]any)
	config := profile["model_config"].(map[string]any)
	if config["max_calls"] != json.Number("8") || len(config["tools"].([]any)) != 4 {
		t.Fatal("source fixture is not full original 8/4")
	}
	// Keep all original fields, including the source tool schema and argv.
	before, err := runtimepolicy.Hash(config)
	if err != nil {
		t.Fatal(err)
	}
	argv, err := json.Marshal(profile["argv"])
	if err != nil {
		t.Fatal(err)
	}
	inputs["worker.json"], err = json.Marshal(config)
	if err != nil {
		t.Fatal(err)
	}
	delete(manifest, runtimepolicy.ProjectionField)
	for _, name := range []string{"legacy", "normal"} {
		t.Run(name, func(t *testing.T) {
			copy := cloneQualificationBridgeManifest(t, manifest)
			if name == "normal" {
				admission := copy["admission"].(map[string]any)
				admission["qualification_bootstrap"] = false
				admission["permission"].(map[string]any)["purpose"] = "mu_turn"
			}
			if err := validateBridgeProgram(copy, inputs); err != nil {
				t.Fatalf("original unmarked Mu config rejected: %v", err)
			}
			current := copy["admission"].(map[string]any)["profile"].(map[string]any)
			after, err := runtimepolicy.Hash(current["model_config"])
			if err != nil || after != before {
				t.Fatalf("original config changed: %s %s %v", before, after, err)
			}
			currentArgv, err := json.Marshal(current["argv"])
			if err != nil || !bytes.Equal(currentArgv, argv) {
				t.Fatalf("original argv changed: %v", err)
			}
		})
	}
}

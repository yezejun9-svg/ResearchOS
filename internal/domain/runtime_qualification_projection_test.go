package domain

import (
	"encoding/json"
	"testing"

	"researchos.local/research-os/internal/runtimepolicy"
)

func TestQualificationProjectionDomainCanonicalHash(t *testing.T) {
	value := Object{"😀": []any{Object{"中": json.Number("1e0"), "n": json.Number("2.500")}}, "tools": Empty()}
	policy, err := runtimepolicy.Hash(value)
	if err != nil {
		t.Fatal(err)
	}
	if policy != Hash(value) || policy != "sha256:bcce6b88b4df307036224038610c85590a86b6dc8254202f49f1dfe532131257" {
		t.Fatalf("domain/policy hash mismatch: %s %s", Hash(value), policy)
	}
}

type qualificationProjectionMutation struct {
	name  string
	apply func(Object)
}

// The same independent attacks are applied at each production consumer. Each
// caller first proves that its unmodified numeric clone is valid.
func qualificationProjectionMutations() []qualificationProjectionMutation {
	cases := []qualificationProjectionMutation{}
	for _, field := range []string{"schema", "project_id", "task_id", "run_id", "epoch", "runtime_id", "dispatch_key", "task_type", "profile_ref", "profile_hash", "source_profile_body_hash", "source_model_config_hash", "qualification_plan_hash", "permission_hash", "effective_model_config_hash", "policy"} {
		field := field
		cases = append(cases, qualificationProjectionMutation{"marker." + field, func(m Object) {
			m[runtimepolicy.ProjectionField].(map[string]any)[field] = "tampered"
		}})
	}
	cases = append(cases,
		qualificationProjectionMutation{"marker.policy.max_model_calls", func(m Object) {
			m[runtimepolicy.ProjectionField].(map[string]any)["policy"].(map[string]any)["max_model_calls"] = json.Number("2")
		}},
		qualificationProjectionMutation{"marker.policy.max_tool_calls", func(m Object) {
			m[runtimepolicy.ProjectionField].(map[string]any)["policy"].(map[string]any)["max_tool_calls"] = json.Number("1")
		}},
		qualificationProjectionMutation{"marker.extra_field", func(m Object) { m[runtimepolicy.ProjectionField].(map[string]any)["extra_field"] = true }},
		qualificationProjectionMutation{"marker.null_marker", func(m Object) { m[runtimepolicy.ProjectionField] = nil }},
		qualificationProjectionMutation{"marker.partial_marker", func(m Object) { m[runtimepolicy.ProjectionField] = Object{"schema": runtimepolicy.ProjectionSchema} }},
		qualificationProjectionMutation{"authority.qualification_bootstrap", func(m Object) { m["admission"].(map[string]any)["qualification_bootstrap"] = false }},
		qualificationProjectionMutation{"authority.permission.purpose", func(m Object) { m["admission"].(map[string]any)["permission"].(map[string]any)["purpose"] = "mu_turn" }},
		qualificationProjectionMutation{"authority.permission.plan_hash", func(m Object) {
			m["admission"].(map[string]any)["permission"].(map[string]any)["plan_hash"] = "sha256:other"
		}},
		qualificationProjectionMutation{"authority.profile_ref", func(m Object) {
			m["admission"].(map[string]any)["profile_ref"].(map[string]any)["id"] = "other-profile"
		}},
		qualificationProjectionMutation{"authority.profile_hash", func(m Object) { m["admission"].(map[string]any)["profile_hash"] = "sha256:other" }},
		qualificationProjectionMutation{"authority.profile.model_config", func(m Object) {
			m["admission"].(map[string]any)["profile"].(map[string]any)["model_config"].(map[string]any)["max_output_tokens"] = json.Number("513")
		}},
		qualificationProjectionMutation{"authority.model_qualification.route", func(m Object) {
			m["admission"].(map[string]any)["profile"].(map[string]any)["model_qualification"].(map[string]any)["route"] = "other"
		}},
		qualificationProjectionMutation{"authority.model_qualification.model_config_hash", func(m Object) {
			m["admission"].(map[string]any)["profile"].(map[string]any)["model_qualification"].(map[string]any)["model_config_hash"] = "sha256:other"
		}},
		qualificationProjectionMutation{"authority.model_qualification.max_calls", func(m Object) {
			m["admission"].(map[string]any)["profile"].(map[string]any)["model_qualification"].(map[string]any)["max_calls"] = json.Number("2")
		}},
	)
	return cases
}

func qualificationProjectionClone(t *testing.T, manifest Object) Object {
	t.Helper()
	copy, err := Decode(Bytes(manifest))
	if err != nil || Hash(copy) != Hash(manifest) {
		t.Fatalf("unmodified numeric clone invalid: %v", err)
	}
	effective, err := runtimepolicy.Effective(copy, "runtime_qualification")
	if err != nil {
		t.Fatalf("unmodified projected clone invalid: %v", err)
	}
	if n, err := Num(effective, "max_calls"); err != nil || n != 1 || len(Arr(effective, "tools")) != 0 {
		t.Fatalf("unmodified projected bounds invalid: %v %v", effective, err)
	}
	return copy
}

func qualificationProjectionMutant(t *testing.T, manifest Object, mutation qualificationProjectionMutation) Object {
	t.Helper()
	copy := qualificationProjectionClone(t, manifest)
	before := Hash(copy)
	mutation.apply(copy)
	if Hash(copy) == before {
		t.Fatalf("mutation %s made no change", mutation.name)
	}
	if _, err := runtimepolicy.Effective(copy, "runtime_qualification"); err == nil {
		t.Fatalf("mutation %s did not invalidate projection", mutation.name)
	}
	return copy
}

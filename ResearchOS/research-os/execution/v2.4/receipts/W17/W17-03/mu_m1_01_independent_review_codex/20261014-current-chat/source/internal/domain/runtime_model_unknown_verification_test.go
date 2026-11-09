package domain

import "testing"

// These are verifier counterexamples, not fabricated runtime acceptance.
// Actual producer/ledger/snapshot integration is tested by the Host synthetic
// transport case using the real broker and separate verifier executable.
func TestMuUnknownVerificationFidelity(t *testing.T) {
	const at = "2026-10-01T00:00:00Z"
	run := Object{"id": "run", "created_at": at}
	task := Object{"id": "task", "project_id": "project", "goal_id": "goal"}
	request := Object{"capability": "MODEL", "credential_revision": "none", "route": "local", "payload": Object{"model": "fixture"}}
	ledger := Object{"id": "ledger", "project_id": "project", "run_id": "run", "provider_request_id": "key", "provider_event_id": "prepare/key", "operation": "UNKNOWN", "cost_basis": "UNKNOWN", "money": nil, "reservation_id": nil, "occurred_at": at, "policy_id": "project-policy"}
	cost := Object{"policy_id": "project-policy", "run_id": "run", "operation": "UNKNOWN", "money": nil, "provider_request_id": "key", "provider_event_id": "prepare/key", "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": at}
	effect := Object{"key": "key", "reservation_id": "ledger", "request_hash": Hash([]any{request, cost})}
	policy := func(id string, parent any, scope string, project any) Object {
		return Object{"id": id, "parent_policy_id": parent, "scope_type": scope, "project_id": project, "revision": 1, "effective_from": at, "updated_at": at, "mode": "UNLIMITED_AMOUNT", "cap": nil, "unknown_cost_action": "ALLOW_AND_RECORD"}
	}
	mu := Object{"profile": Object{"max_cost": nil, "credential_revision": "none", "host_setup": Object{"schema": "researchos.local-runtime-setup.v1"}, "model_config": Object{"endpoint": "http://127.0.0.1:1/v1/chat/completions", "credential_ref": nil}}, "ledger": []any{ledger}, "unknown_budget": Object{"goal": Object{"id": "goal", "project_id": "project", "budget_policy_id": "project-policy"}, "leaves": Object{"project-policy": true}, "policies": []any{policy("project-policy", "global", "PROJECT", "project"), policy("global", nil, "GLOBAL", nil)}}}
	all := Object{"mu": mu, "task": task, "run": run, "request": request, "effect": effect, "ledger": ledger}
	check := func(input Object) string {
		return verifyMuUnknownBudget(input["mu"].(map[string]any), input["task"].(map[string]any), input["run"].(map[string]any), input["request"].(map[string]any), input["effect"].(map[string]any), input["ledger"].(map[string]any))
	}
	if reason := check(all); reason != "" {
		t.Fatal(reason)
	}
	budget := func(o Object) Object { return o["mu"].(map[string]any)["unknown_budget"].(map[string]any) }
	row := func(o Object) Object { return o["ledger"].(map[string]any) }
	cases := map[string]func(Object){
		"null rewritten as zero":   func(o Object) { row(o)["money"] = dollars("0") },
		"non-null reservation":     func(o Object) { row(o)["reservation_id"] = "other" },
		"forged basis":             func(o Object) { row(o)["cost_basis"] = "ACTUAL" },
		"forged operation":         func(o Object) { row(o)["operation"] = "RESERVE" },
		"wrong original time":      func(o Object) { row(o)["occurred_at"] = "2026-10-02T00:00:00Z" },
		"wrong request hash":       func(o Object) { o["effect"].(map[string]any)["request_hash"] = Digest([]byte("wrong")) },
		"missing policy chain":     func(o Object) { budget(o)["policies"] = Empty() },
		"missing global ancestor":  func(o Object) { budget(o)["policies"] = Arr(budget(o), "policies")[:1] },
		"capped global":            func(o Object) { Arr(budget(o), "policies")[1].(map[string]any)["mode"] = "CAPPED" },
		"global denies unknown":    func(o Object) { Arr(budget(o), "policies")[1].(map[string]any)["unknown_cost_action"] = "BLOCK" },
		"policy changed after run": func(o Object) { Arr(budget(o), "policies")[0].(map[string]any)["updated_at"] = "2026-10-02T00:00:00Z" },
		"scope leaf missing":       func(o Object) { budget(o)["leaves"] = Object{} },
		"unrelated goal":           func(o Object) { budget(o)["goal"].(map[string]any)["id"] = "wrong" },
		"duplicate liability":      func(o Object) { m := o["mu"].(map[string]any); m["ledger"] = append(Arr(m, "ledger"), row(o)) },
		"remote endpoint": func(o Object) {
			o["mu"].(map[string]any)["profile"].(map[string]any)["model_config"].(map[string]any)["endpoint"] = "https://example.org/v1/chat/completions"
		},
		"credential supplied": func(o Object) {
			o["mu"].(map[string]any)["profile"].(map[string]any)["model_config"].(map[string]any)["credential_ref"] = "secret-ref"
		},
		"tool cost unknown": func(o Object) { o["request"].(map[string]any)["capability"] = "TOOL" },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			clone, e := Decode(Bytes(all))
			if e != nil {
				t.Fatal(e)
			}
			mutate(clone)
			if reason := check(clone); reason == "" {
				t.Fatal("invalid UNKNOWN evidence accepted")
			}
		})
	}
	if ledger["money"] != nil || ledger["reservation_id"] != nil || ledger["operation"] != "UNKNOWN" {
		t.Fatal("verifier mutated original accounting")
	}
}

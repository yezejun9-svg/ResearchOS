package domain

import "time"

// Only the configured credential-free local MODEL path can use this exception.
// No budget row is changed, and null monetary cost is never replaced with zero.
func verifyMuUnknownBudget(mu, task, run, request, effect, ledger Object) string {
	profile, _ := mu["profile"].(map[string]any)
	config, _ := profile["model_config"].(map[string]any)
	setup, _ := profile["host_setup"].(map[string]any)
	if request["capability"] != "MODEL" || profile["max_cost"] != nil || setup["schema"] != "researchos.local-runtime-setup.v1" || !clientConfigurationLoopbackModelEndpoint(Str(config, "endpoint")) || config["credential_ref"] != nil || profile["credential_revision"] != "none" || request["credential_revision"] != "none" {
		return "Unknown cost is not the frozen credential-free local model branch."
	}
	key := Str(effect, "key")
	if ledger == nil || ledger["project_id"] != task["project_id"] || ledger["run_id"] != run["id"] || ledger["id"] != effect["reservation_id"] || ledger["provider_request_id"] != key || ledger["provider_event_id"] != "prepare/"+key || ledger["operation"] != "UNKNOWN" || ledger["cost_basis"] != "UNKNOWN" || ledger["money"] != nil || ledger["reservation_id"] != nil || ledger["occurred_at"] != run["created_at"] {
		return "Original UNKNOWN ledger with null money and reservation required."
	}
	count := 0
	for _, value := range Arr(mu, "ledger") {
		row, _ := value.(map[string]any)
		if row["provider_request_id"] == key {
			count++
		}
	}
	if count != 1 {
		return "Unknown model liability must retain its single original ledger row."
	}
	budget, _ := mu["unknown_budget"].(map[string]any)
	goal, _ := budget["goal"].(map[string]any)
	if goal["id"] != task["goal_id"] || goal["project_id"] != task["project_id"] || goal["budget_policy_id"] != ledger["policy_id"] {
		return "Unknown budget goal scope missing or changed."
	}
	// Normalize typed maps from direct Go and JSON IPC snapshots identically.
	leavesObject, err := Decode(Bytes(budget["leaves"]))
	if err != nil || len(leavesObject) == 0 || leavesObject[Str(ledger, "policy_id")] != true {
		return "Unknown budget scope leaves missing."
	}
	policies := []Object{}
	byID := map[string]Object{}
	started, err := time.Parse(time.RFC3339Nano, Str(run, "created_at"))
	if err != nil {
		return "Unknown budget run timestamp missing."
	}
	for _, value := range Arr(budget, "policies") {
		policy, ok := value.(map[string]any)
		id := Str(policy, "id")
		if !ok || id == "" || byID[id] != nil {
			return "Unknown budget policy identity missing or duplicated."
		}
		revision, e := Num(policy, "revision")
		if e != nil || revision < 1 {
			return "Unknown budget policy revision missing."
		}
		for _, field := range []string{"effective_from", "updated_at"} {
			at, e := time.Parse(time.RFC3339Nano, Str(policy, field))
			if e != nil || at.After(started) {
				return "Unknown budget changed since the original run admission."
			}
		}
		if policy["project_id"] != nil && policy["project_id"] != "" && policy["project_id"] != task["project_id"] {
			return "Unknown budget belongs to another project."
		}
		policies = append(policies, policy)
		byID[id] = policy
	}
	if qualificationUnlimitedPolicies(policies) != nil {
		return "Unknown cost requires every budget ancestor unlimited with ALLOW_AND_RECORD."
	}
	seenAll := map[string]bool{}
	for leaf, allowed := range leavesObject {
		if allowed != true {
			return "Malformed unknown budget scope leaf."
		}
		seen := map[string]bool{}
		id := leaf
		for {
			p := byID[id]
			if p == nil || seen[id] {
				return "Unknown budget ancestry missing or cyclic."
			}
			seen[id] = true
			seenAll[id] = true
			parent := Str(p, "parent_policy_id")
			if parent == "" {
				if p["scope_type"] != "GLOBAL" || (p["project_id"] != nil && p["project_id"] != "") {
					return "Unknown budget ancestry lacks its global root."
				}
				break
			}
			id = parent
		}
	}
	if len(seenAll) != len(byID) {
		return "Unknown budget has unrelated policy evidence."
	}
	cost := Object{"policy_id": ledger["policy_id"], "run_id": run["id"], "operation": "UNKNOWN", "money": nil, "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": run["created_at"]}
	if effect["request_hash"] != Hash([]any{request, cost}) {
		return "Unknown effect request differs from its original null-cost admission."
	}
	return ""
}

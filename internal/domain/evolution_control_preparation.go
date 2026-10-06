//go:build windows

package domain

import (
	"database/sql"
	"fmt"
	"researchos.local/research-os/evaluation/evolution"
	"strings"
)

// createExperiment creates one default child budget before G0. This permits
// only that exact new policy; existing and unrelated policies remain frozen.
func controlPreparationBudget(before upgradeData, n *controlCurrentNames) (string, error) {
	old := map[string]Object{}
	for _, row := range before["domain_objects"] {
		old[controlEntityKey(row)] = row
	}
	var experiment, profile Object
	var policyRow Object
	for _, row := range n.Rows["domain_objects"] {
		if row["project"] == n.Project && row["kind"] == "Experiment" && row["id"] == n.Experiment {
			experiment, _ = controlBody(row)
		}
	}
	for _, row := range before["domain_objects"] {
		if row["project"] == n.Project && row["kind"] == "ProjectProfile" {
			profile, _ = controlBody(row)
		}
	}
	for _, row := range n.Rows["domain_objects"] {
		if row["project"] == n.Project && row["kind"] == "BudgetPolicy" && row["id"] == experiment["budget_policy_id"] {
			policyRow = row
		}
	}
	if experiment == nil || profile == nil || policyRow == nil || old[controlEntityKey(policyRow)] != nil {
		return "", fmt.Errorf("CONTROL_PREPARATION_EXPERIMENT_BUDGET_REQUIRED")
	}
	p, err := controlBody(policyRow)
	if err != nil {
		return "", err
	}
	parent := old[Hash([]any{n.Project, "BudgetPolicy", profile["budget_policy_id"]})]
	expected := Object{"id": p["id"], "project_id": n.Project, "revision": 1, "created_at": p["created_at"], "updated_at": p["updated_at"], "scope_type": "EXPERIMENT", "scope_id": n.Experiment, "parent_policy_id": profile["budget_policy_id"], "mode": "UNLIMITED_AMOUNT", "cap": nil, "enforcement": "ACCOUNTING_ONLY", "period": "LIFETIME", "timezone": "Asia/Shanghai", "effective_from": p["effective_from"], "unknown_cost_action": "ALLOW_AND_RECORD"}
	if parent == nil || p["created_at"] != p["updated_at"] || Str(p, "created_at") == "" || Str(p, "effective_from") == "" || Hash(p) != Hash(expected) || policyRow["revision"] != int64(1) || policyRow["content_hash"] != nil || policyRow["immutable"] != int64(0) {
		return "", fmt.Errorf("CONTROL_PREPARATION_EXPERIMENT_BUDGET_CHANGED")
	}
	return Str(p, "id"), nil
}

func controlPreparationExisting(kind string, before, after Object, n *controlCurrentNames) bool {
	if kind == "ProjectState" {
		return controlSameExcept(before, after, "revision updated_at event_sequence")
	}
	if kind != "Goal" || before["id"] != n.Goal || after["id"] != n.Goal || !controlSameExcept(before, after, "revision updated_at task_ids") {
		return false
	}
	oldRevision, oe := Num(before, "revision")
	newRevision, ne := Num(after, "revision")
	for _, id := range Arr(before, "task_ids") {
		if id == n.Task {
			return false
		}
	}
	expected := append(append([]any{}, Arr(before, "task_ids")...), n.Task)
	return oe == nil && ne == nil && newRevision == oldRevision+1 && Hash(after["task_ids"]) == Hash(expected)
}

func controlPreparationAuthorityDelta(q controlQuery, before, after upgradeData, n *controlCurrentNames) ([]evolution.ControlGenerationDelta, error) {
	delta, err := controlRowDifferences(q, before, after)
	if err != nil {
		return nil, err
	}
	indexes, err := controlIndexChanges(q, before, after, delta)
	if err != nil {
		return nil, err
	}
	for i := range delta {
		d := &delta[i]
		authority := strings.HasPrefix(d.Table, "auth_") || strings.HasPrefix(d.Table, "remote_") || d.Table == "orchestration_identity"
		if !authority {
			continue
		}
		r := indexes[d.Table].after[d.KeyHash]
		// All identities and credentials are provisioned before B0. The sole
		// authority addition is createRuntimeRun's exact named executor grant.
		if d.BeforeHash != "" || d.Table != "auth_grants" || r == nil || r["principal"] != n.Executor || r["project"] != n.Project || r["task"] != n.Task || r["run"] != n.Run || r["restricted"] != int64(0) {
			return nil, fmt.Errorf("CONTROL_PREPARATION_AUTHORITY_CHANGED:%s", d.Table)
		}
		d.Reason = "NAMED_CLAIM_EXECUTOR_RUN_GRANT"
	}
	return delta, nil
}

func (a *currentControlAuthority) validatePreparation(tx *sql.Tx, before upgradeData, n *controlCurrentNames) ([]evolution.ControlGenerationDelta, error) {
	after := n.Rows
	budgetID, err := controlPreparationBudget(before, n)
	if err != nil {
		return nil, err
	}
	delta, err := controlPreparationAuthorityDelta(tx, before, after, n)
	if err != nil {
		return nil, err
	}
	// Each principal must already exist in B0, even when a later current check
	// would still consider a substituted identity locally authorized.
	principals := map[string]bool{}
	for _, r := range before["auth_principals"] {
		principals[Str(r, "id")] = true
	}
	for _, id := range []string{a.ownerID, n.Author, n.Release, n.Executor, n.Verifier} {
		if !principals[id] {
			return nil, fmt.Errorf("CONTROL_PREPARATION_PRINCIPAL_NOT_IN_B0")
		}
	}
	old := map[string]Object{}
	objects := map[string]Object{}
	versions := map[string]Object{}
	for _, r := range before["domain_objects"] {
		old[controlEntityKey(r)] = r
	}
	for _, r := range after["domain_objects"] {
		objects[controlEntityKey(r)] = r
	}
	for _, r := range after["domain_versions"] {
		versions[controlVersionKey(r)] = r
	}
	allowed := map[string]bool{"Task:" + n.Task: true, "Run:" + n.Run: true, "Experiment:" + n.Experiment: true, "SystemCandidate:" + n.Candidate: true, "NoProgressRecord:" + n.Retention: true, "ProjectState:" + n.State: true}
	allowed["BudgetPolicy:"+budgetID] = true
	allowed["Goal:"+n.Goal] = true
	taskRow := objects[Hash([]any{n.Project, "Task", n.Task})]
	task, e := controlBody(taskRow)
	if e != nil {
		return nil, e
	}
	contextID := Str(task, "context_bundle_id")
	allowed["ContextBundle:"+contextID] = true
	var refs func(any)
	refs = func(v any) {
		switch value := v.(type) {
		case map[string]any:
			if value["entity_type"] == "Artifact" {
				allowed["Artifact:"+Str(value, "id")] = true
			}
			for _, x := range value {
				refs(x)
			}
		case []any:
			for _, x := range value {
				refs(x)
			}
		}
	}
	refs(a.snapshotRef)
	refs(a.stableRef)
	refs(a.candidateRef)
	refs(a.provenanceRef)
	for _, pair := range []struct{ kind, id string }{{"Task", n.Task}, {"Run", n.Run}, {"Experiment", n.Experiment}, {"SystemCandidate", n.Candidate}, {"ContextBundle", contextID}} {
		row := objects[Hash([]any{n.Project, pair.kind, pair.id})]
		body, e := controlBody(row)
		if e != nil {
			return nil, e
		}
		refs(body)
	}
	h, e := evolutionHost(tx, n.Project)
	if e != nil {
		return nil, e
	}
	refs(h)
	frozen, present, e := evolutionHoldoutEntry(tx, n.Project, n.Candidate, "HOLDOUT_FROZEN")
	if e != nil || !present {
		return nil, fmt.Errorf("CONTROL_PREPARATION_HOLDOUT_MISSING")
	}
	refs(frozen)
	bundle, err := controlBody(objects[Hash([]any{n.Project, "ContextBundle", contextID})])
	if err != nil {
		return nil, err
	}
	goal, err := controlBody(objects[Hash([]any{n.Project, "Goal", n.Goal})])
	if err != nil {
		return nil, err
	}
	scopes, _, err := runBudgetScopes(tx, n.Project, n.Run)
	if err != nil {
		return nil, err
	}
	currency := "USD"
	for _, p := range scopes {
		if p["cap"] != nil {
			currency = Str(p["cap"].(map[string]any), "currency")
			break
		}
	}
	ledgerCount := 0
	for key, row := range objects {
		if old[key] != nil || row["project"] != n.Project {
			continue
		}
		body, e := controlBody(row)
		if e != nil {
			return nil, e
		}
		switch row["kind"] {
		case "BudgetLedgerEntry":
			expected := Object{"id": body["id"], "project_id": n.Project, "revision": 1, "created_at": body["created_at"], "policy_id": goal["budget_policy_id"], "run_id": n.Run, "operation": "RESERVE", "money": Object{"amount": "0", "currency": currency}, "provider_request_id": "fixture-dispatch/" + n.Run, "provider_event_id": "fixture-dispatch/" + n.Run, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": body["occurred_at"], "receipt_hash": body["receipt_hash"]}
			if Hash(expected) == Hash(body) && body["receipt_hash"] == Receipt(body) {
				allowed["BudgetLedgerEntry:"+Str(row, "id")] = true
				ledgerCount++
			}
		case "ImpactLink":
			ref, _ := body["from_ref"].(map[string]any)
			version := versions[Hash([]any{n.Project, "Task", n.Task, ref["revision"]})]
			boundTask, _ := controlBody(version)
			to, _ := body["to_ref"].(map[string]any)
			if Hash(body["revision"]) == Hash(1) && body["status"] == "ACTIVE" && body["basis"] == "DETERMINISTIC" && body["relation"] == "DEPENDS_ON" && ref["entity_type"] == "Task" && ref["id"] == n.Task && boundTask["context_bundle_id"] == contextID && Hash(ref) == Hash(Ref(boundTask, "Task")) && containsRef(Arr(bundle, "version_vector"), to) && Hash(body["evidence_refs"]) == Hash([]any{Ref(bundle, "ContextBundle")}) {
				allowed["ImpactLink:"+Str(row, "id")] = true
			}
		}
	}
	if ledgerCount != 1 {
		return nil, fmt.Errorf("CONTROL_PREPARATION_EXACT_ZERO_FIXTURE_RESERVATION")
	}
	for key, row := range objects {
		if old[key] != nil || row["project"] != n.Project {
			continue
		}
		body, e := controlBody(row)
		if e != nil {
			return nil, e
		}
		switch row["kind"] {
		case "EventEnvelope":
			ref, _ := body["aggregate_ref"].(map[string]any)
			if allowed[Str(ref, "entity_type")+":"+Str(ref, "id")] && (n.actor(Str(body, "actor_id")) || body["actor_id"] == a.ownerID) {
				allowed["EventEnvelope:"+Str(row, "id")] = true
			}
		}
	}
	indexes, err := controlIndexChanges(tx, before, after, delta)
	if err != nil {
		return nil, err
	}
	for i := range delta {
		d := &delta[i]
		if d.Reason != "" {
			continue
		}
		index := indexes[d.Table]
		b, r := index.before[d.KeyHash], index.after[d.KeyHash]
		if r == nil {
			return nil, fmt.Errorf("CONTROL_PREPARATION_ROW_REMOVED:%s", d.Table)
		}
		permitted := false
		if b != nil {
			if d.Table == "domain_objects" && r["project"] == n.Project && (r["kind"] == "ProjectState" && r["id"] == n.State || r["kind"] == "Goal" && r["id"] == n.Goal) {
				bb, be := controlBody(b)
				rb, re := controlBody(r)
				permitted = be == nil && re == nil && controlPreparationExisting(Str(r, "kind"), bb, rb, n)
			}
			if d.Table == "sqlite_sequence" && r["name"] == "evolution_journal" {
				permitted = true
			}
		} else {
			switch d.Table {
			case "domain_objects", "domain_versions":
				permitted = r["project"] == n.Project && allowed[Str(r, "kind")+":"+Str(r, "id")]
				if original := old[controlEntityKey(r)]; permitted && original != nil {
					ob, oe := controlBody(original)
					rb, re := controlBody(r)
					permitted = oe == nil && re == nil && controlPreparationExisting(Str(r, "kind"), ob, rb, n)
				}
			case "domain_refs":
				permitted = r["project"] == n.Project && allowed[Str(r, "kind")+":"+Str(r, "id")] && controlReferenceRowBound(r, versions, old)
			case "outbox":
				permitted = r["project"] == n.Project && allowed["EventEnvelope:"+Str(r, "id")] && r["acknowledged"] == int64(0)
			case "event_state_snapshots":
				permitted = r["project"] == n.Project && allowed["EventEnvelope:"+Str(r, "event_id")]
			case "uploaded_content":
				if r["project"] == n.Project && (n.actor(Str(r, "principal")) || r["principal"] == a.ownerID) && r["sealed"] == int64(1) {
					for _, obj := range objects {
						if obj["kind"] == "Artifact" && allowed["Artifact:"+Str(obj, "id")] {
							body, e := controlBody(obj)
							raw, ok := r["bytes"].([]byte)
							if e == nil && ok && body["storage_key"] == r["storage_key"] && body["content_hash"] == Digest(raw) && r["content_hash"] == Digest(raw) {
								permitted = true
							}
						}
					}
				}
			case "evolution_hosts":
				current, _ := h["current_control"].(map[string]any)
				body, decodeErr := controlBody(r)
				permitted = r["project"] == n.Project && current["session_id"] == a.id && decodeErr == nil && Hash(body) == Hash(h)
			case "evolution_slots":
				permitted = r["project"] == n.Project && r["stable_hash"] == a.owner.StableHash && r["active_hash"] == a.owner.StableHash && r["state"] == "STABLE" && r["candidate"] == nil && r["epoch"] == int64(1)
			case "evolution_builds":
				permitted = r["project"] == n.Project && (r["artifact"] == a.stableRef["id"] || r["artifact"] == a.candidateRef["id"])
			case "evolution_candidates":
				permitted = r["project"] == n.Project && r["candidate"] == n.Candidate && r["creator"] == n.Author && r["plan_hash"] == n.Plan
			case "evolution_tasks":
				permitted = r["project"] == n.Project && r["task"] == n.Task && r["candidate"] == n.Candidate && r["phase"] == "REGRESSION"
			case "experiment_tasks":
				permitted = r["project"] == n.Project && r["experiment"] == n.Experiment && r["task"] == n.Task
			case "experiment_runs":
				permitted = r["project"] == n.Project && r["experiment"] == n.Experiment && r["run"] == n.Run
			case "orchestration_contracts":
				permitted = r["project"] == n.Project && r["task"] == n.Task
			case "orchestration_run_dependencies":
				permitted = r["project"] == n.Project && r["run"] == n.Run && r["snapshot"] == string(Bytes(Object{"refs": Empty()}))
			case "evolution_journal":
				body, e := controlBody(r)
				permitted = r["project"] == n.Project && r["candidate"] == n.Candidate && r["run"] == "" && (r["event"] == "ISOLATED" || r["event"] == "HOLDOUT_FROZEN") && e == nil && r["receipt_hash"] == Hash(body)
			case "sqlite_sequence":
				permitted = r["name"] == "evolution_journal"
			case "idempotency":
				ops := map[string]bool{}
				for _, op := range strings.Fields("uploadContent sealArtifact createContextBundle createExperiment registerExperiment createSystemCandidate actOnSystemCandidate createTask actOnTask claimTask heartbeatRun") {
					ops[op] = true
				}
				permitted = r["project"] == n.Project && (n.actor(Str(r, "principal")) || r["principal"] == a.ownerID) && ops[Str(r, "operation")]
			}
		}
		if !permitted {
			return nil, fmt.Errorf("CONTROL_PREPARATION_DELTA_REJECTED:%s:%s", d.Table, d.KeyHash)
		}
		d.Reason = "NAMED_CURRENT_SESSION_REGISTRATION_METADATA"
	}
	baseline := *n
	baseline.Rows = before
	if err = controlValidateVersionEvents(&baseline, after); err != nil {
		return nil, err
	}
	return delta, nil
}

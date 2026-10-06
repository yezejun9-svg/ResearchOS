package domain

import (
	"database/sql"
	"fmt"
	"strings"
	"unicode/utf8"
)

// Reconstruct from immutable admission and original receipts, never a session's
// current head or a worker/terminal claim. Used before PREPARED and by restore.
func providerTransport(tx *sql.Tx, project string, run, dispatch Object) (Object, error) {
	m, _ := dispatch["manifest"].(map[string]any)
	a, _ := m["admission"].(map[string]any)
	p, _ := a["profile"].(map[string]any)
	config, _ := p["model_config"].(map[string]any)
	policy, err := providerPolicy(config)
	if err != nil || !policy {
		return nil, err
	}
	if err = validateRuntimeModelConfig(p); err != nil {
		return nil, err
	}
	if m["project_id"] != project || m["run_id"] != run["id"] || m["task_id"] != run["task_id"] || m["runtime_id"] != run["runtime_id"] || Hash(m) != dispatch["manifest_hash"] || !providerPolicyEndpoint(Str(config, "endpoint"), a["mode"] == "FIXTURE") {
		return nil, historyInvalid("provider original admission binding")
	}
	ref, ok := a["profile_ref"].(map[string]any)
	if !ok || a["profile_hash"] != Hash(ref) {
		return nil, historyInvalid("provider profile reference")
	}
	artifact, err := version(tx, project, ref)
	if err != nil {
		return nil, err
	}
	profile, err := runtimeProfileBody(tx, project, artifact)
	if err != nil || Hash(profile) != Hash(p) {
		return nil, historyInvalid("provider immutable profile")
	}
	kind, id := "session", ""
	var witness Object
	if a["qualification_bootstrap"] == true {
		kind, id = "qualification_task", Str(m, "task_id")
		var taskRun, runtime, planHash, profileHash, contractHash, inputHash, contextID, owner string
		var epoch int64
		err = tx.QueryRow(`SELECT run,runtime,epoch,plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root FROM runtime_qualification_runs WHERE project=? AND task=?`, project, id).Scan(&taskRun, &runtime, &epoch, &planHash, &profileHash, &contractHash, &inputHash, &contextID, &owner)
		if err != nil {
			return nil, err
		}
		plan, digest, root, e := qualificationPlan(tx, project, id, runtime)
		if e != nil {
			return nil, e
		}
		task, e := load(tx, project, "Task", id)
		if e != nil {
			return nil, e
		}
		if task["task_type"] != "runtime_qualification" || taskRun != run["id"] || runtime != m["runtime_id"] || Hash(epoch) != Hash(m["epoch"]) || planHash != digest || owner != root || profileHash != Hash(ref) || Hash(plan["profile_ref"]) != Hash(ref) || contractHash != m["contract_hash"] || inputHash != Hash(m["input_refs"]) || contextID != m["context_bundle_id"] || plan["task_hash"] != qualificationTaskHash(task) {
			return nil, historyInvalid("provider original qualification witness")
		}
		witness = Object{"plan_hash": planHash, "contract_hash": contractHash, "input_hash": inputHash, "context_bundle": contextID, "owner_root": owner}
	} else {
		var generation, session string
		var count int
		if err = tx.QueryRow(`SELECT count(*) FROM client_queue_fences WHERE project=? AND run_id=? AND runtime_epoch=?`, project, run["id"], m["epoch"]).Scan(&count); err != nil {
			return nil, err
		}
		if count != 1 {
			return nil, historyInvalid("provider unique original session")
		}
		if err = tx.QueryRow(`SELECT generation,session_id FROM client_queue_fences WHERE project=? AND task_id=? AND run_id=? AND runtime_epoch=? AND dispatch_key=? AND manifest_hash=?`, project, m["task_id"], run["id"], m["epoch"], dispatch["dispatch_key"], dispatch["manifest_hash"]).Scan(&generation, &session); err != nil {
			return nil, err
		}
		if err = tx.QueryRow(`SELECT count(*) FROM client_sessions WHERE project_id=? AND id=?`, project, session).Scan(&count); err != nil {
			return nil, err
		}
		if count != 1 {
			return nil, historyInvalid("provider session project")
		}
		binding := Object{"project_id": project, "session_id": session, "task_id": m["task_id"], "run_id": run["id"], "runtime_epoch": m["epoch"], "queue_generation": generation, "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "process_identity": dispatch["identity"]}
		read := func(receiptID, kind string) (Object, string, error) {
			var raw, hash string
			if e := tx.QueryRow(`SELECT body,body_hash FROM client_control_receipts WHERE project=? AND generation=? AND receipt_id=? AND kind=?`, project, generation, receiptID, kind).Scan(&raw, &hash); e != nil {
				return nil, "", e
			}
			v, e := Decode([]byte(raw))
			if e != nil || Digest([]byte(raw)) != hash {
				return nil, "", historyInvalid("provider receipt hash")
			}
			for key, want := range binding {
				if Hash(v[key]) != Hash(want) {
					return nil, "", historyInvalid("provider receipt identity")
				}
			}
			return v, hash, nil
		}
		deliveredID := Str(dispatch, "dispatch_key") + ":initialize-delivered"
		delivered, dh, e := read(deliveredID, "command.initialize.delivered")
		if e != nil {
			return nil, e
		}
		seq, e := Num(delivered, "initialization_sequence")
		if e != nil || seq < 1 || delivered["delivered"] != true {
			return nil, historyInvalid("provider delivered initialization")
		}
		acceptedID := fmt.Sprintf("%s:%d", dispatch["dispatch_key"], seq)
		accepted, ah, e := read(acceptedID, "command.accepted")
		if e != nil {
			return nil, e
		}
		if accepted["initialized"] != true {
			return nil, historyInvalid("provider initialization acceptance")
		}
		if err = tx.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE project=? AND generation=? AND kind='command.accepted' AND json_extract(body,'$.initialized')=1`, project, generation).Scan(&count); err != nil {
			return nil, err
		}
		if count != 1 {
			return nil, historyInvalid("provider ambiguous initialization")
		}
		id = session
		witness = Object{"session_id": session, "queue_generation": generation, "initialization_sequence": seq, "initialized_receipt_id": acceptedID, "initialized_receipt_body_hash": ah, "delivered_receipt_id": deliveredID, "delivered_receipt_body_hash": dh}
	}
	scope := Object{"kind": kind, "project_id": project, "id": id}
	value := "ros-v1-" + strings.TrimPrefix(Hash(Merge(Merge(Object{}, scope), Object{"version": "researchos-opencode-session-v1"})), "sha256:")
	authority := Object{"kind": kind, "project_id": project, "task_id": m["task_id"], "run_id": run["id"], "runtime_id": m["runtime_id"], "runtime_epoch": m["epoch"], "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "profile_ref_hash": Hash(ref), "model_config_hash": Hash(config), "witness": witness}
	return Object{"version": "researchos.provider-transport.v1", "provider_policy": runtimeProviderPolicy, "endpoint": config["endpoint"], "user_agent": "ResearchOS/2.4", "session_header": "x-opencode-session", "session_value": value, "affinity_scope": scope, "authority": authority}, nil
}

// Resolve the effect's historical Run identity, not the current Run after a
// lease takeover or runtime replacement. Status-only revisions may repeat it.
func providerOriginalRun(tx *sql.Tx, project, runID string, effect Object) (Object, error) {
	epoch, err := Num(effect, "epoch")
	if err != nil || epoch < 1 {
		return nil, historyInvalid("provider original Run epoch invalid")
	}
	rows, err := tx.Query(`SELECT body FROM domain_versions WHERE project=? AND kind='Run' AND id=? AND json_extract(body,'$.lease_epoch')=? ORDER BY revision`, project, runID, epoch)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var original Object
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			return nil, err
		}
		run, e := Decode([]byte(raw))
		if e != nil || run["project_id"] != project || run["id"] != runID || run["task_id"] != effect["task_id"] || Str(run, "runtime_id") == "" || Hash(run["lease_epoch"]) != Hash(effect["epoch"]) {
			return nil, historyInvalid("provider original Run identity")
		}
		if original != nil {
			for _, key := range []string{"task_id", "runtime_id", "created_at", "executor_principal_id"} {
				if Hash(original[key]) != Hash(run[key]) {
					return nil, historyInvalid("provider ambiguous original Run epoch")
				}
			}
		} else {
			original = run
		}
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	if original == nil {
		return nil, historyInvalid("provider original Run epoch unavailable")
	}
	return original, nil
}

// A binding is independently keyed by the original Run's runtime. Its absence
// is not proof of legacy: callers still require positive original admission.
// These tables prevent UPDATE, not DELETE; every required link is checked.
func providerOriginalProfile(tx *sql.Tx, project string, run Object) (Object, Object, string, error) {
	var raw, digest, technical string
	err := tx.QueryRow(`SELECT profile_ref,profile_hash,technical_hash FROM runtime_bindings WHERE project=? AND runtime=?`, project, run["runtime_id"]).Scan(&raw, &digest, &technical)
	if err == sql.ErrNoRows {
		return nil, nil, "", nil
	}
	if err != nil {
		return nil, nil, "", err
	}
	ref, err := Decode([]byte(raw))
	if err != nil || ref["entity_type"] != "Artifact" || Hash(ref) != digest {
		return nil, nil, "", historyInvalid("provider frozen binding reference")
	}
	artifact, err := version(tx, project, ref)
	if err != nil {
		return nil, nil, "", err
	}
	profile, err := runtimeProfileBody(tx, project, artifact)
	if err != nil {
		return nil, nil, "", err
	}
	if profile["runtime_id"] != run["runtime_id"] || profile["technical_hash"] != technical || artifact["project_id"] != project || artifact["id"] != ref["id"] || Hash(artifact["revision"]) != Hash(ref["revision"]) {
		return nil, nil, "", historyInvalid("provider frozen binding identity")
	}
	return ref, profile, technical, nil
}

// Follow the original persisted relationship revision, never today's head.
func providerHistoricalRelation(tx *sql.Tx, project, kind string, owner Object, field, targetKind, targetID string) (Object, error) {
	revision, err := Num(owner, "revision")
	if err != nil {
		return nil, historyInvalid("provider historical relation owner")
	}
	rows, err := tx.Query(`SELECT r.target_project,r.target_kind,r.target_id,r.target_revision,v.body FROM domain_refs r JOIN domain_versions v ON v.project=r.target_project AND v.kind=r.target_kind AND v.id=r.target_id AND v.revision=r.target_revision WHERE r.project=? AND r.kind=? AND r.id=? AND r.revision=? AND r.field=?`, project, kind, owner["id"], revision, field)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var result Object
	for rows.Next() {
		var p, k, id, raw string
		var rev int64
		if err = rows.Scan(&p, &k, &id, &rev, &raw); err != nil {
			return nil, err
		}
		v, e := Decode([]byte(raw))
		allowedProject := p == project || (p == "" && targetKind == "BudgetPolicy")
		if e != nil || result != nil || !allowedProject || k != targetKind || id != targetID || Str(v, "project_id") != p || v["id"] != id || Hash(v["revision"]) != Hash(rev) {
			return nil, historyInvalid("provider historical relation identity")
		}
		result = v
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	if result == nil {
		return nil, historyInvalid("provider historical relation missing")
	}
	return result, nil
}

func providerOriginalReservation(tx *sql.Tx, project string, run Object, id string) (Object, error) {
	var raw, digest, historicalRaw, historicalDigest string
	var revision, immutable int64
	err := tx.QueryRow(`SELECT o.body,o.revision,o.content_hash,o.immutable,v.body,v.content_hash FROM domain_objects o JOIN domain_versions v ON v.project=o.project AND v.kind=o.kind AND v.id=o.id AND v.revision=o.revision WHERE o.project=? AND o.kind='BudgetLedgerEntry' AND o.id=?`, project, id).Scan(&raw, &revision, &digest, &immutable, &historicalRaw, &historicalDigest)
	if err != nil {
		return nil, historyInvalid("provider original reservation unavailable")
	}
	ledger, err := Decode([]byte(raw))
	historical, he := Decode([]byte(historicalRaw))
	if err != nil || he != nil || immutable != 1 || revision != 1 || ledger["project_id"] != project || ledger["id"] != id || Hash(ledger["revision"]) != Hash(revision) || ledger["receipt_hash"] != digest || Receipt(ledger) != digest || historicalDigest != digest || Hash(historical) != Hash(ledger) {
		return nil, historyInvalid("provider original reservation immutable identity")
	}
	boundRun, err := providerHistoricalRelation(tx, project, "BudgetLedgerEntry", ledger, "/run_id", "Run", Str(run, "id"))
	if err != nil {
		return nil, err
	}
	for _, field := range []string{"id", "task_id", "runtime_id", "lease_epoch", "created_at", "executor_principal_id"} {
		if Hash(boundRun[field]) != Hash(run[field]) {
			return nil, historyInvalid("provider reservation original Run")
		}
	}
	task, err := providerHistoricalRelation(tx, project, "Run", boundRun, "/task_id", "Task", Str(run, "task_id"))
	if err != nil {
		return nil, err
	}
	goal, err := providerHistoricalRelation(tx, project, "Task", task, "/goal_id", "Goal", Str(task, "goal_id"))
	if err != nil {
		return nil, err
	}
	if ledger["policy_id"] != goal["budget_policy_id"] || ledger["run_id"] != run["id"] {
		return nil, historyInvalid("provider reservation original budget policy")
	}
	if _, err = providerHistoricalRelation(tx, project, "Goal", goal, "/budget_policy_id", "BudgetPolicy", Str(ledger, "policy_id")); err != nil {
		return nil, err
	}
	if _, err = providerHistoricalRelation(tx, project, "BudgetLedgerEntry", ledger, "/policy_id", "BudgetPolicy", Str(ledger, "policy_id")); err != nil {
		return nil, err
	}
	return ledger, nil
}

// Every original MODEL reservation must still have its own PREPARED chain.
// This also finds erased/aliased effects when no request marker survives.
func providerReconcileReservations(tx *sql.Tx, project, runID string, prepared map[string][]Object) error {
	rows, err := tx.Query(`SELECT project,id,body FROM domain_objects WHERE kind='BudgetLedgerEntry' AND (?='' OR project=?) AND (?='' OR json_extract(body,'$.run_id')=?) AND json_extract(body,'$.operation')='RESERVE' AND instr(json_extract(body,'$.provider_request_id'),':model:')>0 AND substr(json_extract(body,'$.provider_event_id'),1,8)='prepare/'`, project, project, runID, runID)
	if err != nil {
		return err
	}
	items := []Object{}
	for rows.Next() {
		var p, id, raw string
		if err = rows.Scan(&p, &id, &raw); err != nil {
			rows.Close()
			return err
		}
		v, e := Decode([]byte(raw))
		if e != nil || v["project_id"] != p || v["id"] != id {
			rows.Close()
			return historyInvalid("provider original MODEL reservation identity")
		}
		items = append(items, v)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, ledger := range items {
		p, r, key := Str(ledger, "project_id"), Str(ledger, "run_id"), Str(ledger, "provider_request_id")
		parts := strings.Split(key, ":")
		var epoch, ordinal int64
		if len(parts) != 5 || parts[1] != r || parts[3] != "model" {
			return historyInvalid("provider original MODEL reservation key")
		}
		if _, err = fmt.Sscan(parts[2], &epoch); err != nil || epoch < 1 || parts[2] != fmt.Sprint(epoch) {
			return historyInvalid("provider original MODEL reservation epoch")
		}
		if _, err = fmt.Sscan(parts[4], &ordinal); err != nil || ordinal < 1 || parts[4] != fmt.Sprint(ordinal) {
			return historyInvalid("provider original MODEL reservation ordinal")
		}
		run, e := providerOriginalRun(tx, p, r, Object{"task_id": parts[0], "epoch": epoch})
		if e != nil {
			return e
		}
		_, profile, _, e := providerOriginalProfile(tx, p, run)
		if e != nil {
			return e
		}
		config, _ := profile["model_config"].(map[string]any)
		policy, e := providerPolicy(config)
		if e != nil {
			return e
		}
		if !policy {
			// Individual effects still need positive nonpolicy admission.
			// Missing bindings cannot justify an erased original MODEL hold.
			if profile == nil {
				return historyInvalid("provider original MODEL reservation provenance")
			}
			continue
		}
		if _, e = providerOriginalReservation(tx, p, run, Str(ledger, "id")); e != nil {
			return e
		}
		facts := prepared[p+"/"+r+"/"+key]
		if len(facts) != 1 || facts[0]["state"] != "PREPARED" || facts[0]["reservation_id"] != ledger["id"] {
			return historyInvalid("provider unmatched original MODEL reservation")
		}
	}
	return nil
}

func providerTypedEffectProof(tx *sql.Tx, project string, run, profile, effect Object) (string, error) {
	ledger, err := providerOriginalReservation(tx, project, run, Str(effect, "reservation_id"))
	if err != nil {
		return "", err
	}
	key := Str(effect, "key")
	if ledger["provider_request_id"] != key {
		return "", historyInvalid("provider reservation original effect key")
	}
	request, _ := effect["payload"].(map[string]any)
	capability := Str(request, "capability")
	if capability != "MODEL" && capability != "TOOL" {
		return "", historyInvalid("provider original typed capability")
	}
	prefix := fmt.Sprintf("%s:%s:%v:%s:", run["task_id"], run["id"], run["lease_epoch"], strings.ToLower(capability))
	var ordinal int64
	if !strings.HasPrefix(key, prefix) {
		return "", historyInvalid("provider original typed key")
	}
	if _, err = fmt.Sscan(strings.TrimPrefix(key, prefix), &ordinal); err != nil || ordinal < 1 || key != prefix+fmt.Sprint(ordinal) {
		return "", historyInvalid("provider original typed ordinal")
	}
	found := 0
	var bound any
	for _, v := range Arr(profile, "effect_routes") {
		route, _ := v.(map[string]any)
		if route["id"] == request["route"] && route["capability"] == capability && route["credential_revision"] == request["credential_revision"] {
			found++
			bound = route["upper_bound"]
		}
	}
	if found != 1 || bound == nil {
		return "", historyInvalid("provider ambiguous original typed route")
	}
	cost := Object{}
	for _, field := range []string{"policy_id", "run_id", "operation", "money", "provider_request_id", "provider_event_id", "reservation_id", "cost_basis", "occurred_at"} {
		v, ok := ledger[field]
		if !ok {
			return "", historyInvalid("provider original cost field missing")
		}
		cost[field] = v
	}
	if cost["operation"] != "RESERVE" || cost["cost_basis"] != "UPPER_BOUND" || cost["provider_event_id"] != "prepare/"+key || cost["reservation_id"] != nil || cost["occurred_at"] != run["created_at"] || Hash(cost["money"]) != Hash(bound) || effect["request_hash"] != Hash([]any{request, cost}) {
		return "", historyInvalid("provider original request and complete cost")
	}
	if capability == "TOOL" && (!modelExactKeys(request, "route", "capability", "credential_revision", "payload") || request["provider_transport"] != nil) {
		return "", historyInvalid("provider original TOOL request")
	}
	return capability, nil
}

// Every original MODEL is classified before examining removable transport or
// dispatch markers. Successful empty inventory requires proven nonpolicy.
func validateProviderInventory(tx *sql.Tx, project, runID string) (map[string]Object, error) {
	rows, err := tx.Query(`SELECT project,run,effect_key,sequence,body FROM resource_effects WHERE (?='' OR project=?) AND (?='' OR run=?) ORDER BY project,run,effect_key,sequence`, project, project, runID, runID)
	if err != nil {
		return nil, err
	}
	type record struct {
		project, run, key string
		sequence          int64
		body              Object
	}
	all := []record{}
	prepared := map[string][]Object{}
	for rows.Next() {
		var p, r, key, raw string
		var seq int64
		if err = rows.Scan(&p, &r, &key, &seq, &raw); err != nil {
			rows.Close()
			return nil, err
		}
		v, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		if v["project_id"] != p || v["run_id"] != r || v["key"] != key || Hash(v["sequence"]) != Hash(seq) || seq < 1 {
			rows.Close()
			return nil, historyInvalid("provider effect SQL identity")
		}
		if seq == 1 {
			group := p + "/" + r + "/" + key
			prepared[group] = append(prepared[group], v)
		}
		all = append(all, record{p, r, key, seq, v})
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	if err = providerReconcileReservations(tx, project, runID, prepared); err != nil {
		return nil, err
	}
	transports := map[string]Object{}
	originals := map[string]Object{}
	sequences := map[string]int64{}
	for _, record := range all {
		e := record.body
		if e["project_id"] != record.project || e["run_id"] != record.run || e["key"] != record.key || Hash(e["sequence"]) != Hash(record.sequence) || record.sequence < 1 {
			return nil, historyInvalid("provider effect SQL identity")
		}
		run, err := providerOriginalRun(tx, record.project, record.run, e)
		if err != nil {
			return nil, err
		}
		ref, frozen, technical, err := providerOriginalProfile(tx, record.project, run)
		if err != nil {
			return nil, err
		}
		config, _ := frozen["model_config"].(map[string]any)
		policy, err := providerPolicy(config)
		if err != nil {
			return nil, err
		}
		request, _ := e["payload"].(map[string]any)
		key := record.key
		modelKey := fmt.Sprintf("%s:%s:%v:model:", run["task_id"], record.run, run["lease_epoch"])
		modelEffect := request["capability"] == "MODEL" || strings.HasPrefix(key, modelKey) || request["provider_transport"] != nil
		// On a policy Run even a claimed TOOL needs original reservation
		// proof. Route IDs are intentionally shared across capabilities.
		if !modelEffect && !policy {
			continue
		}
		d, err := runtimeDispatch(tx, record.project, record.run, e["epoch"])
		if err == sql.ErrNoRows {
			// Old generic fixture claims stored no RuntimeRegistration ref.
			// A later fixture flag/current registration cannot supply that
			// missing temporal proof. Keep this compatibility gap explicit.
			return nil, historyInvalid("provider original MODEL dispatch or legacy provenance unavailable")
		}
		if err != nil {
			return nil, err
		}
		m, _ := d["manifest"].(map[string]any)
		a, _ := m["admission"].(map[string]any)
		p, _ := a["profile"].(map[string]any)
		runtimeRef, ok := a["runtime_ref"].(map[string]any)
		if !ok || runtimeRef["entity_type"] != "RuntimeRegistration" || runtimeRef["id"] != run["runtime_id"] || m["task_id"] != run["task_id"] || m["runtime_id"] != run["runtime_id"] || m["executor_principal_id"] != run["executor_principal_id"] || ref == nil || Hash(a["profile_ref"]) != Hash(ref) || a["profile_hash"] != Hash(ref) || Hash(p) != Hash(frozen) || a["technical_hash"] != technical {
			return nil, historyInvalid("provider original admission provenance")
		}
		runtime, err := version(tx, record.project, runtimeRef)
		if err != nil {
			return nil, err
		}
		if runtime["project_id"] != record.project || runtime["id"] != run["runtime_id"] || Hash(Ref(runtime, "RuntimeRegistration")) != Hash(runtimeRef) || runtimeTechnicalHash(runtime) != technical || a["mode"] != runtime["measurement_mode"] {
			return nil, historyInvalid("provider original runtime revision")
		}
		if !policy {
			if request["provider_transport"] != nil {
				return nil, historyInvalid("provider transport without original policy")
			}
			continue
		}
		capability, err := providerTypedEffectProof(tx, record.project, run, p, e)
		if err != nil {
			return nil, err
		}
		seq, err := Num(e, "sequence")
		if err != nil {
			return nil, err
		}
		group := record.project + "/" + record.run + "/" + key
		if seq != sequences[group]+1 || e["project_id"] != record.project || e["run_id"] != record.run || e["task_id"] != m["task_id"] || Hash(e["epoch"]) != Hash(m["epoch"]) {
			return nil, historyInvalid("provider effect sequence or identity")
		}
		sequences[group] = seq
		if seq == 1 {
			if e["state"] != "PREPARED" {
				return nil, historyInvalid("provider missing PREPARED")
			}
			originals[group] = e
		} else {
			old := originals[group]
			if old == nil || Hash(old["payload"]) != Hash(request) || old["request_hash"] != e["request_hash"] || old["reservation_id"] != e["reservation_id"] {
				return nil, historyInvalid("provider history rebound")
			}
		}
		if capability == "TOOL" {
			if e["state"] != "PREPARED" && e["state"] != "STARTED" && e["state"] != "UNKNOWN" && e["state"] != "NOT_APPLIED" && e["state"] != "CONFIRMED" {
				return nil, historyInvalid("provider invalid effect state")
			}
			continue
		}
		var ordinal int64
		if !strings.HasPrefix(key, modelKey) {
			return nil, historyInvalid("provider original MODEL key")
		}
		if _, err = fmt.Sscan(strings.TrimPrefix(key, modelKey), &ordinal); err != nil || ordinal < 1 || key != modelKey+fmt.Sprint(ordinal) {
			return nil, historyInvalid("provider original MODEL ordinal")
		}
		transport, err := providerTransport(tx, record.project, run, d)
		if err != nil {
			return nil, err
		}
		if request["capability"] != "MODEL" || !modelExactKeys(request, "route", "capability", "credential_revision", "payload", "provider_transport") || Hash(request["provider_transport"]) != Hash(transport) {
			return nil, historyInvalid("provider original transport")
		}
		payload, _ := request["payload"].(map[string]any)
		if _, err = validateRuntimeModelRequest(config, payload); err != nil {
			return nil, err
		}
		var bound any
		found := 0
		for _, value := range Arr(p, "effect_routes") {
			r, _ := value.(map[string]any)
			if r["id"] == request["route"] && r["capability"] == "MODEL" && r["credential_revision"] == request["credential_revision"] {
				bound = r["upper_bound"]
				found++
			}
		}
		if found != 1 || bound == nil {
			return nil, historyInvalid("provider monetary route")
		}
		ledger, err := load(tx, record.project, "BudgetLedgerEntry", Str(e, "reservation_id"))
		if err != nil {
			return nil, err
		}
		cost := Object{"policy_id": ledger["policy_id"], "run_id": record.run, "operation": "RESERVE", "money": bound, "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": run["created_at"]}
		if e["request_hash"] != Hash([]any{request, cost}) || ledger["run_id"] != record.run || ledger["provider_request_id"] != key || ledger["operation"] != "RESERVE" || ledger["cost_basis"] != "UPPER_BOUND" || Hash(ledger["money"]) != Hash(bound) {
			return nil, historyInvalid("provider original request and budget hash")
		}
		transports[key] = transport
		switch e["state"] {
		case "PREPARED", "STARTED", "UNKNOWN", "NOT_APPLIED":
		case "CONFIRMED":
			receipt, _ := e["receipt"].(map[string]any)
			payload, _ := receipt["payload"].(map[string]any)
			raw := Str(payload, "body")
			if receipt["state"] != "CONFIRMED" || receipt["key"] != key || receipt["run_id"] != record.run || Hash(receipt["epoch"]) != Hash(m["epoch"]) || receipt["model_transport"] != true || receipt["actual_cost"] != nil || receipt["receipt_id"] != Digest([]byte(raw)) || payload["content_type"] != "text/event-stream" || Hash(payload["status"]) != Hash(200) || len(raw) > modelStreamMaxRaw || !completeRuntimeModelSSE([]byte(raw)) || providerSSEPolicy([]byte(raw)) != nil {
				return nil, historyInvalid("provider original sealed response")
			}
			var settled int
			if err = tx.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.provider_request_id')=? AND (json_extract(body,'$.cost_basis')='ACTUAL' OR json_extract(body,'$.operation') IN ('RELEASE','RECONCILE'))`, record.project, record.run, key).Scan(&settled); err != nil {
				return nil, err
			}
			if settled != 0 {
				return nil, historyInvalid("provider unknown monetary cost settled")
			}
		default:
			return nil, historyInvalid("provider invalid effect state")
		}
	}
	return transports, nil
}

func providerSSEChunks(raw []byte) ([]Object, error) {
	chunks := []Object{}
	for _, event := range strings.Split(strings.ReplaceAll(string(raw), "\r\n", "\n"), "\n\n") {
		data := []string{}
		for _, line := range strings.Split(event, "\n") {
			if strings.HasPrefix(line, "data:") {
				data = append(data, strings.TrimPrefix(strings.TrimPrefix(line, "data:"), " "))
			}
		}
		text := strings.Join(data, "\n")
		if text == "" || text == "[DONE]" {
			continue
		}
		chunk, err := Decode([]byte(text))
		if err != nil {
			return nil, err
		}
		for _, v := range Arr(chunk, "choices") {
			choice, _ := v.(map[string]any)
			delta, _ := choice["delta"].(map[string]any)
			for _, key := range []string{"reasoning_details", "reasoning_signature", "signature"} {
				if _, present := delta[key]; present {
					return nil, historyInvalid("unsupported provider reasoning alternative")
				}
			}
			for _, v := range Arr(delta, "tool_calls") {
				call, _ := v.(map[string]any)
				if call["thoughtSignature"] != nil || call["custom"] != nil {
					return nil, historyInvalid("unsupported provider tool alternative")
				}
			}
		}
		chunks = append(chunks, chunk)
	}
	return chunks, nil
}
func providerSSEPolicy(raw []byte) error { _, err := providerSSEChunks(raw); return err }

func providerReasoningParts(raw string) (string, []Object, error) {
	chunks, err := providerSSEChunks([]byte(raw))
	if err != nil {
		return "", nil, err
	}
	var normalized strings.Builder
	parts := []Object{}
	textIndex, thinkingIndex := -1, -1
	tools := map[int64]bool{}
	for _, chunk := range chunks {
		choices := Arr(chunk, "choices")
		if len(choices) > 0 {
			choice, _ := choices[0].(map[string]any)
			delta, _ := choice["delta"].(map[string]any)
			if text := Str(delta, "content"); text != "" {
				if textIndex < 0 {
					textIndex = len(parts)
					parts = append(parts, Object{"type": "text", "text": ""})
				}
				parts[textIndex]["text"] = Str(parts[textIndex], "text") + text
			}
			selected, text := "", ""
			for _, key := range []string{"reasoning_content", "reasoning", "reasoning_text"} {
				if Str(delta, key) != "" {
					selected, text = key, Str(delta, key)
					break
				}
			}
			for _, key := range []string{"reasoning_content", "reasoning", "reasoning_text"} {
				delete(delta, key)
			}
			if selected != "" {
				delta["reasoning_content"] = text
				if thinkingIndex < 0 {
					if selected == "reasoning" {
						selected = "reasoning_content"
					}
					thinkingIndex = len(parts)
					parts = append(parts, Object{"type": "thinking", "thinking": "", "thinkingSignature": selected})
				}
				parts[thinkingIndex]["thinking"] = Str(parts[thinkingIndex], "thinking") + text
			}
			for _, v := range Arr(delta, "tool_calls") {
				call, _ := v.(map[string]any)
				index, e := Num(call, "index")
				if e != nil {
					return "", nil, e
				}
				if !tools[index] {
					tools[index] = true
					parts = append(parts, Object{"type": "toolCall", "index": index})
				}
			}
		}
		fmt.Fprintf(&normalized, "data: %s\n\n", Bytes(chunk))
	}
	normalized.WriteString("data: [DONE]\n\n")
	return normalized.String(), parts, nil
}

func providerResponse(config Object, raw string) (muAssistant, error) {
	policy, err := providerPolicy(config)
	if err != nil {
		return muAssistant{}, err
	}
	if !policy {
		return muResponse(raw)
	}
	if !completeRuntimeModelSSE([]byte(raw)) {
		return muAssistant{}, historyInvalid("provider incomplete SSE")
	}
	text, _, err := providerReasoningParts(raw)
	if err != nil {
		return muAssistant{}, err
	}
	return muResponse(text)
}

func verifyProviderReasoning(raw string, message Object) error {
	_, parts, err := providerReasoningParts(raw)
	if err != nil {
		return err
	}
	actual := Arr(message, "content")
	if len(parts) != len(actual) {
		return historyInvalid("provider SDK content ordering")
	}
	for i, want := range parts {
		got, ok := actual[i].(map[string]any)
		if !ok || got["type"] != want["type"] {
			return historyInvalid("provider SDK content type ordering")
		}
		switch want["type"] {
		case "thinking":
			if got["thinking"] != want["thinking"] || got["thinkingSignature"] != want["thinkingSignature"] {
				return historyInvalid("provider SDK original reasoning signature or bytes")
			}
		case "text":
			if got["text"] != want["text"] {
				return historyInvalid("provider SDK original text")
			}
		case "toolCall":
			if got["thoughtSignature"] != nil {
				return historyInvalid("provider SDK unsupported tool signature")
			}
		}
	}
	return nil
}

func providerWireReasoning(message Object, sdk bool) (Object, error) {
	result := Object{}
	if !sdk {
		for _, key := range []string{"reasoning_content", "reasoning", "reasoning_text", "reasoning_details"} {
			if value, exists := message[key]; exists {
				if _, ok := value.(string); !ok || key == "reasoning_details" {
					return nil, historyInvalid("provider wire reasoning type")
				}
				result[key] = value
			}
		}
		return result, nil
	}
	texts := []string{}
	signature := ""
	for _, v := range Arr(message, "content") {
		part, _ := v.(map[string]any)
		if part["type"] != "thinking" {
			continue
		}
		text, ok := part["thinking"].(string)
		if !ok {
			return nil, historyInvalid("provider SDK reasoning type")
		}
		if strings.TrimSpace(text) == "" {
			continue
		}
		sig := Str(part, "thinkingSignature")
		if sig != "reasoning" && sig != "reasoning_content" && sig != "reasoning_text" {
			return nil, historyInvalid("provider SDK unsupported signature")
		}
		if len(texts) == 0 {
			signature = sig
		}
		texts = append(texts, text)
	}
	if len(texts) > 0 {
		if signature == "reasoning" {
			signature = "reasoning_content"
		}
		result[signature] = strings.Join(texts, "\n")
	}
	if _, exists := result["reasoning_content"]; !exists {
		result["reasoning_content"] = ""
	}
	return result, nil
}

func verifyProviderWireHistory(wire, sdk []any, cwd ...string) error {
	previous := []Object{}
	custom := map[string]Object{}
	for _, v := range sdk {
		m, _ := v.(map[string]any)
		if m["role"] == "assistant" {
			previous = append(previous, m)
		}
		if m["role"] == "custom" {
			d, _ := m["details"].(map[string]any)
			custom[Str(d, "command_id")] = m
		}
	}
	wh, we := providerRequestHistory(wire, cwd...)
	sh, se := muRequestHistory(sdk, true, custom)
	if we != nil || se != nil || Hash(wh) != Hash(sh) {
		return historyInvalid("provider complete original request history")
	}
	n := 0
	for _, v := range wire {
		m, _ := v.(map[string]any)
		if m["role"] != "assistant" {
			continue
		}
		if n >= len(previous) {
			return historyInvalid("provider injected assistant")
		}
		got, e := providerWireReasoning(m, false)
		want, ee := providerWireReasoning(previous[n], true)
		if e != nil || ee != nil || Hash(got) != Hash(want) {
			return historyInvalid("provider original reasoning wire history")
		}
		n++
	}
	if n != len(previous) {
		return historyInvalid("provider omitted assistant")
	}
	return nil
}

func providerRequestHistory(wire []any, cwd ...string) ([]any, error) {
	// The pinned reasoning model serializes the worker's fixed system prompt as
	// developer. This exception does not authorize arbitrary developer messages.
	const instruction = "You are the ResearchOS task worker. Use only the supplied task, context, and explicitly declared tools. Preserve relevant evidence in the final answer. Do not assume access to files, shell commands, network, or credentials."
	expected := instruction
	if len(cwd) == 1 && cwd[0] != "" {
		expected += "\n\n<cwd>\n" + cwd[0] + "\n</cwd>"
	}
	checked := make([]any, 0, len(wire))
	seen := false
	for i, v := range wire {
		m, ok := v.(map[string]any)
		if !ok {
			return nil, historyInvalid("provider message shape")
		}
		if m["role"] == "developer" || m["role"] == "system" {
			text, ok := muText(m["content"])
			if !ok || text != expected || seen || i != 0 {
				return nil, historyInvalid("provider Host instruction changed")
			}
			seen = true
			checked = append(checked, Merge(Merge(Object{}, m), Object{"role": "system"}))
			continue
		}
		checked = append(checked, m)
	}
	if len(cwd) == 1 && !seen {
		return nil, historyInvalid("provider Host instruction missing")
	}
	return muRequestHistory(checked, false)
}

func providerOriginalCWD(dispatch Object) string {
	identity, _ := dispatch["identity"].(map[string]any)
	return strings.TrimRight(strings.ReplaceAll(Str(identity, "staging_directory"), "\\", "/"), "/") + "/output"
}

// muTurnSnapshot adds immutable broker history to BOTH acceptance snapshots.
// Worker counters and SDK placeholder costs are never independent evidence.
func (s *Service) muTurnSnapshot(tx *sql.Tx, project string, task, run, contract, observation Object) (Object, error) {
	needed := false
	for _, v := range Arr(contract, "checks") {
		check, _ := v.(map[string]any)
		needed = needed || check["command_key"] == "mu.turn-output-v1"
	}
	if !needed {
		return nil, nil
	}
	if task["task_type"] != "mu_turn" && task["task_type"] != "runtime_qualification" {
		return nil, Fail(422, "GATE_FAILED", "Mu verifier requires a finite Mu turn or runtime qualification")
	}
	dispatch, err := nativeDispatchProof(tx, project, run, observation)
	if err != nil {
		return nil, err
	}
	admission, err := s.currentDispatchAdmission(tx, project, task, run, dispatch, "accept")
	if err != nil {
		return nil, err
	}
	profile, _ := admission["profile"].(map[string]any)
	if profile["backend"] != runtimeMuBackend {
		return nil, Fail(422, "GATE_FAILED", "Mu native dispatch profile required")
	}
	if err = validateRuntimeModelConfig(profile); err != nil {
		return nil, err
	}
	bundle, err := load(tx, project, "ContextBundle", Str(run, "context_bundle_id"))
	if err != nil {
		return nil, err
	}
	goal, err := load(tx, project, "Goal", Str(task, "goal_id"))
	if err != nil {
		return nil, err
	}
	request := Object{"run_id": run["id"], "task_id": task["id"], "task_type": task["task_type"], "task_title": task["title"], "task_description": goal["original_intent"], "epoch": run["lease_epoch"], "context": bundle, "input_refs": run["input_refs"], "checkpoint_artifact_id": run["checkpoint_artifact_id"], "artifact_inputs": Empty()}
	attachments := Empty()
	for _, v := range Arr(run, "input_refs") {
		ref, _ := v.(map[string]any)
		if ref["entity_type"] != "Artifact" {
			continue
		}
		a, err := version(tx, project, ref)
		if err != nil {
			return nil, err
		}
		var raw []byte
		if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&raw); err != nil {
			return nil, err
		}
		if Digest(raw) != a["content_hash"] || !utf8.Valid(raw) {
			return nil, Fail(422, "GATE_FAILED", "Mu input artifact seal or UTF-8 mismatch")
		}
		if Hash(ref) == Hash(admission["profile_ref"]) {
			continue // Host control input stays hash-bound, never user prompt text.
		}
		request["artifact_inputs"] = append(Arr(request, "artifact_inputs"), Object{"id": a["id"], "content_hash": a["content_hash"], "media_type": a["media_type"], "path": "artifacts/" + Str(a, "id")})
		attachments = append(attachments, Object{"id": a["id"], "content_hash": a["content_hash"], "media_type": a["media_type"], "text": string(raw)})
	}
	prompt := Merge(request, Object{"attachments": attachments})
	history, ledger := Empty(), Empty()
	rows, err := tx.Query("SELECT rowid,body FROM resource_effects WHERE project=? AND run=? ORDER BY effect_key,sequence", project, run["id"])
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var raw string
		var position int64
		if err = rows.Scan(&position, &raw); err != nil {
			rows.Close()
			return nil, err
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		// Local append order is read from SQLite, never accepted from a worker.
		// It proves MODEL -> TOOL -> MODEL ordering without trusting wall time.
		o["_journal_position"] = position
		history = append(history, o)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	rows, err = tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? ORDER BY id", project, run["id"])
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return nil, err
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		ledger = append(ledger, o)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	snapshot := Object{"dispatch": dispatch, "profile": profile, "request": request, "prompt": prompt, "effects": history, "ledger": ledger}
	if policy, _ := providerPolicy(profile["model_config"].(map[string]any)); policy {
		transports, e := validateProviderInventory(tx, project, Str(run, "id"))
		if e != nil {
			return nil, e
		}
		snapshot["provider_transports"] = transports
	}
	stream, err := s.modelStreamAcceptanceSnapshot(tx, project, run)
	if err != nil {
		return nil, err
	}
	if stream != nil {
		snapshot["model_stream"] = stream
	}
	return snapshot, nil
}

type muAssistant struct {
	Text, Thinking, Stop string
	Calls                []Object
}

// Parse the broker's bounded original SSE, independently of the SDK artifact.
func muResponse(raw string) (muAssistant, error) {
	result := muAssistant{Calls: []Object{}}
	if !completeRuntimeModelSSE([]byte(raw)) {
		return result, fmt.Errorf("incomplete model SSE")
	}
	calls := map[int64]Object{}
	for _, event := range strings.Split(strings.ReplaceAll(raw, "\r\n", "\n"), "\n\n") {
		data := []string{}
		for _, line := range strings.Split(event, "\n") {
			if strings.HasPrefix(line, "data:") {
				data = append(data, strings.TrimPrefix(strings.TrimPrefix(line, "data:"), " "))
			}
		}
		payload := strings.Join(data, "\n")
		if payload == "" || payload == "[DONE]" {
			continue
		}
		chunk, err := Decode([]byte(payload))
		if err != nil || chunk["error"] != nil {
			return result, fmt.Errorf("model error or malformed SSE")
		}
		choices := Arr(chunk, "choices")
		if len(choices) == 0 {
			continue
		}
		if len(choices) != 1 {
			return result, fmt.Errorf("multiple model choices")
		}
		choice, ok := choices[0].(map[string]any)
		if !ok {
			return result, fmt.Errorf("malformed choice")
		}
		index, err := Num(choice, "index")
		if err != nil || index != 0 {
			return result, fmt.Errorf("unexpected model choice")
		}
		delta, _ := choice["delta"].(map[string]any)
		if result.Stop != "" && (len(delta) > 0 || choice["finish_reason"] != nil) {
			return result, fmt.Errorf("data after model finish")
		}
		if delta["role"] != nil && delta["role"] != "assistant" {
			return result, fmt.Errorf("invalid response role")
		}
		for _, key := range []string{"content", "reasoning_content", "reasoning", "reasoning_text"} {
			if delta[key] != nil {
				if _, ok := delta[key].(string); !ok {
					return result, fmt.Errorf("nontext model delta")
				}
			}
		}
		result.Text += Str(delta, "content")
		for _, key := range []string{"reasoning_content", "reasoning", "reasoning_text"} {
			result.Thinking += Str(delta, key)
		}
		if delta["refusal"] != nil || delta["function_call"] != nil {
			return result, fmt.Errorf("unsupported refusal or legacy call")
		}
		for _, v := range Arr(delta, "tool_calls") {
			part, ok := v.(map[string]any)
			if !ok {
				return result, fmt.Errorf("malformed tool delta")
			}
			n, err := Num(part, "index")
			if err != nil || n < 0 || n > 31 {
				return result, fmt.Errorf("invalid tool index")
			}
			call := calls[n]
			if call == nil {
				call = Object{"id": "", "name": "", "arguments": ""}
				calls[n] = call
			}
			if part["type"] != nil && part["type"] != "function" {
				return result, fmt.Errorf("unsupported tool type")
			}
			if id := Str(part, "id"); id != "" {
				if Str(call, "id") != "" && call["id"] != id {
					return result, fmt.Errorf("tool ID changed")
				}
				call["id"] = id
			}
			fn, _ := part["function"].(map[string]any)
			call["name"] = Str(call, "name") + Str(fn, "name")
			call["arguments"] = Str(call, "arguments") + Str(fn, "arguments")
		}
		if stop := Str(choice, "finish_reason"); stop != "" {
			result.Stop = stop
		}
	}
	if result.Stop != "stop" && result.Stop != "tool_calls" {
		return result, fmt.Errorf("model did not finish successfully")
	}
	for n := int64(0); n < int64(len(calls)); n++ {
		call := calls[n]
		if call == nil || Str(call, "id") == "" || Str(call, "name") == "" {
			return result, fmt.Errorf("incomplete tool call")
		}
		args, err := Decode([]byte(Str(call, "arguments")))
		if err != nil {
			return result, err
		}
		call["arguments"] = args
		result.Calls = append(result.Calls, call)
	}
	if (result.Stop == "tool_calls") != (len(result.Calls) > 0) {
		return result, fmt.Errorf("tool finish mismatch")
	}
	return result, nil
}

func muSDKAssistant(message Object) (muAssistant, error) {
	r := muAssistant{Calls: []Object{}, Stop: Str(message, "stopReason")}
	if r.Stop == "toolUse" {
		r.Stop = "tool_calls"
	}
	for _, v := range Arr(message, "content") {
		part, ok := v.(map[string]any)
		if !ok {
			return r, fmt.Errorf("malformed SDK content")
		}
		switch part["type"] {
		case "text":
			r.Text += Str(part, "text")
		case "thinking":
			r.Thinking += Str(part, "thinking")
		case "toolCall":
			r.Calls = append(r.Calls, Object{"id": part["id"], "name": part["name"], "arguments": part["arguments"]})
		default:
			return r, fmt.Errorf("unsupported SDK content")
		}
	}
	return r, nil
}

func muText(content any) (string, bool) {
	if s, ok := content.(string); ok {
		return s, true
	}
	parts, ok := content.([]any)
	if !ok {
		return "", false
	}
	text := ""
	for _, v := range parts {
		p, ok := v.(map[string]any)
		if !ok || p["type"] != "text" {
			return "", false
		}
		s, ok := p["text"].(string)
		if !ok {
			return "", false
		}
		text += s
	}
	return text, true
}

// Compare semantic request history without depending on SDK timestamps, usage
// placeholders or provider-specific optional serialization fields.
func muRequestHistory(messages []any, sdk bool, authorizedCustom ...map[string]Object) ([]any, error) {
	result := Empty()
	for _, v := range messages {
		m, ok := v.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("malformed message")
		}
		role := Str(m, "role")
		if role == "system" {
			continue
		}
		switch role {
		case "custom":
			details, _ := m["details"].(map[string]any)
			if !sdk || len(authorizedCustom) != 1 || m["customType"] != "researchos.command.v1" || Hash(authorizedCustom[0][Str(details, "command_id")]) != Hash(m) {
				return nil, fmt.Errorf("unverified custom message")
			}
			text, ok := muText(m["content"])
			if !ok {
				return nil, fmt.Errorf("nontext custom message")
			}
			result = append(result, Object{"role": "user", "text": text})
		case "user":
			text, ok := muText(m["content"])
			if !ok {
				return nil, fmt.Errorf("nontext user input")
			}
			result = append(result, Object{"role": "user", "text": text})
		case "assistant":
			text := ""
			calls := []Object{}
			if sdk {
				a, err := muSDKAssistant(m)
				if err != nil {
					return nil, err
				}
				text = a.Text
				calls = a.Calls
			} else {
				if m["content"] != nil {
					var ok bool
					text, ok = muText(m["content"])
					if !ok {
						return nil, fmt.Errorf("nontext assistant")
					}
				}
				for _, v := range Arr(m, "tool_calls") {
					c, ok := v.(map[string]any)
					if !ok || c["type"] != "function" {
						return nil, fmt.Errorf("invalid wire tool call")
					}
					fn, _ := c["function"].(map[string]any)
					args, err := Decode([]byte(Str(fn, "arguments")))
					if err != nil {
						return nil, err
					}
					calls = append(calls, Object{"id": c["id"], "name": fn["name"], "arguments": args})
				}
			}
			result = append(result, Object{"role": "assistant", "text": text, "calls": calls})
		case "tool", "toolResult":
			text, ok := muText(m["content"])
			if !ok {
				return nil, fmt.Errorf("nontext tool result")
			}
			id := m["tool_call_id"]
			if sdk {
				id = m["toolCallId"]
				parts := []string{}
				for _, v := range Arr(m, "content") {
					p, _ := v.(map[string]any)
					parts = append(parts, Str(p, "text"))
				}
				text = strings.Join(parts, "\n")
				if text == "" {
					text = "(no tool output)"
				}
			}
			result = append(result, Object{"role": "tool", "id": id, "text": text})
		default:
			return nil, fmt.Errorf("unsupported role")
		}
	}
	return result, nil
}

// verifyMuTurn proves only execution of this finite turn, not correctness of
// business claims or repairs described by an assistant.
func verifyMuTurn(snapshot Object) (string, string) {
	fail := func(reason string) (string, string) { return "FAIL", reason }
	mu, _ := snapshot["mu_turn"].(map[string]any)
	if mu == nil {
		return fail("Mu native evidence snapshot missing.")
	}
	task, _ := snapshot["task"].(map[string]any)
	run, _ := snapshot["run"].(map[string]any)
	profile, _ := mu["profile"].(map[string]any)
	config, _ := profile["model_config"].(map[string]any)
	artifacts := Arr(snapshot, "artifacts")
	if len(artifacts) != 1 {
		return fail("One sealed SDK result required.")
	}
	entry, _ := artifacts[0].(map[string]any)
	raw, ok := entry["bytes"].([]byte)
	if !ok {
		return fail("SDK result bytes missing.")
	}
	result, err := Decode(raw)
	if err != nil || result["task_id"] != task["id"] || result["run_id"] != run["id"] || Hash(result["epoch"]) != Hash(run["lease_epoch"]) || result["model_ref"] != config["ref"] || result["model"] != config["model"] || result["actual_cost"] != nil || result["sdk_cost_is_placeholder"] != true {
		return fail("SDK result identity, model or cost binding mismatch.")
	}
	histories := map[string][]Object{}
	for _, v := range Arr(mu, "effects") {
		e, ok := v.(map[string]any)
		if !ok {
			return fail("Malformed effect history.")
		}
		histories[Str(e, "key")] = append(histories[Str(e, "key")], e)
	}
	models, tools := map[int64]Object{}, map[int64]Object{}
	for key, history := range histories {
		if len(history) < 3 || history[0]["state"] != "PREPARED" || history[1]["state"] != "STARTED" {
			return fail("Effect lacks prepared and started broker facts.")
		}
		e := history[len(history)-1]
		receipt, _ := e["receipt"].(map[string]any)
		request, _ := e["payload"].(map[string]any)
		if policy, _ := providerPolicy(config); policy && request["capability"] == "MODEL" {
			transports, _ := mu["provider_transports"].(map[string]Object)
			var expected any = transports[key]
			if decoded, ok := mu["provider_transports"].(map[string]any); ok {
				expected = decoded[key]
			}
			if expected == nil || Hash(expected) != Hash(request["provider_transport"]) {
				return fail("Provider original canonical transport missing or changed.")
			}
		}
		if e["state"] != "CONFIRMED" || receipt["state"] != "CONFIRMED" || e["project_id"] != task["project_id"] || e["task_id"] != task["id"] || e["run_id"] != run["id"] || Hash(e["epoch"]) != Hash(run["lease_epoch"]) || e["context_bundle_id"] != run["context_bundle_id"] || receipt["run_id"] != run["id"] || receipt["key"] != key || Hash(receipt["epoch"]) != Hash(run["lease_epoch"]) {
			return fail("Every effect must be confirmed for this exact run and epoch.")
		}
		for i, h := range history {
			n, _ := Num(h, "sequence")
			if n != int64(i+1) || h["request_hash"] != e["request_hash"] || Hash(h["payload"]) != Hash(request) || h["reservation_id"] != e["reservation_id"] || h["epoch"] == nil || Hash(h["epoch"]) != Hash(e["epoch"]) {
				return fail("Effect history binding changed.")
			}
		}
		capability := Str(request, "capability")
		prefix := fmt.Sprintf("%s:%s:%v:%s:", task["id"], run["id"], run["lease_epoch"], strings.ToLower(capability))
		var ordinal int64
		if !strings.HasPrefix(key, prefix) {
			return fail("Effect logical key mismatch.")
		}
		if _, err = fmt.Sscan(strings.TrimPrefix(key, prefix), &ordinal); err != nil || ordinal < 1 || key != prefix+fmt.Sprint(ordinal) {
			return fail("Invalid effect ordinal.")
		}
		bound := false
		var routeBound any
		for _, v := range Arr(profile, "effect_routes") {
			route, _ := v.(map[string]any)
			if route["id"] == request["route"] && route["capability"] == capability && route["credential_revision"] == request["credential_revision"] {
				bound = true
				routeBound = route["upper_bound"]
			}
		}
		if !bound || request["route"] != config["route"] {
			return fail("Effect route differs from frozen profile.")
		}
		var reservation Object
		for _, v := range Arr(mu, "ledger") {
			l, _ := v.(map[string]any)
			if l["id"] == e["reservation_id"] {
				reservation = l
			}
			if capability == "MODEL" && receipt["actual_cost"] == nil && l["provider_request_id"] == key && (l["cost_basis"] == "ACTUAL" || l["operation"] == "RELEASE" || l["operation"] == "RECONCILE") {
				return fail("Unknown model money was settled or released.")
			}
		}
		if reservation == nil || reservation["run_id"] != run["id"] || reservation["provider_request_id"] != key || reservation["operation"] != "RESERVE" || reservation["cost_basis"] != "UPPER_BOUND" {
			return fail("Bounded durable effect reservation missing.")
		}
		cost := Object{"policy_id": reservation["policy_id"], "run_id": run["id"], "operation": "RESERVE", "money": reservation["money"], "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": run["created_at"]}
		if Hash(reservation["money"]) != Hash(routeBound) || e["request_hash"] != Hash([]any{request, cost}) {
			return fail("Effect request or reserved bound differs from immutable admission.")
		}
		switch capability {
		case "MODEL":
			if receipt["model_transport"] != true || receipt["actual_cost"] != nil {
				return fail("Model transport must retain unknown monetary cost.")
			}
			models[ordinal] = e
		case "TOOL":
			if task["task_type"] == "runtime_qualification" {
				return fail("Qualification cannot execute tools.")
			}
			money, ok := receipt["actual_cost"].(map[string]any)
			amount, moneyErr := moneyAmount(money)
			if !ok || moneyErr != nil || amount.Sign() != 0 || Hash(receipt["actual_cost"]) != Hash(routeBound) {
				return fail("Host tool monetary receipt differs from its zero bound.")
			}
			tools[ordinal] = e
		default:
			return fail("Unrecognized effect capability.")
		}
	}
	max, _ := Num(config, "max_calls")
	if task["task_type"] == "runtime_qualification" {
		q, _ := profile["model_qualification"].(map[string]any)
		max, _ = Num(q, "max_calls")
	}
	if len(models) < 1 || int64(len(models)) > max {
		return fail("Model call count violates frozen bounds.")
	}
	mc, mcErr := Num(result, "model_calls")
	tc, tcErr := Num(result, "tool_calls")
	if mcErr != nil || tcErr != nil || mc != int64(len(models)) || tc != int64(len(tools)) {
		return fail("Worker counts differ from broker facts.")
	}
	stream, streaming := mu["model_stream"].(map[string]any)
	customAllowed := map[string]Object{}
	canonicalCommands := map[string]Object{}
	if mu["model_stream"] != nil && !streaming {
		return fail("Malformed canonical streaming proof.")
	}
	if streaming {
		bindings := Arr(stream, "bindings")
		if len(bindings) != len(models) {
			return fail("Canonical stream/model membership mismatch.")
		}
		for i, value := range bindings {
			b, ok := value.(map[string]any)
			effect := models[int64(i+1)]
			if !ok || b["run_id"] != run["id"] || b["task_id"] != task["id"] || Hash(b["runtime_epoch"]) != Hash(run["lease_epoch"]) || b["effect_key"] != effect["key"] || b["request_hash"] != effect["request_hash"] {
				return fail("Canonical stream effect binding mismatch.")
			}
		}
		for _, value := range Arr(stream, "commands") {
			cmd, ok := value.(map[string]any)
			if !ok {
				return fail("Invalid canonical consumption.")
			}
			id := Str(cmd, "command_id")
			rec, _ := cmd["consumption"].(map[string]any)
			if id == "" || canonicalCommands[id] != nil || cmd["state"] != "CONSUMED" || cmd["content_hash"] != Digest([]byte(Str(cmd, "content"))) || cmd["consumption_hash"] != Digest(Bytes(rec)) || rec["command_id"] != id || rec["message_id"] != cmd["message_id"] || rec["content_hash"] != cmd["content_hash"] || rec["run_id"] != run["id"] {
				return fail("Canonical command consumption binding mismatch.")
			}
			canonicalCommands[id] = cmd
		}
	}
	messages := Arr(result, "messages")
	consumeCustom := func(cursor *int) error {
		for *cursor < len(messages) {
			m, ok := messages[*cursor].(map[string]any)
			if !ok {
				return fmt.Errorf("SDK message shape")
			}
			if m["role"] != "custom" {
				break
			}
			details, _ := m["details"].(map[string]any)
			id := Str(details, "command_id")
			cmd := canonicalCommands[id]
			if !streaming || cmd == nil || customAllowed[id] != nil || m["customType"] != "researchos.command.v1" || Hash(cmd["sdk_position"]) != Hash(*cursor) {
				return fmt.Errorf("SDK custom consumption order")
			}
			rec, _ := cmd["consumption"].(map[string]any)
			expected := Object{"command_id": id, "queue_generation": rec["queue_generation"], "queue_sequence": cmd["queue_sequence"], "content_hash": cmd["content_hash"]}
			if Hash(details) != Hash(expected) {
				return fmt.Errorf("SDK command identity")
			}
			content, e := Decode([]byte(Str(cmd, "content")))
			if e != nil {
				return e
			}
			parts := []any{Object{"type": "text", "text": content["text"]}}
			for _, v := range Arr(content, "attachments") {
				a, ok := v.(map[string]any)
				if !ok {
					return fmt.Errorf("command attachment")
				}
				parts = append(parts, Object{"type": "text", "text": a["text"]})
			}
			if Hash(parts) != Hash(m["content"]) {
				return fmt.Errorf("SDK command content")
			}
			customAllowed[id] = m
			*cursor++
		}
		return nil
	}
	cursor := 0
	for cursor < len(messages) {
		m, _ := messages[cursor].(map[string]any)
		if m["role"] != "system" {
			break
		}
		cursor++
	}
	if cursor >= len(messages) {
		return fail("SDK user input missing.")
	}
	user, _ := messages[cursor].(map[string]any)
	text, valid := muText(user["content"])
	prompt, e := Decode([]byte(text))
	if !valid || e != nil || user["role"] != "user" || Hash(prompt) != Hash(mu["prompt"]) {
		return fail("SDK prompt differs from frozen task inputs.")
	}
	cursor++
	toolOrdinal := int64(0)
	usedIDs := map[string]bool{}
	lastPosition := int64(0)
	ordered := func(effect Object, after int64) (int64, bool) {
		history := histories[Str(effect, "key")]
		if len(history) == 0 {
			return 0, false
		}
		for _, fact := range history {
			pos, err := Num(fact, "_journal_position")
			if err != nil || pos <= after {
				return 0, false
			}
			after = pos
		}
		return after, true
	}
	previousStop := ""
	for n := int64(1); n <= int64(len(models)); n++ {
		priorCustom := len(customAllowed)
		if err := consumeCustom(&cursor); err != nil {
			return fail(err.Error())
		}
		if n > 1 && previousStop == "stop" && len(customAllowed) == priorCustom {
			return fail("Intermediate stop lacks actual consumed next input.")
		}
		e := models[n]
		modelEnd, orderedModel := ordered(e, lastPosition)
		if e == nil || !orderedModel {
			return fail("Missing model call.")
		}
		lastPosition = modelEnd
		request, _ := e["payload"].(map[string]any)
		payload, _ := request["payload"].(map[string]any)
		body, err := validateRuntimeModelRequest(config, payload)
		if err != nil {
			return fail("Broker model request differs from frozen configuration.")
		}
		providerMessages := Arr(body, "messages")
		wireHistory, wireErr := muRequestHistory(providerMessages, false)
		if policy, _ := providerPolicy(config); policy {
			wireHistory, wireErr = providerRequestHistory(providerMessages, providerOriginalCWD(mu["dispatch"].(map[string]any)))
		}
		sdkHistory, sdkErr := muRequestHistory(messages[:cursor], true, customAllowed)
		if wireErr != nil || sdkErr != nil || Hash(wireHistory) != Hash(sdkHistory) {
			return fail("Broker request history differs from preceding confirmed SDK messages.")
		}
		if policy, _ := providerPolicy(config); policy {
			if e := verifyProviderWireHistory(providerMessages, messages[:cursor], providerOriginalCWD(mu["dispatch"].(map[string]any))); e != nil {
				return fail(e.Error())
			}
		}
		found := false
		for _, v := range providerMessages {
			m, _ := v.(map[string]any)
			if m["role"] == "user" {
				input, ok := muText(m["content"])
				p, err := Decode([]byte(input))
				if !ok {
					return fail("Broker user input changed.")
				}
				if err == nil && Hash(p) == Hash(prompt) {
					if found {
						return fail("Duplicate broker task prompt.")
					}
					found = true
				} else if !streaming {
					return fail("Broker user input changed.")
				}
				// Streaming extra users are already matched, in full order, to
				// the canonical consumed SDK custom messages by wireHistory.
			}
		}
		if !found {
			return fail("Broker request omitted task inputs.")
		}
		receipt, _ := e["receipt"].(map[string]any)
		response, _ := receipt["payload"].(map[string]any)
		status, _ := Num(response, "status")
		responseRaw := Str(response, "body")
		if status != 200 || response["content_type"] != "text/event-stream" || receipt["receipt_id"] != Digest([]byte(responseRaw)) {
			return fail("Broker model response seal mismatch.")
		}
		expected, err := providerResponse(config, responseRaw)
		if err != nil {
			return fail("Broker model response: " + err.Error())
		}
		if cursor >= len(messages) {
			return fail("SDK omitted model response.")
		}
		message, _ := messages[cursor].(map[string]any)
		actual, err := muSDKAssistant(message)
		if policy, _ := providerPolicy(config); policy {
			if e := verifyProviderReasoning(responseRaw, message); e != nil {
				return fail(e.Error())
			}
		}
		if err != nil || message["role"] != "assistant" || message["model"] != config["model"] || message["provider"] != config["provider"] || message["api"] != config["api"] || Hash(actual) != Hash(expected) {
			return fail("SDK assistant differs from broker response.")
		}
		if message["errorMessage"] != nil || (message["rawStopReason"] != nil && message["rawStopReason"] != expected.Stop) {
			return fail("SDK assistant reports an inconsistent stop or error.")
		}
		cursor++
		for _, call := range expected.Calls {
			declared := false
			for _, v := range Arr(config, "tools") {
				definition, _ := v.(map[string]any)
				fn, _ := definition["function"].(map[string]any)
				declared = declared || fn["name"] == call["name"]
			}
			if !declared {
				return fail("Provider called an undeclared tool.")
			}
			id := Str(call, "id")
			if usedIDs[id] {
				return fail("Duplicate provider tool call ID.")
			}
			usedIDs[id] = true
			toolOrdinal++
			effect := tools[toolOrdinal]
			toolEnd, orderedTool := ordered(effect, modelEnd)
			if effect == nil || !orderedTool {
				return fail("Provider tool call lacks a confirmed host effect.")
			}
			if toolEnd > lastPosition {
				lastPosition = toolEnd
			}
			req, _ := effect["payload"].(map[string]any)
			args, _ := req["payload"].(map[string]any)
			rec, _ := effect["receipt"].(map[string]any)
			output, _ := rec["payload"].(map[string]any)
			if args["name"] != call["name"] || Hash(args["arguments"]) != Hash(call["arguments"]) || rec["host_tool"] != call["name"] || rec["receipt_id"] != Digest(Bytes(output)) {
				return fail("Host tool request or result differs from provider call.")
			}
			if cursor >= len(messages) {
				return fail("SDK tool result missing.")
			}
			m, _ := messages[cursor].(map[string]any)
			if m["role"] != "toolResult" || m["toolCallId"] != id || m["toolName"] != call["name"] || m["isError"] != false || Hash(m["content"]) != Hash(output["content"]) || Hash(m["details"]) != Hash(output["details"]) {
				return fail("SDK tool result differs from confirmed host result.")
			}
			cursor++
		}
		if !streaming && (n == int64(len(models))) != (expected.Stop == "stop") {
			return fail("Model call chain did not finish exactly once with stop.")
		}
		if streaming && n == int64(len(models)) && expected.Stop != "stop" {
			return fail("Streaming model chain did not finish with stop.")
		}
		previousStop = expected.Stop
	}
	if cursor != len(messages) || toolOrdinal != int64(len(tools)) || len(customAllowed) != len(canonicalCommands) {
		return fail("Unaccounted SDK messages or host effects.")
	}
	return "PASS", fmt.Sprintf("Verified finite Mu turn against native dispatch, sealed inputs/output and %d MODEL / %d TOOL broker receipts; model money remains unknown and reserved. No claim about semantic repair correctness.", len(models), len(tools))
}

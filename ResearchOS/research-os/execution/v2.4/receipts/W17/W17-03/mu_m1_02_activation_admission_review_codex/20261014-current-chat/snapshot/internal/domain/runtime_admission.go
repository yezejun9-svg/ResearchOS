package domain

import (
	"database/sql"
	"time"
)

// qualificationEvidence validates the private bootstrap marker against current authority.
// It cannot turn a fixture observation into a LIVE qualification.
func (s *Service) qualificationEvidence(tx *sql.Tx, project string, receipt Object, caller string) (Object, Object, Object, error) {
	ref, ok := receipt["subject_ref"].(map[string]any)
	if !ok || ref["entity_type"] != "Task" || receipt["verdict"] != "PASS" || receipt["receipt_hash"] != Receipt(receipt) || receipt["project_id"] != project {
		return nil, nil, nil, Fail(422, "GATE_FAILED", "PASS task acceptance receipt required")
	}
	t, e := load(tx, project, "Task", Str(ref, "id"))
	if e != nil {
		return nil, nil, nil, e
	}
	if t["task_type"] != "runtime_qualification" || t["status"] != "ACCEPTED" || t["acceptance_id"] != receipt["id"] {
		return nil, nil, nil, Fail(422, "GATE_FAILED", "receipt is not an accepted runtime qualification task")
	}
	subject, e := version(tx, project, ref)
	if e != nil {
		return nil, nil, nil, e
	}
	if subject["status"] != "EXECUTION_REPORTED" || qualificationTaskHash(subject) != qualificationTaskHash(t) {
		return nil, nil, nil, Fail(412, "STALE_INPUT", "receipt subject differs from accepted task")
	}
	checks := map[string]bool{}
	for _, item := range Arr(receipt, "checks") {
		check, ok := item.(map[string]any)
		if !ok || check["status"] != "PASS" || checks[Str(check, "check_id")] {
			return nil, nil, nil, Fail(422, "GATE_FAILED", "qualification checks incomplete")
		}
		checks[Str(check, "check_id")] = true
	}
	for _, item := range Arr(t["acceptance_contract"].(map[string]any), "checks") {
		check := item.(map[string]any)
		if check["required"] == true && !checks[Str(check, "check_id")] {
			return nil, nil, nil, Fail(422, "GATE_FAILED", "required qualification check absent")
		}
	}
	r, e := load(tx, project, "Run", Str(receipt, "run_id"))
	if e != nil {
		return nil, nil, nil, e
	}
	var runID, runtimeID, planHash, profileHash, contractHash, inputHash, contextID, ownerRoot string
	var epoch int64
	if e = tx.QueryRow("SELECT run,runtime,epoch,plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root FROM runtime_qualification_runs WHERE project=? AND task=?", project, t["id"]).Scan(&runID, &runtimeID, &epoch, &planHash, &profileHash, &contractHash, &inputHash, &contextID, &ownerRoot); e != nil {
		return nil, nil, nil, Fail(422, "GATE_FAILED", "trusted qualification marker absent")
	}
	plan, digest, root, e := qualificationPlan(tx, project, Str(t, "id"), runtimeID)
	if e != nil {
		return nil, nil, nil, e
	}
	if digest != planHash || root != ownerRoot || r["id"] != runID || t["active_run_id"] != runID || r["runtime_id"] != runtimeID || r["task_id"] != t["id"] || r["status"] != "SETTLED" || r["children_stopped"] != true || r["queue_empty"] != true || Hash(r["lease_epoch"]) != Hash(epoch) || contractHash != receipt["contract_hash"] || contractHash != t["acceptance_contract"].(map[string]any)["contract_hash"] || inputHash != Hash(t["input_refs"]) || inputHash != Hash(receipt["input_refs"]) || contextID != t["context_bundle_id"] || contextID != r["context_bundle_id"] || Hash(r["result_artifact_ids"]) != Hash(t["output_artifact_ids"]) {
		return nil, nil, nil, Fail(412, "STALE_INPUT", "qualification run or task binding changed")
	}
	if e = s.taskContext(tx, project, t); e != nil {
		return nil, nil, nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, nil, nil, e
	}
	if Hash(receipt["policy_revision"]) != Hash(state["policy_revision"]) || len(Arr(t, "blocking_conflict_ids"))+len(Arr(state, "blocking_conflict_ids")) != 0 {
		return nil, nil, nil, Fail(412, "STALE_INPUT", "qualification policy or conflicts changed")
	}
	if _, e = s.runDependenciesCurrent(tx, project, t, r); e != nil {
		return nil, nil, nil, e
	}
	if e = effectsReconciled(tx, project, runID); e != nil {
		return nil, nil, nil, e
	}
	refs := Empty()
	for _, v := range Arr(t, "output_artifact_ids") {
		a, _, err := s.artifactUse(tx, project, r, v.(string), true)
		if err != nil {
			return nil, nil, nil, err
		}
		if err = s.requireCurrentArtifactBody(tx, project, a); err != nil {
			return nil, nil, nil, err
		}
		refs = append(refs, Ref(a, "Artifact"))
	}
	if len(refs) == 0 || Hash(refs) != Hash(receipt["artifact_refs"]) {
		return nil, nil, nil, Fail(422, "GATE_FAILED", "accepted output vector changed")
	}
	for _, v := range append(Arr(t, "input_refs"), Arr(t, "requirement_refs")...) {
		if e = s.effective(tx, project, v.(map[string]any)); e != nil {
			return nil, nil, nil, e
		}
	}
	rt, e := load(tx, project, "RuntimeRegistration", runtimeID)
	if e != nil {
		return nil, nil, nil, e
	}
	profileRef, profile, e := s.currentRuntimeBinding(tx, project, rt)
	if e != nil {
		return nil, nil, nil, e
	}
	profileBody, e := runtimeProfileBody(tx, project, profile)
	if e != nil {
		return nil, nil, nil, e
	}
	if Hash(profileRef) != profileHash || Hash(profileRef) != Hash(plan["profile_ref"]) {
		return nil, nil, nil, Fail(412, "STALE_INPUT", "runtime profile changed")
	}
	var author string
	if tx.QueryRow("SELECT author FROM runtime_qualification_plans WHERE project=? AND task=?", project, t["id"]).Scan(&author) != nil || !runtimeRoleAndGrant(tx, author, project, "OWNER") || !runtimeRoleAndGrant(tx, Str(receipt, "verifier_principal_id"), project, "VERIFIER") {
		return nil, nil, nil, Fail(403, "FORBIDDEN", "qualification authority revoked")
	}
	verifierRoot, e := currentAuthorityRoot(tx, Str(receipt, "verifier_principal_id"))
	if e != nil {
		return nil, nil, nil, e
	}
	executorRoot, e := currentAuthorityRoot(tx, Str(r, "executor_principal_id"))
	if e != nil {
		return nil, nil, nil, e
	}
	authorRoot, e := currentAuthorityRoot(tx, author)
	if e != nil {
		return nil, nil, nil, e
	}
	if authorRoot != ownerRoot {
		return nil, nil, nil, Fail(403, "FORBIDDEN", "qualification author authority changed")
	}
	if caller != "" {
		callerRoot, err := currentAuthorityRoot(tx, caller)
		if err != nil {
			return nil, nil, nil, err
		}
		if callerRoot == authorRoot || callerRoot == executorRoot {
			return nil, nil, nil, Fail(403, "FORBIDDEN", "qualification caller is not independent")
		}
	}
	if verifierRoot == executorRoot || verifierRoot == authorRoot || Hash(receipt["executor_principal_ids"]) != Hash([]any{r["executor_principal_id"]}) {
		return nil, nil, nil, Fail(403, "FORBIDDEN", "qualification verifier is not independent")
	}
	created, e := time.Parse(time.RFC3339Nano, Str(receipt, "created_at"))
	valid, err := Num(plan, "max_validity_seconds")
	if e != nil || err != nil || valid <= 0 || !time.Now().Before(created.Add(time.Duration(valid)*time.Second)) {
		return nil, nil, nil, Fail(412, "STALE_INPUT", "qualification expired")
	}
	obs, e := runtimeObservation(tx, project, r)
	if e != nil {
		return nil, nil, nil, e
	}
	spec, _ := obs["spec"].(map[string]any)
	protocol, _ := obs["protocol"].(map[string]any)
	if obs["state"] != "SETTLED" || obs["children_stopped"] != true || obs["queue_empty"] != true || protocol["settled"] != true || spec["run_id"] != runID || spec["task_id"] != t["id"] || Hash(spec["epoch"]) != Hash(epoch) || spec["profile_hash"] != profileHash || spec["technical_hash"] != runtimeTechnicalHash(rt) || !runtimeProfileObserved(spec, profileBody) {
		return nil, nil, nil, Fail(422, "GATE_FAILED", "trusted host observation differs from frozen plan")
	}
	observed := map[string]bool{}
	for _, v := range Arr(spec, "capabilities") {
		if value, ok := v.(string); ok {
			observed[value] = true
		}
	}
	for _, v := range Arr(plan, "required_capabilities") {
		if !observed[v.(string)] {
			return nil, nil, nil, Fail(422, "GATE_FAILED", "frozen capability not observed")
		}
	}
	if receipt["measurement_mode"] != rt["measurement_mode"] {
		return nil, nil, nil, Fail(422, "GATE_FAILED", "evidence mode differs from runtime")
	}
	if rt["measurement_mode"] == "LIVE" {
		dispatch, err := nativeDispatchProof(tx, project, r, obs)
		if err != nil {
			return nil, nil, nil, Fail(503, "RESOURCE_UNAVAILABLE", "LIVE qualification requires bound native dispatch evidence")
		}
		admission := dispatch["manifest"].(map[string]any)["admission"].(map[string]any)
		if admission["qualification_bootstrap"] != true || admission["mode"] != "LIVE" {
			return nil, nil, nil, Fail(422, "GATE_FAILED", "LIVE qualification bootstrap identity missing")
		}
	}
	return plan, rt, r, nil
}

func (s *Service) qualifyRuntime(tx *sql.Tx, p Principal, project, runtimeID string, b Object) (Object, error) {
	if !p.HasRole("VERIFIER") || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current verifier grant required")
	}
	rt, e := load(tx, project, "RuntimeRegistration", runtimeID)
	if e != nil {
		return nil, e
	}
	if rt["status"] == "REVOKED" || rt["status"] == "UNAVAILABLE" {
		return nil, Fail(409, "STATE_CONFLICT", "runtime unavailable")
	}
	if _, _, e = s.currentRuntimeBinding(tx, project, rt); e != nil {
		return nil, e
	}
	ids := Arr(b, "qualification_ids")
	if len(ids) == 0 {
		return nil, Fail(422, "GATE_FAILED", "qualification receipt required")
	}
	seen := map[string]bool{}
	var run Object
	var plan Object
	for _, v := range ids {
		id, ok := v.(string)
		if !ok || seen[id] {
			return nil, Fail(422, "GATE_FAILED", "duplicate or invalid qualification receipt")
		}
		seen[id] = true
		receipt, err := load(tx, project, "AcceptanceReceipt", id)
		if err != nil {
			return nil, Fail(422, "GATE_FAILED", "same-project acceptance receipt required")
		}
		currentPlan, currentRuntime, currentRun, err := s.qualificationEvidence(tx, project, receipt, p.ID)
		if err != nil {
			return nil, err
		}
		if currentRuntime["id"] != runtimeID || (run != nil && run["id"] != currentRun["id"]) {
			return nil, Fail(422, "GATE_FAILED", "receipt does not qualify this runtime")
		}
		plan, run = currentPlan, currentRun
	}
	if len(ids) != 1 {
		return nil, Fail(422, "GATE_FAILED", "frozen plan requires one exact qualification receipt")
	}
	if e = s.runtimeReceipt(tx, project, run, b["receipt_artifact_ref"], mustRuntimeObservation(tx, project, run)); e != nil {
		return nil, e
	}
	if b["supports_resume"] == true {
		if Str(plan, "resume_check_id") == "" || b["resume_evidence_ref"] == nil {
			return nil, Fail(422, "GATE_FAILED", "independent resume proof required")
		}
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "S1 has no verified native resume proof")
	}
	if b["resume_evidence_ref"] != nil {
		return nil, Fail(422, "GATE_FAILED", "resume evidence without supported resume")
	}
	if e = bump(rt); e != nil {
		return nil, e
	}
	rt["status"] = "AVAILABLE"
	rt["qualification_ids"] = ids
	rt["supports_resume"] = false
	rt["resume_evidence_ref"] = nil
	rt["health_checked_at"] = Now()
	if e = s.put(tx, "RuntimeRegistration", rt); e != nil {
		return nil, e
	}
	_, e = tx.Exec("INSERT INTO runtime_qualification_approvals(project,runtime,revision,qualification_hash,run,receipt_ref,approved_at) VALUES(?,?,?,?,?,?,?)", project, runtimeID, rt["revision"], Hash(ids), run["id"], string(Bytes(b["receipt_artifact_ref"])), Now())
	return rt, e
}

func mustRuntimeObservation(tx *sql.Tx, project string, run Object) Object {
	o, _ := runtimeObservation(tx, project, run)
	return o
}

// currentRuntimeAdmission returns only current, verified authority facts.
// Legacy fixture registrations retain their old local-only path, never dispatch authority.
func (s *Service) currentRuntimeAdmission(tx *sql.Tx, project string, task, runtime Object, requestedCapabilities []any, operation string) (Object, error) {
	if runtime["measurement_mode"] == "LIVE" && len(Arr(runtime, "qualification_ids")) == 0 {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "LIVE runtime has no current qualification")
	}
	if runtime["status"] != "AVAILABLE" {
		return nil, Fail(409, "STATE_CONFLICT", "runtime not available")
	}
	current, e := load(tx, project, "RuntimeRegistration", Str(runtime, "id"))
	if e != nil {
		return nil, e
	}
	if Hash(current["revision"]) != Hash(runtime["revision"]) {
		return nil, Fail(412, "STALE_INPUT", "runtime snapshot changed")
	}
	runtime = current
	if runtime["status"] != "AVAILABLE" {
		return nil, Fail(409, "STATE_CONFLICT", "runtime not available")
	}
	if task != nil && task["project_id"] != project {
		return nil, Fail(403, "FORBIDDEN", "task belongs to another project")
	}
	if operation == "resume" && runtime["supports_resume"] != true {
		return nil, Fail(422, "GATE_FAILED", "runtime has no native resume proof")
	}
	available := map[string]bool{}
	for _, v := range Arr(runtime, "capabilities") {
		if cap, ok := v.(string); ok {
			available[cap] = true
		}
	}
	for _, v := range requestedCapabilities {
		cap, ok := v.(string)
		if !ok || !available[cap] {
			return nil, Fail(422, "GATE_FAILED", "runtime capability unavailable")
		}
	}
	if runtime["measurement_mode"] == "FIXTURE" {
		var count int
		if e := tx.QueryRow("SELECT count(*) FROM orchestration_fixtures WHERE project=? AND runtime=?", project, runtime["id"]).Scan(&count); e != nil {
			return nil, e
		}
		if count == 1 && len(Arr(runtime, "qualification_ids")) == 0 {
			return Object{"mode": "FIXTURE", "runtime_id": runtime["id"], "legacy_fixture": true}, nil
		}
	}
	if len(Arr(runtime, "qualification_ids")) != 1 {
		return nil, Fail(422, "GATE_FAILED", "exact runtime qualification required")
	}
	var runID, raw, qualificationHash string
	if e := tx.QueryRow("SELECT run,receipt_ref,qualification_hash FROM runtime_qualification_approvals WHERE project=? AND runtime=? ORDER BY revision DESC LIMIT 1", project, runtime["id"]).Scan(&runID, &raw, &qualificationHash); e != nil || qualificationHash != Hash(runtime["qualification_ids"]) {
		return nil, Fail(422, "GATE_FAILED", "current runtime approval missing")
	}
	ref, e := Decode([]byte(raw))
	if e != nil {
		return nil, Fail(422, "GATE_FAILED", "runtime approval receipt invalid")
	}
	profileRef, profileArtifact, e := s.currentRuntimeBinding(tx, project, runtime)
	if e != nil {
		return nil, e
	}
	profileBody, e := runtimeProfileBody(tx, project, profileArtifact)
	if e != nil {
		return nil, e
	}
	var expires time.Time
	evidence := Empty()
	for _, v := range Arr(runtime, "qualification_ids") {
		receipt, e := load(tx, project, "AcceptanceReceipt", v.(string))
		if e != nil {
			return nil, e
		}
		plan, rt, run, err := s.qualificationEvidence(tx, project, receipt, "")
		if err != nil || rt["id"] != runtime["id"] || run["id"] != runID {
			return nil, Fail(422, "GATE_FAILED", "current runtime qualification invalid")
		}
		observation, err := runtimeObservation(tx, project, run)
		if err != nil {
			return nil, err
		}
		planned := map[string]bool{}
		observed := map[string]bool{}
		for _, v := range Arr(plan, "required_capabilities") {
			if cap, ok := v.(string); ok {
				planned[cap] = true
			}
		}
		spec, _ := observation["spec"].(map[string]any)
		for _, v := range Arr(spec, "capabilities") {
			if cap, ok := v.(string); ok {
				observed[cap] = true
			}
		}
		for _, v := range requestedCapabilities {
			cap, _ := v.(string)
			if !planned[cap] || !observed[cap] {
				return nil, Fail(422, "GATE_FAILED", "runtime capability lacks qualified host evidence")
			}
		}
		if err = s.runtimeReceipt(tx, project, run, ref, observation); err != nil {
			return nil, err
		}
		created, err := time.Parse(time.RFC3339Nano, Str(receipt, "created_at"))
		valid, ve := Num(plan, "max_validity_seconds")
		if err != nil || ve != nil || valid <= 0 {
			return nil, Fail(422, "GATE_FAILED", "qualification lifetime invalid")
		}
		end := created.Add(time.Duration(valid) * time.Second)
		if expires.IsZero() || end.Before(expires) {
			expires = end
		}
		evidence = append(evidence, Object{"acceptance_ref": Ref(receipt, "AcceptanceReceipt"), "observation_hash": Hash(observation), "receipt_ref": ref, "plan_hash": Hash(plan), "required_capabilities": plan["required_capabilities"]})
	}
	var permission Object
	if task != nil {
		permission, e = s.currentRuntimePurpose(tx, project, task, runtime, profileRef)
		if e != nil {
			return nil, e
		}
		end, _ := time.Parse(time.RFC3339Nano, Str(permission, "expires_at"))
		if end.Before(expires) {
			expires = end
		}
	}
	return Object{"mode": runtime["measurement_mode"], "runtime_id": runtime["id"], "runtime_ref": Ref(runtime, "RuntimeRegistration"), "profile_ref": profileRef, "profile_hash": Hash(profileRef), "profile": profileBody, "technical_hash": runtimeTechnicalHash(runtime), "qualification_ids": runtime["qualification_ids"], "qualification_evidence": evidence, "permission": permission, "credential_revision": profileBody["credential_revision"], "expires_at": expires.UTC().Format(time.RFC3339Nano), "requested_capabilities": requestedCapabilities}, nil
}

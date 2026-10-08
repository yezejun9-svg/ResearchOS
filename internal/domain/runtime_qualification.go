package domain

import (
	"context"
	"database/sql"
	"strings"
	"time"
)

func runtimeTechnicalHash(r Object) string {
	return Hash([]any{r["adapter"], r["adapter_revision"], r["capabilities"], r["platform"], r["measurement_mode"], r["credential_ref"]})
}

func qualificationTaskHash(t Object) string {
	return Hash([]any{t["goal_id"], t["task_type"], t["input_refs"], t["requirement_refs"], t["context_bundle_id"], t["dependency_task_ids"], t["acceptance_contract"], t["stop_policy"]})
}

// qualificationUnlimitedPolicies is the explicit default-policy exception to
// the LIVE upper-bound reservation. It never admits a CAPPED ancestor, even an
// accounting-only one, and never reinterprets unknown cost as zero.
func qualificationUnlimitedPolicies(policies []Object) error {
	if len(policies) == 0 {
		return Fail(422, "GATE_FAILED", "active budget ancestry required")
	}
	for _, p := range policies {
		if p["mode"] != "UNLIMITED_AMOUNT" || p["cap"] != nil || p["unknown_cost_action"] != "ALLOW_AND_RECORD" {
			return Fail(422, "GATE_FAILED", "LIVE unknown cost requires unlimited active ancestry")
		}
	}
	return nil
}

func qualificationUnlimitedGoal(tx *sql.Tx, project, goalID string) error {
	goal, e := load(tx, project, "Goal", goalID)
	if e != nil {
		return e
	}
	policies, e := budgetChain(tx, project, Str(goal, "budget_policy_id"))
	if e != nil {
		return e
	}
	return qualificationUnlimitedPolicies(policies)
}

// RegisterRuntimeQualificationPlan is a trusted local host decision, not an HTTP operation.
// Its immutable profile is an ordinary sealed Artifact included in the Task inputs.
func (s *Service) RegisterRuntimeQualificationPlan(ctx context.Context, token, project, taskID, runtimeID string, profileRef Object, requiredCapabilities []any, maxValidity time.Duration, resumeCheckID string) error {
	if maxValidity <= 0 || maxValidity > 30*24*time.Hour || profileRef["entity_type"] != "Artifact" || len(requiredCapabilities) == 0 {
		return Fail(422, "GATE_FAILED", "bounded profile and capabilities required")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return e
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) {
		return Fail(403, "FORBIDDEN", "current project owner required")
	}
	t, e := load(tx, project, "Task", taskID)
	if e != nil {
		return e
	}
	r, e := load(tx, project, "RuntimeRegistration", runtimeID)
	if e != nil {
		return e
	}
	if t["status"] != "DRAFT" || t["task_type"] != "runtime_qualification" || len(Arr(t, "dependency_task_ids")) != 0 || r["status"] == "REVOKED" || r["status"] == "UNAVAILABLE" {
		return Fail(409, "STATE_CONFLICT", "qualification plan requires an eligible draft and runtime")
	}
	profile, e := version(tx, project, profileRef)
	if e != nil {
		return e
	}
	if profile["validity"] != "CURRENT" || profile["sealed_at"] == nil || profile["content_hash"] != profileRef["content_hash"] || profile["access_class"] == "VERIFIER_ONLY" {
		return Fail(422, "GATE_FAILED", "immutable sealed profile required")
	}
	if e = s.requireCurrentArtifactBody(tx, project, profile); e != nil {
		return e
	}
	profileBody, e := runtimeProfileBody(tx, project, profile)
	if e != nil {
		return e
	}
	if profileBody["runtime_id"] != runtimeID || profileBody["technical_hash"] != runtimeTechnicalHash(r) || profileBody["adapter"] != r["adapter"] || profileBody["adapter_revision"] != r["adapter_revision"] || profileBody["platform"] != r["platform"] || Str(profileBody, "build_hash") == "" || Str(profileBody, "sandbox") == "" || Str(profileBody, "credential_revision") == "" || Str(profileBody, "backend") == "" || Str(profileBody, "model") == "" {
		return Fail(422, "GATE_FAILED", "profile lacks frozen runtime identity or permission boundary")
	}
	if e = validateRuntimeModelConfig(profileBody); e != nil {
		return e
	}
	if r["measurement_mode"] == "LIVE" {
		maxCost, declared := profileBody["max_cost"]
		if !declared {
			return Fail(422, "GATE_FAILED", "LIVE qualification cost basis must be declared")
		}
		if maxCost == nil {
			if e = qualificationUnlimitedGoal(tx, project, Str(t, "goal_id")); e != nil {
				return e
			}
		} else {
			cost, err := moneyAmount(maxCost)
			if err != nil || cost.Sign() <= 0 || Str(maxCost.(map[string]any), "currency") == "" {
				return Fail(422, "GATE_FAILED", "LIVE qualification needs positive frozen cost bound")
			}
		}
	}
	found := false
	for _, v := range Arr(t, "input_refs") {
		if Hash(v) == Hash(profileRef) {
			found = true
		}
	}
	if !found {
		return Fail(422, "GATE_FAILED", "profile must be a frozen task input")
	}
	for _, v := range append(Arr(t, "input_refs"), Arr(t, "requirement_refs")...) {
		if ref, ok := v.(map[string]any); !ok || ref["entity_type"] == "RuntimeRegistration" {
			return Fail(422, "GATE_FAILED", "runtime lifecycle revision cannot be a qualification input")
		}
		if e = s.effective(tx, project, v.(map[string]any)); e != nil {
			return e
		}
	}
	known := map[string]bool{}
	for _, v := range Arr(r, "capabilities") {
		known[v.(string)] = true
	}
	for _, v := range requiredCapabilities {
		cap, ok := v.(string)
		if !ok || cap == "" || !known[cap] {
			return Fail(422, "GATE_FAILED", "plan capability outside runtime registration")
		}
		if known["required:"+cap] {
			return Fail(422, "GATE_FAILED", "duplicate plan capability")
		}
		known["required:"+cap] = true
	}
	root, e := authorityRoot(tx, p.ID)
	if e != nil {
		return e
	}
	plan := Object{"runtime_id": runtimeID, "profile_ref": profileRef, "task_hash": qualificationTaskHash(t), "required_capabilities": requiredCapabilities, "max_validity_seconds": int64(maxValidity.Seconds()), "resume_check_id": resumeCheckID}
	if permission, ok := profileBody["model_qualification"].(map[string]any); ok {
		if profileBody["backend"] != runtimeMuBackend {
			return Fail(422, "GATE_FAILED", "model qualification requires the frozen Mu backend")
		}
		plan["model_qualification"] = permission
	}
	if _, e = tx.Exec("INSERT INTO runtime_bindings(project,runtime,profile_ref,profile_hash,technical_hash,owner) VALUES(?,?,?,?,?,?)", project, runtimeID, string(Bytes(profileRef)), Hash(profileRef), runtimeTechnicalHash(r), p.ID); e != nil {
		return e
	}
	if _, e = tx.Exec("INSERT INTO runtime_qualification_plans(project,task,runtime,plan,plan_hash,author,author_root) VALUES(?,?,?,?,?,?,?)", project, taskID, runtimeID, string(Bytes(plan)), Hash(plan), p.ID, root); e != nil {
		return e
	}
	return tx.Commit()
}

func qualificationPlan(tx *sql.Tx, project, taskID, runtimeID string) (Object, string, string, error) {
	var raw, digest, root string
	if e := tx.QueryRow("SELECT plan,plan_hash,author_root FROM runtime_qualification_plans WHERE project=? AND task=? AND runtime=?", project, taskID, runtimeID).Scan(&raw, &digest, &root); e != nil {
		return nil, "", "", Fail(422, "GATE_FAILED", "trusted host qualification plan required")
	}
	p, e := Decode([]byte(raw))
	if e != nil || Hash(p) != digest {
		return nil, "", "", Fail(422, "GATE_FAILED", "frozen qualification plan changed")
	}
	return p, digest, root, nil
}

func (s *Service) currentRuntimeBinding(tx *sql.Tx, project string, rt Object) (Object, Object, error) {
	var raw, profileHash, technicalHash string
	if e := tx.QueryRow("SELECT profile_ref,profile_hash,technical_hash FROM runtime_bindings WHERE project=? AND runtime=?", project, rt["id"]).Scan(&raw, &profileHash, &technicalHash); e != nil {
		return nil, nil, Fail(422, "GATE_FAILED", "runtime has no host profile binding")
	}
	ref, e := Decode([]byte(raw))
	if e != nil || Hash(ref) != profileHash || runtimeTechnicalHash(rt) != technicalHash {
		return nil, nil, Fail(412, "STALE_INPUT", "runtime technical profile changed")
	}
	profile, e := version(tx, project, ref)
	if e != nil {
		return nil, nil, e
	}
	if profile["content_hash"] != ref["content_hash"] {
		return nil, nil, Fail(412, "STALE_INPUT", "profile changed")
	}
	if e = s.effective(tx, project, ref); e != nil {
		return nil, nil, e
	}
	profileBody, e := runtimeProfileBody(tx, project, profile)
	if e != nil {
		return nil, nil, e
	}
	if profileBody["runtime_id"] != rt["id"] || profileBody["technical_hash"] != technicalHash {
		return nil, nil, Fail(412, "STALE_INPUT", "frozen profile technical identity changed")
	}
	return ref, profile, nil
}

func runtimeProfileBody(tx *sql.Tx, project string, artifact Object) (Object, error) {
	var raw []byte
	if e := tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, artifact["storage_key"]).Scan(&raw); e != nil {
		return nil, Fail(422, "GATE_FAILED", "sealed runtime profile unavailable")
	}
	if Digest(raw) != artifact["content_hash"] {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "runtime profile bytes changed")
	}
	profile, e := Decode(raw)
	if e != nil {
		return nil, Fail(422, "GATE_FAILED", "runtime profile is not JSON")
	}
	return profile, nil
}

func runtimeProfileObserved(spec, profile Object) bool {
	for _, field := range []string{"build_hash", "backend", "model", "sandbox", "platform", "adapter", "adapter_revision", "credential_revision"} {
		if Str(profile, field) == "" || spec[field] != profile[field] {
			return false
		}
	}
	return true
}

func (s *Service) reserveQualificationDispatch(tx *sql.Tx, project string, run, runtime Object) error {
	_, profile, e := s.currentRuntimeBinding(tx, project, runtime)
	if e != nil {
		return e
	}
	profileBody, e := runtimeProfileBody(tx, project, profile)
	if e != nil {
		return e
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return e
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return e
	}
	requestID := "qualification-dispatch/" + Str(run, "id")
	if profileBody["max_cost"] == nil {
		if runtime["measurement_mode"] != "LIVE" {
			return Fail(422, "GATE_FAILED", "LIVE unknown cost path required")
		}
		policies, _, err := runBudgetScopes(tx, project, Str(run, "id"))
		if err != nil {
			return err
		}
		if err = qualificationUnlimitedPolicies(policies); err != nil {
			return err
		}
		// The actual MODEL effect records UNKNOWN/money=nil in brokerEffect.
		// Do not create a second unresolved qualification-dispatch liability.
		return nil
	}
	cost, e := moneyAmount(profileBody["max_cost"])
	if e != nil || cost.Sign() <= 0 {
		return Fail(422, "GATE_FAILED", "LIVE qualification cost bound missing")
	}
	_, e = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "RESERVE", "money": profileBody["max_cost"], "provider_request_id": requestID, "provider_event_id": requestID, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()})
	return e
}

func (s *Service) releaseQualificationReservation(tx *sql.Tx, project string, run Object) error {
	requestID := "qualification-dispatch/" + Str(run, "id")
	var raw string
	e := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id')=? AND json_extract(body,'$.operation')='RESERVE'", project, requestID).Scan(&raw)
	if e == sql.ErrNoRows {
		return nil
	}
	if e != nil {
		return e
	}
	reserve, e := Decode([]byte(raw))
	if e != nil {
		return e
	}
	var settled int
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id')=? AND json_extract(body,'$.operation') IN ('RELEASE','COMMIT','RECONCILE')", project, requestID).Scan(&settled); e != nil {
		return e
	}
	if settled != 0 {
		return nil
	}
	money := reserve["money"].(map[string]any)
	_, e = s.appendBudget(tx, project, Object{"policy_id": reserve["policy_id"], "run_id": run["id"], "operation": "RELEASE", "money": Object{"amount": "0", "currency": money["currency"]}, "provider_request_id": requestID, "provider_event_id": requestID + "/released", "reservation_id": reserve["id"], "cost_basis": "ACTUAL", "occurred_at": Now()})
	return e
}

func (s *Service) beginRuntimeQualification(tx *sql.Tx, p Principal, project, taskID, runtimeID, executor string) (Object, string, error) {
	t, e := load(tx, project, "Task", taskID)
	if e != nil {
		return nil, "", e
	}
	if t["status"] != "DRAFT" || t["task_type"] != "runtime_qualification" || len(Arr(t, "dependency_task_ids")) != 0 {
		return nil, "", Fail(409, "STATE_CONFLICT", "only planned dependency-free draft qualifies")
	}
	plan, planHash, root, e := qualificationPlan(tx, project, taskID, runtimeID)
	if e != nil {
		return nil, "", e
	}
	if rootNow, err := authorityRoot(tx, p.ID); err != nil || rootNow != root {
		return nil, "", Fail(403, "FORBIDDEN", "host plan owner root changed")
	}
	if !runtimeExecutorAllowed(tx, executor, project, taskID) {
		return nil, "", Fail(403, "FORBIDDEN", "executor role or project grant revoked")
	}
	if qualificationTaskHash(t) != plan["task_hash"] {
		return nil, "", Fail(412, "STALE_INPUT", "qualification task changed after host approval")
	}
	rt, e := load(tx, project, "RuntimeRegistration", runtimeID)
	if e != nil {
		return nil, "", e
	}
	if rt["status"] == "REVOKED" || rt["status"] == "UNAVAILABLE" {
		return nil, "", Fail(409, "STATE_CONFLICT", "runtime unavailable")
	}
	ref, _, e := s.currentRuntimeBinding(tx, project, rt)
	if e != nil {
		return nil, "", e
	}
	if Hash(ref) != Hash(plan["profile_ref"]) {
		return nil, "", Fail(412, "STALE_INPUT", "qualification profile changed")
	}
	ready, e := s.orchestrateTask(tx, project, t, Object{"action": "SUBMIT"})
	if e != nil {
		return nil, "", e
	}
	if ready["status"] != "READY" {
		return nil, "", Fail(409, "STATE_CONFLICT", "qualification draft cannot become READY")
	}
	result, e := s.claimTaskMode(tx, p, project, taskID, Object{"runtime_id": runtimeID, "executor_principal_id": executor, "context_bundle_id": ready["context_bundle_id"]}, ID(), true)
	if e != nil {
		return nil, "", e
	}
	r := result["run"].(map[string]any)
	epoch, _ := Num(r, "lease_epoch")
	_, e = tx.Exec("INSERT INTO runtime_qualification_runs(project,task,run,runtime,epoch,plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root) VALUES(?,?,?,?,?,?,?,?,?,?,?)", project, taskID, r["id"], runtimeID, epoch, planHash, Hash(ref), ready["acceptance_contract"].(map[string]any)["contract_hash"], Hash(ready["input_refs"]), ready["context_bundle_id"], root)
	if e != nil {
		return nil, "", e
	}
	_, profileArtifact, e := s.currentRuntimeBinding(tx, project, rt)
	if e != nil {
		return nil, "", e
	}
	profileBody, e := runtimeProfileBody(tx, project, profileArtifact)
	if e != nil {
		return nil, "", e
	}
	if profileBody["sandbox"] == runtimeSandboxProfile {
		currentTask := result["task"].(map[string]any)
		admission, err := s.bootstrapRuntimeAdmission(tx, project, currentTask, r, rt)
		if err != nil {
			return nil, "", err
		}
		if err = s.prepareRuntimeDispatch(tx, project, currentTask, r, admission); err != nil {
			return nil, "", err
		}
	}
	return r, Str(result, "lease_token"), nil
}

func runtimeRoleAndGrant(tx *sql.Tx, id, project, role string) bool {
	var roles string
	var revoked int
	if tx.QueryRow("SELECT roles,revoked FROM auth_principals WHERE id=?", id).Scan(&roles, &revoked) != nil || revoked != 0 || !strings.Contains(roles, `"`+role+`"`) {
		return false
	}
	var grant int
	return tx.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=? AND task='' AND run=''", id, project).Scan(&grant) == nil && grant > 0
}

func runtimeExecutorAllowed(tx *sql.Tx, id, project, task string) bool {
	var roles string
	var revoked int
	if tx.QueryRow("SELECT roles,revoked FROM auth_principals WHERE id=?", id).Scan(&roles, &revoked) != nil || revoked != 0 || !strings.Contains(roles, `"EXECUTOR"`) {
		return false
	}
	var count int
	return tx.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=? AND (task='' OR task=?) AND run=''", id, project, task).Scan(&count) == nil && count > 0
}

func qualificationEffectBlocked(tx *sql.Tx, project string, task Object) error {
	var count int
	if e := tx.QueryRow("SELECT count(*) FROM runtime_qualification_runs WHERE project=? AND task=?", project, task["id"]).Scan(&count); e != nil {
		return e
	}
	if count != 0 {
		return Fail(503, "RESOURCE_UNAVAILABLE", "S1 qualification marker has no provider dispatch authority")
	}
	return nil
}

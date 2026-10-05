package domain

import (
	"database/sql"
	"path/filepath"
	"time"
)

const runtimeSandboxProfile = "appcontainer-zero-capabilities-v1"
const runtimeBridgeRevision = "windows-appcontainer-v1"

func validateRuntimeDispatchProfile(profile Object) error {
	if e := validateRuntimeModelConfig(profile); e != nil {
		return e
	}
	if profile["sandbox"] != runtimeSandboxProfile || profile["adapter_revision"] != runtimeBridgeRevision || profile["platform"] != "windows-amd64" || Str(profile, "command_id") == "" || Str(profile, "build_hash") == "" {
		return Fail(503, "RESOURCE_UNAVAILABLE", "runtime profile has no supported AppContainer command binding")
	}
	permissions, ok := profile["permissions"].(map[string]any)
	if !ok || len(Arr(permissions, "capabilities")) != 0 || permissions["network"] != "none" || permissions["environment"] != "staging-only" || Hash(permissions["process_limit"]) != Hash(1) || Hash(permissions["memory_mib"]) != Hash(256) {
		return Fail(422, "GATE_FAILED", "unsupported task permission profile")
	}
	seconds, e := Num(profile, "timeout_seconds")
	if e != nil || seconds <= 0 || seconds > 300 {
		return Fail(422, "GATE_FAILED", "bounded native timeout required")
	}
	seen := map[string]bool{}
	if len(Arr(profile, "outputs")) == 0 || len(Arr(profile, "outputs")) > 16 {
		return Fail(422, "GATE_FAILED", "bounded output manifest required")
	}
	for _, v := range Arr(profile, "outputs") {
		path, ok := v.(string)
		if !ok || !filepath.IsLocal(path) || seen[path] {
			return Fail(422, "GATE_FAILED", "unique local output paths required")
		}
		seen[path] = true
	}
	for _, v := range Arr(profile, "argv") {
		if _, ok := v.(string); !ok {
			return Fail(422, "GATE_FAILED", "frozen argument vector required")
		}
	}
	return nil
}

func (s *Service) bootstrapRuntimeAdmission(tx *sql.Tx, project string, task, run, runtime Object) (Object, error) {
	plan, planHash, root, e := qualificationPlan(tx, project, Str(task, "id"), Str(runtime, "id"))
	if e != nil {
		return nil, e
	}
	var storedRun, author string
	var epoch int64
	if e = tx.QueryRow("SELECT run,epoch FROM runtime_qualification_runs WHERE project=? AND task=?", project, task["id"]).Scan(&storedRun, &epoch); e != nil || storedRun != run["id"] || Hash(epoch) != Hash(run["lease_epoch"]) {
		return nil, Fail(422, "GATE_FAILED", "exact qualification dispatch marker required")
	}
	if e = tx.QueryRow("SELECT author FROM runtime_qualification_plans WHERE project=? AND task=?", project, task["id"]).Scan(&author); e != nil {
		return nil, e
	}
	ownerRoot, e := authorityRoot(tx, author)
	if e != nil || ownerRoot != root || !runtimeRoleAndGrant(tx, author, project, "OWNER") || !runtimeExecutorAllowed(tx, Str(run, "executor_principal_id"), project, Str(task, "id")) {
		return nil, Fail(403, "FORBIDDEN", "qualification dispatch authority revoked")
	}
	if plan["task_hash"] != qualificationTaskHash(task) || runtime["status"] == "REVOKED" || runtime["status"] == "UNAVAILABLE" {
		return nil, Fail(412, "STALE_INPUT", "qualification dispatch inputs changed")
	}
	ref, artifact, e := s.currentRuntimeBinding(tx, project, runtime)
	if e != nil {
		return nil, e
	}
	profile, e := runtimeProfileBody(tx, project, artifact)
	if e != nil {
		return nil, e
	}
	if Hash(ref) != Hash(plan["profile_ref"]) {
		return nil, Fail(412, "STALE_INPUT", "qualification dispatch profile changed")
	}
	created, e := time.Parse(time.RFC3339Nano, Str(run, "created_at"))
	if e != nil {
		return nil, e
	}
	valid, e := Num(plan, "max_validity_seconds")
	if e != nil {
		return nil, e
	}
	expires := created.Add(time.Duration(valid) * time.Second)
	if !expires.After(time.Now()) {
		return nil, Fail(412, "STALE_INPUT", "qualification dispatch plan expired")
	}
	return Object{"mode": runtime["measurement_mode"], "runtime_id": runtime["id"], "runtime_ref": Ref(runtime, "RuntimeRegistration"), "profile_ref": ref, "profile_hash": Hash(ref), "profile": profile, "technical_hash": runtimeTechnicalHash(runtime), "qualification_ids": Empty(), "qualification_evidence": Empty(), "permission": Object{"purpose": "runtime_qualification", "authorized_by": author, "author_root": root, "plan_hash": planHash}, "credential_revision": profile["credential_revision"], "expires_at": expires.UTC().Format(time.RFC3339Nano), "requested_capabilities": plan["required_capabilities"], "qualification_bootstrap": true}, nil
}

func (s *Service) prepareRuntimeDispatch(tx *sql.Tx, project string, task, run, admission Object) error {
	profile, ok := admission["profile"].(map[string]any)
	if !ok {
		return Fail(422, "GATE_FAILED", "verified admission snapshot required")
	}
	if e := validateRuntimeDispatchProfile(profile); e != nil {
		return e
	}
	manifest := Object{"version": 1, "project_id": project, "run_id": run["id"], "task_id": task["id"], "epoch": run["lease_epoch"], "runtime_id": run["runtime_id"], "executor_principal_id": run["executor_principal_id"], "contract_hash": task["acceptance_contract"].(map[string]any)["contract_hash"], "input_refs": run["input_refs"], "context_bundle_id": run["context_bundle_id"], "checkpoint_artifact_id": run["checkpoint_artifact_id"], "admission": admission}
	key := ID()
	manifest["dispatch_key"] = key
	_, e := tx.Exec("INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at) VALUES(?,?,?,?,?,?,'PREPARED',?,?)", project, run["id"], run["lease_epoch"], key, string(Bytes(manifest)), Hash(manifest), Now(), Now())
	return e
}

func runtimeDispatch(tx *sql.Tx, project, run string, epoch any) (Object, error) {
	var key, manifest, digest, state, worker, locator, identity, observation, reason string
	var sequence int64
	e := tx.QueryRow("SELECT dispatch_key,manifest,manifest_hash,state,worker,journal_locator,identity,observation_sequence,observation_hash,reason FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?", project, run, epoch).Scan(&key, &manifest, &digest, &state, &worker, &locator, &identity, &sequence, &observation, &reason)
	if e != nil {
		return nil, e
	}
	m, e := Decode([]byte(manifest))
	if e != nil || Hash(m) != digest || m["dispatch_key"] != key || m["run_id"] != run || m["project_id"] != project || Hash(m["epoch"]) != Hash(epoch) {
		return nil, Fail(422, "GATE_FAILED", "immutable dispatch manifest mismatch")
	}
	id, e := Decode([]byte(identity))
	if e != nil {
		return nil, e
	}
	return Object{"dispatch_key": key, "manifest": m, "manifest_hash": digest, "state": state, "worker": worker, "journal_locator": locator, "identity": id, "observation_sequence": sequence, "observation_hash": observation, "reason": reason}, nil
}

// currentDispatchAdmission rechecks authority without granting a fresh launch.
func (s *Service) currentDispatchAdmission(tx *sql.Tx, project string, task, run, dispatch Object, operation string) (Object, error) {
	manifest := dispatch["manifest"].(map[string]any)
	if manifest["task_id"] != task["id"] || manifest["runtime_id"] != run["runtime_id"] || manifest["executor_principal_id"] != run["executor_principal_id"] || Hash(manifest["epoch"]) != Hash(run["lease_epoch"]) || manifest["context_bundle_id"] != run["context_bundle_id"] || Hash(manifest["input_refs"]) != Hash(run["input_refs"]) || manifest["contract_hash"] != task["acceptance_contract"].(map[string]any)["contract_hash"] {
		return nil, Fail(412, "STALE_INPUT", "dispatch no longer binds current Run")
	}
	if !runtimeExecutorAllowed(tx, Str(run, "executor_principal_id"), project, Str(task, "id")) {
		return nil, Fail(403, "FORBIDDEN", "executor dispatch role or grant revoked")
	}
	runtime, e := load(tx, project, "RuntimeRegistration", Str(run, "runtime_id"))
	if e != nil {
		return nil, e
	}
	prior := manifest["admission"].(map[string]any)
	var admission Object
	if prior["qualification_bootstrap"] == true {
		admission, e = s.bootstrapRuntimeAdmission(tx, project, task, run, runtime)
	} else {
		admission, e = s.currentRuntimeAdmission(tx, project, task, runtime, Arr(prior, "requested_capabilities"), operation)
	}
	if e != nil {
		return nil, e
	}
	// Runtime health/lifecycle revisions are not a technical identity. Every
	// profile, permission, qualification proof and expiry fact remains exact.
	for _, key := range []string{"mode", "profile_hash", "profile", "technical_hash", "qualification_ids", "qualification_evidence", "permission", "credential_revision", "expires_at", "requested_capabilities", "qualification_bootstrap"} {
		if Hash(prior[key]) != Hash(admission[key]) {
			return nil, Fail(412, "STALE_INPUT", "dispatch authority snapshot changed")
		}
	}
	if e = s.taskContextForRun(tx, project, run); e != nil {
		return nil, e
	}
	if _, e = s.runDependenciesCurrent(tx, project, task, run); e != nil {
		return nil, e
	}
	return admission, nil
}

func (s *Service) currentDispatchedRun(tx *sql.Tx, project string, run Object, operation string) error {
	dispatch, e := runtimeDispatch(tx, project, Str(run, "id"), run["lease_epoch"])
	if e == sql.ErrNoRows {
		return nil
	} // Existing bounded fixture contracts remain compatible.
	if e != nil {
		return e
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return e
	}
	_, e = s.currentDispatchAdmission(tx, project, task, run, dispatch, operation)
	return e
}

func nativeDispatchProof(tx *sql.Tx, project string, run, observation Object) (Object, error) {
	dispatch, e := runtimeDispatch(tx, project, Str(run, "id"), run["lease_epoch"])
	if e != nil {
		return nil, e
	}
	if dispatch["state"] != "OBSERVED" || dispatch["observation_hash"] != Hash(observation) || observation["dispatch_key"] != dispatch["dispatch_key"] || observation["manifest_hash"] != dispatch["manifest_hash"] || observation["worker"] != dispatch["worker"] || Hash(observation["identity"]) != Hash(dispatch["identity"]) || observation["streams_drained"] != true || observation["cleanup_complete"] != true {
		return nil, Fail(422, "GATE_FAILED", "native terminal proof missing or changed")
	}
	return dispatch, nil
}

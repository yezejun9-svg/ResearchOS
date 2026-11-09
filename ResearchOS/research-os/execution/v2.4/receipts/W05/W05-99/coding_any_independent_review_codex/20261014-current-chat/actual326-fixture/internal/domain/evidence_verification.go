package domain

import "database/sql"

func init() { implemented["verifyEvidence"] = true }

// verifyEvidence records a judgement about the exact current Evidence version.
// The accepted fixture report binds the judgement; it does not prove source truth.
func (s *Service) verifyEvidence(tx *sql.Tx, p Principal, project, id string, b Object) (Object, error) {
	if !p.HasRole("VERIFIER") || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current verifier project grant required")
	}
	ev, e := s.readObject(tx, p, project, "Evidence", id)
	if e != nil {
		return nil, e
	}
	if ev["validity"] != "CURRENT" || ev["verification_status"] != "UNVERIFIED" {
		return nil, Fail(409, "STATE_CONFLICT", "current unverified evidence required")
	}
	snapshotRef, ok := ev["snapshot_artifact_ref"].(map[string]any)
	if !ok || snapshotRef["entity_type"] != "Artifact" {
		return nil, Fail(422, "GATE_FAILED", "snapshot reference required")
	}
	snapshot, e := s.readObject(tx, p, project, "Artifact", Str(snapshotRef, "id"))
	if e != nil {
		return nil, e
	}
	if Hash(Ref(snapshot, "Artifact")) != Hash(snapshotRef) || snapshot["validity"] != "CURRENT" {
		return nil, Fail(412, "STALE_INPUT", "evidence snapshot changed")
	}
	// A fixture's JSON equality only authenticates its report, not a LIVE source claim.
	if ev["evidence_kind"] != "SIMULATED" || snapshot["kind"] != "SOURCE_SNAPSHOT" || snapshot["evidence_kind"] != "SIMULATED" || snapshot["measurement_mode"] != "FIXTURE" {
		return nil, Fail(422, "GATE_FAILED", "fixture verification requires simulated evidence and fixture snapshot")
	}
	if e = s.requireCurrentArtifactBody(tx, project, snapshot); e != nil {
		return nil, e
	}
	var sealed []byte
	if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, snapshot["storage_key"]).Scan(&sealed); e != nil || Digest(sealed) != snapshot["content_hash"] {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "sealed snapshot unavailable or changed")
	}
	r, e := load(tx, project, "Run", Str(b, "verification_run_id"))
	if e != nil {
		return nil, e
	}
	t, e := load(tx, project, "Task", Str(r, "task_id"))
	if e != nil {
		return nil, e
	}
	if t["task_type"] != "evidence_verification" || t["status"] != "ACCEPTED" || t["active_run_id"] != r["id"] || r["status"] != "SETTLED" || r["task_id"] != t["id"] || r["context_bundle_id"] != t["context_bundle_id"] || Hash(r["input_refs"]) != Hash(t["input_refs"]) || Hash(r["result_artifact_ids"]) != Hash(t["output_artifact_ids"]) {
		return nil, Fail(422, "GATE_FAILED", "settled accepted evidence verification run required")
	}
	inputs := Arr(t, "input_refs")
	if len(inputs) != 2 || Hash(inputs[0]) != Hash(Ref(ev, "Evidence")) || Hash(inputs[1]) != Hash(snapshotRef) {
		return nil, Fail(412, "STALE_INPUT", "verification task must bind exact evidence and snapshot versions")
	}
	if e = s.taskContext(tx, project, t); e != nil {
		return nil, e
	}
	if _, e = s.runDependenciesCurrent(tx, project, t, r); e != nil {
		return nil, e
	}
	var frozen string
	if e = tx.QueryRow("SELECT contract FROM orchestration_contracts WHERE project=? AND task=?", project, t["id"]).Scan(&frozen); e != nil {
		return nil, Fail(422, "GATE_FAILED", "submitted verification contract required")
	}
	contract, e := Decode([]byte(frozen))
	if e != nil || Hash(contract) != Hash(t["acceptance_contract"]) || contract["contract_hash"] != contractDigest(contract) {
		return nil, Fail(422, "GATE_FAILED", "frozen verification contract changed")
	}
	if e = s.acceptedTaskBinding(tx, project, t); e != nil {
		return nil, e
	}
	observation, e := runtimeObservation(tx, project, r)
	if e != nil {
		return nil, e
	}
	protocol, _ := observation["protocol"].(map[string]any)
	if observation["state"] != "SETTLED" || protocol["settled"] != true || observation["children_stopped"] != true || observation["queue_empty"] != true || r["children_stopped"] != true || r["queue_empty"] != true {
		return nil, Fail(422, "GATE_FAILED", "successful current runtime observation required")
	}
	receipt, e := load(tx, project, "AcceptanceReceipt", Str(t, "acceptance_id"))
	if e != nil {
		return nil, e
	}
	if e = retentionIndependent(tx, t, receipt); e != nil {
		return nil, e
	}
	if receipt["run_id"] != r["id"] || receipt["measurement_mode"] != "FIXTURE" || receipt["independence_basis"] != "DETERMINISTIC_SERVICE" || len(Arr(receipt, "checks")) == 0 || Hash(receipt["checks"]) != Hash(b["check_results"]) {
		return nil, Fail(422, "GATE_FAILED", "current independent checks must match accepted run")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(state["policy_revision"]) != Hash(receipt["policy_revision"]) {
		return nil, Fail(412, "STALE_INPUT", "acceptance policy changed")
	}
	var authorized int
	if e = tx.QueryRow("SELECT count(*) FROM auth_principals p JOIN auth_grants g ON g.principal=p.id WHERE p.id=? AND p.revoked=0 AND instr(p.roles, '\"VERIFIER\"')>0 AND g.project=? AND g.task='' AND g.run=''", receipt["verifier_principal_id"], project).Scan(&authorized); e != nil {
		return nil, e
	}
	if authorized == 0 {
		return nil, Fail(403, "FORBIDDEN", "acceptance verifier grant revoked")
	}
	producerRoot, e := authorityRoot(tx, Str(snapshot, "produced_by"))
	if e != nil {
		return nil, e
	}
	executorRoot, e := authorityRoot(tx, Str(r, "executor_principal_id"))
	if e != nil {
		return nil, e
	}
	acceptorRoot, e := authorityRoot(tx, Str(receipt, "verifier_principal_id"))
	if e != nil {
		return nil, e
	}
	callerRoot, e := authorityRoot(tx, p.ID)
	if e != nil {
		return nil, e
	}
	if producerRoot == "" || acceptorRoot == producerRoot || callerRoot == producerRoot || acceptorRoot == executorRoot || callerRoot == executorRoot {
		return nil, Fail(403, "FORBIDDEN", "evidence reviewer must be independent of source and execution")
	}
	if len(Arr(receipt, "artifact_refs")) != 1 {
		return nil, Fail(422, "GATE_FAILED", "one accepted result artifact required")
	}
	result, e := s.artifactJSON(tx, project, Arr(receipt, "artifact_refs")[0].(map[string]any))
	if e != nil {
		return nil, e
	}
	judgement, ok := result.(map[string]any)
	if !ok || len(judgement) != 5 || judgement["type"] != "researchos.evidence-verification.v1" || Hash(judgement["evidence_ref"]) != Hash(Ref(ev, "Evidence")) || Hash(judgement["snapshot_artifact_ref"]) != Hash(snapshotRef) || judgement["status"] != b["status"] || Str(judgement, "reason") == "" {
		return nil, Fail(422, "GATE_FAILED", "accepted result does not bind this evidence judgement")
	}
	checks := Arr(contract, "checks")
	if len(checks) != 1 {
		return nil, Fail(422, "GATE_FAILED", "one deterministic judgement check required")
	}
	check := checks[0].(map[string]any)
	expected, e := Decode([]byte(Str(check, "expected")))
	if e != nil || check["kind"] != "DETERMINISTIC" || check["required"] != true || check["command_key"] != "orchestration.json-equals" || check["rubric_ref"] != nil || check["qualification_id"] != nil || Hash(expected) != Hash(result) {
		return nil, Fail(422, "GATE_FAILED", "frozen check does not verify exact judgement")
	}
	if e = bump(ev); e != nil {
		return nil, e
	}
	ev["verification_status"] = b["status"]
	ev["verified_by_run_id"] = r["id"]
	return ev, s.put(tx, "Evidence", ev)
}

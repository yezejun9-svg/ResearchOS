package domain

import (
	"context"
	"database/sql"
)

// acceptanceSnapshot validates bindings inside a short transaction. Artifact
// computation happens after it closes; finalization rebuilds this snapshot.
func (s *Service) acceptanceSnapshot(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	if !p.HasRole("VERIFIER") || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current independent verifier grant required")
	}
	ref := b["subject_ref"].(map[string]any)
	t, e := load(tx, project, "Task", Str(ref, "id"))
	if e != nil {
		return nil, e
	}
	if t["status"] != "EXECUTION_REPORTED" && t["status"] != "VERIFYING" {
		return nil, Fail(409, "STATE_CONFLICT", "task is not awaiting independent verification")
	}
	if Hash(Ref(t, "Task")) != Hash(ref) {
		return nil, Fail(412, "STALE_INPUT", "task version changed")
	}
	if e = s.taskContext(tx, project, t); e != nil {
		return nil, e
	}
	var frozen string
	if e = tx.QueryRow("SELECT contract FROM orchestration_contracts WHERE project=? AND task=?", project, t["id"]).Scan(&frozen); e != nil {
		return nil, Fail(422, "GATE_FAILED", "normal submitted frozen contract required")
	}
	c, e := Decode([]byte(frozen))
	if e != nil {
		return nil, e
	}
	if Hash(c) != Hash(t["acceptance_contract"]) || c["contract_hash"] != b["contract_hash"] || c["contract_hash"] != contractDigest(c) {
		return nil, Fail(422, "GATE_FAILED", "frozen contract mismatch")
	}
	r, e := load(tx, project, "Run", Str(t, "active_run_id"))
	if e != nil {
		return nil, e
	}
	if r["id"] != b["run_id"] || r["task_id"] != t["id"] || r["status"] != "SETTLED" || r["children_stopped"] != true || r["queue_empty"] != true || r["context_bundle_id"] != t["context_bundle_id"] || Hash(r["input_refs"]) != Hash(t["input_refs"]) || Hash(r["result_artifact_ids"]) != Hash(t["output_artifact_ids"]) {
		return nil, Fail(422, "GATE_FAILED", "settled current epoch and exact output/context binding required")
	}
	dependencies, e := s.runDependenciesCurrent(tx, project, t, r)
	if e != nil {
		return nil, e
	}
	observation, e := runtimeObservation(tx, project, r)
	if e != nil {
		return nil, e
	}
	protocol, _ := observation["protocol"].(map[string]any)
	if observation["state"] != "SETTLED" || protocol["settled"] != true || observation["children_stopped"] != true || observation["queue_empty"] != true {
		return nil, Fail(422, "GATE_FAILED", "current epoch has no successful trusted observation")
	}
	if Hash(b["input_refs"]) != Hash(t["input_refs"]) {
		return nil, Fail(412, "STALE_INPUT", "acceptance input vector mismatch")
	}
	for _, v := range append(Arr(t, "input_refs"), Arr(t, "requirement_refs")...) {
		if e = s.effective(tx, project, v.(map[string]any)); e != nil {
			return nil, e
		}
	}
	root, e := authorityRoot(tx, p.ID)
	if e != nil {
		return nil, e
	}
	executorRoot, e := authorityRoot(tx, Str(r, "executor_principal_id"))
	if e != nil {
		return nil, e
	}
	if root == executorRoot {
		return nil, Fail(403, "FORBIDDEN", "executor, alias or delegated authority cannot accept own output")
	}
	if Hash(b["executor_principal_ids"]) != Hash([]any{r["executor_principal_id"]}) {
		return nil, Fail(422, "GATE_FAILED", "executor identity binding mismatch")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(b["policy_revision"]) != Hash(state["policy_revision"]) {
		return nil, Fail(412, "STALE_INPUT", "policy revision changed")
	}
	if len(Arr(t, "blocking_conflict_ids"))+len(Arr(state, "blocking_conflict_ids"))+len(Arr(b, "blocking_conflict_ids")) != 0 {
		return nil, Fail(409, "STATE_CONFLICT", "blocking conflict unresolved")
	}
	rt, e := load(tx, project, "RuntimeRegistration", Str(r, "runtime_id"))
	if e != nil {
		return nil, e
	}
	var fixture int
	if e = tx.QueryRow("SELECT count(*) FROM orchestration_fixtures WHERE project=? AND runtime=?", project, rt["id"]).Scan(&fixture); e != nil {
		return nil, e
	}
	if fixture != 1 || rt["measurement_mode"] != "FIXTURE" || b["measurement_mode"] != "FIXTURE" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "LIVE acceptance requires qualified runtime and verification resources")
	}
	if b["independence_basis"] != "DETERMINISTIC_SERVICE" || len(Arr(b, "qualification_ids")) != 0 {
		return nil, Fail(422, "GATE_FAILED", "only deterministic service verification is implemented")
	}
	requested := map[string]Object{}
	for _, v := range Arr(b, "checks") {
		x := v.(map[string]any)
		id := Str(x, "check_id")
		if requested[id] != nil {
			return nil, Fail(422, "GATE_FAILED", "duplicate requested check")
		}
		requested[id] = x
	}
	if len(requested) != len(Arr(c, "checks")) {
		return nil, Fail(422, "GATE_FAILED", "all frozen checks required")
	}
	for _, v := range Arr(c, "checks") {
		check := v.(map[string]any)
		x := requested[Str(check, "check_id")]
		if x == nil || Hash(x["command_key"]) != Hash(check["command_key"]) {
			return nil, Fail(422, "GATE_FAILED", "requested checks differ from frozen checks")
		}
	}
	artifacts, refs := Empty(), Empty()
	for _, v := range Arr(t, "output_artifact_ids") {
		a, use, e := s.artifactUse(tx, project, r, v.(string), true)
		if e != nil {
			return nil, e
		}
		if use["measurement_mode"] != "FIXTURE" || a["access_class"] == "VERIFIER_ONLY" {
			return nil, Fail(422, "GATE_FAILED", "output provenance or isolation mismatch")
		}
		var raw []byte
		if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, use["storage_key"]).Scan(&raw); e != nil {
			return nil, e
		}
		size, _ := Num(a, "byte_size")
		if Digest(raw) != a["content_hash"] || size != int64(len(raw)) {
			return nil, Fail(422, "CONTENT_HASH_MISMATCH", "output bytes no longer match seal")
		}
		artifacts = append(artifacts, Object{"artifact": a, "use": use, "bytes": raw})
		refs = append(refs, Ref(a, "Artifact"))
	}
	if len(artifacts) == 0 || Hash(refs) != Hash(b["artifact_refs"]) {
		return nil, Fail(422, "GATE_FAILED", "exact output artifact vector required")
	}
	return Object{"task": t, "run": r, "contract": c, "artifacts": artifacts, "artifact_refs": refs, "policy_revision": state["policy_revision"], "runtime": rt, "authority": root, "observation": observation, "dependency_refs": dependencies}, nil
}

type preparedAcceptance struct {
	snapshot          Object
	checks            []any
	verdict           string
	started, finished string
}

func (s *Service) prepareTaskAcceptance(ctx context.Context, token, project string, b Object) (*preparedAcceptance, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	p, e := authenticate(tx, token)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	snap, e := s.acceptanceSnapshot(tx, p, project, b)
	tx.Rollback()
	if e != nil {
		return nil, e
	}
	a := &preparedAcceptance{snapshot: snap, checks: Empty(), verdict: "PASS", started: Now()}
	c := snap["contract"].(map[string]any)
	for _, v := range Arr(c, "checks") {
		check := v.(map[string]any)
		status, actual := "NOT_RUN", "Check requires an unavailable qualified verifier or command handler."
		var exit any
		if check["kind"] == "DETERMINISTIC" && check["command_key"] == "orchestration.json-equals" && check["rubric_ref"] == nil && check["qualification_id"] == nil {
			expected, err := Decode([]byte(Str(check, "expected")))
			artifacts := Arr(snap, "artifacts")
			status = "FAIL"
			actual = "Expected one JSON artifact matching the frozen expected object."
			exit = 1
			if err == nil && len(artifacts) == 1 {
				entry := artifacts[0].(map[string]any)
				obj, err := Decode(entry["bytes"].([]byte))
				if err == nil {
					actual = string(Bytes(obj))
					if Hash(obj) == Hash(expected) {
						status = "PASS"
						exit = 0
					}
				}
			}
		}
		if check["required"] == true {
			if status == "FAIL" {
				a.verdict = "FAIL"
			} else if status != "PASS" && a.verdict != "FAIL" {
				a.verdict = "BLOCKED"
			}
		}
		a.checks = append(a.checks, Object{"check_id": check["check_id"], "status": status, "actual": actual, "command_key": check["command_key"], "exit_code": exit, "evidence_refs": Empty(), "started_at": a.started, "finished_at": Now()})
	}
	a.finished = Now()
	return a, nil
}

func (s *Service) acceptTask(tx *sql.Tx, p Principal, project string, b Object, a *preparedAcceptance) (Object, error) {
	if a == nil {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "independent verification was not performed")
	}
	current, e := s.acceptanceSnapshot(tx, p, project, b)
	if e != nil {
		return nil, e
	}
	if Hash(current) != Hash(a.snapshot) {
		return nil, Fail(412, "STALE_INPUT", "inputs changed during independent verification")
	}
	if b["verdict"] != a.verdict {
		return nil, Fail(422, "GATE_FAILED", "requested verdict differs from independently computed checks")
	}
	t := current["task"].(map[string]any)
	r := current["run"].(map[string]any)
	ev, e := s.serverArtifact(tx, project, p.ID, "REPORT", Bytes(Object{"task_ref": Ref(t, "Task"), "run_ref": Ref(r, "Run"), "lease_epoch": r["lease_epoch"], "contract_hash": b["contract_hash"], "input_refs": t["input_refs"], "artifact_refs": current["artifact_refs"], "checks": a.checks, "started_at": a.started, "finished_at": a.finished}), Arr(current, "artifact_refs"))
	if e != nil {
		return nil, e
	}
	for _, v := range a.checks {
		v.(map[string]any)["evidence_refs"] = []any{Ref(ev, "Artifact")}
	}
	receipt := Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "subject_ref": Ref(t, "Task"), "run_id": r["id"], "contract_hash": b["contract_hash"], "input_refs": t["input_refs"], "artifact_refs": current["artifact_refs"], "checks": a.checks, "verdict": a.verdict, "verifier_principal_id": p.ID, "executor_principal_ids": []any{r["executor_principal_id"]}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": current["policy_revision"], "measurement_mode": "FIXTURE", "reason": "Server recomputed frozen deterministic checks; no model or LIVE qualification claimed."}
	receipt["receipt_hash"] = Receipt(receipt)
	if e = s.put(tx, "AcceptanceReceipt", receipt); e != nil {
		return nil, e
	}
	if e = bump(t); e != nil {
		return nil, e
	}
	t["acceptance_id"] = receipt["id"]
	switch a.verdict {
	case "PASS":
		t["status"] = "ACCEPTED"
	case "FAIL":
		if e = s.taskFailed(tx, project, t, "mandatory acceptance check failed"); e != nil {
			return nil, e
		}
	default:
		t["status"] = "BLOCKED"
	}
	if e = s.put(tx, "Task", t); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Task", t, p.ID, ID(), "TASK_CHANGED"); e != nil {
		return nil, e
	}
	if a.verdict == "PASS" {
		if e = s.releaseSuccessors(tx, p, project, t); e != nil {
			return nil, e
		}
	}
	return receipt, nil
}

func (s *Service) acceptedTaskBinding(tx *sql.Tx, project string, t Object) error {
	receipt, e := load(tx, project, "AcceptanceReceipt", Str(t, "acceptance_id"))
	if e != nil {
		return Fail(422, "GATE_FAILED", "accepted dependency lacks receipt")
	}
	c := t["acceptance_contract"].(map[string]any)
	if receipt["verdict"] != "PASS" || receipt["receipt_hash"] != Receipt(receipt) || receipt["contract_hash"] != c["contract_hash"] || c["contract_hash"] != contractDigest(c) || Hash(receipt["input_refs"]) != Hash(t["input_refs"]) || receipt["run_id"] != t["active_run_id"] {
		return Fail(422, "GATE_FAILED", "dependency acceptance binding changed")
	}
	r, e := load(tx, project, "Run", Str(receipt, "run_id"))
	if e != nil {
		return e
	}
	ids := Empty()
	for _, v := range Arr(receipt, "artifact_refs") {
		ref := v.(map[string]any)
		a, _, e := s.artifactUse(tx, project, r, Str(ref, "id"), true)
		if e != nil {
			return e
		}
		if Hash(Ref(a, "Artifact")) != Hash(ref) {
			return Fail(412, "STALE_INPUT", "accepted result version changed")
		}
		ids = append(ids, ref["id"])
	}
	if Hash(ids) != Hash(t["output_artifact_ids"]) {
		return Fail(422, "GATE_FAILED", "dependency output binding changed")
	}
	return nil
}

func (s *Service) releaseSuccessors(tx *sql.Tx, p Principal, project string, accepted Object) error {
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.status')='BLOCKED'", project)
	if e != nil {
		return e
	}
	candidates := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return e
		}
		t, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return e
		}
		candidates = append(candidates, t)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, t := range candidates {
		depends := false
		for _, v := range Arr(t, "dependency_task_ids") {
			if v == accepted["id"] {
				depends = true
			}
		}
		if !depends || len(Arr(t, "blocking_conflict_ids")) != 0 {
			continue
		}
		var submitted int
		if e = tx.QueryRow("SELECT count(*) FROM orchestration_contracts WHERE project=? AND task=?", project, t["id"]).Scan(&submitted); e != nil {
			return e
		}
		if submitted == 0 {
			continue
		}
		ready, e := s.dependenciesReady(tx, project, t)
		if e != nil || !ready {
			continue
		}
		if e = s.taskContext(tx, project, t); e != nil {
			continue
		}
		g, e := load(tx, project, "Goal", Str(t, "goal_id"))
		if e != nil {
			return e
		}
		if g["status"] != "ACTIVE" {
			continue
		}
		t["status"] = "READY"
		if e = bump(t); e != nil {
			return e
		}
		if e = s.put(tx, "Task", t); e != nil {
			return e
		}
		if e = s.event(tx, project, "Task", t, p.ID, ID(), "TASK_CHANGED"); e != nil {
			return e
		}
	}
	return nil
}

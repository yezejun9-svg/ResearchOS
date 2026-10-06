package domain

import (
	"database/sql"
	"sort"
)

func freezeGoalContract(tx *sql.Tx, project string, g Object) error {
	c := g["acceptance_contract"].(map[string]any)
	if c["contract_hash"] != contractDigest(c) || c["require_independent_verifier"] != true || c["version_policy"] != "EXACT" {
		return Fail(422, "GATE_FAILED", "exact independent goal contract required")
	}
	required := 0
	seen := map[string]bool{}
	for _, v := range Arr(c, "checks") {
		check := v.(map[string]any)
		id := Str(check, "check_id")
		if seen[id] {
			return Fail(422, "GATE_FAILED", "duplicate goal check")
		}
		seen[id] = true
		if check["required"] == true {
			required++
		}
	}
	if required == 0 {
		return Fail(422, "GATE_FAILED", "mandatory goal check required")
	}
	var raw string
	e := tx.QueryRow("SELECT contract FROM orchestration_goal_contracts WHERE project=? AND goal=?", project, g["id"]).Scan(&raw)
	if e == nil {
		old, _ := Decode([]byte(raw))
		if Hash(old) != Hash(c) {
			return Fail(422, "GATE_FAILED", "goal contract frozen at activation")
		}
		return nil
	}
	if e != sql.ErrNoRows {
		return e
	}
	_, e = tx.Exec("INSERT INTO orchestration_goal_contracts(project,goal,contract) VALUES(?,?,?)", project, g["id"], string(Bytes(c)))
	return e
}

func (s *Service) goalAcceptanceSnapshot(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	ref := b["subject_ref"].(map[string]any)
	g, e := load(tx, project, "Goal", Str(ref, "id"))
	if e != nil {
		return nil, e
	}
	if g["status"] != "ACTIVE" && g["status"] != "VERIFYING" {
		return nil, Fail(409, "STATE_CONFLICT", "goal is not awaiting verification")
	}
	if Hash(Ref(g, "Goal")) != Hash(ref) {
		return nil, Fail(412, "STALE_INPUT", "goal changed")
	}
	var raw string
	if e = tx.QueryRow("SELECT contract FROM orchestration_goal_contracts WHERE project=? AND goal=?", project, g["id"]).Scan(&raw); e != nil {
		return nil, Fail(422, "GATE_FAILED", "goal has no frozen activation contract")
	}
	c, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	if Hash(c) != Hash(g["acceptance_contract"]) || c["contract_hash"] != b["contract_hash"] || c["contract_hash"] != contractDigest(c) {
		return nil, Fail(422, "GATE_FAILED", "goal contract mismatch")
	}
	if b["run_id"] != nil || b["independence_basis"] != "DETERMINISTIC_SERVICE" || len(Arr(b, "qualification_ids")) != 0 {
		return nil, Fail(422, "GATE_FAILED", "goal acceptance uses current accepted task runs")
	}
	var planningTask string
	planningErr := tx.QueryRow("SELECT planning_task FROM intent_plan_bindings WHERE project=? AND planning_goal=?", project, g["id"]).Scan(&planningTask)
	if planningErr != nil && planningErr != sql.ErrNoRows {
		return nil, planningErr
	}
	mode := Str(b, "measurement_mode")
	if mode != "FIXTURE" && (mode != "LIVE" || planningErr != nil) {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "LIVE goal acceptance remains unavailable")
	}
	if planningErr == nil && (len(Arr(g, "task_ids")) != 1 || Arr(g, "task_ids")[0] != planningTask) {
		return nil, Fail(422, "GATE_FAILED", "planning Goal must contain its exact bound Task")
	}
	if len(Arr(g, "task_ids")) == 0 {
		return nil, Fail(422, "GATE_FAILED", "goal needs accepted deliverable tasks")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(b["policy_revision"]) != Hash(state["policy_revision"]) {
		return nil, Fail(412, "STALE_INPUT", "goal policy changed")
	}
	if len(Arr(state, "blocking_conflict_ids"))+len(Arr(b, "blocking_conflict_ids")) != 0 {
		return nil, Fail(409, "STATE_CONFLICT", "goal conflict unresolved")
	}
	root, e := authorityRoot(tx, p.ID)
	if e != nil {
		return nil, e
	}
	inputs := append(Empty(), Arr(g, "requirement_refs")...)
	tasks, artifacts, refs := Empty(), Empty(), Empty()
	authors := map[string]bool{}
	for _, v := range Arr(g, "task_ids") {
		t, e := load(tx, project, "Task", v.(string))
		if e != nil {
			return nil, e
		}
		if t["status"] != "ACCEPTED" || len(Arr(t, "blocking_conflict_ids")) != 0 {
			return nil, Fail(409, "STATE_CONFLICT", "all goal tasks must be independently accepted")
		}
		if e = s.acceptedTaskBinding(tx, project, t); e != nil {
			return nil, e
		}
		if e = s.taskContext(tx, project, t); e != nil {
			return nil, e
		}
		receipt, e := load(tx, project, "AcceptanceReceipt", Str(t, "acceptance_id"))
		if e != nil {
			return nil, e
		}
		if receipt["measurement_mode"] != mode {
			return nil, Fail(422, "GATE_FAILED", "goal and task verification modes differ")
		}
		if planningErr == nil {
			run, err := load(tx, project, "Run", Str(receipt, "run_id"))
			if err != nil {
				return nil, err
			}
			dispatch, err := runtimeDispatch(tx, project, Str(run, "id"), run["lease_epoch"])
			if err == nil {
				observation, err := runtimeObservation(tx, project, run)
				if err != nil {
					return nil, err
				}
				if _, err = nativeDispatchProof(tx, project, run, observation); err != nil {
					return nil, err
				}
				admission, err := s.currentDispatchAdmission(tx, project, t, run, dispatch, "accept")
				if err != nil {
					return nil, err
				}
				if admission["mode"] != mode {
					return nil, Fail(422, "GATE_FAILED", "planning runtime mode changed")
				}
			} else if err != sql.ErrNoRows || mode != "FIXTURE" {
				return nil, Fail(422, "GATE_FAILED", "planning Goal requires current native dispatch evidence")
			}
		}
		for _, v := range Arr(receipt, "executor_principal_ids") {
			id := v.(string)
			authority, e := authorityRoot(tx, id)
			if e != nil {
				return nil, e
			}
			if authority == root {
				return nil, Fail(403, "FORBIDDEN", "goal verifier cannot share authority with a deliverable executor")
			}
			authors[id] = true
		}
		inputs = append(inputs, Ref(t, "Task"))
		tasks = append(tasks, t)
		for _, v := range Arr(receipt, "artifact_refs") {
			ref := v.(map[string]any)
			run, e := load(tx, project, "Run", Str(receipt, "run_id"))
			if e != nil {
				return nil, e
			}
			a, use, e := s.artifactUse(tx, project, run, Str(ref, "id"), true)
			if e != nil {
				return nil, e
			}
			if use["measurement_mode"] != mode || Hash(Ref(a, "Artifact")) != Hash(ref) {
				return nil, Fail(422, "GATE_FAILED", "goal output use differs from accepted artifact")
			}
			var data []byte
			if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, use["storage_key"]).Scan(&data); e != nil {
				return nil, e
			}
			size, _ := Num(a, "byte_size")
			if Digest(data) != a["content_hash"] || size != int64(len(data)) {
				return nil, Fail(422, "CONTENT_HASH_MISMATCH", "goal deliverable hash mismatch")
			}
			artifacts = append(artifacts, Object{"artifact": a, "use": use, "bytes": data})
			refs = append(refs, ref)
		}
	}
	for _, v := range Arr(g, "requirement_refs") {
		if e = s.effective(tx, project, v.(map[string]any)); e != nil {
			return nil, e
		}
	}
	executorIDs := []string{}
	for id := range authors {
		executorIDs = append(executorIDs, id)
	}
	sort.Strings(executorIDs)
	if Hash(inputs) != Hash(b["input_refs"]) || Hash(refs) != Hash(b["artifact_refs"]) || Hash(executorIDs) != Hash(b["executor_principal_ids"]) {
		return nil, Fail(422, "GATE_FAILED", "goal inputs, outputs or executor identities mismatch")
	}
	requested := map[string]Object{}
	for _, v := range Arr(b, "checks") {
		x := v.(map[string]any)
		id := Str(x, "check_id")
		if requested[id] != nil {
			return nil, Fail(422, "GATE_FAILED", "duplicate goal check")
		}
		requested[id] = x
	}
	if len(requested) != len(Arr(c, "checks")) {
		return nil, Fail(422, "GATE_FAILED", "all goal checks required")
	}
	for _, v := range Arr(c, "checks") {
		x := v.(map[string]any)
		r := requested[Str(x, "check_id")]
		if r == nil || Hash(r["command_key"]) != Hash(x["command_key"]) {
			return nil, Fail(422, "GATE_FAILED", "goal check mismatch")
		}
	}
	var planning Object
	if planningErr == nil {
		planning, e = s.planningSnapshot(tx, project, tasks[0].(map[string]any))
		if e != nil {
			return nil, e
		}
	}
	compiled, e := s.compiledPlanningSnapshot(tx, project, g)
	if e != nil {
		return nil, e
	}
	return Object{"goal": g, "contract": c, "tasks": tasks, "artifacts": artifacts, "artifact_refs": refs, "input_refs": inputs, "executor_ids": executorIDs, "policy_revision": state["policy_revision"], "authority": root, "measurement_mode": mode, "planning": planning, "compiled_plan": compiled}, nil
}

func (s *Service) acceptGoal(tx *sql.Tx, p Principal, project string, b Object, a *preparedAcceptance, cid string) (Object, error) {
	current, e := s.acceptanceSnapshot(tx, p, project, b)
	if e != nil {
		return nil, e
	}
	if Hash(current) != Hash(a.snapshot) {
		return nil, Fail(412, "STALE_INPUT", "goal inputs changed during verification")
	}
	if b["verdict"] != a.verdict {
		return nil, Fail(422, "GATE_FAILED", "goal verdict differs from computed checks")
	}
	g := current["goal"].(map[string]any)
	ev, e := s.serverArtifactMode(tx, project, p.ID, "REPORT", Str(current, "measurement_mode"), Bytes(Object{"goal_ref": Ref(g, "Goal"), "checks": a.checks, "input_refs": current["input_refs"], "artifact_refs": current["artifact_refs"], "started_at": a.started, "finished_at": a.finished}), Arr(current, "artifact_refs"))
	if e != nil {
		return nil, e
	}
	for _, v := range a.checks {
		v.(map[string]any)["evidence_refs"] = []any{Ref(ev, "Artifact")}
	}
	receipt := Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "subject_ref": Ref(g, "Goal"), "run_id": nil, "contract_hash": b["contract_hash"], "input_refs": current["input_refs"], "artifact_refs": current["artifact_refs"], "checks": a.checks, "verdict": a.verdict, "verifier_principal_id": p.ID, "executor_principal_ids": current["executor_ids"], "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": current["policy_revision"], "measurement_mode": current["measurement_mode"], "reason": "Independent deterministic goal deliverable verification."}
	receipt["receipt_hash"] = Receipt(receipt)
	if e = s.put(tx, "AcceptanceReceipt", receipt); e != nil {
		return nil, e
	}
	g["acceptance_id"] = receipt["id"]
	g["status"] = "BLOCKED"
	if a.verdict == "PASS" {
		g["status"] = "ACCEPTED"
	}
	if e = bump(g); e != nil {
		return nil, e
	}
	if e = s.put(tx, "Goal", g); e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	active := Empty()
	for _, v := range Arr(state, "active_goal_ids") {
		if v != g["id"] {
			active = append(active, v)
		}
	}
	state["active_goal_ids"] = active
	if e = bump(state); e != nil {
		return nil, e
	}
	if e = s.put(tx, "ProjectState", state); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Goal", g, p.ID, cid, "PROJECT_UPDATED"); e != nil {
		return nil, e
	}
	if planning, _ := current["planning"].(map[string]any); a.verdict == "PASS" && planning != nil {
		if e = s.compileIntentPlan(tx, project, current, receipt); e != nil {
			return nil, e
		}
	}
	return receipt, nil
}

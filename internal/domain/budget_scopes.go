package domain

import "database/sql"

// Every call is constrained by its Goal and every preregistered Experiment.
// The W10 binding is optional only while that migration is absent; query errors
// after integration fail closed. A ledger caller cannot choose its own scope.
func runBudgetScopes(tx *sql.Tx, project, runID string) ([]Object, map[string]bool, error) {
	run, e := load(tx, project, "Run", runID)
	if e != nil {
		return nil, nil, e
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return nil, nil, e
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return nil, nil, e
	}
	leaves := map[string]bool{Str(goal, "budget_policy_id"): true}
	var installed int
	if e = tx.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='experiment_tasks'").Scan(&installed); e != nil {
		return nil, nil, e
	}
	if installed == 1 {
		rows, e := tx.Query("SELECT experiment FROM experiment_tasks WHERE project=? AND task=?", project, task["id"])
		if e != nil {
			return nil, nil, e
		}
		ids := []string{}
		for rows.Next() {
			var id string
			if e = rows.Scan(&id); e != nil {
				rows.Close()
				return nil, nil, e
			}
			ids = append(ids, id)
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return nil, nil, e
		}
		for _, id := range ids {
			experiment, e := load(tx, project, "Experiment", id)
			if e != nil {
				return nil, nil, e
			}
			leaves[Str(experiment, "budget_policy_id")] = true
		}
	}
	policies := []Object{}
	seen := map[string]bool{}
	for leaf := range leaves {
		chain, e := budgetChain(tx, project, leaf)
		if e != nil {
			return nil, nil, e
		}
		for _, policy := range chain {
			key := Str(policy, "id")
			if !seen[key] {
				seen[key] = true
				policies = append(policies, policy)
			}
		}
	}
	return policies, leaves, nil
}

func (s *Service) admitResourceQueue(tx *sql.Tx, project, taskID string) error {
	profile, e := singleton(tx, project, "ProjectProfile")
	if e != nil {
		return e
	}
	local, e := load(tx, project, "RunPolicy", Str(profile, "run_policy_id"))
	if e != nil {
		return e
	}
	global, e := singleton(tx, "", "RunPolicy")
	if e != nil {
		return e
	}
	for _, p := range []Object{local, global} {
		limit, _ := Num(p, "max_queue")
		var queued int64
		e = tx.QueryRow(`SELECT count(*) FROM domain_objects t WHERE t.kind='Task' AND t.id<>? AND (?='' OR t.project=?) AND json_extract(t.body,'$.status') IN ('READY','BLOCKED') AND NOT EXISTS (SELECT 1 FROM domain_objects r WHERE r.project=t.project AND r.kind='Run' AND json_extract(r.body,'$.task_id')=t.id AND json_extract(r.body,'$.status') NOT IN ('SETTLED','FAILED','CANCELLED'))`, taskID, Str(p, "project_id"), Str(p, "project_id")).Scan(&queued)
		if e != nil {
			return e
		}
		if queued >= limit {
			return Fail(409, "STATE_CONFLICT", "durable task queue full; existing work retained")
		}
	}
	return nil
}

func (s *Service) admitGlobalConcurrency(tx *sql.Tx) error {
	p, e := singleton(tx, "", "RunPolicy")
	if e != nil {
		return e
	}
	limit, _ := Num(p, "max_concurrency")
	var count int64
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.status') NOT IN ('SETTLED','FAILED','CANCELLED')").Scan(&count); e != nil {
		return e
	}
	if count >= limit {
		return Fail(409, "STATE_CONFLICT", "global concurrency exhausted")
	}
	return nil
}

// Fixture dispatch has a proved zero provider charge. LIVE dispatch remains
// blocked by the existing W05 gate until its price bound/qualification exists.
// The zero is a claim about the provider, so it is only admissible for a runtime
// registered as FIXTURE: under a CAPPED policy that enforces STRICT (or blocks on
// unknown cost) an unprovable bound stops the run here instead of entering the
// ledger as 0 and spending budget that nothing ever priced.
func (s *Service) reserveFixtureDispatch(tx *sql.Tx, project string, run Object) error {
	scopes, _, e := runBudgetScopes(tx, project, Str(run, "id"))
	if e != nil {
		return e
	}
	capped := false
	for _, p := range scopes {
		if p["mode"] != "CAPPED" {
			continue
		}
		if p["enforcement"] == "STRICT" || p["unknown_cost_action"] == "BLOCK" {
			capped = true
		}
	}
	if capped {
		registration, e := load(tx, project, "RuntimeRegistration", Str(run, "runtime_id"))
		if e != nil {
			return e
		}
		if Str(registration, "measurement_mode") != "FIXTURE" {
			return Fail(422, "GATE_FAILED", "run cost bound cannot be established at start")
		}
	}
	currency := "USD"
	for _, p := range scopes {
		if p["cap"] != nil {
			currency = Str(p["cap"].(map[string]any), "currency")
			break
		}
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return e
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return e
	}
	_, e = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "RESERVE", "money": Object{"amount": "0", "currency": currency}, "provider_request_id": "fixture-dispatch/" + Str(run, "id"), "provider_event_id": "fixture-dispatch/" + Str(run, "id"), "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()})
	return e
}

// AppContainer creation is a local operation with no provider request. Its
// zero charge is explicit and separate from every typed broker reservation.
func (s *Service) reserveRuntimeLocalLaunch(tx *sql.Tx, project string, run, admission Object) error {
	profile, ok := admission["profile"].(map[string]any)
	if !ok {
		return Fail(422, "GATE_FAILED", "dispatch cost admission requires frozen profile")
	}
	if e := validateRuntimeDispatchProfile(profile); e != nil {
		return e
	}
	scopes, _, e := runBudgetScopes(tx, project, Str(run, "id"))
	if e != nil {
		return e
	}
	currency := "USD"
	for _, p := range scopes {
		if p["cap"] != nil {
			currency = Str(p["cap"].(map[string]any), "currency")
			break
		}
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return e
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return e
	}
	request := "runtime-local-launch/" + Str(run, "id") + "/" + string(Bytes(run["lease_epoch"]))
	// Exposure groups by (project, run, provider_request_id) and a hold that is never
	// settled keeps counting. Each lease epoch therefore takes its own reservation, and
	// taking over a lease must first release the hold the dead epoch left open - as an
	// explicit ledger entry, never a deletion - or the same run is charged again next to
	// its own earlier hold while the original stays unresolved. A restart neither
	// recounts the charge nor clears the accounting trail.
	prefix := "runtime-local-launch/" + Str(run, "id") + "/"
	stale, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.provider_request_id') LIKE ? AND json_extract(body,'$.operation')='RESERVE'", project, run["id"], prefix+"%")
	if e != nil {
		return e
	}
	holds := []Object{}
	for stale.Next() {
		var raw string
		if e = stale.Scan(&raw); e != nil {
			stale.Close()
			return e
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			stale.Close()
			return e
		}
		if Str(o, "provider_request_id") != request {
			holds = append(holds, o)
		}
	}
	e = stale.Err()
	stale.Close()
	if e != nil {
		return e
	}
	for _, hold := range holds {
		release := Str(hold, "provider_request_id") + "/released"
		if _, e = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "RELEASE", "money": Object{"amount": "0", "currency": currency}, "provider_request_id": Str(hold, "provider_request_id"), "provider_event_id": release, "reservation_id": hold["id"], "cost_basis": "ACTUAL", "occurred_at": Now()}); e != nil {
			return e
		}
	}
	_, e = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "RESERVE", "money": Object{"amount": "0", "currency": currency}, "provider_request_id": request, "provider_event_id": request, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()})
	return e
}

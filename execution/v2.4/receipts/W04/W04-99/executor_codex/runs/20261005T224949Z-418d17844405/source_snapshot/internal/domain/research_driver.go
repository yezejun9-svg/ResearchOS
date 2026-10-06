package domain

import (
	"database/sql"
	"errors"
	"fmt"
	"time"
)

type researchWork struct {
	Project, Cycle, Key, Stage, Task                                   string
	PlanRef, Parameters, SourceReceipt                                 Object
	InputRefs                                                          []any
	SourceID, EvidenceID, Experiment, WindowFrom, WindowTo, ProgressID string
}

func loadResearchWork(tx *sql.Tx, project, taskID string) (*researchWork, error) {
	var planRaw, refsRaw, parameters string
	var source, evidence, experiment, from, to, progress, receipt sql.NullString
	w := &researchWork{Project: project, Task: taskID}
	err := tx.QueryRow("SELECT cycle,logical_key,stage,plan_ref,input_refs,parameters,source_id,evidence_id,experiment,window_from,window_to,progress_record_id,source_receipt FROM research_cycle_work WHERE project=? AND task=? ORDER BY created_at DESC LIMIT 1", project, taskID).Scan(&w.Cycle, &w.Key, &w.Stage, &planRaw, &refsRaw, &parameters, &source, &evidence, &experiment, &from, &to, &progress, &receipt)
	if err != nil {
		return nil, err
	}
	w.SourceID, w.EvidenceID, w.Experiment, w.WindowFrom, w.WindowTo, w.ProgressID = source.String, evidence.String, experiment.String, from.String, to.String, progress.String
	if w.PlanRef, err = Decode([]byte(planRaw)); err != nil {
		return nil, err
	}
	if w.Parameters, err = Decode([]byte(parameters)); err != nil {
		return nil, err
	}
	refs, err := Decode([]byte(`{"refs":` + refsRaw + `}`))
	if err != nil {
		return nil, err
	}
	w.InputRefs = Arr(refs, "refs")
	if receipt.Valid {
		w.SourceReceipt, err = Decode([]byte(receipt.String))
	}
	return w, err
}

func (w *researchWork) publicParameters() Object {
	return Object{"cycle_id": w.Cycle, "logical_key": w.Key, "stage": w.Stage, "plan_ref": w.PlanRef, "parameters": w.Parameters, "window_from": w.WindowFrom, "window_to": w.WindowTo}
}

func (s *Service) materializeResearchWork(tx *sql.Tx, owner Principal, project string, meta Object, plan *MonitorPlan, cycle Object, stage, key string, params Object, deps []any, inputs []any) (Object, error) {
	var id string
	if err := tx.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND cycle=? AND logical_key=?", project, cycle["id"], key).Scan(&id); err == nil {
		return load(tx, project, "Task", id)
	} else if err != sql.ErrNoRows {
		return nil, err
	}
	var count int
	if err := tx.QueryRow("SELECT count(*) FROM research_cycle_work WHERE project=? AND cycle=?", project, cycle["id"]).Scan(&count); err != nil {
		return nil, err
	}
	if count >= plan.MaxTasks {
		return nil, Fail(422, "GATE_FAILED", "finite cycle task bound exhausted")
	}
	goal := meta["goal"].(map[string]any)
	refs := mergeUnique([]any{meta["brief_ref"], meta["acceptance_ref"]}, inputs)
	command := map[string]string{"discovery": "research.source-page-v1", "verification": "research.source-support-v1", "experiment": "experiments.paired-mean-v1", "review": "research.candidate-review-v1", "delivery": "research.cycle-report-v1", "follow_up": "research.follow-up-v1"}[stage]
	if command == "" {
		return nil, Fail(422, "GATE_FAILED", "unsupported research stage")
	}
	contract := researchContract(command)
	if stage == "experiment" {
		x, err := load(tx, project, "Experiment", Str(params, "experiment_id"))
		if err != nil {
			return nil, err
		}
		contract = x["acceptance_contract"].(map[string]any)
	}
	task, err := s.createTask(tx, project, Object{"goal_id": goal["id"], "title": "研究阶段：" + stage, "task_type": "research_" + stage, "stage": stage, "dependency_task_ids": deps, "requirement_refs": goal["requirement_refs"], "input_refs": refs, "acceptance_contract": contract, "origin_problem_id": Arr(goal, "problem_ids")[0], "candidate_id": "work-" + key[:32], "stop_policy": Object{"wall_time_seconds": plan.WallTimeSeconds, "max_attempts": 2, "max_parallel_runs": 1, "stop_conditions": []any{"input drift", "work bound exhausted", "unknown effect", "Owner pause or cancel"}}})
	if err != nil {
		return nil, err
	}
	_, err = tx.Exec("INSERT INTO research_cycle_work(project,cycle,logical_key,plan_ref,stage,task,experiment,source_id,evidence_id,input_refs,input_hash,parameters,window_from,window_to,progress_record_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", project, cycle["id"], key, string(Bytes(meta["brief_ref"])), stage, task["id"], nullableText(Str(params, "experiment_id")), nullableText(Str(params, "source_id")), nullableText(Str(params, "evidence_id")), string(Bytes(refs)), Hash(refs), string(Bytes(params)), cycle["window_from"], cycle["window_to"], meta["progress_record_id"], Now())
	if err != nil {
		return nil, err
	}
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return nil, err
	}
	if _, err = s.createContext(tx, owner, project, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]}); err != nil {
		return nil, err
	}
	task, err = load(tx, project, "Task", Str(task, "id"))
	if err != nil {
		return nil, err
	}
	task, err = s.orchestrateTask(tx, project, task, Object{"action": "SUBMIT"})
	if err != nil {
		return nil, err
	}
	if err = s.event(tx, project, "Task", task, owner.ID, ID(), "TASK_CHANGED"); err != nil {
		return nil, err
	}
	return task, nil
}

func nullableText(value string) any {
	if value == "" {
		return nil
	}
	return value
}

func researchStageCapacity(tx *sql.Tx, project, cycle string, plan *MonitorPlan) (bool, error) {
	var count int
	err := tx.QueryRow("SELECT count(*) FROM research_cycle_work WHERE project=? AND cycle=?", project, cycle).Scan(&count)
	return count < plan.MaxTasks-1, err // The final immutable plan slot belongs to delivery.
}

func bindResearchMonitorCycle(tx *sql.Tx, project string, cycle, meta Object, plan *MonitorPlan) error {
	goal := meta["goal"].(map[string]any)
	var existingGoal, existingPlan string
	err := tx.QueryRow("SELECT goal,plan_ref FROM research_monitor_cycles WHERE project=? AND cycle=?", project, cycle["id"]).Scan(&existingGoal, &existingPlan)
	if err == nil {
		if existingGoal != Str(goal, "id") || existingPlan != string(Bytes(meta["brief_ref"])) {
			return Fail(412, "STALE_INPUT", "cycle belongs to another accepted monitor plan")
		}
		return nil
	}
	if err != sql.ErrNoRows {
		return err
	}
	if Hash(cycle["profile_ref"]) != Hash(plan.ProfileRef) {
		return Fail(412, "STALE_INPUT", "cycle profile differs from accepted monitor plan")
	}
	from, to, err := parseCycleWindow(Str(cycle, "window_from"), Str(cycle, "window_to"))
	if err != nil {
		return err
	}
	// A pre-existing manual cycle can be adopted only within the approved initial
	// lookback. Scheduled coalescing has already been bounded by createResearchCycle.
	if cycle["trigger"] != "SCHEDULE" && to.Sub(from) > time.Duration(plan.FirstLookbackSeconds)*time.Second {
		return Fail(422, "GATE_FAILED", "manual cycle exceeds accepted monitor window")
	}
	_, err = tx.Exec("INSERT INTO research_monitor_cycles(project,cycle,goal,plan_ref,created_at) VALUES(?,?,?,?,?)", project, cycle["id"], goal["id"], string(Bytes(meta["brief_ref"])), Now())
	return err
}

// One bounded domain step; the existing coordinator owns the only polling loop.
func (s *Service) advanceResearchProject(tx *sql.Tx, scheduler Principal, project string, now time.Time) error {
	var goalID string
	err := tx.QueryRow("SELECT compiled_goal FROM intent_plan_bindings WHERE project=? AND monitor_current=1", project).Scan(&goalID)
	if err == sql.ErrNoRows {
		return nil
	}
	if err != nil {
		return err
	}
	goal, err := load(tx, project, "Goal", goalID)
	if err != nil {
		return err
	}
	if goal["status"] != "ACTIVE" {
		return s.holdResearchMonitor(tx, scheduler, project, goal)
	}
	meta, plan, err := s.monitorSnapshot(tx, project, goalID, true)
	if err != nil {
		var raw string
		if e := tx.QueryRow("SELECT brief_ref FROM intent_plan_bindings WHERE project=? AND compiled_goal=? AND monitor_current=1", project, goalID).Scan(&raw); e != nil {
			return e
		}
		ref, e := Decode([]byte(raw))
		if e != nil {
			return e
		}
		// Cancellation must read the immutable historical approval even after its
		// profile inputs become stale. It grants no authority to run new work.
		artifact, e := version(tx, project, ref)
		if e != nil {
			return e
		}
		var approval []byte
		if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, artifact["storage_key"]).Scan(&approval); e != nil {
			return e
		}
		if Digest(approval) != Str(artifact, "content_hash") {
			return Fail(422, "CONTENT_HASH_MISMATCH", "historical monitor approval changed")
		}
		brief, e := parseGoalBrief(approval)
		if e != nil {
			return e
		}
		profile, e := singleton(tx, project, "ProjectProfile")
		if e != nil {
			return e
		}
		if brief.Monitor != nil && Hash(brief.Monitor.ProfileRef) != Hash(Ref(profile, "ProjectProfile")) {
			cancelled := Merge(Object{}, goal)
			cancelled["status"] = "CANCELLED"
			return s.holdResearchMonitor(tx, scheduler, project, cancelled, "Monitor profile changed; prior="+string(Bytes(brief.Monitor.ProfileRef))+" current="+string(Bytes(Ref(profile, "ProjectProfile")))+". Original results retained; renewed Owner plan required.")
		}
		return s.holdResearchMonitor(tx, scheduler, project, goal)
	}
	progress, err := load(tx, project, "NoProgressRecord", Str(meta, "progress_record_id"))
	if err != nil {
		return err
	}
	if progress["status"] == "DEFERRED_NO_PROGRESS" {
		return s.holdResearchMonitor(tx, scheduler, project, goal)
	}
	owner := meta["owner_principal"].(Principal)
	if err = s.resumeResearchMonitor(tx, owner, project, goal); err != nil {
		return err
	}
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return err
	}
	var cycle Object
	if id := Str(state, "active_cycle_id"); id != "" {
		cycle, err = load(tx, project, "ResearchCycle", id)
		if err != nil {
			return err
		}
		// An existing manual cycle is linked only to this approved current plan.
		if Hash(cycle["profile_ref"]) != Hash(plan.ProfileRef) {
			return Fail(412, "STALE_INPUT", "active cycle belongs to an older profile")
		}
	} else {
		started, err := time.Parse(time.RFC3339Nano, Str(meta, "monitor_started_at"))
		if err != nil {
			return err
		}
		if now.Before(started) {
			return nil
		}
		due := started
		var prior string
		err = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='ResearchCycle' ORDER BY json_extract(body,'$.created_at') DESC LIMIT 1", project).Scan(&prior)
		if err == nil {
			last, e := Decode([]byte(prior))
			if e != nil {
				return e
			}
			end, e := time.Parse(time.RFC3339Nano, Str(last, "window_to"))
			if e != nil {
				return e
			}
			period := time.Duration(plan.PeriodSeconds) * time.Second
			if now.Before(end.Add(period)) {
				return nil
			}
			due = end.Add(time.Duration(now.Sub(end)/period) * period)
		} else if err != sql.ErrNoRows {
			return err
		}
		cycle, err = s.createResearchCycle(tx, scheduler, project, Object{"trigger": "SCHEDULE", "profile_revision": plan.ProfileRef["revision"], "window_from": due.Add(-time.Duration(plan.FirstLookbackSeconds) * time.Second).UTC().Format(time.RFC3339Nano), "window_to": due.UTC().Format(time.RFC3339Nano)})
		if err != nil {
			return err
		}
		if err = s.event(tx, project, "ResearchCycle", cycle, scheduler.ID, ID(), "PROJECT_UPDATED"); err != nil {
			return err
		}
	}
	if err = bindResearchMonitorCycle(tx, project, cycle, meta, plan); err != nil {
		return err
	}
	return s.advanceResearchStages(tx, owner, project, meta, plan, cycle)
}

func (s *Service) holdResearchMonitor(tx *sql.Tx, p Principal, project string, goal Object, reason ...string) error {
	for _, raw := range Arr(goal, "task_ids") {
		task, err := load(tx, project, "Task", raw.(string))
		if err != nil {
			return err
		}
		if task["status"] == "ACCEPTED" || task["status"] == "CANCELLED" || task["status"] == "DEFERRED_NO_PROGRESS" || task["status"] == "NEEDS_REVALIDATION" {
			continue
		}
		var reason, control string
		err = tx.QueryRow("SELECT reason,action FROM orchestration_task_controls WHERE project=? AND task=?", project, task["id"]).Scan(&reason, &control)
		if err == nil && (goal["status"] != "CANCELLED" || control == "CANCEL") {
			continue
		}
		if err != nil && err != sql.ErrNoRows {
			return err
		}
		action := "PAUSE"
		if goal["status"] == "CANCELLED" {
			action = "CANCEL"
		}
		task, err = s.controlTask(tx, p, project, task, Object{"action": action, "reason": "MONITOR_LIFECYCLE_HOLD"}, ID())
		if err != nil {
			return err
		}
		if err = s.event(tx, project, "Task", task, p.ID, ID(), "TASK_CHANGED"); err != nil {
			return err
		}
	}
	if goal["status"] == "CANCELLED" {
		state, err := singleton(tx, project, "ProjectState")
		if err != nil {
			return err
		}
		if active := Str(state, "active_cycle_id"); active != "" {
			var boundGoal string
			if err = tx.QueryRow("SELECT goal FROM research_monitor_cycles WHERE project=? AND cycle=?", project, active).Scan(&boundGoal); err != nil && err != sql.ErrNoRows {
				return err
			}
			if boundGoal != Str(goal, "id") {
				return nil
			}
			summary := "Owner cancelled monitor; original results and unresolved effects retained."
			if len(reason) > 0 {
				summary = reason[0]
			}
			cycle, err := s.closeResearchCycle(tx, p, project, active, Object{"requested_status": "CANCELLED", "outcome_summary": summary})
			if err != nil {
				var fault *Fault
				if errors.As(err, &fault) && fault.Status == 409 {
					return nil
				} // Commit cancellation requests while reconciliation retains ownership.
				return err
			}
			if err = s.event(tx, project, "ResearchCycle", cycle, p.ID, ID(), "PROJECT_UPDATED"); err != nil {
				return err
			}
		}
		_, err = tx.Exec("UPDATE intent_plan_bindings SET monitor_current=0 WHERE project=? AND compiled_goal=? AND monitor_current=1", project, goal["id"])
		return err
	}
	return nil
}

func (s *Service) resumeResearchMonitor(tx *sql.Tx, p Principal, project string, goal Object) error {
	for _, raw := range Arr(goal, "task_ids") {
		var reason, action string
		err := tx.QueryRow("SELECT reason,action FROM orchestration_task_controls WHERE project=? AND task=?", project, raw).Scan(&reason, &action)
		if err == sql.ErrNoRows {
			continue
		}
		if err != nil {
			return err
		}
		if reason != "MONITOR_LIFECYCLE_HOLD" || action != "PAUSE" {
			continue
		}
		task, err := load(tx, project, "Task", raw.(string))
		if err != nil {
			return err
		}
		if task["status"] != "BLOCKED" {
			continue
		}
		if id := Str(task, "active_run_id"); id != "" {
			run, e := load(tx, project, "Run", id)
			if e != nil {
				return e
			}
			if !runTerminal(run) {
				continue
			}
			if e = effectsReconciled(tx, project, id); e != nil {
				continue
			}
		}
		task, err = s.orchestrateTask(tx, project, task, Object{"action": "RESUME"})
		if err != nil {
			var fault *Fault
			if errors.As(err, &fault) && fault.Status < 500 {
				continue
			}
			return err
		}
		if err = s.event(tx, project, "Task", task, p.ID, ID(), "TASK_CHANGED"); err != nil {
			return err
		}
	}
	return nil
}

func (s *Service) advanceResearchStages(tx *sql.Tx, owner Principal, project string, meta Object, plan *MonitorPlan, cycle Object) error {
	// Report materialization freezes this finite round. Later ticks cannot append
	// new stage facts behind an already-running independent report.
	var reportID string
	if err := tx.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND cycle=? AND stage='delivery'", project, cycle["id"]).Scan(&reportID); err == nil {
		report, err := load(tx, project, "Task", reportID)
		if err != nil {
			return err
		}
		if report["status"] == "ACCEPTED" {
			return s.closeReportedResearchCycle(tx, owner, project, meta, cycle, report)
		}
		return nil
	} else if err != sql.ErrNoRows {
		return err
	}
	profile := meta["profile"].(map[string]any)
	readyForReport := true
	deps := Empty()
	for _, raw := range Arr(profile, "source_configs") {
		config := raw.(map[string]any)
		var cursorRaw string
		err := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='SourceCursor' AND json_extract(body,'$.source_id')=? AND json_extract(body,'$.query_hash')=?", project, config["source_id"], Hash(config["query"])).Scan(&cursorRaw)
		if err != nil && err != sql.ErrNoRows {
			return err
		}
		cursor := Object{}
		if err == nil {
			cursor, err = Decode([]byte(cursorRaw))
			if err != nil {
				return err
			}
		}
		from, to := Str(cycle, "window_from"), Str(cycle, "window_to")
		if pending := Str(cursor, "pending_window_from"); pending != "" {
			from, to = pending, Str(cursor, "pending_window_to")
		} else if covered := Str(cursor, "covered_until"); covered != "" {
			from = covered
		}
		ft, e1 := time.Parse(time.RFC3339Nano, from)
		tt, e2 := time.Parse(time.RFC3339Nano, to)
		if e1 != nil || e2 != nil {
			return Fail(422, "GATE_FAILED", "invalid bounded source position")
		}
		if !ft.Before(tt) {
			continue
		}
		params := Object{"source_id": config["source_id"], "cursor_id": Str(cursor, "id"), "query_hash": Hash(config["query"]), "page_cursor_in": Str(cursor, "opaque_cursor"), "window_from": from, "window_to": to, "limit": plan.ItemsPerPage}
		key := stringsDigest(Hash([]any{"discovery", meta["brief_ref"], params}))
		var pages int
		if err = tx.QueryRow("SELECT count(*) FROM research_cycle_work WHERE project=? AND cycle=? AND stage='discovery' AND source_id=?", project, cycle["id"], config["source_id"]).Scan(&pages); err != nil {
			return err
		}
		var exists int
		if err = tx.QueryRow("SELECT count(*) FROM research_cycle_work WHERE project=? AND cycle=? AND logical_key=?", project, cycle["id"], key).Scan(&exists); err != nil {
			return err
		}
		if pages >= plan.PagesPerSource && exists == 0 {
			continue
		}
		if exists == 0 {
			capacity, e := researchStageCapacity(tx, project, Str(cycle, "id"), plan)
			if e != nil {
				return e
			}
			if !capacity {
				continue
			}
		}
		task, err := s.materializeResearchWork(tx, owner, project, meta, plan, cycle, "discovery", key, params, Empty(), Empty())
		if err != nil {
			return err
		}
		if config["enabled"] != true || Str(cursor, "id") == "" {
			if err = s.holdIntentResource(tx, owner, project, task, "RESEARCH_SOURCE_NOT_CONFIGURED", "来源未配置；本轮保留准确缺口，其余来源继续。"); err != nil {
				return err
			}
			continue
		}
		if task["status"] == "ACCEPTED" {
			if _, err = s.researchAcceptedTask(tx, project, task); err != nil {
				return err
			}
			deps = append(deps, task["id"])
		} else if task["status"] != "BLOCKED" && task["status"] != "FAILED" && task["status"] != "DEFERRED_NO_PROGRESS" {
			readyForReport = false
		}
	}
	candidatesReady, err := s.advanceResearchCandidates(tx, owner, project, meta, plan, cycle)
	if err != nil {
		return err
	}
	experimentsReady, err := s.advanceResearchExperiments(tx, owner, project, meta, plan, cycle)
	if err != nil {
		return err
	}
	if !readyForReport || !candidatesReady || !experimentsReady {
		return nil
	}
	key := stringsDigest(Hash([]any{"delivery", cycle["id"], meta["brief_ref"]}))
	report, err := s.materializeResearchWork(tx, owner, project, meta, plan, cycle, "delivery", key, Object{}, deps, Empty())
	if err != nil {
		return err
	}
	if report["status"] == "ACCEPTED" {
		if _, err = s.researchAcceptedTask(tx, project, report); err != nil {
			return err
		}
		return s.closeReportedResearchCycle(tx, owner, project, meta, cycle, report)
	}
	return nil
}

func stringsDigest(hash string) string { return fmt.Sprintf("%s", hash[len("sha256:"):]) }

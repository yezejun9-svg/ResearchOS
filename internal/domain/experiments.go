package domain

import (
	"context"
	"database/sql"
	"math/big"
	"time"
)

func init() {
	for _, name := range []string{"createExperiment", "registerExperiment", "recordExperimentResult", "listExperiment", "getExperiment"} {
		implemented[name] = true
	}
}
func experimentPlan(o Object) Object {
	p := Object{}
	for _, k := range []string{"cycle_id", "scope", "hypothesis", "candidate_ref", "baseline_refs", "input_refs", "metrics", "acceptance_contract", "stop_policy", "budget_policy_id", "measurement_mode"} {
		p[k] = o[k]
	}
	return p
}
func (s *Service) experimentCurrent(tx *sql.Tx, project string, o Object) error {
	if o["preregistration_hash"] != Hash(experimentPlan(o)) {
		return Fail(422, "CONTENT_HASH_MISMATCH", "frozen experiment plan changed")
	}
	for _, v := range append(append([]any{o["candidate_ref"]}, Arr(o, "baseline_refs")...), Arr(o, "input_refs")...) {
		if e := s.effective(tx, project, v.(map[string]any)); e != nil {
			return e
		}
	}
	c := o["acceptance_contract"].(map[string]any)
	if c["contract_hash"] != contractDigest(c) {
		return Fail(422, "GATE_FAILED", "frozen contract digest mismatch")
	}
	return nil
}
func (s *Service) createExperiment(tx *sql.Tx, project string, b Object) (Object, error) {
	o := Merge(Base(project), b)
	parent, e := load(tx, project, "BudgetPolicy", Str(b, "budget_policy_id"))
	if e != nil {
		return nil, e
	}
	policy, e := s.policy(tx, "BudgetPolicy", project, "EXPERIMENT", Str(o, "id"), Str(parent, "id"))
	if e != nil {
		return nil, e
	}
	o["budget_policy_id"] = policy["id"]
	if _, e = experimentCaseIDs(o); e != nil {
		return nil, Fail(422, "GATE_FAILED", e.Error())
	}
	seen := map[string]bool{}
	for _, v := range Arr(o, "metrics") {
		m := v.(map[string]any)
		id := Str(m, "metric_id")
		if seen[id] {
			return nil, Fail(422, "GATE_FAILED", "duplicate metric")
		}
		seen[id] = true
		if m["operator"] == "BETWEEN" && m["upper_target"] == nil {
			return nil, Fail(422, "GATE_FAILED", "BETWEEN needs upper target")
		}
	}
	Merge(o, Object{"status": "DRAFT", "registered_at": nil, "run_ids": Empty(), "results": Empty(), "outcome": nil, "acceptance_id": nil})
	o["preregistration_hash"] = Hash(experimentPlan(o))
	if e = s.experimentCurrent(tx, project, o); e != nil {
		return nil, e
	}
	return o, s.put(tx, "Experiment", o)
}
func (s *Service) registerExperiment(tx *sql.Tx, project, id string, b Object) (Object, error) {
	o, e := load(tx, project, "Experiment", id)
	if e != nil {
		return nil, e
	}
	if o["status"] != "DRAFT" {
		return nil, Fail(409, "STATE_CONFLICT", "new rules require a new experiment")
	}
	if b["expected_preregistration_hash"] != o["preregistration_hash"] {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "preregistration digest mismatch")
	}
	if e = s.experimentCurrent(tx, project, o); e != nil {
		return nil, e
	}
	bump(o)
	o["status"] = "REGISTERED"
	o["registered_at"] = Now()
	return o, s.put(tx, "Experiment", o)
}

// BindExperimentTask is an internal scheduler hook before claim; there is no second queue.
func (s *Service) BindExperimentTask(ctx context.Context, token, project, experiment, task string) error {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return e
	}
	if !p.HasRole("SCHEDULER") || !p.Allowed(project, "", "", false) {
		return Fail(403, "FORBIDDEN", "scheduler required")
	}
	x, e := load(tx, project, "Experiment", experiment)
	if e != nil {
		return e
	}
	if x["status"] != "REGISTERED" {
		return Fail(409, "STATE_CONFLICT", "registered experiment required")
	}
	t, e := load(tx, project, "Task", task)
	if e != nil {
		return e
	}
	if t["active_run_id"] != nil {
		return Fail(409, "STATE_CONFLICT", "bind before claim")
	}
	if e = s.experimentCurrent(tx, project, x); e != nil {
		return e
	}
	if e = experimentTaskInputs(x, t); e != nil {
		return e
	}
	if _, e = tx.Exec("INSERT INTO experiment_tasks(project,experiment,task,bound_at) VALUES(?,?,?,?)", project, experiment, task, Now()); e != nil {
		return e
	}
	return tx.Commit()
}
func experimentTaskInputs(x, t Object) error {
	inputs := map[string]bool{}
	for _, v := range Arr(t, "input_refs") {
		inputs[Hash(v)] = true
	}
	for _, v := range append(append([]any{x["candidate_ref"]}, Arr(x, "baseline_refs")...), Arr(x, "input_refs")...) {
		if !inputs[Hash(v)] {
			return Fail(422, "GATE_FAILED", "task must bind all candidate, baseline and data versions")
		}
	}
	return nil
}

// BeginExperiment rechecks an existing claimed Run immediately before worker execution.
func (s *Service) BeginExperiment(ctx context.Context, token, project, id, runID string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if !p.HasRole("SCHEDULER") || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "scheduler required")
	}
	r, e := load(tx, project, "Run", runID)
	if e != nil {
		return nil, e
	}
	if r["status"] != "QUEUED" {
		return nil, Fail(409, "STATE_CONFLICT", "current claimed run required")
	}
	x, e := s.beginExperimentTx(tx, p, project, id, runID)
	if e != nil {
		return nil, e
	}
	return x, tx.Commit()
}

func (s *Service) beginExperimentTx(tx *sql.Tx, p Principal, project, id, runID string) (Object, error) {
	x, e := load(tx, project, "Experiment", id)
	if e != nil {
		return nil, e
	}
	if x["status"] != "REGISTERED" && x["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "registered experiment required")
	}
	if e = s.experimentCurrent(tx, project, x); e != nil {
		return nil, e
	}
	r, e := load(tx, project, "Run", runID)
	if e != nil {
		return nil, e
	}
	if r["status"] != "QUEUED" {
		w, err := loadResearchWork(tx, project, Str(r, "task_id"))
		if err != nil || r["status"] != "RUNNING" || w.Stage != "experiment" || w.Experiment != id {
			return nil, Fail(409, "STATE_CONFLICT", "current claimed run required")
		}
		task, err := load(tx, project, "Task", w.Task)
		if err != nil {
			return nil, err
		}
		if _, _, err = s.monitorSnapshot(tx, project, Str(task, "goal_id"), true); err != nil {
			return nil, err
		}
	}
	var n int
	if e = tx.QueryRow("SELECT count(*) FROM experiment_tasks WHERE project=? AND experiment=? AND task=?", project, id, r["task_id"]).Scan(&n); e != nil || n != 1 {
		return nil, Fail(422, "GATE_FAILED", "task was not bound before claim")
	}
	t, e := load(tx, project, "Task", Str(r, "task_id"))
	if e != nil {
		return nil, e
	}
	if t["active_run_id"] != runID || r["context_bundle_id"] != t["context_bundle_id"] {
		return nil, Fail(412, "STALE_INPUT", "run epoch mismatch")
	}
	if e = experimentTaskInputs(x, t); e != nil {
		return nil, e
	}
	registered, e := time.Parse(time.RFC3339Nano, Str(x, "registered_at"))
	if e != nil {
		return nil, e
	}
	started, e := time.Parse(time.RFC3339Nano, Str(r, "created_at"))
	if e != nil || !started.After(registered) {
		return nil, Fail(422, "GATE_FAILED", "run must follow preregistration")
	}
	stop := x["stop_policy"].(map[string]any)
	max, _ := Num(stop, "max_attempts")
	if int64(len(Arr(x, "run_ids"))) >= max {
		return nil, Fail(422, "GATE_FAILED", "experiment attempt limit reached")
	}
	var active int
	if e = tx.QueryRow("SELECT count(*) FROM experiment_runs er JOIN domain_objects d ON d.project=er.project AND d.kind='Run' AND d.id=er.run WHERE er.project=? AND er.experiment=? AND json_extract(d.body,'$.status') NOT IN ('SETTLED','FAILED','CANCELLED')", project, id).Scan(&active); e != nil {
		return nil, e
	}
	parallel, _ := Num(stop, "max_parallel_runs")
	if int64(active) >= parallel {
		return nil, Fail(422, "GATE_FAILED", "experiment parallel limit reached")
	}
	if _, e = tx.Exec("INSERT INTO experiment_runs(project,experiment,run,started_at,preregistration_hash) VALUES(?,?,?,?,?)", project, id, runID, Now(), x["preregistration_hash"]); e != nil {
		return nil, e
	}
	bump(x)
	x["status"] = "RUNNING"
	x["run_ids"] = append(Arr(x, "run_ids"), runID)
	if e = s.put(tx, "Experiment", x); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Experiment", x, p.ID, ID(), "PROJECT_UPDATED"); e != nil {
		return nil, e
	}
	return x, nil
}
func metricStatus(m, r Object) (string, error) {
	n, e := Num(r, "sample_count")
	if e != nil {
		return "", e
	}
	if r["baseline"] == nil || r["candidate"] == nil || n == 0 {
		return "INCONCLUSIVE", nil
	}
	v, ok := new(big.Rat).SetString(Str(r, "candidate"))
	target, ok2 := new(big.Rat).SetString(Str(m, "target"))
	if !ok || !ok2 {
		return "", Fail(422, "GATE_FAILED", "decimal metric required")
	}
	cmp := v.Cmp(target)
	pass := false
	switch m["operator"] {
	case "LT":
		pass = cmp < 0
	case "LTE":
		pass = cmp <= 0
	case "EQ":
		pass = cmp == 0
	case "GTE":
		pass = cmp >= 0
	case "GT":
		pass = cmp > 0
	case "BETWEEN":
		upper, ok := new(big.Rat).SetString(Str(m, "upper_target"))
		if !ok {
			return "", Fail(422, "GATE_FAILED", "invalid upper target")
		}
		pass = cmp >= 0 && v.Cmp(upper) <= 0
	}
	if pass {
		return "PASS", nil
	}
	return "FAIL", nil
}
func (s *Service) recordExperimentResult(tx *sql.Tx, project, id string, b Object) (Object, error) {
	x, e := load(tx, project, "Experiment", id)
	if e != nil {
		return nil, e
	}
	if x["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "experiment has not run or is terminal")
	}
	if e = s.experimentCurrent(tx, project, x); e != nil {
		return nil, e
	}
	if Hash(x["run_ids"]) != Hash(b["run_ids"]) {
		return nil, Fail(422, "GATE_FAILED", "all runs must be retained")
	}
	receipt, e := s.experimentAcceptance(tx, project, x, Str(b, "acceptance_id"))
	if e != nil {
		return nil, e
	}
	// The independently checked sealed JSON is the observation source, never caller-supplied metrics.

	artifacts := Empty()
	for _, v := range Arr(receipt, "artifact_refs") {
		a, e := version(tx, project, v.(map[string]any))
		if e != nil {
			return nil, e
		}
		var raw []byte
		if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&raw); e != nil {
			return nil, e
		}
		if Digest(raw) != a["content_hash"] {
			return nil, Fail(422, "CONTENT_HASH_MISMATCH", "result bytes changed")
		}
		artifacts = append(artifacts, Object{"artifact": a, "bytes": raw})
	}
	observed, e := experimentObservation(artifacts)
	if e != nil {
		return nil, Fail(422, "GATE_FAILED", e.Error())
	}
	if observed["experiment_id"] != id || observed["preregistration_hash"] != x["preregistration_hash"] || Hash(observed["results"]) != Hash(b["results"]) || observed["outcome"] != b["outcome"] {
		return nil, Fail(422, "GATE_FAILED", "metrics differ from independently verified observations")
	}
	metrics := map[string]Object{}
	for _, v := range Arr(x, "metrics") {
		m := v.(map[string]any)
		metrics[Str(m, "metric_id")] = m
	}
	if len(Arr(b, "results")) != len(metrics) {
		return nil, Fail(422, "GATE_FAILED", "no metric deletion")
	}
	missing, failed := false, false
	for _, v := range Arr(b, "results") {
		r := v.(map[string]any)
		m, ok := metrics[Str(r, "metric_id")]
		if !ok {
			return nil, Fail(422, "GATE_FAILED", "unknown or duplicate metric")
		}
		delete(metrics, Str(r, "metric_id"))
		status, e := metricStatus(m, r)
		if e != nil {
			return nil, e
		}
		if r["status"] != status {
			return nil, Fail(422, "GATE_FAILED", "metric status inconsistent with frozen threshold")
		}
		if m["mandatory"] == true {
			missing = missing || status == "INCONCLUSIVE"
			failed = failed || status == "FAIL"
		}
	}
	if missing && b["outcome"] != "INCONCLUSIVE" || !missing && failed && b["outcome"] == "IMPROVED" {
		return nil, Fail(422, "GATE_FAILED", "missing data or failed hard gate cannot imply improvement")
	}
	bump(x)
	x["results"] = b["results"]
	x["outcome"] = b["outcome"]
	x["acceptance_id"] = receipt["id"]
	x["status"] = "COMPLETED"
	if b["outcome"] == "INCONCLUSIVE" {
		x["status"] = "INCONCLUSIVE"
	}
	return x, s.put(tx, "Experiment", x)
}

// Recheck the current acceptance graph whenever experimental results are used.
func (s *Service) experimentAcceptance(tx *sql.Tx, project string, x Object, acceptanceID string) (Object, error) {
	if e := s.experimentCurrent(tx, project, x); e != nil {
		return nil, e
	}
	receipt, e := load(tx, project, "AcceptanceReceipt", acceptanceID)
	if e != nil {
		return nil, e
	}
	if receipt["verdict"] != "PASS" || receipt["receipt_hash"] != Receipt(receipt) || receipt["measurement_mode"] != x["measurement_mode"] {
		return nil, Fail(422, "GATE_FAILED", "valid independent receipt required")
	}
	ref := receipt["subject_ref"].(map[string]any)
	if ref["entity_type"] != "Task" {
		return nil, Fail(422, "GATE_FAILED", "result verification task required")
	}
	t, e := load(tx, project, "Task", Str(ref, "id"))
	if e != nil {
		return nil, e
	}
	if t["status"] != "ACCEPTED" || t["acceptance_id"] != receipt["id"] || Hash(t["acceptance_contract"]) != Hash(x["acceptance_contract"]) {
		return nil, Fail(422, "GATE_FAILED", "frozen experiment verification contract required")
	}
	if e = s.acceptedTaskBinding(tx, project, t); e != nil {
		return nil, e
	}
	if e = s.taskContext(tx, project, t); e != nil {
		return nil, e
	}
	if e = retentionIndependent(tx, t, receipt); e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(receipt["policy_revision"]) != Hash(state["policy_revision"]) {
		return nil, Fail(412, "STALE_INPUT", "policy changed")
	}
	root, e := authorityRoot(tx, Str(receipt, "verifier_principal_id"))
	if e != nil {
		return nil, e
	}
	found := false
	for _, v := range Arr(x, "run_ids") {
		r, e := load(tx, project, "Run", v.(string))
		if e != nil {
			return nil, e
		}
		author, e := authorityRoot(tx, Str(r, "executor_principal_id"))
		if e != nil {
			return nil, e
		}
		if author == root {
			return nil, Fail(403, "FORBIDDEN", "experiment executor cannot accept results")
		}
		if r["id"] == receipt["run_id"] {
			found = true
		}
		if r["status"] != "SETTLED" {
			return nil, Fail(422, "GATE_FAILED", "framework run failure is not candidate no improvement")
		}
	}
	if !found {
		return nil, Fail(422, "GATE_FAILED", "receipt run not part of experiment")
	}
	return receipt, nil
}

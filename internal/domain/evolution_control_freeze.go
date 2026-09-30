//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"researchos.local/research-os/evaluation/evolution"
	"sort"
)

type controlCurrentNames struct {
	Project, Candidate, Task, Run, Experiment, Goal, Retention, State string
	Verifier, Executor, Author, Release                               string
	Epoch                                                             int64
	Holdout, Plan, Contract                                           string
	Schema                                                            string
	Rows                                                              upgradeData
}

func (a *currentControlAuthority) independentVerifier(tx *sql.Tx, id string, n *controlCurrentNames) error {
	p, err := evolutionCurrentPrincipal(tx, id)
	if err != nil || p.DeviceID != "" || !p.HasRole("VERIFIER") || !protectedAllowed(p, a.project) {
		return fmt.Errorf("CONTROL_CURRENT_RESTRICTED_LOCAL_VERIFIER")
	}
	root, err := authorityRoot(tx, id)
	if err != nil {
		return err
	}
	for _, other := range []string{n.Executor, n.Author, n.Release} {
		r, e := authorityRoot(tx, other)
		if e != nil {
			return e
		}
		if root == r {
			return fmt.Errorf("CONTROL_CURRENT_VERIFIER_AUTHORITY_INTERSECTION")
		}
	}
	return nil
}

func (a *currentControlAuthority) deriveNames(tx *sql.Tx, req evolution.ControlCurrentRequest) (*controlCurrentNames, error) {
	n := &controlCurrentNames{Project: a.project, Candidate: req.CandidateID, Task: req.TaskID, Run: req.RunID}
	x, err := load(tx, a.project, "SystemCandidate", n.Candidate)
	if err != nil {
		return nil, err
	}
	h, err := a.s.evolutionCurrent(tx, a.project, x)
	if err != nil {
		return nil, err
	}
	current, _ := h["current_control"].(map[string]any)
	if current["session_id"] != a.id || x["status"] != "EVALUATING" || Hash(x["stable_artifact_ref"]) != Hash(a.stableRef) || Hash(x["candidate_artifact_ref"]) != Hash(a.candidateRef) {
		return nil, fmt.Errorf("CONTROL_CURRENT_CANDIDATE_BINDING")
	}
	task, err := load(tx, a.project, "Task", n.Task)
	if err != nil {
		return nil, err
	}
	run, err := load(tx, a.project, "Run", n.Run)
	if err != nil {
		return nil, err
	}
	if task["active_run_id"] != n.Run || run["task_id"] != n.Task || run["status"] != "RUNNING" || len(Arr(task, "dependency_task_ids")) != 0 {
		return nil, fmt.Errorf("CONTROL_CURRENT_RUNNING_TASK_REQUIRED")
	}
	n.Epoch, _ = Num(run, "lease_epoch")
	n.Executor = Str(run, "executor_principal_id")
	n.Experiment = Str(x, "experiment_id")
	n.Goal = Str(task, "goal_id")
	n.Retention = Str(task, "no_progress_record_id")
	n.Release = Str(h, "release_principal")
	state, err := singleton(tx, a.project, "ProjectState")
	if err != nil {
		return nil, err
	}
	n.State = Str(state, "id")
	if err = tx.QueryRow("SELECT creator FROM evolution_candidates WHERE project=? AND candidate=?", a.project, n.Candidate).Scan(&n.Author); err != nil {
		return nil, err
	}
	var count int
	for _, query := range []string{
		"SELECT count(*) FROM evolution_tasks WHERE project=? AND candidate=? AND task=? AND phase='REGRESSION'",
	} {
		if err = tx.QueryRow(query, a.project, n.Candidate, n.Task).Scan(&count); err != nil || count != 1 {
			return nil, fmt.Errorf("CONTROL_CURRENT_TASK_BINDING")
		}
	}
	if err = tx.QueryRow("SELECT count(*) FROM experiment_runs WHERE project=? AND experiment=? AND run=?", a.project, n.Experiment, n.Run).Scan(&count); err != nil || count != 1 {
		return nil, fmt.Errorf("CONTROL_CURRENT_EXPERIMENT_BINDING")
	}
	exp, err := load(tx, a.project, "Experiment", n.Experiment)
	if err != nil || exp["status"] != "RUNNING" {
		return nil, fmt.Errorf("CONTROL_CURRENT_EXPERIMENT_RUNNING")
	}
	if err = tx.QueryRow("SELECT count(*) FROM evolution_executions WHERE project=? AND candidate=?", a.project, n.Candidate).Scan(&count); err != nil || count != 0 {
		return nil, fmt.Errorf("CONTROL_CURRENT_EXECUTION_ALREADY_STARTED")
	}
	frozen, present, err := evolutionHoldoutEntry(tx, a.project, n.Candidate, "HOLDOUT_FROZEN")
	if err != nil || !present {
		return nil, fmt.Errorf("CONTROL_CURRENT_FROZEN_HOLDOUT_REQUIRED")
	}
	_, evaluated, err := evolutionHoldoutEntry(tx, a.project, n.Candidate, "HOLDOUT_EVALUATED")
	if err != nil || evaluated {
		return nil, fmt.Errorf("CONTROL_CURRENT_HOLDOUT_ALREADY_EXECUTED")
	}
	p, err := authenticate(tx, req.VerifierToken)
	if err != nil {
		return nil, err
	}
	n.Verifier = p.ID
	if frozen["verifier_id"] != p.ID {
		return nil, fmt.Errorf("CONTROL_CURRENT_HOLDOUT_VERIFIER")
	}
	if err = a.independentVerifier(tx, n.Verifier, n); err != nil {
		return nil, err
	}
	if err = a.s.taskContextForRun(tx, a.project, run); err != nil {
		return nil, err
	}
	if err = a.s.evolutionHostContract(tx, a.project, h, task["acceptance_contract"].(map[string]any), "REGRESSION"); err != nil {
		return nil, err
	}
	n.Holdout, n.Plan, n.Contract = Hash(frozen), Hash(evolutionPlan(x)), Hash(task["acceptance_contract"])
	n.Rows, err = controlCurrentRows(tx)
	if err != nil {
		return nil, err
	}
	n.Schema, err = controlSchemaHash(tx)
	return n, err
}

func (s *Service) freezeCurrentControl(ctx context.Context, a *currentControlAuthority, req evolution.ControlCurrentRequest) (evolution.ControlCurrentReply, error) {
	a.mu.Lock()
	defer a.mu.Unlock()
	var out evolution.ControlCurrentReply
	if !a.registered || a.frozen != nil {
		return out, fmt.Errorf("CONTROL_CURRENT_FREEZE_SINGLE_USE")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	if err = a.currentOwner(tx); err != nil {
		tx.Rollback()
		return out, err
	}
	n, err := a.deriveNames(tx, req)
	tx.Rollback()
	if err != nil {
		return out, err
	}
	_, b0, err := controlReadPrivateSnapshot(ctx, a.store, a.project, a.b0)
	if err != nil {
		return out, err
	}
	defer b0.Close()
	b0rows, err := controlCurrentRows(b0)
	if err != nil {
		return out, err
	}
	budgetID, err := controlPreparationBudget(b0rows, n)
	if err != nil {
		return out, err
	}
	businessRows := upgradeData{"domain_objects": []Object{}}
	for _, row := range n.Rows["domain_objects"] {
		if !(row["project"] == n.Project && row["kind"] == "BudgetPolicy" && row["id"] == budgetID) {
			businessRows["domain_objects"] = append(businessRows["domain_objects"], row)
		}
	}
	if err = controlBusinessReadsetUnchanged(b0rows, businessRows, a.project, a.cycle); err != nil {
		return out, err
	}
	raw, err := controlCurrentSnapshot(ctx, s.DB)
	if err != nil {
		return out, err
	}
	snapshot, err := controlSavePrivateSnapshot(ctx, a.store, a.project, a.id, "G0", raw)
	if err != nil {
		return out, err
	}
	_, g0, err := controlReadPrivateSnapshot(ctx, a.store, a.project, snapshot)
	if err != nil {
		return out, err
	}
	defer g0.Close()
	captured, err := controlCurrentRows(g0)
	if err != nil || Hash(captured) != Hash(n.Rows) {
		return out, fmt.Errorf("CONTROL_CURRENT_FREEZE_MOVED")
	}
	tx, err = s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	if err = a.currentOwner(tx); err != nil {
		return out, err
	}
	delta, err := a.validatePreparation(tx, b0rows, n)
	if err != nil {
		return out, err
	}
	hash, err := evolution.ControlDatabaseHash(tx)
	if err != nil || hash != snapshot.Generation {
		return out, fmt.Errorf("CONTROL_CURRENT_FREEZE_GENERATION_MOVED")
	}
	a.g0, a.frozen, a.preparationDelta = snapshot, n, delta
	out = controlCurrentReply(a, "FREEZE")
	out.DeltaHash = Hash(delta)
	return out, nil
}

func controlBusinessReadsetUnchanged(before, after upgradeData, project, cycle string) error {
	selectRows := func(all upgradeData) []Object {
		out := []Object{}
		for _, r := range all["domain_objects"] {
			k, p := Str(r, "kind"), Str(r, "project")
			selected := p == project && (k == "ProjectProfile" || k == "ProjectState" || k == "BudgetPolicy" || k == "RunPolicy" || k == "AcceptancePolicy" || k == "SourceCursor" || k == "ResearchCycle" && r["id"] == cycle) || p == "" && (k == "BudgetPolicy" || k == "RunPolicy")
			if !selected {
				continue
			}
			copy := copyObject(r)
			if k == "ProjectState" {
				b, _ := Decode([]byte(Str(r, "body")))
				delete(b, "event_sequence")
				delete(b, "revision")
				delete(b, "updated_at")
				copy["body"] = string(Bytes(b))
				delete(copy, "revision")
			}
			out = append(out, copy)
		}
		return out
	}
	if controlRowSetHash(selectRows(before)) != controlRowSetHash(selectRows(after)) {
		old := map[string]Object{}
		for _, row := range selectRows(before) {
			old[controlEntityKey(row)] = row
		}
		for _, row := range selectRows(after) {
			prior := old[controlEntityKey(row)]
			if Hash(prior) == Hash(row) {
				delete(old, controlEntityKey(row))
				continue
			}
			fields := []string{}
			for k, value := range row {
				if Hash(value) == Hash(prior[k]) {
					continue
				}
				if k == "body" {
					left, _ := Decode([]byte(Str(prior, "body")))
					right, _ := Decode([]byte(Str(row, "body")))
					for field, v := range right {
						if Hash(v) != Hash(left[field]) {
							fields = append(fields, "body."+field)
						}
					}
				} else {
					fields = append(fields, k)
				}
			}
			sort.Strings(fields)
			return fmt.Errorf("CONTROL_CURRENT_BUSINESS_READSET_CHANGED:%s:%s:%v:%s:%s", Str(row, "kind"), Str(row, "id"), fields, Hash(prior), Hash(row))
		}
		return fmt.Errorf("CONTROL_CURRENT_BUSINESS_READSET_CHANGED:REMOVED_ROWS:%d", len(old))
	}
	return nil
}

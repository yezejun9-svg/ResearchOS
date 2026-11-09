//go:build windows

package domain

import (
	"context"
	"database/sql"
	"errors"
)

// advanceIntentTasks is a bounded preflight inside the existing sole coordinator.
// It creates no second queue, never resumes a user-held or previously run Task,
// and never interprets a resolved resource request as restored authority.
func (c *RuntimeCoordinator) advanceIntentTasks(ctx context.Context) error {
	projects := map[string][]RuntimeCoordinatorRoute{}
	for _, route := range c.runtimeRoutes() {
		projects[route.ProjectID] = append(projects[route.ProjectID], route)
	}
	var failures []error
	for project, routes := range projects {
		tx, e := c.service.DB.BeginTx(ctx, nil)
		if e != nil {
			failures = append(failures, e)
			continue
		}
		if e = resourceWriteLock(tx); e == nil {
			e = c.advanceIntentProject(tx, project, routes)
		}
		if e == nil {
			e = tx.Commit()
		}
		tx.Rollback()
		if e != nil {
			failures = append(failures, e)
		}
	}
	return errors.Join(failures...)
}

func (c *RuntimeCoordinator) advanceIntentProject(tx *sql.Tx, project string, routes []RuntimeCoordinatorRoute) error {
	s := c.service
	p, e := resourcePrincipal(tx, c.schedulerCredential(project), project, "SCHEDULER")
	if e != nil {
		return e
	}
	rows, e := tx.Query("SELECT t.body,b.actor FROM domain_objects t JOIN intent_plan_bindings b ON b.project=t.project AND (b.planning_task=t.id OR b.compiled_goal=json_extract(t.body,'$.goal_id')) WHERE t.project=? AND t.kind='Task' AND json_extract(t.body,'$.status') IN ('READY','BLOCKED') AND json_extract(t.body,'$.active_run_id') IS NULL AND NOT EXISTS(SELECT 1 FROM orchestration_task_controls x WHERE x.project=t.project AND x.task=t.id)", project)
	if e != nil {
		return e
	}
	type candidate struct {
		task  Object
		actor string
	}
	candidates := []candidate{}
	for rows.Next() {
		var raw, actor string
		if e = rows.Scan(&raw, &actor); e != nil {
			rows.Close()
			return e
		}
		task, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return err
		}
		candidates = append(candidates, candidate{task, actor})
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, candidate := range candidates {
		task := candidate.task
		goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
		if e != nil {
			return e
		}
		if goal["status"] != "ACTIVE" {
			continue
		}
		owner, ownerErr := s.planningOwner(tx, project, candidate.actor)
		contextErr := s.taskContext(tx, project, task)
		if task["task_type"] == "intent_planning" {
			if _, err := s.planningSnapshot(tx, project, task); err != nil {
				contextErr = err
			}
		} else {
			if _, err := s.compiledPlanningSnapshot(tx, project, goal); err != nil {
				contextErr = err
			}
		}
		ready, dependencyErr := s.dependenciesReady(tx, project, task)
		if ownerErr != nil || contextErr != nil || dependencyErr != nil {
			if e = s.holdIntentResource(tx, p, project, task, "INTENT_INPUT_CHANGED", "原始意图、规划来源或当前授权已变化，需显式重验后继续。"); e != nil {
				return e
			}
			continue
		}
		if !ready {
			continue
		}
		var runtime Object
		for _, route := range routes {
			current, err := load(tx, project, "RuntimeRegistration", route.RuntimeID)
			if err != nil {
				continue
			}
			admission, err := s.currentRuntimeAdmission(tx, project, task, current, []any{"start"}, "claim")
			if err != nil {
				continue
			}
			profile, _ := admission["profile"].(map[string]any)
			if profile == nil || profile["command_id"] != route.CommandID || !runtimeExecutorAllowed(tx, route.ExecutorID, project, Str(task, "id")) {
				continue
			}
			if task["task_type"] == "research_discovery" && !c.researchSourceAvailable(tx, project, task, route, profile) {
				continue
			}
			executor, err := authenticate(tx, route.ExecutorToken)
			if err != nil || executor.ID != route.ExecutorID || !executor.HasRole("EXECUTOR") {
				continue
			}
			independent, err := intentIndependentVerifier(tx, project, route.ExecutorID)
			if err != nil {
				return err
			}
			if !independent {
				continue
			}
			runtime = current
			break
		}
		if runtime == nil {
			if e = s.holdIntentResource(tx, p, project, task, "INTENT_PLANNER_UNAVAILABLE", "等待当前合格且获用途授权的运行器与独立验证者；资源请求被关闭不代表能力恢复。"); e != nil {
				return e
			}
			continue
		}
		dependencyRefs, e := s.dependencyVector(tx, project, task)
		if e != nil {
			return e
		}
		if e = s.dependencyContext(tx, project, task, dependencyRefs); e != nil {
			state, err := singleton(tx, project, "ProjectState")
			if err != nil {
				return err
			}
			if _, err = s.createContext(tx, owner, project, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]}); err != nil {
				return err
			}
			task, err = load(tx, project, "Task", Str(task, "id"))
			if err != nil {
				return err
			}
		}
		if task["status"] == "BLOCKED" {
			task, e = s.orchestrateTask(tx, project, task, Object{"action": "RESUME"})
			if e != nil {
				return e
			}
			if e = s.event(tx, project, "Task", task, p.ID, ID(), "TASK_CHANGED"); e != nil {
				return e
			}
		}
		// Close only this concrete missing-runtime request, with current real evidence.
		var resourceID string
		e = tx.QueryRow("SELECT id FROM domain_objects WHERE project=? AND kind='ResourceRequest' AND json_extract(body,'$.reason_code')=? AND json_extract(body,'$.status') IN ('OPEN','ACKNOWLEDGED')", project, "INTENT_PLANNER_UNAVAILABLE:"+Str(task, "id")).Scan(&resourceID)
		if e != nil && e != sql.ErrNoRows {
			return e
		}
		if e == nil {
			proof := []any{Ref(runtime, "RuntimeRegistration")}
			for _, id := range Arr(runtime, "qualification_ids") {
				r, err := load(tx, project, "AcceptanceReceipt", id.(string))
				if err != nil {
					return err
				}
				proof = append(proof, Ref(r, "AcceptanceReceipt"))
			}
			resolved, err := s.resolveResourceRequest(tx, p, project, resourceID, Object{"resolution_evidence_refs": proof, "reason": "Coordinator rechecked current native qualification, frozen route, purpose, executor and independent verifier"})
			if err != nil {
				return err
			}
			if err = s.event(tx, project, "ResourceRequest", resolved, p.ID, ID(), "RESOURCE_REQUESTED"); err != nil {
				return err
			}
		}
	}
	return nil
}

func intentIndependentVerifier(tx *sql.Tx, project, executor string) (bool, error) {
	root, e := authorityRoot(tx, executor)
	if e != nil {
		return false, e
	}
	rows, e := tx.Query("SELECT DISTINCT p.id FROM auth_principals p JOIN auth_grants g ON g.principal=p.id WHERE p.revoked=0 AND g.project=? AND g.task='' AND g.run='' AND EXISTS(SELECT 1 FROM json_each(p.roles) WHERE value='VERIFIER')", project)
	if e != nil {
		return false, e
	}
	ids := []string{}
	for rows.Next() {
		var id string
		if e = rows.Scan(&id); e != nil {
			rows.Close()
			return false, e
		}
		ids = append(ids, id)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return false, e
	}
	for _, id := range ids {
		other, e := authorityRoot(tx, id)
		if e != nil {
			return false, e
		}
		if root != other {
			return true, nil
		}
	}
	return false, nil
}

func (s *Service) holdIntentResource(tx *sql.Tx, p Principal, project string, task Object, code, summary string) error {
	if task["status"] != "BLOCKED" {
		task["status"] = "BLOCKED"
		if e := bump(task); e != nil {
			return e
		}
		if e := s.put(tx, "Task", task); e != nil {
			return e
		}
		if e := s.event(tx, project, "Task", task, p.ID, ID(), "TASK_CHANGED"); e != nil {
			return e
		}
	}
	var count int
	if e := tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResourceRequest' AND json_extract(body,'$.reason_code')=? AND json_extract(body,'$.status') IN ('OPEN','ACKNOWLEDGED')", project, code+":"+Str(task, "id")).Scan(&count); e != nil {
		return e
	}
	if count == 0 {
		return s.intentResource(tx, p, project, task, "PERMISSION", code, summary, Empty())
	}
	return nil
}

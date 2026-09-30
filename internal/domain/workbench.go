package domain

import (
	"database/sql"
	"errors"
	"fmt"
	"time"
)

var workbenchOperations = map[string]bool{
	"getProgressProjection": true, "createMilestoneRelease": true,
	"listMilestoneRelease": true, "getMilestoneRelease": true,
	"listNotification": true, "getNotification": true,
	"markNotificationRead": true, "streamEvents": true,
}

func init() {
	for name := range workbenchOperations {
		implemented[name] = true
	}
}

// Called by the existing recursive visibility gate for each object. ID-only
// relations need the same classification checks as explicit VersionRefs.
func (s *Service) workbenchVisible(tx *sql.Tx, p Principal, project string, o Object, seen map[string]bool) bool {
	if o["channel"] == "IN_APP" && o["recipient_id"] != nil && o["recipient_id"] != p.ID {
		return false
	}
	for field, value := range o {
		kind := idTargets[field]
		if kind == "" || value == nil {
			continue
		}
		values := []any{value}
		if a, ok := value.([]any); ok {
			values = a
		}
		for _, v := range values {
			id, ok := v.(string)
			if !ok {
				return false
			}
			key := "relation:" + Hash([]any{project, kind, id})
			if seen[key] {
				continue
			}
			seen[key] = true
			related, e := load(tx, project, kind, id)
			if e != nil {
				var fault *Fault
				if errors.As(e, &fault) && fault.Status == 404 {
					continue // Domain reference validation owns unknown-ID errors.
				}
				return false
			}
			if !s.visibleGraph(tx, p, project, related, seen) {
				return false
			}
		}
	}
	return true
}

func workbenchObjects(tx *sql.Tx, project, kind string) ([]Object, error) {
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind=? ORDER BY id", project, kind)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	objects := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			return nil, e
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
		objects = append(objects, o)
	}
	return objects, rows.Err()
}

// Plan revisions are rebuildable from immutable Task versions: initial revision
// 1, then one increment per creation or change to these planning fields. Runtime
// status, assigned executor, outputs and verification timestamps do not revise a
// plan. No writable projection or second Task state is introduced.
func workbenchPlan(tx *sql.Tx, project string, visible map[string]bool) (int64, error) {
	rows, e := tx.Query("SELECT id,body FROM domain_versions WHERE project=? AND kind='Task' ORDER BY id,revision", project)
	if e != nil {
		return 0, e
	}
	defer rows.Close()
	last := map[string]string{}
	revision := int64(1)
	for rows.Next() {
		var id, raw string
		if e = rows.Scan(&id, &raw); e != nil {
			return 0, e
		}
		if !visible[id] {
			continue
		}
		t, e := Decode([]byte(raw))
		if e != nil {
			return 0, e
		}
		plan := Object{}
		for _, field := range []string{"title", "stage", "goal_id", "requirement_refs", "input_refs", "dependency_task_ids", "stop_policy"} {
			plan[field] = t[field]
		}
		if c, ok := t["acceptance_contract"].(map[string]any); ok {
			plan["contract_hash"] = c["contract_hash"]
		}
		h := Hash(plan)
		if h != last[id] {
			revision++
			last[id] = h
		}
	}
	return revision, rows.Err()
}

func (s *Service) workbenchProgress(tx *sql.Tx, p Principal, project string) (Object, error) {
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	counts := map[string]Object{}
	stages := Empty()
	for _, stage := range []string{"discovery", "verification", "experiment", "review", "delivery", "follow_up"} {
		c := Object{"stage": stage, "planned": 0, "accepted": 0, "pending_review": 0, "blocked": 0, "active": 0}
		counts[stage] = c
		stages = append(stages, c)
	}
	tasks, e := workbenchObjects(tx, project, "Task")
	if e != nil {
		return nil, e
	}
	visible := map[string]bool{}
	refs, resources := Empty(), Empty()
	seen := map[string]bool{}
	var last any
	var lastTime time.Time
	planned := 0
	for _, task := range tasks {
		if !s.visible(tx, p, project, task) {
			continue
		}
		visible[Str(task, "id")] = true
		c := counts[Str(task, "stage")]
		if c == nil {
			return nil, Fail(500, "INTERNAL_ERROR", "invalid authoritative task stage")
		}
		c["planned"] = c["planned"].(int) + 1
		planned++
		field := ""
		switch task["status"] {
		case "EXECUTION_REPORTED", "VERIFYING":
			field = "pending_review"
		case "BLOCKED", "FAILED", "NEEDS_REVALIDATION", "DEFERRED_NO_PROGRESS":
			field = "blocked"
		case "RUNNING":
			field = "active"
		case "ACCEPTED":
			receipt, err := s.workbenchTaskAcceptance(tx, project, task)
			if err != nil {
				var fault *Fault
				if !errors.As(err, &fault) {
					return nil, err
				}
				field = "blocked"
			} else {
				field = "accepted"
				at, err := time.Parse(time.RFC3339Nano, Str(receipt, "created_at"))
				if err != nil {
					return nil, err
				}
				if at.After(lastTime) {
					lastTime, last = at, receipt["created_at"]
				}
				for _, ref := range Arr(receipt, "artifact_refs") {
					if !seen[Hash(ref)] && s.visible(tx, p, project, ref) {
						seen[Hash(ref)] = true
						refs = append(refs, ref)
					}
				}
			}
		}
		if field != "" {
			c[field] = c[field].(int) + 1
		}
	}
	revision, e := workbenchPlan(tx, project, visible)
	if e != nil {
		return nil, e
	}
	requests, e := workbenchObjects(tx, project, "ResourceRequest")
	if e != nil {
		return nil, e
	}
	for _, request := range requests {
		if (request["status"] == "OPEN" || request["status"] == "ACKNOWLEDGED") && s.visible(tx, p, project, request) {
			resources = append(resources, request["id"])
		}
	}
	var release any
	if id := Str(state, "latest_release_id"); id != "" {
		if r, err := s.readObject(tx, p, project, "MilestoneRelease", id); err == nil {
			release = r["id"]
		}
	}
	var note any
	if revision > 1 {
		note = fmt.Sprintf("计划修订 %d；当前计划 %d 项。新增任务或计划字段变化推进修订，执行与待评审不计作已验收。", revision, planned)
	}
	return Object{"id": "progress-" + project, "project_id": project, "revision": state["revision"], "created_at": state["created_at"], "updated_at": state["updated_at"], "as_of_event_sequence": state["event_sequence"], "project_state_revision": state["revision"], "plan_revision": revision, "stages": stages, "last_effective_progress_at": last, "recent_artifact_refs": refs, "latest_release_id": release, "open_resource_request_ids": resources, "plan_change_note": note}, nil
}

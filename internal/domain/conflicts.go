package domain

import (
	"database/sql"
)

// Integration requires a real task with valid context and sealed candidate evidence.
func (s *Service) changeConflicts(tx *sql.Tx, project string, proposal Object) ([]any, error) {
	chosen := map[string]bool{}
	integration := false
	for _, v := range Arr(proposal, "edits") {
		edit := v.(map[string]any)
		r := edit["target_ref"].(map[string]any)
		if r["entity_type"] != "ProjectState" || edit["field"] != "current_decision_refs" {
			continue
		}
		value, e := s.artifactJSON(tx, project, edit["proposed_value_artifact_ref"].(map[string]any))
		if e != nil {
			return nil, e
		}
		for _, v := range value.([]any) {
			chosen[Str(v.(map[string]any), "id")] = true
		}
		a, e := version(tx, project, edit["proposed_value_artifact_ref"].(map[string]any))
		if e != nil {
			return nil, e
		}
		for _, v := range Arr(a, "input_refs") {
			ref := v.(map[string]any)
			if ref["entity_type"] == "Task" {
				task, e := version(tx, project, ref)
				if e != nil {
					return nil, e
				}
				if task["task_type"] == "integration" && s.effective(tx, project, ref) == nil && s.taskContext(tx, project, task) == nil {
					integration = true
				}
			}
		}
	}
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='Conflict' AND json_extract(body,'$.status')='OPEN' ORDER BY id", project)
	if e != nil {
		return nil, e
	}
	conflicts := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return nil, e
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		conflicts = append(conflicts, o)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	ids := Empty()
	for _, c := range conflicts {
		matched := false
		root := ""
		for _, v := range Arr(c, "subject_refs") {
			r := v.(map[string]any)
			if r["entity_type"] != "DecisionReceipt" {
				return nil, Fail(409, "STATE_CONFLICT", "unresolved non-decision conflict")
			}
			var lineage string
			if e = tx.QueryRow("SELECT root_id FROM decision_lineage WHERE project=? AND receipt_id=?", project, r["id"]).Scan(&lineage); e != nil {
				return nil, e
			}
			if root != "" && root != lineage {
				return nil, Fail(409, "STATE_CONFLICT", "unrelated decision conflict")
			}
			root = lineage
			matched = matched || chosen[Str(r, "id")]
		}
		if !matched || !integration {
			return nil, Fail(409, "STATE_CONFLICT", "conflict requires an explicit integration task and chosen candidate")
		}
		ids = append(ids, c["id"])
	}
	return ids, nil
}

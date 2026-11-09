package domain

import "database/sql"

// Only a validated change of input versions selects a new origin key. Existing
// records remain durable, so renaming a Task/Goal or session cannot reset them.
func (s *Service) progressForInputs(tx *sql.Tx, project string, t Object) (Object, error) {
	old, e := load(tx, project, "NoProgressRecord", Str(t, "no_progress_record_id"))
	if e != nil {
		return nil, e
	}
	inputHash := Hash(t["input_refs"])
	if old["input_hash"] == inputHash {
		return old, nil
	}
	key := Hash([]any{old["origin_problem_id"], old["candidate_id"], inputHash})
	var raw string
	e = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='NoProgressRecord' AND json_extract(body,'$.key_hash')=?", project, key).Scan(&raw)
	var next Object
	if e == sql.ErrNoRows {
		next = Merge(Base(project), Object{"origin_problem_id": old["origin_problem_id"], "candidate_id": old["candidate_id"], "input_hash": inputHash, "key_hash": key, "same_failure_count": 0, "no_progress_iterations": 0, "best_accepted_artifact_ref": nil, "last_effective_progress_at": nil, "resume_conditions": old["resume_conditions"], "status": "ACTIVE"})
		if e = s.put(tx, "NoProgressRecord", next); e != nil {
			return nil, e
		}
	} else if e != nil {
		return nil, e
	} else {
		next, e = Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
	}
	t["no_progress_record_id"] = next["id"]
	return next, nil
}

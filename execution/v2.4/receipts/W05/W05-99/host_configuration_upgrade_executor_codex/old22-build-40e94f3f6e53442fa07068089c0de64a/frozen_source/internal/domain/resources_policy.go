package domain

import "database/sql"

// policy_revision fences existing ContextBundles even for inherited GLOBAL
// policy changes, which do not otherwise alter a project's direct policy ref.
func (s *Service) resourcePolicyChanged(tx *sql.Tx, p Principal, project string) error {
	rows, e := tx.Query("SELECT project FROM domain_objects WHERE kind='ProjectState' AND (?='' OR project=?)", project, project)
	if e != nil {
		return e
	}
	projects := []string{}
	for rows.Next() {
		var id string
		if e = rows.Scan(&id); e != nil {
			rows.Close()
			return e
		}
		projects = append(projects, id)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, id := range projects {
		state, e := singleton(tx, id, "ProjectState")
		if e != nil {
			return e
		}
		revision, e := Num(state, "policy_revision")
		if e != nil {
			return e
		}
		if revision == 1<<63-1 {
			return Fail(409, "STATE_CONFLICT", "policy revision exhausted")
		}
		state["policy_revision"] = revision + 1
		if e = bump(state); e != nil {
			return e
		}
		if e = s.put(tx, "ProjectState", state); e != nil {
			return e
		}
		if project == "" {
			profile, e := singleton(tx, id, "ProjectProfile")
			if e != nil {
				return e
			}
			if e = s.event(tx, id, "ProjectProfile", profile, p.ID, ID(), "POLICY_CHANGED"); e != nil {
				return e
			}
		}
	}
	return nil
}

func (s *Service) effectiveRetryPolicy(tx *sql.Tx, project string) (Object, error) {
	profile, e := singleton(tx, project, "ProjectProfile")
	if e != nil {
		return nil, e
	}
	local, e := load(tx, project, "RunPolicy", Str(profile, "run_policy_id"))
	if e != nil {
		return nil, e
	}
	global, e := singleton(tx, "", "RunPolicy")
	if e != nil {
		return nil, e
	}
	for _, field := range []string{"same_failure_retry_limit", "no_progress_iteration_limit"} {
		a, e := Num(local, field)
		if e != nil {
			return nil, e
		}
		b, e := Num(global, field)
		if e != nil {
			return nil, e
		}
		if b < a {
			local[field] = b
		}
	}
	return local, nil
}

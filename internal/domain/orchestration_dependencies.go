package domain

import "database/sql"

// Dependency identity includes the accepted Task version and the receipt/output
// versions used by this run. Becoming ACCEPTED again is not the same input.
func (s *Service) dependencyVector(tx *sql.Tx, project string, t Object) ([]any, error) {
	ready, e := s.dependenciesReady(tx, project, t)
	if e != nil {
		return nil, e
	}
	if !ready {
		return nil, Fail(409, "STATE_CONFLICT", "dependency acceptance is no longer current")
	}
	refs := Empty()
	for _, v := range Arr(t, "dependency_task_ids") {
		dep, e := load(tx, project, "Task", v.(string))
		if e != nil {
			return nil, e
		}
		receipt, e := load(tx, project, "AcceptanceReceipt", Str(dep, "acceptance_id"))
		if e != nil {
			return nil, e
		}
		refs = append(refs, Ref(dep, "Task"), Ref(receipt, "AcceptanceReceipt"))
		refs = append(refs, Arr(receipt, "artifact_refs")...)
	}
	return refs, nil
}

func (s *Service) dependencyContext(tx *sql.Tx, project string, t Object, refs []any) error {
	bundle, e := load(tx, project, "ContextBundle", Str(t, "context_bundle_id"))
	if e != nil {
		return e
	}
	present := map[string]bool{}
	for _, v := range Arr(bundle, "version_vector") {
		present[Hash(v)] = true
	}
	for _, ref := range refs {
		if !present[Hash(ref)] {
			return Fail(412, "STALE_INPUT", "refresh context with exact accepted dependency inputs before dispatch")
		}
	}
	return nil
}

func (s *Service) runDependenciesCurrent(tx *sql.Tx, project string, t, r Object) ([]any, error) {
	current, e := s.dependencyVector(tx, project, t)
	if e != nil {
		return nil, e
	}
	var raw string
	if e = tx.QueryRow("SELECT snapshot FROM orchestration_run_dependencies WHERE project=? AND run=?", project, r["id"]).Scan(&raw); e != nil {
		return nil, Fail(422, "GATE_FAILED", "run has no frozen dependency vector")
	}
	frozen, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	if Hash(frozen["refs"]) != Hash(current) {
		return nil, Fail(412, "STALE_INPUT", "accepted dependency versions differ from this run's frozen inputs")
	}
	if e = s.dependencyContext(tx, project, t, current); e != nil {
		return nil, e
	}
	return current, nil
}

package domain

import (
	"database/sql"
	"errors"
)

// This is a retained independently qualified result, not a score or ranking.
// A valid existing selection wins: without a preregistered comparable metric,
// accepting another output does not establish that it is better.
func (s *Service) retainAcceptedResult(tx *sql.Tx, project string, task Object) error {
	current, e := load(tx, project, "Task", Str(task, "id"))
	if e != nil {
		return e
	}
	if Hash(current) != Hash(task) {
		return Fail(412, "STALE_INPUT", "retention requires the current accepted task version")
	}
	if task["status"] != "ACCEPTED" {
		return Fail(422, "GATE_FAILED", "retention requires current independent task acceptance")
	}
	if e := s.acceptedTaskBinding(tx, project, task); e != nil {
		return e
	}
	receipt, e := load(tx, project, "AcceptanceReceipt", Str(task, "acceptance_id"))
	if e != nil {
		return e
	}
	if e = retentionIndependent(tx, task, receipt); e != nil {
		return e
	}
	n, e := load(tx, project, "NoProgressRecord", Str(task, "no_progress_record_id"))
	if e != nil {
		return e
	}
	if n["input_hash"] != Hash(task["input_refs"]) || n["key_hash"] != Hash([]any{n["origin_problem_id"], n["candidate_id"], n["input_hash"]}) {
		return Fail(422, "GATE_FAILED", "retention origin and input key mismatch")
	}
	prior := Hash(n)
	if e = s.refreshRetainedProgress(tx, project, n); e != nil {
		return e
	}
	if n["best_accepted_artifact_ref"] == nil && len(Arr(receipt, "artifact_refs")) > 0 {
		n["best_accepted_artifact_ref"] = Arr(receipt, "artifact_refs")[0]
		n["last_effective_progress_at"] = receipt["created_at"]
	}
	if Hash(n) == prior {
		return nil
	}
	if e = bump(n); e != nil {
		return e
	}
	// Do not reset failure counters, reactivate a deferred key, or rewrite Task
	// output ownership. The existing NoProgressRecord remains the sole pointer.
	if e = s.put(tx, "NoProgressRecord", n); e != nil {
		return e
	}
	return s.event(tx, project, "NoProgressRecord", n, Str(receipt, "verifier_principal_id"), Str(receipt, "id"), "PROJECT_UPDATED")
}

func retentionIndependent(tx *sql.Tx, task, receipt Object) error {
	subject, _ := receipt["subject_ref"].(map[string]any)
	verifier := Str(receipt, "verifier_principal_id")
	if receipt["verdict"] != "PASS" || receipt["receipt_hash"] != Receipt(receipt) || verifier == "" || subject["entity_type"] != "Task" || subject["id"] != task["id"] || len(Arr(receipt, "executor_principal_ids")) == 0 {
		return Fail(422, "GATE_FAILED", "retention receipt is not an independent passing task receipt")
	}
	if verifier == Str(task, "assigned_principal_id") {
		return Fail(403, "FORBIDDEN", "assigned executor cannot approve retained output")
	}
	for _, executor := range Arr(receipt, "executor_principal_ids") {
		if executor == verifier {
			return Fail(403, "FORBIDDEN", "executor cannot approve retained output")
		}
		verifierRoot, e := authorityRoot(tx, verifier)
		if e != nil {
			return e
		}
		executorRoot, e := authorityRoot(tx, executor.(string))
		if e != nil {
			return e
		}
		if verifierRoot == executorRoot {
			return Fail(403, "FORBIDDEN", "delegated executor authority cannot approve retained output")
		}
	}
	return nil
}

// Reuse the current acceptance/contribution graph, including its established
// stale-content revalidation proof path. Historical receipt existence alone is
// insufficient; it must still bind a current ACCEPTED task on this exact key.
func (s *Service) retainedProgressQualified(tx *sql.Tx, project string, n, ref Object) (bool, error) {
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.no_progress_record_id')=? AND json_extract(body,'$.status')='ACCEPTED' ORDER BY id", project, n["id"])
	if e != nil {
		return false, e
	}
	tasks := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return false, e
		}
		task, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return false, e
		}
		tasks = append(tasks, task)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return false, e
	}
	for _, task := range tasks {
		if n["input_hash"] != Hash(task["input_refs"]) {
			continue
		}
		receipt, e := load(tx, project, "AcceptanceReceipt", Str(task, "acceptance_id"))
		if e != nil {
			return false, e
		}
		found := false
		for _, candidate := range Arr(receipt, "artifact_refs") {
			if Hash(candidate) == Hash(ref) {
				found = true
				break
			}
		}
		if !found {
			continue
		}
		if e = retentionIndependent(tx, task, receipt); e == nil {
			e = s.acceptedTaskBinding(tx, project, task)
		}
		if e == nil {
			return true, nil
		}
		var fault *Fault
		if !errors.As(e, &fault) {
			return false, e
		}
	}
	return false, nil
}

// Before updating the progress record, detach a now ineffective current
// pointer. Its old version and sealed bytes stay retained as historical
// evidence; this prevents an exact stale reference from breaking later failure
// accounting, and does not promote another unverified result.
func (s *Service) refreshRetainedProgress(tx *sql.Tx, project string, n Object) error {
	if n["best_accepted_artifact_ref"] == nil {
		return nil
	}
	ref, ok := n["best_accepted_artifact_ref"].(map[string]any)
	if !ok {
		return Fail(422, "GATE_FAILED", "invalid retained artifact reference")
	}
	qualified, e := s.retainedProgressQualified(tx, project, n, ref)
	if e != nil {
		return e
	}
	if !qualified {
		n["best_accepted_artifact_ref"] = nil
		n["resume_conditions"] = mergeUnique(Arr(n, "resume_conditions"), []any{"Previously retained output requires independent revalidation before reuse."})
	}
	return nil
}

package domain

import (
	"database/sql"
	"strings"
)

type sourceDecisionEdit struct {
	decisions []any
	artifact  Object
}

// Integration requires a real task with valid context and sealed candidate evidence.
func (s *Service) changeConflicts(tx *sql.Tx, project string, proposal Object) ([]any, error) {
	return s.changeConflictsExcept(tx, project, proposal, nil)
}

func (s *Service) changeConflictsExcept(tx *sql.Tx, project string, proposal Object, excluded map[string]bool) ([]any, error) {
	chosen := map[string]bool{}
	integration := false
	edits := []sourceDecisionEdit{}
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
		edits = append(edits, sourceDecisionEdit{decisions: value.([]any), artifact: a})
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
		if excluded[Str(c, "id")] {
			continue
		}
		if sourceEvidenceConflict(c) {
			if e := s.checkSourceConflictResolution(tx, project, c, edits); e != nil {
				return nil, e
			}
			ids = append(ids, c["id"])
			continue
		}
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

func sourceEvidenceConflict(c Object) bool {
	if c["kind"] != "EVIDENCE" || len(Arr(c, "subject_refs")) < 2 {
		return false
	}
	for _, v := range Arr(c, "subject_refs") {
		r, ok := v.(map[string]any)
		if !ok || r["entity_type"] != "Artifact" {
			return false
		}
	}
	return true
}

func hasExactRef(refs []any, want Object) bool {
	for _, v := range refs {
		if Hash(v) == Hash(want) {
			return true
		}
	}
	return false
}

func sourceConflictInProposal(tx *sql.Tx, project string, proposal Object) (bool, error) {
	for _, v := range Arr(proposal, "conflict_ids") {
		c, e := load(tx, project, "Conflict", v.(string))
		if e != nil {
			return false, e
		}
		if sourceEvidenceConflict(c) {
			return true, nil
		}
	}
	return false, nil
}

// Source-resolution changes require a currently authorized independent
// verifier, not merely a matching name in an old receipt.
func sourceConflictVerifier(tx *sql.Tx, project, verifier string, authors []any) error {
	var count int
	e := tx.QueryRow("SELECT count(*) FROM auth_principals p WHERE p.id=? AND p.revoked=0 AND EXISTS (SELECT 1 FROM json_each(p.roles) WHERE value='VERIFIER') AND EXISTS (SELECT 1 FROM auth_grants g WHERE g.principal=p.id AND g.project=? AND g.task='' AND g.run='')", verifier, project).Scan(&count)
	if e != nil {
		return e
	}
	if count != 1 {
		return Fail(403, "FORBIDDEN", "current independent verifier grant required")
	}
	root, e := authorityRoot(tx, verifier)
	if e != nil {
		return e
	}
	for _, v := range authors {
		id := v.(string)
		authorRoot, e := authorityRoot(tx, id)
		if e != nil {
			return e
		}
		if id == verifier || authorRoot == root {
			return Fail(403, "FORBIDDEN", "source-resolution author cannot verify own change")
		}
	}
	return nil
}

// A source conflict is resolved only by a selected decision about this exact
// OPEN Conflict version, backed by every source and a task whose frozen context
// includes the same conflict and sources. An unrelated integration task cannot
// resolve it just because it belongs to the project.
func (s *Service) checkSourceConflictResolution(tx *sql.Tx, project string, c Object, edits []sourceDecisionEdit) error {
	conflictRef := Ref(c, "Conflict")
	qualified := 0
	for _, edit := range edits {
		for _, v := range edit.decisions {
			r := v.(map[string]any)
			d, e := version(tx, project, r)
			if e != nil {
				return e
			}
			if Hash(d["subject_ref"]) != Hash(conflictRef) {
				continue
			}
			if d["status"] != "DECIDED" || d["mode"] != "ADVISORY" || len(decisionHardFailures(d)) != 0 || strings.TrimSpace(Str(d, "rationale")) == "" || len(Arr(d, "revocation_conditions")) == 0 {
				return Fail(422, "GATE_FAILED", "source resolution decision lacks independent reviewable basis")
			}
			if !hasExactRef(Arr(d, "input_refs"), conflictRef) || !hasExactRef(Arr(edit.artifact, "input_refs"), conflictRef) {
				return Fail(422, "GATE_FAILED", "source resolution does not bind current conflict")
			}
			for _, source := range Arr(c, "subject_refs") {
				sr := source.(map[string]any)
				if e := s.effective(tx, project, sr); e != nil {
					return e
				}
				if !hasExactRef(Arr(d, "input_refs"), sr) || !hasExactRef(Arr(d, "evidence_refs"), sr) || !hasExactRef(Arr(edit.artifact, "input_refs"), sr) {
					return Fail(422, "GATE_FAILED", "source resolution omits a conflicting source version")
				}
			}
			for _, input := range Arr(edit.artifact, "input_refs") {
				tr, ok := input.(map[string]any)
				if !ok || tr["entity_type"] != "Task" {
					continue
				}
				task, e := version(tx, project, tr)
				if e != nil {
					return e
				}
				if task["task_type"] != "integration" || !hasExactRef(Arr(task, "input_refs"), conflictRef) || s.taskContext(tx, project, task) != nil {
					continue
				}
				bundle, e := load(tx, project, "ContextBundle", Str(task, "context_bundle_id"))
				if e != nil {
					return e
				}
				if !hasExactRef(Arr(bundle, "version_vector"), conflictRef) {
					continue
				}
				complete := true
				for _, source := range Arr(c, "subject_refs") {
					sr := source.(map[string]any)
					complete = complete && hasExactRef(Arr(task, "input_refs"), sr) && hasExactRef(Arr(bundle, "version_vector"), sr)
				}
				if complete {
					qualified++
					break
				}
			}
		}
	}
	if qualified == 1 {
		return nil
	}
	return Fail(409, "STATE_CONFLICT", "source conflict requires a bound integration decision and task")
}

// After applyChange advances Conflict to RESOLVED, the selected decision still
// names the exact OPEN version it settled. This proof is the sole exception to
// the normal current-version rule for a DecisionReceipt's Conflict reference.
func (s *Service) resolvedSourceDecision(tx *sql.Tx, project string, decision, oldRef Object) (bool, error) {
	if oldRef["entity_type"] != "Conflict" || Hash(decision["subject_ref"]) != Hash(oldRef) {
		return false, nil
	}
	old, e := version(tx, project, oldRef)
	if e != nil {
		return false, e
	}
	current, e := load(tx, project, "Conflict", Str(oldRef, "id"))
	if e != nil {
		return false, e
	}
	if !sourceEvidenceConflict(old) || old["status"] != "OPEN" || current["status"] != "RESOLVED" || Str(current, "resolution_proposal_id") == "" || Hash(Ref(current, "Conflict")) == Hash(oldRef) {
		return false, nil
	}
	proposal, e := load(tx, project, "ChangeProposal", Str(current, "resolution_proposal_id"))
	if e != nil {
		return false, e
	}
	if proposal["status"] != "APPLIED" || !containsString(Arr(proposal, "conflict_ids"), Str(current, "id")) || Str(proposal, "acceptance_id") == "" {
		return false, nil
	}
	receipt, e := load(tx, project, "AcceptanceReceipt", Str(proposal, "acceptance_id"))
	if e != nil {
		return false, e
	}
	if receipt["verdict"] != "PASS" || receipt["independence_basis"] != "DETERMINISTIC_SERVICE" || receipt["measurement_mode"] != "FIXTURE" || receipt["receipt_hash"] != Receipt(receipt) || receipt["contract_hash"] != changeHash(proposal) || Str(receipt["subject_ref"].(map[string]any), "id") != Str(proposal, "id") {
		return false, nil
	}
	if _, e := version(tx, project, receipt["subject_ref"].(map[string]any)); e != nil {
		return false, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return false, e
	}
	decisionRef := Ref(decision, "DecisionReceipt")
	if !hasExactRef(Arr(state, "current_decision_refs"), decisionRef) {
		return false, nil
	}
	selected := false
	for _, v := range Arr(proposal, "edits") {
		edit := v.(map[string]any)
		target := edit["target_ref"].(map[string]any)
		if target["entity_type"] != "ProjectState" || edit["field"] != "current_decision_refs" {
			continue
		}
		ref := edit["proposed_value_artifact_ref"].(map[string]any)
		a, e := version(tx, project, ref)
		if e != nil {
			return false, e
		}
		var raw []byte
		if e := tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&raw); e != nil {
			return false, e
		}
		if Digest(raw) != a["content_hash"] {
			return false, Fail(422, "CONTENT_HASH_MISMATCH", "resolution value bytes changed")
		}
		value, e := Decode(append(append([]byte(`{"value":`), raw...), '}'))
		if e != nil {
			return false, e
		}
		refs, ok := value["value"].([]any)
		selected = selected || ok && hasExactRef(refs, decisionRef) && hasExactRef(Arr(a, "input_refs"), oldRef)
	}
	if !selected || decision["status"] != "DECIDED" || decision["mode"] != "ADVISORY" || len(decisionHardFailures(decision)) != 0 {
		return false, nil
	}
	for _, v := range Arr(old, "subject_refs") {
		r := v.(map[string]any)
		if !hasExactRef(Arr(decision, "input_refs"), r) || !hasExactRef(Arr(decision, "evidence_refs"), r) {
			return false, nil
		}
	}
	return true, nil
}

func containsString(values []any, want string) bool {
	for _, v := range values {
		if v == want {
			return true
		}
	}
	return false
}

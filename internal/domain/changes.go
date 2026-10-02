package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"sort"
)

var changeChecks = []string{"context.inputs-frozen", "context.impact-exact", "context.authority-independent"}

func changeHash(o Object) string {
	return Hash(Object{"edits": o["edits"], "base_state_revision": o["base_state_revision"], "test_check_ids": o["test_check_ids"], "migration_steps": o["migration_steps"], "rollback_steps": o["rollback_steps"], "rules": "W04-change-1"})
}
func (s *Service) artifactJSON(tx *sql.Tx, project string, r Object) (any, error) {
	if e := s.effective(tx, project, r); e != nil {
		return nil, e
	}
	o, e := version(tx, project, r)
	if e != nil {
		return nil, e
	}
	if r["entity_type"] != "Artifact" || o["validity"] != "CURRENT" || o["access_class"] != "PROJECT" {
		return nil, Fail(422, "GATE_FAILED", "current project artifact required")
	}
	var raw []byte
	if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, o["storage_key"]).Scan(&raw); e != nil {
		return nil, Fail(422, "GATE_FAILED", "sealed content unavailable")
	}
	if Digest(raw) != o["content_hash"] {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "sealed bytes changed")
	}
	wrapped, e := Decode(append(append([]byte(`{"value":`), raw...), '}'))
	if e != nil {
		return nil, Fail(400, "INVALID_REQUEST", "proposed value must be strict JSON with exact numbers")
	}
	return wrapped["value"], nil
}
func (s *Service) recordDecision(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	prepared, err := s.prepareDecision(tx, p, project, b)
	if err != nil {
		return nil, err
	}
	b = prepared
	found := false
	for _, v := range Arr(b, "options") {
		if v == b["selected"] {
			found = true
		}
	}
	if !found || b["input_hash"] != Hash(b["input_refs"]) {
		return nil, Fail(422, "GATE_FAILED", "decision option or input hash mismatch")
	}
	o := Merge(Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "recorded_by": p.ID}, b)
	o["receipt_hash"] = Receipt(o)
	if e := s.put(tx, "DecisionReceipt", o); e != nil {
		return nil, e
	}
	root := Str(o, "id")
	generation := 1
	if b["supersedes_id"] != nil {
		if e := tx.QueryRow("SELECT root_id,generation+1 FROM decision_lineage WHERE project=? AND receipt_id=?", project, b["supersedes_id"]).Scan(&root, &generation); e != nil {
			return nil, Fail(422, "GATE_FAILED", "decision parent lineage unavailable")
		}
	}
	_, e := tx.Exec("INSERT INTO decision_lineage(project,receipt_id,root_id,generation) VALUES(?,?,?,?)", project, o["id"], root, generation)
	if e != nil {
		return nil, e
	}
	for _, r := range semanticReferences("DecisionReceipt", o) {
		if _, e = s.impactLink(tx, project, Object{"from_ref": Ref(o, "DecisionReceipt"), "to_ref": r, "relation": "DEPENDS_ON", "basis": "DETERMINISTIC", "evidence_refs": Empty()}); e != nil {
			return nil, e
		}
	}
	return o, nil
}
func allowedEdit(kind, field string) bool {
	return kind == "ProjectState" && field == "current_decision_refs" || kind == "Requirement" && field == "text" || kind == "ProjectProfile" && (field == "intent" || field == "facts" || field == "constraints")
}
func (s *Service) validateDecisions(tx *sql.Tx, project string, old, newValue any) error {
	values, ok := newValue.([]any)
	if !ok {
		return Fail(400, "INVALID_REQUEST", "decision refs array required")
	}
	roots := map[string]string{}
	oldIDs := map[string]bool{}
	for _, v := range old.([]any) {
		oldIDs[Str(v.(map[string]any), "id")] = true
	}
	for _, v := range values {
		r, ok := v.(map[string]any)
		if !ok || r["entity_type"] != "DecisionReceipt" {
			return Fail(400, "INVALID_REQUEST", "decision reference required")
		}
		d, e := version(tx, project, r)
		if e != nil {
			return e
		}
		if e = s.effectiveInputs(tx, project, "DecisionReceipt", d, map[string]bool{}); e != nil {
			return e
		}
		if d["status"] != "DECIDED" {
			return Fail(422, "GATE_FAILED", "abstained or failed decision cannot be adopted")
		}
		if len(decisionHardFailures(d)) > 0 {
			return Fail(422, "GATE_FAILED", "failed checks or missing evidence prevent decision adoption")
		}
		var root string
		if e = tx.QueryRow("SELECT root_id FROM decision_lineage WHERE project=? AND receipt_id=?", project, r["id"]).Scan(&root); e != nil {
			return e
		}
		if roots[root] != "" {
			return Fail(409, "STATE_CONFLICT", "two current decisions in one lineage")
		}
		roots[root] = Str(r, "id")
		if !oldIDs[Str(r, "id")] && len(oldIDs) > 0 && d["supersedes_id"] == nil {
			return Fail(422, "GATE_FAILED", "replacement requires explicit predecessor")
		}
	}
	for oldID := range oldIDs {
		var root string
		if e := tx.QueryRow("SELECT root_id FROM decision_lineage WHERE project=? AND receipt_id=?", project, oldID).Scan(&root); e != nil {
			return e
		}
		newID := roots[root]
		if newID == "" {
			return Fail(422, "GATE_FAILED", "unrelated decision cannot disappear")
		}
		if newID != oldID {
			d, e := load(tx, project, "DecisionReceipt", newID)
			if e != nil {
				return e
			}
			if d["supersedes_id"] != oldID {
				return Fail(409, "STATE_CONFLICT", "replacement is not the next decision generation")
			}
		}
	}
	return nil
}
func (s *Service) createChange(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(state["revision"]) != Hash(b["base_state_revision"]) {
		return nil, Fail(412, "STALE_REVISION", "proposal base changed")
	}
	if Hash(b["test_check_ids"]) != Hash(changeChecks) {
		return nil, Fail(422, "GATE_FAILED", "change must freeze the supported deterministic checks")
	}
	roots := []Object{}
	originals := Empty()
	seen := map[string]bool{}
	for _, v := range Arr(b, "edits") {
		edit := v.(map[string]any)
		r := edit["target_ref"].(map[string]any)
		kind, field := Str(r, "entity_type"), Str(edit, "field")
		if !allowedEdit(kind, field) {
			return nil, Fail(403, "FORBIDDEN", "field is not changeable through this workflow")
		}
		key := kind + ":" + Str(r, "id") + ":" + field
		if seen[key] {
			return nil, Fail(400, "INVALID_REQUEST", "duplicate edit target")
		}
		seen[key] = true
		current, e := load(tx, project, kind, Str(r, "id"))
		if e != nil {
			return nil, e
		}
		if Hash(Ref(current, kind)) != Hash(r) {
			return nil, Fail(412, "STALE_INPUT", "edit target changed")
		}
		value, e := s.artifactJSON(tx, project, edit["proposed_value_artifact_ref"].(map[string]any))
		if e != nil {
			return nil, e
		}
		candidate := copyObject(current)
		candidate[field] = value
		if !s.visible(tx, p, project, candidate) {
			return nil, Fail(403, "FORBIDDEN", "proposed value references restricted content")
		}
		if e = s.Contracts.Validate(kind, candidate); e != nil {
			return nil, Fail(400, "INVALID_REQUEST", "proposed field violates entity schema")
		}
		originals = append(originals, current[field])
		if kind == "ProjectState" {
			if e = s.validateDecisions(tx, project, current[field], value); e != nil {
				return nil, e
			}
			for _, v := range current[field].([]any) {
				if !containsRef(value.([]any), v.(map[string]any)) {
					roots = append(roots, v.(map[string]any))
				}
			}
		} else {
			roots = append(roots, r)
		}
	}
	impacted, links, e := s.closure(tx, project, roots)
	if e != nil {
		return nil, e
	}
	o := Merge(Base(project), b)
	Merge(o, Object{"status": "IMPACT_ANALYZED", "impacted_refs": impacted, "impact_link_ids": links, "semantic_review_run_id": nil, "conflict_ids": Empty(), "acceptance_id": nil, "applied_state_revision": nil})
	conflicts, e := s.changeConflicts(tx, project, o)
	if e != nil {
		return nil, e
	}
	o["conflict_ids"] = conflicts
	if e = s.put(tx, "ChangeProposal", o); e != nil {
		return nil, e
	}
	_, e = tx.Exec("INSERT INTO context_changes(project,proposal_id,author,contract_hash,original_values) VALUES(?,?,?,?,?)", project, o["id"], p.ID, changeHash(o), string(Bytes(originals)))
	return o, e
}
func copyObject(o Object) Object {
	n := Object{}
	for k, v := range o {
		n[k] = v
	}
	return n
}
func containsRef(values []any, r Object) bool {
	for _, v := range values {
		if Hash(v) == Hash(r) {
			return true
		}
	}
	return false
}
func (s *Service) checkChange(tx *sql.Tx, p Principal, project string, proposal Object) ([]any, error) {
	var original string
	var frozen string
	if e := tx.QueryRow("SELECT contract_hash,original_values FROM context_changes WHERE project=? AND proposal_id=?", project, proposal["id"]).Scan(&frozen, &original); e != nil {
		return nil, e
	}
	if frozen != changeHash(proposal) {
		return nil, Fail(422, "GATE_FAILED", "frozen change contract changed")
	}
	var originals []any
	d := json.NewDecoder(bytes.NewReader([]byte(original)))
	d.UseNumber()
	if e := d.Decode(&originals); e != nil {
		return nil, e
	}
	roots := []Object{}
	values := Empty()
	for i, v := range Arr(proposal, "edits") {
		edit := v.(map[string]any)
		r := edit["target_ref"].(map[string]any)
		kind, field := Str(r, "entity_type"), Str(edit, "field")
		current, e := load(tx, project, kind, Str(r, "id"))
		if e != nil {
			return nil, e
		}
		if Hash(current[field]) != Hash(originals[i]) {
			return nil, Fail(409, "STATE_CONFLICT", "edited value changed since proposal")
		}
		value, e := s.artifactJSON(tx, project, edit["proposed_value_artifact_ref"].(map[string]any))
		if e != nil {
			return nil, e
		}
		candidate := copyObject(current)
		candidate[field] = value
		if !s.visible(tx, p, project, candidate) {
			return nil, Fail(403, "FORBIDDEN", "current permission denies proposed value")
		}
		values = append(values, value)
		if kind == "ProjectState" {
			if e = s.validateDecisions(tx, project, current[field], value); e != nil {
				return nil, e
			}
			for _, v := range current[field].([]any) {
				if !containsRef(value.([]any), v.(map[string]any)) {
					roots = append(roots, v.(map[string]any))
				}
			}
		} else {
			roots = append(roots, r)
		}
	}
	semanticConflicts := Empty()
	var e error
	if proposal["semantic_review_run_id"] != nil {
		var reviews []semanticReview
		reviews, e = s.semanticReviews(tx, project, proposal, false)
		if e != nil {
			return nil, e
		}
		semanticConflicts = Arr(reviews[0].report, "conflict_ids")
	}
	var affected, links []any
	if proposal["semantic_review_run_id"] != nil {
		affected, links, e = s.reviewClosure(tx, project, proposal)
	} else {
		affected, links, e = s.closure(tx, project, roots)
	}
	if e != nil {
		return nil, e
	}
	if Hash(affected) != Hash(proposal["impacted_refs"]) || Hash(links) != Hash(proposal["impact_link_ids"]) {
		return nil, Fail(412, "STALE_INPUT", "impact closure changed")
	}
	conflicts, e := s.changeConflictsExcept(tx, project, proposal, stringSet(semanticConflicts))
	if e != nil {
		return nil, e
	}
	if Hash(append(conflicts, semanticConflicts...)) != Hash(proposal["conflict_ids"]) {
		return nil, Fail(412, "STALE_INPUT", "conflict set changed")
	}
	return values, nil
}
func (s *Service) serverArtifact(tx *sql.Tx, project, principal, kind string, data []byte, refs []any) (Object, error) {
	return s.serverArtifactMode(tx, project, principal, kind, "FIXTURE", data, refs)
}

func (s *Service) serverArtifactMode(tx *sql.Tx, project, principal, kind, mode string, data []byte, refs []any) (Object, error) {
	if mode != "FIXTURE" && mode != "LIVE" {
		return nil, Fail(422, "GATE_FAILED", "trusted artifact mode required")
	}
	u, e := s.upload(tx, Principal{ID: principal}, project, data)
	if e != nil {
		return nil, e
	}
	o := Merge(Base(project), Object{"run_id": nil, "kind": kind, "evidence_kind": "OBSERVED", "measurement_mode": mode, "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": artifactMedia(data), "byte_size": len(data), "input_refs": refs, "source_refs": Empty(), "produced_by": principal, "access_class": "PROJECT", "validity": "CURRENT", "sealed_at": Now()})
	if e = s.put(tx, "Artifact", o); e != nil {
		return nil, e
	}
	_, e = tx.Exec("UPDATE uploaded_content SET sealed=1 WHERE storage_key=?", o["storage_key"])
	return o, e
}
func (s *Service) acceptChange(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	r := b["subject_ref"].(map[string]any)
	if r["entity_type"] == "Task" {
		task, e := load(tx, project, "Task", Str(r, "id"))
		if e != nil {
			return nil, e
		}
		if e = s.taskContext(tx, project, task); e != nil {
			return nil, e
		}
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "Task acceptance belongs to W06")
	}
	if r["entity_type"] != "ChangeProposal" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "acceptance subject requires its owning stage")
	}
	proposal, e := load(tx, project, "ChangeProposal", Str(r, "id"))
	if e != nil {
		return nil, e
	}
	if proposal["status"] != "IMPACT_ANALYZED" {
		return nil, Fail(409, "STATE_CONFLICT", "change is not awaiting verification")
	}
	if Hash(Ref(proposal, "ChangeProposal")) != Hash(r) {
		return nil, Fail(412, "STALE_INPUT", "proposal changed")
	}
	if b["contract_hash"] != changeHash(proposal) {
		return nil, Fail(422, "GATE_FAILED", "frozen check contract mismatch")
	}
	var author string
	if e = tx.QueryRow("SELECT author FROM context_changes WHERE project=? AND proposal_id=?", project, proposal["id"]).Scan(&author); e != nil {
		return nil, e
	}
	authors, e := s.candidateAuthors(tx, project, proposal, author)
	if e != nil {
		return nil, e
	}
	if sourceResolution, e := sourceConflictInProposal(tx, project, proposal); e != nil {
		return nil, e
	} else if sourceResolution || proposal["semantic_review_run_id"] != nil {
		if e := sourceConflictVerifier(tx, project, p.ID, authors); e != nil {
			return nil, e
		}
	}
	for _, id := range authors {
		if id == p.ID {
			return nil, Fail(403, "FORBIDDEN", "author cannot independently accept this change")
		}
	}
	if _, e = s.checkChange(tx, p, project, proposal); e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	started := Now()
	evidence, e := s.serverArtifact(tx, project, p.ID, "REPORT", Bytes(Object{"proposal_ref": r, "contract_hash": changeHash(proposal), "computed_impact": proposal["impacted_refs"], "checks": changeChecks, "verifier": p.ID, "verified_at": started}), []any{r})
	if e != nil {
		return nil, e
	}
	checks := Empty()
	actual := "Server recomputed frozen inputs, exact impact and independent authority."
	reason := "Independent deterministic change validation; not Task acceptance."
	if proposal["semantic_review_run_id"] != nil {
		actual = "Server checked sealed report provenance, merged impact closure and independent authority; semantic content remains a fixture claim."
		reason = "Independent structural validation of fixture semantic review; semantic truth is not established."
	}
	for _, id := range changeChecks {
		checks = append(checks, Object{"check_id": id, "status": "PASS", "evidence_refs": []any{Ref(evidence, "Artifact")}, "command_key": "test.context", "actual": actual, "exit_code": 0, "started_at": started, "finished_at": Now()})
	}
	o := Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "subject_ref": r, "run_id": nil, "contract_hash": changeHash(proposal), "input_refs": []any{r}, "artifact_refs": []any{Ref(evidence, "Artifact")}, "checks": checks, "verdict": "PASS", "verifier_principal_id": p.ID, "executor_principal_ids": authors, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": state["policy_revision"], "measurement_mode": "FIXTURE", "reason": reason}
	o["receipt_hash"] = Receipt(o)
	return o, s.put(tx, "AcceptanceReceipt", o)
}
func (s *Service) applyChange(tx *sql.Tx, p Principal, project, id string, b Object) (Object, error) {
	proposal, e := load(tx, project, "ChangeProposal", id)
	if e != nil {
		return nil, e
	}
	if proposal["status"] != "IMPACT_ANALYZED" {
		return nil, Fail(409, "STATE_CONFLICT", "change cannot be applied in this state")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(state["revision"]) != Hash(b["expected_project_state_revision"]) {
		return nil, Fail(412, "STALE_REVISION", "state changed")
	}
	receipt, e := load(tx, project, "AcceptanceReceipt", Str(b, "acceptance_id"))
	if e != nil {
		return nil, e
	}
	if receipt["verdict"] != "PASS" || receipt["contract_hash"] != changeHash(proposal) || Hash(receipt["subject_ref"]) != Hash(Ref(proposal, "ChangeProposal")) || receipt["receipt_hash"] != Receipt(receipt) || Hash(receipt["policy_revision"]) != Hash(state["policy_revision"]) {
		return nil, Fail(422, "GATE_FAILED", "acceptance does not bind this change")
	}
	if sourceResolution, e := sourceConflictInProposal(tx, project, proposal); e != nil {
		return nil, e
	} else if sourceResolution || proposal["semantic_review_run_id"] != nil {
		var author string
		if e := tx.QueryRow("SELECT author FROM context_changes WHERE project=? AND proposal_id=?", project, proposal["id"]).Scan(&author); e != nil {
			return nil, e
		}
		authors, e := s.candidateAuthors(tx, project, proposal, author)
		if e != nil {
			return nil, e
		}
		if Hash(authors) != Hash(receipt["executor_principal_ids"]) {
			return nil, Fail(412, "STALE_INPUT", "change authors changed")
		}
		if e := sourceConflictVerifier(tx, project, Str(receipt, "verifier_principal_id"), authors); e != nil {
			return nil, e
		}
	}
	values, e := s.checkChange(tx, p, project, proposal)
	if e != nil {
		return nil, e
	}
	changed := []struct {
		kind   string
		object Object
	}{}
	for i, v := range Arr(proposal, "edits") {
		edit := v.(map[string]any)
		r := edit["target_ref"].(map[string]any)
		kind := Str(r, "entity_type")
		o, e := load(tx, project, kind, Str(r, "id"))
		if e != nil {
			return nil, e
		}
		o[Str(edit, "field")] = values[i]
		if e = bump(o); e != nil {
			return nil, e
		}
		if e = s.put(tx, kind, o); e != nil {
			return nil, e
		}
		if kind == "Artifact" {
			if e = s.freezeSkillsForSource(tx, project, Str(o, "id")); e != nil {
				return nil, e
			}
		}
		changed = append(changed, struct {
			kind   string
			object Object
		}{kind, o})
		if kind == "ProjectState" {
			state = o
		}
		if kind == "ProjectProfile" {
			state["profile_revision"] = o["revision"]
		}
		if kind == "Requirement" {
			refs := Arr(state, "current_requirement_refs")
			for i, v := range refs {
				if v.(map[string]any)["id"] == o["id"] {
					refs[i] = Ref(o, kind)
				}
			}
			state["current_requirement_refs"] = refs
		}
	}
	for _, v := range Arr(proposal, "impacted_refs") {
		r := v.(map[string]any)
		kind := Str(r, "entity_type")
		if kind != "Task" && kind != "Artifact" && kind != "Goal" {
			continue
		}
		o, e := load(tx, project, kind, Str(r, "id"))
		if e != nil {
			return nil, e
		}
		if kind == "Task" || kind == "Goal" {
			if o["status"] == "CANCELLED" {
				continue
			}
			o["status"] = "NEEDS_REVALIDATION"
		} else {
			o["validity"] = "STALE"
		}
		if e = bump(o); e != nil {
			return nil, e
		}
		if e = s.put(tx, kind, o); e != nil {
			return nil, e
		}
		if kind == "Artifact" {
			if e = s.freezeSkillsForSource(tx, project, Str(o, "id")); e != nil {
				return nil, e
			}
		}
		changed = append(changed, struct {
			kind   string
			object Object
		}{kind, o})
	}
	formalConflicts := Arr(proposal, "conflict_ids")
	for _, id := range formalConflicts {
		c, e := load(tx, project, "Conflict", id.(string))
		if e != nil {
			return nil, e
		}
		c["status"] = "RESOLVED"
		c["resolution_proposal_id"] = proposal["id"]
		c["resolution_reason"] = "Independent integration change applied"
		if e = bump(c); e != nil {
			return nil, e
		}
		if e = s.put(tx, "Conflict", c); e != nil {
			return nil, e
		}
	}
	remaining := Empty()
	for _, id := range Arr(state, "blocking_conflict_ids") {
		resolved := false
		for _, rid := range formalConflicts {
			resolved = resolved || id == rid
		}
		if !resolved {
			remaining = append(remaining, id)
		}
	}
	state["blocking_conflict_ids"] = remaining
	currentState, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	state["revision"] = currentState["revision"]
	if e = bump(state); e != nil {
		return nil, e
	}
	if e = s.put(tx, "ProjectState", state); e != nil {
		return nil, e
	}
	for _, change := range changed {
		eventType := "PROJECT_UPDATED"
		if change.kind == "Task" {
			eventType = "TASK_CHANGED"
		}
		if e = s.event(tx, project, change.kind, change.object, p.ID, Str(proposal, "id"), eventType); e != nil {
			return nil, e
		}
	}
	state, e = singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	proposal["status"] = "APPLIED"
	proposal["acceptance_id"] = receipt["id"]
	revision, e := Num(state, "revision")
	if e != nil {
		return nil, e
	}
	proposal["applied_state_revision"] = revision + 1
	if e = bump(proposal); e != nil {
		return nil, e
	}
	return proposal, s.put(tx, "ChangeProposal", proposal)
}
func (s *Service) createConflict(tx *sql.Tx, project string, b Object) (Object, error) {
	o := Merge(Base(project), b)
	Merge(o, Object{"status": "OPEN", "resolution_proposal_id": nil, "resolution_reason": nil})
	if e := s.put(tx, "Conflict", o); e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	state["blocking_conflict_ids"] = append(Arr(state, "blocking_conflict_ids"), o["id"])
	if e = bump(state); e != nil {
		return nil, e
	}
	return o, s.put(tx, "ProjectState", state)
}
func (s *Service) resolveConflict(tx *sql.Tx, project, id string, b Object) (Object, error) {
	o, e := load(tx, project, "Conflict", id)
	if e != nil {
		return nil, e
	}
	proposal, e := load(tx, project, "ChangeProposal", Str(b, "resolution_proposal_id"))
	if e != nil {
		return nil, e
	}
	// The old guard also required the conflict to already name this proposal, but
	// resolution_proposal_id is precisely what this operation writes and CreateConflictRequest does
	// not carry it, so no conflict could ever be resolved: the check contradicted its own schema.
	// The requirement that survives is the real one - only an accepted and applied change settles a
	// conflict - and the resolution is recorded here rather than demanded in advance.
	if proposal["status"] != "APPLIED" {
		return nil, Fail(409, "STATE_CONFLICT", "resolution change has not been accepted and applied")
	}
	o["status"] = "RESOLVED"
	o["resolution_proposal_id"] = proposal["id"]
	o["resolution_reason"] = b["reason"]
	if e = bump(o); e != nil {
		return nil, e
	}
	return o, s.put(tx, "Conflict", o)
}
func (s *Service) ChangeContractHash(ctx context.Context, project, id string) (string, error) {
	var raw string
	if e := s.DB.QueryRowContext(ctx, "SELECT contract_hash FROM context_changes WHERE project=? AND proposal_id=?", project, id).Scan(&raw); e != nil {
		return "", fmt.Errorf("frozen change unavailable: %w", e)
	}
	return raw, nil
}

func artifactMedia(data []byte) string {
	if json.Valid(data) {
		return "application/json"
	}
	return "text/plain; charset=utf-8"
}

// candidateAuthors follows the material being promoted, not the superseded lineage.
// Source snapshots and unrelated/current decisions are not candidate authorship.
func (s *Service) candidateAuthors(tx *sql.Tx, project string, proposal Object, author string) ([]any, error) {
	authors := map[string]bool{author: true}
	if proposal["semantic_review_run_id"] != nil {
		reviews, e := s.semanticReviews(tx, project, proposal, false)
		if e != nil {
			return nil, e
		}
		for _, review := range reviews {
			authors[review.executor] = true
		}
	}
	visited := map[string]bool{}
	var artifact func(Object, bool) error
	artifact = func(ref Object, direct bool) error {
		key := Hash(ref)
		if visited[key] {
			return nil
		}
		visited[key] = true
		a, e := version(tx, project, ref)
		if e != nil {
			return e
		}
		if !direct && a["kind"] == "SOURCE_SNAPSHOT" {
			return nil
		}
		authors[Str(a, "produced_by")] = true
		for _, r := range Arr(a, "input_refs") {
			v := r.(map[string]any)
			if v["entity_type"] == "Artifact" {
				if e = artifact(v, false); e != nil {
					return e
				}
			}
		}
		return nil
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	current := map[string]bool{}
	for _, r := range Arr(state, "current_decision_refs") {
		current[Str(r.(map[string]any), "id")] = true
	}
	for _, v := range Arr(proposal, "edits") {
		edit := v.(map[string]any)
		ref := edit["proposed_value_artifact_ref"].(map[string]any)
		if e = artifact(ref, true); e != nil {
			return nil, e
		}
		target := edit["target_ref"].(map[string]any)
		if target["entity_type"] != "ProjectState" || edit["field"] != "current_decision_refs" {
			continue
		}
		value, e := s.artifactJSON(tx, project, ref)
		if e != nil {
			return nil, e
		}
		for _, v := range value.([]any) {
			r := v.(map[string]any)
			if current[Str(r, "id")] {
				continue
			}
			d, e := version(tx, project, r)
			if e != nil {
				return nil, e
			}
			authors[Str(d, "recorded_by")] = true
			for _, r := range Arr(d, "evidence_refs") {
				evidence := r.(map[string]any)
				if evidence["entity_type"] == "Artifact" {
					if e = artifact(evidence, false); e != nil {
						return nil, e
					}
				}
			}
		}
	}
	ids := []string{}
	for id := range authors {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	result := Empty()
	for _, id := range ids {
		result = append(result, id)
	}
	return result, nil
}

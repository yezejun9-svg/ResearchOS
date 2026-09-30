package domain

import (
	"database/sql"
	"sort"
	"strings"
)

// reviewInputs binds the normal task to immutable edit targets and value artifacts.
// The proposal revision is deliberately absent: analyze itself advances it.
func reviewInputs(proposal Object) []any {
	refs := Empty()
	seen := map[string]bool{}
	for _, value := range Arr(proposal, "edits") {
		edit := value.(map[string]any)
		for _, field := range []string{"target_ref", "proposed_value_artifact_ref"} {
			ref := edit[field].(map[string]any)
			if !seen[Hash(ref)] {
				refs = append(refs, ref)
				seen[Hash(ref)] = true
			}
		}
	}
	return refs
}

func exactUnique(values []any) bool {
	seen := map[string]bool{}
	for _, value := range values {
		key := Hash(value)
		if seen[key] {
			return false
		}
		seen[key] = true
	}
	return true
}

// semanticEvidence checks the current execution epoch and its sealed single
// report. A task type or an artifact label alone never establishes provenance.
func (s *Service) semanticEvidence(tx *sql.Tx, project string, proposal Object, runID string) (Object, Object, string, error) {
	r, e := load(tx, project, "Run", runID)
	if e != nil {
		return nil, nil, "", e
	}
	t, e := load(tx, project, "Task", Str(r, "task_id"))
	if e != nil {
		return nil, nil, "", e
	}
	exitCode, exitErr := Num(r, "exit_code")
	if t["task_type"] != "impact_review" || (t["status"] != "EXECUTION_REPORTED" && t["status"] != "ACCEPTED") || t["active_run_id"] != runID || r["status"] != "SETTLED" || exitErr != nil || exitCode != 0 || r["children_stopped"] != true || r["queue_empty"] != true || r["context_bundle_id"] != t["context_bundle_id"] || Hash(r["input_refs"]) != Hash(reviewInputs(proposal)) || Hash(t["input_refs"]) != Hash(reviewInputs(proposal)) || Hash(r["result_artifact_ids"]) != Hash(t["output_artifact_ids"]) || len(Arr(r, "result_artifact_ids")) != 1 {
		return nil, nil, "", Fail(422, "GATE_FAILED", "normal settled impact review with exact edit inputs and one output required")
	}
	var executorGrant int
	if e = tx.QueryRow("SELECT count(*) FROM auth_principals p WHERE p.id=? AND p.revoked=0 AND EXISTS (SELECT 1 FROM json_each(p.roles) WHERE value='EXECUTOR') AND EXISTS (SELECT 1 FROM auth_grants g WHERE g.principal=p.id AND g.project=? AND ((g.task=? AND g.run=?) OR (g.task='' AND g.run='')))", r["executor_principal_id"], project, t["id"], runID).Scan(&executorGrant); e != nil {
		return nil, nil, "", e
	}
	if executorGrant != 1 {
		return nil, nil, "", Fail(403, "FORBIDDEN", "current review executor grant required")
	}
	root, e := authorityRoot(tx, Str(r, "executor_principal_id"))
	if e != nil {
		return nil, nil, "", e
	}
	var rootActive int
	if e = tx.QueryRow("SELECT count(*) FROM auth_principals WHERE id=? AND revoked=0", root).Scan(&rootActive); e != nil {
		return nil, nil, "", e
	}
	if rootActive != 1 {
		return nil, nil, "", Fail(403, "FORBIDDEN", "review executor authority root revoked")
	}
	if root != r["executor_principal_id"] {
		var rootGrant int
		if e = tx.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=? AND ((task=? AND run=?) OR (task='' AND run=''))", root, project, t["id"], runID).Scan(&rootGrant); e != nil {
			return nil, nil, "", e
		}
		if rootGrant == 0 {
			return nil, nil, "", Fail(403, "FORBIDDEN", "review executor authority root has no project grant")
		}
	}
	if e = s.taskContext(tx, project, t); e != nil {
		return nil, nil, "", e
	}
	var frozen string
	if e = tx.QueryRow("SELECT contract FROM orchestration_contracts WHERE project=? AND task=?", project, t["id"]).Scan(&frozen); e != nil {
		return nil, nil, "", Fail(422, "GATE_FAILED", "submitted frozen review task required")
	}
	contract, e := Decode([]byte(frozen))
	if e != nil {
		return nil, nil, "", e
	}
	if Hash(contract) != Hash(t["acceptance_contract"]) || contract["contract_hash"] != contractDigest(contract) {
		return nil, nil, "", Fail(422, "GATE_FAILED", "review task contract changed")
	}
	if _, e = s.runDependenciesCurrent(tx, project, t, r); e != nil {
		return nil, nil, "", e
	}
	for _, value := range append(Arr(t, "input_refs"), Arr(t, "requirement_refs")...) {
		if e = s.effective(tx, project, value.(map[string]any)); e != nil {
			return nil, nil, "", e
		}
	}
	observation, e := runtimeObservation(tx, project, r)
	if e != nil {
		return nil, nil, "", e
	}
	var observedHash string
	if e = tx.QueryRow("SELECT receipt_hash FROM runtime_observations WHERE project=? AND run=? AND epoch=? ORDER BY observed_at DESC LIMIT 1", project, r["id"], r["lease_epoch"]).Scan(&observedHash); e != nil {
		return nil, nil, "", e
	}
	protocol, _ := observation["protocol"].(map[string]any)
	spec, _ := observation["spec"].(map[string]any)
	if observedHash != Hash(observation) || spec["run_id"] != r["id"] || spec["task_id"] != t["id"] || Hash(spec["epoch"]) != Hash(r["lease_epoch"]) || observation["state"] != "SETTLED" || protocol["settled"] != true || observation["children_stopped"] != true || observation["queue_empty"] != true {
		return nil, nil, "", Fail(422, "GATE_FAILED", "trusted settled review observation changed")
	}
	registration, e := load(tx, project, "RuntimeRegistration", Str(r, "runtime_id"))
	if e != nil {
		return nil, nil, "", e
	}
	var fixture int
	if e = tx.QueryRow("SELECT count(*) FROM orchestration_fixtures WHERE project=? AND runtime=?", project, registration["id"]).Scan(&fixture); e != nil {
		return nil, nil, "", e
	}
	if fixture != 1 || registration["measurement_mode"] != "FIXTURE" || registration["status"] == "REVOKED" || registration["status"] == "UNAVAILABLE" {
		return nil, nil, "", Fail(503, "RESOURCE_UNAVAILABLE", "qualified review runtime unavailable")
	}
	a, use, e := s.artifactUse(tx, project, r, Arr(r, "result_artifact_ids")[0].(string), true)
	if e != nil {
		return nil, nil, "", e
	}
	if a["kind"] != "REPORT" || a["media_type"] != "application/json" || a["access_class"] != "PROJECT" || a["measurement_mode"] != "FIXTURE" || use["measurement_mode"] != "FIXTURE" {
		return nil, nil, "", Fail(422, "GATE_FAILED", "review output must be a project-readable fixture report")
	}
	manifest := Arr(observation, "artifacts")
	entry, ok := map[string]any(nil), false
	if len(manifest) == 1 {
		entry, ok = manifest[0].(map[string]any)
	}
	if !ok || entry["content_hash"] != a["content_hash"] || Hash(entry["byte_size"]) != Hash(a["byte_size"]) {
		return nil, nil, "", Fail(422, "GATE_FAILED", "review report differs from trusted output manifest")
	}
	var raw []byte
	if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, use["storage_key"]).Scan(&raw); e != nil {
		return nil, nil, "", e
	}
	if Digest(raw) != a["content_hash"] {
		return nil, nil, "", Fail(422, "CONTENT_HASH_MISMATCH", "review bytes changed")
	}
	report, e := Decode(raw)
	if e != nil {
		return nil, nil, "", Fail(422, "GATE_FAILED", "review report is not a JSON object")
	}
	if (len(report) != 5 && len(report) != 6) || report["proposal_id"] != proposal["id"] || report["change_contract_hash"] != changeHash(proposal) || strings.TrimSpace(Str(report, "reason")) == "" {
		return nil, nil, "", Fail(422, "GATE_FAILED", "review report does not bind this frozen proposal")
	}
	if len(report) == 6 && Str(report, "previous_review_run_id") == "" {
		return nil, nil, "", Fail(422, "GATE_FAILED", "review continuation must identify previous run")
	}
	additional, ok := report["additional_impacted_refs"].([]any)
	if !ok || !exactUnique(additional) {
		return nil, nil, "", Fail(422, "GATE_FAILED", "invalid review impact vector")
	}
	conflicts, ok := report["conflict_ids"].([]any)
	if !ok || !exactUnique(conflicts) {
		return nil, nil, "", Fail(422, "GATE_FAILED", "invalid review conflict vector")
	}
	return report, a, Str(r, "executor_principal_id"), nil
}

type semanticReview struct {
	report   Object
	artifact Object
	executor string
	runID    string
}

func (s *Service) semanticReviews(tx *sql.Tx, project string, proposal Object, continuing bool) ([]semanticReview, error) {
	reviews := []semanticReview{}
	seen := map[string]bool{}
	for runID := Str(proposal, "semantic_review_run_id"); runID != ""; {
		if seen[runID] || len(reviews) >= 16 {
			return nil, Fail(422, "GATE_FAILED", "cyclic or excessive review history")
		}
		seen[runID] = true
		report, artifact, executor, e := s.semanticEvidence(tx, project, proposal, runID)
		if e != nil {
			return nil, e
		}
		refs, e := reviewLinkRefs(tx, project, proposal, artifact)
		if e != nil {
			return nil, e
		}
		if Hash(sortedHashes(refs)) != Hash(sortedHashes(Arr(report, "additional_impacted_refs"))) {
			return nil, Fail(422, "GATE_FAILED", "semantic impact links differ from sealed review")
		}
		for _, value := range Arr(report, "conflict_ids") {
			conflict, err := load(tx, project, "Conflict", value.(string))
			if err != nil {
				return nil, err
			}
			current := len(reviews) == 0
			if current && !continuing && proposal["status"] == "BLOCKED" && conflict["status"] == "OPEN" {
				continue
			}
			if err = resolvedReviewConflict(tx, project, proposal, conflict); err != nil {
				return nil, err
			}
		}
		reviews = append(reviews, semanticReview{report, artifact, executor, runID})
		runID = Str(report, "previous_review_run_id")
	}
	if len(reviews) == 0 {
		return nil, Fail(422, "GATE_FAILED", "semantic review unavailable")
	}
	if !continuing && len(Arr(reviews[0].report, "conflict_ids")) != 0 && proposal["status"] != "BLOCKED" {
		return nil, Fail(409, "STATE_CONFLICT", "semantic conflict remains blocking")
	}
	return reviews, nil
}

func resolvedReviewConflict(tx *sql.Tx, project string, proposal, conflict Object) error {
	if conflict["status"] != "RESOLVED" || conflict["resolution_proposal_id"] == nil || conflict["resolution_proposal_id"] == proposal["id"] {
		return Fail(409, "STATE_CONFLICT", "semantic conflict requires formal resolution")
	}
	resolution, e := load(tx, project, "ChangeProposal", Str(conflict, "resolution_proposal_id"))
	if e != nil {
		return e
	}
	if resolution["status"] != "APPLIED" {
		return Fail(409, "STATE_CONFLICT", "semantic conflict resolution was not applied")
	}
	return nil
}

func (s *Service) analyzeChangeImpact(tx *sql.Tx, p Principal, project, id string, b Object) (Object, error) {
	proposal, e := load(tx, project, "ChangeProposal", id)
	if e != nil {
		return nil, e
	}
	previous := copyObject(proposal)
	first := proposal["status"] == "IMPACT_ANALYZED" && proposal["semantic_review_run_id"] == nil
	continuing := (proposal["status"] == "BLOCKED" || proposal["status"] == "IMPACT_ANALYZED") && proposal["semantic_review_run_id"] != nil
	if (!first && !continuing) || proposal["acceptance_id"] != nil {
		return nil, Fail(409, "STATE_CONFLICT", "proposal is not awaiting semantic review")
	}
	if continuing {
		if _, e = s.semanticReviews(tx, project, proposal, true); e != nil {
			return nil, e
		}
	}
	report, artifact, _, e := s.semanticEvidence(tx, project, proposal, Str(b, "semantic_review_run_id"))
	if e != nil {
		return nil, e
	}
	if Hash(report["additional_impacted_refs"]) != Hash(b["additional_impacted_refs"]) || Hash(report["conflict_ids"]) != Hash(b["conflict_ids"]) {
		return nil, Fail(422, "GATE_FAILED", "review request differs from sealed report")
	}
	if continuing {
		if Str(b, "semantic_review_run_id") == Str(proposal, "semantic_review_run_id") || report["previous_review_run_id"] != proposal["semantic_review_run_id"] {
			return nil, Fail(422, "GATE_FAILED", "continuation must bind a new run to the prior review")
		}
	} else if report["previous_review_run_id"] != nil {
		return nil, Fail(422, "GATE_FAILED", "first review cannot claim a predecessor")
	}
	anchor := Arr(proposal, "edits")[0].(map[string]any)["target_ref"].(map[string]any)
	for _, value := range Arr(b, "additional_impacted_refs") {
		ref, ok := value.(map[string]any)
		if !ok {
			return nil, Fail(400, "INVALID_REQUEST", "invalid impact reference")
		}
		current, err := load(tx, project, Str(ref, "entity_type"), Str(ref, "id"))
		if err != nil {
			return nil, err
		}
		if Hash(Ref(current, Str(ref, "entity_type"))) != Hash(ref) || !s.visible(tx, p, project, current) || Hash(ref) == Hash(anchor) {
			return nil, Fail(412, "STALE_INPUT", "additional impact must be current, readable and distinct from edit root")
		}
		if _, err = s.impactLink(tx, project, Object{"from_ref": ref, "to_ref": anchor, "relation": "DEPENDS_ON", "basis": "SEMANTIC_REVIEW", "evidence_refs": []any{Ref(artifact, "Artifact"), Ref(proposal, "ChangeProposal")}}); err != nil {
			return nil, err
		}
	}
	// The review may identify conflicts; it never resolves them.
	for _, value := range Arr(b, "conflict_ids") {
		conflict, err := load(tx, project, "Conflict", value.(string))
		if err != nil {
			return nil, err
		}
		if conflict["status"] != "OPEN" || !s.visible(tx, p, project, conflict) {
			return nil, Fail(412, "STALE_INPUT", "review conflict is not open")
		}
	}
	proposal["semantic_review_run_id"] = b["semantic_review_run_id"]
	// checkChange recomputes the original roots plus semantic root and report.
	impacted, links, e := s.reviewClosure(tx, project, proposal)
	if e != nil {
		return nil, e
	}
	proposal["impacted_refs"] = impacted
	proposal["impact_link_ids"] = links
	if continuing {
		preserved := map[string]bool{}
		for _, ref := range impacted {
			r := ref.(map[string]any)
			preserved[Str(r, "entity_type")+":"+Str(r, "id")] = true
		}
		for _, value := range Arr(previous, "impacted_refs") {
			r := value.(map[string]any)
			if !preserved[Str(r, "entity_type")+":"+Str(r, "id")] {
				return nil, Fail(412, "STALE_INPUT", "prior impact disappeared from closure")
			}
		}
	}
	known := map[string]bool{Hash(Ref(proposal, "ChangeProposal")): true}
	for _, ref := range append(reviewInputs(proposal), impacted...) {
		known[Hash(ref)] = true
	}
	for _, value := range Arr(b, "conflict_ids") {
		conflict, err := load(tx, project, "Conflict", value.(string))
		if err != nil {
			return nil, err
		}
		related := false
		for _, ref := range Arr(conflict, "subject_refs") {
			related = related || known[Hash(ref)]
		}
		if !related {
			return nil, Fail(422, "GATE_FAILED", "review conflict has no subject in this change")
		}
	}
	formal, e := s.changeConflictsExcept(tx, project, proposal, stringSet(Arr(b, "conflict_ids")))
	if e != nil {
		return nil, e
	}
	proposal["conflict_ids"] = append(formal, Arr(b, "conflict_ids")...)
	proposal["status"] = "IMPACT_ANALYZED"
	if len(Arr(b, "conflict_ids")) > 0 {
		proposal["status"] = "BLOCKED"
	}
	if e = bump(proposal); e != nil {
		return nil, e
	}
	if e = s.put(tx, "ChangeProposal", proposal); e != nil {
		return nil, e
	}
	if _, e = s.checkChange(tx, p, project, proposal); e != nil {
		return nil, e
	}
	return proposal, nil
}

func stringSet(values []any) map[string]bool {
	set := map[string]bool{}
	for _, value := range values {
		set[value.(string)] = true
	}
	return set
}

func (s *Service) reviewClosure(tx *sql.Tx, project string, proposal Object) ([]any, []any, error) {
	roots := []Object{}
	for _, value := range Arr(proposal, "edits") {
		target := value.(map[string]any)["target_ref"].(map[string]any)
		roots = append(roots, target)
		if target["entity_type"] == "ProjectState" {
			current, e := load(tx, project, "ProjectState", Str(target, "id"))
			if e != nil {
				return nil, nil, e
			}
			proposed, e := s.artifactJSON(tx, project, value.(map[string]any)["proposed_value_artifact_ref"].(map[string]any))
			if e != nil {
				return nil, nil, e
			}
			for _, old := range Arr(current, "current_decision_refs") {
				if !containsRef(proposed.([]any), old.(map[string]any)) {
					roots = append(roots, old.(map[string]any))
				}
			}
		}
	}
	return s.closure(tx, project, roots)
}

func reviewLinkRefs(tx *sql.Tx, project string, proposal, artifact Object) ([]any, error) {
	refs := Empty()
	for _, value := range Arr(proposal, "impact_link_ids") {
		link, e := load(tx, project, "ImpactLink", value.(string))
		if e != nil {
			return nil, e
		}
		evidence := Arr(link, "evidence_refs")
		if link["basis"] == "SEMANTIC_REVIEW" && len(evidence) == 2 && Hash(evidence[0]) == Hash(Ref(artifact, "Artifact")) && evidence[1].(map[string]any)["entity_type"] == "ChangeProposal" && evidence[1].(map[string]any)["id"] == proposal["id"] {
			if link["status"] != "ACTIVE" || link["relation"] != "DEPENDS_ON" {
				return nil, Fail(422, "GATE_FAILED", "review impact link is inactive or malformed")
			}
			refs = append(refs, link["from_ref"])
		}
	}
	return refs, nil
}

func sortedHashes(values []any) []string {
	out := []string{}
	for _, value := range values {
		out = append(out, Hash(value))
	}
	sort.Strings(out)
	return out
}

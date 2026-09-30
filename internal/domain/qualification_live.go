package domain

import (
	"context"
	"database/sql"
	"researchos.local/research-os/adapters/decision"
	"researchos.local/research-os/adapters/protectedstore"
	holdout "researchos.local/research-os/evaluation/holdout/jev"
	"sort"
	"time"
)

const frozenDevelopmentDatasetHash = "sha256:c4408fcca39320561ed03de0b56c2a9b8400dadf4eccd1b99802599e685ee979"

var qualificationChecks = []string{"qualification.real-service", "qualification.exact-binding", "qualification.safe-failure"}

// QualificationThresholdsHash binds the frozen initial contract, not a client's
// preferred confidence or a statistic learned from the holdout.
func QualificationThresholdsHash() string {
	return Hash(Object{"confidence_threshold": holdout.Threshold, "minimum_development_cases": 60, "minimum_disjoint_holdout_cases": 30, "critical_false_accepts_max": 0, "false_accept_count_over_holdout_count_max": .05})
}

func qualificationContract(q Object) string {
	fields := Object{"checks": qualificationChecks, "rules": "W11-frozen-service-result-v1"}
	for _, key := range []string{"scope", "dataset_artifact_ref", "holdout_artifact_ref", "thresholds_hash", "thresholds_frozen_at", "total_case_count", "holdout_case_count", "label_basis", "measurement_mode", "expires_at"} {
		fields[key] = q[key]
	}
	return Hash(fields)
}

// This proof is internal Go state. JSON clients cannot manufacture a successful
// SCM/PID/binary-bound service query by submitting an aggregate or LIVE flag.
type preparedQualification struct {
	SubjectHash string
	PrincipalID string
	Summary     protectedstore.SafeSummary
}

func (s *Service) prepareQualification(ctx context.Context, token, project, id string) (*preparedQualification, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	p, e := authenticate(tx, token)
	if e == nil && (!p.HasRole("VERIFIER") || !p.Allowed(project, "", "", false)) {
		e = Fail(403, "FORBIDDEN", "independent verifier required")
	}
	var q Object
	if e == nil {
		q, e = s.readObject(tx, p, project, "Qualification", id)
	}
	tx.Rollback()
	if e != nil {
		return nil, e
	}
	if q["measurement_mode"] != "LIVE" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "only the independently protected live evaluation admits results")
	}
	if !protectedAllowed(p, project) {
		return nil, Fail(403, "FORBIDDEN", "restricted independent verifier required")
	}
	// No database transaction spans IPC. handle authenticates again, checks the
	// ETag, then matches this exact object and its current inputs before writing.
	summary, e := protectedstore.QueryFrozenService("aggregate")
	if e != nil {
		return nil, protectedFailure(e)
	}
	if summary.Frozen == nil || summary.Frozen.RunState != "COMPLETED" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "complete protected evaluation is unavailable")
	}
	return &preparedQualification{Hash(q), p.ID, summary}, nil
}

func (s *Service) qualificationBinding(tx *sql.Tx, p Principal, project string, q Object, proof *preparedQualification) (protectedstore.FrozenKeyCounts, []any, error) {
	var counts protectedstore.FrozenKeyCounts
	if proof == nil || proof.PrincipalID != p.ID || proof.SubjectHash != Hash(q) || !p.HasRole("VERIFIER") || !protectedAllowed(p, project) {
		return counts, nil, Fail(403, "FORBIDDEN", "current independent verification authority is required")
	}
	f := proof.Summary.Frozen
	if proof.Summary.Validate() != nil || f == nil || f.RunState != "COMPLETED" || f.Dataset == nil || f.Qualification != "FAILED" || proof.Summary.MaximumMode != "ADVISORY" {
		return counts, nil, Fail(503, "RESOURCE_UNAVAILABLE", "completed protected evaluation required")
	}
	if q["status"] != "DRAFT" || q["measurement_mode"] != "LIVE" || q["label_basis"] != "OBJECTIVE" || q["thresholds_hash"] != QualificationThresholdsHash() || q["thresholds_frozen_at"] != f.FrozenAt {
		return counts, nil, Fail(422, "GATE_FAILED", "qualification declaration differs from the frozen evaluation")
	}
	if expiry := Str(q, "expires_at"); expiry != "" {
		when, err := time.Parse(time.RFC3339Nano, expiry)
		if err != nil || !when.After(time.Now()) {
			return counts, nil, Fail(422, "GATE_FAILED", "qualification declaration expired")
		}
	}
	found := false
	for _, key := range f.Keys {
		if Hash(q["scope"]) == Hash(key.Scope) {
			counts, found = key, true
		}
	}
	if !found || Hash(q["total_case_count"]) != Hash(counts.DevelopmentCount+counts.Planned) || Hash(q["holdout_case_count"]) != Hash(counts.Planned) {
		return counts, nil, Fail(422, "GATE_FAILED", "scope or per-key sample counts differ")
	}
	authors := map[string]bool{}
	for _, name := range []string{"dataset_artifact_ref", "holdout_artifact_ref"} {
		ref, ok := q[name].(map[string]any)
		if !ok || ref["entity_type"] != "Artifact" {
			return counts, nil, Fail(422, "GATE_FAILED", "evaluation artifact required")
		}
		if e := s.effective(tx, project, ref); e != nil {
			return counts, nil, e
		}
		a, e := s.readObject(tx, p, project, "Artifact", Str(ref, "id"))
		if e != nil {
			return counts, nil, e
		}
		if a["validity"] != "CURRENT" || a["measurement_mode"] != "LIVE" {
			return counts, nil, Fail(422, "GATE_FAILED", "current live evaluation artifacts required")
		}
		if name == "dataset_artifact_ref" {
			if a["content_hash"] != frozenDevelopmentDatasetHash || a["access_class"] != "PROJECT" {
				return counts, nil, Fail(422, "GATE_FAILED", "public development dataset hash differs")
			}
			if _, e = s.artifactJSON(tx, project, ref); e != nil {
				return counts, nil, e
			}
		} else if a["access_class"] != "VERIFIER_ONLY" || a["content_hash"] != f.Dataset.Hash || a["storage_key"] != f.Dataset.Ticket || Hash(a["byte_size"]) != Hash(f.Dataset.Size) || a["media_type"] != f.Dataset.MediaType {
			return counts, nil, Fail(422, "GATE_FAILED", "protected dataset descriptor differs")
		}
		authors[Str(a, "produced_by")] = true
	}
	if authors[p.ID] {
		return counts, nil, Fail(403, "FORBIDDEN", "evaluation input registrar cannot independently accept it")
	}
	ids := make([]string, 0, len(authors))
	for id := range authors {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	result := Empty()
	for _, id := range ids {
		result = append(result, id)
	}
	return counts, result, nil
}

func (s *Service) acceptQualification(tx *sql.Tx, p Principal, project string, b Object, proof *preparedQualification) (Object, error) {
	r := b["subject_ref"].(map[string]any)
	q, e := s.readObject(tx, p, project, "Qualification", Str(r, "id"))
	if e != nil {
		return nil, e
	}
	_, authors, e := s.qualificationBinding(tx, p, project, q, proof)
	if e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(r) != Hash(Ref(q, "Qualification")) || b["contract_hash"] != qualificationContract(q) || Hash(b["policy_revision"]) != Hash(state["policy_revision"]) || b["measurement_mode"] != "LIVE" || b["run_id"] != nil {
		return nil, Fail(422, "GATE_FAILED", "qualification acceptance binding differs")
	}
	// The authenticated service deliberately declassifies only its fixed terminal
	// aggregate. This is the only public output; private content/lineage never
	// enters uploads, prompts, previews, logs or this control-plane database.
	raw := decision.Encode(proof.Summary)
	u, e := s.upload(tx, p, project, raw)
	if e != nil {
		return nil, e
	}
	evidence, e := s.seal(tx, p, project, Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"})
	if e != nil {
		return nil, e
	}
	checks := Empty()
	for _, id := range qualificationChecks {
		checks = append(checks, Object{"check_id": id, "status": "PASS", "evidence_refs": []any{Ref(evidence, "Artifact")}, "command_key": "test.jev.live", "actual": "Independent protected service completed the exact frozen evaluation; qualification FAILED and automatic authority NONE.", "exit_code": 0, "started_at": proof.Summary.Frozen.FrozenAt, "finished_at": Now()})
	}
	o := Object{"id": ID(), "project_id": project, "revision": 1, "created_at": Now(), "subject_ref": r, "run_id": nil, "contract_hash": qualificationContract(q), "input_refs": []any{q["dataset_artifact_ref"], q["holdout_artifact_ref"]}, "artifact_refs": []any{Ref(evidence, "Artifact")}, "checks": checks, "verdict": "PASS", "verifier_principal_id": p.ID, "executor_principal_ids": authors, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": state["policy_revision"], "measurement_mode": "LIVE", "reason": "Completed protected evaluation accepted as evidence; the model has no automatic qualification."}
	o["receipt_hash"] = Receipt(o)
	if e = qualificationReceiptBinding(q, o, authors, p.ID, state["policy_revision"], o["artifact_refs"]); e != nil {
		return nil, e
	}
	return o, s.put(tx, "AcceptanceReceipt", o)
}

// The live writer and offline upgrade use the same evidence semantics. Callers
// supply the exact accepted DRAFT, its actual input authors and policy snapshot.
// This validates preserved evidence; it does not issue verification authority.
func qualificationReceiptBinding(q, receipt Object, authors []any, verifier string, policy, testRefs any) error {
	if q["status"] != "DRAFT" || receipt["project_id"] != q["project_id"] || Hash(receipt["revision"]) != Hash(1) ||
		receipt["verdict"] != "PASS" || receipt["receipt_hash"] != Receipt(receipt) || receipt["contract_hash"] != qualificationContract(q) ||
		Hash(receipt["subject_ref"]) != Hash(Ref(q, "Qualification")) || verifier == "" || receipt["verifier_principal_id"] != verifier ||
		receipt["measurement_mode"] != "LIVE" || Hash(receipt["policy_revision"]) != Hash(policy) || receipt["run_id"] != nil ||
		Hash(testRefs) != Hash(receipt["artifact_refs"]) || len(Arr(receipt, "artifact_refs")) != 1 ||
		Hash(receipt["input_refs"]) != Hash([]any{q["dataset_artifact_ref"], q["holdout_artifact_ref"]}) ||
		len(authors) == 0 || Hash(receipt["executor_principal_ids"]) != Hash(authors) || receipt["independence_basis"] != "DETERMINISTIC_SERVICE" ||
		len(Arr(receipt, "blocking_conflict_ids")) != 0 || len(Arr(receipt, "qualification_ids")) != 0 {
		return Fail(422, "GATE_FAILED", "independent evaluation acceptance does not bind this result")
	}
	for _, author := range authors {
		if author == "" || author == verifier {
			return Fail(422, "GATE_FAILED", "evaluation input registrar cannot independently accept it")
		}
	}
	checks := Arr(receipt, "checks")
	if len(checks) != len(qualificationChecks) {
		return Fail(422, "GATE_FAILED", "all frozen qualification checks required")
	}
	seen := map[string]bool{}
	for _, value := range checks {
		check, ok := value.(map[string]any)
		if !ok {
			return Fail(422, "GATE_FAILED", "invalid qualification check")
		}
		id, known := Str(check, "check_id"), false
		for _, expected := range qualificationChecks {
			known = known || id == expected
		}
		if !known || seen[id] || check["status"] != "PASS" || check["command_key"] != "test.jev.live" || Hash(check["exit_code"]) != Hash(0) || Hash(check["evidence_refs"]) != Hash(receipt["artifact_refs"]) {
			return Fail(422, "GATE_FAILED", "qualification check differs from frozen evidence")
		}
		seen[id] = true
	}
	return nil
}

func (s *Service) recordQualificationResult(tx *sql.Tx, p Principal, project, id string, b Object, proof *preparedQualification) (Object, error) {
	q, e := s.readObject(tx, p, project, "Qualification", id)
	if e != nil {
		return nil, e
	}
	counts, authors, e := s.qualificationBinding(tx, p, project, q, proof)
	if e != nil {
		return nil, e
	}
	receipt, e := s.readObject(tx, p, project, "AcceptanceReceipt", Str(b, "acceptance_id"))
	if e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if e = qualificationReceiptBinding(q, receipt, authors, p.ID, state["policy_revision"], b["test_receipt_refs"]); e != nil {
		return nil, e
	}
	value, e := s.artifactJSON(tx, project, Arr(receipt, "artifact_refs")[0].(map[string]any))
	if e != nil {
		return nil, e
	}
	if Hash(value) != Hash(proof.Summary) {
		return nil, Fail(422, "GATE_FAILED", "accepted aggregate differs from the authenticated service")
	}
	if counts.Planned <= 0 || counts.PositiveLabelCount <= 0 {
		return nil, Fail(422, "GATE_FAILED", "measured label denominators required")
	}
	fa := float64(counts.FalseAccept) / float64(counts.Planned)
	fr := float64(counts.FalseReject) / float64(counts.PositiveLabelCount)
	abstain := float64(counts.Abstain) / float64(counts.Planned)
	if Hash(b["critical_false_accept_count"]) != Hash(counts.CriticalFalseAccept) || Hash(b["false_accept_rate"]) != Hash(fa) || Hash(b["false_reject_rate"]) != Hash(fr) || Hash(b["abstain_rate"]) != Hash(abstain) {
		return nil, Fail(422, "GATE_FAILED", "client statistics differ from protected measurements")
	}
	Merge(q, Object{"status": "FAILED", "maximum_mode": "ADVISORY", "jev_called": true, "critical_false_accept_count": counts.CriticalFalseAccept, "false_accept_rate": fa, "false_reject_rate": fr, "abstain_rate": abstain, "test_receipt_refs": receipt["artifact_refs"], "acceptance_id": receipt["id"]})
	if e = bump(q); e != nil {
		return nil, e
	}
	return q, s.put(tx, "Qualification", q)
}

package domain

import (
	"database/sql"
	"time"
)

// A DRAFT is a frozen declaration, not a claim that labels or model calls have
// been independently verified. Result admission remains closed until the
// protected evaluator provides a verified result, rather than client counts.
func (s *Service) createQualification(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	frozen, e := time.Parse(time.RFC3339Nano, Str(b, "thresholds_frozen_at"))
	if e != nil || frozen.After(time.Now()) {
		return nil, Fail(422, "GATE_FAILED", "thresholds must already be frozen")
	}
	if b["expires_at"] != nil {
		expiry, e := time.Parse(time.RFC3339Nano, Str(b, "expires_at"))
		if e != nil || !expiry.After(time.Now()) {
			return nil, Fail(422, "GATE_FAILED", "qualification expiry must be in the future")
		}
	}
	holdout, _ := Num(b, "holdout_case_count")
	total, _ := Num(b, "total_case_count")
	if holdout > total || Hash(b["dataset_artifact_ref"]) == Hash(b["holdout_artifact_ref"]) {
		return nil, Fail(422, "GATE_FAILED", "distinct development and holdout references required")
	}
	for _, key := range []string{"dataset_artifact_ref", "holdout_artifact_ref"} {
		ref := b[key].(map[string]any)
		if ref["entity_type"] != "Artifact" {
			return nil, Fail(422, "GATE_FAILED", "dataset artifact required")
		}
		if e = s.effective(tx, project, ref); e != nil {
			return nil, e
		}
		a, e := s.readObject(tx, p, project, "Artifact", Str(ref, "id"))
		if e != nil {
			return nil, e
		}
		if e = s.requireCurrentArtifactBody(tx, project, a); e != nil {
			return nil, e
		}
	}
	o := Merge(Base(project), b)
	o = Merge(o, Object{"status": "DRAFT", "maximum_mode": "ADVISORY", "jev_called": false, "critical_false_accept_count": 0, "false_accept_rate": nil, "false_reject_rate": nil, "abstain_rate": nil, "test_receipt_refs": Empty(), "acceptance_id": nil})
	return o, s.put(tx, "Qualification", o)
}

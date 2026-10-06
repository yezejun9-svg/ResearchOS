package domain

import (
	"context"
	"database/sql"
	"researchos.local/research-os/adapters/protectedstore"
)

// ImportFrozenQualifications registers the completed service's opaque dataset
// and public development bytes. It creates declarations, never acceptances.
func (s *Service) ImportFrozenQualifications(ctx context.Context, token, project string, development []byte) (Object, error) {
	if Digest(development) != frozenDevelopmentDatasetHash {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "frozen public development dataset required")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	p, e := authenticate(tx, token)
	if e == nil && (!p.HasRole("OWNER") || !protectedAllowed(p, project)) {
		e = Fail(403, "FORBIDDEN", "restricted owner required")
	}
	tx.Rollback()
	if e != nil {
		return nil, e
	}
	summary, e := protectedstore.QueryFrozenService("aggregate")
	if e != nil {
		return nil, protectedFailure(e)
	}
	if summary.Validate() != nil || summary.Frozen == nil || summary.Frozen.RunState != "COMPLETED" || summary.Frozen.Dataset == nil {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "completed protected evaluation required")
	}
	metadata := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "input_refs": Empty(), "source_refs": Empty()}
	private, e := s.RegisterProtectedArtifact(ctx, token, project, summary.Frozen.Dataset.Ticket, metadata)
	if e != nil {
		return nil, e
	}
	tx, e = s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	current, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if current.ID != p.ID || !current.HasRole("OWNER") || !protectedAllowed(current, project) {
		return nil, Fail(403, "FORBIDDEN", "registration authority changed")
	}
	if e = s.effective(tx, project, Ref(private, "Artifact")); e != nil {
		return nil, e
	}
	u, e := s.upload(tx, current, project, development)
	if e != nil {
		return nil, e
	}
	public, e := s.seal(tx, current, project, Merge(copyObject(metadata), Object{"content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(development), "produced_by": current.ID, "access_class": "PROJECT"}))
	if e != nil {
		return nil, e
	}
	result, e := s.frozenDeclarations(tx, current, project, summary, public, private)
	if e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return result, nil
}

func (s *Service) frozenDeclarations(tx *sql.Tx, p Principal, project string, summary protectedstore.SafeSummary, public, private Object) (Object, error) {
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	result := Empty()
	for _, key := range summary.Frozen.Keys {
		request := Object{"scope": key.Scope, "dataset_artifact_ref": Ref(public, "Artifact"), "holdout_artifact_ref": Ref(private, "Artifact"), "thresholds_hash": QualificationThresholdsHash(), "thresholds_frozen_at": summary.Frozen.FrozenAt, "total_case_count": key.DevelopmentCount + key.Planned, "holdout_case_count": key.Planned, "label_basis": "OBJECTIVE", "measurement_mode": "LIVE", "jev_called": false, "expires_at": nil}
		// Convert typed scope and integer counters to the normal JSON domain form.
		request, e = Decode(Bytes(request))
		if e != nil {
			return nil, e
		}
		if e = s.Contracts.Validate("CreateQualificationRequest", request); e != nil {
			return nil, e
		}
		var prior string
		e = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Qualification' AND json_extract(body,'$.dataset_artifact_ref.id')=? AND json_extract(body,'$.holdout_artifact_ref.id')=? AND json_extract(body,'$.scope.language')=? ORDER BY rowid LIMIT 1", project, public["id"], private["id"], key.Scope.Language).Scan(&prior)
		var q Object
		if e == nil {
			q, e = Decode([]byte(prior))
			if e != nil {
				return nil, e
			}
			if qualificationContract(q) != qualificationContract(request) {
				return nil, Fail(409, "STATE_CONFLICT", "existing evaluation declaration differs")
			}
		} else if e == sql.ErrNoRows {
			q, e = s.createQualification(tx, p, project, request)
			if e != nil {
				return nil, e
			}
			if e = s.event(tx, project, "Qualification", q, p.ID, ID(), "PROJECT_UPDATED"); e != nil {
				return nil, e
			}
		} else {
			return nil, e
		}
		result = append(result, Object{"qualification": q, "contract_hash": qualificationContract(q), "check_ids": qualificationChecks, "policy_revision": state["policy_revision"]})
	}
	return Object{"project_id": project, "qualifications": result, "requires_independent_verifier": true, "automatic_authority": "NONE"}, nil
}

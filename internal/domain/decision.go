package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"researchos.local/research-os/adapters/decision"
	"sort"
	"strings"
)

var decisionOperations = map[string]bool{"recordDecision": true, "getDecisionReceipt": true, "listDecisionReceipt": true, "createQualification": true, "getQualification": true, "listQualification": true, "recordQualificationResult": true}

func init() {
	for op := range decisionOperations {
		implemented[op] = true
	}
}
func (s *Service) decisionOperation(tx *sql.Tx, p Principal, project, id string, b Object, op string) (Object, string, int, error) {
	switch op {
	case "recordDecision":
		o, e := s.recordDecision(tx, p, project, b)
		return o, "DecisionReceipt", 201, e
	case "createQualification":
		o, e := s.createQualification(tx, p, project, b)
		return o, "Qualification", 201, e
	case "recordQualificationResult":
		return nil, "", 0, Fail(503, "RESOURCE_UNAVAILABLE", "independent protected evaluation provenance is required; client statistics cannot grant qualification")
	}
	return nil, "", 0, Fail(503, "RESOURCE_UNAVAILABLE", "decision operation unavailable")
}

// DecisionRubric is sealed before invocation. No model-generated rubric is accepted here.
type DecisionRubric struct {
	Schema              string                       `json:"schema"`
	Revision            string                       `json:"revision"`
	ConfidenceThreshold float64                      `json:"confidence_threshold"`
	Questions           map[string]decision.Question `json:"questions"`
}

// This in-process capability cannot be represented by a JSON request. Only the
// host invocation path can attest that a LIVE response was actually requested.
type decisionInvocationProof struct{ RawHash string }

func (s *Service) decisionRubric(tx *sql.Tx, project string, b Object) (DecisionRubric, error) {
	var rubric DecisionRubric
	v, e := s.artifactJSON(tx, project, b["rubric_ref"].(map[string]any))
	if e != nil {
		return rubric, e
	}
	if decision.Strict(Bytes(v), &rubric) != nil || rubric.Schema != "researchos.jev-rubric.v1" || rubric.Revision != Str(b["scope"].(map[string]any), "rubric_revision") || rubric.ConfidenceThreshold < 0.5 || rubric.ConfidenceThreshold > 1 {
		return rubric, Fail(422, "GATE_FAILED", "frozen typed decision rubric required")
	}
	q, ok := rubric.Questions["action"]
	if !ok || q.Type != "choice" {
		return rubric, Fail(422, "GATE_FAILED", "rubric must measure the action option set")
	}
	var criteria map[string]string
	if decision.Strict(Bytes(q.Criteria), &criteria) != nil || len(criteria) != len(Arr(b, "options")) {
		return rubric, Fail(422, "GATE_FAILED", "rubric and decision options differ")
	}
	for _, v := range Arr(b, "options") {
		if _, ok := criteria[v.(string)]; !ok {
			return rubric, Fail(422, "GATE_FAILED", "rubric and decision options differ")
		}
	}
	return rubric, nil
}
func (s *Service) prepareDecision(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	if b["mode"] == "BOUNDED_AUTO" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "BOUNDED_AUTO awaits independent protected qualification; automatic authority is disabled")
	}
	if len(Arr(b, "signals")) == 0 && b["qualification_id"] == nil {
		return b, nil
	}
	b = copyObject(b)
	proof, _ := b["_host_invocation"].(decisionInvocationProof)
	delete(b, "_host_invocation")
	for _, v := range Arr(b, "input_refs") {
		ref := v.(map[string]any)
		if _, e := s.readObject(tx, p, project, Str(ref, "entity_type"), Str(ref, "id")); e != nil {
			return nil, e
		}
		if e := s.effective(tx, project, ref); e != nil {
			return nil, e
		}
	}
	reasons := []string{}
	signals := Empty()
	selected := ""
	if qid := Str(b, "qualification_id"); qid != "" {
		q, e := s.readObject(tx, p, project, "Qualification", qid)
		if e != nil {
			return nil, e
		}
		if Hash(q["scope"]) != Hash(b["scope"]) || q["status"] != "PASSED" {
			reasons = append(reasons, "QUALIFICATION_NOT_VALID_FOR_SCOPE")
		}
		b["qualification_id"] = nil
	}
	if len(Arr(b, "signals")) > 0 {
		rubric, e := s.decisionRubric(tx, project, b)
		if e != nil {
			return nil, e
		}
		seen := map[string]bool{}
		for _, v := range Arr(b, "signals") {
			supplied := v.(map[string]any)
			ref := supplied["raw_artifact_ref"].(map[string]any)
			key := Hash(ref)
			if seen[key] {
				continue
			}
			seen[key] = true
			value, e := s.artifactJSON(tx, project, ref)
			if e != nil {
				return nil, e
			}
			var env decision.Envelope
			result := decision.Result{Abstained: true, Reasons: []string{"INVALID_RAW_ENVELOPE"}}
			scope := b["scope"].(map[string]any)
			if decision.Strict(Bytes(value), &env) == nil && env.Binding.ProjectID == project && env.Binding.InputHash == b["input_hash"] && env.Binding.RubricHash == b["rubric_ref"].(map[string]any)["content_hash"] && Hash(env.Binding.Scope) == Hash(scope) && Hash(env.Request.Questions) == Hash(rubric.Questions) {
				result = decision.Evaluate(env, rubric.ConfidenceThreshold)
			}
			if result.Abstained {
				reasons = append(reasons, result.Reasons...)
			}
			if result.Selected != "" {
				if selected != "" && selected != result.Selected {
					reasons = append(reasons, "CONTRADICTORY_MODEL_ACTIONS")
				}
				selected = result.Selected
			}
			mode := "FIXTURE"
			called := false
			if env.MeasurementMode == "LIVE" && env.JevCalled && proof.RawHash == Str(ref, "content_hash") {
				mode = "LIVE"
				called = true
			} else if env.MeasurementMode == "LIVE" {
				reasons = append(reasons, "UNVERIFIED_IMPORTED_INVOCATION")
			}
			if len(result.Signals) == 0 {
				signals = append(signals, Object{"adapter": decision.Adapter, "provider": scope["provider"], "model_revision": scope["model_revision"], "jev_called": called, "measurement_mode": mode, "operation": "CHOICE", "raw_artifact_ref": ref, "value": nil, "probability": nil, "host_abstained": true, "abstain_reason": strings.Join(result.Reasons, ";")})
			}
			for _, a := range result.Signals {
				var reason any
				if a.Abstained {
					reason = a.Reason
				}
				signals = append(signals, Object{"adapter": decision.Adapter, "provider": scope["provider"], "model_revision": scope["model_revision"], "jev_called": called, "measurement_mode": mode, "operation": a.Operation, "raw_artifact_ref": ref, "value": a.Value, "probability": a.Probability, "host_abstained": a.Abstained, "abstain_reason": reason})
			}
		}
		if selected == "" {
			reasons = append(reasons, "ACTION_NOT_MEASURED")
		} else if selected != b["selected"] {
			reasons = append(reasons, "SELECTED_DIFFERS_FROM_MEASURED_ACTION")
		}
	}
	for _, v := range Arr(b, "deterministic_results") {
		check := v.(map[string]any)
		if check["status"] != "PASS" && check["status"] != "NOT_APPLICABLE" {
			reasons = append(reasons, "DETERMINISTIC_CHECK_NOT_PASSED:"+Str(check, "check_id"))
		}
	}
	if len(Arr(b, "missing_evidence")) > 0 {
		reasons = append(reasons, "MISSING_EVIDENCE")
	}
	if b["status"] != "DECIDED" {
		reasons = append(reasons, "CALLER_ABSTAIN_OR_ERROR")
	}
	b["signals"] = signals
	if len(reasons) > 0 {
		sort.Strings(reasons)
		b["status"] = "ABSTAIN"
		b["rationale"] = Str(b, "rationale") + "; host gate: " + strings.Join(reasons, ";")
	}
	return b, nil
}

// InvokeJev is the authenticated host entry point. Credentials stay in the caller's
// Client, never in an Artifact. Imported envelopes are advisory evidence only;
// this method does not confer qualification or acceptance authority.
func (s *Service) InvokeJev(ctx context.Context, token, project string, b Object, client decision.Client) (Object, error) {
	var principal string
	var binding decision.Binding
	var request decision.Request
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	p, e := authenticate(tx, token)
	if e == nil && (!(p.HasRole("OWNER") || p.HasRole("PLANNER")) || !p.Allowed(project, "", "", false)) {
		e = Fail(403, "FORBIDDEN", "project planner required")
	}
	if e == nil {
		e = s.Contracts.Validate("CreateDecisionRequest", b)
	}
	if e == nil && (b["mode"] == "BOUNDED_AUTO" || len(Arr(b, "signals")) != 0 || b["qualification_id"] != nil) {
		e = Fail(422, "GATE_FAILED", "host invocation starts with unqualified SHADOW or ADVISORY request")
	}
	var rubric DecisionRubric
	if e == nil {
		rubric, e = s.decisionRubric(tx, project, b)
	}
	if e == nil {
		for _, v := range Arr(b, "input_refs") {
			if e = s.effective(tx, project, v.(map[string]any)); e != nil {
				break
			}
		}
	}
	if e == nil && b["input_hash"] != Hash(b["input_refs"]) {
		e = Fail(422, "GATE_FAILED", "input hash mismatch")
	}
	if e == nil {
		_ = json.Unmarshal(Bytes(b["scope"]), &binding.Scope)
		binding.ProjectID = project
		binding.InputHash = Str(b, "input_hash")
		binding.RubricHash = Str(b["rubric_ref"].(map[string]any), "content_hash")
		inputs := []any{}
		for _, v := range Arr(b, "input_refs") {
			ref := v.(map[string]any)
			o, err := s.readObject(tx, p, project, Str(ref, "entity_type"), Str(ref, "id"))
			if err != nil {
				e = err
				break
			}
			if o["access_class"] == "VERIFIER_ONLY" {
				e = Fail(403, "FORBIDDEN", "protected evaluation material cannot enter decision prompts")
				break
			}
			inputs = append(inputs, o)
		}
		request = decision.Request{Model: binding.Scope.ModelRevision, State: Object{"binding": binding, "inputs": inputs}, Questions: rubric.Questions}
		principal = p.ID
	}
	tx.Rollback()
	if e != nil {
		return nil, e
	}
	envelope, e := client.Call(ctx, binding, request)
	if e != nil {
		return nil, e
	}
	tx, e = s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e = authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if p.ID != principal || !p.Allowed(project, "", "", false) || !(p.HasRole("OWNER") || p.HasRole("PLANNER")) {
		return nil, Fail(403, "FORBIDDEN", "planner authorization changed")
	}
	// Freeze actual response even on timeout; then record the decision transactionally.
	raw := Bytes(envelope)
	u, e := s.upload(tx, p, project, raw)
	if e != nil {
		return nil, e
	}
	artifact := Merge(Base(project), Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": envelope.MeasurementMode, "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": b["input_refs"], "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT", "validity": "CURRENT", "sealed_at": Now()})
	if e = s.put(tx, "Artifact", artifact); e != nil {
		return nil, e
	}
	if _, e = tx.Exec("UPDATE uploaded_content SET sealed=1 WHERE project=? AND storage_key=?", project, artifact["storage_key"]); e != nil {
		return nil, e
	}
	b = copyObject(b)
	b["_host_invocation"] = decisionInvocationProof{RawHash: Str(artifact, "content_hash")}
	b["signals"] = []any{Object{"raw_artifact_ref": Ref(artifact, "Artifact")}}
	b["evidence_refs"] = append(Arr(b, "evidence_refs"), Ref(artifact, "Artifact"))
	receipt, e := s.recordDecision(tx, p, project, b)
	if e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "DecisionReceipt", receipt, p.ID, ID(), "DECISION_RECORDED"); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return receipt, nil
}

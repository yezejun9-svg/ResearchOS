package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"mime"
	"researchos.local/research-os/adapters/decision"
	"sort"
	"strings"
	"unicode/utf8"
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

const decisionArtifactLimit = 256 << 10
const decisionPromptLimit = 1 << 20

// The local entry point has no HTTP middleware, so it must enforce the same
// visible graph and current-version rules itself, both before and after IO.
func (s *Service) checkDecisionGraph(tx *sql.Tx, p Principal, project string, b Object) error {
	if !s.visible(tx, p, project, b) || !s.visible(tx, Principal{ID: p.ID, Roles: []string{"READER"}, Grants: []Grant{{ProjectID: project}}}, project, b) {
		return Fail(403, "FORBIDDEN", "decision graph contains inaccessible or protected evidence")
	}
	for _, ref := range semanticReferences("DecisionReceipt", b) {
		if _, e := s.readObject(tx, p, project, Str(ref, "entity_type"), Str(ref, "id")); e != nil {
			return e
		}
		if e := s.effective(tx, project, ref); e != nil {
			return e
		}
	}
	return nil
}

func (s *Service) decisionPromptInputs(tx *sql.Tx, p Principal, project string, b Object) ([]any, error) {
	if e := s.checkDecisionGraph(tx, p, project, b); e != nil {
		return nil, e
	}
	inputs := Empty()
	total := 0
	for _, ref := range semanticReferences("DecisionReceipt", b) {
		o, e := s.readObject(tx, p, project, Str(ref, "entity_type"), Str(ref, "id"))
		if e != nil {
			return nil, e
		}
		entry := Object{"ref": ref, "metadata": o}
		if ref["entity_type"] == "Artifact" {
			if o["access_class"] != "PROJECT" {
				return nil, Fail(403, "FORBIDDEN", "protected evidence cannot enter prompts")
			}
			if e = s.requireCurrentArtifactBody(tx, project, o); e != nil {
				return nil, e
			}
			media, _, e := mime.ParseMediaType(Str(o, "media_type"))
			if e != nil || !(strings.HasPrefix(media, "text/") || media == "application/json" || strings.HasSuffix(media, "+json")) {
				return nil, Fail(422, "GATE_FAILED", "decision evidence must be text or JSON; binary body is not sent")
			}
			size, e := Num(o, "byte_size")
			if e != nil || size < 0 || size > decisionArtifactLimit {
				return nil, Fail(422, "GATE_FAILED", "decision artifact exceeds 256 KiB bound")
			}
			var raw []byte
			if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1 AND length(bytes)<=?", project, o["storage_key"], decisionArtifactLimit).Scan(&raw); e != nil || int64(len(raw)) != size || Digest(raw) != o["content_hash"] {
				return nil, Fail(422, "CONTENT_HASH_MISMATCH", "current sealed decision body unavailable")
			}
			if !utf8.Valid(raw) {
				return nil, Fail(422, "GATE_FAILED", "decision evidence must be valid UTF-8")
			}
			if media == "application/json" || strings.HasSuffix(media, "+json") {
				var value any
				if decision.Strict(raw, &value) != nil {
					return nil, Fail(422, "GATE_FAILED", "decision JSON evidence must be strict valid JSON")
				}
			}
			entry["body"] = string(raw)
			entry["body_sha256"] = o["content_hash"]
		}
		total += len(Bytes(entry))
		if total > decisionPromptLimit {
			return nil, Fail(422, "GATE_FAILED", "decision prompt exceeds 1 MiB bound")
		}
		inputs = append(inputs, entry)
	}
	return inputs, nil
}

func (s *Service) sealDecisionEnvelope(tx *sql.Tx, p Principal, project string, b Object, envelope decision.Envelope) (Object, error) {
	raw := Bytes(envelope)
	u, e := s.upload(tx, p, project, raw)
	if e != nil {
		return nil, e
	}
	refs := Empty()
	for _, ref := range semanticReferences("DecisionReceipt", b) {
		refs = append(refs, ref)
	}
	return s.seal(tx, p, project, Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": envelope.MeasurementMode, "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": refs, "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"})
}

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
func decisionHardFailures(b Object) []string {
	reasons := []string{}
	for _, v := range Arr(b, "deterministic_results") {
		check := v.(map[string]any)
		if check["status"] != "PASS" && check["status"] != "NOT_APPLICABLE" {
			reasons = append(reasons, "DETERMINISTIC_CHECK_NOT_PASSED:"+Str(check, "check_id"))
		}
	}
	if len(Arr(b, "missing_evidence")) > 0 {
		reasons = append(reasons, "MISSING_EVIDENCE")
	}
	return reasons
}

func (s *Service) prepareDecision(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	if b["mode"] == "BOUNDED_AUTO" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "BOUNDED_AUTO awaits independent protected qualification; automatic authority is disabled")
	}
	b = copyObject(b)
	proof, _ := b["_host_invocation"].(decisionInvocationProof)
	delete(b, "_host_invocation")
	if len(Arr(b, "signals")) > 0 || b["qualification_id"] != nil {
		if e := s.checkDecisionGraph(tx, p, project, b); e != nil {
			return nil, e
		}
	}
	reasons := decisionHardFailures(b)
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
		e = s.checkDecisionGraph(tx, p, project, b)
	}
	if e == nil {
		rubric, e = s.decisionRubric(tx, project, b)
	}
	var inputs []any
	if e == nil {
		inputs, e = s.decisionPromptInputs(tx, p, project, b)
	}
	if e == nil && b["input_hash"] != Hash(b["input_refs"]) {
		e = Fail(422, "GATE_FAILED", "input hash mismatch")
	}
	if e == nil {
		_ = json.Unmarshal(Bytes(b["scope"]), &binding.Scope)
		binding.ProjectID = project
		binding.InputHash = Str(b, "input_hash")
		binding.RubricHash = Str(b["rubric_ref"].(map[string]any), "content_hash")
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
	currentInputs, e := s.decisionPromptInputs(tx, p, project, b)
	if e != nil {
		return nil, e
	}
	if Hash(currentInputs) != Hash(inputs) {
		return nil, Fail(412, "STALE_INPUT", "decision evidence changed during model invocation")
	}
	// Freeze actual response even on timeout; then record the decision transactionally.
	artifact, e := s.sealDecisionEnvelope(tx, p, project, b, envelope)
	if e != nil {
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

package domain

import (
	"context"
	"researchos.local/research-os/adapters/decision"
	"strings"
	"testing"
)

func TestW1101DecisionChain(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	body := w11Body(f, o.req)
	delete(body, "mode")
	original := copyObject(body)
	receipt, err := f.s.InvokeJev(context.Background(), f.token, f.project, body, w11Client(t, "positive"))
	if err != nil {
		t.Fatal(err)
	}
	w11Assert(t, "W11-01-DEFAULT-SHADOW", []any{"SHADOW", "DECIDED", nil}, []any{receipt["mode"], receipt["status"], receipt["qualification_id"]}, receipt)
	w11Assert(t, "W11-01-NO-CALLER-MUTATION", false, body["mode"] != nil, body)

	refs := Arr(receipt, "evidence_refs")
	var originalRef Object
	for _, candidate := range refs {
		ref := candidate.(map[string]any)
		tx, beginErr := f.db.Begin()
		if beginErr != nil {
			t.Fatal(beginErr)
		}
		value, readErr := f.s.artifactJSON(tx, f.project, ref)
		tx.Rollback()
		if readErr != nil {
			t.Fatal(readErr)
		}
		if record, ok := value.(map[string]any); ok && record["schema"] == "researchos.original-decision.v1" {
			originalRef = Object(ref)
			w11Assert(t, "W11-01-ORIGINAL-FROZEN", true,
				record["selected"] == original["selected"] && record["status"] == original["status"] && record["rationale"] == original["rationale"] &&
					record["input_hash"] == original["input_hash"] && Hash(record["scope"]) == Hash(original["scope"]) &&
					record["mode"] == "SHADOW" && Hash(record["evidence_refs"]) == Hash(original["evidence_refs"]) && record["recorded_by"] == f.owner,
				record)
		}
	}
	rawRef := Arr(receipt, "signals")[0].(map[string]any)["raw_artifact_ref"].(map[string]any)
	w11Assert(t, "W11-01-ONE-DECISION-CHAIN", true, originalRef != nil && Hash(originalRef) != Hash(rawRef) && hasRef(refs, rawRef) &&
		receipt["recorded_by"] == f.owner && receipt["receipt_hash"] == Receipt(receipt), receipt)

	proposal := f.proposal([]any{Ref(receipt, "DecisionReceipt")})
	applied := f.apply(proposal)
	w11Assert(t, "W11-01-INDEPENDENT-ADOPTION", true, applied["status"] == "APPLIED" &&
		Hash(f.state()["current_decision_refs"]) == Hash([]any{Ref(receipt, "DecisionReceipt")}), applied)

	// The review task takes this exact decision revision as an input. Its
	// AcceptanceReceipt is issued by the existing independent verifier gate.
	task := o.task("review-recorded-decision", Empty(), []any{Ref(receipt, "DecisionReceipt")})
	run := o.claim(task)
	output := o.report(run, []byte(`{"result":"verified"}`))
	acceptance := o.acceptance(run, output)
	for _, alias := range []string{"renamed-verifier", "delegated-verifier"} {
		f.switchPrincipal(alias, []string{"VERIFIER"})
		if err = f.s.RegisterExecutionIdentity(context.Background(), alias, run.executor); err != nil {
			t.Fatal(err)
		}
		status, _, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(run.task), acceptance)
		w11Assert(t, "W11-01-SELF-SIGN-"+alias, 403, status, alias)
	}
	f.switchPrincipal("w1101-independent-verifier", []string{"VERIFIER"})
	accepted := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), acceptance)
	w11Assert(t, "W11-01-INDEPENDENT-ACCEPTANCE", true, accepted["verdict"] == "PASS" &&
		Hash(accepted["input_refs"]) == Hash([]any{Ref(receipt, "DecisionReceipt")}) &&
		accepted["verifier_principal_id"] == "w1101-independent-verifier" &&
		accepted["verifier_principal_id"] != run.executor, accepted)
}

func hasRef(refs []any, target map[string]any) bool {
	for _, candidate := range refs {
		if Hash(candidate) == Hash(target) {
			return true
		}
	}
	return false
}

func TestW1101Rejections(t *testing.T) {
	t.Run("shadow-disagreement", func(t *testing.T) {
		f := contextFixture(t)
		body := w11Body(f, f.requirement())
		delete(body, "mode")
		receipt, err := f.s.InvokeJev(context.Background(), f.token, f.project, body, w11Client(t, "recommend_reject"))
		if err != nil {
			t.Fatal(err)
		}
		recorded := f.read("decisions", Str(receipt, "id"))
		w11Assert(t, "W11-01-SHADOW-DOES-NOT-OVERRIDE", true, receipt["status"] == "DECIDED" &&
			receipt["selected"] == "ACCEPT" && Arr(recorded, "signals")[0].(map[string]any)["value"] == "REJECT" &&
			strings.Contains(Str(receipt, "rationale"), "SELECTED_DIFFERS_FROM_MEASURED_ACTION"), receipt)
	})
	t.Run("high-score-hard-failure", func(t *testing.T) {
		f := contextFixture(t)
		body := w11Body(f, f.requirement())
		counter := f.artifact(Object{"failure": "hard check"}, Empty())
		body["deterministic_results"] = []any{w11FailCheck("hard check", counter)}
		body["evidence_refs"] = append(Arr(body, "evidence_refs"), Ref(counter, "Artifact"))
		receipt, err := f.s.InvokeJev(context.Background(), f.token, f.project, body, w11Client(t, "positive"))
		if err != nil {
			t.Fatal(err)
		}
		w11Assert(t, "W11-01-HIGH-SCORE-HARD-FAIL", true, receipt["status"] == "ABSTAIN" &&
			strings.Contains(Str(receipt, "rationale"), "DETERMINISTIC_CHECK_NOT_PASSED") &&
			len(Arr(receipt, "signals")) == 3, receipt)
	})
	t.Run("timeout", func(t *testing.T) {
		f := contextFixture(t)
		receipt, err := f.s.InvokeJev(context.Background(), f.token, f.project, w11Body(f, f.requirement()), w11Client(t, "timeout"))
		if err != nil {
			t.Fatal(err)
		}
		w11Assert(t, "W11-01-TIMEOUT-ABSTAINS", true, receipt["status"] == "ABSTAIN" &&
			strings.Contains(Str(receipt, "rationale"), "TIMEOUT"), receipt)
	})
	t.Run("stale-version", func(t *testing.T) {
		f := contextFixture(t)
		body := w11Body(f, f.requirement())
		body["subject_ref"].(map[string]any)["revision"] = 999
		_, err := f.s.InvokeJev(context.Background(), f.token, f.project, body, decision.Client{})
		w11Assert(t, "W11-01-STALE-VERSION-REJECTED", true,
			err != nil && strings.Contains(err.Error(), "referenced version unavailable"), errorString(err))
	})
	t.Run("cross-purpose", func(t *testing.T) {
		f := contextFixture(t)
		body := w11Body(f, f.requirement())
		dev := f.artifact(Object{"cases": []any{"dev"}}, Empty())
		hold := f.artifact(Object{"cases": []any{"holdout"}}, Empty())
		f.switchPrincipal("w1101-qualification-verifier", []string{"VERIFIER"})
		otherScope := copyObject(Object(body["scope"].(map[string]any)))
		otherScope["task_type"] = "context_trim"
		qualification := f.expect(201, "POST", f.path("/qualifications"), ID(), f.stateTag(), Object{"scope": otherScope, "dataset_artifact_ref": Ref(dev, "Artifact"), "holdout_artifact_ref": Ref(hold, "Artifact"), "thresholds_hash": Digest([]byte("frozen")), "thresholds_frozen_at": "2026-01-01T00:00:00Z", "total_case_count": 90, "holdout_case_count": 30, "label_basis": "OBJECTIVE", "measurement_mode": "FIXTURE", "jev_called": true, "expires_at": nil})
		f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
		body["qualification_id"] = qualification["id"]
		imported := f.expect(201, "POST", f.path("/decisions"), ID(), f.stateTag(), body)
		w11Assert(t, "W11-01-CROSS-PURPOSE-NO-GRANT", true, imported["status"] == "ABSTAIN" &&
			strings.Contains(Str(imported, "rationale"), "QUALIFICATION_NOT_VALID_FOR_SCOPE") && imported["qualification_id"] == nil, imported)
		body["mode"] = "BOUNDED_AUTO"
		status, _, _ := f.request("POST", f.path("/decisions"), ID(), f.stateTag(), body)
		w11Assert(t, "W11-01-NO-AUTO-WITH-OTHER-KEY", 503, status, qualification)
	})
}

package domain

import "testing"

func TestW11ManualDecisionHardGate(t *testing.T) {
	for _, scenario := range []string{"failed_check", "missing_evidence"} {
		for _, legacy := range []bool{false, true} {
			name := scenario + "_new"
			if legacy {
				name = scenario + "_legacy"
			}
			t.Run(name, func(t *testing.T) {
				f := contextFixture(t)
				body := w11Body(f, f.requirement())
				if scenario == "failed_check" {
					body["deterministic_results"] = []any{w11FailCheck("objective failure", f.artifact(Object{"failed": true}, Empty()))}
				} else {
					body["missing_evidence"] = []any{"required independent evidence"}
				}
				var receipt Object
				if legacy {
					// Import an immutable pre-fix record with the old incorrect DECIDED status.
					receipt = Merge(Object{"id": ID(), "project_id": f.project, "revision": 1, "created_at": Now(), "recorded_by": f.owner}, body)
					receipt["receipt_hash"] = Receipt(receipt)
					tx, e := f.db.Begin()
					if e != nil {
						t.Fatal(e)
					}
					if e = f.s.put(tx, "DecisionReceipt", receipt); e != nil {
						tx.Rollback()
						t.Fatal(e)
					}
					if e = tx.Commit(); e != nil {
						t.Fatal(e)
					}
				} else {
					receipt = f.expect(201, "POST", f.path("/decisions"), ID(), f.stateTag(), body)
					w11Assert(t, "C07-MANUAL-ABSTAIN-"+scenario, "ABSTAIN", receipt["status"], receipt)
				}
				value := f.artifact([]any{Ref(receipt, "DecisionReceipt")}, Empty())
				state := f.state()
				proposal := Object{"title": "manual decision hard gate", "reason": name, "base_state_revision": state["revision"], "edits": []any{Object{"target_ref": Ref(state, "ProjectState"), "field": "current_decision_refs", "proposed_value_artifact_ref": Ref(value, "Artifact"), "reason": name}}, "migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"none"}}
				code, reply, _ := f.request("POST", f.path("/change-proposals"), ID(), testTag(state), proposal)
				w11Assert(t, "C07-MANUAL-NO-ADOPT-"+name, []any{422, state["current_decision_refs"]}, []any{code, f.state()["current_decision_refs"]}, Object{"reply": reply, "receipt": receipt})
			})
		}
	}
}

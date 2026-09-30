package domain

import (
	"context"
	"testing"
)

func changeRequest(state, target, value Object, field string) Object {
	return Object{"title": "dependency regression", "reason": "verify actual semantic inputs", "base_state_revision": state["revision"], "edits": []any{Object{"target_ref": target, "field": field, "proposed_value_artifact_ref": Ref(value, "Artifact"), "reason": "explicit regression change"}}, "migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"independently verified reversal"}}
}
func decisionRequest(receipt Object) Object {
	b := copyObject(receipt)
	for _, k := range []string{"id", "revision", "project_id", "receipt_hash", "created_at", "recorded_by"} {
		delete(b, k)
	}
	return b
}
func acceptanceRequest(f *fixture, proposal Object) Object {
	f.t.Helper()
	frozen, e := f.s.ChangeContractHash(context.Background(), f.project, Str(proposal, "id"))
	if e != nil {
		f.t.Fatal(e)
	}
	return Object{"subject_ref": Ref(proposal, "ChangeProposal"), "run_id": nil, "contract_hash": frozen, "input_refs": []any{Ref(proposal, "ChangeProposal")}, "artifact_refs": Empty(), "checks": []any{Object{"check_id": "client-not-authoritative", "status": "NOT_RUN", "evidence_refs": Empty(), "command_key": nil, "actual": "server must recompute", "exit_code": nil, "started_at": nil, "finished_at": nil}}, "verdict": "PASS", "executor_principal_ids": Empty(), "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": 1, "measurement_mode": "FIXTURE", "reason": "independent actual candidate verification"}
}
func TestW04DecisionDependencies(t *testing.T) {
	for _, field := range []string{"rubric_ref", "evidence_refs", "subject_ref"} {
		t.Run(field, func(t *testing.T) {
			f := contextFixture(t)
			req := f.requirement()
			rubric := f.artifact(Object{"rubric": "stable"}, Empty())
			d1 := f.decision(req, rubric, nil, "A")
			f.apply(f.proposal([]any{Ref(d1, "DecisionReceipt")}))
			staleArtifact := f.artifact(Object{"rubric": "old source"}, []any{Ref(req, "Requirement")})
			value := f.artifact("new requirement text", Empty())
			state := f.state()
			change := f.expect(201, "POST", f.path("/change-proposals"), ID(), testTag(state), changeRequest(state, Ref(req, "Requirement"), value, "text"))
			f.apply(change)
			currentReq := f.read("requirements", Str(req, "id"))
			staleNow := f.read("artifacts", Str(staleArtifact, "id"))
			if staleNow["validity"] != "STALE" {
				t.Fatal("fixture did not invalidate dependency")
			}
			b := decisionRequest(d1)
			b["supersedes_id"] = d1["id"]
			b["input_refs"] = []any{Ref(currentReq, "Requirement")}
			b["input_hash"] = Hash(b["input_refs"])
			b["subject_ref"] = Ref(currentReq, "Requirement")
			switch field {
			case "rubric_ref":
				b[field] = Ref(staleArtifact, "Artifact")
			case "evidence_refs":
				b[field] = []any{Ref(staleArtifact, "Artifact")}
			case "subject_ref":
				b[field] = Ref(req, "Requirement")
			}
			candidate := f.expect(201, "POST", f.path("/decisions"), ID(), f.stateTag(), b)
			value = f.artifact([]any{Ref(candidate, "DecisionReceipt")}, Empty())
			state = f.state()
			status, response, _ := f.request("POST", f.path("/change-proposals"), ID(), testTag(state), changeRequest(state, Ref(state, "ProjectState"), value, "current_decision_refs"))
			evidence := Object{"candidate": candidate, "stale_dependency": staleNow, "proposal_response": response, "proposal_status": status}
			if status == 201 {
				f.apply(response)
				task := f.task(currentReq, []any{Ref(candidate, "DecisionReceipt")}, "bad-dependency-task")
				bundle := f.bundle(task)
				_, err := f.s.GetTaskContext(context.Background(), f.token, f.project, Str(task, "id"))
				evidence["invalid_candidate_promoted"] = true
				evidence["invalid_context_allowed"] = err == nil
				evidence["bundle"] = bundle
			}
			assertion(t, "W04-G02-DEPENDENCY-"+field, 412, status, evidence)
		})
	}
}
func TestW04CandidateIndependence(t *testing.T) {
	f := contextFixture(t)
	req := f.requirement()
	rubric := f.artifact(Object{"rubric": "independence"}, Empty())
	d1 := f.decision(req, rubric, nil, "A")
	f.apply(f.proposal([]any{Ref(d1, "DecisionReceipt")}))
	candidateAuthor := "candidate-author-verifier"
	f.switchPrincipal(candidateAuthor, []string{"PLANNER", "VERIFIER"})
	d2 := f.decision(req, rubric, d1["id"], "B")
	f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
	proposal := f.proposal([]any{Ref(d2, "DecisionReceipt")})
	request := acceptanceRequest(f, proposal)
	f.switchPrincipal(candidateAuthor, []string{"PLANNER", "VERIFIER"})
	status, response, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(proposal), request)
	assertion(t, "W04-G02-CANDIDATE-SELF", 403, status, Object{"candidate_author": d2["recorded_by"], "proposal": proposal, "response": response, "client_executor_list": request["executor_principal_ids"]})
	f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
	f.apply(proposal)
	d3 := f.decision(req, rubric, d2["id"], "A")
	next := f.proposal([]any{Ref(d3, "DecisionReceipt")})
	request = acceptanceRequest(f, next)
	f.switchPrincipal(candidateAuthor, []string{"PLANNER", "VERIFIER"})
	status, response, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(next), request)
	assertion(t, "W04-G02-HISTORY-NOT-CANDIDATE", 201, status, Object{"prior_author": d2["recorded_by"], "current_candidate_author": d3["recorded_by"], "acceptance": response})
}

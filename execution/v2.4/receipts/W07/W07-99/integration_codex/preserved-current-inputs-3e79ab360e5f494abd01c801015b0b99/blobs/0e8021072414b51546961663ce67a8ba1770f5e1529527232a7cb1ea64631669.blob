package domain

import (
	"context"
	"encoding/json"
	"net/http"
	"researchos.local/research-os/adapters/decision"
	"testing"
)

// A changed scoring rubric cannot turn an unchanged objective fixture result
// into improvement or automatic decision authority.
func TestW11C20RubricOnly(t *testing.T) {
	f := contextFixture(t)
	req := f.requirement()
	objective := f.artifact(Object{"fixture_input": "same question", "objective_outcome": "unchanged"}, Empty())
	oldBody := w11Body(f, req)
	oldBody["input_refs"] = append(Arr(oldBody, "input_refs"), Ref(objective, "Artifact"))
	oldBody["input_hash"] = Hash(oldBody["input_refs"])
	oldBody["evidence_refs"] = append(Arr(oldBody, "evidence_refs"), Ref(objective, "Artifact"))
	before := f.state()["current_decision_refs"]

	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	oldRubricRaw, err := f.s.artifactJSON(tx, f.project, oldBody["rubric_ref"].(map[string]any))
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	var revised DecisionRubric
	if err = json.Unmarshal(Bytes(oldRubricRaw), &revised); err != nil {
		t.Fatal(err)
	}
	revised.Revision = "2"
	quality := revised.Questions["quality"]
	quality.Instructions = "Rate the same evidence with a revised scale"
	quality.Criteria = []string{"insufficient", "adequate", "complete"}
	revised.Questions["quality"] = quality
	newRubric := f.artifact(revised, Empty())
	newBody := copyObject(oldBody)
	newBody["rubric_ref"] = Ref(newRubric, "Artifact")
	newBody["evidence_refs"] = []any{Ref(newRubric, "Artifact"), Ref(objective, "Artifact")}
	newScope := copyObject(Object(oldBody["scope"].(map[string]any)))
	newScope["rubric_revision"] = "2"
	newBody["scope"] = newScope

	var newResponse decision.Response
	if err = json.Unmarshal([]byte(w11Response()), &newResponse); err != nil {
		t.Fatal(err)
	}
	newQuality := newResponse.Answers["quality"]
	score := 2.0
	newQuality.Score = &score
	newQuality.Probabilities = map[string]float64{"0": 0, "1": 0, "2": 1}
	newQuality.Legend = map[string]string{"0": "insufficient", "1": "adequate", "2": "complete"}
	newResponse.Answers["quality"] = newQuality

	invoke := func(body Object, raw []byte) (Object, decision.Envelope, decision.Response) {
		t.Helper()
		called := false
		server, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/__researchos_fixture_readiness__" {
				w.WriteHeader(http.StatusNotFound)
				return
			}
			called = true
			w.Write(raw)
		}))
		defer server.Close()
		receipt, callErr := f.s.InvokeJev(context.Background(), f.token, f.project, body, decision.Client{URL: server.URL, Fixture: true})
		if callErr != nil || !called {
			t.Fatalf("authenticated fixture Jev invocation failed: %v; called=%v", callErr, called)
		}
		ref := Arr(receipt, "signals")[0].(map[string]any)["raw_artifact_ref"].(map[string]any)
		readTx, beginErr := f.db.Begin()
		if beginErr != nil {
			t.Fatal(beginErr)
		}
		value, readErr := f.s.artifactJSON(readTx, f.project, ref)
		readTx.Rollback()
		if readErr != nil {
			t.Fatal(readErr)
		}
		var envelope decision.Envelope
		var response decision.Response
		if json.Unmarshal(Bytes(value), &envelope) != nil || json.Unmarshal(envelope.Response, &response) != nil {
			t.Fatal("sealed Jev raw envelope invalid")
		}
		return receipt, envelope, response
	}
	oldDecision, oldEnvelope, oldResult := invoke(oldBody, []byte(w11Response()))
	newDecision, newEnvelope, newResult := invoke(newBody, Bytes(newResponse))
	oldInputs := oldEnvelope.Request.State.(map[string]any)["inputs"]
	newInputs := newEnvelope.Request.State.(map[string]any)["inputs"]
	objectivePrompt := func(raw any) []any {
		var selected []any
		for _, value := range raw.([]any) {
			entry := value.(map[string]any)
			ref := entry["ref"].(map[string]any)
			if ref["id"] == req["id"] || ref["id"] == objective["id"] {
				selected = append(selected, entry)
			}
		}
		return selected
	}
	oldObjective, newObjective := objectivePrompt(oldInputs), objectivePrompt(newInputs)
	w11Assert(t, "C20-JEV-SAME-OBJECTIVE", true,
		Hash(oldBody["input_refs"]) == Hash(newBody["input_refs"]) && oldEnvelope.Binding.InputHash == newEnvelope.Binding.InputHash &&
			len(oldObjective) == 2 && Hash(oldObjective) == Hash(newObjective) && Hash(oldInputs) != Hash(newInputs) &&
			oldDecision["selected"] == newDecision["selected"] && oldDecision["selected"] == "ACCEPT" &&
			oldResult.Answers["action"].Choice != nil && newResult.Answers["action"].Choice != nil &&
			*oldResult.Answers["action"].Choice == *newResult.Answers["action"].Choice,
		Object{"objective_artifact_sha256": objective["content_hash"], "input_hash": oldEnvelope.Binding.InputHash})
	w11Assert(t, "C20-JEV-RUBRIC-SCORE-UP", true,
		oldEnvelope.Binding.RubricHash != newEnvelope.Binding.RubricHash &&
			oldResult.Answers["quality"].Score != nil && newResult.Answers["quality"].Score != nil &&
			*oldResult.Answers["quality"].Score == 1 && *newResult.Answers["quality"].Score == 2 &&
			oldDecision["status"] == "DECIDED" && newDecision["status"] == "DECIDED",
		Object{"old_score": oldResult.Answers["quality"].Score, "new_score": newResult.Answers["quality"].Score,
			"old_rubric_hash": oldEnvelope.Binding.RubricHash, "new_rubric_hash": newEnvelope.Binding.RubricHash})
	auto := copyObject(newBody)
	auto["mode"] = "BOUNDED_AUTO"
	code, _, _ := f.request("POST", f.path("/decisions"), ID(), f.stateTag(), auto)
	w11Assert(t, "C20-JEV-NO-AUTO", true,
		code == 503 && oldDecision["mode"] == "ADVISORY" && newDecision["mode"] == "ADVISORY" &&
			oldDecision["qualification_id"] == nil && newDecision["qualification_id"] == nil &&
			Hash(before) == Hash(f.state()["current_decision_refs"]),
		Object{"automatic_http_status": code, "measurement_mode": "FIXTURE", "real_world_gain": "NOT_ESTABLISHED"})
}

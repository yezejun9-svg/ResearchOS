package domain

import (
	"context"
	"encoding/json"
	"net/http"
	"researchos.local/research-os/adapters/decision"
	"strings"
	"testing"
)

func TestW11PromptBoundaries(t *testing.T) {
	for _, scenario := range []string{"text-body", "json-body", "binary", "oversized", "protected-input", "protected-rubric-lineage", "protected-evidence", "rubric-race"} {
		t.Run(scenario, func(t *testing.T) {
			f := contextFixture(t)
			body := w11Body(f, f.requirement())
			text := "current sealed evidence unique payload"
			media := "text/plain; charset=utf-8"
			if scenario == "json-body" {
				media = "application/json"
				text = `{"value":"current sealed JSON evidence"}`
			}
			if scenario == "binary" {
				media = "application/octet-stream"
			}
			if scenario == "oversized" {
				text = strings.Repeat("x", decisionArtifactLimit+1)
			}
			u := f.expect(201, "POST", f.path("/content"), ID(), "", []byte(text))
			artifact := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": media, "byte_size": len(text), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
			body["input_refs"] = append(Arr(body, "input_refs"), Ref(artifact, "Artifact"))
			body["input_hash"] = Hash(body["input_refs"])
			if strings.HasPrefix(scenario, "protected-") {
				// Classification-only metadata; no protected bytes or holdout is created.
				private := Merge(Base(f.project), Object{"run_id": nil, "kind": "TEST_RESULT", "evidence_kind": "SIMULATED", "validity": "CURRENT", "measurement_mode": "FIXTURE", "content_hash": Digest(nil), "storage_key": "unbound-w11-protected-metadata", "media_type": "application/json", "byte_size": 0, "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "sealed_at": Now(), "access_class": "VERIFIER_ONLY"})
				tx, err := f.db.Begin()
				if err != nil {
					t.Fatal(err)
				}
				defer tx.Rollback()
				if err = f.s.put(tx, "Artifact", private); err != nil {
					t.Fatal(err)
				}
				body["input_refs"] = []any{body["subject_ref"]}
				if scenario == "protected-input" {
					body["input_refs"] = append(Arr(body, "input_refs"), Ref(private, "Artifact"))
				}
				if scenario == "protected-evidence" {
					body["evidence_refs"] = append(Arr(body, "evidence_refs"), Ref(private, "Artifact"))
				}
				if scenario == "protected-rubric-lineage" {
					hiddenRubric := Merge(Base(f.project), Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "SIMULATED", "validity": "CURRENT", "measurement_mode": "FIXTURE", "content_hash": Digest([]byte("synthetic-restricted-rubric-metadata")), "storage_key": "unbound-w11-rubric-metadata", "media_type": "application/json", "byte_size": 0, "input_refs": []any{Ref(private, "Artifact")}, "source_refs": Empty(), "produced_by": f.owner, "sealed_at": Now(), "access_class": "PROJECT"})
					if err = f.s.put(tx, "Artifact", hiddenRubric); err != nil {
						t.Fatal(err)
					}
					body["rubric_ref"] = Ref(hiddenRubric, "Artifact")
				}
				body["input_hash"] = Hash(body["input_refs"])
				if err = tx.Commit(); err != nil {
					t.Fatal(err)
				}
			}
			called, bodySent := false, false
			server, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/__researchos_fixture_readiness__" {
					w.WriteHeader(http.StatusNotFound)
					return
				}
				called = true
				var request decision.Request
				if e := json.NewDecoder(r.Body).Decode(&request); e != nil {
					t.Error(e)
				}
				for _, v := range request.State.(map[string]any)["inputs"].([]any) {
					entry := v.(map[string]any)
					if entry["body"] == text && entry["body_sha256"] == artifact["content_hash"] {
						bodySent = true
					}
				}
				if scenario == "rubric-race" {
					ref := body["rubric_ref"].(map[string]any)
					if _, e := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.validity','STALE') WHERE project=? AND kind='Artifact' AND id=?", f.project, ref["id"]); e != nil {
						t.Error(e)
					}
				}
				w.Write([]byte(w11Response()))
			}))
			defer server.Close()
			receipt, e := f.s.InvokeJev(context.Background(), f.token, f.project, body, decision.Client{URL: server.URL, Fixture: true})
			wantSuccess := scenario == "text-body" || scenario == "json-body"
			wantCall := wantSuccess || scenario == "rubric-race"
			w11Assert(t, "JEV-PROMPT-"+scenario, []any{wantSuccess, wantCall, wantCall}, []any{e == nil, called, bodySent}, Object{"receipt": receipt, "error": errorString(e)})
		})
	}
}
func errorString(e error) any {
	if e == nil {
		return nil
	}
	return e.Error()
}

func TestW11RawReuse(t *testing.T) {
	f := contextFixture(t)
	body := w11Body(f, f.requirement())
	extra := f.artifact(Object{"extra": "different provenance"}, Empty())
	env := decision.Envelope{Version: 1, MeasurementMode: "FIXTURE", Response: []byte(w11Response())}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	p, e := authenticate(tx, f.token)
	if e != nil {
		t.Fatal(e)
	}
	a, e := f.s.sealDecisionEnvelope(tx, p, f.project, body, env)
	if e != nil {
		t.Fatal(e)
	}
	b, e := f.s.sealDecisionEnvelope(tx, p, f.project, body, env)
	if e != nil {
		t.Fatal(e)
	}
	var count int
	tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact' AND content_hash=?", f.project, a["content_hash"]).Scan(&count)
	w11Assert(t, "JEV-RAW-CANONICAL-REUSE", []any{true, 1}, []any{a["id"] == b["id"], count}, Object{"first": a, "second": b})
	altered := copyObject(body)
	altered["evidence_refs"] = []any{Ref(extra, "Artifact")}
	_, e = f.s.sealDecisionEnvelope(tx, p, f.project, altered, env)
	w11Assert(t, "JEV-RAW-REUSE-PROVENANCE", true, e != nil, errorString(e))
	w11Assert(t, "QUAL-RESULT-TRUSTED-ONLY", true, implemented["recordQualificationResult"], "result admission requires an independent protected service proof")
}

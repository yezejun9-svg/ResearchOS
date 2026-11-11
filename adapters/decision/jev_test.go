package decision

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func fixtureEnvelope() Envelope {
	r := Request{Model: "jev-1.13.0", State: map[string]any{"evidence": "fixture"}, Questions: map[string]Question{"action": {Type: "choice", Instructions: "choose", Criteria: map[string]string{"ACCEPT": "valid", "REJECT": "invalid"}}, "quality": {Type: "score", Instructions: "score", Criteria: []string{"bad", "good"}}, "evidence": {Type: "noul", Instructions: "enough evidence"}}}
	raw := []byte(`{"model":"jev-1.13.0","answers":{"action":{"type":"choice","choice":"ACCEPT","confidence":1,"probabilities":{"ACCEPT":1,"REJECT":0}},"quality":{"type":"score","score":1,"confidence":1,"probabilities":{"0":0,"1":1},"legend":{"0":"bad","1":"good"}},"evidence":{"type":"noul","noul":1}},"usage":{"input_tokens":12,"output_tokens":3}}`)
	return Envelope{Version: 1, Binding: Binding{ProjectID: "fixture-project", InputHash: Digest([]byte("inputs")), RubricHash: Digest([]byte("rubric")), Scope: Scope{TaskType: "evidence-validity", Language: "zh", Provider: "typesafe", ModelRevision: r.Model, RubricRevision: "1"}}, Request: r, RequestHash: Digest(Encode(r)), Response: raw, ResponseHash: Digest(raw), HTTPStatus: 200, MeasurementMode: "FIXTURE"}
}
func assert(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if string(Encode(want)) != string(Encode(got)) {
		status = "FAIL"
	}
	fmt.Println("W11_ASSERTION " + string(Encode(map[string]any{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": "strict typed adapter fixture"})))
	if status != "PASS" {
		t.Fatalf("%s: want %v got %v", id, want, got)
	}
}
func TestW11TypedAdapter(t *testing.T) {
	env := fixtureEnvelope()
	r := Evaluate(env, .8)
	assert(t, "JEV-TYPED-POSITIVE", []any{false, "ACCEPT", 3}, []any{r.Abstained, r.Selected, len(r.Signals)})
	// Official confidence summarizes distribution shape; it is not the chosen probability.
	actual := fixtureEnvelope()
	actual.Response = []byte(strings.Replace(string(actual.Response), `"confidence":1,"probabilities":{"ACCEPT":1,"REJECT":0}`, `"confidence":0.89,"probabilities":{"ACCEPT":0.94,"REJECT":0.06}`, 1))
	actual.ResponseHash = Digest(actual.Response)
	parsed := Evaluate(actual, .8)
	assert(t, "JEV-CONFIDENCE-DISTINCT-FROM-PROBABILITY", []any{false, "ACCEPT"}, []any{parsed.Abstained, parsed.Selected})
	cases := []struct{ id, from, to string }{
		{"UNKNOWN-ACTION", `"choice":"ACCEPT"`, `"choice":"DELETE_PROJECT"`},
		{"NONMAXIMUM-CHOICE", `"ACCEPT":1,"REJECT":0`, `"ACCEPT":0.1,"REJECT":0.9`},
		{"MISSING-ANSWER", `,"evidence":{"type":"noul","noul":1}`, ``},
		{"MODEL-DRIFT", `"model":"jev-1.13.0"`, `"model":"jev-next"`},
		{"DUPLICATE-JSON", `"model":"jev-1.13.0"`, `"model":"jev-1.13.0","model":"jev-1.13.0"`},
		{"OUT-OF-RANGE", `"confidence":1`, `"confidence":2`},
		{"NONFINITE", `"confidence":1`, `"confidence":1e999`},
		{"MISSING-CONFIDENCE", `"confidence":1,`, ``},
		{"LOW-CONFIDENCE", `"confidence":1,"probabilities":{"ACCEPT":1,"REJECT":0}`, `"confidence":0.55,"probabilities":{"ACCEPT":0.55,"REJECT":0.45}`},
		{"LOW-SCORE", `"score":1,"confidence":1,"probabilities":{"0":0,"1":1}`, `"score":0,"confidence":1,"probabilities":{"0":1,"1":0}`},
		{"NOUL-FALSE", `"noul":1`, `"noul":0`},
		{"BAD-SUM", `"REJECT":0`, `"REJECT":0.2`},
		{"SCORE-MEAN", `"score":1`, `"score":0.5`},
		{"LEGEND-DRIFT", `"1":"good"`, `"1":"unrelated"`},
		{"USAGE-MISSING", `,"usage":{"input_tokens":12,"output_tokens":3}`, ``},
		{"UNKNOWN-FIELD", `"output_tokens":3`, `"output_tokens":3,"accepted":true`},
	}
	for _, c := range cases {
		t.Run(c.id, func(t *testing.T) {
			e := fixtureEnvelope()
			e.Response = []byte(strings.Replace(string(e.Response), c.from, c.to, 1))
			if string(e.Response) == string(env.Response) {
				t.Fatal("mutation did not apply")
			}
			e.ResponseHash = Digest(e.Response)
			assert(t, "JEV-"+c.id, true, Evaluate(e, .8).Abstained)
		})
	}
	e := fixtureEnvelope()
	e.ResponseHash = Digest([]byte("wrong"))
	assert(t, "JEV-RAW-HASH", true, Evaluate(e, .8).Abstained)
	e = fixtureEnvelope()
	e.Request.Model = "other"
	assert(t, "JEV-REQUEST-BINDING", true, Evaluate(e, .8).Abstained)
}
func TestW11Transport(t *testing.T) {
	base := fixtureEnvelope()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/timeout" {
			select {
			case <-r.Context().Done():
			case <-time.After(time.Second):
			}
			return
		}
		if r.Header.Get("Authorization") != "" {
			t.Error("fixture leaked credential")
		}
		if r.URL.Path == "/redirect" {
			http.Redirect(w, r, "https://example.invalid/", 302)
			return
		}
		w.Write(base.Response)
	}))
	defer server.Close()
	// Positive transport cases allow native Windows loopback startup latency;
	// the explicit cancellation case below retains its 10 ms deadline.
	client := Client{URL: server.URL, Fixture: true, Token: "do-not-send", Timeout: 5 * time.Second}
	e, err := client.Call(context.Background(), base.Binding, base.Request)
	assert(t, "JEV-HTTP-FIXTURE", []any{true, false, "FIXTURE", false}, []any{err == nil, e.JevCalled, e.MeasurementMode, Evaluate(e, .8).Abstained})
	client.URL = server.URL + "/timeout"
	client.Timeout = 10 * time.Millisecond
	e, err = client.Call(context.Background(), base.Binding, base.Request)
	assert(t, "JEV-TIMEOUT", []any{true, true, "TIMEOUT_OR_CANCELLED"}, []any{err == nil, Evaluate(e, .8).Abstained, e.TransportError})
	client.URL = server.URL + "/redirect"
	client.Timeout = 5 * time.Second
	e, err = client.Call(context.Background(), base.Binding, base.Request)
	assert(t, "JEV-NO-REDIRECT", []any{true, 302, true}, []any{err == nil, e.HTTPStatus, Evaluate(e, .8).Abstained})
	client.Fixture = false
	_, err = client.Call(context.Background(), base.Binding, base.Request)
	assert(t, "JEV-ENDPOINT-BOUNDARY", true, err != nil)
}

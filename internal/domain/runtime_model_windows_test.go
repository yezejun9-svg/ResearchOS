//go:build windows

package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestRuntimeMuHostProfileIsNotPromptText(t *testing.T) {
	marker := "host-control-inventory-not-user-context"
	c, route, r, calls := muBrokerFixtureProgram(t, func(w http.ResponseWriter, req *http.Request) {
		raw, err := io.ReadAll(req.Body)
		if err != nil || len(raw) > 48*1024 || strings.Contains(string(raw), marker) {
			t.Errorf("host policy leaked into bounded model prompt: len=%d err=%v", len(raw), err)
		}
		w.Header().Set("Content-Type", "text/event-stream")
		fmt.Fprint(w, "data: {\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"qualified\"},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
	}, func(_ Object, profile Object) {
		profile["timeout_seconds"] = 900
		profile["tool_policy"] = Object{"max_calls": 1, "read_paths": []any{strings.Repeat(marker+"/", 1800)}, "write_paths": Empty()}
	})
	qualifyNativeCoordinator(t, c, route, r)
	if calls.Load() != 1 || r.registration["status"] != "AVAILABLE" {
		t.Fatalf("bounded host-profile qualification failed: calls=%d", calls.Load())
	}
}

func muBrokerFixture(t *testing.T, respond http.HandlerFunc) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture, *atomic.Int32) {
	return muBrokerFixtureProgram(t, respond, nil)
}

func muBrokerFixtureProgram(t *testing.T, respond http.HandlerFunc, configure func(Object, Object), expectedBearer ...string) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture, *atomic.Int32) {
	t.Helper()
	bareAuthorization := "Bearer host-only-model-fixture"
	if len(expectedBearer) > 0 {
		bareAuthorization = expectedBearer[0]
	}
	bundle := os.Getenv("RESEARCHOS_MU_BUNDLE")
	if bundle == "" {
		t.Skip("requires explicitly built immutable Mu bundle")
	}
	node, e := exec.LookPath("node")
	if e != nil {
		t.Fatal(e)
	}
	node, e = filepath.EvalSymlinks(node)
	if e != nil {
		t.Fatal(e)
	}
	binary, e := os.ReadFile(node)
	if e != nil {
		t.Fatal(e)
	}
	bundleRaw, e := os.ReadFile(bundle)
	if e != nil {
		t.Fatal(e)
	}
	var calls atomic.Int32
	server, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(404)
			return
		}
		calls.Add(1)
		if r.Header.Get("Authorization") != bareAuthorization {
			w.WriteHeader(403)
			return
		}
		var body Object
		if json.NewDecoder(r.Body).Decode(&body) != nil || body["model"] != "fixture-model" || body["payload"] != nil {
			w.WriteHeader(400)
			return
		}
		if respond != nil {
			r.Body = io.NopCloser(bytes.NewReader(Bytes(body)))
			respond(w, r)
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for _, delta := range []Object{{"role": "assistant", "content": "qualified fixture response"}, {}} {
			finish := any(nil)
			if len(delta) == 0 {
				finish = "stop"
			}
			chunk := Object{"id": "fixture-response", "object": "chat.completion.chunk", "created": 1, "model": "fixture-model", "choices": []any{Object{"index": 0, "delta": delta, "finish_reason": finish}}}
			fmt.Fprintf(w, "data: %s\n\n", Bytes(chunk))
		}
		fmt.Fprint(w, "data: [DONE]\n\n")
	}))
	t.Cleanup(server.Close)
	config := modelFixtureConfig(server.URL + "/v1/chat/completions")
	c, route, r := coordinatorFixtureProgram(t, false, false, func(profile Object) (string, string) {
		profile["backend"], profile["model"], profile["model_config"] = runtimeMuBackend, config["model"], config
		profile["build_hash"], profile["bundle_hash"] = Digest(binary), Digest(bundleRaw)
		profile["argv"] = []any{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}
		profile["effect_routes"] = []any{Object{"id": config["route"], "capability": "MODEL", "credential_revision": "test-v1", "upper_bound": dollars("1")}}
		profile["model_qualification"] = Object{"route": config["route"], "model_config_hash": Hash(config), "max_calls": 1}
		profile["timeout_seconds"] = 60
		if configure != nil {
			configure(config, profile)
		}
		profile["model_qualification"].(map[string]any)["model_config_hash"] = Hash(config)
		return node, bundle
	})
	c.config.Providers = []RuntimeProviderRoute{{ID: Str(config, "route"), ProjectID: r.f.project, RuntimeID: route.RuntimeID, Purpose: "runtime_qualification", Capability: "MODEL", CredentialRevision: "test-v1", Endpoint: Str(config, "endpoint"), BearerToken: "host-only-model-fixture", UpperBound: dollars("1"), MeasurementMode: "FIXTURE", ModelConfig: config}}
	return c, route, r, &calls
}

func TestRuntimeMuQualificationBroker(t *testing.T) {
	c, route, r, calls := muBrokerFixture(t, nil)
	var e error
	if e = c.RunAdmitted(context.Background(), route, r.run, r.lease); e != nil {
		t.Fatal(e)
	}
	if calls.Load() != 1 {
		var locator string
		r.f.db.QueryRow("SELECT journal_locator FROM runtime_dispatches WHERE run=?", r.run["id"]).Scan(&locator)
		stderr, _ := os.ReadFile(filepath.Join(c.config.DataRoot, "runtime-dispatches", locator, "stderr.raw"))
		stdout, _ := os.ReadFile(filepath.Join(c.config.DataRoot, "runtime-dispatches", locator, "stdout.raw"))
		t.Fatalf("model calls = %d stderr=%s stdout=%s", calls.Load(), stderr, stdout)
	}
	var state string
	if e = r.f.db.QueryRow("SELECT json_extract(body,'$.state') FROM resource_effects WHERE run=? ORDER BY sequence DESC LIMIT 1", r.run["id"]).Scan(&state); e != nil || state != "CONFIRMED" {
		t.Fatalf("effect %s %v", state, e)
	}
	var charged int
	if e = r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.cost_basis')='ACTUAL'", r.run["id"]).Scan(&charged); e != nil || charged != 0 {
		t.Fatalf("unknown model cost converted to actual: %d %v", charged, e)
	}
	updated := r.f.read("tasks", Str(r.task, "id"))
	if updated["status"] != "EXECUTION_REPORTED" {
		t.Fatalf("task not reported: %s", Bytes(updated))
	}
	t.Log("MU_QUALIFICATION_BROKER real_SDK=true no_network_AppContainer=true provider=loopback_FIXTURE model_calls=1 model_effect=CONFIRMED actual_cost=null task=EXECUTION_REPORTED independent_acceptance=NOT_RUN")
}

func TestRuntimeMuLocalModelDoesNotForwardSDKOrBrokerHeaders(t *testing.T) {
	t.Setenv("OPENAI_API_KEY", "synthetic-never-forward")
	var expectedHost string
	c, route, r, calls := muBrokerFixtureProgram(t, func(w http.ResponseWriter, req *http.Request) {
		for _, name := range []string{"Authorization", "Cookie", "Proxy-Authorization", "X-Api-Key", "Idempotency-Key"} {
			if req.Header.Get(name) != "" {
				t.Errorf("local provider received %s", name)
			}
		}
		if req.URL.Path != "/v1/chat/completions" || req.Host != expectedHost || req.URL.RawQuery != "" {
			t.Errorf("local provider request escaped frozen endpoint: %s", req.URL)
		}
		w.Header().Set("Content-Type", "text/event-stream")
		fmt.Fprint(w, "data: {\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"qualified\"},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
	}, func(_ Object, profile Object) {
		profile["credential_revision"] = "none"
		profile["effect_routes"] = []any{Object{"id": "model-fixture", "capability": "MODEL", "credential_revision": "none", "upper_bound": dollars("1")}}
	}, "")
	c.config.Providers[0].BearerToken = ""
	c.config.Providers[0].CredentialRevision = "none"
	u, err := url.Parse(c.config.Providers[0].Endpoint)
	if err != nil || u.Scheme != "http" || !clientConfigurationLoopbackModelEndpoint(u.String()) {
		t.Fatal("fixture endpoint must be strict local HTTP")
	}
	expectedHost = u.Host
	qualifyNativeCoordinator(t, c, route, r)
	if calls.Load() != 1 {
		t.Fatalf("expected one credential-free local model request, got %d", calls.Load())
	}
}

func TestRuntimeMuUnknownNeverRetries(t *testing.T) {
	c, route, r, calls := muBrokerFixture(t, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		fmt.Fprint(w, "data: {\"content\":\"not a terminator: [DONE]\"}\n\n")
	})
	if e := c.RunAdmitted(context.Background(), route, r.run, r.lease); e == nil {
		t.Fatal("incomplete provider response was accepted")
	}
	if calls.Load() != 1 {
		t.Fatalf("provider retried %d times", calls.Load())
	}
	var state string
	if e := r.f.db.QueryRow("SELECT json_extract(body,'$.state') FROM resource_effects WHERE run=? ORDER BY sequence DESC LIMIT 1", r.run["id"]).Scan(&state); e != nil || state != "UNKNOWN" {
		t.Fatalf("effect=%s %v", state, e)
	}
	if e := c.RunAdmitted(context.Background(), route, r.run, r.lease); e == nil {
		t.Fatal("unknown dispatch relaunched")
	}
	if calls.Load() != 1 {
		t.Fatal("unknown provider operation repeated")
	}
	t.Log("MU_UNKNOWN transport_incomplete=true effect=UNKNOWN provider_calls=1 relaunch=DENIED")
}

func TestRuntimeMuCancelStopsTransport(t *testing.T) {
	runtimeMuCancelStopsTransport(t, false)
}

func TestRuntimeMuTypedCancelStopsTransport(t *testing.T) {
	runtimeMuCancelStopsTransport(t, true)
}

func runtimeMuCancelStopsTransport(t *testing.T, typed bool) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	entered := make(chan struct{})
	stopped := make(chan struct{})
	c, route, r, calls := muBrokerFixture(t, func(w http.ResponseWriter, r *http.Request) { close(entered); <-r.Context().Done(); close(stopped) })
	var sid string
	if typed {
		sid = mixedSessionEvents(t, r.f, 0)
		if _, err := r.f.db.Exec("UPDATE client_sessions SET run_id=? WHERE id=?", r.run["id"], sid); err != nil {
			t.Fatal(err)
		}
	}
	done := make(chan error, 1)
	go func() { done <- c.RunAdmitted(ctx, route, r.run, r.lease) }()
	select {
	case <-entered:
	case <-time.After(20 * time.Second):
		t.Fatal("model request did not start")
	}
	if typed {
		svc := &ClientService{Doc: clientHistoryDoc(t), Domain: r.f.s, Host: ClientHostInfo{CoreBuildID: "mixed-fixture", LeaseTTL: time.Minute}}
		env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("mixed-client"), ProjectID: &r.f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("session.control"), Payload: Bytes(Object{"action": "CANCEL", "target_id": r.run["id"], "reason": "user cancelled"})}
		sourceTx(t, r.f.db, func(tx *sql.Tx) error {
			res, _, err := svc.Execute(context.Background(), tx, handlerDecode(t, env), r.f.owner)
			if err != nil {
				return err
			}
			if deref(res.Status) != "ACKNOWLEDGED" {
				t.Fatalf("typed cancel rejected: %s", Bytes(res))
			}
			return nil
		})
	} else {
		cancel()
	}
	select {
	case <-stopped:
	case <-time.After(3 * time.Second):
		t.Fatal("inflight model request survived cancellation")
	}
	select {
	case e := <-done:
		if e == nil {
			t.Fatal("cancelled turn was reported successful")
		}
	case <-time.After(10 * time.Second):
		t.Fatal("cancelled worker did not stop")
	}
	if calls.Load() != 1 {
		t.Fatal("cancelled model request retried")
	}
	t.Log("MU_CANCEL inflight_HTTP_stopped=true sandbox_stopped=true provider_calls=1")
}

func TestRuntimeMuMissingCredentialNotApplied(t *testing.T) {
	c, route, r, calls := muBrokerFixture(t, nil)
	c.config.Providers[0].CredentialRef = "missing-fixture-reference"
	if e := c.RunAdmitted(context.Background(), route, r.run, r.lease); e != nil {
		t.Fatal(e)
	}
	if run := r.f.read("runs", Str(r.run, "id")); run["status"] != "FAILED" || run["children_stopped"] != true || run["queue_empty"] != true {
		t.Fatalf("known refusal did not settle as FAILED: %s", Bytes(run))
	}
	if calls.Load() != 0 {
		t.Fatal("request sent without protected credential")
	}
	var state string
	if e := r.f.db.QueryRow("SELECT json_extract(body,'$.state') FROM resource_effects WHERE run=? ORDER BY sequence DESC LIMIT 1", r.run["id"]).Scan(&state); e != nil || state != "NOT_APPLIED" {
		t.Fatalf("known absent operation became %s: %v", state, e)
	}
	t.Log("MU_CREDENTIAL missing=true provider_calls=0 effect=NOT_APPLIED")
}

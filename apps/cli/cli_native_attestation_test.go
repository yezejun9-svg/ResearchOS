package main

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

type attestRoundTripper func(*http.Request) (*http.Response, error)

func (f attestRoundTripper) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func attestFixture(t *testing.T) (*v2Context, discovery, string) {
	t.Helper()
	root := t.TempDir()
	d := discovery{URL: "http://127.0.0.1:45678", PID: 42, DataDir: filepath.Join(root, "data")}
	file := filepath.Join(root, "discovery.json")
	writeCLIDiscovery(t, file, d, "host-012345abcdef")
	t.Setenv("RESEARCHOS_CLI_DISCOVERY", file)
	t.Setenv("RESEARCHOS_NATIVE_CREATE_PILOT", "1")
	return &v2Context{clientID: "fixture-cli", credential: "fixture-bearer", projectID: "proj-fixture", commandID: "cmd-fixture", baseURL: d.URL}, d, file
}

func attestReply() []byte {
	return []byte(fmt.Sprintf(`{"kind":"NATIVE_CLIENT_ATTEST_RESULT","payload":{"schema_version":1,"attestation_ref":"natt-%s","client_instance_ref":"nci-%s","host_instance_id":"host-012345abcdef","expires_at":%q}}`, strings.Repeat("a", 64), strings.Repeat("b", 32), time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano)))
}

func installAttestFakes(t *testing.T, dial func(string, []byte) ([]byte, error), transport attestRoundTripper) {
	t.Helper()
	oldDial, oldTransport := cliNativeDial, http.DefaultTransport
	cliNativeDial = dial
	http.DefaultTransport = transport
	t.Cleanup(func() { cliNativeDial = oldDial; http.DefaultTransport = oldTransport })
}

func createAttestPayload() map[string]any {
	return map[string]any{"workspace_ref": "ws-fixture", "model_config_ref": nil, "title": "Fixture"}
}

func TestNativeCreateFinalBearerAndActualHTTPBytes(t *testing.T) {
	c, _, _ := attestFixture(t)
	var commitment map[string]any
	nativeCalls, httpCalls := 0, 0
	installAttestFakes(t, func(pipe string, raw []byte) ([]byte, error) {
		nativeCalls++
		if pipe != `\\.\pipe\ResearchOSHost-v1-012345abcdef` {
			t.Fatal("wrong Native identity")
		}
		var frame struct {
			Kind    string         `json:"kind"`
			Client  string         `json:"client_id"`
			Payload map[string]any `json:"payload"`
		}
		if json.Unmarshal(raw, &frame) != nil || frame.Kind != cliNativeAttestRequest || frame.Client != c.clientID {
			t.Fatal("wrong private frame")
		}
		commitment = frame.Payload
		if commitment["credential_value"] != "fixture-bearer" || commitment["method"] != "session.create" || commitment["project_id"] != c.projectID || len(commitment) != 9 {
			t.Fatal("wrong commitment scope")
		}
		return attestReply(), nil
	}, func(r *http.Request) (*http.Response, error) {
		httpCalls++
		raw, _ := io.ReadAll(r.Body)
		sum := sha256.Sum256(raw)
		if commitment["request_raw_sha256"] != fmt.Sprintf("sha256:%x", sum) || r.Header.Get("Authorization") != "Bearer fixture-bearer" || r.Header.Get(cliNativeAttestHeader) != "natt-"+strings.Repeat("a", 64) {
			t.Fatal("wire not bound to final commitment")
		}
		return &http.Response{StatusCode: 503, Body: io.NopCloser(strings.NewReader("fixture")), Header: make(http.Header)}, nil
	})
	v2Call(c, "session.create", createAttestPayload())
	if nativeCalls != 1 || httpCalls != 1 {
		t.Fatalf("calls native=%d http=%d", nativeCalls, httpCalls)
	}
}

func TestNativeCreateRefusalAndMutationNeverSend(t *testing.T) {
	for _, mode := range []string{"unsupported", "malformed", "duplicate", "extra", "missing", "expired", "wronghost", "tokenchange", "payloadchange", "discoverychange", "keycase", "payloadcase", "topcasecollision", "payloadcasecollision"} {
		t.Run(mode, func(t *testing.T) {
			c, d, file := attestFixture(t)
			payload := createAttestPayload()
			sent := 0
			installAttestFakes(t, func(_ string, _ []byte) ([]byte, error) {
				raw := string(attestReply())
				switch mode {
				case "unsupported":
					return nil, fmt.Errorf("fixture-bearer must not leak")
				case "malformed":
					return []byte(`{"kind":true}`), nil
				case "duplicate":
					raw = strings.Replace(raw, `"schema_version":1`, `"schema_version":1,"schema_version":1`, 1)
				case "keycase":
					raw = strings.Replace(raw, `"kind":`, `"Kind":`, 1)
				case "payloadcase":
					raw = strings.Replace(raw, `"schema_version":1`, `"SCHEMA_VERSION":1`, 1)
				case "topcasecollision":
					raw = strings.Replace(raw, `"kind":"NATIVE_CLIENT_ATTEST_RESULT"`, `"kind":"NATIVE_CLIENT_ATTEST_RESULT","Kind":"NATIVE_CLIENT_ATTEST_RESULT"`, 1)
				case "payloadcasecollision":
					raw = strings.Replace(raw, `"schema_version":1`, `"schema_version":1,"SCHEMA_VERSION":1`, 1)
				case "extra":
					raw = strings.Replace(raw, `"schema_version":1`, `"schema_version":1,"extra":true`, 1)
				case "missing":
					raw = strings.Replace(raw, `"schema_version":1,`, "", 1)
				case "expired":
					var v map[string]any
					json.Unmarshal([]byte(raw), &v)
					v["payload"].(map[string]any)["expires_at"] = "2020-01-01T00:00:00Z"
					b, _ := json.Marshal(v)
					raw = string(b)
				case "wronghost":
					raw = strings.ReplaceAll(raw, "host-012345abcdef", "host-ffffffffffff")
				case "tokenchange":
					c.credential = "changed-bearer"
				case "payloadchange":
					payload["title"] = "changed"
				case "discoverychange":
					d.PID++
					writeCLIDiscovery(t, file, d, "host-012345abcdef")
				}
				return []byte(raw), nil
			}, func(*http.Request) (*http.Response, error) {
				sent++
				return nil, fmt.Errorf("HTTP must remain fake and unsent")
			})
			reply, reason, code := v2Call(c, "session.create", payload)
			if sent != 0 || code != exitNotImplemented || reply["dispatch_state"] != "NOT_SENT" || strings.Contains(reason, "bearer") || strings.Contains(reason, "natt-") {
				t.Fatalf("not closed: sent=%d reason=%s", sent, reason)
			}
		})
	}
}

func TestNativeCreateGateOffAndOtherMethodsMakeNoNewNativeCalls(t *testing.T) {
	for _, method := range []string{"session.create", "host.status"} {
		t.Run(method, func(t *testing.T) {
			c, _, _ := attestFixture(t)
			if method == "session.create" {
				t.Setenv("RESEARCHOS_NATIVE_CREATE_PILOT", "0")
			}
			sent := 0
			installAttestFakes(t, func(string, []byte) ([]byte, error) { t.Fatal("unexpected Native call"); return nil, nil }, func(r *http.Request) (*http.Response, error) {
				sent++
				if r.Header.Get(cliNativeAttestHeader) != "" {
					t.Fatal("selector on legacy request")
				}
				return &http.Response{StatusCode: 503, Body: io.NopCloser(strings.NewReader("fixture")), Header: make(http.Header)}, nil
			})
			payload := createAttestPayload()
			if method == "host.status" {
				payload = map[string]any{}
			}
			v2Call(c, method, payload)
			if sent != 1 {
				t.Fatal("legacy request changed")
			}
		})
	}
}

// This fixture creates discovery files only in t.TempDir; no user token file,
// running Native pipe or listening HTTP service is accessed.

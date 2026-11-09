//go:build windows

package domain

import (
	"bytes"
	"context"
	"fmt"
	"golang.org/x/sys/windows"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"strconv"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func c22IndependentAssert(t *testing.T, id string, want, actual, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(actual) {
		status = "FAIL"
	}
	fmt.Println("C22_INDEPENDENT_ASSERTION " + string(Bytes(Object{"assertion_id": id, "status": status, "expected": want, "actual": actual, "evidence": evidence})))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}
func TestIndependentC22CurrentHTTPAuthority(t *testing.T) {
	for _, scenario := range []string{"grant-drop", "role-drop", "principal-revoke", "credential-revoke", "provider-unavailable"} {
		t.Run(scenario, func(t *testing.T) {
			f, store, token := protectedFixture(t)
			artifact := protectedRegister(t, f, store, c22Marker+" independent private synthetic payload", protectedMetadata())
			server, _ := fixtureHTTPServer(t, f.s.Handler())
			defer server.Close()
			audit, e := os.Create(filepath.Join(os.Getenv("RESEARCHOS_C22_EVIDENCE"), "current-"+scenario+"-http.jsonl"))
			if e != nil {
				t.Fatal(e)
			}
			defer audit.Close()
			a := &c22Audit{t: t, file: audit, url: server.URL, phase: "before-mutation", role: "restricted-verifier", audience: "AUTHORIZED_CONTROL", principal: "canary-restricted-verifier", token: token, project: f.project}
			path := "/artifacts/" + Str(artifact, "id") + "/content"
			status, raw, h := a.request("GET", path, "", "", nil)
			c22IndependentAssert(t, scenario+"-positive", []any{200, true, "no-store"}, []any{status, strings.Contains(string(raw), c22Marker), h.Get("Cache-Control")}, nil)
			interceptor := &protectedInterceptor{Provider: store}
			f.s.Protected = interceptor
			fired := false
			interceptor.afterRead = func() {
				fired = true
				var err error
				switch scenario {
				case "grant-drop":
					_, err = f.db.Exec("UPDATE auth_grants SET restricted=0 WHERE principal=? AND project=?", "canary-restricted-verifier", f.project)
				case "role-drop":
					_, err = f.db.Exec("UPDATE auth_principals SET roles=? WHERE id=?", string(Bytes([]string{"EXECUTOR"})), "canary-restricted-verifier")
				case "principal-revoke":
					err = f.s.RevokePrincipal(context.Background(), "canary-restricted-verifier")
				case "credential-revoke":
					_, err = f.db.Exec("UPDATE auth_credentials SET revoked=1 WHERE token_hash=?", Digest([]byte(token)))
				case "provider-unavailable":
					f.s.Protected = nil
				}
				if err != nil {
					t.Error(err)
				}
			}
			a.phase = "after-provider-read-current-check"
			a.audience = "CANDIDATE"
			status, raw, _ = a.request("GET", path, "", "", nil)
			expected := 404
			if scenario == "principal-revoke" || scenario == "credential-revoke" {
				expected = 401
			}
			if scenario == "provider-unavailable" {
				expected = 503
			}
			c22IndependentAssert(t, scenario+"-current-http", []any{true, expected, false}, []any{fired, status, strings.Contains(string(raw), c22Marker)}, Object{"response": string(raw), "mutation_stage": "after provider IO, before response"})
			var cached int
			if e = f.db.QueryRow("SELECT count(*) FROM idempotency WHERE instr(CAST(body AS TEXT),?)>0", c22Marker).Scan(&cached); e != nil {
				t.Fatal(e)
			}
			c22IndependentAssert(t, scenario+"-no-private-cache", 0, cached, nil)
		})
	}
}
func TestIndependentC22NativeNetworkAndHandle(t *testing.T) {
	root := t.TempDir()
	privateRoot := filepath.Join(root, "private")
	store, e := protectedstore.NewCanary(privateRoot)
	if e != nil {
		t.Fatal(e)
	}
	defer store.Close()
	blob, e := store.CreateCanary(context.Background(), "independent-c22-network-handle", "text/plain", []byte(c22Marker+" inherited-handle-only-fixture"))
	if e != nil {
		t.Fatal(e)
	}
	privatePath := filepath.Join(privateRoot, strings.TrimPrefix(blob.Ticket, "ps1:")+".bin")
	handle, e := os.Open(privatePath)
	if e != nil {
		t.Fatal(e)
	}
	defer handle.Close()
	positive, e := io.ReadAll(handle)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = handle.Seek(0, 0); e != nil {
		t.Fatal(e)
	}
	c22IndependentAssert(t, "native-host-private-positive", true, bytes.Contains(positive, []byte(c22Marker)), Object{"fixture_path": privatePath, "hash": Digest(positive)})
	wh := windows.Handle(handle.Fd())
	if e = windows.SetHandleInformation(wh, windows.HANDLE_FLAG_INHERIT, windows.HANDLE_FLAG_INHERIT); e != nil {
		t.Fatal(e)
	}
	defer windows.SetHandleInformation(wh, windows.HANDLE_FLAG_INHERIT, 0)
	var requests atomic.Int64
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests.Add(1)
		w.Write([]byte("fixture-loopback-positive"))
	}))
	defer server.Close()
	response, e := server.Client().Get(server.URL)
	if e != nil {
		t.Fatal(e)
	}
	hostResponse, e := io.ReadAll(response.Body)
	response.Body.Close()
	if e != nil {
		t.Fatal(e)
	}
	c22IndependentAssert(t, "native-host-loopback-positive", []any{200, "fixture-loopback-positive"}, []any{response.StatusCode, string(hostResponse)}, Object{"url": server.URL})
	input := filepath.Join(root, "input")
	output := filepath.Join(root, "output")
	for _, path := range []string{input, output} {
		if e = os.Mkdir(path, 0700); e != nil {
			t.Fatal(e)
		}
	}
	executable := filepath.Join(input, "network-handle-probe.exe")
	childSource := os.Getenv("C22_INDEPENDENT_CHILD_SOURCE")
	command := exec.Command(os.Getenv("RESEARCHOS_GO"), "build", "-o", executable, childSource)
	command.Env = append(os.Environ(), "GOTOOLCHAIN=local", "GOENV=off")
	raw, e := command.CombinedOutput()
	if e != nil {
		t.Fatalf("build: %v %s", e, raw)
	}
	binary, e := os.ReadFile(executable)
	if e != nil {
		t.Fatal(e)
	}
	target := strings.TrimPrefix(server.URL, "http://")
	resultPath := filepath.Join(output, "result.json")
	receipt, e := sandbox.Run(context.Background(), sandbox.Command{Executable: executable, Args: []string{strconv.FormatUint(uint64(handle.Fd()), 10), target, resultPath}, InputDirectory: input, OutputDirectory: output, Timeout: 10 * time.Second})
	c22Save(t, "independent-network-handle-receipt.json", receipt)
	if e != nil {
		t.Fatalf("independent sandbox failed; no retry: %v", e)
	}
	resultRaw, e := os.ReadFile(resultPath)
	if e != nil {
		t.Fatal(e)
	}
	result, e := Decode(resultRaw)
	if e != nil {
		t.Fatal(e)
	}
	c22Save(t, "independent-network-handle-output.json", result)
	c22Save(t, "independent-network-handle-input.json", Object{"source": childSource, "binary_sha256": Digest(binary), "binary_bytes": len(binary), "fixture_path": privatePath, "fixture_content_hash": Digest(positive), "handle": uint64(handle.Fd()), "loopback_target": target, "host_positive": true, "only_extra_inheritable_handle": "new synthetic canary file; no production handles probed"})
	c22IndependentAssert(t, "native-process-bounded", []any{0, true, false, 0, true}, []any{receipt.ExitCode, receipt.Stopped, receipt.TimedOut, len(receipt.Capabilities), receipt.SID != "" && receipt.PID != 0}, Object{"sid": receipt.SID, "pid": receipt.PID})
	c22IndependentAssert(t, "native-inherited-canary-handle-denied", []any{6, 0, ""}, []any{result["handle_read_code"], result["handle_read_bytes"], result["handle_read_body"]}, result["handle_read_error"])
	c22IndependentAssert(t, "native-loopback-network-denied", []any{false, 10013, int64(1)}, []any{result["network_connected"], result["network_code"], requests.Load()}, result["network_error"])
	c22IndependentAssert(t, "native-private-environment-not-inherited", []any{"", "", false}, []any{result["inherited_researchos_go"], result["inherited_c22_evidence"], bytes.Contains(resultRaw, []byte(c22Marker))}, nil)
}

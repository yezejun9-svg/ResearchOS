//go:build windows

package domain

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestIndependentC22NativeNetworkOnly(t *testing.T) {
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
	positive, e := io.ReadAll(response.Body)
	response.Body.Close()
	if e != nil {
		t.Fatal(e)
	}
	c22IndependentAssert(t, "network-host-loopback-positive", []any{200, "fixture-loopback-positive"}, []any{response.StatusCode, string(positive)}, Object{"url": server.URL})
	root := t.TempDir()
	input := filepath.Join(root, "input")
	output := filepath.Join(root, "output")
	for _, path := range []string{input, output} {
		if e = os.Mkdir(path, 0700); e != nil {
			t.Fatal(e)
		}
	}
	executable := filepath.Join(input, "network-only.exe")
	command := exec.Command(os.Getenv("RESEARCHOS_GO"), "build", "-o", executable, os.Getenv("C22_INDEPENDENT_CHILD_SOURCE"))
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
	receipt, e := sandbox.Run(context.Background(), sandbox.Command{Executable: executable, Args: []string{target, resultPath}, InputDirectory: input, OutputDirectory: output, Timeout: 10 * time.Second})
	c22Save(t, "independent-network-receipt.json", receipt)
	if e != nil {
		t.Fatalf("independent sandbox failed; no retry: %v", e)
	}
	c22IndependentAssert(t, "network-process-bounded", []any{0, true, false, 0, true}, []any{receipt.ExitCode, receipt.Stopped, receipt.TimedOut, len(receipt.Capabilities), receipt.SID != "" && receipt.PID != 0}, Object{"sid": receipt.SID, "pid": receipt.PID})
	resultRaw, e := os.ReadFile(resultPath)
	if e != nil {
		t.Fatal(e)
	}
	result, e := Decode(resultRaw)
	if e != nil {
		t.Fatal(e)
	}
	c22Save(t, "independent-network-output.json", result)
	c22Save(t, "independent-network-input.json", Object{"source": os.Getenv("C22_INDEPENDENT_CHILD_SOURCE"), "binary_sha256": Digest(binary), "binary_bytes": len(binary), "loopback_target": target, "host_positive": true, "no_private_path_or_handle_passed": true})
	c22IndependentAssert(t, "network-loopback-denied", []any{false, 10013, int64(1)}, []any{result["network_connected"], result["network_code"], requests.Load()}, result["network_error"])
	c22IndependentAssert(t, "network-private-environment-not-inherited", []any{"", "", false}, []any{result["inherited_researchos_go"], result["inherited_c22_evidence"], bytes.Contains(resultRaw, []byte(c22Marker))}, nil)
	fmt.Println("C22_NETWORK_SCOPE " + string(Bytes(Object{"target": "owned ephemeral loopback listener only", "external_network_not_contacted": true})))
}

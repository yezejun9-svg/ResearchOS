//go:build windows

package sandbox

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestSandboxChild(t *testing.T) {
	i := -1
	for n, a := range os.Args {
		if a == "--probe" {
			i = n
			break
		}
	}
	if i < 0 {
		return
	}
	a := os.Args[i+1:]
	if len(a) != 5 {
		os.Exit(90)
	}
	if a[4] == "timeout" {
		time.Sleep(10 * time.Second)
		os.Exit(91)
	}
	raw, e := os.ReadFile(a[0])
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(92)
	}
	var values []int
	if e = json.Unmarshal(raw, &values); e != nil {
		os.Exit(93)
	}
	sum := 0
	for _, v := range values {
		sum += v
	}
	if a[4] == "candidate" {
		sum++
	}
	_, readErr := os.ReadFile(a[1])
	writeErr := os.WriteFile(a[1], []byte("breach"), 0600)
	inputErr := os.WriteFile(a[0], []byte("breach"), 0600)
	conn, networkErr := net.DialTimeout("tcp", a[3], time.Second)
	if conn != nil {
		conn.Close()
	}
	external, externalErr := net.DialTimeout("tcp", "1.1.1.1:443", time.Second)
	if external != nil {
		external.Close()
	}
	out := map[string]any{"sum": sum, "count": len(values), "read_denied": os.IsPermission(readErr), "write_denied": os.IsPermission(writeErr), "input_write_denied": os.IsPermission(inputErr), "network_denied": networkErr != nil, "external_denied": externalErr != nil && strings.Contains(externalErr.Error(), "forbidden"), "network_error": fmt.Sprint(networkErr), "external_error": fmt.Sprint(externalErr)}
	b, _ := json.Marshal(out)
	if e = os.WriteFile(a[2], b, 0600); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(94)
	}
	fmt.Println(string(b))
	os.Exit(0)
}
func assertion(t *testing.T, id string, expected, actual any) {
	t.Helper()
	a, _ := json.Marshal(expected)
	b, _ := json.Marshal(actual)
	status := "PASS"
	if string(a) != string(b) {
		status = "FAIL"
	}
	row, _ := json.Marshal(map[string]any{"assertion_id": id, "expected": expected, "actual": actual, "status": status, "evidence": "native AppContainer process and real OS access calls"})
	fmt.Println("W10_ASSERTION " + string(row))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}
func TestNativeSandbox(t *testing.T) {
	root := t.TempDir()
	input := filepath.Join(root, "input")
	output := filepath.Join(root, "output")
	os.Mkdir(input, 0700)
	os.Mkdir(output, 0700)
	exe, _ := os.Executable()
	raw, e := os.ReadFile(exe)
	if e != nil {
		t.Fatal(e)
	}
	child := filepath.Join(input, "candidate.exe")
	os.WriteFile(child, raw, 0700)
	data := filepath.Join(input, "data.json")
	os.WriteFile(data, []byte(`[1,2,3,4]`), 0600)
	canary := filepath.Join(root, "host-private.txt")
	os.WriteFile(canary, []byte("stable"), 0600)
	listener, e := net.Listen("tcp", "127.0.0.1:0")
	if e != nil {
		t.Fatal(e)
	}
	defer listener.Close()
	host, e := net.Dial("tcp", listener.Addr().String())
	if e != nil {
		t.Fatal(e)
	}
	host.Close()
	control, e := listener.Accept()
	if e != nil {
		t.Fatal(e)
	}
	control.Close()
	assertion(t, "SANDBOX-HOST-CONTROL", true, e == nil)
	for _, mode := range []string{"baseline", "candidate", "timeout"} {
		dest := filepath.Join(output, mode+".json")
		timeout := 5 * time.Second
		if mode == "timeout" {
			timeout = 100 * time.Millisecond
		}
		r, e := Run(context.Background(), Command{child, []string{"-test.run=^TestSandboxChild$", "--", "--probe", data, canary, dest, listener.Addr().String(), mode}, input, output, timeout})
		if e != nil {
			t.Fatalf("AppContainer %s: %v", mode, e)
		}
		fmt.Printf("SANDBOX_RAW %s %s %s\n", mode, r.Stdout, r.Stderr)
		if dir := os.Getenv("W10_EVIDENCE_DIR"); dir != "" {
			b, _ := json.Marshal(r)
			os.WriteFile(filepath.Join(dir, "sandbox-"+mode+".json"), b, 0600)
			os.WriteFile(filepath.Join(dir, mode+".stdout.txt"), r.Stdout, 0600)
			os.WriteFile(filepath.Join(dir, mode+".stderr.txt"), r.Stderr, 0600)
		}
		if mode == "timeout" {
			assertion(t, "SANDBOX-TIMEOUT", []any{true, true, 124}, []any{r.TimedOut, r.Stopped, r.ExitCode})
			continue
		}
		assertion(t, "SANDBOX-EXIT-"+mode, []any{0, true}, []any{r.ExitCode, r.Stopped})
		b, e := os.ReadFile(dest)
		if e != nil {
			t.Fatal(e)
		}
		var result map[string]any
		json.Unmarshal(b, &result)
		for _, k := range []string{"read_denied", "write_denied", "input_write_denied", "network_denied", "external_denied"} {
			assertion(t, "SANDBOX-"+mode+"-"+k, true, result[k])
		}
		want := float64(10)
		if mode == "candidate" {
			want = 11
		}
		assertion(t, "SANDBOX-RECOMPUTE-"+mode, want, result["sum"])
	}
	listener.(*net.TCPListener).SetDeadline(time.Now().Add(100 * time.Millisecond))
	unexpected, networkErr := listener.Accept()
	if unexpected != nil {
		unexpected.Close()
	}
	assertion(t, "SANDBOX-OBSERVED-EGRESS", true, networkErr != nil)
	b, e := os.ReadFile(canary)
	assertion(t, "SANDBOX-STABLE-UNCHANGED", "stable", string(b))
	if e != nil {
		t.Fatal(e)
	}
}

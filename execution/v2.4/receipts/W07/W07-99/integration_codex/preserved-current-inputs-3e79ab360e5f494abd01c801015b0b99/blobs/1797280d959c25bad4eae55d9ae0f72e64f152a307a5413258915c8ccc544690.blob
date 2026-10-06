//go:build windows

package sandbox

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// W14_GO_TOOLCHAIN enables this opt-in real toolchain probe. The pinned host
// toolchain is copied into a new caller-owned input tree before any sandbox run.
func TestNativeGoToolchain(t *testing.T) {
	toolchain := os.Getenv("W14_GO_TOOLCHAIN")
	if toolchain == "" {
		t.Skip("set W14_GO_TOOLCHAIN to run the native Go probe")
	}
	root := t.TempDir()
	input, output := filepath.Join(root, "input"), filepath.Join(root, "output")
	if err := os.MkdirAll(input, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(output, 0700); err != nil {
		t.Fatal(err)
	}
	goRoot := filepath.Join(input, "go")
	if err := os.MkdirAll(goRoot, 0700); err != nil {
		t.Fatal(err)
	}
	for _, dir := range []string{"bin", "pkg", "lib"} {
		to := filepath.Join(goRoot, dir)
		if err := os.MkdirAll(to, 0700); err != nil {
			t.Fatal(err)
		}
		if err := copyTree(context.Background(), filepath.Join(toolchain, dir), to); err != nil {
			t.Fatalf("stage Go %s: %v", dir, err)
		}
	}
	if err := os.MkdirAll(filepath.Join(goRoot, "src"), 0700); err != nil {
		t.Fatal(err)
	}
	entries, err := os.ReadDir(filepath.Join(toolchain, "src"))
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if entry.Name() == "cmd" || entry.Name() == "testdata" {
			continue
		}
		if !entry.IsDir() {
			continue
		}
		to := filepath.Join(goRoot, "src", entry.Name())
		if err := os.MkdirAll(to, 0700); err != nil {
			t.Fatal(err)
		}
		if err := copyTree(context.Background(), filepath.Join(toolchain, "src", entry.Name()), to); err != nil {
			t.Fatalf("stage Go src/%s: %v", entry.Name(), err)
		}
	}
	for _, file := range []string{"VERSION", "go.env"} {
		content, err := os.ReadFile(filepath.Join(toolchain, file))
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(goRoot, file), content, 0600); err != nil {
			t.Fatal(err)
		}
	}
	for _, file := range []string{"go.mod", "go.sum"} {
		content, err := os.ReadFile(filepath.Join(toolchain, "src", file))
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(goRoot, "src", file), content, 0600); err != nil {
			t.Fatal(err)
		}
	}
	sample := filepath.Join(input, "sample")
	if err := os.MkdirAll(sample, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(sample, "go.mod"), []byte("module example.test/nativeprobe\n\ngo 1.27\n"), 0600); err != nil {
		t.Fatal(err)
	}
	const source = `package nativeprobe
import (
    "fmt"
    "testing"
    "time"
)
func TestPass(t *testing.T) { if fmt.Sprint(1 + 1) != "2" { t.Fatal("bad arithmetic") } }
func TestCancellation(t *testing.T) { fmt.Println("W14_CANCEL_READY"); time.Sleep(60 * time.Second) }
`
	if err := os.WriteFile(filepath.Join(sample, "native_test.go"), []byte(source), 0600); err != nil {
		t.Fatal(err)
	}
	executable := filepath.Join(input, "go", "bin", "go.exe")
	command := Command{Executable: executable, InputDirectory: input, OutputDirectory: output, Timeout: 120 * time.Second, ProcessLimit: 32, MemoryMiB: 1024,
		Env: map[string]string{"GOROOT": filepath.Join(input, "go"), "GOPATH": filepath.Join(output, "gopath"), "GOCACHE": filepath.Join(output, "gocache"), "GOTMPDIR": output, "GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off", "GOENV": "off", "GOWORK": "off", "CGO_ENABLED": "0"}}
	command.Args = []string{"-C", sample, "test", "-p=2", "-count=1", "-run", "^TestPass$", "./..."}
	success, err := Run(context.Background(), command)
	if err != nil {
		t.Fatalf("native go test: %v", err)
	}
	if success.ExitCode != 0 || !success.Stopped || !success.StreamsDrained || !success.CleanupComplete || !success.OutputCopied || success.JobProcesses < 2 {
		t.Fatalf("native go test failed: exit=%d children=%d stopped=%v drained=%v cleanup=%v copy=%v stdout=%s stderr=%s", success.ExitCode, success.JobProcesses, success.Stopped, success.StreamsDrained, success.CleanupComplete, success.OutputCopied, success.Stdout, success.Stderr)
	}
	if !strings.Contains(string(success.Stdout), "ok") {
		t.Fatalf("go test did not pass: %s %s", success.Stdout, success.Stderr)
	}
	cancelOutput := filepath.Join(root, "cancel-output")
	if err := os.MkdirAll(cancelOutput, 0700); err != nil {
		t.Fatal(err)
	}
	command.OutputDirectory = cancelOutput
	command.Env["GOPATH"] = filepath.Join(cancelOutput, "gopath")
	command.Env["GOCACHE"] = filepath.Join(cancelOutput, "gocache")
	command.Env["GOTMPDIR"] = cancelOutput
	command.Args = []string{"-C", sample, "test", "-p=2", "-count=1", "-v", "-run", "^TestCancellation$", "./..."}
	ready := make(chan struct{}, 1)
	var seen string
	child, err := Start(context.Background(), command, StartOptions{OnStream: func(chunk StreamChunk) error {
		if chunk.Stream == "stdout" {
			seen += string(chunk.Data)
		}
		if strings.Contains(seen, "W14_CANCEL_READY") {
			select {
			case ready <- struct{}{}:
			default:
			}
		}
		return nil
	}})
	if err != nil {
		t.Fatalf("start cancellation case: %v", err)
	}
	select {
	case <-ready:
		child.Cancel()
	case <-time.After(90 * time.Second):
		child.Cancel()
		child.Wait(context.Background())
		t.Fatal("Go child did not reach cancellation checkpoint")
	}
	cancelled, err := child.Wait(context.Background())
	if err != nil {
		t.Fatalf("cancellation wait: %v", err)
	}
	if !cancelled.TimedOut || cancelled.ExitCode != 124 || !cancelled.Stopped || !cancelled.StreamsDrained || !cancelled.CleanupComplete || cancelled.JobProcesses < 2 {
		t.Fatalf("cancel failed: exit=%d timed=%v children=%d stopped=%v drained=%v cleanup=%v", cancelled.ExitCode, cancelled.TimedOut, cancelled.JobProcesses, cancelled.Stopped, cancelled.StreamsDrained, cancelled.CleanupComplete)
	}
	report := struct {
		Status    string  `json:"status"`
		Toolchain string  `json:"toolchain"`
		GoTest    Receipt `json:"go_test"`
		Cancelled Receipt `json:"cancelled"`
	}{"PASS", "", success, cancelled}
	version, err := os.ReadFile(filepath.Join(goRoot, "VERSION"))
	if err != nil {
		t.Fatal(err)
	}
	fields := strings.Fields(string(version))
	if len(fields) == 0 {
		t.Fatal("empty staged Go VERSION")
	}
	report.Toolchain = fields[0]
	if path := os.Getenv("W14_GO_EVIDENCE_FILE"); path != "" {
		body, err := json.MarshalIndent(report, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, append(body, '\n'), 0600); err != nil {
			t.Fatal(err)
		}
	}
	fmt.Printf("W14_NATIVE_GO pass processes=%d cancel_processes=%d\n", success.JobProcesses, cancelled.JobProcesses)
}

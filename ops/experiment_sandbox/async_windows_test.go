//go:build windows

package sandbox

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"researchos.local/research-os/internal/canonical"
)

func TestRuntimeSandboxIdentityJSONExact(t *testing.T) {
	const created int64 = 1790787239271034300
	for _, value := range []any{Identity{PID: 123, Created: created}, Receipt{PID: 123, Created: created}} {
		raw, err := json.Marshal(value)
		if err != nil {
			t.Fatal(err)
		}
		canon, err := canonical.JSON(raw)
		if err != nil {
			t.Fatalf("canonical identity: %v %s", err, raw)
		}
		var object map[string]any
		if err = json.Unmarshal(canon, &object); err != nil {
			t.Fatal(err)
		}
		if object["process_created_ns"] != "1790787239271034300" {
			t.Fatalf("creation identity rounded: %s", canon)
		}
		var id Identity
		if err = json.Unmarshal(canon, &id); err != nil || id.Created != created {
			t.Fatalf("typed identity roundtrip: %+v %v", id, err)
		}
		var receipt Receipt
		if err = json.Unmarshal(canon, &receipt); err != nil || receipt.Created != created {
			t.Fatalf("typed receipt roundtrip: %+v %v", receipt, err)
		}
	}
}

func TestRuntimeSandboxChild(t *testing.T) {
	idx := -1
	for i, arg := range os.Args {
		if arg == "--runtime-probe" {
			idx = i
			break
		}
	}
	if idx < 0 {
		return
	}
	mode := os.Args[idx+1]
	if mode == "overflow" {
		fmt.Print(strings.Repeat("x", MaxStreamBytes+1))
		os.Exit(0)
	}
	if mode == "wait" {
		time.Sleep(10 * time.Second)
		os.Exit(0)
	}
	fmt.Println(`{"request":"typed-echo"}`)
	if mode == "interactive" {
		line, err := bufio.NewReader(os.Stdin).ReadString('\n')
		if err != nil || line != "{\"reply\":\"approved\"}\n" {
			os.Exit(51)
		}
	}
	if os.Getenv("RESEARCHOS_TEST_SECRET") != "" || os.Getenv("HTTP_PROXY") != "" || os.Getenv("CODEX_HOME") != "" {
		os.Exit(52)
	}
	fmt.Fprintln(os.Stderr, "stderr complete")
	if err := os.WriteFile("result.json", []byte(`{"result":"verified"}`), 0600); err != nil {
		os.Exit(53)
	}
	fmt.Println(`{"result":"verified"}`)
	os.Exit(0)
}

func runtimeSandboxCommand(t *testing.T, mode string) Command {
	t.Helper()
	root := t.TempDir()
	input := filepath.Join(root, "input")
	output := filepath.Join(root, "output")
	for _, p := range []string{input, output} {
		if err := os.Mkdir(p, 0700); err != nil {
			t.Fatal(err)
		}
	}
	exe, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(exe)
	if err != nil {
		t.Fatal(err)
	}
	child := filepath.Join(input, "candidate.exe")
	if err = os.WriteFile(child, raw, 0700); err != nil {
		t.Fatal(err)
	}
	return Command{Executable: child, Args: []string{"-test.run=^TestRuntimeSandboxChild$", "--", "--runtime-probe", mode}, InputDirectory: input, OutputDirectory: output, Timeout: 5 * time.Second}
}

func TestRuntimeSandboxAsync(t *testing.T) {
	t.Setenv("RESEARCHOS_TEST_SECRET", "host-only-sentinel")
	command := runtimeSandboxCommand(t, "interactive")
	var persisted atomic.Bool
	var identity Identity
	var mu sync.Mutex
	offsets := map[string]int64{}
	p, err := Start(context.Background(), command, StartOptions{Interactive: true, BeforeResume: func(id Identity) error {
		identity = id
		if id.PID == 0 || id.Created <= 0 || id.Job == "" || !strings.HasPrefix(id.SID, "S-1-15-2-") {
			return errors.New("missing suspended host identity")
		}
		persisted.Store(true)
		return nil
	}, OnStream: func(chunk StreamChunk) error {
		if !persisted.Load() {
			return errors.New("child ran before identity persistence")
		}
		mu.Lock()
		defer mu.Unlock()
		if chunk.Offset != offsets[chunk.Stream] {
			return errors.New("stream gap")
		}
		offsets[chunk.Stream] += int64(len(chunk.Data))
		return nil
	}})
	if err != nil {
		t.Fatal(err)
	}
	if err = p.Write(context.Background(), []byte("{\"reply\":\"approved\"}\n")); err != nil {
		p.Cancel()
		t.Fatal(err)
	}
	r, err := p.Wait(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if r.PID != identity.PID || r.Created != identity.Created || r.ExitCode != 0 || !r.Stopped || !r.StreamsDrained || !r.OutputCopied || !r.CleanupComplete || len(r.Stdout) == 0 || len(r.Stderr) == 0 {
		t.Fatalf("incomplete host receipt: %+v", r)
	}
	raw, err := os.ReadFile(filepath.Join(command.OutputDirectory, "result.json"))
	if err != nil || string(raw) != `{"result":"verified"}` {
		t.Fatalf("output: %s %v", raw, err)
	}
	encoded, _ := json.Marshal(r)
	t.Logf("RUNTIME_NATIVE_RECEIPT %s", encoded)
}

func TestRuntimeSandboxBeforeResumeVeto(t *testing.T) {
	command := runtimeSandboxCommand(t, "normal")
	var pid uint32
	var output atomic.Int64
	p, err := Start(context.Background(), command, StartOptions{BeforeResume: func(id Identity) error { pid = id.PID; return errors.New("durable identity write rejected") }, OnStream: func(chunk StreamChunk) error { output.Add(int64(len(chunk.Data))); return nil }})
	if err == nil || p != nil || pid == 0 || output.Load() != 0 {
		t.Fatalf("veto did not prevent execution: pid=%d output=%d err=%v", pid, output.Load(), err)
	}
	entries, e := os.ReadDir(command.OutputDirectory)
	if e != nil || len(entries) != 0 {
		t.Fatalf("veto produced output: %v %v", entries, e)
	}
	t.Logf("RUNTIME_BEFORE_RESUME_VETO pid=%d zero_output=true", pid)
}

func TestRuntimeSandboxStreamLimit(t *testing.T) {
	command := runtimeSandboxCommand(t, "overflow")
	p, err := Start(context.Background(), command, StartOptions{})
	if err != nil {
		t.Fatal(err)
	}
	r, err := p.Wait(context.Background())
	if err == nil || r.StreamsDrained || len(r.Stdout) > MaxStreamBytes || !r.Stopped || !r.CleanupComplete {
		t.Fatalf("stream limit not enforced: size=%d stopped=%v drained=%v err=%v", len(r.Stdout), r.Stopped, r.StreamsDrained, err)
	}
	t.Logf("RUNTIME_STREAM_LIMIT bytes=%d stopped=%v drained=%v error=%v", len(r.Stdout), r.Stopped, r.StreamsDrained, err)
}

func TestRuntimeSandboxQueuedWriteDeadline(t *testing.T) {
	p, err := Start(context.Background(), runtimeSandboxCommand(t, "wait"), StartOptions{Interactive: true})
	if err != nil {
		t.Fatal(err)
	}
	first := make(chan error, 1)
	go func() { first <- p.Write(context.Background(), bytes.Repeat([]byte("x"), 64*1024)) }()
	deadline := time.Now().Add(time.Second)
	for len(p.writeGate) == 0 {
		if time.Now().After(deadline) {
			p.Cancel()
			t.Fatal("first writer did not acquire gate")
		}
		time.Sleep(time.Millisecond)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 40*time.Millisecond)
	defer cancel()
	start := time.Now()
	err = p.Write(ctx, []byte("queued\n"))
	elapsed := time.Since(start)
	if !errors.Is(err, context.DeadlineExceeded) || elapsed > 200*time.Millisecond {
		p.Cancel()
		t.Fatalf("queued deadline: %v %s", err, elapsed)
	}
	select {
	case <-p.stopped:
		t.Fatal("queued caller cancellation stopped active writer")
	default:
	}
	p.Cancel()
	select {
	case <-first:
	case <-time.After(time.Second):
		t.Fatal("blocked first writer did not stop")
	}
	r, err := p.Wait(context.Background())
	if err != nil || !r.Stopped || !r.CleanupComplete {
		t.Fatalf("cancel cleanup: %+v %v", r, err)
	}
	t.Logf("RUNTIME_QUEUED_WRITE deadline_ms=40 elapsed_ms=%d stopped=%v", elapsed.Milliseconds(), r.Stopped)
}

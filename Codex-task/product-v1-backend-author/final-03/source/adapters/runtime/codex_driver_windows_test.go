//go:build windows

package runtime

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestCodexHarnessOwnedChild(t *testing.T) {
	if os.Getenv("RESEARCHOS_CODEX_FAKE_CHILD") != "1" {
		t.Skip("owned child entry point; assertions run in lifecycle parent")
	}
	data, _ := io.ReadAll(os.Stdin)
	if string(data) == "WAIT" {
		time.Sleep(time.Minute)
	}

	mode := string(data)
	if mode == "THREAD_AFTER_MESSAGE" {
		fmt.Println(`{"type":"item.completed","item":{"id":"early","type":"agent_message","text":"unbound"}}`)
	}
	switch mode {
	case "NO_THREAD":
	case "EMPTY_THREAD":
		fmt.Println(`{"type":"thread.started","thread_id":""}`)
	case "WHITESPACE_THREAD":
		fmt.Println(`{"type":"thread.started","thread_id":"  "}`)
	case "CONTROL_THREAD":
		fmt.Println(`{"type":"thread.started","thread_id":"bad\nthread"}`)
	case "WRONGTYPE_THREAD":
		fmt.Println(`{"type":"thread.started","thread_id":7}`)
	default:
		fmt.Println(`{"type":"thread.started","thread_id":"fake-owned-thread"}`)
	}
	if mode == "CONFLICTING_THREADS" {
		fmt.Println(`{"type":"thread.started","thread_id":"other-owned-thread"}`)
	}
	if mode == "DUPLICATE_THREAD" {
		fmt.Println(`{"type":"thread.started","thread_id":"fake-owned-thread"}`)
	}
	fmt.Println(`{"type":"item.completed","item":{"id":"a","type":"agent_message","text":"fixture response"}}`)
	fmt.Println(`{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}`)
	os.Exit(0)
}
func TestCodexHarnessFixedArguments(t *testing.T) {
	d := &codexCLI{}
	args := d.arguments("C:\\owned cwd", "D:\\source \" root")
	joined := strings.Join(args, "\n")
	for _, s := range []string{"--json", "--ephemeral", "--ignore-user-config", `default_permissions="researchos-readonly"`, "notify=[]", "features.hooks=false", `project_root_markers=[".researchos-codex-root"]`, "D:\\\\source \\\" root"} {
		if !strings.Contains(joined, s) {
			t.Fatalf("fixed argument missing %q: %q", s, args)
		}
	}
	for _, s := range []string{"--sandbox", "--dangerously-bypass-approvals-and-sandbox", "--ignore-rules", "CODEX_HOME"} {
		if strings.Contains(joined, s) {
			t.Fatal("unsafe fixed argument", s)
		}
	}
}
func TestCodexHarnessNativeLifecycle(t *testing.T) {
	exe, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(exe)
	if err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"COMPLETE", "WAIT", "FENCE", "NO_THREAD", "EMPTY_THREAD", "WHITESPACE_THREAD", "CONTROL_THREAD", "WRONGTYPE_THREAD", "CONFLICTING_THREADS", "DUPLICATE_THREAD", "THREAD_AFTER_MESSAGE"} {
		t.Run(mode, func(t *testing.T) {
			driver, err := NewCodexCLI(CodexCLIOptions{Executable: exe, Descriptor: CodexDescriptor{Present: true, ExecutableHash: Hash(raw), AuthState: "LOGGED_IN", ConfigurationControlled: true}})
			if err != nil {
				t.Fatal(err)
			}
			d := driver.(*codexCLI)
			d.fixtureArgs = []string{"-test.run=^TestCodexHarnessOwnedChild$"}
			d.fixtureEnv = []string{"RESEARCHOS_CODEX_FAKE_CHILD=1"}
			source := t.TempDir()
			sentinel := filepath.Join(source, "source.txt")
			os.WriteFile(sentinel, []byte("unchanged"), 0600)
			directory := filepath.Join(t.TempDir(), "dispatch")
			seen := false
			events := 0
			h, err := d.Start(context.Background(), CodexLaunch{TaskID: "t", RunID: "r-" + mode, Epoch: "1", Workspace: source, Prompt: mode, Directory: directory, Timeout: 5 * time.Second}, CodexCallbacks{BeforeResume: func(i CodexIdentity) error {
				seen = i.PID > 0 && i.Created > 0 && i.Job != ""
				if mode == "FENCE" {
					return fmt.Errorf("fixture fence")
				}
				return nil
			}, Event: func(e CodexEvent) error { events++; return nil }})
			if mode == "FENCE" {
				if err == nil || !seen {
					t.Fatal("rejected suspended fence resumed")
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if mode == "WAIT" {
				h.Cancel()
			}
			result, err := h.Wait(context.Background())
			if err != nil {
				t.Fatal(err)
			}
			expected := "UNKNOWN"
			if mode == "COMPLETE" || mode == "DUPLICATE_THREAD" {
				expected = "COMPLETED"
			} else if mode == "WAIT" {
				expected = "CANCELLED"
			}
			if result.State != expected || !seen || !result.Stopped || !result.StreamsDrained || !result.CleanupComplete {
				t.Fatalf("incomplete process ownership: %+v", result)
			}
			if expected == "UNKNOWN" && (result.ThreadID != "" || result.Failure != "CODEX_THREAD_IDENTITY_INVALID") {
				t.Fatal("invalid thread identity was exposed or misclassified", result.ThreadID, result.Failure)
			}
			if expected == "COMPLETED" && result.ThreadID != "fake-owned-thread" {
				t.Fatal("declared thread identity changed", result.ThreadID)
			}
			if mode == "COMPLETE" && (result.Assistant != "fixture response" || events != 1) {
				t.Fatal("actual JSONL events not mapped", result.Assistant, events)
			}
			marker := filepath.Join(directory, "cwd", ".researchos-codex-root")
			info, err := os.Stat(marker)
			if err != nil || !info.Mode().IsRegular() {
				t.Fatal("owned custom root marker must be a regular file", err)
			}
			markerBytes, err := os.ReadFile(marker)
			if err != nil || string(markerBytes) != "researchos-codex-owned-root-v1\n" {
				t.Fatal("owned marker bytes changed", err)
			}
			if _, err = os.Stat(filepath.Join(directory, "cwd", ".git")); !os.IsNotExist(err) {
				t.Fatal("Host marker must not pretend to be Git", err)
			}
			if raw, _ := os.ReadFile(sentinel); string(raw) != "unchanged" {
				t.Fatal("source modified")
			}
		})
	}
}

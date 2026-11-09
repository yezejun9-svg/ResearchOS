//go:build windows

package runtime

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// This is a local Go test child, never the Native executable or model.
func TestCodexRPCFakeChild(t *testing.T) {
	if os.Getenv("RESEARCHOS_RPC_FAKE_CHILD") != "1" {
		t.Skip("local fake-child entry")
	}
	mode := os.Getenv("RESEARCHOS_RPC_FAKE_MODE")
	rd := bufio.NewReader(os.Stdin)
	request := func(method string) map[string]any {
		line, err := rd.ReadBytes('\n')
		if err != nil {
			os.Exit(71)
		}
		var frame map[string]any
		if json.Unmarshal(line, &frame) != nil || frame["method"] != method {
			os.Exit(72)
		}
		return frame
	}
	request("initialize")
	fmt.Fprintln(os.Stdout, `{"id":1,"result":{"userAgent":"fake-go-child"}}`)
	request("initialized")
	start := request("thread/start")
	params, ok := start["params"].(map[string]any)
	if !ok || params["approvalPolicy"] != "never" || params["approvalsReviewer"] != "user" || params["ephemeral"] != true {
		os.Exit(73)
	}
	profile, _ := params["permissions"].(string)
	cwd, _ := params["cwd"].(string)
	roots, _ := params["runtimeWorkspaceRoots"].([]any)
	if len(roots) != 1 || !strings.HasPrefix(profile, "researchos-readonly-") {
		os.Exit(74)
	}
	source, _ := roots[0].(string)
	if mode == "STDERR_WARNING" {
		// One kernel pipe must preserve the synchronous stderr prefix before stdout.
		fmt.Fprint(os.Stderr, "Native helper setup warning\n")
	}
	active := map[string]any{"id": profile}
	sandbox := map[string]any{"type": "readOnly", "networkAccess": false}
	if mode == "PROFILE_FALLBACK" {
		active["id"] = "default"
	}
	if mode == "EXTENDS" {
		active["extends"] = "base"
	}
	if mode == "WRITE_SANDBOX" {
		sandbox["type"] = "workspaceWrite"
	}
	if mode == "NETWORK" {
		sandbox["networkAccess"] = true
	}
	if mode == "UNKNOWN_STARTUP" {
		fmt.Fprintln(os.Stdout, `{"method":"thread/replaced","params":{}}`)
	}
	result := map[string]any{"thread": map[string]any{"id": "fake-thread"}, "activePermissionProfile": active,
		"cwd": cwd, "runtimeWorkspaceRoots": []string{source}, "approvalPolicy": "never", "approvalsReviewer": "user", "sandbox": sandbox}
	if mode == "CWD" {
		result["cwd"] = "C:\\other"
	}
	response, _ := json.Marshal(map[string]any{"id": 2, "result": result})
	fmt.Fprintln(os.Stdout, string(response))
	if mode == "DUPLICATE_RESPONSE" {
		fmt.Fprintln(os.Stdout, string(response))
	}
	fmt.Fprintln(os.Stdout, `{"method":"thread/started","params":{"thread":{"id":"fake-thread"}}}`)
	turn := request("turn/start")
	turnParams, ok := turn["params"].(map[string]any)
	if !ok || len(turnParams) != 2 || turnParams["threadId"] != "fake-thread" {
		os.Exit(75)
	}
	items, _ := turnParams["input"].([]any)
	if len(items) != 1 {
		os.Exit(76)
	}
	item, _ := items[0].(map[string]any)
	if item["type"] != "text" || !strings.Contains(fmt.Sprint(item["text"]), "researchos.codex-source-context.v1") {
		os.Exit(77)
	}
	fmt.Fprintln(os.Stdout, `{"id":3,"result":{"turn":{"id":"turn-1"}}}`)
	if mode == "DUPLICATE_ACK" {
		fmt.Fprintln(os.Stdout, `{"id":3,"result":{"turn":{"id":"turn-1"}}}`)
	}
	fmt.Fprintln(os.Stdout, `{"method":"turn/started","params":{"threadId":"fake-thread","turn":{"id":"turn-1","status":"inProgress"}}}`)
	itemThread, itemTurn, itemType := "fake-thread", "turn-1", "agentMessage"
	if mode == "ITEM_OTHER_THREAD" {
		itemThread = "other"
	}
	if mode == "ITEM_OTHER_TURN" {
		itemTurn = "other"
	}
	if mode == "UNEXPECTED_ITEM" {
		itemType = "fileChange"
	}
	itemFrame, _ := json.Marshal(map[string]any{"method": "item/completed", "params": map[string]any{
		"threadId": itemThread, "turnId": itemTurn, "item": map[string]any{"type": itemType, "text": "fixture response"}}})
	fmt.Fprintln(os.Stdout, string(itemFrame))
	if mode == "TURN_WRONG_THREAD" {
		fmt.Fprintln(os.Stdout, `{"method":"turn/completed","params":{"threadId":"other","turn":{"id":"turn-1","status":"completed"}}}`)
	} else {
		fmt.Fprintln(os.Stdout, `{"method":"turn/completed","params":{"threadId":"fake-thread","turn":{"id":"turn-1","status":"completed"}}}`)
	}
	os.Exit(0)
}

func rpcFakeDriver(t *testing.T, qualified bool) *codexRPC {
	t.Helper()
	exe, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(exe)
	if err != nil {
		t.Fatal(err)
	}
	options := CodexRPCOptions{Executable: exe, NormalHome: os.Getenv("USERPROFILE"),
		Descriptor: CodexDescriptor{Present: true, ExecutableHash: Hash(raw), AuthState: "LOGGED_IN", ConfigurationControlled: true}}
	var driver CodexDriver
	if qualified {
		driver, err = NewCodexRPCForTrustedGoTest(options, CodexQualificationFunc(func(ctx context.Context, e CodexTurnEvidence) error {
			if ctx.Err() != nil || e.ThreadID != "fake-thread" || e.ProfileNonce == "" || e.SourceBindingHash != "source-hash" ||
				e.Process.PID == 0 || e.Process.Created == 0 || e.RenderedConfigSHA256 == "" {
				return errors.New("BAD_FAKE_EVIDENCE")
			}
			return nil
		}))
	} else {
		driver, err = NewCodexRPC(options)
	}
	if err != nil {
		t.Fatal(err)
	}
	d := driver.(*codexRPC)
	d.fixtureArgs = []string{"-test.run=^TestCodexRPCFakeChild$"}
	return d
}

func TestCodexRPCFakeLifecycle(t *testing.T) {
	for _, tc := range []struct {
		name      string
		qualified bool
		failure   string
		turn      bool
	}{
		{"COMPLETE", true, "", true},
		{"UNQUALIFIED", false, "QUALIFICATION_REQUIRED", false},
		{"STDERR_WARNING", true, "CODEX_RPC_FRAME_INVALID", false},
		{"PROFILE_FALLBACK", true, "CODEX_RPC_ACTIVE_PROFILE_MISMATCH", false},
		{"EXTENDS", true, "CODEX_RPC_ACTIVE_PROFILE_MISMATCH", false},
		{"WRITE_SANDBOX", true, "CODEX_RPC_SANDBOX_MISMATCH", false},
		{"NETWORK", true, "CODEX_RPC_SANDBOX_MISMATCH", false},
		{"CWD", true, "CODEX_RPC_THREAD_SETTINGS_MISMATCH", false},
		{"UNKNOWN_STARTUP", true, "CODEX_RPC_UNEXPECTED_STARTUP_FRAME", false},
		{"DUPLICATE_RESPONSE", true, "CODEX_RPC_DUPLICATE_RESPONSE", false},
		{"TURN_WRONG_THREAD", true, "CODEX_RPC_EVENT_THREAD_MISMATCH", true},
		{"ITEM_OTHER_THREAD", true, "CODEX_RPC_EVENT_THREAD_MISMATCH", true},
		{"ITEM_OTHER_TURN", true, "CODEX_RPC_EVENT_TURN_MISMATCH", true},
		{"UNEXPECTED_ITEM", true, "CODEX_RPC_UNEXPECTED_ITEM", true},
		{"DUPLICATE_ACK", true, "CODEX_RPC_TURN_RESPONSE_INVALID", true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			d := rpcFakeDriver(t, tc.qualified)
			d.fixtureEnv = []string{"RESEARCHOS_RPC_FAKE_CHILD=1", "RESEARCHOS_RPC_FAKE_MODE=" + tc.name}
			source := t.TempDir()
			directory := filepath.Join(t.TempDir(), "dispatch")
			beforeResume, beforeTurn, events := 0, 0, 0
			h, err := d.Start(context.Background(), CodexLaunch{TaskID: "task", RunID: "rpc-" + tc.name, Epoch: "1",
				Workspace: source, Prompt: "Read source", Directory: directory, SourceBindingHash: "source-hash", Timeout: 10 * time.Second},
				CodexCallbacks{BeforeResume: func(i CodexIdentity) error {
					beforeResume++
					if i.PID == 0 || i.Created == 0 {
						return errors.New("BAD_PROCESS")
					}
					return nil
				},
					BeforeModelTurn: func(e CodexTurnEvidence) error { beforeTurn++; return nil },
					Event:           func(e CodexEvent) error { events++; return nil }})
			if err != nil {
				t.Fatal(err)
			}
			result, err := h.Wait(context.Background())
			if err != nil {
				t.Fatal(err)
			}
			if beforeResume != 1 || !result.Stopped || !result.StreamsDrained || !result.CleanupComplete {
				t.Fatalf("ownership: %+v, beforeResume=%d", result, beforeResume)
			}
			if tc.failure == "" {
				if result.State != "COMPLETED" || result.Assistant != "fixture response" || events != 1 || beforeTurn != 1 {
					t.Fatalf("completion: %+v events=%d turn=%d", result, events, beforeTurn)
				}
			} else if result.State != "UNKNOWN" || result.Failure != tc.failure {
				t.Fatalf("expected %s: %+v", tc.failure, result)
			}
			intent := filepath.Join(directory, "native-turn-write-intent.json")
			_, statErr := os.Stat(intent)
			if tc.turn && statErr != nil {
				t.Fatal("consumed turn intent missing", statErr)
			}
			if !tc.turn && !os.IsNotExist(statErr) {
				t.Fatal("turn intent minted before barrier", statErr)
			}
			if tc.name == "STDERR_WARNING" {
				capture := string(result.Stdout)
				initAt := strings.Index(capture, `"id":1`)
				warningAt := strings.Index(capture, "Native helper setup warning\n")
				threadAt := strings.Index(capture, `"id":2`)
				// The fake child writes the initialize response first, then
				// stderr warning, then the thread response. The single kernel
				// capture pipe must preserve that order without letting the
				// later valid response authorize a prompt.
				if initAt < 0 || warningAt <= initAt || (threadAt >= 0 && threadAt <= warningAt) {
					t.Fatal("single-pipe startup ordering lost", capture)
				}
			}
		})
	}
}

func TestCodexRPCBeforeResumeAndTurnFences(t *testing.T) {
	for _, fence := range []string{"RESUME", "TURN"} {
		t.Run(fence, func(t *testing.T) {
			d := rpcFakeDriver(t, true)
			d.fixtureEnv = []string{"RESEARCHOS_RPC_FAKE_CHILD=1", "RESEARCHOS_RPC_FAKE_MODE=COMPLETE"}
			directory := filepath.Join(t.TempDir(), "dispatch")
			h, err := d.Start(context.Background(), CodexLaunch{TaskID: "task", RunID: "rpc-fence-" + fence, Epoch: "1",
				Workspace: t.TempDir(), Prompt: "Read source", Directory: directory, SourceBindingHash: "source-hash", Timeout: 10 * time.Second},
				CodexCallbacks{BeforeResume: func(CodexIdentity) error {
					if fence == "RESUME" {
						return errors.New("RESUME_REFUSED")
					}
					return nil
				},
					BeforeModelTurn: func(CodexTurnEvidence) error {
						if fence == "TURN" {
							return errors.New("TURN_REFUSED")
						}
						return nil
					},
					Event: func(CodexEvent) error { return nil }})
			if fence == "RESUME" {
				if err == nil || !strings.Contains(err.Error(), "RESUME_REFUSED") || h != nil {
					t.Fatal("suspended fence resumed", h, err)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			result, err := h.Wait(context.Background())
			if err != nil || result.State != "UNKNOWN" || result.Failure != "TURN_REFUSED" || !result.CleanupComplete {
				t.Fatal(result, err)
			}
			if _, err := os.Stat(filepath.Join(directory, "native-turn-write-intent.json")); !os.IsNotExist(err) {
				t.Fatal("turn sent after fence", err)
			}
		})
	}
}

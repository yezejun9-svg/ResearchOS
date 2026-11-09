//go:build windows

package runtime

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
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
	if _, present := params["environments"]; present {
		os.Exit(78)
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
	if mode == "DELAYED_WARNING" || mode == "DELAYED_PARTIAL" || mode == "DELAYED_REQUEST" {
		time.Sleep(50 * time.Millisecond)
		if mode == "DELAYED_WARNING" {
			fmt.Fprint(os.Stderr, "late native warning\n")
		}
		if mode == "DELAYED_PARTIAL" {
			fmt.Fprint(os.Stderr, `{"method":`)
		}
		if mode == "DELAYED_REQUEST" {
			fmt.Fprintln(os.Stdout, `{"id":55,"method":"item/requestApproval","params":{}}`)
		}
	}
	turn := request("turn/start")
	if sentinel := os.Getenv("RESEARCHOS_RPC_TURN_SENTINEL"); sentinel != "" {
		_ = os.WriteFile(sentinel, []byte("turn-received"), 0600)
	}
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
	if mode == "COMPLETE" {
		fmt.Fprintln(os.Stdout, `{"method":"thread/status/changed","params":{"threadId":"fake-thread","status":{"type":"active","activeFlags":[]}}}`)
	}
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
	startFrame, _ := json.Marshal(map[string]any{"method": "item/started", "params": map[string]any{
		"threadId": "fake-thread", "turnId": "turn-1", "item": map[string]any{"id": "item-1", "type": itemType}}})
	fmt.Fprintln(os.Stdout, string(startFrame))
	if mode == "MISSING_ITEM_COMPLETION" {
		fmt.Fprintln(os.Stdout, `{"method":"turn/completed","params":{"threadId":"fake-thread","turn":{"id":"turn-1","status":"completed"}}}`)
		os.Exit(0)
	}
	if mode == "COMPLETE" {
		fmt.Fprintln(os.Stdout, `{"method":"item/agentMessage/delta","params":{"threadId":"fake-thread","turnId":"turn-1","itemId":"item-1","delta":"fixture "}}`)
	}
	itemText := "fixture response"
	if mode == "EMPTY_ASSISTANT" {
		itemText = ""
	}
	itemFrame, _ := json.Marshal(map[string]any{"method": "item/completed", "params": map[string]any{
		"threadId": itemThread, "turnId": itemTurn, "item": map[string]any{"id": "item-1", "type": itemType, "text": itemText}}})
	fmt.Fprintln(os.Stdout, string(itemFrame))
	if mode == "DUPLICATE_ITEM" {
		fmt.Fprintln(os.Stdout, string(itemFrame))
	}
	if mode == "TURN_WRONG_THREAD" {
		fmt.Fprintln(os.Stdout, `{"method":"turn/completed","params":{"threadId":"other","turn":{"id":"turn-1","status":"completed"}}}`)
	} else if mode == "TRAILING_ERROR" {
		fmt.Fprint(os.Stdout, `{"method":"turn/completed","params":{"threadId":"fake-thread","turn":{"id":"turn-1","status":"completed"}}}`+"\n"+
			`{"method":"error","params":{"threadId":"fake-thread"}}`+"\n")
	} else if mode == "TRAILING_PARTIAL" {
		fmt.Fprint(os.Stdout, `{"method":"turn/completed","params":{"threadId":"fake-thread","turn":{"id":"turn-1","status":"completed"}}}`+"\n"+
			`{"method":`)
	} else if mode == "COMPLETE" {
		fmt.Fprint(os.Stdout, `{"method":"turn/completed","params":{"threadId":"fake-thread","turn":{"id":"turn-1","status":"completed"}}}`+"\n"+
			`{"method":"thread/status/changed","params":{"threadId":"fake-thread","status":{"type":"idle"}}}`+"\n")
	} else {
		fmt.Fprintln(os.Stdout, `{"method":"turn/completed","params":{"threadId":"fake-thread","turn":{"id":"turn-1","status":"completed"}}}`)
	}
	os.Exit(0)
}

func TestCodexRPCCaptureBudget(t *testing.T) {
	input, err := os.CreateTemp(t.TempDir(), "capture-input")
	if err != nil {
		t.Fatal(err)
	}
	defer input.Close()
	if _, err = input.Write(bytes.Repeat([]byte("x"), rpcCaptureLimit+1)); err != nil {
		t.Fatal(err)
	}
	if _, err = input.Seek(0, 0); err != nil {
		t.Fatal(err)
	}
	file, err := os.CreateTemp(t.TempDir(), "capture-durable")
	if err != nil {
		t.Fatal(err)
	}
	var raw bytes.Buffer
	_, err = io.Copy(io.Discard, &rpcCaptureReader{pipe: input, file: file, raw: &raw})
	if !errors.Is(err, errRPCCaptureLimit) || raw.Len() != rpcCaptureLimit {
		t.Fatal("ingestion ceiling failed", raw.Len(), err)
	}
	if err = file.Sync(); err != nil {
		t.Fatal(err)
	}
	durable, err := os.ReadFile(file.Name())
	if err != nil || !bytes.Equal(raw.Bytes(), durable) {
		t.Fatal("bounded prefix not durable", err)
	}
	if err = file.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err = input.Seek(0, 0); err != nil {
		t.Fatal(err)
	}
	raw.Reset()
	n, err := (&rpcCaptureReader{pipe: input, file: file, raw: &raw}).Read(make([]byte, 16))
	if n != 0 || err == nil || !strings.Contains(err.Error(), "CODEX_RPC_CAPTURE_PERSIST_FAILED") {
		t.Fatal("closed durable sink did not fail closed", n, err)
	}
}

func TestCodexRPCOwnedJobBudget(t *testing.T) {
	nonce, err := rpcNonce()
	if err != nil {
		t.Fatal(err)
	}
	job, err := newJob("researchos-rpc-budget-fake-" + nonce)
	if err != nil {
		t.Fatal(err)
	}
	budget, err := rpcApplyJobBudget(job)
	if err != nil {
		closeJob(job)
		t.Fatal(err)
	}
	if budget.LimitFlags != 0x2308 || budget.ActiveProcessLimit != 16 ||
		budget.ProcessCommitBytes != 1<<30 || budget.JobCommitBytes != 2<<30 {
		closeJob(job)
		t.Fatal("actual Job query did not match fixed caps", budget)
	}
	closeJob(job)
	if _, err = rpcApplyJobBudget(job); err == nil {
		t.Fatal("closed Job was accepted as bounded")
	}
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
		{"MISSING_ITEM_COMPLETION", true, "CODEX_RPC_TURN_NOT_COMPLETED", true},
		{"EMPTY_ASSISTANT", true, "CODEX_RPC_ASSISTANT_INVALID", true},
		{"DUPLICATE_ITEM", true, "CODEX_RPC_ITEM_ID_MISMATCH", true},
		{"TRAILING_ERROR", true, "CODEX_RPC_TERMINAL_TRAILING_BYTES", true},
		{"TRAILING_PARTIAL", true, "CODEX_RPC_TERMINAL_TRAILING_BYTES", true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			d := rpcFakeDriver(t, tc.qualified)
			d.fixtureEnv = []string{"RESEARCHOS_RPC_FAKE_CHILD=1", "RESEARCHOS_RPC_FAKE_MODE=" + tc.name}
			source := t.TempDir()
			directory := filepath.Join(t.TempDir(), "dispatch")
			sentinel := filepath.Join(t.TempDir(), "turn-seen")
			d.fixtureEnv = append(d.fixtureEnv, "RESEARCHOS_RPC_TURN_SENTINEL="+sentinel)
			beforeResume, beforeTurn, events := 0, 0, 0
			var eventValues []CodexEvent
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
					Event:           func(e CodexEvent) error { events++; eventValues = append(eventValues, e); return nil }})
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
				if result.State != "COMPLETED" || result.Assistant != "fixture response" || events != 1 || beforeTurn != 1 ||
					eventValues[0].Kind != "ASSISTANT_MESSAGE" || eventValues[0].NativeID != "item-1" {
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
			_, sentinelErr := os.Stat(sentinel)
			if tc.turn && sentinelErr != nil {
				t.Fatal("fake child never received turn", sentinelErr)
			}
			if !tc.turn && !os.IsNotExist(sentinelErr) {
				t.Fatal("fake child received forbidden turn", sentinelErr)
			}
			durable, readErr := os.ReadFile(filepath.Join(directory, "native-rpc-capture.raw"))
			if readErr != nil || string(durable) != string(result.Stdout) {
				t.Fatal("durable capture differed from bounded result", readErr)
			}
			if _, err := os.Stat(filepath.Join(directory, "native-rpc-terminal.json")); err != nil {
				t.Fatal("terminal receipt missing", err)
			}
			budgetRaw, err := os.ReadFile(filepath.Join(directory, "native-rpc-job-limits.json"))
			if err != nil {
				t.Fatal("same Job budget audit missing", err)
			}
			var budgetAudit struct {
				Requested, Queried                           rpcJobBudget
				Job, Source, SourceBindingHash, AppliedAtUTC string
			}
			if json.Unmarshal(budgetRaw, &budgetAudit) != nil || budgetAudit.Requested != budgetAudit.Queried ||
				budgetAudit.Queried.LimitFlags != 0x2308 || budgetAudit.Queried.ActiveProcessLimit != 16 ||
				budgetAudit.Source != source || budgetAudit.SourceBindingHash != "source-hash" || budgetAudit.Job != result.Identity.Job ||
				budgetAudit.AppliedAtUTC == "" {
				t.Fatal("budget audit not bound to actual RPC Job", string(budgetRaw))
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

func TestCodexRPCDelayedCaptureFence(t *testing.T) {
	for _, mode := range []string{"DELAYED_WARNING", "DELAYED_PARTIAL", "DELAYED_REQUEST"} {
		t.Run(mode, func(t *testing.T) {
			d := rpcFakeDriver(t, true)
			sentinel := filepath.Join(t.TempDir(), "turn-seen")
			d.fixtureEnv = []string{"RESEARCHOS_RPC_FAKE_CHILD=1", "RESEARCHOS_RPC_FAKE_MODE=" + mode,
				"RESEARCHOS_RPC_TURN_SENTINEL=" + sentinel}
			directory := filepath.Join(t.TempDir(), "dispatch")
			h, err := d.Start(context.Background(), CodexLaunch{TaskID: "task", RunID: "rpc-late-" + mode, Epoch: "1",
				Workspace: t.TempDir(), Prompt: "Read source", Directory: directory, SourceBindingHash: "source-hash", Timeout: 10 * time.Second},
				CodexCallbacks{BeforeResume: func(CodexIdentity) error { return nil },
					BeforeModelTurn: func(CodexTurnEvidence) error { time.Sleep(200 * time.Millisecond); return nil },
					Event:           func(CodexEvent) error { return nil }})
			if err != nil {
				t.Fatal(err)
			}
			result, err := h.Wait(context.Background())
			if err != nil || result.State != "UNKNOWN" || result.Failure == "" || !result.CleanupComplete {
				t.Fatal("late preturn traffic did not stop safely", result, err)
			}
			if _, err := os.Stat(sentinel); !os.IsNotExist(err) {
				t.Fatal("prompt reached child after late diagnostic", err)
			}
			if _, err := os.Stat(filepath.Join(directory, "native-turn-write-intent.json")); !os.IsNotExist(err) {
				t.Fatal("turn intent minted after late diagnostic", err)
			}
			raw, err := os.ReadFile(filepath.Join(directory, "native-rpc-capture.raw"))
			if err != nil || len(raw) == 0 || string(raw) != string(result.Stdout) {
				t.Fatal("late diagnostic not durably captured", err, result)
			}
			if mode == "DELAYED_WARNING" && !strings.Contains(string(raw), "late native warning") {
				t.Fatal("warning missing from durable capture")
			}
			if mode == "DELAYED_PARTIAL" && !strings.HasSuffix(string(raw), `{"method":`) {
				t.Fatal("partial frame lost", string(raw))
			}
		})
	}
}

func TestCodexRPCCancelDuringTurnFence(t *testing.T) {
	d := rpcFakeDriver(t, true)
	sentinel := filepath.Join(t.TempDir(), "turn-seen")
	d.fixtureEnv = []string{"RESEARCHOS_RPC_FAKE_CHILD=1", "RESEARCHOS_RPC_FAKE_MODE=COMPLETE",
		"RESEARCHOS_RPC_TURN_SENTINEL=" + sentinel}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	directory := filepath.Join(t.TempDir(), "dispatch")
	h, err := d.Start(ctx, CodexLaunch{TaskID: "task", RunID: "rpc-cancel-fence", Epoch: "1",
		Workspace: t.TempDir(), Prompt: "Read source", Directory: directory, SourceBindingHash: "source-hash", Timeout: 10 * time.Second},
		CodexCallbacks{BeforeResume: func(CodexIdentity) error { return nil },
			BeforeModelTurn: func(CodexTurnEvidence) error { cancel(); return nil },
			Event:           func(CodexEvent) error { return nil }})
	if err != nil {
		t.Fatal(err)
	}
	result, err := h.Wait(context.Background())
	if err != nil || result.State != "UNKNOWN" || result.Failure != "CODEX_RPC_TURN_FENCE_CLOSED" || !result.Stopped {
		t.Fatal("cancel did not close turn fence", result, err)
	}
	if _, err := os.Stat(sentinel); !os.IsNotExist(err) {
		t.Fatal("prompt reached cancelled child", err)
	}
	if _, err := os.Stat(filepath.Join(directory, "native-turn-write-intent.json")); !os.IsNotExist(err) {
		t.Fatal("intent after cancel", err)
	}
}

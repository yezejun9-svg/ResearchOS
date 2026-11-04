//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	goruntime "runtime"
	"sync/atomic"
	"testing"
	"time"
)

type harnessAuthorityFixture struct {
	principal string
	err       error
}

func (a *harnessAuthorityFixture) HarnessPrincipal(context.Context) (string, error) {
	return a.principal, a.err
}
func harnessExecutable(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	source := filepath.Join(dir, "main.go")
	binary := filepath.Join(dir, "owned-codex-fixture.exe")
	program := `package main
 import("os";"io";"fmt";"time";"encoding/json")
 func main(){raw,_:=io.ReadAll(os.Stdin);var input map[string]json.RawMessage;var schema,prompt string;var source map[string]string
 if json.Unmarshal(raw,&input)!=nil||json.Unmarshal(input["schema"],&schema)!=nil||schema!="researchos.codex-source-context.v1"||json.Unmarshal(input["source_context"],&source)!=nil||source["source_workspace"]==""||source["process_working_directory"]==""||source["access"]!="READ_ONLY"||json.Unmarshal(input["user_request"],&prompt)!=nil{os.Exit(73)}
 if prompt=="WAIT"{time.Sleep(time.Minute)}
 fmt.Println("{\"type\":\"thread.started\",\"thread_id\":\"fixture-cli-thread\"}")
 fmt.Println("{\"type\":\"item.completed\",\"item\":{\"id\":\"a\",\"type\":\"agent_message\",\"text\":\"finite fixture response\"}}")
 if prompt=="UNKNOWN"{return};if prompt=="FAIL"{os.Exit(7)}
 fmt.Println("{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":1,\"output_tokens\":1}}")
 }`
	if err := os.WriteFile(source, []byte(program), 0600); err != nil {
		t.Fatal(err)
	}
	command := exec.Command(filepath.Join(goruntime.GOROOT(), "bin", "go.exe"), "build", "-o", binary, source)
	command.Env = append(os.Environ(), "GOPROXY=off", "GOSUMDB=off", "GOTOOLCHAIN=local", "GOENV=off", "CGO_ENABLED=0")
	if output, err := command.CombinedOutput(); err != nil {
		t.Fatalf("owned fake executable compile: %v %s", err, output)
	}
	return binary
}
func harnessFixture(t *testing.T, exe string) (*fixture, *RuntimeCoordinator, *WorkspaceBinding) {
	t.Helper()
	f := contextFixtureFrom(setupWithConstructor(t, NewCurrentMu))
	b := &WorkspaceBinding{AuthorizedRef: "workspace-harness", DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "fixture-client", HostPrincipalRef: "fixture-host", CreatedAt: Now()}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
	})
	raw, err := os.ReadFile(exe)
	if err != nil {
		t.Fatal(err)
	}
	driver, err := rt.NewCodexCLI(rt.CodexCLIOptions{Executable: exe, Descriptor: rt.CodexDescriptor{Present: true, ExecutableHash: Digest(raw), AuthState: "LOGGED_IN", AuthKind: "other", ConfigurationControlled: true}})
	if err != nil {
		t.Fatal(err)
	}
	var seq int
	var name, dbpath string
	if err = f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbpath); err != nil {
		t.Fatal(err)
	}
	c, err := f.s.NewRuntimeCoordinator(context.Background(), RuntimeCoordinatorConfig{DataRoot: filepath.Dir(dbpath), APIURL: "http://127.0.0.1:1", WorkspaceAuthority: clientWorkspaceAuthority{}, HarnessAuthority: &harnessAuthorityFixture{principal: f.owner}, HarnessDriver: driver})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := c.Close(); err != nil {
			t.Error(err)
		}
	})
	return f, c, b
}
func harnessSubmitFixture(t *testing.T, f *fixture, c *RuntimeCoordinator, b *WorkspaceBinding, prompt string) (string, Object) {
	t.Helper()
	in := HarnessSubmit{RequestID: "request-" + ID(), ProjectID: f.project, WorkspaceRef: b.AuthorizedRef, HarnessID: "codex", Scope: "workspace-read", Prompt: prompt}
	ack, err := c.HarnessV1().Submit(context.Background(), f.token, in)
	if err != nil {
		t.Fatal("real submit", err)
	}
	if replay, err := c.HarnessV1().Submit(context.Background(), f.token, in); err != nil || Hash(replay) != Hash(ack) {
		t.Fatal("idempotent submit", err)
	}
	data := ack["data"].(map[string]any)
	if data["run"] != nil || data["status"] != "QUEUED" {
		t.Fatal("submit fabricated Run", ack)
	}
	id := Str(data["task_ref"].(map[string]any), "task_id")
	in.Prompt += " changed"
	if _, err = c.HarnessV1().Submit(context.Background(), f.token, in); err == nil {
		t.Fatal("request_id changed payload allowed")
	}
	return id, ack
}
func harnessViewFixture(t *testing.T, f *fixture, c *RuntimeCoordinator, id string) Object {
	t.Helper()
	reply, err := c.HarnessV1().Get(context.Background(), f.token, f.project, id)
	if err != nil {
		t.Fatal(err)
	}
	return reply["data"].(map[string]any)
}
func TestHarnessCoordinatorFakeChain(t *testing.T) {
	exe := harnessExecutable(t)
	for _, mode := range []string{"COMPLETE", "FAIL", "UNKNOWN", "WAIT", "QUEUED_CANCEL", "AUTHORITY", "WORKSPACE"} {
		t.Run(mode, func(t *testing.T) {
			f, c, b := harnessFixture(t, exe)
			prompt := mode
			if mode == "QUEUED_CANCEL" || mode == "AUTHORITY" || mode == "WORKSPACE" {
				prompt = "COMPLETE"
			}
			id, _ := harnessSubmitFixture(t, f, c, b, prompt)
			port := c.HarnessV1()
			list, err := port.List(context.Background(), f.token, HarnessList{ProjectID: f.project, Cursor: "0", Limit: 20})
			if err != nil || len(Arr(list["data"].(map[string]any), "items")) != 1 {
				t.Fatal("authoritative task list", list, err)
			}
			if mode == "QUEUED_CANCEL" {
				view := harnessViewFixture(t, f, c, id)
				reply, err := port.Cancel(context.Background(), f.token, f.project, id, HarnessCancel{RequestID: "cancel-before", ExpectedTaskRevision: Str(view, "task_revision")})
				if err != nil {
					t.Fatal(err)
				}
				if reply["data"].(map[string]any)["disposition"] != "CANCELLED_BEFORE_LAUNCH" {
					t.Fatal(reply)
				}
			} else {
				if mode == "AUTHORITY" {
					c.config.HarnessAuthority = &harnessAuthorityFixture{principal: "foreign"}
				}
				if mode == "WORKSPACE" {
					sourceTx(t, f.db, func(tx *sql.Tx) error {
						b.Status = "REVOKED"
						b.Revision++
						return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
					})
				}
				if err = c.Scan(context.Background()); err != nil && mode != "AUTHORITY" {
					t.Fatal("same Scan", err)
				}
				if mode == "AUTHORITY" || mode == "WORKSPACE" {
					var runs int
					f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run'").Scan(&runs)
					if runs != 0 {
						t.Fatal("revoked authority launched")
					}
					return
				}
				if mode == "WAIT" {
					deadline := time.Now().Add(10 * time.Second)
					var view Object
					for time.Now().Before(deadline) {
						view = harnessViewFixture(t, f, c, id)
						if view["status"] == "RUNNING" {
							break
						}
						time.Sleep(20 * time.Millisecond)
					}
					if view["status"] != "RUNNING" {
						t.Fatal("did not start", view)
					}
					run := view["run"].(map[string]any)
					runID, epoch := Str(run, "run_id"), Str(run, "epoch")
					stale := HarnessCancel{RequestID: "cancel-stale", ExpectedTaskRevision: Str(view, "task_revision"), ExpectedRunID: &runID}
					wrong := "999"
					stale.ExpectedEpoch = &wrong
					if _, err = port.Cancel(context.Background(), f.token, f.project, id, stale); err == nil {
						t.Fatal("stale epoch accepted")
					}
					_, err = port.Cancel(context.Background(), f.token, f.project, id, HarnessCancel{RequestID: "cancel-active", ExpectedTaskRevision: Str(view, "task_revision"), ExpectedRunID: &runID, ExpectedEpoch: &epoch})
					if err != nil {
						t.Fatal("cancel", err)
					}
				}
				c.workers.Wait()
			}
			view := harnessViewFixture(t, f, c, id)
			expected := map[string]string{"COMPLETE": "COMPLETED", "FAIL": "FAILED", "UNKNOWN": "UNKNOWN", "WAIT": "CANCELLED", "QUEUED_CANCEL": "CANCELLED"}[mode]
			if view["status"] != expected {
				select {
				case err := <-c.errors:
					t.Log("worker error", err)
				default:
				}
				t.Fatalf("actual status %s expected %s %s", view["status"], expected, Bytes(view))
			}
			events, err := port.Events(context.Background(), f.token, HarnessEvents{ProjectID: f.project, TaskID: id, Cursor: "0", Limit: 500})
			if err != nil {
				t.Fatal("events", err)
			}
			eventData := events["data"].(map[string]any)
			if eventData["end"] != true {
				t.Fatal("terminal event page not ended", events)
			}
			reset, err := port.Events(context.Background(), f.token, HarnessEvents{ProjectID: f.project, TaskID: id, Cursor: "9223372036854775807", Limit: 10})
			if err != nil || reset["data"].(map[string]any)["reset"] != true {
				t.Fatal("cursor reset", reset, err)
			}
			var before int
			f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run'").Scan(&before)
			if err = c.Recover(context.Background()); err != nil {
				t.Fatal("no-launch recovery", err)
			}
			if err = c.Scan(context.Background()); err != nil {
				t.Fatal(err)
			}
			c.workers.Wait()
			var after int
			f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run'").Scan(&after)
			if before != after {
				t.Fatal("terminal or UNKNOWN re-launched")
			}
			t.Log(fmt.Sprintf("real same-DB chain %s, Runs=%d", expected, after))
		})
	}
}

// The terminal persistence fault is installed only after the real owned fake
// process has stopped/drained, so earlier events remain a valid control.
type harnessAtomicFaultDriver struct {
	rt.CodexDriver
	db       *sql.DB
	injected atomic.Bool
	starts   atomic.Int64
}
type harnessAtomicFaultHandle struct {
	rt.CodexHandle
	owner *harnessAtomicFaultDriver
}

func (d *harnessAtomicFaultDriver) Start(ctx context.Context, in rt.CodexLaunch, cb rt.CodexCallbacks) (rt.CodexHandle, error) {
	d.starts.Add(1)
	h, err := d.CodexDriver.Start(ctx, in, cb)
	if err != nil {
		return nil, err
	}
	return &harnessAtomicFaultHandle{CodexHandle: h, owner: d}, nil
}
func (h *harnessAtomicFaultHandle) Wait(ctx context.Context) (rt.CodexResult, error) {
	result, err := h.CodexHandle.Wait(ctx)
	if err != nil {
		return result, err
	}
	_, err = h.owner.db.Exec("CREATE TRIGGER harness_fixture_terminal_event_fault BEFORE INSERT ON domain_objects WHEN NEW.kind='EventEnvelope' BEGIN SELECT RAISE(ABORT,'author terminal persistence fixture fault'); END")
	if err == nil {
		h.owner.injected.Store(true)
	}
	return result, err
}
func TestHarnessUnknownTransitionAtomic(t *testing.T) {
	f, c, b := harnessFixture(t, harnessExecutable(t))
	driver := &harnessAtomicFaultDriver{CodexDriver: c.config.HarnessDriver, db: f.db}
	c.config.HarnessDriver = driver
	id, _ := harnessSubmitFixture(t, f, c, b, "UNKNOWN")
	if err := c.Scan(context.Background()); err != nil {
		t.Fatal(err)
	}
	c.workers.Wait()
	if !driver.injected.Load() || driver.starts.Load() != 1 {
		t.Fatal("fault control did not follow exactly one owned process")
	}
	view := harnessViewFixture(t, f, c, id)
	countTerminal := func() (int, Object) {
		page, err := c.HarnessV1().Events(context.Background(), f.token, HarnessEvents{ProjectID: f.project, TaskID: id, Cursor: "0", Limit: 500})
		if err != nil {
			t.Fatal(err)
		}
		data := page["data"].(map[string]any)
		n := 0
		for _, value := range Arr(data, "events") {
			if value.(map[string]any)["kind"] == "TASK_TERMINAL" {
				n++
			}
		}
		return n, data
	}
	n, page := countTerminal()
	if view["terminal"] != false || n != 0 || page["end"] != false {
		t.Fatal("failed terminal event partially committed UNKNOWN", view, page)
	}
	runRef := view["run"].(map[string]any)
	runID := Str(runRef, "run_id")
	epoch, err := HarnessDecimal(Str(runRef, "epoch"), true)
	if err != nil {
		t.Fatal(err)
	}
	var state, reason string
	if err = f.db.QueryRow("SELECT state,reason FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?", f.project, runID, epoch).Scan(&state, &reason); err != nil {
		t.Fatal(err)
	}
	if state != "STARTED" || reason != "" {
		t.Fatal("unknown state/reason escaped failed transaction", state, reason)
	}
	if err = c.Scan(context.Background()); err != nil {
		t.Fatal(err)
	}
	c.workers.Wait()
	var runs int
	if err = f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run'", f.project).Scan(&runs); err != nil {
		t.Fatal(err)
	}
	if runs != 1 || driver.starts.Load() != 1 {
		t.Fatal("terminal persistence failure re-dispatched the task")
	}
	// Explicit trusted reconciliation after fixing this fresh DB fault may
	// publish UNKNOWN; it grants no new execution or lease.
	if _, err = f.db.Exec("DROP TRIGGER harness_fixture_terminal_event_fault"); err != nil {
		t.Fatal(err)
	}
	if err = c.harnessUnknown(context.Background(), f.project, runID, epoch, "explicit fresh fixture reconciliation"); err != nil {
		t.Fatal(err)
	}
	view = harnessViewFixture(t, f, c, id)
	n, page = countTerminal()
	if view["status"] != "UNKNOWN" || view["terminal"] != true || n != 1 || page["end"] != true {
		t.Fatal("UNKNOWN did not commit with its final event", view, page)
	}
	if err = c.harnessUnknown(context.Background(), f.project, runID, epoch, "same epoch repeated reconciliation"); err != nil {
		t.Fatal(err)
	}
	n, _ = countTerminal()
	if n != 1 || driver.starts.Load() != 1 {
		t.Fatal("reconciliation duplicated terminal event or execution")
	}
}

//go:build windows

package domain

import (
	"context"
	"database/sql"
	"errors"
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

func TestHarnessRPCPolicySealIsDistinctFromHistoricalExec(t *testing.T) {
	rpc := rt.CodexRPCPolicyIdentity("sha256:binary")
	profile := map[string]any{
		"sandbox": rt.CodexRPCSandboxID, "command_id": rt.CodexRPCCommandID,
		"native_policy_revision": rpc.Revision, "windows_sandbox": rpc.WindowsSandbox,
		"permission_profile": rpc.PermissionProfile, "requested_config_sha256": rpc.RequestedConfigSHA256,
		"build_hash": rpc.BinarySHA256, "native_transport": rpc.Transport,
		"helper_contract": rpc.HelperContract,
	}
	if !harnessPolicyMatches(profile, rpc) {
		t.Fatal("exact RPC identity rejected")
	}
	profile["backend"] = "codex-cli-readonly-v1"
	profile["adapter"] = "codex-cli-harness-v1"
	profile["adapter_revision"] = "codex-cli-readonly-v1"
	profile["platform"] = "windows-amd64"
	profile["harness_owner"] = "owner"
	if err := validateRuntimeDispatchProfile(Object(profile)); err != nil {
		t.Fatal("sealed RPC profile rejected by dispatch admission", err)
	}
	profile["permission_profile"] = "researchos-readonly"
	if err := validateRuntimeDispatchProfile(Object(profile)); err == nil {
		t.Fatal("legacy permission profile accepted as RPC")
	}
	profile["permission_profile"] = rpc.PermissionProfile
	legacy := rt.CodexRequestedPolicyIdentity("sha256:binary")
	if harnessPolicyMatches(profile, legacy) {
		t.Fatal("historical exec identity upgraded to RPC")
	}
	for _, field := range []string{"sandbox", "command_id", "native_policy_revision", "native_transport", "helper_contract", "build_hash", "requested_config_sha256"} {
		altered := make(map[string]any, len(profile))
		for k, v := range profile {
			altered[k] = v
		}
		altered[field] = "stale"
		if harnessPolicyMatches(altered, rpc) {
			t.Fatalf("changed RPC %s accepted", field)
		}
	}
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
 import("os";"io";"fmt";"time";"encoding/json";"strings")
 func main(){args:=strings.Join(os.Args[1:],"|");if strings.Count(args,"windows.sandbox=\"mxc\"")!=1||!strings.Contains(args,"--ignore-user-config")||!strings.Contains(args,"approval_policy=\"never\""){os.Exit(74)};raw,_:=io.ReadAll(os.Stdin);var input map[string]json.RawMessage;var schema,prompt string;var source map[string]string
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
	driver, err := rt.NewCodexCLIForTrustedGoTest(rt.CodexCLIOptions{Executable: exe, Descriptor: rt.CodexDescriptor{Present: true, ExecutableHash: Digest(raw), AuthState: "LOGGED_IN", AuthKind: "other", ConfigurationControlled: true}}, rt.CodexReadinessFunc(func() rt.CodexReadiness {
		return rt.CodexReadiness{State: "READY", PolicyIdentity: rt.CodexRequestedPolicyIdentity(Digest(raw))}
	}))
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
	for _, mode := range []string{"COMPLETE", "FAIL", "UNKNOWN", "WAIT", "QUEUED_CANCEL", "AUTHORITY", "WORKSPACE", "WORKSPACE_REBIND"} {
		t.Run(mode, func(t *testing.T) {
			f, c, b := harnessFixture(t, exe)
			prompt := mode
			if mode == "QUEUED_CANCEL" || mode == "AUTHORITY" || mode == "WORKSPACE" || mode == "WORKSPACE_REBIND" {
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
				if mode == "WORKSPACE_REBIND" {
					sourceTx(t, f.db, func(tx *sql.Tx) error {
						b.RealPath = t.TempDir()
						b.Revision++
						return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
					})
				}
				if err = c.Scan(context.Background()); err != nil && mode != "AUTHORITY" {
					t.Fatal("same Scan", err)
				}
				if mode == "AUTHORITY" || mode == "WORKSPACE" || mode == "WORKSPACE_REBIND" {
					if mode == "WORKSPACE_REBIND" && harnessViewFixture(t, f, c, id)["status"] == "" {
						t.Fatal("historical Task unreadable")
					}
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

// The binding changes after runHarness captures the old source path and before
// its suspended child resumes. No output from that child may enter the Task.
type harnessRebindAtStartDriver struct {
	rt.CodexDriver
	db                    *sql.DB
	service               *Service
	binding               *WorkspaceBinding
	original, replacement string
	starts                atomic.Int64
}

func (d *harnessRebindAtStartDriver) Start(ctx context.Context, in rt.CodexLaunch, cb rt.CodexCallbacks) (rt.CodexHandle, error) {
	d.starts.Add(1)
	if in.Workspace != d.original {
		return nil, fmt.Errorf("driver source was not the admitted source")
	}
	tx, err := d.db.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	d.binding.RealPath = d.replacement
	d.binding.Revision++
	if err = d.service.putOpaque(ctx, tx, "", KindWorkspaceBinding, d.binding.AuthorizedRef, d.binding.record()); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return d.CodexDriver.Start(ctx, in, cb)
}
func TestHarnessSourceRebindBeforeResume(t *testing.T) {
	exe := harnessExecutable(t)
	f, c, b := harnessFixture(t, exe)
	id, _ := harnessSubmitFixture(t, f, c, b, "COMPLETE")
	driver := &harnessRebindAtStartDriver{CodexDriver: c.config.HarnessDriver, db: f.db, service: f.s,
		binding: b, original: b.RealPath, replacement: t.TempDir()}
	c.config.HarnessDriver = driver
	if err := c.Scan(context.Background()); err != nil {
		t.Fatal(err)
	}
	c.workers.Wait()
	view := harnessViewFixture(t, f, c, id)
	if driver.starts.Load() != 1 || view["status"] == "COMPLETED" || view["result"] != nil {
		t.Fatalf("rebound source resumed or fabricated result: starts=%d view=%s", driver.starts.Load(), Bytes(view))
	}
	events, err := c.HarnessV1().Events(context.Background(), f.token, HarnessEvents{ProjectID: f.project, TaskID: id, Cursor: "0", Limit: 500})
	if err != nil {
		t.Fatal(err)
	}
	for _, item := range Arr(events["data"].(map[string]any), "events") {
		row := item.(map[string]any)
		if row["kind"] == "ASSISTANT_DELTA" {
			t.Fatal("suspended rebound child emitted assistant content")
		}
	}
	if err = c.Scan(context.Background()); err != nil {
		t.Fatal(err)
	}
	c.workers.Wait()
	if driver.starts.Load() != 1 {
		t.Fatal("rebound dispatch relaunched")
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

// This driver is deliberately in-process. It exercises the real coordinator's
// two callbacks and database fences but never starts Native or writes a prompt.
type harnessRPCTurnFixtureDriver struct {
	descriptor    rt.CodexDescriptor
	snapshot      rt.CodexReadiness
	resumed       chan error
	proceed       chan struct{}
	launch        rt.CodexLaunch
	firstErr      error
	secondErr     error
	duplicate     bool
	tamperProcess bool
	starts        atomic.Int64
	turns         atomic.Int64
}

func (d *harnessRPCTurnFixtureDriver) Descriptor() rt.CodexDescriptor       { return d.descriptor }
func (d *harnessRPCTurnFixtureDriver) ReadinessSnapshot() rt.CodexReadiness { return d.snapshot }
func (d *harnessRPCTurnFixtureDriver) Start(ctx context.Context, in rt.CodexLaunch, cb rt.CodexCallbacks) (rt.CodexHandle, error) {
	d.starts.Add(1)
	d.launch = in
	if err := os.MkdirAll(in.Directory, 0700); err != nil {
		return nil, err
	}
	process := rt.CodexIdentity{PID: 42, Created: 12345, Job: "trusted-go-only-job"}
	err := cb.BeforeResume(process)
	d.resumed <- err
	if err != nil {
		return nil, err
	}
	<-d.proceed
	evidence := rt.CodexTurnEvidence{PolicyIdentity: rt.CodexRPCPolicyIdentity(d.descriptor.ExecutableHash),
		RenderedConfigSHA256: "sha256:trusted-rendered", SourceBindingHash: in.SourceBindingHash,
		ProfileNonce: "trusted-go-nonce", ThreadID: "trusted-go-thread", TaskID: in.TaskID,
		RunID: in.RunID, Epoch: in.Epoch, Process: process, CaptureBytes: 12}
	if d.tamperProcess {
		evidence.Process.Created++
	}
	d.firstErr = cb.BeforeModelTurn(evidence)
	if d.firstErr == nil {
		d.turns.Add(1)
	}
	if d.duplicate {
		d.secondErr = cb.BeforeModelTurn(evidence)
	}
	return nil, errors.New("trusted Go fixture stops before model prompt")
}

func harnessRPCTurnFixture(t *testing.T) (*fixture, *RuntimeCoordinator, *WorkspaceBinding, *harnessRPCTurnFixtureDriver) {
	t.Helper()
	f := contextFixtureFrom(setupWithConstructor(t, NewCurrentMu))
	b := &WorkspaceBinding{AuthorizedRef: "workspace-harness", DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "fixture-client", HostPrincipalRef: "fixture-host", CreatedAt: Now()}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
	})
	d := &harnessRPCTurnFixtureDriver{descriptor: rt.CodexDescriptor{Present: true, Version: "0.166.0", ExecutableHash: "sha256:trusted-go-only", AuthState: "LOGGED_IN", AuthKind: "chatgpt", ConfigurationControlled: true, NativeTransport: rt.CodexRPCTransport}, resumed: make(chan error, 1), proceed: make(chan struct{})}
	d.snapshot = rt.CodexReadiness{State: "PREPARATION_READY", PolicyIdentity: rt.CodexRPCPolicyIdentity(d.descriptor.ExecutableHash)}
	var seq int
	var name, dbpath string
	if err := f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbpath); err != nil {
		t.Fatal(err)
	}
	c, err := f.s.NewRuntimeCoordinator(context.Background(), RuntimeCoordinatorConfig{DataRoot: filepath.Dir(dbpath), APIURL: "http://127.0.0.1:1", WorkspaceAuthority: clientWorkspaceAuthority{}, HarnessAuthority: &harnessAuthorityFixture{principal: f.owner}, HarnessDriver: d})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := c.Close(); err != nil {
			t.Error(err)
		}
	})
	return f, c, b, d
}

// Replace the live runtime binding with a newly sealed, individually valid
// profile. The original Run's dispatch snapshot must still reject the turn.
func harnessRPCRebindSealedProfile(t *testing.T, f *fixture, d *harnessRPCTurnFixtureDriver) {
	t.Helper()
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		run, err := load(tx, f.project, "Run", d.launch.RunID)
		if err != nil {
			return err
		}
		runtime, err := load(tx, f.project, "RuntimeRegistration", Str(run, "runtime_id"))
		if err != nil {
			return err
		}
		prior, artifact, err := f.s.currentRuntimeBinding(tx, f.project, runtime)
		if err != nil {
			return err
		}
		profile, err := runtimeProfileBody(tx, f.project, artifact)
		if err != nil {
			return err
		}
		profile["consent_expires_at"] = time.Now().UTC().Add(23 * time.Hour).Format(time.RFC3339Nano)
		if !harnessPolicyMatches(profile, rt.CodexRPCPolicyIdentity(d.descriptor.ExecutableHash)) {
			return errors.New("replacement profile lost canonical RPC seal")
		}
		owner, err := authenticate(tx, f.token)
		if err != nil {
			return err
		}
		newArtifact, err := f.s.sealRuntimeSetupProfile(tx, owner, f.project, profile)
		if err != nil {
			return err
		}
		newRef := Ref(newArtifact, "Artifact")
		if Hash(newRef) == Hash(prior) {
			return errors.New("replacement binding did not change")
		}
		_, err = tx.Exec("UPDATE runtime_bindings SET profile_ref=?,profile_hash=? WHERE project=? AND runtime=?", string(Bytes(newRef)), Hash(newRef), f.project, runtime["id"])
		if err != nil {
			return err
		}
		current, _, err := f.s.currentRuntimeBinding(tx, f.project, runtime)
		if err != nil || Hash(current) != Hash(newRef) {
			return errors.New("replacement profile is not the live valid binding")
		}
		return nil
	})
}

func TestHarnessRPCTurnSecondFence(t *testing.T) {
	for _, mode := range []string{"one_turn", "duplicate", "owner", "source_rebind", "source_revision", "policy_readiness", "sealed_binding", "auth_metadata", "process_identity", "lease_epoch", "cancel", "artifact_fault"} {
		t.Run(mode, func(t *testing.T) {
			f, c, b, d := harnessRPCTurnFixture(t)
			caps, err := c.HarnessV1().Capabilities(context.Background(), f.token)
			if err != nil {
				t.Fatal(err)
			}
			data := caps["data"].(map[string]any)
			verification := data["verification"].(map[string]any)
			if data["can_submit"] != true || verification["execution"] != "UNVERIFIED" || verification["workspace_read_scope"] != "UNVERIFIED" || verification["cancellation"] != "UNVERIFIED" || data["security_scope"].(map[string]any)["enforcement_verified"] != false {
				t.Fatal("preparation misrepresented as verified execution", caps)
			}
			id, _ := harnessSubmitFixture(t, f, c, b, "trusted Go callback fixture only")
			if mode == "duplicate" || mode == "artifact_fault" {
				d.duplicate = true
			}
			if mode == "process_identity" {
				d.tamperProcess = true
			}
			if err := c.Scan(context.Background()); err != nil {
				t.Fatal(err)
			}
			select {
			case err := <-d.resumed:
				if err != nil {
					t.Fatal("first fence rejected fixture", err)
				}
			case <-time.After(10 * time.Second):
				close(d.proceed)
				c.workers.Wait()
				t.Fatal("first fence did not arrive")
			}
			released := false
			defer func() {
				if !released {
					close(d.proceed)
					c.workers.Wait()
				}
			}()
			switch mode {
			case "owner":
				c.config.HarnessAuthority = &harnessAuthorityFixture{principal: "foreign"}
			case "source_rebind", "source_revision":
				sourceTx(t, f.db, func(tx *sql.Tx) error {
					if mode == "source_rebind" {
						b.RealPath = t.TempDir()
					}
					b.Revision++
					return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
				})
			case "policy_readiness":
				d.snapshot.PolicyIdentity = rt.CodexRPCPolicyIdentity("sha256:stale-binary")
			case "sealed_binding":
				harnessRPCRebindSealedProfile(t, f, d)
			case "auth_metadata":
				d.descriptor.AuthState = "LOGGED_OUT"
			case "lease_epoch":
				sourceTx(t, f.db, func(tx *sql.Tx) error {
					run, err := load(tx, f.project, "Run", d.launch.RunID)
					if err != nil {
						return err
					}
					run["lease_epoch"] = int64(99)
					if err = bump(run); err != nil {
						return err
					}
					return f.s.put(tx, "Run", run)
				})
			case "cancel":
				view := harnessViewFixture(t, f, c, id)
				run := view["run"].(map[string]any)
				runID, epoch := Str(run, "run_id"), Str(run, "epoch")
				if _, err := c.HarnessV1().Cancel(context.Background(), f.token, f.project, id, HarnessCancel{RequestID: "cancel-at-second-fence", ExpectedTaskRevision: Str(view, "task_revision"), ExpectedRunID: &runID, ExpectedEpoch: &epoch}); err != nil {
					t.Fatal(err)
				}
			case "artifact_fault":
				if _, err := f.db.Exec("CREATE TRIGGER harness_turn_artifact_fault BEFORE INSERT ON domain_objects WHEN NEW.kind='Artifact' BEGIN SELECT RAISE(ABORT,'trusted turn artifact fault'); END"); err != nil {
					t.Fatal(err)
				}
			}
			close(d.proceed)
			released = true
			c.workers.Wait()
			if d.starts.Load() != 1 {
				t.Fatal("fixture started more than one Run")
			}
			marker := filepath.Join(d.launch.Directory, "native-turn-authorization.json")
			_, markerErr := os.Stat(marker)
			wantMarker := mode == "one_turn" || mode == "duplicate" || mode == "artifact_fault"
			if (markerErr == nil) != wantMarker {
				t.Fatalf("turn marker mismatch for %s: %v", mode, markerErr)
			}
			if mode == "one_turn" || mode == "duplicate" {
				if d.firstErr != nil || d.turns.Load() != 1 {
					t.Fatal("one trusted callback failed", d.firstErr)
				}
				var audits int
				if err := f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE sealed=1 AND CAST(bytes AS TEXT) LIKE '%researchos.native-turn-authorization.v1%'").Scan(&audits); err != nil || audits != 1 {
					t.Fatal("sanitized turn LOG not durable once", audits, err)
				}
				if mode == "duplicate" && !errors.Is(d.secondErr, os.ErrExist) {
					t.Fatal("duplicate turn did not fail at exclusive marker", d.secondErr)
				}
			} else if d.firstErr == nil || d.turns.Load() != 0 {
				t.Fatal("stale or failed second fence granted turn", mode)
			}
			if mode == "artifact_fault" {
				if _, err := f.db.Exec("DROP TRIGGER harness_turn_artifact_fault"); err != nil {
					t.Fatal(err)
				}
				if d.firstErr == nil {
					t.Fatal("artifact failure allowed turn")
				}
				if !errors.Is(d.secondErr, os.ErrExist) {
					t.Fatal("failed artifact transaction reused consumed marker", d.secondErr)
				}
				var audits int
				if err := f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE sealed=1 AND CAST(bytes AS TEXT) LIKE '%researchos.native-turn-authorization.v1%'").Scan(&audits); err != nil || audits != 0 {
					t.Fatal("rolled-back artifact escaped failed turn", audits, err)
				}
			}
			if view := harnessViewFixture(t, f, c, id); view["result"] != nil {
				t.Fatal("fixture produced a model result")
			}
			if err := c.Scan(context.Background()); err != nil && (mode == "one_turn" || mode == "duplicate") {
				t.Fatal(err)
			}
			c.workers.Wait()
			if d.starts.Load() != 1 {
				t.Fatal("consumed Run relaunched")
			}
		})
	}
}

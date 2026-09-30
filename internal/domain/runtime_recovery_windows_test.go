//go:build windows

package domain

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"researchos.local/research-os/internal/store"
)

type coordinatorProcessInput struct {
	Config   RuntimeCoordinatorConfig `json:"config"`
	Database string                   `json:"database"`
	Run      Object                   `json:"run"`
	Lease    string                   `json:"lease"`
}

func TestRuntimeCoordinatorCheckpointCrashRecovery(t *testing.T) {
	c, route, qualification := coordinatorFixtureOptions(t, false, true)
	c, _, r, _ := nativeNormalFrom(t, c, route, qualification)
	f := r.f
	var database, name string
	var sequence int
	if e := f.db.QueryRow("PRAGMA database_list").Scan(&sequence, &name, &database); e != nil {
		t.Fatal(e)
	}
	path := filepath.Join(filepath.Dir(database), "checkpoint-control.json")
	raw, e := json.Marshal(coordinatorProcessInput{Config: c.config, Database: database})
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(path, raw, 0600); e != nil {
		t.Fatal(e)
	}
	c.Close()
	first := runCoordinatorProcess(t, path, "checkpoint_durable", 86)
	task := f.read("tasks", Str(r.task, "id"))
	run := f.read("runs", Str(task, "active_run_id"))
	expired := time.Now().Add(-time.Hour).UTC().Format(time.RFC3339Nano)
	if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.lease_expires_at',?) WHERE project=? AND kind='Run' AND id=?", expired, f.project, run["id"]); e != nil {
		t.Fatal(e)
	}
	second := runCoordinatorProcess(t, path, "recover", 0)
	recovered := f.read("runs", Str(run, "id"))
	if recovered["lease_expires_at"] != expired || Str(recovered, "checkpoint_artifact_id") == "" || Hash(recovered["lease_epoch"]) != Hash(run["lease_epoch"]) || runTerminal(recovered) {
		t.Fatalf("checkpoint recovery changed authority or lost data: %s", Bytes(recovered))
	}
	checkpoint := f.read("artifacts", Str(recovered, "checkpoint_artifact_id"))
	if checkpoint["kind"] != "CHECKPOINT" || checkpoint["content_hash"] != Digest([]byte(`{"cursor":"durable-fixture-position"}`)) {
		t.Fatal("checkpoint bytes changed")
	}
	if _, e = f.s.ResumeCheckpoint(context.Background(), c.config.SchedulerToken, f.project, Str(run, "id"), ID(), int64(recovered["revision"].(float64))); e == nil {
		t.Fatal("incomplete process/stream facts allowed resume")
	}
	t.Logf("RUNTIME_CHECKPOINT_CRASH original_control=%d recovery_control=%d checkpoint_recovered=true lease_extended=false incomplete_terminal_resume_blocked=true", first, second)
}

func TestRuntimeCoordinatorControlProcess(t *testing.T) {
	index := -1
	for i, arg := range os.Args {
		if arg == "--runtime-control" {
			index = i
			break
		}
	}
	if index < 0 {
		return
	}
	raw, e := os.ReadFile(os.Args[index+1])
	if e != nil {
		t.Fatal(e)
	}
	var input coordinatorProcessInput
	if e = json.Unmarshal(raw, &input); e != nil {
		t.Fatal(e)
	}
	phase := os.Args[index+2]
	db, e := store.Open(input.Database)
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	service, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	crash := func(name string) { fmt.Println("RUNTIME_CONTROL_CRASH " + name); os.Stdout.Sync(); os.Exit(86) }
	handler := service.Handler()
	server, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(404)
			return
		}
		lost := r.Method == "POST" && ((phase == "seal_ack_lost" && strings.HasSuffix(r.URL.Path, "/artifacts")) || (phase == "report_ack_lost" && strings.HasSuffix(r.URL.Path, "/report")))
		if lost {
			record := httptest.NewRecorder()
			handler.ServeHTTP(record, r)
			if record.Code >= 200 && record.Code < 300 {
				crash(phase)
			}
			for name, values := range record.Header() {
				w.Header()[name] = values
			}
			w.WriteHeader(record.Code)
			io.Copy(w, record.Body)
			return
		}
		handler.ServeHTTP(w, r)
	}))
	defer server.Close()
	input.Config.APIURL = server.URL
	c, e := service.NewRuntimeCoordinator(context.Background(), input.Config)
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	if phase == "recover" {
		if e = c.Recover(context.Background()); e != nil {
			t.Fatal(e)
		}
		if e = c.Scan(context.Background()); e != nil {
			t.Fatal(e)
		}
		c.workers.Wait()
		fmt.Println("RUNTIME_CONTROL_RECOVERY_COMPLETE")
		return
	}
	c.boundaryHook = func(name string, _ Object) {
		if phase == name {
			crash(name)
		}
	}
	if input.Run == nil {
		e = c.Scan(context.Background())
		c.workers.Wait()
		select {
		case workerError := <-c.errors:
			e = workerError
		default:
		}
	} else {
		e = c.RunAdmitted(context.Background(), input.Config.Routes[0], input.Run, input.Lease)
	}
	if e != nil {
		t.Fatal(e)
	}
	t.Fatalf("requested crash boundary %s not reached", phase)
}

func TestRuntimeCoordinatorEffectCrashRecovery(t *testing.T) {
	for _, phase := range []string{"effect_prepared", "effect_started", "provider_responded", "effect_receipt_durable"} {
		t.Run(phase, func(t *testing.T) {
			c, route, r, _ := nativeNormalFixture(t, true)
			f := r.f
			var calls atomic.Int32
			provider, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, request *http.Request) {
				if request.URL.Path == "/__researchos_fixture_readiness__" {
					w.WriteHeader(404)
					return
				}
				calls.Add(1)
				var body Object
				if e := json.NewDecoder(request.Body).Decode(&body); e != nil {
					w.WriteHeader(400)
					return
				}
				json.NewEncoder(w).Encode(Object{"key": body["key"], "epoch": body["epoch"], "run_id": body["run_id"], "receipt_id": "late-provider-receipt", "state": "CONFIRMED", "actual_cost": dollars("1.25"), "payload": Object{"echo": "approved"}})
			}))
			defer provider.Close()
			c.config.Providers = []RuntimeProviderRoute{{ID: "fixture-echo", ProjectID: f.project, RuntimeID: route.RuntimeID, Purpose: "json-verification", Capability: "fixture.echo", CredentialRevision: "test-v1", Endpoint: provider.URL, UpperBound: dollars("1"), MeasurementMode: "FIXTURE"}}
			var dbPath, name string
			var seq int
			if e := f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbPath); e != nil {
				t.Fatal(e)
			}
			input := coordinatorProcessInput{Config: c.config, Database: dbPath}
			path := filepath.Join(filepath.Dir(dbPath), "control-fixture.json")
			raw, e := json.Marshal(input)
			if e != nil {
				t.Fatal(e)
			}
			if e = os.WriteFile(path, raw, 0600); e != nil {
				t.Fatal(e)
			}
			if e = c.Close(); e != nil {
				t.Fatal(e)
			}
			runCoordinatorProcess(t, path, phase, 86)
			task := f.read("tasks", Str(r.task, "id"))
			run := f.read("runs", Str(task, "active_run_id"))
			if phase == "effect_receipt_durable" {
				// Controlled stale-callback fault: no second process is launched. A
				// late old-epoch receipt must account cost without touching epoch 2.
				if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.lease_epoch',2) WHERE project=? AND kind='Run' AND id=?", f.project, run["id"]); e != nil {
					t.Fatal(e)
				}
			}
			runCoordinatorProcess(t, path, "recover", 0)
			runCoordinatorProcess(t, path, "recover", 0)
			wantCalls := int32(0)
			wantState := "UNKNOWN"
			if phase == "effect_prepared" {
				wantState = "PREPARED"
			}
			if phase == "provider_responded" {
				wantCalls = 1
			}
			if phase == "effect_receipt_durable" {
				wantCalls = 1
				wantState = "CONFIRMED"
			}
			var body string
			if e = f.db.QueryRow("SELECT body FROM resource_effects WHERE project=? AND run=? AND effect_key='single-fixture-effect' ORDER BY sequence DESC LIMIT 1", f.project, run["id"]).Scan(&body); e != nil {
				t.Fatal(e)
			}
			effect, e := Decode([]byte(body))
			if e != nil {
				t.Fatal(e)
			}
			if calls.Load() != wantCalls || effect["state"] != wantState || Hash(effect["epoch"]) != Hash(1) {
				t.Fatalf("unknown effect resent or moved: calls=%d effect=%s", calls.Load(), body)
			}
			var actual int
			if e = f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.operation')='RECONCILE'", f.project, run["id"]).Scan(&actual); e != nil {
				t.Fatal(e)
			}
			if phase == "effect_receipt_durable" {
				if actual != 1 || Hash(f.read("runs", Str(run, "id"))["lease_epoch"]) != Hash(2) {
					t.Fatal("late cost altered current epoch or duplicated reconciliation")
				}
			} else if actual != 0 {
				t.Fatal("unknown effect invented actual cost")
			}
			t.Logf("RUNTIME_EFFECT_CRASH phase=%s provider_calls=%d state=%s original_epoch=1 actual_receipts=%d repeated_recovery_no_retry=true", phase, calls.Load(), effect["state"], actual)
		})
	}
}

func runCoordinatorProcess(t *testing.T, path, phase string, want int) int {
	t.Helper()
	exe, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	command := exec.Command(exe, "-test.run=^TestRuntimeCoordinatorControlProcess$", "--", "--runtime-control", path, phase)
	output, e := command.CombinedOutput()
	code := 0
	if e != nil {
		exit, ok := e.(*exec.ExitError)
		if !ok {
			t.Fatal(e)
		}
		code = exit.ExitCode()
	}
	if code != want {
		t.Fatalf("control phase=%s exit=%d want=%d raw=%s", phase, code, want, output)
	}
	t.Logf("RUNTIME_CONTROL_PROCESS phase=%s pid=%d exit=%d output=%s", phase, command.Process.Pid, code, strings.TrimSpace(string(output)))
	return command.Process.Pid
}

func TestRuntimeCoordinatorCrashRecovery(t *testing.T) {
	for _, phase := range []string{"before_launch_fence", "dispatch_started", "suspended_identity", "native_started", "terminal_durable", "artifact_sealed", "seal_ack_lost", "report_ack_lost", "reported"} {
		t.Run(phase, func(t *testing.T) {
			c, _, r := coordinatorFixture(t)
			f := r.f
			var dbPath, name string
			var seq int
			if e := f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbPath); e != nil {
				t.Fatal(e)
			}
			input := coordinatorProcessInput{Config: c.config, Database: dbPath, Run: r.run, Lease: r.lease}
			path := filepath.Join(filepath.Dir(dbPath), "control-fixture.json")
			raw, e := json.Marshal(input)
			if e != nil {
				t.Fatal(e)
			}
			if e = os.WriteFile(path, raw, 0600); e != nil {
				t.Fatal(e)
			}
			if e = c.Close(); e != nil {
				t.Fatal(e)
			}
			first := runCoordinatorProcess(t, path, phase, 86)
			expired := time.Now().Add(-time.Hour).UTC().Format(time.RFC3339Nano)
			if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.lease_expires_at',?) WHERE project=? AND kind='Run' AND id=?", expired, f.project, r.run["id"]); e != nil {
				t.Fatal(e)
			}
			second := runCoordinatorProcess(t, path, "recover", 0)
			recovered := f.read("runs", Str(r.run, "id"))
			task := f.read("tasks", Str(r.task, "id"))
			if recovered["lease_expires_at"] != expired || Hash(recovered["lease_epoch"]) != Hash(r.run["lease_epoch"]) {
				t.Fatal("recovery renewed execution authority")
			}
			terminal := phase == "terminal_durable" || phase == "artifact_sealed" || phase == "seal_ack_lost" || phase == "report_ack_lost" || phase == "reported"
			var state string
			if e = f.db.QueryRow("SELECT state FROM runtime_dispatches WHERE run=?", r.run["id"]).Scan(&state); e != nil {
				t.Fatal(e)
			}
			if terminal {
				if recovered["status"] != "SETTLED" || task["status"] != "EXECUTION_REPORTED" || state != "OBSERVED" {
					t.Fatalf("complete terminal facts not recovered: run=%s task=%s dispatch=%s", recovered["status"], task["status"], state)
				}
			} else if state != "UNKNOWN" || runTerminal(recovered) {
				t.Fatalf("incomplete dispatch promoted: state=%s run=%s", state, recovered["status"])
			}
			var runs, dispatches int
			f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?", f.project, r.task["id"]).Scan(&runs)
			f.db.QueryRow("SELECT count(*) FROM runtime_dispatches WHERE project=? AND run=?", f.project, r.run["id"]).Scan(&dispatches)
			if runs != 1 || dispatches != 1 {
				t.Fatalf("recovery forked business identity: runs=%d dispatches=%d", runs, dispatches)
			}
			t.Logf("RUNTIME_CRASH_RECOVERY phase=%s original_control=%d recovery_control=%d dispatch=%s terminal_recovered=%v no_lease_extension=true no_relaunch=true", phase, first, second, state, terminal)
		})
	}
}

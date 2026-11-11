package domain

import (
	"bufio"
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"testing"
	"time"
)

func TestW12ProcessHelper(t *testing.T) {
	mode := os.Getenv("W12_PROCESS_MODE")
	if mode == "" {
		return
	}
	db, e := store.Open(os.Getenv("W12_PROCESS_DB"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	s, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	project, run, key, token := os.Getenv("W12_PROJECT"), os.Getenv("W12_RUN"), os.Getenv("W12_KEY"), os.Getenv("W12_TOKEN")
	if mode == "crash" || mode == "resume" {
		fixtureHTTPReady(t, http.DefaultClient, os.Getenv("W12_PROVIDER")+"?key=__readiness__")
	}
	if mode == "crash" {
		effect, e := s.BeginEffect(context.Background(), token, project, run, key)
		if e != nil {
			t.Fatal(e)
		}
		response, e := http.Post(os.Getenv("W12_PROVIDER"), "application/json", bytes.NewReader(Bytes(effect)))
		if e != nil {
			t.Fatal(e)
		}
		raw, e := io.ReadAll(response.Body)
		response.Body.Close()
		if e != nil || response.StatusCode != 200 {
			t.Fatalf("provider %d %s %v", response.StatusCode, raw, e)
		}
		fmt.Println("EXTERNAL_COMMITTED_BEFORE_LOCAL_ACK")
		time.Sleep(time.Minute)
		t.Fatal("parent failed to kill child")
	}
	if mode == "resume" {
		response, e := http.Get(os.Getenv("W12_PROVIDER") + "?key=" + key)
		if e != nil {
			t.Fatal(e)
		}
		raw, e := io.ReadAll(response.Body)
		response.Body.Close()
		if e != nil || response.StatusCode != 200 {
			t.Fatal("provider reconciliation unavailable")
		}
		receipt, e := Decode(raw)
		if e != nil {
			t.Fatal(e)
		}
		if e = s.ObserveEffect(context.Background(), project, run, key, "CONFIRMED", receipt); e != nil {
			t.Fatal(e)
		}
		var body string
		if e = db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND id=?", project, run).Scan(&body); e != nil {
			t.Fatal(e)
		}
		r, _ := Decode([]byte(body))
		revision, _ := Num(r, "revision")
		resumeKey := "persisted-resume-key-0001"
		result, e := s.ResumeCheckpoint(context.Background(), token, project, run, resumeKey, revision)
		if e != nil {
			t.Fatal(e)
		}
		replay, e := s.ResumeCheckpoint(context.Background(), token, project, run, resumeKey, revision)
		if e != nil || Hash(result) != Hash(replay) {
			t.Fatal("resume replay diverged", e)
		}
		if e = os.WriteFile(os.Getenv("W12_RESULT"), Bytes(result), 0600); e != nil {
			t.Fatal(e)
		}
	}
}

func TestW12CrashAndResume(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	r := o.claim(o.task("durable-operation", Empty(), Empty()))
	executorToken := f.token
	checkpoint := resourceCheckpoint(r, Object{"next_step": "query original provider key, never reissue unknown effect", "project_id": f.project, "goal_id": o.goal["id"], "task_id": r.task["id"], "run_id": r.run["id"]})
	before := r.run
	f.token = o.owner
	// The ResearchCycle envelope is validated fixture setup; W08 scheduling is not
	// exercised or claimed by this recovery contract test.
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	profile, e := singleton(tx, f.project, "ProjectProfile")
	if e != nil {
		t.Fatal(e)
	}
	cycle := Merge(Base(f.project), Object{"profile_ref": Ref(profile, "ProjectProfile"), "status": "RUNNING", "trigger": "RECOVERY", "window_from": Now(), "window_to": Now(), "source_coverage": []any{Object{"source_id": "local-fixture-source", "required": true, "status": "PARTIAL", "requested_from": Now(), "requested_to": Now(), "observed_from": nil, "observed_to": nil, "record_count": 0, "gap_reason": "crash test setup", "cursor_id": nil}}, "candidate_evidence_ids": Empty(), "required_experiment_ids": Empty(), "decision_ids": Empty(), "follow_up_task_ids": []any{r.task["id"]}, "checkpoint_artifact_id": checkpoint["id"], "outcome_summary": nil, "started_at": Now(), "closed_at": nil})
	if e = f.s.put(tx, "ResearchCycle", cycle); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	policy := f.expect(200, "GET", f.path("/goals/"+Str(o.goal, "id")+"/budget-policy"), "", "", nil)
	key := "stable-provider-operation-key"
	cost := budgetRequest(r, Str(policy, "id"), "UNKNOWN", key, nil, "UNKNOWN", nil)
	intent, e := f.s.PrepareEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key, Object{"effect": "one externally committed fixture record"}, cost)
	if e != nil {
		t.Fatal(e)
	}
	resourceSnapshot(f, "before-crash.json")
	external, e := store.Open(filepath.Join(t.TempDir(), "external-fixture.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer external.Close()
	if _, e = external.Exec("CREATE TABLE effects(key TEXT PRIMARY KEY, request_hash TEXT NOT NULL, receipt TEXT NOT NULL)"); e != nil {
		t.Fatal(e)
	}
	provider, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, q *http.Request) {
		if q.Method == "POST" {
			raw, _ := io.ReadAll(q.Body)
			b, _ := Decode(raw)
			receipt := Object{"provider_key": b["key"], "external_effect_id": ID(), "state": "APPLIED", "amount": nil, "cost_known": false}
			_, err := external.Exec("INSERT INTO effects(key,request_hash,receipt) VALUES(?,?,?) ON CONFLICT(key) DO NOTHING", b["key"], b["request_hash"], string(Bytes(receipt)))
			if err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			var saved, hash string
			external.QueryRow("SELECT receipt,request_hash FROM effects WHERE key=?", b["key"]).Scan(&saved, &hash)
			if hash != b["request_hash"] {
				http.Error(w, "key mismatch", 409)
				return
			}
			w.Write([]byte(saved))
			return
		}
		var receipt string
		if err := external.QueryRow("SELECT receipt FROM effects WHERE key=?", q.URL.Query().Get("key")).Scan(&receipt); err != nil {
			http.Error(w, "unknown", 404)
			return
		}
		w.Write([]byte(receipt))
	}))
	defer provider.Close()
	var index int
	var dbName, dbPath string
	if e = f.db.QueryRow("PRAGMA database_list").Scan(&index, &dbName, &dbPath); e != nil {
		t.Fatal(e)
	}
	exe, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	resultPath := filepath.Join(t.TempDir(), "resume.json")
	env := append(os.Environ(), "W12_PROCESS_DB="+dbPath, "W12_PROJECT="+f.project, "W12_RUN="+Str(r.run, "id"), "W12_KEY="+key, "W12_TOKEN="+o.owner, "W12_PROVIDER="+provider.URL, "W12_RESULT="+resultPath)
	child := exec.Command(exe, "-test.run=^TestW12ProcessHelper$")
	child.Env = append(env, "W12_PROCESS_MODE=crash")
	stdout, e := child.StdoutPipe()
	if e != nil {
		t.Fatal(e)
	}
	var stderr bytes.Buffer
	child.Stderr = &stderr
	if e = child.Start(); e != nil {
		t.Fatal(e)
	}
	signal := make(chan bool, 1)
	var childOutput bytes.Buffer
	go func() {
		scan := bufio.NewScanner(stdout)
		for scan.Scan() {
			line := scan.Text()
			childOutput.WriteString(line + "\n")
			if line == "EXTERNAL_COMMITTED_BEFORE_LOCAL_ACK" {
				signal <- true
				return
			}
		}
		signal <- false
	}()
	select {
	case ready := <-signal:
		if !ready {
			child.Wait()
			t.Fatalf("child failed %s %s", childOutput.String(), stderr.String())
		}
	case <-time.After(15 * time.Second):
		child.Process.Kill()
		child.Wait()
		t.Fatal("child checkpoint timeout")
	}
	if e = child.Process.Kill(); e != nil {
		t.Fatal(e)
	}
	waitError := child.Wait()
	if waitError == nil {
		t.Fatal("expected forced termination")
	}
	resourceEvidence(t, "crash-process.json", Object{"cwd": "internal/domain", "argv": child.Args, "pid": child.Process.Pid, "exit_code": child.ProcessState.ExitCode(), "stdout": childOutput.String(), "stderr": stderr.String(), "fault_point": "after_external_effect_before_local_ack", "mode": "NATIVE_PROCESS_WITH_LOCAL_SERVICE_FIXTURE"})
	if _, e = f.s.BeginEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key); e == nil {
		t.Fatal("blind retry allowed")
	}
	if e = f.s.ObserveEffect(context.Background(), f.project, Str(r.run, "id"), key, "UNKNOWN", Object{"reason": "local process killed before ACK", "pid": child.Process.Pid}); e != nil {
		t.Fatal(e)
	}
	if _, e = f.s.BeginEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key); e == nil {
		t.Fatal("unknown blindly retried")
	}
	obs := r.observation("LOST", false)
	obs["native_process_exit_code"] = child.ProcessState.ExitCode()
	r.observe(obs)
	revision, _ := Num(r.run, "revision")
	if _, e = f.s.ResumeCheckpoint(context.Background(), o.owner, f.project, Str(r.run, "id"), "blocked-resume-key-0001", revision); e == nil {
		t.Fatal("unreconciled resume allowed")
	}
	resourceSnapshot(f, "after-crash-before-reconcile.json")
	if e = f.db.Close(); e != nil {
		t.Fatal(e)
	}
	resumed := exec.Command(exe, "-test.run=^TestW12ProcessHelper$")
	resumed.Env = append(env, "W12_PROCESS_MODE=resume")
	raw, e := resumed.CombinedOutput()
	resourceEvidence(t, "resume-process.json", Object{"argv": resumed.Args, "pid": resumed.Process.Pid, "exit_code": resumed.ProcessState.ExitCode(), "stdout": string(raw)})
	if e != nil {
		t.Fatalf("resume subprocess %v %s", e, raw)
	}
	f.db, e = store.Open(dbPath)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { f.db.Close() })
	f.s, e = New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	resourceHTTP(f)
	raw, e = os.ReadFile(resultPath)
	if e != nil {
		t.Fatal(e)
	}
	result, e := Decode(raw)
	if e != nil {
		t.Fatal(e)
	}
	r.run = result["run"].(map[string]any)
	r.lease = Str(result, "lease_token")
	f.token = executorToken
	// Old callbacks are fenced; the carried checkpoint remains readable under
	// the new epoch and cannot be converted into a newly accepted result.
	f.expect(409, "POST", f.path("/runs/"+Str(r.run, "id")+"/heartbeat"), ID(), testTag(r.run), Object{"lease_token": "old-token", "lease_epoch": before["lease_epoch"], "external_run_id": "old", "checkpoint_artifact_id": nil})
	f.expect(200, "GET", f.path("/artifacts/"+Str(checkpoint, "id")), "", "", nil)
	hb := r.heartbeat()
	hb["checkpoint_artifact_id"] = checkpoint["id"]
	r.call("/heartbeat", hb, 200)
	f.token = o.owner
	var effectCount int
	external.QueryRow("SELECT count(*) FROM effects").Scan(&effectCount)
	var afterCycleRaw string
	f.db.QueryRow("SELECT body FROM domain_objects WHERE kind='ResearchCycle' AND id=?", cycle["id"]).Scan(&afterCycleRaw)
	afterCycle, _ := Decode([]byte(afterCycleRaw))
	task := f.read("tasks", Str(r.task, "id"))
	goal := f.read("goals", Str(o.goal, "id"))
	resourcesAssert(t, "C11-01", true, r.run["id"] == before["id"] && r.run["task_id"] == before["task_id"] && task["goal_id"] == goal["id"] && Hash(cycle) == Hash(afterCycle) && result["context"].(map[string]any)["id"] != before["context_bundle_id"], Object{"before": before, "after": r.run, "cycle_before": cycle, "cycle_after": afterCycle, "current_context": result["context"]})
	resourcesAssert(t, "C11-02", 1, effectCount, Object{"original_intent": intent, "blind_retry": "BLOCKED", "unknown_resume": "BLOCKED", "reconciliation": "QUERIED_PROVIDER_BEFORE_RESUME", "same_provider_key": key})
	resourcesAssert(t, "C13-02", []any{"ACTIVE", "RUNNING", true}, []any{goal["status"], task["status"], task["active_run_id"] == before["id"]}, Object{"old_session_pid": child.Process.Pid, "new_session_pid": resumed.Process.Pid, "context": result["context"]})
	late := budgetRequest(r, Str(policy, "id"), "RECONCILE", key, dollars("1.25"), "ACTUAL", intent["reservation_id"])
	f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), late)
	resourceSnapshot(f, "after-resume.json")
}

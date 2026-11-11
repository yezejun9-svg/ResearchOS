package domain

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"sort"
	"testing"
	"time"
)

func TestW06ConcurrentDispatch(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("concurrent", Empty(), Empty())
	executor := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		t.Fatal(e)
	}
	body := Object{"runtime_id": o.rt["id"], "executor_principal_id": executor, "context_bundle_id": task["context_bundle_id"]}
	server, _ := fixtureHTTPServer(t, f.h)
	defer server.Close()
	type result struct {
		status int
		body   Object
		key    string
	}
	ch := make(chan result, 2)
	for range 2 {
		go func() {
			key := ID()
			req, _ := http.NewRequest("POST", server.URL+f.path("/tasks/"+Str(task, "id")+"/claim"), bytes.NewReader(Bytes(body)))
			req.Header.Set("Authorization", "Bearer "+o.owner)
			req.Header.Set("If-Match", testTag(task))
			req.Header.Set("Idempotency-Key", key)
			res, e := server.Client().Do(req)
			if e != nil {
				ch <- result{status: 0}
				return
			}
			defer res.Body.Close()
			raw, _ := io.ReadAll(res.Body)
			b, _ := Decode(raw)
			ch <- result{res.StatusCode, b, key}
		}()
	}
	codes := []int{}
	var winner result
	for range 2 {
		r := <-ch
		codes = append(codes, r.status)
		if r.status == 201 {
			winner = r
		}
	}
	sort.Ints(codes)
	var runs int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run'").Scan(&runs)
	replay := f.expect(201, "POST", f.path("/tasks/"+Str(task, "id")+"/claim"), winner.key, testTag(task), body)
	orchestrationAssert(t, "A02-04-SINGLE-CLAIM", []any{201, 412, 1, true}, []any{codes[0], codes[1], runs, replay["run"].(map[string]any)["id"] == winner.body["run"].(map[string]any)["id"]}, Object{"http_statuses": codes, "run_count": runs, "run_id": replay["run"].(map[string]any)["id"], "idempotent_replay": true})
}

func TestW06RecoveryFence(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	r := o.claim(o.task("recover", Empty(), Empty()))
	tx, _ := f.db.Begin()
	run, _ := load(tx, f.project, "Run", Str(r.run, "id"))
	run["lease_expires_at"] = time.Now().UTC().Add(-time.Second).Format(time.RFC3339Nano)
	bump(run)
	if e := f.s.put(tx, "Run", run); e != nil {
		t.Fatal(e)
	}
	if e := tx.Commit(); e != nil {
		t.Fatal(e)
	}
	restarted, e := New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	f.s = restarted
	f.h = restarted.Handler()
	recovered, e := restarted.RecoverExpiredRuns(context.Background(), o.owner, f.project)
	if e != nil {
		t.Fatal(e)
	}
	again, e := restarted.RecoverExpiredRuns(context.Background(), o.owner, f.project)
	if e != nil {
		t.Fatal(e)
	}
	r.refresh()
	status, reply, _ := f.request("POST", f.path("/runs/"+Str(r.run, "id")+"/heartbeat"), ID(), testTag(r.run), r.heartbeat())
	f.token = o.owner
	task := f.read("tasks", Str(r.task, "id"))
	claim, _, _ := f.request("POST", f.path("/tasks/"+Str(task, "id")+"/claim"), ID(), testTag(task), Object{"runtime_id": o.rt["id"], "executor_principal_id": r.executor, "context_bundle_id": task["context_bundle_id"]})
	var runs int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run'").Scan(&runs)
	orchestrationAssert(t, "A02-04-RECOVERY-FENCE", []any{1, 0, "RECONCILING", "RUNNING", 409, 409, 1}, []any{len(recovered), len(again), r.run["status"], task["status"], status, claim, runs}, Object{"run": r.run, "heartbeat_rejection": reply})
}

func TestW06CrashHelper(t *testing.T) {
	if os.Getenv("W06_CRASH_HELPER") != "1" {
		return
	}
	db, e := store.Open(os.Getenv("W06_CRASH_DB"))
	if e != nil {
		panic(e)
	}
	s, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		panic(e)
	}
	tx, e := db.Begin()
	if e != nil {
		panic(e)
	}
	p, e := authenticate(tx, os.Getenv("W06_CRASH_TOKEN"))
	if e != nil {
		panic(e)
	}
	body, e := Decode([]byte(os.Getenv("W06_CRASH_BODY")))
	if e != nil {
		panic(e)
	}
	_, e = s.claimTask(tx, p, os.Getenv("W06_CRASH_PROJECT"), os.Getenv("W06_CRASH_TASK"), body, ID())
	if e != nil {
		panic(e)
	}
	// Deliberately terminate the actual process with business and outbox writes uncommitted.
	os.Stdout.WriteString("claim and outbox written in open transaction; terminating before commit\n")
	os.Exit(23)
}

func TestW06CrashRollback(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("crash-transaction", Empty(), Empty())
	executor := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		t.Fatal(e)
	}
	var seq int
	f.db.QueryRow("SELECT count(*) FROM outbox").Scan(&seq)
	var index int
	var name, path string
	if e := f.db.QueryRow("PRAGMA database_list").Scan(&index, &name, &path); e != nil {
		t.Fatal(e)
	}
	body := Object{"runtime_id": o.rt["id"], "executor_principal_id": executor, "context_bundle_id": task["context_bundle_id"]}
	exe, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	cmd := exec.Command(exe, "-test.run=^TestW06CrashHelper$")
	cmd.Env = append(os.Environ(), "W06_CRASH_HELPER=1", "W06_CRASH_DB="+path, "W06_CRASH_PROJECT="+f.project, "W06_CRASH_TASK="+Str(task, "id"), "W06_CRASH_TOKEN="+o.owner, "W06_CRASH_BODY="+string(Bytes(body)))
	raw, e := cmd.CombinedOutput()
	exit := 0
	if x, ok := e.(*exec.ExitError); ok {
		exit = x.ExitCode()
	} else if e != nil {
		t.Fatal(e)
	}
	var runs, after int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run'").Scan(&runs)
	f.db.QueryRow("SELECT count(*) FROM outbox").Scan(&after)
	orchestrationAssert(t, "A03-03-CRASH-ROLLBACK", []any{23, 0, seq, "READY"}, []any{exit, runs, after, f.read("tasks", Str(task, "id"))["status"]}, Object{"argv": cmd.Args, "exit": exit, "stdout": string(raw), "stdout_hash": Digest(raw), "environment_names": []any{"W06_CRASH_HELPER", "W06_CRASH_DB", "W06_CRASH_PROJECT", "W06_CRASH_TASK", "W06_CRASH_TOKEN", "W06_CRASH_BODY"}})
	claimed := f.expect(201, "POST", f.path("/tasks/"+Str(task, "id")+"/claim"), ID(), testTag(task), body)
	events := f.expect(200, "GET", f.path("/events")+"?limit=100", "", "", nil)
	unique := map[string]bool{}
	ordered := true
	last := int64(0)
	for _, v := range Arr(events, "items") {
		event := v.(map[string]any)
		n, _ := Num(event, "sequence")
		if n <= last || unique[Str(event, "id")] {
			ordered = false
		}
		last = n
		unique[Str(event, "id")] = true
		if e = f.s.AcknowledgeEvent(context.Background(), f.project, Str(event, "id")); e != nil {
			t.Fatal(e)
		}
		if e = f.s.AcknowledgeEvent(context.Background(), f.project, Str(event, "id")); e != nil {
			t.Fatal(e)
		}
	}
	var pending int
	f.db.QueryRow("SELECT count(*) FROM outbox WHERE acknowledged=0").Scan(&pending)
	orchestrationAssert(t, "A03-03-RESTART-OUTBOX", []any{"RUNNING", true, 0}, []any{claimed["task"].(map[string]any)["status"], ordered, pending}, Object{"event_ids": unique, "last_sequence": last, "duplicate_delivery_acknowledged_once": true})
	items := Arr(events, "items")
	for i := len(items) - 1; i >= 0; i-- {
		if _, e = f.s.ConsumeEvent(context.Background(), "restart-projection", f.project, Str(items[i].(map[string]any), "id")); e != nil {
			t.Fatal(e)
		}
	}
	for _, item := range items {
		if _, e = f.s.ConsumeEvent(context.Background(), "restart-projection", f.project, Str(item.(map[string]any), "id")); e != nil {
			t.Fatal(e)
		}
	}
	var projectionRaw string
	if e = f.db.QueryRow("SELECT body FROM context_projection WHERE consumer='restart-projection' AND project=? AND kind='Task' AND id=?", f.project, task["id"]).Scan(&projectionRaw); e != nil {
		t.Fatal(e)
	}
	projection, e := Decode([]byte(projectionRaw))
	if e != nil {
		t.Fatal(e)
	}
	var position, applied int
	if e = f.db.QueryRow("SELECT sequence FROM consumer_positions WHERE consumer='restart-projection' AND project=?", f.project).Scan(&position); e != nil {
		t.Fatal(e)
	}
	if e = f.db.QueryRow("SELECT count(*) FROM consumer_inbox WHERE consumer='restart-projection' AND project=? AND applied=1", f.project).Scan(&applied); e != nil {
		t.Fatal(e)
	}
	orchestrationAssert(t, "A03-03-CONSUMER-PROJECTION", []any{len(items), len(items), Hash(f.read("tasks", Str(task, "id")))}, []any{position, applied, Hash(projection)}, Object{"reverse_delivery_and_full_replay": true, "projection": projection})
}

func TestW06RouteEvidence(t *testing.T) {
	read := func(path string) Object {
		raw, e := os.ReadFile(filepath.Join("../..", path))
		if e != nil {
			t.Fatal(e)
		}
		o, e := Decode(raw)
		if e != nil {
			t.Fatal(e)
		}
		return o
	}
	route := read("execution/route.json")
	qualification := read("qualification/core/results.json")
	attempts := read("qualification/core/attempts.json")
	bounded := len(Arr(attempts, "approaches")) <= 2
	for _, v := range Arr(attempts, "approaches") {
		n, _ := Num(v.(map[string]any), "repair_rounds")
		if n > 1 {
			bounded = false
		}
	}
	// W01's actual Paperclip failures are reused; this fixture does not retry upstream.
	orchestrationAssert(t, "A02-01-03-FROZEN-ROUTE", []any{"THIN_CORE", false, true}, []any{route["selected_route"], qualification["paperclip_qualified"], bounded}, Object{"route_hash": Hash(route), "qualification_hash": Hash(qualification), "attempts_hash": Hash(attempts), "actual_live_upstream_retry_count": 0, "basis": "W01 accepted bounded fallback evidence"})
}

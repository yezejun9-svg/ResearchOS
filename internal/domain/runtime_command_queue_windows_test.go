//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/store"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestRuntimeClientQueueActualMuSameProcess(t *testing.T) { testRuntimeClientQueueActual(t, false) }
func TestRuntimeClientQueueActualMuCancelUnknownEffect(t *testing.T) {
	testRuntimeClientQueueActual(t, true)
}
func TestRuntimeClientQueueGoalCancelClaimOrdering(t *testing.T) {
	for _, order := range []string{"cancel_before_claim", "cancel_after_claim_before_launch"} {
		t.Run(order, func(t *testing.T) { testRuntimeClientQueueActual(t, false, order) })
	}
}
func testRuntimeClientQueueActual(t *testing.T, cancelActive bool, raceOrder ...string) {
	var calls atomic.Int32
	held := make(chan struct{})
	release := make(chan struct{})
	var once sync.Once
	t.Cleanup(func() { once.Do(func() { close(release) }) })
	var bodiesMu sync.Mutex
	var bodies []string
	c, route, r, _ := muBrokerFixtureProgram(t, func(w http.ResponseWriter, request *http.Request) {
		n := calls.Add(1)
		raw, _ := io.ReadAll(request.Body)
		bodiesMu.Lock()
		bodies = append(bodies, string(raw))
		bodiesMu.Unlock()
		if n == 2 {
			close(held)
			select {
			case <-release:
			case <-request.Context().Done():
				return
			}
		}
		w.Header().Set("Content-Type", "text/event-stream")
		fmt.Fprint(w, "data: {\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"complete\"},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
	}, nil)
	qualifyNativeCoordinator(t, c, route, r)
	f := r.f
	f.token = r.ownerToken
	workspace := t.TempDir()
	c.config.WorkspaceAuthority = permissionWorkspaceFixture{workspace}
	c.config.ClientSchema = clientHistoryDoc(t)
	provider := c.config.Providers[0]
	provider.Purpose = "mu_turn"
	c.config.Providers = append(c.config.Providers, provider)
	if err := f.s.AuthorizeRuntimePurpose(context.Background(), f.token, f.project, route.RuntimeID, "mu_turn", time.Now().Add(time.Minute*10)); err != nil {
		t.Fatal(err)
	}
	route.ExecutorID = ID()
	if err := f.s.ProvisionPrincipal(context.Background(), Principal{ID: route.ExecutorID, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}); err != nil {
		t.Fatal(err)
	}
	var err error
	route.ExecutorToken, err = f.s.IssueCredential(context.Background(), route.ExecutorID, time.Minute*10)
	if err != nil {
		t.Fatal(err)
	}
	c.config.Routes = []RuntimeCoordinatorRoute{route}
	client := "queue-sdk-client"
	binding := WorkspaceBinding{AuthorizedRef: "queue-workspace-" + ID(), DisplayName: "queue", DisplayPath: workspace, RealPath: workspace, Access: "READ_WRITE", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: client, HostPrincipalRef: "fixture", CreatedAt: Now()}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, binding.AuthorizedRef, binding.record())
	})
	svc := &ClientService{Doc: c.config.ClientSchema, Domain: f.s, SessionRuntime: c, Host: ClientHostInfo{CoreBuildID: "queue-sdk-test", LeaseTTL: time.Minute}}
	created, _ := goalCommand(t, f, svc, goalEnvelope(f, client, "Hold original turn for same-process commands", false))
	if deref(created.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(created)))
	}
	sid := Str(created.Result["snapshot"].(map[string]any), "session_id")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if len(raceOrder) != 0 {
		var goal, task string
		if err = f.db.QueryRow("SELECT goal_id,task_id FROM client_sessions WHERE id=?", sid).Scan(&goal, &task); err != nil {
			t.Fatal(err)
		}
		var envelope *Envelope
		var original *Response
		cancelGoal := func() {
			envelope = queueClientEnvelope(t, f, client, sid, "session.control", Object{"action": "CANCEL", "target_id": goal, "reason": "claim transaction ordering fixture"})
			original, _ = goalCommand(t, f, svc, envelope)
		}
		wantRuns, wantStatus := 0, "COMPLETED"
		if raceOrder[0] == "cancel_before_claim" {
			cancelGoal()
		} else {
			wantRuns, wantStatus = 1, "ACKNOWLEDGED"
			c.boundaryHook = func(name string, _ Object) {
				if name == "claim_committed" {
					cancelGoal()
				}
			}
		}
		if err = c.Scan(ctx); err != nil {
			t.Fatal(err)
		}
		c.workers.Wait()
		c.boundaryHook = nil
		if original == nil || deref(original.Status) != wantStatus {
			t.Fatalf("ordered cancellation outcome: %s", Bytes(original))
		}
		for i := 0; i < 2; i++ {
			if err = c.Scan(ctx); err != nil {
				t.Fatal(err)
			}
			c.workers.Wait()
		}
		var runs, started int
		if err = f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.task_id')=?", task).Scan(&runs); err != nil {
			t.Fatal(err)
		}
		if err = f.db.QueryRow("SELECT count(*) FROM runtime_dispatches WHERE json_extract(manifest,'$.task_id')=? AND (state<>'PREPARED' OR worker<>'')", task).Scan(&started); err != nil {
			t.Fatal(err)
		}
		if runs != wantRuns || started != 0 || calls.Load() != 1 {
			t.Fatalf("later claim/launch escaped cancellation: runs=%d started=%d model_calls=%d", runs, started, calls.Load())
		}
		replayed, replay := goalCommand(t, f, svc, envelope)
		if !replay || Hash(replayed) != Hash(original) {
			t.Fatal("original cancellation result/identity changed")
		}
		if wantRuns == 1 {
			select {
			case e := <-c.errors:
				if !strings.Contains(e.Error(), "run cannot dispatch") {
					t.Fatal(e)
				}
			default:
				t.Fatal("claimed Run bypassed cancelled dispatch gate")
			}
		}
		t.Logf("actual qualified Goal/claim/control order=%s original_status=%s Run_count=%d physical_dispatches=0 repeated_scan_no_successor=true", raceOrder[0], wantStatus, runs)
		return
	}
	if err = c.Scan(ctx); err != nil {
		t.Fatal(err)
	}
	select {
	case <-held:
	case failure := <-c.errors:
		var rows []Object
		for _, kind := range []string{"Task", "Run"} {
			found, e := backupObjects(f.db, "SELECT body FROM domain_objects WHERE kind='"+kind+"'")
			if e != nil {
				t.Fatal(e)
			}
			rows = append(rows, found...)
		}
		if dir := os.Getenv("RESEARCHOS_QUEUE_FAILURE_DIR"); dir != "" {
			if e := os.MkdirAll(dir, 0700); e != nil {
				t.Fatal(e)
			}
			path := filepath.Join(dir, t.Name()+".sqlite")
			if _, e := f.db.Exec("VACUUM INTO ?", path); e != nil {
				t.Fatal(e)
			}
			t.Log("isolated failed fixture snapshot:", path)
		}
		t.Fatalf("original Mu worker failed before MODEL: %v; canonical=%s", failure, Bytes(rows))
	case <-ctx.Done():
		t.Fatal("original Mu turn did not reach broker")
	}
	text := "保持重复文本的两个独立指令"
	for _, mode := range []string{"STEER", "FOLLOW_UP"} {
		reply, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": text, "attachment_artifact_ids": Empty(), "delivery": mode}))
		if deref(reply.Status) != "COMPLETED" {
			t.Fatal(string(Bytes(reply)))
		}
	}
	deadline := time.Now().Add(5 * time.Second)
	accepted := 0
	for time.Now().Before(deadline) {
		if err = f.db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE session_id=? AND state='SDK_ACCEPTED'`, sid).Scan(&accepted); err != nil {
			t.Fatal(err)
		}
		if accepted == 2 {
			break
		}
		time.Sleep(20 * time.Millisecond)
	}
	if accepted != 2 {
		t.Fatalf("SDK accepted=%d while original MODEL pending", accepted)
	}

	if cancelActive {
		var goal, taskID, runID string
		if err = f.db.QueryRow(`SELECT goal_id,task_id,run_id FROM client_sessions WHERE id=?`, sid).Scan(&goal, &taskID, &runID); err != nil {
			t.Fatal(err)
		}
		env := queueClientEnvelope(t, f, client, sid, "session.control", Object{"action": "CANCEL", "target_id": goal, "reason": "cancel held actual MODEL and same worker queue"})
		reply, _ := goalCommand(t, f, svc, env)
		if deref(reply.Status) != "ACKNOWLEDGED" {
			t.Fatal(string(Bytes(reply)))
		}
		c.workers.Wait()
		once.Do(func() { close(release) })
		var unknown, clear, abort, idle, dispatches int
		f.db.QueryRow(`SELECT count(*) FROM resource_effects WHERE json_extract(body,'$.state')='UNKNOWN'`).Scan(&unknown)
		f.db.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE kind='command.cleared'`).Scan(&clear)
		f.db.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE kind='command.abort_observed'`).Scan(&abort)
		f.db.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE kind='command.idle' AND json_extract(body,'$.cancelled')=1`).Scan(&idle)
		if unknown == 0 || clear != 2 || abort == 0 || idle == 0 {
			t.Fatalf("unknown=%d SDK clear=%d abort=%d cancelled idle=%d", unknown, clear, abort, idle)
		}
		repeated, replay := goalCommand(t, f, svc, env)
		if !replay || deref(repeated.Status) != "ACKNOWLEDGED" {
			t.Fatal("unknown effect falsely confirmed cancellation", string(Bytes(repeated)))
		}
		if err = c.Recover(context.Background()); err != nil {
			t.Log("recovery truthfully remains pending", err)
		}
		if err = c.Scan(context.Background()); err != nil {
			t.Fatal(err)
		}
		f.db.QueryRow(`SELECT count(*) FROM runtime_dispatches WHERE project=? AND json_extract(manifest,'$.task_id')=?`, f.project, taskID).Scan(&dispatches)
		if dispatches != 1 {
			t.Fatal("unknown cancellation was redispatched", dispatches)
		}
		drain, err := f.s.RuntimeDrainSnapshot(context.Background())
		if err != nil || drain.UnresolvedCommands == 0 || drain.UnresolvedEffects == 0 {
			t.Fatalf("false complete drain: %+v %v", drain, err)
		}
		t.Logf("same SDK process clear=%d abort=%d idle=%d; actual cancelled effect UNKNOWN=%d; original CANCEL remains ACKNOWLEDGED; no redispatch", clear, abort, idle, unknown)
		return
	}

	// Capture the exact pre-consumption database while the original process is
	// alive, then recover only from its later authenticated durable journal.
	snapshotDB := filepath.Join(t.TempDir(), "accepted.sqlite")
	if _, err = f.db.Exec(`VACUUM INTO ?`, snapshotDB); err != nil {
		t.Fatal(err)
	}
	var sealRefusal atomic.Bool
	c.boundaryHook = func(name string, _ Object) {
		if name != "queue_sealing" {
			return
		}
		late, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": "racing final idle", "attachment_artifact_ids": Empty(), "delivery": "FOLLOW_UP"}))
		sealRefusal.Store(deref(late.Status) == "REJECTED")
	}
	once.Do(func() { close(release) })
	c.workers.Wait()
	select {
	case err := <-c.errors:
		t.Fatal(err)
	default:
	}
	var consumed, dispatches int
	var taskID, runID string
	if err = f.db.QueryRow(`SELECT task_id,run_id FROM client_sessions WHERE id=?`, sid).Scan(&taskID, &runID); err != nil {
		t.Fatal(err)
	}
	f.db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE session_id=? AND state='CONSUMED'`, sid).Scan(&consumed)
	f.db.QueryRow(`SELECT count(*) FROM runtime_dispatches WHERE project=? AND json_extract(manifest,'$.task_id')=?`, f.project, taskID).Scan(&dispatches)
	if consumed != 2 || dispatches != 1 {
		t.Fatalf("consumed=%d dispatches=%d", consumed, dispatches)
	}
	run := f.read("runs", runID)
	if run["status"] != "SETTLED" || run["queue_empty"] != true {
		t.Fatalf("unsettled run: %s", Bytes(run))
	}
	var fence string
	var acceptedThrough, sealedThrough int64
	f.db.QueryRow(`SELECT state,accepted_through,sealed_through FROM client_queue_fences WHERE session_id=?`, sid).Scan(&fence, &acceptedThrough, &sealedThrough)
	if fence != "SEALED" || acceptedThrough != 2 || sealedThrough != 2 {
		t.Fatalf("seal=%s %d/%d", fence, acceptedThrough, sealedThrough)
	}
	bodiesMu.Lock()
	last := bodies[len(bodies)-1]
	bodiesMu.Unlock()
	if strings.Count(last, text) != 2 || strings.Contains(last, "queue_generation") {
		t.Fatalf("model payload changed supplementary input: %s", last)
	}

	if !sealRefusal.Load() {
		t.Fatal("enqueue after committed SEALING was not rejected before success")
	}
	var locator, manifestHash string
	var epoch int64
	if err = f.db.QueryRow(`SELECT dispatch_key,manifest_hash,epoch FROM runtime_dispatches WHERE project=? AND run=?`, f.project, runID).Scan(&locator, &manifestHash, &epoch); err != nil {
		t.Fatal(err)
	}
	journal, err := rt.ReadBridgeTerminal(filepath.Join(c.config.DataRoot, "runtime-dispatches", locator), manifestHash)
	if err != nil {
		t.Fatal(err)
	}
	oldDB, err := store.Open(snapshotDB)
	if err != nil {
		t.Fatal(err)
	}
	defer oldDB.Close()
	recovered := &RuntimeCoordinator{service: &Service{DB: oldDB}}
	sourceTx(t, oldDB, func(tx *sql.Tx) error {
		return unknownClientRunQueue(tx, f.project, runID, "injected crash after SDK acceptance before consumed receipt commit")
	})
	before, _ := backupQueueState(oldDB)
	foreign := journal
	foreign.Identity.Created++
	if recovered.recoverClientQueue(context.Background(), f.project, runID, epoch, foreign) == nil {
		t.Fatal("foreign original process accepted")
	}
	if recovered.recoverClientQueue(context.Background(), f.project, runID, epoch+1, journal) == nil {
		t.Fatal("foreign runtime epoch accepted")
	}
	after, _ := backupQueueState(oldDB)
	if Hash(before) != Hash(after) {
		t.Fatal("rejected recovery mutated queue")
	}
	if err = recovered.recoverClientQueue(context.Background(), f.project, runID, epoch, journal); err != nil {
		t.Fatal(err)
	}
	var reconciled int
	if err = oldDB.QueryRow(`SELECT count(*) FROM client_command_queue WHERE state='CONSUMED'`).Scan(&reconciled); err != nil || reconciled != 2 {
		t.Fatalf("exact old SDK evidence did not reconcile: %d %v", reconciled, err)
	}
	before, _ = backupQueueState(oldDB)
	if err = recovered.recoverClientQueue(context.Background(), f.project, runID, epoch, journal); err != nil {
		t.Fatal(err)
	}
	after, _ = backupQueueState(oldDB)
	if Hash(before) != Hash(after) {
		t.Fatal("same original receipt replay not idempotent")
	}
	if _, err = oldDB.Exec(`UPDATE client_queue_fences SET restore_fenced=1,state='RECONCILING'`); err != nil {
		t.Fatal(err)
	}
	if err = recovered.recoverClientQueue(context.Background(), f.project, runID, epoch, journal); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, oldDB, func(tx *sql.Tx) error {
		if clientQueueSettled(tx, f.project, runID) == nil {
			t.Fatal("old snapshot receipt removed restore fence")
		}
		return nil
	})
	t.Logf("actual pinned Mu SDK, one original Task/Run/process, accepted=2 consumed=2 sealed=2 model_calls=%d (qualification included), provider=loopback FIXTURE", calls.Load())
}

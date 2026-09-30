//go:build windows

package supervisor

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/store"
)

// These tests run the real control executable with disposable same-user data.
// Synthetic admission validates process mechanics only, never release authority.
func TestActualControlDrain(t *testing.T) {
	repo, e := filepath.Abs(filepath.Join("..", ".."))
	if e != nil {
		t.Fatal(e)
	}
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		t.Fatal("pinned RESEARCHOS_GO required")
	}
	base := t.TempDir()
	exe := filepath.Join(base, "control.exe")
	build := exec.Command(goexe, "build", "-trimpath", "-buildvcs=false", "-o", exe, "./apps/control")
	build.Dir = repo
	if raw, e := build.CombinedOutput(); e != nil {
		t.Fatalf("build: %v %s", e, raw)
	}
	web := filepath.Join(base, "web")
	if e = os.Mkdir(web, 0700); e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(web, "index.html"), []byte("fixture"), 0600); e != nil {
		t.Fatal(e)
	}
	config := filepath.Join(base, "coordinator.json")
	if e = os.WriteFile(config, []byte(`{}`), 0600); e != nil {
		t.Fatal(e)
	}
	type continuity struct {
		token, project, profileDigest string
		revision                      any
	}
	states := map[*ControlFixtureDriver]continuity{}
	request := func(t *testing.T, d *ControlFixtureDriver, token, method, path, body string, status int) map[string]any {
		t.Helper()
		r, e := http.NewRequest(method, "http://"+d.Listen+path, strings.NewReader(body))
		if e != nil {
			t.Fatal(e)
		}
		r.Header.Set("Authorization", "Bearer "+token)
		r.Header.Set("Content-Type", "application/json")
		r.Header.Set("Idempotency-Key", ReleaseDigest(path+body))
		res, e := (&http.Client{Timeout: 3 * time.Second}).Do(r)
		if e != nil {
			t.Fatal(e)
		}
		defer res.Body.Close()
		raw, e := io.ReadAll(res.Body)
		if e != nil {
			t.Fatal(e)
		}
		if res.StatusCode != status {
			t.Fatalf("%s %s status=%d body=%s", method, path, res.StatusCode, raw)
		}
		var result map[string]any
		if e = json.Unmarshal(raw, &result); e != nil {
			t.Fatal(e)
		}
		return result
	}
	newFixture := func(t *testing.T, seed string) (*ReleaseEngine, *ControlFixtureDriver, *ReleaseJournal) {
		root := t.TempDir()
		data := filepath.Join(root, "data")
		init := exec.Command(exe, "--bootstrap-owner", "--credential-file", filepath.Join(root, "owner.json"))
		init.Dir = repo
		init.Env = append(os.Environ(), "RESEARCHOS_DATA_DIR="+data, "RESEARCHOS_WEB_DIR="+web)
		if raw, e := init.CombinedOutput(); e != nil {
			t.Fatalf("initialize: %v %s", e, raw)
		}
		raw, e := os.ReadFile(filepath.Join(root, "owner.json"))
		if e != nil {
			t.Fatal(e)
		}
		var credential struct {
			Token string `json:"token"`
		}
		if e = json.Unmarshal(raw, &credential); e != nil {
			t.Fatal(e)
		}
		db, e := store.Open(filepath.Join(data, "researchos.sqlite"))
		if e != nil {
			t.Fatal(e)
		}
		if seed != "" {
			if _, e = db.Exec(seed); e != nil {
				t.Fatal(e)
			}
		}
		if e = db.Close(); e != nil {
			t.Fatal(e)
		}
		l, e := net.Listen("tcp", "127.0.0.1:0")
		if e != nil {
			t.Fatal(e)
		}
		addr := l.Addr().String()
		l.Close()
		j, e := OpenReleaseJournal(filepath.Join(root, "journal"))
		if e != nil {
			t.Fatal(e)
		}
		logfile, e := os.Create(filepath.Join(root, "control.log"))
		if e != nil {
			t.Fatal(e)
		}
		d := &ControlFixtureDriver{Journal: j, WorkDir: repo, WebDir: web, Listen: addr, CoordinatorConfig: config, Output: logfile}
		engine, e := NewReleaseEngine(j, d, d, func(ReleaseAdmission) error { return nil })
		if e != nil {
			t.Fatal(e)
		}
		t.Cleanup(func() {
			// Forced termination is disposable-fixture cleanup only. No drain
			// success, stopped receipt, or candidate launch is derived from it.
			if d.process.PID != 0 {
				if e := (NativeFixtureDriver{}).Stop(d.process); e != nil {
					t.Errorf("disposable cleanup exact process: %v", e)
				}
			}
			logfile.Close()
			if t.Failed() {
				raw, _ := os.ReadFile(logfile.Name())
				t.Logf("control log: %s", raw)
			}
			j.Close()
		})
		if e = engine.BootstrapFixture(context.Background(), exe, data); e != nil {
			t.Fatal(e)
		}
		created := request(t, d, credential.Token, http.MethodPost, "/v1/projects", `{"name":"Actual control continuity","intent":"verify fixture drain","facts":[],"accepted_scope":["fixture"],"constraints":[],"source_configs":[],"source_document_refs":[],"read_snapshot_ids":[]}`, 201)
		project, ok := created["project_id"].(string)
		if !ok || project == "" {
			t.Fatal("created project identity absent")
		}
		profile := request(t, d, credential.Token, http.MethodGet, "/v1/projects/"+project+"/profile", "", 200)
		states[d] = continuity{credential.Token, project, ReleaseDigest(profile), profile["revision"]}
		s := j.State()
		a := ReleaseAdmission{Project: "fixture", CandidateID: "mechanism-only", AcceptanceID: "synthetic-test", ExecutionSHA256: ReleaseDigest("execution"), Operation: "actual-control-drain", ExpectedEpoch: s.Epoch, StableSHA256: s.Active, CandidateSHA256: s.Active, BackupReceiptSHA256: ReleaseDigest("fixture-backup"), VerifierReceiptSHA256: ReleaseDigest("fixture-verifier"), HoldoutProofSHA256: ReleaseDigest("fixture-holdout"), SameSchema: true, NoUnknownEffects: true, ExpiresUTC: time.Now().Add(time.Minute)}
		if _, e = engine.PrepareFixture(a, exe); e != nil {
			t.Fatal(e)
		}
		return engine, d, j
	}
	checkLocked := func(t *testing.T, data string) {
		t.Helper()
		if l, e := rt.AcquireDataRootLease(data); e == nil {
			l.Close()
			t.Fatal("second writer obtained data root")
		}
	}
	checkHTTP := func(t *testing.T, d *ControlFixtureDriver, method string, want int) {
		t.Helper()
		path := "/healthz"
		if method == http.MethodPost {
			path = "/v1/projects"
		}
		r, _ := http.NewRequest(method, "http://"+d.Listen+path, nil)
		c := &http.Client{Timeout: time.Second}
		res, e := c.Do(r)
		if e != nil {
			t.Fatal(e)
		}
		res.Body.Close()
		if res.StatusCode != want {
			t.Fatalf("HTTP %s=%d want %d", method, res.StatusCode, want)
		}
	}
	t.Run("idle_same_root_switch_preserves_data", func(t *testing.T) {
		engine, d, j := newFixture(t, "")
		old := processIn(j.State())
		checkLocked(t, j.State().Data)
		admin := exec.Command(exe, "--issue-credential", "fixture", "--credential-file", filepath.Join(t.TempDir(), "must-not-exist.json"))
		admin.Dir = repo
		admin.Env = append(os.Environ(), "RESEARCHOS_DATA_DIR="+j.State().Data)
		if raw, e := admin.CombinedOutput(); e == nil || !strings.Contains(string(raw), "control data-root lease unavailable") {
			t.Fatalf("administration bypassed live writer lock: %v %s", e, raw)
		}
		s, e := engine.SwitchFixture(context.Background(), j.State().Operation)
		if e != nil {
			t.Fatal(e)
		}
		if s.Phase != "CANARY" || s.PID == old.PID || s.CreatedNS == old.CreatedNS {
			t.Fatalf("no new control: %+v", s)
		}
		if alive, e := d.Alive(old); e != nil || alive {
			t.Fatalf("old writer remains: %v %v", alive, e)
		}
		checkLocked(t, s.Data)
		checkHTTP(t, d, http.MethodGet, 200)
		before := states[d]
		profile := request(t, d, before.token, http.MethodGet, "/v1/projects/"+before.project+"/profile", "", 200)
		if ReleaseDigest(profile) != before.profileDigest || profile["revision"] != before.revision {
			t.Fatal("authority project changed across actual restart")
		}
		t.Logf("actual idle stop/same-root restart: old=%+v candidate=%+v durable=%s project=%s revision=%v profile_sha256=%s preserved via actual GET", old, processIn(s), s.Phase, before.project, before.revision, before.profileDigest)
	})
	t.Run("occupied_listener_cannot_prove_child_ready", func(t *testing.T) {
		root := t.TempDir()
		data := filepath.Join(root, "data")
		init := exec.Command(exe, "--bootstrap-owner", "--credential-file", filepath.Join(root, "owner.json"))
		init.Dir = repo
		init.Env = append(os.Environ(), "RESEARCHOS_DATA_DIR="+data, "RESEARCHOS_WEB_DIR="+web)
		if raw, e := init.CombinedOutput(); e != nil {
			t.Fatalf("initialize: %v %s", e, raw)
		}
		unrelated := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))
		defer unrelated.Close()
		res, e := unrelated.Client().Get(unrelated.URL + "/healthz")
		if e != nil {
			t.Fatal(e)
		}
		res.Body.Close()
		if res.StatusCode != 200 {
			t.Fatal("unrelated listener not healthy")
		}
		// Hold a disposable pre-start SQLite write transaction so the actual
		// child remains alive in bootstrap until after the readiness check.
		// No production DB or running control writer is involved.
		db, e := store.Open(filepath.Join(data, "researchos.sqlite"))
		if e != nil {
			t.Fatal(e)
		}
		defer db.Close()
		tx, e := db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		defer tx.Rollback()
		if _, e = tx.Exec("UPDATE auth_principals SET revoked=revoked"); e != nil {
			t.Fatal(e)
		}
		j, e := OpenReleaseJournal(filepath.Join(root, "journal"))
		if e != nil {
			t.Fatal(e)
		}
		defer j.Close()
		_, hash, e := exactImage(exe)
		if e != nil {
			t.Fatal(e)
		}
		if e = j.Append(ReleaseState{Epoch: 1, Operation: "bootstrap", Phase: "STARTING", Active: hash, ActivePath: exe, LastGood: hash, LastGoodPath: exe, Data: data}); e != nil {
			t.Fatal(e)
		}
		logfile, e := os.Create(filepath.Join(root, "control.log"))
		if e != nil {
			t.Fatal(e)
		}
		defer logfile.Close()
		d := &ControlFixtureDriver{Journal: j, WorkDir: repo, WebDir: web, Listen: strings.TrimPrefix(unrelated.URL, "http://"), CoordinatorConfig: config, Output: logfile}
		p, e := d.Start(exe, "bootstrap-1", data)
		if e != nil {
			t.Fatal(e)
		}
		defer func() {
			if e := (NativeFixtureDriver{}).Stop(p); e != nil {
				t.Errorf("exact fixture cleanup: %v", e)
			}
		}()
		ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
		defer cancel()
		if e = d.Ready(ctx, p, "bootstrap-1"); e == nil {
			t.Fatal("unrelated HTTP 200 certified an unready actual child")
		}
		if alive, err := d.Alive(p); err != nil || !alive {
			t.Fatalf("check did not exercise live startup child: %v %v", alive, err)
		}
		checkLocked(t, data)
		t.Logf("unrelated health=200 rejected for still-live actual child=%+v; private READY absent; phase=%s", p, j.State().Phase)
	})
	for _, tc := range []struct{ name, seed string }{
		{"nonterminal_run", `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('fixture','Run','active',1,'{"status":"RUNNING"}')`},
		{"unknown_effect", `INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES('fixture','old-run','effect',1,'{"state":"UNKNOWN"}')`},
		{"pending_reservation", `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('fixture','BudgetLedgerEntry','reserved',1,'{"operation":"RESERVE","run_id":"old-run","provider_request_id":"request"}')`},
	} {
		t.Run(tc.name, func(t *testing.T) {
			engine, d, j := newFixture(t, tc.seed)
			before := processIn(j.State())
			if _, e := engine.SwitchFixture(context.Background(), j.State().Operation); e == nil {
				t.Fatal("busy control switched")
			}
			if j.State().Phase != "PREPARED" || processIn(j.State()) != before {
				t.Fatal("busy control changed")
			}
			checkHTTP(t, d, http.MethodGet, 200)
			checkHTTP(t, d, http.MethodPost, 401)
			checkLocked(t, j.State().Data)
			t.Logf("busy refusal retains %+v, phase=%s", before, j.State().Phase)
		})
	}
	t.Run("inflight_HTTP_write", func(t *testing.T) {
		engine, d, j := newFixture(t, "")
		conn, e := net.Dial("tcp", d.Listen)
		if e != nil {
			t.Fatal(e)
		}
		defer conn.Close()
		_, e = fmt.Fprintf(conn, "POST /v1/projects HTTP/1.1\r\nHost: %s\r\nAuthorization: Bearer %s\r\nExpect: 100-continue\r\nContent-Length: 1000\r\n\r\n", d.Listen, states[d].token)
		if e != nil {
			t.Fatal(e)
		}
		if e = conn.SetReadDeadline(time.Now().Add(time.Second)); e != nil {
			t.Fatal(e)
		}
		reader := bufio.NewReader(conn)
		line, e := reader.ReadString('\n')
		if e != nil || line != "HTTP/1.1 100 Continue\r\n" {
			t.Fatalf("body never entered handler: %q %v", line, e)
		}
		if line, e = reader.ReadString('\n'); e != nil || line != "\r\n" {
			t.Fatalf("100 headers: %q %v", line, e)
		}
		if _, e = engine.SwitchFixture(context.Background(), j.State().Operation); e == nil {
			t.Fatal("inflight write switched")
		}
		if j.State().Phase != "PREPARED" {
			t.Fatal(j.State().Phase)
		}
		checkHTTP(t, d, http.MethodGet, 200)
		checkLocked(t, j.State().Data)
		t.Log("actual incomplete HTTP body blocked drain; stable read health retained")
	})
	for _, stage := range []string{"QUIESCED", "COMMIT_EXIT"} {
		t.Run("lost_"+stage+"_ACK", func(t *testing.T) {
			engine, d, j := newFixture(t, "")
			s := j.State()
			p := processIn(s)
			if stage == "QUIESCED" {
				c, e := d.connection(p)
				if e != nil {
					t.Fatal(e)
				}
				f := DrainFrame{Kind: "QUIESCE", Operation: s.Operation, Epoch: s.Epoch, Root: s.Data, Nonce: ReleaseDigest("drop-quiesced")}
				s.Phase = "DRAIN_UNKNOWN"
				s.DrainNonce = f.Nonce
				if e = j.Append(s); e != nil {
					t.Fatal(e)
				}
				if e = d.send(c, f); e != nil {
					t.Fatal(e)
				}
				// Read-and-discard models a reply lost before the supervisor records it.
				if r, e := d.read(c, f); e != nil || r.Kind != "QUIESCED" {
					t.Fatalf("quiesce %v %v", r, e)
				}
				c.Close()
			} else {
				proof, e := d.Drain(context.Background(), p, s.Operation)
				if e != nil {
					t.Fatal(e)
				}
				s = j.State()
				s.DrainReceipt = proof
				s.Phase = "DRAINED"
				if e = j.Append(s); e != nil {
					t.Fatal(e)
				}
				c, e := d.connection(p)
				if e != nil {
					t.Fatal(e)
				}
				s.Phase = "EXIT_UNKNOWN"
				if e = j.Append(s); e != nil {
					t.Fatal(e)
				}
				f := d.frame
				f.Kind = "COMMIT_EXIT"
				if e = d.send(c, f); e != nil {
					t.Fatal(e)
				}
				if r, e := d.read(c, f); e != nil || r.Kind != "COMMIT_READY" {
					t.Fatalf("commit %v %v", r, e)
				}
				c.Close() // EXIT_ACK deliberately absent.
			}
			checkHTTP(t, d, http.MethodGet, 200)
			checkHTTP(t, d, http.MethodPost, 503)
			checkLocked(t, s.Data)
			if alive, e := d.Alive(p); e != nil || !alive {
				t.Fatalf("identity lost %v %v", alive, e)
			}
			if _, e := engine.SwitchFixture(context.Background(), s.Operation); e == nil {
				t.Fatal("unknown switch repeated")
			}
			if e := d.Stop(p); e == nil {
				t.Fatal("unknown stop repeated")
			}
			if _, e := d.Start(exe, s.Operation, s.Data); e == nil {
				t.Fatal("unknown start repeated")
			}
			if _, e := engine.Reconcile(); e == nil {
				t.Fatal("unknown phase reconciled as success")
			}
			phase := j.State().Phase
			if e := j.Close(); e != nil {
				t.Fatal(e)
			}
			j2, e := OpenReleaseJournal(j.root)
			if e != nil {
				t.Fatal(e)
			}
			defer j2.Close()
			if j2.State().Phase != phase || processIn(j2.State()) != p {
				t.Fatal("durable unknown identity changed")
			}
			t.Logf("lost %s retains process=%+v root lease and durable phase=%s", stage, p, phase)
		})
	}
}

//go:build windows

package protectedstore

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/adapters/decision"
	holdout "researchos.local/research-os/evaluation/holdout/jev"
)

func frozenAssert(t *testing.T, id string, expected, actual any) {
	t.Helper()
	status := "PASS"
	if !reflect.DeepEqual(expected, actual) {
		status = "FAIL"
	}
	row, _ := json.Marshal(map[string]any{"assertion_id": id, "expected": expected, "actual": actual, "status": status, "scope": "PUBLIC_FIXTURE_ONLY", "formal_holdout_accessed": false, "real_provider_called": false})
	fmt.Println("FROZEN_ASSERTION " + string(row))
	if status != "PASS" {
		t.Fatal(id)
	}
}
func frozenFixture(t *testing.T) (*CanaryStore, frozenGenerator, frozenBatch) {
	t.Helper()
	s, e := NewCanary(filepath.Join(t.TempDir(), "private"))
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { s.Close() })
	convert := func(batch holdout.Batch) (frozenBatch, error) {
		if batch.Split != holdout.PublicFixtureSplit || holdout.Validate(batch) != nil {
			return frozenBatch{}, ErrIntegrity
		}
		out := frozenBatch{Raw: decision.Encode(batch)}
		for _, c := range batch.Cases {
			out.Cases = append(out.Cases, frozenCase{ID: c.ID, Scope: c.Scope, Request: c.Request, Expected: c.Expected, Critical: c.Critical})
		}
		return out, nil
	}
	g := frozenGenerator{Generate: func() (frozenBatch, error) {
		b, e := holdout.GeneratePublicFixture()
		if e != nil {
			return frozenBatch{}, e
		}
		return convert(b)
	}, Restore: func(raw []byte) (frozenBatch, error) {
		var b holdout.Batch
		if decision.Strict(raw, &b) != nil {
			return frozenBatch{}, ErrIntegrity
		}
		return convert(b)
	}}
	batch, e := g.Generate()
	if e != nil {
		t.Fatal(e)
	}
	return s, g, batch
}
func fixtureResponse(choice string) []byte {
	p := map[string]float64{"ACCEPT": .01, "REJECT": .99}
	if choice == "ACCEPT" {
		p = map[string]float64{"ACCEPT": .99, "REJECT": .01}
	}
	confidence := .96
	zero := int64(0)
	return decision.Encode(decision.Response{Model: holdout.ModelRevision, Usage: decision.Usage{InputTokens: &zero, OutputTokens: &zero}, Answers: map[string]decision.Answer{"action": {Type: "choice", Choice: &choice, Confidence: &confidence, Probabilities: p}}})
}
func fixtureEnvelope(c frozenCase) decision.Envelope {
	raw := fixtureResponse(c.Expected)
	return decision.Envelope{Version: 1, Binding: frozenBinding(c), Request: c.Request, RequestHash: decision.Digest(decision.Encode(c.Request)), Response: raw, ResponseHash: decision.Digest(raw), HTTPStatus: 200, MeasurementMode: "FIXTURE"}
}

func TestFrozenSingleRunAndNoProgressLeak(t *testing.T) {
	s, g, batch := frozenFixture(t)
	var generated atomic.Int64
	original := g.Generate
	g.Generate = func() (frozenBatch, error) { generated.Add(1); return original() }
	var requests atomic.Int64
	second := make(chan struct{})
	release := make(chan struct{})
	var releaseOnce sync.Once
	releaseHeld := func() { releaseOnce.Do(func() { close(release) }) }
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		i := int(requests.Add(1) - 1)
		if i >= 30 {
			t.Error("budget exceeded")
			http.Error(w, "budget", 500)
			return
		}
		var request decision.Request
		body, _ := io.ReadAll(io.LimitReader(r.Body, 1<<20))
		if decision.Strict(body, &request) != nil {
			t.Error("unexpected request body")
		}
		intentRaw, e := s.readFile(intentName(i), 4096)
		var intent callIntent
		if e != nil || decision.Strict(intentRaw, &intent) != nil || intent.RequestHash != decision.Digest(body) {
			t.Error("network IO preceded durable intent")
		}
		if !bytes.Equal(body, decision.Encode(batch.Cases[i].Request)) {
			t.Error("candidate saw something other than frozen request")
		}
		if i == 1 {

			close(second)
			<-release
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write(fixtureResponse(batch.Cases[i].Expected))
	}))
	defer server.Close()
	defer releaseHeld()
	transport := server.Client().Transport.(*http.Transport).Clone()
	transport.DisableKeepAlives = true
	client := decision.Client{Fixture: true, URL: server.URL, HTTP: &http.Client{Transport: transport}, Timeout: 10 * time.Second}
	engine := newFrozenEngine(context.Background(), s, g, func() (frozenCall, error) { return client.Call, nil })
	initial := engine.start()
	select {
	case <-second:
	case <-time.After(3 * time.Second):
		t.Fatal("second request did not start")
	}
	whileRunning := engine.snapshot()
	frozenAssert(t, "FROZEN-NO-RUNNING-COUNTS", []any{"RUNNING", int64(0), 0, true}, []any{whileRunning.Frozen.RunState, whileRunning.Total, len(whileRunning.Frozen.Keys), reflect.DeepEqual(initial, whileRunning)})
	for i := 0; i < 5; i++ {
		engine.start()
	}
	frozenAssert(t, "FROZEN-REPEATED-START-SAME-RUN", []int64{1, 2}, []int64{generated.Load(), requests.Load()})
	releaseHeld()
	engine.wait()
	terminal := engine.snapshot()
	frozenAssert(t, "FROZEN-30-BOUNDED-PRIVATE-RESULTS", []any{int64(30), int64(30), int64(30), "COMPLETED", "FAILED", "ADVISORY"}, []any{requests.Load(), terminal.Total, terminal.Correct, terminal.Frozen.RunState, terminal.Frozen.Qualification, terminal.MaximumMode})
	frozenAssert(t, "FROZEN-PER-KEY-15-FROZEN-NEW-DEV", []int64{15, 15, 30, 30}, []int64{terminal.Frozen.Keys[0].StartedRequests, terminal.Frozen.Keys[1].StartedRequests, terminal.Frozen.Keys[0].DevelopmentCount, terminal.Frozen.Keys[1].DevelopmentCount})
	raw, e := s.readFile(terminalFile, 4096)
	if e != nil {
		t.Fatal(e)
	}
	frozenAssert(t, "FROZEN-SUMMARY-4096-BOUND", true, len(raw) <= 4096)
	t.Logf("terminal aggregate bytes=%d limit=4096", len(raw))
	frozenAssert(t, "FROZEN-DATASET-TERMINAL-HASH", []any{true, decision.Digest(batch.Raw), int64(len(batch.Raw))}, []any{terminal.Frozen.Dataset.Valid(), terminal.Frozen.Dataset.Hash, terminal.Frozen.Dataset.Size})
	frozenAssert(t, "FROZEN-SUMMARY-NO-PRIVATE-FIELDS", false, bytes.Contains(raw, []byte("source_documents")) || bytes.Contains(raw, []byte("truth_hash")) || bytes.Contains(raw, []byte("seed")))
	restarted := newFrozenEngine(context.Background(), s, g, func() (frozenCall, error) {
		t.Error("terminal restart accessed call factory")
		return nil, ErrUnavailable
	})
	restarted.start()
	frozenAssert(t, "FROZEN-TERMINAL-RESTART-NO-RECALL", []any{int64(30), true}, []any{requests.Load(), reflect.DeepEqual(terminal, restarted.snapshot())})
}

func TestFrozenCrashConsumesUnknownRequest(t *testing.T) {
	s, g, batch := frozenFixture(t)
	for name, value := range map[string]any{
		runMarkerFile:   runMarker{Schema: "researchos.frozen-run.v1", PlanHash: frozenPlanHash(), StartedAt: time.Now().UTC().Format(time.RFC3339Nano)},
		batchCommitFile: batchCommit{Hash: decision.Digest(batch.Raw)},
	} {
		if e := s.createFile(name, decision.Encode(value)); e != nil {
			t.Fatal(e)
		}
	}
	if e := s.createFile(batchFile, batch.Raw); e != nil {
		t.Fatal(e)
	}
	for i := 0; i < 2; i++ {
		c := batch.Cases[i]
		if e := s.createFile(intentName(i), decision.Encode(callIntent{Index: i, ID: c.ID, Language: c.Scope.Language, RequestHash: decision.Digest(decision.Encode(c.Request))})); e != nil {
			t.Fatal(e)
		}
	}
	if e := s.createFile(envelopeName(1), decision.Encode(fixtureEnvelope(batch.Cases[1]))); e != nil {
		t.Fatal(e)
	}
	var calls atomic.Int64
	engine := newFrozenEngine(context.Background(), s, g, func() (frozenCall, error) { calls.Add(1); return nil, ErrUnavailable })
	terminal := engine.start()
	unknown := terminal.Frozen.Keys[0].UnknownRequests + terminal.Frozen.Keys[1].UnknownRequests
	frozenAssert(t, "FROZEN-CRASH-NO-REPLAY", []any{int64(0), "INTERRUPTED", int64(2), int64(1), int64(1), "FAILED"}, []any{calls.Load(), terminal.Frozen.RunState, terminal.Total, unknown, terminal.Abstain, terminal.Frozen.Qualification})
	frozenAssert(t, "FROZEN-CRASH-TERMINAL-DURABLE", true, privateExists(s, terminalFile))
}

func TestFrozenCredentialBoundary(t *testing.T) {
	s, _, _ := frozenFixture(t)
	sample := []byte("SYNTHETIC-CREDENTIAL-NOT-A-PROVIDER-KEY")
	if e := s.saveServiceCredential(sample); e != nil {
		t.Fatal(e)
	}
	raw, e := s.readFile(serviceCredentialFile, 16384)
	if e != nil {
		t.Fatal(e)
	}
	restored, e := s.loadServiceCredential()
	frozenAssert(t, "FROZEN-CREDENTIAL-DPAPI-PRIVATE", []bool{true, true, false}, []bool{e == nil, bytes.Equal(restored, sample), bytes.Contains(raw, sample)})
	wipe(restored)
	frozenAssert(t, "FROZEN-CREDENTIAL-WRITE-ONCE", true, s.saveServiceCredential(sample) != nil)
	frozenAssert(t, "FROZEN-CREDENTIAL-DOES-NOT-START", false, privateExists(s, runMarkerFile))
	if e = os.WriteFile(filepath.Join(s.root, serviceCredentialFile), []byte("corrupt fixture"), 0600); e != nil {
		t.Fatal(e)
	}
	_, e = s.loadServiceCredential()
	frozenAssert(t, "FROZEN-CREDENTIAL-CORRUPTION", true, e != nil)
	if windows.GetCurrentProcessToken().IsElevated() {
		t.Fatal("requires ordinary unelevated developer")
	}
	name := fmt.Sprintf(`\\.\pipe\ResearchOSConfigACLTest-%d-%d`, os.Getpid(), time.Now().UnixNano())
	h, e := newConfigPipeNamed(name, "S-1-5-80-2827915021-3673354303-1056739677-2648886565-40618300")
	if e != nil {
		t.Fatal(e)
	}
	defer windows.CloseHandle(h)
	client, e := windows.CreateFile(windows.StringToUTF16Ptr(name), pipeClientRights, 0, nil, windows.OPEN_EXISTING, windows.SECURITY_SQOS_PRESENT|windows.SECURITY_IDENTIFICATION, 0)
	if e == nil {
		windows.CloseHandle(client)
	}
	frozenAssert(t, "FROZEN-ADMIN-CONFIG-PIPE-DENIES-DEVELOPER", true, e == windows.ERROR_ACCESS_DENIED)
}

func TestFrozenSummaryRejectsAuthorityAndProgress(t *testing.T) {
	s := newFrozenSummary("RUNNING")
	s.Total = 1
	s.Abstain = 1
	frozenAssert(t, "FROZEN-RUNNING-SCORE-REJECTED", true, s.Validate() != nil)
	s = newFrozenSummary("RUNNING")
	s.MaximumMode = "BOUNDED_AUTO"
	frozenAssert(t, "FROZEN-AUTO-AUTHORITY-REJECTED", true, s.Validate() != nil)
	s = newFrozenSummary("READY")
	s.Frozen.Threshold = .7
	frozenAssert(t, "FROZEN-THRESHOLD-DRIFT-REJECTED", true, s.Validate() != nil)
}

func TestFrozenConfigurationProtocol(t *testing.T) {
	s, g, _ := frozenFixture(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	engine := newFrozenEngine(ctx, s, g, func() (frozenCall, error) {
		raw, err := s.loadServiceCredential()
		wipe(raw)
		if err != nil {
			return nil, err
		}
		return func(context.Context, decision.Binding, decision.Request) (decision.Envelope, error) {
			t.Error("configuration called provider")
			return decision.Envelope{}, ErrUnavailable
		}, nil
	})
	boundary, _ := s.Boundary(ctx)
	name := fmt.Sprintf(`\\.\pipe\ResearchOSConfigProtocol-%d-%d`, os.Getpid(), time.Now().UnixNano())
	h, err := newConfigPipeNamed(name, boundary.OwnerSID)
	if err != nil {
		t.Fatal(err)
	}
	defer windows.CloseHandle(h)
	done := make(chan struct{})
	go func() { defer close(done); serveConfigPipe(ctx, h, engine) }()
	defer func() { cancel(); <-done }()
	client, err := windows.CreateFile(windows.StringToUTF16Ptr(name), pipeClientRights, 0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OVERLAPPED|windows.SECURITY_SQOS_PRESENT|windows.SECURITY_IDENTIFICATION, 0)
	if err != nil {
		t.Fatal(err)
	}
	file := os.NewFile(uintptr(client), "fixture-config-pipe")
	defer file.Close()
	if file.SetDeadline(time.Now().Add(3*time.Second)) != nil {
		t.Fatal("deadline")
	}
	if _, err = file.Write([]byte(configPrefix + "SYNTHETIC-PIPE-TEST")); err != nil {
		t.Fatal(err)
	}
	reply := make([]byte, 128)
	n, err := file.Read(reply)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = file.Write([]byte("ack")); err != nil {
		t.Fatal(err)
	}
	frozenAssert(t, "FROZEN-CONFIG-NATIVE-HANDOFF-NO-AUTORUN", []any{"configured-v1", "READY", false}, []any{string(reply[:n]), engine.snapshot().Frozen.RunState, privateExists(s, runMarkerFile)})
	frozenAssert(t, "FROZEN-CONFIG-SECOND-HANDOFF-REFUSED", true, engine.installCredential([]byte("OTHER-SYNTHETIC")) != nil)
}
func TestFrozenInvalidBindingsAndCancelledRun(t *testing.T) {
	s, g, b := frozenFixture(t)
	ctx, cancel := context.WithCancel(context.Background())
	calls := 0
	engine := newFrozenEngine(ctx, s, g, func() (frozenCall, error) {
		return func(context.Context, decision.Binding, decision.Request) (decision.Envelope, error) {
			calls++
			env := fixtureEnvelope(b.Cases[0])
			env.Binding.InputHash = decision.Digest([]byte("mismatch"))
			cancel()
			return env, nil
		}, nil
	})
	engine.start()
	engine.wait()
	summary := engine.snapshot()
	frozenAssert(t, "FROZEN-CANCEL-NO-NEXT-CALL", []any{1, "INTERRUPTED", int64(1), int64(1)}, []any{calls, summary.Frozen.RunState, summary.Total, summary.Abstain})
	frozenAssert(t, "FROZEN-BINDING-MISMATCH-ERROR", int64(1), summary.Frozen.Keys[0].Errors+summary.Frozen.Keys[1].Errors)
}

func TestFrozenProviderNeverReads(t *testing.T) {
	p := &FrozenProvider{}
	raw, err := p.Read(context.Background(), Blob{})
	frozenAssert(t, "FROZEN-PROVIDER-READ-ALWAYS-DENIED", []bool{true, true}, []bool{len(raw) == 0, err == ErrIsolation})
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	frozenAssert(t, "FROZEN-PROVIDER-NONLIVE-READY-DENIED", true, p.Ready(context.Background(), "FIXTURE") == ErrBoundary)
	frozenAssert(t, "FROZEN-PROVIDER-CANCELLED-READY-DENIED", true, p.Ready(ctx, "LIVE") != nil)
}

package main

import (
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"strings"
	"sync"
	"testing"
	"time"
)

type spyConn struct {
	mu             sync.Mutex
	writes, closes int
	read           *strings.Reader
	port           int
}

func (c *spyConn) Read(p []byte) (int, error) {
	if c.read == nil {
		return 0, io.EOF
	}
	return c.read.Read(p)
}
func (c *spyConn) Write(p []byte) (int, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.writes++
	return len(p), nil
}
func (c *spyConn) Close() error        { c.mu.Lock(); c.closes++; c.mu.Unlock(); return nil }
func (c *spyConn) LocalAddr() net.Addr { return &net.TCPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 52117} }
func (c *spyConn) RemoteAddr() net.Addr {
	p := c.port
	if p == 0 {
		p = 43861
	}
	return &net.TCPAddr{IP: net.IPv4(127, 0, 0, 1), Port: p}
}
func (c *spyConn) SetDeadline(time.Time) error      { return nil }
func (c *spyConn) SetReadDeadline(time.Time) error  { return nil }
func (c *spyConn) SetWriteDeadline(time.Time) error { return nil }
func serverRow(t socketTuple, pid uint32) tcpOwnerRow {
	return tcpOwnerRow{state: 5, localIP: t.serverIP, remoteIP: t.clientIP, localPort: t.serverPort, remotePort: t.clientPort, pid: pid}
}
func TestConnectedReplacementCannotReceiveHTTP(t *testing.T) {
	c := &spyConn{}
	proof := connectionProof{dial: func(context.Context, string, string) (net.Conn, error) { return c, nil }, rows: func(tuple socketTuple) ([]tcpOwnerRow, error) {
		ownedListener := serverRow(tuple, 7)
		ownedListener.state = 2
		return []tcpOwnerRow{ownedListener, serverRow(tuple, 99)}, nil
	}, owned: func(_ context.Context, pid uint32) error {
		if pid != 7 {
			return errors.New("foreign connected owner")
		}
		return nil
	}}
	transport := &http.Transport{Proxy: nil, DisableKeepAlives: true, DialContext: proof.DialContext}
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport, Timeout: time.Second}
	if _, e := client.Get("http://127.0.0.1:43861/api/version"); e == nil {
		t.Fatal("replacement accepted")
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.writes != 0 || c.closes != 1 {
		t.Fatalf("HTTP reached foreign socket or socket leaked: writes=%d closes=%d", c.writes, c.closes)
	}
}
func TestTupleProofRejectsMissingAmbiguousOrListenerOnly(t *testing.T) {
	for _, kind := range []string{"missing", "ambiguous", "listener-only", "wrong-client-port", "lookup-error"} {
		t.Run(kind, func(t *testing.T) {
			c := &spyConn{}
			proof := connectionProof{dial: func(context.Context, string, string) (net.Conn, error) { return c, nil }, rows: func(tuple socketTuple) ([]tcpOwnerRow, error) {
				r := serverRow(tuple, 7)
				switch kind {
				case "missing":
					return nil, nil
				case "ambiguous":
					return []tcpOwnerRow{r, r}, nil
				case "listener-only":
					r.state = 2
				case "wrong-client-port":
					r.remotePort++
				case "lookup-error":
					return nil, errors.New("query unavailable")
				}
				return []tcpOwnerRow{r}, nil
			}, owned: func(context.Context, uint32) error { return nil }}
			if _, e := proof.DialContext(context.Background(), "tcp", "127.0.0.1:43861"); e == nil {
				t.Fatal("missing actual-tuple proof accepted")
			}
			if c.writes != 0 || c.closes != 1 {
				t.Fatal("failed proof leaked or wrote")
			}
		})
	}
}
func TestActualTupleIsUsedBeforeOwnedConnectionReturned(t *testing.T) {
	c := &spyConn{read: strings.NewReader("HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")}
	checked := false
	proof := connectionProof{dial: func(context.Context, string, string) (net.Conn, error) { return c, nil }, rows: func(tuple socketTuple) ([]tcpOwnerRow, error) {
		if tuple.clientPort != 52117 || tuple.serverPort != 43861 {
			t.Fatal("not actual connected tuple")
		}
		return []tcpOwnerRow{serverRow(tuple, 7)}, nil
	}, owned: func(context.Context, uint32) error {
		if c.writes != 0 {
			t.Fatal("HTTP bytes before owner validation")
		}
		checked = true
		return nil
	}}
	conn, e := proof.DialContext(context.Background(), "tcp", "127.0.0.1:43861")
	if e != nil || !checked || conn != c {
		t.Fatal("proved connection not returned")
	}
	if _, e = conn.Write([]byte("GET /api/version HTTP/1.1\r\n\r\n")); e != nil || c.writes != 1 {
		t.Fatal("proved connection unusable")
	}
	conn.Close()
}
func TestCanceledOrWrongEndpointProofClosesWithoutWrite(t *testing.T) {
	for _, wrong := range []bool{false, true} {
		c := &spyConn{}
		if wrong {
			c.port = 11435
		}
		ctx, cancel := context.WithCancel(context.Background())
		proof := connectionProof{dial: func(context.Context, string, string) (net.Conn, error) { return c, nil }, rows: func(tuple socketTuple) ([]tcpOwnerRow, error) { return []tcpOwnerRow{serverRow(tuple, 7)}, nil }, owned: func(context.Context, uint32) error { cancel(); return nil }}
		if _, e := proof.DialContext(ctx, "tcp", "127.0.0.1:43861"); e == nil {
			t.Fatal("canceled/wrong-endpoint connection returned")
		}
		cancel()
		if c.writes != 0 || c.closes != 1 {
			t.Fatal("bad socket leaked or wrote")
		}
	}
}

type fakeKernel struct {
	mu                                     sync.Mutex
	active                                 uint32
	stuck, gap, closed                     bool
	terminateCalls, closeCalls, afterClose int
	closedAt                               time.Time
}

func (k *fakeKernel) check() {
	if k.closed {
		k.afterClose++
	}
}
func (k *fakeKernel) Create() (processRecord, error) {
	k.mu.Lock()
	defer k.mu.Unlock()
	k.check()
	k.active = 1
	return processRecord{PID: 7, HandleHeld: true, InJob: true}, nil
}
func (k *fakeKernel) Resume() error { k.mu.Lock(); defer k.mu.Unlock(); k.check(); return nil }
func (k *fakeKernel) Poll(d time.Duration) error {
	time.Sleep(d)
	k.mu.Lock()
	defer k.mu.Unlock()
	k.check()
	return nil
}
func (k *fakeKernel) ValidatePID(uint32) error {
	k.mu.Lock()
	defer k.mu.Unlock()
	k.check()
	return nil
}
func (k *fakeKernel) State() kernelState {
	k.mu.Lock()
	defer k.mu.Unlock()
	k.check()
	return kernelState{Total: 1, Active: k.active, PrimarySignaled: k.active == 0, Complete: k.active == 0 && !k.gap}
}
func (k *fakeKernel) Terminate() error {
	k.mu.Lock()
	defer k.mu.Unlock()
	k.check()
	k.terminateCalls++
	if !k.stuck {
		k.active = 0
		return nil
	}
	return errors.New("injected terminate failure")
}
func (k *fakeKernel) Close() closeProof {
	k.mu.Lock()
	defer k.mu.Unlock()
	k.check()
	k.closeCalls++
	k.closed = true
	k.closedAt = time.Now()
	return closeProof{JobClosed: true, PrimarySignaled: k.active == 0}
}
func awaitOutcome(t *testing.T, o *kernelOwner) ownerOutcome {
	t.Helper()
	select {
	case out := <-o.out:
		return out
	case <-time.After(2 * time.Second):
		t.Fatal("owner cleanup blocked")
		return ownerOutcome{}
	}
}
func TestStalledDiagnosticCannotPostponeJobClose(t *testing.T) {
	blocked := make(chan struct{})
	diagDone := make(chan struct{})
	go func() { <-blocked; close(diagDone) }()
	defer func() { close(blocked); <-diagDone }()
	k := &fakeKernel{stuck: true}
	start := time.Now()
	o := startOwner(k, ownerPolicy{Native: 20 * time.Millisecond, Cleanup: 30 * time.Millisecond})
	<-o.started
	out := awaitOutcome(t, o)
	if time.Since(start) > time.Second || !out.Close.JobClosed || out.CleanupProved {
		t.Fatal("stalled diagnostic/failed terminate blocked fail-safe or became success")
	}
	k.mu.Lock()
	defer k.mu.Unlock()
	if k.closeCalls != 1 {
		t.Fatal("final close not exactly once")
	}
}
func TestLateTimeoutOrStopCannotUseClosedJob(t *testing.T) {
	k := &fakeKernel{}
	o := startOwner(k, ownerPolicy{Native: 40 * time.Millisecond, Cleanup: 20 * time.Millisecond})
	<-o.started
	o.stopOnce("metadata complete")
	out := awaitOutcome(t, o)
	if !out.CleanupProved {
		t.Fatalf("fixture cleanup failed: %+v", out)
	}
	time.Sleep(100 * time.Millisecond)
	o.stopOnce("late cancellation")
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	if e := o.request(ctx, "validate", 7); e == nil {
		t.Fatal("closed owner admitted validation")
	}
	k.mu.Lock()
	defer k.mu.Unlock()
	if k.afterClose != 0 || k.closeCalls != 1 || k.terminateCalls != 1 {
		t.Fatalf("late handle use: after=%d close=%d terminate=%d", k.afterClose, k.closeCalls, k.terminateCalls)
	}
}
func TestTrackingOrStreamGapNeverClaimsPostStopIntegrity(t *testing.T) {
	k := &fakeKernel{gap: true}
	o := startOwner(k, ownerPolicy{Native: time.Second, Cleanup: 20 * time.Millisecond})
	<-o.started
	o.stopOnce("metadata complete")
	out := awaitOutcome(t, o)
	if out.CleanupProved || canVerifyPostStop(out, true, false) {
		t.Fatal("tracking gap became post-stop integrity")
	}
	good := ownerOutcome{CleanupProved: true, State: kernelState{Active: 0}, Close: closeProof{JobClosed: true, PrimarySignaled: true}}
	if canVerifyPostStop(good, false, false) || canVerifyPostStop(good, true, true) {
		t.Fatal("undrained/overflow stream admitted")
	}
}

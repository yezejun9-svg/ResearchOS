//go:build windows

package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"os"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/ops/supervisor"
	"sync"
	"time"
)

// drainGate closes the HTTP mutation ingress before the coordinator scan gate
// and SQLite/effect checks. It does not expose a public drain endpoint.
type drainGate struct {
	mu       sync.Mutex
	quiesced bool
	closing  bool
	inflight int
	requests sync.WaitGroup
}

func (g *drainGate) Wrap(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		g.mu.Lock()
		if g.closing {
			g.mu.Unlock()
			http.Error(w, "control closing", http.StatusServiceUnavailable)
			return
		}
		g.requests.Add(1)
		g.mu.Unlock()
		defer g.requests.Done()
		write := r.Method != http.MethodGet && r.Method != http.MethodHead && r.Method != http.MethodOptions
		if write {
			g.mu.Lock()
			if g.quiesced {
				g.mu.Unlock()
				http.Error(w, "control quiesced", http.StatusServiceUnavailable)
				return
			}
			g.inflight++
			g.mu.Unlock()
			defer func() { g.mu.Lock(); g.inflight--; g.mu.Unlock() }()
		}
		next.ServeHTTP(w, r)
	})
}

func (g *drainGate) Quiesce() error {
	g.mu.Lock()
	defer g.mu.Unlock()
	if g.quiesced {
		return errors.New("control already quiesced")
	}
	g.quiesced = true
	if g.inflight != 0 {
		g.quiesced = false
		return errors.New("control has in-flight HTTP writes")
	}
	return nil
}
func (g *drainGate) Resume() { g.mu.Lock(); g.quiesced = false; g.mu.Unlock() }

func (g *drainGate) Close() {
	g.mu.Lock()
	g.closing = true
	g.mu.Unlock()
	g.requests.Wait()
}

type controlDrain struct {
	gate                      *drainGate
	service                   *domain.Service
	coordinator               *domain.RuntimeCoordinator
	lease                     *rt.DataRootLease
	listener                  net.Listener
	startup                   *supervisor.DrainBootstrap
	pipe, root                string
	key                       []byte
	peer                      supervisor.ProcessIdentity
	stop                      func()
	mu                        sync.Mutex
	operation, nonce, receipt string
	epoch                     uint64
}

func (d *controlDrain) observe(ctx context.Context) (domain.RuntimeDrainSnapshot, error) {
	snap, e := d.service.RuntimeDrainSnapshot(ctx)
	if e != nil {
		return snap, e
	}
	if snap.ActiveRuns != 0 || snap.UnresolvedEffects != 0 || snap.UnresolvedDispatches != 0 || snap.ActiveWorkers != 0 || snap.Reservations != 0 {
		return snap, errors.New("control has active Run or unresolved external effect")
	}
	return snap, nil
}

func (d *controlDrain) quiesce(ctx context.Context, frame supervisor.DrainFrame) (string, error) {
	if e := d.gate.Quiesce(); e != nil {
		return "", e
	}
	resume := true
	coordinatorQuiesced := false
	defer func() {
		if resume {
			d.gate.Resume()
			if coordinatorQuiesced {
				d.coordinator.ResumeAfterReleaseAbort()
			}
		}
	}()
	var snap domain.RuntimeDrainSnapshot
	var e error
	if d.coordinator != nil {
		snap, e = d.coordinator.QuiesceForRelease(ctx)
	} else {
		snap, e = d.observe(ctx)
	}
	if e != nil {
		return "", e
	}
	coordinatorQuiesced = d.coordinator != nil
	if snap, e = d.observe(ctx); e != nil {
		return "", e
	}
	var busy, logged, checkpointed int
	if e = d.service.DB.QueryRowContext(ctx, "PRAGMA wal_checkpoint(FULL)").Scan(&busy, &logged, &checkpointed); e != nil || busy != 0 {
		return "", errors.New("authority SQLite checkpoint not idle")
	}
	snap.CheckpointBusy = busy
	identity, e := supervisor.ObserveProcess(uint32(os.Getpid()))
	if e != nil {
		return "", e
	}
	receipt := supervisor.ReleaseDigest(struct {
		Operation            string
		Epoch                uint64
		Nonce, Root          string
		Process              supervisor.ProcessIdentity
		Snapshot             domain.RuntimeDrainSnapshot
		Logged, Checkpointed int
	}{frame.Operation, frame.Epoch, frame.Nonce, d.root, identity, snap, logged, checkpointed})
	d.operation, d.epoch, d.nonce, d.receipt = frame.Operation, frame.Epoch, frame.Nonce, receipt
	resume = false
	return receipt, nil
}

func (d *controlDrain) response(kind string, frame supervisor.DrainFrame, receipt, state string) supervisor.DrainFrame {
	reply, _ := supervisor.DrainFrameSign(d.key, supervisor.DrainFrame{Kind: kind, Operation: frame.Operation, Epoch: frame.Epoch, Root: d.root, Nonce: frame.Nonce, Receipt: receipt, State: state})
	return reply
}

func (d *controlDrain) handle(ctx context.Context) error {
	conn, e := supervisor.AcceptDrainPipe(ctx, d.pipe, d.peer)
	if e != nil {
		return e
	}
	defer conn.Close()
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	if e = conn.SetDeadline(time.Now().Add(5 * time.Second)); e != nil {
		return e
	}
	frame, e := supervisor.ReadDrainFrame(conn)
	if e != nil {
		return e
	}
	if !supervisor.DrainFrameValid(d.key, frame) || frame.Operation == "" || frame.Epoch == 0 || frame.Root != d.root || frame.Nonce == "" {
		return errors.New("drain capability or binding invalid")
	}
	d.mu.Lock()
	defer d.mu.Unlock()
	switch frame.Kind {
	case "READY":
		if d.startup == nil || frame.Operation != d.startup.Token || frame.Epoch != d.startup.Epoch || ctx.Err() != nil {
			return errors.New("startup readiness binding changed")
		}
		if d.coordinator != nil && !d.coordinator.StartupReady() {
			return supervisor.WriteDrainFrame(conn, d.response("BUSY", frame, "", "STARTING"))
		}
		d.gate.mu.Lock()
		available := !d.gate.closing && !d.gate.quiesced
		d.gate.mu.Unlock()
		if !available || !d.lease.Held() || d.lease.Root() != d.root || d.listener == nil || d.listener.Addr().String() != d.startup.Listener {
			return errors.New("control listener or lease not ready")
		}
		identity, err := supervisor.ObserveProcess(uint32(os.Getpid()))
		if err != nil {
			return err
		}
		reply := d.response("READY", frame, "", "READY")
		reply.Readiness = &supervisor.DrainReadiness{Process: identity, Listener: d.listener.Addr().String(), LeaseHeld: true, StartupComplete: true}
		reply, err = supervisor.DrainFrameSign(d.key, reply)
		if err != nil {
			return err
		}
		return supervisor.WriteDrainFrame(conn, reply)
	case "QUIESCE":
		if d.operation != "" {
			return errors.New("another control drain is pending")
		}
		receipt, err := d.quiesce(ctx, frame)
		if err != nil {
			_ = supervisor.WriteDrainFrame(conn, d.response("BUSY", frame, "", "STABLE"))
			return nil
		}
		return supervisor.WriteDrainFrame(conn, d.response("QUIESCED", frame, receipt, "QUIESCED"))
	case "RESUME":
		if d.operation != frame.Operation || d.epoch != frame.Epoch || d.nonce != frame.Nonce || d.receipt != frame.Receipt {
			return errors.New("resume binding changed")
		}
		d.gate.Resume()
		if d.coordinator != nil {
			d.coordinator.ResumeAfterReleaseAbort()
		}
		d.operation, d.nonce, d.receipt = "", "", ""
		d.epoch = 0
		return supervisor.WriteDrainFrame(conn, d.response("RESUMED", frame, "", "STABLE"))
	case "COMMIT_EXIT":
		if d.operation != frame.Operation || d.epoch != frame.Epoch || d.nonce != frame.Nonce || d.receipt != frame.Receipt {
			return errors.New("commit exit binding changed")
		}
		if _, err := d.observe(ctx); err != nil {
			return err
		}
		ready := d.response("COMMIT_READY", frame, d.receipt, "QUIESCED")
		if err := supervisor.WriteDrainFrame(conn, ready); err != nil {
			return err
		}
		// The control retains its PID, lease and quiesce fence if this ACK is lost.
		confirm, err := supervisor.ReadDrainFrame(conn)
		if err != nil {
			return err
		}
		if !supervisor.DrainFrameValid(d.key, confirm) || confirm.Kind != "EXIT_ACK" || confirm.Root != d.root || confirm.Operation != d.operation || confirm.Epoch != d.epoch || confirm.Nonce != d.nonce || confirm.Receipt != d.receipt {
			return errors.New("commit exit acknowledgment invalid")
		}
		if _, err = d.observe(ctx); err != nil {
			return err
		}
		go d.stop()
		return nil
	default:
		return fmt.Errorf("unknown drain action %s", frame.Kind)
	}
}

func (d *controlDrain) Serve(ctx context.Context, onError func(error)) {
	for ctx.Err() == nil {
		if e := d.handle(ctx); e != nil && ctx.Err() == nil && onError != nil {
			onError(e)
		}
	}
}

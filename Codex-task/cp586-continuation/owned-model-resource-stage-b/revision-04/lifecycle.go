package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

type processRecord struct {
	PID           uint32 `json:"pid"`
	CreationTicks string `json:"creation_filetime_decimal"`
	Image         string `json:"image"`
	HandleHeld    bool   `json:"handle_held"`
	InJob         bool   `json:"in_owned_job"`
	NewEvent      bool   `json:"new_process_event"`
	Signaled      bool   `json:"signaled_after_cleanup"`
	ExitCode      uint32 `json:"exit_code"`
}
type kernelState struct {
	Total, Active             uint32
	PrimarySignaled, Complete bool
	Processes                 []processRecord
	Errors                    []string
}
type closeProof struct {
	JobClosed, PrimarySignaled bool
	Errors                     []string
}

// Only the owner loop may call this backend. Implementations must not perform
// file hashing, journal writes, Sync, user callbacks, or diagnostic joins.
type kernelBackend interface {
	Create() (processRecord, error)
	Resume() error
	Poll(time.Duration) error
	ValidatePID(uint32) error
	State() kernelState
	Terminate() error
	Close() closeProof
}
type ownerPolicy struct{ Native, Cleanup time.Duration }
type ownerOutcome struct {
	State           kernelState
	Close           closeProof
	CleanupProved   bool
	CleanupDeadline time.Time
	Error           string
	Primary         processRecord
}
type ownerCommand struct {
	kind  string
	pid   uint32
	reply chan error
}
type stopRequest struct {
	reason   string
	deadline time.Time
}
type kernelOwner struct {
	commands      chan ownerCommand
	stop          chan stopRequest
	started       chan processRecord
	startError    chan error
	done          chan struct{}
	out           chan ownerOutcome
	cleanupBudget time.Duration
}

func startOwner(k kernelBackend, p ownerPolicy) *kernelOwner {
	o := &kernelOwner{commands: make(chan ownerCommand), stop: make(chan stopRequest, 1), started: make(chan processRecord, 1), startError: make(chan error, 1), done: make(chan struct{}), out: make(chan ownerOutcome, 1), cleanupBudget: p.Cleanup}
	go o.loop(k, p)
	return o
}
func (o *kernelOwner) loop(k kernelBackend, p ownerPolicy) {
	// No watchdog goroutine ever receives a Job handle. Timer events are consumed
	// by this one owner, which also performs final Close before publishing done.
	timer := time.NewTimer(p.Native)
	defer timer.Stop()
	defer close(o.done)
	primary, e := k.Create()
	if e != nil {
		o.startError <- e
		o.cleanup(k, time.Now().Add(p.Cleanup), primary, "create: "+e.Error())
		return
	}
	o.started <- primary
	reason := ""
	resumed := false
	var cleanupDeadline time.Time
	for reason == "" {
		select {
		case request := <-o.stop:
			reason = request.reason
			cleanupDeadline = request.deadline
		case <-timer.C:
			reason = "native deadline"
		case c := <-o.commands:
			var err error
			switch c.kind {
			case "resume":
				if resumed {
					err = errors.New("resume already consumed")
				} else {
					err = k.Resume()
					resumed = err == nil
				}
			case "validate":
				err = k.ValidatePID(c.pid)
			default:
				err = errors.New("unknown owner command")
			}
			c.reply <- err
			if err != nil && c.kind == "resume" {
				reason = "resume: " + err.Error()
			}
		default:
			if err := k.Poll(10 * time.Millisecond); err != nil {
				reason = "kernel monitor: " + err.Error()
			}
		}
	}
	if cleanupDeadline.IsZero() {
		cleanupDeadline = time.Now().Add(p.Cleanup)
	}
	o.cleanup(k, cleanupDeadline, primary, reason)
}
func (o *kernelOwner) cleanup(k kernelBackend, deadline time.Time, primary processRecord, reason string) {
	termErr := k.Terminate()
	var s kernelState
	for {
		s = k.State()
		if s.Active == 0 && s.Complete {
			break
		}
		remaining := time.Until(deadline)
		if remaining <= 0 {
			break
		}
		wait := 10 * time.Millisecond
		if remaining < wait {
			wait = remaining
		}
		if err := k.Poll(wait); err != nil {
			s.Errors = append(s.Errors, err.Error())
			break
		}
	}
	// This final fail-safe is unconditional and precedes all diagnostic work.
	// Missing monitor evidence produces failure, never an unbounded join.
	closed := k.Close()
	proved := s.Active == 0 && s.Complete && closed.JobClosed && closed.PrimarySignaled && len(s.Errors) == 0 && len(closed.Errors) == 0
	errText := ""
	if reason != "metadata complete" {
		errText = reason
	}
	if termErr != nil {
		errText = fmt.Sprintf("%s; terminate: %v", errText, termErr)
		proved = false
	}
	if !proved {
		errText += "; kernel cleanup/roster evidence unproved"
	}
	o.out <- ownerOutcome{State: s, Close: closed, CleanupProved: proved, CleanupDeadline: deadline, Error: errText, Primary: primary}
}
func (o *kernelOwner) request(ctx context.Context, kind string, pid uint32) error {
	r := make(chan error, 1)
	select {
	case <-o.done:
		return errors.New("kernel owner already closed")
	case <-ctx.Done():
		return ctx.Err()
	case o.commands <- ownerCommand{kind: kind, pid: pid, reply: r}:
	}
	select {
	case e := <-r:
		return e
	case <-o.done:
		return errors.New("kernel owner closed during request")
	case <-ctx.Done():
		return ctx.Err()
	}
}
func (o *kernelOwner) stopOnce(reason string) time.Time {
	deadline := time.Now().Add(o.cleanupBudget)
	select {
	case <-o.done:
		return deadline
	default:
	}
	select {
	case o.stop <- stopRequest{reason: reason, deadline: deadline}:
	default:
	}
	return deadline
}
func canVerifyPostStop(o ownerOutcome, drained, overflow bool) bool {
	return o.CleanupProved && o.Close.JobClosed && o.Close.PrimarySignaled && o.State.Active == 0 && drained && !overflow
}

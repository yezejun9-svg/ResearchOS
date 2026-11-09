//go:build windows

// cancel_windows.go exposes the child-process half of W05-02 step 4: a worker confined to a job
// object that already exists in this package (created with KILL_ON_JOB_CLOSE, so a worker cannot
// outlive the handle owner), plus one cancel entry point whose order is fixed by the API rather than
// left to the caller: clear the queue, abort the job, wait until it settles, and only then report.
//
// Nothing here re-implements job creation or termination. newJob, launch, jobPIDs, killJob and
// closeJob are this package's own functions, which is why this file lives beside them instead of in a
// caller: a second job-object implementation would be a second answer to "did anything survive?".

package runtime

import (
	"errors"
	"fmt"
	"os"
	"sync"
	"time"

	"golang.org/x/sys/windows"
)

const stillActive = 259

var ErrCancelOrderViolated = errors.New("CANCEL_ORDER_VIOLATED: the queue must be cleared before the job is aborted")

type Child struct {
	mu      sync.Mutex
	job     windows.Handle
	p       *process
	name    string
	queue   []string
	closed  bool
	killed  bool
	dropped int
	files   []*os.File
}

type CancelReport struct {
	JobName       string   `json:"job_name"`
	WorkerPID     uint32   `json:"worker_pid"`
	QueuedDropped int      `json:"queued_dropped"`
	Terminated    bool     `json:"terminated"`
	Settled       bool     `json:"settled"`
	RemainingPIDs []uint32 `json:"remaining_pids"`
	ExitCode      int      `json:"worker_exit_code"`
	Elapsed       int64    `json:"elapsed_ms"`
	Order         []string `json:"order"`
}

// StartChild launches c inside a fresh job object named name. The caller supplies the three child
// stdio handles; they must be distinct, because the pinned launcher publishes an explicit inheritable
// handle list and reusing one handle for two descriptors makes CreateProcess fail.
func StartChild(name string, c Command, env []string, stdout, stderr, stdin *os.File) (*Child, error) {
	if stdout == nil || stderr == nil || stdin == nil {
		return nil, errors.New("NO_CHILD_STDIO_HANDLES")
	}
	job, e := newJob(name)
	if e != nil {
		return nil, fmt.Errorf("JOB_CREATE_FAILED: %w", e)
	}
	p, e := launch(job, c, env, stdin, stdout, stderr)
	if e != nil {
		closeJob(job)
		return nil, fmt.Errorf("CHILD_LAUNCH_FAILED: %w", e)
	}
	return &Child{job: job, p: p, name: name, files: []*os.File{stdin, stdout, stderr}}, nil
}

func (c *Child) PID() uint32 {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.p == nil {
		return 0
	}
	return c.p.pid
}

// Admit is refused once the queue has been cleared, which is what makes "clear_queue then abort"
// observable rather than a comment: a late item cannot slip into a run that is already cancelling.
func (c *Child) Admit(item string) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.killed {
		return ErrCancelOrderViolated
	}
	c.queue = append(c.queue, item)
	return nil
}

// ClearQueue drops everything still waiting and returns how much it dropped.
func (c *Child) ClearQueue() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	n := len(c.queue)
	c.queue = nil
	c.killed = true
	c.dropped += n
	return n
}

// Dropped reports how many queued items the cascade has so far discarded, across repeated clears.
func (c *Child) Dropped() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.dropped
}

func (c *Child) LivePIDs() ([]uint32, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	return jobPIDs(c.job)
}

// Cancel runs the cascade in the required order and reports each step, so a caller cannot claim a
// cancellation that only killed something: it must show the queue cleared, the job terminated, the
// job empty afterwards, and the worker's real exit code.
func (c *Child) Cancel(settle time.Duration) (CancelReport, error) {
	if settle <= 0 {
		return CancelReport{}, errors.New("NO_SETTLE_WINDOW")
	}
	c.mu.Lock()
	if !c.killed {
		c.mu.Unlock()
		return CancelReport{}, ErrCancelOrderViolated
	}
	dropped := c.dropped
	name := c.name
	pid := c.p.pid
	handle := c.p.handle
	job := c.job
	c.mu.Unlock()

	rep := CancelReport{JobName: name, WorkerPID: pid, QueuedDropped: dropped, Order: []string{"clear_queue"}}
	started := time.Now()

	if e := killJob(job); e != nil {
		rep.Order = append(rep.Order, "abort:failed")
		return rep, fmt.Errorf("JOB_TERMINATE_FAILED: %w", e)
	}
	rep.Terminated = true
	rep.Order = append(rep.Order, "abort")

	deadline := time.Now().Add(settle)
	for {
		live, e := jobPIDs(job)
		if e == nil && len(live) == 0 {
			rep.Settled = true
			rep.RemainingPIDs = live
			break
		}
		if time.Now().After(deadline) {
			live, _ := jobPIDs(job)
			rep.RemainingPIDs = live
			rep.Order = append(rep.Order, "settled:timeout")
			return rep, errors.New("CHILD_NOT_SETTLED: processes remain in the job")
		}
		time.Sleep(20 * time.Millisecond)
	}
	var code uint32
	if e := windows.GetExitCodeProcess(handle, &code); e == nil && code != stillActive {
		rep.ExitCode = int(code)
	} else if code == stillActive {
		rep.Order = append(rep.Order, "exit_code:still_active")
	}
	rep.Order = append(rep.Order, "settled", "child_confirmed")
	rep.Elapsed = time.Since(started).Milliseconds()
	return rep, nil
}

// Close releases the job handle. Because the job was created with KILL_ON_JOB_CLOSE, releasing it
// takes any surviving member with it - the property the W05-02 negative test measures from outside by
// killing the parent and then watching whether the worker keeps writing.
func (c *Child) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.closed {
		return
	}
	c.closed = true
	if c.p != nil && c.p.handle != 0 {
		windows.CloseHandle(c.p.handle)
	}
	for _, f := range c.files {
		if f != nil {
			f.Close()
		}
	}
	if c.job != 0 {
		closeJob(c.job)
	}
}

// OpenExistingJob attaches to a named job for read-only inspection, so a test can ask whether any
// member survived a parent that exited without closing anything.
func OpenExistingJob(name string) (windows.Handle, error) { return openJob(name) }

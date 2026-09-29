//go:build windows

// Package runtime manages one already-admitted Run. It never schedules Tasks or accepts results.
package runtime

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"golang.org/x/sys/windows"
)

const Revision = "windows-job-v1"
const HeartbeatInterval = 15 * time.Second
const LeaseDuration = 90 * time.Second

type Command struct {
	Executable string   `json:"executable"`
	Args       []string `json:"args"`
	Directory  string   `json:"directory"`
	Input      string   `json:"-"`
}
type Spec struct {
	RunID       string        `json:"run_id"`
	TaskID      string        `json:"task_id"`
	Epoch       int64         `json:"epoch"`
	Commands    []Command     `json:"commands"`
	Model       string        `json:"model"`
	Environment []string      `json:"-"`
	Lease       time.Duration `json:"-"`
	Timeout     time.Duration `json:"-"`
}
type Tree struct {
	At    string   `json:"at"`
	PIDs  []uint32 `json:"pids"`
	Error string   `json:"error,omitempty"`
}
type Journal struct {
	Spec             Spec     `json:"spec"`
	Revision         string   `json:"adapter_revision"`
	Job              string   `json:"job"`
	State            string   `json:"state"`
	Reason           string   `json:"reason"`
	Worker           string   `json:"worker"`
	PID              uint32   `json:"pid"`
	Created          int64    `json:"process_created_ns"`
	Launched         int      `json:"launched"`
	Pending          int      `json:"pending"`
	Exit             *int     `json:"exit_code"`
	Cancelled        bool     `json:"cancelled"`
	QueueEmpty       bool     `json:"queue_empty"`
	ChildrenStopped  bool     `json:"children_stopped"`
	Started          string   `json:"started"`
	Ended            string   `json:"ended"`
	EnvironmentNames []string `json:"environment_names"`
	Trees            []Tree   `json:"trees"`
	Streams          []Stream `json:"streams"`
	Protocol         Protocol `json:"protocol"`
}
type Stream struct {
	Out     string `json:"stdout"`
	Err     string `json:"stderr"`
	OutHash string `json:"stdout_hash"`
	ErrHash string `json:"stderr_hash"`
}
type Worker struct {
	mu        sync.Mutex
	directory string
	lock      *os.File
	job       windows.Handle
	p         *process
	journal   Journal
	deadline  time.Time
	timeout   time.Time
	done      chan struct{}
}

func Hash(b []byte) string { h := sha256.Sum256(b); return "sha256:" + hex.EncodeToString(h[:]) }
func now() string          { return time.Now().UTC().Format(time.RFC3339Nano) }
func save(path string, v any) error {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	f, e := os.OpenFile(path+".next", os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(b)
	if e == nil {
		e = f.Sync()
	}
	ce := f.Close()
	if e == nil {
		e = ce
	}
	if e != nil {
		return e
	}
	return atomicReplace(path+".next", path)
}
func (w *Worker) persist() error { return save(filepath.Join(w.directory, "journal.json"), w.journal) }
func Start(directory string, s Spec) (*Worker, error) {
	if s.RunID == "" || s.TaskID == "" || s.Epoch < 1 || len(s.Commands) == 0 || len(s.Environment) == 0 {
		return nil, errors.New("run/task/epoch/commands/explicit environment required")
	}
	for _, c := range s.Commands {
		if !filepath.IsAbs(c.Executable) || !filepath.IsAbs(c.Directory) {
			return nil, errors.New("absolute executable and workspace required")
		}
		if _, e := os.Stat(c.Executable); e != nil {
			return nil, e
		}
		if strings.ContainsRune(c.Input, 0) {
			return nil, errors.New("invalid stdin")
		}
	}
	if e := os.Mkdir(directory, 0700); e != nil {
		return nil, e
	}
	lock, e := lockFile(filepath.Join(directory, "owner.lock"))
	if e != nil {
		return nil, e
	}
	w := &Worker{directory: directory, lock: lock, done: make(chan struct{})}
	w.journal = Journal{Spec: s, Revision: Revision, Job: "Local\\ResearchOS-" + strings.TrimPrefix(Hash([]byte(directory+s.RunID)), "sha256:"), State: "STARTING", Worker: fmt.Sprintf("%d-%d", os.Getpid(), time.Now().UnixNano()), Started: now(), Pending: len(s.Commands), Trees: []Tree{}, Streams: []Stream{}}
	for _, v := range s.Environment {
		n, _, _ := strings.Cut(v, "=")
		w.journal.EnvironmentNames = append(w.journal.EnvironmentNames, n)
	}
	sort.Strings(w.journal.EnvironmentNames)
	if s.Lease <= 0 {
		s.Lease = LeaseDuration
	}
	if s.Timeout <= 0 {
		s.Timeout = 10 * time.Minute
	}
	w.deadline = time.Now().Add(s.Lease)
	w.timeout = time.Now().Add(s.Timeout)
	// Durable intent precedes every possible external side effect.
	if e = w.persist(); e != nil {
		lock.Close()
		return nil, e
	}
	if w.job, e = newJob(w.journal.Job); e != nil {
		w.journal.State = "FAILED"
		w.journal.Reason = e.Error()
		w.persist()
		lock.Close()
		return nil, e
	}
	go w.run(s)
	return w, nil
}
func (w *Worker) snapshotTree() {
	ids, e := jobPIDs(w.job)
	x := Tree{At: now(), PIDs: ids}
	if e != nil {
		x.Error = e.Error()
	}
	w.journal.Trees = append(w.journal.Trees, x)
}
func (w *Worker) Renew(epoch int64, d time.Duration) error {
	w.mu.Lock()
	defer w.mu.Unlock()
	if epoch != w.journal.Spec.Epoch || d <= 0 || d > LeaseDuration || w.journal.Cancelled {
		return errors.New("stale epoch or invalid lease")
	}
	w.deadline = time.Now().Add(d)
	return nil
}
func (w *Worker) Cancel(epoch int64, reason string) error {
	w.mu.Lock()
	defer w.mu.Unlock()
	if epoch != w.journal.Spec.Epoch {
		return errors.New("stale epoch")
	}
	if w.journal.Ended != "" {
		return nil
	}
	w.journal.Cancelled = true
	w.journal.Pending = 0
	w.journal.QueueEmpty = true
	w.journal.State = "CANCEL_REQUESTED"
	w.journal.Reason = reason
	w.snapshotTree()
	if e := w.persist(); e != nil {
		return e
	}
	return killJob(w.job)
}
func (w *Worker) Read() Journal {
	w.mu.Lock()
	defer w.mu.Unlock()
	b, _ := json.Marshal(w.journal)
	var j Journal
	json.Unmarshal(b, &j)
	return j
}
func (w *Worker) Wait(ctx context.Context) (Journal, error) {
	select {
	case <-w.done:
		return w.Read(), nil
	case <-ctx.Done():
		return w.Read(), ctx.Err()
	}
}
func (w *Worker) run(s Spec) {
	defer close(w.done)
	defer w.lock.Close()
	defer closeJob(w.job)
	for i, c := range s.Commands {
		w.mu.Lock()
		if w.journal.Cancelled {
			w.finishLocked()
			w.mu.Unlock()
			return
		}
		if time.Now().After(w.deadline) || time.Now().After(w.timeout) {
			w.journal.Cancelled = true
			w.journal.Reason = "deadline before launch"
			w.finishLocked()
			w.mu.Unlock()
			return
		}
		w.journal.State = "STARTING"
		w.journal.Pending = len(s.Commands) - i - 1
		if e := w.persist(); e != nil {
			w.journal.State = "UNKNOWN"
			w.journal.Reason = e.Error()
			w.mu.Unlock()
			return
		}
		prefix := filepath.Join(w.directory, fmt.Sprintf("%03d", i))
		in, e := os.OpenFile(prefix+".stdin", os.O_CREATE|os.O_TRUNC|os.O_RDWR, 0600)
		if e == nil {
			_, e = in.WriteString(c.Input)
			if e == nil {
				_, e = in.Seek(0, 0)
			}
		}
		var out, errout *os.File
		if e == nil {
			out, e = os.OpenFile(prefix+".stdout", os.O_CREATE|os.O_TRUNC|os.O_RDWR, 0600)
		}
		if e == nil {
			errout, e = os.OpenFile(prefix+".stderr", os.O_CREATE|os.O_TRUNC|os.O_RDWR, 0600)
		}
		if e == nil {
			w.p, e = launch(w.job, c, s.Environment, in, out, errout)
		}
		if in != nil {
			in.Close()
		}
		os.Remove(prefix + ".stdin")
		if out != nil {
			out.Close()
		}
		if errout != nil {
			errout.Close()
		}
		if e != nil {
			w.journal.State = "FAILED"
			w.journal.Reason = e.Error()
			w.finishLocked()
			w.mu.Unlock()
			return
		}
		w.journal.PID = w.p.pid
		w.journal.Created = w.p.created
		w.journal.Launched++
		w.journal.State = "RUNNING"
		w.snapshotTree()
		if e = w.persist(); e != nil {
			w.journal.Cancelled = true
			w.journal.Reason = "journal failure"
			killJob(w.job)
		}
		w.mu.Unlock()
		ticker := time.NewTicker(30 * time.Millisecond)
		for range ticker.C {
			w.mu.Lock()
			if !w.journal.Cancelled && (time.Now().After(w.deadline) || time.Now().After(w.timeout)) {
				w.journal.Cancelled = true
				w.journal.Pending = 0
				w.journal.QueueEmpty = true
				w.journal.Reason = "request_timeout"
				w.journal.State = "CANCEL_REQUESTED"
				w.snapshotTree()
				w.persist()
				killJob(w.job)
			}
			exited, code, err := w.p.exited()
			ids, treeErr := jobPIDs(w.job)
			if err != nil || treeErr != nil {
				w.journal.State = "UNKNOWN"
				w.journal.Reason = "process inspection unavailable"
				w.persist()
				w.mu.Unlock()
				ticker.Stop()
				return
			}
			if exited && len(ids) == 0 {
				ticker.Stop()
				w.journal.Exit = &code
				w.p.close()
				w.p = nil
				w.journal.ChildrenStopped = true
				w.snapshotTree()
				stream := Stream{Out: prefix + ".stdout", Err: prefix + ".stderr"}
				for _, path := range []string{stream.Out, stream.Err} {
					b, readErr := os.ReadFile(path)
					if readErr != nil {
						w.journal.State = "UNKNOWN"
						w.journal.Reason = readErr.Error()
						w.persist()
						w.mu.Unlock()
						return
					}
					b = Redact(b)
					if e = os.WriteFile(path, b, 0600); e != nil {
						w.journal.State = "UNKNOWN"
						w.persist()
						w.mu.Unlock()
						return
					}
					if path == stream.Out {
						stream.OutHash = Hash(b)
						w.journal.Protocol = Parse(b, code)
					} else {
						stream.ErrHash = Hash(b)
					}
				}
				w.journal.Streams = append(w.journal.Streams, stream)
				if code != 0 || w.journal.Cancelled {
					if !w.journal.Cancelled {
						w.journal.State = "FAILED"
						w.journal.Reason = "executor_exit"
					}
					w.finishLocked()
					w.mu.Unlock()
					return
				}
				w.mu.Unlock()
				break
			}
			// A parent exit does not prove descendants stopped. Deadline/cancel still kills the job.
			w.mu.Unlock()
		}
	}
	w.mu.Lock()
	w.journal.State = "SETTLED"
	w.finishLocked()
	w.mu.Unlock()
}
func (w *Worker) finishLocked() {
	ids, e := jobPIDs(w.job)
	w.snapshotTree()
	w.journal.Pending = 0
	w.journal.QueueEmpty = true
	w.journal.ChildrenStopped = e == nil && len(ids) == 0
	if !w.journal.ChildrenStopped {
		w.journal.State = "UNKNOWN"
	} else if w.journal.Cancelled {
		w.journal.State = "CANCELLED"
	} else if w.journal.State != "FAILED" {
		w.journal.State = "SETTLED"
	}
	w.journal.Ended = now()
	if e = w.persist(); e != nil {
		w.journal.State = "UNKNOWN"
		w.journal.Reason = e.Error()
	}
}

// Reconcile never resumes a session or launches a replacement. Unknown side effects retain ownership.
func Reconcile(directory string) (Journal, error) {
	lock, e := lockFile(filepath.Join(directory, "owner.lock"))
	if e != nil {
		return Journal{}, errors.New("worker still owns run")
	}
	defer lock.Close()
	b, e := os.ReadFile(filepath.Join(directory, "journal.json"))
	if e != nil {
		return Journal{}, e
	}
	var j Journal
	if e = json.Unmarshal(b, &j); e != nil {
		return j, e
	}
	if j.Ended != "" && j.ChildrenStopped && j.QueueEmpty {
		return j, nil
	}
	j.Pending = 0
	j.QueueEmpty = true
	j.Cancelled = true
	j.State = "UNKNOWN"
	j.Reason = "worker restarted; external outcome unconfirmed"
	job, je := openJob(j.Job)
	if je == nil {
		defer closeJob(job)
		if e = killJob(job); e == nil {
			for i := 0; i < 100; i++ {
				ids, er := jobPIDs(job)
				j.Trees = append(j.Trees, Tree{At: now(), PIDs: ids})
				if er == nil && len(ids) == 0 {
					j.ChildrenStopped = true
					break
				}
				time.Sleep(20 * time.Millisecond)
			}
		}
	}
	if j.PID != 0 {
		alive, ie := inspectIdentity(j.PID, j.Created)
		if ie != nil || alive {
			j.ChildrenStopped = false
		} else if je != nil {
			j.ChildrenStopped = true
		}
	}
	// Missing job/PID confirms process termination only, never outcome or rollback of external effects.
	if e = save(filepath.Join(directory, "journal.json"), j); e != nil {
		return j, e
	}
	return j, nil
}

// Minimal process environment. Credential values are supplied only through an explicitly selected home.
func Environment(codexHome string) []string {
	env := []string{}
	for _, k := range []string{"SystemRoot", "WINDIR", "PATH", "PATHEXT", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "COMSPEC", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"} {
		if v := os.Getenv(k); v != "" {
			env = append(env, k+"="+v)
		}
	}
	if codexHome != "" {
		env = append(env, "CODEX_HOME="+codexHome)
	}
	sort.Strings(env)
	return env
}

//go:build windows

package runtime

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"golang.org/x/sys/windows"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"researchos.local/research-os/internal/canonical"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

const BridgeRevision = "windows-appcontainer-v1"

type BridgeFrame struct {
	Sequence   int64           `json:"sequence"`
	Type       string          `json:"type"`
	Key        string          `json:"key,omitempty"`
	Route      string          `json:"route,omitempty"`
	Capability string          `json:"capability,omitempty"`
	Payload    json.RawMessage `json:"payload,omitempty"`
	Path       string          `json:"path,omitempty"`
}

type BridgeRequest struct {
	WorkerID     string
	Manifest     json.RawMessage
	ManifestHash string
	Executable   string
	// Only explicit immutable inputs cross into the task sandbox. Credentials,
	// authority paths and the host manifest never enter this map.
	Inputs       map[string][]byte
	BeforeResume func(sandbox.Identity) error
}

type BridgeJournal struct {
	Version            int              `json:"version"`
	Manifest           json.RawMessage  `json:"manifest"`
	ManifestHash       string           `json:"manifest_hash"`
	DispatchKey        string           `json:"dispatch_key"`
	Worker             string           `json:"worker"`
	Revision           string           `json:"adapter_revision"`
	Identity           sandbox.Identity `json:"identity"`
	State              string           `json:"state"`
	Reason             string           `json:"reason"`
	Started            string           `json:"started"`
	Ended              string           `json:"ended"`
	Sequence           int64            `json:"observation_sequence"`
	Frames             int64            `json:"frames"`
	Acknowledged       int64            `json:"acknowledged"`
	ContextReady       bool             `json:"context_ready"`
	CheckpointSequence int64            `json:"checkpoint_sequence"`
	Paused             bool             `json:"paused"`
	InputHash          string           `json:"input_hash"`
	ProtocolComplete   bool             `json:"protocol_complete"`
	Cancelled          bool             `json:"cancelled"`
	Receipt            sandbox.Receipt  `json:"sandbox_receipt"`
	Artifacts          []Artifact       `json:"artifacts"`
	StdoutHash         string           `json:"stdout_hash"`
	StderrHash         string           `json:"stderr_hash"`
}

type Bridge struct {
	mu             sync.Mutex
	directory      string
	lock           *os.File
	process        *sandbox.Process
	cancel         context.CancelFunc
	journal        BridgeJournal
	frames         chan BridgeFrame
	done           chan struct{}
	deadline       time.Time
	wallDeadline   time.Time
	pending        []byte
	stdout, stderr *os.File
	streamOffsets  map[string]int64
	err            error
}

func bridgeMap(raw []byte) (map[string]any, error) {
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	var m map[string]any
	err := d.Decode(&m)
	if err == nil && m == nil {
		err = errors.New("object required")
	}
	return m, err
}
func bridgeString(m map[string]any, key string) string { s, _ := m[key].(string); return s }
func bridgeNumber(m map[string]any, key string) int64 {
	n, _ := m[key].(json.Number)
	v, _ := n.Int64()
	return v
}
func canonicalHash(raw []byte) (string, error) {
	b, e := canonical.JSON(raw)
	if e != nil {
		return "", e
	}
	return Hash(b), nil
}

// LockDataRoot is held for the complete control coordinator lifetime. It uses
// an OS-exclusive non-inherited handle, not the SQLite connection count.
func LockDataRoot(directory string) (*os.File, error) {
	abs, e := filepath.Abs(directory)
	if e != nil {
		return nil, e
	}
	if e = os.MkdirAll(abs, 0700); e != nil {
		return nil, e
	}
	actual, e := filepath.EvalSymlinks(abs)
	if e != nil || !strings.EqualFold(filepath.Clean(abs), filepath.Clean(actual)) {
		return nil, errors.New("canonical non-reparse data root required")
	}
	return lockFile(filepath.Join(actual, "coordinator.lock"))
}

func (w *Bridge) persist() error {
	w.journal.Sequence++
	return save(filepath.Join(w.directory, "bridge.json"), w.journal)
}

func StartBridge(ctx context.Context, directory string, request BridgeRequest) (*Bridge, error) {
	digest, e := canonicalHash(request.Manifest)
	if e != nil || digest != request.ManifestHash {
		return nil, errors.New("immutable manifest hash mismatch")
	}
	manifest, e := bridgeMap(request.Manifest)
	if e != nil {
		return nil, e
	}
	admission, _ := manifest["admission"].(map[string]any)
	profile, _ := admission["profile"].(map[string]any)
	if e = validateBridgeProgram(profile, request.Inputs); e != nil {
		return nil, e
	}
	if request.WorkerID == "" || bridgeString(manifest, "dispatch_key") == "" || bridgeNumber(manifest, "epoch") < 1 || bridgeString(profile, "sandbox") != "appcontainer-zero-capabilities-v1" || bridgeString(profile, "adapter_revision") != BridgeRevision || request.BeforeResume == nil {
		return nil, errors.New("complete bound profile and beforeResume required")
	}
	if !filepath.IsAbs(request.Executable) || !strings.EqualFold(filepath.Ext(request.Executable), ".exe") {
		return nil, errors.New("trusted native executable required")
	}
	actual, e := filepath.EvalSymlinks(request.Executable)
	if e != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(request.Executable)) {
		return nil, errors.New("executable reparse rejected")
	}
	info, e := os.Stat(actual)
	if e != nil || !info.Mode().IsRegular() || info.Size() > 128*1024*1024 {
		return nil, errors.New("bounded regular executable required")
	}
	binary, e := os.ReadFile(actual)
	if e != nil {
		return nil, e
	}
	if Hash(binary) != profile["build_hash"] {
		return nil, errors.New("executable differs from frozen build")
	}
	if e = os.Mkdir(directory, 0700); e != nil {
		return nil, e
	} // Never reuses a dispatch directory.
	if _, e = PrivateDirectory(directory); e != nil {
		return nil, e
	}
	lock, e := lockFile(filepath.Join(directory, "owner.lock"))
	if e != nil {
		return nil, e
	}
	child, cancel := context.WithCancel(ctx)
	w := &Bridge{directory: directory, lock: lock, cancel: cancel, frames: make(chan BridgeFrame, 32), done: make(chan struct{}), deadline: time.Now().Add(LeaseDuration), wallDeadline: time.Now().UTC().Add(LeaseDuration), streamOffsets: map[string]int64{}}
	w.journal = BridgeJournal{Version: 1, Manifest: append(json.RawMessage(nil), request.Manifest...), ManifestHash: digest, DispatchKey: bridgeString(manifest, "dispatch_key"), Worker: request.WorkerID, Revision: BridgeRevision, State: "PREPARED", Started: now(), Artifacts: []Artifact{}, InputHash: Hash(request.Inputs["request.json"])}
	failed := true
	defer func() {
		if failed {
			cancel()
			lock.Close()
			if w.stdout != nil {
				w.stdout.Close()
			}
			if w.stderr != nil {
				w.stderr.Close()
			}
		}
	}()
	if e = w.persist(); e != nil {
		return nil, e
	}
	input, output := filepath.Join(directory, "input"), filepath.Join(directory, "output")
	for _, path := range []string{input, output} {
		if e = os.Mkdir(path, 0700); e != nil {
			return nil, e
		}
	}
	if e = os.WriteFile(filepath.Join(input, "worker.exe"), binary, 0700); e != nil {
		return nil, e
	}
	var inputBytes int64
	for relative, raw := range request.Inputs {
		if !filepath.IsLocal(relative) || strings.EqualFold(relative, "worker.exe") {
			return nil, errors.New("local immutable input names required")
		}
		inputBytes += int64(len(raw))
		if inputBytes > 64*1024*1024 {
			return nil, errors.New("input limit exceeded")
		}
		path := filepath.Join(input, relative)
		if e = os.MkdirAll(filepath.Dir(path), 0700); e != nil {
			return nil, e
		}
		if e = os.WriteFile(path, raw, 0600); e != nil {
			return nil, e
		}
	}
	w.stdout, e = os.OpenFile(filepath.Join(directory, "stdout.raw"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return nil, e
	}
	w.stderr, e = os.OpenFile(filepath.Join(directory, "stderr.raw"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return nil, e
	}
	args := []string{}
	argv, _ := profile["argv"].([]any)
	for _, v := range argv {
		arg, ok := v.(string)
		if !ok {
			return nil, errors.New("argument string required")
		}
		switch arg {
		case "{input}":
			arg = input
		case "{output}":
			arg = output
		case "{manifest}":
			arg = filepath.Join(input, "request.json")
		case "{bundle}":
			arg = filepath.Join(input, "mu-worker.mjs")
		case "{checkpoint}":
			arg = filepath.Join(input, "checkpoint.json")
		}
		args = append(args, arg)
	}
	seconds := bridgeNumber(profile, "timeout_seconds")
	maxSeconds := int64(300)
	if profile["backend"] == "mu-sdk-broker-v1" {
		maxSeconds = 900
	}
	if seconds < 1 || seconds > maxSeconds {
		return nil, errors.New("bounded profile timeout required")
	}
	command := sandbox.Command{Executable: filepath.Join(input, "worker.exe"), Args: args, InputDirectory: input, OutputDirectory: output, Timeout: time.Duration(seconds) * time.Second}
	w.process, e = sandbox.Start(child, command, sandbox.StartOptions{Interactive: true, AllowCodingTurnTimeout: profile["backend"] == "mu-sdk-broker-v1", OnStream: w.consume, BeforeResume: func(identity sandbox.Identity) error {
		w.mu.Lock()
		defer w.mu.Unlock()
		w.journal.Identity = identity
		w.journal.State = "STARTED"
		if err := w.persist(); err != nil {
			return err
		}
		return request.BeforeResume(identity)
	}})
	if e != nil {
		w.journal.State = "UNKNOWN"
		w.journal.Reason = e.Error()
		w.persist()
		return nil, e
	}
	failed = false
	go w.wait(child, profile)
	return w, nil
}

func (w *Bridge) consume(chunk sandbox.StreamChunk) error {
	w.mu.Lock()
	defer w.mu.Unlock()
	if chunk.Offset != w.streamOffsets[chunk.Stream] {
		return errors.New("stream sequence gap")
	}
	f := w.stdout
	if chunk.Stream == "stderr" {
		f = w.stderr
	}
	if _, e := f.Write(chunk.Data); e != nil {
		return e
	}
	if e := f.Sync(); e != nil {
		return e
	}
	w.streamOffsets[chunk.Stream] += int64(len(chunk.Data))
	if chunk.Stream != "stdout" {
		return nil
	}
	w.pending = append(w.pending, chunk.Data...)
	for {
		end := bytes.IndexByte(w.pending, '\n')
		if end < 0 {
			break
		}
		line := w.pending[:end]
		w.pending = w.pending[end+1:]
		if len(line) == 0 || len(line) > 64*1024 {
			return errors.New("protocol frame size invalid")
		}
		var frame BridgeFrame
		if _, e := canonical.JSON(line); e != nil {
			return errors.New("invalid canonical JSON protocol line")
		}
		decoder := json.NewDecoder(bytes.NewReader(line))
		decoder.DisallowUnknownFields()
		if e := decoder.Decode(&frame); e != nil {
			return errors.New("invalid typed protocol")
		}
		if e := decoder.Decode(new(any)); e != io.EOF {
			return errors.New("one complete JSON object per protocol line required")
		}
		if frame.Sequence != w.journal.Frames+1 || w.journal.ProtocolComplete {
			return errors.New("protocol sequence or terminal ordering invalid")
		}
		switch frame.Type {
		case "context.ready":
			payload, err := bridgeMap(frame.Payload)
			if err != nil || w.journal.ContextReady || payload["input_hash"] != w.journal.InputHash {
				return errors.New("context acknowledgement mismatch")
			}
			w.journal.ContextReady = true
		case "effect.request", "checkpoint":
			if !w.journal.ContextReady {
				return errors.New("context acknowledgement required before work")
			}
			if frame.Type == "checkpoint" {
				w.journal.CheckpointSequence = frame.Sequence
			}
		case "turn.paused":
			if !w.journal.ContextReady || w.journal.CheckpointSequence == 0 || w.journal.Acknowledged < w.journal.CheckpointSequence {
				return errors.New("durably acknowledged checkpoint required before pause")
			}
			w.journal.Paused, w.journal.ProtocolComplete = true, true
		case "turn.completed":
			if !w.journal.ContextReady {
				return errors.New("context acknowledgement required before completion")
			}
			w.journal.ProtocolComplete = true
		default:
			return errors.New("unknown protocol frame")
		}
		w.journal.Frames = frame.Sequence
		select {
		case w.frames <- frame:
		default:
			return errors.New("protocol queue overflow")
		}
	}
	if len(w.pending) > 64*1024 {
		return errors.New("protocol frame overflow")
	}
	return nil
}

func (w *Bridge) wait(ctx context.Context, profile map[string]any) {
	defer close(w.done)
	defer close(w.frames)
	defer w.lock.Close()
	finished := make(chan struct{})
	go func() {
		ticker := time.NewTicker(50 * time.Millisecond)
		defer ticker.Stop()
		for {
			select {
			case <-finished:
				return
			case <-ticker.C:
				w.mu.Lock()
				expired := time.Now().After(w.deadline) || time.Now().UTC().After(w.wallDeadline)
				w.mu.Unlock()
				if expired {
					w.Cancel("lease expired")
					return
				}
			case <-ctx.Done():
				w.Cancel("coordinator control channel closed")
				return
			}
		}
	}()
	receipt, err := w.process.Wait(context.Background())
	close(finished)
	w.mu.Lock()
	defer w.mu.Unlock()
	w.journal.Receipt = receipt
	w.journal.Ended = now()
	err = errors.Join(err, w.stdout.Close(), w.stderr.Close())
	w.journal.StdoutHash = Hash(receipt.Stdout)
	w.journal.StderrHash = Hash(receipt.Stderr)
	if len(w.pending) != 0 {
		err = errors.Join(err, errors.New("unterminated protocol frame"))
	}
	if err != nil || !receipt.Stopped || !receipt.StreamsDrained || !receipt.OutputCopied || !receipt.CleanupComplete {
		w.journal.State = "UNKNOWN"
	} else if receipt.ExitCode != 0 || receipt.TimedOut || w.journal.Cancelled || !w.journal.ProtocolComplete || !w.journal.ContextReady {
		w.journal.State = "FAILED"
	} else if w.journal.Paused {
		w.journal.State = "PAUSED"
	} else {
		w.journal.State = "EXITED"
	}
	if w.journal.State == "EXITED" {
		outputs, _ := profile["outputs"].([]any)
		var total int64
		for _, v := range outputs {
			relative, ok := v.(string)
			if !ok || !filepath.IsLocal(relative) {
				err = errors.New("invalid output path")
				break
			}
			path := filepath.Join(w.directory, "output", relative)
			actual, e := filepath.EvalSymlinks(path)
			if e != nil || !strings.EqualFold(actual, path) {
				err = errors.New("output reparse rejected")
				break
			}
			info, e := os.Stat(path)
			if e != nil || !info.Mode().IsRegular() || info.Size() > 64*1024*1024 {
				err = errors.New("output missing or exceeds bound")
				break
			}
			total += info.Size()
			if total > 64*1024*1024 {
				err = errors.New("output total exceeds bound")
				break
			}
			raw, e := os.ReadFile(path)
			if e != nil {
				err = e
				break
			}
			w.journal.Artifacts = append(w.journal.Artifacts, Artifact{Path: relative, Hash: Hash(raw), Size: int64(len(raw))})
		}
		if err != nil {
			w.journal.State = "FAILED"
		}
	}
	if err != nil {
		w.journal.Reason = err.Error()
	}
	w.err = errors.Join(err, w.persist())
}

func (w *Bridge) Frames() <-chan BridgeFrame { return w.frames }
func (w *Bridge) Done() <-chan struct{}      { return w.done }
func (w *Bridge) Directory() string          { return w.directory }
func (w *Bridge) Read() BridgeJournal {
	w.mu.Lock()
	defer w.mu.Unlock()
	b, _ := json.Marshal(w.journal)
	var journal BridgeJournal
	json.Unmarshal(b, &journal)
	return journal
}
func (w *Bridge) Renew(epoch int64, lease time.Duration) error {
	w.mu.Lock()
	defer w.mu.Unlock()
	manifest, e := bridgeMap(w.journal.Manifest)
	if e != nil || epoch != bridgeNumber(manifest, "epoch") || lease <= 0 || lease > LeaseDuration || w.journal.Cancelled || time.Now().After(w.deadline) || time.Now().UTC().After(w.wallDeadline) {
		return errors.New("expired, cancelled or stale worker lease")
	}
	w.deadline = time.Now().Add(lease)
	w.wallDeadline = time.Now().UTC().Add(lease)
	return nil
}
func (w *Bridge) Cancel(reason string) {
	w.mu.Lock()
	w.journal.Cancelled = true
	w.journal.Reason = reason
	w.persist()
	w.mu.Unlock()
	w.cancel()
	if w.process != nil {
		w.process.Cancel()
	}
}
func (w *Bridge) Acknowledge(ctx context.Context, sequence int64, response any) error {
	w.mu.Lock()
	if sequence != w.journal.Acknowledged+1 || sequence > w.journal.Frames {
		w.mu.Unlock()
		return errors.New("protocol acknowledgement out of order")
	}
	w.journal.Acknowledged = sequence
	err := w.persist()
	w.mu.Unlock()
	if err != nil {
		return err
	}
	if response != nil {
		raw, e := json.Marshal(response)
		if e != nil {
			return e
		}
		if len(raw) > 64*1024 {
			return errors.New("protocol response exceeds frame limit")
		}
		return w.process.Write(ctx, append(raw, '\n'))
	}
	return nil
}
func (w *Bridge) Finalize(effectsReconciled bool) (BridgeJournal, error) {
	select {
	case <-w.done:
	default:
		return BridgeJournal{}, errors.New("process not drained")
	}
	w.mu.Lock()
	defer w.mu.Unlock()
	if w.err != nil {
		return w.journal, w.err
	}
	if w.journal.Acknowledged != w.journal.Frames || !effectsReconciled {
		return w.journal, errors.New("protocol or effect reconciliation incomplete")
	}
	if w.journal.State == "EXITED" {
		w.journal.State = "SETTLED"
	}
	if e := w.persist(); e != nil {
		return w.journal, e
	}
	return w.journal, nil
}

// Observation is host-created. PID creation time is represented as decimal
// text to retain all 64 bits through canonical JSON, unlike a float64 number.
func (j BridgeJournal) Observation() (map[string]any, error) {
	manifest, e := bridgeMap(j.Manifest)
	if e != nil {
		return nil, e
	}
	admission, _ := manifest["admission"].(map[string]any)
	profile, _ := admission["profile"].(map[string]any)
	spec := map[string]any{"run_id": manifest["run_id"], "task_id": manifest["task_id"], "epoch": manifest["epoch"], "profile_hash": admission["profile_hash"], "technical_hash": admission["technical_hash"], "capabilities": []any{"start"}}
	if j.ContextReady {
		spec["capabilities"] = []any{"start", "context_rebuild"}
	}
	for _, key := range []string{"build_hash", "backend", "model", "sandbox", "platform", "adapter", "adapter_revision", "credential_revision"} {
		spec[key] = profile[key]
	}
	state := j.State
	if state == "EXITED" {
		state = "UNKNOWN"
	}
	if j.Cancelled && j.Receipt.Stopped && j.Receipt.StreamsDrained {
		state = "CANCELLED"
	}
	return map[string]any{"spec": spec, "dispatch_key": j.DispatchKey, "manifest_hash": j.ManifestHash, "worker": j.Worker, "identity": map[string]any{"pid": j.Identity.PID, "process_created_ns": strconv.FormatInt(j.Identity.Created, 10), "job": j.Identity.Job, "appcontainer_sid": j.Identity.SID, "profile": j.Identity.Profile, "staging_directory": j.Identity.StagingDirectory}, "observation_sequence": j.Sequence, "state": state, "reason": j.Reason, "children_stopped": j.Receipt.Stopped, "queue_empty": j.Acknowledged == j.Frames, "streams_drained": j.Receipt.StreamsDrained, "cleanup_complete": j.Receipt.CleanupComplete, "exit_code": j.Receipt.ExitCode, "ended": j.Ended, "protocol": map[string]any{"settled": state == "SETTLED" && j.ProtocolComplete && j.Receipt.StreamsDrained, "frames": j.Frames, "acknowledged": j.Acknowledged}, "artifacts": j.Artifacts, "stdout_hash": j.StdoutHash, "stderr_hash": j.StderrHash}, nil
}

// ReadBridgeTerminal checks the trusted directory and raw hashes. It never
// creates a process, renews a lease or turns missing PID into success.
func ReadBridgeTerminal(directory, manifestHash string) (BridgeJournal, error) {
	lock, e := lockFile(filepath.Join(directory, "owner.lock"))
	if e != nil {
		return BridgeJournal{}, errors.New("worker still owns dispatch")
	}
	defer lock.Close()
	raw, e := os.ReadFile(filepath.Join(directory, "bridge.json"))
	if e != nil {
		return BridgeJournal{}, e
	}
	var j BridgeJournal
	if e = json.Unmarshal(raw, &j); e != nil {
		return j, e
	}
	digest, e := canonicalHash(j.Manifest)
	if e != nil || digest != manifestHash || j.ManifestHash != manifestHash {
		return j, errors.New("recovery manifest mismatch")
	}
	if j.Identity.PID != 0 {
		alive, e := inspectIdentity(j.Identity.PID, j.Identity.Created)
		if e != nil || alive {
			return j, errors.New("old process identity not confirmed stopped")
		}
	}
	if j.Ended == "" || !j.Receipt.Stopped || !j.Receipt.StreamsDrained || !j.Receipt.CleanupComplete {
		return j, errors.New("dispatch outcome UNKNOWN")
	}
	if j.State == "SETTLED" && (!j.ProtocolComplete || j.Acknowledged != j.Frames || j.Receipt.ExitCode != 0 || !j.Receipt.OutputCopied || j.Cancelled) {
		return j, errors.New("terminal protocol is not settled")
	}
	for file, digest := range map[string]string{"stdout.raw": j.StdoutHash, "stderr.raw": j.StderrHash} {
		f, e := os.Open(filepath.Join(directory, file))
		if e != nil {
			return j, e
		}
		raw, e := io.ReadAll(io.LimitReader(f, sandbox.MaxStreamBytes+1))
		f.Close()
		if e != nil || len(raw) > sandbox.MaxStreamBytes || Hash(raw) != digest {
			return j, errors.New("recovery stream mismatch")
		}
	}
	manifest, e := bridgeMap(j.Manifest)
	if e != nil {
		return j, e
	}
	admission, _ := manifest["admission"].(map[string]any)
	profile, _ := admission["profile"].(map[string]any)
	expected, _ := profile["outputs"].([]any)
	if j.State == "SETTLED" && len(expected) != len(j.Artifacts) {
		return j, errors.New("recovery output manifest incomplete")
	}
	var total int64
	for i, a := range j.Artifacts {
		if i >= len(expected) || expected[i] != a.Path || !filepath.IsLocal(a.Path) {
			return j, errors.New("recovery output manifest changed")
		}
		path := filepath.Join(directory, "output", a.Path)
		actual, e := filepath.EvalSymlinks(path)
		if e != nil || !strings.EqualFold(path, actual) {
			return j, errors.New("recovery output reparse rejected")
		}
		info, e := os.Stat(path)
		if e != nil || !info.Mode().IsRegular() || info.Size() != a.Size || a.Size < 0 || a.Size > 64*1024*1024 {
			return j, errors.New("recovery output size changed")
		}
		total += a.Size
		if total > 64*1024*1024 {
			return j, errors.New("recovery outputs exceed total bound")
		}
		raw, e := os.ReadFile(path)
		if e != nil || Hash(raw) != a.Hash {
			return j, errors.New("recovery output bytes changed")
		}
	}
	return j, nil
}

// ReconcileBridge stops only the exact recorded process after the worker lock
// is released. Missing end/drain records remain UNKNOWN even after termination.
func ReconcileBridge(directory, manifestHash string) (BridgeJournal, error) {
	lock, e := lockFile(filepath.Join(directory, "owner.lock"))
	if e != nil {
		return BridgeJournal{}, errors.New("worker still owns dispatch")
	}
	raw, e := os.ReadFile(filepath.Join(directory, "bridge.json"))
	if e != nil {
		lock.Close()
		return BridgeJournal{}, e
	}
	var j BridgeJournal
	if e = json.Unmarshal(raw, &j); e != nil {
		lock.Close()
		return j, e
	}
	digest, e := canonicalHash(j.Manifest)
	if e != nil || digest != manifestHash || j.ManifestHash != manifestHash {
		lock.Close()
		return j, errors.New("recovery manifest mismatch")
	}
	if j.Identity.PID != 0 {
		alive, e := inspectIdentity(j.Identity.PID, j.Identity.Created)
		if e != nil {
			lock.Close()
			return j, e
		}
		if alive {
			h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.PROCESS_TERMINATE|windows.SYNCHRONIZE, false, j.Identity.PID)
			if e != nil {
				lock.Close()
				return j, e
			}
			var created, exit, kernel, user windows.Filetime
			e = windows.GetProcessTimes(h, &created, &exit, &kernel, &user)
			if e == nil && created.Nanoseconds() != j.Identity.Created {
				e = errors.New("PID reused; refusing termination")
			}
			if e == nil {
				e = windows.TerminateProcess(h, 1)
			}
			if e == nil {
				var state uint32
				state, e = windows.WaitForSingleObject(h, 5000)
				if state != windows.WAIT_OBJECT_0 {
					e = errors.New("old process stop unconfirmed")
				}
			}
			windows.CloseHandle(h)
			if e != nil {
				lock.Close()
				return j, e
			}
			j.State = "UNKNOWN"
			j.Reason = "orphan terminated; missing terminal stream/cleanup evidence"
			j.Sequence++
			if e = save(filepath.Join(directory, "bridge.json"), j); e != nil {
				lock.Close()
				return j, e
			}
		}
		if !j.Receipt.CleanupComplete {
			if e = sandbox.CleanupAbandoned(j.Identity); e != nil {
				lock.Close()
				return j, e
			}
			j.Receipt.CleanupComplete = true
			j.Receipt.Stopped = true
			j.State = "UNKNOWN"
			j.Reason = "old sandbox stopped and cleaned; terminal stream facts remain unknown"
			j.Sequence++
			if e = save(filepath.Join(directory, "bridge.json"), j); e != nil {
				lock.Close()
				return j, e
			}
		}
	}
	lock.Close()
	return ReadBridgeTerminal(directory, manifestHash)
}

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
const PauseProtocol = "RESEARCHOS_PAUSE_V1"
const PauseCheckpointFilename = "pause-checkpoint.json"
const MaxPauseCheckpointBytes = 12 * 1024 * 1024

type PauseCheckpoint struct {
	QueueCut          int64           `json:"queue_cut"`
	CommandLedgerHash string          `json:"command_ledger_hash"`
	SDKWatermarks     json.RawMessage `json:"sdk_watermarks"`
	SDKSessionID      string          `json:"sdk_session_id"`
	Version           string          `json:"version"`
	PauseID           string          `json:"pause_id"`
	Binding           json.RawMessage `json:"binding"`
	ContentHash       string          `json:"content_hash"`
	Bytes             int64           `json:"bytes"`
	InputHash         string          `json:"input_hash"`
	ModelCalls        int64           `json:"model_calls"`
	ToolCalls         int64           `json:"tool_calls"`
}
type CheckpointSeal struct {
	CheckpointUsePrincipal   string          `json:"checkpoint_use_principal"`
	Type                     string          `json:"type"`
	Version                  string          `json:"version"`
	PauseID                  string          `json:"pause_id"`
	Binding                  json.RawMessage `json:"binding"`
	Sequence                 int64           `json:"checkpoint_sequence"`
	ContentHash              string          `json:"content_hash"`
	CheckpointArtifactID     string          `json:"checkpoint_artifact_id"`
	CheckpointUseReceiptHash string          `json:"checkpoint_use_receipt_hash"`
	JournalCheckpointHash    string          `json:"journal_checkpoint_hash"`
}

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
	PauseProtocol      string           `json:"pause_protocol,omitempty"`
	PauseRequested     bool             `json:"pause_requested,omitempty"`
	PauseID            string           `json:"pause_id,omitempty"`
	QueueBinding       json.RawMessage  `json:"queue_binding,omitempty"`
	Checkpoint         *PauseCheckpoint `json:"checkpoint,omitempty"`
	CheckpointSeal     *CheckpointSeal  `json:"checkpoint_seal,omitempty"`
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
	QueueRequired      bool             `json:"queue_required"`
	QueueSealed        bool             `json:"queue_sealed"`
	QueueAbortObserved bool             `json:"queue_abort_observed"`
	QueueCancelIdle    bool             `json:"queue_cancel_idle"`
	QueueIdle          bool             `json:"queue_idle"`
	QueueInitSequence  int64            `json:"queue_init_sequence"`
	CommandReceipts    []BridgeFrame    `json:"command_receipts,omitempty"`
}

type bridgeCheckpointMode uint8

const (
	checkpointDisabled bridgeCheckpointMode = iota
	checkpointLegacy
	checkpointPauseV1
)

type Bridge struct {
	checkpointMode                            bridgeCheckpointMode
	mu                                        sync.Mutex
	directory                                 string
	lock                                      *os.File
	process                                   *sandbox.Process
	cancel                                    context.CancelFunc
	journal                                   BridgeJournal
	frames                                    chan BridgeFrame
	done                                      chan struct{}
	deadline                                  time.Time
	wallDeadline                              time.Time
	pending                                   []byte
	stdout, stderr                            *os.File
	streamOffsets                             map[string]int64
	err                                       error
	writeMu                                   sync.Mutex
	modelInitDelivered                        bool
	modelStreams                              []*ModelStream
	modelObservations                         chan ModelStreamObservation
	modelChanged                              chan struct{}
	modelDataRecords, modelObservationRecords int
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

// The host request and manifest select the protocol before any worker output.
// In particular, an older Mu worker can run normally without pause capability,
// but its frames cannot opt into the legacy context-rebuild checkpoint path.
func checkpointModeForRequest(manifest map[string]any, raw []byte) (bridgeCheckpointMode, error) {
	if _, err := canonical.JSON(raw); err != nil {
		return checkpointDisabled, errors.New("invalid frozen checkpoint request")
	}
	request, err := bridgeMap(raw)
	if err != nil {
		return checkpointDisabled, err
	}
	if request["task_id"] != manifest["task_id"] || request["run_id"] != manifest["run_id"] || bridgeNumber(request, "epoch") != bridgeNumber(manifest, "epoch") {
		return checkpointDisabled, errors.New("checkpoint request differs from manifest")
	}
	if protocol, exists := request["pause_protocol"]; exists {
		if protocol != PauseProtocol {
			return checkpointDisabled, errors.New("unknown pause protocol")
		}
		return checkpointPauseV1, nil
	}
	admission, _ := manifest["admission"].(map[string]any)
	profile, _ := admission["profile"].(map[string]any)
	if bridgeString(profile, "backend") == "" {
		return checkpointDisabled, errors.New("checkpoint profile backend required")
	}
	if profile["backend"] == "mu-sdk-broker-v1" {
		return checkpointDisabled, nil
	}
	return checkpointLegacy, nil
}

func validateLegacyCheckpoint(frame BridgeFrame) error {
	payload, err := bridgeMap(frame.Payload)
	if err != nil || len(frame.Payload) > 64*1024 || (frame.Path != "" && frame.Path != "checkpoint.json") || frame.Key != "" || payload["version"] == PauseProtocol {
		return errors.New("bounded legacy inline checkpoint required")
	}
	return nil
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
	checkpointMode, e := checkpointModeForRequest(manifest, request.Inputs["request.json"])
	if e != nil {
		return nil, e
	}
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
	w := &Bridge{checkpointMode: checkpointMode, directory: directory, lock: lock, cancel: cancel, frames: make(chan BridgeFrame, 32), done: make(chan struct{}), deadline: time.Now().Add(LeaseDuration), wallDeadline: time.Now().UTC().Add(LeaseDuration), streamOffsets: map[string]int64{}, modelObservations: make(chan ModelStreamObservation, ModelStreamWindow), modelChanged: make(chan struct{})}
	w.journal = BridgeJournal{Version: 1, Manifest: append(json.RawMessage(nil), request.Manifest...), ManifestHash: digest, DispatchKey: bridgeString(manifest, "dispatch_key"), Worker: request.WorkerID, Revision: BridgeRevision, State: "PREPARED", Started: now(), Artifacts: []Artifact{}, InputHash: Hash(request.Inputs["request.json"])}
	inputRequest, _ := bridgeMap(request.Inputs["request.json"])
	w.journal.QueueRequired = inputRequest["queue_control"] == true
	w.journal.QueueBinding, _ = json.Marshal(inputRequest["queue_binding"])
	if checkpointMode == checkpointPauseV1 {
		w.journal.PauseProtocol = PauseProtocol
	}
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
		shape, shapeErr := bridgeMap(line)
		if shapeErr != nil {
			return shapeErr
		}
		if _, auxiliary := shape["version"]; auxiliary {
			if err := w.consumeModelFrame(line); err != nil {
				return err
			}
			continue
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
			if w.journal.PauseProtocol != "" && payload["pause_protocol"] != PauseProtocol {
				return errors.New("pause capability unsupported")
			}
			w.journal.ContextReady = true
		case "effect.request", "checkpoint":
			if !w.journal.ContextReady || w.journal.QueueRequired && (w.journal.QueueInitSequence == 0 || w.journal.Acknowledged < w.journal.QueueInitSequence) {
				return errors.New("context and queue initialization acknowledgement required before work")
			}
			if frame.Type == "checkpoint" {
				switch w.checkpointMode {
				case checkpointPauseV1:
					if err := w.capturePauseCheckpoint(frame); err != nil {
						return err
					}
				case checkpointLegacy:
					if err := validateLegacyCheckpoint(frame); err != nil {
						return err
					}
				default:
					return errors.New("checkpoint capability was not negotiated")
				}
				w.journal.CheckpointSequence = frame.Sequence
			}
		case "turn.paused":
			if !w.journal.ContextReady || w.journal.CheckpointSequence == 0 || w.journal.Acknowledged < w.journal.CheckpointSequence {
				return errors.New("durably acknowledged checkpoint required before pause")
			}
			switch w.checkpointMode {
			case checkpointPauseV1:
				if w.journal.CheckpointSeal == nil || w.journal.Checkpoint == nil {
					return errors.New("typed checkpoint seal required before pause")
				}
				var paused CheckpointSeal
				if json.Unmarshal(frame.Payload, &paused) != nil || paused.Version != PauseProtocol || !samePauseBinding(paused.Binding, w.journal.Checkpoint.Binding) || paused.Sequence != w.journal.CheckpointSequence || paused.ContentHash != w.journal.Checkpoint.ContentHash || paused.PauseID != w.journal.PauseID || paused.CheckpointUsePrincipal != w.journal.CheckpointSeal.CheckpointUsePrincipal || paused.CheckpointArtifactID != w.journal.CheckpointSeal.CheckpointArtifactID || paused.CheckpointUseReceiptHash != w.journal.CheckpointSeal.CheckpointUseReceiptHash || paused.JournalCheckpointHash != w.journal.CheckpointSeal.JournalCheckpointHash {
					return errors.New("paused seal correlation mismatch")
				}
			case checkpointLegacy:
				if len(frame.Payload) != 0 {
					return errors.New("legacy pause cannot carry a typed seal")
				}
			default:
				return errors.New("pause capability was not negotiated")
			}
			w.journal.Paused, w.journal.ProtocolComplete = true, true
		case "turn.completed":
			if !w.journal.ContextReady || w.journal.QueueRequired && !w.journal.QueueSealed {
				return errors.New("context acknowledgement required before completion")
			}
			w.journal.ProtocolComplete = true
		case "command.accepted", "command.consumed", "command.cleared", "command.abort_observed", "command.idle", "command.sealed":
			if !w.journal.ContextReady || !w.journal.QueueRequired || len(w.journal.CommandReceipts) >= 256 {
				return errors.New("unexpected or excessive command receipt")
			}
			payload, err := bridgeMap(frame.Payload)
			if err != nil || w.validateControlBinding(payload) != nil {
				return errors.New("unbound command receipt")
			}
			if frame.Type == "command.accepted" && payload["initialized"] == true {
				if w.journal.QueueInitSequence != 0 {
					return errors.New("duplicate initialization receipt")
				}
				if w.journal.PauseProtocol != "" && payload["pause_protocol"] != PauseProtocol {
					return errors.New("pause initialization negotiation failed")
				}
				w.journal.QueueInitSequence = frame.Sequence
			} else if w.journal.QueueInitSequence == 0 || w.journal.Acknowledged < w.journal.QueueInitSequence {
				return errors.New("command receipt before initialization")
			}
			if frame.Type == "command.abort_observed" {
				w.journal.QueueAbortObserved = payload["sdk_idle"] == true && payload["sdk_queue_empty"] == true
			}
			if frame.Type == "command.idle" || frame.Type == "command.sealed" {
				if !w.journal.Cancelled && payload["cancelled"] != true {
					for _, stream := range w.modelStreams {
						if !stream.closed || stream.failed || stream.creditedObservation != stream.observationSequence {
							return errors.New("SDK idle before MODEL stream observations reconciled")
						}
					}
				}
				if payload["sdk_idle"] != true || payload["sdk_queue_empty"] != true {
					return errors.New("false SDK settlement witness")
				}
				w.journal.QueueIdle = true
				if payload["cancelled"] == true && w.journal.QueueAbortObserved {
					w.journal.QueueCancelIdle = true
				}
			}
			if frame.Type == "command.sealed" {
				w.journal.QueueSealed = true
			}
			w.journal.CommandReceipts = append(w.journal.CommandReceipts, frame)
		default:
			return errors.New("unknown protocol frame")
		}
		w.journal.Frames = frame.Sequence
		if strings.HasPrefix(frame.Type, "command.") || frame.Type == "checkpoint" || frame.Type == "turn.paused" {
			if err := w.persist(); err != nil {
				return err
			}
		}
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
	if !w.journal.Cancelled {
		for _, stream := range w.modelStreams {
			if !stream.closed || stream.failed || stream.creditedObservation != stream.observationSequence {
				err = errors.Join(err, errors.New("MODEL stream closure not reconciled"))
				w.journal.State = "UNKNOWN"
			}
		}
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
	w.mu.Lock()
	w.modelNotifyLocked()
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
	if sequence == w.journal.CheckpointSequence {
		raw, e := json.Marshal(response)
		if e != nil {
			w.mu.Unlock()
			return e
		}
		switch w.checkpointMode {
		case checkpointPauseV1:
			var reply struct {
				Sequence int64          `json:"sequence"`
				Key      string         `json:"key"`
				State    string         `json:"state"`
				Payload  CheckpointSeal `json:"payload"`
			}
			if json.Unmarshal(raw, &reply) != nil || reply.Sequence != sequence || reply.Key != "checkpoint.sealed" || reply.State != "CONFIRMED" || w.validateCheckpointSeal(reply.Payload) != nil {
				w.mu.Unlock()
				return errors.New("checkpoint requires durable artifact/use/journal seal")
			}
			seal := reply.Payload
			w.journal.CheckpointSeal = &seal
		case checkpointLegacy:
			reply, e := bridgeMap(raw)
			artifact, _ := reply["artifact_ref"].(map[string]any)
			if e != nil || bridgeNumber(reply, "sequence") != sequence || reply["type"] != "checkpoint.sealed" || reply["payload"] != nil || artifact["entity_type"] != "Artifact" || bridgeString(artifact, "id") == "" {
				w.mu.Unlock()
				return errors.New("legacy checkpoint requires artifact acknowledgement")
			}
		default:
			w.mu.Unlock()
			return errors.New("checkpoint acknowledgement without negotiated capability")
		}
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
		w.writeMu.Lock()
		defer w.writeMu.Unlock()
		if err := w.process.Write(ctx, append(raw, '\n')); err != nil {
			return err
		}
		w.mu.Lock()
		if sequence == w.journal.QueueInitSequence {
			w.modelInitDelivered = true
			w.modelNotifyLocked()
		}
		w.mu.Unlock()
		return nil
	}
	return nil
}

func (w *Bridge) validateControlBinding(binding map[string]any) error {
	manifest, err := bridgeMap(w.journal.Manifest)
	identity := map[string]any{"pid": w.journal.Identity.PID, "process_created_ns": strconv.FormatInt(w.journal.Identity.Created, 10), "job": w.journal.Identity.Job, "appcontainer_sid": w.journal.Identity.SID, "profile": w.journal.Identity.Profile, "staging_directory": w.journal.Identity.StagingDirectory}
	raw, _ := json.Marshal(identity)
	expected, _ := canonicalHash(raw)
	actualRaw, _ := json.Marshal(binding["process_identity"])
	actual, _ := canonicalHash(actualRaw)
	if err != nil || binding["task_id"] != manifest["task_id"] || binding["run_id"] != manifest["run_id"] || bridgeNumber(binding, "runtime_epoch") != bridgeNumber(manifest, "epoch") || binding["dispatch_key"] != w.journal.DispatchKey || binding["manifest_hash"] != w.journal.ManifestHash || actual != expected || bridgeString(binding, "queue_generation") == "" {
		return errors.New("control identity mismatch")
	}
	if len(w.journal.QueueBinding) > 0 && string(w.journal.QueueBinding) != "null" {
		expected, e := bridgeMap(w.journal.QueueBinding)
		if e != nil {
			return e
		}
		for _, key := range []string{"project_id", "session_id", "queue_generation"} {
			if expected[key] != binding[key] {
				return errors.New("frozen queue binding mismatch")
			}
		}
	}
	return nil
}

// Control shares a single process stdin writer with effect acknowledgements.
func (w *Bridge) Control(ctx context.Context, frame any) error {
	raw, err := json.Marshal(frame)
	if err != nil {
		return err
	}
	if len(raw) > 64*1024 {
		return errors.New("control frame exceeds bound")
	}
	value, err := bridgeMap(raw)
	if err != nil {
		return err
	}
	binding, _ := value["binding"].(map[string]any)
	w.mu.Lock()
	err = w.validateControlBinding(binding)
	if err == nil && (!w.journal.QueueRequired || w.journal.ProtocolComplete) {
		err = errors.New("control on closed worker")
	}
	if err == nil && value["type"] == "command.pause" {
		if w.journal.PauseProtocol != PauseProtocol || value["version"] != PauseProtocol || w.journal.PauseRequested || w.journal.QueueSealed || w.journal.Cancelled || w.journal.QueueInitSequence == 0 || w.journal.Acknowledged < w.journal.QueueInitSequence || bridgeString(value, "pause_id") == "" {
			err = errors.New("pause unsupported or fenced")
		} else {
			w.journal.PauseRequested = true
			w.journal.PauseID = bridgeString(value, "pause_id")
			err = w.persist()
		}
	} else if err == nil && w.journal.PauseRequested {
		err = errors.New("control blocked during pause")
	}
	if err == nil && value["type"] == "command.deliver" && value["initialize"] != true {
		w.journal.QueueIdle = false
	}
	w.mu.Unlock()
	if err != nil {
		return err
	}
	w.writeMu.Lock()
	defer w.writeMu.Unlock()
	return w.process.Write(ctx, append(raw, '\n'))
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
	if !w.journal.Cancelled {
		for _, stream := range w.modelStreams {
			if !stream.closed || stream.failed || stream.creditedObservation != stream.observationSequence {
				return w.journal, errors.New("MODEL stream closure not reconciled")
			}
		}
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
	return map[string]any{"spec": spec, "dispatch_key": j.DispatchKey, "manifest_hash": j.ManifestHash, "worker": j.Worker, "identity": map[string]any{"pid": j.Identity.PID, "process_created_ns": strconv.FormatInt(j.Identity.Created, 10), "job": j.Identity.Job, "appcontainer_sid": j.Identity.SID, "profile": j.Identity.Profile, "staging_directory": j.Identity.StagingDirectory}, "observation_sequence": j.Sequence, "state": state, "reason": j.Reason, "children_stopped": j.Receipt.Stopped, "queue_empty": j.Acknowledged == j.Frames && (!j.QueueRequired || j.QueueSealed || j.Cancelled && j.QueueCancelIdle), "streams_drained": j.Receipt.StreamsDrained, "cleanup_complete": j.Receipt.CleanupComplete, "exit_code": j.Receipt.ExitCode, "ended": j.Ended, "protocol": map[string]any{"settled": state == "SETTLED" && j.ProtocolComplete && j.Receipt.StreamsDrained, "frames": j.Frames, "acknowledged": j.Acknowledged}, "artifacts": j.Artifacts, "stdout_hash": j.StdoutHash, "stderr_hash": j.StderrHash}, nil
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
	manifest, e := bridgeMap(j.Manifest)
	if e != nil {
		return j, e
	}
	request, e := readBridgeInputFile(filepath.Join(directory, "input", "request.json"), 64*1024*1024)
	if e != nil || Hash(request) != j.InputHash {
		return j, errors.New("recovery frozen request mismatch")
	}
	mode, e := checkpointModeForRequest(manifest, request)
	if e != nil {
		return j, e
	}
	expectedProtocol := ""
	if mode == checkpointPauseV1 {
		expectedProtocol = PauseProtocol
	}
	if j.PauseProtocol != expectedProtocol {
		return j, errors.New("recovery pause protocol differs from frozen request")
	}
	if mode != checkpointPauseV1 && (j.Checkpoint != nil || j.CheckpointSeal != nil || j.PauseRequested || j.PauseID != "") {
		return j, errors.New("recovery mixed checkpoint protocol")
	}
	if mode == checkpointDisabled && (j.Paused || j.CheckpointSequence != 0) {
		return j, errors.New("recovery unnegotiated checkpoint")
	}
	if j.Paused && (!j.ContextReady || !j.ProtocolComplete || j.CheckpointSequence <= 0 || j.Acknowledged < j.CheckpointSequence || j.Acknowledged != j.Frames || j.State != "PAUSED" || j.Receipt.ExitCode != 0 || !j.Receipt.OutputCopied || j.Cancelled) {
		return j, errors.New("recovery pause terminal incomplete")
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
	if j.Checkpoint != nil {
		checkpoint, e := readPauseFile(filepath.Join(directory, "checkpoint.sealed.json"))
		if e != nil || int64(len(checkpoint)) != j.Checkpoint.Bytes || Hash(checkpoint) != j.Checkpoint.ContentHash {
			return j, errors.New("recovery checkpoint bytes changed")
		}
	}
	if mode == checkpointPauseV1 && j.Paused && (j.CheckpointSeal == nil || j.Checkpoint == nil || (&Bridge{directory: directory, journal: j}).validateCheckpointSeal(*j.CheckpointSeal) != nil) {
		return j, errors.New("recovery checkpoint seal missing")
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

// readPauseFile opens the final path without following a reparse point and
// denies concurrent writes/deletion while reading at most 12 MiB + 1 byte.
func readPauseFile(path string) ([]byte, error) {
	return readBridgeInputFile(path, MaxPauseCheckpointBytes)
}

func readBridgeInputFile(path string, maxBytes int64) ([]byte, error) {
	actual, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(path)) {
		return nil, errors.New("checkpoint reparse rejected")
	}
	p, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return nil, err
	}
	handle, err := windows.CreateFile(p, windows.GENERIC_READ, windows.FILE_SHARE_READ, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, err
	}
	file := os.NewFile(uintptr(handle), path)
	defer file.Close()
	finalPath := make([]uint16, 32768)
	count, e := windows.GetFinalPathNameByHandle(handle, &finalPath[0], uint32(len(finalPath)), 0)
	expectedPath := strings.TrimPrefix(filepath.Clean(path), `\\?\`)
	if e != nil || count >= uint32(len(finalPath)) || !strings.EqualFold(strings.TrimPrefix(windows.UTF16ToString(finalPath[:count]), `\\?\`), expectedPath) {
		return nil, errors.New("checkpoint opened path differs")
	}
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(handle, &info); err != nil || info.FileAttributes&(windows.FILE_ATTRIBUTE_REPARSE_POINT|windows.FILE_ATTRIBUTE_DIRECTORY) != 0 {
		return nil, errors.New("regular non-reparse checkpoint required")
	}
	stat, err := file.Stat()
	if err != nil || !stat.Mode().IsRegular() || stat.Size() <= 0 || stat.Size() > maxBytes {
		return nil, errors.New("checkpoint size invalid")
	}
	raw, err := io.ReadAll(io.LimitReader(file, maxBytes+1))
	if err != nil || int64(len(raw)) > maxBytes || int64(len(raw)) != stat.Size() {
		return nil, errors.New("checkpoint read bound violated")
	}
	return raw, nil
}
func (w *Bridge) capturePauseCheckpoint(frame BridgeFrame) error {
	var checkpoint PauseCheckpoint
	if !w.journal.PauseRequested || w.journal.Checkpoint != nil || frame.Path != PauseCheckpointFilename || frame.Key != "checkpoint.sealed" || json.Unmarshal(frame.Payload, &checkpoint) != nil || checkpoint.Version != PauseProtocol || checkpoint.PauseID != w.journal.PauseID || checkpoint.Bytes <= 0 || checkpoint.Bytes > MaxPauseCheckpointBytes || "sha256:"+checkpoint.InputHash != w.journal.InputHash || checkpoint.ModelCalls < 0 || checkpoint.ToolCalls < 0 || checkpoint.QueueCut < 0 || !validPauseHash(checkpoint.CommandLedgerHash) || checkpoint.SDKSessionID == "" {
		return errors.New("invalid bound pause checkpoint")
	}
	binding, err := bridgeMap(checkpoint.Binding)
	if err != nil || w.validateControlBinding(binding) != nil {
		return errors.New("checkpoint binding mismatch")
	}
	for _, stream := range w.modelStreams {
		if !stream.closed || stream.failed || stream.creditedObservation != stream.observationSequence {
			return errors.New("checkpoint before stream drain")
		}
	}
	raw, err := readPauseFile(filepath.Join(w.journal.Identity.StagingDirectory, "output", PauseCheckpointFilename))
	if err != nil {
		return err
	}
	if int64(len(raw)) != checkpoint.Bytes || Hash(raw) != checkpoint.ContentHash {
		return errors.New("checkpoint content mismatch")
	}
	dest := filepath.Join(w.directory, "checkpoint.sealed.json")
	file, err := os.OpenFile(dest, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	_, err = file.Write(raw)
	if err == nil {
		err = file.Sync()
	}
	err = errors.Join(err, file.Close())
	if err != nil {
		return err
	}
	w.journal.Checkpoint = &checkpoint
	return nil
}
func (w *Bridge) validateCheckpointSeal(seal CheckpointSeal) error {
	c := w.journal.Checkpoint
	if c == nil || seal.Type != "checkpoint.sealed" || seal.Version != PauseProtocol || seal.Sequence != w.journal.CheckpointSequence || seal.PauseID != c.PauseID || seal.ContentHash != c.ContentHash || seal.CheckpointUsePrincipal == "" || seal.CheckpointArtifactID == "" || !validPauseHash(seal.CheckpointUseReceiptHash) || !validPauseHash(seal.JournalCheckpointHash) {
		return errors.New("incomplete checkpoint seal")
	}
	a, e := canonicalHash(seal.Binding)
	b, f := canonicalHash(c.Binding)
	if e != nil || f != nil || a != b {
		return errors.New("checkpoint seal binding changed")
	}
	fact, err := readPauseFile(filepath.Join(w.directory, "checkpoint-"+strconv.FormatInt(seal.Sequence, 10)+".json"))
	if err != nil || len(fact) > 64*1024 || Hash(fact) != seal.JournalCheckpointHash {
		return errors.New("durable checkpoint journal fact missing or changed")
	}
	value, err := bridgeMap(fact)
	binding, _ := bridgeMap(c.Binding)
	if err != nil || value["project_id"] != binding["project_id"] || value["run_id"] != binding["run_id"] || bridgeNumber(value, "epoch") != bridgeNumber(binding, "runtime_epoch") || value["manifest_hash"] != w.journal.ManifestHash || value["dispatch_key"] != w.journal.DispatchKey || bridgeNumber(value, "sequence") != seal.Sequence || value["content_hash"] != c.ContentHash {
		return errors.New("checkpoint journal identity mismatch")
	}
	return nil
}
func validPauseHash(v string) bool {
	if len(v) != 71 || !strings.HasPrefix(v, "sha256:") {
		return false
	}
	for _, c := range v[7:] {
		if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'f') {
			return false
		}
	}
	return true
}

// SealCheckpoint must be called only after Core has durably recorded the exact
// bytes as a CHECKPOINT Artifact and its authorized use. It persists the receipt
// before the worker can observe the acknowledgement.
func (w *Bridge) SealCheckpoint(ctx context.Context, seal CheckpointSeal) error {
	return w.Acknowledge(ctx, seal.Sequence, map[string]any{"sequence": seal.Sequence, "key": "checkpoint.sealed", "state": "CONFIRMED", "payload": seal})
}

// CheckpointBytes returns the already captured trusted bytes, never a second
// read of the sandbox file. Core hashes and stores these exact bytes.
func (w *Bridge) CheckpointBytes() ([]byte, error) {
	w.mu.Lock()
	defer w.mu.Unlock()
	if w.journal.Checkpoint == nil {
		return nil, errors.New("checkpoint not captured")
	}
	raw, err := readPauseFile(filepath.Join(w.directory, "checkpoint.sealed.json"))
	if err != nil {
		return nil, err
	}
	if Hash(raw) != w.journal.Checkpoint.ContentHash {
		return nil, errors.New("trusted checkpoint changed")
	}
	return raw, nil
}

func samePauseBinding(a, b json.RawMessage) bool {
	x, e := canonicalHash(a)
	y, f := canonicalHash(b)
	return e == nil && f == nil && x == y
}

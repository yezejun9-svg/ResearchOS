//go:build windows

package runtime

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

func checkpointCompatInputs(backend string, protocol any) ([]byte, []byte) {
	manifest, _ := json.Marshal(map[string]any{"task_id": "task", "run_id": "run", "epoch": 1, "dispatch_key": "dispatch", "admission": map[string]any{"profile": map[string]any{"backend": backend, "outputs": []any{}}}})
	request := map[string]any{"task_id": "task", "run_id": "run", "epoch": 1}
	if protocol != nil {
		request["pause_protocol"] = protocol
	}
	raw, _ := json.Marshal(request)
	return manifest, raw
}

func TestBridgeCheckpointModeFrozenInputs(t *testing.T) {
	for _, tc := range []struct {
		name, backend string
		protocol      any
		mode          bridgeCheckpointMode
		fails         bool
	}{
		{"legacy", "fixture", nil, checkpointLegacy, false},
		{"old-mu-normal", "mu-sdk-broker-v1", nil, checkpointDisabled, false},
		{"mu-v1", "mu-sdk-broker-v1", PauseProtocol, checkpointPauseV1, false},
		{"non-mu-explicit-v1", "fixture", PauseProtocol, checkpointPauseV1, false},
		{"unknown", "fixture", "RESEARCHOS_PAUSE_V2", 0, true},
		{"empty-negotiation", "fixture", "", 0, true},
		{"invalid-type", "fixture", true, 0, true},
		{"no-profile", "", nil, 0, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			manifest, raw := checkpointCompatInputs(tc.backend, tc.protocol)
			m, _ := bridgeMap(manifest)
			mode, err := checkpointModeForRequest(m, raw)
			if (err != nil) != tc.fails || err == nil && mode != tc.mode {
				t.Fatalf("mode=%v err=%v", mode, err)
			}
		})
	}
	manifest, raw := checkpointCompatInputs("fixture", nil)
	m, _ := bridgeMap(manifest)
	for _, key := range []string{"task_id", "run_id", "epoch"} {
		t.Run("foreign-"+key, func(t *testing.T) {
			r, _ := bridgeMap(raw)
			r[key] = "foreign"
			bad, _ := json.Marshal(r)
			if _, err := checkpointModeForRequest(m, bad); err == nil {
				t.Fatal("foreign request accepted")
			}
		})
	}
}

func checkpointCompatBridge(t *testing.T, backend string, protocol any) *Bridge {
	t.Helper()
	manifest, request := checkpointCompatInputs(backend, protocol)
	m, _ := bridgeMap(manifest)
	mode, err := checkpointModeForRequest(m, request)
	if err != nil {
		t.Fatal(err)
	}
	directory := t.TempDir()
	f, err := os.Create(filepath.Join(directory, "stdout.raw"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { f.Close() })
	w := &Bridge{directory: directory, checkpointMode: mode, stdout: f, frames: make(chan BridgeFrame, 8), streamOffsets: map[string]int64{}, journal: BridgeJournal{Manifest: manifest, InputHash: Hash(request), ContextReady: true, Frames: 1, Acknowledged: 1}}
	if mode == checkpointPauseV1 {
		w.journal.PauseProtocol = PauseProtocol
	}
	return w
}

func checkpointCompatConsume(w *Bridge, frame BridgeFrame) error {
	raw, _ := json.Marshal(frame)
	return w.consume(sandbox.StreamChunk{Stream: "stdout", Offset: w.streamOffsets["stdout"], Data: append(raw, '\n')})
}

func TestBridgeCheckpointCrossModeFrames(t *testing.T) {
	for _, tc := range []struct {
		name, backend string
		protocol      any
		frame         BridgeFrame
		fails         bool
	}{
		{"legacy-inline", "fixture", nil, BridgeFrame{Sequence: 2, Type: "checkpoint", Payload: json.RawMessage(`{"cursor":"saved"}`)}, false},
		{"legacy-inline-file-label", "fixture", nil, BridgeFrame{Sequence: 2, Type: "checkpoint", Path: "checkpoint.json", Payload: json.RawMessage(`{"cursor":"saved"}`)}, false},
		{"legacy-v1-file", "fixture", nil, BridgeFrame{Sequence: 2, Type: "checkpoint", Path: PauseCheckpointFilename, Payload: json.RawMessage(`{}`)}, true},
		{"legacy-v1-key", "fixture", nil, BridgeFrame{Sequence: 2, Type: "checkpoint", Key: "checkpoint.sealed", Payload: json.RawMessage(`{}`)}, true},
		{"legacy-v1-payload", "fixture", nil, BridgeFrame{Sequence: 2, Type: "checkpoint", Payload: json.RawMessage(`{"version":"RESEARCHOS_PAUSE_V1"}`)}, true},
		{"legacy-empty", "fixture", nil, BridgeFrame{Sequence: 2, Type: "checkpoint"}, true},
		{"mu-unnegotiated-inline", "mu-sdk-broker-v1", nil, BridgeFrame{Sequence: 2, Type: "checkpoint", Payload: json.RawMessage(`{}`)}, true},
		{"mu-unnegotiated-normal", "mu-sdk-broker-v1", nil, BridgeFrame{Sequence: 2, Type: "turn.completed"}, false},
		{"v1-inline", "mu-sdk-broker-v1", PauseProtocol, BridgeFrame{Sequence: 2, Type: "checkpoint", Payload: json.RawMessage(`{"cursor":"saved"}`)}, true},
		{"v1-missing-metadata", "mu-sdk-broker-v1", PauseProtocol, BridgeFrame{Sequence: 2, Type: "checkpoint", Path: PauseCheckpointFilename, Key: "checkpoint.sealed", Payload: json.RawMessage(`{}`)}, true},
		{"explicit-non-mu-cannot-fallback", "fixture", PauseProtocol, BridgeFrame{Sequence: 2, Type: "checkpoint", Payload: json.RawMessage(`{}`)}, true},
		{"legacy-oversized-inline", "fixture", nil, BridgeFrame{Sequence: 2, Type: "checkpoint", Payload: json.RawMessage(`{"cursor":"` + strings.Repeat("x", 64*1024) + `"}`)}, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			w := checkpointCompatBridge(t, tc.backend, tc.protocol)
			err := checkpointCompatConsume(w, tc.frame)
			if (err != nil) != tc.fails {
				t.Fatalf("err=%v", err)
			}
			if tc.fails && w.journal.Frames != 1 {
				t.Fatal("rejected frame advanced journal")
			}
		})
	}
	for _, tc := range []struct {
		name, backend string
		protocol      any
		payload       json.RawMessage
		fails         bool
	}{
		{"legacy-empty-paused", "fixture", nil, nil, false},
		{"legacy-typed-paused", "fixture", nil, json.RawMessage(`{"version":"RESEARCHOS_PAUSE_V1"}`), true},
		{"mu-empty-paused", "mu-sdk-broker-v1", nil, nil, true},
		{"v1-empty-paused", "mu-sdk-broker-v1", PauseProtocol, nil, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			w := checkpointCompatBridge(t, tc.backend, tc.protocol)
			w.journal.CheckpointSequence = 1
			if tc.protocol == PauseProtocol {
				w.journal.Checkpoint = &PauseCheckpoint{Version: PauseProtocol, Binding: json.RawMessage(`{}`)}
				w.journal.CheckpointSeal = &CheckpointSeal{Version: PauseProtocol}
			}
			err := checkpointCompatConsume(w, BridgeFrame{Sequence: 2, Type: "turn.paused", Payload: tc.payload})
			if (err != nil) != tc.fails {
				t.Fatalf("err=%v", err)
			}
			if tc.fails && w.journal.Paused {
				t.Fatal("rejected pause became terminal")
			}
		})
	}
}

func TestBridgeCheckpointCrossModeAcknowledgements(t *testing.T) {
	legacy := map[string]any{"sequence": 2, "type": "checkpoint.sealed", "artifact_ref": map[string]any{"entity_type": "Artifact", "id": "artifact"}}
	typed := map[string]any{"sequence": 2, "key": "checkpoint.sealed", "state": "CONFIRMED", "payload": map[string]any{"version": PauseProtocol}}
	for _, tc := range []struct {
		name, backend   string
		protocol, reply any
	}{
		{"v1-legacy-ack", "mu-sdk-broker-v1", PauseProtocol, legacy},
		{"v1-weak-ack", "mu-sdk-broker-v1", PauseProtocol, typed},
		{"legacy-typed-ack", "fixture", nil, typed},
		{"legacy-nil-ack", "fixture", nil, nil},
		{"mu-unnegotiated-legacy-ack", "mu-sdk-broker-v1", nil, legacy},
	} {
		t.Run(tc.name, func(t *testing.T) {
			w := checkpointCompatBridge(t, tc.backend, tc.protocol)
			w.journal.Frames = 2
			w.journal.CheckpointSequence = 2
			if err := w.Acknowledge(context.Background(), 2, tc.reply); err == nil {
				t.Fatal("cross-mode or incomplete ACK accepted")
			}
			if w.journal.Acknowledged != 1 {
				t.Fatal("invalid ACK advanced state")
			}
		})
	}
}

func checkpointCompatTerminal(t *testing.T, backend string, protocol any) (string, BridgeJournal) {
	t.Helper()
	directory := t.TempDir()
	manifest, request := checkpointCompatInputs(backend, protocol)
	hash, _ := canonicalHash(manifest)
	if err := os.Mkdir(filepath.Join(directory, "input"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, "input", "request.json"), request, 0600); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"stdout.raw", "stderr.raw"} {
		if err := os.WriteFile(filepath.Join(directory, name), nil, 0600); err != nil {
			t.Fatal(err)
		}
	}
	j := BridgeJournal{Manifest: manifest, ManifestHash: hash, DispatchKey: "dispatch", InputHash: Hash(request), Ended: "2026-10-14T00:00:00Z", State: "PAUSED", Frames: 3, Acknowledged: 3, ContextReady: true, ProtocolComplete: true, Paused: true, CheckpointSequence: 2, StdoutHash: Hash(nil), StderrHash: Hash(nil), Receipt: sandbox.Receipt{Stopped: true, StreamsDrained: true, CleanupComplete: true, OutputCopied: true}}
	if protocol == PauseProtocol {
		j.PauseProtocol = PauseProtocol
		j.PauseRequested = true
		j.PauseID = "pause"
		checkpoint := []byte(`{"sdk":"frozen"}`)
		binding := json.RawMessage(`{"project_id":"project","run_id":"run","runtime_epoch":1}`)
		j.Checkpoint = &PauseCheckpoint{Version: PauseProtocol, PauseID: "pause", Binding: binding, Bytes: int64(len(checkpoint)), ContentHash: Hash(checkpoint)}
		fact, _ := json.Marshal(map[string]any{"project_id": "project", "run_id": "run", "epoch": 1, "manifest_hash": hash, "dispatch_key": "dispatch", "sequence": 2, "content_hash": j.Checkpoint.ContentHash})
		if err := os.WriteFile(filepath.Join(directory, "checkpoint.sealed.json"), checkpoint, 0600); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(directory, "checkpoint-2.json"), fact, 0600); err != nil {
			t.Fatal(err)
		}
		j.CheckpointSeal = &CheckpointSeal{Type: "checkpoint.sealed", Version: PauseProtocol, PauseID: "pause", Binding: binding, Sequence: 2, ContentHash: j.Checkpoint.ContentHash, CheckpointArtifactID: "artifact", CheckpointUsePrincipal: "executor", CheckpointUseReceiptHash: Hash([]byte("use")), JournalCheckpointHash: Hash(fact)}
	}
	return directory, j
}

func TestBridgeCheckpointRecoveryNoProtocolDowngrade(t *testing.T) {
	for _, tc := range []struct {
		name, backend string
		protocol      any
		mutate        func(string, *BridgeJournal)
		fails         bool
	}{
		{"legacy-paused", "fixture", nil, nil, false},
		{"v1-paused", "mu-sdk-broker-v1", PauseProtocol, nil, false},
		{"v1-erased-mode", "mu-sdk-broker-v1", PauseProtocol, func(_ string, j *BridgeJournal) { j.PauseProtocol = "" }, true},
		{"v1-erased-all-pause-fields", "fixture", PauseProtocol, func(_ string, j *BridgeJournal) {
			j.PauseProtocol = ""
			j.Checkpoint = nil
			j.CheckpointSeal = nil
			j.PauseRequested = false
			j.PauseID = ""
		}, true},
		{"v1-changed-mode", "mu-sdk-broker-v1", PauseProtocol, func(_ string, j *BridgeJournal) { j.PauseProtocol = "RESEARCHOS_PAUSE_V2" }, true},
		{"v1-missing-seal", "mu-sdk-broker-v1", PauseProtocol, func(_ string, j *BridgeJournal) { j.CheckpointSeal = nil }, true},
		{"v1-changed-checkpoint", "mu-sdk-broker-v1", PauseProtocol, func(d string, j *BridgeJournal) {
			os.WriteFile(filepath.Join(d, "checkpoint.sealed.json"), []byte("changed"), 0600)
		}, true},
		{"v1-erased-request-mode", "mu-sdk-broker-v1", PauseProtocol, func(d string, j *BridgeJournal) {
			_, r := checkpointCompatInputs("mu-sdk-broker-v1", nil)
			os.WriteFile(filepath.Join(d, "input", "request.json"), r, 0600)
		}, true},
		{"foreign-request-even-with-new-hash", "fixture", nil, func(d string, j *BridgeJournal) {
			r := []byte(`{"task_id":"task","run_id":"foreign","epoch":1}`)
			j.InputHash = Hash(r)
			os.WriteFile(filepath.Join(d, "input", "request.json"), r, 0600)
		}, true},
		{"changed-manifest-profile", "mu-sdk-broker-v1", PauseProtocol, func(_ string, j *BridgeJournal) { j.Manifest, _ = checkpointCompatInputs("fixture", nil) }, true},
		{"legacy-mixed-seal", "fixture", nil, func(_ string, j *BridgeJournal) { j.CheckpointSeal = &CheckpointSeal{} }, true},
		{"legacy-undrained", "fixture", nil, func(_ string, j *BridgeJournal) { j.Receipt.StreamsDrained = false }, true},
		{"legacy-unacked", "fixture", nil, func(_ string, j *BridgeJournal) { j.Acknowledged = 1 }, true},
		{"mu-unnegotiated-paused", "mu-sdk-broker-v1", nil, nil, true},
		{"mu-unnegotiated-normal", "mu-sdk-broker-v1", nil, func(_ string, j *BridgeJournal) { j.Paused = false; j.CheckpointSequence = 0; j.State = "SETTLED" }, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			d, j := checkpointCompatTerminal(t, tc.backend, tc.protocol)
			hash := j.ManifestHash
			if tc.mutate != nil {
				tc.mutate(d, &j)
			}
			if err := save(filepath.Join(d, "bridge.json"), j); err != nil {
				t.Fatal(err)
			}
			_, err := ReadBridgeTerminal(d, hash)
			if (err != nil) != tc.fails {
				t.Fatalf("err=%v", err)
			}
		})
	}
}

func TestBridgeCheckpointFrozenRequestNoReparse(t *testing.T) {
	directory := t.TempDir()
	targetDirectory := filepath.Join(directory, "target")
	if err := os.Mkdir(targetDirectory, 0700); err != nil {
		t.Fatal(err)
	}
	target := filepath.Join(targetDirectory, "request.json")
	if err := os.WriteFile(target, []byte(`{"request":"frozen"}`), 0600); err != nil {
		t.Fatal(err)
	}
	linkDirectory := filepath.Join(directory, "input")
	// A directory junction exercises reparse ancestors without requiring the
	// machine-wide symbolic-link privilege or Developer Mode.
	if output, err := exec.Command("cmd", "/c", "mklink", "/J", linkDirectory, targetDirectory).CombinedOutput(); err != nil {
		t.Fatalf("create junction negative: %v %s", err, output)
	}
	if _, err := readBridgeInputFile(filepath.Join(linkDirectory, "request.json"), 64*1024*1024); err == nil {
		t.Fatal("reparse request accepted")
	}
	if _, err := readBridgeInputFile(target, 4); err == nil {
		t.Fatal("bounded request reader exceeded limit")
	}
}

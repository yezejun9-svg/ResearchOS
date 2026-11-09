//go:build windows

package runtime

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"strconv"
	"strings"
	"testing"
	"time"
)

func TestBridgeQueueEmptyNeedsSDKProof(t *testing.T) {
	j := BridgeJournal{Manifest: json.RawMessage(`{"task_id":"task","run_id":"run","epoch":1,"admission":{"profile":{}}}`), QueueRequired: true, Frames: 4, Acknowledged: 4, State: "SETTLED", ProtocolComplete: true, Receipt: sandbox.Receipt{Stopped: true, StreamsDrained: true}}
	observation, err := j.Observation()
	if err != nil {
		t.Fatal(err)
	}
	if observation["queue_empty"] != false {
		t.Fatal("frame ACK count falsely proved SDK queue empty")
	}
	j.QueueSealed = true
	observation, err = j.Observation()
	if err != nil || observation["queue_empty"] != true {
		t.Fatal("sealed queue proof missing", err)
	}
	j.QueueSealed = false
	j.Cancelled = true
	observation, _ = j.Observation()
	if observation["queue_empty"] != false {
		t.Fatal("physical process death falsely proved queue empty")
	}
	j.QueueIdle = true
	j.QueueCancelIdle = true
	observation, _ = j.Observation()
	if observation["queue_empty"] != true {
		t.Fatal("cancel idle witness missing")
	}
}

func TestBridgeControlIdentityRejectsForeignProcessAndEpoch(t *testing.T) {
	identity := sandbox.Identity{PID: 12, Created: 123, Job: "job", SID: "sid", Profile: "profile", StagingDirectory: "stage"}
	bridge := &Bridge{journal: BridgeJournal{Manifest: json.RawMessage(`{"task_id":"task","run_id":"run","epoch":7}`), ManifestHash: "sha256:manifest", DispatchKey: "dispatch", Identity: identity}}
	raw := []byte(`{"task_id":"task","run_id":"run","runtime_epoch":7,"dispatch_key":"dispatch","manifest_hash":"sha256:manifest","queue_generation":"generation","process_identity":{"pid":12,"process_created_ns":"123","job":"job","appcontainer_sid":"sid","profile":"profile","staging_directory":"stage"}}`)
	good, err := bridgeMap(raw)
	if err != nil || bridge.validateControlBinding(good) != nil {
		t.Fatal("valid exact binding refused", err)
	}
	for _, field := range []string{"run_id", "task_id", "runtime_epoch", "dispatch_key", "manifest_hash", "process_identity"} {
		t.Run(field, func(t *testing.T) {
			bad, _ := bridgeMap(raw)
			bad[field] = "foreign"
			if bridge.validateControlBinding(bad) == nil {
				t.Fatal("foreign binding accepted")
			}
		})
	}
}

var pauseWorkerBundle = flag.String("pause-worker-bundle", "", "explicit current candidate production bundle for native isolated pause test")
var pauseWorkerNode = flag.String("pause-worker-node", "", "explicit Node executable for native isolated pause test")

func TestBridgeProductionPauseCheckpointNative(t *testing.T) {
	if *pauseWorkerBundle == "" || *pauseWorkerNode == "" {
		t.Skip("explicit candidate assets required; no native proof claimed")
	}
	bundle, err := os.ReadFile(*pauseWorkerBundle)
	if err != nil {
		t.Fatal(err)
	}
	node, err := os.ReadFile(*pauseWorkerNode)
	if err != nil {
		t.Fatal(err)
	}
	config := map[string]any{"ref": "fixture", "api": "openai-completions", "provider": "openai", "model": "fixture", "endpoint": "https://fixture.invalid", "route": "broker", "max_output_tokens": 128, "max_calls": 8, "tools": []any{}}
	workerConfig, _ := json.Marshal(config)
	profile := map[string]any{"backend": "mu-sdk-broker-v1", "model": "fixture", "sandbox": "appcontainer-zero-capabilities-v1", "adapter_revision": BridgeRevision, "build_hash": Hash(node), "bundle_hash": Hash(bundle), "model_config": config, "argv": []string{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}, "timeout_seconds": 60, "outputs": []string{"result.json"}}
	manifest, _ := json.Marshal(map[string]any{"task_id": "task", "run_id": "run", "epoch": 1, "dispatch_key": "dispatch-pause", "admission": map[string]any{"profile": profile}})
	manifestHash, _ := canonicalHash(manifest)
	binding := map[string]any{"project_id": "project", "session_id": "session", "task_id": "task", "run_id": "run", "runtime_epoch": 1, "queue_generation": "generation", "dispatch_key": "dispatch-pause", "manifest_hash": manifestHash}
	request, _ := json.Marshal(map[string]any{"task_id": "task", "run_id": "run", "epoch": 1, "input_refs": []any{}, "context": map[string]any{}, "task_title": "native synthetic pause", "task_description": "one original prompt", "queue_control": true, "queue_binding": binding, "pause_protocol": PauseProtocol})
	directory := filepath.Join(t.TempDir(), "dispatch")
	ctx, cancel := context.WithTimeout(context.Background(), 65*time.Second)
	defer cancel()
	w, err := StartBridge(ctx, directory, BridgeRequest{WorkerID: "native-pause", Manifest: manifest, ManifestHash: manifestHash, Executable: *pauseWorkerNode, Inputs: map[string][]byte{"request.json": request, "worker.json": workerConfig, "mu-worker.mjs": bundle}, BeforeResume: func(i sandbox.Identity) error {
		binding["process_identity"] = map[string]any{"pid": i.PID, "process_created_ns": strconv.FormatInt(i.Created, 10), "job": i.Job, "appcontainer_sid": i.SID, "profile": i.Profile, "staging_directory": i.StagingDirectory}
		return nil
	}})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { w.Cancel("test cleanup"); <-w.Done() })
	send := func(value map[string]any) {
		t.Helper()
		value["binding"] = binding
		if e := w.Control(ctx, value); e != nil {
			t.Fatal(e)
		}
	}
	var sequences []int64
	var checkpointSequence int64
	var checkpointRaw []byte
	for {
		select {
		case frame, ok := <-w.Frames():
			if !ok {
				goto done
			}
			sequences = append(sequences, frame.Sequence)
			switch frame.Type {
			case "context.ready":
				if err = w.Acknowledge(ctx, frame.Sequence, nil); err != nil {
					t.Fatal(err)
				}
				send(map[string]any{"type": "command.deliver", "initialize": true, "command": nil, "pause_protocol": PauseProtocol})
			case "command.accepted":
				payload, _ := bridgeMap(frame.Payload)
				var reply any
				if payload["initialized"] == true {
					reply = map[string]any{"sequence": frame.Sequence, "key": "command.initialize", "state": "CONFIRMED", "payload": map[string]any{}}
				}
				if err = w.Acknowledge(ctx, frame.Sequence, reply); err != nil {
					t.Fatal(err)
				}
			case "effect.request":
				if frame.Sequence != 3 {
					t.Fatal("unexpected extra model call")
				}
				for i, delivery := range []string{"STEER", "FOLLOW_UP"} {
					content, _ := json.Marshal(map[string]any{"text": strings.Repeat("x", 20000), "attachments": []any{}})
					send(map[string]any{"type": "command.deliver", "command": map[string]any{"command_id": fmt.Sprint("c", i), "message_id": fmt.Sprint("m", i), "queue_sequence": i + 1, "content": string(content), "content_hash": Hash(content), "delivery": delivery}})
				}
				send(map[string]any{"type": "command.pause", "version": PauseProtocol, "pause_id": "native-pause"})
				sse := []byte("data: {\"id\":\"fixture\",\"object\":\"chat.completion.chunk\",\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"reply\"},\"finish_reason\":null}]}\n\ndata: {\"id\":\"fixture\",\"object\":\"chat.completion.chunk\",\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
				var packed bytes.Buffer
				gzipWriter := gzip.NewWriter(&packed)
				_, _ = gzipWriter.Write(sse)
				_ = gzipWriter.Close()
				reply := map[string]any{"sequence": frame.Sequence, "key": frame.Key, "state": "CONFIRMED", "payload": map[string]any{"status": 200, "content_type": "text/event-stream", "body_encoding": "gzip+base64", "body_gzip_base64": base64.StdEncoding.EncodeToString(packed.Bytes()), "body_sha256": Hash(sse)}}
				if err = w.Acknowledge(ctx, frame.Sequence, reply); err != nil {
					t.Fatal(err)
				}
			case "checkpoint":
				checkpointSequence = frame.Sequence
				raw, e := w.CheckpointBytes()
				checkpointRaw = raw
				if e != nil {
					t.Fatal(e)
				}
				if len(raw) <= 64*1024 {
					t.Fatal("checkpoint file must prove transport beyond line bound")
				}
				var snap map[string]any
				if json.Unmarshal(raw, &snap) != nil {
					t.Fatal("invalid checkpoint")
				}
				j := w.Read()
				if Hash(raw) != j.Checkpoint.ContentHash {
					t.Fatal("trusted byte mismatch")
				}
				// The Core-shaped durable journal fact is a test stand-in for the later
				// canonical coordinator card. No DB Artifact acceptance is claimed here.
				fact := map[string]any{"project_id": "project", "run_id": "run", "epoch": 1, "manifest_hash": manifestHash, "dispatch_key": "dispatch-pause", "sequence": frame.Sequence, "content_hash": Hash(raw), "payload": json.RawMessage(frame.Payload)}
				factRaw, _ := json.Marshal(fact)
				f, e := os.OpenFile(filepath.Join(directory, "checkpoint-"+strconv.FormatInt(frame.Sequence, 10)+".json"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
				if e != nil {
					t.Fatal(e)
				}
				_, e = f.Write(factRaw)
				if e == nil {
					e = f.Sync()
				}
				e = errors.Join(e, f.Close())
				if e != nil {
					t.Fatal(e)
				}
				b, _ := json.Marshal(binding)
				seal := CheckpointSeal{Type: "checkpoint.sealed", Version: PauseProtocol, PauseID: "native-pause", Binding: b, Sequence: frame.Sequence, ContentHash: Hash(raw), CheckpointArtifactID: "fixture-artifact", CheckpointUseReceiptHash: Hash([]byte("fixture-use")), CheckpointUsePrincipal: "fixture-executor", JournalCheckpointHash: Hash(factRaw)}
				if err = w.SealCheckpoint(ctx, seal); err != nil {
					t.Fatal(err)
				}
			case "turn.paused":
				if frame.Sequence <= checkpointSequence {
					t.Fatal("non-advancing paused sequence")
				}
				if err = w.Acknowledge(ctx, frame.Sequence, nil); err != nil {
					t.Fatal(err)
				}
			default:
				t.Fatalf("unexpected frame %s", frame.Type)
			}
		case <-ctx.Done():
			t.Fatal(ctx.Err())
		}
	}
done:
	<-w.Done()
	j := w.Read()
	if j.State != "PAUSED" || !j.Receipt.Stopped || !j.Receipt.StreamsDrained || !j.Receipt.CleanupComplete || !j.Receipt.OutputCopied || j.Frames != j.Acknowledged {
		t.Fatalf("native pause not settled: state=%s frames=%d ack=%d stderr=%s", j.State, j.Frames, j.Acknowledged, string(j.Receipt.Stderr))
	}
	if j.QueueSealed {
		t.Fatal("paused queue incorrectly reported empty/sealed")
	}
	recovered, e := ReadBridgeTerminal(directory, manifestHash)
	if e != nil || !recovered.Paused {
		t.Fatalf("durable recovery: %v", e)
	}
	reviewCaptureBridge(t, "pause", w.Directory())
	t.Logf("NATIVE_SYNTHETIC production worker+bridge, frames=%v bytes=%d checkpoint=%d model_calls=%d stopped=%v drained=%v; Core canonical integration OPEN", sequences, j.Checkpoint.Bytes, j.CheckpointSequence, j.Checkpoint.ModelCalls, j.Receipt.Stopped, j.Receipt.StreamsDrained)
	// A new physical AppContainer resumes the original SDK header/tree under
	// a same-Run successor activation. The old checkpoint bytes remain exact.
	manifest2, _ := json.Marshal(map[string]any{"task_id": "task", "run_id": "run", "epoch": 2, "dispatch_key": "dispatch-resume", "admission": map[string]any{"profile": profile}})
	hash2, _ := canonicalHash(manifest2)
	binding2 := map[string]any{"project_id": "project", "session_id": "session", "task_id": "task", "run_id": "run", "runtime_epoch": 2, "queue_generation": "generation", "dispatch_key": "dispatch-resume", "manifest_hash": hash2}
	request2, _ := json.Marshal(map[string]any{"task_id": "task", "run_id": "run", "epoch": 2, "input_refs": []any{}, "context": map[string]any{}, "task_title": "native synthetic pause", "task_description": "one original prompt", "queue_control": true, "queue_binding": binding2, "pause_protocol": PauseProtocol, "pause_activation": map[string]any{"version": PauseProtocol, "previous_epoch": 1, "new_epoch": 2, "checkpoint_hash": j.Checkpoint.ContentHash, "checkpoint_artifact_id": j.CheckpointSeal.CheckpointArtifactID, "checkpoint_use_receipt_hash": j.CheckpointSeal.CheckpointUseReceiptHash, "checkpoint_use_principal": j.CheckpointSeal.CheckpointUsePrincipal, "carry_use_receipt_hash": Hash([]byte("fixture-carry")), "original_input_hash": j.Checkpoint.InputHash}})
	w2, e := StartBridge(ctx, filepath.Join(t.TempDir(), "resume"), BridgeRequest{WorkerID: "native-resume", Manifest: manifest2, ManifestHash: hash2, Executable: *pauseWorkerNode, Inputs: map[string][]byte{"request.json": request2, "worker.json": workerConfig, "mu-worker.mjs": bundle, PauseCheckpointFilename: checkpointRaw}, BeforeResume: func(i sandbox.Identity) error {
		binding2["process_identity"] = map[string]any{"pid": i.PID, "process_created_ns": strconv.FormatInt(i.Created, 10), "job": i.Job, "appcontainer_sid": i.SID, "profile": i.Profile, "staging_directory": i.StagingDirectory}
		return nil
	}})
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { w2.Cancel("test cleanup"); <-w2.Done() })
	send2 := func(v map[string]any) {
		t.Helper()
		v["binding"] = binding2
		if e := w2.Control(ctx, v); e != nil {
			t.Fatal(e)
		}
	}
	prepared, committed := false, false
	consumed, models := 0, 0
	for frame := range w2.Frames() {
		var reply any
		switch frame.Type {
		case "context.ready":
		case "command.accepted":
			p, _ := bridgeMap(frame.Payload)
			if p["initialized"] != true {
				t.Fatal("restored command redelivered")
			}
			reply = map[string]any{"sequence": frame.Sequence, "key": "command.initialize", "state": "CONFIRMED", "payload": map[string]any{}}
		case "command.consumed":
			consumed++
		case "effect.request":
			models++
			if frame.Key != fmt.Sprintf("task:run:2:model:%d", models+1) {
				t.Fatal("effect count reset", frame.Key)
			}
			sse := []byte("data: {\"id\":\"fixture\",\"object\":\"chat.completion.chunk\",\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"resumed\"},\"finish_reason\":null}]}\n\ndata: {\"id\":\"fixture\",\"object\":\"chat.completion.chunk\",\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
			var buf bytes.Buffer
			z := gzip.NewWriter(&buf)
			_, _ = z.Write(sse)
			_ = z.Close()
			reply = map[string]any{"sequence": frame.Sequence, "key": frame.Key, "state": "CONFIRMED", "payload": map[string]any{"status": 200, "content_type": "text/event-stream", "body_encoding": "gzip+base64", "body_gzip_base64": base64.StdEncoding.EncodeToString(buf.Bytes()), "body_sha256": Hash(sse)}}
		case "command.idle", "command.sealed", "turn.completed":
		default:
			t.Fatal("unexpected restored frame", frame.Type)
		}
		if e = w2.Acknowledge(ctx, frame.Sequence, reply); e != nil {
			t.Fatal(e)
		}
		if frame.Type == "context.ready" {
			send2(map[string]any{"type": "command.deliver", "initialize": true, "command": nil, "pause_protocol": PauseProtocol})
		}
		if frame.Type == "command.idle" {
			if !prepared {
				prepared = true
				send2(map[string]any{"type": "command.prepare_seal", "through": 2})
			} else if !committed {
				committed = true
				send2(map[string]any{"type": "command.commit_seal", "through": 2})
			}
		}
	}
	<-w2.Done()
	j2 := w2.Read()
	if j2.State != "EXITED" || !j2.Receipt.Stopped || !j2.Receipt.StreamsDrained || consumed != 2 || models != 2 {
		t.Fatalf("native resume state=%s consumed=%d models=%d stderr=%s", j2.State, consumed, models, string(j2.Receipt.Stderr))
	}
	resultRaw, e := os.ReadFile(filepath.Join(w2.Directory(), "output", "result.json"))
	if e != nil {
		t.Fatal(e)
	}
	result, e := bridgeMap(resultRaw)
	if e != nil || bridgeNumber(result, "model_calls") != 3 || strings.Count(string(resultRaw), "one original prompt") != 1 {
		t.Fatal("restored counts/prompt replay", e)
	}
	if Hash(checkpointRaw) != j.Checkpoint.ContentHash {
		t.Fatal("original checkpoint relabelled")
	}
	reviewCaptureBridge(t, "resume", w2.Directory())
	t.Logf("NATIVE_SYNTHETIC same Run epoch 1 -> 2, consumed=%d model_calls=3 no prompt replay, new process=%d old process=%d", consumed, j2.Identity.PID, j.Identity.PID)

}

func TestPauseCheckpointFileBoundsAndSealRejection(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "checkpoint.json")
	if err := os.WriteFile(path, bytes.Repeat([]byte("x"), MaxPauseCheckpointBytes+1), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := readPauseFile(path); err == nil {
		t.Fatal("oversized checkpoint accepted")
	}
	if err := os.WriteFile(path, []byte("exact"), 0600); err != nil {
		t.Fatal(err)
	}
	raw, err := readPauseFile(path)
	if err != nil || string(raw) != "exact" {
		t.Fatal(err)
	}
	w := &Bridge{directory: root, journal: BridgeJournal{Frames: 4, Acknowledged: 3, CheckpointSequence: 4, Checkpoint: &PauseCheckpoint{Version: PauseProtocol, PauseID: "p", ContentHash: Hash(raw), Binding: json.RawMessage(`{}`)}}}
	for _, reply := range []any{nil, map[string]any{"sequence": 4, "key": "checkpoint.sealed", "state": "CONFIRMED", "payload": map[string]any{"persisted": true}}} {
		if err = w.Acknowledge(context.Background(), 4, reply); err == nil {
			t.Fatal("unsealed checkpoint ACK accepted")
		}
		if w.Read().Acknowledged != 3 {
			t.Fatal("rejected seal advanced ACK")
		}
	}
}

func reviewCaptureBridge(t *testing.T, label, directory string) {
 t.Helper()
 target := filepath.Join("D:\\\u4f5c\u54c1\u96c6\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W17\\W17-03\\bridge_checkpoint_compat_independent_review_codex\\20261014-current-chat\\native-capture", label)
 if e := os.MkdirAll(target,0700); e != nil {t.Fatal(e)}
 names := []string{"bridge.json","stdout.raw","stderr.raw","input/request.json","checkpoint.sealed.json","output/result.json"}
 extra,_ := filepath.Glob(filepath.Join(directory,"checkpoint-*.json"));for _,p := range extra {names=append(names,filepath.Base(p))}
 for _,name := range names {raw,e := os.ReadFile(filepath.Join(directory,filepath.FromSlash(name)));if os.IsNotExist(e) {continue};if e != nil {t.Fatal(e)};out:=filepath.Join(target,filepath.FromSlash(name));if e=os.MkdirAll(filepath.Dir(out),0700);e!=nil {t.Fatal(e)};if e=os.WriteFile(out,raw,0600);e!=nil {t.Fatal(e)}}
}

//go:build windows

package runtime

import (
	"context"
	"encoding/json"
	"errors"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"testing"
	"time"
)

func streamBridgeFixture(t *testing.T) (*Bridge, *ModelStream) {
	t.Helper()
	identity := sandbox.Identity{PID: 12, Created: 123, Job: "job", SID: "sid", Profile: "profile", StagingDirectory: "stage"}
	w := &Bridge{journal: BridgeJournal{Manifest: json.RawMessage(`{"task_id":"task","run_id":"run","epoch":7}`), ManifestHash: Hash([]byte("manifest")), DispatchKey: "dispatch", Identity: identity, QueueRequired: true, QueueInitSequence: 2, Frames: 3, Acknowledged: 2}, modelInitDelivered: true, modelChanged: make(chan struct{}), modelObservations: make(chan ModelStreamObservation, 4), done: make(chan struct{})}
	b := map[string]any{"project_id": "project", "session_id": "session", "task_id": "task", "run_id": "run", "runtime_epoch": 7, "queue_generation": "generation", "dispatch_key": "dispatch", "manifest_hash": w.journal.ManifestHash, "process_identity": map[string]any{"pid": 12, "process_created_ns": "123", "job": "job", "appcontainer_sid": "sid", "profile": "profile", "staging_directory": "stage"}, "effect_sequence": 3, "effect_key": "model:1", "request_hash": Hash([]byte("request"))}
	b["stream_id"] = ModelStreamID(b)
	raw, _ := json.Marshal(b)
	bound, err := bridgeMap(raw)
	if err != nil {
		t.Fatal(err)
	}
	s := &ModelStream{bridge: w, binding: bound, pending: map[int64]ModelStreamFrame{}, observationDigest: Hash(nil)}
	w.modelStreams = []*ModelStream{s}
	return w, s
}

func streamBridgeObserve(s *ModelStream, event, text string) ModelStreamFrame {
	p := map[string]any{"event": event, "text": text, "message_ordinal": 1, "text_part": 0, "sdk_content_index": 0}
	return ModelStreamFrame{ModelStreamVersion, "stream.observe", s.binding, s.observationSequence + 1, s.observationOffset + int64(len(text)), modelStreamHash(map[string]any{"previous": s.observationDigest, "payload": p}), p}
}

func TestModelStreamBridgeAuxiliaryDoesNotConsumeOrdinaryACK(t *testing.T) {
	w, s := streamBridgeFixture(t)
	for i := 0; i < 40; i++ {
		event, text := "text_delta", "中🙂"
		if i == 0 {
			event, text = "text_start", ""
		}
		f := streamBridgeObserve(s, event, text)
		raw, _ := json.Marshal(f)
		if err := w.consumeModelFrame(raw); err != nil {
			t.Fatal(err)
		}
		if err := w.consumeModelFrame(raw); err != nil {
			t.Fatal("exact in-flight duplicate", err)
		}
		if len(w.modelObservations) != 1 {
			t.Fatal("duplicate enqueued second durable callback")
		}
		got := <-w.modelObservations
		if got.Frame.Digest != f.Digest {
			t.Fatal("changed observation")
		}
		delete(s.pending, f.Sequence)
		s.creditedObservation = f.Sequence
	}
	if w.journal.Acknowledged != 2 || w.journal.Frames != 3 || w.journal.QueueIdle || w.journal.QueueSealed {
		t.Fatal("auxiliary credits changed ordinary proof")
	}
	if w.ModelStreamsClosed() {
		t.Fatal("unconfirmed stream closed")
	}
}

func TestModelStreamBridgeRefusesForeignMalformedAndExhausted(t *testing.T) {
	for name, mutate := range map[string]func(*Bridge, *ModelStream, *ModelStreamFrame){
		"init-undelivered": func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { w.modelInitDelivered = false },
		"cancelled":        func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { w.journal.Cancelled = true },
		"old-epoch": func(w *Bridge, s *ModelStream, f *ModelStreamFrame) {
			f.Binding = map[string]any{}
			for k, v := range s.binding {
				f.Binding[k] = v
			}
			f.Binding["runtime_epoch"] = 6
		},
		"sequence-gap":   func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { f.Sequence++ },
		"changed-digest": func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { f.Digest = Hash([]byte("other")) },
		"wrong-offset":   func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { f.Offset = 1 },
		"record-limit": func(w *Bridge, s *ModelStream, f *ModelStreamFrame) {
			w.modelObservationRecords = modelStreamRecordLimit
		},
		"float-index":     func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { f.Payload["text_part"] = 0.5 },
		"string-index":    func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { f.Payload["text_part"] = "0" },
		"null-index":      func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { f.Payload["sdk_content_index"] = nil },
		"extra-field":     func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { f.Payload["secret"] = "fixture" },
		"wrong-direction": func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { f.Type = "stream.data" },
		"early-terminal":  func(w *Bridge, s *ModelStream, f *ModelStreamFrame) { *f = streamBridgeObserve(s, "message_end", "") },
	} {
		t.Run(name, func(t *testing.T) {
			w, s := streamBridgeFixture(t)
			f := streamBridgeObserve(s, "text_start", "")
			mutate(w, s, &f)
			raw, _ := json.Marshal(f)
			if err := w.consumeModelFrame(raw); err == nil {
				t.Fatal("invalid auxiliary accepted")
			}
			if len(w.modelObservations) != 0 {
				t.Fatal("invalid frame reached durable callback")
			}
		})
	}
}

func TestModelStreamBridgeDuplicateAndWindow(t *testing.T) {
	w, s := streamBridgeFixture(t)
	first := streamBridgeObserve(s, "text_start", "")
	raw, _ := json.Marshal(first)
	if err := w.consumeModelFrame(raw); err != nil {
		t.Fatal(err)
	}
	first.Payload["text_part"] = 1
	raw, _ = json.Marshal(first)
	if err := w.consumeModelFrame(raw); err == nil {
		t.Fatal("changed exact-sequence duplicate accepted")
	}
	for i := 0; i < 3; i++ {
		f := streamBridgeObserve(s, "text_delta", "A")
		raw, _ = json.Marshal(f)
		if err := w.consumeModelFrame(raw); err != nil {
			t.Fatal(err)
		}
	}
	f := streamBridgeObserve(s, "text_delta", "B")
	raw, _ = json.Marshal(f)
	if err := w.consumeModelFrame(raw); err == nil {
		t.Fatal("fifth uncredited observation accepted")
	}
}

func TestModelStreamTerminalWaitsForEarlierSDKPullAndCancels(t *testing.T) {
	w, s := streamBridgeFixture(t)
	s.dataSequence = 1 // Inside the ordinary four-frame window.
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan error, 1)
	go func() {
		defer func() {
			if recover() != nil {
				done <- errors.New("terminal wrote before earlier pull")
			}
		}()
		done <- s.Send(ctx, []byte("data: [DONE]\n\n"), true)
	}()
	select {
	case err := <-done:
		t.Fatal("terminal must wait for ordinary data credit", err)
	case <-time.After(30 * time.Millisecond):
	}
	cancel()
	select {
	case err := <-done:
		if !errors.Is(err, context.Canceled) {
			t.Fatal(err)
		}
	case <-time.After(time.Second):
		t.Fatal("terminal wait ignored cancellation")
	}
	if w.modelDataRecords != 0 {
		t.Fatal("terminal bytes admitted before previous pulls")
	}
}

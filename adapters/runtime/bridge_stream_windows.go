//go:build windows

package runtime

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"strings"
	"unicode/utf8"
)

const ModelStreamVersion = "MODEL_SSE_V1"
const ModelStreamMaxRaw = 2 * 1024 * 1024
const ModelStreamFragment = 8192
const ModelStreamWindow = 4
const modelStreamRecordLimit = 262144

type ModelStreamFrame struct {
	Version  string         `json:"version"`
	Type     string         `json:"type"`
	Binding  map[string]any `json:"binding"`
	Sequence int64          `json:"sequence"`
	Offset   int64          `json:"offset"`
	Digest   string         `json:"digest"`
	Payload  map[string]any `json:"payload"`
}

type ModelStreamObservation struct{ Frame ModelStreamFrame }
type modelStreamCheckpoint struct {
	offset int64
	digest string
}

type ModelStream struct {
	bridge                                                      *Bridge
	binding                                                     map[string]any
	raw                                                         []byte
	dataSequence, creditedData                                  int64
	dataChecks                                                  []modelStreamCheckpoint
	observationSequence, creditedObservation, observationOffset int64
	observationDigest                                           string
	observationHashes                                           []string
	pending                                                     map[int64]ModelStreamFrame
	terminal, closed, failed                                    bool
	terminalObservation                                         int64
}

func modelWireInteger(value any) (int64, bool) {
	n, ok := value.(json.Number)
	if !ok {
		return 0, false
	}
	i, e := n.Int64()
	return i, e == nil
}
func modelWireDigest(value string) bool {
	if len(value) != 71 || !strings.HasPrefix(value, "sha256:") {
		return false
	}
	b, e := hex.DecodeString(value[7:])
	return e == nil && len(b) == 32 && value == strings.ToLower(value)
}

func exactModelKeys(value map[string]any, keys ...string) bool {
	if len(value) != len(keys) {
		return false
	}
	for _, k := range keys {
		if _, ok := value[k]; !ok {
			return false
		}
	}
	return true
}

func modelStreamHash(value any) string {
	raw, _ := json.Marshal(value)
	h, _ := canonicalHash(raw)
	return h
}

func ModelStreamID(binding map[string]any) string {
	value := map[string]any{}
	for k, v := range binding {
		if k != "stream_id" {
			value[k] = v
		}
	}
	return modelStreamHash(value)
}

func (w *Bridge) modelNotifyLocked() {
	if w.modelChanged != nil {
		close(w.modelChanged)
	}
	w.modelChanged = make(chan struct{})
}

func (w *Bridge) ModelInitializationDelivered() bool {
	w.mu.Lock()
	defer w.mu.Unlock()
	return w.modelInitDelivered && w.journal.QueueRequired && !w.journal.Cancelled
}

func (w *Bridge) ModelObservations() <-chan ModelStreamObservation { return w.modelObservations }

func (w *Bridge) ModelStreamsClosed() bool {
	w.mu.Lock()
	defer w.mu.Unlock()
	for _, s := range w.modelStreams {
		if !s.closed || s.failed || s.creditedObservation != s.observationSequence {
			return false
		}
	}
	return true
}

func (w *Bridge) OpenModelStream(ctx context.Context, binding map[string]any) (*ModelStream, error) {
	raw, err := json.Marshal(binding)
	if err != nil {
		return nil, err
	}
	bound, err := bridgeMap(raw)
	if err != nil {
		return nil, err
	}
	if !exactModelKeys(bound, "project_id", "session_id", "task_id", "run_id", "runtime_epoch", "queue_generation", "dispatch_key", "manifest_hash", "process_identity", "effect_sequence", "effect_key", "request_hash", "stream_id") || ModelStreamID(bound) != bound["stream_id"] || bridgeNumber(bound, "effect_sequence") < 1 || bridgeString(bound, "effect_key") == "" || !modelWireDigest(bridgeString(bound, "request_hash")) {
		return nil, errors.New("invalid MODEL stream binding")
	}
	w.mu.Lock()
	if err = w.validateControlBinding(bound); err != nil {
		w.mu.Unlock()
		return nil, err
	}
	if !w.modelInitDelivered || !w.journal.QueueRequired || w.journal.Cancelled || w.journal.ProtocolComplete || len(w.modelStreams) >= 32 || bridgeNumber(bound, "effect_sequence") <= w.journal.QueueInitSequence {
		w.mu.Unlock()
		return nil, errors.New("MODEL stream initialization or lifetime gate")
	}
	for _, old := range w.modelStreams {
		if !old.closed || old.binding["stream_id"] == bound["stream_id"] {
			w.mu.Unlock()
			return nil, errors.New("MODEL stream already active or replayed")
		}
	}
	s := &ModelStream{bridge: w, binding: bound, pending: map[int64]ModelStreamFrame{}, observationDigest: Hash(nil)}
	w.modelStreams = append(w.modelStreams, s)
	w.modelNotifyLocked()
	w.mu.Unlock()
	frame := ModelStreamFrame{ModelStreamVersion, "stream.open", bound, 0, 0, Hash(nil), map[string]any{"status": 200, "content_type": "text/event-stream"}}
	if err = w.writeModelFrame(ctx, frame); err != nil {
		s.Fail(ctx)
		return nil, err
	}
	return s, nil
}

func (w *Bridge) writeModelFrame(ctx context.Context, frame ModelStreamFrame) error {
	raw, err := json.Marshal(frame)
	if err != nil {
		return err
	}
	if len(raw) > 64*1024 {
		return errors.New("MODEL auxiliary envelope bound")
	}
	w.writeMu.Lock()
	defer w.writeMu.Unlock()
	return w.process.Write(ctx, append(raw, '\n'))
}

func (s *ModelStream) Send(ctx context.Context, raw []byte, terminal bool) error {
	w := s.bridge
	for len(raw) > 0 {
		part := raw[:min(len(raw), ModelStreamFragment)]
		for {
			w.mu.Lock()
			if s.failed || s.closed || s.terminal || w.journal.Cancelled || len(s.raw)+len(part) > ModelStreamMaxRaw || w.modelDataRecords >= modelStreamRecordLimit {
				w.mu.Unlock()
				return errors.New("MODEL stream closed or bounded input exhausted")
			}
			if s.dataSequence-s.creditedData < ModelStreamWindow && (!terminal || s.creditedData == s.dataSequence) {
				break
			}
			changed := w.modelChanged
			w.mu.Unlock()
			select {
			case <-changed:
			case <-ctx.Done():
				return ctx.Err()
			case <-w.done:
				return errors.New("MODEL worker stopped")
			}
		}
		s.raw = append(s.raw, part...)
		s.dataSequence++
		w.modelDataRecords++
		checkpoint := modelStreamCheckpoint{int64(len(s.raw)), Hash(s.raw)}
		s.dataChecks = append(s.dataChecks, checkpoint)
		frame := ModelStreamFrame{ModelStreamVersion, "stream.data", s.binding, s.dataSequence, checkpoint.offset, checkpoint.digest, map[string]any{"data_base64": base64.StdEncoding.EncodeToString(part), "terminal": terminal}}
		w.mu.Unlock()
		if err := w.writeModelFrame(ctx, frame); err != nil {
			return err
		}
		raw = raw[len(part):]
	}
	return nil
}

// Terminal is invoked only after the original resource receipt committed. It
// never waits for SDK terminal events, which depend on the ordinary effect ACK.
func (s *ModelStream) Terminal(ctx context.Context, receiptID string) (map[string]any, error) {
	w := s.bridge
	for {
		w.mu.Lock()
		if s.failed || s.closed || w.journal.Cancelled || receiptID != Hash(s.raw) {
			w.mu.Unlock()
			return nil, errors.New("MODEL stream final receipt mismatch")
		}
		if s.creditedData == s.dataSequence {
			break
		}
		changed := w.modelChanged
		w.mu.Unlock()
		select {
		case <-changed:
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-w.done:
			return nil, errors.New("MODEL worker stopped")
		}
	}
	s.terminal = true
	s.terminalObservation = s.creditedObservation
	frame := ModelStreamFrame{ModelStreamVersion, "stream.terminal", s.binding, s.dataSequence, int64(len(s.raw)), receiptID, map[string]any{"receipt_id": receiptID, "observation_sequence": s.terminalObservation}}
	ack := map[string]any{"status": 200, "content_type": "text/event-stream", "body_encoding": ModelStreamVersion, "stream_id": s.binding["stream_id"], "body_sha256": receiptID, "receipt_id": receiptID, "raw_bytes": len(s.raw), "data_sequence": s.dataSequence, "observation_sequence": s.terminalObservation}
	w.mu.Unlock()
	if err := w.writeModelFrame(ctx, frame); err != nil {
		return nil, err
	}
	return ack, nil
}

func (s *ModelStream) Fail(ctx context.Context) {
	w := s.bridge
	w.mu.Lock()
	s.failed = true
	frame := ModelStreamFrame{ModelStreamVersion, "stream.fail", s.binding, s.dataSequence, int64(len(s.raw)), Hash(s.raw), map[string]any{"code": "MODEL_STREAM_ABORTED"}}
	w.modelNotifyLocked()
	w.mu.Unlock()
	_ = w.writeModelFrame(ctx, frame)
}

// Called under the bridge lock, before ordinary BridgeFrame sequence handling.
func (w *Bridge) consumeModelFrame(line []byte) error {
	var frame ModelStreamFrame
	d := json.NewDecoder(bytes.NewReader(line))
	d.UseNumber()
	d.DisallowUnknownFields()
	if d.Decode(&frame) != nil || d.Decode(new(any)) != io.EOF || frame.Version != ModelStreamVersion || frame.Binding == nil || frame.Payload == nil {
		return errors.New("invalid MODEL auxiliary frame")
	}
	keys, err := bridgeMap(line)
	if err != nil || !exactModelKeys(keys, "version", "type", "binding", "sequence", "offset", "digest", "payload") {
		return errors.New("MODEL auxiliary exact keys")
	}
	if !w.modelInitDelivered || w.journal.Cancelled || w.validateControlBinding(frame.Binding) != nil {
		return errors.New("MODEL auxiliary old initialization or generation")
	}
	var s *ModelStream
	for _, candidate := range w.modelStreams {
		if candidate.binding["stream_id"] == frame.Binding["stream_id"] {
			s = candidate
			break
		}
	}
	if s == nil || modelStreamHash(s.binding) != modelStreamHash(frame.Binding) || s.failed {
		return errors.New("foreign MODEL stream")
	}
	switch frame.Type {
	case "stream.transport_credit":
		if len(frame.Payload) != 0 || frame.Sequence < 1 || frame.Sequence > s.dataSequence {
			return errors.New("invalid MODEL transport credit")
		}
		check := s.dataChecks[frame.Sequence-1]
		if check.offset != frame.Offset || check.digest != frame.Digest || frame.Sequence > s.creditedData+1 {
			return errors.New("changed MODEL credit or gap")
		}
		if frame.Sequence == s.creditedData+1 {
			s.creditedData = frame.Sequence
			w.modelNotifyLocked()
		}
	case "stream.observe":
		if !exactModelKeys(frame.Payload, "event", "message_ordinal", "text_part", "sdk_content_index", "text") || frame.Sequence < 1 || frame.Sequence > s.observationSequence+1 || frame.Offset < 0 || frame.Offset > ModelStreamMaxRaw {
			return errors.New("invalid MODEL observation fields or sequence")
		}
		typeName := bridgeString(frame.Payload, "event")
		text := bridgeString(frame.Payload, "text")
		if _, ok := frame.Payload["text"].(string); !ok || !utf8.ValidString(text) || len(text) > ModelStreamFragment || utf8.RuneCountInString(text) > 16384 {
			return errors.New("MODEL observation text bound")
		}
		ordinal, validOrdinal := modelWireInteger(frame.Payload["message_ordinal"])
		part, validPart := modelWireInteger(frame.Payload["text_part"])
		index, validIndex := modelWireInteger(frame.Payload["sdk_content_index"])
		if !validOrdinal || !validPart || !validIndex || ordinal < 1 || ordinal > 32 || part < 0 || part >= 64 || index < 0 || index >= 4096 {
			return errors.New("MODEL observation identity bound")
		}
		if typeName != "text_delta" && text != "" || typeName == "text_delta" && text == "" {
			return errors.New("MODEL observation phase content")
		}
		if typeName != "text_start" && typeName != "text_delta" && typeName != "text_end" && typeName != "message_end" {
			return errors.New("MODEL observation phase")
		}
		fingerprint := modelStreamHash(frame)
		if frame.Sequence <= s.observationSequence {
			if s.observationHashes[frame.Sequence-1] != fingerprint {
				return errors.New("changed duplicate MODEL observation")
			}
		} else {
			if s.closed || w.modelObservationRecords >= modelStreamRecordLimit || len(s.pending) >= ModelStreamWindow || frame.Offset != s.observationOffset+int64(len(text)) || frame.Digest != modelStreamHash(map[string]any{"previous": s.observationDigest, "payload": frame.Payload}) || typeName == "message_end" && !s.terminal {
				return errors.New("MODEL observation digest, bound or terminal gate")
			}
			s.observationSequence = frame.Sequence
			s.observationOffset = frame.Offset
			s.observationDigest = frame.Digest
			s.observationHashes = append(s.observationHashes, fingerprint)
			w.modelObservationRecords++
		}
		// One pending callback owns the durable commit/credit. An exact retry
		// before that callback finishes must not enqueue a second commit. A
		// retry after credit is replayed through the canonical stored receipt.
		if _, exists := s.pending[frame.Sequence]; exists {
			return nil
		}
		s.pending[frame.Sequence] = frame
		select {
		case w.modelObservations <- ModelStreamObservation{frame}:
		default:
			return errors.New("MODEL observation queue bound")
		}
	default:
		return errors.New("wrong MODEL auxiliary direction")
	}
	return nil
}

func (w *Bridge) CreditModelObservation(ctx context.Context, observation ModelStreamObservation, eventIDs []string, watermark int64) error {
	f := observation.Frame
	w.mu.Lock()
	var s *ModelStream
	for _, candidate := range w.modelStreams {
		if candidate.binding["stream_id"] == f.Binding["stream_id"] {
			s = candidate
			break
		}
	}
	if s == nil || s.failed || modelStreamHash(s.pending[f.Sequence]) != modelStreamHash(f) || f.Sequence > s.creditedObservation+1 {
		w.mu.Unlock()
		return errors.New("MODEL durable credit identity or order")
	}
	delete(s.pending, f.Sequence)
	if f.Sequence > s.creditedObservation {
		s.creditedObservation = f.Sequence
	}
	if f.Payload["event"] == "message_end" {
		s.closed = true
	}
	w.modelNotifyLocked()
	w.mu.Unlock()
	if eventIDs == nil {
		eventIDs = []string{}
	}
	f.Type = "stream.observation_credit"
	f.Payload = map[string]any{"journal_event_ids": eventIDs, "session_watermark": watermark}
	return w.writeModelFrame(ctx, f)
}

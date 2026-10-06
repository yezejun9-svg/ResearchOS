package domain

// Typed session events for researchos-client/2 (W03-02) and validation of the
// transient native bridge messages (never journaled; rejection as CommandEnvelope
// is covered by DecodeEnvelope's method registry).
//
// The field set is exactly the published SessionEvent schema: ten required keys,
// no extras, with run_id/command_id/domain_event_id required-but-nullable.

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

var eventKinds = map[string]bool{
	"MESSAGE": true, "TOOL_STARTED": true, "TOOL_RESULT": true, "JUDGE_DECISION": true,
	"RUN_STATE": true, "GOAL_STATE": true, "ARTIFACT": true, "USAGE": true, "CHECKPOINT": true,
	"CLIENT_HANDOFF": true, "BOOTSTRAP_STATE": true, "PERMISSION_REQUIRED": true,
	"PERMISSION_RESOLVED": true, "ERROR": true,
}

// eventFields is the schema's SessionEvent property set (additionalProperties:false).
var eventFields = map[string]bool{
	"event_id": true, "session_id": true, "sequence": true, "core_build_id": true,
	"protocol_version": true, "run_id": true, "command_id": true, "domain_event_id": true,
	"kind": true, "payload": true,
}

type SessionEvent struct {
	EventID         *string         `json:"event_id"`
	SessionID       *string         `json:"session_id"`
	Sequence        *int64          `json:"sequence"`
	CoreBuildID     *string         `json:"core_build_id"`
	ProtocolVersion *string         `json:"protocol_version"`
	RunID           *string         `json:"run_id"`
	CommandID       *string         `json:"command_id"`
	DomainEventID   *string         `json:"domain_event_id"`
	Kind            *string         `json:"kind"`
	Payload         json.RawMessage `json:"payload"`
}

var (
	ErrEventSequence  = errors.New("EVENT_SEQUENCE_OUT_OF_ORDER")
	ErrResyncRequired = errors.New("SNAPSHOT_RESYNC_REQUIRED")
	ErrSensitiveField = errors.New("SENSITIVE_FIELD_IN_EVENT_PAYLOAD")
)

// DecodeEvent rejects bare shapes, unknown kinds, missing required keys, and any
// field the published schema does not declare. Per-kind payload typing is done by
// ValidateEventPayload against the schema document so the two cannot drift.
func DecodeEvent(raw []byte) (*SessionEvent, error) {
	var probe map[string]json.RawMessage
	dec := json.NewDecoder(strings.NewReader(string(raw)))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&probe); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrBareObject, err)
	}
	for k := range probe {
		if !eventFields[k] {
			return nil, fmt.Errorf("UNKNOWN_FIELD:%s", k)
		}
	}
	for _, req := range []string{"event_id", "session_id", "sequence", "core_build_id",
		"protocol_version", "run_id", "command_id", "domain_event_id", "kind", "payload"} {
		if _, has := probe[req]; !has {
			return nil, fmt.Errorf("MISSING_FIELD:%s", req)
		}
	}
	var ev SessionEvent
	if err := json.Unmarshal(raw, &ev); err != nil {
		return nil, err
	}
	if ev.ProtocolVersion == nil || *ev.ProtocolVersion != ProtocolV2 {
		return nil, ErrProtocolVersion
	}
	for name, v := range map[string]*string{"event_id": ev.EventID, "session_id": ev.SessionID, "core_build_id": ev.CoreBuildID, "kind": ev.Kind} {
		if err := requiredString(name, v); err != nil {
			return nil, err
		}
	}
	for name, v := range map[string]*string{"run_id": ev.RunID, "command_id": ev.CommandID, "domain_event_id": ev.DomainEventID} {
		if v != nil && *v == "" {
			return nil, fmt.Errorf("EMPTY_STRING:%s", name)
		}
	}
	if ev.Sequence == nil || *ev.Sequence < 0 {
		return nil, fmt.Errorf("BAD_SEQUENCE")
	}
	if !eventKinds[*ev.Kind] {
		return nil, fmt.Errorf("UNKNOWN_EVENT_KIND:%s", *ev.Kind)
	}
	if len(ev.Payload) == 0 || !json.Valid(ev.Payload) {
		return nil, fmt.Errorf("BAD_EVENT_PAYLOAD")
	}
	return &ev, nil
}

// ValidateEventPayload checks the payload against the schema def published for the
// event kind, in read direction: writeOnly-annotated fields (credential material)
// can never appear in a durable event, and the value-shape rules (stream phase,
// cost_known/money coupling, cancel settlement) come from the schema itself.
// The only extra rule here is the sensitive-key red list, which no JSON Schema
// keyword in the pinned document expresses.
func ValidateEventPayload(doc *SchemaDoc, ev *SessionEvent) error {
	var p any
	if err := json.Unmarshal(ev.Payload, &p); err != nil {
		return fmt.Errorf("PAYLOAD_NOT_OBJECT:%v", err)
	}
	obj, ok := p.(map[string]any)
	if !ok || obj == nil {
		return fmt.Errorf("PAYLOAD_NOT_OBJECT")
	}
	if k, bad := firstSensitiveKey(obj); bad {
		return fmt.Errorf("%w:%s", ErrSensitiveField, k)
	}
	if doc != nil {
		def, err := doc.EventPayloadDef(*ev.Kind)
		if err != nil {
			return err
		}
		if err := doc.ValidateDef(def, p); err != nil {
			return fmt.Errorf("EVENT_PAYLOAD_SCHEMA:%v", err)
		}
	}
	return nil
}

// sensitiveKeyPatterns are matched case-insensitively against every payload key that
// actually carries a value; credentials belong to the native transient import path.
var sensitiveKeyPatterns = []string{"credential_value", "api_key", "apikey", "secret", "token_value", "password", "authorization"}

func firstSensitiveKey(node any) (string, bool) {
	switch tv := node.(type) {
	case map[string]any:
		for _, k := range sortedKeys(tv) {
			for _, pat := range sensitiveKeyPatterns {
				if strings.EqualFold(k, pat) || strings.Contains(strings.ToLower(k), pat) {
					return k, true
				}
			}
			if k, bad := firstSensitiveKey(tv[k]); bad {
				return k, bad
			}
		}
	case []any:
		for _, x := range tv {
			if k, bad := firstSensitiveKey(x); bad {
				return k, bad
			}
		}
	}
	return "", false
}

// ValidateNativeTransient grades the four transient OS-bridge message shapes against the
// published defs. They are never durable commands and never written to journals or events:
// a request direction may carry credential material, a result direction may not.
func ValidateNativeTransient(doc *SchemaDoc, def string, raw []byte, writeDirection bool) error {
	if !strings.HasPrefix(def, "Native") {
		return fmt.Errorf("UNKNOWN_NATIVE_DEFINITION:%s", def)
	}
	if doc == nil {
		return fmt.Errorf("SCHEMA_REQUIRED")
	}
	var v any
	if err := json.Unmarshal(raw, &v); err != nil {
		return err
	}
	if writeDirection {
		return doc.ValidateDefInput(def, v)
	}
	return doc.ValidateDef(def, v)
}

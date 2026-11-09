package domain

// Typed researchos-client/2 protocol core (W03-02).
// One local service shared by CLI and Desktop: envelope handshake, per-method
// typed payloads and results, command_id content-hash idempotency, writer/session/
// revision CAS checks, and typed session events. Schema-shaped rejection of bare
// objects, cross-method results, old protocol downgrade and untyped payloads lives
// here, not in callers.

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"sort"
	"strings"
	"time"

	"researchos.local/research-os/internal/canonical"
)

const ProtocolV2 = "researchos-client/2"

var ErrProtocolVersion = errors.New("UNSUPPORTED_PROTOCOL")
var ErrBareObject = errors.New("UNtyped_ENVELOPE")
var ErrUnknownMethod = errors.New("UNKNOWN_METHOD")
var ErrCrossMethod = errors.New("CROSS_METHOD_RESULT")
var ErrIdemConflict = errors.New("IDEMPOTENCY_CONFLICT")
var ErrSessionNotFound = errors.New("UNKNOWN_SESSION")

var methodsV2 = map[string]bool{
	"host.status": true, "host.configure": true, "project.bootstrap": true,
	"session.list": true, "session.create": true, "session.get": true, "session.attach": true,
	"session.send": true, "session.control": true, "session.events": true, "session.handoff": true,
	"goal.start": true, "provider.models": true, "provider.probe": true,
	"workspace.register": true, "workspace.list": true, "workspace.tree": true, "workspace.read": true,
	"workspace.diff": true, "workspace.write": true, "artifact.import": true, "session.update": true,
	"permission.respond": true,
}

// durable command methods may never carry native-only or secret-bearing payloads
// write-class methods require full identity/CAS fields in the envelope
var writeMethods = map[string]bool{
	"session.create": true, "host.configure": true,
	"session.send": true, "session.control": true, "session.update": true, "session.handoff": true,
	"workspace.write": true, "artifact.import": true, "permission.respond": true, "goal.start": true,
	"project.bootstrap": true,
}

type Envelope struct {
	ProtocolVersion  *string         `json:"protocol_version"`
	CommandID        *string         `json:"command_id"`
	ClientID         *string         `json:"client_id"`
	ProjectID        *string         `json:"project_id"`
	SessionID        *string         `json:"session_id"`
	ExpectedRevision *int64          `json:"expected_revision"`
	WriterEpoch      *int64          `json:"writer_epoch"`
	Method           *string         `json:"method"`
	Payload          json.RawMessage `json:"payload"`
	extra            map[string]json.RawMessage
	originalRaw      []byte
}

func requiredString(name string, v *string) error {
	if v == nil || *v == "" {
		return fmt.Errorf("MISSING_FIELD:%s", name)
	}
	return nil
}

// DecodeEnvelope enforces protocol_version first; a bare object (no protocol_version)
// can never be mistaken for a valid command and there is no /1 downgrade path.
func DecodeEnvelope(raw []byte) (*Envelope, error) {
	if len(raw) == 0 || len(raw) > clientIdentityMaxRequest {
		return nil, fmt.Errorf("ENVELOPE_SIZE")
	}
	if _, err := canonical.JSON(raw); err != nil {
		return nil, fmt.Errorf("ENVELOPE_JSON: %w", err)
	}
	var probe map[string]json.RawMessage
	dec := json.NewDecoder(strings.NewReader(string(raw)))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&probe); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrBareObject, err)
	}
	if _, ok := probe["protocol_version"]; !ok {
		return nil, ErrBareObject
	}
	for k := range probe {
		switch k {
		case "protocol_version", "command_id", "client_id", "project_id", "session_id", "expected_revision", "writer_epoch", "method", "payload":
		default:
			return nil, fmt.Errorf("UNKNOWN_FIELD:%s", k)
		}
	}
	var e Envelope
	if err := json.Unmarshal(raw, &e); err != nil {
		return nil, err
	}
	e.extra = probe
	e.originalRaw = append([]byte(nil), raw...)
	for _, key := range []string{"project_id", "session_id", "expected_revision", "writer_epoch"} {
		if _, ok := probe[key]; !ok {
			return nil, fmt.Errorf("MISSING_FIELD:%s", key)
		}
	}
	if err := requiredString("protocol_version", e.ProtocolVersion); err != nil {
		return nil, err
	}
	if *e.ProtocolVersion != ProtocolV2 {
		return nil, ErrProtocolVersion
	}
	if err := requiredString("command_id", e.CommandID); err != nil {
		return nil, err
	}
	if err := requiredString("client_id", e.ClientID); err != nil {
		return nil, err
	}
	if err := requiredString("method", e.Method); err != nil {
		return nil, err
	}
	if !methodsV2[*e.Method] {
		return nil, ErrUnknownMethod
	}
	// project_id/session_id are required keys but legal nulls (host-level commands carry
	// neither); an empty string is never a valid reference.
	if e.SessionID != nil && *e.SessionID == "" {
		return nil, fmt.Errorf("MISSING_FIELD:session_id")
	}
	if e.ProjectID != nil && *e.ProjectID == "" {
		return nil, fmt.Errorf("MISSING_FIELD:project_id")
	}
	if e.Payload == nil {
		return nil, fmt.Errorf("MISSING_FIELD:payload")
	}
	// takeover (session.attach with request_write_owner) must not claim a writer epoch;
	// read attach must carry the observed epoch.
	if *e.Method == "session.attach" {
		var ap struct {
			RequestWriteOwner *bool `json:"request_write_owner"`
		}
		json.Unmarshal(e.Payload, &ap)
		claim := ap.RequestWriteOwner != nil && *ap.RequestWriteOwner
		if claim && e.WriterEpoch != nil {
			return nil, fmt.Errorf("ATTACKER_CLAIMED_EPOCH")
		}
		if !claim && e.WriterEpoch == nil {
			return nil, fmt.Errorf("MISSING_FIELD:writer_epoch")
		}
	}
	if writeMethods[*e.Method] && *e.Method != "host.configure" && *e.Method != "session.attach" && *e.Method != "session.create" && *e.Method != "project.bootstrap" && *e.Method != "workspace.register" {
		if err := requiredString("project_id", e.ProjectID); err != nil {
			return nil, err
		}
		// A project-level Goal creates its own real session. Only a Goal naming an
		// existing session may claim that session's revision and writer epoch.
		if *e.Method == "goal.start" && e.SessionID == nil {
			if e.ExpectedRevision != nil || e.WriterEpoch != nil {
				return nil, fmt.Errorf("INVALID_REQUEST:project goal must not claim a session writer")
			}
		} else {
			if e.ExpectedRevision == nil {
				return nil, fmt.Errorf("MISSING_FIELD:expected_revision")
			}
			if e.WriterEpoch == nil {
				return nil, fmt.Errorf("MISSING_FIELD:writer_epoch")
			}
		}
	}
	if *e.Method == "host.configure" {
		if err := validateClientConfigurationScope(&e); err != nil {
			return nil, err
		}
	}

	if err := e.validatePayload(); err != nil {
		return nil, err
	}
	return &e, nil
}

func decodePayloadObject(e *Envelope) (map[string]json.RawMessage, error) {
	var m map[string]json.RawMessage
	if err := json.Unmarshal(e.Payload, &m); err != nil {
		return nil, fmt.Errorf("PAYLOAD_NOT_OBJECT:%v", err)
	}
	return m, nil
}

func hasKey(m map[string]json.RawMessage, k string) bool {
	_, ok := m[k]
	return ok
}

func hasKeyRaw(m map[string]json.RawMessage, k string) bool {
	_, ok := m[k]
	return ok
}

func isTrue(m map[string]json.RawMessage, k string) bool {
	raw, ok := m[k]
	if !ok {
		return false
	}
	var b bool
	return json.Unmarshal(raw, &b) == nil && b
}

func isSHA256(s string, allowNull bool, raw json.RawMessage) bool {
	if allowNull && string(raw) == "null" {
		return true
	}
	return strings.HasPrefix(s, "sha256:") && len(s) == 71 && regexpHex(s[7:])
}

func regexpHex(s string) bool {
	for _, r := range s {
		if !((r >= '0' && r <= '9') || (r >= 'a' && r <= 'f')) {
			return false
		}
	}
	return len(s) == 64
}

func (e *Envelope) validatePayload() error {
	m, err := decodePayloadObject(e)
	if err != nil {
		return err
	}

	switch *e.Method {
	case "workspace.write":
		var p struct {
			WorkspaceRef        *string `json:"workspace_ref"`
			RelativePath        *string `json:"relative_path"`
			TaskID              *string `json:"task_id"`
			ExpectedContentHash *string `json:"expected_content_hash"`
			Text                *string `json:"text"`
			CreateIfMissing     bool    `json:"create_if_missing"`
		}
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return err
		}
		if err := requiredString("workspace_ref", p.WorkspaceRef); err != nil {
			return err
		}
		if err := requiredString("relative_path", p.RelativePath); err != nil {
			return err
		}
		// EDIT-REQUIRES-EXISTING-TASK: a save must bind a real task
		if err := requiredString("task_id", p.TaskID); err != nil {
			return err
		}
		if p.Text == nil {
			return fmt.Errorf("MISSING_FIELD:text")
		}
		lp := strings.ToLower(*p.RelativePath)
		if strings.HasPrefix(*p.RelativePath, "/") || strings.Contains(lp, ":") {
			return fmt.Errorf("ABSOLUTE_PATH")
		}
		for _, seg := range strings.Split(*p.RelativePath, "/") {
			if seg == ".." {
				return fmt.Errorf("PATH_ESCAPE")
			}
		}
		rawHash := m["expected_content_hash"]
		if p.CreateIfMissing {
			if string(rawHash) != "null" && hasKey(m, "expected_content_hash") && p.ExpectedContentHash != nil {
				return fmt.Errorf("CREATE_WITH_EXISTING_HASH")
			}
		} else {
			if p.ExpectedContentHash == nil {
				return fmt.Errorf("OVERWRITE_NULL_HASH")
			}
			if !isSHA256("", true, rawHash) && !isSHA256(*p.ExpectedContentHash, false, rawHash) {
				return fmt.Errorf("BAD_CONTENT_HASH")
			}
		}
	case "provider.probe":
		var p struct {
			ModelConfigRef  *string `json:"model_config_ref"`
			AllowNetwork    *bool   `json:"allow_network"`
			MaxOutputTokens *int64  `json:"max_output_tokens"`
			TimeoutMs       *int64  `json:"timeout_ms"`
		}
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return err
		}
		if err := requiredString("model_config_ref", p.ModelConfigRef); err != nil {
			return err
		}
		if p.AllowNetwork == nil || !*p.AllowNetwork {
			return fmt.Errorf("PROBE_WITHOUT_NETWORK_CONSENT")
		}
		if p.MaxOutputTokens == nil || *p.MaxOutputTokens < 1 || *p.MaxOutputTokens > 32 {
			return fmt.Errorf("UNBOUNDED_PROBE")
		}
		if p.TimeoutMs == nil || *p.TimeoutMs < 1000 || *p.TimeoutMs > 30000 {
			return fmt.Errorf("UNBOUNDED_PROBE")
		}
		// exactly one authorized request and it must land in the project ledger
		if e.ProjectID == nil || *e.ProjectID == "" {
			return fmt.Errorf("PROBE_WITHOUT_PROJECT_LEDGER")
		}
	case "provider.models":
		if isTrue(m, "refresh") && !isTrue(m, "allow_network") {
			return fmt.Errorf("CATALOG_REFRESH_WITHOUT_CONSENT")
		}
	case "permission.respond":
		for _, k := range []string{"resource_request_id", "action_digest"} {
			if !hasKey(m, k) {
				return fmt.Errorf("MISSING_FIELD:%s", k)
			}
		}
		var p struct {
			ResourceRequestID       *string `json:"resource_request_id"`
			ResourceRequestRevision *int64  `json:"resource_request_revision"`
			ActionDigest            *string `json:"action_digest"`
			Decision                *string `json:"decision"`
		}
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return err
		}
		if p.ResourceRequestRevision == nil {
			return fmt.Errorf("MISSING_FIELD:resource_request_revision")
		}
		if p.ActionDigest == nil || !isSHA256(*p.ActionDigest, false, m["action_digest"]) {
			return fmt.Errorf("MISSING_FROZEN_SCOPE_DIGEST")
		}
		if p.Decision == nil || !map[string]bool{"ALLOW_ONCE": true, "DENY": true}[func() string {
			if p.Decision != nil {
				return *p.Decision
			}
			return ""
		}()] {
			return fmt.Errorf("UNKNOWN_DECISION")
		}

	case "session.send":
		if !hasKey(m, "text") {
			return fmt.Errorf("MISSING_FIELD:text")
		}
	case "session.control":
		var p struct {
			Action   *string `json:"action"`
			TargetID *string `json:"target_id"`
		}
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return err
		}
		if p.Action == nil || p.TargetID == nil {
			return fmt.Errorf("MISSING_FIELD:action/target_id")
		}
	case "session.attach":
		if !hasKey(m, "after_sequence") {
			return fmt.Errorf("MISSING_FIELD:after_sequence")
		}
	}
	return nil
}

// ContentHash is the canonical (RFC8785-flavoured: sorted keys, no extra space)
// digest of the envelope; idempotency binds command_id to this hash.
func (e *Envelope) ContentHash() (string, error) {
	var generic map[string]any
	if err := json.Unmarshal([]byte(mustMarshal(e.extra)), &generic); err != nil {
		return "", err
	}
	return "sha256:" + canonicalHash(generic), nil
}

func mustMarshal(m map[string]json.RawMessage) string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var sb strings.Builder
	sb.WriteByte('{')
	for i, k := range keys {
		if i > 0 {
			sb.WriteByte(',')
		}
		kb, _ := json.Marshal(k)
		sb.Write(kb)
		sb.WriteByte(':')
		sb.Write(compactJSON(m[k]))
	}
	sb.WriteByte('}')
	return sb.String()
}

func compactJSON(raw json.RawMessage) json.RawMessage {
	var v any
	if json.Unmarshal(raw, &v) != nil {
		return raw
	}
	b, err := json.Marshal(v)
	if err != nil {
		return raw
	}
	return b
}

func canonicalHash(v any) string {
	b := canonicalBytes(v)
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

func canonicalBytes(v any) []byte {
	switch t := v.(type) {
	case map[string]any:
		keys := make([]string, 0, len(t))
		for k := range t {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		var sb strings.Builder
		sb.WriteByte('{')
		for i, k := range keys {
			if i > 0 {
				sb.WriteByte(',')
			}
			kb, _ := json.Marshal(k)
			sb.Write(kb)
			sb.WriteByte(':')
			sb.Write(canonicalBytes(t[k]))
		}
		sb.WriteByte('}')
		return []byte(sb.String())
	case []any:
		var sb strings.Builder
		sb.WriteByte('[')
		for i, x := range t {
			if i > 0 {
				sb.WriteByte(',')
			}
			sb.Write(canonicalBytes(x))
		}
		sb.WriteByte(']')
		return []byte(sb.String())
	default:
		b, _ := json.Marshal(t)
		return b
	}
}

// ProtocolError is the published error object: every rejection carries the machine code,
// a human message, whether retrying the same command can help, the recovery action, and
// the current revision/epoch the client must refresh against.
type ProtocolError struct {
	Code               string `json:"code"`
	Message            string `json:"message"`
	Retryable          bool   `json:"retryable"`
	Recovery           string `json:"recovery"`
	CurrentRevision    any    `json:"current_revision"`
	CurrentWriterEpoch any    `json:"current_writer_epoch"`
	ResourceRequestID  any    `json:"resource_request_id"`
	RetryAfterMs       any    `json:"retry_after_ms"`
	CorrelationID      string `json:"correlation_id"`
}

// Response is the typed CommandResponse; result must match the request method,
// completion of a cancel requires settlement, and REJECTED carries a matching error_code.
type Response struct {
	ProtocolVersion *string        `json:"protocol_version"`
	CommandID       *string        `json:"command_id"`
	Method          *string        `json:"method"`
	Status          *string        `json:"status"`
	SessionID       *string        `json:"session_id"`
	Revision        *int64         `json:"revision"`
	ErrorCode       *string        `json:"error_code"`
	Error           *ProtocolError `json:"error"`
	Result          map[string]any `json:"result"`
}

func DecodeResponse(raw []byte) (*Response, error) {
	var probe map[string]json.RawMessage
	dec := json.NewDecoder(strings.NewReader(string(raw)))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&probe); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrBareObject, err)
	}
	for k := range probe {
		switch k {
		case "protocol_version", "command_id", "method", "status", "session_id", "revision", "error_code", "error", "result":
		default:
			return nil, fmt.Errorf("UNKNOWN_FIELD:%s", k)
		}
	}
	var r Response
	if err := json.Unmarshal(raw, &r); err != nil {
		return nil, err
	}
	if r.ProtocolVersion == nil || *r.ProtocolVersion != ProtocolV2 {
		return nil, ErrProtocolVersion
	}
	if err := requiredString("command_id", r.CommandID); err != nil {
		return nil, err
	}
	if err := requiredString("method", r.Method); err != nil {
		return nil, err
	}
	if !methodsV2[*r.Method] {
		return nil, ErrUnknownMethod
	}
	if r.Status == nil {
		return nil, fmt.Errorf("MISSING_FIELD:status")
	}
	switch *r.Status {
	case "COMPLETED", "ACKNOWLEDGED", "REJECTED", "NOT_IMPLEMENTED", "IN_PROGRESS":
	default:
		return nil, fmt.Errorf("UNKNOWN_STATUS:%s", *r.Status)
	}
	if r.Revision == nil {
		return nil, fmt.Errorf("MISSING_FIELD:revision")
	}
	if *r.Status == "REJECTED" {
		if r.ErrorCode == nil || *r.ErrorCode == "" {
			return nil, fmt.Errorf("REJECT_WITHOUT_ERROR_CODE")
		}
		if !protocolErrorCodes[*r.ErrorCode] {
			return nil, fmt.Errorf("UNKNOWN_ERROR_CODE:%s", *r.ErrorCode)
		}
		if r.Error == nil || r.Error.Code != *r.ErrorCode {
			return nil, fmt.Errorf("REJECT_WITHOUT_MATCHING_ERROR_OBJECT")
		}
		if hasResultPayload(r.Result) {
			return nil, fmt.Errorf("REJECT_WITH_SIDE_EFFECT_PAYLOAD")
		}
	} else {
		// rule 0 of the published CommandResponse: only REJECTED may carry error fields.
		if r.ErrorCode != nil || r.Error != nil {
			return nil, fmt.Errorf("NON_REJECT_WITH_ERROR_FIELDS")
		}
	}
	if *r.Status == "COMPLETED" {
		if r.Result == nil {
			return nil, fmt.Errorf("UNtyped_RESULT") // bare-object success forbidden
		}
		if *r.Method == "session.control" {
			var p struct {
				Action          *string `json:"action"`
				Settled         *bool   `json:"settled"`
				ChildrenStopped *bool   `json:"children_stopped"`
				QueueEmpty      *bool   `json:"queue_empty"`
			}
			b, _ := json.Marshal(r.Result)
			json.Unmarshal(b, &p)
			if p.Action != nil && *p.Action == "CANCEL" {
				if p.Settled == nil || !*p.Settled || p.ChildrenStopped == nil || !*p.ChildrenStopped || p.QueueEmpty == nil || !*p.QueueEmpty {
					return nil, fmt.Errorf("CANCEL_COMPLETED_UNSETTLED")
				}
			}
		}
	}
	if *r.Status == "ACKNOWLEDGED" {
		// An acknowledgement is only a reservation: it may not claim a completed effect.
		if _, has := r.Result["settled"]; has {
			return nil, fmt.Errorf("ACKNOWLEDGED_CLAIMS_SETTLEMENT")
		}
	}
	return &r, nil
}

var protocolErrorCodes = map[string]bool{
	"INVALID_REQUEST": true, "UNSUPPORTED_PROTOCOL": true, "UNSUPPORTED_METHOD": true,
	"UNAUTHENTICATED": true, "FORBIDDEN": true, "POLICY_DENIED": true, "NOT_FOUND": true,
	"NOT_IMPLEMENTED": true, "HOST_UNAVAILABLE": true, "STALE_REVISION": true,
	"STALE_WRITER_EPOCH": true, "WRITER_BUSY": true, "LEASE_EXPIRED": true, "SESSION_BUSY": true,
	"SESSION_ARCHIVED": true, "COMMAND_ID_CONFLICT": true, "COMMAND_PENDING": true,
	"CURSOR_EXPIRED": true, "CURSOR_INVALID": true, "PATH_OUT_OF_SCOPE": true,
	"WORKSPACE_REVOKED": true, "SELECTION_EXPIRED": true, "SELECTION_ALREADY_USED": true,
	"CONTENT_CONFLICT": true, "CONTENT_TOO_LARGE": true, "UNSUPPORTED_CONTENT": true,
	"NOT_A_REPOSITORY": true, "EXTERNAL_WRITE_RACE": true, "ARTIFACT_IMMUTABLE": true,
	"CREDENTIAL_MISSING": true, "CREDENTIAL_REVOKED": true, "CONFIG_CONFLICT": true,
	"MODEL_UNAVAILABLE": true, "PROVIDER_AUTH_FAILED": true, "PROVIDER_RATE_LIMITED": true,
	"PROVIDER_TIMEOUT": true, "NETWORK_UNAVAILABLE": true, "RESOURCE_BLOCKED": true,
	"CANCEL_UNCONFIRMED": true, "ALREADY_TERMINAL": true, "INTERNAL_ERROR": true,
	"VERSION_CONFLICT": true,
}

func hasResultPayload(res map[string]any) bool {
	if len(res) == 0 {
		return false
	}
	for k := range res {
		switch k {
		case "echo", "request", "note", "state", "snapshot":
			continue
		}
		return true
	}
	return false
}

// ValidateResultAgainstMethod rejects cross-method result payloads and, when a schema
// document is supplied, requires a COMPLETED result to satisfy the published result def
// for the request method — the same mapping the fixtures are graded against.
func ValidateResultAgainstMethod(reqMethod string, res *Response, doc *SchemaDoc) error {
	if res.Method == nil || *res.Method != reqMethod {
		return ErrCrossMethod
	}
	if doc == nil || res.Status == nil || *res.Status != "COMPLETED" || res.Result == nil {
		return nil
	}
	def, err := doc.MethodResultDef(reqMethod)
	if err != nil {
		return err
	}
	raw, err := json.Marshal(res.Result)
	if err != nil {
		return err
	}
	var generic any
	if err := json.Unmarshal(raw, &generic); err != nil {
		return err
	}
	if err := doc.ValidateDef(def, generic); err != nil {
		return fmt.Errorf("%w: %s -> %s: %v", ErrResponseSchema, reqMethod, def, err)
	}
	return nil
}

// ClientHostInfo is what the typed service reports about itself; the api layer fills it from the
// running host and the authenticated OS principal, so host.status never invents identity.
type ClientHostInfo struct {
	InstanceID     string
	CoreBuildID    string
	OperatingMode  string
	ConfigRevision int64
	// LeaseTTL is the host's writer-lease duration, taken from real host configuration;
	// a handoff is refused when it is not set.
	LeaseTTL       time.Duration
	ModelConfigs   []any
	CredentialSumm []any
	WorkspaceBind  []any
}

// ClientService is the single typed command service shared by the CLI and the Desktop (W03-02).
type ClientService struct {
	Doc                    *SchemaDoc
	Host                   ClientHostInfo
	Domain                 *Service
	SessionRuntime         ClientSessionRuntime
	WorkspaceAuthority     WorkspaceAuthority
	WorkspaceFiles         ClientWorkspaceFiles
	InventoryScanner       LocalInventoryScanner
	ConfigurationAuthority ClientConfigurationAuthority
	NativeCreateAuthority  NativeCreateAuthority
}

var (
	ErrResponseSchema = errors.New("RESPONSE_VIOLATES_PUBLISHED_SCHEMA")
)

// recoveryByCode maps each published error code to the action the client must take;
// nothing here claims a retry is safe unless the same command could change outcome.
var recoveryByCode = map[string]string{
	"INVALID_REQUEST": "FIX_INPUT", "UNSUPPORTED_PROTOCOL": "RECONFIGURE", "UNSUPPORTED_METHOD": "RECONFIGURE",
	"UNAUTHENTICATED": "REAUTHENTICATE_OS_USER", "FORBIDDEN": "REAUTHENTICATE_OS_USER",
	"POLICY_DENIED": "REAUTHENTICATE_OS_USER", "NOT_FOUND": "REFRESH_SNAPSHOT",
	"NOT_IMPLEMENTED": "REFRESH_SNAPSHOT", "HOST_UNAVAILABLE": "WAIT_FOR_SETTLEMENT",
	"STALE_REVISION": "REFRESH_SNAPSHOT", "STALE_WRITER_EPOCH": "ACQUIRE_WRITER",
	"WRITER_BUSY": "ACQUIRE_WRITER", "LEASE_EXPIRED": "ACQUIRE_WRITER", "SESSION_BUSY": "WAIT_FOR_SETTLEMENT",
	"SESSION_ARCHIVED": "REFRESH_SNAPSHOT", "COMMAND_ID_CONFLICT": "FIX_INPUT",
	"COMMAND_PENDING": "WAIT_FOR_SETTLEMENT", "CURSOR_EXPIRED": "REFRESH_SNAPSHOT",
	"CURSOR_INVALID": "REFRESH_SNAPSHOT", "PATH_OUT_OF_SCOPE": "FIX_INPUT",
	"WORKSPACE_REVOKED": "REAUTHENTICATE_OS_USER", "SELECTION_EXPIRED": "REFRESH_SNAPSHOT",
	"SELECTION_ALREADY_USED": "FIX_INPUT", "CONTENT_CONFLICT": "REFRESH_SNAPSHOT",
	"CONTENT_TOO_LARGE": "FIX_INPUT", "UNSUPPORTED_CONTENT": "FIX_INPUT",
	"NOT_A_REPOSITORY": "FIX_INPUT", "EXTERNAL_WRITE_RACE": "REFRESH_SNAPSHOT",
	"ARTIFACT_IMMUTABLE": "FIX_INPUT", "CREDENTIAL_MISSING": "RECONFIGURE",
	"CREDENTIAL_REVOKED": "RECONFIGURE", "CONFIG_CONFLICT": "RECONFIGURE",
	"MODEL_UNAVAILABLE": "RECONFIGURE", "PROVIDER_AUTH_FAILED": "RECONFIGURE",
	"PROVIDER_RATE_LIMITED": "WAIT_FOR_SETTLEMENT", "PROVIDER_TIMEOUT": "RETRY_SAME_COMMAND",
	"NETWORK_UNAVAILABLE": "WAIT_FOR_SETTLEMENT", "RESOURCE_BLOCKED": "RESOLVE_RESOURCE",
	"CANCEL_UNCONFIRMED": "WAIT_FOR_SETTLEMENT", "ALREADY_TERMINAL": "REFRESH_SNAPSHOT",
	"INTERNAL_ERROR": "WAIT_FOR_SETTLEMENT", "VERSION_CONFLICT": "REFRESH_SNAPSHOT",
}

// retryableCodes are the only answers where re-sending the identical command_id can change
// the outcome; everything else needs a client-side change first.
var retryableCodes = map[string]bool{
	"COMMAND_PENDING": true, "PROVIDER_TIMEOUT": true, "NETWORK_UNAVAILABLE": true,
	"HOST_UNAVAILABLE": true, "SESSION_BUSY": true, "CANCEL_UNCONFIRMED": true,
	"PROVIDER_RATE_LIMITED": true, "INTERNAL_ERROR": true,
}

// clientSessionRow is the authoritative index snapshot every command gate reads.
type clientSessionRow struct {
	project        string
	sessionID      string
	revision       int64
	epoch          int64
	watermark      int64
	writerClientID string
	runID          string
	sealed         bool
	archived       bool
}

// Execute runs one typed command through the identity/CAS gate with idempotent replay and
// transactional event journaling. It returns (response, replayed, error): a rejection is a
// normal response, while a non-nil error means the caller must roll the whole transaction
// back so neither business state nor an event survives.
func (s *ClientService) Execute(ctx context.Context, tx *sql.Tx, env *Envelope, principal string) (*Response, bool, error) {
	if env == nil || env.Method == nil {
		return nil, false, fmt.Errorf("COMMAND_ENVELOPE_REQUIRED")
	}
	if _, err := clientAuthenticatedPrincipal(ctx, tx, principal); err != nil {
		return nil, false, err
	}
	if s.Doc == nil {
		return nil, false, fmt.Errorf("COMMAND_SCHEMA_REQUIRED")
	}
	if _, err := validateClientIdentityRequest(s.Doc, env.originalRaw, env); err != nil {
		return NewTypedRejection(env, "INVALID_REQUEST", "command violates the published request schema"), false, nil
	}
	if _, err := nativeOriginHistoryTx(ctx, tx, s.Doc); err != nil {
		return nil, false, err
	}
	hash, err := env.ContentHash()
	if err != nil {
		return nil, false, err
	}
	original, err := lookupClientCommandIdentity(ctx, tx, s.Doc, principal, env.originalRaw, env)
	if err != nil {
		return nil, false, err
	}
	if original != nil && !(deref(env.Method) == "session.control" && deref(original.Status) == "ACKNOWLEDGED") {
		return original, true, nil
	}

	nativeOrigin, err := s.authorizeNativeCreate(ctx, tx, env, principal)
	if err != nil {
		return clientFaultForExecute(env, err)
	}
	var existingHash, body string
	row := tx.QueryRowContext(ctx, `SELECT request_hash, body FROM idempotency WHERE principal=? AND project=? AND operation=? AND key=?`,
		principal, deref(env.ProjectID), "v2:"+*env.Method, *env.CommandID)
	err = row.Scan(&existingHash, &body)
	switch {
	case err == nil:
		if existingHash != hash {
			return nil, false, ErrIdemConflict
		}
		var r Response
		if err := json.Unmarshal([]byte(body), &r); err != nil {
			return nil, false, err
		}
		if deref(env.Method) == "session.control" && deref(r.Status) == "ACKNOWLEDGED" {
			final, err := s.finalizeClientCancel(ctx, tx, env, principal, nil)
			if err != nil {
				return nil, false, err
			}
			if final != nil {
				if s.Doc != nil {
					var generic map[string]any
					if err = json.Unmarshal(Bytes(final), &generic); err != nil {
						return nil, false, err
					}
					if err = s.Doc.ValidateDef("CommandResponse", generic); err != nil {
						return nil, false, err
					}
					if err = ValidateResultAgainstMethod(*env.Method, final, s.Doc); err != nil {
						return nil, false, err
					}
				}
				if _, err = tx.ExecContext(ctx, "UPDATE idempotency SET body=? WHERE principal=? AND project=? AND operation=? AND key=? AND request_hash=?", string(Bytes(final)), principal, deref(env.ProjectID), "v2:"+deref(env.Method), deref(env.CommandID), hash); err != nil {
					return nil, false, err
				}
				return final, true, nil
			}
		}
		return &r, true, nil
	case err != sql.ErrNoRows:
		return nil, false, err
	}
	if _, err = reserveClientCommandIdentity(ctx, tx, s.Doc, principal, env.originalRaw, env); err != nil {
		return nil, false, err
	}
	headers, err := writeClientCommandEnvelope(s.Doc, env)
	if err != nil {
		return nil, false, err
	}
	// A typed rejection is committed for idempotency, but must not preserve any
	// intermediate business writes made before a handler discovers the refusal.
	if _, err = tx.ExecContext(ctx, "SAVEPOINT client_command"); err != nil {
		return nil, false, err
	}
	ctx, err = s.pendingCommandContext(ctx, tx, env, principal)
	if err != nil {
		return nil, false, err
	}
	res, err := s.dispatch(ctx, tx, env, principal)
	if err != nil {
		return nil, false, err
	}
	if res != nil && (deref(res.Status) == "REJECTED" || deref(res.Status) == "NOT_IMPLEMENTED") {
		if _, err = tx.ExecContext(ctx, "ROLLBACK TO client_command"); err != nil {
			return nil, false, err
		}
	}
	if _, err = tx.ExecContext(ctx, "RELEASE client_command"); err != nil {
		return nil, false, err
	}
	if res.ProtocolVersion == nil || *res.ProtocolVersion != ProtocolV2 {
		return nil, false, fmt.Errorf("RESPONSE_PROTOCOL")
	}
	// Our own output is validated against the published schema in read direction, so a
	// handler can never emit a shape the contract forbids (credential material included).
	if s.Doc != nil {
		raw, _ := json.Marshal(res)
		var generic map[string]any
		if err := json.Unmarshal(raw, &generic); err != nil {
			return nil, false, err
		}
		if err := s.Doc.ValidateDef("CommandResponse", generic); err != nil {
			return nil, false, fmt.Errorf("%w: %v", ErrResponseSchema, err)
		}
		if err := ValidateResultAgainstMethod(*env.Method, res, s.Doc); err != nil {
			return nil, false, err
		}
	}
	rb, _ := json.Marshal(res)
	if deref(env.Method) == "session.control" {
		if _, err = tx.ExecContext(ctx, "UPDATE client_control_requests SET original_response=coalesce(original_response,?) WHERE principal=? AND project=? AND command_id=?", string(rb), principal, deref(env.ProjectID), deref(env.CommandID)); err != nil {
			return nil, false, err
		}
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,?,?,?,?)`,
		principal, deref(env.ProjectID), "v2:"+*env.Method, *env.CommandID, hash, 0, string(rb), headers, time.Now().UTC().Format(time.RFC3339Nano)); err != nil {
		return nil, false, err
	}
	if _, err = lookupClientCommandIdentity(ctx, tx, s.Doc, principal, env.originalRaw, env); err != nil {
		return nil, false, err
	}
	if deref(env.Method) == "goal.start" && deref(res.Status) == "COMPLETED" {
		snapshot, _ := res.Result["snapshot"].(map[string]any)
		sid := Str(snapshot, "session_id")
		row, e := loadClientSession(ctx, tx, sid, deref(env.ProjectID))
		if e != nil {
			return nil, false, e
		}
		creator, e := clientSessionCreationPrincipal(ctx, tx, deref(env.ProjectID), sid)
		if e != nil || creator != principal {
			return nil, false, fmt.Errorf("COMMAND_IDENTITY_GOAL_CREATION")
		}
		if env.SessionID != nil && sid != *env.SessionID {
			return nil, false, fmt.Errorf("COMMAND_IDENTITY_GOAL_SESSION")
		}
		if e = s.validateSessionConfiguration(ctx, tx, principal, row, true); e != nil {
			return nil, false, e
		}
	}
	if deref(env.Method) == "host.configure" && deref(res.Status) == "COMPLETED" {
		owner, e := s.configurationOwner(ctx, tx, principal)
		if e != nil {
			return nil, false, e
		}
		if _, e = readClientConfiguration(ctx, tx, s.Doc, owner, principal, Str(res.Result, "model_config_ref")); e != nil {
			return nil, false, e
		}
	}
	if err := s.recordNativeCreateOrigin(ctx, tx, env, principal, res, nativeOrigin); err != nil {
		return nil, false, err
	}
	return res, false, nil
}

func deref(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// dispatch authenticates, then applies the session/project/revision/epoch gate to every
// write method before any handler runs.
func (s *ClientService) dispatch(ctx context.Context, tx *sql.Tx, env *Envelope, principal string) (*Response, error) {
	reject := func(rev int64, epoch any, code, msg string) *Response {
		return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method,
			Status: strptr("REJECTED"), SessionID: env.SessionID, Revision: revPtr(rev),
			ErrorCode: strptr(code),
			Error: &ProtocolError{Code: code, Message: msg, Retryable: retryableCodes[code],
				Recovery: recoveryByCode[code], CurrentRevision: revAny(rev), CurrentWriterEpoch: epoch,
				ResourceRequestID: nil, RetryAfterMs: nil, CorrelationID: deref(env.CommandID)}}
	}
	if principal == "" {
		return reject(0, nil, "UNAUTHENTICATED", "no authenticated OS principal on this connection"), nil
	}
	if !methodsV2[*env.Method] {
		return reject(0, nil, "UNSUPPORTED_METHOD", "method is not part of researchos-client/2"), nil
	}
	if *env.Method == "session.create" {
		if env.SessionID != nil || env.ExpectedRevision != nil || env.WriterEpoch != nil {
			return reject(0, nil, "INVALID_REQUEST", "session creation must not claim a session revision or writer epoch"), nil
		}
		return s.createClientSession(ctx, tx, env, principal)
	}
	if *env.Method == "session.list" {
		return s.listClientSessions(ctx, tx, env, principal)
	}
	if *env.Method == "workspace.register" || *env.Method == "project.bootstrap" {
		return s.clientFirstUse(ctx, tx, env, principal)
	}
	if *env.Method == "host.status" || *env.Method == "workspace.list" {
		if env.SessionID != nil || env.ExpectedRevision != nil || env.WriterEpoch != nil {
			return reject(0, nil, "INVALID_REQUEST", "workspace metadata reads cannot claim session or writer state"), nil
		}
	}
	if deref(env.SessionID) != "" {
		if *env.Method == "session.attach" && isTruePayloadAttach(env.Payload) {
			owner, err := clientPrincipal(ctx, tx, principal, deref(env.ProjectID), true)
			if err != nil || owner.DeviceID != "" {
				return reject(0, nil, "FORBIDDEN", "local project Owner required for writer attach"), nil
			}
		}
		if err := clientSessionOwner(ctx, tx, deref(env.ProjectID), deref(env.SessionID), principal); err != nil {
			return reject(0, nil, "FORBIDDEN", "session belongs to another principal"), nil
		}
	}
	// session.attach is dual-mode: reading a snapshot needs no writer claim, while
	// request_write_owner is a write that must pass the full gate.
	takeover := false
	if *env.Method == "session.attach" {
		var p struct {
			RequestWriteOwner bool `json:"request_write_owner"`
		}
		json.Unmarshal(env.Payload, &p)
		takeover = p.RequestWriteOwner
	}
	if !writeMethods[*env.Method] && !takeover {
		return s.handleRead(ctx, tx, env, principal, reject)
	}
	if deref(env.SessionID) == "" {
		// Host-level writes (configure, bootstrap, workspace registration) legitimately
		// carry no session; they are gated by the project/OS identity checks in their own
		// handler cards, not by a session row that does not exist yet.
		switch *env.Method {
		case "host.configure", "project.bootstrap", "workspace.register":
			return s.handleWrite(ctx, tx, env, principal, nil, reject)
		case "goal.start":
			return s.startClientGoal(ctx, tx, env, principal, nil)
		}
		return reject(0, nil, "INVALID_REQUEST", "write command requires a session id"), nil
	}
	sess, err := loadClientSession(ctx, tx, deref(env.SessionID), deref(env.ProjectID))
	if err == sql.ErrNoRows {
		return reject(0, nil, "NOT_FOUND", "unknown session for this project"), nil
	}
	if err != nil {
		return nil, err
	}
	if sess.sealed || sess.archived {
		return reject(sess.revision, sess.epoch, "SESSION_ARCHIVED", "session is sealed or archived"), nil
	}
	if env.ExpectedRevision == nil || *env.ExpectedRevision != sess.revision {
		// A stale snapshot answers with the live revision; the client must refresh, and the
		// service never retries the command on its behalf.
		return reject(sess.revision, sess.epoch, "VERSION_CONFLICT", "expected_revision is not the current session revision"), nil
	}
	if takeover {
		if env.WriterEpoch != nil {
			return reject(sess.revision, sess.epoch, "INVALID_REQUEST", "a takeover request must not claim a writer epoch"), nil
		}
	} else {
		if env.WriterEpoch == nil {
			return reject(sess.revision, sess.epoch, "STALE_WRITER_EPOCH", "writer_epoch is required for a write"), nil
		}
		if *env.WriterEpoch != sess.epoch {
			return reject(sess.revision, sess.epoch, "STALE_WRITER_EPOCH", "writer_epoch is not the current owner"), nil
		}
		if sess.writerClientID != deref(env.ClientID) {
			return reject(sess.revision, sess.epoch, "WRITER_BUSY", "writer attribution belongs to another client"), nil
		}
	}
	if deref(env.Method) == "session.send" || deref(env.Method) == "goal.start" {
		if err := s.validateSessionConfiguration(ctx, tx, principal, sess, false); err != nil {
			return clientFault(env, err)
		}
	}
	return s.handleWrite(ctx, tx, env, principal, sess, reject)
}

func isTruePayloadAttach(raw json.RawMessage) bool {
	var p struct {
		RequestWriteOwner bool `json:"request_write_owner"`
	}
	return json.Unmarshal(raw, &p) == nil && p.RequestWriteOwner
}

func loadClientSession(ctx context.Context, tx *sql.Tx, sessionID, project string) (*clientSessionRow, error) {
	row := &clientSessionRow{}
	if sessionID == "" {
		return nil, sql.ErrNoRows
	}
	var runID, sealedAt, archivedAt sql.NullString
	err := tx.QueryRowContext(ctx, `SELECT project_id, revision, writer_epoch, event_watermark, writer_client_id, run_id, sealed_at, archived_at
		FROM client_sessions WHERE id=?`, sessionID).
		Scan(&row.project, &row.revision, &row.epoch, &row.watermark, &row.writerClientID, &runID, &sealedAt, &archivedAt)
	if err != nil {
		return nil, err
	}
	if project != "" && row.project != project {
		// Cross-project references never resolve, and the answer must not leak the real project.
		return nil, sql.ErrNoRows
	}
	row.sessionID = sessionID
	row.runID = runID.String
	row.sealed = sealedAt.Valid
	row.archived = archivedAt.Valid
	return row, nil
}

func (s *ClientService) handleRead(ctx context.Context, tx *sql.Tx, env *Envelope, principal string,
	reject func(int64, any, string, string) *Response) (*Response, error) {
	complete := func(rev int64, result map[string]any) *Response {
		return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method,
			Status: strptr("COMPLETED"), SessionID: env.SessionID, Revision: revPtr(rev), Result: result}
	}
	switch *env.Method {
	case "host.status":
		if s.Host.InstanceID == "" || s.Host.CoreBuildID == "" {
			return reject(0, nil, "HOST_UNAVAILABLE", "host identity is not configured"), nil
		}
		mode := s.Host.OperatingMode
		if mode == "" {
			mode = "LOCAL_USER_HOST"
		}
		methods := make([]string, 0, len(methodsV2))
		for m := range methodsV2 {
			methods = append(methods, m)
		}
		sort.Strings(methods)
		support := make([]any, 0, len(methods))
		for _, m := range methods {
			support = append(support, m)
		}
		revision, configs, credentials, err := s.clientConfigurationStatus(ctx, tx, principal)
		if err != nil {
			return clientFault(env, err)
		}
		workspaces, err := s.clientWorkspaceProjection(ctx, tx, env, principal)
		if err != nil {
			return clientFault(env, err)
		}
		return complete(1, map[string]any{
			"host_instance_id": s.Host.InstanceID, "core_build_id": s.Host.CoreBuildID,
			"protocol_versions": []any{ProtocolV2}, "host_state": "READY",
			"client_id": deref(env.ClientID), "authenticated_principal_ref": principal,
			"config_revision": revision, "model_configurations": configs,
			"credentials": credentials, "workspaces": workspaces,
			"supported_methods": support, "operating_mode": mode,
		}), nil
	case "workspace.list":
		workspaces, err := s.clientWorkspaceProjection(ctx, tx, env, principal)
		if err != nil {
			return clientFault(env, err)
		}
		return complete(1, map[string]any{"items": workspaces}), nil
	case "workspace.tree", "workspace.read", "workspace.diff":
		return s.readClientWorkspace(ctx, tx, env, principal)
	case "session.get", "session.attach":
		sess, err := loadClientSession(ctx, tx, deref(env.SessionID), deref(env.ProjectID))
		if err == sql.ErrNoRows {
			return reject(0, nil, "NOT_FOUND", "unknown session for this project"), nil
		}
		if err != nil {
			return nil, err
		}
		snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
		if err != nil {
			return nil, err
		}
		if *env.Method == "session.get" {
			return complete(sess.revision, snap), nil
		}
		var p struct {
			AfterSequence *int64 `json:"after_sequence"`
		}
		json.Unmarshal(env.Payload, &p)
		if after := derefI64(p.AfterSequence, 0); after > sess.watermark {
			// A cursor from the future cannot be served by the journal; the snapshot is the
			// recovery vehicle, so the client is told to restart from it.
			return reject(sess.revision, sess.epoch, "CURSOR_INVALID", "after_sequence exceeds the session watermark; recover from snapshot"), nil
		}
		return complete(sess.revision, map[string]any{"snapshot": snap, "write_owner_acquired": false}), nil
	case "session.events":
		sess, err := loadClientSession(ctx, tx, deref(env.SessionID), deref(env.ProjectID))
		if err == sql.ErrNoRows {
			return reject(0, nil, "NOT_FOUND", "unknown session for this project"), nil
		}
		if err != nil {
			return nil, err
		}
		var p struct {
			AfterSequence *int64 `json:"after_sequence"`
			Limit         *int64 `json:"limit"`
		}
		json.Unmarshal(env.Payload, &p)
		page, err := ReadSessionEvents(ctx, tx, sess.project, sess.sessionID, derefI64(p.AfterSequence, 0), derefI64(p.Limit, MaxEventPage))
		if err == ErrResyncRequired {
			return reject(sess.revision, sess.epoch, "CURSOR_INVALID", err.Error()), nil
		}
		if err != nil {
			return nil, err
		}
		events := make([]any, 0, len(page.Events))
		for i := range page.Events {
			raw, err := json.Marshal(page.Events[i])
			if err != nil {
				return nil, err
			}
			var g map[string]any
			if err := json.Unmarshal(raw, &g); err != nil {
				return nil, err
			}
			events = append(events, g)
		}
		return complete(sess.revision, map[string]any{"events": events, "next_sequence": page.NextSequence,
			"high_watermark": page.HighWatermark, "has_more": page.HasMore}), nil
	default:
		return reject(0, nil, "NOT_IMPLEMENTED", "no handler for this read method on this host build"), nil
	}
}

func (s *ClientService) handleWrite(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow, reject func(int64, any, string, string) *Response) (*Response, error) {
	complete := func(rev int64, result map[string]any) *Response {
		return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method,
			Status: strptr("COMPLETED"), SessionID: env.SessionID, Revision: revPtr(rev), Result: result}
	}
	switch *env.Method {
	case "host.configure":
		return s.configureClientHost(ctx, tx, env, principal, sess)
	case "workspace.register", "project.bootstrap":
		return s.clientFirstUse(ctx, tx, env, principal)
	case "session.send":
		return s.sendClientMessage(ctx, tx, env, principal, sess)
	case "goal.start":
		return s.startClientGoal(ctx, tx, env, principal, sess)
	case "artifact.import":
		return s.importClientArtifact(ctx, tx, env, principal, sess)
	case "workspace.write":
		return s.writeClientWorkspace(ctx, tx, env, principal, sess)
	case "permission.respond":
		return s.respondClientPermission(ctx, tx, env, principal, sess)
	case "session.attach":
		var p struct {
			RequestWriteOwner bool  `json:"request_write_owner"`
			AfterSequence     int64 `json:"after_sequence"`
		}
		if err := json.Unmarshal(env.Payload, &p); err != nil {
			return nil, err
		}
		if !p.RequestWriteOwner {
			return reject(sess.revision, sess.epoch, "INVALID_REQUEST", "attach without write ownership is a read path"), nil
		}
		if p.AfterSequence < 0 || p.AfterSequence > sess.watermark {
			return reject(sess.revision, sess.epoch, "CURSOR_INVALID", "after_sequence exceeds the session watermark; recover from snapshot"), nil
		}
		if s.Host.LeaseTTL <= 0 || s.Host.LeaseTTL > 15*time.Minute {
			return nil, fmt.Errorf("HOST_LEASE_POLICY_INVALID")
		}
		creator, err := s.attachCreationAuthority(ctx, tx, principal, sess)
		if err != nil {
			return clientFault(env, err)
		}
		if creator != principal {
			return reject(sess.revision, sess.epoch, "FORBIDDEN", "session belongs to another principal"), nil
		}
		if sess.writerClientID != deref(env.ClientID) {
			marked, err := hasNativeWriterOrigin(ctx, tx, sess.project, sess.sessionID)
			if err != nil {
				return nil, err
			}
			if marked {
				return reject(sess.revision, sess.epoch, "WRITER_BUSY", "Native-origin writer handoff is not supported by this pilot"), nil
			}
		}
		var oldLease sql.NullString
		if err := tx.QueryRowContext(ctx, `SELECT lease_expires_at FROM client_sessions WHERE id=? AND project_id=?`, sess.sessionID, sess.project).Scan(&oldLease); err != nil {
			return nil, err
		}
		nowT := time.Now().UTC()
		var until time.Time
		if oldLease.Valid {
			until, err = time.Parse(time.RFC3339Nano, oldLease.String)
			if err != nil {
				return reject(sess.revision, sess.epoch, "WRITER_BUSY", "writer lease state is invalid"), nil
			}
		}
		if oldLease.Valid && sess.writerClientID == deref(env.ClientID) {
			// An ordinary renewal does not invalidate the current writer's claims.
			if err := s.attachRenewalSafe(ctx, tx, principal, sess); err != nil {
				return clientFault(env, err)
			}
			res, err := tx.ExecContext(ctx, `UPDATE client_sessions SET lease_expires_at=?,updated_at=? WHERE id=? AND project_id=? AND writer_client_id=? AND revision=? AND writer_epoch=? AND lease_expires_at=? AND sealed_at IS NULL AND archived_at IS NULL`, nowT.Add(s.Host.LeaseTTL).Format(time.RFC3339Nano), nowT.Format(time.RFC3339Nano), sess.sessionID, sess.project, sess.writerClientID, sess.revision, sess.epoch, oldLease.String)
			if err != nil {
				return nil, err
			}
			if n, err := res.RowsAffected(); err != nil || n != 1 {
				return nil, fmt.Errorf("ATTACH_RENEWAL_CAS: %v", err)
			}
			snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
			if err != nil {
				return nil, err
			}
			return complete(sess.revision, map[string]any{"snapshot": snap, "write_owner_acquired": true}), nil
		}
		if oldLease.Valid && until.After(nowT) {
			return reject(sess.revision, sess.epoch, "WRITER_BUSY", "another client holds the writer lease"), nil
		}
		if err := s.attachRenewalSafe(ctx, tx, principal, sess); err != nil {
			return clientFault(env, err)
		}
		if err := s.attachSettlement(ctx, tx, principal, sess); err != nil {
			return clientFault(env, err)
		}
		if sess.epoch == math.MaxInt64 || sess.revision > math.MaxInt64-2 || sess.watermark == math.MaxInt64 {
			return nil, fmt.Errorf("ATTACH_SEQUENCE_OVERFLOW")
		}
		prevEpoch, prevClient := sess.epoch, sess.writerClientID
		newEpoch, err := HandoffEpoch(ctx, tx, sess.sessionID, sess.epoch, sess.revision)
		if err != nil {
			code := "WRITER_BUSY"
			if errors.Is(err, ErrStaleRevision) || errors.Is(err, ErrStaleEpoch) {
				code = "VERSION_CONFLICT"
			}
			return reject(sess.revision, sess.epoch, code, err.Error()), nil
		}
		// Writer attribution moves with the epoch inside this same transaction, so the old
		// client cannot slip a command in between the transfer and the journal row.
		res, err := tx.ExecContext(ctx, `UPDATE client_sessions SET writer_client_id=?,lease_expires_at=?,updated_at=? WHERE id=? AND project_id=? AND writer_epoch=? AND revision=? AND writer_client_id=? AND lease_expires_at IS ? AND sealed_at IS NULL AND archived_at IS NULL`,
			deref(env.ClientID), nowT.Add(s.Host.LeaseTTL).Format(time.RFC3339Nano), nowT.Format(time.RFC3339Nano), sess.sessionID, sess.project, newEpoch, sess.revision+1, prevClient, oldLease)
		if err != nil {
			return nil, err
		}
		if n, err := res.RowsAffected(); err != nil || n != 1 {
			return nil, fmt.Errorf("ATTACH_GRANT_CAS: %v", err)
		}
		sess.writerClientID = deref(env.ClientID)
		now := nowT.Format(time.RFC3339Nano)
		// the transfer already advanced epoch and revision; the journal row is written under
		// the new ownership claim, so both CAS layers agree inside this one transaction
		sess.epoch = newEpoch
		sess.revision = sess.revision + 1
		if err := s.journal(ctx, tx, env, sess, "CLIENT_HANDOFF", map[string]any{
			"previous_client_id": prevClient,
			"target_client_id":   deref(env.ClientID),
			"previous_epoch":     prevEpoch,
			"writer": map[string]any{
				"client_id":  deref(env.ClientID),
				"epoch":      newEpoch,
				"expires_at": nowT.Add(s.Host.LeaseTTL).Format(time.RFC3339Nano),
			},
			"effective_at": now,
		}); err != nil {
			return nil, err
		}
		snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
		if err != nil {
			return nil, err
		}
		return complete(sess.revision+1, map[string]any{"snapshot": snap, "write_owner_acquired": true}), nil
	case "session.control":
		var p struct {
			Action   *string `json:"action"`
			TargetID *string `json:"target_id"`
		}
		json.Unmarshal(env.Payload, &p)
		if deref(p.Action) == "RESUME" && deref(p.TargetID) == sess.sessionID {
			pending, err := clientPendingCommands(ctx, tx, sess.project, sess.sessionID)
			if err != nil {
				return nil, err
			}
			var fenced int
			if err = tx.QueryRow(`SELECT count(*) FROM client_queue_fences WHERE project=? AND session_id=? AND (restore_fenced<>0 OR state='RECONCILING')`, sess.project, sess.sessionID).Scan(&fenced); err != nil {
				return nil, err
			}
			if len(pending) > 0 || fenced > 0 {
				return reject(sess.revision, sess.epoch, "SESSION_BUSY", "command queue requires reconciliation before resume"), nil
			}
			// Resuming a session restores its saved context. A cancelled or failed
			// Run is never restarted; a later explicit send creates the next turn.
			if sess.runID != "" {
				run, err := loadClientRun(ctx, tx, sess.project, sess.runID)
				if err != nil {
					return nil, err
				}
				if !run.terminal() || !run.childrenStopped || !run.queueEmpty {
					return reject(sess.revision, sess.epoch, "SESSION_BUSY", "previous runtime must settle before session resume"), nil
				}
			}
			snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
			if err != nil {
				return nil, err
			}
			return complete(sess.revision, map[string]any{"action": "RESUME", "target_id": sess.sessionID,
				"control_request_id": "ctrl-" + deref(env.CommandID), "settled": true,
				"children_stopped": true, "queue_empty": true, "snapshot": snap}), nil
		}
		if p.Action == nil || *p.Action != "CANCEL" {
			return reject(sess.revision, sess.epoch, "NOT_IMPLEMENTED", "only CANCEL run and RESUME session controls are implemented on this host build"), nil
		}
		return s.cancelClientTarget(ctx, tx, env, principal, sess, deref(p.TargetID))
	default:
		if sess == nil {
			return reject(0, nil, "NOT_IMPLEMENTED", "handler belongs to a later card"), nil
		}
		return reject(sess.revision, sess.epoch, "NOT_IMPLEMENTED", "handler belongs to a later card"), nil
	}
}

// attachCreationAuthority requires one original, immutable creation receipt and its
// command identity. A mapped session with no such proof remains readable only.
func (s *ClientService) attachCreationAuthority(ctx context.Context, tx *sql.Tx, principal string, sess *clientSessionRow) (string, error) {
	creator, err := clientSessionCreationPrincipal(ctx, tx, sess.project, sess.sessionID)
	if err != nil || creator != principal {
		return "", Fail(403, "FORBIDDEN", "original session creation attribution unavailable")
	}
	var key, operation, hash, headers, body string
	err = tx.QueryRowContext(ctx, `SELECT key,operation,request_hash,headers,body FROM idempotency WHERE principal=? AND project=? AND ((operation='v2:session.create' AND json_extract(body,'$.status')='COMPLETED' AND json_extract(body,'$.result.session_id')=?) OR (operation='v2:goal.start' AND json_extract(body,'$.status')='COMPLETED' AND json_extract(body,'$.session_id') IS NULL AND json_extract(body,'$.result.snapshot.session_id')=?))`, principal, sess.project, sess.sessionID, sess.sessionID).Scan(&key, &operation, &hash, &headers, &body)
	if err != nil {
		return "", Fail(403, "FORBIDDEN", "original session creation receipt unavailable")
	}
	req, known, err := readClientCommandEnvelope(s.Doc, headers)
	if err != nil {
		return "", err
	}
	if err := requireClientOriginalHeader(ctx, tx, principal, key, known); err != nil {
		return "", err
	}
	if !known || req.hash != hash || deref(req.env.CommandID) != key || deref(req.env.ProjectID) != sess.project || "v2:"+deref(req.env.Method) != operation {
		return "", Fail(403, "FORBIDDEN", "original session request identity unavailable")
	}
	var n int
	if err := tx.QueryRowContext(ctx, `SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=? AND request_hash=? AND project=? AND method=?`, principal, key, hash, sess.project, deref(req.env.Method)).Scan(&n); err != nil {
		return "", err
	}
	if n != 1 {
		return "", Fail(403, "FORBIDDEN", "original session command identity unavailable")
	}
	if _, err := decodeClientIdentityResponse(s.Doc, req, []byte(body)); err != nil {
		return "", err
	}
	return creator, nil
}

func (s *ClientService) attachRenewalSafe(ctx context.Context, tx *sql.Tx, principal string, sess *clientSessionRow) error {
	var restore, fences int
	var workspace string
	err := tx.QueryRowContext(ctx, `SELECT resume_requires_explicit_user,COALESCE(workspace_ref,'') FROM client_sessions WHERE id=? AND project_id=?`, sess.sessionID, sess.project).Scan(&restore, &workspace)
	if err != nil {
		return err
	}
	if restore != 0 {
		return Fail(409, "SESSION_BUSY", "session restore requires explicit recovery")
	}
	err = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_queue_fences WHERE project=? AND session_id=? AND (restore_fenced<>0 OR state='RECONCILING')`, sess.project, sess.sessionID).Scan(&fences)
	if err != nil {
		return err
	}
	if fences != 0 {
		return Fail(409, "SESSION_BUSY", "session recovery fence is active")
	}
	if sess.runID != "" {
		status, _, err := runState(ctx, tx, sess.project, sess.runID)
		if err != nil {
			return err
		}
		if status == "RECONCILING" || status == "LOST" {
			return Fail(409, "SESSION_BUSY", "session run requires recovery")
		}
	}
	if s.Domain == nil {
		return Fail(503, "HOST_UNAVAILABLE", "workspace authority unavailable")
	}
	b, err := s.Domain.binding(ctx, tx, workspace)
	if err != nil || b.ProjectID == nil || *b.ProjectID != sess.project || b.PrincipalID != principal || b.Status != WorkspaceActive {
		return Fail(403, "WORKSPACE_REVOKED", "session workspace is unavailable")
	}
	return nil
}

// attachSettlement is the lease-independent, read-only settlement predicate used
// only for a new writer grant. The configuration predicate remains unchanged.
func (s *ClientService) attachSettlement(ctx context.Context, tx *sql.Tx, principal string, sess *clientSessionRow) error {
	if sess.runID != "" {
		run, err := load(tx, sess.project, "Run", sess.runID)
		if err != nil || !runTerminal(run) || run["children_stopped"] != true || run["queue_empty"] != true || effectsReconciled(tx, sess.project, sess.runID) != nil {
			return Fail(409, "SESSION_BUSY", "current session run is not settled")
		}
	}
	originalTasks, e := s.originalSessionTasks(ctx, tx, principal, sess.project, sess.sessionID)
	if e != nil {
		return e
	}
	rows, e := tx.QueryContext(ctx, `SELECT DISTINCT t.body FROM domain_objects t WHERE t.project=? AND t.kind='Task' AND (t.id=(SELECT task_id FROM client_sessions WHERE id=?) OR json_extract(t.body,'$.goal_id') IN(SELECT COALESCE(json_extract(body,'$.result.goal_id'),json_extract(body,'$.result.snapshot.goal_id')) FROM idempotency WHERE project=? AND operation IN('v2:goal.start','v2:session.send') AND json_extract(body,'$.status')='COMPLETED' AND (json_extract(body,'$.session_id')=? OR json_extract(body,'$.result.snapshot.session_id')=?)) OR t.id IN(SELECT task_id FROM client_queue_fences WHERE project=? AND session_id=?))`, sess.project, sess.sessionID, sess.project, sess.sessionID, sess.sessionID, sess.project, sess.sessionID)
	if e != nil {
		return e
	}
	tasks := originalTasks
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return e
		}
		task, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return e
		}
		tasks = append(tasks, task)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, task := range tasks {
		if !clientTurnSettled(tx, sess.project, sess.sessionID, task) {
			return Fail(409, "SESSION_BUSY", "session task is not settled")
		}
		// A later active_run_id cannot hide an older generation's unresolved
		// effects or child process. Reuse the actual settlement predicate for
		// each canonical Run belonging to the original Task, without writes.
		runs, err := tx.QueryContext(ctx, `SELECT id FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?`, sess.project, Str(task, "id"))
		if err != nil {
			return err
		}
		ids := []string{}
		for runs.Next() {
			var id string
			if err = runs.Scan(&id); err != nil {
				runs.Close()
				return err
			}
			ids = append(ids, id)
		}
		err = runs.Err()
		runs.Close()
		if err != nil {
			return err
		}
		for _, id := range ids {
			historical := Object{}
			for k, v := range task {
				historical[k] = v
			}
			historical["active_run_id"] = id
			if !clientTurnSettled(tx, sess.project, sess.sessionID, historical) {
				return Fail(409, "SESSION_BUSY", "earlier session run is not settled")
			}
		}
	}
	var pending int
	e = tx.QueryRowContext(ctx, `SELECT (SELECT count(*) FROM client_command_queue WHERE project=? AND session_id=? AND state NOT IN('CONSUMED','DROPPED'))+(SELECT count(*) FROM client_control_requests WHERE project=? AND session_id=? AND state<>'CONFIRMED')+(SELECT count(*) FROM client_queue_fences WHERE project=? AND session_id=? AND (restore_fenced<>0 OR state='RECONCILING'))`, sess.project, sess.sessionID, sess.project, sess.sessionID, sess.project, sess.sessionID).Scan(&pending)
	if e != nil {
		return e
	}
	if pending != 0 {
		return Fail(409, "SESSION_BUSY", "session controls remain unresolved")
	}
	rows, e = tx.QueryContext(ctx, `SELECT q.state,q.command_id,q.generation,COALESCE(r.kind,''),COALESCE(r.body,''),COALESCE(r.body_hash,'') FROM client_command_queue q LEFT JOIN client_control_receipts r ON r.receipt_id=q.last_receipt_id AND r.project=q.project AND r.generation=q.generation AND r.command_id=q.command_id WHERE q.project=? AND q.session_id=?`, sess.project, sess.sessionID)
	if e != nil {
		return e
	}
	type terminalReceipt struct{ state, command, generation, kind, body, hash string }
	receipts := []terminalReceipt{}
	for rows.Next() {
		var r terminalReceipt
		if e = rows.Scan(&r.state, &r.command, &r.generation, &r.kind, &r.body, &r.hash); e != nil {
			rows.Close()
			return e
		}
		receipts = append(receipts, r)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, r := range receipts {
		if Digest([]byte(r.body)) != r.hash {
			return Fail(409, "SESSION_BUSY", "queue settlement receipt unavailable")
		}
		if r.state == "DROPPED" && r.kind == "CANCEL_FENCE" {
			if e = s.validatePreSDKConfigurationDrop(ctx, tx, principal, sess, r.command, r.generation, r.body); e != nil {
				return e
			}
		} else if (r.state == "CONSUMED" && r.kind != "command.consumed") || (r.state == "DROPPED" && r.kind != "command.cleared") {
			return Fail(409, "SESSION_BUSY", "queue settlement receipt unavailable")
		}
	}

	// Permission facts are related to the original Session even after its head
	// Task/Run has advanced; inspect the complete relation, not just the head.
	e = tx.QueryRowContext(ctx, `SELECT count(*) FROM resource_effects x JOIN domain_objects r ON r.project=x.project AND r.kind='ResourceRequest' AND r.id=json_extract(x.body,'$.permission.request_id') WHERE x.project=? AND json_extract(x.body,'$.permission.session_id')=? AND json_extract(r.body,'$.status') IN('OPEN','ACKNOWLEDGED')`, sess.project, sess.sessionID).Scan(&pending)
	if e != nil {
		return e
	}
	if pending > 0 {
		return Fail(409, "SESSION_BUSY", "session permission remains unresolved")
	}
	return nil
}

// journal appends one typed event for the command's session inside the same transaction as
// the business write, under the writer's own epoch and revision.
func (s *ClientService) journal(ctx context.Context, tx *sql.Tx, env *Envelope, sess *clientSessionRow, kind string, payload map[string]any) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	seq := sess.watermark + 1
	runID := any(nil)
	if sess.runID != "" {
		runID = sess.runID
	}
	ev := &SessionEvent{
		// (session, sequence) is the journal's natural key, so the id cannot collide across
		// principals that replay the same command text in different sessions.
		EventID:   strptr(fmt.Sprintf("ev-%s-%d", sess.sessionID, seq)),
		SessionID: strptr(sess.sessionID), Sequence: int64ptr(seq),
		CoreBuildID: strptr(s.Host.CoreBuildID), ProtocolVersion: strptr(ProtocolV2),
		CommandID: env.CommandID, DomainEventID: nil,
		Kind: strptr(kind), Payload: body,
	}
	if rs, ok := runID.(string); ok {
		ev.RunID = strptr(rs)
	}
	return AppendSessionEvent(ctx, tx, s.Doc, sess.project, ev, sess.epoch, sess.revision)
}

func revPtr(v int64) *int64 {
	if v <= 0 {
		return nil
	}
	return &v
}

func revAny(v int64) any {
	if v <= 0 {
		return nil
	}
	return v
}

type clientRunRow struct {
	id              string
	revision        int64
	status          string
	childrenStopped bool
	queueEmpty      bool
	cancelAt        string
	confirmedAt     string
}

func (r clientRunRow) terminal() bool {
	switch r.status {
	case "SETTLED", "COMPLETED", "FAILED", "CANCELLED":
		return true
	}
	return false
}

func (r clientRunRow) cancelConfirmed() bool { return r.confirmedAt != "" }

func loadClientRun(ctx context.Context, tx *sql.Tx, project, runID string) (*clientRunRow, error) {
	var body string
	var rev int64
	err := tx.QueryRowContext(ctx, `SELECT body, revision FROM domain_objects WHERE kind='Run' AND id=? AND project=?`,
		runID, project).Scan(&body, &rev)
	if err != nil {
		return nil, err
	}
	var m map[string]any
	if err := json.Unmarshal([]byte(body), &m); err != nil {
		return nil, err
	}
	r := &clientRunRow{id: runID, revision: rev}
	if s, ok := m["status"].(string); ok {
		r.status = s
	}
	if b, ok := m["children_stopped"].(bool); ok {
		r.childrenStopped = b
	}
	if b, ok := m["queue_empty"].(bool); ok {
		r.queueEmpty = b
	}
	if t, ok := m["cancel_requested_at"].(string); ok {
		r.cancelAt = t
	}
	if t, ok := m["cancel_confirmed_at"].(string); ok {
		r.confirmedAt = t
	}
	if r.status == "" {
		r.status = "RUNNING"
	}
	if r.revision < 1 {
		r.revision = 1
	}
	return r, nil
}

func strptr(s string) *string { return &s }
func int64ptr(i int64) *int64 { return &i }

func derefI64(p *int64, def int64) int64 {
	if p == nil {
		return def
	}
	return *p
}

// NewTypedRejection builds the published rejection shape for a boundary the request could not
// pass (missing credential, absent grant). Only fields the caller actually know are filled:
// the session id and current revision come from the decoded envelope, never from the client's
// claim, and the error object carries the recovery the client must perform.
func NewTypedRejection(env *Envelope, code, message string) *Response {
	rev := int64(0)
	if env != nil && env.ExpectedRevision != nil {
		rev = *env.ExpectedRevision
	}
	cid := envCommand(env)
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method,
		Status: strptr("REJECTED"), SessionID: env.SessionID, Revision: revPtr(rev),
		ErrorCode: strptr(code),
		Error: &ProtocolError{Code: code, Message: message, Retryable: retryableCodes[code],
			Recovery: recoveryByCode[code], CurrentRevision: revAny(rev), CurrentWriterEpoch: nil,
			ResourceRequestID: nil, RetryAfterMs: nil, CorrelationID: cid}}
}

func envCommand(env *Envelope) string {
	if env == nil || env.CommandID == nil {
		return "unparsed-command"
	}
	return *env.CommandID
}

func clientFaultForExecute(env *Envelope, err error) (*Response, bool, error) {
	r, e := clientFault(env, err)
	return r, false, e
}

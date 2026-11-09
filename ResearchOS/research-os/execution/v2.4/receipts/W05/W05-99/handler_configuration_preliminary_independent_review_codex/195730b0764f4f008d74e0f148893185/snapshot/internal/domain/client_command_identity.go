package domain

// Private caller-transaction helpers. Authentication must precede their use;
// they neither dispatch commands nor own response state. The existing
// idempotency row remains the only response authority (including cancel ACK
// finalization). Public Execute integration is deliberately not installed here.

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"unicode"
	"unicode/utf8"

	"researchos.local/research-os/internal/canonical"
)

const clientIdentityMaxRequest = 1 << 20

type clientIdentityRequest struct {
	env  *Envelope
	hash string
}

func clientIdentityLabel(value string) bool {
	return value != "" && len(value) <= 512 && utf8.ValidString(value) && strings.TrimSpace(value) == value && !strings.ContainsFunc(value, unicode.IsControl)
}

// Keep strict original bytes until after duplicate/Unicode validation. This
// private decoder performs contract shape validation, not the still-unwired
// host/session authorization or existing public DecodeEnvelope CAS gate.
func decodeClientIdentityEnvelope(doc *SchemaDoc, raw []byte) (*Envelope, error) {
	if doc == nil || len(raw) == 0 || len(raw) > clientIdentityMaxRequest {
		return nil, fmt.Errorf("COMMAND_IDENTITY_SCHEMA_OR_SIZE")
	}
	strict, err := canonical.JSON(raw)
	if err != nil {
		return nil, fmt.Errorf("COMMAND_IDENTITY_JSON: %w", err)
	}
	var generic any
	if err = json.Unmarshal(strict, &generic); err != nil {
		return nil, err
	}
	if err = doc.ValidateDefInput("CommandEnvelope", generic); err != nil {
		return nil, err
	}
	var env Envelope
	if err = json.Unmarshal(raw, &env); err != nil {
		return nil, err
	}
	if err = json.Unmarshal(raw, &env.extra); err != nil {
		return nil, err
	}
	env.originalRaw = append([]byte(nil), raw...)
	return &env, nil
}

func validateClientIdentityRequest(doc *SchemaDoc, raw []byte, env *Envelope) (clientIdentityRequest, error) {
	parsed, err := decodeClientIdentityEnvelope(doc, raw)
	if err != nil {
		return clientIdentityRequest{}, err
	}
	if env == nil || len(env.extra) == 0 {
		return clientIdentityRequest{}, fmt.Errorf("COMMAND_IDENTITY_RETAINED_ENVELOPE_REQUIRED")
	}
	original, err := canonical.JSON(raw)
	if err != nil {
		return clientIdentityRequest{}, err
	}
	fields, err := json.Marshal(env)
	if err != nil {
		return clientIdentityRequest{}, err
	}
	fields, err = canonical.JSON(fields)
	if err != nil || !bytes.Equal(fields, original) {
		return clientIdentityRequest{}, fmt.Errorf("COMMAND_IDENTITY_FIELDS_DIFFER_FROM_RAW")
	}
	retained, err := canonical.JSON([]byte(mustMarshal(env.extra)))
	if err != nil || !bytes.Equal(retained, original) {
		return clientIdentityRequest{}, fmt.Errorf("COMMAND_IDENTITY_RETAINED_RAW_MISMATCH")
	}
	hash, err := env.ContentHash()
	if err != nil {
		return clientIdentityRequest{}, err
	}
	actual, err := parsed.ContentHash()
	if err != nil || hash != actual {
		return clientIdentityRequest{}, fmt.Errorf("COMMAND_IDENTITY_HASH_MISMATCH")
	}
	return clientIdentityRequest{parsed, actual}, nil
}

func decodeClientIdentityResponse(doc *SchemaDoc, req clientIdentityRequest, raw []byte) (*Response, error) {
	if doc == nil || req.env == nil {
		return nil, fmt.Errorf("COMMAND_IDENTITY_SCHEMA_REQUIRED")
	}
	strict, err := canonical.JSON(raw)
	if err != nil {
		return nil, err
	}
	var generic any
	if err = json.Unmarshal(strict, &generic); err != nil {
		return nil, err
	}
	if err = doc.ValidateDef("CommandResponse", generic); err != nil {
		return nil, err
	}
	var response Response
	if err = json.Unmarshal(strict, &response); err != nil {
		return nil, err
	}
	derived := deref(req.env.Method) == "session.create" && deref(response.Status) == "COMPLETED" && req.env.SessionID == nil && response.SessionID != nil && Str(response.Result, "session_id") == *response.SessionID
	if deref(response.ProtocolVersion) != ProtocolV2 || deref(response.CommandID) != deref(req.env.CommandID) ||
		deref(response.Method) != deref(req.env.Method) || (!derived && !sameClientString(response.SessionID, req.env.SessionID)) {
		return nil, fmt.Errorf("COMMAND_IDENTITY_RESPONSE_MISMATCH")
	}
	if err = ValidateResultAgainstMethod(deref(req.env.Method), &response, doc); err != nil {
		return nil, err
	}
	if deref(req.env.Method) == "host.status" && deref(response.Status) == "COMPLETED" && Str(response.Result, "client_id") != deref(req.env.ClientID) {
		return nil, fmt.Errorf("COMMAND_IDENTITY_RESPONSE_CLIENT")
	}
	return &response, nil
}

// lookup scans the entire legacy v2 command namespace even when an identity is
// already present: an old unintegrated writer may have added a conflicting
// locator. Multiple legacy rows never get an arbitrary winning interpretation.
func lookupClientCommandIdentity(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, principal string, raw []byte, env *Envelope) (*Response, error) {
	req, err := validateClientIdentityRequest(doc, raw, env)
	if err != nil {
		return nil, err
	}
	if tx == nil || !clientIdentityLabel(principal) {
		return nil, fmt.Errorf("COMMAND_IDENTITY_PRINCIPAL")
	}
	var protocol, project, method, operation, hash string
	err = tx.QueryRowContext(ctx, `SELECT protocol,project,method,operation,request_hash FROM client_command_identities WHERE principal=? AND command_id=?`, principal, deref(env.CommandID)).Scan(&protocol, &project, &method, &operation, &hash)
	present := err == nil
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return nil, err
	}
	if present && (protocol != ProtocolV2 || project != deref(env.ProjectID) || method != deref(env.Method) || operation != "v2:"+deref(env.Method) || hash != req.hash) {
		return nil, ErrIdemConflict
	}
	rows, err := tx.QueryContext(ctx, `SELECT project,operation,request_hash,body,headers FROM idempotency WHERE principal=? AND key=? AND substr(operation,1,3)='v2:' ORDER BY project,operation`, principal, deref(env.CommandID))
	if err != nil {
		return nil, err
	}
	count := 0
	var body []byte
	var headers string
	mismatch := false
	for rows.Next() {
		count++
		var p, o, h string
		var b []byte
		if err = rows.Scan(&p, &o, &h, &b, &headers); err != nil {
			rows.Close()
			return nil, err
		}
		if p != deref(env.ProjectID) || o != "v2:"+deref(env.Method) || h != req.hash {
			mismatch = true
		}
		body = b
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	if count > 1 || mismatch {
		return nil, ErrIdemConflict
	}
	if count == 0 {
		if present {
			return nil, fmt.Errorf("COMMAND_IDENTITY_ORPHAN")
		}
		return nil, nil
	}
	stored, known, err := readClientCommandEnvelope(doc, headers)
	if err != nil {
		return nil, err
	}
	if known {
		if !present || stored.hash != req.hash {
			return nil, fmt.Errorf("COMMAND_IDENTITY_ORIGINAL_REQUEST")
		}
		req = stored
	}
	response, err := decodeClientIdentityResponse(doc, req, body)
	if err != nil {
		return nil, err
	}
	if err = validateClientDerivedSession(ctx, tx, principal, req, response); err != nil {
		return nil, err
	}
	return response, nil
}

func sameClientString(a, b *string) bool {
	return (a == nil && b == nil) || (a != nil && b != nil && *a == *b)
}

const clientCommandHeaderSchema = "researchos.private-command-envelope.v1"
const clientCommandHeaderMax = 1398200

type clientCommandHeader struct {
	Schema   string `json:"schema"`
	Encoding string `json:"encoding"`
	Raw      string `json:"raw_envelope_base64"`
}

func writeClientCommandEnvelope(doc *SchemaDoc, env *Envelope) (string, error) {
	if env == nil {
		return "", fmt.Errorf("COMMAND_IDENTITY_RETAINED_ENVELOPE_REQUIRED")
	}
	if _, err := validateClientIdentityRequest(doc, env.originalRaw, env); err != nil {
		return "", err
	}
	b, err := json.Marshal(clientCommandHeader{clientCommandHeaderSchema, "base64", base64.StdEncoding.EncodeToString(env.originalRaw)})
	return string(b), err
}

// Old headers retain their old interpretation. Recognized new records must
// satisfy the complete original-request proof; malformed records never grant
// the rejected-Session exception.
func readClientCommandEnvelope(doc *SchemaDoc, headers string) (clientIdentityRequest, bool, error) {
	var zero clientIdentityRequest
	if headers == "" || headers == "{}" {
		return zero, false, nil
	}
	if len(headers) > clientCommandHeaderMax {
		return zero, false, fmt.Errorf("COMMAND_ENVELOPE_HEADER_SIZE")
	}
	strict, err := canonical.JSON([]byte(headers))
	if err != nil {
		return zero, false, err
	}
	var fields map[string]json.RawMessage
	if err = json.Unmarshal(strict, &fields); err != nil {
		return zero, false, err
	}
	_, schema := fields["schema"]
	_, encoding := fields["encoding"]
	_, raw := fields["raw_envelope_base64"]
	if !schema && !encoding && !raw {
		return zero, false, nil
	}
	var h clientCommandHeader
	if len(fields) != 3 || json.Unmarshal(strict, &h) != nil || h.Schema != clientCommandHeaderSchema || h.Encoding != "base64" || len(h.Raw) > 1398104 {
		return zero, true, fmt.Errorf("COMMAND_ENVELOPE_HEADER_SCHEMA")
	}
	stored, _ := json.Marshal(h)
	if !bytes.Equal(stored, []byte(headers)) {
		return zero, true, fmt.Errorf("COMMAND_ENVELOPE_HEADER_CANONICAL")
	}
	b, err := base64.StdEncoding.Strict().DecodeString(h.Raw)
	if err != nil || len(b) == 0 || len(b) > clientIdentityMaxRequest || base64.StdEncoding.EncodeToString(b) != h.Raw {
		return zero, true, fmt.Errorf("COMMAND_ENVELOPE_HEADER_BASE64")
	}
	env, err := decodeClientIdentityEnvelope(doc, b)
	if err != nil {
		return zero, true, err
	}
	req, err := validateClientIdentityRequest(doc, b, env)
	return req, true, err
}

func validateClientDerivedSession(ctx context.Context, tx *sql.Tx, principal string, req clientIdentityRequest, response *Response) error {
	method := deref(req.env.Method)
	if (method != "session.create" && method != "goal.start") || deref(response.Status) != "COMPLETED" {
		return nil
	}
	sid := deref(response.SessionID)
	var n int
	if method == "goal.start" {
		snapshot, _ := response.Result["snapshot"].(map[string]any)
		sid = Str(snapshot, "session_id")
		if sid == "" || (req.env.SessionID != nil && sid != *req.env.SessionID) {
			return fmt.Errorf("COMMAND_IDENTITY_GOAL_SESSION")
		}
	} else {
		if sid == "" || Str(response.Result, "session_id") != sid {
			return fmt.Errorf("COMMAND_IDENTITY_DERIVED_SESSION")
		}
	}
	if err := tx.QueryRowContext(ctx, `SELECT count(*) FROM client_sessions WHERE id=? AND project_id=?`, sid, deref(req.env.ProjectID)).Scan(&n); err != nil || n != 1 {
		return fmt.Errorf("COMMAND_IDENTITY_DERIVED_SESSION")
	}
	owner, err := clientSessionCreationPrincipal(ctx, tx, deref(req.env.ProjectID), sid)
	if err != nil || owner != principal {
		return fmt.Errorf("COMMAND_IDENTITY_DERIVED_CREATION")
	}
	return nil
}

// reserve is called once, before new business writes, inside the same outer
// transaction that will insert the original idempotency row. Commit-time FK
// rejects missing or different request hashes. Exact legacy replay may be
// linked, but this function never stores or updates a response.
func reserveClientCommandIdentity(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, principal string, raw []byte, env *Envelope) (*Response, error) {
	response, err := lookupClientCommandIdentity(ctx, tx, doc, principal, raw, env)
	if err != nil {
		return nil, err
	}
	req, err := validateClientIdentityRequest(doc, raw, env)
	if err != nil {
		return nil, err
	}
	var count int
	if err = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=?`, principal, deref(env.CommandID)).Scan(&count); err != nil {
		return nil, err
	}
	if count == 0 {
		_, err = tx.ExecContext(ctx, `INSERT INTO client_command_identities(principal,command_id,protocol,project,method,operation,request_hash,created_at) VALUES(?,?,?,?,?,?,?,?)`, principal, deref(env.CommandID), ProtocolV2, deref(env.ProjectID), deref(env.Method), "v2:"+deref(env.Method), req.hash, Now())
	}
	return response, err
}

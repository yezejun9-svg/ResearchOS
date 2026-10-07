package domain

// Private caller-transaction helpers. Authentication must precede their use;
// they neither dispatch commands nor own response state. The existing
// idempotency row remains the only response authority (including cancel ACK
// finalization). Public Execute integration is deliberately not installed here.

import (
	"bytes"
	"context"
	"database/sql"
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
	if deref(response.ProtocolVersion) != ProtocolV2 || deref(response.CommandID) != deref(req.env.CommandID) ||
		deref(response.Method) != deref(req.env.Method) || deref(response.SessionID) != deref(req.env.SessionID) {
		return nil, fmt.Errorf("COMMAND_IDENTITY_RESPONSE_MISMATCH")
	}
	if err = ValidateResultAgainstMethod(deref(req.env.Method), &response, doc); err != nil {
		return nil, err
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
	rows, err := tx.QueryContext(ctx, `SELECT project,operation,request_hash,body FROM idempotency WHERE principal=? AND key=? AND substr(operation,1,3)='v2:' ORDER BY project,operation`, principal, deref(env.CommandID))
	if err != nil {
		return nil, err
	}
	count := 0
	var body []byte
	mismatch := false
	for rows.Next() {
		count++
		var p, o, h string
		var b []byte
		if err = rows.Scan(&p, &o, &h, &b); err != nil {
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
	return decodeClientIdentityResponse(doc, req, body)
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

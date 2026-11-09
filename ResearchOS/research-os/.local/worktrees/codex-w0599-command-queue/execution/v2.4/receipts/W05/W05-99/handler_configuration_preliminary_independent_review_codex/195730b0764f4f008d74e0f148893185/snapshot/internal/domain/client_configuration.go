package domain

// SQL23 private storage primitives, not a host.configure implementation. The
// caller owns authentication, the transaction and the original response row.
// Only default-only records can be staged here; settled-session switching and
// host/vault/runtime authority require their separately reviewed integration.

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"strings"
	"time"

	"researchos.local/research-os/internal/canonical"
)

const clientConfigurationMaxRevision int64 = 9007199254740991

var clientConfigurationOwner = regexp.MustCompile(`^host-[0-9a-f]{12}$`)
var clientConfigurationRef = regexp.MustCompile(`^mc-[0-9a-f]{32}$`)
var clientConfigurationCredential = regexp.MustCompile(`^cred-[a-z0-9_]{1,24}-[a-z0-9_]{1,24}-[1-9][0-9]{0,18}-[0-9a-f]{8}-[0-9a-f]{8}$`)

type clientConfigurationPayload struct {
	Revision   int64   `json:"config_revision"`
	Provider   string  `json:"provider_id"`
	BaseURL    string  `json:"base_url"`
	Model      string  `json:"model_id"`
	Credential *string `json:"credential_ref"`
}
type clientConfigurationRecord struct {
	Ref, Owner, Principal                                    string
	Payload                                                  clientConfigurationPayload
	CommandID, RequestHash, ConfigHash, ScopeHash, CreatedAt string
	ConfigJSON, ScopeJSON                                    []byte
}
type clientConfigurationHead struct {
	Revision int64
	Ref      string
}

func parseClientConfiguration(doc *SchemaDoc, raw []byte) (clientConfigurationPayload, []byte, error) {
	var p clientConfigurationPayload
	if doc == nil || len(raw) > clientIdentityMaxRequest {
		return p, nil, fmt.Errorf("CONFIGURATION_SCHEMA_OR_SIZE")
	}
	c, err := canonical.JSON(raw)
	if err != nil {
		return p, nil, err
	}
	var value any
	if err = json.Unmarshal(c, &value); err != nil {
		return p, nil, err
	}
	if err = doc.ValidateDefInput("ConfigurePayload", value); err != nil {
		return p, nil, err
	}
	if err = json.Unmarshal(raw, &p); err != nil {
		return p, nil, err
	}
	if p.Revision < 1 || p.Revision > clientConfigurationMaxRevision || !clientIdentityLabel(p.Provider) || !clientIdentityLabel(p.Model) {
		return p, nil, fmt.Errorf("CONFIGURATION_VALUES")
	}
	u, err := url.Parse(p.BaseURL)
	if err != nil || u.Scheme != "https" || u.Host == "" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.ForceQuery || u.Fragment != "" || strings.ContainsAny(p.BaseURL, "#\r\n\t ") {
		return p, nil, fmt.Errorf("CONFIGURATION_ENDPOINT")
	}
	if p.Credential != nil && !clientConfigurationCredential.MatchString(*p.Credential) {
		return p, nil, fmt.Errorf("CONFIGURATION_CREDENTIAL_REFERENCE")
	}
	return p, c, nil
}

func clientConfigurationScope(env *Envelope) ([]byte, error) {
	return canonical.JSON(Bytes(Object{"client_id": env.ClientID, "project_id": env.ProjectID, "session_id": env.SessionID, "expected_revision": env.ExpectedRevision, "writer_epoch": env.WriterEpoch}))
}

func validateClientConfigurationOwner(owner, principal string) error {
	if !clientConfigurationOwner.MatchString(owner) || !clientIdentityLabel(principal) {
		return fmt.Errorf("CONFIGURATION_OWNER_REQUIRED")
	}
	return nil
}

func clientConfigurationProjection(record clientConfigurationRecord) Object {
	return Object{"model_config_ref": record.Ref, "config_revision": record.Payload.Revision, "provider_id": record.Payload.Provider, "base_url": record.Payload.BaseURL, "model_id": record.Payload.Model, "credential_ref": record.Payload.Credential, "verified_at": nil}
}

// stage returns storage data only, never a CommandResponse. After inserting the
// original typed idempotency response, the caller MUST run
// readClientConfiguration (the final semantic/linkage validation) before commit.
// Any error here requires rollback of the caller's complete transaction.
func stageClientConfiguration(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, owner, principal string, raw []byte, env *Envelope) (clientConfigurationRecord, error) {
	if env == nil || env.ProjectID != nil || env.SessionID != nil || env.ExpectedRevision != nil || env.WriterEpoch != nil {
		return clientConfigurationRecord{}, fmt.Errorf("CONFIGURATION_SESSION_INTEGRATION_REQUIRED")
	}
	return stageScopedClientConfiguration(ctx, tx, doc, owner, principal, raw, env)
}

func stageScopedClientConfiguration(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, owner, principal string, raw []byte, env *Envelope) (clientConfigurationRecord, error) {
	var r clientConfigurationRecord
	if tx == nil {
		return r, fmt.Errorf("CONFIGURATION_CALLER_TRANSACTION_REQUIRED")
	}
	if err := validateClientConfigurationOwner(owner, principal); err != nil {
		return r, err
	}
	req, err := validateClientIdentityRequest(doc, raw, env)
	if err != nil {
		return r, err
	}
	if deref(env.Method) != "host.configure" || validateClientConfigurationScope(env) != nil {
		return r, fmt.Errorf("CONFIGURATION_SESSION_INTEGRATION_REQUIRED")
	}
	payload, config, err := parseClientConfiguration(doc, env.Payload)
	if err != nil {
		return r, err
	}
	var identityHash, method, project string
	if err = tx.QueryRowContext(ctx, `SELECT request_hash,method,project FROM client_command_identities WHERE principal=? AND command_id=?`, principal, deref(env.CommandID)).Scan(&identityHash, &method, &project); err != nil {
		return r, err
	}
	if identityHash != req.hash || method != "host.configure" || project != deref(env.ProjectID) {
		return r, fmt.Errorf("CONFIGURATION_COMMAND_IDENTITY")
	}
	// A replay must be resolved before reaching a business mutation primitive.
	var receipts int
	if err = tx.QueryRowContext(ctx, `SELECT count(*) FROM idempotency WHERE principal=? AND key=? AND substr(operation,1,3)='v2:'`, principal, deref(env.CommandID)).Scan(&receipts); err != nil {
		return r, err
	}
	if receipts != 0 {
		return r, ErrIdemConflict
	}
	head, err := readClientConfigurationHead(ctx, tx, doc, owner, principal)
	if err != nil {
		return r, err
	}
	if head.Revision >= clientConfigurationMaxRevision || payload.Revision != head.Revision+1 {
		return r, Fail(409, "CONFIG_CONFLICT", "configuration revision must advance the current head exactly once")
	}
	scope, err := clientConfigurationScope(env)
	if err != nil {
		return r, err
	}
	r = clientConfigurationRecord{Ref: "mc-" + ID(), Owner: owner, Principal: principal, Payload: payload, CommandID: deref(env.CommandID), RequestHash: req.hash, ConfigHash: Digest(config), ScopeHash: Digest(scope), CreatedAt: Now(), ConfigJSON: config, ScopeJSON: scope}
	if _, err = tx.ExecContext(ctx, `INSERT INTO host_model_configurations(model_config_ref,owner_host_ref,principal,config_revision,canonical_config_json,config_hash,command_id,request_hash,operation_scope_json,scope_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)`, r.Ref, owner, principal, payload.Revision, string(config), r.ConfigHash, r.CommandID, r.RequestHash, string(scope), r.ScopeHash, r.CreatedAt); err != nil {
		return clientConfigurationRecord{}, err
	}
	if head.Revision == 0 {
		_, err = tx.ExecContext(ctx, `INSERT INTO host_model_config_heads(owner_host_ref,principal,current_revision,default_model_config_ref) VALUES(?,?,1,?)`, owner, principal, r.Ref)
	} else {
		var result sql.Result
		result, err = tx.ExecContext(ctx, `UPDATE host_model_config_heads SET current_revision=?,default_model_config_ref=? WHERE owner_host_ref=? AND principal=? AND current_revision=? AND default_model_config_ref=?`, payload.Revision, r.Ref, owner, principal, head.Revision, head.Ref)
		if err == nil {
			var n int64
			n, err = result.RowsAffected()
			if err == nil && n != 1 {
				err = Fail(409, "CONFIG_CONFLICT", "configuration head changed")
			}
		}
	}
	return r, err
}

func readClientConfiguration(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, owner, principal, ref string) (clientConfigurationRecord, error) {
	var r clientConfigurationRecord
	var revision int64
	if tx == nil || doc == nil {
		return r, fmt.Errorf("CONFIGURATION_TRANSACTION_AND_SCHEMA_REQUIRED")
	}
	if err := validateClientConfigurationOwner(owner, principal); err != nil {
		return r, err
	}
	if !clientConfigurationRef.MatchString(ref) {
		return r, fmt.Errorf("CONFIGURATION_REFERENCE")
	}
	err := tx.QueryRowContext(ctx, `SELECT model_config_ref,owner_host_ref,principal,config_revision,canonical_config_json,config_hash,command_id,request_hash,operation_scope_json,scope_hash,created_at FROM host_model_configurations WHERE model_config_ref=? AND owner_host_ref=? AND principal=?`, ref, owner, principal).Scan(&r.Ref, &r.Owner, &r.Principal, &revision, &r.ConfigJSON, &r.ConfigHash, &r.CommandID, &r.RequestHash, &r.ScopeJSON, &r.ScopeHash, &r.CreatedAt)
	if err != nil {
		return r, err
	}
	p, c, err := parseClientConfiguration(doc, r.ConfigJSON)
	if err != nil {
		return r, err
	}
	scope, err := canonical.JSON(r.ScopeJSON)
	if err != nil || !bytes.Equal(scope, r.ScopeJSON) || !bytes.Equal(c, r.ConfigJSON) || p.Revision != revision || Digest(c) != r.ConfigHash || Digest(scope) != r.ScopeHash {
		return r, fmt.Errorf("CONFIGURATION_CORRUPT_BYTES")
	}
	if _, err = time.Parse(time.RFC3339Nano, r.CreatedAt); err != nil {
		return r, fmt.Errorf("CONFIGURATION_CREATED_AT")
	}
	var target map[string]json.RawMessage
	if err = json.Unmarshal(scope, &target); err != nil {
		return r, err
	}
	if len(target) != 5 {
		return r, fmt.Errorf("CONFIGURATION_SCOPE")
	}
	for _, key := range []string{"client_id", "project_id", "session_id", "expected_revision", "writer_epoch"} {
		if _, ok := target[key]; !ok {
			return r, fmt.Errorf("CONFIGURATION_SCOPE")
		}
	}
	original := map[string]json.RawMessage{}
	for k, v := range target {
		original[k] = v
	}
	original["protocol_version"] = Bytes(ProtocolV2)
	original["command_id"] = Bytes(r.CommandID)
	original["method"] = Bytes("host.configure")
	original["payload"] = c
	raw, err := json.Marshal(original)
	if err != nil {
		return r, err
	}
	env, err := decodeClientIdentityEnvelope(doc, raw)
	if err != nil {
		return r, err
	}
	if err = validateClientConfigurationScope(env); err != nil {
		return r, err
	}
	req, err := validateClientIdentityRequest(doc, raw, env)
	if err != nil || req.hash != r.RequestHash {
		return r, fmt.Errorf("CONFIGURATION_REQUEST_HASH")
	}
	var linked int
	if err = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=? AND request_hash=? AND project=? AND method='host.configure'`, principal, r.CommandID, r.RequestHash, deref(env.ProjectID)).Scan(&linked); err != nil {
		return r, err
	}
	if linked != 1 {
		return r, fmt.Errorf("CONFIGURATION_IDENTITY_LINK")
	}
	response, err := lookupClientCommandIdentity(ctx, tx, doc, principal, raw, env)
	if err != nil {
		return r, err
	}
	if response == nil || deref(response.Status) != "COMPLETED" {
		return r, fmt.Errorf("CONFIGURATION_ORIGINAL_RECEIPT_REQUIRED")
	}
	if env.SessionID != nil && (response.Revision == nil || *response.Revision != *env.ExpectedRevision+1) {
		return r, fmt.Errorf("CONFIGURATION_ORIGINAL_REVISION")
	}
	r.Payload = p
	projected, _ := canonical.JSON(Bytes(clientConfigurationProjection(r)))
	actual, err := canonical.JSON(Bytes(response.Result))
	if err != nil || !bytes.Equal(projected, actual) {
		return r, fmt.Errorf("CONFIGURATION_ORIGINAL_RESULT_MISMATCH")
	}
	return r, nil
}

func readClientConfigurationHead(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, owner, principal string) (clientConfigurationHead, error) {
	var head clientConfigurationHead
	if tx == nil || doc == nil {
		return head, fmt.Errorf("CONFIGURATION_TRANSACTION_AND_SCHEMA_REQUIRED")
	}
	if err := validateClientConfigurationOwner(owner, principal); err != nil {
		return head, err
	}
	err := tx.QueryRowContext(ctx, `SELECT current_revision,default_model_config_ref FROM host_model_config_heads WHERE owner_host_ref=? AND principal=?`, owner, principal).Scan(&head.Revision, &head.Ref)
	if errors.Is(err, sql.ErrNoRows) {
		return head, nil
	}
	if err != nil {
		return head, err
	}
	r, err := readClientConfiguration(ctx, tx, doc, owner, principal, head.Ref)
	if err != nil {
		return head, err
	}
	if r.Payload.Revision != head.Revision {
		return head, fmt.Errorf("CONFIGURATION_HEAD_MISMATCH")
	}
	return head, nil
}

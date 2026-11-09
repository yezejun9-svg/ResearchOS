package domain

import (
	"context"
	"database/sql"
	_ "embed"
	"encoding/json"
	"fmt"
	"regexp"
	"sort"
	"sync"
	"time"

	"researchos.local/research-os/internal/canonical"
)

// These immutable byte mirrors are the public API's existing frozen schemas.
// The external URI remains domain.schema.json, regardless of the local name.
//
//go:embed contracts/client.protocol.schema.json
var backupConfigurationProtocol []byte

//go:embed contracts/client.protocol.domain.schema.json
var backupConfigurationDomain []byte

var backupConfigurationSchemaOnce sync.Once
var backupConfigurationSchemaDoc *SchemaDoc
var backupConfigurationSchemaError error
var backupConfigurationHash = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)

func loadBackupConfigurationSchema(protocol, external []byte) (*SchemaDoc, error) {
	if Digest(protocol) != "sha256:8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b" || Digest(external) != "sha256:b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54" {
		return nil, fmt.Errorf("BACKUP_CONFIGURATION_SCHEMA_HASH")
	}
	return LoadSchemaWithExternals(protocol, map[string][]byte{"domain.schema.json": external})
}
func backupConfigurationSchema() (*SchemaDoc, error) {
	backupConfigurationSchemaOnce.Do(func() {
		backupConfigurationSchemaDoc, backupConfigurationSchemaError = loadBackupConfigurationSchema(backupConfigurationProtocol, backupConfigurationDomain)
	})
	return backupConfigurationSchemaDoc, backupConfigurationSchemaError
}

type configurationBackupQuery interface {
	Query(string, ...any) (*sql.Rows, error)
}

func configurationBackupRows(db configurationBackupQuery, query string, args ...any) ([]Object, error) {
	rows, e := db.Query(query, args...)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	cols, e := rows.Columns()
	if e != nil {
		return nil, e
	}
	result := []Object{}
	for rows.Next() {
		values := make([]any, len(cols))
		ptrs := make([]any, len(cols))
		for i := range values {
			ptrs[i] = &values[i]
		}
		if e = rows.Scan(ptrs...); e != nil {
			return nil, e
		}
		row := Object{}
		for i, k := range cols {
			row[k] = values[i]
		}
		result = append(result, row)
	}
	return result, rows.Err()
}

// The schema fingerprint includes all three tables, their explicit indexes and
// immutable/CAS triggers plus the exact journal request-hash index. It was
// derived from the fixed SQL23 bytes; no runtime database can redefine it.
func backupConfigurationPresent(db *sql.DB) (bool, error) {
	versions, e := backupMigrations(db)
	if e != nil || len(versions) == 0 || len(versions) > 23 {
		return false, fmt.Errorf("BACKUP_CONFIGURATION_VERSION")
	}
	for i, v := range versions {
		if v != i+1 {
			return false, fmt.Errorf("BACKUP_CONFIGURATION_VERSION")
		}
	}
	schema, e := configurationBackupRows(db, `SELECT type,name,tbl_name,sql FROM sqlite_master WHERE (tbl_name IN ('client_command_identities','host_model_configurations','host_model_config_heads') OR name='client_identity_receipt_request') AND sql IS NOT NULL ORDER BY type,name`)
	if e != nil {
		return false, e
	}
	if len(versions) < 23 {
		if len(schema) != 0 {
			return false, fmt.Errorf("BACKUP_CONFIGURATION_PREMATURE_SCHEMA")
		}
		return false, nil
	}
	if len(schema) != 14 || Hash(schema) != "sha256:06b466cca32bb266d07134db80ad3af6c02500c13e16a4fd70b7e07ed6ca7a65" {
		return false, fmt.Errorf("BACKUP_CONFIGURATION_SCHEMA")
	}
	return true, nil
}

func backupHostConfigurationState(db *sql.DB) (Object, error) {
	present, e := backupConfigurationPresent(db)
	if e != nil || !present {
		return nil, e
	}
	state := Object{"format": "RESEARCHOS_HOST_CONFIGURATION_V1"}
	for _, table := range []string{"client_command_identities", "host_model_configurations", "host_model_config_heads"} {
		rows, e := configurationBackupRows(db, "SELECT * FROM "+table)
		if e != nil {
			return nil, e
		}
		sort.Slice(rows, func(i, j int) bool { return Hash(rows[i]) < Hash(rows[j]) })
		state[table] = rows
	}
	// Include every original response linked by the global principal+command
	// identity, not a second response authority or a projected success label.
	rows, e := configurationBackupRows(db, `SELECT i.* FROM idempotency i JOIN client_command_identities c ON c.principal=i.principal AND c.command_id=i.key WHERE substr(i.operation,1,3)='v2:'`)
	if e != nil {
		return nil, e
	}
	sort.Slice(rows, func(i, j int) bool { return Hash(rows[i]) < Hash(rows[j]) })
	state["original_responses"] = rows
	return state, nil
}

func validateBackupHostConfiguration(db *sql.DB) error {
	present, e := backupConfigurationPresent(db)
	if e != nil || !present {
		return e
	}
	doc, e := backupConfigurationSchema()
	if e != nil {
		return e
	}
	tx, e := db.BeginTx(context.Background(), &sql.TxOptions{ReadOnly: true})
	if e != nil {
		return e
	}
	defer tx.Rollback()
	records, e := configurationBackupRows(tx, `SELECT * FROM host_model_configurations ORDER BY owner_host_ref,principal,config_revision`)
	if e != nil {
		return e
	}
	heads := map[string]clientConfigurationHead{}
	configured := map[string]bool{}
	for _, row := range records {
		owner, principal, ref := Str(row, "owner_host_ref"), Str(row, "principal"), Str(row, "model_config_ref")
		record, e := readClientConfiguration(context.Background(), tx, doc, owner, principal, ref)
		if e != nil {
			return e
		}
		key := Hash([]string{owner, principal})
		head := heads[key]
		if record.Payload.Revision != head.Revision+1 {
			return fmt.Errorf("BACKUP_CONFIGURATION_HISTORY_GAP")
		}
		heads[key] = clientConfigurationHead{record.Payload.Revision, record.Ref}
		configured[Hash([]string{principal, record.CommandID})] = true
	}
	rows, e := configurationBackupRows(tx, `SELECT * FROM host_model_config_heads`)
	if e != nil {
		return e
	}
	if len(rows) != len(heads) {
		return fmt.Errorf("BACKUP_CONFIGURATION_HEAD_COUNT")
	}
	for _, row := range rows {
		key := Hash([]string{Str(row, "owner_host_ref"), Str(row, "principal")})
		head, ok := heads[key]
		rev, e := Num(row, "current_revision")
		if e != nil || !ok || rev != head.Revision || Str(row, "default_model_config_ref") != head.Ref {
			return fmt.Errorf("BACKUP_CONFIGURATION_HEAD_HISTORY")
		}
		delete(heads, key)
	}
	identities, e := configurationBackupRows(tx, `SELECT * FROM client_command_identities`)
	if e != nil {
		return e
	}
	for _, identity := range identities {
		principal, command, method := Str(identity, "principal"), Str(identity, "command_id"), Str(identity, "method")
		if !clientIdentityLabel(principal) || !clientIdentityLabel(command) || identity["protocol"] != ProtocolV2 || identity["operation"] != "v2:"+method || !backupConfigurationHash.MatchString(Str(identity, "request_hash")) {
			return fmt.Errorf("BACKUP_CONFIGURATION_IDENTITY")
		}
		if _, e = time.Parse(time.RFC3339Nano, Str(identity, "created_at")); e != nil {
			return fmt.Errorf("BACKUP_CONFIGURATION_IDENTITY_TIME")
		}
		var roles string
		var revoked, canCreate int
		if e = tx.QueryRow(`SELECT roles,revoked,can_create_project FROM auth_principals WHERE id=?`, principal).Scan(&roles, &revoked, &canCreate); e != nil {
			return fmt.Errorf("BACKUP_CONFIGURATION_PRINCIPAL: %w", e)
		}
		var roleList []string
		if json.Unmarshal([]byte(roles), &roleList) != nil || roleList == nil || (revoked != 0 && revoked != 1) || (canCreate != 0 && canCreate != 1) {
			return fmt.Errorf("BACKUP_CONFIGURATION_PRINCIPAL")
		}
		for _, role := range roleList {
			if !clientIdentityLabel(role) {
				return fmt.Errorf("BACKUP_CONFIGURATION_PRINCIPAL")
			}
		}
		journal, e := configurationBackupRows(tx, `SELECT * FROM idempotency WHERE principal=? AND key=? AND substr(operation,1,3)='v2:'`, principal, command)
		if e != nil {
			return e
		}
		if len(journal) != 1 || journal[0]["project"] != identity["project"] || journal[0]["operation"] != identity["operation"] || journal[0]["request_hash"] != identity["request_hash"] {
			return fmt.Errorf("BACKUP_CONFIGURATION_ORIGINAL_RESPONSE")
		}
		raw := []byte(Str(journal[0], "body"))
		if b, ok := journal[0]["body"].([]byte); ok {
			raw = b
		}
		strict, e := canonical.JSON(raw)
		if e != nil {
			return e
		}
		var value any
		if e = json.Unmarshal(strict, &value); e != nil {
			return e
		}
		if e = doc.ValidateDef("CommandResponse", value); e != nil {
			return e
		}
		var response Response
		if e = json.Unmarshal(strict, &response); e != nil {
			return e
		}
		if deref(response.ProtocolVersion) != ProtocolV2 || deref(response.CommandID) != command || deref(response.Method) != method {
			return fmt.Errorf("BACKUP_CONFIGURATION_RESPONSE_IDENTITY")
		}
		if e = ValidateResultAgainstMethod(method, &response, doc); e != nil {
			return e
		}
		req, known, e := readClientCommandEnvelope(doc, Str(journal[0], "headers"))
		if e != nil {
			return e
		}
		if known {
			if req.hash != identity["request_hash"] || req.hash != journal[0]["request_hash"] || deref(req.env.CommandID) != command || deref(req.env.Method) != method || deref(req.env.ProjectID) != identity["project"] {
				return fmt.Errorf("BACKUP_CONFIGURATION_ORIGINAL_REQUEST")
			}
			if _, e = decodeClientIdentityResponse(doc, req, raw); e != nil {
				return e
			}
			if e = validateClientDerivedSession(context.Background(), tx, principal, req, &response); e != nil {
				return e
			}
		}
		if method == "host.status" && deref(response.Status) == "COMPLETED" && response.Result["authenticated_principal_ref"] != principal {
			return fmt.Errorf("BACKUP_CONFIGURATION_RESPONSE_PRINCIPAL")
		}
		if method == "host.configure" && deref(response.Status) == "COMPLETED" && !configured[Hash([]string{principal, command})] {
			return fmt.Errorf("BACKUP_CONFIGURATION_RESULT_WITHOUT_HISTORY")
		}
		if response.SessionID != nil && !(known && deref(response.Status) == "REJECTED") {
			var n int
			if e = tx.QueryRow(`SELECT count(*) FROM client_sessions WHERE id=? AND project_id=?`, *response.SessionID, identity["project"]).Scan(&n); e != nil || n != 1 {
				return fmt.Errorf("BACKUP_CONFIGURATION_RESPONSE_SESSION")
			}
		}
	}
	return nil
}

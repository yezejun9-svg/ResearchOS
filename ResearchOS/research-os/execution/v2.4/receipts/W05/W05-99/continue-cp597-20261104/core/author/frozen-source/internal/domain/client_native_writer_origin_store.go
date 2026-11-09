package domain

import (
	"context"
	"database/sql"
	"fmt"
)

const nativeOriginColumns = "origin_schema,schema_version,attestation_ref,witness_hash,principal,authority_root,command_id,request_hash,request_wire_hash,response_hash,project,session_id,writer_epoch,writer_client_id,host_instance_ref,host_generation_ref,connection_instance_ref,os_subject_ref,credential_hash,attested_at,attestation_expires_at,created_at,origin_body,origin_hash"

func insertNativeOrigin(ctx context.Context, tx *sql.Tx, row nativeOriginRow) error {
	b := row.body
	_, err := tx.ExecContext(ctx, `INSERT INTO client_native_writer_origins(`+nativeOriginColumns+`) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`, b.OriginSchema, b.SchemaVersion, b.AttestationRef, b.WitnessHash, b.Principal, b.AuthorityRoot, b.CommandID, b.RequestHash, b.RequestWireHash, b.ResponseHash, b.Project, b.SessionID, b.WriterEpoch, b.WriterClientID, b.HostInstanceRef, b.HostGenerationRef, b.ConnectionInstanceRef, b.OSSubjectRef, b.CredentialHash, b.AttestedAt, b.AttestationExpiresAt, b.CreatedAt, row.raw, row.hash)
	return err
}
func readNativeOrigins(ctx context.Context, ex nativeOriginExecutor) ([]nativeOriginRow, error) {
	rows, err := ex.QueryContext(ctx, `SELECT `+nativeOriginColumns+` FROM client_native_writer_origins ORDER BY attestation_ref`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []nativeOriginRow{}
	for rows.Next() {
		var b clientNativeWriterOriginBody
		var raw, hash string
		if err = rows.Scan(&b.OriginSchema, &b.SchemaVersion, &b.AttestationRef, &b.WitnessHash, &b.Principal, &b.AuthorityRoot, &b.CommandID, &b.RequestHash, &b.RequestWireHash, &b.ResponseHash, &b.Project, &b.SessionID, &b.WriterEpoch, &b.WriterClientID, &b.HostInstanceRef, &b.HostGenerationRef, &b.ConnectionInstanceRef, &b.OSSubjectRef, &b.CredentialHash, &b.AttestedAt, &b.AttestationExpiresAt, &b.CreatedAt, &raw, &hash); err != nil {
			return nil, err
		}
		row, e := makeNativeOriginRow(b)
		if e != nil {
			return nil, e
		}
		stored, e := decodeNativeOriginRow(raw, hash)
		if e != nil {
			return nil, e
		}
		if stored.raw != row.raw || stored.hash != row.hash {
			return nil, fmt.Errorf("NATIVE_ORIGIN_COLUMN_BODY")
		}
		out = append(out, stored)
		if len(out) > 10000 {
			return nil, fmt.Errorf("NATIVE_ORIGIN_INVENTORY_LIMIT")
		}
	}
	return out, rows.Err()
}

func validateNativeOriginPair(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, row nativeOriginRow) error {
	b := row.body
	var project, method, requestHash, headers, body string
	err := tx.QueryRowContext(ctx, `SELECT i.project,i.method,i.request_hash,d.headers,d.body FROM client_command_identities i JOIN idempotency d ON d.principal=i.principal AND d.project=i.project AND d.operation=i.operation AND d.key=i.command_id AND d.request_hash=i.request_hash WHERE i.principal=? AND i.command_id=?`, b.Principal, b.CommandID).Scan(&project, &method, &requestHash, &headers, &body)
	if err != nil {
		return fmt.Errorf("NATIVE_ORIGIN_RECEIPT:%w", err)
	}
	if project != b.Project || method != "session.create" || requestHash != b.RequestHash || Digest([]byte(body)) != b.ResponseHash {
		return fmt.Errorf("NATIVE_ORIGIN_RECEIPT_BINDING")
	}
	req, known, err := readClientCommandEnvelope(doc, headers)
	if err != nil || !known || req.nativeOrigin == nil {
		return fmt.Errorf("NATIVE_ORIGIN_MARKER_MISSING")
	}
	m := req.nativeOrigin
	if m.SchemaVersion != 1 || m.AttestationRef != b.AttestationRef || m.WitnessHash != b.WitnessHash || m.OriginHash != row.hash || req.hash != b.RequestHash || Digest(req.env.originalRaw) != b.RequestWireHash || deref(req.env.ClientID) != b.WriterClientID || deref(req.env.ProjectID) != b.Project || deref(req.env.Method) != "session.create" || req.env.SessionID != nil || req.env.ExpectedRevision != nil || req.env.WriterEpoch != nil {
		return fmt.Errorf("NATIVE_ORIGIN_MARKER_BINDING")
	}
	res, err := decodeClientIdentityResponse(doc, req, []byte(body))
	if err != nil {
		return err
	}
	if deref(res.Status) != "COMPLETED" || deref(res.SessionID) != b.SessionID || Str(res.Result, "session_id") != b.SessionID || Str(res.Result, "project_id") != b.Project {
		return fmt.Errorf("NATIVE_ORIGIN_RESPONSE")
	}
	writer, ok := res.Result["writer"].(map[string]any)
	if !ok || Str(writer, "client_id") != b.WriterClientID || fmt.Sprint(writer["epoch"]) != "1" {
		return fmt.Errorf("NATIVE_ORIGIN_RESPONSE_WRITER")
	}
	return validateClientDerivedSession(ctx, tx, b.Principal, req, res)
}

func validateClientNativeReceipt(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, principal string, req clientIdentityRequest) error {
	present, err := nativeOriginSchemaState(ctx, tx)
	if err != nil {
		return err
	}
	if !present {
		if req.nativeOrigin != nil {
			return fmt.Errorf("NATIVE_ORIGIN_SCHEMA_MISSING")
		}
		return nil
	}
	rows, err := readNativeOrigins(ctx, tx)
	if err != nil {
		return err
	}
	var found *nativeOriginRow
	for i := range rows {
		if rows[i].body.Principal == principal && rows[i].body.CommandID == deref(req.env.CommandID) {
			if found != nil {
				return fmt.Errorf("NATIVE_ORIGIN_DUPLICATE")
			}
			found = &rows[i]
		}
	}
	if found == nil {
		if req.nativeOrigin != nil {
			return fmt.Errorf("NATIVE_ORIGIN_ROW_MISSING")
		}
		return nil
	}
	return validateNativeOriginPair(ctx, tx, doc, *found)
}

func nativeOriginHistoryTx(ctx context.Context, tx *sql.Tx, doc *SchemaDoc) (string, error) {
	present, err := nativeOriginSchemaState(ctx, tx)
	if err != nil {
		return "", err
	}
	if !present {
		return "", nil
	}
	rows, err := readNativeOrigins(ctx, tx)
	if err != nil {
		return "", err
	}
	items := []any{}
	for _, row := range rows {
		if err = validateNativeOriginPair(ctx, tx, doc, row); err != nil {
			return "", err
		}
		items = append(items, Object{"origin_body": row.raw, "origin_hash": row.hash})
	}
	var marked int
	if err = tx.QueryRowContext(ctx, `SELECT count(*) FROM idempotency WHERE CASE WHEN json_valid(headers) THEN json_extract(headers,'$.schema')=? OR json_type(headers,'$.native_create_origin') IS NOT NULL ELSE instr(headers,?)>0 END`, nativeCommandHeaderSchema, nativeCommandHeaderSchema).Scan(&marked); err != nil {
		return "", err
	}
	if marked != len(rows) {
		return "", fmt.Errorf("NATIVE_ORIGIN_MARKER_INVENTORY")
	}
	return Hash(Object{"schema": "researchos.native-origin-history.v1", "ddl": Digest([]byte(nativeWriterOriginDDL)), "origins": items}), nil
}

func hasNativeWriterOrigin(ctx context.Context, tx *sql.Tx, project, session string) (bool, error) {
	present, err := nativeOriginSchemaState(ctx, tx)
	if err != nil {
		return false, err
	}
	if !present {
		return false, nil
	}
	var n int
	err = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_native_writer_origins WHERE project=? AND session_id=?`, project, session).Scan(&n)
	return n != 0, err
}

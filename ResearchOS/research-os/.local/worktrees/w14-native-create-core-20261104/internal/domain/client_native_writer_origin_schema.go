package domain

import (
	"bytes"
	"context"
	"database/sql"
	_ "embed"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
	"time"

	"researchos.local/research-os/internal/canonical"
)

//go:embed contracts/0025_client_native_writer_origins.sql
var nativeWriterOriginDDL string

const nativeOriginLegacyReplayGuard = "CREATE TRIGGER idempotency_immutable BEFORE UPDATE ON idempotency BEGIN SELECT RAISE(ABORT,'immutable replay'); END"

const nativeWriterOriginSchema = "researchos.client-native-writer-origin.v1"
const nativeCommandHeaderSchema = "researchos.private-command-envelope.native-create.v2"

var nativeDigestPattern = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)
var nativeConnectionPattern = regexp.MustCompile(`^nci-[0-9a-f]{32}$`)
var nativeHostPattern = regexp.MustCompile(`^host-[0-9a-f]{12}$`)

func nativeDigest(s string) bool        { return nativeDigestPattern.MatchString(s) }
func nativeConnectionRef(s string) bool { return nativeConnectionPattern.MatchString(s) }
func nativeHostRef(s string) bool       { return nativeHostPattern.MatchString(s) }

type clientNativeWriterOriginBody struct {
	OriginSchema          string `json:"origin_schema"`
	SchemaVersion         int64  `json:"schema_version"`
	AttestationRef        string `json:"attestation_ref"`
	WitnessHash           string `json:"witness_hash"`
	Principal             string `json:"principal"`
	AuthorityRoot         string `json:"authority_root"`
	CommandID             string `json:"command_id"`
	RequestHash           string `json:"request_hash"`
	RequestWireHash       string `json:"request_wire_hash"`
	ResponseHash          string `json:"response_hash"`
	Project               string `json:"project"`
	SessionID             string `json:"session_id"`
	WriterEpoch           int64  `json:"writer_epoch"`
	WriterClientID        string `json:"writer_client_id"`
	HostInstanceRef       string `json:"host_instance_ref"`
	HostGenerationRef     string `json:"host_generation_ref"`
	ConnectionInstanceRef string `json:"connection_instance_ref"`
	OSSubjectRef          string `json:"os_subject_ref"`
	CredentialHash        string `json:"credential_hash"`
	AttestedAt            string `json:"attested_at"`
	AttestationExpiresAt  string `json:"attestation_expires_at"`
	CreatedAt             string `json:"created_at"`
}
type nativeOriginRow struct {
	body      clientNativeWriterOriginBody
	raw, hash string
}
type nativeCreateOriginMarker struct {
	SchemaVersion  int64  `json:"schema_version"`
	AttestationRef string `json:"attestation_ref"`
	WitnessHash    string `json:"witness_hash"`
	OriginHash     string `json:"origin_hash"`
}

func nativeUTCTime(s string) (time.Time, error) {
	t, err := time.Parse(time.RFC3339Nano, s)
	if err != nil || t.UTC().Format(time.RFC3339Nano) != s {
		return time.Time{}, fmt.Errorf("NATIVE_ORIGIN_UTC_TIME")
	}
	return t, nil
}
func makeNativeOriginRow(b clientNativeWriterOriginBody) (nativeOriginRow, error) {
	if b.OriginSchema != nativeWriterOriginSchema || b.SchemaVersion != 1 || b.WriterEpoch != 1 || !nativeAttestationRefPattern.MatchString(b.AttestationRef) || !nativeConnectionRef(b.ConnectionInstanceRef) || !nativeHostRef(b.HostInstanceRef) {
		return nativeOriginRow{}, fmt.Errorf("NATIVE_ORIGIN_BODY_SHAPE")
	}
	for _, s := range []string{b.WitnessHash, b.RequestHash, b.RequestWireHash, b.ResponseHash, b.HostGenerationRef, b.CredentialHash} {
		if !nativeDigest(s) {
			return nativeOriginRow{}, fmt.Errorf("NATIVE_ORIGIN_DIGEST")
		}
	}
	for _, s := range []string{b.Principal, b.AuthorityRoot, b.CommandID, b.Project, b.SessionID, b.WriterClientID, b.OSSubjectRef} {
		if !clientIdentityLabel(s) {
			return nativeOriginRow{}, fmt.Errorf("NATIVE_ORIGIN_LABEL")
		}
	}
	issued, e := nativeUTCTime(b.AttestedAt)
	if e != nil {
		return nativeOriginRow{}, e
	}
	expires, e := nativeUTCTime(b.AttestationExpiresAt)
	if e != nil {
		return nativeOriginRow{}, e
	}
	created, e := nativeUTCTime(b.CreatedAt)
	if e != nil {
		return nativeOriginRow{}, e
	}
	if !issued.Before(expires) || created.Before(issued) || created.After(expires) {
		return nativeOriginRow{}, fmt.Errorf("NATIVE_ORIGIN_TIME_ORDER")
	}
	raw, e := canonical.JSON(Bytes(b))
	if e != nil {
		return nativeOriginRow{}, e
	}
	return nativeOriginRow{b, string(raw), Digest(raw)}, nil
}
func decodeNativeOriginRow(raw, hash string) (nativeOriginRow, error) {
	if len(raw) == 0 || len(raw) > 16384 {
		return nativeOriginRow{}, fmt.Errorf("NATIVE_ORIGIN_BODY_SIZE")
	}
	strict, e := canonical.JSON([]byte(raw))
	if e != nil || !bytes.Equal(strict, []byte(raw)) {
		return nativeOriginRow{}, fmt.Errorf("NATIVE_ORIGIN_CANONICAL")
	}
	var b clientNativeWriterOriginBody
	d := json.NewDecoder(strings.NewReader(raw))
	d.DisallowUnknownFields()
	if e = d.Decode(&b); e != nil {
		return nativeOriginRow{}, e
	}
	row, e := makeNativeOriginRow(b)
	if e != nil {
		return nativeOriginRow{}, e
	}
	if row.raw != raw || row.hash != hash {
		return nativeOriginRow{}, fmt.Errorf("NATIVE_ORIGIN_BODY_HASH")
	}
	return row, nil
}

type nativeOriginExecutor interface {
	ExecContext(context.Context, string, ...any) (sql.Result, error)
	QueryContext(context.Context, string, ...any) (*sql.Rows, error)
	QueryRowContext(context.Context, string, ...any) *sql.Row
}

func nativeOriginDDLObjects() map[string]string {
	objects := map[string]string{}
	for _, part := range strings.Split(nativeWriterOriginDDL, "-- object: ")[1:] {
		name, sqlText, ok := strings.Cut(part, "\n")
		if ok {
			objects[strings.TrimSpace(name)] = strings.TrimSuffix(strings.TrimSpace(sqlText), ";")
		}
	}
	return objects
}
func nativeOriginSchemaState(ctx context.Context, ex nativeOriginExecutor) (bool, error) {
	rows, err := ex.QueryContext(ctx, `SELECT name,coalesce(sql,'') FROM sqlite_master WHERE tbl_name='client_native_writer_origins' OR name LIKE 'native_origin_%' ORDER BY name`)
	if err != nil {
		return false, err
	}
	found := map[string]string{}
	for rows.Next() {
		var name, ddl string
		if err = rows.Scan(&name, &ddl); err != nil {
			rows.Close()
			return false, err
		}
		if ddl != "" {
			found[name] = ddl
		}
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return false, err
	}
	var basePresent int
	if err = ex.QueryRowContext(ctx, `SELECT count(*) FROM sqlite_master WHERE type='table' AND name='idempotency'`).Scan(&basePresent); err != nil {
		return false, err
	}
	if basePresent == 0 {
		if len(found) > 0 {
			return false, fmt.Errorf("NATIVE_ORIGIN_BASE_SCHEMA_MISSING")
		}
		return false, nil
	}
	var replayGuard string
	if err = ex.QueryRowContext(ctx, `SELECT sql FROM sqlite_master WHERE type='trigger' AND name='idempotency_immutable'`).Scan(&replayGuard); err != nil && err != sql.ErrNoRows {
		return false, err
	}
	if strings.Contains(replayGuard, nativeCommandHeaderSchema) || strings.Contains(replayGuard, "client_native_writer_origins") {
		found["idempotency_immutable"] = replayGuard
	}
	var markers int
	if err = ex.QueryRowContext(ctx, `SELECT count(*) FROM idempotency WHERE CASE WHEN json_valid(headers) THEN json_extract(headers,'$.schema')=? OR json_type(headers,'$.native_create_origin') IS NOT NULL ELSE instr(headers,?)>0 END`, nativeCommandHeaderSchema, nativeCommandHeaderSchema).Scan(&markers); err != nil {
		return false, err
	}
	if len(found) == 0 {
		if markers != 0 {
			return false, fmt.Errorf("NATIVE_ORIGIN_SCHEMA_MISSING")
		}
		return false, nil
	}
	expected := nativeOriginDDLObjects()
	if len(found) != len(expected) {
		return false, fmt.Errorf("NATIVE_ORIGIN_SCHEMA_OBJECTS")
	}
	for name, sqlText := range expected {
		if strings.TrimSpace(found[name]) != sqlText {
			return false, fmt.Errorf("NATIVE_ORIGIN_SCHEMA_DRIFT:%s", name)
		}
	}
	rows, err = ex.QueryContext(ctx, `SELECT name FROM pragma_index_list('client_native_writer_origins')`)
	if err != nil {
		return false, err
	}
	indexes := []string{}
	for rows.Next() {
		var name string
		if err = rows.Scan(&name); err != nil {
			rows.Close()
			return false, err
		}
		indexes = append(indexes, name)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return false, err
	}
	if len(indexes) != 3 {
		return false, fmt.Errorf("NATIVE_ORIGIN_INDEX_DRIFT")
	}
	want := map[string]bool{"attestation_ref": true, "principal,command_id": true, "project,session_id,writer_epoch": true}
	for _, name := range indexes {
		r, e := ex.QueryContext(ctx, `SELECT name FROM pragma_index_info(?) ORDER BY seqno`, name)
		if e != nil {
			return false, e
		}
		cols := []string{}
		for r.Next() {
			var col string
			if e = r.Scan(&col); e != nil {
				r.Close()
				return false, e
			}
			cols = append(cols, col)
		}
		e = r.Err()
		r.Close()
		if e != nil {
			return false, e
		}
		key := strings.Join(cols, ",")
		if !want[key] {
			return false, fmt.Errorf("NATIVE_ORIGIN_INDEX_COLUMNS")
		}
		delete(want, key)
	}
	return true, nil
}
func requireNativeOriginSchema(ctx context.Context, ex nativeOriginExecutor) error {
	present, err := nativeOriginSchemaState(ctx, ex)
	if err != nil {
		return err
	}
	if !present {
		return fmt.Errorf("NATIVE_CREATE_UNSUPPORTED")
	}
	return nil
}

// Trusted explicit fresh-fixture installation only. It is never a startup migration.
func InstallClientNativeWriterOriginPreparedSchema(ctx context.Context, db *sql.DB) error {
	present, err := nativeOriginSchemaState(ctx, db)
	if err != nil {
		return err
	}
	if present {
		return nil
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var replayGuard string
	if err = tx.QueryRowContext(ctx, `SELECT sql FROM sqlite_master WHERE type='trigger' AND name='idempotency_immutable'`).Scan(&replayGuard); err != nil {
		return err
	}
	if strings.TrimSpace(replayGuard) != nativeOriginLegacyReplayGuard {
		return fmt.Errorf("NATIVE_ORIGIN_BASE_GUARD_PREIMAGE:%s", Digest([]byte(replayGuard)))
	}
	if _, err = tx.ExecContext(ctx, nativeWriterOriginDDL); err != nil {
		return err
	}
	if err = requireNativeOriginSchema(ctx, tx); err != nil {
		return err
	}
	return tx.Commit()
}

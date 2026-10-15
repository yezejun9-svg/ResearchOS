//go:build windows

package host

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"errors"
	"fmt"
	"net/url"
	"path/filepath"
	"strings"

	_ "modernc.org/sqlite"
	"researchos.local/research-os/internal/auth"
)

// OwnedCoreStopPublicIdentity contains only public authority metadata. It
// never reads credentials, keys, vault records or private process memory.
type OwnedCoreStopPublicIdentity struct {
	DataRoot        string `json:"data_root"`
	Database        string `json:"database"`
	DatabaseVolume  uint32 `json:"database_volume"`
	DatabaseIndex   uint64 `json:"database_index"`
	SID             string `json:"sid"`
	PrincipalRef    string `json:"principal_ref"`
	HostID          string `json:"host_id"`
	OwnerID         string `json:"owner_id"`
	OwnerRoot       string `json:"owner_root"`
	HostStateSHA256 string `json:"host_state_sha256"`
	SchemaVersion   int    `json:"schema_version"`
}

// ReadOwnedCoreStopPublicIdentity opens an existing database read-only and
// reads the protected host_state.json through the existing same-SID reader.
// The caller's SQLite barrier, when present, keeps this database view stable.
func ReadOwnedCoreStopPublicIdentity(ctx context.Context, dataRoot string) (OwnedCoreStopPublicIdentity, error) {
	var out OwnedCoreStopPublicIdentity
	if e := replacementPath(dataRoot); e != nil {
		return out, e
	}
	actual, e := filepath.EvalSymlinks(dataRoot)
	if e != nil || !strings.EqualFold(actual, dataRoot) {
		return out, errors.New("data-root reparse refused")
	}
	hostDir := filepath.Join(dataRoot, "host")
	dbPath := filepath.Join(dataRoot, "researchos.sqlite")
	for i, path := range []string{dataRoot, hostDir, dbPath} {
		if _, e = replacementIdentity(path, i < 2); e != nil {
			return out, e
		}
		if e = replacementACL(path, i < 2, i == 1); e != nil {
			return out, e
		}
	}
	dbID, e := replacementIdentity(dbPath, false)
	if e != nil {
		return out, e
	}
	raw, e := replacementRead(filepath.Join(hostDir, stateFile), 64<<10)
	if e != nil {
		return out, e
	}
	var state hostState
	if e = decodeRuntimeManaged(raw, &state); e != nil {
		return out, e
	}
	identity, e := auth.Current()
	if e != nil {
		return out, e
	}
	sid, e := currentSIDString()
	if e != nil {
		return out, e
	}
	if state.Version != 1 || state.HostInstanceID == "" || state.PrincipalID == "" || state.PrincipalRef != identity.Ref {
		return out, ErrHostIdentity
	}
	stateHash := sha256.Sum256(raw)
	out = OwnedCoreStopPublicIdentity{DataRoot: dataRoot, Database: dbPath, DatabaseVolume: dbID.Volume, DatabaseIndex: uint64(dbID.IndexHigh)<<32 | uint64(dbID.IndexLow), SID: sid, PrincipalRef: identity.Ref, HostID: state.HostInstanceID, OwnerID: state.PrincipalID, HostStateSHA256: hex.EncodeToString(stateHash[:])}
	u := url.URL{Scheme: "file", Opaque: filepath.ToSlash(dbPath)}
	q := u.Query()
	q.Set("mode", "ro")
	u.RawQuery = q.Encode()
	db, e := sql.Open("sqlite", u.String())
	if e != nil {
		return out, e
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	var versions, minVersion int
	if e = db.QueryRowContext(ctx, `SELECT max(version),min(version),count(DISTINCT version) FROM schema_migrations`).Scan(&out.SchemaVersion, &minVersion, &versions); e != nil || out.SchemaVersion != 24 || minVersion != 1 || versions != 24 {
		return out, errors.New("schema 24 fingerprint unavailable")
	}
	var owners int
	rows, e := db.QueryContext(ctx, `SELECT id,roles,revoked FROM auth_principals ORDER BY id`)
	if e != nil {
		return out, e
	}
	for rows.Next() {
		var id, roles string
		var revoked int
		if e = rows.Scan(&id, &roles, &revoked); e != nil {
			break
		}
		var list []string
		if e = decodeRuntimeManaged([]byte(roles), &list); e != nil {
			break
		}
		for _, role := range list {
			if role == "OWNER" && revoked == 0 {
				owners++
				if id != out.OwnerID {
					e = ErrHostIdentity
					break
				}
			}
		}
		if e != nil {
			break
		}
	}
	if e == nil {
		e = rows.Err()
	}
	rows.Close()
	if e != nil {
		return out, e
	}
	if owners != 1 {
		return out, fmt.Errorf("current unrevoked OWNER count %d", owners)
	}
	if e = db.QueryRowContext(ctx, `SELECT root FROM orchestration_identity WHERE principal=?`, out.OwnerID).Scan(&out.OwnerRoot); e != nil || out.OwnerRoot == "" {
		return out, errors.New("Owner root unavailable")
	}
	return out, nil
}
